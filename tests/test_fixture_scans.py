from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from project_doctor.cli import app


FIXTURES = Path(__file__).parent / "fixtures"
REPORT_FILES = {
    "project_report.md",
    "repo_summary.md",
    "dependency_report.json",
    "docs_report.json",
    "todo_report.json",
    "secrets_report.json",
    "findings_summary.json",
    "git_status_report.json",
    "test_ci_report.json",
    "repo_summary.json",
    "codex_context.md",
}
IGNORED_SECRET_VALUES = {
    "ignored-secret-value",
    "ignored-dist-secret",
    "ignored-build-secret",
    "ignored-dotvenv-secret",
    "ignored-venv-secret",
    "ignored-env-secret",
    "ignored-pycache-secret",
    "ignored-cache-secret",
    "ignored-coverage-secret",
}


runner = CliRunner()


def _scan_fixture(name: str, tmp_path: Path) -> Path:
    out_dir = tmp_path / f"{name}-reports"
    history_dir = tmp_path / f"{name}-history"
    result = runner.invoke(
        app,
        ["scan", str(FIXTURES / name), "--out", str(out_dir), "--history-dir", str(history_dir)],
    )

    assert result.exit_code == 0, result.output
    assert list(history_dir.glob("*.jsonl"))
    return out_dir


def _read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def test_python_fixture_scan_generates_expected_reports_and_redacts_secrets(tmp_path):
    out_dir = _scan_fixture("python_project", tmp_path)
    repo = FIXTURES / "python_project"

    assert {path.name for path in out_dir.iterdir() if path.is_file()} == REPORT_FILES
    assert list((out_dir / "task_packets").glob("*.md"))
    assert not (repo / "reports" / "project_report.md").exists()

    summary = _read_json(out_dir / "repo_summary.json")
    dependencies = _read_json(out_dir / "dependency_report.json")
    docs = _read_json(out_dir / "docs_report.json")
    todos = _read_json(out_dir / "todo_report.json")
    secrets = _read_json(out_dir / "secrets_report.json")
    findings_summary = _read_json(out_dir / "findings_summary.json")
    test_ci = _read_json(out_dir / "test_ci_report.json")

    assert "FastAPI" in summary["detected_stack"]
    assert "Python package" in summary["detected_stack"]
    assert dependencies["files_found"] == ["pyproject.toml"]
    assert dependencies["dependencies"]["pyproject.toml:project.dependencies"] == ["fastapi", "pytest"]
    assert docs["has_readme"] is True
    assert "pytest" in test_ci["test_runners"]
    assert "python -m pytest" in test_ci["test_commands"]
    assert todos == [
        {
            "file": "src/app.py",
            "line": 5,
            "tag": "TODO",
            "text": "# TODO: replace fixture implementation",
            "category": "source",
            "priority": "medium",
            "reason": "source code follow-up",
        }
    ]
    assert secrets == [
        {
            "file": "src/app.py",
            "line": 1,
            "key": "API_KEY",
            "redacted_text": "API_KEY=...REDACTED",
            "reason": "secret-like code assignment or configuration reference",
            "severity": "medium",
        }
    ]
    assert findings_summary["todos"]["top_files"] == [{"count": 1, "file": "src/app.py"}]
    assert findings_summary["possible_secrets"]["by_severity"] == {"medium": 1}

    combined = "\n".join(path.read_text(encoding="utf-8") for path in out_dir.rglob("*") if path.is_file())
    assert "fixture-secret-value" not in combined
    for value in IGNORED_SECRET_VALUES:
        assert value not in combined
    assert "ignored dependency folder" not in combined
    assert "ignored report folder" not in combined


def test_node_fixture_scan_detects_stack_test_commands_and_ci(tmp_path):
    out_dir = _scan_fixture("node_project", tmp_path)

    summary = _read_json(out_dir / "repo_summary.json")
    dependencies = _read_json(out_dir / "dependency_report.json")
    secrets = _read_json(out_dir / "secrets_report.json")
    todos = _read_json(out_dir / "todo_report.json")
    findings_summary = _read_json(out_dir / "findings_summary.json")
    test_ci = _read_json(out_dir / "test_ci_report.json")

    assert {path.name for path in out_dir.iterdir() if path.is_file()} == REPORT_FILES
    assert "Node" in summary["detected_stack"]
    assert "React/Vite" in summary["detected_stack"]
    assert dependencies["files_found"] == ["package.json"]
    assert dependencies["package_manager_locks"] == ["pnpm-lock.yaml"]
    assert dependencies["dependencies"]["package.json:dependencies"] == ["react"]
    assert dependencies["dependencies"]["package.json:devDependencies"] == ["vite", "vitest"]
    assert dependencies["scripts"] == {
        "build": "vite build",
        "lint": "eslint .",
        "test": "vitest run",
    }
    assert secrets == []
    assert "vitest" in test_ci["test_runners"]
    assert "pnpm run test" in test_ci["test_commands"]
    assert "pnpm run lint" in test_ci["test_commands"]
    assert test_ci["ci_workflows"] == [".github/workflows/ci.yml"]
    assert todos == [
        {
            "file": "src/App.tsx",
            "line": 2,
            "tag": "FIXME",
            "text": "// FIXME: add real fixture UI",
            "category": "source",
            "priority": "high",
            "reason": "source defect marker",
        }
    ]
    assert findings_summary["todos"]["by_priority"] == {"high": 1}
    assert findings_summary["possible_secrets"]["total"] == 0


def test_fixture_subcommands_include_meaningful_detected_values(tmp_path):
    python_repo = FIXTURES / "python_project"
    node_repo = FIXTURES / "node_project"

    docs_result = runner.invoke(app, ["docs", str(python_repo)])
    todos_result = runner.invoke(app, ["todos", str(python_repo)])
    test_ci_result = runner.invoke(app, ["test-ci", str(node_repo)])

    assert docs_result.exit_code == 0
    assert "README.md" in docs_result.output
    assert "True" in docs_result.output
    assert todos_result.exit_code == 0
    assert "src/app.py:5" in todos_result.output
    assert "TODO" in todos_result.output
    assert test_ci_result.exit_code == 0
    assert "vitest" in test_ci_result.output
    assert "pnpm run test" in test_ci_result.output
