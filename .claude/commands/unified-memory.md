# Canvas v2.0 统一记忆系统命令

## 命令描述

提供Canvas v2.0统一记忆系统的完整操作接口，整合时序记忆(Graphiti)和语义记忆(MCP)系统。

## 命令实现

```python
# 统一记忆系统斜杠命令实现
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 导入统一记忆系统组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from memory_system import (
        UnifiedMemoryInterface,
        TemporalMemoryManager,
        SemanticMemoryManager,
        MemoryConsistencyValidator,
        GracefulDegradationManager,
        UnifiedMemoryEntry,
        MemoryType,
        LearningState
    )
    from canvas_memory_integration import create_enhanced_canvas_orchestrator
except ImportError as e:
    print(f"❌ 导入统一记忆系统失败: {e}")
    print("请确保Story 8.19已正确部署")

def get_unified_memory_system():
    """获取统一记忆系统实例"""
    try:
        # 创建增强的Canvas编排器（包含统一记忆系统）
        enhanced_orchestrator = create_enhanced_canvas_orchestrator()
        return enhanced_orchestrator.unified_memory
    except Exception as e:
        print(f"❌ 创建统一记忆系统失败: {e}")
        return None

def format_memory_info(memory_entry: UnifiedMemoryEntry) -> str:
    """格式化记忆信息显示"""
    created_time = memory_entry.created_at.strftime("%Y-%m-%d %H:%M:%S")
    updated_time = memory_entry.updated_at.strftime("%Y-%m-%d %H:%M:%S")

    return f"""
📝 **记忆信息**
- 🆔 ID: {memory_entry.memory_id[:8]}...
- 🎨 Canvas: {memory_entry.canvas_id}
- 🔗 节点: {memory_entry.node_id}
- 📊 类型: {memory_entry.memory_type.value}
- ⏰ 创建: {created_time}
- 🔄 更新: {updated_time}
- 📄 内容: {memory_entry.content[:100]}{'...' if len(memory_entry.content) > 100 else ''}
"""

# ==================== 核心命令实现 ====================

async def cmd_unified_memory_status(args: str = "") -> str:
    """查看统一记忆系统状态"""
    unified_memory = get_unified_memory_system()
    if not unified_memory:
        return "❌ 统一记忆系统不可用"

    try:
        # 获取系统状态
        status = await unified_memory.get_system_status()

        # 获取健康检查结果
        health_status = await unified_memory.health_check()

        return f"""
🧠 **Canvas v2.0 统一记忆系统状态**

📊 **系统状态**: {status['status'].upper()}
- 🔄 临时记忆: {'✅ 正常' if status['temporal_memory_available'] else '❌ 不可用'}
- 🧠 语义记忆: {'✅ 正常' if status['semantic_memory_available'] else '❌ 不可用'}
- 🔗 一致性验证: {'✅ 启用' if status['consistency_validator_enabled'] else '❌ 禁用'}
- 🛡️ 优雅降级: {'✅ 启用' if status['graceful_degradation_enabled'] else '❌ 禁用'}

📈 **性能指标**:
- 📊 总记忆数: {status['total_memories']}
- 🔗 关联数: {status['total_links']}
- ⚡ 平均响应时间: {status['avg_response_time_ms']}ms
- 📈 成功率: {status['success_rate']}%

🏥 **健康检查**: {health_status['overall_health'].upper()}
- 📊 分数: {health_status['health_score']}/100
- 📝 检查详情: {len(health_status['checks'])}项检查
"""
    except Exception as e:
        return f"❌ 获取系统状态失败: {e}"

async def cmd_store_learning_memory(args: str) -> str:
    """存储学习记忆

    用法: /unified-memory-store <canvas_id> <node_id> <content> [learning_state] [confidence_score]
    示例: /unified-memory-store 离散数学 123 "逆否命题的理解" yellow 0.7
    """
    if not args or len(args.split()) < 3:
        return """
❌ 参数不足
📖 **用法**: /unified-memory-store <canvas_id> <node_id> <content> [learning_state] [confidence_score]

📝 **参数说明**:
- canvas_id: Canvas白板ID
- node_id: 节点ID
- content: 学习内容（用引号包围）
- learning_state: 学习状态 (red/yellow/purple/green，默认: red)
- confidence_score: 置信度 0-1 (默认: 0.0)

💡 **示例**: /unified-memory-store 离散数学 123 "我理解了逆否命题" yellow 0.7
"""

    parts = args.split(' ', 3)
    if len(parts) < 4:
        return "❌ 内容参数必须用引号包围"

    canvas_id, node_id, content_part = parts[0], parts[1], parts[2:]

    # 解析剩余参数
    remaining = ' '.join(content_part)
    content_match = remaining.split('"')
    if len(content_match) < 2:
        return "❌ 内容必须用双引号包围"

    content = content_match[1]
    params = content_match[2].strip().split() if len(content_match) > 2 else []

    learning_state = params[0] if len(params) > 0 else "red"
    confidence_score = float(params[1]) if len(params) > 1 else 0.0

    unified_memory = get_unified_memory_system()
    if not unified_memory:
        return "❌ 统一记忆系统不可用"

    try:
        memory_id = await unified_memory.store_complete_learning_memory(
            canvas_id=canvas_id,
            node_id=node_id,
            content=content,
            learning_state=learning_state,
            confidence_score=confidence_score
        )

        return f"""
✅ **学习记忆存储成功**

🆔 **记忆ID**: {memory_id[:8]}...
📚 **Canvas**: {canvas_id}
🔗 **节点**: {node_id}
📊 **学习状态**: {learning_state}
🎯 **置信度**: {confidence_score}
⏰ **存储时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

💡 记忆已同时存储到时序记忆和语义记忆系统，并建立了关联关系。
"""
    except Exception as e:
        return f"❌ 存储学习记忆失败: {e}"

async def cmd_retrieve_memory(args: str) -> str:
    """检索记忆

    用法: /unified-memory-retrieve <query> [canvas_id] [limit]
    示例: /unified-memory-retrieve 逆否命题 离散数学 5
    """
    if not args:
        return """
❌ 参数不足
📖 **用法**: /unified-memory-retrieve <query> [canvas_id] [limit]

📝 **参数说明**:
- query: 搜索关键词
- canvas_id: 限定Canvas范围 (可选)
- limit: 结果数量限制 (默认: 10)

💡 **示例**: /unified-memory-retrieve 逆否命题 离散数学 5
"""

    parts = args.split()
    query = parts[0]
    canvas_id = parts[1] if len(parts) > 1 else None
    limit = int(parts[2]) if len(parts) > 2 else 10

    unified_memory = get_unified_memory_system()
    if not unified_memory:
        return "❌ 统一记忆系统不可用"

    try:
        memories = await unified_memory.retrieve_contextual_memory(
            query=query,
            canvas_id=canvas_id,
            limit=limit
        )

        if not memories:
            return f"🔍 未找到与 '{query}' 相关的记忆"

        result = f"""
🔍 **记忆检索结果** (关键词: {query})
📊 找到 {len(memories)} 条相关记忆:
"""

        for i, memory in enumerate(memories, 1):
            result += f"""
---
**{i}. {memory.memory_id[:8]}...**
📚 Canvas: {memory.canvas_id}
🔗 节点: {memory.node_id}
📊 类型: {memory.memory_type.value}
📄 内容: {memory.content[:150]}{'...' if len(memory.content) > 150 else ''}
⏰ {memory.created_at.strftime("%Y-%m-%d %H:%M:%S")}
"""

        return result
    except Exception as e:
        return f"❌ 检索记忆失败: {e}"

async def cmd_memory_consistency_check(args: str = "") -> str:
    """执行记忆一致性检查"""
    unified_memory = get_unified_memory_system()
    if not unified_memory:
        return "❌ 统一记忆系统不可用"

    try:
        report = await unified_memory.validate_all_memory_consistency()

        status = "✅ 一致" if report.is_consistent else "⚠️ 发现问题"

        result = f"""
🔍 **记忆一致性检查报告**

📊 **总体状态**: {status}
📈 **一致性分数**: {report.consistency_score}/100
🔍 **检查条目**: {report.total_checked}条记忆, {report.total_links_checked}个关联
⏰ **检查时间**: {report.check_duration_seconds}秒

📋 **问题详情**:
"""

        if report.issues:
            for issue in report.issues:
                result += f"- ❌ {issue['type']}: {issue['description']}\n"
        else:
            result += "- ✅ 未发现一致性问题\n"

        if report.auto_repairs:
            result += "\n🔧 **自动修复**:\n"
            for repair in report.auto_repairs:
                result += f"- 🔧 {repair['action']}: {repair['description']}\n"

        return result
    except Exception as e:
        return f"❌ 一致性检查失败: {e}"

async def cmd_memory_links(args: str) -> str:
    """查看记忆关联

    用法: /unified-memory-links <memory_id>
    示例: /unified-memory-links abc12345
    """
    if not args:
        return """
❌ 参数不足
📖 **用法**: /unified-memory-links <memory_id>

💡 **示例**: /unified-memory-links abc12345
"""

    memory_id = args.strip()
    unified_memory = get_unified_memory_system()
    if not unified_memory:
        return "❌ 统一记忆系统不可用"

    try:
        links = await unified_memory.get_memory_links(memory_id)

        if not links:
            return f"🔗 记忆 {memory_id[:8]}... 没有关联"

        result = f"""
🔗 **记忆关联信息** (ID: {memory_id[:8]}...)

📊 找到 {len(links)} 个关联:
"""

        for i, link in enumerate(links, 1):
            strength_icon = "🔴" if link.strength < 0.3 else "🟡" if link.strength < 0.7 else "🟢"
            result += f"""
**{i}. {link.link_type.upper()}**
{strength_icon} 强度: {link.strength:.2f}
🎯 目标: {link.target_memory_id[:8]}...
⏰ 创建: {link.created_at.strftime("%Y-%m-%d %H:%M:%S")}
"""

        return result
    except Exception as e:
        return f"❌ 获取记忆关联失败: {e}"

async def cmd_memory_analytics(args: str = "") -> str:
    """记忆分析统计"""
    unified_memory = get_unified_memory_system()
    if not unified_memory:
        return "❌ 统一记忆系统不可用"

    try:
        analytics = await unified_memory.get_memory_analytics()

        return f"""
📊 **记忆分析统计**

📈 **总量统计**:
- 📝 总记忆数: {analytics['total_memories']}
- 🔗 总关联数: {analytics['total_links']}
- 📚 Canvas数量: {analytics['canvas_count']}

🎯 **类型分布**:
- 🕐 时序记忆: {analytics['temporal_count']} ({analytics['temporal_percentage']}%)
- 🧠 语义记忆: {analytics['semantic_count']} ({analytics['semantic_percentage']}%)
- 🔄 统一记忆: {analytics['unified_count']} ({analytics['unified_percentage']}%)

📊 **学习状态分布**:
- 🔴 红色(不理解): {analytics['learning_states']['red']}
- 🟡 黄色(理解中): {analytics['learning_states']['yellow']}
- 🟣 紫色(部分理解): {analytics['learning_states']['purple']}
- 🟢 绿色(完全理解): {analytics['learning_states']['green']}

⏰ **时间统计**:
- 📅 今日新增: {analytics['today_new_memories']}
- 📅 本周新增: {analytics['week_new_memories']}
- 📅 本月新增: {analytics['month_new_memories']}
"""
    except Exception as e:
        return f"❌ 获取记忆分析失败: {e}"

# ==================== 命令注册表 ====================

COMMANDS = {
    "unified-memory-status": cmd_unified_memory_status,
    "unified-memory-store": cmd_store_learning_memory,
    "unified-memory-retrieve": cmd_retrieve_memory,
    "unified-memory-check": cmd_memory_consistency_check,
    "unified-memory-links": cmd_memory_links,
    "unified-memory-analytics": cmd_memory_analytics,
}

COMMAND_DESCRIPTIONS = {
    "unified-memory-status": "查看统一记忆系统状态和健康指标",
    "unified-memory-store": "存储学习记忆到时序和语义系统",
    "unified-memory-retrieve": "检索相关记忆内容",
    "unified-memory-check": "执行记忆一致性检查和修复",
    "unified-memory-links": "查看记忆的关联关系",
    "unified-memory-analytics": "查看记忆系统统计分析",
}

# ==================== 主要执行函数 ====================

async def execute_unified_memory_command(command: str, args: str = "") -> str:
    """执行统一记忆系统命令"""
    if command not in COMMANDS:
        available = ", ".join([f"/{cmd}" for cmd in COMMANDS.keys()])
        return f"❌ 未知命令: /{command}\n可用命令: {available}"

    try:
        return await COMMANDS[command](args)
    except Exception as e:
        return f"❌ 执行命令 /{command} 失败: {e}"

def get_command_help():
    """获取命令帮助信息"""
    help_text = """
🧠 **Canvas v2.0 统一记忆系统命令**

"""
    for cmd, desc in COMMAND_DESCRIPTIONS.items():
        help_text += f"**/{cmd}** - {desc}\n"

    help_text += """
💡 **使用示例**:
- /unified-memory-status  # 查看系统状态
- /unified-memory-store 离散数学 node123 "我理解了逆否命题" yellow 0.8
- /unified-memory-retrieve 逆否命题
- /unified-memory-check  # 检查一致性
- /unified-memory-analytics  # 查看统计分析

📚 **说明**: 统一记忆系统整合了时序记忆(Graphiti)和语义记忆(MCP)，提供完整的Canvas学习记忆管理功能。
"""
    return help_text
```

## 使用说明

### 基本命令

1. **查看系统状态**
   ```
   /unified-memory-status
   ```

2. **存储学习记忆**
   ```
   /unified-memory-store <canvas_id> <node_id> "<content>" [learning_state] [confidence_score]
   ```

3. **检索记忆**
   ```
   /unified-memory-retrieve <keyword> [canvas_id] [limit]
   ```

4. **一致性检查**
   ```
   /unified-memory-check
   ```

5. **查看记忆关联**
   ```
   /unified-memory-links <memory_id>
   ```

6. **记忆分析统计**
   ```
   /unified-memory-analytics
   ```

### 日常使用场景

1. **学习时自动记录**: 使用Canvas操作时自动存储记忆
2. **复习时检索**: 搜索相关概念的历史记忆
3. **知识关联**: 查看概念之间的关联关系
4. **学习分析**: 查看学习进度和记忆分布

## 技术特性

- ✅ 统一接口整合时序和语义记忆
- ✅ 异步操作支持高并发
- ✅ 自动一致性验证和修复
- ✅ 优雅降级保证系统稳定
- ✅ 详细的性能监控和分析
- ✅ 完整的错误处理和日志

## 注意事项

1. 需要Story 8.19统一记忆系统已部署
2. 命令参数区分大小写
3. 内容参数必须用双引号包围
4. 系统会自动处理时序和语义记忆的同步

---

**版本**: Canvas v2.0 统一记忆系统
**兼容**: Story 8.19 统一记忆接口
**维护**: Canvas Learning System Team