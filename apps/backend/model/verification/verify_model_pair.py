"""Verify the active Keras/TFLite model pair and its golden corpus.

The verifier is deliberately fail-closed: runtime parity is not enough to
activate a model when the producer has not supplied class-index provenance or
corpus permissions. It never infers a label mapping from predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

RAW_CLASSES = ("non_sapi", "pmk", "sehat")
MODEL_LABEL_MAPPING = {
    "non_sapi": "non_cattle",
    "pmk": "FMD",
    "sehat": "healthy",
}
CANONICAL_CLASSES = tuple(MODEL_LABEL_MAPPING[label] for label in RAW_CLASSES)
EXPECTED_CLASS_INDICES = {str(index): label for index, label in enumerate(RAW_CLASSES)}
EXPECTED_INPUT_SHAPE = (1, 224, 224, 3)
EXPECTED_OUTPUT_SHAPE = (1, 3)
SCORE_TOLERANCE = 2e-6
EXPECTED_RESCALE_SCALE = 1 / 127.5
EXPECTED_RESCALE_OFFSET = -1.0
PLACEHOLDER_VALUES = {"", "not supplied", "unknown", "pending", "null", "none"}
TEAM_OWNED_LABEL_SOURCE = "owner_approved_project_label"
TEAM_OWNED_SOURCE_URL = "not applicable; team-owned corpus"
TEAM_OWNED_LICENSE = "not asserted; team-owned corpus"
TEAM_OWNED_PERMISSION = "team-owned; owner-approved for this personal repository"

REQUIRED_VERIFICATION_GATES = (
    "metadata_pair_contract",
    "metadata_activation_status",
    "artifact_checksums",
    "tensor_contract_declaration",
    "runtime_tensor_contract",
    "finite_probability_contract",
    "valid_image_top_class_parity",
    "score_tolerance",
    "labeled_corpus_expectations",
    "corpus_label_provenance",
    "corpus_file_integrity",
    "corrupt_input_fixture",
    "former_lsd_policy",
    "class_identity_provenance",
    "corpus_source_permissions",
    "physical_android_offline_smoke",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        if path.is_file():
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()
        if not path.is_dir():
            return ""
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(child.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            with child.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _is_full_repository(root: Path) -> bool:
    return (root / "apps/backend").is_dir() and (root / "apps/mobile").is_dir()


def _path(root: Path, value: str) -> Path:
    """Resolve a manifest path within either supported repository layout."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Manifest path must be a non-empty string")
    candidate = Path(value)
    resolved_root = root.resolve()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        relative = candidate
        if not _is_full_repository(resolved_root) and relative.parts[:2] == (
            "apps",
            "backend",
        ):
            relative = Path(*relative.parts[2:])
        resolved = (resolved_root / relative).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {value}") from exc
    return resolved


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _repository_root(start: Path) -> Path:
    """Find a full monorepo or backend-only root from a verifier path."""
    start = start.resolve()
    candidates = (start, *start.parents)
    for candidate in candidates:
        if _is_full_repository(candidate):
            return candidate
    for candidate in candidates:
        if (candidate / "model/verification").is_dir() and (
            candidate / "model/metadata.json"
        ).is_file():
            return candidate
    raise ValueError(f"Could not find repository root from {start}")


def _metadata_pair_gate(root: Path) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    backend_path = _path(root, "apps/backend/model/metadata.json")
    mobile_path = _path(root, "apps/mobile/assets/model/model_metadata.json")
    metadata: dict[str, Any] = {"backend": {}, "mobile": {}}
    for name, path in (("backend", backend_path), ("mobile", mobile_path)):
        if not path.is_file():
            errors.append(f"{name} model metadata file is missing: {path}")
            continue
        try:
            metadata[name] = _json(path)
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        return False, errors, metadata

    backend = metadata["backend"]
    mobile = metadata["mobile"]
    backend_version = backend.get("model_version")
    mobile_version = mobile.get("model_version")
    if not isinstance(backend_version, str) or not backend_version.strip():
        errors.append("backend model version is missing")
    if not isinstance(mobile_version, str) or not mobile_version.strip():
        errors.append("Flutter model version is missing")
    if backend_version != mobile_version:
        errors.append("backend and Flutter model versions differ")
    backend_base_version = backend.get("base_model_version")
    mobile_base_version = mobile.get("base_model_version")
    if not isinstance(backend_base_version, str) or not backend_base_version.strip():
        errors.append("backend base model version is missing")
    if not isinstance(mobile_base_version, str) or not mobile_base_version.strip():
        errors.append("Flutter base model version is missing")
    if backend_base_version != mobile_base_version:
        errors.append("backend and Flutter base model versions differ")
    if backend.get("class_order") != list(RAW_CLASSES):
        errors.append("backend raw class order is not the model contract")
    if mobile.get("class_order") != list(RAW_CLASSES):
        errors.append("Flutter raw class order is not the model contract")
    if backend.get("label_mapping") != MODEL_LABEL_MAPPING:
        errors.append("backend canonical label mapping is invalid")
    if mobile.get("label_mapping") != MODEL_LABEL_MAPPING:
        errors.append("Flutter canonical label mapping is invalid")
    if backend.get("class_indices") != EXPECTED_CLASS_INDICES:
        errors.append("backend class indices are not the active contract")
    if mobile.get("class_indices") != EXPECTED_CLASS_INDICES:
        errors.append("Flutter class indices are not the active contract")
    if (
        not isinstance(backend.get("architecture"), str)
        or not backend["architecture"].strip()
    ):
        errors.append("backend model architecture is missing")
    if mobile.get("architecture") != backend.get("architecture"):
        errors.append("backend and Flutter model architectures differ")
    for field, label in (
        ("keras_artifact", "Keras"),
        ("tflite_artifact", "TFLite"),
    ):
        value = backend.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"backend {label} artifact filename is missing")
    if not isinstance(mobile.get("asset"), str) or not mobile["asset"].strip():
        errors.append("Flutter TFLite artifact filename is missing")
    if backend.get("tflite_artifact") != mobile.get("asset"):
        errors.append("backend and Flutter TFLite artifact filenames differ")
    if backend.get("tflite_sha256") != mobile.get("sha256"):
        errors.append("backend and Flutter TFLite checksums differ")

    statuses = {backend.get("artifact_status"), mobile.get("artifact_status")}
    if statuses != {"pending"} and statuses != {"verified"}:
        errors.append("backend and Flutter artifact statuses must agree")
    for name, metadata in (("backend", backend), ("Flutter", mobile)):
        verification = metadata.get("verification")
        if not isinstance(verification, dict):
            errors.append(f"{name} verification metadata is missing")

    preprocessing_errors = _preprocessing_errors(
        "backend", backend.get("preprocessing")
    )
    preprocessing_errors.extend(
        _preprocessing_errors("Flutter", mobile.get("preprocessing"))
    )
    errors.extend(preprocessing_errors)

    backend_tensor = backend.get("tensor_contract", {})
    mobile_tensor = mobile.get("tensor_contract", {})
    if not isinstance(backend_tensor, dict):
        errors.append("backend tensor contract is missing")
        backend_tensor = {}
    if not isinstance(mobile_tensor, dict):
        errors.append("Flutter tensor contract is missing")
        mobile_tensor = {}
    expected_backend_tensor = {
        "keras_input_tensor_count": 1,
        "keras_output_tensor_count": 1,
        "keras_input_shape": [None, 224, 224, 3],
        "keras_output_shape": [None, 3],
        "keras_input_dtype": "float32",
        "keras_output_dtype": "float32",
        "tflite_input_tensor_count": 1,
        "tflite_output_tensor_count": 1,
        "tflite_input_shape": [1, 224, 224, 3],
        "tflite_output_shape": [1, 3],
        "tflite_input_dtype": "float32",
        "tflite_output_dtype": "float32",
    }
    expected_mobile_tensor = {
        "input_tensor_count": 1,
        "output_tensor_count": 1,
        "input_shape": [1, 224, 224, 3],
        "output_shape": [1, 3],
        "input_dtype": "float32",
        "output_dtype": "float32",
    }
    for key, value in expected_backend_tensor.items():
        if backend_tensor.get(key) != value:
            errors.append(f"backend tensor contract mismatch: {key}")
    for key, value in expected_mobile_tensor.items():
        if mobile_tensor.get(key) != value:
            errors.append(f"Flutter tensor contract mismatch: {key}")

    return not errors, errors, {"backend": backend, "mobile": mobile}


def _preprocessing_errors(name: str, preprocessing: Any) -> list[str]:
    if not isinstance(preprocessing, dict):
        return [f"{name} preprocessing metadata is missing"]
    errors: list[str] = []
    if preprocessing.get("input_size") != [224, 224]:
        errors.append(f"{name} input size is not [224, 224]")
    if preprocessing.get("channels") != 3 or preprocessing.get("color_mode") != "RGB":
        errors.append(f"{name} preprocessing is not RGB with three channels")
    if preprocessing.get("resize_method") != "bilinear":
        errors.append(f"{name} resize method is not bilinear")
    if preprocessing.get("input_range") != [0, 255]:
        errors.append(f"{name} input range is not [0, 255]")
    if preprocessing.get("input_dtype") != "float32":
        errors.append(f"{name} input dtype is not float32")
    if not isinstance(
        preprocessing.get("internal_rescaling"), bool
    ) or not preprocessing.get("internal_rescaling"):
        errors.append(f"{name} does not declare internal rescaling")
    scale_value = preprocessing.get("internal_rescaling_scale")
    offset_value = preprocessing.get("internal_rescaling_offset")
    try:
        scale_ok = math.isclose(
            float(scale_value)
            if isinstance(scale_value, (int, float, str))
            else math.nan,
            EXPECTED_RESCALE_SCALE,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        offset_ok = math.isclose(
            float(offset_value)
            if isinstance(offset_value, (int, float, str))
            else math.nan,
            EXPECTED_RESCALE_OFFSET,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    except (TypeError, ValueError, OverflowError):
        scale_ok = offset_ok = False
    if not scale_ok or not offset_ok:
        errors.append(f"{name} internal rescaling does not match the contract")
    if preprocessing.get("exif_orientation_correction") in (None, False):
        errors.append(f"{name} EXIF orientation correction is not declared")
    return errors


def _metadata_activation_gate(metadata: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    backend = metadata.get("backend", {})
    mobile = metadata.get("mobile", {})
    if not isinstance(backend, dict) or not isinstance(mobile, dict):
        return False, ["backend and Flutter metadata are unavailable"]
    statuses = {backend.get("artifact_status"), mobile.get("artifact_status")}
    if statuses != {"verified"}:
        errors.append("model artifacts are not marked verified")
    for name, value in (("backend", backend), ("Flutter", mobile)):
        verification = value.get("verification")
        if (
            not isinstance(verification, dict)
            or not isinstance(verification.get("overall_pass"), bool)
            or not verification.get("overall_pass")
        ):
            errors.append(f"{name} verification overall_pass is not true")
    return not errors, errors


def _artifact_gate(
    root: Path, manifest: dict[str, Any], metadata: dict[str, Any]
) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    artifacts: dict[str, Any] = {}
    backend = metadata.get("backend", {})
    mobile = metadata.get("mobile", {})
    if not isinstance(backend, dict) or not isinstance(mobile, dict):
        return False, ["metadata pair is unavailable"], artifacts
    declarations = {
        "keras": (backend.get("keras_artifact"), backend.get("keras_sha256")),
        "tflite": (mobile.get("asset"), mobile.get("sha256")),
    }
    manifest_artifacts = manifest.get("artifacts", {})
    if not isinstance(manifest_artifacts, dict):
        return False, ["manifest artifacts must be an object"], artifacts

    for name, (declared_path, declared_hash) in declarations.items():
        manifest_entry = manifest_artifacts.get(name, {})
        if not isinstance(manifest_entry, dict):
            errors.append(f"manifest artifact declaration is incomplete: {name}")
            continue
        relative_path = manifest_entry.get("path")
        expected_hash = manifest_entry.get("sha256")
        if (
            not isinstance(relative_path, str)
            or not relative_path.strip()
            or not isinstance(expected_hash, str)
            or not expected_hash.strip()
        ):
            errors.append(f"manifest artifact declaration is incomplete: {name}")
            continue
        if declared_hash != expected_hash:
            errors.append(f"metadata and manifest hashes differ: {name}")
        if manifest_entry.get("model_version") != backend.get("model_version"):
            errors.append(f"manifest model version differs: {name}")
        try:
            artifact = _path(root, relative_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        is_expected_type = (
            artifact.is_file()
            if name == "tflite"
            else artifact.is_file() or artifact.is_dir()
        )
        if not is_expected_type:
            errors.append(f"artifact type is invalid or missing: {relative_path}")
        actual_hash = _sha256(artifact)
        matches = (
            is_expected_type and bool(actual_hash) and actual_hash == expected_hash
        )
        artifacts[name] = {
            "path": relative_path,
            "exists": artifact.exists(),
            "sha256": actual_hash,
            "expected_sha256": expected_hash,
            "matches": matches,
        }
        if not matches:
            errors.append(f"artifact checksum mismatch or missing: {relative_path}")
        if (
            not isinstance(declared_path, str)
            or Path(declared_path).name != artifact.name
        ):
            errors.append(f"metadata artifact filename differs: {name}")

    if backend.get("tflite_artifact") != mobile.get("asset"):
        errors.append("backend and Flutter TFLite artifact declarations differ")
    if backend.get("tflite_sha256") != mobile.get("sha256"):
        errors.append("backend and Flutter TFLite checksum declarations differ")
    return not errors, errors, artifacts


def _corpus_permissions(cases: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            errors.append("corpus case must be an object")
            continue
        case_id = case.get("id", case.get("path", "<unknown>"))
        if case.get("category") == "corrupt":
            if (
                case.get("source_url") == "generated in repository"
                and case.get("license") == "repository-authored fixture"
                and case.get("permission") == "repository-authored fixture"
            ):
                continue
        elif (
            case.get("source_url") == TEAM_OWNED_SOURCE_URL
            and case.get("license") == TEAM_OWNED_LICENSE
            and case.get("permission") == TEAM_OWNED_PERMISSION
        ):
            continue
        for field in ("source_url", "license", "permission"):
            value = case.get(field)
            normalized = value.strip().lower() if isinstance(value, str) else ""
            if (
                not isinstance(value, str)
                or not value.strip()
                or normalized in PLACEHOLDER_VALUES
            ):
                errors.append(f"{case_id}: {field} is not supplied")
            else:
                errors.append(f"{case_id}: ownership/permission policy is unrecognized")
                break
    return not errors, errors


def _corpus_file_gate(
    root: Path, cases: list[dict[str, Any]]
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    details: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("corpus case must be an object")
            details.append({"id": None, "path": None})
            continue
        case_id = case.get("id")
        path_value = case.get("path")
        detail: dict[str, Any] = {"id": case_id, "path": path_value}
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append("corpus case id must be a non-empty string")
        elif case_id in seen_ids:
            errors.append(f"duplicate corpus case id: {case_id}")
        else:
            seen_ids.add(case_id)
        if not isinstance(path_value, str) or not path_value.strip():
            errors.append(f"{case_id}: corpus path is missing")
            details.append(detail)
            continue
        try:
            path = _path(root, path_value)
        except ValueError as exc:
            errors.append(f"{case_id}: {exc}")
            details.append(detail)
            continue
        if path in seen_paths:
            errors.append(f"{case_id}: duplicate corpus path")
        else:
            seen_paths.add(path)
        actual_hash = _sha256(path)
        expected_hash = case.get("sha256")
        matches = bool(actual_hash) and actual_hash == expected_hash
        detail.update(
            {
                "exists": path.exists(),
                "sha256": actual_hash,
                "expected_sha256": expected_hash,
                "matches": matches,
            }
        )
        if not matches:
            errors.append(f"{case_id}: corpus file checksum mismatch or missing")
        details.append(detail)
    return not errors, errors, details


def _corpus_label_gate(cases: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    categories = {"fmd", "healthy", "non_cattle", "former_lsd", "corrupt"}
    for case in cases:
        if not isinstance(case, dict):
            errors.append("corpus case must be an object")
            continue
        case_id = case.get("id", case.get("path", "<unknown>"))
        category = case.get("category")
        if not isinstance(category, str) or category not in categories:
            errors.append(f"{case_id}: unknown corpus category")
            continue
        if category in {"fmd", "healthy", "non_cattle"}:
            if case.get("expected_label") not in CANONICAL_CLASSES:
                errors.append(f"{case_id}: active expected_label is invalid")
            if case.get("label_status") != "authoritative":
                errors.append(f"{case_id}: label provenance is not authoritative")
            if case.get("label_source") != TEAM_OWNED_LABEL_SOURCE:
                errors.append(
                    f"{case_id}: owner-approved project label evidence is missing"
                )
            if (
                not isinstance(case.get("label_evidence"), str)
                or not case["label_evidence"].strip()
            ):
                errors.append(f"{case_id}: label evidence is missing")
            limitation = case.get("accepted_limitation")
            if limitation is not None and (
                not isinstance(limitation, dict)
                or limitation.get("option") != "C"
                or limitation.get("status") != "accepted"
                or limitation.get("observed_label") not in CANONICAL_CLASSES
                or limitation.get("observed_label") == case.get("expected_label")
                or not isinstance(limitation.get("reason"), str)
                or not limitation["reason"].strip()
            ):
                errors.append(f"{case_id}: accepted limitation is invalid")
        elif category == "former_lsd":
            if case.get("source_label") != "LSD":
                errors.append(f"{case_id}: former-LSD source label is missing")
            if case.get("expected_label") is not None:
                errors.append(
                    f"{case_id}: former-LSD case must not have an active label"
                )
            if case.get("expected_policy") != "must_not_be_non_cattle":
                errors.append(f"{case_id}: former-LSD policy is missing")
            if case.get("label_status") != "authoritative":
                errors.append(
                    f"{case_id}: former-LSD label provenance is not authoritative"
                )
            if case.get("label_source") != TEAM_OWNED_LABEL_SOURCE:
                errors.append(
                    f"{case_id}: former-LSD owner-approved label evidence is missing"
                )
            if (
                not isinstance(case.get("label_evidence"), str)
                or not case["label_evidence"].strip()
            ):
                errors.append(f"{case_id}: former-LSD label evidence is missing")
        elif category == "corrupt":
            if case.get("expected_label") is not None:
                errors.append(f"{case_id}: corrupt case must not have a label")
            if case.get("expected_policy") != "reject_before_model_invocation":
                errors.append(f"{case_id}: corrupt-input policy is missing")
    return not errors, errors


def _corrupt_fixture_gate(
    root: Path, cases: list[dict[str, Any]]
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    details: list[dict[str, Any]] = []
    corrupt_cases = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("category") == "corrupt"
    ]
    if not corrupt_cases:
        return False, ["at least one corrupt corpus fixture is required"], details
    for case in corrupt_cases:
        case_id = case.get("id", "<unknown>")
        detail = {
            "id": case_id,
            "path": case.get("path"),
            "model_invocations": 0,
        }
        if case.get("expected_policy") != "reject_before_model_invocation":
            errors.append(f"{case_id}: corrupt-input policy is missing")
        path_value = case.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            detail.update(
                {
                    "decode_status": "not_checked",
                    "error": "ValueError: corrupt fixture path is missing",
                }
            )
            errors.append(f"{case_id}: corrupt fixture path is invalid")
            details.append(detail)
            continue
        try:
            fixture = _path(root, path_value)
        except (KeyError, TypeError, ValueError) as exc:
            detail.update(
                {
                    "decode_status": "not_checked",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            errors.append(f"{case_id}: corrupt fixture path is invalid")
        else:
            detail["exists"] = fixture.is_file()
            detail["sha256"] = _sha256(fixture)
            try:
                with Image.open(fixture) as image:
                    image.verify()
            except Exception as exc:
                detail["decode_status"] = "rejected_before_inference"
                detail["error_type"] = type(exc).__name__
            else:
                detail["decode_status"] = "decoded_unexpectedly"
                errors.append(f"corrupt fixture decoded: {path_value}")
            if detail.get("sha256") != case.get("sha256"):
                errors.append(f"{case_id}: corrupt fixture checksum mismatch")
        details.append(detail)
    return not errors, errors, details


def _preprocess(path: Path) -> Any:
    import numpy as np  # type: ignore[import-not-found]

    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    image = image.resize((224, 224), Image.Resampling.BILINEAR)
    return np.expand_dims(np.asarray(image, dtype=np.float32), axis=0)


def _int_shape(value: Any) -> tuple[int, ...]:
    try:
        return tuple(int(item) for item in value)
    except (TypeError, ValueError, OverflowError):
        return ()


def _probabilities(value: Any) -> list[float]:
    import numpy as np  # type: ignore[import-not-found]

    array = np.asarray(value)
    if array.shape != EXPECTED_OUTPUT_SHAPE or array.dtype != np.float32:
        raise ValueError(
            f"expected float32 output shape {EXPECTED_OUTPUT_SHAPE}, got "
            f"{array.shape} {array.dtype}"
        )
    try:
        values = [float(item) for item in array[0].tolist()]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("output probabilities could not be converted") from exc
    if any(not np.isfinite(item) or item < 0 or item > 1 for item in values):
        raise ValueError("output contains a non-finite or out-of-range probability")
    if not np.isclose(sum(values), 1.0, atol=1e-3):
        raise ValueError("output probabilities do not sum to one")
    return values


def _remove_key(value: Any, key: str) -> bool:
    changed = False
    if isinstance(value, dict):
        if key in value:
            value.pop(key)
            changed = True
        for nested in value.values():
            changed = _remove_key(nested, key) or changed
    elif isinstance(value, list):
        for nested in value:
            changed = _remove_key(nested, key) or changed
    return changed


def _keras_predictor(
    path: Path,
) -> tuple[Callable[[Any], list[float]], dict[str, Any], Callable[[], None]]:
    import tensorflow as tf  # type: ignore[import-not-found]

    temporary: Any = None
    model: Any
    try:
        model = tf.keras.models.load_model(path, compile=False)
    except (OSError, TypeError, ValueError):
        model = None

    if model is None:
        temporary = tempfile.TemporaryDirectory(prefix="sapisehat_verify_")
        try:
            patched = Path(temporary.name) / path.name
            if path.is_file() and path.suffix == ".keras":
                with (
                    zipfile.ZipFile(path) as archive,
                    zipfile.ZipFile(patched, "w") as output,
                ):
                    config = json.loads(archive.read("config.json"))
                    _remove_key(config, "quantization_config")
                    for info in archive.infolist():
                        data = (
                            json.dumps(config).encode()
                            if info.filename == "config.json"
                            else archive.read(info)
                        )
                        output.writestr(info, data)
                model = tf.keras.models.load_model(patched, compile=False)
            elif path.is_dir():
                shutil.copytree(path, patched)
                config_path = patched / "config.json"
                config = json.loads(config_path.read_text(encoding="utf-8"))
                if not _remove_key(config, "quantization_config"):
                    raise
                config_path.write_text(json.dumps(config), encoding="utf-8")
                model = tf.keras.models.load_model(f"{patched}/", compile=False)
            else:
                raise
        except (OSError, KeyError, TypeError, ValueError, zipfile.BadZipFile):
            temporary.cleanup()
            raise

    inputs = getattr(model, "inputs", [])
    outputs = getattr(model, "outputs", [])
    tensor = inputs[0] if len(inputs) == 1 else None
    output_tensor = outputs[0] if len(outputs) == 1 else None
    shape = tuple(getattr(tensor, "shape", ())) if tensor is not None else ()
    output_shape = (
        tuple(getattr(output_tensor, "shape", ())) if output_tensor is not None else ()
    )
    dtype = str(getattr(tensor, "dtype", "")).lower() if tensor is not None else ""
    output_dtype = (
        str(getattr(output_tensor, "dtype", "")).lower()
        if output_tensor is not None
        else ""
    )
    contract = {
        "input_tensor_count": len(inputs),
        "output_tensor_count": len(outputs),
        "input_shape": list(shape),
        "output_shape": list(output_shape),
        "input_dtype": dtype,
        "output_dtype": output_dtype,
        "valid": len(inputs) == 1
        and len(outputs) == 1
        and shape in {(None, 224, 224, 3), (1, 224, 224, 3)}
        and output_shape in {(None, 3), (1, 3)}
        and dtype in {"float32", "<f4", "numpy.float32"}
        and output_dtype in {"float32", "<f4", "numpy.float32"},
    }

    def predict(batch: Any) -> list[float]:
        return _probabilities(model.predict(batch, verbose=0))

    def cleanup() -> None:
        nonlocal temporary
        if temporary is not None:
            temporary.cleanup()
            temporary = None

    return predict, contract, cleanup


def _tflite_predictor(
    path: Path,
) -> tuple[Callable[[Any], list[float]], dict[str, Any], Callable[[], None]]:
    import numpy as np  # type: ignore[import-not-found]
    import tensorflow as tf  # type: ignore[import-not-found]

    interpreter = tf.lite.Interpreter(model_path=str(path))
    interpreter.allocate_tensors()
    inputs = interpreter.get_input_details()
    outputs = interpreter.get_output_details()
    input_detail = inputs[0] if len(inputs) == 1 else {}
    output_detail = outputs[0] if len(outputs) == 1 else {}
    shape = _int_shape(input_detail.get("shape", ()))
    output_shape = _int_shape(output_detail.get("shape", ()))
    input_dtype = (
        str(np.dtype(input_detail.get("dtype"))).lower() if input_detail else ""
    )
    output_dtype = (
        str(np.dtype(output_detail.get("dtype"))).lower() if output_detail else ""
    )
    contract = {
        "input_tensor_count": len(inputs),
        "output_tensor_count": len(outputs),
        "input_shape": list(shape),
        "output_shape": list(output_shape),
        "input_dtype": input_dtype,
        "output_dtype": output_dtype,
        "valid": len(inputs) == 1
        and len(outputs) == 1
        and shape == EXPECTED_INPUT_SHAPE
        and output_shape == EXPECTED_OUTPUT_SHAPE
        and input_dtype == "float32"
        and output_dtype == "float32",
    }

    def predict(batch: Any) -> list[float]:
        interpreter.set_tensor(input_detail["index"], batch)
        interpreter.invoke()
        return _probabilities(interpreter.get_tensor(output_detail["index"]))

    def cleanup() -> None:
        close = getattr(interpreter, "close", None)
        if callable(close):
            close()

    return predict, contract, cleanup


def _top_index(scores: list[float]) -> int:
    return max(range(len(scores)), key=scores.__getitem__)


def verify_runtime_case(
    root: Path,
    case: dict[str, Any],
    keras_predict: Callable[[Any], list[float]],
    tflite_predict: Callable[[Any], list[float]],
) -> dict[str, Any]:
    """Decode one corpus case, then invoke both runtimes only if decoding passed."""
    if not isinstance(case, dict):
        return {
            "id": None,
            "path": None,
            "model_invocations": 0,
            "decode_status": "not_checked",
            "probabilities_valid": False,
            "error": "ValueError: corpus case must be an object",
        }
    detail: dict[str, Any] = {
        "id": case.get("id"),
        "path": case.get("path"),
        "model_invocations": 0,
    }
    try:
        image_path = _path(root, case["path"])
    except (KeyError, TypeError, ValueError) as exc:
        detail.update(
            {
                "decode_status": "not_checked",
                "probabilities_valid": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return detail
    if case.get("category") == "corrupt":
        try:
            with Image.open(image_path) as image:
                image.verify()
        except Exception as exc:
            detail.update(
                {
                    "decode_status": "rejected_before_inference",
                    "probabilities_valid": None,
                    "error_type": type(exc).__name__,
                }
            )
        else:
            detail.update(
                {
                    "decode_status": "decoded_unexpectedly",
                    "probabilities_valid": False,
                    "error": "corrupt fixture decoded unexpectedly",
                }
            )
        return detail

    try:
        batch = _preprocess(image_path)
    except Exception as exc:
        detail.update(
            {
                "decode_status": "rejected_before_inference",
                "probabilities_valid": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return detail

    detail["decode_status"] = "decoded"
    try:
        detail["model_invocations"] = 1
        keras_scores = keras_predict(batch)
        detail["model_invocations"] = 2
        tflite_scores = tflite_predict(batch)
        keras_index = _top_index(keras_scores)
        tflite_index = _top_index(tflite_scores)
        delta = max(
            abs(left - right)
            for left, right in zip(keras_scores, tflite_scores, strict=True)
        )
        detail.update(
            {
                "keras_scores": keras_scores,
                "tflite_scores": tflite_scores,
                "keras_top_class": CANONICAL_CLASSES[keras_index],
                "tflite_top_class": CANONICAL_CLASSES[tflite_index],
                "score_delta_max_abs": delta,
                "top_class_match": keras_index == tflite_index,
                "probabilities_valid": True,
            }
        )
    except Exception as exc:
        detail.update(
            {
                "probabilities_valid": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
    return detail


def _empty_runtime() -> dict[str, Any]:
    return {
        "status": "not_run",
        "runtime": None,
        "tensor_contract": {"keras": {"valid": False}, "tflite": {"valid": False}},
        "cases": [],
        "valid_cases_checked": 0,
        "max_observed_score_delta": None,
        "top_class_mismatches": None,
        "probability_contract_failures": [],
        "runtime_case_failures": [],
    }


def _runtime_checks(
    root: Path, artifacts: dict[str, Any], cases: list[dict[str, Any]]
) -> dict[str, Any]:
    result = _empty_runtime()
    try:
        import tensorflow as tf  # type: ignore[import-not-found]
    except (ImportError, OSError) as exc:
        result["status"] = "unavailable"
        result["error"] = f"TensorFlow unavailable: {exc}"
        return result

    keras_cleanup: Callable[[], None] | None = None
    tflite_cleanup: Callable[[], None] | None = None
    try:
        keras_path = _path(root, artifacts["keras"]["path"])
        tflite_path = _path(root, artifacts["tflite"]["path"])
        (
            keras_predict,
            keras_contract,
            keras_cleanup,
        ) = _keras_predictor(keras_path)
        (
            tflite_predict,
            tflite_contract,
            tflite_cleanup,
        ) = _tflite_predictor(tflite_path)
        result.update(
            {
                "status": "completed",
                "runtime": f"TensorFlow {tf.__version__}",
                "tensor_contract": {
                    "keras": keras_contract,
                    "tflite": tflite_contract,
                },
            }
        )
        if not keras_contract["valid"] or not tflite_contract["valid"]:
            return result

        maximum_delta: float | None = None
        mismatches = 0
        valid_checked = 0
        for case in cases:
            if not isinstance(case, dict):
                result["runtime_case_failures"].append("<invalid-case>")
                continue
            detail = verify_runtime_case(root, case, keras_predict, tflite_predict)
            result["cases"].append(detail)
            if case.get("category") == "corrupt":
                if detail.get("decode_status") != "rejected_before_inference":
                    result["runtime_case_failures"].append(case.get("id"))
                continue
            valid_checked += 1
            if not detail.get("probabilities_valid"):
                result["probability_contract_failures"].append(case.get("id"))
                result["runtime_case_failures"].append(case.get("id"))
                continue
            delta = detail["score_delta_max_abs"]
            maximum_delta = (
                delta if maximum_delta is None else max(maximum_delta, delta)
            )
            if not detail["top_class_match"]:
                mismatches += 1
        result["valid_cases_checked"] = valid_checked
        result["max_observed_score_delta"] = maximum_delta
        result["top_class_mismatches"] = mismatches
    except Exception as exc:
        result["status"] = "failed"
        result["runtime"] = f"TensorFlow {tf.__version__}"
        result["error"] = f"runtime contract load failed: {type(exc).__name__}: {exc}"
    finally:
        if tflite_cleanup is not None:
            tflite_cleanup()
        if keras_cleanup is not None:
            keras_cleanup()
    return result


def _former_lsd_gate(
    runtime: dict[str, Any], cases: list[dict[str, Any]]
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    results = {
        case.get("id"): case
        for case in runtime.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    former_cases = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("category") == "former_lsd"
    ]
    if runtime.get("status") != "completed":
        return False, ["former-LSD behavior requires completed runtime verification"]
    if not former_cases:
        return False, ["at least one former-LSD corpus case is required"]
    for case in former_cases:
        case_id = case.get("id")
        result = results.get(case_id)
        if result is None:
            errors.append(f"{case_id}: former-LSD case was not run")
            continue
        if result.get("keras_top_class") == "non_cattle":
            errors.append(f"{case_id}: Keras rejected a former-LSD cattle probe")
        if result.get("tflite_top_class") == "non_cattle":
            errors.append(f"{case_id}: TFLite rejected a former-LSD cattle probe")
        if not result.get("probabilities_valid"):
            errors.append(f"{case_id}: former-LSD runtime probabilities are invalid")
    return not errors, errors


def _class_identity_gate(
    root: Path,
    manifest: dict[str, Any],
    metadata: dict[str, Any],
) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    identity: dict[str, Any] = {}
    try:
        identity_path = _path(root, manifest.get("class_identity_manifest", ""))
        identity = _json(identity_path)
    except Exception as exc:
        return False, [f"class identity manifest unavailable: {exc}"], identity

    backend = metadata.get("backend", {})
    expected_artifacts = manifest.get("artifacts", {})
    if identity.get("class_order") != list(RAW_CLASSES):
        errors.append("class identity manifest does not state the raw model order")
    if identity.get("label_mapping") != MODEL_LABEL_MAPPING:
        errors.append("class identity manifest canonical mapping is invalid")
    if identity.get("class_indices") != EXPECTED_CLASS_INDICES:
        errors.append("class identity manifest indices do not state the active order")
    if identity.get("status") != "authoritative":
        errors.append("class identity evidence is not authoritative")
    if identity.get("model_version") != backend.get("model_version"):
        errors.append("class identity evidence model version differs")
    if identity.get("artifacts") != expected_artifacts:
        errors.append("class identity evidence does not name the exact artifact pair")
    evidence = identity.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("class identity evidence details are missing")
    else:
        if evidence.get("status") != "authoritative":
            errors.append("class identity evidence source is not authoritative")
        if evidence.get("source") != "apps/backend/model/class_names.json":
            errors.append("class identity evidence source is not class_names.json")
        if not isinstance(evidence.get("basis"), str) or not evidence["basis"].strip():
            errors.append("class identity evidence basis is missing")
    return not errors, errors, identity


def _physical_android_smoke_gate(
    manifest: dict[str, Any],
) -> tuple[bool, list[str]]:
    smoke = manifest.get("physical_android_offline_smoke")
    if not isinstance(smoke, dict) or smoke.get("status") != "passed":
        return False, [
            "physical Android offline smoke test has not been performed; activation remains pending"
        ]
    return True, []


def validate_manifest(
    manifest_path: Path,
    *,
    repo_root: Path | None = None,
    run_runtime: bool = False,
) -> dict[str, Any]:
    """Return an auditable verification report for the model pair and corpus."""
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_base = Path(repo_root) if repo_root is not None else Path.cwd()
        manifest_path = manifest_base / manifest_path
    manifest_path = manifest_path.resolve()
    root = (
        Path(repo_root).resolve()
        if repo_root is not None
        else _repository_root(manifest_path.parent)
    )
    try:
        manifest_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Manifest must be inside the repository root") from exc

    manifest = _json(manifest_path)
    cases = manifest.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("manifest cases must be a list")

    metadata_pair, metadata_errors, metadata = _metadata_pair_gate(root)
    metadata_activation, metadata_activation_errors = _metadata_activation_gate(
        metadata
    )
    artifact_ok, artifact_errors, artifacts = _artifact_gate(root, manifest, metadata)
    permissions_ok, permission_errors = _corpus_permissions(cases)
    labels_ok, label_errors = _corpus_label_gate(cases)
    files_ok, file_errors, file_details = _corpus_file_gate(root, cases)
    corrupt_ok, corrupt_errors, corrupt_details = _corrupt_fixture_gate(root, cases)
    identity_ok, identity_errors, identity = _class_identity_gate(
        root, manifest, metadata
    )
    physical_smoke_ok, physical_smoke_errors = _physical_android_smoke_gate(manifest)

    runtime = (
        _runtime_checks(root, artifacts, cases)
        if run_runtime and artifact_ok and metadata_pair
        else _empty_runtime()
    )
    valid_case_count = sum(
        isinstance(case, dict) and case.get("category") != "corrupt" for case in cases
    )
    runtime_tensor_ok = (
        runtime.get("status") == "completed"
        and bool(runtime.get("tensor_contract", {}).get("keras", {}).get("valid"))
        and bool(runtime.get("tensor_contract", {}).get("tflite", {}).get("valid"))
    )
    finite_probability_ok = (
        runtime_tensor_ok
        and runtime.get("valid_cases_checked") == valid_case_count
        and not runtime.get("probability_contract_failures")
    )
    max_score_delta = runtime.get("max_observed_score_delta")
    score_delta_ok = (
        isinstance(max_score_delta, (int, float))
        and math.isfinite(max_score_delta)
        and max_score_delta <= SCORE_TOLERANCE
    )
    parity_ok = (
        finite_probability_ok
        and runtime.get("top_class_mismatches") == 0
        and not runtime.get("runtime_case_failures")
    )

    runtime_cases = {
        case.get("id"): case
        for case in runtime.get("cases", [])
        if isinstance(case, dict)
    }
    labeled_cases = [
        case
        for case in cases
        if isinstance(case, dict)
        and case.get("category") in {"fmd", "healthy", "non_cattle"}
    ]

    def expectation_passes(case: dict[str, Any]) -> bool:
        result = runtime_cases.get(case.get("id"))
        if result is None:
            return False
        observed = {
            result.get("keras_top_class"),
            result.get("tflite_top_class"),
        }
        if observed == {case.get("expected_label")}:
            return True
        limitation = case.get("accepted_limitation")
        return (
            isinstance(limitation, dict)
            and limitation.get("option") == "C"
            and limitation.get("status") == "accepted"
            and observed == {limitation.get("observed_label")}
        )

    labeled_cases_ok = (
        bool(labeled_cases)
        and runtime_tensor_ok
        and all(expectation_passes(case) for case in labeled_cases)
    )
    former_lsd_ok, former_lsd_errors = _former_lsd_gate(runtime, cases)
    corrupt_runtime_ok = corrupt_ok and all(
        detail.get("decode_status") == "rejected_before_inference"
        and detail.get("model_invocations") == 0
        for detail in corrupt_details
    )
    if run_runtime and runtime.get("status") == "completed":
        corrupt_runtime_ok = corrupt_runtime_ok and all(
            runtime_cases.get(detail.get("id"), {}).get("decode_status")
            == "rejected_before_inference"
            and runtime_cases.get(detail.get("id"), {}).get("model_invocations") == 0
            for detail in corrupt_details
        )

    gates = {
        "metadata_pair_contract": metadata_pair,
        "metadata_activation_status": metadata_activation,
        "artifact_checksums": artifact_ok,
        "tensor_contract_declaration": metadata_pair,
        "runtime_tensor_contract": runtime_tensor_ok,
        "finite_probability_contract": finite_probability_ok,
        "valid_image_top_class_parity": parity_ok,
        "score_tolerance": score_delta_ok and finite_probability_ok,
        "labeled_corpus_expectations": labeled_cases_ok,
        "corpus_label_provenance": labels_ok,
        "corpus_file_integrity": files_ok,
        "corrupt_input_fixture": corrupt_runtime_ok,
        "former_lsd_policy": former_lsd_ok,
        "class_identity_provenance": identity_ok,
        "corpus_source_permissions": permissions_ok,
        "physical_android_offline_smoke": physical_smoke_ok,
    }
    activation_ready = all(
        gates.get(name, False) for name in REQUIRED_VERIFICATION_GATES
    )

    blocker_messages = [
        *metadata_errors,
        *metadata_activation_errors,
        *artifact_errors,
        *identity_errors,
        *permission_errors,
        *physical_smoke_errors,
        *label_errors,
        *file_errors,
        *corrupt_errors,
        *former_lsd_errors,
    ]
    if not runtime_tensor_ok:
        blocker_messages.append("runtime tensor contract has not passed")
    if not finite_probability_ok:
        blocker_messages.append("finite probability contract has not passed")
    if not parity_ok:
        blocker_messages.append("Keras/TFLite top-class parity has not passed")
    if not score_delta_ok:
        blocker_messages.append("Keras/TFLite score tolerance has not passed")
    if not labeled_cases_ok:
        blocker_messages.append("labeled corpus expectations have not passed")
    if not files_ok:
        blocker_messages.append("corpus file integrity has not passed")
    if not corrupt_runtime_ok:
        blocker_messages.append("corrupt input pre-inference rejection has not passed")
    if runtime.get("error"):
        blocker_messages.append(str(runtime["error"]))
    if not metadata_activation:
        blocker_messages.append("metadata remains fail-closed and is not activated")
    blockers = list(dict.fromkeys(message for message in blocker_messages if message))

    return {
        "schema_version": 2,
        "generated_from": str(manifest_path.relative_to(root)),
        "model_version": metadata.get("backend", {}).get("model_version"),
        "artifact_status": "verified" if activation_ready else "pending",
        "activation_ready": activation_ready,
        "overall_pass": activation_ready,
        "required_gates": list(REQUIRED_VERIFICATION_GATES),
        "gates": gates,
        "blockers": blockers,
        "artifacts": artifacts,
        "class_identity": identity,
        "corpus_files": file_details,
        "corrupt_fixtures": corrupt_details,
        "runtime": runtime,
        "cases": cases,
        "corpus_summary": {
            "total_cases": len(cases),
            "valid_cases": valid_case_count,
            "former_lsd_cases": sum(
                isinstance(case, dict) and case.get("category") == "former_lsd"
                for case in cases
            ),
        },
        "score_tolerance_max_abs": SCORE_TOLERANCE,
        "notes": [
            "Predictions are never used to infer class identity.",
            "Former-LSD probes are historical source-label probes, not active LSD labels.",
            "non-cattle-human-02 (mulut manusia.png) predicts FMD; this is an explicitly accepted Option C known limitation, not hidden or relabeled.",
            "Activation remains blocked until provenance, permissions, physical Android offline smoke, and every required gate pass.",
        ],
    }


def format_markdown(report: dict[str, Any]) -> str:
    runtime = report.get("runtime", {})
    lines = [
        "# Three-output model verification report",
        "",
        f"- **Model version:** `{report.get('model_version')}`",
        f"- **Artifact status:** `{report.get('artifact_status')}`",
        f"- **Activation ready:** `{report.get('activation_ready')}`",
        f"- **Runtime:** `{runtime.get('runtime') or runtime.get('status')}`",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{name}` | {'PASS' if value else 'BLOCKED'} |"
        for name, value in report.get("gates", {}).items()
    )
    lines.extend(["", "## Blockers", ""])
    blockers = report.get("blockers", []) or ["None"]
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(
        [
            "",
            "## Corpus policy",
            "",
            "Owner-approved policy: existing corpus images are team-owned and project labels are authoritative for this personal repository; no external URL, license, signature, or veterinary review is asserted.",
            "Former-LSD filenames are historical source labels only and are never mapped to an active class. Every former-LSD cattle probe must avoid `non_cattle`; every corrupt fixture must be rejected before model invocation.",
            "Option C known limitation is intentionally visible: non-cattle-human-02 (`mulut manusia.png`) is expected `non_cattle` but both runtimes predict FMD; the mismatch is accepted, not hidden or relabeled.",
            "",
            "## Runtime case results",
            "",
            "| Case | Category | Keras top | TFLite top | Max score delta | Invocations |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    runtime_cases = {
        case.get("id"): case
        for case in runtime.get("cases", [])
        if isinstance(case, dict)
    }
    for case in report.get("cases", []):
        case_id = case.get("id") if isinstance(case, dict) else "<invalid>"
        category = case.get("category") if isinstance(case, dict) else "<invalid>"
        result = runtime_cases.get(case_id, {})
        lines.append(
            f"| `{case_id}` | `{category}` | "
            f"`{result.get('keras_top_class', 'not run')}` | "
            f"`{result.get('tflite_top_class', 'not run')}` | "
            f"`{result.get('score_delta_max_abs', 'not run')}` | "
            f"`{result.get('model_invocations', 0)}` |"
        )
    lines.extend(
        [
            "",
            "## Safety notes",
            "",
            "- This report does not establish clinical diagnosis or disease confirmation.",
            "- A pending report must not be used to activate backend or Flutter inference.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root when running from a backend-only container",
    )
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--markdown-report", type=Path)
    parser.add_argument(
        "--no-runtime",
        action="store_true",
        help="Only run checksum, metadata, and corpus checks",
    )
    args = parser.parse_args(argv)
    root = (
        args.repo_root.resolve()
        if args.repo_root is not None
        else _repository_root(Path(__file__))
    )
    verification_dir = (
        root / "apps/backend/model/verification"
        if _is_full_repository(root)
        else root / "model/verification"
    )

    def resolve_output(value: Path | None, default: Path) -> Path:
        if value is None:
            return default
        return value if value.is_absolute() else root / value

    manifest_path = resolve_output(
        args.manifest, verification_dir / "golden_corpus_manifest.json"
    )
    json_report_path = resolve_output(
        args.json_report, verification_dir / "verification_report.json"
    )
    markdown_report_path = resolve_output(
        args.markdown_report, verification_dir / "verification_report.md"
    )
    report = validate_manifest(
        manifest_path, repo_root=root, run_runtime=not args.no_runtime
    )
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_report_path.write_text(format_markdown(report), encoding="utf-8")
    print(format_markdown(report))
    return 0 if report["activation_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
