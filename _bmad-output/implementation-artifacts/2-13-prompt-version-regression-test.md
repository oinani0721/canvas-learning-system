# Story 2.13: Prompt 版本管理与回归测试

Status: ready-for-dev

## Story

As a 开发者,
I want Prompt 模板有版本管理，变更后自动触发回归测试，
So that Prompt 修改不会意外降低 AI 质量。

## Acceptance Criteria

1. **AC-1: Prompt 模板版本化存储**
   - **Given** 后端 `prompts/` 目录存放 LLM 系统 prompt 模板
   - **When** 开发者需要修改 Prompt 模板（检索相关：查询改写、CRAG 判定等）
   - **Then** 创建新版本文件（如 `autoscore_v2.md`），旧版本保留不删除
   - **And** 每个 Prompt 文件头包含元数据注释（引用方 service、版本号、创建日期、变更说明）
   - **And** `CHANGELOG.md` 记录每次版本变更的原因和影响范围

2. **AC-2: PromptRegistry 统一加载管理**
   - **Given** 后端服务启动
   - **When** PromptRegistry 初始化
   - **Then** 自动扫描 `prompts/` 目录加载所有当前版本模板
   - **And** 每个模板通过 `PromptRegistry.get(name)` 获取，支持版本参数 `PromptRegistry.get(name, version)`
   - **And** Service 引用 Prompt 模板时通过 PromptRegistry，不直接硬编码文件路径
   - **And** 加载失败时抛出明确错误（PromptLoadError），不静默降级

3. **AC-3: 变更检测触发机制**
   - **Given** 开发者修改了 `prompts/` 目录中的 .md 文件
   - **When** 变更被提交（git commit）或手动触发
   - **Then** 自动运行 `tests/regression/` 目录下对应的回归测试
   - **And** 映射规则：`prompts/autoscore_*.md` 变更 -> 跑 `test_autoscore_regression.py`
   - **And** 映射规则：`prompts/question_gen_*.md` 变更 -> 跑 `test_question_gen_regression.py`
   - **And** 映射规则：`prompts/context_extract_*.md` 变更 -> 跑 `test_context_extract_regression.py`
   - **And** 可通过 `pytest tests/regression/ -k <prompt_name>` 手动触发单模板回归测试

4. **AC-4: 标准测试集与基线管理**
   - **Given** 每个 Prompt 模板有对应的回归测试
   - **When** 回归测试执行
   - **Then** 使用 `tests/fixtures/regression_baselines/` 中的标准测试集（固定输入-预期输出对）
   - **And** AutoSCORE 回归：5+ 个评分场景（含边界：满分/零分/争议分），验证评分一致性
   - **And** 出题回归：5+ 个出题场景（不同考察模式/白板类型），验证题目质量指标
   - **And** 提取回归：5+ 个提取场景（错误/Tips/关键问答），验证提取准确性
   - **And** 测试集场景覆盖中英文混合内容

5. **AC-5: 质量指标对比与报告**
   - **Given** 回归测试执行完成
   - **When** 测试结果生成
   - **Then** 输出结构化报告：变更前基线指标 vs 变更后指标
   - **And** 评分回归报告包含：评分一致性率（>= 80%）、平均分差（<= 0.5 分）
   - **And** 出题回归报告包含：题目格式合规率（>= 90%）、难度匹配率（>= 70%）
   - **And** 提取回归报告包含：提取召回率（>= 85%）、分类准确率（>= 80%）
   - **And** 指标显著下降时测试标记为 FAIL 并输出详细 diff
   - **And** 测试结果对比变更前后的质量指标（MRR、Precision、CRAG 触发率）

6. **AC-6: Prompt 版本回滚支持**
   - **Given** 回归测试发现新版本 Prompt 质量下降
   - **When** 开发者决定回滚
   - **Then** 通过 PromptRegistry 切换回旧版本（`set_active_version` 或修改 service 引用的版本号）
   - **And** 旧版本文件始终保留在 `prompts/` 目录中
   - **And** 回滚操作记录到 `CHANGELOG.md`

## Tasks / Subtasks

### Task 1: 迁移检索管道内联 Prompt 到版本化模板 (AC: #1, #2)

现有检索管道中有多处内联 prompt（硬编码在 Python 代码中），需要外部化到 `prompts/` 目录并纳入 PromptRegistry 管理。

- [ ] 1.1 外部化 `src/agentic_rag/mastery_injection.py` 中的查询改写 prompt（`multi_query_rewrite` 函数中的 medium/complex 两个 f-string prompt）为 `prompts/query_rewrite_v1.md`
- [ ] 1.2 外部化 `src/agentic_rag/agent_graph.py` 中的搜索意图分析 prompt（L101 `system_prompt="你是一个搜索意图分析器..."` ）为 `prompts/search_intent_v1.md`
- [ ] 1.3 外部化 `src/agentic_rag/agent_graph.py` 中的文档相关性 CRAG 评分 prompt（L265-280 `grading_prompt` + L279 `system_prompt="你是一个文档相关性评估器..."` ）为 `prompts/crag_grading_v1.md`
- [ ] 1.4 外部化 `src/agentic_rag/agent_graph.py` 中的查询优化 prompt（L362 `system_prompt="你是一个搜索查询优化器..."` ）为 `prompts/query_optimize_v1.md`
- [ ] 1.5 更新各 service 引用：从硬编码字符串改为通过 `PromptRegistry.get(name)` 加载
- [ ] 1.6 为每个新模板添加文件头元数据（引用方、版本、创建日期、变更说明）
- [ ] 1.7 更新 `prompts/CHANGELOG.md` 记录新增模板

### Task 2: 修复现有 Service 的 PromptRegistry 集成 (AC: #2)

当前 `autoscore.py` 仍直接通过文件路径加载 prompt（`_load_prompt` 方法），未使用 PromptRegistry。

- [ ] 2.1 重构 `backend/app/services/autoscore.py`：删除 `_load_prompt` 方法，改为通过 `PromptRegistry.get("autoscore")` 加载
- [ ] 2.2 确认 `exam_service_ext.py` 中 `prompts/exam/` 子目录模板的加载方式是否需纳入 PromptRegistry（exam 子目录模板不使用 `{name}_v{N}.md` 命名规范，可选性纳入或保持现状）
- [ ] 2.3 确认 `.claude/agents/*.md` 的 agent prompt 模板（通过 `GeminiClient.load_prompt_template` 加载）保持独立管理，不纳入本 Story 范围

### Task 3: 检索管道 Prompt 回归测试集设计 (AC: #4)

为新外部化的检索管道 prompt 创建回归测试基线数据。

- [ ] 3.1 创建 `tests/fixtures/regression_baselines/query_rewrite/` 目录，5+ 场景 JSON（输入=原始查询+复杂度等级，期望=改写后查询数量+格式合规）
- [ ] 3.2 创建 `tests/fixtures/regression_baselines/crag_grading/` 目录，5+ 场景 JSON（输入=查询+文档列表，期望=相关性判定分布+触发率范围）
- [ ] 3.3 创建 `tests/fixtures/regression_baselines/search_intent/` 目录，5+ 场景 JSON（输入=用户查询，期望=意图分析 JSON 格式合规）
- [ ] 3.4 每个测试集包含中英文混合场景
- [ ] 3.5 更新 `baseline_metadata.json` 添加新模板的基线 hash 和测试日期

### Task 4: 检索管道 Prompt 回归测试实现 (AC: #3, #4, #5)

- [ ] 4.1 创建 `backend/tests/regression/test_query_rewrite_regression.py` — 查询改写质量回归（格式合规率 >= 90%、改写多样性）
- [ ] 4.2 创建 `backend/tests/regression/test_crag_grading_regression.py` — CRAG 判定回归（触发率 15-30%、分类一致性 >= 80%）
- [ ] 4.3 创建 `backend/tests/regression/test_search_intent_regression.py` — 意图分析回归（JSON 格式合规率、意图分类准确率）
- [ ] 4.4 在 `conftest.py` 中注册新的 baseline loader fixtures（`query_rewrite_baselines`、`crag_grading_baselines`、`search_intent_baselines`）
- [ ] 4.5 在 `report_generator.py` 的 `QUALITY_THRESHOLDS` 中添加新模板的质量阈值配置

### Task 5: 端到端检索质量指标集成 (AC: #5)

Story 2.13 特别要求回归测试对比 MRR、Precision、CRAG 触发率等检索管道端到端指标。

- [ ] 5.1 在 `--live` 模式下，查询改写回归测试集成 MRR@10 对比（变更前后 MRR 差值 <= -0.05）
- [ ] 5.2 在 `--live` 模式下，CRAG 回归测试验证健康触发率范围（15-30%）
- [ ] 5.3 在 `--live` 模式下，集成 Precision@5 对比（变更前后 Precision 差值 <= -0.05）
- [ ] 5.4 报告生成器扩展：输出检索管道端到端指标对比表

### Task 6: 变更检测与触发机制完善 (AC: #3)

- [ ] 6.1 扩展 `PROMPT_TEST_MAP` 映射配置，添加新模板到回归测试的映射
- [ ] 6.2 更新 `scripts/run_prompt_regression.py`（如已存在）或创建该脚本，支持新增模板的回归触发
- [ ] 6.3 配置 lefthook / pre-commit hook：检测 `prompts/` 目录变更时提示运行回归测试
- [ ] 6.4 支持 `pytest tests/regression/ --prompt=query_rewrite` 单模板回归测试

### Task 7: 单元测试补充 (AC: #1-#6)

- [ ] 7.1 单元测试：PromptRegistry 正确加载新增的检索管道模板（query_rewrite、crag_grading、search_intent、query_optimize）
- [ ] 7.2 单元测试：Service 层通过 PromptRegistry 获取模板后变量替换正确
- [ ] 7.3 单元测试：`set_active_version` / `clear_active_version` 回滚机制
- [ ] 7.4 单元测试：新模板的文件头元数据解析

## Dev Notes

### 与 Story 7.3 的关系

本 Story（2.13）在 Epic 2（智能检索管道）上下文中定义，侧重检索相关 prompt（查询改写、CRAG 判定等）的版本管理。Story 7.3 已实现了 Prompt 版本管理基础设施：

**Story 7.3 已完成的资产（可直接复用）：**
- `backend/app/services/prompt_registry.py` — PromptRegistry 单例，load_all/get/list_versions/set_active_version 全部实现
- `backend/app/core/exceptions.py` — PromptLoadError 异常类
- `backend/app/main.py` — FastAPI startup 中 PromptRegistry 初始化（L127-134）
- `backend/app/prompts/autoscore_v1.md` — AutoSCORE 两阶段评分 prompt（95 行，含 SOLO 锚定 4 维评分）
- `backend/app/prompts/question_gen_v1.md` — 出题 5 层结构 prompt（74 行，含 Bloom's Taxonomy + 错误类型映射）
- `backend/app/prompts/context_extract_v1.md` — 对话结构化提取 prompt（90 行，含 4 类错误 + Tips + 关键问答）
- `backend/app/prompts/CHANGELOG.md` — 版本变更记录
- `backend/tests/regression/conftest.py` — 共享 fixtures（PromptRegistry、BaselineLoader、RegressionMetricsCollector、双模式 --live/replay）
- `backend/tests/regression/test_autoscore_regression.py` — AutoSCORE 评分回归（评分一致性 >= 80%、平均分差 <= 0.5）
- `backend/tests/regression/test_question_gen_regression.py` — 出题回归（格式合规率 >= 90%、难度匹配率 >= 70%）
- `backend/tests/regression/test_context_extract_regression.py` — 提取回归（提取召回率 >= 85%、分类准确率 >= 80%）
- `backend/tests/regression/report_generator.py` — RegressionReportGenerator + RegressionReport + QUALITY_THRESHOLDS + 终端表格输出 + JSON 保存
- `backend/tests/fixtures/regression_baselines/` — 完整基线数据集（autoscore 5 场景 + question_gen 5 场景 + context_extract 5 场景 + baseline_metadata.json）

**本 Story 需要新增的工作（7.3 未覆盖）：**
1. 检索管道内联 prompt 外部化（query_rewrite、crag_grading、search_intent、query_optimize 四个模板）
2. 修复 `autoscore.py` 仍直接通过文件路径加载 prompt 的问题（应改用 PromptRegistry）
3. 检索管道 prompt 的回归测试集和回归测试实现
4. 端到端检索质量指标（MRR、Precision、CRAG 触发率）集成到回归报告

### 现有 Prompt 模板清单

| 位置 | 文件 | 版本管理 | 引用方 |
|------|------|---------|--------|
| `backend/app/prompts/autoscore_v1.md` | AutoSCORE 两阶段评分 | PromptRegistry 管理（但 autoscore.py 未使用 Registry） | `services/autoscore.py` |
| `backend/app/prompts/question_gen_v1.md` | 出题 5 层结构 | PromptRegistry 管理 | `services/question_generator.py` |
| `backend/app/prompts/context_extract_v1.md` | 对话结构化提取 | PromptRegistry 管理 | `services/conversation_archive.py` |
| `backend/app/prompts/scoring/stage1_evidence.md` | AutoSCORE Stage 1 | 文件直接加载（未纳入 PromptRegistry） | `services/autoscore.py` |
| `backend/app/prompts/scoring/stage2_rubric.md` | AutoSCORE Stage 2 | 文件直接加载（未纳入 PromptRegistry） | `services/autoscore.py` |
| `backend/app/prompts/exam/layer1_role.md` | 考察角色定义 | 文件直接加载 | `services/exam_service_ext.py` |
| `backend/app/prompts/exam/layer2_mode.md` | 考察模式 | 文件直接加载 | `services/exam_service_ext.py` |
| `backend/app/prompts/exam/layer4_rules.md` | 出题规则 | 文件直接加载 | `services/exam_service_ext.py` |
| `backend/app/prompts/exam/layer5_scoring_preset.md` | 评分预设 | 文件直接加载 | `services/exam_service_ext.py` |
| `backend/app/prompts/exam/hint_level{1-4}.md` | 4 级提示 | 文件直接加载 | `services/exam_service_ext.py` |
| `.claude/agents/*.md` (17 files) | Agent 系统 prompt 模板 | `GeminiClient.load_prompt_template` 独立管理 | `services/agent_service.py` |

### 需要外部化的内联 Prompt（检索管道）

| 当前位置 | 内联 prompt 描述 | 目标文件 |
|---------|-----------------|---------|
| `src/agentic_rag/mastery_injection.py:246-248` | 查询改写 prompt（medium: "请从不同角度改写..." / complex: "请将以下复杂查询拆分..."） | `prompts/query_rewrite_v1.md` |
| `src/agentic_rag/agent_graph.py:101` | 搜索意图分析 system_prompt（"你是一个搜索意图分析器"） | `prompts/search_intent_v1.md` |
| `src/agentic_rag/agent_graph.py:265-280` | CRAG 文档相关性评分 grading_prompt + system_prompt（"你是一个文档相关性评估器"） | `prompts/crag_grading_v1.md` |
| `src/agentic_rag/agent_graph.py:362` | 查询优化 system_prompt（"你是一个搜索查询优化器"） | `prompts/query_optimize_v1.md` |

### autoscore.py 直接文件加载问题

`backend/app/services/autoscore.py` 在 `__init__` 中通过 `_load_prompt("autoscore_v1.md")` 直接从文件系统加载 prompt，绕过了 PromptRegistry。需重构为：
```python
# Before (current):
self._stage1_prompt = self._load_prompt("autoscore_v1.md", section="stage1")
# After (should be):
registry = get_prompt_registry()
self._stage1_prompt = registry.get("autoscore")
```

### 架构约束

- **PromptRegistry 文件命名规范**: 仅扫描 `{name}_v{N}.md` 格式的文件。`prompts/exam/` 和 `prompts/scoring/` 子目录的模板不使用此命名规范，暂不纳入 PromptRegistry 管理
- **LiteLLM 统一调用**: 回归测试中所有 LLM 调用通过 LiteLLM SDK
- **双模式测试**: replay 模式（CI 快速）+ `--live` 模式（真实 LLM 调用）
- **NFR-MAINT-02 对齐**: 直接满足 "Prompt 变更后自动运行标准测试集" 非功能需求
- **检索管道端到端指标**: `--live` 模式下集成 MRR@10、Precision@5、CRAG 触发率对比

### Key Libraries

- `pytest` — 测试框架 + `--live` / `--prompt` 自定义参数
- `hashlib` — SHA-256 content hash 变更检测
- `litellm` — 统一 LLM 调用（`--live` 模式）
- `pathlib` — 文件路径管理
- `json` — 基线场景数据和报告输出

### File Paths

**已存在（Story 7.3 资产）：**
- `backend/app/services/prompt_registry.py` — PromptRegistry 完整实现
- `backend/app/core/exceptions.py` — PromptLoadError
- `backend/app/prompts/autoscore_v1.md`
- `backend/app/prompts/question_gen_v1.md`
- `backend/app/prompts/context_extract_v1.md`
- `backend/app/prompts/CHANGELOG.md`
- `backend/tests/regression/conftest.py`
- `backend/tests/regression/test_autoscore_regression.py`
- `backend/tests/regression/test_question_gen_regression.py`
- `backend/tests/regression/test_context_extract_regression.py`
- `backend/tests/regression/report_generator.py`
- `backend/tests/fixtures/regression_baselines/` (15 scenario JSONs + metadata)

**需要新增：**
- `backend/app/prompts/query_rewrite_v1.md` — 查询改写 prompt 模板
- `backend/app/prompts/search_intent_v1.md` — 搜索意图分析 prompt 模板
- `backend/app/prompts/crag_grading_v1.md` — CRAG 文档相关性评分 prompt 模板
- `backend/app/prompts/query_optimize_v1.md` — 查询优化 prompt 模板
- `backend/tests/regression/test_query_rewrite_regression.py`
- `backend/tests/regression/test_crag_grading_regression.py`
- `backend/tests/regression/test_search_intent_regression.py`
- `backend/tests/fixtures/regression_baselines/query_rewrite/` (5+ scenario JSONs)
- `backend/tests/fixtures/regression_baselines/crag_grading/` (5+ scenario JSONs)
- `backend/tests/fixtures/regression_baselines/search_intent/` (5+ scenario JSONs)

**需要修改：**
- `backend/app/services/autoscore.py` — 重构为通过 PromptRegistry 加载
- `src/agentic_rag/mastery_injection.py` — 外部化内联 prompt
- `src/agentic_rag/agent_graph.py` — 外部化内联 prompt（3 处）
- `backend/tests/regression/conftest.py` — 添加新 baseline loader fixtures
- `backend/tests/regression/report_generator.py` — 添加新模板的 QUALITY_THRESHOLDS
- `backend/tests/fixtures/regression_baselines/baseline_metadata.json` — 添加新模板元数据

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.13 — AC 原始定义]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2 — 智能检索管道上下文]
- [Source: _bmad-output/planning-artifacts/architecture.md#能力域9 — FR-QA-02: Prompt 模板版本管理+回归测试]
- [Source: _bmad-output/planning-artifacts/architecture.md#可维护性 — NFR-MAINT-02: Prompt 回归测试]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure — prompts/ 目录、tests/regression/ 目录]
- [Source: _bmad-output/planning-artifacts/architecture.md#Prompt 文件规范 — 文件头元数据格式]
- [Source: _bmad-output/planning-artifacts/architecture.md#Testing Mapping — prompts/*.md 变更触发 tests/regression/]
- [Source: _bmad-output/implementation-artifacts/7-3-prompt-version-regression-test.md — 前置 Story 7.3 完整实现规范]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
