from __future__ import annotations

import re
from pathlib import Path

from project_doctor.config import TODO_TAGS
from project_doctor.models import TodoItem
from project_doctor.utils.file_utils import is_probably_text, iter_files, read_text_safely
from project_doctor.utils.path_utils import relative_to_repo

TAG_RE = re.compile(r"\b(" + "|".join(TODO_TAGS) + r")\b", re.IGNORECASE)


def scan_todos(repo_path: Path) -> list[TodoItem]:
    items: list[TodoItem] = []
    for path in iter_files(repo_path):
        if not is_probably_text(path):
            continue
        for line_number, line in enumerate(read_text_safely(path).splitlines(), start=1):
            match = TAG_RE.search(line)
            if match:
                items.append(
                    TodoItem(
                        file=relative_to_repo(path, repo_path),
                        line=line_number,
                        tag=match.group(1).upper(),
                        text=line.strip()[:300],
                    )
                )
    return items
