# Changelog: codex-external-handoff

## 1.0.0 - 2026-08-21

### Added
- Initial public release of `codex-external-handoff`.
- Deterministic CLI wrapper (`scripts/codex_external_handoff.py`) over `codex app-server` stdio JSONL protocol.
- Six core operations: `doctor`, `ask`, `continue`, `status`, `result`, `cancel`, and `open`.
- Recoverable background job receipts and log management under `CODEX_EXTERNAL_HANDOFF_HOME` / `~/.codex/external-handoff`.
- Structured JSON result contract with `status`, `conclusion`, `evidence`, `risks`, `artifacts`, `recommended_actions`, and `suggested_state_delta`.
- Read-only sandbox enforcement by default with explicit `workspace-write` authorization gate.
- Direct desktop handoff via `codex://threads/<threadId>` URL scheme and `codex resume <threadId>` CLI command.
