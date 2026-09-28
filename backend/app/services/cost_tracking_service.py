"""
backend/app/services/cost_tracking_service.py

Phase 17: LLM Token Cost Tracking & Budget Guardrails Service.
Monitors token consumption and estimates USD costs across LLM models (OpenAI, Gemini).
"""

from __future__ import annotations

import datetime
import logging
from typing import Dict, List, Any
from app.schemas.cost_tracking import TokenUsageRecord, TokenUsageSummary

logger = logging.getLogger(__name__)

# Standard LLM API Pricing per 1,000 tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"prompt": 0.00015 / 1000, "completion": 0.00060 / 1000},
    "gpt-4o": {"prompt": 0.0025 / 1000, "completion": 0.0100 / 1000},
    "text-embedding-3-small": {"prompt": 0.00002 / 1000, "completion": 0.0},
    "gemini-1.5-flash": {"prompt": 0.000075 / 1000, "completion": 0.00030 / 1000},
    "gemini-1.5-pro": {"prompt": 0.00125 / 1000, "completion": 0.00500 / 1000},
    "mock-provider": {"prompt": 0.0, "completion": 0.0},
}


class CostTracker:
    """Manages token consumption records and calculates estimated USD operational costs."""

    def __init__(self, monthly_budget_usd: float = 50.0):
        self.monthly_budget_usd = monthly_budget_usd
        self.records: List[TokenUsageRecord] = []
        self._seed_default_logs()

    def _seed_default_logs(self):
        """Seed baseline telemetry entry for immediate dashboard metrics."""
        self.log_usage(
            model_name="gpt-4o-mini",
            prompt_tokens=1420,
            completion_tokens=380,
            endpoint="ai_service/bullet_rewriter",
        )
        self.log_usage(
            model_name="text-embedding-3-small",
            prompt_tokens=5200,
            completion_tokens=0,
            endpoint="embedding_service/hybrid_rank",
        )

    def calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["mock-provider"])
        cost = (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])
        return round(cost, 6)

    def log_usage(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        endpoint: str = "ai_service",
    ) -> TokenUsageRecord:
        total_tokens = prompt_tokens + completion_tokens
        cost = self.calculate_cost(model_name, prompt_tokens, completion_tokens)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        record = TokenUsageRecord(
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            endpoint=endpoint,
            timestamp=timestamp,
        )
        self.records.append(record)
        logger.info(f"Logged LLM cost: {model_name} ({total_tokens} tokens, ${cost:.6f} USD)")
        return record

    def get_summary(self) -> TokenUsageSummary:
        total_requests = len(self.records)
        total_prompt = sum(r.prompt_tokens for r in self.records)
        total_comp = sum(r.completion_tokens for r in self.records)
        total_tokens = sum(r.total_tokens for r in self.records)
        total_cost = sum(r.estimated_cost_usd for r in self.records)

        usage_by_model: Dict[str, Dict[str, Any]] = {}
        for r in self.records:
            m = r.model_name
            if m not in usage_by_model:
                usage_by_model[m] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
            usage_by_model[m]["requests"] += 1
            usage_by_model[m]["tokens"] += r.total_tokens
            usage_by_model[m]["cost_usd"] = round(usage_by_model[m]["cost_usd"] + r.estimated_cost_usd, 6)

        budget_remaining = max(0.0, self.monthly_budget_usd - total_cost)
        pct_used = (total_cost / self.monthly_budget_usd) * 100 if self.monthly_budget_usd > 0 else 0

        if pct_used > 90:
            status = "CRITICAL_BUDGET"
        elif pct_used > 75:
            status = "WARNING_BUDGET"
        else:
            status = "HEALTHY"

        return TokenUsageSummary(
            total_requests=total_requests,
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_comp,
            total_tokens=total_tokens,
            total_cost_usd=round(total_cost, 6),
            usage_by_model=usage_by_model,
            budget_limit_usd=self.monthly_budget_usd,
            budget_remaining_usd=round(budget_remaining, 6),
            budget_status=status,
        )

    def clear(self):
        self.records.clear()


# Singleton instance
cost_tracker = CostTracker()
