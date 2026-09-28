"""
ml/scripts/run_phase30_benchmark.py

Phase 30 — Matching Policy & Ranking Validation Benchmark Script.

Evaluates Current Production Matching Policy vs Proposed Offline Gated Policy
across 10 realistic evaluation scenarios (A through J).

THIS IS AN EVALUATION BENCHMARK SCRIPT ONLY.
DO NOT MODIFY PRODUCTION SCORING OR ACTIVATE GATED POLICIES IN PRODUCTION.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.matching_service import compute_match, compute_hybrid_match
from app.services.skill_service import SkillMatch, match_skills
from app.services.embedding_service import get_embedding_service

# Job Requirement Fixture
SAMPLE_JOB = {
    "title": "Senior Python Backend Engineer",
    "domain": "Web Development",
    "description": "Seeking a Senior Python Backend Engineer to build scalable web APIs using FastAPI, PostgreSQL, Docker, and AWS.",
    "required_skills": [("Python", 1.0), ("FastAPI", 1.0), ("PostgreSQL", 1.0)],
    "preferred_skills": [("Docker", 1.0), ("AWS", 1.0)],
}

# 10 Evaluation Scenarios (A through J)
EVALUATION_SCENARIOS = [
    {
        "id": "SCENARIO_A",
        "label": "ALL REQUIRED SKILLS PRESENT",
        "expected_rank": 1,
        "resume_text": "Senior Python Backend Engineer with 5 years experience building web APIs with FastAPI and PostgreSQL. Deployed applications on AWS using Docker containers.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python experience"),
            SkillMatch("FastAPI", "FastAPI", "Web Development", "backend", "FastAPI experience"),
            SkillMatch("PostgreSQL", "PostgreSQL", "Web Development", "databases", "PostgreSQL experience"),
            SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker experience"),
            SkillMatch("AWS", "AWS", "Cloud Computing", "aws", "AWS experience"),
        ],
        "domain": "Web Development",
    },
    {
        "id": "SCENARIO_B",
        "label": "ONE REQUIRED SKILL MISSING",
        "expected_rank": 2,
        "resume_text": "Python Backend Developer experienced in FastAPI, Docker, and AWS cloud deployments.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python experience"),
            SkillMatch("FastAPI", "FastAPI", "Web Development", "backend", "FastAPI experience"),
            SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker experience"),
            SkillMatch("AWS", "AWS", "Cloud Computing", "aws", "AWS experience"),
        ],
        "domain": "Web Development",
    },
    {
        "id": "SCENARIO_C",
        "label": "MULTIPLE REQUIRED SKILLS MISSING",
        "expected_rank": 4,
        "resume_text": "Developer proficient in Python and Docker containerization.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python experience"),
            SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker experience"),
        ],
        "domain": "Web Development",
    },
    {
        "id": "SCENARIO_D",
        "label": "ZERO REQUIRED SKILLS PRESENT BUT PREFERRED SKILLS PRESENT",
        "expected_rank": 5,
        "resume_text": "DevOps Engineer specializing in Docker containerization and AWS infrastructure automation.",
        "candidate_skills": [
            SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker experience"),
            SkillMatch("AWS", "AWS", "Cloud Computing", "aws", "AWS experience"),
        ],
        "domain": "DevOps",
    },
    {
        "id": "SCENARIO_E",
        "label": "ZERO REQUIRED AND ZERO PREFERRED SKILLS PRESENT",
        "expected_rank": 6,
        "resume_text": "Java Enterprise Developer with experience in Spring Boot, MySQL, and Hibernate ORM.",
        "candidate_skills": [],
        "domain": "Web Development",
    },
    {
        "id": "SCENARIO_F",
        "label": "REQUIRED SKILLS PRESENT BUT LOW SEMANTIC SIMILARITY",
        "expected_rank": 3,
        "resume_text": "Academic biology researcher who wrote Python scripts for parsing text and stored raw data in PostgreSQL databases during genetics thesis project.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python scripts"),
            SkillMatch("PostgreSQL", "PostgreSQL", "Web Development", "databases", "PostgreSQL database"),
        ],
        "domain": "Data Science",
    },
    {
        "id": "SCENARIO_G",
        "label": "HIGH SEMANTIC SIMILARITY BUT REQUIRED SKILLS MISSING",
        "expected_rank": 5,
        "resume_text": "Senior Systems Architect designing high-throughput microservices, distributed RPC protocols, relational storage, and container orchestration using Rust and C++.",
        "candidate_skills": [],
        "domain": "Web Development",
    },
    {
        "id": "SCENARIO_H",
        "label": "STRONG KEYWORD OVERLAP BUT WRONG DOMAIN",
        "expected_rank": 6,
        "resume_text": "Commercial Sales Executive who lists Python, FastAPI, and PostgreSQL under personal weekend hobbies on resume.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python hobby"),
            SkillMatch("FastAPI", "FastAPI", "Web Development", "backend", "FastAPI hobby"),
            SkillMatch("PostgreSQL", "PostgreSQL", "Web Development", "databases", "PostgreSQL hobby"),
        ],
        "domain": "Sales",
    },
    {
        "id": "SCENARIO_I",
        "label": "PARAPHRASED SKILLS WITH LOW EXACT-WORD OVERLAP",
        "expected_rank": 2,
        "resume_text": "Engineered asynchronous web microservices in Python backed by relational SQL datastores and containerized infrastructure.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python services"),
            SkillMatch("FastAPI", "FastAPI", "Web Development", "backend", "web microservices"),
            SkillMatch("PostgreSQL", "PostgreSQL", "Web Development", "databases", "SQL datastores"),
            SkillMatch("Docker", "Docker", "DevOps", "containers", "containerized"),
        ],
        "domain": "Web Development",
    },
    {
        "id": "SCENARIO_J",
        "label": "STRONG TECHNICAL MATCH WITH DIFFERENT WORDING",
        "expected_rank": 1,
        "resume_text": "Senior Server-Side Engineer developing scalable Python microservices using FastAPI framework, Postgres relational database, Docker, and Amazon Cloud.",
        "candidate_skills": [
            SkillMatch("Python", "Python", "Web Development", "backend", "Python microservices"),
            SkillMatch("FastAPI", "FastAPI", "Web Development", "backend", "FastAPI framework"),
            SkillMatch("PostgreSQL", "Postgres", "Web Development", "databases", "Postgres database"),
            SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker"),
            SkillMatch("AWS", "Amazon Cloud", "Cloud Computing", "aws", "Amazon Cloud"),
        ],
        "domain": "Web Development",
    },
]


def evaluate_policy() -> Dict[str, Any]:
    print("=========================================================")
    print("PHASE 30 — MATCHING POLICY & RANKING VALIDATION BENCHMARK")
    print("=========================================================\n")

    embedder = get_embedding_service()
    req_skills = SAMPLE_JOB["required_skills"]
    pref_skills = SAMPLE_JOB["preferred_skills"]
    job_text = SAMPLE_JOB["description"]
    job_domain = SAMPLE_JOB["domain"]

    results = []

    for scenario in EVALUATION_SCENARIOS:
        # 1. Current Production Match (Policy 1)
        base_res = compute_match(req_skills, pref_skills, scenario["candidate_skills"])
        hybrid_res = compute_hybrid_match(
            required_skills=req_skills,
            preferred_skills=pref_skills,
            candidate_skills=scenario["candidate_skills"],
            resume_text=scenario["resume_text"],
            job_description=job_text,
            predicted_domain=scenario["domain"],
            job_domain=job_domain,
            confidence="High",
        )

        curr_req_cov = base_res.required_coverage
        curr_pref_cov = base_res.preferred_coverage
        curr_base_score = base_res.combined_match
        curr_hybrid_score = hybrid_res.combined_match

        # 2. Proposed Offline Gated Policy (Policy 2)
        # Multiplier gate: Score * (ReqCoverage / 100)
        gated_multiplier = curr_req_cov / 100.0
        gated_base_score = round(curr_base_score * gated_multiplier, 2)
        gated_hybrid_score = round(curr_hybrid_score * gated_multiplier, 2)

        signals = hybrid_res.score_breakdown.get("signal_scores", {})

        results.append({
            "id": scenario["id"],
            "label": scenario["label"],
            "expected_rank": scenario["expected_rank"],
            "required_coverage": curr_req_cov,
            "preferred_coverage": curr_pref_cov,
            "semantic_similarity": signals.get("semantic_similarity", 0.0),
            "lexical_similarity": signals.get("lexical_similarity", 0.0),
            "policy_1_base_score": curr_base_score,
            "policy_1_hybrid_score": curr_hybrid_score,
            "policy_2_gated_base_score": gated_base_score,
            "policy_2_gated_hybrid_score": gated_hybrid_score,
            "missing_required": base_res.missing_required,
        })

    # Sort results by Policy 1 Hybrid vs Policy 2 Gated Hybrid
    p1_ranked = sorted(results, key=lambda x: x["policy_1_hybrid_score"], reverse=True)
    p2_ranked = sorted(results, key=lambda x: x["policy_2_gated_hybrid_score"], reverse=True)

    print("--- SCENARIO EVALUATION RESULTS TABLE ---")
    print(f"{'Scenario ID':<15} | {'Req Cov':<7} | {'Pref Cov':<8} | {'Semantic':<8} | {'P1 Hybrid':<9} | {'P2 Gated':<8} | {'Missing Req'}")
    print("-" * 85)
    for r in results:
        missing_str = ", ".join(r["missing_required"]) if r["missing_required"] else "None"
        print(f"{r['id']:<15} | {r['required_coverage']:<7}% | {r['preferred_coverage']:<8}% | {r['semantic_similarity']:<8}% | {r['policy_1_hybrid_score']:<9}% | {r['policy_2_gated_hybrid_score']:<8}% | {missing_str}")

    print("\n--- SPECIFIC MANDATORY-SKILL TEST (Scenario D vs Scenario A/B/C) ---")
    scen_d = next(r for r in results if r["id"] == "SCENARIO_D")
    print(f"Scenario D (0% Req, 100% Pref):")
    print(f"  - Policy 1 Base Score  : {scen_d['policy_1_base_score']}% (Demonstrates 30% baseline from preferred match)")
    print(f"  - Policy 1 Hybrid Score: {scen_d['policy_1_hybrid_score']}%")
    print(f"  - Policy 2 Gated Score : {scen_d['policy_2_gated_hybrid_score']}% (Correctly suppressed to 0.0%)")

    print("\n--- HYBRID SCORE POLICY TEST (Candidate G High Sem vs Candidate B High Req) ---")
    scen_g = next(r for r in results if r["id"] == "SCENARIO_G")
    scen_b = next(r for r in results if r["id"] == "SCENARIO_B")
    print(f"Scenario G (High Semantic 0% Req): P1 Hybrid = {scen_g['policy_1_hybrid_score']}%, P2 Gated = {scen_g['policy_2_gated_hybrid_score']}%")
    print(f"Scenario B (High Req 66.67% Req):  P1 Hybrid = {scen_b['policy_1_hybrid_score']}%, P2 Gated = {scen_b['policy_2_gated_hybrid_score']}%")
    print(f"Policy 1 Winner: {'Scenario G (Zero Req)' if scen_g['policy_1_hybrid_score'] > scen_b['policy_1_hybrid_score'] else 'Scenario B (High Req)'}")
    print(f"Policy 2 Winner: {'Scenario G (Zero Req)' if scen_g['policy_2_gated_hybrid_score'] > scen_b['policy_2_gated_hybrid_score'] else 'Scenario B (High Req)'}")

    # Ranking Quality Metrics (NDCG@3 and Precision@1)
    # Objective relevant set: Scenarios A, J, B, I (contain required skills in Web Dev context)
    rel_ids = {"SCENARIO_A", "SCENARIO_J", "SCENARIO_B", "SCENARIO_I"}
    p1_p1 = 1.0 if p1_ranked[0]["id"] in rel_ids else 0.0
    p2_p1 = 1.0 if p2_ranked[0]["id"] in rel_ids else 0.0

    p1_top3_rel = sum(1 for r in p1_ranked[:3] if r["id"] in rel_ids) / 3.0
    p2_top3_rel = sum(1 for r in p2_ranked[:3] if r["id"] in rel_ids) / 3.0

    print("\n--- RANKING QUALITY METRICS ---")
    print(f"Policy 1 (Current): Precision@1 = {p1_p1:.2f}, Precision@3 = {p1_top3_rel:.2f}")
    print(f"Policy 2 (Gated)  : Precision@1 = {p2_p1:.2f}, Precision@3 = {p2_top3_rel:.2f}")

    # Save benchmark report
    report_data = {
        "job": SAMPLE_JOB,
        "results": results,
        "p1_ranking": [r["id"] for r in p1_ranked],
        "p2_ranking": [r["id"] for r in p2_ranked],
        "metrics": {
            "p1_precision_at_1": p1_p1,
            "p1_precision_at_3": p1_top3_rel,
            "p2_precision_at_1": p2_p1,
            "p2_precision_at_3": p2_top3_rel,
        }
    }

    report_path = Path(__file__).resolve().parent.parent.parent / "reports" / "phase30_matching_policy_benchmark.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nSaved benchmark raw metrics to {report_path}")

    return report_data


if __name__ == "__main__":
    evaluate_policy()
