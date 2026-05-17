from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from project_doctor.models import ProjectReport, SecretFinding, TodoItem


def _counter_dict(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _top_files(items: Iterable[TodoItem | SecretFinding], limit: int = 10) -> list[dict[str, int | str]]:
    counts = Counter(item.file for item in items)
    return [{"file": file, "count": count} for file, count in counts.most_common(limit)]


def build_findings_summary(report: ProjectReport) -> dict:
    return {
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
