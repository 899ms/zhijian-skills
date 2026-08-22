# Codex CLI Model Bridge

在 Codex 里接入已验证的 Grok、DeepSeek 等本机模型，同时保住 ChatGPT 的默认 Provider 和历史。

<p align="center"><a href="./README.md">English</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-cli-model-bridge">唯一源码</a></p>

当你希望 Codex 显示 CLI 订阅模型、又不想让厂商助手改掉 `model_provider`、把 GPT 历史藏起来时，使用这个 Skill。

## 安装到 Agent

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill codex-cli-model-bridge --agent codex --global --copy --yes
```

完整载荷同时支持 Claude Code 和通用 Agents-compatible Harness。

## 运行要求

- 已安装 Codex CLI；桥接脚本需要 Python 3.11 或更高版本
- 本机 loopback 上的 CLIProxyAPI（或已有 Codex Router），并且已经暴露目标模型
- 若 Desktop 历史应留在 `openai`，需保持 ChatGPT 登录

Windows 默认走隔离 profile `cli-proxy`。Homebrew、LaunchAgent 和 Codex Router 都不是硬性要求。

## 它会做什么

- 审计 Codex 配置、Provider 历史、loopback 健康和目录归属，不打印密钥。
- 改模型前先恢复占多数历史的 Provider。
- 写入隔离的 `codex --profile cli-proxy` 目录，接入 Grok、DeepSeek 等 Responses 兼容路由。
- 可选地把 Desktop 指到本机改写请求头的代理，并保持 `model_provider = "openai"`。
- 按策略隐藏过期的原生选择器 ID，不删除对应路由。
- 用一次性 `codex exec` 探测模型，包括 Shell 和 Multi-Agent 检查。

## 它怎么工作

Codex 每个任务只选一个 Provider。这个 Skill 不会把模型目录当成按模型分流。

1. `audit` 报告占多数的历史 Provider 和实时代理。
2. `configure` 写入 `~/.codex/cli-proxy.config.toml` 和本机凭证助手。
3. `sync` 把已验证清单叠到 Codex 原生模型元数据上。
4. `probe` 通过 Codex 本身证明模型可用，不只看 `/v1/models`。

macOS 上 `configure-desktop` 可以安装监听 `127.0.0.1:8318` 的 LaunchAgent。Windows 继续用 `codex --profile cli-proxy`，或者启动 `node scripts/transparent_proxy.mjs` 并保持该进程运行。

路径通过 `$CODEX_HOME` / `%USERPROFILE%\.codex` 解析。CLIProxyAPI 从 PATH、`CLIPROXYAPI_CONFIG` 和常见安装位置发现。

## 示例请求

```text
使用 $codex-cli-model-bridge 把 Grok 4.6 和 DeepSeek V4 Pro 加到 Codex，保留我的 ChatGPT 历史，并探测这两个模型。
```

```text
在这台 Windows 电脑上使用 $codex-cli-model-bridge。隔离 profile 就够了，不要安装 LaunchAgent。
```

安装后也可直接运行：

```bash
python3 scripts/bridge.py audit
python3 scripts/bridge.py configure --apply
python3 scripts/bridge.py sync --apply
python3 scripts/bridge.py probe --models grok-4.6,deepseek-v4-pro
```

Windows 上如果没有 `python3`，改用 `py -3` 或 `python`。

## 安全边界与限制

- CLIProxyAPI 必须停在 loopback，远程管理保持关闭。
- 不要运行 `npx @z_ai/coding-helper`。它会覆盖 `model_provider`，把 GPT 历史藏起来。
- 仅 Chat Completions 的路由（包括普通 GLM `/api/paas/v4`）不能当作 Codex 兼容。GLM Coding Plan 需要已验证的 Responses 路径或 Codex Router；见 Skill 内 `references/glm-coding-plan.md`。
- Fast 是服务档，不是第二个目录别名。
- Skill 不会把 API Key 写入 Codex 配置，也不会打印凭证助手输出。
- Windows 文件权限不是 Unix `0600`。把 Codex 和助手文件留在当前用户目录。

## 许可证

[MIT](https://github.com/zjp1997720/zhijian-skills/blob/main/skills/codex-cli-model-bridge/LICENSE)
