"""Package facade for the legacy last30days skill engine."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LEGACY_SCRIPTS_DIR = _REPO_ROOT / "skills" / "last30days" / "scripts"
_LEGACY_CLI_PATH = _LEGACY_SCRIPTS_DIR / "last30days.py"
_LEGACY_MODULE_NAME = "last30days._legacy_cli"

_EXPORTS = {
    "MIN_PYTHON",
    "build_parser",
    "comparison_topic",
    "compute_save_path_display",
    "emit_comparison_output",
    "emit_output",
    "ensure_supported_python",
    "main",
    "parse_competitors_plan",
    "parse_search_flag",
    "persist_report",
    "register_child_pid",
    "save_output",
    "slugify",
    "subrun_kwargs_for",
    "unregister_child_pid",
}

__all__ = sorted(_EXPORTS)


def _ensure_legacy_scripts_path() -> None:
    if _LEGACY_SCRIPTS_DIR.exists():
        scripts_path = str(_LEGACY_SCRIPTS_DIR)
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)


def _alias_legacy_lib() -> None:
    """Expose the existing top-level ``lib`` package as ``last30days.lib``."""
    try:
        lib_module = importlib.import_module("lib")
    except ImportError:
        return
    sys.modules.setdefault("last30days.lib", lib_module)
    for module_name, module in list(sys.modules.items()):
        if module_name.startswith("lib."):
            sys.modules.setdefault(f"last30days.{module_name}", module)


def _load_from_source_checkout() -> ModuleType:
    if not _LEGACY_CLI_PATH.exists():
        raise ImportError(f"legacy last30days CLI not found at {_LEGACY_CLI_PATH}")
    module = sys.modules.get(_LEGACY_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_LEGACY_MODULE_NAME, _LEGACY_CLI_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load legacy last30days CLI from {_LEGACY_CLI_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_LEGACY_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def load_legacy_cli() -> ModuleType:
    """Load the current engine while package migration remains incremental."""
    _ensure_legacy_scripts_path()
    try:
        module = importlib.import_module("last30days.engine.last30days")
    except ModuleNotFoundError as exc:
        if exc.name not in {"last30days.engine", "last30days.engine.last30days"}:
            raise
        module = _load_from_source_checkout()
    _alias_legacy_lib()
    return module


def _sync_package_overrides(legacy_cli: ModuleType) -> dict[str, Any]:
    package = sys.modules.get("last30days")
    if package is None:
        return {}
    originals: dict[str, Any] = {}
    for name in _EXPORTS - {"main"}:
        if name in package.__dict__:
            originals[name] = getattr(legacy_cli, name)
            setattr(legacy_cli, name, package.__dict__[name])
    return originals


def main(argv: list[str] | None = None) -> int:
    legacy_cli = load_legacy_cli()
    originals = _sync_package_overrides(legacy_cli)
    try:
        if argv is None:
            return legacy_cli.main()

        original_argv = sys.argv[:]
        sys.argv = [original_argv[0], *argv]
        try:
            return legacy_cli.main()
        finally:
            sys.argv = original_argv
    finally:
        for name, value in originals.items():
            setattr(legacy_cli, name, value)


def __getattr__(name: str) -> Any:
    return getattr(load_legacy_cli(), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(load_legacy_cli())))
