# Codex 对抗审查 · CARD-D3 持久化失败信号消费方诚实化

> 审查模型: codex exec gpt-5.6-sol / 一轮 ultra · 二轮/三轮 high / --sandbox read-only
> 日期: 2026-08-28 · 分支 card/m2-honest（审查时未 commit 的工作树 diff）

## 一轮（0 BLOCKER / 3 HIGH / 2 MEDIUM / 2 LOW）

结论：**FAIL，建议阻断合并**。共 **0 BLOCKER / 3 HIGH / 2 MEDIUM / 2 LOW**。

## BLOCKER

无。

## HIGH

1. **失败信号只诚实一次，随后立即误报 `persisted=True`**

   [review_service.py:2087](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:2087)、[review_service.py:2106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:2106)、[review_service.py:2121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:2121)

   auto-create 或 record 写失败后，卡仍留在 `_card_states`。同进程第二次 GET 命中缓存便无条件设置 `persisted=True`，并删除失败 reason。写盘尚在 `to_thread` 进行时，并发 GET 也会提前报 True。这个“窗口”是每次失败/在途写都会制造的实时状态，注释不能使响应诚实。

   卡内方案：记录文件已提交的 exact card bytes/revision；若暂不记录 provenance，缓存命中应保守返回 `persisted=None`，不能声称 True。

2. **`_save_card_states()` 的 True 没有绑定本次响应的 `card_data`**

   [review_service.py:1020](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:1020)、[review_service.py:338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:338)、[review_service.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:341)、[review_service.py:1067](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:1067)

   mutation 发生在锁外。若 C 持锁，A 先写 `dict[x]=A1` 等锁，B 再覆盖成 B1；A 随后取得锁时实际持久化 B1，却向自己的响应返回 `card_data=A1 + card_state_persisted=True`。A1 从未写入文件。

   因而 bool 只证明“某个全量快照 replace 成功”，不能证明本次响应的状态成功。需把 mutation、exact snapshot 和提交结果放进同一版本/锁协议。

3. **部分真实写失败不会返回 False，而会落入 Ebbinghaus 并标成“不适用”**

   [schemas.py:874](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/models/schemas.py:874)、[review_service.py:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:341)、[review_service.py:350](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:350)、[review_service.py:1071](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:1071)、[review_service.py:1108](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:1108)

   `_save_card_states()` 只捕获 `OSError/TypeError`。请求模型允许 lone surrogate，例如转义后的 `node_id="\ud800"`；`ensure_ascii=False` 后 UTF-8 写入会抛 `UnicodeEncodeError`，它属于 `ValueError`，不会转为 False。

   此时缓存已经更新，record 外层却转入 Ebbinghaus并返回两个 None；query 路径则变成 `found=False/error`，均违反本卡失败契约。该非法 key 还会让后续全量保存持续失败。持久化异常应在持久化边界归一为 False，且不得进入算法 fallback。

## MEDIUM

1. **Optional 默认 None 会改变旧响应的 wire key 集**

   [schemas.py:966](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/models/schemas.py:966)、[schemas.py:1003](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/models/schemas.py:1003)、[review.py:1028](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/api/v1/endpoints/review.py:1028)、[review.py:1365](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/api/v1/endpoints/review.py:1365)

   两个路由均未启用 `response_model_exclude_none`。因此 legacy/fallback/not-found 响应会新增 `persisted:null`，或 `card_state_persisted:null`、`degraded_reason:null`。宽松客户端通常安全，但这字面上不满足“默认值不改变既有序列化行为”，严格 key-set 客户端可能断裂。

2. **提交到仓库的 OpenAPI 契约没有同步**

   [backend/openapi.json:13447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/openapi.json:13447)、[backend/openapi.json:19416](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/openapi.json:19416)

   静态 `FSRSStateQueryResponse` 缺 `persisted`，reason 描述仍只覆盖 `found=false`；`RecordReviewResponse` 缺另外两个字段。动态 `app.openapi()` 会包含它们，但依赖仓库 OpenAPI 生成的未来客户端看不到本卡信号。

## LOW

1. **测试没有锁定 reason 键必须缺席**

   [test_fsrs_state_query.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_fsrs_state_query.py:399)、[test_fsrs_state_query.py:418](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_fsrs_state_query.py:418)

   `result.get("reason") is None` 同时接受“键不存在”和 `"reason": None`，无法保护第 3 条契约。应断言 `"reason" not in result`。当前生产代码确实只在失败时插入 reason，既有消费方未发现断裂。

2. **fallback fixture 泄漏模块级运行状态**

   [unit/conftest.py:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/conftest.py:83)、[review_service.py:281](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:281)、[test_review_service_fsrs.py:691](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_review_service_fsrs.py:691)

   `fallback_service` 构造时把全局 `FSRS_RUNTIME_OK` 设为 False，却不保存/恢复；新增最后一个测试会留下确定尾状态，可能污染随后同 worker 的 health 测试。

## 已验证项与边界

- `False` 经端点 `.get()` 原样转发，没有被 truthiness 吞掉；200/404 控制流未改变。
- empty concept 与真正无 FSRS manager 的 fallback 赋值完整，无未定义变量。
- `_CARD_STATES_FILE` 的共享 fixture、class monkeypatch 与 `/dev/null` patch 按 LIFO 恢复；未发现路径或实例状态泄漏。
- 新增测试漏掉“失败后同实例立即再查”这一核心反例；existing-card 测试只命中同实例缓存。
- 审阅基线：`card/m2-honest@91383b1f`。未运行 pytest；`git diff --check` 通过。
- 工作树另叠有未展示的 CARD-D4/回归测试改动，本结论未把它们混入 CARD-D3。
- 当前未暴露 `graphiti-canvas`，无法执行 Graphiti 审查记录/搜索。



---

## 二轮复核（H1/H2/LOW×2 RESOLVED；H3 残留 HIGH；M1 rejection 不成立；M2 未闭环）

结论：**FAIL，继续阻断 CARD-D3 合并**。当前为 **0 BLOCKER / 1 HIGH / 1 MEDIUM 未解决 / 1 MEDIUM 部分解决**。

核心原因：HIGH-3 只修复了“本次请求不再错误回退”，但 lone-surrogate 会永久留在进程内全量快照中，导致后续正常 concept 也无法持久化。

| 一轮 finding | 二轮裁定 | 证据 |
|---|---|---|
| HIGH-1 缓存命中洗白 | **RESOLVED** | 失败 concept 会在锁内加入 `_unpersisted_concepts`，缓存查询也在锁内读取该集合：[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:352)、[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:2140)。同实例二次查询反例已锁定：[test_fsrs_state_query.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_fsrs_state_query.py:427)。 |
| HIGH-2 bool 未绑定本次 card_data | **RESOLVED** | 三个调用点均传入 `pending`；mutation、snapshot、replace 同处锁内。实测两个并发写返回 `[True, True]`，replace 前 exact 快照依次为 `A1`、`B1`，最终文件为 `B1`，符合线性化语义：[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:328)。 |
| HIGH-3 UnicodeEncodeError 逃逸 | **部分** | 首次 lone-surrogate 请求现在确实返回 `fsrs-4.5 / False / card_state_write_failed`。但 mutation 在序列化前发生，捕获异常后没有回滚或隔离坏 key：[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:352)。连续真实调用结果：surrogate 首写失败后，`normal-after-surrogate` 也失败；dirty 集合同时包含两个 concept，磁盘文件不存在。现有测试只断言第一次调用，未覆盖后续正常写：[test_review_service_fsrs.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_review_service_fsrs.py:703)。这是仍未关闭的 **HIGH**。 |
| MEDIUM-1 wire key-set | **NOT-RESOLVED；rejection 不成立** | 当前 `model_dump` 确认旧响应新增 `persisted:null`、`card_state_persisted:null`、`degraded_reason:null`：[schemas.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/models/schemas.py:966)。`exclude_none` 会删除既有 null 字段这一点成立，但它不是唯一实现方式；可采用条件 kwargs/定向 unset 序列化。仓库搜索未发现 live 前端消费者，故实际风险较低，但技术事实仍存在，而且未找到所称入档记录。 |
| MEDIUM-2 静态 OpenAPI | **部分；范围延期理由基本成立，但未闭环** | 静态文件仍缺三个字段：[openapi.json](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/openapi.json:13447)、[openapi.json](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/openapi.json:19416)。独立重算确认全量漂移很大：11,515 条 unified-diff 行，+8,243/-1,876；未精确复现处置单的 10,519/+8,444，但支持“不应混入本卡”的判断。问题是当前工作树没有实际债卡/验收记录，所以只能裁定部分。 |
| LOW-1 reason 缺席断言 | **RESOLVED** | 两处均改为 `"reason" not in result`：[test_fsrs_state_query.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_fsrs_state_query.py:398)。 |
| LOW-2 fixture 全局泄漏 | **RESOLVED** | fixture 保存并在 yield 后恢复 `FSRS_RUNTIME_OK`：[conftest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/conftest.py:83)。 |

验证结果：

- 指定三文件套件：**79 passed，2334 warnings，473.55s**。
- Unicode 单测关闭 pytest capture 后：**1 passed**。
- `git diff --check`：PASS。
- 未运行全量 `tests/` 或 CI。
- D4 路径已排除，未发现 D3/D4 交叉缺陷。
- 没有发现独立的“修复新引入”缺陷；上述 HIGH 是 HIGH-3 的同根残留/修复不完整。
- 当前会话未暴露 Graphiti 与 LSP，无法写入 Graphiti `[Code-Review]` 或取得 LSP diagnostics。

**BLOCKER/HIGH 清零: 否**



---

## 三轮终裁（残留 HIGH RESOLVED · BLOCKER/HIGH 清零: 是）

三轮终裁：**0 BLOCKER / 0 HIGH**。但两项 MEDIUM 的治理闭环尚未全部完成。

1. 残留 HIGH：**RESOLVED**

- pending mutation、`prev` 捕获、写盘及回滚均在同一锁内；并发恢复不会覆盖其他已线性化写入。[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:353)
- `TypeError/ValueError` 会恢复旧值或删除新 key，毒 key 不再进入后续快照。[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:370)
- 连续查询毒 key 会每次重新 auto-create，并返回 `found=True / persisted=False / auto_created_not_persisted`，与“本请求生成了卡但未保存”自洽。
- `OSError` 分支继续保留内存状态并加入 dirty，H1 的 `cached_state_not_persisted` 反例仍成立。[review_service.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/services/review_service.py:382)
- 新毒 key 后续保存反例已覆盖。[test_review_service_fsrs.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/unit/test_review_service_fsrs.py:718)

边界：该裁定基于服务自身生成的干净持久化快照；`_load_card_states()` 尚未验证手工篡改快照中的 surrogate，可另列防御性加固，但不延续本次 HIGH。

2. M1：**处置方式可接受，但不是 RESOLVED**

“reasoned rejection + 用户拍板”可作为 MEDIUM 风险处置；无 live 消费方且 route 级序列化改造收益有限，理由成立。需修正一处事实：生产代码共有 **5 个**响应构造点，而非 4 个——2 个 `RecordReviewResponse`、3 个 `FSRSStateQueryResponse`。[review.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/app/api/v1/endpoints/review.py:1117)

当前仍应标记为：**技术事实存在、建议拒绝修代码、等待用户接受风险**。

3. M2：**未闭环**

当前 checkout 中：

- 没有 CARD-D3 验收单；
- 没有 CARD-D3 commit 或相应 commit body；
- `backend/openapi.json` 没有本卡变更；
- 只有未跟踪的 CARD-D3 审查报告及 CARD-D4 验收单。

即使将来写入“待确认”的 DEBT 候选，也只能证明已升级，不能代替用户接受。故目前仍为 **PARTIAL / pending authorization**。

验证：指定三文件套件 **80 passed、0 failed、2334 warnings，490.71s**；`git diff --check` PASS。当前工作树混有未提交 CARD-D4 变更；Graphiti/LSP 工具未暴露。

**BLOCKER/HIGH 清零: 是**
