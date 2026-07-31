# codex-model-routing-team characterization

- **Trigger contract:** Route complex parallel Codex work to independently configured background tasks.
- **Boundary:** Use native `spawn_agent` only when the live schema accepts the exact model/reasoning/speed tuple; simple or destructive tasks do not auto-dispatch.
- **Workflow invariant:** Main Agent plans, assigns, validates, integrates, and archives bounded Worker tasks.
- **Output invariant:** Traceable task packets, model/thinking/speed choices, lifecycle state, and integrated evidence.
- **Resource graph:** routing, task-packet, lifecycle, durable-mode, upstream-adapter, validation references, and agent metadata.
