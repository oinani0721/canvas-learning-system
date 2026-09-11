> 批次: BATCH-2026-09-07-第十三批 · 车道 U9 · 卡 CARD-G3-7-R2 round-5（末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G3-7-R2-r5.md)"`
> 审查绑定: `dc033ba42274b77b247cb4ff8a2f1b2dd3932b74`（Codex 自行 `git rev-parse HEAD` 两次核对，见其正文首句）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `Reading additional input from stdin...` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

复核绑定最终 HEAD **`dc033ba42274b77b247cb4ff8a2f1b2dd3932b74`**，已两次核对一致；**本轮 BLOCKER=0、HIGH=0**，另有 **MEDIUM=1、LOW=2**。

全程只读，未连接数据库、运行测试或脚本。测试源码按该提交读取；指定三份 `_bmad-output` 文档均不在该提交树内，以下作为本次读取的外置证据核验。

**MEDIUM**

**1. [test_mastery_fsrs_projection_boundary.py:235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:235)：flags 检查仍把“已知拼写”当成“已知来源”，存在残余漏写。**

静态示例，未执行：

```python
O_RDONLY = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
os.open(p, O_RDONLY)
```

`:237–238` 仅收取参数名字，得到 `names={"O_RDONLY"}`、`unparsed=False`；`:249` 返回 `False`，但实际 flags 含创建、截断位。

同样，`get_flags().O_RDONLY` 在 `:235–236` 只收末段属性，接收者中的未知调用不会设置 `unparsed=True`。`:239–241` 也接受所有 `BinOp`，没有限定按位或运算。

这是**旧实现残余，未发现本轮新增漏写回退**：新版保留旧版全部报写条件，只进一步缩小放行集合。遗漏平台只读附加位造成的误报，符合作者明确声明的从严取舍，本身不另列问题。

**LOW**

**4. [UAT-CARD-G3-7-R2-2026-09-08.md:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/验收单/UAT-CARD-G3-7-R2-2026-09-08.md:250)：round-4 LOW-4 尚未闭合，旧示例与数量错误均仍存在。**

该段开头仍把 `from os import replace as r; r(a, b)` 列为“看不见”，后半段却说明它已被覆盖，前后矛盾。矩阵实际为 **31 条＝原 28 条＋新增 3 条**，不是 29 条。

**6. [test_mastery_fsrs_projection_boundary.py:372](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/backend/tests/unit/test_mastery_fsrs_projection_boundary.py:372)：导入表提前查询增加了跨作用域的裸名 `open` 误报。**

`:319–331` 收集全树导入，不区分作用域。例如：

```python
def f():
    from shutil import copyfile as open

def g():
    return open("a.md")
```

`g` 中实际是内建只读 `open`，但新分支会报 `open(imported)`；旧分支会放行。属于从严误报。

**没有发现该顺序调整新增漏写**：导入分支限定 `ast.Name`，不会抢占同名绑定方法或模块属性调用；`Path(p).open(...)`、`d.copy()` 等仍走原分支。

**已核实成立的处置**

| round-4 编号 | 核验结论与证据 |
|---|---|
| **MEDIUM-1** | **两个原反例整改成立，整体部分成立。** 测试 `:470` 的未知变量使子集判定失败；`:471` 的混合调用使 `unparsed=True`。上述来源识别残余仍在。 |
| **MEDIUM-2** | **成立。** `:372–379` 在文本 `open` 特判前命中导入表；`:473–476` 的 `as open` 示例能报写。新增误报见 LOW-6。 |
| **LOW-3** | **成立。** `:217–226` 与 `:465–468` 均明确缺 flags 是无效调用，返回 False 仅表示静态不报写。 |
| **LOW-4** | **未闭合。** §10.9 仍保留旧例，且 29 应为 31。 |
| **LOW-5** | **文字处置成立。** [census:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery/_bmad-output/审查/evidence-g37r2/census-20260908T073936.md:107) 已写“命中 4 个文件（排除所有权模块 `review_service.py` 后为 3）”，与同句枚举一致。 |

**矩阵逐条静态推演**

实际 **31 条全部符合各自布尔期望：20 条命中、11 条放行**。以下行号均指上述测试文件；这不表示测试已经运行。

| # | 行 | 矩阵项 | 期望＝静态结果 |
|---:|---:|---|---|
| 1 | 455 | 内建 open 写 | 命中 |
| 2 | 456 | 内建 open 读 | 放行 |
| 3 | 457 | 绑定 open 写 | 命中 |
| 4 | 458 | 绑定 open 读带 buffering | 放行 |
| 5 | 459 | io.open 常量路径写 | 命中 |
| 6 | 460 | io.open 常量路径读 | 放行 |
| 7 | 461 | io.open 变量路径写 | 命中 |
| 8 | 462 | builtins.open 常量路径写 | 命中 |
| 9 | 463 | os.open 位掩码写 | 命中 |
| 10 | 465 | os.open 缺 flags 无效调用 | 放行，调用无效 |
| 11 | 469 | os.open O_RDONLY | 放行 |
| 12 | 470 | os.open 未知变量 flags | 命中 |
| 13 | 471 | os.open 混合未知调用 | 命中 |
| 14 | 473 | as open 导入劫持写 | 命中 |
| 15 | 477 | 字符串 replace | 放行 |
| 16 | 478 | 字典 copy | 放行 |
| 17 | 479 | 列表 remove | 放行 |
| 18 | 480 | os.replace | 命中 |
| 19 | 481 | shutil.move | 命中 |
| 20 | 482 | json.dump | 命中 |
| 21 | 483 | json.dumps | 放行 |
| 22 | 484 | Path.write_text | 命中 |
| 23 | 485 | write_text 属性回调 | 命中 |
| 24 | 486 | os.replace 属性回调 | 命中 |
| 25 | 487 | from-import 裸名写 | 命中 |
| 26 | 488 | from-import 别名 r | 命中 |
| 27 | 489 | 第一档别名 cp | 命中 |
| 28 | 490 | 裸名 replace 回调 | 命中 |
| 29 | 491 | Path.read_text | 放行 |
| 30 | 492 | json.load | 放行 |
| 31 | 493 | 常量名文件对象 write_text | 命中 |

**未核实**

最终 HEAD 的测试运行结果，以及 census 实测命中、排除与零命中的真实性，本轮均未重放核实。依照末轮协议，上述剩余 MEDIUM / LOW 作为验收单与台账登记项，不再开启整改轮；本次未修改这些文件。


