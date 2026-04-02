# M001: 

## Vision
让 Canvas Learning System 的核心学习体验链路真正工作——用户能和节点 AI 对话、Agent 能调用后端工具、笔记能被精准检索、学习记忆能被写入和检索、检验白板考察能完整执行。从"代码存在但管道断裂"到"端到端真正跑通"。

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S01 | 代码库清理 + 环境就绪 | low | — | ⬜ | 1730 TS 错误清零，垃圾文件删除，废弃代码清理，npm run tauri dev + docker compose up 一键启动成功，双层 Key 分离配置就绪 |
| S02 | 个人记忆系统全量接入 | high | S01 | ⬜ | Tips/错误/Edge 理由写入 Graphiti（自定义类型）→ search_() 高级搜索返回精准结果 → AI 主动识别错误强制写入 → 社区检测发现知识簇 → LearningMemoryClient JSON 双写消除 → 跨层 relevance 统一排序 + FSRS R 值注入检索 |
| S03 | RAG 检索管道激活 + per-白板索引 + 中文搜索 | high | S01 | ⬜ | 每个白板绑定独立笔记文件夹 → 笔记被正确索引到 LanceDB → RAG 返回该白板对应的精确中文笔记片段 → Reranker 中文适配（Qwen3-Reranker）验证通过 |
| S04 | Sidecar MCP 修复 + 检验白板考察全链路 | high | S02, S03 | ⬜ | 点击节点→Agent 调用 MCP 工具→search_memories 返回记忆→生成检验白板→AI 基于薄弱点出题→AutoSCORE 隐形评分→BKT/FSRS 更新→精通度变化可观察→新节点实时同步回原白板 |
