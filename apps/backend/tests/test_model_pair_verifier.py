"""Focused contract checks for the candidate model-pair verifier."""

from model.verification.verify_model_pair import (
    _repository_root,
    validate_manifest,
    verify_runtime_case,
)

from tests.conftest import REPO_ROOT, repo_file

ROOT = REPO_ROOT
MANIFEST = repo_file("apps/backend/model/verification/golden_corpus_manifest.json")


def test_manifest_records_passed_smoke_and_rejects_corrupt_fixture():
    report = validate_manifest(MANIFEST, repo_root=ROOT)

    if report["artifacts"].get("tflite", {}).get("exists"):
        assert report["gates"]["artifact_checksums"] is True
        assert report["gates"]["tensor_contract_declaration"] is True
    else:
        assert report["gates"]["artifact_checksums"] is False
        assert report["gates"]["metadata_pair_contract"] is False
        assert any("mobile model metadata" in blocker for blocker in report["blockers"])
    assert report["gates"]["corrupt_input_fixture"] is True
    assert report["gates"]["class_identity_provenance"] is True
    assert report["gates"]["corpus_source_permissions"] is True
    assert report["gates"]["physical_android_offline_smoke"] is True
    assert report["gates"]["metadata_activation_status"] is True
    assert report["activation_ready"] is False
    assert "runtime tensor contract has not passed" in report["blockers"]

    former_lsd = [case for case in report["cases"] if case["category"] == "former_lsd"]
    assert len(former_lsd) == 4
    assert all(case["expected_label"] is None for case in former_lsd)
    assert any(case["source_label"] == "LSD" for case in former_lsd)

    limitation = next(
        case for case in report["cases"] if case["id"] == "non-cattle-human-02"
    )
    assert limitation["accepted_limitation"]["option"] == "C"
    assert limitation["accepted_limitation"]["observed_label"] == "FMD"

    corrupt = [
        case for case in report["corrupt_fixtures"] if case["id"] == "corrupt-01"
    ]
    assert len(corrupt) == 1
    assert corrupt[0]["decode_status"] == "rejected_before_inference"
    assert corrupt[0]["model_invocations"] == 0


def test_backend_only_root_is_discovered_without_mobile_tree(tmp_path):
    backend_root = tmp_path / "backend"
    verification_dir = backend_root / "model" / "verification"
    verification_dir.mkdir(parents=True)
    (backend_root / "model" / "metadata.json").write_text("{}")
    manifest = verification_dir / "golden_corpus_manifest.json"
    manifest.write_text(
        '{"cases": [], "class_identity_manifest": '
        '"model/verification/class_identity_manifest.json"}'
    )
    (verification_dir / "class_identity_manifest.json").write_text("{}")

    assert _repository_root(manifest) == backend_root
    report = validate_manifest(manifest)

    assert report["activation_ready"] is False
    assert report["artifact_status"] == "pending"


def test_corrupt_fixture_is_rejected_before_runtime_invocation():
    calls = []
    case = {
        "id": "corrupt-01",
        "category": "corrupt",
        "path": "apps/backend/tests/assets/corrupt-image.bin",
    }

    def predictor(_batch):
        calls.append(True)
        return [0.1, 0.8, 0.1]

    result = verify_runtime_case(ROOT, case, predictor, predictor)

    assert result["decode_status"] == "rejected_before_inference"
    assert result["model_invocations"] == 0
    assert calls == []
