from __future__ import annotations

import re
from pathlib import Path

from project_doctor.config import TODO_TAGS
from project_doctor.models import TodoItem
from project_doctor.utils.file_utils import is_probably_text, iter_files, read_text_safely
from project_doctor.utils.path_utils import relative_to_repo

TAG_RE = re.compile(r"\b(" + "|".join(TODO_TAGS) + r")\b", re.IGNORECASE)
HISTORICAL_DOC_MARKERS = (
    "changelog",
    "retrospective",
    "super-productivity",
)
BACKLOG_DOC_MARKERS = (
    "auth-lanes",
    "backlog",
    "build-runbook",
    "checklist",
    "current-status",
    "known-issues",
    "migration",
    "next-steps",
    "readiness",
    "todo",
    "transfer-status",
)


def _classify_todo(relative_path: str, tag: str) -> tuple[str, str, str]:
    path_lower = relative_path.lower()
    tag_upper = tag.upper()

    is_doc = path_lower.startswith("docs/") or path_lower.endswith((".md", ".txt"))

    if path_lower.startswith(
        (
            "tmp/",
            "fixtures/",
            "exports/",
            "archived results/",
        )
    ):
        category = "generated"
        priority = "low"
        reason = "fixture, package, or temporary artifact"
    elif is_doc and any(marker in path_lower for marker in HISTORICAL_DOC_MARKERS):
        category = "historical"
        priority = "low"
        reason = "historical documentation or work log"
    elif is_doc and any(marker in path_lower for marker in BACKLOG_DOC_MARKERS):
        category = "backlog"
        priority = "medium"
        reason = "active backlog or planning document"
    elif is_doc:
        category = "documentation"
        priority = "low"
        reason = "documentation note or backlog reference"
    elif "/test" in path_lower or path_lower.startswith("test") or path_lower.startswith("tests/"):
        category = "test"
        priority = "medium"
        reason = "test coverage or validation follow-up"
    elif path_lower.startswith("scripts/"):
        category = "script"
        priority = "medium"
        reason = "automation script follow-up"
    elif path_lower.startswith(("src/", "app/", "server/", "components/", "pages/")):
        category = "source"
        priority = "medium"
        reason = "source code follow-up"
    else:
        category = "other"
        priority = "medium"
        reason = "general follow-up"

    if tag_upper in {"BUG", "FIXME"}:
        if category in {"generated", "historical"}:
            priority = "low"
        elif category in {"documentation", "backlog"}:
            priority = "medium"
        else:
            priority = "high"
        reason = f"{category} defect marker"
    elif tag_upper == "HACK":
        priority = "medium"
        reason = f"{category} workaround marker"
    elif tag_upper == "REVIEW":
        priority = "medium"
        reason = f"{category} review marker"

    return category, priority, reason


def scan_todos(repo_path: Path) -> list[TodoItem]:
    items: list[TodoItem] = []
    for path in iter_files(repo_path):
        if not is_probably_text(path):
            continue
        for line_number, line in enumerate(read_text_safely(path).splitlines(), start=1):
            match = TAG_RE.search(line)
            if match:
                relative_path = relative_to_repo(path, repo_path)
                tag = match.group(1).upper()
                category, priority, reason = _classify_todo(relative_path, tag)
                items.append(
                    TodoItem(
                        file=relative_path,
                        line=line_number,
                        tag=tag,
                        text=line.strip()[:300],
                        category=category,
                        priority=priority,
                        reason=reason,
                    )
                )
    return items
