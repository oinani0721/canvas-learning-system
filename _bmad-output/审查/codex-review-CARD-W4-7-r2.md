> 批次: BATCH-2026-09-07-第十三批 · 车道 U7（`card-u7-w4guard`） · 卡 CARD-W4-7 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/codex-prompt-CARD-W4-7-r2.md)"`
> 审查绑定: `001a8271`（跑时 HEAD `001a8271` —— 同审 SHA）
> 会话头自证（抄 `codex-review-CARD-W4-7-r2.stderr` 会话头含 model 行的三行，stderr 本身不入库；该文件**字面前三行**为 `Reading additional input from stdin...` / 版本行 / `--------`，不含 model 行，故按规则「含 model 行」抄取三要素并标注实际行号）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

BLOCKER 0 / HIGH 0。

审查绑定 `001a8271fae56853f8f808ba05d0d67143695743`。两条原 HIGH 在真实 tuple／str 子类输入域内闭合；仍有 **MEDIUM 2 / LOW 1**。全程只读，未运行测试、探针或负控，未连接端口。以下按未闭合问题优先排序；“原级别”不计入本轮未闭合数量。

1. **MEDIUM：说谎子类用例的拒绝方向覆盖不足。（问题 4）**

   依据：[test_live_port_guard_contract.py:749](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:749) 的两个方法分别取反。对 `_Liar("uvloop")`：

   - `__eq__("uvloop")` 返回 `False`；
   - `startswith("uvloop.")` 返回 **`True`**，因为原字符串本来就不以带点前缀开头。

   所以即使错误地改回绑定调用 `name == "uvloop" or name.startswith("uvloop.")`，`:764-765` 的正向仍绿；后面的 `"json"` 方向才会红。**整条测试不是恒真，但两个方向没有分别证明注释声称的性质。**

   更明确的静态反例是：

   ```python
   str.__eq__(name, "uvloop") is True or (
       str.startswith(name, "uvloop.") and name.startswith("uvloop.")
   )
   ```

   该错误实现可满足现有普通子类、`_Liar("uvloop")`、`_Liar("json")` 用例，却放行 `_Liar("uvloop.loop")`。这是静态推导，未执行变异。

   四条新增门的检出能力如下：

   | 新增门 | 什么情况下会红 |
   |---|---|
   | [BaseException 门:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:101) | 退回只捕 `Exception`，三种异常不能正常返回 `None`；可能表现为失败或会话中断。 |
   | [近似哨兵门:600](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:600) | 改成后缀匹配，把无 NUL 的近似名字判为自证。 |
   | [普通 str 子类门:712](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:712) | 退回精确类型检查，两个参数均不再抛规定的拒绝异常。 |
   | [说谎子类门:735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:735) | 放行真实 `"uvloop"`，或误拦真实 `"json"`；但未覆盖说谎的子模块前缀拒绝路径。 |

   **建议：**拒绝方向使用两个方法恒返回 `False` 的子类，参数化 `"uvloop"`／`"uvloop.loop"`；误拦方向另用恒返回 `True` 的子类。

2. **MEDIUM：自我更正只有“装门后一条”得到获准证据支持。（问题 6、7）**

   [after2 输出:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-after2-20260909T112753.txt:22) 明确记录 `importlib__poison-removed` 被本门拒绝、事件为 `['uvloop.includes']`、子进程 rc 为 0。这部分更正准确。

   但 [m4-importlib-probe.py:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-probe.py:46) 无条件 `g.install()`，`:51-84` 的四种形态均装门。获准 after2 输出没有无门分组。因此以下两处“**不装门时观测到的完整四条序列**”仍是**未验证**：

   - [live_port_guard.py:710](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:710)
   - [test_live_port_guard_contract.py:692](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:692)

   后者引用的 `m4-importlib-r2-*.txt` 不在本轮指定读取列表，未读取。

   **建议：**补充获准的无门观测记录，或将该半句标为未验证；“装门后只会看到第一条”也应限定为此次环境和 `importlib__poison-removed` 形态。单靠改写注释，尚不能关闭这项证据缺口。

3. **LOW：新负控脚本仍可能错误归因，但不推翻本次已保存的具体失败。（新增问题）**

   [r1-high-negctl.sh:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl.sh:50) 未保存 pytest 退出码；`:54-56` 从**整个输出**寻找期望串，再配合泛化的 `N failed` 判通过。它没有强制要求指定失败节点及异常正文命中。

   HIGH-1 的期望文字本身位于测试源码中；`--tb=long` 打印源码上下文时，即使失败另有原因，也可能满足字符串条件。

   不过，本次记录能独立核对：
   
   - [HIGH-1 输出:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl-r1-high1-after2-20260909T112753.txt:5) 有准确节点及 `E SystemExit` 正文。**只显示一个参数失败**，另外两个参数的实跑结果未验证。
   - [HIGH-2 输出:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl-r1-high2-after2-20260909T112753.txt:5) 有两个准确节点及两条 `DID NOT RAISE`。
   - [negctl_patch_w47.py:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl_patch_w47.py:43) 的两个变异确实恢复对应修前实现。记录中的还原哈希也与当前 guard 文件一致。

   **建议：**保存 pytest 退出码，绑定准确失败节点，并将拒因匹配限定于异常正文。

4. **原 HIGH-1：整改闭合；不能扩大成“任意输入绝不抛异常”。（问题 1）**

   [live_port_guard.py:555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:555) 使用未绑定的 `tuple.__len__`／`tuple.__getitem__`，索引是固定整数 `1`。对真实 tuple 及其子类，**不会执行子类重载的读槽位方法**，所以 `:559` 无需机械改成 `BaseException`。

   执行端口用户代码的 `operator.index(raw)` 已被 `:561-579` 的捕获完整包住。异常后返回 `None`，该端口对象又被 `port_is_trustworthy` 判为不可信，随后到达 [记账位置:800](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:800)。

   剩余输入边界是 `:553`：`isinstance(address, tuple)` 在 `try` 外，非 tuple 对象的自定义 `__class__` getter 仍可能抛异常。因此“还有没有异常逸出路径”的严格答案是**有，但不属于上述真实 tuple 子类读槽位路径**。它能否构成真实受拦 TCP 连接的漏账，本轮材料未验证，不据此新增 HIGH。

   **建议：**明确有效地址域；若要求函数覆盖任意对象，再消除动态 `__class__` 判定，不能只修改 `:559`。

5. **原 HIGH-2：整改闭合；未发现新增合法模块名误拦。（问题 2、3）**

   [live_port_guard.py:732](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:732) 对真实 `str` 及其子类直接调用基类方法，子类重载的 `__eq__`／`startswith` 不参与判断。

   各输入形态的边界：

   | 形态 | 当前判定 |
   |---|---|
   | 真实 `str` 子类，包括重载比较方法者 | 按真实字符串内容判断。 |
   | 非字符串通过 `__class__` 伪装为 `str` | 可能通过 `isinstance`，随后基类描述符因接收者类型不符抛 `TypeError`；不是放行。 |
   | 普通 `UserString`、`bytes`、`bytearray` | 返回 `False`；此处不做字符串转换。 |
   | 输入类型自定义 `__instancecheck__` | 不是这里的控制点；检查对象是第二参数 `str` 的元类。 |

   在真实字符串接收者与固定右操作数 `"uvloop"` 下，`str.__eq__` 返回布尔值，**不会出现 `NotImplemented`**；伪装接收者导致的是 `TypeError`。因此 `is True` 在当前调用中冗余但无害，也不能替代接收者类型保障。伪装对象进入真实导入路径的可达性，本轮未验证。

   当前匹配集合恰是 `"uvloop"` 或 `"uvloop."` 开头。[四个 lookalike:772](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:772) 足以检出裸前缀、包含关系等常见错误，不能视为穷尽证明；未绑定方法的明确比较规则支持这里的静态结论。

   **建议：**保留当前真实字符串判据，补第 1 条的子模块说谎用例；若要求处理任意合成审计输入，再单独明确非字符串异常策略。

6. **原 MEDIUM：M4 跑器所述三种条件性假通过已关闭。（问题 5）**

   [m4-importlib-probe.py:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-probe.py:133) 的控制流明确：

   - 缺裁定行、任一子进程非零：返回 2。
   - 去毒化后导入成功：返回 1。
   - 去毒化后既非成功、又无本门拒因：返回 2。
   - 两个去毒化形态均匹配本门拒因：才返回 0。

   当前 `CASES` 固定包含两个去毒化形态，不能把假设删除 case 后的空集合问题当作当前运行路径。JSON 错误、缺字段、超时也不会正常走到返回 0。

   **但“彻底”的范围有限：**`:144` 仍以拒因子串归因，`:126` 仅打印事件列表。其他来源的异常若携带同一拒因文字，判据仍可接受；该运行反例未验证。返回 0 因而不能单独证明事件列表非空、事件来源或四条序列。

   **建议：**将结论限定为现有两条去毒化路径的拒因验证；需要证明事件行为时，另加对应断言。

7. **原 LOW 已恰当处置；事件来源措辞的收窄基本成立。（问题 7）**

   [哨兵断言:571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:571) 的精确 `str` 加首字符 NUL，确实蕴含末三条断言。注明它们没有独立检出能力是准确处置；这里原本是检出能力表述问题，加注足够。

   [近似哨兵负例:608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:608) 则实际加入了无 NUL 输入，能检出后缀匹配错误，属于实质补门。

   [事件来源说明:704](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:704) 已明确否认“只有 `__import__` 发事件”，承认缓存及 Python／uvloop／loader 组合的未证明边界。该收窄合理；仍未关闭的是第 2 条“无门完整四条”的证据声明。

   **建议：**保留两项 LOW 的现有处置，将事件观察陈述逐一绑定具体形态与获准记录。


