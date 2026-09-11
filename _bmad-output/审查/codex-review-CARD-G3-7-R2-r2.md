> 批次: BATCH-2026-09-07-第十三批 · 车道 U9 · 卡 CARD-G3-7-R2 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-7-R2-r2.md)"`
> 审查绑定: `65e18d04d038ac0e3a47119be737a01e6622c277`（Codex 自行 `git rev-parse HEAD` 两次核对，见其正文首句）
> 会话头自证（抄 .stderr，stderr 本身不入库；本跑 stderr 前几行混有 models_manager 非致命 ERROR，故抄第 1 行与第 7/11 行的 model/effort 自证行）:
> `Reading additional input from stdin...` / `model: gpt-6-astra`（stderr:7）/ `reasoning effort: ultra`（stderr:11）

---

复核绑定：`HEAD 65e18d04d038ac0e3a47119be737a01e6622c277`，已两次核对一致。全程只读，未修改文件、连接数据库或运行测试／脚本。**没有已核实的新增 BLOCKER／HIGH，但不能判定五条整改全部闭合。**

代码按该提交读取；指定 `_bmad-output` 材料不在该提交树中，以下将其作为本次读取的外置证据核验。

**MEDIUM**

**1. [test_mastery_fsrs_projection_boundary.py:140](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:140)：`open` 整改引入了模块函数调用的参数错位。**

代码把所有 `ast.Attribute` 都当成绑定方法，取 `args[0]` 为 mode。但 `io.open`、`builtins.open` 的第一个参数仍是路径。

| 静态反例，未执行 | 实际行为 | 当前检查结果 |
|---|---|---|
| `io.open("notes.md", "w")` | 写文件 | **漏报**：将 `"notes.md"` 当 mode，其中没有 `wax+` |
| `builtins.open("notes.md", "w")` | 写文件 | **漏报**：同上 |
| `io.open("card.md", "r")` | 只读 | **误报**：文件名中的 `a` 被当成追加模式 |

这些普通调用在旧版取第二参数时能正确判断。**这是整改回退，不能归入 import 别名或动态调用盲区。**

**2. [test_mastery_fsrs_projection_boundary.py:241](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:241)：两档名单与回调扫描没有完整衔接，仍存在普通静态写入漏报及读取后处理误报。**

`:245–249` 的回调扫描只接受第一档，未对第二档调用现有接收者判断。因此：

- `asyncio.to_thread(os.replace, a, b)`、`asyncio.to_thread(json.dump, obj, fh)` 均漏报，尽管 `os`、`json` 已在可识别模块名单中。
- `from os import replace; replace(a, b)` **没有使用别名**，仍因 `:242` 必须是 `Attribute` 而漏报。
- `file_text = Path(p).read_text(); file_text.replace("a", "b")` 会因变量名包含 `file` 而误拦；反过来，`p = Path("notes.md"); p.replace(q)` 因名字 `p` 没有提示片段而漏报。
- 新增第一档的 `copyfileobj` 也并非只操作文件系统：两个 `io.BytesIO` 之间的 `shutil.copyfileobj(...)` 是内存复制，当前仍会报写盘。

验收单 [§10.9:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md:211) 承认非穷尽检测，这部分诚实；但“新增写法时门会红一次”仍不成立。尤其第二档回调遗漏，是现有规则没有接入该分支。

**3. [census:86](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:86)：新增 API 面只搜索 `backend/app`，尚未补齐定义中的全仓普通静态消费。**

定义 `:17–21` 没有排除 `scripts`、`backend/lib`，但这些目录在 `:198–212` 仍只扫旧字符串。若其中出现普通 `svc.get_fsrs_state(cid)` 或 `svc.record_review_result(...)`，该取数方法依然会漏掉；新增 §七.7 没有明确列出这个目录覆盖缺口。

**没有发现实际第二个消费文件，不能据此判定数值 1 错误。** 因 `:246` 已明确撤回“完整总数为 1”的主张，本轮不维持原 HIGH 定级；但 HIGH-1 只能判为“实质补证＋结论收窄”，不能判为“完整 census 已证明”。

**4. [docs/fsrs-truth-source-d0-revision.md:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/docs/fsrs-truth-source-d0-revision.md:68)：生产检索范围已改正，历史结论仍比证据宽，且所列历史命令路径不准确。**

“全仓 0”改成 `backend/app` 零命中，成立。但仍断言 Requirement 与实现“**从未一致**”；当前标识符不存在，加上单文件、单标识符的历史搜索，不能独立证明整个实现历史。

此外，文档写的是 `git log -S'_legacy_card_states' -- review_service.py`；从指定仓库根执行，该路径不指向实际生产文件。相比之下，[census:255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:255) 记录了完整的 `backend/app/services/review_service.py` 路径。两处没有做到“实际命令”一致。

**LOW**

**5. [census:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:32)：错误的“N 恒等于 0”论证仍作为正文保留。**

`:36` 的更正明确、方向正确，但前面原句没有删除或标为作废，形成前后矛盾。因此是“已撤回错误结论，正文清理未完成”。

**6. [test_mastery_fsrs_projection_boundary.py:327](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:327)：说明仍引用已删除的 `BANNED_WRITE_CALLS`。**

另 `:293–294` 所称矩阵“前四条早前全错”不准确：前两条内建 `open` 在旧版已经正确。模块开头的旧计数门说明则确实已修好。

**已核实成立的整改**

| 对应意见 | 核验结果 |
|---|---|
| **HIGH-1** | census 确实新增方法表、逐方法调用表及第三个调用点，并在 `:246` 明确限定 N 的含义。**不是仅换说法**；但表内枚举真实性与完整性仍未独立核实。 |
| **MEDIUM-2** | 原 `Path(p).open("w")` 漏报、`Path(p).open("r", -1)` 误报、读取后直接链式 `.replace(...)` 误报，以及 `to_thread(Path(p).write_text, data)` 漏报，按当前分支推演均已修复。 |
| **MEDIUM-3** | [测试:638](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:638) 先追加 `touched` 再抛异常，`:646` 独立断言空列表。只要调用触达被替换的 getter，即使业务吞掉异常，计数仍会使测试失败。 |
| **MEDIUM-4** | D0 文档明确改为生产目录 `backend/app`，并承认文档／spec 中仍有这些标识符。原“全仓 0”错误已解决；历史绝对结论问题见上。 |
| **LOW-5** | [mastery_engine.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/app/services/mastery_engine.py:295) 已改用函数名锚。门文件模块 docstring 也已正确描述“可执行代码引用检查”，与 `:342–375` 实现一致。两个读方函数体是否仍符合描述，见未核实项。 |

**16 条矩阵逐条静态推演均与其预期一致**：按 `:297–312` 顺序，命中的是第 **1、3、8、9、10、12、13、16** 条，其余放行。这不代表所有 round-1 反例都已变绿：`mode = "r"; open(p, mode)` 仍被拦，只是在 `:135–138` 明确声明为有意从严，而且没有纳入矩阵。

计数锁也有执行面限制：预先绑定到其他模块的 getter 引用、绕过 getter 直接使用 client，或断言之后才执行的后台调用，不能由这条计数断言保证捕获。因此成立的是**被替换 getter 的访问不再依赖异常冒泡**。

作者自加退役门的自评**诚实**：[测试:611](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_review_service_fsrs.py:611) 能拦住该 fixture 实例上通常形式的同名方法复活；它不检查等价行为，改名复活不在覆盖面内。§10.10 如实声明了这一点。

**负控正文核验**

本轮可以关闭原“未核实-2”中关于**失败是否命中点名断言**的疑问：

| 负控 | 原始正文证据 | 结论 |
|---|---|---|
| N1 | [附录 A:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/negctl-N1N2-20260908T114151.txt:39) 指向测试 `:268`，`E` 行显示 `mastery_store.py count=0`；汇总为 1 failed、5 passed | 命中锚点断言 |
| N2 门② | [附录 B:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/negctl-N1N2-20260908T114151.txt:101) 指向测试 `:335`，明确报告 `write_text@L342` | 命中静态写入断言 |
| N2 门③ | [附录 B:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/negctl-N1N2-20260908T114151.txt:106) 指向测试 `:460` 的最终 `assert not target.exists()`，结果为 `True` | 命中最终边界断言，非前提断言失败 |

这些断言行号与 HEAD 一致；N2 汇总为 2 failed、4 passed。本轮确认的是**存档正文显示的失败位置**，没有重跑，也未独立核验未提供的完整变异源码及判杀实现。

**未核实**

- **9 个方法是否完整、有没有第 10 个、调用点和 `OperationTracker` 排除是否真实，以及两个 mastery 读方函数体：未核实。** 原读取面未包含所需生产源码；扩读询问尚未收到答复，因此没有越界读取。
- **基点说明：足以解释来源，不足以证明表内数据正确。** census `:61–63` 已明确面④取自 `c480de1d`；整改 diff 没有改变相关生产文件，因此若原表行号正确，可以沿用到 HEAD。但前三面仍是 `8f7440ef` 快照，不能称为最终 HEAD 全量重扫。
- **动态调用链：未核实。** §10.4 保留这一限制是诚实的。
- **行为门前提：仍未完全核实。** 当前测试仍只在调用后断言 `fsrs_card_data is not None`，未断言初值；默认值不在读取面内。§10.8 正确披露 skip，但没有覆盖初值证明和 CI 是否禁止 skip 的疑问。
- **OpenSpec 正式移交闭环：未核实。** §10.6 承认规格未处置，但“登记与移交”的声明不能代替移交完成证据。
