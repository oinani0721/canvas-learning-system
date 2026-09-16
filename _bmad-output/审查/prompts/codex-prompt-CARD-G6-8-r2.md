# CARD-G6-8 独立审查请求（round-2）

## 〇 判定口径

用户裁定 D-15：有代码改动的卡多轮审查，直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0。
**不要用「既有 / BASE 已有」豁免任何问题**——只要落在下列地盘文件内就照报：

```
backend/scripts/g68_five_view_contract.py
backend/tests/regression/test_g68_five_view_contract.py
_bmad-output/审查/evidence-g68/scripts/g68_negctl.py
.github/workflows/test.yml（只允许 +1 行）
```

本卡**未改**任何生产代码（review_overview / review_app / 两个 skill 脚本 /
daily_review_pick 全部零改动）——契约没有暴露它们的分歧。

### 最小读取面（写死，勿扩）

1. `git diff d6ecd4edf8a24cbcfc3a5420d4257abf6932558f 6e2ee891 -- . ':(exclude)_bmad-output'` —— 本轮改动
2. `backend/scripts/g68_five_view_contract.py` 全文
3. `backend/tests/regression/test_g68_five_view_contract.py` 全文
4. `_bmad-output/审查/evidence-g68/scripts/g68_negctl.py` —— 负控实跑的就是这一份
5. `review_overview.py` 的 `_collect` / `_summarize` / `_gate_buckets` / `_display_*` 段（只读对照）
6. `review_app.py:1-70`、`daily_review_pick.py:29-96,:971-1160`、两 skill 脚本的 `main` / `parse_now`（只读对照）

## 一 你 r1 的七条，逐条处置

**修 7 条，0 条驳回。** 你那句「原版 13/13 通过，四组负控副本也各 13/13 通过」是本轮
整改的起点——门当轮确实对那四种改动毫无反应。

| 条目 | 处置 | 复现结果与修法 |
|---|---|---|
| **H1** 声明产出方仍可静默退出比较 | 修 | 成立。缺值改为 `MISSING`（参与比对并判红）；`check_producers_declaration` 新增「声明产出方交出 `NOT_PRODUCED` ⇒ 当场抛」。 |
| **H2** 日期豁免无条件覆盖整格 | 修 | 成立，且**比你的措辞更严重**：不只 `2099-01-01`，连 `MISSING` 也被豁免。改为**谓词**豁免——只认「恰好等于同一时刻在固定 +08:00 下的本地日」；谓词自身抛异常也按未登记处理。 |
| **H3** AST 门未检查字典字段读取 | 修 | 成立。你那句「现有负控依赖局部变量恰好命名为 `fsrs_due`」**属实**——原负控是靠巧合红的。补认两种形态：落在下标位置的字符串、落在 `get`/`pop`/`setdefault` 首参位置的字符串。 |
| **H4** overview 日期列未绑定实际响应 | 修 | 成立。拆两列：`display_day` 取响应顶层 `generated_at` 的日期部分，**新增 `projection_day`** 取响应复述的 `projection.date`。 |
| **M5** 声明与实现同步缩减时对账仍通过 | 修 | 成立。加「每列至少两个声明产出方，否则当场抛」+ 把 `FIELD_PRODUCERS` 形状钉进测试。 |
| **M6** snooze/done 消费结果未被观察 | 修（部分） | 成立。新增 `check_ranked_yield_partition` 观察「让位板整体靠后」。**如实声明**：不覆盖 done/snooze 之间的先后（U6-C 登记、D-37 不改）——与你那句「不构成要求修改 D-37 的依据」一致。 |
| **M7** 负控文本锚未绑定实际失败断言 | 修 | 成立。锚的搜索面缩到「该 nodeid 自己的失败块」内（`failure_block()`）。 |

**你的五组对照输入已全部做成常驻负控段**：`R1H1_NOTI_ABSENT` / `R1H2_INBOX_ABSURD_DAY` /
`R1H3_DICT_DUE_READ` / `R1M5_SHRINK_DECLARATION` / `R1H4_RESPONSE_DATE`，
15 段 15 合判据、rc=0。

**本轮整改自己又抓出两条**（一并交你复核）：
1. `RO_DAY` 的红点随 H4 修复**迁移**——`_display_today` 不再决定 `display_day`，改它显形在
   **done** 列。已改名 `RO_DONE_DAY` 换锚，另补 `RO_GENERATED_AT` 专守 `display_day`。
2. 新加的声明对账**误报**：把「这块板该面根本没有」当成「该面交出了 `NOT_PRODUCED`」而抛，
   盖住真正的 `MISSING` 信号（负控 `RO_BOARD_IDENTITY` 实测 rc=2 抓到）。已改为只看该面
   **真的交出来的**那些值。

## 二 按重要性排序的问题

0. **矩阵是否仍有「某一面改了却不红」的门未覆盖的路径**？请给对照输入。
   本轮新增了 `MISSING` / 谓词豁免 / `projection_day` / 让位分区四处，重点看它们的交叉格。
1. 谓词豁免是否可被「让 inbox 的值恰好等于固定 +08:00 当日、但它其实是从别处算出来的」
   这类输入越过？谓词的粒度是不是仍太粗？
2. `check_producers_declaration` 的两个方向（声明却零产出 / 产出却未声明 / 交出哨兵）
   是否仍存在「声明与实现各说各话」的缝？
3. `projection_day` 与 `display_day` 拆列之后，是否出现了新的**恒等**列
   （某列的两个产出方按实现必然相等 ⇒ 该列是恒真判据）？
4. `check_ranked_yield_partition` 的退化条款（无让位板 / 全部让位时直接返回）是否
   让它在本卡 fixture 之外的常见输入下变成恒真？
5. `failure_block()` 的边界切法（下一个 `___ test ___` 或 `=== short test summary ===`）
   是否会在某些 pytest 输出形态下切错，导致锚判定失真？
6. review_app 的 AST 门补了两种形态之后，还有哪些**未被拦下的**读法（请给对照输入）？
7. 确定性：计算期把 stdout 换成缓冲区——这个做法是否会吞掉某些本该让人看见的失败信息？

## 三 输出格式与边界

- BLOCKER / HIGH / MEDIUM / LOW + `file:line` + 一句复现思路
- 边界：只读、不连库、不跑完整复习链、不评 picker / display_tz 本体设计
- 措辞：一律用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」
