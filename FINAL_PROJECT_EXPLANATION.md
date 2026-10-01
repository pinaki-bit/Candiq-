# FINAL PROJECT EXPLANATION — CANDIQ

## A. What is Candiq?
**Candiq** is an AI-powered candidate intelligence and recruitment platform that automates resume understanding, candidate classification, skill matching, semantic candidate discovery, recruiter analytics, and AI-assisted hiring workflows. Built with a production-ready FastAPI backend, SQLAlchemy ORM, scikit-learn ML pipeline, spaCy NLP PhraseMatcher, local sentence-transformers vector embeddings, and Streamlit HUD / React frontends, Candiq ensures deterministic, transparent, and auditable candidate evaluation without the hallucination and black-box limitations of conventional ATS software.

---

## B. Problem Statement
Traditional Applicant Tracking Systems (ATS) and manual resume screening workflows suffer from four major flaws:
1. **Keyword Rigidity & Blindness**: Keyword-matching ATS tools reject qualified candidates due to minor phrasing variations or synonyms, while allowing keyword-stuffed irrelevant resumes to pass.
2. **Out-of-Domain (OOD) Hallucination & Failure**: Standard ML classifiers force every upload into a predefined domain class (e.g., classifying an Accountant or Chef resume as "Web Development" with high confidence), leading to false positives and low system trust.
3. **Black-Box AI & Missing Transparency**: Most AI screening tools output opaque percentile scores without explaining why a candidate scored high or low, or which required skills were missing.
4. **Data Privacy & LLM Vulnerabilities**: Sending raw candidate PII and resumes to third-party LLMs exposes companies to privacy leaks and prompt injection attacks embedded in PDF text layers.

---

## C. Main Objectives
- **Secure PDF Extraction**: Validate PDF magic bytes (`%PDF`), size limits (10MB), and file structure; extract text securely via `pdfminer.six` with ligature normalization and optional Tesseract OCR fallback.
- **Calibrated ML Domain Classification**: Train and serve a Calibrated `LinearSVC` model (Platt Sigmoids, 5-fold cross-validation) across 5 primary technical domains (Cloud Computing, Cybersecurity, Data Science, DevOps, Web Development) achieving **97.84% test accuracy** and **0.981 macro F1**.
- **OOD Abstention Guardrail**: Implement a non-destructive Out-of-Domain policy engine frozen at **Phase 24 OP-4 threshold (0.85)** that routes low-confidence predictions to a mandatory "Needs Manual Review" state rather than misclassifying them.
- **Transparent Skill Extraction & Matching**: Extract canonical skills using spaCy `PhraseMatcher` against a 5-domain taxonomy with evidence snippets; calculate transparent skill coverage (Required 70% / Preferred 30%).
- **6-Signal Hybrid Ranking**: Rank candidates using 6 weighted signals: Required Skill Coverage (35%), Preferred Skill Coverage (15%), Semantic Similarity (25% via `all-MiniLM-L6-v2`), Lexical Jaccard Overlap (10%), Experience Depth (10%), and Domain Alignment (5%), guaranteeing semantic scores never conceal missing required skills.
- **Enterprise Security & Observability**: Enforce OAuth2/JWT authentication, RBAC (`admin`, `recruiter`, `reviewer`), multi-tenant isolation (`tenant_id`), prompt injection defense (`DATA_BOUNDARY` tags), audit logging, rate limiting, and request correlation (`X-Request-ID`).

---

## D. Complete Architecture
```
                                 ┌──────────────────────────────────────────┐
                                 │          User (Recruiter / Admin)         │
                                 └────────────────────┬─────────────────────┘
                                                      │ HTTP / REST / WebSockets
                                                      ▼
                                 ┌──────────────────────────────────────────┐
                                 │     Streamlit HUD / React Frontend UI    │
                                 └────────────────────┬─────────────────────┘
                                                      │ JWT Auth Header
                                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       FastAPI v0.3.0 Application                                       │
│                                                                                                        │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────┐                     │
│  │ Security & Middleware │   │    Auth & Security    │   │  Rate Limiting        │                     │
│  │ X-Request-ID, CSP,    │   │ OAuth2 / JWT (HS256) │   │ SlowAPI               │                     │
│  │ CORS, Nosniff, HSTS   │   │ Password Hashing      │   │ Login: 10/min         │                     │
│  └───────────────────────┘   └───────────────────────┘   │ Upload: 20/min        │                     │
│                                                          └───────────────────────┘                     │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                  v1 REST & WebSocket Routers                                     │  │
│  │  /api/v1/auth    /api/v1/jobs    /api/v1/resumes      /api/v1/screening   /api/v1/discovery    │  │
│  │  /api/v1/admin   /api/v1/analytics /api/v1/ats        /api/v1/ai          /api/v1/resume-builder │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────────────────────┘  │
│                                     │                                                                  │
│  ┌──────────────────────────────────▼───────────────────────────────────────────────────────────────┐  │
│  │                                    Core Service Pipeline Layer                                   │  │
│  │                                                                                                  │  │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐          │  │
│  │  │   PDF & Text Service    │  │     NLP Skill Service   │  │   Classification Engine │          │  │
│  │  │ Magic Check, pdfminer,  │  │ spaCy PhraseMatcher     │  │ Calibrated LinearSVC    │          │  │
│  │  │ Ligature Normalization  │  │ Entity Recognition      │  │ TF-IDF (1,1) 50k       │          │  │
│  │  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘          │  │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐          │  │
│  │  │  OOD Abstention Policy  │  │   Embedding Service     │  │  6-Signal Hybrid Ranker │          │  │
│  │  │ Threshold >= 0.85 (OP-4) │  │ all-MiniLM-L6-v2 (384d) │  │ Skill+Sem+Lex+Exp+Dom   │          │  │
│  │  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘          │  │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐          │  │
│  │  │  AI / LLM Architecture  │  │  Candidate Discovery    │  │  Resume Builder Service │          │  │
│  │  │ Mock / OpenAI / Gemini  │  │ Semantic Multi-Filter   │  │ ATS Real-time Optimizer │          │  │
│  │  └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘          │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┼──────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       SQLAlchemy 2.x Database Engine             │
             │   SQLite WAL Mode (Dev) / PostgreSQL (Prod)      │
             │                                                  │
             │  • Users              • ScreeningResults         │
             │  • Jobs & Requirements│  • ModelVersions         │
             │  • Candidates         │  • AuditEvents & Tokens  │
             │  • Resumes & Skills   │  • ResumeDrafts/Versions │
             └──────────────────────────────────────────────────┘
```

---

## E. End-to-End Workflow
1. **Upload & Security Sanitization**: User uploads a resume PDF via UI. The backend validates extension (`.pdf`), magic bytes (`%PDF`), max file size (10MB), and checks for path traversal. The file is saved under a UUID filename.
2. **Text Extraction**: `pdfminer.six` extracts text, normalizes ligatures (e.g., `\ufb01` -> `fi`), and strips invalid whitespace. If raw text is empty/short, optional Tesseract OCR fallback is attempted.
3. **NLP Skill Extraction**: spaCy PhraseMatcher identifies canonical skills from `shared/skill_taxonomy.json` using case-insensitive matching (`attr="LOWER"`), outputting matched text, domain, category, frequency, and 200-character evidence snippets.
4. **ML Domain Classification & OOD Check**: Text is vectorized using TF-IDF (1,1 unigrams, max 50k features) and passed to Calibrated LinearSVC. If `top_probability < 0.85`, the OOD engine flags the candidate as `possible_out_of_domain` (`review_required=True`).
5. **Database Persistence**: Candidate record, extracted skills, and screening results are persisted atomically with `tenant_id` scoping.
6. **Job Matching & 6-Signal Ranking**: Candidate's profile is scored against job requirements using the 6-signal hybrid ranker (Skill Coverage, Semantic Similarity via `MiniLM-L6-v2`, Lexical Jaccard, Experience Depth, Domain Alignment).
7. **Recruiter Intelligence & AI Assistance**: Recruiter views ranked candidates, inspects score breakdowns, triggers AI explanation summaries, generates tailored 5-question interview kits, or exports analytics reports.

---

## F. Frontend Architecture
- **Framework**: Streamlit layout (`frontend/app.py`) with theme injection (`frontend/styles/theme.py`) providing a HUD dark-mode design system. (An alternative Vite + React SPA exists in `frontend_react`).
- **Session Management**: `st.session_state` manages JWT access tokens, active user profile, tenant context, selected job/candidate IDs, and page router navigation.
- **View Modules**:
  - `views/login.py`: Authentication page.
  - `views/dashboard.py`: Recruiter metrics summary, recent uploads, active jobs.
  - `views/jobs.py`: Job creation, requirements definition with skill weights (required/preferred).
  - `views/upload.py`: Batch drag-and-drop resume PDF processor with live status.
  - `views/results.py`: Interactive candidate screening table, OOD badges, score breakdowns, candidate status updates (`shortlisted`, `rejected`).
  - `views/candidate_discovery.py`: Semantic talent pool search, skill filters, candidate side-by-side comparison.
  - `views/resume_builder.py`: ATS resume creator, version history snapshot/restore, real-time score optimization.
  - `views/analytics.py`: Domain distribution, skill gap analysis, confidence histograms, CSV/JSON exports.
  - `views/system_health.py`: Live server CPU/memory, database connectivity, request correlation metrics.
  - `views/admin.py` & `views/audit_logs.py`: User management, RBAC role assignment, security audit trail.

---

## G. Backend Architecture
- **Framework**: FastAPI v0.3.0 in `backend/app/main.py` using factory pattern `create_app()`.
- **API Routing**: Clean modularization under `backend/app/api/v1/` (`auth.py`, `jobs.py`, `resumes.py`, `screening.py`, `admin.py`, `analytics.py`, `discovery.py`, `ai.py`, `resume_builder.py`, `ats.py`, `extension.py`).
- **Middleware Chain**:
  1. Security headers middleware (`nosniff`, `DENY` frame-options, `CSP`, `HSTS` in prod).
  2. Request correlation and latency middleware (`X-Request-ID`, execution duration logging via `metrics_collector`).
  3. Restricted CORS middleware (explicit origins, methods `GET, POST, PUT, PATCH, DELETE, OPTIONS`, allowed headers).
  4. Global structured exception handler (returns JSON standard format with request ID, error code, timestamp).
  5. SlowAPI rate limiter (`10/min` login, `20/min` upload, `200/min` default).
- **Real-Time WebSockets**: `/ws/pipeline` endpoint managed by `WebSocketManager` for real-time background screening event broadcasting.

---

## H. Database Architecture
- **ORM & Engine**: SQLAlchemy 2.x in `backend/app/database.py` with thread-safe session generator `get_db()`.
- **Database Support**: SQLite in WAL mode (`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`) for low-latency development; zero-code migration path to PostgreSQL for production via `DATABASE_URL`.
- **Core Entities (`backend/app/models/`)**:
  - `User`: Email, password hash, role (`admin`, `recruiter`, `reviewer`), `tenant_id`, `must_change_password`.
  - `Job` & `JobRequirement`: Job postings and requirement tuples (`skill_name`, `is_required`, `weight`).
  - `Candidate`: Email, full name, phone, links, location, candidate status, `tenant_id`.
  - `Resume`: Stored file path, raw text, character count, page count, upload status.
  - `ExtractedSkill`: Skill matches (`canonical_name`, `matched_text`, `domain`, `category`, `evidence_snippet`, `frequency`).
  - `ScreeningResult`: Domain prediction, top probability, all probabilities, OOD status, review required flag, required coverage, preferred coverage, composite match score, breakdown JSON.
  - `ModelVersion`: Registry of trained ML artifacts (`version_tag`, `artifact_filename`, `is_active`, test metrics).
  - `AuditEvent`: Security log (`user_id`, `event_type`, `resource_type`, `details`, `ip_address`).
  - `TokenBlocklist`: Revoked JWT JTI list for secure logout.
  - `ResumeDraft` & `ResumeVersion`: Resume builder data structures with version history snapshots.

---

## I. PDF Processing Pipeline
Implemented in `backend/app/services/pdf_service.py`:
1. **Pre-validation (`validate_upload`)**:
   - Extension check (must be `.pdf`).
   - Magic bytes check (first 4 bytes must equal `b"%PDF"`).
   - Max file size (10MB default).
   - Filename sanitization (rejects path traversal `..`, `/`, `\`).
2. **Storage**: File written to `uploads/` directory with a UUID name (`uuid4().hex + ".pdf"`).
3. **Text Extraction (`extract_text_from_path`)**:
   - Uses `pdfminer.high_level.extract_text` to extract text streams.
   - Extracts page count via `pdfminer.high_level.extract_pages`.
   - Normalizes ligatures (`\ufb01` -> `fi`, `\ufb02` -> `fl`, `\u2013` -> `-`).
   - Collapses excessive whitespace while preserving paragraph structure.
4. **Fallback OCR**: If extracted text is under 50 characters, checks for `pytesseract` and `pdf2image` to perform OCR on image-based PDFs. If OCR is absent, returns descriptive `No text could be extracted` error.

---

## J. NLP Pipeline
Implemented in `backend/app/services/nlp_service.py`:
- **spaCy Model**: Loads `en_core_web_sm` (or `en_core_web_lg`) once at startup using `@lru_cache`.
- **Named Entity Recognition (NER)**: Extracts `ORG`/`COMPANY` (organizations) and `DATE`/`TIME` entities.
- **Token Stream Normalization**: Tokenizes resume text, removes stop words, punctuation, spaces, and computes lowercased lemmatized token stream.
- **Structured Section Parser**: Uses regular expressions to extract major sections (`WORK EXPERIENCE`, `EDUCATION`, `CERTIFICATIONS`).

---

## K. ML Classification Pipeline
Implemented in `ml/src/train.py` & `backend/app/services/classification_service.py`:
- **Model Architecture**: `CalibratedClassifierCV(estimator=LinearSVC(C=0.1, class_weight="balanced"), method="sigmoid", cv=5)`.
- **Feature Extraction**: Word-level TF-IDF Vectorizer (unigrams `1,1`, `min_df=2`, `max_features=50,000`).
- **Target Categories (5 Domains)**: `Cloud Computing`, `Cybersecurity`, `Data Science`, `DevOps`, `Web Development`.
- **Validated Metrics**:
  - Training Samples: 1,570 | Test Samples: 278
  - **Test Accuracy**: 0.9784 (97.84%)
  - **Macro F1 Score**: 0.9810
  - **Weighted F1 Score**: 0.9784
  - **Cloud Computing Recall**: 1.0000
- **Model Verification & Integrity**:
  - SHA-256 hash computed before loading.
  - Verification against `.sha256` sidecar file to detect tampering.
  - Fallback to `model_latest.joblib` or safe `MODEL_UNAVAILABLE` error state if artifact missing.

---

## L. Out-Of-Domain (OOD) Detection Engine
Implemented in `backend/app/services/ood_policy.py`:
- **Operating Point**: Phase 24 OP-4 confidence threshold frozen at **`0.85`** (achieves 91.01% test coverage and 96.85% OOD developer/finance rejection).
- **Policy Decision Matrix**:
  - If `top_probability >= 0.85`: `status="accepted"`, `ood_status="in_domain_like"`, `review_required=False`.
  - If `top_probability < 0.85`: `status="review"`, `ood_status="possible_out_of_domain"`, `review_required=True`.
- **Abstention Principle**: OOD detection is non-destructive. A low confidence score indicates **"Needs Manual Review"**, NEVER automatic candidate rejection.

---

## M. Skill Extraction Pipeline
Implemented in `backend/app/services/skill_service.py`:
- **Mechanism**: spaCy `PhraseMatcher` configured with `attr="LOWER"` for case-insensitive exact matching.
- **Taxonomy Source**: `shared/skill_taxonomy.json` containing hierarchical domain-category-skill mappings and alias arrays.
- **Deduplication & Snippet Extraction**: Matches are aggregated by canonical skill name, frequency is tracked, and a 200-character evidence snippet surrounding the match context is saved.

---

## N. Job Matching Engine
Implemented in `backend/app/services/matching_service.py`:
- **Formula**:
  $$\text{Required Coverage (\%)} = \frac{\sum \text{weight of matched required skills}}{\sum \text{weight of all required skills}} \times 100$$
  $$\text{Preferred Coverage (\%)} = \frac{\sum \text{weight of matched preferred skills}}{\sum \text{weight of all preferred skills}} \times 100$$
  $$\text{Combined Match} = \frac{0.70 \times \text{Required Coverage} + 0.30 \times \text{Preferred Coverage}}{0.70 + 0.30}$$
- **Transparency**: Returns matched required skills, missing required skills, matched preferred skills, and evidence snippets for every matched skill.

---

## O. 6-Signal Hybrid Candidate Ranking
Implemented in `backend/app/services/matching_service.py` (`compute_hybrid_match`):
- **Signals & Weights**:
  1. **Required Skill Coverage (35%)**: Direct matching against required job skills.
  2. **Preferred Skill Coverage (15%)**: Direct matching against preferred job skills.
  3. **Semantic Similarity (25%)**: Vector cosine distance between resume and job description.
  4. **Lexical Similarity (10%)**: Jaccard token overlap score.
  5. **Experience / Depth Relevance (10%)**: Dynamic function of skill density and document length.
  6. **Domain Alignment (5%)**: Match bonus between classifier predicted domain and job domain.
- **Strict Invariant**: High semantic similarity or domain alignment **NEVER** hides missing required skills or inflates missing skill coverage.

---

## P. Semantic Embeddings Engine
Implemented in `backend/app/services/embedding_service.py`:
- **Primary Provider**: `SentenceTransformerEmbeddingProvider` using `sentence-transformers/all-MiniLM-L6-v2` producing **384-dimensional dense L2-normalized vectors**.
- **Fallback Providers**:
  - `LocalEmbeddingProvider`: 128-dim MD5 feature hashing vectorizer for zero-dependency execution.
  - `OpenAIEmbeddingProvider`: `text-embedding-3-small` via httpx REST client.
- **Cosine Similarity**: Vector dot product normalized by L2 norms, clamped to $[0.0, 1.0]$.

---

## Q. Candidate Discovery System
Implemented in `backend/app/services/discovery_service.py`:
- Multi-parameter candidate search across the organization pool.
- Filter by domain, required skills array, minimum hybrid score, and OOD status.
- Candidate comparison engine providing side-by-side skill matrix and score breakdown.
- Multi-tenant tenant isolation enforced across all discovery queries.

---

## R. Recruiter Workflow & Candidate Management
Implemented in `backend/app/api/v1/screening.py` & `views/results.py`:
- Single and batch resume screening triggers.
- Candidate lifecycle status transitions: `pending_review` -> `reviewed` -> `shortlisted` -> `rejected`.
- Re-screening and manual override capabilities for review-required OOD candidates.
- Security audit event logged for every candidate status change.

---

## S. Analytics Engine
Implemented in `backend/app/api/v1/analytics.py`:
- **Metrics Calculated**: Total candidates, total jobs, screening throughput, domain distribution percentage, skill demand vs supply gap matrix, confidence level distribution, average match scores per job.
- **Exporting**: Instant CSV and JSON report exports for compliance and hiring metrics analysis.

---

## T. LLM Intelligence & AI Architecture
Implemented in `backend/app/services/ai_service.py`:
- **Provider Facade (`AIService`)**: Abstract interface supporting `MockAIProvider` (offline/dev), `OpenAIProvider` (`gpt-4o-mini`), and `GeminiProvider` (`gemini-1.5-flash`).
- **Prompt Injection Defense**: Untrusted external text wrapped in `<<<DATA_BOUNDARY_START>>>` and `<<<DATA_BOUNDARY_END>>>` markers with explicit system instructions to treat content strictly as data.
- **PII Redaction**: `sanitize_pii` redacts emails, phone numbers, and SSNs before sending data to external APIs.
- **Anti-Hallucination Guardrails**: `STRICT_FACTUAL_GUARDRAIL` enforces zero-invention policies; missing quantitative metrics are replaced with `[Metric Required: ...]` placeholders.
- **Cost & Token Observability**: Token estimation (`estimate_tokens`) and USD cost tracking (`calculate_cost`) logged per LLM call.

---

## U. Interactive Resume Builder
Implemented in `backend/app/services/resume_builder_service.py`:
- Interactive candidate resume creation and editing interface.
- Version history snapshotting (`ResumeVersion`) with one-click restore capabilities.
- Real-time ATS compatibility scoring engine analyzing structure, contact details, skill density, and formatting.
- AI bullet point rewriter using action verbs and quantifiable impact placeholders.

---

## V. Authentication & Role-Based Access Control (RBAC)
Implemented in `backend/app/core/security.py` & `backend/app/api/v1/auth.py`:
- **Authentication**: OAuth2 password flow issuing JSON Web Tokens (JWT) signed with `HS256` and configurable expiration (60 mins). Passwords hashed using `passlib` with bcrypt.
- **Token Revocation**: `TokenBlocklist` table tracks logged-out JWT JTI tokens.
- **RBAC Roles**:
  - `admin`: Full platform control, user management, audit log access, model version management.
  - `recruiter`: Job creation, resume upload, candidate status updates, AI tools, discovery.
  - `reviewer`: Read-only access to candidates, screening results, and analytics.

---

## W. Multi-Tenancy Architecture
- Enforced via `tenant_id` string column across `User`, `Candidate`, `Job`, and `Resume` models.
- All database queries filter by the current authenticated user's `tenant_id`.
- Prevents cross-organization data leakage in multi-organization cloud deployments.

---

## X. Platform Security
- **File Upload Security**: Extension check, `%PDF` magic byte verification, 10MB size limit, UUID file naming, non-executable storage directory.
- **Input Sanitization**: HTML tag stripping, script injection removal, regex path traversal protection.
- **Security Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy: default-src 'self'`, `Strict-Transport-Security` (production).
- **Rate Limiting**: IP and user-based throttling via SlowAPI.

---

## Y. Observability & Monitoring
Implemented in `backend/app/core/metrics.py` & `backend/app/routers/health.py`:
- Request correlation via `X-Request-ID` header attached to every HTTP request and response.
- In-memory `metrics_collector` recording request count, error count, and latency histograms.
- Health probes: `/health/liveness` (app status) and `/health/db` (SQLAlchemy connectivity check).

---

## Z. Deployment Architecture
Implemented in `docker-compose.yml` & `DEPLOYMENT_GUIDE.md`:
- **Dockerization**: Multi-stage Docker build for backend FastAPI application (`Dockerfile`) and frontend Streamlit application (`frontend/Dockerfile`).
- **Production Application Server**: Gunicorn with Uvicorn workers (`uvicorn.workers.UvicornWorker`).
- **Configuration**: Managed via `.env` file validated at startup by Pydantic v2 `BaseSettings`.
