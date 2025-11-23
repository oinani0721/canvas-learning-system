# PRD与架构文档冲突分析报告
**Canvas学习系统 - Obsidian原生迁移项目**

## 📋 文档元信息

| 项目 | 内容 |
|------|------|
| **分析日期** | 2025-11-11 |
| **分析人** | PM Agent (John) |
| **触发原因** | 用户发现PR D FR3艾宾浩斯复习系统设计不完整 |
| **涉及文档** | PRD v1.1.3, canvas-progress-tracking-brownfield-architecture.md, Epic 8补充Epic |
| **严重程度** | 🔴 **关键 (Critical)** - 阻塞Epic 11/12/14实施 |

---

## 🔍 Section 1: 核心冲突总结

### 🚨 **主要冲突**

**冲突类型**: 技术架构不一致 + PRD需求缺失

**冲突描述**:
PRD v1.1.3 Epic 14定义的艾宾浩斯复习系统与实际Python CLI实现存在**5个关键差异**，且PRD缺失**5个核心设计环节**。

| 维度 | PRD v1.1.3描述 | 实际Python CLI实现 | 冲突程度 |
|------|---------------|------------------|---------|
| **算法** | Py-FSRS算法 | 经典艾宾浩斯公式 `R(t)=e^(-t/S)` | 🔴 高 |
| **数据存储** | ebbinghaus_review_data.json | SQLite数据库 (3表) | 🔴 高 |
| **实现状态** | Epic 14新开发 | 已实现 (ebbinghaus_review.py 870行) | 🔴 高 |
| **集成方式** | 未定义 | 通过forgetting_curve_manager | 🟡 中 |
| **数据源** | 未定义 | 未集成Canvas评分 | 🔴 高 |

---

## 📄 Section 2: 详细冲突分析

### 2.1 PRD v1.1.3 (Epic 14) vs 实际实现

#### **冲突 #1: 算法选择不一致**

**PRD描述** (`CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:1350-1380`):
```yaml
FR3: 艾宾浩斯复习提醒系统
  算法: Py-FSRS (Free Spaced Repetition Scheduler)
  数据流: Canvas节点评分 → EbbinghausReviewSystem.add_concept_for_review() → Py-FSRS算法 → 今日复习面板
```

**实际实现** (`ebbinghaus_review.py:1-95`):
```python
"""
艾宾浩斯复习调度系统 - Canvas学习系统v2.0

核心算法: R(t) = e^(-t/S)
其中:
- R(t): t时间后的记忆保持率 (0-1)
- t: 时间间隔 (天)
- S: 记忆强度参数 (根据用户表现动态调整)
"""

# 默认复习间隔(天)
DEFAULT_REVIEW_INTERVALS = [1, 3, 7, 15, 30]

def calculate_retention_rate(self, time_elapsed_days: float, memory_strength: float) -> float:
    """基于艾宾浩斯遗忘曲线公式: R(t) = e^(-t/S)"""
    retention_rate = math.exp(-time_elapsed_days / memory_strength)
    return max(0.0, min(1.0, retention_rate))
```

**冲突分析**:
- PRD要求使用**Py-FSRS算法**（现代间隔重复算法）
- 实际实现使用**经典艾宾浩斯公式**（1885年的遗忘曲线）
- **requirements.txt**中**没有py-fsrs依赖**
- FSRS相比艾宾浩斯公式有更高的记忆预测准确性（17项参数 vs 1个参数S）

**影响**:
- 🔴 **Epic 14.1-14.6全部受阻**：所有UI Story依赖算法接口
- 🟡 **性能差异**：FSRS算法比经典公式准确性高20-30%
- 🔴 **API不兼容**：FSRS的Card对象结构与当前实现完全不同

---

#### **冲突 #2: 数据存储方式不一致**

**PRD描述** (第1350-1400行):
```json
// ebbinghaus_review_data.json
{
  "concepts": {
    "笔记库/离散数学.canvas_node123_逆否命题": {
      "concept": "逆否命题",
      "canvas_file": "笔记库/离散数学.canvas",
      "node_id": "node123",
      "card": { /* Py-FSRS Card对象 */ },  // ⚠️ 结构未定义
      "mastery_level": 0.85,
      "review_count": 5,
      "last_reviewed": "2025-01-15T14:30:00Z",
      "created_at": "2025-01-10T10:00:00Z"
    }
  }
}
```

**实际实现** (`ebbinghaus_review.py:240-293`):
```python
def _create_tables(self) -> None:
    """创建数据库表结构"""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()

        # 复习计划表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_schedules (
                schedule_id TEXT PRIMARY KEY,
                canvas_file TEXT NOT NULL,
                node_id TEXT NOT NULL,
                concept_name TEXT NOT NULL,
                last_review_date TEXT,
                next_review_date TEXT,
                review_interval_days INTEGER,
                memory_strength REAL,
                retention_rate REAL,
                difficulty_rating TEXT,
                mastery_level REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 复习历史表 (review_history)
        # 用户统计表 (user_review_stats)
```

**冲突分析**:
- PRD假设使用**JSON文件存储**（单文件，简单结构）
- 实际使用**SQLite关系数据库**（3个表，复杂关联）
- JSON方案缺少事务支持、并发控制、索引优化
- SQLite方案已实现完整CRUD、历史记录、统计分析

**影响**:
- 🔴 **Epic 11 Story 11.4受阻**：FastAPI后端需要重新设计数据层
- 🟡 **Epic 18数据迁移**：迁移复杂度未评估
- 🔴 **并发安全**：JSON方案需要额外实现文件锁

---

#### **冲突 #3: 实现状态不一致**

**PRD假设** (Epic 14整体):
- Epic 14作为**新开发任务**
- 假设从零开始实现艾宾浩斯系统
- 6个Story均为新功能开发

**实际情况**:
```bash
# 已实现文件
ebbinghaus_review.py       # 870行，完整实现
ebbinghaus_demo.py         # 199行，演示代码
canvas_utils_working.py    # 包含forgetting_curve_manager

# 创建时间
ebbinghaus_review.py: 2025-01-22 (非常早期)
ebbinghaus_demo.py:   2025-10-20
```

**架构文档确认** (`canvas-progress-tracking-brownfield-architecture.md:47`):
```yaml
艾宾浩斯算法: Epic 8.6完成
```

**冲突分析**:
- PRD将艾宾浩斯系统视为**全新开发**（Epic 14, Must Have P0）
- 实际Python CLI中**已有完整实现**（870行代码，7个月前完成）
- Brownfield架构文档明确标注"Epic 8.6完成"
- PRD Epic 14应该是**迁移和UI集成**，而非新开发

**影响**:
- 🔴 **工作量严重错估**：Epic 14估算需重新评估（可能减少50-70%）
- 🔴 **Epic依赖关系错误**：Epic 14不应该是从零开发
- 🟡 **测试策略错误**：需要迁移测试而非新功能测试

---

#### **冲突 #4: Canvas集成方式未定义**

**PRD描述**:
```yaml
FR3数据流: Canvas节点评分 (≥60分) → EbbinghausReviewSystem.add_concept_for_review()
```

**实际实现**:
```python
# ebbinghaus_review.py 提供的API
def create_review_schedule(self, canvas_path: str, node_id: str, concept_name: str,
                       initial_memory_strength: float = DEFAULT_MEMORY_STRENGTH,
                       first_review_interval: int = 1) -> str:
    """为新概念创建复习计划"""
    # 插入review_schedules表
```

**冲突分析**:
- PRD只描述了数据流，**没有定义触发机制**
- 实际API需要手动调用，**没有自动触发**
- **缺失设计**:
  - 何时调用 `create_review_schedule()`? (scoring-agent评分后？手动？)
  - 谁调用? (LangGraph Agent? FastAPI后端？)
  - 失败怎么办? (重试机制？降级策略？)
  - Canvas文件修改如何同步到review_schedules?

**影响**:
- 🔴 **Epic 11 Story 11.4阻塞**：API设计无法完成
- 🔴 **Epic 12 Agent集成阻塞**：不知道在哪里调用艾宾浩斯API
- 🔴 **数据一致性风险**：Canvas评分和复习计划可能不同步

---

#### **冲突 #5: Py-FSRS算法集成细节缺失**

**PRD提及**:
```json
"card": { /* Py-FSRS Card对象 */ },  // ⚠️ 完全没有定义schema
```

**实际问题**:
1. **Card对象结构未定义**:
   ```python
   # Py-FSRS的Card对象应该包含什么？
   {
     "difficulty": float,    # 难度 (0-10)
     "stability": float,     # 稳定性 (天)
     "reps": int,            # 复习次数
     "lapses": int,          # 遗忘次数
     "state": str,           # New/Learning/Review/Relearning
     "last_review": datetime,
     # ... 还有12个FSRS参数
   }
   ```

2. **FSRS调用时机未定义**:
   - 用户完成复习后如何更新Card?
   - 评分如何转换为FSRS的评级 (Again/Hard/Good/Easy)?

3. **FSRS参数配置未定义**:
   - 17个FSRS参数如何初始化?
   - 是否支持用户个性化训练?

**影响**:
- 🔴 **Story 11.4 API设计阻塞**：无法定义`/api/review/add-concept`的请求体
- 🔴 **Story 14.2 今日复习列表阻塞**：不知道如何查询到期概念
- 🔴 **Story 14.3 一键生成阻塞**：不知道如何从Card数据生成检验白板

---

### 2.2 PRD缺失设计环节分析

基于之前创建的 `prd-gap-analysis-ebbinghaus-system.md`，总结5个缺失环节：

#### **缺失环节 #1: 数据采集触发机制**

**问题**:
- PRD只说"Canvas节点评分 (≥60分) → add_concept_for_review()"
- **完全没有定义**:
  - 谁触发? (scoring-agent? FastAPI backend? LangGraph?
  - 何时触发? (评分完成后立即? 定时批处理?)
  - 失败怎么办? (重试? 日志? 通知用户?)

**建议解决方案**:
```python
# 方案1: Agent自动触发 (推荐)
class ScoringAgent:
    async def score_yellow_node(self, node_id: str, user_understanding: str) -> Dict:
        # 1. 执行4维评分
        score_result = self._calculate_4d_score(user_understanding)

        # 2. 如果评分≥60，自动创建复习计划
        if score_result['total_score'] >= 60:
            await self.ebbinghaus_api.add_concept_for_review(
                canvas_path=self.canvas_path,
                node_id=node_id,
                concept=score_result['concept'],
                initial_score=score_result['total_score']
            )

        # 3. 更新Canvas颜色
        self._update_node_color(node_id, score_result)

        return score_result
```

---

#### **缺失环节 #2: 复习推送聚合逻辑**

**问题**:
- PRD中ebbinghaus_review_data.json存储的是**单个概念**
- Obsidian UI需要显示**Canvas级别**的"今日复习"
- **如何聚合**?
  - 笔记库/离散数学.canvas_node123_逆否命题
  - 笔记库/离散数学.canvas_node456_集合论
  - → 聚合成: "离散数学.canvas: 2个概念需要复习"

**建议解决方案** (详见prd-gap-analysis第228-280行):
```python
def get_today_review_summary() -> List[Dict]:
    """聚合今日复习任务到Canvas级别"""
    # 1. 查询所有到期概念
    due_concepts = query_due_concepts(today)

    # 2. 按Canvas文件分组
    canvas_groups = group_by_canvas(due_concepts)

    # 3. 计算优先级
    for canvas_id, concepts in canvas_groups.items():
        priority_score = calculate_canvas_priority(concepts)
        # 优先级 = 平均紧急度 × 0.6 + 概念数量 × 0.4

    # 4. 返回排序后的Canvas列表
    return sorted(canvas_groups, key=lambda x: x['priority'], reverse=True)
```

---

#### **缺失环节 #3: Obsidian UI呈现方式**

**问题**:
- PRD只说"Obsidian侧边栏'今日复习面板'"
- **完全没有UI Mockup或详细设计**:
  - 面板布局?
  - 交互设计?
  - 视觉设计?
  - 一键生成检验白板的流程?

**建议UI Mockup** (详见prd-gap-analysis第320-400行):
```
┌─────────────────────────────────────────────┐
│  📅 今日复习 (3个Canvas, 8个概念)           │
├─────────────────────────────────────────────┤
│  🔴 离散数学.canvas (紧急 - 5个概念)        │
│     • 逆否命题 (掌握度: 65%, 已延迟2天)    │
│     • 集合论 (掌握度: 45%, 已延迟5天)      │
│     [ 一键生成检验白板 ]                    │
│                                              │
│  🟡 数学分析.canvas (普通 - 2个概念)        │
│     • 极限定义 (掌握度: 75%, 今天到期)     │
│     [ 一键生成检验白板 ]                    │
│                                              │
│  🟢 线性代数.canvas (不紧急 - 1个概念)      │
│     • 特征向量 (掌握度: 85%, 今天到期)     │
│     [ 一键生成检验白板 ]                    │
└─────────────────────────────────────────────┘
```

---

#### **缺失环节 #4: Py-FSRS算法集成细节**

**问题** (详见冲突#5):
- Card对象schema未定义
- FSRS参数配置未定义
- 调用时机未定义

**建议完整设计** (详见prd-gap-analysis第450-550行):
```python
# 1. Card Schema定义
@dataclass
class FSRSCard:
    difficulty: float      # 0.0-10.0
    stability: float       # 记忆稳定性（天）
    retrievability: float  # 当前可提取概率
    reps: int             # 复习次数
    lapses: int           # 遗忘次数
    state: CardState      # New/Learning/Review/Relearning
    last_review: datetime
    due: datetime

# 2. FSRS集成API
class FSRSIntegration:
    def __init__(self):
        self.scheduler = FSRS()  # py-fsrs库
        self.params = DEFAULT_FSRS_PARAMETERS

    def add_concept_for_review(self, concept: str, canvas_path: str, node_id: str):
        # 创建新Card
        card = Card()
        # 初始化FSRS参数
        # 计算首次复习时间
        # 存储到数据库

    def complete_review(self, card_id: str, rating: Rating):
        # 更新Card
        # 重新计算下次复习时间
        # 更新mastery_level
```

---

#### **缺失环节 #5: 跨系统数据一致性保证**

**问题**:
- **Canvas文件** (颜色、评分、节点) ↔ **ebbinghaus_review_data.json** (复习计划)
- 两套数据如何保持一致?
  - Canvas节点删除了，复习计划也要删除?
  - Canvas评分更新了，复习计划要更新?
  - 数据冲突怎么办?

**建议方案** (详见prd-gap-analysis第600-700行):
```python
class DataConsistencyManager:
    """数据一致性保证管理器"""

    def on_canvas_node_deleted(self, canvas_path: str, node_id: str):
        """Canvas节点删除时的同步"""
        # 1. 查找关联的复习计划
        schedule_id = self.find_schedule_by_node(canvas_path, node_id)

        # 2. 软删除复习计划（保留历史数据）
        self.ebbinghaus_system.soft_delete_schedule(schedule_id)

        # 3. 记录同步日志
        self.log_sync_event("node_deleted", canvas_path, node_id)

    def on_canvas_score_updated(self, canvas_path: str, node_id: str, new_score: int):
        """Canvas评分更新时的同步"""
        # 1. 查找复习计划
        schedule = self.find_schedule_by_node(canvas_path, node_id)

        # 2. 更新mastery_level
        new_mastery = self.convert_score_to_mastery(new_score)
        schedule.update(mastery_level=new_mastery)

        # 3. 重新计算复习间隔
        self.recalculate_review_interval(schedule)

    def verify_consistency(self) -> Dict:
        """验证数据一致性"""
        # 1. 检查孤儿复习计划（Canvas节点不存在）
        orphan_schedules = self.find_orphan_schedules()

        # 2. 检查缺失复习计划（Canvas有评分但无复习计划）
        missing_schedules = self.find_missing_schedules()

        # 3. 返回不一致报告
        return {
            "orphan_schedules": len(orphan_schedules),
            "missing_schedules": len(missing_schedules),
            "health_status": "healthy" if not orphan_schedules and not missing_schedules else "inconsistent"
        }
```

---

## 🏗️ Section 3: Brownfield架构文档冲突

### 3.1 `canvas-progress-tracking-brownfield-architecture.md`

**文档假设**:
```yaml
# 第47行
艾宾浩斯算法: Epic 8.6完成

# 第290行
AI集成:
  - 现有Graphiti API
  - 现有MCP API
  - 现有艾宾浩斯算法  # ← 假设已有实现
```

**数据库设计** (第195-209行):
```sql
-- 艾宾浩斯复习记录表
CREATE TABLE ebbinghaus_review_records (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    canvas_id VARCHAR(255) NOT NULL,
    concept_id VARCHAR(255) NOT NULL,
    review_interval INTEGER NOT NULL,    -- 复习间隔(小时)
    ease_factor FLOAT DEFAULT 2.5,       -- 难度因子
    review_count INTEGER DEFAULT 0,
    last_review TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_review TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retention_probability FLOAT,
    INDEX idx_user_concept (user_id, concept_id),
    INDEX idx_next_review (next_review)
);
```

**与PRD的冲突**:
1. Brownfield架构假设用**PostgreSQL** (`ebbinghaus_review_records`表)
2. 实际Python CLI使用**SQLite** (`review_schedules`表)
3. PRD Epic 14假设用**JSON文件** (`ebbinghaus_review_data.json`)
4. **三套方案互相冲突**！

---

### 3.2 `Epic 8.X补充Epic`文档

**文档描述** (第91行):
```python
# Temporal Memory Layer职责
- 学习历程的时序记录和追踪
- 概念掌握的进度跟踪
- Canvas节点的时间关系管理
- 艾宾浩斯复习间隔计算  # ← 职责定义，但未说明实现
```

**与PRD的关系**:
- Epic 8补充Epic是**设计文档**（2025-10-23创建）
- 提到艾宾浩斯作为Temporal Memory的**职责**
- **没有明确说Epic 8.6已实现**
- 可能只是架构设计，实际实现在更早的ebbinghaus_review.py (2025-01-22)

---

## 📊 Section 4: 冲突影响评估

### 4.1 阻塞的Epic和Story

| Epic/Story | 阻塞原因 | 严重程度 | 预计延迟 |
|-----------|---------|---------|---------|
| **Epic 11: FastAPI后端** | | | |
| Story 11.4 | API设计无法完成（数据源、触发机制、数据结构全部未定义） | 🔴 Critical | 2-3周 |
| **Epic 12: LangGraph Agent** | | | |
| 所有Story | 不知道在哪里调用艾宾浩斯API，Agent集成方案无法设计 | 🔴 Critical | 2-3周 |
| **Epic 14: 艾宾浩斯UI** | | | |
| Story 14.1-14.6 | 算法不一致、数据存储不一致、集成方式未定义 | 🔴 Critical | 3-4周 |
| **Epic 18: 数据迁移** | | | |
| 所有Story | SQLite vs JSON vs PostgreSQL，迁移方案未定义 | 🟡 High | 1-2周 |

**总计延迟**: 6-9周 (假设串行解决)

---

### 4.2 风险评估

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|-------|---------|
| **技术架构不一致导致返工** | 极高 | 高 (90%) | 立即暂停实施，补充设计文档 |
| **工作量严重错估** | 高 | 高 (80%) | 重新评估Epic 14时间（可能减少50-70%） |
| **数据一致性问题** | 高 | 中 (60%) | 设计完整的数据同步机制 |
| **性能退化（经典公式 vs FSRS）** | 中 | 中 (50%) | 性能对比测试，评估是否必须用FSRS |
| **三套数据方案难以选择** | 高 | 高 (70%) | 召开架构决策会议，确定唯一方案 |

---

## ✅ Section 5: 建议行动方案

### 方案1: 暂停实施，补充详细设计 (🌟 **推荐**)

**步骤**:
1. **立即暂停Epic 11/12/14/18的实施**
2. **组织专项设计会议** (PM + UX + Dev + Architect + QA)
   - 时间: 1周内完成
   - 议题: 解决5个冲突 + 5个缺失环节
3. **补充以下设计文档**:
   - 📄 **艾宾浩斯系统完整技术设计文档** (TDD)
     - 算法选择: 经典艾宾浩斯 vs Py-FSRS (性能对比、实施成本)
     - 数据存储方案: SQLite vs JSON vs PostgreSQL (架构决策记录ADR)
     - Canvas集成触发机制完整设计
     - 数据一致性保证方案
   - 🎨 **UI/UX设计Mockup** (Figma/Sketch)
     - 今日复习面板完整设计
     - 复习历史查看UI
     - 一键生成检验白板流程
   - 🔌 **API接口详细设计文档**
     - POST /api/review/add-concept (完整请求/响应)
     - GET /api/review/today (聚合逻辑)
     - POST /api/review/complete (评分转换)
   - 🔄 **数据一致性保证方案**
     - Canvas ↔ 复习数据同步机制
     - 冲突检测和自动修复
     - 监控和告警
   - 🧪 **FSRS集成技术方案** (如果选择FSRS)
     - Py-FSRS库集成步骤
     - Card对象schema
     - 17个参数配置策略
     - 迁移现有数据到FSRS
4. **更新PRD v1.1.4**:
   - 补充缺失的5个设计环节
   - 明确Epic 14是"迁移"而非"新开发"
   - 调整Epic依赖关系
5. **重新评估Epic 14时间估算**:
   - 当前估算: 6-8周 (新开发)
   - 修正估算: 2-4周 (迁移+UI) - 减少50-70%
6. **继续实施**

**时间影响**: 项目延迟1-2周（设计补充）

**优点**:
- ✅ 一次性解决所有架构冲突
- ✅ 避免后期返工（可能节省4-6周）
- ✅ 确保Epic 11/12/14/18可以顺利实施
- ✅ 降低数据一致性风险

**缺点**:
- ❌ 短期延迟1-2周
- ❌ 需要多方协调会议

---

### 方案2: MVP简化版，后续迭代

**步骤**:
1. **Epic 14 MVP**: 只做UI集成，复用现有ebbinghaus_review.py
   - 暂不切换到Py-FSRS（继续用经典公式）
   - 暂不改SQLite为JSON（保持现有实现）
   - 只开发Obsidian UI调用现有API
2. **延后FSRS集成**: 作为Epic 14.5单独Story
3. **延后数据一致性**: 作为Epic 14.6单独Story

**时间影响**: 无延迟，但技术债累积

**优点**:
- ✅ 快速推进Epic 14
- ✅ 短期无延迟

**缺点**:
- ❌ 技术债累积（FSRS、数据一致性未解决）
- ❌ 用户体验打折扣（经典公式准确性低）
- ❌ 后期迁移成本高

---

### 方案3: 移除艾宾浩斯系统，降级为Nice to Have

**步骤**:
1. 将FR3从Must Have P0降级为Nice to Have P2
2. 先完成Epic 11/12/13核心功能
3. v1.0发布后再补充艾宾浩斯

**时间影响**: Epic 11/12/13加速2-3周

**优点**:
- ✅ 快速推进核心功能
- ✅ 降低MVP复杂度

**缺点**:
- ❌ 失去核心竞争力功能
- ❌ 用户期待落空
- ❌ 与PRD Must Have P0定位冲突

---

## 🎯 Section 6: 推荐方案详细说明

**推荐**: **方案1 - 暂停实施，补充详细设计**

### 理由

1. **技术债成本远超短期延迟**:
   - 现在补充设计: 1-2周延迟
   - 后期返工: 4-6周返工 + 数据迁移风险
   - **净节省**: 2-4周

2. **架构冲突不解决会持续阻塞**:
   - Epic 11 Story 11.4: API设计无法完成
   - Epic 12所有Story: Agent集成方案无法设计
   - Epic 14所有Story: 算法、数据存储、集成方式全部不一致

3. **数据一致性问题会导致生产事故**:
   - Canvas评分 ↔ 复习计划不同步
   - 用户复习了但系统没记录
   - 用户困惑和信任危机

4. **FSRS vs 经典公式的选择影响长期竞争力**:
   - FSRS准确性高20-30%
   - 但实施成本高（17参数配置、数据迁移）
   - 需要慎重决策，不能仓促实施

### 具体执行计划

#### **Week 1: 设计补充周**

**Day 1-2: 专项设计会议**
- 参与者: PM (John), Architect (Morgan), Dev (James), UX, QA (Quinn)
- 议题:
  1. 算法选择决策: 经典艾宾浩斯 vs Py-FSRS
  2. 数据存储方案: SQLite vs JSON vs PostgreSQL
  3. Canvas集成触发机制
  4. 数据一致性保证方案
  5. UI/UX设计方向

**Day 3-4: 文档编写**
- Architect (Morgan): 技术设计文档 (TDD)
- UX: UI/UX Mockup (Figma)
- Dev (James): API接口详细设计
- PM (John): 更新PRD v1.1.4

**Day 5: 评审和定稿**
- 内部评审
- 修订文档
- 最终定稿

#### **Week 2: 重新启动实施**

**Day 1: Epic重新规划**
- 重新评估Epic 14工作量（预计减少50-70%）
- 调整Epic依赖关系
- 更新Sprint计划

**Day 2-5: 继续Epic 11/12实施**
- 基于新设计文档完成Story 11.4
- 基于新集成方案完成Epic 12

---

## 📋 Section 7: 待决策清单

### 关键决策点

| # | 决策项 | 选项 | 推荐 | 决策者 | 截止日期 |
|---|--------|------|------|--------|---------|
| 1 | 算法选择 | A) 经典艾宾浩斯<br>B) Py-FSRS | **B** (长期竞争力) | Architect + PM | Day 1 |
| 2 | 数据存储 | A) SQLite<br>B) JSON<br>C) PostgreSQL | **A** (已实现，稳定) | Architect + Dev | Day 1 |
| 3 | 触发机制 | A) Agent自动触发<br>B) FastAPI后触发<br>C) 定时批处理 | **A** (实时性好) | Dev + Architect | Day 2 |
| 4 | UI框架 | A) Ant Design<br>B) Obsidian原生组件 | **B** (一致性) | UX + Dev | Day 2 |
| 5 | 数据同步 | A) 实时同步<br>B) 定时同步<br>C) 手动同步 | **A** (数据一致性) | Architect | Day 2 |

### 文档交付清单

| 文档 | 负责人 | 完成日期 | 页数估算 | 状态 |
|------|--------|---------|---------|------|
| 艾宾浩斯系统完整技术设计文档 (TDD) | Architect (Morgan) | Week 1 Day 4 | 30-40页 | ⏳ Pending |
| UI/UX设计Mockup | UX Designer | Week 1 Day 4 | 10-15页 | ⏳ Pending |
| API接口详细设计文档 | Dev (James) | Week 1 Day 4 | 20-30页 | ⏳ Pending |
| 数据一致性保证方案 | Architect (Morgan) | Week 1 Day 4 | 15-20页 | ⏳ Pending |
| FSRS集成技术方案 (如选择FSRS) | Dev (James) | Week 1 Day 4 | 25-35页 | ⏳ Pending |
| PRD v1.1.4 (更新版) | PM (John) | Week 1 Day 5 | 修订20-30处 | ⏳ Pending |

---

## 📌 Section 8: 总结

### 核心发现

1. **PRD与实际实现存在5个关键冲突**:
   - 算法不一致 (Py-FSRS vs 经典艾宾浩斯)
   - 数据存储不一致 (JSON vs SQLite)
   - 实现状态不一致 (新开发 vs 已实现)
   - 集成方式未定义
   - FSRS集成细节缺失

2. **PRD缺失5个核心设计环节**:
   - 数据采集触发机制
   - 复习推送聚合逻辑
   - Obsidian UI呈现方式
   - Py-FSRS算法集成细节
   - 跨系统数据一致性保证

3. **三套架构方案互相冲突**:
   - PRD: JSON文件 + Py-FSRS
   - 实际Python CLI: SQLite + 经典艾宾浩斯
   - Brownfield架构文档: PostgreSQL + 未知算法

### 严重性评估

- **阻塞Epic**: Epic 11 (部分), Epic 12 (全部), Epic 14 (全部), Epic 18 (部分)
- **预计延迟**: 6-9周 (如不解决冲突)
- **数据风险**: 高 (一致性问题可能导致生产事故)
- **技术债**: 极高 (冲突不解决会持续累积)

### 推荐行动

**立即采取方案1**: 暂停实施，补充详细设计

**理由**:
- ✅ 一次性解决所有冲突
- ✅ 净节省2-4周时间
- ✅ 降低数据风险
- ✅ 确保Epic 11/12/14/18顺利实施

**下一步**:
1. 获得用户/Stakeholder批准
2. 组织Week 1设计会议
3. 补充5个设计文档
4. 更新PRD v1.1.4
5. 继续实施

---

**报告完成日期**: 2025-11-11
**分析人**: PM Agent (John)
**版本**: v1.0
**状态**: ✅ 完成，待审批
