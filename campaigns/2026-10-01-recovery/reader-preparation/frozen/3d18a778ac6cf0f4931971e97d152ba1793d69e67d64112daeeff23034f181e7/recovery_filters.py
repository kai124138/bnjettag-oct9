# Pure metadata/log filters copied exactly from recover.py; no cluster/model code.

import re

import json

SECRET_KEY = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|client[_-]?secret|secret)$")

QUOTED_OR_TOKEN = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;]+)'''

def redact_text(text):
    # Consume authorization schemes and their values before generic key/value rules.
    text = re.sub(r'''(?i)(["']?authorization["']?\s*[=:]\s*)(?:(?:Bearer|Basic)\s+[^\s,;]+|'''
                  + QUOTED_OR_TOKEN + ")", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
    text = re.sub(r'''(?i)(["']?(?:[A-Za-z0-9_-]*api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret|secret)["']?\s*[=:]\s*)'''
                  + QUOTED_OR_TOKEN, r"\1[REDACTED]", text)
    text = re.sub(r"\b(?:wandb_v1_|sk-|ghp_|github_pat_)[A-Za-z0-9_-]+", "[REDACTED]", text)
    return re.sub(r"\b[0-9a-fA-F]{40}\b", "[REDACTED_40_HEX]", text)

def sanitize_json(value):
    """Walk objects before serializing, so redaction cannot invalidate JSON syntax."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SECRET_KEY.search(key) else sanitize_json(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    return redact_text(value) if isinstance(value, str) else value

def credential_json(value):
    if isinstance(value, dict):
        return any(SECRET_KEY.search(key) or credential_json(item) for key, item in value.items())
    if isinstance(value, list):
        return any(credential_json(item) for item in value)
    return isinstance(value, str) and redact_text(value) != value

def redact(text):
    # Logs are sanitized derivatives. These rules are not a universal secret detector.
    try:
        value = json.loads(text)
    except ValueError:
        return redact_text(text)
    sanitized = sanitize_json(value)
    return json.dumps(sanitized) if sanitized != value else text

def cache_identity(info, expected):
    failures = []
    if info.get("array_sha256") != expected["expected_array_sha256"]:
        failures.append("array_sha256_missing_or_mismatched")
    for key in ("n_train", "n_val", "pt_gate_gev"):
        if "expected_" + key in expected and info.get(key) != expected["expected_" + key]:
            failures.append(key + "_missing_or_mismatched")
    if "expected_cache_code_sha256" in expected and info.get("code_sha256") != expected["expected_cache_code_sha256"]:
        failures.append("cache_code_sha256_missing_or_mismatched")
    return {"status": "metadata_matches_historical_expectations" if not failures else "identity_unavailable_or_mismatched",
            "failures": failures, "limitation": "metadata comparison only; actual array bytes are not rehashed"}
