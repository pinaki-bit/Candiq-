import fitz, easyocr, time, io, os, glob, json, joblib
import numpy as np
import pandas as pd
from PIL import Image

print('=== PHASE 23D: OCR-ENABLED CORPUS EVALUATION (17 CATEGORIES, N=34) ===')

# Load Candidate Model v2
m2_path = 'ml/artifacts/model_v2.joblib'
m2_obj = joblib.load(m2_path)
model = m2_obj['pipeline']
classes = list(model.classes_)

# Initialize EasyOCR engine
print('Initializing EasyOCR engine...')
reader = easyocr.Reader(['en'], gpu=False)

# Collect all PDF files in archive_1
pdf_files = sorted(glob.glob('ml/data/raw/archive_1/Resumes PDF/**/*.pdf', recursive=True))
print(f'Total PDF files in archive_1: {len(pdf_files)}')

# Select stratified benchmark sample: exactly 2 PDFs per subfolder across all 17 categories (N=34)
categories = sorted(list(set(os.path.dirname(f) for f in pdf_files)))
selected_pdfs = []
for cat_dir in categories:
    cat_files = [f for f in pdf_files if os.path.dirname(f) == cat_dir]
    selected_pdfs.extend(cat_files[:2])

print(f'Selected stratified benchmark corpus of {len(selected_pdfs)} PDFs across {len(categories)} category folders.')

full_results = []
sample_outputs = []

for idx, fpath in enumerate(selected_pdfs):
    rel_path = os.path.relpath(fpath, 'ml/data/raw/archive_1/Resumes PDF')
    cat_folder = rel_path.split(os.sep)[0]
    
    t0_ocr = time.perf_counter()
    try:
        doc = fitz.open(fpath)
        page_count = len(doc)
        full_text_pages = []
        
        for p_num in range(page_count):
            page = doc[p_num]
            pix = page.get_pixmap(dpi=96)
            img = Image.open(io.BytesIO(pix.tobytes('png')))
            img_np = np.array(img)
            
            ocr_out = reader.readtext(img_np, detail=0)
            page_text = ' '.join(ocr_out)
            full_text_pages.append(page_text)
            
        extracted_text = ' '.join(full_text_pages).strip()
        t1_ocr = time.perf_counter()
        ocr_latency_ms = (t1_ocr - t0_ocr) * 1000.0
        
        if len(extracted_text) < 50:
            ocr_status = 'OCR_UNUSABLE'
        else:
            ocr_status = 'SUCCESS'
            
    except Exception as e:
        t1_ocr = time.perf_counter()
        ocr_latency_ms = (t1_ocr - t0_ocr) * 1000.0
        extracted_text = ''
        page_count = 0
        ocr_status = f'FAILED: {str(e)}'
        
    # Model inference
    t0_inf = time.perf_counter()
    if extracted_text:
        proba = model.predict_proba([extracted_text])[0]
        max_idx = np.argmax(proba)
        pred_class = classes[max_idx]
        conf = float(proba[max_idx])
        probs_dict = {c: float(p) for c, p in zip(classes, proba)}
    else:
        pred_class = 'UNMAPPED'
        conf = 0.0
        probs_dict = {c: 0.0 for c in classes}
    t1_inf = time.perf_counter()
    inf_latency_ms = (t1_inf - t0_inf) * 1000.0
    
    res = {
        'id': idx + 1,
        'file': rel_path,
        'source_category': cat_folder,
        'page_count': page_count,
        'ocr_status': ocr_status,
        'extracted_char_count': len(extracted_text),
        'ocr_latency_ms': ocr_latency_ms,
        'predicted_class': str(pred_class),
        'confidence': conf,
        'probabilities': probs_dict,
        'inference_latency_ms': inf_latency_ms,
        'total_latency_ms': ocr_latency_ms + inf_latency_ms
    }
    full_results.append(res)
    
    # Save a sanitized sample of extracted text (first 300 chars, no PII) for error analysis
    sample_outputs.append({
        'file': rel_path,
        'source_category': cat_folder,
        'ocr_status': ocr_status,
        'char_count': len(extracted_text),
        'text_snippet_sanitized': extracted_text[:300]
    })
        
    print(f"[{idx+1}/{len(selected_pdfs)}] {rel_path}: Chars={len(extracted_text)}, OCR={ocr_latency_ms:.0f}ms, Pred={pred_class}, Conf={conf:.4f}")

df_full = pd.DataFrame(full_results)
print('\n=== Full Corpus Evaluation Summary ===')
print(f"Total Documents Processed: {len(df_full)}")
print(f"OCR Success Rate: {(df_full['ocr_status'] == 'SUCCESS').mean()*100:.1f}%")
print(f"OCR Unusable Rate: {(df_full['ocr_status'] == 'OCR_UNUSABLE').mean()*100:.1f}%")
print(f"Mean Extracted Chars: {df_full['extracted_char_count'].mean():.1f}, Median: {df_full['extracted_char_count'].median():.1f}")
print(f"Min Chars: {df_full['extracted_char_count'].min()}, Max Chars: {df_full['extracted_char_count'].max()}")
print(f"OCR Latency (ms) - Mean: {df_full['ocr_latency_ms'].mean():.1f}, Median: {df_full['ocr_latency_ms'].median():.1f}, p95: {np.percentile(df_full['ocr_latency_ms'], 95):.1f}")
print(f"Inference Latency (ms) - Mean: {df_full['inference_latency_ms'].mean():.2f}, Median: {df_full['inference_latency_ms'].median():.2f}, p95: {np.percentile(df_full['inference_latency_ms'], 95):.2f}")
print(f"Total Latency (ms) - Mean: {df_full['total_latency_ms'].mean():.1f}, Median: {df_full['total_latency_ms'].median():.1f}, p95: {np.percentile(df_full['total_latency_ms'], 95):.1f}")

# Category Breakdown
cat_summary = []
for cat, grp in df_full.groupby('source_category'):
    n = len(grp)
    succ_cnt = (grp['ocr_status'] == 'SUCCESS').sum()
    unusable_cnt = (grp['ocr_status'] == 'OCR_UNUSABLE').sum()
    mean_chars = grp['extracted_char_count'].mean()
    dom_class = grp['predicted_class'].mode()[0] if len(grp) > 0 else 'N/A'
    dom_pct = ((grp['predicted_class'] == dom_class).sum() / n) * 100.0
    mean_conf = grp['confidence'].mean()
    high_conf_cnt = (grp['confidence'] >= 0.80).sum()
    high_conf_rate = (high_conf_cnt / n) * 100.0
    mean_total_ms = grp['total_latency_ms'].mean()
    
    cat_summary.append({
        'source_category': cat,
        'record_count': n,
        'ocr_success_rate_pct': (succ_cnt / n) * 100.0,
        'ocr_unusable_rate_pct': (unusable_cnt / n) * 100.0,
        'mean_extracted_chars': mean_chars,
        'dominant_predicted_class': dom_class,
        'dominant_class_pct': dom_pct,
        'mean_confidence': mean_conf,
        'high_confidence_count': high_conf_cnt,
        'high_confidence_rate_pct': high_conf_rate,
        'average_total_latency_ms': mean_total_ms
    })

df_cat_summary = pd.DataFrame(cat_summary)
print('\n=== Category Summary Table ===')
print(df_cat_summary.to_string(index=False))

# High-confidence OOD predictions
high_conf_df = df_full[df_full['confidence'] >= 0.80]
print(f"\nTotal High-Confidence Predictions (>=0.80): {len(high_conf_df)} ({(len(high_conf_df)/len(df_full))*100.0:.1f}%)")
print(f"High-Confidence Class Distribution:\n{high_conf_df['predicted_class'].value_counts()}")

# Save outputs
os.makedirs('reports', exist_ok=True)
with open('reports/phase23d_ocr_results.json', 'w') as f:
    json.dump(full_results, f, indent=2)

with open('reports/phase23d_sample_ocr_outputs.json', 'w') as f:
    json.dump(sample_outputs, f, indent=2)

df_cat_summary.to_csv('reports/phase23d_category_summary.csv', index=False)
print('\nSaved machine-readable artifacts:')
print('  - reports/phase23d_ocr_results.json')
print('  - reports/phase23d_category_summary.csv')
print('  - reports/phase23d_sample_ocr_outputs.json')
