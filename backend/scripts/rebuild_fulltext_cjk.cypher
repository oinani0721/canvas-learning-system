// 批次4' R4 (MEM-FLYWHEEL-2026-07-22): fulltext 索引重建为 CJK analyzer。
// 背景: 中文 vs 英文检索精度系统性 -26pt (对抗审查), 根因 fulltext 未配
// analyzer (standard 对中文单字切分, BM25 失效)。cjk analyzer 实测可用
// (CALL db.index.fulltext.listAvailableAnalyzers 确认, 2026-07-23)。
// cjk 对拉丁文按空格分词照常, 英文无损。
// 用法: docker exec -i canvas-learning-system-neo4j cypher-shell -u neo4j -p <pw> < 本文件
// 注意: Graphiti 自家索引 (edge_name_and_fact/node_name_and_summary) 用
// IF NOT EXISTS 语义, 重建后不会被 graphiti-core 覆盖回 standard。

DROP INDEX episode_content IF EXISTS;
CREATE FULLTEXT INDEX episode_content FOR (n:EpisodicNode) ON EACH [n.content]
OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}};

DROP INDEX edge_name_and_fact IF EXISTS;
CREATE FULLTEXT INDEX edge_name_and_fact FOR ()-[r:RELATES_TO]-() ON EACH [r.name, r.fact, r.group_id]
OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}};

DROP INDEX node_name_and_summary IF EXISTS;
CREATE FULLTEXT INDEX node_name_and_summary FOR (n:Entity) ON EACH [n.name, n.summary, n.group_id]
OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}};

DROP INDEX node_search_unified IF EXISTS;
CREATE FULLTEXT INDEX node_search_unified FOR (n:Node|EntityNode) ON EACH [n.text, n.name, n.summary, n.concept, n.episode_body]
OPTIONS {indexConfig: {`fulltext.analyzer`: 'cjk'}};
