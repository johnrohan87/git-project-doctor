from __future__ import annotations

import subprocess

from project_doctor.scanners.git_scanner import scan_git


def test_scan_git_reports_non_repo(tmp_path):
    status = scan_git(tmp_path)

    assert status.is_git_repo is False
    assert "Not a Git repository" in status.errors


def test_scan_git_detects_untracked_file(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "new.txt").write_text("hello", encoding="utf-8")

    status = scan_git(tmp_path)

    assert status.is_git_repo is True
    assert status.dirty is True
    assert "new.txt" in status.untracked_files
