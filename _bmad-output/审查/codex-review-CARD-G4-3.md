结论：**FAIL / 不可验收**。基准为 `HEAD 9cf0fb85ed839bb7035d023534fca222a24d6968`，以最终工作树字节复核。未发现硬边界违规，但 AND 条件被真实 `/rag/query` 入口击穿。

## BLOCKER

### 1. `/rag/query` 的真实 unavailable fallback 返回 500，新增测试是假绿

- 文件：[rag_service.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:197)（197–228、326–333）、[rag.py:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:137)（137、334）、[test_rag_four_state_api.py:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:36)（36–53、139–150）
- 问题：真实 `RAGService.query()` 在 `ainvoke()` 返回 `None` 时产生 `retrieval_status="unavailable"`，同时产生 `quality_grade=None`。端点的 `result.get("quality_grade", "low")` 不会替换显式 `None`，随后构造 `quality_grade: str` 的响应模型失败，HTTP 500。
- 可复现反例：将真实 `canvas_agentic_rag.ainvoke` patch 为 `AsyncMock(return_value=None)`，向路由注入真实 `RAGService` 后 POST `/api/v1/rag/query`。实测 `ainvoke_calls=1`、响应 500。新增测试的 `_state()` 却对所有状态固定伪造 `quality_grade="high"`，所以 `test_unavailable_still_returns_200` 没覆盖生产形状。
- 影响：直接违反条件 (e) 的 unavailable/200，也使 (c) 的真实纯透传路径不可达。这个形状矛盾在 HEAD 已存在，不是本 diff 新造，但本卡的“200 证明”因此不成立。
- 建议：遵守硬边界，只在端点改为 `quality_grade=result.get("quality_grade") or "low"`；增加经过真实 `RAGService.query → _get_fallback_result` 的 HTTP 回归，不能继续只测合成字典。

## HIGH

### 1. trace 落账异常会把本应 200 的业务响应升成 500

- 文件：[decision_tracker.py:128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:128)、[memory.py:250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/memory.py:250)（250–272、313–327、412–440）、[rag.py:301](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:301)（301–371）
- 问题：四个端点均在返回前同步调用 `log_retrieval_status_decision()`；它直接调用真正的 `log_decision()`，没有隔离观测面异常。
- 可复现反例：patch `app.core.decision_tracker.log_decision` 为 `side_effect=RuntimeError("trace sink failed")`，注入合法 unavailable 载荷：
  - `/memory/episodes` → 500，且错误被误报为 `Failed to query learning history: trace sink failed`；
  - `/rag/query` → 500 `Internal Server Error`。
- 建议：在 `log_retrieval_status_decision()` 内 fail-open 隔离落账异常，并用独立安全 logger 记录；新增 patch **真实落账函数**抛错后 memory/rag 仍返回 200、原状态字段不变的测试。

## MEDIUM

### 1. “零消费方”结论需收窄；验收单给出的证据路径不可复现

- 文件：[验收单.md:258](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:258)（258–277）、[零消费方证据:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/01-review-suggestions-零消费方-grep.txt:1)、[归档 ApiClient.ts:1413](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_archive/canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts:1413)
- 问题：
  - 验收单指向不存在的 `scratchpad/evidence-consumers.txt`；实际证据位于 `evidence-g43/01-...txt`，但未被链接。
  - 证据 B/C 只有结果 `0`，没有复跑命令。
  - 活跃源码确实没有消费方，但 `_archive` 中存在返回 `Promise<MemoryReviewSuggestionItem[]>` 的真实客户端；信封会破坏它。仓外消费方则是 `UNVERIFIABLE`。
- 独立验证：
  - 对 frontend、活跃 Obsidian 插件、sidecar、MCP、backend 客户端/脚本运行 `rg -S 'review-suggestions|getReviewSuggestions|reviewSuggestions'`，仅命中端点/schema/service 定义；
  - 对 `_archive` 重跑同一命令，命中上述数组客户端。
- 建议：改成“当前仓内活跃生产源码消费方为 0”；登记归档客户端恢复时的迁移风险和仓外不可验证边界；修正证据链接并保存三组完整 `rg` 命令及输出。

### 2. 验收单的 59 条失败根因表仍然错误

- 文件：[验收单.md:315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:315)（315–335）
- 问题：当前文本已撤回“59 条全是 auth”，但 50-block 辅助表仍写成 41 auth、5 条“RAG 服务未就绪”，且漏掉其他根因。
- 可复现结果：从独立 archive baseline 和隔离 current 各跑同一选择集，59 个 FAILED nodeid 逐项完全一致。准确分类为：
  - 46 auth 403；
  - 7 个 stale RAG mock signature：`mock_query() got an unexpected keyword argument 'subject_id'`，不是服务未就绪；
  - 3 ImportError；
  - 1 coroutine 未 await 导致的 TypeError；
  - 1 `Mock history query error` 异常逸出；
  - 1 陈旧 group_id 期望。
- 建议：直接按全部 59 个 nodeid/trace 分类，删除依赖失败文本块正则的 41/5/3/1 表。

## LOW

### 1. Legacy 副本语义准确，但“逐字副本”措辞过头，且两条嵌套契约未执行

- 文件：[test_memory_four_state_api.py:369](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:369)（369–447）、[test_rag_four_state_api.py:202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:202)（202–260）
- 问题：与 HEAD 对照后，字段、必填性、类型、默认值、`Literal`、`ge/le` 约束均准确，没有把必填抄成可选；但并非源码字节级“逐字”，描述/example 被省略。更重要的是 concept 用 `timeline=[]`、RAG 用 `multimodal_results=[]`，因此两个 Legacy 嵌套模型没有真正参与解析。
- 建议：分别加入一个非空 timeline 和 multimodal item；将说明改为“验证语义等价副本”，或用冻结 JSON Schema 自动生成对照。

### 2. 状态登记的端点数、符号和调用计数均不实

- 文件：[状态词汇对齐登记.md:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-状态词汇对齐登记.md:28)、[同文件:111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-状态词汇对齐登记.md:111)、[同文件:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-状态词汇对齐登记.md:118)
- 问题：写成 3 个端点，实际是 4 个；引用不存在的 `memory.py::_trace_retrieval_status`；AST 实查实际 `log_decision()` Call 为 19 个，其中状态类 2、业务类 17，不是 20/18。
- 建议：改为 4、`decision_tracker.py::log_retrieval_status_decision`、19/17。

### 3. 验收单两处事实说明错误或不完整

- 文件：[验收单.md:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:109)、[验收单.md:276](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:276)、[memory_service.py:1077](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:1077)、[neo4j_edge_client.py:755](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/clients/neo4j_edge_client.py:755)
- 问题：所谓“服务层全部赋值点”漏列 review-suggestions 的 1077/1086/1089 三个出口；`LearningMemoryClient` 也不是“Neo4j 直连”，而是本地 JSON 文件客户端。两处不改变合法值域/零 HTTP 消费结论。
- 建议：补齐 `StatusedResult` 出口，并将客户端说明改成“本地 JSON 存储、不走 HTTP”。

### 4. 实际 untracked 范围超过用户给出的文件清单，变异脚本会原地写生产源码

- 文件：[mutation_gate_check_g43.py:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:10)（10–18、151–185）
- 问题：最终 `git status` 还包含未列出的 `evidence-g43/` 和零字节 `codex-review-CARD-G4-3.md`。变异脚本直接改当前工作树源文件再恢复；进程被强杀或存在并发编辑时，`finally` 不能保证安全，恢复还可能覆盖他人新改动。
- 建议：把证据目录纳入改动清单；变异测试改在 `git archive`/临时 worktree 中运行，不原地改审查目标。

## 确认无问题项

1. **加性纯度——确认无问题。** [memory_schemas.py:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/models/memory_schemas.py:150)、[rag.py:131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:131)：`git diff -U0 HEAD` 证明 episodes、concept history、RAG 的旧字段零删除、零改名、零类型收窄；新增两字段均 `Optional[...] = None`。

2. **信封豁免诚实性——确认无问题。** [memory_schemas.py:552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/models/memory_schemas.py:552)、[验收单.md:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:245)：明确写成“破坏性、非加性”，没有用加性措辞掩盖。消费证据的可复现性和范围问题见 MEDIUM-1。

3. **trace 枚举归一及接线——确认无问题。** [decision_tracker.py:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:114)：枚举成员和裸 value 字符串实测都落为 `degraded`/`unavailable`；四个端点只走该单点。测试 patch 的是实际 `app.core.decision_tracker.log_decision`，不是包装函数。异常隔离问题见 HIGH-1。

4. **端点不发明状态——确认无问题。** [memory.py:248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/memory.py:248)、[rag.py:301](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:301)：缺键均通过无默认的 `.get()`/模型默认得到 `null`，没有 `None → ok/empty` 路径。

5. **枚举 5xx 副作用登记及生产值域——确认无问题。** [验收单.md:94](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:94)、[service_status.py:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/models/service_status.py:73)、[nodes.py:572](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/lib/agentic_rag/nodes.py:572)：越界值导致 5xx 已显式登记；实际赋值点仅产生四个合法值或 `None`，`StatusedResult` 构造时还会强制枚举校验。

6. **硬边界——确认无问题。** 对 `rag_service.py`、`memory_service.py`、`chat.py`、`agents.py`、`nodes.py`、`backend/openapi.json` 比较 HEAD blob 与当前 `git hash-object`，六组完全一致。`get_review_suggestions_with_status()` 与兼容委托在 HEAD 已存在于 [memory_service.py:1018](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:1018)，端点换调用点不构成越界。

7. **chat/MCP 仅登记、OpenAPI 只登记不修——确认无问题。** [状态词汇登记.md:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-状态词汇对齐登记.md:38) 仅列后续计划；请求侧 scope 文件未动。[backend/openapi.json:5353](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/openapi.json:5353) 仍是旧数组 schema，且文件与 HEAD 相同；漂移已在验收单登记。

8. **既有选择集对账——确认零新增失败。** 独立隔离复跑：
   - baseline：`59 failed / 243 passed`，302 collected；
   - current：`59 failed / 302 passed`，361 collected；
   - 59 个 FAILED nodeid 逐项一致，双向差集均为空。
   
   两个改断言文件在 baseline 与 current 都是全红：25/25 + 21/21，均先被 auth 403 挡住；[验收单.md:337](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:337) 对“断言修改没有让它们转绿”的表述属实。新增两个 API 文件另行实跑为 59 passed。该结论仅覆盖验收单列出的选择集，不等同于全仓 CI。

限制：本轮没有可调用的 `graphiti-canvas` 工具，因此未执行其记忆事实搜索；未读取 Vault、`.env` 或私有数据，也未修改工作树。


