终裁：**需十四轮**。已核对 `HEAD=c0743a7e246e8995dc5141559f6ce4a38ac2338c`。**BLOCKER 清零；残留 HIGH ×1，属 CARD-G3-1；CARD-G3-4 仍可独立验收。**

1. proof 键集：**CONFIRMED-CLOSED（主契约）**

- `result_hash` 已指向分状态键集；Learning/Relearning 六键、Review 五键省略 `fsrs_step`。[schema:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:211) [schema:213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:213)
- canonical 类型、UTC 时间格式及 JSON 编码均已冻结。[schema:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:223)
- 主契约内未发现仍生效的五/六键矛盾。

严格按全文搜索仍有一处 **NEW-FINDING / LOW**：G3-1 验收单的九轮历史处置仍写“恰含 FIELD_ORDER 六键”。它已被后续十二轮段落明确取代，不构成当前契约 HIGH，但属于历史文案残留。[UAT:198](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:198)

2. 跨层单调门：**绕过 CLOSED，但 proof 整体 STILL-OPEN / HIGH / CARD-G3-1**

新增门本身有效：

- 每层内部时间严格递增。[schema:235](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:235)
- ancestor 末时刻严格小于 child 首事件。[schema:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:245)
- 两者归纳可得全链严格递增，因此 `L1=t2、L2=t1` 的双单事件分层必被拒绝。正常 A3 链本来就满足新事件 `> W`，该新增门本身不误伤。[schema:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:160)

但十二轮已点名的另一半歧义未改：

- [schema:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:197) 要求 E 后不得再有适用事件；
- [schema:210](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:210) 与 [schema:244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:244) 又规定 `ancestor_proof` 递归为 proof。

对正常 `L1=t1、L2=t2` 链，若尾部约束递归执行，ancestor 会因 L2 存在而失效；若只约束最外层，文档没有写明。两个合理 verifier 会给出相反结果，故仍不能机械唯一验真。现有校验器和测试也没有 proof 行为实现，十二轮存证仅做文本计数，无法消除该歧义。

3. vault_id 降级：**CONFIRMED-CLOSED**

- 校验器的 `open + safe_load` 已捕获全部 `Exception`，并复用生产 sanitizer；生产入口也是同口径。[validator:431](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:431) [production:777](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:777)
- 独立真实 CLI 复验：`ValueError`、`ParserError`、`RecursionError`、`ConstructorError` 均为 `exit 0 + WARN + PASS`，零 traceback。
- 扩展复验的 `ScannerError`、`ComposerError`、非法 UTF-8 也同样降级。`KeyboardInterrupt/SystemExit` 不捕获，但生产亦如此，且不属于 YAML 输入异常。
- `None` 会在 review/1 行转成 WARN 而非 FAIL。[validator:527](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:527)

4. 文档与测试口径：**点名整改 CONFIRMED-CLOSED；新增计数问题 OPEN**

- 交付清单已正确写成“主体 stdlib-only；绑定层需 PyYAML/backend”。[UAT:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:61)
- 重名测试现仅一处，且全文件无其他同名 `test_*`。[test:564](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:564)
- 新测试确实覆盖非法日期、语法错、2000 层 YAML、未知标签；四类均断言降级，非法日期另锁真实 CLI。[test:811](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:811)

**NEW-FINDING / MEDIUM / CARD-G3-1 文档**：验收单顶部仍写契约测试 `54 passed + 1 skipped`，同一行却声称合跑 `74 passed + 1 skipped`；实测及该单底部均为 `55 passed + 1 skipped`。[UAT:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:32) [UAT:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:240)

5. CARD-G3-4：**CONFIRMED-CLOSED**

- c0743a7e 未修改 generator、manifest、vectors、golden test 或钉版 requirements。
- golden `13 passed`；扩展 FSRS 套件亦复现 `91/91 + 100/100`。
- 当前 SHA 与冻结证据一致：manifest `82eaaffa…`、vectors `df60dbc6…`、test `14118eb4…`。
- 声明范围内未发现新缺口。

6. 回归与一致性：**运行事实 CLOSED；验收单宣称部分 OPEN**

- 三文件：**74 passed + 1 skipped，10 个依赖弃用类 pytest warnings**。
- 现网账本：23 行，`exit 0`，输出仅 PASS，零 schema WARN/FAIL。
- vault 绑定：validator 与真实 `Settings.vault_id` 均为 `canvas_vault`。
- 账本前后 SHA：均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`。
- 十三笔提交逐笔复算 blob 恒定：
  - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
- G3-4 验收单核心计数成立；G3-1 验收单存在上述 54/55 矛盾。

残留清单：

- **BLOCKER：0**
- **HIGH ×1**：递归 proof 中“E 后无适用事件”的层级作用域未冻结，属 CARD-G3-1。
- **MEDIUM ×1**：G3-1 验收单顶部契约测试计数仍为 54+1。
- **LOW ×1**：验收单历史段仍残留旧“恰六键”叙述。
- G3-2/G3-3 的 bridge、reducer、锁与生产接入问题继续按既有移交处理，不计本卡。

因此：**CARD-G3-4 可验收；CARD-G3-1 仍不可验收；总终裁为需十四轮。**

本轮按只读并行审计流程交叉核验真实入口与 machine anchors；`graphiti-canvas` 未在当前会话配置。未读取未跟踪的 round13 草稿，测试后工作树仍仅保留该既有未跟踪文件。


