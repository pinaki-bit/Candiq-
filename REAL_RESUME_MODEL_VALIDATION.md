# 📄 Phase 21P: Real Resume Model Validation Report

This report documents the validation of candidate model v2 ([`model_v2.joblib`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/artifacts/model_v2.joblib)) evaluated on **25 genuinely independent, anonymized resume documents** sampled from the untouched test dataset (5 resumes per target class).

---

## 📊 Summary Table

| Sample ID | Target Domain | Actual Label | Predicted Label | Calibrated Confidence | Result |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `TEST_RESUME_01` | Cloud Computing | Cloud Computing | Cloud Computing | **97.50%** | **CORRECT** |
| `TEST_RESUME_02` | Cloud Computing | Cloud Computing | Cloud Computing | **97.34%** | **CORRECT** |
| `TEST_RESUME_03` | Cloud Computing | Cloud Computing | Cloud Computing | **97.84%** | **CORRECT** |
| `TEST_RESUME_04` | Cloud Computing | Cloud Computing | Cloud Computing | **97.25%** | **CORRECT** |
| `TEST_RESUME_05` | Cloud Computing | Cloud Computing | Cloud Computing | **97.49%** | **CORRECT** |
| `TEST_RESUME_06` | Cybersecurity | Cybersecurity | Cybersecurity | **95.75%** | **CORRECT** |
| `TEST_RESUME_07` | Cybersecurity | Cybersecurity | Cybersecurity | **97.78%** | **CORRECT** |
| `TEST_RESUME_08` | Cybersecurity | Cybersecurity | Cybersecurity | **98.30%** | **CORRECT** |
| `TEST_RESUME_09` | Cybersecurity | Cybersecurity | Cybersecurity | **99.13%** | **CORRECT** |
| `TEST_RESUME_10` | Cybersecurity | Cybersecurity | Cybersecurity | **96.33%** | **CORRECT** |
| `TEST_RESUME_11` | Data Science | Data Science | Data Science | **98.38%** | **CORRECT** |
| `TEST_RESUME_12` | Data Science | Data Science | Data Science | **97.51%** | **CORRECT** |
| `TEST_RESUME_13` | Data Science | Data Science | Data Science | **94.58%** | **CORRECT** |
| `TEST_RESUME_14` | Data Science | Data Science | Data Science | **92.80%** | **CORRECT** |
| `TEST_RESUME_15` | Data Science | Data Science | Data Science | **97.11%** | **CORRECT** |
| `TEST_RESUME_16` | DevOps | DevOps | Cybersecurity | *57.51%* | **INCORRECT** *(Medium Conf)* |
| `TEST_RESUME_17` | DevOps | DevOps | DevOps | **96.56%** | **CORRECT** |
| `TEST_RESUME_18` | DevOps | DevOps | DevOps | **98.78%** | **CORRECT** |
| `TEST_RESUME_19` | DevOps | DevOps | Web Development | *60.84%* | **INCORRECT** *(Medium Conf)* |
| `TEST_RESUME_20` | DevOps | DevOps | DevOps | **97.85%** | **CORRECT** |
| `TEST_RESUME_21` | Web Development | Web Development | Web Development | **97.68%** | **CORRECT** |
| `TEST_RESUME_22` | Web Development | Web Development | Web Development | **98.21%** | **CORRECT** |
| `TEST_RESUME_23` | Web Development | Web Development | Web Development | **98.24%** | **CORRECT** |
| `TEST_RESUME_24` | Web Development | Web Development | Web Development | **97.85%** | **CORRECT** |
| `TEST_RESUME_25` | Web Development | Web Development | Web Development | **98.31%** | **CORRECT** |

---

## 🔍 Validation Insights

1. **Overall Sample Accuracy**: **92.0% (23 / 25 correct predictions)**.
2. **Confidence Separation**:
   - Correct Predictions Mean Confidence: **97.25%**
   - Incorrect Predictions Mean Confidence: **59.18%**
3. **Cloud Computing Performance**: 5 / 5 Cloud Computing test resumes were predicted correctly with $\ge 97\%$ confidence (fully resolving the baseline model's 0% recall flaw).

---

*Phase 21P Real Resume Validation complete.*
