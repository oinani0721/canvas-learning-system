你是本次改动的独立审查者。请只依据**仓库里的真实文件**作判断，逐条给出 file:line 与你自己跑出来的观测值；不要复述我的说法。

## 仓库与审查范围

工作树根目录（绝对路径）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas`

本轮**只审**这一段 diff（基线 `304f03ca` → 本卡唯一 commit `47a37a0c`）：

```
git -C /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas \
    diff 304f03ca 47a37a0c
```

改动的 8 个实质文件：

- `canvas-vault/.claude/skills/quiz-answer/SKILL.md`（两个 PYEOF 静态块）
- `canvas-vault/.claude/skills/start-exam-board/SKILL.md`
- `canvas-vault/.claude/scripts/fsrs_bridge.py`
- `backend/app/services/learning_event_log.py`
- `backend/tests/regression/test_g3_3_cas.py`（新增，21 门）
- `backend/scripts/g33_mutation_gates.py`（新增，7 条负控变异）
- `backend/scripts/g33_concurrency_evidence.py`（新增）
- `.gitignore`（新增一行 `canvas-vault/.locks/`）

范围外的文件、范围外的历史轮次结论，都不在本轮。

## 这次改了什么

给复习写侧加了**三层并发防护**：per-node 跨进程写锁、账本追加的跨进程锁、
发布 frontmatter 前的 compare-and-set；并给迟到事件加了**加性**的 `out_of_order` 补录标记。

### 1. per-node 写锁（`quiz-answer/SKILL.md` 两个 PYEOF 块）

- 位置：主块在 `GN2 = round(GN, 2)` 之后、`s = open(NODE...).read()` **之前**。
- 机制：`fcntl.lockf`（POSIX 记录锁）加在 `<VAULT>/.locks/node-<sha1(realpath(NODE))[:16]>.lock` 上，
  轮询取锁，60 s 超时后 `SystemExit` 零写。锁 fd 全程不关（进程退出时内核释放）。
- 声称解决的问题：两个进程若各自读到同一份旧 frontmatter，后发布的那份按旧基线算，
  `attempt_count` 双双写 1、水位线只反映一次评分 —— 账本 2 行而笔记只算 1 次。

### 2. 账本追加锁（三个写点）

- `quiz-answer/SKILL.md`：`os.open(EV, O_RDWR|O_CREAT|O_APPEND)` 后先取锁，
  再做 LF 守卫 → `os.write` → `fsync`。
- `start-exam-board/SKILL.md`：同形态（该块的失败契约不变：写失败不阻断出题）。
- `backend/app/services/learning_event_log.py::append_event`：整段「查重 → LF 守卫 → 写」
  收进 `fcntl.lockf` + 原有 `threading.Lock`；取不到锁返回 `False` + `logger.error`。

**关键实现细节（本轮请重点核）**：三处都在持锁期间**只用同一个 fd** 做
`os.lseek` / `os.read` / `os.write`，不再 `open()` 第二次。理由是 POSIX 记录锁的释放语义
按「进程 × 文件」——本进程关掉指向该文件的**任意**一个 fd，该文件上的全部记录锁整体释放。
`learning_event_log._read_all(fd)` 是这条约束的载体。

### 3. 发布前 CAS（`fsrs_bridge.py` 边界 + `SKILL.md` 四个发布点）

- `fsrs_bridge.cas_token(node_text)` 由**读入的那份字节**算 `sha256` + revision 面
  （`fsrs_last_review` / `attempt_count`）；`cas_conflict(path, token)` 重读盘上内容比较。
- 判据是**全文 sha256**，不只是 revision 两字段。
- 写分主块的三个 `os.replace(NODE...)` 之前各插一次 `_cas_guard(...)`；冲突 → 零写 `SystemExit`。
- A3 增量归纳块（第二个 PYEOF 块）：同一把锁 + 同一 CAS 口径，但冲突时是**自动重读重算**
  （最多 4 轮），不是 fail-closed。两处口径**故意不同**，理由写在该块注释里。

### 4. 乱序补录标记（`learning_event_log.append_event`）

- 新事件若 `payload.schema_ext == "review/1"` 且 `effective_at` 不晚于
  本节点已记录的最新**适用**复习事件（同 node_id / review/1 / 未标 out_of_order），
  就在 payload 里补 `out_of_order: True`（拷贝调用方 dict，不就地改）。
- 依据是 `docs/learning-events-schema-v1.md` §6.2 第 266 / 270 行已冻结的口径。
  **schema 文档本轮零改动**（`git diff 304f03ca 47a37a0c -- docs/` 为空）。

## 已裁决、不在本轮讨论的事项

- schema §6.1–6.3 不改（本卡硬边界）；`out_of_order` 的字段形态与语义沿用既有冻结口径。
- 不改 picker / 投影 / UI；不做 G3-9 跨视图对账；不部署 live vault。
- 网络文件系统上的锁语义：`fcntl` 只在本机成立，跨机并发不在本卡承诺范围。
- `start-exam-board` 块的账本查重仍是子串匹配、且该块**没有 LF 守卫**——两条都**先于本卡**
  存在，本卡只加锁不改它们，已作为观察项登记，不算本轮缺陷。

## 我自己已经做过的验证（请当作待质疑的断言，不要当前提）

- 21 道行为门全绿：`test_g3_3_cas.py`。
- 7 条负控变异 7/7 KILLED（`backend/scripts/g33_mutation_gates.py`），
  结果见 `_bmad-output/审查/evidence-g33/mutation-results.json`。
  每条变异声明了它**必须**打红的 nodeid，KILLED 判据是 `rc != 0 且该 nodeid 在失败集里`。
- 并发取证 3 轮 0 lost update：`_bmad-output/审查/evidence-g33/concurrency-run.json`。
- 裁判：`test_g3_2_review_ledger.py + test_g3_3_cas.py` = 146 passed（基线 125 不回退）；
  `test_fsrs_bridge/test_learning_events_schema_contract/test_learning_event_log` = 210 passed 1 skipped；
  `tests/skills` = 369 passed。

## 请重点回答的问题

1. **锁的选型与用法是否站得住**：用 `fcntl.lockf`（POSIX 记录锁，per-process）而不是 `flock`
   （per-open-file-description）。声称的理由是「同一个 pytest 进程会 exec 静态块不止一次，
   flock 会自锁死」。这个理由在本仓的测试形态下成立吗？
   更重要的：POSIX 记录锁「本进程任意一个 fd 关闭即整体释放」这条性质，在本 diff 的
   **四处**用法里（per-node 锁 ×2、账本锁 ×3，其中 quiz-answer 两块各一）有没有仍被违反的地方？
   请逐个持锁区间读一遍，看有没有哪条路径上还会 `open()` 到同一个文件（含间接调用）。

2. **锁的覆盖面是否够**：主块的 per-node 锁从「读节点前」持到进程退出。这段区间里
   是否还有**未被锁保护**的写入面？`.locks/` 目录在什么情况下会被创建、
   是否可能让零写门的判据落空（既有零写断言 `_write_face` 比的是节点 sha + 账本 sha）？

3. **CAS 的判据强度**：用全文 sha256 而不是只比 revision 两字段。这个选择在
   「用户在 Obsidian 里编辑正文的同时评分」这个场景下的结论是什么？反过来，
   它会不会把某些**本该放行**的情形误拒？请在 `SKILL.md` 里核对：`_cas_guard` 的四个
   调用点之后、对应的 `os.replace` 之前，是否还有别的路径能改到节点文件。

4. **两处冲突处置口径不同**（主块 fail-closed vs 增量块自动重算）：注释给的理由是
   「主块从读入起就把 body 留在内存里，自动重算会拿旧正文覆盖别人的编辑；
   增量块的产物只由盘上当前 body + 本次 callouts 决定，重算安全」。
   这个区分是否成立？增量块的 4 轮重试里，`added` 计数与最终写入的一致性有没有问题？
   4 轮用尽后 fail-closed 的那条路径，是否真的零写？

5. **乱序标记的判据**：`append_event` 拿「本节点已记录的最新适用复习事件的
   `effective_at`」当基准，而 schema 说的是 `review_time <= W`（W = 节点 frontmatter 的
   `fsrs_last_review`）。这两个基准在什么情况下会分叉？分叉时本实现会给出错误的标记吗？
   另外：`<=` 还是 `<`，本实现选了 `<=`，与 §6.2 A3（在线写侧推进到 W+1s 保证严格大于）
   放在一起看是否自洽？还有：`_instant()` 对无时区时刻返回 `None` ⇒ 该行不参与基准，
   这个降级方向对不对？

6. **负控是否真的承重**：`backend/scripts/g33_mutation_gates.py` 的 KILLED 判据是
   `rc != 0 and _hit(nodeid, failed)`。请核对 `_failed_nodeids` 的正则与 `_hit` 的前缀匹配
   是否存在「被别的门红了喂饱」的路径。另外请判断：7 条变异是否覆盖了这次引入的
   **每一条**防线；有没有哪条防线拆掉之后没有任何门会红（即那条防线没有负控）。

7. **门是否有自证成分**：
   - `test_append_event_holds_lock_across_the_whole_scan` 的判据是「抢到锁之后子进程
     还剩多少活」，阈值 60 ms，账本预置 20 万行。这个阈值与预置规模的组合，在机器负载
     波动时会不会翻转结论（既可能假红也可能假绿）？
   - `test_skill_ledger_section_opens_no_second_fd` 是**形态门**（静态扫描源码片段），
     它剥掉了注释行。这个判据有没有别的落空方式？
   - 并发门 `test_concurrent_same_node_no_lost_update` 的两个子进程启动间隔，
     是否足以让竞态窗口在**未加锁**时可靠出现？（变异 M1 的实测输出在
     `_bmad-output/审查/evidence-g33/mutation-results.json`，可以参考。）

8. 任何**本 diff 引入的**新缺陷：数据丢失 / 死锁 / 无限等待 / 幂等破裂 / 契约违反 /
   fail-closed 方向写反 / 异常路径上锁或 fd 泄漏。

## 输出格式

按严重度分节（BLOCKER / HIGH / MEDIUM / LOW），每条给：
`file:line` + 你观察到的事实 + 为什么它是问题 + 你建议的处置方向。
没有发现的严重度分节请写"无"。最后给一句总体判断。
