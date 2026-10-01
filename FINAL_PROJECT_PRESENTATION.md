# 5-MINUTE PROJECT PRESENTATION SCRIPT — CANDIQ

**Speaker:** Student / Lead Developer  
**Audience:** Project Evaluators, Professors, Technical Interviewers  
**Target Duration:** 5 Minutes (300 Seconds)

---

### [0:00 — 0:30] Problem Statement (30 Seconds)
"Good morning, everyone. Today I'm excited to present **Candiq**, an AI-powered candidate intelligence and recruitment platform that I built for my final-year project.

When companies post a single job opening, they often receive hundreds of resume PDFs. Traditional Applicant Tracking Systems try to solve this with simple keyword matching, but they fail constantly—rejecting great candidates over minor word phrasing while letting keyword-stuffed resumes pass. On the flip side, blindly feeding resumes into LLMs creates hallucination risks, slow response times, and high API costs. Furthermore, standard ML models have a major flaw: if an Accountant uploads a resume to a Software ATS, the model forces it into a tech domain with high confidence. We set out to solve all of these problems with a deterministic, auditable, and production-ready system."

---

### [0:30 — 1:00] Solution Overview (30 Seconds)
"**Candiq** addresses these challenges through a multi-stage intelligent pipeline. First, it securely extracts and normalizes text from PDFs. Second, it classifies resumes into five core technical domains using a calibrated machine learning model. Third, it applies an Out-Of-Domain abstention guardrail to flag non-technical or uncertain resumes for manual human review rather than guessing. Fourth, it extracts canonical skills with evidence snippets using spaCy NLP. Finally, it ranks candidates using a transparent 6-signal hybrid scoring formula and provides AI-driven interview kits and analytics."

---

### [1:00 — 1:45] Architecture & Ingestion (45 Seconds)
"Let me walk you through our architecture. The system is built with a decoupled FastAPI backend in Python and a Streamlit HUD frontend interface, along with an alternative React Single Page Application.

When a PDF is uploaded, our backend validates file magic bytes—ensuring it's a real PDF starting with `%PDF`—enforces a 10MB size limit, sanitizes filenames against path traversal, and saves it under a UUID. We use `pdfminer.six` to extract raw text streams while normalizing PDF font ligatures. If a resume is an image-based scan, the system gracefully falls back to Tesseract OCR."

---

### [1:45 — 2:30] ML Pipeline & OOD Abstention Guardrail (45 Seconds)
"Now, let's talk about the machine learning core. For domain classification, we extract word-level TF-IDF unigram features across 50,000 max features. We train a `LinearSVC` classifier wrapped in `CalibratedClassifierCV` using Platt sigmoids across 5-fold cross-validation. On our 278-sample independent test set, this model achieved **97.84% accuracy** and a **0.981 macro F1 score**.

To handle out-of-domain resumes—like finance or medical profiles—we implemented a non-destructive OOD policy engine. Based on our Phase 24 validation, we froze our operating threshold at **0.85 confidence**. If a candidate's top predicted class probability drops below 0.85, the system flags the resume as 'Needs Manual Review' rather than misclassifying it. This guarantees zero automatic false rejections."

---

### [2:30 — 3:15] Matching Engine & Semantic Search (45 Seconds)
"For skill extraction, we built a spaCy `PhraseMatcher` that scans resumes against a 5-domain taxonomy, extracting canonical skills, occurrence frequencies, and 200-character context snippets as evidence.

To rank candidates against job postings, we implemented a 6-signal hybrid ranking engine. It combines Required Skill Coverage weighted at 35%, Preferred Skill Coverage at 15%, Semantic Similarity at 25%, Lexical Overlap at 10%, Experience Depth at 10%, and Domain Alignment at 5%. For semantic search, we integrate `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional dense vectors to compute cosine similarity. Critically, our ranking logic enforces a strict invariant: high semantic similarity can never conceal missing required skills."

---

### [3:15 — 4:00] Recruiter Workflow & Interactive Tools (45 Seconds)
"From the recruiter's dashboard, hiring managers can view candidates sorted by hybrid score, inspect visual score breakdowns, view matched skill evidence, and filter out-of-domain reviews.

We also built an interactive ATS Resume Builder. It allows candidates to edit section drafts, maintain snapshot versions with one-click restoration, analyze ATS formatting compatibility, and rewrite resume bullet points with action verbs and metric placeholders."

---

### [4:00 — 4:30] Generative AI Features & Security (30 Seconds)
"For our Generative AI features, we designed a multi-provider `AIService` supporting Mock, OpenAI (`gpt-4o-mini`), and Google Gemini (`gemini-1.5-flash`). It generates candidate match summaries and tailored 5-question technical interview kits.

To prevent prompt injection attacks embedded inside PDF resumes, all untrusted candidate text is wrapped in `DATA_BOUNDARY` tags with strict system guardrails. Additionally, we redact PII like emails and phone numbers before sending data to external APIs."

---

### [4:30 — 5:00] Security, Testing & Conclusion (30 Seconds)
"Finally, Candiq is built with enterprise security: OAuth2 JWT authentication with token blocklisting, Role-Based Access Control (`admin`, `recruiter`, `reviewer`), multi-tenant data isolation, rate limiting, and request correlation headers. Our automated test suite includes **299 passing tests** with **81% code coverage**.

In conclusion, Candiq combines deterministic ML classification, transparent hybrid matching, robust OOD guardrails, and secure LLM intelligence into a scalable, auditable hiring platform. Thank you, and I welcome any questions!"
