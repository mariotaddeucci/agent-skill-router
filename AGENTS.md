# AGENTS.md

## Commands

```bash
uv run pytest                        # run all tests
uv run pytest tests/test_server.py   # run a single test file
uv run pytest -k test_name           # run a single test by name
uv run ruff check src/ tests/        # lint
uv run ruff format src/ tests/       # format
uv run pyrefly check                 # type check
uv run pytest --cov                  # tests + coverage
```

Static analysis / pre-commit hooks (prek):
```bash
uv run prek run --all-files   # run all hooks on every file (lint, format, type-check)
uvx prek install              # install git hooks locally
```

## Architecture

- `src/agent_skill_router/server.py` — core: `_PROVIDER_ROOTS` list, `_resolve_roots()`, `build_mcp()`
- `src/agent_skill_router/settings.py` — all config via `SKILL_ROUTER_*` env vars (pydantic-settings)
- `src/agent_skill_router/cli.py` — Typer app; entrypoint (`agent-skill-router = "agent_skill_router.cli:app"`); commands: `list`, `install`, `run`, `setup-mcp`
- `src/agent_skill_router/__init__.py` — re-exports `app`, `build_mcp`, `Settings`; `main()` delegates to `app()`
- `src/agent_skill_router/_skills.py` — `discover_skills()`, `install_skill()`, `SkillEntry` used by the `list`/`install` CLI commands
- `src/agent_skill_router/agents/` — `AgentSetupProvider` ABC + one module per agent; used by the `setup-mcp` CLI command
- `src/agent_skill_router/skills/` — bundled skills shipped in the wheel (e.g. `skill-creator/SKILL.md`); coverage omits this dir

## Key conventions

- **Python 3.13+ only** — do not add `from __future__ import annotations`; use native PEP 604/585 types directly.
- **Absolute imports only** — never use relative imports (`from .foo import ...`).
- **All path operations use `pathlib.Path`** — never `os.path`.
- **Bundled skills path**: `Path(__file__).parent / "skills"` — not `importlib.resources`.
- **All providers** use `supporting_files="resources"` so every file in a skill is listed individually as an MCP resource.
- **`extra_dirs` and `enable_bundled`** are never gated by `enable_workspace_level` / `enable_user_level` — they are always included when set.
- **`_PROVIDER_ROOTS`** is a module-level list; tests monkey-patch it directly with `srv._PROVIDER_ROOTS = patched` (+ `# type: ignore[assignment]`) instead of touching real user dirs.
- ERA001 (commented-out code) is enforced — use docstrings or delete; do not leave example snippets as comments inside classes or functions.

## Testing quirks

- `asyncio_mode = "auto"` is set — never add `@pytest.mark.asyncio`.
- Tests are always **functions, never classes** — except `tests/test_setup.py` which uses classes; follow the pattern of whichever file you are editing.
- `all_disabled_settings` fixture disables every provider — always use it as baseline when testing a single provider to avoid ambient filesystem state.
- `Path.home()` is patched via `monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))` in tests that touch user-level paths.
- `main()` is not unit-testable (calls `mcp.run()` which starts a server); coverage gap there is expected.

## Linting rules worth knowing

- `ANN` rules apply to `src/` but not `tests/` — type annotations required in production code.
- `S` (bandit security) is suppressed in `tests/` only.
- `ERA001` (commented-out code) is active — inline `# Example: ...` or section-header comments (`# --- Foo ---`) inside files will fail.
- `TCH` is active — imports used only in type annotations must go inside `TYPE_CHECKING` blocks, unless `from __future__ import annotations` is present (it isn't — see above). For `Path` used at runtime in signatures/dataclasses, no `noqa` needed.
- `UP045` is active — use `X | None` not `Optional[X]`; `noqa: UP007` is no longer needed.
- Runtime deps are pinned to current major: `fastmcp>=3.x,<x+1`, `pydantic-settings>=2.x,<x+1`. Bump upper bounds deliberately when adopting a new major.

## Adding a new skill provider (MCP server side)

1. Add `enable_<name>: bool = Field(default=True, ...)` to `Settings` in `settings.py`.
2. Add an entry to `_PROVIDER_ROOTS` in `server.py` with both `"workspace"` and `"user"` keys.
3. Use `SkillsDirectoryProvider` for generic dirs; use the vendor class (e.g. `ClaudeSkillsProvider`) for official providers.
4. Add test coverage in `test_server.py` using the monkey-patch pattern for `_PROVIDER_ROOTS`.

## Adding a new agent setup provider (CLI `setup-mcp` command)

1. Create `src/agent_skill_router/agents/<name>.py` with a class extending `AgentSetupProvider`.
2. Implement `config_path_workspace()` and `config_path_user()` in every provider.
3. Implement `discover()` and `install()` only if automated setup is feasible; otherwise leave them raising `NotImplementedError` (the CLI will print manual instructions).
4. Register the instance in `AGENT_PROVIDERS` dict in `src/agent_skill_router/agents/__init__.py`.
5. Add tests in `tests/test_setup.py`.

`setup-mcp` (no `--agent`) installs into `config_path(user=user)` for every provider that does **not** raise `NotImplementedError` on `install()`. It creates the config file if it does not exist.
