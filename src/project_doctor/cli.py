from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from project_doctor.config import DEFAULT_OUTPUT_DIR
from project_doctor.models import ProjectReport, RepoSummary
from project_doctor.reporters.codex_context_reporter import write_codex_context
from project_doctor.reporters.json_reporter import write_json_reports
from project_doctor.reporters.markdown_reporter import write_markdown_reports
from project_doctor.reporters.task_packet_reporter import write_task_packets
from project_doctor.scanners.dependency_scanner import scan_dependencies
from project_doctor.scanners.docs_scanner import scan_docs
from project_doctor.scanners.git_scanner import scan_git
from project_doctor.scanners.secrets_scanner import scan_secrets
from project_doctor.scanners.structure_scanner import scan_structure
from project_doctor.scanners.todo_scanner import scan_todos
from project_doctor.utils.path_utils import resolve_repo_path

app = typer.Typer(help="Local-first Git project review and update planning tool.")
console = Console()


def _recommended_next_steps(report: ProjectReport) -> list[str]:
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
    if not steps:
        steps.append("No urgent Phase 1 issues detected; consider adding deeper test and CI review in Phase 2")
    return steps


def _health_score(report: ProjectReport) -> int:
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
    score -= min(len(report.todos), 20)
    score -= min(len(report.secrets) * 10, 30)
    return max(0, min(100, score))


def build_report(repo_path: Path) -> ProjectReport:
    git = scan_git(repo_path)
    dependencies = scan_dependencies(repo_path)
    docs = scan_docs(repo_path)
    todos = scan_todos(repo_path)
    secrets = scan_secrets(repo_path)
    structure = scan_structure(repo_path)

    summary = RepoSummary(
        path=repo_path,
        name=repo_path.name,
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
    )
    report.summary.health_score = _health_score(report)
    report.summary.recommended_next_steps = _recommended_next_steps(report)
    return report


def _validate_path(path: str) -> Path:
    repo_path = resolve_repo_path(path)
    if not repo_path.exists() or not repo_path.is_dir():
        raise typer.BadParameter(f"Path does not exist or is not a directory: {repo_path}")
    return repo_path


@app.command()
def scan(
    path: str = typer.Argument(..., help="Repository path to scan."),
    out: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--out", "-o", help="Output directory for reports."),
) -> None:
    """Run all scanners and write Phase 1 reports."""
    repo_path = _validate_path(path)
    out_dir = out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report = build_report(repo_path)
    write_markdown_reports(report, out_dir)
    write_json_reports(report, out_dir)
    write_codex_context(report, out_dir)
    task_paths = write_task_packets(report, out_dir)

    console.print(f"[green]Wrote reports to[/green] {out_dir}")
    console.print(f"Wrote {len(task_paths)} task packet(s) to {out_dir / 'task_packets'}")
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
def todos(path: str = typer.Argument(..., help="Repository path to scan.")) -> None:
    """Find TODO, FIXME, HACK, BUG, and REVIEW comments."""
    items = scan_todos(_validate_path(path))
    table = Table(title=f"TODO Items ({len(items)})")
    table.add_column("Location")
    table.add_column("Tag")
    table.add_column("Text")
    for item in items:
        table.add_row(f"{item.file}:{item.line}", item.tag, item.text)
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
    table.add_row("Setup keywords", ", ".join(report.setup_keywords_found) or "None")
    table.add_row("Commands documented", str(report.documents_package_scripts_or_commands))
    console.print(table)


@app.command("codex-context")
def codex_context(
    path: str = typer.Argument(..., help="Repository path to scan."),
    out: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--out", "-o", help="Output directory."),
) -> None:
    """Generate codex_context.md only."""
    repo_path = _validate_path(path)
    out_dir = out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(repo_path)
    write_codex_context(report, out_dir)
    console.print(f"[green]Wrote[/green] {out_dir / 'codex_context.md'}")


@app.command("task-packets")
def task_packets(
    path: str = typer.Argument(..., help="Repository path to scan."),
    out: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--out", "-o", help="Output directory."),
) -> None:
    """Generate Codex/Cline task packet Markdown files."""
    repo_path = _validate_path(path)
    out_dir = out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(repo_path)
    paths = write_task_packets(report, out_dir)
    console.print(f"[green]Wrote {len(paths)} task packet(s) to[/green] {out_dir / 'task_packets'}")


if __name__ == "__main__":
    app()
