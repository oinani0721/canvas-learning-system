> 批次: BATCH-2026-09-07-第十三批 · 车道 U9 · 卡 CARD-G3-7-R2 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-7-R2-r3.md)"`
> 审查绑定: `975af19c10922a46b8bdb3fea547eb50714c36ed`（Codex 自行 `git rev-parse HEAD` 两次核对，见其正文首句）
> 会话头自证（抄 .stderr，stderr 本身不入库；本跑 stderr 前几行混有 models_manager 非致命 ERROR，故抄第 1 行与第 7/11 行的 model/effort 自证行）:
> `Reading additional input from stdin...` / `model: gpt-6-astra`（stderr:7）/ `reasoning effort: ultra`（stderr:11）

---

复核绑定 **HEAD `975af19c10922a46b8bdb3fea547eb50714c36ed`**，已两次核对一致；本轮 **BLOCKER=0、HIGH=0，MEDIUM=4、LOW=2**，六条处置尚未全部闭合。

全程只读，未修改文件、连接数据库或运行测试／脚本。代码和 D0 按该提交读取；三份 `_bmad-output` 材料不在提交树内，以下作为本次读取的外置证据核验。

**MEDIUM**

**1. [test_mastery_fsrs_projection_boundary.py:148](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:148)：三分逻辑修好了 `io.open`，但对 `os.open` 引入新的普通静态漏报。**

`os.open` 的第二参数是 `flags`，`mode` 表示权限位，不能套用文本打开模式。静态反例，未执行：

```python
os.open(p, flags=os.O_WRONLY | os.O_CREAT)
```

`:156–161` 找不到第二位置参数，也不识别 `flags` 关键字，最终按“默认只读”放行。旧版取 `args[0]=p`，反而会因其不是字符串常量而报写。因此这是整改新增漏报，不能归为别名或动态调用盲区。

**2. [test_mastery_fsrs_projection_boundary.py:291](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:291)：导入追踪没有完整接入调用与回调判定。**

以下均为静态推演：

| 反例 | 漏报原因 |
|---|---|
| `from os import replace as r; r(a, b)` | `:246` 已记录 `r`，但 `:291` 先要求名字属于原始写名单，导致记录未被查询 |
| `from shutil import copyfile as cp; cp(a, b)` | 第一档导入别名同样没有接入 |
| `from os import replace; asyncio.to_thread(replace, a, b)` | `:299` 的回调扫描只接受 `Attribute`，跳过裸名 `Name` |

第三例没有别名，也不需要动态解析，属于本次“直接导入＋回调扫描”的衔接遗漏。

关于 `node.module.split(".")[0]`：它确实把 `os.path` 归入 `os`，但这不足以证明导入项是写 API。**不能拿不存在的标准库导入 `from os.path import replace` 当有效反例**；本轮未据此确认另一项实际误报。

**3. [census:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:98)：第三步补充了扫描范围，仍未证明覆盖全部“仓内其余代码”。**

`:101` 只列：

```text
backend/lib scripts canvas-vault/.claude frontend
```

加上第二步的 `backend/app`，仍没有目录全集及逐项覆盖／排除依据。例如 `backend/scripts/`、backend 根目录文件、仓库根目录代码不在这些 pathspec 内；**这些位置当前是否存在符合定义的消费代码，未核实**。

`:282` 新增的是“仓外不可覆盖”，没有登记上述仓内覆盖余项。不能据此认定发现了第二个消费者，也不能认定全仓覆盖已经完成。

**4. [census:258](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:258)：历史断言只在 D0 收窄，证据与验收单尚未同步。**

读取面内仍有：

- census `:258`：“与实现从未一致”；`:264`：“整条 Requirement 从未被实现过”。
- census `:261`：把单文件历史搜索解释为“本分支历史中从未出现过该标识符”。
- [验收单 §10.6:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md:208)：“从未实现过的行为”。

因此，作者所称“D0 与验收单均已收窄”**不成立**；D0 那一处修改成立。

**LOW**

**5. [test_mastery_fsrs_projection_boundary.py:359](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:359)：矩阵历史注释仍失实，真实路径常量反例没有完整纳入。**

`:359/:361` 使用的是 `io.open(p, 'w')`、`builtins.open(p, 'w')`。旧 r2 即使误取 `p` 为 mode，也会因其不是字符串常量而返回 `True`，所以这两条当时并不漏报。

原漏报使用 `"notes.md"` 常量路径；当前矩阵没有这两条。因此 `:351` 所称“三行上回退”不符合当前矩阵内容。

**6. [census:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:55)：新增第三步后，步骤引用没有同步。**

`:55`、`:252`、`:278` 仍写“两步法”，`:283` 已写“三步法”，尤其 `:252` 是 N 的正式限定句，应保持一致。

**已核实成立的处置**

| round-2 编号 | 本轮核验 |
|---|---|
| **MEDIUM-1** | 原 `io.open("notes.md", "w")`、`builtins.open("notes.md", "w")` 漏报及 `io.open("card.md", "r")` 误报均已修复；但新增 `os.open` 问题，整体仅部分成立。 |
| **MEDIUM-2** | 第二档属性回调、无别名的直接导入调用已接通；两类误报也确已登记。别名及裸名回调衔接仍缺失，部分成立。 |
| **MEDIUM-3** | census `:98–104` 确已增加四目录、六方法名、基点与正控记录；未重跑检索，未证明目录全集，部分成立。 |
| **MEDIUM-4** | [D0:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/docs/fsrs-truth-source-d0-revision.md:68) 的措辞、完整历史命令路径及证据限定均已修正；验收单与 census 未同步，部分成立。 |
| **LOW-5** | **成立**。census `:32–36` 已删除用于立论的“N 恒等于 0”，该句仅留在明确的撤回说明中。 |
| **LOW-6** | 旧常量引用已换成两个现有常量；矩阵历史注释仍有上述错误，部分成立。 |

**关于两处“登记不修”**

变量名提示造成的误拦，以及 `copyfileobj(BytesIO, BytesIO)` 的误报，确实都扩大拒绝范围。作为这两个模块内部静态门的保守取舍，**可以接受，当前不必因此引入完整类型／赋值分析**。

但这只能说明这两处误报方向保守，不能证明整个检查器 fail-closed。验收单 `:211` 的“新增写法时门会红一次”仍被上述漏报反例否定；函数 `:155` 的“罕见形态按写处理”也不是入口保证，因为无法识别的调用已先在 `:282–283` 被跳过。

**21 条矩阵逐条静态推演均符合当前预期**，不等于矩阵外形态已覆盖。census 零命中的真实性、目录全集、历史实现是否存在及最终 HEAD 的运行结果，均**未核实**。


