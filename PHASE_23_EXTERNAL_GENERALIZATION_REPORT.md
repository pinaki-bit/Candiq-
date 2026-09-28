# Phase 23C — Independent External Generalization & Robustness Evaluation Report

## 1. Executive Summary

Phase 23C performs an independent, zero-shot external generalization and out-of-domain (OOD) robustness evaluation of candidate model **`model_v2.joblib`** (Calibrated LinearSVC v2.0.0).

This phase evaluates model behavior on three distinct non-training datasets without model retraining, hyperparameter tuning, threshold modification, or metric manipulation:
1. **Independent Out-of-Domain PDF Corpus** (`archive_1/Resumes PDF/`): 1,874 PDF documents across 17 non-IT professional categories.
2. **Out-of-Domain Negative Test** (`ocr_results.csv`): 283 OCR-extracted text records from Accountant PDF resumes.
3. **Independent Synthetic Test Set ($N=5$)** (`audit_pdfs/*.pdf`): 5 out-of-band synthetic test resumes (1 per canonical target class).

---

## 2. Evaluation Scope & Protocol

- **Evaluation Mode**: Zero-shot inference only. No gradient updates, threshold changes, or re-calibration.
- **Exclusions**: `ml/data/raw/master_combined.csv` (20,306 records) was **EXCLUDED** from external generalization metrics, as Phase 23B established it is **Unseen Same-Family Contaminated** (sharing 6,834 synthetic template headers with training data).
- **Inference Service**: Standard Scikit-Learn `predict_proba()` inference pipeline on raw extracted text.

---

## 3. Model & Data Preservation Verification

Pre-evaluation and post-evaluation SHA-256 hashes were recorded to guarantee 100% model and split immutability:

| File Path | SHA-256 Hash (Pre & Post Match Verified) | Immutability Status |
| :--- | :--- | :---: |
| `ml/artifacts/model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **UNTOUCHED** |
| `ml/artifacts/model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **UNTOUCHED** |
| `ml/data/processed/train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **UNTOUCHED** |
| `ml/data/processed/val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **UNTOUCHED** |
| `ml/data/processed/test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **UNTOUCHED** |

---

## 4. Dataset Evaluation Findings

### A. Independent Out-of-Domain PDF Corpus (`archive_1/Resumes PDF/`)
- **Dataset Size**: 1,874 PDF documents across 17 non-IT professional categories (Accountant, Advocate, Aviation, Agricultural, Apparel, Architect, Arts, Automobile, etc.).
- **Extraction Result**: **100% Extraction Failure / Empty Text** (1,874 / 1,874).
- **Root Cause Analysis**: Detailed PDF inspection revealed that all 1,874 PDFs in `archive_1` are **scanned image-only PDFs** containing bitmap images of resumes without embedded digital text layers. Direct text extraction (via PyMuPDF / PyPDF2) yields 0 characters per document.
- **Model Behavior**: Returned `UNMAPPED` status with 0.0 confidence due to empty input text.

### B. Out-of-Domain Negative Test (`ocr_results.csv`)
- **Dataset Size**: 283 OCR-extracted text records from Accountant PDF resumes.
- **Classification Status**: 100% out-of-domain (`Accountant`).
- **Processing Success Rate**: 283 / 283 (100.0%).
- **Predicted Class Distribution**:
  - `Web Development`: **271 records** (95.8%)
  - `Data Science`: **12 records** (4.2%)
  - `Cloud Computing`: 0 records
  - `DevOps`: 0 records
  - `Cybersecurity`: 0 records
- **Confidence Metrics**:
  - Mean Confidence: **0.7115** | Median Confidence: **0.7269**
- **High-Confidence Out-of-Domain False Positives ($\ge 0.80$ Confidence)**:
  - **42 records** (14.8% of all Accountant resumes) were classified as `Web Development` or `Data Science` with confidence $\ge 0.80$.
- **Finding**: Because the 5-class model lacks an explicit `Unmapped / Out-of-Domain` class or an active confidence abstention threshold, out-of-domain resumes are forced into the closest technical category (`Web Development` due to broad lexical term overlap).

### C. Independent Synthetic Test Set ($N=5$) (`audit_pdfs/*.pdf`)
- **Dataset Size**: 5 digital PDF resumes authored in Phase 20 (1 per canonical target class).
- **Purpose**: End-to-End Synthetic Pipeline Sanity Check ($N=5$).
- **Results Table**:

| Synthetic PDF File | Expected Target Class | Predicted Class | Status | Confidence | Latency (ms) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `resume_cloud_elena.pdf` | Cloud Computing | **Cloud Computing** | **MATCH** | 84.61% | 16.70 ms |
| `resume_devops_marcus.pdf` | DevOps | **DevOps** | **MATCH** | 96.92% | 3.46 ms |
| `resume_ds_alex.pdf` | Data Science | **Data Science** | **MATCH** | 99.11% | 4.97 ms |
| `resume_sec_david.pdf` | Cybersecurity | **Cybersecurity** | **MATCH** | 96.95% | 3.45 ms |
| `resume_web_sarah.pdf` | Web Development | **Web Development** | **MATCH** | 99.05% | 3.30 ms |

- **Sanity Check Accuracy**: **100.0% (5 / 5 correct)**.
- **Mean Synthetic Confidence**: **95.33%**.
- **Mean Pipeline Latency**: **6.37 ms**.

---

## 5. High-Confidence Out-of-Domain False Positive Analysis

When evaluating out-of-domain `Accountant` resumes (`ocr_results.csv`):
- **14.8% (42 / 283)** of Accountant resumes produced predictions with confidence $\ge 0.80$.
- **Primary Driver**: Accountant resumes frequently mention generic business, analytical, software, and administrative terms (e.g., `"data analysis"`, `"reporting"`, `"system"`, `"management"`), which trigger high TF-IDF weights toward `Web Development` and `Data Science`.
- **System Weakness**: In closed-world 5-class classification without an abstention threshold, out-of-domain inputs are forced into target classes with high confidence.

---

## 6. Source-Category Breakdown for PDF Corpus (`archive_1`)

All 17 subdirectories in `archive_1/Resumes PDF/` consist of image-only PDFs:

| Source Category Folder | Total PDFs | Successfully Extracted Text | Empty Text Count | Dominant Prediction | Mean Confidence | High-Conf Rate ($\ge 0.80$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `Accountant` | 284 | 0 | 284 | UNMAPPED | 0.00% | 0.0% |
| `Accountant resumes` | 67 | 0 | 67 | UNMAPPED | 0.00% | 0.0% |
| `Advocate` | 247 | 0 | 247 | UNMAPPED | 0.00% | 0.0% |
| `Advocate resumes` | 94 | 0 | 94 | UNMAPPED | 0.00% | 0.0% |
| `Agricultural` | 199 | 0 | 199 | UNMAPPED | 0.00% | 0.0% |
| `Agricultural resumes` | 68 | 0 | 68 | UNMAPPED | 0.00% | 0.0% |
| `Agriculture` | 79 | 0 | 79 | UNMAPPED | 0.00% | 0.0% |
| `Apparel` | 69 | 0 | 69 | UNMAPPED | 0.00% | 0.0% |
| `Apparel resumes` | 51 | 0 | 51 | UNMAPPED | 0.00% | 0.0% |
| `Architect` | 84 | 0 | 84 | UNMAPPED | 0.00% | 0.0% |
| `Architects resumes` | 60 | 0 | 60 | UNMAPPED | 0.00% | 0.0% |
| `Arts` | 255 | 0 | 255 | UNMAPPED | 0.00% | 0.0% |
| `Arts resumes` | 68 | 0 | 68 | UNMAPPED | 0.00% | 0.0% |
| `Automobile` | 73 | 0 | 73 | UNMAPPED | 0.00% | 0.0% |
| `Automobile resumes` | 40 | 0 | 40 | UNMAPPED | 0.00% | 0.0% |
| `Aviation` | 85 | 0 | 85 | UNMAPPED | 0.00% | 0.0% |
| `Aviation resumes` | 51 | 0 | 51 | UNMAPPED | 0.00% | 0.0% |

---

## 7. Latency Analysis

Evaluation inference latency was measured per record across datasets:

| Dataset | Sample Size | Mean Latency | Median Latency | P95 Latency | Max Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Accountant OCR (`ocr_results.csv`)** | 283 | **3.51 ms** | **3.44 ms** | **4.14 ms** | **6.37 ms** |
| **Synthetic PDF Set (`audit_pdfs`)** | 5 | **6.37 ms** | **3.46 ms** | **16.70 ms** | **16.70 ms** |
| **Overall Model Inference Speed** | — | **~3.5 ms / resume** | **~3.4 ms / resume** | **< 5.0 ms** | **16.7 ms** |

---

## 8. Confidence & Abstention Analysis

- **Abstention Mechanism Status**: `"No abstention mechanism was applied during this evaluation."`
- The model outputs probabilities summing to 1.0 across the 5 target classes. In the absence of an empirical confidence cutoff threshold (e.g. $<0.60 \rightarrow \text{UNMAPPED}$), out-of-domain resumes are forced into whichever of the 5 technical classes gets the highest relative score.

---

## 9. Data Independence Statement

1. `master_combined.csv` is **Unseen Same-Family Contaminated** and was excluded from external validation metrics.
2. `archive_1/Resumes PDF/` is an **Independent Out-of-Domain PDF Corpus** (image-only PDFs).
3. `ocr_results.csv` is an **Out-of-Domain Negative Test** (283 Accountant resumes).
4. `audit_pdfs/*.pdf` is an **Independent Synthetic Test Set ($N=5$)**.

No claims of "independent five-class external accuracy" have been manufactured, as no external 5-class labeled dataset exists in the repository outside of the Phase 21 splits.

---

## 10. Production Implications

1. **OCR Pipeline Requirement**: Scanned image PDFs (like `archive_1`) cannot be processed by digital PDF text extractors and require OCR preprocessing in production.
2. **Abstention / Confidence Gating**: Production inference should incorporate a confidence threshold (e.g. flag predictions with confidence $< 60\%$ as `Low Confidence / Unmapped`) to prevent forcing out-of-domain resumes into technical categories.

---

## 11. Final Phase 23C Verdict

- **A. In-Domain Performance**: Confirmed on untouched Phase 22 test set (`test.csv`, 278 records): **97.84% Accuracy**, **0.9810 Macro F1** (vs Baseline 88.85% Acc, 0.7205 Macro F1).
- **B. Independent External Generalization**: No independent 5-class labeled real-world external dataset is present in the repo. `master_combined.csv` is same-family contaminated.
- **C. Out-of-Domain Robustness**: Out-of-domain Accountant resumes are predicted as `Web Development` (95.8%) and `Data Science` (4.2%), with a 14.8% high-confidence ($\ge 0.80$) false-positive rate.
- **D. Synthetic Pipeline Correctness**: **100.0% Accuracy** (5 / 5 correct) on Phase 20 synthetic PDFs ($N=5$).
- **E. Production Promotion Readiness**: Model v2 exhibits massive in-domain gains (+36.2% relative Macro F1) and perfect synthetic pipeline pass rates, but requires confidence-gating to handle out-of-domain resumes gracefully.

---

> [!IMPORTANT]
> **PHASE 23C STOP DIRECTIVE SATISFIED**
> `model_v2.joblib` has NOT been promoted. `model_latest.joblib` remains untouched.
