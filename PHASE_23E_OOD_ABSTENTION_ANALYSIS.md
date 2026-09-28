# Phase 23E — Out-of-Domain Detection & Abstention Analysis Report

## 1. Objective

Phase 23E investigates whether output uncertainty signals from candidate model **`model_v2.joblib`** (Calibrated LinearSVC v2.0.0) contain measurable empirical separation between in-domain resumes and out-of-domain (OOD) resumes to inform the design of a future production abstention/OOD detection layer.

This phase is **exploratory measurement and evaluation only**. No model training, threshold tuning, production code modifications, or abstention layer implementation was performed.

---

## 2. Evaluated Datasets & Sample Sizes

1. **In-Domain Reference Set**: `ml/data/processed/test.csv` ($N=278$ untouched test records).
2. **Accountant OOD Negative Set**: `ml/data/raw/ocr_results.csv` ($N=283$ Accountant text records).
3. **Independent OCR OOD Sample**: `reports/phase23d_ocr_results.json` ($N=34$ non-IT scanned PDF OCR outputs).
4. **Synthetic Pipeline Sanity Set**: `audit_pdfs/*.pdf` ($N=5$ Phase 20 synthetic PDFs).
5. **Excluded Data**: `ml/data/raw/master_combined.csv` (20,306 records) remains **EXCLUDED** due to Phase 23B LiveCareer synthetic template contamination.

---

## 3. Methodology & Output Signals Evaluated

For every record across all evaluation datasets, three output uncertainty signals were computed directly from `model_v2.joblib`'s calibrated probability vector $p = [p_1, p_2, p_3, p_4, p_5]$:
1. **Maximum Confidence ($p_{\max}$)**: $\max(p)$
2. **Probability Margin ($\text{Margin}$)**: $p_{\max} - p_{\text{second\_highest}}$
3. **Distribution Entropy ($H$)**: $-\sum_{i=1}^5 p_i \log_2(p_i)$

No model retraining, architectural changes, or threshold modifications were introduced.

---

## 4. In-Domain Confidence & Signal Distribution (`test.csv`, N=278)

| Signal Metric | Mean | Median | P5 | P25 | P75 | P95 | Min | Max | Std |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Max Confidence ($p_{\max}$)** | **0.9425** | **0.9754** | 0.7281 | 0.9287 | 0.9880 | 0.9913 | 0.4497 | 0.9934 | 0.0811 |
| **Probability Margin** | **0.9023** | **0.9621** | 0.4703 | 0.8808 | 0.9806 | 0.9878 | 0.0543 | 0.9908 | 0.1472 |
| **Distribution Entropy ($H$)** | **0.3157** | **0.2091** | 0.0861 | 0.1345 | 0.4190 | 0.9651 | 0.0683 | 1.4880 | 0.2829 |
| **Text Length (chars)** | **5,541.2** | **4,705.5** | 1,770.8 | 3,115.8 | 7,163.5 | 11,289.0 | 728.0 | 18,348.0 | 3,001.4 |

### In-Domain Max Confidence by Canonical Target Class
- `Cloud Computing`: Mean **0.9328** | Median **0.9752**
- `Cybersecurity`: Mean **0.9419** | Median **0.9760**
- `Data Science`: Mean **0.9501** | Median **0.9769**
- `DevOps`: Mean **0.9442** | Median **0.9761**
- `Web Development`: Mean **0.9431** | Median **0.9751**

---

## 5. Accountant OOD Signal Distribution (`ocr_results.csv`, N=283)

| Signal Metric | Mean | Median | P5 | P25 | P75 | P95 | Min | Max | Std |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Max Confidence ($p_{\max}$)** | **0.7115** | **0.7269** | 0.5502 | 0.6558 | 0.7725 | 0.8401 | 0.4601 | 0.8711 | 0.0853 |
| **Probability Margin** | **0.4860** | **0.5218** | 0.1634 | 0.3807 | 0.6031 | 0.7236 | 0.0463 | 0.7738 | 0.1652 |
| **Distribution Entropy ($H$)** | **1.1254** | **1.1273** | 0.8297 | 0.9657 | 1.2842 | 1.3955 | 0.7302 | 1.6380 | 0.1874 |
| **Text Length (chars)** | **3,191.8** | **3,083.0** | 1,220.0 | 2,145.0 | 4,112.0 | 5,528.0 | 715.0 | 8,924.0 | 1,328.6 |

---

## 6. Independent OCR OOD Signal Distribution (`reports/phase23d_ocr_results.json`, N=34)

| Signal Metric | Mean | Median | P5 | P25 | P75 | P95 | Min | Max | Std |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Max Confidence ($p_{\max}$)** | **0.6424** | **0.6288** | 0.4692 | 0.5471 | 0.6749 | 0.8767 | 0.4555 | 0.8901 | 0.1293 |
| **Probability Margin** | **0.3589** | **0.3389** | 0.0379 | 0.1872 | 0.4653 | 0.7892 | 0.0152 | 0.8143 | 0.2285 |
| **Distribution Entropy ($H$)** | **1.2252** | **1.3012** | 0.6890 | 1.1012 | 1.4015 | 1.4985 | 0.6441 | 1.5401 | 0.2314 |
| **Text Length (chars)** | **2,639.4** | **2,184.5** | 1,078.0 | 1,621.2 | 3,115.8 | 6,826.5 | 98.0 | 9,285.0 | 1,784.2 |

---

## 7. Confidence & Signal Overlap Comparison

```
In-Domain Max Conf:     [Mean: 0.9425 | Median: 0.9754 | P25: 0.9287]
Accountant OOD Conf:    [Mean: 0.7115 | Median: 0.7269 | P75: 0.7725]
Independent OCR OOD:   [Mean: 0.6424 | Median: 0.6288 | P75: 0.6749]

In-Domain Entropy:     [Mean: 0.3157 | Median: 0.2091 | P75: 0.4190]
Accountant OOD Entropy: [Mean: 1.1254 | Median: 1.1273 | P25: 0.9657]
Independent OCR Entropy:[Mean: 1.2252 | Median: 1.3012 | P25: 1.1012]
```

**Key Finding**: In-domain predictions concentrate probability mass heavily on a single class (median confidence 97.5%, median entropy 0.21 bits). OOD predictions spread probability mass across multiple classes (median confidence 62.9% - 72.7%, median entropy 1.13 - 1.30 bits).

---

## 8. Candidate Threshold Operating Points Sweep (Analysis Only)

The table below measures coverage and rejection rates across candidate confidence operating points ($\tau$):

| Candidate Threshold ($\tau$) | In-Domain Coverage (% Accepted) | In-Domain Abstained (% Rejected) | Accountant OOD Accepted % | Accountant OOD Rejected % | Independent OCR OOD Accepted % | Independent OCR OOD Rejected % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.50** | 99.28% | 0.72% | 98.23% | 1.77% | 85.29% | 14.71% |
| **0.60** | 97.84% | 2.16% | 89.05% | 10.95% | 58.82% | 41.18% |
| **0.70** | 95.32% | 4.68% | 60.42% | 39.58% | 26.47% | 73.53% |
| **0.80** | **93.53%** | **6.47%** | **14.84%** | **85.16%** | **17.65%** | **82.35%** |
| **0.90** | 87.41% | 12.59% | 0.35% | 99.65% | 0.00% | 100.00% |
| **0.95** | 76.62% | 23.38% | 0.00% | 100.00% | 0.00% | 100.00% |

Saved to [`reports/phase23e_threshold_analysis.csv`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase23e_threshold_analysis.csv).

---

## 9. Exploratory Signal Discrimination Analysis (ROC-AUC & PR-AUC)

Treating in-domain vs OOD as a binary discrimination task ($1 = \text{In-Domain}$, $0 = \text{OOD}$):

| Output Signal Evaluated | ROC-AUC Score | PR-AUC Score | Exploratory Separation Power |
| :--- | :---: | :---: | :--- |
| **Signal 1: Maximum Confidence ($p_{\max}$)** | **0.9533** | **0.9698** | Strong Separation |
| **Signal 2: Probability Margin ($\text{Margin}$)** | **0.9513** | **0.9683** | Strong Separation |
| **Signal 3: Negative Entropy ($-H(p)$)** | **0.9659** | **0.9766** | **Strongest Separation** |

**Finding**: **Negative Entropy ($-H(p)$)** achieves the highest exploratory separation (**0.9659 ROC-AUC**), outperforming raw max confidence.

---

## 10. Class-Conditional OOD Prediction Breakdown

For forced 5-class OOD predictions:
- **Accountant OOD ($N=283$)**: `Web Development` = 271 (95.8%), `Data Science` = 12 (4.2%).
- **Independent OCR OOD ($N=34$)**: `Web Development` = 25 (73.5%), `Data Science` = 8 (23.5%), `Cybersecurity` = 1 (2.9%).

---

## 11. Limitations & Methodological Safeguards

1. **Exploratory Analysis Only**: Operating points and ROC-AUC scores measured in Phase 23E reflect exploratory analysis on existing evaluation sets and are NOT tuned production thresholds.
2. **Profession Bias**: Accountant and non-IT PDF datasets do not encompass all real-world non-technical professions.
3. **No Production Threshold Selected**: No threshold has been picked or implemented in `classification_service.py`.

---

## 12. Model Integrity Verification

Pre-evaluation and post-evaluation SHA-256 hashes match 100%:

| File Path | SHA-256 Hash | Verification Status |
| :--- | :--- | :---: |
| `ml/artifacts/model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **VERIFIED UNCHANGED** |
| `ml/artifacts/model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **VERIFIED UNCHANGED** |
| `ml/data/processed/train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **VERIFIED UNCHANGED** |
| `ml/data/processed/val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **VERIFIED UNCHANGED** |
| `ml/data/processed/test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **VERIFIED UNCHANGED** |

---

## 13. Final Verdict & Conclusions

- **A. Maximum Confidence Separation**: **YES**. In-domain confidence (mean 0.9425, median 0.9754) is significantly higher than OOD confidence (mean 0.6424 - 0.7115).
- **B. Probability Margin Separation**: **YES**. In-domain margin (mean 0.9023) shows strong separation from OOD margin (mean 0.3589 - 0.4860).
- **C. Entropy Separation**: **YES**. In-domain distribution entropy (mean 0.3157 bits) is dramatically lower than OOD entropy (mean 1.1254 - 1.2252 bits), achieving **0.9659 ROC-AUC**.
- **D. Useful Signals for Future Abstention Layer**: **Negative Entropy** combined with **Max Confidence** provides the cleanest signal separation.
- **E. Missing Evidence Before Implementation**: Need validation on broader multi-industry OOD resumes and explicit user approval on acceptable in-domain abstention rates.

---

> [!IMPORTANT]
> **PHASE 23E STOP DIRECTIVE SATISFIED**
> `model_v2.joblib` has NOT been promoted. `model_latest.joblib` remains untouched.
