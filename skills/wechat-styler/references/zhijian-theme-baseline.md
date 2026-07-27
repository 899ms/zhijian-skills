# Zhijian 主题视觉基线

`theme_revision: editorial-weighted-2026-07`

这份基线记录智见AI 公众号主题的审美取舍和可执行样式锁。统一品牌语气依靠颜色、节奏和结构；标题、正文、元信息与代码按角色分工。

## 版本对照

| 维度 | 旧版编辑感 | 1.9.0 统一宋体版 | 当前基线 |
|---|---|---|---|
| H2 | 仓耳今楷 22/500 | 思源宋体 VF 22/500 | 仓耳今楷 22/500 |
| H3 | 仓耳今楷 18/600 | 思源宋体 VF 19/500 | 仓耳今楷 18/600 |
| 正文 | 思源宋体 17/400/1.58 | 思源宋体 VF 15/400/1.68 | 思源宋体 VF 15/450/1.68 |
| 元信息 | 思源黑体 13 | 思源宋体 VF 12 | 思源黑体 13 |
| 加粗 | 暖陶 `#A04A2E` | 近黑 `#141413` | 暖陶 `#A04A2E` |
| 链接 | 暖陶 | 墨蓝 | 墨蓝 |
| 引用 | 暖陶左线 | 信任蓝卡片 | 信任蓝卡片 |

当前基线保留 1.9.0 的移动端字号、信任蓝引用、墨蓝链接、内容密度门和移动端 QA；恢复旧版标题性格、正文重量、元信息清晰度和暖陶阅读锚点。

## 样式锁

- H2：仓耳今楷优先，22px / 500 / 1.28，4px 暖陶左线。
- H3：仓耳今楷优先，18px / 600 / 1.32，墨蓝。
- 正文与列表：思源宋体 VF 优先，15px / 450 / 1.68，近黑 `#141413`。
- 图注与元信息：思源黑体优先，13px / 1.4，石灰 `#6B6A64`。
- 普通加粗：暖陶安全文字色 `#A04A2E`；链接：信任蓝 `#1B365D`。
- 引用：浅信任蓝底 `#EEF2F7`，无左线，开引号与首行同段对齐。

## 视觉证据

- 版本实页对照：`../assets/zhijian-theme-version-comparison-2026-07.jpg`
- 当前 390px 移动端基线：`../assets/zhijian-theme-mobile-baseline.png`
- 可重复输入：`tests/fixtures/zhijian-visual-baseline.md`

生成并验证：

```bash
node scripts/convert.mjs tests/fixtures/zhijian-visual-baseline.md \
  --theme zhijian --output /tmp/zhijian-visual-baseline.html

npm run qa:mobile -- /tmp/zhijian-visual-baseline.html \
  --expect-zhijian \
  --screenshot assets/zhijian-theme-mobile-baseline.png
```

任何主题调整必须同时更新样式锁、自动回归和移动端基线图。字体变更还要在真实手机上核对回退字体；仓耳今楷未安装时允许回退到思源宋体。
