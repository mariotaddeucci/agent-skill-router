# Documentation Plan - Loop 00001

## Summary
- **Total Gaps:** 12
- **Auto-Document (PENDING):** 12
- **Needs Context:** 0
- **Won't Do:** 0

## Current Coverage: 89.2%
## Target Coverage: 90%
## Estimated Post-Loop Coverage: 90.2%

---

## PENDING - Ready for Auto-Documentation

### DOC-001: `Settings` class
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001
- **File:** `src/agent_skill_router/settings.py`
- **Gap ID:** GAP-001
- **Type:** Class
- **Visibility:** PUBLIC
- **Importance:** CRITICAL
- **Signature:**
  ```
  class Settings(BaseSettings)
  ```
- **Documentation Added:**
  - [x] Description
  - [x] Parameters (N/A — fields use Field(description=...))
  - [x] Returns (N/A)
  - [x] Example

---

### DOC-002: `SlashCommand` type alias
- **Status:** `IMPLEMENTED`
- **Implemented In:** Loop 00001
- **File:** `src/agent_skill_router/agents/_base.py`
- **Gap ID:** GAP-002
- **Type:** Type alias
- **Visibility:** PUBLIC
- **Importance:** HIGH
- **Signature:**
  ```
  SlashCommand = Annotated[PromptSlashCommand | ToolSlashCommand | ResourceSlashCommand, Field(discriminator="type")]
  ```
- **Documentation Added:**
  - [x] Description: Discriminated union of the three slash-command variants; the `type` field determines which variant is in use
  - [x] Parameters: N/A
  - [x] Returns: N/A
  - [x] Examples: No
  - [x] Errors: N/A

---

### DOC-003: `ClaudeProvider.config_path_workspace`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/claude.py`
- **Gap ID:** GAP-003
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the Claude MCP config file for workspace-level installation (`.claude/mcp.json` relative to `Path.cwd()`)
  - [ ] Parameters: None
  - [ ] Returns: `Path` — workspace-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-004: `ClaudeProvider.config_path_user`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/claude.py`
- **Gap ID:** GAP-004
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the Claude MCP config file for user-level installation (`~/.claude/mcp.json`)
  - [ ] Parameters: None
  - [ ] Returns: `Path` — user-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-005: `CursorProvider.config_path_workspace`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/cursor.py`
- **Gap ID:** GAP-005
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the Cursor MCP config file for workspace-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — workspace-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-006: `CursorProvider.config_path_user`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/cursor.py`
- **Gap ID:** GAP-006
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the Cursor MCP config file for user-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — user-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-007: `GeminiProvider.config_path_workspace`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/gemini.py`
- **Gap ID:** GAP-007
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the Gemini MCP config file for workspace-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — workspace-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-008: `GeminiProvider.config_path_user`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/gemini.py`
- **Gap ID:** GAP-008
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the Gemini MCP config file for user-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — user-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-009: `GithubCopilotProvider.config_path_workspace`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/github_copilot.py`
- **Gap ID:** GAP-009
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the GitHub Copilot MCP config file for workspace-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — workspace-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-010: `GithubCopilotProvider.config_path_user`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/github_copilot.py`
- **Gap ID:** GAP-010
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the GitHub Copilot MCP config file for user-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — user-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-011: `OpenCodeProvider.config_path_workspace`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/opencode.py`
- **Gap ID:** GAP-011
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_workspace(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the OpenCode MCP config file for workspace-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — workspace-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

### DOC-012: `OpenCodeProvider.config_path_user`
- **Status:** `PENDING`
- **File:** `src/agent_skill_router/agents/opencode.py`
- **Gap ID:** GAP-012
- **Type:** Method
- **Visibility:** INTERNAL
- **Importance:** HIGH
- **Signature:**
  ```
  def config_path_user(self) -> Path
  ```
- **Documentation Plan:**
  - [ ] Description: Return the path to the OpenCode MCP config file for user-level installation
  - [ ] Parameters: None
  - [ ] Returns: `Path` — user-scoped config path
  - [ ] Examples: No
  - [ ] Errors: N/A

---

## PENDING - NEEDS CONTEXT

*(none)*

---

## WON'T DO

*(none)*

---

## Documentation Order

Recommended sequence based on visibility and dependencies:

1. **DOC-001** - `Settings` (PUBLIC, CRITICAL — primary extension point for operators)
2. **DOC-002** - `SlashCommand` (PUBLIC, HIGH — discriminated union used by callers)
3. **DOC-003** - `ClaudeProvider.config_path_workspace` (INTERNAL, HIGH)
4. **DOC-004** - `ClaudeProvider.config_path_user` (INTERNAL, HIGH)
5. **DOC-005** - `CursorProvider.config_path_workspace` (INTERNAL, HIGH)
6. **DOC-006** - `CursorProvider.config_path_user` (INTERNAL, HIGH)
7. **DOC-007** - `GeminiProvider.config_path_workspace` (INTERNAL, HIGH)
8. **DOC-008** - `GeminiProvider.config_path_user` (INTERNAL, HIGH)
9. **DOC-009** - `GithubCopilotProvider.config_path_workspace` (INTERNAL, HIGH)
10. **DOC-010** - `GithubCopilotProvider.config_path_user` (INTERNAL, HIGH)
11. **DOC-011** - `OpenCodeProvider.config_path_workspace` (INTERNAL, HIGH)
12. **DOC-012** - `OpenCodeProvider.config_path_user` (INTERNAL, HIGH)

## Related Documentation

Exports that should be documented together for consistency:

- **Group A:** DOC-001 — `Settings` class (standalone, highest priority)
- **Group B:** DOC-002 — `SlashCommand` type alias (document alongside `PromptSlashCommand`, `ToolSlashCommand`, `ResourceSlashCommand` in `_base.py`)
- **Group C:** DOC-003 + DOC-004 — `ClaudeProvider` config path methods (pair together)
- **Group D:** DOC-005 + DOC-006 — `CursorProvider` config path methods (pair together)
- **Group E:** DOC-007 + DOC-008 — `GeminiProvider` config path methods (pair together)
- **Group F:** DOC-009 + DOC-010 — `GithubCopilotProvider` config path methods (pair together)
- **Group G:** DOC-011 + DOC-012 — `OpenCodeProvider` config path methods (pair together)
