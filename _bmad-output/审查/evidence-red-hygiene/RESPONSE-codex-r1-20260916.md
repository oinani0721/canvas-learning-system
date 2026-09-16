# CARD-RED-HYGIENE 对 Codex r1 的逐条处置

> r1 存档：`_bmad-output/审查/codex-review-CARD-RED-HYGIENE-r1.md`（绑 `8bfcdfce`）
> r1 计数：**BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 4**
> ⚠️ r1 审查期间本 session 已提交 `b38e1d04`（只读对抗自审的整改），Codex 在报告末尾
> 自行实测并如实声明「diff 非空：3 files changed」——**r1 不绑最终 HEAD，不作终审**。
> 本文件写完后本卡再送 r2。

---

## HIGH-1 目录级「不增」判据：车道给理由，**不自判通过**（D-15）

**Codex 实测**（其环境）：

| 运行条件 | 结果 | `<` | `>` | 端口哨兵 |
|---|---|---:|---:|---|
| 原环境 | 67 failed / 5133 passed | 30 | **33** | blocked=0 |
| 仅前置已有 Node v24.16.0 | 35 failed / 5165 passed | 30 | **1** | **blocked=1** |

**车道实测**（本树，三次独立全跑）：

| 运行 | HEAD | 结果 | `<` | `>` | 端口哨兵 |
|---|---|---|---:|---:|---|
| `unit-close-20260916T131111` | 8bfcdfce | 34 failed / 5166 passed | 30 | **0** | blocked=0 |
| `FINAL-unit-close-20260916T191150` | b38e1d04 | 34 failed / 5166 passed | 30 | **0** | blocked=0 |
| `FINAL-R2-unit-close-20260916T192615` | **2c740216（最终）** | 35 failed / 5165 passed | 30 | **1** | **blocked=1** |

⚠️ **第三跑（绑最终 HEAD）车道自己也跑出了 `>` = 1** —— 与你 r1 第二跑**同一条 nodeid、
同样 blocked=1**。所以这不是「你的环境有问题、车道这边干净」，而是两个独立环境上
同形出现的同一现象。车道据此**撤回**原先那种「车道两跑都是 0」的对照式表述，
验收单也改成不声称 `>` = 0。那条的失败正文首行逐字是协议 §3 的哨兵指纹：

    - ('::1', 7691, 0, 0) on thread MainThread (owner=…test_accept_candidate_already_accepted_returns_422)

唯一指纹数 = 1，`advisory=0 / unaccounted=0`，连接**被拦下**（未连上现网 7691），
随后走 JSON 降级。三跑的 `blocked=` 分别是 0 / 0 / 1。

**车道给出的理由（三条，逐条可核）：**

0. **（本轮新增，最重要的一条）车道在最终 HEAD 上复现了同一现象** —— 见上表第三行。
   这条既削弱了「它只是 Codex 环境问题」这个解释，也加强了「它是哨兵归属漂移而非本卡回归」
   这个解释：同一条 nodeid、同样 blocked=1、两个独立环境、两个不同 SHA，
   而本卡三个 commit 都没碰任何与端口 / Neo4j / conftest 相关的文件。

1. **第一跑的 33 条是环境故障，Codex 自己已归因**：其原环境 Node 缺
   `libllhttp.9.3.dylib` 导致 Node 启动失败。这不是代码面的事，本卡未改任何
   与 Node 相关的文件（地盘 6 文件里没有 JS/Node 面）。

2. **第二跑唯一那条 `>` 正是协议 §3 点名的 W4 哨兵载体，协议明令不得按 nodeid 判。**
   `.claude/rules/card-batch-protocol.md` §3 第 79 行原文：

   > **W4 哨兵判据绑 `blocked=` 次数 + 失败正文，不绑 nodeid**（R-08/R-10，第十四批起）：
   > 同一代码状态下哨兵红会在 nodeid 之间翻转（U10-A r4/r4b 实测：
   > `candidate422` ↔ `mock_warning`…），**逐 nodeid diff 自带 flaky**。

   Codex 第二跑的那条 `>` = `test_accept_candidate_already_accepted_returns_422`
   （即协议里的 `candidate422`），该跑 **`blocked=1`**；车道三跑的 `blocked=` 分别是
   **0 / 0 / 1**，出现 `>` = 1 的那一跑恰恰就是 `blocked=1` 的那一跑。
   ⇒ `>` 的出现与 `blocked=` 严格同步，与 SHA 无关（车道三跑跨三个不同 SHA）。
   按协议就不能在 nodeid 轴上把不同哨兵状态的两跑直接相减。
   Codex 自己也实测「随后单跑它为 1 passed，blocked=0」。

3. **归属侧 Codex 给了比车道更强的证据，且结论一致**：其反面问题 #4 的回答里写，
   把 `$PREV` 已入库的 `epw-unit-close7.nodeids` 与本卡存档相比，
   **双方同为完全相同的 34 条红** ⇒「本卡贡献 0」成立。
   （车道原先只用「本卡 4 个测试文件不在 BASE 红集里」来论证，Codex 指出那不充分，
   车道接受这个批评：`attribution-*.txt` 已补更正段，本条以 Codex 的对照为准。）

**车道不自判通过**：依 D-15「车道对 HIGH 的驳回要写理由但不能自判通过，由主 session
复核时裁定，裁定前该卡按未完成」。上列三条是理由，**裁定权在主 session**。
建议主 session 核的三件事：
(a) 「`>` 的出现与 `blocked=` 严格同步、与 SHA 无关」这个观察是否成立
    （车道三跑跨三个 SHA：blocked 0/0/1 对 `>` 0/0/1）；
(b) 那条 `>` 是否按协议 §3 归入哨兵归属漂移而非本卡引入；
(c) 更上一层：既然逐 nodeid diff 在有哨兵红时结构上不可用，
    「目录级只许 `<`」这条卡级判据本身是否该改成协议 §3 的 `blocked=` 口径
    （本卡不自行改判据口径，只提请裁定）。

---

## MEDIUM-1 模板 guard 会漏掉「绑定之后再就地改表」—— ✅ 已修

Codex 实测（抽真实 helper、内存替换 `inspect.getsource` 输入）：

```
原名单：                        GUARD_PASS extracted=13 runtime=13 equal=True
expected_templates += ["new"]： GUARD_PASS extracted=13 runtime=14 equal=False   ← 漏检
expected_templates[0]="renamed"：GUARD_PASS extracted=13 runtime=13 equal=False  ← 漏检
```

**车道接受，已修**（`test_agents_health.py`，本卡地盘内）：

1. **作用域收窄**：新增 `_own_statements()`，只遍历 `health_check` **自己**的语句，
   不下钻进嵌套 `FunctionDef` / `AsyncFunctionDef` / `Lambda` / `ClassDef`。
   （原先用 `ast.walk`，嵌套函数里的同名局部变量会被一起收进来。）
2. **就地改表检测**：新增 `_assert_not_mutated_after_binding()`，对
   `AugAssign` / 下标赋值 / `Delete` 下标 / `.append|.extend|.insert|.remove|.pop|.clear|.sort|.reverse`
   任一命中即**报红**并写明理由 —— 不去猜改动后的值，而是直接判定「读字面量」这个
   取值前提已失效。
3. **顶层形态断言**：`inspect.getsource` 必须取到单个函数定义，否则红。
4. **覆盖声明收窄**：guard 的 docstring 明写它钉的是「mock 的名单 ==
   生产**在绑定处声明**的名单」，**不**钉运行时值；第 2 条把「声明 ≠ 运行时」的形态
   挡在门外，使门通过时两者必然一致。原先「增/删/改名/换序任一发生都会红」这句
   过强表述已删除。

   > ⛔ **撤回（2026-09-17，Codex r6 LOW-1）**：上面那句「**使门通过时两者必然一致**」
   > 本身就是同型的过强声明，**予以撤回**。正文保留原样以存历史，但**不得再被引用为保证**。
   > 反证来自 r6 第 3 问的实跑（它直接加载当前测试文件、内存替换 `inspect.getsource`、
   > 调用**真实完整 guard**）：`match` 星号捕获、类体 `.pop()`、已触发的 `except … as`、
   > `import math as`、`def` 同名函数 —— **五种形态都能通过 guard，而名单已被改掉**。
   > ⇒ 门通过**不蕴含**两者一致。这正是本卡反复踩的那个坑：撤掉一句穷尽声明之后，
   > 替代措辞里又写进了一句新的穷尽声明。本卡同型累计第 7 处。

**用 Codex 的方法复验**（`FINAL3-guard-shapes-*.txt`，import 入库的真 helper，
不是另抄一份）：

```
01 当前生产形态（字面量 13 项）      GUARD 通过，取到 13 项，与 mock 逐元素相等 = True
02 带类型注解（无害改动）            GUARD 通过
03 绑定后 += 追加（Codex 演示之一）  GUARD 红（AugAssign）
04 绑定后下标改名（Codex 演示之二）  GUARD 红（Assign 下标）
05 绑定后 .append                    GUARD 红（Call）
06 绑定后 .remove                    GUARD 红（Call）
07 嵌套函数里同名局部变量            GUARD 通过且取到**外层**那张表（作用域修复生效）
08 改从常量读                        GUARD 红（非字面量）
09 列表推导                          GUARD 红（非字面量）
10 两处顶层绑定                      GUARD 红（FOUND-2）
11 变量改名                          GUARD 红（FOUND-0）
```

⇒ Codex 演示的两种漏检形态（03 / 04）现在都红。

---

## MEDIUM-2 第 0 分钟「工作树干净」证据不足 —— ✅ 接受，记为**未证实**

Codex 的反驳成立：**空目录本身不会被 git 计入脏项**，所以「仅仅 mkdir 了 evidence
目录」并不能自动解释 porcelain 的那个 1；而该存档只记了 `wc -l` 的结果 **1**，
没有留下 porcelain 的原始路径，事后无法排除当时还有别的脏项。

**车道处置**：不追认。`minute0-*.txt` 的补注段已说明它是「本判据自己刚创建的
evidence 目录」，但那是**事后重建的解释，不是当时的证据**；本处正式把
「第 0 分钟工作树干净」记为 **未证实（PARTIAL）**，写进验收单 §六「本卡未证明什么」。

可作旁证但不充分：本卡后续每一次 `git status --porcelain`（territory 两份存档）
里的未跟踪项**全部**是本卡自己的 evidence / codex 产物，未出现任何第三方脏项。

---

## MEDIUM-3 最终 commit 的 `python-typecheck` 实跑未被独立证明 —— ✅ 接受，已补

Codex 的反驳成立：车道引的 `✔️ python-typecheck (3.07 seconds)` 出自**第一次失败的**
commit 尝试，两次成功的 commit（`8bfcdfce` / `b38e1d04`）没有留下 hook 的完整输出；
且该 hook 在工具缺席时会 SKIP 并返回 0，勾号本身不足以证明实跑。

**车道处置**：本卡最后一个 commit 把 pre-commit 的完整输出落盘为
`FINAL-precommit-hooks-*.txt`（含 `python-typecheck` 那一节的原始文字），
并在同一份里贴 `pyright app` 的独立实跑结果。对前两个 commit，
如实标记为 **历史执行项 PARTIAL**（未留原始输出），不追认。

另记 Codex 的一条实测：其环境默认 Node 损坏导致 `$P app` 起不来，
仅前置 Node v24.16.0 后得 `0 errors, 81 warnings, 0 informations`
—— 与车道环境的结果一致，但两者**不能混写成「原命令直接通过」**。

---

## LOW-1 「零 await 等于 handler 正文未执行」措辞过宽 —— ✅ 已修

`_handler_was_not_reached` 的 docstring 已收窄：零 await 直接证明的是
**没有走到那一次 LLM 调用**，不等于「正文一行都没跑」（那行之前还有
`format_litellm_model(...)`）。「鉴权先于 handler」这个更强结论改为由三样东西
合起来支撑：路由的 `dependencies=[Depends(...)]` 声明 + 拒绝档返回 503 +
只摘鉴权依赖就让同一谓词翻成 False 的对照用例。

---

## LOW-2 计数 / 索引 / 行号三处不准 —— ✅ 全部已修

1. fixture docstring「既有 12 条」→ **10 条**（自审 RH-5 已修，Codex 独立复现同一数字）。
2. `test_cache_configuration.py` 文件头仍列已删的 retry 测试 → 已标注 AC-2 随死配置退役。
3. 格式豁免存档的行号精度：原文引的是 hunk 头与跨度（`@@ -244,9`），
   实际被改行是 **PREV 284-286 → 被审 SHA 247-249 → 当前 HEAD 250-252**。
   已在 `lefthook-exclude-justification-*.txt` 末尾逐版更正；结论（不与本卡改动行相交）不变。

---

## LOW-3 定性结论超出采样证据 —— ✅ 已修（自审同批发现）

flaky 定性与 contract pattern 两处的过强结论，在送 r1 之前的只读对抗自审里已分别
更正（见 `flaky-characterization-*.txt` 与 `contract-nodeid-CORRECTED-*.txt` 的更正段）。
Codex 独立得出同样结论，两边一致。

---

## LOW-4 最终地盘证据未进入被审提交 —— ✅ 已修

`territory-headcommit-*.txt` 当时写于 commit 之后、尚未入库，
已随 `b38e1d04` 提交。Codex 也确认「这是归档缺口，不是地盘越界」。

---

## 本文件未证明什么

1. 未证明 Codex 第二跑那条 `>` **一定**是哨兵漂移 —— 车道给的是协议 §3 的口径依据
   与两跑哨兵状态不同这一事实，**没有**在 Codex 的环境里复现并定位到具体成因。
2. 未证明车道环境的两次 `>` = 0 能代表候选树 —— 集成期主 session 需在候选树重跑。
3. 未证明 MEDIUM-2 里那个 porcelain 的 1 确实只是 evidence 目录 —— 已按未证实记。
4. 未在 r1 之后对 `test_sync_batch_auth.py` / `.env.example` / `config.py` 三个未被 r1
   点名的地盘文件做额外加固 —— r1 对它们无 finding，车道也未主动扩面。
