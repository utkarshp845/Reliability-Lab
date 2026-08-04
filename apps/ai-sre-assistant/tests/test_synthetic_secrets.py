import json

from app.redaction import REDACTED, redact_text
from evals.synthetic_secrets import (
    SYNTHETIC_FIXTURES,
    github_token_and_credential_case,
    jwt_and_aws_key_case,
)


def test_jwt_and_aws_key_case_shapes_match_redaction_patterns():
    line, secrets = jwt_and_aws_key_case()
    entry = json.loads(line)

    jwt, aws_key = secrets
    assert jwt.count(".") == 2
    assert jwt.startswith("eyJ")
    assert aws_key.startswith(("AKIA", "ASIA"))
    assert len(aws_key) == 20
    assert jwt in entry["message"]
    assert aws_key in entry["message"]


def test_github_token_and_credential_case_shapes_match_redaction_patterns():
    line, secrets = github_token_and_credential_case()
    entry = json.loads(line)

    token, password = secrets
    assert token.startswith("ghp_")
    assert len(token) - len("ghp_") >= 20
    assert token in entry["message"]
    assert password in entry["message"]


def test_synthetic_fixtures_are_fully_redacted():
    for builder in SYNTHETIC_FIXTURES.values():
        line, secrets = builder()
        entry = json.loads(line)

        redacted_message = redact_text(entry["message"])

        assert REDACTED in redacted_message
        for secret in secrets:
            assert secret not in redacted_message
