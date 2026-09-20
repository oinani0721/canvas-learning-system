#!/usr/bin/env python3
"""机器级安装副本（`~/Library` 下的 launchd plist + wrapper）的只读 DRIFT 校验器。

CARD-DEBT-10。与 `verify_vault_install.py` 的分工（DD-13 名实一致）: 那一支校验
**vault 内容**（manifest 的 `items`），本支校验 **机器级安装副本**（manifest 的
顶层 `machine_items`）—— 两支各解释各自那一个键, 不共享逻辑、不互改对方。四档
退出码与它逐字同口径（`verify_vault_install.py:79-82`）。

要防的那个坑: 这 6 件当初都是人工 `cp` 进去的, 仓库里没有任何东西记着「它们该长
什么样」。改了仓内源却忘了重装 = 复习链静默停摆（wrapper 源 :5 那句「改动后需重新
cp 安装」只是一句注释, 没有守门人）—— 2026-09-05 已真的发生过一次。

只读承诺（三道锁, 缺一把都不够）:
  1. `verify()` 及其调用链只 stat / 列目录 / 读字节。全文件的**写调用**被 AST 门
     钉死在 `_apply_reinstall` / `_write_report` 两个函数体内 —— 判据在
     `backend/tests/unit/test_verify_install_manifest.py::collect_write_call_owners`,
     它数的是 `ast.Call` 节点而不是文本（注释/字符串字面量骗不过它）。
  2. **调用图门**: 从 `verify` / `_verify_one` / `_verify_program` / `plan_reinstall`
     四个只读入口出发, 沿调用图不许走到那两个写者 —— 第 1 条是**调用点**判据, 它对
     「`verify()` 里加一行 `_write_report(...)`」完全无感（写调用还在写者体内）。
  3. `--reinstall --dry-run` 只打印计划, 行为门对 `--home` 整棵树做「相对路径 +
     sha256 + mode + 软链目标」全量快照, 跑前跑后必须逐项同。

`--apply` 对**真实 HOME** 还要显式 `--i-confirm-home-write`, 缺失即 EXIT_USAGE,
且该档在任何写入之前判定。「是不是真实 HOME」按 **inode 身份**判（`st_dev, st_ino`）
而不是路径字符串 —— macOS 的启动卷大小写不敏感, `/users/x`、`/USERS/X`、
`/System/Volumes/Data/Users/x` 是同一个目录却是四个不同的字符串, 字符串判据挡不住
其中任何一个（内部对抗复核 2026-09-19 实测四种拼法全部写穿）。

写入落点同样按**物理位置**判: `_apply_reinstall` 在写之前要求目标父目录 resolve 之后
仍在 `--home` 之下 —— 只查叶子是不是软链挡不住「`<home>/Library` 本身是软链」这种
祖先别名（`os.replace` 换目录项的纪律只对叶子有效）。

⛔ 本脚本不调用 `launchctl` 任何子命令 —— 重装之后的重载是人的动作, 不是它的（移交另立卡）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

# 四档退出码 —— 与 verify_vault_install.py:79-82 逐字同口径。
EXIT_OK = 0
EXIT_MISSING = 1  # 只缺东西
EXIT_MISMATCH = 2  # 内容漂 / 读不动 / 解析不动 / 指向的程序体不对
EXIT_USAGE = 3  # 用法或配置错

VALID_ROLES = frozenset({"launchd-plist", "launchd-wrapper"})
VALID_MANAGED = frozenset({"repo", "external"})
REQUIRED_ITEM_KEYS = ("label", "role", "managed", "source", "install", "origin", "note")
OPTIONAL_ITEM_KEYS = ("program_source",)
# 与 test_vault_install_manifest.py:261 的 banned 同口径, 外加 version:
# 「版本」由本校验器在报告里打 source_blob + 两侧 sha256, 不进 manifest
# （G2-6「活源即模板, manifest 不带内容基线」）。
BANNED_ITEM_KEYS = frozenset({"sha256", "sha", "checksum", "content", "bytes", "size", "hash", "version"})

# 安装侧状态。EXTERNAL-* 只报告、不计退出码（managed:external 的口径就是
# 「仓库不保管它的内容」）—— 但它们必须出现在报告正文, 且摘要单独计数,
# 否则「4 件全丢」会静默。
STATUS_MATCH = "MATCH"
STATUS_DRIFT = "DRIFT"
STATUS_MISSING = "MISSING"
STATUS_UNREADABLE = "UNREADABLE"
STATUS_EXTERNAL_PRESENT = "EXTERNAL-PRESENT"
STATUS_EXTERNAL_MISSING = "EXTERNAL-MISSING"

# 程序体侧状态（只对带 program_source 的条目算）。
PROGRAM_MATCH = "PROGRAM-MATCH"
PROGRAM_DRIFT = "PROGRAM-DRIFT"
PROGRAM_DANGLING = "PROGRAM-DANGLING"
PROGRAM_UNPARSEABLE = "UNPARSEABLE"
PROGRAM_SKIPPED = "SKIPPED"  # plist 不在位 ⇒ 无从解析, 不计退出码

BLOCKING_STATUSES = frozenset({STATUS_DRIFT, STATUS_UNREADABLE, PROGRAM_DRIFT, PROGRAM_DANGLING, PROGRAM_UNPARSEABLE})

# 这一族全是 KB 级的 plist / wrapper。设上限是为了让「读不动」与「读不完」都有档位,
# 而不是把进程挂在一个 10 GB 的文件上。
MAX_READ_BYTES = 64 * 1024 * 1024
_MAX_ANCESTOR_HOPS = 256

DEFAULT_MANIFEST = Path(__file__).resolve().parent / "vault-install-manifest.json"
DEFAULT_HARNESS = Path(__file__).resolve().parent.parent


class ManifestError(Exception):
    """manifest 结构/取值问题 —— 归 EXIT_USAGE, 不是「校验不过」。"""


class UsageError(Exception):
    """参数组合或落点问题 —— 归 EXIT_USAGE, 在任何写入之前判定。"""


class ApplyError(Exception):
    """`--apply` 期间的写入失败。`applied` 记住失败之前**已经装好**的那几件。

    没有它的话, 多件计划中途失败 = 树处在半更新状态而报告根本没落盘, 只剩 stderr
    一行 —— 运维事后翻不出「到底装进去了哪几件」。
    """

    def __init__(self, message: str, applied: list[str] | None = None) -> None:
        super().__init__(message)
        self.applied = applied or []


class ReportWriteError(Exception):
    """报告落盘失败。"""


@dataclass(frozen=True)
class MachineItem:
    label: str
    role: str
    managed: str
    source: str | None
    install: str
    origin: str
    note: str
    program_source: str | None = None


@dataclass
class ItemResult:
    item: MachineItem
    install_abs: Path
    status: str
    source_abs: Path | None = None
    installed_sha256: str | None = None
    source_sha256: str | None = None
    source_blob: str | None = None
    reason: str | None = None
    program_status: str | None = None
    program_path: str | None = None
    program_rule: str | None = None
    program_sha256: str | None = None
    harness_source_abs: Path | None = None
    harness_sha256: str | None = None
    program_reason: str | None = None
    notes: list[str] = field(default_factory=list)


# ── 纯函数: 哈希 ────────────────────────────────────────────────


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _same_dir(left: Path, right: Path) -> bool:
    """两个路径是不是**同一个目录**（按 inode 身份, 不是按字符串）。

    `Path.resolve()` 展开软链但**不折叠大小写**, 而 macOS 启动卷默认大小写不敏感,
    还有 `/System/Volumes/Data/...` 这层 firmlink 拼法 —— `df` / Time Machine 打印的
    就是后者。所以 `a.resolve() == b.resolve()` 不是目录身份, `(st_dev, st_ino)` 才是。
    stat 不到时退回字符串比较（宁可判「是同一个」而多要一次确认, 也不放行）。
    """
    try:
        left_stat, right_stat = os.stat(str(left)), os.stat(str(right))
    except OSError:
        return left.resolve() == right.resolve()
    return (left_stat.st_dev, left_stat.st_ino) == (right_stat.st_dev, right_stat.st_ino)


def _err_text(exc: BaseException) -> str:
    """错误文本只要类型 + 内核给的那句话, **不要文件名**。

    `OSError.__str__()` 会把 filename 拼进去 —— 于是刚在上一行脱敏掉的路径,
    又原样从异常消息里漏回报告。`strerror` 不含文件名。
    """
    detail = getattr(exc, "strerror", None) or str(exc)
    return _safe_text(f"{type(exc).__name__}: {detail}")


def _safe_text(value: str) -> str:
    """让任何一段文本都能安全地进报告。

    macOS 允许软链目标 / 文件名不是合法 UTF-8, `os.readlink()` 会返回带代理字符的
    字符串; 把它原样拼进报告, 报告落盘时 `text.encode("utf-8")` 直接抛 UnicodeEncodeError
    —— 一个损坏的软链就能让整份报告写不出来。
    """
    return value.encode("utf-8", "backslashreplace").decode("utf-8")


def _presence(path: Path) -> tuple[bool, str | None]:
    """返回 (在不在, 问不出来的原因)。

    ⛔ `os.path.lexists()` 把 EACCES / ENOTDIR 一并吞成 False —— 「我问不出来」被压成
    「它不存在」, 于是退出码从承诺的「读不动 = 2」降成「只是缺东西 = 1」。
    这一族（把失败压成一个看起来正常的值）是本仓反复吃过的亏, 必须区分开。
    """
    try:
        os.lstat(str(path))
        return True, None
    except FileNotFoundError:
        return False, None
    except (OSError, ValueError) as exc:
        return False, _err_text(exc)


def _regular_file_problem(path: Path) -> str | None:
    """不是「普通文件」就给出理由。None = 可以放心读。

    ⛔ 必须在读之前问: 对一个没有写端的 FIFO 调 `read_bytes()` 会在内核里**永久阻塞**,
    `except OSError` 永远等不到（内部对抗复核实测 25 秒无输出无退出码）。一个校验器
    挂住比报错更糟 —— 定时任务会一直卡在那里。
    """
    try:
        info = os.stat(str(path))
    except (OSError, ValueError) as exc:
        # ValueError: 路径里含 NUL —— binary plist 完全可能带进来, 只捕 OSError
        # 会让它裸抛穿过 main 的两个 except, 解释器退 1 而非承诺的档位。
        return _err_text(exc)
    if not stat.S_ISREG(info.st_mode):
        return f"不是普通文件（st_mode={stat.filemode(info.st_mode)}）"
    if info.st_size > MAX_READ_BYTES:
        # 这一族文件是 KB 级的 plist 与 wrapper。把一个 10 GB 的东西整个读进内存
        # 算 sha 不是校验, 是把自己挂住 —— 门拿着 st_size 却不看, 等于白 stat 一次。
        return f"太大, 拒绝整读（{info.st_size} 字节 > 上限 {MAX_READ_BYTES}）"
    return None


def _under(target: Path, root: Path) -> bool:
    return target == root or root in target.parents


def _within_any_form(target: Path, root: Path) -> bool:
    """「这个落点是不是**碰得到**受管面」—— 字面与物理两种形态**任一**命中即算命中。

    用在禁止性判定（报告落点）上, 方向是保守多禁: 单看物理形态会漏掉「root 自己是
    软链」那一侧（root 被展开成链目标, 而 target 还是链路径, 两边对不上）; 单看字面
    形态会漏掉「用一条软链绕进去」。
    """
    for candidate in {target, _resolve_lenient(target)}:
        for base in {root, _resolve_lenient(root)}:
            if _under(candidate, base):
                return True
    # 两种**路径**形态一起看仍漏掉大小写别名: macOS 启动卷大小写不敏感而 resolve()
    # 不折叠大小写, `<harness>/SCRIPTS/x` 与 `<harness>/scripts/x` 是同一个目录却是
    # 两个字符串。补一层按 (st_dev, st_ino) 的身份比对: 沿 target 向上找到第一个
    # **已存在**的祖先, 与 root 是同一个 inode 就算命中。
    # ⚠️ 必须**逐级**比, 不能只比「第一个存在的祖先」: 大小写别名路径本身就存在
    # （`<harness>/SCRIPTS/launchd/x.plist` 在大小写不敏感卷上 lexists 为真）,
    # 只比它一级等于拿一个文件去跟一个目录比 inode, 恒不相等 ⇒ 门直接放行。
    for ancestor in [target, *target.parents]:
        if os.path.lexists(ancestor) and _same_dir(ancestor, root):
            return True
    return False


def _fd_within(fd: int, root: Path) -> bool:
    """「这个**已经打开的目录**在不在 root 里面」—— 全程用 fd 上溯, 不碰路径字符串。

    ⚠️ 为什么不能拿 `os.fstat(fd)` 去比 `os.stat(路径)`: 那是**检查之后**的两次观测,
    中间被换掉两边会一起变, 等于没比。沿 `os.open("..", dir_fd=…)` 一级级往上走,
    每一步都锚在上一步的 fd 上, 没有任何一次重新解析路径 —— 这才是钉死身份。
    """
    try:
        root_info = os.stat(str(root))
    except OSError:
        return False
    current = os.dup(fd)
    try:
        for _ in range(_MAX_ANCESTOR_HOPS):
            info = os.fstat(current)
            if (info.st_dev, info.st_ino) == (root_info.st_dev, root_info.st_ino):
                return True
            try:
                parent = os.open("..", os.O_RDONLY | os.O_DIRECTORY, dir_fd=current)
            except OSError:
                return False
            parent_info = os.fstat(parent)
            os.close(current)
            current = parent
            if (parent_info.st_dev, parent_info.st_ino) == (info.st_dev, info.st_ino):
                return False  # 走到文件系统根了
        return False
    finally:
        try:
            os.close(current)
        except OSError:
            pass


def _physically_within(target: Path, root: Path) -> bool:
    """「这个落点**确实**在受管面里面」—— 两边都物理解析后才算数。

    ⚠️ 与上面那个方向**相反**, 不能共用。允许性判定必须严格: 字面形态在
    `<home>/Library` 整个是一条指向树外的软链时照样「看起来在 home 下」, union
    口径会把写穿判成合法。这里只认 resolve 之后的物理位置。
    """
    return _under(_resolve_lenient(target), _resolve_lenient(root))


def _resolve_lenient(path: Path) -> Path:
    """路径不存在时也能解析（解析已存在的祖先, 末段原样拼回）。"""
    try:
        return path.resolve()
    except OSError:  # pragma: no cover — resolve(strict=False) 基本不抛
        return path.parent.resolve() / path.name


def _git_blob_sha1(data: bytes) -> str:
    """与 `git hash-object <file>` 逐字同的 blob id, 纯 Python 算。

    刻意不 shell out: 一个只读校验器不该为了一个 40 位字符串去 fork 一个
    「只差一个 `-w` 就能写仓库」的二进制, 那等于给自己的零写承诺开后门。
    等价性由 `test_git_blob_sha1_matches_real_git` 对真实 git 实测钉住。
    """
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ── manifest 读取与校验 ────────────────────────────────────────


def _require_str(value: object, what: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{what} 必须是非空字符串, 实为 {value!r}")
    return value


def _check_clean_str(value: object, what: str) -> str:
    """非空字符串 + 无 NUL + 可编码。

    `label` / `origin` / `note` 都会被原样渲染进报告 —— 只查「非空字符串」不够:
    一个不可编码的 label 会让报告落盘时抛 UnicodeEncodeError, 而那时已经晚了。
    """
    text = _require_str(value, what)
    _require_clean_text(text, what)
    return text


def _check_relative_source(value: str, what: str) -> str:
    if value.startswith("/") or value.startswith("~"):
        raise ManifestError(f"{what} 必须是仓内相对路径, 实为 {value!r}")
    if ".." in Path(value).parts:
        raise ManifestError(f"{what} 不得含 .. : {value!r}")
    _require_clean_text(value, what)
    return value


def _check_install_path(value: str, what: str) -> str:
    """安装路径必须 HOME 相对（`~/` 开头）。

    ⛔ 不许绝对路径: `test_manifest_has_no_absolute_paths_and_no_secrets_inline`
    （:251）对**整个 manifest 原文**断言不含 `/Users/`, 写绝对路径当场打红;
    更实质的理由是绝对 HOME 路径把「这台机器的用户名」钉进了可移植清单。
    """
    if not value.startswith("~/"):
        raise ManifestError(f"{what} 必须以 '~/' 开头（HOME 相对）, 实为 {value!r}")
    rest = value[2:]
    if not rest:
        raise ManifestError(f"{what} 缺少 '~/' 之后的路径: {value!r}")
    # ⛔ 余段本身必须是相对的。`~//Library/x` 的余段是 `/Library/x`,
    # 而 `home / "/Library/x"` 在 pathlib 里**丢掉左操作数**直接变 `/Library/x` ——
    # 安装路径就此脱离 --home, 读和写都落到树外（内部对抗复核实测端到端写穿）。
    parts = Path(rest).parts
    if Path(rest).is_absolute() or (parts and parts[0] == os.sep):
        raise ManifestError(f"{what} 的 '~/' 之后必须是相对路径, 实为 {value!r}")
    if ".." in parts:
        raise ManifestError(f"{what} 不得含 .. : {value!r}")
    if "." in parts:
        raise ManifestError(f"{what} 不得含 . 段（会让重复检测漏判）: {value!r}")
    _require_clean_text(value, what)
    return value


def _require_clean_text(value: str, what: str) -> None:
    """NUL 与不可编码字符一律归 manifest 错档 —— 与 `verify_vault_install.py` 的

    `_check_relative_segment` 同口径。不查的话 `Path(value).parts` 会抛裸 ValueError,
    穿过 main 的两个 except 直接让解释器退 1, 而契约承诺的是用法错档 3。
    """
    if "\x00" in value:
        raise ManifestError(f"{what} 含 NUL 字符: {value!r}")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ManifestError(f"{what} 不是可编码的 UTF-8: {value!r} — {exc}") from exc


def load_machine_items(path: Path | str) -> tuple[MachineItem, ...]:
    """读 manifest 的顶层 `machine_items` 并逐条校验 schema。

    读取阶段把 OSError / UnicodeDecodeError / ValueError 一并转成 ManifestError
    —— 照 `verify_vault_install.py::load_manifest` 的口径: 「manifest 指向一个
    目录 / 不可读 / 非 UTF-8」该归用法错档, 不该以未捕获异常终止。
    """
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest 不存在: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ManifestError(f"manifest 不是 UTF-8 文本: {path} — {exc}") from exc
    except OSError as exc:
        raise ManifestError(f"manifest 不可读: {path} — {exc}") from exc
    except ValueError as exc:
        raise ManifestError(f"manifest 不是合法 JSON: {path} — {exc}") from exc

    if not isinstance(raw, dict):
        raise ManifestError("manifest 顶层必须是对象")
    entries = raw.get("machine_items")
    if entries is None:
        raise ManifestError(f"manifest 缺少顶层 machine_items: {path}")
    if not isinstance(entries, list):
        raise ManifestError(f"machine_items 必须是列表, 实为 {type(entries).__name__}")
    if not entries:
        raise ManifestError("machine_items 为空列表 —— 空清单等于没有守门人")

    try:
        return _parse_machine_entries(entries)
    except ManifestError:
        raise
    except Exception as exc:  # 任何未预期异常也归用法错档, 不让它穿到解释器退 1
        raise ManifestError(f"machine_items 解析失败: {type(exc).__name__}: {exc}") from exc


def _parse_machine_entries(entries: list) -> tuple[MachineItem, ...]:
    items: list[MachineItem] = []
    seen_labels: set[str] = set()
    seen_installs: set[str] = set()
    for index, entry in enumerate(entries):
        what = f"machine_items[{index}]"
        if not isinstance(entry, dict):
            raise ManifestError(f"{what} 必须是对象, 实为 {type(entry).__name__}")
        banned = set(entry) & BANNED_ITEM_KEYS
        if banned:
            raise ManifestError(f"{what} 携带了内容基线字段 {sorted(banned)} —— sha 在校验时算, 不进 manifest")
        missing = [key for key in REQUIRED_ITEM_KEYS if key not in entry]
        if missing:
            raise ManifestError(f"{what} 缺少必需键 {missing}")
        unknown = set(entry) - set(REQUIRED_ITEM_KEYS) - set(OPTIONAL_ITEM_KEYS)
        if unknown:
            raise ManifestError(f"{what} 含未知键 {sorted(unknown)}")

        label = _require_str(entry["label"], f"{what} 的 label")
        _require_clean_text(label, f"{what} 的 label")
        if label in seen_labels:
            raise ManifestError(f"machine_items 有重复 label: {label!r}")
        seen_labels.add(label)

        role = _require_str(entry["role"], f"{what} 的 role")
        if role not in VALID_ROLES:
            raise ManifestError(f"{what} 的 role 必须 ∈ {sorted(VALID_ROLES)}, 实为 {role!r}")
        managed = _require_str(entry["managed"], f"{what} 的 managed")
        if managed not in VALID_MANAGED:
            raise ManifestError(f"{what} 的 managed 必须 ∈ {sorted(VALID_MANAGED)}, 实为 {managed!r}")

        source = entry["source"]
        if managed == "repo":
            source = _check_relative_source(_require_str(source, f"{what} 的 source"), f"{what} 的 source")
        elif source is not None:
            raise ManifestError(f"{what} 是 external, source 必须是 null, 实为 {source!r}")

        install = _check_install_path(_require_str(entry["install"], f"{what} 的 install"), f"{what} 的 install")
        # 去重键取**规范化之后**的路径: 守卫和下游消费方必须用同一个键,
        # 否则 `a/bin/x` 与 `a/./bin/x` 会当成两条而 expand_install 把它们合成一个。
        install_key = str(Path(install[2:]))
        if install_key in seen_installs:
            raise ManifestError(f"machine_items 有重复 install（规范化后）: {install!r}")
        seen_installs.add(install_key)

        program_source = entry.get("program_source")
        if program_source is not None:
            program_source = _check_relative_source(
                _require_str(program_source, f"{what} 的 program_source"),
                f"{what} 的 program_source",
            )
            if role != "launchd-plist":
                raise ManifestError(f"{what} 的 program_source 只对 launchd-plist 有意义")

        items.append(
            MachineItem(
                label=label,
                role=role,
                managed=managed,
                source=source,
                install=install,
                origin=_check_clean_str(entry["origin"], f"{what} 的 origin"),
                note=_check_clean_str(entry["note"], f"{what} 的 note"),
                program_source=program_source,
            )
        )
    return tuple(items)


def expand_install(install: str, home: Path) -> Path:
    """`~/a/b` → `<home>/a/b`。只认 `~/` 前缀, 且结果必须仍在 `<home>` 之下。

    这里的包含断言是**纵深防御**: load 时已经拒了绝对余段, 但这个函数同时是读路径和
    写路径的唯一入口, 它自己不该依赖「上游一定校验过」这个前提（docstring 曾声称
    「load 时已校验过」而 load 恰恰没校验这一条）。
    """
    if not install.startswith("~/"):
        raise ManifestError(f"install 必须以 '~/' 开头: {install!r}")
    resolved = home / install[2:]
    if not _under(resolved, home):
        raise ManifestError(f"install 展开后落在 --home 之外: {install!r} -> {resolved}")
    return resolved


# ── 只读校验 ──────────────────────────────────────────────────


def _read_bytes(path: Path) -> tuple[bytes | None, str | None]:
    """读字节。返回 (data, 失败原因) —— 「读不到」必须能被上层计成阻断,

    不能压成「没有这条数据」（把 OSError 吞成 None 再当 MATCH 处理, 就是
    「读不动的文件一律算没漂」这类假绿的来源）。
    """
    try:
        return path.read_bytes(), None
    except (OSError, ValueError) as exc:
        return None, _err_text(exc)


# launchd 里常见的解释器: `ProgramArguments = ["/bin/bash", "<脚本>"]` 这种形状,
# 真正要盯的是 [1] 那个脚本而不是 /bin/bash。清单外的情形一律按 launchd 本身的
# 规则取可执行体, 并把用了哪条规则打进报告, 不让口径藏在代码里。
INTERPRETER_NAMES = frozenset({"bash", "sh", "zsh", "dash", "ksh", "env", "python", "python3", "perl", "ruby", "node"})


def _redact(value: str) -> str:
    """把 `NAME=VALUE` 里的 VALUE 抹掉。

    ⛔ 报告要落盘、要贴进验收单 —— plist 的 ProgramArguments 里完全可能带着
    `API_KEY=...`。路径本身可以原样打（那正是要给人看的信息）, 但任何「等号右边」
    一律不进报告。
    """
    name, sep, _ = value.partition("=")
    return f"{name}=<redacted>" if sep else value


def _describe_args(argv: list) -> str:
    """只描述 ProgramArguments 的**形状**, 不打它的内容。

    原先出错时把整个列表 `{args!r}` 打进报告 —— 那就是凭据泄漏的那条路径。
    """
    return f"<{len(argv)} 个元素, 类型 {[type(a).__name__ for a in argv]}>"


def _resolve_program_target(
    parsed: dict,
) -> tuple[str | None, str | None, str | None, str | None]:
    """按 launchd 的规则取「这个任务实际会跑的那个文件」。

    返回 `(程序路径, 用了哪条规则, 错误原因, 解释器路径)`。

    launchd.plist(5): `Program` 在时它就是可执行体; 缺失时用 `ProgramArguments[0]`。
    本卡这 5 份 plist 都是 `["/bin/bash", "<脚本>"]`, 要盯的是 [1] —— 但直接写死
    「永远取 [1]」在没有 [1] 的 plist 上会把「形状不同」误报成解析失败。
    解释器路径单独返回, 因为「解释器本身不存在」时这个任务根本跑不起来, 不能因为
    第二个参数的内容对得上就判 PROGRAM-MATCH（Codex r1 MEDIUM-7）。

    ⛔ 所有错误原因只描述**形状**不回显内容 —— plist 里可能带着凭据。
    """
    program = parsed.get("Program")
    if program is not None and not isinstance(program, str):
        return None, None, f"Program 键不是字符串（实为 {type(program).__name__}）", None
    raw_args = parsed.get("ProgramArguments")
    argv: list[str] = []
    if raw_args is not None:
        if not isinstance(raw_args, list):
            return None, None, f"ProgramArguments 不是列表（实为 {type(raw_args).__name__}）", None
        if not all(isinstance(a, str) for a in raw_args):
            return None, None, f"ProgramArguments 含非字符串元素 {_describe_args(raw_args)}", None
        argv = list(raw_args)
    executable = program if program else (argv[0] if argv else None)
    if executable is None:
        return None, None, "既没有 Program 也没有可用的 ProgramArguments", None
    if Path(executable).name not in INTERPRETER_NAMES:
        return executable, ("Program" if program else "ProgramArguments[0]"), None, None

    # 解释器形态: 要跳过两类**不是程序路径**的元素 ——
    #   ① `env` 前面那串 `NAME=VALUE` 赋值（它们恰恰最可能带凭据）;
    #   ② `-c` / `-S` / `--login` 这类解释器选项。
    # ⚠️ 赋值判定不能写成 `"=" not in a.split("/")[0]`: 对 `a/b=<凭据>` 那一段取到的
    # 是 `a`（不含 =）, 于是它被当成程序路径留下来。环境赋值的名字里不会有 `/`,
    # 所以按「第一个 = 之前那段不含 /」判才对。
    def _is_assignment(item: str) -> bool:
        name, sep, _ = item.partition("=")
        return bool(sep) and "/" not in name

    rest = [a for a in argv[1:] if not _is_assignment(a) and not a.startswith("-")]
    if not rest:
        return None, None, f"解释器形态但没有可用的程序路径 {_describe_args(argv)}", None
    return rest[0], "interpreter+ProgramArguments[1]", None, executable


def _verify_program(item: MachineItem, install_abs: Path, harness: Path) -> dict[str, object]:
    """解析**已装** plist, 取出它实际会跑的那个文件, 按**内容**比对 harness 侧同名源。

    ⛔ 刻意不比路径字符串: 已装 plist 指的是主干树的绝对路径, 而校验器可能跑在
    另一棵 worktree 上 —— 按路径比 = 恒判漂移。所以比 sha256, 并在报告里把
    「它实际指向哪棵树」「用了哪条取值规则」原样打出来给人读。
    """
    out: dict[str, object] = {}
    present, presence_problem = _presence(install_abs)
    if presence_problem is not None:
        out["program_status"] = PROGRAM_UNPARSEABLE
        out["program_reason"] = f"连「plist 在不在」都问不出来 — {presence_problem}"
        return out
    if not present:
        out["program_status"] = PROGRAM_SKIPPED
        out["program_reason"] = "plist 不在位, 无从解析"
        return out

    problem = _regular_file_problem(install_abs)
    if problem is not None:
        out["program_status"] = PROGRAM_UNPARSEABLE
        out["program_reason"] = f"plist 读不了 — {problem}"
        return out
    data, read_problem = _read_bytes(install_abs)
    if data is None:
        out["program_status"] = PROGRAM_UNPARSEABLE
        out["program_reason"] = f"plist 不可读 — {read_problem}"
        return out
    try:
        parsed = plistlib.loads(data)
    except Exception as exc:  # plistlib 的失败类型随格式而异, 一律归 UNPARSEABLE
        out["program_status"] = PROGRAM_UNPARSEABLE
        # 只给类型: plistlib 的异常消息会把它读到的内容片段拼进去。
        out["program_reason"] = f"plist 解析失败 — {type(exc).__name__}"
        return out
    if not isinstance(parsed, dict):
        out["program_status"] = PROGRAM_UNPARSEABLE
        out["program_reason"] = "plist 顶层不是字典"
        return out

    raw_target, rule, rule_problem, interpreter = _resolve_program_target(parsed)
    if raw_target is None:
        out["program_status"] = PROGRAM_UNPARSEABLE
        out["program_reason"] = rule_problem
        return out
    out["program_rule"] = rule
    out["program_path"] = _redact(raw_target)
    if interpreter is not None:
        if not Path(interpreter).is_absolute():
            # ⛔ 不拿进程 cwd 补全解释器路径 —— 与下面对程序路径的口径同。
            # 原写法先 stat 再查绝对性, 于是「相对解释器」会按校验器**从哪个目录被
            # 调起**得出不同答案, 同样的磁盘内容换个 cwd 就翻档。
            out["program_status"] = PROGRAM_DANGLING
            out["program_reason"] = "plist 里的解释器路径不是绝对路径（launchd 要求绝对路径）"
            return out
        interpreter_problem = _regular_file_problem(Path(interpreter))
        if interpreter_problem is not None:
            out["program_status"] = PROGRAM_DANGLING
            out["program_reason"] = f"解释器本身读不了 {_redact(interpreter)} — {interpreter_problem}"
            return out

    target = Path(raw_target)
    harness_source = harness / str(item.program_source)
    out["harness_source_abs"] = harness_source
    if not target.is_absolute():
        # ⛔ 不拿进程 cwd 去补全: launchd 本身要求绝对路径, 而「相对路径」在校验器
        # 眼里会随它从哪个目录被调起而变出不同答案 —— 同样的磁盘内容, 换个 cwd
        # 就从 PROGRAM-MATCH 翻成 PROGRAM-DANGLING。这种判据不配当门。
        out["program_status"] = PROGRAM_DANGLING
        out["program_reason"] = "plist 里的程序路径不是绝对路径（launchd 要求绝对路径）"
        return out
    target_problem = _regular_file_problem(target)
    if target_problem is not None:
        out["program_status"] = PROGRAM_DANGLING
        out["program_reason"] = f"plist 指向的程序体读不了 — {target_problem}"
        return out
    target_data, target_read_problem = _read_bytes(target)
    if target_data is None:
        out["program_status"] = PROGRAM_DANGLING
        out["program_reason"] = f"程序体不可读 — {target_read_problem}"
        return out
    out["program_sha256"] = _sha256_bytes(target_data)
    harness_problem = _regular_file_problem(harness_source)
    if harness_problem is not None:
        out["program_status"] = PROGRAM_DANGLING
        out["program_reason"] = f"harness 侧源读不了 {harness_source} — {harness_problem}"
        return out
    harness_data, harness_read_problem = _read_bytes(harness_source)
    if harness_data is None:
        out["program_status"] = PROGRAM_DANGLING
        out["program_reason"] = f"harness 侧源不可读 {harness_source} — {harness_read_problem}"
        return out
    out["harness_sha256"] = _sha256_bytes(harness_data)
    out["program_status"] = PROGRAM_MATCH if out["program_sha256"] == out["harness_sha256"] else PROGRAM_DRIFT
    return out


def _verify_one(item: MachineItem, home: Path, harness: Path) -> ItemResult:
    install_abs = expand_install(item.install, home)
    result = ItemResult(item=item, install_abs=install_abs, status=STATUS_UNREADABLE)

    if item.managed == "repo":
        source_abs = harness / str(item.source)
        result.source_abs = source_abs
        source_shape = _regular_file_problem(source_abs)
        source_data, source_problem = (None, source_shape) if source_shape else _read_bytes(source_abs)
        if source_data is None:
            result.status = STATUS_UNREADABLE
            result.reason = f"仓内源不可读 {source_abs} — {source_problem}"
        else:
            result.source_sha256 = _sha256_bytes(source_data)
            result.source_blob = _git_blob_sha1(source_data)
            present, presence_problem = _presence(install_abs)
            if presence_problem is not None:
                result.status = STATUS_UNREADABLE
                result.reason = f"连「在不在」都问不出来 — {presence_problem}"
            elif not present:
                result.status = STATUS_MISSING
                result.reason = "安装副本不在位"
            elif install_abs.is_symlink():
                # 软链不是「一份副本」: 读它拿到的是别处的内容, 写它会写穿到别处。
                # 归阻断档而不是 MATCH —— 安装形态本身已经偏离。
                result.status = STATUS_UNREADABLE
                result.reason = _safe_text(f"安装副本是软链, 不是真副本（→ {os.readlink(install_abs)}）")
            elif _regular_file_problem(install_abs) is not None:
                result.status = STATUS_UNREADABLE
                result.reason = f"安装路径不是普通文件 — {_regular_file_problem(install_abs)}"
            else:
                installed_data, installed_problem = _read_bytes(install_abs)
                if installed_data is None:
                    result.status = STATUS_UNREADABLE
                    result.reason = f"安装副本不可读 — {installed_problem}"
                else:
                    result.installed_sha256 = _sha256_bytes(installed_data)
                    result.status = STATUS_MATCH if result.installed_sha256 == result.source_sha256 else STATUS_DRIFT
    else:
        present, presence_problem = _presence(install_abs)
        if presence_problem is not None:
            # 「问不出来」不是 external 的内容问题, 是环境问题 —— 归阻断档。
            # managed:external 的豁免只覆盖「仓库不保管它的内容」, 不覆盖
            # 「这块目录整个读不动」。
            result.status = STATUS_UNREADABLE
            result.reason = f"连「在不在」都问不出来 — {presence_problem}"
        elif not present:
            result.status = STATUS_EXTERNAL_MISSING
            result.reason = "external 件不在位（不计退出码, 但必须被看见）"
        else:
            result.status = STATUS_EXTERNAL_PRESENT
            shape_problem = _regular_file_problem(install_abs)
            if shape_problem is not None:
                result.reason = f"external 件读不了 — {shape_problem}"
            else:
                installed_data, installed_problem = _read_bytes(install_abs)
                if installed_data is None:
                    result.reason = f"external 件不可读 — {installed_problem}"
                else:
                    result.installed_sha256 = _sha256_bytes(installed_data)

    if item.program_source is not None:
        for key, value in _verify_program(item, install_abs, harness).items():
            setattr(result, key, value)
    return result


def verify(items: tuple[MachineItem, ...], home: Path, harness: Path) -> list[ItemResult]:
    """全量只读校验。⛔ 本函数及其调用链不得有任何写调用（AST 门钉死）。"""
    return [_verify_one(item, home, harness) for item in items]


def exit_code_for(results: list[ItemResult]) -> int:
    blocking = [r for r in results if r.status in BLOCKING_STATUSES or (r.program_status in BLOCKING_STATUSES)]
    if blocking:
        return EXIT_MISMATCH
    if any(r.status == STATUS_MISSING for r in results):
        return EXIT_MISSING
    return EXIT_OK


# ── 重装计划 ──────────────────────────────────────────────────


def plan_reinstall(results: list[ItemResult]) -> list[tuple[Path, Path, str]]:
    """只有 `managed: repo` 且状态 ∈ {DRIFT, MISSING} 的件进计划。

    external 件永不进（仓库不保管它的内容）; UNREADABLE 件也不进 —— 「读不动」
    的时候把源盖上去是拿猜测覆盖未知状态。
    """
    plan: list[tuple[Path, Path, str]] = []
    for result in results:
        if result.item.managed != "repo":
            continue
        if result.status not in (STATUS_DRIFT, STATUS_MISSING):
            continue
        if result.source_abs is None:
            continue
        plan.append((result.source_abs, result.install_abs, result.item.label))
    return plan


def _apply_reinstall(plan: list[tuple[Path, Path, str]], home: Path) -> list[str]:
    """本文件**唯一**会往 `--home` 树写字节的函数（另一个写者 `_write_report`
    只写报告, 且落点被 `--report` 的落点门挡在受管面之外）。

    三条纪律照抄 `verify_vault_install.py::_write_report`（:916-961）, 每条都对应
    一个实测出来的坏结果:
      - 临时名带 pid + 随机串, `O_EXCL` 创建; 失败意味着那个文件不是本次创建的,
        绝不清理它（无条件 unlink 会删掉别人的文件）;
      - `os.write` 会短写, 必须循环写满才换目录项, 否则发布一份截断的副本;
      - 换的是目录项（`os.replace`）而不是原地覆盖 —— 原地写会顺着别名写穿。

    **目录身份钉死（Codex r1 MEDIUM-6）**: 包含检查之后、写入之前, 有人可以把
    `<home>/Library` 换成一条指向树外的软链 —— 后面每一次按**路径**做的操作都会
    重新解析, 于是写到树外。所以这里先把父目录 `open(O_DIRECTORY)` 成一个 fd,
    核对它的 `(st_dev, st_ino)` 与刚才检查过的那个目录一致, 之后所有操作都走
    `dir_fd=` 与 `fchmod(fd)`, **不再出现任何一次按路径的解析**。
    残余窗口如实声明: 检查与 `open` 之间那一瞬仍可能被换, 但换了就会在 inode 核对
    那一步被抓住并拒写; 要把窗口降到零需要 `openat2(RESOLVE_BENEATH)`, macOS 没有。

    权限位口径与手工 `cp` 一致: 目标已在则保留它原有的权限位, 不在则取仓内源的。
    """
    applied: list[str] = []
    for source, dest, label in plan:
        parent = dest.parent
        # ⛔ 祖先别名检查。只查叶子是不是软链挡不住「<home>/Library 本身是软链」:
        # 那时 parent.is_dir() 从链穿过去返回 True, 临时文件、O_EXCL 创建、os.replace
        # 全都发生在链**目标**目录里。os.replace 换目录项的纪律只对叶子有效。
        if not _physically_within(parent, home):
            raise ApplyError(f"{label}: 安装目录物理位置在 --home 之外, 拒绝写入 —— {parent}", applied)
        tmp_name = f".{dest.name}.tmp-{os.getpid()}-{os.urandom(4).hex()}"
        parent_fd = None
        fd = None
        created = False
        try:
            data = source.read_bytes()
            if not parent.is_dir():
                os.makedirs(str(parent), exist_ok=True)
            parent_fd = os.open(str(parent), os.O_RDONLY | os.O_DIRECTORY)
            # 身份判定沿**这个 fd** 一级级上溯到 --home, 全程不再解析路径字符串。
            # 拿 fstat(fd) 去比 stat(同一个路径) 是两次事后观测, 中间被换掉两边会
            # 一起变 —— 那种比法看着严谨, 其实什么也没钉住。
            if not _fd_within(parent_fd, home):
                raise ApplyError(
                    f"{label}: 安装目录的物理位置不在 --home 之内, 拒绝写入 —— {parent}",
                    applied,
                )
            try:
                dest_info = os.lstat(dest.name, dir_fd=parent_fd)
            except FileNotFoundError:
                mode = os.stat(str(source)).st_mode & 0o777
            else:
                if stat.S_ISLNK(dest_info.st_mode):
                    raise ApplyError(f"{label}: 安装路径是软链, 拒绝写入 —— {dest}", applied)
                mode = dest_info.st_mode & 0o777
            fd = os.open(tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode, dir_fd=parent_fd)
            created = True
            written = 0
            while written < len(data):
                chunk = os.write(fd, data[written:])
                if chunk <= 0:  # pragma: no cover — 正常内核不会返回 0
                    raise OSError("os.write 返回 0, 无法写满安装副本")
                written += chunk
            os.fchmod(fd, mode)  # 抵消 umask; 走 fd 而不是路径, 不给别名留缝
            os.close(fd)
            fd = None
            os.replace(tmp_name, dest.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        except (OSError, ValueError) as exc:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if created and parent_fd is not None:  # 只清理本次真正创建的那一个
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
                except OSError:
                    pass
            raise ApplyError(f"{label}: 安装失败 {dest} — {_err_text(exc)}", applied) from exc
        finally:
            if parent_fd is not None:
                try:
                    os.close(parent_fd)
                except OSError:
                    pass
        applied.append(label)
    return applied


def _write_report(path: Path, text: str) -> None:
    """写新 inode 再换目录项 —— 口径同 `verify_vault_install.py::_write_report`。"""
    data = text.encode("utf-8")
    tmp = path.parent / f".{path.name}.tmp-{os.getpid()}-{os.urandom(4).hex()}"
    fd = None
    created = False
    try:
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        written = 0
        while written < len(data):
            chunk = os.write(fd, data[written:])
            if chunk <= 0:  # pragma: no cover
                raise OSError("os.write 返回 0, 无法写满报告")
            written += chunk
        os.close(fd)
        fd = None
        os.replace(str(tmp), str(path))
    except OSError as exc:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if created:
            try:
                os.unlink(str(tmp))
            except OSError:
                pass
        raise ReportWriteError(f"报告落盘失败: {path} — {exc}") from exc


# ── 报告 ──────────────────────────────────────────────────────


def _fmt(value: object) -> str:
    return "-" if value is None else str(value)


def render_report(
    results: list[ItemResult],
    plan: list[tuple[Path, Path, str]],
    *,
    home: Path,
    harness: Path,
    manifest: Path,
    mode: str,
    applied: list[str] | None = None,
    post_plan: list[tuple[Path, Path, str]] | None = None,
    apply_error: str | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# 机器级安装副本校验报告 — CARD-DEBT-10")
    lines.append(f"manifest={manifest}")
    lines.append(f"home={home}")
    lines.append(f"harness={harness}")
    lines.append(f"mode={mode}")
    lines.append("")
    lines.append("## 逐件状态")
    for result in results:
        item = result.item
        lines.append(f"- label={item.label} role={item.role} managed={item.managed} status={result.status}")
        lines.append(f"    install={item.install} -> {result.install_abs}")
        lines.append(
            f"    source={_fmt(item.source)} installed_sha256={_fmt(result.installed_sha256)} "
            f"source_sha256={_fmt(result.source_sha256)} source_blob={_fmt(result.source_blob)}"
        )
        if result.reason:
            lines.append(f"    reason={result.reason}")
        if item.program_source is not None:
            lines.append(f"    program_status={_fmt(result.program_status)} program_source={item.program_source}")
            lines.append(
                f"    program_path={_fmt(result.program_path)} "
                f"program_rule={_fmt(result.program_rule)} "
                f"program_sha256={_fmt(result.program_sha256)}"
            )
            lines.append(
                f"    harness_source={_fmt(result.harness_source_abs)} harness_sha256={_fmt(result.harness_sha256)}"
            )
            if result.program_reason:
                lines.append(f"    program_reason={result.program_reason}")
    lines.append("")

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
        if result.program_status is not None:
            counts[result.program_status] = counts.get(result.program_status, 0) + 1
    lines.append("## 摘要")
    for name in sorted(counts):
        lines.append(f"{name}={counts[name]}")
    external_missing = counts.get(STATUS_EXTERNAL_MISSING, 0)
    if external_missing:
        lines.append(
            f"⚠️ EXTERNAL-MISSING={external_missing} —— 按 managed:external 的口径不计"
            "退出码（仓库不保管它的内容）, 但它就在上面这份正文里, 不会静默。"
        )
    lines.append("")

    lines.append("## 重装计划")
    if not plan:
        lines.append("PLAN 空（没有 managed:repo 的件处在 DRIFT/MISSING）")
    for source, dest, label in plan:
        lines.append(f"PLAN cp {source} -> {dest}  # {label}")
    if mode == "dry-run":
        lines.append("DRY-RUN 未写入任何字节")
    if applied is not None:
        lines.append("")
        lines.append("## 已执行")
        if not applied:
            lines.append("APPLIED 空")
        for label in applied:
            lines.append(f"APPLIED {label}")
    if post_plan is not None:
        lines.append("")
        lines.append("## 重装后复核")
        if not post_plan:
            lines.append("POST-PLAN 空（幂等: 再跑一次没有任何件需要重装）")
        for source, dest, label in post_plan:
            lines.append(f"POST-PLAN cp {source} -> {dest}  # {label}")
    if apply_error is not None:
        lines.append("")
        lines.append("## 重装中断")
        lines.append(f"APPLY-ERROR {apply_error}")
        lines.append("⚠️ 计划只执行了上面「已执行」段列出的那几件, 其余未动。")
    lines.append("")
    lines.append("## 边界")
    lines.append("本校验器不调用 launchctl —— 重装之后的重载是人的动作, 不在它的面内。")
    return "\n".join(lines) + "\n"


# ── 落点门 ────────────────────────────────────────────────────


def forbidden_report_roots(items: tuple[MachineItem, ...], home: Path, harness: Path) -> list[Path]:
    """报告不许落进「受管面」—— 往被审计的目录里写东西会污染审计本身。

    受管面**从 manifest 推出来**, 不硬编码: 每条 install 相对 home 的第一段
    （本清单里都是 `Library`）即一个受管根, 外加 `<harness>/scripts`。
    ⚠️ 与卡文 (e) 字面「不得在 --home 树内」的偏差已在验收单声明: 本仓所有
    evidence 落点都在 `/Users/Heishing/...` 即 HOME 之下, 字面实现会让 §二.6
    自己那条 `--report $EV/...` 恒 EXIT_USAGE, 两条要求互斥。
    """
    roots: set[Path] = set()
    for item in items:
        install_abs = expand_install(item.install, home)
        try:
            parts = install_abs.relative_to(home).parts
        except ValueError:  # pragma: no cover — install 恒由 home 拼出
            roots.add(install_abs.resolve())
            continue
        roots.add(home / parts[0] if parts else install_abs)
        # `--home` 指向别处时, 真实 HOME 的同名受管根同样不许当落点 ——
        # 否则 `--home <tmp> --report ~/Library/x` 会往真机受管面里写东西。
        real_home = Path.home()
        if parts:
            roots.add(real_home / parts[0])
    roots.add(harness / "scripts")
    return sorted(roots)


def report_location_problem(report: Path, items: tuple[MachineItem, ...], home: Path, harness: Path) -> str | None:
    """落点判定走 **物理解析**（resolve）而不是字符串前缀 —— 一条软链就能让
    词法判据和物理现实给出不同答案。"""
    target = report.expanduser()
    for root in forbidden_report_roots(items, home, harness):
        if _within_any_form(target, root):
            return f"报告落点在受管面内: {target} ⊆ {root}"
    return None


# ── CLI ───────────────────────────────────────────────────────


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="verify_install_manifest.py",
        description=(
            "校验 ~/Library 下的机器级安装副本（launchd plist + wrapper）是否与仓内源一致。"
            "只读; --reinstall 需配 --dry-run 或 --apply。不调用 launchctl。"
        ),
    )
    parser.add_argument("--manifest", help=f"清单路径（缺省 {DEFAULT_MANIFEST}）")
    parser.add_argument("--home", help="HOME 根（缺省 Path.home()；测试传 tmp 目录）")
    parser.add_argument("--harness", help=f"仓库树根（缺省 {DEFAULT_HARNESS}）")
    parser.add_argument("--report", help="报告落盘路径（缺省打到 stdout）")
    parser.add_argument("--reinstall", action="store_true", help="计算重装计划")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划, 零写入")
    parser.add_argument("--apply", action="store_true", help="真正重装 managed:repo 的漂移件")
    parser.add_argument(
        "--i-confirm-home-write",
        action="store_true",
        help="对真实 HOME 执行 --apply 时必须显式带上",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except UsageError as exc:
        print(f"用法错: {exc}", file=sys.stderr)
        return EXIT_USAGE

    try:
        home = Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
        harness = Path(args.harness).expanduser().resolve() if args.harness else DEFAULT_HARNESS
        manifest = Path(args.manifest).expanduser() if args.manifest else DEFAULT_MANIFEST

        if (args.dry_run or args.apply) and not args.reinstall:
            raise UsageError("--dry-run / --apply 是 --reinstall 的修饰, 必须与它同时给出")
        if args.reinstall and not (args.dry_run or args.apply):
            raise UsageError("--reinstall 必须与 --dry-run 或 --apply 二选一同时给出")
        if args.dry_run and args.apply:
            raise UsageError("--dry-run 与 --apply 互斥")
        if args.apply and _same_dir(home, Path.home()) and not args.i_confirm_home_write:
            raise UsageError(
                "--apply 指向真实 HOME, 必须显式带 --i-confirm-home-write —— 这是唯一会往 ~/Library 写字节的路径"
            )

        items = load_machine_items(manifest)
        if args.apply and not args.i_confirm_home_write:
            # ⛔ 上面那条只问「--home 是不是家目录」, 而真正该问的是「**这次要写的地方**
            # 在不在家目录里」。`--home /` 配一条 `~/Users/<user>/Library/...` 的安装路径,
            # 就能让 home ≠ 真实 HOME 而写目标恰恰是真实的安装副本（Codex r1 HIGH-3）。
            real_home = Path.home()
            for item in items:
                if item.managed != "repo":
                    continue
                dest = expand_install(item.install, home)
                # ⚠️ 这里是**禁止性**判定（「要不要逼用户带确认标志」）, 必须用并集谓词。
                # 用允许性谓词等于把方向写反: `Path.resolve()` 既不折叠大小写也不折叠
                # firmlink, 于是真实 HOME 的每一种别名拼法都答 False —— 我自己在
                # docstring 里写了「两个方向相反、不能共用」, 却在这一处用错了。
                if _within_any_form(dest, real_home):
                    raise UsageError(
                        f"--apply 的写目标落在真实 HOME 之内（{item.label}）, 必须显式带 --i-confirm-home-write"
                    )

        report_path: Path | None = None
        if args.report:
            report_path = Path(args.report).expanduser()
            problem = report_location_problem(report_path, items, home, harness)
            if problem is not None:
                raise UsageError(problem)

        results = verify(items, home, harness)
        plan = plan_reinstall(results)
        mode = "verify"
        applied: list[str] | None = None
        post_plan: list[tuple[Path, Path, str]] | None = None
        apply_error: ApplyError | None = None
        if args.reinstall and args.dry_run:
            mode = "dry-run"
        if args.reinstall and args.apply:
            mode = "apply"
            try:
                applied = _apply_reinstall(plan, home)
            except ApplyError as exc:
                # 半更新的树必须留下记录: 只丢一行 stderr 的话, 事后翻不出
                # 「到底装进去了哪几件」。报告照出, 退出码仍是阻断档。
                apply_error = exc
                applied = list(exc.applied)
            results = verify(items, home, harness)
            post_plan = plan_reinstall(results)

        text = render_report(
            results,
            plan,
            home=home,
            harness=harness,
            manifest=manifest,
            mode=mode,
            applied=applied,
            post_plan=post_plan,
            apply_error=str(apply_error) if apply_error is not None else None,
        )
        if report_path is not None:
            _write_report(report_path, text)
            print(f"报告已落盘: {report_path}")
            print(text.split("## 摘要", 1)[1].split("\n\n", 1)[0].strip())
        else:
            print(text, end="")
        if apply_error is not None:
            print(f"失败: {apply_error}", file=sys.stderr)
            return EXIT_MISMATCH
        return exit_code_for(results)
    except (ManifestError, UsageError) as exc:
        print(f"用法错: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (ApplyError, ReportWriteError) as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return EXIT_MISMATCH


if __name__ == "__main__":
    sys.exit(main())
