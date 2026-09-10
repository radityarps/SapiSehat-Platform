"""Atomic publication rules for Guide Articles."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException  # type: ignore[import-not-found]
from sqlalchemy import select, text  # type: ignore[import-not-found]

from api.db_models import (
    GuideArticleModel,
    GuideArticleTranslationModel,
    GuideCategoryModel,
    GuideCategoryTranslationModel,
    GuideManifestModel,
    GuideMediaModel,
)

PUBLICATION_LOCK_ID = 947006
FORBIDDEN_HEALTH_CLAIMS = (
    "diagnosis pasti",
    "diagnosis terkonfirmasi",
    "wabah terkonfirmasi",
    "wabah dipastikan",
    "positif pmk",
    "terinfeksi pmk",
    "confirmed diagnosis",
    "confirmed outbreak",
    "infected with fmd",
    "positive for fmd",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def lock_publication(session) -> None:
    """Serialize mobile-visible writes on PostgreSQL for one consistent snapshot."""
    if session.bind.dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": PUBLICATION_LOCK_ID}
        )


def article_document(session, article: GuideArticleModel) -> dict:
    translations = session.scalars(
        select(GuideArticleTranslationModel)
        .where(GuideArticleTranslationModel.article_id == article.id)
        .order_by(GuideArticleTranslationModel.locale)
    ).all()
    return {
        "id": article.id,
        "category_id": article.category_id,
        "state": "published",
        "published_at": article.published_at,
        "translations": [
            {
                "locale": row.locale,
                "title": row.title,
                "summary": row.summary,
                "blocks": row.blocks,
            }
            for row in translations
        ],
    }


def validate_and_capture_article(session, article: GuideArticleModel) -> dict:
    session.flush()
    document = article_document(session, article)
    translations = document["translations"]
    indonesian = next((item for item in translations if item["locale"] == "id"), None)
    if (
        not indonesian
        or not indonesian["title"].strip()
        or not indonesian["summary"].strip()
        or not indonesian["blocks"]
    ):
        raise HTTPException(
            status_code=422, detail="Complete Bahasa Indonesia content is required"
        )
    text_value = canonical_json(translations).casefold()
    if any(term in text_value for term in FORBIDDEN_HEALTH_CLAIMS):
        raise HTTPException(
            status_code=422, detail="Guide content must use non-diagnostic language"
        )
    for media_id in {
        block.get("media_id")
        for translation in translations
        for block in translation["blocks"]
        if block.get("type") == "image"
    }:
        media = session.get(GuideMediaModel, media_id)
        if media is None or not media.ready:
            raise HTTPException(
                status_code=422, detail=f"Guide media not ready: {media_id}"
            )
    return document


def category_document(session, category: GuideCategoryModel) -> dict:
    translations = session.scalars(
        select(GuideCategoryTranslationModel)
        .where(GuideCategoryTranslationModel.category_id == category.id)
        .order_by(GuideCategoryTranslationModel.locale)
    ).all()
    return {
        "id": category.id,
        "state": category.state,
        "system_owned": category.system_owned,
        "display_order": category.display_order,
        "translations": [
            {"locale": item.locale, "label": item.label} for item in translations
        ],
    }


def build_manifest(session) -> GuideManifestModel:
    """Build immutable complete membership from captured published documents."""
    lock_publication(session)
    session.flush()
    categories = session.scalars(
        select(GuideCategoryModel)
        .where(GuideCategoryModel.state == "active")
        .order_by(GuideCategoryModel.display_order, GuideCategoryModel.id)
    ).all()
    articles = session.scalars(
        select(GuideArticleModel)
        .where(GuideArticleModel.state == "published")
        .order_by(GuideArticleModel.category_id, GuideArticleModel.published_at.desc())
    ).all()
    category_docs = [category_document(session, row) for row in categories]
    article_docs = []
    for row in articles:
        document = row.published_document
        if (
            not isinstance(document, dict)
            or document.get("id") != row.id
            or document.get("state") != "published"
            or not isinstance(document.get("translations"), list)
        ):
            raise HTTPException(
                status_code=422, detail=f"Published Guide document is invalid: {row.id}"
            )
        article_docs.append(dict(document))
    media_ids = sorted(
        {
            block["media_id"]
            for article in article_docs
            for translation in article["translations"]
            for block in translation["blocks"]
            if block.get("type") == "image"
        }
    )
    media_rows = [session.get(GuideMediaModel, media_id) for media_id in media_ids]
    if any(row is None or not row.ready for row in media_rows):
        raise HTTPException(
            status_code=422, detail="Published Guide media is not ready"
        )
    media = [
        {
            "id": row.id,
            "sha256": row.sha256,
            "mime_type": row.mime_type,
            "byte_size": row.byte_size,
            "width": row.width,
            "height": row.height,
            "url": f"/api/guide/media/{row.id}",
        }
        for row in media_rows
        if row is not None
    ]
    stores = {
        "categories": {doc["id"]: doc for doc in category_docs},
        "articles": {doc["id"]: doc for doc in article_docs},
    }
    descriptors = {
        kind: [
            {
                "id": doc["id"],
                "sha256": canonical_hash(doc),
                "url": f"/api/guide/documents/{kind}/{doc['id']}",
            }
            for doc in docs
        ]
        for kind, docs in (("categories", category_docs), ("articles", article_docs))
    }
    manifest = GuideManifestModel(created_at=now(), catalog={})
    session.add(manifest)
    session.flush()  # Native identity/sequence allocates a concurrency-safe version.
    for values in descriptors.values():
        for value in values:
            value["url"] += f"?version={manifest.version}"
    manifest.catalog = {
        "version": manifest.version,
        "documents": descriptors,
        "document_store": stores,
        "media": media,
    }
    return manifest


def public_manifest(
    current: GuideManifestModel, previous: GuideManifestModel | None
) -> dict:
    catalog = current.catalog
    result = {
        "changed": True,
        "version": current.version,
        "documents": catalog["documents"],
        "media": catalog["media"],
    }
    current_docs = {
        item["id"]: item["sha256"]
        for kind in ("categories", "articles")
        for item in catalog["documents"][kind]
    }
    current_media = {item["id"]: item["sha256"] for item in catalog["media"]}
    old_docs: dict[str, str] = {}
    old_media: dict[str, str] = {}
    if previous is not None:
        old_docs = {
            item["id"]: item["sha256"]
            for kind in ("categories", "articles")
            for item in previous.catalog["documents"][kind]
        }
        old_media = {item["id"]: item["sha256"] for item in previous.catalog["media"]}
    result["changed_document_ids"] = sorted(
        item_id
        for item_id, digest in current_docs.items()
        if old_docs.get(item_id) != digest
    )
    result["removed_document_ids"] = sorted(old_docs.keys() - current_docs.keys())
    result["changed_media_ids"] = sorted(
        item_id
        for item_id, digest in current_media.items()
        if old_media.get(item_id) != digest
    )
    result["removed_media_ids"] = sorted(old_media.keys() - current_media.keys())
    return result
