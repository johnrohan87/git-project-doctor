from __future__ import annotations

from pathlib import Path
from typing import Iterator

from project_doctor.config import IGNORED_DIRS, TEXT_FILE_SUFFIXES


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


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
