import io
import json
import runpy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient  # type: ignore[import-not-found]
from PIL import Image
from sqlalchemy import func, select  # type: ignore[import-not-found]

from api.authorization import refresh_agency_users
from api.database import DATABASE_URL, SessionLocal
from api.db_models import (
    GuideArticleModel,
    GuideEditorialAuditEventModel,
    GuideManifestModel,
    GuideMediaModel,
)
from api.guide_seed import ARTICLES, CATEGORIES, TIMESTAMP, seed_bundled_guide_catalog
from api.surface_auth import (
    DEFAULT_AGENCY_ADMIN_ID,
    DEFAULT_AGENCY_OFFICER_ID,
    issue_token,
    seed_default_agency_accounts,
    seed_default_farmer_accounts,
    surface_account_store,
)
from config import settings
from main import app


def _auth(account_type: str, email: str) -> str:
    account = surface_account_store.get(account_type=account_type, email=email)
    assert account is not None
    return f"Bearer {issue_token(account)}"


def _admin_headers(
    user_id: str = DEFAULT_AGENCY_ADMIN_ID, email: str | None = None
) -> dict[str, str]:
    return {
        "Authorization": _auth("agency", email or settings.master_admin_email),
        "X-Agency-User-Id": user_id,
    }


def _article(
    title: str = "Panduan Uji", category_id: str = "guide-category-umum"
) -> dict:
    return {
        "category_id": category_id,
        "translations": [
            {
                "locale": "id",
                "title": title,
                "summary": "Ringkasan aman",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "Pantau kondisi sapi dan hubungi petugas bila perlu.",
                    }
                ],
            }
        ],
    }


def setup_module() -> None:
    seed_default_agency_accounts()
    seed_default_farmer_accounts()
    refresh_agency_users()
    seed_bundled_guide_catalog()


def test_seed_is_idempotent_and_manifest_has_six_stable_documents() -> None:
    with SessionLocal() as session:
        before = session.scalar(select(func.count()).select_from(GuideManifestModel))
    seed_bundled_guide_catalog()
    seed_bundled_guide_catalog()
    with SessionLocal() as session:
        after = session.scalar(select(func.count()).select_from(GuideManifestModel))
        ids = set(
            session.scalars(
                select(GuideArticleModel.id).where(
                    GuideArticleModel.id.in_([row[0] for row in ARTICLES])
                )
            ).all()
        )
    assert ids == {row[0] for row in ARTICLES}
    assert after == before
    farmer = _auth("farmer", "farmer@example.com")
    body = (
        TestClient(app)
        .get("/api/guide/manifest", headers={"Authorization": farmer})
        .json()
    )
    assert len(body["documents"]["articles"]) >= 6
    assert all(
        len(item["sha256"]) == 64 and "url" in item
        for item in body["documents"]["articles"]
    )


def test_bundled_migration_and_runtime_seed_have_exact_parity() -> None:
    migration = runpy.run_path("apps/backend/alembic/versions/0020_guide_cms.py")
    assert migration["CATEGORIES"] == CATEGORIES
    assert migration["ARTICLES"] == ARTICLES
    assert migration["TIMESTAMP"] == TIMESTAMP
    bundle = json.loads(Path("apps/mobile/assets/guide/catalog.json").read_text())
    categories = {item["id"]: item for item in bundle["documents"]["categories"]}
    articles = {item["id"]: item for item in bundle["documents"]["articles"]}
    assert set(categories) == {item[0] for item in CATEGORIES}
    assert set(articles) == {item[0] for item in ARTICLES}
    for category_id, label, order, system_owned in CATEGORIES:
        category = categories[category_id]
        assert (
            category["translations"][0]["label"],
            category["display_order"],
            category["system_owned"],
        ) == (label, order, system_owned)
    for article_id, category_id, title, summary, paragraph in ARTICLES:
        article = articles[article_id]
        translation = article["translations"][0]
        assert (
            article["category_id"],
            translation["title"],
            translation["summary"],
            translation["blocks"],
            article["published_at"],
        ) == (
            category_id,
            title,
            summary,
            [{"type": "paragraph", "text": paragraph}],
            TIMESTAMP,
        )


def test_only_matching_global_admin_can_access_cms() -> None:
    client = TestClient(app)
    officer = _auth("agency", "semarang-officer@sapisehat.test")
    assert (
        client.get(
            "/api/agency/guide/articles",
            headers={"Authorization": officer, "X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/agency/guide/articles", headers=_admin_headers("wrong-id")
        ).status_code
        == 403
    )
    assert (
        client.get("/api/agency/guide/articles", headers=_admin_headers()).status_code
        == 200
    )


def test_unknown_block_type_and_fields_are_rejected() -> None:
    client = TestClient(app)
    bad_type = _article()
    bad_type["translations"][0]["blocks"] = [{"type": "html", "text": "<b>x</b>"}]
    bad_field = _article()
    bad_field["translations"][0]["blocks"] = [
        {"type": "paragraph", "text": "x", "href": "https://example.com"}
    ]
    assert (
        client.post(
            "/api/agency/guide/articles", headers=_admin_headers(), json=bad_type
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/agency/guide/articles", headers=_admin_headers(), json=bad_field
        ).status_code
        == 422
    )


def test_input_limits_are_enforced() -> None:
    client = TestClient(app)
    payloads = []
    for field, value in (("title", "x" * 161), ("summary", "x" * 501)):
        payload = _article()
        payload["translations"][0][field] = value
        payloads.append(payload)
    for blocks in (
        [{"type": "paragraph", "text": "x" * 4001}],
        [{"type": "bullet_list", "items": ["x"] * 31}],
        [{"type": "bullet_list", "items": ["x" * 501]}],
        [
            {"type": "image", "media_id": f"guide-media-{index}", "alt": "Sapi"}
            for index in range(11)
        ],
    ):
        payload = _article()
        payload["translations"][0]["blocks"] = blocks
        payloads.append(payload)
    assert all(
        client.post(
            "/api/agency/guide/articles", headers=_admin_headers(), json=payload
        ).status_code
        == 422
        for payload in payloads
    )


def test_publish_requires_indonesian_and_ready_media() -> None:
    client = TestClient(app)
    missing_id = _article()
    missing_id["translations"][0]["locale"] = "en"
    created = client.post(
        "/api/agency/guide/articles", headers=_admin_headers(), json=missing_id
    ).json()
    assert (
        client.post(
            f"/api/agency/guide/articles/{created['id']}/publish",
            headers=_admin_headers(),
        ).status_code
        == 422
    )
    image_article = _article()
    image_article["translations"][0]["blocks"] = [
        {"type": "image", "media_id": "guide-media-not-ready", "alt": "Sapi"}
    ]
    created = client.post(
        "/api/agency/guide/articles", headers=_admin_headers(), json=image_article
    ).json()
    assert (
        client.post(
            f"/api/agency/guide/articles/{created['id']}/publish",
            headers=_admin_headers(),
        ).status_code
        == 422
    )


def test_draft_edit_is_invisible_until_explicit_republish() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/agency/guide/articles",
        headers=_admin_headers(),
        json=_article("Versi satu"),
    ).json()
    assert (
        client.post(
            f"/api/agency/guide/articles/{created['id']}/publish",
            headers=_admin_headers(),
        ).status_code
        == 200
    )
    farmer_headers = {"Authorization": _auth("farmer", "farmer@example.com")}
    first = client.get("/api/guide/manifest", headers=farmer_headers).json()
    descriptor = next(
        item for item in first["documents"]["articles"] if item["id"] == created["id"]
    )
    assert (
        client.get(descriptor["url"], headers=farmer_headers).json()["translations"][0][
            "title"
        ]
        == "Versi satu"
    )
    before_version = first["version"]
    assert (
        client.put(
            f"/api/agency/guide/articles/{created['id']}",
            headers=_admin_headers(),
            json=_article("Versi dua"),
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/guide/manifest?version={before_version}", headers=farmer_headers
        ).json()["changed"]
        is False
    )
    assert (
        client.post(
            f"/api/agency/guide/articles/{created['id']}/publish",
            headers=_admin_headers(),
        ).status_code
        == 200
    )
    second = client.get(
        f"/api/guide/manifest?version={before_version}", headers=farmer_headers
    ).json()
    assert created["id"] in second["changed_document_ids"]
    descriptor = next(
        item for item in second["documents"]["articles"] if item["id"] == created["id"]
    )
    assert (
        client.get(descriptor["url"], headers=farmer_headers).json()["translations"][0][
            "title"
        ]
        == "Versi dua"
    )


def test_article_archive_hides_article_and_records_audit() -> None:
    client = TestClient(app)
    article = client.post(
        "/api/agency/guide/articles", headers=_admin_headers(), json=_article()
    ).json()
    client.post(
        f"/api/agency/guide/articles/{article['id']}/publish", headers=_admin_headers()
    )
    response = client.post(
        f"/api/agency/guide/articles/{article['id']}/archive",
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    assert response.json()["state"] == "archived"
    with SessionLocal() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(GuideEditorialAuditEventModel)
                .where(
                    GuideEditorialAuditEventModel.target_id == article["id"],
                    GuideEditorialAuditEventModel.action == "archive",
                )
            )
            == 1
        )


def test_unpublish_returns_tombstone_and_hides_article() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/agency/guide/articles", headers=_admin_headers(), json=_article()
    ).json()
    client.post(
        f"/api/agency/guide/articles/{created['id']}/publish", headers=_admin_headers()
    )
    farmer_headers = {"Authorization": _auth("farmer", "farmer@example.com")}
    old = client.get("/api/guide/manifest", headers=farmer_headers).json()
    client.post(
        f"/api/agency/guide/articles/{created['id']}/unpublish",
        headers=_admin_headers(),
    )
    delta = client.get(
        f"/api/guide/manifest?version={old['version']}", headers=farmer_headers
    ).json()
    assert created["id"] in delta["removed_document_ids"]
    assert created["id"] not in {item["id"] for item in delta["documents"]["articles"]}


def test_category_archive_preserves_published_copy_and_emits_one_manifest() -> None:
    client = TestClient(app)
    category = client.post(
        "/api/agency/guide/categories",
        headers=_admin_headers(),
        json={
            "display_order": 90,
            "translations": [{"locale": "id", "label": "Sementara"}],
        },
    ).json()
    article = client.post(
        "/api/agency/guide/articles",
        headers=_admin_headers(),
        json=_article("Versi satu", category["id"]),
    ).json()
    client.post(
        f"/api/agency/guide/articles/{article['id']}/publish", headers=_admin_headers()
    )
    client.put(
        f"/api/agency/guide/articles/{article['id']}",
        headers=_admin_headers(),
        json=_article("Versi dua", category["id"]),
    )
    with SessionLocal() as session:
        before = session.scalar(select(func.count()).select_from(GuideManifestModel))
    response = client.post(
        f"/api/agency/guide/categories/{category['id']}/archive",
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    with SessionLocal() as session:
        row = session.get(GuideArticleModel, article["id"])
        after = session.scalar(select(func.count()).select_from(GuideManifestModel))
        assert (
            row is not None
            and row.state == "published"
            and row.category_id == "guide-category-umum"
        )
        assert before is not None and after == before + 1
        actions = set(
            session.scalars(
                select(GuideEditorialAuditEventModel.action).where(
                    GuideEditorialAuditEventModel.target_id.in_(
                        [category["id"], article["id"]]
                    )
                )
            ).all()
        )
        assert {"archive", "category_move"} <= actions
        assert row.published_document is not None
        assert row.published_document["translations"][0]["title"] == "Versi satu"
        assert row.published_document["category_id"] == "guide-category-umum"
    farmer_headers = {"Authorization": _auth("farmer", "farmer@example.com")}
    manifest = client.get("/api/guide/manifest", headers=farmer_headers).json()
    descriptor = next(
        item
        for item in manifest["documents"]["articles"]
        if item["id"] == article["id"]
    )
    document = client.get(descriptor["url"], headers=farmer_headers).json()
    assert document["translations"][0]["title"] == "Versi satu"
    assert document["category_id"] == "guide-category-umum"


def test_active_category_mutations_each_emit_one_manifest() -> None:
    client = TestClient(app)
    with SessionLocal() as session:
        version = session.scalar(select(func.max(GuideManifestModel.version))) or 0
    created = client.post(
        "/api/agency/guide/categories",
        headers=_admin_headers(),
        json={
            "display_order": 91,
            "translations": [{"locale": "id", "label": "Kosong"}],
        },
    )
    assert created.status_code == 201
    category = created.json()
    farmer_headers = {"Authorization": _auth("farmer", "farmer@example.com")}
    after_create = client.get("/api/guide/manifest", headers=farmer_headers).json()
    assert after_create["version"] == version + 1
    created_descriptor = next(
        item
        for item in after_create["documents"]["categories"]
        if item["id"] == category["id"]
    )
    updated = client.put(
        f"/api/agency/guide/categories/{category['id']}",
        headers=_admin_headers(),
        json={
            "display_order": 3,
            "translations": [
                {"locale": "id", "label": "Berganti"},
                {"locale": "en", "label": "Renamed"},
            ],
        },
    )
    assert updated.status_code == 200
    after_update = client.get("/api/guide/manifest", headers=farmer_headers).json()
    assert after_update["version"] == version + 2
    updated_descriptor = next(
        item
        for item in after_update["documents"]["categories"]
        if item["id"] == category["id"]
    )
    assert updated_descriptor["sha256"] != created_descriptor["sha256"]
    archived = client.post(
        f"/api/agency/guide/categories/{category['id']}/archive",
        headers=_admin_headers(),
    )
    assert archived.status_code == 200
    after_archive = client.get("/api/guide/manifest", headers=farmer_headers).json()
    assert after_archive["version"] == version + 3
    assert category["id"] not in {
        item["id"] for item in after_archive["documents"]["categories"]
    }


def test_category_duplicate_locale_is_rejected() -> None:
    response = TestClient(app).post(
        "/api/agency/guide/categories",
        headers=_admin_headers(),
        json={
            "translations": [
                {"locale": "id", "label": "Satu"},
                {"locale": "id", "label": "Dua"},
            ]
        },
    )
    assert response.status_code == 422


def test_safe_language_is_checked_in_every_locale_and_text_field() -> None:
    client = TestClient(app)
    locations = [
        ("title", "confirmed diagnosis"),
        ("summary", "confirmed outbreak"),
        ("paragraph", "infected with FMD"),
        ("heading", "positive for FMD"),
        ("bullet_list", "positive for FMD"),
        ("image", "diagnosis terkonfirmasi"),
    ]
    for field, phrase in locations:
        payload = _article()
        translation = {
            "locale": "en",
            "title": "Safe title",
            "summary": "Educational summary",
            "blocks": [{"type": "paragraph", "text": "Contact animal health staff"}],
        }
        if field in {"title", "summary"}:
            translation[field] = phrase
        elif field in {"paragraph", "heading"}:
            translation["blocks"] = [{"type": field, "text": phrase}]
        elif field == "bullet_list":
            translation["blocks"] = [{"type": "bullet_list", "items": [phrase]}]
        else:
            translation["blocks"] = [
                {"type": "image", "media_id": "guide-media-missing", "alt": phrase}
            ]
        payload["translations"].append(translation)
        article = client.post(
            "/api/agency/guide/articles", headers=_admin_headers(), json=payload
        ).json()
        response = client.post(
            f"/api/agency/guide/articles/{article['id']}/publish",
            headers=_admin_headers(),
        )
        assert response.status_code == 422
    for phrase in (
        "indikasi awal",
        "sinyal risiko",
        "kemungkinan peningkatan risiko",
        "hubungi petugas kesehatan hewan",
        "hasil bukan diagnosis",
    ):
        article = client.post(
            "/api/agency/guide/articles",
            headers=_admin_headers(),
            json=_article(phrase),
        ).json()
        assert (
            client.post(
                f"/api/agency/guide/articles/{article['id']}/publish",
                headers=_admin_headers(),
            ).status_code
            == 200
        )


def test_admin_lists_and_farmer_reads_enforce_surface_authorization() -> None:
    client = TestClient(app)
    officer_headers = {
        "Authorization": _auth("agency", "semarang-officer@sapisehat.test"),
        "X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID,
    }
    for path in ("/api/agency/guide/media", "/api/agency/guide/audit-events"):
        assert client.get(path, headers=officer_headers).status_code == 403
        assert client.get(path, headers=_admin_headers()).status_code == 200
    farmer_headers = {"Authorization": _auth("farmer", "farmer@example.com")}
    manifest = client.get("/api/guide/manifest", headers=farmer_headers).json()
    descriptor = manifest["documents"]["categories"][0]
    assert client.get(descriptor["url"], headers=farmer_headers).status_code == 200
    agency_token = _auth("agency", settings.master_admin_email)
    assert (
        client.get(
            descriptor["url"], headers={"Authorization": agency_token}
        ).status_code
        == 403
    )
    unknown = client.get(
        "/api/guide/manifest?version=999999999", headers=farmer_headers
    ).json()
    expected = {
        item["id"]
        for kind in ("categories", "articles")
        for item in unknown["documents"][kind]
    }
    assert set(unknown["changed_document_ids"]) == expected


def test_media_mime_size_and_dimensions_are_validated(monkeypatch) -> None:
    client = TestClient(app)
    assert (
        client.post(
            "/api/agency/guide/media",
            headers=_admin_headers(),
            files={"file": ("large.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
        ).status_code
        == 413
    )
    output = io.BytesIO()
    Image.new("RGB", (8193, 1), "white").save(output, "PNG")
    assert (
        client.post(
            "/api/agency/guide/media",
            headers=_admin_headers(),
            files={"file": ("wide.png", output.getvalue(), "image/png")},
        ).status_code
        == 422
    )


def test_media_mime_must_match_and_draft_media_is_not_farmer_readable(
    monkeypatch,
) -> None:
    client = TestClient(app)
    output = io.BytesIO()
    Image.new("RGB", (20, 10), "white").save(output, "PNG")
    assert (
        client.post(
            "/api/agency/guide/media",
            headers=_admin_headers(),
            files={"file": ("fake.jpg", output.getvalue(), "image/jpeg")},
        ).status_code
        == 422
    )
    monkeypatch.setattr(
        "api.guide_cms.media_storage_client.put_object", lambda **_: "key"
    )
    uploaded = client.post(
        "/api/agency/guide/media",
        headers=_admin_headers(),
        files={"file": ("image.png", output.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 201
    media_id = uploaded.json()["id"]
    assert (
        client.get(
            f"/api/guide/media/{media_id}",
            headers={"Authorization": _auth("farmer", "farmer@example.com")},
        ).status_code
        == 404
    )


def test_admin_media_preview_requires_admin_and_returns_private_bytes(
    monkeypatch,
) -> None:
    with SessionLocal() as session:
        media = GuideMediaModel(
            id="guide-media-preview-test",
            object_key="cms/guides/preview.png",
            mime_type="image/png",
            width=2,
            height=2,
            byte_size=3,
            sha256="a" * 64,
            ready=True,
            created_at="2026-01-01T00:00:00+00:00",
        )
        session.merge(media)
        session.commit()
    monkeypatch.setattr(
        "api.guide_cms.media_storage_client.get_object", lambda **_: b"png"
    )
    client = TestClient(app)
    path = "/api/agency/guide/media/guide-media-preview-test/preview"
    farmer_headers = {"Authorization": _auth("farmer", "farmer@example.com")}
    officer = _auth("agency", "semarang-officer@sapisehat.test")
    assert client.get(path, headers=farmer_headers).status_code == 422
    assert (
        client.get(
            path,
            headers={
                "Authorization": officer,
                "X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID,
            },
        ).status_code
        == 403
    )
    response = client.get(path, headers=_admin_headers())
    assert response.status_code == 200
    assert response.content == b"png"
    assert response.headers["cache-control"] == "private, no-store"


def test_postgresql_concurrent_publications_are_complete_and_ordered() -> None:
    if not DATABASE_URL.startswith(("postgresql://", "postgresql+")):
        pytest.skip("PostgreSQL DATABASE_URL is not configured")

    def create_and_publish(index: int) -> int:
        with TestClient(app) as client:
            article = client.post(
                "/api/agency/guide/articles",
                headers=_admin_headers(),
                json=_article(f"Concurrent {index}"),
            ).json()
            return client.post(
                f"/api/agency/guide/articles/{article['id']}/publish",
                headers=_admin_headers(),
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(create_and_publish, range(2)))
    assert statuses == [200, 200]
    with SessionLocal() as session:
        versions = session.scalars(
            select(GuideManifestModel.version).order_by(GuideManifestModel.version)
        ).all()
        manifests = session.scalars(
            select(GuideManifestModel)
            .order_by(GuideManifestModel.version.desc())
            .limit(2)
        ).all()
    assert len(versions) == len(set(versions)) and versions == sorted(versions)
    assert len(manifests) == 2
    assert all(
        manifest.catalog["documents"]["categories"]
        and manifest.catalog["documents"]["articles"]
        and manifest.catalog["document_store"]["categories"]
        and manifest.catalog["document_store"]["articles"]
        for manifest in manifests
    )
