# codex-image-gen Changelog

## 1.0.0 — 2026-08-18

- Publish the first independently governed Portfolio release.
- Reuse the local Codex CLI OAuth login (`~/.codex/auth.json`) to generate and edit images from any bash/python-capable Agent, without an OpenAI API key.
- Refresh expired access tokens with the single-use refresh token and write them back with `0600` permissions.
- Call the Codex Responses endpoint with the required `User-Agent`, `originator`, and `ChatGPT-Account-ID` headers, and parse the SSE stream for `image_generation_call.result` with partial-image fallback.
- Support text-to-image, image editing, repeatable reference images, three aspect presets, and three quality levels through one stdlib-only script.
- Add deterministic argument, request-body, SSE-parsing, JWT-expiry, auth-file, and CLI contract tests.
