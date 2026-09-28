import fitz, easyocr, time, io, os, glob, json, joblib
import numpy as np
import pandas as pd
from PIL import Image

print('=== PHASE 23D: STEP 1 — PILOT OCR EVALUATION (20 PDFs) ===')

# Load Candidate Model v2
m2_path = 'ml/artifacts/model_v2.joblib'
m2_obj = joblib.load(m2_path)
model = m2_obj['pipeline']
classes = list(model.classes_)

# Initialize EasyOCR reader
print('Initializing EasyOCR engine...')
reader = easyocr.Reader(['en'], gpu=False)

# Select 20 representative PDFs from different categories
pdf_files = sorted(glob.glob('ml/data/raw/archive_1/Resumes PDF/**/*.pdf', recursive=True))

# Pick ~1-2 per subdirectory to get exactly 20 files
categories = sorted(list(set(os.path.dirname(f) for f in pdf_files)))
selected_pdfs = []
for cat_dir in categories:
    cat_files = [f for f in pdf_files if os.path.dirname(f) == cat_dir]
    selected_pdfs.extend(cat_files[:2])
    if len(selected_pdfs) >= 20:
        break
selected_pdfs = selected_pdfs[:20]

print(f'Selected {len(selected_pdfs)} pilot PDFs across {len(set(os.path.dirname(f) for f in selected_pdfs))} category folders.')

pilot_results = []

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
        'total_latency_ms': ocr_latency_ms + inf_latency_ms,
        'text_snippet': extracted_text[:200]
    }
    pilot_results.append(res)
    print(f"[{idx+1}/20] {rel_path}: OCR Status={ocr_status}, Chars={len(extracted_text)}, OCR Latency={ocr_latency_ms:.1f}ms, Pred={pred_class}, Conf={conf:.4f}")

df_pilot = pd.DataFrame(pilot_results)
print('\n=== Pilot Evaluation Summary ===')
print(f"Total Pilot Documents: {len(df_pilot)}")
print(f"OCR Success Rate: {(df_pilot['ocr_status'] == 'SUCCESS').mean()*100:.1f}%")
print(f"OCR Unusable Rate: {(df_pilot['ocr_status'] == 'OCR_UNUSABLE').mean()*100:.1f}%")
print(f"Mean Extracted Chars: {df_pilot['extracted_char_count'].mean():.1f}, Median: {df_pilot['extracted_char_count'].median():.1f}")
print(f"Min Chars: {df_pilot['extracted_char_count'].min()}, Max Chars: {df_pilot['extracted_char_count'].max()}")
print(f"OCR Latency (ms) - Mean: {df_pilot['ocr_latency_ms'].mean():.1f}, Median: {df_pilot['ocr_latency_ms'].median():.1f}, p95: {np.percentile(df_pilot['ocr_latency_ms'], 95):.1f}")

os.makedirs('reports', exist_ok=True)
with open('reports/phase23d_pilot_results.json', 'w') as f:
    json.dump(pilot_results, f, indent=2)

print('\nPilot evaluation script complete. Saved to reports/phase23d_pilot_results.json')
