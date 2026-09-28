import joblib, json, os, glob
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc

print('=== PHASE 23E: OUT-OF-DOMAIN DETECTION & ABSTENTION ANALYSIS ENGINE ===')

# Load Candidate Model v2
m2_path = 'ml/artifacts/model_v2.joblib'
m2_obj = joblib.load(m2_path)
model = m2_obj['pipeline']
classes = list(model.classes_)

def compute_record_signals(text, dataset_name, true_label=None):
    if not isinstance(text, str) or not text.strip():
        return {
            'dataset': dataset_name,
            'true_label': true_label if true_label else 'UNMAPPED',
            'pred_class': 'UNMAPPED',
            'max_confidence': 0.0,
            'margin': 0.0,
            'entropy': float(-np.sum([0.2 * np.log2(0.2)] * 5)), # max entropy for 5 classes
            'text_length': 0
        }
    
    proba = model.predict_proba([text])[0]
    sorted_proba = np.sort(proba)[::-1]
    max_conf = float(sorted_proba[0])
    margin = float(sorted_proba[0] - sorted_proba[1])
    
    # Entropy: H(p) = - sum p_i log2(p_i)
    # Clip proba to avoid log2(0)
    clipped_p = np.clip(proba, 1e-12, 1.0)
    entropy = float(-np.sum(clipped_p * np.log2(clipped_p)))
    
    pred_idx = np.argmax(proba)
    pred_class = classes[pred_idx]
    
    return {
        'dataset': dataset_name,
        'true_label': true_label if true_label else 'UNMAPPED',
        'pred_class': str(pred_class),
        'max_confidence': max_conf,
        'margin': margin,
        'entropy': entropy,
        'text_length': len(text)
    }

records = []

# 1. IN-DOMAIN TEST SET (test.csv, N=278)
print('Evaluating In-Domain Test Set (test.csv, N=278)...')
df_test = pd.read_csv('ml/data/processed/test.csv')
for idx, row in df_test.iterrows():
    rec = compute_record_signals(row['Text'], 'in_domain_test', row['Mapped_Category'])
    records.append(rec)

# 2. ACCOUNTANT OOD SET (ocr_results.csv, N=283)
print('Evaluating Accountant OOD Set (ocr_results.csv, N=283)...')
df_ocr = pd.read_csv('ml/data/raw/ocr_results.csv')
for idx, row in df_ocr.iterrows():
    rec = compute_record_signals(row['Text'], 'accountant_ood', 'Accountant')
    records.append(rec)

# 3. OCR INDEPENDENT OOD SAMPLE (phase23d_ocr_results.json, N=34)
print('Evaluating Independent OCR OOD Sample (phase23d_ocr_results.json, N=34)...')
with open('reports/phase23d_ocr_results.json', 'r') as f:
    pdf_eval_data = json.load(f)

for row in pdf_eval_data:
    # Calculate margin and entropy from saved probabilities
    probs = list(row['probabilities'].values())
    if probs and sum(probs) > 0:
        sorted_p = np.sort(probs)[::-1]
        max_conf = float(sorted_p[0])
        margin = float(sorted_p[0] - sorted_p[1])
        cp = np.clip(probs, 1e-12, 1.0)
        entropy = float(-np.sum(cp * np.log2(cp)))
        pred_class = row['predicted_class']
    else:
        max_conf = 0.0
        margin = 0.0
        entropy = 2.3219 # log2(5)
        pred_class = 'UNMAPPED'
        
    records.append({
        'dataset': 'independent_ocr_ood',
        'true_label': row['source_category'],
        'pred_class': pred_class,
        'max_confidence': max_conf,
        'margin': margin,
        'entropy': entropy,
        'text_length': row['extracted_char_count']
    })

# Convert to DataFrame
df_all = pd.DataFrame(records)

os.makedirs('reports', exist_ok=True)
df_all.to_csv('reports/phase23e_distribution_data.csv', index=False)

def get_stats(series):
    return {
        'count': int(len(series)),
        'mean': float(series.mean()),
        'median': float(series.median()),
        'p5': float(np.percentile(series, 5)),
        'p25': float(np.percentile(series, 25)),
        'p75': float(np.percentile(series, 75)),
        'p95': float(np.percentile(series, 95)),
        'min': float(series.min()),
        'max': float(series.max()),
        'std': float(series.std())
    }

print('\n=== Distribution Statistics by Dataset ===')
datasets = ['in_domain_test', 'accountant_ood', 'independent_ocr_ood']
dist_summary = {}

for ds in datasets:
    sub = df_all[df_all['dataset'] == ds]
    dist_summary[ds] = {
        'max_confidence': get_stats(sub['max_confidence']),
        'margin': get_stats(sub['margin']),
        'entropy': get_stats(sub['entropy']),
        'text_length': get_stats(sub['text_length'])
    }
    print(f"\n--- Dataset: {ds} ({len(sub)} records) ---")
    print(f"Max Confidence: Mean={sub['max_confidence'].mean():.4f}, Median={sub['max_confidence'].median():.4f}, P5={np.percentile(sub['max_confidence'], 5):.4f}, P95={np.percentile(sub['max_confidence'], 95):.4f}")
    print(f"Margin: Mean={sub['margin'].mean():.4f}, Median={sub['margin'].median():.4f}, P5={np.percentile(sub['margin'], 5):.4f}, P95={np.percentile(sub['margin'], 95):.4f}")
    print(f"Entropy: Mean={sub['entropy'].mean():.4f}, Median={sub['entropy'].median():.4f}, P5={np.percentile(sub['entropy'], 5):.4f}, P95={np.percentile(sub['entropy'], 95):.4f}")

# 4. CANDIDATE THRESHOLD ANALYSIS (Operating Points Sweep)
print('\n=== Candidate Threshold Operating Points Sweep ===')
thresholds = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
thresh_rows = []

df_indomain = df_all[df_all['dataset'] == 'in_domain_test']
df_acc_ood = df_all[df_all['dataset'] == 'accountant_ood']
df_ocr_ood = df_all[df_all['dataset'] == 'independent_ocr_ood']

for tau in thresholds:
    in_cov = (df_indomain['max_confidence'] >= tau).mean() * 100.0
    in_abs = (df_indomain['max_confidence'] < tau).mean() * 100.0
    
    acc_acc = (df_acc_ood['max_confidence'] >= tau).mean() * 100.0
    acc_rej = (df_acc_ood['max_confidence'] < tau).mean() * 100.0
    
    ocr_acc = (df_ocr_ood['max_confidence'] >= tau).mean() * 100.0
    ocr_rej = (df_ocr_ood['max_confidence'] < tau).mean() * 100.0
    
    thresh_rows.append({
        'candidate_threshold': tau,
        'in_domain_coverage_pct': in_cov,
        'in_domain_abstained_pct': in_abs,
        'accountant_ood_accepted_pct': acc_acc,
        'accountant_ood_rejected_pct': acc_rej,
        'ocr_ood_accepted_pct': ocr_acc,
        'ocr_ood_rejected_pct': ocr_rej
    })

df_thresh = pd.DataFrame(thresh_rows)
print(df_thresh.to_string(index=False))
df_thresh.to_csv('reports/phase23e_threshold_analysis.csv', index=False)

# 5. EXPLORATORY ROC-AUC AND PR-AUC DISCRIMINATION ANALYSIS
print('\n=== Exploratory ROC-AUC & PR-AUC Signal Separation ===')
# Binary target: 1 = In-Domain, 0 = OOD (combining accountant + ocr ood)
df_eval = df_all.copy()
df_eval['is_indomain'] = (df_eval['dataset'] == 'in_domain_test').astype(int)

# Signal A: Max Confidence
roc_conf = roc_auc_score(df_eval['is_indomain'], df_eval['max_confidence'])
prec_conf, rec_conf, _ = precision_recall_curve(df_eval['is_indomain'], df_eval['max_confidence'])
pr_conf = auc(rec_conf, prec_conf)

# Signal B: Margin
roc_margin = roc_auc_score(df_eval['is_indomain'], df_eval['margin'])
prec_mar, rec_mar, _ = precision_recall_curve(df_eval['is_indomain'], df_eval['margin'])
pr_margin = auc(rec_mar, prec_mar)

# Signal C: Negative Entropy (-H(p)) -> higher negative entropy means lower uncertainty
roc_entropy = roc_auc_score(df_eval['is_indomain'], -df_eval['entropy'])
prec_ent, rec_ent, _ = precision_recall_curve(df_eval['is_indomain'], -df_eval['entropy'])
pr_entropy = auc(rec_ent, prec_ent)

signal_summary = {
    'signal_max_confidence': {'roc_auc': float(roc_conf), 'pr_auc': float(pr_conf)},
    'signal_margin': {'roc_auc': float(roc_margin), 'pr_auc': float(pr_margin)},
    'signal_negative_entropy': {'roc_auc': float(roc_entropy), 'pr_auc': float(pr_entropy)}
}

print(f"Signal 1 (Max Confidence):  ROC-AUC = {roc_conf:.4f} | PR-AUC = {pr_conf:.4f}")
print(f"Signal 2 (Probability Margin): ROC-AUC = {roc_margin:.4f} | PR-AUC = {pr_margin:.4f}")
print(f"Signal 3 (Negative Entropy):   ROC-AUC = {roc_entropy:.4f} | PR-AUC = {pr_entropy:.4f}")

# 6. CLASS-CONDITIONAL OOD PREDICTION BREAKDOWN
print('\n=== Class-Conditional Prediction Distribution for OOD Data ===')
print("Accountant OOD Predictions:")
print(df_acc_ood['pred_class'].value_counts())
print("\nIndependent OCR OOD Predictions:")
print(df_ocr_ood['pred_class'].value_counts())

# Master JSON Artifact
metrics_artifact = {
    'distribution_summary': dist_summary,
    'candidate_threshold_sweep': thresh_rows,
    'signal_discrimination_auc': signal_summary,
    'class_conditional_ood_counts': {
        'accountant_ood': df_acc_ood['pred_class'].value_counts().to_dict(),
        'independent_ocr_ood': df_ocr_ood['pred_class'].value_counts().to_dict()
    }
}

with open('reports/phase23e_ood_metrics.json', 'w') as f:
    json.dump(metrics_artifact, f, indent=2)

print('\nAnalysis script completed successfully!')
print('Saved artifacts:')
print('  - reports/phase23e_ood_metrics.json')
print('  - reports/phase23e_threshold_analysis.csv')
print('  - reports/phase23e_distribution_data.csv')
