---
hide:
  - navigation
  - toc
---

# Writing Skills

A **skill** is a directory that teaches an AI agent how to perform a specific, reusable task. The router discovers skills from many locations and exposes them to every connected agent via MCP.

---

## Anatomy of a skill

```
my-skill/
├── SKILL.md          ← required: instructions + metadata
├── scripts/          ← optional: helper scripts the agent can run
├── references/       ← optional: reference docs, standards, examples
└── assets/           ← optional: templates, config files, other resources
```

The only required file is `SKILL.md`. Everything else in the directory is automatically registered as an MCP resource and becomes accessible to the agent.

---

## SKILL.md format

`SKILL.md` is a Markdown file with a YAML frontmatter block followed by the skill's instruction body.

```markdown
---
name: my-skill
description: >
  Use this skill when you need to <do something specific>.
  Triggers on: <keywords or conditions>.
defaults:
  output_dir: .agents/skills
---

## What this skill does

Detailed instructions for the agent go here. Write in plain English,
as if explaining to a careful developer.

## Steps

1. First, ...
2. Then, ...
3. Finally, ...

## Examples

...
```

### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Unique identifier. Should match the directory name. |
| `description` | Yes | **Critical.** Tells the agent *when* to use this skill. The agent reads this to decide whether to invoke the skill. Write it as a trigger condition, not a title. |
| `defaults` | No | Default values the skill can reference. Commonly used for `output_dir`. |
| `compatibility` | No | Tools or environment requirements (e.g. `requires: [git, gh]`). |

!!! warning "The `description` field drives invocation"
    The `description` is the most important field. Agents use it to decide when to load and use the skill. Be explicit about trigger conditions:

    **Bad:** `"A skill for writing tests"`
    **Good:** `"Use when the user asks to write, add, or improve tests. Triggers on: write tests, add coverage, test this function, improve test suite."`

---

## Where to put skills

Choose the right location based on who should have access:

| Location | Scope | Use case |
|---|---|---|
| `<workspace>/.agents/skills/` | Project | Skills specific to this repository |
| `~/.agents/skills/` | User (global) | Personal skills used across all projects |
| `<workspace>/.claude/skills/` | Project (Claude path) | Skills placed where Claude looks first |

The `.agents/skills/` path is recommended for most cases — it is agent-agnostic and always discovered regardless of which agent the user is running.

---

## Installing a skill

### From a local directory

```bash
# Install into the current workspace
agent-skill-router install ./path/to/my-skill

# Install globally (available in all projects)
agent-skill-router install ./path/to/my-skill --user

# Overwrite an existing skill
agent-skill-router install ./path/to/my-skill --force
```

### Using the built-in `create-skill` prompt

Any connected agent can call the `create-skill` MCP prompt to generate a new skill from scratch:

```
create-skill(
  goal="Write a skill that runs our test suite and summarizes failures",
  save_to_user_level=False
)
```

The agent will use the bundled `skill-creator` skill — which contains detailed instructions for writing high-quality skills — to produce the result and save it to the appropriate directory.

---

## Complete example: `run-tests` skill

```
.agents/skills/
└── run-tests/
    ├── SKILL.md
    └── scripts/
        └── summarize-failures.sh
```

```markdown title=".agents/skills/run-tests/SKILL.md"
---
name: run-tests
description: >
  Use when the user asks to run tests, check test coverage, execute the test
  suite, or diagnose test failures. Triggers on: run tests, check coverage,
  why are tests failing, fix failing tests.
defaults:
  test_command: uv run pytest
---

## Running the test suite

Run the full test suite with:

```bash
{{ defaults.test_command }} --tb=short -q
```

If tests fail, use `scripts/summarize-failures.sh` to produce a concise summary
before reporting results to the user.

## Interpreting results

- **All pass** → report count and elapsed time.
- **Some fail** → list each failed test with its error message. Do not truncate.
- **Import errors** → check for missing dependencies before reporting a test failure.
```

---

## Verifying discovered skills

```bash
# List all skills the server would expose
agent-skill-router list

# List only workspace-level skills
agent-skill-router list --workspace

# List only user-level skills
agent-skill-router list --user
```

Example output:

```
SKILLS
  NAME        DIRECTORY                        DESCRIPTION
  --------------------------------------------------------------------------
  run-tests   .agents/skills/run-tests         Use when the user asks to run tests...
  skill-creator  /usr/.../skills/skill-creator  Create new skills, modify and improve...

PROMPTS
  NAME          DESCRIPTION
  -------------------------------------------
  create-skill  Create a new skill from scratch
  fix-bug       Find and fix a bug in the codebase
```
