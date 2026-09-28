"""
ml/scripts/run_fair_comparison.py

Phase 22C: Fair Side-by-Side Model Comparison on Identical 278 Test Records.
Compares model_latest.joblib vs model_v2.joblib on test.csv ONLY.
"""

import json
import pandas as pd

def run_fair_comparison():
    with open('reports/baseline_test_metrics.json') as f:
        b_metrics = json.load(f)

    with open('reports/final_test_metrics.json') as f:
        v2_metrics = json.load(f)

    classes = b_metrics['target_classes']

    comparison = {
        'evaluation_dataset': 'ml/data/processed/test.csv (278 records)',
        'baseline_model': 'model_latest.joblib (LinearSVC v20260922_235001)',
        'v2_candidate_model': 'model_v2.joblib (Calibrated LinearSVC v2.0.0)',
        'overall_metrics_comparison': {
            'accuracy': {
                'baseline': b_metrics['accuracy'],
                'v2_candidate': v2_metrics['accuracy'],
                'absolute_diff': round(v2_metrics['accuracy'] - b_metrics['accuracy'], 4)
            },
            'macro_precision': {
                'baseline': b_metrics['macro_precision'],
                'v2_candidate': v2_metrics['macro_precision'],
                'absolute_diff': round(v2_metrics['macro_precision'] - b_metrics['macro_precision'], 4)
            },
            'macro_recall': {
                'baseline': b_metrics['macro_recall'],
                'v2_candidate': v2_metrics['macro_recall'],
                'absolute_diff': round(v2_metrics['macro_recall'] - b_metrics['macro_recall'], 4)
            },
            'macro_f1': {
                'baseline': b_metrics['macro_f1'],
                'v2_candidate': v2_metrics['macro_f1'],
                'absolute_diff': round(v2_metrics['macro_f1'] - b_metrics['macro_f1'], 4)
            },
            'weighted_f1': {
                'baseline': b_metrics['weighted_f1'],
                'v2_candidate': v2_metrics['weighted_f1'],
                'absolute_diff': round(v2_metrics['weighted_f1'] - b_metrics['weighted_f1'], 4)
            }
        },
        'per_class_f1_comparison': {
            cls: {
                'baseline_f1': b_metrics['per_class_metrics'][cls]['f1_score'],
                'v2_f1': v2_metrics['per_class'][cls]['f1_score'],
                'baseline_recall': b_metrics['per_class_metrics'][cls]['recall'],
                'v2_recall': v2_metrics['per_class'][cls]['recall'],
                'absolute_f1_diff': round(v2_metrics['per_class'][cls]['f1_score'] - b_metrics['per_class_metrics'][cls]['f1_score'], 4)
            }
            for cls in classes
        },
        'confusion_matrices': {
            'baseline': b_metrics['confusion_matrix'],
            'v2_candidate': v2_metrics['confusion_matrix']
        }
    }

    with open('reports/fair_baseline_vs_v2_test_comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2)

    print('=== FAIR BASELINE VS V2 COMPARISON ON SAME 278 TEST RECORDS ===')
    print(f"Baseline Accuracy:   {b_metrics['accuracy']*100:.2f}%  | v2 Accuracy:   {v2_metrics['accuracy']*100:.2f}%  | Diff: +{v2_metrics['accuracy'] - b_metrics['accuracy']:.4f}")
    print(f"Baseline Macro F1:   {b_metrics['macro_f1']:.4f}   | v2 Macro F1:   {v2_metrics['macro_f1']:.4f}   | Diff: +{v2_metrics['macro_f1'] - b_metrics['macro_f1']:.4f}")
    print(f"Baseline Weighted F1:{b_metrics['weighted_f1']:.4f}   | v2 Weighted F1:{v2_metrics['weighted_f1']:.4f}   | Diff: +{v2_metrics['weighted_f1'] - b_metrics['weighted_f1']:.4f}")

    print('\nPer-Class Recall Comparison:')
    for cls in classes:
        b_rec = b_metrics['per_class_metrics'][cls]['recall']
        v2_rec = v2_metrics['per_class'][cls]['recall']
        diff_rec = v2_rec - b_rec
        print(f" - {cls:20s}: Baseline Recall = {b_rec:.4f} -> v2 Recall = {v2_rec:.4f} (Diff: {diff_rec:+.4f})")

if __name__ == '__main__':
    run_fair_comparison()
