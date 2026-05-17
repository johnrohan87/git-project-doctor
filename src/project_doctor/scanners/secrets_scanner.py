from __future__ import annotations

import re
from pathlib import Path

from project_doctor.models import ProjectDoctorConfig, SecretFinding
from project_doctor.utils.file_utils import is_probably_text, iter_files, read_text_safely
from project_doctor.utils.path_utils import relative_to_repo

SECRET_RE = re.compile(
    r"\b(?P<key>[A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)[A-Z0-9_]*)\b"
    r"\s*[:=]\s*(?P<value>['\"]?[^'\"\s#]+)",
    re.IGNORECASE,
)

PLACEHOLDER_VALUES = {
    "",
    "change-me",
    "changeme",
    "demo",
    "dummy",
    "example",
    "fake",
    "none",
    "placeholder",
    "sample",
    "test",
    "todo",
    "your-api-key",
    "your-secret",
    "your-token",
}

CACHE_OR_PATH_KEYS = (
    "cache",
    "cache_dir",
    "cache_path",
    "path",
)
CONTROL_FLAG_KEYS = (
    "force_refresh_token",
    "use_token_cache",
)
KNOWN_NON_SECRET_KEYS = {
    "monthtokens",
    "reactproptypessecret",
}
LOW_SEVERITY_SUFFIXES = (
    "_endpoint",
    "_endpoint_template",
    "_url",
)
CODE_REFERENCE_SUFFIXES = (
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".ts",
    ".tsx",
    ".rb",
    ".rs",
    ".sh",
)
DOC_SUFFIXES = (".md", ".txt")
CODE_COMMENT_PREFIXES = ("//", "#", "/*", "*")


def _redact(line: str, key: str) -> str:
    prefix = line.split(key, 1)[0] + key
    separator = "=" if "=" in line else ":"
    return f"{prefix}{separator}...REDACTED"


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("'\"").lower()
    if normalized in PLACEHOLDER_VALUES:
        return True
    return normalized.startswith(("your-", "example-", "sample-", "dummy-", "fake-"))


def _is_code_reference_false_positive(path: Path, line: str, key: str, value: str) -> bool:
    stripped = line.strip()
    key_lower = key.lower()
    value_stripped = value.strip()
    value_clean = value.strip().strip("'\"")
    suffix = path.suffix.lower()

    if key_lower in KNOWN_NON_SECRET_KEYS:
        return True
    if key_lower in CONTROL_FLAG_KEYS:
        return True
    if key_lower.endswith(LOW_SEVERITY_SUFFIXES):
        return True
    if suffix in CODE_REFERENCE_SUFFIXES and stripped.startswith(CODE_COMMENT_PREFIXES):
        return True
    if (
        suffix in CODE_REFERENCE_SUFFIXES
        and key_lower in {"secret", "token"}
        and re.search(rf"\.[ \t]*{re.escape(key)}\b\s*[:=]", stripped, re.IGNORECASE)
    ):
        return True
    if suffix in CODE_REFERENCE_SUFFIXES and re.search(rf"\bconsole\.[A-Za-z_]+\([^)]*\b{re.escape(key)}\b", stripped):
        return True
    if suffix in CODE_REFERENCE_SUFFIXES and re.search(
        rf"\b{re.escape(key)}\s*:\s*[A-Za-z_][A-Za-z0-9_\[\] |.]*[,)=]?",
        stripped,
    ):
        return True
    if re.search(rf"\b{re.escape(key)}\s*=>", stripped):
        return True
    if re.search(rf"\bfunction\s*\([^)]*\b{re.escape(key)}\b", stripped):
        return True
    if suffix in CODE_REFERENCE_SUFFIXES and not value_stripped.startswith(("'", '"')):
        if re.match(r"[A-Za-z_$][A-Za-z0-9_$.]*(?:[.(\[]|$)", value_clean):
            return True
        if value_clean.startswith(("{", "[", "(", "<", "/", ",", ")", "=>")):
            return True
    if value_clean.startswith((">", "=>")):
        return True
    return False


def _classify(path: Path, key: str) -> tuple[str, str]:
    key_lower = key.lower()
    suffix = path.suffix.lower()
    if suffix in DOC_SUFFIXES:
        return "low", "documentation example or note"
    if key_lower in CONTROL_FLAG_KEYS:
        return "low", "token-related control flag"
    if key_lower.endswith(LOW_SEVERITY_SUFFIXES):
        return "low", "endpoint or URL template reference"
    if any(token in key_lower for token in CACHE_OR_PATH_KEYS):
        return "low", "token/cache path or configuration reference"
    if suffix in CODE_REFERENCE_SUFFIXES:
        return "medium", "secret-like code assignment or configuration reference"
    if path.name.startswith(".env") or suffix in {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg"}:
        return "high", "secret-like configuration value"
    return "medium", "secret-like assignment"


def _is_config_ignored(relative_path: str, config: ProjectDoctorConfig) -> bool:
    path_lower = relative_path.lower()
    for raw_prefix in config.secret_ignored_path_prefixes:
        prefix = raw_prefix.strip().strip("/").lower()
        if not prefix:
            continue
        if path_lower == prefix or path_lower.startswith(f"{prefix}/"):
            return True
    return False


def scan_secrets(repo_path: Path, config: ProjectDoctorConfig | None = None) -> list[SecretFinding]:
    active_config = config or ProjectDoctorConfig()
    findings: list[SecretFinding] = []
    for path in iter_files(repo_path):
        relative_path = relative_to_repo(path, repo_path)
        if _is_config_ignored(relative_path, active_config):
            continue
        if not (is_probably_text(path) or path.name.startswith(".env")):
            continue
        for line_number, line in enumerate(read_text_safely(path).splitlines(), start=1):
            match = SECRET_RE.search(line)
            if not match:
                continue
            key = match.group("key")
            value = match.group("value")
            if _is_placeholder(value) or _is_code_reference_false_positive(path, line, key, value):
                continue
            severity, reason = _classify(path, key)
            findings.append(
                SecretFinding(
                    file=relative_path,
                    line=line_number,
                    key=key,
                    redacted_text=_redact(line.strip(), key),
                    severity=severity,
                    reason=reason,
                )
            )
    return findings
