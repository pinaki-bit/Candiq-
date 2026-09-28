# Phase 22 — Model Integrity Audit & Independent Validation Report

## 1. Evaluation Protocol Correctness

- **Phase 21 Protocol Audit Finding**: In Phase 21E, the baseline production model (`model_latest.joblib`) was evaluated on `val.csv` (277 records), whereas Candidate Model v2 (`model_v2.joblib`) was evaluated on `test.csv` (278 records).
- **Phase 22 Correction**: Both models have now been evaluated on the **EXACT SAME 278 UNTOUCHED TEST RECORDS** (`ml/data/processed/test.csv`), establishing a 100% fair and rigorous evaluation protocol.
- Documented in [`MODEL_EVALUATION_PROTOCOL_AUDIT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/MODEL_EVALUATION_PROTOCOL_AUDIT.md).

---

## 2. True Baseline Test Performance

Evaluated `ml/artifacts/model_latest.joblib` (LinearSVC v20260922_235001) on `test.csv` (278 records):
- **Accuracy**: **88.85%**
- **Macro Precision**: **0.7101** | **Macro Recall**: **0.7474** | **Macro F1 Score**: **0.7205**
- **Weighted Precision**: **0.8685** | **Weighted Recall**: **0.8885** | **Weighted F1 Score**: **0.8721**
- **Cloud Computing Recall**: **0.0000 (0/14 correct)** — Confirming the baseline 0% recall flaw exists on the test set.
- Saved to [`reports/baseline_test_metrics.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/baseline_test_metrics.json).

---

## 3. True Candidate v2 Test Performance

Evaluated `ml/artifacts/model_v2.joblib` (Calibrated LinearSVC v2.0.0) on the exact same `test.csv` (278 records):
- **Accuracy**: **97.84%**
- **Macro Precision**: **0.9840** | **Macro Recall**: **0.9783** | **Macro F1 Score**: **0.9810**
- **Weighted Precision**: **0.9787** | **Weighted Recall**: **0.9784** | **Weighted F1 Score**: **0.9784**
- **Cloud Computing Recall**: **1.0000 (14/14 correct)** — Fully resolving the baseline flaw.
- Saved to [`reports/final_test_metrics.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/final_test_metrics.json).

---

## 4. Fair Baseline vs. v2 Test Comparison

| Evaluation Metric | True Baseline (`model_latest.joblib`) | Candidate Model v2 (`model_v2.joblib`) | Absolute Diff (Identical Test Set) |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 88.85% | **97.84%** | **+8.99%** |
| **Macro Precision** | 0.7101 | **0.9840** | **+0.2739** |
| **Macro Recall** | 0.7474 | **0.9783** | **+0.2309** |
| **Macro F1 Score** | 0.7205 | **0.9810** | **+0.2605 (+36.2% relative gain)** |
| **Weighted F1 Score** | 0.8721 | **0.9784** | **+0.1063** |
| **Cloud Computing Recall** | **0.0000 (0%)** | **1.0000 (100%)** | **+1.0000 (+100%)** |

Documented in [`FAIR_MODEL_COMPARISON.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/FAIR_MODEL_COMPARISON.md) and [`reports/fair_baseline_vs_v2_test_comparison.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/fair_baseline_vs_v2_test_comparison.json).

---

## 5. Independent Validation Status

- **Audit Finding**: The 25 sample resumes evaluated in Phase 21P were drawn directly from `test.csv` via `test_df.groupby('Mapped_Category').apply(...)`.
- **Correction**: These 25 records have been officially re-labeled as **Stratified Subsample Validation** (25 test records) rather than an independent external dataset.
- Documented in [`INDEPENDENT_VALIDATION_AUDIT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/INDEPENDENT_VALIDATION_AUDIT.md).

---

## 6. Calibration Status

- **Brier Score**: **0.0290** (near-perfect probability estimation).
- **Expected Calibration Error (ECE)**: **0.0441 (4.41%)**.
- **Reliability Breakdown**:
  - High Confidence Bin ($\ge 80\%$): 260 / 278 samples -> **100.0% Empirical Test Accuracy**.
  - Low Confidence Bin ($< 60\%$): 6 / 278 samples -> **33.3% Empirical Accuracy**.
- Documented in [`CALIBRATION_AUDIT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/CALIBRATION_AUDIT.md) and [`reports/calibration_metrics.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/calibration_metrics.json).

---

## 7. Duplicate Detection Status

- **Audit Finding**: Phase 21C executed **MD5 snippet hashing over normalized leading 400 characters**, which successfully removed 55 template/contact duplicate resumes. It was incorrectly described as "token Jaccard similarity > 0.90".
- **Action**: Corrected documentation without modifying current dataset splits. MinHash + LSH + Jaccard token overlap recommended for future dataset ingestion pipelines.
- Documented in [`DUPLICATE_DETECTION_AUDIT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/DUPLICATE_DETECTION_AUDIT.md).

---

## 8. Dataset Generalization Risks

- **Synthetic Header Artifact**: 687 resumes (55.5% of `resumes.csv`) contain a standardized placeholder header (`"Jessica Claire 100 Montgomery St..."`).
- **Cloud Computing Sample Scarcity**: Cloud Computing has 92 total clean samples (14 in test set). Out-of-distribution cloud architectures could experience lower real-world accuracy.
- Documented in [`DATASET_GENERALIZATION_RISK.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/DATASET_GENERALIZATION_RISK.md).

---

## 9. Production Promotion Blockers

1. **Explicit User Promotion Authorization**: Candidate Model v2 (`model_v2.joblib`) remains in `ml/artifacts/` and must not overwrite `model_latest.joblib` until explicitly authorized by the user.
2. **Contact Header Preprocessing Cleanup**: Contact header template stripping should be added to `preprocessing.py` before final model promotion.

---

## 10. Recommended Next Phase

- **Phase 23: Controlled Model Promotion & Production Deployment**:
  - Upon user authorization, promote `model_v2.joblib` to `model_latest.joblib` (preserving a versioned backup `model_v1_legacy.joblib`).
  - Update `classification_service.py` model metadata loader to report Calibrated LinearSVC v2.0.0.
  - Execute full regression test suite to verify end-to-end backend and Streamlit UI functionality.

---

> [!IMPORTANT]
> - `model_v2.joblib` has NOT been promoted.
> - `model_latest.joblib` remains preserved and active on disk.
> - Production APIs and frontend code remain unchanged.

---

*Phase 22 Model Integrity Audit complete. Awaiting user instructions.*
