# Execution checkpoints

完整商业书通常跨研究、写作、构建和视觉检查多个长阶段。把可恢复状态写进项目文件，不依赖单个模型回合或最终聊天消息。

## Phase order

固定顺序：

1. `scaffold`
2. `brief`
3. `research`
4. `outline`
5. `writing`
6. `build`
7. `visual-qa`
8. `review-ready`
9. `publish-ready`（可选）

完成一个阶段后运行：

```bash
python3 scripts/leadbook-stage.py mark research --note "公开 Web 证据完成"
python3 scripts/leadbook-stage.py next
```

脚本会阻止跳过前置阶段，并对关键文件、URL 数、构建产物、视觉审计状态和 gate receipt 做轻量验证。`blocked` 只记录真实外部阻塞；普通质量问题保持 `in-progress` 并继续修复。

## Durable execution

- 六章以上或要求 PDF 时，至少在 research、outline、writing、build、visual-qa 后落检查点。
- 每章写作后更新章节 refs、cases、`BOOK_SUMMARY.md` 和 `book-state.yaml`；阶段检查点不能代替章节状态。
- 会话提前结束时先运行 `leadbook-stage.py status` 和 `next`，再检查当前文件。不要重新脚手架、重新抓取或覆盖已完成章节。
- 最终聊天报告不是完成事实源。`dist/qa/gates/review-ready.json` 或 `publish-ready.json` 的有效 receipt 才能升级成熟度。

## Gate transaction

运行：

```bash
python3 scripts/check-leadbook.py --target review-ready --update-state dist/book.md
```

检查失败时，状态保持或回退到较低成熟度，并写失败 receipt。检查成功时，脚本原子更新 `book-state.yaml`，写入当前产物摘要。之后任何书稿、HTML、PDF、视觉审计或参考资料变化都会让 receipt 失效，必须重新构建和检查。
