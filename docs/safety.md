# Safety Model

`git-project-doctor` Phase 1 is read-only with respect to the scanned target repository.

## What Phase 1 May Do

- Read files from the target repository.
- Ignore generated, dependency, cache, and report folders.
- Run safe read-only Git commands in the target repository.
- Write reports to the selected output directory.

## What Phase 1 Must Not Do

- Modify files in the target repository.
- Delete files from the target repository.
- Install packages in the target repository.
- Run Git write operations such as `push`, `pull`, `commit`, `reset`, `checkout`, or `merge`.
- Rewrite user code.
- Print secret values.
- Upload repository contents.
- Make network or API calls.

## Output Directory Rule

The default output directory is `./reports`, relative to the current working directory where the CLI is run. A user may choose another location with `--out`.

The scanner does not write into the scanned repository unless the user explicitly chooses an output path inside that repository.

## Secret Handling

Secret scanning is pattern-based and produces warnings, not proof that a value is a live credential.

When a possible secret is found, output must include only a redacted value, such as:

```text
API_KEY=...REDACTED
```

Generated reports, Codex context, and task packets must not include the original value.

## Ignored Paths

Scanners must ignore these folders anywhere in the target path:

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

Scanners also ignore local tool/cache prefixes such as:

- `.tools/bin`
- `.tools/cache`
- `.tools/local-state`
- `.tools/tmp`
