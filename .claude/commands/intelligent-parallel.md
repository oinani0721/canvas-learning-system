---
name: intelligent-parallel
description: 智能并行处理Canvas学习系统中的黄色节点
version: "1.0"
usage: "*intelligent-parallel [options] [canvas_file]"
parameters:
  - name: canvas_file
    type: string
    required: false
    description: Canvas文件路径（默认使用当前Canvas）
    position: 0

  - name: max
    alias: m
    type: integer
    required: false
    default: 12
    range: [1, 20]
    description: 最大并发Agent数量（1-20，默认12）

  - name: auto
    alias: a
    type: boolean
    required: false
    default: false
    description: 自动执行，跳过用户确认

  - name: dry_run
    alias: d
    type: boolean
    required: false
    default: false
    description: 预览模式，只生成计划不执行

  - name: nodes
    alias: n
    type: string
    required: false
    description: 指定处理的黄色节点ID（逗号分隔）

  - name: verbose
    alias: v
    type: boolean
    required: false
    default: false
    description: 显示详细执行信息
examples:
  - basic: "*intelligent-parallel"
    description: "使用默认设置处理当前Canvas的所有黄色节点"

  - custom_concurrency: "*intelligent-parallel --max 20"
    description: "设置最大并发数为20"

  - auto_execute: "*intelligent-parallel --auto"
    description: "自动执行，跳过确认步骤"

  - preview_only: "*intelligent-parallel --dry-run"
    description: "只预览执行计划，不实际执行"

  - specific_nodes: "*intelligent-parallel --nodes node1,node2,node3"
    description: "只处理指定的黄色节点"

  - custom_canvas: "*intelligent-parallel \"笔记库/离散数学/离散数学.canvas\""
    description: "处理指定的Canvas文件"

  - verbose_output: "*intelligent-parallel --verbose"
    description: "显示详细的执行过程信息"
---

# *intelligent-parallel - 智能并行处理器

## ✅ **实现状态**

**当前版本**: v1.1
**完成日期**: 2025-10-28
**核心功能**: ✅ 已实现并可用
**已知限制**: ⚠️ 三层记忆存储部分缺失 (仅会话创建，活动记录待实现)

**核心功能验证**:
- ✅ 黄色节点自动扫描
- ✅ 智能分组算法
- ✅ 真实Agent调用 (通过Task tool)
- ✅ 解释文档生成 (.md文件)
- ✅ Canvas文件修改 (添加蓝色节点)
- ⚠️ Neo4j记忆存储 (会话创建成功，活动记录待实现 - 见Epic 10.14)

**执行方式**:
```bash
# Claude Code调用方式
/intelligent-parallel "path/to/canvas.canvas" --auto

# 或使用斜杠命令
*intelligent-parallel "path/to/canvas.canvas" --auto

# 底层执行
python intelligent_parallel_executor.py
```

**后续改进**: Epic 10.14 - 三层记忆存储完整集成

---

## 概述

智能并行命令能够自动分析Canvas中的黄色理解节点，使用IntelligentParallelScheduler进行智能分组和并行处理，大幅提升学习效率。

默认情况下，命令会：
1. 扫描Canvas文件中的所有黄色节点
2. 分析节点内容并智能分组
3. 为每组推荐最适合的Agent
4. 生成执行计划供用户确认
5. 并行执行所有任务并生成结果

所有操作都在本地进行，确保数据隐私和安全。

## 语法

```
*intelligent-parallel [canvas_file] [options]
```

## 参数说明

### 位置参数
- **canvas_file**: Canvas文件路径（可选，默认查找当前目录下的Canvas文件）

### 可选参数
- **-m, --max**: 最大并发Agent数量（1-20，默认12）
- **-a, --auto**: 自动执行，跳过用户确认
- **-d, --dry-run**: 预览模式，只生成计划不执行
- **-n, --nodes**: 指定处理的黄色节点ID（逗号分隔）
- **-v, --verbose**: 显示详细执行信息

## 使用示例

### 基础用法
```bash
# 使用默认设置处理当前Canvas的所有黄色节点
*intelligent-parallel

# 处理指定的Canvas文件
*intelligent-parallel "笔记库/离散数学/离散数学.canvas"
```

### 自定义并发数
```bash
# 设置最大并发数为20
*intelligent-parallel --max 20

# 设置最大并发数为6
*intelligent-parallel -m 6
```

### 自动执行和预览
```bash
# 自动执行，跳过确认步骤
*intelligent-parallel --auto

# 只预览执行计划，不实际执行
*intelligent-parallel --dry-run

# 预览时显示详细信息
*intelligent-parallel -d -v
```

### 指定节点
```bash
# 只处理指定的黄色节点
*intelligent-parallel --nodes node1,node2,node3

# 处理指定节点并自动执行
*intelligent-parallel -n node-abc,node-def -a
```

### 详细输出
```bash
# 显示详细的执行过程信息
*intelligent-parallel --verbose

# 组合使用多个选项
*intelligent-parallel --max 8 --auto --verbose
```

## 输出格式

### 预览模式输出
```
🚀 智能并行处理计划预览
📋 分析Canvas文件: 离散数学.canvas
🔍 发现 8 个黄色节点
🧠 智能分组完成，生成 3 个任务组

⚡ 执行计划预览:
┌─────────────────────────────────────────────────┐
│ Task Group 1: clarification-path (3个节点)       │
│ - 优先级: 高 | 预估时间: 45-60秒                 │
├─────────────────────────────────────────────────┤
│ Task Group 2: comparison-table (2个节点)         │
│ - 优先级: 中 | 预估时间: 25-35秒                 │
├─────────────────────────────────────────────────┤
│ Task Group 3: memory-anchor (3个节点)            │
│ - 优先级: 中 | 预估时间: 30-40秒                 │
└─────────────────────────────────────────────────┘

📊 总体预估: 90-135秒 | 最大并发: 4个任务
💡 提示: 使用 --auto 参数跳过确认直接执行
```

### 执行过程输出
```
🚀 启动智能并行处理...
📋 分析Canvas文件: 离散数学.canvas
🔍 发现 8 个黄色节点
🧠 智能分组完成，生成 3 个任务组
✅ 用户确认执行计划

⚡ 智能并行处理进度: 0% (0/12)
⚡ 智能并行处理进度: 25% (3/12) - 正在执行clarification-path...
⚡ 智能并行处理进度: 50% (6/12) - 正在执行comparison-table...
⚡ 智能并行处理进度: 75% (9/12) - 正在执行memory-anchor...
⚡ 智能并行处理进度: 100% (12/12) - 执行完成

✅ 智能并行处理完成!
📊 执行统计:
- 处理节点: 8个
- 生成解释: 6个
- 创建总结: 6个
- 执行时间: 102秒
- 成功率: 100%
```

### 详细模式输出（--verbose）
```
🔄 [15:30:00] 开始分析节点内容...
📝 [15:30:02] 发现节点1: "逆否命题的理解" - 质量评分: 0.75
📝 [15:30:03] 发现节点2: "逻辑蕴含的关系" - 质量评分: 0.68
🧠 [15:30:05] 智能分组算法: 基于语义相似度聚类
📋 [15:30:06] 生成Task Group 1: clarification-path (相似度: 0.82)
📋 [15:30:07] 生成Task Group 2: comparison-table (相似度: 0.76)
⚡ [15:30:08] 执行计划创建完成

🔄 [15:30:10] 开始并行执行...
🎯 [15:30:15] Task Group 1 - clarification-path: 33% 完成
📝 [15:30:20] 生成解释文档: 逆否命题-澄清路径-20250127.md
🎯 [15:30:35] Task Group 2 - comparison-table: 50% 完成
📝 [15:30:40] 生成对比文档: 逆否命题-vs-否命题-20250127.md
✅ [15:31:50] 所有任务执行完成

📊 [15:31:52] 生成执行报告...
💡 [15:31:55] 学习建议:
- 节点"逆否命题"建议进一步深度拆解
- 节点"逻辑蕴含"掌握程度良好，可继续前进
```

## 智能分组策略

系统会根据以下规则对黄色节点进行智能分组：

1. **语义相似度**: 内容相近的节点分为一组
2. **学习阶段**: 根据理解质量评分分组
3. **Agent适配**: 为每组推荐最适合的Agent
4. **负载均衡**: 控制每组的大小，避免过长

### 常见的Agent推荐
- **clarification-path**: 理解模糊、需要深度澄清的概念
- **comparison-table**: 容易混淆、需要对比的概念
- **memory-anchor**: 抽象、需要形象化记忆的概念
- **oral-explanation**: 需要口语化讲解的概念
- **example-teaching**: 需要通过例题理解的概念
- **four-level-explanation**: 需要渐进式理解的概念

## 注意事项

1. **首次使用**: 建议先使用--dry-run参数预览执行计划
2. **自动执行**: --auto参数会跳过用户确认，请谨慎使用
3. **大规模处理**: 超过20个节点时建议适当降低--max参数
4. **资源消耗**: 每个Agent会消耗API额度，请合理规划
5. **数据安全**: 所有处理都在本地进行，不会上传到外部服务器

## 最佳实践

1. **分批处理**: 对于大量黄色节点，可以先用--nodes指定部分节点
2. **预览确认**: 执行前使用--dry-run查看计划
3. **并发调整**: 根据设备性能调整--max参数
4. **详细模式**: 使用--verbose了解执行细节
5. **定期检查**: 处理完成后检查生成的文档质量

## 故障排除

### 问题: "未找到可处理的黄色节点"
- 原因: Canvas中没有黄色节点，或黄色节点为空
- 解决: 先填写黄色节点中的理解内容

### 问题: "并发数超限"
- 原因: --max参数超过20或系统资源不足
- 解决: 降低--max参数值

### 问题: "节点不存在"
- 原因: --nodes指定的节点ID错误
- 解决: 检查节点ID或使用默认模式

### 问题: "执行超时"
- 原因: 节点过多或并发数过高
- 解决: 降低--max参数或分批处理

## 相关命令

- `*parallel-agents`: 手动指定Agent类型的并行处理
- `*parallel-nodes`: 处理指定节点列表
- `*canvas-help`: 获取Canvas命令帮助

## 💾 记忆记录集成

`*intelligent-parallel` 命令已集成三级记忆记录系统，自动记录所有处理过程：

### 记录内容
- **处理计划**: 智能分组结果和Agent推荐
- **执行过程**: 并行处理进度和状态变化
- **生成文档**: 所有创建的解释文档和总结
- **性能指标**: 处理时间、成功率、并发效率
- **用户交互**: 确认步骤和参数选择

### 三级保障
1. **主记录**: 同步到Graphiti知识图谱
2. **本地备份**: 加密存储到SQLite数据库
3. **文件日志**: 纯文本格式保存到日志文件

### 查看记录
```bash
# 查看记忆统计
/learning status

# 验证记录完整性
/learning verify

# 恢复丢失记录
/learning recover
```

## 版本信息

- **版本**: v1.1
- **发布日期**: 2025-10-28
- **兼容性**: Canvas Learning System v1.1+
- **新增特性**: 三级记忆记录系统集成
