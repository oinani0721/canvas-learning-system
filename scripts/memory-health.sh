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
# 证明「跑过」, 证明不了生成/推送成功 (终审 A7 假绿修正)。
# CARD-C1a: state 已 per-vault 命名空间化 (daily-review.<key>.state.json)。
# Codex-C1a B4: 只枚举已存在文件会对「配置了却从没跑过的库」假绿 — 必须
# 以 .env 期望集合 (DAILY_REVIEW_VAULTS, 缺省 ACTIVE_VAULT) 为基准逐库核对,
# 缺 state 显式报 "无state"; 多余 state 标注已移出配置; 旧全局文件标注待迁移。
REVIEW_ENV="$WT/.env"
EXPECTED=$(grep -E '^DAILY_REVIEW_VAULTS=' "$REVIEW_ENV" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
[ -z "$EXPECTED" ] && EXPECTED=$(grep -E '^ACTIVE_VAULT=' "$REVIEW_ENV" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
[ -z "$EXPECTED" ] && EXPECTED="canvas-vault"
MH_ROOT=$(grep -E '^VAULTS_ROOT=' "$REVIEW_ENV" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
review_push=$(/usr/bin/python3 - "$WT/scripts" "$REPO/backups" "$EXPECTED" "${MH_ROOT:-$REPO}" <<'PYEOF' 2>/dev/null || echo "state损坏"
import datetime, glob, json, os, re, sys
scripts_dir, backups, expected_csv, vaults_root = sys.argv[1:5]
sys.dont_write_bytecode = True
sys.path.insert(0, scripts_dir)
try:
    from send_bark import vault_key as key_of
except Exception:
    def key_of(name):
        return name  # send_bark 不可读兜底: 退回原名 (仍逐库核对)
today = datetime.date.today()
# 用昨日界 (Code-Review M1): 本体检 9:00 跑, 推送 9:05 生成 — 用 ==today
# 会天天误报 ❌ 狼来了。>= 昨天 = 管道最近 48h 内活着。
yesterday = today - datetime.timedelta(days=1)

def _date(v):
    # Codex-C1a F7 (round3 严格版): 词法比较对垃圾值恒 >= — 必须整串严格
    # 解析 ("2026-08-25junk" 截前 10 位会漏过, 整数/非 str 直接拒),
    # 失败按无记录 (❌/-), 不许假绿
    if not isinstance(v, str):
        return None
    try:
        return datetime.date.fromisoformat(v)
    except (ValueError, TypeError):
        return None

def _fresh(v):
    # 健康窗 = [昨天, 明天]: 未来日期 (时钟异常/数据损坏) 同样不算健康,
    # 只留 1 天时区容差 — "9999-12-31" 不得永久假绿
    d = _date(v)
    return d is not None and yesterday <= d <= today + datetime.timedelta(days=1)

def verdict(path):
    try:
        st = json.load(open(path))
        if not isinstance(st, dict):
            raise ValueError
    except Exception:
        return "state损坏"
    gen = "✅" if _fresh(st.get("last_generate_date")) else "❌"
    if _fresh(st.get("last_push_accepted_date")):
        push = "✅"
    elif _fresh(st.get("last_local_notify_date")):
        push = "兜底"
    else:
        push = "-"
    return f"生成:{gen} 推送:{push}"

# 拆分与 wrapper 对齐: 逗号 + ASCII 空白 (\s 会连 NBSP 一起拆, wrapper 不会)
expected = [n for n in re.split(r"[,\t\n\r\f\v ]+", expected_csv) if n]
seen, parts = set(), []
for name in expected:
    # 与 runner 同一条名字规则: 存在的路径先 resolve (symlink 归一),
    # 否则清单里写 alias 名会与 runner 的真名 key 漂移
    p = os.path.join(vaults_root, name)
    real = os.path.basename(os.path.realpath(p)) if os.path.exists(p) else name
    base = f"daily-review.{key_of(real)}.state.json"
    seen.add(base)
    path = os.path.join(backups, base)
    parts.append(f"{name} {verdict(path)}" if os.path.exists(path)
                 else f"{name}=无state")
legacy = os.path.join(backups, "daily-review.state.json")
if os.path.exists(legacy):
    parts.append(f"旧全局(待迁移) {verdict(legacy)}")
for path in sorted(glob.glob(os.path.join(backups, "daily-review.*.state.json"))):
    base = os.path.basename(path)
    if base not in seen:
        m = re.match(r"daily-review\.(.+)\.state\.json$", base)
        parts.append(f"{m.group(1)}(已移出配置) {verdict(path)}")
print(" | ".join(parts) if parts else "无state")
PYEOF
)

echo "[$(date '+%F %T')] Neo4j:$neo4j 后端:$backend Qwen:$qwen Rerank:$rerank Embed:$ollama | 死信累计:${dead} 待补归档:${queued} | ${pollution} | 今日事件:${events_today} | 复习推送:${review_push} | 最新备份:${latest_backup}" >> "$OUT"
