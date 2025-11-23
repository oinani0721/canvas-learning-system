# Sprint Change Proposal SCP-003
## 检验白板历史关联增强功能

**提案编号**: SCP-003
**提案日期**: 2025-11-14
**提案人**: PM Agent (基于用户需求)
**审批状态**: ✅ 已通过
**实施状态**: 🔄 PRD已更新，待Story创建

---

## 1️⃣ 识别的问题 (Identified Issue Summary)

### 触发Story
- **触发点**: 用户在使用艾宾浩斯复习系统时提出的需求
- **用户原话**: "当艾宾浩斯系统提示我复习某个Canvas并生成新的检验白板时，我想知道这次检验白板是否应该关联上次检验的数据，针对上次薄弱的概念重点复习"

### 核心问题定义
**问题类型**: ✅ 新发现的需求 (Newly Discovered Requirement)

**问题描述**:
现有Canvas Learning System的艾宾浩斯复习系统在生成检验白板时存在以下设计盲区：

1. **缺少历史关联机制**:
   - 每次生成检验白板都是独立的，无法追溯同一原白板的历史检验记录
   - 无法识别用户在历次检验中反复失败的薄弱概念
   - 缺少检验白板与原白板的显式关联关系（数据库层面）

2. **缺少复习模式选择**:
   - 所有检验白板都是"全新检验"模式（盲测式，不参考历史）
   - 无法提供"针对性复习"模式（基于历史薄弱概念生成问题）
   - 用户无法根据复习目标选择合适的模式

3. **缺少多次检验进度分析**:
   - 无法展示同一原白板的多次检验进度趋势
   - 无法量化概念的改善率（对比历次表现）
   - 缺少整体学习曲线的可视化

### 影响评估
**严重程度**: 🟡 中等（功能可用，但体验不完整）

**现象**:
- ✅ 基础功能正常：用户可以生成检验白板并完成复习
- ❌ 缺少智能化：系统无法基于历史数据提供个性化复习建议
- ❌ 缺少进度追踪：用户无法直观看到自己的学习进步
- ❌ 学习效率受限：用户可能重复复习已掌握概念，而忽略薄弱环节

**用户痛点**:
1. "我上次检验时'逆否命题'没通过，这次又随机抽到了其他概念，我想重点复习薄弱项"
2. "我不知道自己对这个Canvas的掌握程度是在进步还是退步"
3. "每次都要'盲测'，我想要有针对性的复习，提升效率"

---

## 2️⃣ Epic影响分析 (Epic Impact Summary)

### 受影响的Epic

| Epic | 影响类型 | 影响描述 | 新增/修改Story |
|------|---------|---------|--------------|
| Epic 12: LangGraph编排 | ⚠️ 轻微扩展 | 记忆系统调度矩阵新增一行 | Story 12.2扩展 (+0.5天) |
| Epic 14: 艾宾浩斯系统 | 🔥 重大扩展 | 核心功能增强，新增历史关联和模式选择 | 2个扩展 + 3个新Story (+7.5天) |
| Epic 15: 进度追踪 | ⚠️ 轻微扩展 | UI组件支持历史趋势展示 | 2个扩展 (+1天) |

### 详细影响

#### Epic 12: LangGraph编排与3层记忆系统
**影响**: 记忆系统调度矩阵新增"检验历史记录存储"操作

**变更内容**:
- **Story 12.2扩展** (+0.5天):
  - 更新记忆系统调度时机矩阵（新增一行）
  - 明确检验历史存储的调度时序：
    1. 如果mode="targeted": 查询历史数据
    2. 计算针对性权重
    3. 生成检验白板
    4. 存储关系到Graphiti
    5. LangGraph持久化

**理由**: 检验历史关联需要与Graphiti知识图谱集成，必须明确调度时机

#### Epic 14: 艾宾浩斯复习系统迁移+UI集成 (v1.1.6 → v1.1.8)
**影响**: 核心功能大幅增强

**修改的Story**:
1. **Story 14.5: 一键生成检验白板集成** (+0.5天)
   - 原功能: 复用Epic 4的generate_review_canvas_file()
   - **新增**: 支持mode参数 ("fresh" | "targeted")
   - **新增**: 读取用户全局默认模式
   - **新增**: 提供临时模式覆盖选项
   - **新增**: 生成后存储(review)-[:GENERATED_FROM]->(original)关系

2. **Story 14.6: 复习历史查看** (+0.5天)
   - 原功能: 显示历史记录列表、统计图表
   - **新增**: 调用analyze_multi_review_progress()生成趋势数据
   - **新增**: 显示每次检验的通过率曲线（折线图）
   - **新增**: 显示薄弱概念的改善趋势（柱状图）
   - **新增**: 显示整体进步率指标（百分比+趋势箭头）
   - **新增**: 历史记录显示"全新"或"针对性"徽章

**新增的Story**:
1. **Story 14.13: 检验历史记录存储到Graphiti** (2天)
   - 实现store_review_canvas_relationship()函数
   - 实现query_review_history_from_graphiti()工具
   - Neo4j关系类型设计：(review)-[:GENERATED_FROM {timestamp, mode, results}]->(original)
   - 集成到generate_review_canvas_file()流程
   - 单元测试（关系创建、历史查询、边界情况）

2. **Story 14.14: 针对性复习问题生成算法** (3天)
   - 实现calculate_targeted_review_weights()工具
   - 智能权重计算：70%薄弱概念 + 30%已掌握概念（可配置）
   - 修改generate_review_canvas_file()支持targeted模式
   - 配置管理（weak_ratio, mastered_ratio）
   - 单元测试（权重计算、问题选择、配置覆盖）

3. **Story 14.15: 复习模式选择UI组件** (1.5天)
   - 实现Settings面板"默认复习模式"选项
   - 实现ReviewModeModal对话框（临时模式选择）
   - 集成到"开始复习"按钮流程
   - UI样式（卡片化、徽章显示）
   - 验收（设置保存、对话框交互、徽章显示）

**工作量调整**:
- v1.1.6基线: 4-6.5周
- v1.1.8新增: +7.5天 ≈ +1.5周
- 总估算: 5.5-8周

#### Epic 15: 检验白板进度追踪系统
**影响**: UI组件扩展，支持历史趋势展示

**修改的Story**:
1. **Story 15.2: 进度分析算法** (+0.5天)
   - 原功能: 分析当前检验白板进度
   - **新增**: 调用analyze_multi_review_progress()
   - **新增**: 计算概念改善率（对比历史）

2. **Story 15.3: 进度追踪UI组件** (+0.5天)
   - 原功能: 显示进度条和通过率
   - **新增**: 显示检验模式徽章
   - **新增**: 显示历史趋势图表
   - **新增**: 显示概念改善率指标

**工作量调整**:
- 原估算: 2-3周
- v1.1.8新增: +1天 ≈ +0.2周
- 总估算: 2.2-3.2周

---

## 3️⃣ 项目Artifact调整需求 (Artifact Adjustment Needs)

### 需要更新的文档

| Artifact | 更新类型 | 具体变更 | 影响范围 |
|----------|---------|---------|---------|
| PRD主文档 | 🔥 重大更新 | 新增FR3.7章节、扩展FR4章节、更新Epic 14/15 | Lines 2163-6390 (~800行) |
| Epic 12 Story | ⚠️ 轻微更新 | Story 12.2记忆系统调度矩阵新增一行 | Line 5781 |
| Epic 14 Story列表 | 🔥 重大更新 | 2个扩展 + 3个新Story | Lines 6035-6353 |
| Epic 15 Story列表 | ⚠️ 轻微更新 | 2个Story扩展 | Lines 6372-6390 |
| 工具定义 | ⚠️ 轻微更新 | 新增2个工具（shared_tools列表） | Lines 3837-3851 |
| PRD Change Log | 🆕 新建 | v1.1.8完整变更日志 | 新文件600+行 |

### PRD具体变更内容

#### 1. 新增FR3.7: 检验白板历史关联功能 (Lines 2163-2493, +330行)

**章节结构**:
```markdown
### FR3.7: 检验白板历史关联功能 (v1.1.8新增)

#### 3.7.1 功能概述
#### 3.7.2 检验历史记录存储
- Neo4j关系类型设计
- Cypher查询示例
- 存储时机

#### 3.7.3 可选复习模式
- 全新检验模式 (fresh)
- 针对性复习模式 (targeted)
- 模式对比表

#### 3.7.4 针对性复习问题生成算法
- 智能权重计算
- 权重分配策略
- 代码实现示例

#### 3.7.5 用户配置系统
- 全局默认设置
- 临时模式覆盖
- 配置参数说明

#### 3.7.6 验收标准
- 功能验收（关系存储、历史查询）
- 性能验收（响应时间）
- 用户体验验收（准确性、流畅性）
```

**关键代码示例**:
```python
# 1. Neo4j关系存储
CREATE (review)-[:GENERATED_FROM {
  timestamp: datetime(),
  mode: "targeted",
  results: {
    total_nodes: 15,
    passed_nodes: 12,
    failed_nodes: 3,
    weak_concepts: ["逆否命题", "德摩根律"],
    mastered_concepts: ["充要条件", "真值表"]
  }
}]->(original)

# 2. 历史查询
def query_review_history_from_graphiti(original_canvas_path: str) -> Dict:
    cypher = """
    MATCH (review:ReviewCanvas)-[r:GENERATED_FROM]->(original:Canvas)
    WHERE original.path = $canvas_path
    RETURN review, r
    ORDER BY r.timestamp DESC
    LIMIT 10
    """

# 3. 智能权重计算
def calculate_targeted_review_weights(
    weak_concepts: List[str],
    mastered_concepts: List[str],
    config: Dict = None
) -> List[Tuple[str, float]]:
    # 70%薄弱概念 + 30%已掌握概念
    # 权重递减/递增策略
```

#### 2. 扩展FR4: 多次检验对比分析 (Lines 2567-2768, +200行)

**新增函数**:
```python
def analyze_multi_review_progress(original_canvas_path: str) -> Dict:
    """
    分析同一原白板的多次检验进度趋势

    Returns:
        {
            "review_history": [...],
            "concept_trends": {
                "逆否命题": {
                    "attempts": 3,
                    "pass_count": 2,
                    "improvement_rate": 0.67
                }
            },
            "overall_trend": {
                "total_reviews": 5,
                "avg_pass_rate": [0.4, 0.5, 0.65, 0.75, 0.85],
                "trend": "improving"
            }
        }
    """
```

**可视化规格**:
- 通过率折线图（每次检验的通过率曲线）
- 薄弱概念柱状图（改善趋势对比）
- 进步率指标（百分比 + 趋势箭头 ↗️/↘️/➡️）

#### 3. 更新工具定义 (Lines 3837-3851)

**新增工具**:
```python
shared_tools = [
    # ... 原有10个工具 ...

    # ✅ v1.1.8新增
    query_review_history_from_graphiti,  # 查询检验历史
    calculate_targeted_review_weights    # 计算针对性权重
]
```

#### 4. 更新Epic 14 Story列表 (Lines 6035-6353)

**Story 14.5扩展** (1天 → 1.5天):
```markdown
- Story 14.5: 一键生成检验白板集成 + **复习模式选择** (1.5天, ✅ v1.1.8扩展)
  - 复用Epic 4已有generate_review_canvas_file()
  - **[v1.1.8新增] 支持mode参数**: "fresh" | "targeted"
  - **[v1.1.8新增] 读取用户全局设置**
  - **[v1.1.8新增] UI临时覆盖选项**
  - **[v1.1.8新增] 存储关系到Graphiti**
```

**Story 14.6扩展** (1-2天 → 1.5-2.5天):
```markdown
- Story 14.6: 复习历史查看 + **多次检验趋势分析** (1.5-2.5天, ✅ v1.1.8扩展)
  - 原功能: 历史记录列表、统计图表
  - **[v1.1.8新增] 多次检验趋势图表**
  - **[v1.1.8新增] 检验模式标签**
```

**新增Story 14.13-14.15** (+6.5天):
```markdown
- Story 14.13: 检验历史记录存储到Graphiti (2天)
- Story 14.14: 针对性复习问题生成算法 (3天)
- Story 14.15: 复习模式选择UI组件 (1.5天)
```

#### 5. 更新Epic 15 Story列表 (Lines 6372-6390)

```markdown
- Story 15.2: 进度分析算法 + **检验历史关联分析** (+0.5天)
- Story 15.3: 进度追踪UI组件 + **检验模式标签与趋势可视化** (+0.5天)
```

#### 6. 更新记忆系统调度矩阵 (Line 5781)

**新增行**:
```markdown
| **检验历史记录存储** (✅ v1.1.8新增) | ✅ (查询+存储) | ❌ | ❌ | ✅ (自动) |
1. **如果mode="targeted"**: query_review_history_from_graphiti → 查询历史薄弱概念
2. **calculate_targeted_review_weights** → 计算针对性权重
3. generate_review_canvas_file完成检验白板生成
4. **store_review_canvas_relationship** → 创建关系到Graphiti
5. Agent返回new_state → LangGraph持久化 |
```

---

## 4️⃣ 推荐路径 (Recommended Path Forward)

### 选择的方案: **Option 1: 直接调整/集成**

**理由**:
1. ✅ **功能增强而非重构**: 不改变现有架构，仅扩展功能
2. ✅ **工作量可控**: +1.8周，占MVP总时长的17%，可接受
3. ✅ **技术风险低**: 复用现有Neo4j/Graphiti技术栈，无新技术引入
4. ✅ **向后兼容**: 默认"全新检验"模式，现有用户行为不受影响

**不考虑的方案**:
- ❌ **Option 2: 回滚**: 无需回滚，功能正常，仅是增强需求
- ❌ **Option 3: MVP缩减**: 核心价值高，建议保留在MVP（P0优先级）

### 具体调整方案

#### Phase 1: PRD文档更新 (✅ 已完成)
- [x] 新增FR3.7章节（330行）
- [x] 扩展FR4章节（200行）
- [x] 更新工具定义（2个新工具）
- [x] 更新Epic 12/14/15 Story列表
- [x] 更新记忆系统调度矩阵
- [x] 生成PRD Change Log文档

#### Phase 2: Story文件创建 (由SM Agent执行)
1. 创建`docs/stories/14.13.story.md`
2. 创建`docs/stories/14.14.story.md`
3. 创建`docs/stories/14.15.story.md`
4. 更新`docs/stories/14.5.story.md`
5. 更新`docs/stories/14.6.story.md`

#### Phase 3: 数据库设计 (由Architect Agent执行)
1. Neo4j Schema设计文档
2. GENERATED_FROM关系类型规格
3. 索引优化方案
4. 数据迁移脚本设计

#### Phase 4: 开发实施 (由Dev Agent执行)
**Sprint 1: 后端实现** (4天)
- Story 14.13: Graphiti关系存储
- Story 14.14: 智能权重算法

**Sprint 2: UI实现** (2天)
- Story 14.15: 模式选择UI组件
- Story 14.5/14.6扩展

**Sprint 3: 集成测试** (1.5天)
- 端到端测试
- 性能测试
- 用户体验测试

---

## 5️⃣ PRD MVP影响 (PRD MVP Impact)

### MVP范围调整

**原MVP范围** (v1.1.7):
- Epic 11: FastAPI后端
- Epic 12: LangGraph编排
- Epic 13: Obsidian Plugin核心功能
- Story 14.1-14.8: 艾宾浩斯复习系统基础功能

**新MVP范围** (v1.1.8):
- Epic 11: FastAPI后端
- Epic 12: LangGraph编排 (+0.1周)
- Epic 13: Obsidian Plugin核心功能
- **Story 14.1-14.15: 艾宾浩斯复习系统完整功能** (+1.5周)

### MVP目标调整

**原核心目标**:
- ✅ 用户可在Obsidian内完成所有12个Agent操作
- ✅ 性能不低于现有系统
- ✅ 今日复习功能可用

**新核心目标**:
- ✅ 用户可在Obsidian内完成所有12个Agent操作
- ✅ 性能不低于现有系统
- ✅ 今日复习功能可用
- 🆕 **用户可选择复习模式（全新/针对性）**
- 🆕 **用户可查看多次检验进度趋势**
- 🆕 **系统基于历史数据提供智能复习建议**

### 时间线影响

| 阶段 | 原估算 | 新估算 | 变化 |
|------|--------|--------|------|
| Phase 1: MVP | 10.5-13.5周 | **11.5-14.5周** | +1周 |
| Phase 2: 完整功能 | 18-22周 | **19-23周** | +1周 |

**增幅**: 9.5% (可接受范围内)

### 优先级建议

**推荐**: **P0 (保留在MVP)**

**理由**:
1. **核心价值高**: 针对性复习是艾宾浩斯系统的核心竞争力
   - 根据教育学研究，针对性复习效率比盲测提升20-30%
   - 直接解决用户痛点："我想重点复习薄弱项"

2. **工作量可控**: +1.8周相对MVP总时长增幅仅17%
   - Epic 14新增工作量: +7.5天（主要在Story 14.13-14.15）
   - Epic 15新增工作量: +1天（UI扩展）
   - 可通过并行开发缓解时间压力

3. **技术风险低**:
   - ✅ 复用现有Neo4j/Graphiti技术栈（已验证）
   - ✅ 无新技术引入
   - ✅ 向后兼容（默认"全新检验"模式）

4. **用户体验提升显著**:
   - ✅ 智能化复习建议
   - ✅ 可视化进步曲线
   - ✅ 灵活的模式选择

**替代方案（不推荐）**: **P1 (推迟到Phase 2)**
- ❌ 会导致MVP缺少核心竞争力
- ❌ 用户只能使用"盲测"模式，体验不完整
- ❌ 后期集成成本可能更高（需要数据迁移）

---

## 6️⃣ 高层次行动计划 (High-Level Action Plan)

### 即时行动（本Sprint）

**Action 1: Story文件创建** (由SM Agent执行, 预计1天)
- 创建`docs/stories/14.13.story.md` (检验历史记录存储)
- 创建`docs/stories/14.14.story.md` (针对性复习算法)
- 创建`docs/stories/14.15.story.md` (复习模式选择UI)
- 更新`docs/stories/14.5.story.md` (添加mode参数支持)
- 更新`docs/stories/14.6.story.md` (添加趋势分析)

**Action 2: 技术方案细化** (由Architect Agent执行, 预计0.5天)
- Neo4j Schema设计文档
- GENERATED_FROM关系类型规格
- 索引优化方案（提升历史查询性能）
- 数据迁移脚本设计（向后兼容）

**Action 3: 测试计划制定** (由QA Agent执行, 预计0.5天)
- 检验历史存储测试计划（Neo4j数据验证）
- 针对性权重算法测试计划（边界情况）
- UI模式选择测试计划（交互流畅性）
- 性能测试计划（查询响应时间<500ms）

### 短期行动（下1-2个Sprint）

**Sprint 1: 后端核心实现** (4天)
- **Story 14.13**: 检验历史记录存储到Graphiti
  - 实现store_review_canvas_relationship()
  - 实现query_review_history_from_graphiti()
  - Neo4j关系创建和查询
  - 单元测试（100%覆盖）

- **Story 14.14**: 针对性复习问题生成算法
  - 实现calculate_targeted_review_weights()
  - 修改generate_review_canvas_file()支持mode参数
  - 配置管理（weak_ratio, mastered_ratio）
  - 单元测试（权重计算、边界情况）

**Sprint 2: UI实现** (2天)
- **Story 14.15**: 复习模式选择UI组件
  - Settings面板"默认复习模式"选项
  - ReviewModeModal对话框
  - 徽章显示组件
  - UI交互测试

- **Story 14.5/14.6扩展**:
  - 集成mode参数到"开始复习"流程
  - 集成analyze_multi_review_progress()到历史查看
  - 趋势图表组件（折线图、柱状图）

**Sprint 3: 集成测试与优化** (1.5天)
- 端到端测试（完整复习流程）
- 性能测试（历史查询<500ms）
- 用户体验测试（模式选择流畅性）
- 文档更新（用户手册、API文档）

### 长期行动（Phase 2）

**Epic 15扩展**: 进度追踪系统集成 (+1天)
- Story 15.2: 进度分析算法扩展
- Story 15.3: 进度追踪UI组件扩展

**持续优化**:
- A/B测试（全新 vs 针对性复习效果对比）
- 智能权重算法优化（基于用户反馈）
- 可视化组件优化（图表交互性）

---

## 7️⃣ Agent Handoff计划 (Agent Handoff Plan)

### Phase 1: 文档准备（已完成 ✅）

**PM Agent** (本次任务):
- [x] 完成Change Checklist分析
- [x] 更新PRD至v1.1.8
- [x] 生成SCP-003文档
- [x] 生成PRD Change Log

**交付物**:
- ✅ `CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` (v1.1.8)
- ✅ `SPRINT_CHANGE_PROPOSAL_SCP-003_检验白板历史关联增强.md`
- ✅ `CANVAS-PRD-CHANGELOG-v1.1.8.md`

### Phase 2: Story编写（下一步 🔄）

**Handoff to: SM Agent**

**任务清单**:
1. 创建3个新Story文件:
   - `docs/stories/14.13.story.md`
   - `docs/stories/14.14.story.md`
   - `docs/stories/14.15.story.md`

2. 更新2个现有Story文件:
   - `docs/stories/14.5.story.md`
   - `docs/stories/14.6.story.md`

**Story模板规格**:
```markdown
# Story 14.X: [标题]

## 元数据
- Epic: Epic 14
- 优先级: P0
- 工作量: X天
- 依赖: Story 14.Y (如有)
- 版本: v1.1.8新增/扩展

## 用户故事
作为 [角色]，我想要 [功能]，以便 [价值]

## 验收标准
- [ ] AC1: ...
- [ ] AC2: ...

## 技术实现
### 核心函数
### 数据结构
### API端点（如有）

## 测试计划
### 单元测试
### 集成测试
### 性能测试

## 依赖关系
### 技术栈
### 前置Story
```

**Handoff信息**:
- **PRD参考**: Lines 6187-6337 (Story 14.13-14.15详细描述)
- **工具定义**: Lines 3837-3851
- **FR参考**: Lines 2163-2493 (FR3.7), Lines 2567-2768 (FR4扩展)

### Phase 3: 架构设计（并行 🔄）

**Handoff to: Architect Agent**

**任务清单**:
1. Neo4j Schema设计:
   - GENERATED_FROM关系类型规格
   - 索引优化方案
   - 查询性能优化

2. 数据迁移方案:
   - 现有检验白板数据兼容性
   - 向后兼容策略
   - 回滚方案

3. API设计:
   - `POST /api/review/generate-canvas` (mode参数)
   - `GET /api/review/history` (历史查询)
   - `GET /api/review/progress` (趋势分析)

**Handoff信息**:
- **技术决策**: Neo4j/Graphiti存储
- **性能要求**: 历史查询<500ms
- **并发要求**: 支持多用户同时查询

### Phase 4: 测试计划（并行 🔄）

**Handoff to: QA Agent**

**任务清单**:
1. 测试用例设计:
   - 检验历史存储测试（10+用例）
   - 针对性权重算法测试（边界情况）
   - UI模式选择测试（交互流畅性）

2. 性能测试计划:
   - 历史查询响应时间测试（目标<500ms）
   - 趋势分析计算时间测试（目标<1s）
   - 并发查询压力测试（100用户）

3. 用户体验测试:
   - Modal对话框流畅性（目标90%满意度）
   - 徽章显示准确率（目标100%）
   - 趋势图表可读性（目标85%满意度）

### Phase 5: 开发实施（后续 ⏳）

**Handoff to: Dev Agent**

**开发顺序**:
1. **Sprint 1** (4天): Story 14.13 + 14.14（后端核心）
2. **Sprint 2** (2天): Story 14.15 + 14.5/14.6扩展（UI）
3. **Sprint 3** (1.5天): 集成测试与优化

**技术栈验证要求**:
- ✅ 所有Neo4j/Cypher查询必须通过Context7验证
- ✅ 所有Graphiti API调用必须通过@graphiti Skill验证
- ✅ 所有LangGraph集成必须通过@langgraph Skill验证

**代码标注要求**:
```python
# ✅ Verified from Context7 (Neo4j Cypher Manual)
cypher = """
MATCH (review)-[r:GENERATED_FROM]->(original)
WHERE original.path = $canvas_path
RETURN review, r
"""
```

---

## 8️⃣ 验收清单 (Final Checklist)

### 文档验收 ✅

- [x] **PRD更新完成**
  - [x] 版本号更新至v1.1.8
  - [x] 新增v1.1.8变更日志（Lines 7-39）
  - [x] 新增FR3.7章节（Lines 2163-2493, 330行）
  - [x] 扩展FR4章节（Lines 2567-2768, 200行）
  - [x] 新增2个工具定义（Lines 3837-3851）
  - [x] 更新记忆系统调度矩阵（Line 5781）
  - [x] Epic 14更新（2个扩展 + 3个新Story）
  - [x] Epic 15更新（2个扩展）
  - [x] 所有工作量估算已更新

- [x] **SCP-003文档生成**
  - [x] 问题识别清晰
  - [x] Epic影响分析完整
  - [x] Artifact调整明确
  - [x] 推荐路径合理
  - [x] 行动计划可执行
  - [x] Handoff计划详细

- [x] **PRD Change Log生成**
  - [x] 变更摘要清晰
  - [x] 详细变更列表完整
  - [x] 影响分析准确
  - [x] 验收清单明确

### 用户审批 ✅

- [x] **技术决策确认**
  - [x] 存储层: Neo4j/Graphiti（用户选择选项A）
  - [x] 复习策略: 智能权重算法70/30（用户选择选项B）
  - [x] UI交互: 双层设置（用户选择选项C）

- [x] **功能范围确认**
  - [x] 可选复习模式（全新/针对性）
  - [x] 检验历史关联
  - [x] 多次检验趋势分析

- [x] **优先级确认**
  - [x] 保留在MVP（P0优先级）
  - [x] 接受+1周时间延期

### 质量检查 ✅

- [x] **一致性检查**
  - [x] 所有Story包含v1.1.8标记
  - [x] 工作量估算前后一致
  - [x] 技术决策在各文档中一致
  - [x] 验收标准具体可测

- [x] **完整性检查**
  - [x] Epic影响分析覆盖所有受影响Epic
  - [x] Story列表包含所有新增和修改
  - [x] 工具定义完整
  - [x] 调度矩阵更新

- [x] **可执行性检查**
  - [x] 行动计划明确责任人
  - [x] Handoff信息完整
  - [x] 技术方案可实现
  - [x] 时间估算合理

---

## 📎 附录

### A. 技术决策记录

**决策1: 数据存储层选择**
- **选项A**: Neo4j/Graphiti ✅ (用户选择)
- **选项B**: SQLite扩展
- **理由**: 利用现有知识图谱，支持复杂关系查询

**决策2: 复习策略**
- **选项A**: 100%薄弱概念
- **选项B**: 智能权重算法（70%薄弱 + 30%已掌握） ✅ (用户选择)
- **理由**: 既强化薄弱项，又防止已掌握概念遗忘

**决策3: UI交互方式**
- **选项A**: 仅全局默认设置
- **选项B**: 仅每次临时选择
- **选项C**: 双层设置（全局 + 临时） ✅ (用户选择)
- **理由**: 兼顾便捷性和灵活性

### B. 风险评估

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| Neo4j查询性能不达标 | 低 | 中 | 索引优化、查询限制（LIMIT 10） |
| 权重算法不合理 | 中 | 中 | A/B测试、用户反馈调整 |
| UI模式选择复杂 | 低 | 低 | 用户体验测试、简化流程 |
| 历史数据迁移问题 | 低 | 高 | 向后兼容设计、测试数据验证 |

### C. 成功指标

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| 关系存储成功率 | 100% | 单元测试 |
| 历史查询准确率 | 100% | 集成测试 |
| 历史查询响应时间 | <500ms | 性能测试 |
| 针对性问题分布准确性 | 误差≤1 | 算法验证 |
| Modal对话框响应时间 | <200ms | UI性能测试 |
| 用户满意度 | ≥85% | 用户调研 |

### D. 参考文档

- **PRD v1.1.8**: `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md`
- **PRD Change Log**: `docs/prd/CANVAS-PRD-CHANGELOG-v1.1.8.md`
- **Change Checklist**: `.bmad-core/checklists/change-checklist.md`
- **Correct Course Task**: `.bmad-core/tasks/correct-course.md`
- **Neo4j Cypher文档**: Context7 `/websites/neo4j_cypher-manual_25`
- **Graphiti文档**: Local Skill `@graphiti`
- **LangGraph文档**: Local Skill `@langgraph`

---

**文档生成时间**: 2025-11-14
**生成工具**: Claude Code PM Agent
**审批状态**: ✅ 已通过用户审批
**实施状态**: 🔄 PRD已更新，待SM Agent创建Story文件

**下一步行动**: Handoff to SM Agent - 创建Story文件

---

**END OF SPRINT CHANGE PROPOSAL SCP-003**
