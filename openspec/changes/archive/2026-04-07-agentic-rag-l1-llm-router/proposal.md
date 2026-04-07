# Upgrade Agentic-RAG L1 Router from Keyword Rules to LLM-based Routing

## Why

A9 用户原始诉求（`docs/project-status/fr-exploration/A9.md:30`）明确指出当前 L1 路由"算法不够灵活智能"，原话：

> "如果算法不够灵活智能，那么 dumb tool, smart agent，交给 opus 4.6 来进行成熟的判断，或者 deep explore 社区找到进一步更加成熟聪明的方案。"

经 4 个 Explore Agent 实地核实（`backend/lib/agentic_rag/state_graph.py:65-243`），当前 `classify_query_intent()` 是关键词规则匹配——遇到 `"笔记"/"文件"` 走 file_locate；遇到 `"之前"/"复习"/"历史"` 走 learning_history；其余全部退化为 comprehensive（5 路全开）。这种实现的 3 个问题：

1. **关键词覆盖率低**：实测 70%+ 查询命中"comprehensive"分支（即 5 路全开），路由相当于没做。例如 `"万有引力的计算公式"` 根本不含任何关键词，被默认丢给 comprehensive。
2. **没有语义理解**：`"我之前学过的导数题目里有哪些是错的"` 同时包含 history+verification 意图，规则只匹配第一个命中的 `"之前"`，丢失第二个意图。
3. **维护成本高**：关键词列表是项目内部硬编码，新增意图必须改代码 + 改 list，无法用配置或样本驱动。

Story 2.6 AC-5 在创建时已经在代码注释里写明 "**MVP 阶段使用规则分类，LLM 分类为远期增强**"（`state_graph.py:76-77`）—— 本 change 就是落地这个"远期增强"。

### 历史背景

| 阶段 | 实现 | 备注 |
|------|------|------|
| Story 2.6 (2025-Q4) | 规则分类（5 路 fan-out） | MVP，注释明确"远期升级 LLM" |
| FR-KG-04 探索（2026-04） | 用户在 A9 批注重申"smart agent"诉求 | 触发本 change |

### 不在范围

- ❌ 不动 5 路检索器实现（`retrieve_graphiti / retrieve_lancedb / retrieve_multimodal / retrieve_cross_canvas / retrieve_vault_notes`）
- ❌ 不动融合策略（`layered_rrf` 是默认，已在 `nodes.py:409-927` 实现 4 种）
- ❌ 不动重排序（local + cohere 双引擎已在 `reranking.py` 落地）
- ❌ 不动质量门控（CRAG binary grading 已实现）
- ❌ 不引入分类器训练（项目无标注数据）

## What Changes

### 目标

把 L1 路由器从单一规则匹配升级为 **LLM 路由 + 规则 fallback + safe degradation** 的三层 hybrid 链，由配置开关控制策略选择。

### 范围

**做**：

- **新增 `backend/lib/agentic_rag/llm_router.py`**：LiteLLM 调用 `gemini/gemini-2.0-flash`，输出 JSON `{"activate": [...], "reason": "..."}`，含超时/JSON 解析/异常兜底。
- **修改 `backend/lib/agentic_rag/state_graph.py:fan_out_retrieval`**：接入 hybrid fallback 链 — 先 LLM → 失败/超时回退到 `classify_query_intent` → 再失败兜底全 5 路。
- **新增 3 个配置项到 `backend/lib/agentic_rag/config.py:CanvasRAGConfig`**：
  - `l1_router_strategy: Literal["llm", "rule", "hybrid"]`（默认 `"hybrid"`）
  - `l1_router_llm_model: str`（默认 `"gemini/gemini-2.0-flash"`）
  - `l1_router_timeout_seconds: float`（默认 `3.0`）
- **新增可观测日志**：每次路由决策记录 `query / strategy / activated_paths / latency_ms / fallback_used`。
- **新增对比验证脚本** `backend/scripts/compare_l1_router_strategies.py`：10 个典型查询对比 rule vs llm vs hybrid 的路径选择。
- **单元测试**：mock LLM 响应（成功/超时/JSON 异常），验证 fallback 链路径。

**不做（延后）**：

- ❌ 不增加 router 训练数据收集（独立 change）
- ❌ 不替换为本地 Qwen3-8B 路由（成本/延迟评估后再看）
- ❌ 不动 `_build_sends_for_intent` 的 4 种 intent 静态映射（intent → channels 映射本身可用，本 change 只换 intent 来源）
- ❌ 不为 LLM 路由增加缓存层（首版不做，依据观测决定）

### 与已存在 change 的关系

| Change | 关系 |
|--------|------|
| `fix-fr-kg-04-schema-drift-and-sync-hardening` | **正交** — 处理"数据进图谱"的同步管道，本 change 处理"数据出图谱"的检索路由 |
| `fix-rag-transform-and-episode-isolation` | **正交** — 处理 RAG transform 字段完整性，与路由层不冲突 |
| `fr-kg-04-sync-pipeline-fix` | **正交** — sync 管道修复 |
| `review-enrichment-signal-fix` | **同批姊妹 change** — A9 修复的另一半（G-SILENT-001 schema 漏字段） |

## Capabilities

### Modified Capabilities

- `agentic-rag`: L1 路由契约扩展 — 新增"LLM 路由策略"作为首选实现，规则路由降级为 fallback。fan_out_retrieval 仍保证返回非空 Send 列表（safe degradation 兜底）。

### New Capabilities

无（本 change 不引入新能力，只把已有 L1 路由能力从规则升级为 LLM）。

## Impact

### Affected Code

**Backend agentic_rag**:

- `backend/lib/agentic_rag/llm_router.py` (新文件) — LLM 路由实现
- `backend/lib/agentic_rag/state_graph.py:65-243` — `fan_out_retrieval` 接入 hybrid 链；`classify_query_intent` 保留作为 fallback
- `backend/lib/agentic_rag/config.py:72-147` — `CanvasRAGConfig` 新增 3 字段；`DEFAULT_CONFIG` 加默认值；`validate_config` 加校验规则
- `backend/lib/agentic_rag/config.py:217-385` — `validate_config` 增加 `l1_router_strategy` enum 校验、`l1_router_llm_model` string 校验、`l1_router_timeout_seconds` 数值范围校验

**Tests**:

- `backend/tests/unit/test_l1_llm_router.py` (新) — 5 个场景：成功路由 / 超时回退 / JSON 解析异常 / API 异常 / strategy=rule 跳过 LLM
- `backend/tests/unit/test_state_graph_l1_routing.py` (新) — 验证 hybrid 链端到端

**Scripts**:

- `backend/scripts/compare_l1_router_strategies.py` (新) — 10 个典型查询对比表生成器

### Affected APIs

- 无 API breaking change
- `fan_out_retrieval(state)` 签名不变，仍返回 `list[Send]`
- 新配置项可通过 `config/rag_config.yaml` 或 `graph.invoke(..., context=config)` 注入

### Affected Dependencies

- 无新增 Python 依赖（LiteLLM 已在项目中使用）
- 新增 LLM 调用成本：典型查询 ~50 input + ~30 output token，按 Gemini 2.0 Flash 单价约 $0.001/req

### Systems

- **LangGraph**：fan_out_retrieval 是 conditional edge，函数签名/返回类型不变
- **LiteLLM**：复用现有 `quality_check_model / multi_query_model` 的调用模式
- **配置系统**：`merge_config` 自动加载新字段，向后兼容

### Not Changing

- `_build_sends_for_intent(intent, state)` 的 intent → channels 映射（4 种 intent 静态映射本身合理，本 change 只换 intent 的产生方式）
- `retrieve_*` 5 个检索器节点
- `nodes.py:409-927` 的融合策略
- `reranking.py` 双引擎
- 质量门控 / 查询改写 loop

### Verification

**功能验证**（实施时执行）：

1. **10 查询对比表**：跑 `compare_l1_router_strategies.py`，对比 rule vs llm vs hybrid 的路径选择，至少 6/10 LLM 选择优于 rule（即 LLM 给出更精准的子集，而 rule 退回 comprehensive）
2. **fallback 链测试**：mock LiteLLM 抛超时 → 断言 hybrid 自动切到 rule；mock rule 异常 → 断言兜底全 5 路
3. **延迟基线**：LLM 路由 p50 < 1500ms / p99 < 3000ms（受 timeout 保护）
4. **配置切换**：`l1_router_strategy="rule"` 时完全跳过 LLM 调用（断言 LiteLLM 0 次）

**回归验证**：

- 现有 `test_state_graph.py` / `test_routing.py` 全绿
- `pytest backend/tests/unit/test_l1_llm_router.py -v` 新测试通过

### Rollback

**单步回滚**：在 `config/rag_config.yaml` 设置 `l1_router_strategy: "rule"`，不需要改代码、不需要重启即可回到原行为。

**完全回滚**：

1. revert `state_graph.py` 的 `fan_out_retrieval` 改动
2. revert `config.py` 的 3 个新字段
3. 删除 `llm_router.py` / 测试 / 脚本

### Risk

| 风险 | 概率 | 缓解 |
|------|------|------|
| LLM 调用延迟 ≥ 2s 影响体验 | 中 | `l1_router_timeout_seconds=3.0` 强制超时 + fallback；监控 p99 |
| LLM JSON 输出格式错乱 | 中 | `temperature=0.0` + `max_tokens=100` + 严格 JSON parse + 失败回退到 rule |
| Gemini API 配额耗尽 | 低 | 监控 `l1_router_llm_calls_total` metric；超阈值降级 strategy=rule |
| LLM 把所有查询都路由到全 5 路（等同于不路由） | 中 | 对比验证脚本兜底，发现退化时改 prompt |
| 成本增加 | 低 | 50+30 token × ~$0.001 = 单查询成本 ~0.001 美元；月活 1000 查询 ≈ 1 美元 |

## 探索记录

详细分析见：

- `docs/project-status/fr-exploration/A9.md`（用户原始诉求）
- `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md`（FR-KG-04 主线探索）
- 4 个 Explore Agent 代码核实报告（2026-04-06）
- ChatGPT Deep Research 报告 #8 交叉验证

### 未在本 change 范围内的探索发现（仅作记录）

- **L1 routing latency 已实测 < 1ms**（规则版本）— 升级 LLM 后 p99 ≤ 3s 是显著退化，但被 hybrid fallback 兜住
- **70%+ 查询走 comprehensive 分支**— 实测数据来自 `state_graph.py` log 抽样，本 change 验证步骤需要重新跑
- **`_build_sends_for_intent` 的 4 种 intent 映射本身合理**—不动它，只换 intent 来源
