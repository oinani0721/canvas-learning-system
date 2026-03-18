<!-- prompts/crag_grading_v1.md -->
<!-- 引用方: src/agentic_rag/agent_graph.py:grade_documents() -->
<!-- 版本: v1 | 创建: 2026-03-18 -->
<!-- 变更时: 1.创建新版本文件 2.更新service引用 3.跑tests/regression/ -->

# CRAG 文档相关性评分 Prompt

你是一个文档相关性评估器。只返回JSON数组。

## 任务

评估检索到的文档是否与用户请求相关，用于 Corrective RAG（CRAG）判定。

### 输入
- **用户意图**: {{user_intent}}
- **用户请求**: {{user_prompt}}
- **文档列表**: {{doc_summaries}}

### 评估标准

对每个文档判断 "relevant" 或 "irrelevant"：

1. **relevant（相关）**: 文档内容直接回答用户问题，或包含回答所需的关键信息
2. **irrelevant（不相关）**: 文档内容与用户问题无关，或仅有表面关键词匹配但实质不相关

### 判定规则

- 部分相关也算 "relevant"（宁可多纳入，不遗漏关键信息）
- 纯粹的术语碰撞（表面关键词相同但语义不同）判为 "irrelevant"
- 同一主题的背景知识也算 "relevant"

### 输出格式

返回 JSON 数组，每个元素对应一个文档的相关性判定：

```json
["relevant", "irrelevant", "relevant", ...]
```

### 规则

1. 只返回 JSON 数组，不要其他文字
2. 数组长度必须等于文档数量
3. 每个元素只能是 "relevant" 或 "irrelevant"
4. 支持中英文混合内容评估
