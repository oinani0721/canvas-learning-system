# Agent描述对比与优化建议

**生成日期**: 2025-10-15
**目的**: 对比当前agent描述与Story/PRD中的详细规格,提供优化建议

---

## 概述

本文档对比了12个Sub-agent的当前YAML描述与Story文件中记录的实际详细规格,为优化agent描述提供依据。

**数据来源**:
- 当前描述: `.claude/agents/*.md` 文件的YAML frontmatter
- 详细规格: `docs/stories/` Epic 1-4 Story文件
- 架构文档: `docs/architecture/sub-agent-templates.md`

---

## 1. canvas-orchestrator (主控Agent)

### 当前描述
```yaml
description: Orchestrates all Canvas learning system operations and sub-agents
```

### Story详细规格 [Source: Story 1.7, 1.10]
- **文件大小**: 658 lines agent definition
- **工作流**: 6-step workflow (解析指令 → 读取Canvas → 调用Sub-agent → 整合结果 → 记录日志 → 报告)
- **支持的操作**: 21 command variants across 11 operation types
- **调用协议**: Natural language calling protocol for all 11 sub-agents
- **Intent recognition**: Recognizes 21 command variants like "拆解", "评分", "生成口语化解释" etc.

### 优化建议 ⭐
```yaml
description: "Orchestrates all Canvas learning system operations, coordinating 11 specialized sub-agents through natural language calling protocol. Supports 21 command variants across 11 operation types (decomposition, explanation, scoring, verification). Handles complete workflow: intent recognition → canvas reading → sub-agent delegation → result integration → reporting."
```

**改进理由**:
- 突出主控Agent的核心职责 (orchestration + coordination)
- 说明支持的11个sub-agents和21种命令
- 描述完整的6步工作流
- 更准确反映Story 1.7和1.10的实现

---

## 2. basic-decomposition (基础拆解)

### 当前描述
```yaml
description: "Decomposes difficult materials into basic guiding questions"
```

### Story详细规格 [Source: Story 2.1]
- **问题数量**: Generates 3-7 questions (not unlimited)
- **问题类型**: 4 types - 定义型 (definitional), 实例型 (example-based), 对比型 (comparative), 探索型 (exploratory)
- **拆解策略**: 4 decomposition strategies
- **输入**: material_content + topic (user_understanding is null)
- **测试覆盖**: 100% test coverage
- **QA评分**: 5/5 stars (Excellent)

### 优化建议 ⭐
```yaml
description: "Decomposes difficult materials into 3-7 basic guiding questions using 4 question types (定义型/实例型/对比型/探索型). Helps transition from 'completely lost' (red nodes) to 'partial understanding' (purple nodes) through structured questioning."
```

**改进理由**:
- 明确问题数量范围 (3-7个)
- 列出4种问题类型 (Story 2.1核心特性)
- 说明教育目标 (red → purple transition)
- 更准确反映Story 2.1的AC要求

---

## 3. deep-decomposition (深度拆解)

### 当前描述
```yaml
description: "Creates deep verification questions to test true understanding"
```

### Story详细规格 [Source: Story 2.2]
- **问题数量**: Generates 3-10 deep questions (vs basic's 3-7)
- **问题类型**: 4 types - 对比型 (comparative), 原因型 (causal), 应用型 (application), 边界型 (boundary)
- **关键区别**: Requires `user_understanding` field (basic-decomposition does NOT)
- **目标**: Transition from purple (似懂非懂) to green (完全理解)
- **问题性质**: 检验型 (verification) vs 引导型 (guiding)
- **QA评分**: 5/5 stars (Excellent)

### 优化建议 ⭐
```yaml
description: "Creates 3-10 deep verification questions to test true understanding and expose blind spots. Uses 4 question types (对比型/原因型/应用型/边界型). Requires user's existing understanding as input. Helps transition from partial understanding (purple nodes) to complete mastery (green nodes)."
```

**改进理由**:
- 明确与basic-decomposition的区别 (deep vs basic, 检验型 vs 引导型)
- 说明需要user_understanding input (关键差异)
- 列出4种深度问题类型
- 说明教育目标 (purple → green transition)

---

## 4. question-decomposition (问题拆解)

### 当前描述
```yaml
description: "Generates verification questions to test understanding for purple nodes"
```

### Story详细规格 [Source: Story 2.3]
- **目标节点**: 针对紫色节点 (似懂非懂状态)
- **问题性质**: Problem-solving breakthrough questions
- **教育目的**: 帮助从partial understanding过渡到full understanding
- **与deep-decomposition的关系**: 类似但侧重点不同

### 优化建议 ⭐
```yaml
description: "Generates problem-solving breakthrough questions specifically for purple nodes (partial understanding). Helps students transition from 'seems to understand' to 'truly understands' through targeted questioning."
```

**改进理由**:
- 明确针对purple nodes
- 说明"breakthrough questions"的性质
- 描述教育转化目标

---

## 5. oral-explanation (口语化解释)

### 当前描述
```yaml
description: "Generates oral-style explanations (800-1200 words) like a professor teaching"
```

### Story详细规格 [Source: Story 3.1]
- **字数**: 800-1200 words (already in current description ✓)
- **结构**: 4-element structure:
  1. **背景铺垫** (background context)
  2. **核心解释** (core explanation)
  3. **生动举例** (vivid examples)
  4. **常见误区** (common misconceptions)
- **风格**: Like a professor teaching orally, not written academic text
- **输出**: Creates `.md` file with emoji 🗣️
- **命名**: `{concept}-口语化解释-{timestamp}.md`

### 优化建议 ⭐
```yaml
description: "Generates 800-1200 word oral-style explanations like a professor teaching, with 4-element structure: background context, core explanation, vivid examples, and common misconceptions. Creates .md files with emoji 🗣️."
```

**改进理由**:
- 保留字数 (核心规格)
- 添加4-element结构说明 (Story 3.1关键特性)
- 说明输出格式 (.md file + emoji)
- 更完整反映Story 3.1实现

---

## 6. clarification-path (澄清路径)

### 当前描述
```yaml
description: "Generates 1500+ word in-depth explanations following 4-step process"
```

### Story详细规格 [Source: Story 3.2]
- **字数**: 1500+ words (already in current description ✓)
- **结构**: 4-step process:
  1. **问题澄清** (problem clarification)
  2. **概念拆解** (concept decomposition)
  3. **深度解释** (deep explanation)
  4. **验证总结** (verification summary)
- **输出**: Creates `.md` file with emoji 🔍
- **目标**: For students who need systematic, step-by-step clarification

### 优化建议 ⭐
```yaml
description: "Generates 1500+ word in-depth explanations following 4-step process: problem clarification, concept decomposition, deep explanation, and verification summary. Creates .md files with emoji 🔍. Ideal for systematic clarification of complex concepts."
```

**改进理由**:
- 保留字数 (核心规格)
- 详细说明4-step process (Story 3.2核心方法)
- 添加emoji和输出格式
- 说明适用场景

---

## 7. comparison-table (对比表)

### 当前描述
```yaml
description: "Generates structured comparison tables for distinguishing similar concepts"
```

### Story详细规格 [Source: Story 3.3]
- **格式**: Markdown table format
- **结构**: 多维度对比 (definition, characteristics, use cases, examples, common errors)
- **输出**: Creates `.md` file with emoji 📊
- **目标**: Distinguish易混淆概念 (similar/confusing concepts)
- **典型场景**: "逆否命题 vs 否命题", "类 vs 对象"

### 优化建议 ⭐
```yaml
description: "Generates structured comparison tables in markdown format for distinguishing similar/confusing concepts. Compares across multiple dimensions: definitions, characteristics, use cases, examples, and common errors. Creates .md files with emoji 📊."
```

**改进理由**:
- 说明输出格式 (markdown table)
- 列出对比维度 (Story 3.3的标准结构)
- 添加emoji
- 说明适用场景 (易混淆概念)

---

## 8. memory-anchor (记忆锚点)

### 当前描述
```yaml
description: "Generates vivid analogies, stories, and mnemonics to aid long-term memory"
```

### Story详细规格 [Source: Story 3.4]
- **内容类型**: 3 types - analogies (类比), stories (故事), mnemonics (记忆口诀)
- **输出**: Creates `.md` file with emoji ⚓
- **目标**: Aid long-term memory retention (already in current description ✓)
- **典型场景**: "理解了但记不住"的情况

### 优化建议 ⭐
```yaml
description: "Generates vivid analogies, stories, and mnemonics to aid long-term memory retention. Creates .md files with emoji ⚓. Ideal for concepts that are understood but hard to remember."
```

**改进理由**:
- 保留核心描述 (已经很准确)
- 添加输出格式 (emoji ⚓)
- 说明适用场景

---

## 9. four-level-explanation (四层次答案)

### 当前描述
```yaml
description: "Generates progressive four-level explanations from beginner to innovation"
```

### Story详细规格 [Source: Story 3.5]
- **4个层次**:
  1. 新手层 (Beginner) - 300-400 words
  2. 进阶层 (Intermediate) - 300-400 words
  3. 专家层 (Expert) - 300-400 words
  4. 创新层 (Innovation) - 300-400 words
- **总字数**: 1200-1600 words
- **输出**: Creates `.md` file with emoji 🎯
- **渐进性**: Progressive depth, each level builds on previous

### 优化建议 ⭐
```yaml
description: "Generates progressive 4-level explanations (新手→进阶→专家→创新), 300-400 words per level, total 1200-1600 words. Each level builds on the previous, allowing learners to choose their starting point. Creates .md files with emoji 🎯."
```

**改进理由**:
- 明确4个层次名称 (中文)
- 说明每层字数和总字数 (Story 3.5核心规格)
- 强调渐进性 (progressive nature)
- 添加emoji和输出格式

---

## 10. example-teaching (例题教学)

### 当前描述
```yaml
description: "Generates complete example problems with detailed solutions"
```

### Story详细规格 [Source: Story 3.6]
- **字数**: ~1000 words (800-1200 range)
- **6个section结构**:
  1. **题目** (Problem statement)
  2. **思路分析** (Solution approach analysis)
  3. **分步求解** (Step-by-step solution)
  4. **易错点提醒** (Common mistakes reminder)
  5. **变式练习** (Variation practice problems)
  6. **答案提示** (Answer hints)
- **输出**: Creates `.md` file with emoji 📝
- **目标**: Complete problem-solving tutorial

### 优化建议 ⭐
```yaml
description: "Generates complete problem-solving tutorials (~1000 words) with 6 sections: 题目, 思路分析, 分步求解, 易错点提醒, 变式练习, 答案提示. Creates .md files with emoji 📝. Ideal for learning through worked examples."
```

**改进理由**:
- 添加字数范围 (~1000 words)
- 列出完整的6-section结构 (Story 3.6核心特性)
- 添加emoji和输出格式
- 说明教育目的 (learning through examples)

---

## 11. scoring-agent (评分Agent)

### 当前描述
```yaml
description: "Evaluates user's understanding in yellow nodes using 4-dimension scoring"
```

### Story详细规格 [Source: Story 2.8, 2.9]
- **4个维度** (4-dimension scoring):
  1. **Accuracy** (准确性) - 25 points
  2. **Imagery** (具象性) - 25 points
  3. **Completeness** (完整性) - 25 points
  4. **Originality** (原创性) - 25 points
- **总分**: 100 points (25 × 4)
- **阈值**:
  - ≥80分 → 绿色 (完全理解)
  - 60-79分 → 紫色 (似懂非懂)
  - <60分 → 保持红色 (不理解)
- **智能建议** (Story 2.9): Dimension-based agent recommendations
- **输出**: JSON format with scores + suggestions

### 优化建议 ⭐
```yaml
description: "Evaluates user's understanding in yellow nodes using 4-dimension scoring: Accuracy, Imagery, Completeness, Originality (25 points each, total 100). Generates intelligent agent recommendations based on dimension weaknesses. Determines color transitions: ≥80=green, 60-79=purple, <60=red."
```

**改进理由**:
- 列出4个维度名称 (核心评分标准)
- 说明分数分配 (每个25分,总分100)
- 添加智能推荐功能 (Story 2.9创新特性)
- 说明颜色流转规则 (教育系统核心逻辑)

---

## 12. verification-question-agent (检验问题生成)

### 当前描述
```yaml
description: "Generates deep verification questions from red/purple nodes to reveal understanding gaps"
```

### Story详细规格 [Source: Story 4.2 - Epic 4核心Agent]
- **输入**: Red nodes + purple nodes + related yellow understanding
- **输出数量**:
  - Red nodes: 1-2 questions (突破型/基础型)
  - Purple nodes: 2-3 questions (检验型/应用型)
- **问题类型**:
  - 突破型 (Breakthrough): Alternative perspectives
  - 基础型 (Foundational): Lower barrier questions
  - 检验型 (Verification): Test true understanding
  - 应用型 (Application): Transfer to new scenarios
- **目标**: Reveal understanding gaps and blind spots
- **Epic 4地位**: Core agent for paperless review system

### 优化建议 ⭐
```yaml
description: "Generates deep verification questions from red/purple nodes to reveal understanding gaps. Red nodes: 1-2 突破型/基础型 questions; Purple nodes: 2-3 检验型/应用型 questions. Core agent for Epic 4 paperless review system. Analyzes user's yellow node understanding to identify blind spots."
```

**改进理由**:
- 明确问题数量 (red: 1-2, purple: 2-3)
- 列出问题类型 (4种类型)
- 强调Epic 4核心地位
- 说明分析黄色节点理解的能力

---

## 总结

### 优化统计

| Agent | 当前描述长度 | 优化后长度 | 改进幅度 | 关键改进 |
|-------|------------|-----------|---------|---------|
| canvas-orchestrator | 短 (~10词) | 详细 (~40词) | +300% | 添加21命令,11代理,6步流程 |
| basic-decomposition | 简单 (~8词) | 详细 (~25词) | +200% | 添加3-7问题,4类型 |
| deep-decomposition | 简单 (~8词) | 详细 (~35词) | +300% | 添加3-10问题,user_understanding要求 |
| question-decomposition | 简单 (~10词) | 详细 (~20词) | +100% | 明确purple nodes,breakthrough性质 |
| oral-explanation | 较详细 (~12词) | 详细 (~25词) | +100% | 添加4-element结构,emoji |
| clarification-path | 较详细 (~10词) | 详细 (~30词) | +200% | 添加4-step process细节 |
| comparison-table | 适中 (~10词) | 详细 (~25词) | +150% | 添加对比维度,emoji |
| memory-anchor | 适中 (~12词) | 详细 (~20词) | +70% | 添加emoji,适用场景 |
| four-level-explanation | 简单 (~8词) | 详细 (~35词) | +300% | 添加字数,4层次名称 |
| example-teaching | 简单 (~7词) | 详细 (~25词) | +250% | 添加6-section结构 |
| scoring-agent | 适中 (~10词) | 详细 (~35词) | +250% | 添加4维度,分数,颜色规则 |
| verification-question-agent | 适中 (~12词) | 详细 (~35词) | +200% | 添加问题数量,类型,Epic 4地位 |

### 关键发现

1. **当前描述普遍过于简略**:
   - 缺少具体数字 (问题数量,字数范围)
   - 缺少结构细节 (4-element, 6-section等)
   - 缺少输出格式 (emoji, .md文件)

2. **Story文件包含丰富的实现细节**:
   - 用户正确: "有更详细的描述,但是你却没有找到相关文件"
   - Epic 1-4 Story文件记录了完整的agent规格
   - 测试AC和QA审查提供了质量验证

3. **优化原则**:
   - **具体化**: 添加数字 (3-7问题,1200-1600字)
   - **结构化**: 说明内部结构 (4维度,6 sections)
   - **场景化**: 说明适用场景和教育目标
   - **标准化**: 添加emoji,输出格式

---

## 下一步行动

1. ✅ **本文档已完成**: Agent描述对比与优化建议
2. ⏳ **待执行**: 更新所有12个agent的YAML frontmatter描述
3. ⏳ **待执行**: 创建CLAUDE.md (使用优化后的描述)
4. ⏳ **待执行**: 创建README.md (完整项目文档)
5. ⏳ **待执行**: 提供打包文件清单

---

**文档生成者**: Claude (Ultrathink deep analysis mode)
**数据来源**: Epic 1-4 Story files (26个story文件完整分析)
**质量保证**: 所有规格均可追溯到具体Story文件和行号
