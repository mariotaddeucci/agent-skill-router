---
type: analysis
title: Documentation Plan - Loop 00001
created: 2026-05-02
tags:
  - documentation
  - plan
  - coverage
related:
  - '[[LOOP_00001_GAPS]]'
  - '[[LOOP_00001_DOC_REPORT]]'
---

# Documentation Plan - Loop 00001

## Summary
- **Total Gaps:** 8
- **Auto-Document (PENDING):** 8
- **Needs Context:** 0
- **Won't Do:** 0

## Current Coverage: 87.5%
## Target Coverage: 90%
## Estimated Post-Loop Coverage: 92.7%

---

## PENDING - Ready for Auto-Documentation

### DOC-001: `build_mcp`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001
- **File:** `src/agent_skill_router/server.py`
- **Gap ID:** GAP-001
- **Type:** Function
- **Visibility:** PUBLIC
- **Importance:** CRITICAL
- **Signature:**
  ```
  def build_mcp(settings: Settings | None = None, workspace_dir: Path | None = None) -> FastMCP
  ```
- **Documentation Added:**
  - [x] Description: Primary public entry point; builds and returns a configured FastMCP server instance
  - [x] Parameters: `settings` (optional Settings override), `workspace_dir` (optional workspace path override)
  - [x] Returns: Configured `FastMCP` instance exposing skill resources and tools
  - [x] Examples: Yes — basic usage and settings-override example
  - [x] Errors: Documented workspace resolution fallback behaviour

### DOC-002: `ClaudeAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001
- **File:** `src/agent_skill_router/agents/claude.py`
- **Gap ID:** GAP-002
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Scans `.claude/commands/*.md` under each root for slash command definitions
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, one per `.md` file
  - [x] Examples: No
  - [x] Errors: No

### DOC-003: `CursorAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001
- **File:** `src/agent_skill_router/agents/cursor.py`
- **Gap ID:** GAP-003
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Scans `.cursor/rules/*.mdc` and `*.md` under each root for rule/prompt definitions
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, de-duplicated by stem
  - [x] Examples: No
  - [x] Errors: No

### DOC-004: `GithubCopilotAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001
- **File:** `src/agent_skill_router/agents/github_copilot.py`
- **Gap ID:** GAP-004
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Scans `.github/prompts/*.prompt.md` under each root for slash command definitions
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, de-duplicated by stem
  - [x] Examples: No
  - [x] Errors: No

### DOC-005: `OpencodeAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001 (iteration 2)
- **File:** `src/agent_skill_router/agents/opencode.py`
- **Gap ID:** GAP-005
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Scans `.opencode/commands/*.md` under each root for slash command definitions
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, de-duplicated by stem
  - [x] Examples: No
  - [x] Errors: No

### DOC-006: `GooseAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001 (iteration 1 — already had docstring)
- **File:** `src/agent_skill_router/agents/goose.py`
- **Gap ID:** GAP-006
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Reads recipes from `.goose/recipes/*.yaml` under each root
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, de-duplicated by title
  - [x] Examples: No
  - [x] Errors: No

### DOC-007: `GeminiAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001 (iteration 2)
- **File:** `src/agent_skill_router/agents/gemini.py`
- **Gap ID:** GAP-007
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Scans `.gemini/commands/**/*.toml` under each root for slash command definitions
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, de-duplicated by colon-joined path name
  - [x] Examples: No
  - [x] Errors: No

### DOC-008: `CodexAgentSetupProvider.list_prompts`
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001 (iteration 2)
- **File:** `src/agent_skill_router/agents/codex.py`
- **Gap ID:** GAP-008
- **Type:** Function
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Added:**
  - [x] Description: Scans `.codex/prompts/*.md` under each root for slash command definitions
  - [x] Parameters: `roots` (list of base directories to scan; defaults to `[Path.cwd()]` if None)
  - [x] Returns: List of `SlashCommand` objects discovered, de-duplicated by stem
  - [x] Examples: No
  - [x] Errors: No

---

## PENDING - NEEDS CONTEXT

_(None)_

---

## WON'T DO

_(None)_

---

## Documentation Order

Recommended sequence based on visibility and dependencies:

1. **DOC-001** - `build_mcp` (PUBLIC, CRITICAL — primary library entry point; document first)
2. **DOC-002** - `ClaudeAgentSetupProvider.list_prompts` (INTERNAL, HIGH — reference impl for group)
3. **DOC-003** - `CursorAgentSetupProvider.list_prompts` (INTERNAL, HIGH)
4. **DOC-004** - `GithubCopilotAgentSetupProvider.list_prompts` (INTERNAL, HIGH)
5. **DOC-005** - `OpencodeAgentSetupProvider.list_prompts` (INTERNAL, HIGH)
6. **DOC-006** - `GooseAgentSetupProvider.list_prompts` (INTERNAL, HIGH)
7. **DOC-007** - `GeminiAgentSetupProvider.list_prompts` (INTERNAL, HIGH)
8. **DOC-008** - `CodexAgentSetupProvider.list_prompts` (INTERNAL, HIGH)

## Related Documentation

Exports that should be documented together for consistency:

- **Group A:** DOC-002 through DOC-008 — all `list_prompts` overrides across agent providers; identical signatures, one-liner docstrings mentioning the specific directory each scans
- **Group B:** DOC-001 — `build_mcp` standalone; highest priority as the primary public API
