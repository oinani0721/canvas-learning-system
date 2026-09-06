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

1. 整改 diff：`git diff a795741f c4dfb9e6 -- . ':(exclude)_bmad-output'`
2. `backend/scripts/g33_mutation_gates.py` 里的残留判据段（`_mark_files` 及其下游到 `return`）
3. `backend/tests/regression/test_g3_3_cas.py` 里被改的四处：
   `test_concurrent_same_node_no_lost_update`、`_install_racing_bridge` + 新增的 `_race_fired`、
   `test_writer_refuses_when_other_writer_took_the_event_id`、
   `test_out_of_order_marker_is_additive`，以及两条新门里新增的那一行前提断言。

需要时可读被测生产文件作为参考（不要改）：
`canvas-vault/.claude/skills/quiz-answer/SKILL.md`、`backend/app/services/learning_event_log.py`。

---

## 二 整改内容（**请独立核对**，不要采信）

整改分两批：先按 round-1 的五条改（R1-xx），随后作者又跑了一轮**内部多视角对抗审查**
（5 视角 × 2 反驳者），它抓出 13 条改动了代码或结论的问题（I-xx），也一并整改了。
下表是**最终状态**，不是 round-1 之后的中间态。

| 编号 | 整改（最终状态） |
|---|---|
| R1-01 | 把「前提」与「后果」拆成两条断言身份：M15 门先断言 `ids.count(evid) >= 1`（消息「账本里一行都没有 — 写点在追加之前就死了…」），再断言 `== 1`（消息「同 event_id 被写了两遍」）；M1 门先断言 `len(rows) == 2`，再走原来那条链式 `== 2` |
| R1-02 + I-3 + I-4 | 竞态注入的代码额外写一个与节点正文**无关**的凭据 `<节点绝对路径>.race-fired`；**四条**门在判「正文里没有 RACE_MARK」之前先断言 `_race_fired(...)`——两条恢复门、`test_cas_conflict_refuses_and_rerun_converges`（M2）、`test_incremental_block_cas_preserves_racing_edit`（M13）。⚠️ 作者最初判断后两条「靠断言顺序已保护」，**内部审查驳回并被对照输入证实判断错了**（M2 在旧判据下会被判 KILLED） |
| R1-03 | **未改匹配器** `_error_lines()`（理由见问题 3），改为用前提断言把残余口堵在门这一侧；残余面登记在验收单 §十二.8 |
| R1-04 | 在「没多 `out_of_order` 键」那条之后补 `assert caller_payload == caller_snapshot` |
| R1-05 + I-5/I-7/I-8/I-10/I-11 | **把 `grep` 整个换掉**，改成 Python 逐字节扫描（`os.walk(onerror=..., followlinks=False)` + 分块读 + 重叠尾巴）；`_source_of()` 用 stdlib `importlib.util.source_from_cache()` 把 `__pycache__/*.pyc` 归到源文件（不认识的形态抛 `ValueError` → fallback 保持自身路径 → **进 leftovers 报出来**）；`leftovers` 用原始路径、`baseline_missing` 只认**源文件自身的直接命中**（不认 `.pyc`，防陈旧字节码替已删基线顶包）；扫描失败时两个列表置 `None`（不是塞哨兵串），失败由布尔 `mark_scan_ok` 表达；退出码加入 `scan_ok` 与 `baseline_missing` |
| I-1 | `_install_racing_bridge` 改成返回 `tuple[str, dict[str, str]]`（此前注解还是 `-> str`，pyright 4 error 会阻断提交）；新增 `_race_env(vault)` 让凭据路径与注入路径**单点派生**，三处注入点都从它取 |
| I-6 + 自查 | 新增 `_check_expect_msg_unique()`：在跑任何变异**之前**逐条核「每条 `expect_msg` 在它绑定的门文件里恰好出现 1 次」**且**「在 `canvas-vault/` 与 `backend/app/` 里命中 0 次」，不满足 `return 2`。后半条是为了堵住「pytest 给多行断言消息的每一行都加 `E ` 前缀 ⇒ 内嵌 `{out}/{err}` 的断言一旦红，子进程全部输出都进判据面」这个残余口 |
| I-9 | 信号处置补 `SIGQUIT`；`SIGKILL` 挡不住，已在注释里如实声明 |

作者跑的**对照输入**（语法合法但运行期即死：在写点主块最前面 `raise SystemExit(...)`，
编译自检通过）声称：**四条**门（M2 / M15 / M16 / M17）在旧判据下都会被判 KILLED、
整改后全部正确判 SURVIVED，且跑后 `SKILL.md` sha 与跑前相同。
作者同时**如实声明**：M16/M17 那两条红在**对照段**断言上（`_race_fired` 挡的那一支没被触发）；
M13 与 M1 两条门**没有**对照输入覆盖。

作者的收官实测（绑定 `g33_mutation_gates.py = b209e5dc…` / `test_g3_3_cas.py = 3e44005c…`）：
18/18 KILLED、SYNTAX-INVALID 0、还原逐字节相同、残留无、基线不缺、rc=0；
回归 161 passed + 1 xfailed；`tests/skills` 369 passed；ruff / pyright 全 rc=0。

---

## 三 请按重要性排序回答的问题

1. **前提断言是否真的把两种情形分开了？** 有没有哪种输入能让**后果**断言（`== 1` /
   链式 `== 2` / RACE_MARK）在**前提不成立**时仍然先红？反过来，前提断言会不会在
   **真实缺陷**发生时先红，从而把本该 KILLED 的变异误报成 SURVIVED（修过头）？
   请特别看 M1：`len(rows) == 2` 与它下面那条链式断言的关系——真的 lost update 会不会
   让账本少于 2 行、从而被前提断言先拦下？
2. **`.race-fired` 凭据是否可靠？** 它由注入代码自己写；有没有「注入跑了但凭据没落盘」
   或「凭据落盘了但那次正文追加没成功」的情形？它落在 `节点/` 目录里，会不会影响写点、
   校验器、或那条 `*.quiz-tmp` 残留断言？`_race_env()` 单点派生之后，凭据路径与注入路径
   还有没有分叉的可能？
3. **R1-03 不改匹配器是否可接受？** 作者的理由是：`_run_gate` 每次只跑一个 nodeid；
   18 个片段在门文件里各出现一次且已升成常驻门；换成结构化失败报告属另一层工程。
   请评估这个取舍，并指出在**当前**代码下还剩哪些具体输入能让 `expect_msg` 命中而
   目标断言其实没红——特别是 `_check_expect_msg_unique()` 的「生产面 0 命中」这一条
   够不够堵住「断言消息内嵌 `{out}/{err}` ⇒ 子进程输出进判据面」。
4. **新的 Python 扫描器是否正确、是否有漏面？** 请逐行核 `_mark_files()` 与 `_source_of()`：
   分块读 + 重叠尾巴跨块边界的命中真的抓得到吗？`os.walk(onerror=...)` 是否覆盖了全部
   遍历失败面？`baseline_missing` 只认源文件直接命中之后，还有没有别的顶包路径？
   `scan_ok=False` 时把两个列表置 `None`，下游打印与退出码是否自洽？
5. **有没有「加了门但没证明它承重」的地方？** 作者登记了 5 条新断言（4 处 `_race_fired`
   与那条整份比）没有变异指向它们，并说明**不为它们编变异**的理由。这个取舍对吗？
6. 其余你认为影响结论的问题。

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
