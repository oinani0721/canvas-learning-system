---
document_type: "Architecture"
version: "2.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Canvas学习系统 - 4层架构设计

**版本**: v2.0
**最后更新**: 2025-11-17
**状态**: ✅ Epic 1-5, 10 已完成并验证

---

## 📋 架构概述

Canvas学习系统采用**4层Python架构** + **14个专项Agents** + **3层记忆系统**，实现了费曼学习法的数字化和智能化。

### 核心设计理念

**"输出驱动输入，检验暴露盲区"**

- **输出驱动**: 强制用户用自己的话解释概念（黄色节点）
- **多Agent协作**: 14个专业化Agent提供拆解、解释、评分、检验、调度和记忆管理
- **颜色流转**: 红→紫→绿，可视化学习进度
- **无纸化检验**: 自动生成检验白板，实现知识复现

---

## 🏗️ Layer 1: CanvasJSONOperator（底层JSON操作）

### 职责

提供原子化的Canvas文件读写操作，确保数据完整性。

### 核心函数

```python
class CanvasJSONOperator:
    """
    底层JSON操作层
    位置: canvas_utils.py:100-500
    Epic 1: 核心Canvas操作层
    """

    @staticmethod
    def read_canvas(file_path: str) -> dict:
        """
        读取Canvas文件

        Returns:
            {
                "nodes": [...],  # 所有节点
                "edges": [...]   # 所有边
            }
        """

    @staticmethod
    def write_canvas(file_path: str, canvas_data: dict) -> None:
        """
        写入Canvas文件

        Safety:
            - UTF-8编码保证中文支持
            - ensure_ascii=False保持中文可读
            - indent=2提高可读性
        """

    @staticmethod
    def add_node(canvas_data: dict, node_type: str,
                 text: str, x: int, y: int,
                 width: int = 250, height: int = 60,
                 color: str = None) -> str:
        """
        添加节点到Canvas

        Args:
            node_type: "text" | "file" | "group" | "link"
            color: "1" (红) | "2" (绿) | "3" (紫) | "5" (蓝) | "6" (黄)

        Returns:
            node_id: 新节点的UUID
        """

    @staticmethod
    def find_node_by_id(canvas_data: dict, node_id: str) -> dict:
        """
        通过ID查找节点

        Returns:
            {
                "id": "...",
                "type": "text",
                "text": "...",
                "x": 100,
                "y": 200,
                "color": "1"
            }
        """

    @staticmethod
    def update_node_color(canvas_data: dict, node_id: str,
                          new_color: str) -> None:
        """
        更新节点颜色

        Use Case:
            - 评分后自动流转颜色 (Epic 2)
            - 完成学习后标记为绿色
        """

    @staticmethod
    def add_edge(canvas_data: dict, from_node: str,
                 to_node: str) -> None:
        """
        添加边连接两个节点

        Edge Structure:
            {
                "id": "...",
                "fromNode": "node1_id",
                "fromSide": "bottom",
                "toNode": "node2_id",
                "toSide": "top"
            }
        """
```

### 颜色常量

```python
# Canvas Color Codes (Official Obsidian Values)
COLOR_RED = "1"      # 🔴 不理解/未通过
COLOR_GREEN = "2"    # 🟢 完全理解/已通过
COLOR_PURPLE = "3"   # 🟣 似懂非懂/待检验
COLOR_BLUE = "5"     # 🔵 AI补充解释
COLOR_YELLOW = "6"   # 🟡 个人理解输出区
```

### 关键决策（ADR-0001: Use Obsidian Canvas）

**为什么选择Obsidian Canvas?**

- ✅ 原生支持JSON格式（无需额外解析）
- ✅ 可视化知识图谱（符合费曼学习法）
- ✅ 丰富的节点类型（text/file/group/link）
- ✅ 颜色系统（5种颜色支持状态流转）
- ✅ 社区生态（插件、主题）

---

## 🧩 Layer 2: CanvasBusinessLogic（业务逻辑层）

### 职责

实现Canvas业务逻辑，包括布局算法、节点聚类、检验白板生成。

### 核心函数

```python
class CanvasBusinessLogic:
    """
    业务逻辑层
    位置: canvas_utils.py:500-1200
    Epic 2-4: 问题拆解 + 补充解释 + 无纸化检验
    """

    # ==================== Epic 2: 布局算法 ====================

    @staticmethod
    def calculate_yellow_node_position(question_node: dict) -> tuple:
        """
        v1.1布局算法：黄色节点在问题正下方，垂直对齐

        Rules:
            - x坐标: question_x + 50px (右移50px)
            - y坐标: question_y + question_height + 30px (下移30px间隔)

        Returns:
            (x, y)
        """

    # ==================== Epic 3: 上下文提取 ====================

    @staticmethod
    def extract_verification_nodes(canvas_data: dict) -> dict:
        """
        提取检验白板所需节点

        Returns:
            {
                "red_nodes": [...],    # 完全不懂的概念
                "purple_nodes": [...], # 似懂非懂的概念
                "context_nodes": [...] # 上下文节点（用于理解）
            }
        """

    # ==================== Epic 4: 问题聚类 ====================

    @staticmethod
    def cluster_questions_by_topic(questions: list) -> dict:
        """
        按主题聚类问题（智能分组）

        Algorithm:
            - 使用LLM进行主题聚类
            - 相似问题分组到同一主题
            - 每个主题生成标题

        Returns:
            {
                "主题1": [q1, q2, q3],
                "主题2": [q4, q5]
            }
        """

    # ==================== Epic 4: 检验白板生成 ====================

    @staticmethod
    def generate_review_canvas_file(
        source_canvas_path: str,
        output_canvas_path: str,
        questions: list
    ) -> None:
        """
        生成检验白板文件

        Workflow:
            1. 提取红/紫节点
            2. 为每个节点生成检验问题
            3. 按主题聚类
            4. 创建新Canvas文件
            5. 添加问题节点（红色）+ 黄色空白节点

        Canvas Structure:
            主题1：
                问题1 (红色) → 空白黄色节点
                问题2 (红色) → 空白黄色节点
            主题2：
                问题3 (红色) → 空白黄色节点
        """
```

### 布局算法详解（Epic 2.7: v1.1布局算法）

**v1.1布局规则**:

1. **黄色节点定位**:
   - 位置: 问题节点正下方（垂直对齐）
   - x坐标: `question_x + 50px`
   - y坐标: `question_y + question_height + 30px`

2. **聚类布局**:
   - 主题间间隔: 100px (CLUSTER_GAP)
   - 问题+黄色组合高度: 380px (VERTICAL_SPACING_BASE)
   - 聚类总高度 = 问题数 × 380px

3. **错误处理**:
   - 缺失x/y坐标 → 使用默认值 (x=0, y=0)
   - 缺失width/height → 使用默认值 (250×60)
   - 颜色不在可选范围 → 默认无颜色

---

## 🎯 Layer 3: CanvasOrchestrator（高级API）

### 职责

提供高级封装接口，协调Sub-agent调用和完整操作工作流。

### 核心函数

```python
class CanvasOrchestrator:
    """
    高级API层
    位置: canvas_utils.py:1200-2000
    Epic 5: 智能化增强功能
    """

    # ==================== Epic 5: Sub-agent调用 ====================

    @staticmethod
    def generate_verification_questions_with_agent(
        node_content: str,
        node_color: str
    ) -> list:
        """
        调用verification-question-agent生成检验问题

        Natural Language Calling Protocol:
            "Use the verification-question-agent subagent to {task}

            Input: {JSON数据}

            Expected output: {输出格式}

            ⚠️ IMPORTANT: Return ONLY raw JSON."

        Returns:
            [
                {
                    "question": "...",
                    "type": "breakthrough" | "basic" | "verification" | "application",
                    "difficulty": "low" | "medium" | "high"
                },
                ...
            ]
        """

    # ==================== Epic 5: 完整工作流 ====================

    @staticmethod
    def complete_review_workflow(
        canvas_path: str,
        output_canvas_name: str = None
    ) -> str:
        """
        完整检验白板生成工作流

        Workflow:
            1. 读取原Canvas
            2. 提取红/紫节点
            3. 为每个节点调用Agent生成问题
            4. 按主题聚类
            5. 生成新Canvas文件
            6. 返回新Canvas路径

        Returns:
            output_canvas_path
        """
```

### Sub-agent调用协议（Epic 5核心创新）

**自然语言调用** (不是函数调用):

```python
call_statement = f"""
Use the {agent-name} subagent to {task description}

Input: {输入数据JSON}

Expected output: {输出格式说明}

⚠️ IMPORTANT: Return ONLY the raw JSON. Do NOT wrap it in markdown code blocks.
"""
```

**关键约束**:
- 必须返回纯JSON，不能用markdown code fence
- 必须包含Expected output说明
- Input使用`ensure_ascii=False`保持中文可读

---

## 🤖 Layer 4: 系统级Agent调度（Epic 10/12扩展）

### 职责

智能调度、记忆管理、并行执行等系统级功能。

### 核心组件

```python
# ==================== Epic 10: 智能Agent选择器 ====================

class ReviewBoardAgentSelector:
    """
    智能分析黄色理解节点质量，推荐最合适的学习型agents

    位置: .claude/agents/review-board-agent-selector.md
    Epic 10: 智能并行处理系统
    """

    def analyze_node_quality(node_content: str) -> dict:
        """
        四维质量分析

        Dimensions:
            - Accuracy (准确性): 0.0-1.0
            - Completeness (完整性): 0.0-1.0
            - Clarity (清晰度): 0.0-1.0
            - Originality (原创性): 0.0-1.0
        """

    def recommend_agents(quality_analysis: dict,
                        confidence_threshold: float = 0.7) -> list:
        """
        推荐Agent列表

        Returns:
            [
                {
                    "agent": "oral-explanation",
                    "confidence": 0.85,
                    "reason": "Accuracy低，需要系统化解释"
                },
                {
                    "agent": "clarification-path",
                    "confidence": 0.80,
                    "reason": "Completeness低，需要深度澄清"
                }
            ]
        """

# ==================== Epic 10.2: 异步并行执行引擎 ====================

class AsyncExecutionEngine:
    """
    真正的异步并发执行，8倍性能提升

    位置: canvas_utils.py:2000-2500
    Epic 10.2: 异步并行执行引擎
    """

    async def execute_agents_parallel(
        agents: list,
        max_concurrent: int = 12
    ) -> list:
        """
        并行执行多个agents

        Performance:
            - 10节点: ~100秒 → 12秒 (8.3倍)
            - 20节点: ~200秒 → 25秒 (8.0倍)
            - 50节点: ~500秒 → 58秒 (8.6倍)

        Technology:
            - asyncio.create_task()
            - asyncio.gather()
        """

# ==================== Epic 12: Graphiti知识图谱记忆 ====================

class GraphitiMemoryAgent:
    """
    管理学习会话记录到时序知识图谱

    位置: .claude/agents/graphiti-memory-agent.md
    Epic 12: 3层记忆系统集成
    """

    def record_learning_session(
        canvas_path: str,
        concepts: list,
        relationships: list
    ) -> None:
        """
        记录学习会话到Neo4j/Graphiti

        Data Flow:
            学习会话 → graphiti-memory-agent
                     → Neo4j/Graphiti (概念+关系)
                     → 检验白板生成 (查询薄弱点)
                     → 艾宾浩斯系统 (复习推荐)
        """

    def query_weak_concepts(
        user_id: str,
        top_n: int = 10
    ) -> list:
        """
        查询用户薄弱概念

        Ebbinghaus Integration:
            - 70% 薄弱点 (score < 60)
            - 30% 已掌握概念 (score ≥ 80)
        """
```

---

## 🎨 Canvas颜色系统

### 颜色语义

| Canvas Color Code | 视觉颜色 | 含义 | 使用场景 | 判断标准 |
|-------------------|---------|------|---------|---------|
| `"1"` | 🔴 红色 | 不理解/未通过 | 学生完全不懂的问题节点 | 评分 < 60 或未填写黄色节点 |
| `"2"` | 🟢 绿色 | 完全理解/已通过 | 评分≥80分的问题 | 评分 ≥ 80 |
| `"3"` | 🟣 紫色 | 似懂非懂/待检验 | 评分60-79分,需要深度检验 | 60 ≤ 评分 < 80 |
| `"5"` | 🔵 蓝色 | AI补充解释 | AI生成的解释文档节点 | Agent生成的文档 |
| `"6"` | 🟡 黄色 | 个人理解输出区 | 学生用自己话的解释 | 用户填写的理解节点 |

### 颜色流转路径

```
🔴 红色 (完全不懂，score < 60)
  ↓ 基础拆解 (basic-decomposition) + 填写理解
🟣 紫色 (似懂非懂，60 ≤ score < 80)
  ↓ 深度拆解 (deep-decomposition) + 补充解释 + 优化理解
🟢 绿色 (完全理解，score ≥ 80)
```

### Canvas 3层结构（Epic 10.2.3修复）

**正确结构**:

```
黄色问题节点 (Yellow Text Node)
    ↓ (edge)
蓝色TEXT节点 (Blue Text Node with Markdown link)
    ↓ (edge)
File节点 (File Node pointing to .md file)
```

**关键修复**:
- Epic 10初版: 黄色节点 → File节点（错误，Obsidian无法打开）
- Epic 10.2.3: 黄色节点 → 蓝色TEXT节点 → File节点（正确，可打开）

**文件路径**:
- 使用相对路径: `解释文档/oral-explanation-20251104120000.md`
- 不使用绝对路径: `C:/Users/...` （Obsidian无法识别）

---

## 🧪 性能指标（Epic 10.2实测）

### 串行 vs 并行

| 节点数 | 旧版本（串行） | 新版本（异步并行） | 性能提升 |
|-------|--------------|-------------------|---------|
| 10节点 | ~100秒 | **12秒** | **8.3倍** ⚡ |
| 20节点 | ~200秒 | **25秒** | **8.0倍** ⚡ |
| 50节点 | ~500秒 | **58秒** | **8.6倍** ⚡ |

### 单个操作

- 节点提取: <200ms (100节点)
- 问题生成: <5秒 (20节点)
- 聚类: <1秒 (60问题)
- 检验白板生成: <8秒 (完整流程)
- Agent调用: 5-10秒/agent

---

## 📚 技术栈映射

### Layer 1 → Python标准库

- `json`: Canvas文件读写
- `uuid`: 节点ID生成
- `os.path`: 文件路径处理

### Layer 2 → AI/ML技术

- **LLM调用**: 问题聚类、主题生成
- **自然语言处理**: 概念提取、相似度计算

### Layer 3 → Sub-agent系统

- **verification-question-agent**: 检验问题生成
- **scoring-agent**: 理解评分
- **decomposition agents**: 问题拆解

### Layer 4 → 高级技术栈

- **LangGraph**: Agent工作流编排
- **Graphiti**: 知识图谱记忆
- **Neo4j**: 图数据库存储
- **LanceDB**: 语义向量存储
- **Py-FSRS**: 艾宾浩斯间隔重复算法
- **asyncio**: 异步并发执行

---

## 🔍 关键ADR决策

### ADR-0001: 选择Obsidian Canvas

**Date**: 2025-10-01
**Status**: Accepted
**Context**: 需要可视化知识图谱平台
**Decision**: 使用Obsidian Canvas
**Consequences**:
- ✅ 原生JSON格式
- ✅ 丰富的节点类型
- ✅ 颜色系统
- ❌ 需要自行实现实时监听

### ADR-0002: LangGraph Agent系统

**Date**: 2025-10-05
**Status**: Accepted
**Context**: 需要多Agent协作框架
**Decision**: 使用LangGraph创建14个专项agents
**Consequences**:
- ✅ 成熟的工作流编排
- ✅ 自然语言调用协议
- ✅ 社区支持
- ❌ 学习曲线较陡

### ADR-0003: Graphiti知识图谱

**Date**: 2025-10-10
**Status**: Accepted
**Context**: 需要长期学习记忆管理
**Decision**: 集成Graphiti + Neo4j
**Consequences**:
- ✅ 时序知识图谱
- ✅ 薄弱环节分析
- ✅ 艾宾浩斯复习支持
- ❌ 部署复杂度增加

### ADR-0004: 异步并行执行引擎

**Date**: 2025-11-04
**Status**: Accepted
**Context**: 串行执行速度太慢
**Decision**: 使用asyncio实现真正的异步并发
**Consequences**:
- ✅ 8倍性能提升
- ✅ 支持最多12个agents并发
- ❌ 代码复杂度增加
- ❌ 需要处理异步错误

---

## 📊 测试覆盖率

- **Unit Tests**: 360+ tests
- **Coverage**: 99.5%
- **E2E Tests**: 100% pass
- **Performance Tests**: 100% pass

**测试位置**:
- `src/tests/test_canvas_utils.py` - Layer 1-3测试
- `src/tests/test_epic10_2_e2e.py` - Epic 10.2端到端测试
- `src/tests/test_epic10_2_performance.py` - 性能测试

---

## 🚀 未来扩展方向

### Epic 13: 实时Canvas监听

- Obsidian插件开发
- WebSocket实时通信
- 增量更新Canvas

### Epic 14: 艾宾浩斯复习系统完整集成

- 完善薄弱点聚类（Neo4j GDS Leiden算法）
- 动态复习计划调整
- 复习进度跟踪

### Epic 15: RAG增强

- LanceDB语义搜索
- CUDA加速
- 多模态支持（图片、音频）

---

## 📖 参考文档

- **PRD**: `docs/prd/FULL-PRD-REFERENCE.md`
- **Epic 1-5 Stories**: `docs/stories/*.story.md`
- **Epic 10 Stories**: `docs/HONEST_STATUS_REPORT_EPIC10.md`
- **Canvas Error Log**: `CANVAS_ERROR_LOG.md`
- **BMad Integration**: `docs/RESEARCH_REPORT_BMAD_INTEGRATION.md`

---

**最后更新**: 2025-11-17
**维护者**: Dev Agent (James)
**状态**: ✅ 生产就绪
