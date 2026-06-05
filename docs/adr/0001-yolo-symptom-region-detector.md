# Use YOLO-family detector for symptom regions

SapiSehat will evaluate a small YOLO-family detector as the first **Symptom Region Detector** for the server-first two-stage pipeline, while keeping the existing TensorFlow/Keras classifier pipeline for disease classification and Android fallback. This deliberately breaks the earlier single-framework assumption because symptom-region detection benefits from YOLO's object-detection tooling and annotation workflow, and the detector is introduced server-side before any mobile portability commitment.

**Considered Options**

- TensorFlow/Keras object detection stack — better framework consistency, but heavier setup and less direct tooling for the planned annotation workflow.
- KerasCV YOLO — closer to the existing stack, but not selected as the first baseline because the project needs a practical detection baseline before mobile export pressure.

**Consequences**

- Two-stage server inference may use both PyTorch/Ultralytics-style detector tooling and TensorFlow/Keras classifier artifacts.
- Android on-device inference remains the current single-stage TFLite fallback until detector size, latency, and parity are proven.
