from __future__ import annotations

import json
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
from project_doctor.reporters.json_reporter import write_json_reports


def _report() -> ProjectReport:
    return ProjectReport(
        summary=RepoSummary(path=Path("/tmp/example"), name="example", detected_stack=["Python package"]),
        git=GitStatus(is_git_repo=True, branch="main"),
        dependencies=DependencyReport(files_found=["pyproject.toml"]),
        docs=DocsReport(has_readme=True, has_env_example=False, notes=[".env.example is missing"]),
        todos=[
            TodoItem(file="src/app.py", line=4, tag="TODO", text="TODO: wire app", category="source"),
            TodoItem(file="docs/notes.md", line=2, tag="FIXME", text="FIXME: docs", category="documentation", priority="low"),
        ],
        secrets=[
            SecretFinding(
                file=".env",
                line=1,
                key="API_KEY",
                redacted_text="API_KEY=...REDACTED",
            )
        ],
        structure=StructureReport(project_types=["Python package"]),
    )


def test_write_json_reports_includes_docs_and_redacted_secrets(tmp_path):
    write_json_reports(_report(), tmp_path)

    docs = json.loads((tmp_path / "docs_report.json").read_text(encoding="utf-8"))
    secrets = json.loads((tmp_path / "secrets_report.json").read_text(encoding="utf-8"))
    findings_summary = json.loads((tmp_path / "findings_summary.json").read_text(encoding="utf-8"))

    assert docs["has_readme"] is True
    assert docs["notes"] == [".env.example is missing"]
    assert secrets == [
        {
            "file": ".env",
            "key": "API_KEY",
            "line": 1,
            "reason": "secret-like assignment",
            "redacted_text": "API_KEY=...REDACTED",
            "severity": "medium",
        }
    ]
    assert findings_summary["todos"]["total"] == 2
    assert findings_summary["todos"]["by_category"] == {"documentation": 1, "source": 1}
    assert findings_summary["possible_secrets"]["total"] == 1
    assert findings_summary["possible_secrets"]["by_severity"] == {"medium": 1}
    assert findings_summary["possible_secrets"]["top_files"] == [{"count": 1, "file": ".env"}]
    assert findings_summary["top_risks"][0]["risk"] == "Possible secret in .env:1"
    assert findings_summary["top_risks"][0]["confidence"] == "medium"
    assert findings_summary["top_risks"][0]["false_positive_hint"]
    assert findings_summary["top_next_actions"]
