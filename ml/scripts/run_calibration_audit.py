"""
ml/scripts/run_calibration_audit.py

Phase 22E: Proper Probability Calibration & Reliability Audit.
Calculates Brier Score, Expected Calibration Error (ECE), and Confidence Bins.
"""

import json
import joblib
import pandas as pd
import numpy as np

def run_calibration_audit():
    artifact = joblib.load('ml/artifacts/model_v2.joblib')
    pipeline = artifact['pipeline']
    classes = list(pipeline.classes_)

    test_df = pd.read_csv('ml/data/processed/test.csv')
    X_test = test_df['Clean_Text']
    y_test = test_df['Mapped_Category']

    probs = pipeline.predict_proba(X_test)
    preds = pipeline.predict(X_test)

    # Multi-class Brier score
    y_test_onehot = pd.get_dummies(y_test)[classes].values
    brier_score = float(np.mean(np.sum((probs - y_test_onehot) ** 2, axis=1)))

    # Expected Calibration Error (ECE)
    def calculate_ece(y_true, y_pred, probs, n_bins=5):
        confidences = np.max(probs, axis=1)
        accuracies = (y_true == y_pred).astype(float)
        
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        bin_stats = []
        
        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i+1]
            
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            prop_in_bin = np.mean(in_bin)
            
            if prop_in_bin > 0:
                accuracy_in_bin = np.mean(accuracies[in_bin])
                avg_confidence_in_bin = np.mean(confidences[in_bin])
                gap = np.abs(accuracy_in_bin - avg_confidence_in_bin)
                ece += gap * prop_in_bin
                
                bin_stats.append({
                    'bin_range': f'{bin_lower:.1f} - {bin_upper:.1f}',
                    'count': int(np.sum(in_bin)),
                    'accuracy': round(float(accuracy_in_bin), 4),
                    'avg_confidence': round(float(avg_confidence_in_bin), 4),
                    'abs_calibration_gap': round(float(gap), 4)
                })
                
        return ece, bin_stats

    ece_val, bin_stats = calculate_ece(y_test.values, preds, probs, n_bins=5)

    top_conf = np.max(probs, axis=1)
    correct_mask = (y_test.values == preds)

    avg_conf_correct = float(np.mean(top_conf[correct_mask]))
    avg_conf_incorrect = float(np.mean(top_conf[~correct_mask])) if np.sum(~correct_mask) > 0 else 0.0

    calib_summary = {
        'brier_score': round(brier_score, 4),
        'expected_calibration_error_ece': round(ece_val, 4),
        'avg_confidence_correct': round(avg_conf_correct, 4),
        'avg_confidence_incorrect': round(avg_conf_incorrect, 4),
        'confidence_bin_breakdown': bin_stats
    }

    with open('reports/calibration_metrics.json', 'w') as f:
        json.dump(calib_summary, f, indent=2)

    print('=== CALIBRATION METRICS ON UNTOUCHED TEST SET (278 Records) ===')
    print(f"Brier Score:                     {brier_score:.4f} (lower is better, 0.0 = perfect)")
    print(f"Expected Calibration Error (ECE): {ece_val:.4f} (lower is better, 0.0 = perfect)")
    print(f"Mean Confidence (Correct):       {avg_conf_correct*100:.2f}%")
    print(f"Mean Confidence (Incorrect):     {avg_conf_incorrect*100:.2f}%")
    print('\nConfidence Bin Breakdown:')
    for b in bin_stats:
        acc_pct = b['accuracy'] * 100.0
        conf_pct = b['avg_confidence'] * 100.0
        gap_pct = b['abs_calibration_gap'] * 100.0
        print(f" Bin {b['bin_range']}: Count={b['count']:3d} | Accuracy={acc_pct:5.1f}% | AvgConf={conf_pct:5.1f}% | Gap={gap_pct:4.1f}%")

if __name__ == '__main__':
    run_calibration_audit()
