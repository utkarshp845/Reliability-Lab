# ai-sre-assistant

`ai-sre-assistant` reads recent `demo-service` logs and explains what happened in operational language.

It can use an OpenAI-compatible LLM provider for richer analysis. If no provider is configured, it uses a deterministic rule-based analyzer so the project works for everyone.

## API

- `GET /health`
- `GET /metrics`
- `POST /analyze/logs`
- `POST /analyze/metrics`
- `POST /ask`
- `POST /summarize-incident`

Example:

```bash
curl -s -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What errors happened recently?","max_lines":120}'
```

Analyze metrics:

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

## CLI

From the repository root after `make up` and `make generate-traffic`:

```bash
make analyze-logs
```

Or from this app directory:

```bash
python cli/sre.py analyze --log-path ../../logs/demo-service.log
python cli/sre.py ask "Is this a latency issue or an application bug?" --log-path ../../logs/demo-service.log
```

## LLM Configuration

The deterministic analyzer is the default. To use an LLM, update `.env`:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=your_model
LLM_MAX_LOG_ENTRIES=50
LLM_MAX_PROMPT_CHARS=12000
LLM_INPUT_USD_PER_MILLION_TOKENS=
LLM_OUTPUT_USD_PER_MILLION_TOKENS=
DEMO_SERVICE_METRICS_URL=http://localhost:8000/metrics
```

For local Ollama experiments, set `LLM_PROVIDER=ollama` and use an OpenAI-compatible Ollama base URL.

## Cost Controls

The rule-based analyzer remains the lowest-cost path. Keep `LLM_PROVIDER=none` or set `use_llm=false` on requests when LLM enrichment is not needed.

When an LLM provider is enabled, the assistant limits provider prompts with:

- `LLM_MAX_LOG_ENTRIES`: how many recent log records can be included in the prompt.
- `LLM_MAX_PROMPT_CHARS`: maximum assembled user prompt size before the provider request.

API responses that attempt LLM enrichment include `llm_cost_controls` so callers can see which limits were active. If prompt evidence is truncated, the response includes an `llm_notice`.

See `../../docs/16-cost-optimization.md` for the Day 3 cost optimization guide.

## Provider Telemetry

When `use_llm=true`, LLM-enabled API responses include `llm_telemetry` with bounded provider and model labels, configuration and attempt state, success or fallback outcome, request latency, and normalized token usage when the provider reports it.

The telemetry object never includes prompts, incident evidence, credentials, provider base URLs, generated output, or user and incident identifiers. It is per-request metadata, not a persistent usage ledger. When both deployment-owned input/output prices and provider-reported token directions are available, responses also include an `llm_cost_estimate`; otherwise its cost fields remain explicitly unknown.

`GET /metrics` exposes privacy-safe in-memory aggregates for analysis outcomes, provider request latency, deterministic fallbacks, and provider-reported input/output tokens. Labels are limited to the configured provider/model and fixed outcome, reason, and direction enums. These process-local counters reset when the assistant restarts.

See `../../docs/22-provider-telemetry.md` for field semantics, privacy rules, failure behavior, and the remaining Week 5 sequence.

## Evaluation

The assistant includes a deterministic incident corpus and a five-part quality rubric. Run it locally from this directory:

```bash
python -m evals.run_evals
```

Or run the containerized workflow from the repository root:

```bash
make evaluate-assistant
```

The suite covers healthy traffic, error spikes, latency, memory pressure, malformed logs, missing logs, and secret-bearing evidence. Every case is checked for grounded, useful, safe, private, and honest output.

See `../../docs/17-assistant-evaluation.md` for the rubric, limitations, and future product path.

## Redaction

The assistant replaces obvious sensitive values with `[REDACTED]` before analysis and before data is sent to an optional LLM provider.

Redaction covers:

- parsed and raw log content.
- sensitive nested fields and common token patterns.
- questions echoed by the API.
- LLM prompt inputs and generated text.
- final API responses.

This is a pattern-based backup control, not a complete data loss prevention system. Keep secrets out of logs and review operational data before sharing it or enabling an external provider. See `../../docs/15-secret-handling-and-redaction.md`.

## Provider Evaluation Cost Report

To join the deterministic rubric with real optional-provider outcomes and estimated cost, configure the provider and prices, then run:

```bash
python -m evals.run_evals --provider-report
```

This explicit command makes one provider call per evaluation case and prints a bounded JSON report, including estimated cost per successful evaluated analysis when complete token and price data is available. It remains outside CI so the normal release gate stays offline and cost-free.

## Local Provider Comparison

To compare the deterministic release gate with the configured provider path, run:

```bash
python -m evals.run_evals --comparison-report
```

The report contains only counts, bounded provider/model identity, quality-gate parity, provider outcomes, fallback count, and cost summaries. It does not print fixture evidence, prompts, provider output, credentials, or endpoints. A configured provider makes one call per fixture; with `LLM_PROVIDER=none`, the same command is an offline end-to-end fallback check.
