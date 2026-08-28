终裁：**需十二轮**。已核对 `HEAD=a035850d6c72f5f354b3d201a0a58541de018029`。**BLOCKER 清零；残留 HIGH ×3，均属 CARD-G3-1；CARD-G3-4 保持 CONFIRMED-CLOSED。**

## 逐点裁定

1. **A7：STILL-OPEN / HIGH / 本卡**

   实际行为已经闭合：validator 与分类器都拒绝端点 `9000-01-01T00:00:00Z`、接受最后合法秒；真实 bridge 产出 `due=9000-01-01T00:09:59Z` 后仍分类 `normal`。[validator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:470) [classifier](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:244)

   但冻结文档仍自相矛盾：主条款写端点不合法，下一条却仍称“合法的 `review_time=9000-01-01Z`”；其他位置仍残留 `≤9000`。[schema 主条款](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:142) [矛盾句](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:146) [旧上界措辞](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:113)

   另有 **NEW-FINDING / MEDIUM**：`_parse_ts()` 用对象身份 `is` 判断排他上界；传值相等但新建的 `datetime` 会错误接受端点。当前真实调用均传常量，尚未命中。[实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:156)

2. **vault_id：STILL-OPEN / HIGH / 本卡**

   “与 backend 完全同源”不成立。测试中的 backend oracle 只是再次实现 `safe_load + strip`；生产 `Settings.vault_id` 还会调用 `sanitize_vault_id()` 并在非字符串/异常时回退。[假 oracle](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:723) [生产入口](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:785) [sanitize](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:1020)

   最小真实反例：

   - 配置 `vault_id: team#1`
   - validator 绑定 `team#1`，完整 review/1 账本 **0 problems、0 WARN**
   - backend 实际绑定 `team_1`

   独立复算 27 例，与完整 backend property 有 **15/27 分叉**；即使只看双方都接受为字符串的形态，plain scalar 折行、两种 `team#1`、Unicode 转义值仍有 4 例分叉。

   此外冻结 schema 仍完整描述旧“手写 YAML 三重白名单”，与现实现直接冲突。[旧 schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:93)

   PyYAML 缺失时“不绑定”方向安全，review/1 行会产生 WARN；但测试只断言 `None`，未验证 WARN。深嵌套 YAML 还可让 validator 抛 `RecursionError`，而 backend 会捕获并回退，属 **NEW-FINDING / MEDIUM**。现网配置是稳定子集，双方当前均正确绑定 `canvas_vault`。

3. **proof schema：STILL-OPEN / HIGH / 本卡**

   新增值类型和行号升序条款本身有效，但整体仍不能机械唯一验真：

   - E 按 `(review_time, 行号)` 最大值选取，hash/单调门却只覆盖到 `cursor_line`。`L1=t2、L2=t1` 且两行均未标乱序时，E=L1，区间只有 L1，单调门真空通过，尾部 L2 完全逃逸。[E 选取](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:197) [区间与门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:227)
   - “状态恰六键”与 Review 态省略 `fsrs_step` 直接矛盾。[六键](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:212) [省略 step](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:219)
   - `new_card` 表格仍定义左端点 0，后文又改为 `first_event_line-1`；`genesis_evidence` 嵌套位置、frontmatter 精确字节域及可复验原文未冻结。单独一个 hash 也不能证明历史上从未存在未入账 Review 状态。[旧定义](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:209) [genesis 条款](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:231)

   reducer 精度、tie、bridge bytes 仍按文档明确归 G3-2，不计本卡残留。

4. **测试命名：CONFIRMED-CLOSED**

   已改为 `test_stability_semantic_ceiling`，目标文件无旧名。[测试](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:651)

5. **CARD-G3-4：CONFIRMED-CLOSED**

   golden **13 passed**；扩展 FSRS 套件 **191 passed、2721 条第三方/deprecation warning**。三个 golden 文件 exact SHA 与负验证存档一致，第十一笔未修改这些文件；声明范围内未发现新语义缺口。

6. **回归与一致性：运行事实确认，文档口径 NEW-FINDING / MEDIUM**

   - 合跑：**73 passed + 1 skipped，10 warnings**
   - 现网账本：23 行，exit 0、零 WARN/FAIL，`vault_id='canvas_vault'`
   - SHA256：`f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`
   - 十一提交 blob 恒定：
     - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
     - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
   - G3-4 验收单核心计数与宣称成立。
   - G3-1 验收单的测试数、live、blob 成立，但 A7/vault/proof 关闭宣称不成立；实际矩阵是 27 例，验收单一处和 CURRENT_TASK 仍写 17。
   - PyYAML 在 CURRENT_TASK 已登记，验收单整改行也提及；但验收单交付清单、schema 和 validator docstring 仍称 `stdlib-only`，因此不能判“如实登记完全一致”。

## 残留清单

- **BLOCKER：0**
- **HIGH ×3，全部属于 CARD-G3-1**
  1. A7 冻结文档仍存在排他端点矛盾；
  2. vault_id 测试使用假 backend oracle，真实入口仍可静默分叉；
  3. proof 的区间、状态形状和 genesis 锚仍非机械唯一。
- **已移交 G3-2/G3-3 的生产实现缺陷：不计入。**

验证限制：本会话未提供 `graphiti-canvas`，无法执行规定的 Graphiti 查询；负验证脚本会原位 mutation，按只读边界未重跑，改以 exact SHA、baseline 及门代码复核。工作树未被修改，既存未跟踪 round11 报告保持原样且未作为证据。


