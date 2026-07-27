# Provider Telemetry Contract

Week 5, Days 1 through 3 establish privacy-safe per-request metadata, process-local aggregate metrics, and explicit per-call cost estimates for optional LLM calls.

The assistant already bounded prompts and fell back to deterministic analysis. The missing foundation was a consistent way to answer: which provider path was selected, was a request attempted, did it succeed, how long did it take, did the provider report token usage, and did the deterministic fallback protect the user?

## API Contract

When `use_llm=true`, `/ask`, `/analyze/logs`, and `/summarize-incident` include `llm_telemetry` alongside the existing analysis and cost-control fields.

```json
{
  "llm_telemetry": {
    "provider": "openai",
    "model": "approved-model",
    "configured": true,
    "attempted": true,
    "outcome": "success",
    "request_latency_ms": 842.37,
    "fallback_used": false,
    "fallback_reason": null,
    "usage": {
      "reported": true,
      "input_tokens": 420,
      "output_tokens": 96,
      "total_tokens": 516
    }
  }
}
```

This API contract is per request. Day 2 also aggregates its bounded fields as Prometheus text. Day 3 adds a per-call `llm_cost_estimate` only when deployment-owned prices and provider-reported input/output token counts are both available. None of these surfaces is a persistent usage ledger.

## Field Semantics

| Field | Meaning |
| --- | --- |
| `provider` | Bounded, redacted provider label from configuration. It never contains the base URL. |
| `model` | Bounded, redacted model label when the provider is configured; otherwise `null`. |
| `configured` | Whether the selected provider has the minimum required configuration. |
| `attempted` | Whether the assistant attempted a network request to the provider. |
| `outcome` | One of `success`, `failure`, or `not_configured`. |
| `request_latency_ms` | Provider request duration measured with a monotonic clock; `null` when no request was attempted. |
| `fallback_used` | Whether the final response stayed on the deterministic rule-based path. |
| `fallback_reason` | `provider_not_configured`, `provider_request_failed`, or `null`. |
| `usage.reported` | Whether the provider returned usable token counts. |
| `usage.input_tokens` | Normalized `prompt_tokens`, or `null` when unavailable. |
| `usage.output_tokens` | Normalized `completion_tokens`, or `null` when unavailable. |
| `usage.total_tokens` | Provider total, or the sum of valid input and output counts when both exist. |

## Cost Estimate Contract

When `use_llm=true`, the response also includes `llm_cost_estimate`. Pricing is supplied by the deployment; the project never fetches or embeds provider price lists because those prices are model-, region-, and time-dependent.

```json
{
  "llm_cost_estimate": {
    "currency": "USD",
    "pricing_configured": true,
    "input_usd_per_million_tokens": "0.15",
    "output_usd_per_million_tokens": "0.60",
    "estimate_available": true,
    "estimated_input_cost_usd": "0.00001800",
    "estimated_output_cost_usd": "0.00001800",
    "estimated_total_cost_usd": "0.00003600",
    "unavailable_reason": null
  }
}
```

Set `LLM_INPUT_USD_PER_MILLION_TOKENS` and `LLM_OUTPUT_USD_PER_MILLION_TOKENS` to non-negative USD values per million provider-reported tokens. Both values are optional and default to unknown. The estimate is available only when both prices and both token directions are reported; otherwise every estimated cost remains `null` and `unavailable_reason` is `pricing_not_configured` or `incomplete_token_usage`.

Cost values are decimal strings to avoid floating-point ambiguity. They are estimates for one provider call, not invoices, durable metering, or identity-linked usage attribution.

Unknown, negative, boolean, or malformed token values are treated as unavailable. Providers may omit usage; omission does not turn a successful analysis into a failure.

## Aggregate Metrics

`GET /metrics` on the AI SRE Assistant exposes four process-local metric families:

| Metric | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `ai_sre_provider_analyses_total` | Counter | `provider`, `model`, `outcome` | LLM enrichment selections, including successful, failed, and not-configured outcomes. |
| `ai_sre_provider_request_duration_seconds` | Histogram | `provider`, `model`, `outcome` | Latency distribution for attempted provider requests only. |
| `ai_sre_provider_fallbacks_total` | Counter | `provider`, `model`, `reason` | Deterministic fallbacks caused by missing configuration or request failure. |
| `ai_sre_provider_tokens_total` | Counter | `provider`, `model`, `direction` | Provider-reported input and output tokens; missing usage is not treated as zero. |

The histogram uses fixed buckets from 50 milliseconds through the 30-second request timeout plus `+Inf`. Unconfigured selections increment the analysis and fallback counters but do not create a provider-request latency observation.

These aggregates are intentionally in memory and reset when the assistant process restarts. Durable metering, retention, multi-process aggregation, and identity-linked usage history remain separate production concerns.

### Label Boundary

Provider and model values come only from deployment configuration, pass through redaction, and are limited to 100 characters. Outcome, fallback reason, and token direction use fixed enums. The registry maps unexpected enum values to `unknown` or `other` rather than accepting arbitrary strings.

The aggregate contract never labels metrics with prompts, evidence, generated content, provider endpoints, errors, request IDs, users, workspaces, or incidents. Operators should also keep the number of configured provider/model pairs within an explicit cardinality budget.

Example:

```text
ai_sre_provider_analyses_total{provider="openai",model="approved-model",outcome="success"} 12
ai_sre_provider_request_duration_seconds_bucket{provider="openai",model="approved-model",outcome="success",le="1"} 9
ai_sre_provider_fallbacks_total{provider="openai",model="approved-model",reason="provider_request_failed"} 2
ai_sre_provider_tokens_total{provider="openai",model="approved-model",direction="input"} 5040
```

## Outcomes And Fallbacks

| Situation | Outcome | Attempted | Fallback |
| --- | --- | --- | --- |
| `LLM_PROVIDER=none` or incomplete configuration | `not_configured` | No | Yes: `provider_not_configured` |
| Valid response with non-empty content | `success` | Yes | No |
| Network, HTTP, parsing, or empty-content failure | `failure` | Yes | Yes: `provider_request_failed` |
| Request sets `use_llm=false` | No LLM telemetry block | No | The deterministic path was explicitly selected, not used as a provider fallback. |

## Privacy Boundary

Provider telemetry may contain only bounded operational metadata.

Allowed:

- Provider and model labels.
- Configuration, attempt, outcome, and fallback state.
- Request latency.
- Numeric token counts.

Forbidden:

- Questions or prompts.
- Log, metric, trace, or incident evidence.
- API keys, authorization headers, or credentials.
- Provider base URLs.
- Model output or failure payloads.
- User, request, workspace, or incident identifiers.

Tests inject secrets into questions, logs, credentials, provider output, and failure messages and verify that those values never enter the telemetry object. The final API response still passes through the existing defense-in-depth redaction boundary.

## Operational Value

This contract helps maintainers understand provider behavior without storing sensitive content:

- Operators can distinguish successful enrichment from deterministic fallback.
- Provider latency and token usage can be compared with evaluated quality later.
- Managed and private OpenAI-compatible endpoints share the same normalized outcome contract.

Do not attach user or workspace identifiers to Prometheus labels. Detailed audit records require an access-controlled event store with explicit retention.

## Day 1 Definition Of Done

- Provider and model identity are exposed as bounded, redacted labels.
- Success, failure, unconfigured state, and deterministic fallback are distinguishable.
- Provider request latency uses a monotonic clock.
- OpenAI-compatible token usage is normalized when present and honest when absent.
- No prompt, evidence, credential, endpoint URL, or generated output enters telemetry.
- Both LLM-enabled API flows expose the same contract.
- Success, failure, fallback, usage, latency, and privacy behavior have deterministic tests.

## Day 2 Definition Of Done

- Provider outcome selections are counted across success, failure, and not-configured paths.
- Attempted requests populate a fixed latency histogram with count and sum.
- Deterministic fallback reasons are counted separately.
- Valid provider-reported input and output tokens are accumulated without converting unknown usage to zero.
- Labels are limited to configured provider/model values and fixed enums.
- Sensitive payload fields and arbitrary error text never enter the aggregate metrics.
- The assistant exposes the contract as Prometheus text at `GET /metrics`.
- Aggregation, histogram, fallback, token, malformed-value, privacy, and endpoint behavior have deterministic tests.

## Day 3 Definition Of Done

- Input and output pricing are explicit deployment configuration, never a hard-coded or fetched provider price table.
- Estimates require both valid prices and both provider-reported token directions.
- Missing, malformed, partial, or unavailable inputs remain unknown rather than becoming zero cost.
- Decimal-string cost values avoid floating-point ambiguity.
- API, configuration parsing, incomplete usage, and privacy behavior have deterministic tests.

## Day 4 Definition Of Done

- The deterministic evaluation corpus can be run with explicit optional-provider enrichment.
- Each result joins the rubric outcome with bounded provider telemetry and the per-call cost estimate.
- The report calculates cost per successful evaluated analysis only when every successful evaluation has complete cost data.
- Unknown price or token information remains unknown and includes a reason rather than becoming zero.
- Normal evaluation remains offline and cost-free; provider calls require an explicit command.

## Day 5 Definition Of Done

- `python -m evals.run_evals --comparison-report` emits a bounded local comparison of the deterministic release gate and selected provider path.
- The report includes only quality summaries, provider/model identity, outcome counts, fallback count, and cost summary; it excludes fixture evidence, prompts, outputs, credentials, and endpoints.
- A configured provider remains opt-in and makes one call per fixture; the normal CI evaluation remains offline and cost-free.
- `LLM_PROVIDER=none` exercises the deterministic fallback end to end and reports `provider_not_configured` without attempting a network call.
- A provider is ready to compare only when the deterministic gate passes, every provider call succeeds, and cost data is complete.

## Week 5 Exit Gate Review

The Week 5 exit gate is met for the local learning path: provider identity, latency, usage, outcome, fallback, and deployment-owned cost estimates can be compared with deterministic evaluation outcomes without storing prompts, incident evidence, credentials, endpoints, or generated output.

The comparison is intentionally a local point-in-time report, not a durable usage ledger, a provider-quality benchmark, or an approval to enable a provider in CI. Week 6 will expand and version the corpus; Week 8 will evaluate managed and private endpoints under a controlled benchmark plan.
