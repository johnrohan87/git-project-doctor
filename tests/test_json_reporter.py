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
)
from project_doctor.reporters.json_reporter import write_json_reports


def _report() -> ProjectReport:
    return ProjectReport(
        summary=RepoSummary(path=Path("/tmp/example"), name="example", detected_stack=["Python package"]),
        git=GitStatus(is_git_repo=True, branch="main"),
        dependencies=DependencyReport(files_found=["pyproject.toml"]),
        docs=DocsReport(has_readme=True, has_env_example=False, notes=[".env.example is missing"]),
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

    assert docs["has_readme"] is True
    assert docs["notes"] == [".env.example is missing"]
    assert secrets == [
        {
            "file": ".env",
            "key": "API_KEY",
            "line": 1,
            "redacted_text": "API_KEY=...REDACTED",
        }
    ]
