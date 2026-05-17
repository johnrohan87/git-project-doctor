from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from project_doctor.models import ProjectReport, SecretFinding, TodoItem

_SECRET_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
_TODO_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _counter_dict(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _top_files(items: Iterable[TodoItem | SecretFinding], limit: int = 10) -> list[dict[str, int | str]]:
    counts = Counter(item.file for item in items)
    return [{"file": file, "count": count} for file, count in counts.most_common(limit)]


def confidence_for_secret(item: SecretFinding) -> str:
    if item.severity == "high":
        return "high"
    if item.severity == "low":
        return "low"
    return "medium"


def false_positive_hint_for_secret(item: SecretFinding) -> str:
    if item.severity == "low":
        return "Likely false positive if this is documentation, a cache/path setting, or a URL template."
    if item.severity == "medium":
        return "Could be a code reference or config lookup; confirm the value is a real credential before rotating."
    return "Less likely to be noise in config/env files; verify and rotate if real."


def confidence_for_todo(item: TodoItem) -> str:
    if item.priority == "high":
        return "high"
    if item.priority == "low":
        return "low"
    return "medium"


def false_positive_hint_for_todo(item: TodoItem) -> str:
    if item.priority == "low":
        return "Likely informational if this is in docs, generated output, fixtures, or historical notes."
    if item.category in {"backlog", "documentation"}:
        return "May be planning noise; prioritize only if it blocks active work."
    if item.priority == "high":
        return "Less likely to be noise because it is a BUG/FIXME marker outside low-signal paths."
    return "Review when the referenced area is part of current work."


def build_top_risks(report: ProjectReport, limit: int = 5) -> list[dict[str, str]]:
    risks: list[dict[str, str | int]] = []

    for item in sorted(
        report.secrets,
        key=lambda finding: (_SECRET_SEVERITY_RANK.get(finding.severity, 1), finding.file, finding.line),
    ):
        rank = _SECRET_SEVERITY_RANK.get(item.severity, 1)
        risks.append(
            {
                "sort": rank,
                "risk": f"Possible secret in {item.file}:{item.line}",
                "evidence": f"{item.key} ({item.severity}; {item.reason})",
                "next_action": "Verify whether the value is a real credential; rotate/remove it if exposed.",
                "confidence": confidence_for_secret(item),
                "false_positive_hint": false_positive_hint_for_secret(item),
            }
        )

    for item in sorted(
        report.todos,
        key=lambda todo: (_TODO_PRIORITY_RANK.get(todo.priority, 1), todo.file, todo.line),
    ):
        rank = _TODO_PRIORITY_RANK.get(item.priority, 1) + 3
        risks.append(
            {
                "sort": rank,
                "risk": f"{item.tag} in {item.file}:{item.line}",
                "evidence": f"{item.priority}/{item.category}; {item.reason}",
                "next_action": "Decide whether to fix, defer with owner/context, or remove stale marker.",
                "confidence": confidence_for_todo(item),
                "false_positive_hint": false_positive_hint_for_todo(item),
            }
        )

    if report.git.dirty:
        risks.append(
            {
                "sort": 6,
                "risk": "Dirty working tree",
                "evidence": f"{len(report.git.modified_files)} modified, {len(report.git.untracked_files)} untracked",
                "next_action": "Review local changes before starting update work.",
                "confidence": "high",
                "false_positive_hint": "Expected if the scan is intentionally run during active development.",
            }
        )
    if not report.test_ci.test_commands:
        risks.append(
            {
                "sort": 7,
                "risk": "No clear test command detected",
                "evidence": "test_ci.test_commands is empty",
                "next_action": "Document or add the local command maintainers should run first.",
                "confidence": "medium",
                "false_positive_hint": "May be false positive for projects with external or manual validation only.",
            }
        )
    if not report.docs.has_readme:
        risks.append(
            {
                "sort": 8,
                "risk": "README.md missing",
                "evidence": "docs.has_readme is false",
                "next_action": "Add setup, usage, and validation instructions.",
                "confidence": "high",
                "false_positive_hint": "May be acceptable for private scratch or generated repos.",
            }
        )

    rendered = []
    for item in sorted(risks, key=lambda risk: (int(risk["sort"]), str(risk["risk"])))[:limit]:
        rendered.append({key: str(value) for key, value in item.items() if key != "sort"})
    return rendered


def build_top_next_actions(report: ProjectReport, limit: int = 5) -> list[str]:
    if report.summary.recommended_next_steps:
        return report.summary.recommended_next_steps[:limit]
    return ["No urgent Phase 1 issues detected; keep reports current before the next update cycle."]


def build_findings_summary(report: ProjectReport) -> dict:
    return {
        "top_risks": build_top_risks(report),
        "top_next_actions": build_top_next_actions(report),
        "todos": {
            "total": len(report.todos),
            "by_category": _counter_dict(item.category for item in report.todos),
            "by_priority": _counter_dict(item.priority for item in report.todos),
            "by_tag": _counter_dict(item.tag for item in report.todos),
            "top_files": _top_files(report.todos),
        },
        "possible_secrets": {
            "total": len(report.secrets),
            "by_severity": _counter_dict(item.severity for item in report.secrets),
            "by_reason": _counter_dict(item.reason for item in report.secrets),
            "top_files": _top_files(report.secrets),
        },
    }


def render_summary_items(items: dict[str, int]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {name}: {count}" for name, count in items.items())


def render_top_files(items: list[dict[str, int | str]]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- `{item['file']}`: {item['count']}" for item in items)
