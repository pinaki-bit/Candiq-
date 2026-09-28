# 🔍 PROJECT AUDIT: RESUME INTEL

**Audit Date**: September 27, 2026  
**Project Name**: Resume Intelligence (ATS & Hiring Intelligence Platform)  
**Status**: Existing Production Codebase Audit Completed  

---

## 1. Executive Summary

A comprehensive repository audit was conducted across all subsystems of the **Resume Intel** codebase. The repository contains a fully functional, multi-tiered AI Applicant Tracking System featuring:
- **FastAPI Backend (`/backend`)**: Asynchronous Python web API with JWT auth, rate-limiting, audit logging, and SQLite database.
- **Trained Machine Learning Model (`/ml`)**: TF-IDF + LinearSVC classification pipeline serialized as `.joblib` artifacts predicting job categories across 5 target domains.
- **NLP & Feature Pipeline (`/backend/app/services`)**: `spaCy` tokenization, entity extraction, section parsing, and `PhraseMatcher`-based taxonomy skill extraction against `shared/skill_taxonomy.json`.
- **Dual Frontend Implementations**:
  1. **Streamlit UI (`/frontend`)**: HR Admin dashboard for resume uploads, job screening, candidate filtering, analytics, and password management.
  2. **React + Three.js Dashboard (`/frontend_react`)**: Vite, TypeScript, TailwindCSS v4, Zustand, Framer Motion, and React Three Fiber (`@react-three/fiber` 3D Canvas with `IntelligenceCore.tsx`).

---

## 2. Component-by-Component Inventory

### 2.1 Backend Subsystem (`/backend`)
- **Framework**: FastAPI `0.111.1` running on Uvicorn `0.30.1`.
- **Database & ORM**: SQLAlchemy `2.0.31` with SQLite database (`resume_screening.db`) and Alembic migrations.
- **Models Implemented (`/backend/app/models`)**:
  - `User`: Admin/HR/Readonly RBAC, password hashes, `must_change_password` flag.
  - `Job` & `JobRequirement`: Job postings with required & preferred skills.
  - `Candidate` & `Resume`: Candidate profiles, UUID file references, processing status (`uploaded`, `processing`, `completed`, `needs_review`, `failed`).
  - `ExtractedSkill`: Extracted skill canonical names, domain tags, evidence snippets, frequencies.
  - `ScreeningResult`: Relevance score, tier (`Excellent`, `Good`, `Fair`, `Low Match`), coverage breakdown, review status (`pending`, `approved`, `rejected`, `on_hold`).
  - `ModelVersion`: Artifact hash verification and active ML version tracking.
  - `TokenBlocklist`: Server-side JWT JTI revocation.
  - `AuditEvent`: Security & access log trails.
  - `Notification`: In-app notification queue.
- **API Endpoints (`/backend/app/api/v1`)**:
  - `/api/v1/auth`: `login`, `logout`, `change-password`, `revoke-all`, `me`.
  - `/api/v1/resumes`: `upload`, `list`, `get_by_id`, `archive`.
  - `/api/v1/jobs`: CRUD operations for job postings & requirements.
  - `/api/v1/screening`: `match/{job_id}/{resume_id}`, `get_job_results`, `update_review`.
  - `/api/v1/admin`: User management, database stats, model status.
  - `/api/v1/analytics`: Aggregate statistics, domain breakdown, skill demand.

### 2.2 Machine Learning & NLP Pipeline (`/ml` & `/backend/app/services`)
- **Trained Model Artifacts (`/ml/artifacts`)**:
  - `model_latest.joblib` (4.17 MB): Serialized Scikit-Learn `LinearSVC` + `TfidfVectorizer` pipeline trained on resume dataset.
  - Hash Integrity Verification: SHA-256 sidecar verification in `classification_service.py`.
  - Target Categories: `Data Science`, `Web Development`, `Cloud Computing`, `DevOps`, `Cybersecurity`.
  - Confidence Thresholds: High ($\ge 0.70$), Medium ($\ge 0.45$), Low ($< 0.45 \rightarrow$ `needs_review`).
- **NLP Service (`nlp_service.py` & `skill_service.py`)**:
  - Uses `spaCy` (`en_core_web_sm` / `en_core_web_lg`) for named entity recognition (ORG, DATE, GPE) and token lemmatization.
  - `PhraseMatcher` against `shared/skill_taxonomy.json` for deterministic technical skill extraction.
- **PDF Processing (`pdf_service.py`)**:
  - Text extraction via `pdfminer.six` with fallback support for OCR processing.

### 2.3 Frontend Subsystems
- **Streamlit App (`/frontend`)**:
  - Main router `app.py` with views: `dashboard.py`, `upload.py`, `jobs.py`, `results.py`, `analytics.py`, `admin.py`, `candidate_profile.py`, `audit_logs.py`.
  - Reusable advisor component `frontend/components/resume_advisor.py` providing actionable resume upgrade suggestions.
- **React 19 3D Interface (`/frontend_react`)**:
  - Vite + React + TypeScript web app with Three.js (`@react-three/fiber`, `@react-three/drei`).
  - 3D Visualizer `IntelligenceCore.tsx` rendering animated canvas representing AI pipeline states.
  - Views: `Login.tsx`, `UploadPortal.tsx`, `TalentExplorer.tsx`, `Jobs.tsx`, `AdminAnalytics.tsx`.

---

## 3. Ground Truth Verification & Dependencies

| Subsystem | Version / Tech | Key Dependencies | Status |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | `fastapi`, `sqlalchemy`, `scikit-learn`, `spacy`, `pdfminer.six`, `uvicorn`, `slowapi` | Healthy & Verified |
| **ML Model** | Joblib Artifact | `LinearSVC` + `TfidfVectorizer` (4.17MB) | Active (`model_latest.joblib`) |
| **Streamlit** | 1.36.0 | `streamlit`, `requests`, `plotly`, `pandas` | Active on Port 8501 |
| **React** | 19.2.8 / Vite 8 | `three`, `@react-three/fiber`, `@react-three/drei`, `zustand`, `lucide-react` | Active |
| **Database** | SQLite | `resume_screening.db` with 11 relational tables | Populated & Seeded |

---

## 4. Protected Assets & Constraints

The following core assets must remain untouched and fully preserved during all upcoming upgrade phases:
1. **Model Pipeline**: `ml/artifacts/model_latest.joblib` and `ml/scripts/train_model.py`.
2. **Preprocessing Integrity**: `ml/src/preprocessing.py` clean_text logic.
3. **Database Data**: Existing DB tables, schemas, and seeded records in `resume_screening.db`.
4. **Existing API Routes**: All `/api/v1/*` contracts must maintain backward compatibility.
5. **Deterministic Foundation**: Classification and skill matching must remain deterministic; LLM functionality will only augment, not replace them.
