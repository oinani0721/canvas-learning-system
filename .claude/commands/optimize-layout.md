---
name: optimize-layout
description: 优化Canvas布局，支持智能对齐、间距调整和聚类排列
tools: Read, Write, Edit
model: sonnet
---

# Canvas布局优化命令

## 用法

```bash
/optimize-layout [Canvas文件路径] [选项]
```

## 功能

自动优化Canvas文件中的节点布局，包括：

1. **黄色节点精确定位** - 确保黄色节点严格位于问题节点正下方30px处
2. **多种对齐方式** - 支持左对齐、居中对齐、右对齐
3. **智能间距调整** - 自动避免节点重叠，优化视觉间距
4. **聚类优化** - 同主题节点自动分组排列
5. **布局质量评估** - 提供布局质量分数和改进建议

## 参数

- `Canvas文件路径`: 要优化的Canvas文件路径（必需）
- `--alignment, -a`: 对齐方式 (left/center/right，默认center)
- `--mode, -m`: 优化模式 (auto/alignment/spacing/clustering，默认auto)
- `--no-backup`: 跳过优化前的备份创建
- `--preview, -p`: 仅预览优化效果，不实际修改文件
- `--suggestions, -s`: 仅显示布局优化建议

## 示例

```bash
# 基本布局优化
/optimize-layout 离散数学.canvas

# 指定对齐方式
/optimize-layout 离散数学.canvas --alignment center

# 仅优化对齐
/optimize-layout 离散数学.canvas --mode alignment

# 预览优化效果
/optimize-layout 离散数学.canvas --preview

# 查看优化建议
/optimize-layout 离散数学.canvas --suggestions
```

## 输出格式

```
Canvas布局优化完成
📁 文件: 离散数学.canvas
⏱️ 耗时: 1.2秒
🎯 质量分数: 8.5/10

优化统计:
• 节点总数: 25
• 重叠修复: 3个
• 对齐调整: 5个
• 聚类优化: 2个

主要变更:
✅ 调整了3个黄色节点的水平位置
✅ 修复了2个节点重叠问题
✅ 重新排列了1个问题聚类

备份信息:
📸 快照ID: snap-20250121-143000
💾 可使用 /undo-layout 恢复
```

## 注意事项

- 优化前会自动创建布局快照，支持撤销操作
- 大型Canvas（100+节点）可能需要更长时间处理
- 优化结果会自动保存，无需手动保存
- 支持与现有v1.1布局算法完全兼容