# Story Template v3.0 - 完整使用指南

**版本**: v3.0 Enhanced (Anti-Hallucination Edition)
**发布日期**: 2025-10-29
**基于**: Story 10.9 UltraThink验证经验
**状态**: 🟢 生产就绪

---

## 📋 目录

1. [v3.0 重大改进](#v30-重大改进)
2. [完整模板示例](#完整模板示例)
3. [使用指南](#使用指南)
4. [验证清单](#验证清单)
5. [从v2.0迁移](#从v20迁移)
6. [常见问题FAQ](#常见问题faq)

---

## 🚀 v3.0 重大改进

### 改进概述

| 改进类别 | v2.0状态 | v3.0增强 | 影响等级 |
|----------|---------|---------|----------|
| **Epic上下文** | ❌ 无此章节 | ✅ 新增必需章节 | 🔴 关键 |
| **依赖验证** | ⚠️ 隐式 | ✅ 新增验证清单 | 🔴 关键 |
| **文档引用** | ⚠️ 零散 | ✅ 集中引用章节 | 🟡 重要 |
| **AC增强** | ⚠️ 基础 | ✅ Epic关联必需 | 🟡 重要 |
| **任务增强** | ⚠️ 基础 | ✅ Story依赖必需 | 🟡 重要 |
| **反幻觉** | ❌ 无规则 | ✅ 全流程验证 | 🔴 关键 |

### 问题根源分析

**Story 10.9发现的问题**:
```
原问题: Story可以在没有Epic上下文的情况下编写
   ↓
导致: Story与Epic脱节，引用了可能不存在的类
   ↓
后果: 实施准备度从应有的9/10降到5/10
   ↓
修复: UltraThink验证2小时，修复+187行
```

**v3.0解决方案**:
```
模板层面强制: Epic Context & Background章节必需
   ↓
编写时验证: Dependencies Verification清单必需
   ↓
质量保证: 自动化验证规则
   ↓
结果: 预防类似问题，提高Story质量
```

---

## 📝 完整模板示例

### Story XX.Y: [Story标题]

#### Status
Draft

#### Parallel Development Support (v3.1)

**affected_files**: (Required for parallel development)
```yaml
affected_files:
  - src/canvas_utils.py
  - src/agents/example_teaching.py
```

**parallel_group**: (Filled by orchestrator)
```yaml
parallel_group: "sprint-13-batch-1"
worktree: "../Canvas-develop-13.1"
```

> **Note**: The `affected_files` field is used by `analyze-dependencies.ps1` to detect
> conflicts before parallel development. List all files this Story will modify.

#### Epic背景与上下文

**所属Epic**: EPIC-XXX - [Epic名称]
**Epic文档**: [epic-xx-xxx.story.md](./epic-xx-xxx.story.md)

**本Story在Epic中的定位**:
- Story XX.Y是Epic XX的**[角色描述]**
- **依赖**: Story XX.A 和 Story XX.B 必须完成

**Epic核心问题回顾**:

##### 🔴 Problem 1: [问题名称]
- **现象**: [问题表现]
- **根因**: [根本原因]
- **修复**: 本Story创建了`[类名/功能]`
- **本Story验证**: AC X, AC Y 验证Problem 1已修复

##### 🟡 Problem 2: [问题名称]
- **现象**: [问题表现]
- **根因**: [根本原因]
- **修复**: 本Story实现了`[类名/功能]`
- **本Story验证**: AC Z 验证Problem 2已修复

---

#### Story

**As a** [角色],
**I want** [功能],
**so that** [价值].

#### Acceptance Criteria

##### AC 1: [AC标题] (验证Problem 1修复)
- 验证项1: [详细描述]
- 验证项2: [详细描述]
- **Epic关联**: 直接验证Problem 1的修复效果

##### AC 2: [AC标题] (Story XX.A依赖)
- 验证项1: [详细描述]
- **Story XX.A依赖**: 验证`[类名]`正确工作

#### Tasks / Subtasks

##### 任务1: [任务名称] (AC: 1)
- [ ] 1.1: [子任务描述]
      - Phase 1: [阶段1] (测试Story XX.A)
      - Phase 2: [阶段2] (验证Problem 1修复)
- [ ] 1.2: [子任务描述]
- [ ] 1.3: 创建测试数据文件 (path/to/file)
      - **内容规格**: [详细说明应该包含什么]
      - 数据示例: "[具体示例1]", "[具体示例2]"

##### 任务2: [任务名称] (AC: 2, Story XX.A验证)
- [ ] 2.1: [子任务描述]
      - 验证`[类名]`数量和内容
      - 验证[具体细节]
- [ ] 2.2: [子任务描述]

#### Dev Notes

##### 🎯 [主要技术策略标题]

**Epic XX背景** [Source: docs/stories/epic-xx-xxx.story.md]:
```
[从Epic文档中摘录的关键信息]

已完成Story (XX%):
- ✅ Story XX.1: [Story名称] (file.py)
- ✅ Story XX.2: [Story名称] (file.py)

本Story依赖:
- 🔥 Story XX.A: [Story名称] ([类名])
- 🔥 Story XX.B: [Story名称] ([类名])
```

**核心验证点**:
1. ✅ **Problem 1已修复**: [验证内容]
   - 验证方式: AC X Phase Y, AC Z全部
2. ✅ **Problem 2已修复**: [验证内容]
   - 验证方式: AC X Phase Y, AC Z全部

**前置依赖验证** (必须先完成):
- [ ] Story XX.A单元测试通过 (file.py)
- [ ] Story XX.B单元测试通过 (file.py)
- [ ] `类名A`已验证存在: path/to/file.py (第X行)
- [ ] `类名B`已验证存在: path/to/file.py (第Y行)
- [ ] 外部服务X已配置或Mock策略已准备

---

##### 📐 [技术实现章节标题]

**[子标题1]** [NEW - 修复反馈]:

**1. [详细说明1]**:
```bash
# [命令或配置示例]
# 说明: [目的]
# 验证: [如何验证]
```

**2. [详细说明2]** (用于[场景]):
```python
# [代码示例]
```

**[子标题2]** [Source: docs/architecture/xxx.md]:
```python
# [详细的代码示例，包含注释]

@decorator
def function_name():
    """详细的docstring

    [详细说明]:
    - [说明1]
    - [说明2]

    依赖: Story XX.A的[类名]
    Source: file.py
    """
    pass
```

---

##### 🔗 相关文档引用

**Epic和Story文档**:
- [Epic XX完整文档](./epic-xx-xxx.story.md) - Epic背景和问题定义
- [Story XX.A文档](./xx.a.xxx.story.md) - [依赖说明]
- [Story XX.B文档](./xx.b.xxx.story.md) - [依赖说明]

**架构文档** [Source: docs/architecture/]:
- [coding-standards.md](../architecture/coding-standards.md) - 编码标准
- [tech-stack.md](../architecture/tech-stack.md) - 技术栈
- [xxx-design.md](../architecture/xxx-design.md) - [具体架构]

**源代码位置**:
- `path/to/file.py` - [模块说明] (Story XX.A实现)
- `path/to/another.py` - [模块说明] (Story XX.B实现)
- `ClassName` - 类位置和说明

---

#### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-XX-XX | v1.0 | 创建Story XX.Y，[简要描述] | PM Agent (Sarah) |
| 2025-XX-XX | v2.0 | 🔥 **UltraThink修复**: [修复内容摘要] | PM Agent (Sarah) |

**v2.0修复内容** (如果有):
- ✅ [修复项1]
- ✅ [修复项2]

---

#### Dev Agent Record

##### Agent Model Used
_待Dev Agent填写_

##### Debug Log References
_待Dev Agent填写_

##### Completion Notes List
_待Dev Agent填写_

##### File List
_待Dev Agent填写_

#### QA Results
_待QA Agent填写_

---

## 📚 使用指南

### Step 1: 阅读Epic文档

**在开始编写Story之前**，必须：

1. ✅ 完整阅读parent Epic文档
2. ✅ 理解Epic的业务目标
3. ✅ 识别Epic中的Problem 1, Problem 2等
4. ✅ 理解本Story在Epic中的角色

**为什么这很重要**:
- 避免Story与Epic脱节
- 确保Story解决的是真实问题
- 防止引用不存在的类或功能

### Step 2: 填写Epic Context章节

**这是v3.0的新增必需章节**，按照以下顺序填写：

```markdown
## Epic背景与上下文

**所属Epic**: [从Epic文档复制]
**Epic文档**: [确保链接有效]

**本Story在Epic中的定位**:
- [用1-2句话说明这个Story的作用]
- **依赖**: [列出必须先完成的Story]

**Epic核心问题回顾**:
[从Epic文档复制相关Problem的描述]
- 修复: 本Story [说明本Story做了什么]
- 本Story验证: [说明哪些AC验证了这个修复]
```

**验证清单**:
- [ ] Epic文档路径正确且文件存在
- [ ] Problem编号与Epic文档一致
- [ ] Story依赖已列出且已验证存在
- [ ] 说明了本Story如何解决Epic问题

### Step 3: 编写增强的AC

**v3.0要求每个AC都要链接到Epic**:

```markdown
### AC 1: [AC标题] (验证Problem X修复)
- [验证项]
- **Epic关联**: 直接验证Problem X的修复效果

### AC 2: [AC标题] (Story XX.A依赖)
- [验证项]
- **Story XX.A依赖**: 验证`ClassName`正确工作
```

**最佳实践**:
- 在AC标题中注明验证的Problem或Story
- 在AC结尾添加Epic关联或Story依赖说明
- 确保所有AC都可测量、可验证

### Step 4: 编写增强的任务列表

**v3.0要求所有任务标注AC和Story依赖**:

```markdown
### 任务1: [任务名] (AC: 1)
- [ ] 1.1: [子任务]
- [ ] 1.2: [子任务] (测试Story XX.A)

### 任务2: [任务名] (AC: 2, Story XX.A验证)
- [ ] 2.1: [子任务]
```

**特别注意**:
- 测试数据任务必须详细说明内容
- 不要只写"创建测试文件"
- 要写"创建测试文件，包含3个红色节点，节点内容为..."

### Step 5: 填写前置依赖验证清单

**这是v3.0的新增必需子章节**:

```markdown
**前置依赖验证** (必须先完成):
- [ ] Story XX.A单元测试通过 (file.py)
- [ ] `ClassName`已验证存在: path/to/file.py
- [ ] 外部服务已配置或Mock
```

**如何验证类存在**:
1. 使用Glob工具搜索: `**/*ClassName*.py`
2. 使用Grep工具搜索: `class ClassName`
3. 确认文件路径和类定义存在
4. 在清单中记录: `path/to/file.py (第X行)`

### Step 6: 填写相关文档引用

**这是v3.0的新增必需子章节**:

```markdown
### 🔗 相关文档引用

**Epic和Story文档**:
- [Epic文档](./epic.md)
- [依赖Story文档](./story.md)

**架构文档**:
- [coding-standards.md](../architecture/coding-standards.md)

**源代码位置**:
- `file.py` - 模块说明
```

**为什么这很重要**:
- 集中所有文档引用
- Dev Agent可以快速找到相关信息
- 避免在Dev Notes中分散引用

---

## ✅ 验证清单

在提交Story之前，运行以下检查：

### Epic Context检查
- [ ] ✅ "Epic背景与上下文"章节存在
- [ ] ✅ Epic文档路径正确且文件存在
- [ ] ✅ Problem编号与Epic一致
- [ ] ✅ Story依赖已列出
- [ ] ✅ 说明了本Story在Epic中的作用

### 反幻觉检查
- [ ] ✅ 所有类名已验证存在（使用Glob/Grep）
- [ ] ✅ 所有函数名已验证存在
- [ ] ✅ 所有Story依赖已验证存在
- [ ] ✅ 所有文件路径正确
- [ ] ✅ Dev Notes使用[Source: file.md]注释

### AC和任务检查
- [ ] ✅ 所有AC都链接到Epic问题或Story依赖
- [ ] ✅ 所有任务都标注AC编号
- [ ] ✅ 依赖其他Story的任务标注Story编号
- [ ] ✅ 测试数据任务有详细内容规格

### Dev Notes检查
- [ ] ✅ "前置依赖验证"子章节存在且完整
- [ ] ✅ "相关文档引用"子章节存在且完整
- [ ] ✅ 所有技术声明有来源标注
- [ ] ✅ 代码示例包含验证注释

### 整体质量检查
- [ ] ✅ Story自包含，Dev Agent无需读Epic
- [ ] ✅ 所有依赖明确且可验证
- [ ] ✅ 测试数据详细且可实施
- [ ] ✅ 外部服务有设置说明或Mock策略

---

## 🔄 从v2.0迁移

### 迁移步骤

如果你有使用v2.0模板的现有Story，按以下步骤升级：

#### Step 1: 添加Epic Context章节

在"Status"之后、"Story"之前添加：

```markdown
## Epic背景与上下文

[填写Epic信息...]
```

#### Step 2: 增强AC

在每个AC中添加Epic关联或Story依赖：

```markdown
### AC 1: ... (验证Problem X修复)
...
- **Epic关联**: ...

### AC 2: ... (Story Y依赖)
...
- **Story Y依赖**: ...
```

#### Step 3: 增强任务

为所有任务添加AC和Story依赖标注：

```markdown
### 任务1: ... (AC: 1)
...
### 任务2: ... (AC: 2, Story Y验证)
...
```

#### Step 4: 添加依赖验证清单

在Dev Notes中添加：

```markdown
**前置依赖验证** (必须先完成):
- [ ] Story X已完成...
- [ ] 类Y已验证存在...
```

#### Step 5: 添加文档引用章节

在Dev Notes末尾添加：

```markdown
### 🔗 相关文档引用

**Epic和Story文档**:
...

**架构文档**:
...

**源代码位置**:
...
```

#### Step 6: 更新Change Log

添加迁移记录：

```markdown
| 2025-XX-XX | v2.0 | 迁移到v3.0模板，添加Epic上下文 | PM Agent |
```

### 迁移优先级

**高优先级** (立即迁移):
- 状态为Draft或InProgress的Story
- 验证失败的Story
- 有反幻觉问题的Story

**中优先级** (逐步迁移):
- 状态为Review的Story
- 即将开始实施的Story

**低优先级** (可选):
- 已Done且质量好的Story
- 无问题的历史Story

---

## ❓ 常见问题FAQ

### Q1: 为什么Epic Context是必需的？

**A**: Story 10.9的UltraThink验证发现，缺少Epic上下文导致：
- Story引用了不存在的类（幻觉）
- Story与Epic目标脱节
- 实施准备度大幅下降（从9/10降到5/10）
- 需要额外2小时修复

Epic Context章节强制Story作者在编写时理解Epic背景，从根源预防这些问题。

### Q2: 如何验证类是否存在？

**A**: 使用以下方法：

1. **使用Glob工具**:
   ```
   pattern: **/*ClassName*.py
   ```

2. **使用Grep工具**:
   ```
   pattern: class ClassName
   output_mode: files_with_matches
   ```

3. **记录验证结果**:
   ```markdown
   - [ ] `ClassName`已验证存在: path/to/file.py (第42行)
   ```

### Q3: "前置依赖验证"和"相关文档引用"都是必需的吗？

**A**: 是的，这两个子章节在v3.0中都是必需的。

- **前置依赖验证**: 防止引用不存在的类/函数/Story
- **相关文档引用**: 集中所有文档链接，方便Dev Agent查找

虽然花费额外时间，但可以避免后期更大的修复成本。

### Q4: 如何处理测试数据规格？

**A**: v3.0要求详细说明测试数据内容，不能只写"创建测试文件"。

**❌ 错误示例**:
```markdown
- [ ] 创建测试Canvas文件 (tests/fixtures/test.canvas)
```

**✅ 正确示例**:
```markdown
- [ ] 创建测试Canvas文件 (tests/fixtures/test.canvas)
      - **内容规格**: 包含3个红色节点（模拟待学习问题）
      - 节点ID: red-node-1, red-node-2, red-node-3
      - 节点内容: "什么是逆否命题？", "如何证明充要条件？", "集合的幂集定义"
```

### Q5: 如何处理外部服务依赖？

**A**: v3.0要求在Dev Notes中说明：

1. **外部服务列表**:
   ```markdown
   **外部服务依赖**:
   - Graphiti服务: docker-compose up -d graphiti
   - MCP服务: 由ServiceLauncher启动
   ```

2. **Mock策略** (CI环境):
   ```markdown
   **Mock策略**:
   - 如果服务不可用，使用Mock
   - Mock配置在conftest.py
   ```

3. **在依赖验证清单中记录**:
   ```markdown
   - [ ] Graphiti服务已配置或Mock策略已准备
   ```

### Q6: v3.0会显著增加Story编写时间吗？

**A**: 初期会增加**20-30%**的时间，但：

**时间对比**:
- v2.0编写时间: 2小时
- v3.0编写时间: 2.5小时 (+25%)
- 避免的修复时间: 2小时 (Story 10.9案例)

**净效益**: 节约1.5小时 + 提高质量

随着熟悉v3.0，额外时间会减少到**10-15%**。

### Q7: 可以选择性地使用v3.0特性吗？

**A**: **不可以**。以下特性在v3.0中是**强制的**：

1. ✅ Epic Context & Background章节
2. ✅ 前置依赖验证子章节
3. ✅ 相关文档引用子章节
4. ✅ AC的Epic关联
5. ✅ 任务的AC标注

这些是基于Story 10.9修复经验确定的**最小必需集**，缺少任何一项都可能导致质量问题。

### Q8: 如何知道我的Story符合v3.0标准？

**A**: 使用[验证清单](#验证清单)进行自检。

如果条件允许，建议运行**UltraThink验证**：
1. 使用validate-next-story.md流程
2. 运行10个维度的验证
3. 确保反幻觉评分≥9/10

---

## 📊 v3.0 vs v2.0 对比总结

| 维度 | v2.0 | v3.0 | 改进幅度 |
|------|------|------|----------|
| **Epic关联** | 隐式 | 显式必需 | 🟢 +100% |
| **依赖验证** | 无 | 必需清单 | 🟢 +100% |
| **反幻觉防护** | 无 | 全流程验证 | 🟢 +100% |
| **文档引用** | 零散 | 集中章节 | 🟡 +50% |
| **AC质量** | 基础 | Epic关联 | 🟡 +40% |
| **任务质量** | 基础 | Story依赖 | 🟡 +40% |
| **编写时间** | 基线 | +20-30% | 🟡 初期增加 |
| **修复时间** | 基线 | -80% | 🟢 大幅减少 |
| **实施准备度** | 7/10平均 | 9/10目标 | 🟢 +28% |

---

## 🎉 总结

**Story Template v3.0**基于**Story 10.9的UltraThink验证经验**，通过**强制Epic上下文**、**依赖验证清单**和**反幻觉检查**，从根源预防Story质量问题。

**核心价值**:
1. ✅ 预防反幻觉问题
2. ✅ 确保Story与Epic对齐
3. ✅ 提高实施准备度
4. ✅ 减少后期修复成本

**立即行动**:
- 📖 阅读本指南
- 📝 使用v3.0编写新Story
- 🔄 迁移重要的现有Story
- ✅ 运行验证清单

---

**文档版本**: v1.0
**最后更新**: 2025-10-29
**维护者**: PM Agent (Sarah)
**反馈渠道**: [项目Issue Tracker]
