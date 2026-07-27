# Leadbook Quality Gates

## 完成状态定义

`leadbook` 必须用三档状态汇报，不得把主书完成说成整包发布完成。

| 状态 | 含义 | 允许缺口 | 必须通过 |
|---|---|---|---|
| `draft` | 正文可继续写作和内部修改 | 证据未闭环、PDF 未出、附件未做 | 正文无硬 CTA、无后台词、无明显草稿残留 |
| `review-ready` | 主书完整，可内部评审 | 书外运营包可未完成，公众号抓取可标 partial | `dist/book.md`、`dist/book.html`、`dist/book.pdf`、参考资料页、证据表、视觉资产、状态表 |
| `publish-ready` | 整套公开分发包完整 | 无默认缺口；例外必须显式说明 | `review-ready` 全部项目、公众号/权威来源闭环、行为层、交易层、工作表、分发说明、私域承接包、PDF 视觉审计 |

推荐命令：

```bash
python3 scripts/check-leadbook.py --target draft dist/book.md
python3 scripts/check-leadbook.py --target review-ready --update-state dist/book.md
python3 scripts/check-leadbook.py --target publish-ready --update-state dist/book.md
```

需要把检查结果写入状态或审计记录时，使用：

```bash
python3 scripts/check-leadbook.py --target publish-ready dist/book.md --output-json
```

最终汇报必须写明当前状态。没有通过 `publish-ready`，不得使用“可发布”“完整引流包”“交付闭环完成”这类表述。

## 正文硬门

正式书籍正文必须满足：

- 独立成立：没有任何后端产品，读者也能完整受益。
- 不写硬 CTA：不得出现“加企微”“领取资料”“购买课程”“咨询我”等转化话术。
- 不绑定产品：不得把正文逻辑导向某个课程、定制服务或分身系统。
- 不伪精确：无法核验的数据写数量级或标记缺口。
- 不空泛：少用抽象大词，多用具体场景、判断、案例和动作。

## 默认禁止词

这些词不是绝对不能出现，但出现时必须有具体定义和上下文。无定义时删掉：

- 赋能
- 重构
- 拥抱
- 范式
- 生态
- 闭环
- 抓手
- 破局
- 底层逻辑
- 认知升级
- 打造
- 全链路

## 章节完成定义

每章完成使用 chapter contract。不同书型可以用不同标题和叙事结构，但必须具备：

1. 结论或判断：直接给判断。
2. 读者问题：具体到场景，不写泛泛焦虑。
3. 证据或来源：事实、需求、行为、交易、观点或自有案例来自哪里。
4. 案例或反例：来自 `CASE_LIBRARY.md`、`BEHAVIOR_LEDGER.md`、`TRANSACTION_LEDGER.md`，或明确标记为假设案例。
5. 行动产出：读者读完本章会得到一个判断、工具、模板、清单、自测或动作。
6. 作者判断：至少 1 处带有 `voice_profile` 特征的明确判断。

不强制每章使用同一套标题。白皮书可以偏事实链和边界，playbook 可以偏步骤和模板，方法论书可以偏概念定义和系统关系。

chapter contract 是覆盖面要求，不是栏目清单。`行动产出` 可以是一条判断原则、一张模型图、一个决策表、一个步骤、一份模板或一个附录入口；不等于每章都必须出现“操作方法”“本章产出”“自测问题”这些标题。

## 读者体验门

正式稿必须从读者视角读一遍。以下情况直接返工：

- 读者看不出作者是谁、凭什么这样判断。
- 章节只是在搬运资料，没有作者立场、取舍和边界。
- 读者看到“样本、线索、元数据、文章池”这类后台词。
- 案例只写“某人/某品牌/某公司”，没有具体处境、动作、结果。
- 目录只有章节名，没有让读者知道读完会获得什么。
- 连续两页都是长段落，没有表格、模型、清单、案例框或信息图调节节奏。

## 反说明书门

以下情况说明正文正在从“书”滑向“说明书”或“工作坊手册”：

- H1 后直接进入第 1 章，没有真正的开场、问题重定义和阅读路径。
- 大多数章节重复同一组二级标题，尤其是 `本章产出 / 操作方法 / 自测问题`。
- 非 `course-manual` 正文把大量填写任务、练习题、检查表放在主结构里。
- 每章都像独立任务单，看不出上一章到下一章的推进关系。
- 作者判断很少，更多是在分发工具，而不是建立一个更完整的判断框架。

处理原则：

- `playbook` 可以保留更强的动作密度，但也不能每章机械复用同一骨架。
- `methodology-book`、`whitepaper`、`business-report` 优先保证开场、论证、模型、边界和章节节奏。
- 能进入 `dist/worksheets/` 的填写任务，优先不抢正文主结构。

## Voice Profile Gate

`BOOK_BRIEF.md` 必须写明 `content_profile`、`voice_profile` 和 `voice_anchor`。名人锚点只用于压缩思考姿态，不用于复制原文句式、口头禅和可识别表达。正文必须符合所选 voice：

- `strategy-consultant`：Drucker / Christensen 型，每章有取舍判断和边界。
- `operator-playbook`：Hormozi / Ramit 型，每章有操作步骤、错误清单或交付标准。
- `research-analyst`：Mary Meeker / Ben Thompson 型，事实、推论和作者判断分开。
- `product-architect`：Bezos / Marty Cagan 型，每章有输入、输出、模块关系或失败信号。
- `austrian-economics`：Hayek / Mises / Kirzner 型，解释主观价值、激励、机会成本或市场信号。
- `teacher-coach`：Feynman / Sal Khan 型，有学习路径、练习、自测或过渡解释。

一章读完像资料汇编，判定为 voice_profile 未落地。

## 事实与判断

- 当前事实、市场数据、平台规则、公司/产品信息必须进入 `CLAIM_LEDGER.md`。
- 公开 fact、行为信号和交易信号必须提供具体页面 URL；“公开检索”“厂商案例页”“某平台岗位”不计入有效证据。
- 引用外部材料时记录来源、发布日期、访问日期。
- 推论必须写成“基于以上事实，我的判断是...”，不要把判断伪装成事实。
- 高置信事实必须来自 `L1-fact` 权威来源，或至少两个独立公开来源交叉验证。
- 小红书只作为需求侧证据：用户语言、痛点、反对意见、内容反应，不能单独支撑行业事实。
- 行为层只证明公开组织动作存在：招聘、活动、公开项目、合作公告不能单独证明方法有效。
- 交易层只证明市场上有人这样承诺和销售：定价页、产品页、报名页、交付说明不能单独证明交付质量。
- 公众号和网页文章是观点侧证据，引用其事实时要追到原始来源。
- 公众号文章池必须先经过 `AUTHORITY_ACCOUNTS.md` 筛选：先确认领域权威账号，再抓最近 365 天文章。
- 商业、平台、AI、运营、自媒体类主题使用超过 365 天的公众号材料时，必须标记为 `evergreen` 或 `historical`。
- Nowledge/Obsidian 只作为低权重本地上下文；除非是特别贴合的自有案例，否则不进入正文证据链。
- Nowledge/Obsidian 不得作为 high confidence fact 的来源。

## 证据表达门

正式正文禁止出现后台证据语言：

- `SOURCE_MAP`
- `CLAIM_LEDGER`
- `CASE_LIBRARY`
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
- `需求侧样本`
- `行为层样本`
- `交易层样本`
- `公众号元数据`
- `文章池`
- `抓取结果`
- `小红书样本`
- `线索`
- `适合放在`
- `后续补`
- `这里先提炼`

每个证据段落必须写成读者语言：

- 来源是谁。
- 发生在什么时间或什么场景。
- 它能支持什么。
- 它不能支持什么。

## 视觉资产门

正文配图必须来自 `VISUAL_PLAN.md`。每张图都有读者用途、图型、来源、路径和 caption。

硬门：

- 信息图缺文件，不能交付。
- Markdown 图片路径不存在，不能交付。
- 图表 caption 缺失，不能交付。
- 图表文字不可读、出框、溢出页面、没居中、出现明显英文工程标签，必须返工。
- 图表出现内框大卡片、模板水印、`Kami information diagram` 备注、内部重复大标题，必须返工。
- 图表的 SVG 画布虽然满宽但可见图形只占中间一小块，必须返工。
- 正文使用 AI 氛围图替代结构图，必须返工。
- `$imagegen` 生成图必须登记在 `IMAGEGEN_BRIEF.md`，并写清用途。

案例分级：

- A 级：公开、可核验、有具体处境、动作、结果。
- B 级：公开但信息不完整，可以作为辅助案例。
- C 级：读者需求、评论、场景抽象，只能作为“场景”或“问题”，不能包装成完整案例。
- D 级：自有经验或匿名案例，必须标明边界。

C 级需求材料不能标题写成“案例”，只能写成“读者场景”“常见困惑”“反对意见”。

## 输出前检查

正式 PDF 生成前检查：

- `dist/book.md` 不包含硬 CTA。
- `dist/book.html` 没有 `{{...}}` placeholder。
- 目录和章节顺序正确。
- 图表不溢出页面。
- 图表所在 PDF 页面已渲染成图片并逐页视觉检查。
- 中文字体正常。
- 目录不出现假的页码占位符，例如 `—`。
- 封面包含书名、副标题、作者、版本或日期；封面视觉不遮挡文本。
- 每张图能在 PDF 中被读者看清，caption 能独立解释图的作用。
- 每张图与正文宽度协调，图内文字不出框、不漂移、无模板备注。
- `dist/qa/pdf-visual-audit.md` 已记录渲染命令、含图页、检查结果、修复状态和剩余风险。
- 视觉审计覆盖 PDF 的每一页，并且每个 `VISUAL_PLAN.md` 必检图表 ID 都映射到具体页码。
- 公开发布级 PDF 的参考资料分页没有单条孤项或大面积空白尾页。
- 成熟度由 `check-leadbook.py --update-state` 签发；手工修改状态不构成通过。
- `distribution-note.md` 和 `private-domain-pack.md` 没有进入正式书籍正文。
- `CLAIM_LEDGER.md` 没有把 Nowledge/Obsidian 标成 high confidence source。
- `SOURCE_MAP.md` 已记录事实、需求、行为、交易、观点、自有来源的不同用途。
- `AUTHORITY_ACCOUNTS.md` 已记录公众号候选、选择理由、抓取窗口和输出路径。

## Publish-Ready 硬门

公开发布前额外检查：

- `book-state.yaml` 中 `research.wxmp_pack` 不能是 `partial / false / blocked / rate-limited`；若主题明确不需要公众号证据，必须在汇报里说明，并显式使用 `--allow-partial-wxmp`。
- `research.wxmp_rate_limited` 不能为 `true`。
- `AUTHORITY_ACCOUNTS.md` 至少有 5 个有效 selected / exported / fetched / done 来源；少于 5 个不得默认发布。
- `BEHAVIOR_LEDGER.md` 至少有 3 条有效行为信号；若主题不需要，必须显式说明并使用 `--allow-missing-behavior`。
- `TRANSACTION_LEDGER.md` 至少有 3 条有效交易信号；若主题不需要，必须显式说明并使用 `--allow-missing-transaction`。
- `book-state.yaml` 中 `research.behavior_pack` 和 `research.transaction_pack` 必须标记为闭环状态。
- `dist/qa/pdf-visual-audit.md` 不能缺失，不能保留 `open` 状态问题，不能残留草稿词。
- `dist/qa/pdf-visual-audit.md` 必须勾选参考资料分页检查，不能留下单条孤项或大面积空白尾页。
- `dist/worksheets/` 不能只有 `.gitkeep`，至少要有一份可填写或可执行工作表。
- 工作表必须有可填写行动结构，能对应主书核心模型，不能只是空文档。
- `dist/distribution-note.md` 不得残留“待填写 / 待补充 / 待完善”等草稿词。
- `dist/private-domain-pack.md` 不得残留“待填写 / 待补充 / 待完善”等草稿词。
- `dist/distribution-note.md` 必须包含书籍定位、适合读者、读完能得到什么、分发边界。
- `dist/private-domain-pack.md` 必须包含欢迎语、标签问题、读者分层、后续内容、边界说明。
- `dist/book.md` 必须有读者可见的“参考资料 / 参考来源 / 延伸阅读 / Bibliography / References”章节，或单独生成 `dist/references.md`。
- 最终汇报必须区分主书质量和整包质量：例如“主书 review-ready，publish-ready 还差 wxmp 和 worksheets”。
