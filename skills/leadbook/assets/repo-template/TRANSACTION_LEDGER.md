# Transaction Ledger

记录交易层信号：市场如何定价、如何承诺结果、如何说明交付边界、如何处理购买异议。

| ID | Source Type | Seller | Offer | Price Or Commitment | Promise | Boundary | Objection | URL | Confidence | Chapter Use | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T001 | pricing-page / offer-page / signup-page / delivery-page / objection | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | low / medium / high | 待填写 | 待填写 |

## 使用规则

- 交易层只证明“市场上有人这样承诺和销售”，不能单独证明交付质量。
- `Promise` 写对方承诺了什么结果，`Boundary` 写对方不承诺什么或如何限制风险。
- `Objection` 写购买前异议、FAQ、退款说明、评论质疑或用户顾虑。
- `URL` 必须指向具体产品、定价、报名、交付或 FAQ 页面；网站首页只有在该页本身包含被引用信息时才有效。
- `publish-ready` 默认至少需要 3 条有效交易信号；少数主题不需要时，必须显式说明。
