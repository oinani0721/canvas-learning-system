终裁：**需十轮**。`HEAD=2edd440505c9…`；**BLOCKER 清零，但 CARD-G3-1 仍有 HIGH ×3**。CARD-G3-4 保持 **CONFIRMED-CLOSED**。

## 逐点裁定

1. **stability：原 HIGH CONFIRMED-CLOSED；NEW-FINDING / MEDIUM ×2 / 本卡**

   `1e9` 已诚实定义为语义合理性上界，而非技术执行边界，[schema:119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:119) 与 [validator:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:175) 一致。它会有意拒绝技术可执行的 `1e9~1e100`，但作为 fail-closed 人工确认阈值可以接受。

   真实 bridge 从 2026 起连续到期 Easy 至 review 域末端，75 次后 `S≈3.44e6`，仍远低于 `1e9`；现网也未命中。因此真实人类数据误报风险极低，但这只是经验验证，不是“所有轨迹均不超过 1e9”的数学证明。

   新 MEDIUM：

   - 运行时原因仍称“**可执行上界/会溢出**”，测试 docstring 也如此，与 `S=1e10/1e100` 实测可执行矛盾：[validator:277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:277)、[test:629](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:629)。
   - `_finite_number(10**309)` 在 `float(int)` 处抛未捕获 `OverflowError`，没有 fail-closed 返回 degraded：[validator:190](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:190)。

2. **W 与 review 域：原反例 CONFIRMED-CLOSED；NEW-FINDING / HIGH / 本卡**

   `W=9400/9000` 已判 degraded，`W=8999-12-31T23:59:59Z` 正常，`fsrs_due=9400` 仍正常，原“无合法后继 normal 卡”反例已封。

   但输入/输出域端点不闭合：schema 允许 `review_time <= 9000-01-01Z`，[schema:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:137)；分类器却拒绝 `W >= 9000`，[validator:249](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:249)。实测：

   ```text
   合法前态 W=8999-12-31T23:59:59Z
   合规 review_time=9000-01-01T00:00:00Z
   bridge 输出 W=9000-01-01Z, due=9000-01-02Z
   classify_card_state(输出) -> degraded
   ```

   即合法事件会确定性制造残缺卡，属 schema/validator 闭包缺陷，不是 G3-2/G3-3 生产移交项。另有 MEDIUM：分类器仍接受非整秒 W，与文档的 canonical 秒精度不一致。

3. **vault_id：STILL-OPEN / HIGH / 本卡**

   宽正则只覆盖裸键后的空白，[validator:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:381)，仍不等价于 backend 的 `yaml.safe_load` 真值面，[config.py:780](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:780)。

   独立复现：

   ```text
   vault_id: fake
   "vault_id": real
   PyYAML/backend -> real
   validator      -> fake
   完整 review/1 账本 -> exit 0，零 WARN
   ```

   另有 `vault_id: true`：PyYAML 得 bool、backend 回退，而校验器绑定字符串 `"true"`；以及空行后的 plain-scalar 续接仍返回截断值。这些是静默错绑，不是设计内“不绑定”。

   现网配置仍正确绑定 `canvas_vault`。但 [G3-1 UAT:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:39) 声称 21 形态已含 round-5/6/7/8 全部错绑反例，不成立。

4. **degraded proof：STILL-OPEN / HIGH / 本卡**

   已闭合：prefix exact bytes、E 行 LF/EOF、cursor 截断点、origin 二选一、同 vault/node、cursor 严格递减及最终 `new_card`。

   仍不能机械唯一验真：

   - `FIELD_ORDER` 六字段本已包含 `fsrs_last_review/W`，[bridge:44](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:44)，但 proof 定义“six_fields + W”，未冻结对象形状及两份 W 必须相等：[schema:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:203)。
   - 未明确要求 `snapshot_hash == ancestor_proof.result_hash`、snapshot W 等于 ancestor `review_time`/内部 `fsrs_last_review`：[schema:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:205)。
   - 未定义 ancestor cursor 到当前 E 的精确闭开折叠区间；同瞬间不同行事件仍有两种解释。
   - `prefix_ends_without_lf` 的 false/省略规则、字段类型及编码未冻结。

   即使完全排除已移交 G3-2 的 reducer 精度/tie/blob，proof 本身仍不唯一。

5. **四项 MEDIUM**

   - envelope 只约束 `review/1`：**CONFIRMED-CLOSED**，[schema:175](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:175)。
   - 5000 位整数字段：**CONFIRMED-CLOSED**；`ValueError` 已转 degraded，[validator:216](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:216)。
   - `fsrs_step:null`：**本卡登记职责 CONFIRMED-CLOSED；生产 STILL-OPEN / 已移交 G3-2/G3-3**，[schema:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:240)。
   - 三处指定证据文案：**CONFIRMED-CLOSED**。round-7 已收窄、live 存证已有可复制命令、`a917` 的 §九实际新增量已按三条记录。新增的不实宣称是上述 UAT“全部错绑反例”及 stability 运行时措辞。

6. **CARD-G3-4：CONFIRMED-CLOSED**

   golden 门复现 **13 passed**；当前 test/manifest/vectors SHA256 与负验证存档一致。第九笔只修改 G3-4 UAT 一行，现已诚实说明存证 HEAD 较早但 bytes 未变，[G3-4 UAT:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:121)。未发现新缺口。

7. **回归与一致性**

   - 三文件合跑：**69 passed + 1 skipped**，另有 10 条第三方弃用 warning；分项即契约 `50+1`、golden `13`、既有账本 `6`。
   - 现网账本：23 行，`exit 0`，零 validator WARN/FAIL，`vault_id='canvas_vault'`；前后 SHA256 均为 `f78b99f…c11de`。
   - 九笔提交 blob 恒定：
     - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
     - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
   - 两份 UAT 的主测试计数可复现；G3-4 声明准确。G3-1 的闭合宣称及“全部错绑反例”宣称不成立。

## 残留 BLOCKER/HIGH

- **BLOCKER：0**
- **HIGH ×3，均属 CARD-G3-1**
  1. 合法 review 上界事件写出 W 上界后立即被判 degraded；
  2. vault_id 仍有多种可静默错绑形态；
  3. degraded proof 的状态形状、祖先等式与折叠区间未唯一化。

**最终裁定：CARD-G3-1 不可验收，需十轮；CARD-G3-4 可保持验收关闭。**

本轮未修改工作树；审阅前已有的空白未跟踪 round9 文件仍原样存在。`graphiti-canvas` 本会话未提供，故未执行其检索；其余结论均来自当前 HEAD、真实 bridge/validator、现网账本与 Git 对象复算。
