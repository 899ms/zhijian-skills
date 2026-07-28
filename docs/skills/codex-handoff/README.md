# Codex Handoff

Continue an oversized or slow Codex task in a fresh user-visible task without copying the full conversation history.

[简体中文](./README.zh-CN.md) · [Canonical source](https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-handoff)

## Install

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill codex-handoff --agent codex --global --copy --yes
```

Invoke it explicitly:

```text
$codex-handoff Continue the release verification in a fresh task.
```

## Requirements

- Codex Desktop with user-visible task creation tools.
- A current saved project that Codex can resolve when the work depends on project files.
- Explicit invocation. Automatic activation is disabled because creating a task changes app state.

## What It Does

Long-lived Codex tasks can accumulate enough history that every new model turn must process a large context, even after compaction. `codex-handoff` treats this as a context-rollover problem:

- distills only the objective, verified state, decisions, authoritative artifacts, failures, remaining work, fragile state, and useful Skills;
- targets a compact continuity prompt instead of copying the transcript;
- creates one fresh, user-visible Codex task in the resolved project;
- preserves the configured model unless the user explicitly requests an override;
- starts the next action in the new task and stops work in the old one.

The old task remains available as history. The new task no longer pays the per-turn cost of carrying the complete conversation.

## How It Works

```text
Oversized current task
  → verify workspace and active instructions
  → compress continuity into a pointer-first prompt
  → resolve the saved Codex project
  → create and title one fresh task
  → begin the next action there
  → leave the old task unchanged as history
```

The continuity prompt points to plans, files, issues, commits, diffs, and URLs instead of duplicating them. Secrets, credentials, unrelated personal information, giant status output, and repeated reasoning are excluded.

## Example Requests

```text
$codex-handoff This task is getting slow. Continue from the first failing release check in a fresh task.
```

```text
$codex-handoff Roll this oversized conversation into a fresh task and finish the remaining documentation work.
```

```text
$codex-handoff 新 task 只继续完成测试、PR 和发布验证。
```

## Safety and Limitations

- It does not fork full history, spawn an internal subagent, move another task's Git checkout, or write a handoff document.
- It does not trigger for ordinary continuation in the current task.
- It follows project instructions and Codex environment policy. If material uncommitted state would be missing, it stops before creating an unsafe continuation.
- A queued worktree setup is reported as queued, not as a running task.
- Temporary and machine-local paths are marked as fragile.
- If Codex task tools are unavailable, the Skill stops instead of simulating success.

## Development

```bash
python3 -m unittest discover -s skills/codex-handoff/tests -v
```

The package includes manual-trigger positives, negatives, near neighbors, and output contract fixtures under `evals/`.

## License

[MIT](../../../LICENSE)
