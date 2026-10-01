# 🚀 Candiq: Production Deployment & Operations Guide

This guide provides comprehensive instructions for deploying, configuring, securing, and scaling **Candiq** in an enterprise production environment.

---

## 📋 Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & System Requirements](#2-prerequisites--system-requirements)
3. [Environment Configuration](#3-environment-configuration)
4. [Docker Containerization](#4-docker-containerization)
5. [Database Setup & Persistence](#5-database-setup--persistence)
6. [Security Hardening Checklist](#6-security-hardening-checklist)
7. [High Availability & Worker Scaling](#7-high-availability--worker-scaling)
8. [Monitoring, Cost Telemetry & Logging](#8-monitoring-cost-telemetry--logging)
9. [ATS & Chrome Extension Integration](#9-ats--chrome-extension-integration)
10. [Troubleshooting & Verification](#10-troubleshooting--verification)

---

## 1. Architecture Overview

Candiq is built as a microservice-ready enterprise platform comprising:
- **FastAPI Backend (Port 8000)**: Asynchronous REST and WebSocket API server.
- **Streamlit Frontend (Port 8501)**: Interactive recruiter UI with 3D WebGL WebGL visualizations.
- **Machine Learning Core**: Scikit-Learn TF-IDF domain classifier (`model_latest.joblib`) and spaCy NLP PhraseMatcher pipeline.
- **LLM Integration Engine**: Multi-provider support (OpenAI / Gemini / Mock) with token cost tracking and budget controls.
- **ATS Adapter Suite**: Unified adapters for Greenhouse, Lever, and Workday.
- **Chrome Extension Package**: Manifest v3 integration for candidate sourcing.

```
                    ┌────────────────────────┐
                    │    Chrome Extension    │
                    └───────────┬────────────┘
                                │ REST
                                ▼
┌─────────────────┐       ┌──────────┐       ┌────────────────────────┐
│ Streamlit UI    │──────>│ FastAPI  │──────>│ Scikit-Learn & spaCy   │
│ (Port 8501)     │ WS/   │ Backend  │ ML/   │ NLP Pipeline           │
└─────────────────┘ REST  │ (8000)   │ NLP   └────────────────────────┘
                          └────┬─────┘
                               │ ORM
                               ▼
                        ┌──────────────┐
                        │ SQLite DB    │
                        └──────────────┘
```

---

## 2. Prerequisites & System Requirements

### Hardware Requirements
- **CPU**: 4 vCPUs minimum (8 vCPUs recommended for concurrent PDF parsing).
- **RAM**: 8 GB RAM minimum (16 GB recommended).
- **Disk Storage**: 20 GB SSD storage (plus dedicated volume for PDF storage).

### Software Requirements
- **Python**: Version 3.12+
- **Docker Engine**: Version 24.0+
- **Docker Compose**: Version 2.20+
- **OS**: Ubuntu 22.04 LTS, Windows Server 2022, or macOS 14+

---

## 3. Environment Configuration

Create a `.env` file in the project root based on the following template:

```ini
# Application Configuration
APP_ENV=production
DEBUG=false
SECRET_KEY=generate_a_secure_random_hex_string_64_chars_long

# CORS & Security
ALLOWED_ORIGINS=https://app.resumeintel.com,http://localhost:8501
TENANT_ISOLATION_ENABLED=true

# Database Configuration
DATABASE_URL=sqlite:///./resume_screening.db

# LLM & AI Provider Settings
DEFAULT_LLM_PROVIDER=openai # Options: openai, gemini, mock
OPENAI_API_KEY=sk-prod-your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# Cost Telemetry & Budget Caps
DAILY_TOKEN_BUDGET_USD=50.00
MAX_TOKENS_PER_REQUEST=4096

# Admin Bootstrap Credentials
ADMIN_EMAIL=admin@resumeintel.com
ADMIN_PASSWORD=SuperSecureProductionPassword123!
```

---

## 4. Docker Containerization

### Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpoppler-cpp-dev \
    tesseract-ocr \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]
```

### Production `docker-compose.yml`
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: resume_intel_backend
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - resume_data:/app/uploads
      - db_data:/app/data

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: resume_intel_frontend
    restart: always
    ports:
      - "8501:8501"
    environment:
      - BACKEND_API_URL=http://backend:8000
    depends_on:
      - backend

volumes:
  resume_data:
  db_data:
```

---

## 5. Database Setup & Persistence

1. **Database Initialization**: On initial startup, FastAPI automatically runs SQLAlchemy migrations to create tables and indexes.
2. **Persistence Volume**: Ensure the directory storing `resume_screening.db` is mounted to persistent host storage.
3. **Backup Strategy**: Schedule daily SQLite database backups:
   ```bash
   sqlite3 /app/data/resume_screening.db ".backup '/backups/resume_db_$(date +%Y%m%m_%H%M%S).sqldump'"
   ```

---

## 6. Security Hardening Checklist

- [x] **Content Security Policy (CSP)**: Strict headers enforced in FastAPI middleware (`default-src 'self'; script-src 'self' 'unsafe-eval' https://cdn.jsdelivr.net;`).
- [x] **Path Traversal Sanitization**: `sanitize_filepath` strips `../`, `./`, and non-alphanumeric characters from file storage targets.
- [x] **XSS HTML Escaping**: `sanitize_html` strips embedded scripts and unsafe attributes from candidate resumes and rewriter inputs.
- [x] **Tenant Isolation**: Multi-tenant database boundary verification (`verify_tenant_access`) ensures strict data isolation between corporate accounts.
- [x] **JWT Token Expiry**: Token blocklisting enabled for immediate user logout handling.

---

## 7. High Availability & Worker Scaling

For high-concurrency production deployments:
- Use **Gunicorn** with **Uvicorn Workers**:
  ```bash
  gunicorn -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000 app.main:app
  ```
- **Rule of Thumb for Workers**: `(2 * CPU_CORES) + 1` workers.
- **Nginx Reverse Proxy**: Route external HTTPS traffic to Gunicorn on port 8000 and Streamlit on port 8501.

---

## 8. Monitoring, Cost Telemetry & Logging

- **Token Telemetry**: Monitor daily LLM API expenditure via `GET /api/v1/analytics/token-usage`.
- **Health Checks**: Endpoint `GET /api/v1/health` provides continuous DB, NLP, and model status checks.
- **Log Aggregation**: Application logs are formatted with ISO-8601 timestamps and logged to stdout for Docker log drivers.

---

## 9. ATS & Chrome Extension Integration

- **Greenhouse / Lever / Workday**: Configure provider API credentials in candidate export requests (`POST /api/v1/ats/export`).
- **Chrome Extension**: Distribute the pre-packaged extension from `browser_extension/` via Chrome Web Store Developer Dashboard or internal enterprise MDM.

---

## 10. Troubleshooting & Verification

To verify complete system health after deployment:
```bash
# Execute Pytest Full Test Suite
cd backend
pytest -v
```

All 132 tests should pass cleanly.
