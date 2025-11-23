# Canvas监控系统业务逻辑完成 - Brownfield Enhancement PRD

**文档版本**: v2.0
**创建日期**: 2025-01-15
**项目类型**: Brownfield Enhancement
**作者**: Product Manager (John) + Claude Code
**状态**: ✅ 已完成，等待开发启动

---

## 📋 文档元数据

| 属性 | 值 |
|------|-----|
| **项目名称** | Canvas监控系统业务逻辑完成 |
| **Epic编号** | Epic 1 |
| **Story数量** | 9个 |
| **预估工作量** | 35-49小时（MVP: 20-28小时） |
| **技术栈** | Python 3.12.7, asyncio, SQLite, watchdog |
| **依赖系统** | Canvas Learning System v1.1, 12 AI Agents |

---

## 🎯 执行摘要

### 项目简介

Canvas监控系统的**基础文件监控架构**（Epic 8.17）已完成，但**核心业务功能**（学习分析、数据持久化、报告生成）缺失80%。本PRD定义了完成剩余业务逻辑的开发计划，将现有的"空壳"转变为生产就绪的学习分析平台。

### 关键目标

- ✅ 实现实时Canvas内容解析（响应时间 < 500ms）
- ✅ 基于颜色流转的学习进度分析（红→紫→绿）
- ✅ 双层数据持久化（JSON热数据 + SQLite历史）
- ✅ 学习报告生成（每日/每周/Canvas分析）
- ✅ 与12个AI Agent和艾宾浩斯复习系统集成

### 技术决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **架构方案** | 异步处理（asyncio + ThreadPool） | 保证高性能，不阻塞监控主线程 |
| **存储方案** | JSON热数据 + SQLite冷数据 | 最佳性能 + 长期查询能力 |
| **实时性要求** | 500ms响应（用户感知） | 高性能体验标准 |
| **回调策略** | 异步执行 | 避免阻塞，提升并发能力 |

---

# 第一部分：项目分析与背景

## 1.1 现有项目概览

### 1.1.1 分析来源

- **来源类型**: IDE分析 + 用户提供文档
- **关键文档**:
  - `MONITORING_STATUS.md` - 当前状态诚实评估
  - `MONITORING_SYSTEM_TRUTH.md` - 完整技术真相报告
  - `CLAUDE.md` - Canvas学习系统总览
  - `canvas_progress_tracker/canvas_monitor_engine.py` - 监控引擎代码

### 1.1.2 当前项目状态

**Canvas学习系统（主项目）**：

Canvas Learning System是一个成熟的AI辅助学习平台（v1.1），基于费曼学习法，通过12个专业化Sub-agent协作完成深度学习循环。

- ✅ **开发状态**: Epic 1-5完成（100%）
- ✅ **测试覆盖**: 420/420测试通过
- ✅ **代码规模**: ~150KB Python代码
- ✅ **核心架构**: 3层Python架构（canvas_utils.py）
  - Layer 1: CanvasJSONOperator（底层JSON操作）
  - Layer 2: CanvasBusinessLogic（业务逻辑层）
  - Layer 3: CanvasOrchestrator（高级API）
- ✅ **生产状态**: 已部署，正常使用中

**监控系统组件（本项目焦点）**：

- **开发状态**: Epic 8.17部分完成（20%）
- **已有功能**:
  - ✅ 文件系统监控（watchdog库集成）
  - ✅ 防抖机制（DebounceManager，500ms延迟）
  - ✅ Canvas变更检测方法（`_detect_canvas_changes()`已实现但未调用）
  - ✅ 回调系统框架（callback列表存在但为空）
  - ✅ 性能监控框架（CPU/内存追踪）

- **缺失功能**（80%）:
  - ❌ Canvas内容解析未连接（方法存在但不调用）
  - ❌ 学习分析逻辑（颜色流转识别、理解度计算）
  - ❌ 数据持久化层（无JSON/SQLite存储实现）
  - ❌ 报告生成器（无学习报告功能）
  - ❌ 系统集成（未与12 Agent/艾宾浩斯系统连接）

### 1.1.3 技术债务与已知问题

**根据`MONITORING_SYSTEM_TRUTH.md`的诚实评估**：

1. **架构空壳问题**:
   - 回调机制存在但回调列表为空
   - `_detect_canvas_changes()`完整实现但从未被调用
   - 数据模型定义完备但无业务逻辑使用

2. **文档与代码不同步**:
   - `MONITORING_SYSTEM_GUIDE.md`承诺了未实现的功能
   - 用户期望与实际能力存在80%差距

3. **性能未验证**:
   - 虽有性能监控框架，但无实际业务负载测试
   - Canvas解析延迟（目标150ms）未验证

---

## 1.2 可用文档分析

**✅ 充足的技术文档**：

| 文档类型 | 状态 | 文件路径 |
|---------|------|---------|
| 技术栈文档 | ✅ 详尽 | `CLAUDE.md` |
| 源代码架构 | ✅ 清晰 | `canvas_utils.py` (3层架构) |
| API文档 | ✅ 完整 | Agent调用协议已记录 |
| 编码规范 | ✅ 明确 | Python 3.9+, UTF-8要求 |
| 技术债务评估 | ✅ 诚实 | `MONITORING_SYSTEM_TRUTH.md` |
| Canvas文件格式 | ✅ 规范 | JSON schema已记录 |
| 测试策略 | ✅ 成熟 | pytest框架，420个测试 |

**结论**: 无需运行document-project任务，现有文档充足。

---

## 1.3 增强范围定义

### 1.3.1 增强类型

- ☑ **新功能添加**（完成未完成的功能）
- ☑ **与现有系统集成**（连接12个AI Agent）
- ☑ **性能/可扩展性改进**（高效Canvas解析，异步处理）

### 1.3.2 增强描述

完成Canvas文件监控系统的业务逻辑层，将当前的文件监视器外壳转变为功能性学习分析平台，能够：

1. **实时解析Canvas内容**：读取JSON结构，提取节点/边/颜色信息
2. **追踪学习进度**：识别颜色转换（红→紫→绿），计算理解提升率
3. **持久化学习历史**：双层存储（JSON热数据实时写入 + SQLite历史批量同步）
4. **生成智能报告**：每日/每周学习总结，Canvas深度分析
5. **无缝集成**：与现有12-agent Canvas学习系统和艾宾浩斯复习系统集成

### 1.3.3 影响评估

- ☑ **中等影响**（部分现有代码修改）

**理由**：
- 核心监控引擎已存在，新业务逻辑作为模块化组件添加
- 需要修改`DebounceManager`连接解析逻辑
- `canvas_utils.py`可能需要回调注册点
- ✅ 不破坏现有Canvas学习工作流（420测试必须继续通过）

---

## 1.4 目标和背景

### 1.4.1 项目目标

1. **实现自动学习活动追踪**
   - 无需手动干预，后台实时记录所有Canvas操作
   - 检测延迟 < 600ms（包含500ms防抖）

2. **提供量化学习洞察**
   - 学习时长统计（精确到分钟）
   - 概念掌握度（红/紫/绿节点分布）
   - 理解提升率（正向颜色流转占比）

3. **生成智能复习建议**
   - 基于艾宾浩斯遗忘曲线
   - 识别薄弱知识点（停留在红色 > 3天）
   - 推荐复习时间表（1天、2天、4天...）

4. **创建数据基础**
   - 为未来ML驱动的学习优化准备数据集
   - 支持长期学习趋势分析（90天历史）

5. **保持高性能**
   - CPU使用率 ≤ 5%（平均）
   - 内存占用 ≤ 100MB
   - 不影响Obsidian的Canvas编辑流畅度

### 1.4.2 背景与动机

**问题陈述**：

Canvas学习系统成功实现了费曼学习法（Epic 1-5，100%完成），但监控组件（Epic 8.17）发现仅完成基础设施（20%），无业务逻辑。用户期望的功能（学习时间追踪、概念掌握分析、智能复习调度）在`MONITORING_SYSTEM_GUIDE.md`中有文档说明，但代码中从未实现。

**业务影响**：

1. **功能承诺未兑现**：文档与现实的80%差距导致用户困惑
2. **数据价值未释放**：虽能检测文件变更，但无法提供有意义的学习洞察
3. **系统割裂**：监控系统孤立存在，未与12 Agent和复习系统集成
4. **错失优化机会**：缺少数据基础，无法进行学习模式分析和个性化推荐

**解决方案价值**：

- ✅ **兑现承诺**：完成文档中承诺的所有监控功能
- ✅ **数据驱动**：提供量化的学习洞察，帮助用户优化学习策略
- ✅ **系统整合**：打通监控与Agent/复习系统，形成完整学习闭环
- ✅ **未来就绪**：为ML优化和个性化推荐打下数据基础

---

## 1.5 变更日志

| 变更内容 | 日期 | 版本 | 描述 | 作者 |
|---------|------|------|------|------|
| 初始PRD创建 | 2025-01-15 | v1.0 | 基于用户技术决策创建完整PRD | PM Agent |
| 技术决策确认 | 2025-01-15 | v2.0 | 确认异步架构+混合存储+500ms响应 | User + PM Agent |

---

# 第二部分：功能需求

## 2.1 功能性需求 (Functional Requirements)

### FR1: 实时Canvas文件监控

**需求描述**：系统应自动检测`笔记库/`目录下所有`.canvas`文件的创建、修改、删除事件。

**详细规格**：

- **监控范围**：
  - 递归监控所有子目录
  - 仅监控`.canvas`扩展名文件
  - 自动处理文件移动和重命名事件

- **检测延迟**：
  - 文件系统事件触发 < 50ms（OS级别）
  - 防抖延迟：500ms（可配置）
  - 总检测延迟 ≤ 600ms

- **事件类型**：
  - CREATE：新Canvas文件创建
  - UPDATE：Canvas文件内容修改
  - DELETE：Canvas文件删除
  - MOVE：Canvas文件移动或重命名

**验收标准**：

- ✅ 在Obsidian中保存Canvas后600ms内触发处理
- ✅ 500ms内的重复修改仅触发1次处理（防抖生效）
- ✅ 支持同时监控至少10个Canvas文件
- ✅ 监控进程崩溃不影响Canvas文件完整性

---

### FR2: Canvas内容解析与变更检测

**需求描述**：系统应解析Canvas JSON文件结构，提取节点和边的详细信息，并检测细粒度变更。

**解析内容**：

- **节点信息**：
  - `id`：节点唯一标识符
  - `type`：节点类型（text/file/link/group）
  - `text`：节点文本内容
  - `color`：节点颜色代码（"1"=红/"2"=绿/"3"=紫/"5"=蓝/"6"=黄）
  - `x`, `y`：节点位置坐标
  - `width`, `height`：节点尺寸

- **边信息**：
  - `id`：边唯一标识符
  - `fromNode`, `toNode`：连接的节点ID
  - `fromSide`, `toSide`：连接点位置

**变更检测**：

| 变更类型 | 检测内容 | 用途 |
|---------|---------|------|
| 节点新增 | 新节点ID出现 | 追踪知识体系扩展 |
| 节点删除 | 节点ID消失 | 识别知识点移除 |
| 颜色变更 | color字段变化 | **核心**：学习进度追踪（红→紫→绿） |
| 位置变更 | x/y坐标变化 | 布局调整追踪 |
| 内容更新 | text字段变化 | 理解深化追踪 |

**性能要求**：

- Canvas解析时间：
  - 50节点：< 150ms
  - 100节点：< 300ms
  - 200节点：< 600ms

**验收标准**：

- ✅ 成功解析符合Obsidian Canvas格式的JSON文件
- ✅ 正确识别所有5种颜色代码
- ✅ 检测到节点新增、删除、颜色变更、位置变更
- ✅ 解析失败时记录错误但不崩溃监控进程
- ✅ 性能达标（50节点 < 150ms）

---

### FR3: 学习进度分析

**需求描述**：系统应基于颜色流转自动识别学习事件，并统计学习指标。

**学习事件识别**：

| 事件类型 | 颜色流转 | 含义 | 优先级 |
|---------|---------|------|-------|
| `understanding_improving` | 红(1) → 紫(3) | 从完全不懂到似懂非懂 | 🟡 正常进步 |
| `understanding_mastered` | 紫(3) → 绿(2) | 从似懂非懂到完全掌握 | 🟢 掌握成功 |
| `breakthrough` | 红(1) → 绿(2) | 跨越式突破 | 🌟 重大进步 |
| `understanding_regressed` | 绿(2) → 紫(3)<br>紫(3) → 红(1) | 理解退步 | 🔴 需要复习 |
| `knowledge_node_added` | 无颜色 → 红(1) | 新增问题节点 | 📝 知识扩展 |
| `personal_understanding_updated` | 黄(6)节点内容变化 | 个人理解填写/优化 | 💭 输出训练 |

**学习指标统计**：

1. **学习时长**：
   - 计算方式：首次Canvas打开到最后修改的时间跨度
   - 单位：分钟
   - 聚合：每Canvas、每日、每周

2. **颜色分布**：
   - 统计红/紫/绿/蓝/黄节点的数量和占比
   - 趋势：追踪颜色分布随时间的变化

3. **理解提升率**：
   - 公式：`(正向流转次数) / (总流转次数) × 100%`
   - 正向流转：红→紫、紫→绿、红→绿
   - 目标值：> 70%表示学习效果良好

4. **Agent使用频率**：
   - 检测蓝色节点（AI生成解释）的创建
   - 从节点文本推断使用的Agent（如：🗣️ = oral-explanation）
   - 统计Top 3最常用Agent

**验收标准**：

- ✅ 正确识别6种学习事件类型
- ✅ 学习时长统计误差 < 5分钟
- ✅ 颜色分布统计准确（与手动计数一致）
- ✅ 理解提升率计算公式正确
- ✅ Agent识别准确率 > 90%（基于emoji和关键词）

---

### FR4: 双层数据持久化

**需求描述**：系统应实现热数据（JSON）和冷数据（SQLite）的双层存储架构。

#### 4.1 热数据层（JSON文件）

**目的**：实时记录最近24小时的学习活动，提供快速写入和查询。

**文件结构**：

```
.learning_sessions/
├── session_2025-01-15.json      # 当日会话
├── session_2025-01-14.json      # 昨日会话（待同步）
├── hot_stats.json                # 实时统计缓存
└── metadata.json                 # 会话元数据
```

**JSON Schema**：

```json
{
  "session_id": "session_2025-01-15",
  "start_time": "2025-01-15T08:30:00",
  "last_update": "2025-01-15T23:45:00",
  "events": [
    {
      "event_id": "evt_1705300523000",
      "timestamp": "2025-01-15T10:15:23",
      "canvas_id": "离散数学.canvas",
      "event_type": "color_changed",
      "node_id": "node_abc123",
      "details": {
        "old_color": "1",
        "new_color": "3",
        "analysis": {
          "progress_type": "understanding_improving",
          "score_change": "+20"
        }
      }
    }
  ],
  "stats": {
    "total_changes": 45,
    "learning_duration_seconds": 3600,
    "color_distribution": {
      "red": 5,
      "purple": 8,
      "green": 12,
      "blue": 3,
      "yellow": 7
    },
    "understanding_rate": 0.73
  }
}
```

**性能要求**：

- JSON写入延迟：< 20ms（单次写入，SSD环境）
- 写入失败重试：最多3次，间隔100ms
- 文件大小限制：单文件 < 10MB（约10000条事件）

**验收标准**：

- ✅ 每天自动创建新session文件
- ✅ 每次Canvas变更后立即写入JSON
- ✅ JSON格式符合预定义Schema
- ✅ 写入失败时重试并记录错误日志
- ✅ 支持查询当日统计数据（< 100ms）

#### 4.2 冷数据层（SQLite数据库）

**目的**：长期存储学习历史，提供强大的查询和分析能力。

**数据库Schema**：

```sql
-- 表1: Canvas变更记录（所有细粒度变更）
CREATE TABLE canvas_changes (
    change_id TEXT PRIMARY KEY,
    canvas_id TEXT NOT NULL,
    change_type TEXT NOT NULL,  -- CREATE/UPDATE/DELETE
    node_id TEXT,
    node_type TEXT,
    old_content TEXT,           -- JSON格式
    new_content TEXT,           -- JSON格式
    timestamp DATETIME NOT NULL,
    file_path TEXT,
    INDEX idx_canvas_timestamp (canvas_id, timestamp),
    INDEX idx_change_type (change_type)
);

-- 表2: 学习事件（高级语义事件）
CREATE TABLE learning_events (
    event_id TEXT PRIMARY KEY,
    canvas_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- understanding_improving/mastered/breakthrough
    node_id TEXT,
    details TEXT,              -- JSON格式详细信息
    timestamp DATETIME NOT NULL,
    INDEX idx_canvas_event (canvas_id, timestamp)
);

-- 表3: 颜色流转记录
CREATE TABLE color_transitions (
    transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canvas_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    from_color TEXT,           -- "1"=红/"3"=紫/"2"=绿
    to_color TEXT,
    transition_type TEXT,      -- improving/mastered/regressed
    timestamp DATETIME NOT NULL,
    INDEX idx_node_transitions (node_id, timestamp)
);

-- 表4: 每日统计摘要
CREATE TABLE daily_stats (
    stat_date DATE PRIMARY KEY,
    total_canvas_files INTEGER,
    total_changes INTEGER,
    total_learning_seconds INTEGER,
    nodes_red INTEGER,
    nodes_purple INTEGER,
    nodes_green INTEGER,
    understanding_rate REAL,   -- 理解提升率
    created_at DATETIME NOT NULL
);
```

**性能要求**：

- 批量插入：1000条记录 < 500ms
- 查询性能：按日期范围查询 < 100ms
- 数据库大小：90天数据 < 500MB

**数据同步策略**：

- 同步频率：每小时一次（可配置）
- 同步流程：
  1. 读取昨天的JSON文件
  2. 批量插入到SQLite
  3. 验证插入成功（记录数匹配）
  4. 删除JSON文件
- 数据保留：
  - SQLite保留90天
  - 90天后归档到`.learning_data/archive/YYYY-MM.tar.gz`

**验收标准**：

- ✅ 首次启动时自动创建数据库和表
- ✅ 支持4种数据表的插入和查询
- ✅ 批量插入性能达标（1000条 < 500ms）
- ✅ 查询性能达标（按日期范围 < 100ms）
- ✅ 数据完整性约束生效（主键、索引）
- ✅ 每小时自动同步热数据到冷数据
- ✅ 90天后自动归档

---

### FR5: 学习报告生成

**需求描述**：系统应支持生成3种类型的学习报告，格式为Markdown文本。

#### 5.1 每日学习报告

**内容结构**：

```markdown
# 学习报告 - 2025年01月15日

## 📊 学习概览

- **学习时长**: 120分钟
- **操作Canvas数**: 3个
- **节点变更**: 45次

## 🎯 理解进度

- 🔴 红色（不理解）: 5个
- 🟣 紫色（似懂非懂）: 8个
- 🟢 绿色（完全掌握）: 12个

**理解提升率**: 73.3%

## 🚀 学习突破

- **10:15** - 离散数学.canvas: "逆否命题" 红→紫（理解提升）
- **14:30** - 线性代数.canvas: "特征向量" 紫→绿（完全掌握）✨
- **16:45** - 概率论.canvas: "贝叶斯定理" 红→绿（突破性进步）🌟

## 🤖 Agent使用分析

1. **oral-explanation** - 使用8次
2. **clarification-path** - 使用5次
3. **memory-anchor** - 使用3次

## 💡 复习建议

**需要复习的知识点**（停留在红色 > 3天）：
- 离散数学.canvas: "命题逻辑完备性"（已停留5天）
- 线性代数.canvas: "矩阵秩的几何意义"（已停留4天）

**建议复习时间**: 明天上午10:00
```

**生成时间要求**：< 2秒

**验收标准**：

- ✅ 报告包含所有6个部分
- ✅ 数据准确（与数据库一致）
- ✅ 突破事件按时间排序
- ✅ Agent使用频率Top 3准确
- ✅ 复习建议基于实际停留时间

#### 5.2 每周学习总结

**内容结构**：

```markdown
# 每周学习总结 - 2025年第3周

## 📈 学习趋势

**每日学习时长（分钟）**：
```
周一: ████████████ 120
周二: ██████████ 100
周三: ██████████████ 140
周四: ████████ 80
周五: ███████████████ 150
周六: ██████████████████ 180
周日: ██████████ 100
```

**总学习时长**: 870分钟（14.5小时）
**平均每日**: 124分钟

## 🎯 知识掌握曲线

**绿色节点占比趋势**：
```
周一: 35% ████████
周二: 40% █████████
周三: 45% ██████████
周四: 48% ███████████
周五: 52% ████████████
周六: 58% █████████████
周日: 62% ██████████████
```

**本周进步**: +27%（从35%到62%）🎉

## 🔍 薄弱知识点识别

**停留在红色 > 3天的节点**：

1. **离散数学.canvas**: "命题逻辑完备性"（停留7天）
   - 建议：使用clarification-path深度澄清

2. **线性代数.canvas**: "矩阵秩的几何意义"（停留5天）
   - 建议：使用memory-anchor生成类比记忆

## 🤖 Agent使用偏好

- **oral-explanation**: 45次（最爱口语化解释）
- **clarification-path**: 32次（喜欢系统化澄清）
- **memory-anchor**: 18次（需要记忆辅助）
```

**生成时间要求**：< 5秒

**验收标准**：

- ✅ 每日学习时长折线图（文本表示）
- ✅ 绿色节点占比趋势准确
- ✅ 薄弱知识点识别逻辑正确（> 3天红色）
- ✅ Agent使用频率统计准确

#### 5.3 Canvas分析报告

**内容结构**：

```markdown
# Canvas深度分析 - 离散数学.canvas

## 📅 学习历程时间线

**2025-01-10 09:00** - Canvas创建
- 初始节点：15个红色问题节点

**2025-01-10 10:30** - 首次理解突破
- "命题逻辑基础" 红→紫

**2025-01-11 14:00** - 第一个完全掌握
- "命题连接词" 紫→绿✨

**2025-01-15 16:00** - 当前状态
- 总节点：35个
- 绿色：12个（34%）
- 紫色：8个（23%）
- 红色：5个（14%）
- 黄色：7个（20%，个人理解）
- 蓝色：3个（9%，AI解释）

## 🔥 节点颜色变化热力图

```
节点                    Day1  Day2  Day3  Day4  Day5
命题逻辑基础           🔴    🟣    🟣    🟢    🟢
命题连接词             🔴    🟣    🟢    🟢    🟢
真值表                 🔴    🔴    🟣    🟣    🟢
逆否命题               🔴    🔴    🔴    🟣    🟣
命题逻辑完备性         🔴    🔴    🔴    🔴    🔴 ⚠️
```

## 📊 学习效率分析

- **平均每节点学习时长**: 18分钟
- **最快掌握**: "命题连接词"（30分钟）
- **最慢掌握**: "真值表"（3天累计120分钟）

## 💡 改进建议

1. **"命题逻辑完备性"停滞5天**
   - 建议使用basic-decomposition拆解
   - 或寻求更基础的学习资源

2. **Agent使用不均衡**
   - oral-explanation使用8次
   - 建议尝试comparison-table对比易混淆概念
```

**生成时间要求**：< 3秒

**验收标准**：

- ✅ 时间线包含关键事件（创建、首次突破、首次掌握）
- ✅ 颜色热力图准确反映节点变化
- ✅ 学习效率统计正确
- ✅ 改进建议基于实际数据

---

### FR6: 与现有系统集成

**需求描述**：系统应通过回调机制与12个AI Agent和艾宾浩斯复习系统无缝集成。

#### 6.1 与12个AI Agent集成

**集成方式**：观察者模式（监控系统不修改Agent）

**集成内容**：

1. **Agent使用追踪**：
   - 检测蓝色节点（color="5"）的创建
   - 从节点文本推断使用的Agent：
     - 🗣️ 或 "口语化解释" → oral-explanation
     - 🔍 或 "澄清路径" → clarification-path
     - 📊 或 "对比表" → comparison-table
     - ⚓ 或 "记忆锚点" → memory-anchor
     - 🎯 或 "四层次" → four-level-explanation
     - 📝 或 "例题教学" → example-teaching
   - 记录Agent使用事件到数据库

2. **Agent效果分析**：
   - 追踪Agent使用后的颜色变化
   - 例如：使用oral-explanation后，相关红色节点是否在24小时内变为紫色
   - 生成Agent效果报告

**验收标准**：

- ✅ 在监控运行时，调用任意Agent都正常工作
- ✅ Agent使用被正确记录（识别准确率 > 90%）
- ✅ 监控不干扰Agent的正常执行
- ✅ Agent效果分析逻辑正确

#### 6.2 与艾宾浩斯复习系统集成

**集成方式**：事件驱动触发

**触发逻辑**：

```python
if event_type == "understanding_mastered":  # 紫→绿
    schedule_review(
        canvas_id=canvas_id,
        node_id=node_id,
        intervals=[1, 2, 4, 7, 15, 30]  # 天数
    )
```

**复习提醒格式**：

```markdown
## 📚 复习提醒

**知识点**: 离散数学.canvas - "逆否命题"
**上次掌握**: 2025-01-10
**建议复习**: 今天（第4天复习）

**历史复习记录**：
- ✅ 第1天复习（2025-01-11）
- ✅ 第2天复习（2025-01-12）
- ⏭️ 第4天复习（今天）

**复习方法建议**：
1. 回顾原Canvas节点的黄色理解
2. 尝试不看资料重新解释
3. 如果遗忘，使用Agent重新学习
```

**验收标准**：

- ✅ 节点变为绿色时自动触发复习调度
- ✅ 复习提醒在预定时间出现（误差 < 1小时）
- ✅ 复习记录被追踪（完成/未完成）
- ✅ 支持手动标记"已复习"

#### 6.3 与canvas_utils.py兼容性

**兼容性要求**：

- ✅ 不修改`canvas_utils.py`的公共API
- ✅ 监控系统作为独立模块运行
- ✅ 通过回调机制集成，无侵入式修改
- ✅ 现有420个测试继续100%通过

**验收标准**：

- ✅ 运行`pytest tests/ -v`，所有测试通过
- ✅ 监控运行时，canvas_utils.py的所有功能正常
- ✅ 3层架构（CanvasJSONOperator/BusinessLogic/Orchestrator）完整保留

---

## 2.2 非功能性需求 (Non-Functional Requirements)

### NFR1: 性能要求

**响应时间要求**：

| 操作 | 目标时间 | 测量方法 |
|------|---------|---------|
| 文件系统检测 | < 50ms | OS级别，不可控 |
| 防抖等待 | 500ms | 固定延迟 |
| 异步队列传递 | < 10ms | asyncio内存队列 |
| Canvas JSON解析 | < 150ms (50节点)<br>< 300ms (100节点) | 性能测试脚本 |
| 学习分析 | < 50ms | 单次回调执行时间 |
| JSON写入 | < 20ms | 异步文件IO |
| SQLite批量提交 | 后台执行 | 不影响主流程 |
| **总响应时间** | **< 800ms** | 从保存到数据记录完成 |

**用户感知延迟**：编辑Canvas → 保存文件 → 500ms防抖 → 150ms处理 = **650ms**

**并发能力**：

- 支持同时监控 ≥ 10个Canvas文件
- 4个worker线程并发处理
- 异步队列容量：1000条任务

**资源使用限制**：

- CPU使用率：
  - 平均 < 5%
  - 峰值 < 15%（短时间高峰可接受）
- 内存占用：
  - 监控进程 < 100MB
  - 增长率 < 10MB/天（检测内存泄漏）
- 磁盘IO：
  - JSON写入 < 1MB/小时（热数据）
  - SQLite写入 < 10MB/天（冷数据）

**性能测试要求**：

- P50响应时间 < 800ms
- P95响应时间 < 1200ms
- P99响应时间 < 2000ms

**验收标准**：

- ✅ 性能基准测试通过（100次Canvas修改）
- ✅ CPU/内存使用在限制范围内
- ✅ 长期运行测试（72小时）无性能劣化

---

### NFR2: 可靠性要求

**可用性目标**：

- 监控进程正常运行时间 > 99%（排除主动停止）
- 崩溃后30秒内自动重启（通过系统服务管理）

**错误处理**：

1. **回调执行失败**：
   - 捕获异常，记录到错误日志
   - 不影响监控主流程
   - 其他回调继续执行

2. **Canvas解析失败**：
   - 记录JSON格式错误
   - 跳过该文件，继续监控其他文件
   - 提供手动修复提示

3. **数据写入失败**：
   - 自动重试（最多3次）
   - 重试间隔：100ms, 500ms, 2000ms
   - 失败后记录到错误日志，等待下次同步

4. **监控进程崩溃**：
   - 保存未写入的数据到临时文件
   - 记录崩溃堆栈到crash.log
   - 自动重启（通过系统服务）

**超时控制**：

- 单个回调执行超时：2秒
- Canvas解析超时：5秒（超大文件）
- 数据库查询超时：10秒
- 优雅关闭超时：30秒（等待队列处理完成）

**数据完整性**：

- JSON文件原子写入（写入临时文件 → 重命名）
- SQLite事务一致性（批量插入作为单一事务）
- 数据校验（插入后验证记录数）

**验收标准**：

- ✅ 故障注入测试通过（模拟回调异常、文件损坏、数据库锁）
- ✅ 72小时soak测试无崩溃
- ✅ 数据完整性验证（同步前后记录数一致）

---

### NFR3: 可扩展性要求

**模块化设计**：

- 新的分析算法通过回调添加（无需修改核心引擎）
- 新的存储后端通过接口实现（支持PostgreSQL/MongoDB扩展）
- 新的报告类型通过模板添加（无需修改报告生成器）

**配置灵活性**：

- 所有关键参数可配置（防抖延迟、同步间隔、保留天数）
- 配置文件：`.canvas_monitor_config.yaml`
- 支持热加载配置（部分参数无需重启）

**API开放性**：

- 提供REST API（HTTP端点）供外部系统集成
- 提供Python API（回调注册）供自定义扩展
- 预留ML分析接口（未来支持机器学习模型）

**数据格式版本化**：

- JSON schema包含版本号
- SQLite schema支持迁移脚本
- 向后兼容承诺（v2.x可读v1.x数据）

**验收标准**：

- ✅ 成功添加一个自定义回调（无需修改核心代码）
- ✅ 配置文件修改后生效
- ✅ 数据格式升级测试（v1.0 → v2.0迁移）

---

### NFR4: 可用性要求

**易用性目标**：用户无需阅读文档即可启动和使用

**一键启动**：

- Windows批处理：双击`start_monitoring.bat`
- Python脚本：`python start_canvas_monitoring.py`
- 自动环境检查（Python版本、依赖库、目录权限）

**状态可见性**：

- 启动后显示实时状态（监控文件数、CPU/内存使用）
- 斜杠命令：`/monitoring-status`查看详细状态
- HTTP端点：`http://localhost:5678/status`（JSON格式）

**日志与诊断**：

- 日志文件：`logs/monitor.log`（所有级别）
- 错误日志：`logs/errors.log`（仅ERROR）
- 性能日志：`logs/performance.log`（响应时间统计）
- 日志轮转：每个文件最大10MB，保留5个备份

**错误消息可读性**：

- 使用中文错误消息
- 提供解决方案提示
- 示例：
  ```
  ❌ 错误：找不到笔记库目录

  可能原因：
  1. 目录路径配置错误
  2. 目录已被移动或删除

  解决方案：
  1. 检查配置文件：.canvas_monitor_config.yaml
  2. 确认笔记库路径是否正确：C:\Users\ROG\托福\笔记库
  3. 如需帮助，查看文档：docs/troubleshooting.md
  ```

**文档完整性**：

- 用户手册：如何启动、如何使用、常见问题
- 故障排除指南：常见错误和解决方案
- API文档：回调接口规格
- 开发指南：如何添加自定义分析器

**验收标准**：

- ✅ 新用户能在5分钟内启动监控系统
- ✅ 错误消息提供明确的解决方案
- ✅ 文档覆盖所有主要功能
- ✅ 用户满意度 > 4/5

---

### NFR5: 兼容性要求

**平台兼容性**：

- **主要平台**：Windows 10/11（开发和测试重点）
- **次要平台**：macOS, Linux（基础支持）
- Python版本：3.9+（建议3.12.7）

**Obsidian兼容性**：

- Canvas文件格式：兼容当前所有版本（v1.0+）
- 非侵入式监控：不修改Canvas文件格式
- 不干扰Obsidian操作：监控时Obsidian编辑流畅

**依赖库版本**：

| 库名 | 最低版本 | 推荐版本 | 用途 |
|------|---------|---------|------|
| watchdog | 4.0.0 | 最新 | 文件系统监控 |
| psutil | 5.9.0 | 最新 | 性能监控 |
| pytest | 7.0.0 | 最新 | 单元测试 |
| pytest-asyncio | 0.21.0 | 最新 | 异步测试 |

**向后兼容性**：

- 配置文件格式向后兼容（v2.0可读v1.0配置）
- 数据格式向后兼容（v2.0可读v1.0数据）
- API接口向后兼容（弃用但保留旧接口）

**验收标准**：

- ✅ 在Windows 10/11上测试通过
- ✅ 在macOS上基础功能测试通过（可选）
- ✅ 兼容Obsidian最新版本
- ✅ 现有420个测试继续通过

---

## 2.3 兼容性需求 (Compatibility Requirements)

### CR1: API兼容性

**要求**：监控系统应保持现有`canvas_utils.py`的API不变。

**具体承诺**：

- ✅ `CanvasJSONOperator`的所有公共方法保持签名不变
- ✅ `CanvasBusinessLogic`的布局算法不修改
- ✅ `CanvasOrchestrator`的Agent调用接口保持不变
- ✅ 新增的回调接口向后兼容（可选参数）

**如果必须修改**：

- 提供弃用警告（deprecation warning）
- 保留旧接口至少2个版本
- 提供迁移指南

**验收标准**：

- ✅ 运行`pytest tests/test_canvas_utils.py`，所有测试通过
- ✅ API文档更新（标注新增/弃用）

---

### CR2: 数据库Schema兼容性

**要求**：SQLite数据库schema应支持版本升级。

**版本管理**：

- 在数据库中存储schema版本号
- 创建迁移脚本：`migrations/v1_to_v2.sql`
- 启动时自动检测并执行迁移

**迁移策略**：

```sql
-- migrations/v1_to_v2.sql

-- 1. 检查当前版本
SELECT version FROM schema_version;

-- 2. 添加新列（如果需要）
ALTER TABLE canvas_changes ADD COLUMN processing_time_ms INTEGER;

-- 3. 更新版本号
UPDATE schema_version SET version = '2.0', updated_at = datetime('now');
```

**验收标准**：

- ✅ v1.0数据库可自动升级到v2.0
- ✅ 迁移过程不丢失数据
- ✅ 迁移失败时回滚（事务保护）

---

### CR3: UI/UX一致性

**要求**：学习报告的格式应与现有Canvas学习系统的文档风格一致。

**格式规范**：

- Markdown格式（支持GitHub Flavored Markdown）
- 使用emoji保持友好性（📊 📈 🎯 ✨）
- 中文为主，英文为辅
- 表格和图表使用文本ASCII艺术

**错误消息规范**：

- 中文错误消息
- 提供具体的解决方案
- 友好的语气（避免"错误"、"失败"等严厉词汇，使用"无法"、"未找到"）

**命令命名规范**：

- 斜杠命令格式：`/xxx-xxx`（小写，连字符分隔）
- 示例：`/monitoring-status`, `/learning-report`, `/stop-monitoring`
- 与现有命令保持一致性

**验收标准**：

- ✅ 报告格式与现有文档风格一致
- ✅ 错误消息友好且有用
- ✅ 命令命名符合规范

---

### CR4: 系统集成兼容性

**要求**：与12个AI Agent和现有系统的集成应通过标准回调协议。

**Agent集成原则**：

- ✅ 不修改Agent定义文件（`.claude/agents/*.md`）
- ✅ 不修改Agent调用协议
- ✅ 监控系统是观察者，不主动触发Agent

**颜色系统兼容**：

- ✅ 使用现有颜色常量（canvas_utils.py中定义）
- ✅ 颜色代码：1=红, 2=绿, 3=紫, 5=蓝, 6=黄
- ✅ 不引入新的颜色代码

**Canvas文件格式兼容**：

- ✅ 不修改.canvas文件格式
- ✅ 只读取，不写入Canvas文件
- ✅ 兼容Obsidian Canvas JSON schema

**验收标准**：

- ✅ 12个Agent在监控运行时正常工作
- ✅ 颜色系统一致（与canvas_utils.py一致）
- ✅ Canvas文件完整性不受影响

---

# 第三部分：技术约束与集成方案

## 3.1 现有技术栈

### 3.1.1 语言与运行时

- **Python 3.12.7**（已安装并验证）
- **编码要求**：所有Python文件必须声明`# -*- coding: utf-8 -*-`
- **虚拟环境**：建议使用venv或conda隔离依赖

### 3.1.2 核心框架与库

**已安装依赖**：

| 库名 | 版本 | 用途 |
|------|------|------|
| watchdog | 4.0+ | 文件系统监控 |
| psutil | 5.9+ | 系统性能监控 |
| asyncio | 标准库 | 异步处理核心 |
| threading | 标准库 | 防抖管理器 |
| sqlite3 | 标准库 | 冷数据存储 |
| json | 标准库 | 热数据存储和Canvas解析 |
| pytest | 7.0+ | 测试框架 |

### 3.1.3 现有架构

**Canvas Learning System架构**：

```
canvas_utils.py (~150KB)
├── Layer 1: CanvasJSONOperator
│   ├── read_canvas(file_path) -> dict
│   ├── write_canvas(file_path, data) -> bool
│   ├── add_node(data, node) -> str
│   ├── find_node_by_id(data, node_id) -> dict
│   └── add_edge(data, edge) -> str
│
├── Layer 2: CanvasBusinessLogic
│   ├── v1.1布局算法（黄色节点对齐）
│   ├── extract_verification_nodes(data) -> list
│   ├── cluster_questions_by_topic(questions) -> dict
│   └── generate_review_canvas_file(...)
│
└── Layer 3: CanvasOrchestrator
    ├── generate_verification_questions_with_agent(...)
    └── 完整操作工作流
```

**监控系统现有架构**：

```
canvas_progress_tracker/
├── __init__.py
├── canvas_monitor_engine.py
│   ├── CanvasMonitorEngine (核心引擎)
│   ├── DebounceManager (防抖管理器)
│   ├── CanvasFileHandler (文件事件处理器)
│   ├── _detect_canvas_changes() ✅ 已实现但未调用
│   └── callback lists ✅ 存在但为空
│
└── system_integration.py (空文件)
```

**12个AI Agents**：

位置：`.claude/agents/`
- canvas-orchestrator.md
- basic-decomposition.md
- deep-decomposition.md
- oral-explanation.md
- clarification-path.md
- comparison-table.md
- memory-anchor.md
- four-level-explanation.md
- example-teaching.md
- scoring-agent.md
- verification-question-agent.md
- question-decomposition.md

---

## 3.2 集成方案

### 3.2.1 数据库集成策略

#### 热数据层（JSON文件）实现

**目录结构**：

```
.learning_sessions/
├── session_2025-01-15.json      # 当日实时会话
├── session_2025-01-14.json      # 昨日会话（待同步）
├── hot_stats.json                # 实时统计缓存
└── metadata.json                 # 会话元数据
```

**实现类**：

```python
# canvas_progress_tracker/data_stores.py

import json
import asyncio
from pathlib import Path
from datetime import datetime
import threading

class HotDataStore:
    """热数据JSON存储"""

    def __init__(self, base_path: str = ".learning_sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.current_session = self._load_today_session()
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def _load_today_session(self) -> dict:
        """加载或创建今日session"""
        today = datetime.now().strftime("%Y-%m-%d")
        session_file = self.base_path / f"session_{today}.json"

        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "session_id": f"session_{today}",
                "start_time": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat(),
                "events": [],
                "stats": {
                    "total_changes": 0,
                    "learning_duration_seconds": 0,
                    "color_distribution": {}
                }
            }

    async def write_event(self, event: dict) -> None:
        """异步写入事件（10-20ms）"""
        with self._lock:
            self.current_session["events"].append(event)
            self.current_session["last_update"] = datetime.now().isoformat()
            self.current_session["stats"]["total_changes"] += 1

            # 异步写入文件
            await asyncio.to_thread(
                self._write_json,
                self._get_session_path(),
                self.current_session
            )

    def _write_json(self, file_path: Path, data: dict) -> None:
        """原子化JSON写入"""
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            temp_file.replace(file_path)  # 原子操作
        except Exception as e:
            self.logger.error(f"JSON写入失败: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def _get_session_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.base_path / f"session_{today}.json"

    def get_current_stats(self) -> dict:
        """获取当日统计"""
        with self._lock:
            return self.current_session["stats"].copy()
```

#### 冷数据层（SQLite数据库）实现

**实现类**：

```python
# canvas_progress_tracker/data_stores.py (续)

import sqlite3
from typing import List, Dict

class ColdDataStore:
    """冷数据SQLite存储"""

    def __init__(self, db_path: str = ".learning_data/learning_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """初始化数据库schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            # 创建schema_version表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version TEXT PRIMARY KEY,
                    updated_at DATETIME NOT NULL
                )
            """)

            # 创建canvas_changes表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS canvas_changes (
                    change_id TEXT PRIMARY KEY,
                    canvas_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    node_id TEXT,
                    node_type TEXT,
                    old_content TEXT,
                    new_content TEXT,
                    timestamp DATETIME NOT NULL,
                    file_path TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_canvas_timestamp ON canvas_changes(canvas_id, timestamp)")

            # 创建learning_events表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    canvas_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    node_id TEXT,
                    details TEXT,
                    timestamp DATETIME NOT NULL
                )
            """)

            # 创建color_transitions表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS color_transitions (
                    transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canvas_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    from_color TEXT,
                    to_color TEXT,
                    transition_type TEXT,
                    timestamp DATETIME NOT NULL
                )
            """)

            # 创建daily_stats表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    stat_date DATE PRIMARY KEY,
                    total_canvas_files INTEGER,
                    total_changes INTEGER,
                    total_learning_seconds INTEGER,
                    nodes_red INTEGER,
                    nodes_purple INTEGER,
                    nodes_green INTEGER,
                    understanding_rate REAL,
                    created_at DATETIME NOT NULL
                )
            """)

            conn.commit()
        finally:
            conn.close()

    async def batch_commit_from_json(self, json_path: Path) -> int:
        """从JSON文件批量提交到SQLite（后台任务）"""
        with open(json_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        conn = sqlite3.connect(self.db_path)
        records_inserted = 0

        try:
            conn.execute("BEGIN TRANSACTION")

            for event in session_data["events"]:
                # 插入到canvas_changes
                conn.execute("""
                    INSERT OR IGNORE INTO canvas_changes
                    (change_id, canvas_id, change_type, node_id, timestamp, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event["event_id"],
                    event["canvas_id"],
                    event["event_type"],
                    event.get("node_id"),
                    event["timestamp"],
                    event.get("file_path", "")
                ))
                records_inserted += 1

            conn.execute("COMMIT")
            self.logger.info(f"批量提交完成: {records_inserted}条记录")
            return records_inserted

        except Exception as e:
            conn.execute("ROLLBACK")
            self.logger.error(f"批量提交失败: {e}")
            raise
        finally:
            conn.close()
```

#### 数据同步调度器实现

```python
# canvas_progress_tracker/data_stores.py (续)

class DataSyncScheduler:
    """数据同步调度器"""

    def __init__(self, hot_store: HotDataStore, cold_store: ColdDataStore):
        self.hot_store = hot_store
        self.cold_store = cold_store
        self.sync_task = None
        self.logger = logging.getLogger(__name__)

    async def start_sync_loop(self):
        """启动同步循环（每小时）"""
        while True:
            try:
                await asyncio.sleep(3600)  # 1小时
                await self._sync_hot_to_cold()
                await self._cleanup_old_sessions()
            except Exception as e:
                self.logger.error(f"同步循环错误: {e}")

    async def _sync_hot_to_cold(self):
        """将热数据同步到冷数据"""
        yesterday = datetime.now() - timedelta(days=1)
        json_path = self.hot_store.base_path / f"session_{yesterday.strftime('%Y-%m-%d')}.json"

        if json_path.exists():
            try:
                records = await self.cold_store.batch_commit_from_json(json_path)
                self.logger.info(f"同步成功: {records}条记录")

                # 删除JSON文件
                json_path.unlink()
                self.logger.info(f"已删除: {json_path}")

            except Exception as e:
                self.logger.error(f"同步失败，保留JSON文件: {e}")

    async def _cleanup_old_sessions(self):
        """清理90天前的数据"""
        cutoff_date = datetime.now() - timedelta(days=90)
        # TODO: 实现归档逻辑
```

---

### 3.2.2 异步处理架构

#### 异步处理器实现

```python
# canvas_progress_tracker/async_processor.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List
import logging

class AsyncCanvasProcessor:
    """异步Canvas处理器"""

    def __init__(self, monitor_engine, workers: int = 4):
        self.monitor_engine = monitor_engine
        self.processing_queue = asyncio.Queue(maxsize=1000)
        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.processing_task = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """启动异步处理循环"""
        self.is_running = True
        self.processing_task = asyncio.create_task(
            self._async_process_loop(),
            name="canvas_processor"
        )
        self.logger.info(f"异步处理器已启动: {self.executor._max_workers} workers")

    async def stop(self):
        """停止异步处理"""
        self.is_running = False
        if self.processing_task:
            await self.processing_task
        self.executor.shutdown(wait=True)
        self.logger.info("异步处理器已停止")

    async def _async_process_loop(self):
        """异步处理循环"""
        while self.is_running:
            try:
                # 从队列获取待处理的Canvas
                file_path, changes = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )

                # 在线程池中执行Canvas分析
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.monitor_engine._process_canvas_changes,
                    file_path,
                    changes
                )

                self.processing_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"异步处理失败: {e}")

    async def enqueue_processing(self, file_path: str, changes: List):
        """将处理任务放入队列"""
        try:
            await self.processing_queue.put((file_path, changes))
        except asyncio.QueueFull:
            self.logger.warning("处理队列已满，丢弃任务")
```

#### 修改防抖管理器连接异步处理

```python
# canvas_progress_tracker/canvas_monitor_engine.py (修改)

class DebounceManager:
    def __init__(self, delay_ms: int, async_processor: AsyncCanvasProcessor):
        self.delay_ms = delay_ms
        self.async_processor = async_processor
        # ... 其他代码不变

    def _flush_changes(self, file_path: str) -> None:
        """内部方法：处理变更（定时器回调）"""
        changes = self.flush_changes(file_path)
        if changes:
            self.logger.debug(f"防抖处理完成: {file_path}, {len(changes)}个变更")

            # ✅ 新增：将任务放入异步队列
            asyncio.run_coroutine_threadsafe(
                self.async_processor.enqueue_processing(file_path, changes),
                asyncio.get_event_loop()
            )
```

---

### 3.2.3 学习分析器实现

```python
# canvas_progress_tracker/learning_analyzer.py

from dataclasses import dataclass
from datetime import datetime
import logging

class LearningAnalyzer:
    """学习分析器"""

    def __init__(self, hot_store: HotDataStore, cold_store: ColdDataStore):
        self.hot_store = hot_store
        self.cold_store = cold_store
        self.logger = logging.getLogger(__name__)

    def on_canvas_change(self, change: CanvasChange):
        """Canvas变更回调"""
        try:
            # 检测颜色变更
            if self._is_color_change(change):
                self._analyze_color_transition(change)

            # 检测节点新增
            if change.change_type == CanvasChangeType.CREATE:
                self._analyze_new_node(change)

            # 记录到热数据
            asyncio.create_task(self._record_event(change))

        except Exception as e:
            self.logger.error(f"学习分析失败: {e}")

    def _is_color_change(self, change: CanvasChange) -> bool:
        """判断是否为颜色变更"""
        if change.change_type != CanvasChangeType.UPDATE:
            return False

        old_color = change.old_content.get("color") if change.old_content else None
        new_color = change.new_content.get("color") if change.new_content else None

        return old_color != new_color

    def _analyze_color_transition(self, change: CanvasChange):
        """分析颜色转换"""
        old_color = change.old_content.get("color")
        new_color = change.new_content.get("color")

        # 定义颜色流转类型
        transition_map = {
            ("1", "3"): "understanding_improving",   # 红→紫
            ("3", "2"): "understanding_mastered",    # 紫→绿
            ("1", "2"): "breakthrough",              # 红→绿
            ("2", "3"): "understanding_regressed",   # 绿→紫
            ("3", "1"): "understanding_regressed",   # 紫→红
        }

        transition_type = transition_map.get((old_color, new_color))

        if transition_type:
            event = {
                "event_id": f"evt_{int(time.time() * 1000)}",
                "timestamp": datetime.now().isoformat(),
                "canvas_id": change.canvas_id,
                "event_type": "color_transition",
                "node_id": change.node_id,
                "details": {
                    "old_color": old_color,
                    "new_color": new_color,
                    "transition_type": transition_type
                }
            }

            self.logger.info(
                f"学习进步: {change.canvas_id}/{change.node_id} "
                f"{old_color}→{new_color} ({transition_type})"
            )

            # 异步写入（将在下一个方法中实现）
            asyncio.create_task(self.hot_store.write_event(event))

    def _analyze_new_node(self, change: CanvasChange):
        """分析新节点创建"""
        color = change.new_content.get("color")

        if color == "1":  # 红色问题节点
            event = {
                "event_id": f"evt_{int(time.time() * 1000)}",
                "timestamp": datetime.now().isoformat(),
                "canvas_id": change.canvas_id,
                "event_type": "knowledge_node_added",
                "node_id": change.node_id,
                "details": {"color": color}
            }
            asyncio.create_task(self.hot_store.write_event(event))

    async def _record_event(self, change: CanvasChange):
        """记录事件到热数据"""
        event = {
            "event_id": change.change_id,
            "timestamp": change.timestamp.isoformat(),
            "canvas_id": change.canvas_id,
            "event_type": change.change_type.value,
            "node_id": change.node_id,
            "details": {
                "old_content": change.old_content,
                "new_content": change.new_content
            }
        }
        await self.hot_store.write_event(event)
```

---

## 3.3 部署与运维

### 3.3.1 启动脚本

**Windows批处理（增强版）**：

```batch
@echo off
REM start_monitoring.bat

echo ========================================
echo Canvas监控系统启动脚本 v2.0
echo ========================================
echo.

REM 1. 环境检查
echo [1/4] 检查环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python！请安装Python 3.9+
    pause
    exit /b 1
)

REM 2. 创建必要目录
echo [2/4] 创建数据目录...
if not exist ".learning_sessions" mkdir .learning_sessions
if not exist ".learning_data" mkdir .learning_data
if not exist "logs" mkdir logs

REM 3. 启动监控服务
echo [3/4] 启动监控服务...
start /B python start_canvas_monitoring_v2.py

REM 4. 等待并验证启动
echo [4/4] 验证启动状态...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 监控系统已启动！
echo 使用 /monitoring-status 查看状态
echo 使用 /stop-monitoring 停止监控
echo ========================================
pause
```

**Python启动脚本（完整版）**：

```python
# start_canvas_monitoring_v2.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from canvas_progress_tracker import CanvasMonitorEngine
from canvas_progress_tracker.async_processor import AsyncCanvasProcessor
from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore, DataSyncScheduler
from canvas_progress_tracker.learning_analyzer import LearningAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """启动监控系统主函数"""

    print("🚀 启动Canvas监控系统 v2.0...")

    try:
        # 1. 初始化数据存储
        logger.info("初始化数据存储...")
        hot_store = HotDataStore(".learning_sessions")
        cold_store = ColdDataStore(".learning_data/learning_history.db")
        sync_scheduler = DataSyncScheduler(hot_store, cold_store)

        # 2. 初始化监控引擎
        logger.info("初始化监控引擎...")
        monitor = CanvasMonitorEngine("./笔记库")

        # 3. 初始化异步处理器
        logger.info("初始化异步处理器...")
        processor = AsyncCanvasProcessor(monitor, workers=4)

        # 4. 初始化学习分析器
        logger.info("初始化学习分析器...")
        analyzer = LearningAnalyzer(hot_store, cold_store)
        monitor.add_change_callback(analyzer.on_canvas_change)

        # 5. 启动所有组件
        logger.info("启动监控组件...")
        monitor.start_monitoring()
        await processor.start()
        asyncio.create_task(sync_scheduler.start_sync_loop())

        print("✅ 监控系统运行中...")
        print("📊 实时状态: http://localhost:5678/status")
        print("📝 日志文件: logs/monitor.log")
        print("⏹️  停止监控: Ctrl+C 或使用 /stop-monitoring")

        # 6. 保持运行
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n⏹️ 正在停止监控系统...")
            await processor.stop()
            monitor.stop_monitoring()
            print("✅ 监控系统已停止")

    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        print(f"❌ 启动失败: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

---

## 3.4 配置管理

**配置文件**：

```yaml
# .canvas_monitor_config.yaml

monitoring:
  base_path: "./笔记库"
  debounce_delay_ms: 500
  max_cpu_percent: 5.0
  max_memory_mb: 100
  recursive: true

async_processing:
  worker_count: 4
  queue_max_size: 1000
  callback_timeout_seconds: 2

data_storage:
  hot_data_path: ".learning_sessions"
  cold_data_path: ".learning_data/learning_history.db"
  sync_interval_hours: 1
  retention_days: 90

performance:
  response_time_target_ms: 500
  canvas_parse_timeout_ms: 300
  enable_performance_logging: true

logging:
  level: "INFO"
  log_dir: "logs"
  max_file_size_mb: 10
  backup_count: 5
```

---

# 第四部分：Epic和Story结构

## 4.1 Epic结构方法

### Epic结构决策：单一综合Epic

**理由**：

- ✅ **功能内聚性高**：所有Story都围绕"完成监控系统业务逻辑"
- ✅ **技术栈统一**：全部使用Python + asyncio + SQLite
- ✅ **交付目标明确**：从空壳到可用的监控系统
- ✅ **Brownfield特性**：对单一现有组件的增强

**不采用多Epic的原因**：

- 拆分会导致Story之间的跨Epic依赖复杂
- 每个Epic无法独立交付价值
- 增加管理开销而无实际收益

---

## 4.2 Epic 1: Canvas监控系统业务逻辑完成

**Epic目标**：

将现有Canvas文件监控基础设施（20%完成）转变为功能完整的学习分析平台（100%完成），实现：
- 实时Canvas内容解析和变更检测
- 基于颜色流转的学习进度分析
- 双层数据持久化（JSON + SQLite）
- 学习报告生成和智能复习建议
- 与现有12-Agent系统的无缝集成

**集成要求**：

1. 向后兼容性：现有`canvas_utils.py`的API不变
2. 非侵入式：监控作为独立进程，不修改Obsidian
3. 可观测性：提供实时状态查询和性能监控
4. 优雅降级：性能压力大时自动降低监控频率

---

## 4.3 Story清单

### Story 1.1：连接Canvas内容解析逻辑

**作为**：监控系统开发者
**我想要**：连接现有的`_detect_canvas_changes()`方法到防抖管理器
**以便**：在文件变更后自动触发Canvas内容解析

**技术描述**：
- 修改`DebounceManager._flush_changes()`
- 实现`CanvasMonitorEngine._process_canvas_changes()`
- 调用现有的`_detect_canvas_changes()`
- 触发所有注册的`change_callbacks`

**Acceptance Criteria**：
1. ✅ Canvas修改后500ms触发内容解析
2. ✅ 成功检测节点级别变更
3. ✅ 所有回调被调用
4. ✅ 异常不导致崩溃
5. ✅ 解析耗时记录到性能统计
6. ✅ 单元测试覆盖 > 95%

**Integration Verification**：
- IV1: 现有测试继续通过
- IV2: 防抖机制未受影响
- IV3: CPU < 5%, 内存增长 < 10MB

**工作量估算**：3-5小时

---

### Story 1.2：实现热数据JSON存储

**作为**：监控系统用户
**我想要**：系统实时记录学习活动到JSON文件
**以便**：监控进程崩溃时不丢失今天的数据

**技术描述**：
- 创建`data_stores.py`模块
- 实现`HotDataStore`类
- 实现回调函数`hot_data_callback()`
- 注册到监控引擎

**Acceptance Criteria**：
1. ✅ 每天自动创建新session文件
2. ✅ 事件立即追加到当日文件
3. ✅ JSON写入 < 20ms
4. ✅ 符合预定义Schema
5. ✅ 写入失败自动重试（最多3次）
6. ✅ 支持查询当日统计

**Integration Verification**：
- IV1: 不影响监控实时性（< 600ms）
- IV2: 文件锁不冲突（并发测试）
- IV3: Obsidian编辑无卡顿

**工作量估算**：2-3小时

---

### Story 1.3：实现学习分析回调

**作为**：学习者
**我想要**：系统自动识别学习进步（红→紫→绿）
**以便**：量化地看到理解提升

**技术描述**：
- 创建`learning_analyzer.py`模块
- 实现`LearningAnalyzer`类
- 实现颜色流转分析
- 计算学习指标

**Acceptance Criteria**：
1. ✅ 正确识别4种颜色流转类型
2. ✅ 每种流转类型写入不同事件
3. ✅ 实时更新学习统计
4. ✅ 分析耗时 < 50ms
5. ✅ 支持批量分析
6. ✅ 边缘情况处理

**Integration Verification**：
- IV1: 与现有颜色系统兼容
- IV2: 不干扰Agent操作
- IV3: 多Canvas并发分析准确

**工作量估算**：4-6小时

---

### Story 1.4：实现异步处理架构

**作为**：系统架构师
**我想要**：将Canvas解析放入异步处理管道
**以便**：保证监控主线程不被阻塞

**技术描述**：
- 创建`async_processor.py`模块
- 实现`AsyncCanvasProcessor`类
- 修改`DebounceManager`连接异步队列
- 重构`_process_canvas_changes()`在worker线程执行

**Acceptance Criteria**：
1. ✅ 防抖后立即返回（不等待处理）
2. ✅ 4个worker线程并发处理
3. ✅ 同一Canvas的变更按顺序处理
4. ✅ 回调超时控制（2秒）
5. ✅ 队列容量限制（1000）
6. ✅ 优雅关闭（等待最多30秒）

**Performance**：
- 队列延迟 < 10ms
- Canvas解析 < 150ms
- 总响应 < 800ms

**Integration Verification**：
- IV1: 主线程CPU < 2%
- IV2: 现有测试100%通过
- IV3: 异常不影响监控稳定性

**工作量估算**：6-8小时

---

### Story 1.5：实现冷数据SQLite存储

**作为**：数据分析师
**我想要**：系统将学习历史存储到SQLite
**以便**：查询和分析长期学习趋势

**技术描述**：
- 在`data_stores.py`实现`ColdDataStore`类
- 创建SQLite schema（4个表）
- 实现批量数据导入
- 实现查询接口

**Acceptance Criteria**：
1. ✅ 首次启动自动创建数据库
2. ✅ 支持4种表的插入和查询
3. ✅ 批量插入：1000条 < 500ms
4. ✅ 查询性能：< 100ms
5. ✅ 数据完整性约束
6. ✅ 数据库路径可配置
7. ✅ Schema版本升级机制

**Integration Verification**：
- IV1: 不影响热数据写入（< 20ms）
- IV2: 数据一致性（JSON vs SQLite）
- IV3: 并发访问安全

**工作量估算**：4-5小时

---

### Story 1.6：实现数据同步调度器

**作为**：系统运维人员
**我想要**：系统自动同步热数据到冷数据
**以便**：节省磁盘空间并提供长期查询

**技术描述**：
- 在`data_stores.py`实现`DataSyncScheduler`类
- 实现定时任务（每小时）
- 实现数据迁移逻辑（JSON → SQLite → 删除）
- 实现数据归档（90天后压缩）

**Acceptance Criteria**：
1. ✅ 每小时自动触发同步
2. ✅ 同步流程完整（读取→插入→验证→删除）
3. ✅ 错误处理（损坏/失败/崩溃）
4. ✅ 数据归档（90天后压缩）
5. ✅ 监控和可观测性

**Integration Verification**：
- IV1: 同步期间不影响监控
- IV2: 数据完整性跨存储层
- IV3: 磁盘空间管理

**工作量估算**：3-4小时

---

### Story 1.7：实现学习报告生成

**作为**：学习者
**我想要**：系统生成每日/每周学习报告
**以便**：回顾进度并发现需要复习的知识点

**技术描述**：
- 创建`report_generator.py`模块
- 实现`LearningReportGenerator`类
- 支持3种报告类型（每日/每周/Canvas分析）
- Markdown格式
- 集成到`/learning-report`命令

**Acceptance Criteria**：
1. ✅ 每日报告包含6个部分
2. ✅ 每周报告包含趋势图和热力图
3. ✅ Canvas分析报告包含时间线和效率分析
4. ✅ 生成时间 < 2秒（每日）、< 5秒（每周）
5. ✅ 报告保存到`.learning_reports/`
6. ✅ 支持日期范围参数

**Integration Verification**：
- IV1: 与斜杠命令兼容
- IV2: 报告数据准确性
- IV3: 大数据量性能（30天 < 5秒）

**工作量估算**：4-6小时

---

### Story 1.8：系统集成与性能优化

**作为**：产品负责人
**我想要**：监控系统完全集成并达到性能目标
**以便**：交付生产就绪的完整产品

**技术描述**：
- 集成测试套件（端到端）
- 性能基准测试和优化
- 与12个AI Agent集成验证
- 与艾宾浩斯复习系统集成
- 生产环境配置和文档

**Acceptance Criteria**：
1. ✅ 端到端集成测试通过
2. ✅ 性能目标达成（P50 < 800ms, P95 < 1200ms）
3. ✅ 12个AI Agent集成验证
4. ✅ 艾宾浩斯复习集成
5. ✅ 生产就绪检查（启动脚本、健康检查、日志）
6. ✅ 文档完成（用户手册、故障排除、API文档）

**Integration Verification**：
- IV1: 现有系统零破坏（420测试通过）
- IV2: 真实用户场景测试（UAT）
- IV3: 长期稳定性（72小时soak测试）

**工作量估算**：6-8小时

---

### Story 1.9：监控仪表板与运维工具

**作为**：系统管理员
**我想要**：实时查看监控系统状态
**以便**：快速诊断问题和优化配置

**技术描述**：
- 实现HTTP服务器（端口5678）
- 提供REST API端点（/health, /status, /stats, /sync, /stop）
- 增强`/monitoring-status`斜杠命令

**Acceptance Criteria**：
1. ✅ 健康检查端点（< 50ms）
2. ✅ 状态端点（< 100ms）
3. ✅ 统计端点（< 200ms）
4. ✅ 管理端点（手动同步、优雅停止）
5. ✅ 斜杠命令增强
6. ✅ 安全性（localhost only）

**Integration Verification**：
- IV1: 不影响监控性能
- IV2: 与Claude Code集成
- IV3: 优雅停止机制

**工作量估算**：3-4小时

---

## 4.4 Story依赖关系图

```
Story 1.1 (连接解析逻辑)
    ↓
Story 1.2 (热数据存储)
    ↓
Story 1.3 (学习分析)
    ↓
Story 1.4 (异步架构) ← 可重构1.1
    ↓
Story 1.5 (冷数据存储)
    ↓
Story 1.6 (数据同步) ← 依赖1.2和1.5
    ↓
Story 1.7 (报告生成) ← 依赖1.2或1.5
    ↓
Story 1.8 (集成优化) ← 依赖所有前置Story
    ↓
Story 1.9 (运维工具) ← 可独立开发
```

---

## 4.5 开发里程碑

### Milestone 1: MVP (最小可行产品)

**包含Story**: 1.1, 1.2, 1.3, 1.7, 1.8（核心部分）

**工作量**: 20-28小时

**交付物**：
- ✅ 能监控Canvas文件变更
- ✅ 能识别学习进步（颜色流转）
- ✅ 能记录到JSON文件
- ✅ 能生成每日学习报告
- ✅ 通过基础集成测试

**用户价值**：
- 看到学习活动被自动追踪
- 获得每日学习总结
- 有数据驱动的学习洞察

---

### Milestone 2: 生产版本

**包含Story**: 全部9个Story

**工作量**: 35-49小时

**交付物**：
- ✅ 高性能异步架构（响应 < 800ms）
- ✅ 长期数据存储和查询（SQLite）
- ✅ 自动数据同步和归档
- ✅ 完整报告系统（每日/每周/Canvas分析）
- ✅ 运维工具和监控仪表板
- ✅ 完整文档和测试

**用户价值**：
- 生产级性能和可靠性
- 长期学习趋势分析
- 便捷的运维管理
- 完整的学习闭环

---

## 4.6 风险矩阵

| Story | 技术风险 | 业务风险 | 缓解策略 |
|-------|---------|---------|---------|
| 1.1 | 🟢 低 | 🟢 低 | 充分利用现有代码 |
| 1.2 | 🟢 低 | 🟢 低 | JSON写入简单可靠 |
| 1.3 | 🟡 中 | 🟢 低 | 核心逻辑需充分测试 |
| 1.4 | 🟡 中 | 🟢 低 | 异步代码复杂，需性能测试 |
| 1.5 | 🟢 低 | 🟢 低 | SQLite成熟稳定 |
| 1.6 | 🟢 低 | 🟢 低 | 数据同步逻辑简单 |
| 1.7 | 🟡 中 | 🟢 低 | 报告格式需用户验证 |
| 1.8 | 🟡 中 | 🟡 中 | 集成测试覆盖面要广 |
| 1.9 | 🟢 低 | 🟢 低 | HTTP服务器简单 |

---

## 4.7 质量保证计划

### 单元测试覆盖率目标

- 核心逻辑：> 95%
- 集成模块：> 85%
- 总体覆盖率：> 90%

### 测试类型

1. **单元测试**：每个Story完成后
2. **集成测试**：Story 1.8
3. **性能测试**：Story 1.4和1.8
4. **端到端测试**：Story 1.8
5. **用户验收测试（UAT）**：Milestone 1和2

### 测试环境

- 开发环境：本地Windows 10/11
- 测试环境：真实Obsidian + Canvas文件
- 性能测试：模拟100个Canvas文件，1000次变更

---

# 附录

## A. 术语表

| 术语 | 定义 |
|------|------|
| Canvas | Obsidian中的可视化知识管理文件（.canvas） |
| 颜色流转 | Canvas节点颜色的变化（如红→紫→绿） |
| 热数据 | 最近24小时的学习活动数据（JSON文件） |
| 冷数据 | 历史学习数据（SQLite数据库） |
| 防抖 | 延迟处理以避免频繁触发（500ms） |
| 异步处理 | 使用asyncio和线程池的并发处理 |
| Agent | 12个专业化AI Sub-agent |
| 费曼学习法 | 通过输出倒逼输入的学习方法 |
| 艾宾浩斯曲线 | 遗忘规律，用于安排复习间隔 |

## B. 参考文档

| 文档 | 路径 | 用途 |
|------|------|------|
| Canvas学习系统总览 | `CLAUDE.md` | 了解现有系统架构 |
| 监控系统真相报告 | `MONITORING_SYSTEM_TRUTH.md` | 理解当前状态 |
| 监控系统状态 | `MONITORING_STATUS.md` | 快速参考 |
| Canvas工具库 | `canvas_utils.py` | API接口 |
| 监控引擎代码 | `canvas_progress_tracker/canvas_monitor_engine.py` | 技术实现 |

## C. 联系方式

- **项目目录**: `C:/Users/ROG/托福/`
- **文档位置**: `docs/`
- **代码位置**: `canvas_progress_tracker/`
- **测试位置**: `tests/`

---

**文档结束**

**最后更新**: 2025-01-15
**下一步行动**: 根据Story优先级启动开发
**预计完成时间**: MVP 20-28小时，完整版 35-49小时

---

📋 **PRD状态**: ✅ 完成，等待审批和开发启动
