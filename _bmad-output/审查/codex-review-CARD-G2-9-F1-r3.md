代码审查绑定 **`0ec1f0c3`**；未修改文件、执行测试或连接数据库、网络。验收单期间新增了六行未提交说明，下文文档行号按当前文件。

**B 类未发现 BLOCKER／HIGH；A 类移交处置仍有缺口。** 我不认为安排 F2 根治本身不可接受，但当前材料不足以支持认定 A 类处置已经完成。

1. **[A] [MEDIUM] [test_lancedb_cross_vault_drop_g29f1.py:423](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:423)：仅缺陷锁自己的建表或读回失败时，仍会被误认成“缺陷仍在”。**

   前提门与缺陷锁分别创建不同的临时数据库；前者通过，不能证明后者的创建、连接及 `:425` 最终枚举成功。后者整个函数仍受 xfail 覆盖。

   | 情形 | 普通前提门 | 缺陷锁 |
   |---|---|---|
   | 两边共同发生建表错误 | FAILED | XFAIL |
   | 当前缺陷正常复现 | PASS | XFAIL |
   | F2 修正归属且执行正常 | FAILED，归属断言提示更新标记 | XPASS(strict) |
   | **只有缺陷锁自己的连接／读回异常** | **PASS** | **XFAIL** |

   因此，r2 的“归属断言先失败，吞掉修复信号”已修；**“所有夹具坏都会红”尚不成立**。另一个第四状态是分页回退：前提 PASS、页外缺陷锁 XPASS，负控 6 正在证明它。XPASS 不能单独解释为“F2 已修好，可以删标记”。

2. **[A] [MEDIUM] [UAT:471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md:471)：将新增删除面限定为四个条件同时满足，漏记了不需要 schema 漂移的显式删索引路径。**

   整卡同时把 [list_vault_tables:913](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/lib/agentic_rag/clients/lancedb_client.py:913) 改为全量枚举；`drop_vault_tables:937–940` 直接删除其结果。真实入口是 [index.py:107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/app/api/v1/endpoints/index.py:107)。

   静态反例：前十张为健康 `a_00..a_09`，页外为**健康** `a_b_canvas_nodes`；删除 vault `a` 的索引，新版也会删除这张重叠表，旧版默认分页碰不到。指纹表同样没有启动检查的后缀豁免。

   这属于 **A 类登记不完整，不新增 B HIGH**。启动漂移场景的描述与代码一致，但移交还应纳入这条路径；选项 B 只有明确覆盖该枚举入口，才能支持“不引入新可达面”的声称，其代价也包括页外正常表无法完成显式删除。

3. **[A] [LOW] [UAT:550](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md:550)：读取最终验收结论时，仍能遇到未经限定的“不会 drop 它们”。**

   收窄尚未同步完整：`:560–561` 仍写“门⑤没有负控”；`:524` 的“算法／算法进阶”也不符合下划线边界，实际 `算法进阶_canvas_nodes` 不以 `算法_` 开头。标题区及移交区已正确承认分页扩大影响，但这些旧文仍应更正。

4. **[A] [LOW] [test_lancedb_cross_vault_drop_g29f1.py:373](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:373)：把最小复现用于证明当前四用例的实际三态结果，证据范围过宽。**

   [拆分复现档案:11](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/审查/evidence-g29f1/xfail-split-premise-fix-20260908T073624.txt:11) 的修好场景是“前提 PASS＋主门 XPASS”；当前源码预期则是“归属前提 FAILED＋主门 XPASS”。档案支持拆分原理，不能称当前四用例的三态已经实测。

5. **B 类 `_assert_table_shape` 过严：未发现问题。** [测试:105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:105) 只检查夹具明确构造的列存在性和首行向量长度，与生产读取方式一致；没有额外要求 Arrow 精确类型、字段值或完整列集合。

6. **B 类分页版本漂移静默通过：未发现问题。** [测试:383](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/backend/tests/unit/test_lancedb_cross_vault_drop_g29f1.py:383) 直接检查目标是否处于默认页外。默认容量或排序改变，使目标进入页内，会让无 xfail 的前提门失败；若目标仍在页外，则该测试所需前提仍成立。门③另有默认返回十张的明确断言。

7. **[B] [LOW] [UAT:382](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance/_bmad-output/验收单/UAT-CARD-G2-9-F1-2026-09-08.md:382)：删除失败返回分支但保留 `report.get` 时，旧“计数承重”声称仍会成立。**

   r2 LOW-7 尚未同步清除。新增 AST 控制流证据是恰当补充，当前 canary 守卫本身**未发现问题**。除此之外，整卡未发现此前未报告的确定性 B 类代码问题；两个生产直接调用点及临时连接溯源与源码一致。

8. **B 类六段负控拆层不符：未发现问题。** 六份 diff 均可在内存重建出档案记录的变异体 SHA。第 1／2／4／5／6 段各改一行，第 3 段改签名和选择表达式两行。第 6 段与第 4 段使用相同变异，撤掉外层分页收口，足以让页外目标不可达；它没有回滚全部分页改动。

B 类 BLOCKER = 0，B 类 HIGH = 0。


