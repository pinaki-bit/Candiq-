# 📋 Phase 22A: Model Evaluation Protocol Audit

This audit independently verifies the dataset splits and evaluation protocols utilized during **Phase 21** for both the baseline production model (`ml/artifacts/model_latest.joblib`) and the candidate model (`ml/artifacts/model_v2.joblib`).

---

## 🔍 Dataset Split Usage Matrix

| Evaluation Stage / Task | Dataset File Used in Phase 21 | Record Count | Stratified | Correct Protocol? | Audit Finding |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Baseline Production Evaluation (Phase 21E)** | `ml/data/processed/val.csv` | 277 | Yes | ❌ **MISMATCH** | Evaluated on **Validation set** instead of the untouched Test set. |
| **Model Experiments (Phase 21G)** | Train: `train.csv`<br/>Val: `val.csv` | Train: 1,293<br/>Val: 277 | Yes | ✅ **CORRECT** | Models A–F trained on Train set, selected using Validation set. |
| **Hyperparameter Tuning (Phase 21I)** | Train: `train.csv`<br/>Val: `val.csv` | Train: 1,293<br/>Val: 277 | Yes | ✅ **CORRECT** | Grid search tuned on Train set, evaluated on Validation set. |
| **Probability Calibration (Phase 21L)** | Train+Val: `train.csv` + `val.csv` | 1,570 | Yes | ✅ **CORRECT** | 5-Fold `CalibratedClassifierCV` fitted on Train+Val prior to testing. |
| **Candidate Model v2 Test (Phase 21K)** | `ml/data/processed/test.csv` | 278 | Yes | ✅ **CORRECT** | Evaluated on the untouched Test set. |
| **"Real Resume Validation" (Phase 21P)** | `ml/data/processed/test.csv` | 25 | Yes | ❌ **MISLABELED** | Sampled from **`test.csv`**, NOT an independent external dataset. |

---

## ⚠️ Protocol Flaws & Mislabeled Metrics Identified

1. **Baseline vs Candidate Dataset Mismatch**:
   - In Phase 21E, the baseline model (`model_latest.joblib`) was evaluated on `val.csv` (277 records), yielding `Accuracy = 87.00%` and `Macro F1 = 0.7066`.
   - In Phase 21K, candidate model v2 (`model_v2.joblib`) was evaluated on `test.csv` (278 records), yielding `Accuracy = 97.84%` and `Macro F1 = 0.9810`.
   - **Audit Finding**: Comparing baseline on `val.csv` against candidate v2 on `test.csv` violated the identical test population requirement. Both models must be evaluated on the exact same 278 test records in `test.csv`.

2. **Mislabeled "Independent External Validation"**:
   - Phase 21P evaluated 25 resumes and claimed "Independent Validation on Public Resumes".
   - **Audit Finding**: Inspection of `validate_real_resumes_v2.py` reveals these 25 samples were drawn directly from `test.csv` via `test_df.groupby('Mapped_Category').apply(...)`. Describing a subset of the test set as "independent external validation" was incorrect.

---

## 🛠️ Required Protocol Corrections in Phase 22

- **Phase 22B**: Evaluate `model_latest.joblib` directly on `test.csv` (278 records).
- **Phase 22C**: Compare `model_latest.joblib` vs `model_v2.joblib` on the exact same 278 test records in `test.csv`.
- **Phase 22D**: Re-label Phase 21P results as **Test Subsample Validation** (25 test records).

---

*Phase 22A Evaluation Protocol Audit complete.*
