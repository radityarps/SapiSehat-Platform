"""Real Keras artifact integration tests."""

import numpy as np  # type: ignore[import-not-found]
import pytest

from config import MODEL_CLASS_ORDER, settings
from inference_server import InferenceService
from model.loader import ModelLoader


def reset_model_loader():
    ModelLoader._instance = None
    ModelLoader._initialized = False


def test_verified_model_artifact_is_loaded():
    reset_model_loader()

    loader = ModelLoader(settings.model_path)

    assert loader.class_names == list(MODEL_CLASS_ORDER)


def test_inference_service_uses_active_model_class_order(monkeypatch):
    class StubLoader:
        def __init__(self):
            self.class_names = list(MODEL_CLASS_ORDER)

        def predict(self, image_array):
            return np.array([[0.01, 0.98, 0.01]], dtype=np.float32)

    monkeypatch.setattr("inference_server.ModelLoader", lambda model_path: StubLoader())
    service = InferenceService()

    prediction = service._build_prediction(
        service._as_probabilities(np.array([[0.01, 0.98, 0.01]], dtype=np.float32))
    )

    assert prediction["disease_class"] == "FMD"
    assert set(prediction["scores"]) == {"FMD", "healthy"}
    np.testing.assert_allclose(
        list(prediction["scores"].values()),
        [0.98 / 0.99, 0.01 / 0.99],
    )


def test_probability_output_is_not_transformed(monkeypatch):
    class StubLoader:
        def __init__(self):
            self.class_names = list(MODEL_CLASS_ORDER)

        def predict(self, image_array):
            return np.array([[0.1, 0.8, 0.1]], dtype=np.float32)

    monkeypatch.setattr("inference_server.ModelLoader", lambda model_path: StubLoader())
    service = InferenceService()

    probs = service._as_probabilities(np.array([[0.1, 0.8, 0.1]], dtype=np.float32))

    np.testing.assert_allclose(probs, [0.1, 0.8, 0.1])


def test_bare_probability_vector_is_rejected(monkeypatch):
    class StubLoader:
        def __init__(self):
            self.class_names = list(MODEL_CLASS_ORDER)

    monkeypatch.setattr("inference_server.ModelLoader", lambda model_path: StubLoader())
    service = InferenceService()

    with pytest.raises(Exception, match=r"shape \[1, 3\]"):
        service._as_probabilities(np.array([0.1, 0.8, 0.1], dtype=np.float32))
