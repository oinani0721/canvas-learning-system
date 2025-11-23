---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial PRD with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 0
  fr_count: 0
  nfr_count: 0
---

# Canvas Learning System PRD Change Log - v1.1.8

**文档版本**: v1.1.8 变更日志
**变更日期**: 2025-11-14
**变更类型**: 功能增强 - 检验历史关联与可选复习模式
**变更审批**: SCP-003 (Sprint Change Proposal #003)
**文档状态**: ✅ 已完成

---

## 📋 变更摘要

**核心变更**: 艾宾浩斯复习系统生成检验白板时，支持关联历史检验数据并提供两种复习模式选择。

**变更动机**:
- **问题**: 现有系统每次生成检验白板都是"全新检验"，无法利用历史数据进行针对性复习
- **用户需求**: "我想知道这次检验白板是否应该关联上次检验的数据，针对上次薄弱的概念重点复习"
- **解决方案**:
  1. 将检验历史存储到Neo4j/Graphiti（关系: `(review)-[:GENERATED_FROM]->(original)`）
  2. 提供两种模式: "全新检验" (盲测) vs "针对性复习" (70%薄弱+30%已掌握)
  3. 实现多次检验趋势分析，可视化进步曲线

**技术决策**:
- **存储层**: Neo4j/Graphiti（利用现有知识图谱，检验白板节点关联到原白板节点）
- **复习策略**: 智能权重算法（70%薄弱概念 + 30%已掌握概念防遗忘，比例可配置）
- **UI交互**: 双层设置（全局默认 + 每次可临时覆盖）

---

## 📊 详细变更列表

### 1. PRD文档头部变更

**位置**: Lines 3-5

**变更内容**:
```markdown
**文档版本**: v1.1.8 (检验白板历史关联增强版)
**创建日期**: 2025-01-15
**最后更新**: 2025-11-14 (**NEW**: 检验白板历史关联与可选复习模式 - 艾宾浩斯系统核心增强)
```

**新增变更日志**: Lines 7-39 (完整v1.1.8变更记录)

---

### 2. 新增功能需求 - FR3.7

**位置**: Lines 2163-2493 (新增330行)

**章节标题**: **FR3.7: 检验白板历史关联功能 (v1.1.8新增)**

**核心功能**:
1. **检验历史记录存储**:
   - Neo4j关系类型: `(review:ReviewCanvas)-[:GENERATED_FROM {timestamp, mode, results}]->(original:Canvas)`
   - 存储数据: 时间戳、复习模式、通过率、薄弱概念、已掌握概念
   - Cypher查询示例（查询最近10次检验记录）

2. **可选复习模式**:
   - **"全新检验" (fresh)**: 不参考历史，盲测式检验真实掌握程度
   - **"针对性复习" (targeted)**: 基于历史薄弱概念生成问题

3. **针对性复习问题生成算法**:
   ```python
   def calculate_targeted_review_weights(
       weak_concepts: List[str],
       mastered_concepts: List[str],
       config: Dict = None
   ) -> List[Tuple[str, float]]:
       """
       70%薄弱概念（权重递减: 1.0, 0.95, 0.90...）
       30%已掌握概念（防遗忘，权重递增: 0.5, 0.55, 0.60...）
       """
   ```

4. **用户配置系统**:
   - 全局默认模式设置 (Settings.default_review_mode)
   - 每次生成时临时覆盖（Modal对话框选择）
   - 权重比例配置 (默认70/30，可调整为80/20或60/40)

**验收标准** (Lines 2456-2493):
- 关系存储成功率 100%
- 历史查询准确率 100%
- 针对性问题分布符合配置比例（误差≤1）
- UI模式选择响应时间 <200ms

---

### 3. 扩展功能需求 - FR4

**位置**: Lines 2567-2768 (新增200行)

**新增功能**: **多次检验对比分析**

**核心函数**:
```python
def analyze_multi_review_progress(original_canvas_path: str) -> Dict:
    """
    分析同一原白板的多次检验进度趋势

    Returns:
        {
            "review_history": [...],  # 历史检验记录列表
            "concept_trends": {       # 每个概念的改善趋势
                "逆否命题": {
                    "attempts": 3,
                    "pass_count": 2,
                    "improvement_rate": 0.67,
                    "last_status": "passed"
                }
            },
            "overall_trend": {        # 整体趋势
                "total_reviews": 5,
                "avg_pass_rate": [0.4, 0.5, 0.65, 0.75, 0.85],
                "trend": "improving",
                "improvement_rate": 0.45
            }
        }
    ```

**可视化组件**:
- 通过率折线图 (每次检验的通过率曲线)
- 薄弱概念改善柱状图 (对比历次表现)
- 整体进步率指标 (百分比 + 趋势箭头 ↗️/↘️/➡️)

---

### 4. 新增工具定义

**位置**: Lines 3837-3851

**新增工具**:
```python
shared_tools = [
    # ... 原有10个工具 ...

    # ✅ v1.1.8新增: 检验历史关联工具
    query_review_history_from_graphiti,  # ✅ 查询检验历史数据
    calculate_targeted_review_weights    # ✅ 计算针对性复习权重
]
```

**工具职责**:
- `query_review_history_from_graphiti(original_canvas_path)`: 查询最近10次检验记录
- `calculate_targeted_review_weights(weak_concepts, mastered_concepts, config)`: 智能权重计算

---

### 5. Epic 12: 记忆系统调度矩阵更新

**位置**: Lines 5775-5783

**新增行**: **检验历史记录存储** (v1.1.8)

| Canvas操作 | Graphiti | Temporal | Semantic | LangGraph Checkpointer | 精确时序 |
|-----------|----------|----------|----------|----------------------|---------|
| **检验历史记录存储** (✅ v1.1.8新增) | ✅ (查询+存储) | ❌ | ❌ | ✅ (自动) | 1. **如果mode="targeted"**: query_review_history_from_graphiti → 查询历史薄弱概念<br>2. **calculate_targeted_review_weights** → 计算针对性权重<br>3. generate_review_canvas_file完成检验白板生成<br>4. **store_review_canvas_relationship** → 创建(review)-[:GENERATED_FROM {mode, results}]->(original)到Graphiti<br>5. Agent返回new_state → LangGraph持久化 |

**工作量影响**: +0.5天 (Story 12.2扩展)

---

### 6. Epic 14: 艾宾浩斯复习系统迁移+UI集成

#### 6.1 Story 14.5扩展

**位置**: Lines 6035-6044

**原估算**: 1天
**新估算**: 1.5天 (+0.5天)

**新增功能**:
- 支持mode参数: "fresh" (全新检验) 或 "targeted" (针对性复习)
- 默认值读取用户全局设置 (Settings.default_review_mode)
- UI提供临时覆盖选项 (Modal对话框)
- 生成时存储关系: 创建(review)-[:GENERATED_FROM]->(original)到Graphiti

#### 6.2 Story 14.6扩展

**位置**: Lines 6046-6055

**原估算**: 1-2天
**新估算**: 1.5-2.5天 (+0.5天)

**新增功能**:
- 同一原白板的多次检验趋势图表
- 调用analyze_multi_review_progress()生成趋势数据
- 显示每次检验的通过率曲线（折线图）
- 显示薄弱概念的改善趋势（柱状图）
- 显示整体进步率（百分比+趋势箭头）
- 历史记录显示"全新检验"或"针对性复习"徽章

#### 6.3 新增Story 14.13

**位置**: Lines 6187-6235

**工作量**: 2天

**目标**: 实现检验历史记录存储到Graphiti

**核心功能**:
```python
def store_review_canvas_relationship(
    review_canvas_path: str,
    original_canvas_path: str,
    mode: str,  # "fresh" | "targeted"
    results: Dict
):
    """将检验白板关系存储到Graphiti"""
    # 创建(review)-[:GENERATED_FROM]->(original)关系
    # 存储时间戳、模式、结果数据
```

**验收标准**:
- 每次生成检验白板都成功存储关系
- query_review_history_from_graphiti()查询准确率100%
- Neo4j数据一致性检查通过

#### 6.4 新增Story 14.14

**位置**: Lines 6237-6292

**工作量**: 3天

**目标**: 实现针对性复习问题生成算法

**核心功能**:
```python
def calculate_targeted_review_weights(
    weak_concepts: List[str],
    mastered_concepts: List[str],
    config: Dict = None
) -> List[Tuple[str, float]]:
    """
    计算针对性复习的概念权重

    默认配置: {"weak_ratio": 0.7, "mastered_ratio": 0.3}
    薄弱概念权重递减: 1.0, 0.95, 0.90, ...
    已掌握概念权重递增: 0.5, 0.55, 0.60, ...
    """
```

**修改generate_review_canvas_file()**:
- 如果mode="targeted": 调用历史查询和权重计算
- 使用权重排序选择检验问题

**配置管理**:
- 添加用户设置: weak_ratio (默认0.7), mastered_ratio (默认0.3)
- 支持动态调整（如0.8/0.2或0.6/0.4）

**验收标准**:
- 针对性复习问题分布符合配置比例（误差≤1）
- 薄弱概念优先级正确（最近失败的排最前）
- 已掌握概念防遗忘机制有效

#### 6.5 新增Story 14.15

**位置**: Lines 6294-6337

**工作量**: 1.5天

**目标**: 实现复习模式选择UI组件

**Settings面板**:
- 新增"默认复习模式"设置项
- Radio Button: [全新检验] / [针对性复习]
- 默认值: "全新检验"（向后兼容）

**Modal对话框（临时覆盖）**:
```typescript
class ReviewModeModal extends Modal {
    onOpen() {
        // 🆕 全新检验选项
        // 🎯 针对性复习选项（70%薄弱+30%已掌握）
    }
}
```

**集成到"开始复习"按钮流程**:
- 点击"开始复习" → 弹出Modal对话框
- 用户选择模式 → 调用FastAPI传入mode参数
- 支持"使用默认模式跳过对话框"选项

**验收标准**:
- Settings默认模式可正确保存和读取
- Modal对话框交互流畅（点击选项立即生成）
- 徽章显示正确（与实际生成模式一致）

#### 6.6 Epic 14工作量调整

**位置**: Lines 6344-6353

**v1.1.6基线**: 4-6.5周
**v1.1.8新增/扩展**:
- Story 14.5扩展: +0.5天
- Story 14.6扩展: +0.5天
- Story 14.13新增: +2天
- Story 14.14新增: +3天
- Story 14.15新增: +1.5天
- **小计**: +7.5天 ≈ **+1.5周**

**总估算 (v1.1.8)**: **5.5-8周** (含检验历史关联增强功能)

---

### 7. Epic 15: 检验白板进度追踪系统

#### 7.1 Story 15.2扩展

**位置**: Lines 6372-6375

**原估算**: 包含在2-3周总估算中
**新估算**: +0.5天

**新增功能**:
- 调用analyze_multi_review_progress()生成多次检验趋势数据
- 计算概念改善率（对比历史检验结果）

#### 7.2 Story 15.3扩展

**位置**: Lines 6376-6380

**原估算**: 包含在2-3周总估算中
**新估算**: +0.5天

**新增功能**:
- 显示检验模式徽章（"全新检验" / "针对性复习"）
- 显示历史检验趋势图表（折线图+柱状图）
- 显示概念改善率指标（百分比+趋势箭头）

#### 7.3 Epic 15工作量调整

**位置**: Lines 6384-6390

**原估算**: 2-3周
**v1.1.8扩展**:
- Story 15.2扩展: +0.5天
- Story 15.3扩展: +0.5天
- **小计**: +1天 ≈ **+0.2周**

**总估算 (v1.1.8)**: **2.2-3.2周** (含检验历史关联增强)

---

## 📈 影响分析

### 工作量影响

| Epic | 原估算 | v1.1.8增量 | 新估算 |
|------|--------|-----------|--------|
| Epic 12 (LangGraph编排) | 6-8周 | +0.5天 (+0.1周) | 6.1-8.1周 |
| Epic 14 (艾宾浩斯系统) | 4-6.5周 | +7.5天 (+1.5周) | 5.5-8周 |
| Epic 15 (进度追踪) | 2-3周 | +1天 (+0.2周) | 2.2-3.2周 |
| **总计** | **12-17.5周** | **+9天 (+1.8周)** | **13.8-19.3周** |

### MVP时间线调整

**原MVP时间线** (v1.1.7): 10.5-13.5周
**新MVP时间线** (v1.1.8): **11.5-14.5周** (+1周，取整)

**Phase 1: MVP** (11.5-14.5周):
- ✅ Epic 11: FastAPI后端
- ✅ Epic 12: LangGraph编排 (+0.1周)
- ✅ Epic 13: Plugin核心功能
- ✅ Story 14.1-14.15: 复习系统完整功能 (+1.5周)

**Phase 2: 完整功能** (18-22周 → 19-23周):
- ✅ Epic 14: 艾宾浩斯复习系统完整功能
- ✅ Epic 15: 进度追踪 (+0.2周)
- ✅ Epic 16: 跨Canvas关联
- ✅ Epic 18: 数据迁移

### 技术栈影响

**新增技术依赖**: 无（复用现有Neo4j/Graphiti技术栈）

**数据库Schema变更**:
```cypher
// 新增关系类型
(review:ReviewCanvas)-[:GENERATED_FROM {
    timestamp: datetime,
    mode: "fresh" | "targeted",
    results: {
        total_nodes: int,
        passed_nodes: int,
        failed_nodes: int,
        weak_concepts: [string],
        mastered_concepts: [string]
    }
}]->(original:Canvas)
```

**API变更**:
- `POST /api/review/generate-canvas`: 新增`mode`参数（默认"fresh"，向后兼容）
- `GET /api/review/history?original_canvas_path=...`: 新增历史查询端点
- `GET /api/review/progress?original_canvas_path=...`: 新增趋势分析端点

---

## 🎯 优先级评估

**推荐优先级**: **P0 (保留在MVP)**

**理由**:
1. **核心价值高**: 针对性复习是艾宾浩斯系统的核心竞争力，显著提升学习效率
2. **工作量可控**: +1.8周相对MVP总时长的增幅为17%，可接受
3. **技术风险低**: 复用现有Neo4j/Graphiti技术栈，无新技术引入
4. **用户体验提升**: 解决"每次都盲测"的痛点，提供智能化复习体验

**影响**:
- ✅ **积极影响**: 提升复习效率20-30%（根据教育学研究，针对性复习效果显著优于盲测）
- ⚠️ **时间影响**: MVP延期1周，但可通过并行开发Story 14.13-14.15缓解
- ✅ **质量影响**: 增强系统智能化程度，符合产品定位

---

## ✅ 验收清单

**PRD文档更新**:
- [x] 版本号更新至v1.1.8
- [x] 新增v1.1.8变更日志（Lines 7-39）
- [x] 新增FR3.7章节（Lines 2163-2493）
- [x] 扩展FR4章节（Lines 2567-2768）
- [x] 新增2个工具定义（Lines 3837-3851）
- [x] 更新记忆系统调度矩阵（Line 5781新增行）
- [x] Epic 14: Story 14.5/14.6扩展 + 3个新Story (14.13-14.15)
- [x] Epic 14工作量调整（Lines 6344-6353）
- [x] Epic 15: Story 15.2/15.3扩展
- [x] Epic 15工作量调整（Lines 6384-6390）

**Sprint Change Proposal**:
- [x] SCP-003已生成（Sprint Change Proposal #003）
- [x] 变更分析已完成
- [x] 用户审批已获得

**文档一致性**:
- [x] 所有Story描述包含v1.1.8标记
- [x] 工作量估算已更新
- [x] 技术决策已记录
- [x] 验收标准已明确

---

## 📝 下一步行动

### 立即行动（由SM Agent执行）

1. **创建Story文件**:
   - `docs/stories/14.13.story.md` (检验历史记录存储到Graphiti)
   - `docs/stories/14.14.story.md` (针对性复习问题生成算法)
   - `docs/stories/14.15.story.md` (复习模式选择UI组件)

2. **更新Story文件**:
   - `docs/stories/14.5.story.md`: 添加mode参数支持
   - `docs/stories/14.6.story.md`: 添加趋势分析功能

3. **创建测试计划**:
   - 检验历史存储测试（Neo4j数据验证）
   - 针对性权重算法测试（边界情况）
   - UI模式选择测试（交互流畅性）

### 后续行动（由Dev Agent执行）

1. **数据库迁移脚本**:
   - 创建Neo4j迁移脚本（新增GENERATED_FROM关系类型）
   - 测试数据生成脚本（模拟历史检验记录）

2. **API实现**:
   - 实现`query_review_history_from_graphiti()`
   - 实现`calculate_targeted_review_weights()`
   - 实现`store_review_canvas_relationship()`
   - 实现`analyze_multi_review_progress()`

3. **UI实现**:
   - 实现Settings面板"默认复习模式"选项
   - 实现ReviewModeModal对话框
   - 实现历史趋势图表组件

### 监控指标（由QA Agent执行）

1. **功能验收**:
   - 关系存储成功率 = 100%
   - 历史查询准确率 = 100%
   - 针对性问题分布误差 ≤ 1

2. **性能验收**:
   - 历史查询响应时间 < 500ms
   - Modal对话框响应时间 < 200ms
   - 趋势分析计算时间 < 1s

3. **用户体验验收**:
   - Modal对话框交互流畅性 ≥ 90%满意度
   - 徽章显示准确率 = 100%
   - 趋势图表可读性 ≥ 85%满意度

---

## 📎 附录

### 变更文件清单

| 文件路径 | 变更类型 | 行数变化 |
|---------|---------|---------|
| `docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md` | 修改 | +800行 |
| `docs/prd/CANVAS-PRD-CHANGELOG-v1.1.8.md` | 新增 | +600行 (本文件) |
| `docs/SPRINT_CHANGE_PROPOSAL_SCP-003_检验白板历史关联增强.md` | 新增 | +400行 |

### 相关引用

- **SCP-003**: Sprint Change Proposal #003 (检验白板历史关联增强)
- **PRD v1.1.7**: 基线版本 (2025-11-13)
- **PRD v1.1.8**: 本次变更版本 (2025-11-14)
- **Change Checklist**: `.bmad-core/checklists/change-checklist.md`
- **Correct Course Task**: `.bmad-core/tasks/correct-course.md`

### 技术文档引用

- **Neo4j Cypher文档**: Context7 `/websites/neo4j_cypher-manual_25` (2,032 snippets)
- **Graphiti文档**: Local Skill `@graphiti` (完整框架文档)
- **Py-FSRS文档**: 官方GitHub仓库
- **LangGraph文档**: Local Skill `@langgraph` (952页)

---

**文档生成时间**: 2025-11-14
**生成工具**: Claude Code PM Agent
**审批状态**: ✅ 已通过用户审批
**实施状态**: 🔄 待SM Agent创建Story文件

---

**END OF CHANGE LOG**
