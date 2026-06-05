"""
Tests verifying no-retention server inference behavior.

Acceptance criteria (Issue #12):
- Backend does not write uploaded images to persistent storage.
- Logs exclude image content, precise location, and identifiers.
- Predict endpoint processes image in memory only.
"""

import builtins
import io
import json
import logging
import os
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image
from utils.logger import JSONFormatter


class TestNoRetentionPolicy:
    """Verify that the predict endpoint does not persist uploaded images."""

    def test_predict_request_does_not_persist_image(self, tmp_path):
        """
        Call /api/predict with real image bytes and verify no file persistence.

        Uses targeted patching of file write APIs (PIL.Image.save and builtins.open
        with write mode) to detect any attempt to persist the uploaded image.
        This is more reliable than directory scanning, which can flake from other
        processes writing to temp directories.
        """
        img = Image.new("RGB", (224, 224), color=(128, 64, 32))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        image_bytes = buf.getvalue()

        mock_result = {
            "status": "success",
            "prediction": {
                "disease_class": "healthy",
                "display_label_key": "disease.healthy",
                "confidence": 0.95,
                "is_reliable": True,
                "scores": {"FMD": 0.02, "LSD": 0.03, "healthy": 0.95},
            },
            "model_info": {"version": "1.0.0"},
            "processing_time_ms": 150,
            "preprocessing_time_ms": 50,
            "inference_time_ms": 100,
        }

        save_calls = []
        original_save = Image.Image.save

        def tracking_save(self, fp, *args, **kwargs):
            if isinstance(fp, (str, bytes)):
                save_calls.append(str(fp))
            elif (
                hasattr(fp, "name")
                and isinstance(fp.name, str)
                and not isinstance(fp, io.BytesIO)
            ):
                save_calls.append(fp.name)
            return original_save(self, fp, *args, **kwargs)

        write_opens = []
        original_open = builtins.open

        def tracking_open(file, mode="r", *args, **kwargs):
            if isinstance(file, (str, bytes)) and ("w" in mode or "a" in mode):
                file_str = str(file).lower()
                if any(ext in file_str for ext in (".jpg", ".jpeg", ".png", ".webp")):
                    write_opens.append(str(file))
            return original_open(file, mode, *args, **kwargs)

        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.get_inference_service") as mock_svc,
            patch.object(Image.Image, "save", tracking_save),
            patch("builtins.open", tracking_open),
        ):
            mock_svc.return_value.predict.return_value = mock_result

            from main import app

            client = TestClient(app)

            response = client.post(
                "/api/predict",
                files={"image": ("test.jpg", image_bytes, "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(save_calls) == 0, (
            f"Image was persisted via PIL.Image.save to: {save_calls}"
        )
        assert len(write_opens) == 0, (
            f"Image file was opened for writing: {write_opens}"
        )

    def test_routes_module_has_no_file_write_calls(self):
        """
        Static analysis: routes module should not contain file write operations.
        """
        routes_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "api",
            "routes.py",
        )
        with open(routes_path) as f:
            content = f.read()

        assert "open(" not in content or "io.BytesIO" in content, (
            "routes.py should not open files for writing"
        )
        assert ".save(" not in content, "routes.py should not save images to disk"
        assert "shutil.copy" not in content, "routes.py should not copy files"

    def test_predict_docstring_documents_no_retention(self):
        """Predict endpoint docstring should document no-retention policy."""
        from api.routes import predict

        docstring = predict.__doc__ or ""
        assert (
            "NO-RETENTION" in docstring.upper() or "no-retention" in docstring.lower()
        ), "predict endpoint should document no-retention policy"

    def test_logger_does_not_log_image_bytes(self):
        """
        Logger configuration should not include image content.
        JSONFormatter logs timestamp, level, logger, message, module, function, line.
        """
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)

        data = json.loads(output)
        expected_keys = {
            "timestamp",
            "level",
            "logger",
            "message",
            "module",
            "function",
            "line",
        }
        assert set(data.keys()).issubset(expected_keys | {"exception"}), (
            f"Logger outputs unexpected fields: {set(data.keys()) - expected_keys}"
        )
