"""Backend-primary fusion tracer tests."""

from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from uuid import uuid4

from main import app

client = TestClient(app)


def create_farmer_and_cattle():
    suffix = uuid4().hex[:8]
    farmer_response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": f"08123{suffix[:5]}", "name": "Fusion Farmer", "jurisdiction_id": "district-bandung-1"},
    )
    assert farmer_response.status_code == 200, farmer_response.text
    farmer = farmer_response.json()
    cattle_response = client.post(
        f"/api/farmers/{farmer['id']}/cattle",
        json={"tag": f"FUSION-{suffix}", "sex": "female", "breed": "sapi bali", "jurisdiction_id": "district-bandung-1", "age_months": 36},
    )
    assert cattle_response.status_code == 200, cattle_response.text
    cattle = cattle_response.json()
    return farmer["id"], cattle["id"]


def image(top_class="FMD", confidence=0.82, quality_status="accepted"):
    scores = {"healthy": 1 - confidence, "FMD": confidence}
    if top_class == "healthy":
        scores = {"healthy": confidence, "FMD": 1 - confidence}
    return {
        "source": "image",
        "model_version": "image-model-1.0.0",
        "inference_mode": "online",
        "disease_scores": scores,
        "top_class": top_class,
        "confidence": confidence,
        "quality_status": quality_status,
        "rejection_reasons": ["too_blurry"] if quality_status == "rejected" else [],
    }


def nlp(top_class="FMD", confidence=0.8):
    scores = {"healthy": 1 - confidence, "FMD": confidence}
    if top_class == "healthy":
        scores = {"healthy": confidence, "FMD": 1 - confidence}
    return {
        "source": "nlp",
        "model_version": "nlp-model-1.0.0",
        "inference_mode": "online",
        "questionnaire_answers": {"mouth_lesion": top_class == "FMD"},
        "notes_present": False,
        "disease_scores": scores,
        "top_class": top_class,
        "confidence": confidence,
        "evidence_terms": ["mouth_lesion"],
    }


def fuse(payload):
    response = client.post("/api/fusion/results", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_matching_medium_high_evidence_produces_reliable_result_and_stores_breakdown():
    farmer_id, cattle_id = create_farmer_and_cattle()

    result = fuse({"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": image(), "nlp_evidence": nlp()})

    assert result["disease_class"] == "FMD"
    assert result["reliability"] == "reliable"
    assert result["inference_mode"] == "hybrid"
    assert result["conflict_status"] == "none"
    assert result["confidence_level"] == "high"
    assert result["model_versions"] == {"image": "image-model-1.0.0", "nlp": "nlp-model-1.0.0"}
    assert result["evidence_breakdown"]["image"]["source"] == "image"
    assert result["evidence_breakdown"]["nlp"]["source"] == "nlp"
    assert "diagnosis" not in result["handling_advice_key"]


def test_fusion_result_cattle_association_can_be_changed():
    farmer_id, cattle_id = create_farmer_and_cattle()
    suffix = uuid4().hex[:8]
    second_cattle = client.post(
        f"/api/farmers/{farmer_id}/cattle",
        json={
            "tag": f"FUSION-NEW-{suffix}",
            "sex": "female",
            "breed": "sapi bali",
            "jurisdiction_id": "district-bandung-1",
            "age_months": 30,
        },
    )
    assert second_cattle.status_code == 200, second_cattle.text
    result = fuse(
        {
            "farmer_id": farmer_id,
            "cattle_id": cattle_id,
            "image_evidence": image(),
            "nlp_evidence": nlp(),
        }
    )

    updated = client.patch(
        f"/api/fusion/results/{result['id']}/cattle",
        json={"farmer_id": farmer_id, "cattle_id": second_cattle.json()["id"]},
    )

    assert updated.status_code == 200, updated.text
    assert updated.json()["id"] == result["id"]
    assert updated.json()["cattle_id"] == second_cattle.json()["id"]


def test_fusion_result_can_be_deleted():
    farmer_id, cattle_id = create_farmer_and_cattle()
    result = fuse(
        {
            "farmer_id": farmer_id,
            "cattle_id": cattle_id,
            "image_evidence": image(),
            "nlp_evidence": nlp(),
        }
    )

    deleted = client.delete(
        f"/api/fusion/results/{result['id']}", params={"farmer_id": farmer_id}
    )

    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"status": "deleted"}


def test_conflicting_top_classes_need_review():
    farmer_id, cattle_id = create_farmer_and_cattle()

    result = fuse({"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": image("FMD", 0.8), "nlp_evidence": nlp("healthy", 0.76)})

    assert result["conflict_status"] == "image_nlp_conflict"
    assert result["reliability"] == "needs_review"

def test_lsd_evidence_is_rejected_before_persistence():
    farmer_id, cattle_id = create_farmer_and_cattle()
    response = client.post(
        "/api/fusion/results",
        json={
            "farmer_id": farmer_id,
            "cattle_id": cattle_id,
            "image_evidence": {
                **image("FMD"),
                "disease_scores": {"FMD": 0.8, "healthy": 0.1, "LSD": 0.1},
            },
        },
    )

    assert response.status_code == 422


def test_missing_image_produces_low_reliability_nlp_result():
    farmer_id, cattle_id = create_farmer_and_cattle()

    result = fuse({"farmer_id": farmer_id, "cattle_id": cattle_id, "nlp_evidence": nlp("healthy", 0.7)})

    assert result["disease_class"] == "healthy"
    assert result["conflict_status"] == "missing_image"
    assert result["reliability"] == "low_reliability"
    assert result["model_versions"]["image"] == "missing"


def test_missing_nlp_produces_low_reliability_image_result():
    farmer_id, cattle_id = create_farmer_and_cattle()

    result = fuse({"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": image("FMD", 0.7)})

    assert result["disease_class"] == "FMD"
    assert result["conflict_status"] == "missing_nlp"
    assert result["reliability"] == "low_reliability"
    assert result["model_versions"]["nlp"] == "missing"


def test_low_confidence_evidence_produces_insufficient_evidence():
    farmer_id, cattle_id = create_farmer_and_cattle()

    result = fuse({"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": image("healthy", 0.55), "nlp_evidence": nlp("healthy", 0.55)})

    assert result["confidence_level"] == "low"
    assert result["reliability"] == "insufficient_evidence"


def test_low_quality_image_uses_nlp_but_marks_low_quality_conflict():
    farmer_id, cattle_id = create_farmer_and_cattle()

    result = fuse({"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": image("FMD", 0.82, "rejected"), "nlp_evidence": nlp("FMD", 0.78)})

    assert result["disease_class"] == "FMD"
    assert result["conflict_status"] == "low_quality_image"
    assert result["reliability"] == "low_reliability"
    assert result["evidence_breakdown"]["image"]["quality_status"] == "rejected"
