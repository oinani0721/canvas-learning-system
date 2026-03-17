# Story 7.3: Prompt 版本管理与回归测试

Status: ready-for-dev

## Story

As a 开发者,
I want Prompt 模板有版本管理，变更后自动触发回归测试，
so that Prompt 修改不会意外降低 AI 质量，每次变更的质量影响可追溯。

## Acceptance Criteria

1. **AC-1: Prompt 模板版本化存储**
   - **Given** 后端 `prompts/` 目录存放 LLM 系统 prompt 模板
   - **When** 开发者需要修改 Prompt 模板
   - **Then** 创建新版本文件（如 `autoscore_v2.md`），旧版本保留不删除
   - **And** 每个 Prompt 文件头包含元数据注释（引用方 service、版本号、创建日期、变更说明）
   - **And** `CHANGELOG.md` 记录每次版本变更的原因和影响范围

2. **AC-2: PromptRegistry 统一加载管理**
   - **Given** 后端服务启动
   - **When** PromptRegistry 初始化
   - **Then** 自动扫描 `prompts/` 目录加载所有当前版本模板
   - **And** 每个模板通过 PromptRegistry.get(name) 获取，支持版本参数 PromptRegistry.get(name, version)
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
   - **And** 出题回归报告包含：题目格式合规率、难度匹配率、覆盖维度完整性
   - **And** 提取回归报告包含：提取召回率（>= 85%）、分类准确率（>= 80%）
   - **And** 指标显著下降时测试标记为 FAIL 并输出详细 diff

6. **AC-6: Prompt 版本回滚支持**
   - **Given** 回归测试发现新版本 Prompt 质量下降
   - **When** 开发者决定回滚
   - **Then** 通过 PromptRegistry 切换回旧版本（修改 service 引用的版本号）
   - **And** 旧版本文件始终保留在 `prompts/` 目录中
   - **And** 回滚操作记录到 `CHANGELOG.md`

## Tasks / Subtasks

- [ ] Task 1: Prompt 模板目录结构与版本化规范 (AC: #1)
  - [ ] 1.1 创建 `backend/app/prompts/` 目录（架构规范位置）
  - [ ] 1.2 创建 `autoscore_v1.md` — AutoSCORE 评分 prompt（5 层结构：角色-模式-ACP-规则-评分预设）
  - [ ] 1.3 创建 `question_gen_v1.md` — 出题 prompt（含 Bloom's Taxonomy PS4 策略、错误类型到出题策略映射）
  - [ ] 1.4 创建 `context_extract_v1.md` — 对话提取 prompt（错误/Tips/关键问答结构化提取）
  - [ ] 1.5 创建 `CHANGELOG.md` — 版本变更记录模板
  - [ ] 1.6 定义 Prompt 文件头元数据规范

- [ ] Task 2: PromptRegistry 加载器实现 (AC: #2)
  - [ ] 2.1 创建 `backend/app/services/prompt_registry.py` — Prompt 模板注册与加载
  - [ ] 2.2 实现 `PromptRegistry.load_all()` — 启动时扫描 `prompts/` 目录加载所有 .md 模板
  - [ ] 2.3 实现 `PromptRegistry.get(name, version=None)` — 按名称+版本获取模板内容
  - [ ] 2.4 实现 `PromptRegistry.list_versions(name)` — 列出某模板的所有可用版本
  - [ ] 2.5 实现 Prompt 文件头元数据解析（提取引用方、版本号、创建日期）
  - [ ] 2.6 实现 content_hash 计算（SHA256），用于变更检测
  - [ ] 2.7 实现 PromptLoadError 异常类：文件缺失/格式错误/元数据不完整时明确报错
  - [ ] 2.8 在 FastAPI app startup 中注册 PromptRegistry 初始化

- [ ] Task 3: 变更检测与回归测试触发 (AC: #3)
  - [ ] 3.1 创建 `backend/scripts/run_prompt_regression.py` — 命令行触发器脚本
  - [ ] 3.2 实现 Prompt 文件到回归测试文件的映射配置
  - [ ] 3.3 实现 content_hash 对比检测：对比当前文件与 `regression_baselines/` 中记录的上次测试基线 hash
  - [ ] 3.4 实现 git pre-commit hook 片段（可选）：检测 `prompts/` 变更时提示运行回归测试
  - [ ] 3.5 支持 `pytest tests/regression/ --prompt=autoscore` 单模板回归测试

- [ ] Task 4: 标准测试集设计与基线数据 (AC: #4)
  - [ ] 4.1 创建 `backend/tests/fixtures/regression_baselines/` 目录结构
  - [ ] 4.2 设计 AutoSCORE 回归测试集：5+ 评分场景 JSON（输入=学生回答+评分标准，期望=4 维评分范围）
  - [ ] 4.3 设计出题回归测试集：5+ 出题场景 JSON（输入=节点内容+考察模式+ACP 数据包，期望=题目质量指标）
  - [ ] 4.4 设计提取回归测试集：5+ 提取场景 JSON（输入=对话文本，期望=提取出的错误/Tips/关键问答）
  - [ ] 4.5 每个测试集包含中英文混合场景
  - [ ] 4.6 创建 `baseline_metadata.json` — 记录每个基线的 prompt 版本、hash、测试日期

- [ ] Task 5: 回归测试实现 (AC: #4, #5)
  - [ ] 5.1 创建 `backend/tests/regression/test_autoscore_regression.py` — AutoSCORE 评分回归
  - [ ] 5.2 创建 `backend/tests/regression/test_question_gen_regression.py` — 出题质量回归
  - [ ] 5.3 创建 `backend/tests/regression/test_context_extract_regression.py` — 提取准确性回归
  - [ ] 5.4 创建 `backend/tests/regression/conftest.py` — 共享 fixtures（LLM 录制回放模式 + 基线加载）
  - [ ] 5.5 实现 LLM 调用模式切换：真实 LLM（集成测试）vs 录制回放（CI 快速测试）
  - [ ] 5.6 实现评分一致性指标计算：Krippendorff's alpha 或 Cohen's kappa
  - [ ] 5.7 实现提取召回率/准确率计算

- [ ] Task 6: 质量报告生成 (AC: #5)
  - [ ] 6.1 创建 `backend/tests/regression/report_generator.py` — 结构化报告生成器
  - [ ] 6.2 实现 before/after 指标对比输出（终端表格 + JSON 文件）
  - [ ] 6.3 实现质量阈值门控：指标低于阈值时 pytest 标记 FAIL
  - [ ] 6.4 实现详细 diff 输出：指标下降时展示具体哪些测试用例出现退化

- [ ] Task 7: 版本回滚机制 (AC: #6)
  - [ ] 7.1 在 PromptRegistry 中支持动态切换版本（运行时 + 配置文件）
  - [ ] 7.2 Service 层引用 Prompt 时通过配置指定版本（默认最新）
  - [ ] 7.3 CHANGELOG.md 模板包含回滚记录格式

- [ ] Task 8: 单元测试 (AC: #1-#6)
  - [ ] 8.1 单元测试：PromptRegistry 加载/获取/版本列表
  - [ ] 8.2 单元测试：Prompt 文件头元数据解析
  - [ ] 8.3 单元测试：content_hash 计算与对比
  - [ ] 8.4 单元测试：Prompt 到回归测试映射配置
  - [ ] 8.5 单元测试：报告生成器输出格式

## Dev Notes

### Prompt 版本控制方案

**版本化策略（文件级版本，非 git 依赖）：**

架构文档规定 Prompt 文件位于 `backend/app/prompts/` 目录，每个文件以 `{name}_v{N}.md` 命名。版本管理采用文件级策略（而非纯 git 历史），原因：
- 旧版本文件保留在目录中，便于快速回滚和 A/B 对比
- 开发者无需精通 git 操作即可管理 Prompt 版本
- PromptRegistry 启动时自动发现所有版本，提供 API 查询

**Prompt 文件头规范（架构文档已定义）：**

```markdown
<!-- prompts/autoscore_v1.md -->
<!-- 引用方: services/autoscore.py:AutoScoreService.evaluate() -->
<!-- 版本: v1 | 创建: 2026-03-16 -->
<!-- 变更时: 1.创建新版本文件 2.更新service引用 3.跑tests/regression/ -->
```

**三个核心 Prompt 模板（架构文档指定）：**

| 模板文件 | 引用方 Service | 用途 |
|---------|--------------|------|
| `autoscore_v1.md` | `services/autoscore.py` | AutoSCORE 两阶段评分（证据提取 + 4 维 4 分制 Rubric 逐维打分） |
| `question_gen_v1.md` | `services/question_generator.py` | 出题（5 层结构：角色-模式-ACP-规则-评分预设） |
| `context_extract_v1.md` | `services/conversation_archive.py` | 对话归档时结构化提取（错误/Tips/关键问答） |

### PromptRegistry 设计

```
PromptRegistry（单例）
  load_all()             - 启动时扫描 prompts/ 目录
  get(name, version)     - 获取模板内容（默认最新版本）
  list_versions(name)    - 列出某模板的所有版本
  get_metadata(name, v)  - 获取模板元数据
  get_hash(name, v)      - 获取内容 hash
  _registry              - dict[str, dict[int, PromptTemplate]]
```

**PromptTemplate 数据结构：**

```python
@dataclass
class PromptTemplate:
    name: str           # e.g., "autoscore"
    version: int        # e.g., 1
    content: str        # 模板原始内容
    content_hash: str   # SHA256
    service_ref: str    # 引用方 service 路径
    created_at: str     # 创建日期
    file_path: Path     # 文件绝对路径
```

### 变更检测触发机制

**架构文档已定义映射规则：**

```
改了 prompts/*.md  ->  跑 tests/regression/ 对应
```

**具体实现方式：**

1. **手动触发（主要方式）**：`python scripts/run_prompt_regression.py --prompt autoscore`
2. **pytest 直接运行**：`pytest tests/regression/ -k autoscore`
3. **全量回归**：`pytest tests/regression/`
4. **可选 git hook**：pre-commit 检测 `prompts/` 目录变更时输出提醒（非强制阻断）

**映射配置（run_prompt_regression.py 内）：**

```python
PROMPT_TEST_MAP = {
    "autoscore": "test_autoscore_regression.py",
    "question_gen": "test_question_gen_regression.py",
    "context_extract": "test_context_extract_regression.py",
}
```

### 标准测试集设计

**测试集存储位置：** `backend/tests/fixtures/regression_baselines/`

**目录结构：**

```
regression_baselines/
  baseline_metadata.json              全局基线元数据
  autoscore/
    scenario_01_full_score.json       满分场景
    scenario_02_zero_score.json       零分场景
    scenario_03_partial_mixed.json    部分得分（中英混合）
    scenario_04_edge_dispute.json     争议评分边界
    scenario_05_chinese_only.json     纯中文场景
  question_gen/
    scenario_01_point_to_point.json   点对点突破模式
    scenario_02_comprehensive.json    综合题考察模式
    scenario_03_mixed_mode.json       混合模式
    scenario_04_knowledge_type.json   知识点类型白板
    scenario_05_problem_type.json     题目类型白板
  context_extract/
    scenario_01_error_extract.json    错误提取（4 类）
    scenario_02_tips_extract.json     Tips 提取
    scenario_03_qa_extract.json       关键问答提取
    scenario_04_mixed_chinese.json    中文混合提取
    scenario_05_edge_sparse.json      稀疏内容边界场景
```

**测试场景 JSON 格式（以 AutoSCORE 为例）：**

每个场景文件包含 scenario_id、description、input（student_answer + rubric + context 的完整文本内容）、expected_output（每维评分的合理范围区间 + overall 范围），以及 tags 用于筛选。

### 回归测试执行模式

**双模式支持：**

1. **录制回放模式（CI/快速测试）**：使用预录制的 LLM 响应（存储在 fixtures 中），不实际调用 LLM。用于快速验证 Prompt 模板的格式、结构和变量注入是否正确。

2. **真实 LLM 模式（完整回归）**：通过 LiteLLM 调用真实模型，用于验证 Prompt 变更对实际 AI 输出质量的影响。需要配置 LLM API Key。通过 `--live` 标志切换。

**质量阈值门控：**

| 指标 | 阈值 | 适用模板 |
|------|------|---------|
| 评分一致性率 | >= 80% | autoscore |
| 平均分差 | <= 0.5 | autoscore |
| 题目格式合规率 | >= 90% | question_gen |
| 难度匹配率 | >= 70% | question_gen |
| 提取召回率 | >= 85% | context_extract |
| 分类准确率 | >= 80% | context_extract |

### 架构约束与注意事项

- **LiteLLM 统一调用**：回归测试中所有 LLM 调用通过 LiteLLM SDK，确保模型可配置
- **Prompt 5 层结构对齐**：autoscore 和 question_gen 模板必须遵循 PRD 定义的 5 层结构（角色定义-考察模式-ACP 数据包-出题规则-评分预设）
- **错误类型映射**：question_gen 模板须包含 4 类错误到出题策略映射（破题错误-同结构新题 / 推理谬误-找错+反例 / 知识点缺失-回退定义题 / 似懂非懂-辨析+迁移题）
- **NFR-MAINT-02 对齐**：本 Story 直接满足 "Prompt 变更后自动运行标准测试集" 这一非功能需求
- **与 Story 7.1 的关系**：7.1 的 PromptTemplate 构造器（防注入）和本 Story 的 PromptRegistry 需协调。PromptRegistry 加载模板内容后，通过 7.1 的 PromptTemplate.build() 构造最终 LLM 消息
- **前端 skills/templates/ 不在本 Story 范围**：本 Story 仅管理后端 `prompts/` 目录的 LLM 系统 prompt。前端用户技能 prompt 模板由 Claude Code CLI 原生加载

### Project Structure Notes

**新增文件（按架构目录规范）：**

| 文件 | 目录 | 说明 |
|------|------|------|
| `autoscore_v1.md` | `backend/app/prompts/` | AutoSCORE 评分 prompt 模板 v1 |
| `question_gen_v1.md` | `backend/app/prompts/` | 出题 prompt 模板 v1 |
| `context_extract_v1.md` | `backend/app/prompts/` | 对话提取 prompt 模板 v1 |
| `CHANGELOG.md` | `backend/app/prompts/` | Prompt 版本变更记录 |
| `prompt_registry.py` | `backend/app/services/` | Prompt 模板注册与加载服务 |
| `run_prompt_regression.py` | `backend/scripts/` | 回归测试命令行触发器 |
| `test_autoscore_regression.py` | `backend/tests/regression/` | AutoSCORE 评分回归测试 |
| `test_question_gen_regression.py` | `backend/tests/regression/` | 出题质量回归测试 |
| `test_context_extract_regression.py` | `backend/tests/regression/` | 提取准确性回归测试 |
| `conftest.py` | `backend/tests/regression/` | 回归测试共享 fixtures |
| `report_generator.py` | `backend/tests/regression/` | 质量报告生成器 |
| `baseline_metadata.json` | `backend/tests/fixtures/regression_baselines/` | 基线元数据 |
| `test_prompt_registry.py` | `backend/tests/unit/` | PromptRegistry 单元测试 |

**修改文件：**

| 文件 | 修改内容 |
|------|---------|
| `backend/app/main.py` | 在 app startup 中初始化 PromptRegistry |

**不触及的文件：**

前端组件、IndexedDB schema、MCP 工具定义、前端 skills/templates/ — 本 Story 纯后端 Prompt 管理与测试基础设施。

### References

- [Source: _bmad-output/planning-artifacts/prd.md#能力域9 — FR-QA-02: Prompt 模板版本管理+回归测试]
- [Source: _bmad-output/planning-artifacts/prd.md#可维护性 — NFR-MAINT-02: Prompt 回归测试]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure — prompts/ 目录、tests/regression/ 目录]
- [Source: _bmad-output/planning-artifacts/architecture.md#Prompt 文件规范 — 文件头元数据格式]
- [Source: _bmad-output/planning-artifacts/architecture.md#Prompt 模板划分 — 前后端 Prompt 职责分离]
- [Source: _bmad-output/planning-artifacts/architecture.md#Testing Mapping — prompts/*.md 变更触发 tests/regression/]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Flow — 出题 Prompt 5 层结构]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.3 — AC 原始定义]
- [Source: _bmad-output/planning-artifacts/prd.md#出题 Prompt 5 层结构 — Bloom's Taxonomy PS4 策略]
- [Source: _bmad-output/planning-artifacts/prd.md#错误类型到出题策略映射 — 4 类错误差异化出题]

## Dev Agent Record

### Agent Model Used

(To be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
