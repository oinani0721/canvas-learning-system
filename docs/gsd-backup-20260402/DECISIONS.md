# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? | Made By |
|---|------|-------|----------|--------|-----------|------------|---------|
| D001 | M001 | arch | M001 目标平台 | Mac M5 Max + 128GB 为 M001 主要平台，Windows 支持延后到 M002+ | 用户在 Mac M5 Max 上开发和使用，聚焦主要平台避免分散精力。当前 Windows 代码分支保留不删除。 | Yes — M002 时加入 Windows | collaborative |
| D002 | M001/S02 | arch | Graphiti SDK 利用范围 | Graphiti 全量接入：自定义 Entity/Edge Types + search_() 高级搜索 + 社区检测 + 批量摄入 + 时间线检索 + AI 主动识别强制写入 | 当前利用率仅 25%（仅 add_episode + basic search），用户要求全量接入。Context7 文档确认所有 API 可用。 | Yes | collaborative |
| D003 | M002 | arch | 上下文压缩策略 | 后端 3 处暴力截断改用 LLM 语义摘要（参考 Claude Code 泄漏的压缩算法），对话中压缩维持 SDK 原生 | SDK 原生 compaction 已在工作（compact_boundary 事件透传）。后端 learning_context_service/compression.py/question_generator 的暴力截断丢失语义。 | Yes | collaborative |
| D004 | M001/S02 | arch | 蒸馏策略分类 | Edge 对话不蒸馏，产出直接存为结构化 Edge 语义标签。只有节点对话需要蒸馏。蒸馏可选用 Opus 做高质量摘要。 | Edge 产出本身就是结构化的理由记录，无需 LLM 提取。节点对话蒸馏用 Opus 质量最高。 | Yes | collaborative |
| D005 | M001/S03 | arch | 笔记索引范围 | 每个白板绑定独立笔记文件夹路径，RAG 检索以此为搜索范围（从全局改为 per-白板） | 不同白板=不同学科=不同笔记源。全局索引无法隔离学科。用户多次强调。 | Yes | human |
