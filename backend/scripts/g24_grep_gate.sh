#!/usr/bin/env bash
# CARD-G2-4 裁判门 (BATCH-2026-08-29-第七批).
#
# 三条判据 (卡文钉死):
#   G1  "reading legacy"                     0 命中 (B0.7 回退日志文案)
#   G2  在线路径直开裸表 open_table(<裸表名>)  0 命中 (AST 判定, 非字面量匹配)
#   G3  ENABLE_LANCEDB_TIER2_FALLBACK        0 命中 (活代码+活配置, 见 §豁免)
#
# ⛔ 防死门设计 (记忆 reference_gate_design_pitfalls: "把没有发生当验证通过")。
# round-1 审查 (MEDIUM-6) 指出的三条 fail-open 已修:
#   a) 扫描面**先证明存在且可读**, 目录写错/没权限时判红而不是"0 命中通过";
#   b) grep 的 rc 分三档: 0=有命中, 1=无命中, >1=grep 自己出错 → 判红
#      (旧写法把 rc 丢进 /dev/null, grep 报错与"干净"同形);
#   c) G2 改用 Python AST 判 `X.open_table("vault_notes")` 调用 —— 旧的双引号
#      字面量匹配对单引号、换行、变量传参一律漏判;
#   d) G3 的"落在删除锁类里"改成**真正的类区间** (下一个顶层 class 或 EOF),
#      旧写法只比"行号大于类起点", 类之后的任何位置都能冒充;
#   e) mktemp 失败立即退出 (旧写法会退化成往 `/control.txt` 写)。
#
# §豁免 (显式枚举, 不是"我记得没有"):
#   1) _bmad-output/ 与 _archive/ = 历史存档。改写存档 = 篡改证据, 故排除。
#   2) backend/tests/unit/test_supplementary_search_service.py = G3 的**删除锁**
#      测试所在文件。锁"这个 env 开关已经没了"必然要写出它的名字。
#      → 额外收紧: 该文件里的命中必须全部落在删除锁类的**区间内**。
#   3) 本脚本自身 (它也得写出这些模式)。
#
# 用法: bash backend/scripts/g24_grep_gate.sh   (rc=0 全绿 / rc=1 有违规)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

SELF_REL="backend/scripts/g24_grep_gate.sh"
TIER2_TEST_ALLOWLIST="backend/tests/unit/test_supplementary_search_service.py"
LOCK_CLASS="TestTier2BranchRemoved"

# 扫描面 (活代码 + 活配置)。每一项都会被先验证存在且可读。
SCAN_ROOTS=(backend frontend canvas-vault docker config)
ONLINE_ROOTS=(backend/app backend/lib)

EXCLUDES=(
  --exclude-dir=.git
  --exclude-dir=node_modules
  --exclude-dir=.venv
  --exclude-dir=__pycache__
  --exclude-dir=_bmad-output
  --exclude-dir=_bmad-archive
  --exclude-dir=_archive
  --exclude-dir=.pytest_cache
  --exclude-dir=.ruff_cache
)

fail=0
TMPDIR_SELF=""
cleanup() { [[ -n "$TMPDIR_SELF" && -d "$TMPDIR_SELF" ]] && rm -rf "$TMPDIR_SELF"; }
trap cleanup EXIT

# ── 扫描面存在性 (fail-open 的头号来源) ──────────────────────────────────────
verify_roots() {
  local missing=0 r
  for r in "$@"; do
    if [[ ! -e "$r" ]]; then
      echo "  ✗ 扫描面不存在: $r —— '0 命中'在这种情况下毫无意义, 判红"
      missing=1
    elif [[ ! -r "$r" ]]; then
      echo "  ✗ 扫描面不可读: $r"
      missing=1
    fi
  done
  return $missing
}

# scan <pattern> <path...> — stdout=命中行; 返回 0=有命中 1=无命中 2=grep 自身出错
scan() {
  local pattern="$1"; shift
  local out rc
  out="$(grep -rnF "${EXCLUDES[@]}" --binary-files=without-match -- "$pattern" "$@" 2>/dev/null)"
  rc=$?
  printf '%s' "$out"
  return $rc
}

# self_check <pattern> — 正向对照: 种一个含 pattern 的文件, 同法必须抓到。
self_check() {
  local pattern="$1" tmp hits rc
  tmp="$(mktemp -d)" || { echo "  ✗ mktemp 失败 — 无法做正向对照, 判红"; return 1; }
  TMPDIR_SELF="$tmp"
  printf 'planted control line: %s\n' "$pattern" > "$tmp/control.txt" || {
    echo "  ✗ 无法写入对照文件, 判红"; return 1; }
  hits="$(scan "$pattern" "$tmp")"; rc=$?
  rm -rf "$tmp"; TMPDIR_SELF=""
  if [[ $rc -ne 0 || -z "$hits" ]]; then
    echo "  ✗ 自检失败 (rc=$rc): 扫描命令抓不到自己种下的 '$pattern' — 门本身是坏的"
    return 1
  fi
  echo "  · 自检通过 (种下的对照被抓到)"
  return 0
}

report_hits() {
  local out="$1"
  out="$(printf '%s\n' "$out" | grep -v "^${SELF_REL}:" | grep -v '^$')"
  if [[ -n "$out" ]]; then
    echo "  ✗ 违规命中:"
    printf '%s\n' "$out" | sed 's/^/      /'
    return 1
  fi
  echo "  ✓ 0 命中"
  return 0
}

echo "CARD-G2-4 裁判门 @ $REPO_ROOT"
echo

# ── G1: B0.7 回退日志文案 ────────────────────────────────────────────────────
echo "── G1 B0.7 回退日志: 'reading legacy'"
if ! verify_roots "${SCAN_ROOTS[@]}"; then fail=1
elif ! self_check "reading legacy"; then fail=1
else
  out="$(scan "reading legacy" "${SCAN_ROOTS[@]}")"; rc=$?
  if [[ $rc -gt 1 ]]; then
    echo "  ✗ grep 自身出错 (rc=$rc) — 不得当成 0 命中"; fail=1
  else
    report_hits "$out" || fail=1
  fi
fi
echo

# ── G2: 在线路径直开裸表 (AST) ───────────────────────────────────────────────
echo "── G2 在线路径直开裸表: AST 判 X.open_table(<裸表名>)"
if ! verify_roots "${ONLINE_ROOTS[@]}"; then
  fail=1
else
  g2_out="$(python3 - "${ONLINE_ROOTS[@]}" <<'PY'
import ast, pathlib, sys

BARE = {"vault_notes", "canvas_nodes", "multimodal_content",
        "file_fingerprints", "edge_rationales", "canvas_explanations"}
DIRECT_CALLS = {"open_table", "create_table"}
SELF_CONTROL = "__g24_gate_selfcheck__"

# ── 存量基线 (棘轮, 不是豁免) ────────────────────────────────────────────────
#
# 本卡射程 = vault_notes 这条链。AST 扫描顺带照出了**别的表**上同型的存量直开,
# 它们不在本卡的文件面里, 本卡不改 —— 但也绝不静默: 钉成基线, 新增一处就判红。
# 不钉行号 (会漂), 只钉 "文件 → 表名"。
#
# CARD-G2-4 实测 (2026-08-31): backend/app/api/v1/endpoints/edges.py 的写侧
# fallback 分支直接 open_table/create_table 裸 "edge_rationales", 完全绕过
# resolve_table_name —— 与本卡删掉的 B0.7 同型的跨 vault 写混面, 已作为移交项
# 登记在 CARD-G2-4 验收单 §六.5 FU-4。
KNOWN_PREEXISTING = {
    ("backend/app/api/v1/endpoints/edges.py", "edge_rationales"),
}

def scan(path: pathlib.Path):
    hits = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        # 解析不了 ≠ 干净 —— 显式报出来, 让门变红
        return [(path, 0, f"UNPARSEABLE: {type(e).__name__}: {e}")]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name not in DIRECT_CALLS or not node.args:
            continue
        a0 = node.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and a0.value in BARE:
            hits.append((path, node.lineno, name, a0.value))
    return hits

# 正向对照: 先证明扫描器抓得到一个已知的违规形态 (含单引号写法)
import tempfile, os
with tempfile.TemporaryDirectory() as d:
    probe = pathlib.Path(d) / "probe.py"
    probe.write_text("db.open_table('vault_notes')\n", encoding="utf-8")
    if not scan(probe):
        print(f"{SELF_CONTROL}: AST 扫描器抓不到已知违规形态 — 门是坏的")
        sys.exit(3)

roots = [pathlib.Path(r) for r in sys.argv[1:]]
files = [p for r in roots for p in r.rglob("*.py")
         if "__pycache__" not in p.parts and ".venv" not in p.parts]
if not files:
    print(f"{SELF_CONTROL}: 扫描面里一个 .py 都没有 — 路径写错了")
    sys.exit(3)
all_hits = [h for f in files for h in scan(f)]
new_hits, baseline_hits = [], []
for h in all_hits:
    if len(h) == 3:  # UNPARSEABLE 报文
        new_hits.append(h)
        continue
    path, line, call, table = h
    (baseline_hits if (str(path), table) in KNOWN_PREEXISTING else new_hits).append(h)

for h in baseline_hits:
    path, line, call, table = h
    print(f"BASELINE {path}:{line}: {call}(\"{table}\")  [存量, 已登记 FU-4, 本卡不改]")
for h in new_hits:
    if len(h) == 3:
        path, line, what = h
        print(f"NEW {path}:{line}: {what}")
    else:
        path, line, call, table = h
        print(f"NEW {path}:{line}: {call}(\"{table}\")")
sys.exit(1 if new_hits else 0)
PY
)"; g2_rc=$?
  if [[ $g2_rc -eq 3 ]]; then
    echo "  ✗ AST 扫描器自检失败:"; printf '%s\n' "$g2_out" | sed 's/^/      /'; fail=1
  elif [[ $g2_rc -eq 0 ]]; then
    echo "  · 自检通过 (AST 扫描器抓到了种下的单引号违规形态)"
    echo "  ✓ 0 条**新增**裸表直开 (扫描面: ${ONLINE_ROOTS[*]})"
    if [[ -n "$g2_out" ]]; then
      echo "  · 存量基线 (棘轮, 新增即判红; 本卡射程外, 已登记 FU-4):"
      printf '%s\n' "$g2_out" | sed 's/^/      /'
    fi
  else
    echo "  · 自检通过 (AST 扫描器抓到了种下的单引号违规形态)"
    echo "  ✗ 违规命中:"; printf '%s\n' "$g2_out" | sed 's/^/      /'; fail=1
  fi
  echo "  · 扫描面 = ${ONLINE_ROOTS[*]} (在线路径定义); 测试/脚本刻意不在内 —"
  echo "    行为门与归档器必须能直开裸表来构造场景 / 做归档。"
fi
echo

# ── G3: tier-2 env 闸 ────────────────────────────────────────────────────────
echo "── G3 tier-2 env 闸: 'ENABLE_LANCEDB_TIER2_FALLBACK'"
if ! verify_roots "${SCAN_ROOTS[@]}" "$TIER2_TEST_ALLOWLIST"; then
  fail=1
elif ! self_check "ENABLE_LANCEDB_TIER2_FALLBACK"; then
  fail=1
else
  g3_all="$(scan "ENABLE_LANCEDB_TIER2_FALLBACK" "${SCAN_ROOTS[@]}")"; g3_rc=$?
  if [[ $g3_rc -gt 1 ]]; then
    echo "  ✗ grep 自身出错 (rc=$g3_rc) — 不得当成 0 命中"; fail=1
  else
    g3_out="$(printf '%s\n' "$g3_all" \
      | grep -v "^${SELF_REL}:" | grep -v "^${TIER2_TEST_ALLOWLIST}:" | grep -v '^$')"
    if [[ -n "$g3_out" ]]; then
      echo "  ✗ 违规命中 (白名单外):"; printf '%s\n' "$g3_out" | sed 's/^/      /'; fail=1
    else
      echo "  ✓ 白名单外 0 命中"
    fi

    # 白名单内收紧: 命中必须落在删除锁类的**真实区间**内 (下一个顶层 class 或 EOF)
    lock_start="$(grep -nE "^class ${LOCK_CLASS}\b" "$TIER2_TEST_ALLOWLIST" | head -1 | cut -d: -f1)"
    if [[ -z "$lock_start" ]]; then
      echo "  ✗ 白名单文件里找不到顶层删除锁类 ${LOCK_CLASS} — 豁免失去依据"; fail=1
    else
      lock_end="$(awk -v s="$lock_start" 'NR>s && /^class /{print NR-1; exit}' "$TIER2_TEST_ALLOWLIST")"
      [[ -z "$lock_end" ]] && lock_end="$(wc -l < "$TIER2_TEST_ALLOWLIST" | tr -d ' ')"
      stray="$(grep -nF 'ENABLE_LANCEDB_TIER2_FALLBACK' "$TIER2_TEST_ALLOWLIST" \
        | awk -F: -v s="$lock_start" -v e="$lock_end" '$1 < s || $1 > e')"
      # 文件顶部说明行允许存在, 但必须自称"删除"
      stray="$(printf '%s\n' "$stray" | grep -v '删除' | grep -v '^$')"
      if [[ -n "$stray" ]]; then
        echo "  ✗ 白名单文件里出现删除锁类区间 (L${lock_start}-L${lock_end}) 之外的引用:"
        printf '%s\n' "$stray" | sed 's/^/      /'; fail=1
      else
        echo "  ✓ 白名单内引用全部落在 ${LOCK_CLASS} 区间 L${lock_start}-L${lock_end} 或自称删除的说明行"
      fi
    fi
  fi
fi

echo
if [[ "$fail" -eq 0 ]]; then
  echo "全部判据通过 (含三次正向对照自检 + 扫描面存在性校验)"
else
  echo "存在违规 — 见上"
fi
exit "$fail"
