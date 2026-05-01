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

Pre-commit hooks (prek):
```bash
uvx prek run --all-files   # run all hooks on every file
uvx prek install           # install git hooks locally
```

## Architecture

- `src/agent_skill_router/server.py` — core: `_PROVIDER_ROOTS` list, `_resolve_roots()`, `build_mcp()`
- `src/agent_skill_router/settings.py` — all config via `SKILL_ROUTER_*` env vars (pydantic-settings)
- `src/agent_skill_router/__init__.py` — `main()` entrypoint: reads `Settings()`, calls `build_mcp()`, calls `mcp.run()`
- `src/agent_skill_router/skills/` — bundled skills shipped in the wheel (e.g. `skill-creator/SKILL.md`); coverage omits this dir

## Key conventions

- **All path operations use `pathlib.Path`** — never `os.path`.
- **Bundled skills path**: `Path(__file__).parent / "skills"` — not `importlib.resources`.
- **All providers** use `supporting_files="resources"` so every file in a skill is listed individually as an MCP resource.
- **`extra_dirs` and `enable_bundled`** are never gated by `enable_workspace_level` / `enable_user_level` — they are always included when set.
- **`_PROVIDER_ROOTS`** is a module-level list; tests monkey-patch it directly with `srv._PROVIDER_ROOTS = patched` (+ `# type: ignore[assignment]`) instead of touching real user dirs.
- ERA001 (commented-out code) is enforced — use docstrings or delete; do not leave example snippets as comments inside classes.

## Testing quirks

- `asyncio_mode = "auto"` is set — never add `@pytest.mark.asyncio`.
- Tests are always functions, never classes.
- `all_disabled_settings` fixture disables every provider — always use it as baseline when testing a single provider to avoid ambient filesystem state.
- `Path.home()` is patched via `monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))` in tests that touch user-level paths.
- `main()` is not unit-testable (calls `mcp.run()` which starts a server); coverage gap there is expected.

## Linting rules worth knowing

- `ANN` rules apply to `src/` but not `tests/` — type annotations required in production code.
- `S` (bandit security) is suppressed in `tests/` only.
- `ERA001` (commented-out code) is active — inline `# Example: ...` comments inside classes will fail.
- Runtime deps are pinned to current major: `fastmcp>=3.x,<x+1`, `pydantic-settings>=2.x,<x+1`. Bump upper bounds deliberately when adopting a new major.

## Adding a new provider

1. Add `enable_<name>: bool = Field(default=True, ...)` to `Settings` in `settings.py`.
2. Add an entry to `_PROVIDER_ROOTS` in `server.py` with both `"workspace"` and `"user"` keys.
3. Use `SkillsDirectoryProvider` for generic dirs; use the vendor class (e.g. `ClaudeSkillsProvider`) for official providers.
4. Add test coverage in `test_server.py` using the monkey-patch pattern for `_PROVIDER_ROOTS`.
