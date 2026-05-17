from __future__ import annotations

from project_doctor.project_config import load_project_config
from project_doctor.scanners.todo_scanner import scan_todos


def test_load_project_config_from_default_file(tmp_path):
    (tmp_path / ".project-doctor.toml").write_text(
        """
profile = "custom"

[todos]
generated_path_prefixes = ["exports"]
historical_doc_markers = ["work-log"]
backlog_doc_markers = ["active-plan"]

[secrets]
ignored_path_prefixes = ["public/assets"]
""".strip(),
        encoding="utf-8",
    )

    config = load_project_config(tmp_path)

    assert config.profile == "custom"
    assert config.generated_path_prefixes == ["exports"]
    assert config.historical_doc_markers == ["work-log"]
    assert config.backlog_doc_markers == ["active-plan"]
    assert config.secret_ignored_path_prefixes == ["public/assets"]


def test_load_project_config_from_explicit_file(tmp_path):
    config_path = tmp_path / "doctor.toml"
    config_path.write_text(
        """
[project_doctor]
profile = "custom"
generated_path_prefixes = ["snapshots"]
secret_ignored_path_prefixes = ["generated"]
""".strip(),
        encoding="utf-8",
    )

    config = load_project_config(tmp_path, config_path)

    assert config.profile == "custom"
    assert config.generated_path_prefixes == ["snapshots"]
    assert config.secret_ignored_path_prefixes == ["generated"]


def test_scan_todos_uses_project_config_classification(tmp_path):
    (tmp_path / ".project-doctor.toml").write_text(
        """
[todos]
generated_path_prefixes = ["exports"]
historical_doc_markers = ["decision-log"]
backlog_doc_markers = ["active-plan"]
""".strip(),
        encoding="utf-8",
    )
    exports = tmp_path / "exports"
    docs = tmp_path / "docs"
    exports.mkdir()
    docs.mkdir()
    (exports / "sample.json").write_text('"note": "TODO generated"\n', encoding="utf-8")
    (docs / "decision-log.md").write_text("TODO historical\n", encoding="utf-8")
    (docs / "active-plan.md").write_text("TODO backlog\n", encoding="utf-8")

    config = load_project_config(tmp_path)
    items = scan_todos(tmp_path, config)

    assert sorted((item.file, item.category, item.priority) for item in items) == [
        ("docs/active-plan.md", "backlog", "medium"),
        ("docs/decision-log.md", "historical", "low"),
        ("exports/sample.json", "generated", "low"),
    ]
