> 批次: BATCH-2026-09-07-第十三批 · 车道 U7（`card-u7-w4guard`） · 卡 CARD-W4-7 round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-7-r5.md)"`
> 审查绑定: `b9ba828b`（跑时 HEAD `e9a68b78` —— **不同**：跑时 HEAD 为 `e9a68b78`（只动 `_bmad-output` 的存档 commit），代码树与审 SHA 等价（实测 `git diff --stat b9ba828b e9a68b78 -- . ':(exclude)_bmad-output'` rc=0 且空））
> 会话头自证（抄 `codex-review-CARD-W4-7-r5.stderr` 会话头含 model 行的三行；该文件**字面前三行**不含 model 行，故按 §2.1「含 model 行」抄三要素并标实际行号）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

**BLOCKER 0 / HIGH 0；0/0 审查门达标，但现有证据不足以按完整验收口径直接收口。**

本轮全程只读，未运行测试、探针、负控或连接端口。新增反例均为静态推导，运行结果**未验证**。

1. **MEDIUM｜结构门没有关闭整族，只拦住了特定直接语法。**

   **文件：**[test_live_port_guard_contract.py:853](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:853)，另见865、873行。

   **依据：**前两条只识别直接拼写为 `name` 的 `ast.Name`；第三条只要求某种调用出现。以下改写能绕过三条规则：

   ```python
   if not isinstance(name, str):
       return False
   alias = name
   return str.__eq__(name, "uvloop") is True or (
       str.startswith(name, "uvloop.")
       and (not (alias == "uvloop") or alias.startswith("uvloop."))
   )
   ```

   现有八格按逻辑仍通过；但对 `__eq__` 恒真、`startswith` 恒假的子类，真实值 `"uvloop.loop"` 仍被放行。当前 guard **没有**这段错误实现。

   对你列出的其他写法：

   | 写法 | 当前结构门 |
   |---|---|
   | 先赋给局部别名再操作 | 漏检 |
   | `getattr(name, "startswith")(...)` | 前两条漏检 |
   | `operator.eq(name, ...)` | 前两条漏检 |
   | `"uvloop" == name` | **会拦**，865行检查左右两侧 |
   | f-string／`"%s" % name` | 前两条漏检，可触发子类格式化／字符串转换 |

   后三种漏检路径只需保留原未绑定调用，就满足第三条。

   **建议：**本卡将“整族关闭”改为“拦住三个历史反例的直接写法”，保留 MEDIUM。若继续追求整族保证，应针对这个短函数约束完整允许语法、方法和返回值依赖，不能继续把局部语法扫描称为全称证明。

2. **LOW｜不挑样本的处理可接受；“非本卡引入”和替换原验收门仍不成立。**

   **文件：**[验收单:315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/验收单/UAT-CARD-W4-7-2026-09-09.md:315)，另见333–340行。

   **依据：**独立复算八份日志，确实每份都是 **202 个唯一 FAILED／ERROR nodeid＝173 failed＋29 errors**；交集201、并集203，只有两个节点二选一，分布6∶2。应称“红集大小恒202”，不能称“红集相同”。

   更强的只读证据也成立：

   - [基线:1575](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/unit-before-20260908T173316.txt:1575) 与 [final:973](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/unit-final-20260909T144035.txt:973) 都是哨兵结算一次 `('::1',7691,0,0)`、MainThread 的连接尝试，业务断言不是失败原因。
   - 八跑账本均为 **12 attempts／12 blocked／0 advisory／0 unaccounted**。
   - candidate 均先于 guard contract 执行，新增结构门的**测试体执行**不能导致此前的 candidate 失败。

   这些支持归属漂移假说。但开工基线只有一跑，只展示了其中一种归属；不能由“跨基线”推出“本卡改动前已经发生同样的双向漂移”。整卡因果排除仍是**未验证**。

   **建议：**保留全部八次样本及315–318行的窄结论。336–340行不能用三条统计不变量自动替代“任何新增 `>` 即阻断”的原门槛；指定证据内未见正式例外。漂移根因调查可另立卡。

3. **LOW｜最终 HEAD 的完整执行绑定未验证，且脚本修复不在 `b9ba828b` 提交内。**

   **文件：**[验收单:331](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/验收单/UAT-CARD-W4-7-2026-09-09.md:331)、[r1-high-negctl.sh:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl.sh:89)。

   **依据：**当前 HEAD 为 `e9a68b78`。`b9ba828b → e9a68b78` 的 guard、契约测试及主探针相同；但 `r4-med1`、三个 `struct-*` case 和单次还原修复实际在后者才进入 Git。

   final 日志未记录 HEAD、工作树状态或完整输入摘要。三个结构负控的还原 SHA 与当前 guard 相同，能绑定**guard 单文件**，不能独立绑定整套执行输入。验收单286行“最终裁判”还指向旧版本。

   **建议：**明确区分被审代码版本、负控脚本版本和归档版本；如有既存运行记录则补引用，否则登记“完整执行绑定未验证”，不要通过补写声明冒充历史证据。

4. **LOW｜结构门存在误拒；`casefold` 示例取决于写法。**

   **文件：**[test_live_port_guard_contract.py:865](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:865)。

   **依据：**

   - `str.casefold(name) == "uvloop"`：**不会被拒**，比较操作数是 `Call`。
   - `name = str.casefold(name)` 后再比较 `name`：会被拒，规则不认识重新赋值后的安全结果。
   - `name is None`：也会被拒，尽管身份比较不调用重载 `__eq__`。
   - 安全的未绑定方法别名也可能因第三条要求固定语法而被拒。

   **建议：**将其定位为实现形态约束，合法重构时同步复核规则。是否允许模块名忽略大小写属于另外的行为契约，不能由结构门通过与否决定。

5. **INFO｜三条规则分别有作用，第三条不足以防止实际判据被删掉。**

   **文件：**[test_live_port_guard_contract.py:850](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:850)。

   **依据：**以下“单独红”仅指三条结构子规则之间：

   | 子规则 | 仅该规则红的改动 |
   |---|---|
   | 禁属性接收者 | r2 变体：保留未绑定调用，子模块分支追加 `and name.startswith(...)` |
   | 禁 Compare | r3 变体：保留未绑定调用，追加 `and not (name == "uvloop")` |
   | 必须存在未绑定调用 | 整个函数改为 `return False` |

   但保留类型检查后写成：

   ```python
   str.__len__(name)
   return False
   ```

   三条结构规则都会通过。不可达代码中的调用同样能满足第三条。它没有限定方法名、可达性或返回值依赖；恒假实现需要行为测试来拒绝。

   已归档的 [struct-r2:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-struct-r2-final-20260909T144035.txt:11)、[struct-r3:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-struct-r3-final-20260909T144035.txt:11)、[struct-r4:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/negctl-struct-r4-final-20260909T144035.txt:11) 分别命中**属性、比较、属性**规则。r4 在第一条已经失败，没有独立验证后两条；第三条单独承重的运行证据**未验证**。

   **建议：**保留这三份具体负控证据，收窄其证明范围。

6. **INFO｜未发现新增运行时 BLOCKER／HIGH；既有 HIGH 维持闭合。**

   **文件：**[live_port_guard.py:563](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:563)，另见735–738行。

   **依据：**确认 guard 与 `backend/scripts/lifespan_isolation_guard_probes.py` 自既审版本未改；`BaseException` 捕获及未绑定字符串判据仍在。指定增量确实只有测试文件新增59行。归档 final 记录契约151 passed、探针59/59；这些是日志核验，没有本轮重跑。

   当前归档脚本的 INT／TERM 只退出130／143，EXIT 唯一负责还原，LOW-3b 的重复还原已在源码层修正；实际信号执行**未验证**。

   LOW-3a 仍存在：未确认应通过节点实际 PASS、未拒未知节点、失败理由仍汇总计数。“维护性假红更安全”原意支持严格检查，不能用来说明现有检查已消除假绿。

   **建议／收口判定：**可登记移交 LOW-3a 和进一步结构门加固，不要求因此修改当前正确 guard 或启动第六轮。本卡仍须准确登记：
   **整族封闭未成立、整卡漂移因果未验证、完整执行绑定未验证。** 原新增红门是否存在获准例外也尚未得到证据支持，因此本轮可以给出 **0/0 达标**，不能同时给出**完整验收 PASS**。
