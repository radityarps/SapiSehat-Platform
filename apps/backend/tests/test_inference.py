"""Unit tests for inference service."""

import unittest
from unittest.mock import patch
import numpy as np  # type: ignore[import-not-found]
from PIL import Image
from inference_server import inference_service, InferenceService
from preprocessing.model_preprocessor import ModelPreprocessor
from utils.errors import PreprocessingError


class TestModelPreprocessor(unittest.TestCase):
    """Test Tahap 2 preprocessing (model preprocessing)."""

    def test_preprocessing_returns_correct_shape(self):
        """Test that preprocessing returns correct numpy array shape."""
        img = Image.new('RGB', (800, 600), color='red')
        arr = ModelPreprocessor.process(img)
        # Should be [1, 224, 224, 3] (channels-last, batch dim)
        self.assertEqual(arr.shape, (1, 224, 224, 3))
        self.assertEqual(arr.dtype, np.float32)

    def test_preprocessing_is_deterministic(self):
        """Test that preprocessing produces deterministic output."""
        img1 = Image.new('RGB', (256, 256), color='blue')
        img2 = Image.new('RGB', (256, 256), color='blue')
        arr1 = ModelPreprocessor.process(img1)
        arr2 = ModelPreprocessor.process(img2)
        self.assertTrue(np.allclose(arr1, arr2))

    def test_preprocessing_keeps_float32_pixels_in_model_range(self):
        """The model performs its own rescaling from raw [0, 255] pixels."""
        img = Image.new('RGB', (224, 224), color=(128, 128, 128))
        arr = ModelPreprocessor.process(img)
        self.assertEqual(arr.dtype, np.float32)
        self.assertGreaterEqual(arr.min(), 0.0)
        self.assertLessEqual(arr.max(), 255.0)
        self.assertTrue(np.allclose(arr, 128.0))

    def test_preprocessing_uses_bilinear_resize(self):
        """Resize output matches Pillow's bilinear implementation."""
        img = Image.new('RGB', (2, 2))
        img.putdata([(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)])
        expected = np.asarray(
            img.resize((224, 224), Image.Resampling.BILINEAR), dtype=np.float32
        )
        actual = ModelPreprocessor.process(img)[0]
        self.assertTrue(np.array_equal(actual, expected))

    def test_preprocessing_handles_different_formats(self):
        """Test that preprocessing handles different image formats."""
        img_rgb = Image.new('RGB', (300, 300), color='green')
        img_rgba = Image.new('RGBA', (300, 300), color='green')
        img_gray = Image.new('L', (300, 300), color=100)

        arr_rgb = ModelPreprocessor.process(img_rgb)
        arr_rgba = ModelPreprocessor.process(img_rgba)
        arr_gray = ModelPreprocessor.process(img_gray)

        for arr in [arr_rgb, arr_rgba, arr_gray]:
            self.assertEqual(arr.shape, (1, 224, 224, 3))


class TestInferenceService(unittest.TestCase):
    """Test InferenceService (pure inference logic)."""

    def setUp(self):
        """Set up test fixtures."""
        service = inference_service
        if service is None:
            self.skipTest("verified model artifact is not available")
        self.service: InferenceService = service

    def test_predict_returns_valid_response_structure(self):
        """Test that predict returns properly structured response."""
        img = Image.new('RGB', (224, 224), color='red')
        result = self.service.predict(img)
        self.assertEqual(result["status"], "success")
        self.assertIn("prediction", result)
        self.assertIn("model_info", result)
        self.assertIn("processing_time_ms", result)

    def test_predict_includes_required_fields(self):
        """Test that prediction includes all required fields."""
        img = Image.new('RGB', (224, 224), color='blue')
        result = self.service.predict(img)
        prediction = result["prediction"]
        self.assertIn("disease_class", prediction)
        self.assertIn("display_label_key", prediction)
        self.assertIn("confidence", prediction)
        self.assertIn("is_reliable", prediction)
        self.assertIn("scores", prediction)
        self.assertIsInstance(prediction["disease_class"], str)
        self.assertIsInstance(prediction["confidence"], (int, float))
        self.assertIsInstance(prediction["is_reliable"], bool)
        self.assertIsInstance(prediction["scores"], dict)

    def test_predict_label_is_valid(self):
        """Test that predicted label is one of valid classes."""
        img = Image.new('RGB', (224, 224), color='green')
        result = self.service.predict(img)
        disease_class = result["prediction"]["disease_class"]
        self.assertIn(disease_class, self.service.LABELS)

    def test_predict_confidence_in_valid_range(self):
        """Test that confidence score is between 0 and 1."""
        img = Image.new('RGB', (400, 300), color='red')
        result = self.service.predict(img)
        confidence = result["prediction"]["confidence"]
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_predict_scores_sum_to_one(self):
        """Test that all prediction scores sum to approximately 1.0."""
        img = Image.new('RGB', (224, 224), color='yellow')
        result = self.service.predict(img)
        scores = result["prediction"]["scores"]
        total = sum(scores.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_predict_is_deterministic(self):
        """Test that predictions are deterministic for same image."""
        img1 = Image.new('RGB', (224, 224), color=(100, 150, 200))
        img2 = Image.new('RGB', (224, 224), color=(100, 150, 200))
        result1 = self.service.predict(img1)
        result2 = self.service.predict(img2)
        self.assertEqual(result1["prediction"]["disease_class"], result2["prediction"]["disease_class"])
        self.assertEqual(result1["prediction"]["confidence"], result2["prediction"]["confidence"])

    def test_predict_timing_is_reasonable(self):
        """Test that inference timing is reasonable."""
        img = Image.new('RGB', (224, 224), color='white')
        result = self.service.predict(img)
        total_ms = result["processing_time_ms"]
        self.assertGreater(total_ms, 0)
        self.assertLess(total_ms, 30000)


class TestSingletonModel(unittest.TestCase):
    """Test model singleton behavior."""

    def test_model_is_singleton(self):
        """Test that model is loaded only once."""
        from model.loader import ModelLoader

        ModelLoader._instance = None
        ModelLoader._initialized = False
        with patch.object(ModelLoader, "_load_model") as load_model:
            loader1 = ModelLoader("verified-test.keras")
            loader2 = ModelLoader("verified-test.keras")

        self.assertIs(loader1, loader2)
        load_model.assert_called_once_with("verified-test.keras")


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""

    def test_invalid_image_handling(self):
        """Test handling of invalid inputs."""
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
