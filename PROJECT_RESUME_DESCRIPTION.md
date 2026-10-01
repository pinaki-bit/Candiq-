# PROJECT RESUME DESCRIPTION — CANDIQ

Professional, technically accurate copy for your resume, LinkedIn, GitHub repository, and portfolio website.

---

### 1-Line Description
> **Candiq**: An AI-powered candidate intelligence and recruitment platform built with FastAPI, scikit-learn ML (97.84% accuracy), spaCy NLP, Sentence-Transformers semantic search, and Streamlit HUD.

---

### 3-Line Description
> **Candiq** is an AI-powered candidate intelligence and recruitment platform that automates resume understanding, candidate classification, skill matching, semantic candidate discovery, recruiter analytics, and AI-assisted hiring workflows. It features an Out-Of-Domain (OOD) abstention guardrail to eliminate false rejections, spaCy PhraseMatcher skill extraction with evidence snippets, and prompt-defended LLM interview kit generation. Engineered with FastAPI, SQLAlchemy (SQLite/PostgreSQL), OAuth2/JWT auth, multi-tenant RBAC, and Docker containerization.

---

### Resume Bullet Points (Software Engineer / ML Engineer / Full-Stack Role)

- **Engineered an enterprise candidate intelligence platform** using **FastAPI**, **SQLAlchemy**, and **Streamlit**, achieving **350ms end-to-end PDF upload to screening latency**.
- **Trained and deployed a Calibrated LinearSVC ML classifier** (Platt sigmoids, 5-fold CV) across 5 technical domains, attaining **97.84% test accuracy** and **0.981 macro F1 score**.
- **Designed a non-destructive OOD Abstention Policy Engine** frozen at OP-4 threshold (0.85 confidence), routing low-confidence predictions to manual review and achieving **96.85% out-of-domain rejection**.
- **Implemented a 6-signal hybrid ranking algorithm** combining spaCy PhraseMatcher skill coverage (70% required / 30% preferred), `sentence-transformers` vector cosine similarity, and lexical Jaccard overlap.
- **Integrated multi-provider LLM intelligence** (OpenAI `gpt-4o-mini`, Gemini `1.5-flash`, Mock) with `DATA_BOUNDARY` prompt injection protection, PII redaction, and automated USD cost tracking.
- **Architected enterprise security & multi-tenancy** with OAuth2/JWT token blocklisting, RBAC (`admin`, `recruiter`, `reviewer`), tenant isolation (`tenant_id`), SlowAPI rate limiting, and request correlation (`X-Request-ID`).
- **Built an automated test suite of 299 unit, integration, and security tests** achieving **81% code coverage** and containerized deployment with **Docker & Gunicorn/Uvicorn**.

---

### LinkedIn Project Description
**Candiq — Candidate Intelligence & AI-Powered Recruitment Platform**

🚀 Developed **Candiq**, a production-grade AI platform designed to replace black-box ATS keyword scanners with transparent, multi-signal candidate evaluation.

**Key Technical Achievements:**
- 🔹 **Machine Learning Core**: Calibrated `LinearSVC` model trained on TF-IDF features across 5 technical domains, achieving **97.84% accuracy** and **0.981 Macro F1**.
- 🔹 **OOD Trust Engine**: Built an Out-Of-Domain policy engine thresholded at 0.85 confidence to catch non-technical or uncertain resumes and route them for human recruiter review.
- 🔹 **NLP & Skill Extraction**: spaCy `PhraseMatcher` skill extraction with canonical deduplication and 200-character evidence context snippets.
- 🔹 **6-Signal Hybrid Ranking**: Multi-attribute candidate matching combining required/preferred skill coverage, `all-MiniLM-L6-v2` dense vector similarity, lexical overlap, and domain alignment.
- 🔹 **Generative AI & Security**: Multi-provider LLM integration (OpenAI/Gemini/Mock) for 5-question interview kit generation with prompt-injection defense and PII redaction.
- 🔹 **Production Backend**: Built with FastAPI, SQLAlchemy 2.x, OAuth2/JWT auth with blocklist revocation, RBAC, multi-tenant scoping, and WebSockets.

**Tech Stack**: Python, FastAPI, scikit-learn, spaCy, Sentence-Transformers, Pytest, Streamlit, React, SQLite WAL / PostgreSQL, Docker, Gunicorn.

---

### GitHub Repository Description
```markdown
# 🎯 Candiq — Candidate Intelligence & AI-Powered Recruitment Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI v0.3.0](https://img.shields.io/badge/FastAPI-v0.3.0-009688.svg)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-Calibrated%20LinearSVC-F7931E.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-299%20Passed%20%7C%2081%25%20Coverage-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

Candiq is an AI-powered candidate intelligence and recruitment platform that automates PDF resume parsing, ML domain classification, spaCy skill extraction, out-of-domain uncertainty detection, 6-signal hybrid job matching, and AI interview kit generation.

### Key Features
- ⚡ **Calibrated ML Classifier**: 97.84% accuracy, 0.981 Macro F1 across 5 technical domains.
- 🛡️ **OOD Abstention Guardrail**: Phase 24 OP-4 confidence threshold (0.85) routing uncertain resumes to manual review.
- 🔍 **spaCy Skill Matcher**: PhraseMatcher skill extraction with evidence context snippets.
- 📊 **6-Signal Hybrid Ranker**: Weighted matching (Skill Coverage, MiniLM-L6-v2 Vector Similarity, Jaccard Overlap).
- 🤖 **Defended LLM Layer**: OpenAI / Gemini / Mock provider abstraction with `DATA_BOUNDARY` prompt injection defense.
- 🔒 **Enterprise Security**: OAuth2/JWT auth, Token Blocklist, RBAC, Multi-tenancy (`tenant_id`), and Rate Limiting.
```

---

### Portfolio Website Project Summary
**Title:** Candiq — Candidate Intelligence & AI-Powered Recruitment Platform  
**Category:** Full-Stack Machine Learning & Enterprise Backend Systems  
**Overview:** Candiq is an AI-powered candidate intelligence and recruitment platform engineered to overcome the keyword rigidity and black-box opacity of legacy ATS software.  
**Architecture Highlights:**
- Developed a high-performance RESTful API in **FastAPI** paired with a Streamlit dark-mode HUD dashboard and React SPA.
- Trained a **Calibrated LinearSVC** classifier achieving **97.84% test accuracy** for 5-domain technical resume classification.
- Engineered an **Out-Of-Domain (OOD) policy engine** that abstains from high-uncertainty predictions (`prob < 0.85`), preventing false candidate rejections.
- Integrated **spaCy PhraseMatcher** for skill extraction with evidence snippets and **sentence-transformers (`all-MiniLM-L6-v2`)** for 384-dimensional dense vector semantic search.
- Built a **6-signal hybrid ranking engine** and a prompt-defended **AI interview kit generator** with multi-provider failover.
- Verified with an automated **299-test Pytest suite (81% coverage)** and packaged with **Docker & Gunicorn**.

---

### Architecture Showcase

Architecture diagram:

docs/assets/candiq-architecture.png

This diagram demonstrates:
User → Frontend → FastAPI → Resume Processing → NLP/ML → OOD → Matching → Semantic Search → Database → Recruiter Intelligence.
