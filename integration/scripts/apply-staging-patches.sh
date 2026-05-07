#!/usr/bin/env bash
# integration/scripts/apply-staging-patches.sh
# 把 integration/deeptutor-patches/* 应用到 ~/Desktop/canvas/deeptutor-fork/
#
# 用法：
#   ./apply-staging-patches.sh --dry-run   # 预览要 cp 的文件
#   ./apply-staging-patches.sh --force     # 强制（即使 fork 有 dirty 改动）
#   ./apply-staging-patches.sh             # 默认：检查 fork 是否 clean

set -euo pipefail

RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YEL=$'\033[1;33m'; CYA=$'\033[0;36m'; NC=$'\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_SRC="$(cd "${SCRIPT_DIR}/../deeptutor-patches" && pwd)"
FORK_DIR="${DEEPTUTOR_FORK:-${HOME}/Desktop/canvas/deeptutor-fork}"

MODE="${1:-prompt}"
DRY=0; FORCE=0
[[ "${MODE}" == "--dry-run" ]] && DRY=1
[[ "${MODE}" == "--force" ]]   && FORCE=1

[[ -d "${PATCH_SRC}" ]] || { echo "${RED}[FAIL]${NC} patches 不存在: ${PATCH_SRC}"; exit 1; }
[[ -d "${FORK_DIR}/.git" ]] || { echo "${RED}[FAIL]${NC} DeepTutor fork 未 clone: ${FORK_DIR}"; exit 1; }

# patch 映射: <patch内相对路径>:<fork内目标相对路径>
# Verified against DeepTutor v1.3.7 真实结构（2026-05-06 修正 Day 0 假设）:
#   - routers: deeptutor/api/routers/ (18+ 现有 routers 模式)
#   - clients: deeptutor/services/<domain>/client.py (参考 llm/client.py, embedding/client.py)
#   - frontend lib: web/lib/ (扁平，无 src 子目录)
declare -a MAPPINGS=(
  "backend/canvas_client.py:deeptutor/services/canvas/client.py"
  "backend/wikilink_proxy_router.py:deeptutor/api/routers/wikilink_proxy.py"
  "backend/exam_proxy_router.py:deeptutor/api/routers/exam_proxy.py"
  "frontend/wikilink-parser.ts:web/lib/wikilink/parser.ts"
  "frontend/remark-wikilink-plugin.ts:web/lib/wikilink/remark-wikilink-plugin.ts"
  "docker/docker-compose.canvas.yml:docker-compose.canvas.yml"
)

echo "${CYA}===== Apply Staging Patches =====${NC}"
echo "  源:   ${PATCH_SRC}"
echo "  目标: ${FORK_DIR}"
[[ ${DRY} -eq 1 ]] && echo "  ${YEL}模式: DRY-RUN${NC}"

# 检查 fork 是否在干净分支
if [[ ${FORCE} -eq 0 && ${DRY} -eq 0 ]]; then
  if ! ( cd "${FORK_DIR}" && git diff --quiet ); then
    echo "${RED}[STOP]${NC} DeepTutor fork 有未提交变更"
    echo "       cd ${FORK_DIR} && git status"
    echo "       commit/stash 后重跑，或加 --force"
    exit 1
  fi
fi

count=0; skipped=0
echo ""
for entry in "${MAPPINGS[@]}"; do
  src_rel="${entry%%:*}"
  dst_rel="${entry##*:}"
  src="${PATCH_SRC}/${src_rel}"
  dst="${FORK_DIR}/${dst_rel}"

  if [[ ! -f "${src}" ]]; then
    echo "  ${YEL}[skip]${NC} 源文件缺失: ${src_rel}"
    ((skipped++)); continue
  fi

  printf "  %-50s -> %s\n" "${src_rel}" "${dst_rel}"
  if [[ ${DRY} -eq 0 ]]; then
    mkdir -p "$(dirname "${dst}")"
    cp -p "${src}" "${dst}"
  fi
  ((count++))
done

echo ""
echo "${GRN}[done]${NC} ${count} 文件已 patch，${skipped} 跳过"
[[ ${DRY} -eq 1 ]] && echo "${YEL}DRY-RUN 完成，未真正写入。去掉 --dry-run 真正应用。${NC}"

if [[ ${DRY} -eq 0 && ${count} -gt 0 ]]; then
  echo ""
  echo "下一步:"
  echo "  cd ${FORK_DIR}"
  echo "  git status                    # 确认 patch 落点"
  echo "  git diff                      # 审查改动"
  echo "  git add -A && git commit -m 'feat: apply Canvas integration patches'"
  echo "  git tag mvp-day-1-patches"
fi
