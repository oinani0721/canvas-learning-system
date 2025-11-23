---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Sub-agent调用协议

**版本**: v1.0
**最后更新**: 2025-01-14

---

## 🎯 核心原则

Claude Code的Sub-agent调用使用**自然语言描述**，而非代码函数调用。

### ❌ 错误示例（不存在的API）
```python
# 这些函数不存在！
Task(subagent_type="basic-decomposition", prompt="...")
call_agent("basic-decomposition", {...})
```

### ✅ 正确示例（自然语言调用）
```
"Use the basic-decomposition subagent to decompose the following material:

Material: [材料内容]
Topic: 逆否命题

Please return JSON format with sub_questions."
```

---

## 📐 调用语法

### 基础语法

```
"Use the {agent-name} subagent to {task description}

Input: {输入数据}

Expected output: {输出格式说明}"
```

**关键要素**:
1. `Use the {agent-name} subagent` - 明确指定Agent名称
2. `to {task description}` - 简短的任务描述
3. 提供清晰的输入数据
4. 说明期望的输出格式

### 示例1：调用basic-decomposition

```
"Use the basic-decomposition subagent to decompose the following difficult material into 3-5 basic guiding questions:

Input:
{
  "material_content": "逆否命题：如果原命题是'若p则q'，则逆否命题是'若非q则非p'。逆否命题与原命题等价。",
  "topic": "逆否命题",
  "user_understanding": null
}

Expected output: JSON format with sub_questions array, each containing text, type, difficulty, and guidance fields."
```

### 示例2：调用scoring-agent

```
"Use the scoring-agent subagent to evaluate the user's understanding:

Input:
{
  "question_text": "什么是逆否命题？",
  "user_understanding": "逆否命题就是把原命题反过来说，而且和原命题意思相同。",
  "reference_material": "逆否命题：如果原命题是'若p则q'，则逆否命题是'若非q则非p'。逆否命题与原命题等价。"
}

Expected output: JSON format with total_score, breakdown, pass, feedback, and color_action fields."
```

---

## 🔄 完整调用流程

### 场景：Canvas-Orchestrator调用Basic-Decomposition

```markdown
# Canvas-Orchestrator的处理逻辑

## Step 1: 准备输入数据
从Canvas文件中提取相关信息：
- 材料节点内容
- 主题
- 用户的现有理解（如果有）

## Step 2: 构造调用语句
"Use the basic-decomposition subagent to decompose the following material:

Material: "逆否命题：如果原命题是'若p则q'，则逆否命题是'若非q则非p'。逆否命题与原命题等价。"
Topic: "逆否命题"
User Understanding: None

Please analyze this material and generate 3-5 basic guiding questions that help the user understand from scratch. Return ONLY JSON format:
{
  \"sub_questions\": [
    {
      \"text\": \"问题文本\",
      \"type\": \"定义型|实例型|对比型|探索型\",
      \"difficulty\": \"基础\",
      \"guidance\": \"💡 提示文字\"
    }
  ]
}"

## Step 3: 接收返回结果
Claude Code会激活basic-decomposition agent，处理后返回JSON：
{
  "sub_questions": [
    {
      "text": "原命题'若p则q'是什么意思？",
      "type": "定义型",
      "difficulty": "基础",
      "guidance": "💡 从日常生活的因果关系想起"
    },
    {
      "text": "'非p'和'非q'分别表示什么？",
      "type": "定义型",
      "difficulty": "基础",
      "guidance": "💡 '非'就是否定的意思"
    },
    {
      "text": "如果原命题是'若下雨则地湿'，逆否命题是什么？",
      "type": "实例型",
      "difficulty": "基础",
      "guidance": "💡 按照'若非q则非p'的格式"
    }
  ]
}

## Step 4: 处理返回结果
解析JSON，使用canvas_utils.py更新Canvas文件：

```python
from canvas_utils import CanvasOrchestrator

orchestrator = CanvasOrchestrator("笔记库/离散数学/离散数学.canvas")

result = orchestrator.handle_basic_decomposition(
    material_node_id="node-abc123",
    sub_questions=response["sub_questions"]
)

print(f"创建了 {len(result['question_ids'])} 个问题节点")
```

## Step 5: 向用户报告
"✅ 拆解完成！
- 生成了3个子问题
- 创建了3个黄色理解节点
- 请在黄色节点中填写你的理解"
```

---

## 📊 Agent调用关系图

```
用户输入
  ↓
canvas-orchestrator（总是第一个被调用）
  ↓
  ├→ basic-decomposition
  │   → 返回JSON → orchestrator处理
  │
  ├→ deep-decomposition
  │   → 返回JSON → orchestrator处理
  │
  ├→ oral-explanation
  │   → 返回Markdown → orchestrator创建笔记文件
  │
  ├→ scoring-agent
  │   → 返回JSON → orchestrator更新节点颜色
  │
  └→ review-verification
      → 返回JSON → orchestrator创建检验白板
```

**调用层级**：
- 用户 → Canvas-Orchestrator（主控）
- Canvas-Orchestrator → 其他12个Sub-agents
- Sub-agents → canvas_utils.py（通过Python代码）
- Sub-agents之间**不直接**相互调用

---

## ⚙️ 调用参数说明

### Agent名称规范

| Agent文件名 | 调用时的名称 | 示例 |
|------------|-------------|------|
| `basic-decomposition.md` | `basic-decomposition` | `"Use the basic-decomposition subagent to..."` |
| `scoring-agent.md` | `scoring-agent` | `"Use the scoring-agent subagent to..."` |
| `canvas-orchestrator.md` | 通常不被其他Agent调用 | N/A |

**规则**：调用名称 = 文件名（去除.md扩展名）

### 输入数据格式

**JSON格式**（推荐）:
```
Input:
{
  "field1": "value1",
  "field2": "value2"
}
```

**文本格式**（简单场景）:
```
Material: "逆否命题定义..."
Topic: "逆否命题"
User Understanding: None
```

### 输出数据格式

**必须明确指定**期望的输出格式：

```
Expected output: JSON format with the following structure:
{
  "field1": "description",
  "field2": ["array", "of", "items"]
}

⚠️ Important: Return ONLY JSON, no additional text or markdown code blocks.
```

---

## 🚨 常见错误和解决方案

### 错误1：Sub-agent返回了Markdown代码块

**问题**:
```markdown
```json
{
  "sub_questions": [...]
}
```
```

**原因**: Agent误以为需要格式化输出

**解决方案**: 在调用时明确强调：
```
"⚠️ IMPORTANT: Return ONLY the raw JSON. Do NOT wrap it in markdown code blocks (```json)."
```

### 错误2：Sub-agent返回了额外的文本

**问题**:
```
好的，我已经分析了材料，生成了以下问题：

{"sub_questions": [...]}

希望这些问题能帮助你理解。
```

**解决方案**: 强调只返回JSON：
```
"Return ONLY JSON, no explanatory text before or after."
```

### 错误3：Agent名称拼写错误

**问题**:
```
"Use the basic_decomposition subagent to..."  # 下划线而非连字符
```

**解决方案**: 使用连字符（kebab-case）：
```
"Use the basic-decomposition subagent to..."
```

### 错误4：JSON格式错误

**问题**: Sub-agent返回的JSON有语法错误（如尾部逗号、单引号等）

**解决方案**: 在Agent的System Prompt中强调：
```markdown
### JSON格式要求
- 使用双引号，不使用单引号
- 不要有尾部逗号
- 确保所有括号配对
- 布尔值用小写：true/false
```

---

## 🔒 调用限制和约束

### 并发限制

| 限制类型 | 值 | 说明 |
|---------|---|------|
| **最大并发Agent数** | 10 | Claude Code同时运行的Sub-agent任务上限 |
| **调用深度** | 2层 | Orchestrator → Sub-agent（不建议Sub-agent再调用其他Agent） |

### 性能考虑

```
单个Agent调用耗时：
- 简单Agent（basic-decomposition）: 5-10秒
- 复杂Agent（oral-explanation）: 15-25秒
- 检验白板生成（review-verification）: 10-20秒

建议：
- 不要在循环中频繁调用Agent
- 批量处理时考虑使用异步调用（如果支持）
```

### 错误重试策略

```python
def call_sub_agent_with_retry(agent_name, input_data, max_retries=2):
    """调用Sub-agent，支持重试"""
    for attempt in range(max_retries):
        try:
            result = call_sub_agent(agent_name, input_data)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"调用失败，重试 {attempt + 1}/{max_retries}")
            time.sleep(2)
```

---

## 📝 最佳实践

### 1. 明确的输入输出契约

```
❌ 不好：
"Use the basic-decomposition subagent to decompose this material."

✅ 好：
"Use the basic-decomposition subagent to decompose the following material:

Input:
{
  "material_content": "...",
  "topic": "...",
  "user_understanding": null
}

Expected output: JSON array of 3-5 questions, each with text, type, difficulty, and guidance fields."
```

### 2. 提供充足的上下文

```
✅ 好：
"Use the basic-decomposition subagent to decompose the following material:

Material: "逆否命题：如果原命题是'若p则q'，则逆否命题是'若非q则非p'。逆否命题与原命题等价。"

Topic: "逆否命题"

Context: This is from a discrete mathematics course. The user is a college freshman with basic logic knowledge but struggles with formal definitions.

User Understanding: None (first exposure to this concept)

Generate 3-5 basic guiding questions..."
```

### 3. 健壮的错误处理

```python
try:
    # 调用Sub-agent
    response = call_sub_agent("basic-decomposition", input_data)

    # 验证返回格式
    if "sub_questions" not in response:
        raise ValueError("返回数据缺少 sub_questions 字段")

    # 验证每个问题的格式
    for q in response["sub_questions"]:
        if "text" not in q or "type" not in q:
            raise ValueError(f"问题格式不正确: {q}")

    # 处理结果
    result = orchestrator.handle_basic_decomposition(...)

except ValueError as e:
    print(f"数据格式错误: {e}")
    # 报告给用户
except Exception as e:
    print(f"调用失败: {e}")
    # 重试或报告错误
```

### 4. 调用日志记录

```python
import logging
from datetime import datetime

def log_agent_call(agent_name, input_data, response, duration):
    """记录Agent调用日志"""
    logging.info(f"""
    Agent Call Log:
    - Time: {datetime.now().isoformat()}
    - Agent: {agent_name}
    - Input size: {len(str(input_data))} chars
    - Output size: {len(str(response))} chars
    - Duration: {duration:.2f}s
    - Success: {response is not None}
    """)
```

---

## ✅ 调用协议检查清单

在实现Agent调用时，确认以下要点：

**调用语句**:
- [ ] 使用 `"Use the {agent-name} subagent to..."`
- [ ] Agent名称与文件名一致（kebab-case）
- [ ] 提供了清晰的输入数据
- [ ] 说明了期望的输出格式
- [ ] 强调了只返回JSON（如果适用）

**错误处理**:
- [ ] 捕获Sub-agent调用失败
- [ ] 验证返回数据格式
- [ ] 有重试机制（至少1次）
- [ ] 向用户报告错误

**性能**:
- [ ] 考虑了调用耗时
- [ ] 避免频繁调用
- [ ] 记录了调用日志

---

## 🔄 示例代码：完整的Agent调用流程

```python
from canvas_utils import CanvasOrchestrator
import json
import logging

class CanvasOrchestatorAgent:
    """Canvas-Orchestrator Agent实现"""

    def __init__(self, canvas_path: str):
        self.orchestrator = CanvasOrchestrator(canvas_path)

    def handle_decomposition_request(self, material_node_id: str):
        """处理用户的拆解请求"""

        # Step 1: 提取材料内容
        material_content = self._get_node_content(material_node_id)

        # Step 2: 构造Sub-agent调用
        call_statement = f"""
        Use the basic-decomposition subagent to decompose the following material:

        Input:
        {{
          "material_content": "{material_content}",
          "topic": "extracted_from_material",
          "user_understanding": null
        }}

        Expected output: JSON format with sub_questions array.
        ⚠️ Return ONLY JSON, no additional text.
        """

        # Step 3: 调用Sub-agent（这里简化为打印，实际由Claude Code处理）
        print(call_statement)

        # Step 4: 接收返回结果（模拟）
        response = {
            "sub_questions": [
                {
                    "text": "什么是...",
                    "type": "定义型",
                    "difficulty": "基础",
                    "guidance": "💡 提示..."
                }
            ]
        }

        # Step 5: 处理结果
        try:
            result = self.orchestrator.handle_basic_decomposition(
                material_node_id=material_node_id,
                sub_questions=response["sub_questions"]
            )

            # Step 6: 向用户报告
            return f"✅ 拆解完成！生成了 {len(result['question_ids'])} 个问题"

        except Exception as e:
            logging.error(f"处理拆解结果失败: {e}")
            return f"❌ 处理失败: {e}"
```

---

**文档版本**: v1.0
**最后更新**: 2025-01-14
**维护者**: Architect Agent

**相关文档**:
- [sub-agent-templates.md](sub-agent-templates.md) - 13个Agent模板
- [canvas-3-layer-architecture.md](canvas-3-layer-architecture.md) - 3层架构
- [tech-stack.md](tech-stack.md) - 技术栈
