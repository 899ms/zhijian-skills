# Leadbook

Turn a business topic into an evidence-backed Chinese short book, white paper, methodology book, or playbook with an auditable project structure.

## Install

```bash
npx skills add zjp1997720/zhijian-skills \
  -g -a codex --skill leadbook --copy -y
```

Then ask Codex to use `$leadbook` with a topic, audience, or working title.

## Requirements

- Python 3.10+ for the standard-library Core workflow.
- Default: the public Web for factual, behavioral, transactional, and discourse evidence.
- Optional: WeChat, Xiaohongshu, and local-content providers; their absence does not block the Core workflow.
- Optional: Kami plus WeasyPrint or Chrome/Chromium for higher-fidelity HTML and PDF output.

The Core scaffold, state sync, Markdown export, SVG generation, and quality checks run without external services.

## What It Does

- Creates a structured book project instead of producing one untracked long response.
- Separates book brief, reader, positioning, evidence ledgers, chapters, visuals, and distribution materials.
- Uses six evidence layers for facts, demand, behavior, transactions, discourse, and owned experience.
- Supports white papers, playbooks, methodology books, business reports, and course manuals.
- Keeps unfinished chapter templates out of WIP exports.
- Enforces distinct `draft`, `review-ready`, and `publish-ready` quality gates.
- Requires direct, verifiable URLs for public facts, behavior signals, and transaction signals.
- Persists durable phase checkpoints in `.leadbook-run.json` for exact recovery after an interrupted run.
- Promotes maturity only through digest-bound gate receipts instead of manual state edits.
- Renders every PDF page and prepares a contact sheet plus page-by-page visual QA checklist.
- Allows planned visuals to remain unbuilt at the pre-build `draft` gate while enforcing real assets at review and publish gates.
- Rejects orphaned bibliography entries or mostly blank trailing reference pages at the publish visual gate.
- Produces Markdown first, with optional SVG, HTML, PDF, worksheets, and distribution materials.

## How It Works

1. Scaffold a marked Leadbook project and synchronize the initial chapter tree.
2. Write a v0 brief, reader profile, positioning, evidence plan, opening, and outline.
3. Research from the public Web by default and map specific source URLs to chapters.
4. Write one chapter at a time, remove its template marker, and synchronize state.
5. Export Markdown; untouched chapters stay out of the WIP manuscript.
6. Generate diagrams, HTML, and PDF, then complete page-by-page visual QA.
7. Use `check-leadbook.py --update-state` to issue the maturity gate receipt.

State synchronization merges existing progress and recomputes chapter words, references, and cases. The scaffold refuses to replace an unmarked non-empty directory.

## Example Requests

```text
Use $leadbook to create a Chinese white paper for SME owners adopting AI agents.
```

```text
Use $leadbook to continue chapter three of this book and export an honest WIP draft.
```

```text
Use $leadbook to audit this book for publish-ready status without fabricating missing evidence.
```

## Safety or Limitations

- `--force` replaces only a directory carrying the generated `.leadbook-project.json` marker.
- Optional provider failure remains visible in project state; it is never reported as complete.
- Xiaohongshu detail tokens stay in memory and are removed from output. IP-location labels are omitted by default.
- Non-loopback Xiaohongshu providers require an explicit flag because detail requests transmit a short-lived token.
- Automated quality checks do not replace human source review or page-by-page PDF visual inspection.
- Search terms, site names, homepages, and generic “public case page” descriptions do not count as evidence.
- A claimed `review_ready` or `publish_ready` state must carry a receipt matching the current artifacts.
- Gate transactions synchronize visual coverage, and a failed publish gate preserves any still-valid `review-ready` visual state.
- The built-in HTML template is intentionally basic; Kami is optional and produces the preferred editorial layout.

## Repository Layout

```text
skills/leadbook/
├── SKILL.md
├── agents/
├── assets/repo-template/
├── evals/
├── references/
├── scripts/
└── tests/
```

## License

[MIT](../../../skills/leadbook/LICENSE)
