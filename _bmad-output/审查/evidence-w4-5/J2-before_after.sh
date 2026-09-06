#!/usr/bin/env bash
# J2：六组 before/after —— 证明本卡新增的每条反例「改前不被抓、改后被抓」。
#
# 纪律（卡文 §二.2 / §三）：
#   * 禁 git stash（栈跨 worktree 共享）—— 用 `git show <BASE>:<path>` 取旧版；
#   * EXIT trap **无条件**还原，不写任何条件；
#   * 跑完全文件 sha256 与跑前逐字节相同；
#   * before / after 在**两个独立进程**里跑（避免同进程 import 缓存把两侧读成同源）。
set -u

W=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y8-w4-ast
EV="$W/_bmad-output/审查/evidence-w4-5"
PY="$W/backend/.venv/bin/python"
F="scripts/lifespan_isolation_negative_control.py"
SCRATCH="$(dirname "$0")"
cd "$W/backend" || exit 9

BASE=$(git rev-parse HEAD)
echo "BASE(开工SHA)=$BASE"
SHA0=$(shasum -a 256 "$F" | awk '{print $1}')
echo "SHA0(改后文件)=$SHA0"

# ── 1. 从**改后**文件里 AST 提取全部 case 源码（两侧同源，不各写一份） ──
PYTHONDONTWRITEBYTECODE=1 "$PY" - "$F" "$SCRATCH/cases.json" <<'PYX'
import ast, json, sys
src = open(sys.argv[1], encoding="utf-8").read()
tree = ast.parse(src)
out = {}
for n in ast.walk(tree):
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in ("_AST_MUST_FLAG", "_AST_MUST_PASS"):
        out[n.target.id] = [list(ast.literal_eval(e)) for e in n.value.elts]
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
print(f"提取 must_flag={len(out['_AST_MUST_FLAG'])} must_pass={len(out['_AST_MUST_PASS'])}")
PYX
[ $? -eq 0 ] || { echo "提取失败"; exit 1; }

# ── 2. 备份 + 无条件 EXIT trap ──
BAK=$(mktemp)
cp "$F" "$BAK"
trap 'cp -f "$BAK" "$F"; echo "[trap] 已还原 $F"; shasum -a 256 "$F"' EXIT

# ── 3. 换入开工版本，跑 before ──
git show "${BASE}:backend/${F}" > "$F" || { echo "取旧版失败"; exit 1; }
echo "SHA_BASE(改前文件)=$(shasum -a 256 "$F" | awk '{print $1}')"
PYTHONDONTWRITEBYTECODE=1 "$PY" - "$F" "$SCRATCH/cases.json" "$SCRATCH/before.json" <<'PYX'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("negctl_before", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
sys.modules["negctl_before"] = mod          # dataclass 自省要求先注册（Py3.14）
spec.loader.exec_module(mod)
cases = json.load(open(sys.argv[2], encoding="utf-8"))
res = {}
for tbl, items in cases.items():
    for label, src in items:
        res[f"{tbl}|{label}"] = mod.analyze_source(src, "<before>")
json.dump(res, open(sys.argv[3], "w"), ensure_ascii=False)
print(f"before 跑完 {len(res)} 条（改前版本 _AST_MUST_FLAG={len(mod._AST_MUST_FLAG)} 条）")
PYX
BEFORE_RC=$?

# ── 4. 还原（trap 也会再做一次，无条件） ──
cp -f "$BAK" "$F"
SHA1=$(shasum -a 256 "$F" | awk '{print $1}')
echo "SHA1(还原后)=$SHA1"
if [ "$SHA0" = "$SHA1" ]; then echo "SHA 前后逐字节相同: YES"; else echo "SHA 前后逐字节相同: NO ***"; fi

# ── 5. 新进程跑 after ──
PYTHONDONTWRITEBYTECODE=1 "$PY" - "$F" "$SCRATCH/cases.json" "$SCRATCH/after.json" <<'PYX'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("negctl_after", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
sys.modules["negctl_after"] = mod
spec.loader.exec_module(mod)
cases = json.load(open(sys.argv[2], encoding="utf-8"))
res = {}
for tbl, items in cases.items():
    for label, src in items:
        res[f"{tbl}|{label}"] = mod.analyze_source(src, "<after>")
json.dump(res, open(sys.argv[3], "w"), ensure_ascii=False)
print(f"after 跑完 {len(res)} 条（改后版本 _AST_MUST_FLAG={len(mod._AST_MUST_FLAG)} 条）")
PYX
AFTER_RC=$?

# ── 6. 对照表 ──
PYTHONDONTWRITEBYTECODE=1 "$PY" - "$SCRATCH/before.json" "$SCRATCH/after.json" <<'PYX'
import json, sys
b = json.load(open(sys.argv[1], encoding="utf-8"))
a = json.load(open(sys.argv[2], encoding="utf-8"))
flag = [k for k in a if k.startswith("_AST_MUST_FLAG|")]
pas  = [k for k in a if k.startswith("_AST_MUST_PASS|")]
print("\n=== must-FLAG：改前 → 改后 ===")
newly = []
for k in flag:
    lab = k.split("|", 1)[1]
    bv, av = b.get(k, []), a[k]
    mark = "改前放行→改后抓  ⬅ 本卡新覆盖" if not bv and av else ("both-caught" if bv and av else ("MISSED ***" if not av else "?"))
    if not bv and av:
        newly.append(lab)
    print(f"  before={len(bv):>2} after={len(av):>2}  [{mark}]  {lab}")
print(f"\n「改前放行→改后抓」共 {len(newly)} 条：")
for lab in newly:
    print(f"    - {lab}")
print("\n=== must-PASS：改前 → 改后（改后必须全 0） ===")
for k in pas:
    lab = k.split("|", 1)[1]
    bv, av = b.get(k, []), a[k]
    print(f"  before={len(bv):>2} after={len(av):>2}  {'OK' if not av else 'FALSE POSITIVE ***'}  {lab}")
PYX
echo "before_rc=$BEFORE_RC after_rc=$AFTER_RC"
