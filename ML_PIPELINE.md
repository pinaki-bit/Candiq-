# 🧠 Resume Intel: Machine Learning Pipeline Architecture

This document details the complete end-to-end Machine Learning and Natural Language Processing (NLP) pipeline architecture for domain classification in **Resume Intel**.

---

## 🛠️ End-to-End Pipeline Architecture

```
┌─────────────────────────┐
│ Raw Resume Datasets     │ (37,000+ records across CSV/JSONL)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Label Normalization     │ (shared/label_mapping.json)
│ & Defensible Mapping    │ (Filters non-tech labels, maps to 5 canonical domains)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Data Quality & Cleaning │ (HTML stripping, whitespace normalization,
│ & Deduplication         │  exact & near-duplicate purging -> 1,848 clean records)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Stratified Splitting    │ (70% Train [1,293], 15% Val [277], 15% Test [278])
│ (Zero Data Leakage)     │ (Test set kept untouched until final evaluation)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Feature Extraction      │ (TfidfVectorizer: word unigrams, min_df=2,
│ & Tokenization          │  max_features=50,000)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Calibrated LinearSVC    │ (C=0.1, class_weight='balanced', max_iter=2000)
│ Classification Model    │ (CalibratedClassifierCV 5-fold Platt sigmoids)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Production Inference    │ (predict(resume_text) -> ClassificationResult)
│ REST API Interface      │ (Returns predicted_domain, confidence_label, all_probs)
└─────────────────────────┘
```

---

## 📊 Pipeline Stages Detailed

### 1. Dataset Acquisition & Scope
- **Sources**: Kaggle Resume Datasets (`resumes.csv` & `resumes_dataset.jsonl`).
- **Target Domains (5 Classes)**: `Data Science`, `Web Development`, `Cloud Computing`, `DevOps`, `Cybersecurity`.

### 2. Label Mapping & Filtering
- Explicit mapping defined in [`shared/label_mapping.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/shared/label_mapping.json).
- Granular tech roles mapped (e.g. `React Developer` -> `Web Development`, `Machine Learning Engineer` -> `Data Science`, `Cloud Engineer` -> `Cloud Computing`).
- Ambiguous/general roles (`Python Developer`, `SQL Developer`, `Accountant`, `Sales`) marked `UNMAPPED` to eliminate class contamination.

### 3. Data Hygiene & Deduplication
- **Deduplication**: 916 exact text duplicates and 55 near-duplicates removed.
- **Normalization**: HTML stripping, ligature replacement, line collapsing.
- **Clean Dataset**: 1,848 unique clean resumes saved to `ml/data/processed/clean_mapped_resumes.csv`.

### 4. Stratified Data Splitting
- **Train (70%)**: 1,293 records.
- **Validation (15%)**: 277 records (used for hyperparameter tuning).
- **Test (15%)**: 278 records (kept 100% untouched until final evaluation).

### 5. Feature Engineering & Vectorization
- **Vectorization**: `TfidfVectorizer(ngram_range=(1, 1), min_df=2, max_features=50000)`.
- **Character N-Grams Rejection**: FeatureUnion with character n-grams was evaluated but rejected due to a 20x latency penalty (11.6s vs 0.5s) with no Macro F1 gain.

### 6. Model Selection & Probability Calibration
- **Classifier**: `LinearSVC(C=0.1, class_weight='balanced', max_iter=2000)`.
- **Calibration**: `CalibratedClassifierCV(cv=5)` produces smooth, well-calibrated class probabilities ($P(\text{class} | \text{text})$).

### 7. Evaluation & Production Results
- **Validation Macro F1**: `0.9889`
- **Untouched Test Macro F1**: `0.9810` (**+27.44% improvement over 0.7066 baseline**)
- **Cloud Computing Recall**: `1.00 (100%)` (resolves 0% baseline recall flaw)
- **High Confidence Rate ($\ge 70\%$)**: 95.3% on test predictions.

---

## 💾 Model Artifacts & Production Compatibility

- **Serialized Artifact**: [`ml/artifacts/model_v2.joblib`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/artifacts/model_v2.joblib)
- **Metadata**: [`ml/artifacts/model_metadata.json`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/ml/artifacts/model_metadata.json)
- **Production Safety**: Existing model `model_latest.joblib` remains preserved. The candidate model `model_v2.joblib` has been verified via 7 regression tests ([`test_model_v2_regression.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/tests/test_model_v2_regression.py)) and maintains 100% schema compatibility with the production `predict(resume_text)` interface.
