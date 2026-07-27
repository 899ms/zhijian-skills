# Portfolio Release Contract

Single-Skill releases start with `release_portfolio.py plan --source-checkout <original-checkout> --skill <name> --dry-run`. Intentional Portfolio waves use `--all` plus optional repeated `--exclude <name>`. `--skill` and `--all` are mutually exclusive, and `--exclude` cannot be combined with `--skill`. The plan freezes the canonical commit, live `origin/main` SHA, original checkout, selected Skill payload and documentation digests, exact versions and tags, validation commands, candidate refs, and executor identity. Candidate refs are local implementation details; publication uses a short-lived branch and PR.

Execution must call `verify` immediately before every remote wave. It repeats `git ls-remote`; remote drift, a changed source file, Registry, schema, governance script, pinned `skills` CLI, Python, or Node runtime invalidates the plan. Credential-bearing release processes must never be reused for candidate tests or package export.

When the release repository is a temporary clean clone, planning writes a `release-in-progress` marker into the original checkout and installs a pre-commit guard. After the PR merge, `record-step --step canonical-pushed --remote-sha <sha>` verifies that live `main` contains the planned source, records the transition, and upgrades the marker to `needs-sync`. The marker clears only when the original checkout is clean and local `HEAD` equals the verified remote SHA.

Remote progress is recorded in an atomic, plan-scoped XDG state ledger. Verified steps are idempotent; interrupted releases resume from remote verification rather than repeating or rewriting history.
