#!/usr/bin/env bash
# integration/scripts/start-integration.sh
# 一键启动 Canvas + DeepTutor 双服务（MVP）
#
# 用法：
#   ./start-integration.sh              # 双服务（Canvas + DeepTutor）
#   ./start-integration.sh --canvas-only # 仅 Canvas（DeepTutor fork 还没就绪时）

set -euo pipefail

RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[1;33m'; CYA=$'\033[0;36m'; NC=$'\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEEPTUTOR_FORK="${DEEPTUTOR_FORK:-${HOME}/Desktop/canvas/deeptutor-fork}"

CANVAS_ONLY=0
[[ "${1:-}" == "--canvas-only" ]] && CANVAS_ONLY=1

echo "${CYA}===== Canvas + DeepTutor MVP 集成启动 =====${NC}"
echo "  Canvas worktree: ${WORKTREE_ROOT}"
echo "  DeepTutor fork:  ${DEEPTUTOR_FORK}"
echo ""

# ── Step 1: 启动 Canvas Neo4j + Backend (端口 8011) ─────────────────────────
cd "${WORKTREE_ROOT}"

echo "${YEL}[1/3] 启动 Canvas Neo4j (Bolt :7691, HTTP :7478)...${NC}"
COMPOSE_PROJECT_NAME=canvas-mvp docker compose up -d neo4j

echo "${YEL}     等待 Neo4j healthcheck (最长 70s)...${NC}"
for i in {1..35}; do
  if [[ "$(docker inspect -f '{{.State.Health.Status}}' canvas-learning-system-neo4j 2>/dev/null || echo missing)" == "healthy" ]]; then
    echo "  ${GRN}[OK]${NC}   Neo4j healthy"
    break
  fi
  sleep 2
  [[ $i -eq 35 ]] && { echo "${RED}[FAIL]${NC} Neo4j 启动超时"; exit 1; }
done

echo "${YEL}[2/3] 启动 Canvas backend (端口 8011)...${NC}"
COMPOSE_PROJECT_NAME=canvas-mvp docker compose up -d backend

for i in {1..30}; do
  if curl -fsS http://localhost:8011/api/v1/health >/dev/null 2>&1; then
    echo "  ${GRN}[OK]${NC}   Canvas :8011/api/v1/health"
    break
  fi
  sleep 2
  [[ $i -eq 30 ]] && { echo "${RED}[FAIL]${NC} Canvas backend 启动超时（curl :8011 无响应）"; exit 1; }
done

# ── Step 2: 启动 DeepTutor fork（如果存在 + 不是 --canvas-only）─────────────
if (( CANVAS_ONLY == 1 )); then
  echo "${YEL}[3/3] 跳过 DeepTutor（--canvas-only）${NC}"
else
  if [[ ! -d "${DEEPTUTOR_FORK}/.git" ]]; then
    echo "${YEL}[3/3] DeepTutor fork 未 clone（${DEEPTUTOR_FORK}）${NC}"
    echo "       仅启动 Canvas。Fork 完成后重跑此脚本。"
  else
    echo "${YEL}[3/3] 启动 DeepTutor fork (端口 8001 + 3782)...${NC}"
    cd "${DEEPTUTOR_FORK}"
    docker compose up -d
    sleep 10
    if curl -fsS http://localhost:8001/api/v1/health >/dev/null 2>&1; then
      echo "  ${GRN}[OK]${NC}   DeepTutor :8001/api/v1/health"
    else
      echo "  ${YEL}[WARN]${NC} DeepTutor :8001 无响应（可能仍在启动；运行 ./health-check.sh 复查）"
    fi
  fi
fi

echo ""
echo "${GRN}===== 启动完成 =====${NC}"
echo "  Canvas:    http://localhost:8011/api/v1/health"
echo "  Canvas docs: http://localhost:8011/docs (Swagger)"
echo "  DeepTutor: http://localhost:8001/api/v1/health"
echo "  DeepTutor UI: http://localhost:3782"
echo ""
echo "  健康全检: ${SCRIPT_DIR}/health-check.sh"
