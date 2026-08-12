# Reliability Lab

Simple first. Production-minded always.

Reliability Lab is a practical learning lab for AI infrastructure. It starts with a normal web service, adds logs and metrics, then uses an AI SRE Assistant to explain what is happening operationally.

The first version runs on a normal laptop. No GPU, Kubernetes, vLLM, Triton, Ray, KServe, or full MLOps platform is required on Day 1.

## Who This Is For

This project is for developers, DevOps engineers, platform engineers, and cloud engineers who understand production systems but are new to AI infrastructure.

AI infra feels intimidating because the ecosystem often starts in the deep end: model servers, GPU scheduling, distributed inference, autoscaling, observability, evals, safety, and cost controls all appear at once. This starter kit introduces those ideas in order:

local app -> AI service -> logs/metrics -> AI SRE assistant -> observability -> containers -> Kubernetes -> production considerations.

## What You Build

- `demo-service`: a FastAPI service that behaves like a small production API.
- `ai-sre-assistant`: a FastAPI service and CLI that reads demo logs and metrics, then explains incidents.
- Docker Compose wiring so both services share the same log file locally.
- Tests, sample logs, docs, and a 30-day roadmap for building in public.
- Incident walkthroughs that show how to reason from symptoms, metrics, logs, and safe next steps.
- A runnable assistant evaluation corpus with grounded, useful, safe, private, and honest checks.

## Architecture

```mermaid
flowchart LR
    user["User"] --> demo["demo-service"]
    demo --> signals["logs / metrics"]
    signals --> assistant["ai-sre-assistant"]
    assistant --> provider["LLM provider<br/>OpenAI-compatible or Ollama"]
    provider --> assistant
    assistant --> output["operational summary<br/>root-cause guesses<br/>safe next steps"]
    output --> user
```

The AI assistant does not need an LLM key to work. If no provider is configured, it falls back to a deterministic rule-based analyzer so the project is useful for everyone.

## Quickstart

```bash
git clone https://github.com/utkarshp845/Reliability-Lab.git
cd Reliability-Lab
cp .env.example .env
make up
make test
make generate-traffic
make analyze-logs
make down
```

If `make` is not installed, run the same workflow directly:

```bash
docker compose up --build -d
docker compose build demo-service ai-sre-assistant
docker compose run --rm --no-deps demo-service pytest -q
docker compose run --rm --no-deps ai-sre-assistant pytest -q
python scripts/generate-demo-traffic.py --base-url http://localhost:8000
docker compose run --rm --no-deps ai-sre-assistant python cli/sre.py analyze --max-lines 120
docker compose down
```

Useful local URLs:

- Demo service: `http://localhost:8000`
- Demo health: `http://localhost:8000/health`
- Demo metrics: `http://localhost:8000/metrics`
- AI SRE Assistant: `http://localhost:8001`
- AI SRE health: `http://localhost:8001/health`
- AI SRE provider metrics: `http://localhost:8001/metrics`

For the kind-based Kubernetes walkthrough, see `infra/k8s/README.md`.

For a practical Kubernetes operations checklist, see `docs/10-kubernetes-operations-runbook.md`.

For Kubernetes config and secrets basics, see `docs/11-kubernetes-config-and-secrets.md`.

For Kubernetes probes and resource basics, see `docs/12-kubernetes-health-and-resources.md`.

For a Kubernetes incident debugging walkthrough, see `docs/13-kubernetes-incident-debugging.md`.

For Kubernetes production next steps, see `docs/14-kubernetes-production-next-steps.md`.

For security hardening basics, see `docs/07-security.md` and `SECURITY.md`.

For secret handling and enforced assistant redaction rules, see `docs/15-secret-handling-and-redaction.md`.

For practical cost optimization controls, see `docs/16-cost-optimization.md`.

For the assistant evaluation corpus and quality rubric, see `docs/17-assistant-evaluation.md`.

For the production observability architecture and staged migration path, see `docs/18-production-observability.md`.

For the advanced model serving decision framework, see `docs/19-advanced-model-serving-roadmap.md`.

For the Week 4 release gates, readiness verdict, and next-stage priorities, see `docs/20-production-readiness-review.md`.


For the Week 5 provider telemetry contract, aggregate metrics, and privacy boundary, see `docs/22-provider-telemetry.md`.

For the optional OpenTelemetry Collector path (`make otel-up`), see `docs/23-otel-collector-path.md`.

For the optional dashboard and alert (`make dashboard-up`), see `docs/24-dashboard-and-alert.md`.

For the end-to-end incident drill (`make incident-drill`) that closes the Week 7 exit gate, see `docs/25-incident-drill.md`.

Ask the assistant directly:

```bash
curl -s -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why is the demo service failing?","max_lines":120}'
```

Ask for metrics analysis:

```bash
curl -s -X POST http://localhost:8001/analyze/metrics \
  -H "Content-Type: application/json" \
  -d '{}'
```

Summarize an incident with logs and metrics:

```bash
curl -s -X POST http://localhost:8001/summarize-incident \
  -H "Content-Type: application/json" \
  -d '{"max_lines":120}'
```

## Repository Structure

```text
Reliability-Lab/
  apps/
    demo-service/        # FastAPI app that emits health, failure, latency, logs, and metrics
    ai-sre-assistant/    # FastAPI app and CLI that analyze demo-service logs
  docs/                  # Learning path and production notes
    incidents/           # Guided operational debugging examples
    10-kubernetes-operations-runbook.md
    11-kubernetes-config-and-secrets.md
    12-kubernetes-health-and-resources.md
    13-kubernetes-incident-debugging.md
    14-kubernetes-production-next-steps.md
    15-secret-handling-and-redaction.md
    16-cost-optimization.md
    17-assistant-evaluation.md
    18-production-observability.md
    19-advanced-model-serving-roadmap.md
    20-production-readiness-review.md
    22-provider-telemetry.md
    23-otel-collector-path.md
    24-dashboard-and-alert.md
    25-incident-drill.md
  infra/                 # Docker, Kubernetes, and Terraform starter notes
    docker/               # Optional OpenTelemetry Collector, Prometheus, and Grafana overlays
    k8s/                 # kind-first Kubernetes manifests and walkthrough
  scripts/               # Local traffic and log helper scripts
  examples/              # Sample logs and questions
```

## How The Apps Work Together

1. You run both apps with Docker Compose.
2. `demo-service` writes JSON logs to `/shared/logs/demo-service.log`.
3. The host maps that file to `./logs/demo-service.log`.
4. `ai-sre-assistant` reads the same file and fetches `demo-service` metrics.
5. The assistant separates facts from guesses, cites evidence, and recommends safe next debugging steps.

## Example Workflow

```bash
make up
make generate-traffic
make analyze-logs
```

You should see the assistant report intentionally generated 500s, latency spikes, warning-level events, and which endpoints were involved.

## Roadmap

- Week 1: local demo-service, AI SRE Assistant, Docker Compose, sample logs, basic README.
- Week 2: observability basics, metrics, dashboards, structured logging, incident examples.
- Week 3: Kubernetes manifests, operations, config/secrets, probes/resources, incident debugging, production next steps.
- Week 4: security hardening, cost optimization, evaluation, production observability, advanced serving decisions, and a release-gated production-readiness review.
- Week 5: privacy-safe provider identity, latency, usage, outcome, fallback, and deployment-owned cost estimates.
- Week 6: a larger versioned evaluation corpus with machine-readable CI regression reports.
- Week 7: an optional OpenTelemetry signal path plus one owned alert-to-runbook exercise.
- Week 8: a provider-versus-private-endpoint benchmark and an evidence-backed build-versus-buy decision.

The technical weeks add measurable capabilities while preserving the small, local-first learning path. See `docs/09-roadmap.md`.

## Build In Public

This repo is designed to be built in public one small step at a time. Good updates to share:

- What broke today.
- What concept became clearer.
- What was intentionally left out.
- How a local-only version maps to production thinking.
- Where AI infra gets complicated and why.

Start with `docs/build-log.md`.

## Lessons Learned

Day 1 lessons are intentionally simple:

- AI infrastructure is still infrastructure.
- Logs, health checks, and clear failure modes matter before GPUs.
- An AI assistant is more useful when it is grounded in evidence.
- A deterministic fallback keeps the project accessible.
- Simple first does not mean toy forever.

## Contributing

Contributions should keep the learning path gradual. Before adding a new tool, explain the problem it solves and where it fits in the local app -> production-minded path. See `CONTRIBUTING.md` for details.

## Security

Do not commit real secrets, API keys, private logs, or local Kubernetes Secret files. See `SECURITY.md` for reporting guidance and `docs/07-security.md` for the project security model.
