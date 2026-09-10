# Three-output model verification report

- **Model version:** `cattle-disease-mobilenetv3large-v20260902-pmk-fp32`
- **Artifact status:** `verified`
- **Activation ready:** `True`
- **Runtime:** `TensorFlow 2.21.0`

## Gates

| Gate | Result |
| --- | --- |
| `metadata_pair_contract` | PASS |
| `metadata_activation_status` | PASS |
| `artifact_checksums` | PASS |
| `tensor_contract_declaration` | PASS |
| `runtime_tensor_contract` | PASS |
| `finite_probability_contract` | PASS |
| `valid_image_top_class_parity` | PASS |
| `score_tolerance` | PASS |
| `labeled_corpus_expectations` | PASS |
| `corpus_label_provenance` | PASS |
| `corpus_file_integrity` | PASS |
| `corrupt_input_fixture` | PASS |
| `former_lsd_policy` | PASS |
| `class_identity_provenance` | PASS |
| `corpus_source_permissions` | PASS |
| `physical_android_offline_smoke` | PASS |

## Blockers

- None

## Corpus policy

Owner-approved policy: existing corpus images are team-owned and project labels are authoritative for this personal repository; no external URL, license, signature, or veterinary review is asserted.
Former-LSD filenames are historical source labels only and are never mapped to an active class. Every former-LSD cattle probe must avoid `non_cattle`; every corrupt fixture must be rejected before model invocation.
Option C known limitation is intentionally visible: non-cattle-human-02 (`mulut manusia.png`) is expected `non_cattle` but both runtimes predict FMD; the mismatch is accepted, not hidden or relabeled.

## Runtime case results

| Case | Category | Keras top | TFLite top | Max score delta | Invocations |
| --- | --- | --- | --- | --- | --- |
| `fmd-pmk-01` | `fmd` | `FMD` | `FMD` | `2.60770320892334e-08` | `2` |
| `fmd-pmk-02` | `fmd` | `FMD` | `FMD` | `1.7621459846850485e-12` | `2` |
| `fmd-pmk-03` | `fmd` | `FMD` | `FMD` | `1.1641532182693481e-10` | `2` |
| `fmd-pmk-04` | `fmd` | `FMD` | `FMD` | `4.76837158203125e-07` | `2` |
| `fmd-pmk-05` | `fmd` | `FMD` | `FMD` | `6.332993507385254e-08` | `2` |
| `fmd-pmk-06` | `fmd` | `FMD` | `FMD` | `2.510205376893282e-09` | `2` |
| `fmd-pmk-07` | `fmd` | `FMD` | `FMD` | `6.111804395914078e-10` | `2` |
| `fmd-pmk-08` | `fmd` | `FMD` | `FMD` | `9.313225746154785e-09` | `2` |
| `healthy-01` | `healthy` | `healthy` | `healthy` | `8.940696716308594e-07` | `2` |
| `healthy-02` | `healthy` | `healthy` | `healthy` | `2.980232238769531e-07` | `2` |
| `healthy-03` | `healthy` | `healthy` | `healthy` | `1.1920928955078125e-07` | `2` |
| `healthy-04` | `healthy` | `healthy` | `healthy` | `1.4202669262886047e-08` | `2` |
| `non-cattle-cat-01` | `non_cattle` | `non_cattle` | `non_cattle` | `1.564621925354004e-07` | `2` |
| `non-cattle-human-01` | `non_cattle` | `non_cattle` | `non_cattle` | `2.6193447411060333e-09` | `2` |
| `non-cattle-cat-02` | `non_cattle` | `non_cattle` | `non_cattle` | `2.3096799850463867e-07` | `2` |
| `non-cattle-human-02` | `non_cattle` | `FMD` | `FMD` | `6.556510925292969e-07` | `2` |
| `non-cattle-object-01` | `non_cattle` | `non_cattle` | `non_cattle` | `5.960464477539063e-08` | `2` |
| `former-lsd-01` | `former_lsd` | `FMD` | `FMD` | `1.1920928955078125e-07` | `2` |
| `former-lsd-02` | `former_lsd` | `healthy` | `healthy` | `2.4400651454925537e-07` | `2` |
| `former-lsd-03` | `former_lsd` | `FMD` | `FMD` | `2.384185791015625e-07` | `2` |
| `former-lsd-04` | `former_lsd` | `FMD` | `FMD` | `6.556510925292969e-07` | `2` |
| `corrupt-01` | `corrupt` | `not run` | `not run` | `not run` | `0` |

## Safety notes

- This report does not establish clinical diagnosis or disease confirmation.
- A pending report must not be used to activate backend or Flutter inference.
