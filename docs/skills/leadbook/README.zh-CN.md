# Leadbook

把一个商业主题生产成有证据、有章节状态、可审计质量门的中文短书、白皮书、方法论书或操作手册。

## 安装

```bash
npx skills add zjp1997720/zhijian-skills \
  -g -a codex --skill leadbook --copy -y
```

安装后，提供主题、读者或书名，并明确使用 `$leadbook`。

## 环境要求

- Core 流程只需要 Python 3.10+ 标准库。
- 默认：公开 Web，用于事实、行为、交易和观点证据。
- 可选：公众号、小红书和本地内容 Provider；缺失时不影响 Core 成书流程。
- 可选：Kami 与 WeasyPrint 或 Chrome/Chromium，用于更完整的 HTML/PDF 排版。

脚手架、状态同步、Markdown 导出、SVG 生成和质量检查都可以在没有外部服务时运行。

## 功能

- 生成结构化书籍项目，避免把整本书散落在一次长回复里。
- 分离 Brief、读者、定位、证据账本、章节、视觉和书外分发材料。
- 用事实、需求、行为、交易、观点、自有经验六层证据支撑内容。
- 支持白皮书、playbook、方法论书、商业报告和课程手册。
- WIP 导出自动跳过仍是模板的未写章节。
- 使用 `draft`、`review-ready`、`publish-ready` 三档质量门。
- 要求公开事实、行为和交易记录提供可直接核验的具体 URL。
- 用 `.leadbook-run.json` 保存阶段检查点，支持长任务中断后精确续跑。
- 用摘要绑定的 gate receipt 事务化升级成熟度，防止手工状态误报。
- 自动渲染全部 PDF 页面、生成 contact sheet 和逐页视觉检查清单。
- 构建前的 `draft` 门允许已规划视觉资产暂未生成；评审与发布门仍强制资产真实存在。
- 发布级视觉门拦截参考资料单条孤页或大面积空白尾页。
- 先产出 Markdown，再按需生成 SVG、HTML、PDF、工作表和分发材料。

## 工作方式

1. 创建带安全标记的 Leadbook 项目，并同步初始章节树。
2. 生成 v0 Brief、读者画像、定位、证据计划、开场和大纲。
3. 默认从公开 Web 采集证据，并把具体 URL 映射到章节。
4. 每次只写一章，删除模板标记，再同步状态。
5. 导出 Markdown；未写章节不会污染 WIP 书稿。
6. 生成信息图、HTML 和 PDF，运行逐页视觉 QA。
7. 使用 `check-leadbook.py --update-state` 签发质量门 receipt。

状态同步采用 merge，保留已有研究与进度，并重新计算章节字数、引用和案例。脚手架不会覆盖没有 Leadbook 标记的非空目录。

## 示例请求

```text
使用 $leadbook 写一本面向中小企业老板的 AI Agent 落地白皮书。
```

```text
使用 $leadbook 继续写第三章，其他未写章节先不要进入 WIP 书稿。
```

```text
使用 $leadbook 检查这本书是否达到 publish-ready，不要补造缺失证据。
```

## 安全与限制

- `--force` 只允许替换带 `.leadbook-project.json` 标记的既有项目。
- 可选 Provider 失败会保留在状态表中，不会被写成已经闭环。
- 小红书详情 token 只在内存中使用，输出默认删除 token、原始响应和 IP 地域。
- 使用非本机小红书 Provider 时必须显式确认，因为详情请求会传输短期 token。
- 自动检查不能替代人工事实审查和 PDF 逐页视觉检查。
- 搜索词、网站名、平台首页和“公开案例页”描述不会被计为有效证据。
- 状态文件里的 `review_ready` / `publish_ready` 必须有当前产物摘要匹配的 gate receipt。
- 门禁自动同步视觉覆盖率；失败的发布门不会抹掉仍有效的 `review-ready` 视觉状态。
- 内置 HTML 模板保持基础可用；Kami 是可选的首选编辑排版方案。

## 仓库结构

```text
skills/leadbook/
├── SKILL.md
├── agents/
├── assets/repo-template/
├── evals/
├── references/
├── scripts/
└── tests/
```

## 许可证

[MIT](../../../skills/leadbook/LICENSE)
