# PHASE 36 — ADVANCED CANDIDATE DISCOVERY, SEMANTIC SEARCH & HIRING INTELLIGENCE

## 1. Overview & Architecture
Phase 36 introduces an enterprise-grade **Candidate Discovery & Hiring Intelligence Engine** for recruiters to search, filter, analyze, compare, and discover candidates across the platform.

Crucially:
- **Deterministic Match Integrity**: The existing 6-signal hybrid screening model (`35%` Required Coverage, `15%` Preferred Coverage, `25%` Semantic Similarity, `10%` Lexical Overlap, `10%` Experience Depth, `5%` Domain Alignment) remains the unchanged source of truth for job screening.
- **Discovery Relevance Score**: A distinct, transparent Discovery Relevance score (`discovery_relevance_score`) is calculated for candidate search and job-candidate discovery to rank candidates dynamically without silently overriding screening results.
- **Data Integrity**: Zero fake candidates, fake jobs, synthetic scores, or artificial recommendations are used. Every result stems from real persisted database records (`Candidate`, `Resume`, `Job`, `ScreeningResult`).

---

## 2. Semantic Search & Vector Embeddings
- **Production Provider**: `sentence-transformers/all-MiniLM-L6-v2` (`SentenceTransformerEmbeddingProvider`) via `EmbeddingService`.
- **Strategy**: On-demand vector encoding with LRU caching (`lru_cache`) to avoid external vector database infrastructure overhead for current scale.
- **Invalidation**: Text updates to resumes or jobs immediately update source text hashes and invalidate cached vector representations.

---

## 3. Discovery APIs & Functionality
The platform adds 5 dedicated discovery endpoints under `/api/v1/discovery`:

1. **`GET /api/v1/discovery/search`**
   - Natural language search query parsing (`q="Python backend developer with FastAPI and AWS"`).
   - Real candidate/resume vector semantic similarity.
   - Structured filter integration (`domain`, `min_required_cov`, `min_preferred_cov`, `min_semantic_sim`, `ood_status`, `review_status`).
   - Detailed explainability breakdown (matched skills, missing required skills, OOD review status, candidate experience).

2. **`GET /api/v1/discovery/jobs/{job_id}/candidates`**
   - Ranks real candidates against a target job using both deterministic screening score and discovery relevance.
   - Supports pagination, multi-field sorting, and recruiter status filtering.

3. **`GET /api/v1/discovery/candidates/{candidate_id}/similar`**
   - Identifies semantically similar candidate profiles using vector cosine distance.
   - Clearly labeled: `"Semantically similar — not automatically equivalent."`

4. **`GET /api/v1/discovery/jobs/{job_id}/similar`**
   - Finds semantically related job requisitions within the same organization tenant based on requirements, domain, and description text embeddings.

5. **`POST /api/v1/discovery/compare`**
   - Side-by-side factual metric matrix for multiple candidates (screening score, coverage, semantic similarity, matched/missing skills, domain, OOD status).
   - Produces objective metric comparisons with zero subjective verdicts.

---

## 4. Frontend Discovery Workspace
- **Layout**: Integrated Streamlit workspace (`frontend/views/candidate_discovery.py`).
  - **Top**: Natural Language Search input with filter tag extraction.
  - **Left**: Multi-faceted filter sidebar (Domain, Coverage sliders, OOD status, Review status).
  - **Center**: Real Candidate Result Cards displaying screening score, discovery relevance, match breakdowns, matched/missing skills.
  - **Right**: Candidate Intelligence & Comparison Panel with direct action shortcuts (Shortlist, Hold, Review, Compare).

---

## 5. Security, RBAC & Tenant Isolation
- **Authentication**: JWT token validation required (`get_current_user`).
- **RBAC**: Enforced via `AnyAuthUser` (`admin`, `hr`, `readonly` roles). Unauthenticated requests return `401 Unauthorized`; unauthorized roles return `403 Forbidden`.
- **Tenant Isolation**: Strict cross-tenant access prevention via `verify_tenant_access`. Candidates and jobs belonging to other tenants are hidden and return `403 Forbidden` / empty scope.
- **PII Protection**: PII fields (email, phone, address, internal notes) are scrubbed from search cards unless authorized.

---

## 6. OOD (Out-of-Domain) Policy Preservation
- **OOD Threshold**: Preserved at exact $\tau = 0.85$.
- **OOD Handling**: Candidates with `ood_status == "needs_review"` are clearly flagged with an AI/OOD warning badge (`Needs Review`). They are NEVER automatically rejected or hidden from discovery results.

---

## 7. Model & Data Integrity Verification
All model artifacts and processed dataset SHA-256 hashes are verified intact:
- `ml/artifacts/model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb`
- `ml/artifacts/model_v2.joblib`: `6be329ae771bfba5a86bf1130669bdc54aac786768581ebc21e124561e6df4`
- `ml/data/processed/train.csv`: `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0`
- `ml/data/processed/val.csv`: `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6`
- `ml/data/processed/test.csv`: `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4`

---

## 8. Test Execution & Verification
- **Phase 36 Test Suite (`backend/tests/test_phase36_discovery.py`)**: 25 passed out of 25 tests (100%).
- **Full Backend Test Suite (`backend/tests`)**: 274 passed out of 274 tests (100%).

---

## 9. System Limitations
- Vector index is cached in-memory per worker process; multi-node clusters with millions of resumes should transition to a dedicated vector index (e.g. Pgvector or Qdrant) in future phases.
- Keyword extraction for NL search relies on exact phrase & domain dictionary match.
