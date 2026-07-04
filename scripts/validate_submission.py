#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("::error::PyYAML is required. Install with: python -m pip install pyyaml")
    sys.exit(2)

ROOT = Path.cwd()
POLICY_PATH = ROOT / ".github" / "submission-policy.yml"


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True, cwd=ROOT).strip()


def error(message: str, file: str | None = None) -> None:
    if file:
        print(f"::error file={file}::{message}")
    else:
        print(f"::error::{message}")


def warning(message: str, file: str | None = None) -> None:
    if file:
        print(f"::warning file={file}::{message}")
    else:
        print(f"::warning::{message}")


def load_policy() -> dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def tracked_files() -> list[str]:
    out = run_git(["ls-files"])
    return [line for line in out.splitlines() if line]


def changed_files() -> list[str]:
    base_sha = os.environ.get("BASE_SHA", "").strip()
    if base_sha:
        try:
            out = run_git(["diff", "--name-only", f"{base_sha}...HEAD"])
            return [line for line in out.splitlines() if line]
        except subprocess.CalledProcessError:
            warning("Could not compute PR diff; falling back to all tracked files.")
    return tracked_files()


def get_team_folder(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) >= 2 and parts[0] == "projects" and parts[1] != ".gitkeep":
        return parts[1]
    return None


def get_nested_value(data: Any, dotted: str) -> Any:
    cur = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    return False


def validate_submodules() -> list[str]:
    failures: list[str] = []

    if (ROOT / ".gitmodules").exists():
        error("Do not submit projects as git submodules. Remove .gitmodules.", ".gitmodules")
        failures.append(".gitmodules exists")

    ls_files_s = run_git(["ls-files", "-s"])
    for line in ls_files_s.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "160000":
            path = parts[3]
            error("Submodule/gitlink entry detected. Remove nested .git metadata and re-add real files.", path)
            failures.append(f"gitlink: {path}")

    for nested in (ROOT / "projects").rglob(".git"):
        rel = str(nested.relative_to(ROOT))
        error("Nested .git metadata is not allowed in submissions.", rel)
        failures.append(f"nested git: {rel}")

    return failures


def validate_forbidden_paths(policy: dict[str, Any], files: list[str]) -> list[str]:
    failures: list[str] = []
    patterns = [re.compile(p) for p in policy.get("forbidden_path_patterns", [])]
    for path in files:
        for pat in patterns:
            if pat.search(path):
                error("Forbidden file/folder path detected.", path)
                failures.append(f"forbidden path: {path}")
                break
    return failures


def validate_file_sizes(policy: dict[str, Any], files: list[str]) -> list[str]:
    failures: list[str] = []
    max_mb = float(policy.get("max_file_size_mb", 50))
    max_bytes = int(max_mb * 1024 * 1024)
    for path in files:
        full = ROOT / path
        if full.is_file() and full.stat().st_size > max_bytes:
            error(f"File is larger than {max_mb:g} MB.", path)
            failures.append(f"large file: {path}")
    return failures


def heading_exists(readme_text: str, section: str) -> bool:
    # Allows headings like '## 1. 프로젝트 소개' or '## 프로젝트 소개'.
    pattern = re.compile(rf"^#+\s*(?:\d+\.\s*)?{re.escape(section)}\s*$", re.MULTILINE)
    return bool(pattern.search(readme_text))


def validate_team_folder(policy: dict[str, Any], folder: str) -> list[str]:
    failures: list[str] = []
    folder_path = ROOT / "projects" / folder
    folder_rel = f"projects/{folder}"

    pattern = re.compile(policy.get("team_folder_pattern", r"^team[0-9]{2}-[a-z0-9][a-z0-9-]*$"))
    if not pattern.match(folder):
        error("Team folder name must match teamNN-project-name, e.g. team01-newscatcher.", folder_rel)
        failures.append(f"bad folder name: {folder}")

    for required_file in policy.get("required_team_files", []):
        rel = f"{folder_rel}/{required_file}"
        if not (folder_path / required_file).is_file():
            error(f"Required team file is missing: {required_file}", rel)
            failures.append(f"missing file: {rel}")

    readme_path = folder_path / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        for section in policy.get("required_readme_sections", []):
            if not heading_exists(readme_text, section):
                error(f"Required README section is missing: {section}", str(readme_path.relative_to(ROOT)))
                failures.append(f"missing readme section: {section}")
        for section in policy.get("optional_readme_sections", []):
            if not heading_exists(readme_text, section):
                warning(f"Optional README section is missing: {section}", str(readme_path.relative_to(ROOT)))

    project_yml_path = folder_path / "project.yml"
    if project_yml_path.is_file():
        try:
            data = yaml.safe_load(project_yml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            error(f"project.yml is not valid YAML: {exc}", str(project_yml_path.relative_to(ROOT)))
            failures.append("invalid project.yml")
            data = {}
        for field in policy.get("required_project_yml_fields", []):
            if is_empty(get_nested_value(data, field)):
                error(f"Required project.yml field is missing or empty: {field}", str(project_yml_path.relative_to(ROOT)))
                failures.append(f"missing yml field: {field}")
        folder_name = get_nested_value(data, "team.folder_name")
        if folder_name and folder_name != folder:
            error(f"team.folder_name must match folder name: {folder}", str(project_yml_path.relative_to(ROOT)))
            failures.append("folder_name mismatch")

    return failures


def main() -> int:
    policy = load_policy()
    files = tracked_files()
    changed = changed_files()
    failures: list[str] = []

    failures.extend(validate_submodules())
    failures.extend(validate_forbidden_paths(policy, files))
    failures.extend(validate_file_sizes(policy, files))

    changed_team_folders = sorted({folder for path in changed if (folder := get_team_folder(path))})
    all_team_folders = sorted({folder for path in files if (folder := get_team_folder(path))})

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name == "pull_request" and policy.get("require_single_team_folder_per_pr", True):
        if len(changed_team_folders) == 0:
            error("PR must include a team folder under projects/.")
            failures.append("no team folder")
        elif len(changed_team_folders) > 1:
            error(f"PR must modify only one team folder. Found: {', '.join(changed_team_folders)}")
            failures.append("multiple team folders")

    target_folders = changed_team_folders if event_name == "pull_request" else all_team_folders
    for folder in target_folders:
        failures.extend(validate_team_folder(policy, folder))

    if failures:
        print("\nValidation failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Submission validation passed.")
    if target_folders:
        print("Validated team folders:")
        for folder in target_folders:
            print(f"- projects/{folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
