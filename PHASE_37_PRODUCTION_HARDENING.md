# PHASE 37 — PRODUCTION DEPLOYMENT, OBSERVABILITY, PERFORMANCE & RELIABILITY HARDENING

## 1. Executive Summary & Overview
Phase 37 hardens **Candiq** for enterprise production deployment. It establishes robust health probes, structured logging, request correlation tracing, runtime performance observability, database lifecycle management, automated SQLite/relational backup and recovery, strict rate limiting, security headers, file upload security, and graceful shutdown capabilities.

**Core Rules Compliance**:
- **Zero Retraining or Model Replacement**: The ML classifier (`model_latest.joblib`) and production embedding provider (`sentence-transformers/all-MiniLM-L6-v2`) remain intact.
- **Data & Policy Integrity**:
  - Out-of-Domain (OOD) threshold remains frozen at $\tau = 0.85$.
  - 6-signal hybrid screening weights remain unchanged (`35%` Required Coverage, `15%` Preferred Coverage, `25%` Semantic Similarity, `10%` Lexical Overlap, `10%` Experience Depth, `5%` Domain Alignment).
- **Zero Synthetic Observability**: All latency metrics and status reports reflect actual runtime execution data without fabricated statistics.
- **No Git Commit/Push**: Kept in local working state as requested.

---

## 2. Production Architecture & Configuration Management
- **Configuration Engine**: Managed via `pydantic-settings` (`Settings` in `backend/app/config.py`). Environment variables are type-validated at startup from `.env` or system environment.
- **Secrets Management**:
  - `SECRET_KEY`: Auto-generates a 256-bit cryptographic token if default sentinel is detected.
  - Production mode (`APP_ENV=production`) disables OpenAPI/Swagger UI endpoints (`/docs`, `/redoc`, `/openapi.json`) and refuses to start with default credentials (`admin_password`).
- **Environment Variables**:
  - `APP_ENV`: `development` | `production` | `test`
  - `DATABASE_URL`: `sqlite:///./resume_screening.db` (dev) | `postgresql://user:pass@host:5432/dbname` (prod)
  - `SECRET_KEY`: 256-bit random hex string.
  - `CORS_ORIGINS`: Comma-separated list of allowed origins.
  - `API_BASE_URL`: Frontend configuration for backend base URL.

---

## 3. Health & Readiness Probes
The platform provides 4 health and reliability routes under `/health` and `/api/v1/health`:

1. **`GET /health`** (Liveness Overview)
   - Returns app title, version (`v0.3.0`), and environment (`status=ok`).
2. **`GET /health/live`** (Kubernetes Liveness Probe)
   - Fast, non-blocking check returning `{"status": "alive"}` (HTTP 200). Does NOT touch external dependencies.
3. **`GET /health/ready`** (Kubernetes Readiness Probe)
   - Verifies 4 core dependencies:
     - **Database**: `check_db_connection()` (`SELECT 1` ping).
     - **ML Classifier Model**: Verifies existence and readability of `active_model_path`.
     - **Embedding Provider**: Verifies availability of `EmbeddingService`.
     - **File Storage**: Verifies writable permissions on `upload_dir`.
   - Returns HTTP 200 `{"status": "ready", "checks": {...}}` when all pass, or HTTP 503 `{"status": "not_ready", ...}` if any required component fails.
4. **`GET /health/metrics`** (Runtime Observability Probe)
   - Exposes real aggregate performance metrics collected by `MetricsCollector` (API request counts, average API latency, DB query latency, ML inference latency, embedding latency, LLM latency, PDF extraction latency). Returns `"No runtime data available"` if uninitialized.

---

## 4. Structured Logging & Request Correlation
- **Correlation ID Middleware**: Every incoming HTTP request is assigned a unique `X-Request-ID` (`req_<uuid12>`) or inherits the client's `X-Request-ID` header.
- **Response Header**: `X-Request-ID` is returned in all HTTP response headers for request tracing.
- **PII & Secret Protection**: Logs sanitize sensitive data. Raw resume text, JWT tokens, passwords, API keys, and PII are never logged.

---

## 5. Error Handling & Exception Management
- **Structured Error Responses**: Standardized JSON format across API errors:
  ```json
  {
    "detail": "Descriptive error message.",
    "error_code": "INTERNAL_SERVER_ERROR",
    "request_id": "req_a1b2c3d4e5f6",
    "timestamp": "2026-10-02T00:45:00+00:00"
  }
  ```
- **Production Traceback Masking**: Raw Python stack traces are hidden from API clients in production mode (`is_production = True`).

---

## 6. Database Reliability & Backup System
- **SQLite Optimization**: Uses Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and Foreign Key enforcement (`PRAGMA foreign_keys=ON`) for concurrency.
- **Connection Lifecycle**: `pool_pre_ping=True` handles stale connections.
- **Automated Live Backup**: Real database backup service (`backend/app/services/backup_service.py`):
  - Uses `sqlite3` online backup API to write timestamped backup copies to `backups/db_backup_YYYYMMDD_HHMMSS.db`.
  - Verifies backup file integrity via `PRAGMA quick_check`.
- **PostgreSQL Compatibility**: SQLAlchemy engine natively supports PostgreSQL via `postgresql://` connection strings for high-scale production clusters.

---

## 7. Security Headers & Rate Limiting
- **Security Headers**:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'`
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (Production mode)
- **Rate Limiting**: Enforced via `slowapi` on login (`10/min`), upload (`20/min`), and API endpoints (`200/min`). Exceeded requests receive structured HTTP 429 JSON responses.

---

## 8. File Upload Security
- **Strict Validation**:
  - Extension check against allowed set (`.pdf`).
  - Magic byte verification (`%PDF` header signature match).
  - Maximum upload size enforcement (`10 MB`).
  - Path traversal protection (stripping `..`, `/`, `\`).
  - UUID filename generation for stored files (`uuid4.hex.pdf`).
  - Non-executable permissions on upload storage directory.

---

## 9. ML, Embedding & LLM Provider Reliability
- **ML Classifier Loading**: Single-instance eager/lazy initialization with existence checks on model artifacts.
- **Embedding Provider**: `SentenceTransformerEmbeddingProvider` with LRU caching. Graceful fallback on missing dependencies.
- **LLM Provider**: Configurable timeout (`timeout_seconds`), retry limits, and mock/graceful fallback handling when external AI APIs are unreachable.

---

## 10. WebSockets & Graceful Shutdown
- **WebSocket Endpoint**: `/ws/pipeline` supports real-time pipeline event streaming with heartbeats (`ping`/`pong`) and disconnection cleanup.
- **Graceful Shutdown**: FastAPI lifespan hook disposes database connections (`engine.dispose()`) and logs clean process termination.

---

## 11. Model & Dataset Hashes Verification
Verified SHA-256 hashes of all artifacts:
- `ml/artifacts/model_latest.joblib`: `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb`
- `ml/artifacts/model_v2.joblib`: `6be329ae771bfba5a86bf1130669bdc54aac786768581ebc21e124561e6df4`
- `ml/data/processed/train.csv`: `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0`
- `ml/data/processed/val.csv`: `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6`
- `ml/data/processed/test.csv`: `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4`

---

## 12. Test Execution Results
- **Phase 37 Test Suite (`backend/tests/test_phase37_production.py`)**: `33 / 33` passed (100%).
- **Full Backend Regression Suite (`backend/tests`)**: `307 / 307` passed (100%).

---

## 13. Production Deployment Recommendation
For high-availability enterprise production deployment:
1. Deploy backend using Gunicorn + Uvicorn workers (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`).
2. Migrate database target from SQLite to managed PostgreSQL (`AWS RDS` or `GCP Cloud SQL`).
3. Position Nginx or AWS ALB reverse-proxy in front of the application for SSL termination and DDoS mitigation.
