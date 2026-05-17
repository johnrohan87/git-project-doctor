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
    TestCiReport as ProjectTestCiReport,
    TodoItem,
)
from project_doctor.reporters.codex_context_reporter import render_codex_context
from project_doctor.reporters.markdown_reporter import render_project_report, render_repo_summary


def _report() -> ProjectReport:
    return ProjectReport(
        summary=RepoSummary(
            path=Path("/tmp/example"),
            name="example",
            detected_stack=["Python package"],
            health_score=62,
            recommended_next_steps=[
                "Review 1 possible secret findings and rotate any exposed credentials",
                "Review 1 TODO/FIXME/HACK/BUG/REVIEW comments",
                "Document or add a clear test command",
            ],
        ),
        git=GitStatus(is_git_repo=True, branch="main", dirty=True, modified_files=["src/app.py"]),
        dependencies=DependencyReport(files_found=["pyproject.toml"]),
        docs=DocsReport(has_readme=True, has_env_example=False, documentation_score=70),
        todos=[
            TodoItem(
                file="src/app.py",
                line=10,
                tag="FIXME",
                text="# FIXME: handle retry failure",
                category="source",
                priority="high",
                reason="source defect marker",
            )
        ],
        secrets=[
            SecretFinding(
                file=".env",
                line=1,
                key="API_KEY",
                redacted_text="API_KEY=...REDACTED",
                severity="high",
                reason="secret-like configuration value",
            )
        ],
        structure=StructureReport(project_types=["Python package"]),
        test_ci=ProjectTestCiReport(),
    )


def test_project_report_leads_with_decision_sections_and_hints() -> None:
    rendered = render_project_report(_report())

    assert rendered.index("## Top Risks") < rendered.index("## Health Score")
    assert rendered.index("## Top Next Actions") < rendered.index("## Health Score")
    assert "Possible secret in .env:1" in rendered
    assert "confidence: high" in rendered
    assert "Less likely to be noise in config/env files" in rendered
    assert "API_KEY=...REDACTED" in rendered
    assert "actual-secret-value" not in rendered


def test_repo_summary_includes_compact_risks_and_actions() -> None:
    rendered = render_repo_summary(_report())

    assert "## Top Risks" in rendered
    assert "## Top Next Actions" in rendered
    assert "Review 1 possible secret findings" in rendered
    assert "Possible secret in .env:1" in rendered


def test_codex_context_includes_decision_summary() -> None:
    rendered = render_codex_context(_report())

    assert rendered.index("## Top Risks") < rendered.index("## Important Files")
    assert "Possible secret in .env:1" in rendered
    assert "Document or add a clear test command" in rendered
