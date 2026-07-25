# 微信公众号文章采集器

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="微信公众号文章采集器通过正文质量门并在状态账本中记录完整或部分成功结果">
</p>

<p align="center"><strong>把指定公众号加工成可迁移的 Markdown、索引和真实反映完成度的采集报告。</strong></p>

<p align="center"><a href="./README.md">English</a> · <a href="https://github.com/zjp1997720/zhijian-skills/tree/main/skills/wxmp-article-harvester">统一源码</a></p>

适合按明确公众号、日期范围和标题规则归档公开文章，也适合补全文、筛选教程文章和安全续抓深历史内容。

## 安装

```bash
npx skills add zjp1997720/zhijian-skills \
  -g -a codex --skill wxmp-article-harvester -y
```

## 环境要求

- Python 3.10+
- [`wcx`](https://github.com/lovstudio/wcx)，Skill 内固定了已验证 commit
- Python Playwright 与 Chromium
- 一个可登录 `mp.weixin.qq.com` 后台的公众号账号，用于搜索账号和读取官方文章索引
- 可选 `METASO_API_KEY`，仅在用户明确同意付费与第三方 URL 传输后使用

第一次运行前执行确定性预检：

```bash
python3 scripts/preflight.py --json
```

预检只报告依赖状态，不会自动安装或升级软件。

## 它做什么

- 通过 `wcx` 确认公众号并导出官方文章元数据。
- 按精确日期、年份、最近时段或透明标题正则筛选文章。
- 通过 Playwright 读取公开页面 DOM，保留图片在正文中的顺序。
- 拒绝摘要占位、通用 Video 页面壳、验证码、已删除页面和低信息量正文。
- 输出 Markdown 正文、JSON/CSV/Markdown 索引和未完成项报告。
- 通过任务指纹、远端边界、游标日期、冷却时间和完成原因安全续抓深历史文章。

## 实测证据

一次带日期的腾讯 WorkBuddy 实测中，流水线索引了 23 篇文章，筛出 10 篇教程类标题，保存 9 篇可信 Markdown 正文，并把 1 篇视频页面壳如实标记为 `partial`。这是单账号实测结果，不代表全平台平均成功率。

## 工作原理

1. `preflight.py` 检查运行环境和固定的 `wcx` API 契约。
2. `wcx_run.py` 在后台登录态失效时刷新一次，再导出公众号元数据。
3. `harvest_wxmp.py` 执行日期、标题筛选，并检查已有正文是否可信。
4. Playwright 提取公开页面 DOM。第一次命中微信验证码即打开熔断，停止本轮后续浏览器请求，同时保全已经验证的 Markdown。
5. 原子写入 `articles/`、三个索引、`harvest-report.md` 和批次状态。

`wcx 0.2.0` 没有 CLI cursor。这个 Skill 通过已验证的 Python API 实现真实 offset 批次，并联合远端总量、头部文章 ID、上一批边界 ID 和游标日期证明续传连续性。只有游标越过目标日期或远端列表耗尽时，任务才会标记完成。

## 请求示例

```text
把这个公众号最近 30 天的文章保存成 Markdown。
```

```text
把这个公众号从 2026-06-01 到 2026-06-30 的教程类文章抓下来，正文要完整，不要用付费 API。
```

```text
冷却时间到了，继续上次的年度采集；如果游标漂移就直接报告。
```

```text
把这个公开的 mp.weixin.qq.com 文章保存成 Markdown，保留正文图片顺序。
```

## 输出

```text
<公众号>/
├── articles/
│   └── YYYY-MM-DD 标题.md
├── index.json
├── index.csv
├── index.md
├── harvest-report.md
└── .harvest-state.json   # 仅批次模式
```

每篇文章都有明确状态。`browser`、`existing`、`wcx` 和经过授权的 `metaso` 代表可信完整正文；`partial` 表示已有元数据，但缺少可信全文。

## 安全与限制

- 只接受公开的 `https://mp.weixin.qq.com/s...` 文章 URL。
- 每批元数据请求硬限制为 80。续抓命令会执行冷却，测试覆盖场景除外。
- 登录值和 Cookie 只通过受保护的运行时通道传递，不打印，也不进入命令参数。
- Metaso 默认关闭，因为它可能产生费用，并会把文章 URL 发给第三方。
- 纯视频文章可能保持 `partial`；Skill 不会虚构文字正文。
- 微信验证码和风控可能暂时降低正文成功率；已经验证的旧文件会被保留。
- 只用于获得授权的研究、学习和内部归档。保留作者、发布时间和原文链接；未经许可不要重新发布受版权保护的全文。

## 仓库结构

```text
skills/wxmp-article-harvester/
├── SKILL.md
├── agents/openai.yaml
├── evals/evals.json
├── references/troubleshooting.md
├── scripts/
└── tests/
```

## 许可证

[MIT](../../../LICENSE)
