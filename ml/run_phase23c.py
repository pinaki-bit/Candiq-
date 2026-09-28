import joblib, time, os, glob, re, json
import pandas as pd
import numpy as np
import fitz

print('=== PHASE 23C: INDEPENDENT EXTERNAL EVALUATION ENGINE ===')

# Load Candidate Model v2
m2_path = 'ml/artifacts/model_v2.joblib'
m2_obj = joblib.load(m2_path)
model = m2_obj['pipeline']
classes = list(model.classes_)

def predict_single(text):
    t0 = time.perf_counter()
    if not isinstance(text, str) or not text.strip():
        t1 = time.perf_counter()
        return {
            'status': 'empty_text',
            'text_len': 0,
            'pred_class': 'UNMAPPED',
            'confidence': 0.0,
            'probabilities': {c: 0.0 for c in classes},
            'latency_ms': (t1 - t0) * 1000.0
        }
    try:
        proba = model.predict_proba([text])[0]
        max_idx = np.argmax(proba)
        pred_class = classes[max_idx]
        conf = float(proba[max_idx])
        t1 = time.perf_counter()
        return {
            'status': 'success',
            'text_len': len(text),
            'pred_class': str(pred_class),
            'confidence': conf,
            'probabilities': {c: float(p) for c, p in zip(classes, proba)},
            'latency_ms': (t1 - t0) * 1000.0
        }
    except Exception as e:
        t1 = time.perf_counter()
        return {
            'status': f'error: {str(e)}',
            'text_len': len(text) if isinstance(text, str) else 0,
            'pred_class': 'ERROR',
            'confidence': 0.0,
            'probabilities': {c: 0.0 for c in classes},
            'latency_ms': (t1 - t0) * 1000.0
        }

# Ensure reports directory exists
os.makedirs('reports', exist_ok=True)

# 1. EVALUATE AUDIT_PDFS (Synthetic PDF Set, N=5)
print('\n--- 1. Evaluating audit_pdfs (N=5) ---')
audit_files = sorted(glob.glob('audit_pdfs/*.pdf'))
audit_results = []
expected_map = {
    'resume_cloud_elena.pdf': 'Cloud Computing',
    'resume_devops_marcus.pdf': 'DevOps',
    'resume_ds_alex.pdf': 'Data Science',
    'resume_sec_david.pdf': 'Cybersecurity',
    'resume_web_sarah.pdf': 'Web Development'
}

for fname in audit_files:
    base = os.path.basename(fname)
    doc = fitz.open(fname)
    text = ''.join(page.get_text() for page in doc)
    res = predict_single(text)
    exp = expected_map.get(base, 'UNKNOWN')
    res['file'] = base
    res['expected_class'] = exp
    res['is_correct'] = (res['pred_class'] == exp)
    audit_results.append(res)
    print(f"{base}: Expected={exp}, Pred={res['pred_class']}, Conf={res['confidence']:.4f}, Correct={res['is_correct']}, Latency={res['latency_ms']:.2f}ms")

with open('reports/phase23c_synthetic_results.json', 'w') as f:
    json.dump(audit_results, f, indent=2)

# 2. EVALUATE OCR_RESULTS.CSV (Accountant OCR, N=283)
print('\n--- 2. Evaluating ocr_results.csv (Accountant OCR, N=283) ---')
df_ocr = pd.read_csv('ml/data/raw/ocr_results.csv')
ocr_results = []
for idx, row in df_ocr.iterrows():
    text = row['Text']
    res = predict_single(text)
    res['id'] = idx
    res['source_category'] = row['Category']
    ocr_results.append(res)

df_ocr_res = pd.DataFrame(ocr_results)
print(f"Total Accountant OCR records: {len(df_ocr_res)}")
print(f"Processing Statuses: {df_ocr_res['status'].value_counts().to_dict()}")
print(f"Predicted Class Distribution:\n{df_ocr_res['pred_class'].value_counts()}")
print(f"Mean Confidence: {df_ocr_res['confidence'].mean():.4f}, Median: {df_ocr_res['confidence'].median():.4f}")
high_conf_ocr = (df_ocr_res['confidence'] >= 0.80).sum()
print(f"High-Confidence (>=0.80) Count: {high_conf_ocr} ({(high_conf_ocr/len(df_ocr_res))*100.0:.1f}%)")
print(f"Latency (ms) - Mean: {df_ocr_res['latency_ms'].mean():.2f}, Median: {df_ocr_res['latency_ms'].median():.2f}, p95: {np.percentile(df_ocr_res['latency_ms'], 95):.2f}, Max: {df_ocr_res['latency_ms'].max():.2f}")

with open('reports/phase23c_ocr_accountant_results.json', 'w') as f:
    json.dump(ocr_results, f, indent=2)

# 3. EVALUATE ARCHIVE_1 RESUMES PDF (1,874 PDFs across 17 non-IT categories)
print('\n--- 3. Evaluating archive_1/Resumes PDF (Independent PDF Corpus) ---')
pdf_files = glob.glob('ml/data/raw/archive_1/Resumes PDF/**/*.pdf', recursive=True)
print(f"Found {len(pdf_files)} PDF files in archive_1")

pdf_results = []
for fname in pdf_files:
    rel_path = os.path.relpath(fname, 'ml/data/raw/archive_1/Resumes PDF')
    category_folder = rel_path.split(os.sep)[0] if os.sep in rel_path else 'UNKNOWN'
    
    try:
        doc = fitz.open(fname)
        text = ''.join(page.get_text() for page in doc)
    except Exception as e:
        text = ''
        
    res = predict_single(text)
    res['file'] = rel_path
    res['source_category'] = category_folder
    pdf_results.append(res)

df_pdf_res = pd.DataFrame(pdf_results)
print(f"Total Independent PDF records evaluated: {len(df_pdf_res)}")
print(f"Processing Statuses: {df_pdf_res['status'].value_counts().to_dict()}")
print(f"Overall Predicted Class Distribution:\n{df_pdf_res['pred_class'].value_counts()}")
print(f"Overall Mean Confidence: {df_pdf_res['confidence'].mean():.4f}, Median: {df_pdf_res['confidence'].median():.4f}")
high_conf_pdf = (df_pdf_res['confidence'] >= 0.80).sum()
print(f"Overall High-Confidence (>=0.80) Count: {high_conf_pdf} ({(high_conf_pdf/len(df_pdf_res))*100.0:.1f}%)")
print(f"Latency (ms) - Mean: {df_pdf_res['latency_ms'].mean():.2f}, Median: {df_pdf_res['latency_ms'].median():.2f}, p95: {np.percentile(df_pdf_res['latency_ms'], 95):.2f}, Max: {df_pdf_res['latency_ms'].max():.2f}")

# Group by source category
print('\n=== Source Category Breakdown for PDF Corpus ===')
cat_summary = []
for cat, grp in df_pdf_res.groupby('source_category'):
    n = len(grp)
    dom_class = grp['pred_class'].mode()[0] if len(grp) > 0 else 'N/A'
    dom_cnt = (grp['pred_class'] == dom_class).sum()
    mean_conf = grp['confidence'].mean()
    high_conf_cnt = (grp['confidence'] >= 0.80).sum()
    high_conf_rate = (high_conf_cnt / n) * 100.0
    cat_summary.append({
        'source_category': cat,
        'count': n,
        'dominant_predicted_class': dom_class,
        'dominant_class_pct': (dom_cnt / n) * 100.0,
        'mean_confidence': mean_conf,
        'high_confidence_count': high_conf_cnt,
        'high_confidence_rate_pct': high_conf_rate
    })

df_cat_summary = pd.DataFrame(cat_summary)
print(df_cat_summary.to_string(index=False))

with open('reports/phase23c_pdf_corpus_results.json', 'w') as f:
    json.dump(pdf_results, f, indent=2)

df_cat_summary.to_csv('reports/phase23c_pdf_category_summary.csv', index=False)
print('\nEvaluation script completed successfully!')
