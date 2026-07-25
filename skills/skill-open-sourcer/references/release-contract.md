# Portfolio Release Contract

Single-Skill releases start with `release_portfolio.py plan --skill <name> --dry-run`. Intentional Portfolio waves use `--all` plus optional repeated `--exclude <name>`. `--skill` and `--all` are mutually exclusive, and `--exclude` cannot be combined with `--skill`. The plan freezes the canonical commit, selected Skill payload and documentation digests, exact versions and tags, validation commands, candidate refs, and executor identity. Local candidate refs are implementation details, never branches.

Execution must call `verify` before every remote wave. A changed source file, Registry, schema, governance script, pinned `skills` CLI, Python, or Node runtime invalidates the plan. Credential-bearing release processes must never be reused for candidate tests or package export.

Remote progress is recorded in an atomic, plan-scoped XDG state ledger. Verified steps are idempotent; interrupted releases resume from remote verification rather than repeating or rewriting history.
