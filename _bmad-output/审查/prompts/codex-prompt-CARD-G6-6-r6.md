# 对抗性代码审查 — CARD-G6-6 round-6（U6-C 时间炸弹修法）

你是独立审查者。只读，不改任何文件，不连任何数据库。

---

## 一 本轮是什么

前五轮（round-1 ~ round-5）审的是「板级 snooze 两档」这张卡的实现，末轮 round-5 判
BLOCKER 0 / HIGH 0 / MEDIUM 0 + 1 LOW（已修）。卡在 2026-09-09 收官。

**2026-09-11 该卡的一条门自己红了，代码一个字没改**：

```
tests/unit/test_review_overview.py::test_g66_end_to_end_snooze_yields_top_slot_in_the_real_projection
E   AssertionError: 被推迟的板必须让出榜首
E   assert 'CS 61B' != 'CS 61B'
```

本轮只审**这一次修法**。审查面：

```
git diff 8e517721da08622c8dad8e39db6da9eb0d5f9963 9fb119b97ebc4b3bd942f55ff7f5017962c13932 -- . ':(exclude)_bmad-output'
```

= 单文件 `backend/tests/unit/test_review_overview.py`，+105 / -1。

请重点读：
- 新增 `_pin_child_now` 与 `_assert_child_now_pinned`（紧跟既有 `_pin_now` 之后）
- 既有 `_pin_now`（未改）、既有 `_spy_subprocess_run`（未改，同一条打补丁的形态）
- 改动后的 `test_g66_end_to_end_snooze_yields_top_slot_in_the_real_projection`
- 新增 `test_g66_e2e_snooze_verdict_is_clock_independent`（3 参数）
- 生产侧（**本轮零改动**，但判定链在这里，需要你核）：
  - `scripts/daily_review_pick.py`：`main()` 的 `--now` 分支、`active_snoozed`、`parse_snooze_until`
  - `backend/app/api/v1/endpoints/review_overview.py`：`_display_now`、`_snooze_until`、
    `_run_pick`、`_child_env`、`_PICK_REL`、`_rebuild_projection`

---

## 二 作者自述（请独立核对，不要采信）

1. **根因**：`_pin_now` 只打 `review_overview._display_now` 这个进程内入口；而 refresh 走
   `subprocess` 起 `daily_review_pick.py`，子进程用 `datetime.now(timezone.utc)` 自己读钟。
   端点被钉在 `2026-09-09T10:00` ⇒ 写出的 `until = 2026-09-09T20:00+08:00` 是一个**绝对
   过去时刻**，真实墙钟越过它之后子进程判它不活跃 ⇒ 让位不发生。该门只在
   `real-now < 2026-09-09T20:00+08:00` 期间绿。

2. **这是测试缺陷不是生产缺陷**：生产里端点与生产器读的是同一个真实墙钟（相差一次
   spawn 的毫秒级），`until` 恒在写下之后 ⇒ 「落盘那一刻就已过期」这个状态生产不可达。
   是单侧钉钟把它造了出来。

3. **修法**：`_pin_child_now` 包住 `mod.subprocess.run`，对 argv 里含生产器脚本名的那次
   调用追加 `--now <同一个 pinned 的 isoformat>`（生产器既有的只读旗标，`main()` 已支持）。
   脚本名取自生产常量 `mod._PICK_REL[-1]`，不手抄字面量。

4. **刻意不改生产**：没有把 `--now` 接进 `_run_pick`。理由两条——
   (a) `payload["generated_at"]` 会从「子进程真正生成的那一刻」变成「父进程读钟那一刻」；
   (b) launchd runner（`daily_review_run.py`）那条调用路**不**传 `--now`，只改 Web 这一路
   会让两条生成路径不同源。

5. **前提断言**：`_assert_child_now_pinned` 断言 argv 里真的有 `--now` 且值就是那一刻。
   少了它，`_pin_child_now` 哪天匹配不上脚本名就会**静默**退回单侧钉钟，门会继续绿到下
   一次墙钟越线。

6. **常驻门**：`test_g66_e2e_snooze_verdict_is_clock_independent` 在 2020 / 2026 / 2099 三个
   pinned 值上跑同一条核心性质（让位 + 不除名），把「判定与真实墙钟无关」变成常驻不变量。
   夹具 `fsrs_due` 取 2019 是为了三个参照时刻上节点都已到期。

7. **变异负控**（`_bmad-output/审查/evidence-g66/mutation-u6c-timebomb-final-20260911T083817.txt`，
   串行、跑后立即还原、跑前跑后两文件 sha 逐字节相同、rc=0）：
   | 变异 | 预期红在 | 实测 |
   |---|---|---|
   | `_pin_child_now` 不再追加 `--now` | 「子进程 argv 里没有 --now (钉子没落上)」 | 4 failed，命中 |
   | `active_snoozed` 恒返回 `{}` | 「被推迟的板必须让出榜首」 | 4 failed，命中 |
   | `active_snoozed` 只在 `now.year == 2026` 判活跃 | 恰好 2020 / 2099 两条红、2026 绿 | 2 failed / 2 passed，命中 |

8. **同族哑弹扫描**（`timebomb-class-sweep-20260911T083447.txt`）：判据
   `_pin_now(端点钉钟) ∧ _REFRESH_URL(起子进程) ∧ ¬_pin_child_now(子进程未钉)`
   在四个卡文件上 = **0 条**；松掉第三项的验伪锚命中 2 条，说明判据不是恒空扫描。

9. **门面与回归**：四文件 365 passed（原 362 + 本轮 3）；`ruff check` / `ruff format --check`
   rc=0；`pyright` 在该测试文件上的诊断**多重集**与 HEAD 版逐项相同（零新增，
   `reportUnusedVariable` 8 = 8）；pyright 的门面按 D-16 甲是 `backend/app/*.py`，本轮零触碰。

10. **现网零触碰**：`backups/daily-review.canvas-vault.state.json` 与
    `canvas-vault/outputs/今日复习.json` 的 mtime 均为 2026-09-10，早于本次作业开始
    （2026-09-11 08:21 CST）。

---

## 三 请按重要性排序回答的问题

1. **修法方向对不对**。自述 2 说「生产不可达」——`_write_board_snooze` 的调用链上，有没有
   任何一条真实路径能让落盘的 `until` 在生产器读到它时已经过期（例如去抖 / in_progress /
   重试 / 队列延迟 / 子进程启动耗时异常）？如果存在，那就不只是测试问题，请点名那条路径。

2. **`--now` 该不该接进生产**。自述 4 给了两条不接的理由。请核这两条是否成立，以及**反方向**
   的代价有没有被低估：父进程 `_display_now()` 与子进程 `datetime.now()` 是两次独立读钟，
   在**当地午夜前后**它们可能落在不同的一天。`payload["date"]`、`board_done` 的日历键匹配
   （`_board_done_today` 用父进程的今天，生产器用它自己的今天）会不会因此不一致？若会，
   这是既有形态还是本卡引入的？（作者的判断：既有，属 G6-7-R 的面，已登记为移交项而不是
   在本轮顺手修。请核这个归属判断。）

3. **`_pin_child_now` 的打补丁面**。它 `monkeypatch.setattr(mod.subprocess, "run", ...)`，
   而 `mod.subprocess` 就是 stdlib 的 `subprocess` 模块对象 ⇒ 补丁在该用例期间是**进程级**的。
   `_spy_subprocess_run` 早就是同一形态。请核：在这两条用例的执行窗口里，还有没有别的
   调用方会走 `subprocess.run`（从而被意外追加 `--now` 或被记账）？`fork`/`Popen`/
   `check_output` 等别的入口会不会绕过这层包装而让门失真？

3b. 包装里的匹配条件是 `any(str(a).endswith(basename) for a in argv)`。请核这个匹配会不会
    **误命中**（例如 argv 里某个参数恰好以同名结尾）或**漏命中**（例如脚本以 `-m` 模块形式
    或经软链以别名被调起）。漏命中时 `_assert_child_now_pinned` 是否一定会红（fail-closed）？

4. **参数化是否真的承重**。三个 pinned 值（2020 / 2026 / 2099）里，有没有哪一个其实与另一个
   等价（同一条代码路径、同一组判定），以至于它只是把同一件事跑了三遍？自述 7 的第三条变异
   声称「恰好 2020 / 2099 红」，请核这个结论与代码一致（`active_snoozed` 的判定里 `now` 的
   年份确实是三个参数唯一实质不同的输入吗）。极值侧 2099-12-30 会不会在某处触发与本门无关
   的溢出/换算分支，从而让绿是「因为别的原因」？

5. **新门有没有把旧门弄松**。改动后的端到端门里，`_assert_child_now_pinned(seen, pinned)`
   插在第二次 refresh 之后、读 `after` 之前。请核这个位置会不会让「让位」那条断言在某些
   失败形态下**根本跑不到**，从而把一个本该红在让位上的回归报成红在前提上（诊断失真）。
   另：原门的其余断言（stats / boards / buckets / GET 侧 `due_count == 3` / `snoozed` 集合）
   是否一字未动？

6. **哑弹扫描的判据够不够**。自述 8 的三项合取只覆盖「`_pin_now` + refresh 子进程」这一种
   分叉。同一个卡面上还有没有**别的**「一侧钉死、另一侧读真实墙钟」的形态没被这条判据覆盖
   （例如 `_display_today()` 走真实墙钟而夹具用字面量日期、runner 侧的 `now` 传参、
   `fsrs_due` 字面量到某个年份后语义翻转）？若有，请点名用例。

7. **还有没有别的时间依赖**。`test_g66_e2e_snooze_verdict_is_clock_independent` 只钉了
   `_display_now` 与子进程 `--now`。`review_overview` 里还有没有第三个读钟点在这两条用例的
   路径上（`_read_entry` 的 `datetime.now(_display_tz())`、`_display_today()`、去抖用的
   `time.monotonic()`）会让判定在某些真实时刻不同？其中哪些是无害的、哪些是下一颗哑弹？

8. **自述与代码是否一致**。第 9 条的数字（365 = 362 + 3、8 = 8）、第 10 条的 mtime 结论、
   第 3 条「脚本名取自生产常量」，逐条与代码/证据核对，指出任何过度断言。

---

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line`、问题陈述、以及一个**具体的
失败场景**（什么输入 / 什么状态 → 什么错误结果）。没有问题的分级写「无」。

---

## 五 边界

- 只读审查：不要修改任何文件。
- 不要连接任何数据库或网络服务。
- 已裁事项不要当缺陷提：D-8（板级 / 两档）、20:00 阈值（任务书默认值，待用户确认）、
  D-18（时区来源由 U6-A 落地）、U6-B 的锁与三方合并行为。
- `canvas-vault/.claude/scripts/fsrs_bridge.py` 与 `decay_beta.py` 本卡零触碰，不在审查面内。
- 本轮只改了一个测试文件；前五轮已审过的实现面，除非你发现本轮改动**使它的结论失效**，
  否则不必重审。
