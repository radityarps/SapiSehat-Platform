"""
Kaggle wrapper cell (issue #19) — PRIMARY training environment.

Paste this into a Kaggle Notebook cell. It is a THIN wrapper: all training and
evaluation logic lives in the repository (`docs/model/training_wrapper.py` ->
`docs/model/evaluate_candidates.py`). No secret-only notebook logic.

Setup on Kaggle:
  1. Enable GPU: Notebook settings -> Accelerator -> GPU.
  2. Add the dataset as a Kaggle Dataset input, OR clone this repo and point
     --data at the dataset path.
  3. Make the repo available (clone or add as a Utility Script / Dataset):

        !git clone https://github.com/radityarps/Tugas-Akhir-Klasifikasi-Penyakit-Sapi-CNN.git repo

  4. Run the wrapper (edit DATA_DIR to your Kaggle input path):
"""

import subprocess
import sys

# --- EDIT THESE for your Kaggle session ---
REPO_DIR = "repo"  # where you cloned the repository
DATA_DIR = "/kaggle/input/pmk-dan-penyakit-lato-lato"  # your dataset input path
ARCHITECTURE = "mobilenetv2"
SEED = 42
EPOCHS = 50
OUT_DIR = "/kaggle/working/run_out"
# Preferred: build the approved fixed-seed 70/15/15 split (issue #18) and train
# from its manifest. Set to False to fall back to raw train/valid folders.
USE_PREPARED_SPLIT = True
PREP_OUT = "/kaggle/working/dataset_artifacts"
# -------------------------------------------

if USE_PREPARED_SPLIT:
    # 1) Generate the prepared split manifest from the dataset.
    #    PREP_OUT is absolute, so the CLI writes there regardless of cwd.
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
# and copy it back into the repository (e.g. docs/model/artifacts/).
