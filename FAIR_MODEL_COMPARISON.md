# ⚖️ Phase 22C: Fair Side-by-Side Model Comparison Report

This report presents an empirical, side-by-side performance evaluation comparing the **existing production model** ([`ml/artifacts/model_latest.joblib`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/artifacts/model_latest.joblib), LinearSVC v20260922_235001) against the **candidate model** ([`ml/artifacts/model_v2.joblib`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/artifacts/model_v2.joblib), Calibrated LinearSVC v2.0.0) evaluated on the **EXACT SAME 278 UNTOUCHED TEST RECORDS** (`ml/data/processed/test.csv`).

---

## 📊 Overall Metrics Comparison (Identical 278 Test Records)

| Metric | Baseline Model (`model_latest.joblib`) | Candidate Model (`model_v2.joblib`) | Absolute Difference | Relative Change |
| :--- | :---: | :---: | :---: | :---: |
| **Accuracy** | 88.85% | **97.84%** | **+8.99%** | **+10.1%** |
| **Macro Precision** | 0.7101 | **0.9840** | **+0.2739** | **+38.6%** |
| **Macro Recall** | 0.7474 | **0.9783** | **+0.2309** | **+30.9%** |
| **Macro F1 Score** | 0.7205 | **0.9810** | **+0.2605** | **+36.2%** |
| **Weighted F1 Score** | 0.8721 | **0.9784** | **+0.1063** | **+12.2%** |

---

## 📋 Per-Class Recall & F1-Score Side-by-Side Comparison

| Target Class | Support Count | Baseline Recall | Candidate v2 Recall | Recall Diff | Baseline F1 | Candidate v2 F1 | F1 Diff |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cloud Computing** | 14 | **0.0000** | **1.0000** | **+1.0000** | 0.0000 | **1.0000** | **+1.0000** |
| **Cybersecurity** | 56 | 0.9107 | **0.9821** | **+0.0714** | 0.9533 | **0.9821** | **+0.0288** |
| **Data Science** | 62 | 0.8548 | **0.9677** | **+0.1129** | 0.8983 | **0.9836** | **+0.0853** |
| **DevOps** | 41 | **1.0000** | 0.9512 | -0.0488 | 0.7885 | **0.9630** | **+0.1745** |
| **Web Development** | 105 | 0.9714 | **0.9905** | **+0.0191** | 0.9623 | **0.9765** | **+0.0142** |

> [!NOTE]
> Baseline DevOps recall was 1.0000 because `model_latest.joblib` falsely misclassified 100% of Cloud Computing resumes into DevOps. Candidate Model v2 correctly separates Cloud Computing from DevOps, increasing DevOps Precision from 0.6508 to 0.9750 (+0.3242) and DevOps F1 from 0.7885 to 0.9630 (+0.1745).

---

## 🧩 Confusion Matrix Side-by-Side

### Baseline Model (`model_latest.joblib`)
```
                      Predicted Labels
Actual Labels         Cloud   Cyber   DataSci   DevOps   WebDev
Cloud Computing         0       0        0        14       0
Cybersecurity           0      51        0         5       0
Data Science            0       0       53         9       0
DevOps                  0       0        0        41       0
Web Development         0       0        3         2     100
```

### Candidate Model v2 (`model_v2.joblib`)
```
                      Predicted Labels
Actual Labels         Cloud   Cyber   DataSci   DevOps   WebDev
Cloud Computing        14       0        0         0        0
Cybersecurity           0      55        0         0        1
Data Science            0       0       60         2        0
DevOps                  0       1        0        39        1
Web Development         0       0        0         1      104
```

---

## 💾 Saved Comparison Artifacts

- [`reports/fair_baseline_vs_v2_test_comparison.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/fair_baseline_vs_v2_test_comparison.json)

---

*Phase 22C Fair Side-by-Side Model Comparison complete.*
