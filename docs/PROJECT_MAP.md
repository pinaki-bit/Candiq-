# PROJECT MAP & DIRECTORY REGISTRY — RESUME INTEL

**Project**: Resume Intel  
**Document Version**: 1.0 (Phase 27.5 Checkpoint)  
**Date**: September 28, 2026  

---

## 1. HIGH-LEVEL DIRECTORY MAP

```text
RESUME_SCREENING/
├── backend/
│   ├── app/
│   │   ├── api/            # Route dependencies, CORS & rate limiters
│   │   ├── api/v1/         # REST API endpoints (auth, resumes, jobs, ats, extension, analytics)
│   │   ├── core/           # Security, password hashing, JWT tokens, sanitization
│   │   ├── models/         # SQLAlchemy ORM models (User, Resume, Job, Skill, Candidate, Audit)
│   │   ├── schemas/        # Pydantic validation and serialization schemas
│   │   ├── services/       # Service layer (PDF, NLP, ML, OOD, Matching, Ranking, AI, WS, Cost)
│   │   ├── config.py       # Application settings & environment variables
│   │   ├── database.py     # SQLAlchemy session setup & engine creation
│   │   ├── main.py         # FastAPI app entrypoint, CORS, & middleware
│   │   └── rate_limiter.py # SlowAPI rate limiting configuration
│   └── tests/              # Pytest automated test suite (162 tests)
│
├── frontend/
│   ├── app.py              # Streamlit navigation router & auth gate
│   ├── components/         # Reusable Streamlit UI components & 3D Three.js visualizers
│   ├── views/              # View pages (Dashboard, Upload, Jobs, Results, Builder, ATS, Talent, 3D, Admin)
│   └── services/           # Backend HTTP API client & WebSocket listener
│
├── frontend_react/         # Secondary React + Vite UI (Experimental)
├── browser_extension/       # Chrome Manifest v3 Extension package
├── ml/
│   ├── artifacts/          # Trained model pipelines (model_latest.joblib, model_v2.joblib)
│   ├── data/               # Raw & processed CSV datasets (train.csv, val.csv, test.csv)
│   ├── scripts/            # Training, calibration, and evaluation scripts
│   └── test_pdfs/          # Real PDF test assets for integration testing
│
├── reports/                # Evaluation & threshold validation JSON/CSV artifacts
├── docs/                   # Engineering documentation (Architecture, Decisions, Development, Phase History)
└── shared/                 # Shared JSON taxonomies (skill_taxonomy.json, label_mapping.json)
```

---

## 2. DETAILED FILE & MODULE REGISTRY

| File / Directory | Component Responsibility | Primary Callers / Used By | Important Dependencies |
| :--- | :--- | :--- | :--- |
| **`backend/app/main.py`** | FastAPI app initialization, CORS middleware, security headers, lifespan event handling. | Uvicorn / Gunicorn server. | FastAPI, app.config, app.api.v1 |
| **`backend/app/config.py`** | Pydantic v2 `Settings` configuration loader from `.env`. Auto-generates SECRET_KEY. | All backend services & routers. | Pydantic BaseSettings |
| **`backend/app/database.py`** | SQLAlchemy engine creation, session factory (`get_db`), declarative Base. | All ORM models & routers. | SQLAlchemy 2.0 |
| **`backend/app/api/dependencies.py`** | Auth dependencies (`AnyAuthUser`, `HRUser`, `AdminUser`) validating JWT tokens. | API routers (`backend/app/api/v1/`). | app.core.security, app.models.user |
| **`backend/app/core/security.py`** | Password hashing (bcrypt), JWT access token generation & decoding. | Auth router, dependencies. | passlib, python-jose / PyJWT |
| **`backend/app/core/sanitizer.py`** | HTML escaping & string sanitization against XSS attacks. | Resume & Candidate ingestion. | html, re |
| **`backend/app/models/user.py`** | `User` SQLAlchemy ORM model (roles: `admin`, `hr`, `readonly`). | Auth, Admin router, DB. | SQLAlchemy Base |
| **`backend/app/models/resume.py`** | `Resume` ORM model storing metadata, text char count, domain, and OOD fields. | Resume pipeline, API router. | SQLAlchemy Base, ProcessingStatus |
| **`backend/app/models/candidate.py`** | `Candidate` ORM model storing candidate profile info. | Resume router, Screening. | SQLAlchemy Base |
| **`backend/app/models/job.py`** | `Job` ORM model storing job title, domain, and skill requisitions. | Job router, Matching service. | SQLAlchemy Base |
| **`backend/app/models/skill.py`** | `ExtractedSkill` ORM model storing matched resume skills. | Skill service, Resume router. | SQLAlchemy Base |
| **`backend/app/models/screening.py`**| `ScreeningResult` ORM model storing candidate-job match score & rank. | Screening router, Matching service. | SQLAlchemy Base |
| **`backend/app/models/audit_event.py`**| `AuditEvent` ORM model for access audit logging. | Audit service, Admin router. | SQLAlchemy Base |
| **`backend/app/schemas/resume.py`** | Pydantic schemas (`ResumeRead`, `ResumeDetailRead`, `ATSCheckResponse`, etc.). | Resume router, API responses. | Pydantic v2 |
| **`backend/app/schemas/job.py`** | Pydantic schemas (`JobCreate`, `JobRead`, `JobUpdate`). | Job router, Matching. | Pydantic v2 |
| **`backend/app/services/pdf_service.py`** | PDF validation, storage under UUID, `pdfminer.six` text extraction, OCR fallback. | `_run_processing_pipeline` in resumes.py. | pdfminer.six, pytesseract, pdf2image |
| **`backend/app/services/skill_service.py`** | spaCy PhraseMatcher NLP skill extraction against taxonomy. | Resume upload pipeline. | spaCy (`en_core_web_sm`), skill_taxonomy.json |
| **`backend/app/services/classification_service.py`** | LRU-cached model loading, SHA-256 sidecar hash verification, classifier execution. | Resume processing pipeline. | joblib, scikit-learn, ood_policy.py |
| **`backend/app/services/ood_policy.py`** | OOD / Abstention policy evaluation engine ($\tau = 0.85$, policy `v1.0-phase24-op4`). | `classification_service.py`. | app.config |
| **`backend/app/services/matching_service.py`**| Candidate-to-job skill match and domain alignment calculation. | Screening router, Results page. | app.models.job, app.models.resume |
| **`backend/app/services/ranking_service.py`** | Hybrid candidate ranking combining skill match, domain alignment, and ATS score. | Screening router. | matching_service.py |
| **`backend/app/services/embedding_service.py`**| TF-IDF / Hashing vector cosine similarity engine. | Matching & Talent Search. | scikit-learn, numpy |
| **`backend/app/services/ai_service.py`** | LLM provider abstraction (`MockAIProvider`, OpenAI, Gemini) with guardrails. | Bullet rewriter, Cover letter, Interview kit. | app.config |
| **`backend/app/services/websocket_manager.py`**| WebSocket connection manager broadcasting pipeline events. | `_run_processing_pipeline`, `/ws/pipeline`. | asyncio, FastAPI WebSocket |
| **`backend/app/services/cost_tracking_service.py`**| LLM token consumption & cost tracking telemetry. | AI service, Analytics router. | app.config |
| **`frontend/app.py`** | Main Streamlit navigation router, session state initialization, and auth gate. | User browser. | Streamlit, views/ |
| **`frontend/views/upload.py`** | Streamlit upload view rendering file uploader, status banners, & resume advisor. | frontend/app.py. | services/api_client.py |
| **`frontend/views/results.py`** | Streamlit results view rendering candidate score charts, skill match cards, & reviews. | frontend/app.py. | services/api_client.py, Plotly |
| **`frontend/services/api_client.py`**| Frontend HTTP client communicating with FastAPI backend endpoints. | Streamlit views (`frontend/views/`). | requests |
| **`ml/artifacts/model_latest.joblib`**| Active production ML model artifact (LinearSVC classifier + TF-IDF). | `classification_service.py`. | scikit-learn |
| **`ml/artifacts/model_v2.joblib`**| Candidate ML model artifact (Calibrated LinearSVC pipeline). | ML evaluation scripts. | scikit-learn |
| **`ml/data/processed/`** | Core benchmark datasets (`train.csv`, `val.csv`, `test.csv`). | ML evaluation, Phase 24–27 scripts. | pandas |
