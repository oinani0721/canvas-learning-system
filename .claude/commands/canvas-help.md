---
name: canvas-help
description: Complete usage guide for Canvas Learning System with monitoring
parameters:
  - name: section
    type: string
    description: Help section to display (overview, monitoring, agents, commands)
    required: false
---

# Canvas学习系统 - 完整使用指南

**版本**: v1.2 (集成监控版)
**最后更新**: 2025-10-25

{{#if (eq parameters.section "monitoring")}}

---

## 📊 监控系统专项指南

### 🎯 监控系统概览

Canvas监控系统是一个**智能学习数据追踪系统**，为你提供：
- 📁 **自动文件监控**: 实时检测Canvas文件变更
- ⏰ **学习时间追踪**: 记录每次学习的时间和时长
- 📈 **理解进度分析**: 追踪知识掌握程度的变化
- 🎯 **个性化建议**: 基于数据的学习优化建议

### 🚀 启动监控系统

#### 方法1: 集成启动（推荐）
```bash
/canvas --with-monitoring
```
一次性启动Canvas学习系统+监控系统

#### 方法2: 独立启动
```bash
python canvas_progress_tracker/monitoring_manager.py start
```
适用于需要精细控制的场景

### 📊 监控功能详解

#### 自动记录内容
- ✅ **Canvas文件变更**: 节点添加、修改、删除、颜色变更
- ✅ **Agent调用记录**: 使用的Agent类型、时间、结果
- ✅ **学习时间统计**: 每次学习的开始、结束、持续时间
- ✅ **理解程度变化**: 颜色流转（红→黄→紫→绿）的完整记录

#### 智能分析功能
- 🧠 **学习模式识别**: 分析你的学习习惯和偏好时间
- 📊 **效率分析**: 评估学习效率和薄弱环节
- 🎯 **个性化复习**: 基于遗忘曲线的智能复习提醒
- 📈 **趋势分析**: 长期学习进展和成就统计

### 📋 监控管理命令

#### 查看监控状态
```bash
/monitoring-status
```
显示：
- 监控系统运行状态
- 实时学习统计
- 性能指标
- 组件状态

#### 生成学习报告
```bash
/learning-report              # 最近7天
/learning-report --days 30    # 最近30天
/learning-report --days 90    # 最近90天
```

#### 停止监控
```bash
/stop-monitoring
```
安全停止并保存最终统计

### 💾 数据存储和隐私

#### 数据位置
```
C:\Users\ROG\托福\canvas_progress_tracker\
├── data\                    # 学习数据
│   ├── learning_analytics\  # 学习分析报告
│   ├── change_history\      # 变更历史
│   └── session_reports\     # 会话报告
└── logs\                    # 系统日志
```

#### 隐私保护
- ✅ **本地存储**: 所有数据存储在本地，不上传云端
- ✅ **内容隐私**: 不记录Canvas文件内容，只记录学习元数据
- ✅ **自动清理**: 可配置数据保留期限，自动清理过期数据
- ✅ **用户控制**: 随时可以停止监控或删除数据

### 🎯 监控数据应用

#### 艾宾浩斯复习集成
监控系统与复习系统无缝集成：
- **智能复习时机**: 基于遗忘曲线计算最佳复习时间
- **薄弱点识别**: 自动识别需要重点复习的知识点
- **复习效果追踪**: 记录复习过程和掌握程度提升

#### 个性化学习建议
基于监控数据生成：
- **学习时间优化**: 推荐最佳学习时间段
- **学习方式建议**: 根据你的学习偏好推荐Agent
- **效率改进建议**: 识别影响学习效率的因素

### ⚙️ 监控配置

#### 性能配置
```yaml
# canvas_monitor_config.yaml
performance:
  max_cpu_usage_percent: 5.0    # CPU使用限制
  max_memory_usage_mb: 100.0     # 内存使用限制

debounce:
  base_delay_ms: 500            # 防抖延迟
  enable_adaptive: true          # 自适应调整
```

#### 存储配置
```yaml
storage:
  snapshot_retention_days: 30    # 快照保留天数
  statistics_retention_days: 90  # 统计数据保留天数
  enable_compression: true       # 启用数据压缩
```

### 🛠️ 高级监控功能

#### 自定义回调
```python
from canvas_progress_tracker import CanvasMonitorSystem

monitor = CanvasMonitorSystem(auto_init=True)

def custom_learning_callback(event_data):
    # 自定义学习事件处理
    print(f"学习活动: {event_data}")

monitor.add_system_callback("learning_activity", custom_learning_callback)
```

#### 数据导出
```bash
# 导出学习报告
python canvas_progress_tracker/monitoring_manager.py report --days 30 --export

# 导出原始数据
python canvas_progress_tracker/monitoring_manager.py export --format json
```

### 💡 监控使用建议

#### 最佳实践
1. **持续监控**: 保持监控系统长期运行以获得完整数据
2. **定期回顾**: 每周查看学习报告，了解进展和调整策略
3. **数据驱动**: 根据监控数据的建议优化学习方法和时间安排
4. **隐私平衡**: 根据需要调整监控级别和数据保留设置

#### 何时使用监控
- ✅ **强烈推荐**: 系统化学习、考试准备、技能提升
- ✅ **推荐使用**: 长期项目、知识体系构建
- ⚪ **可选使用**: 兴趣学习、临时查询

---

{{else if (eq parameters.section "agents")}}

---

## 🤖 AI Agents专项指南

### 📋 Agents分类总览

Canvas学习系统包含**12个专业化AI Agents**，分为4大类：

#### 1. 主控Agent (1个)
- **canvas-orchestrator**: 统一协调所有Agent，自动识别意图并调度

#### 2. 拆解系列Agent (3个)
- **basic-decomposition**: 将复杂材料拆解为基础问题
- **deep-decomposition**: 深度拆解似懂非懂的概念
- **question-decomposition**: 生成突破性问题

#### 3. 解释系列Agent (6个)
- **oral-explanation**: 800-1200词教授式口语化解释
- **clarification-path**: 1500+词系统化澄清路径
- **comparison-table**: 结构化概念对比表格
- **memory-anchor**: 生动类比、故事、记忆口诀
- **four-level-explanation**: 4层次渐进解释(新手→专家)
- **example-teaching**: 完整例题教学(1000词)

#### 4. 评分和检验Agent (2个)
- **scoring-agent**: 4维理解评分(准确性、具象性、完整性、原创性)
- **verification-question-agent**: 深度检验问题生成

### 🎯 Agent使用策略

#### 红色节点 (完全不懂)
```bash
# 首选：基础拆解
帮我基础拆解 @笔记库/数学/高数.canvas 中的"极限"节点

# Agent会生成3-7个简单引导问题，帮助你从完全不懂到初步理解
```

#### 黄色节点 (学习中)
```bash
# 填写个人理解后评分
帮我评分 @笔记库/数学/高数.canvas 中所有黄色节点

# 评分结果：
# - <60分: 保持红色，继续基础拆解
# - 60-79分: 转紫色，需要深度学习
# - ≥80分: 转绿色，完全理解
```

#### 紫色节点 (似懂非懂)
```bash
# 深度拆解 + 补充解释
帮我深度拆解 @笔记库/数学/高数.canvas 中的"极限"，我的理解是：[你的理解]

# 根据需要选择解释Agent：
帮我生成澄清路径 @笔记库/数学/高数.canvas 中的"极限"  # 系统化深度理解
帮我生成对比表：极限 vs 无穷小                      # 对比易混淆概念
帮我生成记忆锚点 @笔记库/数学/高数.canvas 中的"极限"  # 帮助记忆
```

### 📊 Agent详细介绍

#### 拆解系列Agent

**basic-decomposition** (基础拆解)
- **用途**: 红色节点 → 基础理解
- **输出**: 3-7个引导性问题
- **问题类型**: 定义型、实例型、对比型、探索型
- **示例**: "什么是逆否命题？" "能举一个生活中的例子吗？"

**deep-decomposition** (深度拆解)
- **用途**: 紫色节点 → 暴露理解盲区
- **输入**: 需要你现有的理解作为输入
- **输出**: 3-10个深度检验问题
- **问题类型**: 对比型、原因型、应用型、边界型

**question-decomposition** (问题拆解)
- **用途**: 应用题、问题求解场景
- **输出**: 突破性问题链
- **特点**: 逐步引导，降低难度

#### 解释系列Agent

**oral-explanation** (口语化解释) 🗣️
- **篇幅**: 800-1200词
- **风格**: 教授式、口语化
- **结构**: 背景铺垫 → 核心解释 → 生动举例 → 常见误区
- **适用**: 需要系统化、生动讲解的场景

**clarification-path** (澄清路径) 🔍
- **篇幅**: 1500+词
- **风格**: 学术化、系统化
- **结构**: 问题澄清 → 概念拆解 → 深度解释 → 验证总结
- **适用**: 复杂概念需要深度澄清

**comparison-table** (对比表) 📊
- **格式**: Markdown表格
- **对比维度**: 定义、特征、使用场景、示例、常见错误
- **适用**: 区分易混淆概念

**memory-anchor** (记忆锚点) ⚓
- **内容**: 生动类比、故事、记忆口诀
- **目标**: 增强长期记忆
- **适用**: 理解了但难记住的概念

**four-level-explanation** (四层次解释) 🎯
- **层次**: 新手→进阶→专家→创新
- **篇幅**: 每层次300-400词，总计1200-1600词
- **特点**: 渐进式，可自选起点

**example-teaching** (例题教学) 📝
- **结构**: 题目→思路分析→分步求解→易错点→变式练习→答案提示
- **篇幅**: 1000词左右
- **适用**: 通过例题学习掌握应用

#### 评分和检验系列Agent

**scoring-agent** (评分Agent)
- **评分维度** (各25分，总分100):
  - **Accuracy** (准确性): 理解是否正确
  - **Imagery** (具象性): 是否有具体例子
  - **Completeness** (完整性): 理解是否全面
  - **Originality** (原创性): 是否有自己的思考
- **颜色流转规则**: ≥80分→绿色，60-79分→紫色，<60分→红色
- **智能推荐**: 根据弱项推荐合适的Agent

**verification-question-agent** (检验问题Agent)
- **红色节点**: 1-2个突破型/基础型问题
- **紫色节点**: 2-3个检验型/应用型问题
- **用途**: 检验白板生成，暴露理解盲区

### 🎨 Agent选择建议

#### 按学习阶段选择
```
完全不懂 (红色):
└─ basic-decomposition (必需)
   └─ 填写黄色理解 → scoring-agent

似懂非懂 (紫色):
├─ deep-decomposition (暴露盲区)
├─ 选择1-2个解释Agent:
│  ├─ clarification-path (系统化深度)
│  ├─ oral-explanation (生动讲解)
│  ├─ comparison-table (对比易混淆)
│  ├─ memory-anchor (帮助记忆)
│  ├─ four-level-explanation (渐进理解)
│  └─ example-teaching (例题巩固)
└─ 再次评分验证掌握程度
```

#### 按学习类型选择
| 学习目标 | 推荐Agent组合 |
|----------|---------------|
| **系统理解** | basic-decomposition → clarification-path → scoring-agent |
| **快速掌握** | basic-decomposition → oral-explanation → scoring-agent |
| **深度掌握** | basic-decomposition → (clarification-path + memory-anchor) → scoring-agent |
| **应用能力** | basic-decomposition → example-teaching → scoring-agent |
| **辨析概念** | basic-decomposition → comparison-table → scoring-agent |

### 💡 Agent使用技巧

#### 提高Agent效果
1. **明确输入**: 清楚说明你的问题或当前理解
2. **提供上下文**: 告诉Agent你的学习背景和目标
3. **具体化**: 避免模糊的描述，提供具体的概念名称
4. **反馈循环**: 根据Agent输出调整你的理解，再次交互

#### 示例对话
```bash
# 好的提问
帮我基础拆解 @笔记库/线性代数/线性代数.canvas 中的"特征向量"，我正在学习线性代数，但对这个概念很困惑。

# 不够好的提问
拆解特征向量 (缺少上下文和具体场景)
```

---

{{else if (eq parameters.section "commands")}}

---

## 📚 命令大全专项指南

### 🚀 核心启动命令

#### Canvas系统启动
```bash
/canvas                              # 标准模式启动
/canvas --with-monitoring            # 带监控启动 (推荐)
/canvas --with-monitor               # 简写形式
```

#### 监控管理命令
```bash
/monitoring-status                   # 查看监控状态
/learning-report                     # 生成学习报告 (默认7天)
/learning-report --days 30           # 30天学习报告
/learning-report --days 90           # 90天学习报告
/stop-monitoring                     # 停止监控系统
```

#### 系统信息命令
```bash
/canvas-status                       # Canvas系统状态
/canvas-agents                       # 查看所有12个Agent
/canvas-demo                         # 演示示例
/dev-roadmap                         # 开发路线图
/canvas-help                         # 完整使用指南
```

#### 智能并行命令
```bash
# 智能并行处理黄色节点（推荐）
*intelligent-parallel                # 使用默认设置处理当前Canvas
*intelligent-parallel --dry-run      # 预览执行计划
*intelligent-parallel --auto         # 自动执行，跳过确认
*intelligent-parallel --max 20       # 设置最大并发数
*intelligent-parallel --nodes node1,node2  # 处理指定节点
*intelligent-parallel --verbose      # 显示详细进度
```

#### 传统并行命令
```bash
/parallel-agents clarification-path 4     # 并行执行clarification-path
/parallel-nodes node1,node2,node3         # 并行处理指定节点
/parallel-color red                        # 并行处理红色节点
/parallel-mixed clarification-path,scoring-agent  # 混合并行
```

### 🎯 Agent调用命令格式

#### 基础格式
```bash
@文件路径.canvas [操作] [节点名/概念]
```

#### 拆解命令
```bash
# 基础拆解 (红色节点)
帮我基础拆解 @笔记库/数学/高数.canvas 中的"极限"
拆解 @笔记库/物理/力学.canvas "牛顿第二定律"
@离散数学.canvas 拆解"逆否命题"

# 深度拆解 (紫色节点，需要提供当前理解)
帮我深度拆解 @笔记库/数学/高数.canvas 中的"极限"，我的理解是：极限是函数在某点的逼近值，但我不太理解ε-δ定义的几何意义
深度拆解 @线性代数.canvas "特征向量"，我的理解是：...
```

#### 解释命令
```bash
# 口语化解释 (800-1200词教授式)
生成口语化解释 @笔记库/数学/高数.canvas 中的"极限"
帮我生成口语解释"逆否命题"

# 澄清路径 (1500+词系统化)
生成澄清路径 @笔记库/数学/高数.canvas 中的"极限"
帮我生成澄清路径"德摩根律"

# 对比表 (结构化对比)
生成对比表：逆否命题 vs 否命题
帮我对比：析取范式 vs 合取范式
对比 @离散数学.canvas "命题逻辑" vs "谓词逻辑"

# 记忆锚点 (生动类比)
生成记忆锚点 @笔记库/数学/高数.canvas 中的"极限"
帮我生成记忆口诀"德摩根律"

# 四层次解释 (渐进式)
生成四层次答案 @笔记库/数学/高数.canvas 中的"极限"
帮我生成四层次解释"特征向量"

# 例题教学 (完整解题教程)
生成例题教学 @笔记库/数学/高数.canvas 中的"极限在证明中的应用"
帮我生成例题"用德摩根律化简逻辑表达式"
```

#### 评分命令
```bash
# 单节点评分
评分 @笔记库/数学/高数.canvas 这个黄色节点
帮我评分"逆否命题"的理解

# 批量评分
评分 @笔记库/数学/高数.canvas 所有黄色节点
帮我对所有理解节点评分
评分 @离散数学.canvas 黄色节点
```

#### 检验白板命令
```bash
# 生成检验白板
生成检验白板 @笔记库/数学/高数.canvas
帮我创建检验白板
@离散数学.canvas 生成检验白板
```

### 📊 监控相关命令详解

#### 查看监控状态
```bash
/monitoring-status
```
**显示内容**:
- 监控系统运行状态 (运行中/未运行)
- 本次会话统计 (学习时长、处理节点数、理解提升次数)
- 掌握情况分布 (红/黄/紫/绿节点数量)
- 性能指标 (CPU、内存使用)
- 组件状态 (各模块运行状态)
- 个性化学习建议

#### 生成学习报告
```bash
/learning-report                    # 默认7天报告
/learning-report --days 30          # 自定义天数
/learning-report --days 7 --export  # 导出报告
```
**报告内容**:
- 核心指标 (学习天数、时长、活跃度)
- 知识掌握分析 (颜色分布、掌握率)
- 学习模式 (最活跃时间、常用Agent)
- 学习成就 (连续学习天数、最高效一天)
- 个性化建议 (效率优化、复习策略)

#### 停止监控
```bash
/stop-monitoring
```
**功能**:
- 安全停止监控系统
- 保存本次会话的最终统计
- 显示学习成就和建议
- 数据安全保存至本地

### 🛠️ 高级命令用法

#### 组合使用场景
```bash
# 场景1: 开始新的学习主题
/canvas --with-monitoring          # 启动带监控的系统
帮我基础拆解 @笔记库/物理/电磁学.canvas 中的"麦克斯韦方程组"

# 场景2: 检查学习进度
/monitoring-status                  # 查看当前学习状态
/learning-report --days 7          # 查看本周学习报告

# 场景3: 深度学习复杂概念
帮我深度拆解 @笔记库/物理/电磁学.canvas 中的"麦克斯韦方程组"，我的理解是：...
生成澄清路径 @笔记库/物理/电磁学.canvas 中的"麦克斯韦方程组"
帮我生成对比表：电场 vs 磁场

# 场景4: 智能并行处理（批量提升）
*intelligent-parallel --dry-run    # 先预览执行计划
*intelligent-parallel --auto       # 自动并行处理所有黄色节点

# 场景5: 验证掌握程度
帮我评分 @笔记库/物理/电磁学.canvas 所有黄色节点
生成检验白板 @笔记库/物理/电磁学.canvas

# 场景6: 结束学习会话
/stop-monitoring                   # 停止并查看统计
```

#### 智能并行处理详解

智能并行命令是Canvas学习系统的**核心效率工具**：

```bash
# 基础使用
*intelligent-parallel              # 一键智能并行处理

# 预览模式（首次使用推荐）
*intelligent-parallel --dry-run    # 查看执行计划，不实际执行

# 自定义并发数
*intelligent-parallel --max 8      # 限制并发数为8（默认12）

# 自动执行（跳过确认）
*intelligent-parallel --auto       # 适合批量处理

# 详细模式
*intelligent-parallel --verbose    # 显示详细执行过程

# 处理特定节点
*intelligent-parallel --nodes node1,node2,node3
```

**智能并行功能特点**：
- 🧠 **智能分组**: 根据内容相似度自动分组黄色节点
- 🎯 **智能推荐**: 为每组推荐最适合的Agent类型
- ⚡ **并行执行**: 同时处理多个任务，大幅提升效率
- 📊 **进度监控**: 实时显示执行进度和结果
- 💡 **学习建议**: 基于执行结果生成个性化建议

**适用场景**：
- 批量处理多个黄色理解节点
- 需要快速生成多种解释文档
- 系统化复习和知识巩固
- 检验学习效果和盲区

#### 命令参数说明
```bash
# learning-report 参数
/learning-report --days [数字]     # 报告天数 (1-365)
/learning-report --export          # 导出报告到文件
/learning-report --format [格式]   # 报告格式 (text/markdown/json)

# canvas 参数
/canvas --with-monitoring         # 启用监控
/canvas --config [路径]            # 使用自定义配置
/canvas --debug                   # 调试模式
```

### ⚡ 命令使用技巧

#### 提高命令识别率
1. **完整文件路径**: 使用 `@笔记库/学科/文件.canvas` 格式
2. **具体节点名**: 准确指定节点名称或概念
3. **操作明确**: 使用"帮我"、"生成"、"拆解"等明确动词
4. **上下文提供**: 在深度拆解时提供你的当前理解

#### 批量操作技巧
```bash
# 批量评分同一文件的所有节点
评分 @笔记库/数学/高数.canvas 所有黄色节点

# 批量生成解释 (逐个进行)
帮我生成口语化解释 @笔记库/数学/高数.canvas 中的"极限"
帮我生成口语化解释 @笔记库/数学/高数.canvas 中的"连续"
帮我生成口语化解释 @笔记库/数学/高数.canvas 中的"导数"
```

#### 错误处理
```bash
# 如果命令未被识别，尝试：
# 1. 检查文件路径格式
# 2. 确认文件存在
# 3. 简化命令，逐步尝试
# 4. 使用 /canvas-status 检查系统状态
```

---

{{else}}

## 📖 目录

1. [快速开始](#快速开始)
2. [基础概念](#基础概念)
3. [颜色系统](#颜色系统)
4. [命令大全](#命令大全)
5. [监控系统](#监控系统)
6. [AI Agents](#ai-agents)
7. [完整学习流程](#完整学习流程)
8. [Epic 4: 检验白板](#epic-4-检验白板)
9. [故障排除](#故障排除)
10. [最佳实践](#最佳实践)

### 📚 专项帮助
- `/canvas-help --section monitoring` - 监控系统专项指南
- `/canvas-help --section agents` - AI Agents专项指南
- `/canvas-help --section commands` - 命令使用专项指南

{{/if}}

---

## 快速开始

### 前置要求

1. **Obsidian** - 用于查看和编辑Canvas白板
2. **Python 3.9+** - 运行canvas_utils.py
3. **Claude Code** - 已启动（你现在就在用）

### 3步启动

**Step 1: 打开Obsidian**
```
1. 启动 Obsidian
2. "打开文件夹作为库" → 选择 C:\Users\ROG\托福\笔记库
```

**Step 2: 创建Canvas文件**
```
在Obsidian中：
- 创建新Canvas：右键 → New → Canvas
- 或打开现有Canvas：笔记库/[学科]/[文件名].canvas
```

**Step 3: 使用Claude Code Agent**
```
帮我基础拆解 @笔记库/离散数学/离散数学.canvas 中的"逆否命题"节点
```

---

## 基础概念

### 费曼学习法

**核心理念**: "如果你不能简单地解释某件事，说明你还没有真正理解它。" —— 费曼

**在本系统中的实现**:
1. **黄色节点 = 输出区**: 强制用自己的话解释
2. **4维评分**: 量化理解质量
3. **颜色流转**: 可视化学习进度（红→紫→绿）

### 3层Python架构

- **Layer 1: CanvasJSONOperator** - 底层JSON操作
- **Layer 2: CanvasBusinessLogic** - 业务逻辑、布局算法
- **Layer 3: CanvasOrchestrator** - 高级API、Agent调用

---

## 颜色系统

| Canvas颜色 | 含义 | 使用场景 | 流转条件 |
|-----------|------|---------|---------|
| 🔴 红色 (1) | 完全不理解 | 学生完全看不懂的材料 | 评分<60分 |
| 🟡 黄色 (6) | 个人理解输出区 | 用自己的话解释概念 | 用户填写 |
| 🟣 紫色 (3) | 似懂非懂 | 需要深度检验 | 评分60-79分 |
| 🟢 绿色 (2) | 完全理解 | 已掌握 | 评分≥80分 |
| 🔵 蓝色 (5) | AI生成解释 | AI创建的文档节点 | 自动标记 |

**颜色流转路径**:
```
🔴 红色 (完全不懂)
  ↓ 基础拆解 + 填写理解 + 评分
🟣 紫色 (似懂非懂, 60-79分)
  ↓ 深度拆解 + 补充解释 + 优化理解 + 再评分
🟢 绿色 (完全理解, ≥80分)
```

---

## 命令大全

### 拆解命令

**基础拆解** (红色节点 → 简单问题)
```
拆解 @笔记库/离散数学/离散数学.canvas "逆否命题"
帮我基础拆解这个红色节点
@离散数学.canvas 拆解"布尔代数"
```

**深度拆解** (紫色节点 → 检验问题)
```
深度拆解 @笔记库/线性代数/线性代数.canvas "特征向量"，我的理解是：...
帮我深度拆解这个紫色节点
```

### 解释命令

**口语化解释** (800-1200词教授式)
```
生成口语化解释 @离散数学.canvas "逆否命题"
帮我生成口语解释"布尔代数"
```

**澄清路径** (1500+词系统化)
```
生成澄清路径 @离散数学.canvas "范式"
帮我生成澄清路径"逆否命题"
```

**对比表** (结构化对比)
```
生成对比表：逆否命题 vs 否命题
帮我对比：析取范式 vs 合取范式
```

**记忆锚点** (生动类比)
```
生成记忆锚点 @离散数学.canvas "逆否命题"
帮我生成记忆口诀"德摩根律"
```

**四层次答案** (新手→专家)
```
生成四层次答案 @离散数学.canvas "逆否命题"
帮我生成四层次解释"特征向量"
```

**例题教学** (完整解题教程)
```
生成例题教学 @离散数学.canvas "逆否命题在证明中的应用"
帮我生成例题"用德摩根律化简"
```

### 评分命令

**单节点评分**
```
评分 @离散数学.canvas 这个黄色节点
帮我评分"逆否命题"的理解
```

**批量评分**
```
评分 @离散数学.canvas 所有黄色节点
帮我对所有理解节点评分
```

### 智能并行命令 (Story 10.3)

**智能并行处理 - 推荐的批量处理方式**
```
*intelligent-parallel                     # 默认设置处理所有黄色节点
*intelligent-parallel --dry-run           # 预览模式，查看执行计划
*intelligent-parallel --auto              # 自动执行，跳过确认
*intelligent-parallel --max 20            # 设置最大并发数（1-20）
*intelligent-parallel --verbose           # 显示详细执行信息
*intelligent-parallel --nodes node1,node2 # 只处理指定节点
```

**智能分组和Agent推荐示例**：
- 自动识别相似概念并分组
- 为每组推荐最适合的Agent（clarification-path, comparison-table等）
- 并行执行，大幅提升效率

### 检验白板命令 (Epic 4)

**生成检验白板**
```
生成检验白板 @离散数学.canvas
帮我创建检验白板
```

---

## 完整学习流程

### 场景：学习"逆否命题"

**Step 1: 创建学习白板**
1. 在Obsidian创建 `离散数学.canvas`
2. 添加文本节点，输入："逆否命题是什么？"
3. 右键节点 → 设置颜色 → 红色

**Step 2: 基础拆解**
```
@离散数学.canvas 拆解"逆否命题"
```
→ Agent生成3-7个子问题

**Step 3: 填写个人理解**
在Obsidian中，点击黄色节点，用自己的话解释

**Step 4: 评分**
```
@离散数学.canvas 评分所有黄色节点
```
→ 如果<60分，继续拆解；60-79分，转紫色

**Step 5: 深度拆解（紫色节点）**
```
@离散数学.canvas 深度拆解"逆否命题"，我的理解是：...
```

**Step 6: 补充AI解释**
```
@离散数学.canvas 生成口语化解释"逆否命题"
```

**Step 7: 再次评分**
```
@离散数学.canvas 评分所有黄色节点
```
→ 如果≥80分，转绿色！

**Step 8: 生成检验白板验证**
```
@离散数学.canvas 生成检验白板
```
→ 在检验白板上从头复现，检验真正理解程度

---

## Epic 4: 检验白板

### 什么是检验白板？

**原白板** (Learning Canvas):
- 有AI辅助（拆解、解释、评分）
- 边学边填写
- 复杂的知识网络

**检验白板** (Review Canvas):
- 初始无辅助（只有检验问题）
- 从头复现知识
- 暴露理解盲区
- **支持所有Agent操作**（动态学习白板）

### 检验白板使用流程

**Step 1: 生成检验白板**
```
@离散数学.canvas 生成检验白板
```
→ 自动提取红色/紫色节点，生成检验问题
→ 输出：`离散数学-检验白板-20250115.canvas`

**Step 2: 在检验白板上填写理解（不看原白板）**
在Obsidian中打开检验白板，填写黄色节点

**Step 3: 在检验白板上调用Agent（与原白板完全相同）**
```
@离散数学-检验白板-20250115.canvas 评分所有黄色节点
@离散数学-检验白板-20250115.canvas 拆解这个红色问题
```

**Step 4: 持续迭代直到80%绿色**
检验白板支持无限次迭代：
```
填写理解 → 评分 → 拆解 → 补充解释 → 重复
```

### 8步学习循环（检验白板专用）

1. 填写个人理解（黄色节点，不看资料）
2. 发现不足
3. 继续拆解（basic/deep-decomposition）
4. 补充解释（6种解释Agent）
5. 评分验证（scoring-agent）
6. 颜色流转（红→紫→绿）
7. 添加自己的节点
8. 构建完整知识网络

### 何时停止迭代？

满足以下**至少3个条件**：
- ✅ 绿色占比 ≥ 80%
- ✅ 节点数量接近原白板的50-70%
- ✅ 至少生成3个解释文档
- ✅ 至少添加2个原创节点
- ✅ 无红色节点

---

## 故障排除

### Q: Canvas不刷新？
**A**: 按 `Ctrl+R` 或等待Obsidian自动刷新（约5-10秒）

### Q: Agent无法识别命令？
**A**: 确认命令格式：`@文件路径.canvas 操作 节点名`

示例：
```
✅ 正确：@笔记库/离散数学/离散数学.canvas 拆解"逆否命题"
❌ 错误：@离散数学 拆解逆否命题（缺少.canvas扩展名）
```

### Q: 评分失败？
**A**: 先在Obsidian中填写黄色节点的个人理解

### Q: 找不到Canvas文件？
**A**: 使用相对路径：`@笔记库/学科/文件.canvas`

### Q: Python错误？
**A**: 验证Python环境：
```bash
python --version  # 应该是3.9+
python -c "import canvas_utils"  # 应该无错误
```

### Q: 检验白板文件在哪？
**A**: 与原白板同目录，文件名格式：`原文件名-检验白板-YYYYMMDD.canvas`

---

## 🎯 最佳实践

### 原白板学习

**完全不懂（红色节点）**:
1. basic-decomposition拆解
2. 填写黄色节点理解
3. 评分 → 如果<60分，重新拆解更细
4. 如果60-79分 → 转紫色

**似懂非懂（紫色节点）**:
1. deep-decomposition深度拆解
2. 补充AI解释（clarification-path, oral-explanation）
3. 优化黄色节点理解
4. 再次评分 → 如果≥80分，转绿色

### 检验白板学习

**推荐流程**:
1. 生成检验白板（从原白板提取红/紫节点）
2. 初次填写（不看资料），暴露盲区
3. 评分识别弱项
4. 针对性拆解和解释
5. 重新填写优化理解
6. 再次评分验证进步
7. 重复直到80%绿色

**常见场景推荐**:

| 症状 | 推荐Agent | 目标 |
|------|----------|------|
| 完全不懂 | basic-decomposition | 拆解降难度 |
| 似懂非懂(紫色) | clarification-path | 深度理解 |
| 易混淆概念 | comparison-table | 结构化对比 |
| 需要记忆 | memory-anchor | 生动类比 |
| 需要练习 | example-teaching | 例题巩固 |

---

## 📚 更多资源

- **完整使用指南**: QUICK-START.md
- **Agent规格对比**: docs/agent-descriptions-comparison.md
- **项目简报**: docs/project-brief.md
- **架构文档**: docs/architecture/
- **开发路线图**: `/dev-roadmap`

---

**Canvas学习系统 v1.1**

**基于费曼学习法 | 12个专业化Agent | 无纸化检验系统**

提示：输入 `/canvas` 返回主界面
