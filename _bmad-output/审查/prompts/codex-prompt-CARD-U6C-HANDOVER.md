# 代码审查请求 — CARD-U6C-HANDOVER（第十四批 T3 车道第 4/4 张）

## ① 背景

本卡收口前一张卡 CARD-G6-6/U6-C 合入时**登记未做**的四条行为面移交项。用户裁定 **D-10**：
这类行为面修复不得归入纯 pyright 的 U1/U2 两卡（那两卡明写「禁顺手修存量」），必须另立卡，
即本卡。用户裁定 **D-37**：U6-C 的三个产品口径（20:00「今晚」阈值 / 全板推迟退化恒等 /
同板 done+snooze 顺序）按现状确认**不改**，本卡禁碰——若你发现这三处有问题，请只登记不建议改。

四条移交面：

- **item ①** `scripts/daily_review_run.py` 的 `due_crossed` 缺判型。并列的 `wake_crossed`
  在 Codex round-1 MEDIUM-4 已补 `isinstance(..., str)`，`due_crossed` 留在原地。`st` 是外部
  state 文件，一个 `{"next_due_utc": 1}` 会让 `1 <= "…Z"` 抛 `TypeError`，而该分支的
  `except` 只接 `(json.JSONDecodeError, OSError)` ⇒ 整轮 runner 带 traceback 退出（连推送
  都不跑），而不是「当作没有到期点、照常重扫」。
- **item ②** overview 刷新路径的父子读钟跨午夜分日。`review_overview._run_pick` 不传 `--now`，
  生产器子进程自读墙钟；父读钟与子读钟之间隔着一次 `subprocess.run`（0.1–2s），当地午夜前后
  两次落在不同的一天 ⇒ 让位不发生。子进程 `daily_review_pick.py` **早已接受 `--now`**，本卡
  只把它接上，**不改生产器**（那是 T4 车道的地盘）。
- **item ③** `snoozeKey` / `doneKey` 的 NUL 反向碰撞定性 + 负控。正向（snoozeKey 输出撞
  doneKey 值域）已在 U6-C round-5 修掉。
- **item ④** Codex 此前点名的 3 颗既有定时哑弹，逐条定性「引信 / 可达性 / 修或登记」。

地盘：`scripts/daily_review_run.py` 本体原不在 T3 逐文件清单，主 session 裁定 **R-B14-4** 批准
扩入，**附加约束「只改 `due_crossed` 判型与父子墙钟传参段」**。

## ② 审查面（本卡 diff 的六个文件，逐 item 对应）

| 文件 | 对应 item | 本卡改了什么 |
|---|---|---|
| `scripts/daily_review_run.py` | ① | 单一 hunk `@@ -588 +588,8 @@`：`due_crossed` 加 `isinstance(_due, str)` 判型 + 理由注释 |
| `backend/tests/regression/test_daily_review_run.py` | ① | 新增参数化门 `test_u6c_wrong_typed_due_marker_does_not_abort_the_cache_gate`（7 档）+ 控制组 `..._control_group_still_reads_valid_iso` |
| `backend/app/api/v1/endpoints/review_overview.py` | ② | `_run_pick` 增 `now` 形参并在 argv 追加 `--now <isoformat>`；`_rebuild_projection` 取一次 `_display_now()` 存进 `wall_now` 并透传 |
| `backend/tests/unit/test_review_overview.py` | ②④ | 新增三层门 `test_u6c_refresh_passes_parent_now_so_child_agrees_on_the_day`；三颗哑弹逐条拆除 |
| `backend/app/api/v1/endpoints/review_app.py` | ③ | `doneKey` 上补反向方向定性注释（**无代码改动**，纯注释） |
| `backend/tests/unit/test_review_app.py` | ③ | 新增 JS 门「不相交是双向的: doneKey 输出恒含 NUL」 |

## ③ 四条 item 的判据与负控（全部已实跑，证据在 `_bmad-output/审查/evidence-u6c-handover/`）

先红后绿：

- item ① 先红：5 个承重档全部红在 `daily_review_run.py:588` 的 `TypeError`（int / bool / float /
  list / dict）；2 个空容器档因 `bool()` 为假而短路、修复前本来就不崩，测试用参数
  `crashes_before_fix` 如实标注它们是对照档而非承重档。修后 74 passed。
- item ② 先红：红在身份层「子进程 argv 里没有 --now」。修后 12 passed（含既有 g67r 族全绿）。

负控矩阵（8 条，每条跑前 `cp` 工作树副本、`trap ... EXIT` 无条件还原、跑后 `shasum -a 256`
两侧逐字节相同）：

| 编号 | 负控输入 | 期望 | 实测 |
|---|---|---|---|
| NC-1 | item ① 生产面还原成开工 commit 态 | 指定门红在 `:588` TypeError | ✅ 5 档全红 |
| NC-2 | item ② 生产面还原成开工 commit 态 **且**临时摘除门的身份层断言 | 行为层第三条断言必须**自己**红 | ✅ 红在「子 2026-09-17 vs 父 2026-09-16」 |
| NC-3 | 把 `wall_now = _display_now()` 换成 `datetime.now(_display_tz())` | 身份层红 | ✅ 红出「传的不是父侧那一刻」 |
| NC-4 | `doneKey` 分隔符 NUL → `"\|"` | **新**反向门红、**旧**正向门仍绿 | ✅ 新门 ✖ / 旧门 ✔ |
| NC-5 | `snoozeKey` 换成 round-5 被打回的 NUL 前缀实现 | 正向门红（卡文点名的验伪锚） | ✅ 两门都红 |
| NC-6 | item ② 生产面还原成开工 commit 态 | 哑弹② 红在「已完成的板必须让出榜首」 | ✅ |
| NC-7 | 哑弹① 的「未来」偏移改成过去（= 模拟真实时间越过 2099-01-01 那天） | 引信 assert 红 | ✅ `assert 2 == 0` |
| NC-8 | 哑弹③ 端点侧时钟推到次日（= 模拟取日后 GET 前跨当地午夜） | 引信 assert 红 | ✅ `assert 'stale' == 'ok'` |

NC-7 / NC-8 是**引信可达性**证明而非先红：那两颗哑弹的真实点火要等到 2099 / 某个午夜那一秒，
在今天跑不出红，所以改为证明「引信条件一旦成立，那条 assert 确实会红」。

其余裁判：`pyright app` = **0 errors**（开工基线同为 0 errors；warnings 82，与开工基线逐字相同
⇒ 本卡零新增）；`ruff check` / `ruff format --check` 对 6 个改动文件全绿（验伪锚①：文件集含
`scripts/daily_review_run.py`，计数 = 1；验伪锚②：F821 探针文件 rc=1 证 ruff 有牙）；
`tests/unit` 与 64 条红基线的 nodeid diff **空集**（验伪锚：塞一条假 nodeid 时 diff 吐出 `>` 行）；
地盘核 6 个文件全部 ⊆ 允许面，`daily_review_run.py` 只有一个 hunk。

## ④ 请重点审的风险

1. **item ① 的判型是否真覆盖「读法空间」而不是只覆盖那个 `1`**：`isinstance(_due, str)` 之后，
   `st` 里其余外部可控字段（`board_last_recommended` / `board_done` / `snoozed`）错型时会原样
   喂进 `picker.build_payload` / `picker.active_snoozed`——本卡「禁顺手修存量」，该面已如实登记
   不做。请判断这个边界划得对不对，以及本卡的判型本身有没有漏掉哪一类取值。
2. **item ② 传 `--now` 是否真合上了刷新那道缝**：残留的「写推迟/完成账那次请求 / 刷新那次请求 /
   之后 GET 渲染那次」三次独立读钟未消除（已登记）。另外 `_read_entry` 用的是
   `datetime.now(_display_tz())`（本文件的第二个时钟入口，属存量、本卡禁顺手修）。请判断
   「只合一道缝」这个范围声明是否诚实、有没有把某个**必须同批合上**的缝也说成了残留。
3. **item ② 的门有没有一层是死判据**：三层判据里若有一层在任何情形下都不会红，它就是装饰。
   NC-2 / NC-3 分别为行为层与身份层做了独立敏感性，请判断这两条负控输入是否真的只让**那一层**
   变红。
4. **item ③ 反向方向的定性是否成立**：本卡的主张是「两个值域不相交是两个半条件的合取，既有门
   只锁了 snoozeKey 那一半，另一半（doneKey 输出恒含 NUL）此前无门」。`doneKey` 自撞需库名或
   板名含 NUL，本卡判其经 POSIX 取名链不可达，并明说那是**取名链快照而非代码不变量**。请判断
   这个定性对不对，以及新门 ④ 那条 `assert.equal`（如实钉住自撞形态）是不是在锁住一个缺陷。
5. **item ④ 三条处置是否各自对**：哑弹②与 item ② 同根（钉父子同一刻），哑弹①改成相对今天的
   偏移，哑弹③把端点侧时钟钉到与夹具同一刻。请判断有没有哪一条的「修」其实改变了该用例原本
   要验的语义。
6. **pyright 保持 0 / 地盘约束**：`review_overview.py` 与 `review_app.py` 在 `backend/app/**`，
   必须 0 errors；`scripts/daily_review_run.py` 的 diff 必须只落在 `due_crossed` 判型段（R-B14-4
   附加约束）。请核对这两条。

## ⑤ 最小读取面

只需要读下面这些，**不要求**读别的文件：

- `scripts/daily_review_run.py` — `ensure_payload` 内 `due_crossed` / `wake_crossed` 两行及其注释
  （`grep -nF 'due_crossed =' scripts/daily_review_run.py` 定位）
- `backend/app/api/v1/endpoints/review_overview.py` — `_run_pick`、`_rebuild_projection` 内
  `wall_now` 那一段、`_display_now` / `_display_today` 两个函数定义
- `backend/app/api/v1/endpoints/review_app.py` — `doneKey` / `snoozeKey` 两个 JS 函数及其注释
- `backend/tests/regression/test_daily_review_run.py` — 两个 `test_u6c_*` 用例
- `backend/tests/unit/test_review_overview.py` — `test_u6c_refresh_passes_parent_now_*`、
  `test_g67r_refresh_passes_state_and_done_board_yields_top`、
  `test_refresh_rebuilds_projection_and_response_matches_disk`、
  `test_buckets_gate_accepts_real_producer_payload`
- `backend/tests/unit/test_review_app.py` — 「不相交是双向的」与「推迟键与完成键不同族」两条 JS 门

请按 BLOCKER / HIGH / MEDIUM / LOW 分级给出结论，每条附精确的 file:line 与你的判断依据。
