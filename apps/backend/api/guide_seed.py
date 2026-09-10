"""Stable Bundled Guide Catalog records shared with Flutter."""

from __future__ import annotations

from sqlalchemy import func, select  # type: ignore[import-not-found]

from api.database import SessionLocal, create_all_tables
from api.db_models import (
    GuideArticleModel,
    GuideArticleTranslationModel,
    GuideCategoryModel,
    GuideCategoryTranslationModel,
    GuideManifestModel,
)

from .guide_publication import article_document, build_manifest, now

UMUM_CATEGORY_ID = "guide-category-umum"
TIMESTAMP = "2026-01-01T00:00:00+00:00"
CATEGORIES = (
    (UMUM_CATEGORY_ID, "Umum", 0, True),
    ("guide-category-penggunaan", "Penggunaan", 10, False),
    ("guide-category-pmk", "PMK", 20, False),
    ("guide-category-sapi-sehat", "Sapi Sehat", 30, False),
)
ARTICLES = (
    (
        "guide-article-scan-pertama",
        "guide-category-penggunaan",
        "Memulai Scan Pertama",
        "Panduan menggunakan fitur scan untuk melihat sinyal risiko pada sapi.",
        "Buka tab Scan, arahkan kamera ke sapi, lalu ambil foto. Gunakan jarak 1-2 meter, pencahayaan cukup, dan posisi sejajar tubuh sapi.\n\nHasil menampilkan sinyal risiko, confidence score, dan saran tindakan awal. Hasil bukan diagnosis dokter hewan.",
    ),
    (
        "guide-article-mode-offline",
        "guide-category-penggunaan",
        "Mode Online vs Offline",
        "Perbedaan mode inferensi online dan offline.",
        "Mode online memakai server untuk analisis saat internet tersedia. Mode offline memakai model di perangkat ketika koneksi tidak tersedia.\n\nHasil offline disimpan dan dapat disinkronkan saat perangkat kembali online.",
    ),
    (
        "guide-article-mengenal-pmk",
        "guide-category-pmk",
        "Mengenal PMK",
        "Informasi dasar Penyakit Mulut dan Kuku.",
        "PMK adalah penyakit menular pada hewan berkuku belah. Tanda yang dapat terlihat antara lain demam, air liur berlebih, lepuh pada mulut atau kaki, dan pincang.\n\nHubungi petugas kesehatan hewan untuk pemeriksaan lebih lanjut.",
    ),
    (
        "guide-article-pencegahan-pmk",
        "guide-category-pmk",
        "Pencegahan PMK",
        "Biosekuriti dan tindakan awal yang aman.",
        "Pisahkan sapi yang menunjukkan gejala, batasi lalu lintas orang dan ternak, bersihkan serta desinfeksi kandang, dan gunakan alas kaki khusus.\n\nLakukan vaksinasi sesuai arahan petugas kesehatan hewan.",
    ),
    (
        "guide-article-sapi-sehat",
        "guide-category-sapi-sehat",
        "Ciri-Ciri Sapi Sehat",
        "Tanda umum sapi sehat sebagai bahan pemantauan.",
        "Sapi yang sehat umumnya aktif, memiliki nafsu makan baik, mata cerah, bulu dan kulit bersih, serta bergerak normal tanpa pincang.\n\nPantau perubahan perilaku, makan, dan gerak sebagai sinyal untuk tindak lanjut.",
    ),
    (
        "guide-article-biosekuriti",
        "guide-category-sapi-sehat",
        "Biosekuriti Harian",
        "Rutinitas menjaga kesehatan ternak.",
        "Bersihkan kandang, sediakan air bersih, batasi pengunjung, gunakan alas kaki khusus, karantina ternak baru, dan catat kesehatan sapi.",
    ),
)


def seed_bundled_guide_catalog() -> None:
    """Insert deterministic records only when each stable ID is absent."""
    create_all_tables()
    with SessionLocal() as session:
        for category_id, label, order, system_owned in CATEGORIES:
            if session.get(GuideCategoryModel, category_id) is None:
                session.add(
                    GuideCategoryModel(
                        id=category_id,
                        state="active",
                        system_owned=system_owned,
                        display_order=order,
                        created_at=now(),
                        updated_at=now(),
                    )
                )
                session.add(
                    GuideCategoryTranslationModel(
                        id=f"{category_id}:id",
                        category_id=category_id,
                        locale="id",
                        label=label,
                    )
                )
        session.flush()
        for article_id, category_id, title, summary, paragraph in ARTICLES:
            if session.get(GuideArticleModel, article_id) is None:
                article = GuideArticleModel(
                    id=article_id,
                    category_id=category_id,
                    state="published",
                    published_at=TIMESTAMP,
                    published_document=None,
                    created_at=TIMESTAMP,
                    updated_at=TIMESTAMP,
                )
                session.add(article)
                session.add(
                    GuideArticleTranslationModel(
                        id=f"{article_id}:id",
                        article_id=article_id,
                        locale="id",
                        title=title,
                        summary=summary,
                        blocks=[{"type": "paragraph", "text": paragraph}],
                    )
                )
        session.flush()
        for article_id, *_ in ARTICLES:
            article = session.get(GuideArticleModel, article_id)
            if article is not None and article.published_document is None:
                article.published_document = article_document(session, article)
        if session.scalar(select(func.count()).select_from(GuideManifestModel)) == 0:
            build_manifest(session)
        session.commit()
