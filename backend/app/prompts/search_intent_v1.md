<!-- prompts/search_intent_v1.md -->
<!-- 引用方: src/agentic_rag/agent_graph.py:analyze_intent() -->
<!-- 版本: v1 | 创建: 2026-03-18 -->
<!-- 变更时: 1.创建新版本文件 2.更新service引用 3.跑tests/regression/ -->

# 搜索意图分析 Prompt

你是一个搜索意图分析器。只返回JSON格式的分析结果。

## 任务

分析用户请求，判断是否需要搜索笔记库获取更多信息。

### 输入
- **用户请求**: {{user_prompt}}
- **已有上下文**: {{pre_context}}

### 分析维度

1. **意图识别**: 用户的核心意图是什么？
2. **具体请求判断**: 用户是否有具体请求（如"列出笔记""举例子""比较 A 和 B"等）？
3. **搜索必要性**: 当前上下文是否足够回答？是否需要搜索笔记库？
4. **搜索查询生成**: 如果需要搜索，生成 1-3 个精准的搜索查询。

### 输出格式

```json
{
  "intent": "用户的核心意图（一句话）",
  "has_specific_request": true/false,
  "needs_search": true/false,
  "search_queries": ["查询1", "查询2"]
}
```

### 规则

1. 只返回 JSON，不要其他文字
2. 如果 `needs_search` 为 false，`search_queries` 返回空数组
3. 搜索查询应精准、简洁，避免过于宽泛
4. 最多生成 3 个搜索查询
5. 支持中英文混合输入
