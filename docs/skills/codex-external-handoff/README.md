# Codex External Handoff

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Codex External Handoff: launch and supervise persistent, named Codex App Server threads from external agents with structured callbacks">
</p>

<p align="center"><strong>Launch and supervise persistent, user-visible Codex App Server threads from WorkBuddy, Claude Code, or any local agent — with structured result callbacks, read-only defaults, and seamless app takeover.</strong></p>

<p align="center"><a href="./README.zh-CN.md">简体中文</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-external-handoff">Canonical source</a></p>

When an external local agent (WorkBuddy, Claude Code, OpenCode, or custom scripts) needs heavy research, cross-repository retrieval, architectural review, or deterministic code modifications, running an ephemeral headless command loses conversation continuity and prevents live supervision. `codex-external-handoff` bridges this gap: it talks to the local `codex app-server` over stdio JSONL RPC, creates a named, durable Codex Thread that is immediately visible in the Codex Desktop app and CLI, supervises background execution, and delivers validated structured findings, evidence, and artifacts back to the calling agent.

## Install

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill codex-external-handoff --agent codex --global --copy --yes
```

## Requirements

- Local `codex` CLI installed and authenticated (`codex auth login` or ChatGPT login)
- Python 3.9 or newer (standard library only, zero third-party dependencies)
- macOS or Linux local host with `codex` in `PATH`
- Codex Desktop App installed (optional, for one-click visual takeover via `codex://threads/<threadId>`)

## What It Does

- **Six lifecycle operations**: `doctor`, `ask`, `continue`, `status`, `result`, `cancel`, and `open`
- **Persistent named threads**: Creates real non-ephemeral Codex threads with explicit titles and thread IDs
- **Background supervision**: Detaches background worker with recoverable local receipts under `CODEX_EXTERNAL_HANDOFF_HOME` or `~/.codex/external-handoff`
- **Structured output schema**: Enforces a strict JSON callback payload containing `status`, `conclusion`, `evidence[]`, `risks[]`, `artifacts[]`, `recommended_actions[]`, and `suggested_state_delta`
- **Read-only by default**: Automatically sets `sandbox=read-only` and `approvalPolicy=never`; requires explicit `--sandbox workspace-write` for authorized file writes
- **Human & agent takeover**: Returns both `codex://threads/<threadId>` URL scheme and `codex resume <threadId>` CLI command for seamless inspection or takeover

## How It Works

1. **Preflight**: Running `doctor` initiates a lightweight stdio session with `codex app-server`, verifies `initialize` / `initialized` handshake, checks account status, and confirms state storage readiness.
2. **Launch (`ask`)**: Prepares a local request snapshot, spawns a detached supervisor worker, and connects to `codex app-server` to execute `thread/start` and `thread/name/set`.
3. **Turn Execution**: Submits `turn/start` with the task payload, configured model (`gpt-5.6-sol` by default), reasoning effort (`high` / `max`), and output schema constraints.
4. **Supervision & Streaming**: Captures `item/agentMessage/delta`, `item/completed`, and `turn/completed` events, periodically writing heartbeat timestamps to the local job receipt.
5. **Result Extraction & Callback**: Parses and validates the structured JSON outcome, marks job status (`completed`, `blocked`, `failed`, `cancelled`, `timed_out`), and returns the full verdict to the calling agent.

## Example Requests

```text
Delegate this deep architecture review to a persistent Codex thread and return its structured findings.
```

```text
Create a named Codex handoff thread to retrieve cross-project references in read-only mode, and give me the threadId.
```

```text
Follow up on the previous Codex handoff thread with new benchmark results, keeping the existing conversation context.
```

Equivalent direct CLI commands:

```bash
# Preflight environment check
python3 scripts/codex_external_handoff.py doctor

# Launch a background handoff task
python3 scripts/codex_external_handoff.py ask \
  --title "System Architecture & Security Review" \
  --task-file ./task-package.md \
  --cwd "$PWD" \
  --model gpt-5.6-sol \
  --effort high

# Check status, fetch results, or open in Codex App
python3 scripts/codex_external_handoff.py status ceh-20260821-100000-abcd1234
python3 scripts/codex_external_handoff.py result ceh-20260821-100000-abcd1234
python3 scripts/codex_external_handoff.py open ceh-20260821-100000-abcd1234
```

## Safety and Limitations

- **Strict Sandbox Defaults**: The default mode is `read-only` with `approvalPolicy=never`. External agents cannot inadvertently overwrite workspace files without explicitly passing `--sandbox workspace-write`.
- **No Danger Mode**: `danger-full-access` execution is intentionally disallowed through this handoff bridge.
- **Isolated State Receipts**: Task contents are deleted from temporary request files immediately upon worker startup; receipts and execution logs are stored locally under `~/.codex/external-handoff` and never written into project Git trees.
- **Single Turn Serial Execution**: A single thread supports one active turn at a time. Concurrent parallel analysis requires launching distinct handoff threads.
- **Local App Server Dependency**: Requires a functional local `codex` binary; remote cloud execution without a local daemon is outside the scope of this bridge.

## Repository Layout

```text
skills/codex-external-handoff/
├── SKILL.md
├── agents/
│   ├── interface.yaml
│   └── openai.yaml
├── evals/
│   ├── semantic_config.json
│   └── trigger_cases.json
├── manifest.json
├── references/
│   ├── app-server-contract.md
│   └── task-package.md
├── requirements.txt
├── scripts/
│   └── codex_external_handoff.py
├── security/
│   └── permission_policy.json
└── tests/
    └── test_codex_external_handoff.py
```

## License

[MIT](../../../LICENSE)
