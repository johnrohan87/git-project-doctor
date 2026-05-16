from __future__ import annotations

from pathlib import Path

from project_doctor.models import ProjectReport


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _list(items: list[str], empty: str = "None detected") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def render_project_report(report: ProjectReport) -> str:
    deps_found = report.dependencies.files_found + report.dependencies.package_manager_locks
    todo_lines = [
        f"- `{item.file}:{item.line}` [{item.tag}] {item.text}"
        for item in report.todos[:50]
    ]
    secret_lines = [
        f"- `{item.file}:{item.line}` `{item.key}` {item.redacted_text}"
        for item in report.secrets[:50]
    ]

    return "\n".join(
        [
            "# Project Doctor Report",
            "",
            "## Repo Summary",
            "",
            f"- Path: `{report.summary.path}`",
            f"- Detected project type: {', '.join(report.structure.project_types) or 'Unknown'}",
            f"- Git branch: {report.git.branch or 'Unknown'}",
            f"- Dirty working tree: {_yes_no(report.git.dirty)}",
            f"- Remote origin: {report.git.remote_origin or 'None detected'}",
            "",
            "## Health Score",
            "",
            f"Overall: {report.summary.health_score} / 100",
            "",
            "## Git Status",
            "",
            f"- Is Git repo: {_yes_no(report.git.is_git_repo)}",
            f"- Modified files: {len(report.git.modified_files)}",
            f"- Untracked files: {len(report.git.untracked_files)}",
            f"- Last commit: {report.git.last_commit or 'Unknown'}",
            "",
            "## Documentation Review",
            "",
            f"- README.md: {_yes_no(report.docs.has_readme)}",
            f"- .env.example: {_yes_no(report.docs.has_env_example)}",
            f"- CHANGELOG.md: {_yes_no(report.docs.has_changelog)}",
            f"- LICENSE: {_yes_no(report.docs.has_license)}",
            f"- docs/ folder: {_yes_no(report.docs.has_docs_folder)}",
            f"- Setup keywords: {', '.join(report.docs.setup_keywords_found) or 'None detected'}",
            f"- Commands documented: {_yes_no(report.docs.documents_package_scripts_or_commands)}",
            "",
            "## Dependency Files Found",
            "",
            _list(deps_found),
            "",
            "## TODO / FIXME Items",
            "",
            "\n".join(todo_lines) if todo_lines else "- None detected",
            "",
            "## Possible Secrets",
            "",
            "\n".join(secret_lines) if secret_lines else "- None detected",
            "",
            "## Project Structure",
            "",
            "Important folders:",
            _list(report.structure.important_folders),
            "",
            "Important files:",
            _list(report.structure.important_files),
            "",
            "## Recommended Next Steps",
            "",
            "\n".join(f"{idx}. {step}" for idx, step in enumerate(report.summary.recommended_next_steps, start=1)),
            "",
        ]
    )


def render_repo_summary(report: ProjectReport) -> str:
    return "\n".join(
        [
            "# Repo Summary",
            "",
            f"- Name: {report.summary.name}",
            f"- Path: `{report.summary.path}`",
            f"- Stack: {', '.join(report.summary.detected_stack) or 'Unknown'}",
            f"- Health score: {report.summary.health_score} / 100",
            f"- Git dirty: {_yes_no(report.git.dirty)}",
            f"- TODO/FIXME count: {len(report.todos)}",
            f"- Possible secret warnings: {len(report.secrets)}",
            "",
            "## Recommended Next Steps",
            "",
            "\n".join(f"{idx}. {step}" for idx, step in enumerate(report.summary.recommended_next_steps, start=1)),
            "",
        ]
    )


def write_markdown_reports(report: ProjectReport, out_dir: Path) -> None:
    (out_dir / "project_report.md").write_text(render_project_report(report), encoding="utf-8")
    (out_dir / "repo_summary.md").write_text(render_repo_summary(report), encoding="utf-8")
