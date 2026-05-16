# Phase 2 Plan

Phase 2 starts with deeper local analysis while preserving the Phase 1 safety model for scanned repositories.

## Approved Phase 2 Slice

The first approved slice is richer documentation quality review.

This slice may:

- inspect README structure
- detect recommended README sections
- score documentation completeness
- include documentation quality fields in JSON, Markdown, CLI, and Codex context output

This slice must not:

- modify scanned repositories
- install packages in scanned repositories
- make network or API calls
- create GitHub issues or pull requests
- call AI APIs
- add database storage
- implement auto-fix behavior

## Documentation Review Signals

The docs scanner should report:

- whether `README.md` exists
- whether `.env.example`, `CHANGELOG.md`, `LICENSE`, and `docs/` exist
- README line count
- README headings
- missing recommended sections:
  - setup
  - usage
  - testing
  - configuration
- documentation score from 0 to 100

## Future Phase 2 Candidates

These still require explicit approval before implementation:

- local scan history storage
- dependency freshness checks
- GitHub issue or pull request creation
- AI-assisted summaries
- dashboard UI
- auto-fix commands
