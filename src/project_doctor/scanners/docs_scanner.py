from __future__ import annotations

import re
from pathlib import Path

from project_doctor.models import DocsReport
from project_doctor.utils.file_utils import read_text_safely

SETUP_WORDS = ("install", "run", "test", "deploy", "environment")
COMMAND_WORDS = ("npm ", "yarn ", "pnpm ", "python ", "pytest", "uvicorn", "flask")
README_SECTION_RE = re.compile(r"^#{1,6}\s+(?P<title>.+?)\s*$", re.MULTILINE)
RECOMMENDED_SECTIONS = {
    "setup": ("install", "installation", "setup", "getting started"),
    "usage": ("usage", "run", "commands", "example commands"),
    "testing": ("test", "tests", "testing"),
    "configuration": ("configuration", "environment", "env", "settings"),
}


def _readme_sections(text: str) -> list[str]:
    sections = []
    for match in README_SECTION_RE.finditer(text):
        title = re.sub(r"\s+", " ", match.group("title").strip().strip("#"))
        if title:
            sections.append(title)
    return sections


def _missing_sections(sections: list[str], text: str) -> list[str]:
    searchable = "\n".join(sections).lower()
    if not searchable:
        searchable = text
    missing = []
    for name, keywords in RECOMMENDED_SECTIONS.items():
        if not any(keyword in searchable for keyword in keywords):
            missing.append(name)
    return missing


def _documentation_score(report: DocsReport) -> int:
    score = 0
    if report.has_readme:
        score += 30
    if report.setup_keywords_found:
        score += 15
    if report.documents_package_scripts_or_commands:
        score += 15
    if "testing" not in report.missing_recommended_sections:
        score += 10
    if "configuration" not in report.missing_recommended_sections or report.has_env_example:
        score += 10
    if report.has_changelog:
        score += 5
    if report.has_license:
        score += 5
    if report.has_docs_folder:
        score += 5
    if report.readme_line_count >= 10:
        score += 5
    return max(0, min(100, score))


def scan_docs(repo_path: Path) -> DocsReport:
    readme = repo_path / "README.md"
    raw_text = read_text_safely(readme) if readme.exists() else ""
    text = raw_text.lower()
    sections = _readme_sections(raw_text)
    report = DocsReport(
        has_readme=readme.exists(),
        has_env_example=(repo_path / ".env.example").exists(),
        has_changelog=(repo_path / "CHANGELOG.md").exists(),
        has_license=any((repo_path / name).exists() for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")),
        has_docs_folder=(repo_path / "docs").is_dir(),
        readme_line_count=len(raw_text.splitlines()),
        readme_sections=sections,
        missing_recommended_sections=_missing_sections(sections, text) if readme.exists() else list(RECOMMENDED_SECTIONS),
        setup_keywords_found=[word for word in SETUP_WORDS if word in text],
        documents_package_scripts_or_commands=any(word in text for word in COMMAND_WORDS),
    )
    report.documentation_score = _documentation_score(report)

    if not report.has_readme:
        report.notes.append("README.md is missing")
    if report.has_readme and not report.setup_keywords_found:
        report.notes.append("README.md does not appear to include setup keywords")
    if report.has_readme and report.missing_recommended_sections:
        missing = ", ".join(report.missing_recommended_sections)
        report.notes.append(f"README.md is missing recommended sections: {missing}")
    if not report.has_env_example:
        report.notes.append(".env.example is missing")
    return report
