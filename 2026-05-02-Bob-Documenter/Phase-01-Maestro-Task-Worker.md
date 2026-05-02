# Phase 01: Setup Maestro Configuration

Create the `.maestro/` directory and `cue.yaml` configuration file to enable task pooling from TODO.md with max concurrency of 1.

## Tasks

- [x] Create `.maestro/` directory in project root: `mkdir -p .maestro`
- [x] Create `.maestro/cue.yaml` with the following configuration:
  - settings: timeout_minutes: 45, max_concurrent: 1, queue_size: 15
  - subscriptions section with one entry for "Task Worker" that watches TODO.md
  - event: task.pending, watch: 'TODO.md', poll_minutes: 5
  - prompt that extracts pending tasks and processes one at a time, then marks it complete in TODO.md

```yaml
settings:
  timeout_minutes: 45
  max_concurrent: 1
  queue_size: 15

subscriptions:
  - name: Task Worker
    label: Task Worker
    event: task.pending
    watch: 'TODO.md'
    poll_minutes: 5
    prompt: |
      There are pending tasks in TODO.md:
      {content}

      Pick the highest priority pending task and complete it.
      When done, check off the task in the file by replacing "- [ ]" with "- [x]".
```
