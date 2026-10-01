# PHASE 35 — AI RESUME BUILDER + LIVE ATS/JOB MATCH OPTIMIZATION

## Architecture Overview

Phase 35 introduces an interactive, real-time **AI Resume Builder & Live ATS Match Optimizer** to the Resume Screening platform. It allows candidates and recruiters to create, edit, version, and continuously optimize structured resumes against real target jobs using the production 6-signal hybrid matching engine.

```
+------------------+       +-------------------+       +------------------------+
|  Resume Editor   | ----> | Structured Draft  | ----> | 6-Signal Hybrid Match  |
| (Structured JSON)|       | (Section Compiler)|       | (Production ATS Engine)|
+------------------+       +-------------------+       +------------------------+
         |                                                         |
         v                                                         v
+------------------+                                   +------------------------+
| AI Assistant     |                                   | Live Score & Feedback  |
| (Phase 34 LLM)   |                                   | (Breakdown + Delta)    |
+------------------+                                   +------------------------+
```

---

## Database Changes (`backend/app/models/resume_builder.py`)

Added two new ORM models registered under `Base.metadata`:

1. **`ResumeDraft` (`resume_drafts` table)**:
   - `id`, `public_id` (UUID): Primary identifiers.
   - `user_id`, `tenant_id`: Owner user and tenant isolation scoping.
   - `title`: Customizable draft workspace title.
   - `target_job_id`: Foreign key link to target `Job`.
   - `structured_content_json`: JSON text containing structured sections (`personal_info`, `summary`, `skills`, `experience`, `education`, `projects`, `certifications`, `achievements`, `section_order`).
   - `raw_markdown`: Auto-compiled continuous markdown text.
   - `created_at`, `updated_at`: Timestamps.

2. **`ResumeVersion` (`resume_versions` table)**:
   - `id`, `public_id`, `draft_id`: Identifiers and foreign key to parent draft.
   - `version_number`: Auto-incrementing version integer (1, 2, ...).
   - `label`: Snapshot title (e.g. "Initial Draft", "v2_snapshot").
   - `structured_content_json`: Immutable snapshot of draft content.
   - `created_at`: Timestamp of version creation.

---

## API Endpoints (`backend/app/api/v1/resume_builder.py`)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/resume-builder` | `POST` | Create a new structured resume draft workspace |
| `/api/v1/resume-builder` | `GET` | List user's active resume drafts |
| `/api/v1/resume-builder/{id}` | `GET` | Retrieve specific resume draft workspace |
| `/api/v1/resume-builder/{id}` | `PATCH` | Update draft sections, title, or target job (Autosave/Draft Save) |
| `/api/v1/resume-builder/{id}/match` | `POST` | Calculate real-time 6-signal hybrid ATS match score & optional Before/After comparison |
| `/api/v1/resume-builder/{id}/versions` | `POST` | Save immutable snapshot version |
| `/api/v1/resume-builder/{id}/versions` | `GET` | List saved snapshot versions |
| `/api/v1/resume-builder/{id}/restore/{version_id}` | `POST` | Restore previous snapshot version into main draft |
| `/api/v1/resume-builder/{id}/export-pdf` | `GET`/`POST` | Download clean ATS-compliant PDF export generated via ReportLab |
| `/api/v1/resume-builder/{id}/ai-assist` | `POST` | Run AI assistance (Summary, Bullet Optimizer, Keywords, Review) |

---

## Real ATS/Match Calculation Integration

The live ATS match score is computed using the **EXISTING 6-signal hybrid matching engine** (`matching_service.compute_hybrid_match`). **No second scoring algorithm was created.**

### Production Hybrid Weights (Unchanged)
- **Required Skill Coverage**: 35%
- **Preferred Skill Coverage**: 15%
- **Semantic Similarity**: 25% (MiniLM-L6-v2 embeddings)
- **Lexical Token Overlap**: 10% (Jaccard token similarity)
- **Experience Depth**: 10%
- **Domain Alignment**: 5%

### Before / After Score Comparison
When `compare_version_id` is supplied, the engine runs `compute_real_ats_match` on both the previous version and current draft, returning `before_score`, `after_score`, and `score_delta` (+Z / -Z).

---

## AI Assistant & Content Labeling

Leverages the Phase 34 LLM multi-provider abstraction (`OpenAIProvider`, `GeminiProvider`, `MockAIProvider`) for:
- Professional Summary Generation
- STAR & Metric Bullet Point Optimization
- ATS Keyword Suggestions
- Resume Alignment Review & Feedback

Every AI response is restricted by strict factual system guardrails to prevent hallucinated qualifications, and carries the mandatory visual label:
> **AI Generated — Verify Before Use**

---

## PDF Export (`backend/app/services/resume_builder_service.py`)

Integrated ReportLab (`SimpleDocTemplate`, `Paragraph`, `HRFlowable`) to dynamically compile structured JSON resume data into clean, ATS-readable PDF binaries for instant download without placeholder text.

---

## Security & Tenant Isolation

- **Authentication**: All endpoints require valid JWT credentials (`AnyAuthUser`).
- **Tenant Isolation**: Drafts and Target Jobs enforce `tenant_id` verification (`verify_tenant_access`). Cross-tenant access returns `403 Forbidden` or `404 Not Found`.
- **RBAC**: Standard users can only access their own drafts; admins/recruiters can manage team workspaces.

---

## Testing & Integrity Verification

### Test Results
- **Phase 35 Test Suite (`backend/tests/test_phase35_resume_builder.py`)**: 19/19 passed.
- **Full Backend Regression Test Suite (`backend/tests`)**: 231/231 passed.

### Model & Data Hashes (Verified Unchanged)
- `model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb`
- `model_v2.joblib`: `6be329ae771bfba5a86bf1130669bdc54aac786768581ebc21e124561e6df4`
- `train.csv`: `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0`
- `val.csv`: `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6`
- `test.csv`: `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4`

### System Parameters (Verified Unchanged)
- **OOD Threshold**: $\tau = 0.85$
