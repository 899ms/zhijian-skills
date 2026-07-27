# Imagegen Brief

`$imagegen` 只用于封面、章节扉页和书外分发图。正文解释性图优先使用 Kami SVG 信息图。

| ID | Use | Reader Function | Style | Prompt | Output Path | Status | Notes |
|---|---|---|---|---|---|---|---|
| cover-visual | cover | 待填写：帮助读者进入什么主题 | kami parchment, ink-blue, editorial, restrained | 待填写 | assets/images/cover-visual.png | planned / generated / inserted / rejected | 待填写 |

## Prompt Rules

- 风格保持 Kami：warm parchment, ink-blue accent, editorial, restrained, paper texture。
- 不生成正文概念图。概念关系用 SVG 信息图表达。
- 不生成假截图、假数据、假品牌、假人物。
- 不让图承担事实证明功能。
- 生成后把图片复制到 `assets/images/`，不要只保留在临时目录。
