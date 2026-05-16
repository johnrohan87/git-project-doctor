from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from project_doctor.models import ProjectReport


@dataclass(frozen=True)
class TaskPacket:
    slug: str
    title: str
    context: list[str]
    rules: list[str]
    acceptance: list[str]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:70] or "task"


def build_task_packets(report: ProjectReport) -> list[TaskPacket]:
    packets: list[TaskPacket] = []
    stack = ", ".join(report.summary.detected_stack) or "Unknown"

    if not report.docs.has_readme or not report.docs.documents_package_scripts_or_commands:
        packets.append(
            TaskPacket(
                slug="fix-readme-setup-instructions",
                title="Fix README setup instructions",
                context=[
                    f"This repo appears to be: {stack}.",
                    f"README present: {report.docs.has_readme}.",
                    f"Setup keywords found: {', '.join(report.docs.setup_keywords_found) or 'none'}.",
                    f"Package scripts detected: {', '.join(report.dependencies.scripts) or 'none'}.",
                ],
                rules=[
                    "Update documentation only.",
                    "Do not change application code.",
                    "Do not commit, push, pull, reset, checkout, or merge.",
                    "Do not add real secret values.",
                ],
                acceptance=[
                    "README includes install instructions.",
                    "README includes run instructions.",
                    "README includes test instructions when a test command exists.",
                    "README documents required environment variables with placeholders only.",
                ],
            )
        )

    if not report.docs.has_env_example:
        packets.append(
            TaskPacket(
                slug="add-env-example",
                title="Add .env.example placeholders",
                context=[
                    f"This repo appears to be: {stack}.",
                    ".env.example was not detected.",
                    "Secret values must never be copied from local environment files.",
                ],
                rules=[
                    "Create or update .env.example only.",
                    "Use placeholder values.",
                    "Do not inspect or expose real credentials.",
                    "Do not change runtime configuration logic.",
                ],
                acceptance=[
                    ".env.example exists.",
                    "Every value is a placeholder.",
                    "README references the environment setup if README exists.",
                ],
            )
        )

    if report.todos:
        top_items = [f"{item.file}:{item.line} [{item.tag}] {item.text}" for item in report.todos[:10]]
        packets.append(
            TaskPacket(
                slug="review-todo-fixme-comments",
                title="Review TODO/FIXME comments",
                context=[
                    f"{len(report.todos)} TODO/FIXME/HACK/BUG/REVIEW comments were found.",
                    "Top findings:",
                    *top_items,
                ],
                rules=[
                    "Start with review and classification.",
                    "Do not make broad refactors.",
                    "Do not remove TODO comments unless the underlying issue is actually resolved.",
                    "Do not commit unless explicitly requested.",
                ],
                acceptance=[
                    "TODO items are grouped into actionable categories.",
                    "Resolved TODOs include focused code or documentation changes.",
                    "Deferred TODOs have a clear reason.",
                ],
            )
        )

    if report.secrets:
        findings = [
            f"{item.file}:{item.line} `{item.key}` [{item.severity}] {item.reason}: {item.redacted_text}"
            for item in report.secrets[:10]
        ]
        packets.append(
            TaskPacket(
                slug="review-possible-secret-findings",
                title="Review possible secret findings",
                context=[
                    f"{len(report.secrets)} possible secret findings were detected by pattern.",
                    "Values are redacted in this packet.",
                    *findings,
                ],
                rules=[
                    "Do not print, copy, or commit secret values.",
                    "Treat findings as warnings until manually confirmed.",
                    "Rotate credentials if a real secret was committed.",
                    "Do not rewrite Git history unless explicitly approved.",
                ],
                acceptance=[
                    "Each finding is classified as real secret, placeholder, or false positive.",
                    "Real exposed credentials have a rotation plan.",
                    "Safe placeholder examples remain documented.",
                ],
            )
        )

    if not report.test_ci.test_commands:
        packets.append(
            TaskPacket(
                slug="define-local-test-command",
                title="Define local test command",
                context=[
                    f"This repo appears to be: {stack}.",
                    "No obvious local test command was detected.",
                    f"Detected config files: {', '.join(report.test_ci.config_files) or 'none'}.",
                    f"Package scripts detected: {', '.join(report.dependencies.scripts) or 'none'}.",
                ],
                rules=[
                    "Start by identifying the intended test framework.",
                    "Do not install dependencies or change lockfiles without approval.",
                    "Prefer documenting an existing command before adding a new tool.",
                    "Do not commit unless explicitly requested.",
                ],
                acceptance=[
                    "The repo has a clear local test command.",
                    "The command is documented in README or package metadata.",
                    "The command can be run by a future coding agent before and after changes.",
                ],
            )
        )

    if report.test_ci.test_commands and not report.test_ci.ci_workflows:
        packets.append(
            TaskPacket(
                slug="add-ci-workflow-plan",
                title="Plan GitHub Actions workflow",
                context=[
                    f"This repo appears to be: {stack}.",
                    "No GitHub Actions workflow was detected.",
                    "Detected local test commands:",
                    *report.test_ci.test_commands,
                ],
                rules=[
                    "Prepare a CI plan before adding workflow files.",
                    "Do not add secrets to workflow files.",
                    "Do not enable deployment steps without explicit approval.",
                    "Keep the first workflow focused on install and test only.",
                ],
                acceptance=[
                    "The intended CI trigger is clear.",
                    "The install command is identified.",
                    "The test command is identified.",
                    "Deployment and publishing are explicitly out of scope.",
                ],
            )
        )

    if report.git.dirty:
        packets.append(
            TaskPacket(
                slug="review-dirty-working-tree",
                title="Review dirty working tree before changes",
                context=[
                    f"Modified files: {len(report.git.modified_files)}.",
                    f"Untracked files: {len(report.git.untracked_files)}.",
                    "Current branch: " + (report.git.branch or "unknown"),
                ],
                rules=[
                    "Do not overwrite existing local changes.",
                    "Inspect changed files before editing them.",
                    "Do not reset, checkout, stash, or clean without explicit approval.",
                ],
                acceptance=[
                    "User-owned changes are identified.",
                    "Any planned edits avoid unrelated modified files.",
                    "Risky Git operations are not used.",
                ],
            )
        )

    if not packets:
        packets.append(
            TaskPacket(
                slug="plan-next-maintenance-pass",
                title="Plan next maintenance pass",
                context=[
                    f"This repo appears to be: {stack}.",
                    f"Health score: {report.summary.health_score} / 100.",
                    "No urgent Phase 1 issues were detected.",
                ],
                rules=[
                    "Keep the next task scoped.",
                    "Do not introduce automated writes without approval.",
                    "Prefer tests or documentation improvements before larger changes.",
                ],
                acceptance=[
                    "A small next task is selected.",
                    "The task has clear files in scope.",
                    "The task has a verification command.",
                ],
            )
        )

    return packets


def render_task_packet(packet: TaskPacket, index: int) -> str:
    return "\n".join(
        [
            f"# Task {index}: {packet.title}",
            "",
            "## Context",
            "",
            *[f"- {line}" for line in packet.context],
            "",
            "## Rules",
            "",
            *[f"- {line}" for line in packet.rules],
            "",
            "## Acceptance Criteria",
            "",
            *[f"- {line}" for line in packet.acceptance],
            "",
        ]
    )


def write_task_packets(report: ProjectReport, out_dir: Path) -> list[Path]:
    task_dir = out_dir / "task_packets"
    task_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, packet in enumerate(build_task_packets(report), start=1):
        path = task_dir / f"{index:02d}-{_slugify(packet.slug)}.md"
        path.write_text(render_task_packet(packet, index), encoding="utf-8")
        written.append(path)
    return written
