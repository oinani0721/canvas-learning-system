终裁：**需三轮，当前不可验收**。二轮复核后残留 **1 BLOCKER + 3 HIGH**：G3-1 为 1B+2H，G3-4 为 1H。

审查绑定：WT `card/s3-events`，HEAD `a8bab73c`，父提交 `63e034ec`；全程只读，未修改既有未跟踪的二轮报告草稿。

## CARD-G3-1 逐项裁定

| 处置项 | 判定 | 二轮结果 |
|---|---|---|
| e-1 applied-watermark | **STILL-OPEN / BLOCKER** | [schema §6.2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:97) 只覆盖单事件、恢复先于新写的简单三窗，未覆盖交错窗口：FM=t0；E1@t1 落账后崩溃；恢复前 E2@t2 从旧状态推进至 t2；随后 E1 因 `t1<=t2` 被误判“已应用”，实际 FSRS 状态永久漏掉 E1。 |
| e-1 字段/乱序/并列移交 | **STILL-OPEN / BLOCKER** | 契约写 `frontmatter.last_review`，真实键是 [fsrs_last_review](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/canvas-vault/.claude/scripts/fsrs_bridge.py:44)，新卡还可能无该键。`<= ⇔ 已应用` 也不能区分“已应用”和“旧乱序未应用”。G3-3 确实拥有 CAS/乱序范围，但其[卡面](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:612)未定义等时拒绝或复合排序；现有时间戳仅秒级，等时事件可自然产生。 |
| a-1/a-2 tips 两偏离 | **CONFIRMED-CLOSED（处置层）** | G3-1 禁改生产写路径，登记移交正确；`tips.py` 和 `learning_event_log.py` 对父提交零改动。两项缺陷仍真实存在，且“G3-7 或 micro-patch”owner 不够确定——G3-7 卡面并不包含 tips，建议明确独立 micro-patch。 |
| b-1 未知版本 | **CONFIRMED-CLOSED** | v2 新形状现为 WARN、完整跳过 v1 形状、exit 0。[分流实现](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:215)成立。 |
| b-2 NaN/重复键 | **CONFIRMED-CLOSED** | NaN/Infinity、重复 member 均翻红。 |
| b-2 严格 JSON 完整性 | **NEW-FINDING / HIGH** | [decoded.strip()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:202) 会剥除 RFC 8259 不允许的 U+001C 包裹，敌对行实测 exit 0；严格 JSON 门仍可绕过。 |
| b-3 UTF-8/Q 分隔符 | **CONFIRMED-CLOSED** | 非法 UTF-8 逐行报错且无 traceback；`Q` 分隔符翻红。 |
| b-3 完整时间词法 | **NEW-FINDING / MEDIUM** | week-date、小时省略分钟、`+00` offset、逗号小数、offset seconds 均被错误接受，与[冻结语法](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:41)不符；5000 位合法 JSON 整数还会触发未捕获 `ValueError`。 |
| e-3 schema_ext 类型 | **CONFIRMED-CLOSED（基础类型）** | rating bool/越界、缺 review_time 均翻红。 |
| e-3 schema_ext 绑定 | **NEW-FINDING / HIGH** | [扩展校验](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:110)不查 `concept_id==node_id`、`review_time==effective_at`、正常 version/hash 形状、degraded 成对及非空原因；综合坏例仍 exit 0，且 `DEGRADED_PREFIX` 定义后未使用。 |
| c-1 producer 测试 | **CONFIRMED-CLOSED** | 三个 vault 测试确实动态提取并执行 SKILL writer：[ai-linked-doc](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:359)、[start-exam-board](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:375)、[quiz-answer](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_learning_events_schema_contract.py:402)。二跑后行数/类型断言有效。第四条只执行共享 `append_event` 加手写五组实参，并未经过五个 backend callsite，标题“4 条真实 producer”略宽。 |
| c-2 测试计数 | **CONFIRMED-CLOSED** | 当前独立复跑 `25 passed, 1 skipped`。 |
| d-1 单卡切分 | **CONFIRMED-CLOSED** | `63e034ec` 与 `a8bab73c` 为父子独立提交，文件面可单卡切出。 |
| e-2/e-4/a-3 | **CONFIRMED-CLOSED** | LF 守卫契约、G3-4 manifest 依赖、分隔符/D0 引用措辞均已落文档。 |
| d-2 SHA 存证 | **STILL-OPEN / MEDIUM** | validator/test/fixture SHA 与当前 bytes 一致；现网 22 行复算 exit 0、前后 SHA 均为 `2a18023…96cb6`。但证据 HEAD 仍写预提交 `37387a…`，fixture 存证也未包含其宣称的完整命令/HEAD。 |

## CARD-G3-4 逐项裁定

| 处置项 | 判定 | 二轮结果 |
|---|---|---|
| e) CI 接入移交 | **CONFIRMED-CLOSED（处置层）** | [开跑手册](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-第五批开跑手册-8车道13卡.md:112)明确 S8 独占 `.github/workflows/` 且 `test.yml` 零改动。验收单给出了 owner、合并后时点、两测试白名单及 root requirements 双 paths trigger；[测试 docstring](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:24)也已注明。必须标记为 **DEFERRED / NOT-EXECUTED**，不能称 CI 已生效。 |
| f) 点名反例 | **CONFIRMED-CLOSED** | 重复/缺格、前态 999、retrievability 清空、algorithm 任意值、容差放宽、requirements `.post1` 均独立翻红。 |
| f) 真实 5×4 行为矩阵 | **STILL-OPEN / HIGH** | [结构门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:187)从 `id` 后缀推导 rating，但[重放](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/tests/regression/test_fsrs_golden_vectors.py:212)执行的是 `steps[-1].rating`。把 Good 行实际改成 Hard、复制 Hard expected，仍全绿；把 new-card steps 伪装成同前态的 learning-step2，也仍全绿。真实 rating/scenario 缺格尚未锁住。 |
| 容差、requirements、algorithm/timezone、newline | **CONFIRMED-CLOSED** | 所有一轮指名变体均按预期翻红，LF 固定已落生成器。 |
| 负验证 v2 存档 | **STILL-OPEN / MEDIUM** | [存档](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/g3-4-negative-verification.txt:1)中的 test/manifest/vectors SHA、失败名和 exit code可复得；但只有通用 pytest 命令，没有各变体 mutation/restore 命令。实际为 N1–N7 七个负例，不是“8 个负例”，且 algorithm、`.post` 未入存档。 |
| “公开 re-export”口径 | **STILL-OPEN / MEDIUM** | 测试已诚实改为直接 `from fsrs import`，但 UAT 技术判据仍称“只经公开 re-export”，文档自相矛盾。 |
| g) 七门与核心回归 | **CONFIRMED-CLOSED** | 当前复跑：golden `11 passed`；指定六文件 `91 passed, 528 warnings`，106.15 秒。仅代表这些目标套件，不外推全仓 CI。 |
| h) 生产文件零改动 | **CONFIRMED-CLOSED** | 两提交三态中 `learning_event_log.py` git blob 恒为 `28cdaa18…`，`fsrs_manager.py` 恒为 `980b3758…`；两段 path diff 均为空。 |

## 残留 BLOCKER/HIGH

- **BLOCKER — G3-1 applied-watermark**：不能在崩溃、恢复前新写、乱序及等时条件下证明 exactly-once current-state 推进。
- **HIGH — G3-1 严格 JSON 绕过**：非法外围控制字符被 `strip()` 洗成合法 JSON。
- **HIGH — G3-1 review/1 跨字段绑定缺失**：节点、业务时间、库版本/hash 与 degraded 语义未被机械验证。
- **HIGH — G3-4 实际矩阵缺格仍可全绿**：ID/scenario 标签未绑定真实 steps/rating/time skeleton。

三轮最低修复应同时补：持久 applied event/revision 或“恢复先于新写”硬门及三态语义；精确字段名/缺水位线/等时 tie-break；严格 JSON whitespace 与完整时间词法；review/1 跨字段约束；G3-4 的 `id == scenario__final_rating`、每场景 prefix/time skeleton 锁。

`graphiti-canvas` 本会话未暴露，因此无法执行本轮 Graphiti 搜索/写入 `[Code-Review]`；历史记忆只用于审计方法，所有事实均已在当前 checkout 重算。


