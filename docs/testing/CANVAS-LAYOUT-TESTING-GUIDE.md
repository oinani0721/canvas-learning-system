# Canvas学习系统布局测试指南

## 📋 测试概述

本文档提供了Canvas学习系统布局优化的完整测试方案，包含测试Canvas文件、测试场景和验证标准。

## 🎯 测试目标

验证新的G6智能布局算法能否解决以下问题：

1. **黄色节点精确定位** - 确保严格在材料节点正下方
2. **树状图结构清晰** - 明确的父子层次关系
3. **布局美观性** - 合理的节点间距和对齐
4. **布局一致性** - 相同输入产生一致的布局结果

## 📁 测试文件

### 主测试文件
- **文件位置**: `笔记库/测试/canvas-layout-test-suite.canvas`
- **设计目的**: 模拟真实学习场景，包含多种节点类型和关系
- **节点统计**:
  - 材料节点: 3个 (material-001, material-002, material-003)
  - 问题节点: 4个 (2个红色基础问题, 2个紫色进阶问题)
  - 理解节点: 10个 (黄色空白节点)
  - 解释节点: 3个 (蓝色AI解释)

### 布局场景测试

#### 场景1: 基础材料-问题-理解三元组
```
材料节点 → 问题节点 → 理解节点
```
**验证点**:
- 黄色理解节点是否严格在问题节点正下方
- x坐标对齐误差应 < 5px
- y坐标间距应符合规范 (height + 30px)

#### 场景2: 多问题并行布局
```
材料节点 → 问题1 → 理解1
        → 问题2 → 理解2
```
**验证点**:
- 两个问题分支的垂直对齐
- 分支间的水平间距 (建议100px)
- 整体布局的对称性

#### 场景3: 补充解释节点布局
```
理解节点 → 解释节点 → 理解节点
```
**验证点**:
- 解释节点的位置是否合理
- 二级理解节点的对齐
- 避免节点重叠

#### 场景4: 复杂树状结构
```
材料 → 问题1 → 理解1 → 解释1 → 理解2
      → 问题2 → 理解2
      → 理解0
```
**验证点**:
- 多层级树状结构的清晰度
- 同级节点的水平对齐
- 层级间的垂直间距

## 🔧 测试执行流程

### Step 1: 基础布局测试
```bash
# 使用G6布局算法处理测试文件
python g6_canvas_optimizer.py --input "笔记库/测试/canvas-layout-test-suite.canvas" --output "笔记库/测试/test-output-1.canvas"
```

### Step 2: 布局质量验证
检查生成的输出文件是否符合以下标准：

1. **坐标精度验证**
   ```python
   # 验证黄色节点对齐
   def check_yellow_alignment(canvas_data):
       for edge in canvas_data['edges']:
           if edge['toNode'].startswith('yellow') and edge['fromNode'].startswith('question'):
               question_node = find_node(edge['fromNode'])
               yellow_node = find_node(edge['toNode'])

               # x坐标对齐检查
               expected_x = question_node['x'] + 50
               actual_x = yellow_node['x']
               alignment_error = abs(actual_x - expected_x)

               assert alignment_error < 5, f"黄色节点x坐标对齐误差: {alignment_error}px"

               # y坐标间距检查
               expected_y = question_node['y'] + question_node['height'] + 30
               actual_y = yellow_node['y']
               spacing_error = abs(actual_y - expected_y)

               assert spacing_error < 5, f"黄色节点y坐标间距误差: {spacing_error}px"
   ```

2. **树状结构验证**
   ```python
   # 验证树状层次结构
   def verify_tree_structure(canvas_data):
       levels = calculate_node_levels(canvas_data)

       # 同级节点y坐标应该相近
       for level, nodes in levels.items():
           y_coords = [node['y'] for node in nodes]
           y_variance = max(y_coords) - min(y_coords)
           assert y_variance < 50, f"同级节点y坐标差异过大: {y_variance}px"
   ```

### Step 3: 迭代优化测试
1. **手动调整**: 在Obsidian中打开输出文件，手动调整布局
2. **记录调整**: 使用布局偏好学习器记录调整
3. **重新生成**: 基于学习到的偏好重新生成布局
4. **对比验证**: 验证新布局是否更符合用户期望

## 📊 验收标准

### 功能性标准
- ✅ 黄色节点100%对齐到问题节点正下方
- ✅ 树状结构层级清晰可见
- ✅ 无节点重叠或遮挡
- ✅ 所有连接边正确绘制

### 性能标准
- ✅ 布局计算时间 < 2秒 (100节点以内)
- ✅ 布局结果一致性 (相同输入产生相同输出)
- ✅ 内存使用 < 500MB

### 用户体验标准
- ✅ 布局美观，符合直觉
- ✅ 信息层次清晰
- ✅ 易于阅读和理解

## 🐛 常见问题排查

### 问题1: 黄色节点位置偏移
**可能原因**:
- G6布局算法参数设置不当
- Canvas坐标系转换错误
- 节点尺寸计算错误

**解决方案**:
1. 检查`layout_cfg`配置
2. 验证`_canvas_to_g6()`转换函数
3. 确认节点width/height属性

### 问题2: 节点重叠
**可能原因**:
- 节点间距设置过小
- 布局算法选择不当
- 复杂结构处理有误

**解决方案**:
1. 增加`nodeSep`和`rankSep`参数
2. 尝试不同的布局算法 (compactBox, dendrogram)
3. 检查层级计算逻辑

### 问题3: 布局不一致
**可能原因**:
- 随机种子未固定
- 异步处理竞态条件
- 缓存机制问题

**解决方案**:
1. 设置固定的随机种子
2. 确保布局计算的同步性
3. 检查缓存键生成逻辑

## 📈 测试报告模板

```
# Canvas布局测试报告

## 测试环境
- 测试日期: YYYY-MM-DD
- 测试文件: canvas-layout-test-suite.canvas
- 算法版本: G6 v4.8.21

## 测试结果
### 对齐精度
- 黄色节点x对齐平均误差: __ px
- 黄色节点y间距平均误差: __ px
- 最大对齐误差: __ px

### 布局质量
- 树状结构清晰度: ⭐⭐⭐⭐⭐
- 节点重叠数量: 0
- 边交叉数量: __

### 性能指标
- 布局计算时间: __ ms
- 内存使用峰值: __ MB
- 输出文件大小: __ KB

## 问题记录
1. [问题描述]
   - 复现步骤:
   - 期望结果:
   - 实际结果:
   - 严重程度: 低/中/高

## 改进建议
1. [具体建议]
```

## 🚀 自动化测试脚本

```python
# 自动化布局测试
import asyncio
from g6_canvas_optimizer import G6CanvasOptimizer

async def run_layout_tests():
    optimizer = G6CanvasOptimizer()

    test_cases = [
        "笔记库/测试/canvas-layout-test-suite.canvas",
        # 可以添加更多测试文件
    ]

    results = []
    for test_file in test_cases:
        result = await optimizer.optimize_layout(test_file)
        results.append(result)

        # 验证布局质量
        quality_score = evaluate_layout_quality(result['output_file'])
        print(f"{test_file}: 质量评分 {quality_score}/100")

    return results

def evaluate_layout_quality(output_file):
    """评估布局质量的综合得分"""
    # 实现具体的质量评估逻辑
    pass

if __name__ == "__main__":
    asyncio.run(run_layout_tests())
```

## 📝 测试检查清单

- [ ] 测试文件已创建并验证格式正确
- [ ] G6布局算法正常工作
- [ ] 黄色节点对齐精度验证通过
- [ ] 树状结构清晰度验证通过
- [ ] 性能指标达到预期
- [ ] 用户体验评估完成
- [ ] 问题记录和解决方案文档化
- [ ] 自动化测试脚本可用
- [ ] 测试报告生成并归档

---

**最后更新**: 2025-10-18
**负责人**: Canvas学习系统开发团队
**版本**: v1.0
