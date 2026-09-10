"""Guide Article CMS and versioned farmer catalog."""

from __future__ import annotations

import hashlib
import io
import json
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import (  # type: ignore[import-not-found]
    APIRouter,
    File,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from PIL import Image
from pydantic import BaseModel, Field  # type: ignore[import-not-found]
from sqlalchemy import func, select  # type: ignore[import-not-found]

from api.authorization import DEMO_AGENCY_USERS
from api.database import SessionLocal
from api.db_models import (
    GuideArticleModel,
    GuideArticleTranslationModel,
    GuideCategoryModel,
    GuideCategoryTranslationModel,
    GuideEditorialAuditEventModel,
    GuideManifestModel,
    GuideMediaModel,
)
from api.guide_publication import (
    build_manifest,
    canonical_json,
    lock_publication,
    now,
    public_manifest,
    validate_and_capture_article,
)
from api.object_storage import media_storage_client
from api.surface_auth import read_token

router = APIRouter(prefix="/api")
UMUM_CATEGORY_ID = "guide-category-umum"
ALLOWED_IMAGE_TYPES = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_EDGE = 2048
MAX_DECODED_IMAGE_EDGE = 8192
MAX_ARTICLE_IMAGES = 10


def _claims(authorization: str, account_type: str) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if claims.get("account_type") != account_type:
        raise HTTPException(
            status_code=403, detail=f"{account_type.title()} account required"
        )
    return claims


def _admin(authorization: str, agency_user_id: str):
    claims = _claims(authorization, "agency")
    if str(claims.get("sub")) != agency_user_id:
        raise HTTPException(status_code=403, detail="Agency identity mismatch")
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None or agency.role.value != "admin":
        raise HTTPException(status_code=403, detail="Global admin role required")
    return agency


class StrictInput(BaseModel):
    model_config = {"extra": "forbid"}


class GuideBlock(StrictInput):
    type: Literal["heading", "paragraph", "bullet_list", "image"]
    text: str | None = Field(default=None, max_length=4000)
    items: list[str] | None = Field(default=None, max_length=30)
    media_id: str | None = Field(default=None, max_length=80)
    alt: str | None = Field(default=None, max_length=300)

    def model_post_init(self, __context: object, /) -> None:
        if self.type in {"heading", "paragraph"} and not (self.text or "").strip():
            raise ValueError("text is required")
        if self.type == "bullet_list" and not self.items:
            raise ValueError("bullet list items are required")
        if self.items and any(
            not item.strip() or len(item) > 500 for item in self.items
        ):
            raise ValueError("bullet list items must be 1-500 characters")
        if self.type == "image" and (not self.media_id or not (self.alt or "").strip()):
            raise ValueError("image media_id and alt are required")
        allowed = {
            "heading": {"text"},
            "paragraph": {"text"},
            "bullet_list": {"items"},
            "image": {"media_id", "alt"},
        }[self.type]
        supplied = {
            name
            for name in ("text", "items", "media_id", "alt")
            if getattr(self, name) is not None
        }
        if supplied - allowed:
            raise ValueError(
                f"unknown fields for {self.type}: {', '.join(sorted(supplied - allowed))}"
            )


class ArticleTranslationInput(StrictInput):
    locale: str = Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$", max_length=10)
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=500)
    blocks: list[GuideBlock] = Field(min_length=1, max_length=60)


class ArticleInput(StrictInput):
    category_id: str = Field(max_length=80)
    translations: list[ArticleTranslationInput] = Field(min_length=1, max_length=10)

    def model_post_init(self, __context: object, /) -> None:
        locales = [item.locale for item in self.translations]
        if len(locales) != len(set(locales)):
            raise ValueError("translation locales must be unique")
        if any(
            sum(block.type == "image" for block in item.blocks) > MAX_ARTICLE_IMAGES
            for item in self.translations
        ):
            raise ValueError(
                f"each translation accepts at most {MAX_ARTICLE_IMAGES} images"
            )


class CategoryTranslationInput(StrictInput):
    locale: str = Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$", max_length=10)
    label: str = Field(min_length=1, max_length=80)


class CategoryInput(StrictInput):
    display_order: int = Field(default=0, ge=0, le=10000)
    translations: list[CategoryTranslationInput] = Field(min_length=1, max_length=10)

    def model_post_init(self, __context: object, /) -> None:
        locales = [item.locale for item in self.translations]
        if "id" not in locales:
            raise ValueError("Bahasa Indonesia category label is required")
        if len(locales) != len(set(locales)):
            raise ValueError("translation locales must be unique")


def _translation_dict(row: GuideArticleTranslationModel) -> dict:
    return {
        "locale": row.locale,
        "title": row.title,
        "summary": row.summary,
        "blocks": row.blocks,
    }


def _article_dict(session, row: GuideArticleModel) -> dict:
    translations = session.scalars(
        select(GuideArticleTranslationModel)
        .where(GuideArticleTranslationModel.article_id == row.id)
        .order_by(GuideArticleTranslationModel.locale)
    ).all()
    return {
        "id": row.id,
        "category_id": row.category_id,
        "state": row.state,
        "published_at": row.published_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "translations": [_translation_dict(item) for item in translations],
    }


def _category_dict(session, row: GuideCategoryModel) -> dict:
    translations = session.scalars(
        select(GuideCategoryTranslationModel)
        .where(GuideCategoryTranslationModel.category_id == row.id)
        .order_by(GuideCategoryTranslationModel.locale)
    ).all()
    count = (
        session.scalar(
            select(func.count())
            .select_from(GuideArticleModel)
            .where(GuideArticleModel.category_id == row.id)
        )
        or 0
    )
    return {
        "id": row.id,
        "state": row.state,
        "system_owned": row.system_owned,
        "display_order": row.display_order,
        "article_count": count,
        "translations": [
            {"locale": item.locale, "label": item.label} for item in translations
        ],
    }


def _audit(
    session,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
) -> None:
    session.add(
        GuideEditorialAuditEventModel(
            id=f"guide-audit-{uuid4().hex}",
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_json=metadata or {},
            created_at=now(),
        )
    )


def _replace_article_translations(
    session, article_id: str, values: list[ArticleTranslationInput]
) -> None:
    rows = session.scalars(
        select(GuideArticleTranslationModel).where(
            GuideArticleTranslationModel.article_id == article_id
        )
    ).all()
    for row in rows:
        session.delete(row)
    for value in values:
        session.add(
            GuideArticleTranslationModel(
                id=f"{article_id}:{value.locale}",
                article_id=article_id,
                locale=value.locale,
                title=value.title.strip(),
                summary=value.summary.strip(),
                blocks=[
                    {
                        name: getattr(block, name)
                        for name in ("type", "text", "items", "media_id", "alt")
                        if getattr(block, name) is not None
                    }
                    for block in value.blocks
                ],
            )
        )


def _replace_category_translations(
    session, category_id: str, values: list[CategoryTranslationInput]
) -> None:
    rows = session.scalars(
        select(GuideCategoryTranslationModel).where(
            GuideCategoryTranslationModel.category_id == category_id
        )
    ).all()
    for row in rows:
        session.delete(row)
    for value in values:
        session.add(
            GuideCategoryTranslationModel(
                id=f"{category_id}:{value.locale}",
                category_id=category_id,
                locale=value.locale,
                label=value.label.strip(),
            )
        )


@router.get("/agency/guide/categories", tags=["guide-cms"])
def list_categories(
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        rows = session.scalars(
            select(GuideCategoryModel).order_by(
                GuideCategoryModel.display_order, GuideCategoryModel.id
            )
        ).all()
        return {"items": [_category_dict(session, row) for row in rows]}


@router.post("/agency/guide/categories", status_code=201, tags=["guide-cms"])
def create_category(
    request: CategoryInput,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        lock_publication(session)
        category = GuideCategoryModel(
            id=f"guide-category-{uuid4().hex}",
            state="active",
            system_owned=False,
            display_order=request.display_order,
            created_at=now(),
            updated_at=now(),
        )
        session.add(category)
        _replace_category_translations(session, category.id, request.translations)
        _audit(session, agency_user_id, "create", "guide_category", category.id)
        build_manifest(session)
        session.commit()
        return _category_dict(session, category)


@router.put("/agency/guide/categories/{category_id}", tags=["guide-cms"])
def update_category(
    category_id: str,
    request: CategoryInput,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        lock_publication(session)
        category = session.get(GuideCategoryModel, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Guide category not found")
        category.display_order = request.display_order
        category.updated_at = now()
        _replace_category_translations(session, category.id, request.translations)
        _audit(session, agency_user_id, "update", "guide_category", category.id)
        build_manifest(session)
        session.commit()
        return _category_dict(session, category)


@router.post("/agency/guide/categories/{category_id}/archive", tags=["guide-cms"])
def archive_category(
    category_id: str,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        lock_publication(session)
        category = session.get(GuideCategoryModel, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Guide category not found")
        if category.system_owned:
            raise HTTPException(
                status_code=422, detail="Umum category cannot be archived"
            )
        article_ids = list(
            session.scalars(
                select(GuideArticleModel.id).where(
                    GuideArticleModel.category_id == category_id
                )
            ).all()
        )
        for article_id in article_ids:
            article = session.get(GuideArticleModel, article_id)
            if article is not None:
                if article.state == "published":
                    document = article.published_document
                    if not isinstance(document, dict):
                        raise HTTPException(
                            status_code=422,
                            detail=f"Published Guide document is invalid: {article.id}",
                        )
                    try:
                        published = canonical_json(document)
                        preserved = json.loads(published)
                        if (
                            preserved["id"] != article.id
                            or preserved["state"] != "published"
                            or not isinstance(preserved["translations"], list)
                        ):
                            raise ValueError
                    except (KeyError, TypeError, ValueError) as exc:
                        raise HTTPException(
                            status_code=422,
                            detail=f"Published Guide document is invalid: {article.id}",
                        ) from exc
                    preserved["category_id"] = UMUM_CATEGORY_ID
                    article.published_document = preserved
                article.category_id = UMUM_CATEGORY_ID
                article.updated_at = now()
        category.state = "archived"
        category.updated_at = now()
        for article_id in article_ids:
            _audit(
                session,
                agency_user_id,
                "category_move",
                "guide_article",
                article_id,
                {"from": category_id, "to": UMUM_CATEGORY_ID},
            )
        _audit(
            session,
            agency_user_id,
            "archive",
            "guide_category",
            category_id,
            {"moved_articles": len(article_ids)},
        )
        build_manifest(session)
        session.commit()
        return {
            "id": category_id,
            "state": "archived",
            "moved_articles": len(article_ids),
        }


@router.post("/agency/guide/categories/{category_id}/activate", tags=["guide-cms"])
def activate_category(
    category_id: str,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        lock_publication(session)
        category = session.get(GuideCategoryModel, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Guide category not found")
        category.state = "active"
        category.updated_at = now()
        _audit(session, agency_user_id, "activate", "guide_category", category.id)
        build_manifest(session)
        session.commit()
        return _category_dict(session, category)


@router.get("/agency/guide/articles", tags=["guide-cms"])
def list_articles(
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    state: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    locale: str | None = Query(default=None),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        query = select(GuideArticleModel).order_by(GuideArticleModel.updated_at.desc())
        if state:
            query = query.where(GuideArticleModel.state == state)
        if category_id:
            query = query.where(GuideArticleModel.category_id == category_id)
        items = [_article_dict(session, row) for row in session.scalars(query).all()]
        if locale:
            items = [
                item
                for item in items
                if locale in {value["locale"] for value in item["translations"]}
            ]
        if search:
            needle = search.casefold()
            items = [
                item
                for item in items
                if any(
                    needle in value["title"].casefold()
                    for value in item["translations"]
                )
            ]
        return {"items": items}


@router.post("/agency/guide/articles", status_code=201, tags=["guide-cms"])
def create_article(
    request: ArticleInput,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        category = session.get(GuideCategoryModel, request.category_id)
        if category is None or category.state != "active":
            raise HTTPException(
                status_code=422, detail="Active Guide Category required"
            )
        article = GuideArticleModel(
            id=f"guide-article-{uuid4().hex}",
            category_id=request.category_id,
            state="draft",
            published_at=None,
            published_document=None,
            created_at=now(),
            updated_at=now(),
        )
        session.add(article)
        _replace_article_translations(session, article.id, request.translations)
        _audit(session, agency_user_id, "create", "guide_article", article.id)
        session.commit()
        return _article_dict(session, article)


@router.get("/agency/guide/articles/{article_id}", tags=["guide-cms"])
def get_article(
    article_id: str,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        article = session.get(GuideArticleModel, article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Guide Article not found")
        return _article_dict(session, article)


@router.put("/agency/guide/articles/{article_id}", tags=["guide-cms"])
def update_article(
    article_id: str,
    request: ArticleInput,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        article = session.get(GuideArticleModel, article_id)
        category = session.get(GuideCategoryModel, request.category_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Guide Article not found")
        if article.state == "archived":
            raise HTTPException(
                status_code=422, detail="Archived Guide Article cannot be edited"
            )
        if category is None or category.state != "active":
            raise HTTPException(
                status_code=422, detail="Active Guide Category required"
            )
        article.category_id = request.category_id
        article.updated_at = now()
        _replace_article_translations(session, article.id, request.translations)
        _audit(session, agency_user_id, "update", "guide_article", article.id)
        session.commit()
        return _article_dict(session, article)


@router.post("/agency/guide/articles/{article_id}/{action}", tags=["guide-cms"])
def transition_article(
    article_id: str,
    action: Literal["publish", "unpublish", "archive"],
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        lock_publication(session)
        article = session.get(GuideArticleModel, article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Guide Article not found")
        if article.state == "archived":
            raise HTTPException(status_code=422, detail="Guide Article is archived")
        if action == "publish":
            article.state = "published"
            article.published_at = now()
            article.published_document = validate_and_capture_article(session, article)
        elif action == "unpublish":
            if article.state != "published":
                raise HTTPException(
                    status_code=422, detail="Only published articles can be unpublished"
                )
            article.state = "unpublished"
        else:
            article.state = "archived"
        article.updated_at = now()
        _audit(session, agency_user_id, action, "guide_article", article.id)
        build_manifest(session)
        session.commit()
        return _article_dict(session, article)


@router.post("/agency/guide/media", status_code=201, tags=["guide-cms"])
def upload_media(
    file: Annotated[UploadFile, File(...)],
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    declared = file.content_type or ""
    if declared not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=422, detail="Only JPEG, PNG, or WebP guide images are accepted"
        )
    content = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Guide image exceeds 5 MB")
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid guide image") from exc
    if image.format != ALLOWED_IMAGE_TYPES[declared]:
        raise HTTPException(
            status_code=422,
            detail="Guide image content does not match declared MIME type",
        )
    if image.width > MAX_DECODED_IMAGE_EDGE or image.height > MAX_DECODED_IMAGE_EDGE:
        raise HTTPException(
            status_code=422, detail="Guide image decoded dimensions exceed 8192 pixels"
        )
    image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
    output = io.BytesIO()
    if declared == "image/jpeg":
        image.convert("RGB").save(output, "JPEG", quality=82, optimize=True)
    elif declared == "image/png":
        image.save(output, "PNG", optimize=True)
    else:
        image.save(output, "WEBP", quality=82, method=6)
    optimized = output.getvalue()
    media_id = f"guide-media-{uuid4().hex}"
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[
        declared
    ]
    object_key = f"cms/guides/{media_id}.{extension}"
    media_storage_client.put_object(
        object_key=object_key, content=optimized, content_type=declared
    )
    with SessionLocal() as session:
        row = GuideMediaModel(
            id=media_id,
            object_key=object_key,
            mime_type=declared,
            width=image.width,
            height=image.height,
            byte_size=len(optimized),
            sha256=hashlib.sha256(optimized).hexdigest(),
            ready=True,
            created_at=now(),
        )
        session.add(row)
        _audit(session, agency_user_id, "create", "guide_media", media_id)
        session.commit()
        return {
            "id": row.id,
            "mime_type": row.mime_type,
            "width": row.width,
            "height": row.height,
            "byte_size": row.byte_size,
            "sha256": row.sha256,
        }


@router.get("/agency/guide/media", tags=["guide-cms"])
def list_media(
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        rows = session.scalars(
            select(GuideMediaModel)
            .where(GuideMediaModel.ready.is_(True))
            .order_by(GuideMediaModel.created_at.desc())
        ).all()
        return {
            "items": [
                {
                    "id": row.id,
                    "mime_type": row.mime_type,
                    "width": row.width,
                    "height": row.height,
                    "byte_size": row.byte_size,
                    "sha256": row.sha256,
                }
                for row in rows
            ]
        }


@router.get("/agency/guide/media/{media_id}/preview", tags=["guide-cms"])
def preview_media(
    media_id: str,
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        row = session.get(GuideMediaModel, media_id)
        if row is None or not row.ready:
            raise HTTPException(status_code=404, detail="Guide media not found")
        return Response(
            content=media_storage_client.get_object(object_key=row.object_key),
            media_type=row.mime_type,
            headers={"Cache-Control": "private, no-store", "ETag": row.sha256},
        )


@router.get("/agency/guide/audit-events", tags=["guide-cms"])
def list_editorial_audit(
    authorization: str = Header(..., alias="Authorization"),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    limit: int = Query(default=50, ge=1, le=100),
):
    _admin(authorization, agency_user_id)
    with SessionLocal() as session:
        rows = session.scalars(
            select(GuideEditorialAuditEventModel)
            .order_by(GuideEditorialAuditEventModel.created_at.desc())
            .limit(limit)
        ).all()
        return {
            "items": [
                {
                    "id": row.id,
                    "actor_id": row.actor_id,
                    "action": row.action,
                    "target_type": row.target_type,
                    "target_id": row.target_id,
                    "metadata_json": row.metadata_json,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
        }


@router.get("/guide/manifest", tags=["guide"])
def get_manifest(
    authorization: str = Header(..., alias="Authorization"),
    version: int | None = Query(default=None, ge=0),
):
    _claims(authorization, "farmer")
    with SessionLocal() as session:
        current = session.scalar(
            select(GuideManifestModel)
            .order_by(GuideManifestModel.version.desc())
            .limit(1)
        )
        if current is None:
            current = build_manifest(session)
            session.commit()
        if version == current.version:
            return {"changed": False, "version": current.version}
        previous = session.get(GuideManifestModel, version) if version else None
        return public_manifest(current, previous)


@router.get("/guide/documents/{kind}/{document_id}", tags=["guide"])
def get_document(
    kind: Literal["categories", "articles"],
    document_id: str,
    version: int = Query(..., ge=1),
    authorization: str = Header(..., alias="Authorization"),
):
    _claims(authorization, "farmer")
    with SessionLocal() as session:
        manifest = session.get(GuideManifestModel, version)
        document = (
            manifest.catalog.get("document_store", {}).get(kind, {}).get(document_id)
            if manifest
            else None
        )
        if document is None:
            raise HTTPException(status_code=404, detail="Guide document not found")
        return Response(content=canonical_json(document), media_type="application/json")


@router.get("/guide/media/{media_id}", tags=["guide"])
def get_media(media_id: str, authorization: str = Header(..., alias="Authorization")):
    _claims(authorization, "farmer")
    with SessionLocal() as session:
        row = session.get(GuideMediaModel, media_id)
        retained = session.scalars(select(GuideManifestModel)).all()
        referenced = any(
            any(item["id"] == media_id for item in manifest.catalog.get("media", []))
            for manifest in retained
        )
        if row is None or not row.ready or not referenced:
            raise HTTPException(status_code=404, detail="Guide media not found")
        content = media_storage_client.get_object(object_key=row.object_key)
        return Response(
            content=content, media_type=row.mime_type, headers={"ETag": row.sha256}
        )
