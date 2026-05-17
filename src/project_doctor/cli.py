from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from project_doctor.config import DEFAULT_OUTPUT_DIR, default_output_dir_for_repo
from project_doctor.history import latest_history_delta, load_history, write_history_entry
from project_doctor.models import ProjectReport, RepoSummary
from project_doctor.models import ProjectDoctorConfig
from project_doctor.project_config import load_project_config
from project_doctor.reporters.codex_context_reporter import write_codex_context
from project_doctor.reporters.json_reporter import write_json_reports
from project_doctor.reporters.markdown_reporter import write_markdown_reports
from project_doctor.reporters.task_packet_reporter import write_task_packets
from project_doctor.scanners.dependency_scanner import scan_dependencies
from project_doctor.scanners.docs_scanner import scan_docs
from project_doctor.scanners.git_scanner import scan_git
from project_doctor.scanners.secrets_scanner import scan_secrets
from project_doctor.scanners.structure_scanner import scan_structure
from project_doctor.scanners.test_ci_scanner import scan_test_ci
from project_doctor.scanners.todo_scanner import scan_todos
from project_doctor.utils.path_utils import resolve_repo_path

app = typer.Typer(help="Local-first Git project review and update planning tool.")
console = Console()


def _recommended_next_steps(report: ProjectReport, config: ProjectDoctorConfig | None = None) -> list[str]:
    steps: list[str] = []
    if not report.docs.has_readme:
        steps.append("Add README.md with setup and usage instructions")
    elif not report.docs.setup_keywords_found or not report.docs.documents_package_scripts_or_commands:
        steps.append("Update README setup instructions and command documentation")
    if not report.docs.has_env_example:
        steps.append("Add .env.example with safe placeholder values")
    if report.todos:
        steps.append(f"Review {len(report.todos)} TODO/FIXME/HACK/BUG/REVIEW comments")
    if report.secrets:
        steps.append(f"Review {len(report.secrets)} possible secret findings and rotate any exposed credentials")
    if not report.git.is_git_repo:
        steps.append("Initialize Git or scan the repository root if this path is nested")
    elif report.git.dirty:
        steps.append("Review modified and untracked files before starting update work")
    if not report.dependencies.files_found:
        steps.append("Confirm dependency management files are present or document the project type")
    if not report.test_ci.test_commands:
        steps.append("Document or add a clear test command")
    if not report.test_ci.ci_workflows:
        steps.append("Consider adding a CI workflow after the local test command is confirmed")
    if not steps:
        steps.append("No urgent Phase 1 issues detected; consider adding deeper test and CI review in Phase 2")
    return steps


def _health_score(report: ProjectReport, config: ProjectDoctorConfig | None = None) -> int:
    score = 100
    if not report.git.is_git_repo:
        score -= 15
    if report.git.dirty:
        score -= 5
    if not report.docs.has_readme:
        score -= 20
    if not report.docs.has_env_example:
        score -= 10
    if not report.docs.documents_package_scripts_or_commands:
        score -= 10
    if not report.dependencies.files_found:
        score -= 10
    if not report.test_ci.test_commands:
        score -= 10
    if not report.test_ci.ci_workflows:
        score -= 5
    score -= min(len(report.todos), 20)
    score -= min(len(report.secrets) * 10, 30)
    return max(0, min(100, score))


def build_report(repo_path: Path, config_path: Path | None = None) -> ProjectReport:
    config = load_project_config(repo_path, config_path)
    git = scan_git(repo_path)
    dependencies = scan_dependencies(repo_path)
    docs = scan_docs(repo_path)
    todos = scan_todos(repo_path, config)
    secrets = scan_secrets(repo_path, config)
    structure = scan_structure(repo_path)
    test_ci = scan_test_ci(repo_path)

    summary = RepoSummary(
        path=repo_path,
        name=repo_path.name,
        profile=config.profile,
        detected_stack=structure.project_types,
    )
    report = ProjectReport(
        summary=summary,
        git=git,
        dependencies=dependencies,
        docs=docs,
        todos=todos,
        secrets=secrets,
        structure=structure,
        test_ci=test_ci,
    )
    report.summary.health_score = _health_score(report, config)
    report.summary.recommended_next_steps = _recommended_next_steps(report, config)
    return report


def _validate_path(path: str) -> Path:
    repo_path = resolve_repo_path(path)
    if not repo_path.exists() or not repo_path.is_dir():
        raise typer.BadParameter(f"Path does not exist or is not a directory: {repo_path}")
    return repo_path


def _resolve_output_dir(repo_path: Path, out: Path | None) -> tuple[Path, bool]:
    if out is None:
        return default_output_dir_for_repo(repo_path).expanduser().resolve(), False
    return out.expanduser().resolve(), True


def _warn_if_explicit_output_inside_repo(repo_path: Path, out_dir: Path, explicit_out: bool) -> None:
    if explicit_out and out_dir.is_relative_to(repo_path):
        console.print(
            "[yellow]Warning:[/yellow] --out points inside the scanned repository; "
            "reports may appear as Git changes."
        )


@app.command()
def scan(
    path: str = typer.Argument(..., help="Repository path to scan."),
    out: Path | None = typer.Option(DEFAULT_OUTPUT_DIR, "--out", "-o", help="Output directory for reports."),
    history: bool = typer.Option(True, "--history/--no-history", help="Record a local scan history entry."),
    history_dir: Path | None = typer.Option(None, "--history-dir", help="Directory for local scan history JSONL files."),
    config: Path | None = typer.Option(None, "--config", help="Optional project-doctor TOML config file."),
) -> None:
    """Run all scanners and write reports."""
    repo_path = _validate_path(path)
    out_dir, explicit_out = _resolve_output_dir(repo_path, out)
    _warn_if_explicit_output_inside_repo(repo_path, out_dir, explicit_out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = build_report(repo_path, config)
    write_markdown_reports(report, out_dir)
    write_json_reports(report, out_dir)
    write_codex_context(report, out_dir)
    task_paths = write_task_packets(report, out_dir)
    history_path = None
    if history:
        try:
            history_path = write_history_entry(report, history_dir)
        except OSError as exc:
            console.print(f"[yellow]Could not write scan history:[/yellow] {exc}")

    console.print(f"[green]Wrote reports to[/green] {out_dir}")
    console.print(f"Wrote {len(task_paths)} task packet(s) to {out_dir / 'task_packets'}")
    if history_path:
        console.print(f"Wrote scan history to {history_path}")
    console.print(f"Health score: {report.summary.health_score} / 100")


@app.command("git-status")
def git_status(path: str = typer.Argument(..., help="Repository path to inspect.")) -> None:
    """Show read-only Git status details."""
    status = scan_git(_validate_path(path))
    table = Table(title="Git Status")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Is Git repo", str(status.is_git_repo))
    table.add_row("Branch", status.branch or "")
    table.add_row("Dirty", str(status.dirty))
    table.add_row("Remote origin", status.remote_origin or "")
    table.add_row("Modified files", "\n".join(status.modified_files) or "None")
    table.add_row("Untracked files", "\n".join(status.untracked_files) or "None")
    console.print(table)


@app.command()
def todos(
    path: str = typer.Argument(..., help="Repository path to scan."),
    config: Path | None = typer.Option(None, "--config", help="Optional project-doctor TOML config file."),
) -> None:
    """Find TODO, FIXME, HACK, BUG, and REVIEW comments."""
    repo_path = _validate_path(path)
    items = scan_todos(repo_path, load_project_config(repo_path, config))
    table = Table(title=f"TODO Items ({len(items)})")
    table.add_column("Location")
    table.add_column("Tag")
    table.add_column("Priority")
    table.add_column("Category")
    table.add_column("Text")
    for item in items:
        table.add_row(f"{item.file}:{item.line}", item.tag, item.priority, item.category, item.text)
    console.print(table)


@app.command()
def docs(path: str = typer.Argument(..., help="Repository path to inspect.")) -> None:
    """Review basic documentation signals."""
    report = scan_docs(_validate_path(path))
    table = Table(title="Documentation Review")
    table.add_column("Check")
    table.add_column("Result")
    table.add_row("README.md", str(report.has_readme))
    table.add_row(".env.example", str(report.has_env_example))
    table.add_row("CHANGELOG.md", str(report.has_changelog))
    table.add_row("LICENSE", str(report.has_license))
    table.add_row("docs/ folder", str(report.has_docs_folder))
    table.add_row("Documentation score", f"{report.documentation_score} / 100")
    table.add_row("README lines", str(report.readme_line_count))
    table.add_row("README sections", "\n".join(report.readme_sections) or "None")
    table.add_row("Missing sections", "\n".join(report.missing_recommended_sections) or "None")
    table.add_row("Setup keywords", ", ".join(report.setup_keywords_found) or "None")
    table.add_row("Commands documented", str(report.documents_package_scripts_or_commands))
    console.print(table)


@app.command("test-ci")
def test_ci(path: str = typer.Argument(..., help="Repository path to inspect.")) -> None:
    """Detect test runners, test commands, CI workflows, and Docker files."""
    report = scan_test_ci(_validate_path(path))
    table = Table(title="Test and CI Detection")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Test runners", "\n".join(report.test_runners) or "None")
    table.add_row("Test commands", "\n".join(report.test_commands) or "None")
    table.add_row(
        "Package scripts",
        "\n".join(f"{name}: {command}" for name, command in report.package_script_commands.items()) or "None",
    )
    table.add_row("CI workflows", "\n".join(report.ci_workflows) or "None")
    table.add_row("Docker files", "\n".join(report.docker_files) or "None")
    table.add_row("Config files", "\n".join(report.config_files) or "None")
    console.print(table)


@app.command("codex-context")
def codex_context(
    path: str = typer.Argument(..., help="Repository path to scan."),
    out: Path | None = typer.Option(DEFAULT_OUTPUT_DIR, "--out", "-o", help="Output directory."),
    config: Path | None = typer.Option(None, "--config", help="Optional project-doctor TOML config file."),
) -> None:
    """Generate codex_context.md only."""
    repo_path = _validate_path(path)
    out_dir, explicit_out = _resolve_output_dir(repo_path, out)
    _warn_if_explicit_output_inside_repo(repo_path, out_dir, explicit_out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(repo_path, config)
    write_codex_context(report, out_dir)
    console.print(f"[green]Wrote[/green] {out_dir / 'codex_context.md'}")


@app.command("task-packets")
def task_packets(
    path: str = typer.Argument(..., help="Repository path to scan."),
    out: Path | None = typer.Option(DEFAULT_OUTPUT_DIR, "--out", "-o", help="Output directory."),
    config: Path | None = typer.Option(None, "--config", help="Optional project-doctor TOML config file."),
) -> None:
    """Generate Codex/Cline task packet Markdown files."""
    repo_path = _validate_path(path)
    out_dir, explicit_out = _resolve_output_dir(repo_path, out)
    _warn_if_explicit_output_inside_repo(repo_path, out_dir, explicit_out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(repo_path, config)
    paths = write_task_packets(report, out_dir)
    console.print(f"[green]Wrote {len(paths)} task packet(s) to[/green] {out_dir / 'task_packets'}")


@app.command("history")
def history_command(
    path: str = typer.Argument(..., help="Repository path to inspect history for."),
    history_dir: Path | None = typer.Option(None, "--history-dir", help="Directory containing scan history JSONL files."),
    limit: int = typer.Option(10, "--limit", "-n", min=1, help="Maximum history entries to show."),
    diff: bool = typer.Option(False, "--diff", help="Show changes between the latest two scan history entries."),
) -> None:
    """Show local scan history for a repository."""
    repo_path = _validate_path(path)
    entries = load_history(repo_path, history_dir)
    if diff:
        delta = latest_history_delta(entries)
        table = Table(title="Latest Scan Delta")
        table.add_column("Field")
        table.add_column("Change")
        if not delta:
            table.add_row("History", "Need at least two entries to compare")
            console.print(table)
            return
        table.add_row("Previous scan", delta.previous_scanned_at)
        table.add_row("Current scan", delta.current_scanned_at)
        table.add_row("Health score", f"{delta.health_score_delta:+d}")
        table.add_row("Documentation score", f"{delta.documentation_score_delta:+d}")
        table.add_row("TODO count", f"{delta.todo_count_delta:+d}")
        table.add_row("Possible secret count", f"{delta.possible_secret_count_delta:+d}")
        table.add_row("Dependency file count", f"{delta.dependency_file_count_delta:+d}")
        table.add_row("Test command count", f"{delta.test_command_count_delta:+d}")
        table.add_row("CI workflow count", f"{delta.ci_workflow_count_delta:+d}")
        table.add_row("Profile changed", str(delta.profile_changed))
        table.add_row("Dirty changed", str(delta.dirty_changed))
        table.add_row("Branch changed", str(delta.branch_changed))
        table.add_row("Stack added", "\n".join(delta.stack_added) or "None")
        table.add_row("Stack removed", "\n".join(delta.stack_removed) or "None")
        table.add_row("New next steps", "\n".join(delta.new_recommended_next_steps) or "None")
        table.add_row("Resolved next steps", "\n".join(delta.resolved_recommended_next_steps) or "None")
        console.print(table)
        return

    table = Table(title=f"Scan History ({len(entries)})")
    table.add_column("Scanned At")
    table.add_column("Health")
    table.add_column("Profile")
    table.add_column("Docs")
    table.add_column("TODOs")
    table.add_column("Secrets")
    table.add_column("Dirty")
    table.add_column("Branch")

    for entry in entries[-limit:]:
        table.add_row(
            entry.scanned_at,
            str(entry.health_score),
            entry.profile or "",
            str(entry.documentation_score),
            str(entry.todo_count),
            str(entry.possible_secret_count),
            str(entry.dirty),
            entry.branch or "",
        )

    if not entries:
        table.add_row("No history found", "", "", "", "", "", "", "")
    console.print(table)


if __name__ == "__main__":
    app()
