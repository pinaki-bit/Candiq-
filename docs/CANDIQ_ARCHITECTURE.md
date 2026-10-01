# Candiq Architecture Documentation

![Candiq Architecture](assets/candiq-architecture.png)

## 1. High-level architecture
Candiq is built around a centralized FastAPI backend serving multiple frontends (Streamlit, React, and a Browser Extension). It uses a modular service-oriented structure for handling machine learning, candidate matching, and data persistence via SQLite.

## 2. User flow
Candidates and Recruiters interact with specific frontends that consume the API securely over HTTPs, guarded by JWT authentication.

## 3. Candidate resume flow
Candidate → Streamlit Frontend → FastAPI → Resume Processing → NLP/ML → OOD Policy Check → Database Persistence.

## 4. Recruiter workflow
Recruiter → Frontend → Auth → Job Creation / Candidate Discovery → AI Analysis / Matching → Pipeline Dashboard.

## 5. ML pipeline
Resumes undergo feature extraction (TF-IDF) and classification via a Calibrated LinearSVC model. The model identifies one of five technical domains with a discrete confidence score.

## 6. NLP pipeline
spaCy PhraseMatcher evaluates candidate text against a canonical skill taxonomy, yielding precise matches and context snippets without generative AI hallucinations.

## 7. Semantic search
ll-MiniLM-L6-v2 dense embeddings project both candidate resumes and job requirements into a 384-dimensional space, queried via Cosine Similarity.

## 8. Matching engine
A 6-signal hybrid algorithm weights:
- Required Coverage (35%)
- Semantic Similarity (25%)
- Preferred Coverage (15%)
- Lexical Overlap (10%)
- Experience Depth (10%)
- Domain Alignment (5%)

## 9. OOD flow
Out-of-Domain checks examine the maximum predicted probability. If \< 0.85\, the system abstains from automatic classification and flags the candidate for human review, ensuring ethical AI operation.

## 10. LLM flow
External APIs (OpenAI/Gemini) are queried through a secure proxy service that strips PII and establishes firm prompt data boundaries.

## 11. Database/storage
Relational data is stored in SQLite (
esume_screening.db), scaling easily to PostgreSQL via SQLAlchemy. Raw PDFs and models are saved on the local filesystem.

## 12. Authentication/RBAC
OAuth2 with JWT tokens enforces role-based access limits for \dmin\, \hr\, and eadonly\ users, complete with token blocklisting for secure logouts.

## 13. Analytics
SQLAlchemy aggregation functions summarize recruitment pipeline metrics, domain breakdowns, and score distributions directly from the database.

## 14. Observability
Active health checks (/health/live, /health/ready), runtime metrics counting endpoints, and \X-Request-ID\ correlation IDs ensure stable production deployments.

## 15. Deployment
Docker and Docker Compose package the application into isolated containers for fast, reproducible deployment environments across platforms.
