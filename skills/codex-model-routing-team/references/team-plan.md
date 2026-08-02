# 轻量 TeamPlan 编译协议

当主 Agent 准备创建两个及以上 Worker 时读取本协议。TeamPlan 只负责任务编排；模型、推理强度、速度、Provider 和 fallback 继续由每个单元自己的 RoutePlan 决定。

## 收益门

一次有界判断同时满足以下条件才自动派遣：

1. 至少两个 Worker 单元各有独立交付物；
2. 每个单元都有可检查的完成条件，主 Agent 保留集成和最终验收；
3. 预计节省的时间或模型成本高于创建、监督和集成成本。

不满足时简报 `lead_only` 原因并直接执行，不构造 TeamPlan。简单问答、状态查询、单文件小改、强顺序任务和不可逆外部操作仍不自动派遣。

## 最小契约

默认由主 Agent 一次编译 2–3 个 Worker，不创建 Planner、不调用重型计划流程、不写持久文件。通过 stdin 校验：

```json
{
  "schema_version": "1.0",
  "revision": 1,
  "supersedes_revision": null,
  "planning_source": "ad_hoc",
  "source_refs": [],
  "root_goal": "交付完整且经主 Agent 验证的结果",
  "units": [
    {
      "unit_id": "U1",
      "role": "researcher",
      "goal": "完成第一个独立子目标",
      "output": "可检查的结论或路径",
      "depends_on": [],
      "ownership": {"write": [], "forbidden": []},
      "done_when": "证据完整且可复核"
    },
    {
      "unit_id": "U2",
      "role": "verifier",
      "goal": "完成第二个独立子目标",
      "output": "独立验证结论",
      "depends_on": [],
      "ownership": {"write": [], "forbidden": []},
      "done_when": "验证覆盖关键风险"
    }
  ],
  "reserved_slots": 2,
  "integration_owner": "lead",
  "integration_order": ["U1", "U2"],
  "final_verification": "主 Agent 检查真实产物并完成全局验收",
  "revision_reason": "initial"
}
```

每个 Worker 只保留 `unit_id / role / goal / output / depends_on / ownership / done_when` 七个核心字段。Task Packet 再补数据边界、Provider、上下文、权限和验证命令。

运行：

```bash
python3 scripts/validate_team_plan.py /path/to/team-plan.json
printf '%s' "$TEAM_PLAN_JSON" | python3 scripts/validate_team_plan.py -
```

## 来源适配

- `ad_hoc`：目标已经明确，主 Agent 直接编译。
- `ce_plan`：保留 U-ID、依赖、文件、测试与验收引用，不调用 `ce-work`，不重写领域方案。
- `codex_plan`：退出只读 Plan 模式后再编译；会话内计划只作为来源。
- `upstream_skill`：上游拥有 Scale、阶段、路径和业务质量门；本层只增加 Worker、所有权、预算和集成顺序。

非 `ad_hoc` 来源必须写 `source_refs`。引用上游计划，不复制完整正文，也不创建第二套业务账本。

## 调度与所有权

- 依赖图是唯一调度事实源；validator 计算就绪层并按每波最多 3 个切分。
- 同一就绪层出现相同或父子写入路径时拒绝，主 Agent 必须增加依赖、串行化或重分所有权。
- 文件不重叠不等于语义独立；共享 API、schema、migration、lockfile、生成物、服务、数据库、浏览器会话和限流仍由主 Agent 判断。
- `planned workers + reserved_slots <= 8`；Worker 单元最多 6 个，跨 Surface 并发仍最多 6。
- `integration_order` 必须覆盖全部单元并尊重依赖；`integration_owner` 固定为 `lead`。

验证通过后，每个 unit 恰好生成一份 Task Packet 和一份 RoutePlan。派遣简报只展示 Worker 数、精确路由和职责，不向用户倾倒 TeamPlan JSON。

## Revision

路由失败只走 RoutePlan fallback；输出质量失败仍属于原 unit。只有新证据改变依赖、所有权、交付物、范围或验收时才生成新 revision。

- 当前波全部收口后才能修订；
- revision 大于 1 时 `supersedes_revision` 指向直接上一版；
- 语义不变沿用 unit ID，拆分使用新 ID，删除留空且不得复用；
- 已派出的单元不能被静默改写；
- 一次修订仍无法形成明确单元时，由主 Agent 接管或进入任务本来就需要的重型规划。

Run envelope 使用：

```json
{
  "team_plans": [],
  "active_team_plan_revision": 1,
  "workers": []
}
```

Worker 记录用 `team_plan_revision + unit_id` 关联确切计划。微型模式把 envelope 留在上下文并从 stdin 校验；四个以上 Worker、多阶段、长时或需恢复时，写入现有 durable ledger。TeamPlan 不记录 Thread 控制状态。
