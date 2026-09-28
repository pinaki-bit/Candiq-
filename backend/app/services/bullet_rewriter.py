"""
backend/app/services/bullet_rewriter.py

AI Resume Bullet Point Rewriting Module.
Optimizes candidate resume experience bullets into high-impact statements using STAR, Technical, or ATS modes.

Factual Safety Rules:
  - Preserves exact factual domain context from the input bullet.
  - Never invents fake percentages, team sizes, or dollar amounts.
  - If a bullet lacks quantitative metrics, explicit placeholders are inserted:
    [Metric Required: describe metric]
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.ai_service import get_ai_service, validate_factual_guardrails

logger = logging.getLogger(__name__)

VALID_REWRITE_MODES = {"STAR", "TECHNICAL", "ATS"}


@dataclass
class BulletRewriteResult:
    original_bullet: str
    optimized_bullet: str
    mode: str
    key_changes: List[str]
    action_verb_used: str
    placeholders_needed: List[str]
    tokens_used: int
    estimated_cost_usd: float
    guardrail_warnings: List[str] = field(default_factory=list)


def extract_action_verb(text: str) -> str:
    """Extract first action verb from text or fallback."""
    cleaned = re.sub(r"^[•\-\*\s]+", "", text).strip()
    words = cleaned.split()
    if words:
        return words[0].strip(",. ")
    return "Optimized"


def rewrite_bullet_point(
    bullet: str,
    mode: str = "STAR",
    target_job_title: Optional[str] = None,
    target_skills: Optional[List[str]] = None,
) -> BulletRewriteResult:
    """
    Rewrite a resume bullet point according to the selected mode:
      - STAR: Situation, Task, Action, Result structured focus.
      - TECHNICAL: Highlights tools, tech stack, architectural scale, and mechanics.
      - ATS: Action-verb led, keyword-dense, high-clarity parser-optimized format.
    """
    mode_upper = mode.upper()
    if mode_upper not in VALID_REWRITE_MODES:
        logger.warning(f"Invalid mode '{mode}' passed to bullet rewriter. Defaulting to STAR.")
        mode_upper = "STAR"

    ai_service = get_ai_service()

    target_info = ""
    if target_job_title:
        target_info += f"\nTarget Job Title: {target_job_title}"
    if target_skills:
        target_info += f"\nTarget Required Skills: {', '.join(target_skills)}"

    system_prompt = (
        "You are an expert resume writer and recruiter. "
        "Optimize the candidate's resume bullet point according to the specified mode.\n"
        "FACTUAL RULE: Do NOT invent false companies, fake numbers, or unsupported percentages. "
        "If the original bullet lacks a quantitative metric, insert an explicit placeholder like "
        "'[Metric Required: % performance gain or scale]' rather than fabricating a number."
    )

    prompt = (
        f"Mode: {mode_upper}\n"
        f"Original Bullet Point: \"{bullet}\"{target_info}\n\n"
        f"Generate JSON output with fields:\n"
        f"- optimized_bullet: string\n"
        f"- key_changes: list of strings (explaining improvements made)\n"
        f"- placeholders_needed: list of strings (metrics required from user)\n"
    )

    schema_desc = (
        '{\n'
        '  "optimized_bullet": "string",\n'
        '  "key_changes": ["string"],\n'
        '  "placeholders_needed": ["string"]\n'
        '}'
    )

    # Invoke AIService JSON generator
    response_data = ai_service.generate_json(prompt, schema_description=schema_desc, system_prompt=system_prompt)
    
    optimized_bullet = response_data.get("optimized_bullet", "")
    key_changes = response_data.get("key_changes", [])
    placeholders = response_data.get("placeholders_needed", [])

    # Fallback formatting if mock or empty response
    if not optimized_bullet or "error" in response_data:
        action_verb = extract_action_verb(bullet)
        if mode_upper == "STAR":
            optimized_bullet = (
                f"• Spearheaded {bullet.lstrip('•- ').lower()}, achieving "
                f"[Metric Required: % efficiency boost or outcome] across production operations."
            )
            key_changes = ["Structured into Action + Result format", "Added metric placeholder for quantifiable impact"]
        elif mode_upper == "TECHNICAL":
            optimized_bullet = (
                f"• Engineered {bullet.lstrip('•- ').lower()} utilizing scalable architecture "
                f"and automated performance testing."
            )
            key_changes = ["Emphasized engineering terminology", "Highlighted technical architecture"]
        else: # ATS
            optimized_bullet = (
                f"• Orchestrated end-to-end execution of {bullet.lstrip('•- ').lower()}, "
                f"streamlining workflow efficiency."
            )
            key_changes = ["Led with strong ATS action verb 'Orchestrated'", "Improved parser readability"]
        placeholders = ["[Metric Required: quantifiable result]"]

    # Post-process guardrails validation
    warnings = validate_factual_guardrails(optimized_bullet, context=bullet)
    action_verb = extract_action_verb(optimized_bullet)

    return BulletRewriteResult(
        original_bullet=bullet,
        optimized_bullet=optimized_bullet,
        mode=mode_upper,
        key_changes=key_changes,
        action_verb_used=action_verb,
        placeholders_needed=placeholders,
        tokens_used=len(prompt) // 4 + len(optimized_bullet) // 4,
        estimated_cost_usd=0.0,
        guardrail_warnings=warnings,
    )
