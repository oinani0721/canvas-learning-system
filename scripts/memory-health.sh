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

# 批次5'⑥ (MEM-FLYWHEEL): 当日学习事件计数 — 批注直连/评分/派生等 8+1 类
# 动作的日活观测 (callout_ingested 为 0 且当天打过批注 = 直连管道断线信号)
events_today="无"
EV="$REPO/canvas-vault/learning_events.jsonl"
if [ -f "$EV" ]; then
    today=$(date '+%F')
    counts=$(grep "\"recorded_at\": \"$today\|\"recorded_at\":\"$today" "$EV" 2>/dev/null \
        | grep -o '"event_type": *"[a-z_]*"' | sed 's/.*"\([a-z_]*\)"$/\1/' | sort | uniq -c \
        | awk '{printf "%s:%s ", $2, $1}')
    [ -n "$counts" ] && events_today="$counts"
fi

# DAILY-REVIEW-PUSH-2026-07-29 死人开关: 解析结构化 state — grep 日志只能
# 证明「跑过」, 证明不了生成/推送成功 (终审 A7 假绿修正)
review_push="无state"
RSTATE="$REPO/backups/daily-review.state.json"
if [ -f "$RSTATE" ]; then
    review_push=$(/usr/bin/python3 - "$RSTATE" <<'PYEOF' 2>/dev/null || echo "state损坏"
import datetime, json, sys
st = json.load(open(sys.argv[1]))
today = datetime.date.today()
# 用昨日界 (Code-Review M1): 本体检 9:00 跑, 推送 9:05 生成 — 用 ==today
# 会天天误报 ❌ 狼来了。>= 昨天 = 管道最近 48h 内活着。
yesterday = (today - datetime.timedelta(days=1)).isoformat()
gen = "✅" if st.get("last_generate_date", "") >= yesterday else "❌"
if st.get("last_push_accepted_date", "") >= yesterday:
    push = "✅"
elif st.get("last_local_notify_date", "") >= yesterday:
    push = "兜底"
else:
    push = "-"
print(f"生成:{gen} 推送:{push}")
PYEOF
)
fi

echo "[$(date '+%F %T')] Neo4j:$neo4j 后端:$backend Qwen:$qwen Rerank:$rerank Embed:$ollama | 死信累计:${dead} 待补归档:${queued} | ${pollution} | 今日事件:${events_today} | 复习推送:${review_push} | 最新备份:${latest_backup}" >> "$OUT"
