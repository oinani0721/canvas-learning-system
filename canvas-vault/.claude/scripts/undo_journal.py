#!/usr/bin/env python3
"""批次备份快照 + undo journal —— 共用模块 (CARD-G5-7, G5-10 复用)。

本模块只提供「把一批文件搬动记成可逆的账」这一件事, 不认识收件箱、不认识白板:
  · BatchJournal(work_dir, batch_id, root=, fingerprint=)  一个批次 = 一个目录 = 一本账
  · backup(src)                       —— op 之前的逐字节快照 (undo 的真相源)
  · plan(...) / commit(...)           —— 先落 planned 行再动手, 动完落 done 行
  · undo()                            —— 逆序还原; copy/link 产物**移入**回收目录
  · write_provenance(path, meta)      —— frontmatter 溯源块, 原子写 + 回写 mtime/mode
  · write_pair_atomically(items)      —— 成对发布 (两份都写好 tmp 才双双就位)

⛔ 三条贯穿全模块的规矩:

1. **零物理删除原语** (os.remove / os.unlink / Path.unlink / shutil.rmtree /
   os.rmdir / send2trash)。「撤销一次 copy」= 把副本挪进 recycle/undone/, 不是删掉它;
   写失败的 tmp 挪进 stale/, 不是删掉它。裁判见
   backend/tests/skills/test_g5_7_inbox_apply.py 的 F2 AST 门 (数 Call 节点, 不数文本)。

2. **「零删除原语」不等于「不会覆盖」。** `os.replace` / `copyfile` / `O_TRUNC` 都能
   在不调用任何删除原语的情况下把既有内容换掉。所以每一处落笔前都要先证明落点
   **归自己所有**。

3. **「内容相同」不等于「归我所有」。** 判归属只用可计算的等式: done 行比
   `sha256_after`; planned 行比「与备份逐字节相同」或「等于把备份按账上那份
   `prov_meta` 渲染一遍的结果」—— 后者是纯函数, 期望值算得出来, 不是「看起来像」。
   凡是「全文里出现了某个子串」这类启发式都不作数 (Codex round-2 H1)。

祖先链无 symlink 的判定复用 board-split/scripts/split_preview.py 的
`assert_symlink_free`（与 clear-inbox/scripts/inbox_preview.py:266-290 同一条理由:
自己简单写一下, 等于在安全面上开一个没人审过的旁路）。**回执的成对发布不复用**它的
`write_pair_atomically_checked` —— 那个函数用 `O_CREAT` 先把两个目标建出来, 失败时
按路径回滚 unlink, 并发下会删到别人刚放上去的同名目录项。
"""

from __future__ import annotations

import errno
import hashlib
import importlib.util
import json
import os
import shutil
import stat as stat_mod
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
GENERATOR = "undo_journal.py v1.2 (CARD-G5-7 batch backup + undo journal)"

#: 复用来源 —— <vault>/.claude/scripts/ → <vault>/.claude/skills/board-split/scripts/
_SP_PATH = Path(__file__).resolve().parents[1] / "skills" / "board-split" / "scripts" / "split_preview.py"


def _load_split_preview():
    """加载写侧防御的单一真相源。⛔ 缺失即拒绝运行, 不做本地降级实现。"""
    if not _SP_PATH.is_file():
        raise SystemExit(
            f"✗ 复用来源缺失, 拒绝以未加固的写侧运行。需要文件: {_SP_PATH}\n  （祖先链 symlink 守卫复用该模块。）"
        )
    spec = importlib.util.spec_from_file_location("_g57_split_preview", _SP_PATH)
    mod = importlib.util.module_from_spec(spec)
    # ⛔ exec_module 默认会在被导入模块**旁边**写 __pycache__/*.pyc —— 那是往 vault
    # 里、而且是另一条车道的目录里落文件。零写侧不是「不改用户的 md」。
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


_SP = _load_split_preview()

# ───────────────────────────────── 常量 ─────────────────────────────────

JOURNAL_NAME = "journal.jsonl"
BACKUP_DIR = "backup"
RECYCLE_DIR = "recycle"
UNDONE_DIR = "undone"
STALE_DIR = "stale"

PROVENANCE_KEY = "clear_inbox_provenance"
TMP_SUFFIX = ".undo-journal-tmp"

#: journal 行的状态机。tail_sealed 是给「掉电留下的半行」封口用的哨兵行。
STATE_PLANNED = "planned"
#: ⛔ 「排期了」与「已经动过盘」之间必须有一条**可观测**的界。没有它, 落点上那份
#: 同字节的文件既可能是我们刚复制的, 也可能是用户放的, 代码分不出来 —— 于是会给
#: 用户的文件写溯源、撤销时又把它挪走。多这一行账换来状态机是全的。
STATE_ACTING = "acting"
STATE_DONE = "done"
STATE_UNDONE = "undone"
STATE_TAIL_SEALED = "tail_sealed"
#: 记「上一次往回执落点写下去的内容的 sha256」。不是业务状态, 只是归属证据 ——
#: 有了它, 「这份回执是不是我自己上一版」就是一条可计算的等式, 不必猜。
STATE_RECEIPT_SHA = "receipt_sha"
#: 有业务含义的状态 —— 「同一 seq 的最新一条」按它们判, 不按「出现过没有」。
BUSINESS_STATES = (STATE_PLANNED, STATE_ACTING, STATE_DONE, STATE_UNDONE)
#: 账本里允许出现的全部 state —— 认不出来的一律按损坏处理, 不静默忽略。
KNOWN_STATES = BUSINESS_STATES + (STATE_TAIL_SEALED, STATE_RECEIPT_SHA)

#: 可逆的搬运动作。skip 只记账、不动盘。
OP_COPY = "copy"
OP_LINK = "link"
OP_MOVE = "move"
OP_RECYCLE = "recycle"
OP_SKIP = "skip"
OPS = (OP_COPY, OP_LINK, OP_MOVE, OP_RECYCLE, OP_SKIP)
OPS_LEAVE_SOURCE = (OP_COPY, OP_LINK)
OPS_TAKE_SOURCE = (OP_MOVE, OP_RECYCLE)

#: dst 的基准: vault 相对 (copy/link/move) 或批次目录相对 (recycle)
BASE_VAULT = "vault"
BASE_BATCH = "batch"

PROVENANCE_WRITTEN = "written"
PROVENANCE_NOT_MARKDOWN = "skipped:not-markdown"
PROVENANCE_NOT_UTF8 = "skipped:not-utf8"
PROVENANCE_UNTERMINATED = "skipped:unterminated-frontmatter"

#: ⛔ 这三个字符会被 str.splitlines() 当成换行 —— 落进 journal 就会让「一行一条
#: 记录」的口径在不同读法下给出不同答案 (含它的那条记录永远重放不掉)。落盘前统一
#: 转成 \u 转义 (JSON 字符串里合法), 于是整份 journal 里除了行分隔的 \n 再无
#: 任何「像换行的字节」。读侧一律 split("\n"), 绝不用 splitlines()。
_LINE_LIKE = {chr(0x2028): "\\u2028", chr(0x2029): "\\u2029", chr(0x0085): "\\u0085"}


class JournalError(RuntimeError):
    """账目层的拒绝 —— 消息即回执正文, 必须精确到「哪一件 / 为什么 / 现在在哪」。"""


# ───────────────────────────── 原语 ─────────────────────────────


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now_iso(now: datetime | None = None) -> str:
    dt = now or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_symlink(path) -> bool:
    return os.path.islink(str(path))


def assert_path_safe(path, *, what: str) -> None:
    """落笔面的通用准入: 祖先链无 symlink, 且末段本身不是 symlink。

    ⛔ 两件事都要查。`O_NOFOLLOW` 只管末段, 而祖先里的一条 symlink 能把「词法上在
    vault 内」的写整个重定向到别处。
    """
    p = Path(path)
    _SP.assert_symlink_free(p.parent)
    if is_symlink(p):
        raise JournalError(f"✗ {what} 是一条 symlink, 拒绝跟随: {p}")


def json_line(obj: dict) -> bytes:
    """一条记录 = 一行 = 一次 os.write。sort_keys 让同输入逐字节可复现。"""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    for ch, esc in _LINE_LIKE.items():
        s = s.replace(ch, esc)
    if "\n" in s:
        raise JournalError("journal 记录里出现裸换行, 拒绝写入 (会把一条记录切成两条)")
    return (s + "\n").encode("utf-8")


def append_bytes(path: Path, payload: bytes) -> None:
    """单次 O_APPEND write + fsync —— 一行即一个原子追加。"""
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags, 0o644)
    except OSError as e:
        raise JournalError(f"✗ journal 不可追加 (可能被 symlink 布防): {path} ({e})") from e
    try:
        n = os.write(fd, payload)
        if n != len(payload):
            raise JournalError(f"✗ journal 追加不完整 ({n}/{len(payload)} 字节): {path}")
        os.fsync(fd)
    finally:
        os.close(fd)


def _tmp_path_for(path: Path) -> Path:
    """同目录、**唯一名**、点开头的临时文件名。

    ⛔ 固定名 + `O_TRUNC` 是一条覆盖既有内容的路: 名字撞上用户的文件就把它截断;
    若那个名字恰是指向原件的硬链接, 连原件一起改写。唯一名 + `O_EXCL` 让「撞上了」
    变成一个响亮的失败, 而不是一次静默覆盖。点开头是给 Obsidian 看的 (它不索引点文件)。
    """
    return path.with_name(f".{path.name}.{os.getpid()}-{uuid.uuid4().hex[:8]}{TMP_SUFFIX}")


#: 唯一名比原名多出的字节数上界: `.` + `.` + pid(≤7) + `-` + uuid8 + TMP_SUFFIX。
#: 用来在 ENAMETOOLONG 时给出**准确**的原因, 而不是笼统的「已被占用」。
TMP_NAME_OVERHEAD = 2 + 7 + 1 + 8 + len(TMP_SUFFIX)


def _open_new_exclusive(tmp: Path) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(str(tmp), flags, 0o600)
    except OSError as e:
        # ⛔ 「已被占用」对 ENAMETOOLONG 是**误导**: 唯一名比原名多 TMP_NAME_OVERHEAD
        # 字节, 于是原名接近 NAME_MAX 的材料在这里必失败, 而用户按「已被占用」去查
        # 会一无所获（全卡复核 L7）。把真正的原因说出来。
        if getattr(e, "errno", None) == errno.ENAMETOOLONG:
            raise JournalError(
                f"✗ 文件名太长, 放不下临时文件名（临时名比原名多约 {TMP_NAME_OVERHEAD} 字节, "
                f"多数文件系统上限 255）: {tmp.name} —— 请把材料改个短一点的名字再清仓"
            ) from e
        raise JournalError(f"✗ 临时文件已被占用或不可创建, 拒绝写入: {tmp} ({e})") from e


def _write_fd(fd: int, data: bytes) -> None:
    with os.fdopen(fd, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def _park_stale(tmp: Path, stale_dir: Path | None):
    """写失败的 tmp 残片挪进 stale/ 留痕, 不做物理删除。

    ⛔ 这个落点同样要过 symlink 守卫 —— 把 stale/ 指到 vault 外, 残片就被搬出去了。
    守卫不过时**就地留着不动**: 这是异常处理路径, 再抛一个新异常会把真正的失败原因
    盖掉, 而把残片留在原目录比搬到不知道哪里更安全。

    返回残片最终所在的路径（停不成功就是它原来的位置）—— 调用方要能说出「哪一份
    东西需要你去看一眼」, 否则「就地留着」等于无声地留下垃圾 (Codex round-4 L1)。
    """
    if stale_dir is None or not os.path.lexists(str(tmp)):
        return None
    try:
        if is_symlink(stale_dir):
            return tmp
        _SP.assert_symlink_free(stale_dir.parent)
        os.makedirs(str(stale_dir), exist_ok=True)
        _SP.assert_symlink_free(stale_dir)
        target = free_path(stale_dir / tmp.name)
        if is_symlink(target):
            return tmp
        os.replace(str(tmp), str(target))
        return target
    except (OSError, SystemExit, JournalError):
        return tmp  # 留在原地; 原始失败原因不被掩盖


def preserve_foreign_file(path: Path, stale_dir: Path | None, owned_sha: str | None) -> bool:
    """落点上若是一份**不属于我们**的普通文件, 先挪进 stale/ 留痕。停放成功返回 True。

    ⛔ 「产物可以重新生成」不构成覆盖它的理由: 那个路径上放的可能根本不是我们的
    产物, 而是用户自己的文件 (Codex round-4 H6)。本工具默认路径 0 物理删除, 覆盖
    同样算「弄丢」。

    ⛔ 作用域**只到回执落点**, 不进通用的 `_replace_or_park`。round-5 曾把它接进
    通用路径, 于是业务文件每写一次溯源就被挪进 stale/ 一次, 而且「先挪走旧的、再
    放新的」中间留出一个正式路径两头都不在的窗口 —— 中断在那里就谁也恢复不了
    (Codex round-5 HIGH-2, 是 H6 整改自己引入的回归)。作用域和意图要分开看。

    `owned_sha` = 上一次我们往这个路径写下去的内容的 sha256（记在账里）。落点字节与它
    相等 ⇒ 那就是自家上一版产物, 直接让位不留痕（否则每次重跑都堆两份）。

    ⛔ 判据是**可计算的等式**, 不是「全文里出现了 batch_id」那类子串启发式 —— 后者
    与本模块第 3 条铁律正面冲突, 而且落点上任何恰好抄了批次号的用户笔记都会被零留痕
    覆盖（独立复核 H-1 实证; 撤销模式的 batch_id 来自目录名, 长度还不受约束）。
    """
    if not os.path.lexists(str(path)) or is_symlink(path) or not Path(path).is_file():
        return True
    if owned_sha:
        try:
            if sha256_file(path) == owned_sha:
                return True
        except OSError:
            pass
    if stale_dir is None:
        # ⛔ 没有留痕的地方 ⇒ 没有「留不住」这回事, 只有「不许盖」。`_park_stale` 在
        # stale_dir 为 None 时返回 None, 若拿它跟原路径比就会判成「停放成功」——
        # HIGH-1 那个洞会从默认参数上重新开一次（自查发现, 当前无调用方传 None,
        # 但这是公开函数, G5-10 要复用）。
        return False
    return _park_stale(Path(path), stale_dir) != Path(path)


def _replace_or_park(tmp: Path, path: Path, stale_dir: Path | None) -> None:
    """就位。⛔ 最后这一步也要包在残片处理里 —— 它失败时 tmp 同样留在原地。

    ⛔ 把**停放之后**的真实位置挂到异常上 (`_uj_residue`)。`_park_stale` 的 docstring
    明写「返回残片最终所在的路径 …… 调用方要能说出哪一份东西需要你去看一眼」, 而这
    一跳原先把返回值丢了 —— 调用方只能报 tmp 的旧路径, 用户照着去找是空的, 残片其实
    躺在 stale/ 里 (Codex round-5 LOW-1)。它本来「登记不阻断」, 但 M-3 把 notes 打给
    了用户, 这条错值从**没人看得到**变成**端到用户眼前**, 所以跟着 M-3 一起修。
    """
    try:
        os.replace(str(tmp), str(path))
    except BaseException as e:
        parked = _park_stale(tmp, stale_dir)
        if parked is not None:
            try:
                e._uj_residue = Path(parked)  # type: ignore[attr-defined]
            except Exception:
                pass  # 少数内建异常不许挂属性; 报旧路径也好过把原始失败原因弄丢
        raise


class JournalNotOursError(JournalError):
    """这本账不是当前 vault / 不是一本批次账。

    ⛔ 单独一个类型是为了让调用方能**区别对待**: 被判为「不是我们的」之后, 就
    一个字节都不许再往那个目录写 —— 包括失败回执。原先所有撤销失败共用一个
    except, 于是拒绝路径反手把对方批次真实的 undo-receipt 零留痕覆盖成一句假话
    （全卡复核 BLOCKER-B）。
    """


def safe_join(base, rel, *, what: str) -> Path:
    """把账本里记的相对路径拼到 base 上, 并**卡死形状**。

    ⛔ 账本是躺在 vault 里 `outputs/clear-inbox/<batch>/journal.jsonl` 的普通文本:
    用户手改、同步工具改、部分写坏都够得着 —— 它和 preview JSON 是**同一类**输入。
    执行侧对 preview 的 `rel_path` 卡死了形状（`inbox_apply.source_path`, 注释原话
    「一条 `../outside.md` 就能让执行侧去搬 vault 外的文件」）, 撤销侧却对
    `src` / `dst` / `backup` 直接拼 —— 一条 `..` 就能把 vault 内的材料搬出 vault 并
    报「✓ 已撤销」, 绝对路径变体还会在 vault 外造出目录链然后以裸 traceback 收场
    （全卡复核 BLOCKER-C 实测）。

    ⛔ 撤销是后悔药, 它比执行更该 fail-closed。`assert_symlink_free` 挡不住这条:
    它比的是 normpath 与 realpath, 对**无 symlink 的** `../` 路径两者相等, 一律放行。
    """
    if not isinstance(rel, str) or not rel:
        raise JournalError(f"✗ 账上的{what}不是一个路径: {rel!r}")
    cand = Path(rel)
    if cand.is_absolute():
        raise JournalError(f"✗ 账上的{what}是绝对路径, 拒绝采信: {rel!r}")
    if any(p == ".." for p in cand.parts):
        raise JournalError(f"✗ 账上的{what}含 `..`, 拒绝越界: {rel!r}")
    out = Path(base) / cand
    # ⛔ 这里只做**词法**判定。物理层（祖先/末段是不是 symlink）由调用方既有的
    # `assert_symlink_free` / `is_symlink` 守卫负责 —— 在这里改用 realpath 会把
    # 「落点现在是一条指向 vault 外的 symlink」这种情况也吞进同一条错误里, 盖掉那些
    # 更准确、用户更用得上的诊断（实测: 既有的 symlink 门会从「symlink」变成「越界」）。
    base_norm = os.path.normpath(str(Path(base)))
    out_norm = os.path.normpath(str(out))
    if out_norm != base_norm and not out_norm.startswith(base_norm + os.sep):
        raise JournalError(f"✗ 账上的{what}归一化后落在 {base} 之外, 拒绝越界: {rel!r}")
    return out


def park_into_stale(path, stale_dir: Path | None, *, what: str) -> Path:
    """把落点上那份**不是我们造的**东西挪进 stale/ 留痕, 返回它的新位置。

    ⛔ 和 `_park_stale`（给我们自己的 tmp 残片用、挪不成就就地留着）不同: 这里搬的是
    **用户的文件**, 所以要求更严 —— 留痕目录先证明可用, 挪不成就抛。A_LINK 的半态
    分支原先是裸 `os.makedirs` + `os.replace`, 是全卡唯一一处既不查 stale/ 是不是
    symlink、也不记账的搬动: stale/ 被换成指向 vault 外的 symlink 时, 用户的笔记会被
    无声搬出 vault 而工具报「✓ 全部完成」（全卡复核 HIGH-G 实测）。
    """
    assert_stale_dir_usable(stale_dir, what=what)
    stale = Path(stale_dir)
    os.makedirs(str(stale), exist_ok=True)
    _SP.assert_symlink_free(stale)
    target = free_path(stale / Path(path).name)
    assert_path_safe(target, what=what)
    os.replace(str(path), str(target))
    return target


def assert_stale_dir_usable(stale_dir: Path | None, *, what: str) -> None:
    """落点上有外来文件时, 「有地方留痕」必须在**动盘之前**就证明得了。

    ⛔ 只查 `stale_dir is None` 不够: 它有值但**不可用**（被占成普通文件 / 是一条
    symlink / 祖先链里有 symlink）时校验段照样放行, 真正的拒绝被推迟到逐条 replace
    的循环里 —— 第一份已经就位之后第二份才说「留不住」, 于是发布出去的一对回执互相
    矛盾（机器读 .json 是新的, 人读 .md 还是旧的）, 而两段式**之前**这条输入是零写的。
    这是两段式整改自己引入的回退 (独立复核 round-2 D-1 实证)。

    这一段只能证明**静态可判**的那几种不可用; 竞态与 IO 错误（ENOSPC/EACCES/被别的
    进程换掉）仍然只会在动盘段才显形 —— 如实声明, 不假装 replace 之前能证明一切。
    """
    if stale_dir is None:
        raise JournalError(f"✗ {what}上有别的文件且无处留痕, 拒绝覆盖")
    p = Path(stale_dir)
    if is_symlink(p):
        raise JournalError(f"✗ 留痕目录是一条 symlink, 拒绝跟随: {p}")
    if os.path.lexists(str(p)) and not p.is_dir():
        raise JournalError(f"✗ 留痕目录被占成了别的东西, 无处留痕: {p}")
    try:
        _SP.assert_symlink_free(p.parent)
    except SystemExit as e:
        # 统一成 JournalError: 调用方接的是 (OSError, JournalError), 让守卫的失败
        # 走同一个出口, 免得「拒绝」从一种异常类型漏成另一种。
        raise JournalError(f"✗ 留痕目录的祖先链上有 symlink, 无处安全留痕: {p}") from e


def atomic_write_bytes(path: Path, data: bytes, stale_dir: Path | None = None, mode: int | None = None) -> None:
    """同目录唯一名 tmp + os.replace (quiz-answer SKILL.md:156-158 口径)。

    ⛔ 原文件在 os.replace 成功之前一个字节都不动 —— 不用 write_text: 它会先按
    只写模式截断文件, 编码失败时留下一个已经被清空的原件。
    `mode` 给定时在就位前把权限写到 tmp 上（os.replace 换的是 inode, 不带过去
    原文件的权限位）。
    """
    tmp = _tmp_path_for(path)
    fd = _open_new_exclusive(tmp)
    try:
        _write_fd(fd, data)
        if mode is not None:
            os.chmod(str(tmp), stat_mod.S_IMODE(mode))
    except BaseException:
        _park_stale(tmp, stale_dir)
        raise
    _replace_or_park(tmp, path, stale_dir)


def copy_file_atomically(src: Path, dst: Path, stale_dir: Path | None = None) -> None:
    """把 src 逐字节复制到 dst —— 经唯一名 tmp 再 os.replace 就位。

    ⛔ 不直接 `copyfile(src, dst)`: 那会**截断** dst 那个 inode, 于是
      · dst 若是用户自己放的同名文件 —— 内容没了;
      · dst 若与别处硬链接同一个 inode —— 连那一处一起改写。
    换成「先写新 inode, 再换目录项」, 旧 inode 的其它硬链接原样不动。
    """
    tmp = _tmp_path_for(dst)
    fd = _open_new_exclusive(tmp)
    try:
        with os.fdopen(fd, "wb") as out, open(str(src), "rb") as fin:
            shutil.copyfileobj(fin, out)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        _park_stale(tmp, stale_dir)
        raise
    _replace_or_park(tmp, dst, stale_dir)


def free_path(path: Path) -> Path:
    """返回一个尚未被占用的同族路径 (…-2 / …-3 …)。

    ⛔ 撤销时绝不覆盖已存在的条目 —— 覆盖 = 悄悄把某份东西换掉。
    """
    if not os.path.lexists(str(path)):
        return path
    stem, suffix = path.stem, path.suffix
    for n in range(2, 10_000):
        cand = path.with_name(f"{stem}-{n}{suffix}")
        if not os.path.lexists(str(cand)):
            return cand
    raise JournalError(f"✗ 回收目录同名条目过多, 无法安放: {path}")


# ─────────────────────────── provenance ───────────────────────────


def detect_newline(raw: bytes) -> bytes:
    """按**字节**探测换行风格。⛔ 绝不用文本读 —— read_text 的 newline=None 会把
    CRLF 归一成 LF, 于是「保持原样」写回去的是一份被改过行尾的文件。"""
    i = raw.find(b"\n")
    if i > 0 and raw[i - 1 : i] == b"\r":
        return b"\r\n"
    return b"\n"


def frontmatter_span(raw: bytes, nl: bytes) -> tuple[int, int] | None:
    """返回 (正文起点, 收尾 '---' 行的起点); 没有**完整**的 frontmatter 返回 None。"""
    opener = b"---" + nl
    if not raw.startswith(opener):
        return None
    start = len(opener)
    pos = start
    while pos <= len(raw):
        eol = raw.find(nl, pos)
        line = raw[pos:eol] if eol != -1 else raw[pos:]
        if line == b"---":
            return start, pos
        if eol == -1:
            return None
        pos = eol + len(nl)
    return None


def _is_provenance_key_line(line: bytes) -> bool:
    """键行的三种写法都要认 —— 只认裸键会在引号形式下留下重复键。"""
    key = PROVENANCE_KEY.encode("utf-8")
    return line.startswith(key + b":") or line.startswith(b'"' + key + b'":') or line.startswith(b"'" + key + b"':")


def _is_block_neutral(line: bytes) -> bool:
    """空行与顶格注释都**不足以**宣布块结束 —— 得看它们后面还缩不缩进。"""
    s = line.strip()
    return s == b"" or s.startswith(b"#")


def strip_provenance_block(body: bytes, nl: bytes) -> bytes:
    """摘掉既有的溯源块 (键行 + 其下所有缩进子行) —— 重写即幂等的前提。

    ⛔ 块里夹一个空行或一行顶格注释都不算块结束: 它们只有在**下一个有内容的行不再
    缩进**时才算出块。只看「连续缩进」会在这些地方提前收手, 把剩下的子行留在原地,
    于是它们被下一个 mapping 收编 —— 那是静默改掉别人的 metadata。
    """
    lines = body.split(nl)
    out: list[bytes] = []
    inside = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if _is_provenance_key_line(line):
            inside = True
            i += 1
            continue
        if inside:
            if line.startswith(b" ") or line.startswith(b"\t"):
                i += 1
                continue
            if _is_block_neutral(line):
                j = i + 1
                while j < len(lines) and _is_block_neutral(lines[j]):
                    j += 1
                if j < len(lines) and (lines[j].startswith(b" ") or lines[j].startswith(b"\t")):
                    i += 1
                    continue
            inside = False
        out.append(line)
        i += 1
    return nl.join(out)


def _yaml_scalar(value) -> bytes:
    """JSON 标量是 YAML 1.2 的合法子集 —— 路径里的冒号/引号/中文一律交给它转义,
    不手写 YAML 转义规则。"""
    s = json.dumps("" if value is None else str(value), ensure_ascii=False)
    for ch, esc in _LINE_LIKE.items():
        s = s.replace(ch, esc)
    return s.encode("utf-8")


PROVENANCE_FIELDS = ("source_rel_path", "source_mtime_utc", "batch_id", "applied_at_utc", "op")


def provenance_block(meta: dict, nl: bytes) -> bytes:
    lines = [PROVENANCE_KEY.encode("utf-8") + b":"]
    for key in PROVENANCE_FIELDS:
        lines.append(b"  " + key.encode("utf-8") + b": " + _yaml_scalar(meta.get(key)))
    return nl.join(lines) + nl


def render_provenance(raw: bytes, meta: dict) -> bytes:
    """把溯源块合进 frontmatter, 返回**新的全文字节**。原有键一律保留。

    纯函数 —— 同一份输入 + 同一份 meta 恒得同一串字节。落点归属判定靠的就是这一点:
    「我这一步写出来应该长什么样」算得出来, 于是可以逐字节比, 不必猜。
    """
    nl = detect_newline(raw)
    block = provenance_block(meta, nl)
    span = frontmatter_span(raw, nl)
    if span is None:
        return b"---" + nl + block + b"---" + nl + nl + raw
    start, end = span
    body = strip_provenance_block(raw[start:end], nl)
    if body and not body.endswith(nl):
        body += nl
    return raw[:start] + body + block + raw[end:]


def provenance_outcome(raw: bytes, suffix: str) -> str:
    """不落盘地判一份内容会走到哪个分支 —— 与 write_provenance 同一套条件。"""
    if suffix.lower() != ".md":
        return PROVENANCE_NOT_MARKDOWN  # 调用方须在**读文件之前**先判这一条
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return PROVENANCE_NOT_UTF8
    nl = detect_newline(raw)
    if raw.startswith(b"---" + nl) and frontmatter_span(raw, nl) is None:
        return PROVENANCE_UNTERMINATED
    return PROVENANCE_WRITTEN


def expected_after_provenance(raw: bytes, suffix: str, meta: dict) -> bytes:
    """这一份内容写完溯源之后应该是什么字节。跳过的三种情形返回原样。"""
    if provenance_outcome(raw, suffix) != PROVENANCE_WRITTEN:
        return raw
    return render_provenance(raw, meta)


def write_provenance(path: Path, meta: dict, stale_dir: Path | None = None) -> str:
    """给本批次产出的 .md 写溯源 frontmatter, 并回写原 mtime 与权限位。

    看不懂结构的文件**一个字节都不动**:
      · 非 UTF-8 —— 按某个编码猜着写回去等于悄悄损坏用户的材料;
      · `---` 开了头却没有收尾 `---` —— 在它上面再插一份 frontmatter 会把原来那段
        挤进正文（渲染成一条分隔线 + 一段裸文本）。看不懂就别动, 在账上说清楚。
    """
    p = Path(path)
    # ⛔ 后缀先判、再读文件: 否则 PDF / 视频这类本可以直接略过的大文件也会被整份
    # 读进内存（重构时把 read_bytes 提前一行造成的回归, Codex round-3 M12）。
    if p.suffix.lower() != ".md":
        return PROVENANCE_NOT_MARKDOWN
    raw = p.read_bytes()
    outcome = provenance_outcome(raw, p.suffix)
    if outcome != PROVENANCE_WRITTEN:
        return outcome
    new_raw = render_provenance(raw, meta)
    if new_raw == raw:
        return PROVENANCE_WRITTEN  # 已是目标形态 —— 重跑幂等
    st = p.stat()
    atomic_write_bytes(p, new_raw, stale_dir, mode=st.st_mode)
    os.utime(str(p), ns=(st.st_mtime_ns, st.st_mtime_ns))
    return PROVENANCE_WRITTEN


def write_pair_atomically(
    items: list[tuple[Path, bytes]], stale_dir: Path | None = None, owned_shas: dict | None = None
) -> None:
    """成对发布: 两份都写好各自的 tmp, 再双双就位。

    与 split_preview.write_pair_atomically_checked 的差别（有意为之）: 不预建 0 字节
    目标, 因而失败时**没有**「按路径 unlink 回滚」这一步 —— 那一步在并发下会删到
    别人刚放上去的同名目录项。代价如实写明: 两次 `os.replace` 之间若进程被杀,
    仍可能只就位一份。恢复依据是 journal, 回执本来就可以重新生成。
    """
    owned_shas = owned_shas or {}

    # ── 第一段: **只读**校验。⛔ 这一段一个字节都不许动盘 —— 上一版把会动盘的
    # 「停放」放进了校验段, 于是第一份被挪进 stale/ 之后第二份才拒绝, 官方路径两头
    # 都不在、还一个字都不说（独立复核 M-1 实证）。
    needs_park: dict = {}
    for path, _ in items:
        path = Path(path)
        assert_path_safe(path, what="回执落点")
        foreign = (
            os.path.lexists(str(path))
            and not is_symlink(path)
            and path.is_file()
            and sha256_file(path) != owned_shas.get(str(path))
        )
        needs_park[str(path)] = foreign
    if any(needs_park.values()):
        # ⛔ 「有地方留痕」是**动盘的前提**, 不是动盘途中才发现的事。
        assert_stale_dir_usable(stale_dir, what="回执落点")

    tmps: list[tuple[Path, Path]] = []
    try:
        for path, data in items:
            tmp = _tmp_path_for(path)
            fd = _open_new_exclusive(tmp)
            try:
                _write_fd(fd, data)
            except BaseException:
                _park_stale(tmp, stale_dir)
                raise
            tmps.append((tmp, path))
    except BaseException:
        for tmp, _ in tmps:
            _park_stale(tmp, stale_dir)
        raise
    # ── 第二段: 先把**所有**外来文件留痕, 再做**任何一次** replace。
    # ⛔ 顺序本身就是性质的一部分: 边留痕边 replace 的话, 第 k 份留不住时前 k-1 份
    # 已经发布出去了 —— 一对回执互相矛盾, 而这条输入在两段式之前是零写的
    # (独立复核 round-2 D-1)。作用域仍然**只到回执落点**, 不碰业务文件 (round-5 HIGH-2)。
    for path, _ in items:
        if not needs_park.get(str(Path(path))):
            continue
        # ⛔ 留存失败就**不许覆盖**: 明知留不住还是盖了 = 无声弄丢。
        if not preserve_foreign_file(Path(path), stale_dir, None):
            err = JournalError(f"✗ 回执落点上有别的文件且无法留痕, 拒绝覆盖: {path}")
            residues = [_park_stale(t, stale_dir) or t for t, _ in tmps]
            err.add_note("残片位置: " + " / ".join(str(r) for r in residues if r))
            raise err

    # ── 第三段: 全部就位。
    for idx, (tmp, path) in enumerate(tmps):
        try:
            _replace_or_park(tmp, path, stale_dir)
        except BaseException as e:
            # ⛔ 还没就位的那几份也要停放 —— 否则第一份失败就会把后面的 tmp 留在
            # 正式目录里。残片位置挂到异常上, 让调用方说得出「去看哪一份」。
            # ⛔ 当前这一份报的是**停放之后**的位置 (`_uj_residue`), 不是 tmp 的旧
            # 路径 —— 后者在 `_replace_or_park` 里已经被挪走, 照着找是空的 (D-3)。
            residues = [Path(getattr(e, "_uj_residue", None) or tmp)]
            for rest_tmp, _ in tmps[idx + 1 :]:
                residues.append(_park_stale(rest_tmp, stale_dir) or rest_tmp)
            e.add_note("残片位置: " + " / ".join(str(r) for r in residues if r))
            raise


# ─────────────────────────── 账目读法 ───────────────────────────


def latest_by_seq(rows: list[dict]) -> dict:
    """每个 seq 取**最后一条**有业务含义的记录。

    ⛔ 不能按「出现过没有」判。`planned → undone → done`（撤销之后又重新执行过）
    是合法历史; 把「出现过 undone」当成永久终态, 会让重新执行出来的那一份永远
    撤不掉, 而且撤销会安静地返回「零件」。
    """
    out: dict = {}
    for r in rows:
        if r.get("state") in BUSINESS_STATES and "seq" in r:
            out[r["seq"]] = r
    return out


# ─────────────────────────── 批次账本 ───────────────────────────


class BatchJournal:
    """一个批次的账本。目录布局:

    <work_dir>/<batch_id>/journal.jsonl     一行一条记录
    <work_dir>/<batch_id>/backup/<rel>      op 之前的逐字节快照
    <work_dir>/<batch_id>/recycle/<rel>     「删」的留痕落点
    <work_dir>/<batch_id>/recycle/undone/   撤销 copy/link 时产物的去处
    <work_dir>/<batch_id>/stale/            写失败的 tmp 残片
    """

    def __init__(self, work_dir, batch_id: str, root=None, fingerprint: str | None = None):
        self.work_dir = Path(work_dir)
        self.batch_id = batch_id
        #: 创建目录的**上界**。缺省 = work_dir 的父目录必须已存在 (不造祖先链);
        #: 给了 root 则允许在 root 之内逐级创建 —— 调用方对 root 负责。没有这个
        #: 上界, 一个打错的 --work-dir 就会在 home 底下造出一串目录来。
        self.root = Path(root) if root is not None else None
        #: 这本账属于哪个 vault。撤销时拿当前 vault 的指纹核对。
        self.fingerprint = fingerprint
        self.batch_dir = self.work_dir / batch_id
        self.journal_path = self.batch_dir / JOURNAL_NAME
        self.backup_root = self.batch_dir / BACKUP_DIR
        self.recycle_root = self.batch_dir / RECYCLE_DIR
        self.undone_root = self.recycle_root / UNDONE_DIR
        self.stale_root = self.batch_dir / STALE_DIR
        self._tail_malformed = False
        self._tail_unterminated = False
        self._tail_bad_count = 0

    # ── 目录 ──────────────────────────────────────────────

    def mkdir_chain(self, target: Path) -> None:
        """从上界起**逐级**创建, 每级先验祖先无 symlink 再建。

        ⛔ 先验再建的次序不能倒 (split_preview.prepare_out_dir v3 的同一条教训):
        先 mkdir 会穿过 symlink 在物理目标处把目录创建出来, 形成「拒绝但已写」。
        """
        target = Path(target)
        if self.root is None:
            parent = target.parent
            if not parent.is_dir():
                raise JournalError(f"✗ 目标目录的父目录不存在, 拒绝创建祖先链: {parent}")
            chain = [target]
        else:
            if not self.root.is_dir() or self.root.is_symlink():
                raise JournalError(f"✗ 创建上界不是普通目录: {self.root}")
            try:
                rel = target.resolve().relative_to(self.root.resolve())
            except ValueError as e:
                raise JournalError(f"✗ 目标落在允许创建的上界之外, 拒绝: {target}") from e
            chain, cur = [], self.root
            for part in rel.parts:
                cur = cur / part
                chain.append(cur)
        for d in chain:
            if os.path.lexists(str(d)):
                if d.is_symlink() or not d.is_dir():
                    raise JournalError(f"✗ 工作目录路径上的 {d} 不是普通目录, 拒绝写入")
            else:
                _SP.assert_symlink_free(d.parent)
                os.makedirs(str(d), exist_ok=True)
            _SP.assert_symlink_free(d)

    def ensure_dirs(self) -> None:
        """⛔ 只有准入守卫全部跑完才准调用 —— 拒绝路径必须连 work-dir 都不建。"""
        self.mkdir_chain(self.batch_dir)
        self.mkdir_chain(self.backup_root)
        self.mkdir_chain(self.recycle_root)

    # ── 读账 ──────────────────────────────────────────────

    def read_rows(self) -> list[dict]:
        """解析 journal。尾部的坏行 (掉电截断) 容忍并封口; 中间损坏一律拒绝。

        ⛔ 只按 "\\n" 切: splitlines() 会在 U+2028/U+2029/U+0085 处多切一刀, 把一条
        合法记录切成两条非法 JSON —— 那条记录就永远重放不掉了。
        """
        self._tail_malformed = False
        self._tail_unterminated = False
        self._tail_bad_count = 0
        if not self.journal_path.is_file():
            return []
        raw = self.journal_path.read_bytes().decode("utf-8", errors="replace")
        # ⛔ 「最后一条 JSON 完整、只差结尾换行」也要封口: 直接 O_APPEND 会让下一条
        # 记录接在它屁股后面, 两条一起变成读不懂的一行。
        self._tail_unterminated = bool(raw) and not raw.endswith("\n")
        parsed: list[dict | None] = []
        for line in raw.split("\n"):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                parsed.append(None)
                continue
            # ⛔ 认不出来的 state 算损坏, 不能静默忽略: 把 acting 写错一个字母,
            # 「最新状态」就悄悄退回 planned, 撤销会报「未执行, 无需还原」而产物还在
            # (Codex round-4 M1)。
            # ⛔ 而且它**不能**和「半行」共用同一个表示: 共用的话它就顺带继承了半行
            # 的尾部容忍 —— 一条完整但状态拼错的记录落在账尾就又被忽略了
            # (Codex round-5 HIGH-3)。两件性质不同的事, 表示也要分开。
            if not isinstance(obj, dict) or obj.get("state") not in KNOWN_STATES:
                got = obj.get("state") if isinstance(obj, dict) else "<不是对象>"
                raise JournalError(
                    f"✗ journal 第 {len(parsed) + 1} 条记录认不出来 (state={got!r}), "
                    f"这不是掉电截断, 拒绝在看不懂的账上继续动盘: {self.journal_path}"
                )
            parsed.append(obj)

        # 坏行什么时候算「没写完的尾巴」而不是「中间损坏」:
        #   · 它落在**最后一段**全是坏行的尾巴里 —— 掉电截断, 容忍;
        #   · 它被某条封口哨兵**明确覆盖** —— 当初封的就是它, 永远容忍。
        # ⛔ 覆盖面必须是哨兵当初记下的**条数**, 不能是「往前跨过任意多条坏行」:
        # 否则一条本来完整的业务行后来损坏了, 只要它紧挨着那段旧的封口区, 就会被
        # 一起放过 —— 最新状态悄悄退回上一步, 撤销报「未执行」而产物还在
        # (Codex round-4 H3)。
        covered: set[int] = set()
        for idx, obj in enumerate(parsed):
            if not (isinstance(obj, dict) and obj.get("state") == STATE_TAIL_SEALED):
                continue
            n = obj.get("sealed_bad_count")
            # ⛔ 没有计数的哨兵**只覆盖它紧邻的那一条**坏行。曾经为「旧账本兼容」放宽成
            # 「往前跨过整段连续坏行」—— 那正是 round-4 H3 判为缺陷的语义, 等于把一条已判
            # HIGH 的安全性质换掉, 换来的兼容面还是空集（本工具尚未发布, 无旧账本）。
            # 独立复核 M-2 实证: 放宽后「后来才损坏的完整 acting 行」会被静默吞掉,
            # 撤销报「未执行」而产物还在, 之后整批彻底卡死。
            n = int(n) if isinstance(n, int) and n > 0 else 1
            j = idx - 1
            while n > 0 and j >= 0 and parsed[j] is None:
                covered.add(j)
                n -= 1
                j -= 1
        trailing_from = len(parsed)
        while trailing_from > 0 and parsed[trailing_from - 1] is None:
            trailing_from -= 1
        for idx, obj in enumerate(parsed):
            if obj is not None:
                continue
            if idx in covered or idx >= trailing_from:
                continue
            raise JournalError(
                f"✗ journal 中间存在损坏记录 (第 {idx + 1} 条可解析行), 这不是掉电截断, "
                f"拒绝在看不懂的账上继续动盘: {self.journal_path}"
            )
        self._tail_bad_count = len(parsed) - trailing_from
        self._tail_malformed = self._tail_bad_count > 0
        return [o for o in parsed if o is not None]

    def seal_tail_if_needed(self) -> bool:
        """给上一次没写完的尾巴封口, 然后才允许继续追加。

        两种没写完:
          · 尾行**解析不了**（写到一半掉电）—— 补换行终结它, 再落一条哨兵行;
          · 尾行**解析得了但缺结尾换行** —— 只补一个换行即可。
        不封口而直接 O_APPEND, 新记录会接在旧尾巴后面连成一条烂行。
        """
        if not (self._tail_malformed or self._tail_unterminated):
            return False
        payload = b"\n"
        if self._tail_malformed:
            payload += json_line(
                {
                    "schema_version": SCHEMA_VERSION,
                    "state": STATE_TAIL_SEALED,
                    #: 这条哨兵**明确覆盖**它前面这么多条坏行 —— 覆盖面写死, 免得
                    #: 后来新坏的行蹭着旧封口区被一起放过。
                    "sealed_bad_count": int(getattr(self, "_tail_bad_count", 1) or 1),
                    "note": "上一条记录写到一半 (掉电/中断), 已封口忽略",
                    "sealed_at_utc": utc_now_iso(),
                }
            )
        append_bytes(self.journal_path, payload)
        self._tail_malformed = False
        self._tail_unterminated = False
        self._tail_bad_count = 0
        return True

    def load(self) -> list[dict]:
        """读账 + 封口 —— 任何要往账上追加的流程都必须先走这一步。"""
        rows = self.read_rows()
        if self.seal_tail_if_needed():
            rows = self.read_rows()
        return rows

    # ── 写账 ──────────────────────────────────────────────

    def _append(self, row: dict) -> dict:
        row = dict(row)
        row.setdefault("schema_version", SCHEMA_VERSION)
        row.setdefault("batch_id", self.batch_id)
        if self.fingerprint is not None:
            row.setdefault("vault_fingerprint", self.fingerprint)
        row.setdefault("ts_utc", utc_now_iso())
        append_bytes(self.journal_path, json_line(row))
        return row

    def plan(
        self,
        *,
        seq: int,
        op: str,
        stable_id: str,
        src: str,
        dst: str,
        dst_base: str,
        sha256_before: str,
        mtime_ns_before: int,
        mode_before: int | None,
        backup: str | None,
        prov_meta: dict | None = None,
        dir_mtimes: dict | None = None,
        created_dirs: list | None = None,
        meta: dict | None = None,
    ) -> dict:
        if op not in OPS:
            raise JournalError(f"✗ 未知动作: {op!r}")
        return self._append(
            {
                "seq": seq,
                "state": STATE_PLANNED,
                "op": op,
                "stable_id": stable_id,
                "src": src,
                "dst": dst,
                "dst_base": dst_base,
                "sha256_before": sha256_before,
                "mtime_ns_before": mtime_ns_before,
                "mode_before": mode_before,
                "backup": backup,
                #: 本条会写进产物的那份溯源 meta。记下来是为了让「我这一步写出来
                #: 应该长什么样」可以**重算**（落点归属判定要用）。
                "prov_meta": dict(prov_meta) if prov_meta else None,
                # 本条会改动条目集合的那几个目录 —— 撤销时一并还原它们的 mtime。
                "dir_mtimes": dict(dir_mtimes or {}),
                # 本条**新建**出来的目录。撤销不会删掉它们 (默认路径 0 物理删除),
                # 但必须在回执里说出来, 而不是让「全树回到原样」这句话悄悄失真。
                "created_dirs": list(created_dirs or []),
                "meta": meta or {},
            }
        )

    def commit(
        self,
        entry: dict,
        *,
        sha256_after: str | None,
        mtime_ns_after: int | None,
        provenance: str | None = None,
        inode: int | None = None,
        dir_mtimes_at_act: dict | None = None,
        dir_mtimes_after: dict | None = None,
    ) -> dict:
        row = dict(entry)
        row["state"] = STATE_DONE
        row["sha256_after"] = sha256_after
        row["mtime_ns_after"] = mtime_ns_after
        row["provenance"] = provenance
        row["inode"] = inode
        #: op **之后**各目录的 mtime。撤销时要拿它和上一条的「之前」串成一条链,
        #: 链没断且现值等于最后一环, 才敢把时间改回批前值。
        #: **动手那一刻**各目录的 mtime。plan 行里的「之前」可能是上一次跑留下的
        #: 陈旧读数（续跑场景）, 两者不等即说明这一步开工前目录已被人动过 ——
        #: 那段时间不在任何一步的账里, 目录时间就不能改回批前值。
        row["dir_mtimes_at_act"] = dict(dir_mtimes_at_act or {})
        row["dir_mtimes_after"] = dict(dir_mtimes_after or {})
        row.pop("ts_utc", None)
        return self._append(row)

    # ── 备份 ──────────────────────────────────────────────

    def backup(self, src_abs: Path, src_rel: str) -> tuple[str, str, int, int]:
        """op 之前的逐字节快照 —— undo 的真相源。
        返回 (备份相对路径, sha, mtime_ns, mode)。"""
        src_abs = Path(src_abs)
        st = os.lstat(str(src_abs))
        dst = self.backup_root / src_rel
        if self.root is not None:
            self.mkdir_chain(dst.parent)
        else:
            os.makedirs(str(dst.parent), exist_ok=True)
        _SP.assert_symlink_free(dst.parent)
        if is_symlink(dst):
            raise JournalError(f"✗ 备份落点是一条 symlink, 拒绝跟随: {dst}")
        before = sha256_file(src_abs)
        # ⛔ 经 tmp 再 os.replace 只保住了「别处的硬链接」; 备份路径上若是一份**独立的
        # 用户文件**, os.replace 照样把它的目录项换掉。所以先判归属: 与源逐字节相同
        # 就是我们自己上一次写的备份(直接沿用), 否则挪进 stale/ 留痕再写。
        if os.path.lexists(str(dst)):
            # ⛔ 沿用既有备份还要求 nlink == 1: 内容一样但与别处共享 inode 的话,
            # ① 我们的 utime 会改到用户那份文件的时间, ② 用户以后编辑那份文件会
            # 连唯一的备份一起改掉 —— 备份就不再是独立快照 (Codex round-4 H2)。
            if dst.is_file() and os.lstat(str(dst)).st_nlink == 1 and sha256_file(dst) == before:
                os.utime(str(dst), ns=(st.st_mtime_ns, st.st_mtime_ns))
                return f"{BACKUP_DIR}/{src_rel}", before, st.st_mtime_ns, st.st_mode
            os.makedirs(str(self.stale_root), exist_ok=True)
            _SP.assert_symlink_free(self.stale_root)
            os.replace(str(dst), str(free_path(self.stale_root / dst.name)))
        copy_file_atomically(src_abs, dst, self.stale_root)
        os.utime(str(dst), ns=(st.st_mtime_ns, st.st_mtime_ns))
        if sha256_file(dst) != before:
            raise JournalError(f"✗ 备份与原件不一致, 拒绝继续 (备份不可信就等于没有退路): {src_rel}")
        return f"{BACKUP_DIR}/{src_rel}", before, st.st_mtime_ns, st.st_mode

    # ── 归属判定 ──────────────────────────────────────────

    def dst_abs(self, row: dict, vault: Path) -> Path:
        base = self.batch_dir if row.get("dst_base") == BASE_BATCH else Path(vault)
        return safe_join(base, row["dst"], what="落点")

    def backup_abs(self, row: dict):
        return safe_join(self.batch_dir, row["backup"], what="备份路径") if row.get("backup") else None

    def owned_product(self, dst, row: dict) -> bool:
        """落点上的这份东西是不是本批次造的 —— 只用可计算的等式, 不用启发式。

        · `done` 行：比 `sha256_after`（那就是我们写完之后的实测值）。
        · `acting` 行：还没记 after, 但期望值算得出来 ——
            ① 与备份逐字节相同（主动作做了、溯源还没写）, 或
            ② 等于「把备份按账上那份 prov_meta 渲染一遍」的结果（溯源也写完了）。
        · `planned` 行：**一律不认领**。那时候主动作还没开始, 落点上按定义不该有我们
          的东西; 认了就等于把用户恰好同字节的独立文件当成自家产物 (Codex round-3 H2)。
        ⛔ 绝不用「全文里出现了 batch_id」这类判据: 用户在保留印记的前提下改了正文,
        它照样为真, 而那份改动会被我们覆盖掉。
        """
        dst = Path(dst)
        state = row.get("state")
        if state == STATE_DONE:
            if is_symlink(dst) or not Path(dst).is_file():
                return False
            return bool(row.get("sha256_after")) and sha256_file(dst) == row["sha256_after"]
        if state != STATE_ACTING:
            return False
        return self.looks_like_our_product(dst, row)

    def looks_like_our_product(self, path, row: dict) -> bool:
        """这份内容是不是「本批这一步写出来的样子」—— 两条可计算的等式。"""
        path = Path(path)
        if is_symlink(path) or not path.is_file():
            return False
        if row.get("sha256_after") and sha256_file(path) == row["sha256_after"]:
            return True
        if not row.get("sha256_before"):
            return False
        if sha256_file(path) == row["sha256_before"]:
            return True
        bak = self.backup_abs(row)
        meta = row.get("prov_meta")
        if not (meta and bak and bak.is_file() and not is_symlink(bak)):
            return False
        if sha256_file(bak) != row["sha256_before"]:
            return False  # 备份本身已不可信, 不拿它推期望值
        return path.read_bytes() == expected_after_provenance(bak.read_bytes(), path.suffix, meta)

    def recorded_receipt_shas(self, rows: list[dict], stem: str) -> dict:
        """账上记的「上一次这个 stem 的两份回执各是什么内容」。"""
        out: dict = {}
        for r in rows:
            if r.get("state") == STATE_RECEIPT_SHA and r.get("stem") == stem:
                out = dict(r.get("shas") or {})
        return out

    def record_receipt_shas(self, stem: str, shas: dict) -> None:
        """写完回执把它们的 sha 落账 —— 下一次据此认自家产物（尽力而为, 失败不致命）。

        ⛔ 必须**先封口再追加**。这是全模块唯一一个可能在 `load()` 自己抛过之后仍被
        调用到的 `_append` 点: 撤销失败时 `undo()` 里的 `load()` 抛在封口**之前**,
        异常被调用方接住后照样会来写回执。不封口直接 O_APPEND, 「完整但缺结尾换行」
        的末行会被新记录接在屁股后面粘成一条烂行 —— 工具在刚宣布「拒绝在看不懂的账
        上继续动盘」的那条路径上, 反手把这本账写坏了 (独立复核 round-2 D-2 实证)。

        ⛔ `read_rows()` 抛 ⇒ 这本账根本读不回来 ⇒ **一个字节都不写**。落不了账的
        代价只是下一次重跑把自家上一版回执多留一次痕 (保守侧), 远轻于弄坏账本。
        """
        try:
            self.read_rows()  # 设 _tail_*; 中间损坏会抛 ⇒ 下面两步都不做
            self.seal_tail_if_needed()
            self._append({"state": STATE_RECEIPT_SHA, "stem": stem, "shas": dict(shas)})
        except (OSError, JournalError):
            pass

    def mark_acting(self, entry: dict) -> dict:
        """在主动作**之前**落一条 acting 行 —— 「排期了」与「动过盘了」的分界。"""
        row = dict(entry)
        row["state"] = STATE_ACTING
        row.pop("ts_utc", None)
        return self._append(row)

    # ── 撤销 ──────────────────────────────────────────────

    def assert_is_ours(self, fingerprint: str | None = None) -> list[dict]:
        """纯读判定「这本账是不是我们自己这一批的」。**不写一个字节。**

        ⛔ 这是**往账本所在目录写任何东西的准入**: 调用方在这一步通过之前, 不得写
        回执、不得建 `stale/`、不得追加账目。

        原先撤销侧的零写契约挂在 `JournalNotOursError` 这个**异常类型**上 —— 那是
        钩子, 不是不变量。`read_rows()` 对「读得出行、但读不懂」的账抛的是普通
        `JournalError`, 于是它落进**会写回执**的那个 except: 往一个陌生目录写下
        undo-receipt.json/.md, 并把那里同名的用户文件无声挪进新建的 `stale/`
        (最终 HEAD 独立复核 H-B, boundary / no-delete / undo-order 三个维度各自撞到)。

        保护性改动要写成不变量: **先证明这是我们的批次目录, 才获得写它的资格**,
        而不是「捕获到某几个异常类时才不写」—— 后者只覆盖当时想到的那几条路径。
        """
        rows = self.read_rows()
        self._assert_is_a_batch_journal(rows)
        self._assert_bound_to(rows, fingerprint)
        return rows

    def _assert_bound_to(self, rows: list[dict], fingerprint: str | None) -> None:
        """这本账是不是这个 vault 的。

        ⛔ 判据是「**每一条**业务记录都绑着当前 vault」, 不是「当前指纹出现在集合里」——
        后者对「全部缺失」和「A/B 混合」两种账本都放行。
        """
        if fingerprint is None:
            return
        for r in rows:
            if r.get("state") not in BUSINESS_STATES:
                continue
            got = r.get("vault_fingerprint")
            if got != fingerprint:
                raise JournalNotOursError(
                    f"✗ 这本账不是当前 vault 的 (第 {r.get('seq')} 条记的是 {got!r}, "
                    f"现算 {fingerprint!r}), 拒绝拿别处的记录来动这里的文件: {self.journal_path}"
                )
            # ⛔ 同一个 vault 里还有「另一批」这回事: 把 A 批的账原样放进 B 批目录,
            # 只核 vault 的话 B 会拿 A 的落点去复核并报完成 (Codex round-4 H5)。
            if r.get("batch_id") != self.batch_id:
                raise JournalNotOursError(
                    f"✗ 这本账不是本批次的 (第 {r.get('seq')} 条记的是 {r.get('batch_id')!r}, "
                    f"本批 {self.batch_id!r}), 拒绝采信: {self.journal_path}"
                )

    def _assert_is_a_batch_journal(self, rows: list[dict]) -> None:
        """这个文件在**结构上**是不是一本批次账。

        ⛔ `_assert_bound_to` 的判据是「**每一条**业务记录都绑着当前 vault」——
        对 `rows == []` 是**空真**。而 `read_rows()` 又把「整份文件一条都解析不出
        JSON」归成「最后一段全是坏行的尾巴」(掉电截断), 于是**任意文本文件**都会被
        当成一本空账一路通过, 最后打印「✓ 已撤销 0 件」并 rc=0
        （全卡复核 HIGH-D 实测: 两行普通中文的 journal.jsonl 即可）。

        后果不是「没做事」, 是「指错了文件」与「这一批确实已经撤完了」在输出上
        **逐字相同** —— 用户据此认为已回滚, 而原批次的 move/recycle 仍然生效。
        """
        if not any(r.get("state") in BUSINESS_STATES for r in rows):
            raise JournalNotOursError(
                f"✗ 这个文件里没有任何一条批次记录, 它不是一本清仓账本, 拒绝采信: {self.journal_path}"
            )

    def _entries_to_undo(self, rows: list[dict]) -> list[dict]:
        """要还原的条目 = 每个 seq 的**最新**状态是 planned / acting / done 的那些。

        ⛔ `acting` 是后来为「排期了 / 动过盘了」的分界新引入的状态, 实现跟着改了、
        这句说明当初没改（全卡复核 L12, DD-13 名实一致）。少了它, 读这段的人会以为
        「已动盘未 done」那一件不在撤销面里 —— 而它恰恰是最需要被撤的那一类。
        """
        latest = latest_by_seq(rows)
        out = [r for r in latest.values() if r.get("state") in (STATE_PLANNED, STATE_ACTING, STATE_DONE)]
        return sorted(out, key=lambda r: r.get("seq", 0), reverse=True)

    def undo(self, vault, fingerprint: str | None = None) -> dict:
        """逆序还原。任一步对不上即停下, 不继续。"""
        vault = Path(vault)
        # ⛔ 绑定与结构校验必须发生在**任何一次写盘之前**。原先第一句就是
        # `rows = self.load()`, 而 `load()` 内含 `seal_tail_if_needed()` —— 它会往这个
        # 文件追加一条封口哨兵。于是「这本账不是这个 vault 的」这句拒绝, 是在**已经
        # 改写过对方账本之后**才说出口的（全卡复核 BLOCKER-B 实测: 453 → 454 字节）。
        # 先纯读判一遍, 通过了再走 load() 去封口。
        self.assert_is_ours(fingerprint)
        # ⛔ `load()` 之后**再判一遍**, 不是冗余: load() 会封口追加, 且两次读取之间
        # 文件可能被换掉。把两次读合并成一次快照会删掉这条重查契约。
        rows = self.load()
        self._assert_is_a_batch_journal(rows)
        self._assert_bound_to(rows, fingerprint)
        targets = self._entries_to_undo(rows)

        to_retime, skipped_dirs = self._dir_retime_plan(rows, vault)
        # ⛔ 从**全部**行汇总, 不是只看最新行: undone 行不带 created_dirs, 第二次
        # 撤销时「最新行」全成了 undone, 这条如实声明就被抹成空了 (round-3 L14)。
        created_dirs: list[str] = []
        for r in rows:
            for d in r.get("created_dirs") or []:
                if d not in created_dirs:
                    created_dirs.append(d)

        # ⛔ 逐件推进, 不用列表推导: 第 k 件抛出时, 前 k-1 件的盘面动作（产物挪进
        # recycle/undone/、原路径收尾、UNDONE 行落账）都已经做完了。异常里必须把
        # 「已经还原了几件」带出去, 否则回执会把 total/completed 写成 0, 用户据此
        # 以为「什么都没撤」（全卡复核 M7 实测: 盘上已还原 2 件, 回执写 0）。
        restored: list = []
        try:
            for row in targets:
                restored.append(self._undo_one(row, vault))
        except BaseException as e:
            try:
                e._uj_restored = list(restored)  # type: ignore[attr-defined]
            except Exception:
                pass
            raise

        retimed = []
        vault_real_now = Path(os.path.realpath(vault))
        for rel, ns in to_retime.items():
            # ⛔ **物理包含**在这里必须重查, 不能复用 plan 阶段的结论: 两次读取之间夹着
            # `_undo_one` 的整轮写盘, 祖先目录可能已被换成指向 vault 外的 symlink。
            # 负控实测: 只中和 plan 那一道, 这一道会独自拦住 ⇒ 它是真承重的。
            #
            # 形状(safe_join)则不同: 键已在 `_clean` 里过过同一个函数、同一个字符串,
            # 这里再调不会有第二种结果。所以它是**构造路径**, 不是设门 —— 不把它写成
            # 「重查契约」(DD-13 名实一致; 负控点名它时不红, 已如实降级)。
            d = safe_join(vault, rel, what="目录时间的目录")
            real_d = Path(os.path.realpath(d))
            if real_d != vault_real_now and vault_real_now not in real_d.parents:
                skipped_dirs.append({"dir": rel, "why": "撤销过程中它被解析到了 vault 之外"})
                continue
            if d.is_dir() and not is_symlink(d):
                # ⛔ 目录时间还原是**装饰性**的, 它失败不得否决整批撤销。此刻材料已经
                # 还原完毕, 若让 OSError(权限/只读卷/ENOENT 竞态) 逃出去, 它会落进
                # run_undo_mode 那个会写失败回执的 except —— 而 `_uj_restored` 只挂在
                # `_undo_one` 那圈循环上, 这里抛出时它不存在 ⇒ partial 为空 ⇒ 回执把
                # 「已还原 N 件」写成「已还原 0 件」, 且 done 行已全部变 undone,
                # 再跑多少次都收敛不回来 (delta 复核 MEDIUM-4)。
                # 与 HIGH-1 同一条原则: 装饰性字段的失败只登记, 不升级成整批失败。
                try:
                    os.utime(str(d), ns=(int(ns), int(ns)))
                # ⛔ 不能只接 OSError: `_clean` 的 int() 对 10**30 是**成功**的, 到
                # os.utime 才抛 **OverflowError**（"timestamp out of range for
                # platform time_t", 本机实测）—— 它不是 OSError, 会原样逃出去,
                # 于是这条修复在最容易触发的那个输入上根本不生效。
                except (OSError, OverflowError, ValueError) as e:
                    skipped_dirs.append({"dir": rel, "why": f"改不动它的时间, 材料本身已还原: {e}"})
                else:
                    retimed.append(rel)
            else:
                skipped_dirs.append({"dir": rel, "why": "撤销过程中它不再是普通目录"})

        # ⛔ 「上一次已经撤掉的那几件」也要带回去。第二次跑同一条 `--undo` 是文档承诺的
        # 幂等空操作, 但回执不能因此变成「共 0 件」—— 它写的是同一个 stem, 会把上一次
        # 那份**记着产物停放位置**的回执原地换掉, 而 undone 行本身不记停放位置, 于是
        # 「我的东西去哪了」从此无处可查（全卡复核 M5 实测）。执行侧对同一个坑做了回填
        # (run_apply 从账上重建 results), 撤销侧原先没有。
        already: list = []
        for r in latest_by_seq(rows).values():
            if r.get("state") == STATE_UNDONE:
                already.append({"seq": r.get("seq"), "op": r.get("op"), "action": "上一次已撤销"})
        return {
            "ok": True,
            "batch_id": self.batch_id,
            "restored": restored,
            "already_undone": sorted(already, key=lambda x: x.get("seq") or 0),
            "dirs_retimed": sorted(retimed),
            "dirs_not_retimed": skipped_dirs,
            "dirs_left_behind": sorted(created_dirs),
        }

    def _dir_retime_plan(self, rows: list[dict], vault: Path):
        """哪些目录的时间可以改回批前值。

        ⛔ 「现值 == 最后一次操作后的值」只证明**最后一次操作之后**没人动过, 不证明
        整个批次期间没人动过。所以要把每一步的「之前 / 之后」串成一条链: 后一步的
        「之前」必须等于前一步的「之后」, 链不断、且现值等于最后一环, 才敢改。
        """
        # ⛔ 不能用 `latest_by_seq`: 撤销中途失败之后再跑一次时, 上一轮已还原那几件的
        # **最新**行全是 undone, 它们碰过的目录于是既进不了 `to_retime`、也进不了
        # `skipped` —— 回执的「目录时间」段对这些目录一个字都不说, 而它们的 mtime 确实
        # 没被还原（全卡复核 M4 实测: `归档` 在两张表里都不出现）。紧挨着的 `undo()`
        # 对 `created_dirs` 正是为了同一个原因改成「从**全部**行汇总」(round-3 L14)。
        latest: dict = {}
        for r in rows:
            if r.get("state") in (STATE_PLANNED, STATE_ACTING, STATE_DONE) and "seq" in r:
                latest[r["seq"]] = r
        chain: dict[str, list] = {}
        # ⛔ 必须在下面 chain 循环里的 `_clean` **调用之前**绑定: 它是这个函数的局部,
        # 放到循环之后赋值会让 `_clean` 撞上 UnboundLocalError。
        bad_dir_keys: dict[str, str] = {}
        for seq in sorted(latest):
            r = latest[seq]
            pre = r.get("dir_mtimes") or {}
            at_act = r.get("dir_mtimes_at_act") or {}
            post = r.get("dir_mtimes_after") or {}

            def _slot(rel: str, seq=seq):
                """⛔ 按 seq 取环, 不能盲取 [-1]: 某一步的 post 里若出现了它自己
                `pre` 中没有的目录（执行期间目录被改名重建）, 盲取会把那个读数写进
                **上一步**的环里, 于是撤销拿新目录的时间回填旧目录的批前值。"""
                bucket = chain.setdefault(rel, [])
                for item in bucket:
                    if item["seq"] == seq:
                        return item
                item = {"seq": seq, "pre": None, "at_act": None, "post": None}
                bucket.append(item)
                return item

            # ⛔ 账本里的目录**键**与**值**都是不可信输入, 但它们只驱动收尾那句
            # os.utime —— 一个装饰性字段。不过就**登记跳过**, 绝不抛。
            #
            # 上一版这里是 fail-closed 抛出, 照搬了 src/dst/backup 的口径。那是把
            # 两件后果完全不同的事混成一条: src/dst/backup 驱动**用户材料的搬动**,
            # 放行就等于把材料搬出 vault, 必须拒整批; 而目录时间放行最坏也只是
            # 「某个目录的 mtime 没回去」。抛出换来的是: 整批撤销被否决、用户材料
            # 卡在落点、CLI 没有任何跳过开关 ⇒ 这一批再也撤不回来, 而 stderr 还打
            # 「修好原因后再跑一次只会补做剩下的」这句不实的恢复建议。
            # 更糟的是抛出点落在**会写回执**那一支, 把上一次成功撤销留下的
            # undo-receipt 原地换成「共 0 件」——那正是 M5 专门修好的不变量。
            # （delta 复核 cf951eb4 判 HIGH-1 + MEDIUM ×3, 同一根因。）
            #
            # 安全性不依赖抛出: 跳过就**不会有任何 os.utime**, 越界写照样发生不了。
            def _clean(dct: dict | None, what: str) -> dict:
                out: dict[str, int] = {}
                for rel, ns in (dct or {}).items():
                    try:
                        safe_join(vault, rel, what="目录时间的目录")
                    except JournalError as e:
                        bad_dir_keys.setdefault(str(rel), f"账上的目录键形状不可信, 不动它的时间: {e}")
                        continue
                    try:
                        out[rel] = int(ns)
                    except (TypeError, ValueError, OverflowError):
                        # int() 对坏值抛的是 ValueError/TypeError, **两个 except 都不接**
                        # ⇒ 裸 traceback（delta 复核 MEDIUM-5）。
                        bad_dir_keys.setdefault(str(rel), f"账上这个目录的{what}不是一个时间数, 不动它的时间: {ns!r}")
                return out

            for rel, ns in _clean(pre, "操作前时间").items():
                _slot(rel)["pre"] = ns
            for rel, ns in _clean(at_act, "动手时时间").items():
                _slot(rel)["at_act"] = ns
            for rel, ns in _clean(post, "操作后时间").items():
                _slot(rel)["post"] = ns

        to_retime: dict[str, int] = {}
        skipped: list[dict] = []
        vault_real = Path(os.path.realpath(vault))
        for rel, why in bad_dir_keys.items():
            skipped.append({"dir": rel, "why": why})
        for rel, steps in chain.items():
            # ⛔ 账本里的目录键与 src/dst/backup 同属不可信输入, 且**同样驱动写盘**
            # (收尾那句 os.utime)。原先这里直接 `vault / rel`: pathlib 遇绝对路径会把
            # base 整个丢掉, `..` 交给内核解析, 而现存两道判据 (is_dir / 末段 is_symlink)
            # 对 `<vault>/../../../..` 全部放行 ⇒ os.utime 打到 vault 之外, 还 rc=0 把
            # 那条路径当成功项列进回执 (最终 HEAD 独立复核 H-A, 四个维度各自撞到)。
            #
            # 两类问题分开处置, 不要混成一句「已不是普通目录」(DD-13 名实一致):
            #   · **键的形状**来自账本 = 被人改过 ⇒ 与 src 同口径 fail-closed 拒整批。
            #     这一步在 `_undo_one` 动用户材料**之前**, 拒绝时用户材料一件没动。
            #   · **目录的当下状态**(不再是目录 / 成了 symlink / 祖先链被换) 是运行期
            #     变化, 不是篡改 ⇒ 登记跳过, 不拒整批。
            # 键已在 `_clean` 里过过同一个 safe_join, 这里是**构造路径**不是设门 ——
            # 同函数同字符串, 不会有第二种结果 (DD-13: 别把不可能触发的分支写成门)。
            d = safe_join(vault, rel, what="目录时间的目录")
            if not d.is_dir() or is_symlink(d):
                skipped.append({"dir": rel, "why": "已不是普通目录"})
                continue
            # ⛔ 词法在 vault 内不等于物理在 vault 内: os.utime 会跟随**祖先链**上的
            # symlink, 而末段 is_symlink 看不到祖先。用正向包含判定一次性覆盖所有位置,
            # 不去枚举「symlink 可能出现在第几段」(reference: O_NOFOLLOW 只管末段)。
            real_d = Path(os.path.realpath(d))
            if real_d != vault_real and vault_real not in real_d.parents:
                skipped.append({"dir": rel, "why": "物理解析后已不在 vault 内 (路径上有 symlink)"})
                continue
            steps = sorted(steps, key=lambda x: x["seq"])
            why = None
            for k, st in enumerate(steps):
                if st["pre"] is None:
                    why = f"第 {st['seq']} 件没留下操作前的目录时间, 无从证明这期间没人动过"
                    break
                if st["post"] is None:
                    why = f"第 {st['seq']} 件没留下操作后的目录时间 (那一步没记完账), 无从证明这期间没人动过"
                    break
                if st["at_act"] is not None and st["at_act"] != st["pre"]:
                    why = f"第 {st['seq']} 件排期之后、动手之前这个目录被动过"
                    break
                if k and steps[k - 1]["post"] != st["pre"]:
                    why = f"第 {steps[k - 1]['seq']} 件与第 {st['seq']} 件之间这个目录被动过"
                    break
            if why is None and d.stat().st_mtime_ns != steps[-1]["post"]:
                why = "执行之后这个目录被动过, 不改它的时间"
            if why:
                skipped.append({"dir": rel, "why": why})
                continue
            to_retime[rel] = steps[0]["pre"]
        return to_retime, skipped

    # ── 撤销一件 ──────────────────────────────────────────

    def _assert_backup_trustworthy(self, row: dict) -> Path:
        """⛔ 在**动手之前**验备份。事后再验太晚: 正确的产物已经被坏备份盖掉了。"""
        bak = self.backup_abs(row)
        if bak is None:
            raise JournalError(f"✗ 第 {row.get('seq')} 件账上没有备份路径, 无从还原")
        if is_symlink(bak) or not bak.is_file():
            raise JournalError(f"✗ 第 {row.get('seq')} 件的备份不在或不是普通文件: {bak}")
        _SP.assert_symlink_free(bak.parent)
        if sha256_file(bak) != row.get("sha256_before"):
            raise JournalError(f"✗ 第 {row.get('seq')} 件的备份已经和原件对不上了, 拒绝拿它去覆盖任何东西: {bak}")
        return bak

    def _finish_restore(self, row: dict, src: Path) -> None:
        """把原路径收尾到「与批前逐项相同」: 先验 → 权限 → 时间 → 复核。可重入。

        ⛔ 先验再动。chmod / utime 会**跟随 symlink**, 也会改到用户放在那个路径上的
        别的文件 —— 拒绝必须发生在动手之前, 否则「拒绝了」的同时已经改了别人的东西
        (Codex round-3 H1)。
        """
        if is_symlink(src) or not src.is_file():
            raise JournalError(f"✗ 第 {row.get('seq')} 件的原路径不是普通文件, 拒绝在它上面动手: {src}")
        actual = sha256_file(src)
        if actual != row.get("sha256_before"):
            raise JournalError(
                f"✗ 第 {row.get('seq')} 件的原路径上不是当初那一份 (当前 {actual[:12]}… ≠ 原 "
                f"{str(row.get('sha256_before'))[:12]}…), 拒绝在它上面动手: {src}"
            )
        if row.get("mode_before") is not None:
            os.chmod(str(src), stat_mod.S_IMODE(int(row["mode_before"])))
        ns = int(row["mtime_ns_before"])
        os.utime(str(src), ns=(ns, ns))
        self._verify_restored(row, src)

    def _rewrite_from_backup(self, row: dict, src: Path) -> None:
        """用备份逐字节覆写原路径。

        ⛔ 不直接 `copyfile(bak, src)`: 它先截断再写, 中途失败会留下一份半截文件,
        而那份半截既不等于 before 也不等于 after, 重试时两边都不认 = 再也恢复不了
        (Codex round-3 H8)。换成原子替换还顺带解决了 0444 写不进去的问题 ——
        `os.replace` 要的是目录写权限, 不是文件写权限。写完由 _finish_restore
        按账上的 mode 盖回去。
        """
        bak = self._assert_backup_trustworthy(row)
        copy_file_atomically(bak, src, self.stale_root)

    def _park_product(self, row: dict, dst: Path) -> str:
        """copy/link 的产物移进 recycle/undone/ 留痕（不是删掉）。"""
        if self.root is not None:
            self.mkdir_chain(self.undone_root)
        else:
            os.makedirs(str(self.undone_root), exist_ok=True)
        # ⛔ 这个新落点也要过 symlink 守卫 —— 否则把 undone/ 指到 vault 外,
        # 撤销会把用户的材料搬出去并报成功。
        _SP.assert_symlink_free(self.undone_root)
        target = free_path(self.undone_root / f"{int(row['seq']):03d}-{dst.name}")
        assert_path_safe(target, what="撤销落点")
        os.replace(str(dst), str(target))
        return str(target.relative_to(self.batch_dir))

    def _undo_one(self, row: dict, vault: Path) -> dict:
        op = row.get("op")
        seq = row.get("seq")
        src = safe_join(vault, row["src"], what="原路径")
        if op == OP_SKIP:
            self._append({"seq": seq, "state": STATE_UNDONE, "op": op})
            return {"seq": seq, "op": op, "action": "无需还原"}
        if op not in OPS:
            raise JournalError(f"✗ 账上出现未知动作, 拒绝还原: {op!r}")

        _SP.assert_symlink_free(src.parent)
        if row.get("state") == STATE_PLANNED:
            # 排期了但主动作还没开始 —— 盘上没有本批留下的任何东西, 只需记账。
            # ⛔ 不能顺手去「收尾」原路径: 那会对用户放在那里的东西 chmod/utime。
            #
            # ⛔ 但「最新状态是 planned」只是**账上**的推断, 它的前提是「acting 行一定
            # 还在账上」。账本一旦在某条记录边界处被截短（同步回滚 / 外部工具 / 手改 ——
            # `outputs/` 就在 vault 内, 会被 Obsidian Sync 一类工具同步）, 已执行那一件的
            # acting/done 行就没了, 最新状态退回 planned —— 于是撤销对一件**确实搬走了**
            # 的材料说「未执行, 无需还原」, 报 rc=0 成功而材料仍躺在落点上
            # （全卡复核 M6 实测: 三件 move 的账截到第 4 条记录, `✓ 已撤销 2 件`,
            # 而乙.md / 丙.md 仍在 归档/）。撤销是后悔药, 这里必须看一眼盘再下结论。
            probe = self.dst_abs(row, vault) if row.get("dst") else None
            if probe is not None and os.path.lexists(str(probe)):
                raise JournalError(
                    f"✗ 账上说第 {seq} 件没执行过, 但它的落点上确实有东西: {probe}\n"
                    f"  账本很可能被截短或改过（少了 acting/done 行）, 拒绝按「未执行」处理 ——"
                    f"按它处理会报成功而材料还在原地。请核对后再撤销。"
                )
            self._append({"seq": seq, "state": STATE_UNDONE, "op": op, "note": "未执行, 无需还原"})
            return {"seq": seq, "op": op, "action": "未执行, 无需还原"}

        dst = self.dst_abs(row, vault)

        # ── 落点已经不在了。三种可能, 都靠「原路径现在是什么」来分辨 ──
        #    ① 这一条根本没执行到（planned 写了、还没动盘）
        #    ② 上一次撤销已经还原、只是没来得及记账
        #    ③ 上一次撤销还原到一半（字节回来了, 时间/权限还没盖回去）
        #    ①②③ 的正确动作是同一个: 把原路径收尾到批前态, 然后记账。
        if not os.path.lexists(str(dst)):
            if is_symlink(src) or not src.is_file():
                raise JournalError(
                    f"✗ 第 {seq} 件的去处已不存在, 原路径也没有可用的原件, 无从还原: {dst}"
                    f"（备份仍在 {row.get('backup')}）"
                )
            actual = sha256_file(src)
            if actual != row.get("sha256_before"):
                # ⛔ planned/acting 行没有 sha256_after, 不能只认它: 统一走「像不像
                # 本批这一步写出来的样子」那两条等式 (Codex round-3 H7)。
                if op in OPS_TAKE_SOURCE and self.looks_like_our_product(src, row):
                    self._rewrite_from_backup(row, src)  # 溯源还留在上面, 用备份抹掉
                else:
                    raise JournalError(
                        f"✗ 第 {seq} 件的去处已不存在, 而原路径上的内容既不是原件也不是本批次的产物, 拒绝继续: {src}"
                    )
            self._finish_restore(row, src)
            self._append({"seq": seq, "state": STATE_UNDONE, "op": op})
            return {"seq": seq, "op": op, "action": str(src.relative_to(vault))}

        # ── 落点还在 ──
        if is_symlink(dst):
            raise JournalError(f"✗ 第 {seq} 件的落点现在是一条 symlink, 拒绝跟随: {dst}")
        _SP.assert_symlink_free(dst.parent)
        if not self.owned_product(dst, row):
            raise JournalError(
                f"✗ 第 {seq} 件的落点在执行之后被改动过, 还原会把改动一起搬走 / 让修改时间说谎, 拒绝继续: {dst}"
            )

        if op in OPS_LEAVE_SOURCE:
            # ⛔ 搬产物**之前**先确认原路径仍是当初那一份: 拒绝得越早, 被动过的东西
            # 越少 (Codex round-3 H1 的同族 —— 别在还没验之前先动手)。
            if is_symlink(src) or not src.is_file() or sha256_file(src) != row.get("sha256_before"):
                raise JournalError(f"✗ 第 {seq} 件的原路径已不是当初那一份, 撤销的前提不成立, 拒绝继续: {src}")
            where = self._park_product(row, dst)
        else:
            self._assert_backup_trustworthy(row)  # ⛔ 搬之前先验, 不是搬完再验
            if os.path.lexists(str(src)):
                raise JournalError(f"✗ 第 {seq} 件的原路径已被新的材料占用, 还原会覆盖它, 拒绝继续: {src}")
            os.makedirs(str(src.parent), exist_ok=True)
            os.replace(str(dst), str(src))
            if sha256_file(src) != row.get("sha256_before"):
                self._rewrite_from_backup(row, src)
            where = str(src.relative_to(vault))

        self._finish_restore(row, src)
        self._append({"seq": seq, "state": STATE_UNDONE, "op": op})
        return {"seq": seq, "op": op, "action": where}

    def _verify_restored(self, row: dict, src: Path) -> None:
        if is_symlink(src) or not src.is_file():
            raise JournalError(f"✗ 还原后原路径不是普通文件: {src}")
        actual = sha256_file(src)
        if actual != row.get("sha256_before"):
            raise JournalError(
                f"✗ 第 {row.get('seq')} 件还原后内容对不上 (当前 {actual[:12]}… ≠ 原 "
                f"{str(row.get('sha256_before'))[:12]}…), 拒绝继续: {src}"
            )
        st = src.stat()
        if st.st_mtime_ns != int(row["mtime_ns_before"]):
            raise JournalError(
                f"✗ 第 {row.get('seq')} 件还原后修改时间对不上 "
                f"(mtime_ns 当前 {st.st_mtime_ns} ≠ 记录 {row['mtime_ns_before']}), 拒绝继续: {src}"
            )
        want = row.get("mode_before")
        if want is not None and stat_mod.S_IMODE(st.st_mode) != stat_mod.S_IMODE(int(want)):
            raise JournalError(
                f"✗ 第 {row.get('seq')} 件还原后权限位对不上 "
                f"(当前 {stat_mod.S_IMODE(st.st_mode):o} ≠ 记录 {stat_mod.S_IMODE(int(want)):o}), "
                f"拒绝继续: {src}"
            )
