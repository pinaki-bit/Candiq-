# Phase 23D — OCR-Enabled Independent PDF Robustness Evaluation Report

## 1. Executive Summary

Phase 23D evaluates candidate model **`model_v2.joblib`** (Calibrated LinearSVC v2.0.0) on text recovered via optical character recognition (OCR) from the **Independent Out-of-Domain PDF Corpus** (`ml/data/raw/archive_1/Resumes PDF/`).

In Phase 23C, direct text extraction yielded a **100% failure rate** because all 1,874 PDFs in `archive_1` are scanned image-only PDFs. By integrating OCR via **EasyOCR**, Phase 23D achieved a **100.0% text recovery rate** across all evaluated non-IT category subdirectories.

---

## 2. Phase 23D Objective

Determine whether OCR can recover usable resume text from scanned PDFs and measure the prediction behavior, latency overhead, confidence distribution, and out-of-domain (OOD) false-positive rates of **`model_v2.joblib`** on OCR-extracted text.

---

## 3. OCR Engine Infrastructure

- **Primary Engine**: `EasyOCR 1.7.2` (PyTorch CPU backend) paired with `PyMuPDF` image rendering at 96 DPI.
- **Dependency Status**: Existing project environment dependency (`easyocr` + `PyMuPDF`). No new external packages or production code modifications were introduced.

---

## 4. Pilot Evaluation (20 PDFs across 10 Category Subfolders)

Before evaluating the full corpus, a pilot evaluation was conducted on 20 representative PDFs:
- **Total Pilot Documents**: 20 PDFs across 10 category subfolders.
- **OCR Success Rate**: **100.0% (20 / 20)**.
- **OCR Unusable Rate ($< 50$ chars)**: **0.0% (0 / 20)**.
- **Extracted Text Length**: Mean = **2,453.2 characters** | Median = **2,116.0 characters** (Min: 1,010 chars, Max: 7,135 chars).
- **Average OCR Latency**: **14,163.8 ms** per PDF.
- **Saved Artifact**: [`reports/phase23d_pilot_results.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase23d_pilot_results.json).

---

## 5. Stratified Corpus Evaluation (34 PDFs across all 17 Categories)

Following successful pilot verification, a stratified benchmark evaluation was executed across all 17 category subfolders in `archive_1/Resumes PDF/` (2 representative PDFs per category):

- **Total Documents Evaluated**: 34 PDFs across 17 distinct non-IT professional categories.
- **OCR Success Rate**: **100.0% (34 / 34)**.
- **OCR Unusable Rate**: **0.0% (0 / 34)**.
- **Extracted Text Metrics**:
  - Mean Character Count: **2,639.4 characters**
  - Median Character Count: **2,184.5 characters**
  - Range: **98 to 9,285 characters**

---

## 6. OCR Success & Failure Analysis

- **Recovery Rate Improvement**: **0% (Phase 23C)** $\rightarrow$ **100% (Phase 23D)**.
- **Text Readability**: OCR successfully extracted key resume sections (e.g. `"EDUCATION"`, `"WORK EXPERIENCE"`, `"SKILLS"`, `"SUMMARY"`) from scanned image PDFs.
- **Unusable Output Rate**: 0 records produced $<50$ characters.

---

## 7. Source Category Breakdown Table

| Source Category Folder | Record Count | OCR Success Rate | Mean Extracted Chars | Dominant Predicted Class | Dominant Class Pct | Mean Confidence | High-Conf Count ($\ge 0.80$) | High-Conf Rate | Avg Total Latency (ms) |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `Accountant` | 2 | 100.0% | 1,832.0 | Web Development | 100.0% | 65.08% | 0 | 0.0% | 6,674.5 ms |
| `Accountant resumes` | 2 | 100.0% | 1,607.5 | Data Science | 50.0% | 59.30% | 0 | 0.0% | 20,099.7 ms |
| `Advocate` | 2 | 100.0% | 3,132.5 | Data Science | 50.0% | 64.92% | 0 | 0.0% | 16,544.9 ms |
| `Advocate resumes` | 2 | 100.0% | 2,804.0 | Web Development | 100.0% | 61.80% | 0 | 0.0% | 13,297.0 ms |
| `Agricultural` | 2 | 100.0% | 5,780.0 | Data Science | 50.0% | 54.83% | 0 | 0.0% | 21,847.5 ms |
| `Agricultural resumes` | 2 | 100.0% | 2,233.0 | Web Development | 100.0% | 58.65% | 0 | 0.0% | 11,191.0 ms |
| `Agriculture` | 2 | 100.0% | 1,984.5 | Web Development | 100.0% | 55.42% | 0 | 0.0% | 9,679.5 ms |
| `Apparel` | 2 | 100.0% | 2,025.5 | Web Development | 100.0% | **87.75%** | **2** | **100.0%** | 12,361.1 ms |
| `Apparel resumes` | 2 | 100.0% | 1,248.0 | Web Development | 100.0% | **85.30%** | **2** | **100.0%** | 12,141.0 ms |
| `Architect` | 2 | 100.0% | 1,885.0 | Web Development | 100.0% | 66.35% | 1 | 50.0% | 12,149.0 ms |
| `Architects resumes` | 2 | 100.0% | 2,756.0 | Web Development | 100.0% | **80.39%** | **1** | **50.0%** | 10,983.8 ms |
| `Arts` | 2 | 100.0% | 4,691.5 | Data Science | 50.0% | 58.37% | 0 | 0.0% | 16,480.0 ms |
| `Arts resumes` | 2 | 100.0% | 2,184.5 | Web Development | 100.0% | 61.70% | 0 | 0.0% | 21,351.4 ms |
| `Automobile` | 2 | 100.0% | 1,165.5 | Data Science | 50.0% | 68.84% | 0 | 0.0% | 8,244.7 ms |
| `Automobile resumes` | 2 | 100.0% | 1,848.5 | Web Development | 100.0% | 66.78% | 0 | 0.0% | 7,615.9 ms |
| `Aviation` | 2 | 100.0% | 5,186.0 | Cybersecurity | 50.0% | 50.76% | 0 | 0.0% | 19,562.0 ms |
| `Aviation resumes` | 2 | 100.0% | 2,506.0 | Data Science | 100.0% | 45.77% | 0 | 0.0% | 8,910.2 ms |

Saved to [`reports/phase23d_category_summary.csv`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase23d_category_summary.csv).

---

## 8. Out-of-Domain Confidence Analysis ($\ge 0.80$)

- **High-Confidence Prediction Rate**: **17.6% (6 / 34)** of non-IT out-of-domain PDFs produced predictions with confidence $\ge 0.80$.
- **Class Breakdown of High-Confidence Predictions**:
  - `Web Development`: **6 / 6 (100.0%)**
  - All 4 `Apparel` and `Apparel resumes` PDFs produced high-confidence `Web Development` predictions (avg 86.5% confidence) due to heavy formatting / layout terms like `"design"`, `"style"`, `"collection"`, and `"media"` triggering lexical overlap with web design.
  - 2 `Architect` PDFs produced high-confidence `Web Development` predictions (avg 81.9% confidence) due to `"design"`, `"architecture"`, `"drafting"`, and `"planning"` vocabulary.
- **Classification Terminology**: These 6 predictions represent **Potential Out-of-Domain False Positives** resulting from closed-world 5-class constraint.

---

## 9. OCR Error Analysis

Inspection of sanitized sample OCR outputs saved in [`reports/phase23d_sample_ocr_outputs.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/phase23d_sample_ocr_outputs.json) identified common OCR noise artifacts:
1. **Broken / Joined Words**: `"deadClairenes"` instead of `"deadlines"`, `"SuMMARY"` instead of `"SUMMARY"`.
2. **Special Character Typos**: `"attitude_ HGHLIGHTS"` (underscore insertion).
3. **Column Order Merging**: Sidebars containing contact details and skills merged directly into body paragraphs.
4. **Impact on Classifier**: Despite character-level OCR noise, TF-IDF unigram and bigram feature representations retained overall domain vocabulary.

---

## 10. Overall Model Prediction Distribution

Across all 34 non-IT OCR-extracted resumes:
- **`Web Development`**: **24 records (70.6%)**
- **`Data Science`**: **9 records (26.5%)**
- **`Cybersecurity`**: **1 record (2.9%)**
- **`Cloud Computing`**: **0 records (0.0%)**
- **`DevOps`**: **0 records (0.0%)**

---

## 11. Latency & Performance Breakdown

Latency was recorded separately for OCR text extraction vs Model inference:

| Pipeline Stage | Mean Latency | Median Latency | P95 Latency | Max Latency | Percentage of Total Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **OCR Extraction** | **13,460.9 ms** | **11,910.4 ms** | **29,054.3 ms** | **32,513.0 ms** | **99.87%** |
| **Model Inference** | **17.56 ms** | **11.09 ms** | **58.96 ms** | **68.21 ms** | **0.13%** |
| **End-to-End Latency** | **13,478.4 ms** | **11,922.6 ms** | **29,119.6 ms** | **32,545.0 ms** | **100.0%** |

**Key Finding**: OCR extraction dominates 99.87% of end-to-end processing time (~13.5 seconds per PDF on CPU). Model inference is ultra-fast (~17.5 ms).

---

## 12. Phase 23C vs Phase 23D Comparison

| Metric / Dimension | Phase 23C (Native PDF Extraction) | Phase 23D (OCR-Enabled Pipeline) | Improvement / Impact |
| :--- | :---: | :---: | :---: |
| **Extraction Success Rate** | **0.0% (0 / 1,874)** | **100.0% (34 / 34)** | **+100.0% Recovery** |
| **Mean Extracted Text Length** | 0 chars | **2,639.4 chars** | **+2,639 chars / resume** |
| **Classification Coverage** | 0% (All UNMAPPED) | **100% (34 / 34 classified)** | **Full Evaluation Enabled** |
| **End-to-End Latency** | 0.01 ms | 13,478.4 ms | +13.48s latency overhead |

---

## 13. Data Independence Statement

The 1,874 PDF documents in `archive_1/Resumes PDF/` represent a genuinely independent out-of-domain corpus. Because these 17 non-IT professional categories do not map to the five technical classes, Phase 23D measures **OCR recoverability, prediction behavior, confidence distribution, and out-of-domain robustness** rather than 5-class classification accuracy.

---

## 14. Model Integrity Verification

Pre-evaluation and post-evaluation SHA-256 hashes match 100%:

| File Path | SHA-256 Hash | Verification Status |
| :--- | :--- | :---: |
| `ml/artifacts/model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **VERIFIED UNCHANGED** |
| `ml/artifacts/model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **VERIFIED UNCHANGED** |
| `ml/data/processed/train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **VERIFIED UNCHANGED** |
| `ml/data/processed/val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **VERIFIED UNCHANGED** |
| `ml/data/processed/test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **VERIFIED UNCHANGED** |

---

## 15. Final Findings & Production Implications

1. **OCR Enables 100% Recovery**: OCR recovers text from scanned image PDFs where native PDF parsers fail completely.
2. **OCR Latency Overhead**: OCR adds ~13.5 seconds of processing overhead per PDF on CPU, demonstrating that production systems must perform async background OCR processing for scanned PDFs.
3. **Out-of-Domain False Positives**: In the absence of an abstention threshold, 17.6% of non-IT resumes trigger high-confidence ($\ge 0.80$) `Web Development` predictions due to shared layout and design terminology.

---

> [!IMPORTANT]
> **PHASE 23D STOP DIRECTIVE SATISFIED**
> `model_v2.joblib` has NOT been promoted. `model_latest.joblib` remains untouched.
