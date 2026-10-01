# DEVELOPMENT & CONTRIBUTION GUIDE

## 1. Local Development Environment
### Environment Setup
- Python 3.12+
- Virtual Environment: `python -m venv backend/.venv`

### Backend Server
```bash
cd backend
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

### Frontend Workspace
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

---

## 2. Running Test Suites
```bash
# Run all backend tests (300+ tests across Phases 1–38)
backend\.venv\Scripts\python.exe -m pytest backend/tests

# Run specific Phase test
backend\.venv\Scripts\python.exe -m pytest backend/tests/test_phase38_final_release.py
```

---

## 3. Code Standards & Architecture Guidelines
- **No Direct Local State Mutation**: Mutate ORM entities through explicit SQLAlchemy transactions.
- **Tenant Isolation**: Always verify `tenant_id` on resource queries using `verify_tenant_access`.
- **No Fake Data**: All monitoring metrics and analytics must query real persisted data or report missing data cleanly.
- **Model Integrity**: Never alter ML model artifacts (`.joblib`) or datasets (`train.csv`, `val.csv`, `test.csv`).
