# workbuddy-cli-model-bridge Changelog

## 1.1.0 — 2026-07-24

- Make local model catalogs Provider-declared with safe JSON and TOML field mappings.
- Require exact, sourced input/output token limits before registration.
- Add a bounded live probe for declared maximum output parameters.
- Add verified Grok 4.5 and Gemini 3.6/3.5 Flash limits.
- Expand tests across Codex, Grok, Gemini, generic Providers, invalid evidence, missing limits, and route rejection.

## 1.0.1 — 2026-07-24

- Resolve token limits by exact model ID so GPT-5.6 metadata cannot leak into older fallback candidates.
- Prefer an exact local CLIProxyAPI/OpenCodex route context window over the public API fallback.
- Register GPT-5.6 Sol and Fast with verified output limits and route-correct input limits.
- Add malformed-catalog, precedence, fallback-isolation, and synchronized-output coverage.

## 1.0.0 — 2026-07-22

- Add a macOS-first CLIProxyAPI-to-WorkBuddy convergence workflow.
- Bundle verified Codex, xAI/Grok, and Antigravity Provider manifests.
- Add live text, streaming, tool, image, and reasoning-control probes.
- Use a 256×192 two-shape vision fixture to avoid false negatives from tiny monochrome probe images.
- Preserve manual WorkBuddy models through owned, atomic, idempotent merges.
- Add a validated machine-local Provider extension contract for new CLIs.
- Add isolated integration tests with credential-redaction and rollback coverage.
