# CLI Reference

The `agent-skill-router` command-line tool manages skills, slash commands, and the MCP server.

```
Usage: agent-skill-router [OPTIONS] COMMAND [ARGS]...

  Manage agent skills and run the MCP server.

Options:
  --help  Show this message and exit.

Commands:
  list       List all skills and prompts accessible to the MCP server.
  install    Install a skill into the local or user-level skills directory.
  run        Start the Agent Skill Router MCP server.
  setup-mcp  Add the Agent Skill Router MCP server to an agent's config.
```

---

## `list`

List every skill and slash command the MCP server would load.

```bash
agent-skill-router list [OPTIONS]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--user` | `false` | Show only user-level skills (`~/.agents/skills/` etc.) |
| `--workspace` | `false` | Show only workspace-level skills (`.agents/skills/` etc.) |
| `--workspace-dir PATH` | auto-detect | Explicit workspace root directory |
| `--help` | | Show help |

### Examples

```bash
# Show everything (both workspace and user)
agent-skill-router list

# Show only skills available globally (user-level)
agent-skill-router list --user

# Show only skills scoped to this repository
agent-skill-router list --workspace

# Use a different workspace root
agent-skill-router list --workspace-dir /path/to/project
```

### Sample output

```
SKILLS
  NAME           DIRECTORY                            DESCRIPTION
  -----------------------------------------------------------------------
  run-tests      .agents/skills/run-tests             Use when the user asks to run tests...
  code-review    .claude/skills/code-review           Perform a thorough code review...
  skill-creator  /usr/.../skills/skill-creator        Create new skills, modify and improve...

PROMPTS
  NAME          DESCRIPTION
  -------------------------------------------
  create-skill  Create a new skill from scratch
  fix-bug       Find and fix a bug in the codebase
  review-code   Review code for quality and correctness
```

!!! tip
    Use `--workspace` before committing to verify only project-local skills are included in your repository's scope.

---

## `install`

Install a skill directory into `.agents/skills/` (workspace) or `~/.agents/skills/` (user).

```bash
agent-skill-router install SOURCE [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `SOURCE` | Yes | Path to the skill directory to install. Must contain a `SKILL.md` file. |

### Options

| Option | Default | Description |
|---|---|---|
| `--user` | `false` | Install to `~/.agents/skills/` (user-global) instead of `<workspace>/.agents/skills/` |
| `--force`, `-f` | `false` | Overwrite the skill if it already exists at the destination |
| `--workspace-dir PATH` | auto-detect | Explicit workspace root directory |
| `--help` | | Show help |

### Examples

```bash
# Install a skill into the current project
agent-skill-router install ./my-skill

# Install globally (available in all projects)
agent-skill-router install ./my-skill --user

# Replace an existing skill
agent-skill-router install ./my-skill --force

# Install into a specific workspace
agent-skill-router install ./my-skill --workspace-dir /path/to/project
```

### Behavior

1. Resolves `SOURCE` to an absolute path.
2. Validates that `SOURCE` exists and contains a `SKILL.md` file.
3. Copies the entire directory to the destination.
4. If the skill already exists at the destination and `--force` is not set, exits with an error.

```
Installed 'my-skill' to /project/.agents/skills/my-skill  [workspace (.agents/skills/)]
```

---

## `run`

Start the MCP server over stdio. This is the command agents call to launch the server.

```bash
agent-skill-router run [OPTIONS]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--workspace-dir PATH` | auto-detect | Explicit workspace root directory |
| `--help` | | Show help |

### Examples

```bash
# Start the server (reads all SKILL_ROUTER_* env vars)
agent-skill-router run

# Start with an explicit workspace root
agent-skill-router run --workspace-dir /path/to/project

# Start with specific providers disabled
SKILL_ROUTER_ENABLE_GOOSE=false agent-skill-router run
```

### MCP config

This is how you add `run` to an agent's MCP config:

```json
{
  "mcpServers": {
    "agent-skill-router": {
      "command": "uvx",
      "args": ["agent-skill-router", "run"]
    }
  }
}
```

With an explicit workspace:

```json
{
  "mcpServers": {
    "agent-skill-router": {
      "command": "uvx",
      "args": ["agent-skill-router", "run", "--workspace-dir", "/path/to/project"]
    }
  }
}
```

---

## `setup-mcp`

Add the Agent Skill Router MCP server entry to one or all agents' config files.

```bash
agent-skill-router setup-mcp [AGENT] [OPTIONS]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `AGENT` | No | Agent to configure. Available: `claude`, `github-copilot`, `cursor`, `opencode`, `gemini`, `goose`, `codex`. Omit to auto-configure all. |

### Options

| Option | Default | Description |
|---|---|---|
| `--user` | `false` | Write to the user-scoped config file instead of the workspace one |
| `--help` | | Show help |

### Examples

```bash
# Configure all detected agents (workspace-level)
agent-skill-router setup-mcp

# Configure all detected agents (user-level, applies to all projects)
agent-skill-router setup-mcp --user

# Configure only Claude
agent-skill-router setup-mcp claude

# Configure only Copilot at user level
agent-skill-router setup-mcp github-copilot --user
```

### Behavior

**With an agent name:**

- Writes the MCP server entry to that agent's config file.
- Creates the config file if it does not exist.
- If automated setup is not supported, prints the config file path and manual instructions, then exits with code 1.

**Without an agent name (auto-discover):**

- Iterates every registered provider.
- Installs into providers that support automated install; silently skips the rest.
- If no providers could be configured, prints available options.

### Supported agents

| `AGENT` value | Workspace config | User config |
|---|---|---|
| `claude` | `.claude/mcp.json` | `~/.claude/mcp.json` |
| `github-copilot` | `.vscode/mcp.json` | `~/.vscode/mcp.json` |
| `cursor` | `.cursor/mcp.json` | `~/.cursor/mcp.json` |
| `opencode` | `.opencode/mcp.json` | `~/.config/opencode/opencode.json` |
| `gemini` | `.gemini/settings.json` | `~/.gemini/settings.json` |
| `goose` | `.goose/mcp.json` | `~/.config/goose/config.yaml` |
| `codex` | `.codex/config.toml` | `~/.codex/config.toml` |

---

## Global `--workspace-dir`

All commands except `setup-mcp` accept `--workspace-dir`. This flag overrides the automatic git-root detection and the `SKILL_ROUTER_WORKSPACE_DIR` environment variable.

```bash
# All three commands respect --workspace-dir
agent-skill-router list --workspace-dir /my/project
agent-skill-router install ./skill --workspace-dir /my/project
agent-skill-router run --workspace-dir /my/project
```

The flag must point to an existing directory.
