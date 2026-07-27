# Codex 模型路由团队

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Codex 主任务把受控的后台工作分配给明确模型">
</p>

<p align="center"><strong>主 Agent 负责集成和验收；受控工作路由到精确模型的原生 Subagent 或耐久 App Thread。</strong></p>

<p align="center"><a href="./README.md">English</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/codex-model-routing-team">统一源码</a></p>

适合复杂并行任务：主 Agent 负责规划、文件所有权和集成，Worker 按明确 Surface、模型与推理强度执行。

## 安装

这条常用简写是 `skills` CLI 的正确语法：

```bash
npx skills add zjp1997720/zhijian-skills
```

推荐用下面的命令全局安装到 Codex，并复制真实文件而不是创建软链接：

```bash
npx skills add zjp1997720/zhijian-skills \
  -g -a codex --skill codex-model-routing-team --copy -y
```

完整的组合仓库 GitHub 链接同样有效：

```bash
npx skills add https://github.com/zjp1997720/zhijian-skills \
  -g -a codex --skill codex-model-routing-team --copy -y
```

安装后检查入口文件和配套策略是否齐全：

```bash
npx skills ls -g -a codex
find ~/.agents/skills/codex-model-routing-team -maxdepth 2 -type f | sort
```

文件列表至少应包含 `SKILL.md`、`references/model-registry.json`、`references/audit-schema.json`、`references/native-audit-schema.json`、`references/surface-selection-policy.md`、`references/native-subagent-lifecycle.md`、`references/routing-policy.md`、`references/provider-policy.md`、`references/recovery-policy.md`、`references/task-packet.md`、`references/thread-lifecycle.md`、`references/thread-supervision-protocol.md`、`scripts/route_policy.py`、`scripts/model_preflight.py`、`scripts/validate_route_plan.py` 和 `scripts/validate_team_ledger.py`。如果只有 `SKILL.md`，说明装到的是旧版残缺包，删除后重新安装当前版本。

## 启用方式

安装完成后，可以直接点名使用：

```text
使用 $codex-model-routing-team 并行调研这 6 个互不依赖的主题，最后统一核验并整合结论。
```

如果希望 Codex 自动判断复杂度并主动使用这个 Skill，把下面的长期授权加入 `~/.codex/AGENTS.md`。只想在某个项目中启用时，把它放到该项目的 `AGENTS.md`。

```markdown
## Codex 后台模型路由授权

- 用户长期授权 Codex 在复杂、可并行任务中自动使用 `$codex-model-routing-team`，并按任务生命周期选择精确模型的原生 Subagent 或 Codex App 独立 Thread；派遣前用一条简短通知说明数量、Surface、模型、强度和职责，无需再次确认。
- 主 Agent 保持当前模型，负责规划、文件所有权、集成、验证和最终交付。
- 原生 Subagent 默认处理短时、边界清晰、回到父任务集成的工作；需要持久恢复、worktree、独立历史或严格 Thread 审计时使用 App Thread。
- 跨 Surface 同时运行最多 6 个 Worker；单个根任务累计最多 8 次 Worker attempt，失败、未实体化和 fallback 都计数。Worker 不得继续创建任何后台任务或子 Agent。
- Worker 禁止使用 Ultra；Terra 为 opt-in，默认不参与自动路由。原生精确模型/推理强度必须通过 live spawn schema；不可用时只走预声明 fallback 或由主 Agent 接管。
- 简单问答、状态查询、单文件小改、强顺序任务以及发布、发送、付款、删除、账户或生产操作不自动派遣。
```

这段内容是用户自己配置的 Codex 指令，不是 OpenAI 隐藏的系统提示词。没有长期授权时，仍然可以通过点名 `$codex-model-routing-team` 手动启用。

## 为什么需要它

当前 Codex 原生 Subagent 的 spawn schema 已经可以暴露每个 Worker 的 `model` 与推理强度控制。可用性仍取决于具体 runtime 和 Surface：同一环境可能接受 Sol、拒绝 Terra；“请求或平台接受了某模型”也不等于平台回显了真实运行模型。

这个 Skill 把新能力变成受控双路径路由器：边界清晰、回到父任务集成的工作用原生 Subagent；需要持久恢复、独立任务历史或 worktree 的工作用 Codex App Thread。两条路径共享 Provider 门、fallback 计划、次数预算和主 Agent 验收。

普通 2–3 个 OpenAI 原生 Worker 默认走 `native-light`：只加载当前路径需要的策略，RoutePlan 和 ledger 可通过 stdin 校验并留在上下文，不创建 `agent_team/`。涉及恢复、worktree、独立历史、高风险审批、跨 Provider 或 fallback 时进入完整 `governed` 路径。两档共享同一套安全门。

## 主要能力

- 只路由真正复杂且可并行的任务，例如多来源调研、多章节内容、复杂 Skill 或 PPT、跨模块开发和独立验证。
- 原生 Sol low/medium/high 分别承担 scout、worker、smart worker；Luna 与 Sol App Thread 提供耐久基线；Grok 4.5 在 runtime/provider 预检后承担复杂执行和异构审查。
- `gpt-5.6-terra` 为 opt-in，只能作为用户明确点名的首项候选；unknown model 只判定该精确原生组合失败，禁止静默继承父模型。
- Gemini 3.6 Flash 保留显式路由模板，但当前 Antigravity 第三方登录路径受官方条款阻断；正式 API/Vertex 路径需要新的 registry entry。
- 每波最多新增 3 个 Worker，跨 Surface 同时运行最多 6 个，单个根任务累计最多 8 次 Worker attempt。
- 每个新模型/推理强度/工具签名组合的首个真实业务任务充当健康探针；HTTP 成功、Thread 实体化、模型数据事件和交付质量分别验收。
- 区分正式 `threadId`、排队 `pendingWorktreeId`、超时和歧义状态；用唯一 task id 恢复排队任务，`UNKNOWN` 状态禁止追问、归档、fallback 和重复创建。
- 以最新官方 Thread/turn 读取作为当前状态真相，通过最小 ledger validator 检查 attempt、实体化、DATA_READY 与归档不变量。
- 用 `task_intent` 和 `mutation_authority` 限定 Worker 写入权限；研究和验证任务不能顺手扩大修改范围。
- fallback 在派遣前固定；每个子任务最多两个 Worker attempt，完整输出最多在原 Worker follow-up 一次。
- 单候选 RoutePlan 只占 1 个 Worker 上限；只有声明 fallback 候选时才使用 2。
- 可以作为 Deep Research 等上游 Skill 的双 Surface Orchestrator，保留上游流程、阶段门、产物和质量标准。
- 发布、付款、删除、账户操作和生产变更始终由主 Agent 执行。

## 工作方式

1. 主 Agent 固定任务画像、Provider allowlist、执行 Surface 和有序候选链。
2. 校验 registry 与 Provider 门；每个原生 `model/reasoning_effort` 精确组合还要通过 live spawn schema。
3. 边界清晰的 OpenAI 原生任务使用 `native-light`；耐久、跨 Provider、fallback 或高风险任务使用 `governed`。
4. 原生 V1 使用 `fork_context=false`，V2 使用 `fork_turns="none"`；App Thread 使用唯一 task id 和官方读取恢复排队 worktree。
5. requested、platform accepted 与 observed runtime model 分开记录；平台未回显时 observed 保持 `unknown`。
6. 失败只沿预声明链前进，包括跨 Surface fallback；单候选失败后由主 Agent 接管。
7. 已采纳的原生 Worker 必须关闭；App Thread 必须通过完成与归档门。

轻量路径可以直接从 stdin 校验，不留下临时协调文件：

```bash
printf '%s' "$ROUTE_PLAN_JSON" | python3 scripts/validate_route_plan.py -
printf '%s' "$TEAM_LEDGER_JSON" | python3 scripts/validate_team_ledger.py -
```

`max_worker_threads` 必须等于候选链长度：单候选且失败后由主 Agent 接管时写 `1`；声明 fallback 候选时写 `2`。

上游 Skill 已经完成任务拆分时，本 Skill 接受其阶段顺序和任务预算，只负责模型路由、任务生命周期与安全上限。声明工作区输出路径的任务始终绑定项目；只有纯聊天交付才能使用 projectless。

Deep Research 默认预算为 `2-4 个 researcher + 1 个 verifier + 1 个 reviewer + 2 个重试位`，总数不超过 8 个。

## 使用示例

```text
使用 $codex-model-routing-team 分别实现、测试和审查 3 个独立模块，避免文件所有权重叠。
```

```text
使用 $codex-model-routing-team 准备一套培训 PPT，分别安排调研、写作和审查任务。
```

```text
让 $codex-model-routing-team 作为 $deep-research 的路由 Orchestrator，保留 verifier 和 reviewer 阶段。
```

## 环境要求与边界

- Codex 能提供可确认精确模型/推理组合的原生 Subagent spawn、Codex App Thread 工具或两者。某条声明路径不可用时，只能使用预声明的另一条路径。
- 当前账号可以使用主 Agent 选择的模型与推理强度。
- `gpt-5.6-sol / medium` 只用于用户明确点名或 RoutePlan 明确证明中等推理足够的任务；默认画像仍保持 high 以上。
- 跨 Provider 路由前必须确认数据边界、凭证路径和服务条款；订阅可登录不等于第三方代理被授权。
- Worker 必须能够验证已经真实创建。原生模型接受状态与 observed identity 分开记录；App Thread 仍必须通过实体化门。
- Terra 因 live 可用性与策略声明可能不同而保持 opt-in；Ultra 永久禁止。

## 仓库结构

```text
.
├── README.md
├── README.zh-CN.md
├── LICENSE
├── skills/
│   └── codex-model-routing-team/
│       ├── SKILL.md
│       ├── agents/
│       ├── evals/
│       ├── references/
│       └── scripts/
└── tests/
```

Agent 的完整工作流见 [SKILL.md](../../../skills/codex-model-routing-team/SKILL.md)，配套策略见 [references](../../../skills/codex-model-routing-team/references/)。

## 验证情况

工作流已经覆盖原生 Sol 路由、Terra opt-in 拒绝与 fallback、Luna/Sol App Thread、条件 Grok 4.5 和 Gemini Provider 阻断；包含 Surface 预检、RoutePlan 校验、原生关闭门、pending worktree 恢复、混合 ledger 校验和隔离 `npx skills` 安装。

## 许可证

[MIT](../../../skills/codex-model-routing-team/LICENSE)
