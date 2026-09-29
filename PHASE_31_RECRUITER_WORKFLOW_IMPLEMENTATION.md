# PHASE 31 — REAL RECRUITER WORKFLOW & CANDIDATE MANAGEMENT REPORT

## EXECUTIVE SUMMARY

Phase 31 successfully built a **Real Recruiter Workflow & Candidate Management System** around Resume Intel's verified production intelligence engine (`sentence-transformers/all-MiniLM-L6-v2` semantic embeddings, 6-signal hybrid matching formula, NLP skill extraction, and ML domain classification).

Key principles enforced throughout Phase 31:
1. **Zero Fake Data / Zero Mock Activity**: Every count, table row, candidate score, and status badge is loaded dynamically from real SQLite database persistence.
2. **Assistive Ranking Signal — No Automatic Rejection**: AI scores are explicitly presented as assistive ranking signals for human decision-makers. AI does **NOT** automatically reject candidates.
3. **Explicit Recruiter Actions**: Shortlisting (`approved`), Rejection (`rejected`), and Marking for Review (`pending`/`on_hold`) are explicit, persistent recruiter actions.
4. **OOD Policy Distinction**: OOD uncertainty (`needs_review`) remains distinct from recruiter decisions (`rejected` or `approved`).
5. **Multi-Resume Batch Workflow**: Recruiters can upload single or multiple PDF resumes in a batch and optionally auto-match them against an active job position.

---

## 1. WORKFLOW ARCHITECTURE

```
                  Recruiter Login (JWT & RBAC)
                               ↓
                 Recruiter Dashboard (Real Metrics)
                               ↓
              Select / Create Job Position (Requirements)
                               ↓
        Upload Resumes (Single / Multi-Resume PDF Upload)
                               ↓
                     Processing Pipeline:
     [Text Extraction → Skill Extraction → ML Domain Classification → OOD Policy]
                               ↓
                  Candidate Record Persistence
                               ↓
       6-Signal Hybrid Matching & Score Explanation
                               ↓
       Candidate Ranking Table (Filter, Sort, Search)
                               ↓
             Candidate Evidence Card & Skill Chips
                               ↓
        Recruiter Review Action & Persistent Notes
             [Shortlist / Mark for Review / Reject]
```

---

## 2. KEY CAPABILITIES IMPLEMENTED & VERIFIED

### A. Job Management & Requirements Definition
- Recruiters can create, list, view, and deactivate job positions (`/api/v1/jobs`).
- Jobs define required skills (70% base weight) and preferred skills (30% base weight).

### B. Multi-Resume Batch Upload & Processing
- Introduced `/api/v1/resumes/upload-batch` to handle multi-file PDF resume uploads in a single request.
- Runs full processing pipeline per file: PDF text extraction $\rightarrow$ NLP skill extraction $\rightarrow$ ML domain classification $\rightarrow$ OOD evaluation $\rightarrow$ Candidate persistence.
- Optional auto-matching matches uploaded resumes against a target job automatically.

### C. Job-Candidate Screening & Persistent Match Records
- Persistent `ScreeningResult` records link Candidates to Jobs and store:
  - `relevance_score` (Composite 6-signal hybrid match)
  - `required_skill_coverage` & `preferred_skill_coverage`
  - JSON arrays of `matched_required_skills`, `missing_required_skills`, and `matched_preferred_skills`
  - `score_breakdown` JSON detailing exact formula breakdown & evidence snippets.

### D. Candidate Ranking Dashboard & Filtering
- Candidate ranking view displays candidates ranked by `relevance_score` descending.
- Supports sorting by Match Score, Required Coverage, or Domain Match.
- Filterable by review status (`pending`, `approved`, `rejected`, `on_hold`).

### E. Recruiter Actions, Bulk Actions & Notes
- Individual candidate review: Recruiters can update status (`approved`/`shortlisted`, `rejected`, `on_hold`) and add persistent reviewer notes.
- Bulk review: Introduced `/api/v1/screening/results/bulk-review` allowing recruiters to select multiple candidates and apply decisions in bulk.
- Batch match: Introduced `/api/v1/screening/{job_id}/match-all` allowing recruiters to screen all available resumes for a position in 1 click.

---

## 3. SECURITY & COMPLIANCE

- **RBAC Enforced**: `admin`, `hr`, and `readonly` roles control action permissions (only `hr`/`admin` can upload, create jobs, or update reviews).
- **PII Protection**: Original raw PDF text is never exposed in API responses or logs. Candidate display names / emails are optional reference codes.
- **Path Traversal & Validation**: PDF uploads are validated via magic bytes, MIME type, and size limits, stored under server-generated UUID filenames.

---

## 4. MODEL & DATA INTEGRITY VERIFICATION

| File | Expected SHA-256 | Actual SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **MATCH** |
| `model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **MATCH** |
| `train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **MATCH** |
| `val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **MATCH** |
| `test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **MATCH** |

- **OOD Threshold**: $\tau = 0.85$ (unchanged).

---

## 5. FILES CREATED / MODIFIED

- **Backend APIs**:
  - [`backend/app/api/v1/resumes.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/app/api/v1/resumes.py) — Added `upload_batch_resumes`
  - [`backend/app/api/v1/screening.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/app/api/v1/screening.py) — Added `bulk_update_reviews` & `match_all_resumes_to_job`
  - [`backend/app/schemas/screening.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/app/schemas/screening.py) — Added `BulkReviewUpdate`
- **Frontend Views**:
  - [`frontend/services/api_client.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/frontend/services/api_client.py) — Added `upload_batch_resumes`, `bulk_update_reviews`, `match_all_resumes_to_job`
  - [`frontend/views/upload.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/frontend/views/upload.py) — Multi-file uploader & job auto-matching
  - [`frontend/views/results.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/frontend/views/results.py) — Recruiter dashboard with sorting, skill chips, bulk decision bar, and candidate cards
- **Tests**:
  - [`backend/tests/test_phase31_recruiter_workflow.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/tests/test_phase31_recruiter_workflow.py) — E2E integration test suite for recruiter workflow
