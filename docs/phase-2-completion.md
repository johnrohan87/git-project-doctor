# Phase 2 Completion Checklist

Phase 2 is complete when the approved local-only analysis improvements are implemented, covered by tests, and still preserve the read-only scanned-repository safety contract.

## Completed Scope

- Richer README and documentation scoring.
- Local summary-only scan history with latest-scan diff output.
- Local tool cache ignore refinement for noisy generated artifacts.
- Possible-secret severity and reason classification.
- TODO category, priority, and reason classification.
- Optional `.project-doctor.toml` / `--config` support for local scanner tuning.

## Required Safety Properties

- Scans do not modify the target repository unless the user explicitly chooses an output path inside it.
- Possible secret values are redacted in reports, Codex context, task packets, and summaries.
- History entries do not include source file contents, TODO text, possible secret values, or full local repository paths.
- Future features that modify repositories, call APIs, create GitHub resources, use AI, or add database storage remain out of scope until separately approved.

## Required Validation

- Unit and CLI tests pass locally.
- GitHub Actions passes on the release commit.
- Wheel and sdist builds pass.
- Built distributions include `project_doctor/py.typed`.
- Wheel install smoke test exposes `project-doctor --help`.

## Out Of Scope Until Approved

- Dependency freshness checks.
- GitHub issue or pull request creation.
- AI-assisted summaries.
- Dashboard UI.
- Auto-fix behavior.
- Database-backed scan history.
