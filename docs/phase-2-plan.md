# Phase 2 Plan

Phase 2 starts with deeper local analysis while preserving the Phase 1 safety model for scanned repositories.

## Approved Phase 2 Slice

The first approved slices are richer documentation quality review and local scan history.

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

## Local Scan History

`project-doctor scan PATH` records a summary-only JSONL history entry by default.

Default location:

```text
~/.local/share/git-project-doctor/history
```

Users may opt out with:

```bash
project-doctor scan PATH --no-history
```

Users may choose a different local history directory with:

```bash
project-doctor scan PATH --history-dir /path/to/history
```

History entries include summary metadata only:

- scan timestamp
- repository path hash and repository name
- Git branch and dirty state
- health score
- documentation score
- detected stack
- TODO count
- possible secret count
- dependency file count
- test command count
- CI workflow count
- recommended next step text

History entries must not include source file contents, TODO text, or secret values.

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
