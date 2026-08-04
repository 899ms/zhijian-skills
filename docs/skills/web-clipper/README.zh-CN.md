# Web Clipper

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Web Clipper 把单篇文章 URL 或归档页经过分层提取后保存成结构化 Markdown">
</p>

<p align="center"><strong>把公开文章 URL 和归档页变成可迁移、可追溯、支持 Agent 批量收藏的 Markdown。</strong></p>

<p align="center"><a href="./README.md">English</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/web-clipper">统一源码</a></p>

适合让 Agent 收藏一篇公开文章、从 archive 页抓取指定数量的文章，或补上浏览器剪藏插件无法自动批处理的环节。它面向 Obsidian 和其他本地 Markdown 知识库，但输出不绑定具体软件。

## 安装

```bash
npx skills add zjp1997720/zhijian-skills \
  --skill web-clipper --agent codex --global --copy --yes
```

## 环境要求

- Python 3.9 或更高版本
- 可以访问目标公开网页的网络环境
- 可选 Node.js 与 `npx`，用于固定版本的 `defuddle@0.19.2` 提取器
- 可选浏览器控制能力，用于懒加载归档页和渲染后 DOM 兜底
- 可选 `METASO_API_KEY`；启用 Metaso Reader 可能产生账号费用，并会把目标 URL 发给第三方

所有命令都应从准备接收剪藏的 vault 或项目根目录执行。统一入口是：

```bash
bash <web-clipper-root>/scripts/run_web_clipper.sh --help
```

第一次运行有明确副作用：检查 Python，必要时尝试安装，创建默认 clipping 目录，并在当前项目写入 `.web-clipper/EXTEND.md`。

## 它做什么

- 把一篇公开文章保存为带 YAML frontmatter 的 `YYYY-MM-DD 标题.md`。
- 从归档页、索引页、专题页或作者主页收集指定数量的文章链接。
- 懒加载页面可以先由浏览器收集 URL，再交给确定性脚本批量落地。
- 记录真正成功的提取器：`static`、`defuddle`、`jina`、`metaso` 或 `browser_cdp`。
- 输出 `source_candidate` 元数据，方便后续筛选、知识编译或写作复用。
- 分开报告链接收集、正文提取和文件写入问题；空批次不会伪装成成功。

## 工作原理

1. wrapper 检查运行时，解析项目内输出目录，并写入可复用的本地配置。
2. 公开 X 长文和微信公众号文章优先尝试固定版本 Defuddle；普通网页优先读取静态 HTML、JSON-LD、`<article>` 或 `<main>`。
3. 失败页面按站点特征继续尝试 Defuddle、Jina Reader 和可选 Metaso。
4. 懒加载索引页由可用浏览器收集 URL，脚本再逐篇写入 Markdown。
5. 静态提取和普通 Browser 运行时都失败、但页面在 Chrome 中可见时，可用 CDP 流程读取渲染后 DOM，并记录 `browser_cdp`。

浏览器负责渲染与找链接；脚本负责稳定的文件名、元数据、正文序列化和批量结果回执。

## 请求示例

```text
把这篇公开文章保存到我的 Obsidian Clippings，保留作者、日期和原链接：<URL>
```

```text
把这个 archive 页前 20 篇文章保存成 Markdown；如果页面懒加载，先用浏览器收集 URL：<URL>
```

```text
这篇公众号文章静态提取失败，但 Chrome 能打开。保存完整渲染正文，并记录实际使用的提取器：<URL>
```

## 输出

```yaml
---
type: "source_candidate"
title: "示例文章"
source: "https://example.com/article"
published: "2026-08-04"
extractor: "static"
compile_status: "queued"
status: "unprocessed"
topics:
  - Agent
candidate_outputs:
  - source_card
  - writing_fuel
tags:
  - clipping
---
```

## 安全与限制

- 只处理有权访问的公开 HTTP(S) 页面，不绕过登录、付费墙、验证码或访问控制。
- wrapper 只接受当前项目内的输出路径；必须从目标 vault 根目录运行。
- Jina Reader 和可选 Metaso 会接收目标 URL。设置 `METASO_API_KEY` 即表示启用 Metaso；先确认费用与数据传输边界。
- Defuddle 以固定版本 `npx` 包运行。没有 Node.js 时，其他提取路径仍可使用。
- Browser 和 CDP 兜底依赖当前 Agent Harness 与可用的浏览器控制 Skill。
- 网页正文可能受版权保护。保留作者、日期与原链接，只用于获得授权的研究或内部归档；未经许可不要公开转载全文。
- 网页结构和反自动化策略会变化。Skill 会指出失败层级，但不能承诺所有站点都能成功提取。

## 仓库结构

```text
skills/web-clipper/
├── SKILL.md
├── agents/openai.yaml
├── evals/evals.json
├── references/config/first-time-setup.md
├── scripts/
└── tests/
```

## 许可证

[MIT](../../../LICENSE)
