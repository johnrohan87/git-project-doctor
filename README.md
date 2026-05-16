# git-project-doctor

`git-project-doctor` is a local-first CLI for reviewing software repositories and generating update-planning reports. Phase 1 is read-only: it scans local files and safe Git metadata, then writes reports outside the scanned repo unless you explicitly point `--out` there.

## What It Generates

- Repo health report
- Dependency report
- README/documentation report
- TODO/FIXME report
- Git status report
- Security/secrets warning report with redacted values
- Recommended next steps
- Codex/Cline context file
- Codex/Cline task packets
- Test runner, CI workflow, and Dockerfile detection

## Install Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Example Commands

```bash
project-doctor scan .
project-doctor scan ~/Documents/VSCodeProjects/Pirates_Babylon
project-doctor scan . --out ./reports
project-doctor git-status .
project-doctor todos .
project-doctor docs .
project-doctor test-ci .
project-doctor codex-context .
project-doctor task-packets .
project-doctor history .
```

## Report Files

By default, `project-doctor scan PATH` writes:

```text
reports/
├── project_report.md
├── dependency_report.json
├── docs_report.json
├── todo_report.json
├── secrets_report.json
├── git_status_report.json
├── test_ci_report.json
├── repo_summary.json
├── repo_summary.md
├── codex_context.md
└── task_packets/
    └── 01-example-task.md
```

## Phase 1 Limitations

- No dependency freshness checks against the internet
- No package installation
- No Git write operations
- No repository modifications
- No AI API calls
- No database or scan history
- No web dashboard

## Task Packets

`project-doctor task-packets PATH` generates scoped Markdown prompts for Codex or Cline. Packets are based on scan findings, include task-specific rules, and are written under `reports/task_packets/`.

The generator remains read-only with respect to the scanned repository.

## Safety Model

The scanner ignores large or generated folders such as `.git`, `node_modules`, `dist`, `build`, `.venv`, `env`, `__pycache__`, `.cache`, `coverage`, and `reports`.

Possible secrets are detected by pattern only and values are redacted in output.

See [docs/safety.md](docs/safety.md) for the full Phase 1 safety contract.

## Phase 1 Completion

See [docs/phase-1-completion.md](docs/phase-1-completion.md) for the completion checklist, required report outputs, and remaining low-risk work.

## Phase 2

Phase 2 begins with richer local documentation quality review while preserving read-only scanned-repo behavior. See [docs/phase-2-plan.md](docs/phase-2-plan.md).

`project-doctor scan PATH` also records summary-only scan history by default under:

```text
~/.local/share/git-project-doctor/history
```

Use `--no-history` to skip history writes, or `--history-dir PATH` to choose a different local history directory.

To compare the latest two scans:

```bash
project-doctor history PATH --diff
```

## Project Config

`project-doctor` can read optional repo-specific configuration from `.project-doctor.toml` in the scanned repo, or from an explicit path:

```bash
project-doctor scan PATH --config /path/to/project-doctor.toml
```

Example:

```toml
profile = "custom"

[todos]
generated_path_prefixes = ["exports", "snapshots"]
historical_doc_markers = ["decision-log"]
backlog_doc_markers = ["active-plan", "next-steps"]
```

When `profile = "custom"` is set, health scoring uses custom-oriented signals and does not penalize missing package files, package test commands, or CI workflows by default. The active profile is included in summaries, markdown context, and scan history as structured metadata.

Example custom profile configs are available in [docs/examples](docs/examples):

- [Example Project](docs/examples/example-project.project-doctor.toml)
- [Example Project](docs/examples/example-project.project-doctor.toml)
- [Example Project](docs/examples/example-project.project-doctor.toml)

Use an external `--out` path when scanning active work repos to keep the scanned repo unchanged:

```bash
project-doctor scan ~/Documents/VSCodeProjects/example-project \
  --config docs/examples/example-project.project-doctor.toml \
  --out /tmp/project-doctor-reports/example-project

project-doctor scan ~/Documents/VSCodeProjects/"Example Project" \
  --config docs/examples/example-project.project-doctor.toml \
  --out /tmp/project-doctor-reports/example-project

project-doctor scan ~/Documents/VSCodeProjects/Example Project \
  --config docs/examples/example-project.project-doctor.toml \
  --out /tmp/project-doctor-reports/example-project
```

## Release Notes

See [CHANGELOG.md](CHANGELOG.md) for release notes and unreleased changes.

## Test

```bash
pytest
```

The test suite includes scanner tests, reporter tests, CLI integration tests, and fixture-based scans for small Python and Node repositories.

## Roadmap

Future phases require explicit approval before implementation:

- GitHub issue creation
- Dependency freshness checks
- Renovate config generator
- README auto-draft
- Dockerfile review
- GitHub Actions review
- Test runner detection
- AI-assisted repo summary
- React dashboard
- SQLite scan history
- Safe autofix mode
