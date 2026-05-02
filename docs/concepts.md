---
hide:
  - navigation
  - toc
---

# Concepts

This page explains the core ideas behind Agent Skill Router: what it is, how it works, and why it is structured the way it is.

---

## Multi-Agent Friendly Workspace

When working with multiple AI agents in the same repository, each agent reads instructions and skills from its own native locations. This quickly leads to duplicated files and divergent instructions.

Agent Skill Router solves this with the `init-workspace` command, which establishes a single source of truth using two conventions:

### `AGENTS.md` as the canonical instruction file

`AGENTS.md` is a cross-agent standard adopted by Claude Code, GitHub Copilot, Gemini CLI, OpenAI Codex, and others. Instead of maintaining separate `CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md` files, `init-workspace` merges them all into a single `AGENTS.md` and replaces the originals with symlinks:

```
AGENTS.md          ← single source of truth
CLAUDE.md          → symlink to AGENTS.md
GEMINI.md          → symlink to AGENTS.md
.github/
  copilot-instructions.md  → symlink to AGENTS.md
```

Each agent follows the symlink transparently and reads the same instructions.

### `.claude/skills/` as the canonical skills directory

`.claude/skills/` is the skills directory used by Claude Code and already supported by the `ClaudeSkillsProvider` in this router. After running `init-workspace`, all provider-specific skill directories become symlinks pointing to `.claude/skills/`:

```
.claude/skills/    ← canonical location for all skills
.agents/skills/    → symlink to .claude/skills/
.cursor/skills/    → symlink to .claude/skills/
.gemini/skills/    → symlink to .claude/skills/
.codex/skills/     → symlink to .claude/skills/
.goose/skills/     → symlink to .claude/skills/
.opencode/skills/  → symlink to .claude/skills/
.github/skills/    → symlink to .claude/skills/
```

Any agent scanning its own native skills directory will transparently find the same skills.

### Running `init-workspace`

```bash
# Preview planned changes
agent-skill-router init-workspace --dry-run

# Apply changes
agent-skill-router init-workspace
```

See the [`init-workspace` CLI reference](cli.md#init-workspace) for full usage details.

---

## The proxy model

Agent Skill Router is, at its heart, a **format proxy**. It reads instructions written for Agent A and makes them available to Agent B — without any manual conversion.

```mermaid
flowchart LR
    subgraph "Format A (source)"
        FA1["Claude\n.claude/commands/*.md"]
        FA2["Gemini\n.gemini/commands/*.toml"]
        FA3["Goose\n.goose/recipes/*.yaml"]
        FA4["Copilot\n.github/prompts/*.prompt.md"]
    end

    subgraph "Agent Skill Router"
        PARSE["Parse & normalize"]
        MCP["MCP Server\n(FastMCP)"]
        PARSE --> MCP
    end

    subgraph "Format B (output)"
        FB1["MCP Resources\n(skill files + SKILL.md)"]
        FB2["MCP Prompts\n(slash commands)"]
    end

    FA1 --> PARSE
    FA2 --> PARSE
    FA3 --> PARSE
    FA4 --> PARSE

    MCP --> FB1
    MCP --> FB2
```

Any MCP-compatible agent on the right side — Claude, Cursor, Copilot, Gemini, OpenCode, Goose, Codex — gets the same standardized output, regardless of which agent originally authored the instructions.

---

## Two things the router exposes

### 1. Skills (MCP Resources)

A **skill** is a directory with a `SKILL.md` file. The skill teaches an agent how to perform a specific task — writing tests, creating PRs, following a coding standard, etc.

The router discovers skill directories from every agent's native skill path and registers them as MCP resources. Every file inside the skill directory (scripts, references, templates) is individually listed.

```mermaid
flowchart TD
    D1[".claude/skills/write-tests/"] --> R["Registered as\nMCP Resource"]
    D2[".agents/skills/code-review/"] --> R
    D3["~/.agents/skills/git-flow/"] --> R
    R --> C["Any connected agent\ncan read and load the skill"]
```

### 2. Slash commands (MCP Prompts)

A **slash command** is a reusable prompt — a piece of text an agent sends to the LLM when you invoke a command like `/fix-bug` or `/review-code`.

Each agent stores slash commands in its own native format. The router reads all of them and re-exposes each as an MCP prompt with a normalized name.

```mermaid
flowchart LR
    C1[".claude/commands/fix-bug.md\n(Markdown + frontmatter)"] -->|parse| N["name: fix-bug\ndescription: Fix a bug\nprompt: You are..."]
    C2[".gemini/commands/refactor.toml\n(TOML)"] -->|parse| N2["name: refactor\ndescription: Refactor code\nprompt: Refactor the..."]
    C3[".goose/recipes/standup.yaml\n(YAML)"] -->|parse| N3["name: daily-standup\ndescription: ...\nprompt: Prepare a..."]
    N --> MCP["MCP Prompts\n(any agent can call these)"]
    N2 --> MCP
    N3 --> MCP
```

---

## Discovery order and workspace resolution

The router needs to know *where* to look for skills and commands. It resolves the workspace root in this priority order:

```mermaid
flowchart TD
    A{"--workspace-dir\nCLI flag provided?"}
    A -- Yes --> USE["Use that directory"]
    A -- No --> B{"SKILL_ROUTER_WORKSPACE_DIR\nenv var set?"}
    B -- Yes --> USE
    B -- No --> C{"Inside a\ngit repository?"}
    C -- Yes --> GIT["Use git root\n(walk up until .git found)"]
    C -- No --> CWD["Use current directory"]
```

This means the router always anchors workspace-level paths to the **repository root**, not the subdirectory you happen to be in when you start it.

---

## Two scopes: workspace vs user

Every provider (except `extra_dirs` and bundled skills) supports two scopes:

| Scope | Location | Activated by |
|---|---|---|
| **Workspace** | `<workspace-root>/.agents/skills/` | `SKILL_ROUTER_ENABLE_WORKSPACE_LEVEL=true` |
| **User** | `~/.agents/skills/` | `SKILL_ROUTER_ENABLE_USER_LEVEL=true` |

- **Workspace-scoped** skills are project-specific — checked into the repository.
- **User-scoped** skills are personal — shared across all your projects.

Both scopes are enabled by default. You can limit to one scope with the `--user` or `--workspace` flags on the `list` and `install` commands.

---

## Deduplication: first-wins

When the same skill name (or slash command name) appears in multiple providers, the **first one found wins**. Providers are iterated in a fixed order (Claude → Cursor → VSCode → Codex → Gemini → Goose → Copilot → OpenCode → Agents → OpenClaw → Bundled). Later duplicates are silently skipped.

This gives you a clear, deterministic override mechanism: place your customized version in `.claude/skills/` (first in the list) to override anything from user-level or bundled paths.

```mermaid
flowchart LR
    S1[".claude/skills/lint-fix\n✅ registered"] --> DEDUP{"Already seen\n'lint-fix'?"}
    S2["~/.agents/skills/lint-fix\n⏭ skipped"] --> DEDUP
    DEDUP -- No --> REG["Register"]
    DEDUP -- Yes --> SKIP["Skip"]
```

---

## The built-in `create-skill` prompt

The router ships with a bundled skill called `skill-creator` and a corresponding MCP prompt `create-skill`. When any connected agent calls this prompt, it receives detailed instructions for writing a new skill from scratch — including frontmatter format, body structure, eval loops, and output directory conventions.

```
create-skill(goal="Write a skill that runs our test suite", save_to_user_level=False)
```

The `save_to_user_level` parameter controls where the new skill is saved:
- `false` → `<workspace>/.agents/skills/<name>/`
- `true` → `~/.agents/skills/<name>/`

---

## Architecture overview

```mermaid
flowchart TB
    subgraph "CLI (cli.py)"
        CMD_LIST["list"]
        CMD_INSTALL["install"]
        CMD_RUN["run"]
        CMD_SETUP["setup-mcp"]
    end

    subgraph "Server (server.py)"
        WS["workspace_root()"]
        PROV["_PROVIDER_ROOTS\n(10 vendor providers)"]
        BUILD["build_mcp()"]
        WS --> BUILD
        PROV --> BUILD
    end

    subgraph "Agents (agents/)"]
        BASE["AgentSetupProvider ABC"]
        CLAUDE["ClaudeSetupProvider"]
        COPILOT["GitHubCopilotSetupProvider"]
        OTHERS["Cursor, OpenCode, Gemini,\nGoose, Codex..."]
        BASE --> CLAUDE
        BASE --> COPILOT
        BASE --> OTHERS
    end

    subgraph "Skills (_skills.py)"
        DISC["discover_skills(roots)"]
        INST["install_skill(src, dest)"]
    end

    subgraph "Settings (settings.py)"
        ENV["SKILL_ROUTER_* env vars\n(pydantic-settings)"]
    end

    subgraph "MCP Proxy"
        READ["Read agent configs\n(.claude/mcp.json, etc.)"]
        PROXY["ProxyProvider\nfor remote servers"]
    end

    CMD_RUN --> BUILD
    CMD_LIST --> DISC
    CMD_INSTALL --> INST
    CMD_SETUP --> CLAUDE
    CMD_SETUP --> COPILOT
    CMD_SETUP --> OTHERS
    ENV --> BUILD
    ENV --> CMD_LIST
    ENV --> READ

    BUILD --> MCP["FastMCP instance\n(resources + prompts)"]
    READ --> PROXY
    PROXY --> MCP
```

The MCP proxy component (right side) reads MCP server entries from native agent config files and re-exposes them through `ProxyProvider`, making them accessible to any connected agent.
