# Epic 10 集成到 Canvas-Orchestrator 设计方案

**文档版本**: v1.0
**创建日期**: 2025-11-04
**Epic**: Epic 10 - Intelligent Parallel Processing System
**目标**: 将智能并行处理系统集成到canvas-orchestrator主控Agent

---

## 🎯 集成目标

将Epic 10的三大核心能力集成到canvas-orchestrator:

1. **智能内容分析** (Phase 4): 自动分析节点内容,提取特征
2. **智能Agent匹配** (Phase 4): 基于内容自动推荐最佳Agent
3. **异步并行执行** (Phase 5): 单响应多Task并发调用

**用户体验提升**:
- 用户输入: `@Lecture5.canvas 批量生成所有黄色节点的AI解释`
- 系统自动: 分析内容 → 智能匹配Agent → 并行执行 → 更新Canvas
- 用户获得: 一次性返回所有高质量解释文档

---

## 📊 当前架构分析

### canvas-orchestrator 当前能力

**已有功能**:
1. **意图识别**: 解析自然语言指令
2. **Canvas文件操作**: 读取、解析、更新Canvas
3. **Sub-agent调度**: 逐个调用clarification-path, oral-explanation等
4. **结果整合**: 整合Sub-agent返回并更新Canvas

**当前限制**:
- ❌ 无智能内容分析能力
- ❌ Agent选择依赖用户明确指定或预设规则
- ❌ 串行执行多个Agent (逐个等待)
- ❌ 无批量并行处理能力

### Epic 10 核心能力

**Phase 4 - 智能分组系统**:
```python
def intelligent_agent_matching(node_content: str) -> str:
    """基于内容关键词智能匹配Agent"""

    keywords_map = {
        "clarification-path": ["理解", "解释", "澄清", "概念", "Level Set"],
        "oral-explanation": ["定义", "公式", "推导", "计算", "线性逼近"],
        "memory-anchor": ["记忆", "记住", "Title", "Section", "切平面"]
    }

    for agent, keywords in keywords_map.items():
        if any(kw in node_content for kw in keywords):
            return agent

    return "clarification-path"  # 默认
```

**Phase 5 - 异步并行执行**:
```python
# 单响应中同时调用多个Task
Task(subagent_type="clarification-path", prompt=prompt1)
Task(subagent_type="oral-explanation", prompt=prompt2)
Task(subagent_type="memory-anchor", prompt=prompt3)
Task(subagent_type="memory-anchor", prompt=prompt4)
# 所有Task同时执行
```

---

## 🏗️ 集成架构设计

### 整体架构

```
用户自然语言指令
        ↓
canvas-orchestrator (主控)
        ↓
  [意图识别模块]
        ↓
  ┌─────┴─────┐
  │           │
单节点操作  批量并行操作 ← Epic 10集成点
  │           │
  │      [智能分组引擎] ← Phase 4
  │           ↓
  │      [并行执行引擎] ← Phase 5
  │           ↓
  └─────┬─────┘
        ↓
   结果整合 & Canvas更新
        ↓
   用户反馈
```

### 三层架构

**Layer 1: 意图识别层** (canvas-orchestrator现有)
- 解析用户指令
- 识别操作类型: 单节点 vs 批量

**Layer 2: 智能调度层** (Epic 10新增)
- **智能分组模块** (Phase 4):
  - 分析所有目标节点
  - 提取内容特征
  - 智能匹配Agent
  - 生成执行计划

- **并行执行模块** (Phase 5):
  - 复用分组结果
  - 单响应多Task并发
  - 错误处理和重试

**Layer 3: Canvas更新层** (canvas-orchestrator现有 + Epic 10增强)
- 批量添加蓝色节点
- 批量添加连接边
- 一次性保存Canvas

---

## 💡 新增自然语言命令

### 命令1: 批量智能解释

**用户输入**:
```
@Lecture5.canvas 批量生成所有黄色节点的AI解释
```

**系统行为**:
1. 读取Canvas,提取所有黄色节点
2. 智能分析每个节点内容
3. 自动匹配最佳Agent
4. **并行执行**所有Agent调用
5. 批量更新Canvas (添加蓝色节点+边)
6. 返回执行报告

**预期输出**:
```
✅ 批量智能解释完成！

分析结果:
  - 总节点数: 4个
  - Agent分配:
    • clarification-path: 1个 (Level Set理解)
    • oral-explanation: 1个 (线性逼近)
    • memory-anchor: 2个 (Section标题、切平面)

执行统计:
  - 并行执行时间: 8秒
  - 生成文档: 4个 (13,800字)
  - Canvas更新: +4节点, +4边

生成的文档:
  1. b476fd6b03d8bbff-level-set-clarification-path-{timestamp}.md
  2. kp13-linear-approximation-oral-explanation-{timestamp}.md
  3. section-14-4-header-memory-anchor-{timestamp}.md
  4. kp12-tangent-plane-memory-anchor-{timestamp}.md
```

### 命令2: 智能批量评分

**用户输入**:
```
@Lecture5.canvas 智能批量处理所有黄色节点
```

**系统行为**:
1. 提取所有黄色节点
2. 智能判断每个节点需要的操作:
   - 如果有用户理解内容 → 评分 (scoring-agent)
   - 如果内容空白 → 跳过或提示
   - 如果需要解释 → 智能匹配解释Agent
3. **并行执行**所有操作
4. 批量更新Canvas

### 命令3: 指定Agent批量处理

**用户输入**:
```
@Lecture5.canvas 用memory-anchor批量处理所有KP节点
```

**系统行为**:
1. 提取所有KP节点（通过ID前缀过滤）
2. 所有节点使用指定的memory-anchor Agent
3. **并行执行**
4. 批量更新Canvas

**变种**:
```
@Lecture5.canvas 用clarification-path批量处理所有Section标题
@Lecture5.canvas 用oral-explanation批量处理所有公式节点
```

---

## 🔧 技术实现方案

### 方案1: 扩展canvas-orchestrator.md (推荐)

**优势**:
- 保持现有架构
- 用户体验统一
- 无需新的Agent

**实现步骤**:

**Step 1**: 在canvas-orchestrator.md中添加新的意图识别模式

```markdown
## 三、意图识别（Intent Recognition）

### 新增: 批量并行操作识别

**触发关键词**:
- "批量生成"
- "批量处理"
- "所有黄色节点"
- "智能批量"

**示例**:
- `@file.canvas 批量生成所有黄色节点的AI解释`
- `@file.canvas 智能批量处理所有KP节点`

**执行流程**:
1. 调用Python脚本: `scripts/intelligent_parallel_orchestrator.py`
2. 传入参数: canvas_path, operation_type
3. 等待脚本返回结果
4. 解析JSON结果并向用户反馈
```

**Step 2**: 创建新的Python脚本整合Phase 4+5

文件: `scripts/intelligent_parallel_orchestrator.py`

```python
"""
Intelligent Parallel Orchestrator
整合Phase 4智能分组 + Phase 5并行执行
供canvas-orchestrator调用
"""

import json
import sys
from pathlib import Path
from datetime import datetime

class IntelligentParallelOrchestrator:
    """智能并行处理协调器"""

    def __init__(self, canvas_path: str):
        self.canvas_path = canvas_path
        self.canvas = None
        self.yellow_nodes = []
        self.agent_tasks = []

    def load_canvas(self):
        """加载Canvas文件"""
        with open(self.canvas_path, 'r', encoding='utf-8') as f:
            self.canvas = json.load(f)

    def extract_yellow_nodes(self):
        """提取所有黄色节点（color="6"）"""
        self.yellow_nodes = [
            node for node in self.canvas['nodes']
            if node.get('color') == '6'
        ]

    def intelligent_agent_matching(self, node_content: str) -> str:
        """
        智能Agent匹配 (Phase 4核心)

        基于关键词匹配最佳Agent
        """
        keywords_map = {
            "clarification-path": ["理解", "解释", "澄清", "概念", "Level Set"],
            "oral-explanation": ["定义", "公式", "推导", "计算", "线性逼近", "KP"],
            "memory-anchor": ["记忆", "记住", "Title", "Section", "切平面"]
        }

        for agent, keywords in keywords_map.items():
            if any(kw in node_content for kw in keywords):
                return agent

        # 默认: 如果节点ID包含"kp"用oral-explanation, 否则用clarification-path
        return "clarification-path"

    def analyze_and_group(self):
        """
        分析节点并智能分组 (Phase 4)

        Returns:
            agent_tasks: List[Dict] - Agent任务列表
        """
        for node in self.yellow_nodes:
            node_id = node['id']

            # 提取节点内容
            if node['type'] == 'file':
                node_content = node.get('file', '')
            elif node['type'] == 'text':
                node_content = node.get('text', '')
            else:
                node_content = ''

            # 智能匹配Agent
            agent_name = self.intelligent_agent_matching(node_content)

            self.agent_tasks.append({
                "node_id": node_id,
                "agent_name": agent_name,
                "node_content": node_content,
                "node_type": node['type'],
                "x": node['x'],
                "y": node['y']
            })

    def generate_parallel_task_prompts(self) -> list:
        """
        生成并行Task调用的prompt列表 (Phase 5准备)

        Returns:
            List of dicts with agent_name and prompt
        """
        task_prompts = []

        for task in self.agent_tasks:
            agent_name = task['agent_name']
            node_content = task['node_content']

            # 构造Agent专属prompt
            prompt = f"""
Use the {agent_name} subagent to generate AI explanation for the following node.

Node ID: {task['node_id']}
Content: {node_content}
Canvas Path: {self.canvas_path}

Expected output: High-quality markdown document following {agent_name} format.
"""

            task_prompts.append({
                "agent_name": agent_name,
                "prompt": prompt,
                "node_id": task['node_id']
            })

        return task_prompts

    def run(self) -> dict:
        """
        完整执行流程

        Returns:
            执行结果字典
        """
        # Step 1: 加载Canvas
        self.load_canvas()

        # Step 2: 提取黄色节点
        self.extract_yellow_nodes()

        if not self.yellow_nodes:
            return {
                "success": False,
                "message": "未找到黄色节点",
                "yellow_nodes_count": 0
            }

        # Step 3: 智能分组
        self.analyze_and_group()

        # Step 4: 生成parallel task prompts
        task_prompts = self.generate_parallel_task_prompts()

        # 返回结果供canvas-orchestrator使用
        return {
            "success": True,
            "yellow_nodes_count": len(self.yellow_nodes),
            "agent_tasks": self.agent_tasks,
            "task_prompts": task_prompts,
            "agent_distribution": self._get_agent_distribution()
        }

    def _get_agent_distribution(self) -> dict:
        """统计Agent分布"""
        distribution = {}
        for task in self.agent_tasks:
            agent = task['agent_name']
            distribution[agent] = distribution.get(agent, 0) + 1
        return distribution


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python intelligent_parallel_orchestrator.py <canvas_path>"
        }))
        sys.exit(1)

    canvas_path = sys.argv[1]

    orchestrator = IntelligentParallelOrchestrator(canvas_path)
    result = orchestrator.run()

    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

**Step 3**: 在canvas-orchestrator.md中添加调用逻辑

```markdown
### 批量并行处理工作流

**触发条件**: 用户输入包含"批量"关键词

**执行步骤**:

1. **调用智能分析脚本**:
```python
import subprocess
import json

result = subprocess.run(
    ["python", "scripts/intelligent_parallel_orchestrator.py", canvas_path],
    capture_output=True,
    text=True
)

analysis = json.loads(result.stdout)

if not analysis['success']:
    print(f"❌ {analysis['message']}")
    exit()
```

2. **展示分析结果给用户**:
```
📊 智能分析完成:
  - 黄色节点: {analysis['yellow_nodes_count']}个
  - Agent分配:
    • clarification-path: {count}个
    • oral-explanation: {count}个
    • memory-anchor: {count}个
```

3. **并行调用所有Agent (Phase 5核心)**:

在**单个Claude响应**中执行:
```
for task_prompt in analysis['task_prompts']:
    Task(
        subagent_type=task_prompt['agent_name'],
        prompt=task_prompt['prompt']
    )
```

4. **收集所有Agent返回结果**

5. **批量更新Canvas**:
   - 为每个Agent结果创建蓝色节点
   - 添加连接边
   - 一次性保存Canvas

6. **向用户反馈**:
```
✅ 批量并行处理完成！

执行统计:
  - 并行执行时间: ~8秒
  - 生成文档: {count}个
  - Canvas更新: +{count}节点, +{count}边

生成的文档:
  1. {doc1}
  2. {doc2}
  ...
```
```

---

### 方案2: 创建新的Parallel-Orchestrator Agent (备选)

**优势**:
- 职责更清晰
- 独立维护
- 可复用于其他场景

**劣势**:
- 用户需要区分不同Agent
- 增加系统复杂度

**实现**:

创建 `.claude/agents/parallel-orchestrator.md`:

```markdown
---
name: parallel-orchestrator
description: Intelligent parallel processing orchestrator for batch Canvas operations
model: sonnet
---

# Parallel Orchestrator - 智能并行处理协调器

## Role

专门负责Canvas学习系统的批量并行处理任务，整合Epic 10的核心能力：
1. 智能内容分析
2. 智能Agent匹配
3. 异步并行执行

## Input

用户通过canvas-orchestrator转发的批量处理请求

## 核心能力

### 1. 智能内容分析 (Phase 4)
- 自动提取黄色节点
- 分析节点内容特征
- 智能匹配最佳Agent

### 2. 并行执行 (Phase 5)
- 单响应多Task并发调用
- 4倍性能提升
- 一次性返回所有结果

## Workflow

[详细工作流程...]
```

**调用方式**:

在canvas-orchestrator中:
```markdown
### 批量操作调度

当识别到批量操作意图时，调用parallel-orchestrator:

```python
Task(
    subagent_type="parallel-orchestrator",
    prompt=f"Process all yellow nodes in {canvas_path}"
)
```
```

---

## 🎯 推荐集成方案: 方案1 (扩展canvas-orchestrator)

**理由**:
1. **用户体验**: 单一入口,无需区分Agent
2. **技术简洁**: 复用现有架构
3. **维护性**: 集中维护,易于升级

**实现路径**:

```
1. 创建 scripts/intelligent_parallel_orchestrator.py
   ├─ 智能分组逻辑 (Phase 4)
   └─ Prompt生成逻辑

2. 扩展 canvas-orchestrator.md
   ├─ 新增批量操作意图识别
   ├─ 新增并行执行工作流
   └─ 新增结果整合逻辑

3. 测试完整流程
   └─ @Lecture5.canvas 批量生成所有黄色节点的AI解释
```

---

## 📋 实现检查清单

### Phase 1: 准备阶段
- [ ] 创建 `scripts/intelligent_parallel_orchestrator.py`
- [ ] 实现智能分组逻辑 (Phase 4核心)
- [ ] 实现Prompt生成逻辑
- [ ] 单元测试: 测试分组准确性

### Phase 2: 集成canvas-orchestrator
- [ ] 在canvas-orchestrator.md添加批量操作识别
- [ ] 添加调用intelligent_parallel_orchestrator.py的逻辑
- [ ] 添加并行Task调用逻辑 (Phase 5核心)
- [ ] 添加结果整合和Canvas更新逻辑

### Phase 3: 用户反馈优化
- [ ] 设计清晰的进度反馈
- [ ] 添加错误处理和重试机制
- [ ] 添加执行统计和性能报告

### Phase 4: 测试验证
- [ ] 测试用例1: 批量处理4个黄色节点
- [ ] 测试用例2: 批量处理含不同类型节点
- [ ] 测试用例3: 错误场景（无黄色节点）
- [ ] 性能测试: 对比串行vs并行执行时间

### Phase 5: 文档完善
- [ ] 更新canvas-orchestrator.md
- [ ] 创建用户使用指南
- [ ] 更新CLAUDE.md项目概览

---

## 🚀 执行时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| Phase 1 | 创建orchestrator脚本 | 30分钟 |
| Phase 2 | 集成到canvas-orchestrator | 45分钟 |
| Phase 3 | 用户反馈优化 | 30分钟 |
| Phase 4 | 测试验证 | 30分钟 |
| Phase 5 | 文档完善 | 15分钟 |
| **总计** | | **~2.5小时** |

---

## 📊 预期效果

**集成前** (当前):
```
用户: @file.canvas 生成Level Set的澄清文档
系统: [调用clarification-path] → 返回1个文档

用户: @file.canvas 生成线性逼近的口语化解释
系统: [调用oral-explanation] → 返回1个文档

... (重复4次)
总耗时: ~30-40秒
```

**集成后** (Epic 10):
```
用户: @file.canvas 批量生成所有黄色节点的AI解释
系统:
  [智能分析] → 4个节点
  [智能匹配] → clarification-path(1), oral-explanation(1), memory-anchor(2)
  [并行执行] → 同时调用4个Agent
  [批量更新] → +4节点, +4边

总耗时: ~8-10秒 (4倍提升!)
```

---

## 💡 未来扩展

### 扩展1: 智能推荐

用户输入模糊时，系统智能推荐:

```
用户: @file.canvas 帮我处理这些节点
系统:
  检测到4个黄色节点，建议操作:
  1. 批量生成AI解释（推荐）
  2. 批量评分
  3. 自定义...

  请选择操作类型（输入1-3）
```

### 扩展2: 增量并行

支持增量更新:

```
用户: @file.canvas 批量生成新增黄色节点的AI解释
系统:
  [智能检测] → 2个新节点（未生成蓝色节点）
  [并行执行] → 仅处理新节点
```

### 扩展3: 跨Canvas并行

同时处理多个Canvas:

```
用户: @离散数学.canvas @线性代数.canvas 批量生成所有AI解释
系统:
  [分析] → 离散数学5个节点, 线性代数3个节点
  [并行执行] → 8个Agent同时调用
```

---

## 🎯 结论

**推荐实施方案1**: 扩展canvas-orchestrator.md

**核心优势**:
- ✅ 用户体验统一（单一入口）
- ✅ 技术实现简洁（复用现有架构）
- ✅ 性能提升显著（4倍加速）
- ✅ 维护成本低（集中管理）

**下一步**:
1. 创建 `scripts/intelligent_parallel_orchestrator.py`
2. 扩展 `canvas-orchestrator.md`
3. 测试完整流程
4. 更新用户文档

**预期完成时间**: ~2.5小时

---

**文档版本**: v1.0
**创建日期**: 2025-11-04
**状态**: 设计完成,待实施

**准备实施Epic 10集成！ 🚀**
