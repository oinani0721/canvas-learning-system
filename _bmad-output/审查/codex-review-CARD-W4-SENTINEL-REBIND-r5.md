> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-SENTINEL-REBIND round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-SENTINEL-REBIND-r5.md)"`
> 审查绑定: `3e10f587`（= 本卡代码最终 HEAD 之前一个 commit；其后仅一条 D-32 纯 docstring 尾巴 `dc90b622`，剥 docstring 后 AST 逐字节相同，见 evidence-w4-sentinel-rebind/d32-docstring-tail-ast-*.txt）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `provider: openai`（.stderr:6） / `sandbox: read-only`（.stderr:8）

---

**本轮 BLOCKER：0；HIGH：0。** 审查绑定 `3e10f587197508cee262d1a79977557a12466bd4`。

r4 的 HIGH-1 原例已关闭。本轮未找到需要新增计为 HIGH 的路径，**不触发你规定的“仍有 HIGH 即 D-15 停车”条件**。但验收证据的覆盖声明需要更正，下面列出可移交边界。

1. **MEDIUM — 孤儿兜底仍会条件性误伤合法回显。**

   位置：[w4_sentinel_identity.py:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:102)、`:327–332`。

   **对照输入**：正常 C 块及汇总，CLI 返回 `0`。  
   **负控输入**：只在 captured stdout 中额外回显同一条完整记录：
   ```text
   - ('::1', 7691, 0, 0) on thread MainThread (owner=x)
   ```
   实测变成 **rc=2 / CONFLICT**。甚至 `- cache on thread worker (owner=` 也触发，因为代码使用的是前缀 `.match()`，并非完整记录校验。

   因此，“满足这个形态就无疑义地来自产出方”不成立。**可登记移交为输入来源限制**；本次读取的目录存档没有证明这种误伤已经发生，不能把构造复现写成实际事故。

2. **MEDIUM — “全部 19 条对抗输入＋2 份真实存档”没有被该回归存档证明。**

   位置：[codex-r1to4-regression:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/codex-r1to4-regression-20260915T002400.txt:5)，至第 30 行。

   **对照检查**：实际只有 **18 条 `OK`**：14 条历史正文／噪声输入、2 条 formatter／干净跑对照、2 条真实存档结果。没有展示 advisory 差异、缺四元组、非零 advisory 标签、非法 UTF-8 等旧输入的重打结果，也没有完整执行命令和输入。

   此外，[负控档:132](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/w4sr-negctl-r5-20260915T002406.txt:132) 的四红分别是：空首段 LF、空首段 CR、孤儿记录、B 任意前缀，实际对应**三个问题类别**。

   **这是本卡收尾必须更正的验收声明**。关键旧门本次另行独立复核通过，不能由证据表述问题反推实现存在 HIGH。

3. **MEDIUM — 两次结果不同，尚不足以完成“不是本卡回归”的归因。**

   位置：[unit-close-diff-r4:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/unit-close-diff-r4-20260915T001049.txt:23)、`:25–36`。

   **门未覆盖的路径**：改动也可能引入或影响非确定性回归；同代码两跑一红一绿，并不能排除这种情况。模块不在 lifespan 导入链内，也未排除测试执行时序的间接影响。

   可支持的表述是“观察到同版本结果波动，未证明由本卡引入”。**归因调查可移交；本卡证据中的确定性结论应收窄。**

4. **MEDIUM — 已登记的字段歧义、部分账行漏收仍在，维持原分级。**

   位置：[w4_sentinel_identity.py:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:102)、`:170–174`。

   **未被拦下的输入**：线程名分别为 `worker (owner=A)`、`worker (owner=B)`，正常 C 块和四元组完全相同，两者均被截成 `worker`，真实 CLI 仍返回 **rc=0**；加入换行的同族变体也一样。

   但相同输入已在 [r2 审查:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/codex-review-CARD-W4-SENTINEL-REBIND-r2.md:48) 登记，[r3 审查:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/codex-review-CARD-W4-SENTINEL-REBIND-r3.md:49) 明确维持 MEDIUM。不能重新算成新增 HIGH。

   保留合法汇总、再追加缺右括号的损坏汇总，附加行仍会被忽略；这也属于此前登记的来源／部分漏收边界。**继续移交，不要求本轮扩修。**

5. **LOW — 机制说明仍残留旧实现描述。**

   位置：[w4_sentinel_identity.py:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:266)、`:268`，以及 [测试:446](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:446)。

   **对照输入**：块外完整记录会拒判，说明“块外根本不看”已不准确；“第一条 `- ` 行起”也没有描述当前固定偏移。可随收尾文字更正，不影响本轮代码分级。

关于①，**“记录起点是常量”在当前产出模板内核对通过，但不能扩大为并发存档保证**：

- **C 型核对通过**：[format_sentinel:1589](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1589) 无分支地放入抬头、两行说明，再遍历记录；当前 `+3` 成立。
- **A/B 型局部顺序核对通过**：[A:1545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1545)、[B:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/conftest.py:178) 的记录确实紧随抬头。但多次裸 `print` 不保证整个块连续输出；插入 `background log` 的负控返回 **rc=2**，属于保守拒判，可登记移交。
- **抬头字段核对通过**：给定模板里，`address/thread/owner` 均不进入抬头；C/B 使用常量原因及数量，A 使用计数与状态。未发现记录字段导致抬头换行的入口；A 状态值的上游链不在本轮读取面内。

其余核对结果如下，均区分了实际复现与存档记载：

| 项目 | 本轮结果 |
|---|---|
| r4 空首段 LF／CR、漂移块孤儿、B 任意前缀 | **核对通过**；当前拒判／忽略方向符合预期，入口在 parser `:296` |
| 四条普通噪声反向锚 | **核对通过**；没有恢复旧假红 |
| `blocked_count`、四元组 | **核对通过**；无输出为 `None`，合法增长可接受；倒退、重复账行、算术不洽均拒判 |
| 缺四元组 | **核对通过**；[新增测试:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:530) 的输入确实到达缺汇总分支，rc=2 |
| advisory、零标签、UTF-8 | **核对通过**；advisory 差异 rc=1；非零 advisory 不标 ZERO；非法字节 `80/81` 拒判 |
| owner／portal 归一 | **核对通过**；仅 owner、portal hex 漂移判同，线程类别不同判异 |
| SHA 三态与实际路由 | **核对通过**；[三态:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/hygiene_snapshot_tristate.py:53)、[conftest:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/conftest.py:324)：五组合及真实分流语句均正确 |
| 版本与测试数 | **核对通过**；四工作文件逐字等于审查 HEAD，hash 匹配 r5 证据；64 个测试函数加参数展开确为 67 例 |
| 负控、目录存档 | 存档中的 **67→4 红→67** 成立；目录档独立数出 **64 个唯一红项＝35 FAILED＋29 ERROR，本卡零红** |

真实 E2E 文件记载的 DIFFER／rc=1，以及“旧判据误报不同”的追加更正相互一致。**原始 r4c/r4d、原始基线未扩读，因此本次没有独立重算那一对真实存档或基线逐项 diff，也未核实其中是否存在裸记录回显。** 三份作废存档的自身声明已核对，未纳入当前验收依据。

本轮只读完成：未修改或暂存文件，未运行 pytest、hook 或连接数据库；CLI 复现使用内存管道调用原 `main()`。


