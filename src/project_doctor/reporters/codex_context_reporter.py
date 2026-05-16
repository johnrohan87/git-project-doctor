from __future__ import annotations

from pathlib import Path

from project_doctor.models import ProjectReport


def render_codex_context(report: ProjectReport) -> str:
    scripts = report.dependencies.scripts
    script_lines = [f"- `{name}`: `{command}`" for name, command in scripts.items()]
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
            f"- Detected stack: {', '.join(report.summary.detected_stack) or 'Unknown'}",
            f"- Health score: {report.summary.health_score} / 100",
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
            "\n".join(f"{idx}. {step}" for idx, step in enumerate(report.summary.recommended_next_steps, start=1)),
            "",
        ]
    )


def write_codex_context(report: ProjectReport, out_dir: Path) -> None:
    (out_dir / "codex_context.md").write_text(render_codex_context(report), encoding="utf-8")
