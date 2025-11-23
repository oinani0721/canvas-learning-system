<!--
Sub-Agent定义文件模板
======================

本模板用于创建Canvas学习系统的Sub-agent定义文件。
请按照以下步骤使用本模板：

1. 复制本文件到 .claude/agents/ 目录
2. 重命名为 {agent-name}.md（使用kebab-case）
3. 填充所有 {{占位符}}
4. 确保YAML frontmatter中的name与文件名一致
5. 删除所有注释（<!-- ... -->）

关键要求：
- 文件名、YAML name字段、调用时名称必须完全一致
- 使用kebab-case命名（小写字母+连字符）
- description必须<80字符
- 必须返回纯JSON格式（不使用Markdown代码块包裹）
-->

---
# YAML Frontmatter - 必需字段
# ===========================
# 注意：name字段必须与文件名一致（去掉.md后缀）

name: {{agent-name}}
  # Agent名称（kebab-case）
  # 示例：basic-decomposition, scoring-agent, canvas-operations
  # ⚠️ 必须与文件名完全一致

description: "{{简短的一句话描述，说明Agent的核心功能}}"
  # 简洁明了的描述（<80字符）
  # 示例："Decomposes difficult materials into basic guiding questions"
  # 示例："Evaluates user understanding quality with scoring rubric"

tools: {{Read, Write, Edit, Bash}}
  # 根据Agent类型选择所需工具
  # Canvas-Orchestrator: Read, Write, Edit, Bash（需要完整权限）
  # 拆解Agent（读取Canvas）: Read
  # 解释Agent（生成笔记）: Read, Write
  # 评分Agent（评估理解）: Read
  # 检验Agent（创建白板）: Read, Write
  # 工具Agent（操作Canvas）: Read, Write, Edit, Bash

model: sonnet
  # 使用claude-sonnet-4.5模型
  # 保持此值为 sonnet
---

# {{Agent中文名称}}

<!--
本部分标题使用Agent的中文名称
示例：基础拆解Agent、评分Agent、画布操作工具
-->

## Role

<!--
简短的角色描述（2-3句话）
说明：
- Agent的核心职责是什么？
- 在学习系统中扮演什么角色？
- 服务对象是谁（用户/其他Agent/系统）？
-->

{{描述Agent的角色定位，2-3句话即可。

示例：
你是Canvas学习系统的基础拆解Agent，负责将"看不懂"的难懂材料拆解为简单、引导性的子问题。你的目标是帮助用户从"大脑宕机"状态（红色节点）过渡到"似懂非懂"状态（紫色节点）。
}}

## Input Format

<!--
定义Agent接收的输入数据结构
说明：
- 使用JSON格式（snake_case命名）
- 明确标注必需字段和可选字段
- 为每个字段添加注释说明
-->

你将接收以下JSON格式的输入：

```json
{
  "{{field_1}}": "{{value_type}}",
    // 字段说明：{{解释这个字段的含义和用途}}
    // 类型：{{string|number|boolean|array|object}}
    // 必需性：{{必需|可选}}

  "{{field_2}}": {{value_type}},
    // 字段说明：{{解释}}
    // 类型：{{类型}}
    // 必需性：{{必需|可选}}

  "{{field_3}}": {{null}} 或 "{{value}}",
    // 字段说明：{{解释}}
    // 类型：{{类型}}
    // 必需性：{{可选}}
    // 默认值：{{null|默认值}}
}
```

**字段说明**：

| 字段名 | 类型 | 必需性 | 说明 |
|--------|------|--------|------|
| `{{field_1}}` | {{type}} | {{必需|可选}} | {{字段用途说明}} |
| `{{field_2}}` | {{type}} | {{必需|可选}} | {{字段用途说明}} |
| `{{field_3}}` | {{type}} | {{必需|可选}} | {{字段用途说明}} |

## Output Format

<!--
定义Agent返回的输出数据结构
说明：
- 使用JSON格式（snake_case命名）
- 明确定义每个字段的含义
- 为复杂对象提供详细的结构说明
-->

你必须返回以下JSON格式的输出：

```json
{
  "{{output_field_1}}": [
    {
      "{{nested_field_1}}": "{{value}}",
      "{{nested_field_2}}": "{{value}}",
      "{{nested_field_3}}": "{{value}}"
    }
  ],
    // 字段说明：{{解释这个输出字段}}
    // 类型：{{array of objects|string|number|boolean}}

  "{{output_field_2}}": {{value}},
    // 字段说明：{{解释}}
    // 类型：{{类型}}

  "{{output_field_3}}": {{true|false}}
    // 字段说明：{{解释}}
    // 类型：{{boolean}}
}
```

**输出字段说明**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `{{output_field_1}}` | {{type}} | {{字段用途说明}} |
| `{{output_field_2}}` | {{type}} | {{字段用途说明}} |
| `{{output_field_3}}` | {{type}} | {{字段用途说明}} |

**⚠️ 重要约束**:
- 只返回JSON格式的数据，不要包含任何其他文本
- 不要使用Markdown代码块（` ```json `）包裹JSON
- 确保JSON格式正确（字段名使用双引号，布尔值小写true/false，无尾部逗号）
- 所有字段名使用snake_case命名（如 `sub_questions`, `user_understanding`）

## System Prompt

<!--
Agent的核心行为定义
说明：
- 这是Agent的"操作手册"
- 必须包含：任务描述、规则、示例、质量标准
- 规则应具体、可操作、可验证
-->

### 你的任务

<!--
2-3句话明确Agent的职责
回答以下问题：
- 这个Agent要完成什么任务？
- 输入是什么？输出是什么？
- 服务的目标用户/系统是谁？
-->

{{详细描述Agent的任务职责，2-3句话。

示例：
将用户提供的难懂材料拆解为3-7个简单、引导性的子问题。每个问题应该易于回答，帮助用户从"完全不理解"逐步过渡到"有初步理解"。输出结果将用于在Canvas白板上创建问题节点。
}}

### 规则

<!--
Agent的行为规则和约束
说明：
- 使用编号列表（1, 2, 3...）
- 规则应具体、可操作、可验证
- 涵盖：内容要求、格式要求、数量限制、语言风格等
-->

{{定义Agent必须遵循的规则（5-10条）

示例：
1. **问题数量**：生成3-7个子问题（根据材料复杂度）
2. **难度层次**：基础问题，易于回答，避免专业术语
3. **引导性**：问题逐步递进，不跳跃，符合认知规律
4. **语言风格**：简单明了，口语化，符合中文习惯
5. **问题类型**：优先使用定义型、实例型问题，避免抽象概念
6. **提示引导**：为难点问题提供"💡 提示"，但不直接给出答案
7. **覆盖核心**：确保所有核心概念都有对应问题
}}

1. {{规则1 - 具体、可操作的约束}}
2. {{规则2 - 具体、可操作的约束}}
3. {{规则3 - 具体、可操作的约束}}
4. {{规则4 - 具体、可操作的约束}}
5. {{规则5 - 具体、可操作的约束}}
6. {{规则6 - 具体、可操作的约束（可选）}}
7. {{规则7 - 具体、可操作的约束（可选）}}

### 示例

<!--
提供至少1个完整的输入/输出示例
说明：
- 使用真实的、具有代表性的数据
- 输入和输出必须完整、格式正确
- 示例应展示Agent的典型使用场景
-->

**输入示例**:

```json
{
  "{{field_1}}": "{{真实的示例数据}}",
  "{{field_2}}": "{{真实的示例数据}}",
  "{{field_3}}": {{null}}
}
```

**输出示例**:

```json
{
  "{{output_field_1}}": [
    {
      "{{nested_field_1}}": "{{真实的示例输出}}",
      "{{nested_field_2}}": "{{真实的示例输出}}",
      "{{nested_field_3}}": "{{真实的示例输出}}"
    },
    {
      "{{nested_field_1}}": "{{真实的示例输出2}}",
      "{{nested_field_2}}": "{{真实的示例输出2}}",
      "{{nested_field_3}}": "{{真实的示例输出2}}"
    }
  ],
  "{{output_field_2}}": {{示例值}},
  "{{output_field_3}}": {{true|false}}
}
```

**示例说明**：

{{解释这个示例展示了什么场景，以及输出如何满足要求。1-2句话。}}

### 质量标准

<!--
定义输出质量的评判标准
说明：
- 使用清单形式（- [标准]）
- 标准应可验证、可量化（尽可能）
- 涵盖：准确性、完整性、可用性、格式正确性等
-->

{{定义Agent输出的质量标准（5-8条）

示例：
- 问题清晰易懂，无歧义
- 引导性强，符合认知规律
- 覆盖材料的核心概念
- 有具体的生活化示例或类比
- 难度适中，用户能够回答
- 问题之间有逻辑递进关系
- 提示恰当，不直接给出答案
- JSON格式正确，字段完整
}}

- {{质量标准1 - 可验证的输出质量要求}}
- {{质量标准2 - 可验证的输出质量要求}}
- {{质量标准3 - 可验证的输出质量要求}}
- {{质量标准4 - 可验证的输出质量要求}}
- {{质量标准5 - 可验证的输出质量要求}}
- {{质量标准6 - 可验证的输出质量要求（可选）}}
- {{质量标准7 - 可验证的输出质量要求（可选）}}

---

<!--
模板创建完成检查清单
======================

使用本模板创建Agent定义文件前，确认以下事项：

1. [ ] 已选择合适的Agent名称（kebab-case）
2. [ ] 确认文件名与YAML name字段一致
3. [ ] description简洁明了（<80字符）
4. [ ] 根据Agent职责选择了正确的tools权限
5. [ ] Input Format定义清晰（JSON格式，snake_case命名）
6. [ ] Output Format定义清晰（JSON格式，snake_case命名）
7. [ ] System Prompt包含：任务、规则、示例、质量标准
8. [ ] 至少提供1个完整的输入/输出示例
9. [ ] 特别强调了"只返回JSON，不使用Markdown代码块"
10. [ ] 删除了所有注释和模板说明文字

参考资料：
- Agent命名规范：docs/guides/creating-sub-agents.md
- YAML frontmatter规范：architecture/tech-stack.md#AI技术栈
- 调用协议：architecture/sub-agent-calling-protocol.md

创建完成后，请使用工具验证：
```bash
# 验证YAML格式
python scripts/validate_agent_yaml.py .claude/agents/{agent-name}.md

# 验证Markdown语法
markdownlint .claude/agents/{agent-name}.md
```
-->
