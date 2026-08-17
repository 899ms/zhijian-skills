# Codex OAuth 生图 API 备注

本文档记录 `codex-image-gen` 依赖的最小协议面，方便在 Claude Code、Codex、OpenCode 等 Agent 里排错和二次封装。

## 1. 认证来源

认证文件：

```text
~/.codex/auth.json
```

典型格式：

```json
{
  "auth_mode": "chatgpt",
  "tokens": {
    "id_token": "...",
    "access_token": "...",
    "refresh_token": "...",
    "account_id": "..."
  },
  "last_refresh": "2026-07-03T07:05:56.768466Z"
}
```

脚本需要做 3 件事：

1. 读取 `tokens.access_token`
2. 解 JWT payload，检查 `exp`
3. 过期时用 `tokens.refresh_token` 刷新，并写回原文件

## 2. 刷新 token

刷新端点：

```text
POST https://auth.openai.com/oauth/token
```

最小表单字段：

```text
client_id=app_EMoamEEZ73f0CkXaXp7hrann
grant_type=refresh_token
refresh_token=<auth.json 中的 refresh_token>
```

实现建议：

- 用 `application/x-www-form-urlencoded`
- 刷新成功后保留原有 `auth.json` 字段，只更新 `tokens` 中返回的新值
- `last_refresh` 用 UTC ISO8601，末尾带 `Z`

## 3. Responses API

请求端点：

```text
POST https://chatgpt.com/backend-api/codex/responses
```

### 必备请求头

以下请求头缺一不可，否则常见结果是 403：

```text
User-Agent: codex_cli_rs/0.0.0
originator: codex_cli_rs
ChatGPT-Account-ID: <从 access_token JWT claim 取 chatgpt_account_id>
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: text/event-stream
```

其中 `ChatGPT-Account-ID` 优先从 access token 的 JWT payload 提取；若提取失败，可退回 `auth.json.tokens.account_id` 作为兜底。

## 4. 请求体结构

外层模型固定为：

```json
{"model": "gpt-5.5"}
```

真正负责出图的是 tools 中的 `image_generation`：

```json
{
  "type": "image_generation",
  "model": "gpt-image-2",
  "size": "1024x1024",
  "quality": "medium",
  "output_format": "png",
  "background": "opaque",
  "partial_images": 1
}
```

### 文生图 content

```json
[
  {"type": "input_text", "text": "<prompt>"}
]
```

### image-to-image / 编辑 content

在上面的 `input_text` 后追加：

```json
{
  "type": "input_image",
  "image_url": "data:image/png;base64,..."
}
```

可追加多张输入图 / 参考图。

## 5. 尺寸映射

目前本 skill 只暴露 3 个可控 aspect：

- `square` -> `1024x1024`
- `landscape` -> `1536x1024`
- `portrait` -> `1024x1536`

quality：

- `low`
- `medium`
- `high`

## 6. SSE 响应解析

图片数据可能出现在两类位置：

### A. 最终图片

```json
{"type": "image_generation_call", "result": "<base64>"}
```

### B. 流式中间图

任意嵌套层中的：

```json
{"partial_image_b64": "<base64>"}
```

解析策略建议：

1. 按 SSE 标准逐行读 `data:`
2. 遇到空行就把当前 event 合并并解析 JSON
3. 优先取最后一个 `image_generation_call.result`
4. 如果没有最终图，再回退到最后一个 `partial_image_b64`

## 7. 常见故障

### 401 Unauthorized

通常表示：

- access token 失效
- refresh token 也失效
- 本地登录态已经不可用

处理：让用户重新执行：

```bash
codex auth login
```

### 403 Forbidden

通常表示：

- 缺少 `User-Agent: codex_cli_rs/0.0.0`
- 缺少 `originator: codex_cli_rs`
- 缺少或错误的 `ChatGPT-Account-ID`
- 账号态 / Cloudflare 风控拦截

### 返回成功但没有图片字段

说明上游事件结构变了。应保留原始事件样本，扩展解析逻辑，而不是盲猜字段。

## 8. 这个 skill 的边界

它只解决：

- 已登录 Codex CLI 的本机 OAuth 态复用
- 文生图 / 图像编辑
- 本地 PNG 落地

它不解决：

- 宿主专有的 image_generate 工具封装
- 云端任务队列
- 多图批量调度
- 高级后处理

如果未来要做批量生图，可以在当前脚本外层再包一层 shell / Python 调度器。