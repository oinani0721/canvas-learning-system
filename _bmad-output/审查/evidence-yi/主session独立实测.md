# 乙案 · 主 session 独立实测（与 workflow 结论对照用）

> 2026-09-05 · 全部只读；live vault 只 stat 不写；未连 7691。
> 目的：workflow 的结论要能被独立复现才采信（上一轮乙-2 设计时我犯过「只查一条路径就下结论」的错）。

## 1. 脏检测成本 —— 可忽略

`scripts/daily_review_run.py::_nodes_max_mtime` 的实现是
`for p in (vault/"节点").glob("*.md"): p.stat().st_mtime` + 目录 mtime。

在 live vault 上原样跑 20 次取最快：

| 项 | 实测 |
|---|---|
| 节点数 | **10** |
| 一次全扫 | **0.030 ms** |
| 最忙一小时（720 次 GET 各扫一遍） | **0.022 s** CPU |

⇒ 当前规模下**成本可忽略**。万节点线性外推 ≈ 30ms/次、21.6s/h ——
仍可接受但不再可忽略；G6-3 验收单已登记「未测万节点」，此处沿用该登记。

⚠ docstring 自陈的覆盖面缺口（原文）：
「文件 mtime 抓原地更新 (quiz 写 fsrs_due 不动目录), 目录 mtime 抓增删改名；
**保 mtime 的还原类操作 (rsync -a / Time Machine) 不在本判据覆盖面内**」。
⇒ 这条判据对「答题写入」是可靠的（正是本卡要抓的信号），对「整库还原」会漏。

## 2. 去抖窗口 —— 已存在，且天然限流

`review_overview.py:1194 _REFRESH_TTL_SECONDS = 10.0`；
`:1465` 「同一库 TTL 窗口内只有第一次真起子进程, 其余直接读盘返回」。

轮询最快 5 秒（`review_app.py:159 POLL_MIN_MS = 5000`）
⇒ **每两次轮询才可能触发一次重建**，重建频率天然被压在 ≤6 次/分钟/库。

## 3. 第④条断言锁的到底是什么 —— 锁的是**前端**

`tests/unit/test_review_app.py::test_js_poll_contract_wiring_g63` 第④条的断言原文是
`assert.equal(b.calls.post, 0, ...)` —— `b.calls.post` 是**沙箱 fetch 收到的 POST 次数**，
即「前端在轮询路径上不发 POST」。

⇒ **后端在 GET 处理里自己重建，不违反这条断言的字面。**

⚠ 但这不等于合规：默认裁决② 的**意图**是「不要让自动轮询造成写操作」。
读侧惰性重建绕过了字面却可能违反意图 —— 这一点已交 workflow 的
「纪律与地盘 lens」专门证伪，不由我自己拍板。

## 4. 重建本身的成本（引用 G6-3 实测）

`evidence-g63/e2e-timing.md`：触发后可见耗时 **0.060 / 0.075 / 0.073 秒**（3 轮，含一次真实重建）。
⇒ 若在 GET 里同步重建，那一次请求变慢约 70ms；受 §2 的 10 秒去抖限制，
不会每次 GET 都付这个代价。

## 5. 地盘（读卡文实测）

| 面 | 归属 | 本车道能改吗 |
|---|---|---|
| `review_overview.py` / `review_app.py` / `daily_review_pick.py` | **Z1（本车道）** | ✅ |
| `quiz-answer/SKILL.md`、`fsrs_bridge.py`、`learning_event_log.py` | **Z2（CARD-G3-3 正在改）** | ❌ 撞车 |
| `daily_review_run.py` 主流程、`launchd/*.plist` | A3（第十一批未排卡） | ❌ 需主 session 裁 |

⇒ 「读侧惰性重建」若成立，是**唯一完全落在本车道面内**的路线。
