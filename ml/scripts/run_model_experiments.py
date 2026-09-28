"""
ml/scripts/run_model_experiments.py

Phase 21G: Controlled ML Model Experiments & Benchmark Comparison.
Evaluates Models A through F on the train/validation datasets.
"""

import time
import os
import json
import joblib
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

def run_experiments():
    os.makedirs('reports', exist_ok=True)
    os.makedirs('ml/artifacts/candidates', exist_ok=True)

    # Load train and val datasets
    train_df = pd.read_csv('ml/data/processed/train.csv')
    val_df = pd.read_csv('ml/data/processed/val.csv')

    X_train, y_train = train_df['Clean_Text'], train_df['Mapped_Category']
    X_val, y_val = val_df['Clean_Text'], val_df['Mapped_Category']

    experiments = [
        {
            'id': 'Model_A',
            'name': 'TF-IDF (Word 1-2) + Logistic Regression (Unweighted)',
            'pipeline': Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2)),
                ('clf', LogisticRegression(max_iter=1000, random_state=42))
            ]),
            'feature_config': 'Word TF-IDF (1,2), max_features=50k, min_df=2',
            'hyperparams': 'C=1.0, max_iter=1000, solver=lbfgs',
        },
        {
            'id': 'Model_B',
            'name': 'TF-IDF (Word 1-2) + LinearSVC (Unweighted)',
            'pipeline': Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2)),
                ('clf', LinearSVC(max_iter=2000, random_state=42))
            ]),
            'feature_config': 'Word TF-IDF (1,2), max_features=50k, min_df=2',
            'hyperparams': 'C=1.0, max_iter=2000',
        },
        {
            'id': 'Model_C',
            'name': 'TF-IDF (Word 1-2, Sublinear) + LinearSVC (Balanced)',
            'pipeline': Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2, sublinear_tf=True)),
                ('clf', LinearSVC(class_weight='balanced', max_iter=2000, random_state=42))
            ]),
            'feature_config': 'Word TF-IDF (1,2), sublinear_tf=True, max_features=50k',
            'hyperparams': 'C=1.0, class_weight=balanced, max_iter=2000',
        },
        {
            'id': 'Model_D',
            'name': 'Word+Char FeatureUnion + LinearSVC (Balanced)',
            'pipeline': Pipeline([
                ('features', FeatureUnion([
                    ('word', TfidfVectorizer(ngram_range=(1, 2), max_features=35000, min_df=2, sublinear_tf=True)),
                    ('char', TfidfVectorizer(analyzer='char', ngram_range=(3, 5), max_features=15000, min_df=2, sublinear_tf=True))
                ])),
                ('clf', LinearSVC(class_weight='balanced', max_iter=2000, random_state=42))
            ]),
            'feature_config': 'Word (1,2) [35k] + Char (3,5) [15k] TF-IDF',
            'hyperparams': 'C=1.0, class_weight=balanced, max_iter=2000',
        },
        {
            'id': 'Model_E',
            'name': 'TF-IDF (Word 1-2, Sublinear) + Logistic Regression (Balanced)',
            'pipeline': Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2, sublinear_tf=True)),
                ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
            ]),
            'feature_config': 'Word TF-IDF (1,2), sublinear_tf=True, max_features=50k',
            'hyperparams': 'C=1.0, class_weight=balanced, max_iter=1000',
        },
        {
            'id': 'Model_F',
            'name': 'TF-IDF (Word 1-2, Sublinear) + Multinomial Naive Bayes',
            'pipeline': Pipeline([
                ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=50000, min_df=2, sublinear_tf=True)),
                ('clf', MultinomialNB(alpha=0.1))
            ]),
            'feature_config': 'Word TF-IDF (1,2), sublinear_tf=True, max_features=50k',
            'hyperparams': 'alpha=0.1',
        }
    ]

    results = []

    for exp in experiments:
        t0 = time.time()
        pipe = exp['pipeline']
        pipe.fit(X_train, y_train)
        t_train_ms = (time.time() - t0) * 1000.0
        
        t1 = time.time()
        preds = pipe.predict(X_val)
        t_infer_ms = (time.time() - t1) * 1000.0
        
        acc = float(accuracy_score(y_val, preds))
        p_mac, r_mac, f1_mac, _ = precision_recall_fscore_support(y_val, preds, average='macro')
        p_wei, r_wei, f1_wei, _ = precision_recall_fscore_support(y_val, preds, average='weighted')
        
        rep = classification_report(y_val, preds, output_dict=True)
        cloud_rec = rep.get('Cloud Computing', {}).get('recall', 0.0)
        cloud_f1 = rep.get('Cloud Computing', {}).get('f1-score', 0.0)
        
        exp_id_str = exp['id'].lower()
        save_path = f'ml/artifacts/candidates/model_candidate_{exp_id_str}.joblib'
        joblib.dump({
            'pipeline': pipe,
            'version': f'candidate_{exp_id_str}',
            'model_name': exp['name'],
            'classes': pipe.classes_,
            'val_macro_f1': round(float(f1_mac), 4),
            'val_accuracy': round(float(acc), 4),
        }, save_path)
        
        rec = {
            'Experiment_ID': exp['id'],
            'Model_Name': exp['name'],
            'Feature_Configuration': exp['feature_config'],
            'Hyperparameters': exp['hyperparams'],
            'Training_Time_ms': round(t_train_ms, 2),
            'Val_Accuracy': round(acc, 4),
            'Val_Macro_Precision': round(float(p_mac), 4),
            'Val_Macro_Recall': round(float(r_mac), 4),
            'Val_Macro_F1': round(float(f1_mac), 4),
            'Val_Weighted_F1': round(float(f1_wei), 4),
            'Cloud_Computing_Recall': round(float(cloud_rec), 4),
            'Cloud_Computing_F1': round(float(cloud_f1), 4),
        }
        results.append(rec)

    results_df = pd.DataFrame(results)
    results_df.to_csv('reports/model_comparison.csv', index=False)

    print('=== PHASE 21G MODEL EXPERIMENTS COMPARISON ===')
    print(results_df[['Experiment_ID', 'Val_Accuracy', 'Val_Macro_F1', 'Val_Weighted_F1', 'Cloud_Computing_Recall', 'Training_Time_ms']].to_string(index=False))

if __name__ == '__main__':
    run_experiments()
