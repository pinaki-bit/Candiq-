# 📊 Phase 21A: ML Dataset Discovery & Audit Report

This report documents the exhaustive discovery and structural audit of all resume datasets available within the **Resume Intel** project workspace.

---

## 1. Executive Summary & Audit Scope

A comprehensive scan across `ml/data/raw/`, `ml/data/archive/`, and root directories identified **4 structured dataset files** (CSV / JSONL) containing over **37,000 combined raw resume records**, alongside **1,875 raw PDF resumes**.

### Summary Table of Discovered Datasets

| Dataset File | Format | Total Records | Text Column | Category Column | Unique Texts | Unique Categories | Missing Values |
| :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: |
| `ml/data/raw/resumes.csv` | CSV | 13,389 | `Text` | `Category` | 12,085 | 43 | 0 |
| `ml/data/raw/master_combined.csv` | CSV | 20,306 | `Text` | `Category` | 20,306 | 75 | 0 |
| `ml/data/raw/archive/resumes_dataset.jsonl` | JSONL | 3,500 | `Text` | `Category` | 3,304 | 36 | 0 |
| `ml/data/raw/ocr_results.csv` | CSV | 283 | `Text` | `Category` | 283 | 1 (`Accountant`) | 0 |
| `ml/data/raw/archive_1/Resumes PDF/` | PDF | 1,874 files | N/A (PDF) | Folder Name | 1,874 files | 17 | 0 |

---

## 2. Detailed Dataset Profiles

### 2.1 `ml/data/raw/resumes.csv`
- **File Path**: `ml/data/raw/resumes.csv`
- **Size**: 53.57 MB
- **Total Rows**: 13,389
- **Columns**: `Category` (string), `Text` (string)
- **Data Source**: Public Kaggle Resume Dataset (Kaggle Resume Corpus)
- **Language**: English
- **Missing Values**: 0 missing values in `Category` or `Text`.
- **Exact Duplicates**: 1,304 rows (9.74%) have duplicate resume text.
- **Unique Records**: 12,085
- **Category Count**: 43 distinct categories
- **Key Categories & Counts**:
  - `Education`: 410
  - `Electrical Engineering`: 384
  - `Mechanical Engineer`: 384
  - `Sales`: 364
  - `Human Resources`: 360
  - `Java Developer`: 348
  - `Network Security Engineer`: 330
  - `DotNet Developer`: 329
  - `Web Designing`: 309
  - `Data Science`: 299
  - `DevOps`: 289
  - `Python Developer`: 248
  - `React Developer`: 182
  - `Blockchain`: 47

---

### 2.2 `ml/data/raw/archive/resumes_dataset.jsonl`
- **File Path**: `ml/data/raw/archive/resumes_dataset.jsonl`
- **Size**: 17.11 MB
- **Total Rows**: 3,500
- **Columns** (12 fields):
  - `ResumeID` (int)
  - `Category` (string)
  - `Name` (string)
  - `Email` (string)
  - `Phone` (string)
  - `Location` (string)
  - `Summary` (string)
  - `Skills` (list of strings)
  - `Experience` (list of dicts)
  - `Education` (list of dicts)
  - `Text` (string - full text)
  - `Source` (string)
- **Data Source**: Curated Technical Resume Benchmark Dataset
- **Language**: English
- **Missing Values**: 0 missing values across all 12 fields.
- **Exact Duplicates**: 196 rows (5.60%) have duplicate resume text.
- **Unique Records**: 3,304
- **Category Count**: 36 tech/engineering categories
- **Key Categories & Counts**:
  - `Java Developer`: 200
  - `Python Developer`: 200
  - `Data Science`: 200
  - `DevOps`: 180
  - `SQL Developer`: 180
  - `Web Designing`: 150
  - `React Developer`: 150
  - `Cloud Engineer`: 92
  - `Machine Learning Engineer`: 81
  - `Frontend Developer`: 76
  - `Backend Developer`: 76
  - `Cybersecurity Analyst`: 66
  - `Full Stack Developer`: 102

---

### 2.3 `ml/data/raw/master_combined.csv`
- **File Path**: `ml/data/raw/master_combined.csv`
- **Size**: 128.74 MB
- **Total Rows**: 20,306
- **Columns**: `Category` (string), `Text` (string)
- **Data Source**: Aggregated Master Corpus (combining multiple Kaggle datasets)
- **Language**: English
- **Missing Values**: 0 missing values.
- **Exact Duplicates**: 0 exact text duplicates (pre-deduplicated).
- **Category Count**: 75 distinct raw categories (including domain variations like `Datawarehousing, ETL, Informatica Resumes`, `SQL Developers Resumes`, `Web Developer Resumes`, `Network and Systems Administrators Resumes`).

---

### 2.4 `ml/data/raw/ocr_results.csv`
- **File Path**: `ml/data/raw/ocr_results.csv`
- **Size**: 1.22 MB
- **Total Rows**: 283
- **Columns**: `Filename`, `Category`, `Text`
- **Data Source**: OCR fallback extraction benchmark (`EasyOCR` outputs from image-only PDFs)
- **Category**: 1 category (`Accountant`)

---

### 2.5 PDF Document Archives
- **Directory**: `ml/data/raw/archive_1/Resumes PDF/`
- **Total PDF Files**: 1,874 PDFs across 17 domain subdirectories (Accountant, Advocate, Agricultural, Apparel, Architect, Arts, Automobile, Aviation, etc.).

---

## 3. Existing Preprocessing & Train/Test Split Status

- **Existing Preprocessing**: Text normalization script exists in [`ml/src/preprocessing.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/src/preprocessing.py) (lowercasing, punctuation cleanup, URL removal).
- **Existing Train/Test Split**: No pre-baked train/test split files exist on disk. Previous training runs performed dynamic 80/20 train/test splits during model fitting in `train_model.py`.

---

## 4. Key Findings & Recommendations for Phase 21B

1. **Rich Technical Representation**: `resumes.csv` (13,389 rows) and `resumes_dataset.jsonl` (3,500 rows) contain thousands of resumes directly corresponding to the 5 target production domains (`Data Science`, `Web Development`, `DevOps`, `Cloud Computing`, `Cybersecurity`).
2. **Class Mapping Requirement**: In Phase 21B, an explicit mapping matrix must map granular labels (e.g. `Machine Learning Engineer` -> `Data Science`, `React Developer` -> `Web Development`, `Cloud Engineer` -> `Cloud Computing`, `Network Security Engineer` -> `Cybersecurity`) while explicitly marking non-tech categories (`Accountant`, `Advocate`, `Agriculture`) as `UNMAPPED`.
3. **Data Hygiene Needed**: Deduplication and length filtering (< 50 chars) must be executed before creating the 70/15/15 train/validation/test split in Phase 21C/21D.

---

*Phase 21A Dataset Discovery complete. Awaiting user approval to proceed to Phase 21B (Label Mapping).*
