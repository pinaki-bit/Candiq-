# TECHNICAL DECISIONS & ARCHITECTURAL RATIONALE

## 1. Machine Learning & Model Selection
- **Algorithm**: LinearSVC with Platt Calibration via Sigmoid CalibratedClassifierCV over TF-IDF n-grams (1-2 word range).
- **Rationale**: LinearSVC provides fast, deterministic inference (~5ms on CPU) with sparse feature interpretability compared to heavy uncalibrated deep neural nets.
- **Model Hashes**:
  - `model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb`
  - `model_v2.joblib`: `6be329ae771bfba5a86bf1130669bdc54aac786768581ebc21e124561e6df4`

---

## 2. OOD Policy Engine ($\tau = 0.85$)
- **Decision**: Implemented an auditable, non-destructive Out-Of-Domain policy threshold at $\tau = 0.85$.
- **Rationale**: In closed-world classification, non-technical or out-of-domain resumes would otherwise receive arbitrary high-confidence domain labels. Setting $\tau = 0.85$ captures 96.85% of out-of-domain test cases and routes them to human recruiters for manual review (`status = "needs_review"`). Automatic rejection is strictly forbidden.

---

## 3. Production Semantic Embedding Engine
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`.
- **Rationale**: Generates 384-dimensional dense semantic vectors with fast CPU execution time (~10ms). Avoids heavy external vector database overhead for current scale while providing high-quality semantic similarity.

---

## 4. Deterministic 6-Signal Matching Formula
- **Formula**:
  - Required Skill Coverage: **35%**
  - Preferred Skill Coverage: **15%**
  - Semantic Similarity: **25%**
  - Lexical Token Overlap: **10%**
  - Experience Depth: **10%**
  - Domain Alignment Bonus: **5%**
- **Rationale**: Prevents pure keyword matching vulnerabilities while ensuring that mandatory job requirements remain the dominant factor in candidate ranking.

---

## 5. Security & Multi-Tenancy Strategy
- **Authentication**: JWT Bearer Tokens + Password Hashing (`passlib`/`bcrypt`).
- **Multi-Tenancy**: Data isolation enforced at every service and router layer using `tenant_id`.
- **PII Scrubbing**: PII fields (phone, address, email, raw text) are scrubbed from discovery cards and log streams.

---

## 6. Observability & Database Reliability
- **Observability**: Real runtime metrics collector (`MetricsCollector`) recording API latency, DB query latency, and inference timing without synthetic data.
- **Database Engine**: SQLite WAL mode for development; PostgreSQL recommended for multi-worker containerized production setups.
