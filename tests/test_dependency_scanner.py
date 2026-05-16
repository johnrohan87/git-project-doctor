from __future__ import annotations

import json

from project_doctor.scanners.dependency_scanner import scan_dependencies


def test_scan_dependencies_reads_package_json(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "^18.0.0"},
                "devDependencies": {"vite": "^5.0.0"},
                "scripts": {"dev": "vite"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'", encoding="utf-8")

    report = scan_dependencies(tmp_path)

    assert "package.json" in report.files_found
    assert "pnpm-lock.yaml" in report.package_manager_locks
    assert report.dependencies["package.json:dependencies"] == ["react"]
    assert report.dependencies["package.json:devDependencies"] == ["vite"]
    assert report.scripts == {"dev": "vite"}


def test_scan_dependencies_reads_requirements_and_pyproject(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi>=0.1\n# ignored\n-r base.txt\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["typer>=0.12.0", "rich==13.0.0"]\n',
        encoding="utf-8",
    )

    report = scan_dependencies(tmp_path)

    assert report.dependencies["requirements.txt"] == ["fastapi"]
    assert report.dependencies["pyproject.toml:project.dependencies"] == ["rich", "typer"]
