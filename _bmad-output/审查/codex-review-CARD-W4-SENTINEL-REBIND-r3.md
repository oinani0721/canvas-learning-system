> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-SENTINEL-REBIND round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-SENTINEL-REBIND-r3.md)"`
> 审查绑定: `9a280b16`（该轮审时即 HEAD）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `provider: openai`（.stderr:6） / `sandbox: read-only`（.stderr:8）

---

**本轮 BLOCKER：0；HIGH：1。审查 SHA：`9a280b16be0ada0a620bc279191a508c1ca87497`。目前不能判定复核通过：HIGH-3 的根因仍在。**

本轮通过内存管道调用当前源码的真实 `main()` 复现；未修改或暂存文件，未运行 pytest、hook 或连接数据库。源码 SHA 在审查结束时再次核对一致。

1. **HIGH — 正文仍可能静默消失；两条痕迹不足以判断记录是否完整。**

   位置：[w4_sentinel_identity.py:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:102)、`:107、115、226–240、318`。

   **未被拦下的输入：** 两档附相同四元组 `(1,1,0,0)`，正文分别使用两个不同地址，线程名均为 `"worker\n- continued"`。其中一档实际展开为：

   ```text
   - ('::1', 7691, 0, 0) on thread worker
   - continued (owner=x)
   NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)
   ```

   另一档只把地址换成 `('127.0.0.1', 7687)`。**实测两档 `bodies=[]`，CLI rc=0 / CONSISTENT。** 第一段没有止于 `on thread`；第二段以 `- ` 开头，逃过 orphan 检查。普通单行线程名的**对照输入返回 rc=1**。把 `\n` 换成 `\r`，同样假绿。

   同一根因还有三种输入，合并计为这一条 HIGH：

   - **空线程名：** `- 地址 on thread  (owner=x)` 不满足 `.+?`，两条痕迹也不命中；不同地址仍返回 `0`。实际 `Thread().name = ""` 接受空字符串，验证时未启动线程。
   - **地址段换行：** `"ADDR-A\n- tail"` 对 `"ADDR-B\n- tail"`，两档都只保留 `tail on thread worker`，返回 `0`。
   - **owner 前截断：** `- ADDR-A on thread worker` 对 `- ADDR-B on thread worker`，均被丢弃、返回 `0`。round-2 原本覆盖此类输入的测试，本轮在 [test_w4_sentinel_rebind.py:299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:299) 被换成了恰好止于 `on thread` 的输入；原输入已重新漏过。

   **仍存活的假设是：字段非空、换行一定留下指定断口，以及提取到的集合代表全部正文。**

2. **MEDIUM — 普通输出仍会被当作损坏记录，MEDIUM-3 只修到了原例。**

   位置：[w4_sentinel_identity.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:107)、`:115、231`。

   **对照输入：** 正常正文及汇总，可以比较。**负控输入：** 只增加普通日志 `cache refreshed (owner=worker)`，立即 **rc=2 / CONFLICT**。增加源码回显：

   ```text
   print(f"    - {address} on thread {thread} (owner={owner})")
   ```

   也触发 orphan；普通日志 `- waiting on thread` 则触发 truncated。规则仍扫描全文，没有区分哨兵记录与普通日志的来源。

   原例 `- waiting on thread worker` **核对通过**，但不能据此关闭整个假红问题。

3. **MEDIUM — 解码失败被替换成相同字符，损坏存档仍可能判一致。**

   位置：[w4_sentinel_identity.py:269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:269)。

   **未被拦下的输入：** 两份正文线程名的原始字节分别含 `work\x80er`、`work\x81er`，其余正文及汇总相同。`errors="replace"` 将二者都变成 `work�er`，**实测 rc=0**；合法 UTF-8 的 `work甲er`／`work乙er` 对照返回 `1`。

   这是新的“读不清却仍参与一致性比较”路径；未证明现有目录档发生过此类损坏。

4. **MEDIUM — 已移交的 MEDIUM-5 仍在，维持原分级。**

   位置：[w4_sentinel_identity.py:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:102)、`:147`。

   **未被拦下的输入：** 线程名 `worker (owner=A)`／`worker (owner=B)` 都截成 `worker`。地址内含完整分隔符也仍有歧义。裸 repr 和 portal 之外的线程编号仍不保证跨跑稳定。

   这些继续作为已登记债务，不重复计入上述 HIGH。

5. **MEDIUM — 已移交的 MEDIUM-6 仍在，并有“部分字段缺失”的同族漏收。**

   位置：[w4_sentinel_identity.py:155](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:155)、`:180`。

   **未被拦下的输入：** 对照档有合法汇总；负控档保留它，再追加下面这条缺右括号的汇总：

   ```text
   NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=13 (blocked=1, advisory=12, unaccounted=0
   ```

   追加行被 `if m` 滤掉，两档 **rc=0**；补上右括号的对照立即因重复汇总 **rc=2**。追加一条缺 `reported_status` 的总账也会被忽略。

   因而“整档没有四元组”已经拒判，但“有一条可解析记录，其余损坏记录全部忽略”的假设仍在。连同 `_FINAL_RE` 仅左锚、混档 `summary=2 + final=3`，继续归入已移交的部分漏收／来源绑定边界。

6. **LOW — LOW-7 措辞只改了一部分。**

   [模块头:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:39) 的新表述**核对通过**，但 [测试:171](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:171) 仍明确写“那 12 次是真连上了现网”；`:193` 和 parser `:265` 也有同族残留。

   **门未覆盖的路径：** 尝试获放行后，对端仍可能拒连，不能据 advisory 推断成功连接。

7. **LOW — 目录运行的真实退出码未保存，补正的解释也不成立。**

   位置：[unit-close-diff-r3:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/unit-close-diff-r3-20260914T233251.txt:22)、`:24–26`。

   存档撤销 `rc=0` 合理，但不能改称“实测为 1”。**对照输入：**

   ```sh
   zsh -f -c 'false | true | true; print -r -- $pipestatus[1]'
   ```

   实测输出 `1`：该索引取第一段，不是补正所称的第二段 `tail`。原退出码为何变成 `0`，指定证据不足解释；应保留为**未知／未正确记录**。这不直接推翻独立提取出的红项集合。

**你指定的字符与缩进矩阵如下。** `B/T/O` 分别表示正文、truncated、orphan；判断均发生在 `strip()` 之后。

| 输入形态 | 命中情况 | 实测结论 |
|---|---|---|
| 线程 `"\nworker"`／`"\rworker"` | 前段 T，后段 O | 拒判，原例核对通过 |
| 线程 `"worker\ncontinued"`／CR 等价 | 前段无，后段 O | 拒判 |
| 线程 `"worker\n- continued"`／CR 等价 | 两段均无 | 身份消失，可假绿 |
| 线程 `"worker\tcontinued"` | B | tab 保留，正常解析 |
| 线程 `"worker (owner=A)"` | B 提前截止 | 只剩 `worker`，既有歧义 |
| 线程 `"worker(owner=A)"` | B | 无前导分隔空格，该字面量保留 |
| 地址 `"ADDR\ncontinued"` | 前段无，后段 O | 拒判 |
| 地址 `"ADDR\n- continued"` | 前段无，后段 B | 地址前段丢失，可假绿 |
| 正文增加 captured-output 前导空格 | B | 缩进核对通过 |
| 空线程名 | 均无 | 身份消失，可假绿 |

相关位置为 parser `:102、107、115、136、227`。**不留下两个断口的损坏记录**，至少包括：续段以 `- ` 开头、owner 出现前已经截断、空身份字段，以及残段恰好满足正文正则。

**缺四元组即 rc=2，我倾向保留。** 指定真实存档中没有找到 final-only 实例；[目录档:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/unit-close-r3-20260914T232722.txt:19) 有合法汇总，fix-verify 中的 final-only 属于构造复现。

合法 final-only 输出与“足够完成本工具的比较”是两回事。[总账产出锚:1545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1545) 没有 advisory；缺它无法完成四元组比较。按模块描述的 summary→final 顺序，仅在 final 之后被杀，也不足以解释此前 summary 为什么缺失，还需考虑采集截断、缺流或绕过汇总的路径。本轮限定锚不足以确认具体生命周期实例。`blocked_count()` 可以继续提供局部计数，完整 CLI 比较应返回 `2`。

**整改与回归的核对结果：**

| 项目 | 独立结果与位置 |
|---|---|
| 一份／两份缺四元组 | **核对通过：CLI rc=2**；parser `:308` |
| advisory `0` 对 `12` | **核对通过：rc=1**；`:317–325` |
| `(12,0,12,0)` 与真正全零 | **核对通过：前者无 ZERO，后者有 ZERO**；`:330` |
| `final >= summary` | **核对通过：2→3 返回3，2→2 返回2，5→2 抛冲突**；`:200–213` |
| 算术自洽、重复汇总／总账 | **核对通过：不自洽及重复均抛冲突**；`:162、165、183` |
| final-only helper | **核对通过：仍返回 final blocked**；`:204–205` |
| R4/R4B、portal 两地址 | **核对通过：均 rc=0；portal 对 MainThread 为 rc=1**；`:147、318` |
| sha 三态与 conftest 路由 | **核对通过：五组合及原分流代码均正确**；[三态:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/hygiene_snapshot_tristate.py:53)、[路由:325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/conftest.py:325) |

另有两条**门未覆盖路径**值得登记：parser `:125、136` 全文去 ANSI 会同时抹掉字段自身的 ANSI 字符；`:102、229` 匹配到 `(owner=` 前缀便接受身份，不检查其后记录是否完整。这些没有另计 HIGH。

**版本与存档核对通过的部分：** 四源码工作区字节均等于审查 commit，SHA 分别匹配 `8cf9cb96…`、`e21500b4…`、`4da5db1c…`、`f0ca7225…`；三份守卫均与卡起点和 HEAD 相同。本轮 diff 只改 parser 与测试，全卡代码范围仍为四文件。

目录档独立数出 **64 个唯一红项＝35 FAILED＋29 ERROR，本卡测试零红**；源码有38个测试函数，[负控档:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/w4sr-negctl-r3-20260914T232637.txt:15) 记录38 passed。它们属于存档核验，本轮未重跑。原始基线集合不在读取面内，因此“逐项完全相同”仍只能确认其存档记载。

四份 evidence 均为未入该 commit 的工作区文件；审查期间目录档从86行增加到108行，追加了退出码及测试 SHA 的事后说明。最终读取快照 SHA 为 `d97380f6…fe19d6`；其中承认“事后测试 SHA 不能证明跑前版本”的限制成立。


