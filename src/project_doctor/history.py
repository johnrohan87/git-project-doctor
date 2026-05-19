from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from project_doctor.models import ProjectReport, ScanHistoryDelta, ScanHistoryEntry


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
        repo_hash=repo_hash(report.summary.path),
        repo_name=report.summary.name,
        profile=report.summary.profile,
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
        handle.write(json.dumps(entry.model_dump(mode="json", exclude_none=True), sort_keys=True))
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


def compare_history_entries(previous: ScanHistoryEntry, current: ScanHistoryEntry) -> ScanHistoryDelta:
    previous_stack = set(previous.detected_stack)
    current_stack = set(current.detected_stack)
    previous_steps = set(previous.recommended_next_steps)
    current_steps = set(current.recommended_next_steps)

    return ScanHistoryDelta(
        previous_scanned_at=previous.scanned_at,
        current_scanned_at=current.scanned_at,
        health_score_delta=current.health_score - previous.health_score,
        documentation_score_delta=current.documentation_score - previous.documentation_score,
        todo_count_delta=current.todo_count - previous.todo_count,
        possible_secret_count_delta=current.possible_secret_count - previous.possible_secret_count,
        dependency_file_count_delta=current.dependency_file_count - previous.dependency_file_count,
        test_command_count_delta=current.test_command_count - previous.test_command_count,
        ci_workflow_count_delta=current.ci_workflow_count - previous.ci_workflow_count,
        profile_changed=current.profile != previous.profile,
        dirty_changed=current.dirty != previous.dirty,
        branch_changed=current.branch != previous.branch,
        stack_added=sorted(current_stack - previous_stack),
        stack_removed=sorted(previous_stack - current_stack),
        new_recommended_next_steps=sorted(current_steps - previous_steps),
        resolved_recommended_next_steps=sorted(previous_steps - current_steps),
    )


def latest_history_delta(entries: list[ScanHistoryEntry]) -> ScanHistoryDelta | None:
    if len(entries) < 2:
        return None
    return compare_history_entries(entries[-2], entries[-1])
