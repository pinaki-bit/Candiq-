# DEVELOPER ONBOARDING & CONTRIBUTION GUIDE — RESUME INTEL

**Project**: Resume Intel  
**Document Version**: 1.0 (Phase 27.5 Checkpoint)  
**Date**: September 28, 2026  

---

## 1. PREREQUISITES

Before developing or running Resume Intel, ensure your local system meets the following prerequisites:

- **Python**: Version 3.10, 3.11, or 3.12 (Python 3.12 recommended).
- **Node.js & npm**: Optional (only required if developing the experimental `frontend_react` React app).
- **Tesseract OCR**: Optional (install `tesseract-ocr` via OS package manager if image-only PDF OCR is required locally).
- **Git**: Required for version control.

---

## 2. LOCAL ENVIRONMENT SETUP

### Step 1: Clone Repository
```bash
git clone https://github.com/pinaki-bit/Resume_screening-.git
cd Resume_screening-
```

### Step 2: Set Up Backend Virtual Environment
```bash
cd backend
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### Step 3: Install Backend Dependencies & spaCy Model
```bash
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 4: Environment Variable Configuration
Create a `.env` file in the `backend/` directory:
```ini
APP_ENV=development
SECRET_KEY=CHANGE_ME_USE_openssl_rand_hex_32
DATABASE_URL=sqlite:///./resume_screening.db
ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
MODEL_DIR=../ml/artifacts
ACTIVE_MODEL_FILENAME=model_latest.joblib
OOD_ENABLED=True
OOD_CONFIDENCE_THRESHOLD=0.85
OOD_POLICY_VERSION=v1.0-phase24-op4
AI_PROVIDER=mock
```

---

## 3. STARTING THE APPLICATION

### Launch Backend API Server
From the `backend/` directory with `.venv` active:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc API Documentation**: `http://127.0.0.1:8000/redoc`

### Launch Streamlit Frontend UI
In a separate terminal window from the repository root:
```bash
# Activate virtual environment
backend\.venv\Scripts\activate

# Run Streamlit UI
streamlit run frontend/app.py
```
- **Streamlit Web Interface**: `http://localhost:8501`

---

## 4. RUNNING TEST SUITE & REGRESSION CHECKS

The project includes an automated test suite covering unit, integration, OOD policy, real PDF upload, security, and regression tests.

### Run All Backend Tests
```bash
cd backend
python -m pytest
```

### Run Tests with Coverage Report
```bash
pytest --cov=app --cov-report=term-missing
```

### Run Specific Test Modules
```bash
pytest tests/test_ood_policy.py                  # Unit tests for OOD policy engine
pytest tests/test_e2e_abstention_verification.py # Integration tests for abstention flow
pytest tests/test_real_pdf_upload_e2e.py        # E2E test suite using real test PDFs
```

---

## 5. FILES THAT MUST NOT BE MODIFIED CASUALLY

To preserve application integrity, strictly adhere to the following rules:

> [!CAUTION]
> **1. Active Model Artifacts**: Never manually overwrite or edit `ml/artifacts/model_latest.joblib` or `ml/artifacts/model_v2.joblib` without running the full calibration and integrity audit scripts.  
> **2. Benchmark Datasets**: Never modify or re-partition `ml/data/processed/train.csv`, `ml/data/processed/val.csv`, or `ml/data/processed/test.csv`. `test.csv` ($N=278$) is an untouched final evaluation split.  
> **3. OOD Threshold & Policy Settings**: Never modify `ood_confidence_threshold` (frozen at $\tau = 0.85$) or change `ood_policy_version` (`v1.0-phase24-op4`) without explicit Phase 24 validation sign-off.

---

## 6. SAFE CUSTOMIZATION & EXTENSION POINTS

Where to safely add new capabilities without breaking existing pipelines:

- **Adding a New API Endpoint**: Add route function under `backend/app/api/v1/` and register router in `backend/app/api/v1/__init__.py`.
- **Adding a New Skill to Taxonomy**: Add entry to `shared/skill_taxonomy.json` under appropriate domain/category.
- **Adding a New UI Page**: Add view module under `frontend/views/` and register route in `frontend/app.py`.
- **Adding a New Unit Test**: Add test module under `backend/tests/` prefixed with `test_`.

---

## 7. COMMON TROUBLESHOOTING & DEBUGGING

### 1. `ModuleNotFoundError: No module named 'app'`
- **Fix**: Run `pytest` from the `backend/` directory, or ensure `PYTHONPATH=backend` is set in your environment.

### 2. `PDFValidationError: File does not appear to be a valid PDF`
- **Fix**: Ensure the uploaded file starts with PDF magic bytes (`%PDF-`). Text files renamed with `.pdf` extension will be rejected by magic byte signature validation.

### 3. Image-Only PDFs Return `status="failed"`
- **Fix**: Install Tesseract OCR on your OS (`sudo apt-get install tesseract-ocr` on Ubuntu/Debian, or `winget install Tesseract-OCR` on Windows).
