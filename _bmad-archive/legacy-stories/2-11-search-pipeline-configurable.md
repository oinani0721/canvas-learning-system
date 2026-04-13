# Story 2.11: Phase 2 — 搜索管道参数可配置化

Status: ready-for-dev

## Story

As a 开发者,
I want 搜索管道的融合权重、质量阈值、reranker 策略等参数通过配置文件调整,
so that 可以在真实数据上调优而无需改代码。

## Acceptance Criteria

1. **AC-1: 完整配置项清单**
   - **Given** 搜索管道包含多个可调参数
   - **When** 查看配置文件
   - **Then** 以下参数全部可配置化（非硬编码）：
     - RRF k 值（默认 60）
     - 融合分组映射（Dense 组 / Graph 组 / Personal 组的通道分配）
     - 融合策略（`layered_rrf` / `rrf` / `weighted`）
     - CRAG 质量门控 model（质量评估用的 LLM 模型名）
     - CRAG max_rewrite 次数（默认 2）
     - Reranker 模型名（默认 `gte-reranker-modernbert-base`）
     - Reranker torch_dtype（默认 `float16`）
     - Adaptive-k buffer / min_k / max_k（默认 5/3/15）
     - 上下文压缩 max_tokens（默认 3000）
     - 掌握度注入 enabled（默认 True）
     - 渐进范围搜索 enabled / min_results_threshold
     - 邻居扩展 enabled / max_count / score_decay
     - Tag Jaccard 桥接 enabled / threshold
     - 搜索超时 timeout_seconds（默认 10）
     - OCR 模型名

2. **AC-2: 配置热加载——无需重启**
   - **Given** 配置文件被修改
   - **When** 下次搜索请求到达
   - **Then** 自动使用最新配置（无需重启 FastAPI 服务）
   - **And** 配置加载延迟 < 10ms（不影响搜索性能）
   - **And** 配置加载方式：每次请求时从 `merge_config()` 读取最新值，或文件监视自动刷新

3. **AC-3: 配置验证与告警**
   - **Given** 配置文件中某个参数值异常（如 RRF k < 0、max_tokens = 0）
   - **When** 配置加载
   - **Then** 验证所有参数的合法性（类型检查 + 范围检查）
   - **And** 无效参数：记录 WARNING 日志 + 使用默认值（不崩溃、不静默回退）
   - **And** 日志格式：`[CONFIG-WARN] Invalid value for {param}: {value}, using default {default}`
   - **And** 配置文件缺失时使用全部默认值 + 记录 INFO 日志

4. **AC-4: LangGraph Context API 配置传递**
   - **Given** Story 2.1 已修复 adapter.py L195 配置传递 bug
   - **When** 管道执行
   - **Then** 所有配置参数通过 LangGraph Context API 正确传递到管道每个节点
   - **And** 每个节点（fan_out、fuse、rerank、check_quality、compress）都能读取到配置
   - **And** 验证：在节点中 `config = context.get("config")` 返回完整配置对象

5. **AC-5: 配置文件格式与位置**
   - **Given** 搜索管道参数需要一个持久化配置入口
   - **When** 配置管理
   - **Then** 配置通过 YAML 或 JSON 文件存储（路径可配置，默认 `config/rag_config.yaml`）
   - **And** 配置文件格式清晰，每个参数有注释说明用途和默认值
   - **And** 支持通过 FastAPI API 端点查询当前生效的配置（`GET /api/v1/rag/config`）
   - **And** 支持通过 API 端点动态更新配置（`PUT /api/v1/rag/config`）

## Tasks / Subtasks

- [ ] **Task 1: 统一配置 Schema** (AC: #1)
  - [ ] 1.1 审查 `src/agentic_rag/config.py` 的 `CanvasRAGConfig`，汇总 Story 2.3-2.10 中新增的所有配置项
  - [ ] 1.2 确保所有配置项都在 `CanvasRAGConfig` TypedDict 中有定义（类型注解 + 默认值）
  - [ ] 1.3 按功能模块分组注释：
    - `# === 融合配置 ===`
    - `# === 精排配置 ===`
    - `# === 质量门控配置 ===`
    - `# === 压缩配置 ===`
    - `# === 过滤与扩展配置 ===`
    - `# === 图片配置 ===`
  - [ ] 1.4 更新 `DEFAULT_CONFIG` 包含所有新增配置项的默认值
  - [ ] 1.5 更新 `merge_config()` 确保所有配置项正确合并（用户值优先，缺失用默认值）

- [ ] **Task 2: 配置验证器** (AC: #3)
  - [ ] 2.1 新增 `validate_config(config: CanvasRAGConfig) -> CanvasRAGConfig` 函数
  - [ ] 2.2 定义每个参数的验证规则：
    - `rrf_k`: int, >= 1
    - `max_rewrite_iterations`: int, 0-5
    - `quality_threshold`: float, 0.0-1.0
    - `adaptive_k_min`: int, >= 1
    - `adaptive_k_max`: int, >= adaptive_k_min
    - `context_max_tokens`: int, >= 100
    - `neighbor_score_decay`: float, 0.0-1.0
    - `tag_jaccard_threshold`: float, 0.0-1.0
    - `timeout_seconds`: int, >= 1
  - [ ] 2.3 无效参数替换为默认值 + 记录 WARNING 日志
  - [ ] 2.4 在 `merge_config()` 末尾调用 `validate_config()`

- [ ] **Task 3: 配置文件支持** (AC: #5)
  - [ ] 3.1 新增 `load_config_from_file(file_path: str) -> Optional[Dict]` 函数：支持 YAML 格式（`pyyaml`）
  - [ ] 3.2 默认配置文件路径：`config/rag_config.yaml`（相对于项目根目录）
  - [ ] 3.3 配置文件不存在时使用全部默认值 + 记录 INFO 日志
  - [ ] 3.4 生成默认配置文件模板（含注释）：`generate_default_config_file(output_path: str)`
  - [ ] 3.5 在 `merge_config()` 中集成文件配置加载：文件配置 → 运行时传入配置 → 默认配置（优先级从高到低）

- [ ] **Task 4: 配置 API 端点** (AC: #5)
  - [ ] 4.1 新增 `GET /api/v1/rag/config` 端点：返回当前生效的完整配置
  - [ ] 4.2 新增 `PUT /api/v1/rag/config` 端点：接收部分配置更新，持久化到配置文件
  - [ ] 4.3 配置更新后自动触发验证（`validate_config`）
  - [ ] 4.4 配置更新日志：`[CONFIG] Updated {param}: {old_value} → {new_value}`

- [ ] **Task 5: LangGraph Context 传递验证** (AC: #4)
  - [ ] 5.1 在管道的每个关键节点（fan_out_retrieval、fuse_results、rerank_results、check_quality、compress_context）中添加配置读取验证日志
  - [ ] 5.2 确认 `adapter.py` 的配置传递修复（Story 2.1）已正确工作
  - [ ] 5.3 测试：修改 RRF k 值 → 执行搜索 → 确认日志中 fuse_results 使用了新的 k 值
  - [ ] 5.4 测试：修改 reranker 模型名 → 执行搜索 → 确认 rerank_results 加载了新模型

- [ ] **Task 6: 配置热加载** (AC: #2)
  - [ ] 6.1 实现方案：每次 `merge_config()` 调用时重新读取配置文件（文件 I/O < 1ms，可接受）
  - [ ] 6.2 可选优化：配置文件 mtime 缓存，只在文件修改时重新加载
  - [ ] 6.3 验证：修改配置文件 → 不重启服务 → 下次搜索使用新配置

- [ ] **Task 7: 端到端验证** (AC: #1-#5)
  - [ ] 7.1 准备测试场景：
    - 修改 RRF k 值 → 搜索结果排序变化
    - 修改 Adaptive-k max_k → 返回结果数量变化
    - 设置无效参数（k=-1）→ WARNING 日志 + 使用默认值
    - 删除配置文件 → INFO 日志 + 全部使用默认值
    - API 查询当前配置 → 返回完整配置 JSON
    - API 更新配置 → 下次搜索生效
  - [ ] 7.2 `ruff check src/agentic_rag/ backend/app/` 全量 lint 通过
  - [ ] 7.3 `ruff format --check src/agentic_rag/ backend/app/` 格式检查通过
  - [ ] 7.4 确认无 mock 数据、无 TODO 空函数、无假实现（DD-03）

## Dev Notes

### Brownfield 上下文——已有代码资产

这是 **Brownfield 项目**，`CanvasRAGConfig` 和 `merge_config()` 已存在但配置项不完整，且 Story 2.1 修复了 adapter.py L195 的配置传递 bug。本 Story 在此基础上完善配置体系。

#### 关键文件清单

| 文件 | 当前状态 | 本 Story 修改内容 |
|------|---------|-----------------|
| `src/agentic_rag/config.py` | `CanvasRAGConfig` 有基础字段，Story 2.3-2.10 各自新增了部分字段 | **统一所有配置项 + 验证器 + 文件加载** |
| `backend/app/api/v1/endpoints/rag.py` | RAG 相关 API 端点 | **新增配置查询和更新端点** |
| `src/agentic_rag/nodes.py` | 节点中直接使用 config 参数 | **确认所有节点正确从 context 读取配置** |
| `src/agentic_rag/state_graph.py` | 图构建和 adapter 配置传递 | **验证配置传递正确性** |

#### 配置传递链路

```
用户/API 设置参数
  → config/rag_config.yaml 文件 OR API PUT /rag/config
  → merge_config() 合并（文件 > 运行时 > 默认值）
  → validate_config() 验证
  → adapter.py context 传递（Story 2.1 已修复 L195）
  → LangGraph Context API
  → 每个节点 context.get("config") 读取
```

### 依赖关系

- **前置 Story 2.1**（死代码清理与配置修复）：adapter.py L195 配置传递 bug 已修复
- **前置 Story 2.3-2.10**：各 Story 新增的配置项需要在本 Story 中统一管理
- **后续所有搜索相关开发**：本 Story 建立的配置体系是后续调优的基础

### 技术决策

1. **配置文件格式**：YAML（人类可读、支持注释），而非 JSON（不支持注释）或 TOML。
2. **热加载策略**：每次请求重读文件（文件 I/O < 1ms，120 文件规模无压力），不引入 watchdog 文件监视（过度复杂）。
3. **配置优先级**：运行时 API 传入 > 配置文件 > 硬编码默认值。
4. **验证策略**：无效参数回退默认值 + WARNING 日志，不崩溃。保证生产环境稳定性。

### 关键代码位置

| 组件 | 文件路径 |
|------|---------|
| 配置定义 | `src/agentic_rag/config.py`（`CanvasRAGConfig` / `DEFAULT_CONFIG` / `merge_config`） |
| 配置传递 | `src/agentic_rag/state_graph.py`（adapter / context） |
| RAG API | `backend/app/api/v1/endpoints/rag.py` |
| 各管道节点 | `src/agentic_rag/nodes.py`（config 消费方） |

### 不做的事项（防蔓延 DD-10）

- 不修改管道逻辑（只配置化已有参数）
- 不实现前端配置 UI（Epic 1 Settings Tab 的范围）
- 不实现配置版本管理或 A/B 测试框架
- 不实现动态加载 Python 模块（如动态切换 reranker 实现类）
- 不实现配置加密或访问控制

### FR 覆盖映射

| FR ID | AC 映射 | 说明 |
|-------|---------|------|
| FR-OPS-02 | AC-1, AC-2, AC-3, AC-5 | 搜索管道参数可配置 |

### Project Structure Notes

- 本 Story 修改范围：`src/agentic_rag/config.py`（主要）、`backend/app/api/v1/endpoints/rag.py`（API）
- 新增 `config/rag_config.yaml` 配置文件
- `pyyaml` 依赖需确认在 `requirements.txt` 中已包含
- 配置项命名采用 snake_case，与 Python 风格一致

### References

- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#能力域 4：配置与运维] — FR-OPS-01/02 定义
- [Source: _bmad-output/planning-artifacts/prd-backend-retrieval-pipeline.md#可靠性] — 配置失效时日志告警，不静默回退默认值
- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.11] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md] — LangGraph Context API 配置传递
- [Source: src/agentic_rag/config.py] — 当前 CanvasRAGConfig 和 merge_config 实现
- [Source: src/agentic_rag/state_graph.py] — adapter 配置传递逻辑

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
