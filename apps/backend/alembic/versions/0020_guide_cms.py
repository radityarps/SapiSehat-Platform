"""add Guide Article CMS with deterministic bundled seed

Revision ID: 0020_guide_cms
Revises: 0019_remove_google_login
"""

import sqlalchemy as sa  # type: ignore[import-not-found]
from alembic import op  # type: ignore[attr-defined]

revision = "0020_guide_cms"
down_revision = "0019_remove_google_login"
branch_labels = None
depends_on = None

CATEGORIES = (
    ("guide-category-umum", "Umum", 0, True),
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
TIMESTAMP = "2026-01-01T00:00:00+00:00"


def upgrade() -> None:
    op.create_table(
        "guide_categories",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("system_owned", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(80), nullable=False),
        sa.Column("updated_at", sa.String(80), nullable=False),
        sa.CheckConstraint(
            "state IN ('active', 'archived')", name="ck_guide_categories_state"
        ),
    )
    op.create_table(
        "guide_category_translations",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "category_id",
            sa.String(80),
            sa.ForeignKey("guide_categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("label", sa.String(80), nullable=False),
        sa.UniqueConstraint("category_id", "locale", name="uq_guide_category_locale"),
    )
    op.create_table(
        "guide_articles",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column(
            "category_id",
            sa.String(80),
            sa.ForeignKey("guide_categories.id"),
            nullable=False,
        ),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("published_at", sa.String(80)),
        sa.Column("published_document", sa.JSON()),
        sa.Column("created_at", sa.String(80), nullable=False),
        sa.Column("updated_at", sa.String(80), nullable=False),
        sa.CheckConstraint(
            "state IN ('draft', 'published', 'unpublished', 'archived')",
            name="ck_guide_articles_state",
        ),
    )
    op.create_table(
        "guide_article_translations",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "article_id",
            sa.String(80),
            sa.ForeignKey("guide_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("blocks", sa.JSON(), nullable=False),
        sa.UniqueConstraint("article_id", "locale", name="uq_guide_article_locale"),
    )
    op.create_table(
        "guide_media",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(40), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("ready", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.String(80), nullable=False),
        sa.CheckConstraint(
            "mime_type IN ('image/jpeg', 'image/png', 'image/webp')",
            name="ck_guide_media_type",
        ),
        sa.CheckConstraint(
            "byte_size >= 0 AND width > 0 AND height > 0",
            name="ck_guide_media_dimensions",
        ),
    )
    op.create_table(
        "guide_manifests",
        sa.Column("version", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("created_at", sa.String(80), nullable=False),
        sa.Column("catalog", sa.JSON(), nullable=False),
    )
    op.create_table(
        "guide_editorial_audit_events",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("actor_id", sa.String(120), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.String(80), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(80), nullable=False),
    )

    category_table = sa.table(
        "guide_categories",
        sa.column("id", sa.String),
        sa.column("state", sa.String),
        sa.column("system_owned", sa.Boolean),
        sa.column("display_order", sa.Integer),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )
    category_translation = sa.table(
        "guide_category_translations",
        sa.column("id", sa.String),
        sa.column("category_id", sa.String),
        sa.column("locale", sa.String),
        sa.column("label", sa.String),
    )
    article_table = sa.table(
        "guide_articles",
        sa.column("id", sa.String),
        sa.column("category_id", sa.String),
        sa.column("state", sa.String),
        sa.column("published_at", sa.String),
        sa.column("published_document", sa.JSON),
        sa.column("created_at", sa.String),
        sa.column("updated_at", sa.String),
    )
    article_translation = sa.table(
        "guide_article_translations",
        sa.column("id", sa.String),
        sa.column("article_id", sa.String),
        sa.column("locale", sa.String),
        sa.column("title", sa.String),
        sa.column("summary", sa.String),
        sa.column("blocks", sa.JSON),
    )
    op.bulk_insert(
        category_table,
        [
            {
                "id": category_id,
                "state": "active",
                "system_owned": system_owned,
                "display_order": order,
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            }
            for category_id, _, order, system_owned in CATEGORIES
        ],
    )
    op.bulk_insert(
        category_translation,
        [
            {
                "id": f"{category_id}:id",
                "category_id": category_id,
                "locale": "id",
                "label": label,
            }
            for category_id, label, _, _ in CATEGORIES
        ],
    )
    documents = []
    for article_id, category_id, title, summary, paragraph in ARTICLES:
        document = {
            "id": article_id,
            "category_id": category_id,
            "state": "published",
            "published_at": TIMESTAMP,
            "translations": [
                {
                    "locale": "id",
                    "title": title,
                    "summary": summary,
                    "blocks": [{"type": "paragraph", "text": paragraph}],
                }
            ],
        }
        documents.append(
            {
                "id": article_id,
                "category_id": category_id,
                "state": "published",
                "published_at": TIMESTAMP,
                "published_document": document,
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            }
        )
    op.bulk_insert(article_table, documents)
    op.bulk_insert(
        article_translation,
        [
            {
                "id": f"{article_id}:id",
                "article_id": article_id,
                "locale": "id",
                "title": title,
                "summary": summary,
                "blocks": [{"type": "paragraph", "text": paragraph}],
            }
            for article_id, _, title, summary, paragraph in ARTICLES
        ],
    )


def downgrade() -> None:
    for table in (
        "guide_editorial_audit_events",
        "guide_manifests",
        "guide_media",
        "guide_article_translations",
        "guide_articles",
        "guide_category_translations",
        "guide_categories",
    ):
        op.drop_table(table)
