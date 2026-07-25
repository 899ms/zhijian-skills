# OpenCLI 注入微信编辑器

微信编辑器会过滤粘贴内容中的 `<animate>`。`scripts/inject-to-wechat.mjs` 通过 OpenCLI 直接注入 DOM，并负责标题、摘要、封面、图片转存和草稿验证。

## 发布后端能力边界

选择注入后端时必须先做只读探测。一个后端只有同时满足以下条件，才能替代 OpenCLI：

1. 允许访问 `mp.weixin.qq.com/cgi-bin/appmsg` 编辑页的 DOM；
2. 允许写入正文编辑区，而不只是只读 `evaluate`；
3. 写入后能回读并确认 `<svg>` 与 `<animate>` 数量；
4. 能通过页面可见信号确认本次草稿保存。

当前 Codex Chrome Browser 在该编辑页会触发域级安全拒绝，并明确禁止通过 CDP 或其他浏览器命令绕过。它不能作为公众号注入后端。遇到该拦截时直接使用 OpenCLI，不要尝试规避安全策略。只有未来同一后端通过上述四项真实编辑器实测后，才能升级为默认路径。

## 前置条件

- `opencli doctor` 显示 daemon、extension 和 profile 已连接
- Chrome 已登录微信公众号后台
- 编辑器页面已经打开，或已有可用的编辑器 URL
- 自动图片优化需要 macOS `sips` 和本机 PicGo/PicList 服务

## 推荐用法

```bash
node scripts/inject-to-wechat.mjs article_wechat.html \
  --reuse-current \
  --title "公众号标题" \
  --summary "转发摘要" \
  --sync-cover-from-body \
  --cover-file /path/to/local-cover.jpg \
  --save-draft \
  --report /tmp/wechat-publish-report.json
```

使用 URL 打开编辑器：

```bash
export OPENCLI_PROFILE="<your-opencli-profile>"
export WX_EDITOR_URL="https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2..."
node scripts/inject-to-wechat.mjs article_wechat.html --save-draft
```

只读检查已打开的草稿：

```bash
node scripts/inject-to-wechat.mjs article_wechat.html --reuse-current --verify-only
```

## 运行流程

```text
读取 data-wechat-root 内容根节点
→ 轮询等待正文编辑器
→ 预检并压缩超过 2MB 的远程图片
→ UTF-8 解码后一次性注入正文
→ 等待微信把图片转存到 mmbiz/qpic
→ 对失败图片压缩、换图床并重新注入
→ 独立同步可见标题、#title、摘要和作者
→ 优先把正文第一张图设为公众号封面
→ 正文选择失败时上传本地封面并完成裁剪确认
→ 校验图片、SVG、动画和正文
→ 可选保存草稿
→ 通过 appmsgid + 保存提示/历史记录确认保存
```

## 编辑器定位规则

| 区域 | 优先选择器 | 兜底策略 |
|---|---|---|
| 标题 | `.title-editor__input .ProseMirror` | `#title` |
| 正文 | `.rich_media_content .ProseMirror` | 排除标题后高度最大的可见 ProseMirror |
| 旧版正文 | `#ueditor_0 [contenteditable=true]` | 无 |

公众号页面同时存在标题和正文两个 ProseMirror。正文定位必须排除 `.title-editor__input`，禁止使用无约束的 `document.querySelector('.ProseMirror')`。

## 图片策略

- 默认检查远程图片的 `Content-Length`
- 超过 2MB 时下载到临时目录
- 使用 `sips` 转成 JPEG，最长边限制为 1920px，质量 85
- 通过 PicGo/PicList 上传优化图
- 优化图使用源 URL 的稳定哈希文件名，避免临时文件都叫 `source-wechat.jpg` 而被图床覆盖
- 不同源图返回同一个上传 URL 时立即停止，不继续替换正文；先检查 PicGo 命名策略，或用 `--no-optimize-images` 保留原图
- 微信转存失败时读取 `data-cacheurl`，强制优化后重试一次
- `mmbiz.qlogo.cn` 是转存过程中的过渡域名，`mmbiz.qpic.cn` 是常见稳定域名；两者和 `wx.qlogo.cn` 均视为微信已接管，不再误报为待转存
- 验收时排除 `.ProseMirror-separator`，只统计真实内容图片

可调参数：

```bash
--no-optimize-images
--max-image-bytes 2097152
--max-image-width 1920
--image-timeout 60000
```

## type=77 封面策略

type=77 编辑器的图片库缩略图可能使用 CSS `background-image`，正文候选不保证渲染成 `<img>`。注入器同时识别 `<img>`、图片库 item 和 CSS 背景，封面流程按下面的状态机执行：

```text
检测已有封面
→ 打开封面选择器
→ 尝试“从正文选择”并识别首个可用候选
→ 循环处理“下一步 / 确认 / 完成”
→ 若失败且提供 --cover-file：关闭残留弹窗
→ 打开图片库并通过 file input 上传本地文件
→ 按上传文件名选中素材
→ 完成裁剪确认
→ 验证封面区出现 img 或 background-image
```

`--cover-file` 可以单独使用，它会自动启用封面流程；如果页面已有封面，显式文件会替换旧封面。只传 `--sync-cover-from-body` 时才保留已有封面。推荐图片比例 2.35:1；macOS 上超过 180KB 会先通过 `sips` 转为最长边 1600px、质量 78 的 JPEG。页面注入兜底限制为 600KB，超过时报告会明确要求压缩后重试。

## 输出契约

`convert.mjs` 在文章根节点输出：

```html
<section data-wechat-root="article">...</section>
```

`wechat-styler` 注入器和 `post2wechat` 都优先读取该节点。旧 HTML 自动回退到 body 中第一个暖纸背景 section。

## 验收标准

注入成功需要同时满足：

- 标题字段和可见标题一致
- 摘要字段与输入一致
- SVG 与 `<animate>` 数量和 HTML 产物一致
- 内容图片数量一致
- 没有 `#imageStatus_root`
- 没有待转存的外部图片；qlogo/qpic 不计入待转存
- 保存模式下 URL 包含 `appmsgid`
- 新草稿出现新的 `appmsgid`，或已有草稿出现新的保存提示/历史记录；旧页面残留的“已保存”不算本次保存成功

报告中的 URL 和错误详情会自动隐藏 token。

## 故障恢复表

带 `--report` 运行时，成功与失败都会落盘 JSON。失败报告中的 `phase` 直接对应恢复动作：

| phase | 判断 | 直接恢复动作 |
|---|---|---|
| `cover` | 正文候选缺失、图片库缩略图结构变化或裁剪未确认 | 增加 `--cover-file <本地 2.35:1 图片>` 重跑；已有封面时先用 `--verify-only` 只读确认 |
| `inject-body` / `retry-images` / `verify-content` | 图片转存失败或仍有外链 | 查看 `live.failedUrls` / `live.pendingImages`；保留默认图片优化后重试，或替换报告列出的 URL |
| `save-draft` / `verify-saved-draft` | `appmsgid`、保存提示和历史记录证据不足 | 检查 URL 与版本历史，再运行 `--reuse-current --verify-only --report <path>`，避免重复写入 |
| `prepare-session` / `wait-editor` | opencli 未绑定到公众号编辑器 | 运行 `opencli doctor`，确认活动标签页是微信文章编辑器后重试 |

保存状态中的 `failedUrls`、`pendingImages` 和 `history` 都会强制归一化成数组。微信字段短暂缺失会继续轮询，不会再因读取 `.length` 终止任务。
