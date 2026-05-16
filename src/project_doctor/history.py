from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from project_doctor.models import ProjectReport, ScanHistoryEntry


def default_history_dir() -> Path:
    return Path.home() / ".local" / "share" / "git-project-doctor" / "history"


def repo_hash(repo_path: Path) -> str:
    normalized = str(repo_path.expanduser().resolve())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def history_file_for_repo(repo_path: Path, history_dir: Path | None = None) -> Path:
    root = history_dir.expanduser().resolve() if history_dir else default_history_dir()
    return root / f"{repo_hash(repo_path)}.jsonl"


def build_history_entry(report: ProjectReport) -> ScanHistoryEntry:
    return ScanHistoryEntry(
        scanned_at=datetime.now(UTC).isoformat(timespec="seconds"),
        repo_path=str(report.summary.path),
        repo_hash=repo_hash(report.summary.path),
        repo_name=report.summary.name,
        branch=report.git.branch,
        is_git_repo=report.git.is_git_repo,
        dirty=report.git.dirty,
        health_score=report.summary.health_score,
        documentation_score=report.docs.documentation_score,
        detected_stack=report.summary.detected_stack,
        todo_count=len(report.todos),
        possible_secret_count=len(report.secrets),
        dependency_file_count=len(report.dependencies.files_found),
        test_command_count=len(report.test_ci.test_commands),
        ci_workflow_count=len(report.test_ci.ci_workflows),
        recommended_next_steps=report.summary.recommended_next_steps,
    )


def write_history_entry(report: ProjectReport, history_dir: Path | None = None) -> Path:
    entry = build_history_entry(report)
    path = history_file_for_repo(report.summary.path, history_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), sort_keys=True))
        handle.write("\n")
    return path


def load_history(repo_path: Path, history_dir: Path | None = None) -> list[ScanHistoryEntry]:
    path = history_file_for_repo(repo_path, history_dir)
    if not path.exists():
        return []

    entries: list[ScanHistoryEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(ScanHistoryEntry.model_validate_json(line))
        except ValueError:
            continue
    return entries
