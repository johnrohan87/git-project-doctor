from __future__ import annotations

from project_doctor.models import ProjectDoctorConfig
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
    assert [(item.category, item.priority) for item in items] == [
        ("source", "medium"),
        ("source", "high"),
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


def test_scan_todos_classifies_docs_scripts_and_tests(tmp_path):
    docs = tmp_path / "docs"
    scripts = tmp_path / "scripts"
    tests = tmp_path / "tests"
    docs.mkdir()
    scripts.mkdir()
    tests.mkdir()
    (docs / "notes.md").write_text("TODO: document release\nFIXME: clarify warning\n", encoding="utf-8")
    (scripts / "repair.py").write_text("# HACK: temporary repair path\n", encoding="utf-8")
    (tests / "test_app.py").write_text("# REVIEW: broaden fixture\n", encoding="utf-8")

    items = scan_todos(tmp_path)

    expected = [
        ("docs/notes.md", "TODO", "documentation", "low", "documentation note or backlog reference"),
        ("docs/notes.md", "FIXME", "documentation", "medium", "documentation defect marker"),
        ("scripts/repair.py", "HACK", "script", "medium", "script workaround marker"),
        ("tests/test_app.py", "REVIEW", "test", "medium", "test review marker"),
    ]
    assert sorted((item.file, item.tag, item.category, item.priority, item.reason) for item in items) == sorted(expected)


def test_scan_todos_classifies_fixture_and_tmp_artifacts_as_low_priority(tmp_path):
    tmp_dir = tmp_path / "tmp"
    fixtures = tmp_path / "fixtures" / "form-submissions"
    packages = tmp_path / "exports" / "export"
    tmp_dir.mkdir()
    fixtures.mkdir(parents=True)
    packages.mkdir(parents=True)
    (tmp_dir / "backup.json").write_text('"note": "TODO archived planning note"\n', encoding="utf-8")
    (fixtures / "sample.json").write_text('"note": "TODO sample fixture"\n', encoding="utf-8")
    (packages / "settings.json").write_text('"note": "FIXME exported package text"\n', encoding="utf-8")

    items = scan_todos(tmp_path)

    assert [(item.file, item.category, item.priority, item.reason) for item in items] == [
        ("tmp/backup.json", "generated", "low", "fixture, package, or temporary artifact"),
        ("fixtures/form-submissions/sample.json", "generated", "low", "fixture, package, or temporary artifact"),
        ("exports/export/settings.json", "generated", "low", "generated defect marker"),
    ]


def test_scan_todos_splits_historical_and_backlog_docs(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "release-changelog.md").write_text("FIXME: old release note\n", encoding="utf-8")
    (docs / "active-todo.md").write_text("TODO: active backlog item\n", encoding="utf-8")
    (docs / "feature-notes.md").write_text("TODO: explain usage\n", encoding="utf-8")

    items = scan_todos(tmp_path)

    expected = [
        ("docs/release-changelog.md", "historical", "low", "historical defect marker"),
        ("docs/active-todo.md", "backlog", "medium", "active backlog or planning document"),
        ("docs/feature-notes.md", "documentation", "low", "documentation note or backlog reference"),
    ]
    assert sorted((item.file, item.category, item.priority, item.reason) for item in items) == sorted(expected)


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


def test_scan_secrets_uses_config_ignored_path_prefixes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("API_KEY='real-value'\n", encoding="utf-8")
    ignored = tmp_path / "public" / "assets"
    ignored.mkdir(parents=True)
    (ignored / "bundle.js").write_text("TOKEN='generated-token-value'\n", encoding="utf-8")
    config = ProjectDoctorConfig(secret_ignored_path_prefixes=["public"])

    findings = scan_secrets(tmp_path, config)

    assert [(item.file, item.key) for item in findings] == [("src/app.py", "API_KEY")]


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


def test_scan_secrets_ignores_token_variable_code_references(tmp_path):
    (tmp_path / "script.py").write_text(
        "\n".join(
            [
                "def __init__(self, token: str):",
                "force_refresh_token=False,",
                "TOKEN_ENDPOINT_TEMPLATE = 'https://login.example.test/token'",
                "monthTokens = ['jan', 'feb', 'mar']",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "script.js").write_text(
        "\n".join(
            [
                "const hasMonth = monthTokens.some(token => lowered.includes(token));",
                "function inspect(token) { return token; }",
            ]
        ),
        encoding="utf-8",
    )

    assert scan_secrets(tmp_path) == []


def test_scan_secrets_still_flags_real_code_token_assignment(tmp_path):
    (tmp_path / "script.py").write_text("access_token='real-looking-value'\n", encoding="utf-8")

    findings = scan_secrets(tmp_path)

    assert len(findings) == 1
    assert findings[0].key == "access_token"
