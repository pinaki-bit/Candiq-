"""
backend/app/services/interview_service.py

AI Interview Intelligence Engine.
Generates grounded 5-category technical interview questions with evaluation criteria and 'Why this question?' mapping.

Categories:
  1. Technical Fundamentals
  2. Practical Implementation
  3. Project-Based Deep Dive
  4. Scenario-Based Problem Solving
  5. Verification / Claim Validation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.ai_service import get_ai_service, validate_factual_guardrails

logger = logging.getLogger(__name__)

INTERVIEW_CATEGORIES = [
    "Technical Fundamentals",
    "Practical Implementation",
    "Project-Based Deep Dive",
    "Scenario-Based Problem Solving",
    "Verification / Claim Validation",
]


@dataclass
class InterviewQuestion:
    question_id: int
    category: str
    question: str
    why_this_question: str
    expected_key_points: List[str]
    difficulty: str


@dataclass
class InterviewKitResult:
    job_title: str
    questions: List[InterviewQuestion]
    tokens_used: int
    estimated_cost_usd: float
    guardrail_warnings: List[str] = field(default_factory=list)


def generate_interview_kit(
    job_title: str = "Software Engineer",
    candidate_skills: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
    resume_text: Optional[str] = None,
    job_description: Optional[str] = None,
) -> InterviewKitResult:
    """
    Generate a 5-category technical interview question kit grounded in candidate background and skill gaps.
    """
    ai_service = get_ai_service()

    skills_str = ", ".join(candidate_skills) if candidate_skills else "Python, SQL, REST APIs"
    missing_str = ", ".join(missing_skills) if missing_skills else "Kubernetes, System Design"

    system_prompt = (
        "You are an expert technical interviewer and engineering director. "
        "Generate exactly 5 grounded interview questions covering the 5 mandated categories:\n"
        "1. Technical Fundamentals\n"
        "2. Practical Implementation\n"
        "3. Project-Based Deep Dive\n"
        "4. Scenario-Based Problem Solving\n"
        "5. Verification / Claim Validation\n\n"
        "Each question MUST include a 'why_this_question' field explaining how it relates to the candidate's resume or skill gaps."
    )

    prompt = (
        f"Target Job Title: {job_title}\n"
        f"Candidate Verified Skills: {skills_str}\n"
        f"Missing / Gap Skills: {missing_str}\n"
        f"Resume Excerpt: {resume_text[:300] if resume_text else 'N/A'}\n\n"
        f"Generate JSON output containing a list of 5 question objects matching the schema."
    )

    schema_desc = (
        '{\n'
        '  "questions": [\n'
        '    {\n'
        '      "question_id": 1,\n'
        '      "category": "Technical Fundamentals",\n'
        '      "question": "string",\n'
        '      "why_this_question": "string",\n'
        '      "expected_key_points": ["string"],\n'
        '      "difficulty": "Medium"\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    response_data = ai_service.generate_json(prompt, schema_description=schema_desc, system_prompt=system_prompt)

    raw_questions = response_data.get("questions", [])
    question_objects: List[InterviewQuestion] = []

    if raw_questions and isinstance(raw_questions, list) and len(raw_questions) >= 5:
        for idx, q in enumerate(raw_questions[:5], 1):
            question_objects.append(
                InterviewQuestion(
                    question_id=idx,
                    category=q.get("category", INTERVIEW_CATEGORIES[(idx - 1) % 5]),
                    question=q.get("question", f"Explain core principles of {skills_str.split(',')[0]}."),
                    why_this_question=q.get("why_this_question", "Mapped to candidate's primary skill set."),
                    expected_key_points=q.get("expected_key_points", ["Core architecture", "Best practices"]),
                    difficulty=q.get("difficulty", "Medium"),
                )
            )
    else:
        # Structured rule-based fallback for 5 categories
        first_skill = candidate_skills[0] if candidate_skills else "Python"
        gap_skill = missing_skills[0] if missing_skills else "Distributed Systems"

        question_objects = [
            InterviewQuestion(
                question_id=1,
                category="Technical Fundamentals",
                question=f"Can you explain the memory management and execution model when utilizing {first_skill} in high-throughput backend services?",
                why_this_question=f"Verified core skill on candidate's resume: {first_skill}.",
                expected_key_points=["Garbage collection / reference counting", "Concurrency models", "Resource optimization"],
                difficulty="Medium",
            ),
            InterviewQuestion(
                question_id=2,
                category="Practical Implementation",
                question=f"How would you design a rate-limited RESTful API endpoint using {skills_str}?",
                why_this_question="Tests practical implementation capability based on claimed API experience.",
                expected_key_points=["Token bucket or sliding window algorithm", "HTTP status codes (429)", "Redis cache integration"],
                difficulty="Medium",
            ),
            InterviewQuestion(
                question_id=3,
                category="Project-Based Deep Dive",
                question="Walk us through the most technically complex architectural decision you made in your recent project. What trade-offs were evaluated?",
                why_this_question="Evaluates depth of engineering ownership in past work experience.",
                expected_key_points=["Problem statement", "Alternative architectures evaluated", "Quantified performance metrics"],
                difficulty="Hard",
            ),
            InterviewQuestion(
                question_id=4,
                category="Scenario-Based Problem Solving",
                question="Suppose a microservice experiences sudden memory spikes during peak traffic. What step-by-step diagnostic workflow would you employ?",
                why_this_question="Assesses incident response and live system troubleshooting under pressure.",
                expected_key_points=["Log analysis & metrics collection", "Profiling tools", "Graceful degradation / circuit breakers"],
                difficulty="Hard",
            ),
            InterviewQuestion(
                question_id=5,
                category="Verification / Claim Validation",
                question=f"Your profile indicates experience relevant to {job_title}, but lacks verified experience in {gap_skill}. How have you approached learning or working with {gap_skill}?",
                why_this_question=f"Probes explicit skill gap: {gap_skill}.",
                expected_key_points=["Self-learning capability", "Transferable knowledge", "Hands-on project initiative"],
                difficulty="Medium",
            ),
        ]

    warnings = validate_factual_guardrails("\n".join(q.question for q in question_objects), context=skills_str)

    return InterviewKitResult(
        job_title=job_title,
        questions=question_objects,
        tokens_used=len(prompt) // 4 + sum(len(q.question) for q in question_objects) // 4,
        estimated_cost_usd=0.0,
        guardrail_warnings=warnings,
    )
