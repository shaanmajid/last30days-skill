"""Static checks for the .skill archive surface."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "last30days"

FORBIDDEN_SKILL_FILES = {
    ".gitattributes",
    "agents/openai.yaml",
    "assets/aging-portrait.jpeg",
    "assets/claude-code-rap.mp3",
    "assets/dog-as-human.png",
    "assets/dog-original.jpeg",
    "assets/swimmom-mockup.jpeg",
    "scripts/build-skill.sh",
    "scripts/compare.sh",
    "scripts/evaluate_search_quality.py",
    "scripts/test-v1-vs-v2.sh",
    "scripts/test_device_auth.py",
    "scripts/verify_v3.py",
}

EXPECTED_RUNTIME_FILES = {
    "SKILL.md",
    "scripts/last30days.py",
    "scripts/lib/env.py",
    "scripts/lib/pipeline.py",
}


def _git_env() -> dict[str, str]:
    env = {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    if home := os.environ.get("HOME"):
        env["HOME"] = home
    return env


def _git(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        env=_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def _is_export_ignored(path: str) -> bool:
    out = _git("check-attr", "export-ignore", "--", path, cwd=SKILL_ROOT).strip()
    return out.endswith(": export-ignore: set")


def _skill_archive_files() -> set[str]:
    files = _git("ls-files", "-z", ".", cwd=SKILL_ROOT).split("\0")
    return {path for path in files if path and not _is_export_ignored(path)}


def test_skill_archive_surface_excludes_non_runtime_helpers() -> None:
    archive_files = _skill_archive_files()

    assert archive_files.isdisjoint(FORBIDDEN_SKILL_FILES)


def test_skill_archive_surface_keeps_runtime_files() -> None:
    archive_files = _skill_archive_files()

    assert EXPECTED_RUNTIME_FILES <= archive_files


def test_repository_archive_marks_skill_helpers_export_ignored() -> None:
    for path in FORBIDDEN_SKILL_FILES - {".gitattributes"}:
        repo_path = f"skills/last30days/{path}"
        out = _git("check-attr", "export-ignore", "--", repo_path).strip()
        assert out.endswith(": export-ignore: set"), repo_path
