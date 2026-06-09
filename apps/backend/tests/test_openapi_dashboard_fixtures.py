"""OpenAPI/dashboard contract fixture checks."""

from pathlib import Path
import json


def test_dashboard_fixture_mentions_backend_contracts():
    path = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "dashboard_api_contract.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert "/api/agency/detection-monitoring" in data["paths"]
    assert "/api/agency/risk-signals" in data["paths"]
    assert "/api/farmers/{farmer_id}/area-advisory" in data["paths"]
    assert "/api/evidence/nlp/placeholder" in data["paths"]
    assert "/api/agency/audit-logs" in data["paths"]
