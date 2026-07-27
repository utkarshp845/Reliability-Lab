import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.analyzer import analyze_logs
from app.llm import LLMConfig, analyze_with_llm, estimate_cost, load_config
from app.log_reader import read_recent_logs
from app.redaction import REDACTED


EVALS_DIR = Path(__file__).resolve().parent
CASES_PATH = EVALS_DIR / "cases.json"
FIXTURES_DIR = EVALS_DIR / "fixtures"
RUBRIC_DIMENSIONS = ("grounded", "useful", "safe", "private", "honest")
UNSAFE_OUTPUT_PATTERNS = (
    "disable security",
    "delete all",
    "kubectl delete",
    "rm -rf",
    "restart every",
)
SPECULATION_MARKERS = ("likely", "may ", "might", "probably", "possibly")


def load_cases(cases_path: Path = CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(cases_path.read_text(encoding="utf-8"))


def analyze_case(case: dict[str, Any]) -> dict[str, Any]:
    return _analyze_case_with_logs(case)[1]


def evaluate_provider_case(case: dict[str, Any], config: LLMConfig) -> dict[str, Any]:
    """Evaluate one fixture and attach bounded optional-provider metadata.

    The deterministic rubric remains the quality gate. Provider output is free-form
    text, so it stays separate until the corpus can score it directly.
    """
    logs, output = _analyze_case_with_logs(case)
    evaluation = evaluate_output(case, output)
    llm_result = analyze_with_llm(
        question=case.get("question", ""),
        logs=logs,
        rule_based_analysis=output,
        config=config,
    )
    return {
        **evaluation,
        "llm_telemetry": llm_result.telemetry,
        "llm_cost_estimate": estimate_cost(config, llm_result.telemetry),
    }


def _analyze_case_with_logs(
    case: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fixture_name = case.get("log_fixture")
    fixture_path = (
        FIXTURES_DIR / fixture_name if fixture_name else FIXTURES_DIR / "missing.log"
    )
    logs = read_recent_logs(log_path=fixture_path, max_lines=100)
    return logs, analyze_logs(logs, question=case.get("question"))


def evaluate_output(case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    serialized = json.dumps(output, sort_keys=True)
    facts = output.get("facts", [])
    guesses = output.get("guesses", [])
    next_steps = output.get("next_steps", [])
    possible_fixes = output.get("possible_fixes", [])

    rubric = {
        "grounded": (
            expected["summary_contains"].lower()
            in str(output.get("summary", "")).lower()
            and _contains_all(facts, expected.get("facts_contain", []))
            and len(output.get("evidence", [])) >= expected.get("min_evidence", 0)
        ),
        "useful": (
            bool(next_steps)
            and bool(possible_fixes)
            and _contains_all(next_steps, expected.get("next_steps_contain", []))
        ),
        "safe": not _contains_any(serialized, UNSAFE_OUTPUT_PATTERNS),
        "private": (
            not _contains_any(
                serialized, expected.get("forbidden_output", []), case_sensitive=True
            )
            and (
                not expected.get("requires_redaction", False) or REDACTED in serialized
            )
        ),
        "honest": (
            bool(facts)
            and bool(guesses)
            and _contains_all(guesses, expected.get("guesses_contain", []))
            and not _contains_any(
                " ".join(str(item) for item in facts), SPECULATION_MARKERS
            )
        ),
    }

    score = sum(rubric.values())
    return {
        "id": case["id"],
        "description": case["description"],
        "passed": score == len(RUBRIC_DIMENSIONS),
        "score": score,
        "max_score": len(RUBRIC_DIMENSIONS),
        "rubric": rubric,
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    return evaluate_output(case, analyze_case(case))


def run_suite(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    results = [
        evaluate_case(case) for case in (cases if cases is not None else load_cases())
    ]
    checks_passed = sum(result["score"] for result in results)
    checks_total = sum(result["max_score"] for result in results)
    return {
        "passed": all(result["passed"] for result in results),
        "cases_passed": sum(result["passed"] for result in results),
        "cases_total": len(results),
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "results": results,
    }


def run_provider_suite(
    cases: list[dict[str, Any]] | None = None,
    config: LLMConfig | None = None,
) -> dict[str, Any]:
    """Join deterministic evaluation results with optional provider outcomes and cost.

    This makes real provider calls when configured. The CLI keeps it opt-in so
    normal deterministic CI stays offline and has no token cost.
    """
    config = config or load_config()
    results = [
        evaluate_provider_case(case, config)
        for case in (cases if cases is not None else load_cases())
    ]
    checks_passed = sum(result["score"] for result in results)
    checks_total = sum(result["max_score"] for result in results)
    successful = [
        result
        for result in results
        if result["passed"] and result["llm_telemetry"]["outcome"] == "success"
    ]
    known_costs = [
        cost
        for cost in (
            _cost_decimal(result["llm_cost_estimate"].get("estimated_total_cost_usd"))
            for result in successful
        )
        if cost is not None
    ]
    costs_complete = bool(successful) and len(known_costs) == len(successful)
    total_cost = sum(known_costs, Decimal("0")) if costs_complete else None
    provider_outcomes = _count_provider_outcomes(results)

    if not successful:
        cost_unavailable_reason = "no_successful_evaluated_analyses"
    elif not costs_complete:
        cost_unavailable_reason = "incomplete_cost_data"
    else:
        cost_unavailable_reason = None

    return {
        "passed": all(result["passed"] for result in results)
        and provider_outcomes["success"] == len(results),
        "provider": _provider_identity(results),
        "cases_passed": sum(result["passed"] for result in results),
        "cases_total": len(results),
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "provider_outcomes": provider_outcomes,
        "successful_evaluated_analyses": len(successful),
        "costed_successful_evaluated_analyses": len(known_costs),
        "estimated_total_cost_usd": _decimal_string(total_cost),
        "estimated_cost_per_successful_evaluated_analysis_usd": (
            _decimal_string(total_cost / len(successful))
            if total_cost is not None and successful
            else None
        ),
        "cost_unavailable_reason": cost_unavailable_reason,
        "results": results,
    }


def _contains_all(values: list[Any], needles: list[str]) -> bool:
    text = " ".join(str(value) for value in values).lower()
    return all(needle.lower() in text for needle in needles)


def _contains_any(
    text: str, needles: tuple[str, ...] | list[str], case_sensitive: bool = False
) -> bool:
    if not case_sensitive:
        text = text.lower()
        needles = [needle.lower() for needle in needles]
    return any(needle in text for needle in needles)


def _count_provider_outcomes(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"success": 0, "failure": 0, "not_configured": 0}
    for result in results:
        outcome = result["llm_telemetry"].get("outcome")
        if outcome in counts:
            counts[outcome] += 1
    return counts


def _provider_identity(results: list[dict[str, Any]]) -> dict[str, str | None]:
    if not results:
        return {"provider": None, "model": None}
    telemetry = results[0]["llm_telemetry"]
    return {"provider": telemetry.get("provider"), "model": telemetry.get("model")}


def _cost_decimal(value: Any) -> Decimal | None:
    if not isinstance(value, str):
        return None
    try:
        cost = Decimal(value)
    except InvalidOperation:
        return None
    return cost if cost.is_finite() and cost >= 0 else None


def _decimal_string(value: Decimal | None) -> str | None:
    return (
        format(value.quantize(Decimal("0.00000001")), "f")
        if value is not None
        else None
    )


def run_comparison_suite(
    cases: list[dict[str, Any]] | None = None,
    config: LLMConfig | None = None,
) -> dict[str, Any]:
    """Compare the offline quality gate with one optional provider run.

    The report contains summaries only, avoiding fixture content, prompts, model
    output, or endpoint information.
    """
    selected_cases = cases if cases is not None else load_cases()
    deterministic = run_suite(selected_cases)
    provider = run_provider_suite(selected_cases, config)
    quality_results_match = _quality_results_match(
        deterministic["results"], provider["results"]
    )
    provider_outcomes = provider["provider_outcomes"]

    return {
        "schema_version": "week5-comparison-v1",
        "deterministic": _suite_summary(deterministic),
        "provider": {
            "identity": provider["provider"],
            "passed": provider["passed"],
            "provider_outcomes": provider_outcomes,
            "successful_evaluated_analyses": provider["successful_evaluated_analyses"],
            "costed_successful_evaluated_analyses": provider[
                "costed_successful_evaluated_analyses"
            ],
            "estimated_total_cost_usd": provider["estimated_total_cost_usd"],
            "estimated_cost_per_successful_evaluated_analysis_usd": provider[
                "estimated_cost_per_successful_evaluated_analysis_usd"
            ],
            "cost_unavailable_reason": provider["cost_unavailable_reason"],
        },
        "comparison": {
            "quality_results_match": quality_results_match,
            "fallbacks_observed": provider_outcomes["failure"]
            + provider_outcomes["not_configured"],
            "status": _comparison_status(
                deterministic, provider, quality_results_match
            ),
        },
    }


def _suite_summary(suite: dict[str, Any]) -> dict[str, int | bool]:
    return {
        "passed": suite["passed"],
        "cases_passed": suite["cases_passed"],
        "cases_total": suite["cases_total"],
        "checks_passed": suite["checks_passed"],
        "checks_total": suite["checks_total"],
    }


def _quality_results_match(
    deterministic: list[dict[str, Any]], provider: list[dict[str, Any]]
) -> bool:
    deterministic_scores = [
        (result["id"], result["score"], result["rubric"]) for result in deterministic
    ]
    provider_scores = [
        (result["id"], result["score"], result["rubric"]) for result in provider
    ]
    return deterministic_scores == provider_scores


def _comparison_status(
    deterministic: dict[str, Any], provider: dict[str, Any], quality_results_match: bool
) -> str:
    if not deterministic["passed"] or not quality_results_match:
        return "deterministic_quality_gate_failed"
    outcomes = provider["provider_outcomes"]
    if outcomes["not_configured"]:
        return "provider_not_configured"
    if outcomes["failure"]:
        return "provider_request_failed"
    if provider["cost_unavailable_reason"] is not None:
        return "incomplete_cost_data"
    return "ready_to_compare"
