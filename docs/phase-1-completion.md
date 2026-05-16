# Phase 1 Completion Checklist

Phase 1 is complete when the public CLI can scan common local repositories, generate useful reports, and preserve the read-only safety contract.

## Required Commands

These commands must remain available:

```bash
project-doctor scan PATH
project-doctor git-status PATH
project-doctor todos PATH
project-doctor docs PATH
project-doctor test-ci PATH
project-doctor codex-context PATH
project-doctor task-packets PATH
```

## Required Report Outputs

`project-doctor scan PATH` should generate:

- `project_report.md`
- `repo_summary.md`
- `repo_summary.json`
- `dependency_report.json`
- `docs_report.json`
- `todo_report.json`
- `secrets_report.json`
- `git_status_report.json`
- `test_ci_report.json`
- `codex_context.md`
- one or more task packet Markdown files under `task_packets/`

## Required Coverage

Phase 1 includes tests for:

- scanner behavior
- reporter behavior
- public CLI commands
- invalid path handling
- custom output directory handling
- redacted secret reporting
- ignored generated and dependency folders
- fixture-based end-to-end scans for small Python and Node repositories
- exact report output file contracts
- meaningful CLI subcommand output from fixture repositories
- placeholder handling for possible secret findings

## Remaining Low-Risk Improvements

The safest remaining work before calling Phase 1 complete is:

1. Review the first GitHub Actions run after pushing.
2. Decide whether to tag the current Phase 1 state as `v0.1.0`.

## Out Of Scope Until Approved

These remain future-phase items:

- automated dependency updates
- GitHub issue or pull request creation
- AI API integration
- database storage
- React dashboard
- auto-fix commands
- any command that modifies scanned repositories
