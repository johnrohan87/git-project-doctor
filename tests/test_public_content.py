from __future__ import annotations

import subprocess
from base64 import b64decode
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
BLOCKED_TERM_PAYLOADS = {
    "Y21z",
    "cG93ZXIgYXV0b21hdGU=",
    "cG93ZXJhdXRvbWF0ZQ==",
    "cGNjbA==",
    "cHJvamVjdGNvbXBsZXRpb25jaGVja2xpc3Q=",
    "c2l0ZSBwcmVwIGNvcA==",
    "c2l0ZS1wcmVwLWNvcA==",
    "dG9vbHRyYWNrZXI=",
    "ZGF0YXZlcnNl",
    "c2hhcmVwb2ludA==",
    "Y3I5MGE4Zg==",
    "Y3VycmVudC1mbG93LXBhY2thZ2Vz",
    "Y29tcGxldGVkIGZsb3cgcmVzdWx0cw==",
    "Zmxvdy10b2Rv",
    "Zmxvdy1jaGFuZ2Vsb2c=",
}


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [REPO_ROOT / line for line in result.stdout.splitlines() if line]


def _blocked_terms() -> set[str]:
    return {b64decode(value).decode("utf-8") for value in BLOCKED_TERM_PAYLOADS}


def test_public_content_does_not_include_customer_specific_notes():
    findings: list[str] = []
    blocked_terms = _blocked_terms()

    for path in _tracked_files():
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            normalized = line.lower()
            for term in blocked_terms:
                if term in normalized:
                    relative_path = path.relative_to(REPO_ROOT)
                    findings.append(f"{relative_path}:{line_number}: {term}")

    assert findings == []
