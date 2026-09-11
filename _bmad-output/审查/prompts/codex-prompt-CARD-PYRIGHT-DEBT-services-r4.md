# 独立复核请求 — CARD-PYRIGHT-DEBT-services（阶段 1，round-4 · 收尾复审）

## 一 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u1-pyright-svc`
基线 `da690bf8`，本轮审 SHA **`8dcfac8e`**。

round-2 与 round-3 你的总判都是「**BLOCKER=0、HIGH=0**」。round-3 你的裁定是：
> 已证明不可达或局部等价的 assert 可以保留；已证实的差异应在本卡恢复，或由主 session 明确接受行为例外。

我按这条裁定精确修了「已证实」的部分。本轮请复核这批整改，并给出收尾判断。

### 请只读

1. `git diff 82d15aac 8dcfac8e -- backend/app/services` —— **本轮全部改动**（6 个文件），最重要。
2. 需要看累计时：`git diff da690bf8 8dcfac8e -- backend/app/services`。

---

## 二 本轮整改（逐条对应你 round-3 的发现）

### MEDIUM-1：`conversation_distiller.py:319`（你已证实）

**采信并修复**。改为 `cast(str, ...)`。注释写明调用方 `:164-166` 会把消息记进日志。

### MEDIUM-2：`signal_registry.py:187/:228/:268`（你已证实 `count` 可为 None）

**采信并在本机复现了你的实证**：
`CalibrationBiasSignal` / `ExamScoreSignal` / `SelfConfidenceSignal` 三个类执行
`preload_from_calibration_records("x_count", [])` 后，`_cache['x_count'] is None` **均为 True**。
我原注释「计数键恒写 int」**是错的**。

**为一致性，该文件 5 处（含你未点名的 `:111`/`:150`）全部改 `cast(float, count)`**，
并把上面的实证写进注释。

### LOW-2：注释与实际不符

**逐处验证 handler 的真实去向后校正 5 处**：
- `autoscore:391` / `error_classifier` ×2 / `exam_service_ext:382`：消息**只进日志**，
  返回值是固定回退结果（`dict.fromkeys(RUBRIC_DIMENSIONS, 1)` / `_heuristic_classify(...)` /
  `_get_fallback_hint(level)`），原注释说「写进返回值」不准确。
- `rag_service:321`：是**日志 + 带 cause 重抛**成 `RAGServiceError`，不是写返回值。
- `autoscore:310` **保留**原注释 —— 已验证它确实把消息写进 6 个返回字段。

**另自查你未点名的 3 处**（`question_generator:778`、`scoring_faithfulness:269/:353`），
验证其注释**准确**（handler 确有 `difficulty_rationale=f"LLM fallback: {{e}}"` /
`"reason": f"Verification failed: {{e}}"` / `"reason": f"Check failed: {{e}}"`），未改。

### LOW-3：计数更正（采信）

你指出「12 个组合对应 **10 个独立 assert**」「剩余 26 个中 **25 个**不在词法 try 内
（`agent_routing_engine:577` 在 try 内）」。**我之前说「9 处」是错的**，已更正。
本轮再删 6 个，**当前剩余 assert = 20**。

### LOW-1 / LOW-4：保留

- `cast(Any, ...)` 两处（`canvas_projection_sync:162` / `rag_service:323`）：保留。
  这两处的目标类型分别是运行期注入的 Neo4j 客户端与未解析的 `agentic_rag` 对象，无更精确类型可用。
- `CanvasRAGConfig` 属性面：**保留登记，移交主 session 裁定**，不自行加回重导出。

---

## 三 请回答

1. 本轮 6 处修改是否都正确恢复了基线的异常类型与消息？有没有改错的？
2. 剩余 **20 个 assert** 中，还有**已证实**（不是"理论上可能"）会改变可观察行为的吗？
   若有，请指出它在什么输入下成立（负控输入 / 门未覆盖的路径的形式即可）。
3. 本轮是否引入新问题（新死 import、新类型放宽、注释与实际不符、新格式漂移）？
4. 5 处注释校正后，是否还有「注释所述与代码实际不符」的地方？
5. **收尾判断**：以「已证明不可达或局部等价可保留、已证实差异须恢复」为标准，
   本卡阶段 1 是否可以收尾？剩余哪些必须作为「行为例外」移交主 session 明确接受？

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，给 `file:line` 与定级理由。
每节无问题请写「该节无发现」。**最后给一句总判：本轮 BLOCKER 与 HIGH 是否均为 0，以及能否收尾。**

---

## 五 边界

- 只读；不连数据库；不跑 integration / e2e。
- 不在本卡范围：`api/v1/endpoints/review.py:1543/:1560/:1561`；`services/review_service.py:1809-1813`。
- 10 个共享文件阶段 1 禁改，仍有 60 条错误 = 预期；另 18 条等 `extraPaths` 合入后才判。
