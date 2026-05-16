from __future__ import annotations

import json

from project_doctor.scanners.test_ci_scanner import scan_test_ci


def test_scan_test_ci_detects_node_scripts_and_github_actions(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "vitest run",
                    "lint": "eslint .",
                    "dev": "vite",
                },
                "devDependencies": {"vitest": "^2.0.0"},
            }
        ),
        encoding="utf-8",
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")

    report = scan_test_ci(tmp_path)

    assert "vitest" in report.test_runners
    assert "npm run test" in report.test_commands
    assert "npm run lint" in report.test_commands
    assert report.ci_workflows == [".github/workflows/ci.yml"]
    assert report.docker_files == ["Dockerfile"]


def test_scan_test_ci_detects_pytest(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8.0"]\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        encoding="utf-8",
    )

    report = scan_test_ci(tmp_path)

    assert report.test_runners == ["pytest"]
    assert report.test_commands == ["python -m pytest"]
    assert "pyproject.toml" in report.config_files
