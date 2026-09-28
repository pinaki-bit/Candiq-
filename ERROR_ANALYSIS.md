# 🔍 Phase 21F: Baseline Error Analysis Report

This document presents a detailed empirical error analysis of the baseline production model (`ml/artifacts/model_latest.joblib`, LinearSVC v20260922_235001) evaluated on the clean validation dataset (`ml/data/processed/val.csv`, 277 records).

---

## 📊 Error Distribution Summary

- **Total Validation Records**: 277
- **Correctly Classified**: 241 (87.00%)
- **Misclassified Records**: 36 (13.00%)

### Error Breakdown Matrix (Actual vs Predicted)

| Actual Domain | Predicted Domain | Error Count | Percentage of Total Errors | Primary Root Cause |
| :--- | :--- | :---: | :---: | :--- |
| **Cloud Computing** | `DevOps` | **14** | 38.9% | Class Imbalance & High Vocabulary Overlap |
| **Data Science** | `DevOps` | **7** | 19.4% | Multi-Domain Keywords (MLOps / Pipelines) |
| **Data Science** | `Web Development` | **5** | 13.9% | Shared Web/Python Frameworks (`Flask`, `FastAPI`) |
| **Cybersecurity** | `Web Development` | **4** | 11.1% | Web Application Security Vocabulary (`WAF`, `HTTP`, `SSL`) |
| **Cybersecurity** | `Cloud Computing` | **3** | 8.3% | Network Cloud Security Overlap (`AWS Security`, `IAM`) |
| **Cybersecurity** | `DevOps` | **1** | 2.8% | Infrastructure Security Automation (`Linux`, `Bash`) |
| **DevOps** | `Web Development` | **1** | 2.8% | Web Deployment Infrastructure (`Nginx`, `Node.js`) |
| **Web Development** | `Data Science` | **1** | 2.8% | Full-stack Data Visualization (`D3.js`, `Python`) |

---

## 🔬 In-Depth Analysis of Major Error Patterns

### Pattern 1: `Cloud Computing` Misclassified as `DevOps` (14/14 = 100% Error Rate)
- **Sample Excerpt**: *"Principal Cloud Architect with experience designing AWS, Azure, and GCP infrastructures using Terraform, Docker, and Kubernetes..."*
- **Root Cause**:
  1. **Class Imbalance in Baseline Training Set**: The baseline model artifact was trained on an early dataset where `Cloud Computing` was severely under-represented compared to `DevOps`.
  2. **High Feature Overlap**: Cloud architecture resumes heavily feature terms like `AWS`, `Terraform`, `Kubernetes`, `Docker`, `CI/CD`, and `Linux`, which the baseline model's TF-IDF vectorizer strongly associated with `DevOps`.
- **Remediation Strategy for Phase 21G/21H**:
  - Apply explicit `class_weight='balanced'` in candidate classifiers.
  - Introduce sublinear TF-IDF scaling and word/char n-gram feature combinations to capture explicit phrases like `cloud solutions architect`, `aws cloudformation`, `gcp serverless`, and `multi-cloud`.

---

### Pattern 2: `Data Science` Misclassified as `DevOps` or `Web Development` (12 Errors)
- **Sample Excerpt**: *"Senior Machine Learning Engineer building REST API data pipelines in Python, Docker, and MLflow..."*
- **Root Cause**:
  1. **MLOps Terminology Confusion**: Modern Data Science resumes include software engineering skills (`Docker`, `Git`, `REST APIs`, `FastAPI`, `Flask`).
  2. **Feature Weight Weighting**: Terms like `API`, `Docker`, and `Python` pull the prediction towards `DevOps` or `Web Development`.
- **Remediation Strategy**:
  - Boost n-gram range to `(1, 2)` or `(1, 3)` to ensure domain-specific compounds like `deep learning`, `machine learning`, `pytorch model`, and `data analysis` receive higher feature priority.

---

### Pattern 3: `Cybersecurity` Misclassified as `Web Development` or `Cloud Computing` (8 Errors)
- **Sample Excerpt**: *"Cybersecurity analyst inspecting web application vulnerabilities, SSL/TLS certificates, and WAF rules..."*
- **Root Cause**:
  1. **Web App Security Overlap**: Security resumes focusing on OWASP top 10, penetration testing of web applications, and HTTPS certificates contain high frequencies of web vocabulary (`HTTP`, `REST`, `SSL`, `Web`).
- **Remediation Strategy**:
  - Retain sublinear TF-IDF scaling and introduce character n-grams to capture security-specific acronyms (`siem`, `penetration`, `wireshark`, `metasploit`, `cissp`).

---

## 🎯 Summary of Insights for Model Experiments (Phase 21G)

1. **Class Weighting is Mandatory**: The 0% recall on `Cloud Computing` in the baseline model is primarily caused by class imbalance. Models in Phase 21G must use balanced class weights or resampled class distributions.
2. **Sublinear TF & N-Gram Refinement**: Using `sublinear_tf=True` and expanding n-grams will reduce the disproportionate impact of common software keywords (`Python`, `API`, `Git`).

---

*Phase 21F Error Analysis complete. Awaiting user approval to proceed to Phase 21G (Model Experiments).*
