> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-SENTINEL-REBIND round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-SENTINEL-REBIND.md)"`
> 审查绑定: `86535afb`。本轮 BLOCKER=0 / HIGH=3，三条均独立复现属实并整改，新 HEAD `5c696c92` 已另送 round-2
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:4） / `model: gpt-6-astra`（.stderr:7） / `reasoning effort: ultra`（.stderr:11）

---

**本轮 BLOCKER：0；HIGH：3。审查 SHA：`86535afb`，目前不能判定复核通过。**

复现均在内存中执行该 SHA 的解析器；未修改文件、运行 pytest/hook 或连接数据库。下面区分实际复现、存档记录和未覆盖路径。

1. **HIGH — CLI 没有比较四元组，更正⑥的实现自述不成立。**

   位置：[w4_sentinel_identity.py:232](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:232)、`:269-271`。`_describe()` 丢掉四元组，CLI 只比较 `blocked` 和正文集合。

   对照输入与负控输入分别是：

   ```text
   NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
   NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=0, advisory=12, unaccounted=0)
   ```

   **实测 rc=0，输出 `CONSISTENT`。** 两份各自算术自洽，但新增的 12 次 advisory 未进入比较。现有测试 `test_w4_sentinel_rebind.py:169-174` 只证明 helper 能区分，没有验证 CLI 拦截。

   `live_port_guard.py:230` 的“只记不拦”**核对通过**；不过这证明连接尝试被放行，不能证明实际连接成功。

2. **HIGH — 有效零汇总不等于“门已安装且本轮已查完”，安装状态及 worker 覆盖没有进入判定。**

   位置：[w4_sentinel_identity.py:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:188)、`:264-267`；输出事实依据为 `live_port_guard.py:446、454-461`。

   **门未覆盖的路径：** 未安装状态仍提供全零汇总，或 xdist 存档只有主进程全零汇总、worker 账本缺席。解析器均会把这条汇总当有效 `0`；两份这样的输入实测 **rc=0**。即使输入额外明确写着 `installed=False`，结果也不变。

   无门行返回 `None`、CLI 返回 `2`，这一**语法层区分核对通过**；但“匹配到零”不能升级为安装与完整覆盖证明。本轮没有实际启动 xdist，也没有证据证明现有目录跑漏装了门；这里指出的是判据未覆盖的输入路径。应明确单进程输入契约，并另验安装及运行来源；worker 场景须覆盖各自账本。

3. **HIGH — 含空格线程名会静默丢失正文，地址变化仍可假绿。**

   位置：[w4_sentinel_identity.py:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:97)、`:207-211、270-271`。

   两份输入保留相同的有效 `blocked=1` 汇总，正文分别为：

   ```text
   - ('::1', 7691, 0, 0) on thread Thread-1 (worker) (owner=x)
   - ('127.0.0.1', 7687) on thread Thread-2 (worker) (owner=x)
   ```

   **实测两份身份集合均为空，CLI rc=0。** `\S+` 无法接收完整线程名，解析失败又没有进入 unchecked。

   非贪婪也不是“不切入 owner”的无条件保证：上述线程名后若跟 `(owner=test[a on thread b (owner=c)])`，正则会继续寻找可匹配分隔符，最终把真实线程名及部分 owner 收进地址身份。应对无法解析的候选正文明确拒判；不需要恢复 `正文条数 == blocked`。

4. **MEDIUM — portal 之外仍保留跨跑变化量，裸 repr 也不保证稳定或无歧义。**

   位置：[w4_sentinel_identity.py:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:100)、`:129、210`。

   **负控／对照实测：** 同地址仅把 `Thread-1` 改成 `Thread-2`，CLI 返回 `1`；地址中的 `<Port object at 0x1234>` 改成 `0x5678`，也返回 `1`。`live_port_guard.py:527-528` 明确涉及支持 `__index__` 的端口对象，因此语义相同的端口不保证裸 repr 相同。

   地址自身含 ` on thread Decoy (owner=` 时，还能使身份提前截断。这里是列举剩余输入面；指定存档没有证明这些形态已在本次目录跑出现。更正④对已展示的 `asyncio-portal-<hex>` 归一**核对通过**，但不能据此声称全部身份跨跑恒定。

5. **MEDIUM — 部分门行漏收可能假绿；`final >= summary` 也不能证明来源一致。**

   位置：[w4_sentinel_identity.py:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:76)、`:88-92、182-195`。

   **负控实测：** 对照仅有裸 `summary blocked=1` 和正文；负控保留两者，再加入带 `stderr_tail = ` 前缀的 `final blocked=2`。总账被忽略，两份仍 **rc=0**。如果所有门行都带前缀，则返回 `None`、rc=2，方向是保守拒判。由此，漏收并非总是假红。

   另外，`_FINAL_RE` **只有左锚，没有右锚**；截到 `reported_status=garbage；` 仍可读出数字。“两个正则都是整行锚”不准确。原样抄入的完整汇总也无法仅凭整行匹配区别于真实产出。

   **未被拦下的混档输入：** A 跑的 `summary=2` 加 B 跑的 `final=3`，仍返回 `3`。数值单调只是必要关系，不能证明同一次运行、同一 STATE。也不宜用文本排列顺序代替来源证明，因为 stdout/stderr 缓冲可能改变排列。

6. **MEDIUM — 负控和目录跑的 parser 哈希未绑定审查版本。**

   位置：[w4sr-negctl-identity-20260914T224508.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/w4sr-negctl-identity-20260914T224508.txt:2)、`:18`，以及 `unit-close-clean-20260914T225233.txt:3`。

   **对照输入：** 存档记录 parser SHA-256 为 `73c5fa34…41bc46`；我独立计算 `86535afb` 中该文件为 `2a16b6f7…897bf`，当前文件也为后者。

   因此这些运行不能直接作为审查版本 parser 的验收证据。它们可以证明旧版本的过程结果；要绑定当前版本，需要对应版本的验证记录。

7. **LOW — 两处文字与实际行为冲突。**

   [unit/conftest.py:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/conftest.py:83) 仍写“前后同为 None 即视为未变化”；**对照输入 `None,None`** 实际走 `cannot_check`。

   [unit-close-diff-20260914T225819.txt:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/unit-close-diff-20260914T225819.txt:39) 至末尾同时记录 rc=0，却解释成应当 UNCHECKED、汇总带上下文。**原始对照行 `unit-close-clean:1118` 是完整裸零汇总**，正常匹配；摘录中的 `1118:` 是行号。这份实际存档不支持“真产出被整行锚拒收”的解释。

对问题①，三条更正的独立核对结果如下：

- **更正③核对通过。** `live_port_guard.py:1551、1595` 和 `backend/tests/conftest.py:184` 确实是三处正文产出；重复输出使正文行数不能直接对应 blocked，集合去重有依据。
- **更正④对 portal 形态核对通过。** `normalise_thread()` 保留 MainThread／portal 类别差异。普通无空格线程名下，owner 含两个分隔符的对照也通过；限制见 HIGH-3。
- **更正⑤局部依据核对通过，完整链条未独立确认。** `:282` 初始化、`:355/:361` 两处递增、`:454-461` 锁内读取，以及根 conftest `:226-227` 的调用点均已核对。但指定读面没有 `finalize_and_snapshot()` 实现、最终 `blocked` 的赋值来源和 atexit 注册代码，不能独立确认“全文件无其它写入”及完整先后链。

**若 final 是同一 STATE 在 summary 之后取得的快照，`final >= summary` 成立；快照本身不推翻这个关系。** 它不能证明快照之后没有新增记录。若实际使用更早的快照，则合法运行也可能 `final < summary`，当前工具会误报冲突。重复打印同一 summary 的负控已确认会抛异常、走 rc=2；不会静默选择其中一条。

对问题④，**三态函数及路由核对通过，失败方向可接受。** `hygiene_snapshot_tristate.py:53-55` 的五种组合正确，`unit/conftest.py:319-333` 正确分流；diff 显示 exists 分支和“环境受干扰”告警未改。

两侧不可读导致 session 检查失败，符合 `unit/conftest.py:304` 的既有契约；应解释为“卫生检查无法完成”，而非认定测试污染。更好的诊断是保留异常类型／errno，并在开跑时报告已知不可读。符号链接本体变化但目标内容相同，仍不在当前内容哈希的覆盖范围内。给出的两组路径确实不相交，但常量定义不在授权源码窗口，不能把 docstring 自述当作独立源码核验。

存档确有 **28 项通过**；干净目录跑可独立数出 **64 条唯一 FAILED/ERROR，新测试零条红**。基线集合未在读取面内，所以只能确认存档记载 `diff_rc=0、>/< 均为零`，不能独立重算两集合完全相同。作废登记关于“首尾哈希相同不能证明期间无人读到变异态”的判断正确；这些历史记录不消除上述当前实现的负控结果。


