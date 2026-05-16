from __future__ import annotations

from pathlib import Path


def resolve_repo_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def relative_to_repo(path: Path, repo_path: Path) -> str:
    try:
        return path.relative_to(repo_path).as_posix()
    except ValueError:
        return path.as_posix()
