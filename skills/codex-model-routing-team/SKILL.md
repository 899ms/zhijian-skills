---
name: codex-model-routing-team
description: 为有明确净并行收益的任务编译 TeamPlan，默认用 Codex 原生 Multi-Agent V2 创建 Luna XHigh/Max leaf Worker，并在需要独立 worktree、侧栏可见、跨任务恢复或耐久监督时切到 App Thread。用于两个以上独立交付物、独立验证，或用户明确要求模型路由、后台 Worker、Agents Team、Grok/Gemini Worker。简单问答、状态查询、单文件小改、强顺序任务和不可逆操作不自动触发。
---

# Codex 模型路由团队

主 Agent 保持当前模型，负责任务拆分、所有权、集成和最终验收。两个以上 Worker 先编译 TeamPlan；默认路由为 `native_subagent/gpt-5.6-luna/xhigh/standard`，高风险升 `max`。App Thread 是有状态工作区与耐久任务的专用 Surface，不再是 Luna 的兼容入口。

## 不使用

简单问答、状态查询、单文件小改、强顺序任务和不可逆外部操作留在主任务；Worker 只能准备外部动作材料。

## 执行模式

- `native-v2`（默认）：用原生 V2 创建 Luna leaf Worker；fresh context 使用 `fork_turns="none"`，需要少量最近上下文时写正整数。三类 JSON 默认从 stdin 校验。
- `durable-app`：任务需要独立 worktree、侧栏可见、跨任务恢复、长期监督，或原生路径缺少精确 live 能力时，使用 App Thread 与耐久账本。
- 上游 Skill 已定义拆分、阶段和产物时，遵守 [适配协议](references/upstream-skill-adapter.md)，不重做 Scale、阶段门或第二套业务账本。

## 执行流程

1. 确认显式或长期授权；只有两个以上独立交付物且净收益为正时派遣，否则 `lead_only`。
2. 两个以上 Worker 按 [TeamPlan 协议](references/team-plan.md) 编译 unit、依赖、所有权、交付物、验收和集成顺序，并运行 `scripts/validate_team_plan.py`；已有上游计划时只编译、不重写。
3. 按 [registry](references/model-registry.json)、[Provider](references/provider-policy.md)、[路由](references/routing-policy.md) 与 [Surface](references/surface-selection-policy.md) 策略固定候选链。
4. 每个 unit 生成 `schema_version: "3.0"` RoutePlan，写 `surface_intent: parent_integrated|durable_app` 并运行 `scripts/validate_route_plan.py`。原生候选必须显式写 `fork_turns` 和 tuple-bound `runtime_evidence`；Fast 还必须有当前 live `service_tier=priority` 证据。
5. [任务包](references/task-packet.md) 写 unit、唯一 `task_id`、权限、验收和禁止下级派遣；简报精确路由、职责、fallback 与 reserved slots。
6. 原生路径遵守 [生命周期](references/native-subagent-lifecycle.md)；App 路径遵守 [Thread 生命周期](references/thread-lifecycle.md) 与 [监督协议](references/thread-supervision-protocol.md)。
7. TeamPlan 默认 `standard` 6/8/3；`expanded` 12/16/6 需 live 容量门、2 个 reserved slots 和 10 分钟内的结构化证据。child slots 等于总槽位减协调者与活动 Worker，按较小值切波。
8. 每 unit 最多 2 次 attempt、一次 follow-up；失败只沿 [预声明链](references/recovery-policy.md)。结构变化才在收口后修订 TeamPlan。
9. 主 Agent 验证集成；原生 Worker 按 live 能力 close 或 completed-idle 后写 `RELEASED`，App Thread 过门后归档。运行 `scripts/validate_team_ledger.py`。

## 硬门

- registry 决定策略范围；live schema 只证明当前 host 接受精确组合。requested/accepted/observed 分开记录，未回显为 `unknown`。
- V2 父 Agent 可创建 picker 可见且未禁用的 V1 leaf model；Luna 可走原生 V2但不获协作工具。Sol/Terra 也禁止下级派遣。
- 不加 `model: luna` frontmatter；编排入口留在协作父 Agent，Luna 只做 Worker。
- Luna 最低 XHigh，高风险 Max；Sol 最低 High；Terra 仅显式首项；Grok 过门；Gemini blocked。禁止旧模型、Ultra 和低强度 fallback。
- Fast 即 `service_tier=priority`；live schema 无字段时一律 Standard，不把 catalog 或请求值冒充 observed Fast。
- `app_thread` 只用于 worktree、侧栏、跨任务恢复、耐久监督或预声明 fallback。
- Worker 不得继续派生任务，也不得执行发布、发送、付款、删除、账户或生产变更。主 Agent 不切换自身模型。
- TeamPlan 默认不创建 Planner、不调用重型计划、不落持久文件；同波写冲突、依赖环、超预算、计划外 Worker 或下放最终验收必须拒绝。
- 未确认返回值或 `pendingWorktreeId` 不得当正式身份；`UNKNOWN` 禁止追问、归档、fallback、重复创建或改数据库。

## 输出契约

交付必须完整、自洽并经主 Agent 验证，包含可审计的 Surface、模型、推理强度、速度、上下文范围、Provider 门、尝试、fallback、采纳及收尾状态。行为边界见 [验证案例](references/validation-cases.md) 与 [`evals/`](evals/)。
