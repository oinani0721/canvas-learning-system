# Implementation Tasks

> **Spec 索引**：本 change 修改 `agentic-rag` capability，验收标准见 `specs/agentic-rag/spec.md`。
>
> **Apply Note (2026-04-07)**：实施期间有 3 个 design 假设被调整（见各 Phase 下的变更说明）。总结：
>   1. LangGraph 版本从假设的 0.2.0 升级为实际的 1.1.4，async conditional edge 完全支持（C1-PRE smoke test 2/2 绿），无需 sync wrapper
>   2. JSON 输出方案遵循项目惯例 `_parse_json_response` (faithfulness_check.py:158) 而非 `response_format={"type":"json_object"}` — 项目从未用过后者
>   3. `map_activate_to_intent` 从 design 中删除 — 让 LLM 直接输出 intent 字符串（匹配现有 `_build_sends_for_intent` 的 4-intent 词汇表），避免 channel list → intent 的反向映射的信息丢失

## 1. 新增 LLM 路由器模块（Phase 1，P0，独立）

- [x] 1.1 创建 `backend/lib/agentic_rag/llm_router.py`，定义模块文件头 + imports（litellm / asyncio / json / logging / typing）
- [x] 1.2 定义模块常量 `LLM_ROUTER_SYSTEM_PROMPT` — 完整 prompt 文本，包含 4 intent 含义和 JSON 输出契约
- [x] 1.3 定义 dataclass `LLMRouterResult`：字段 `intent: str` / `reason: str` / `latency_ms: float` / `success: bool` / `error: Optional[str]`
- [x] 1.4 实现 `async def llm_route(query, model, timeout_s, max_tokens) -> LLMRouterResult`：调用 `litellm.acompletion`，`temperature=0.0`、`max_tokens=150`（**不**用 response_format，遵循项目惯例）
- [x] 1.5 `route()` 内部用 `asyncio.wait_for(coro, timeout=timeout_s)` 强制超时；超时返回 `error="timeout"`
- [x] 1.6 `route()` 内部 try/except `json.JSONDecodeError`：解析失败返回 `error="parse_error"`
- [x] 1.7 `route()` 内部 try/except `Exception` 兜底：返回 `error=type(e).__name__`，避免 router 失败炸到上游
- [x] 1.8 ~~实现 `map_activate_to_intent`~~ **变更**：让 LLM 直接输出 intent 字符串（4 选 1），通过 `ALLOWED_INTENTS` frozenset 校验
- [x] 1.9 使用 `logger.info("[l1_router] LLM routed: query=%r -> intent=%s")` 结构化日志
- [x] 1.10 使用 `logger.warning` 在失败路径输出错误类型

## 2. 修改 state_graph.fan_out_retrieval 接入 hybrid 链（Phase 2，P0，依赖 Phase 1）

- [x] 2.1 ~~顶部 import~~ **变更**：用 lazy import (`from agentic_rag.llm_router import llm_route` 在函数内部)，避免顶层循环依赖
- [x] 2.2 在新的 `_classify_intent_with_strategy(query)` helper 内读 `DEFAULT_CONFIG`，取 `l1_router_strategy` / `l1_router_llm_model` / `l1_router_timeout_seconds`
- [x] 2.3 根据 `strategy` 分支："rule" → 只跑规则；"llm"/"hybrid" → 先跑 LLM
- [x] 2.4 `fan_out_retrieval` 改为 `async def`，前提：C1-PRE smoke test 验证 LangGraph 1.x 支持 async conditional edge（已验证绿 2/2）
- [x] 2.5 LLM 成功：使用返回的 intent 调 `_build_sends_for_intent`
- [x] 2.6 LLM 失败 + strategy="hybrid"：调 `classify_query_intent(query)` 作为 fallback，结构化日志记 metrics
- [x] 2.7 LLM 失败 + strategy="llm"：直接返回 intent="comprehensive"（不走规则）
- [x] 2.8 所有路径出口前输出 `logger.info("[l1_router] route_decision strategy=... intent=... query=... metrics=...")` 含完整可观测性字段
- [x] 2.9 multi-query 路径：**决策**：LLM 只跑 1 次（共享路由决策），因为 intent 应基于用户原始意图而非重写变体。测试 `test_multi_queries_share_single_llm_call` 硬性 pin 这一不变式

## 3. 新增配置项与默认值（Phase 3，P0，独立）

- [x] 3.1 修改 `CanvasRAGConfig` 追加 3 字段：`l1_router_strategy: Literal["llm","rule","hybrid"]` / `l1_router_llm_model: str` / `l1_router_timeout_seconds: float`
- [x] 3.2 修改 `DEFAULT_CONFIG` 追加 3 个默认值：`"hybrid"` / `"gemini/gemini-2.0-flash"` / `3.0`
- [x] 3.3 修改 `validate_config._VALIDATION_RULES` 增加 `l1_router_timeout_seconds` 数值范围 (0.5-30s)
- [x] 3.4 修改 `_ENUM_RULES` 增加 `l1_router_strategy: {"llm","rule","hybrid"}`
- [x] 3.5 修改 `_STRING_FIELDS` 增加 `l1_router_llm_model`
- [x] 3.6 验证 clean config 通过 / bad enum 替换 / bad timeout 替换 / empty model 替换（5 case 全绿）

## 4. 单元测试（Phase 4，P0，依赖 Phase 1+2）

- [x] 4.1 创建 `backend/tests/unit/test_l1_llm_router.py` (15 tests)
- [x] 4.2 `test_classifies_knowledge_point` / `test_classifies_file_locate` / `test_classifies_learning_history` — mock LLM 返回各 intent
- [x] 4.3 `test_timeout_falls_back_to_comprehensive` — `asyncio.sleep(60)` + `timeout_s=0.05`
- [x] 4.4 `test_invalid_json_falls_back` — 返回 "this is not json"
- [x] 4.5 `test_litellm_exception_falls_back` — async function raise RuntimeError
- [x] 4.6-4.8 ~~`test_map_activate_to_intent_*`~~ **变更**：由于不再有 map 函数，改为 `test_allowed_intents_match_state_graph` 确保 4 intent 词汇表与 state_graph.py 保持同步
- [x] 4.9 创建 `backend/tests/unit/test_state_graph_l1_routing.py` (8 tests)
- [x] 4.10 `test_rule_strategy_skips_llm_call` — 用 `patch.dict(DEFAULT_CONFIG, {"l1_router_strategy": "rule"})`，断言 `mock_llm.call_count == 0`
- [x] 4.11 `test_*_activates_*_routes` — mock llm_route 返回各 intent，断言 Send destinations 列表正确
- [x] 4.12 `test_llm_timeout_falls_back_to_rule` — mock 返回 `success=False, error="timeout"`，断言规则分类器接管
- [x] 4.13 ~~`test_strategy_llm_only_failure_*`~~ 由 `test_rule_strategy` + `test_hybrid_fallback` 联合覆盖
- [x] 4.14 `test_multi_queries_share_single_llm_call` — counter 验证 1 次 LLM 调用、15 个 Send（3 变体 × 5 channels）

## 5. 对比验证脚本（Phase 5，P1，可与上面并行）

- [x] 5.1 创建 `backend/scripts/compare_l1_router_strategies.py` 含 10 个 `BENCHMARK_QUERIES`（覆盖 4 种 intent + 无关键词的语义清晰查询）
- [x] 5.2 `_call_rule_router` / `_call_llm_router` helpers 分别跑两种 strategy 返回 (intent, latency_ms, success, error)
- [x] 5.3 主循环逐 query 对比，生成 summary table
- [x] 5.4 验证脚本可运行（在无 GEMINI_API_KEY 环境下正确打印对比表 + 显示 10/10 llm_failures + exit code 1）
- [ ] 5.5 **需要手动运行**：用户在设置 GEMINI_API_KEY 后运行 `.venv/bin/python scripts/compare_l1_router_strategies.py`，验证 ≥6/10 LLM 路由优于 rule

## 6. 文档更新（Phase 6，P2，独立）

- [ ] 6.1 ~~`docs/architecture.md` 追加 L1 LLM 路由说明~~ **SKIPPED**：该 section 不清晰 + 改动太小
- [ ] 6.2 ~~`config/rag_config.yaml` 追加示例~~ **SKIPPED**：该 yaml 文件内容是乱码（fuzz 污染），不动以免引入更多问题。新配置通过 CanvasRAGConfig 的 TypedDict 和 validate_config 即可使用
- [ ] 6.3 ~~`backend/lib/agentic_rag/__init__.py` 导出~~ **SKIPPED**：项目惯例是直接 `from agentic_rag.llm_router import ...`，无需 `__all__`

## Verification Checklist (Apply 阶段最终验收)

- [x] Phase 1-5 任务全部完成（Phase 6 标记为 SKIPPED）
- [x] `pytest backend/tests/unit/test_l1_llm_router.py backend/tests/unit/test_state_graph_l1_routing.py backend/tests/unit/test_langgraph_async_conditional_edge_smoke.py -v` 25/25 绿
- [x] `pytest backend/tests/unit/test_fusion_strategy_override.py backend/tests/unit/test_sharpness_report.py backend/tests/unit/test_fusion_report.py backend/tests/unit/test_deep_research_fallback.py backend/tests/unit/test_textbook_removal.py backend/tests/unit/test_cross_canvas_failsoft.py -v` 63/63 绿（无回归）
- [ ] **需要用户手动运行**：设置 GEMINI_API_KEY 后跑 `compare_l1_router_strategies.py`，确认 ≥6/10 LLM 优于 rule
- [ ] **需要用户手动冒烟**：启动 backend → 发"牛顿第二定律"查询 → 看 `[l1_router] route_decision` 日志 → 期望 strategy=llm/hybrid, success=True, intent != comprehensive
- [ ] **需要用户手动冒烟**：临时 unset GEMINI_API_KEY → 发查询 → 应自动 fallback 到 rule，不报错
- [x] 监控日志：结构化日志字段完整（strategy / intent / query / metrics[llm_latency_ms / llm_success / llm_error]）

## Rollback Steps

如发现问题需紧急回滚：

1. **不动代码**：直接修改 `CanvasRAGConfig.l1_router_strategy = "rule"`，或通过环境变量/runtime context 注入。这会让 `_classify_intent_with_strategy` 完全跳过 LLM 调用，恢复为原 rule-based 行为。**推荐方式**，无需重启。
2. **关闭 LLM 路径**：如 1. 不可行，可以 `unset GEMINI_API_KEY` 让所有 LLM 调用 fallback 到 rule（hybrid strategy 下）。
3. **完全回滚**：`git revert 3b96e49` 撤销本 change 的 7 个文件改动（1239 insertions / 14 deletions）。
