"""last30days CLI."""

from __future__ import annotations

from .cli import __all__ as _CLI_ALL
from .cli import __dir__, __getattr__, main

__all__ = ["main", *_CLI_ALL]
