from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from project_doctor.models import ProjectDoctorConfig


DEFAULT_CONFIG_FILE = ".project-doctor.toml"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def load_project_config(repo_path: Path, config_path: Path | None = None) -> ProjectDoctorConfig:
    path = config_path.expanduser().resolve() if config_path else repo_path / DEFAULT_CONFIG_FILE
    if not path.exists():
        return ProjectDoctorConfig()

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ProjectDoctorConfig()

    raw = data.get("project_doctor", data)
    if not isinstance(raw, dict):
        return ProjectDoctorConfig()

    todos = raw.get("todos", {})
    if not isinstance(todos, dict):
        todos = {}
    secrets = raw.get("secrets", {})
    if not isinstance(secrets, dict):
        secrets = {}

    return ProjectDoctorConfig(
        profile=str(raw["profile"]) if raw.get("profile") else None,
        generated_path_prefixes=_string_list(raw.get("generated_path_prefixes"))
        + _string_list(todos.get("generated_path_prefixes")),
        historical_doc_markers=_string_list(raw.get("historical_doc_markers"))
        + _string_list(todos.get("historical_doc_markers")),
        backlog_doc_markers=_string_list(raw.get("backlog_doc_markers"))
        + _string_list(todos.get("backlog_doc_markers")),
        secret_ignored_path_prefixes=_string_list(raw.get("secret_ignored_path_prefixes"))
        + _string_list(secrets.get("ignored_path_prefixes")),
    )
