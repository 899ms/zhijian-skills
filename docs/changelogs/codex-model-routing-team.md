# codex-model-routing-team Changelog

## Unreleased

- Make `speed` a versioned RoutePlan dimension with backward-compatible legacy Standard behavior.
- Default automatic routing to Luna XHigh App Thread, raise difficult or high-risk tasks to Luna Max, and keep native V2 only for explicit requests or predeclared fallback.
- Treat Luna as App-only while the official native V2 live schema omits it; require Sol High or stronger on every Surface and reject Sol Medium/Low even when explicitly requested.
- Require live `create_thread` speed evidence for App Luna Fast; keep Sol, Terra, and other models on Standard while preserving separate requested/accepted/observed speed audit fields.
- Slim initial Skill/interface context from 1708 to 890 estimated tokens by keeping only triggers, branch selection, the shared execution skeleton, hard gates, and the output contract; defer detailed policy and lifecycle rules to existing references.

## 2.1.0 — 2026-07-27

- Add a `native-light` profile for bounded OpenAI native Workers: load only relevant policies, keep coordination state in memory, and avoid `agent_team/` files.
- Keep recovery, worktree, independent history, high-risk approval, cross-Provider, and fallback work on the fully governed path; duration and file count are now signals rather than standalone App Thread triggers.
- Accept RoutePlan and ledger JSON from stdin while preserving existing file-path validation and all model, Provider, attempt, identity, and lifecycle gates.

## 2.0.0 — 2026-07-27

- Upgrade the Thread-only router into a dual-surface router: exact-model native subagents for bounded parent-integrated work and Codex App threads for durable, recoverable, worktree, or audit-heavy work.
- Add live native spawn confirmation, V1/V2 fresh-context rules, separate requested/accepted/observed model identity, native close gates, and mixed-surface ledger validation.
- Bind native runtime evidence to host/Surface/model/thinking with a 10-minute TTL; Responses semantic probes cannot authorize native spawn routes.
- Reject non-boolean authorization fields, mismatched native identity, inherited context, unclosed completed agents, and inconsistent legacy/canonical attempt counters.
- Add explicit `surface` RoutePlan candidates with backward-compatible omission defaulting to `app_thread`; cross-surface fallback remains deterministic and predeclared.
- Add native Sol low/medium/high profiles. Register `gpt-5.6-terra` as opt-in, first-candidate-only, default-off, and never a silent fallback.
- Preserve the existing Luna/Sol/Grok/Gemini provider policy, one- or two-candidate ceilings, Thread recovery invariants, and upstream Skill stage gates.

### Additional 2.0.0 release details

- Replace the two-model hardcoded policy with a registry-driven four-model policy covering Luna, Sol, conditional Grok 4.5, and a provider-blocked Antigravity Gemini entry that preserves a future official-route template.
- Add provider/data-boundary gates, deterministic candidate chains, scoped circuit breakers, and a two-Worker recovery ceiling.
- Add dependency-free model and RoutePlan validators for registry/runtime evidence, optional semantic nonces, ordered fallbacks, Provider allowlists, and minimum thinking.
- Add a single audit schema with conservative creation-attempt accounting and backward-compatible `model` records.
- Expand contract tests and evaluation cases for provider quota, semantic mismatch, MCP isolation, and explicit Gemini routing.
- Add a minimal Thread supervision state model inspired by FirstMate's authoritative-state and reconciliation contracts, without importing its terminal fleet runtime.
- Support queued `pendingWorktreeId` creation through unique task-id discovery and stable official observations; ambiguous zero/multiple matches now remain `UNKNOWN` and block follow-up, fallback, duplicate creation, and archival.
- Add task-intent mutation boundaries, durable resume ordering, a dependency-free team-ledger validator, and focused regression coverage for state truth, pending recovery, archive gates, and duplicate prevention.

## 1.0.4 — 2026-07-26

- Admit `gpt-5.6-sol` with `medium` thinking for explicit single-candidate RoutePlans after live runtime support is confirmed.
- Keep default task profiles at their existing `high` or stronger minimum; the new level never silently downgrades automatic routing.

## 1.0.3 — 2026-07-26

- Allow a one-candidate RoutePlan to declare `max_worker_threads: 1` when failure returns directly to the lead Agent.
- Require the Worker ceiling to match the declared candidate count, preventing undeclared fallback capacity.

## 1.0.2 — 2026-07-17

- Publish and install exclusively through `zjp1997720/zhijian-skills`.

## 1.0.1 — 2026-07-17

- Add a brand-aligned light README hero and clearer bilingual first-screen guidance.
- Preserve the existing Codex App model-routing contract and runtime behavior.

## 1.0.0 — 2026-07-16

- Establish the first independently versioned governance baseline.
- Preserve explicit Codex App model routing, bounded concurrency, task packets, and lifecycle contracts.
