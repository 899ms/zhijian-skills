# codex-model-routing-team characterization

- **Trigger contract:** Route complex parallel Codex work to independently configured background tasks.
- **Boundary:** Default to Luna XHigh/Max App threads; use native `spawn_agent` only for explicit or predeclared fallback routes accepted by the live schema. Native Luna and Sol below High are rejected.
- **Workflow invariant:** Main Agent plans, assigns, validates, integrates, and archives bounded Worker tasks.
- **Output invariant:** Traceable task packets, model/thinking/speed choices, lifecycle state, and integrated evidence.
- **Resource graph:** routing, task-packet, lifecycle, durable-mode, upstream-adapter, validation references, and agent metadata.
