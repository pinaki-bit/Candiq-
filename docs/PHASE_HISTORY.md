# COMPLETED PHASE CHRONOLOGY & AUDIT HISTORY — RESUME INTEL

**Project**: Resume Intel  
**Document Version**: 1.0 (Phase 27.5 Checkpoint)  
**Date**: September 28, 2026  

---

## EXECUTIVE SUMMARY OF PHASES (20 – 27)

| Phase | Title / Scope | Key Artifact | Model Integrity Status | Final Phase Status |
| :---: | :--- | :--- | :---: | :---: |
| **Phase 20** | Independent Reality Verification Audit | `PHASE_20_REALITY_AUDIT.md` | `model_latest` Unaltered | **VERIFIED** |
| **Phase 21** | Real ML Model Evaluation & Candidate v2 | `PHASE_21_FINAL_REPORT.md` | `model_v2.joblib` Created | **COMPLETED** |
| **Phase 22** | Model Integrity & Independent Validation | `PHASE_22_MODEL_INTEGRITY_REPORT.md` | `model_latest` Unaltered | **AUDITED** |
| **Phase 23A** | External Dataset Data Quality Audit | `PHASE_23_EXTERNAL_DATA_AUDIT.md` | Zero Data Mutation | **AUDITED** |
| **Phase 23B** | Overlap & Contamination Analysis | `PHASE_23_OVERLAP_REPORT.md` | Zero Data Mutation | **AUDITED** |
| **Phase 23C** | Independent External Generalization | `PHASE_23C_EXTERNAL_EVALUATION.md` | Zero Data Mutation | **EVALUATED** |
| **Phase 23D** | OCR-Enabled PDF Robustness Evaluation | `PHASE_23D_OCR_ROBUSTNESS_REPORT.md` | Zero Data Mutation | **EVALUATED** |
| **Phase 23E** | OOD Detection & Abstention Analysis | `PHASE_23E_OOD_ABSTENTION_ANALYSIS.md` | Zero Data Mutation | **ANALYZED** |
| **Phase 24** | OOD Threshold Validation | `PHASE_24_OOD_THRESHOLD_VALIDATION.md` | Operating Points Frozen | **VALIDATED** |
| **Phase 25** | Controlled Abstention Layer Implementation | `PHASE_25_ABSTENTION_IMPLEMENTATION.md` | Policy Engine Built | **IMPLEMENTED** |
| **Phase 26** | E2E Abstention Integration Verification | `PHASE_26_E2E_ABSTENTION_VERIFICATION.md` | 157/157 Tests Passed | **VERIFIED** |
| **Phase 27** | Real Resume Upload E2E Validation | `PHASE_27_REAL_UPLOAD_E2E_VALIDATION.md` | 162/162 Tests Passed | **VALIDATED** |

---

## DETAILED PHASE RECORDS

### Phase 20 — Independent Reality Verification Audit
- **Objective**: Conduct an independent, un-compromised reality verification of the system architecture, test suite, and claims.
- **Key Findings**: Verified that 132/132 unit and integration tests passed, SQLite database and FastAPI services were operational, but identified dataset scarcity in `Cloud Computing` ($N=14$) and synthetic contact-header template artifacts.
- **Artifact**: [`PHASE_20_REALITY_AUDIT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_20_REALITY_AUDIT.md).
- **Status**: **VERIFIED**.

---

### Phase 21 — Real ML Model Evaluation & Candidate Model v2
- **Objective**: Train and evaluate candidate model `model_v2.joblib` using calibrated probability estimates (Platt Scaling) and TF-IDF word n-grams without modifying production classifier `model_latest.joblib`.
- **Key Findings**: Candidate `model_v2` achieved 97.84% accuracy and 0.9810 macro F1 on the test set.
- **Artifact**: [`PHASE_21_FINAL_REPORT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_21_FINAL_REPORT.md).
- **Model Status**: `model_v2.joblib` created in `ml/artifacts/`; `model_latest.joblib` kept active.
- **Status**: **COMPLETED**.

---

### Phase 22 — Model Integrity Audit & Independent Validation
- **Objective**: Perform an un-biased audit comparing baseline `model_latest` against candidate `model_v2` on the untouched 278-record test split (`test.csv`).
- **Key Findings**: Baseline `model_latest` achieved 88.85% accuracy (0.7205 macro F1); Candidate `model_v2` achieved 97.84% accuracy (0.9810 macro F1). Audit confirmed no test-set contamination occurred during training.
- **Artifact**: [`PHASE_22_MODEL_INTEGRITY_REPORT.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_22_MODEL_INTEGRITY_REPORT.md).
- **Status**: **AUDITED**.

---

### Phase 23 (A–E) — External Generalization, Overlap, OCR, & OOD Analysis
- **Phase 23A (External Quality Audit)**: Audited `master_combined.csv` ($N=4,000$) and external OCR datasets (`ocr_results.csv`). Artifact: `PHASE_23_EXTERNAL_DATA_AUDIT.md`.
- **Phase 23B (Overlap Check)**: Evaluated token and exact-text overlap between training sets and external corpora. Discovered high same-family template overlap in `master_combined.csv`. Artifact: `PHASE_23_OVERLAP_REPORT.md`.
- **Phase 23C (External Generalization)**: Evaluated models on independent unseen datasets. Discovered closed-world classifier limitation on OOD non-technical resumes. Artifact: `PHASE_23C_EXTERNAL_EVALUATION.md`.
- **Phase 23D (OCR Robustness)**: Evaluated OCR text recovery on scanned PDF corpus (`archive_1/Resumes PDF`). Tesseract OCR recovered structured text across 34 pilot samples. Artifact: `PHASE_23D_OCR_ROBUSTNESS_REPORT.md`.
- **Phase 23E (OOD Abstention Analysis)**: Evaluated maximum confidence, margin, and entropy as separation signals between in-domain resumes and non-technical OOD resumes. Discovered clear separation. Artifact: `PHASE_23E_OOD_ABSTENTION_ANALYSIS.md`.

---

### Phase 24 — OOD Threshold Selection & Abstention Validation
- **Objective**: Establish a defensible OOD operating point using a two-stage validation protocol (`val.csv` for selection, untouched `test.csv` for frozen candidate evaluation).
- **Key Findings**: Candidate operating point OP-4 ($\tau = 0.85$) selected on validation data achieved **91.01% untouched test coverage** and **96.85% OOD dev rejection**.
- **Artifact**: [`PHASE_24_OOD_THRESHOLD_VALIDATION.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_24_OOD_THRESHOLD_VALIDATION.md).
- **Status**: **VALIDATED**.

---

### Phase 25 — Controlled OOD / Abstention Layer Implementation
- **Objective**: Implement a non-destructive OOD Policy Engine (`backend/app/services/ood_policy.py`) wrapping the classification pipeline without retraining or altering classifier predictions.
- **Key Findings**: Abstention logic sets `status: "review"`, `review_required: True`, `ood_status: "possible_out_of_domain"` when confidence $< 0.85$. Enforced semantic rule: Abstention means `"Needs Manual Review"`, **NEVER** `"Candidate Rejected"`.
- **Artifact**: [`PHASE_25_ABSTENTION_IMPLEMENTATION.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_25_ABSTENTION_IMPLEMENTATION.md).
- **Status**: **IMPLEMENTED**.

---

### Phase 26 — End-to-End OOD / Abstention Integration Verification
- **Objective**: Conduct comprehensive verification across service, API, database, and frontend layers (Test Cases A through J).
- **Key Findings**: 157/157 tests passed cleanly. Confirmed database persistence of OOD columns, API schema compatibility, neutral UI review wording, and 100% pre/post SHA-256 hash match.
- **Artifact**: [`PHASE_26_E2E_ABSTENTION_VERIFICATION.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_26_E2E_ABSTENTION_VERIFICATION.md).
- **Status**: **VERIFIED**.

---

### Phase 27 — Real Resume Upload End-to-End Validation
- **Objective**: Validate the real PDF resume upload flow using actual PDF test files (`technical_resume.pdf`, `accountant_ood_resume.pdf`, `scanned_image_resume.pdf`).
- **Key Findings**:
  - Technical PDF with `model_v2` achieved `classification_status="accepted"`, `review_required=False`.
  - Accountant OOD PDF achieved `classification_status="review"`, `review_required=True`, neutral UI text.
  - Image-only scanned PDF handled OCR fallback gracefully (`status="failed"` with clear error message, zero crashes).
  - Measured latencies: Cold upload = 5.046s, Warm processing = 354.86 ms per upload.
  - Test suite: **162 / 162 passed**. SHA-256 integrity: 100% match.
- **Artifact**: [`PHASE_27_REAL_UPLOAD_E2E_VALIDATION.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/PHASE_27_REAL_UPLOAD_E2E_VALIDATION.md).
- **Status**: **VALIDATED**.
