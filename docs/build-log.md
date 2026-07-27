# Build Log

## Day 1 - Simple First, Production-Minded Always

I am building Reliability Lab because AI infrastructure is becoming part of normal software infrastructure, but the learning path often starts too late in the stack.

AI infra is intimidating because beginners are quickly surrounded by model serving frameworks, GPU scheduling, Kubernetes operators, distributed systems, observability, evals, and cost tradeoffs. Those topics matter, but they do not need to arrive all at once.

Simplicity is the edge for this project. The first version uses a small FastAPI service, structured logs, a metrics endpoint, Docker Compose, and an AI SRE Assistant that reads evidence. That is enough to teach the shape of the workflow without hiding the production direction.

Day 1 includes:

- `demo-service` with health, readiness, normal API, simulated errors, latency, memory pressure, logs, and metrics.
- `ai-sre-assistant` with API endpoints, CLI, rule-based analysis, and optional OpenAI-compatible LLM support.
- Docker Compose for local operation.
- Sample logs and questions.
- Docs for architecture, setup, observability, security, cost, and roadmap.

Next comes better observability: richer metrics, incident examples, dashboard basics, and clearer structured logging patterns.

## Week 2, Day 1 - Metrics Cleanup

Today I started Week 2: observability basics.

Week 1 answered the first question: can someone clone the repo, run the local AI infrastructure lab, generate signals, and ask the AI SRE Assistant what happened?

Week 2 starts with a different question: can someone understand what the service is doing from its operational signals?

The first cleanup was the `/metrics` endpoint in `demo-service`.

What changed:

- Moved metrics logic into a dedicated `app/metrics.py` module.
- Added request counters by method, route template, and status code.
- Added histogram-style latency buckets with `_bucket`, `_sum`, and `_count` output.
- Added counters for simulated errors, latency events, and memory pressure events.
- Normalized dynamic paths like `/api/orders/ord-1001` to `/api/orders/{order_id}`.
- Added tests for metrics output, simulation counters, and route label normalization.
- Updated the observability docs with counters, latency buckets, and label cardinality.

Why this matters:

Metrics are not just numbers. The names and labels decide whether the service stays understandable as traffic grows.

A raw path like `/api/orders/ord-1001` looks harmless in a tiny app, but in a real system it can create a new time series for every order ID. That is a high-cardinality label problem. The production-minded version is to expose the route shape, such as `/api/orders/{order_id}`, so the metric explains the endpoint without exploding the number of series.

Lessons learned:

- Logs tell a story about specific events. Metrics show shape, volume, and trend.
- Averages are not enough for latency. Buckets make slow requests easier to spot.
- Good observability starts before dashboards. It starts with stable signal design.
- Keeping this dependency-free for now keeps the Day 1 and Week 2 path beginner-friendly.
- The AI SRE Assistant will be more useful once it can combine log evidence with these cleaner metrics.

What comes next:

- Add incident walkthroughs for error spikes and latency spikes.
- Teach the AI SRE Assistant to read and summarize metrics.
- Add an optional Prometheus/Grafana path without making it required for the local quickstart.

## Week 2, Day 2 - Structured Logs And Request Correlation

Today I continued observability week by improving structured logs.

Day 1 focused on metrics: counters, latency buckets, simulation counters, and label cardinality.

Day 2 focused on logs: how to follow one request through multiple events.

What changed:

- Added request-scoped context for `request_id`.
- Preserved incoming `X-Request-ID` headers when callers provide them.
- Generated a request ID when callers do not provide one.
- Returned the request ID in the `x-request-id` response header.
- Added the same request ID to route-level logs and `request_completed` logs.
- Added a sample correlated request log.
- Expanded observability docs with structured log fields and request correlation.
- Added tests for request ID response headers and correlated route logs.

Why this matters:

Metrics can show that errors increased or latency crossed a threshold. Logs help explain what happened in a specific request.

Without request IDs, logs are just scattered events. With request IDs, a failure becomes a story that can be followed from the route-level error to the final response log.

Lessons learned:

- Request IDs are one of the simplest useful observability patterns.
- Good logs use stable field names, not just readable messages.
- Correlation IDs make both human debugging and AI analysis more grounded.
- Observability starts with signal quality before dashboards or tracing tools.

What comes next:

- Add incident walkthroughs that combine logs and metrics.
- Teach the AI SRE Assistant to summarize metrics alongside logs.
- Keep the local workflow simple while gradually introducing production habits.

## Week 2, Day 3 - Incident Walkthroughs

Today I added incident walkthroughs.

Day 1 cleaned up metrics.

Day 2 improved structured logs and request correlation.

Day 3 connects those signals into operational reasoning.

What changed:

- Added an incident walkthrough index.
- Added an error spike walkthrough.
- Added a latency spike walkthrough.
- Added a memory pressure walkthrough.
- Linked the walkthroughs from the observability basics doc.

Why this matters:

Observability is only useful if it helps someone debug.

Metrics can show that something changed. Logs can explain what happened in a specific request. Request IDs connect related log lines. Incident walkthroughs show how to combine those signals instead of looking at them in isolation.

Lessons learned:

- A good incident workflow starts with symptoms and evidence, not guesses.
- Metrics and logs answer different questions.
- Request IDs make logs more useful during debugging.
- The AI SRE Assistant should follow the same reasoning pattern: facts, evidence, likely causes, safe next steps.

What comes next:

- Teach the AI SRE Assistant to read metrics.
- Let incident summaries combine log evidence and metric evidence.
- Add optional Prometheus and Grafana without making them required for Day 1.

## Week 2, Day 4 - Assistant Reads Metrics

Today I taught the AI SRE Assistant to read metrics.

Day 1 gave the demo service cleaner metrics.

Day 2 made logs easier to correlate with request IDs.

Day 3 added incident walkthroughs.

Day 4 connects the assistant to a second evidence source.

What changed:

- Added a Prometheus text metrics reader.
- Added deterministic metrics analysis.
- Added `POST /analyze/metrics`.
- Updated `POST /summarize-incident` to include logs, metrics, and combined interpretation.
- Added a sample metrics file.
- Documented the new assistant behavior and metrics URL configuration.

Why this matters:

Logs and metrics answer different questions.

Logs explain specific events. Metrics show volume, status distribution, affected paths, and latency shape.

The assistant becomes more useful when it can combine both instead of only reading recent log lines.

Lessons learned:

- AI analysis is only as good as the evidence it receives.
- Deterministic analysis should work before adding LLM enrichment.
- Metrics help the assistant avoid overfitting to one log line.
- The safest assistant behavior is still facts first, guesses second, safe next steps always.

What comes next:

- Improve combined incident summaries with richer examples.
- Add optional Prometheus and Grafana for people ready to see metrics in a dashboard.
- Keep the default local path small and laptop-friendly.

## Week 3, Day 1 - Kubernetes Manifests With kind

Today I started Week 3: Kubernetes basics.

Week 1 built the local learning lab.

Week 2 added observability signals and taught the AI SRE Assistant to read logs and metrics.

Week 3 starts with the same system running in a new runtime.

What changed:

- Added a dedicated Kubernetes namespace.
- Added a ConfigMap for normal app configuration.
- Added an optional Secret example for future LLM keys.
- Added kind-friendly shared log storage for the local learning path.
- Cleaned up the demo-service and AI SRE Assistant manifests.
- Added consistent Kubernetes labels.
- Kept one replica per app to avoid shared-volume confusion.
- Rewrote the Kubernetes README as a kind-first walkthrough.

Why this matters:

Kubernetes adds complexity, but the system shape is the same:

```text
demo-service -> logs/metrics -> ai-sre-assistant -> operational summary
```

The point is not to introduce the whole Kubernetes ecosystem at once. The point is to map the working Docker Compose lab onto Kubernetes primitives: Deployments, Services, ConfigMaps, Secrets, probes, resources, and storage.

Lessons learned:

- Kubernetes is easier to teach when it is tied to a concrete app.
- A Service gives the assistant a stable name for `demo-service`.
- ConfigMaps are a cleaner home for normal environment variables.
- Secrets should be separate, even when the first version works without one.
- Shared file logs are useful for learning, but production should use a real log pipeline.

What comes next:

- Add a local Kubernetes deployment guide as a standalone doc.
- Spend a day on config and secrets.
- Spend a day on health checks, readiness, liveness, and resource limits.
- Then connect Kubernetes logs and metrics back into the observability story.

## Week 3, Day 3 - Kubernetes Operations Runbook

Today I added a Kubernetes operations runbook for the local kind setup.

Day 1 mapped the Docker Compose learning lab into Kubernetes manifests.

Day 3 focuses on the next practical question: once the pods are running, how do you inspect the system without guessing?

What changed:

- Added a Kubernetes operations runbook.
- Documented quick status checks for Deployments, Pods, Services, and PVCs.
- Added health, readiness, metrics, and assistant analysis checks.
- Added troubleshooting flows for `ImagePullBackOff`, pods that are running but not ready, missing logs, missing metrics, pending PVCs, and port-forward issues.
- Added a safe debugging order that starts with read-only inspection.
- Linked the runbook from the root README and Kubernetes walkthrough.

Why this matters:

Kubernetes is easier to learn when each command answers a specific operational question.

`kubectl get pods` is not just a command to memorize. It answers whether the workload exists and what state Kubernetes sees. `kubectl describe` explains scheduling, probes, mounts, and events. `kubectl logs` shows what the app says happened. The assistant analysis brings the application signals back into the same workflow.

Lessons learned:

- Kubernetes debugging should start with evidence, not restarts.
- Pod status, readiness, service endpoints, and application health are related but different signals.
- A Service can exist even when no ready pods are behind it.
- The shared log PVC is useful for learning, but production logging needs a real pipeline.
- The AI SRE Assistant remains more useful when it can cite logs and metrics instead of guessing.

What comes next:

- Spend a focused day on ConfigMaps, Secrets, and environment-specific configuration.
- Expand the health check and resource limit explanation.
- Keep the kind path simple before introducing Helm, Ingress, or observability stacks.

## Week 3, Day 4 - Kubernetes ConfigMaps And Secrets

Today I documented how configuration moves from Docker Compose into Kubernetes.

Day 3 focused on operating the local kind deployment. Day 4 focuses on how the apps receive configuration once they are running in the cluster.

What changed:

- Added a Kubernetes ConfigMaps and Secrets guide.
- Explained which values belong in the ConfigMap and why.
- Explained why `OPENAI_API_KEY` belongs in a Secret.
- Documented the default no-key path where the assistant uses rule-based analysis.
- Added an optional local LLM setup using a private `secret.local.yaml` file.
- Added `.gitignore` protection for the private local Secret file.
- Clarified `configmap.yaml` and `secret.example.yaml` comments.
- Linked the new guide from the README, Kubernetes walkthrough, and operations runbook.

Why this matters:

Kubernetes configuration is easier to understand when it maps back to something familiar. A Docker Compose `.env` file becomes a ConfigMap for normal values and a Secret for sensitive values.

The important production-minded habit is the boundary: commit normal config when it is safe, but never commit real credentials.

Lessons learned:

- ConfigMaps are for normal configuration, not secrets.
- Secrets should be optional when the beginner path can work without them.
- Environment variables from ConfigMaps and Secrets are read when the container starts.
- Restarting a Deployment is the simple way to pick up changed env values.
- The assistant remains useful without an LLM key because deterministic analysis is the default.

What comes next:

- Spend a focused day on probes, health checks, and resource requests/limits.
- Show how Kubernetes decides whether a pod is ready for traffic.
- Keep the local kind path small before adding Helm, Ingress, or external secret managers.

## Week 3, Day 5 - Kubernetes Health Checks And Resources

Today I documented how Kubernetes uses health checks, readiness checks, and resource settings to operate the local learning lab.

Day 4 focused on how configuration reaches the apps. Day 5 focuses on how Kubernetes decides whether those apps are alive, ready for traffic, and running with reasonable CPU and memory expectations.

What changed:

- Added a Kubernetes health checks and resources guide.
- Explained health vs readiness in beginner-friendly terms.
- Documented liveness probes, readiness probes, resource requests, and resource limits.
- Added commands for inspecting Deployments, Pods, events, endpoints, rollouts, and app health endpoints.
- Added troubleshooting notes for pods that are running but not ready, pods that keep restarting, and `OOMKilled` behavior.
- Added small manifest comments around probes and resources.
- Linked the new guide from the README, Kubernetes walkthrough, and operations runbook.

Why this matters:

Kubernetes needs clear signals to operate an app safely. A liveness probe answers whether Kubernetes should restart a container. A readiness probe answers whether the pod should receive traffic. Resource requests help scheduling. Resource limits create local safety boundaries.

Lessons learned:

- Running is not the same as ready.
- Readiness failures should usually remove traffic, not restart the app.
- Liveness probes should be conservative because bad restart behavior can make incidents worse.
- Resource requests are scheduling signals; limits are enforcement boundaries.
- The current values are learning defaults, not production tuning recommendations.

What comes next:

- Connect Kubernetes events, logs, and assistant analysis into a clearer incident workflow.
- Add a small Kubernetes troubleshooting example using the existing simulated failure endpoints.
- Keep autoscaling and HPA for after resource requests are easier to understand.

## Week 3, Day 6 - Kubernetes Incident Debugging

Today I connected the Kubernetes learning path into an incident debugging workflow.

Day 5 focused on probes and resources. Day 6 focuses on what to do when the app is running in Kubernetes but the service still shows failures, latency, or warning signals.

What changed:

- Added a Kubernetes incident debugging walkthrough.
- Documented how to create intentional symptoms with existing simulation endpoints.
- Added a debugging order from Kubernetes state to app health, logs, metrics, and assistant analysis.
- Added commands for inspecting Deployments, Pods, Services, endpoints, PVCs, events, logs, metrics, and assistant summaries.
- Added a debugging map that connects symptoms to first checks and likely interpretations.
- Linked the walkthrough from the README, Kubernetes walkthrough, and operations runbook.

Why this matters:

Kubernetes can tell you what is happening to the workload, but it does not automatically explain what is happening inside the application. Logs and metrics provide that application evidence. The AI SRE Assistant helps summarize those signals into practical operational language.

Lessons learned:

- Start broad with Kubernetes state before narrowing into app behavior.
- A healthy pod can still serve failing endpoints.
- Logs explain specific events; metrics explain shape and volume.
- Assistant output is most useful when it is grounded in collected evidence.
- Good debugging starts with facts before fixes.

What comes next:

- Wrap Week 3 with production-minded Kubernetes next steps.
- Explain what should change before this pattern becomes production-grade.
- Keep advanced tools like Helm, Ingress, HPA, and service mesh as future roadmap items.

## Week 3, Day 7 - Kubernetes Production Next Steps

Today I closed out Week 3 by documenting what the local Kubernetes path teaches and what still needs to change before anything looks production-grade.

Day 6 connected Kubernetes state, app health, logs, metrics, and assistant analysis into an incident debugging workflow. Day 7 turns that into production-minded next steps.

What changed:

- Added a Kubernetes production next-steps guide.
- Documented which choices are local-only learning defaults.
- Mapped local shortcuts to production alternatives.
- Expanded the production considerations doc.
- Updated the roadmap to reflect Week 3 completion and Week 4 direction.
- Linked the new guide from the README, Kubernetes walkthrough, and incident debugging guide.

Why this matters:

The project should be beginner-friendly without pretending the local kind setup is production architecture. Week 3 taught the primitives: Deployments, Pods, Services, ConfigMaps, Secrets, PVCs, probes, resources, logs, metrics, and incident flow. Day 7 explains what comes next without rushing into every Kubernetes tool at once.

Lessons learned:

- Local Kubernetes is useful when the app stays concrete.
- Shared file logs are a learning bridge, not a production logging design.
- One replica keeps the lesson simple, but production needs stateless scaling patterns.
- Kubernetes Secrets teach the primitive, but production needs stronger secret management.
- Advanced tools should arrive only after the problem they solve is visible.

What comes next:

- Start Week 4 with security hardening basics.
- Add secret handling and redaction rules.
- Introduce cost optimization and assistant evaluation basics.
- Keep vLLM, Triton, Ray, KServe, and GPU scheduling as optional advanced roadmap items.

## Week 4, Day 1 - Security Hardening Basics

Today I started Week 4 by adding the first security hardening layer.

Week 3 answered how the app maps into Kubernetes. Week 4 starts with a different question: what could leak, who can access what, and how should the assistant behave safely?

What changed:

- Added a `SECURITY.md` for public reporting guidance.
- Expanded the security documentation with a project threat model.
- Documented local secret rules for `.env`, `OPENAI_API_KEY`, Kubernetes Secret examples, and `secret.local.yaml`.
- Added guidance for logs, LLM provider safety, assistant behavior, service exposure, containers, and dependency basics.
- Linked security guidance from the README and Kubernetes production next-steps guide.

Why this matters:

Security should show up before production. The local lab is intentionally simple, but the habits should be production-minded: keep secrets out of git, redact sensitive logs, avoid sending private data to LLM providers without review, and treat assistant output as evidence-grounded guidance rather than authority.

Lessons learned:

- Security starts with naming what can leak.
- A local `.env` file is convenient, but it must stay out of git.
- Logs are evidence, but they can also become a data leak.
- The safest assistant behavior is conservative, cited, and non-destructive.
- Kubernetes Secrets teach the primitive, but production needs stronger secret management.

What comes next:

- Add focused redaction guidance for logs and assistant inputs.
- Tighten examples around safe secret handling.
- Continue Week 4 with cost optimization and assistant evaluation basics.

## Week 4, Day 2 - Secret Handling And Redaction Rules

Today I turned the security guidance into an enforced assistant boundary.

Day 1 named the main risks and guardrails. Day 2 focuses on reducing accidental credential exposure as logs and questions move through the assistant.

What changed:

- Added a reusable redaction module for structured fields and common token patterns.
- Redacted parsed JSON fields and raw log text before rule-based analysis.
- Redacted assistant questions before analysis and before echoing them in API responses.
- Added defense-in-depth redaction immediately before optional LLM requests.
- Redacted generated LLM text and final API responses.
- Added focused tests for nested fields, free text, malformed logs, API output, and LLM prompts.
- Added a dedicated secret handling and redaction guide with safe examples and explicit limitations.
- Aligned the assistant README, security model, security policy, and root README with the implemented behavior.

Why this matters:

Logs are valuable operational evidence, but they are also a common path for accidental data exposure. An optional external LLM adds another boundary where the project must minimize what leaves the local environment.

The rule-based path still works without a provider. When a provider is enabled, pattern-based redaction now happens before the request. This reduces obvious leaks without pretending that regex-based filtering makes arbitrary production data safe.

Lessons learned:

- Preventing secrets from entering logs is stronger than removing them later.
- Redaction should happen near ingestion and again at external boundaries.
- Structured field rules and free-text token rules solve different parts of the problem.
- Generated model text needs the same output checks as input prompts.
- A security control should document its false-positive and false-negative limits.
- A leaked credential must be rotated even if the visible copy is later redacted.

What comes next:

- Continue Week 4 with practical cost optimization habits.
- Keep assistant evaluation basics next so safety and usefulness can be tested together.

## Week 4, Day 3 - Cost Optimization Basics

Today I added the first practical cost controls for the AI SRE Assistant.

Day 1 named the security risks. Day 2 enforced redaction. Day 3 focuses on a different production habit: make optional LLM usage explicit, bounded, and easy to turn off.

What changed:

- Kept the deterministic rule-based analyzer as the default no-cost path.
- Added `LLM_MAX_LOG_ENTRIES` to limit how many recent logs can enter an LLM prompt.
- Added `LLM_MAX_PROMPT_CHARS` to cap the assembled provider prompt.
- Added prompt truncation notices when cost controls reduce evidence size.
- Added `llm_cost_controls` metadata to API responses that attempt LLM enrichment.
- Wired the defaults through `.env.example`, Docker Compose, and the Kubernetes ConfigMap.
- Added tests for environment parsing, log-window limits, prompt-size limits, and API cost-control metadata.
- Added a dedicated cost optimization guide and linked it from the README and assistant docs.
- Updated the security guide to connect cost controls with reduced provider data exposure.

Why this matters:

AI infrastructure cost can grow before a usage dashboard exists. A single incident summary may be cheap, but repeated provider calls, large log windows, large prompts, expensive models, and broad refresh loops can turn the same workflow into a cost problem.

The safest beginner default is still local rule-based analysis. When LLM enrichment is useful, the assistant now sends a bounded amount of evidence and tells callers which limits were active.

Lessons learned:

- Cost optimization starts at the call boundary.
- The cheapest provider request is the one you do not need to make.
- A smaller prompt usually means lower cost, lower latency, and lower exposure.
- Character limits are not exact token accounting, but they are useful as beginner guardrails.
- Cost controls should be visible in API responses, not hidden in configuration.
- Security and cost optimization often point in the same direction: send less unnecessary data.

What comes next:

- Add assistant evaluation basics so usefulness, safety, and cost can be checked together.
- Consider provider usage metadata when a provider returns token counts.
- Keep dashboards, caching, quotas, and model routing as later steps after the simple controls are understood.

## Week 4, Day 4 - Assistant Evaluation Basics

Today I made AI SRE Assistant quality testable with a small deterministic evaluation suite.

Day 1 hardened the security model. Day 2 enforced redaction. Day 3 bounded optional LLM cost. Day 4 checks whether the assistant remains useful, safe, and honest while those controls evolve.

What changed:

- Added seven incident evaluation cases for healthy traffic, error spikes, latency, memory pressure, malformed logs, missing logs, and secret-bearing evidence.
- Added a reusable five-part rubric: grounded, useful, safe, private, and honest.
- Added a command-line evaluation runner with a non-zero exit code on regression.
- Added tests for every case plus negative tests that prove missing grounding and leaked secrets are detected.
- Added a containerized `make evaluate-assistant` workflow.
- Documented the limits of deterministic checks and the path toward real incident datasets, human review, and model comparisons.
- Documented how the public evaluation method can grow through versioned cases, private fixtures, release gates, alerts, comparisons, and audit exports.

Why this matters:

An AI assistant can sound plausible without being correct. Operational teams need repeatable evidence that a new prompt, model, provider, or code change did not weaken grounding, privacy, or safety.

Evaluation makes the assistant easier to improve responsibly: maintainers can measure quality over time, use private cases carefully, block regressions, compare cost against outcomes, and preserve governance evidence.

Lessons learned:

- AI assistants need evals before they need more autonomy.
- A small known corpus is more useful than an impressive but unrepeatable demo.
- Safety and privacy should be pass/fail gates, not averages that can be hidden by other scores.
- The evaluator itself needs negative tests so teams know it catches real regressions.
- Open evaluation builds trust and gives contributors a repeatable way to discuss regressions.

What comes next:

- Add production observability upgrade guidance.
- Capture provider token usage, latency, and model identity for future quality/cost comparisons.
- Grow the corpus with sanitized incidents before introducing more assistant autonomy.

## Week 4, Day 5 - Production Observability Upgrade Path

Today I mapped the local Reliability Lab signals to a production observability architecture.

Day 4 made assistant quality testable. Day 5 asks how teams can operate, govern, and measure the service once logs and metrics no longer live on one laptop.

What changed:

- Added a production telemetry flow from services through a collector into metrics, logs, traces, dashboards, alerts, and controlled assistant evidence APIs.
- Separated observability into service reliability and assistant quality-and-safety signals.
- Proposed bounded assistant metric names for requests, latency, fallbacks, truncation, redaction, eval checks, and provider tokens.
- Added dashboard ownership for platform, security, and operations maintainers.
- Added SLI templates for service health, assistant availability, latency, evaluation safety, and provider resilience.
- Documented alert design around user impact, ownership, runbooks, and sustained symptoms.
- Added privacy, security, retention, sampling, cardinality, and telemetry-cost controls.
- Compared open-source, managed, and hybrid deployment paths without changing the default local stack.
- Added a seven-stage migration plan and production-readiness checklist.
- Documented privacy-aware telemetry boundaries without treating sensitive incident data as analytics exhaust.

Why this matters:

Production observability is more than installing dashboards. Teams need stable signals, clear ownership, useful alerts, controlled evidence access, and a way to connect assistant quality and provider cost to real user outcomes.

Those signals must remain useful without compromising the incident data operators trust the lab to protect.

Lessons learned:

- Start with operating questions and owners before choosing a backend.
- Service health and assistant quality require different signals.
- Safety and privacy checks should remain release gates rather than averages.
- Request IDs belong in logs and traces, not high-cardinality metric labels.
- OpenTelemetry can preserve backend choice, but it does not replace retention, access, or cost decisions.
- Outcome telemetry should measure useful results without collecting unnecessary incident content.

What comes next:

- Keep the default setup small and add production components as optional paths.
- Add provider token, latency, and model metadata for quality/cost comparisons.
- Consider a focused OpenTelemetry Collector example after the signal contracts are stable.

## Week 4, Day 6 - Advanced Model Serving Roadmap

Today I defined when Reliability Lab should move from managed model providers to self-hosted inference.

Day 5 mapped the production observability path. Day 6 uses quality, latency, usage, and cost signals to decide whether advanced serving infrastructure is justified.

What changed:

- Added adoption gates for privacy boundaries, model control, latency, sustained volume, availability control, and multi-model workloads.
- Mapped vLLM, NVIDIA Triton Inference Server, Ray Serve, KServe, and Kubernetes GPU scheduling to the specific problems each layer solves.
- Added a staged path from deterministic analysis and managed providers to single-GPU benchmarks and bounded production experiments.
- Added a provider-versus-self-host benchmark plan using the same assistant evaluation corpus and safety gates.
- Defined cost per successful evaluated analysis as the comparison instead of GPU price or token price alone.
- Documented GPU operating requirements, including drivers, device plugins, placement, quotas, memory behavior, autoscaling signals, cold starts, telemetry, and upgrades.
- Added security and governance requirements for model licenses, artifacts, endpoints, isolation, redaction, versioning, and rollback.
- Kept the default project path provider-compatible, deterministic, and GPU-free.

Why this matters:

Self-hosted model serving can improve control and privacy for the right workload. It can also create idle GPU cost, upgrade risk, new security ownership, and an on-call burden before a measured requirement exists.

Lessons learned:

- Advanced infrastructure should follow a demonstrated constraint.
- The smallest serving stack is usually the easiest one to operate.
- Quality and safety must pass before throughput optimization matters.
- Provider and self-hosted paths need the same benchmark workload and acceptance gates.
- GPU utilization alone does not capture engineering, reliability, and idle-capacity cost.
- Private deployment changes who owns security controls; it does not make the system secure automatically.

What comes next:

- Capture provider usage and latency metadata.
- Build a provider-versus-self-host benchmark harness.
- Add one optional single-GPU vLLM example only after the benchmark contract is ready.
- Document any future serving layer as a bounded operational experiment.

## Week 4, Day 7 - Production Readiness Review

Today I closed Week 4 with a release decision and an enforced quality gate.

Day 6 defined when advanced serving infrastructure is justified. Day 7 steps back and asks the more important question: what is this project ready for now, what evidence supports that decision, and what must be true before the next promotion?

What changed:

- Added `make validate` as one local gate for image builds, both test suites, lint, and deterministic assistant evaluations.
- Added the assistant evaluation runner to pull-request CI so quality, safety, and privacy regressions block the build.
- Added a production-readiness review with separate decisions for a local lab, public learning release, sanitized internal pilot, and internet-facing production.
- Mapped current evidence and remaining boundaries across security, cost, quality, observability, reliability, and model serving.
- Defined promotion gates for identity, data handling, secrets, supply chain, reliability, observability, quality, cost, and deployment.
- Prioritized a focused next 30 days around provider metadata, deeper evals, stable telemetry contracts, runbook exercises, and benchmark evidence.
- Updated the roadmap, README, contribution checks, and evaluation guide to match the enforced release workflow.

Why this matters:

Production readiness is not a feeling and it is not a list of tools. It is a decision backed by tests, measurable gates, clear ownership, and an honest account of unresolved risk.

Reliability Lab is ready to ship as an open learning project when the validation gate passes. It is not yet an internet-facing multi-tenant production service, and the review says so explicitly. That boundary makes the project more credible, not less ambitious.

Lessons learned:

- Documentation becomes stronger when its claims are enforced in CI.
- Privacy and safety checks should block releases rather than disappear into an average score.
- A single readiness label is misleading; local, pilot, and internet-facing targets have different gates.
- Advanced infrastructure should follow measured requirements and operational ownership.
- The strongest closeout is a clear decision, visible evidence, and a small next set of priorities.

What comes next:

- Capture provider usage, latency, model identity, and fallback outcomes.
- Grow the evaluation corpus with sanitized representative incidents.
- Add an optional telemetry collector only after signal contracts are stable.
- Exercise one alert and runbook path end to end.
- Benchmark provider and private endpoints before introducing GPU infrastructure.

## Week 5, Day 1 - Provider Telemetry Contract

Today I started the Week 5 measurement cycle by making optional provider behavior visible without recording sensitive incident content.

Week 4 established redaction, prompt bounds, deterministic evaluation, and production-readiness gates. Week 5 starts with the metadata needed to compare provider reliability, quality, and cost honestly.

What changed:

- Added a structured LLM call result with analysis, notice, and bounded telemetry.
- Added provider and model labels without exposing the provider base URL.
- Added configuration, attempt, success, failure, and fallback state.
- Measured provider request latency with a monotonic clock.
- Normalized OpenAI-compatible prompt, completion, and total token usage when reported.
- Kept missing or malformed usage honest with explicit `null` values and `reported=false`.
- Exposed the same `llm_telemetry` contract from log analysis, questions, and incident summaries.
- Added tests for successful usage, latency, provider failure, unconfigured fallback, both API paths, and telemetry privacy.
- Added a provider telemetry guide with field semantics, forbidden data, operational value, and the remaining Week 5 sequence.
- Restored the canonical Weeks 5-8 technical roadmap.

Why this matters:

A provider call should not be a black box. Teams need to know whether enrichment ran, whether it failed safely, how long it took, and whether the provider reported usage. Those facts are the foundation for comparing quality and cost later.

The metadata boundary matters just as much as the fields. Prompt text, incident evidence, credentials, endpoint URLs, generated output, and user identifiers do not belong in provider telemetry.

Operational value:

- Operators can distinguish successful enrichment from silent deterministic fallback.
- Teams can later compare provider latency and token usage with evaluated quality.
- Cost can be measured per successful analysis instead of per token in isolation.
- Managed and private OpenAI-compatible endpoints share the same outcome contract.
- The local contract remains useful without requiring additional platform infrastructure.

Lessons learned:

- Missing usage metadata is not zero usage; it is unknown and should be represented honestly.
- Provider failure and provider-not-configured are different operational outcomes.
- A monotonic clock is the right boundary for request duration.
- Useful telemetry can remain small, bounded, and free of incident content.
- Per-request metadata should come before aggregate metrics or dashboards.

What comes next:

- Add bounded aggregate counters and latency distributions.
- Define explicit pricing inputs without hard-coding unstable provider prices.
- Join provider usage and cost with evaluation outcomes.
- Calculate and report cost per successful evaluated analysis.

## Week 5, Day 2 - Provider Aggregate Metrics

Today I turned the per-request provider contract into privacy-safe operational aggregates.

Day 1 made each provider attempt visible to its caller. Day 2 makes trends scrapeable without retaining prompts, incident evidence, generated content, user identifiers, or arbitrary error text.

What changed:

- Added an in-memory, dependency-free provider metrics registry to the AI SRE Assistant.
- Counted enrichment outcomes across success, failure, and provider-not-configured paths.
- Added a fixed-bucket latency histogram for attempted provider requests.
- Counted deterministic fallbacks by the two supported reasons.
- Accumulated valid provider-reported input and output tokens while keeping missing usage unknown.
- Exposed the aggregates as Prometheus text at `GET /metrics`.
- Limited labels to deployment-configured provider/model values and fixed outcome, reason, and direction enums.
- Mapped unexpected enum values to bounded fallback labels instead of accepting arbitrary strings.
- Added tests for counters, cumulative latency buckets, token totals, fallbacks, malformed values, privacy, and the metrics endpoint.
- Updated the roadmap and telemetry guide to mark Day 2 complete and define the remaining Week 5 sequence.

Why this matters:

Per-request metadata helps debug one analysis. Aggregate counters and distributions reveal whether provider enrichment is reliable, fast, and consistently reporting usage across many analyses. That is the evidence needed before pricing and quality are joined later in the week.

The privacy and cardinality boundaries are part of the feature. Prompts, evidence, errors, endpoints, request IDs, users, workspaces, and incidents never become labels. Process-local metrics also remain honest about their limits: they reset on restart and are not durable usage history.

Lessons learned:

- Latency needs a distribution; an average hides slow tails.
- Not configured is an outcome, but it is not an attempted provider request and should not enter request-latency buckets.
- Missing token usage is unknown, not zero.
- Configured provider/model labels are useful only with an explicit cardinality budget.
- Operational metrics and durable usage history are different systems with different access and retention requirements.

What comes next:

- Define explicit pricing inputs without hard-coding unstable provider prices.
- Calculate estimated cost metadata from reported usage.
- Join cost and provider outcomes with evaluation results.
- Report cost per successful evaluated analysis.


## Week 5, Day 3 - Provider Cost Estimates

Today I made the provider telemetry contract cost-aware without turning the lab into a usage-accounting system.

Day 1 exposed the outcome and usage of one provider attempt. Day 2 made aggregate reliability and token trends scrapeable. Day 3 turns operator-supplied prices and provider-reported token directions into an honest per-call estimate.

What changed:

- Added optional input and output price configuration in USD per million tokens.
- Returned decimal-string `llm_cost_estimate` metadata from every LLM-enabled API path.
- Kept estimates unavailable when either price or either token direction is missing, malformed, or unknown.
- Wired pricing configuration through local environment files, Docker Compose, and the Kubernetes ConfigMap/Deployment.
- Added deterministic tests for arithmetic, malformed pricing, incomplete usage, and API unknown states.
- Updated the provider telemetry contract, roadmap, and assistant documentation.

Why it matters:

Token counts alone do not tell an operator what one enriched analysis costs. A small, explicit estimate lets operators compare provider paths later without pretending the project owns durable usage history or that static provider prices are universally correct.

Key lessons:

- Price inputs are deployment-owned configuration because provider prices change.
- Unknown usage and unknown prices must remain unknown, never silently become zero.
- Currency values should use decimal representations, not floating-point values.
- Cost per successful evaluated analysis belongs in the next step, where quality outcomes can be joined deliberately.

## Week 5, Day 4 - Evaluation Cost Report

Today I joined deterministic assistant evaluation results to bounded optional-provider outcomes and estimated cost.

What changed:

- Added an explicit provider-report mode that makes one enrichment call per corpus fixture.
- Joined each deterministic rubric result with the existing privacy-safe provider telemetry and cost-estimate contracts.
- Calculated estimated total cost and estimated cost per successful evaluated analysis only when all successful evaluations have complete price and token data.
- Kept incomplete cost data unknown instead of treating it as zero.
- Kept the default deterministic evaluation command offline and cost-free for CI.

Next: add a local comparison report, exercise fallback end to end, and close the Week 5 exit gate.

## Week 5, Day 5 - Local Provider Comparison

Today I closed the Week 5 measurement loop with a bounded local comparison report and an end-to-end fallback check.

What changed:

- Added `python -m evals.run_evals --comparison-report` to run the same corpus through the deterministic release gate and the selected optional-provider path.
- Reported only quality summaries, bounded provider/model identity, outcome counts, fallback count, and estimated cost summaries.
- Added an explicit comparison status so `ready_to_compare` requires deterministic quality to pass, every provider call to succeed, and cost data to be complete.
- Kept provider calls opt-in and out of CI; the default evaluation remains offline and cost-free.
- Exercised the `LLM_PROVIDER=none` path end to end to verify that provider-not-configured falls back safely without a network request.

Why this matters:

Provider comparisons are useful only when they preserve the deterministic quality gate and make unknowns visible. A local report makes the tradeoff inspectable without turning test fixtures or provider responses into a usage dataset.

Week 5 exit-gate review:

The local learning path can now compare provider usage, reliability, and deployment-owned cost with deterministic evaluation outcomes while preserving the telemetry privacy boundary. Durable metering, provider-quality scoring, and managed-versus-private benchmarks remain later, deliberately bounded work.
