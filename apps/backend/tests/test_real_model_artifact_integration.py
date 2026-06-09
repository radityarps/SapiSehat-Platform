"""Real Keras artifact integration tests."""

import numpy as np

from config import settings
from inference_server import InferenceService
from model.loader import ModelLoader


def reset_model_loader():
    ModelLoader._instance = None
    ModelLoader._initialized = False


def test_model_class_names_file_defines_prediction_order():
    reset_model_loader()
    loader = ModelLoader(settings.model_path)

    assert loader.class_names == ["FMD", "healthy", "LSD"]


def test_inference_service_uses_model_class_order_not_legacy_settings_order(monkeypatch):
    class StubLoader:
        class_names = ["FMD", "healthy", "LSD"]

        def predict(self, image_array):
            return np.array([[0.01, 0.98, 0.01]], dtype=np.float32)

    monkeypatch.setattr("inference_server.ModelLoader", lambda model_path: StubLoader())
    service = InferenceService()

    prediction = service._build_prediction(service._as_probabilities(np.array([[0.01, 0.98, 0.01]], dtype=np.float32)))

    assert prediction["disease_class"] == "healthy"
    assert prediction["scores"] == {"FMD": 0.01, "healthy": 0.98, "LSD": 0.01}


def test_softmax_output_is_not_softmaxed_twice(monkeypatch):
    class StubLoader:
        class_names = ["FMD", "healthy", "LSD"]

        def predict(self, image_array):
            return np.array([[0.1, 0.8, 0.1]], dtype=np.float32)

    monkeypatch.setattr("inference_server.ModelLoader", lambda model_path: StubLoader())
    service = InferenceService()

    probs = service._as_probabilities(np.array([[0.1, 0.8, 0.1]], dtype=np.float32))

    np.testing.assert_allclose(probs, [0.1, 0.8, 0.1])
