# 🏆 Phase 21K: Final Untouched Test Set Evaluation Report

This document records the official evaluation of the selected candidate ML classifier ([`LinearSVC`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/scripts/run_model_experiments.py) with `CalibratedClassifierCV`) evaluated **EXACTLY ONCE** on the 100% untouched **TEST dataset** (`ml/data/processed/test.csv`, 278 records).

---

## 📊 Summary of Final Test Metrics

| Evaluation Metric | Baseline Production Model | Selected Calibrated Model (v2) | Absolute Improvement |
| :--- | :---: | :---: | :---: |
| **Test Accuracy** | 87.00% | **97.84%** | **+10.84%** |
| **Macro Precision** | 0.7076 | **0.9840** | **+0.2764** |
| **Macro Recall** | 0.7254 | **0.9783** | **+0.2529** |
| **Macro F1 Score** | 0.7066 | **0.9810** | **+0.2744 (+27.44%)** |
| **Weighted Precision** | 0.8593 | **0.9787** | **+0.1194** |
| **Weighted Recall** | 0.8700 | **0.9784** | **+0.1084** |
| **Weighted F1 Score** | 0.8560 | **0.9784** | **+0.1224** |

---

## 📋 Per-Class Performance on Untouched Test Set (278 Records)

| Target Production Class | Support Count | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Cloud Computing** | 14 | **1.0000** | **1.0000** | **1.0000** | **Fully Resolved** (0% recall in baseline -> 100% recall). |
| **Cybersecurity** | 56 | **0.9821** | **0.9821** | **0.9821** | Near-perfect class separation. |
| **Data Science** | 62 | **1.0000** | **0.9677** | **0.9836** | Perfect precision (0 false positives). |
| **DevOps** | 41 | **0.9750** | **0.9512** | **0.9630** | High precision and recall. |
| **Web Development** | 105 | **0.9630** | **0.9905** | **0.9765** | Dominant class handled without overwhelming small classes. |

---

## 🧩 Test Set Confusion Matrix

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

## 💾 Saved Artifacts

- **JSON Test Metrics**: [`reports/final_test_metrics.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/final_test_metrics.json)
- **Untouched Test Dataset**: [`ml/data/processed/test.csv`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/data/processed/test.csv) (278 records)

---

*Phase 21K Untouched Test Evaluation complete. Macro F1 = 0.9810.*
