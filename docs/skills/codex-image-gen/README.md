# Codex Image Gen

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Codex Image Gen reuses the local Codex CLI OAuth login to stream gpt-image-2 results into local PNG files">
</p>

<p align="center"><strong>Turn an already-logged-in Codex CLI into image generation for any Agent — no API key, one dependency-free Python script.</strong></p>

<p align="center"><a href="./README.zh-CN.md">简体中文</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-image-gen">Canonical source</a></p>

Most local Agents cannot generate images unless you buy and wire an OpenAI API key. If you already run `codex` and logged in with your ChatGPT account, this Skill reuses that exact OAuth login to drive `gpt-image-2`: it refreshes expired tokens, calls the Codex Responses endpoint with the headers the backend requires, parses the SSE stream, and writes a local PNG. It works from Claude Code, Codex, OpenCode, or any Agent that can run `python3`.

## Install

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill codex-image-gen --agent codex --global --copy --yes
```

## Requirements

- Codex CLI installed and logged in once: `codex auth login`
- A readable `~/.codex/auth.json` on the machine that runs the Agent
- Python 3.9 or newer; no third-party packages
- Network access to `chatgpt.com` and `auth.openai.com`

## What It Does

- Text-to-image from a `--prompt` or a `--prompt-file`
- Image editing and image-to-image with `--image` and repeatable `--reference-image` inputs (local paths, HTTP(S) URLs, or data URLs)
- Three controlled aspects — `square` (1024x1024), `landscape` (1536x1024), `portrait` (1024x1536) — and `--quality low|medium|high`
- Checks the access token's JWT expiry and refreshes it with the refresh token when needed, writing new tokens back to `~/.codex/auth.json`
- Extracts the final image from the SSE stream, falling back to the last partial image, and saves it as a PNG
- Emits one line of JSON — `{"success": true, "image": "/absolute/path.png"}` — that any Agent can parse

## How It Works

1. The script reads `~/.codex/auth.json`, decodes the access token's JWT payload, and refreshes the token through `auth.openai.com` when it is near expiry.
2. It posts to the Codex Responses endpoint with the exact headers the backend expects (`User-Agent: codex_cli_rs/0.0.0`, `originator: codex_cli_rs`, `ChatGPT-Account-ID`), which is what prevents gratuitous 403s.
3. The outer model carries an `image_generation` tool bound to `gpt-image-2`; local input images are base64-encoded into `input_image` content.
4. The SSE parser keeps the last `image_generation_call.result`, falls back to the last `partial_image_b64`, and writes the decoded bytes as `codex-image-<timestamp>-<prompt-hash>.png`.

## Example Requests

```text
Generate a blue-and-white minimal course cover illustration, no text, 16:9, into ./outputs
```

```text
This machine has no OpenAI API key, but Codex CLI is logged in. Draw a minimal tech illustration.
```

```text
Turn draft.png into a clean whiteboard-style business illustration, using style-ref.png as the style reference.
```

Equivalent direct call:

```bash
python3 scripts/codex_image.py \
  --prompt "minimal blue-white AI course cover, geometric, no text" \
  --aspect landscape --quality high --out-dir ./outputs
```

## Safety and Limitations

- The Skill reuses your own ChatGPT/Codex login and consumes that account's image quota; it does not create entitlements.
- Refresh tokens are single-use, so the script writes refreshed tokens back to `~/.codex/auth.json` immediately with `0600` permissions.
- `401` means the local login is gone — run `codex auth login` again. `403` is usually missing headers or Cloudflare/account checks, not a bad prompt.
- Image generation runs under your account terms; keep prompts and reference images within what your account is allowed to process.
- The Skill generates one image per run. Batch scheduling, queues, and post-processing are explicitly out of scope.
- If the upstream response format changes, the script fails loudly instead of saving garbage; `references/api-notes.md` documents the wire protocol for repairs.

## Repository Layout

```text
skills/codex-image-gen/
├── SKILL.md
├── agents/openai.yaml
├── evals/evals.json
├── references/api-notes.md
├── scripts/codex_image.py
└── tests/test_codex_image.py
```

## License

[MIT](../../../LICENSE)
