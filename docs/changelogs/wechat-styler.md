# wechat-styler Changelog

## 1.9.0 — 2026-07-25

- Refine the `zhijian` long-form theme: reserve warm terracotta for chapter/action cues, render ordinary quotations as trust-blue context blocks, restore neutral bold text, and improve mobile reading rhythm.
- Add a type=77 cover state machine that recognizes CSS-background thumbnails and falls back to uploading a local `--cover-file`, selecting it by filename, and completing crop confirmation.
- Treat WeChat qlogo and qpic image hosts as settled instead of reporting them as pending transfers.
- Normalize missing OpenCLI fields and confirm saves through `appmsgid` plus either the saved banner or version history.
- Write a token-redacted diagnostic report on every failed phase with read-only live state and concrete recovery actions.
- Give every optimized remote image a stable hashed basename and stop when PicGo collapses distinct sources to one URL.
- Add restrained, standard, and rich component-density guidance while preserving the standard 3-6 component default.
- Add a 390px mobile visual QA gate for quote alignment, overflow, broken images, duplicate image URLs, and Zhijian heading semantics.
- Keep OpenCLI as the verified WeChat injection backend after Codex Chrome rejected the article editor at the browser-policy boundary; document the no-CDP-bypass rule and the four-part acceptance gate for future backends.
- Remove the author-machine OpenCLI profile default and require an explicit `--profile` or `OPENCLI_PROFILE` value.

## 1.0.3 — 2026-07-17

- Publish and install exclusively through `zjp1997720/zhijian-skills`.

## 1.0.2 — 2026-07-17

- Add a brand-aligned light README hero and polish the bilingual feature explanation.
- Correct workflow numbering and the documented standalone mirror layout.

## 1.0.1 — 2026-07-17

- Open generated HTML with an argument-safe subprocess call so crafted output paths cannot be interpreted by a shell.
- Add a regression test that uses a shell-shaped filename and verifies no injected command runs.

## 1.0.0 — 2026-07-16

- Establish the public Skill governance baseline from the active local 1.8.0 runtime.
- Include themes, component mode, SVG animation, image pipeline, OpenCLI integration, and deterministic tests.
