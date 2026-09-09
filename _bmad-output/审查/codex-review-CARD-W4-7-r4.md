**BLOCKER 0 / HIGH 0；不建议按“四条整改全部闭合”收口，仍有 MEDIUM 1、LOW 2。**

审 SHA：`3a9beaae80a1536ca064b422ba7f648ec29db405`。全程只读，未运行测试、探针、负控或连接端口。下面的新增反例均为静态推导。

1. **MEDIUM｜交叉参数化部分闭合，仍遗漏两种方法的独立行为。**

   **文件：**[test_live_port_guard_contract.py:772](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:772)，参数化在804、820行。

   **依据：**当前只有 `(__eq__, startswith) = (False, False)` 与 `(True, True)`，缺少两个混合组合。以下错误实现能通过全部八格，对普通字符串及普通子类也正确：

   ```python
   return str.__eq__(name, "uvloop") is True or (
       str.startswith(name, "uvloop.")
       and (not (name == "uvloop") or name.startswith("uvloop."))
   )
   ```

   对子模块，Denier 由 `not eq` 放过附加条件，Affirmer 由重载 `startswith` 放过附加条件。但当子类 **`__eq__` 恒真、`startswith` 恒假** 时，真实值 `"uvloop.loop"` 被错误放行。这是同一故障族的具体缺口，并非要求有限测试证明任意实现。

   作者对两个旧反例的更正成立：[r2负控:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-r2-med1-after4-20260909T132157.txt:8) 杀到 `uvloop.loop-denier`，[r3负控:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-r3-med1-after4-20260909T132157.txt:8) 杀到 `uvloop.loop-affirmer`，均为 `1 failed, 3 passed`。

   **建议：**补两种混合行为与四个真实值的交叉，并纳入上述负控。当前 guard 本身没有这个错误，无需据此修改它。

2. **LOW｜LOW-3a 未完全闭合：仍可能因参数漂移假绿，失败理由也未逐节点绑定。**

   **文件：**[r1-high-negctl.sh:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl.sh:100)。

   **依据：**102–109行只检查应失败参数出现、应通过参数不出现于 FAILED；没有确认实际 PASS，也没有拒绝未知参数。110–114行仍将所有失败正文合并计数。

   | 参数变化 | 当前裁定 |
   |---|---|
   | 删除／改名应失败参数 | 报红，要求维护预期映射 |
   | 删除／跳过应通过参数 | 可假绿：未执行被当成未失败 |
   | 新增未登记的失败参数 | 可假绿：额外 FAILED 无人检查 |
   | 新增未登记的通过参数 | 继续绿，但未完成预期绑定 |

   `rc == 1` 已正确拒绝2／3，却不能证明参数全部执行、各自结果及理由正确。正文命中总数足够，也不蕴含每个失败节点分别命中。

   **建议：**实际完整 nodeid 集合必须等于预期集合，逐节点核对 PASS／FAIL及失败理由，拒绝 SKIP／ERROR和未知节点。**维护性假红更安全**，它会阻止不完整证据被接受。

3. **LOW｜flaky 归因过强；“已排除本卡引入”未验证。**

   **文件：**[验收单:268](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/验收单/UAT-CARD-W4-7-2026-09-09.md:268)。

   **依据：**文件未改、无直接 guard 符号，不能排除全局门、传递调用或共享状态影响。单跑／双文件表现也不能单独证明因果；这些局部执行的原始日志未见于指定证据目录，记为**未验证**。

   更强的只读证据是：[after4:973](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/unit-after4-20260909T132157.txt:973) 的 candidate 失败来自 guard 结算 `('::1',7691,0,0)` 连接尝试，并非422断言；[基线:1575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/unit-before-20260908T173316.txt:1575) 的 mock 用例也是相同地址、MainThread及 Neo4j health-check 初始化签名。它支持“共享初始化的失败归属随时序变化”这一解释。

   三份日志都先运行 candidate，再运行 guard contract，最后运行 mock 用例。因此，本轮新增参数的**执行**不能直接导致此前的 candidate 失败。这支持“未发现本轮增量引入回归”，仍不足以排除整张卡的历史改动影响。

   已独立复算：after4确实一增一减；after5与基线的 **FAILED／ERROR nodeid 集合**相同，均202条。“diff空”不适用于全文或完整测试结果。

   **建议：**收窄为“支持共享初始化／时序假说，非本卡引入的严格因果排除未验证”，保留异常样本。无需为此扩审或修改 `backend/app/**`。

4. **原 MEDIUM-2｜已闭合，未发现当前基线漏验仍返回0的路径。**

   **文件：**[m4-importlib-probe.py:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-probe.py:101)，裁定在188–201行。

   **依据：**只有导入正常返回才置 `_imported=True`；裁定同时要求 `import_succeeded is True` 和事件非空。缺裁定行、子进程非零已先被164–171行拒绝。当前固定 CASES 包含基线，因此189行的条件分支没有形成当前可达漏验路径。

   [after4:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-after4-20260909T132157.txt:28) 同时记录成功导入、模块路径、五个事件及rc=0。

   **建议：**维持闭合，结论限定为归档环境和观察窗口；不扩大为所有 Python／uvloop／loader 组合的证明。

5. **原 LOW-3b｜假成功退出路径已闭合；有重复还原的小问题。**

   **文件：**[r1-high-negctl.sh:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl.sh:77)。

   **依据：**INT／TERM已显式退出130／143，不再沿用先前成功状态。但两个信号处理器仍先还原，随后EXIT又还原一次；第一次删除备份后，第二次复制会失败。正常还原情况下仍保持非零退出，不构成原来的假绿。实际信号执行结果**未验证**。

   **建议：**INT／TERM只输出消息并退出，让EXIT唯一负责还原；该清理不新增生产缺陷计数。

6. **原 HIGH｜维持闭合；本轮未发现新增 BLOCKER／HIGH。**

   **文件：**[live_port_guard.py:563](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:563)、[live_port_guard.py:738](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:738)。

   **依据：**`ad4c853b..审SHA` 的guard与探针脚本diff为空；`BaseException`捕获及未绑定字符串判据仍在。[HIGH-1负控:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-r1-high1-after4-20260909T132157.txt:8) 包含三个参数各自指定异常，[HIGH-2负控:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-r1-high2-after4-20260909T132157.txt:8) 包含两个指定失败；还原哈希与当前guard一致。

   **建议：**保留前三轮已闭合HIGH及其他未被推翻的结论。**0／0门槛仍满足；若按本轮“四条全部整改”口径收口，本卡仍应补齐第1、2条，并修正第3条归因声明。**
