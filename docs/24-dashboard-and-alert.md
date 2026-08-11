# Dashboard And Alert

Week 7, Day 3 adds one small, owned dashboard and one actionable, owned alert. This is [Migration Path](18-production-observability.md#migration-path) step 5. Step 3, the optional OTel Collector, shipped on [Day 2](build-log.md#week-7-day-2---optional-opentelemetry-collector-path); this step reuses the Prometheus-format `/metrics` endpoints both services have exposed since Week 1-2 directly, the same "local shared-log and direct-metrics workflow" [docs/18](18-production-observability.md) already describes - no new instrumentation, no OTLP metrics export.

## Why This Is Optional

Same rule as Day 2: `make up` never starts Prometheus or Grafana. The Week 7 exit gate requires the dependency-light quickstart to stay unchanged, so this is a second opt-in step, layered on top of (but independent from) the Day 2 collector overlay.

## Running It

```bash
make dashboard-up
```

Then open:

- Grafana: <http://localhost:3000> (anonymous viewer access, no login) - dashboard "Reliability Lab - Service Health" is provisioned automatically.
- Prometheus: <http://localhost:9090> - check **Status → Targets** (both services should show `up`) and **Alerts** (the one rule below).

```bash
make dashboard-logs   # Prometheus + Grafana container logs
make dashboard-down
```

Or directly, without `make`:

```bash
docker compose -f docker-compose.yml -f infra/docker/docker-compose.dashboard.yml up --build -d
docker compose -f docker-compose.yml -f infra/docker/docker-compose.dashboard.yml down
```

## The Dashboard

One dashboard, scoped to `demo-service`, matching the "Service health" row of the [Dashboard Set](18-production-observability.md#dashboard-set) table (owner: service or platform team):

| Panel | Answers |
| --- | --- |
| Request Rate by Status Code | Is traffic normal, and what fraction is failing? |
| 5xx Error Ratio | The exact ratio the alert below fires on, so the number that pages someone is always one glance away. |
| p95 Request Latency | Are requests slow, not just failing? |
| Simulated Events by Endpoint | Which intentional simulation endpoint is responsible for what's showing up in the panels above? |

The JSON lives at `infra/docker/grafana/provisioning/dashboards/json/service-health.json` and is provisioned automatically - there is nothing to click through to import it.

The other three dashboards in [docs/18](18-production-observability.md#dashboard-set)'s table (assistant operations, quality and safety, cost and capacity) are future work; a small, single owned dashboard is the Day 3 scope, not the full set.

## The Alert

One rule, in `infra/docker/prometheus-alerts.yml`:

```yaml
- alert: DemoServiceHighErrorRate
  expr: >-
    (
      sum(rate(demo_service_http_requests_total{status_code=~"5.."}[5m]))
      /
      sum(rate(demo_service_http_requests_total[5m]))
    ) > 0.25
  for: 1m
  labels:
    severity: page
    owner: demo-service-oncall
  annotations:
    summary: demo-service is returning elevated 5xx responses
    runbook: docs/incidents/01-error-spike.md
```

This is the "Service availability" SLO indicator from [docs/18](18-production-observability.md#slo-and-alert-design): successful requests divided by all requests, inverted to an error ratio. It has everything [docs/18](18-production-observability.md#slo-and-alert-design) asks an alert to have:

- **Owner:** `demo-service-oncall` (the `owner` label).
- **Runbook:** [`docs/incidents/01-error-spike.md`](incidents/01-error-spike.md), the existing error-spike walkthrough - this alert did not need a new runbook written for it, because that walkthrough already covers this exact symptom end to end.
- **A decision an operator can make:** the runbook's own next steps (confirm the failing path, check whether traffic was intentional, compare against normal API paths) are actions, not just "look at a graph."

### Trigger It Locally

```bash
for i in $(seq 1 90); do curl -s "http://localhost:8000/simulate/error?probability=1.0" > /dev/null; sleep 1; done
```

Watch it move through Prometheus's alert states (`inactive` → `pending` → `firing`) at <http://localhost:9090/alerts>, or poll the API:

```bash
curl -s http://localhost:9090/api/v1/rules | python3 -m json.tool
```

Stop the loop and the ratio recovers within the same 5-minute `rate()` window; the alert clears back to `inactive` without any manual reset.

### Why A Single Ratio Threshold, Not Burn Rate

Production SRE practice usually alerts on multi-window error-budget burn rate (e.g. a fast 5m/1h pair and a slow 6h/3d pair) to balance detection speed against noise. This alert is a single ratio over a single window on purpose - it is the smallest rule that is still genuinely actionable, and the right next step once this feels routine is to replace it with a burn-rate pair, not to add more single-window rules beside it.

### Why No Alertmanager

Prometheus evaluates and exposes the alert's state (`/alerts`, `ALERTS` metric, and Grafana can read it from the same datasource); there is no Alertmanager, and therefore no email, Slack, or paging integration, wired up yet. That is a deliberate scope cut, not an oversight: routing and notification channels are credentials and environment-specific in a way a shared learning repo shouldn't hardcode. The alert is fully real and fully queryable - only the "and then notify a human" step is left for a real deployment to wire up.

## What This Does Not Do Yet

- No Alertmanager routing (see above).
- No dashboards beyond "Service health" (see above).
- No metrics/traces through the Day 2 collector - Prometheus scrapes `/metrics` directly, unchanged from Week 1-2.

Next: exercise one incident end to end - alert, evidence, assistant analysis, runbook action, and recovery review - closing Week 7's exit gate.
