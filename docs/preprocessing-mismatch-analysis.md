# Preprocessing Mismatch Analysis — Backend vs Partner Model

**Date:** 2026-05-04
**Project:** SapiSehat — Tugas Akhir
**Status:** CRITICAL — must resolve before model integration

---

## Summary

The backend (FastAPI/PyTorch) and the trained model (Keras/TensorFlow) use fundamentally
different preprocessing pipelines. If the backend applies its current ImageNet normalization
to images before sending them to the partner's model, predictions will be WRONG — the model
was never trained to expect that input distribution.

---

## What the Partner's Model Expects

From `TA_training_model.ipynb`, training cell (lines 297-298):

```python
train_datagen = ImageDataGenerator(rescale=1./255)
valid_datagen = ImageDataGenerator(rescale=1./255)
```

Inference/prediction cell (lines 605-608):

```python
img = image.load_img(image_path, target_size=(224, 224))
img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0) / 255.0
```

**The full pipeline:**
1. Resize to 224×224
2. Convert to float32
3. Divide by 255.0 (pixel values become [0.0, 1.0])
4. Feed directly to model

**There is NO:**
- ImageNet mean subtraction
- ImageNet standard deviation division
- `preprocess_input()` call
- Any normalization beyond simple rescale

---

## What the Backend Currently Does

From `preprocessing/model_preprocessor.py` (lines 28-30, 35-42):

```python
MEAN = [0.485, 0.456, 0.406]   # ImageNet statistics
STD  = [0.229, 0.224, 0.225]

transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),            # Converts to [0.0, 1.0] float32
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],  # (pixel - mean) / std
        std=[0.229, 0.224, 0.225]
    )
])
```

The backend additionally applies:
- Mean subtraction: pixel_channel_0 - 0.485, pixel_channel_1 - 0.456, pixel_channel_2 - 0.406
- Standard deviation division: divide each channel by [0.229, 0.224, 0.225]

This transforms the input into a completely different numerical range (~[-2.0, 2.0])
compared to what the model was trained on ([0.0, 1.0]).

---

## Why This Matters — Concrete Example

For a mid-gray pixel (128, 128, 128):

| Step | Backend (ImageNet) | Partner Model (Rescale) |
|---|---|---|
| Raw pixel | (128, 128, 128) | (128, 128, 128) |
| After processing | (-0.672, -0.639, -0.503) | (0.502, 0.502, 0.502) |

The backend produces NEGATIVE values; the model expects POSITIVE values in [0, 1].

---

## Why the Notebook Comment About MobileNetV2 Is Misleading

From `docs/PRD.md` (line 123-127):

> "Mengapa standardisasi ImageNet tidak bisa dilewati? MobileNetV2 menggunakan
> bobot pretrained ImageNet. Saat training ImageNet, semua gambar distandardisasi
> dengan nilai tersebut."

This was the original assumption in the PRD — that ImageNet normalization is required.
However, the partner **did not apply** ImageNet normalization during training.
They used `rescale=1./255` only.

**Why this still works:** The pretrained MobileNetV2 weights DO expect ImageNet-normalized
inputs, but since the partner froze the base model and only trained the classification
head, the model may have adapted to the [0,1] input range. More importantly: the model
achieved **98.86% validation accuracy** with this exact preprocessing, so it clearly
works — whatever internal adaptation happened is irrelevant. What matters is that
inference must use the **same preprocessing as training**.

---

## What Must Be Done

### For the Backend Inference Server:

Replace ImageNet normalization with simple rescale:

```python
# CORRECT — matches partner's training
img = image.resize((224, 224))
img_array = np.array(img, dtype=np.float32) / 255.0
img_array = np.expand_dims(img_array, axis=0)
```

### For the Android App (TFLite mode):

When the partner provides the TFLite model, the Kotlin preprocessing
(`ModelPreprocessor.kt`) must also be updated to match — rescale only,
no ImageNet normalization.

### For the Android App (online mode):

The client-side Tahap 1 preprocessing (resize, compress, strip EXIF) is fine.
The server handles Tahap 2 (resize to 224×224, rescale /255).

---

## Verification Checklist

- [ ] Load partner's `.keras` model
- [ ] Test with a known image using rescale-only preprocessing
- [ ] Verify prediction matches notebook output for the same image
- [ ] Compare with ImageNet-normalized version to confirm it produces DIFFERENT (wrong) results
- [ ] Update `model_preprocessor.py`
- [ ] Update mobile `ModelPreprocessor.kt` when TFLite model is available
- [ ] Document the chosen preprocessing in project README or DEVELOPMENT.md
