# RESUME INTEL — SYSTEM ARCHITECTURE SPECIFICATION

**Project**: Resume Intel  
**Document Version**: 1.0 (Phase 27.5 Checkpoint)  
**Date**: September 28, 2026  

---

## 1. HIGH-LEVEL SYSTEM ARCHITECTURE

Resume Intel is built on a decoupled, modular service-oriented architecture designed to separate HTTP API handling, Natural Language Processing (NLP), Machine Learning (ML) inference, Out-Of-Domain (OOD) policy evaluation, and frontend UI presentation.

```mermaid
flowchart TD
    subgraph Client Layer
        UI["Streamlit Frontend (frontend/app.py)"]
        EXT["Chrome Extension (browser_extension/)"]
    end

    subgraph API & Security Layer
        API["FastAPI Backend (app.main:app)"]
        AUTH["JWT Auth & Security (app.core.security)"]
        RATELIMIT["Rate Limiter (app.rate_limiter)"]
        CORS["CORS & Security Headers (app.main)"]
    end

    subgraph Core Processing Pipeline
        PROC["Processing Pipeline (_run_processing_pipeline)"]
        PDF["PDF Extraction (app.services.pdf_service)"]
        OCR["OCR Fallback (pytesseract / pdf2image)"]
        NLP["NLP Skill Matching (app.services.skill_service)"]
        ML["ML Classification (app.services.classification_service)"]
        OOD["OOD Policy Engine (app.services.ood_policy)"]
    end

    subgraph Screening & Service Layer
        MATCH["Job Matching (app.services.matching_service)"]
        RANK["Hybrid Ranking (app.services.ranking_service)"]
        EMBED["Embeddings Engine (app.services.embedding_service)"]
        LLM["AI Service (app.services.ai_service)"]
        WS["WebSocket Manager (app.services.websocket_manager)"]
    end

    subgraph Data & Storage Layer
        DB[("SQLite Database (resume_screening.db)")]
        DISK["Local Storage (uploads/)"]
        MODELS["Model Artifacts (ml/artifacts/)"]
    end

    UI -->|HTTP / JSON| API
    EXT -->|HTTP / JSON| API
    UI <-->|WebSocket Events| WS
    API --> AUTH
    API --> RATELIMIT
    API --> CORS
    API --> PROC
    API --> MATCH
    API --> RANK

    PROC --> PDF
    PDF -->|If Image-Only| OCR
    PROC --> NLP
    PROC --> ML
    ML --> MODELS
    ML --> OOD
    PROC --> DB
    PROC --> DISK
    PROC --> WS

    MATCH --> DB
    MATCH --> EMBED
    LLM --> API
```

---

## 2. RESUME PROCESSING SEQUENCE

The sequence below illustrates the step-by-step processing of a PDF resume upload through the application:

```mermaid
sequenceDiagram
    autonumber
    actor User as HR Recruiter
    participant UI as Streamlit UI
    participant API as FastAPI Router (/upload)
    participant PDF as PDF Service
    participant NLP as spaCy NLP Engine
    participant ML as ML Classifier
    participant OOD as OOD Policy Engine
    participant DB as SQLite DB
    participant WS as WebSocket Manager

    User->>UI: Upload PDF Resume
    UI->>API: POST /api/v1/resumes/upload (JWT)
    API->>API: Validate Auth & Rate Limits
    API->>PDF: validate_upload(filename, content, mime)
    API->>PDF: save_upload() -> uploads/uuid.pdf
    API->>DB: Create Resume record (status=UPLOADED)
    
    API->>WS: Broadcast event: resume.uploaded
    API->>PDF: extract_text_from_path()
    alt Text-based PDF
        PDF-->>API: Extracted Text (pdfminer)
    else Image-only PDF
        PDF->>PDF: _run_ocr_fallback()
        alt Tesseract Binary Present
            PDF-->>API: OCR Extracted Text
        else Binary Missing
            PDF-->>API: Extraction Error (status=FAILED)
        end
    end

    API->>NLP: match_skills(extracted_text)
    NLP-->>API: ExtractedSkill list
    API->>DB: Persist ExtractedSkills

    API->>ML: predict(extracted_text)
    ML->>ML: Run Pipeline (predict_proba / decision_function)
    ML->>OOD: evaluate_ood_policy(predicted_class, top_prob)
    OOD-->>ML: OODDecision (status, ood_status, review_required, version, reason)
    ML-->>API: ClassificationResult

    API->>DB: Update Resume record (predicted_domain, classification_status, ood_status, review_required, status)
    API->>WS: Broadcast event: pipeline.completed
    API-->>UI: ResumeDetailRead JSON Response
    UI-->>User: Display Results & Status Badge
```

---

## 3. MACHINE LEARNING INFERENCE & CALIBRATION PIPELINE

The ML inference subsystem operates independently from model training:

```mermaid
flowchart LR
    subgraph Inputs
        TXT["Clean Extracted Resume Text"]
    end

    subgraph Model Loading & Integrity
        PATH["active_model_path (config.py)"]
        SHA["SHA-256 Hash Verification"]
        CACHE["LRU Cache (_load_model)"]
    end

    subgraph Pipeline Execution
        TFIDF["TF-IDF Vectorizer (1-3 n-grams)"]
        CLF["LinearSVC Classifier"]
        CALIB["CalibratedClassifierCV (Platt Scaling)"]
    end

    subgraph Signals & OOD Policy
        PROB["Class Probability Distribution P(Y=k|X)"]
        TOP["Max Probability S_conf = max P(Y=k|X)"]
        POL["OOD Policy Engine (τ = 0.85)"]
        DEC{"S_conf ≥ 0.85?"}
    end

    subgraph Outputs
        ACCEPT["status = accepted<br/>ood_status = in_domain_like<br/>review_required = False"]
        REVIEW["status = review<br/>ood_status = possible_out_of_domain<br/>review_required = True"]
    end

    TXT --> CACHE
    PATH --> SHA --> CACHE
    CACHE --> TFIDF
    TFIDF --> CLF
    CLF --> CALIB
    CALIB --> PROB
    PROB --> TOP
    TOP --> POL
    POL --> DEC
    DEC -->|Yes| ACCEPT
    DEC -->|No| REVIEW
```

---

## 4. OOD / ABSTENTION DECISION FLOW

The OOD abstention policy enforces a strict non-destructive rule: **Abstention means "Needs Manual Review", NOT "Candidate Rejected"**.

```mermaid
flowchart TD
    START["Classification Output: predicted_class, top_prob"] --> CHK_ENA{"ood_enabled?"}
    
    CHK_ENA -->|False| ACC_DIS["status = accepted<br/>ood_status = in_domain_like<br/>review_required = False<br/>reason = ood_policy_disabled"]
    CHK_ENA -->|True| CHK_NULL{"predicted_class is None OR top_prob is None?"}
    
    CHK_NULL -->|True| REV_EMPTY["status = review<br/>ood_status = possible_out_of_domain<br/>review_required = True<br/>reason = input_empty_or_model_unavailable"]
    CHK_NULL -->|False| CHK_TAU{"top_prob ≥ 0.85?"}
    
    CHK_TAU -->|Yes| ACC_NORM["status = accepted<br/>ood_status = in_domain_like<br/>review_required = False<br/>reason = confidence_above_configured_threshold"]
    CHK_TAU -->|No| REV_LOW["status = review<br/>ood_status = possible_out_of_domain<br/>review_required = True<br/>reason = confidence_below_configured_threshold"]
    
    ACC_NORM --> DB["Persist to DB & Return API Response"]
    ACC_DIS --> DB
    REV_EMPTY --> DB
    REV_LOW --> DB
```

---

## 5. AUTHENTICATION & RBAC FLOW

Request security is enforced using JWT Bearer authentication and role-based access boundaries:

```mermaid
flowchart TD
    REQ["HTTP Request"] --> HEADER["Authorization Header (Bearer JWT)"]
    HEADER --> DEC["Decode & Validate JWT (app.core.security)"]
    DEC -->|Invalid / Expired| ERR401["HTTP 401 Unauthorized"]
    DEC -->|Valid| ROLE["Extract User Role (admin | hr | readonly)"]
    
    ROLE --> ROUTE{"Target Endpoint Permission"}
    
    ROUTE -->|Admin Only (/admin/*)| CHK_ADM{"role == admin?"}
    CHK_ADM -->|Yes| OK["Execute Route Handler"]
    CHK_ADM -->|No| ERR403["HTTP 403 Forbidden"]
    
    ROUTE -->|HR & Admin (/resumes/upload)| CHK_HR{"role in (hr, admin)?"}
    CHK_HR -->|Yes| OK
    CHK_HR -->|No| ERR403
    
    ROUTE -->|Authenticated View (/resumes/{id})| OK
```

---

## 6. DATABASE RELATIONSHIP DIAGRAM (ERD)

The database schema manages candidates, resumes, extracted skills, job requisitions, screening matches, and audit logs:

```mermaid
erDiagram
    USERS ||--o{ RESUMES : "uploaded_by"
    USERS ||--o{ AUDIT_EVENTS : "actor"
    CANDIDATES ||--o{ RESUMES : "owns"
    RESUMES ||--o{ EXTRACTED_SKILLS : "contains"
    RESUMES ||--o{ SCREENING_RESULTS : "screened_in"
    JOBS ||--o{ SCREENING_RESULTS : "evaluates"
    MODEL_VERSIONS ||--o{ RESUMES : "classified_by"

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role
        boolean is_active
        boolean is_admin
        boolean must_change_password
    }

    CANDIDATES {
        int id PK
        string reference_code UK
        string full_name
        string email
        string phone
    }

    RESUMES {
        int id PK
        string public_id UK
        int candidate_id FK
        string original_filename
        string stored_filename UK
        int file_size_bytes
        string mime_type
        int page_count
        string status
        string error_message
        text extracted_text
        int text_char_count
        string predicted_domain
        string prediction_confidence
        string classification_status
        boolean review_required
        string ood_status
        string policy_version
        string policy_reason
        int uploaded_by FK
        datetime uploaded_at
        datetime processed_at
    }

    EXTRACTED_SKILLS {
        int id PK
        int resume_id FK
        string canonical_name
        string matched_text
        string domain
        string category
        string evidence_snippet
        string extraction_method
        int frequency
    }

    JOBS {
        int id PK
        string public_id UK
        string title
        text description
        string domain
        text required_skills_json
        text preferred_skills_json
        int min_experience_years
        string status
        int created_by FK
    }

    SCREENING_RESULTS {
        int id PK
        string public_id UK
        int job_id FK
        int resume_id FK
        float relevance_score
        float required_skill_coverage
        float preferred_skill_coverage
        string tier
        string review_status
        text reviewer_notes
    }

    AUDIT_EVENTS {
        int id PK
        int actor_id FK
        string actor_email
        string resume_public_id
        string action
        string ip_address
        datetime timestamp
    }

    MODEL_VERSIONS {
        int id PK
        string version_tag UK
        string artifact_filename
        float test_accuracy
        float test_macro_f1
        boolean is_active
    }
```

---

## 7. COMPONENT SPECIFICATIONS

### 7.1 Backend Services Directory (`backend/app/services/`)
- `pdf_service.py`: PDF validation (extension, size, magic bytes), storage under UUID name, text extraction via `pdfminer.six`, and OCR fallback via `pytesseract`.
- `skill_service.py`: NLP skill extraction using spaCy `en_core_web_sm` PhraseMatcher against `shared/skill_taxonomy.json`.
- `classification_service.py`: LRU-cached model loading, SHA-256 sidecar integrity verification, classifier prediction execution (`predict`), and OOD policy integration.
- `ood_policy.py`: Non-destructive abstention decision engine ($\tau = 0.85$, policy `v1.0-phase24-op4`).
- `matching_service.py`: Multi-factor deterministic candidate-job skill coverage and domain bonus score calculation.
- `ranking_service.py`: Hybrid candidate ranking combining skill match score, domain alignment, and ATS compatibility.
- `embedding_service.py`: Hashing / TF-IDF vector similarity engine for semantic matching fallback.
- `ai_service.py`: LLM abstraction provider (`MockAIProvider`, OpenAI, Gemini) for bullet rewriting, cover letter generation, and interview kits with factual guardrails.
- `websocket_manager.py`: Async WebSocket connection manager broadcasting real-time resume processing telemetry.
