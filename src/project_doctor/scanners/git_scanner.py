from __future__ import annotations

import subprocess
from pathlib import Path

from project_doctor.models import GitStatus


def _run_git(repo_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )


def scan_git(repo_path: Path) -> GitStatus:
    result = GitStatus()
    inside = _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        result.errors.append("Not a Git repository")
        return result

    result.is_git_repo = True

    branch = _run_git(repo_path, ["branch", "--show-current"])
    if branch.returncode == 0:
        result.branch = branch.stdout.strip() or None

    status = _run_git(repo_path, ["status", "--porcelain"])
    if status.returncode == 0:
        for raw_line in status.stdout.splitlines():
            if not raw_line:
                continue
            code = raw_line[:2]
            file_path = raw_line[3:].strip()
            result.dirty = True
            if code == "??":
                result.untracked_files.append(file_path)
            else:
                result.modified_files.append(file_path)

    remote = _run_git(repo_path, ["remote", "get-url", "origin"])
    if remote.returncode == 0:
        result.remote_origin = remote.stdout.strip() or None

    commit = _run_git(repo_path, ["log", "-1", "--oneline"])
    if commit.returncode == 0:
        result.last_commit = commit.stdout.strip() or None

    return result
