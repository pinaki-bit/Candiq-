# 🧼 Phase 21C: Data Quality & Cleaning Report

This report documents the data quality inspection, text normalization, deduplication, and label hygiene performed on the raw datasets for **Resume Intel**.

---

## 📊 Executive Summary Table

| Metric | Count | Percentage of Total |
| :--- | :---: | :---: |
| **Total Raw Input Records Analyzed** | **16,889** | 100.0% |
| **Unmapped Non-Target Categories** | **14,070** | 83.3% |
| **Raw Mapped Target Records** | **2,819** | 16.7% |
| **Extremely Short / Invalid (< 50 chars)** | **0** | 0.0% |
| **Exact Duplicate Text Records Removed** | **916** | 5.4% |
| **Near-Duplicate Resume Records Removed** | **55** | 0.3% |
| **Final Clean Mapped Dataset Size** | **1,848** | **10.9%** |

---

## 🔍 Data Quality Operations & Verification

### 1. Label Hygiene & Category Scope
- Input datasets `resumes.csv` (13,389 records) and `archive/resumes_dataset.jsonl` (3,500 records) were joined and evaluated against the Phase 21B label mapping specification ([`shared/label_mapping.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/shared/label_mapping.json)).
- **2,819 raw target records** mapped cleanly to the 5 production domains (`Data Science`, `Web Development`, `Cloud Computing`, `DevOps`, `Cybersecurity`).
- **14,070 non-domain records** (`Accountant`, `Advocate`, `Python Developer`, `Java Developer`, `Sales`, `Human Resources`, etc.) were excluded to prevent label ambiguity and data contamination.

### 2. Text Normalization
- HTML tag stripping (`<[^>]+>`) applied across all resume text strings.
- Excessive whitespace, tab characters, and consecutive empty lines collapsed to single spaces and double newlines.
- Encoding integrity verified (UTF-8 normalized).

### 3. Length Validation
- Checked for empty or extremely short (< 50 characters) documents.
- **0 records** were rejected for insufficient character length.

### 4. Deduplication & Near-Duplicate Filtering
- **Exact Duplicates**: **916 exact text duplicates** were detected and eliminated.
- **Near-Duplicates**: **55 near-duplicate resumes** (identifiable by MD5 snippet hashing over normalized leading text) were detected and purged to prevent data leakage across splits.

---

## 📈 Final Clean Class Distribution (`ml/data/processed/clean_mapped_resumes.csv`)

| Target Production Category | Clean Unique Resumes | Class Ratio |
| :--- | :---: | :---: |
| **Web Development** | 701 | 37.9% |
| **Data Science** | 413 | 22.3% |
| **Cybersecurity** | 370 | 20.0% |
| **DevOps** | 272 | 14.7% |
| **Cloud Computing** | 92 | 5.0% |
| **TOTAL CLEAN DATASET** | **1,848** | **100.0%** |

---

## 💾 Processed Data Artifacts

- **Processed File Path**: [`ml/data/processed/clean_mapped_resumes.csv`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/data/processed/clean_mapped_resumes.csv)
- **Raw Datasets Preserved**: Original files (`ml/data/raw/resumes.csv` and `ml/data/raw/archive/resumes_dataset.jsonl`) remain untouched.

---

*Phase 21C Data Quality & Cleaning complete. Awaiting user approval to proceed to Phase 21D (Data Leakage Prevention & Train/Val/Test Splitting).*
