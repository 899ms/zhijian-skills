---
name: codex-model-routing-team
description: 在 Codex 中为复杂、可并行的知识工作或编程任务路由可指定模型与推理强度的原生 Subagent 或 Codex App 独立 Thread，并以确定性状态恢复和审计 Worker 生命周期；由主 Agent 负责规划、provider 数据边界、分工、集成和验收。用于多来源调研、多章节内容、复杂 Skill/PPT、跨模块开发、独立验证或 2 个以上互不依赖工作流；也用于用户明确要求模型路由、后台 Worker、Agents Team、Grok/Gemini Worker 或持久项目协作。简单问答、状态查询、单文件小改、强顺序任务和发布/付款/删除/账户操作不得自动触发。
---

# Codex 模型路由团队

主 Agent 始终是任务总负责人。本 Skill 是双路径路由器：边界清晰、需要回到父任务集成的并行工作优先使用原生 `native_subagent`；需要持久恢复、独立任务历史、worktree 或严格 Thread 审计时使用 `app_thread`。两种路径都必须显式声明精确 `model` 与推理强度。

## Do not use

简单问答、状态查询、单文件小改、强顺序任务，以及发布、付款、删除、账户或生产操作不得自动派遣。外部或不可逆动作只能由主 Agent 在用户授权范围内执行，Worker 只准备材料。

## 上游 Skill 模式

当 Deep Research、PPT、课程生产或其他上游 Skill 已经定义任务拆分、阶段顺序、文件路径和验收标准时，读取 [上游 Skill 适配协议](references/upstream-skill-adapter.md)。上游 Skill 保持业务流程主权；本 Skill 只负责模型与 Surface 路由、Provider 门、并发额度、生命周期和审计。

禁止重复执行 Scale、改写上游阶段依赖或创建第二套事实源。安全上限仍然生效；预算不足时收敛 Worker 数量并明确报告。

## 执行流程

1. 检查当前指令中是否存在用户对后台任务和模型路由的明确授权。全局 `AGENTS.md` 的长期授权有效；没有授权就留在主任务内完成。
2. 读取 [模型注册表](references/model-registry.json)、[路由策略](references/routing-policy.md)、[Provider 策略](references/provider-policy.md) 和 [Surface 选择策略](references/surface-selection-policy.md)。先固定任务画像、数据边界、Surface、有序候选链和最低 `thinking`，再创建任何 Worker。
3. 独立任务由本 Skill判断并行收益；上游 Skill 模式采用上游 Scale 和任务包，只施加安全上限。预计超过 30 分钟、正式交付物达到 4 个、需要恢复、worktree 或高风险审批时，读取 [耐久模式](references/durable-mode.md) 并优先选择 `app_thread`。
4. 为每个子任务生成 concrete RoutePlan。每个候选显式写 `surface`、`model`、`thinking`；旧计划省略 `surface` 时兼容解释为 `app_thread`。原生候选必须附带 10 分钟内生成、绑定 host/Surface/model/thinking 的 `runtime_evidence`，证明 live spawn schema 接受该精确组合。运行 `scripts/validate_route_plan.py` 后才能派遣。
5. 派遣前显示一条简短通知：Worker 数、Surface、精确模型、推理强度、职责、预声明 fallback，以及为后续阶段和重试预留的累计额度。Gemini Antigravity 路径必须说明 manual-only 状态和账号风险。
6. 读取 [任务包模板](references/task-packet.md)，为每个 Worker 写唯一 `task_id`、权限导向的 `task_intent / mutation_authority` 和独立可执行提示词。提示词必须包含“禁止创建任何后台任务、线程或子 Agent”。
7. `native_subagent` 读取 [原生 Subagent 生命周期](references/native-subagent-lifecycle.md)。V1 使用 `fork_context=false`，V2 使用 `fork_turns="none"`；live spawn 参数必须显式传入 `model` 与 `reasoning_effort`，禁止静默继承父 Agent。调用开始前消耗 root `worker_attempt` 和 subtask attempt，并按 [原生审计 schema](references/native-audit-schema.json) 建立记录。
8. `app_thread` 按 [Thread 生命周期](references/thread-lifecycle.md) 和 [监督协议](references/thread-supervision-protocol.md) 执行。用 `codex_app__list_projects` 定位项目；每次调用 `create_thread` 前消耗 root `worker_attempt`、兼容字段 `creation_attempt` 和 subtask attempt，并按 [Thread 审计 schema](references/audit-schema.json) 建立记录。
9. 跨 Surface 运行并发最多 6 个，单个根任务累计最多 8 次 `worker_attempt`；未实体化、超时歧义、原生 spawn 失败和 fallback 都计数。每波最多新增 3 个 Worker。创建前扣除上游后续阶段和恢复的 reserved slots；同一文件同一时刻只允许一个写入者。
10. 按 [恢复策略](references/recovery-policy.md) 分类失败。完整输出质量不足时，原生 Worker 最多一次 follow-up，App Thread 最多在原 Thread 追问一次；仍失败才沿预声明候选链进入下一项。每个子任务最多两个 Worker attempt，禁止随机选模、循环回退、静默降级 `thinking` 或运行时扩大 Provider。
11. 主 Agent 亲自核对事实、运行验证、处理冲突并整合最终交付。采纳的原生 Worker 必须 `CLOSED`；采纳的 App Thread 必须完成输出核验并通过归档门。失败、争议、待审和 `UNKNOWN` Thread 保留。
12. 用 `scripts/validate_team_ledger.py` 验证混合 Surface ledger。平台只确认请求被接受但未回显实际运行模型时，`observed_runtime_model` 保持 `unknown`；不得把 requested/accepted 冒充 observed。最终汇报 Surface 与模型分布、预检、重试、升级、采纳、关闭/归档和未解决风险。

## 硬性边界

- 自动候选、opt-in/manual-only 候选、精确模型 ID 和 Surface 支持的推理强度以 [模型注册表](references/model-registry.json) 为策略事实源；live 工具 schema 只验证当前 host 是否接受该组合，不能静默扩张策略。
- `gpt-5.6-luna` 与 `gpt-5.6-sol` 是稳定基线。原生 Sol 可按 `low`、`medium`、`high` 分别承担 scout、worker、smart worker；App Thread 的默认画像仍从 high 起步，`medium` 只用于显式或证据充分的 RoutePlan。
- `gpt-5.6-terra` 是 opt-in 候选，默认关闭。只有用户明确点名、它位于候选链首项且 live runtime 通过时才能使用；不可作为静默 fallback。精确组合不可用时沿预声明 fallback 或由主 Agent 接管。
- `xai/grok-4.5` 通过 runtime/provider 预检后可作为条件自动候选。`antigravity/gemini-3.6-flash` 为 manual-only，且当前第三方 Antigravity 路径 `terms_status: blocked`，不得创建。
- 禁止自动回退到 `gpt-5.5`、`gpt-5.4`、`gpt-5.4-mini` 或 `gpt-5.3-codex-spark`。Worker 永不使用 Ultra，永不继续派生任务；fallback 不得低于任务声明的最低推理强度。
- 原生 Subagent 的 live spawn schema 是精确组合可用性的运行时事实源。V1 与 V2 都必须显式传模型、推理强度和 fresh-context 参数；缺字段、未知模型或拒绝参数就是该精确组合失败，不能悄悄继承父 Agent。
- 主 Agent 不切换自己的模型。原生工具不可用或精确组合未确认时，可以沿预声明链切换到 `app_thread`；App 后台工具不可用、项目无法安全定位、Provider 数据边界不允许或文件所有权无法隔离时，由主 Agent 完成。
- `pendingWorktreeId` 和未确认返回值都不是可管理 Thread。只允许按唯一 task id 通过官方 `list_threads/read_thread` 有界恢复；零/多匹配进入 `UNKNOWN`，禁止追问、归档、fallback、重复创建或直接修改 Codex 数据库。
- MCP 初始化错误按 workspace/tool signature 处理，不通过连续换模型掩盖环境故障。上游 Skill 的阶段门优先于并行收益；存在 verifier → reviewer 等依赖时必须串行派遣。

## 输出契约

交付必须完整、自洽、经过主 Agent 验证，并包含可审计的 Surface 与模型路由摘要。原生 Worker 通过关闭门，App Thread 通过监督协议的收尾门；上游 Skill 模式另外报告 reserved slots、阶段门、输出采纳和关闭/归档状态。触发、并发、Provider、恢复和生命周期边界见 [验证案例](references/validation-cases.md)。
