#!/usr/bin/env python3
"""CARD-G1-3 [BATCH-2026-09-18-第十五批] — capability-ledger.md 承重门 L0–L15。

⛔ 本文件**不在代码树**（住 `_bmad-output/审查/evidence-g13/`），故不触发 lefthook
`python-lint` / `python-typecheck`，也不把零代码卡变成多轮卡。纯 stdlib，
**不连任何库**（无 7691 / 7692 / 8011 / LanceDB / 网络）；只读文件系统与 `git`。

判据（DD-03：真核，不接受"链接格式合法"替代存在性）:
  L0  表头逐字等于 EXPECTED_HEADERS（列序即契约；表头一变，下面所有按列名取值的判据
      就在讲另一件事——所以它先跑，不过则整体 FAIL 并停）
  L1  表行数 >= MIN_ROWS(15)
  L2  `E 级` 逐字 ∈ E0..E5
  L3  每个 E3+ 行的 `证据` 必含一个**存在**的
      docs/release-evidence/<rc>/journeys/J<nn>/manifest.json，且该 json
      provenance.mode == "live" 且 candidate.dirty is False（计划书 §12.5 / R-EVD S13/S17）
  L4  `入口` 与 `证据` 两列中：含 "/" 的路径 token 必须 os.path.exists(repo/…)；
      8 位十六进制 token 必须 `git cat-file -t` == commit；
      `merged-squash/…` token 必须在 `git tag -l` 内
  L5  `已知限制与失败行为` 非空且 ∉ {无, —, -, N/A, 없음}
  L6  `入口` 非空
  L7  `id` 唯一
  L8  `状态` ∈ {current, implemented-unverified}
  L9  `核验 SHA` == 8 位十六进制、`git cat-file -t` == commit，**且是 `--trunk` 的祖先**
      （核验 SHA 由台账自填，L11/L12 又都以它为基准；不锚到外部引用的话，整条链
      可以自洽地全部落在一个未合入的分支上 —— Codex r2 HIGH-2）
  L10 `uat` 匹配 ^no$ 或 ^yes\\(<路径>.md\\)$ 且括号内路径存在
  L11 `证据` 列里的每个 8 位 SHA 必须是本行 `核验 SHA` 的**祖先**（git merge-base --is-ancestor），
      且每行至少有 1 个这样的 SHA —— 防「拿未合入主干的 commit 当已合能力的证据」。
      ⚠️ `merged-squash/*` tag **不受本条约束**：squash 合并在主干产出新 SHA，原分支不进主干历史，
      所以该类 tag 恒非主干祖先——这是工作流常态而非缺陷（本卡实测 21 个 tag 全部如此）。
      判「是否合入」要看主干上有无该卡的 squash commit，不能用 tag 的祖先关系推断。
  L12 `证据` 里的每个 8 位 SHA 必须**真改动过本行入口列里的文件**（git show --name-only 取交集）。
      祖先关系只说明这个 commit 在主干上，任何主干 commit 都能过 L11，不说明它和这条能力有关。
      已知边界：顺带碰过该文件的 commit（整仓格式化、别卡的 squash）仍能过——见 l12-known-weakness-probe。
  L13 与能力表**同列数**的表格行不得出现在能力表之外。没有这条，把能力行挪进文件后面的
      第二张表就等于让它们完全不受检查（解析器只读第一张表）—— Codex r2 HIGH-1 的负控输入
      正是这样拿到 rows=15、L3 空转、整体 PASS 的。判据用**列数**不用 id 前缀：前缀是内容
      约定，换个前缀就绕开了；列数是表结构本身。

⚠️ 防假绿：每条判据打印它**实际检查了多少个对象**（rows= / checked=）。
   「零失败」与「零检查」在 PASS 字样上不可区分——所以计数必须入账，
   复核时先看计数再看 PASS。L3 在本版是 0 行空转，显式打印 (0 rows) 而非静默 PASS。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

MIN_ROWS = 15
E_LEVELS = ("E0", "E1", "E2", "E3", "E4", "E5")
E3_PLUS = ("E3", "E4", "E5")
STATUSES = ("current", "implemented-unverified")
EMPTY_MARKS = {"", "无", "—", "-", "–", "N/A", "n/a", "待补", "TBD"}

# 固定表列（顺序即契约；表头不符即 FAIL，防"改了列序而判据还按旧索引取值"）
EXPECTED_HEADERS = [
    "id", "能力", "维度", "入口", "E 级", "状态", "uat",
    "证据", "已知限制与失败行为", "来源卡", "核验 SHA",
]

_SHA8 = re.compile(r"^[0-9a-f]{8}$")
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_BACKTICK = re.compile(r"`([^`]+)`")
# （原 _JOURNEY_MANIFEST 整串正则已停用：见 find_manifest_refs 的说明）
_UAT_YES = re.compile(r"^yes\((.+\.md)\)$")
# token 分隔：空白 + 中英标点 + <br>；⇩ 是"降级触发面"在入口单元格内的分隔符
_SPLIT = re.compile(r"(?:<br\s*/?>)|[\s,，、；;·⇩]+")
# ⚠️ 剥词表**不含** `_` 与 `~`：它们是合法文件名字符，剥掉会把 `_bmad-output/…`
# 变成 `bmad-output/…` 而判「不存在」——本卡首跑实测到的假阳性。markdown 的
# `_强调_` 在本表内不使用，故不需要为它付这个代价。
_STRIP_CHARS = "`（）()[]【】「」《》“”\"'。，,、；;：:!！?？* "


class Git:
    """git 查询的薄封装 + 记忆化。fail-closed：任何异常都判为"不成立"。"""

    def __init__(self, repo: str) -> None:
        self.repo = repo
        self._obj_cache: dict[str, str] = {}
        self._tags: set[str] | None = None
        self._anc_cache: dict[str, bool] = {}
        self._files_cache: dict[str, set[str]] = {}

    def object_type(self, rev: str) -> str:
        if rev not in self._obj_cache:
            try:
                out = subprocess.run(
                    ["git", "cat-file", "-t", rev],
                    cwd=self.repo, capture_output=True, text=True, timeout=30,
                )
                self._obj_cache[rev] = out.stdout.strip() if out.returncode == 0 else ""
            except Exception:
                self._obj_cache[rev] = ""
        return self._obj_cache[rev]

    def is_ancestor(self, rev: str, of: str) -> bool:
        key = f"{rev}..{of}"
        if key not in self._anc_cache:
            try:
                out = subprocess.run(
                    ["git", "merge-base", "--is-ancestor", rev, of],
                    cwd=self.repo, capture_output=True, text=True, timeout=30,
                )
                self._anc_cache[key] = out.returncode == 0
            except Exception:
                self._anc_cache[key] = False
        return self._anc_cache[key]

    def files_touched(self, rev: str) -> set[str]:
        if rev not in self._files_cache:
            try:
                out = subprocess.run(
                    ["git", "show", "--name-only", "--format=", "-m", "--first-parent", rev],
                    cwd=self.repo, capture_output=True, text=True, timeout=60,
                )
                self._files_cache[rev] = (
                    {l.strip() for l in out.stdout.splitlines() if l.strip()}
                    if out.returncode == 0 else set()
                )
            except Exception:
                self._files_cache[rev] = set()
        return self._files_cache[rev]

    def rev_parse(self, ref: str) -> str:
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
                cwd=self.repo, capture_output=True, text=True, timeout=30,
            )
            return out.stdout.strip() if out.returncode == 0 else ""
        except Exception:
            return ""

    def tags(self) -> set[str]:
        if self._tags is None:
            try:
                out = subprocess.run(
                    ["git", "tag", "-l"],
                    cwd=self.repo, capture_output=True, text=True, timeout=30,
                )
                self._tags = set(out.stdout.split()) if out.returncode == 0 else set()
            except Exception:
                self._tags = set()
        return self._tags


def parse_table(text: str) -> tuple[list[str], list[list[str]], list[int], list[int]]:
    """取文件中**第一张**以 EXPECTED_HEADERS[0] 开头的表；
    返回 (表头, 数据行, 数据行号, 表块全部行号)。表块行号供 L13 排除能力表自身。"""
    headers: list[str] = []
    rows: list[list[str]] = []
    linenos: list[int] = []
    block: list[int] = []      # 能力表块的全部行号（表头/分隔/数据），供 L13 排除自身
    in_table = False
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = _cells(line)   # 与 scan_tables 同一口径：转义竖线不是分隔符
        if not in_table:
            if cells and cells[0] == EXPECTED_HEADERS[0]:
                headers = cells
                in_table = True
                block.append(i)
            continue
        block.append(i)
        if all(set(c) <= set("-: ") for c in cells if c):  # 分隔行
            continue
        rows.append(cells)
        linenos.append(i)
    return headers, rows, linenos, block


_HTML_TABLE = re.compile(r"<\s*(table|tr|td|th)\b", re.IGNORECASE)
_INLINE_CODE = re.compile(r"`+[^`]*`+")
_FENCE = re.compile(r"^(`{3,}|~{3,})")
_DECLARED_ROWS = re.compile(r"\*\*本版条目数\*\*\s*[:：]\s*(\d+)(?![\d.])")
_ESC_PIPE = "\x00ESCPIPE\x00"
#: 台账允许存在的表格「列数 → 张数」。多一张、少一张、列数不对，都算结构被改动。
EXPECTED_TABLES = {2: 1, 11: 1}


def _cells(line: str) -> list[str]:
    r"""按 markdown 表格行取单元格。外侧竖线可有可无；`\|` 是单元格内的字面竖线，不是分隔符。"""
    t = line.strip().replace("\\|", _ESC_PIPE)
    return [c.strip().replace(_ESC_PIPE, "\\|") for c in t.strip("|").split("|")]


def _is_sep(line: str) -> bool:
    """分隔行：必须**含竖线**。

    只看「由 - : 空格组成」会把 Setext 标题下划线（`-------------`）也算成分隔行，
    于是它上面那行普通文字被当成表头 —— Codex r4 MEDIUM-2 的假红之一。
    """
    t = line.strip()
    if "|" not in t:
        return False
    t = t.strip("|")
    return bool(t) and set(t) <= set("-: |") and "-" in t


def declared_rows(text: str) -> tuple[int | None, str]:
    """取台账自述的条目数。

    ⚠️ 只在**代码块之外**找，且要求全文**恰好一处**：
    r5 的负控在文首放一个 fenced 代码块写「本版条目数: 15」，就抢占了正文里的真声明
    （取第一次命中），于是把六行挪成列表后反而整体 PASS。正则也补了数字右边界，
    否则 `21.5` 会被读成 21。
    """
    hits: list[int] = []
    fence: str | None = None
    for raw in text.splitlines():
        t = raw.strip()
        m = _FENCE.match(t)
        if m:
            tok = m.group(1)
            if fence is None:
                fence = tok
            elif tok[0] == fence[0] and len(tok) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        for mm in _DECLARED_ROWS.finditer(raw):
            hits.append(int(mm.group(1)))
    if not hits:
        return None, "台账未声明「本版条目数」（代码块内的声明不算）"
    if len(hits) > 1:
        return None, f"「本版条目数」在代码块外出现 {len(hits)} 处：{hits} —— 必须恰好一处"
    return hits[0], ""


def scan_tables(text: str) -> tuple[list[tuple[int, int, str, list[int]]], list[int]]:
    """扫全文的 markdown 表格块，跳过 fenced 代码块。

    返回 ([(表头行号, 列数, 首格文本, 数据行号列表)], HTML 表格标签所在行号)。

    ⚠️ 这个函数是 L13/L14 的眼睛，`parse_table` 是判据的眼睛。两双眼睛看同一份文件，
    **口径差就是缝**：r4 的负控只删掉六行最前面的一个竖线，`parse_table` 就停在第 15 行，
    而这里一路扫到底、仍判「结构符合契约」，于是六个 E5 完全不受检查。
    所以 L14 强制两者对同一张能力表看到的数据行号集合逐一相等——这是自洽断言，
    不是又一条识别规则；再多的写法也绕不过「两双眼睛必须看到同一批行」。
    """
    lines = text.splitlines()
    tables: list[tuple[int, int, str, list[int]]] = []
    html: list[int] = []
    fence: str | None = None      # 记录围栏字符与长度：四个反引号不该被三个反引号闭合
    i = 0
    while i < len(lines):
        raw = lines[i]
        t = raw.strip()
        m = _FENCE.match(t)
        if m:
            tok = m.group(1)
            if fence is None:
                fence = tok
                i += 1
                continue
            if tok[0] == fence[0] and len(tok) >= len(fence):
                fence = None
                i += 1
                continue
        if fence is not None:
            i += 1
            continue
        # 行内代码里的 `<table>` 是在讲它，不是在用它
        if _HTML_TABLE.search(_INLINE_CODE.sub(" ", raw)):
            html.append(i + 1)
        if "|" in t and i + 1 < len(lines) and _is_sep(lines[i + 1]) and not _is_sep(t):
            head = _cells(t)
            data: list[int] = []
            j = i + 2
            while j < len(lines):
                nxt = lines[j].strip()
                if _FENCE.match(nxt) or "|" not in nxt:
                    break
                if not _is_sep(nxt):
                    data.append(j + 1)
                j += 1
            tables.append((i + 1, len(head), head[0][:40] if head else "", data))
            # ⚠️ 表体行也要查 HTML 标签：整段跳过会让「塞进单元格里的 <table>」漏检
            for k2 in range(i + 1, j):
                if _HTML_TABLE.search(_INLINE_CODE.sub(" ", lines[k2])):
                    html.append(k2 + 1)
            i = j
            continue
        i += 1
    return tables, html


def classify_tokens(cell: str) -> tuple[list[str], list[str], list[str]]:
    """把单元格切成 (路径 token, 8位SHA token, merged-squash tag token)。

    提取顺序：markdown 链接目标 → 反引号内容 → 裸文本切词。三路并集后去重，
    宁可多核不可漏核（漏核 = 假绿）。
    """
    candidates: list[str] = []
    candidates += _MD_LINK.findall(cell)
    candidates += _BACKTICK.findall(cell)
    stripped = _BACKTICK.sub(" ", _MD_LINK.sub(" ", cell))
    candidates += [t for t in _SPLIT.split(stripped) if t]

    paths: list[str] = []
    shas: list[str] = []
    tags: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        for tok in _SPLIT.split(raw):
            tok = tok.strip(_STRIP_CHARS)
            if not tok or tok in seen:
                continue
            seen.add(tok)
            if tok.startswith(("http://", "https://")):
                continue
            if tok.startswith("merged-squash/"):
                tags.append(tok)
            elif _SHA8.match(tok):
                shas.append(tok)
            elif "/" in tok:
                paths.append(tok)
    return paths, shas, tags


def find_manifest_refs(cell_text: str, repo_root: str) -> list[str]:
    """从单元格里找出所有 release-evidence 下的 manifest 引用。

    ⚠️ 不用「docs/release-evidence/<rc>/journeys/J<nn>/manifest.json」这样的整串正则：
    `…/journeys/./J08/…`、`…/Journeys/J08/…`、`…/journeys/j08/…` 都是真实可打开的
    写法，却全部不匹配该正则 —— 于是同一行里混一份写法不常规的 reconstructed
    manifest，就能整个逃过 L3 的全称检查（Codex r2 MEDIUM-6）。
    这里改为按 token 筛：归一化后落在 docs/release-evidence/ 下、以 manifest.json
    结尾的都算，路径中段怎么写都拦得住。
    """
    paths, _, _ = classify_tokens(cell_text)
    out: list[str] = []
    for tok in paths:
        raw = norm_path(tok)
        # 绝对路径、`../<树名>/docs/…` 这类写法都真实可打开，却不以 docs/ 开头
        # （Codex r3 MEDIUM-3）。所以先落到真实文件系统上再相对化回 repo。
        cand = raw if os.path.isabs(raw) else os.path.join(repo_root, raw)
        try:
            rel = os.path.relpath(os.path.realpath(cand), os.path.realpath(repo_root))
        except Exception:
            rel = os.path.normpath(raw)
        low = rel.replace(os.sep, "/").lower()
        if low.startswith("docs/release-evidence/") and low.endswith("/manifest.json"):
            out.append(rel)
    return out


def norm_path(tok: str) -> str:
    """剥 :行号 / #锚 尾巴；保留 CJK 与空格以外的一切。"""
    tok = tok.split("#", 1)[0]
    tok = re.sub(r":\d+(?:-\d+)?$", "", tok)
    return tok.rstrip("/")


def main() -> int:
    ap = argparse.ArgumentParser(description="capability-ledger.md 承重门 L0–L15")
    ap.add_argument("--repo", required=True, help="仓库/worktree 根（git 与路径解析基准）")
    ap.add_argument("--ledger", required=True, help="ledger 路径（相对 --repo 或绝对）")
    ap.add_argument(
        "--trunk", default="HEAD",
        help="主干引用（默认 HEAD）。每行的『核验 SHA』必须是它的祖先——"
             "核验 SHA 是台账自填的，不锚到外部引用的话，整条 L9→L11→L12 链可以"
             "自洽地全部落在一个未合入的分支上（Codex r2 HIGH-2）。",
    )
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    ledger = args.ledger if os.path.isabs(args.ledger) else os.path.join(repo, args.ledger)
    if not os.path.exists(ledger):
        print(f"L0 FAIL - ledger 不存在: {ledger}")
        print("rows=0")
        print("LINT: FAIL")
        return 1

    git = Git(repo)
    trunk_sha = git.rev_parse(args.trunk)
    if not trunk_sha:
        print(f"L0 FAIL - --trunk {args.trunk!r} 解析不到 commit")
        print("rows=0")
        print("LINT: FAIL")
        return 1
    print(f"# trunk: {args.trunk} = {trunk_sha}")
    with open(ledger, encoding="utf-8") as fh:
        text = fh.read()
    headers, rows, linenos, block = parse_table(text)

    fails: list[str] = []

    def emit(rule: str, ok: bool, rid: str, why: str) -> None:
        print(f"{rule} {'PASS' if ok else 'FAIL'} {rid} {why}")
        if not ok:
            fails.append(f"{rule}/{rid}")

    if headers != EXPECTED_HEADERS:
        emit("L0", False, "-", f"表头不符契约: {headers!r} != {EXPECTED_HEADERS!r}")
        print(f"rows={len(rows)}")
        print("LINT: FAIL")
        return 1
    emit("L0", True, "-", f"表头符合契约（{len(headers)} 列）")

    col = {h: i for i, h in enumerate(headers)}

    def cell(row: list[str], name: str) -> str:
        i = col[name]
        return row[i].strip() if i < len(row) else ""

    # ── L1 行数 ────────────────────────────────────────────────────────────
    emit("L1", len(rows) >= MIN_ROWS, "-", f"表行数 {len(rows)} （下限 {MIN_ROWS}）")

    # ── L7 id 唯一 ─────────────────────────────────────────────────────────
    ids = [cell(r, "id") for r in rows]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    emit("L7", not dup, "-", f"id 唯一性：{len(ids)} 个 id，重复 {dup or '无'}")

    # ── 逐行 L2 / L5 / L6 / L8 / L9 / L10 ──────────────────────────────────
    for row, ln in zip(rows, linenos):
        rid = cell(row, "id") or f"<行{ln}>"
        lvl = cell(row, "E 级")
        emit("L2", lvl in E_LEVELS, rid, f"E 级={lvl!r}（须 ∈ {E_LEVELS}）")

        lim = cell(row, "已知限制与失败行为")
        emit("L5", lim not in EMPTY_MARKS, rid,
             f"限制列 {'非空' if lim not in EMPTY_MARKS else '为空/占位'}（{len(lim)} 字符）")

        ent = cell(row, "入口")
        emit("L6", ent not in EMPTY_MARKS, rid, f"入口列 {len(ent)} 字符")

        st = cell(row, "状态")
        emit("L8", st in STATUSES, rid, f"状态={st!r}（须 ∈ {STATUSES}）")

        sha = cell(row, "核验 SHA").strip(_STRIP_CHARS)
        is_commit = bool(_SHA8.match(sha)) and git.object_type(sha) == "commit"
        # ⚠️ 只核「它是个 commit」不够：核验 SHA 由台账自己填，
        # 后面的 L11/L12 又都以它为基准 —— 整条链可以自洽地落在一个未合入的分支上。
        # 所以这里把它锚到**外部传入**的主干引用上。
        on_trunk = is_commit and git.is_ancestor(sha, trunk_sha)
        emit("L9", is_commit and on_trunk, rid,
             f"核验 SHA={sha!r} → 对象类型={git.object_type(sha)!r}; "
             f"是 --trunk({args.trunk}={trunk_sha[:8]}) 的祖先={on_trunk}")

        uat = cell(row, "uat")
        if uat == "no":
            emit("L10", True, rid, "uat=no")
        else:
            m = _UAT_YES.match(uat)
            if not m:
                emit("L10", False, rid, f"uat={uat!r} 不匹配 ^no$ 或 ^yes\\(<…>.md\\)$")
            else:
                p = norm_path(m.group(1).strip(_STRIP_CHARS))
                ex = os.path.exists(os.path.join(repo, p))
                emit("L10", ex, rid, f"uat=yes({p}) → exists={ex}")

    # ── L3 E3+ 必指 live manifest ──────────────────────────────────────────
    e3_rows = [(r, ln) for r, ln in zip(rows, linenos) if cell(r, "E 级") in E3_PLUS]
    if not e3_rows:
        emit("L3", True, "-", f"(0 rows) 本版无 E3+ 行 —— 判据空转，未对任何行生效")
    for row, ln in e3_rows:
        rid = cell(row, "id") or f"<行{ln}>"
        hits = find_manifest_refs(cell(row, "证据"), repo)
        if not hits:
            emit("L3", False, rid, "E3+ 但证据列无 docs/release-evidence/<rc>/journeys/J<nn>/manifest.json")
            continue
        # ⚠️ 全称判据，不是存在判据：证据里**每一份** journey manifest 都要合格。
        # 只要「命中一份 live 就放行」，把一份 reconstructed 混进同一行就不会被拦下，
        # 而读者会把整行读成「这些旅程都在参考环境跑过」。
        ok_list, bad_list = [], []
        for h in sorted(set(hits)):
            full = os.path.join(repo, h)
            if not os.path.exists(full):
                bad_list.append(f"{h} 不存在")
                continue
            try:
                with open(full, encoding="utf-8") as fh:
                    mf = json.load(fh)
            except Exception as exc:
                bad_list.append(f"{h} 无法解析: {exc}")
                continue
            mode = (mf.get("provenance") or {}).get("mode")
            dirty = (mf.get("candidate") or {}).get("dirty")
            if mode == "live" and dirty is False:
                ok_list.append(h)
            else:
                bad_list.append(f"{h} provenance.mode={mode!r} candidate.dirty={dirty!r}（须 live / False）")
        emit("L3", (not bad_list) and bool(ok_list), rid,
             f"合格 {len(ok_list)}/{len(set(hits))} 份"
             + ("; 不合格: " + "; ".join(bad_list) if bad_list else ""))

    # ── L4 路径 / SHA / tag 真核 ───────────────────────────────────────────
    n_path = n_sha = n_tag = 0
    for row, ln in zip(rows, linenos):
        rid = cell(row, "id") or f"<行{ln}>"
        bad: list[str] = []
        for colname in ("入口", "证据"):
            paths, shas, tags = classify_tokens(cell(row, colname))
            for p in paths:
                n_path += 1
                if not os.path.exists(os.path.join(repo, norm_path(p))):
                    bad.append(f"[{colname}] 路径不存在: {p}")
            for s in shas:
                n_sha += 1
                t = git.object_type(s)
                if t != "commit":
                    bad.append(f"[{colname}] SHA 非 commit({t or '未知对象'}): {s}")
            for tg in tags:
                n_tag += 1
                if tg not in git.tags():
                    bad.append(f"[{colname}] tag 不在 git tag -l: {tg}")
        # ⚠️ 逐行报该行自己的对象数：合计非零不能证明**每一行**都被检查过
        # （Codex r2 MEDIUM-8 的负控输入：删光某行的证据文件与 tag、只留 SHA，
        #   合计 paths 仍有 114，整体照样 PASS）。
        ev_paths, ev_shas, ev_tags = classify_tokens(cell(row, "证据"))
        if not ev_paths:
            bad.append(f"[证据] 该行没有任何文件路径——只有 SHA/tag 不算可复查的证据件")
        emit("L4", not bad, rid,
             "; ".join(bad) if bad
             else f"本行证据对象 路径{len(ev_paths)}/SHA{len(ev_shas)}/tag{len(ev_tags)}，入口+证据 token 全部真核通过")

    print(f"L4 checked= paths={n_path} sha8={n_sha} tags={n_tag} （「零失败」与「零检查」不可混淆：先读这行计数再读结论）")

    # ── L11 证据 SHA 必须已在主干（= 核验 SHA 的祖先） ──────────────────────
    n_anc = 0
    for row, ln in zip(rows, linenos):
        rid = cell(row, "id") or f"<行{ln}>"
        base = cell(row, "核验 SHA").strip(_STRIP_CHARS)
        _, shas, _ = classify_tokens(cell(row, "证据"))
        bad = []
        for sh in shas:
            n_anc += 1
            if not git.is_ancestor(sh, base):
                bad.append(f"{sh} 不是核验 SHA {base} 的祖先（未合入主干？）")
        if not shas:
            emit("L11", False, rid, f"证据列无任何 8 位 SHA — 无法判该能力的代码是否真在 {base} 上")
        else:
            emit("L11", not bad, rid,
                 "; ".join(bad) if bad else f"{len(shas)} 个证据 SHA 全部是 {base} 的祖先")

    print(f"L11 checked= 证据SHA={n_anc}（tag 不计：squash 后原分支恒非主干祖先，见文件头）")

    # ── L12 证据 SHA 与本行能力的对应性 ────────────────────────────────────
    # 祖先关系只说明「这个 commit 在主干上」，不说明「它和这条能力有关」——
    # 任何一个主干 commit 都能过 L11。本条要求该 SHA 至少改动过本行入口列里的一个文件。
    n_corr = 0
    for row, ln in zip(rows, linenos):
        rid = cell(row, "id") or f"<行{ln}>"
        ent_paths, _, _ = classify_tokens(cell(row, "入口"))
        ent_set = {norm_path(x) for x in ent_paths}
        _, shas, _ = classify_tokens(cell(row, "证据"))
        if not ent_set or not shas:
            emit("L12", False, rid,
                 f"入口路径 {len(ent_set)} 个 / 证据 SHA {len(shas)} 个 — 任一为 0 则对应性无法判")
            continue
        unrelated = []
        for sh in shas:
            n_corr += 1
            touched = git.files_touched(sh)
            if not (touched & ent_set):
                unrelated.append(f"{sh} 未改动本行任何入口文件")
        emit("L12", not unrelated, rid,
             "; ".join(unrelated) if unrelated
             else f"{len(shas)} 个证据 SHA 各自都改动过本行入口文件")

    print(f"L12 checked= (证据SHA×行)={n_corr}")

    # ── L13 台账的表格结构必须与契约逐张相符 ──────────────────────────────
    tables, html_lines = scan_tables(text)
    got: dict[int, int] = {}
    for _, ncol, _, _ in tables:
        got[ncol] = got.get(ncol, 0) + 1
    bad13: list[str] = []
    if got != EXPECTED_TABLES:
        bad13.append(f"表格结构不符契约：实测 列数→张数 {got}，期望 {EXPECTED_TABLES}")
        for ln, ncol, first, _ in tables:
            if got.get(ncol, 0) != EXPECTED_TABLES.get(ncol, 0):
                bad13.append(f"  行{ln}: {ncol} 列表，首格={first!r}")
    if html_lines:
        bad13.append(f"出现 HTML 表格标签（行 {html_lines}）——它不经 markdown 表解析，能藏行")
    if bad13:
        for why in bad13:
            emit("L13", False, "-", why)
    else:
        emit("L13", True, "-", f"全文表格结构符合契约：{got}（fenced 代码块内的示例表不计）")
    print(f"L13 checked= 表格块={len(tables)} 列数分布={got} HTML表标签={len(html_lines)}")

    # ── L14 两个解析器必须看到同一批能力行（自洽断言） ────────────────────
    cap_tables = [t for t in tables if t[1] == len(EXPECTED_HEADERS)]
    scan_rows: set[int] = set()
    for _, _, _, data in cap_tables:
        scan_rows |= set(data)
    parse_rows = set(linenos)
    only_scan = sorted(scan_rows - parse_rows)
    only_parse = sorted(parse_rows - scan_rows)
    # 行号一致还不够：两侧对**同一行切出几格**也必须一致，否则「判据看到 12 格、
    # 扫描看到 11 格」这种口径差同样是缝（r5 M-2 第一条）。
    width_bad = [f"行{ln}切出 {len(r)} 格（表头 {len(headers)} 格）"
                 for r, ln in zip(rows, linenos) if len(r) != len(headers)]
    if only_scan or only_parse or width_bad:
        emit("L14", False, "-",
             (f"两个解析器对能力表的行不一致：全文扫描多出 {only_scan}；判据多出 {only_parse}"
              if (only_scan or only_parse) else "")
             + ("；列数不一致：" + "; ".join(width_bad[:5]) if width_bad else ""))
    else:
        emit("L14", True, "-",
             f"判据解析器与全文扫描看到同一批 {len(parse_rows)} 行能力行，且每行都切出 {len(headers)} 格")
    print(f"L14 checked= 判据行={len(parse_rows)} 扫描行={len(scan_rows)} "
          f"扫描独有={len(only_scan)} 判据独有={len(only_parse)}")
    # ── L15 台账自述的条目数必须等于解析到的行数 ──────────────────────────
    # L13 锁结构、L14 锁两个解析器一致；但把能力行挪成列表/引用块/塞进别的表时，
    # 两个解析器会**一致地**看不见它们——那时唯一的信号就是行数少了（Codex r4 给的
    # 另外三种形态）。所以让台账自己声明条目数，由门核对：这是文件对自己的断言，
    # 不是又一条识别规则，也不随藏行写法增加。
    declared, why15 = declared_rows(text)
    if declared is None:
        emit("L15", False, "-", why15 + " —— 无法核对是否有行被挪出本表")
        print(f"L15 checked= 自述=<不可用> 解析={len(rows)}")
    else:
        emit("L15", declared == len(rows), "-",
             f"自述条目数={declared}，解析到={len(rows)}"
             + ("" if declared == len(rows) else "  ← 有行被挪出能力表，或声明未同步"))
        print(f"L15 checked= 自述={declared} 解析={len(rows)}")

    print(f"rows={len(rows)}")
    print(f"LINT: {'FAIL' if fails else 'PASS'}" + (f"  failed={fails}" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
