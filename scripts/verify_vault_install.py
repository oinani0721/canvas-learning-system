#!/usr/bin/env python3
"""Canvas Learning System — vault 部署清单只读校验器 (CARD-G2-6)。

拿 `scripts/vault-install-manifest.json` 声明的部署边界, 去比对一个**已存在**的
vault 目录, 回答三个问题: 该有的在不在 (match / missing)、覆盖面内有没有清单外的
东西 (extra)、以及给了模板源时内容有没有漂 (content-drift)。清单里显式声明「不
复制」的项若在目标里出现, 单独记 intentionally-excluded —— 那通常是人工放的或
Obsidian 自己生成的, 不算缺陷, 只是要让审计者看见。读不进去的条目单独记
unreadable, 并且**计入阻断** —— 「我看不见」不等于「一致」。

**只读**: 本脚本对 --vault / --source 只做 stat / 列目录 / 读字节, 没有任何写入
分支。唯一的写是把报告落到 --report, 而且:
  1. 落点不得在 --vault / --source 之内, **也不得在这两棵树里任何一条 symlink
     解析后的目标之下** —— 只比路径前缀挡不住「vault 里的 .claude 是指向树外
     目录的软链」这种别名;
  2. 落点若是个已存在且有多个硬链接的文件, 直接拒绝;
  3. 真正写的时候是「在同目录独占创建临时文件 → 写 → os.replace 换目录项」,
     从不原地覆盖已有 inode。前两道是可读的早退, 第三道才是承重的那道。
**已知边界(如实声明)**: 检查与写入之间存在 TOCTOU 窗口; 检查之后新建的别名不在
覆盖范围内; 本脚本不是特权程序, 防的是误伤而不是有意的对抗。

**「活 vault 即模板」**(install-vault.sh:2-6): manifest 只声明 path/role/action/kind,
不带任何内容或哈希基线 —— 内容的参照永远是 --source 指向的那个活 vault, 本仓不
维护第二份模板。所以不给 --source 时, content-drift 一律报 "not evaluated",
而不是拿某个内置基线冒充。

退出码:
  0  没有 missing / extra / content-drift / unreadable
  1  有上述任一 (intentionally-excluded 只报告, 不进退出码)
  2  用法或配置错 (清单非法、目录不存在、报告落点非法或写不下去)

用法:
  python3 scripts/verify_vault_install.py --vault <dir> [--source <dir>]
                                          [--manifest <path>] [--report <path>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

EXIT_OK = 0
EXIT_DIFF = 1
EXIT_USAGE = 2

VALID_ACTIONS = frozenset({"copy", "generate", "skeleton", "exclude"})
# "nondir" 对应 install-vault.sh:86 那条强制删除: 它清掉一切**非目录**条目
# (普通文件、指向文件或目录的软链、悬空软链、FIFO 都删; 真目录不删)。
# 用 "file" 表达它是错的 —— is_file() 对后三者为 False。
VALID_KINDS = frozenset({"", "dir", "file", "nondir"})
REQUIRED_ITEM_KEYS = ("path", "role", "action")
# `[` 刻意不算通配符: _pattern_to_regex 对它走 re.escape 当字面量。若把它算进
# GLOB_CHARS, 一条写成字符类的模式就会「被当 glob 走正则路径, 而正则里它又是字面量」
# ⇒ 静默不命中, 正确部署的 vault 被误报 drift。两处口径必须一致, 这里统一选
# 「`[` 一律按字面量」—— 真实文件名里的方括号本来就该按字面匹配。
# 代价如实声明: 本清单不支持字符类模式 (`[abc]*.json` 这种写法匹配的是字面的 `[abc]`)。
GLOB_CHARS = "*?"

DEFAULT_MANIFEST = Path(__file__).resolve().parent / "vault-install-manifest.json"


class ManifestError(Exception):
    """manifest 结构或取值非法 —— 一律走退出码 2, 不与内容差异混为一谈。"""


class ReportWriteError(Exception):
    """报告落盘失败 —— 同样走退出码 2, 不能让它伪装成内容差异。"""


@dataclass(frozen=True)
class Item:
    path: str
    role: str
    action: str
    kind: str = ""  # "" 不限 / "dir" 只目录 / "file" 只普通文件 / "nondir" 一切非目录
    origin: str = ""
    note: str = ""


@dataclass(frozen=True)
class ScanRoot:
    """extra 检测面的一段声明: dir 下直接子项中匹配 match 的那些。"""

    dir: str
    match: str


@dataclass(frozen=True)
class Manifest:
    version: int
    source: str
    items: tuple[Item, ...]
    extra_scan: tuple[ScanRoot, ...]

    @property
    def declared_paths(self) -> frozenset[str]:
        """copy / skeleton / generate 三类的 path —— 即「该在目标里的东西」。"""
        return frozenset(i.path for i in self.items if i.action in ("copy", "skeleton", "generate"))

    @property
    def exclude_items(self) -> tuple[Item, ...]:
        return tuple(i for i in self.items if i.action == "exclude")


@dataclass(frozen=True)
class Finding:
    path: str
    category: str
    action: str
    role: str
    detail: str = ""


@dataclass
class Report:
    manifest_path: Path
    vault: Path
    source: Path | None
    drift_evaluated: bool = False
    match: list[Finding] = field(default_factory=list)
    missing: list[Finding] = field(default_factory=list)
    extra: list[Finding] = field(default_factory=list)
    content_drift: list[Finding] = field(default_factory=list)
    intentionally_excluded: list[Finding] = field(default_factory=list)
    unreadable: list[Finding] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        # unreadable 计入阻断: 读不进去就无法证明一致, 不能报 0。
        blocking = len(self.missing) + len(self.extra) + len(self.content_drift) + len(self.unreadable)
        return EXIT_DIFF if blocking else EXIT_OK


# ── manifest 加载与校验 ───────────────────────────────────────────────


def _check_relative_segment(raw: object, label: str, *, allow_empty: bool = False) -> str:
    """校验并规范化一个「相对 vault 根」的路径值, 返回规范形式。

    path 与 extra_scan.dir **共用这一个函数** —— 同一条约束只在一半字段上生效,
    正是「清单里 path 不许绝对/不许 .., extra_scan.dir 却什么都不查」那条缺陷的根因。
    规范化 (折叠 //、去尾 /) 也在这里做: declared_paths 用原样字符串、extra 检测用
    规范化路径, 两处口径不一致会让同一条目同时进 match 和 extra。
    """
    if not isinstance(raw, str):
        raise ManifestError(f"{label} 必须是字符串, 实为 {type(raw).__name__}")
    if not raw:
        if allow_empty:
            return ""
        raise ManifestError(f"{label} 不得为空字符串")
    if "\x00" in raw:
        raise ManifestError(f"{label} 不得含 NUL 字符")
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError as exc:  # 孤立代理字符等
        raise ManifestError(f"{label} 含无法编码的字符: {exc}") from exc
    if raw.startswith("/") or Path(raw).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", raw):
        raise ManifestError(f"{label} 必须相对 vault 根, 不得是绝对路径: {raw!r}")
    normalized = PurePosixPath(raw).as_posix()
    if ".." in PurePosixPath(normalized).parts:
        raise ManifestError(f"{label} 不得含 .. 逃逸段: {raw!r}")
    return normalized


def _check_path_field(raw: object, seen: set[str]) -> str:
    normalized = _check_relative_segment(raw, "item 的 path")
    if normalized in seen:
        raise ManifestError(f"item 的 path 重复声明(规范化后): {normalized!r}")
    seen.add(normalized)
    return normalized


def load_manifest(path: Path | str) -> Manifest:
    """读并校验 manifest。任何结构/取值问题都抛 ManifestError。

    读取阶段把 OSError / UnicodeDecodeError / ValueError 一并转成 ManifestError ——
    「--manifest 指向一个目录 / 不可读 / 非 UTF-8」不该以未捕获异常终止, 那样调用方
    拿到的是 1 而不是承诺的 2。
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
    except ValueError as exc:  # JSONDecodeError 是它的子类; 超长数字也走这里
        raise ManifestError(f"manifest 不是合法 JSON: {path} — {exc}") from exc

    if not isinstance(raw, dict):
        raise ManifestError("manifest 顶层必须是对象")
    version = raw.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ManifestError(f"manifest 的 version 必须是整数, 实为 {version!r}")
    source = raw.get("source")
    if not isinstance(source, str) or not source:
        raise ManifestError(f"manifest 的 source 必须是非空字符串, 实为 {source!r}")
    raw_items = raw.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ManifestError(f"manifest 的 items 必须是非空列表, 实为 {type(raw_items).__name__}")

    seen: set[str] = set()
    items: list[Item] = []
    for index, entry in enumerate(raw_items):
        if not isinstance(entry, dict):
            raise ManifestError(f"items[{index}] 必须是对象")
        for key in REQUIRED_ITEM_KEYS:
            if key not in entry:
                raise ManifestError(f"items[{index}] 缺必填键 {key}")
        normalized_path = _check_path_field(entry["path"], seen)
        if not isinstance(entry["role"], str) or not entry["role"]:
            raise ManifestError(f"items[{index}] 的 role 必须是非空字符串")
        # 先验类型再查枚举: `action: []` / `{}` 这类 unhashable 值直接做集合成员判断会抛
        # TypeError, 逃出 ManifestError 的捕获面, CLI 就给不出承诺的退出码 2。
        if not isinstance(entry["action"], str):
            raise ManifestError(f"items[{index}] 的 action 必须是字符串, 实为 {type(entry['action']).__name__}")
        if entry["action"] not in VALID_ACTIONS:
            raise ManifestError(f"items[{index}] 的 action {entry['action']!r} 不在枚举 {sorted(VALID_ACTIONS)} 内")
        kind = entry.get("kind", "")
        if not isinstance(kind, str) or kind not in VALID_KINDS:
            raise ManifestError(f"items[{index}] 的 kind {kind!r} 不在枚举 {sorted(VALID_KINDS)} 内")
        items.append(
            Item(
                path=normalized_path,
                role=entry["role"],
                action=entry["action"],
                kind=kind,
                origin=entry.get("origin", ""),
                note=entry.get("note", ""),
            )
        )

    raw_scan = raw.get("extra_scan", [])
    if not isinstance(raw_scan, list):
        raise ManifestError("manifest 的 extra_scan 必须是列表")
    scan: list[ScanRoot] = []
    for index, entry in enumerate(raw_scan):
        if not isinstance(entry, dict) or "dir" not in entry or "match" not in entry:
            raise ManifestError(f"extra_scan[{index}] 必须含 dir 与 match")
        scan_dir = _check_relative_segment(entry["dir"], f"extra_scan[{index}] 的 dir", allow_empty=True)
        scan_match = entry["match"]
        if not isinstance(scan_match, str) or not scan_match:
            raise ManifestError(f"extra_scan[{index}] 的 match 必须是非空字符串")
        scan.append(ScanRoot(dir=scan_dir, match=scan_match))

    return Manifest(version=version, source=source, items=tuple(items), extra_scan=tuple(scan))


# ── glob 语义 ────────────────────────────────────────────────────────


def _pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """把 manifest 的 path 模式编译成相对路径正则。

    语义: `**/` 跨任意层目录, 结尾 `/**` = 该目录下的全部子孙, `*` 不跨 `/`。
    结尾用 `\\Z` 而不是 `$`: `$` 会匹配「最后一个换行之前」的位置, 于是一个名字
    末尾带换行的文件 (POSIX 允许) 会被误判成命中, 而 shell 的模式不会匹配它。
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:[^/]+/)*")
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out.append("/.+")
            i += 3
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out), re.DOTALL)


def _static_prefix(pattern: str) -> str:
    """取模式中第一个通配段之前的目录前缀 —— 用它限定遍历面, 不做全树扫描。"""
    parts = PurePosixPath(pattern).parts
    keep: list[str] = []
    for part in parts:
        if any(ch in part for ch in GLOB_CHARS):
            break
        keep.append(part)
    return "/".join(keep)


def _has_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in GLOB_CHARS)


# ── 目录遍历 (只读) ──────────────────────────────────────────────────


def _walk(root: Path):
    """产出 (相对 root 的 POSIX 路径, 类型) —— 类型 ∈ dir/file/symlink/unreadable。

    自己走而不用 `Path.rglob`: rglob 会**静默吞掉** PermissionError, 于是一棵读不
    进去的子树看起来跟不存在一模一样, 两侧一比就「相等」—— 把「我看不见」说成
    「一致」。那是漏报, 比误报危险得多。这里遇到读不动的地方会明确产出 unreadable。
    """
    stack: list[str] = [""]
    while stack:
        rel = stack.pop()
        here = root / rel if rel else root
        try:
            with os.scandir(here) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            yield (rel, "unreadable")
            continue
        for entry in entries:
            child = f"{rel}/{entry.name}" if rel else entry.name
            try:
                is_link = entry.is_symlink()
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                yield (child, "unreadable")
                continue
            if is_link:
                yield (child, "symlink")
            elif is_dir:
                yield (child, "dir")
                stack.append(child)
            else:
                yield (child, "file")


def _iter_relative(root: Path, base: Path) -> list[str]:
    """列出 root 子树里全部条目相对 base 的 POSIX 路径 (含 root 自身)。"""
    if not root.exists():
        return []
    out = [root.relative_to(base).as_posix()] if root != base else []
    if root.is_dir() and not root.is_symlink():
        prefix = root.relative_to(base).as_posix() if root != base else ""
        for rel, kind in _walk(root):
            if kind == "unreadable" and not rel:
                continue
            out.append(f"{prefix}/{rel}" if prefix else rel)
    return out


def _kind_ok(item: Item, path: Path) -> bool:
    """item.kind 声明的类型条件是否被 path 满足。

    对应 install-vault.sh 里那两条命令自带的类型限定:
      :84 `find ... -type d -name __pycache__`  → 只剪目录 (find 默认不跟随软链)
      :86 强制删除 `pending_archives*.jsonl`     → 删一切**非目录**条目
    kind 为空 = 不限类型 (`:68`/`:69` 那些按路径声明「不复制」的项本就没有类型条件)。
    """
    if item.kind == "dir":
        return path.is_dir() and not path.is_symlink()
    if item.kind == "file":
        return path.is_file()
    if item.kind == "nondir":
        return not (path.is_dir() and not path.is_symlink())
    return True


class ExcludeMatcher:
    """manifest 全部 exclude 项的统一判定口径。

    分类 (intentionally-excluded)、extra 豁免、目录摘要过滤三处**必须共用它**——
    三处各写一份判断就会互相漂移: 摘要那一处曾没用上排除规则, 于是一个被正确部署
    (脚本已剪掉 __pycache__) 的 vault 反被报 drift。
    """

    def __init__(self, items: tuple[Item, ...]) -> None:
        self._rules = [(item, _pattern_to_regex(item.path) if _has_glob(item.path) else None) for item in items]

    def matches_exact(self, base: Path, rel: str) -> bool:
        """rel 这一条本身是否被某条 exclude 覆盖 (含类型条件)。"""
        for item, regex in self._rules:
            hit = bool(regex.fullmatch(rel)) if regex is not None else rel == item.path
            if hit and _kind_ok(item, base / rel):
                return True
        return False

    def is_under_exclusion(self, base: Path, rel: str) -> bool:
        """rel 本身**或它的任一祖先**被排除 —— 用于整棵剪掉被排除的子树。"""
        parts = rel.split("/")
        return any(self.matches_exact(base, "/".join(parts[:n])) for n in range(1, len(parts) + 1))

    def hits_for(self, vault: Path, item: Item) -> list[str]:
        """单条 exclude 在 vault 里实际命中的相对路径 (按静态前缀限定遍历面)。"""
        if not _has_glob(item.path):
            target = vault / item.path
            return [item.path] if target.exists() and _kind_ok(item, target) else []
        prefix = _static_prefix(item.path)
        scan_root = vault / prefix if prefix else vault
        regex = _pattern_to_regex(item.path)
        return sorted(
            rel for rel in _iter_relative(scan_root, vault) if regex.fullmatch(rel) and _kind_ok(item, vault / rel)
        )


# ── 内容摘要 ─────────────────────────────────────────────────────────


def _leaf_digest(path: Path) -> str:
    """单个条目的摘要: 软链记指向, 文件记字节, 目录只记类型 (子孙另行逐条计入)。"""
    try:
        if path.is_symlink():
            return "L:" + hashlib.sha256(str(path.readlink()).encode("utf-8")).hexdigest()
        if path.is_file():
            return "F:" + hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_dir():
            return "D:"
    except OSError:
        return "U:unreadable"
    return "?:unknown"


def _digest(
    path: Path,
    excluder: ExcludeMatcher | None = None,
    base: Path | None = None,
    unreadable: list[str] | None = None,
) -> str:
    """目录按 (相对路径, 叶子摘要) 的稳定聚合; 非目录直接取叶子摘要。只读。

    给了 excluder + base 时, **被 exclude 覆盖的子孙整棵剔除**再算 —— 否则
    「模板源里有 __pycache__ / 归档队列, 目标按脚本剪掉了」这种**正确部署**会被
    判成 content-drift。base 是该 exclude 模式所相对的 vault 根 (源与目标各自的根)。
    读不进去的条目写成 U: 参与摘要, 并登记到 unreadable —— 不能当作「不存在」。
    """
    if path.is_symlink() or not path.is_dir():
        return _leaf_digest(path)
    acc = hashlib.sha256()
    for rel, kind in sorted(_walk(path)):
        child = path / rel if rel else path
        if excluder is not None and base is not None:
            try:
                full_rel = child.relative_to(base).as_posix()
            except ValueError:  # pragma: no cover — child 总在 base 之下
                full_rel = rel
            if excluder.is_under_exclusion(base, full_rel):
                continue
        if kind == "unreadable":
            if unreadable is not None:
                target = child.relative_to(base).as_posix() if base is not None else rel
                unreadable.append(target)
            acc.update(f"{rel}\0U:unreadable\n".encode("utf-8"))
            continue
        acc.update(f"{rel}\0{_leaf_digest(child)}\n".encode("utf-8"))
    return "D:" + acc.hexdigest()


# ── 报告落点与落盘 ───────────────────────────────────────────────────


def _forbidden_roots(tree: Path) -> list[Path]:
    """tree 本身, 外加 tree 里每一条软链解析后的目标。

    报告落点不能只按「路径是否在 tree 前缀下」判: vault 里一条指向树外目录的软链,
    会让一个「树外」路径其实就是 vault 里看得见的文件 —— 路径判据说安全, 写下去
    vault 的内容就变了。已知边界: 这一遍扫描之后新建的别名不在覆盖范围内。
    """
    roots = [tree]
    for rel, kind in _walk(tree):
        if kind != "symlink":
            continue
        try:
            roots.append((tree / rel).resolve())
        except OSError:  # pragma: no cover — 悬空软链等
            continue
    return roots


def _write_report(path: Path, text: str) -> None:
    """写新 inode 再换目录项 —— 绝不原地覆盖一个已经存在的 inode。

    原地 `write_text` 会顺着任何别名写穿: 硬链接、`/dev/fd/N`（它 resolve 成自身、
    stat 又返回被打开文件的属性且 nlink=1, 路径判据和链接数判据同时失明）。
    `os.replace` 换的是目录项, 旧 inode 的其它名字仍指向旧内容。
    """
    tmp = path.parent / f".{path.name}.tmp-{os.getpid()}"
    fd = None
    try:
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        os.write(fd, text.encode("utf-8"))
        os.close(fd)
        fd = None
        os.replace(str(tmp), str(path))
    except OSError as exc:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise ReportWriteError(f"报告落盘失败: {path} — {exc}") from exc


# ── 核心比对 ─────────────────────────────────────────────────────────


def verify(
    vault_dir: Path | str,
    manifest: Manifest,
    source_dir: Path | str | None = None,
    manifest_path: Path | None = None,
) -> Report:
    """把 manifest 比对到 vault_dir 上。source_dir 给了才评 content-drift。"""
    vault = Path(vault_dir)
    source = Path(source_dir) if source_dir is not None else None
    report = Report(
        manifest_path=manifest_path or DEFAULT_MANIFEST,
        vault=vault,
        source=source,
        drift_evaluated=source is not None,
    )
    excluder = ExcludeMatcher(manifest.exclude_items)

    for item in manifest.items:
        if item.action == "exclude":
            hits = excluder.hits_for(vault, item)
            if hits:
                sample = ", ".join(hits[:3])
                more = f" (共 {len(hits)} 项)" if len(hits) > 3 else ""
                report.intentionally_excluded.append(
                    Finding(
                        path=item.path,
                        category="intentionally-excluded",
                        action=item.action,
                        role=item.role,
                        detail=f"目标里存在: {sample}{more}",
                    )
                )
            continue

        target = vault / item.path
        if not target.exists():
            detail = ""
            if item.action == "copy" and source is not None and not (source / item.path).exists():
                detail = "模板源也没有这一项 (install-vault.sh 会打 ⚠️ 跳过)"
            report.missing.append(
                Finding(
                    path=item.path,
                    category="missing",
                    action=item.action,
                    role=item.role,
                    detail=detail,
                )
            )
            continue

        if item.action == "skeleton" and not target.is_dir():
            report.missing.append(
                Finding(
                    path=item.path,
                    category="missing",
                    action=item.action,
                    role=item.role,
                    detail="存在但不是目录 (骨架项须为目录)",
                )
            )
            continue

        # generate 项按 vault 重新生成, 内容本就该与模板源不同 —— 不评 drift。
        if item.action == "copy" and source is not None:
            src = source / item.path
            if src.exists():
                unreadable_here: list[str] = []
                src_digest = _digest(src, excluder, source, unreadable_here)
                tgt_digest = _digest(target, excluder, vault, unreadable_here)
                for rel in unreadable_here:
                    report.unreadable.append(
                        Finding(
                            path=rel,
                            category="unreadable",
                            action=item.action,
                            role=item.role,
                            detail="读不进去, 无法证明两侧一致",
                        )
                    )
                if src_digest != tgt_digest:
                    report.content_drift.append(
                        Finding(
                            path=item.path,
                            category="content-drift",
                            action=item.action,
                            role=item.role,
                            detail="与模板源字节不一致",
                        )
                    )
                    continue

        report.match.append(Finding(path=item.path, category="match", action=item.action, role=item.role))

    _collect_extra(vault, manifest, report, excluder)
    return report


def _collect_extra(vault: Path, manifest: Manifest, report: Report, excluder: ExcludeMatcher) -> None:
    """覆盖面内、既不在 declared_paths 也不被 exclude 覆盖的直接子项 = extra。

    exclude 豁免走 ExcludeMatcher 的 is_under_exclusion（与摘要过滤同一口径，含类型
    条件与祖先剪除）——三处共用一个匹配器却有两种语义，本身就是漂移源。
    """
    declared = manifest.declared_paths

    def is_excluded(rel: str) -> bool:
        return excluder.is_under_exclusion(vault, rel)

    seen: set[str] = set()
    for scan in manifest.extra_scan:
        scan_dir = vault / scan.dir if scan.dir else vault
        if not scan_dir.is_dir():
            continue
        name_regex = _pattern_to_regex(scan.match)
        try:
            with os.scandir(scan_dir) as it:
                children = sorted(it, key=lambda e: e.name)
        except OSError:
            report.unreadable.append(
                Finding(
                    path=scan.dir,
                    category="unreadable",
                    action="-",
                    role="-",
                    detail="extra 覆盖面读不进去, 无法证明没有清单外的东西",
                )
            )
            continue
        for child in children:
            if not name_regex.fullmatch(child.name):
                continue
            rel = f"{scan.dir}/{child.name}" if scan.dir else child.name
            if rel in declared or rel in seen or is_excluded(rel):
                continue
            seen.add(rel)
            report.extra.append(
                Finding(
                    path=rel,
                    category="extra",
                    action="-",
                    role="-",
                    detail=f"位于覆盖面 {scan.dir}/{scan.match} 内但不在 manifest",
                )
            )


# ── 报告渲染 ─────────────────────────────────────────────────────────


def render(report: Report, manifest: Manifest) -> str:
    lines = [
        "# vault-install verification report (CARD-G2-6, read-only)",
        f"# manifest : {report.manifest_path} (version {manifest.version}, source {manifest.source})",
        f"# vault    : {report.vault}",
        f"# source   : {report.source if report.source else '(未提供 — content-drift 未评估)'}",
        "# 语义     : exclude 项按各自模式的静态前缀子树扫描; extra 只看 manifest",
        "#            extra_scan 声明的覆盖面 (根级文档不在覆盖面内, 故不报 extra);",
        "#            读不进去的条目记 unreadable 并计入退出码 —— 看不见不等于一致。",
        "-" * 66,
        f"match                  : {len(report.match)}",
        f"missing                : {len(report.missing)}",
        f"extra                  : {len(report.extra)}",
        "content-drift          : "
        + (str(len(report.content_drift)) if report.drift_evaluated else "not evaluated (无 --source)"),
        f"intentionally-excluded : {len(report.intentionally_excluded)}",
        f"unreadable             : {len(report.unreadable)}",
    ]
    for title, findings in (
        ("missing", report.missing),
        ("extra", report.extra),
        ("content-drift", report.content_drift),
        ("unreadable", report.unreadable),
        ("intentionally-excluded", report.intentionally_excluded),
    ):
        if not findings:
            continue
        lines.append("")
        lines.append(f"## {title}")
        for finding in findings:
            suffix = f"  — {finding.detail}" if finding.detail else ""
            role = f" [{finding.role}]" if finding.role != "-" else ""
            lines.append(f"  {finding.path}{role}{suffix}")
    lines.append("")
    lines.append(f"exit={report.exit_code}")
    return "\n".join(lines) + "\n"


# ── CLI ──────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_vault_install.py",
        description="只读校验一个 vault 是否符合 vault-install-manifest.json 声明的部署边界。",
    )
    parser.add_argument("--vault", required=True, help="待校验的 vault 目录 (只读)")
    parser.add_argument("--source", help="模板源 vault, 给了才评 content-drift (只读)")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="清单路径")
    parser.add_argument("--report", help="报告落盘路径, 缺省写 stdout; 不得落在被查树里")
    return parser


def _resolve_dir(raw: str, label: str) -> tuple[Path | None, str | None]:
    path = Path(raw).expanduser()
    if not path.is_dir():
        return None, f"{label} 不是存在的目录: {path}"
    return path.resolve(), None


def _check_report_location(report_path: Path, trees: list[tuple[Path | None, str]]) -> str | None:
    """报告落点是否安全。返回错误消息, None 表示可以写。"""
    for tree, label in trees:
        if tree is None:
            continue
        for root in _forbidden_roots(tree):
            if report_path == root or report_path.is_relative_to(root):
                return f"--report 不得落在 {label} 树内或其软链目标之下 (审计不写被审对象): {report_path} ⊂ {root}"
    if not report_path.parent.is_dir():
        return f"--report 的上级目录不存在: {report_path.parent}"
    # 「路径不在被查树内」不等于「写它不会改到被查树」: 一个树外路径可以与树内文件
    # 共享 inode (硬链接), 写它就等于原地改写那个文件。resolve() 解得开软链, 解不开
    # 硬链接 —— 硬链接没有「指向」可言, 两个目录项本来就平级。
    if report_path.exists() and report_path.stat().st_nlink > 1:
        return (
            f"--report 指向的文件有 {report_path.stat().st_nlink} 个硬链接, "
            f"写它可能改到被查树里的同 inode 文件, 拒绝: {report_path}"
        )
    return None


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    vault, err = _resolve_dir(args.vault, "--vault")
    if err is not None or vault is None:
        print(f"❌ {err or '--vault 解析失败'}", file=sys.stderr)
        return EXIT_USAGE
    source: Path | None = None
    if args.source:
        source, err = _resolve_dir(args.source, "--source")
        if err is not None or source is None:
            print(f"❌ {err or '--source 解析失败'}", file=sys.stderr)
            return EXIT_USAGE

    report_path: Path | None = None
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        problem = _check_report_location(report_path, [(vault, "--vault"), (source, "--source")])
        if problem:
            print(f"❌ {problem}", file=sys.stderr)
            return EXIT_USAGE

    manifest_path = Path(args.manifest).expanduser()
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print(f"❌ manifest 不可用: {exc}", file=sys.stderr)
        return EXIT_USAGE

    report = verify(vault, manifest, source_dir=source, manifest_path=manifest_path)
    text = render(report, manifest)
    if report_path is not None:
        try:
            _write_report(report_path, text)
        except ReportWriteError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return EXIT_USAGE
        print(f"报告已写入 {report_path}")
    else:
        sys.stdout.write(text)
    return report.exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
