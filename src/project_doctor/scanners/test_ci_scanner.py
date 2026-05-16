from __future__ import annotations

import json
import tomllib
from pathlib import Path

from project_doctor.models import TestCiReport
from project_doctor.utils.path_utils import relative_to_repo

SCRIPT_NAMES = ("test", "lint", "typecheck", "check", "coverage")
NODE_RUNNERS = ("vitest", "jest", "playwright", "cypress")
PYTHON_RUNNERS = ("pytest", "tox", "nox")


def _read_package_json(repo_path: Path) -> dict:
    path = repo_path / "package.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _detect_node(repo_path: Path, report: TestCiReport) -> None:
    package = _read_package_json(repo_path)
    if not package:
        return

    scripts = package.get("scripts", {})
    if isinstance(scripts, dict):
        for name, command in sorted(scripts.items()):
            if any(token in name.lower() for token in SCRIPT_NAMES):
                report.package_script_commands[str(name)] = str(command)
                package_runner = _package_runner(repo_path)
                report.test_commands.append(f"{package_runner} {name}")

    all_deps: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = package.get(section, {})
        if isinstance(deps, dict):
            all_deps.update({str(key): str(value) for key, value in deps.items()})

    for runner in NODE_RUNNERS:
        if runner in all_deps or any(runner in command for command in report.package_script_commands.values()):
            report.test_runners.append(runner)


def _package_runner(repo_path: Path) -> str:
    if (repo_path / "pnpm-lock.yaml").exists():
        return "pnpm run"
    if (repo_path / "yarn.lock").exists():
        return "yarn"
    return "npm run"


def _detect_python(repo_path: Path, report: TestCiReport) -> None:
    requirement_text = ""
    requirements = repo_path / "requirements.txt"
    if requirements.exists():
        requirement_text = requirements.read_text(encoding="utf-8", errors="replace").lower()

    pyproject_data = {}
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            pyproject_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            pyproject_data = {}

    pyproject_text = pyproject.read_text(encoding="utf-8", errors="replace").lower() if pyproject.exists() else ""
    combined = f"{requirement_text}\n{pyproject_text}"

    if "pytest" in combined or (repo_path / "pytest.ini").exists():
        report.test_runners.append("pytest")
        report.test_commands.append("python -m pytest")
    if "tox" in combined or (repo_path / "tox.ini").exists():
        report.test_runners.append("tox")
        report.test_commands.append("tox")
    if "nox" in combined or (repo_path / "noxfile.py").exists():
        report.test_runners.append("nox")
        report.test_commands.append("nox")

    if "tool" in pyproject_data and "pytest" in pyproject_text:
        report.config_files.append("pyproject.toml")


def _detect_config_files(repo_path: Path, report: TestCiReport) -> None:
    exact_files = (
        "pytest.ini",
        "tox.ini",
        "noxfile.py",
        "vitest.config.js",
        "vitest.config.ts",
        "jest.config.js",
        "jest.config.ts",
        "playwright.config.js",
        "playwright.config.ts",
        "cypress.config.js",
        "cypress.config.ts",
    )
    for file_name in exact_files:
        if (repo_path / file_name).exists():
            report.config_files.append(file_name)

    github_workflows = repo_path / ".github" / "workflows"
    if github_workflows.is_dir():
        for path in sorted(github_workflows.glob("*")):
            if path.suffix.lower() in {".yml", ".yaml"}:
                report.ci_workflows.append(relative_to_repo(path, repo_path))

    for file_name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        if (repo_path / file_name).exists():
            report.docker_files.append(file_name)


def scan_test_ci(repo_path: Path) -> TestCiReport:
    report = TestCiReport()
    _detect_node(repo_path, report)
    _detect_python(repo_path, report)
    _detect_config_files(repo_path, report)

    report.test_runners = sorted(set(report.test_runners))
    report.test_commands = sorted(set(report.test_commands))
    report.config_files = sorted(set(report.config_files))

    if not report.test_commands:
        report.notes.append("No obvious test command detected")
    if not report.ci_workflows:
        report.notes.append("No GitHub Actions workflows detected")
    return report
