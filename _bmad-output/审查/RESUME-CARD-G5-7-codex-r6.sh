#!/bin/zsh
# CARD-G5-7 · 条件 (n) 解除后的一键续跑
# ───────────────────────────────────────────────────────────────────────────
# 前置（只能用户本人做，本脚本不代办凭据操作）:
#     export OPENAI_API_KEY='...'          # 需有 gpt-6-astra 权限
#     printenv OPENAI_API_KEY | codex login --with-api-key
#
# 然后:  zsh _bmad-output/审查/RESUME-CARD-G5-7-codex-r6.sh
#
# 本脚本做三件事:
#   ① 前置自证 —— 不满足就**停下**，不硬跑（避免又拿一份 0 字节存档当结论）
#   ② 跑 Codex round-6（协议 §2 的固定命令；模型/档位不可改）
#   ③ 存档补协议 §2.1 首部（含从 .stderr 逐字抄的会话头自证；.stderr 不入库）
# 跑完由主 session 读存档判 BLOCKER/HIGH；若有代码改动，按卡文「审后改代码必再送一轮」
# 重跑全套裁判（负控八组 + 结构门 + tests/skills + test_g5_6 + tests/unit）。
set -o pipefail
R=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x
PROMPT=$R/_bmad-output/审查/prompts/codex-prompt-CARD-G5-7-r6.md
MD=$R/_bmad-output/审查/codex-review-CARD-G5-7-r6.md
ERR=$R/_bmad-output/审查/codex-review-CARD-G5-7-r6.stderr

print -r -- "═══ ① 前置自证 ═══"
fail=0

ver=$(codex --version 2>&1)
print -r -- "  codex:        $ver"

login=$(codex login status 2>&1 | head -1)
print -r -- "  登录态:       $login"
[[ "$login" == *"api key"* || "$login" == *"API key"* || "$login" == *apikey* ]] \
  || { print -r -- "  ⚠ 不是 API key 登录 —— ChatGPT 账号用不了 gpt-6-astra（§6.8 实测）"; fail=1 }

# ⛔ 必须解析 `models[].slug`，不能在整坨 JSON 文本里 grep ——
#    `gpt-6-astra` 这个名字会出现在别的字段里（availability_nux 等），
#    文本 grep 会给出**假绿**（本脚本第一次干跑就是这么骗过自己的）。
slugs=$(codex debug models 2>/dev/null | python3 -c "
import json,sys
line = sys.stdin.readline()
try:
    print(' '.join(m.get('slug','') for m in json.loads(line).get('models', [])))
except Exception:
    print('')
")
print -r -- "  账号可用模型: ${slugs:-（取不到）}"
if [[ " $slugs " == *" gpt-6-astra "* ]]; then
  print -r -- "  gpt-6-astra:  在清单里 ✅"
else
  print -r -- "  gpt-6-astra:  ⚠ **不在**清单里 —— 这正是 §6.8 那条 400 的根因"
  fail=1
fi

[[ -f $PROMPT ]] || { print -r -- "  ⚠ prompt 缺席: $PROMPT"; fail=1 }

head=$(git -C $R rev-parse HEAD)
dirty=$(git -C $R --no-pager -c core.quotepath=false status --porcelain | grep -v '^??' | wc -l | tr -d ' ')
print -r -- "  HEAD:         $head"
print -r -- "  工作树:       $dirty 条已跟踪改动（须为 0，否则审查绑定说不清）"
[[ $dirty == 0 ]] || fail=1

if [[ $fail != 0 ]]; then
  print -r -- ""
  print -r -- "⛔ 前置不满足，**不跑**。硬跑只会再拿一份 0 字节存档。"
  print -r -- "   解除办法见验收单 §6.8。"
  exit 1
fi

print -r -- ""
print -r -- "═══ ② Codex round-6（绑 $head）═══"
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat $PROMPT)" > $MD 2> $ERR < /dev/null
rc=$?
bytes=$(wc -c < $MD | tr -d ' ')
print -r -- "  codex_rc=$rc · 存档 $bytes 字节"
if [[ $rc != 0 || $bytes == 0 ]]; then
  print -r -- "  ⚠ 失败。stderr 末两行（不入库）:"
  tail -2 $ERR | sed 's/^/     /'
  print -r -- "  按协议 §2.1: 原样重发一次；再 0 字节 → 主 session 人审替代。"
  exit 1
fi

print -r -- ""
print -r -- "═══ ③ 补协议 §2.1 首部 ═══"
python3 - "$MD" "$ERR" "$head" "$ver" <<'PY'
import io, sys
md, err, head, ver = sys.argv[1:5]
body = io.open(md, encoding="utf-8").read()
if body.lstrip().startswith(">"):
    print("  已有首部，跳过"); raise SystemExit(0)
want = ("OpenAI Codex", "model:", "reasoning effort")
proof = []
for i, line in enumerate(io.open(err, encoding="utf-8", errors="replace"), 1):
    t = line.rstrip("\n"); s = t.strip()
    if any((w == "model:" and s.startswith("model:")) or (w != "model:" and w in t) for w in want):
        proof.append(f"(L{i}) {s}")
    if len(proof) == 3:
        break
hdr = [
    "> 批次: BATCH-2026-09-18-第十五批 · 车道 P7-A · 卡 CARD-G5-7 round-6",
    f"> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `{ver}`",
    '> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" '
    '"$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G5-7-r6.md)"`',
    f"> 审查绑定: `{head}`（= 跑这一轮时的 HEAD；工作树已自证干净）",
    "> 会话头自证（抄自同名 `.stderr`，括注实际行号；stderr 本身不入库）:",
    "> " + " / ".join(f"`{p}`" for p in proof) if proof else "> `未自证`",
]
io.open(md, "w", encoding="utf-8", newline="").write("\n".join(hdr) + "\n\n---\n\n" + body)
print(f"  ✓ 首部已补（自证 {len(proof)}/3 行）")
PY

print -r -- ""
print -r -- "═══ 下一步（主 session）═══"
print -r -- "  1. 读 $MD，数 BLOCKER / HIGH"
print -r -- "  2. BLOCKER=0 且 HIGH=0 且绑定仍成立 ⇒ 条件 (n) 达成，卡可判完成"
print -r -- "  3. 有 HIGH ⇒ 整改 → 按卡文「审后改代码必再送一轮」重跑本脚本 + 全套裁判"
print -r -- "  4. 全套裁判 = 负控八组 + F1/地盘/零写者/只读 grep + tests/skills + test_g5_6 + tests/unit"
print -r -- "     （各自的命令与期望值见验收单 §4-A）"
