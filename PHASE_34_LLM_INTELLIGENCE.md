# PHASE 34 — LLM INTELLIGENCE LAYER

## Architecture & Provider Abstraction

Phase 34 introduces a secure, production-grade LLM Intelligence Layer on top of the existing Resume Intel platform.

### Multi-Provider Architecture (`backend/app/services/ai_service.py`)

```
                 +--------------------------+
                 |    AIService (Factory)   |
                 +--------------------------+
                               |
         +---------------------+---------------------+
         |                     |                     |
+-----------------+   +------------------+   +----------------+
|  OpenAIProvider |   |  GeminiProvider  |   | MockAIProvider |
|  (gpt-4o-mini)  |   | (gemini-1.5-fl)  |   |   (Offline)    |
+-----------------+   +------------------+   +----------------+
```

### Provider Features
1. **Configurable Provider**: Configured via `LLM_PROVIDER` (`openai`, `gemini`, `mock`).
2. **API Keys via Environment**: Keys retrieved ONLY from environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`).
3. **Structured `LLMResponse`**: Standardized response container:
   - `content`: Generated text content.
   - `prompt_tokens`, `completion_tokens`, `total_tokens`: Explicit usage metrics.
   - `estimated_cost_usd`: Dynamic cost calculation based on pricing tables.
   - `provider_status`: `"success" | "provider_unavailable" | "failed"`.
   - `label`: `"AI Generated — Verify Before Use"`.
   - `guardrail_warnings`: List of flagged anti-hallucination or metric compliance issues.
4. **Graceful Degraded States**: When API keys are missing or provider APIs return errors, the provider returns `provider_status="provider_unavailable"` or `"failed"` without crashing the server or throwing uncaught exceptions.

---

## Production Endpoints (`backend/app/api/v1/ai.py`)

| Endpoint | Method | Description | Guardrails & Output |
| :--- | :--- | :--- | :--- |
| `/api/v1/ai/candidates/{id}/explanation` | `POST` | Fact-grounded candidate match explanation | Returns `summary`, `matching_reasons`, `missing_requirements`, `strengths`, `concerns`, `evidence`, `explanation`, and deterministic score |
| `/api/v1/ai/candidates/{id}/interview-questions` | `POST` | 5-category role-specific interview kit | Returns structured questions across `Technical`, `Experience`, `Problem Solving`, `Behavioral`, `Role Specific` |
| `/api/v1/ai/candidates/{id}/cover-letter` | `POST` | Tailored draft cover letter | Fact-restricted draft with mandatory editability label |
| `/api/v1/ai/resumes/{id}/rewrite-bullets` | `POST` | STAR/Metric experience bullet optimization | Optimizes bullet structure and injects metric placeholders (`[Metric Required: %...]`) without inventing experience |

---

## Security & Prompt Injection Defense (`backend/app/core/sanitizer.py`)

### 1. Data Boundary Isolation
Untrusted candidate resume text and job description content are delimited using explicit XML-style boundary tags:
```
<<<DATA_BOUNDARY_START: CANDIDATE_RESUME>>>
... untrusted candidate text ...
<<<DATA_BOUNDARY_END: CANDIDATE_RESUME>>>
```
System prompts explicitly instruct the LLM that content inside boundary tags is strictly DATA, neutralizing prompt injection attempts (e.g., "Ignore previous instructions").

### 2. PII Sanitization
Sensitive personal identifiable information (Social Security Numbers, Credit Card Numbers, 10-digit Phone Numbers) is redacted prior to sending prompts to external APIs.

### 3. Tenant & Authorization Isolation
All AI endpoints enforce tenant isolation (`verify_tenant_access`) and RBAC checks (`AnyAuthUser`). Cross-tenant candidate or resume access is strictly rejected with `403 Forbidden` or `404 Not Found`.

---

## Auditability & Cost Safety

### Event Logging (`backend/app/services/audit_service.py`)
All AI generation requests emit immutable audit events (`AuditEvent`) recording:
- Event type: `ai.candidate_explanation`, `ai.interview_questions`, `ai.cover_letter`, `ai.rewrite_bullets`
- Actor ID & Email
- Target Resource Type (`candidate` or `resume`) & Public ID
- Execution Outcome (`success` | `failure`)

### Safeguards
- **Input Truncation**: Maximum text length limits applied to prompts (`sanitize_prompt_input`).
- **Zero Fabrication**: Deterministic screening scores and OOD statuses are appended directly from database records.
- **No Secret Exposure**: API keys and raw PII are strictly excluded from log files and response bodies.

---

## Frontend Integration (`frontend/views/candidate_profile.py`)

Integrated a 4-tab interactive **🤖 AI Intelligence Assistant** into the recruiter candidate profile view:
1. **AI Match Explanation**: Summary, strengths, concerns, and factual evidence.
2. **Interview Question Generator**: 5-category interview kit with question difficulty and expected response key points.
3. **Tailored Cover Letter**: Editable draft with tone selection.
4. **Resume Bullet Point Improvement**: STAR & Metric bullet point optimizer.

Every tab renders prominent warnings:
> ⚠️ **AI Generated — Verify Before Use**

---

## Integrity & Verification

### Model & Data Hashes (Verified Unchanged)
- `model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb`
- `model_v2.joblib`: `6be329ae771bfba5a86bf1130669bdc54aac786768581ebc21e124561e6df4`
- `train.csv`: `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0`
- `val.csv`: `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6`
- `test.csv`: `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4`

### System Parameters (Verified Unchanged)
- **OOD Threshold**: $\tau = 0.85$
- **Hybrid Matching Weights**:
  - Required Skill Coverage: 35%
  - Preferred Skill Coverage: 15%
  - Semantic Similarity: 25%
  - Lexical Token Overlap: 10%
  - Experience Depth: 10%
  - Domain Alignment: 5%

### Test Results
- **Phase 34 Test Suite**: 12/12 passed (`backend/tests/test_phase34_llm.py`).
- **Full Backend Test Suite**: 212/212 passed (`backend/tests`).
