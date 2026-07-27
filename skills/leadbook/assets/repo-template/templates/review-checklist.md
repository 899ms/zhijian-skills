# Review Checklist

- [ ] 本章有明确结论。
- [ ] 本章有具体读者问题。
- [ ] 本章有证据或来源：事实、需求、行为、交易、观点或自有案例。
- [ ] 本章有案例或反例。
- [ ] 本章有行动产出：判断、工具、模板、清单、自测或动作。
- [ ] 本章至少有一个符合 `voice_profile` 的作者判断。
- [ ] 本章承担了明确章节任务，不只是重复上一章骨架。
- [ ] 这章真的需要放进正文的模板、自测或填写任务，才放在正文；能进 `dist/worksheets/` 的内容没有抢主结构。
- [ ] 本章没有“需求侧样本 / 行为层样本 / 交易层样本 / 公众号元数据 / 线索 / 文章池 / 适合放在”等后台词。
- [ ] 证据已经写成读者能理解的具体来源和具体场景。
- [ ] C 级需求材料没有被包装成完整案例。
- [ ] 如本章需要图，已登记 `VISUAL_PLAN.md`，图有路径和 caption。
- [ ] 正文解释性图优先使用 Kami SVG，没有用氛围图替代结构图。
- [ ] 本章引用的公众号材料来自 `AUTHORITY_ACCOUNTS.md` 中已确认的来源。
- [ ] 商业/平台/AI/运营类判断优先使用最近 365 天内的公众号材料；更早材料已标记为 evergreen / historical。
- [ ] 关键事实进入 `CLAIM_LEDGER.md`。
- [ ] 高置信事实有 L1-fact 来源或交叉验证。
- [ ] 本章 `refs.md` 已回填，不是空模板；若 `book-state.yaml` 里本章 `refs > 0`，记录数与实际一致。
- [ ] 本章 `cases.md` 已回填，不是空模板；若 `book-state.yaml` 里本章 `cases > 0`，记录数与实际一致。
- [ ] 小红书材料只作为需求侧证据，没有被写成行业事实。
- [ ] 行为层材料只作为公开组织动作，没有被写成结果有效性证明。
- [ ] 交易层材料只作为市场承诺和购买异议，没有被写成交付质量证明。
- [ ] Nowledge/Obsidian 没有被当作高权重信息源；如使用，只作为特别贴合的自有案例或场景。
- [ ] 本章摘要已写入 `BOOK_SUMMARY.md`。
- [ ] `book-state.yaml` 已更新。
- [ ] 正文没有硬 CTA。

## 整书状态检查

- [ ] `python3 scripts/check-leadbook.py --target review-ready dist/book.md` 已通过，主书才可标 `review-ready`。
- [ ] 需要公开分发时，`python3 scripts/check-leadbook.py --target publish-ready dist/book.md` 已通过，整包才可标 `publish-ready`。
- [ ] 若 `wxmp_pack` 仍为 `partial`，最终汇报明确写成 `review-ready`，不写成 `publish-ready`。
- [ ] 若行为层或交易层未闭环，最终汇报明确说明，并使用显式豁免参数，不默认写成 `publish-ready`。
- [ ] `outputs.references=true` 和 `quality.reference_page=true` 只在读者参考页真实存在且不单薄时才标记。
- [ ] H1 后有真正的开场，不是直接进入第 1 章任务单。
- [ ] 全书没有机械重复同一组二级标题；读者能感到章节在推进，而不是在重复交付任务单。
- [ ] `dist/qa/pdf-visual-audit.md` 已完成，无 open 问题。
- [ ] `dist/worksheets/`、`distribution-note.md`、`private-domain-pack.md` 未完成时，不把这本书称为“完整引流包”。
