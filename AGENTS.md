# Zhijian Skills Repository Instructions

## Repository role

This repository is the only editable source for the public Zhijian Skills portfolio.

- Treat `main` as a protected integration branch. Start each task from the live `origin/main` SHA on a short-lived branch, push only that branch, and merge through a PR.
- Before publishing, record and re-check the live remote SHA. A `.git/zhijian-needs-sync.json` marker blocks commits, pulls, and pushes until the checkout is clean and exactly synchronized to `origin/main`.
- `skills/<name>/` is the install payload and must remain self-contained.
- Human documentation lives in `docs/skills/<name>/`.
- Per-Skill release notes live in `docs/changelogs/<name>.md`.
- Do not create or update standalone Skill repositories. Every public Skill is released only from this Portfolio.

## Safety

- Never publish credentials, personal absolute paths, customer data, caches, generated previews, reports, browser profiles, or dependency directories.
- Candidate Skill code runs without release credentials.
- Release and repository-admin credentials stay separate.
- Unknown source drift blocks the affected Skill.
- Never force-push or rewrite published Portfolio history or Tags.

## Verification

Before committing a Skill change:

1. Run the repository-owned Skill validator.
2. Run that Skill's declared deterministic tests.
3. Run its isolated install check.
4. Run Portfolio contract tests when Registry or governance code changes.

The Registry is the single machine-readable source for Skill paths, versions, validation, capabilities, Harness support, and documentation. Mirror metadata is forbidden.
