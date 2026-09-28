import joblib, json, os
import pandas as pd
import numpy as np

print('=== PHASE 24: OOD THRESHOLD SELECTION & ABSTENTION VALIDATION ENGINE ===')

# Load Candidate Model v2
m2_path = 'ml/artifacts/model_v2.joblib'
m2_obj = joblib.load(m2_path)
model = m2_obj['pipeline']
classes = list(model.classes_)

def compute_signals(text):
    if not isinstance(text, str) or not text.strip():
        return {
            'pred_class': 'UNMAPPED',
            'max_conf': 0.0,
            'margin': 0.0,
            'entropy': float(-np.sum([0.2 * np.log2(0.2)] * 5)),
            'text_len': 0
        }
    proba = model.predict_proba([text])[0]
    sorted_p = np.sort(proba)[::-1]
    max_conf = float(sorted_p[0])
    margin = float(sorted_p[0] - sorted_p[1])
    clipped_p = np.clip(proba, 1e-12, 1.0)
    entropy = float(-np.sum(clipped_p * np.log2(clipped_p)))
    pred_class = classes[np.argmax(proba)]
    return {
        'pred_class': str(pred_class),
        'max_conf': max_conf,
        'margin': margin,
        'entropy': entropy,
        'text_len': len(text)
    }

# 1. LOAD DATASETS FOR STAGE 1 (DEVELOPMENT & THRESHOLD SELECTION)
print('\n--- STAGE 1: Development Data Loading (val.csv + OOD Dev Data) ---')
df_val = pd.read_csv('ml/data/processed/val.csv')
val_records = []
for idx, row in df_val.iterrows():
    sig = compute_signals(row['Text'])
    sig['mapped_category'] = row['Mapped_Category']
    val_records.append(sig)
df_val_sigs = pd.DataFrame(val_records)
print(f"Validation In-Domain Dataset (val.csv): {len(df_val_sigs)} records")

# Load OOD Development Data (Accountant OCR N=283 + Phase 23D OCR N=34)
df_ocr = pd.read_csv('ml/data/raw/ocr_results.csv')
ood_dev_records = []
for idx, row in df_ocr.iterrows():
    sig = compute_signals(row['Text'])
    sig['source'] = 'accountant_ocr'
    ood_dev_records.append(sig)

with open('reports/phase23d_ocr_results.json', 'r') as f:
    pdf_ocr = json.load(f)

for row in pdf_ocr:
    probs = list(row['probabilities'].values())
    if probs and sum(probs) > 0:
        sp = np.sort(probs)[::-1]
        mc = float(sp[0])
        mg = float(sp[0] - sp[1])
        cp = np.clip(probs, 1e-12, 1.0)
        ent = float(-np.sum(cp * np.log2(cp)))
        pc = row['predicted_class']
    else:
        mc, mg, ent, pc = 0.0, 0.0, 2.3219, 'UNMAPPED'
    ood_dev_records.append({
        'pred_class': pc,
        'max_conf': mc,
        'margin': mg,
        'entropy': ent,
        'text_len': row['extracted_char_count'],
        'source': 'independent_pdf_ocr'
    })

df_ood_dev = pd.DataFrame(ood_dev_records)
print(f"OOD Development Population: {len(df_ood_dev)} records ({len(df_ocr)} Accountant + 34 Independent OCR)")

# 2. FINE THRESHOLD GRID SWEEP ON VAL DATA
print('\n--- Fine Grid Threshold Sweep (Max Confidence, Margin, Entropy) ---')
conf_grid = np.arange(0.50, 1.00, 0.01)
sweep_results = []

for c_thresh in conf_grid:
    val_cov = (df_val_sigs['max_conf'] >= c_thresh).mean() * 100.0
    val_rej = (df_val_sigs['max_conf'] < c_thresh).mean() * 100.0
    
    ood_rej = (df_ood_dev['max_conf'] < c_thresh).mean() * 100.0
    ood_acc = (df_ood_dev['max_conf'] >= c_thresh).mean() * 100.0
    
    sweep_results.append({
        'signal': 'max_confidence',
        'threshold': round(float(c_thresh), 2),
        'val_in_domain_coverage_pct': val_cov,
        'val_in_domain_rejection_pct': val_rej,
        'ood_dev_rejection_pct': ood_rej,
        'ood_dev_acceptance_pct': ood_acc
    })

df_sweep = pd.DataFrame(sweep_results)
os.makedirs('reports', exist_ok=True)
df_sweep.to_csv('reports/phase24_threshold_validation.csv', index=False)

# 3. IDENTIFY FROZEN CANDIDATE OPERATING POINTS ON VAL DATA
print('\n--- Selection of Candidate Operating Points on Validation Data ---')
op_candidates = {}

# OP-1: High Coverage Constraint (val in-domain coverage >= 95%)
op1_df = df_sweep[df_sweep['val_in_domain_coverage_pct'] >= 95.0]
op1 = op1_df.iloc[-1] # highest threshold satisfying constraint
op_candidates['OP-1 (High Coverage >=95%)'] = {
    'signal': 'max_confidence',
    'threshold': float(op1['threshold']),
    'val_coverage_pct': float(op1['val_in_domain_coverage_pct']),
    'val_rejection_pct': float(op1['val_in_domain_rejection_pct']),
    'ood_dev_rejection_pct': float(op1['ood_dev_rejection_pct']),
    'ood_dev_acceptance_pct': float(op1['ood_dev_acceptance_pct'])
}

# OP-2: Balanced Coverage Constraint (val in-domain coverage >= 90%)
op2_df = df_sweep[df_sweep['val_in_domain_coverage_pct'] >= 90.0]
op2 = op2_df.iloc[-1]
op_candidates['OP-2 (Balanced Coverage >=90%)'] = {
    'signal': 'max_confidence',
    'threshold': float(op2['threshold']),
    'val_coverage_pct': float(op2['val_in_domain_coverage_pct']),
    'val_rejection_pct': float(op2['val_in_domain_rejection_pct']),
    'ood_dev_rejection_pct': float(op2['ood_dev_rejection_pct']),
    'ood_dev_acceptance_pct': float(op2['ood_dev_acceptance_pct'])
}

# OP-3: High OOD Rejection Constraint (ood rejection >= 85%)
op3_df = df_sweep[df_sweep['ood_dev_rejection_pct'] >= 85.0]
op3 = op3_df.iloc[0] # lowest threshold satisfying constraint
op_candidates['OP-3 (High OOD Rejection >=85%)'] = {
    'signal': 'max_confidence',
    'threshold': float(op3['threshold']),
    'val_coverage_pct': float(op3['val_in_domain_coverage_pct']),
    'val_rejection_pct': float(op3['val_in_domain_rejection_pct']),
    'ood_dev_rejection_pct': float(op3['ood_dev_rejection_pct']),
    'ood_dev_acceptance_pct': float(op3['ood_dev_acceptance_pct'])
}

# OP-4: Strict OOD Rejection Constraint (ood rejection >= 95%)
op4_df = df_sweep[df_sweep['ood_dev_rejection_pct'] >= 95.0]
op4 = op4_df.iloc[0]
op_candidates['OP-4 (Strict OOD Rejection >=95%)'] = {
    'signal': 'max_confidence',
    'threshold': float(op4['threshold']),
    'val_coverage_pct': float(op4['val_in_domain_coverage_pct']),
    'val_rejection_pct': float(op4['val_in_domain_rejection_pct']),
    'ood_dev_rejection_pct': float(op4['ood_dev_rejection_pct']),
    'ood_dev_acceptance_pct': float(op4['ood_dev_acceptance_pct'])
}

for name, info in op_candidates.items():
    print(f"\nCandidate {name}: Threshold={info['threshold']}")
    print(f"  Val Coverage: {info['val_coverage_pct']:.1f}% | Val Rejection: {info['val_rejection_pct']:.1f}%")
    print(f"  OOD Dev Rejection: {info['ood_dev_rejection_pct']:.1f}% | OOD Acceptance: {info['ood_dev_acceptance_pct']:.1f}%")

with open('reports/phase24_operating_points.json', 'w') as f:
    json.dump(op_candidates, f, indent=2)

# 4. STAGE 2: FROZEN TEST EVALUATION ON UNTOUCHED TEST.CSV (N=278)
print('\n--- STAGE 2: Frozen Operating Point Evaluation on test.csv (N=278) ---')
df_test = pd.read_csv('ml/data/processed/test.csv')
test_records = []
for idx, row in df_test.iterrows():
    sig = compute_signals(row['Text'])
    sig['mapped_category'] = row['Mapped_Category']
    test_records.append(sig)
df_test_sigs = pd.DataFrame(test_records)
print(f"Untouched Test Set (test.csv): {len(df_test_sigs)} records")

test_frozen_eval = {}
for op_name, op_info in op_candidates.items():
    tau = op_info['threshold']
    t_cov = (df_test_sigs['max_conf'] >= tau).mean() * 100.0
    t_rej = (df_test_sigs['max_conf'] < tau).mean() * 100.0
    
    test_frozen_eval[op_name] = {
        'threshold': tau,
        'test_in_domain_coverage_pct': t_cov,
        'test_in_domain_rejection_pct': t_rej,
        'val_in_domain_coverage_pct': op_info['val_coverage_pct'],
        'coverage_delta_pct': t_cov - op_info['val_coverage_pct']
    }
    print(f"{op_name} (Tau={tau}): Test Coverage = {t_cov:.2f}% | Test Rejection = {t_rej:.2f}% (Val Coverage = {op_info['val_coverage_pct']:.2f}%)")

with open('reports/phase24_test_frozen_evaluation.json', 'w') as f:
    json.dump(test_frozen_eval, f, indent=2)

# 5. CLASS-CONDITIONAL COVERAGE ANALYSIS (val.csv + test.csv)
print('\n--- Class-Conditional Coverage Analysis ---')
class_cond_rows = []

for op_name, op_info in op_candidates.items():
    tau = op_info['threshold']
    
    # Class breakdown on validation set
    for cls, grp in df_val_sigs.groupby('mapped_category'):
        c_cov = (grp['max_conf'] >= tau).mean() * 100.0
        c_rej = (grp['max_conf'] < tau).mean() * 100.0
        class_cond_rows.append({
            'operating_point': op_name,
            'split': 'val.csv',
            'canonical_class': cls,
            'sample_count': len(grp),
            'coverage_pct': c_cov,
            'rejection_pct': c_rej
        })
        
    # Class breakdown on test set
    for cls, grp in df_test_sigs.groupby('mapped_category'):
        c_cov = (grp['max_conf'] >= tau).mean() * 100.0
        c_rej = (grp['max_conf'] < tau).mean() * 100.0
        class_cond_rows.append({
            'operating_point': op_name,
            'split': 'test.csv',
            'canonical_class': cls,
            'sample_count': len(grp),
            'coverage_pct': c_cov,
            'rejection_pct': c_rej
        })

df_class_cond = pd.DataFrame(class_cond_rows)
df_class_cond.to_csv('reports/phase24_class_conditional_coverage.csv', index=False)

print('\nClass-Conditional Coverage for OP-2 (Threshold = 0.88, Balanced Coverage >=90%):')
print(df_class_cond[(df_class_cond['operating_point'].str.contains('OP-2')) & (df_class_cond['split'] == 'test.csv')][['canonical_class', 'sample_count', 'coverage_pct', 'rejection_pct']].to_string(index=False))

print('\nPhase 24 validation engine completed successfully!')
print('Saved artifacts:')
print('  - reports/phase24_threshold_validation.csv')
print('  - reports/phase24_operating_points.json')
print('  - reports/phase24_test_frozen_evaluation.json')
print('  - reports/phase24_class_conditional_coverage.csv')
