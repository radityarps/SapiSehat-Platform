> **Legacy scope note:** This PRD documents the earlier Team 1 image/mobile subsystem. Current product scope is the full SapiSehat disease early detection platform. Start from [system integration README](../README.md) (`docs/system-integration/README.md`) and [platform PRD](PRD-platform-rebuild.md).

# PRD — SapiSehat: Model CNN & Sistem Mobile Android

**Product Requirements Document**
**Versi:** 5.0.0
**Tanggal:** Mei 2026 (revisi pasca-implementasi)
**Tim:** Raditya Rafif Pratama Sasmita & Noval Putra Ramadhan
**Institusi:** Teknik Informatika, Politeknik Negeri Semarang

> **Catatan revisi 5.0.0:** Dokumen ini telah diselaraskan dengan implementasi aktual per Mei 2026. Perubahan utama: framework backend dari PyTorch ke TensorFlow/Keras, label kelas disatukan ke `FMD`/`LSD`/`healthy`, preprocessing tahap 2 dari ImageNet normalization ke simple rescale, skema database diperbarui, penambahan `moshi-kotlin` pada mobile, dan penyederhanaan `isOnline()` untuk kompatibilitas emulator.

---

## 1. Ringkasan Sistem

Aplikasi Android **SapiSehat** untuk mendeteksi penyakit sapi (PMK dan LSD/Lato-Lato)
dari foto menggunakan CNN berbasis MobileNetV2.

### 1.1 Satu Model, Dua Format, Dua Tujuan

```
Training MobileNetV2 (TensorFlow/Keras)
(1 kali training, dataset yang sama)
          │
          ├──▶ mobilenetv2_best.keras  → Server (inferensi online via FastAPI)
          │                              HP tidak terbebani komputasi
          │
          └──▶ cattle_disease.tflite   → APK Android (inferensi offline)
                                         Dipakai saat tidak ada internet
```

Karena model yang sama, **hasil prediksi online dan offline identik**
untuk gambar yang sama.

> **Implementasi aktual:** Backend menggunakan TensorFlow/Keras langsung (bukan PyTorch).
> File model: `mobilenetv2_best.keras` (~20 MB). Model TFLite untuk offline masih dalam
> pengembangan — saat ini aplikasi mobile berjalan online-first dengan fallback ke
> error message jika server tidak tersedia.

### 1.2 Strategi Online First, Offline Fallback

```
Ada internet?
     │
  ┌──┴──┐
 YA    TIDAK
  │      │
  ▼      ▼
Kirim  Langsung
foto   pakai
ke     TFLite
server di HP
  │      │
  └──┬───┘
     ▼
Tampilkan hasil
```

- **Online**: foto dikirim ke server → inferensi di server → hasil ke HP
- **Offline**: foto diproses langsung di HP menggunakan TFLite
- **Fallback**: jika server gagal/timeout → otomatis beralih ke TFLite

### 1.3 Kelas Output

| Label | Kelas (canonical) | Display Label (Indonesia)   | Deskripsi                 |
| ----- | ----------------- | --------------------------- | ------------------------- |
| 0     | `healthy`         | Sapi Sehat                  | Tidak ada gejala penyakit |
| 1     | `FMD`             | Penyakit Mulut & Kuku (FMD) | Foot and Mouth Disease    |
| 2     | `LSD`             | Lumpy Skin Disease (LSD)    | Lato-Lato                 |

> **Catatan:** Label canonical (`FMD`/`LSD`/`healthy`) digunakan sebagai key di database,
> API response, dan skor. Display label (`"Sapi Sehat"`, dll.) ditampilkan ke pengguna.
> Kedua nilai dikembalikan oleh backend dalam field `label` dan `display_label`.

---

## 2. Preprocessing Gambar

### 2.1 Prinsip

Preprocessing dibagi menjadi dua tahap dengan tujuan yang berbeda:

```
TAHAP 1 — Di HP (sebelum upload / sebelum inferensi offline)
Tujuan: efisiensi jaringan + privasi

TAHAP 2 — Di server / di HP saat offline (sebelum masuk model)
Tujuan: menyiapkan input sesuai format yang diharapkan model CNN
```

### 2.2 Tahap 1 — Preprocessing di HP

```
Foto mentah dari kamera/galeri
(misal: 4000x3000px, ~4MB)
          │
          ▼
┌─────────────────────────────┐
│  1. Koreksi orientasi EXIF  │  → foto tidak terbalik
│  2. Resize max 800x800px    │  → hemat bandwidth upload
│  3. Kompres JPEG 85%        │  → kurangi ukuran file
│  4. Hapus metadata EXIF     │  → hilangkan data GPS/privasi
└─────────────────────────────┘
          │
          ▼
Output: ~100–300KB JPEG
```

> Tahap ini **tidak mengubah konten visual** secara signifikan,
> hanya menyiapkan gambar agar efisien dikirim atau diproses.

### 2.3 Tahap 2 — Preprocessing untuk Model CNN

```
Gambar dari Tahap 1
          │
          ▼
┌──────────────────────────────────────────┐
│  1. Resize ke 224x224px                  │
│     (ukuran input standar MobileNetV2)   │
│     Menggunakan LANCZOS interpolation    │
│                                          │
│  2. Konversi ke float32 + rescale ÷255   │
│     pixel: 0–255 → 0.0–1.0              │
│     (simple rescale, tanpa normalisasi)  │
│                                          │
│  3. Expand dimensi: [H,W,C] → [1,H,W,C] │
│     (tambah batch dimension)             │
└──────────────────────────────────────────┘
          │
          ▼
Array float32 [1, 224, 224, 3] siap masuk model
```

> **Implementasi aktual:** Backend menggunakan `ModelPreprocessor.process()` di
> `preprocessing/model_preprocessor.py` dengan simple rescale (`pixel / 255.0`).
> Mobile menggunakan `ClientPreprocessor` untuk Tahap 1 dan `ModelPreprocessor`
> untuk Tahap 2. Keduanya **tidak** menggunakan ImageNet normalization, karena
> model TensorFlow/Keras dilatih dengan preprocessing yang sama. Ini berbeda
> dari versi PRD sebelumnya (v4.0.0) yang menggunakan standardisasi ImageNet
> (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]).

### 2.4 Implementasi Preprocessing (Kode)

```python
# Backend (Python/TensorFlow) — Tahap 2 preprocessing
# Lihat: apps/backend/preprocessing/model_preprocessor.py
import numpy as np
from PIL import Image

def preprocess(image: Image.Image) -> np.ndarray:
    image = image.resize((224, 224), Image.LANCZOS)
    array = np.array(image, dtype=np.float32) / 255.0
    return np.expand_dims(array, axis=0)
```

```kotlin
// Mobile (Kotlin) — Tahap 2 preprocessing
// Lihat: apps/mobile/.../ml/preprocessing/ClientPreprocessor.kt
val resized = Bitmap.createScaledBitmap(bitmap, 224, 224, true)
for (pixel in pixels) {
    val r = (pixel shr 16 and 0xFF) / 255.0f
    val g = (pixel shr 8  and 0xFF) / 255.0f
    val b = (pixel        and 0xFF) / 255.0f
    buffer.putFloat(r); buffer.putFloat(g); buffer.putFloat(b)
}
```

> **Penting:** Preprocessing Tahap 2 harus **identik** antara server (Python)
> dan HP (Kotlin/TFLite). Implementasi aktual menggunakan simple rescale
> (`pixel / 255.0`) **tanpa** ImageNet normalization. Model TensorFlow/Keras
> dilatih dengan preprocessing yang sama.

---

## 3. Pembuatan Model CNN

### 3.1 Arsitektur: MobileNetV2

MobileNetV2 dipilih karena:

- Ringan setelah konversi TFLite (~4MB) → cocok untuk HP
- Akurasi cukup tinggi dengan transfer learning ImageNet
- Hasil prediksi online dan offline identik (model sama)
- Cocok untuk skala tugas akhir (tidak terlalu kompleks)

```python
# Implementasi aktual: TensorFlow/Keras
# Lihat: apps/backend/model/loader.py
import tensorflow as tf
model = tf.keras.models.load_model("mobilenetv2_best.keras")
```

> **Catatan implementasi:** Kode training dan evaluasi di Section 3.3–3.9 menggunakan
> PyTorch sebagai ilustrasi alur. Implementasi backend aktual menggunakan TensorFlow/Keras
> dengan file model `mobilenetv2_best.keras` (~20 MB). Model TFLite untuk offline masih
> dalam pengembangan.

### 3.2 Dataset

**Sumber:**

- Kaggle — Lumpy Skin Disease dataset (~500–1000 gambar)
- Roboflow Universe — FMD cattle dataset (~300–600 gambar)
- Data lapangan peternakan lokal (~60–150 gambar, 20–50/kelas)

**Struktur folder:**

```
dataset/
├── train/
│   ├── sehat/
│   ├── pmk/
│   └── lato_lato/
├── val/
│   ├── sehat/
│   ├── pmk/
│   └── lato_lato/
└── test/          ← tidak disentuh selama training
    ├── sehat/
    ├── pmk/
    └── lato_lato/
```

**Split:** 70% train / 15% val / 15% test

**Kriteria gambar yang diterima:**

- Resolusi minimal 224x224px
- Gejala terlihat jelas
- Tidak blur, tidak duplikat, label benar

### 3.3 Augmentasi saat Training

Augmentasi hanya diterapkan pada **training set**, tidak pada
val/test/inferensi. Tujuannya mensimulasikan kondisi foto lapangan
yang bervariasi agar model lebih robust.

```python
train_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(degrees=30),
    transforms.ColorJitter(
        brightness=0.4,    # variasi cahaya kandang vs outdoor
        contrast=0.4,
        saturation=0.3,
        hue=0.1
    ),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Val, test, dan inferensi — tanpa augmentasi
# Catatan: Implementasi aktual menggunakan simple rescale (÷255), bukan ImageNet normalization (lihat Section 2.3)
inference_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])
```

### 3.4 Training

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

def train_model(
    dataset_dir: str,
    output_path: str = "cattle_disease.pth",
    epochs: int = 30
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Dataset
    train_dataset = ImageFolder(f"{dataset_dir}/train", transform=train_transform)
    val_dataset   = ImageFolder(f"{dataset_dir}/val",   transform=inference_transform)

    train_loader = DataLoader(train_dataset, batch_size=32,
                              shuffle=True, num_workers=4, pin_memory=True)
    val_loader   = DataLoader(val_dataset,   batch_size=32,
                              shuffle=False, num_workers=4)

    model = create_model(num_classes=3).to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = train_correct = train_total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_correct += predicted.eq(labels).sum().item()
            train_total += labels.size(0)

        # Validation
        model.eval()
        val_correct = val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)

        train_acc = train_correct / train_total
        val_acc   = val_correct / val_total
        scheduler.step()

        print(f"Epoch [{epoch+1:02d}/{epochs}] "
              f"Loss: {train_loss/len(train_loader):.4f} | "
              f"Train: {train_acc:.4f} | Val: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), output_path)
            print(f"  ✓ Checkpoint disimpan (val_acc={val_acc:.4f})")

    print(f"\nTraining selesai. Akurasi terbaik: {best_val_acc:.4f}")
```

### 3.5 Evaluasi

```python
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def evaluate(model_path: str, dataset_dir: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    CLASS_NAMES = ["healthy", "FMD", "LSD"]

    model = create_model()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval().to(device)

    test_dataset = ImageFolder(f"{dataset_dir}/test", transform=inference_transform)
    test_loader  = DataLoader(test_dataset, batch_size=32, shuffle=False)

    all_preds  = []
    all_labels = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())

    # Classification report
    print(classification_report(all_labels, all_preds,
                                target_names=CLASS_NAMES, digits=4))

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
    plt.title('Confusion Matrix — MobileNetV2')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig("confusion_matrix.png")
    plt.show()
```

### 3.6 Konversi ke TFLite

```python
import tensorflow as tf
import numpy as np

def convert_to_tflite(
    model_path: str,
    dataset_dir: str,
    output_path: str = "cattle_disease.tflite"
):
    # Step 1: PyTorch → ONNX
    import torch.onnx, onnx, onnx_tf

    model = create_model()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    dummy = torch.randn(1, 3, 224, 224)
    torch.onnx.export(model, dummy, "temp.onnx",
                      input_names=["input"], output_names=["output"],
                      opset_version=11)
    print("Step 1: PyTorch → ONNX ✓")

    # Step 2: ONNX → TensorFlow SavedModel
    onnx_model = onnx.load("temp.onnx")
    tf_rep = onnx_tf.backend.prepare(onnx_model)
    tf_rep.export_graph("savedmodel_temp")
    print("Step 2: ONNX → TensorFlow ✓")

    # Step 3: TFLite + INT8 Quantization
    converter = tf.lite.TFLiteConverter.from_saved_model("savedmodel_temp")
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Kalibrasi quantization dengan 100 gambar training
    cal_dataset = ImageFolder(f"{dataset_dir}/train",
                              transform=inference_transform)

    def representative_dataset():
        for i in range(min(100, len(cal_dataset))):
            image, _ = cal_dataset[i]
            img = image.permute(1, 2, 0).numpy()          # CHW → HWC
            img = np.expand_dims(img, 0).astype(np.float32)
            yield [img]

    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type  = tf.float32
    converter.inference_output_type = tf.float32

    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)

    print(f"Step 3: TFLite INT8 ✓  →  {len(tflite_model)/1024/1024:.2f} MB")

# Jalankan
convert_to_tflite(
    model_path="cattle_disease.pth",
    dataset_dir="./dataset",
    output_path="cattle_disease.tflite"
)
```

### 3.7 Validasi TFLite

Pastikan akurasi TFLite tidak drop lebih dari 2% vs TF/Keras:

```python
def validate_tflite(tflite_path: str, dataset_dir: str):
    CLASS_NAMES = ["healthy", "FMD", "LSD"]

    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    input_idx  = interpreter.get_input_details()[0]['index']
    output_idx = interpreter.get_output_details()[0]['index']

    test_dataset = ImageFolder(f"{dataset_dir}/test",
                               transform=inference_transform)
    all_preds, all_labels = [], []

    for image, label in test_dataset:
        img = image.permute(1, 2, 0).numpy()
        img = np.expand_dims(img, 0).astype(np.float32)
        interpreter.set_tensor(input_idx, img)
        interpreter.invoke()
        output = interpreter.get_tensor(output_idx)
        all_preds.append(np.argmax(output[0]))
        all_labels.append(label)

    print(classification_report(all_labels, all_preds,
                                target_names=CLASS_NAMES, digits=4))
```

### 3.8 Target Metrik Model

| Metrik             | TF/Keras (.keras) | TFLite (.tflite) |
| ------------------ | ----------------- | ---------------- |
| Akurasi (test set) | ≥ 88%             | ≥ 86%            |
| Presisi per kelas  | ≥ 85%             | ≥ 83%            |
| Recall per kelas   | ≥ 85%             | ≥ 83%            |
| F1-Score           | ≥ 85%             | ≥ 83%            |
| Drop TF → TFLite   | —                 | ≤ 2%             |
| Ukuran file        | ~20 MB            | < 5 MB           |

### 3.9 Alur Training Lengkap

```
START
  │
  ▼
Kumpulkan & cleaning dataset
(validasi label, hapus blur/duplikat)
  │
  ▼
Split 70/15/15
  │
  ▼
Training MobileNetV2
(pretrained ImageNet + fine-tune + augmentasi)
  │
  ▼
Evaluasi di test set
(akurasi, presisi, recall, F1, confusion matrix)
Target: ≥ 88%
  │
  ├── [Tidak tercapai] → tambah data / tuning hyperparameter
  │
  ▼
Simpan mobilenetv2_best.keras → deploy ke server
  │
  ▼
Konversi ke TFLite (INT8 Quantization)
  │
  ▼
Validasi TFLite di test set
Target: drop ≤ 2%, ukuran < 5MB
  │
  ├── [Drop > 2%] → perbaiki kalibrasi quantization
  │
  ▼
Simpan cattle_disease.tflite → bundled ke APK
  │
  ▼
SELESAI
```

---

## 4. Sistem Mobile Android

### 4.1 Stack Teknologi

```
Language        : Kotlin
Min SDK         : API 24 (Android 7.0)
Target SDK      : API 34 (Android 14)
Architecture    : MVVM
DI Framework    : Hilt
```

### 4.2 Alur Sistem Lengkap

```
User foto sapi
      │
      ▼
Tahap 1 Preprocessing di HP
(koreksi EXIF, resize max 800px,
 kompres JPEG 85%, hapus metadata)
      │
      ▼
Ada internet?
      │
  ┌───┴───┐
 YA      TIDAK
  │        │
  ▼        ▼
Upload   Tahap 2 Preprocessing di HP
ke       (resize 224px, rescale
server   ÷255)
  │        │
  │     TFLite Inference
  │        │
  ├[gagal/timeout]──▶ fallback ke TFLite
  │        │
  └────┬───┘
       │
       ▼
Tampilkan hasil
(label + confidence + badge mode + saran)
       │
       ▼
Simpan ke Room DB
```

### 4.3 Struktur Package

```
com.sapisehat.app/
├── data/
│   ├── local/
│   │   ├── dao/DetectionDao.kt
│   │   ├── entity/DetectionEntity.kt
│   │   ├── AppDatabase.kt
│   │   └── SettingsDataStore.kt
│   ├── remote/
│   │   ├── api/InferenceApiService.kt
│   │   └── dto/PredictResponseDto.kt
│   └── repository/
│       └── DetectionRepository.kt
│
├── domain/
│   ├── model/
│   │   ├── DetectionResult.kt
│   │   └── InferenceMode.kt
│   └── usecase/ClassifyImageUseCase.kt
│
├── ml/
│   ├── InferenceRouter.kt              ← routing online/offline
│   ├── OnlineInferenceClient.kt        ← upload ke server
│   ├── OfflineInferenceEngine.kt       ← TFLite on-device
│   └── preprocessing/
│       ├── ClientPreprocessor.kt       ← Tahap 1 (kompres/EXIF)
│       └── ModelPreprocessor.kt        ← Tahap 2 (224px/rescale ÷255)
│
├── ui/
│   ├── camera/CameraRoute.kt + CameraViewModel.kt
│   ├── result/ResultRoute.kt + ResultViewModel.kt
│   ├── history/HistoryRoute.kt + HistoryViewModel.kt
│   ├── guide/GuideRoute.kt
│   ├── about/AboutRoute.kt
│   ├── onboarding/OnboardingRoute.kt
│   ├── settings/SettingsRoute.kt
│   ├── splash/SplashRoute.kt
│   ├── navigation/SapiSehatNavHost.kt
│   └── theme/Color.kt, Theme.kt, Type.kt
│
└── di/
    ├── AppModule.kt
    ├── DatabaseModule.kt
    └── NetworkModule.kt
```

### 4.4 Implementasi ClientPreprocessor.kt (Tahap 1)

```kotlin
@Singleton
class ClientPreprocessor @Inject constructor(private val context: Context) {

    fun process(imageUri: Uri): ByteArray {
        val bitmap = decodeBitmap(imageUri)
        val corrected = correctOrientation(bitmap, imageUri)  // koreksi EXIF
        val resized = resize(corrected, maxDimension = 800)   // resize max 800px

        // Kompres ke JPEG — metadata EXIF otomatis hilang karena encode ulang
        val output = ByteArrayOutputStream()
        resized.compress(Bitmap.CompressFormat.JPEG, 85, output)
        return output.toByteArray()
    }

    private fun decodeBitmap(uri: Uri): Bitmap =
        context.contentResolver.openInputStream(uri)?.use {
            BitmapFactory.decodeStream(it)
        } ?: throw IllegalArgumentException("Tidak dapat membaca gambar")

    private fun correctOrientation(bitmap: Bitmap, uri: Uri): Bitmap {
        val exif = context.contentResolver.openInputStream(uri)
            ?.use { ExifInterface(it) } ?: return bitmap

        val rotation = when (exif.getAttributeInt(
            ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL
        )) {
            ExifInterface.ORIENTATION_ROTATE_90  -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> return bitmap
        }
        val matrix = Matrix().apply { postRotate(rotation) }
        return Bitmap.createBitmap(bitmap, 0, 0,
            bitmap.width, bitmap.height, matrix, true)
    }

    private fun resize(bitmap: Bitmap, maxDimension: Int): Bitmap {
        val w = bitmap.width; val h = bitmap.height
        if (w <= maxDimension && h <= maxDimension) return bitmap
        val ratio = minOf(maxDimension.toFloat() / w, maxDimension.toFloat() / h)
        return Bitmap.createScaledBitmap(
            bitmap, (w * ratio).toInt(), (h * ratio).toInt(), true)
    }
}
```

### 4.5 Implementasi ModelPreprocessor.kt (Tahap 2)

```kotlin
@Singleton
class ModelPreprocessor @Inject constructor() {

    companion object {
        const val INPUT_SIZE = 224
        // Simple rescale ÷255 — tidak menggunakan ImageNet normalization
        // (lihat Section 2.3 dan docs/system-integration/architecture/legacy-architecture-overview.md)
    }

    /**
     * Konversi ByteArray JPEG → ByteBuffer siap masuk TFLite.
     * Hanya dipakai saat mode offline.
     * Saat online, preprocessing ini dilakukan di server (Python).
     */
    fun process(jpegBytes: ByteArray): ByteBuffer {
        // Decode JPEG → Bitmap
        val bitmap = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)

        // Resize ke 224x224
        val resized = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)

        // Alokasi ByteBuffer: float32 × 224 × 224 × 3 channel
        val buffer = ByteBuffer.allocateDirect(4 * INPUT_SIZE * INPUT_SIZE * 3)
        buffer.order(ByteOrder.nativeOrder())

        val pixels = IntArray(INPUT_SIZE * INPUT_SIZE)
        resized.getPixels(pixels, 0, INPUT_SIZE, 0, 0, INPUT_SIZE, INPUT_SIZE)

        for (pixel in pixels) {
            // Simple rescale: pixel 0–255 → 0.0–1.0
            val r = (pixel shr 16 and 0xFF) / 255.0f
            val g = (pixel shr 8  and 0xFF) / 255.0f
            val b = (pixel        and 0xFF) / 255.0f

            buffer.putFloat(r)
            buffer.putFloat(g)
            buffer.putFloat(b)
        }

        return buffer
    }
}
```

### 4.6 Implementasi OfflineInferenceEngine.kt

```kotlin
@Singleton
class OfflineInferenceEngine @Inject constructor(
    private val context: Context,
    private val modelPreprocessor: ModelPreprocessor
) {
    companion object {
        const val MODEL_FILE = "cattle_disease.tflite"
        const val CONFIDENCE_THRESHOLD = 0.60f
        val LABELS = listOf("healthy", "FMD", "LSD")
        val LABEL_DISPLAY = mapOf(
            "healthy"   to "Sapi Sehat",
            "FMD"       to "Penyakit Mulut & Kuku (FMD)",
            "LSD"       to "Penyakit Lato-Lato (LSD)"
        )
    }

    private val interpreter: Interpreter by lazy {
        context.assets.openFd(MODEL_FILE).let { fd ->
            val model = FileInputStream(fd.fileDescriptor).channel.map(
                FileChannel.MapMode.READ_ONLY,
                fd.startOffset, fd.declaredLength
            )
            Interpreter(model, Interpreter.Options().apply {
                numThreads = 4
                useNNAPI = true
            })
        }
    }

    suspend fun classify(jpegBytes: ByteArray): DetectionResult =
        withContext(Dispatchers.Default) {
            // Tahap 2 preprocessing
            val inputBuffer = modelPreprocessor.process(jpegBytes)
            val output = Array(1) { FloatArray(3) }

            interpreter.run(inputBuffer, output)

            val scores = output[0]
            val maxIdx = scores.indices.maxByOrNull { scores[it] } ?: 0
            val label  = LABELS[maxIdx]

            DetectionResult(
                label        = label,
                displayLabel = LABEL_DISPLAY[label] ?: label,
                confidence   = scores[maxIdx],
                isReliable   = scores[maxIdx] >= CONFIDENCE_THRESHOLD,
                allScores    = mapOf(
                    "healthy"   to scores[0],
                    "FMD"       to scores[1],
                    "LSD"       to scores[2]
                ),
                inferenceMode = InferenceMode.OFFLINE
            )
        }
}
```

### 4.7 Implementasi OnlineInferenceClient.kt

```kotlin
@Singleton
class OnlineInferenceClient @Inject constructor(
    private val apiService: InferenceApiService
) {
    // Tahap 2 preprocessing dilakukan di server (Python)
    // HP hanya upload JPEG hasil Tahap 1
    suspend fun classify(jpegBytes: ByteArray): DetectionResult =
        withContext(Dispatchers.IO) {
            val body = jpegBytes.toRequestBody("image/jpeg".toMediaType())
            val part = MultipartBody.Part.createFormData("image", "photo.jpg", body)
            val response = apiService.predict(part)

            DetectionResult(
                label        = response.prediction.label,
                displayLabel = response.prediction.displayLabel,
                confidence   = response.prediction.confidence,
                isReliable   = response.prediction.isReliable,
                allScores    = response.prediction.scores,
                inferenceMode = InferenceMode.ONLINE
            )
        }
}
```

### 4.8 Implementasi InferenceRouter.kt

```kotlin
@Singleton
class InferenceRouter @Inject constructor(
    private val clientPreprocessor: ClientPreprocessor,
    private val onlineClient: OnlineInferenceClient,
    private val offlineEngine: OfflineInferenceEngine,
    private val connectivityManager: ConnectivityManager
) {
    suspend fun classify(imageUri: Uri): DetectionResult {
        // Tahap 1 preprocessing selalu dilakukan
        val jpegBytes = withContext(Dispatchers.IO) {
            clientPreprocessor.process(imageUri)
        }

        return if (isOnline()) {
            try {
                onlineClient.classify(jpegBytes)       // server handle Tahap 2
            } catch (e: Exception) {
                offlineEngine.classify(jpegBytes)      // HP handle Tahap 2
                    .copy(inferenceMode = InferenceMode.OFFLINE_FALLBACK)
            }
        } else {
            offlineEngine.classify(jpegBytes)          // HP handle Tahap 2
        }
    }

    private fun isOnline(): Boolean {
        val caps = connectivityManager
            .getNetworkCapabilities(connectivityManager.activeNetwork ?: return false)
            ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }
}

enum class InferenceMode { ONLINE, OFFLINE, OFFLINE_FALLBACK }
```

---

## 5. Backend Server

### 5.1 Stack

```
Framework : FastAPI (Python)
Model     : MobileNetV2 (mobilenetv2_best.keras)
Server    : Uvicorn + Gunicorn
Deploy    : Docker
```

### 5.2 Implementasi Server

```python
# main.py (simplified — actual implementation uses singleton ModelLoader and routes module)
import io, time, asyncio
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import tensorflow as tf

app = FastAPI()

# Setup model (TF/Keras)
MODEL_VERSION = "5.0.0"
CLASS_NAMES = {0: "FMD", 1: "LSD", 2: "healthy"}
LABEL_DISPLAY = {
    "FMD":     "Penyakit Mulut & Kuku (FMD)",
    "LSD":     "Penyakit Lato-Lato (LSD)",
    "healthy": "Sapi Sehat"
}

# Load model once at startup
MODEL_PATH = "./model/mobilenetv2_best.keras"
model = tf.keras.models.load_model(MODEL_PATH)

# Tahap 2 preprocessing — simple rescale ÷255, tanpa ImageNet normalization
def preprocess(image: Image.Image) -> np.ndarray:
    img = image.resize((224, 224), Image.LANCZOS).convert("RGB")
    array = np.array(img, dtype=np.float32) / 255.0     # rescale ke [0, 1]
    return np.expand_dims(array, axis=0)                 # [1, 224, 224, 3]

@app.post("/api/predict")
async def predict(image: UploadFile = File(...)):
    start = time.time()

    if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(422, {"code": "INVALID_IMAGE"})

    try:
        img = Image.open(io.BytesIO(await image.read()))
        tensor = await asyncio.to_thread(preprocess, img)
    except Exception:
        raise HTTPException(422, {"code": "INVALID_IMAGE"})

    # Run inference (async via thread to avoid blocking event loop)
    output = await asyncio.to_thread(model.predict, tensor, verbose=0)
    probs = tf.nn.softmax(output[0]).numpy()

    idx = int(np.argmax(probs))
    label = CLASS_NAMES[idx]

    return JSONResponse({
        "status": "success",
        "prediction": {
            "label":         label,
            "display_label": LABEL_DISPLAY[label],
            "confidence":    round(float(probs[idx]), 4),
            "is_reliable":   float(probs[idx]) >= 0.60,
            "scores": {
                CLASS_NAMES[i]: round(float(probs[i]), 4)
                for i in range(3)
            }
        },
        "model_info": {"version": MODEL_VERSION},
        "processing_time_ms": int((time.time() - start) * 1000)
    })

@app.get("/api/health")
async def health():
    return {"status": "ok", "model_version": MODEL_VERSION}
```

---

## 6. Database Lokal (Room)

```sql
CREATE TABLE detection_records (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        INTEGER NOT NULL,
    predicted_class  TEXT NOT NULL,     -- 'FMD' | 'LSD' | 'healthy'
    display_label    TEXT NOT NULL,
    confidence       REAL NOT NULL,
    score_healthy    REAL NOT NULL,
    score_fmd        REAL NOT NULL,
    score_lsd        REAL NOT NULL,
    inference_mode   TEXT NOT NULL,     -- 'ONLINE' | 'OFFLINE' | 'OFFLINE_FALLBACK'
    is_reliable      INTEGER NOT NULL,
    processing_ms    INTEGER
);
```

---

## 7. Tampilan Hasil Deteksi

```
┌─────────────────────────────────────┐
│  [Foto yang dianalisis]             │
│                                     │
│  🌐 Analisis Online                 │  ← badge mode
│  ─────────────────────────────────  │
│  🔴 FMD TERDETEKSI                  │
│  Keyakinan: 94.3%                   │
│  [████████████░░] 94.3%             │
│                                     │
│  Sehat       ░░░░  3.1%             │
│  FMD         ████ 94.3%             │
│  LSD         ░░░░  2.6%             │
│                                     │
│  ⚠️ Saran Penanganan:               │
│  1. Isolasi sapi segera             │
│  2. Hubungi dokter hewan            │
│  3. Lapor ke Dinas Peternakan       │
│                                     │
│  [💾 Simpan] [📤 Bagikan] [🔄 Ulangi]│
└─────────────────────────────────────┘
```

**Badge mode:**

- `🌐 Analisis Online` — inferensi berhasil di server
- `📴 Analisis Offline` — tidak ada internet, TFLite lokal
- `⚠️ Offline (Server tidak merespons)` — fallback otomatis

**Threshold confidence:**

- ≥ 80%: hasil normal
- 60–79%: "Keyakinan sedang, pertimbangkan foto ulang"
- < 60%: "Foto kurang jelas, silakan coba lagi"

---

## 8. Metrik Keberhasilan

### 8.1 Model

| Metrik             | TF/Keras (.keras) | TFLite Offline |
| ------------------ | ----------------- | -------------- |
| Akurasi test set   | ≥ 88%             | ≥ 86%          |
| F1-Score per kelas | ≥ 85%             | ≥ 83%          |
| Drop TF → TFLite   | —                 | ≤ 2%           |
| Ukuran file        | ~20 MB            | < 5 MB         |

### 8.2 Aplikasi

| Metrik                               | Target        |
| ------------------------------------ | ------------- |
| Inferensi online end-to-end (4G)     | < 3 detik     |
| Inferensi offline (mid-range device) | < 1 detik     |
| Ukuran APK                           | < 20 MB       |
| Fallback otomatis                    | 100% berhasil |
| Crash rate                           | < 1% sesi     |

---

## 9. Timeline

```
Maret 2026 Week 3–4
  └── Pengumpulan & cleaning dataset, split 70/15/15

April 2026 Week 1
  └── Training MobileNetV2 + evaluasi test set

April 2026 Week 2
  └── Konversi TFLite + validasi akurasi & ukuran

April 2026 Week 3–4
  └── Setup project Android, MVVM, Hilt, Room DB
      ClientPreprocessor + ModelPreprocessor
      OfflineInferenceEngine + OnlineInferenceClient
      InferenceRouter + ResultFragment

Mei 2026 Week 1–2
  └── Backend FastAPI + deployment server

Mei 2026 Week 3–4
  └── HistoryFragment + GuideFragment
      End-to-end testing semua skenario koneksi

Juni 2026
  └── Field testing → revisi → finalisasi laporan

Juli 2026
  └── Ujian Pemaparan
```

---

## 10. Risiko & Mitigasi

| Risiko                                    | Dampak | Mitigasi                                     |
| ----------------------------------------- | ------ | -------------------------------------------- |
| Akurasi MobileNetV2 < 88%                 | Tinggi | Augmentasi lebih agresif, tambah data publik |
| TFLite drop > 2% setelah quantization     | Sedang | Perbanyak kalibrasi (200 gambar)             |
| Preprocessing HP ≠ server (inkonsistensi) | Tinggi | Unit test verifikasi output identik          |
| Dataset tidak seimbang antar kelas        | Sedang | Weighted loss atau oversampling              |
| Server timeout di jaringan 3G             | Sedang | Fallback otomatis, kompres gambar ketat      |

---

## 11. Glossary

| Istilah                | Penjelasan                                               |
| ---------------------- | -------------------------------------------------------- |
| PMK                    | Penyakit Mulut dan Kuku (FMD)                            |
| LSD / Lato-Lato        | Lumpy Skin Disease                                       |
| MobileNetV2            | Arsitektur CNN ringan, cocok untuk mobile                |
| TFLite                 | TensorFlow Lite — format model untuk Android             |
| INT8 Quantization      | Kompresi model FP32 → INT8, ukuran ~4x lebih kecil       |
| Inference              | Proses model memprediksi kelas dari gambar               |
| ImageNet Normalization | Tidak digunakan. Preprocessing pakai simple rescale ÷255 |
| Augmentasi             | Variasi gambar saat training agar model lebih robust     |
| Tahap 1 Preprocessing  | Di HP: kompres/EXIF untuk efisiensi transfer             |
| Tahap 2 Preprocessing  | Di server/HP: resize 224px + rescale ÷255 untuk model    |
| InferenceRouter        | Komponen yang memutuskan jalur online atau offline       |
| Fallback               | Beralih otomatis ke TFLite saat server gagal             |

---

_PRD v5.0.0 — 1 model MobileNetV2, 2 format (.keras server + .tflite mobile),
preprocessing simple rescale, sistem online first dengan offline fallback._
