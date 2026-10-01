# LIVE DEMO SCRIPT — CANDIQ

This script provides an exact step-by-step sequence of verified actions to demonstrate **Candiq** during a live presentation, viva, or interview.

---

### Step 1: Start Backend Server
Open terminal in the project root directory and run:
```bash
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
*Expected Result:* Terminal logs show startup security checks passing, database table creation, admin seeding, and `Application startup complete` on `http://127.0.0.1:8000`.

---

### Step 2: Start Frontend UI
Open a second terminal in the project root directory and run:
```bash
streamlit run frontend/app.py
```
*Expected Result:* Streamlit launches automatically in browser at `http://localhost:8501` displaying the HUD design system Login page.

---

### Step 3: Login as Recruiter / Admin
1. On the login screen (`http://localhost:8501`), enter:
   - **Email:** `admin@example.com`
   - **Password:** `changeme123`
2. Click **Login**.
*Expected Result:* Successful authentication. The app transitions to the Recruiter Dashboard displaying candidate statistics and active jobs.

---

### Step 4: Create a New Job Posting
1. Navigate to **Job Postings** in the sidebar.
2. Click **Create New Job**.
3. Enter details:
   - **Title:** `Senior Python Backend Engineer`
   - **Department:** `Engineering`
   - **Domain:** `Web Development`
   - **Description:** `Seeking a Senior Python Backend Engineer skilled in FastAPI, PostgreSQL, Docker, and Redis microservices.`
4. Add Requirements:
   - Required Skill: `Python` (Weight: 1.0)
   - Required Skill: `FastAPI` (Weight: 1.0)
   - Preferred Skill: `Docker` (Weight: 0.5)
5. Click **Save Job Posting**.
*Expected Result:* Job is saved to database and appears in active job listings.

---

### Step 5: Upload a Real Resume PDF
1. Navigate to **Upload Resumes** in the sidebar.
2. Select target job: `Senior Python Backend Engineer`.
3. Drag and drop a technical resume PDF (e.g. `test_resume.pdf` or from `Resumes PDF/`).
4. Click **Process Uploads**.
*Expected Result:* Live progress bar updates via WebSockets streaming ingestion events (`Uploaded` -> `Processing` -> `Completed`).

---

### Step 6: Show Text Extraction
1. Navigate to **Screening Results**.
2. Locate the processed candidate in the table.
3. Click **View Extracted Text**.
*Expected Result:* Displays raw text extracted by `pdfminer.six` with character count, page count, and ligature normalization.

---

### Step 7: Show ML Classification
1. In the candidate row, view the **Predicted Domain** badge (e.g., `Web Development`).
2. Expand **Classification Details**.
*Expected Result:* Shows model version (`v2.0.0`), top class probability (e.g., `0.9421`), and probability distribution across all 5 classes (Cloud, Security, Data Science, DevOps, Web Dev).

---

### Step 8: Show OOD Abstention Decision
1. (Demonstration Option A): Show the technical candidate displaying `OOD Status: in_domain_like` with a green `Accepted` badge (`top_prob >= 0.85`).
2. (Demonstration Option B): Upload an out-of-domain PDF (e.g., Accountant or Chef resume).
*Expected Result:* OOD engine flags the resume as `OOD Status: possible_out_of_domain` with an amber **Needs Manual Review** badge (`top_prob < 0.85`), proving abstention safety.

---

### Step 9: Show Extracted Canonical Skills & Evidence
1. Scroll to **Extracted Skills** section in the candidate view.
*Expected Result:* Displays badges for canonical skills extracted via spaCy `PhraseMatcher` (e.g. `Python`, `FastAPI`, `PostgreSQL`), along with occurrence frequencies and 200-character evidence snippets.

---

### Step 10: Show Skill Match Score
1. View the **Combined Skill Match Score** card (e.g. `85.0%`).
*Expected Result:* Displays required skill coverage percentage, preferred skill coverage percentage, matched required skills, and missing required skills.

---

### Step 11: Show Score Breakdown & Transparency
1. Click **View Transparent Score Breakdown**.
*Expected Result:* Renders JSON score breakdown showing exact mathematical formulas:
$$\text{Combined Match} = \frac{0.70 \times \text{Req Coverage} + 0.30 \times \text{Pref Coverage}}{0.70 + 0.30}$$
Proves zero black-box hidden scoring.

---

### Step 12: Open Candidate Profile & Update Status
1. Click **Open Candidate Profile**.
2. Review candidate history, contact details, and uploaded files.
3. Change candidate status dropdown from `pending_review` to `shortlisted`.
4. Click **Update Status**.
*Expected Result:* Candidate status updates in database and records an entry in `AuditEvent` log.

---

### Step 13: Show Semantic Candidate Discovery
1. Navigate to **Candidate Discovery** in the sidebar.
2. In the semantic query bar, type: `Backend developer experienced in microservices and database optimization`.
3. Set minimum match score filter to `70%`.
4. Click **Search Talent Pool**.
*Expected Result:* `discovery_service` computes `sentence-transformers` vector cosine similarity and returns ranked candidate matches across all stored applicants.

---

### Step 14: Show AI Candidate Match Explanation
1. In Candidate Discovery or Candidate Profile, click **Generate AI Summary**.
*Expected Result:* `ai_service.py` executes (using Mock, OpenAI, or Gemini provider) and generates a structured summary with matching reasons, strengths, concerns, and evidence bullets wrapped in `DATA_BOUNDARY` tags.

---

### Step 15: Generate Tailored 5-Question Interview Kit
1. Click **Generate Interview Kit**.
*Expected Result:* AI generates a structured 5-question interview kit containing Technical, Experience, Problem Solving, Behavioral, and Skill Gap probing questions with expected candidate key points.

---

### Step 16: Show Recruiter Analytics & Report Export
1. Navigate to **Analytics** in the sidebar.
*Expected Result:* Renders interactive charts showing candidate domain distribution, skill demand vs supply gap matrix, screening throughput over time, and average match scores per job.
2. Click **Export CSV Report**.
*Expected Result:* Instantly downloads aggregated hiring metrics report file.

---

### Step 17: Show System Health & Observability
1. Navigate to **System Health** in the sidebar.
*Expected Result:* Displays live server status, database connection state (SQLite WAL), total HTTP requests processed, error rates, average latency, and active request correlation metrics (`X-Request-ID`).
