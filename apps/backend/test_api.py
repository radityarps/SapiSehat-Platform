"""
Quick check script for SapiSehat Backend API (Windows/Linux/Mac).

Usage:
    python test_api.py

Requirements:
    - Server running on localhost:8000
    - requests library installed (pip install requests)
"""

import json
from pathlib import Path

import requests
from PIL import Image

BASE_URL = "http://localhost:8000/api"


def check_health() -> bool:
    """Check health endpoint from a running local server."""
    print("Testing /api/health endpoint...")
    response = requests.get(f"{BASE_URL}/health", timeout=30)

    if response.status_code == 200:
        print("✓ Health check passed")
        print(f"Response: {response.json()}\n")
        return True

    print(f"✗ Health check failed: {response.status_code}")
    return False


def check_predict(image_path: str) -> bool:
    """Check predict endpoint from a running local server."""
    print(f"Testing /api/predict endpoint with {image_path}...")

    if not Path(image_path).exists():
        print(f"✗ Image file not found: {image_path}")
        return False

    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(f"{BASE_URL}/predict", files=files, timeout=60)

    if response.status_code != 200:
        print(f"✗ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()
    if result.get("status") != "success":
        print(f"✗ Prediction failed: {result.get('message')}")
        return False

    print("✓ Prediction successful")
    print(f"Response: {json.dumps(result, indent=2)}\n")

    prediction = result["prediction"]
    print(f"Predicted class: {prediction['disease_class']}")
    print(f"Display label key: {prediction['display_label_key']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"Reliable: {prediction['is_reliable']}")
    print(f"Processing time: {result['processing_time_ms']}ms\n")

    return True


def create_test_image(path: str = "test_image.jpg") -> None:
    """Create a simple test image."""
    print(f"Creating test image: {path}...")
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    img.save(path)
    print("✓ Test image created\n")


if __name__ == "__main__":
    print("SapiSehat Backend API Test\n")
    print("=" * 50 + "\n")

    if not check_health():
        print("✗ Server not running. Start with: python main.py")
        raise SystemExit(1)

    test_image_path = "test_image.jpg"
    if not Path(test_image_path).exists():
        create_test_image(test_image_path)

    if check_predict(test_image_path):
        print("✓ All checks passed!")
    else:
        print("✗ Checks failed")
        raise SystemExit(1)
