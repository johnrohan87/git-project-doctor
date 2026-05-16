from __future__ import annotations

from pathlib import Path

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".cache",
    "coverage",
    "reports",
}

DEFAULT_OUTPUT_DIR = Path("reports")

TODO_TAGS = ("TODO", "FIXME", "BUG", "HACK", "REVIEW")

TEXT_FILE_SUFFIXES = {
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
