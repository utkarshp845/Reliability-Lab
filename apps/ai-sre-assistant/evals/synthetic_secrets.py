"""Synthetic, non-functional secret-shaped values for redaction eval cases.

These exist so the deterministic redaction module has real provider token
shapes to catch: a JWT, an AWS-style access key, and a GitHub-style personal
access token. Every value is assembled from split literal fragments so no
committed file ever contains one contiguous string that matches a provider's
token format. A pattern-based secret scanner reads committed source text; it
cannot see a value that only exists once these fragments are joined at
import or call time.

None of these values are ever real credentials. See the "Synthetic Secrets
In The Evaluation Corpus" section of docs/15-secret-handling-and-redaction.md.
"""

import json
from collections.abc import Callable
from typing import Any


def _jwt() -> str:
    header = "eyJhbGciOiJFVkFMIn0"
    payload = "eyJmaXh0dXJlIjoibm90LXJlYWwifQ"
    signature = "ZXZhbC1maXh0dXJlLXNpZ25hdHVyZQ"
    return f"{header}.{payload}.{signature}"


def _aws_style_key() -> str:
    prefix = "AKIA"
    body = "EVALTESTFIXTURE1"
    return prefix + body


def _github_style_token() -> str:
    prefix = "ghp_"
    body = "EVALFIXTURETOKENNOTREALDONOTUSE12"
    return prefix + body


def _inline_password() -> str:
    words = ("eval", "fixture", "not", "a", "real", "secret")
    return "-".join(words)


def _log_line(fields: dict[str, Any]) -> str:
    return json.dumps(fields)


def jwt_and_aws_key_case() -> tuple[str, list[str]]:
    """Return a synthetic log line and the secrets it must redact."""
    jwt = _jwt()
    aws_key = _aws_style_key()
    message = f"token {jwt} rejected; leaked key {aws_key} found in config"
    line = _log_line(
        {
            "level": "ERROR",
            "event": "auth_failed",
            "message": message,
            "path": "/api/auth",
            "status_code": 500,
        }
    )
    return line, [jwt, aws_key]


def github_token_and_credential_case() -> tuple[str, list[str]]:
    """Return a synthetic log line and the secrets it must redact."""
    token = _github_style_token()
    password = _inline_password()
    message = f"webhook auth failed with {token} and password={password}"
    line = _log_line(
        {
            "level": "ERROR",
            "event": "webhook_failed",
            "message": message,
            "path": "/api/webhooks",
            "status_code": 500,
        }
    )
    return line, [token, password]


SYNTHETIC_FIXTURES: dict[str, Callable[[], tuple[str, list[str]]]] = {
    "jwt_and_aws_key": jwt_and_aws_key_case,
    "github_token_and_credential": github_token_and_credential_case,
}
