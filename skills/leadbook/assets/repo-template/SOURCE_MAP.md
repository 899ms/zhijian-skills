# Source Map

| ID | Layer | Tool | Query / Account | URL | Output Path | Use | Weight | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| S001 | L1-fact | web / official source | 待填写 | 待填写 | research/fact/ | fact / rule / data | high | planned | 官方资料、报告、平台公告、公司公开信息 |
| S002 | L3-behavior | web | BEHAVIOR_SEED_PLAN.md | 待填写 | research/behavior/ | job / agenda / public action | medium-high | planned | Agent 从 brief / reader / outline 自动推导 |
| S003 | L4-transaction | web | 待填写 | 待填写 | research/transaction/ | offer / pricing / promise / objection | medium-high | planned | 产品页、定价页、报名页、交付说明 |
| S004 | L5-discourse | web | 待填写 | 待填写 | research/clippings/ | article / interview / case material | medium | planned | 单篇好文、访谈或报告解读 |

## Layer Rules

- L1-fact：官方资料、研究报告、平台公告、公司公开信息、可信媒体。用于事实、数据、平台规则。
- L2-demand：小红书搜索、笔记正文、评论样本、互动数据。用于用户语言、需求强度、反对意见、内容钩子。
- L3-behavior：招聘 JD、活动议程、公开项目、合作公告。用于判断市场真实动作和组织资源配置。
- L4-transaction：定价页、产品页、报名页、交付说明、FAQ、购买异议。用于判断付费意愿、承诺方式和交易边界。
- L5-discourse：公众号、博客、对标作者、行业文章。用于观点谱系、叙事结构、案例素材。
- L6-owned：Nowledge、Obsidian、Vault 历史材料。只用于自有案例、历史项目、场景补充，不作为高权重事实来源。

## Hard Rules

- `CLAIM_LEDGER.md` 的 high confidence fact 必须能回到 L1-fact，或至少有两个独立公开来源交叉验证。
- 标记 `used / selected / fetched / exported / done` 的公开来源必须提供可直接打开的 `http://` 或 `https://` URL；“公开检索入口”“厂商案例页”等描述不算来源。
- 小红书不能单独支撑市场规模、平台规则、行业事实。
- 行为层只能证明公开组织动作存在，不能单独证明方法有效。
- 交易层只能证明市场上有人这样承诺和销售，不能单独证明交付质量。
- 公众号文章不能单独支撑高置信事实，除非它引用了可追溯来源。
- 公众号调研必须先完成 `AUTHORITY_ACCOUNTS.md`，再抓文章池。
- 商业/运营/平台/AI 类主题，公众号文章默认只抓最近 365 天；更早文章必须标记为 evergreen / historical。
- Nowledge/Obsidian 不能标为 high weight；除非是特别合适的自有案例，否则不进入正文证据链。

## Optional Providers

- 小红书、公众号采集和本地内容都是可选 Provider。只有用户明确需要且运行环境可用时才增加对应行。
- 通用模式默认只用公开 Web，也必须完成事实、行为、交易和观点层证据，不得因缺少本地 Provider 降低 URL 标准。
