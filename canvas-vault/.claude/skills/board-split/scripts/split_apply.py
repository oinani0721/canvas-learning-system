#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""board-split 执行侧 (CARD-G5-10, scripts-only, ⛔ 不加 SKILL.md)。

消费 `split_preview.py` 产出的 `split-preview-<board>.json` + 用户逐条拍板的
`--confirm <stable_id>`，在确认后**原子创建** `节点/` 派生 md：

- 准入五门（任一不过 = 整批拒绝且零产物，连批次目录都不建）：
  ① preview 过期：重算 preview 比 `vault_fingerprint` + 候选集 + 逐候选内容指纹/行号
     + 锚文件**字节锚**（`sources[]` 的 sha256；容忍面 = 仅本 preview 候选名的精确形态
     callout 行插入 —— 全量重写 JSON 仍可伪造, 见 UAT「H 整改」残余风险）；
  ② `--confirm` 的 stable_id 必须在本 preview 候选集里；
  ③ `identity_ambiguous=true` 候选拒绝持久化 `split_stable_id`
     （split_preview.py docstring :41-42 铁律）；
  ④ `conflict_unresolvable` 或目标已存在且其 `split_stable_id` ≠ 本候选 ⇒ 拒绝；
     已存在且相同 = 已应用，计入「跳过」；
  ⑤ `节点/` / `原白板/` / 目标路径 / 来源锚点含 symlink 组件 ⇒ 拒绝。
- 创建走 `O_CREAT | O_EXCL | O_NOFOLLOW` + `fsync`（既有文件绝不覆盖）；每件
  写前记 `intent`、写后记 `done` + 实际 sha256，账本复用 P7-A 的
  `canvas-vault/.claude/scripts/undo_journal.py`（BatchJournal）。
- `--undo <batch_id>`：只删账上记着且当前 sha256 与记录一致的自建文件（用户改过
  的拒删并列出），被 callout 改过的板文件从批次备份逐字节还原；可重入。
- `--insert-callout`（默认关）：TTY 逐候选 `y/N`；非 TTY 必须 `--confirm-insert`，
  未给 = 全部跳过（不静默插）。插入文本逐字照 `split_preview.render_md` :1002。

⛔ 默认路径 0 物理删除：`os.remove` 只出现在 undo 分支、只作用于账上记录的自建文件
（AST 门数 Call 节点，不数文本）。⛔ 不改 `split_preview.py`；不调
`sync_board_concepts.py`（板内 Concepts 托管块 = P7-C 地盘）。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPLIT_PREVIEW_PATH = _HERE / "split_preview.py"
_UNDO_JOURNAL_PATH = _HERE.parents[2] / "scripts" / "undo_journal.py"


def _load_sibling(path: Path, mod_name: str, why: str):
    """加载兄弟模块。⛔ 缺失即拒绝运行, 不做本地降级实现。"""
    if not path.is_file():
        raise SystemExit(f"✗ 复用来源缺失, 拒绝以未加固的写侧运行: {path}\n  （{why}）")
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    # ⛔ exec_module 默认会往被导入模块旁边写 __pycache__ —— 那是往 vault 里落文件。
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


_SP = _load_sibling(
    _SPLIT_PREVIEW_PATH,
    "_g510_split_preview",
    "stable id / 候选字段 / 写侧物理防御必须与产出 preview 的引擎同源, 手抄一份必然漂移",
)
_UJ = _load_sibling(
    _UNDO_JOURNAL_PATH,
    "_g510_undo_journal",
    "备份 / 账本 / 撤销是共用模块, 本脚本不自带第二份实现",
)

# ───────────────────────────────── 常量 ─────────────────────────────────

DEFAULT_WORK_PARENT = "outputs"
DEFAULT_WORK_NAME = "board-split"

#: 本脚本的账本动作（与 P7-A 的 copy/link/move/recycle/skip 并列, 只住在 split 批次里）。
OP_SPLIT_CREATE = "split_create"
OP_SPLIT_MODIFY = "split_modify"

STATE_PLANNED = _UJ.STATE_PLANNED
STATE_DONE = _UJ.STATE_DONE
STATE_UNDONE = _UJ.STATE_UNDONE

_SOURCE_PREFIXES = ("原白板/", "节点/")


def die(msg: str) -> "None":
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def yaml_scalar(value: str) -> str:
    """字符串 → YAML 双引号标量。JSON 字符串语法是 YAML 双引号标量的子集,
    用它承载任意用户内容（含引号/反斜杠/控制字符）不会拼出非法 YAML。"""
    return json.dumps(value, ensure_ascii=False)


def vault_fingerprint(vault: Path) -> str:
    """与 split_preview.build_preview 同一算式（G5-3 冻结的 vf1- 格式）。"""
    real = os.path.realpath(vault)
    return "vf1-" + hashlib.sha256(real.encode("utf-8")).hexdigest()[: _SP._HASH_HEX]


def work_root(vault: Path) -> Path:
    return vault / DEFAULT_WORK_PARENT / DEFAULT_WORK_NAME


def callout_line(resolved_name: str) -> str:
    """逐字照 split_preview.render_md :1002（`+` 是它的 diff 记号, 不是内容）。"""
    return f"> [!relation/related_to]+ 已派生为 [[节点/{resolved_name}]] · 相关"


def existing_split_stable_id(path: Path) -> "str | None":
    """读既有节点 frontmatter 的 `split_stable_id`（只认我们自己写的确切形状）。

    读不出来一律返回 None ⇒ 调用方按「≠ 本候选」处置（拒绝侧, fail-closed）。
    ⛔ 不设行数上限：上限会让 frontmatter 超长（split_stable_id 落在 200 行后）的残留
    读不出 id 而从减法中消失, 旧名变成「空闲」再建同 id 副本（r5-HIGH-2 路径 B）。
    """
    try:
        raw = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            for ln in lines[1:i]:
                if ln.startswith("split_stable_id:"):
                    return ln.split(":", 1)[1].strip().strip('"').strip("'") or None
            return None
    return None


def preview_display_path(vault: Path, preview_path: Path) -> str:
    """账上记 preview 路径时优先记 vault 相对路径（不把用户机器目录结构写进 vault）。"""
    try:
        return str(preview_path.resolve().relative_to(vault.resolve()))
    except ValueError:
        return preview_path.name


# ─────────────────────────── 准入五门 ───────────────────────────


def _confirmed_candidates(data: dict, confirm_ids: list[str]) -> list[dict]:
    by_id = {c["stable_id"]: c for c in data["candidates"]}
    unknown = [sid for sid in confirm_ids if sid not in by_id]
    if unknown:
        die(f"✗ --confirm 的 stable_id 不在本 preview 的候选集里: {', '.join(unknown)}")
    return [c for c in data["candidates"] if c["stable_id"] in set(confirm_ids)]


def _check_symlink_gates(vault: Path, confirmed: list[dict]) -> dict[str, Path]:
    """门⑤：目录/目标/来源锚点全程无 symlink 组件。返回 {stable_id: 目标绝对路径}。"""
    for d in ("原白板", "节点"):
        dp = vault / d
        if dp.is_symlink():
            die(f"✗ {d}/ 目录本身是 symlink, 拒绝写入: {dp}")
        _SP.assert_symlink_free(dp)
    targets: dict[str, Path] = {}
    for c in confirmed:
        name = c.get("resolved_name") or ""
        if not _SP.member_name_ok(name):
            die(f"✗ 候选 {c['stable_id']} 的 resolved_name 含非法字符/路径逃逸, 拒绝: {name!r}")
        if len(f"{name}.md".encode("utf-8")) > _SP.MAX_FILENAME_BYTES:
            die(f"✗ 候选 {c['stable_id']} 的节点文件名过长: {name!r}")
        target = _UJ.safe_join(vault, f"节点/{name}.md", what="节点落点")
        _SP.assert_symlink_free(target)
        anchor_rel = c["source_anchor"]["file"]
        if not anchor_rel.startswith(_SOURCE_PREFIXES):
            die(f"✗ 候选 {c['stable_id']} 的来源锚点在 原白板/ 或 节点/ 之外, 拒绝: {anchor_rel!r}")
        anchor = _UJ.safe_join(vault, anchor_rel, what="来源锚点")
        if os.path.islink(str(anchor)):
            die(f"✗ 候选 {c['stable_id']} 的来源锚点是 symlink, 拒绝读取: {anchor}")
        try:
            _SP.assert_symlink_free(anchor)
        except SystemExit as e:
            die(f"✗ 候选 {c['stable_id']} 的来源锚点路径含 symlink 组件: {e}")
        targets[c["stable_id"]] = target
    return targets


def _check_ambiguous(confirmed: list[dict]) -> None:
    """门③：identity_ambiguous 候选拒绝持久化 split_stable_id（docstring :41-42）。"""
    for c in confirmed:
        if c["identity_ambiguous"]:
            die(
                f"✗ 候选 {c['stable_id']}（index={c['index']}）identity_ambiguous=true"
                f"（同标题路径出现 {c['ambiguous_group_size']} 次, 身份绑在槽位上而非内容单元），"
                "按 G5-3 契约拒绝为它持久化 split_stable_id"
            )


def _check_conflicts(confirmed: list[dict], targets: dict[str, Path]) -> list[dict]:
    """门④：conflict_unresolvable ⇒ 拒绝；目标已存在且 split_stable_id ≠ 本候选 ⇒ 拒绝；
    相同 ⇒ 已应用（跳过）。返回已应用（skip）的候选列表。"""
    applied: list[dict] = []
    for c in confirmed:
        if c["conflict_unresolvable"]:
            die(f"✗ 候选 {c['stable_id']}（{c['resolved_name']}）conflict_unresolvable=true, 重名不可解, 拒绝")
        target = targets[c["stable_id"]]
        if os.path.lexists(str(target)):
            got = existing_split_stable_id(target)
            if got == c["stable_id"]:
                applied.append(c)
            else:
                die(
                    f"✗ 目标已存在且不是本候选的产物: {target}\n"
                    f"  它记录的 split_stable_id={got!r} ≠ 本候选 {c['stable_id']!r}；拒绝覆盖（零产物）"
                )
    return applied


def _span_drift_reason(vault: Path, c: dict, stored_fp: str) -> "tuple[str | None, bool]":
    """门①的内容面：在**账上行号**处重算 content_fingerprint（按字节读, 不做换行归一）。

    返回 (拒绝原因, 是否走了 callout 容差)：
    - (None, False)：原字节指纹**精确**相符 —— 区间自 preview 起未被改动, 区间内的
      callout 形态行是预览时的真实内容, 创建时必须原样保留（r5-HIGH-3）；
    - (None, True)：原样不符, 但把**全文件**的派生 callout 形态行（生成段/注释里的除外）
      全部剔除后, 账上行号处的内容指纹与记录一致 —— preview 后插入 callout 的漂移解释
      路径（含嵌套候选 callout 与自己的插入, 剔除后行号对齐复原）, 创建时须剔除这些行；
    - (原因, _)：其余任何内容/行号漂移。区间原本就含 callout 行的极少数输入会因此保守拒绝。"""
    anchor = _UJ.safe_join(vault, c["source_anchor"]["file"], what="来源锚点")
    try:
        raw = anchor.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return f"来源文件读不回来: {anchor} ({e})", False
    lines = raw.split("\n")
    a0, a1 = c["source_anchor"]["line_start"], c["source_anchor"]["line_end"]
    mask = [k in _SP.MACHINE_KINDS for k in _SP.strip_generated_detail(lines)]
    if _SP.compute_content_fingerprint(lines, a0, a1, mask) == stored_fp:
        return None, False
    stripped = _SP.strip_generated(lines)
    comments = _SP.comment_mask(lines, stripped)
    hits = {
        i for i in range(len(lines)) if not stripped[i] and not comments[i] and _SP._DERIVED_CALLOUT.search(lines[i])
    }
    if hits:
        lines2 = [ln for i, ln in enumerate(lines) if i not in hits]
        mask2 = [m for i, m in enumerate(mask) if i not in hits]
        if _SP.compute_content_fingerprint(lines2, a0, a1, mask2) == stored_fp:
            return None, True
    return f"第 {c['index']} 条候选（{c['resolved_name']}）的内容指纹与该行号区间已对不上", False


_SPLITLINES_ONLY_RE = re.compile(r"[\v\f\x1c-\x1e\x85\u2028\u2029]")


def _check_anchor_line_contract(vault: Path, confirmed: list[dict]) -> None:
    """preview 用 splitlines() 切行、执行侧用 split("\\n")：裸 CR 与行分隔类字符下两套行号
    口径不可比（会以「过期」的含糊理由失败）。这里提前给出精确的拒绝理由。"""
    seen: set[str] = set()
    for c in confirmed:
        rel = c["source_anchor"]["file"]
        if rel in seen:
            continue
        seen.add(rel)
        anchor = _UJ.safe_join(vault, rel, what="来源锚点")
        try:
            text = anchor.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as e:
            die(f"✗ 来源文件读不回来: {anchor} ({e})")
        if "\r" in text.replace("\r\n", "") or _SPLITLINES_ONLY_RE.search(text):
            die(
                f"✗ 来源文件含裸 CR / 行分隔类字符（preview 与执行侧的切行口径不同, 行号不可信）: "
                f"{rel} —— 请把行尾统一为 LF 或 CRLF 后重跑 preview"
            )


def _callout_mapped_span(vault: Path, rel: str, start: int, end: int):
    """把 fresh 坐标下的 (line_start, line_end) 映射到「剔除全部派生 callout 行」的坐标系。

    合法漂移只有「本批插入的 callout 行」；映射后仍与账上行号不符 ⇒ 板被换过。"""
    anchor = _UJ.safe_join(vault, rel, what="来源锚点")
    try:
        lines = anchor.read_bytes().decode("utf-8").split("\n")
    except (OSError, UnicodeDecodeError):
        return None
    stripped = _SP.strip_generated(lines)
    comments = _SP.comment_mask(lines, stripped)
    callout_idx = [
        i for i, ln in enumerate(lines) if not stripped[i] and not comments[i] and _SP._DERIVED_CALLOUT.search(ln)
    ]
    return (
        start - sum(1 for i in callout_idx if i < start),
        end - sum(1 for i in callout_idx if i < end),
    )


def _enumerate_node_pool(node_dir: Path) -> "tuple[list[tuple[Path, str]], str | None]":
    """显式递归枚举 节点/ 下需要参与归属判定的条目。

    ⛔ 不用 `Path.rglob`：它的递归 `scandir` 遇 `OSError` 会**静默跳过整段**（r8-HIGH-1）——
    不可列举目录里的同 `stable_id` 残留会凭空消失, 旧名被当「空闲」再建副本。这里任何一层目录
    枚举失败都返回原因（调用方 fail-closed 拒绝整批）, 绝不跳过。

    返回 `([(path, kind)], 拒绝原因)`；kind ∈ {"symlink-dir", "symlink-md", "dir-md", "md"}，
    与旧 `rglob("*.md")` + `rglob("*")` 兜底同覆盖面（.md 文件 + symlink 目录 + 目录名以 .md 结尾）。
    """
    out: list[tuple[Path, str]] = []
    stack = [node_dir]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for ent in sorted(it, key=lambda e: e.name):
                    p = Path(ent.path)
                    if ent.is_symlink():
                        if ent.is_dir():
                            out.append((p, "symlink-dir"))
                        elif p.name.endswith(".md"):
                            out.append((p, "symlink-md"))
                    elif ent.is_dir(follow_symlinks=False):
                        if p.name.endswith(".md"):
                            out.append((p, "dir-md"))
                        else:
                            stack.append(p)
                    elif p.name.endswith(".md"):
                        out.append((p, "md"))
        except OSError as e:
            return out, (
                f"池内目录无法枚举（{d}）—— 无法排除里面藏着同 stable_id 的残留, "
                f"拒绝（fail-closed, 请恢复该目录的可列举权限后重跑）: {e}"
            )
    return out, None


def _resolution_replay_reason(vault: Path, data: dict) -> "str | None":
    """按「批前池」重放整份候选命名解析：确定性选名必须与 preview 逐条一致。

    ⛔ 不比对 fresh 的 resolved_name 而重放：本 preview 已落地的节点会进池, 让 fresh 名
    带上 `_2.._9` 后缀（合法重跑/分段确认）；批前池 = 当前池减去「**本 preview 的产物**」
    （判据 = 该名字的节点 frontmatter `split_stable_id` 命中同 id 候选 —— 跨批次也成立）,
    重放结果应与 preview 逐字相同 —— 手改成任意空闲后缀（含同基错误后缀）都会露馅。"""
    node_dir = vault / "节点"
    pool = {p.stem for p in node_dir.glob("*.md")} if node_dir.is_dir() else set()
    # ⛔ 残留定位: 递归枚举全池查「携带本 preview 候选 stable_id」的节点 —— **只有** canonical
    # 顶层路径 节点/<账上名>.md 才算自家产物（可放行）；其余位置一律拒绝：改名、移入子目录
    # （含保持原名）、symlink 目录/文件、不可枚举或不可读的目录/条目。枚举用显式 scandir
    # （⛔ 不用 rglob：其递归 scandir 静默吞 OSError, 不可列举目录会整段消失 —— r8-HIGH-1）,
    # 任何目录枚举失败 = fail-closed（r4-HIGH-1 / r5-HIGH-2 / r7-HIGH-1 / r8-HIGH-1）。
    by_id = {c["stable_id"]: c["resolved_name"] for c in data["candidates"]}
    entries, enum_reason = _enumerate_node_pool(node_dir) if node_dir.is_dir() else ([], None)
    if enum_reason:
        return enum_reason
    for p, kind in entries:
        rel = f"节点/{p.relative_to(node_dir)}"
        if kind == "symlink-dir":
            return (
                f"发现无法安全判定归属的池内条目: {rel} 是 symlink 目录 —— 无法排除里面藏着残留, "
                f"拒绝（请移出 节点/ 或恢复为普通目录后重跑）"
            )
        if kind == "symlink-md":
            return (
                f"发现无法安全判定归属的池内条目: {rel} 是 symlink —— 无法证明它"
                f"不是本 preview 产物的残留, 拒绝（请移出 节点/ 或恢复为普通文件后重跑）"
            )
        if not p.is_file():
            return (
                f"发现无法安全判定归属的池内条目: {rel} 不是普通文件 —— "
                f"无法证明它不是本 preview 产物的残留, 拒绝（请移出 节点/ 后重跑）"
            )
        try:
            p.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            return (
                f"发现无法安全读取归属的池内条目: {rel}（读不回或非 UTF-8）—— "
                f"无法证明它不是本 preview 产物的残留, 拒绝（fail-closed）"
            )
        sid = existing_split_stable_id(p)
        if sid in by_id and p != node_dir / f"{by_id[sid]}.md":
            return (
                f"发现同 stable_id 的残留节点: {rel}（候选账上路径 节点/{by_id[sid]}.md）"
                f"—— 请把该文件移回原路径并恢复原文件名（重跑 preview 不解除本门）"
            )
    ours: set = set()
    for c in data["candidates"]:
        name = c["resolved_name"]
        p = node_dir / f"{name}.md"
        if p.is_file() and not _UJ.is_symlink(p) and existing_split_stable_id(p) == c["stable_id"]:
            ours.add(name)
    claimed: set = set()
    for c in data["candidates"]:
        exp = _SP.resolve_name(c["suggested_name"], pool - ours, claimed)["resolved_name"]
        if exp != c["resolved_name"]:
            return (
                f"候选 {c['stable_id']} 的 resolved_name 与按批前池重放不符"
                f"（preview {c['resolved_name']!r} vs 重放 {exp!r}）"
            )
        claimed.add(exp)
    return None


def _anchor_sha_reconciliation(vault: Path, data: dict, confirmed: list[dict]) -> None:
    """门① 的**锚文件字节锚**（r5-HIGH-1）：`sources[]` 里的 sha256 才是与 preview 生成时
    板/种子字节的绑定；只对账候选 `content_fingerprint`（旧 JSON 里可编辑）时,「改正文 +
    只把新指纹抄进旧 JSON」会让确认 id 落到改后内容。

    容忍面**严格限于**「本 preview 候选名的**精确形态** callout 行」插入（逐字等于
    `callout_line(resolved_name)`，含 CRLF 尾 `\\r`）：多轮拆分里旧一轮 callout 的节点名
    已被 resolve_name 加后缀, 不在本轮候选名集, 故不会被误剔（strip-all 会 livelock 多轮流）。
    """
    sources = data.get("sources")
    by_file = {s["file"]: s for s in sources if isinstance(s, dict) and s.get("file")} if isinstance(sources, list) else {}
    board_entry = by_file.get(data.get("board_file"))
    if board_entry is None or board_entry.get("sha256") != data.get("board_sha256"):
        die("✗ preview 已过期：sources[] 的板记录与 board_sha256 不自洽（preview JSON 被拼改过）—— 请重跑 preview")
    forms = {callout_line(c["resolved_name"]) for c in data["candidates"]}
    forms |= {f + "\r" for f in forms}
    seen: set[str] = set()
    for c in confirmed:
        rel = c["source_anchor"]["file"]
        if rel in seen:
            continue
        seen.add(rel)
        entry = by_file.get(rel)
        if entry is None or not entry.get("sha256"):
            die(
                f"✗ preview 已过期：sources[] 没有 {rel} 的 sha256 记录 —— "
                "无法证明该锚文件自 preview 后未被改, 拒绝（请重跑 preview）"
            )
        anchor = _UJ.safe_join(vault, rel, what="来源锚点")
        try:
            raw_bytes = anchor.read_bytes()
        except OSError as e:
            die(f"✗ preview 已过期：来源锚文件读不回来: {rel} ({e})")
        if sha256_bytes(raw_bytes) == entry["sha256"]:
            continue
        try:
            raw = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            die(f"✗ preview 已过期：来源锚文件非 UTF-8, 无法对账字节锚: {rel} —— 请重跑 preview")
        lines = raw.split("\n")
        # ⛔ 只剔**可能被当作本轮插入**的行：机器段（code fence / AUTO-GENERATED / Recent Activity）
        # 与 HTML 注释里的同形行是 preview 时就存在的内容, 与 derived_names_in 同口径（r6-MEDIUM-1）。
        machine = _SP.strip_generated(lines)
        comments = _SP.comment_mask(lines, machine)
        kept = [ln for i, ln in enumerate(lines) if machine[i] or comments[i] or ln not in forms]
        if sha256_bytes("\n".join(kept).encode("utf-8")) == entry["sha256"]:
            continue
        die(f"✗ preview 已过期：{rel} 与 preview 生成时的字节锚不符（板/种子文件已改）—— 请重跑 preview")


def _check_fresh(vault: Path, data: dict, confirmed: list[dict]) -> dict[str, tuple[int, int, bool]]:
    """门①：重算 preview（vault 指纹 + 候选集 + 命名重放 + 逐候选绑定/内容/行号）。

    返回 {stable_id: (fresh 行起, fresh 行止, 是否 callout 容差)} —— 后续创建与插入必须用
    **这套当前行号**；第三位决定创建时是否剔除 callout 形态行（r5-HIGH-3）。"""
    try:
        fresh = _SP.build_preview(vault, data["board"], int(data["scale_gate"]["threshold"]))
    except SystemExit as e:
        die(f"✗ preview 已过期校验失败（重算 preview 不通过）: {e}")
    if fresh["vault_fingerprint"] != data["vault_fingerprint"]:
        die(
            f"✗ preview 已过期：vault 指纹不符（preview {data['vault_fingerprint']} ≠ 现算 "
            f"{fresh['vault_fingerprint']}）—— 这份 preview 不是当前 vault 的, 请重跑 preview"
        )
    old_ids = {c["stable_id"] for c in data["candidates"]}
    new_ids = {c["stable_id"] for c in fresh["candidates"]}
    if old_ids != new_ids:
        added = sorted(new_ids - old_ids)[:2]
        gone = sorted(old_ids - new_ids)[:2]
        die(f"✗ preview 已过期：候选集合已变（新增 {added} · 移除 {gone}）—— 板或种子笔记已改, 请重跑 preview")
    # ⛔ 安全标志必须与重算结果对账, 不能只信旧 JSON（HIGH-1: 手改 preview 把
    # identity_ambiguous/conflict_unresolvable 改成 false, 门③④ 会 fail-open）。
    fresh_by_id = {c["stable_id"]: c for c in fresh["candidates"]}
    for c in data["candidates"]:
        fc = fresh_by_id[c["stable_id"]]
        for key in ("identity_ambiguous", "ambiguous_group_size", "conflict_unresolvable", "basis"):
            if c.get(key) != fc.get(key):
                die(
                    f"✗ preview 已过期：候选 {c['stable_id']} 的 {key} 与重算不符"
                    f"（preview {c.get(key)!r} ≠ 现算 {fc.get(key)!r}）—— 拒绝按未经对账的预览动盘, 请重跑 preview"
                )
    # ⛔ 命名解析必须按批前池重放（见 _resolution_replay_reason）：只看 fresh 名会被
    # 「本 preview 产物入池 → 合法后缀」掩住, 放行手改成同基任意后缀的 preview。
    replay_reason = _resolution_replay_reason(vault, data)
    if replay_reason:
        die(f"✗ preview 已过期：{replay_reason} —— 请重跑 preview")
    # ⛔ 内容指纹存在旧 JSON 里、可被手改；另起一条与 preview 生成时**字节**绑定的锚（r5-HIGH-1）。
    _anchor_sha_reconciliation(vault, data, confirmed)
    positions: dict[str, tuple[int, int, bool]] = {}
    for c in confirmed:
        fc = fresh_by_id[c["stable_id"]]
        ct, ft = c["source_anchor"], fc["source_anchor"]
        if ct["file"] != ft["file"] or ct["heading_path"] != ft["heading_path"]:
            die(f"✗ preview 已过期：候选 {c['stable_id']} 的来源锚点（file/heading_path）与重算不符 —— 请重跑 preview")
        if fc["suggested_name"] != c["suggested_name"]:
            die(f"✗ preview 已过期：候选 {c['stable_id']} 的 suggested_name 与重算不符 —— 请重跑 preview")
        mapped = _callout_mapped_span(vault, ct["file"], ft["line_start"], ft["line_end"])
        if mapped is not None and mapped != (ct["line_start"], ct["line_end"]):
            die(
                f"✗ preview 已过期：候选 {c['stable_id']} 的行号在剔除本批 callout 后与现算不符"
                f"（{mapped} ≠ {(ct['line_start'], ct['line_end'])}）—— 板可能被换过, 请重跑 preview"
            )
        reason, strip_callouts = _span_drift_reason(vault, c, c["content_fingerprint"])
        if reason:
            die(f"✗ preview 已过期：{reason} —— 请重跑 preview")
        positions[c["stable_id"]] = (ft["line_start"], ft["line_end"], strip_callouts)
    return positions


def run_gates(
    vault: Path, data: dict, confirm_ids: list[str]
) -> tuple[list[dict], list[dict], dict[str, Path], dict[str, tuple[int, int, bool]]]:
    """五门按代价从低到高跑；任一不过即 die（拒绝路径零产物）。"""
    confirmed = _confirmed_candidates(data, confirm_ids)
    if not confirmed:
        die("✗ --confirm 为空：没有任何候选被确认（本工具只做「显式确认后创建」）")
    targets = _check_symlink_gates(vault, confirmed)
    _check_ambiguous(confirmed)
    applied = _check_conflicts(confirmed, targets)
    _check_anchor_line_contract(vault, confirmed)
    positions = _check_fresh(vault, data, confirmed)
    return confirmed, applied, targets, positions


# ─────────────────────────── 创建 ───────────────────────────


def render_node_md(c: dict, board: str, body_lines: list[str], created_at: str) -> str:
    """派生节点全文。frontmatter 键口径对齐 ai-linked-doc SKILL.md :140-158:
    `source_board` + `relationships` 双写, `created_from: board_split`,
    新增 G5-3 指定的 `split_stable_id` + `split_stable_id_basis`。"""
    anchor_file = c["source_anchor"]["file"]
    stem = anchor_file[:-3] if anchor_file.endswith(".md") else anchor_file
    scalars = {
        "type": "concept",
        "created_at": created_at,
        "source_board": yaml_scalar(f"[[原白板/{board}]]"),
        "created_from": "board_split",
        "split_stable_id": c["stable_id"],
        "split_stable_id_basis": json.dumps(c["stable_id_basis"], ensure_ascii=False),
    }
    if c["basis"].startswith("seed-note"):
        seed_stem = stem[len("节点/") :] if stem.startswith("节点/") else stem
        scalars["source_note"] = yaml_scalar(f"[[{seed_stem}]]")
    L = ["---", *[f"{k}: {v}" for k, v in scalars.items()]]
    L += [
        "relationships:",
        "  - type: split_from",
        f"    target: {yaml_scalar(f'[[{stem}]]')}",
        f"    derived_at: {created_at}",
        "---",
        "",
        f"# {c['resolved_name']}",
        "",
        *body_lines,
    ]
    return "\n".join(L) + "\n"


def _append_entry(journal, row: dict) -> dict:
    return journal._append(row)


def run_create(
    vault: Path,
    data: dict,
    confirmed: list[dict],
    applied: list[dict],
    targets: dict[str, Path],
    positions: dict[str, tuple[int, int, bool]],
    batch_id: str,
    shared_meta: dict,
) -> tuple[int, set[str]]:
    """--apply 主流程：批次 + 逐件 intent→写→done。返回 (failed, 已落地/可认领的 stable_id 集)。"""
    vf = data["vault_fingerprint"]
    journal = _UJ.BatchJournal(work_root(vault), batch_id, root=vault, fingerprint=vf)
    # ⛔ 先纯读判绑定（账已存在时）, 再允许建目录/封口/追加。
    try:
        if journal.journal_path.exists():
            journal.assert_is_ours(vf)
        journal.ensure_dirs()
        rows = journal.load()
        if rows:
            journal._assert_is_a_batch_journal(rows)
            journal._assert_bound_to(rows, vf)
    except _UJ.JournalError as e:
        die(str(e))
    prior = _UJ.latest_by_seq(rows)

    applied_ids = {c["stable_id"] for c in applied}
    created = skipped = failed = 0
    ok_ids: set[str] = set()
    for seq, c in enumerate(confirmed, start=1):
        target_rel = f"节点/{c['resolved_name']}.md"
        target = targets[c["stable_id"]]
        if c["stable_id"] in applied_ids:
            prev_entry = prior.get(seq)
            if prev_entry is not None and prev_entry.get("state") == STATE_PLANNED:
                # 中断重跑：只有**内容与账上计划逐字节相符**才认领补记 —— 目标上那份可能
                # 根本不是本进程写下的（认领外来文件会让 --undo 删掉它, BLOCKER-1）。
                cur = _UJ.sha256_file(target)
                if cur == prev_entry.get("sha256_planned"):
                    _append_entry(journal, {**prev_entry, "state": STATE_DONE, "sha256_after": cur})
                    skipped += 1
                    ok_ids.add(c["stable_id"])
                    print(f"· 跳过（已应用）并补记 done {target_rel}")
                else:
                    failed += 1
                    print(
                        f"✗ [{seq}] 目标已存在且 split_stable_id 相同, 但内容与账上计划不符, "
                        f"拒绝认领（可能是外部文件）: {target_rel}",
                        file=sys.stderr,
                    )
                continue
            skipped += 1
            ok_ids.add(c["stable_id"])
            print(f"· 跳过（已应用） {target_rel}")
            continue
        entry = _append_entry(
            journal,
            {
                "seq": seq,
                "state": STATE_PLANNED,
                "op": OP_SPLIT_CREATE,
                "src": "",
                "dst": target_rel,
                "dst_base": _UJ.BASE_VAULT,
                "sha256_planned": None,
                "meta": dict(shared_meta),
            },
        )
        try:
            anchor = _UJ.safe_join(vault, c["source_anchor"]["file"], what="来源锚点")
            raw = anchor.read_bytes().decode("utf-8")
            lines = raw.split("\n")
            # ⛔ 行号用门① 返回的 **fresh 坐标系**（不是 preview 存的旧行号）：重跑时
            # 上方若已有 callout, 旧行号切片会错位（r3-HIGH-1）。
            a0, a1, strip_callouts = positions[c["stable_id"]]
            if strip_callouts:
                # ⛔ 仅「callout 漂移容差」路径才剔除：正文剔除**全部**派生 callout 形态行
                # （不只自家那把）—— 父候选可能包含后插入的子候选 callout, 收进正文就与
                # preview 时的内容单元不符（r4-HIGH-2）。
                stripped = _SP.strip_generated(lines)
                comments = _SP.comment_mask(lines, stripped)
                callout_idx = {
                    i
                    for i, ln in enumerate(lines)
                    if not stripped[i] and not comments[i] and _SP._DERIVED_CALLOUT.search(ln)
                }
                body_lines = [ln for i, ln in enumerate(lines) if a0 <= i < a1 and i not in callout_idx]
            else:
                # ⛔ exact 指纹已证明区间自 preview 起未被改动：区间内 callout 形态行是
                # 预览时的**真实内容**（已进内容指纹）, 一个都不剔, 否则派生正文少行（r5-HIGH-3）。
                body_lines = lines[a0:a1]
            content = render_node_md(c, data["board"], body_lines, shared_meta["created_at"])
            planned = sha256_bytes(content.encode("utf-8"))
            if not planned:
                raise _UJ.JournalError("内容 sha 计算失败")
        except (OSError, UnicodeDecodeError, _UJ.JournalError) as e:
            failed += 1
            print(f"✗ [{seq}] 读取来源失败, 未创建: {c['source_anchor']['file']} ({e})", file=sys.stderr)
            continue
        entry = _append_entry(journal, {**entry, "sha256_planned": planned})
        try:
            _SP.assert_symlink_free(target.parent)
        except SystemExit as e:
            failed += 1
            print(f"✗ [{seq}] 落点父目录含 symlink 组件（窗口内被换?）, 拒绝创建: {target_rel} ({e})", file=sys.stderr)
            continue
        try:
            fd = os.open(
                str(target),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o644,
            )
        except FileExistsError:
            # 竞态或已应用：判归属（门④ 在准入段已查过, 这里是窗口内兜底）。
            # ⛔ 认领条件 = 同 id **且**当前字节与本次计划逐字节相符 —— 只对 id 会让
            # 外来同名文件被记成 done, 之后 --undo 会把它删掉（BLOCKER-1 同族）。
            got = existing_split_stable_id(target)
            cur = _UJ.sha256_file(target) if target.is_file() and not _UJ.is_symlink(target) else None
            if got == c["stable_id"] and cur == planned:
                _append_entry(journal, {**entry, "state": STATE_DONE, "sha256_after": cur})
                skipped += 1
                ok_ids.add(c["stable_id"])
                print(f"· 跳过（竞态内已应用） {target_rel}")
            else:
                failed += 1
                print(
                    f"✗ [{seq}] 目标已被占用且无法证明是本批计划内容（id 或字节不符）, 拒绝认领: {target_rel}",
                    file=sys.stderr,
                )
            continue
        except OSError as e:
            failed += 1
            print(f"✗ [{seq}] 无法创建节点（O_EXCL/no-follow）: {target_rel} ({e})", file=sys.stderr)
            continue
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content.encode("utf-8"))
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            failed += 1
            print(f"✗ [{seq}] 写入节点失败（账上记 intent, 重跑会重建）: {target_rel} ({e})", file=sys.stderr)
            continue
        _append_entry(
            journal,
            {
                **entry,
                "state": STATE_DONE,
                "sha256_after": _UJ.sha256_file(target),
                "mtime_ns_after": os.stat(str(target), follow_symlinks=False).st_mtime_ns,
            },
        )
        created += 1
        ok_ids.add(c["stable_id"])
        print(f"✓ 创建 {target_rel}（stable_id={c['stable_id']}）")
    print(f"总结: created={created} skipped={skipped} failed={failed} · 批次 {batch_id} · 账本 {journal.journal_path}")
    if failed:
        print("✗ 有失败件：账本已逐件记录, 修正原因后重跑同一命令只会补缺", file=sys.stderr)
    return failed, ok_ids


# ─────────────────────────── callout 插入 ───────────────────────────


def _ask_tty(question: str) -> bool:
    if not sys.stdin.isatty():
        return False
    print(question + " [y/N] ", end="", flush=True)
    try:
        return input().strip().lower() in ("y", "yes")
    except EOFError:
        return False


def run_callout_insert(
    vault: Path,
    data: dict,
    confirmed: list[dict],
    targets: dict[str, Path],
    positions: dict[str, tuple[int, int, bool]],
    ok_ids: set[str],
    batch_id: str,
    confirm_insert: "list[str] | None",
) -> int:
    """--insert-callout：逐候选确认后插一行 callout；同一候选已存在同形 callout 即跳过。"""
    vf = data["vault_fingerprint"]
    journal = _UJ.BatchJournal(work_root(vault), batch_id, root=vault, fingerprint=vf)
    try:
        if journal.journal_path.exists():
            journal.assert_is_ours(vf)
        rows = journal.load()
    except _UJ.JournalError as e:
        die(str(e))
    prior = _UJ.latest_by_seq(rows)
    next_seq = max([r for r in prior] or [0]) + 1

    insert_set = None if confirm_insert is None else set(confirm_insert)
    planned_items: list[dict] = []
    for c in confirmed:
        # ⛔ 只对「本候选创建/认领成功」的件插 callout：创建失败的候选目标可能存在
        # （外来文件）, 给它插「已派生」是替别人的文件作证（r4-MEDIUM-1）。
        if c["stable_id"] not in ok_ids:
            continue
        if not targets[c["stable_id"]].is_file():
            continue  # 节点没建/不在 ⇒ 没有"已派生"可言
        if insert_set is not None:
            if c["stable_id"] in insert_set:
                planned_items.append(c)
            continue
        if _ask_tty(f"为 {c['resolved_name']} 插入「已派生」callout 到 {c['source_anchor']['file']}?"):
            planned_items.append(c)

    # ⛔ 同一文件多条插入按行号**从下往上**做: 上面的插入会顶掉下面的行号。
    by_file: dict[str, list[dict]] = {}
    for c in planned_items:
        by_file.setdefault(c["source_anchor"]["file"], []).append(c)

    inserted = skipped = failed = 0
    for anchor_rel, items in by_file.items():
        items.sort(key=lambda c: c["source_anchor"]["line_start"], reverse=True)
        anchor = _UJ.safe_join(vault, anchor_rel, what="来源锚点")
        for c in items:
            name = c["resolved_name"]
            # ⛔ 窗口内重查来源锚点: 门⑤ 通过之后再被换成 symlink 的话,
            # 读取/备份/写入都会跟随它 —— 每次插入前重验一遍。
            if _UJ.is_symlink(anchor) or not anchor.is_file():
                failed += 1
                print(f"✗ callout 跳过（来源锚点已不是普通文件, 窗口内被换?）: {anchor_rel}", file=sys.stderr)
                continue
            try:
                _SP.assert_symlink_free(anchor)
            except SystemExit as e:
                failed += 1
                print(f"✗ callout 跳过（来源锚点路径含 symlink 组件）: {anchor_rel} ({e})", file=sys.stderr)
                continue
            try:
                raw_bytes = anchor.read_bytes()
                text = raw_bytes.decode("utf-8")
            except (OSError, UnicodeDecodeError) as e:
                failed += 1
                print(f"✗ callout 读取失败: {anchor_rel} ({e})", file=sys.stderr)
                continue
            lines = text.split("\n")
            stripped = _SP.strip_generated(lines)
            comments = _SP.comment_mask(lines, stripped)
            # ⛔ 「已存在」判据与 derived_names_in 同口径: 生成段/代码 fence/HTML 注释
            # 里的字样不算真 callout（过宽判定会把真插入误跳过）。
            present = any(
                not stripped[i]
                and not comments[i]
                and any(m.group(1) == name for m in _SP._DERIVED_CALLOUT.finditer(ln))
                for i, ln in enumerate(lines)
            )
            if present:
                skipped += 1
                print(f"· callout 跳过（已存在同形） {anchor_rel} → [[节点/{name}]]")
                continue
            ls = positions[c["stable_id"]][0]
            if not (0 <= ls <= len(lines)):
                failed += 1
                print(f"✗ callout 行号越界（preview 过期?）: {anchor_rel}:{ls}", file=sys.stderr)
                continue
            # ⛔ 插入行沿用**插入点上一行**的换行风格（往 CRLF 行插 LF 会把局部行尾弄脏）。
            prev_line = lines[ls - 1] if ls - 1 >= 0 else ""
            terminator = "\r" if prev_line.endswith("\r") else ""
            new_text = "\n".join(lines[:ls] + [callout_line(name) + terminator] + lines[ls:])
            try:
                backup_rel, before_sha, before_mtime, before_mode = journal.backup(anchor, anchor_rel)
            except (_UJ.JournalError, OSError) as e:
                failed += 1
                print(f"✗ callout 备份失败, 未插入: {anchor_rel} ({e})", file=sys.stderr)
                continue
            entry = _append_entry(
                journal,
                {
                    "seq": next_seq,
                    "state": STATE_PLANNED,
                    "op": OP_SPLIT_MODIFY,
                    "src": anchor_rel,
                    "dst": anchor_rel,
                    "dst_base": _UJ.BASE_VAULT,
                    "sha256_before": before_sha,
                    "mtime_ns_before": before_mtime,
                    "mode_before": before_mode,
                    "backup": backup_rel,
                    "sha256_planned": sha256_bytes(new_text.encode("utf-8")),
                    "meta": {},
                },
            )
            next_seq += 1
            try:
                _UJ.atomic_write_bytes(anchor, new_text.encode("utf-8"), journal.stale_root, mode=int(before_mode))
            except (_UJ.JournalError, OSError) as e:
                failed += 1
                print(f"✗ callout 写入失败（原文件未动）: {anchor_rel} ({e})", file=sys.stderr)
                continue
            _append_entry(
                journal,
                {
                    **entry,
                    "state": STATE_DONE,
                    "sha256_after": _UJ.sha256_file(anchor),
                    "mtime_ns_after": os.stat(str(anchor), follow_symlinks=False).st_mtime_ns,
                },
            )
            inserted += 1
            print(f"✓ callout 已插入 {anchor_rel}:{ls + 1} → [[节点/{name}]]")
    print(f"总结: callout_inserted={inserted} callout_skipped={skipped} callout_failed={failed}")
    return failed


# ─────────────────────────── undo ───────────────────────────


def _undo_target_chain_ok(vault: Path, p: Path) -> "str | None":
    """撤销动作（删/还原）前验目标父链无 symlink 组件、物理解析仍在 vault 内。"""
    try:
        _SP.assert_symlink_free(p)
    except SystemExit as e:
        return str(e)
    real = Path(os.path.realpath(p))
    vault_real = Path(os.path.realpath(vault))
    if real != vault_real and vault_real not in real.parents:
        return f"物理解析后已不在 vault 内: {real}"
    return None


def _assert_batch_chain_symlink_free(vault: Path, batch: Path) -> None:
    """undo 不跟随 symlink：批次目录链任一环是符号链接就拒绝（账本追加会落到 vault 外）。"""
    for p in (vault, vault / DEFAULT_WORK_PARENT, work_root(vault), batch):
        if _UJ.is_symlink(p):
            die(f"✗ 批次目录链上存在 symlink, 拒绝读写: {p}")
        try:
            _SP.assert_symlink_free(p)
        except SystemExit as e:
            die(f"✗ 批次目录链上含 symlink 组件: {p} ({e})")
    j = batch / _UJ.JOURNAL_NAME
    if _UJ.is_symlink(j):
        die(f"✗ 账本本身是 symlink, 拒绝: {j}")


def run_undo_mode(vault: Path, batch_id: str) -> int:
    """--undo：只删账上记着且 sha256 对得上的自建文件；callout 改过的板从备份还原。"""
    vf = vault_fingerprint(vault)
    work = work_root(vault)
    batch = work / batch_id
    if not (batch / _UJ.JOURNAL_NAME).is_file():
        die(f"✗ 找不到这个批次的账本: {batch / _UJ.JOURNAL_NAME}")
    _assert_batch_chain_symlink_free(vault, batch)
    journal = _UJ.BatchJournal(work, batch_id, root=vault, fingerprint=vf)
    try:
        journal.assert_is_ours(vf)
        rows = journal.load()
        journal._assert_is_a_batch_journal(rows)
        journal._assert_bound_to(rows, vf)
    except _UJ.JournalError as e:
        die(str(e))
    latest = _UJ.latest_by_seq(rows)
    targets = sorted(
        [
            r
            for r in latest.values()
            if r.get("op") in (OP_SPLIT_CREATE, OP_SPLIT_MODIFY) and r.get("state") in (STATE_PLANNED, STATE_DONE)
        ],
        key=lambda r: r.get("seq") or 0,
        reverse=True,
    )

    restored = refused = already = 0
    for r in targets:
        seq = r.get("seq")
        if r["op"] == OP_SPLIT_CREATE:
            try:
                dst = _UJ.safe_join(vault, r.get("dst") or "", what="节点落点")
            except _UJ.JournalError as e:
                refused += 1
                print(f"✗ 拒绝撤销第 {seq} 件（落点形状不可信）: {e}", file=sys.stderr)
                continue
            why = _undo_target_chain_ok(vault, dst)
            if why is not None:
                refused += 1
                print(f"✗ 拒绝删除第 {seq} 件（落点父链含 symlink/越界, 不跟随）: {dst} ({why})", file=sys.stderr)
                continue
            if not os.path.lexists(str(dst)):
                _append_entry(journal, {"seq": seq, "state": STATE_UNDONE, "op": r["op"], "note": "已不在"})
                already += 1
                continue
            if _UJ.is_symlink(dst) or not dst.is_file():
                refused += 1
                print(f"✗ 拒绝删除第 {seq} 件（已不是普通文件）: {dst.relative_to(vault)}", file=sys.stderr)
                continue
            if r.get("state") != STATE_DONE:
                # ⛔ planned（无 done）一律不认领: 账上没有「我们写完过」的证据,
                # 落点上这份东西可能是任何人放的（undo_journal.py 的所有权规则）。
                refused += 1
                print(
                    f"✗ 拒绝删除第 {seq} 件（账上只有 intent 没有 done, 无法证明是自建产物）: {dst.relative_to(vault)}",
                    file=sys.stderr,
                )
                continue
            want = r.get("sha256_after")
            if not want or _UJ.sha256_file(dst) != want:
                refused += 1
                print(
                    f"✗ 拒绝删除第 {seq} 件（执行之后被改动过, 保留不动）: {dst.relative_to(vault)}",
                    file=sys.stderr,
                )
                continue
            os.remove(str(dst))
            _append_entry(journal, {"seq": seq, "state": STATE_UNDONE, "op": r["op"]})
            restored += 1
            print(f"✓ 已删除自建节点 {dst.relative_to(vault)}")
        else:  # OP_SPLIT_MODIFY：从批次备份逐字节还原
            try:
                src = _UJ.safe_join(vault, r.get("src") or "", what="原路径")
            except _UJ.JournalError as e:
                refused += 1
                print(f"✗ 拒绝还原第 {seq} 件（原路径形状不可信）: {e}", file=sys.stderr)
                continue
            why = _undo_target_chain_ok(vault, src)
            if why is not None:
                refused += 1
                print(f"✗ 拒绝还原第 {seq} 件（原路径父链含 symlink/越界, 不跟随）: {src} ({why})", file=sys.stderr)
                continue
            if not os.path.lexists(str(src)) or _UJ.is_symlink(src) or not src.is_file():
                refused += 1
                print(f"✗ 拒绝还原第 {seq} 件（原路径不在或不是普通文件）: {src.relative_to(vault)}", file=sys.stderr)
                continue
            cur = _UJ.sha256_file(src)
            if cur == r.get("sha256_before"):
                _append_entry(journal, {"seq": seq, "state": STATE_UNDONE, "op": r["op"], "note": "已是批前内容"})
                already += 1
                print(f"· 已是批前内容（上次已还原）: {src.relative_to(vault)}")
                continue
            # 本批写下的版本的证据: done 行用实测 sha; 写后/记 done 前中断则用计划 sha
            # （只认 sha256_after 会让这类中断永远无法还原——HIGH-2）。
            ours = r.get("sha256_after") or r.get("sha256_planned")
            if cur != ours:
                refused += 1
                print(
                    f"✗ 拒绝还原第 {seq} 件（板文件在 apply 之后被改过, 覆盖会丢用户的改动）: {src.relative_to(vault)}",
                    file=sys.stderr,
                )
                continue
            try:
                journal._assert_backup_trustworthy(r)
                _UJ.copy_file_atomically(journal.backup_abs(r), src, journal.stale_root)
                journal._finish_restore(r, src)
            except (_UJ.JournalError, OSError) as e:
                refused += 1
                print(f"✗ 拒绝还原第 {seq} 件（备份不可信/还原失败）: {src.relative_to(vault)} ({e})", file=sys.stderr)
                continue
            _append_entry(journal, {"seq": seq, "state": STATE_UNDONE, "op": r["op"]})
            restored += 1
            print(f"✓ 已从批次备份还原 {src.relative_to(vault)}")
    print(f"总结: restored={restored} refused={refused} already_undone={already} · 批次 {batch_id}")
    if refused:
        print(
            "✗ 有件被拒（见上）: 它们保持原状、账上未标 undone —— 处理后可重跑同一条 --undo 重试",
            file=sys.stderr,
        )
    return 1 if refused else 0


# ─────────────────────────── CLI ───────────────────────────


def parse_ids(raw: "str | None", file_path: "str | None") -> list[str]:
    ids: list[str] = []
    if raw:
        ids += [x.strip() for x in raw.split(",") if x.strip()]
    if file_path:
        try:
            for ln in Path(file_path).read_text(encoding="utf-8").split("\n"):
                t = ln.strip()
                if t and not t.startswith("#"):
                    ids.append(t)
        except OSError as e:
            die(f"✗ 读不到 --confirm-file: {file_path} ({e})")
    seen: set[str] = set()
    out: list[str] = []
    for sid in ids:
        if sid not in seen:
            seen.add(sid)
            out.append(sid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="board-split 执行侧（CARD-G5-10）：确认后原子创建派生节点 + 可撤销（scripts-only）"
    )
    ap.add_argument("--vault", required=True, help="vault 根目录")
    ap.add_argument("--preview", default=None, help="split_preview.py 产出的 split-preview-<board>.json")
    ap.add_argument("--confirm", default=None, help="逗号分隔的 stable_id 列表（显式确认）")
    ap.add_argument("--confirm-file", default=None, help="一行一个 stable_id 的确认文件")
    ap.add_argument("--dry-run", action="store_true", help="只出计划不写（二者皆缺时的默认）")
    ap.add_argument("--apply", action="store_true", help="真写：原子创建 + 落账")
    ap.add_argument("--insert-callout", action="store_true", help="可选：向来源文件插「已派生」callout（默认关）")
    ap.add_argument("--confirm-insert", default=None, help="非 TTY 下的逐行确认：逗号分隔 stable_id（缺 = 全跳过）")
    ap.add_argument("--undo", default=None, help="撤销模式：批次 id（在 <vault>/outputs/board-split/ 下）")
    args = ap.parse_args()

    vault = Path(args.vault).resolve()
    if not (vault / "原白板").is_dir():
        die(f"✗ 不是合法 vault（缺 原白板/）: {vault}")

    if args.undo:
        if args.preview or args.confirm or args.confirm_file or args.apply or args.dry_run:
            die("✗ --undo 与 apply/dry-run 参数互斥")
        if not re.fullmatch(r"bs-[0-9a-f]{16}", args.undo):
            die(f"✗ --undo 的批次 id 形状不对（应形如 bs-<16 位十六进制>）: {args.undo!r}")
        return run_undo_mode(vault, args.undo)

    if not args.preview:
        die("✗ 需要 --preview <split-preview-<board>.json>（或用 --undo <batch_id>）")
    if args.apply and args.dry_run:
        die("✗ --apply 与 --dry-run 互斥")
    if args.insert_callout and not args.apply:
        die("✗ --insert-callout 只在 --apply 时有效（dry-run 不写任何文件）")
    confirm_ids = parse_ids(args.confirm, args.confirm_file)
    if not confirm_ids:
        die("✗ 需要 --confirm <stable_id>[,…] 或 --confirm-file（本工具只做「显式确认后创建」）")

    preview_path = Path(args.preview)
    if not preview_path.is_file():
        die(f"✗ 读不到 preview JSON: {preview_path}")
    data = _SP.load_preview_json(preview_path, "apply")
    confirmed, applied, targets, positions = run_gates(vault, data, confirm_ids)

    preview_sha = _UJ.sha256_file(preview_path)
    batch_id = (
        "bs-"
        + hashlib.sha256(
            ("split-apply/v1\x00" + preview_sha + "\x00" + ",".join(sorted(confirm_ids))).encode("utf-8")
        ).hexdigest()[:16]
    )
    shared_meta = {
        "preview": preview_display_path(vault, preview_path),
        "preview_sha256": preview_sha,
        "board": data["board"],
        "created_at": _UJ.utc_now_iso(),
    }

    insert_ids: "list[str] | None" = None
    if args.insert_callout and args.confirm_insert is not None:
        insert_ids = [x.strip() for x in args.confirm_insert.split(",") if x.strip()]
        known = {c["stable_id"] for c in confirmed}
        unknown = [sid for sid in insert_ids if sid not in known]
        if unknown:
            die(f"✗ --confirm-insert 的 stable_id 不在本批 --confirm 里: {', '.join(unknown)}")

    if not args.apply:
        print("dry-run 计划（不写任何文件）:")
        applied_ids = {c["stable_id"] for c in applied}
        for c in confirmed:
            rel = f"节点/{c['resolved_name']}.md"
            if c["stable_id"] in applied_ids:
                print(f"  · 跳过（已应用） {rel}")
            else:
                print(f"  · 将创建 {rel} ← {c['source_anchor']['file']}:{positions[c['stable_id']][0]}")
        print(f"计划完毕: 将创建 {len(confirmed) - len(applied)} 件, 跳过 {len(applied)} 件。（dry-run, 未写任何文件）")
        return 0

    failed, ok_ids = run_create(vault, data, confirmed, applied, targets, positions, batch_id, shared_meta)
    if args.insert_callout:
        failed += run_callout_insert(vault, data, confirmed, targets, positions, ok_ids, batch_id, insert_ids)
    if failed:
        print(f"✗ 有 {failed} 件失败（见上）", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
