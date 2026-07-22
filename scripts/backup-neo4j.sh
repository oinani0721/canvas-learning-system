#!/usr/bin/env bash
# Neo4j Community 每日备份 (MEM-FLYWHEEL-2026-07-22 批次0 0-2)
#
# Community 版唯一官方备份姿势: 停库 → neo4j-admin database dump → 启库
# (在线备份是 Enterprise 专属, 见 neo4j.com/docs/operations-manual/backup-restore/offline-backup/)
# 数据是宿主 bind mount (主仓 docker/neo4j/data), dump 经临时容器执行。
# 保留最近 7 份; neo4j + system 两库都备 (官方建议)。
set -euo pipefail

REPO="/Users/Heishing/Desktop/canvas/canvas-learning-system"
DATA_DIR="$REPO/docker/neo4j/data"
BACKUP_DIR="$REPO/backups/neo4j"
CONTAINER="canvas-learning-system-neo4j"
IMAGE="neo4j:5.26-community"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$BACKUP_DIR/backup.log"

mkdir -p "$BACKUP_DIR"

if ! docker info >/dev/null 2>&1; then
    echo "[$(date '+%F %T')] SKIP: docker daemon 不可用" >> "$LOG"
    exit 0
fi

was_running=false
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    was_running=true
    docker stop "$CONTAINER" >/dev/null
fi

restore_container() {
    if [ "$was_running" = true ]; then
        docker start "$CONTAINER" >/dev/null || true
    fi
}
trap restore_container EXIT

for db in neo4j system; do
    docker run --rm \
        -v "$DATA_DIR":/data \
        -v "$BACKUP_DIR":/backups \
        "$IMAGE" \
        neo4j-admin database dump "$db" --to-path=/backups --overwrite-destination=true >/dev/null
    mv "$BACKUP_DIR/${db}.dump" "$BACKUP_DIR/${db}-${STAMP}.dump"
done

# 只保留最近 7 份
for db in neo4j system; do
    ls -t "$BACKUP_DIR"/${db}-*.dump 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
done

size=$(du -h "$BACKUP_DIR/neo4j-${STAMP}.dump" | cut -f1)
echo "[$(date '+%F %T')] OK: neo4j-${STAMP}.dump (${size})" >> "$LOG"
