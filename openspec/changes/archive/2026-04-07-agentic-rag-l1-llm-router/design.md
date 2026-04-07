# Design — Agentic-RAG L1 LLM Router

## D1. 为什么用 LLM 而不是分类器？

### 问题

`classify_query_intent` 是关键词规则匹配（`state_graph.py:65-129`），70%+ 查询命中默认 comprehensive 分支。要升级到"smart agent"路径，候选方案有 3 种。

### 候选方案

| 方案 | 实现 | 标注数据 | 延迟 | 维护 | 选择 |
|------|------|---------|------|------|------|
| A | 用户更细的关键词列表 | ❌ 不需要 | <1ms | 🔴 高（每加意图改代码） | ❌ 现状的延伸，治标 |
| B | 训练 sklearn 分类器 (LR/SVM) | ⚠️ 需要 200+ 标注样本 | <10ms | 🟡 中（重训需要数据 pipeline） | ❌ 项目无标注数据 |
| C | 训练 BERT 微调分类器 | 🔴 需要 1000+ 标注样本 + GPU | <100ms | 🔴 高（模型版本管理） | ❌ 重，不符合 MVP |
| D | LLM zero-shot 路由 (Gemini Flash) | ✅ 不需要 | 500-2000ms | 🟢 低（改 prompt 即可） | ✅ 选择 |
| E | 本地 LLM 路由 (Qwen3-8B Ollama) | ✅ 不需要 | 200-1000ms | 🟢 低 | ⚠️ 延后评估（M5Max 决策待） |

### 选 D 的理由

- **用户明确要求"smart agent"路径**——LLM 是最直接的"smart"实现，符合 A9 原话 "交给 opus 4.6 进行成熟的判断"
- **零标注数据**——项目目前没有 query → intent 的标注样本，分类器路径走不通
- **Gemini Flash 成本足够低**——~50+30 token、~$0.001/query，月活 1000 查询年成本 ~$12
- **维护成本最低**——加新意图只需要改 prompt 模板，不需要训模型不需要改代码
- **fallback 安全**——LLM 失败时退回到现有规则，**最坏情况等于现状**，无下行风险

### 选 D 而非 E 的理由

本地 Qwen3-8B 的延迟在 M1/M2 Mac 上不可控（200ms-1500ms 抖动），且依赖 Ollama 服务在线。用户决策 `decision_s40_priorities` 中明确"M5Max 本地模型"延后到优先级 3，本 change 不依赖该决策。

## D2. Prompt 设计

### 输入

```
SYSTEM:
你是 Canvas Learning System 的检索路由器。给定用户查询，决定激活以下 5 路检索器中的哪几路：

1. graphiti — Neo4j 知识图谱，适合"概念间关系/学习历史/复习记录/掌握度"类查询
2. lancedb — bge-m3 向量库，适合"知识点定义/笔记内容语义匹配"类查询
3. multimodal — OCR 后的图片/PDF，适合"图表/公式/截图内容"类查询
4. cross_canvas — 跨白板标签关联，适合"我在别的白板学过类似概念吗"类查询
5. vault_notes — Markdown 笔记文件，适合"按文件名/路径定位笔记"类查询

只输出 JSON，格式：{"activate": ["lancedb", "vault_notes"], "reason": "查询是知识点定义"}
不要输出任何额外文字。

USER:
查询: {query}
```

### 约束

- `temperature=0.0` — 确定性输出
- `max_tokens=100` — 强制紧凑（避免 LLM 长篇大论）
- `timeout=l1_router_timeout_seconds`（默认 3.0s）— hard timeout
- `response_format={"type": "json_object"}` — 强制 JSON 模式（Gemini Flash 支持）

### 输出示例

| 查询 | LLM 输出 |
|------|---------|
| `"万有引力的计算公式"` | `{"activate": ["lancedb", "vault_notes"], "reason": "知识点定义查询"}` |
| `"我之前学过的导数题目里有哪些是错的"` | `{"activate": ["graphiti", "lancedb"], "reason": "学习历史 + 验证记录"}` |
| `"导数 vs 微分 有什么区别"` | `{"activate": ["lancedb", "graphiti", "cross_canvas"], "reason": "概念对比 + 跨白板"}` |
| `"找一下我笔记里关于傅里叶变换的内容"` | `{"activate": ["vault_notes", "lancedb"], "reason": "按文件定位笔记"}` |

## D3. Fallback 链（Hybrid 策略）

### 数据流

```
fan_out_retrieval(state)
   │
   ▼
查 config: l1_router_strategy
   │
   ├─ "rule" → 直接走 classify_query_intent → _build_sends_for_intent → 返回
   │
   ├─ "llm"  → 走 llm_router.route(query) → _build_sends_for_intent → 返回
   │            ↓ 失败
   │          fallback 全 5 路（safe degradation）
   │
   └─ "hybrid" (默认)
        │
        ▼
       llm_router.route(query, timeout=3.0)
        │
        ├─ 成功 + 有效 JSON → 抽 intent → _build_sends_for_intent → 返回（log fallback_used=False）
        │
        └─ 失败/超时/JSON解析失败
            │
            ▼
           classify_query_intent(query)（log fallback_used=True, reason=...）
            │
            ├─ 成功 → _build_sends_for_intent → 返回
            │
            └─ 异常 → 全 5 路（双重兜底）
```

### intent 抽取逻辑

LLM 输出的 `activate` list 不直接当 channels 用，而是反向映射到 4 种 intent 之一（兼容现有 `_build_sends_for_intent`）：

| LLM activate | 抽出的 intent |
|--------------|--------------|
| 含 `vault_notes` 且 ≤2 路 | `file_locate` |
| 含 `graphiti` 且不含 `multimodal` | `learning_history` |
| ≥4 路 | `comprehensive` |
| 其余 | `comprehensive`（保守） |

**为什么不直接用 LLM 的 activate list 当 channels？**

- 兼容现有 `_build_sends_for_intent` 的 4 种 intent 映射，减少改动面
- intent 映射经过测试稳定，直接用 LLM 输出可能产生未覆盖组合
- 后续 change 可以直接让 LLM 输出 channels 而不经过 intent，但本 change 不动这层

### 配置 vs 默认

| 配置 | 行为 |
|------|------|
| `l1_router_strategy="rule"` | 完全跳过 LLM（向后兼容 / 紧急回滚） |
| `l1_router_strategy="llm"` | 强制 LLM，失败兜底全 5 路（无规则 fallback） |
| `l1_router_strategy="hybrid"`（默认） | LLM 优先，失败回退规则，再失败全 5 路 |

## D4. 可观测性

### 结构化日志（每次路由决策一条）

```python
logger.info(
    "[l1_router] route_decision",
    extra={
        "query": query[:100],
        "strategy": "hybrid",
        "llm_called": True,
        "llm_latency_ms": 850,
        "llm_success": True,
        "fallback_used": False,
        "fallback_reason": None,
        "intent": "knowledge_point",
        "activated_channels": ["lancedb", "vault_notes"],
        "channel_count": 2,
    }
)
```

失败场景：

```python
logger.warning(
    "[l1_router] llm_failed_fallback_to_rule",
    extra={
        "query": query[:100],
        "strategy": "hybrid",
        "llm_latency_ms": 3050,  # 超时
        "fallback_reason": "TimeoutError",
        "fallback_intent": "comprehensive",
    }
)
```

### Metrics（不在本 change 范围，列出供下游 change 接入）

- `l1_router_llm_calls_total` — counter，分 strategy 和 success
- `l1_router_llm_latency_seconds` — histogram
- `l1_router_fallback_total` — counter，分 reason
- `l1_router_intent_distribution` — counter，分 intent

## D5. 配置开关与默认值

### 新增配置项

```python
class CanvasRAGConfig(TypedDict, total=False):
    # ...existing fields...

    # === L1 Router (新增) ===
    l1_router_strategy: Literal["llm", "rule", "hybrid"]  # 路由策略，默认 hybrid
    l1_router_llm_model: str   # LLM 模型名，默认 gemini/gemini-2.0-flash
    l1_router_timeout_seconds: float  # LLM 调用 timeout，默认 3.0s
```

### 默认值

```python
DEFAULT_CONFIG = CanvasRAGConfig(
    # ...existing defaults...

    # === L1 Router 默认值 ===
    l1_router_strategy="hybrid",   # MVP 期间采用 hybrid 兜底，正式运行后可改为 "llm"
    l1_router_llm_model="gemini/gemini-2.0-flash",
    l1_router_timeout_seconds=3.0,
)
```

### 校验规则（追加到 `validate_config`）

```python
_ENUM_RULES["l1_router_strategy"] = {"llm", "rule", "hybrid"}
_VALIDATION_RULES["l1_router_timeout_seconds"] = {"type": (int, float), "min": 0.5, "max": 30.0}
_STRING_FIELDS.append("l1_router_llm_model")
```

为什么默认是 `hybrid` 而不是 `llm`：

- MVP 期间任何 LLM 异常（API key 失效、网络抖动、配额超限）都不应该直接破坏检索功能
- `hybrid` 的最坏情况 = 现状（规则路由），下行风险为零
- 实施 1-2 周后观察 metrics，发现 fallback rate 稳定 < 1% 后可以改为 `llm`

## 数据流变化对比

### 改动前（state_graph.py:170-243）

```
query → classify_query_intent (规则) → intent → _build_sends_for_intent → Send list
```

单分支路径，所有失败兜底全 5 路。

### 改动后

```
query → fan_out_retrieval
          ↓
        config.l1_router_strategy
          ↓
        ┌──────────┬──────────┐
        ↓          ↓          ↓
      "rule"    "llm"      "hybrid"
        │         │           │
classify_query   llm_router   llm_router (3s timeout)
   _intent      .route()       │
        │         │            ├─ ✅ → 抽 intent
        │         │            └─ ❌ → classify_query_intent
        │         │                       │
        ▼         ▼                       ▼
        intent → _build_sends_for_intent → Send list
```

## 与 Story 2.6 AC-5 的契约延续

Story 2.6 AC-5 的契约是 "fan_out_retrieval 必须返回非空 Send list 且包含至少 1 个有效 retrieval node"，本 change **不破坏**这个契约：

- LLM 成功 → intent → _build_sends_for_intent → 与原契约完全一致
- LLM 失败 → 规则 fallback → 与原契约一致
- 双重失败 → 全 5 路兜底 → 与原契约一致（仍是非空）

`_build_sends_for_intent` 的实现完全不动，所以下游 5 个 retrieval node 的输入契约也不变。
