# 独立复审 round-2 — CARD-G3-3-R1（按 round-1 意见整改后的复核）

你是独立审查者。工作树**只读**，不要修改任何文件、不要连接任何数据库或网络服务。

---

## 一 背景与**最小读取面**

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z2-cas`
（分支 `card/z2-cas`）。

round-1（绑 `a795741f`）给出 HIGH×2 / MEDIUM×2 / LOW×1。作者对其中四条做了整改，
第三条（MEDIUM，`_error_lines()` 没有绑定回溯段/异常类型/断言位置）**没有改匹配器**，
改为在门这一侧加前提断言，并把残余面写进验收单。本轮只复核**整改本身**。

**请只读**：

1. 整改 diff：`git diff a795741f <R2_SHA> -- . ':(exclude)_bmad-output'`
2. `backend/scripts/g33_mutation_gates.py` 里的残留判据段（`_mark_files` 及其下游到 `return`）
3. `backend/tests/regression/test_g3_3_cas.py` 里被改的四处：
   `test_concurrent_same_node_no_lost_update`、`_install_racing_bridge` + 新增的 `_race_fired`、
   `test_writer_refuses_when_other_writer_took_the_event_id`、
   `test_out_of_order_marker_is_additive`，以及两条新门里新增的那一行前提断言。

需要时可读被测生产文件作为参考（不要改）：
`canvas-vault/.claude/skills/quiz-answer/SKILL.md`、`backend/app/services/learning_event_log.py`。

---

## 二 整改内容（**请独立核对**，不要采信）

| round-1 编号 | 整改 |
|---|---|
| R1-01（HIGH） | 把「前提」与「后果」拆成两条断言身份：M15 门先断言 `ids.count(evid) >= 1`（消息「账本里一行都没有 — 插队写者根本没跑到…」），再断言 `== 1`（消息「同 event_id 被写了两遍」）；M1 门先断言 `len(rows) == 2`（消息「两个写者没有都落账，本门的前提不成立…」），再走原来那条链式 `== 2` |
| R1-02（HIGH） | `_install_racing_bridge` 注入的代码额外写一个与节点正文**无关**的凭据文件（`<节点绝对路径>.race-fired`）；两条恢复路径门在判「正文里没有 RACE_MARK」**之前**先断言 `_race_fired(race)` |
| R1-03（MEDIUM） | **未改匹配器**（理由见问题 3），改为用 R1-01/R1-02 的前提断言把残余口堵在门这一侧；残余面登记在验收单 §十二 |
| R1-04（MEDIUM） | 在「没多 `out_of_order` 键」那条之后补 `assert caller_payload == caller_snapshot` |
| R1-05（LOW） | 判据两个方向都看（`leftovers` 与 `baseline_missing`）；退出码加入 `scan_ok` 与 `baseline_missing`。**并且把 `grep` 整个换掉**：改成 Python 逐字节扫描（分块 + 重叠尾巴），新增 `_source_of()` 把 `X/__pycache__/name.cpython-*.pyc` 归到源文件 `X/name.py` 后再判「自身 / 基线」 |

作者另跑了一条**对照输入**（语法合法但运行期即死：在写点主块最前面 `raise SystemExit(...)`），
声称三条门在旧判据下都会被判 KILLED、整改后都正确判 SURVIVED，且跑后 `SKILL.md` sha 与跑前相同。

---

## 三 请按重要性排序回答的问题

1. **前提断言是否真的把两种情形分开了？** 有没有哪种输入能让**后果**断言（`== 1` /
   链式 `== 2` / RACE_MARK）在**前提不成立**时仍然先红？反过来，前提断言会不会在
   **真实缺陷**发生时先红，从而把本该 KILLED 的变异误报成 SURVIVED（修过头）？
   请特别看 M1：`len(rows) == 2` 与它下面那条链式断言的关系。
2. **`.race-fired` 凭据是否可靠？** 它由注入代码自己写；有没有「注入跑了但凭据没落盘」
   或「凭据落盘了但那次追加没成功」的情形？它落在 `节点/` 目录里，会不会影响写点、
   校验器、或那条 `*.quiz-tmp` 残留断言？三条用到 `_install_racing_bridge` 的门里，
   只有两条断言了这个凭据（作者认为另一条由断言顺序已经保护），这个判断对吗？
3. **R1-03 不改匹配器是否可接受？** 作者的理由是：`_run_gate` 每次只跑一个 nodeid；
   18 个片段在门文件里各出现一次；换成结构化失败报告属另一层工程，且收口卡里换判据
   实现风险更大。请评估这个取舍，并指出在**当前**代码下还剩哪些具体输入能让
   `expect_msg` 命中而目标断言其实没红。
4. **新的 Python 扫描器是否正确、是否有漏面？** 请逐行核 `_mark_files()` 与 `_source_of()`：
   分块读 + 重叠尾巴（`tail = chunk[-(len(needle)-1):]`）跨块边界的命中真的抓得到吗？
   跳过 symlink / 非普通文件会不会漏掉该扫的东西？`_source_of()` 的
   `p.name.split('.')[0]` 对 `name.cpython-314.opt-1.pyc` 或文件名本身含点号的情形对吗？
   把 `.pyc` 归到 `.py` 后再判「自身 / 基线」，会不会把**生产文件**的 `.pyc` 里的真残留误排除？
   `scan_ok=False` 时 `leftovers` / `baseline_missing` 都被置成 `["<扫描失败>"]`，
   这个表示法与退出码条件是否覆盖了全部失败面、会不会误导读日志的人？

   背景（作者实测，可质疑）：换掉 `grep` 的原因是**同一条判据的结论取决于 PATH**——
   本机交互 shell 的 `grep` 是个函数、最终跑 ugrep 7.8.4，对二进制文件默认静默跳过；
   而 Python 的 subprocess 解析到 `/usr/bin/grep`（BSD），它会报。实测同一个 `.pyc`
   第 29686 字节处确有 MARK：`grep -c` rc=1（看不见），`grep -a -c` = 1。
5. 其余你认为影响结论的问题。

---

## 四 输出格式

```
## 结论
（一句话：整改后是否仍存在阻断级问题）

## 对五条整改的逐条裁定
（R1-01 ~ R1-05，逐条写「整改有效 / 整改不完整（附你看到的事实与行号）/ 修过头 / 无法核对」）

## 新发现
| 级别 | 编号 | 位置 | 事实 | 影响 | 建议处置 |

## 我没有核对到的面
```

---

## 五 边界

- 工作树**只读**：不要写入、不要 `git` 改状态。`backend/scripts/g33_mutation_gates.py`
  会改写生产文件（跑完还原）——**不要运行它**，只读源码。
- 不要连接 Neo4j（7691 / 7687）或任何网络服务。
- 已裁决不重开：`fsrs_bridge.py` 的 live 部署不在本卡范围；CAS 是 check-then-replace
  而非原子 CAS 是既有能力边界；不新增第二套投影字段。
- 本轮只需要分析结论与行号指认，不需要示例代码。
