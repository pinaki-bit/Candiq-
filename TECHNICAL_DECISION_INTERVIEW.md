# TECHNICAL DECISION INTERVIEW GUIDE — CANDIQ

This document outlines the engineering rationale behind every major technology choice in **Candiq**. Use this guide during technical interviews to defend technology decisions with empirical evidence and architectural clarity.

---

### 1. FastAPI vs Flask / Django
- **Why FastAPI?**  
  - Native asynchronous I/O (`async`/`await`) support built on Starlette and Pydantic v2.
  - Automatic OpenAPI / Swagger schema generation and runtime data validation.
  - High performance (comparable to Node.js and Go) for high-concurrency API workloads.
  - Native support for WebSocket streaming endpoints (`/ws/pipeline`).
- **Why not Flask?**  
  - Flask is WSGI-based (synchronous by default), requiring external extensions (Gevent/Celery) for async or WebSocket capabilities. Data validation requires manual setup (Marshmallow).
- **Why not Django?**  
  - Django is heavyweight and opinionated. Its built-in ORM and template rendering add unnecessary bloat for a decoupled REST API and ML microservice.

---

### 2. SQLite (WAL Mode) vs PostgreSQL
- **Why SQLite (in WAL mode)?**  
  - Zero-configuration, serverless single-file database ideal for local development, reproducible testing, and single-instance deployments.
  - Write-Ahead Logging (`PRAGMA journal_mode=WAL`) allows concurrent read operations while a write transaction is occurring, eliminating database lock contention.
  - Configured through SQLAlchemy ORM, enabling instant migration to PostgreSQL by changing one line in `.env` (`DATABASE_URL`).
- **Why not PostgreSQL for initial development?**  
  - Running a PostgreSQL service container adds setup complexity and external dependencies for local testing, slowing down rapid iteration without adding benefit during initial verification.

---

### 3. scikit-learn vs Deep Learning (PyTorch / TensorFlow)
- **Why scikit-learn?**  
  - CPU-friendly, lightweight (~50MB package footprint), lightning-fast training and inference (sub-10ms), and highly reproducible.
  - Tabular/sparse TF-IDF text classification on 1,570 samples achieves **97.84% accuracy** without requiring expensive GPU infrastructure.
- **Why not Deep Learning (PyTorch/TensorFlow)?**  
  - Fine-tuning a Transformer (e.g. RoBERTa) on 1,570 samples carries extreme risk of overfitting, requires GPU hosting (increasing deployment costs by 10x), increases inference latency from 5ms to 200ms+, and creates black-box interpretability issues.

---

### 4. TF-IDF Vectorization vs Fine-Tuned BERT Classifier
- **Why TF-IDF Vectorization?**  
  - Extracts distinct domain vocabulary (e.g., "Kubernetes", "Pentesting", "PyTorch") explicitly.
  - Produces deterministic, highly interpretable 50,000-dimensional sparse feature vectors.
  - Sub-millisecond vectorization latency with zero external model download requirements.
- **Why not BERT Classifier?**  
  - BERT models have a strict 512-token limit, requiring complex truncation or sliding-window chunking for multi-page resumes (which average 1,000–2,000 tokens). TF-IDF handles full-length text effortlessly.

---

### 5. LinearSVC vs Logistic Regression / XGBoost
- **Why LinearSVC?**  
  - Constructs maximum-margin decision boundaries optimal for high-dimensional sparse text vectors ($D=50,000$).
  - Achieved the highest **Macro F1 (0.9810)** and **Cloud Computing Recall (1.0000)** in our empirical model benchmarking audit (`FAIR_MODEL_COMPARISON.md`).
- **Why not Logistic Regression?**  
  - Logistic Regression achieved lower recall on minority domain classes under identical cross-validation splits.
- **Why not XGBoost?**  
  - XGBoost gradient boosted trees on 50,000 sparse TF-IDF columns caused high memory consumption and slower inference without improving classification accuracy over LinearSVC.

---

### 6. CalibratedClassifierCV (Platt Sigmoids) vs Uncalibrated Raw SVM Scores
- **Why CalibratedClassifierCV?**  
  - Raw LinearSVC decision function output scores represent geometric distances to hyperplanes, NOT true class probabilities.
  - Wrapping LinearSVC in `CalibratedClassifierCV(method="sigmoid", cv=5)` applies Platt scaling, producing true, well-calibrated $[0.0, 1.0]$ probability distributions across classes.
  - Essential for setting a reliable **Out-Of-Domain (OOD) confidence threshold at `0.85`**.
- **Why not Uncalibrated Raw SVM Scores?**  
  - Raw distance scores vary unpredictably in scale across classes, making uniform OOD thresholding impossible.

---

### 7. spaCy PhraseMatcher vs Regex / Generative AI Skill Extraction
- **Why spaCy PhraseMatcher?**  
  - Fast, deterministic, case-insensitive (`attr="LOWER"`) exact phrase matching against a taxonomy of 5 domains and hundreds of canonical skill aliases.
  - Guarantees zero hallucinations, extracts exact evidence context snippets, and counts skill occurrence frequencies.
- **Why not simple Regex?**  
  - Naive regex matching (e.g. matching "Java") creates high false positive rates (matching "JavaScript" or "Javanese"). spaCy's tokenizer respects word boundary tokens.
- **Why not Generative AI (LLM) Skill Extraction?**  
  - LLM skill extraction introduces non-deterministic outputs, API latency (1–3s per resume), recurring API costs, and risks hallucinating skills not present in the document.

---

### 8. MiniLM (`all-MiniLM-L6-v2`) vs OpenAI Embeddings (`text-embedding-3-small`)
- **Why MiniLM (`all-MiniLM-L6-v2`)?**  
  - Lightweight (90MB model size), 384-dimensional dense L2-normalized vector output.
  - Runs locally on CPU in ~20ms per document with zero API costs, zero internet dependency, and complete candidate data privacy.
- **Why not OpenAI Embeddings as default?**  
  - External API calls send candidate resume text over the internet, incurring recurring costs and introducing network latency and privacy exposure risks. (OpenAI is supported as an optional provider).

---

### 9. Cosine Similarity vs Euclidean / Manhattan Distance
- **Why Cosine Similarity?**  
  - Measures the angle between direction vectors in high-dimensional space regardless of magnitude.
  - A short resume and a long resume covering the same technical concepts yield identical directional alignment.
  - With L2-normalized vectors, Cosine Similarity simplifies to a fast dot product bounded in $[0.0, 1.0]$.
- **Why not Euclidean or Manhattan Distance?**  
  - Distance metrics are heavily sensitive to document length (vector magnitude). A longer resume with more words is naturally "further away" in Euclidean space even if it covers the exact same skills.

---

### 10. Streamlit vs React (Why both exist in the codebase)
- **Why Streamlit (`frontend/`)?**  
  - Used as the primary rapid-demonstration HUD interface. Written purely in Python, allowing seamless integration with data structures, session states, and rapid view prototyping.
- **Why React (`frontend_react/`)?**  
  - Included as a production SPA proof-of-concept demonstrating how the FastAPI backend integrates with modern frontend JavaScript frameworks (Vite, TypeScript, React) for enterprise white-label deployments.

---

### 11. WebSockets vs HTTP Long-Polling
- **Why WebSockets (`/ws/pipeline`)?**  
  - Full-duplex, single-TCP-connection event streaming. Enables server-initiated real-time event broadcasting (`text_extracted`, `skills_matched`, `classification_complete`) during batch uploads without client polling overhead.
- **Why not HTTP Long-Polling?**  
  - Long-polling creates repeated HTTP request/response headers, connection setup overhead, and server thread exhaustion under concurrent batch uploads.

---

### 12. JWT (Stateless Tokens) vs Session Cookies
- **Why JWT (JSON Web Tokens)?**  
  - Stateless, self-contained authentication. Tokens contain user ID, role, and tenant ID signed cryptographically via `HS256`, enabling effortless horizontal scaling across stateless backend nodes.
  - Paired with a `TokenBlocklist` table to support secure logout revocation.
- **Why not Session Cookies?**  
  - Server-side session cookies require centralized session storage (Redis/DB lookup) on every request, creating a bottleneck for decoupled microservices and mobile/extension clients.

---

### 13. Docker vs Bare-Metal Virtual Environments
- **Why Docker Containerization?**  
  - Encapsulates OS dependencies, C libraries (`poppler-utils`, `tesseract-ocr`), Python 3.12 runtime, and ML model artifacts into an immutable image.
  - Guarantees identical execution across development, testing, and production environments.
- **Why not Bare-Metal Virtual Environments?**  
  - Bare-metal setups suffer from system library mismatch issues (e.g. missing `pdf2image` binary dependencies or conflicting OS-level C++ compilers).

---

### 14. Multi-Provider LLM Abstraction vs Hardcoded LLM Provider
- **Why Multi-Provider Abstraction (`AIService` Facade)?**  
  - Encapsulates LLM calls behind a unified interface (`BaseAIProvider`), supporting `MockAIProvider` (offline/dev), `OpenAIProvider`, and `GeminiProvider`.
  - Prevents vendor lock-in, enables seamless failover if one API goes down, and allows unit testing with zero API costs using the Mock provider.
- **Why not hardcoding OpenAI or Gemini directly?**  
  - Hardcoding a single provider breaks offline testing, causes test suite failures when API keys are absent, and locks the application to a single vendor's pricing and uptime.
