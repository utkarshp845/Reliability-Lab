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
- Day 4 - complete: add `make incident-drill`, a repeatable script that exercises one incident end to end - alert, evidence, assistant analysis (with cross-service correlation), runbook action, and recovery review - closing the exit gate below.

**Exit gate:** the project demonstrates a complete symptom-to-recovery workflow without changing the dependency-light quickstart.

## Week 8 - Provider Versus Private Endpoint Benchmark

- Run the same evaluation corpus against deterministic, managed-provider, and OpenAI-compatible private endpoints.
- Measure quality, latency, token usage, fallbacks, throughput, and cost per successful evaluated analysis.
- Test representative input sizes, concurrency, and burst behavior.
- Record an evidence-backed provider-versus-private-endpoint decision before adding GPU infrastructure.

**Exit gate:** evidence supports continuing with a provider or starting one bounded private-model experiment.

## Internal Deployment Readiness

Begin only after the Week 5-8 measurement loop works and named maintainers own the operational controls.

- Authentication, service identity, and role-based access.
- Managed secrets, rotation, artifact pinning, and supply-chain scanning.
- Ingress, TLS, environment separation, and hardened deployment automation.
- Centralized telemetry, retention policies, audit records, quotas, and budgets.
- Initial SLOs, routed alerts, rollback tests, and recovery exercises.
- Private evaluation datasets and controlled evidence access.

**Exit gate:** a sanitized internal deployment can operate with explicit ownership, access controls, measurable reliability, and a tested rollback path.

## Advanced Serving Phase - Only If Earned

- Test one approved model behind an authenticated OpenAI-compatible endpoint.
- Add an optional single-GPU vLLM example only when the Week 8 benchmark or a named deployment requirement justifies it.
- Add GPU scheduling, quotas, utilization telemetry, queue metrics, and out-of-memory recovery tests for a real workload.
- Introduce Ray Serve, Triton, or KServe only when its specific orchestration problem appears.
- Consider private VPC, dedicated, or on-premises packaging only for a documented deployment requirement.

The default project remains deterministic, provider-compatible, laptop-friendly, and GPU-free throughout these phases.

## Longer-Term Community Backlog

- Versioned evaluation history and regression alerts.
- Collaboration around private incident datasets.
- Audit-ready exports, policy controls, and usage governance.
- Privacy-aware outcome telemetry.
- Provider and model quality/cost comparisons over time.
- Log, metrics, and trace backend examples using Prometheus, Grafana, compatible open-source components, or managed services.
- Multi-environment and cloud deployment examples.
- Horizontal Pod Autoscaling for measured non-GPU workloads.
