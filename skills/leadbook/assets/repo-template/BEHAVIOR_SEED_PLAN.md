# Behavior Seed Plan

行为层由 Agent 自动生成，不默认让用户提供公司名或关键词。

## 推导来源

| Source File | Extracted Signal | Notes |
|---|---|---|
| BOOK_BRIEF.md | 待填写 | 这本书要解决的问题 |
| READER_PROFILE.md | 待填写 | 读者所属行业、角色、场景 |
| POSITIONING.md | 待填写 | 核心主张和反常识判断 |
| OUTLINE.md | 待填写 | 每章需要验证的行为信号 |
| SOURCE_MAP.md | 待填写 | 现有证据缺口 |

## 默认行为信号

| Signal Type | Search Pattern | Why It Matters | Status |
|---|---|---|---|
| job-posting | 待填写 | 组织正在配置什么能力 | planned |
| event-agenda | 待填写 | 行业正在讨论什么执行主题 | planned |
| case-page | 待填写 | 哪些方法被真实组织采用 | planned |
| tender | 待填写 | 是否存在公开采购和预算 | optional |
| partnership | 待填写 | 哪些能力正在被打包成方案 | optional |

## 使用规则

- 先抓开放网页，不碰登录墙。
- 行为层证明“公开组织动作存在”，不能单独证明方法有效。
- 至少 3 条有效行为信号进入 `BEHAVIOR_LEDGER.md`，才算初步闭环。
- 如果主题确实不需要行为层，必须写明原因，并在最终汇报里说明。
