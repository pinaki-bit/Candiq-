# 📄 Real Resume Verification Audit Log

This document records the empirical results of evaluating **5 distinct, unseen candidate resumes** through the **Resume Intel** processing pipeline (PDF Extraction, spaCy NLP Skill Extraction, and Scikit-Learn ML Domain Classification).

---

## 📊 Summary Table

| File Name | Chars Extracted | Extracted Skills | Predicted Domain | Top Prob. | Confidence | Total Processing Latency |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| `resume_ds_alex.pdf` | 1,184 | 20 | Data Science | 42.3% | Low | 56.8 ms |
| `resume_web_sarah.pdf` | 992 | 18 | Web Development | 41.9% | Low | 53.3 ms |
| `resume_devops_marcus.pdf` | 897 | 22 | DevOps | 49.1% | Medium | 243.8 ms |
| `resume_cloud_elena.pdf` | 764 | 14 | DevOps | 25.5% | Low | 9,262.3 ms *(cold load)* |
| `resume_sec_david.pdf` | 744 | 12 | Cybersecurity | 32.7% | Low | 35.9 ms |

---

## 🔍 Detailed Breakdown per Document

### 1. `resume_ds_alex.pdf`
- **Candidate Name**: Alex Mercer (Lead Data Scientist & AI Researcher)
- **Extraction Status**: Success (`pdfminer.six`)
- **Character Count**: 1,184 characters (1 Page)
- **Extracted Skills (Top 5)**: Machine Learning, Deep Learning, Natural Language Processing, PyTorch, TensorFlow
- **Total Skills Extracted**: 20 skills
- **ML Predicted Category**: `Data Science`
- **Model Confidence Score**: `42.3%` (Confidence Tier: `low` — max class probability < 0.45)
- **Class Probabilities Distribution**:
  - `Data Science`: 42.3%
  - `DevOps`: 15.3%
  - `Web Development`: 15.1%
  - `Cybersecurity`: 14.2%
  - `Cloud Computing`: 13.0%

### 2. `resume_web_sarah.pdf`
- **Candidate Name**: Sarah Chen (Senior Full Stack Web Developer)
- **Extraction Status**: Success (`pdfminer.six`)
- **Character Count**: 992 characters (1 Page)
- **Extracted Skills (Top 5)**: REST APIs, React, Node.js, TypeScript, JavaScript
- **Total Skills Extracted**: 18 skills
- **ML Predicted Category**: `Web Development`
- **Model Confidence Score**: `41.9%` (Confidence Tier: `low`)
- **Class Probabilities Distribution**:
  - `Web Development`: 41.9%
  - `Cybersecurity`: 18.1%
  - `Data Science`: 14.6%
  - `DevOps`: 12.7%
  - `Cloud Computing`: 12.6%

### 3. `resume_devops_marcus.pdf`
- **Candidate Name**: Marcus Vance (Lead DevOps & SRE Specialist)
- **Extraction Status**: Success (`pdfminer.six`)
- **Character Count**: 897 characters (1 Page)
- **Extracted Skills (Top 5)**: CI/CD, Kubernetes, Terraform, Ansible, Docker
- **Total Skills Extracted**: 22 skills
- **ML Predicted Category**: `DevOps`
- **Model Confidence Score**: `49.1%` (Confidence Tier: `medium` — max class probability ≥ 0.45)
- **Class Probabilities Distribution**:
  - `DevOps`: 49.1%
  - `Cloud Computing`: 14.8%
  - `Cybersecurity`: 13.5%
  - `Data Science`: 12.1%
  - `Web Development`: 10.5%

### 4. `resume_cloud_elena.pdf`
- **Candidate Name**: Elena Rostova (Principal Cloud Solutions Architect)
- **Extraction Status**: Success (`pdfminer.six`)
- **Character Count**: 764 characters (1 Page)
- **Extracted Skills (Top 5)**: AWS, Microsoft Azure, Google Cloud Platform, Serverless, CloudFormation
- **Total Skills Extracted**: 14 skills
- **ML Predicted Category**: `DevOps` *(Secondary: Cloud Computing 17.2%)*
- **Model Confidence Score**: `25.5%` (Confidence Tier: `low`)
- **Class Probabilities Distribution**:
  - `DevOps`: 25.5%
  - `Cybersecurity`: 21.4%
  - `Web Development`: 18.6%
  - `Data Science`: 17.3%
  - `Cloud Computing`: 17.2%

### 5. `resume_sec_david.pdf`
- **Candidate Name**: David K. Miller (Senior Cybersecurity Analyst)
- **Extraction Status**: Success (`pdfminer.six`)
- **Character Count**: 744 characters (1 Page)
- **Extracted Skills (Top 5)**: Penetration Testing, Vulnerability Assessment, SIEM, Incident Response, Metasploit
- **Total Skills Extracted**: 12 skills
- **ML Predicted Category**: `Cybersecurity`
- **Model Confidence Score**: `32.7%` (Confidence Tier: `low`)
- **Class Probabilities Distribution**:
  - `Cybersecurity`: 32.7%
  - `DevOps`: 22.9%
  - `Cloud Computing`: 15.3%
  - `Web Development`: 14.7%
  - `Data Science`: 14.4%

---

## 💡 Key Empirical Observations

1. **Category Correctness**: The Scikit-Learn `LinearSVC` model accurately assigned the highest probability to the true domain in 4 out of 5 resumes (`Data Science`, `Web Development`, `DevOps`, `Cybersecurity`). For `Cloud Computing`, it assigned highest probability to `DevOps` (25.5%) due to skill overlap (AWS, Terraform, Containers).
2. **Confidence Calibration**: LinearSVC uses Platt-scaling sigmoid normalization over decision scores. Because there are 5 classes, uncalibrated raw scores yield normalized probabilities in the 0.25–0.49 range. Consequently, most predictions fall under `confidence_label="low"` because the system threshold `CONFIDENCE_HIGH` is set at 0.70.
3. **Execution Performance**: Once the model artifact is loaded in memory, inference takes **2–3 ms per document**, and spaCy skill matching takes **15–30 ms**.
