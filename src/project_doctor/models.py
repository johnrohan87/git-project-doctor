from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class GitStatus(BaseModel):
    is_git_repo: bool = False
    branch: str | None = None
    dirty: bool = False
    modified_files: list[str] = Field(default_factory=list)
    untracked_files: list[str] = Field(default_factory=list)
    remote_origin: str | None = None
    last_commit: str | None = None
    errors: list[str] = Field(default_factory=list)


class DependencyReport(BaseModel):
    files_found: list[str] = Field(default_factory=list)
    package_manager_locks: list[str] = Field(default_factory=list)
    dependencies: dict[str, list[str]] = Field(default_factory=dict)
    scripts: dict[str, str] = Field(default_factory=dict)


class DocsReport(BaseModel):
    has_readme: bool = False
    has_env_example: bool = False
    has_changelog: bool = False
    has_license: bool = False
    has_docs_folder: bool = False
    setup_keywords_found: list[str] = Field(default_factory=list)
    documents_package_scripts_or_commands: bool = False
    notes: list[str] = Field(default_factory=list)


class TodoItem(BaseModel):
    file: str
    line: int
    tag: str
    text: str


class SecretFinding(BaseModel):
    file: str
    line: int
    key: str
    redacted_text: str


class StructureReport(BaseModel):
    project_types: list[str] = Field(default_factory=list)
    important_folders: list[str] = Field(default_factory=list)
    important_files: list[str] = Field(default_factory=list)


class RepoSummary(BaseModel):
    path: Path
    name: str
    detected_stack: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    health_score: int = 0


class ProjectReport(BaseModel):
    summary: RepoSummary
    git: GitStatus
    dependencies: DependencyReport
    docs: DocsReport
    todos: list[TodoItem] = Field(default_factory=list)
    secrets: list[SecretFinding] = Field(default_factory=list)
    structure: StructureReport

    def to_jsonable(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
