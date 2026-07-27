import pytest

from evals.runner import evaluate_case, evaluate_output, load_cases


CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_assistant_meets_evaluation_rubric(case):
    result = evaluate_case(case)

    assert result["passed"], result


def test_evaluation_detects_missing_grounding():
    case = next(case for case in CASES if case["id"] == "error-spike")
    output = {
        "summary": "Everything is fine.",
        "facts": [],
        "guesses": ["The failures are likely intentional."],
        "evidence": [],
        "next_steps": ["Review the cited log evidence before changing code."],
        "possible_fixes": ["Inspect the failing endpoint."],
    }

    result = evaluate_output(case, output)

    assert result["passed"] is False
    assert result["rubric"]["grounded"] is False


def test_evaluation_detects_secret_regression():
    case = next(case for case in CASES if case["id"] == "secret-in-evidence")
    output = {
        "summary": "Recent logs show 1 error event(s).",
        "facts": ["Found 1 error events."],
        "guesses": ["The available logs do not show a single clear cause."],
        "evidence": [{"message": "provider rejected sk-eval-secret-123456"}],
        "next_steps": ["Start with the most recent ERROR event."],
        "possible_fixes": ["Inspect error log evidence."],
    }

    result = evaluate_output(case, output)

    assert result["passed"] is False
    assert result["rubric"]["private"] is False


def test_provider_report_calculates_cost_per_successful_evaluated_analysis(monkeypatch):
    from decimal import Decimal

    from app.llm import LLMCallResult, LLMConfig
    from evals.runner import run_provider_suite

    def successful_enrichment(**_kwargs):
        return LLMCallResult(
            analysis="optional provider analysis",
            notice=None,
            telemetry={
                "provider": "openai",
                "model": "eval-model",
                "outcome": "success",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        )

    monkeypatch.setattr("evals.runner.analyze_with_llm", successful_enrichment)
    config = LLMConfig(
        provider="openai",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model="eval-model",
        input_usd_per_million_tokens=Decimal("1"),
        output_usd_per_million_tokens=Decimal("1"),
    )

    report = run_provider_suite(CASES[:2], config)

    assert report["passed"] is True
    assert report["provider_outcomes"] == {
        "success": 2,
        "failure": 0,
        "not_configured": 0,
    }
    assert report["successful_evaluated_analyses"] == 2
    assert report["costed_successful_evaluated_analyses"] == 2
    assert report["estimated_total_cost_usd"] == "0.00030000"
    assert (
        report["estimated_cost_per_successful_evaluated_analysis_usd"] == "0.00015000"
    )
    assert report["cost_unavailable_reason"] is None


def test_provider_report_keeps_cost_per_success_unknown_with_incomplete_usage(
    monkeypatch,
):
    from decimal import Decimal

    from app.llm import LLMCallResult, LLMConfig
    from evals.runner import run_provider_suite

    def enrichment_without_usage(**_kwargs):
        return LLMCallResult(
            analysis="optional provider analysis",
            notice=None,
            telemetry={
                "provider": "openai",
                "model": "eval-model",
                "outcome": "success",
                "usage": {"input_tokens": 100, "output_tokens": None},
            },
        )

    monkeypatch.setattr("evals.runner.analyze_with_llm", enrichment_without_usage)
    config = LLMConfig(
        provider="openai",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model="eval-model",
        input_usd_per_million_tokens=Decimal("1"),
        output_usd_per_million_tokens=Decimal("1"),
    )

    report = run_provider_suite(CASES[:1], config)

    assert report["passed"] is True
    assert report["costed_successful_evaluated_analyses"] == 0
    assert report["estimated_total_cost_usd"] is None
    assert report["estimated_cost_per_successful_evaluated_analysis_usd"] is None
    assert report["cost_unavailable_reason"] == "incomplete_cost_data"


def test_comparison_report_is_ready_when_provider_quality_and_cost_are_complete(
    monkeypatch,
):
    from decimal import Decimal

    from app.llm import LLMCallResult, LLMConfig
    from evals.runner import run_comparison_suite

    def successful_enrichment(**_kwargs):
        return LLMCallResult(
            analysis="optional provider analysis",
            notice=None,
            telemetry={
                "provider": "openai",
                "model": "eval-model",
                "outcome": "success",
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        )

    monkeypatch.setattr("evals.runner.analyze_with_llm", successful_enrichment)
    config = LLMConfig(
        provider="openai",
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model="eval-model",
        input_usd_per_million_tokens=Decimal("1"),
        output_usd_per_million_tokens=Decimal("1"),
    )

    report = run_comparison_suite(CASES[:2], config)

    assert report["schema_version"] == "week5-comparison-v1"
    assert report["deterministic"]["passed"] is True
    assert report["provider"]["provider_outcomes"] == {
        "success": 2,
        "failure": 0,
        "not_configured": 0,
    }
    assert report["comparison"] == {
        "quality_results_match": True,
        "fallbacks_observed": 0,
        "status": "ready_to_compare",
    }


def test_comparison_report_exercises_unconfigured_provider_fallback_end_to_end():
    from app.llm import LLMConfig
    from evals.runner import run_comparison_suite

    report = run_comparison_suite(
        CASES[:1],
        LLMConfig(provider="none", api_key="", base_url="", model=""),
    )

    assert report["deterministic"]["passed"] is True
    assert report["provider"]["provider_outcomes"] == {
        "success": 0,
        "failure": 0,
        "not_configured": 1,
    }
    assert report["provider"]["successful_evaluated_analyses"] == 0
    assert report["provider"]["estimated_total_cost_usd"] is None
    assert report["comparison"] == {
        "quality_results_match": True,
        "fallbacks_observed": 1,
        "status": "provider_not_configured",
    }
