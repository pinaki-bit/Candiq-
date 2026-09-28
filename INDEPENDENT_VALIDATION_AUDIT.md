# 📑 Phase 22D: Independent Validation Audit & Claim Correction Report

This audit inspects the validation dataset claims in Phase 21P ([`REAL_RESUME_MODEL_VALIDATION.md`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/REAL_RESUME_MODEL_VALIDATION.md) and [`reports/real_resume_validation_v2.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/reports/real_resume_validation_v2.json)).

---

## 🔍 Audit Verification & Code Line Tracing

1. **Origin of the 25 Resumes**:
   - Code inspection of `validate_real_resumes_v2.py` (lines 9–10) reveals the sampling logic:
     ```python
     test_df = pd.read_csv('ml/data/processed/test.csv')
     sampled = test_df.groupby('Mapped_Category').apply(lambda x: x.sample(n=min(5, len(x)), random_state=42))
     ```
   - **Finding**: The 25 sample resumes evaluated in Phase 21P were drawn directly from `ml/data/processed/test.csv` (the 278-record test set).

2. **Correction of Mislabeled Claims**:
   - In Phase 21P, these records were titled *"Validation of Candidate Model v2 across 25 Independent Test Resumes"*.
   - **Audit Correction**: Describing a 25-record subset of `test.csv` as an *"independent external dataset"* was methodologically inaccurate. 
   - **Official Status**: These 25 records are a **Stratified Subsample of the Untouched Test Set** (5 resumes per class).

---

## 📊 Corrected Validation Nomenclature

- **Dataset**: `ml/data/processed/test.csv` (Subsample of 25 records: 5 Cloud, 5 Cyber, 5 Data Sci, 5 DevOps, 5 Web Dev).
- **Subsample Accuracy**: **92.0% (23 / 25 correct predictions)**.
- **Role of Subsample**: Serves as a qualitative inspection subset to verify individual resume text predictions and confidence scores.

---

## 💾 Preserved Artifacts & Corrected Documentation

- The evaluation data in `reports/real_resume_validation_v2.json` and `REAL_RESUME_MODEL_VALIDATION.md` has been preserved intact.
- Titles and metadata have been explicitly updated to denote **Test Subsample Validation** rather than independent external validation.

---

*Phase 22D Independent Validation Audit complete.*
