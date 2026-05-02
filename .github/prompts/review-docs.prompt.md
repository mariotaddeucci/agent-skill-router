---
description: "Review recent repository changes and check if documentation and README are up to date. Use when: checking docs after commits, validating README accuracy, reviewing documentation coverage, post-PR doc review."
name: "Review Docs After Changes"
argument-hint: "Time period to review (e.g. '1 day', '3 days', '1 week') — defaults to 1 day"
agent: "agent"
tools: ["git_diff", "git_log", "read_file", "grep_search", "file_search", "semantic_search"]
---

Review the recent changes in this repository and assess whether the documentation is accurate and complete.

## Step 1 — Collect recent changes

Run `git log --oneline --since="$ARGS"` (default: `1 day ago`) to list commits.
Then run `git diff HEAD~<n> HEAD -- .` (or `git diff --stat @{1.day.ago}`) to see all files changed.

If the user provided a time argument, use that instead of the default `1 day ago`.

## Step 2 — Analyse what changed

For each changed file, understand:
- What was added, removed, or modified (features, options, commands, behaviour)
- Whether it is a source file, config, test, or existing doc
- Whether the change is user-facing (API, CLI, config keys, output format, etc.)

## Step 3 — Identify documentation that must be reviewed

Cross-reference the changed files against the documentation sources in this project:
- [README.md](../../README.md)
- [docs/](../../docs/) — all Markdown files
- [AGENTS.md](../../AGENTS.md) / [CLAUDE.md](../../CLAUDE.md) — contributor guides

For each doc file, check:
1. Does it still accurately describe the current behaviour?
2. Are new options, commands, or config keys documented?
3. Are removed or renamed items still mentioned?
4. Are code examples, default values, and flag names correct?

## Step 4 — Report

Produce a structured report with the following sections:

### Summary of Changes
Brief bullet list of what changed (files + purpose).

### Documentation Status
A table with columns: **Doc file** | **Status** | **Issue**.

Status values: ✅ Up to date | ⚠️ Needs update | ❌ Missing coverage.

### Recommended Actions
Numbered list of specific edits to make, referencing exact doc files and sections.
If a section is fully up to date, say so explicitly — no action needed.

### Optional: Apply fixes
After showing the report, ask the user: "Would you like me to apply the recommended documentation fixes now?"
If yes, make the edits directly.
