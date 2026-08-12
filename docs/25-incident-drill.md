# Incident Drill: Alert To Recovery

Week 7, Day 4 closes the Week 7 exit gate: "the project demonstrates a complete symptom-to-recovery workflow without changing the dependency-light quickstart." This is [Migration Path](18-production-observability.md#migration-path) step 6.

Days 1-3 built the pieces - cross-service correlation, an optional collector, a dashboard and an alert. Day 4 does not add a new signal. It proves the pieces work together as one workflow, and gives you a repeatable way to run that proof yourself.

## Running It

```bash
make up              # demo-service + ai-sre-assistant (required)
make dashboard-up    # Prometheus + Grafana (optional - richer output with it)
make incident-drill
```

Or directly: `python scripts/run-incident-drill.py`.

`scripts/run-incident-drill.py` needs demo-service and ai-sre-assistant; it degrades gracefully without Prometheus (the alert-transition steps print a note and are skipped instead of failing), the same "richer when more of the optional infra is present, still useful without it" shape the assistant's own LLM fallback already has.

## What It Does

1. **Baseline** - confirms demo-service, ai-sre-assistant, and (if present) Prometheus are reachable, and prints the alert's state before anything happens.
2. **Trigger Symptom** - calls `/simulate/error?probability=1.0` on a loop, polling and printing the alert's state on every transition.
3. **Evidence And Assistant Analysis** - calls `ai-sre-assistant`'s `/summarize-incident` with its own `X-Request-ID`, then prints that request ID alongside the `correlated_request_ids` it returns - the exact cross-service link [Day 1](build-log.md#week-7-day-1---structured-assistant-logs-and-cross-service-correlation) built - plus the summary, facts, and cited evidence.
4. **Runbook Action** - reads the *Likely Cause* and *Safe Debugging Steps* sections straight out of [`docs/incidents/01-error-spike.md`](incidents/01-error-spike.md), the same runbook the [Day 3](build-log.md#week-7-day-3---dashboard-and-alert) alert annotation points to, so there is one source of truth for "what do I do," not two.
5. **Recovery Review** - stops generating traffic and watches the alert clear back to `inactive`, or reports how long it had not yet cleared if you interrupt it early.

## Sample Run

Captured from a real `make dashboard-up` + `make incident-drill` run on 2026-08-12. The alert was already `firing` when this run started - a prior drill run had just finished, and a `for: 1m` debounce measures wall-clock state, not "time since this script started" (see Lessons Learned below). `correlated_request_ids` and the evidence entries are trimmed for length; nothing else is edited.

```text
=== Step 0: Baseline ===
OK  demo-service: http://localhost:8000/health -> 200
OK  ai-sre-assistant: http://localhost:8001/health -> 200
OK  prometheus: http://localhost:9090/-/healthy -> 200
alert state before the drill: firing

=== Step 1: Trigger Symptom ===
Calling http://localhost:8000/simulate/error?probability=1.0 for 90s ...
  [1s in] alert state: firing
Sent 90 intentional-failure requests.

=== Step 2: Evidence And Assistant Analysis ===
assistant request_id (this analysis call): incident-drill-d8119caf-fc62-46e7-a744-cffe16be0317
correlated_request_ids (demo-service requests this analysis is grounded in): [113 IDs - truncated for this doc]
logs_read: 200
summary: Recent logs show 175 error event(s), 0 warning event(s), and 0 slow event(s). Top events: {'request_completed': 113, 'simulated_error': 87}.
facts:
  - Read 200 recent log events.
  - Found 175 error events and 0 warning events.
  - Found 0 slow events at or above 1000 ms.
  - Observed HTTP status counts: {'500': 88, '200': 25}.
  - Most active endpoint/path: /simulate/error.
evidence (most recent):
  - {'line': 860, 'event': 'request_completed', 'path': '/simulate/error', 'status_code': 500, 'duration_ms': 1.58, 'request_id': 'e490cbbb-6077-4972-891b-bf96e1fd5eef'}
  - {'line': 861, 'event': 'simulated_error', 'endpoint': '/simulate/error', 'error_type': 'checkout_dependency_timeout', 'request_id': 'a8e171d6-0062-4fff-a222-ca3c6cd151b7'}
  - {'line': 862, 'event': 'request_completed', 'path': '/simulate/error', 'status_code': 500, 'duration_ms': 1.7, 'request_id': 'a8e171d6-0062-4fff-a222-ca3c6cd151b7'}
combined_analysis summary: Combined incident analysis includes both recent logs and demo-service metrics.

=== Step 3: Runbook Action ===
Runbook: docs/incidents/01-error-spike.md

Likely Cause:
This is an intentional simulated dependency timeout from `/simulate/error`.

The most likely cause is test traffic hitting the simulation endpoint, not a real production dependency outage.

Safe Debugging Steps:
- Confirm the failing path is `/simulate/error`.
- Check whether recent traffic intentionally called the simulation endpoint.
- Compare the 500 count against normal API paths like `/api/orders`.
- Use the request ID to inspect related log lines.
- Avoid changing infrastructure until the evidence points outside the app.

=== Step 4: Recovery Review ===
  alert state: firing
  alert state: inactive
Alert cleared back to inactive after 273.7s (the alert's 5m rate() window drains gradually, not instantly).

=== Drill Complete ===
Symptom -> alert -> evidence -> assistant analysis -> runbook action -> recovery review.
```

## What This Confirms

- **Alert:** `DemoServiceHighErrorRate` reached `firing` from real traffic, not a hand-crafted test fixture.
- **Evidence:** `ai-sre-assistant` read the same `demo-service` log file the drill's requests wrote to, with no manual log-shipping step - 113 distinct `demo-service` request IDs, all pulled from that shared file.
- **Cross-service correlation:** the assistant's own `request_id` for the analysis call and the `correlated_request_ids` it found in evidence are two different, independently generated IDs from two different services - printed side by side, not asserted.
- **Runbook:** the exact next steps an operator would follow come from a file written back in Week 1, unmodified for this exercise.
- **Recovery:** the alert's `rate()`-based ratio drained back to `inactive` in 273.7s after traffic stopped, without any manual reset.

## Week 7 Retrospective

The exit gate asked for a complete symptom-to-recovery workflow that does not change the dependency-light quickstart. Every optional piece - the collector, the dashboard, the alert - is additive: `docker-compose.yml` has a zero-line diff across all of Week 7, and `make up` still works exactly as it did after Week 1.

What made this drill possible was mostly *not* written this week: `request_id` correlation, the JSON log shape, the deterministic rule-based analyzer, and the Week 1 error-spike runbook all predate Week 7. Week 7's job was to connect them - a shared log shape and correlation field (Day 1), a way to watch the signal path from outside the app (Day 2), a threshold that turns the signal into a decision (Day 3), and a repeatable proof that the whole chain holds together (Day 4).

Next: Week 8 - benchmark deterministic, managed-provider, and OpenAI-compatible private endpoints against the same evaluation corpus, and record an evidence-backed build-versus-buy decision before adding GPU infrastructure.
