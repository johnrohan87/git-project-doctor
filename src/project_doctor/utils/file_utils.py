from __future__ import annotations

from pathlib import Path
from typing import Iterator

from project_doctor.config import IGNORED_DIRS, IGNORED_PATH_PREFIXES, TEXT_FILE_SUFFIXES


def should_ignore(path: Path) -> bool:
    parts = path.parts
    if any(part in IGNORED_DIRS for part in parts):
        return True
    for prefix in IGNORED_PATH_PREFIXES:
        prefix_length = len(prefix)
        for index in range(len(parts) - prefix_length + 1):
            if parts[index : index + prefix_length] == prefix:
                return True
    return False


def iter_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if should_ignore(path.relative_to(root)):
            continue
        if path.is_file():
            yield path


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_FILE_SUFFIXES:
        return True
    if path.name in {".env.example", ".env.sample", "Dockerfile", "Makefile"}:
        return True
    return False


def read_text_safely(path: Path, max_bytes: int = 1_000_000) -> str:
    if path.stat().st_size > max_bytes:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
