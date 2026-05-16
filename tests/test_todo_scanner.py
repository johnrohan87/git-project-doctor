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


def test_scan_todos_ignores_local_tool_state_prefixes(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("# TODO: keep this\n", encoding="utf-8")
    ignored = tmp_path / ".tools" / "local-state" / "capture"
    ignored.mkdir(parents=True)
    (ignored / "schema.txt").write_text("TODO ignored generated capture\n", encoding="utf-8")

    items = scan_todos(tmp_path)

    assert [(item.file, item.line, item.tag) for item in items] == [("src/app.py", 1, "TODO")]


def test_scan_secrets_redacts_values(tmp_path):
    (tmp_path / ".env.example").write_text("API_KEY=actual-secret-value\n", encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].key == "API_KEY"
    assert findings[0].severity == "high"
    assert findings[0].reason == "secret-like configuration value"
    assert "actual-secret-value" not in findings[0].redacted_text
    assert "REDACTED" in findings[0].redacted_text


def test_scan_secrets_redacts_colon_and_quoted_values(tmp_path):
    (tmp_path / "config.yml").write_text('service_token: "real-token-value"\n', encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].key == "service_token"
    assert findings[0].severity == "high"
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


def test_scan_secrets_ignores_local_tool_binary_cache_prefixes(tmp_path):
    (tmp_path / "config.yml").write_text("API_KEY: real-value\n", encoding="utf-8")
    ignored = tmp_path / ".tools" / "bin" / "vendor"
    ignored.mkdir(parents=True)
    (ignored / "bundle.js").write_text("TOKEN=ignored-vendor-token\n", encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert [(item.file, item.key) for item in findings] == [("config.yml", "API_KEY")]


def test_scan_secrets_classifies_docs_and_cache_paths_as_low_severity(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "setup.md").write_text("TOKEN=not-a-real-doc-value\n", encoding="utf-8")
    (tmp_path / "script.py").write_text("token_cache_path='/tmp/token-cache.json'\n", encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert sorted((item.file, item.severity, item.reason) for item in findings) == [
        ("docs/setup.md", "low", "documentation example or note"),
        ("script.py", "low", "token/cache path or configuration reference"),
    ]


def test_scan_secrets_classifies_code_assignments_as_medium_severity(tmp_path):
    (tmp_path / "script.py").write_text("access_token='real-looking-value'\n", encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].severity == "medium"
    assert findings[0].reason == "secret-like code assignment or configuration reference"
