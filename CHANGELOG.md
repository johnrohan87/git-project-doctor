# Changelog

All notable changes to `git-project-doctor` will be documented in this file.

## Unreleased

- Added local summary-only scan history with a `project-doctor history` command.
- Started Phase 2 with richer documentation quality scoring.
- Added Phase 1 safety and completion documentation.
- Added JSON outputs for documentation and possible secret findings.
- Added CLI integration coverage for public Phase 1 commands.
- Added fixture-based end-to-end scans for Python and Node repositories.
- Added placeholder-aware secret scanning to reduce obvious false positives.
- Added GitHub Actions test workflow.

## 0.1.0

- Initial public Phase 1 CLI.
- Added read-only scanners for Git status, dependencies, docs, TODOs, possible secrets, project structure, and test/CI signals.
- Added Markdown, JSON, Codex context, and task packet report outputs.
