# App Server 兼容合同

## 采用的稳定协议

本 Skill 通过 `codex app-server` 的 stdio JSONL 传输工作，每次连接先执行：

1. `initialize`
2. `initialized`
3. 新任务使用 `thread/start`，续问使用 `thread/resume`
4. `thread/name/set`
5. `turn/start`
6. 等待 `turn/completed`

状态和结果由本地运行回执保存；取消通过当前 Worker 向同一 App Server 发送 `turn/interrupt`。持久 Thread 由 Codex 自身保存，不依赖 Worker 长期存活。

官方依据：

- [Codex App Server 文档](https://learn.chatgpt.com/docs/app-server)
- [OpenAI Codex App Server 源码说明](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [OpenAI Claude Code Codex 插件](https://github.com/openai/codex-plugin-cc)

## 本地状态

默认运行回执目录：

```text
${CODEX_EXTERNAL_HANDOFF_HOME}
${CODEX_HOME}/external-handoff
~/.codex/external-handoff
```

按上述优先级选择。任务正文存入 `<job>.request.json`，Worker 读取后立即删除；`<job>.json` 保留运行标识、状态、结果和日志路径。

## 可见性与接管

- Codex App：`codex://threads/<threadId>`
- Codex CLI：`codex resume <threadId>`

`open` 在 macOS 调用 URL Scheme；无法打开图形界面时仍返回 URL 和 CLI 命令。

## 兼容检查

出现以下变化时运行 `doctor`、单元测试和真实烟雾测试：

- Codex CLI 升级；
- `thread/start`、`turn/start` 或通知字段变化；
- 自定义模型目录或 Provider 变化；
- Codex App URL Scheme 变化；
- 外部 Agent Shell 环境不再继承 `PATH`、`CODEX_HOME` 或模型 Provider 所需环境变量。

本 Skill 不依赖实验性 WebSocket 传输、鼠标自动化或 Codex App 内部私有未导出工具。
