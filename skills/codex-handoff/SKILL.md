---
name: codex-handoff
description: Roll an oversized or slow Codex task into a fresh user-visible task with compact continuity. Use only for an explicit handoff or context rollover; not for ordinary continuation, delegation, full-history forks, Git migration, or handoff files.
argument-hint: "[focus for the fresh task]"
disable-model-invocation: true
---

# Codex Handoff

## Preconditions

- Explicit invocation approves one user-owned task. Arguments set its focus; otherwise recover the current objective from verified context.
- Require `list_projects` and `create_thread`. If unavailable, stop; do not substitute a shell command or Markdown file.

## Build the continuity prompt

Write a self-contained prompt of roughly 2,000–4,000 Chinese characters or comparable size. Prefer smaller when links carry detail. Include:

- objective and first action;
- completed work and current state;
- decisions, constraints, and material rejected alternatives;
- authoritative files, plans, issues, commits, diffs, or URLs;
- verification performed and failures observed;
- remaining work, blockers, fragile state, and transient paths;
- relevant installed Skills.

Point to authoritative artifacts instead of reproducing them. Omit transcript history, large diffs or status output, repeated reasoning, secrets, credentials, and unrelated personal information. Mark transient paths as fragile. End with: read active instructions, verify current state, and begin the first action now.

## Create the fresh task

1. Resolve the current saved project with `list_projects`; obey project and host environment rules. Never guess another project or silently fall back to projectless. If the target omits material uncommitted state, stop and state the risk.
2. Call `create_thread` with the compact prompt. Omit model and reasoning overrides unless explicitly requested.
3. For a ready `threadId`, title it with `set_thread_title` and take one bounded `wait_threads` snapshot; do not wait for completion. For only `clientThreadId`, report setup as queued, not running.
4. Return a one-line summary and the created-task directive. Claim only the returned state.
5. Stop work in the old task. Keep it as history; do not archive it or keep editing the shared workspace.

## Exclusions

- Do not use `fork_thread`; full-history copies defeat the context reset.
- Do not spawn a subagent; delegation is not a user-owned continuation task.
- Do not use `handoff_thread`; it moves another task's Git environment.
- Do not create or resume a handoff document; that is a file-oriented workflow.
- Do not trigger on ordinary requests to continue in the current task.

Maintain the manual trigger boundary with `evals/trigger_cases.json` and the continuity behavior with `evals/output/cases.jsonl`.
