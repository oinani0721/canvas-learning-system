终裁：**需十三轮**。已核对 `HEAD=6d3aafc7228e4339621344d770cf8e6ebb4eb476`。**BLOCKER 清零；残留 HIGH ×1，属于 CARD-G3-1 proof；CARD-G3-4 保持 CONFIRMED-CLOSED。**

1. A7：**CONFIRMED-CLOSED**

- 冻结文档的主条款、闭包解释和旧上界残留均已统一为排他上界。[schema:143](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:143) [schema:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:146)
- `_parse_ts()` 已改为值比较 `upper_bound == REVIEW_INPUT_MAX`；review 校验和分类器使用同一边界。[validator:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:162)
- 独立实测：新建等值对象 `is=False、==True`；端点返回 `False`；最后合法秒返回 `True`；分类器分别为 `degraded/normal`。等瞬间的 `+08:00` 上界对象也正确排他。

2. vault_id：**NEW-FINDING / MEDIUM / 本卡**  
   原“假 oracle、非 None 错绑”HIGH 已 **CONFIRMED-CLOSED**。

- 校验器确实动态导入生产 `sanitize_vault_id` 本体；测试 oracle 也直接调用真实 `Settings.vault_id`。[validator:392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:392) [test:758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:758)
- 独立差分 1,229 种 YAML：267 种同值绑定、962 种保守 `None`、**非 None 错绑 0**。现网双方均为 `canvas_vault`。
- 但降级路径仍不完整。配置：

```yaml
vault_id: 2023-13-40
```

  会让 PyYAML timestamp constructor 抛 `ValueError`。生产入口捕获 `Exception` 并回退；校验器只捕获 `YAMLError/RecursionError` 等，实测 **exit 1 + traceback**，没有“不绑定 + WARN”。[validator:435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:435) [production:777](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:777)

3. proof schema：**STILL-OPEN / HIGH / CARD-G3-1**

部分整改成立：`new_card` 左端点三处均为 `first_event_line - 1`；frontmatter 字节域、原文携带及证明强度上限已经成文。[schema:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:229) [schema:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:233)

但仍不能机械唯一验真：

- 直接矛盾仍在：`result_hash` 行要求状态对象“**恰六键**”，下一条却要求 Review “**五键并省略 fsrs_step**”。Review 无论用五键还是六键都会违反一条规范。[schema:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:211) [schema:213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:213)
- E 的平铺尾逸已封，但 snapshot 链仍可把 `L1=t2、L2=t1` 拆成 ancestor `(0,1]` 与 child `(1,2]`；两个单事件区间的单调门都真空通过。规范缺少“ancestor W < 子区间首事件”的跨层单调门。若把“其后无适用事件”递归施于 ancestor，则任何有后继事件的 ancestor 又都失效。[schema:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:197) [schema:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:224)

4. 三项 MEDIUM：**2 项 CLOSED，1 项 STILL-OPEN**

- PyYAML 缺失 WARN：**CONFIRMED-CLOSED**；测试同时断言 `None` 和 WARN，真实 `python -S` CLI 也为 exit 0 + WARN。[test:832](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:832)
- YAML `RecursionError`：**CONFIRMED-CLOSED**，2000 层真实 YAML 复验返回 `None`。现有深嵌套回归实际只测 JSON，建议补 YAML 专项锁，但不单独阻断。
- stdlib-only 口径：**STILL-OPEN / MEDIUM**。schema、validator docstring 和验收单新依赖行已正确；但十一轮点名的“验收单交付清单”仍写无条件的“stdlib 确定性校验器”，并未改成分层依赖口径。[UAT:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:42) [UAT:61](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:61)

5. CARD-G3-4：**CONFIRMED-CLOSED**

- `a035850d → 6d3aafc7` 未修改 generator、manifest、vectors、golden test。
- golden **13 passed**。
- 三个 SHA 与负验证存档一致：manifest `82eaaffa…`、vectors `df60dbc6…`、test `14118eb4…`。
- 未发现声明范围内的新语义缺口。

6. 回归与一致性：**运行事实 CLOSED；验收宣称仍部分 OPEN**

- 契约：**54 passed + 1 skipped**
- golden：**13 passed**
- 既有账本：**6 passed**
- 合跑：**73 passed + 1 skipped，10 warnings**
- 现网：23 行，exit 0，仅 PASS、零 WARN/FAIL；前后 SHA 均为 `f78b99f30791570dde64b7ee33c32298d592037c21c9b948ec3007f7ef9c11de`；validator 与生产均绑定 `canvas_vault`。
- 十二笔提交 blob 恒定：
  - `learning_event_log.py`：`28cdaa18602b72670c0f2e57b3cba6a7c1453dd0`
  - `fsrs_manager.py`：`980b3758758b1d78d6795451c76270c10713cc60`
- G3-4 验收单核心计数与宣称成立；G3-1 的数字、现网、blob、25 形态计数成立，但 proof 与依赖口径的“全部闭合”宣称不成立。
- 非阻断 LOW：契约测试内 `test_watermark_comparison_must_be_instant_based` 在 [524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:524) 和 [585](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:585) 重名，后一份静默覆盖前一份；不影响当前 54+1，但应清理。

残留清单：

- **BLOCKER：0**
- **HIGH ×1（按十一轮 proof 大项计，CARD-G3-1）**：状态五/六键直接矛盾；snapshot 分层仍可绕过全链单调性。
- **已移交 G3-2/G3-3 的 bridge、reducer、锁及生产接入缺陷：不计入。**

因此：**CARD-G3-4 可独立验收；CARD-G3-1 仍不可验收，需十三轮。**

验证限制：`graphiti-canvas` 本会话未配置；本轮未重跑 191 项扩展 FSRS 套件，但 G3-4 相关 blobs 未变且聚焦 13 门全绿。既存未跟踪 round12 草稿未读取、未修改。


