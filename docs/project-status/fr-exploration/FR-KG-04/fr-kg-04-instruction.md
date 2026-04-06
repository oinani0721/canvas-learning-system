# Deep Research 分析请求

## 项目背景
- 技术栈：Tauri 2 + React + TypeScript + FastAPI + Neo4j + LanceDB + Graphiti
- 架构：前端 (React/Zustand/Dexie) ↔ Tauri IPC ↔ 后端 (FastAPI) ↔ Neo4j + LanceDB + Graphiti
- 关键入口：`backend/app/main.py` (FastAPI), `frontend/src/App.tsx` (React)
- 目录：`frontend/src/` (前端), `backend/app/` (后端), `backend/lib/` (RAG/Memory)

## 分析议题
FR-KG-04：节点/连线自动同步后端 Knowledge Graph

### 已确认的架构问题
1. **三层图互不相通**：同一 Neo4j 中存在三套独立关系类型 (CANVAS_EDGE / CONNECTS_TO / RELATES_TO)，各自有写入方和读取方但互不通信
2. **CONNECTS_TO 是死代码**：CanvasService._sync_edge_to_neo4j() (Story 36.3) 没有调用方，验证服务读 CONNECTS_TO 返回空
3. **RAG 字段名不匹配**：验证服务期望 learning_history/related_concepts/common_mistakes，RAG 返回 reranked_results
4. **内存缓存缺少 group_id 过滤**：memory_service.py:561 的内存查询可能混入其他白板数据
5. **三因子权重无学术支撑**：question_generator.py 的 0.4/0.3/0.3 权重无论文/实验依据，且与设计文档不一致
6. **验证服务出题按文件顺序**：不看 FSRS 状态、不做图谱依赖分析、不做拓扑排序

### 用户决策
- 图片处理改用本地模型（不依赖 Gemini API）
- 跨白板关联应是手动选择（非自动 Jaccard）
- 出题应像 Plan 文件逐步递进（Mastery-Based Progression）
- 考虑用 Graphiti add_triplet() 统一管理两层图

## 打包内容
55 个文件：核心源码 18 + 配置 8 + 数据模型 6 + 测试 8 + 文档 15

## 分析方法
1. 通读 `<directory_structure>` 建立心智模型
2. 从 `sync_service.py` 和 `canvas_service.py` 追踪两条 Neo4j 写入路径
3. 引用 `<file path="...">` + 行号作为证据
4. 验证发现与代码实际行为一致

## 请分析
1. 三层图架构是否应该合并？如何合并？Graphiti add_triplet() 方案是否可行？
2. 6 个已确认问题的修复方案（优先级排序）
3. 验证服务的图谱查询应该如何重构？（用 Graphiti 替代 1-hop CONNECTS_TO）
4. 出题策略如何改为 Mastery-Based Progression？
5. 与社区最佳实践的差距（特别是 BKT+FSRS 组合权重的学术依据）

## 输出格式
| 编号 | 严重度 | 文件:行号 | 问题 | 影响 | 建议 |
