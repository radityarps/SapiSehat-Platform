"""NLP placeholder must be explicit and side-effect free."""

from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from api.fusion_results import fusion_result_store
from api.risk_signals import cluster_risk_signal_store

client = TestClient(app)


def create_farmer_and_cattle():
    suffix = uuid4().hex[:8]
    farmer = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08777{suffix[:5]}",
            "name": "NLP Placeholder Farmer",
            "jurisdiction_id": "tembalang",
            "consent_state": "agency_monitoring",
        },
    ).json()
    cattle = client.post(
        f"/api/farmers/{farmer['id']}/cattle",
        json={
            "tag": f"NLP-{suffix}",
            "sex": "female",
            "breed": "sapi bali",
            "age_months": 20,
            "jurisdiction_id": "tembalang",
        },
    )
    assert cattle.status_code == 200, cattle.text
    return farmer["id"], cattle.json()["id"]


def test_nlp_placeholder_returns_unavailable_without_scores_or_side_effects():
    fusion_result_store.clear()
    cluster_risk_signal_store.clear()
    farmer_id, cattle_id = create_farmer_and_cattle()

    response = client.post(
        "/api/evidence/nlp/placeholder",
        json={
            "farmer_id": farmer_id,
            "cattle_id": cattle_id,
            "symptom_text": "mouth lesion and fever noted by farmer",
            "questionnaire_answers": {"mouth_lesion": True},
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "status": "unavailable",
        "evidence_state": "nlp_unavailable",
        "accepted_for_fusion": False,
        "creates_review_item": False,
        "creates_risk_signal": False,
        "message": "Team 2 NLP evidence is not available yet. This placeholder does not produce scores or affect fusion, review items, or risk signals.",
    }
    assert "disease_scores" not in body
    assert fusion_result_store.list_all() == []
    assert cluster_risk_signal_store.list_all() == []
