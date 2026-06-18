# Distribution Topology

This repo ships the same `/last30days` runtime through several install surfaces. Keep the runtime source small and shared; treat release bundles as outputs.

## Canonical Channels

| Channel | User install path | Source today | Release artifact | Update path |
|---------|-------------------|--------------|------------------|-------------|
| Claude Code plugin | `/plugin marketplace add mvanhorn/last30days-skill` | Repo archive plus `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` | None attached separately; Claude Code reads the repo/plugin marketplace metadata | Marketplace/plugin update |
| Agent Skills CLI | `npx skills add mvanhorn/last30days-skill -g` | `skills/last30days/` plus adapter metadata such as `gemini-extension.json` | None attached separately | `npx skills update last30days -g` |
| claude.ai web | Download `last30days.skill` from GitHub Releases | `skills/last30days/` packaged and pruned by `skills/last30days/scripts/build-skill.sh` | `dist/last30days.skill` attached by `.github/workflows/release.yml` | Re-download/re-upload |
| Claude Desktop | Download platform `.mcpb` from GitHub Releases | `mcp/manifest.json`, Go MCP wrapper, and `skills/last30days/scripts/` mirrored by `mcp/scripts/sync-engine.sh` at build time | `last30days-pp-mcp-<os>-<arch>.mcpb` attached by release CI | Re-download/reinstall |
| Gemini CLI | Usually via `npx skills add ... -a gemini-cli` | `gemini-extension.json` and `skills/last30days/` | None attached separately | `npx skills update ...` |
| OpenClaw | `clawhub install last30days-official` | `skills/last30days/SKILL.md` `metadata.openclaw` plus `.clawhubignore` | ClawHub-managed package, not built by this repo's release workflow | `clawhub update last30days-official` |
| Hermes | `hermes skills install mvanhorn/last30days-skill --force` | `skills/last30days/` filtered by `skills/last30days/.skillignore` | Hermes-managed install from GitHub, not built by this repo's release workflow | Reinstall with `--force` |
| Manual developer install | Symlink `skills/last30days` into a host skill directory | Working tree | None | `git pull` |

## Source Of Truth Today

- Runtime command, prompts, and setup behavior: `skills/last30days/SKILL.md` and `skills/last30days/scripts/`.
- Shared Python engine source: `skills/last30days/scripts/`; never edit generated MCP vendored copies.
- Package version for Python/project metadata: `pyproject.toml`.
- Version mirrors checked by tests: `skills/last30days/SKILL.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `gemini-extension.json`.
- Claude Code marketplace metadata: `.claude-plugin/`.
- Agent marketplace availability metadata: `.agents/plugins/marketplace.json`.
- Gemini settings surface: `gemini-extension.json`.
- OpenClaw metadata: `skills/last30days/SKILL.md` `metadata.openclaw`; packaging excludes live in `.clawhubignore`.
- Hermes scan/install excludes: `skills/last30days/.skillignore`.
- Claude Desktop MCPB metadata: `mcp/manifest.json`.

Generated or release-time outputs:

- `dist/last30days.skill`: built from `HEAD:skills/last30days` by `skills/last30days/scripts/build-skill.sh`.
- `mcp/internal/engine/vendored/`: build-time mirror from `skills/last30days/scripts/`, kept out of source except `.gitkeep`.
- `mcp/build/*.mcpb`: built by release CI from the Go MCP wrapper, `mcp/manifest.json`, and the mirrored engine.
- GitHub release assets: `last30days.skill` and platform `.mcpb` files attached by `.github/workflows/release.yml`.

## Target State

1. Short term, treat `skills/last30days/` as the current runtime source tree. Long term, move the core engine into a real package such as `src/last30days`, with skill, MCP, plugin, and CLI surfaces as adapters.
2. Keep `pyproject.toml` as the canonical version, with existing tests enforcing mirrors for SKILL/plugin/Gemini metadata.
3. Keep `mcp/manifest.json` versioning independent as documented in `mcp/README.md`: hand-bump it when MCPB-facing changes warrant it, while release CI stamps the Go binary version from the tag.
4. Introduce a machine-readable release manifest only when it has a schema or a generator. Until then, keep this document as the maintained distribution map.
5. Keep generated bundles out of git. Release CI should continue to attach `.skill` and `.mcpb` files from clean tag builds.

## Release Checklist

Before tagging a release:

1. Update the canonical version and mirrored metadata covered by `tests/test_plugin_contract.py`.
2. If the release affects Claude Desktop, update `mcp/manifest.json` deliberately.
3. Confirm README install instructions still match the supported channels above.
4. Confirm `skills/last30days/scripts/build-skill.sh`, `.clawhubignore`, and `skills/last30days/.skillignore` still exclude only files that are unsafe or unnecessary for their target channel.
5. Tag `vX.Y.Z`; release CI should publish `last30days.skill` and platform `.mcpb` assets.
6. Verify the GitHub release contains the expected assets and generated notes.
