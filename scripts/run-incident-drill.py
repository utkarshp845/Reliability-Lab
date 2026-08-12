#!/usr/bin/env python
"""Exercise one incident end to end: alert, evidence, analysis, runbook, recovery.

This is the Week 7 exit-gate exercise (see docs/25-incident-drill.md): it
does not add a new signal, it proves the ones already built work together as
one symptom-to-recovery workflow.

- demo-service and ai-sre-assistant are required (`make up`).
- Prometheus is optional (`make dashboard-up`). Without it, the alert-state
  steps are skipped with a note instead of failing - the evidence, assistant
  analysis, and runbook steps never depended on the dashboard overlay.

No third-party dependencies, matching scripts/generate-demo-traffic.py.
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4


RUNBOOK_PATH = Path(__file__).resolve().parent.parent / "docs" / "incidents" / "01-error-spike.md"


def _request(method: str, url: str, headers: dict | None = None, body: bytes | None = None, timeout: float = 10) -> tuple[int, dict]:
    request = urllib.request.Request(url, method=method, data=body, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, _parse_json(raw)
    except urllib.error.HTTPError as exc:
        return exc.code, _parse_json(exc.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return 0, {"error": str(exc)}


def _parse_json(raw: str) -> dict:
    # Not every endpoint here returns JSON - Prometheus's own health/ready
    # checks are plain text ("Prometheus Server is Healthy."), for example.
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def _header(title: str) -> None:
    print(f"\n=== {title} ===")


def check_reachable(name: str, url: str) -> bool:
    status, _ = _request("GET", url, timeout=5)
    ok = status == 200
    print(f"{'OK ' if ok else 'FAIL'} {name}: {url} -> {status}")
    return ok


def alert_state(prometheus_url: str) -> str | None:
    status, body = _request("GET", f"{prometheus_url}/api/v1/rules", timeout=5)
    if status != 200:
        return None
    try:
        for group in body["data"]["groups"]:
            for rule in group["rules"]:
                if rule.get("name") == "DemoServiceHighErrorRate":
                    return rule["state"]
    except (KeyError, IndexError):
        return None
    return None


def trigger_symptom_and_watch_alert(demo_url: str, prometheus_url: str | None, duration_seconds: int) -> None:
    _header("Step 1: Trigger Symptom")
    print(f"Calling {demo_url}/simulate/error?probability=1.0 for {duration_seconds}s ...")
    if prometheus_url is None:
        print("Prometheus not reachable - traffic will run, but alert transitions won't be shown. Run `make dashboard-up` to see this step.")

    sent = 0
    seen_state = None
    deadline = time.time() + duration_seconds
    while time.time() < deadline:
        _request("GET", f"{demo_url}/simulate/error?probability=1.0", timeout=5)
        sent += 1
        if prometheus_url is not None:
            state = alert_state(prometheus_url)
            if state != seen_state:
                print(f"  [{sent}s in] alert state: {state}")
                seen_state = state
        time.sleep(1)

    print(f"Sent {sent} intentional-failure requests.")
    return seen_state


def wait_for_alert_state(prometheus_url: str | None, target_state: str, max_wait_seconds: int, already_seen: str | None = None) -> bool:
    if prometheus_url is None:
        return False
    if already_seen == target_state:
        return True

    seen = already_seen
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        state = alert_state(prometheus_url)
        if state != seen:
            print(f"  alert state: {state}")
            seen = state
        if state == target_state:
            return True
        time.sleep(3)
    print(f"  gave up waiting for '{target_state}' after {max_wait_seconds}s (last seen: {seen})")
    return False


def pull_evidence_and_analysis(assistant_url: str, max_lines: int) -> dict:
    _header("Step 2: Evidence And Assistant Analysis")
    analysis_request_id = f"incident-drill-{uuid4()}"
    body = json.dumps({"max_lines": max_lines, "include_metrics": True, "use_llm": False}).encode("utf-8")
    status, response = _request(
        "POST",
        f"{assistant_url}/summarize-incident",
        headers={"Content-Type": "application/json", "X-Request-ID": analysis_request_id},
        body=body,
        timeout=15,
    )
    if status != 200:
        print(f"FAIL summarize-incident: HTTP {status} {response}")
        return {}

    log_analysis = response.get("log_analysis", {})
    print(f"assistant request_id (this analysis call): {analysis_request_id}")
    print(f"correlated_request_ids (demo-service requests this analysis is grounded in): {response.get('correlated_request_ids')}")
    print(f"logs_read: {response.get('logs_read')}")
    print(f"summary: {log_analysis.get('summary')}")
    print("facts:")
    for fact in log_analysis.get("facts", []):
        print(f"  - {fact}")
    print("evidence (most recent):")
    for item in log_analysis.get("evidence", [])[-3:]:
        print(f"  - {item}")
    combined = response.get("combined_analysis", {})
    if combined.get("summary"):
        print(f"combined_analysis summary: {combined['summary']}")
    return response


def runbook_action() -> None:
    _header("Step 3: Runbook Action")
    if not RUNBOOK_PATH.exists():
        print(f"Runbook not found at {RUNBOOK_PATH}")
        return
    text = RUNBOOK_PATH.read_text(encoding="utf-8")
    repo_root = RUNBOOK_PATH.parent.parent.parent
    print(f"Runbook: {RUNBOOK_PATH.relative_to(repo_root)}")
    for section in ("Likely Cause", "Safe Debugging Steps"):
        match = re.search(rf"## {re.escape(section)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        if match:
            print(f"\n{section}:")
            print(match.group(1).strip())


def recovery_review(prometheus_url: str | None, demo_url: str, max_wait_seconds: int) -> None:
    _header("Step 4: Recovery Review")
    if prometheus_url is None:
        health_ok = check_reachable("demo-service /health", f"{demo_url}/health")
        print(
            "Recovery signal without Prometheus: service is reachable and no longer receiving forced failures."
            if health_ok
            else "demo-service did not respond."
        )
        return

    started = time.time()
    recovered = wait_for_alert_state(prometheus_url, target_state="inactive", max_wait_seconds=max_wait_seconds)
    elapsed = round(time.time() - started, 1)

    if recovered:
        print(f"Alert cleared back to inactive after {elapsed}s (the alert's 5m rate() window drains gradually, not instantly).")
    else:
        print(f"Alert had not cleared after {elapsed}s. This can take up to ~5 minutes after traffic stops; check {prometheus_url}/alerts.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise one incident end to end: alert, evidence, analysis, runbook, recovery.")
    parser.add_argument("--demo-url", default="http://localhost:8000")
    parser.add_argument("--assistant-url", default="http://localhost:8001")
    parser.add_argument("--prometheus-url", default="http://localhost:9090")
    parser.add_argument("--duration", type=int, default=90, help="Seconds of sustained intentional failures.")
    parser.add_argument("--max-lines", type=int, default=200)
    parser.add_argument("--recovery-wait", type=int, default=300)
    args = parser.parse_args()

    _header("Step 0: Baseline")
    demo_ok = check_reachable("demo-service", f"{args.demo_url}/health")
    assistant_ok = check_reachable("ai-sre-assistant", f"{args.assistant_url}/health")
    prometheus_url = args.prometheus_url if check_reachable("prometheus", f"{args.prometheus_url}/-/healthy") else None

    if not (demo_ok and assistant_ok):
        print("\ndemo-service and ai-sre-assistant are required. Run `make up` first.")
        return 1

    if prometheus_url:
        print(f"alert state before the drill: {alert_state(prometheus_url)}")

    seen_state = trigger_symptom_and_watch_alert(args.demo_url, prometheus_url, args.duration)
    wait_for_alert_state(prometheus_url, target_state="firing", max_wait_seconds=120, already_seen=seen_state)

    pull_evidence_and_analysis(args.assistant_url, args.max_lines)
    runbook_action()
    recovery_review(prometheus_url, args.demo_url, args.recovery_wait)

    _header("Drill Complete")
    print("Symptom -> alert -> evidence -> assistant analysis -> runbook action -> recovery review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
