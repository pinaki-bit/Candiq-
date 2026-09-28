# PHASE 24 — OOD THRESHOLD SELECTION & ABSTENTION VALIDATION

**Project**: Resume Intel  
**Author**: Senior ML Validation & Reliability Engineer  
**Date**: September 27, 2026  
**Status**: Evaluation & Operating-Point Validation Complete — Production Implementation Deferred  

---

## 1. OBJECTIVE

Phase 23E established that maximum prediction confidence, probability margin, and prediction entropy exhibit clear empirical separation between in-domain technical resumes (`train.csv`, `val.csv`, `test.csv`) and non-technical out-of-domain (OOD) data (Accountant OCR resumes and independent scanned PDFs).

**Phase 24 Objective**: To establish a rigorous, disciplined two-stage validation methodology for selecting an out-of-domain (OOD) abstention operating point **without modifying production APIs, changing the model, or contaminating the untouched test set (`test.csv`)**.

This phase explicitly does **not** maximize OOD rejection at all costs nor select a "production threshold". Rather, it quantifies the trade-off between **In-Domain Coverage** ($\text{Coverage} = P(\text{Confidence} \ge \tau \mid \text{In-Domain})$) and **OOD Rejection** ($\text{Rejection} = P(\text{Confidence} < \tau \mid \text{OOD})$) across documented candidate operating points.

> [!IMPORTANT]
> **Zero Model Mutation Policy**: Phase 24 is strictly an offline operating-point design and validation effort. No model files (`model_v2.joblib`, `model_latest.joblib`), dataset files (`train.csv`, `val.csv`, `test.csv`), backend APIs, or frontend interfaces were modified or promoted.

---

## 2. DATA SEPARATION STRATEGY

To eliminate test-set threshold tuning and data contamination, Phase 24 enforces strict data separation across two distinct validation stages:

```
[ STAGE 1: CANDIDATE SELECTION ]
  In-Domain Dev:  ml/data/processed/val.csv (N=277)
  OOD Dev Data:   ml/data/raw/ocr_results.csv (N=283 Accountant OCR)
                 + reports/phase23d_ocr_results.json (N=34 Independent PDF OCR)
        │
        ▼
  Sweep Grid: Confidence 0.50 → 0.99 (step=0.01)
  Identify Candidate Operating Points (OP-1, OP-2, OP-3, OP-4)
        │
        ▼
  FREEZE Candidate Operating Points (Thresholds: 0.81, 0.82, 0.85, 0.91)

[ STAGE 2: UNTOUCHED FROZEN EVALUATION ]
  Untouched Test: ml/data/processed/test.csv (N=278)
        │
        ▼
  Evaluate Frozen Thresholds EXACTLY ONCE on test.csv
  Report Test Coverage, Test Rejection, & Class-Conditional Breakdown
```

1. **Stage 1 (Development & Threshold Selection)**:
   - Candidate operating points were identified exclusively using `val.csv` ($N=277$) and the combined OOD development population ($N=317$).
2. **Stage 2 (Frozen Evaluation)**:
   - Once selected, the operating points were **frozen**. They were then evaluated exactly once on `test.csv` ($N=278$). No threshold adjustments were made after viewing test results.

---

## 3. IN-DOMAIN VALIDATION POPULATION

The in-domain development population comprises the official validation dataset (`ml/data/processed/val.csv`, $N=277$).

- **Distribution Across Canonical Classes**:
  - `Web Development`: 105 records (37.9%)
  - `Data Science`: 62 records (22.4%)
  - `Cybersecurity`: 55 records (19.9%)
  - `DevOps`: 41 records (14.8%)
  - `Cloud Computing`: 14 records (5.1%)
- **Validation Signal Baseline**:
  - Mean Maximum Confidence: **0.9381** (Median: **0.9942**)
  - Mean Probability Margin: **0.9002** (Median: **0.9904**)
  - Mean Entropy: **0.1834** bits (Median: **0.0246** bits)

---

## 4. OOD DEVELOPMENT POPULATION

The out-of-domain development dataset ($N=317$) combines two separate external text sources:
1. **Accountant OCR Resumes** (`ml/data/raw/ocr_results.csv`): 283 text records extracted via Tesseract OCR from non-technical accounting resumes.
2. **Independent PDF OCR Resumes** (`reports/phase23d_ocr_results.json`): 34 text records extracted via OCR from `archive_1/Resumes` PDF files in Phase 23D.

> [!WARNING]
> **Dataset Limitation Warning**: The OOD development population represents non-technical accounting resumes and scanned independent resumes. It does **not** represent all possible out-of-domain resume types (e.g., medical, legal, artistic, or corrupt text). OOD rejection rates reported here are empirical measurements against this specific sample, not guaranteed theoretical detection bounds for arbitrary external documents.

---

## 5. SIGNAL DEFINITIONS

Three scalar prediction signals produced by `model_v2` (TF-IDF + Calibrated LinearSVC classifier) were evaluated:

1. **Maximum Probability ($S_{\text{conf}}$)**:
   $$S_{\text{conf}} = \max_{k \in \{1 \dots C\}} P(Y = k \mid X)$$
2. **Probability Margin ($S_{\text{margin}}$)**:
   $$S_{\text{margin}} = P(Y = k_{(1)} \mid X) - P(Y = k_{(2)} \mid X)$$
   where $k_{(1)}$ and $k_{(2)}$ are the top-1 and top-2 ranked classes.
3. **Normalized Prediction Entropy ($S_{\text{entropy}}$)**:
   $$S_{\text{entropy}} = -\sum_{k=1}^C P(Y = k \mid X) \log_2 P(Y = k \mid X)$$

> [!NOTE]
> **Combined Signal Policy**: Adhering strictly to Phase 24 guidelines, no arbitrary weighted combination of signals (e.g., $0.5 S_{\text{conf}} + 0.5 S_{\text{margin}}$) was implemented because learning combination weights would require training a secondary meta-classifier, violating the zero-retraining directive. Maximum probability $S_{\text{conf}}$ was selected as the primary operating metric as it correlates monotonically with both margin and entropy in a 5-class calibrated softmax output.

---

## 6. THRESHOLD SWEEP

A fine-grid numerical sweep of maximum probability thresholds ($\tau \in [0.50, 0.99]$, step = $0.01$) was conducted on `val.csv` ($N=277$) and OOD Dev ($N=317$).

| Threshold ($\tau$) | Val In-Domain Coverage (%) | Val In-Domain Rejection (%) | OOD Dev Rejection (%) | OOD Dev Acceptance (%) |
| :---: | :---: | :---: | :---: | :---: |
| **0.50** | 98.92% | 1.08% | 22.40% | 77.60% |
| **0.60** | 98.19% | 1.81% | 51.10% | 48.90% |
| **0.70** | 97.47% | 2.53% | 74.45% | 25.55% |
| **0.80** | 95.67% | 4.33% | 85.17% | 14.83% |
| **0.81** | 95.31% | 4.69% | 88.01% | 11.99% |
| **0.82** | 95.31% | 4.69% | 90.22% | 9.78% |
| **0.85** | 93.86% | 6.14% | 96.85% | 3.15% |
| **0.88** | 92.42% | 7.58% | 99.05% | 0.95% |
| **0.90** | 90.97% | 9.03% | 99.68% | 0.32% |
| **0.91** | 90.25% | 9.75% | 100.00% | 0.00% |
| **0.95** | 78.34% | 21.66% | 100.00% | 0.00% |

*Full sweep results are stored in [`reports/phase24_threshold_validation.csv`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase24_threshold_validation.csv).*

---

## 7. CONSTRAINT ANALYSIS

Four candidate operating points were formulated on `val.csv` based on distinct operational constraints:

1. **High In-Domain Coverage ($\ge 95\%$)**: Maximize in-domain retention while accepting lower OOD rejection.
2. **Balanced Coverage ($\ge 90\%$)**: Maintain $\ge 90\%$ in-domain coverage while pushing OOD rejection above 95%.
3. **High OOD Rejection ($\ge 85\%$)**: Achieve at least 85% OOD rejection.
4. **Strict OOD Rejection ($\ge 95\%$)**: Achieve at least 95% OOD rejection.

---

## 8. CANDIDATE OPERATING POINTS

From Stage 1 validation data, the following 4 candidate operating points were identified and frozen:

| Operating Point | Operational Goal | Threshold ($\tau$) | Val In-Domain Coverage | Val False Rejection | OOD Dev Rejection | OOD Dev Acceptance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **OP-1** | High Coverage ($\ge 95\%$) | **0.82** | 95.31% | 4.69% | 90.22% | 9.78% |
| **OP-2** | Balanced Coverage ($\ge 90\%$) | **0.91** | 90.25% | 9.75% | 100.00% | 0.00% |
| **OP-3** | High OOD Rejection ($\ge 85\%$) | **0.81** | 95.31% | 4.69% | 88.01% | 11.99% |
| **OP-4** | Strict OOD Rejection ($\ge 95\%$) | **0.85** | 93.86% | 6.14% | 96.85% | 3.15% |

*Operating points JSON artifact stored in [`reports/phase24_operating_points.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase24_operating_points.json).*

---

## 9. FROZEN TEST EVALUATION

In Stage 2, the four frozen candidate operating points were evaluated on the untouched final test set (`ml/data/processed/test.csv`, $N=278$).

| Candidate Operating Point | Selected Threshold ($\tau$) | Validation Coverage | Untouched Test Coverage | Test False Rejection Rate | Coverage Delta ($\Delta$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **OP-1 (High Coverage)** | **0.82** | 95.31% | **92.81%** | 7.19% | -2.50% |
| **OP-2 (Balanced)** | **0.91** | 90.25% | **85.61%** | 14.39% | -4.64% |
| **OP-3 (High OOD Rej)** | **0.81** | 95.31% | **93.53%** | 6.47% | -1.78% |
| **OP-4 (Strict OOD Rej)** | **0.85** | 93.86% | **91.01%** | 8.99% | -2.86% |

> [!IMPORTANT]
> **OOD Test Set Transparency**: As specified in Phase 24 requirements, the OOD development dataset (Accountant OCR $N=283$ + Independent OCR $N=34$) was utilized during Stage 1 threshold candidate selection. Therefore, OOD rejection metrics on this set are **development evaluation measurements**, not independent final OOD validation.

*Frozen test evaluation stored in [`reports/phase24_test_frozen_evaluation.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase24_test_frozen_evaluation.json).*

---

## 10. CLASS-CONDITIONAL COVERAGE

Global thresholds do not impact all canonical resume categories equally. In-domain coverage was evaluated separately across each class on `test.csv` ($N=278$):

### Class Coverage Breakdown at Candidate Thresholds

| Canonical Class | Sample Count ($N$) | OP-1 ($\tau=0.82$) Coverage | OP-3 ($\tau=0.81$) Coverage | OP-4 ($\tau=0.85$) Coverage | OP-2 ($\tau=0.91$) Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cloud Computing** | 14 | 100.00% | 100.00% | 100.00% | 100.00% |
| **DevOps** | 41 | 95.12% | 95.12% | 95.12% | 92.68% |
| **Cybersecurity** | 56 | 96.43% | 96.43% | 91.07% | 87.50% |
| **Web Development** | 105 | 90.48% | 90.48% | 90.48% | 84.76% |
| **Data Science** | 62 | 90.32% | 93.55% | 87.10% | 77.42% |

### Key Class-Conditional Observations:
1. **Data Science Sensitivity**: `Data Science` exhibits the steepest drop in coverage when moving from $\tau=0.81$ (93.55%) to $\tau=0.91$ (77.42%). At $\tau=0.91$, nearly **22.6% of valid Data Science resumes** would be rejected as low confidence/OOD.
2. **Web Development Volume**: `Web Development` has the largest sample count ($N=105$), maintaining 90.48% coverage up to $\tau=0.85$, but dropping to 84.76% at $\tau=0.91$.
3. **Cloud Computing Stability**: `Cloud Computing` ($N=14$) maintains 100% coverage across all candidate thresholds, though its small sample size warrants cautious interpretation.

*Class-conditional dataset stored in [`reports/phase24_class_conditional_coverage.csv`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase24_class_conditional_coverage.csv).*

---

## 11. CONFIDENCE CALIBRATION CONSISTENCY

In Phase 22, probability calibration via CalibratedClassifierCV (Platt Scaling / Isotonic regression on `model_v2`) was analyzed.
- **Consistency Verification**:
  - The maximum confidence scores on `val.csv` (mean 0.9381) and `test.csv` (mean 0.9295) align closely with Phase 22 calibration curve observations.
  - In-domain resumes reliably cluster above probability $\tau = 0.80$ (95.31% of validation records, 93.53% of test records).
  - Non-technical OOD resumes cluster below $\tau = 0.80$ (88.01% of Accountant/Independent OCR resumes fall below 0.81).

---

## 12. LIMITATIONS

1. **OOD Sample Narrowness**: OOD development data is confined to Accountant resumes and 34 scanned PDF OCR samples. It does not reflect all real-world edge cases (e.g., medical resumes, non-English resumes, multi-page graphic designs, or corrupted raw text).
2. **Test Coverage Generalization Drift**: A small coverage drop ($-1.78\%$ to $-4.64\%$) was observed between validation and untouched test sets, demonstrating that test-set performance slightly trails validation estimates.
3. **Fixed Linear Classifier Baseline**: `model_v2` relies on TF-IDF word n-grams. Text containing heavy technical jargon from unknown domains (e.g., advanced physics or bio-engineering) may receive low confidence despite being legitimate academic documents.

---

## 13. DATA LEAKAGE & CONTAMINATION CHECK

To guarantee complete compliance with Phase 24 requirements, a pre- and post-execution SHA-256 hash comparison was conducted across all core model and dataset files.

| Artifact Path | Pre-Phase 24 SHA-256 Hash | Post-Phase 24 SHA-256 Hash | Status |
| :--- | :--- | :--- | :---: |
| `ml/artifacts/model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **MATCH** |
| `ml/artifacts/model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **MATCH** |
| `ml/data/processed/train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **MATCH** |
| `ml/data/processed/val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **MATCH** |
| `ml/data/processed/test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **MATCH** |

**Zero Contamination Confirmed**: All model and dataset files remain 100% unaltered.

---

## 14. FINDINGS

1. **Defensible Candidate Operating Points Established**:
   - **OP-3 ($\tau = 0.81$)**: Achieves **93.53% untouched test coverage** with **88.01% OOD dev rejection**.
   - **OP-4 ($\tau = 0.85$)**: Achieves **91.01% untouched test coverage** with **96.85% OOD dev rejection**.
   - **OP-2 ($\tau = 0.91$)**: Achieves **100.0% OOD dev rejection**, but severely penalizes `Data Science` resumes (reducing test coverage to 77.42%).
2. **Methodological Validity**: Selecting candidate operating points on `val.csv` prior to frozen evaluation on `test.csv` prevented test-set contamination and provided realistic coverage expectations.
3. **No Winner Declared**: The selection of a final production operating point depends on business priorities (e.g., whether false rejection of valid resumes or accidental acceptance of non-technical resumes is more costly to recruiters).

---

## 15. REQUIREMENTS FOR PRODUCTION ABSTENTION

Before any abstention mechanism can be implemented in production APIs or frontend UIs (in a future phase):

1. **Product Owner Sign-off**: Product management must explicitly select an operating point (e.g., OP-3 vs OP-4) based on acceptable in-domain rejection tolerance.
2. **Class-Conditional Mitigation**: If a strict threshold like $\tau = 0.91$ is preferred, class-conditional thresholds ($\tau_k$) or re-calibration per class should be evaluated to avoid disproportionately rejecting `Data Science` resumes.
3. **Structured API Response Schema**: Production endpoints must return structured abstention flags (e.g., `is_ood: boolean`, `confidence_score: float`, `abstention_reason: string`) without throwing 500 errors.
4. **User Experience Design**: Frontend UI must gracefully handle low-confidence/OOD responses with informative warning badges rather than raw failure state.

---

## 16. FINAL VERDICT & STOP CONDITION

- **Validation Objective Met**: A defensible, two-stage threshold validation framework was executed without test-set tuning or model mutation.
- **Production Status**: Model promotion and API abstention implementation remain strictly **deferred**.
- **SHA-256 Verification**: 100% passed (zero bytes modified).

**STOP CONDITION ACKNOWLEDGED**: Phase 24 is complete. All required artifacts have been generated. No production code or frontend files were modified. Awaiting explicit user approval before proceeding to Phase 25.
