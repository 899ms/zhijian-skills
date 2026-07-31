# 路由策略

## 是否创建 Worker

出现下列信号时评估并行；单个信号不强制触发：

- 至少 2 条互不依赖的工作流。
- 输入可按来源、章节、模块或主题拆分。
- 独立验证能降低主 Agent 的自证偏差。
- 任务跨调研、写作、编码、设计、测试或审查多个领域。
- 预计节省的时间或质量增益明显高于协调成本。

典型任务创建 2–3 个 Worker；广泛调研或多模块任务创建 4–6 个。简单问答、状态查询、单文件小改、强顺序流程直接由主 Agent 完成。

## 选择顺序

路由优先级固定为：

1. 数据边界、Provider 条款、工具需求、任务风险和最低推理强度等硬门。
2. [Surface 选择策略](surface-selection-policy.md)：短时、边界清晰、父任务集成优先原生 Subagent；持久、可恢复、worktree 或独立审计优先 App Thread。
3. [模型注册表](model-registry.json) 的 automatic、opt-in 和 manual-only 状态。
4. [恢复策略](recovery-policy.md) 中精确 `surface/model/thinking/speed` 组合的熔断与近期健康证据。
5. 对应任务类型的能力匹配、独立验证需求、延迟和稳定性信号。
6. 下表的稳定顺序作为最终 tie-break。

禁止只因模型更快或订阅额度看似充足而绕过前四项。

## Surface 与模型

精确 ID、允许的推理强度和自动状态以 [模型注册表](model-registry.json) 为策略事实源。live 工具 schema 与本地 catalog 只验证当前 host 的运行接受性，不能自动把未知模型加入策略。

| 路由名 | Surface | `model` | 推理强度 | 速度 | 适用工作 |
| --- | --- | --- | --- | --- | --- |
| Native Scout | `native_subagent` | `gpt-5.6-sol` | `low` | Standard | 快速定位、搜索、事实扫描、边界清晰的小型探查 |
| Native Sol Worker | `native_subagent` | `gpt-5.6-sol` | `medium` | Standard | Luna Fast 不可用时的常规原生 fallback |
| Native Sol Smart Worker | `native_subagent` | `gpt-5.6-sol` | `high` | Standard | Luna Fast 不可用时的复杂原生 fallback |
| Native Luna High Fast | `native_subagent` | `gpt-5.6-luna` | `high` | Fast | live schema 接受 priority 时的机械提取、分类和简单验证 |
| Native Luna X High Fast | `native_subagent` | `gpt-5.6-luna` | `xhigh` | Fast | live schema 接受 priority 时的默认原生研究、实现与审查 |
| Native Luna Max Fast | `native_subagent` | `gpt-5.6-luna` | `max` | Fast | live schema 接受 priority 时的边界清晰高难执行 |
| Luna High App | `app_thread` | `gpt-5.6-luna` | `high` | Standard | 机械提取、格式整理、分类、简单验证的耐久执行 |
| Luna X High App | `app_thread` | `gpt-5.6-luna` | `xhigh` | Standard | 默认耐久 Worker；调研、初稿、常规编码与审查 |
| Luna Max App | `app_thread` | `gpt-5.6-luna` | `max` | Standard | 边界清晰、难度高、时效不敏感的耐久深度执行 |
| Sol Medium | `app_thread` | `gpt-5.6-sol` | `medium` | Standard | 用户明确点名或有证据支持的中等强度耐久执行 |
| Sol High | `app_thread` | `gpt-5.6-sol` | `high` | Standard | 高歧义规划、架构、困难调试、高风险判断、关键审查 |
| Sol X High | `app_thread` | `gpt-5.6-sol` | `xhigh` | Standard | 更深推理的关键审查与方案裁决 |
| Sol Max | `app_thread` | `gpt-5.6-sol` | `max` | Standard | 有明确质量理由的最高强度单任务 |
| Grok Medium/High | 任一已确认 Surface | `xai/grok-4.5` | `medium` / `high` | Standard | 条件自动的技术分析、Agent 执行与异构复核 |
| Terra Opt-in | 任一已确认 Surface | `gpt-5.6-terra` | `low`–`max` | Standard | 用户明确点名且 live runtime 接受时的 opt-in Worker |
| Gemini Low/Medium/High | 任一已确认 Surface | `antigravity/gemini-3.6-flash` | `low` / `medium` / `high` | Standard | blocked manual-review 模板，当前不得创建 |

`gpt-5.6-terra` 默认关闭，只能作为用户明确点名的首项候选，不能静默 fallback。Grok 必须通过 runtime/provider 预检。Gemini Antigravity 当前 `terms_default: blocked`；它出现在表中用于解释显式请求和未来迁移。

Ultra 永久禁止。不得把成本比例、订阅额度或 TPS 写成未经当前环境验证的固定事实。

`thinking` 是 RoutePlan 的跨 Surface 规范字段，比较顺序为 `low < medium < high < xhigh < max`。原生 spawn 时映射到 `reasoning_effort`；App Thread 创建时映射到 `thinking`。候选必须同时满足该 Surface 的支持范围和 `minimum_thinking`。

`speed` 是与模型、推理强度分离的 RoutePlan 字段，取值为 `standard | fast`。Fast 映射为 `service_tier=priority`；Standard 不传该 tier。只有 Luna 允许 `speed=fast`，Sol、Terra 和其他模型必须写 `speed=standard`。`schema_version: "2.1"` 的 RoutePlan 必须显式填写；旧计划省略版本/速度时兼容解释为 Standard。某个 Surface 的 live schema 没有速度参数时，该 Surface 不能证明或强制 Fast，必须把精确组合视为不可用或保持 Standard。

## 任务画像与候选链

每个子任务在派遣前选择一个画像并固化候选链：

| 画像 | 最低 thinking | 主候选 → fallback | 说明 |
| --- | --- | --- | --- |
| `NATIVE_SCOUT` | low | Native Scout → Native Sol Worker | 快速探查；结果回到父任务直接使用 |
| `NATIVE_WORKER` | high | Native Luna X High Fast → Native Sol Smart Worker | 默认原生实现与分析；Fast schema 缺失时走 Sol Standard |
| `NATIVE_SMART_WORKER` | high | Native Luna Max Fast → Sol X High App Thread | 原生高难任务；Fast 不可用或需要耐久恢复时 fallback |
| `DEFAULT_GENERAL` | high | Luna X High App → Sol High App Thread | 通用耐久研究、写作、编码与验证；App 未暴露速度参数时保持 Standard |
| `FAST_MECHANICAL` | high | Native Luna High Fast → Luna High App | 低风险提取、分类和格式整理；Fast 不可用时转耐久 Standard |
| `DEEP_AGENTIC_CODE` | high | Grok High → Sol High App Thread | Grok/provider 通过硬门后用于复杂工程执行 |
| `REVIEW_OPENAI_PRIMARY` | high | Grok High → Sol X High App Thread | OpenAI 主执行后的异构复核 |
| `REVIEW_XAI_PRIMARY` | xhigh | Sol X High App Thread → Luna X High App | xAI 主执行后的 OpenAI 复核 |
| `CRITICAL_ARBITRATION` | xhigh | Sol X High App Thread → Sol Max App Thread | 关键裁决保持 OpenAI 高强度质量下限 |
| `TERRA_EXPLICIT` | low | Terra Opt-in → 对应最低强度的 Sol | 仅显式请求；Terra 不可用时走预声明 Sol 或主 Agent |
| `GEMINI_EXPLICIT_FAST_BREADTH` | medium | Gemini Medium → Luna X High App | 当前 Antigravity 条款 blocked，不能执行 |

fallback 必须满足最低 `thinking`。首项被静态门排除时，通知应说明从下一项开始，不能伪称运行时失败。`Sol Medium` App Thread 只用于用户明确指定或有任务证据的计划；默认耐久画像仍从 high 起步。

新 RoutePlan 顶层写 `"schema_version": "2.1"`。Standard 原生候选结构：

```json
{
  "surface": "native_subagent",
  "model": "gpt-5.6-sol",
  "thinking": "medium",
  "speed": "standard",
  "runtime_evidence": {
    "kind": "live_spawn_schema",
    "surface": "native_subagent",
    "model": "gpt-5.6-sol",
    "thinking": "medium",
    "speed": "standard",
    "service_tier": null,
    "accepted": true,
    "host": "current-host",
    "checked_at": "<ISO-8601>"
  }
}
```

Native Luna Fast 使用同一 `runtime_evidence`，但必须同时包含 `"speed": "fast"` 与 `"service_tier": "priority"`。App Luna Fast 只有在 `create_thread` 的 live schema 明确接受速度参数时才允许，并在候选中附加：

```json
"speed_evidence": {
  "kind": "live_create_schema",
  "surface": "app_thread",
  "model": "gpt-5.6-luna",
  "thinking": "xhigh",
  "speed": "fast",
  "service_tier": "priority",
  "accepted": true,
  "host": "current-host",
  "checked_at": "<ISO-8601>"
}
```

如果 live schema 没有速度字段，则不得创建 App Fast 候选。`surface` 省略时仅为兼容旧计划，解释为 `app_thread`；`speed` 省略时兼容解释为 `standard`。新计划必须显式填写两者。证据 10 分钟过期，并与 host/Surface/model/thinking/speed 精确绑定；它只表示请求被控制面接受，不表示平台已经回显实际运行模型或速度，也不是加密证明。

用户指定具体 fallback 时，先写入 concrete RoutePlan，再运行：

```bash
python3 scripts/validate_route_plan.py /path/to/route-plan.json
```

通过验证的用户链优先于画像默认链；不满足 Provider allowlist、最低 thinking、opt-in 位置、两 Worker 上限或无循环约束时拒绝采用。跨 Surface fallback 只能来自派遣前声明的候选链。

## 数量与失败升级

- 跨 Surface 运行并发上限 6；root `worker_attempt` 上限 8，替换、超时歧义、未实体化和原生 spawn 失败都计数。
- `planned_workers + reserved_slots <= 8`。reserved slots 用于上游后续阶段和失败恢复。
- Deep Research 默认预算为 `2-4 researcher + 1 verifier + 1 reviewer + 2 retry reserve`；verifier → reviewer 的阶段依赖必须保持串行。
- 完整输出质量不足时，原 Worker 最多一次 follow-up；仍失败才进入候选链下一项。
- 同一子任务最多两个 Worker attempt；单候选失败后由主 Agent 接管。
- 主 Agent 可组合不同 Provider 或 Surface 做独立验证，不设置僵硬模型配额。

## 工作区与冲突

- 默认把可写任务按互斥文件或目录分配；同一文件实行单写者规则。
- 需要隔离分支、独立 cwd 或 worktree 的工程任务使用 `app_thread`；主 Agent 负责比较、移植和验证。
- 只要 App Thread 任务包声明工作区输出路径，就必须使用匹配 project local；projectless 只用于纯聊天交付。
- 原生 Worker 使用 fresh context，任务包必须独立提供工作目录、目标和验证命令，不能依赖父 Agent 的隐式对话历史。
- 无法确认项目、起始状态、Provider 数据边界或合并路径时，留在主任务执行。
