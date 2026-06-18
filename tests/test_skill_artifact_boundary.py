import os
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "last30days"
BUILD_SCRIPT = SKILL_ROOT / "scripts" / "build-skill.sh"


def _archive_members(archive_path: Path) -> set[str]:
    with zipfile.ZipFile(archive_path) as archive:
        return set(archive.namelist())


def _skillignore_patterns() -> list[str]:
    patterns = []
    for line in (SKILL_ROOT / ".skillignore").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def test_skill_artifact_excludes_non_runtime_surface(tmp_path: Path) -> None:
    archive_path = tmp_path / "last30days.skill"

    subprocess.run(
        ["bash", str(BUILD_SCRIPT)],
        check=True,
        env={
            "HOME": str(tmp_path),
            "LAST30DAYS_SKILL_OUT": str(archive_path),
            "PATH": os.environ.get("PATH", ""),
        },
        cwd=ROOT,
    )

    members = _archive_members(archive_path)

    assert "last30days/.skillignore" not in members
    for pattern in _skillignore_patterns():
        archive_pattern = f"last30days/{pattern}"
        if pattern.endswith("/"):
            assert not any(member.startswith(archive_pattern) for member in members)
        else:
            assert archive_pattern not in members

    assert "last30days/SKILL.md" in members
    assert "last30days/scripts/last30days.py" in members
    assert "last30days/scripts/lib/env.py" in members
