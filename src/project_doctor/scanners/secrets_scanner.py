from __future__ import annotations

import re
from pathlib import Path

from project_doctor.models import SecretFinding
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


def _redact(line: str, key: str) -> str:
    prefix = line.split(key, 1)[0] + key
    separator = "=" if "=" in line else ":"
    return f"{prefix}{separator}...REDACTED"


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("'\"").lower()
    if normalized in PLACEHOLDER_VALUES:
        return True
    return normalized.startswith(("your-", "example-", "sample-", "dummy-", "fake-"))


def scan_secrets(repo_path: Path) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for path in iter_files(repo_path):
        if not is_probably_text(path):
            continue
        for line_number, line in enumerate(read_text_safely(path).splitlines(), start=1):
            match = SECRET_RE.search(line)
            if not match:
                continue
            key = match.group("key")
            if _is_placeholder(match.group("value")):
                continue
            findings.append(
                SecretFinding(
                    file=relative_to_repo(path, repo_path),
                    line=line_number,
                    key=key,
                    redacted_text=_redact(line.strip(), key),
                )
            )
    return findings
