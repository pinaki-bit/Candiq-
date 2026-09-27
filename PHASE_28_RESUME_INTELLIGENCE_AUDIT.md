# PHASE 28 — RESUME INTELLIGENCE CORE: REAL SKILL EXTRACTION & JOB MATCHING AUDIT REPORT

**Project**: Resume Intel  
**Phase**: Phase 28 (Resume Intelligence Core Audit & Validation)  
**Date**: September 28, 2026  
**Status**: **COMPLETED & VALIDATED (OUTCOME A)**

---

## 1. EXECUTIVE SUMMARY & VERIFICATION MATRIX

Phase 28 audited, measured, and validated the core resume extraction, skill normalization, evidence snippet generation, job matching formula, mandatory skill behavior, and semantic embedding implementations without retraining ML models or modifying datasets.

### Feature Classification Matrix

| Subsystem / Capability | Phase 28 Classification | Implementation Location | Notes |
| :--- | :---: | :--- | :--- |
| **NLP Skill Extraction** | **IMPLEMENTED AND VERIFIED** | `backend/app/services/skill_service.py` | Uses spaCy `PhraseMatcher` (`attr="LOWER"`). |
| **Alias Normalization** | **IMPLEMENTED AND VERIFIED** | `shared/skill_taxonomy.json` | Maps 100+ skill aliases to canonical terms. |
| **Evidence Snippet Extraction** | **IMPLEMENTED AND VERIFIED** | `backend/app/services/skill_service.py` | Preserves 200-char context window around matches. |
| **Skill Matching Formula** | **IMPLEMENTED AND VERIFIED** | `backend/app/services/matching_service.py` | 70% Required / 30% Preferred weighted match score. |
| **Missing Skill Identification** | **IMPLEMENTED AND VERIFIED** | `backend/app/services/matching_service.py` | Explicitly calculates `missing_required` & `missing_preferred`. |
| **Hybrid Ranking Engine** | **IMPLEMENTED AND VERIFIED** | `backend/app/services/matching_service.py` | 6-signal score (Req, Pref, Sem, Lex, Exp, Dom). |
| **Mandatory Skill Behavior** | **PARTIALLY IMPLEMENTED / LIMITATION** | `backend/app/services/matching_service.py` | Zero mandatory skills yield 30% score if preferred match. |
| **Semantic Embedding Engine** | **EXPERIMENTAL / NON-SEMANTIC PLACEHOLDER** | `backend/app/services/embedding_service.py` | `LocalEmbeddingProvider` uses MD5 term hashing projection. |
| **Deterministic Match Explanation** | **IMPLEMENTED AND VERIFIED** | `backend/app/services/matching_service.py` | Returns `score_breakdown` dict with full transparency. |

---

## 2. CURRENT SKILL EXTRACTION & TAXONOMY ARCHITECTURE

### spaCy PhraseMatcher (`backend/app/services/skill_service.py`)
- **Matcher Initialization**: Rebuilds an in-memory spaCy `PhraseMatcher` (`attr="LOWER"`) from `shared/skill_taxonomy.json`.
- **Deduplication & Frequency**: Groups matches by `canonical_name`, accumulates frequency counts, and extracts a clean 200-character evidence snippet around the match location.
- **Security & Privacy**: Processes resume text entirely in-memory. Zero PII logging.

### Taxonomy Structure (`shared/skill_taxonomy.json`)
The taxonomy encompasses 5 primary tech domains:
1. **Data Science**: Python, R, SQL, Julia, scikit-learn, TensorFlow, PyTorch, Pandas, NumPy, Machine Learning, Deep Learning, NLP.
2. **Web Development**: HTML, CSS, JavaScript, TypeScript, React, Vue.js, Angular, Node.js, Express.js, Django, FastAPI, PostgreSQL, MongoDB, REST APIs.
3. **Cloud Computing**: AWS, Amazon EC2, Amazon S3, AWS Lambda, Microsoft Azure, Google Cloud Platform, BigQuery, Terraform, Kubernetes, Docker.
4. **DevOps**: Docker, Kubernetes, Helm, CI/CD, Jenkins, GitHub Actions, Terraform, Ansible, Prometheus, Grafana, Git, Bash.
5. **Cybersecurity**: Network Security, Firewall, VPN, SIEM, Splunk, Penetration Testing, Burp Suite, Nmap, Digital Forensics, Cloud Security, ISO 27001, Linux.

---

## 3. SKILL NORMALIZATION & TEST MATRIX

A test matrix of real resume text phrases was evaluated against the skill extraction engine:

| Test Input Phrase | Extracted Canonical Skill | Domain / Category | Status |
| :--- | :--- | :--- | :---: |
| `Python` | `Python` | Data Science / programming | **PASSED** |
| `python` | `Python` | Data Science / programming | **PASSED** |
| `PYTHON` | `Python` | Data Science / programming | **PASSED** |
| `Python 3` | `Python` | Data Science / programming | **PASSED** |
| `React.js` | `React` | Web Development / frontend | **PASSED** |
| `ReactJS` | `React` | Web Development / frontend | **PASSED** |
| `Node.js` | `Node.js` | Web Development / backend | **PASSED** |
| `Node` | `Node.js` | Web Development / backend | **PASSED** |
| `PostgreSQL` | `PostgreSQL` | Web Development / databases | **PASSED** |
| `Postgres` | `PostgreSQL` | Web Development / databases | **PASSED** |
| `AWS` | `AWS` | Cloud Computing / aws | **PASSED** |
| `Amazon Web Services` | `AWS` | Cloud Computing / aws | **PASSED** |

---

## 4. SKILL EVIDENCE PRESERVATION

When a skill is extracted, the service constructs a `SkillMatch` object containing:
- `canonical_name`: Standardized skill name (e.g. `Python`).
- `matched_text`: Exact verbatim snippet from resume (e.g. `python`).
- `domain`: High-level domain (e.g. `Web Development`).
- `category`: Sub-category (e.g. `backend`).
- `evidence_snippet`: Surrounding sentence/context snippet (max 200 characters).

Example Evidence Output:
```json
{
  "canonical_name": "FastAPI",
  "matched_text": "FastAPI",
  "domain": "Web Development",
  "category": "backend",
  "evidence_snippet": "Developed enterprise microservices using Python and FastAPI on AWS."
}
```

---

## 5. JOB DESCRIPTION PARSING & MATCHING FORMULA

### Job Requirement Parsing (`backend/app/models/job.py`)
- Job descriptions store structured requirements (`JobRequirement` ORM model) divided into `is_required=True` (Required) and `is_required=False` (Preferred), each with a relative weight (default `1.0`).

### Match Score Formula (`backend/app/services/matching_service.py`)
$$\text{Required Coverage} = \frac{\sum \text{Matched Required Weights}}{\sum \text{Total Required Weights}} \times 100$$

$$\text{Preferred Coverage} = \frac{\sum \text{Matched Preferred Weights}}{\sum \text{Total Preferred Weights}} \times 100$$

$$\text{Combined Match Score} = \frac{0.70 \times \text{Required Coverage} + 0.30 \times \text{Preferred Coverage}}{1.0}$$

---

## 6. MANDATORY SKILL BEHAVIOR ANALYSIS

To evaluate the system's behavior when mandatory skills are missing, 4 test scenarios were evaluated:
- **Required Skills**: `Python`, `FastAPI`, `PostgreSQL`
- **Preferred Skills**: `Docker`, `AWS`

| Test Scenario | Matched Required | Matched Preferred | Req Coverage | Pref Coverage | Base Score | Hybrid Score | Behavior Assessment |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Case A**: All Mandatory Present | `Python`, `FastAPI`, `PostgreSQL` | `Docker`, `AWS` | 100.0% | 100.0% | **100.0%** | **65.05%** | **CORRECT** |
| **Case B**: One Mandatory Missing | `Python`, `FastAPI` | `Docker`, `AWS` | 66.67% | 100.0% | **76.67%** | **52.59%** | **ACCEPTABLE** |
| **Case C**: Multiple Mandatory Missing | `Python` | `Docker` | 33.33% | 50.0% | **38.33%** | **31.82%** | **ACCEPTABLE** |
| **Case D**: Zero Mandatory Present | *None* | `Docker`, `AWS` | 0.0% | 100.0% | **30.0%** | **27.65%** | **DESIGN LIMITATION** |

### Analysis & Discovery:
In **Case D**, when a candidate has **ZERO mandatory skills**, `compute_match` still returns a **30.0%** score because preferred skills contribute 30% of the total score.
- **Classification**: `DESIGN LIMITATION / QUESTIONABLE BEHAVIOR`.
- **Proposed Future Fix (Not Implemented in Phase 28 per prompt instructions)**:
  Apply a Mandatory Skill Multiplier Gate:
  $$\text{Final Score} = \text{Combined Match} \times \left(\frac{\text{Required Coverage}}{100}\right)$$
  *(Under this gate, 0% required coverage would correctly force Final Score to 0.0%).*

---

## 7. SEMANTIC EMBEDDING ARCHITECTURE AUDIT

An audit of `backend/app/services/embedding_service.py` was conducted:
- **Default Provider**: `LocalEmbeddingProvider`.
- **Implementation**: Computes an MD5 term-hashing vector projection into a 128-dimensional dense float vector, followed by L2 normalization (`idx = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % 128`).
- **Classification**: **`EXPERIMENTAL / NON-SEMANTIC PLACEHOLDER (HASH-PROJECTION)`**.
- **Finding**: While computationally lightweight ($< 1$ ms) and deterministic, term-hashing does not capture deep semantic embedding relationships (e.g. "Golang" vs "Go").
- **Recommendation for Future Phase**: Replace `LocalEmbeddingProvider` with a real local SentenceTransformers model (e.g. `all-MiniLM-L6-v2` or `bge-small-en-v1.5`).

---

## 8. MODEL & DATASET INTEGRITY VERIFICATION

All core model artifacts and dataset CSVs were verified via SHA-256 checksums:

| File Path | Expected SHA-256 Checksum | Measured SHA-256 Checksum | Verification Status |
| :--- | :--- | :--- | :---: |
| `ml/artifacts/model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **100% MATCH** |
| `ml/artifacts/model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **100% MATCH** |
| `ml/data/processed/train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **100% MATCH** |
| `ml/data/processed/val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **100% MATCH** |
| `ml/data/processed/test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **100% MATCH** |

---

## 9. TEST SUITE EXPANSION & EXECUTION

- **New Test Suite**: Created [`backend/tests/test_phase28_intelligence.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/tests/test_phase28_intelligence.py) containing 8 targeted tests covering skill extraction, alias normalization, multi-word skills, evidence snippets, 70/30 matching formulas, mandatory skill behavior, and embedding verification.
- **Test Results**:
  - **170 / 170 Backend Tests Passing** (100% Pass Rate).
  - Test Execution Time: 40.33 seconds.

---

## 10. DISCOVERED BUGS, LIMITATIONS & PROPOSED IMPROVEMENTS

1. **Multi-Domain Taxonomy Frequency Amplification (Minor Bug)**:
   - *Issue*: When a skill (e.g. `Python`) belongs to multiple taxonomy domains (`Data Science`, `DevOps`, `Cybersecurity`), spaCy `PhraseMatcher` creates multiple rule IDs, causing `frequency` to be multiplied by the number of matching categories.
   - *Fix Recommendation*: Deduplicate match rule IDs per canonical skill during PhraseMatcher registration.
2. **Missing Mandatory Skill Non-Zero Score (Design Limitation)**:
   - *Issue*: Candidates missing 100% of required skills receive a 30% match score if all preferred skills match.
   - *Fix Recommendation*: Implement a mandatory multiplier gate $\text{Score} \times (\text{ReqCoverage} / 100)$.
3. **Local Embedding Hash Projection (Experimental Limitation)**:
   - *Issue*: Local embedding provider relies on term MD5 hashing rather than transformer neural embeddings.
   - *Fix Recommendation*: Upgrade to local SentenceTransformers in a future phase.

---

## 11. CONCLUSION & PHASE 28 STATUS

Phase 28 is complete under **OUTCOME A (No Significant Blocking Code Changes Required)**. All existing capabilities have been audited, measured, documented, and backed by automated pytest cases.

**Git & Safety Status**:
- Zero ML retraining performed.
- Zero dataset files modified.
- Zero model artifacts altered.
- Zero un-audited scoring changes applied.
- Git commit created: **NONE** (holding for user review).
- Git push executed: **NONE**.
