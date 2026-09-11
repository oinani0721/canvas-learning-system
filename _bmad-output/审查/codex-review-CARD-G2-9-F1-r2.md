> 批次: BATCH-2026-09-07-第十三批 · 车道 U5 · 卡 CARD-G2-9-F1 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-9-F1-r2.md)"`
> 审查绑定: `9da89fdd`（本轮送审时的 HEAD；round-3 已前进，故本轮**不**绑最终 HEAD）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `Reading additional input from stdin...` / `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance` / `model: gpt-6-astra`

---

已完成指定读取面的静态审查；未修改文件、执行测试或连接数据库、网络。**本轮仍有 HIGH，不能判定交接已经闭合。**

1. **[HIGH] [lancedb_client.py:1013](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:1013)**：当重叠 vault 的漂移表位于默认分页之外时，整卡扩大外层枚举和内层存在性检查，会删除基线原本触及不到的表。  
   静态反例：冷缓存、当前 vault 为 `a`，前十张是健康的 `a_00..a_09`，第十一张是漂移的 `a_b_canvas_nodes`；旧版不检查第十一张，新版将其误认领并检查删除。**旧 `list_vault_tables` 的前缀判据确实未变，但“本卡没有扩大该缺陷的影响”不成立。** 这是第一轮 HIGH 的进一步确认。

2. **[MEDIUM] [test_lancedb_cross_vault_drop_g29f1.py:340](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:340)**：当 F2 正确修复归属，使 `_owns_table("a_b_canvas_nodes", "a")` 返回 False 时，“前提断言”先失败，结果仍为 **XFAIL**，不会触发承诺的 `XPASS(strict)`。  
   `strict=True` 只有在**整个用例通过**时才报红。因此 client docstring `:884`、测试 `:313` 的“修好后报红”声称不成立。

3. **[MEDIUM] [test_lancedb_cross_vault_drop_g29f1.py:305](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:305)**：当连接、建表、读回或 `:336` 的夹具断言失败时，覆盖整个函数的 xfail 同样可能把它们记为 XFAIL，无法区分“缺陷仍在”和“根本没验证到缺陷”。  
   验收单 `:384–385` 已承认此限制，但它仍未解决；`strict=True` 不限制预期失败的位置。

4. **[LOW] [lancedb_client.py:874](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:874)**：按“互为前缀／互相干扰”理解影响方向和条件会失真；当前例子证明的是短 ID 单向认领长 ID 的表，而且需要下划线边界，`a` 与 `ab` 并不碰撞。

5. **[LOW] [test_lancedb_cross_vault_drop_g29f1.py:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:324)**：维护者按 docstring 寻找 `b_canvas_nodes` 存活的“对照断言”时会找不到，因为门⑤末尾只有 `a_b_canvas_nodes` 的存活断言。门①的独立覆盖不改变这处文实不符。

6. **[LOW] [UAT-CARD-G2-9-F1-2026-09-08.md:374](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md:374)**：若把“本卡只证明『不会 drop 它们』”用于全部别 vault 表，仍宽于实际证据，因为前缀重叠已经有反例。  
   所称三处收窄原文中的标题区、§四.5、4-B 未包含在允许读取的章节内，不能仅凭 `:309` 的登记确认三处全部妥当。

7. **[LOW] [UAT-CARD-G2-9-F1-2026-09-08.md:277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md:277)**：若仍把④b 的调用出现次数视为承重判据，删除失败返回分支也可能满足该计数；`:329` 接受控制流才承重是恰当处置，但 A3 原段落仍未同步更正。

其余核对结果：

- **`owner_vault` 外提：未发现问题。** 已读 `_cache_tables:1005–1041` 没有 `await`，归属循环没有上下文写操作；其他任务或线程修改自己的 ContextVar，不会改写当前任务的值。一次求值形成整轮归属快照是合理语义。完整 getter 与共享 override 的修改路径不在读取面，不能扩展为任意共享状态都绝不变化的保证。
- **其它四门的收集和执行：未发现问题。** 标记只作用于第五个函数。通常 XFAIL 不计失败，目录级运行不改变这一规则；整条通过产生的 `XPASS(strict)` 会失败，使用 `--runxfail` 也会取消豁免。本轮没有验证实际目录级运行结果。
- **MEDIUM-2：作者对所记录场景的反驳成立，完整调用链仍未核实。** 在表集合稳定、所述外层守卫存在的前提下，页外表先被默认分页挡住，内层 A1 改动不可达。第一轮“它也使 `add_documents` 开始处理页外表”的断言过强，应撤回。但复核日志只展示一个 `a_t11` 场景；允许读取面没有 `add_documents` 全文或完整调用点清单，**不能独立排除第三条调用路径**，也不能据此确认“表名恒属本 vault”。
- **旧谓词提取、显式 None 和 default 兼容：未发现问题。** 全卡 diff 中旧实现与新谓词同形；128 组合存档及验伪锚与此一致。两种枚举分支的存档只支持 **12 张表夹具**上的等价，超过 10,000 张的 fallback 限制仍在。

五段负控的实际失败摘录如下：

| 负控 | 档案声称撤掉的层 | 失败位置 |
|---|---|---|
| 1 | 外层归属过滤 | 门①：`b_canvas_nodes` 被删 |
| 2 | default 分支正确性 | 门②：`canvas_nodes` 被删 |
| 3 | 哨兵三态区分 | 门④及既有 regression：返回带前缀指纹表 |
| 4 | 外层扫描的分页修复 | 门③：`a_t11` 仍在 |
| 5 | 内层存在性检查的分页修复 | 门③：`a_t11` 仍在 |

**记录中的失败行确实吻合声称的断言**；五份变异体 SHA 各不相同，每份跑前、跑后 SHA 相等。第一轮“记录不可查看”的限制已经解除。

**未发现负控层重复的问题。** 4、5 是串联的两个条件，撤掉任意一个都会阻止同一页外表被处理；同红在终点断言，结合控制流足以支持“两处都需要修”。不过档案没有变异体内容或 diff，摘要本身不能独立证明“每份确实只改了声明的一层”。正向对照存档也支持所记录夹具中的漂移删除，证明范围止于删除。

总体判断：**“保留缺陷并移交”可以如实登记，但当前交接门和收窄声称不足以支持处置完成；指定读取面内未发现其它确定问题。BLOCKER 0，HIGH 1 仍存在。**
