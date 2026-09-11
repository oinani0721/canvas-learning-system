> 批次: BATCH-2026-09-07-第十三批 · 车道 U9 · 卡 CARD-G3-7-R2 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-7-R2-r4.md)"`
> 审查绑定: `2c18ff1d6ae813beaf56f33c03dbdf622d2b0db7`（Codex 自行 `git rev-parse HEAD` 两次核对，见其正文首句）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `Reading additional input from stdin...` / `model: gpt-6-astra`（stderr:5）/ `reasoning effort: ultra`（stderr:9）

---

复核绑定最终 HEAD **`2c18ff1d6ae813beaf56f33c03dbdf622d2b0db7`**，已两次核对一致；**本轮 BLOCKER=0、HIGH=0**，另有 **MEDIUM=2、LOW=3**，尚不能确认六条处置全部闭合。

全程只读，未连接数据库、运行测试或脚本。测试源码按 HEAD 读取；指定三份 `_bmad-output` 材料不在该提交树内，以下作为本次读取的外置证据核验。

**MEDIUM**

**1. [test_mastery_fsrs_projection_boundary.py:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:195)：新 flags 判定会放行未知变量，与函数声明的 fail-closed 相反。**

静态反例，未执行：

```python
flags = os.O_WRONLY
os.open(p, flags)
os.open(p, os.O_RDONLY | flags)
```

两次调用分别得到 `names={"flags"}`、`{"O_RDONLY", "flags"}`：没有命中写 flags 名单，但集合非空，`:209 return not names` 均返回 `False`。前一个位置参数形态在 r3 的文本模式逻辑下反而会按写处理，因此存在整改回退。

`_collect` 对明确写 flags 的位或递归有效，但没有保留“子表达式无法解析”的状态；例如 `os.O_RDONLY | get_flags()` 也会丢弃未知调用后放行。这不要求实现赋值追踪，按 `:184–185` 的既定承诺将未知情况判写即可。

**2. [test_mastery_fsrs_projection_boundary.py:332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:332)：导入表仍位于 `open` 特判之后，第一档导入别名存在静态遗漏。**

```python
from shutil import copyfile as open
open('source.md', 'notes.md')
```

导入表已记录 `open`，但 `:332–335` 抢先把目的路径 `'notes.md'` 当文本 mode；它不含 `w/a/x/+`，于是放行并跳过导入表查询。该调用的 Name 已记入 `called_name_nodes`，回调扫描也不会补报。

因此，r3 的 `r`／`cp` 具体反例确已修复，但“导入先查”的整体衔接仍有例外。

**LOW**

**3. [test_mastery_fsrs_projection_boundary.py:422](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:422)：`os.open(p)` 不能作为“默认只读”负控。**

`os.open` 的 `flags` 是必填参数；缺省会报缺参错误，不会默认 `O_RDONLY`。`:183/:192` 的说明同样不准确。该矩阵项只证明检查器放行无效调用；`:423` 的显式 `os.O_RDONLY` 才是有效只读形态。

**4. [UAT-CARD-G3-7-R2-2026-09-08.md:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md:238)：§10.9 的原则表述已收窄，但示例及矩阵数量没有同步。**

该段仍把 `from os import replace as r; r(a, b)` 列为“看不见”的形态，而测试 `:435` 已明确覆盖且静态推演命中。另外，源码 `:413–440` 每行一个 case，实际为 **28 条**，不是所写的 26 条。

**5. [census-20260908T073936.md:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:107)：第三步的生产命中文件数与同句枚举不一致。**

正文写“仅 3 个文件”，却列出 `review.py`、`rollback.py`、`rollback_service.py`、`review_service.py` 四个文件。若意指排除所有权模块后为三，应明确写出。此处不构成第二个消费者证据，也不直接推翻 N=1。

**已核实成立的处置**

| round-3 编号 | 本轮核验 |
|---|---|
| **MEDIUM-1** | **部分成立**。测试 `:155–158/:200–206` 已正确分流并识别原 `flags=os.O_WRONLY \| os.O_CREAT` 反例；未知 flags 仍有上述漏报。 |
| **MEDIUM-2** | **三个原反例均成立，整体部分成立**。`:336–341` 接通 `r`／`cp`；`:358–360` 接通裸名回调。`called_name_nodes` 按节点身份排除直接调用，不会把另一个作为回调参数的 Name 一并排除。仍有 `open` 优先级问题。保留 `node.module.split(".")[0]` 未据此发现有效新问题。 |
| **MEDIUM-3** | **tracked 文件的目录范围整改成立，实测结果未核实**。census `:103–104` 使用根路径 `.` 加两个路径排除，消除了原四目录枚举缺口。 |
| **MEDIUM-4** | **成立**。census `:261/:264/:267` 已收窄标题、单文件历史解释及结论；UAT `:235` 明确“未见实现证据（限定检索口径，非穷尽证明）”。 |
| **LOW-5** | **原意见成立**。测试 `:417/:420` 已加入 `'notes.md'` 常量路径；`:140–143/:404–409` 对变量路径与常量路径的历史错向解释准确。矩阵数量另见 LOW-4。 |
| **LOW-6** | **成立**。census 全文已无“两步法”，`:55/:255/:281/:286` 均采用三步口径。 |

§10.9 的“枚举面内守门、不是 fail-closed 入口保证”原则已如实收窄；不能据此认定上述实现与声明不一致的问题也已解决。

**矩阵逐条静态推演**

实际 **28 条全部符合源码各自的布尔期望**；这不等于所有示例的 API 语义有效，也不代表测试已运行。以下行号均指上述测试文件。

| 行 | 矩阵项 | 期望＝静态结果 |
|---|---|---|
| 413 | 内建 open 写 | 命中 |
| 414 | 内建 open 读 | 放行 |
| 415 | 绑定 open 写 | 命中 |
| 416 | 绑定 open 读带 buffering | 放行 |
| 417 | io.open 常量路径写 | 命中 |
| 418 | io.open 常量路径读 | 放行 |
| 419 | io.open 变量路径写 | 命中 |
| 420 | builtins.open 常量路径写 | 命中 |
| 421 | os.open 位掩码写 | 命中 |
| 422 | os.open 缺省 flags | 放行，但调用无效 |
| 423 | os.open O_RDONLY | 放行 |
| 424 | 字符串 replace | 放行 |
| 425 | 字典 copy | 放行 |
| 426 | 列表 remove | 放行 |
| 427 | os.replace | 命中 |
| 428 | shutil.move | 命中 |
| 429 | json.dump | 命中 |
| 430 | json.dumps | 放行 |
| 431 | Path.write_text | 命中 |
| 432 | write_text 属性回调 | 命中 |
| 433 | os.replace 属性回调 | 命中 |
| 434 | from-import 裸名调用 | 命中 |
| 435 | from-import 别名 r | 命中 |
| 436 | 第一档别名 cp | 命中 |
| 437 | 裸名 replace 回调 | 命中 |
| 438 | Path.read_text | 放行 |
| 439 | json.load | 放行 |
| 440 | 常量名文件对象 write_text | 命中 |

**未核实**

census 的零命中真实性、命中清单完整性、正控数量及接收者排除真实性，本轮均未重放核实。读取面内没有发现第二个消费者证据；指定整改 diff 也仅改变测试文件。但这不能证明第二个消费者不存在，最终 HEAD 的测试运行结果同样**未核实**。


