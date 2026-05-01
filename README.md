# Agent Skill Router

An MCP server that discovers, aggregates, and standardizes reusable agent skills across projects and multiple AI providers — enabling Claude, Gemini, OpenCode, GitHub Copilot, Cursor, and other agents to share the same capabilities seamlessly.

### Key Features

- **Zero-config skill sharing.** Drop a `SKILL.md` file in any supported directory and every connected agent sees it immediately.
- **Multi-vendor.** Reads skills from Claude, Cursor, VS Code Copilot, Codex, Gemini, Goose, OpenCode, and generic `.agents/skills/` directories.
- **Workspace + user scope.** Separate flags to include project-local skills and user-global skills independently.
- **Bundled skill creator.** Ships a `skill-creator` skill and a `create-skill` prompt so agents can author new skills on demand.
- **Fully configurable.** All providers and scopes are toggled via environment variables (`SKILL_ROUTER_*`).

### Requirements

- Python 3.13+
- `uvx` (comes with [uv](https://docs.astral.sh/uv/getting-started/installation/))
- Any MCP client: Claude Code, Claude Desktop, Cursor, VS Code Copilot, opencode, Goose, or any other MCP-compatible tool

### Getting started

Install the Agent Skill Router MCP server with your client.

**Standard config** works in most tools:

```json
{
  "mcpServers": {
    "agent-skill-router": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router"
      ]
    }
  }
}
```

<details>
<summary>Claude Code</summary>

Use the Claude Code CLI to add the Agent Skill Router MCP server:

```bash
claude mcp add agent-skill-router -- uvx --from git+https://github.com/mariotaddeucci/agent-skill-router agent-skill-router
```

</details>

<details>
<summary>Claude Desktop</summary>

Open Claude Desktop and navigate to **File > Settings > Developer**. Click **Edit Config** and add:

```json
{
  "mcpServers": {
    "agent-skill-router": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router"
      ]
    }
  }
}
```

Save the file and perform a hard restart of the Claude app.

</details>

<details>
<summary>Cursor</summary>

Create or edit `.cursor/mcp.json` in your project root (or `~/.cursor/mcp.json` for global):

```json
{
  "mcpServers": {
    "agent-skill-router": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router"
      ]
    }
  }
}
```

</details>

<details>
<summary>VS Code (GitHub Copilot)</summary>

Create `.vscode/mcp.json` in your project:

```json
{
  "servers": {
    "agent-skill-router": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router"
      ]
    }
  }
}
```

Save the file, then click **Start** next to the server in the MCP panel.

</details>

<details>
<summary>opencode</summary>

Add to `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "agent-skill-router": {
      "type": "local",
      "command": [
        "uvx",
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router"
      ],
      "enabled": true
    }
  }
}
```

</details>

<details>
<summary>Goose</summary>

Go to **Advanced settings** → **Extensions** → **Add custom extension**. Use type `STDIO` and set the command to:

```
uvx --from git+https://github.com/mariotaddeucci/agent-skill-router agent-skill-router
```

Or add to your Goose config directly:

```json
{
  "mcpServers": {
    "agent-skill-router": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mariotaddeucci/agent-skill-router",
        "agent-skill-router"
      ]
    }
  }
}
```

</details>

<details>
<summary>Codex (OpenAI)</summary>

Create or edit `~/.codex/config.toml` and add:

```toml
[mcp_servers.agent-skill-router]
command = "uvx"
args = ["--from", "git+https://github.com/mariotaddeucci/agent-skill-router", "agent-skill-router"]
```

</details>

<details>
<summary>Windsurf</summary>

Follow the Windsurf MCP [documentation](https://docs.windsurf.com/windsurf/cascade/mcp). Use the standard config above.

</details>

<details>
<summary>Gemini CLI</summary>

Follow the MCP install [guide](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md#configure-the-mcp-server-in-settingsjson). Use the standard config above.

</details>

### Skill directories discovered

The server automatically scans the following directories (only those that exist on disk are loaded):

| Provider | Workspace path | User path |
|----------|---------------|-----------|
| Claude | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| VS Code / Copilot | `.copilot/skills/` | `~/.copilot/skills/` |
| Codex | `.codex/skills/` | `/etc/codex/skills/`, `~/.codex/skills/` |
| Gemini | `.gemini/skills/` | `~/.gemini/skills/` |
| Goose | `.goose/skills/` | `~/.config/agents/skills/` |
| OpenCode | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Generic agents | `.agents/skills/` | `~/.agents/skills/` |
| OpenClaw | `.openclaw/skills/` | `~/.openclaw/skills/` |
| Bundled | — | shipped inside the package |

All providers use the same `SKILL.md` format — no conversion needed.

Workspace paths are relative to the current working directory (`<cwd>/...`). Both scopes are enabled by default and can be toggled independently via `SKILL_ROUTER_ENABLE_WORKSPACE_LEVEL` and `SKILL_ROUTER_ENABLE_USER_LEVEL`.

### Configuration

All settings are controlled via environment variables with the `SKILL_ROUTER_` prefix.

| Variable | Default | Description |
|----------|---------|-------------|
| `SKILL_ROUTER_ENABLE_WORKSPACE_LEVEL` | `true` | Include workspace-scoped directories (`<cwd>/...`) |
| `SKILL_ROUTER_ENABLE_USER_LEVEL` | `true` | Include user-scoped directories (`~/.../skills/`) |
| `SKILL_ROUTER_ENABLE_BUNDLED` | `true` | Include skills bundled inside the package |
| `SKILL_ROUTER_ENABLE_CLAUDE` | `true` | Claude skills provider |
| `SKILL_ROUTER_ENABLE_CURSOR` | `true` | Cursor skills provider |
| `SKILL_ROUTER_ENABLE_VSCODE` | `true` | VS Code / Copilot skills provider |
| `SKILL_ROUTER_ENABLE_CODEX` | `true` | Codex skills provider |
| `SKILL_ROUTER_ENABLE_GEMINI` | `true` | Gemini skills provider |
| `SKILL_ROUTER_ENABLE_GOOSE` | `true` | Goose skills provider |
| `SKILL_ROUTER_ENABLE_COPILOT` | `true` | GitHub Copilot skills provider |
| `SKILL_ROUTER_ENABLE_OPENCODE` | `true` | OpenCode skills provider |
| `SKILL_ROUTER_ENABLE_AGENTS` | `true` | Generic `.agents/skills/` provider |
| `SKILL_ROUTER_ENABLE_OPENCLAW` | `true` | OpenClaw skills provider |
| `SKILL_ROUTER_EXTRA_DIRS` | `[]` | Additional directories (JSON array of `{"path": "..."}`) |

**Example: workspace-only skills, no Claude:**

```bash
SKILL_ROUTER_ENABLE_USER_LEVEL=false \
SKILL_ROUTER_ENABLE_CLAUDE=false \
uvx --from git+https://github.com/mariotaddeucci/agent-skill-router agent-skill-router
```

**Example: add an extra custom directory:**

```bash
SKILL_ROUTER_EXTRA_DIRS='[{"path": "/my/team/skills"}]' \
uvx --from git+https://github.com/mariotaddeucci/agent-skill-router agent-skill-router
```

Extra directories are always loaded regardless of the workspace/user scope flags.

### Prompts

The server exposes a `create-skill` prompt that helps any connected agent author a new skill:

- **`create-skill(goal, save_to_user_level=false)`** — returns instructions to create a skill for the given goal. By default saves to `<cwd>/.agents/skills/` (workspace); set `save_to_user_level=true` to save to `~/.agents/skills/` (all workspaces).

The bundled `skill-creator` skill is automatically available to guide the agent through the skill-authoring process.

### CLI

The package ships a CLI for managing skills and starting the server without writing any config.

**List all skills the server would load:**

```bash
uvx --from git+https://github.com/mariotaddeucci/agent-skill-router agent-skill-router list
```

Filter by scope:

```bash
agent-skill-router list --workspace   # workspace-scoped skills only
agent-skill-router list --user        # user-scoped skills only
```

**Install a skill into your project:**

```bash
agent-skill-router install ./path/to/my-skill
```

Installs to `.agents/skills/` in the current directory. Use `--user` to install globally (`~/.agents/skills/`):

```bash
agent-skill-router install ./path/to/my-skill --user
```

Use `--force` / `-f` to overwrite an existing skill with the same name.

**Start the MCP server directly:**

```bash
agent-skill-router run
```

### What is a skill?

A skill is a directory containing a `SKILL.md` file with structured instructions that an AI assistant loads to perform a specific task consistently. Think of it as a reusable playbook — once written, every agent that connects to this MCP server can use it.

```
.agents/skills/
└── my-skill/
    └── SKILL.md      ← instructions the agent follows
    └── template.py   ← optional supporting files (also exposed as resources)
```
