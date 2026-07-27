# Kami Output Rules

Leadbook 的正式 PDF 使用 `$kami` 中文 long-doc 风格输出。正文图优先是信息图，不是氛围插画。

## 输出原则

- 书籍正文是独立出版物，不是销售资料。
- PDF 内只包含正式内容和必要附录。
- `distribution-note.md`、`private-domain-pack.md` 是书外材料，不进入 PDF。
- Kami 负责排版和信息图语言，不负责补事实。事实缺口必须先在 `CLAIM_LEDGER.md` 处理。
- 正文配图的任务是降低理解成本：把大段文字变成结构、流程、对比、公式、检查清单。
- 氛围视觉只适合封面、章节扉页或分发海报；正文段落默认不用氛围图。

## 视觉标准

- 背景：parchment `#f5f4ed`
- 强调色：ink-blue `#1B365D`
- 中文标题：TsangerJinKai02，缺失时用 Source Han Serif / Noto Serif CJK fallback
- 正文：克制、正式、可长期阅读
- 页面：A4 long-doc
- 图表：只在能提升理解时使用

## Visual Planning

写正文后、导出 PDF 前，先维护 `VISUAL_PLAN.md`。不要边导出边临时想图。

每张图必须回答：

- 图解决读者的哪一个理解问题？
- 图里展示什么结构，读者能通过看图少读哪一大段文字？
- 这张图是正文信息图，还是封面 / 章节扉页视觉？
- 图的来源是正文结构、证据表、案例表，还是 `imagegen` 生成？
- 这张图是否必须进入 PDF？

推荐字段：

| ID | Chapter | Reader Problem | Visual Purpose | Type | Source | Required | Status | Output Path | Caption |
|---|---|---|---|---|---|---|---|---|---|
| fig-01 | chapter-01 | 读者分不清能力、服务、产品 | 把三层关系画清楚 | layer-stack | Chapter model | yes | planned | assets/diagrams/fig-01.svg | 能力不是产品，产品是能力的交易包装 |

## Kami Information Diagrams

正文默认用 Kami diagram primitive。新版 Kami 已经把 diagram 当成 long-doc 内部素材，优先从 `$KAMI_SKILL/assets/diagrams/` 取模板或风格参考。

当前实现边界：

- 已安装 Kami 时默认使用 `~/.agents/skills/kami`；未安装时 HTML 导出使用内置基础模板，Core Markdown 流程不受影响。
- SVG 是正文里的结构素材，不是独立海报。不要画外层大卡片、内部标题区、logo、watermark、`Kami information diagram` 备注。
- 图内只保留读者需要理解的结构：节点、箭头、分层、坐标、数量关系。
- 图外由正文和 figcaption 解释，图内不重复章节结论。
- 图的可见结构必须与正文宽度对齐；避免“透明画布 full-width，但节点只占中间一小块”。
- 节点宽度、箭头落点、分隔线按固定网格布置。肉眼可见的偏移、漂浮箭头、遮挡都算失败。
- 中文标签优先缩短到 2-6 个字；长标签必须换行并保持在节点内。

优先选择：

| 内容关系 | Diagram Type |
|---|---|
| 方法论分层、能力地图、系统层级 | `layer-stack` / `tree` |
| 流程、决策路径、承接链路 | `flowchart` |
| 跨角色协作、用户旅程 | `swimlane` |
| 生命周期、状态变化 | `state-machine` |
| 路线图、阶段推进 | `timeline` |
| 二维分类、优先级判断 | `quadrant` |
| 分类对比、数量对比 | `bar-chart` |
| 价值拆解、收益桥 | `waterfall` |

生成器把 `tree` 映射为 `layer-stack`，把 `state-machine` 映射为 `flowchart`，把 `bar-chart` 映射为结构化卡片。未列出的类型会明确失败，不会静默生成错误图型。

判断标准：

- 一段好文字是否比图更清楚？如果是，不画。
- 图能不能被一句 caption 准确解释？不能，就先重写模型。
- 图里是否出现英文工程标签、旋转英文、无意义装饰？有就重画。
- 图是否只是在“让页面不空”？如果是，删掉。
- 图是否出现内框、水印、模板说明、重复大标题？有就重画。
- PDF 页面上图的可见内容是否与正文宽度一致？不一致就重画或改 SVG viewBox / 坐标。

## imagegen Visuals

`$imagegen` 用于生成位图视觉，默认只放在：

- 封面主视觉
- 章节扉页
- 书外分发图

正文段落不默认使用 AI 氛围插图。正文需要图片时，优先用 Kami 信息图或真实截图 / 案例素材。

使用 `$imagegen` 时必须维护 `IMAGEGEN_BRIEF.md`：

| Field | Rule |
|---|---|
| Use | cover / section opener / distribution image |
| Reader Function | 这张图帮助读者进入什么主题或情绪 |
| Style | kami parchment, ink-blue, editorial, restrained |
| Prompt | 可复用 prompt |
| Output Path | `assets/images/...` |
| Status | planned / generated / inserted / rejected |

Prompt 原则：

- 用“paper editorial / structured business method / warm parchment / ink-blue”保持 Kami 一致性。
- 不生成正文概念图。概念图用 SVG 信息图。
- 不生成假截图、假数据、假品牌、假人物。
- 不让图承担事实证明功能。

## Build Steps

1. `python3 scripts/export-markdown.py`
2. `python3 scripts/check-leadbook.py --target draft dist/book.md`
3. `python3 scripts/generate-kami-diagrams.py`
4. `python3 scripts/export-kami-html.py dist/book.md dist/book.html`
5. `python3 scripts/render-pdf.py dist/book.html dist/book.pdf`
6. `python3 scripts/prepare-pdf-visual-audit.py`
7. 实际查看 contact sheet 和逐页 PNG，完成 `dist/qa/pdf-visual-audit.md`
8. `python3 scripts/check-leadbook.py --target review-ready --update-state dist/book.md`

第 2 步属于正文级 `draft` 门。此时允许 `VISUAL_PLAN.md` 中已规划的 SVG / section image 尚未生成；检查器会给 warning。`review-ready` 与 `publish-ready` 仍把缺失视觉资产作为 error。

公开分发前额外运行：

```bash
python3 scripts/check-leadbook.py --target publish-ready --update-state dist/book.md
```

如果没有信息图，`generate-kami-diagrams.py` 可以不生成新文件，但 `VISUAL_PLAN.md` 仍要说明为什么不需要图。

## Metadata

`export-kami-html.py` 必须填充：

- `{{文档标题}}`
- `{{作者}}`
- `{{摘要}}`
- `{{关键词}}`

PDF 生成后，检查 HTML 内不应残留任何 `{{...}}`。

## PDF Visual QA

正式交付前至少检查：

- 封面：标题、作者、版本、封面视觉不遮挡正文。
- 目录：不要出现假的页码占位符，例如 `—`。
- 每个章节首页：标题不贴边，不出现低密度空页。
- 每张图：caption 清楚，图不溢出，文字可读，没有旋转英文标签，没有水印/内框/模板备注。
- 每张图：可见图形区域要和正文宽度协调；不能出现正文宽、图窄，或图框宽、内容窄。
- 每张图：节点内文字居中、不出框；箭头落在节点边缘或清晰连接点。
- 正文节奏：连续两页纯大段文字后，应出现表格、信息图、检查清单、案例框或自测框。
- 尾页：附录、参考来源、工具包不是销售页。

推荐验收方式：

```bash
pdftoppm -png -r 110 dist/book.pdf /tmp/leadbook-pages/page
```

把含图页面做成 contact sheet 或逐页打开检查。自动检查只能确认文件存在，不能替代视觉验收。

视觉验收必须写入 `dist/qa/pdf-visual-audit.md`，至少记录：

- 渲染命令。
- 每个含图页的页码和页面图片路径。
- 是否检查封面、目录、图表、caption、尾页。
- 发现的问题、修复状态和剩余风险。

没有 `dist/qa/pdf-visual-audit.md`，不能汇报 `review-ready` 或 `publish-ready`。
