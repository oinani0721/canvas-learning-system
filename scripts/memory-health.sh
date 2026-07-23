#!/usr/bin/env bash
# 记忆系统每日健康摘要 (MEM-FLYWHEEL-2026-07-22 批次0 0-5)
# 一行看清: 各服务活没活 / 死信几条 / 备份新不新。追加写, 不随容器蒸发。
set -uo pipefail

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
WT="$REPO/.claude/worktrees/feature-obsidian-hybrid-dev"
OUT="$REPO/backups/memory-health.log"
mkdir -p "$(dirname "$OUT")"

probe() { curl -s -m 3 "$1" >/dev/null 2>&1 && echo "✅" || echo "❌"; }

neo4j=$(probe "http://localhost:7478")
backend=$(probe "http://localhost:8011/api/v1/health")
qwen=$(probe "http://127.0.0.1:12341/v1/models")
rerank=$(probe "http://127.0.0.1:18012/v1/models")
ollama=$(probe "http://127.0.0.1:11434")

dead=0
for f in "$WT/data/dead_letter_episodes.jsonl" "$WT/backend/data/dead_letter_episodes.jsonl"; do
    [ -f "$f" ] && dead=$((dead + $(wc -l < "$f")))
done

queued=0
qfile="$REPO/canvas-vault/.claude/hooks/pending_archives.jsonl"
[ -f "$qfile" ] && queued=$(wc -l < "$qfile" | tr -d ' ')

latest_backup="无"
lb=$(ls -t "$REPO/backups/neo4j"/neo4j-*.dump 2>/dev/null | head -1)
[ -n "$lb" ] && latest_backup=$(basename "$lb")

# 批次1'⑥ (MEM-FLYWHEEL): 每日污染审计 — 生产 vault__ 组内测试标记计数
# (TestConcept / UAT-2.5 / m3-e2e, 对抗审查 C1 清单)。数据治理三层防线
# 第三层: 写入强校验挡新增, 本审计抓存量与漏网。cypher-shell 经容器执行,
# 凭据取 backend/.env; 任一环节失败记 "审计:跳过" 不炸摘要。
pollution="审计:跳过"
NEO4J_PASSWORD=$(grep -m1 '^NEO4J_PASSWORD=' "$WT/backend/.env" 2>/dev/null | cut -d= -f2-)
if [ -n "${NEO4J_PASSWORD:-}" ]; then
    polluted=$(docker exec canvas-learning-system-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" --format plain \
        "MATCH (n) WHERE n.group_id STARTS WITH 'vault__' AND (
           coalesce(n.name,'') CONTAINS 'TestConcept' OR coalesce(n.content,'') CONTAINS 'TestConcept'
           OR coalesce(n.name,'') CONTAINS 'UAT-2.5' OR coalesce(n.content,'') CONTAINS 'UAT-2.5'
           OR coalesce(n.name,'') CONTAINS 'm3-e2e' OR coalesce(n.content,'') CONTAINS 'm3-e2e')
         RETURN count(n);" 2>/dev/null | tail -1)
    polluted_edges=$(docker exec canvas-learning-system-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" --format plain \
        "MATCH ()-[r]-() WHERE coalesce(r.group_id,'') STARTS WITH 'vault__' AND (
           coalesce(r.fact,'') CONTAINS 'TestConcept' OR coalesce(r.fact,'') CONTAINS 'UAT-2.5'
           OR coalesce(r.fact,'') CONTAINS 'm3-e2e')
         RETURN count(DISTINCT r);" 2>/dev/null | tail -1)
    if [ -n "$polluted" ] && [ -n "$polluted_edges" ]; then
        pollution="污染:节点${polluted}/边${polluted_edges}"
    fi
fi

echo "[$(date '+%F %T')] Neo4j:$neo4j 后端:$backend Qwen:$qwen Rerank:$rerank Embed:$ollama | 死信累计:${dead} 待补归档:${queued} | ${pollution} | 最新备份:${latest_backup}" >> "$OUT"
