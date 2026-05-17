from __future__ import annotations

from pathlib import Path

from project_doctor.models import ProjectReport
from project_doctor.reporters.finding_summary import build_findings_summary


def _numbered(items: list[str]) -> str:
    if not items:
        return "1. None detected"
    return "\n".join(f"{idx}. {item}" for idx, item in enumerate(items, start=1))


def _render_top_risks(risks: list[dict[str, str]]) -> str:
    if not risks:
        return "- No urgent Phase 1 risks detected."
    return "\n".join(
        f"- {item['risk']} | confidence: {item['confidence']} | action: {item['next_action']}"
        for item in risks
    )


def render_codex_context(report: ProjectReport) -> str:
    findings_summary = build_findings_summary(report)
    scripts = report.dependencies.scripts
    script_lines = [f"- `{name}`: `{command}`" for name, command in scripts.items()]
    test_command_lines = [f"- `{command}`" for command in report.test_ci.test_commands]
    ci_lines = [f"- `{workflow}`" for workflow in report.test_ci.ci_workflows]
    modified = [f"- {item}" for item in report.git.modified_files[:30]]
    untracked = [f"- {item}" for item in report.git.untracked_files[:30]]

    return "\n".join(
        [
            "# Codex/Cline Context",
            "",
            "## Repo Summary",
            "",
            f"- Name: {report.summary.name}",
            f"- Path: `{report.summary.path}`",
            f"- Profile: {report.summary.profile or 'default'}",
            f"- Detected stack: {', '.join(report.summary.detected_stack) or 'Unknown'}",
            f"- Health score: {report.summary.health_score} / 100",
            f"- Documentation score: {report.docs.documentation_score} / 100",
            "",
            "## Top Risks",
            "",
            _render_top_risks(findings_summary["top_risks"]),
            "",
            "## Top Next Actions",
            "",
            _numbered(findings_summary["top_next_actions"]),
            "",
            "## Important Files",
            "",
            "\n".join(f"- `{file}`" for file in report.structure.important_files) or "- None detected",
            "",
            "## Important Folders",
            "",
            "\n".join(f"- `{folder}/`" for folder in report.structure.important_folders) or "- None detected",
            "",
            "## Package Scripts",
            "",
            "\n".join(script_lines) if script_lines else "- None detected",
            "",
            "## Test and CI",
            "",
            f"- Test runners: {', '.join(report.test_ci.test_runners) or 'None detected'}",
            f"- Docker files: {', '.join(report.test_ci.docker_files) or 'None detected'}",
            "",
            "Recommended test commands:",
            "\n".join(test_command_lines) if test_command_lines else "- None detected",
            "",
            "CI workflows:",
            "\n".join(ci_lines) if ci_lines else "- None detected",
            "",
            "## Current Git Status",
            "",
            f"- Is Git repo: {report.git.is_git_repo}",
            f"- Branch: {report.git.branch or 'Unknown'}",
            f"- Dirty working tree: {report.git.dirty}",
            f"- Remote origin: {report.git.remote_origin or 'None detected'}",
            "",
            "Modified files:",
            "\n".join(modified) if modified else "- None",
            "",
            "Untracked files:",
            "\n".join(untracked) if untracked else "- None",
            "",
            "## Safety Rules For Next Coding Task",
            "",
            "- Do not commit, push, pull, reset, checkout, or merge unless explicitly requested.",
            "- Do not expose secret values.",
            "- Confirm before modifying generated reports or repository configuration.",
            "",
            "## Recommended Next Steps",
            "",
            _numbered(report.summary.recommended_next_steps),
            "",
        ]
    )


def write_codex_context(report: ProjectReport, out_dir: Path) -> None:
    (out_dir / "codex_context.md").write_text(render_codex_context(report), encoding="utf-8")
