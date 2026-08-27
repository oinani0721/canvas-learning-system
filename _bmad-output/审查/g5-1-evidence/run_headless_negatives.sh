#!/bin/bash
# G5-1 (c) — fresh agent headless 负例回归 runner (BATCH-2026-08-27-第四批 / CARD-G5-1)
#
# 对 skill_trigger_matrix.yaml 全部负例, 以本 worktree canvas-vault 为 cwd,
# 每条起一个全新 headless agent (claude -p, 最小上下文), 逐条采集:
#   logs/<ID>.jsonl        — 完整 stream-json 会话流
#   manifests/<ID>-before.txt / <ID>-after.txt — vault 内容面 shasum 清单 (逐条前后)
#   manifests/<ID>-outputs-{before,after}.txt  — outputs/ 文件清单
# 判定由 judge_headless_logs.py 消费 (skill 零调用 + outputs 零新增 + shasum 一致)。
#
# 内容面口径 (D5 先例同口径): 原白板/ 节点/ 检验白板/ raw/ wiki/ templates/ outputs/
# + vault 根 *.md + .canvas-config.yaml。⛔ .claude/ 下的 hook 队列文件
# (pending_archives.jsonl) 属基础设施非板面内容, 不入内容面 — 在 README 如实声明。
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
VAULT="$REPO/canvas-vault"
YAML="$REPO/backend/tests/regression/skill_trigger_matrix.yaml"
PY="$REPO/backend/.venv/bin/python3"

mkdir -p "$HERE/logs" "$HERE/manifests"

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

# 从 YAML 抽负例 (id<TAB>utterance)
"$PY" - "$YAML" <<'PYEOF' > "$HERE/negatives.tsv"
import sys, yaml
data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
for e in data["entries"]:
    if e["polarity"] == "negative" and e.get("headless") is True:
        print(f"{e['id']}\t{e['utterance']}")
PYEOF

echo "== 负例清单 =="; cat "$HERE/negatives.tsv"

while IFS=$'\t' read -r ID UTT; do
  echo "── [$ID] $UTT"
  vault_manifest > "$HERE/manifests/$ID-before.txt"
  outputs_listing > "$HERE/manifests/$ID-outputs-before.txt"
  RC=0
  (cd "$VAULT" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
     claude -p "$UTT" --output-format stream-json --verbose --max-turns 8 \
     </dev/null > "$HERE/logs/$ID.jsonl" 2>&1) || RC=$?
  printf '{"id":"%s","utterance":"%s","exit_code":%d,"ran_at":"%s"}\n' \
    "$ID" "$UTT" "$RC" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$HERE/manifests/$ID-meta.json"
  [ "$RC" -ne 0 ] && echo "  ⚠ claude 退出码 $RC (judge 的 result-success 门会兜底判定)"
  vault_manifest > "$HERE/manifests/$ID-after.txt"
  outputs_listing > "$HERE/manifests/$ID-outputs-after.txt"
  if diff -q "$HERE/manifests/$ID-before.txt" "$HERE/manifests/$ID-after.txt" >/dev/null \
     && diff -q "$HERE/manifests/$ID-outputs-before.txt" "$HERE/manifests/$ID-outputs-after.txt" >/dev/null; then
    echo "  ✓ vault 内容面 + outputs/ 前后一致"
  else
    echo "  ✗ vault 有变化! (详见 manifests/$ID-*)"
  fi
done < "$HERE/negatives.tsv"

echo "== 全部负例运行完毕, 跑 judge_headless_logs.py 出终判 =="
