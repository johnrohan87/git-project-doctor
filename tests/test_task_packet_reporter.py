from __future__ import annotations

from pathlib import Path

from project_doctor.models import (
    DependencyReport,
    DocsReport,
    GitStatus,
    ProjectReport,
    RepoSummary,
    SecretFinding,
    StructureReport,
    TodoItem,
)
from project_doctor.reporters.task_packet_reporter import build_task_packets, write_task_packets


def _report() -> ProjectReport:
    return ProjectReport(
        summary=RepoSummary(
            path=Path("/tmp/example"),
            name="example",
            detected_stack=["React/Vite"],
            health_score=72,
        ),
        git=GitStatus(is_git_repo=True, branch="main"),
        dependencies=DependencyReport(scripts={"dev": "vite"}),
        docs=DocsReport(has_readme=True, has_env_example=False, documents_package_scripts_or_commands=False),
        todos=[TodoItem(file="src/app.ts", line=5, tag="TODO", text="TODO: split component")],
        secrets=[SecretFinding(file=".env", line=1, key="API_KEY", redacted_text="API_KEY=...REDACTED")],
        structure=StructureReport(project_types=["React/Vite"]),
    )


def test_build_task_packets_from_findings():
    packets = build_task_packets(_report())

    titles = [packet.title for packet in packets]
    assert "Fix README setup instructions" in titles
    assert "Add .env.example placeholders" in titles
    assert "Review TODO/FIXME comments" in titles
    assert "Review possible secret findings" in titles


def test_custom_profile_task_packets_skip_generic_package_tasks():
    report = _report()
    report.summary.detected_stack = ["Profile: custom"]
    report.todos = [
        TodoItem(file="docs/current-status.md", line=3, tag="TODO", text="TODO: finish rollout", category="backlog"),
        TodoItem(file="tmp/export.json", line=1, tag="TODO", text="TODO generated", category="generated"),
    ]
    report.secrets = [
        SecretFinding(
            file="docs/notes.md",
            line=1,
            key="TOKEN",
            redacted_text="TOKEN=...REDACTED",
            severity="low",
            reason="documentation token reference",
        )
    ]

    packets = build_task_packets(report)

    titles = [packet.title for packet in packets]
    assert "Improve custom runbook documentation" in titles
    assert "Review active custom TODO backlog" in titles
    assert "Add .env.example placeholders" not in titles
    assert "Define local test command" not in titles
    assert "Review possible secret findings" not in titles

    todo_packet = next(packet for packet in packets if packet.title == "Review active custom TODO backlog")
    assert "1 active backlog/script/source TODO findings were found." in todo_packet.context
    assert all("tmp/export.json" not in line for line in todo_packet.context)


def test_write_task_packets_redacts_secret_values(tmp_path):
    paths = write_task_packets(_report(), tmp_path)

    assert paths
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "API_KEY=...REDACTED" in combined
    assert "actual-secret" not in combined
