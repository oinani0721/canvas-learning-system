#!/bin/bash
# G5-1 (d) — board-recap 正例路径实跑确认触发 (BATCH-2026-08-27-第四批 / CARD-G5-1)
#
#   B1: /board-recap 特征值与特征向量  — 带板名全链实跑
#       (--dangerously-skip-permissions: 让 skill 跑完 Bash 收集器与 outputs/ 写入的
#        完整路径; 安全兜底 = 前后 manifest + D5 先例已证零写侧, worktree vault 受 git 管)
#   B2: /board-recap                    — 无参路径, 判定 = Skill 触发 + AskUserQuestion 出现
#       (默认权限即可, 选板问题在 headless 无人作答, 触发确认不受影响)
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
VAULT="$REPO/canvas-vault"

vault_manifest() {
  # v3 (Codex 二轮): + .claude/skills 施工面 (N2 曾在此写脚本而 .claude 排除口径漏看)
  #                  + FIFO/socket + symlink 记录目标 (retarget 可见)
  (cd "$VAULT" && {
     find 原白板 节点 检验白板 raw wiki templates outputs .claude/skills -type f 2>/dev/null
     find . -maxdepth 1 -type f \( -name '*.md' -o -name '.canvas-config.yaml' \) | sed 's|^\./||'
   } | sort -u | while IFS= read -r f; do [ -f "$f" ] && shasum -a 256 "$f"; done
   echo "== dirs/links/special =="
   { find 原白板 节点 检验白板 raw wiki templates outputs .claude/skills \( -type d -o -type l -o -type p -o -type s \) 2>/dev/null
     find . -maxdepth 1 \( -type l -o \( -type d ! -name '.*' ! -name '.' \) \) | sed 's|^\./||'
   } | sort -u | while IFS= read -r e; do
       if [ -L "$e" ]; then echo "L $e -> $(readlink "$e")"; elif [ -p "$e" ]; then echo "P $e"; elif [ -S "$e" ]; then echo "S $e"; else echo "D $e"; fi
     done)
}
outputs_listing() { (cd "$VAULT" && find outputs -type f 2>/dev/null | sort); }

run_one() {
  local ID="$1"; shift
  local UTT="$1"; shift
  echo "── [$ID] $UTT ($*)"
  vault_manifest > "$HERE/manifests/$ID-before.txt"
  outputs_listing > "$HERE/manifests/$ID-outputs-before.txt"
  (cd "$VAULT" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
     claude -p "$UTT" --output-format stream-json --verbose "$@" \
     </dev/null > "$HERE/logs/$ID.jsonl" 2>&1) || echo "  ⚠ claude 退出码非 0 (照常判定)"
  vault_manifest > "$HERE/manifests/$ID-after.txt"
  outputs_listing > "$HERE/manifests/$ID-outputs-after.txt"
  diff "$HERE/manifests/$ID-before.txt" "$HERE/manifests/$ID-after.txt" > "$HERE/manifests/$ID-content-diff.txt" || true
  echo "  内容面 diff 行数: $(wc -l < "$HERE/manifests/$ID-content-diff.txt" | tr -d ' ')"
}

mkdir -p "$HERE/logs" "$HERE/manifests"
run_one B1 "/board-recap 特征值与特征向量" --dangerously-skip-permissions --max-turns 40
run_one B2 "/board-recap" --max-turns 8
echo "== 正例运行完毕, 用 judge_headless_logs.py --positive B1 --positive B2 出终判 =="
