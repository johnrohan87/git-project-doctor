from __future__ import annotations

from project_doctor.scanners.secrets_scanner import scan_secrets
from project_doctor.scanners.todo_scanner import scan_todos


def test_scan_todos_finds_tags_and_ignores_node_modules(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("# TODO: wire CLI\nprint('x')\n# FIXME bad path\n", encoding="utf-8")
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "dep.js").write_text("// TODO ignored\n", encoding="utf-8")

    items = scan_todos(tmp_path)

    assert [(item.file, item.line, item.tag) for item in items] == [
        ("src/app.py", 1, "TODO"),
        ("src/app.py", 3, "FIXME"),
    ]


def test_scan_secrets_redacts_values(tmp_path):
    (tmp_path / ".env.example").write_text("API_KEY=actual-secret-value\n", encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].key == "API_KEY"
    assert "actual-secret-value" not in findings[0].redacted_text
    assert "REDACTED" in findings[0].redacted_text


def test_scan_secrets_redacts_colon_and_quoted_values(tmp_path):
    (tmp_path / "config.yml").write_text('service_token: "real-token-value"\n', encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].key == "service_token"
    assert findings[0].redacted_text == "service_token:...REDACTED"
    assert "real-token-value" not in findings[0].redacted_text


def test_scan_secrets_ignores_obvious_placeholders(tmp_path):
    (tmp_path / ".env.example").write_text(
        "\n".join(
            [
                "API_KEY=your-api-key",
                "TOKEN=changeme",
                "PASSWORD=example-password",
                "PRIVATE_KEY='placeholder'",
                "CLIENT_SECRET=dummy-value",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_secrets(tmp_path) == []
