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
    readme_line_count: int = 0
    readme_sections: list[str] = Field(default_factory=list)
    missing_recommended_sections: list[str] = Field(default_factory=list)
    documentation_score: int = 0
    setup_keywords_found: list[str] = Field(default_factory=list)
    documents_package_scripts_or_commands: bool = False
    notes: list[str] = Field(default_factory=list)


class TodoItem(BaseModel):
    file: str
    line: int
    tag: str
    text: str
    category: str = "source"
    priority: str = "medium"
    reason: str = "source TODO"


class SecretFinding(BaseModel):
    file: str
    line: int
    key: str
    redacted_text: str
    severity: str = "medium"
    reason: str = "secret-like assignment"


class StructureReport(BaseModel):
    project_types: list[str] = Field(default_factory=list)
    important_folders: list[str] = Field(default_factory=list)
    important_files: list[str] = Field(default_factory=list)


class TestCiReport(BaseModel):
    test_runners: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    package_script_commands: dict[str, str] = Field(default_factory=dict)
    ci_workflows: list[str] = Field(default_factory=list)
    docker_files: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RepoSummary(BaseModel):
    path: Path
    name: str
    detected_stack: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    health_score: int = 0


class ScanHistoryEntry(BaseModel):
    schema_version: int = 1
    scanned_at: str
    repo_path: str
    repo_hash: str
    repo_name: str
    branch: str | None = None
    is_git_repo: bool = False
    dirty: bool = False
    health_score: int = 0
    documentation_score: int = 0
    detected_stack: list[str] = Field(default_factory=list)
    todo_count: int = 0
    possible_secret_count: int = 0
    dependency_file_count: int = 0
    test_command_count: int = 0
    ci_workflow_count: int = 0
    recommended_next_steps: list[str] = Field(default_factory=list)


class ScanHistoryDelta(BaseModel):
    previous_scanned_at: str
    current_scanned_at: str
    health_score_delta: int = 0
    documentation_score_delta: int = 0
    todo_count_delta: int = 0
    possible_secret_count_delta: int = 0
    dependency_file_count_delta: int = 0
    test_command_count_delta: int = 0
    ci_workflow_count_delta: int = 0
    dirty_changed: bool = False
    branch_changed: bool = False
    stack_added: list[str] = Field(default_factory=list)
    stack_removed: list[str] = Field(default_factory=list)
    new_recommended_next_steps: list[str] = Field(default_factory=list)
    resolved_recommended_next_steps: list[str] = Field(default_factory=list)


class ProjectReport(BaseModel):
    summary: RepoSummary
    git: GitStatus
    dependencies: DependencyReport
    docs: DocsReport
    todos: list[TodoItem] = Field(default_factory=list)
    secrets: list[SecretFinding] = Field(default_factory=list)
    structure: StructureReport
    test_ci: TestCiReport = Field(default_factory=TestCiReport)

    def to_jsonable(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
