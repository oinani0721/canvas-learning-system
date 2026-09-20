#!/usr/bin/env python3
"""待处理清仓 —— 执行侧 (CARD-G5-7, scripts-only, 无 SKILL.md)。

输入 = G5-6 只读 preview 的 JSON 产物 + 用户逐条拍板的 decisions；
输出 = 按拍板把材料 copy / link / move / 移入回收目录 / 留原地, 并落一本可撤销的账。

    inbox_apply.py --vault <V> --preview <inbox-preview-*.json> --decisions <d.json>
    inbox_apply.py --vault <V> --undo <…/journal.jsonl>

decisions 形态 (schema_version = 1):
    {"schema_version": 1, "decisions": [
      {"stable_id": "inb1-…", "action": "copy|link|move|recycle|skip",
       "target": "<vault 内相对目录>", "confirm": true}
    ]}

⛔ 四条不肯让步的事:

1. **默认路径 0 物理删除。**「删」在本脚本里只有一个含义 —— 移进
   `<work-dir>/<batch_id>/recycle/` 留痕, 且必须 `--confirm-recycle`(整批) **且**
   该条 `confirm: true`(逐件) 双重显式确认, 缺一即**整批拒绝、零写**。本文件与
   undo_journal.py 内零 os.remove / os.unlink / Path.unlink / shutil.rmtree /
   os.rmdir / send2trash (AST 门 F2 常驻 backend/tests/skills/test_g5_7_inbox_apply.py)。

2. **不覆盖不属于自己的东西。**「零删除原语」不等于「不会覆盖」——`os.replace` 与
   `copyfile` 都能在不调用任何删除原语的情况下把既有内容换掉。所以每个落点在落笔前
   都要先证明**归本批次所有**: 不存在, 或者是自己上一次跑留下的 (按 sha 或自带的
   批次溯源印记认)。只看「路径在账上」是不够的 —— 中断之后用户完全可能在那个路径上
   放了自己的新文件。

3. **准入次序铁律**: 全部守卫跑完**再**碰 work-dir —— 拒绝路径连 `outputs/` 这一级
   都不许被建出来 (口径抄 inbox_preview.py:2425-2455)。

4. **不报含糊的完成。** 任一件失败即 rc≠0, 回执写明「第几件 / 哪一件 / 为什么 /
   账在哪 / 已完成几件」; 同输入重跑落同一本账, 只补未完成的那几件。

数据面只消费 preview 的 `stable_id` / `rel_path` / `size_bytes` / `mtime_utc` /
`label` 这些**机械字段**; 提名理由一类经过裸 .strip() 的自由文本一概不进写侧
(AST 门 F4)。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat as stat_mod
import sys
from pathlib import Path

SCHEMA_VERSION = 1
GENERATOR = "clear-inbox/inbox_apply.py v1.1 (CARD-G5-7 执行侧)"

_HERE = Path(__file__).resolve()
_PREVIEW_PATH = _HERE.parent / "inbox_preview.py"
_JOURNAL_PATH = _HERE.parents[3] / "scripts" / "undo_journal.py"


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


_IP = _load_sibling(
    _PREVIEW_PATH,
    "_g57_inbox_preview",
    "时刻格式 / 身份键编码必须与产出 preview 的那个引擎同源, 手抄一份必然漂移",
)
_UJ = _load_sibling(
    _JOURNAL_PATH,
    "_g57_undo_journal",
    "备份 / 账本 / 撤销是共用模块, 本脚本不自带第二份实现",
)
_SP = _IP._SP  # 祖先链 symlink 守卫的单一真相源 (split_preview)

# ───────────────────────────────── 常量 ─────────────────────────────────

#: 缺省工作目录。`outputs` 在 preview 的语料排除集 (inbox_preview.py:327), 且不在
#: 收件箱内 —— 于是本脚本的产物不会在下一次 preview 里被当成待处理材料盘点回来。
DEFAULT_WORK_PARENT = "outputs"
DEFAULT_WORK_NAME = "clear-inbox"

A_COPY = "copy"
A_LINK = "link"
A_MOVE = "move"
A_RECYCLE = "recycle"
A_SKIP = "skip"
ACTIONS = (A_COPY, A_LINK, A_MOVE, A_RECYCLE, A_SKIP)

#: 需要落点目录的动作。recycle 的落点由本脚本定 (回收目录), skip 没有落点。
ACTIONS_NEEDING_TARGET = (A_COPY, A_LINK, A_MOVE)
#: 会把源从原路径拿走的动作 —— 重跑对账时「源不在了」对它们是正常的。
ACTIONS_TAKE_SOURCE = (A_MOVE, A_RECYCLE)
#: 会产出一份「本批次新造的 md」的动作 —— 只有它们写溯源 frontmatter。
#: link 与原件同 inode, 写溯源等于改原件, 所以不在此列。
ACTIONS_WITH_PROVENANCE = (A_COPY, A_MOVE)

#: 落点首段黑名单: 配置目录 / 产物目录不是放学习材料的地方。
FORBIDDEN_FIRST_SEGMENTS = frozenset({".claude", ".obsidian", DEFAULT_WORK_PARENT})

RECEIPT_STEM = "receipt"
UNDO_RECEIPT_STEM = "undo-receipt"


def sha256_file(path) -> str:
    return _UJ.sha256_file(path)


def die(msg: str):
    raise SystemExit(msg if msg.startswith("✗") else f"✗ {msg}")


# ───────────────────────── 输入读取 ─────────────────────────


def load_json_file(path: Path, what: str) -> tuple[dict, str]:
    """返回 (解析结果, 文件 sha256)。sha 进 batch_id —— 同输入同批次。"""
    if path.is_symlink():
        die(f"{what} 本身是 symlink, 拒绝读取: {path}")
    if not path.is_file():
        die(f"{what} 不存在或不是普通文件: {path}")
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        die(f"{what} 不是合法 UTF-8 JSON: {path} ({e})")
    if not isinstance(data, dict):
        die(f"{what} 顶层必须是对象: {path}")
    if data.get("schema_version") != SCHEMA_VERSION:
        die(
            f"{what} 的 schema_version 不是 {SCHEMA_VERSION} "
            f"(实得 {data.get('schema_version')!r}), 拒绝按未知契约执行: {path}"
        )
    return data, hashlib.sha256(raw).hexdigest()


def compute_vault_fingerprint(vault: Path) -> str:
    """与 inbox_preview.py:2157-2158 同式。两边一致性由行为门证明:
    真跑 preview 产出的指纹必须被接受, 换一个 vault 的必须被拒。"""
    return "vf1-" + hashlib.sha256(os.path.realpath(vault).encode("utf-8")).hexdigest()[:16]


def resolve_vault(raw: str) -> Path:
    vault = Path(raw)
    if vault.is_symlink():
        die(f"vault 路径本身是 symlink, 拒绝越界写入: {vault}")
    if not vault.is_dir():
        die(f"vault 不存在或不是目录: {vault}")
    return vault.resolve()


def resolve_work_dir(vault: Path, raw: str | None) -> Path:
    """只做词法与边界判定, **不创建任何目录**。"""
    if raw is None:
        return vault / DEFAULT_WORK_PARENT / DEFAULT_WORK_NAME
    work = Path(raw)
    if not work.is_absolute():
        work = vault / work
    real = Path(os.path.realpath(work))
    vault_real = Path(os.path.realpath(vault))
    if real != vault_real and vault_real not in real.parents:
        die(f"--work-dir 必须落在 vault 内, 拒绝越界: {work}")
    return work


def assert_work_dir_outside_inbox(vault: Path, work_dir: Path, inbox_name: str) -> None:
    """工作目录不能落在收件箱里 —— 备份与回收件落进**正在清理的那个目录**,
    下一次盘点会把它们当噪音扫进来, 而「删掉的东西」就躺在你要清空的地方。"""
    real = Path(os.path.realpath(work_dir))
    inbox_real = Path(os.path.realpath(vault / inbox_name))
    if real == inbox_real or inbox_real in real.parents:
        die(f"--work-dir 落在收件箱内 ({real}), 拒绝: 备份与回收件不能放进要清理的那个目录")


# ───────────────────────── 准入守卫 ─────────────────────────


def _path_is_within(real, anchor) -> bool:
    """`real` 是不是就是 `anchor`、或落在它下面 —— **大小写不敏感**地判。

    ⛔ macOS 默认卷 (APFS/HFS+) 大小写不敏感, 而 `os.path.realpath` **不做**大小写
    规范化: `realpath('<v>/.Claude')` 原样返回 `.Claude`, 但它和 `.claude` 是同一个
    目录（`lexists` / `is_dir` 对它都为真）。于是纯字符串比较整条失效 —— 把 target
    首段换一个字母的大小写, 三道边界判据一起落空, 学习材料被写进 `.claude/`（本工具
    自己的脚本就在这棵树下）/ `.obsidian/` / `outputs/`（全卡复核 HIGH-F 实测）。

    先用 `samefile` 问文件系统（两端都存在时这是权威答案）, 问不出来再退回逐段
    casefold 比较 —— 后者对「落点还不存在」的常态也成立。
    """
    try:
        if os.path.exists(real) and os.path.exists(anchor) and os.path.samefile(str(real), str(anchor)):
            return True
    except OSError:
        pass
    r = [p.casefold() for p in Path(real).parts]
    a = [p.casefold() for p in Path(anchor).parts]
    return len(r) >= len(a) and r[: len(a)] == a


def validate_target(vault: Path, inbox_name: str, work_dir: Path, raw) -> Path:
    """落点目录白名单。⛔ 先词法后物理: `..` 与绝对路径在词法层就拒掉, 再用 realpath
    判边界 —— 只做词法判定会被祖先 symlink 绕过 (O_NOFOLLOW 只管末段)。"""
    if not isinstance(raw, str) or not raw.strip("/"):
        die(f"target 必须是非空的 vault 内相对目录, 实得 {raw!r}")
    cand = Path(raw)
    if cand.is_absolute():
        die(f"target 必须是相对目录, 不接受绝对路径: {raw!r}")
    parts = cand.parts
    # ⛔ `Path(".").parts` 与 `Path("./").parts` 都是**空元组**（pathlib 把纯 `.` 规范化
    # 掉了）, 而上面的 `raw.strip("/")` 判非空放行了它 —— 于是下面取 `parts[0]` 抛裸
    # IndexError, 逃出本文件承诺的 `die()` 统一出口（全卡复核 L3/L6）。
    if not parts:
        die(f"target 指的是 vault 根本身, 那不是放学习材料的地方: {raw!r}")
    if any(part == ".." for part in parts):
        die(f"target 含 `..`, 拒绝越界: {raw!r}")
    # ⛔ casefold 比较: 大小写不敏感卷上 `.Claude` 和 `.claude` 是同一个目录。
    head = parts[0].casefold()
    if head in {s.casefold() for s in FORBIDDEN_FIRST_SEGMENTS}:
        die(f"target 首段 {parts[0]!r} 是配置/产物目录, 不是放学习材料的地方: {raw!r}")
    if head == inbox_name.casefold():
        die(f"target 指回收件箱本身, 那不叫清仓: {raw!r}")

    dst_dir = vault / cand
    real = Path(os.path.realpath(dst_dir))
    vault_real = Path(os.path.realpath(vault))
    if not _path_is_within(real, vault_real):
        die(f"target 解析后落在 vault 之外 ({real}), 拒绝越界: {raw!r}")
    inbox_real = Path(os.path.realpath(vault / inbox_name))
    if _path_is_within(real, inbox_real):
        die(f"target 解析后落在收件箱内 ({real}), 拒绝: {raw!r}")
    work_real = Path(os.path.realpath(work_dir))
    if _path_is_within(real, work_real):
        die(f"target 解析后落在工作目录内 ({real}), 拒绝: {raw!r}")
    # 祖先链无 symlink —— 词法上在 vault 内的写会被祖先 symlink 重定向到别处
    _SP.assert_symlink_free(dst_dir)
    return dst_dir


def source_path(vault: Path, item: dict, inbox_name: str) -> Path:
    """源路径 + 形状校验 + 祖先链守卫。

    ⛔ `rel_path` 是从 preview 的 JSON 里读出来的, 而那份 JSON 用户改得动。不校验
    形状就直接拼路径, 一条 `../outside.md` 就能让执行侧去搬 vault 外的文件（备份
    落点仍在批次目录内, 看上去一切正常）。preview 自己产出的形状恒是
    `<收件箱名>/<文件名>` 两段 (inbox_preview.py:1963-1978), 这里照这个形状卡死。

    ⛔ 只查末段也是不够的: 把整个收件箱挪到 vault 外再用一条 symlink 接回来, 末段
    (那个 .md) 仍是普通文件, 而读写全都发生在 vault 之外 —— 所以还要查祖先链。
    """
    rel = item.get("rel_path")
    if not isinstance(rel, str) or not rel:
        die(f"preview 条目缺少 rel_path 或格式不对: {rel!r}")
    cand = Path(rel)
    if cand.is_absolute() or any(part == ".." for part in cand.parts):
        die(f"preview 条目的 rel_path 不是 vault 内的相对路径, 拒绝: {rel!r}")
    parts = cand.parts
    if len(parts) != 2 or parts[0] != inbox_name:
        die(f"preview 条目的 rel_path 形状不对 (应为 <{inbox_name}>/<文件名>): {rel!r}")
    if parts[1] != item.get("name"):
        die(f"preview 条目的 rel_path 与 name 对不上 ({parts[1]!r} ≠ {item.get('name')!r})")

    src = vault / cand
    inbox_real = Path(os.path.realpath(vault / inbox_name))
    if Path(os.path.realpath(src)).parent != inbox_real:
        die(f"preview 条目解析后不在收件箱内, 拒绝: {rel!r}")
    _SP.assert_symlink_free(src.parent)
    return src


def check_source_fresh(src: Path, item: dict):
    """源材料必须仍与 preview 记录的那一份**逐项**对得上。"""
    rel = item["rel_path"]
    try:
        st = os.lstat(str(src))
    except OSError as e:
        die(f"源材料已不在原处, preview 已过期, 请重跑 preview: {rel} ({e.strerror})")
    if stat_mod.S_ISLNK(st.st_mode):
        die(f"源材料现在是一条 symlink, 拒绝跟随 (可能指向 vault 外): {rel}")
    if not stat_mod.S_ISREG(st.st_mode):
        die(f"源材料不是普通文件, 拒绝搬动: {rel}")
    if st.st_size != item["size_bytes"]:
        die(f"源材料大小与 preview 不符 ({st.st_size} ≠ {item['size_bytes']}), preview 已过期, 请重跑 preview: {rel}")
    actual_mtime = _IP.fmt_utc(st.st_mtime)
    if actual_mtime != item["mtime_utc"]:
        die(
            f"源材料修改时间与 preview 不符 ({actual_mtime} ≠ {item['mtime_utc']}), "
            f"preview 已过期, 请重跑 preview: {rel}"
        )
    return st


def compute_batch_id(fingerprint: str, preview_sha: str, decisions_sha: str) -> str:
    """同 vault + 同 preview + 同拍板 ⇒ 同一本账 ⇒ 中断重跑幂等。

    换了 --now 重跑 preview ⇒ JSON 字节变 ⇒ 这是**另一个批次**, 会在落点归属守卫
    (copy/link/move) 或源材料新鲜度守卫 (move/recycle 的源已被上一批拿走) 上被拦下,
    而不是默默再做一遍。
    """
    raw = "\n".join([fingerprint, preview_sha, decisions_sha]).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def build_plans(vault, work_dir, preview, decisions, confirm_recycle, journal, rows):
    """把拍板翻译成逐条执行计划。任何一条不过关 ⇒ 整批拒绝、零写。

    `rows` 是本批次账本的既有记录 (只读地读来的)。有它才分得清两种「源不在了」:
    上一次已经把它合法搬走了 (该跳过 / 该续跑), 还是 preview 过期了 (该拒绝)。
    没有这一层, move/recycle 做成之后重跑会**恒**卡在新鲜度守卫上, 幂等根本走不到。
    """
    label = preview.get("label")
    if not isinstance(label, str) or not label:
        die("preview 缺少 label (收件箱目录名), 拒绝执行")
    items = {}
    for it in preview.get("items", []):
        items[it["stable_id"]] = it
    if not items:
        die("preview 里没有任何条目, 没有可执行的事")

    raw_list = decisions.get("decisions")
    if not isinstance(raw_list, list) or not raw_list:
        die("decisions 必须是非空列表")

    # ⛔ 取每个 seq 的**最新**状态。按「出现过 done」判的话, 撤销之后重新执行的
    # 那一轮会被当成「上次已完成」直接跳过, 于是什么都没做却报完成。
    latest = _UJ.latest_by_seq(rows)
    done_by_seq = {k: r for k, r in latest.items() if r.get("state") == _UJ.STATE_DONE}
    #: 已排期但还没记完的 —— planned（没动过盘）与 acting（动过盘了）两种。
    open_by_seq = {k: r for k, r in latest.items() if r.get("state") in (_UJ.STATE_PLANNED, _UJ.STATE_ACTING)}

    plans = []
    seen = set()
    for idx, d in enumerate(raw_list, start=1):
        if not isinstance(d, dict):
            die(f"第 {idx} 条拍板不是对象: {d!r}")
        sid = d.get("stable_id")
        if sid not in items:
            die(f"第 {idx} 条拍板的 stable_id 不在这份 preview 里 (可能拿错了盘点单): {sid!r}")
        if sid in seen:
            die(f"第 {idx} 条拍板的 stable_id 重复出现, 一件材料只能有一个去向: {sid!r}")
        seen.add(sid)

        action = d.get("action")
        if action not in ACTIONS:
            die(f"第 {idx} 条拍板的 action 未知 (只认 {'/'.join(ACTIONS)}): {action!r}")

        prior = done_by_seq.get(idx) or open_by_seq.get(idx)
        if prior is not None and prior.get("stable_id") not in (None, sid):
            die(f"第 {idx} 条拍板与账上第 {idx} 条对不上 (账 {prior.get('stable_id')!r} ≠ 拍板 {sid!r})")

        item = items[sid]
        src = source_path(vault, item, label)

        target_raw = d.get("target")
        if action in ACTIONS_NEEDING_TARGET:
            dst_dir = validate_target(vault, label, work_dir, target_raw)
            dst = dst_dir / item["name"]
            dst_base = _UJ.BASE_VAULT
            dst_rel = str(dst.relative_to(vault))
        else:
            if target_raw not in (None, ""):
                die(f"第 {idx} 条拍板的 action={action} 不该带 target, 实得 {target_raw!r}")
            if action == A_RECYCLE:
                dst_rel = f"{_UJ.RECYCLE_DIR}/{item['rel_path']}"
                dst = journal.batch_dir / dst_rel
                dst_base = _UJ.BASE_BATCH
            else:
                dst, dst_base, dst_rel = None, _UJ.BASE_BATCH, ""

        if action == A_RECYCLE:
            # ⛔ 双重显式确认: 整批 flag 与逐件 confirm 缺一不可, 且 confirm 必须是
            # **布尔真** —— 认「真值」的话, "no" / 0.0 之外的任何东西都能蒙混过关。
            if not confirm_recycle:
                die(
                    f"第 {idx} 条要移入回收目录, 但没有给 --confirm-recycle, 整批拒绝、未动任何文件: {item['rel_path']}"
                )
            if d.get("confirm") is not True:
                die(
                    f"第 {idx} 条要移入回收目录, 但该条的 confirm 不是 true "
                    f"(实得 {d.get('confirm')!r}), 整批拒绝、未动任何文件: {item['rel_path']}"
                )

        settled = idx in done_by_seq
        # 已动盘但还没记 done 的取源动作: 源不在、落点在 ⇒ 这是中断点, 不是 preview 过期
        # ⛔ 只有 **acting**（确实动过盘）才算「源不在是正常的」。planned 只是排了期,
        # 那时源必须还在原处, 否则就是 preview 过期。
        resumable = (
            not settled
            and open_by_seq.get(idx, {}).get("state") == _UJ.STATE_ACTING
            and action in ACTIONS_TAKE_SOURCE
            and not os.path.lexists(str(src))
            and dst is not None
            and os.path.lexists(str(dst))
        )
        st = None
        if not (settled or resumable):
            st = check_source_fresh(src, item)
            prior_open = open_by_seq.get(idx)
            if prior_open is not None and prior_open.get("sha256_before"):
                # ⛔ 账上已经有这一件的 sha 了, 复用旧记录时就该拿它核, 而不是再信
                # 一次「大小 + 秒级 mtime」那个粗判据 —— 等长改写并保持 mtime 就能
                # 穿过去, 然后撤销会拿旧内容把新内容盖掉 (Codex round-4 H1)。
                actual = sha256_file(src)
                if actual != prior_open["sha256_before"]:
                    die(
                        f"第 {idx} 条的源材料在排期之后被改动过 (当前 {actual[:12]}… ≠ 账上 "
                        f"{prior_open['sha256_before'][:12]}…), 续跑会让账与实盘对不上, "
                        f"拒绝: {item['rel_path']}（请重跑 preview 另起一批）"
                    )

        plans.append(
            {
                "seq": idx,
                "action": action,
                "stable_id": sid,
                "name": item["name"],
                "src_rel": item["rel_path"],
                "src_abs": src,
                "dst_abs": dst,
                "dst_base": dst_base,
                "dst_rel": dst_rel,
                "mtime_utc": item["mtime_utc"],
                "size_bytes": item["size_bytes"],
                "st": st,
                "settled": settled,
                "resumable": resumable,
            }
        )
    return plans


def check_destinations_free(plans, journal, rows) -> None:
    """落点归属守卫 —— 「覆写幂等」的安全前提, 对**每一个**动作都要过。

    执行时 copy 是覆写式的、move/recycle 是 os.replace 式的 (才幂等), 所以必须先证明
    每个落点要么空着, 要么**确实是本批次自己**先前造出来的。少了这一条, 一次重跑就
    能悄悄盖掉用户的同名文件 —— 而「路径在账上」证明不了这件事: 中断之后用户完全
    可能在那个路径上放了自己的东西。回收目录同样要过这道门, 它不是法外之地。
    """
    # ⛔ acting 必须收进来。加新状态时只改了「最新状态」与撤销侧, 漏了这里 ——
    # 于是主动作做完、done 还没落账时重跑, 自家产物会被判成外来文件而拒绝
    # (Codex round-4 H4)。加一个状态就得把**所有读这个状态机的地方**列一遍。
    by_seq = {
        k: r
        for k, r in _UJ.latest_by_seq(rows).items()
        if r.get("state") in (_UJ.STATE_PLANNED, _UJ.STATE_ACTING, _UJ.STATE_DONE)
    }
    for p in plans:
        dst = p["dst_abs"]
        if p["action"] == A_SKIP or dst is None:
            continue
        if p.get("settled"):
            # ⛔ 账上已 done 的那几件交给 `verify_done` —— 它对同一个输入给的是
            # 「账上说第 N 件已完成, 但落点内容已被改动 (…≠…)」, 而这里无差别跑归属守卫
            # 会先撞上「不是本批次造的, 先自己处理掉那份同名文件」。后者对「用户编辑过
            # 自己已经搬过去的那份笔记」这个**完全正常**的行为是错的诊断, 而且会把后面
            # 没补完的那几件永远堵死（全卡复核 M15 实测）。两道门触发条件重合时，
            # 要让**诊断更准**的那一道先说话。
            continue
        if not os.path.lexists(str(dst)):
            continue
        if _UJ.is_symlink(dst):
            die(f"第 {p['seq']} 件的落点是一条 symlink, 拒绝跟随: {p['dst_rel']}")
        row = by_seq.get(p["seq"])
        if row is not None and row.get("dst") == p["dst_rel"] and row.get("dst_base") == p["dst_base"]:
            if journal.owned_product(dst, row):
                continue  # 是自家上一次跑留下的产物
        die(
            f"第 {p['seq']} 件的落点已经有东西了, 而且它不是本批次造的, 不会覆盖它: "
            f"{p['dst_rel']}（先改个落点, 或自己处理掉那份同名文件）"
        )


# ───────────────────────── 执行 ─────────────────────────


def _provenance_meta(plan, batch_id: str, applied_at: str) -> dict:
    return {
        "source_rel_path": plan["src_rel"],
        "source_mtime_utc": plan["mtime_utc"],
        "batch_id": batch_id,
        "applied_at_utc": applied_at,
        "op": plan["action"],
    }


def _dir_chain_for_mtime(vault: Path, d: Path) -> list:
    """`d` 自己 + 它**尚不存在的那几级的父目录**里最深的那个已存在祖先。

    ⛔ 落点目录是本次新建的（`归档/2026`）时, 被改动条目集合的其实是它的**父目录**
    `归档` —— 而 `归档` 从来没进过任何一条账目行, 于是撤销既不会还原它的 mtime,
    也不会把它登进 `dirs_not_retimed`。回执的「目录时间」一节自称完整, 却漏了它
    （全卡复核 L13）。
    """
    out = [d]
    cur = Path(d)
    while not cur.exists() and cur != cur.parent:
        cur = cur.parent
        out.append(cur)
    return out


def touched_dir_mtimes(vault: Path, plan) -> dict:
    """本条会改动条目集合的那几个 vault 内目录, 连同它们此刻的 mtime。"""
    out: dict = {}
    if plan["action"] == A_SKIP:
        return out
    cands = [plan["src_abs"].parent]
    if plan["dst_base"] == _UJ.BASE_VAULT and plan["dst_abs"] is not None:
        # ⛔ 落点目录若是本次新建的, 被改动条目集合的是它**最深的那个已存在祖先**;
        # 不收进来的话那个祖先既不会被还原、也不会被登进 dirs_not_retimed（L13）。
        cands.extend(_dir_chain_for_mtime(vault, plan["dst_abs"].parent))
    for d in cands:
        try:
            rel = str(d.relative_to(vault))
        except ValueError:
            continue  # 不在 vault 内 (回收目录等) —— 不是要还原的面
        if d.is_dir() and not _UJ.is_symlink(d):
            out[rel] = d.stat().st_mtime_ns
    return out


def missing_dirs(vault: Path, target: Path) -> list:
    """target 这一路上还不存在、本次会被建出来的目录 (vault 相对)。

    撤销**不会**删掉它们 (默认路径 0 物理删除), 所以必须记下来在回执里说出口 ——
    否则「撤销后全树回到原样」这句话会在这一点上悄悄失真。
    """
    out = []
    cur = Path(target)
    while True:
        try:
            rel = str(cur.relative_to(vault))
        except ValueError:
            break
        if os.path.lexists(str(cur)):
            break
        out.append(rel)
        cur = cur.parent
    return list(reversed(out))


def perform(plan, entry, journal, batch_id: str, applied_at: str):
    """做一件。每一步都写成可重入的: 重跑落到同一结果, 不叠加副作用。"""
    action = plan["action"]
    if action == A_SKIP:
        return None, None, None, None

    src, dst = plan["src_abs"], plan["dst_abs"]
    if plan["dst_base"] == _UJ.BASE_VAULT:
        journal.mkdir_chain(dst.parent)
    else:
        os.makedirs(str(dst.parent), exist_ok=True)
    _SP.assert_symlink_free(dst.parent)

    if action == A_COPY:
        # ⛔ 不直接 copyfile: 它先截断再写, 中途失败留下的半截文件既不等于 before
        # 也不等于 after, 归属判定两边都不认 = 重试时只能拒绝 (Codex round-3 H8)。
        _UJ.copy_file_atomically(src, dst, journal.stale_root)
    elif action == A_LINK:
        if os.path.lexists(str(dst)):
            if os.stat(str(dst)).st_ino == os.stat(str(src)).st_ino:
                pass  # 上一次已经链好, 只是没来得及记账
            else:
                # 半态残留: 挪进 stale/ 留痕, 不做物理删除。
                # ⛔ 走带守卫的 park_into_stale, 不是裸 makedirs+replace —— 后者是全卡
                # 唯一一处不查 stale/ 是否 symlink 的搬动, 而搬的是**用户的文件**:
                # stale/ 指向 vault 外时它会被无声搬出去而工具报 ✓ 完成
                # （全卡复核 HIGH-G）。落点还要记进账, 否则「它去哪了」无处可查。
                parked = _UJ.park_into_stale(dst, journal.stale_root, what="link 半态残留")
                entry["link_parked"] = str(parked)
                print(f"⚠ 落点上原有一份不是本批次造的文件, 已挪到 {parked} 留痕", file=sys.stderr)
                os.link(str(src), str(dst))
        else:
            os.link(str(src), str(dst))
    elif action in (A_MOVE, A_RECYCLE):
        if os.path.lexists(str(src)):
            os.replace(str(src), str(dst))
        elif not os.path.lexists(str(dst)):
            raise OSError(f"源与落点都不存在, 不猜它去哪了: {plan['src_rel']}（备份在 {entry.get('backup')}）")
        # src 不在而 dst 在 = 上一次的 os.replace 已原子完成, 从下面的收尾续跑

    provenance = None
    if action in ACTIONS_WITH_PROVENANCE:
        # ⛔ 用**账上那份** prov_meta。续跑时本次的 applied_at 与排期那次不同, 拿新的
        # 重算会写出与账上期望不符的字节, 于是下一次连自己刚写的产物都不认
        # (Codex round-3 H6)。账里记的才是这一步的唯一期望。
        meta = entry.get("prov_meta") or _provenance_meta(plan, batch_id, applied_at)
        provenance = _UJ.write_provenance(dst, meta, journal.stale_root)
    mode = entry.get("mode_before")
    if mode is not None:
        os.chmod(str(dst), stat_mod.S_IMODE(int(mode)))
    ns = int(entry["mtime_ns_before"])
    os.utime(str(dst), ns=(ns, ns))
    st = os.stat(str(dst))
    return sha256_file(dst), st.st_mtime_ns, provenance, st.st_ino


def verify_done(plan, row, vault: Path, journal) -> None:
    """复核一条已记 done 的账是否与实盘相符。对不上就停下 —— 世界在两次跑之间被改过,
    盲目重做可能把用户已经手工整理过的东西再搬一次。"""
    action = plan["action"]
    if action == A_SKIP:
        return
    dst = journal.dst_abs(row, vault)
    if not os.path.lexists(str(dst)):
        die(f"账上说第 {plan['seq']} 件已完成, 但落点已不在: {dst}（请检查后重跑 preview）")
    if _UJ.is_symlink(dst):
        die(f"账上说第 {plan['seq']} 件已完成, 但落点现在是一条 symlink: {dst}")
    actual = sha256_file(dst)
    if actual != row.get("sha256_after"):
        die(
            f"账上说第 {plan['seq']} 件已完成, 但落点内容已被改动 "
            f"({actual[:12]}… ≠ {str(row.get('sha256_after'))[:12]}…): {dst}"
        )
    if action in ACTIONS_TAKE_SOURCE and os.path.lexists(str(plan["src_abs"])):
        die(f"账上说第 {plan['seq']} 件已搬走, 但原路径又有东西了: {plan['src_rel']}")
    if action == A_LINK:
        # ⛔ 硬链接的「完成」是一种**关系**, 不是一份内容: 只验落点内容的话, 原件被
        # 换成另一个文件之后这条关系早断了, 却还会报完成。
        src = plan["src_abs"]
        if _UJ.is_symlink(src) or not src.is_file():
            die(f"账上说第 {plan['seq']} 件已硬链接, 但原路径已不是普通文件: {plan['src_rel']}")
        if os.stat(str(src)).st_ino != os.stat(str(dst)).st_ino:
            die(f"账上说第 {plan['seq']} 件已硬链接, 但它和原件已不是同一份了: {plan['src_rel']}")


def render_receipt_md(data: dict) -> str:
    lines = [
        f"# 清仓回执 · 批次 {data['batch_id']}",
        "",
        f"- 结果: {'全部完成' if data['ok'] else '中途停下'}",
        f"- 共 {data['total']} 件, 已完成 {data['completed']} 件",
        f"- 账本: `{data['journal']}`",
        f"- 时刻(UTC): {data['applied_at_utc']}",
        "",
    ]
    if not data["ok"] and data.get("failed"):
        f = data["failed"]
        lines += [
            "## 停在哪一件",
            "",
            f"- 第 {f['index']} 件 · `{f['src']}` · 动作 {f['op']}",
            f"- 原因: {f['reason']}",
            "",
            "前面已完成的那几件都记在账上了; 修好原因后**用同一份 preview 与同一份拍板**重跑, 它只会补做没做完的。",
            "",
        ]
    lines += ["## 逐件", "", "| # | 动作 | 材料 | 去处 | 溯源 |", "|---|---|---|---|---|"]
    for r in data["results"]:
        lines.append(f"| {r['index']} | {r['op']} | `{r['src']}` | `{r['dst'] or '—'}` | {r['provenance'] or '—'} |")
    if data.get("created_dirs"):
        lines += [
            "",
            "## 本次新建的目录",
            "",
            "撤销**不会**删掉它们（本工具默认路径上没有物理删除）, 撤销后会留成空目录:",
            "",
        ]
        lines += [f"- `{d}`" for d in data["created_dirs"]]
    if data.get("dirs_retimed") is not None:
        lines += ["", "## 目录时间", "", f"- 已还原: {data['dirs_retimed'] or '无'}"]
        for item in data.get("dirs_not_retimed") or []:
            lines.append(f"- 未还原 `{item['dir']}`: {item['why']}")
    lines += ["", f"> {data['note']}", ""]
    return "\n".join(lines)


def write_receipt(journal, data: dict, stem: str) -> None:
    """写两份回执。落点若已有东西, 只有「与账上记的上一版 sha 相同」才算自家产物,
    否则先挪进 stale/ 留痕 —— 判据是可计算的等式, 不是子串启发式（独立复核 H-1）。"""
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    md = render_receipt_md(data).encode("utf-8")
    items = [
        (journal.batch_dir / f"{stem}.json", payload),
        (journal.batch_dir / f"{stem}.md", md),
    ]
    try:
        prior = journal.recorded_receipt_shas(journal.read_rows(), stem)
    except (OSError, _UJ.JournalError):
        prior = {}
    _UJ.write_pair_atomically(items, journal.stale_root, owned_shas=prior)
    journal.record_receipt_shas(stem, {str(path): hashlib.sha256(blob).hexdigest() for path, blob in items})


def _do_one(plan, entry, journal, vault: Path, batch_id: str, applied_at: str, created_dirs: list):
    """做一件的全部动作: 备份 → plan → acting → perform → commit。

    ⛔ 整段都要能被调用方的失败处理接住。此前只有 perform 在 try 里, 于是 backup /
    记账 这几步一旦失败就是直接抛出去 —— 前面已完成的那几件没有回执, 「不报含糊的
    完成」这条承诺在这条路径上落空 (Codex round-4 M3)。
    """
    seq = plan["seq"]
    if entry is None:
        if plan["action"] == A_SKIP:
            backup_rel, sha_before, mtime_ns_before, mode_before = (
                None,
                sha256_file(plan["src_abs"]),
                plan["st"].st_mtime_ns,
                plan["st"].st_mode,
            )
        else:
            backup_rel, sha_before, mtime_ns_before, mode_before = journal.backup(plan["src_abs"], plan["src_rel"])
        if plan["dst_abs"] is None or plan["dst_base"] != _UJ.BASE_VAULT:
            new_dirs = []
        else:
            new_dirs = missing_dirs(vault, plan["dst_abs"].parent)
        created_dirs += [d for d in new_dirs if d not in created_dirs]
        entry = journal.plan(
            seq=seq,
            op=plan["action"],
            stable_id=plan["stable_id"],
            src=plan["src_rel"],
            dst=plan["dst_rel"],
            dst_base=plan["dst_base"],
            sha256_before=sha_before,
            mtime_ns_before=mtime_ns_before,
            mode_before=mode_before,
            backup=backup_rel,
            prov_meta=(
                _provenance_meta(plan, batch_id, applied_at) if plan["action"] in ACTIONS_WITH_PROVENANCE else None
            ),
            dir_mtimes=touched_dir_mtimes(vault, plan),
            created_dirs=new_dirs,
            meta={"name": plan["name"], "size_bytes": plan["size_bytes"]},
        )
    else:
        created_dirs += [d for d in (entry.get("created_dirs") or []) if d not in created_dirs]

    # ⛔ 动手那一刻再读一次目录时间: entry 里的「之前」可能是上一次跑留下的陈旧
    # 读数, 那两次之间用户对这个目录做的事不在任何一步的账里。
    dir_at_act = touched_dir_mtimes(vault, plan)
    # ⛔ 落一条 acting 行再动手 —— 「排期了」与「动过盘了」的分界线。少了它,
    # 落点上那份同字节的文件是我们写的还是用户放的, 代码分不出来。
    if entry.get("state") != _UJ.STATE_ACTING:
        entry = journal.mark_acting(entry)

    sha_after, mtime_after, provenance, inode = perform(plan, entry, journal, batch_id, applied_at)

    journal.commit(
        entry,
        sha256_after=sha_after,
        mtime_ns_after=mtime_after,
        provenance=provenance,
        inode=inode,
        dir_mtimes_at_act=dir_at_act,
        dir_mtimes_after=touched_dir_mtimes(vault, plan),
    )
    return entry, sha_after, mtime_after, provenance, inode


def write_receipt_best_effort(journal, data: dict, stem: str):
    """写回执, 但**不让它自己的失败盖掉调用方要说的话**。

    ⛔ 原始失败摘要（停在第几件 / 为什么 / 账在哪）才是用户唯一看得懂的东西; 回执
    写不成只是「少一份可以重新生成的产物」。两条路径（执行 / 撤销）同口径 ——
    只修 apply 那一半就是「管道只修了一半」（自查发现）。
    返回写入异常, 没出错则 None。
    """
    try:
        write_receipt(journal, data, stem)
        return None
    except (OSError, SystemExit, _UJ.JournalError) as e:
        # ⛔ `str(e)` 不含 `__notes__` —— 残片位置就挂在那里。只打 str(e) 等于把
        # round-4 L1 好不容易补上的「哪一份残片要处理」又弄丢了（独立复核 M-3 实证:
        # 改前走裸 traceback 反而看得到, 改后看不到了）。
        notes = "".join(f"\n  {n}" for n in getattr(e, "__notes__", []) or [])
        print(f"⚠ 回执没写成: {e}{notes}（账本仍在 {journal.journal_path}）", file=sys.stderr)
        return e


def run_apply(vault: Path, args, applied_at: str) -> int:
    preview, preview_sha = load_json_file(Path(args.preview), "preview")
    expect = preview.get("vault_fingerprint")
    fingerprint = compute_vault_fingerprint(vault)
    if expect != fingerprint:
        die(
            f"这份 preview 不是为当前 vault 生成的 (指纹 {expect!r} ≠ {fingerprint!r}), "
            f"拒绝拿着别处的盘点单动这里的文件"
        )
    decisions, decisions_sha = load_json_file(Path(args.decisions), "decisions")

    work_dir = resolve_work_dir(vault, args.work_dir)
    label = preview.get("label")
    if isinstance(label, str) and label:
        assert_work_dir_outside_inbox(vault, work_dir, label)

    batch_id = compute_batch_id(fingerprint, preview_sha, decisions_sha)
    journal = _UJ.BatchJournal(work_dir, batch_id, root=vault, fingerprint=fingerprint)

    # ⛔ 只读地读既有账 —— 读不创建目录, 于是拒绝路径仍然零写
    try:
        rows = journal.read_rows()
    except _UJ.JournalError as e:
        die(str(e))  # ⛔ 账本损坏要给干净的拒绝, 不是裸 traceback（零写不受影响）
    # ⛔ 采信历史记录之前先核绑定。只在撤销侧核是不够的: apply 会拿这些行判「哪几件
    # 已完成」「落点归谁」, 一本不属于本 vault 的账能让它直接报完成 (round-3 H9)。
    journal._assert_bound_to(rows, fingerprint)
    plans = build_plans(vault, work_dir, preview, decisions, args.confirm_recycle, journal, rows)
    check_destinations_free(plans, journal, rows)

    # ── 至此全部守卫通过, 才允许碰 work-dir ──
    journal.ensure_dirs()
    # ⛔ 第二次读账同样要包起来。上面第一次 `read_rows()` 已经按「账本损坏要给干净的
    # 拒绝, 不是裸 traceback」包过了, 而 `load()` 比它**多一步会写盘的**
    # `seal_tail_if_needed()` —— 漏包的话, 这里的失败会以裸栈收场（全卡复核 L5）。
    try:
        rows = journal.load()
    except _UJ.JournalError as e:
        die(str(e))
    latest = _UJ.latest_by_seq(rows)
    done_rows = {k: r for k, r in latest.items() if r.get("state") == _UJ.STATE_DONE}
    open_rows = {k: r for k, r in latest.items() if r.get("state") in (_UJ.STATE_PLANNED, _UJ.STATE_ACTING)}

    results, completed, failed, created_dirs = [], 0, None, []
    for plan in plans:
        seq = plan["seq"]
        if seq in done_rows:
            verify_done(plan, done_rows[seq], vault, journal)
            row = done_rows[seq]
            # ⛔ 重跑时也要把旧账上的「本次新建的目录」汇总进来, 否则第二份回执会写成
            # `created_dirs: []`, 把一条如实声明悄悄抹掉。
            created_dirs += [d for d in (row.get("created_dirs") or []) if d not in created_dirs]
            completed += 1
            results.append(
                {
                    "index": seq,
                    "stable_id": plan["stable_id"],
                    "op": plan["action"],
                    "src": plan["src_rel"],
                    "dst": row.get("dst") or None,
                    "provenance": row.get("provenance"),
                    "state": "已完成(上一次)",
                }
            )
            continue

        entry = open_rows.get(seq)
        try:
            entry, sha_after, mtime_after, provenance, inode = _do_one(
                plan, entry, journal, vault, batch_id, applied_at, created_dirs
            )
        except (OSError, SystemExit, _UJ.JournalError) as e:
            failed = {
                "index": seq,
                "stable_id": plan["stable_id"],
                "op": plan["action"],
                "src": plan["src_rel"],
                "dst": plan["dst_rel"] or None,
                "reason": str(e),
            }
            break

        completed += 1
        results.append(
            {
                "index": seq,
                "stable_id": plan["stable_id"],
                "op": plan["action"],
                "src": plan["src_rel"],
                "dst": plan["dst_rel"] or None,
                "provenance": provenance,
                "state": "已完成",
            }
        )
    data = {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "mode": "apply",
        "batch_id": batch_id,
        "vault_fingerprint": fingerprint,
        "applied_at_utc": applied_at,
        "ok": failed is None,
        "total": len(plans),
        "completed": completed,
        "journal": str(journal.journal_path),
        "work_dir": str(work_dir),
        "results": results,
        "failed": failed,
        "created_dirs": sorted(created_dirs),
        "note": (
            f"撤销这一批: inbox_apply.py --vault <V> --undo {journal.journal_path}"
            "（撤销会把搬走的放回原路径并还原修改时间与权限; 复制/硬链出来的那几份移进 "
            "recycle/undone/ 留痕, 不做物理删除; 本次新建的目录会留成空目录）"
        ),
    }
    # ⛔ 回执写入自己再失败, 不能把**原始**失败摘要一起吞掉 (Codex round-5 MEDIUM-2)。
    receipt_error = write_receipt_best_effort(journal, data, RECEIPT_STEM)

    if failed is not None:
        print(
            f"✗ 停在第 {failed['index']} 件（{failed['src']}）: {failed['reason']}\n"
            f"  已完成 {completed}/{len(plans)} 件; 账本 {journal.journal_path}\n"
            f"  修好后用同一份 preview 与同一份拍板重跑, 只会补做没做完的。",
            file=sys.stderr,
        )
        return 1
    if receipt_error is not None:
        # ⛔ 只说「回执没写成」用户无从判断材料动没动 —— 把实际完成数一起说出来。
        print(f"  （材料已按拍板处理: {completed}/{len(plans)} 件 · 批次 {batch_id}）", file=sys.stderr)
        return 1
    print(f"✓ 清仓完成: {completed}/{len(plans)} 件 · 批次 {batch_id}")
    print(f"  回执 {journal.batch_dir / (RECEIPT_STEM + '.md')}")
    print(f"  后悔了就撤销: --undo {journal.journal_path}")
    return 0


def run_undo_mode(vault: Path, journal_arg: str, applied_at: str) -> int:
    journal_path = Path(journal_arg)
    if journal_path.is_symlink():
        die(f"账本是一条 symlink, 拒绝跟随: {journal_path}")
    if not journal_path.is_file():
        die(f"账本不存在或不是普通文件: {journal_path}")
    if journal_path.name != _UJ.JOURNAL_NAME:
        # ⛔ 只取父目录再固定读 journal.jsonl 的话, 用户指错文件(比如 receipt.json)
        # 也会照常撤销, 而他以为撤的是别的 (Codex round-4 M2)。
        die(f"--undo 必须指向 {_UJ.JOURNAL_NAME}, 实得: {journal_path.name}")
    # ⛔ 撤销侧也要有「写入面在 vault 内」这条边界。apply 侧有 `resolve_work_dir`
    # (「--work-dir 必须落在 vault 内, 拒绝越界」), 撤销侧原先一条都没有 ——
    # `--undo` 指到哪里, 回执 / `stale/` / 账目追加就落到哪里, 还会把那个目录里的
    # 同名用户文件挪进新建的 `stale/`, 而 rc=0 报「✓ 已撤销 0 件」
    # （全卡复核 BLOCKER-A 实测: 指向一个恰好叫 journal.jsonl 的用户笔记即可）。
    # `BatchJournal(root=vault)` 只约束 `mkdir_chain`, 回执与账目追加都不走它。
    journal_real = journal_path.resolve()
    vault_real = Path(os.path.realpath(vault))
    if vault_real not in journal_real.parents:
        die(f"--undo 指向的账本必须落在 vault 内, 拒绝越界: {journal_path}")
    batch_dir = journal_real.parent
    fingerprint = compute_vault_fingerprint(vault)
    journal = _UJ.BatchJournal(batch_dir.parent, batch_dir.name, root=vault, fingerprint=fingerprint)
    # ⛔ **写这个目录的准入**, 必须在任何一次写盘之前。下面那两个 except 是按
    # 异常类型分流的, 而「读得出行但读不懂」的账抛的是普通 JournalError, 会落进
    # 会写回执的那一支 —— 于是 `--undo` 指到 vault 内任何一个恰好叫 journal.jsonl
    # 的用户文件, 都会在那个目录留下 undo-receipt 并把同名文件挪进新建的 stale/
    # (最终 HEAD 独立复核 H-B)。这里先纯读判一次, 不过就一个字节都不写。
    try:
        journal.assert_is_ours(fingerprint)
    except (_UJ.JournalError, OSError) as e:
        print(f"✗ {e}", file=sys.stderr)
        print("  （没有往这本账所在的目录写任何东西）", file=sys.stderr)
        return 1

    try:
        result = journal.undo(vault, fingerprint)
    except _UJ.JournalNotOursError as e:
        # ⛔ 这本账刚被判为「不是当前 vault 的 / 不是一本批次账」——那就**一个字节都
        # 不许往它那儿写**。原先与其它失败共用一个 except, 于是拒绝路径会把对方批次
        # 真实的 undo-receipt **零留痕**覆盖成「共 0 件 · 中途停下」, 并往对方账本追加
        # 一条带**本 vault** 指纹的 receipt_sha 行（全卡复核 BLOCKER-B 实测）。
        # `undo-receipt.md` 是用户唯一读得懂的「我的东西还原了没有」的凭证。
        print(f"✗ {e}", file=sys.stderr)
        print("  （没有往这本账所在的目录写任何东西）", file=sys.stderr)
        return 1
    except (_UJ.JournalError, SystemExit, OSError) as e:
        # ⛔ 从异常上取「已经还原了几件」。硬编码 0 的话, 回执会告诉用户「什么都没撤」,
        # 而盘上确实已经还原了 k 件 —— 执行侧那一半是对的（用真实 completed 计数）,
        # 只有撤销这一半没有（全卡复核 M7）。
        partial = list(getattr(e, "_uj_restored", None) or [])
        data = {
            "schema_version": SCHEMA_VERSION,
            "generator": GENERATOR,
            "mode": "undo",
            "batch_id": journal.batch_id,
            "applied_at_utc": applied_at,
            "ok": False,
            "total": len(partial),
            "completed": len(partial),
            "journal": str(journal.journal_path),
            "work_dir": str(journal.work_dir),
            "results": [
                {
                    "index": r["seq"],
                    "stable_id": "",
                    "op": r["op"],
                    "src": r["action"],
                    "dst": None,
                    "provenance": None,
                    "state": "已还原",
                }
                for r in partial
            ],
            "failed": {
                "index": 0,
                "stable_id": "",
                "op": "undo",
                "src": "",
                "dst": None,
                "reason": str(e),
            },
            "note": "撤销中途停下: 已还原的那几件记在账上了, 修好原因后再跑一次只会补做剩下的。",
        }
        write_receipt_best_effort(journal, data, UNDO_RECEIPT_STEM)
        print(f"✗ {e}", file=sys.stderr)
        print(f"  （已还原 {len(partial)} 件; 修好原因后再跑一次只会补做剩下的）", file=sys.stderr)
        return 1

    # ⛔ 「本次还原的」+「上一次已经撤掉的」一起进回执。只写本次的话, 第二次跑同一条
    # `--undo`（幂等空操作）会把上一次那份回执原地换成「共 0 件 / results: []」,
    # 把一条如实声明悄悄抹掉（全卡复核 M5）。执行侧对同一个坑做了回填, 见 run_apply。
    prior = result.get("already_undone") or []
    items = [
        {
            "index": r["seq"],
            "stable_id": "",
            "op": r["op"],
            "src": r["action"],
            "dst": None,
            "provenance": None,
            "state": "已还原" if r in result["restored"] else "上一次已撤销",
        }
        for r in list(result["restored"]) + list(prior)
    ]
    data = {
        "schema_version": SCHEMA_VERSION,
        "generator": GENERATOR,
        "mode": "undo",
        "batch_id": journal.batch_id,
        "applied_at_utc": applied_at,
        "ok": True,
        "total": len(items),
        "completed": len(result["restored"]),
        "journal": str(journal.journal_path),
        "work_dir": str(journal.work_dir),
        "results": items,
        "failed": None,
        "created_dirs": result.get("dirs_left_behind") or [],
        "dirs_retimed": result.get("dirs_retimed") or [],
        "dirs_not_retimed": result.get("dirs_not_retimed") or [],
        "note": "复制/硬链出来的那几份已移进 recycle/undone/ 留痕, 没有做任何物理删除。",
    }
    if write_receipt_best_effort(journal, data, UNDO_RECEIPT_STEM) is not None:
        print(f"  （已撤销 {len(result['restored'])} 件 · 批次 {journal.batch_id}）", file=sys.stderr)
        return 1
    print(f"✓ 已撤销 {len(result['restored'])} 件 · 批次 {journal.batch_id}")
    print(f"  回执 {journal.batch_dir / (UNDO_RECEIPT_STEM + '.md')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="待处理清仓执行侧 (CARD-G5-7)")
    ap.add_argument("--vault", required=True, help="vault 根目录")
    ap.add_argument("--preview", default=None, help="G5-6 产出的 inbox-preview-<label>.json")
    ap.add_argument("--decisions", default=None, help="用户逐条拍板 JSON")
    ap.add_argument(
        "--work-dir",
        default=None,
        help=f"备份/账本/回收目录 (缺省 <vault>/{DEFAULT_WORK_PARENT}/{DEFAULT_WORK_NAME})",
    )
    ap.add_argument(
        "--confirm-recycle",
        action="store_true",
        help="整批允许「移入回收目录」; 仍需每条自带 confirm: true",
    )
    ap.add_argument("--undo", default=None, help="撤销模式: 指向某批次的 journal.jsonl")
    ap.add_argument("--now", default=None, help="回执时刻 ISO-8601 (缺省当前 UTC)")
    args = ap.parse_args()

    applied_at = _UJ.utc_now_iso(_IP.parse_now(args.now) if args.now else None)
    vault = resolve_vault(args.vault)

    if args.undo is not None:
        if args.preview or args.decisions:
            die("--undo 与执行模式互斥, 请分两次跑")
        return run_undo_mode(vault, args.undo, applied_at)

    if not args.preview or not args.decisions:
        die("执行模式必须同时给 --preview 与 --decisions（撤销请用 --undo）")
    return run_apply(vault, args, applied_at)


if __name__ == "__main__":
    raise SystemExit(main())
