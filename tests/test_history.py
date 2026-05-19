from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from project_doctor.cli import app, build_report
from project_doctor.history import build_history_entry, compare_history_entries, load_history, write_history_entry


runner = CliRunner()


def _repo(path: Path) -> Path:
    path.mkdir()
    (path / "README.md").write_text(
        "# Example\n\n## Installation\nInstall with pip.\n\n## Testing\nRun python -m pytest.\n",
        encoding="utf-8",
    )
    (path / "pyproject.toml").write_text('[project]\ndependencies = ["pytest>=8"]\n', encoding="utf-8")
    (path / "app.py").write_text("# TODO: test history\n", encoding="utf-8")
    return path


def test_build_history_entry_contains_summary_without_findings(tmp_path):
    repo = _repo(tmp_path / "repo")
    report = build_report(repo)

    entry = build_history_entry(report)

    assert entry.repo_name == "repo"
    assert entry.schema_version == 3
    assert entry.repo_path is None
    assert entry.profile is None
    assert entry.health_score == report.summary.health_score
    assert entry.documentation_score == report.docs.documentation_score
    assert entry.todo_count == 1
    assert entry.possible_secret_count == 0
    assert entry.recommended_next_steps
    payload = entry.model_dump(mode="json")
    assert "TODO: test history" not in json.dumps(payload)
    assert str(repo) not in json.dumps(payload)


def test_build_history_entry_includes_profile(tmp_path):
    repo = _repo(tmp_path / "repo")
    (repo / ".project-doctor.toml").write_text('profile = "custom"\n', encoding="utf-8")
    report = build_report(repo)

    entry = build_history_entry(report)

    assert report.summary.profile == "custom"
    assert entry.profile == "custom"
    assert "Profile: custom" not in entry.detected_stack


def test_write_and_load_history_entries(tmp_path):
    repo = _repo(tmp_path / "repo")
    history_dir = tmp_path / "history"
    report = build_report(repo)

    path = write_history_entry(report, history_dir)
    write_history_entry(report, history_dir)
    entries = load_history(repo, history_dir)
    payload = path.read_text(encoding="utf-8")

    assert path.parent == history_dir.resolve()
    assert len(entries) == 2
    assert all(entry.repo_hash == entries[0].repo_hash for entry in entries)
    assert "repo_path" not in payload
    assert str(repo) not in payload


def test_scan_writes_history_and_history_command_displays_it(tmp_path):
    repo = _repo(tmp_path / "repo")
    out_dir = tmp_path / "reports"
    history_dir = tmp_path / "history"

    scan_result = runner.invoke(app, ["scan", str(repo), "--out", str(out_dir), "--history-dir", str(history_dir)])
    history_result = runner.invoke(app, ["history", str(repo), "--history-dir", str(history_dir)])

    assert scan_result.exit_code == 0
    assert "Wrote scan history" in scan_result.output
    assert history_result.exit_code == 0
    assert "Scan History (1)" in history_result.output
    assert "repo" not in history_result.output


def test_compare_history_entries_reports_deltas(tmp_path):
    repo = _repo(tmp_path / "repo")
    first = build_history_entry(build_report(repo))
    first.scanned_at = "2026-05-16T10:00:00+00:00"
    (repo / "app.py").write_text("# TODO: test history\n# FIXME: second item\n", encoding="utf-8")
    (repo / "config.yml").write_text("API_KEY: real-value\n", encoding="utf-8")
    second = build_history_entry(build_report(repo))
    second.scanned_at = "2026-05-16T11:00:00+00:00"
    second.profile = "custom"

    delta = compare_history_entries(first, second)

    assert delta.previous_scanned_at == "2026-05-16T10:00:00+00:00"
    assert delta.current_scanned_at == "2026-05-16T11:00:00+00:00"
    assert delta.todo_count_delta == 1
    assert delta.possible_secret_count_delta == 1
    assert delta.health_score_delta < 0
    assert delta.profile_changed is True


def test_history_diff_command_displays_latest_delta(tmp_path):
    repo = _repo(tmp_path / "repo")
    out_dir = tmp_path / "reports"
    history_dir = tmp_path / "history"

    first_scan = runner.invoke(app, ["scan", str(repo), "--out", str(out_dir), "--history-dir", str(history_dir)])
    (repo / "app.py").write_text("# TODO: test history\n# FIXME: second item\n", encoding="utf-8")
    second_scan = runner.invoke(app, ["scan", str(repo), "--out", str(out_dir), "--history-dir", str(history_dir)])
    diff_result = runner.invoke(app, ["history", str(repo), "--history-dir", str(history_dir), "--diff"])

    assert first_scan.exit_code == 0
    assert second_scan.exit_code == 0
    assert diff_result.exit_code == 0
    assert "Latest Scan Delta" in diff_result.output
    assert "TODO count" in diff_result.output
    assert "+1" in diff_result.output
