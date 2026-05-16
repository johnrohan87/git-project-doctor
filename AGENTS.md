# AGENTS.md

## Project

This project is called `git-project-doctor`.

It is a local-first Git project review and update planning tool. Its purpose is to scan software repositories and generate clear reports about repo health, documentation, dependencies, TODOs, Git state, possible secrets, and recommended next steps.

## Current phase

Phase 1 is read-only.

The tool may inspect files and run safe read-only commands, but it must not modify the target repository.

## Hard safety rules

Do not:

- Modify files in the scanned repository
- Delete files
- Install packages in the scanned repository
- Run `git push`
- Run `git pull`
- Run `git commit`
- Run `git reset`
- Run `git checkout`
- Run `git merge`
- Rewrite user code
- Print secret values
- Upload repository contents anywhere
- Make internet/API calls unless a future approved phase explicitly allows it

## Allowed Git commands

Read-only commands only, such as:

```bash
git status --short
git branch --show-current
git remote -v
git log -1 --oneline
```

## Ignored folders

Always ignore:

- `.git`
- `node_modules`
- `dist`
- `build`
- `.venv`
- `venv`
- `env`
- `__pycache__`
- `.cache`
- `coverage`
- `reports`

## Output behavior

Reports should be written to an output folder, defaulting to:

```text
./reports
```

The target repo should not be changed.

## Secret handling

If a possible secret is found, redact it.

Correct:

```text
API_KEY=...REDACTED
```

Incorrect:

```text
API_KEY=actual-secret-value
```

## Preferred implementation style

Use:

- Small focused modules
- Clear scanner classes or functions
- Pydantic models for report data
- Typer for CLI commands
- Rich for readable terminal output
- Unit tests for scanner behavior

## Phase 1 deliverables

The project should support:

```bash
project-doctor scan PATH
project-doctor git-status PATH
project-doctor todos PATH
project-doctor docs PATH
project-doctor codex-context PATH
project-doctor task-packets PATH
```

## Future phases require approval

Do not implement these without explicit approval:

- Automated dependency updates
- GitHub issue creation
- GitHub PR creation
- AI API integration
- Database storage
- React dashboard
- Auto-fix commands
- Repository file modifications
