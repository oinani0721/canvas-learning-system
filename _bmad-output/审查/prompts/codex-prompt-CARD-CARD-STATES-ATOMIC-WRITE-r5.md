# 独立复核 round-5（末轮）：CARD-CARD-STATES-ATOMIC-WRITE（BATCH-2026-09-18-第十五批 / 车道 P4）

## ① 背景与最小读取面

r1 B0/H1/M3/L1 → r2 B0/H1/M5/L0 → r3 B0/H1/M3/L1 → **r4 B0/H0/M4/L3**。
r4 已判 HIGH=0。本轮**只改了测试与 spec 文字，`backend/app/services/review_service.py` 与 r4 所审那份逐字节相同**
（`git diff 5d69728a1c7964e9f8e09f0c908b59e5fca7ac2a 28d484b91259f8172ca4ac885e2bc3188fb1ec19 -- backend/app/services/review_service.py` 为空，请自行核）。
本轮是本卡**末轮**（上限 5）；请重点判断「r4 的 MEDIUM/LOW 是否真被关掉」与「本轮改动有没有
引入新问题」，并把仍成立的项一次列全。

只读：

1. 相对 r4 的增量：`git --no-pager diff --no-color 5d69728a1c7964e9f8e09f0c908b59e5fca7ac2a 28d484b91259f8172ca4ac885e2bc3188fb1ec19 -- . ':(exclude)_bmad-output'`
2. 全量：`git --no-pager diff --no-color 9c4e7e82 28d484b91259f8172ca4ac885e2bc3188fb1ec19 -- . ':(exclude)_bmad-output'`（恰 3 文件）
3. `backend/tests/regression/test_g3_7_truth_source.py`：`:685` 到文件末尾（16 个 `concept_identity` 门）
4. `openspec/specs/concept-identity/spec.md` 改后全文（7 个 Scenario）
5. `backend/app/services/review_service.py`：`:655-745`（helper 与三个模块级量）、`:1050-1065`（派发段）
6. 存档（`_bmad-output/审查/evidence-card-states-atomic/`）：
   - `negctl-r5-{1,2,4,5,6,7,8,9,10,11}-*` —— **十段**负控输入（含 `-sha-before/-after`、`-mutant-diff-`）
   - `redbind-r5-*.txt` —— 对照输入（整体换回 `9c4e7e82`）
   - `suites-r5-*.txt` / `dir-regression-r5-*.txt` / `unit-r5-*.txt` / `unit-r5b-*.txt` —— 绑本 HEAD，
     首部含**完整 argv** 与跑前 sha256，末尾含收工时刻与收工 sha256。
     ⚠️ `unit-r5-*.txt` 那次出现一条**不在红基线**的 `>`：
     `tests/unit/test_deploy_vault_sh.py::test_preflight_accepts_leading_zero_cap`，
     失败正文是「npm run build 超时（墙钟上限 5s）」。自述归因：机器高负载导致的假红
     （同批 `tests/regression` 该次耗时 981s，其余两次 510s/606s；单跑该文件 `-k leading_zero`
     = 2 passed；空载复测 `unit-r5b-*.txt` 回到 32 红、diff 只有 `<`）。**请独立核这个归因**。
   - `ast-r5-*.txt` / `territory-ruff-r5-*.txt` / `pyright-r5-*.txt` —— 每条判据都写了**字面 argv**（r4 LOW-7 整改）
   - `probe-cancel-thread-*.txt`；⛔ `unit-r2-*.txt` 首部标注作废，勿采信
   - ⛔ **不要读** `independent-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md` 与
     `codex-review-CARD-CARD-STATES-ATOMIC-WRITE-r5.md`：前者是本轮送审失败期间由另一个
     agent 出的替代报告，后者是「未取得」记录。读它们会污染你这一轮的独立性。
     其余 `codex-review-*{,-r2,-r3,-r4}.md` 可读（那是你自己前四轮的原文）。

## ② 本轮整改自述（请独立核对）

1. **r4 MEDIUM-2（并发门会把合法的过期丢弃判成失败）已修**：观测点从「tmp 被写模式 open」
   改为**锁本身**——用 `_TrackingLock` 包住真锁记录持有区间，`entered == 4` 成为确定性存活锚
   （无论是否被丢弃，每次调用都会进出锁）。已连跑 12 次同组四门，0 次失败。
   副产物：r4 指出的「负控 1 也会红并发门」这层耦合**已解开**——本轮 `negctl-r5-1` 是
   4 failed，并发门不在其中。
2. **r4 MEDIUM-1 三个子项已由行为门覆盖**（不再只靠 AST 脚本）：
   - 新门 `…s7_seq_is_allocated_before_dispatch` 从**生产调用方**观测 `asyncio.to_thread`，
     断言被派发的是 helper、且 seq 是**已算好的 int 实参**、且连续两次严格递增。
     负控 `negctl-r5-9`（取号挪进 lambda）与 `-10`（换同步直调）各让它且只让它变红。
   - 新门 `…s7_failed_publish_does_not_advance_the_watermark`：让较大 seq 的发布在
     `os.replace` 失败，随后一个**更小**且从未发布过的 seq 必须仍能落盘。
     负控 `negctl-r5-11`（把记账挪到 `os.replace` 之前）让它且只让它变红。
3. **r4 LOW-5（spec 把「尝试清理」写成了「保证无残留」）已改**：Requirement 现在明说
   「保证的是每条失败路径都**尝试**移除，不是承诺 `.json.tmp` 永远不会在清理自身失败时存活」；
   Scenario 6 的那条 AND 也补了同样的例外。
4. **r4 LOW-7（存档缺字面 argv）已补**：`ast-r5` / `territory-ruff-r5` / `pyright-r5` 每条判据
   前都写了可逐字复跑的命令。
5. **r4 MEDIUM-3（线程池饥饿）与 MEDIUM-4（锁死 spec 文字失真）未改，已登记**：前者不改线程池
   配置（不在地盘）；后者那句话落在卡文规定的**一字不动**区间，本卡无权改动。
6. **r4 指出的多实例缺口（两个 ReviewService 各持独立容器）**：已写进验收单「本卡未证明什么」，
   本卡不改（基线既有，生产入口是 singleton）。

## ③ 请按重要性回答

0. 本轮的测试改动有没有**削弱**任何一条门？特别是：`_TrackingLock` 包在真锁外面，
   `__enter__` 先取真锁再记账、`__exit__` 先记账再放真锁——这个顺序会不会让重叠检测
   漏判或误判？`entered == 4` 是不是真的确定性？
1. 两条新门（`…before_dispatch` / `…watermark`）有没有**门未覆盖的路径**？
   例如 `…before_dispatch` 只看 `args[2]` 是不是 int，有没有变异体能让它绿而行为已坏？
2. 十段负控输入是否各只拆一层？还有没有变异体能让 16 条全绿？
3. spec 改后的 Requirement 有没有仍然超出实现的承诺？（r4 你指出的 LOW-5 是否已闭合？）
4. 16 条门在**对照输入**（整体换回 `9c4e7e82`）下的分类：哪些是行为红、哪些只是接口错误？
   接口错误的那几条是否应当被视为「没有绑住行为」？
5. r4 的 MEDIUM-1/2 与 LOW-5/7 是否确实关闭？仍成立的是哪几条？
6. 综合判断：以`BLOCKER=0 且 HIGH=0`为标准，本卡现在是否可以收官？若不行，请明确指出
   **必须**在本卡内解决的那一条（而不是可登记的）。

## ④ 输出格式

逐条列 `BLOCKER / HIGH / MEDIUM / LOW`，每条给 `file:line` + 一句复现思路。
措辞统一用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」。
最后给一行：`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## ⑤ 边界

只读，不写任何文件；不连数据库；不评 `next_review` 迁移（P4-B）；不评
`backend/app/utils/atomic_io.py` 该怎么修；不评 `tests/unit` 的隔离问题；不评
`backend/app/models/**`；不评那段被卡文锁死的 spec 文字**该不该**改；不评线程池/worker
配置该怎么改；不评多实例一致性该怎么修（均已登记，不在本卡地盘）。
