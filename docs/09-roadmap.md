# Roadmap

This is the canonical technical execution order for Reliability Lab. Each week adds one measurable capability while keeping the default path laptop-friendly and dependency-light.

## Week 1 - Local Learning Lab

- Local demo-service.
- AI SRE Assistant.
- Docker Compose.
- Sample logs.
- Basic README.

## Week 2 - Observability Basics

- Metrics improvements.
- Structured logging refinements.
- Request correlation.
- Incident examples.
- Assistant metrics analysis.

## Week 3 - Kubernetes Foundations

- kind-first Kubernetes manifests.
- Operations runbook.
- ConfigMaps and Secrets.
- Health checks and resource limits.
- Incident debugging walkthrough.
- Production next-steps guide.

## Week 4 - Production Readiness

- Security hardening basics.
- Secret handling and redaction rules.
- Cost optimization habits.
- Assistant evaluation basics.
- Production observability upgrade path.
- Optional advanced serving roadmap: vLLM, Triton, Ray, KServe, and GPU scheduling.
- Production-readiness review with local and CI release gates.

## Week 5 - Provider Telemetry

- Day 1 - complete: expose a bounded per-call contract for provider/model identity, request latency, token usage, outcome, and deterministic fallback without storing sensitive content.
- Day 2 - complete: add aggregate counters and latency distributions with bounded labels.
- Day 3 - complete: accept explicit deployment-owned pricing inputs and return per-call estimated cost metadata only when prices and token directions are known.
- Day 4 - complete: join provider outcomes and deployment-owned cost estimates with deterministic evaluation results, including cost per successful evaluated analysis when data is complete.
- Day 5 - complete: add a bounded local comparison report across deterministic and configured provider paths, including the end-to-end fallback state.

See [Provider Telemetry Contract](22-provider-telemetry.md) for the per-request contract, aggregate metrics, privacy boundary, and remaining-week sequence.

**Exit gate:** provider usage, reliability, and cost can be compared with evaluation outcomes without storing prompts, incident evidence, credentials, endpoints, or generated content.

## Week 6 - Evaluation Maturity

- Day 1 - complete: version the deterministic corpus/rubric/threshold contract and emit a privacy-safe machine-readable report in CI.
- Day 2 - complete: expand the sanitized deterministic corpus with generic server failures, mixed signals, and client-only errors.
- Day 3 - complete: add adversarial prompt-injection and unsupported-root-cause cases that enforce safe, evidence-grounded behavior.
- Day 4 - complete: expand the corpus with redacted JWT, AWS-style key, GitHub-style token, and inline-credential edge cases.
- Day 5 - complete: add a bounded regression diff between two versioned reports so a case or hard-gate regression is easy to spot in a pull request.

**Exit gate:** a model, prompt, provider, or code change produces a repeatable regression report and cannot bypass required privacy or safety checks.

## Week 7 - Production Signal Path

- Day 1 - complete: give `ai-sre-assistant` structured JSON stdout logs in the same shape as `demo-service`, plus a shared `request_id` field and a `correlated_request_ids` list that ties an assistant analysis back to the demo-service requests it read.
- Day 2 - complete: add an opt-in OpenTelemetry Collector overlay (`make otel-up`) that both services export OTLP/HTTP logs to when `OTEL_EXPORTER_OTLP_ENDPOINT` is set, without changing the default `make up` quickstart.
- Day 3 - complete: add an opt-in Prometheus + Grafana overlay (`make dashboard-up`) with one owned "Service health" dashboard and one owned, runbook-linked alert (`DemoServiceHighErrorRate`), without changing the default `make up` quickstart.
- Exercise one incident from alert through evidence, assistant analysis, runbook action, and recovery review.

**Exit gate:** the project demonstrates a complete symptom-to-recovery workflow without changing the dependency-light quickstart.

## Week 8 - Provider Versus Private Endpoint Benchmark

- Run the same evaluation corpus against deterministic, managed-provider, and OpenAI-compatible private endpoints.
- Measure quality, latency, token usage, fallbacks, throughput, and cost per successful evaluated analysis.
- Test representative input sizes, concurrency, and burst behavior.
- Record an evidence-backed provider-versus-private-endpoint decision before adding GPU infrastructure.
- If, and only if, that evidence justifies it: test one approved model behind an authenticated OpenAI-compatible endpoint, add one single-GPU vLLM example, and add GPU scheduling, quotas, utilization telemetry, and out-of-memory recovery tests. Otherwise, a documented "not yet justified" is a complete, valid outcome. Ray Serve, Triton, or KServe are introduced later only if a specific orchestration problem appears - none of them are a default part of this project.

**Exit gate:** evidence supports continuing with a provider, or one bounded private-model experiment exists with the same evidence rigor as everything else. The default project stays deterministic, provider-compatible, laptop-friendly, and GPU-free either way.

## Week 9 - Production Deployment Readiness

Everything needed to run this specific deployment reliably and securely, beyond a single laptop. Begin once named maintainers own the operational controls this introduces.

- Authentication, service identity, and role-based access for both services.
- Managed secrets, rotation, artifact pinning, and supply-chain scanning (SBOM plus dependency/image scanning) in CI.
- Ingress, TLS, and environment separation (dev/staging/prod-shaped, still kind-first).
- Alertmanager routing for the alert Week 7 shipped without a notification path, plus the three "Assistant operations," "Quality and safety," and "Cost and capacity" dashboard rows Week 7 left as future work (see [Dashboard Set](18-production-observability.md#dashboard-set)).
- Centralized, privacy-aware telemetry retention, audit records, quotas, and budgets.
- One rollback test and one recovery drill, in the same exercised-not-just-documented spirit as Week 7 Day 4's incident drill.
- One multi-environment or cloud deployment example, and Horizontal Pod Autoscaling for measured non-GPU workloads, driven by metrics this project already exposes.

**Exit gate:** an alert reaches a human outside the terminal, a bad deploy has a tested and timed rollback, and the stack runs (documented, reproducible) beyond a single laptop.

## Week 10 - Make It Yours: Adapter Contract And Governance

Turns this from a lab about `demo-service` into a lab you can point at your own application.

- Write down the Adapter Contract: the minimal JSON log shape, metric naming convention, and `/health`/`/ready` shape any service needs to be `ai-sre-assistant`-compatible, formalizing what today is implicit in `demo-service`'s `logging_config.py` and `metrics.py`.
- Add a second example service that satisfies the contract without copying `demo-service`, proving the contract is a real interface and not an accident of one codebase.
- Point `ai-sre-assistant` at both services and run one incident-drill-style walkthrough against the new one.
- Publish a "Bring Your Own Service" guide with the concrete adaptation steps.
- Private evaluation datasets, controlled evidence access, audit-ready exports, policy controls, and usage governance.
- Versioned evaluation history with regression alerts over time, including provider and model quality/cost comparisons over time - extending Week 6's two-report diff into a running history.

**Exit gate:** a service nobody on this project wrote can be plugged in and analyzed using only the written contract, and an evaluation result stays auditable after the fact without re-running anything.

## Open Backlog

Not tied to a week - process and community items, not solo-buildable features.

- Collaboration around private incident datasets.
