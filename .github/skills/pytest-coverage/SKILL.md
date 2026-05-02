---
name: pytest-coverage
description: "Write pytest tests with coverage focus. Use when: adding tests, writing unit tests, writing integration tests, negative tests, edge cases, bug hunting, improving coverage, pytest, test suite."
argument-hint: "module, function, or file to test (e.g. src/agent_skill_router/server.py)"
---

# Pytest Coverage Skill

## Philosophy

Two layers, different responsibilities:

| Layer | Goal | Volume | Focus |
|-------|------|--------|-------|
| **Unit** | Find unmapped bugs | Many | Negative paths, edge cases, invalid inputs |
| **Integration** | Verify real user behavior | Few | Happy paths with high scenario coverage |

Unit tests hunt for bugs. Integration tests prove features work end-to-end.

---

## Step 1 — Explore the target

Before writing any test, read the target module:

1. Identify every **public function/method/class** — these are test targets.
2. For each target, list its **branches**: `if`, `elif`, `else`, `try/except`, early returns, guard clauses.
3. Note **type boundaries**: what happens at `None`, `""`, `0`, negative numbers, empty collections, max values.
4. Check if the module already has tests — read them to avoid duplication and understand existing patterns.

---

## Step 2 — Plan unit tests (negative / edge cases)

Unit tests go in `tests/` (not `tests/integration/`). Each test is a **standalone function** — never a class, unless the existing file uses classes (follow the file's pattern).

For every branch and boundary found in Step 1, create a test that triggers the **unexpected path**:

### Checklist for unit test coverage

- [ ] `None` passed where an object is expected
- [ ] Empty string / empty list / empty dict
- [ ] Negative numbers / zero where positive is expected
- [ ] Invalid type (e.g. `int` where `Path` expected)
- [ ] Path that does not exist (use `tmp_path / "nonexistent"`)
- [ ] Duplicate entries / duplicate names
- [ ] Boundary values (first item, last item, single item)
- [ ] Boolean flags: `True` vs `False` for every flag
- [ ] Combinations of flags that produce conflicting state
- [ ] Exceptions: verify the right exception type AND message fragment

### Naming convention

```python
def test_<function>_<condition>_<expected_outcome>():
    ...
```

Examples:
- `test_resolve_roots_nonexistent_paths_excluded`
- `test_build_mcp_raises_when_settings_invalid`
- `test_discover_returns_empty_list_on_missing_dir`

### Key fixtures to use (project-specific)

- `all_disabled_settings` — baseline with every provider disabled; always start here when testing a single provider
- `tmp_path` — isolated temp directory; never use real home or workspace dirs
- `monkeypatch` — patch `Path.home()` via `monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))`
- `_PROVIDER_ROOTS` — monkey-patch directly: `srv._PROVIDER_ROOTS = patched  # type: ignore[assignment]`

### Do NOT

- Add `@pytest.mark.asyncio` — `asyncio_mode = "auto"` is already set
- Use `from __future__ import annotations`
- Use relative imports

---

## Step 3 — Plan integration tests (user-behavior focused)

Integration tests go in `tests/integration/`. They test **scenarios a real user would trigger**, not internal branches.

### Integration test rules

1. **One scenario per test** — simulate a single coherent user action.
2. **Use real filesystem via `tmp_path`** — create actual files/dirs, not mocks.
3. **Assert on observable outputs** — returned lists, file contents, MCP resource names; not internal state.
4. **Cover the full flow** — from input to final output (e.g. settings → `build_mcp()` → `Client` query → resource list).
5. **Keep count low** — 3–6 tests per module, each covering a distinct scenario.

### Integration scenario template

```python
async def test_<feature>_<scenario>(tmp_path, monkeypatch):
    # Arrange: set up realistic file structure
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\ndescription: x\n---\n# x\n")

    # Act: invoke via public API (build_mcp, discover, install, etc.)
    from fastmcp import Client
    mcp = build_mcp(settings)
    async with Client(mcp) as client:
        resources = await client.list_resources()

    # Assert: observable user-facing result
    uris = [str(r.uri) for r in resources]
    assert any("my-skill" in u for u in uris)
```

---

## Step 4 — Write the tests

Write all tests at once. Follow these rules:

- **Imports at top** of file, not inside functions (unless testing a lazy-import behavior).
- **One assertion per logical concern** — multiple `assert` lines are fine when they check the same thing.
- **No magic values** — use named variables for expected strings, paths, counts.
- **No sleep/wait** — use `asyncio_mode = "auto"` + `async def test_` for async code.
- **Parametrize repetitive cases**:

```python
@pytest.mark.parametrize("value", [None, "", [], {}])
def test_fn_rejects_empty_input(value):
    with pytest.raises(ValueError):
        fn(value)
```

---

## Step 5 — Run and validate coverage

```bash
uv run pytest --cov --cov-report=term-missing
```

Review the `MISS` column. For every uncovered line:

1. Determine if it's a branch, exception handler, or edge case.
2. Add a unit test specifically targeting that line.
3. Re-run until coverage target is met (aim ≥ 90% for new code).

To run only the new tests first:

```bash
uv run pytest tests/test_<module>.py -v
uv run pytest tests/integration/ -v
```

---

## Step 6 — Lint and type-check

```bash
uv run ruff check src/ tests/
uv run pyrefly check
```

Fix any errors before finalizing. Common issues:
- Missing type annotations in `src/` (`ANN` rules)
- Imports that should be inside `TYPE_CHECKING` blocks (`TCH` rules)
- Commented-out code (`ERA001`)

---

## Completion Checklist

- [ ] Every public function has at least one negative test
- [ ] All boolean flags tested in both states
- [ ] All `except` blocks have a test that triggers them
- [ ] Integration tests cover distinct user scenarios (not just repeats of unit tests)
- [ ] Coverage ≥ 90% on new/changed code
- [ ] `ruff check` passes with no errors
- [ ] `pyrefly check` passes with no errors
