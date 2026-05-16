from __future__ import annotations

from project_doctor.scanners.docs_scanner import scan_docs


def test_scan_docs_scores_readme_quality_signals(tmp_path):
    (tmp_path / "README.md").write_text(
        "\n".join(
            [
                "# Example",
                "",
                "## Installation",
                "Install with pip.",
                "",
                "## Usage",
                "Run with `python -m example`.",
                "",
                "## Testing",
                "Run `python -m pytest`.",
                "",
                "## Configuration",
                "Copy `.env.example` before running locally.",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".env.example").write_text("API_KEY=your-api-key\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()

    report = scan_docs(tmp_path)

    assert report.has_readme is True
    assert report.readme_line_count == 13
    assert report.readme_sections == ["Example", "Installation", "Usage", "Testing", "Configuration"]
    assert report.missing_recommended_sections == []
    assert report.documentation_score == 100


def test_scan_docs_reports_missing_recommended_sections(tmp_path):
    (tmp_path / "README.md").write_text("# Sparse\n\nA tiny note.\n", encoding="utf-8")

    report = scan_docs(tmp_path)

    assert report.documentation_score < 50
    assert report.missing_recommended_sections == ["setup", "usage", "testing", "configuration"]
    assert "README.md is missing recommended sections: setup, usage, testing, configuration" in report.notes
