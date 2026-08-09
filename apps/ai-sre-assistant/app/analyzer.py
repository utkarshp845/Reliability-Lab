from collections import Counter
from typing import Any


SLOW_REQUEST_MS = 1000


def _status_code(entry: dict[str, Any]) -> int | None:
    status = entry.get("status_code")
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


def _duration_ms(entry: dict[str, Any]) -> float | None:
    for key in ("duration_ms", "latency_ms"):
        value = entry.get(key)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            continue
    return None


def _is_error(entry: dict[str, Any]) -> bool:
    level = str(entry.get("level", "")).upper()
    status = _status_code(entry)
    return level in {"ERROR", "CRITICAL"} or (status is not None and status >= 500)


def _evidence(entry: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "level",
        "event",
        "message",
        "path",
        "endpoint",
        "status_code",
        "duration_ms",
        "latency_ms",
        "error_type",
        "request_id",
    ]
    return {"line": entry.get("_line_number"), **{key: entry[key] for key in keys if key in entry}}


def correlated_request_ids(logs: list[dict[str, Any]]) -> list[str]:
    """Distinct demo-service request_id values seen in the evidence used for an analysis.

    This is the cross-service correlation field: it lets a reviewer follow one
    assistant analysis back to the specific demo-service request_id values
    that produced it, the same field demo-service already logs per request.
    """
    return sorted({str(entry["request_id"]) for entry in logs if entry.get("request_id")})


def analyze_logs(logs: list[dict[str, Any]], question: str | None = None) -> dict[str, Any]:
    if not logs:
        return {
            "summary": "No recent demo-service logs were found.",
            "facts": ["The configured log file is missing or empty."],
            "guesses": ["The demo service may not have received traffic yet."],
            "evidence": [],
            "correlated_request_ids": [],
            "next_steps": [
                "Run make up and wait for both services to become healthy.",
                "Run make generate-traffic to create normal, error, and latency events.",
                "Check that DEMO_SERVICE_LOG_PATH points to the shared log file.",
            ],
            "possible_fixes": ["Generate traffic before asking for incident analysis."],
        }

    errors = [entry for entry in logs if _is_error(entry)]
    warnings = [entry for entry in logs if str(entry.get("level", "")).upper() == "WARNING"]
    slow = [entry for entry in logs if (_duration_ms(entry) or 0) >= SLOW_REQUEST_MS]
    malformed = [entry for entry in logs if entry.get("malformed")]

    status_counts = Counter(str(_status_code(entry)) for entry in logs if _status_code(entry) is not None)
    path_counts = Counter(entry.get("path") or entry.get("endpoint") or "unknown" for entry in logs)
    event_counts = Counter(str(entry.get("event", "unknown")) for entry in logs)

    facts = [
        f"Read {len(logs)} recent log events.",
        f"Found {len(errors)} error events and {len(warnings)} warning events.",
        f"Found {len(slow)} slow events at or above {SLOW_REQUEST_MS} ms.",
    ]
    if status_counts:
        facts.append(f"Observed HTTP status counts: {dict(status_counts)}.")
    if path_counts:
        facts.append(f"Most active endpoint/path: {path_counts.most_common(1)[0][0]}.")
    if malformed:
        facts.append(f"Found {len(malformed)} malformed log lines.")

    guesses = []
    possible_fixes = []

    if any(entry.get("event") == "simulated_error" for entry in errors):
        guesses.append("The recent 500s are likely intentional failures from /simulate/error.")
        possible_fixes.append("Reduce traffic to /simulate/error or lower its probability query parameter.")

    if any((entry.get("path") or entry.get("endpoint")) == "/simulate/latency" for entry in slow):
        guesses.append("Latency is likely being introduced by the intentional /simulate/latency endpoint.")
        possible_fixes.append("Check latency query parameters and compare request duration against expected sleep time.")

    if any(entry.get("event") == "simulated_memory_pressure" for entry in warnings):
        guesses.append("Memory warnings are likely from the intentional /simulate/memory-pressure endpoint.")
        possible_fixes.append("Keep memory pressure values low locally and add resource limits before Kubernetes testing.")

    if errors and not guesses:
        guesses.append("The service is returning errors, but the available logs do not show a single clear cause.")
        possible_fixes.append("Inspect error log evidence and add more structured fields around the failing path.")

    if not errors and question and "fail" in question.lower():
        guesses.append("The question mentions failure, but recent logs do not show HTTP 5xx or ERROR events.")

    if not guesses:
        guesses.append("Recent logs look mostly healthy based on the current rule set.")
        possible_fixes.append("No fix is suggested until a concrete symptom appears in logs or metrics.")

    next_steps = [
        "Review the cited log evidence before changing code or infrastructure.",
        "Compare /metrics error and latency counters with the log summary.",
        "Reproduce one symptom at a time with the simulate endpoints.",
    ]

    if errors:
        next_steps.append("Start with the most recent ERROR or HTTP 500 event and follow its endpoint/path.")
    if slow:
        next_steps.append("Check whether slow requests are isolated to /simulate/latency or affecting normal endpoints.")
    if malformed:
        next_steps.append("Fix malformed log lines before relying on automated analysis.")

    evidence = [_evidence(entry) for entry in (errors + slow + warnings)[-8:]]

    return {
        "summary": _build_summary(errors=len(errors), warnings=len(warnings), slow=len(slow), top_events=event_counts),
        "facts": facts,
        "guesses": guesses,
        "evidence": evidence,
        "correlated_request_ids": correlated_request_ids(logs),
        "next_steps": next_steps,
        "possible_fixes": possible_fixes,
    }


def _build_summary(errors: int, warnings: int, slow: int, top_events: Counter[str]) -> str:
    if errors or slow:
        return (
            f"Recent logs show {errors} error event(s), {warnings} warning event(s), "
            f"and {slow} slow event(s). Top events: {dict(top_events.most_common(4))}."
        )

    return f"Recent logs do not show obvious incidents. Top events: {dict(top_events.most_common(4))}."

