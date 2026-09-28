# 🎯 Phase 21L: Confidence Calibration & Reliability Analysis Report

This document records the empirical investigation into classifier confidence estimation, probability calibration methods, and reliability metrics for **Resume Intel**.

---

## 🔍 Investigation of Baseline Confidence Flaw

In the Phase 20 Reality Audit, the baseline model (`LinearSVC` without probability calibration) was found to yield uncalibrated raw decision-function values transformed via a simple sigmoid function. 

Because multi-class decision scores were uncalibrated across 5 classes, raw predicted probabilities hovered in the **0.25–0.49** range. Consequently, even correct predictions fell into the `confidence_label="low"` tier because the system threshold `CONFIDENCE_HIGH` was set at `0.70`.

---

## ⚙️ Calibration Methodology & CalibratedClassifierCV Evaluation

To provide statistically sound, well-calibrated confidence probabilities, `CalibratedClassifierCV` (5-fold cross-validation with Platt-scaling Sigmoids) was trained over the `LinearSVC` base pipeline.

### Empirical Calibration Metrics (Evaluated on Untouched Test Set — 278 Records)

| Metric / Dimension | Baseline Model (Uncalibrated) | Calibrated Candidate Model (Platt Sigmoids) |
| :--- | :---: | :---: |
| **Probability Calibration Method** | Sigmoid over `decision_function` | 5-Fold `CalibratedClassifierCV` |
| **Mean Confidence (Correct Predictions)** | 41.2% | **95.06%** |
| **Mean Confidence (Incorrect Predictions)** | 35.4% | **57.68%** |
| **High Confidence ($\ge 70\%$) Count** | 0 / 278 (0.0%) | **265 / 278 (95.3%)** |
| **Medium Confidence (45–70%) Count** | 76 / 278 (27.3%) | **13 / 278 (4.7%)** |
| **Low Confidence ($< 45\%$) Count** | **202 / 278 (72.7%)** | **0 / 278 (0.0%)** |

---

## 📈 Reliability & Separation Analysis

1. **Clean Confidence Separation**: The calibrated model displays a **37.38% confidence gap** between correct predictions (mean 95.06%) and misclassified predictions (mean 57.68%).
2. **Elimination of Artificial Low-Confidence Flags**: 95.3% of test predictions now achieve `confidence_label="high"` ($\ge 0.70$), accurately reflecting the 97.84% test accuracy.
3. **Meaningful Uncertainty Signal**: The remaining 4.7% of predictions fall into `confidence_label="medium"`, providing human recruiters with an accurate signal for human-in-the-loop review.

---

*Phase 21L Confidence Calibration complete.*
