from tests.conftest import repo_text


def _read(path: str) -> str:
    return repo_text(path)


def test_region_ux_validation_protocol_keeps_farmer_boxes_gated():
    protocol = _read("docs/system-integration/validation/VALIDATION_PROTOCOL.md")

    assert "model attention area" in protocol
    assert "area to review" in protocol
    assert "developer/debug-only" in protocol
    assert "remain disabled" in protocol
    assert "not a confirmed lesion" in protocol or "not confirmed lesion" in protocol


def test_region_ux_capture_sheets_record_misleading_risk():
    metrics = _read("docs/system-integration/validation/METRICS_SHEET.md")
    report = _read("docs/system-integration/validation/REPORT_TEMPLATE.md")

    assert "detected lesion" in metrics
    assert "misleading" in metrics
    assert "overconfidence" in report
    assert "Gated farmer-facing trial" in report
    assert "This does not create clinical diagnosis claims" in report
