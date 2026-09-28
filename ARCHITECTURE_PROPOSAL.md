# 🏗️ ARCHITECTURE PROPOSAL: HYBRID AI HIRING PLATFORM

**Proposal Version**: 1.0.0  
**Target System**: Resume Intelligence Enterprise Platform  

---

## 1. System Architecture Overview

The upgraded system extends the existing FastAPI + React/Streamlit architecture into a **Multi-Role Hybrid AI Hiring Intelligence Platform**.

```
                                  ┌──────────────────────────────────────────────┐
                                  │           React 19 / Streamlit UI            │
                                  │   (Recruiter Portal + Candidate Portal)      │
                                  └──────────────────────┬───────────────────────┘
                                                         │ HTTP / WebSockets
                                                         ▼
                                  ┌──────────────────────────────────────────────┐
                                  │             FastAPI Backend API              │
                                  │            (App Security & RBAC)             │
                                  └──────┬───────────────┬───────────────┬───────┘
                                         │               │               │
                 ┌───────────────────────┘               │               └────────────────────────┐
                 ▼                                       ▼                                        ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐             ┌─────────────────────────┐
    │ Deterministic AI Core   │             │   Semantic Search Engine│             │ LLM GenAI Service Layer │
    │ 1. spaCy NLP Pipeline   │             │ 1. Embedding Provider   │             │ 1. AIService Abstraction│
    │ 2. Scikit-Learn Model   │             │    Interface            │             │ 2. OpenAI / Gemini      │
    │    (Domain Predictor)   │             │ 2. Vector DB Adapter    │             │ 3. Prompt & Cost Guard  │
    │ 3. Lexical Skill Match  │             │    (pgvector / Qdrant)  │             │ 4. Bullet Rewriter      │
    └─────────────────────────┘             └─────────────────────────┘             └─────────────────────────┘
```

---

## 2. Core Hybrid Matching Architecture

The matching engine will combine six distinct scoring signals into an explainable composite match score:

$$\text{Composite Score} = w_1 \cdot S_{\text{req}} + w_2 \cdot S_{\text{pref}} + w_3 \cdot S_{\text{sem}} + w_4 \cdot S_{\text{lex}} + w_5 \cdot S_{\text{exp}} + w_6 \cdot S_{\text{dom}}$$

### Default Weight Configuration (Admin Configurable):
- **$S_{\text{req}}$ (Required Skill Coverage)**: $35\%$
- **$S_{\text{pref}}$ (Preferred Skill Coverage)**: $15\%$
- **$S_{\text{sem}}$ (Semantic Similarity via Vector Embeddings)**: $25\%$
- **$S_{\text{lex}}$ (Lexical Keyword / TF-IDF Similarity)**: $10\%$
- **$S_{\text{exp}}$ (Experience & Role Relevance)**: $10\%$
- **$S_{\text{dom}}$ (Machine Learning Domain Classification Alignment)**: $5\%$

> ⚠️ **Strict Constraint Guarantee**: Semantic similarity will *never* satisfy a hard missing requirement. If a candidate lacks 2 years of Kubernetes experience, $S_{\text{req}}$ will explicitly highlight Kubernetes as missing regardless of semantic closeness.

---

## 3. Subsystem Designs

### 3.1 LLM Service Abstraction (`AIService`)
- Abstract base class `LLMProvider` with implementations:
  - `OpenAIProvider`
  - `GeminiProvider`
  - `LocalProvider`
- Zero direct client calls to LLMs; all requests pass through backend proxy with token counting, prompt caching, cost logging, and rate limits.
- **Factual Guardrail**: Enforces strict prompt boundaries preventing fabrication of companies, dates, degrees, or unsupplied metrics.

### 3.2 Embedding & Vector Search Layer (`EmbeddingService`)
- Provider-agnostic interface supporting OpenAI `text-embedding-3-small`, BGE embeddings, or local HuggingFace models.
- Persistence via `pgvector` or file-backed vector index storing 1536-dim / 768-dim resume & job chunk embeddings.

### 3.3 Live Candidate Resume Builder & Match Simulator
- Dual-pane interface: Left-side editor with Markdown/Structured inputs, Right-side real-time preview, Bottom debounced AI optimization panel.
- Debounced calculation engine ($500\text{ms}$ delay) computing ATS formatting checks, keyword density, and job alignment without spamming backend servers.

### 3.4 Interview Intelligence Engine
- Generates 5 grounded technical interview questions categorized into:
  1. Technical Fundamentals
  2. Practical Implementation
  3. Project-Based Deep Dive
  4. Scenario-Based Problem Solving
  5. Verification / Claim Validation Question
- Displays **"Why this question?"** mapping directly back to verified resume snippets or skill gap areas.

### 3.5 Real-Time WebSocket Event Pipeline & 3D Visualizer
- WebSockets (`/ws/pipeline`) emitting actual backend processing events:
  - `resume.uploaded` $\rightarrow$ `resume.extracting` $\rightarrow$ `resume.classified` $\rightarrow$ `resume.matched`.
- The Three.js `IntelligenceCore.tsx` visualizer binds directly to these WebSocket event state streams without synthetic timers.

---

## 4. Multi-Tenant Security & Entitlements
- **Organization Isolation**: Every database query filters by `organization_id`.
- **RBAC**: `recruiter_admin`, `recruiter_member`, `candidate_user`, `system_admin`.
- **SaaS Entitlement Layer**: Tracks monthly processing usage, AI token consumption, and active job limits without blocking the local dev environment.
