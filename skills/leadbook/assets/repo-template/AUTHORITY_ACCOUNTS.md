# Authority Accounts

本文件用于确认“这本书所属领域里，最值得系统抓取的公众号/作者/机构”。先选对来源，再抓文章。

| ID | Domain | Account / Author | Type | Why It Matters | URL | Discovery Method | Recency Window | Fetch Plan | Output Path | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A001 | 待填写 | 待填写 | expert / institution / media / operator / skeptic | 待填写 | 待填写 | web / wechat-article-search / known expert | 365d | discover + harvest | research/wxmp/ | candidate | 待填写 |

## Selection Rules

- 先确认领域，再确认这个领域里最值得听的 5-8 个来源。
- 不只选“名气最大的人”，还要覆盖专家、机构、媒体、实践者和反方声音。
- 商业、运营、平台、AI 落地等变化快的主题，默认只抓最近 365 天。
- 如果是经典理论或长期方法论，可以补充更早文章，但必须标记为 `evergreen`，不能当作当前市场事实。
- 公众号账号搜索只解决“找号”，不是全网文章关键词搜索。关键词筛选在导出到本地之后完成。

## Recommended Mix

- S-tier：领域中有原创框架、长期影响力、被广泛引用的人或机构。
- A-tier：持续输出高质量商业判断、案例和行业观察的公众号。
- B-tier：一线操盘者、公司官方号、垂直媒体，适合补案例和实操细节。
- Counter：反方、质疑者、失败案例来源，防止整本书只剩单边叙事。

## WXMP Workflow

1. 用通用 Web 搜索“主题 + 公众号 / 专家 / 白皮书 / 年度趋势 / 案例”。
2. 用 `wechat-article-search` 搜索候选文章与账号，确认账号身份。
3. 用 `wxmp-article-harvester` 对已确认账号归档目标时间段文章。
3. 对选定账号抓取最近 365 天文章。
4. 导出 Markdown / JSON / CSV 到 `research/wxmp/<account>/`。
5. 用本地关键词筛选文章：核心词、同义词、反对词、购买词、场景词。
6. 只把被实际引用的事实写入 `CLAIM_LEDGER.md`；把案例和场景写入 `CASE_LIBRARY.md`。

## Candidate Quality Checklist

- [ ] 这个账号和主题强相关。
- [ ] 这个账号在过去一年仍有稳定输出。
- [ ] 这个账号有原创判断、案例或一手观察，而不是只搬运热点。
- [ ] 这个账号的立场和商业利益已被记录。
- [ ] 这批账号合在一起覆盖了不同视角，而不是同一种观点的重复。
