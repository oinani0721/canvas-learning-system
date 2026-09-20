#!/bin/zsh
# CARD-G8-10 r12 → r17 —— UAT 引用产物 ↔ git 树的「名实一致」审计 **v2.6.3**（输出头一律 v2.6.3；
#   历史版本 v2/v2.1/v2.3–v2.6.1 的更迭见 UAT §九.44–.66）
#   v2 与 v1（g810-r11-artifact-audit.zsh）的差异：
#     ①（r11-M1）**去掉前缀白名单**：审计面 = UAT（§九 r8 起）里出现的全部 `*.py|*.txt|*.json|*.zsh|*.md`
#       反引号名（含 `check_g810_refs.py` 这类无前缀名）。
#     ②（r11-M1/M2）判定口径 = 该名字的 **basename 必须在 REF 树内至少存在一处**
#       （`git ls-tree -r --name-only REF` 建集合；不校验路径归属/内容哈希——digest 面由 checker 承担）。
#     ③（r11-M2）**名字面与被审 REF 同绑**：UAT 从 `REF:<UAT 路径>` 读出（不读工作区），并记录 UAT blob sha。
#   v2.3（r13 整改）：
#     ④（r12-M2）§十三 排除名单**强制非死项 + 理由非空**（`excl-dead` / `excl-empty-reason` 红）。
#     ⑤（r12-L1）找不到 §九 `29. **r8 开工自证` 边界标记 ⇒ `marker-missing` 红（fail-closed，不再静默扫全文）。
#     ⑥（r12-L2）临时文件改 `mktemp -d` 私有目录（并发不互相覆盖）。
#     ⑦（r12-L3）名字抽取扩展到含 `/ + ( )` 的引用名（判定用 basename）；**含空白不进面**（声明边界，见 UAT §十.50）。
#     ⑧（r12-L4）输出记录 runner 自身 `sha256`/`blob` 与版本号。
#   v2.6.3（r17 整改）：⑭（r16-L1）`28.` 编号唯一 + 前两项编号 = 27/28（防伪 28 移位）；
#     ⑮（r16-L3）`blob_in_ref` 另验 `git cat-file -t` = blob。
#   v2.6.2（r16 整改）：⑫（r15-L1）名字面起点前移到 **28 项行首**（28/29 之间的正文也进面）；
#     ⑬（r15-L2）`blob_in_ref` 只接受 40-hex，否则单一 `absent`（不再混入 `rev-parse` 的失败回显）。
#   v2.6（r14 整改）：⑨（r14-L1）名字面锚改**结构锚 = §九 章节**（唯一标题；§十三 在其外）；
#     ⑩（r14-M2）§十三 逐行校验格式（不符 ⇒ `excl-malformed` 红）；⑪（r14-L2）记录 runner 的
#     `blob_used`（工作区执行版）与 `blob_in_ref`（被审 REF 内同名 blob，可 absent）。
#   用法: zsh g810-r12-artifact-audit.zsh [REF] [OUTDIR] [UAT_FILE_OVERRIDE]（默认 HEAD / $EV / 无覆盖）
set -u
RUNNER_ABS=${0:A}                       # 先解析为绝对路径（cd 之后 $0 相对路径解析不到）
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w || exit 1
EV=_bmad-output/审查/evidence-g810
UAT_REL=_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md
REF=${1:-HEAD}
OUTDIR=${2:-$EV}            # v2.2：可把运行件写到别处（用于「最终 HEAD 复跑不留工作树残留」）
mkdir -p "$OUTDIR"
TS=$(date +%Y%m%dT%H%M%S)
OUT=$OUTDIR/artifact-audit-r12-$TS-$$.txt      # v2.5 / r13-L2：加 pid 防同秒并发互相覆盖
REFSHA=$(git rev-parse "$REF") || exit 1
UATSHA=$(git rev-parse "$REF:$UAT_REL") || exit 1
TMPD=$(mktemp -d "${TMPDIR:-/tmp}/g810r13.XXXXXX") || exit 1
RUNNER_SHA=$(shasum -a 256 "$RUNNER_ABS" | awk '{print $1}')
RUNNER_BLOB_USED=$(git hash-object "$RUNNER_ABS")
RUNNER_REL=${RUNNER_ABS#*/card-p6-skills-w/}
_rb_ref=$(git rev-parse "$REF:$RUNNER_REL" 2>/dev/null) || _rb_ref=""
_rb_type=$(git cat-file -t "$REF:$RUNNER_REL" 2>/dev/null) || _rb_type=""
if [[ $_rb_ref =~ '^[0-9a-f]{40}$' && $_rb_type == blob ]]; then
  RUNNER_BLOB_REF=$_rb_ref      # v2.6.3 / r16-L3：40-hex **且** cat-file -t == blob，否则单一 absent
else
  RUNNER_BLOB_REF=absent
fi
UAT_OVERRIDE=""
if [[ -n "${3:-}" ]]; then            # 仅负控用：显式 UAT 文本覆盖（模拟「标记缺失 / 名单异常」）
  cat "$3" > "$TMPD/uat.txt" || exit 1
  UAT_OVERRIDE=$3
else
  git show "$REF:$UAT_REL" > "$TMPD/uat.txt" || exit 1
fi
git -c core.quotepath=false ls-tree -r --name-only "$REF" > "$TMPD/tree.txt" || exit 1
[[ -n "$UAT_OVERRIDE" ]] && print -r -- "# uat_override=$UAT_OVERRIDE（仅负控：文本来源 ≠ REF 树内 UAT；uat_blob 仍记 REF 树内 UAT 的值）" >> "$TMPD/override-note.txt"
python3 - "$TMPD" "$REFSHA" "$UATSHA" "$OUT" "$RUNNER_SHA" "$RUNNER_BLOB_USED" "$RUNNER_BLOB_REF" <<'PY'
import os, re, sys, pathlib
tmpd, refsha, uatsha, out, runner_sha, runner_blob_used, runner_blob_ref = sys.argv[1:8]
text = pathlib.Path(os.path.join(tmpd, "uat.txt")).read_text(encoding="utf-8")

def _bail(tag: str, detail: str) -> None:
    pathlib.Path(out).write_text(
        f"# CARD-G8-10 产物审计 v2.6.3（REF={refsha[:8]}；UAT blob={uatsha[:8]}）\n"
        f"{tag}: {detail}\n"
        f"# runner_sha256={runner_sha}\n# runner_blob_used={runner_blob_used}\n# runner_blob_in_ref={runner_blob_ref}\nrc=1\n",
        encoding="utf-8")
    print(tag)
    sys.exit(1)

# ---- 锚：§九 章节（唯一）+ 章内 `29. **r8 开工自证` 标记 + 标记前最近编号项 = 28（v2.6.1 / r14-L1）----
_mh = list(re.finditer(r"^## 九 ", text, re.M))
if len(_mh) != 1:
    _bail("section-anchor", f"`## 九 ` 标题出现 {len(_mh)} 次（要求恰 1 次；fail-closed）")
_i9 = _mh[0].start()
_nx = re.search(r"^## (?!九)", text[_i9 + 1:], re.M)
_i9end = (_i9 + 1 + _nx.start()) if _nx else len(text)
_sec9 = text[_i9:_i9end]
_mm = list(re.finditer(r"^29\. \*\*r8 开工自证", _sec9, re.M))
if len(_mm) != 1:
    _bail("marker-count", f"§九 内 `29. **r8 开工自证` 行出现 {len(_mm)} 次（要求恰 1 次）")
_mstart = _mm[0].start()
_prev_items = list(re.finditer(r"^(\d+)\. ", _sec9[:_mstart], re.M))
_prev_nums = [m.group(1) for m in _prev_items]
if len(_prev_items) < 2 or _prev_nums[-1] != "28" or _prev_nums[-2] != "27" or _prev_nums.count("28") != 1:
    _bail("marker-context",
          f"标记前编号项尾 = {_prev_nums[-2:] if len(_prev_nums) >= 2 else _prev_nums}（要求 …27,28 且 28 唯一：防伪 28 把名字面起点后移）")
seg = _sec9[_prev_items[-1].start():]        # v2.6.2 / r15-L1：名字面从 28 项行首起（28/29 之间正文也进面）

# ---- §十三 审计排除名单（逐行解析；格式不符 = malformed 红）----
excl_marker = "## 十三 审计排除名单"
excluded_entries: list[tuple[str, str]] = []
if excl_marker in text:
    if text.find(excl_marker) < _i9:
        excluded_entries.append(("<§十三 在 §九 之前>", ""))
    etxt = text.split(excl_marker, 1)[1]
    etxt = etxt.split("\n## ", 1)[0]
    for line in etxt.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        m = re.match(r"^- `([^`]+)`\s*—\s*(.*)$", line)
        if m:
            excluded_entries.append((m.group(1), m.group(2).strip()))
        else:
            excluded_entries.append((f"<malformed:{line[:40]}>", ""))

# ---- 名字面（§九 段内；无空白/通配/占位符/绝对/.. 起步）----
NAME_RE = re.compile(r"`([^\s`]+\.(?:txt|json|zsh|py|md))`")
BAD_CHARS = set("*{}<>|$?[]=\\")
names = []
for _t in NAME_RE.findall(seg):
    if any(c in BAD_CHARS for c in _t) or _t.startswith("/") or _t.startswith(".."):
        continue
    names.append(_t)
names = sorted(set(names))
# v2.6.1：`excl-dead` 的判定面 = **整个 §九**（含标记之前的 1–28 项：排除项必须在 §九 里被提到过）
names_body = set()
for _t in NAME_RE.findall(_sec9):
    if any(c in BAD_CHARS for c in _t) or _t.startswith("/") or _t.startswith(".."):
        continue
    names_body.add(_t)

tree = [l for l in pathlib.Path(os.path.join(tmpd, "tree.txt")).read_text(encoding="utf-8").splitlines() if l.strip()]
byname: dict[str, list[str]] = {}
for p in tree:
    byname.setdefault(os.path.basename(p), []).append(p)

lines = [
    f"# CARD-G8-10 r12 产物审计 v2.6.3（REF={refsha[:8]}；UAT blob={uatsha[:8]}，从 REF 树读出；名字面 = §九 内 28 项行首起）",
    f"# runner= g810-r12-artifact-audit.zsh sha256={runner_sha} blob_used={runner_blob_used} blob_in_ref={runner_blob_ref}",
    *([pathlib.Path(os.path.join(tmpd, "override-note.txt")).read_text(encoding="utf-8").strip()]
      if os.path.exists(os.path.join(tmpd, "override-note.txt")) else []),
    f"# 审计面 = §九 章节引用的全部产物名 {len(names)} 条；判定 = basename 在 REF 树内至少一处",
    "# 状态 命中路径 名称",
]
missing = []
name_set = set(names)
excl_problems = []
_seen_excl: dict[str, int] = {}
for k, reason in excluded_entries:
    _seen_excl[k] = _seen_excl.get(k, 0) + 1
    if k.startswith("<malformed:"):
        excl_problems.append(f"excl-malformed: {k}（§十三 行格式须为 `- \\`名\\` — 理由`）")
        continue
    if k not in names_body:
        excl_problems.append(f"excl-dead: {k}（§十三 名单项在整个 §九 内 0 命中）")
    if not reason.strip():
        excl_problems.append(f"excl-empty-reason: {k}（§十三 名单项缺理由）")
for k, cnt in _seen_excl.items():
    if cnt > 1:
        excl_problems.append(f"excl-duplicate: {k} 在 §十三 出现 {cnt} 次（同名逐条并列会掩盖空理由/死项）")
for n in names:
    if n in {k for k, _ in excluded_entries}:
        lines.append(f"SKIP  -  {n}（§十三 理由：{dict(excluded_entries)[n]}）")
        continue
    hits = byname.get(os.path.basename(n), [])
    if not hits:
        missing.append(n)
        lines.append(f"MISS  -  {n}")
    else:
        extra = f"（{len(hits)} 处命中）" if len(hits) > 1 else ""
        lines.append(f"OK    {hits[0]}{extra}  {n}")
lines += [f"# names={len(names)} excluded={len(excluded_entries)} (excluded_unique={len(set(k for k, _ in excluded_entries))}) "
          f"tracked={len(names)-len(missing)-len({k for k, _ in excluded_entries})} missing={len(missing)}",
          f"# ref={refsha}", f"# uat_blob={uatsha}",
          f"# runner_sha256={runner_sha}", f"# runner_blob_used={runner_blob_used}", f"# runner_blob_in_ref={runner_blob_ref}"]
if missing:
    lines.append("# missing_list=" + ",".join(missing))
lines += excl_problems
pathlib.Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[-6:]))
sys.exit(1 if (missing or excl_problems) else 0)
PY
rc=$?
echo "artifact_audit_v2 ref=$REFSHA uat_blob=$UATSHA rc=$rc file=$(basename $OUT)"
exit $rc
