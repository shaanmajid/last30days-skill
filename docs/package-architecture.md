# Package and Skill Architecture

`last30days` is being split into two layers:

- `last30days/` is the Python package surface. It owns import stability,
  `python -m last30days`, and the `last30days` console entry point.
- `skills/last30days/` remains the Agent Skill wrapper. `SKILL.md` tells a
  host model how to invoke the engine, and `scripts/last30days.py` remains the
  compatibility executable used by existing skill installs.
- `skills/last30days/scripts/lib/` is still the legacy engine library for this
  migration stage. Packaging metadata exposes it as the existing top-level
  `lib` package so old tests and imports keep working while code moves
  incrementally.

The current package facade loads the legacy CLI module instead of copying or
renaming every engine module. That keeps the first migration review small and
preserves direct calls such as:

```bash
python3 skills/last30days/scripts/last30days.py "query" --emit=compact
python3 -m last30days "query" --emit=compact
last30days "query" --emit=compact
```

The intended next steps are:

- Move stable engine modules from `skills/last30days/scripts/lib/` into the
  package namespace in small batches.
- Replace top-level `lib` imports with package imports once each batch has
  compatibility aliases.
- Thin `skills/last30days/scripts/last30days.py` into a wrapper that imports
  the package entry point when packaged skill installs can reliably include or
  depend on the Python package.
- Keep `SKILL.md` and skill packaging focused on host instructions and assets,
  not on owning the reusable Python SDK surface.
