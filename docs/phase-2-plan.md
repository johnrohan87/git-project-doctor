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

Users may compare the latest two scans with:

```bash
project-doctor history PATH --diff
```

The comparison reports score deltas, finding-count deltas, Git state changes, stack changes, and recommended-next-step changes.

## Local Tool Cache Ignore Refinement

Phase 2 also expands scanner ignores for local tool artifacts that create noisy TODO and possible-secret findings:

- `.tools/bin`
- `.tools/cache`
- `.tools/local-state`
- `.tools/tmp`

These paths are treated as generated/local state and are skipped by file scanners.

## Possible Secret Classification

Possible secret findings include:

- `severity`: `high`, `medium`, or `low`
- `reason`: a short explanation of why that severity was assigned

Classification is heuristic and does not expose secret values.

Initial rules:

- configuration-style files such as `.env`, YAML, JSON, TOML, INI, and CFG are high severity
- source code assignments are medium severity
- documentation examples are low severity
- token/cache path variables are low severity
- code syntax references such as type annotations, arrow parameters, endpoint template constants, and refresh-token control flags are ignored as false positives
- known non-secret token-like names such as `monthTokens` are ignored as false positives

## TODO Triage Classification

TODO findings include:

- `category`: `source`, `script`, `test`, `documentation`, or `other`
- `priority`: `high`, `medium`, or `low`
- `reason`: a short explanation of the classification

Initial rules:

- documentation TODOs are low priority unless they are `FIXME` or `BUG`
- source `FIXME` and `BUG` markers are high priority
- script and test follow-ups are medium priority by default
- fixture, package, and temporary artifact TODOs are `generated` category and low priority
- `HACK` and `REVIEW` markers are medium priority

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
