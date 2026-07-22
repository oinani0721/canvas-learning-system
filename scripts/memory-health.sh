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

echo "[$(date '+%F %T')] Neo4j:$neo4j 后端:$backend Qwen:$qwen Rerank:$rerank Embed:$ollama | 死信累计:${dead} 待补归档:${queued} | 最新备份:${latest_backup}" >> "$OUT"
