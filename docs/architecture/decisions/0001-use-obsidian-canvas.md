# 1. 使用Obsidian Canvas作为可视化知识图谱载体

Date: 2025-10-15

## Status

Accepted

## Context

Canvas Learning System需要一个可视化的知识图谱载体来实现费曼学习法的数字化，需要满足以下需求：

1. **可视化要求**:
   - 支持节点和边的可视化布局
   - 支持颜色系统区分理解状态（红/绿/紫/蓝/黄）
   - 支持文本节点和文件引用节点
   - 用户可直观查看学习进度和知识结构

2. **数据格式要求**:
   - 数据格式必须是结构化的（便于程序读写）
   - 支持节点属性（id, type, x, y, width, height, color, text/file）
   - 支持边属性（id, fromNode, toNode, fromSide, toSide）
   - 格式必须稳定且有明确规范

3. **工具生态要求**:
   - 用户能够手动编辑和查看
   - 支持跨平台（Windows, macOS, Linux）
   - 有活跃的社区和插件生态
   - 免费或低成本

4. **集成要求**:
   - Python可以轻松读写（JSON格式优先）
   - Claude Code可以通过工具调用操作
   - 支持与Markdown文档的链接

### 候选方案对比

我们评估了以下候选方案：

| 方案 | 优点 | 缺点 | 评分 |
|------|------|------|------|
| **Obsidian Canvas** | • JSON格式，易于解析<br>• 活跃社区<br>• 跨平台免费<br>• 与Markdown无缝集成<br>• 支持所有所需特性 | • 文档格式不够公开<br>• 依赖Obsidian应用 | ⭐⭐⭐⭐⭐ |
| Mermaid图表 | • 纯文本，易于版本控制<br>• Markdown原生支持 | • 不支持自由布局<br>• 颜色系统有限<br>• 无交互编辑 | ⭐⭐ |
| Excalidraw | • 手绘风格，美观<br>• JSON格式 | • 主要面向绘图而非知识管理<br>• 节点结构不适合程序化操作<br>• 无颜色语义系统 | ⭐⭐⭐ |
| D3.js自定义图谱 | • 完全自定义<br>• 强大的可视化能力 | • 需要开发前端界面<br>• 用户学习成本高<br>• 开发周期长 | ⭐⭐ |
| Neo4j图数据库 | • 专业图数据库<br>• 强大的查询能力 | • 不适合可视化编辑<br>• 用户界面缺失<br>• 需要服务器部署 | ⭐⭐ |

## Decision

我们决定使用**Obsidian Canvas**作为Canvas Learning System的可视化知识图谱载体。

**选择理由**:

1. **JSON格式完美匹配Python开发**:
   - Canvas文件是纯JSON格式（`.canvas`扩展名）
   - Python可以使用`json.load()`直接读取
   - 节点和边的数据结构清晰明确

2. **完整的颜色系统支持**:
   - Obsidian Canvas支持6种颜色（color code: "1"-"6"）
   - 颜色语义可以自定义映射到学习状态
   - 我们的映射: 红(1)=不理解, 绿(2)=完全理解, 紫(3)=似懂非懂, 蓝(5)=AI解释, 黄(6)=个人理解

3. **用户体验优秀**:
   - Obsidian提供直观的可视化编辑界面
   - 支持拖拽布局和连接
   - 跨平台免费使用
   - 与Markdown笔记无缝集成（文件节点可以链接到`.md`文件）

4. **活跃的社区和文档**:
   - Obsidian有大量用户和插件开发者
   - Canvas插件开发有官方文档支持
   - JSON格式规范可以通过逆向工程获得

5. **未来扩展性**:
   - 可以开发Obsidian插件增强功能
   - Canvas格式稳定，向后兼容性好
   - 支持与其他Obsidian生态工具集成

**技术实现**:

我们将开发`canvas_utils.py`作为Canvas文件的读写工具库，提供以下API：

```python
# Layer 1: 底层JSON操作
def read_canvas(canvas_path: str) -> Dict
def write_canvas(canvas_path: str, canvas_data: Dict)
def add_node(canvas_data: Dict, node: Dict) -> str
def add_edge(canvas_data: Dict, edge: Dict) -> str

# Layer 2: 业务逻辑层
def extract_verification_nodes(canvas_data: Dict) -> List[Dict]
def apply_layout_v1_1(canvas_data: Dict) -> Dict

# Layer 3: 高级API
def generate_review_canvas_file(source_path: str, output_path: str) -> str
```

## Consequences

### 正面影响

1. **开发效率提升** ⚡:
   - JSON格式简化了数据读写逻辑
   - 不需要开发自定义前端界面
   - Python生态工具丰富（`json`, `pathlib`等）

2. **用户体验优秀** 👍:
   - 用户已熟悉Obsidian界面，学习成本低
   - 可视化编辑体验流畅
   - 支持快捷键和高效操作

3. **可维护性高** 🔧:
   - 纯文本JSON格式，易于版本控制（Git）
   - 数据结构简单，bug容易定位
   - 不依赖数据库或复杂基础设施

4. **扩展性强** 🚀:
   - 可以通过Obsidian插件扩展功能
   - 可以集成到Obsidian工作流中
   - 未来可以开发Canvas API服务器

### 负面影响

1. **格式依赖性** ⚠️:
   - Canvas格式没有官方公开规范，依赖逆向工程
   - 如果Obsidian更新Canvas格式，需要适配
   - **缓解措施**: 编写完整的单元测试覆盖Canvas格式解析，及时发现格式变化

2. **Obsidian依赖** ⚠️:
   - 用户必须安装Obsidian才能查看和编辑Canvas
   - 对于不使用Obsidian的用户，学习成本增加
   - **缓解措施**: 提供详细的Obsidian安装和使用文档，考虑未来开发Web查看器

3. **颜色系统限制** ⚠️:
   - Obsidian Canvas颜色代码固定（"1"-"6"），无法自定义颜色
   - 只能使用6种颜色，限制了扩展性
   - **缓解措施**: 当前6种颜色足够满足需求（红/绿/紫/蓝/黄+白），未来可以通过节点文本标签补充语义

4. **离线文档不足** ⚠️:
   - Canvas格式缺少官方文档，需要逆向工程
   - 插件开发文档有限
   - **缓解措施**: 创建obsidian-canvas Skill，收集社区文档和示例代码

### 技术债务

- **TODO**: 监控Obsidian版本更新，及时适配Canvas格式变化
- **TODO**: 考虑开发轻量级Web Canvas查看器，减少对Obsidian的依赖
- **TODO**: 收集和整理Canvas格式规范，创建内部文档

### 度量指标

- **Canvas文件读写性能**: <200ms (100节点)
- **用户满意度**: 目标>90% (基于Obsidian社区反馈)
- **格式兼容性**: 目标100% (向后兼容所有历史Canvas文件)

## References

- Obsidian官网: https://obsidian.md/
- Obsidian Canvas插件: https://obsidian.md/canvas
- JSON Canvas Format (社区逆向工程): https://jsoncanvas.org/
- Canvas Learning System PRD: `docs/prd/FULL-PRD-REFERENCE.md` (Epic 1)

## Notes

此决策是Canvas Learning System的**基础性决策**，影响整个系统的架构设计。一旦选定，更换成本极高，因此经过了充分的调研和对比。

**历史背景**: 在项目启动阶段（2025-10-15），我们评估了5种可视化方案，最终Obsidian Canvas以其JSON格式、活跃社区和优秀用户体验脱颖而出，获得⭐⭐⭐⭐⭐评分。

**实施状态**: Epic 1 (核心Canvas操作层) 已完成，证明了此决策的正确性。
