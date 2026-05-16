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


def _redact(line: str, key: str) -> str:
    prefix = line.split(key, 1)[0] + key
    separator = "=" if "=" in line else ":"
    return f"{prefix}{separator}...REDACTED"


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
            findings.append(
                SecretFinding(
                    file=relative_to_repo(path, repo_path),
                    line=line_number,
                    key=key,
                    redacted_text=_redact(line.strip(), key),
                )
            )
    return findings
