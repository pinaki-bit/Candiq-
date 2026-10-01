# PROJECT MAP & REPOSITORY STRUCTURE

```
RESUME_SCREENING/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py      # JWT Auth, RBAC, Tenant dependencies
│   │   │   └── v1/
│   │   │       ├── admin.py          # Admin management & system routes
│   │   │       ├── ai.py             # LLM intelligence & completion routes
│   │   │       ├── analytics.py     # Hiring analytics & funnel metrics
│   │   │       ├── ats.py           # ATS adapter routes
│   │   │       ├── auth.py          # Auth, login, token management
│   │   │       ├── discovery.py     # Candidate discovery & NL search
│   │   │       ├── jobs.py          # Job requisition management
│   │   │       ├── resume_builder.py# AI Resume Builder routes
│   │   │       ├── resumes.py       # Resume PDF upload & management
│   │   │       └── screening.py     # Deterministic job-candidate matching
│   │   ├── core/
│   │   │   ├── logging_config.py    # Structured logging configuration
│   │   │   ├── metrics.py           # Real runtime performance metrics
│   │   │   ├── sanitizer.py         # XSS, path traversal, tenant checks
│   │   │   └── security.py          # Password hashing & JWT decoding
│   │   ├── models/                  # SQLAlchemy ORM Data Models
│   │   │   ├── candidate.py
│   │   │   ├── job.py
│   │   │   ├── resume.py
│   │   │   ├── resume_builder.py
│   │   │   ├── screening.py
│   │   │   └── user.py
│   │   ├── routers/
│   │   │   └── health.py            # Liveness, Readiness, & Metrics probes
│   │   ├── schemas/                 # Pydantic Request/Response Schemas
│   │   ├── services/                # Core Business Logic Services
│   │   │   ├── ai_service.py        # Generative AI completion provider
│   │   │   ├── backup_service.py    # DB online backup & integrity
│   │   │   ├── classification_service.py # ML domain prediction
│   │   │   ├── discovery_service.py # Vector semantic discovery engine
│   │   │   ├── embedding_service.py # MiniLM vector embedding provider
│   │   │   ├── matching_service.py  # Deterministic 6-signal matcher
│   │   │   ├── nlp_service.py       # spaCy NLP processing
│   │   │   ├── ood_policy.py        # OOD abstention policy engine
│   │   │   ├── pdf_service.py        # PDF extraction & magic bytes check
│   │   │   ├── resume_builder_service.py # Resume builder ATS optimization
│   │   │   ├── skill_service.py     # Skill taxonomy phrase matching
│   │   │   └── websocket_manager.py # WebSocket pipeline broadcaster
│   │   ├── config.py                # App settings & security validation
│   │   ├── database.py              # SQLAlchemy engine & session factory
│   │   └── main.py                  # FastAPI app factory & middleware
│   ├── tests/                       # Pytest Test Suites (Phases 1–38)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── components/
│   │   ├── sidebar.py               # Navigation sidebar
│   │   └── visualization_3d.py     # 3D WebGL Talent Core visualizer
│   ├── services/
│   │   └── api_client.py            # Typed HTTP API client
│   ├── styles/
│   │   └── __init__.py              # HUD Theme CSS & design system
│   ├── views/
│   │   ├── analytics.py             # Hiring Insights & Funnel charts
│   │   ├── candidate_discovery.py   # Semantic candidate search workspace
│   │   ├── candidate_profile.py     # Candidate details & explainability
│   │   ├── dashboard.py             # Recruiter command center
│   │   ├── jobs.py                  # Job creation & management
│   │   ├── results.py               # Screening results & candidate ranking
│   │   ├── resume_builder.py        # AI Resume Builder workspace
│   │   ├── system_health.py         # System Health & Observability UI
│   │   ├── upload.py                # PDF resume upload workspace
│   │   └── visualizer_3d.py         # 3D Talent Visualizer view
│   ├── app.py                       # Streamlit application entrypoint
│   └── requirements.txt
├── ml/
│   ├── artifacts/                   # ML Model artifacts & joblib files
│   └── data/processed/              # Train, validation, test datasets
├── shared/
│   └── skill_taxonomy.json          # Shared canonical technical skill taxonomy
├── docker-compose.yml
├── PHASE_37_PRODUCTION_HARDENING.md
├── PHASE_38_FINAL_RELEASE.md
└── README.md
```
