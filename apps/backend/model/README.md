> **Team 1 image subsystem note:** This model folder supports image inference prototype only. Platform contracts live in `docs/../README.md`; Team 1 docs live in `docs/team-1-image/README.md`. Shared platform contracts path: `docs/system-integration/README.md`.

# Model Directory

Place your trained MobileNetV2 model here.

## File: cattle_disease.pth

This should be a PyTorch checkpoint with:
- Architecture: MobileNetV2 with 3 output classes
- Input size: 224x224x3
- Output classes: SEHAT (0), PMK (1), LATO_LATO (2)

## How to generate model

See training script in repository root: `train_model.py`

## File size

Typical size: ~14 MB (MobileNetV2 with 3 classes)

## Important

The model file is NOT included in Git (see .gitignore).
You must obtain/generate it and place it here before running the backend.
