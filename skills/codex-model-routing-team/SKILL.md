---
name: codex-model-routing-team
description: 为复杂、可并行任务默认创建 Luna XHigh/Max Codex App Thread，并在 live schema 支持时使用原生 fallback，由主 Agent 负责数据边界、分工、集成和验收。用于多个独立工作流、来源/章节/模块、独立验证，或用户明确要求模型路由、后台 Worker、Agents Team、Grok/Gemini Worker。简单问答、状态查询、单文件小改、强顺序任务和不可逆操作不自动触发。
---

# Codex 模型路由团队

主 Agent 保持当前模型并负责规划、文件所有权、集成和验收。默认路由为 `app_thread/gpt-5.6-luna/xhigh`，高难/高风险升 `max`；`native_subagent` 只用于显式请求或预声明 fallback。

## 不使用

简单问答、状态查询、单文件小改、强顺序任务和不可逆操作留在主任务；Worker 只能准备外部动作材料。

## 执行模式

- `governed`（默认）：2–3 个 Luna App Thread，XHigh 起步；短任务从 stdin 校验，需要恢复/worktree/审计时按 [耐久模式](references/durable-mode.md) 留状态。
- `native-light`（显式/回退）：App 不可用时须预声明；Luna 不可走原生，Sol 最低 High。
- 上游 Skill 已定义拆分、阶段和产物时，遵守 [适配协议](references/upstream-skill-adapter.md)，不重做 Scale、阶段门或第二套账本。

## 执行流程

1. 确认用户显式或 `AGENTS.md` 长期授权，并验证并行收益；不满足则主 Agent 直接完成。
2. 读取 [模型注册表](references/model-registry.json)、[Provider 策略](references/provider-policy.md) 和 [路由策略](references/routing-policy.md)，固定数据边界与精确 `surface/model/thinking/speed`；Surface 有歧义时读取 [选择策略](references/surface-selection-policy.md)。
3. 为每个子任务生成 `schema_version: "2.1"` RoutePlan 并运行 `scripts/validate_route_plan.py`。原生组合必须有 live `runtime_evidence`；App Fast 必须有 live `speed_evidence`。
4. 按 [任务包](references/task-packet.md) 写唯一 `task_id`、权限、验收和“禁止创建后台任务/线程/子 Agent”；派遣前简报 Worker 数、精确路由、职责、fallback 与 reserved slots。
5. 原生路径遵守 [生命周期](references/native-subagent-lifecycle.md) 与 [审计 schema](references/native-audit-schema.json)；App 路径遵守 [Thread 生命周期](references/thread-lifecycle.md)、[监督协议](references/thread-supervision-protocol.md) 与 [审计 schema](references/audit-schema.json)。
6. 跨 Surface 并发最多 6、根任务累计 `worker_attempt` 最多 8、每波新增最多 3；每子任务最多 2 次 Worker attempt、原 Worker 最多一次 follow-up；预留后续阶段/恢复额度并保持单写者。
7. 失败只按 [恢复策略](references/recovery-policy.md) 沿预声明链前进；不得随机选模、循环回退、改变 `thinking/speed`、扩大 Provider，或用换模型掩盖 MCP 故障。
8. 主 Agent 验证并集成交付，关闭已采纳原生 Worker，仅归档满足收尾门的 App Thread；运行 `scripts/validate_team_ledger.py` 后汇报路由、尝试、fallback、采纳、关闭/归档与风险。

## 硬门

- registry 决定策略允许范围；live schema 只证明当前 host 接受精确组合。请求、平台接受与 observed 模型/速度必须分开记录，未回显保持 `unknown`。
- 官方原生 V2 live schema 未开放 Luna；Luna 仅走 App Thread，XHigh 起步，高难/高风险 Max。Sol 无论 Surface 均最低 High；Medium/Low 静态拒绝。
- Fast 是 `service_tier=priority`，不是模型 ID；只有 Luna 可用，Sol、Terra 和其他模型一律 Standard。App Surface 未显式接受速度参数时 Luna 保持 Standard，不得声称 Fast。
- Terra 仅在用户点名时作为首项；Grok 须通过 runtime/provider 门；Gemini Antigravity 当前 blocked。禁止自动使用旧模型、Ultra 或低于最低 `thinking` 的 fallback。
- Worker 不得继续派生任务，也不得执行发布、发送、付款、删除、账户或生产变更。主 Agent 不切换自身模型。
- `pendingWorktreeId`/未知返回值不可管理；零或多匹配进入 `UNKNOWN`，禁止追问、归档、fallback、重复创建或修改 Codex 数据库。上游阶段门始终优先。

## 输出契约

交付必须完整、自洽并经主 Agent 验证，包含可审计的 Surface、模型、推理强度、速度、Provider 门、尝试、fallback、采纳及收尾状态。行为边界见 [验证案例](references/validation-cases.md) 与 [`evals/`](evals/)。
