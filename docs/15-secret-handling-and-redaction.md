# Secret Handling And Redaction Rules

Week 4, Day 2 turns the security guidance into a small enforced boundary.

The goal is to reduce accidental credential exposure in logs, assistant questions, API responses, and optional LLM requests. Redaction is a backup control. Sensitive values should still be kept out of logs and prompts at the source.

## Secret Handling Rules

- Keep real values in local environment variables or a secret manager, never in tracked files.
- Keep `.env` and `infra/k8s/secret.local.yaml` local and ignored by git.
- Commit example names and fake placeholders only.
- Do not print secrets while debugging configuration.
- Do not put credentials in URLs, screenshots, incident reports, test fixtures, or shell history.
- Rotate a credential immediately if it is committed, logged, pasted, or shared. Redacting it later does not make the old value safe.
- Use `LLM_PROVIDER=none` when external model access is not needed.

Safe example:

```text
OPENAI_API_KEY=[REDACTED]
Authorization: Bearer [REDACTED]
```

Unsafe example:

```text
OPENAI_API_KEY=<real value>
Authorization: Bearer <real token>
```

The angle-bracket values above are descriptions, not values to copy into configuration.

## Enforced Redaction Boundary

The assistant applies the same reusable redactor in several places:

```text
log file -> parse and redact -> rule-based analysis -> API response
                                      |
                                      +-> redact again -> LLM request -> redact generated text
```

Questions submitted to `POST /ask` are redacted before analysis and before they are echoed in the response. Metrics analysis and incident responses pass through the same final response redaction step.

The redactor preserves field names and replaces sensitive values with `[REDACTED]`. It handles:

- sensitive fields such as `authorization`, `api_key`, `password`, `client_secret`, cookies, credentials, and token fields.
- snake_case, kebab-case, and camelCase field names.
- bearer and basic authorization values in free text.
- common OpenAI, GitHub, AWS access-key, and JWT-shaped token patterns.
- credential assignments such as `password=value` and `api_key: value`.
- nested dictionaries, lists, parsed log fields, raw log text, assistant questions, and generated LLM text.

The optional provider credential is used only in the outbound HTTP authorization header. It is not added to the prompt.

## LLM Provider Rules

Rule-based analysis remains the safest default because it does not send logs to a model provider.

Before enabling an external provider:

- review the log fields and retention policy.
- verify that the data is allowed to leave the environment.
- review the provider's current data handling and retention terms.
- send the minimum useful number of log lines with `LLM_MAX_LOG_ENTRIES`.
- use a scoped, rotatable credential.
- treat `[REDACTED]` as a signal that context was intentionally removed; do not ask the model to reconstruct it.

## What Redaction Does Not Guarantee

This is a focused pattern-based control, not a complete data loss prevention system.

It may miss unknown credential formats, secrets split across fields, encoded values, private operational data, or organization-specific identifiers. It may also hide a non-secret value that happens to look like a token.

Redaction does not:

- remove secrets from historical logs, git history, terminal history, or provider records.
- encrypt data at rest or in transit.
- replace authentication, authorization, least privilege, retention controls, or secret rotation.
- make arbitrary production logs safe to share.
- detect every form of personal or regulated data.

Prevent sensitive logging at the source, keep the rule-based path available, and review data before sharing it externally.

## Synthetic Secrets In The Evaluation Corpus

The deterministic evaluation suite needs real provider token shapes, such as JWT-, AWS access-key-, GitHub-token-, and Bearer-token-shaped values, so its redaction module has something real to catch. See [Assistant Evaluation Basics](17-assistant-evaluation.md) for the redaction cases.

`apps/ai-sre-assistant/evals/synthetic_secrets.py` assembles the JWT, AWS-style key, and GitHub-style token values from split literal fragments at test time, so no committed file contains one of these shapes as a contiguous string. `apps/ai-sre-assistant/evals/fixtures/` also contains a small number of low-entropy, non-standard-length fixture secrets (for example `secret-in-evidence.log`) that are fabricated in the same spirit.

None of these values are ever real credentials. A pattern- or shape-based secret scanner cannot always tell a synthetic redaction fixture from a leaked credential, so an automated scan of this repository may still flag one. `.gitguardian.yaml` at the repository root records that `evals/fixtures/` is expected to contain synthetic secrets and is not an incident.

## Verification

Focused tests cover:

- nested sensitive fields and free-text token patterns.
- parsed JSON logs and malformed raw log lines.
- redacted questions and evidence in API responses.
- every input used to build an LLM prompt.
- generated LLM text before it is returned.

Run them with:

```bash
cd apps/ai-sre-assistant
python -m pytest -q
```

See `07-security.md` for the broader threat model, `16-cost-optimization.md` for prompt budget controls, and `../SECURITY.md` for vulnerability reporting.
