# Visual Plan

正文配图优先是信息图。每张图必须帮助读者理解结构、流程、对比、公式、清单或证据关系。

| ID | Chapter | Reader Problem | Visual Purpose | Type | Source | Required | Status | Output Path | Caption |
|---|---|---|---|---|---|---|---|---|---|
| fig-01 | chapter-01 | 待填写 | 待填写 | layer-stack / flowchart / quadrant / bar-chart / timeline / swimlane / state-machine / tree / waterfall / funnel / cover-visual / section-visual | Chapter model / evidence table / case table / imagegen | yes / no | planned / generated / inserted / rejected | assets/diagrams/fig-01.svg | 待填写：用“步骤一、步骤二、步骤三”或“步骤一 → 步骤二 → 步骤三”提供图内标签 |

## 使用规则

- 正文图默认是 Kami SVG 信息图，放在 `assets/diagrams/`。
- 封面、章节扉页和书外分发图可以用 `$imagegen`，放在 `assets/images/`。
- 没有读者理解功能的图不进入正文。
- 图表 caption 要能独立说明这张图的作用。
- 如果一段文字已经比图更清楚，保留文字，不画图。
