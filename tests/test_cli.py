from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from project_doctor.cli import app


runner = CliRunner()


def _sample_repo(path: Path) -> Path:
    path.mkdir()
    (path / "README.md").write_text(
        "# Example\n\nInstall with pip. Run tests with python -m pytest.\n",
        encoding="utf-8",
    )
    (path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8.0"]\n',
        encoding="utf-8",
    )
    src = path / "src"
    src.mkdir()
    (src / "app.py").write_text("# TODO: wire real app\nAPI_KEY=actual-secret-value\n", encoding="utf-8")
    return path


def test_scan_writes_reports_to_custom_output_dir(tmp_path):
    repo = _sample_repo(tmp_path / "repo")
    out_dir = tmp_path / "doctor-output"
    history_dir = tmp_path / "history"

    result = runner.invoke(app, ["scan", str(repo), "--out", str(out_dir), "--history-dir", str(history_dir)])

    assert result.exit_code == 0
    assert (out_dir / "project_report.md").exists()
    assert (out_dir / "repo_summary.md").exists()
    assert (out_dir / "dependency_report.json").exists()
    assert (out_dir / "docs_report.json").exists()
    assert (out_dir / "todo_report.json").exists()
    assert (out_dir / "secrets_report.json").exists()
    assert (out_dir / "git_status_report.json").exists()
    assert (out_dir / "test_ci_report.json").exists()
    assert (out_dir / "codex_context.md").exists()
    assert list((out_dir / "task_packets").glob("*.md"))
    assert list(history_dir.glob("*.jsonl"))
    assert not (repo / "reports").exists()


def test_scan_report_redacts_secret_values(tmp_path):
    repo = _sample_repo(tmp_path / "repo")
    out_dir = tmp_path / "doctor-output"

    result = runner.invoke(app, ["scan", str(repo), "--out", str(out_dir), "--no-history"])

    assert result.exit_code == 0
    combined = "\n".join(path.read_text(encoding="utf-8") for path in out_dir.rglob("*") if path.is_file())
    assert "API_KEY=...REDACTED" in combined
    assert "actual-secret-value" not in combined


def test_cli_rejects_missing_path(tmp_path):
    result = runner.invoke(app, ["docs", str(tmp_path / "missing")])

    assert result.exit_code != 0
    assert "Path does not exist or is not a directory" in result.output


def test_read_only_subcommands_smoke(tmp_path):
    repo = _sample_repo(tmp_path / "repo")

    commands = [
        (["git-status", str(repo)], "Git Status"),
        (["todos", str(repo)], "TODO Items"),
        (["docs", str(repo)], "Documentation Review"),
        (["test-ci", str(repo)], "Test and CI Detection"),
    ]

    for args, expected in commands:
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        assert expected in result.output


def test_context_commands_write_requested_outputs(tmp_path):
    repo = _sample_repo(tmp_path / "repo")
    out_dir = tmp_path / "doctor-output"

    context_result = runner.invoke(app, ["codex-context", str(repo), "--out", str(out_dir)])
    packets_result = runner.invoke(app, ["task-packets", str(repo), "--out", str(out_dir)])

    assert context_result.exit_code == 0
    assert packets_result.exit_code == 0
    assert (out_dir / "codex_context.md").exists()
    assert list((out_dir / "task_packets").glob("*.md"))
