终裁：**需十一轮**。`HEAD=b85a168ad750343221892be4cb5d04e0cebd496f`。**BLOCKER 清零；CARD-G3-1 三个 HIGH 项仍未全部闭合；CARD-G3-4 保持 CONFIRMED-CLOSED。**

## 逐点裁定

1. **域闭包：STILL-OPEN / HIGH / 本卡**

   代码实现已闭合：`review_time` 与 `fsrs_last_review` 共用排他上界；真实 bridge 输入最后合法秒 `8999-12-31T23:59:59Z`，输出同值 W、`due=9000-01-01T00:09:59Z`，分类为 `normal`。[validator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:133)

   但冻结 schema 的 A7 仍写 `review_time ≤ 9000-01-01`，并称该端点是合法输入，与实现及 UAT 的“严格小于”宣称矛盾。[schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:142)

   `fsrs_due` 使用 9500 上界自洽：最后合法 review 加 36500 天为 `9099-12-07`，仍低于 9500。新排他端点只影响 year-9000 边界，未发现真实数据误报风险。bridge 的非 UTC 缺陷仍属已移交 G3-2，不计本卡。

2. **vault_id：STILL-OPEN / HIGH / 本卡**

   三种字面键及部分隐式类型已处理，但仍存在真实静默错绑。validator 的正则子集与 backend 的 `yaml.safe_load` 真值面仍不同：[validator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:391)、[backend config](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:782)。

   实测反例包括：

   - `vault_id: 0x10`：validator 绑定字符串 `"0x10"`；PyYAML 得整数 16，backend 回退 `canvas_vault`。
   - `vault_id: 1_000`、`vault_id: -.inf`：同类分叉。
   - `vault_id: fake` 加 `"vault_\u0069d": real`：validator=`fake`，backend=`real`。
   - 多行双引号 scalar 内容中的列首 `vault_id: fake`：validator 错当顶层键，backend 实际无该键。

   对其中两例构造完整 `review/1` 账本，真实 CLI 均 **exit 0、零 WARN**，所以不是设计内的保守“不绑定”。

   当前 27 形态矩阵未覆盖此前已点名的多行引号反例，因此 UAT“含各轮点名错绑反例”的收窄宣称仍不成立。[matrix](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:722)、[UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:39)

   现网配置则正确绑定为 `canvas_vault`。

3. **proof schema：STILL-OPEN / HIGH / 本卡**

   已确认闭合的部分：

   - 状态对象不再单列 W；
   - UTF-8、`ensure_ascii=False`、排序及分隔符已冻结；
   - snapshot 三条等式完整；
   - `prefix_ends_without_lf` 的省略/`true` 规则明确。

   但仍不能机械唯一验真：

   - 六个键的**值类型及归一化未冻结**。[schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:210) 实测 `fsrs_state=2,S=10,D=5` 与 `fsrs_state="2",S=10.0,D=5.0` 均被分类器判 `normal`，但 canonical JSON 与 hash 不同。
   - `{"kind":"new_card"}` 只是自报，没有 genesis/prior-state 锚。相同 ledger/proof 在“此前真新卡”和“此前已有未入账 Review state”两个世界中分别折出 Learning 与 Review，proof 无法区分。[new-card origin](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:207)、[不完整历史须冻结](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:222)
   - **NEW-FINDING / MEDIUM**：区间条款同时使用 `(review_time, 行号)` 复合序和纯行号端点，但未明确区间内折叠顺序或非单调行的拒绝规则。[schema](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:217)

   reducer 精度、tie 与 bridge bytes 已明确移交 G3-2，本裁定未把它们计作本卡残留。

4. **三项 MEDIUM**

   - **stability 措辞：STILL-OPEN / MEDIUM / 本卡。** schema、运行时原因、docstring 已改为“语义合理性上界”；但测试仍命名为 `test_stability_executable_ceiling`，与实际判据及 DD-13 名实一致要求冲突。[test](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:650)
   - **`_finite_number` OverflowError：CONFIRMED-CLOSED。** `ValueError/OverflowError` 均 fail-closed 返回 `None`；三种超大值回归通过。[validator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:195)
   - **W 整秒：CONFIRMED-CLOSED。** 小数秒 W 会判 degraded，目标反例已封。[validator](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:244)

5. **CARD-G3-4：CONFIRMED-CLOSED**

   - golden 门：**13 passed**。
   - UAT 列出的扩展 FSRS 套件：**191 passed**，无失败/跳过；2721 条均为第三方/deprecation warning。
   - `b85a168a` 未修改 G3-4 三个 golden 文件；当前 SHA 与负验证存档一致。
   - 声明范围内未发现新的可保持绿灯的语义漂移。[G3-4 UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:25)

## 回归与一致性

- 契约 `53 passed + 1 skipped`
- golden `13 passed`
- 既有账本 `6 passed`
- 合跑：**72 passed + 1 skipped，10 条第三方 warning**
- 现网账本：23 行，生产校验入口 **exit 0、零 WARN/FAIL**，`vault_id='canvas_vault'`
- 现网账本 SHA256：`f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`
- 十笔提交 blob 全程恒定：
  - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
- G3-1 UAT 的测试计数、live 账本和 blob 宣称准确；域闭包、proof 唯一化及 vault 矩阵覆盖宣称不成立。
- G3-4 UAT 的 13、191 与 blob 宣称均与实测一致。
- 工作树未被修改；开始前已有的未跟踪 round10 报告仍原样存在。

## 残留清单

- **BLOCKER：0**
- **HIGH 项 ×3，均属 CARD-G3-1**
  1. 排他域实现与冻结 schema 的 `≤` 条款冲突；
  2. vault_id 仍可静默错绑；
  3. proof 状态值无唯一 canonical 类型，且 `new_card` 无可信 genesis 锚。
- **已移交 G3-2/G3-3 的生产缺陷：未计入。**

**最终裁定：CARD-G3-1 不可验收，CARD-G3-4 保持验收关闭；整体需十一轮。**

验证限制：本会话未提供 `graphiti-canvas`，故无法执行规定的 Graphiti 查询；本结论来自当前 HEAD、真实 validator/bridge、PyYAML 6.0.3、现网账本只读入口、Git 对象与测试复算。


