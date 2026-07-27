# Canonical Portfolio mode

Zhijian Skills publishes every public Skill from `zjp1997720/zhijian-skills`. A local `SKILL.md` is always imported into this Portfolio; it never becomes a standalone repository.

## Entry contract

The canonical checkout contains:

- `registry/skills.json`
- `skills/<name>/SKILL.md` for every active record
- bilingual documentation and a Changelog referenced by the Registry
- a lockfile-pinned `skills` CLI
- an `origin` that resolves to `zjp1997720/zhijian-skills`

Run:

```bash
python3 <skill-open-sourcer-dir>/scripts/portfolio.py audit \
  --repo <zhijian-skills> --strict
```

## Release flow

1. Audit the canonical repository and the incoming Skill.
2. Sanitize and copy the complete payload into `skills/<name>/`.
3. Add bilingual docs, Changelog, Registry metadata, catalog entry, and visual assets.
4. Run declared tests, Portfolio contracts, local discovery, and isolated copy installation.
5. Build one immutable candidate per changed Skill and produce one dry-run summary.
6. Record the live remote SHA in the frozen plan, verify it again immediately before publishing, push only a short-lived branch, and merge through a PR into protected canonical `main`.
7. Record the verified merged SHA in the release ledger. A temporary integration clone marks its original checkout `needs-sync`; that checkout cannot commit again until it is clean and exactly synchronized to remote `main`.
8. Verify the remote Portfolio, then create only the canonical Tag `<skill>/v<version>` and resume interrupted releases from verified state.

No step creates, updates, redirects, or releases a standalone Skill repository.
