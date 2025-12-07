<!-- Powered by BMAD Core -->

# Code Review检查清单 - 零幻觉开发原则

**版本**: v1.0
**创建日期**: 2025-11-14
**用途**: Story 0.6 - Code Review检查清单集成
**关联文档**:
- CLAUDE.md (零幻觉开发原则)
- create-next-story.md (Step 3.5 技术文档验证)
- technical-verification-checklist.md (技术验证详细清单)

---

## 📋 使用说明

**何时使用此检查清单**:
- Dev Agent完成Story开发后，进行Code Review前
- SM Agent审查Story实现质量时
- 任何代码合并到主分支前

**检查方式**:
- 逐项检查，标记 ✅ 通过 或 ❌ 不通过
- 所有检查项必须通过（✅），否则代码不能合并
- 如有不通过项（❌），必须记录原因并修复后重新检查

**检查清单结构**:
1. Section 1: 零幻觉开发4大强制规则
2. Section 2: 技术文档验证
3. Section 3: 代码标注规范
4. Section 4: Skills和Context7使用
5. Section 5: 质量门禁

---

## Section 1: 零幻觉开发4大强制规则 ⚠️

**检查目标**: 确保代码遵守CLAUDE.md中的4大强制规则

### 规则1: 提到什么技术，立即查看对应Skill或Context 7

- [ ] **检查项 1.1**: Story Dev Notes中是否列出了所有涉及的技术栈？
  - 验证方法: 检查Story文件的技术栈清单section
  - 通过标准: 所有核心技术栈已列出

- [ ] **检查项 1.2**: 每个技术栈是否标注了查询方式（Skill/Context7）？
  - 验证方法: 技术栈清单中每项是否有[Skill]或[Context7]标记
  - 通过标准: 100%技术栈已分类

- [ ] **检查项 1.3**: 是否有证据表明实际执行了Skills激活或Context7查询？
  - 验证方法: 检查Story Dev Notes中的技术验证报告
  - 通过标准: 有明确的查询时间戳和结果摘要

### 规则2: 开发时必须持续查阅Skills/Context7，不能仅依赖记忆

- [ ] **检查项 2.1**: 代码中是否有未验证的新API调用？
  - 验证方法: 搜索代码中的import语句和函数调用，交叉验证Story Dev Notes中的API验证列表
  - 通过标准: 所有API调用都在验证列表中

- [ ] **检查项 2.2**: 函数参数是否与官方文档一致？
  - 验证方法: 随机抽查3个API调用，对照Story Dev Notes中记录的参数列表
  - 通过标准: 100%参数匹配

- [ ] **检查项 2.3**: 是否有未记录的技术假设？
  - 验证方法: Code Review过程中发现任何"我认为这个API应该..."的注释
  - 通过标准: 零技术假设，所有细节有文档依据

### 规则3: 每个API调用必须标注文档来源

- [ ] **检查项 3.1**: 核心API调用是否有来源标注？
  - 验证方法: 检查代码中的注释，格式: # ✅ Verified from [来源]
  - 通过标准: 核心API 100%标注，辅助API ≥80%标注

- [ ] **检查项 3.2**: 来源标注是否准确？
  - 验证方法: 抽查3个标注，验证是否可追溯到实际文档位置
  - 通过标准: 100%标注可追溯

- [ ] **检查项 3.3**: 来源标注是否包含具体位置？
  - 验证方法: 检查标注是否包含SKILL.md行号或Context7 topic
  - 通过标准: ≥80%标注包含具体位置

### 规则4: 未验证的API不允许进入代码

- [ ] **检查项 4.1**: 是否有"待验证"或"TODO: 验证"的标记？
  - 验证方法: 全文搜索"待验证", "TODO", "FIXME", "verify"
  - 通过标准: 零未验证API

- [ ] **检查项 4.2**: 是否有明确标记"来源: 猜测"或"来源: 内部知识"？
  - 验证方法: 搜索代码注释中的猜测性语言
  - 通过标准: 零猜测性实现

- [ ] **检查项 4.3**: 所有API调用是否都有对应的Skills/Context7查询记录？
  - 验证方法: API调用总数 = Story Dev Notes中验证的API数量
  - 通过标准: 100%匹配

---

## Section 2: 技术文档验证

**检查目标**: 确保Story开发前执行了create-next-story.md的Step 3.5

### Step 3.5.1: 识别涉及的技术栈

- [ ] **检查项 2.1**: Story Dev Notes是否包含"技术栈清单"？
  - 位置: Story文件的"Dev Notes" → "技术验证报告" → "技术栈清单"
  - 通过标准: 有清单，且非空

- [ ] **检查项 2.2**: 技术栈清单是否完整？
  - 验证方法: 对照代码中的import语句，确认所有外部库已列出
  - 通过标准: 100%覆盖

### Step 3.5.2: 确定文档查询方式

- [ ] **检查项 2.3**: 每个技术栈是否标注了Skill或Context7？
  - 格式: [Skill] LangGraph → @langgraph
  - 格式: [Context7] FastAPI → /websites/fastapi_tiangolo
  - 通过标准: 100%技术栈已分类

### Step 3.5.3: 激活Skills或查询Context7

- [ ] **检查项 2.4**: 是否有Skills激活记录？
  - 验证方法: 检查Story Dev Notes中是否记录了"@skill-name"的使用
  - 通过标准: 所有[Skill]标记的技术栈都有激活记录

- [ ] **检查项 2.5**: 是否有Context7查询记录？
  - 验证方法: 检查Story Dev Notes中是否记录了Library ID和查询topic
  - 通过标准: 所有[Context7]标记的技术栈都有查询记录

### Step 3.5.4: 执行技术验证检查清单

- [ ] **检查项 2.6**: 是否引用了technical-verification-checklist.md？
  - 验证方法: Story Dev Notes中是否提到"技术验证检查清单"
  - 通过标准: 明确引用或执行记录

### Step 3.5.5: 收集官方代码示例

- [ ] **检查项 2.7**: Story Dev Notes是否包含"代码示例库"？
  - 位置: Story文件的"Dev Notes" → "代码示例库"
  - 通过标准: 每个核心技术栈至少1个代码示例

- [ ] **检查项 2.8**: 代码示例是否包含文档来源标注？
  - 验证方法: 每个示例是否标注了"来源: SKILL.md:行号"或"Context7: topic"
  - 通过标准: 100%示例有来源

### Step 3.5.6: Quality Gate 检查

- [ ] **检查项 2.9**: Story Dev Notes是否包含"Quality Gate状态"？
  - 位置: Story文件的"Dev Notes" → "技术验证报告" → "Quality Gate状态"
  - 期望值: "✅ PASSED"
  - 通过标准: 状态为PASSED

### Step 3.5.7: 在Story中记录验证结果

- [ ] **检查项 2.10**: Story Dev Notes是否包含完整的"技术验证报告"？
  - 必需子章节: 技术栈清单, 核心API验证结果, 代码示例库, 技术约束和注意事项
  - 通过标准: 所有子章节完整

---

## Section 3: 代码标注规范

**检查目标**: 确保代码标注符合CLAUDE.md的标准格式

### 标注格式检查

- [ ] **检查项 3.1**: 核心API调用是否使用标准格式？
  - 标准格式:
  - 示例:
  - 通过标准: 核心API 100%使用标准格式

- [ ] **检查项 3.2**: 来源类型是否正确标注？
  - Skills来源:
  - Context7来源:
  - 官方文档来源:
  - 通过标准: 100%来源类型正确

- [ ] **检查项 3.3**: 标注位置是否正确？
  - 要求: 标注必须在API调用的正上方（不能在同行或下方）
  - 通过标准: 100%标注位置正确

### 标注完整性检查

- [ ] **检查项 3.4**: 是否有缺失标注的核心API？
  - 验证方法: Code Review过程中主动搜索未标注的API调用
  - 通过标准: 零缺失

- [ ] **检查项 3.5**: 辅助API标注覆盖率是否达标？
  - 定义: 辅助API = 非核心业务逻辑的API（如logging, datetime等）
  - 通过标准: 辅助API标注覆盖率 ≥80%

---

## Section 4: Skills和Context7使用

**检查目标**: 确保正确使用Skills和Context7 MCP

### Skills使用检查

- [ ] **检查项 4.1**: 是否优先使用Skills而非Context7？
  - 验证方法: 对于有Skills的技术栈（langgraph, graphiti, obsidian-canvas），是否使用了Skill而非Context7
  - 通过标准: 100%优先使用Skills

- [ ] **检查项 4.2**: Skills激活方式是否正确？
  - 正确方式: 在对话中使用
  - 通过标准: Story Dev Notes中有明确的Skills激活记录

- [ ] **检查项 4.3**: 是否从正确的SKILL.md位置引用？
  - 验证方法: 抽查3个Skills来源标注，确认SKILL.md行号正确
  - 通过标准: 100%行号正确（±5行误差可接受）

### Context7使用检查

- [ ] **检查项 4.4**: Context7 Library ID是否正确？
  - 验证方法: 对照CLAUDE.md中的Context7映射表
  - 示例: FastAPI → /websites/fastapi_tiangolo
  - 通过标准: 100% Library ID正确

- [ ] **检查项 4.5**: Context7查询topic是否具体？
  - 不合格示例: topic="general"
  - 合格示例: topic="dependency injection", topic="async operations"
  - 通过标准: 所有Context7查询都有具体topic

- [ ] **检查项 4.6**: 是否记录了Context7查询结果？
  - 验证方法: Story Dev Notes中是否摘录了Context7返回的关键信息
  - 通过标准: 每个Context7查询都有结果摘要

### 决策树遵循检查

- [ ] **检查项 4.7**: 是否遵守"Skills → Context7 → 官方文档"的优先级？
  - 验证方法: 检查是否有跳过Skills直接使用Context7的情况
  - 通过标准: 100%遵守决策树

- [ ] **检查项 4.8**: 如果使用了官方文档（WebFetch），是否记录了原因？
  - 原因示例: "Skills和Context7都不包含此API的文档"
  - 通过标准: 所有官方文档查询都有使用原因

---

## Section 5: 质量门禁

**检查目标**: 最终质量验收，决定代码是否可以合并

### 强制通过标准（任一失败则Code Review不通过）

- [ ] **门禁 5.1**: Section 1所有检查项通过率 = 100%
  - 说明: 零幻觉开发4大强制规则不允许有任何不通过项

- [ ] **门禁 5.2**: Section 2 Quality Gate检查项（2.9）通过
  - 说明: Story Dev Notes必须包含"Quality Gate状态: ✅ PASSED"

- [ ] **门禁 5.3**: Section 3核心API标注通过率 = 100%
  - 说明: 所有核心API必须有正确的来源标注

- [ ] **门禁 5.4**: Section 4 Skills/Context7使用优先级正确
  - 说明: 必须遵守决策树，不允许跳过Skills

### 警告级别（可通过但需要记录改进计划）

- [ ] **警告 5.5**: 辅助API标注覆盖率 < 80%
  - 后果: 需在Story Notes中记录改进计划

- [ ] **警告 5.6**: 代码示例库不足（每个核心技术栈 < 1个示例）
  - 后果: 需在下一个Story中补充

- [ ] **警告 5.7**: Context7查询topic过于宽泛
  - 后果: 需在Story Notes中记录更具体的topic供后续参考

### Code Review通过标记

**最终判定**:
- [ ] **所有强制门禁（5.1-5.4）通过** → Code Review通过 ✅
- [ ] **任一强制门禁失败** → Code Review不通过 ❌，需修复后重新Review

**警告级别处理**:
- 警告级别不阻塞合并，但必须记录改进计划
- 如果警告级别 ≥3项，建议推迟合并直到修复

---

## 📊 Code Review执行记录模板

**Story**: {epicNum}.{storyNum} - {Story名称}
**Reviewer**: {Agent名称}
**Review日期**: {YYYY-MM-DD}

### 检查结果摘要

| Section | 检查项总数 | 通过 | 不通过 | 通过率 |
|---------|-----------|------|--------|--------|
| Section 1: 零幻觉规则 | 11 | {N} | {M} | {N/11}% |
| Section 2: 技术验证 | 10 | {N} | {M} | {N/10}% |
| Section 3: 代码标注 | 5 | {N} | {M} | {N/5}% |
| Section 4: Skills/Context7 | 8 | {N} | {M} | {N/8}% |
| Section 5: 质量门禁 | 4 | {N} | {M} | {N/4}% |
| **总计** | **38** | **{N}** | **{M}** | **{N/38}%** |

### 不通过项详情

1. **检查项 X.Y**: {检查项名称}
   - 问题描述: {具体问题}
   - 修复建议: {如何修复}
   - 预计修复时间: {小时}

### 警告项

1. **警告 5.X**: {警告项名称}
   - 改进计划: {如何改进}

### 最终判定

- [ ] ✅ **通过** - 所有强制门禁通过，代码可合并
- [ ] ❌ **不通过** - 存在{N}个不通过项，需修复后重新Review
- [ ] ⚠️ **条件通过** - 强制门禁通过，但有{N}个警告项需改进

**审查意见**:
{Reviewer的总体评价和建议}

---

**文档版本**: v1.0
**最后更新**: 2025-11-14
**维护者**: SM Agent (Bob)
