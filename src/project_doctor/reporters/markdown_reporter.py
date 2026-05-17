from __future__ import annotations

from pathlib import Path

from project_doctor.models import ProjectReport
from project_doctor.reporters.finding_summary import build_findings_summary, render_summary_items, render_top_files


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _list(items: list[str], empty: str = "None detected") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def render_project_report(report: ProjectReport) -> str:
    deps_found = report.dependencies.files_found + report.dependencies.package_manager_locks
    todo_lines = [
        f"- `{item.file}:{item.line}` [{item.tag}] [{item.priority}/{item.category}] {item.reason}: {item.text}"
        for item in report.todos[:50]
    ]
    secret_lines = [
        f"- `{item.file}:{item.line}` `{item.key}` [{item.severity}] {item.reason}: {item.redacted_text}"
        for item in report.secrets[:50]
    ]
    findings_summary = build_findings_summary(report)
    script_lines = [
        f"- `{name}`: `{command}`"
        for name, command in report.test_ci.package_script_commands.items()
    ]

    return "\n".join(
        [
            "# Project Doctor Report",
            "",
            "## Repo Summary",
            "",
            f"- Path: `{report.summary.path}`",
            f"- Profile: {report.summary.profile or 'default'}",
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
            f"- Documentation score: {report.docs.documentation_score} / 100",
            f"- README line count: {report.docs.readme_line_count}",
            f"- Setup keywords: {', '.join(report.docs.setup_keywords_found) or 'None detected'}",
            f"- Commands documented: {_yes_no(report.docs.documents_package_scripts_or_commands)}",
            f"- README sections: {', '.join(report.docs.readme_sections) or 'None detected'}",
            f"- Missing recommended sections: {', '.join(report.docs.missing_recommended_sections) or 'None detected'}",
            "",
            "## Dependency Files Found",
            "",
            _list(deps_found),
            "",
            "## Test and CI Detection",
            "",
            "Test runners:",
            _list(report.test_ci.test_runners),
            "",
            "Recommended test commands:",
            _list(report.test_ci.test_commands),
            "",
            "Package test/check scripts:",
            "\n".join(script_lines) if script_lines else "- None detected",
            "",
            "CI workflows:",
            _list(report.test_ci.ci_workflows),
            "",
            "Docker files:",
            _list(report.test_ci.docker_files),
            "",
            "## TODO / FIXME Items",
            "",
            f"Total: {findings_summary['todos']['total']}",
            "",
            "By category:",
            render_summary_items(findings_summary["todos"]["by_category"]),
            "",
            "By priority:",
            render_summary_items(findings_summary["todos"]["by_priority"]),
            "",
            "Top files:",
            render_top_files(findings_summary["todos"]["top_files"]),
            "",
            "Details:",
            "\n".join(todo_lines) if todo_lines else "- None detected",
            "",
            "## Possible Secrets",
            "",
            f"Total: {findings_summary['possible_secrets']['total']}",
            "",
            "By severity:",
            render_summary_items(findings_summary["possible_secrets"]["by_severity"]),
            "",
            "Top files:",
            render_top_files(findings_summary["possible_secrets"]["top_files"]),
            "",
            "Details:",
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
            f"- Profile: {report.summary.profile or 'default'}",
            f"- Stack: {', '.join(report.summary.detected_stack) or 'Unknown'}",
            f"- Health score: {report.summary.health_score} / 100",
            f"- Git dirty: {_yes_no(report.git.dirty)}",
            f"- TODO/FIXME count: {len(report.todos)}",
            f"- Possible secret warnings: {len(report.secrets)}",
            f"- Test commands detected: {len(report.test_ci.test_commands)}",
            f"- CI workflows detected: {len(report.test_ci.ci_workflows)}",
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
