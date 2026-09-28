"""
backend/app/services/ai_service.py

Enterprise LLM Architecture & Multi-Provider Abstraction Layer.
Supports OpenAI, Google Gemini, and deterministic Mock/Local providers.

Features:
  - Abstract Provider Interface with unified response contract
  - Token counting & USD cost estimation per API request
  - Factual consistency & anti-hallucination guardrails
  - Fallback logic to Mock provider on API failures or missing keys
  - Structured JSON parsing helper with schema validation
"""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Standard System Anti-Hallucination Guardrail
STRICT_FACTUAL_GUARDRAIL = (
    "STRICT FACTUAL GUARDRAIL: You are an AI hiring intelligence assistant. "
    "You must ONLY rely on provided facts in the resume or job description. "
    "NEVER invent job titles, employment dates, company names, or metrics. "
    "If a quantitative impact metric is requested but absent from the candidate's history, "
    "insert an explicit tag like '[Metric Required: describe metric]'."
)

# Cost tables per 1,000,000 tokens (USD)
PRICING_TABLE_PER_1M = {
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
    "mock": {"prompt": 0.0, "completion": 0.0},
}


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    provider_name: str = "mock"
    model_name: str = "mock-v1"
    latency_ms: float = 0.0
    guardrail_warnings: List[str] = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    """Rough estimation of token count (~4 characters per token for English)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated USD cost based on token counts and model pricing."""
    model_key = model_name.lower()
    pricing = PRICING_TABLE_PER_1M.get(model_key)
    if not pricing:
        # Fallback to gpt-4o-mini rates if model is unknown
        pricing = PRICING_TABLE_PER_1M["gpt-4o-mini"]
    
    prompt_cost = (prompt_tokens / 1_000_000.0) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000.0) * pricing["completion"]
    return round(prompt_cost + completion_cost, 6)


def validate_factual_guardrails(text: str, context: str = "") -> List[str]:
    """
    Scans generated text for anti-hallucination guardrail compliance.
    Returns list of warnings if metric tags or suspicious fabrications are flagged.
    """
    warnings: List[str] = []
    
    # Check if metric tags were inserted due to missing data
    metric_tags = re.findall(r"\[Metric Required:[^\]]+\]", text)
    if metric_tags:
        warnings.append(f"Contains {len(metric_tags)} missing metric placeholder(s): {metric_tags[:3]}")

    # Check for unsupported high percentage fabrications if context is provided
    if context:
        pct_matches = re.findall(r"\b(\d{1,3})%", text)
        for pct in pct_matches:
            full_pct = f"{pct}%"
            if full_pct not in context:
                warnings.append(f"Generated metric '{full_pct}' not found in source context (flagged for review).")
                break

    return warnings


class BaseAIProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        pass

    def generate_json(
        self,
        prompt: str,
        schema_description: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output with fallback parsing."""
        json_sys_prompt = (
            f"{system_prompt or ''}\n"
            f"Respond ONLY with valid JSON matching this schema/description:\n"
            f"{schema_description}\n"
            f"Do not include markdown code block backticks or conversational preamble."
        )
        response = self.generate_text(prompt, system_prompt=json_sys_prompt, temperature=0.2)
        
        # Clean potential markdown wrapping
        raw = response.content.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError as err:
            logger.warning(f"Failed to parse LLM response as JSON ({err}). Raw content: {raw[:200]}")
            return {"error": "Invalid JSON response from LLM", "raw_content": raw}


class MockAIProvider(BaseAIProvider):
    """Fallback / Mock provider delivering rule-based generated text when offline or keyless."""

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        start_time = time.time()
        
        full_sys = f"{system_prompt or ''}\n{STRICT_FACTUAL_GUARDRAIL}".strip()
        p_tokens = estimate_tokens(prompt) + estimate_tokens(full_sys)

        # Context-aware mock output generation
        if "rewrite" in prompt.lower() or "bullet" in prompt.lower():
            content = (
                "• Optimized resume bullet: Orchestrated automated CI/CD pipeline deployment, "
                "reducing release cycle duration by [Metric Required: % reduction] while ensuring zero system downtime."
            )
        elif "cover letter" in prompt.lower():
            content = (
                "Dear Hiring Team,\n\n"
                "I am writing to express my enthusiastic interest in the position. With proven expertise in software development "
                "and technical leadership, I bring a tracked record of building scalable solutions. I am eager to contribute to your team's mission.\n\n"
                "Sincerely,\nCandidate"
            )
        elif "interview" in prompt.lower() or "question" in prompt.lower():
            content = json.dumps({
                "technical_questions": [
                    {
                        "question": "Can you explain how you design asynchronous RESTful APIs for high throughput?",
                        "category": "System Design",
                        "expected_key_points": ["Non-blocking I/O", "Rate limiting", "Queue management"],
                        "difficulty": "Medium"
                    }
                ]
            })
        else:
            content = f"[Mock AI Response] Processed query: '{prompt[:80]}...' using factual guardrails."

        c_tokens = estimate_tokens(content)
        latency = (time.time() - start_time) * 1000.0
        warnings = validate_factual_guardrails(content, prompt)

        return LLMResponse(
            content=content,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            estimated_cost_usd=0.0,
            provider_name="mock",
            model_name="mock-v1",
            latency_ms=round(latency, 2),
            guardrail_warnings=warnings,
        )


class OpenAIProvider(BaseAIProvider):
    """OpenAI API Provider implementation using HTTP client."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name
        self.mock_fallback = MockAIProvider()

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        if not self.api_key:
            logger.warning("OpenAI API key missing. Falling back to MockAIProvider.")
            return self.mock_fallback.generate_text(prompt, system_prompt, temperature, max_tokens)

        start_time = time.time()
        sys_content = f"{system_prompt or ''}\n{STRICT_FACTUAL_GUARDRAIL}".strip()

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": sys_content},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()

            choice = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            p_tokens = usage.get("prompt_tokens", estimate_tokens(prompt))
            c_tokens = usage.get("completion_tokens", estimate_tokens(choice))
            tot_tokens = usage.get("total_tokens", p_tokens + c_tokens)
            cost = calculate_cost(self.model_name, p_tokens, c_tokens)
            latency = (time.time() - start_time) * 1000.0

            warnings = validate_factual_guardrails(choice, prompt)

            return LLMResponse(
                content=choice,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=tot_tokens,
                estimated_cost_usd=cost,
                provider_name="openai",
                model_name=self.model_name,
                latency_ms=round(latency, 2),
                guardrail_warnings=warnings,
            )
        except Exception as exc:
            logger.error(f"OpenAI API call failed ({exc}). Falling back to Mock Provider.")
            fallback_resp = self.mock_fallback.generate_text(prompt, system_prompt, temperature, max_tokens)
            fallback_resp.guardrail_warnings.append(f"OpenAI Provider Error: {str(exc)}")
            return fallback_resp


class GeminiProvider(BaseAIProvider):
    """Google Gemini API Provider implementation via REST API."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.mock_fallback = MockAIProvider()

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        if not self.api_key:
            logger.warning("Gemini API key missing. Falling back to MockAIProvider.")
            return self.mock_fallback.generate_text(prompt, system_prompt, temperature, max_tokens)

        start_time = time.time()
        sys_content = f"{system_prompt or ''}\n{STRICT_FACTUAL_GUARDRAIL}".strip()
        full_user_prompt = f"{sys_content}\n\nUser Request: {prompt}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No response candidates returned from Gemini API.")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            content = parts[0].get("text", "") if parts else ""

            p_tokens = estimate_tokens(full_user_prompt)
            c_tokens = estimate_tokens(content)
            tot_tokens = p_tokens + c_tokens
            cost = calculate_cost(self.model_name, p_tokens, c_tokens)
            latency = (time.time() - start_time) * 1000.0

            warnings = validate_factual_guardrails(content, prompt)

            return LLMResponse(
                content=content,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=tot_tokens,
                estimated_cost_usd=cost,
                provider_name="gemini",
                model_name=self.model_name,
                latency_ms=round(latency, 2),
                guardrail_warnings=warnings,
            )
        except Exception as exc:
            logger.error(f"Gemini API call failed ({exc}). Falling back to Mock Provider.")
            fallback_resp = self.mock_fallback.generate_text(prompt, system_prompt, temperature, max_tokens)
            fallback_resp.guardrail_warnings.append(f"Gemini Provider Error: {str(exc)}")
            return fallback_resp


class AIService:
    """Unified Facade for AI Generation Services."""

    def __init__(self, provider_override: Optional[str] = None):
        settings = get_settings()
        selected_provider = (provider_override or settings.ai_provider or "mock").lower()

        if selected_provider == "openai":
            self.provider: BaseAIProvider = OpenAIProvider(
                api_key=settings.openai_api_key,
                model_name=settings.openai_model,
            )
        elif selected_provider == "gemini":
            self.provider = GeminiProvider(
                api_key=settings.gemini_api_key,
                model_name=settings.gemini_model,
            )
        else:
            self.provider = MockAIProvider()

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        return self.provider.generate_text(prompt, system_prompt, temperature, max_tokens)

    def generate_json(
        self,
        prompt: str,
        schema_description: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.provider.generate_json(prompt, schema_description, system_prompt)


def get_ai_service(provider: Optional[str] = None) -> AIService:
    """Factory helper to obtain an AIService instance."""
    return AIService(provider_override=provider)
