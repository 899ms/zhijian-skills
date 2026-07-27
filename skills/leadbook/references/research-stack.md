# Leadbook Research Stack

## 最小最强工具集

调研阶段默认保留最小工具集，但证据模型按六层组织：

1. 通用 Web 搜索：默认 Provider，找事实层、行为层、交易层和观点层的公开入口。
2. 通用网页读取或剪藏：把单篇网页、报告、产品页、案例页、活动页、招聘页落成本地 Markdown。
3. `wechat-article-search` + `wxmp-article-harvester`：可选；先发现并确认领域权威公众号，再批量归档最近 365 天文章。
4. `xhs-research.py`：可选；通过本地 `xiaohongshu-mcp` REST API 抓需求材料。
5. `Nowledge/Obsidian`：可选；只作低权重内部上下文、历史案例和用户自有材料入口。
6. `leadbook`：把证据加工成 `SOURCE_MAP.md`、`CLAIM_LEDGER.md`、`CASE_LIBRARY.md`、`BEHAVIOR_LEDGER.md`、`TRANSACTION_LEDGER.md`、章节 refs 和最终书稿。

## 六层证据模型

| Layer | 默认工具 | 主要用途 | 可支持内容 | 默认权重 |
|---|---|---|---|---|
| L1-fact | 通用 Web 搜索 / 官方网页 / 报告 | 事实、数据、规则、行业判断 | `CLAIM_LEDGER.md` 中的 fact 和高置信判断 | high |
| L2-demand | `xhs-research.py` / 公开评论 / 问答页 | 用户痛点、语言、反对意见、内容钩子、需求强度 | 读者问题、场景素材、选题判断 | medium |
| L3-behavior | 通用 Web 搜索 / 招聘页 / 活动页 / 项目页 / 合作公告 | 市场真实动作、组织资源配置、能力需求 | 行为信号、趋势判断、案例候选 | medium-high |
| L4-transaction | 通用 Web 搜索 / 网页剪藏 / 产品页 / 定价页 / 报名页 | 付费意愿、承诺方式、交付边界、购买异议 | 商业判断、引流品定位、工作表设计 | medium-high |
| L5-discourse | `wechat-article-search` / `wxmp-article-harvester` / 网页剪藏 / 博客 / 访谈 / 播客 | 对标作者、方法论、观点谱系、案例叙事 | 框架参考、反方观点、案例素材 | medium |
| L6-owned | Nowledge / Obsidian / Vault | 大鹏历史项目、自有经验、已沉淀案例 | 自有案例、场景、措辞偏好 | low |

旧模板里的 `A-authority / B-demand / C-discourse / D-local-context` 可以兼容读取；新项目默认使用 `L1-fact` 到 `L6-owned`。

## 权重规则

- 市场规模、政策规则、平台规则、公司信息、当前数据默认必须来自 `L1-fact`。
- 小红书是需求侧证据，不是事实裁判。它适合回答“用户怎么说”“什么内容有反应”“评论里反对什么”。
- 行为层回答“市场真实在做什么”：公司招什么岗位、活动议程反复出现什么主题、公开项目采购什么能力、合作公告透露什么资源配置。
- 交易层回答“用户为什么愿意付费”：产品页怎么承诺结果、价格怎么分层、报名页如何降低风险、评论区或 FAQ 里有什么购买异议。
- 公众号和网页文章适合回答“行业里有哪些说法”“对标作者怎么组织观点”，不能单独支撑高置信事实。
- Nowledge/Obsidian 默认不能作为高权重信息源。只有当它提供特别贴合的自有案例、历史项目、用户原话或内部经验时，才能进入 `CASE_LIBRARY.md`。
- 来自 Nowledge/Obsidian 的材料不能写成高置信 `fact`。如果确实使用，标为 `case`、`scenario`、`owned experience` 或低/中置信 `judgment`。
- 一个关键事实要进入正文，至少满足：1 个 `L1-fact` 来源，或 2 个相互独立的公开来源交叉确认。
- 公开证据必须保存具体页面 URL。搜索结果页、关键词、网站名、平台首页和“公开案例页”描述不能计为有效来源。
- `publish-ready` 默认要求行为层和交易层都有可审材料。主题确实不需要时，必须在最终汇报里说明，并显式使用检查器的豁免参数。

## 行为层采集规则

行为层不由用户手填关键词。Agent 从以下文件自动生成 `BEHAVIOR_SEED_PLAN.md`：

- `BOOK_BRIEF.md`：这本书解决什么问题。
- `READER_PROFILE.md`：读者是谁、处在什么场景。
- `POSITIONING.md`：核心主张和反常识判断。
- `OUTLINE.md`：每章需要证明什么。
- `SOURCE_MAP.md`：已有证据缺口在哪里。

优先采集开放网页，不碰登录墙：

| Signal Type | 典型来源 | 可支持判断 |
|---|---|---|
| job-posting | 招聘 JD、岗位说明、外包需求 | 组织正在配置什么能力 |
| event-agenda | 行业大会、公开课、直播议程 | 行业正在把什么主题当作问题 |
| case-page | 客户案例、服务商案例、合作案例 | 某类方法是否被真实组织采用 |
| tender | 招投标、采购公告、公示项目 | 预算和采购对象是否真实存在 |
| partnership | 合作公告、生态伙伴页、联合方案 | 哪些能力正在被打包成解决方案 |

`BEHAVIOR_LEDGER.md` 至少记录：`source_type`、`org`、`date`、`signal`、`evidence_excerpt`、`url`、`confidence`、`chapter_use`。

## 交易层采集规则

交易层也由 Agent 从书的定位自动推导，不默认让用户给竞品名单。优先看“读者会拿这本书解决什么购买前问题”。

优先采集：

| Signal Type | 典型来源 | 可支持判断 |
|---|---|---|
| pricing-page | 定价页、套餐页、报价说明 | 市场如何给结果定价 |
| offer-page | 产品页、服务页、课程页、咨询页 | 对方如何承诺结果和边界 |
| signup-page | 报名页、试用页、预约页 | 购买前需要哪些信任动作 |
| delivery-page | 交付说明、FAQ、服务条款 | 真实交付范围和风险边界 |
| objection | 评论区、FAQ、退款说明、差评 | 用户买之前担心什么 |

`TRANSACTION_LEDGER.md` 至少记录：`source_type`、`seller`、`offer`、`price_or_commitment`、`promise`、`boundary`、`objection`、`url`、`chapter_use`。

## 证据去后台化

`SOURCE_MAP.md`、`CLAIM_LEDGER.md`、`CASE_LIBRARY.md`、`BEHAVIOR_LEDGER.md`、`TRANSACTION_LEDGER.md` 是作者工作台，不是读者语言。正文引用证据时，必须把后台标签翻译成读者能理解的具体来源和具体处境。

禁止在正式正文里出现这些后台词：

- `SOURCE_MAP`
- `CLAIM_LEDGER`
- `CASE_LIBRARY`
- `BEHAVIOR_LEDGER`
- `TRANSACTION_LEDGER`
- `Layer A`
- `Layer B`
- `Layer C`
- `Layer D`
- `L1-fact`
- `L2-demand`
- `L3-behavior`
- `L4-transaction`
- `L5-discourse`
- `L6-owned`
- `A-authority`
- `B-demand`
- `C-discourse`
- `D-local-context`
- `高权重来源`
- `需求侧样本`
- `行为层样本`
- `交易层样本`
- `公众号元数据`
- `文章池`
- `抓取结果`
- `小红书样本`
- `线索`
- `适合放在`

工作台语言必须转换成读者语言：

| 工作台写法 | 正文写法 |
|---|---|
| 小红书需求侧样本显示 | 在公开评论和笔记里，读者反复问的是…… |
| 行为层样本显示 | 从公开招聘和活动议程看，组织正在把资源投向…… |
| 交易层样本显示 | 在公开产品页里，服务商通常把承诺写成…… |
| 公众号文章池提供线索 | 几位长期写这个领域的作者都把问题指向…… |
| C-discourse 案例线索 | 公开文章中有一个可复用的案例：…… |
| D-local-context | 我在自己的项目里见过一个相似场景：…… |
| L1-fact | 某机构 / 官方文件 / 报告在 YYYY 年指出…… |
| 低权重内部上下文 | 这只能作为经验提醒，不能当成行业事实。 |

写作规则：

- 不说“我们抓到了什么样本”，要说“读者在什么场景里表达了什么问题”。
- 不说“某资料适合放在某章”，要直接写成读者能读懂的案例、判断或提醒。
- 不说“线索”，要写成“可验证案例”“读者原话”“反方观点”“待核验事实”。
- 需求侧材料只证明“有人这样困惑或这样表达”，不能证明行业事实。
- 行为层材料证明“公开组织动作存在”，不能单独证明结果有效。
- 交易层材料证明“市场上有人这样承诺和销售”，不能单独证明交付质量。
- 自有案例要明确它是经验，不要包装成普遍规律。

## 权威账号地图

公众号调研先做 `AUTHORITY_ACCOUNTS.md`，再抓文章。不要一上来按关键词乱抓。

目标是找到这个主题所属领域里最值得读的 5-8 个来源：

- S-tier：有原创框架、长期影响力、被行业反复引用的人或机构。
- A-tier：持续输出高质量商业判断、案例和行业观察的公众号。
- B-tier：一线操盘者、公司官方号、垂直媒体，适合补案例和实操细节。
- Counter：反方、质疑者、失败案例来源，防止整本书只有单边观点。

推荐组合：

- 1-2 个领域公认专家或思想源头。
- 1-2 个机构/媒体/研究型公众号。
- 1-2 个一线操盘者或案例丰富的账号。
- 1 个反方或质疑来源。

商业性质强、平台变化快、AI 落地、自媒体运营、IP 打造、中小企业增长等主题，默认只抓最近 365 天文章。旧文章只用于经典框架或历史脉络，必须标记为 `evergreen` 或 `historical`，不能当作当前事实。

先用 `wechat-article-search` 按主题发现文章和账号，再用 `wxmp-article-harvester` 对确认账号归档；文章关键词筛选发生在归档之后，用本地检索覆盖核心词、同义词、反对词、购买词和场景词。

## 推荐调研顺序

1. 先写 `SOURCE_MAP.md`：列出问题、关键词、账号、URL、预期用途。
2. 写 `AUTHORITY_ACCOUNTS.md`：确认这个领域最值得读的公众号/专家/机构。
3. 用小红书抓需求：关键词至少覆盖核心词、替代词、反对词、购买词。
4. 自动生成 `BEHAVIOR_SEED_PLAN.md`，再用通用 Web 搜索与网页剪藏落地行为层来源。
5. 自动生成交易层关键词和竞品类型，再用通用 Web 搜索与网页剪藏落地交易层来源。
6. 用 `wxmp-article-harvester` 归档权威公众号最近 365 天文章，再本地关键词筛选。
7. 用网页剪藏落地单篇好文章或报告解读。
8. 用官方网页和报告补事实：把数据、规则、行业事实补齐。
9. 只在需要自有案例时查 Nowledge/Obsidian。
10. 把结果归档：事实进 `CLAIM_LEDGER.md`，案例和场景进 `CASE_LIBRARY.md`，行为信号进 `BEHAVIOR_LEDGER.md`，交易信号进 `TRANSACTION_LEDGER.md`，来源进 `bibliography.md` 和章节 `refs.md`。

## 写作前硬门

进入章节写作前，必须至少完成：

- `SOURCE_MAP.md` 有明确来源分层。
- `AUTHORITY_ACCOUNTS.md` 已选出 5-8 个候选来源，并说明为什么值得抓。
- 商业/平台/AI/运营类主题的公众号抓取窗口默认是最近 365 天。
- `CLAIM_LEDGER.md` 中的关键 fact 有 `L1-fact` 来源或交叉验证。
- 小红书需求证据已经转写成读者问题，而不是直接照搬评论。
- 行为层已经形成 `BEHAVIOR_SEED_PLAN.md` 和初版 `BEHAVIOR_LEDGER.md`；如果不需要，写明原因。
- 交易层已经形成初版 `TRANSACTION_LEDGER.md`；如果不需要，写明原因。
- Nowledge/Obsidian 没有被标成 high confidence source。
- 每章至少有 1 个公开案例、反例、行为信号、交易信号或自有案例素材。
