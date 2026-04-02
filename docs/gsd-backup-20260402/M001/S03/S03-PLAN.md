# S03: RAG 检索管道激活 + per-白板索引 + 中文搜索

**Goal:** 激活 RAG 检索管道数据流，让 Agent 对话时能精准引用用户笔记
**Demo:** After this: 每个白板绑定独立笔记文件夹 → 笔记被正确索引到 LanceDB → RAG 返回该白板对应的精确中文笔记片段 → Reranker 中文适配（Qwen3-Reranker）验证通过

## Tasks
