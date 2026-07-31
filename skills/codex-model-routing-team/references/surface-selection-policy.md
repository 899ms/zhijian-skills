# 执行 Surface 选择策略

本 Skill 在模型候选之前先选择执行 Surface。`native_subagent` 与 `app_thread` 都是真实模型路由；它们解决不同的生命周期问题。

## 确定性选择顺序

1. 简单问答、状态查询、单文件小改、强顺序任务和不可逆操作留在主 Agent。
2. 边界清晰、由父任务汇总、无需恢复或独立工作区的并行任务优先 `native_subagent`。
3. 用户明确要求后台/独立 Thread，或任务需要恢复、单独打开、project/worktree 隔离、独立历史或严格审计时使用 `app_thread`。预计超过 30 分钟或正式交付物达到 4 个只作为耐久信号，需同时存在持久化、恢复或独立审计需求才升级。
4. Surface 缺少精确 live 能力、Provider 门不通过或所有权无法隔离时，进入预声明的下一候选；没有下一候选时由主 Agent 接管。

旧 RoutePlan 候选没有 `surface/speed` 时按 `app_thread/standard` 解释。`schema_version: "2.1"` 的候选规范形状为：

```json
{"surface": "native_subagent", "model": "gpt-5.6-sol", "thinking": "medium", "speed": "standard", "runtime_evidence": {"kind": "live_spawn_schema", "surface": "native_subagent", "model": "gpt-5.6-sol", "thinking": "medium", "speed": "standard", "service_tier": null, "accepted": true, "host": "current-host", "checked_at": "<ISO-8601>"}}
```

`thinking` 是策略字段：原生工具映射为 `reasoning_effort`，App Thread 映射为 `thinking`。`speed=fast` 映射为 `service_tier=priority`，只有 Luna 可以使用，且必须有 live Surface 证据。跨 Surface fallback 必须在 `candidates` 中预声明；`surface + model + thinking + speed` 才是唯一组合。

## 额度

- 一个子任务最多两个候选，`max_worker_threads` 等于候选数。
- 任何已开始的 `spawn_agent` 或 `create_thread` 都消耗一次 root Worker attempt；静态门排除不消耗。
- 跨 Surface 总并发最多 6，root Worker attempts 最多 8。
- 原生 V2 没有 live 上限证据时按“协调者 + 3 个 child”执行；任何更窄 host 上限优先。
- Worker 永不使用 Ultra，永不继续派生 Agent、Thread 或后台任务。

## 模型身份

feature flag、模型 catalog 和文档只提供候选证据。原生候选的 `runtime_evidence` 必须来自当前会话 live spawn schema，与 host/Surface/model/thinking/speed 绑定并在 10 分钟后失效；App Fast 使用同样期限的 `speed_evidence`。它们是协调器审计证据，不是防篡改凭证。成功调用分别写 `platform_accepted_model/platform_accepted_speed`，平台未回显真实身份或速度时对应 observed 字段保持 `unknown`。
