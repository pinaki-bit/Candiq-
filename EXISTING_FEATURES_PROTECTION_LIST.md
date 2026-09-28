# 🛡️ EXISTING FEATURES PROTECTION LIST

The following features, files, data models, and services in the **Resume Intel** project are core components and **MUST NOT BE BROKEN, REMOVED, DELETED, OR REPLACED WITH FAKE DATA** during any phase of this master upgrade:

---

## 1. Machine Learning & Classification Assets
- **Trained Model Artifact (`ml/artifacts/model_latest.joblib`)**: Scikit-Learn `LinearSVC` + `TF-IDF` vectorizer model trained on real resume datasets. Must remain the authoritative engine for resume domain classification.
- **Model Training Pipeline (`ml/scripts/train_model.py`)**: The model training and evaluation script.
- **Text Preprocessing Pipeline (`ml/src/preprocessing.py`)**: The deterministic `clean_text` function and `build_feature_pipeline`.
- **Classification Service (`backend/app/services/classification_service.py`)**: Artifact loading, hash verification, probability estimation, and confidence thresholding (`high`, `medium`, `low`).

## 2. NLP & Skill Extraction System
- **spaCy Pipeline (`backend/app/services/nlp_service.py`)**: `en_core_web_sm` / `en_core_web_lg` model loading, entity recognition (ORG, DATE, GPE), and token normalization.
- **Skill Extraction Service (`backend/app/services/skill_service.py`)**: `PhraseMatcher` logic against `shared/skill_taxonomy.json`.
- **Taxonomy Mappings (`shared/skill_taxonomy.json`, `shared/label_mapping.json`)**: Core taxonomy mapping dataset.

## 3. Database Schema & Data Integrity
- **SQLite Database (`backend/resume_screening.db`)**: Active database containing user accounts, candidate profiles, resume records, extracted skills, jobs, screening results, and audit trails.
- **Database Models (`backend/app/models/`)**:
  - `User` (password hashing, RBAC roles)
  - `Job` & `JobRequirement`
  - `Candidate` & `Resume`
  - `ExtractedSkill`
  - `ScreeningResult`
  - `ModelVersion`
  - `TokenBlocklist`
  - `AuditEvent`
  - `Notification`

## 4. REST API Routes (`backend/app/api/v1/`)
- `/api/v1/auth`: JWT Login, Logout, Revoke-All, Change-Password, Me.
- `/api/v1/resumes`: Upload PDF, List Resumes, Get Resume Detail with Extracted Skills, Archive Resume.
- `/api/v1/jobs`: Create Job, List Jobs, Get Job Detail, Update Job, Delete Job.
- `/api/v1/screening`: Match Resume to Job, Get Job Screening Results, Update Candidate Review Status.
- `/api/v1/admin`: System Stats, User Management, Active Model Status.
- `/api/v1/analytics`: Aggregate Dashboard Statistics, Category Distribution, Skill Demand.

## 5. Security & Authentication Controls
- BCrypt password hashing & verification in `backend/app/core/security.py`.
- Server-side JTI token blocklisting for revoked tokens.
- Security headers middleware and CORS origins restriction.
- Rate limiting on `/login` and `/upload` endpoints via `slowapi`.

## 6. Dual User Interfaces
- **Streamlit Frontend (`/frontend`)**: Fully functional HR dashboard on port 8501.
- **React + Three.js Frontend (`/frontend_react`)**: Vite React app with Three.js canvas component (`IntelligenceCore.tsx`) representing backend AI core states.
