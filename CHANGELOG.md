# Changelog

All notable changes to `git-project-doctor` will be documented in this file.

## Unreleased

- Added a production-readiness review of remaining phase gates.
- Added the `py.typed` package marker to match the typed-package classifier.
- Clarified local scan history documentation now that summary-only history is implemented.

## 0.2.2 - 2026-05-17

- Added release-readiness hardening for packaging, license metadata, CI packaging checks, and grouped report summaries.
- Reduced additional possible-secret false positives for token-like source syntax and UI text.
- Added stronger markdown and JSON reporter coverage for large finding sets.

## 0.2.1 - 2026-05-17

- Added a public-content guard test to catch customer-specific notes before release.
- Added grouped TODO and possible-secret summary output for large scan reports.
- Reduced possible-secret false positives for token-handling source expressions, comments, JSX labels, and console log messages.
- Added config-driven secret scan ignored path prefixes for generated artifacts.

## 0.2.0 - 2026-05-17

- Added structured profile metadata to summaries, markdown context, and scan history.
- Added optional `.project-doctor.toml` / `--config` support for repo-specific TODO classification.
- Split documentation TODOs into backlog, historical, and general documentation categories.
- Added category, priority, and reason classification for TODO findings.
- Classified fixture, package, and temporary TODO findings as generated artifacts.
- Reduced possible-secret false positives for token variable syntax and endpoint/control-flag references.
- Added severity and reason classification for possible secret findings.
- Reduced scan noise by ignoring local `.tools` cache/state prefixes.
- Added latest-scan comparison with `project-doctor history PATH --diff`.
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
