import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY_SCRIPTS = ROOT / "skills" / "last30days" / "scripts"

sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(LEGACY_SCRIPTS))
