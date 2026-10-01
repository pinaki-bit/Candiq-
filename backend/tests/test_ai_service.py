"""
backend/tests/test_ai_service.py

Unit test suite for Phase 5: LLM Architecture & Multi-Provider Abstraction Layer.
"""

import pytest
from app.services.ai_service import (
    AIService,
    GeminiProvider,
    MockAIProvider,
    OpenAIProvider,
    calculate_cost,
    estimate_tokens,
    get_ai_service,
    validate_factual_guardrails,
)


def test_estimate_tokens():
    text = "Hello world, this is a test string for token estimation."
    tokens = estimate_tokens(text)
    assert tokens > 0
    assert tokens == len(text) // 4


def test_calculate_cost():
    # Test gpt-4o-mini pricing
    cost = calculate_cost("gpt-4o-mini", 1000, 1000)
    assert cost > 0.0
    # prompt: 0.001 * 0.15 = 0.00015, completion: 0.001 * 0.60 = 0.0006 -> 0.00075
    assert abs(cost - 0.00075) < 0.00001


def test_mock_ai_provider_text_generation():
    provider = MockAIProvider()
    response = provider.generate_text(
        prompt="Lead software engineering team.",
        system_prompt="You are a professional resume writer.",
    )
    assert response.provider_name == "mock"
    assert response.model_name == "mock-v1"
    assert response.content != ""
    assert response.total_tokens > 0
    assert response.estimated_cost_usd == 0.0


def test_mock_ai_provider_json_generation():
    provider = MockAIProvider()
    result = provider.generate_json(
        prompt="Generate interview questions for Python developer.",
        schema_description="{ 'questions': list }",
    )
    assert isinstance(result, dict)
    assert "questions" in result or "technical_questions" in result


def test_openai_provider_fallback_without_key():
    provider = OpenAIProvider(api_key="", model_name="gpt-4o-mini")
    response = provider.generate_text("Test prompt without key")
    # Phase 34: Must NOT silently pretend mock response is real AI
    assert response.provider_name == "openai"
    assert response.provider_status == "provider_unavailable"


def test_gemini_provider_fallback_without_key():
    provider = GeminiProvider(api_key="", model_name="gemini-1.5-flash")
    response = provider.generate_text("Test prompt without key")
    # Phase 34: Must NOT silently pretend mock response is real AI
    assert response.provider_name == "gemini"
    assert response.provider_status == "provider_unavailable"


def test_ai_service_factory_mock():
    service = get_ai_service(provider="mock")
    response = service.generate_text("Explain microservices architecture")
    assert response.content != ""
    assert isinstance(response.guardrail_warnings, list)


def test_guardrail_validation_flags_missing_metrics():
    text = "Achieved higher efficiency by redesigning system [Metric Required: % reduction]."
    warnings = validate_factual_guardrails(text, context="Worked on backend.")
    assert len(warnings) > 0
    assert "missing metric" in warnings[0].lower()


def test_guardrail_validation_flags_unsupported_percentages():
    context = "Increased sales and managed team."
    text = "Increased sales by 99% across all regions."
    warnings = validate_factual_guardrails(text, context=context)
    assert len(warnings) > 0
    assert "99%" in warnings[0]
