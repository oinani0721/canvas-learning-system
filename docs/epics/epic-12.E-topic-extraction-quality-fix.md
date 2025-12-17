# Epic 12.E: Agent 质量综合修复

**Epic ID**: EPIC-12.E
**Epic类型**: Bug修复 + 质量改进 + 功能增强 (Brownfield Enhancement)
**状态**: Ready for Development
**优先级**: P0 Critical
**创建日期**: 2025-12-15
**更新日期**: 2025-12-15 (扩展范围)
**预计完成**: 2025-12-19 (3.5 个工作日)

---

## 目录

1. [Epic概述](#epic概述)
2. [根因分析报告](#根因分析报告)
3. [Epic目标](#epic目标)
4. [现有系统背景](#现有系统背景)
5. [Story概览](#story概览)
6. [验收标准](#验收标准)
7. [技术约束](#技术约束)
8. [风险与缓解](#风险与缓解)
9. [成功指标](#成功指标)
10. [依赖关系](#依赖关系)

---

## Epic概述

### 简述

**综合修复 LangGraph Agent 的 4 个核心质量问题**，对齐 Claude Code Sub Agent 的质量标准：

1. **提示词格式不一致**: 后端 JSON 构建与 Agent 模板期望不匹配 (如 `comparison-table` 需要 `concepts` 数组)
2. **黄色节点传递缺失**: `user_understanding` 仅在 `enhanced_context` 中，未在 JSON 字段中传递
3. **上下文深度不足**: `_find_adjacent_nodes()` 仅 1-hop，需要 2-hop 遍历
4. **图片处理缺失**: 无 Markdown 图片引用提取，未集成多模态 Agent 调用

原始根因：`_extract_topic_from_content()` 只使用第一行作为主题，导致 AI 收到错误的 `topic` 参数。

### 问题陈述

**核心问题**: 用户选择 Canvas 节点后调用 Agent 解释功能，生成的内容与所选节点**完全无关**。

**具体案例**:

| 测试 | 选择节点 | 预期输出 | 实际输出 |
|------|----------|----------|----------|
| 测试1 | Level Set定义 (kp01) | Level Set / 水平集解释 | 特征值和特征向量 |
| 测试2 | Level Set定义 (kp01) | Level Set / 水平集解释 | Transformer 模型 |
| 测试3 | original-lecture | Section 14.1 Level Set | Section 14.5 隐函数求导 |

**问题严重性**:
- **用户信任**: 严重损害 - AI 生成完全无关内容
- **功能可用性**: 0% - 核心功能完全失效
- **数据污染风险**: 高 - 错误内容可能被保存到知识图谱

### 解决方案

实现**智能主题提取机制**：
- 改进 `_extract_topic_from_content()` 跳过元数据行
- 从文件名提取 topic（FILE 类型节点）
- 在 `call_explanation()` 中集成智能 topic 提取逻辑
- 对齐 Claude Code Sub Agent 的主题指定方式

### 预期影响

**质量提升**:
- 主题正确率: 0% → 95%+
- 用户信任: 恢复
- Agent 解释相关性: 显著提升

**架构对齐**:
- LangGraph Agent 主题选择能力对齐 Claude Code Sub Agent
- 消除 Claude Code vs LangGraph 的质量差距

---

## 根因分析报告

### 调研方法

1. **代码追踪**: 从用户点击右键菜单 → nodeContent 传递 → API 请求 → AI Prompt
2. **文件分析**: 前端/后端/Agent模板/Canvas数据
3. **假设验证**: Epic 12.B (参数传递) → Epic 12.C (上下文污染) → Epic 12.D (FILE节点)

### 根因链路图

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code Sub Agent (质量高)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入: clarify "Level Set" from @Lecture5.canvas            │
│                    ↓                                            │
│  topic = "Level Set" (用户显式指定)                              │
│                    ↓                                            │
│  AI 明确知道聚焦 "Level Set" 主题                                │
│                    ↓                                            │
│  生成高质量、主题正确的解释                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  LangGraph Agent (当前实现 - 质量低)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户点击: original-lecture 节点右键菜单                          │
│                    ↓                                            │
│  content = (整个 lecture 文档, 包含多个 Section)                 │
│                    ↓                                            │
│  topic = _extract_topic_from_content(content)                   │
│        = "🧭 知识图谱控制中心..." (第一行, 错误!)                 │
│                    ↓                                            │
│  AI 收到:                                                        │
│    - topic: "🧭 知识图谱控制中心..."                             │
│    - content: 包含 Section 14.1, 14.5, ... 的整个文档            │
│                    ↓                                            │
│  AI 随机选择一个 Section 生成内容 → Section 14.5 隐函数求导       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### BUG 代码定位

#### BUG 位置: `agent_service.py:1089-1127`

```python
def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
    """
    Extract topic/concept name from content.

    Strategy:
    1. Use first line as topic (most common: "概念名" or "# 标题")  ← 只取第一行！
    2. Clean markdown markers and whitespace
    3. Truncate if too long
    """
    if not content or not content.strip():
        return "Unknown"

    # Get first line
    first_line = content.strip().split('\n')[0].strip()  # ← BUG: 只用第一行！

    # Remove markdown heading markers
    if first_line.startswith('#'):
        first_line = first_line.lstrip('#').strip()

    # ... 清理和截断 ...

    return first_line if first_line else "Unknown"
```

#### JSON Prompt 构造: `agent_service.py:1406-1414`

```python
# ✅ Story 12.B.3: Construct JSON-formatted prompt for agent templates
topic = self._extract_topic_from_content(content)  # ← 提取错误的 topic!
json_prompt = json.dumps({
    "material_content": content,
    "topic": topic,                 # ← 可能是 "🧭 知识图谱控制中心..." (元数据!)
    "concept": topic,
    "user_understanding": user_understanding
}, ensure_ascii=False, indent=2)
```

### Agent 模板期望 vs 实际输入

**Agent 模板期望** (来自 `.claude/agents/*.md`):

```json
{
  "material_content": "要解释的材料内容",
  "topic": "主题名称（如：逆否命题、机器学习、量子纠缠等）",  // ← 期望明确的概念名！
  "user_understanding": "用户的个人理解"
}
```

**后端实际提供**:

```json
{
  "material_content": "🧭 **[知识图谱控制中心...]** ...",
  "topic": "🧭 知识图谱控制中心-Lecture5.md...",  // ← 错误的元数据！
  "user_understanding": null
}
```

### 证据汇总

| 证据编号 | 来源 | 内容 |
|----------|------|------|
| E1 | `agent_service.py:1111` | `first_line = content.strip().split('\n')[0]` |
| E2 | `agent_service.py:1408` | `topic = self._extract_topic_from_content(content)` |
| E3 | `澄清路径.md:43` | `clarify "{概念名称}" from @canvas` (Claude Code 用户指定) |
| E4 | `clarification-path.md:14` | `"topic": "主题名称（如：逆否命题）"` (Agent 期望) |
| E5 | Lecture5.canvas | `original-lecture` 节点第一行是导航元数据 |

### 历史错误假设

| Epic | 假设 | 验证结果 |
|------|------|----------|
| 12.B | "node_content 参数没传递" | 错误 - 原因是 FILE 类型不支持 |
| 12.C | "上下文污染覆盖了节点内容" | 错误 - 禁用后问题依然存在 |
| 12.D | "FILE 类型节点不支持" | 部分正确 - 已修复，但 topic 提取仍然失败 |
| **12.E** | **"主题提取机制失效"** | **正确 - 真正根因** |

---

## Epic目标

### 主要目标

**目标1: 智能主题提取**
- 改进 `_extract_topic_from_content()` 跳过元数据行
- 扫描前15行，找到第一个有效标题或内容行
- 跳过 🧭/📋/---/>/[[/http 等元数据前缀

**目标2: 文件名 Topic 提取**
- 为 FILE 类型节点从文件名提取 topic
- `KP01-Level-Set定义.md` → `Level Set定义`
- 作为智能内容扫描的补充

**目标3: 集成智能 Topic 提取**
- 在 `call_explanation()` 中优先使用文件名 topic
- 回退到智能内容扫描
- 对齐 Claude Code Sub Agent 的主题指定能力

### 非目标 (Out of Scope)

- 前端显式传递 topic 参数（P1，未来 Epic）
- 多主题文档自动拆分（P2，未来功能）
- LLM 辅助主题识别（成本过高）

### 成功标准

**必须达成**:
- `original-lecture` 节点生成与 Level Set 相关的内容
- `kp01` (FILE: KP01-Level-Set定义.md) 节点生成 Level Set 解释
- 跳过所有常见元数据行（🧭, 📋, ---, >, [[, http）

**期望达成**:
- 所有 Agent 解释主题正确率 ≥ 95%
- 无回归：TEXT 类型节点仍然正常工作

---

## 现有系统背景

### 技术栈

**运行环境**:
- Python 3.9+
- FastAPI (后端 API)
- TypeScript/Obsidian Plugin (前端)

**核心文件**:
- `backend/app/services/agent_service.py` - Agent 服务核心
- `backend/app/api/v1/endpoints/agents.py` - API 端点
- `.claude/agents/*.md` - Agent Prompt 模板

### 集成点

**数据流**:
```
用户点击节点 → ContextMenuManager.ts → API Request
                                        ↓
                        agents.py → agent_service.py
                                        ↓
                        _extract_topic_from_content() ← BUG
                                        ↓
                        JSON Prompt → Gemini API
```

**关键方法**:
- `AgentService._extract_topic_from_content()` - 主题提取
- `AgentService.call_explanation()` - 解释 Agent 调用
- `AgentService._construct_json_prompt()` - JSON Prompt 构造

### 现有模式遵循

**Agent 模板输入格式**:
```json
{
  "material_content": "要解释的材料内容",
  "topic": "主题名称",
  "concept": "概念名称",
  "user_understanding": "用户理解（可选）"
}
```

**文件命名规范**:
- `KP01-Level-Set定义.md` - 知识点文件
- `verification-xxx.canvas` - 验证 Canvas
- `clarification-xxx.md` - 澄清文档

---

## Story概览

本 Epic 包含 **6 个 Story**，分为 3 个阶段：

| Story ID | 标题 | 依赖 | 工作量 | 优先级 | 阶段 |
|----------|------|------|--------|--------|------|
| **12.E.1** | 提示词格式对齐 - comparison-table concepts 数组 | 无 | 0.5天 | P0 | 1 |
| **12.E.2** | user_understanding 双通道传递 | 无 | 0.5天 | P0 | 1 |
| **12.E.3** | 2-hop 上下文遍历实现 | 无 | 1天 | P1 | 1 |
| **12.E.4** | Markdown 图片引用提取器 | 无 | 0.5天 | P1 | 2 |
| **12.E.5** | Agent 端点多模态集成 | 12.E.4 | 0.5天 | P1 | 2 |
| **12.E.6** | 集成测试与回归验证 | 12.E.1-5 | 0.5天 | P0 | 3 |

**阶段说明**:
- **阶段 1**: 12.E.1, 12.E.2, 12.E.3 可并行开发
- **阶段 2**: 12.E.4, 12.E.5 顺序开发 (12.E.5 依赖 12.E.4)
- **阶段 3**: 12.E.6 在所有其他 Story 完成后进行

---

### Story 12.E.1: 提示词格式对齐 - comparison-table concepts 数组 [P0]

> 注: 此 Story 原为"智能主题提取"，现扩展为提示词格式对齐

**目标**: 修复 `comparison-table` Agent 的 JSON 输入格式，使其匹配模板期望的 `concepts` 数组

**问题详情**:
- **Agent 模板期望** (`.claude/agents/comparison-table.md:15-17`):
  ```json
  {
    "concepts": ["概念A", "概念B", "概念C"],
    "topic": "主题名称"
  }
  ```
- **后端实际发送** (`agent_service.py:1409-1414`):
  ```json
  {
    "concept": "单个字符串"  // 错误: 应为 concepts 数组
  }
  ```

**修改文件**:
- `backend/app/services/agent_service.py` (第 1395-1435 行)

**新增方法**: `_extract_comparison_concepts()` - 从内容中提取对比概念列表

**验收标准**:
- [ ] comparison-table 收到 `concepts` 数组（>=2 元素）
- [ ] 其他 Agent 格式不变（向后兼容）
- [ ] 单元测试覆盖概念提取逻辑
- [ ] 智能主题提取功能保留（跳过元数据行）

**预计工作量**: 0.5 天

**依赖**: 无

---

### Story 12.E.2: user_understanding 双通道传递 [P0]

> 注: 此 Story 原为"从文件名提取 Topic"，现扩展为黄色节点双通道传递

**目标**: 确保黄色节点 `user_understanding` 同时出现在 JSON 字段和 `enhanced_context` 中

**问题详情**:
- 当前: 仅注入 `enhanced_context` 字符串
- Agent 模板期望: JSON `user_understanding` 字段 (如 `deep-decomposition.md:33` 标记为必需)

**修改文件**:
- `backend/app/services/agent_service.py` (第 1751 行 `generate_explanation()`)
- `backend/app/api/v1/endpoints/agents.py`

**实现方案**:
```python
# generate_explanation() 中
understandings = await self.find_related_understanding_content(...)
user_understanding = "\n\n".join(understandings) if understandings else None

# 双通道传递
json_prompt["user_understanding"] = user_understanding  # JSON 字段
enhanced_context += f"\n\n## 用户理解\n{user_understanding}"  # context
```

**验收标准**:
- [ ] `deep-decomposition` 收到非 null 的 `user_understanding` (当存在黄色节点时)
- [ ] `user_understanding` 同时出现在 JSON 和 context 中
- [ ] 无黄色节点时 `user_understanding` 为 null (不是空字符串)
- [ ] 文件名 topic 提取功能保留

**预计工作量**: 0.5 天

**依赖**: 无 (可与 Story 12.E.1 并行)

---

### Story 12.E.3: 2-hop 上下文遍历实现 [P1]

> 注: 此 Story 原为"集成智能 Topic 提取"，现扩展为 2-hop 上下文遍历

**目标**: 实现 `_find_adjacent_nodes()` 的 2-hop 深度遍历

**问题详情**:
- 当前: 仅 1-hop，`hop_depth` 参数预留但未实现
- 用户需求: 2-hop 以获取更完整的上下文

**修改文件**:
- `backend/app/services/context_enrichment_service.py` (第 481-531 行)

**实现方案**:
```python
def _find_adjacent_nodes(
    self, node_id, nodes, edges,
    hop_depth=2,  # 默认 2-hop
    visited=None
) -> List[AdjacentNode]:
    # 1-hop: 直接相邻
    for edge in edges:
        # ... 现有逻辑，记录 hop_distance=1

    # 2-hop: 递归遍历
    if hop_depth >= 2:
        for hop1_node_id in current_hop_nodes:
            hop2_nodes = self._find_adjacent_nodes(
                hop1_node_id, nodes, edges, hop_depth=1, visited=visited
            )
            for adj in hop2_nodes:
                adj.hop_distance = 2
                adjacent.append(adj)
```

**修改数据类**:
```python
@dataclass
class AdjacentNode:
    node: Dict
    relation: str
    edge_label: str
    hop_distance: int = 1  # 新增
```

**验收标准**:
- [ ] 2-hop 节点被发现并标记 `hop_distance=2`
- [ ] 不产生循环引用 (visited 集合正确维护)
- [ ] 性能可接受 (大型 Canvas < 100ms)
- [ ] 1-hop 功能不受影响（向后兼容）
- [ ] 智能 topic 提取集成保留

**预计工作量**: 1 天

**依赖**: 无 (可与 12.E.1, 12.E.2 并行)

---

### Story 12.E.4: Markdown 图片引用提取器 [P1] (新增)

**目标**: 从节点内容中提取 Markdown 图片引用

**支持格式**:
- Obsidian: `![[image.png]]`, `![[folder/image|caption]]`
- Markdown: `![alt](path.png)`

**新建文件**: `backend/app/services/markdown_image_extractor.py`

**核心类**:
```python
@dataclass
class ImageReference:
    path: str
    alt_text: str = ""
    format: str = ""  # obsidian | markdown
    original_syntax: str = ""

class MarkdownImageExtractor:
    OBSIDIAN_PATTERN = re.compile(r'!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]')
    MARKDOWN_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def extract_all(self, content: str) -> List[ImageReference]:
        """提取所有图片引用"""

    async def resolve_paths(self, refs, vault_path) -> List[Dict]:
        """解析相对路径为绝对路径"""
```

**验收标准**:
- [ ] 正确提取 `![[]]` Obsidian 格式
- [ ] 正确提取 `![]()` 标准 Markdown 格式
- [ ] 跳过 URL 图片 (http/https)
- [ ] 路径解析支持 vault 和 Canvas 相对路径
- [ ] 单元测试覆盖率 >= 80%

**预计工作量**: 0.5 天

**依赖**: 无

---

### Story 12.E.5: Agent 端点多模态集成 [P1] (新增)

**目标**: 将图片提取和处理集成到 Agent API 端点

**依赖**: Story 12.E.4

**修改文件**:
- `backend/app/api/v1/endpoints/agents.py`
- `backend/app/services/agent_service.py`

**实现方案**:
```python
# agents.py _call_explanation() 中
image_refs = image_extractor.extract_all(effective_content)
resolved = await image_extractor.resolve_paths(image_refs, vault_path)
images = await _load_images_for_agent(resolved)

# 调用多模态 API
result = await agent_service.generate_explanation(
    ...,
    images=images,  # 传递图片
)
```

**复用现有组件**:
- `src/agentic_rag/processors/image_processor.py` - 图片处理
- `backend/app/clients/gemini_client.py:call_agent_with_images()` - 多模态调用

**验收标准**:
- [ ] 含图片引用的节点正确提取图片
- [ ] 图片被传递给 `call_agent_with_images()`
- [ ] 无图片时正常降级为文本处理
- [ ] 图片加载失败不影响 Agent 调用

**预计工作量**: 0.5 天

**依赖**: Story 12.E.4

---

### Story 12.E.6: 集成测试与回归验证 [P0] (新增)

**目标**: 确保所有修改不引入回归，并验证新功能正常工作

**依赖**: Story 12.E.1-5

**测试用例**:

1. **提示词格式测试** (`test_agent_prompt_format.py`):
   - `test_comparison_table_receives_concepts_array()`
   - `test_other_agents_format_unchanged()`

2. **黄色节点测试** (`test_user_understanding_dual_channel.py`):
   - `test_understanding_in_json_and_context()`
   - `test_no_understanding_when_no_yellow_node()`

3. **2-hop 遍历测试** (`test_2hop_traversal.py`):
   - `test_2hop_discovers_grandparent_nodes()`
   - `test_2hop_no_cycle()`
   - `test_2hop_performance()`

4. **图片处理测试** (`test_markdown_image_extraction.py`):
   - `test_obsidian_image_extraction()`
   - `test_markdown_image_extraction()`
   - `test_skip_url_images()`

5. **回归测试**:
   - `test_text_node_still_works()`
   - `test_file_node_still_works()`
   - `test_existing_agent_calls_unchanged()`

**验收标准**:
- [ ] 所有新测试通过
- [ ] 所有现有测试通过 (0 回归)
- [ ] 覆盖率 >= 80%

**预计工作量**: 0.5 天

**依赖**: Story 12.E.1, 12.E.2, 12.E.3, 12.E.4, 12.E.5

---

## 原始 Story 定义 (已合并到上方)

以下为原始 Story 定义，保留作为参考。实际实现以上方扩展版本为准。

### [已合并] Story 12.E.1: 智能主题提取 - 跳过元数据行 [P0]

**目标**: 改进 `_extract_topic_from_content()` 跳过元数据行，找到有效主题

**修改文件**:
- `backend/app/services/agent_service.py` (第 1089-1127 行)

**实现方案**:
```python
def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
    """智能主题提取，跳过元数据行"""
    if not content or not content.strip():
        return "Unknown"

    lines = content.strip().split('\n')

    # 扫描前15行，找到有效主题
    for line in lines[:15]:
        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # 跳过元数据/导航行
        if any(line.startswith(prefix) for prefix in ['🧭', '📋', '---', '> ', '[[', 'http', '<!--']):
            continue

        # 跳过纯格式行
        if line in ['', '---', '***', '===']:
            continue

        # 跳过 YAML frontmatter 标记
        if line == '---' or line.startswith('tags:') or line.startswith('date:'):
            continue

        # 找到 # 开头的标题，提取为 topic
        if line.startswith('#'):
            topic = line.lstrip('#').strip()
            # 去掉加粗/斜体标记
            topic = topic.replace('**', '').replace('*', '').replace('_', ' ')
            topic = ' '.join(topic.split())
            return topic[:max_length] if len(topic) > max_length else topic

        # 找到有意义的内容行 (至少5字符)
        if len(line) > 5:
            # 清理 markdown 格式
            clean_line = line.replace('**', '').replace('*', '').replace('_', ' ')
            clean_line = ' '.join(clean_line.split())
            return clean_line[:max_length] if len(clean_line) > max_length else clean_line

    return "Unknown"
```

**验收标准**:
- [ ] 跳过 🧭/📋/--- 开头的元数据行
- [ ] 跳过 [[/http/<!-- 开头的链接/注释行
- [ ] 找到实际的标题 (# 开头) 或内容行
- [ ] 单元测试覆盖所有元数据类型
- [ ] `original-lecture` 节点提取出有效主题（非 "🧭 知识图谱控制中心..."）

**预计工作量**: 0.5 天

**依赖**: 无

---

### Story 12.E.2: 从文件名提取 Topic [P0]

**目标**: 为 FILE 类型节点从文件名提取 topic

**修改文件**:
- `backend/app/services/agent_service.py` (新增方法)

**实现方案**:
```python
import re
from pathlib import Path

def _extract_topic_from_file_path(self, file_path: str) -> str:
    """
    从文件路径提取 topic

    Examples:
        "KP01-Level-Set定义.md" → "Level Set定义"
        "clarification-逆否命题-20251215.md" → "逆否命题"
        "2025_lecture_53_05.md" → "lecture 53 05"
    """
    if not file_path:
        return ""

    # 获取文件名（不含扩展名）
    filename = Path(file_path).stem

    # 去掉常见前缀编号
    # KP01-, KP-01-, 01-, 2025_, clarification-, verification-
    patterns_to_remove = [
        r'^KP\d+[-_]?',           # KP01-, KP-01-
        r'^\d+[-_]',              # 01-, 01_
        r'^\d{4}[-_]',            # 2025-, 2025_
        r'^clarification[-_]',    # clarification-
        r'^verification[-_]',     # verification-
        r'^explanation[-_]',      # explanation-
        r'[-_]\d{8,}$',           # -20251215 (日期后缀)
        r'[-_]corrected$',        # -corrected
        r'[-_]hold$',             # -hold
    ]

    topic = filename
    for pattern in patterns_to_remove:
        topic = re.sub(pattern, '', topic, flags=re.IGNORECASE)

    # 替换分隔符为空格
    topic = topic.replace('-', ' ').replace('_', ' ')

    # 清理多余空格
    topic = ' '.join(topic.split())

    return topic if topic else ""
```

**验收标准**:
- [ ] `KP01-Level-Set定义.md` → `Level Set定义`
- [ ] `clarification-逆否命题-20251215.md` → `逆否命题`
- [ ] `2025_lecture_53_05_corrected_hold.md` → `lecture 53 05`
- [ ] 单元测试覆盖常见文件命名模式
- [ ] 空文件名或无效路径返回空字符串

**预计工作量**: 0.25 天

**依赖**: 无 (可与 Story 12.E.1 并行)

---

### Story 12.E.3: 集成智能 Topic 提取 [P0]

**目标**: 在 `call_explanation()` 中集成智能 topic 提取逻辑

**修改文件**:
- `backend/app/services/agent_service.py` (修改 `call_explanation` 和相关方法)

**实现方案**:
```python
async def call_explanation(
    self,
    agent_type: AgentType,
    content: str,
    context: Optional[str] = None,
    user_understanding: Optional[str] = None,
    file_path: Optional[str] = None,  # 新增：FILE 节点的文件路径
    timeout: Optional[float] = None
) -> AgentResult:
    """
    调用解释类 Agent

    Topic 提取优先级：
    1. 从 file_path 提取（FILE 类型节点）
    2. 从 content 智能提取（TEXT 类型节点或 fallback）
    """
    # 智能 topic 提取
    topic = ""

    # 优先从文件名提取
    if file_path:
        topic = self._extract_topic_from_file_path(file_path)
        if topic:
            logger.info(f"[Story 12.E.3] Topic extracted from file_path: {topic}")

    # Fallback: 从内容智能提取
    if not topic:
        topic = self._extract_topic_from_content(content)
        logger.info(f"[Story 12.E.3] Topic extracted from content: {topic}")

    # 构造 JSON prompt
    json_prompt = json.dumps({
        "material_content": content,
        "topic": topic,
        "concept": topic,
        "user_understanding": user_understanding
    }, ensure_ascii=False, indent=2)

    # 调用 Agent
    return await self.call_agent(
        agent_type=agent_type,
        prompt=json_prompt,
        context=context,
        timeout=timeout
    )
```

**需要修改的调用链**:
1. `agents.py` API 端点传递 `file_path` 参数
2. `context_enrichment_service.py` 提供 `file_path` 信息
3. `agent_service.py` 使用智能 topic 提取

**验收标准**:
- [ ] FILE 类型节点优先使用文件名 topic
- [ ] TEXT 类型节点使用智能内容提取
- [ ] 日志清楚显示 topic 来源 (file_path vs content)
- [ ] `kp01` 节点 (FILE: KP01-Level-Set定义.md) 生成 Level Set 解释
- [ ] 无回归：TEXT 类型节点仍然正常工作

**预计工作量**: 0.25 天

**依赖**: Story 12.E.1, Story 12.E.2

---

## 验收标准

### Epic 级验收标准

**AC1: 主题正确性**
- [ ] `original-lecture` 节点生成与文档首个实际标题相关的内容（非元数据）
- [ ] `kp01` (FILE: KP01-Level-Set定义.md) 节点生成 Level Set 解释
- [ ] 不再生成与所选节点完全无关的内容（如 Transformer、特征值）

**AC2: 元数据跳过**
- [ ] 跳过 🧭 开头的导航行
- [ ] 跳过 📋 开头的元数据行
- [ ] 跳过 --- YAML frontmatter 标记
- [ ] 跳过 [[ 开头的 Obsidian 链接行
- [ ] 跳过 http 开头的 URL 行
- [ ] 跳过 <!-- 开头的注释行

**AC3: 文件名 Topic 提取**
- [ ] `KP01-Level-Set定义.md` → topic 包含 "Level Set"
- [ ] 去掉常见前缀（KP01-, clarification-, verification-）
- [ ] 去掉常见后缀（-20251215, -corrected, -hold）

**AC4: 无回归**
- [ ] TEXT 类型节点仍然正常工作
- [ ] 所有现有测试用例通过
- [ ] 其他 Agent 功能不受影响

**AC5: 日志追踪**
- [ ] 日志显示 topic 提取来源 (file_path vs content)
- [ ] 日志显示提取的 topic 值

---

## 技术约束

### 必须遵守的约束

**编程语言**: Python 3.9+

**修改范围**:
- 只修改 `backend/app/services/agent_service.py`
- 不修改 Agent 模板文件
- 不修改前端代码（本 Epic）

**兼容性**:
- 保持 `call_explanation()` 方法签名向后兼容
- 保持 API 端点参数兼容
- 保持 Agent 模板输入格式不变

### 技术标准

**代码质量**:
- 所有新方法必须有类型注解
- 所有新方法必须有 Google 风格 docstring
- 单元测试覆盖率 ≥ 80%

**测试标准**:
- 元数据行跳过测试（6+ 种类型）
- 文件名提取测试（5+ 种命名模式）
- 集成测试（FILE 和 TEXT 类型节点）

---

## 风险与缓解

### 中风险 (P2)

**风险1: 过度跳过导致找不到有效主题**
- **影响**: 返回 "Unknown"，AI 仍然可能幻觉
- **可能性**: 低 (15%)
- **缓解策略**:
  - 限制扫描行数（15行）
  - 宽松的有效内容判断（5字符以上）
  - 提供 fallback 机制

**风险2: 文件名提取模式不完整**
- **影响**: 部分文件名无法正确提取 topic
- **可能性**: 中 (30%)
- **缓解策略**:
  - 收集真实文件命名样本
  - 使用 fallback 到内容提取
  - 添加日志追踪发现新模式

### 低风险 (P3)

**风险3: 性能影响**
- **影响**: 主题提取增加少量延迟
- **可能性**: 低 (10%)
- **缓解策略**:
  - 只扫描前15行
  - 使用高效的字符串操作
  - 性能影响 < 1ms

### 回滚计划

**场景: 主题提取导致更多问题**
- 步骤1: 回滚到旧的 `_extract_topic_from_content()` 实现
- 步骤2: 禁用文件名 topic 提取
- 步骤3: 分析问题并修复

---

## 成功指标

### 关键绩效指标 (KPI)

| 指标 | 基线 | 目标 | 测量方法 |
|------|------|------|---------|
| **主题正确率** | 0% | ≥95% | 10个测试节点手动验证 |
| **元数据跳过率** | 0% | 100% | 单元测试 |
| **文件名提取成功率** | N/A | ≥90% | 单元测试 |
| **测试覆盖率** | N/A | ≥80% | pytest coverage |

### 验收测试清单

**Story 12.E.1 验收**:
- [ ] 单元测试: 6种元数据类型全部跳过
- [ ] 单元测试: 找到第一个有效 # 标题
- [ ] 单元测试: 找到第一个有效内容行
- [ ] 集成测试: `original-lecture` 节点提取正确 topic

**Story 12.E.2 验收**:
- [ ] 单元测试: 5种文件命名模式正确提取
- [ ] 单元测试: 边界情况（空路径、无效路径）
- [ ] 集成测试: `kp01` 节点从文件名提取 topic

**Story 12.E.3 验收**:
- [ ] 集成测试: FILE 类型优先使用文件名 topic
- [ ] 集成测试: TEXT 类型使用内容提取
- [ ] 回归测试: 所有现有测试用例通过
- [ ] E2E测试: 生成内容主题正确

---

## 依赖关系

### Epic 内部依赖

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  12.E.1     │   │  12.E.2     │   │  12.E.3     │
│ 提示词对齐  │   │ 黄色节点    │   │ 2-hop遍历  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       │                 │                 │
       └────────────────┬┴─────────────────┘
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
┌─────────────┐                   ┌─────────────┐
│  12.E.4     │                   │  12.E.6     │
│ 图片提取器  │                   │ 集成测试    │
└──────┬──────┘                   └─────────────┘
       │                                 ↑
       ▼                                 │
┌─────────────┐                          │
│  12.E.5     │──────────────────────────┘
│ 多模态集成  │
└─────────────┘
```

**并行**: 12.E.1, 12.E.2, 12.E.3, 12.E.4 可并行开发
**顺序**: 12.E.5 依赖 12.E.4; 12.E.6 依赖所有其他 Story

### 外部依赖

**上游依赖**:
- Epic 12.D: FILE 节点内容读取 (**已完成**)
- Epic 12.B: node_content 参数传递 (**已完成**)

**下游影响**:
- 所有 Agent 解释功能将使用新的 topic 提取逻辑
- Claude Code Sub Agent 和 LangGraph Agent 质量差距将缩小

---

## 兼容性要求

### 必须保持兼容

**API 兼容性**:
- `call_explanation()` 方法签名兼容（新增可选参数 `file_path`）
- API 端点参数兼容

**Agent 模板兼容性**:
- JSON 输入格式不变 (`material_content`, `topic`, `concept`, `user_understanding`)
- Agent 模板文件不修改

**功能兼容性**:
- TEXT 类型节点行为不变（使用内容提取）
- FILE 类型节点增强（优先使用文件名提取）

---

## Definition of Done

### Epic 级 DoD

- [ ] 所有 6 个 Story 完成且验收标准达成
- [ ] 所有现有测试用例通过（0 回归）
- [ ] 新增测试覆盖率 ≥ 80%
- [ ] `original-lecture` 节点生成主题正确的内容
- [ ] `kp01` 节点生成 Level Set 相关内容
- [ ] comparison-table Agent 收到 concepts 数组
- [ ] user_understanding 双通道传递正常
- [ ] 2-hop 上下文遍历正常
- [ ] 图片提取和多模态集成正常
- [ ] 代码 review 通过
- [ ] 日志可追踪 topic 提取来源

### Story 级 DoD 模板

每个 Story 必须满足：
- [ ] 验收标准全部达成
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 代码有类型注解和 docstring
- [ ] 代码 review 通过

---

## 附录

### 相关文档

**调研报告**: `C:\Users\ROG\.claude\plans\quirky-leaping-aurora.md` (4-part 深度调研)

**BUG 文件位置**:
- `backend/app/services/agent_service.py:1089-1127` - `_extract_topic_from_content()`
- `backend/app/services/agent_service.py:1406-1414` - JSON prompt 构造

**Agent 模板位置**:
- `.claude/agents/clarification-path.md`
- `.claude/agents/four-level-explanation.md`
- `.claude/agents/oral-explanation.md`

### 测试文件命名样本

从真实项目收集的文件命名模式：
```
KP01-Level-Set定义.md
KP02-隐函数求导.md
clarification-逆否命题-20251215.md
verification-Lecture5-20251214.md
2025_lecture_53_05_corrected_hold.md
explanation-Transformer-基础.md
```

### 元数据行样本

从真实文档收集的元数据行模式：
```
🧭 **[知识图谱控制中心-Lecture5.md]...**
📋 学习进度：已完成 3/10 节点
---
> [!note] 这是一个注释
[[相关链接]]
https://example.com
<!-- HTML 注释 -->
```

---

## Epic 签发

**创建日期**: 2025-12-15
**Epic 状态**: Ready for Development
**优先级**: P0 Critical
**预计周期**: 3.5 个工作日

**下一步行动**:

**阶段 1 (可并行)**:
1. 开发 Story 12.E.1 (提示词格式对齐)
2. 并行开发 Story 12.E.2 (user_understanding 双通道)
3. 并行开发 Story 12.E.3 (2-hop 遍历)
4. 并行开发 Story 12.E.4 (图片提取器)

**阶段 2 (顺序)**:
5. 开发 Story 12.E.5 (多模态集成) - 依赖 12.E.4

**阶段 3 (最后)**:
6. 开发 Story 12.E.6 (集成测试) - 依赖全部

---

**Epic 文档结束**
