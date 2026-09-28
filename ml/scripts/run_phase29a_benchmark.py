"""
ml/scripts/run_phase29a_benchmark.py

Phase 29A — Real Semantic Embedding Evaluation Benchmark Script.

Evaluates MD5 Hash-Projection (LocalEmbeddingProvider) vs
Real Local Transformer (sentence-transformers/all-MiniLM-L6-v2).

THIS IS AN EVALUATION BENCHMARK SCRIPT ONLY.
DO NOT MODIFY PRODUCTION SCORING OR REPLACE PRODUCTION PROVIDERS.
"""

from __future__ import annotations

import json
import math
import os
import platform
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.embedding_service import LocalEmbeddingProvider, cosine_similarity


class SentenceTransformerEmbeddingProvider:
    """
    Isolated Benchmark Provider for sentence-transformers/all-MiniLM-L6-v2.
    Evaluation-only; CPU compatible; 384-dimensional normalized dense vectors.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.load_time_sec = 0.0

    def _ensure_loaded(self):
        if self._model is None:
            t0 = time.perf_counter()
            from sentence_transformers import SentenceTransformer
            # Force CPU for benchmark consistency
            self._model = SentenceTransformer(self.model_name, device="cpu")
            self.load_time_sec = time.perf_counter() - t0

    def embed_text(self, text: str) -> List[float]:
        self._ensure_loaded()
        if not text or not text.strip():
            return [0.0] * 384
        vec = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return [float(x) for x in vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._ensure_loaded()
        if not texts:
            return []
        vecs = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return [[float(x) for x in row] for row in vecs]


# Controlled Benchmark Fixture (7 Categories)
BENCHMARK_PAIRS = [
    {
        "id": "PAIR_01_STRONG_RELEVANT",
        "category": "STRONGLY RELEVANT",
        "is_positive": True,
        "resume": "Senior Python Backend Developer with 5+ years of experience designing scalable microservices using FastAPI, PostgreSQL, Docker, and Redis. Demonstrated track record in building high-throughput REST APIs and async worker pipelines.",
        "job": "Seeking a Senior Python Backend Engineer to build robust RESTful microservices. Requirements include proficiency in Python 3, FastAPI or Django, PostgreSQL database optimization, containerization with Docker, and caching with Redis.",
    },
    {
        "id": "PAIR_02_PARTIAL_RELEVANT",
        "category": "PARTIALLY RELEVANT",
        "is_positive": True,
        "resume": "Data Analyst with 3 years of experience writing SQL queries, performing exploratory data analysis in Python Pandas, and building Tableau business dashboards.",
        "job": "Looking for a Senior Data Scientist to train deep learning models in PyTorch, implement computer vision algorithms, and deploy ML models using Kubernetes.",
    },
    {
        "id": "PAIR_03_UNRELATED",
        "category": "UNRELATED",
        "is_positive": False,
        "resume": "Senior Commercial Litigation Attorney with 10 years of experience managing corporate contract disputes, courtroom trials, regulatory compliance audits, and legal team supervision.",
        "job": "Seeking Cloud Infrastructure Engineer to manage AWS multi-region Terraform deployments, Kubernetes clusters, Prometheus monitoring, and CI/CD pipelines.",
    },
    {
        "id": "PAIR_04_PARAPHRASED",
        "category": "PARAPHRASED / SEMANTICALLY EQUIVALENT",
        "is_positive": True,
        "resume": "Engineered high-concurrency server-side web applications using Python and asynchronous HTTP communication protocols.",
        "job": "Seeking developers experienced in Python server-side development and high-performance API services.",
    },
    {
        "id": "PAIR_05_KEYWORD_DIFF_CONTEXT",
        "category": "SAME KEYWORDS / DIFFERENT CONTEXT",
        "is_positive": False,
        "resume": "Utilized Python scripts to parse legal PDF contracts, format text documents, and organize office file archives.",
        "job": "Looking for Python software developer to build distributed microservices and scalable web applications.",
    },
    {
        "id": "PAIR_06_DOMAIN_RELATED_NOT_IDENTICAL",
        "category": "DOMAIN-RELATED BUT NOT IDENTICAL",
        "is_positive": False,
        "resume": "Cybersecurity Specialist conducting network penetration testing, vulnerability scanning using Burp Suite and Nmap, and SIEM log monitoring.",
        "job": "Frontend Web Developer to build responsive single-page web applications using React, TypeScript, Tailwind CSS, and Redux State Management.",
    },
    {
        "id": "PAIR_07_CROSS_DOMAIN_NEGATIVE",
        "category": "CROSS-DOMAIN NEGATIVE PAIRS",
        "is_positive": False,
        "resume": "Registered Nurse and Clinical Care Specialist with 8 years of hospital emergency room patient care, triage management, and electronic health records administration.",
        "job": "DevOps Engineer responsible for managing Kubernetes cluster auto-scaling, Helm charts, Terraform infrastructure-as-code, and Jenkins CI/CD.",
    },
]


def run_benchmark() -> Dict[str, Any]:
    print("=========================================================")
    print("PHASE 29A — REAL SEMANTIC EMBEDDING BENCHMARK EVALUATION")
    print("=========================================================\n")

    # 1. Environment & Package Metadata
    import torch
    import transformers
    import sentence_transformers

    env_info = {
        "os": platform.platform(),
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "sentence_transformers_version": sentence_transformers.__version__,
        "transformers_version": transformers.__version__,
        "cpu_count": os.cpu_count(),
    }
    print("Environment Metadata:")
    for k, v in env_info.items():
        print(f"  - {k}: {v}")
    print()

    # 2. Instantiate Providers
    local_provider = LocalEmbeddingProvider(dim=128)
    
    t_start_load = time.perf_counter()
    st_provider = SentenceTransformerEmbeddingProvider("sentence-transformers/all-MiniLM-L6-v2")
    st_provider._ensure_loaded()
    cold_load_time = time.perf_counter() - t_start_load
    print(f"SentenceTransformers Cold Model Load Time: {cold_load_time * 1000.0:.2f} ms")

    # 3. Latency Benchmarks
    sample_text = "Senior Python Backend Developer with FastAPI experience."
    
    # Warm Single Embedding Latency
    st_provider.embed_text(sample_text) # warmup
    single_latencies_local = []
    single_latencies_st = []
    
    for _ in range(50):
        t0 = time.perf_counter()
        local_provider.embed_text(sample_text)
        single_latencies_local.append((time.perf_counter() - t0) * 1000.0)

        t0 = time.perf_counter()
        st_provider.embed_text(sample_text)
        single_latencies_st.append((time.perf_counter() - t0) * 1000.0)

    # Batch Latency (10 items)
    batch_texts = [p["resume"] for p in BENCHMARK_PAIRS] + [BENCHMARK_PAIRS[0]["job"], BENCHMARK_PAIRS[1]["job"]]
    
    t0 = time.perf_counter()
    local_provider.embed_batch(batch_texts)
    batch_lat_local = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    st_provider.embed_batch(batch_texts)
    batch_lat_st = (time.perf_counter() - t0) * 1000.0

    # 4. Pair Evaluation
    results = []
    local_pos_sims, local_neg_sims = [], []
    st_pos_sims, st_neg_sims = [], []

    for pair in BENCHMARK_PAIRS:
        # Local MD5 provider
        v_res_loc = local_provider.embed_text(pair["resume"])
        v_job_loc = local_provider.embed_text(pair["job"])
        sim_loc = round(cosine_similarity(v_res_loc, v_job_loc), 4)

        # ST MiniLM provider
        v_res_st = st_provider.embed_text(pair["resume"])
        v_job_st = st_provider.embed_text(pair["job"])
        sim_st = round(cosine_similarity(v_res_st, v_job_st), 4)

        if pair["is_positive"]:
            local_pos_sims.append(sim_loc)
            st_pos_sims.append(sim_st)
        else:
            local_neg_sims.append(sim_loc)
            st_neg_sims.append(sim_st)

        results.append({
            "id": pair["id"],
            "category": pair["category"],
            "is_positive": pair["is_positive"],
            "local_hash_sim": sim_loc,
            "minilm_sim": sim_st,
            "difference_st_minus_local": round(sim_st - sim_loc, 4),
        })

    # Summary Statistics
    mean_loc_pos = round(sum(local_pos_sims) / len(local_pos_sims), 4)
    mean_loc_neg = round(sum(local_neg_sims) / len(local_neg_sims), 4)
    margin_loc = round(mean_loc_pos - mean_loc_neg, 4)

    mean_st_pos = round(sum(st_pos_sims) / len(st_pos_sims), 4)
    mean_st_neg = round(sum(st_neg_sims) / len(st_neg_sims), 4)
    margin_st = round(mean_st_pos - mean_st_neg, 4)

    # Paraphrase Recognition Gap (Pair 04 vs Pair 05)
    # Pair 04: Paraphrased ("server-side web applications using Python")
    # Pair 05: Same keyword different context ("parse legal PDF contracts with Python")
    p4_loc = results[3]["local_hash_sim"] # PAIR_04
    p5_loc = results[4]["local_hash_sim"] # PAIR_05
    paraphrase_gap_loc = round(p4_loc - p5_loc, 4)

    p4_st = results[3]["minilm_sim"]
    p5_st = results[4]["minilm_sim"]
    paraphrase_gap_st = round(p4_st - p5_st, 4)

    report_data = {
        "environment": env_info,
        "latency": {
            "cold_model_load_ms": round(cold_load_time * 1000.0, 2),
            "local_single_warm_mean_ms": round(sum(single_latencies_local) / len(single_latencies_local), 4),
            "minilm_single_warm_mean_ms": round(sum(single_latencies_st) / len(single_latencies_st), 4),
            "local_batch_10_ms": round(batch_lat_local, 2),
            "minilm_batch_10_ms": round(batch_lat_st, 2),
        },
        "pair_results": results,
        "metrics": {
            "local_mean_positive_sim": mean_loc_pos,
            "local_mean_negative_sim": mean_loc_neg,
            "local_separation_margin": margin_loc,
            "minilm_mean_positive_sim": mean_st_pos,
            "minilm_mean_negative_sim": mean_st_neg,
            "minilm_separation_margin": margin_st,
            "local_paraphrase_gap": paraphrase_gap_loc,
            "minilm_paraphrase_gap": paraphrase_gap_st,
        }
    }

    print("--- BENCHMARK RESULTS SUMMARY ---")
    print(f"Local MD5 Hash Provider:")
    print(f"  Mean Positive Sim : {mean_loc_pos}")
    print(f"  Mean Negative Sim : {mean_loc_neg}")
    print(f"  Separation Margin : {margin_loc}")
    print(f"  Paraphrase Gap    : {paraphrase_gap_loc} (Pair 04={p4_loc} vs Pair 05={p5_loc})")
    print()
    print(f"all-MiniLM-L6-v2 Provider:")
    print(f"  Mean Positive Sim : {mean_st_pos}")
    print(f"  Mean Negative Sim : {mean_st_neg}")
    print(f"  Separation Margin : {margin_st}")
    print(f"  Paraphrase Gap    : {paraphrase_gap_st} (Pair 04={p4_st} vs Pair 05={p5_st})")
    print()
    print(f"Separation Margin Improvement: +{round(margin_st - margin_loc, 4)} (+{round((margin_st - margin_loc) / max(0.001, margin_loc) * 100.0, 1)}%)")
    print(f"Paraphrase Gap Improvement    : +{round(paraphrase_gap_st - paraphrase_gap_loc, 4)}")

    # Save benchmark JSON for audit trail
    report_path = Path(__file__).resolve().parent.parent.parent / "reports" / "phase29a_embedding_benchmark.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nSaved raw benchmark metrics to {report_path}")

    return report_data


if __name__ == "__main__":
    run_benchmark()
