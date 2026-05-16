from __future__ import annotations

from pathlib import Path

from project_doctor.models import DocsReport
from project_doctor.utils.file_utils import read_text_safely

SETUP_WORDS = ("install", "run", "test", "deploy", "environment")
COMMAND_WORDS = ("npm ", "yarn ", "pnpm ", "python ", "pytest", "uvicorn", "flask")


def scan_docs(repo_path: Path) -> DocsReport:
    readme = repo_path / "README.md"
    text = read_text_safely(readme).lower() if readme.exists() else ""
    report = DocsReport(
        has_readme=readme.exists(),
        has_env_example=(repo_path / ".env.example").exists(),
        has_changelog=(repo_path / "CHANGELOG.md").exists(),
        has_license=any((repo_path / name).exists() for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")),
        has_docs_folder=(repo_path / "docs").is_dir(),
        setup_keywords_found=[word for word in SETUP_WORDS if word in text],
        documents_package_scripts_or_commands=any(word in text for word in COMMAND_WORDS),
    )

    if not report.has_readme:
        report.notes.append("README.md is missing")
    if report.has_readme and not report.setup_keywords_found:
        report.notes.append("README.md does not appear to include setup keywords")
    if not report.has_env_example:
        report.notes.append(".env.example is missing")
    return report
