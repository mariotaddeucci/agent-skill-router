# Documentation Gaps - Loop 00001

## Summary
- **Total Gaps Found:** 12
- **By Type:** 10 Functions/Methods, 1 Class, 1 Type Alias
- **By Visibility:** 2 Public API, 8 Internal API, 2 Utility
- **Overall Coverage:** 89.2% (target: 90%, gap: 0.8%)

---

## Gap List

### GAP-001: `Settings` class
- **File:** `src/agent_skill_router/settings.py`
- **Line:** 13
- **Type:** Class
- **Visibility:** PUBLIC API
- **Complexity:** MODERATE
- **Current State:** No docs (fields documented via `Field(description=...)` but no class-level docstring)
- **Why It Needs Docs:**
  - All configuration flows through this class; it is the primary extension point for operators
  - Pydantic `Field` descriptions are not surfaced in `help()` or IDEs the same way as a docstring
  - Class purpose, env var prefix (`SKILL_ROUTER_`), and configuration approach should be stated
- **Signature:**
  ```
  class Settings(BaseSettings)
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-002: `SlashCommand` type alias
- **File:** `src/agent_skill_router/agents/_base.py`
- **Line:** 61
- **Type:** Type alias
- **Visibility:** PUBLIC API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - It is a discriminated union; callers need to know the three variants and how the `type` discriminator works
- **Signature:**
  ```
  SlashCommand = Annotated[PromptSlashCommand | ToolSlashCommand | ResourceSlashCommand, Field(discriminator="type")]
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [ ] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-003: `ClaudeProvider.config_path_workspace`
- **File:** `src/agent_skill_router/agents/claude.py`
- **Line:** 44
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Overrides abstract base; semantic meaning of "workspace config path" differs per agent
  - Returns `.claude/mcp.json` relative to `Path.cwd()`
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-004: `ClaudeProvider.config_path_user`
- **File:** `src/agent_skill_router/agents/claude.py`
- **Line:** 47
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Returns `~/.claude/mcp.json`; the user-level vs workspace distinction is significant
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-005: `CursorProvider.config_path_workspace`
- **File:** `src/agent_skill_router/agents/cursor.py`
- **Line:** 43
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-003; Cursor uses a different config path convention
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-006: `CursorProvider.config_path_user`
- **File:** `src/agent_skill_router/agents/cursor.py`
- **Line:** 46
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same as GAP-004
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-007: `GeminiProvider.config_path_workspace`
- **File:** `src/agent_skill_router/agents/gemini.py`
- **Line:** 42
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-003
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-008: `GeminiProvider.config_path_user`
- **File:** `src/agent_skill_router/agents/gemini.py`
- **Line:** 45
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same as GAP-004
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-009: `GithubCopilotProvider.config_path_workspace`
- **File:** `src/agent_skill_router/agents/github_copilot.py`
- **Line:** 42
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-003
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-010: `GithubCopilotProvider.config_path_user`
- **File:** `src/agent_skill_router/agents/github_copilot.py`
- **Line:** 45
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same as GAP-004
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-011: `OpenCodeProvider.config_path_workspace`
- **File:** `src/agent_skill_router/agents/opencode.py`
- **Line:** 39
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same pattern as GAP-003
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

### GAP-012: `OpenCodeProvider.config_path_user`
- **File:** `src/agent_skill_router/agents/opencode.py`
- **Line:** 42
- **Type:** Method
- **Visibility:** INTERNAL API
- **Complexity:** SIMPLE
- **Current State:** No docs
- **Why It Needs Docs:**
  - Same as GAP-004
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Needed:**
  - [x] Description
  - [ ] Parameters
  - [x] Return value
  - [ ] Examples
  - [ ] Error handling

---

## Gaps by Module

| Module | Gap Count | Types |
|--------|-----------|-------|
| `src/agent_skill_router/agents/claude.py` | 2 | 2 Methods |
| `src/agent_skill_router/agents/cursor.py` | 2 | 2 Methods |
| `src/agent_skill_router/agents/gemini.py` | 2 | 2 Methods |
| `src/agent_skill_router/agents/github_copilot.py` | 2 | 2 Methods |
| `src/agent_skill_router/agents/opencode.py` | 2 | 2 Methods |
| `src/agent_skill_router/agents/_base.py` | 1 | 1 Type alias |
| `src/agent_skill_router/settings.py` | 1 | 1 Class |

## Gaps by Type

### Classes
| Name | File | Visibility | Complexity |
|------|------|------------|------------|
| `Settings` | `src/agent_skill_router/settings.py` | PUBLIC API | MODERATE |

### Types/Interfaces
| Name | File | Visibility | Complexity |
|------|------|------------|------------|
| `SlashCommand` | `src/agent_skill_router/agents/_base.py` | PUBLIC API | SIMPLE |

### Methods
| Name | File | Visibility | Complexity |
|------|------|------------|------------|
| `ClaudeProvider.config_path_workspace` | `src/agent_skill_router/agents/claude.py` | INTERNAL API | SIMPLE |
| `ClaudeProvider.config_path_user` | `src/agent_skill_router/agents/claude.py` | INTERNAL API | SIMPLE |
| `CursorProvider.config_path_workspace` | `src/agent_skill_router/agents/cursor.py` | INTERNAL API | SIMPLE |
| `CursorProvider.config_path_user` | `src/agent_skill_router/agents/cursor.py` | INTERNAL API | SIMPLE |
| `GeminiProvider.config_path_workspace` | `src/agent_skill_router/agents/gemini.py` | INTERNAL API | SIMPLE |
| `GeminiProvider.config_path_user` | `src/agent_skill_router/agents/gemini.py` | INTERNAL API | SIMPLE |
| `GithubCopilotProvider.config_path_workspace` | `src/agent_skill_router/agents/github_copilot.py` | INTERNAL API | SIMPLE |
| `GithubCopilotProvider.config_path_user` | `src/agent_skill_router/agents/github_copilot.py` | INTERNAL API | SIMPLE |
| `OpenCodeProvider.config_path_workspace` | `src/agent_skill_router/agents/opencode.py` | INTERNAL API | SIMPLE |
| `OpenCodeProvider.config_path_user` | `src/agent_skill_router/agents/opencode.py` | INTERNAL API | SIMPLE |

## Related Exports

Exports that should be documented together:

- **Group A:** `config_path_workspace` and `config_path_user` across all 5 agent providers — identical pattern, should use the same docstring template
- **Group B:** `Settings` class — standalone, highest priority
- **Group C:** `SlashCommand` type alias — should be documented alongside `PromptSlashCommand`, `ToolSlashCommand`, `ResourceSlashCommand` in `_base.py`

## Recommended Fix Order

1. `Settings` class docstring — highest visibility, single change
2. `SlashCommand` type alias docstring — small, high clarity gain
3. `config_path_workspace` / `config_path_user` in all 5 agents — use a shared one-liner template: `"Return the path to the MCP config file for workspace/user-level installation."`
