from __future__ import annotations

import hashlib
import os
import re
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

IGNORED_PATH_PREFIXES = {
    (".tools", "bin"),
    (".tools", "cache"),
    (".tools", "local-state"),
    (".tools", "tmp"),
}

APP_DIR_NAME = "git-project-doctor"
DEFAULT_OUTPUT_DIR = None


def user_data_dir() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home).expanduser()
    return Path.home() / ".local" / "share"


def repo_output_name(repo_path: Path) -> str:
    resolved = repo_path.expanduser().resolve()
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", resolved.name).strip("-") or "repo"
    repo_hash = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:12]
    return f"{safe_name}-{repo_hash}"


def default_output_dir_for_repo(repo_path: Path) -> Path:
    return user_data_dir() / APP_DIR_NAME / "reports" / repo_output_name(repo_path)

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
