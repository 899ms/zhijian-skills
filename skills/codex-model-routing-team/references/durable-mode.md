# 耐久 App Thread 模式

## 进入条件

自动路由本身已经默认使用 `app_thread`。本文件决定何时把轻量 App Thread 执行升级为持久状态模式：涉及外部/生产/账户/成本审批；需要跨任务恢复、worktree、独立任务历史或严格 Thread 审计；用户明确要求项目管理或持续执行。

预计超过 30 分钟、四个以上 Worker 或有 4 个以上正式交付物只是耐久信号，不单独触发持久状态目录。短时、2–3 个 Worker、文件所有权互斥、回到父任务集成的工作仍使用微型 [TeamPlan](team-plan.md) 和 Luna App Thread，TeamPlan/RoutePlan/ledger 可从 stdin 校验，不创建 `agent_team/`。原生 Subagent 只用于显式请求或预声明 fallback。

## 状态目录

先检查上游 Skill 是否已经提供可恢复的 plan、task ledger 或 run summary。存在上游账本时直接复用，并在其中增加 Thread id、model、thinking、speed、尝试次数、采纳和归档字段；禁止再创建第二套状态事实源。

只有没有上游状态系统且命中上述持久状态条件时，才在项目根目录创建：

```text
agent_team/
  state.json
  task-board.md
  packets/
  handoffs/
```

`state.json` 至少记录：根任务目标、模式、策略版本、`team_plans`、`active_team_plan_revision`、并发/worker attempt 计数、每个 RoutePlan 的有序候选链、Provider allowlist、健康证据，以及遵守 [Thread 审计 schema](audit-schema.json) 的 Worker 记录。每个 Worker 使用唯一 `task_id` 并记录 `unit_id/team_plan_revision`；正式 id、pending id、`control_state` 和最新官方观察分开记录。未返回正式 thread id 的创建尝试也必须保留。

`task-board.md` 展示待办、执行中、待集成、完成、阻塞。`packets/` 保存正式任务包，`handoffs/` 保存可恢复的交接摘要。

## 风险门

Worker 可以准备外部或高风险动作所需的材料。发布、发送、付款、删除、账户、生产变更和不可逆操作必须回到主 Agent，并遵守当前用户授权。恢复任务时先读取 `state.json` 与交接文件，重新验证过期的 Provider/健康证据，禁止重复创建已完成任务。

## 恢复门

恢复时遵守 [Thread 监督协议](thread-supervision-protocol.md)：先读取现有账本；再按 task id 解析 `CREATION_PENDING/UNKNOWN`；随后读取每个正式 Thread；最后才决定 fallback 或新建。active/inProgress、排队未决和歧义记录都不能被“重新跑一个”覆盖。

运行前后可执行：

```bash
python3 scripts/validate_team_ledger.py /path/to/state.json
```

validator 只检查确定性状态不变量，不把本地 ledger 伪装成实时 Thread 真相。

TeamPlan revision 只能在当前波全部收口后新增。路由失败沿原 RoutePlan fallback，输出质量不足沿原 unit follow-up；只有依赖、所有权、交付物、范围或验收发生结构变化时才修订 TeamPlan。

## rollback boundary

回滚范围只包括本 Skill 新建的后台任务、`agent_team/` 协调文件和未集成的 Worker 变更。不得删除用户既有工作；撤销文件变更必须按项目版本控制与所有权逐项执行。
