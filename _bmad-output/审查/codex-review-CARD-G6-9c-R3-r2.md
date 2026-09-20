> 批次: BATCH-2026-09-18-第十五批 · 车道 P5 · 卡 CARD-G6-9c-R3 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9c-R3-r2.md)"`
> 审查绑定: `d062e2b145bc4faa244324228cc29697854158cb`（= 送审时 HEAD，且收工时 HEAD 未变；`git diff --stat d062e2b1 HEAD -- . ':(exclude)_bmad-output'` 为空）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `L4: OpenAI Codex v0.153.3` / `L7: model: gpt-6-astra` / `L11: reasoning effort: ultra`

---

**本轮：BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 1。**

> 批次：BATCH-2026-09-18-第十五批 / CARD-G6-9c-R3 · round-2  
> 审查绑定：`d062e2b145bc4faa244324228cc29697854158cb`  
> 结束时 HEAD 未变；排除 `_bmad-output` 的工作区代码 diff 为空。全程只读、未连接数据库，所有负控均在独立进程内存中运行。

round-1 的两条 HIGH 和一条 MEDIUM 已收口。当前未发现新的生产 HIGH，但新增判据仍有以下覆盖和状态还原问题。

1. **MEDIUM — 同源门漏掉 `_has_dst`，scripts 副本算错仍能通过相关门。**  
   [test_g6_9c_single_tz_source.py:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:118)、`:2387`。

   **负控输入**：仅把 scripts 副本内存中的 `_has_dst` 改成 `return bool(g["dst"])`。

   | 对照输入 | libc／当前原件冬夏偏移 | 内存负控冬夏偏移 |
   |---|---|---|
   | `AAA1+2` | −01:00 / −02:00 | −01:00 / −01:00 |
   | `AAA1-2` | −01:00 / +02:00 | −01:00 / −01:00 |

   **门未覆盖的路径**：共享定义名单没有 `_has_dst`；模块常量 AST 不变；组合门只跑 backend；空 dst 名的新增用例只断言非 None。独立运行相关新增 H1/H2/H3/H4 门仍全部通过。

   最小补充：把 `_has_dst` 纳入同源检查，并给上述两个对照输入断言冬夏偏移。

2. **MEDIUM — 五条计时输入没有覆盖切换时刻字段的数字分割。**  
   [test_g6_9c_single_tz_source.py:2461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:2461)、[test_local_tz_negctl_r3.py:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_local_tz_negctl_r3.py:233)。

   **负控输入**：仅在内存把 `stime` 第一枚冒号改成可选，即 `(?P<stime>[0-9]+(?::?[0-9]+…`。主文件计时门和 negctl 计时 oracle 均通过，但：

   ```text
   "A1B,M3.2.0/" + "1"*n + "+,M11.1.0"
   ```

   Python 3.14.4、min-of-5：

   | n | 202 | 404 | 808 | 1616 | 3232 |
   |---|---:|---:|---:|---:|---:|
   | 秒 | 0.000600 | 0.002384 | 0.009639 | 0.039265 | 0.158125 |

   翻倍约增长四倍。当前生产原件在这一族仍为线性。

   **门未覆盖的路径**：规则时间字段确实是第六类；现有 `digits-after-name` 只是把标准名 `A` 换成 `AAA`，没有增加字段角色。应补 `stime`、`etime` 等规则侧的长数字失败输入。

3. **MEDIUM — libc oracle 的异常还原会删除原来的进程 TZ。**  
   [test_g6_9c_single_tz_source.py:1119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:1119)，既有 `_libc_accepts` 同型位置为 `:1073`。

   **负控输入**：进程原环境为 `TZ=ABC-51`，调用 `_libc_utcoffset("AAA1", datetime(2026,1,15,12))`。函数返回 −01:00，但调用后 `TZ` 从 `ABC-51` 变成不存在；`_libc_accepts("AAA1")` 同样如此。

   **门未覆盖的路径**：恢复原 TZ 时 `tzset()` 抛 `RuntimeError`，`finally` 随后直接删除原环境值。这是确定的全局状态改变，与副本参数无关。原 TZ 不存在或为 `Asia/Tokyo` 时则正常还原。

   最小修正是保留原环境值，并明确暴露无法恢复 libc 状态的情况，不能把删除原配置当成恢复成功。

4. **MEDIUM — `_display_local` 的配置异常修复没有对应行为门。**  
   [test_g6_9c_single_tz_source.py:2743](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/backend/tests/regression/test_g6_9c_single_tz_source.py:2743)；生产修复在 [daily_review_pick.py:405](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review/scripts/daily_review_pick.py:405)。

   **负控输入**：仅在内存撤回这次修复，将 `_display_tz()` 放回 `try` 内。新增现取门仍通过，但 `CANVAS_TZ=Not/AZone` 下调用 `_display_local("2026-07-31T03:30:00Z")` 返回 None。

   **门未覆盖的路径**：新增门只调用 `_display_tz()` 和 `_today_local()`；既有无效配置 CLI 门又会在入口提前抛错，不能检查这里是否吞异常。

   当前生产修复正确。最小补充是直接断言该函数在无效配置下抛 `ValueError`，并保留 Tokyo 对照输入。

5. **LOW — 本卡说明仍有未同步之处。**

   **对照输入**：`"A"*3232+"!"` 当前不匹配，但 `test_g6_9c_single_tz_source.py:2432`、`test_local_tz_negctl_r3.py:213` 仍称匹配成功；生产说明已经更正。

   此外：

   - `test_local_tz_negctl_r3.py:216` 声称与主文件逐条同步，实际只有两个名字维度。
   - 同文件 `:481` 称预检失败显示 `ERROR`，但测试函数主体内的断言失败会显示 `FAILED`。
   - `test_review_overview.py:1082`、`test_g6_9_boundary_matrix.py:432` 仍残留 import 固化的说明。
   - `daily_review_pick.py:1143` 称缺少 `.key` 后消费侧回退，实际 `review_overview.py:572` 直接拒绝。

**对指定问题的核验结果：**

- **⓪ 接受域、移植归属与等价声明。**  
  指定 dst 输入现在均正确处理：

  | 对照输入 | libc 冬夏偏移 | 当前解析器 |
  |---|---|---|
  | `A1<B>>2`、`A1<B>C>2`、`A1<B><C>2` | 0 / 0 | None |
  | `AAA1<>2`、`A1<B>2`、`AAA1+2` | −01:00 / −02:00 | 一致 |

  自建 **279,072** 个组合中，当前与 R2 有 **9,492** 个语义差异，所测差异均与 libc 一致，主要来自 dst 引用名修复；共同接受样本未发现冬夏偏移分歧。另对 `A<>:1+-` 长度 1–6 的短串穷举，也未发现未声明的偏移分歧。

  “所有输入返回等价”仍不成立：`"<A><B>1:"+"0"*4300+"2"` 在 R2 抛 `ValueError`，当前返回 None，libc 全年 UTC。这是改善，但不能记作零变化。

  独立加载 `a8cefab4` 后，r12 原 H1/H2 指定输入返回 None，原 H4 长偏移输入给 −01:00，H3 的 n=3232 输入约 **0.0000137 秒**。因此“原指定输入在移植后已绿”的归属成立，不能推广成整个 H4 家族已经修完。移植涉及的独有文件和共享文件对应函数／hunk 与来源一致；不能称共享文件全文都相同。

- **①、⑨ 计时与 v2 推理。**  
  四倍长度要求耗时比 ≤3 的更正确实成立。当前数字输入 `"A"+"1"*n+"+"` 在 n=202/404/808/1616/3232 的耗时为 **15.17/30.46/60.08/120.00/243.25 微秒**；恢复可选 `std_off` 后，名字输入 n=3232 达 **0.357–0.425 秒**，现门会红。

  v2 的字符类与 FIRST 不相交，是附带条件的局部充分判据，不能直接变成完整线性证明：还须检查可空后继、分支、内部量词及每次后继检查的成本。**有界外层本身不保证线性**，例如 `(a+){1,2}b` 仍可平方。当前冒号结构的关键是最多两枚冒号，数字段由非数字分隔，而非仅仅“重复有界”。

  三个分支也需独立分析；固定分支数本身只增加常数倍。7 个命名组衔接点加 5 个内部形态不能证明枚举完备。此次额外检查的引用名、秒段、M 月／周／日、结束时间等形态均线性，n=3232 最慢约 **0.000505 秒**。

- **② AST 空操作预检。**  
  注释、docstring、冗余括号、`0x10` 与 `16`、隐式字符串拼接等若得到相同指纹，都会被预检拒绝，不能混过。反方向不成立：AST 不同不保证行为不同，因此后面的行为 oracle 必不可少。

- **③ 当前九段断言身份。**  
  **18/18** 次负控均失败在相关断言，没有发现红在无关对照输入上的情况：

  | 段 | `test_local_tz_negctl_r3.py` 实际失败行 |
  |---|---:|
  | COLONPOSIX / H1BARE / H2COLON | 158 / 170 / 194 |
  | H3QUANT / H4ZERO | 236 / 265 |
  | ASCII / RULEA | 285 / 305 |
  | KEYUTF8 / HMAX | 331 / 375 |

  round-1 三段失败位置说明已改正确。`expect_msg` 可作为后续加固；依据当前九段实测，不坚持把未添加它列为本轮缺陷。

- **④ picker 夹具与模块状态。**  
  1048 个 tracked Python 文件的指定 AST 扫描得到 `_DISPLAY_TZ=0`、`_display_tz=53`；唯一语法解析失败文件不含这两个名字。6 处 picker `setattr` 均无 `raising=False`，另一个 `vl` 确属 `vault_lint`。5 组直接赋值先读取旧属性，两解释器中向各自 `try` 内加入异常后均 **5/5 恢复原函数对象**。

  删除的辅助已无代码引用；三个测试模块的普通 import 取得同一 picker 对象。未发现新增辅助覆盖该真实模块名的情况。**没有重跑目录级 pytest、xdist 或完整顺序组合，不能据此保证所有执行顺序。**

- **⑤ UTF-8。**  
  CANVAS_TZ、ZoneInfo 与 `/etc/localtime` 路径确实不经过解析器的编码检查，属于该门未覆盖的路径。本机带代理字符的 CANVAS_TZ 对照输入均抛包装后的 `ValueError`，localtime 返回合法 `Asia/Hong_Kong`；未发现实际返回非法 `.key` 的输入。

- **⑥ pyright。**  
  `backend/app` 零新增 ignore 成立；整个代码面新增 **2 处测试 import ignore**，不能笼统称全卡零新增。实际运行绝对路径 pyright 返回 **rc=250**，Node 缺少 `libllhttp.9.3.dylib`，因此**未独立重现 0 errors**。

- **⑦ `_declared_narrowing`。**  
  保留检查用于类型收窄可以成立，但它不再是行为防线。“生产侧没有这个需求”的说明依据不足，两侧都把 `groupdict()` 的值传给同一个函数。

- **⑧ 新判据的实际观测范围。**  
  H4 扩展门逐处撤掉九个位置的 `.lstrip("0")`，**9/9 均红**，round-1 MEDIUM 已收口。但单独撤掉 `or "0"` 时，局部门只接住 M 规则，另四处仍绿；全零字段属于它未覆盖的路径，不能把“九处剥零均覆盖”扩写成这些表达式的全部行为均覆盖。

  `_libc_utcoffset` 对当前七串的冬夏时间点口径正确；它不支持一般重叠小时的 fold 选择。本机 `EST5EDT,M3.2.0,M11.1.0` 的 `2026-11-01 01:30`，helper 对 fold=0/1 都给 −04:00，正确实现 fold=1 给 −05:00。当前 H4 时间点不在重叠窗口，因此本轮不据此另列 MEDIUM。

  `RuntimeError` 捕获针对的是本机可发生的 `invalid GMT offset`，不是“平台没有 tzset”；缺少该属性不会被这些捕获静默判通过。

  negctl 防删计数门只锁原七段：删掉 `KEYUTF8/HMAX` 后仍可通过。它没有保障九段全部不可删。ASCII／RULEA 在当前数字类下不能触发，放宽数字类后确实能承担第二层检查；COLONPOSIX 两层的冗余只对完整 `display_tz()` 路径成立。

两份终态时区副本仅模块 docstring 不同；真实 Python **3.9.6／3.14.4** 均成功加载，同一组合集的匹配分组指纹一致。固定时区下 picker 的计算表达式保持一致，但此次没有做完整 CLI 产出的逐字节比较。

两段落盘负控存档只证明相应运行结束后的内容恢复，不能证明 Python 脚本异常、trap 自身失败等所有退出路径。前后 SHA 相同只证明两个采样时点相同；验收单已登记这一限制。本轮 B/H 为零不替代尚未独立完成的 pyright 和目录级验收。
