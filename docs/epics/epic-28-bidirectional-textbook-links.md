# Epic 28: 双向链接跳回教材功能 - Brownfield Enhancement

**Epic ID**: EPIC-28
**Epic类型**: 功能增强 (Brownfield Enhancement)
**状态**: Created (Not Started)
**优先级**: P1 High
**创建日期**: 2025-12-26
**来源调研**: 挂载教材功能深度调研 (`resilient-growing-sphinx.md`, `streamed-frolicking-music.md`)

---

## 目录

1. [Epic概述](#epic概述)
2. [现有系统背景](#现有系统背景)
3. [问题分析](#问题分析)
4. [Epic目标](#epic目标)
5. [Story概览](#story概览)
6. [技术方案](#技术方案)
7. [验收标准](#验收标准)
8. [兼容性要求](#兼容性要求)
9. [风险与缓解](#风险与缓解)
10. [Definition of Done](#definition-of-done)

---

## Epic概述

### 简述

**实现Agent回答中的双向链接功能**，让用户可以点击链接跳转到教材原文位置。

当前状态：后端教材检索已完整实现(898行代码)，但Agent回答中**不生成**可点击的Obsidian链接，用户无法跳回教材原文。

### 问题陈述

**用户期望**:
```markdown
# Agent回答
水平集是函数f(x)=c的解集...
参见：[[教材/离散数学.canvas#逆否命题]]  ← 可点击跳转到教材
```

**当前实际**:
```markdown
# Agent回答
水平集是函数f(x)=c的解集...
教材中提到了逆否命题的定义...  ← 无法点击，无法跳转
```

### 根因分析

**问题链路图**:
```
TextbookContextService    ContextEnrichmentService    Agent模板    Obsidian
       ✅                        ❌                      ❌           ✅
    有文件路径                 不传递路径             无格式规范     支持链接
       ↓                        ↓                      ↓            ↓
  textbook_canvas          只传text              无[[]]规范    可解析[[]]

                          ↑ 断裂点!
```

**三层断裂**:
1. `_format_textbook_context()` 只格式化文本，丢弃文件路径元数据
2. Agent模板中无双向链接格式规范
3. PDF页码信息不传递给Agent

### 预期影响

**用户体验提升**:
- 从"无法跳转"到"一键跳转教材原文"
- 从"手动查找教材"到"AI自动标注来源"
- 建立教材引用的可追溯性

**功能完成度**:
- 教材功能从 60% → 95% (补齐双向链接)

---

## 现有系统背景

### 技术栈

**后端服务**:
- Python 3.9+ / FastAPI
- `backend/app/services/textbook_context_service.py` (511行)
- `backend/app/services/context_enrichment_service.py`

**Agent模板**:
- `.claude/agents/*.md` (9个Agent模板)

**前端**:
- TypeScript / Obsidian Plugin
- Obsidian原生支持 `[[file]]` 和 `[[file#section]]` 链接语法

### 现有数据结构

**TextbookContext (已实现)**:
```python
@dataclass
class TextbookContext:
    textbook_canvas: str      # "教材/离散数学.canvas" ← 有路径!
    section_name: str         # "第3章 逆否命题"
    node_id: str              # 匹配节点ID
    relevance_score: float    # 0.95
    content_preview: str      # "逆否命题是指..."
```

**当前格式化输出 (问题所在)**:
```python
# context_enrichment_service.py:_format_textbook_context()
# 只输出文本，丢弃 textbook_canvas 路径!
textbook_context_str = f"""
--- 相关教材参考 ---
[textbook|离散数学] 第3章 逆否命题
  预览: 逆否命题是指...
"""
```

### 集成点

**数据流**:
```
.canvas-links.json → TextbookContextService → ContextEnrichmentService
                                                       ↓
                          enriched_context (丢失路径) → Agent Prompt
                                                       ↓
                                               Gemini API → 回答 (无链接)
```

---

## 问题分析

### 问题1: 文件路径元数据丢失

**位置**: `context_enrichment_service.py` 第356-407行

**现状**:
```python
textbook_context_str = f"[textbook|{ctx.section_name}] {ctx.content_preview}"
# ❌ 丢失了 ctx.textbook_canvas
```

**解决**: 保留并格式化完整路径信息

### 问题2: Agent模板无引用格式规范

**位置**: `.claude/agents/*.md`

**现状**: Agent模板只要求引用用户问题，无教材引用格式

**解决**: 添加教材引用格式规范到Agent模板

### 问题3: PDF页码信息断裂

**位置**: LanceDB存储 → TextbookService传递

**现状**: PDF页码在LanceDB有存储，但不传递给Agent

**解决**: 扩展元数据传递，支持PDF页码

---

## Epic目标

### 主要目标

**目标1: 保留教材路径元数据**
- 修改 `_format_textbook_context()` 传递完整文件路径
- 格式: `来源文件: [[教材/离散数学.canvas#逆否命题]]`

**目标2: Agent模板添加引用规范**
- 在Agent Prompt中添加引用格式要求
- 强制生成 `[[file#section]]` 格式链接

**目标3: PDF页码支持**
- 传递 `page_number` 元数据
- 生成 `[[教材.pdf#page=47]]` 格式链接

### 非目标 (Out of Scope)

- 前端UI教材挂载入口 (已在其他Epic实现)
- 教材版本管理 (Future)
- 智能教材推荐 (Future)

### 成功标准

| 标准 | 描述 |
|------|------|
| **SC1** | Agent回答中包含 `[[教材文件#章节]]` 格式链接 |
| **SC2** | Obsidian中可点击链接跳转到教材 |
| **SC3** | PDF教材生成 `[[file.pdf#page=N]]` 链接 |
| **SC4** | 无回归：现有Agent功能不受影响 |

---

## Story概览

本Epic包含 **4个Story**，可在约2天内完成：

| Story ID | 标题 | 依赖 | 工作量 | 优先级 |
|----------|------|------|--------|--------|
| **28.1** | 教材路径元数据传递 | 无 | 0.5天 | P0 |
| **28.2** | Agent模板引用格式规范 | 无 | 0.5天 | P0 |
| **28.3** | PDF页码链接支持 | 28.1 | 0.5天 | P1 |
| **28.4** | 集成测试与回归验证 | 28.1-3 | 0.5天 | P0 |

**并行策略**: Story 28.1 和 28.2 可并行开发

---

### Story 28.1: 教材路径元数据传递 [P0]

**目标**: 修改 `_format_textbook_context()` 保留并格式化完整教材路径

**修改文件**:
- `backend/app/services/context_enrichment_service.py` (第356-407行)

**实现方案**:
```python
def _format_textbook_context(self, textbook_ctx: FullTextbookContext) -> str:
    """格式化教材上下文，保留双向链接所需的路径信息"""
    if not textbook_ctx.contexts:
        return ""

    sections = []
    for ctx in textbook_ctx.contexts:
        # 生成Obsidian链接格式
        link = f"[[{ctx.textbook_canvas}#{ctx.section_name}]]"

        section = f"""
### 教材参考: {ctx.section_name}
- **来源文件**: {link}
- **相关度**: {ctx.relevance_score:.0%}
- **内容预览**: {ctx.content_preview[:200]}...

> 引用此内容时，请使用链接: {link}
"""
        sections.append(section)

    return "\n".join(sections)
```

**验收标准**:
- [ ] `textbook_canvas` 路径出现在格式化输出中
- [ ] 输出包含Obsidian `[[file#section]]` 格式
- [ ] 单元测试覆盖路径格式化逻辑
- [ ] 无回归：现有上下文增强功能正常

**预计工作量**: 0.5天

---

### Story 28.2: Agent模板引用格式规范 [P0]

**目标**: 在Agent Prompt模板中添加教材引用格式要求

**修改文件**:
- `.claude/agents/oral-explanation.md`
- `.claude/agents/four-level-explanation.md`
- `.claude/agents/clarification-path.md`
- `.claude/agents/example-teaching.md`
- `.claude/agents/comparison-table.md`
- `.claude/agents/memory-anchor.md`
- `.claude/agents/basic-decomposition.md`
- `.claude/agents/deep-decomposition.md`
- `.claude/agents/question-decomposition.md`

**添加内容** (在每个Agent模板的输出规范部分):
```markdown
## 引用规范

当你的回答引用了教材内容时，**必须**使用以下格式标注来源：

### Markdown/Canvas教材
> [引用的内容]
> — 来源: [[教材文件路径#章节名]]

### PDF教材
> [引用的内容]
> — 来源: [[教材文件.pdf#page=页码|章节名]]

### 示例
> 逆否命题是将原命题的条件和结论都取反后得到的命题。
> — 来源: [[教材/离散数学.canvas#第3章-逆否命题]]

**重要**:
- 如果输入中包含"来源文件"信息，必须在回答中使用双括号链接格式引用
- 链接格式必须是 `[[文件路径#章节]]`，确保用户可以点击跳转
```

**验收标准**:
- [ ] 所有9个Agent模板包含引用规范
- [ ] 规范清晰说明链接格式
- [ ] 包含Markdown/Canvas和PDF两种格式示例
- [ ] Agent实际生成链接格式输出 (集成测试验证)

**预计工作量**: 0.5天

---

### Story 28.3: PDF页码链接支持 [P1]

**目标**: 扩展元数据传递，支持PDF页码链接生成

**依赖**: Story 28.1

**修改文件**:
- `backend/app/services/textbook_context_service.py`
- `backend/app/services/context_enrichment_service.py`

**实现方案**:

1. **扩展TextbookContext数据类**:
```python
@dataclass
class TextbookContext:
    textbook_canvas: str
    section_name: str
    node_id: str
    relevance_score: float
    content_preview: str
    page_number: Optional[int] = None  # 新增: PDF页码
    file_type: str = "canvas"          # 新增: canvas | markdown | pdf
```

2. **修改路径格式化**:
```python
def _format_textbook_link(self, ctx: TextbookContext) -> str:
    if ctx.file_type == "pdf" and ctx.page_number:
        return f"[[{ctx.textbook_canvas}#page={ctx.page_number}|{ctx.section_name}]]"
    else:
        return f"[[{ctx.textbook_canvas}#{ctx.section_name}]]"
```

**验收标准**:
- [ ] PDF教材生成 `[[file.pdf#page=N]]` 格式链接
- [ ] 非PDF教材保持 `[[file#section]]` 格式
- [ ] Obsidian可正确解析PDF页码链接
- [ ] 单元测试覆盖PDF链接生成

**预计工作量**: 0.5天

---

### Story 28.4: 集成测试与回归验证 [P0]

**目标**: 验证双向链接功能端到端工作

**依赖**: Story 28.1, 28.2, 28.3

**测试用例**:

1. **双向链接生成测试** (`test_bidirectional_links.py`):
   - `test_agent_generates_canvas_link()`
   - `test_agent_generates_markdown_link()`
   - `test_agent_generates_pdf_page_link()`

2. **格式验证测试**:
   - `test_link_format_obsidian_compatible()`
   - `test_link_contains_section_name()`

3. **回归测试**:
   - `test_agent_without_textbook_still_works()`
   - `test_existing_context_enrichment_unchanged()`

**验收标准**:
- [ ] 所有新测试通过
- [ ] 所有现有测试通过 (0回归)
- [ ] E2E测试: Agent回答包含可点击链接
- [ ] 覆盖率 >= 80%

**预计工作量**: 0.5天

---

## 技术方案

### 数据流修改

**Before (当前)**:
```
TextbookContext.textbook_canvas ──→ 丢弃 ──→ Agent收不到路径
```

**After (目标)**:
```
TextbookContext.textbook_canvas ──→ 格式化为[[link]] ──→ Agent收到链接模板
                                                              ↓
                                              Agent生成: 参见 [[教材#章节]]
```

### 关键代码修改点

| 文件 | 行号 | 修改内容 |
|------|------|---------|
| `context_enrichment_service.py` | 356-407 | `_format_textbook_context()` 保留路径 |
| `textbook_context_service.py` | dataclass | 添加 `page_number`, `file_type` 字段 |
| `.claude/agents/*.md` | 输出规范 | 添加引用格式要求 |

### Obsidian链接格式参考

| 类型 | 格式 | 示例 |
|------|------|------|
| Canvas | `[[file.canvas#节点ID或标题]]` | `[[教材/离散数学.canvas#逆否命题]]` |
| Markdown | `[[file.md#标题]]` | `[[教材/集合论.md#并集定义]]` |
| PDF | `[[file.pdf#page=N]]` | `[[教材/高等数学.pdf#page=47]]` |
| PDF带标题 | `[[file.pdf#page=N\|显示文本]]` | `[[教材.pdf#page=47\|第3章]]` |

---

## 验收标准

### Epic级验收标准

**AC1: 双向链接生成**
- [ ] Agent回答中包含 `[[file#section]]` 格式链接
- [ ] 链接路径与实际教材文件对应

**AC2: Obsidian兼容性**
- [ ] 生成的链接在Obsidian中可点击
- [ ] 点击后跳转到正确的教材位置

**AC3: PDF支持**
- [ ] PDF教材生成 `[[file.pdf#page=N]]` 链接
- [ ] 点击后跳转到PDF指定页

**AC4: 无回归**
- [ ] 无教材关联时Agent正常工作
- [ ] 现有9个Agent功能不受影响
- [ ] 所有现有测试通过

---

## 兼容性要求

### 必须保持兼容

**API兼容性**:
- 现有API端点签名不变
- `TextbookContext` 新增字段有默认值 (向后兼容)

**Agent模板兼容性**:
- JSON输入格式不变
- 仅在输出规范部分添加引用格式

**Obsidian兼容性**:
- 使用Obsidian原生链接语法
- 不依赖第三方插件

---

## 风险与缓解

### 中风险 (P2)

**风险1: Agent不遵循引用格式**
- **影响**: 生成的回答仍然没有链接
- **可能性**: 中 (40%)
- **缓解策略**:
  - Prompt中强调"必须"使用格式
  - 添加示例增强理解
  - 后处理添加链接 (Plan B)

**风险2: Obsidian链接解析问题**
- **影响**: 链接无法点击或跳转错误
- **可能性**: 低 (20%)
- **缓解策略**:
  - 测试各种特殊字符转义
  - 参考Obsidian官方链接规范
  - 添加链接格式验证

### 低风险 (P3)

**风险3: 性能影响**
- **影响**: 上下文增强略微变慢
- **可能性**: 低 (10%)
- **缓解策略**:
  - 路径格式化是简单字符串操作
  - 性能影响 < 1ms

### 回滚计划

**场景: 双向链接导致问题**
1. 回滚Agent模板到原版本
2. 回滚 `_format_textbook_context()` 到原实现
3. 分析问题并修复

---

## Definition of Done

### Epic级DoD

- [ ] 所有4个Story完成且验收标准达成
- [ ] 所有现有测试用例通过 (0回归)
- [ ] 新增测试覆盖率 >= 80%
- [ ] Agent回答中包含可点击的教材链接
- [ ] Obsidian中链接可正确跳转
- [ ] PDF页码链接正常工作
- [ ] 代码review通过

### Story级DoD模板

每个Story必须满足:
- [ ] 验收标准全部达成
- [ ] 单元测试覆盖率 >= 80%
- [ ] 代码有类型注解和docstring
- [ ] 代码review通过

---

## 依赖关系

### Epic内部依赖

```
┌─────────────┐   ┌─────────────┐
│   28.1      │   │   28.2      │
│ 路径元数据  │   │ Agent模板   │
└──────┬──────┘   └──────┬──────┘
       │                 │
       │    可并行开发    │
       │                 │
       └────────┬────────┘
                │
                ▼
       ┌─────────────┐
       │   28.3      │
       │ PDF页码     │
       └──────┬──────┘
              │
              ▼
       ┌─────────────┐
       │   28.4      │
       │ 集成测试    │
       └─────────────┘
```

### 外部依赖

**上游依赖**:
- 教材检索功能 (**已完成** - TextbookContextService)
- RAG五源融合 (**已完成** - TextbookRetriever)

**下游影响**:
- 所有9个Agent将支持双向链接引用
- 教材功能可用性从60%提升到95%

---

## 附录

### 相关调研文档

- `C:\Users\ROG\.claude\plans\resilient-growing-sphinx.md` - 挂载教材功能深度调研
- `C:\Users\ROG\.claude\plans\streamed-frolicking-music.md` - 教材格式支持调研

### 关键代码文件

| 文件 | 行数 | 职责 |
|------|------|------|
| `backend/app/services/textbook_context_service.py` | 511 | 教材检索核心 |
| `backend/app/services/context_enrichment_service.py` | - | 上下文增强 |
| `.claude/agents/*.md` | 9文件 | Agent Prompt模板 |

### Obsidian链接语法参考

```markdown
# 基础链接
[[文件名]]
[[文件名#标题]]
[[文件名#^块ID]]

# 带显示文本
[[文件名|显示文本]]
[[文件名#标题|显示文本]]

# PDF页码
[[文件.pdf#page=47]]
[[文件.pdf#page=47|第3章]]
```

---

## Epic签发

**创建日期**: 2025-12-26
**Epic状态**: Created (Not Started)
**优先级**: P1 High
**预计周期**: 2个工作日

**下一步行动**:
1. ⏳ 等待用户确认Epic范围
2. ⏳ 开始Story 28.1和28.2并行开发
3. ⏳ 完成28.3后进行集成测试

---

**Epic文档结束**
