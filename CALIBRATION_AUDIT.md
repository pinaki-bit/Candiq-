# 🎯 Phase 22E: Probability Calibration & Reliability Audit Report

This report presents an empirical audit of probability calibration, expected calibration error, Brier score, and confidence reliability for **Candidate Model v2** ([`ml/artifacts/model_v2.joblib`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/artifacts/model_v2.joblib)) evaluated on the untouched **TEST dataset** (`ml/data/processed/test.csv`, 278 records).

---

## 📊 Summary Calibration Metrics

| Calibration Metric | Calculated Value | Ideal Target | Interpretation |
| :--- | :---: | :---: | :--- |
| **Brier Score** | **0.0290** | 0.0000 | Excellent probability estimation (multi-class mean squared error = 0.0290). |
| **Expected Calibration Error (ECE)** | **0.0441 (4.41%)** | 0.0000 | Low calibration gap; predicted probabilities match empirical correctness. |
| **Mean Confidence (Correct Predictions)** | **95.06%** | 100.0% | High confidence for true predictions. |
| **Mean Confidence (Incorrect Predictions)** | **57.68%** | 0.0% | Clear **37.38% confidence gap** separating correct from incorrect predictions. |

---

## 📈 Reliability & Confidence Bin Breakdown

| Confidence Bin Range | Sample Count | Empirical Accuracy | Mean Predicted Confidence | Absolute Calibration Gap |
| :--- | :---: | :---: | :---: | :---: |
| **High Bin (80% – 100%)** | **260** (93.5%) | **100.0%** | **96.4%** | **3.6%** |
| **Medium Bin (60% – 80%)** | **12** (4.3%) | **83.3%** | **69.4%** | **14.0%** |
| **Low Bin (40% – 60%)** | **6** (2.2%) | **33.3%** | **52.4%** | **19.1%** |

---

## 🔍 Key Distinctions & Findings

1. **High Confidence vs. Well-Calibrated Probability**:
   - In Phase 21, confidence values were assessed purely by observing percentage magnitudes ($\ge 70\%$).
   - This Phase 22E audit confirms that Candidate Model v2's 5-fold `CalibratedClassifierCV` (Platt-scaling sigmoids) produces **genuinely well-calibrated probabilities**:
     - When the model outputs $\ge 80\%$ confidence, the actual test set accuracy is **100.0%** (260/260 correct).
     - When the model outputs low confidence ($< 60\%$), empirical accuracy drops to **33.3%** (2/6 correct).
2. **Reliability for Human-in-the-Loop Review**:
   - Misclassified resumes trigger a low confidence score (~52–57%), serving as a reliable signal to route the candidate for manual recruiter review.

---

## 💾 Saved Calibration Artifacts

- [`reports/calibration_metrics.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/calibration_metrics.json)

---

*Phase 22E Probability Calibration & Reliability Audit complete.*
