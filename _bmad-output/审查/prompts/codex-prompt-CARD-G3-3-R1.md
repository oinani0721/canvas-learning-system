# 独立复审 — CARD-G3-3-R1（Z2 收口：负控假杀修复 + 两条恢复路径 CAS 门 + M4 补齐）

你是独立审查者。工作树**只读**，不要修改任何文件、不要连接任何数据库或网络服务。

---

## 一 背景与**最小读取面**

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas`
（分支 `card/z2-cas`）。

上一轮（CARD-G3-3）被复核判「不合」，三条原因之一是**负控假杀**：变异 `M15` 声称
「取锁后不重查 ⇒ 同一个 event_id 被写两行」，实际上它的变异体**语法不合法**，写点子进程
在编译期就死，账本 0 行，于是那条声称从未被打红过；判据只绑「哪个门红了」，没绑「哪一条
断言红了」，所以显示 `KILLED`。本卡（R1）修这一层，并补两处此前无门承重的 CAS 发布点。

**请只读下面这三份材料，不要通读全仓**：

1. 本卡代码 diff：
   `git diff 7105e84c <AUDIT_SHA> -- . ':(exclude)_bmad-output'`
2. `backend/scripts/g33_mutation_gates.py` 全文（负控脚本本体）
3. `backend/tests/regression/test_g3_3_cas.py` 里的两条新门
   （`test_a2_foreign_recovery_publish_respects_cas` / `test_dup_recovery_publish_respects_cas`）
   与被改动的 `test_out_of_order_marker_is_additive`

需要时可读被测生产文件作为参考（不要改）：
`canvas-vault/.claude/skills/quiz-answer/SKILL.md`、
`backend/app/services/learning_event_log.py`。

---

## 二 作者自述（**请独立核对**，不要采信）

1. **M15 已改成语法合法的单行短路**，红落在 `test_g3_3_cas.py` 的
   `assert ids.count("quiz:板A#q1") == 1, "同 event_id 被写了两遍"` 这一条上；
   实测抛出 `AssertionError: 同 event_id 被写了两遍: ['quiz:板A#q1', 'quiz:板A#q1']`。
2. **新增第三种裁决 `SYNTAX-INVALID`**：施加变异后、跑门之前做编译自检
   （`.md` 用与测试文件同一条正则抽 PYEOF 块逐块 `compile`；`.py` 直接 `compile`）。
   不通过既不算 KILLED 也不算 SURVIVED，脚本 rc≠0。
   `--selfcheck-syntax` 是它的负控输入检验：旧的（坏的）M15 串必判 `SYNTAX-INVALID`，
   新串与未变异原文必须通过（两个验伪锚），全程只在内存里施加、跑前跑后 sha 相同。
3. **新增变异 M16 / M17 / M4a / M4b** 各自绑定的门与断言：
   M16 → foreign 恢复发布 CAS 门；M17 → dup 恢复发布 CAS 门；
   M4a → 「`append_event` 就地污染了调用方的 payload」；
   M4b → 「`out_of_order` 标记不是加性的」。
4. **`BASELINE_MARK_FILES` 补第 5 项** `g32ccr1_negative_controls.py`：车道 HEAD 已含主干
   `03ac8bf8`，该文件是主干上新增的既有负控脚本；少列它会让「残留检查」把它算成本脚本的
   残留，从而**什么都没错也返 1**。判据仍是「与基线集合相同」，没有改成 `= 0`。
5. **生产逻辑零改动**：`git diff 7105e84c <AUDIT_SHA> -- backend/app canvas-vault` 为空；
   `learning_event_log.py` / `SKILL.md` 只在负控脚本内被临时改写并无条件还原。

---

## 三 请按重要性排序回答的问题

1. **`expect_msg` 判据会不会被别的输出喂饱？** 作者的判据是「`expect_msg` 出现在 pytest
   回溯里以 `E ` 开头的行里」，理由是 long traceback 会把整个测试函数的源码打印出来，
   函数里每条断言的消息串都在 stdout 里，所以 `msg in stdout` 等于恒真。
   请核对 `_error_lines()` 的实现：还有没有别的输出会落进 `E ` 行，使某条 `expect_msg`
   在「它声称的那条断言其实没红」的情况下仍然命中？特别是同一个门里多条断言的消息
   互为前缀、或参数化用例产生多段回溯的情形。
2. **两条恢复路径门的对照段，真的证明了 seed 通过了它前面的两道门吗？**
   （`SKILL.md:2501` 采用时刻门 / `:2649` attempt 序数门。）如果对照段其实是被更早的
   某个分支放行的，那么「注入竞态后失败」就可能不是 CAS 贡献的。请指出对照段的判据里
   哪些是真正把这两道门走完的证据，哪些只是**看上去**像。
3. **M4b 的形态是否只拆掉了被测的那一条防线？** 它把
   `payload_out["out_of_order"] = True` 换成 `payload_out = {"out_of_order": True}`。
   这是否同时破坏了别的东西（例如后续读 `payload_out` 的分支、记录落盘、或校验），
   以致于红是由别的原因贡献的？作者另外把加性断言的期望值从 `caller_payload` 本身
   换成了调用前的 `deepcopy` 快照——这个改动有没有让某条断言变松？
4. **`SYNTAX-INVALID` 有没有漏网形态？** 编译自检只能拦「编译期就死」。**语法合法但
   运行期立刻死**的变异体（例如 `NameError` / 缩进合法但作用域错位 / import 失败）
   同样会造成「防线本该引发的坏事根本没机会发生」而门因别的断言变红。
   请评估：现有的 `expect_msg` 判据能不能覆盖这一类？如果不能，缺口在哪一条变异上？
5. 其余你认为影响结论的问题（负控脚本的还原保证、信号处置、残留判据、门未覆盖的路径）。

---

## 四 输出格式

按下列结构输出 Markdown：

```
## 结论
（一句话：本 diff 是否存在阻断级问题）

## 发现
| 级别 | 编号 | 位置 | 事实 | 影响 | 建议处置 |
（级别用 BLOCKER / HIGH / MEDIUM / LOW；「事实」必须是你自己核对出来的，
 写清楚你读了哪一行、看到了什么，不要复述作者自述）

## 对作者自述的逐条裁定
（§二 的 5 条，逐条写「核对通过 / 不成立（附你看到的事实）/ 无法核对（附原因）」）

## 我没有核对到的面
（如实列出）
```

---

## 五 边界

- 工作树**只读**：不要写入、不要 `git` 改状态、不要运行会改文件的脚本。
  `backend/scripts/g33_mutation_gates.py` 会**改写生产文件**（跑完还原）——**不要运行它**，
  只读它的源码。只读的 `--selfcheck-syntax` 也请不要运行，以免与别的进程互踩。
- 不要连接 Neo4j（7691 / 7687）或任何网络服务。
- `canvas-vault/.claude/scripts/fsrs_bridge.py` 在本车道与线上副本不同，**部署不在本卡范围**
  （由主 session 在合入当天单独执行），请不要把「未部署」当成本 diff 的缺陷。
- 判断以仓内规则文件与 `docs/learning-events-schema-v1.md` 为准。
