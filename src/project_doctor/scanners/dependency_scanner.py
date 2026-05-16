from __future__ import annotations

import json
import tomllib
from pathlib import Path

from project_doctor.models import DependencyReport


def _read_package_json(path: Path, report: DependencyReport) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict):
            report.dependencies[f"package.json:{section}"] = sorted(deps.keys())
    scripts = data.get("scripts", {})
    if isinstance(scripts, dict):
        report.scripts = {str(key): str(value) for key, value in sorted(scripts.items())}


def _read_requirements(path: Path, report: DependencyReport) -> None:
    deps: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    for line in lines:
        clean = line.strip()
        if not clean or clean.startswith("#") or clean.startswith("-"):
            continue
        name = clean.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].split("[")[0].strip()
        if name:
            deps.append(name)
    report.dependencies["requirements.txt"] = sorted(set(deps))


def _read_pyproject(path: Path, report: DependencyReport) -> None:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return
    project = data.get("project", {})
    deps = project.get("dependencies", [])
    if isinstance(deps, list):
        names = [str(dep).split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip() for dep in deps]
        report.dependencies["pyproject.toml:project.dependencies"] = sorted(filter(None, names))


def scan_dependencies(repo_path: Path) -> DependencyReport:
    report = DependencyReport()
    known_files = {
        "package.json": _read_package_json,
        "requirements.txt": _read_requirements,
        "pyproject.toml": _read_pyproject,
    }
    lock_files = ("yarn.lock", "package-lock.json", "pnpm-lock.yaml")

    for file_name, reader in known_files.items():
        path = repo_path / file_name
        if path.exists():
            report.files_found.append(file_name)
            reader(path, report)

    for file_name in lock_files:
        if (repo_path / file_name).exists():
            report.package_manager_locks.append(file_name)

    return report
