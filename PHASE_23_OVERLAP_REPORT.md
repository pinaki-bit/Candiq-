# Phase 23B — Overlap & Data Contamination Audit Report

## Executive Summary

Phase 23B performs an empirical multi-level overlap and data contamination audit across all candidate data sources in the repository against:
- `ml/data/processed/train.csv` (1,293 records)
- `ml/data/processed/val.csv` (277 records)
- `ml/data/processed/test.csv` (278 records)
- `ml/data/processed/clean_mapped_resumes.csv` (1,848 records)

---

## 1. Multi-Level Overlap & Contamination Metrics

| Candidate Data Source | Total Records | Exact Text Overlap | Full SHA-256 Match | Leading 400-Char Snippet Match | TF-IDF Cosine Sim $\ge 0.85$ | Synthetic Template Header Match | Source-Family Classification | Legitimate Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **`master_combined.csv`** | 20,306 | **1,238** (6.1%) | 1,238 | 1,300 | 1,360 | **6,834** (33.7%) | Same Web-Scraped LiveCareer Family | **UNSEEN BUT SAME-FAMILY CONTAMINATED** |
| **`ocr_results.csv`** | 283 | **0** (0.0%) | 0 | 0 | 2 | 171 (60.4%) | PDF OCR Extracted Accountant Resumes | **OUT-OF-DOMAIN (Accountant)** |
| **`archive_1/Resumes PDF/`** | 1,874 | **0** (0.0%) | 0 | 0 | 0 | 0 (0.0%) | Independent PDF Corpus (17 non-IT classes) | **INDEPENDENT & OUT-OF-DOMAIN** |
| **`audit_pdfs/*.pdf`** | 5 | **0** (0.0%) | 0 | 0 | 0 | 0 (0.0%) | Phase 20 Synthetic End-to-End Test Set | **INDEPENDENT SYNTHETIC TEST SET** ($N=5$) |

---

## 2. Detailed Breakdown by Split & Level

### 2.1 `master_combined.csv` (20,306 records)
- **Exact Text Overlap with Benchmark Splits**:
  - `train.csv`: **862 records**
  - `val.csv`: **179 records**
  - `test.csv`: **197 records**
  - Total exact overlap with `clean_mapped_resumes.csv`: **1,238 records** (6.1%).
- **Hash Overlap**:
  - Full text SHA-256 match: 1,238 records.
  - Leading 400-char normalized snippet match: **1,300 records** (62 near-duplicates sharing leading header structure).
- **TF-IDF Cosine Similarity Thresholds**:
  - Cosine Similarity $\ge 0.85$: **1,360 records**
  - Cosine Similarity $\ge 0.90$: **1,330 records**
  - Cosine Similarity $\ge 0.95$: **1,310 records**
- **Template / Boilerplate Contamination**:
  - **6,834 records** (33.7% of all records in `master_combined.csv`) contain the standardized synthetic header pattern (`"Jessica Claire 100 Montgomery St..."`).
- **Source-Family Assessment**:
  - **CRITICAL**: `master_combined.csv` CANNOT be labeled as an "independently sourced external dataset."
  - It originates from the **exact same web-scraped dataset family** (LiveCareer / Kaggle ResumeAtlas scrapes) as `resumes.csv` and `clean_mapped_resumes.csv`.
  - While 19,068 records are "unseen" (not present in Phase 21 train/val/test splits), over one-third of them share identical synthetic contact templates with the training dataset.

### 2.2 `ocr_results.csv` (283 records)
- **Exact Text Overlap**: **0 records** (0.0%).
- **Hash & TF-IDF Overlap**: 0 hash matches, only 2 records with TF-IDF cosine similarity $\ge 0.85$.
- **Template Contamination**: **171 records** (60.4%) contain the LiveCareer template header (`"Jessica Claire..."`).
- **Source-Family Assessment**:
  - Out-of-domain dataset (100% Accountant profession).
  - Useful as an out-of-domain negative test set, but shares template artifacts with LiveCareer.

### 2.3 `archive_1/Resumes PDF/` (1,874 PDF files across 17 subdirectories)
- **Exact Text Overlap**: **0 records** (0.0%).
- **Hash & TF-IDF Overlap**: 0 hash or high-similarity matches.
- **Template Contamination**: **0 records** (0.0%).
- **Source-Family Assessment**:
  - **Genuinely Independent & Out-of-Domain**.
  - Originates from a completely separate PDF document repository across 17 non-IT categories (Accountant, Advocate, Aviation, Agricultural, Arts, etc.). Zero overlap or template leakage with training data.

### 2.4 `audit_pdfs/*.pdf` (5 synthetic PDFs)
- **Exact Text Overlap**: **0 records** (0.0%).
- **Hash & TF-IDF Overlap**: 0 hash or high-similarity matches.
- **Template Contamination**: **0 records** (0.0%).
- **Source-Family Assessment**:
  - **Genuinely Independent Synthetic Test Resumes** created in Phase 20 (Elena Rostova, Marcus Vance, Alex Mercer, David K. Miller, Sarah Chen). Clean, concise, out-of-band test set covering all 5 canonical target classes.

---

## 3. Data Source Classification Summary

| Dataset Name | Unseen Records Count | Same-Family Contamination? | Legitimate External Classification | Recommended Usage |
| :--- | :---: | :---: | :--- | :--- |
| **`master_combined.csv`** | 19,068 | **YES** (Shared LiveCareer Scraping Family) | **UNSEEN SAME-FAMILY POOL** | Candidates must be strictly filtered for overlap & template leakage before evaluation. |
| **`ocr_results.csv`** | 283 | **YES** (Shared Template Header) | **OUT-OF-DOMAIN NEGATIVE TEST** | Out-of-domain negative class evaluation (Accountant). |
| **`archive_1/Resumes PDF/`** | 1,874 | **NO** | **INDEPENDENT OUT-OF-DOMAIN PDF CORPUS** | Out-of-domain generalizability testing across non-IT professions. |
| **`audit_pdfs/*.pdf`** | 5 | **NO** | **INDEPENDENT SYNTHETIC TEST SET** ($N=5$) | Out-of-band zero-shot evaluation on clean technical resumes. |

---

> [!IMPORTANT]
> **PHASE 23B STOP DIRECTIVE SATISFIED**
> No models have been trained or evaluated. Production `model_latest.joblib` and candidate `model_v2.joblib` remain untouched. Dataset splits (`train.csv`, `val.csv`, `test.csv`) remain 100% untouched.
