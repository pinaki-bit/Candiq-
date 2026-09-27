# TECHNICAL DECISIONS LOG — RESUME INTEL

**Project**: Resume Intel  
**Document Version**: 1.0 (Phase 27.5 Checkpoint)  
**Date**: September 28, 2026  

---

## 1. Decision: FastAPI Backend Framework

### Problem
The application requires a modern, high-performance Python backend API capable of handling synchronous PDF parsing, asynchronous WebSocket event broadcasting, automatic JSON schema validation, and automatic OpenAPI documentation.

### Decision
Use **FastAPI** paired with **Uvicorn** (ASGI server) and Pydantic v2 schemas.

### Why
FastAPI provides native asynchronous I/O support, automatic OpenAPI/Swagger documentation generation, strict data validation via Pydantic, and fast execution speeds comparable to NodeJS/Go.

### Alternatives
- **Flask**: Lacks native async, automatic Pydantic validation, and automatic Swagger docs out of the box.
- **Django REST Framework (DRF)**: Heavy monolithic ORM and framework overhead; less optimal for lightweight microservice ML serving.

### Trade-offs
- Requires Python 3.10+ async syntax and Pydantic v2 type annotations.

### Current Status
**Implemented and Verified**. Backend API fully operational under `backend/app/main.py`.

---

## 2. Decision: Scikit-Learn LinearSVC Classifier with TF-IDF Vectorization

### Problem
The system needs to categorize candidate resume text into five target tech domains (`Data Science`, `Web Development`, `Cloud Computing`, `DevOps`, `Cybersecurity`) efficiently without requiring massive GPU inference hardware.

### Decision
Use a **TF-IDF Vectorizer** (1-3 word n-grams) combined with a **Linear Support Vector Classifier (LinearSVC)**.

### Why
TF-IDF + LinearSVC offers fast training and inference latency ($< 20$ ms), strong linear class separability on keyword-dense resume corpora, and minimal RAM footprint.

### Alternatives
- **Fine-tuned Transformer (BERT / RoBERTa)**: High computational cost, expensive GPU inference requirements, and slower processing latency (~500ms per text snippet).
- **Naive Bayes**: Fast but suffers under strong feature dependencies (correlated technical skills).

### Trade-offs
- Relies on surface lexical n-grams rather than deep semantic contextual embeddings.

### Current Status
**Implemented and Verified**. Active model `model_latest.joblib` and candidate `model_v2.joblib` stored in `ml/artifacts/`.

---

## 3. Decision: Non-Destructive OOD / Abstention Policy Layer

### Problem
Closed-world multi-class classifiers assign high pseudo-confidence to out-of-domain (OOD) resumes (e.g. accounting, legal, medical), risking erroneous automatic classification.

### Decision
Implement an explicit, non-destructive **OOD Policy Engine** (`app.services.ood_policy`) using a frozen Phase 24 confidence threshold ($\tau = 0.85$). When confidence falls below 0.85, the system assigns `status: "review"`, `review_required: True`, and `ood_status: "possible_out_of_domain"`.

### Why
Automatic candidate rejection based on classifier uncertainty is ethically and operationally unacceptable. Flagging low-confidence predictions for human recruiter review protects candidates while alerting recruiters to edge cases.

### Alternatives
- **Automatic Candidate Rejection**: High risk of rejecting qualified candidates due to model miscalibration.
- **Training a Secondary Binary Isolation Forest**: Requires additional synthetic OOD training data and introduces meta-model drift.

### Trade-offs
- Resumes with confidence $< 0.85$ require human recruiter intervention.

### Current Status
**Implemented and Verified** (Phases 25–27).

---

## 4. Decision: spaCy PhraseMatcher for Deterministic Skill Extraction

### Problem
Extracting technical skills from raw resume text requires high precision, standard canonical normalization, and zero hallucination.

### Decision
Use **spaCy `en_core_web_sm` PhraseMatcher** matched against a curated taxonomy (`shared/skill_taxonomy.json`).

### Why
PhraseMatcher is deterministic, extremely fast ($< 110$ ms), supports exact multi-word phrase matching (e.g. "Google Cloud Platform", "React Native"), and produces verifiable evidence snippets without LLM hallucination risks.

### Alternatives
- **LLM-only Skill Extraction**: Slower, expensive token costs, and potential for hallucinating skills not present in the source text.
- **Regex Keyword Matching**: Fragile, un-normalized, and prone to false positives (e.g. matching "Go" inside "Good").

### Trade-offs
- Skills not present in `shared/skill_taxonomy.json` will not be automatically recognized.

### Current Status
**Implemented and Verified**.

---

## 5. Decision: SQLite Database with SQLAlchemy 2.0 ORM

### Problem
The project requires a simple, zero-configuration local relational database for development, unit testing, and demonstration.

### Decision
Use **SQLite** with **SQLAlchemy 2.0 ORM** (`Mapped` and `mapped_column` type annotations).

### Why
SQLite requires no separate database daemon, operates as a single file (`resume_screening.db`), supports in-memory testing (`sqlite:///:memory:`), and integrates seamlessly with SQLAlchemy.

### Alternatives
- **PostgreSQL**: Production-grade relational DB, but adds external container/daemon dependency during local setup.

### Trade-offs
- SQLite does not support high concurrency writes in multi-node distributed environments without WAL mode or PostgreSQL migration.

### Current Status
**Implemented and Verified**.

---

## 6. Decision: Model Artifact SHA-256 Hash Verification

### Problem
ML model artifacts (`.joblib` files) loaded via `joblib.load()` present security risks if tampered with or corrupted on disk.

### Decision
Compute SHA-256 hash at startup in `_load_model()` and compare against a sidecar `.sha256` checksum file (`model_latest.joblib.sha256`).

### Why
Guarantees artifact integrity, prevents loading tampered model files, and logs an auditable hash signature on application startup.

### Alternatives
- **Unverified File Load**: Fast, but vulnerable to silent file corruption or unauthorized artifact modification.

### Trade-offs
- Requires updating the `.sha256` sidecar file whenever a model is promoted.

### Current Status
**Implemented and Verified**.

---

## 7. Decision: Two-Stage Model Promotion (model_latest vs model_v2)

### Problem
Candidate models (`model_v2.joblib`) must be rigorously audited and validated across external datasets and OOD tests before replacing active production artifacts.

### Decision
Keep `model_latest.joblib` as the active production model while preserving `model_v2.joblib` as an offline candidate under audit.

### Why
Prevents un-audited candidate models from altering live production API behavior until explicit product owner sign-off and promotion approval.

### Alternatives
- **Immediate In-Place Overwrite**: High risk of silent regressions on live endpoints.

### Trade-offs
- System maintains two model files in `ml/artifacts/`.

### Current Status
**Implemented and Verified**. `model_latest.joblib` remains active production model; `model_v2.joblib` remains candidate.

---

## 8. Decision: Mock AI Provider Fallback

### Problem
LLM features (bullet rewriter, cover letter generator, interview kits) require API keys (OpenAI / Gemini) which may not be available during local development or offline evaluation.

### Decision
Implement `MockAIProvider` (`backend/app/services/ai_service.py`) as the default fallback when external API keys are missing.

### Why
Ensures all API endpoints return valid, schema-compliant responses without failing or throwing 500 errors when external cloud services are offline or unconfigured.

### Alternatives
- **Throwing HTTP 503 Errors**: Breaks UI workflows when API keys are un-configured.

### Trade-offs
- Mock provider returns structured template responses rather than real generative LLM text.

### Current Status
**Implemented and Verified**.

---

## 9. Decision: OCR Fallback Guardrails

### Problem
Image-only scanned PDFs contain zero text layer and fail standard `pdfminer.six` text extraction.

### Decision
Implement `_run_ocr_fallback()` using `pytesseract` and `pdf2image`. If Tesseract system binaries are absent, catch the failure gracefully and mark the record as `ProcessingStatus.FAILED` with a user-safe message.

### Why
Prevents API crashes, unhandled exceptions, or database corruption when users upload image-only PDFs on host systems lacking Tesseract.

### Alternatives
- **Mandatory Hard Dependency**: Crashing the server at startup if Tesseract is missing.

### Trade-offs
- Image-only PDF extraction requires host OS Tesseract binary installation (`tesseract-ocr`).

### Current Status
**Implemented and Verified** (Phase 27).
