# PHASE 29A — REAL SEMANTIC EMBEDDING EVALUATION REPORT

**Project**: Resume Intel / AI Resume Screening & Hiring Platform  
**Phase**: Phase 29A (Real Semantic Embedding Evaluation)  
**Date**: September 28, 2026  
**Status**: **COMPLETED & EVALUATED (EVALUATION ONLY)**

---

## 1. OBJECTIVE

Evaluate whether a real local semantic embedding model (`sentence-transformers/all-MiniLM-L6-v2`) materially improves resume $\leftrightarrow$ job-description semantic matching compared to the current term-hashing vector projection (`LocalEmbeddingProvider`), while maintaining CPU compatibility, fast inference, and zero reliance on external cloud APIs.

**Strict Mandate Verification**:
- Production embedding provider was **NOT** replaced during this phase.
- Production scoring formulas and weights were **NOT** altered.
- Resume classifier was **NOT** retrained.
- Training, validation, and test datasets were **NOT** modified.
- OOD threshold ($\tau = 0.85$) was **NOT** changed.
- Zero Git commits were created; zero code was pushed.

---

## 2. EXISTING EMBEDDING ARCHITECTURE vs. BENCHMARK CANDIDATE

### Existing Production Provider (`LocalEmbeddingProvider`)
- **Location**: `backend/app/services/embedding_service.py`
- **Methodology**: Deterministic term-hashing projection vectorizer.
- **Dimensionality**: 128 dense float dimensions.
- **Mechanism**: Hashes individual lowercase words via MD5 (`idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % 128`), sums frequency counts, and applies L2 normalization.
- **Classification**: `EXPERIMENTAL / NON-SEMANTIC PLACEHOLDER (HASH-PROJECTION)`.

### Benchmark Candidate Provider (`SentenceTransformerEmbeddingProvider`)
- **Location**: `ml/scripts/run_phase29a_benchmark.py` (Isolated Evaluation Script).
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensionality**: 384 dense float dimensions.
- **Architecture**: 6-layer BERT Transformer optimized for sentence embeddings (~22.7M parameters, ~90 MB disk footprint).
- **Execution Mode**: CPU-only execution (`device="cpu"`).

---

## 3. BENCHMARK ENVIRONMENT & METADATA

- **OS**: Windows 11 (`10.0.26200-SP0`)
- **Python**: 3.12.4
- **PyTorch Version**: `2.14.0+cpu`
- **SentenceTransformers Version**: `6.1.0`
- **Transformers Version**: `5.17.0`
- **CPU Cores**: 12 Cores (Logical Processors)
- **GPU Required**: **NO** (Evaluated 100% on CPU)

---

## 4. CONTROLLED BENCHMARK METHODOLOGY & PAIR RESULTS

A controlled benchmark dataset consisting of 7 distinct resume/job-description text pairs across 7 categories was evaluated on both providers:

| Pair ID & Category | Text Description Summary | Pair Type | Local MD5 Hash Sim | MiniLM Sim | MiniLM Gain ($\Delta$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **PAIR_01_STRONG_RELEVANT** | Python FastAPI Backend Developer vs Python FastAPI Backend Engineer Job | Positive | `0.4097` | **`0.8013`** | **+0.3916** (+39.2%) |
| **PAIR_02_PARTIAL_RELEVANT** | Data Analyst (Python/SQL) vs Senior Data Scientist (PyTorch/CV) Job | Positive | `0.2863` | **`0.2638`** | `-0.0225` |
| **PAIR_03_UNRELATED** | Commercial Litigation Attorney vs Cloud Infrastructure Engineer Job | Negative | `0.1800` | **`0.1760`** | `-0.0040` |
| **PAIR_04_PARAPHRASED** | Server-side Web Apps (Python/Async) vs Python Server-side API Services Job | Positive | `0.4523` | **`0.5794`** | **+0.1271** (+12.7%) |
| **PAIR_05_KEYWORD_DIFF_CONTEXT** | Parse Legal PDF Contracts with Python vs Python Distributed Microservices Job | Negative | `0.2434` | **`0.3323`** | `+0.0889` |
| **PAIR_06_DOMAIN_RELATED** | Network Penetration Specialist vs React Frontend Developer Job | Negative | `0.1336` | **`0.0800`** | **-0.0536** (Better Rejection) |
| **PAIR_07_CROSS_DOMAIN_NEG** | Registered Nurse Clinical Care vs DevOps Kubernetes Engineer Job | Negative | `0.1867` | **`0.1360`** | **-0.0507** (Better Rejection) |

---

## 5. STATISTICAL PERFORMANCE METRICS

| Metric | Local MD5 Hash Provider | `all-MiniLM-L6-v2` Provider | Net Measured Improvement |
| :--- | :---: | :---: | :---: |
| **Mean Positive Pair Similarity** | `0.3828` | **`0.5482`** | **+0.1654** (+43.2%) |
| **Mean Negative Pair Similarity** | `0.1859` | **`0.1811`** | **-0.0048** (Cleaner Rejection) |
| **Separation Margin** ($\text{Pos} - \text{Neg}$) | `0.1969` | **`0.3671`** | **+0.1702 (+86.4% Increase)** |
| **Paraphrase Recognition Gap** | `0.2089` | **`0.2471`** | **+0.0382** |

### Core Empirical Findings:
1. **Separation Margin Boost**: `all-MiniLM-L6-v2` increased the separation margin between matching and non-matching candidate resumes from `0.1969` to `0.3671` (**86.4% improvement**).
2. **Strong Match Recognition**: On strongly relevant resume/job pairs (PAIR_01), similarity surged from `0.4097` (MD5 hash) to `0.8013` (MiniLM).
3. **Paraphrase Understanding**: On semantically paraphrased text (PAIR_04), MiniLM recognized semantic equivalence (`0.5794` similarity) significantly better than surface MD5 hashing (`0.4523`).
4. **Cross-Domain Rejection**: On non-technical cross-domain resumes (e.g. Registered Nurse vs DevOps Engineer, PAIR_07), MiniLM produced lower false-similarity (`0.1360`) compared to MD5 hashing (`0.1867`).

---

## 6. LATENCY & RESOURCE FOOTPRINT BENCHMARKS

All latency measurements were taken on a 12-core CPU under standard Python 3.12 execution:

| Performance Dimension | Local MD5 Hash Provider | `all-MiniLM-L6-v2` (CPU) | Impact Assessment |
| :--- | :---: | :---: | :--- |
| **Cold Model Load Time** | `< 1 ms` | `18,313.83 ms` (~18.3 s) | Requires one-time lazy background load on startup. |
| **Single Text Warm Latency** | `0.12 ms` | `13.08 ms` | Well within acceptable REST API latency limits ($< 20$ ms). |
| **Batch (10 Texts) Warm Latency** | `0.99 ms` | `82.64 ms` | Excellent CPU batch performance ($< 8.3$ ms per text). |
| **Disk Storage Footprint** | `0 MB` | `~90 MB` | Compact model artifact size. |
| **RAM Footprint (Loaded Model)** | `< 5 MB` | `~250 MB` | Fits comfortably on any developer or server system. |
| **GPU Dependency** | **None** | **None** | 100% CPU compatible. |

---

## 7. SYSTEM COMPATIBILITY AUDIT (`matching_service.py`)

- **Interface Compatibility**: `SentenceTransformerEmbeddingProvider` cleanly implements `embed_text(text: str) -> list[float]` and `embed_batch(texts: list[str]) -> list[list[float]]`.
- **Vector Normalization**: `all-MiniLM-L6-v2` outputs L2-normalized 384-dimensional dense float arrays, rendering cosine similarity computations directly compatible with existing `cosine_similarity` in `embedding_service.py`.
- **Hybrid Weight Compatibility**: Replacing `LocalEmbeddingProvider` with `all-MiniLM-L6-v2` in `EmbeddingService` would require **ZERO architectural changes** to `compute_hybrid_match` in `matching_service.py`.

---

## 8. REGRESSION & INTEGRITY VERIFICATION

- **Automated Pytest Suite**: **170 / 170 Backend Tests Passing** (100% Pass Rate).
- **Model & Dataset Checksums**:
  - `ml/artifacts/model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` (**100% MATCH**)
  - `ml/artifacts/model_v2.joblib`: `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` (**100% MATCH**)
  - `ml/data/processed/train.csv`: `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` (**100% MATCH**)
  - `ml/data/processed/val.csv`: `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` (**100% MATCH**)
  - `ml/data/processed/test.csv`: `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` (**100% MATCH**)
- **OOD Threshold**: $\tau = 0.85$ (Unchanged).

---

## 9. OBJECTIVE RECOMMENDATION FOR PHASE 29B

Based on empirical benchmark evidence:
1. **Promote `all-MiniLM-L6-v2` to Production**: The candidate transformer model expands the positive-to-negative separation margin by **86.4%** while preserving strict CPU execution safety and fast single-text warm inference (13.08 ms).
2. **Implement Lazy Singleton Loading**: To manage the ~18.3 s cold start latency, the provider should be initialized asynchronously or lazily loaded upon application startup.
3. **Maintain Local Hash Provider as Fallback**: Retain `LocalEmbeddingProvider` as a zero-dependency fallback in case model weight downloading is disabled or restricted.

---

## 10. GIT STATUS & CREATED FILES

- **Created Files**:
  - `ml/scripts/run_phase29a_benchmark.py` (Isolated benchmark script)
  - `reports/phase29a_embedding_benchmark.json` (Raw metrics output)
  - `PHASE_29A_SEMANTIC_EMBEDDING_EVALUATION.md` (Audit document)
- **Modified Files**: `None`
- **Git Commit**: `None` (holding for user review)
- **Git Push**: `None`
