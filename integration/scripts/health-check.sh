#!/usr/bin/env bash
# integration/scripts/health-check.sh
# 双服务健康检查：Canvas + DeepTutor + Neo4j

set -uo pipefail

RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[1;33m'; NC=$'\033[0m'

CANVAS_URL="${CANVAS_URL:-http://localhost:8011/api/v1/health}"
DEEPTUTOR_URL="${DEEPTUTOR_URL:-http://localhost:8001/api/v1/health}"
NEO4J_URL="${NEO4J_URL:-http://localhost:7478}"

probe() {
  local name="$1" url="$2" expected="${3:-200}"
  local code body
  code=$(curl -s -o /tmp/.health-body -w "%{http_code}" --max-time 5 "${url}" 2>/dev/null || echo "000")
  body=$(head -c 200 /tmp/.health-body 2>/dev/null || echo "")
  if [[ "${code}" == "${expected}" ]]; then
    printf "  ${GRN}[OK]${NC}    %-12s %s  (HTTP %s)\n" "${name}" "${url}" "${code}"
    [[ -n "${body}" ]] && printf "          body: %s\n" "$(echo "${body}" | tr -d '\n' | head -c 80)"
    return 0
  else
    printf "  ${RED}[FAIL]${NC}  %-12s %s  (HTTP %s)\n" "${name}" "${url}" "${code}"
    [[ -n "${body}" ]] && printf "          body: %s\n" "${body}"
    return 1
  fi
}

echo "${YEL}===== Canvas-DeepTutor 集成健康检查 =====${NC}"
fail=0
probe "Canvas"    "${CANVAS_URL}"    200 || ((fail++))
probe "DeepTutor" "${DEEPTUTOR_URL}" 200 || ((fail++))
probe "Neo4j"     "${NEO4J_URL}"     200 || ((fail++))

echo ""
echo "${YEL}Docker 容器状态:${NC}"
docker ps --filter "name=canvas-mvp" --filter "name=deeptutor" --format "  {{.Names}}\t{{.Status}}" 2>/dev/null \
  | sed 's/^/  /' \
  | head -10

# CORS 验证（如果 Canvas + DeepTutor 都在）
if (( fail == 0 )); then
  echo ""
  echo "${YEL}CORS preflight (DeepTutor frontend → Canvas backend):${NC}"
  cors=$(curl -s -I -H "Origin: http://localhost:3782" "${CANVAS_URL}" 2>/dev/null | grep -i "access-control-allow-origin" | head -1)
  if [[ -n "${cors}" ]]; then
    printf "  ${GRN}[OK]${NC}    %s\n" "${cors}"
  else
    printf "  ${YEL}[WARN]${NC}  CORS header 未返回（Canvas backend 可能未读 .env CORS_ORIGINS）\n"
  fi
fi

rm -f /tmp/.health-body

echo ""
if (( fail == 0 )); then
  echo "${GRN}===== 全部通过 =====${NC}"
  exit 0
else
  echo "${RED}===== ${fail} 个服务异常 =====${NC}"
  echo "排查："
  echo "  docker logs canvas-mvp-backend-1 --tail 50"
  echo "  docker logs canvas-mvp-neo4j-1 --tail 50"
  echo "  cd ~/Desktop/canvas/deeptutor-fork && docker compose logs --tail 50"
  exit 1
fi
