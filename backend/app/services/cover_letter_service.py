"""
backend/app/services/cover_letter_service.py

AI Cover Letter Generator Module.
Generates tailored, highly relevant cover letters aligning candidate resume background with target job requirements.

Factual Safety Rules:
  - Preserves exact factual candidate background.
  - Never invents unearned degrees, fictitious past employers, or fake years of experience.
  - Aligns candidate's real skills with target job requirements.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.ai_service import get_ai_service, validate_factual_guardrails

logger = logging.getLogger(__name__)

VALID_TONES = {"PROFESSIONAL", "ENTHUSIASTIC", "EXECUTIVE"}


@dataclass
class CoverLetterResult:
    salutation: str
    opening_hook: str
    core_value_proposition: str
    company_alignment_paragraph: str
    closing_call_to_action: str
    full_cover_letter: str
    tone_used: str
    tokens_used: int
    estimated_cost_usd: float
    guardrail_warnings: List[str] = field(default_factory=list)


def generate_cover_letter(
    job_title: str,
    company_name: str,
    candidate_name: Optional[str] = "Candidate",
    candidate_skills: Optional[List[str]] = None,
    candidate_text: Optional[str] = None,
    job_description: Optional[str] = None,
    tone: str = "PROFESSIONAL",
) -> CoverLetterResult:
    """
    Generate a structured, professional cover letter tailored to a job title and company.
    """
    tone_upper = tone.upper()
    if tone_upper not in VALID_TONES:
        tone_upper = "PROFESSIONAL"

    cand_name = candidate_name or "Candidate"
    skills_str = ", ".join(candidate_skills) if candidate_skills else "software engineering and technical problem solving"
    
    ai_service = get_ai_service()

    system_prompt = (
        "You are an executive career coach and recruitment consultant. "
        "Draft a compelling, highly personalized cover letter.\n"
        "FACTUAL RULE: Only reference skills and background provided. "
        "Do NOT invent unsupplied past employer names or fictitious degrees."
    )

    prompt = (
        f"Candidate Name: {cand_name}\n"
        f"Target Job Title: {job_title}\n"
        f"Target Company Name: {company_name}\n"
        f"Candidate Skills: {skills_str}\n"
        f"Tone: {tone_upper}\n"
        f"Job Details: {job_description[:300] if job_description else 'N/A'}\n"
        f"Candidate Summary: {candidate_text[:300] if candidate_text else 'N/A'}\n\n"
        f"Generate JSON output with fields:\n"
        f"- salutation: string\n"
        f"- opening_hook: string\n"
        f"- core_value_proposition: string\n"
        f"- company_alignment_paragraph: string\n"
        f"- closing_call_to_action: string\n"
        f"- full_cover_letter: string\n"
    )

    schema_desc = (
        '{\n'
        '  "salutation": "Dear Hiring Team at [Company],",\n'
        '  "opening_hook": "string",\n'
        '  "core_value_proposition": "string",\n'
        '  "company_alignment_paragraph": "string",\n'
        '  "closing_call_to_action": "string",\n'
        '  "full_cover_letter": "string"\n'
        '}'
    )

    response_data = ai_service.generate_json(prompt, schema_description=schema_desc, system_prompt=system_prompt)

    salutation = response_data.get("salutation", f"Dear Hiring Team at {company_name},")
    opening = response_data.get("opening_hook", f"I am writing to express my enthusiastic interest in the {job_title} role at {company_name}.")
    core_val = response_data.get("core_value_proposition", f"With expertise in {skills_str}, I have consistently delivered robust technical solutions.")
    comp_align = response_data.get("company_alignment_paragraph", f"I am deeply aligned with {company_name}'s commitment to innovation and engineering excellence.")
    closing = response_data.get("closing_call_to_action", f"I welcome the opportunity to discuss how my technical skills align with {company_name}'s goals. Thank you for your consideration.")
    
    full_text = response_data.get("full_cover_letter")
    if not full_text or "error" in response_data:
        full_text = f"{salutation}\n\n{opening}\n\n{core_val}\n\n{comp_align}\n\n{closing}\n\nSincerely,\n{cand_name}"

    warnings = validate_factual_guardrails(full_text, context=skills_str)

    return CoverLetterResult(
        salutation=salutation,
        opening_hook=opening,
        core_value_proposition=core_val,
        company_alignment_paragraph=comp_align,
        closing_call_to_action=closing,
        full_cover_letter=full_text,
        tone_used=tone_upper,
        tokens_used=len(prompt) // 4 + len(full_text) // 4,
        estimated_cost_usd=0.0,
        guardrail_warnings=warnings,
    )
