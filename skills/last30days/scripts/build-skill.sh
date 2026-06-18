#!/usr/bin/env bash
# build-skill.sh - package this repo as a claude.ai-upload-ready .skill file
# Usage: bash skills/last30days/scripts/build-skill.sh  (run from repo root)
#
# Produces dist/last30days.skill, a zip with a single top-level `last30days/`
# directory containing SKILL.md and the scripts/ runtime from skills/last30days.
# See
# docs/plans/2026-04-14-001-fix-skill-upload-200-file-limit-plan.md.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO_ROOT"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "error: working tree is dirty; commit or stash before building" >&2
  exit 1
fi

mkdir -p dist
OUT="${LAST30DAYS_SKILL_OUT:-dist/last30days.skill}"
case "$OUT" in
  /*) OUT_PATH="$OUT" ;;
  *) OUT_PATH="$REPO_ROOT/$OUT" ;;
esac
mkdir -p "$(dirname "$OUT_PATH")"

git archive --format=zip --prefix=last30days/ --output="$OUT_PATH" HEAD:skills/last30days

python3 - "$OUT_PATH" skills/last30days/.skillignore <<'PY'
import os
import sys
import tempfile
import zipfile
from pathlib import Path

archive_path = Path(sys.argv[1])
skillignore_path = Path(sys.argv[2])
patterns = [
    line.strip()
    for line in skillignore_path.read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]


def excluded(name: str) -> bool:
    if name == "last30days/.skillignore":
        return True
    for pattern in patterns:
        archive_pattern = f"last30days/{pattern}"
        if pattern.endswith("/") and name.startswith(archive_pattern):
            return True
        if name == archive_pattern:
            return True
    return False


fd, tmp_name = tempfile.mkstemp(
    prefix=f"{archive_path.name}.",
    suffix=".tmp",
    dir=str(archive_path.parent),
)
os.close(fd)
tmp_path = Path(tmp_name)
try:
    with zipfile.ZipFile(archive_path) as source, zipfile.ZipFile(
        tmp_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as target:
        for member in source.infolist():
            if not excluded(member.filename):
                target.writestr(member, source.read(member.filename))
    os.replace(tmp_path, archive_path)
finally:
    if tmp_path.exists():
        tmp_path.unlink()
PY

COUNT=$(unzip -l "$OUT_PATH" | tail -1 | awk '{print $2}')
SIZE=$(du -h "$OUT_PATH" | cut -f1)

if [ "$COUNT" -gt 200 ]; then
  echo "error: $COUNT files in zip, claude.ai's cap is 200" >&2
  echo "       check .gitattributes export-ignore entries and this script's prune list" >&2
  exit 1
fi

SKILL_MD_COUNT=$(unzip -l "$OUT_PATH" | grep -c "SKILL.md" || true)
if [ "$SKILL_MD_COUNT" -ne 1 ]; then
  echo "error: expected exactly one SKILL.md, found $SKILL_MD_COUNT" >&2
  exit 1
fi

echo "built $OUT_PATH ($COUNT files, $SIZE)"
echo "upload via the claude.ai skill UI"
