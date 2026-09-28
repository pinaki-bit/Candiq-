"""
backend/app/schemas/cost_tracking.py

Phase 17: Performance Optimization & LLM Token Cost Tracking Schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TokenUsageRecord(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_name: str = Field(..., description="LLM model name (e.g. gpt-4o-mini, gemini-1.5-flash)")
    prompt_tokens: int = Field(..., description="Number of prompt/input tokens used")
    completion_tokens: int = Field(..., description="Number of completion/output tokens generated")
    total_tokens: int = Field(..., description="Total tokens used")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    endpoint: str = Field("ai_service", description="Source endpoint or module name")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")


class TokenUsageSummary(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    usage_by_model: Dict[str, Dict[str, Any]] = {}
    budget_limit_usd: float = 50.0
    budget_remaining_usd: float = 50.0
    budget_status: str = "HEALTHY"
