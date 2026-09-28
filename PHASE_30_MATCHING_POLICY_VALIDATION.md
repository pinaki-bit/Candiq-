# PHASE 30 — MATCHING POLICY & RANKING VALIDATION REPORT

**Project**: Resume Intel / AI Resume Screening & Hiring Platform  
**Phase**: Phase 30 (Matching Policy & Ranking Validation)  
**Date**: September 28, 2026  
**Status**: **COMPLETED & EVALUATED (EVALUATION ONLY)**

---

## 1. OBJECTIVE

Evaluate whether the current production matching policy and 6-signal hybrid candidate ranking engine produce intuitive rankings, and measure the empirical effect of an offline gated policy (`Gated Score = Current Score * (ReqCoverage / 100)`) across 10 controlled evaluation scenarios without changing production scoring logic or modifying ML models.

**Strict Mandate Verification**:
- Production scoring formulas and hybrid weights were **NOT** altered in production.
- Resume classifier was **NOT** retrained.
- Training, validation, and test datasets were **NOT** modified.
- OOD threshold ($\tau = 0.85$) was **NOT** changed.
- Zero Git commits were created; zero code was pushed.

---

## 2. CURRENT PRODUCTION SCORING FORMULAS

### Base Skill Matching Formula (`matching_service.py`)
$$\text{Required Coverage} = \frac{\sum \text{Matched Required Weights}}{\sum \text{Total Required Weights}} \times 100$$

$$\text{Preferred Coverage} = \frac{\sum \text{Matched Preferred Weights}}{\sum \text{Total Preferred Weights}} \times 100$$

$$\text{Base Combined Match} = \frac{0.70 \times \text{Required Coverage} + 0.30 \times \text{Preferred Coverage}}{1.0}$$

### Production 6-Signal Hybrid Ranking Engine (`matching_service.py`)
$$\text{Hybrid Score} = 0.35(\text{ReqCov}) + 0.15(\text{PrefCov}) + 0.25(\text{SemSim}) + 0.10(\text{LexSim}) + 0.10(\text{ExpDepth}) + 0.05(\text{DomainBonus})$$

---

## 3. EVALUATION DATASET METHODOLOGY

An evaluation benchmark fixture (`ml/scripts/run_phase30_benchmark.py`) consisting of 10 realistic resume/job-description scenarios was evaluated:

- **SCENARIO_A**: All required skills present (`Python`, `FastAPI`, `PostgreSQL`, `Docker`, `AWS`).
- **SCENARIO_B**: One required skill missing (`PostgreSQL` missing).
- **SCENARIO_C**: Multiple required skills missing (`FastAPI`, `PostgreSQL` missing).
- **SCENARIO_D**: Zero required skills present, but preferred skills present (`Docker`, `AWS`).
- **SCENARIO_E**: Zero required and zero preferred skills present (`Java`, `Spring Boot`).
- **SCENARIO_F**: Required skills present, but low semantic similarity (academic biology text).
- **SCENARIO_G**: High semantic concept similarity, but required skills missing (Rust/C++ Systems Architect).
- **SCENARIO_H**: Strong keyword overlap, but wrong domain (Sales Executive listing hobbies).
- **SCENARIO_I**: Paraphrased skills with low exact-word overlap.
- **SCENARIO_J**: Strong technical match with different wording.

---

## 4. EMPIRICAL RESULTS: POLICY 1 (PRODUCTION) vs POLICY 2 (OFFLINE GATED)

| Scenario ID & Description | Req Cov | Pref Cov | Semantic | Policy 1 Base | Policy 1 Hybrid | Policy 2 Gated Base | Policy 2 Gated Hybrid | Missing Required |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SCENARIO_A** (All Req Present) | 100.0% | 100.0% | 94.22% | **100.0%** | **85.53%** | **100.0%** | **85.53%** | *None* |
| **SCENARIO_J** (Strong Tech Match) | 100.0% | 100.0% | 81.82% | **100.0%** | **82.35%** | **100.0%** | **82.35%** | *None* |
| **SCENARIO_B** (1 Req Missing) | 66.67% | 100.0% | 82.07% | **76.67%** | **69.39%** | **51.12%** | **46.26%** | `PostgreSQL` |
| **SCENARIO_I** (Paraphrased Req) | 100.0% | 50.0% | 61.02% | **85.00%** | **67.27%** | **85.00%** | **67.27%** | *None* |
| **SCENARIO_H** (Wrong Domain Hobbies)| 100.0% | 0.0% | 54.24% | **70.00%** | **51.85%** | **70.00%** | **51.85%** | *None* |
| **SCENARIO_C** (Multi Req Missing) | 33.33% | 50.0% | 57.40% | **38.33%** | **41.14%** | **12.78%** | **13.71%** | `FastAPI`, `PostgreSQL` |
| **SCENARIO_F** (Low Semantic Academic)| 66.67% | 0.0% | 41.59% | **46.67%** | **36.18%** | **31.11%** | **24.12%** | `FastAPI` |
| **SCENARIO_D** (0% Req, 100% Pref) | 0.0% | 100.0% | 46.52% | **30.00%** | **29.21%** | **0.00%** | **0.00%** | `Python`, `FastAPI`, `PostgreSQL` |
| **SCENARIO_G** (High Sem 0% Req) | 0.0% | 0.0% | 44.09% | **0.00%** | **17.31%** | **0.00%** | **0.00%** | `Python`, `FastAPI`, `PostgreSQL` |
| **SCENARIO_E** (0% Req, 0% Pref) | 0.0% | 0.0% | 30.13% | **0.00%** | **13.06%** | **0.00%** | **0.00%** | `Python`, `FastAPI`, `PostgreSQL` |

---

## 5. ANALYSIS OF KEY FINDINGS

### A. The Mandatory-Skill Behavior (Scenario D)
- **Policy 1 (Production Base Match)**: Returns a **30.0%** match score when a candidate has 0% required skills but 100% preferred skills.
- **Policy 1 (Production Hybrid Score)**: Incorporating semantic similarity, experience depth, and domain alignment lowers the total candidate score to **29.21%**, ranking Scenario D at #8 out of 10.
- **Policy 2 (Offline Gated Policy)**: Zero required skills forces the score to **0.0%**.

### B. High Semantic vs High Required Coverage (Scenario G vs Scenario B)
- **Scenario G** (Rust Systems Architect, High Semantic Concept, 0% Required Skills) obtains a Policy 1 Hybrid score of **17.31%**.
- **Scenario B** (Python Developer missing 1 required skill, 66.67% Required Skills) obtains a Policy 1 Hybrid score of **69.39%**.
- **Finding**: High semantic similarity alone **NEVER** overrides missing required skills under the production 6-signal formula. Scenario B wins comfortably under both Policy 1 and Policy 2.

### C. Ranking Quality & Metrics
- **Precision@1**: `1.00` for both Policy 1 and Policy 2.
- **Precision@3**: `1.00` for both Policy 1 and Policy 2.
- **Conclusion**: The production 6-signal hybrid ranking engine (`Policy 1`) already places qualified technical candidates (Scenarios A, J, B, I) at the top of the candidate pool.

---

## 6. REGRESSION & INTEGRITY VERIFICATION

- **Pytest Suite**: **180 / 180 Backend Tests Passing** (100% Pass Rate).
- **Model & Dataset Checksums**:
  - `ml/artifacts/model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` (**100% MATCH**)
  - `ml/artifacts/model_v2.joblib`: `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` (**100% MATCH**)
  - `ml/data/processed/train.csv`: `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` (**100% MATCH**)
  - `ml/data/processed/val.csv`: `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` (**100% MATCH**)
  - `ml/data/processed/test.csv`: `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` (**100% MATCH**)
- **OOD Threshold**: $\tau = 0.85$ (Unchanged).

---

## 7. EVIDENCE-BASED RECOMMENDATION

1. **Preserve Current Production Formula (Policy 1)**: Empirical benchmarking demonstrates that Policy 1 achieves **1.00 Precision@1 and Precision@3**, correctly ranking qualified candidates above non-matching resumes.
2. **Consider Optional Enterprise Strict Gating**: While Policy 1 ranks Scenario D low (~29%), introducing an optional configurable setting (`STRICT_MANDATORY_GATE=True`) in a future phase would allow enterprise clients who require hard 0% cutoffs to enable gating without altering standard screening defaults.

---

## 8. GIT STATUS & CREATED FILES

- **Created Files**:
  - `ml/scripts/run_phase30_benchmark.py` (Evaluation script)
  - `reports/phase30_matching_policy_benchmark.json` (Raw evaluation metrics)
  - `backend/tests/test_phase30_matching.py` (Unit tests)
  - `PHASE_30_MATCHING_POLICY_VALIDATION.md` (Audit document)
- **Modified Files**: `None`
- **Git Commit**: `None` (holding for user review)
- **Git Push**: `None`
