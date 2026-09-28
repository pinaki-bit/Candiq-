# Phase 23A — External Data Audit & Provenance Report

## Executive Summary

Phase 23A conducts a comprehensive audit of all raw data sources in the repository to identify genuinely independent external validation candidates for evaluating **Candidate Model v2** (`ml/artifacts/model_v2.joblib`) and **Baseline Model** (`ml/artifacts/model_latest.joblib`).

Per the Phase 23 prompt directives, candidate external data sources must **NOT** be derived from or contaminated by:
- `ml/data/processed/train.csv` (1,293 records)
- `ml/data/processed/val.csv` (277 records)
- `ml/data/processed/test.csv` (278 records)
- `ml/data/processed/clean_mapped_resumes.csv` (1,848 records)
- `ml/data/raw/resumes.csv` (13,389 records - parent source)
- `ml/data/raw/archive/resumes_dataset.jsonl` (3,500 records - parent source)

---

## 1. Summary of Evaluated Data Sources

| Candidate Data Source | File Path | Total Records | Text Availability | Overlap with `clean_mapped_resumes` | Dataset Family / Provenance | Independent Candidate Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **Source 1: Unseen Master Collection** | `ml/data/raw/master_combined.csv` | 20,306 | 100% (CSV Text) | 1,238 exact matches<br>(**19,068 unseen**) | Web-scraped resume collection family (Kaggle/LiveCareer). Contains 19,068 unseen records across 75 categories. | **CANDIDATE** (Same family, unseen records) |
| **Source 2: OCR Extracted Resumes** | `ml/data/raw/ocr_results.csv` | 283 | 100% (OCR Text) | 0 exact matches | OCR extracted text from PDF resumes in `Resumes PDF/Accountant resumes`. | **OUT-OF-DOMAIN** (100% Accountant) |
| **Source 3: Archive PDF Corpus** | `ml/data/raw/archive_1/Resumes PDF/` | 1,874 | PDF Binary (requires PyMuPDF) | 0 exact matches | PDF document corpus across 17 non-technical subdirectories (Accountant, Advocate, Aviation, etc.). | **OUT-OF-DOMAIN** (100% Non-tech) |
| **Source 4: Phase 20 Verification PDFs** | `audit_pdfs/*.pdf` | 5 | 100% (PDF Extraction) | 0 exact matches | Synthetic end-to-end audit resumes crafted in Phase 20 (1 per canonical target class). | **CANDIDATE** (Synthetic, N=5) |
| **Source 5: Raw Parent Collections** | `resumes.csv` / `resumes_dataset.jsonl` | 13,389 / 3,500 | 100% (CSV/JSONL) | 1,238 / 1,346 exact matches | Direct parent source datasets used to construct `clean_mapped_resumes.csv` in Phase 21. | **REJECTED** (Parent Contaminated) |

---

## 2. Detailed Source Audits

### 2.1 Source 1: Unseen `master_combined.csv` Pool
- **File Path**: `ml/data/raw/master_combined.csv`
- **Total Record Count**: 20,306 rows
- **Provenential Origin**: Merged multi-source raw resume dataset containing web-scraped resumes from public online repositories.
- **Labels / Categories**: 75 distinct raw categories (e.g., `Web Developer Resumes` [706], `DevOps` [22], `Data Science` [13], `Network Security Engineer` [5], `Python Developer` [175], `Network and Systems Administrators Resumes` [674], `Java Developer` [288], `DotNet Developer` [279], etc.).
- **Overlap Analysis**:
  - Overlap with `clean_mapped_resumes.csv` (1,848): **1,238 records** (67.0% of clean set).
  - Overlap with `train.csv`: 862 records.
  - Overlap with `val.csv`: 179 records.
  - Overlap with `test.csv`: 197 records.
  - **Genuinely Unseen Records**: **19,068 records** do NOT appear in `clean_mapped_resumes.csv`.
- **Dataset Family Assessment**: Belongs to the same underlying data collection family (LiveCareer / Kaggle ResumeAtlas scrapes) as `resumes.csv`, but provides 19,068 un-cleaned records that were never part of the Phase 21 train/val/test splits.

### 2.2 Source 2: OCR Extracted Dataset (`ocr_results.csv`)
- **File Path**: `ml/data/raw/ocr_results.csv`
- **Total Record Count**: 283 records
- **Provenential Origin**: Tesseract OCR / text extraction results generated from PDF resume images stored under `Resumes PDF/Accountant resumes/`.
- **Labels / Categories**: Single category: `Accountant` (283 records).
- **Text Availability**: 100% text available.
- **Overlap Analysis**: **0 records** overlap with `train.csv`, `val.csv`, `test.csv`, or `clean_mapped_resumes.csv`.
- **Dataset Family Assessment**: Independent document collection. However, all 283 records belong to the `Accountant` profession, which is an out-of-domain class relative to our 5 technical target classes (`Data Science`, `Web Development`, `Cloud Computing`, `DevOps`, `Cybersecurity`). Useful for unmapped/negative testing.

### 2.3 Source 3: Raw PDF Corpus (`archive_1/Resumes PDF/`)
- **File Path**: `ml/data/raw/archive_1/Resumes PDF/`
- **Total Record Count**: 1,874 PDF documents across 17 subdirectories.
- **Subdirectory Breakdowns**:
  - `Accountant`: 284 files
  - `Accountant resumes`: 67 files
  - `Advocate`: 247 files
  - `Advocate resumes`: 94 files
  - `Agricultural`: 199 files
  - `Agricultural resumes`: 68 files
  - `Agriculture`: 79 files
  - `Apparel`: 69 files
  - `Apparel resumes`: 51 files
  - `Architect`: 84 files
  - `Architects resumes`: 60 files
  - `Arts`: 255 files
  - `Arts resumes`: 68 files
  - `Automobile`: 73 files
  - `Automobile resumes`: 40 files
  - `Aviation`: 85 files
  - `Aviation resumes`: 51 files
- **Labels / Categories**: Non-technical professional categories.
- **Text Availability**: Binary PDF files (parseable using PyMuPDF / PyPDF2).
- **Overlap Analysis**: **0 records** overlap with text splits (these are raw PDF files).
- **Dataset Family Assessment**: Independent raw PDF corpus. Out-of-domain relative to the 5 target IT domains.

### 2.4 Source 4: Phase 20 Verification PDFs (`audit_pdfs/`)
- **File Path**: `audit_pdfs/*.pdf`
- **Total Record Count**: 5 PDF documents
- **Provenential Origin**: Synthetic test resumes authored during the Phase 20 reality verification audit to test live system end-to-end PDF parsing and domain classification.
- **Files & Target Labels**:
  1. `resume_cloud_elena.pdf` -> `Cloud Computing`
  2. `resume_devops_marcus.pdf` -> `DevOps`
  3. `resume_ds_alex.pdf` -> `Data Science`
  4. `resume_sec_david.pdf` -> `Cybersecurity`
  5. `resume_web_sarah.pdf` -> `Web Development`
- **Text Availability**: 100% parseable text (655 - 1,036 characters per PDF).
- **Overlap Analysis**: **0 records** overlap with `train.csv`, `val.csv`, `test.csv`, or `clean_mapped_resumes.csv`.
- **Dataset Family Assessment**: Genuinely independent synthetic test records created out-of-band. High quality, but very small sample size ($N=5$).

### 2.5 Source 5: Raw Parent Collections (`resumes.csv` & `resumes_dataset.jsonl`)
- **File Paths**: `ml/data/raw/resumes.csv` (13,389 rows) & `ml/data/raw/archive/resumes_dataset.jsonl` (3,500 records)
- **Overlap Analysis**: High contamination. `clean_mapped_resumes.csv` (1,848 records) was derived directly from `resumes.csv` and `resumes_dataset.jsonl` via text normalization, domain category filtering, and deduplication.
- **Conclusion**: **REJECTED** from external validation to prevent data leakage and split contamination.

---

## 3. Available Genuinely Independent Source Candidates Summary

To construct an independent external validation set (`23D`) without dataset contamination:

1. **Unseen `master_combined.csv` Records**: Provides 19,068 unseen records. We can extract non-overlapping records for categories semantically mapping to `Web Development`, `DevOps`, `Data Science`, `Cybersecurity`, and `Cloud Computing` (via keyword text matching).
2. **Phase 20 `audit_pdfs/` Resumes**: Provides 5 out-of-band test records covering all 5 target classes.
3. **Out-of-Domain Negative Samples**: `ocr_results.csv` (283 Accountant records) and `archive_1` PDFs provide out-of-domain resumes to test model behavior on unmapped categories.

---

> [!IMPORTANT]
> **PHASE 23A STOP DIRECTIVE SATISFIED**
> No model evaluation or retraining has been performed. Candidate model `model_v2.joblib` remains unpromoted in `ml/artifacts/`, and production `model_latest.joblib` remains untouched.
