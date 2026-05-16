from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from project_doctor.models import ProjectReport


def write_json(path: Path, model: BaseModel | list[BaseModel] | dict) -> None:
    if isinstance(model, BaseModel):
        payload = model.model_dump(mode="json")
    elif isinstance(model, list):
        payload = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in model]
    else:
        payload = model
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_json_reports(report: ProjectReport, out_dir: Path) -> None:
    write_json(out_dir / "dependency_report.json", report.dependencies)
    write_json(out_dir / "docs_report.json", report.docs)
    write_json(out_dir / "todo_report.json", report.todos)
    write_json(out_dir / "secrets_report.json", report.secrets)
    write_json(out_dir / "git_status_report.json", report.git)
    write_json(out_dir / "test_ci_report.json", report.test_ci)
    write_json(out_dir / "repo_summary.json", report.summary)
