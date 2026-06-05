"""Legacy docs framing tests."""

from pathlib import Path


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_readme_describes_platform_not_image_only_app():
    text = read("README.md")

    assert "platform early detection penyakit sapi" in text
    assert "bukti image Team 1" in text
    assert "bukti NLP Team 2" in text
    assert "dashboard agency" in text
    assert "docs/system-integration/README.md" in text
    assert "docs/system-integration/product/PRD-platform-rebuild.md" in text
    assert "Aplikasi Android untuk deteksi penyakit sapi" not in text
    assert "return diagnosis" not in text


def test_current_docs_have_platform_contract_pointers():
    files = [
        "docs/system-integration/product/PRD-platform-rebuild.md",
        "docs/system-integration/product/PLATFORM_SCOPE.md",
        "docs/system-integration/mobile/mobile-full-version-spec.md",
        "docs/team-1-image/backend/README.md",
        "docs/system-integration/backend/development.md",
        "docs/team-1-image/model/README.md",
        "apps/backend/model/README.md",
        "apps/mobile/SMOKE_TEST_CHECKLIST.md",
        "apps/mobile/TFLITE_PARITY.md",
    ]

    for file in files:
        text = read(file)[:1200]
        assert any(marker in text.lower() for marker in ["platform", "team 1 image subsystem", "system-integration", "shared backend direction", "image tracer"])
        assert any(marker in text.lower() for marker in ["system-integration", "docs/system-integration", "platform", "shared backend direction", "image tracer"])


def test_reviewed_docs_do_not_claim_product_is_only_image_app():
    reviewed = [
        "README.md",
        "docs/system-integration/product/PRD-platform-rebuild.md",
        "docs/system-integration/product/PLATFORM_SCOPE.md",
        "docs/system-integration/mobile/mobile-full-version-spec.md",
        "docs/team-1-image/backend/README.md",
        "docs/team-1-image/model/README.md",
    ]
    banned = [
        "Aplikasi Android untuk deteksi penyakit sapi",
        "only image classification app",
        "image-only Android app scope",
    ]

    for file in reviewed:
        text = read(file)
        for phrase in banned:
            assert phrase not in text
