# Codex CLI Model Bridge

Keep ChatGPT as Codex's default Provider while adding verified Grok, DeepSeek, and other loopback models.

<p align="center"><a href="./README.zh-CN.md">简体中文</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-cli-model-bridge">Canonical source</a></p>

Use this Skill when Codex should show subscription-backed CLI models without hiding existing GPT history, and when a vendor helper would otherwise rewrite `model_provider`.

## Install

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill codex-cli-model-bridge --agent codex --global --copy --yes
```

The install payload also supports Claude Code and generic Agents-compatible Harnesses.

## Requirements

- Codex CLI, with Python 3.11 or newer for the bridge script
- a loopback CLIProxyAPI (or an existing Codex Router) that already exposes the models
- ChatGPT login preserved when Desktop history should stay on `openai`

Windows works through the isolated `cli-proxy` profile. Homebrew, LaunchAgents, and Codex Router are optional.

## What It Does

- Audits Codex config, Provider history, loopback health, and catalog ownership without printing secrets.
- Restores the dominant history Provider before changing models.
- Writes an isolated `codex --profile cli-proxy` catalog for Grok, DeepSeek, and other Responses-compatible routes.
- Optionally points Desktop at a local header-rewriting proxy while keeping `model_provider = "openai"`.
- Hides stale native picker IDs without deleting their routes.
- Probes models with ephemeral `codex exec`, including shell and multi-agent checks.

## How It Works

Codex picks one Provider per task. This Skill never treats the model catalog as per-model routing.

1. `audit` reports the dominant history Provider and the live proxy.
2. `configure` writes `~/.codex/cli-proxy.config.toml` and a local credential helper.
3. `sync` overlays verified manifests onto Codex's native model metadata.
4. `probe` proves each requested model through Codex, not only `/v1/models`.

On macOS, `configure-desktop` can install a LaunchAgent on `127.0.0.1:8318`. On Windows, keep using `codex --profile cli-proxy`, or start `node scripts/transparent_proxy.mjs` and leave that process running.

Paths resolve through `$CODEX_HOME` / `%USERPROFILE%\.codex`. CLIProxyAPI is discovered from PATH, `CLIPROXYAPI_CONFIG`, and common install locations.

## Example Requests

```text
Use $codex-cli-model-bridge to add Grok 4.6 and DeepSeek V4 Pro to Codex, keep my ChatGPT history, and probe both models.
```

```text
Use $codex-cli-model-bridge on this Windows machine. Isolated profile is enough; do not install a LaunchAgent.
```

Direct commands after install:

```bash
python3 scripts/bridge.py audit
python3 scripts/bridge.py configure --apply
python3 scripts/bridge.py sync --apply
python3 scripts/bridge.py probe --models grok-4.6,deepseek-v4-pro
```

On Windows, if `python3` is missing, use `py -3` or `python`.

## Safety or Limitations

- CLIProxyAPI must stay on loopback. Remote management stays disabled.
- Do not run `npx @z_ai/coding-helper`. That overwrites `model_provider` and hides GPT history.
- Chat Completions-only routes, including ordinary GLM `/api/paas/v4`, are not Codex-compatible. GLM Coding Plan needs a Responses-proven path or Codex Router; see the Skill's `references/glm-coding-plan.md`.
- Fast is a service tier, not a second catalog alias.
- The Skill does not copy API keys into Codex config and does not print credential-helper output.
- Windows file modes are not Unix `0600`. Keep Codex and helper files inside the current user profile.

## License

[MIT](https://github.com/zjp1997720/zhijian-skills/blob/main/skills/codex-cli-model-bridge/LICENSE)
