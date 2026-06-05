"""
Google Colab wrapper cell (issue #19) — FALLBACK training environment.

Paste this into a Colab cell. It is a THIN wrapper: all training and evaluation
logic lives in the repository (`docs/model/training_wrapper.py` ->
`docs/model/evaluate_candidates.py`). No secret-only notebook logic.

Setup on Colab:
  1. Enable GPU: Runtime -> Change runtime type -> T4 GPU.
  2. Clone the repository:

        !git clone https://github.com/radityarps/Tugas-Akhir-Klasifikasi-Penyakit-Sapi-CNN.git repo

  3. Provide the dataset. Options:
       - Mount Google Drive and point DATA_DIR at the dataset folder:
            from google.colab import drive; drive.mount('/content/drive')
       - Or download it into /content (run OUTSIDE version control):
            !curl -L "<your-dataset-url>" > roboflow.zip && unzip -q roboflow.zip -d data && rm roboflow.zip
  4. Run the wrapper (edit DATA_DIR):
"""

import subprocess
import sys

# --- EDIT THESE for your Colab session ---
REPO_DIR = "repo"
DATA_DIR = "/content/data"  # dataset path (Drive mount or downloaded folder)
ARCHITECTURE = "mobilenetv2"
SEED = 42
EPOCHS = 50
OUT_DIR = "/content/run_out"
# Preferred: build the approved fixed-seed 70/15/15 split (issue #18) and train
# from its manifest. Set to False to fall back to raw train/valid folders.
USE_PREPARED_SPLIT = True
PREP_OUT = "/content/dataset_artifacts"
# ------------------------------------------

if USE_PREPARED_SPLIT:
    # 1) Generate the prepared split manifest from the dataset.
    prep = [
        sys.executable, "-m", "dataset_prep.cli",
        "--data", DATA_DIR, "--out", PREP_OUT,
    ]
    print("Preparing split:", " ".join(prep))
    rc = subprocess.call(prep, cwd=f"{REPO_DIR}/apps/backend")
    if rc != 0:
        raise SystemExit(rc)
    # 2) Train/evaluate from the manifest (train->train, valid->early stop,
    #    test->final metrics). Bundles the #18 artifacts automatically.
    cmd = [
        sys.executable,
        f"{REPO_DIR}/docs/model/training_wrapper.py",
        "--manifest", f"{PREP_OUT}/split_manifest.csv",
        "--architecture", ARCHITECTURE,
        "--seed", str(SEED),
        "--epochs", str(EPOCHS),
        "--out", OUT_DIR,
    ]
else:
    cmd = [
        sys.executable,
        f"{REPO_DIR}/docs/model/training_wrapper.py",
        "--data", DATA_DIR,
        "--architecture", ARCHITECTURE,
        "--seed", str(SEED),
        "--epochs", str(EPOCHS),
        "--out", OUT_DIR,
    ]
print("Running:", " ".join(cmd))
raise SystemExit(subprocess.call(cmd))

# After completion, download the versioned bundle from OUT_DIR:
#   model_training_artifacts_cattle-disease-<arch>-vYYYYMMDD-s<seed>.zip
# from google.colab import files
# files.download(f"{OUT_DIR}/model_training_artifacts_...zip")
