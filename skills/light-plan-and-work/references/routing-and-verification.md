# Routing and verification

## Escalation test

Escalate because coordination cost, ambiguity, or consequence is high. Task length alone is not a heavy condition.

Use a heavy workflow when one or more signals are present:

- an operation is destructive or difficult to recover;
- production data, authentication, billing, security, legal, or compliance is in scope;
- the work changes a public API, performs a migration, or coordinates a release;
- architecture spans multiple systems or repositories;
- multiple agents, teams, owners, or approvers need a durable shared contract;
- inspection cannot resolve acceptance criteria without a material product or business choice;
- the user explicitly requests a full specification, detailed implementation plan, or Compound Engineering.

Before switching, keep read-only findings and completed safe work. Pause only mutations affected by the heavy condition. The heavier plan should make migration, verification, rollback, ownership, and approval boundaries explicit when relevant.

## Specialist and discovery routes

- Use a specialist Skill when it owns the artifact: Skill creation, slides, course compilation, deep research, publication, or another defined production workflow.
- Use `brainstorming` when direction benefits from open exploration.
- Use `batch-grill-me` when many user decisions can be asked in dependency-aware batches.
- Return to `light-plan-and-work` after direction and acceptance criteria are settled.

## Plan quality

A useful step names an observable change or proof:

> Update the project-level prototype workflow so it never creates branches, then run a Git-side-effect check.

Avoid activity labels such as “think about the prototype.” Replace obsolete steps when evidence changes instead of preserving a fictional sequence.

## Verification matrix

- Knowledge work: factual consistency, requested structure, audience, path, and delivery readiness.
- Documents or content: required sections, claims, references, rendering, and export when relevant.
- Code or configuration: targeted tests, lint or type checks, smoke run, diff, and side-effect audit.
- Repository work: status, intended file set, secrets and temporary-file scan, plus remote divergence before publishing.

A passing command proves only the contract it checks. Record unverified assumptions as residual risk.

## Blocked verification protocol

A failed broad gate is not automatically evidence that the current task failed. Classify it with read-only evidence before changing anything:

1. Record the exact command, exit status, and first actionable failure.
2. Compare the failing paths and contract with the task boundary, repository status, and task diff.
3. If the failure is demonstrably pre-existing and unrelated, do not revert, stash, edit, stage, or otherwise absorb that work. Run the strongest targeted checks that directly exercise the changed artifact.
4. In the handoff, state the broad gate as blocked, name the unrelated cause, list the targeted checks that passed, and keep the residual risk explicit. Do not describe the repository or release as fully green.
5. If failing paths overlap task files, provenance is uncertain, the targeted checks also fail, or the broad gate is mandatory for a release, treat the failure as part of the task. Fix it within scope or stop and escalate.

This protocol preserves honest verification coverage. It does not waive release gates, reduce authorization requirements, or turn an unexplained failure into a pass.

## Handoff contract

Lead with the outcome, then include changed files or artifacts, verification performed, blocked broad gates with attribution, and any residual risk or intentional deferral. Do not append an unrelated menu of next steps when the requested outcome is complete.
