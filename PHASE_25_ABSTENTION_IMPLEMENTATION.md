# PHASE 25 — CONTROLLED OOD / ABSTENTION LAYER IMPLEMENTATION

**Project**: Resume Intel  
**Author**: Senior ML Systems & Reliability Engineer  
**Date**: September 27, 2026  
**Status**: Implementation & Verification Complete — STOP Condition Reached  

---

## 1. EXISTING CLASSIFICATION ARCHITECTURE

Prior to Phase 25, the application passed extracted resume text directly into the trained model pipeline (`model_v2.joblib` / `model_latest.joblib`), which assigned one of five canonical domain classes (`Data Science`, `Web Development`, `Cloud Computing`, `DevOps`, `Cybersecurity`) based solely on argmax class probability. If top class confidence fell below 0.45, it was assigned a "low" label, but no formal abstention layer existed to flag out-of-domain (OOD) non-technical resumes or control automatic candidate classification.

```
Resume PDF → PDF Text Extraction → Classification Service → Argmax Class → Final Output
```

---

## 2. NEW ABSTENTION ARCHITECTURE

Phase 25 introduces a non-destructive, auditable **Out-Of-Domain (OOD) / Abstention Policy Layer** wrapper around the inference service.

```
Resume PDF
    │
    ▼
PDF Text Extraction
    │
    ▼
Existing Classifier (model_v2.joblib)
    │
    ▼
Raw Prediction (predicted_class, top_probability, all_probabilities)
    │
    ▼
OOD Policy Engine (app.services.ood_policy)
    │
    ├─────► [Confidence ≥ 0.85] ──► ACCEPT (status="accepted", ood_status="in_domain_like")
    │
    └─────► [Confidence < 0.85] ──► REVIEW / ABSTAIN (status="review", ood_status="possible_out_of_domain")
```

> [!IMPORTANT]
> **Non-Destructive Design**: The abstention layer wraps the classifier without replacing or modifying `model_v2.joblib`. When the system abstains (`status: "review"`), the original `predicted_class` is **retained internally** for auditability and manual recruiter review.

---

## 3. POLICY CONFIGURATION

The OOD policy configuration is managed centrally via Pydantic settings in `backend/app/config.py`:

```python
# backend/app/config.py
ood_enabled: bool = True
ood_confidence_threshold: float = 0.85  # Frozen Phase 24 OP-4 operating point
ood_policy_version: str = "v1.0-phase24-op4"
```

The operating point ($\tau = 0.85$) is derived directly from the **frozen Phase 24 OP-4 candidate** (which achieved 91.01% untouched test coverage and 96.85% OOD dev rejection).

The policy instance is represented by `OODPolicy` in `backend/app/services/ood_policy.py`:

```python
@dataclass
class OODPolicy:
    confidence_threshold: float = 0.85
    entropy_threshold: Optional[float] = None
    margin_threshold: Optional[float] = None
    policy_version: str = "v1.0-phase24-op4"
    enabled: bool = True
```

---

## 4. DECISION LOGIC

The decision logic implemented in `evaluate_ood_policy(...)` follows a simple, auditable rule:

```python
if not policy.enabled:
    status = "accepted"
    ood_status = "in_domain_like"
    review_required = False
    reason = "ood_policy_disabled"

elif predicted_class is None or confidence is None:
    status = "review"
    ood_status = "possible_out_of_domain"
    review_required = True
    reason = "input_empty_or_model_unavailable"

elif confidence >= policy.confidence_threshold:
    status = "accepted"
    ood_status = "in_domain_like"
    review_required = False
    reason = "confidence_above_configured_threshold"

else:
    status = "review"
    ood_status = "possible_out_of_domain"
    review_required = True
    reason = "confidence_below_configured_threshold"
```

> [!CAUTION]
> **Strict Semantic Rule**: Abstention does **NOT** mean candidate rejection. In accordance with Phase 25 instructions, abstention indicates: *"The classifier does not have sufficient evidence to assign a supported category automatically."* The UI and API report `"Needs Manual Review"`, never `"Candidate Rejected"`.

---

## 5. API CHANGES

The classification result schema was updated backward-compatibly in `backend/app/services/classification_service.py` and Pydantic schemas in `backend/app/schemas/resume.py`:

### Sample ACCEPT Response (`POST /api/v1/resumes/upload` / `ClassificationResult`)
```json
{
  "predicted_domain": "Data Science",
  "confidence_label": "high",
  "top_probability": 0.9412,
  "status": "accepted",
  "ood_status": "in_domain_like",
  "review_required": false,
  "policy_version": "v1.0-phase24-op4",
  "reason": "confidence_above_configured_threshold"
}
```

### Sample ABSTAIN / REVIEW Response
```json
{
  "predicted_domain": "Web Development",
  "confidence_label": "medium",
  "top_probability": 0.7830,
  "status": "review",
  "ood_status": "possible_out_of_domain",
  "review_required": true,
  "policy_version": "v1.0-phase24-op4",
  "reason": "confidence_below_configured_threshold"
}
```

---

## 6. DATABASE CHANGES

The SQLAlchemy ORM `Resume` model in `backend/app/models/resume.py` was updated with nullable fields to persist OOD policy decisions without breaking existing schemas:

```python
# OOD Policy & Abstention Layer fields (Phase 25)
classification_status: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "accepted" | "review"
review_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
ood_status: Mapped[str | None] = mapped_column(String(64), nullable=True)             # "in_domain_like" | "possible_out_of_domain"
policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
policy_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
```

When `review_required` is `True`, the overall resume processing status is set to `ProcessingStatus.NEEDS_REVIEW`.

---

## 7. UI CHANGES

In the Streamlit frontend (`frontend/views/upload.py`), when a resume is flagged with `review_required=True` / `status="needs_review"`, the banner displays:

> ⚠️ **Needs Manual Review**: Classification confidence is below the configured automatic-classification threshold.

No candidate rejection language exists in the UI.

---

## 8. TESTS ADDED

A dedicated test suite [`backend/tests/test_ood_policy.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/tests/test_ood_policy.py) was added with 8 comprehensive unit tests:

1. `test_ood_policy_config_loading`: Verifies settings loading from `Settings`.
2. `test_high_confidence_in_domain_accept`: Verifies high confidence ($\ge 0.85$) produces `status="accepted"`.
3. `test_below_threshold_abstain_review`: Verifies below-threshold confidence ($< 0.85$) produces `status="review"`.
4. `test_exactly_at_threshold_behavior`: Verifies exact boundary condition (confidence $= 0.85$) produces `status="accepted"`.
5. `test_empty_input_preserves_error_behavior`: Verifies empty input produces safe review decision.
6. `test_original_predicted_class_retained_when_abstaining`: Verifies `predicted_domain` is preserved when abstaining.
7. `test_api_response_backward_compatibility`: Verifies schema backward compatibility.
8. `test_disabled_ood_policy_accepts_all`: Verifies policy bypass when disabled.

---

## 9. REGRESSION RESULTS

The full backend pytest test suite was executed:

```
====================== 147 passed, 51 warnings in 35.60s ======================
```

- **0 test failures**
- **100% pass rate** across all 147 unit and integration tests (139 existing + 8 new Phase 25 tests).

---

## 10. MODEL INTEGRITY & REGRESSION CHECK

### A. SHA-256 Hash Integrity (Pre vs Post Phase 25)

| Artifact Path | Pre-Phase 25 SHA-256 Hash | Post-Phase 25 SHA-256 Hash | Integrity Status |
| :--- | :--- | :--- | :---: |
| `ml/artifacts/model_latest.joblib` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | `0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb` | **MATCH** |
| `ml/artifacts/model_v2.joblib` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | `6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4` | **MATCH** |
| `ml/data/processed/train.csv` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | `24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0` | **MATCH** |
| `ml/data/processed/val.csv` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | `ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6` | **MATCH** |
| `ml/data/processed/test.csv` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | `10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4` | **MATCH** |

### B. Untouched Classifier Output Regression

Inference on `test.csv` ($N=278$) confirmed that the underlying classifier outputs (`predicted_class`, class probabilities) are 100% identical before and after Phase 25. The abstention policy wraps the prediction output without altering classifier decision boundaries.

---

## 11. SECURITY CONSIDERATIONS

- **PII Protection**: Log messages in `classification_service.py` track only scalar metadata (`domain`, `probability`, `status`, `review_required`, `policy_version`, `reason`). Raw resume text, email addresses, and phone numbers are never logged.
- **Auditability**: Every decision records `policy_version` and `policy_reason` to provide a complete audit trail for compliance auditing.

---

## 12. KNOWN LIMITATIONS

1. **Not a Full Production OOD Classifier**: The abstention policy is a threshold guardrail on classifier softmax confidence. It does not train a secondary generative or isolation-forest OOD detector.
2. **Class Sensitivity**: As established in Phase 24, applying a global $\tau = 0.85$ threshold slightly reduces `Data Science` automatic coverage (87.1% on test set) compared to `Cloud Computing` (100%).

---

## 13. STOP CONDITION ACKNOWLEDGED

Phase 25 is complete:
- Policy engine implemented in [`backend/app/services/ood_policy.py`](file:///c:/Users/pinak/Desktop/RESUME_SCREENIG/backend/app/services/ood_policy.py).
- Service, DB models, API schemas, and UI updated backward-compatibly.
- 147/147 tests passing cleanly.
- Model artifacts and datasets remain 100% unchanged (SHA-256 verified).

**Execution stopped. Awaiting explicit user approval before proceeding.**
