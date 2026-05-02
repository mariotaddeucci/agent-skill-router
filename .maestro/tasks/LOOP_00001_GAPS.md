---
type: analysis
title: Documentation Gaps - Loop 00001
created: 2026-05-02
tags:
  - documentation
  - coverage
  - gaps
related:
  - '[[LOOP_00001_DOC_REPORT]]'
---

# Documentation Gaps - Loop 00001

## Summary
- **Total Gaps Found:** 8
- **By Type:** 8 Functions, 0 Classes, 0 Types, 0 Modules
- **By Visibility:** 1 Public API, 7 Internal API

## Gap List

### GAP-001: `build_mcp`
- **File:** `src/agent_skill_router/server.py`
- **Line:** 190
- **Type:** Function
- **Visibility:** PUBLIC API
- **Complexity:** COMPLEX
- **Current State:** No docs (has inline comments but no top-level docstring)
- **Why It Needs Docs:**
  - Primary public entry point exported from `agent_skill_router.__init__`
  - Called by `cli.py` and importable directly by library consumers
  - Accepts two optional parameters whose interaction and defaults are non-obvious
  - Returns a `FastMCP` instance — what it exposes is undocumented
- **Signature:**
  ```
  def build_mcp(settings: Settings | None = None, workspace_dir: Path | None = None) -> FastMCP
  ```
- **Documentation Needed:**
  - [ ] Description
  - [ ] Parameters (`settings`, `workspace_dir`)
  - [ ] Return value (what the `FastMCP` instance exposes)
  - [ ] Examples
  - [ ] Error handling

---

### GAP-002: `ClaudeAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/claude.py`
- **Line:** 111
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Overrides abstract method from `AgentSetupProvider`; directory scanned (`.claude/commands/*.md`) is not obvious from the name alone
  - Consistent one-liner docstring would match all other provider methods
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention `.claude/commands/*.md` path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

### GAP-003: `CursorAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/cursor.py`
- **Line:** 106
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-002; scanned path is `.cursor/prompts/*.md`
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention `.cursor/prompts/*.md` path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

### GAP-004: `GithubCopilotAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/github_copilot.py`
- **Line:** 109
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-002; scanned path is `.github/prompts/*.prompt.md`
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention `.github/prompts/*.prompt.md` path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

### GAP-005: `OpencodeAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/opencode.py`
- **Line:** 106
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-002; scanned path is `.opencode/prompts/*.md`
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention `.opencode/prompts/*.md` path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

### GAP-006: `GooseAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/goose.py`
- **Line:** 171
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-002; scanned directory for Goose-specific prompt files
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention scanned path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

### GAP-007: `GeminiAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/gemini.py`
- **Line:** 105
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-002; scanned directory for Gemini-specific prompt files
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention scanned path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

### GAP-008: `CodexAgentSetupProvider.list_prompts`
- **File:** `src/agent_skill_router/agents/codex.py`
- **Line:** 141
- **Type:** Function
- **Visibility:** INTERNAL API
- **Complexity:** MODERATE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-002; scanned directory for Codex-specific prompt files
- **Signature:**
  ```
  def list_prompts(self, roots: list[Path] | None = None) -> list[SlashCommand]
  ```
- **Documentation Needed:**
  - [ ] Description (mention scanned path)
  - [ ] Parameters (`roots`)
  - [ ] Return value

---

## Gaps by Module

| Module | Gap Count | Types |
|--------|-----------|-------|
| `src/agent_skill_router/server.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/claude.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/cursor.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/github_copilot.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/opencode.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/goose.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/gemini.py` | 1 | 1 Function |
| `src/agent_skill_router/agents/codex.py` | 1 | 1 Function |

## Gaps by Type

### Functions
| Name | File | Visibility | Complexity |
|------|------|------------|------------|
| `build_mcp` | `src/agent_skill_router/server.py` | PUBLIC API | COMPLEX |
| `ClaudeAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/claude.py` | INTERNAL API | MODERATE |
| `CursorAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/cursor.py` | INTERNAL API | MODERATE |
| `GithubCopilotAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/github_copilot.py` | INTERNAL API | MODERATE |
| `OpencodeAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/opencode.py` | INTERNAL API | MODERATE |
| `GooseAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/goose.py` | INTERNAL API | MODERATE |
| `GeminiAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/gemini.py` | INTERNAL API | MODERATE |
| `CodexAgentSetupProvider.list_prompts` | `src/agent_skill_router/agents/codex.py` | INTERNAL API | MODERATE |

## Related Exports

Exports that should be documented together:

- **Group A:** All 7 `list_prompts` overrides in agent provider files — identical signatures, same pattern; document the ABC method in `_base.py` first, then add one-liners in each override mentioning the specific directory scanned.
- **Group B:** `build_mcp` in `server.py` — standalone, highest priority as the primary public API.
