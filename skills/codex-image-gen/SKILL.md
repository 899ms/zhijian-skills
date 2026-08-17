---
name: codex-image-gen
description: 给任何已登录 Codex CLI 的 Agent 提供本地生图能力，零私有依赖。只要用户提到生图、画图、生成图片、image
  generation、文生图、配图、插图、封面、海报、根据 prompt 出图，或要把本机 `~/.codex/auth.json` 里的 Codex
  OAuth 登录态复用成可执行脚本，都应优先使用本 skill。适用于 Claude Code、Codex、OpenCode 等任何能运行 bash /
  python3 脚本的 Agent。
disable-model-invocation: false
---

# Codex Image Gen

目标：把“本机已登录的 Codex OAuth 生图能力”封装成一个**零私有依赖**的跨 Agent Skill。

它不依赖任何私有模块；任何能执行 `python3` 的 Agent，只要宿主机已经装好 Codex CLI 并执行过 `codex auth login`，就能直接调用 `scripts/codex_image.py` 生图或做图像编辑。

## 前置条件

必须同时满足：

1. 本机已安装 Codex CLI
2. 已执行过 `codex auth login`
3. `~/.codex/auth.json` 存在且可读
4. 机器可访问：
   - `https://chatgpt.com/backend-api/codex/responses`
   - `https://auth.openai.com/oauth/token`

如果 `~/.codex/auth.json` 不存在，不要猜测或绕过。直接提示用户先运行：

```bash
codex auth login
```

## 这个 skill 能做什么

- 文生图
- 配图 / 插图 / 封面图生成
- image-to-image / 编辑
- 把本地参考图编码成 `data:image/...;base64,...` 后发给 Codex Responses API
- 自动检查 access token 是否过期
- access token 过期时自动用 refresh token 刷新，并写回 `~/.codex/auth.json`
- 从 SSE 流里提取图片 base64，保存为本地 PNG

## 核心脚本

相对路径：`scripts/codex_image.py`

典型调用方式：

```bash
python3 scripts/codex_image.py --prompt "极简科技感课程封面，无文字" --aspect landscape
```

如果 Agent 不是在 skill 根目录执行，就显式传 skill 相对路径或绝对路径，例如：

```bash
python3 .claude/skills/codex-image-gen/scripts/codex_image.py \
  --prompt "商业文章封面插图，克制，干净，无文字" \
  --aspect landscape \
  --quality high \
  --out-dir ./outputs
```

## CLI 参数

### 必填

二选一：

- `--prompt "..."`
- `--prompt-file /path/to/prompt.txt`

### 可选

- `--quality low|medium|high`：默认 `medium`
- `--aspect landscape|square|portrait`：默认 `square`
- `--out-dir /path/to/output-dir`：默认当前目录
- `--image /path/to/image.png`：主编辑图 / 输入图
- `--reference-image /path/to/ref.png`：参考图，可重复传入
- `--model gpt-image-2`：默认 `gpt-image-2`

## 推荐工作方式

### 1) 最短路径：文生图

```bash
python3 scripts/codex_image.py \
  --prompt "蓝白配色的 AI 课程封面插图，几何感，极简，无文字" \
  --aspect landscape \
  --quality high \
  --out-dir ./outputs
```

### 2) 用 prompt 文件

```bash
python3 scripts/codex_image.py \
  --prompt-file ./prompt.txt \
  --aspect portrait \
  --out-dir ./outputs
```

### 3) image-to-image / 编辑

```bash
python3 scripts/codex_image.py \
  --prompt "把这张草图做成干净的白板商业插图风格" \
  --image ./draft.png \
  --reference-image ./style-ref.png \
  --aspect landscape \
  --out-dir ./outputs
```

## Agent 执行规则

1. 先确认 `~/.codex/auth.json` 存在；不存在就停止并提示 `codex auth login`
2. 优先直接跑 `python3 scripts/codex_image.py --help` 自检 CLI
3. 真正执行时，给出明确 prompt，不要只传关键词
4. 如果用户要封面/配图，默认优先：
   - `--aspect landscape`
   - `--quality high`
5. 如果用户要头像、图标、方图，默认优先：
   - `--aspect square`
6. 如果返回 401，直接提示重新登录 Codex
7. 如果返回 403，优先怀疑 Cloudflare / 请求头不完整 / 登录态异常，不要误判成 prompt 问题

## 成功输出约定

脚本成功时会输出 JSON：

```json
{"success": true, "image": "/absolute/path/to/file.png"}
```

Agent 应返回：

- 最终图片路径
- 使用的 prompt（必要时可简述）
- 是否用了输入图 / 参考图

## 失败处理

### auth.json 不存在

明确提示：

```bash
codex auth login
```

### 401 Unauthorized

说明本地登录态失效，建议重新登录：

```bash
codex auth login
```

### 403 Forbidden

说明大概率是 Cloudflare / 关键请求头 / 账号态问题。先检查：

- `User-Agent: codex_cli_rs/0.0.0`
- `originator: codex_cli_rs`
- `ChatGPT-Account-ID`

### 没拿到图片数据

说明上游 SSE 响应格式变了，或只返回了中间事件但没有可用图片字段。此时应检查 `references/api-notes.md` 并根据新响应结构更新脚本。

## 参考文档

- API 细节：`references/api-notes.md`
- 核心脚本：`scripts/codex_image.py`
