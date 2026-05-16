from __future__ import annotations

import json
from pathlib import Path

from project_doctor.models import StructureReport


def _package_json(repo_path: Path) -> dict:
    path = repo_path / "package.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def scan_structure(repo_path: Path) -> StructureReport:
    report = StructureReport()
    package = _package_json(repo_path)
    all_deps = {}
    for section in ("dependencies", "devDependencies"):
        deps = package.get(section, {})
        if isinstance(deps, dict):
            all_deps.update(deps)

    if "vite" in all_deps and "react" in all_deps:
        report.project_types.append("React/Vite")
    if "gatsby" in all_deps:
        report.project_types.append("Gatsby")
    if "expo" in all_deps:
        report.project_types.append("Expo/React Native")
    if package:
        report.project_types.append("Node")

    if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
        report.project_types.append("Python package")

    pyproject = (repo_path / "pyproject.toml").read_text(encoding="utf-8", errors="replace") if (repo_path / "pyproject.toml").exists() else ""
    requirements = (repo_path / "requirements.txt").read_text(encoding="utf-8", errors="replace") if (repo_path / "requirements.txt").exists() else ""
    combined_python = f"{pyproject}\n{requirements}".lower()
    if "fastapi" in combined_python:
        report.project_types.append("FastAPI")
    if "flask" in combined_python:
        report.project_types.append("Flask")

    for folder in ("src", "server", "app", "components", "pages", "tests", "docs"):
        if (repo_path / folder).is_dir():
            report.important_folders.append(folder)

    for file_name in ("README.md", "package.json", "pyproject.toml", "requirements.txt", ".env.example", "AGENTS.md"):
        if (repo_path / file_name).exists():
            report.important_files.append(file_name)

    report.project_types = sorted(set(report.project_types))
    return report
