---
name: memory-start
description: 启动Canvas学习实时记忆记录系统 (Story 8.17)
tools: Bash, Read, Write
model: sonnet
---

# Canvas学习实时记忆启动命令

## 功能描述

启动Story 8.17实现的Canvas学习实时记忆集成系统，自动记录您的所有学习活动。

## 使用方式

```bash
/memory-start                    # 启动实时记忆系统
/memory-start --user-id user123  # 为指定用户启动
/memory-start --config custom.yaml  # 使用自定义配置
```

## 启动后功能

✅ **自动记录学习活动**:
- Canvas节点点击和浏览
- Agent调用记录
- 理解输入过程
- 评分结果追踪
- 学习时间统计

✅ **智能分析**:
- 8维度学习模式识别
- 个性化Agent推荐
- 学习进度分析
- 错误模式识别

✅ **数据保护**:
- AES-256加密存储
- 用户隐私保护
- 数据导出功能

## 使用示例

### 基础启动
```bash
/memory-start
```
输出：
```
🚀 Canvas学习记忆系统启动中...
✅ Canvas学习记忆系统已启动
📊 正在监听Canvas学习活动...
🎯 使用说明:
  1. 打开任何Canvas文件开始学习
  2. 系统将自动记录您的学习行为
  3. 按 Ctrl+C 停止记录
```

### 指定用户启动
```bash
/memory-start --user-id your_user_id
```

### 自定义配置启动
```bash
/memory-start --config config/custom_memory_config.yaml
```

## 停止记录

学习完成后按 `Ctrl+C` 停止记录，系统会自动保存所有学习数据。

## 数据保存位置

学习数据保存在：
```
data/realtime_memory/
├── learning_activities/     # 学习活动数据
├── pattern_analysis/        # 学习模式分析
├── personal_insights/       # 个人洞察
└── privacy_controls/        # 隐私控制数据
```

## 依赖要求

- Python 3.9+
- Story 8.17 核心模块已安装
- 配置文件 `config/realtime_memory.yaml` 存在

## 相关命令

- `/memory-stats` - 查看记忆统计
- `/memory-analyze` - 分析学习模式
- `/memory-export` - 导出学习数据
- `/memory-stop` - 停止记忆记录

---

**Story 8.17 实时Canvas记忆集成系统 - 让您的学习过程被智能记录和分析**