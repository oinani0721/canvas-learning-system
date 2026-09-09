#!/usr/bin/env python3
"""Canvas Learning System — vault 部署清单只读校验器 (CARD-G2-6)。

拿 `scripts/vault-install-manifest.json` 声明的部署边界, 去比对一个**已存在**的
vault 目录, 回答三个问题: 该有的在不在 (match / missing)、覆盖面内有没有清单外的
东西 (extra)、以及给了模板源时内容有没有漂 (content-drift)。清单里显式声明「不
复制」的项若在目标里出现, 单独记 intentionally-excluded —— 那通常是人工放的或
Obsidian 自己生成的, 不算缺陷, 只是要让审计者看见。读不进去的条目单独记
unreadable, 并且**计入阻断** —— 「我看不见」不等于「一致」。

**只读**: 本脚本对 --vault / --source 只做 stat / 列目录 / 读字节, 没有任何写入
分支。唯一的写是把报告落到 --report, 由**三道共同承重**(不是「一道承重两道早退」——
换 inode 保护得了旧 inode 的其它名字, 却保护不了「通过目录别名看到的目录项」,
也阻止不了错误清理删掉别人的文件):
  1. **落点按文件系统身份判**((st_dev, st_ino)), 不按路径字符串: resolve() 不做大小写
     规范化, 而 macOS 默认文件系统大小写不敏感 —— 目录实际叫 `Vault` 时,
     `--report vault/x` 的 is_relative_to 为 False 而两者其实是同一个对象。
     禁写身份 = 两棵树本身 + 树内软链目标(**递归展开**, 两层软链能绕开单层解析),
     按目录身份去重防环; 报告的**临时落点**同样过这道检查;
  2. 落点若是已存在且有多个硬链接的文件, 直接拒绝; 若安全性扫描本身没跑完
     (树里有读不动的目录), **拒绝落盘** —— 扫不完就不能说安全;
  3. 写的时候在同目录独占创建临时文件(O_EXCL, 名字带 pid + 随机串) → 循环写满 →
     os.replace 换目录项, 从不原地覆盖已有 inode; 失败时**只清理本次真正创建的那个
     临时文件**(O_EXCL 失败意味着那文件是别人的, 删它就是毁别人的数据)。
**已知边界(如实声明)**: 检查与写入之间存在 TOCTOU 窗口; 检查之后新建的别名不在覆盖
范围内; 软链递归有深度上限, 超限按「扫描未完成」拒绝落盘; 身份比较覆盖大小写/软链/
硬链接这几类别名, 但**不宣称穷尽所有别名**; 本脚本不是特权程序, 防的是误伤而不是对抗。

**模板源**(E-4, CARD-G2-7a): 缺省 = harness 树的 `canvas-vault/`(git 追踪系统件),
`--source` 可改指一个活 vault 取 gitignored 件。manifest 只声明 path/role/action/kind,
不带任何内容或哈希基线 —— 内容的参照永远是 --source 指向的那个活 vault, 本仓不
维护第二份模板。所以不给 --source 时, content-drift 一律报 "not evaluated",
而不是拿某个内置基线冒充。

**extra_allow** (manifest 顶层, CARD-RV-G2-6): 覆盖面内确实多出来、但**允许它多**的
路径白名单。命中的项进 allowed-extra 段, 只报告、不计退出码; 没命中的仍是 extra。
每项走与 item.path 同一套校验 (相对 / 无 `..` / 可编码 / 无重复, 支持 `*?` glob),
且**与 declared_paths 或任一 exclude 模式重叠即拒绝加载** —— 同一路径有两种语义时,
「按哪一条算」就成了实现细节, 那正是清单该挡住的东西。

**hotkey-orphan** (CARD-RV-G2-6): vault 的 `.obsidian/hotkeys.json` 里带
`canvas-learning-system:` 前缀的键, 必须能在同一 vault 的插件构建产物
`.obsidian/plugins/canvas-learning-system/main.js` 里找到对应的命令 id 字面量。
找不到 = 快捷键绑了个不存在的命令, 按 mismatch 阻断。**main.js 是 gitignored 的构建
产物, 可能根本不在** —— 那时报告明写 `not evaluated`, **不计退出码也不静默**:
把「没法查」说成「查过了没问题」是假绿。

**optional** (item 级布尔, CARD-G2-7a): 声明了但**允许它不在**。缺失时进 optional-missing 段,
**不计退出码**。两类用途: ① Obsidian 首次打开自建的配置; ② gitignored 因而模板源里本就没有、
只在 `--source` 指 live 时才拿得到的件。它只放松「在不在」: copy 项在位时照常比内容, **generate 项按定义不比内容**(每 vault 都不同,
只查形态与可读性)。始终留在 declared_paths 里(否则在位时会被反过来报成 extra)。

退出码 (CARD-RV-G2-6 分四档 —— 调用方要能区分「缺东西」与「多东西」):
  0  没有 missing / extra / content-drift / unreadable / hotkey-orphan
  1  **只有 missing**: 该有的没到位, 补齐即可
  2  **mismatch**: extra(未放行) / content-drift / unreadable / hotkey-orphan 任一非空
     —— 同时还有 missing 时也取 2 (多出来的东西比缺东西更需要人看一眼)
  3  用法或配置错 (清单非法、目录不存在、报告落点非法或写不下去)
  intentionally-excluded 与 allowed-extra 只报告, 不进退出码。

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
import stat
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

EXIT_OK = 0
EXIT_MISSING = 1  # 只缺东西
EXIT_MISMATCH = 2  # 多东西 / 内容漂 / 读不动 / 快捷键绑了不存在的命令
EXIT_USAGE = 3  # 用法或配置错

# hotkeys ↔ 插件命令 id 交叉核用到的三个常量 (CARD-RV-G2-6)。
PLUGIN_ID = "canvas-learning-system"
HOTKEYS_REL = ".obsidian/hotkeys.json"
PLUGIN_MAIN_JS_REL = f".obsidian/plugins/{PLUGIN_ID}/main.js"
HOTKEY_PREFIX = f"{PLUGIN_ID}:"
# main.js 是打包压缩过的构建产物, 只能按字面量取命令 id。真相源是
# frontend/obsidian-plugin/src/main.ts 的 addCommand({id: "canvas:…"}), 由测试层单独钉住。
# 三种引号形态都认: 打包器的引号风格不是稳定契约(esbuild/terser/rollup 各有默认,
# 配置一改就变)。只认双引号时, 单引号产物会让命令集变成空集 —— 于是**每一条真实
# 绑定都被误报成 orphan**, 正确部署的 vault 反而阻断。误拦比漏放更难排查, 故放宽。
COMMAND_ID_RE = re.compile(r"""(["'`])(canvas:[a-z0-9-]+)\1""")

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

# 落点检查器: 给一个路径, 返回错误消息或 None。报告本体与临时落点共用它。
LocationGuard = Callable[[Path], "str | None"]


class ManifestError(Exception):
    """manifest 结构或取值非法 —— 一律走用法错档 EXIT_USAGE(3), 不与内容差异混为一谈。"""


class ReportWriteError(Exception):
    """报告落盘失败 —— 同样走用法错档 EXIT_USAGE(3), 不能让它伪装成内容差异。"""


@dataclass(frozen=True)
class Item:
    path: str
    role: str
    action: str
    kind: str = ""  # "" 不限 / "dir" 只目录 / "file" 只普通文件 / "nondir" 一切非目录
    origin: str = ""
    note: str = ""
    # optional (CARD-G2-7a): 声明了但**允许它不在**。缺失时进 optional-missing 段,
    # **不计退出码**。用于两类项: ① Obsidian 首次打开自建的配置 (app.json 等);
    # ② gitignored 因而模板源里本就没有、只在 --source 指 live 时才拿得到的件。
    # ⚠️ 它只放松「在不在」: copy 项在位时照常比内容, **generate 项按定义不比内容**
    # (每 vault 都不同, 只查形态与可读性)。始终留在 declared_paths 里
    # (否则它在位时会被反过来报成 extra)。
    optional: bool = False


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
    extra_allow: tuple[str, ...] = ()

    @property
    def declared_paths(self) -> frozenset[str]:
        """copy / skeleton / generate 三类的 path —— 即「该在目标里的东西」。"""
        return _declared_paths(self.items)

    @property
    def exclude_items(self) -> tuple[Item, ...]:
        return tuple(i for i in self.items if i.action == "exclude")


def _declared_paths(items: tuple[Item, ...]) -> frozenset[str]:
    """「该在目标里的东西」的唯一口径。

    `Manifest.declared_paths` 与 `load_manifest` 的 `extra_allow` 重叠检查**必须**共用它 ——
    各写一份就会漂: 将来给 declared 加一类 action 而只改了一处, `extra_allow` 就能放行
    一条本该被管住的路径, 而且没有任何门会红。
    """
    return frozenset(i.path for i in items if i.action in ("copy", "skeleton", "generate"))


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
    allowed_extra: list[Finding] = field(default_factory=list)
    optional_missing: list[Finding] = field(default_factory=list)
    unreadable: list[Finding] = field(default_factory=list)
    hotkey_orphan: list[Finding] = field(default_factory=list)
    hotkeys_note: str = "not evaluated (未检查)"

    @property
    def exit_code(self) -> int:
        """0 / 1 / 2 三档 (用法错的 3 由 main() 直接返回, 不经过这里)。

        unreadable 计入阻断: 读不进去就无法证明一致, 不能报 0。
        missing 与 mismatch 并存时取 **2** —— 「多出来 / 对不上」的那些项需要人判断,
        而 missing 是照单补齐就行的。合并成一个 1 会让调用方分不出这两件事。
        allowed_extra / intentionally_excluded / optional_missing 只报告, 不进退出码。
        """
        if self.content_drift or self.extra or self.unreadable or self.hotkey_orphan:
            return EXIT_MISMATCH
        if self.missing:
            return EXIT_MISSING
        return EXIT_OK


# ── manifest 加载与校验 ───────────────────────────────────────────────


def _require_encodable(value: str, label: str) -> None:
    """会进报告文本的字符串必须能编码成 UTF-8。

    孤立代理字符(如 JSON 里的 "\\ud800")能通过 json.loads, 却会在写报告时抛
    UnicodeEncodeError —— 那时已经过了 ManifestError 的捕获面, 调用方拿到的不是
    承诺的用法错档(EXIT_USAGE=3), 还会留下临时文件。所以在加载阶段就挡掉。
    """
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ManifestError(f"{label} 含无法编码为 UTF-8 的字符: {exc}") from exc


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
    if normalized == ".":
        # `.` / `./` / `.//` 都是「根」。不归一的话, 拼接会产出 `./a` 这种前缀,
        # 与 declared_paths 里的 `a` 对不上, 已声明的条目会被误报成 extra。
        return "" if allow_empty else normalized
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
    拿到的是 1 而不是承诺的用法错档(EXIT_USAGE=3)。
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
    _require_encodable(source, "manifest 的 source")
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
        _require_encodable(entry["role"], f"items[{index}] 的 role")
        for optional_key in ("origin", "note"):
            if optional_key in entry:
                if not isinstance(entry[optional_key], str):
                    raise ManifestError(f"items[{index}] 的 {optional_key} 必须是字符串")
                _require_encodable(entry[optional_key], f"items[{index}] 的 {optional_key}")
        # optional 单独校验: 它是 bool 不是 str。写成字符串 "true" 会被静默当成真值,
        # 于是一个本该阻断的缺失被放行 —— 类型错直接拒绝加载, 不留模糊地带。
        if "optional" in entry and not isinstance(entry["optional"], bool):
            raise ManifestError(f"items[{index}] 的 optional 必须是布尔值, 实为 {type(entry['optional']).__name__}")
        # 先验类型再查枚举: `action: []` / `{}` 这类 unhashable 值直接做集合成员判断会抛
        # TypeError, 逃出 ManifestError 的捕获面, CLI 就给不出承诺的用法错档(EXIT_USAGE=3)。
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
                optional=bool(entry.get("optional", False)),
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
        _require_encodable(scan_match, f"extra_scan[{index}] 的 match")
        if "/" in scan_match:
            raise ManifestError(f"extra_scan[{index}] 的 match 只匹配单层名字, 不得含 /: {scan_match!r}")
        scan.append(ScanRoot(dir=scan_dir, match=scan_match))

    raw_allow = raw.get("extra_allow", [])
    if not isinstance(raw_allow, list):
        raise ManifestError(f"manifest 的 extra_allow 必须是列表, 实为 {type(raw_allow).__name__}")
    allow_seen: set[str] = set()
    allow: list[str] = []
    declared = _declared_paths(tuple(items))
    exclude_paths = tuple(i.path for i in items if i.action == "exclude")
    for index, entry in enumerate(raw_allow):
        # 与 item 的 path 同一套口径: 相对 / 无 .. / 可编码 / 无重复 (支持 *? glob)。
        normalized = _check_relative_segment(entry, f"extra_allow[{index}]")
        if normalized in allow_seen:
            raise ManifestError(f"extra_allow 重复声明(规范化后): {normalized!r}")
        allow_seen.add(normalized)
        clash = _overlapping_declaration(normalized, declared, exclude_paths)
        if clash is not None:
            raise ManifestError(
                f"extra_allow[{index}] {normalized!r} 与 {clash} 重叠 —— "
                f"同一路径不得既「该在这里」/「故意不复制」又「允许多出来」"
            )
        allow.append(normalized)

    return Manifest(
        version=version,
        source=source,
        items=tuple(items),
        extra_scan=tuple(scan),
        extra_allow=tuple(allow),
    )


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


def _pattern_covers(pattern: str, literal: str) -> bool:
    """pattern 是否覆盖 literal 这一条相对路径 (无通配符时退化为字符串相等)。"""
    if _has_glob(pattern):
        return bool(_pattern_to_regex(pattern).fullmatch(literal))
    return pattern == literal


def _overlapping_declaration(allow: str, declared: frozenset[str], exclude_paths: tuple[str, ...]) -> str | None:
    """extra_allow 的一项是否与 declared / exclude 重叠。返回冲突描述, None = 不重叠。

    **口径如实声明**: 这是**字面层面**的重叠判定 —— 逐条问「allow 这个模式盖不盖得住
    对方那条声明的字面文本」以及「对方那个模式盖不盖得住 allow 的字面文本」。它挡得住
    实际会出问题的三类 (完全相同 / allow 的 glob 罩住了一条已声明的字面路径 /
    exclude 的 glob 罩住了 allow 的字面路径), 但**不做两个 glob 之间的语言包含判定**
    (那需要正则交集, 不在本卡范围)。所以 `a/*x` 与 `a/y*` 这种「都能匹配 a/yx」的
    交叉不会被拒 —— 登记为已知边界, 不假称穷尽。
    """
    for path in sorted(declared):
        if _pattern_covers(allow, path) or _pattern_covers(path, allow):
            return f"已声明项 {path!r}"
    for path in exclude_paths:
        if _pattern_covers(allow, path) or _pattern_covers(path, allow):
            return f"exclude 项 {path!r}"
    return None


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


def _entry_state(path: Path) -> str:
    """`"present"` / `"absent"` / `"unreadable"` —— 取代 `Path.exists()` 做存在性判断。

    **`exists()` 把「不存在」和「问不出来」都返回 False**(它吞 `OSError`): 一个因为祖先目录
    缺搜索权限而 stat 不到的条目, 看起来跟「压根没这个文件」一模一样。于是 exclude 分类
    在**进入** `_walk()` 的错误透传链**之前**就提前返回了空, 报告照样 0 —— 与 `_digest`
    早先「两侧都读不动就判等」同一形态, 只是换了个入口。

    用 `os.lstat` 而不是 `stat`: 悬空软链要算 present(那个目录项确实在, 部署脚本也会删它),
    这与 `hits_for` 原先 `exists() or is_symlink()` 的意图一致。
    """
    try:
        os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        # ENOTDIR 是**确定的**否定答案(路径中间某段是普通文件 ⇒ 这条路径不可能存在),
        # 与「权限不足问不出来」不是一回事。归 absent, 否则 exclude 会被误阻断。
        return "absent"
    except OSError:
        return "unreadable"
    return "present"


def _iter_relative(root: Path, base: Path, unreadable: list[str] | None = None) -> list[str]:
    """列出 root 子树里全部条目相对 base 的 POSIX 路径 (含 root 自身)。

    `unreadable` 给了就把**读不动的位置**一并上报 —— 早先这里遇到读不动只是把它当成
    一个普通条目塞进列表, 调用方(exclude 分类)无从知道发生过遍历失败: 于是
    「一个读不进去的目录里藏着 exclude 项」会被静默跳过, 报告照样 0。
    那是漏报, 与 `_digest` 早先的「摘要相等就算一致」同一形态。
    (UAT-CARD-G2-6 「未证明」#25, 由 CARD-RV-G2-6 收口。)
    """
    state = _entry_state(root)
    if state == "unreadable":
        # 扫描面的根就问不出来 —— 不能当成「这里没有可排除的东西」。
        if unreadable is not None:
            unreadable.append(root.relative_to(base).as_posix() if root != base else ".")
        return []
    if state == "absent":
        return []
    out = [root.relative_to(base).as_posix()] if root != base else []
    if root.is_dir() and not root.is_symlink():
        prefix = root.relative_to(base).as_posix() if root != base else ""
        for rel, kind in _walk(root):
            if kind == "unreadable":
                if unreadable is not None:
                    here = f"{prefix}/{rel}" if prefix and rel else (prefix or rel)
                    unreadable.append(here)
                if not rel:
                    continue
            out.append(f"{prefix}/{rel}" if prefix else rel)
    return out


def _resolved_kind(path: Path) -> str:
    """跟随软链之后的类型: `"dir"` / `"file"` / `"other"` / `"unreadable"`。

    `lstat` 成功只说明**那个目录项**在, 不说明它指向的东西查得到 —— 一条指向不可搜索
    目录里对象的软链, `_entry_state` 是 present, 而 `is_dir()` / `is_file()` 仍会
    (吞掉 OSError 后)返回 False。用它们判「不是目录 ⇒ 不扫描」「不是文件 ⇒ 产物没生成」
    就又把「问不出来」说成了「不是」。
    """
    try:
        st = os.stat(path)
    except OSError:
        return "unreadable"
    if stat.S_ISDIR(st.st_mode):
        return "dir"
    if stat.S_ISREG(st.st_mode):
        return "file"
    return "other"


def _kind_ok(item: Item, path: Path) -> bool | None:
    """item.kind 声明的类型条件是否被 path 满足。

    对应 install-vault.sh 里那两条命令自带的类型限定:
      :84 `find ... -type d -name __pycache__`  → 只剪目录 (find 默认不跟随软链)
      :86 强制删除 `pending_archives*.jsonl`     → 删一切**非目录**条目
    kind 为空 = 不限类型 (`:68`/`:69` 那些按路径声明「不复制」的项本就没有类型条件)。
    """
    if _entry_state(path) == "unreadable":
        # **三态**: 问不出类型就返回 None(「判不了」), 既不宣称满足、也不宣称不满足。
        # round-4 曾一律返回 False —— 那既丢了失败原因(调用方无从登记 unreadable),
        # 又会把一个查不动的条目从「故意不复制」翻成「清单外的 extra」= 误报。
        # 原写法 `not (is_dir() and not is_symlink())` 在谓词被权限吞掉时恒为 True,
        # 于是查不动的条目会被当成 nondir 而误判为「故意不复制」= 漏报。两个方向都不对。
        return None
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
    (CARD-G2-7a 起 digest 侧还复用它过滤 generate 项, 见 verify() 里的 `generated`)
    三处各写一份判断就会互相漂移: 摘要那一处曾没用上排除规则, 于是一个被正确部署
    (脚本已剪掉 __pycache__) 的 vault 反被报 drift。
    """

    def __init__(self, items: tuple[Item, ...]) -> None:
        self._rules = [(item, _pattern_to_regex(item.path) if _has_glob(item.path) else None) for item in items]

    def matches_exact(self, base: Path, rel: str, unreadable: list[str] | None = None) -> bool:
        """rel 这一条本身是否被某条 exclude 覆盖 (含类型条件)。

        类型判不了时(`_kind_ok` 返回 None)**不算命中**, 但会把位置透传给 `unreadable` ——
        「判不了」既不能说成「排除了」(漏报), 也不能默默说成「没排除」(会翻成误报 extra)。
        """
        for item, regex in self._rules:
            hit = bool(regex.fullmatch(rel)) if regex is not None else rel == item.path
            if not hit:
                continue
            verdict = _kind_ok(item, base / rel)
            if verdict is None:
                if unreadable is not None and rel not in unreadable:
                    unreadable.append(rel)
                continue
            if verdict:
                return True
        return False

    def is_under_exclusion(self, base: Path, rel: str, unreadable: list[str] | None = None) -> bool:
        """rel 本身**或它的任一祖先**被排除 —— 用于整棵剪掉被排除的子树。"""
        parts = rel.split("/")
        return any(self.matches_exact(base, "/".join(parts[:n]), unreadable) for n in range(1, len(parts) + 1))

    def hits_for(self, vault: Path, item: Item, unreadable: list[str] | None = None) -> list[str]:
        """单条 exclude 在 vault 里实际命中的相对路径 (按静态前缀限定遍历面)。

        `unreadable` 给了就透传遍历失败的位置 —— 扫不完就不能说「这条排除项不在目标里」。
        """
        if not _has_glob(item.path):
            target = vault / item.path
            # 用 lstat 口径(`_entry_state`): 悬空软链算 present —— 那个目录项**确实在目标里**
            # (部署脚本也会删它), 不登记就等于漏报; 而「问不出来」必须与「不存在」分开,
            # 否则一个 stat 不到的排除项会被静默当成「不在这儿」。
            state = _entry_state(target)
            if state == "unreadable":
                if unreadable is not None:
                    unreadable.append(item.path)
                return []
            verdict = _kind_ok(item, target)
            if verdict is None:
                if unreadable is not None:
                    unreadable.append(item.path)
                return []
            return [item.path] if state == "present" and verdict else []
        prefix = _static_prefix(item.path)
        scan_root = vault / prefix if prefix else vault
        regex = _pattern_to_regex(item.path)
        hits: list[str] = []
        for rel in _iter_relative(scan_root, vault, unreadable):
            if not regex.fullmatch(rel):
                continue
            verdict = _kind_ok(item, vault / rel)
            if verdict is None:
                if unreadable is not None and rel not in unreadable:
                    unreadable.append(rel)
                continue
            if verdict:
                hits.append(rel)
        return sorted(hits)


# ── 内容摘要 ─────────────────────────────────────────────────────────


def _leaf_digest(path: Path) -> tuple[str, bool]:
    """单个条目的 (摘要, 是否读不动)。软链记**原始**指向, 普通文件记字节, 其余记类型位。

    **必须把「读不动」一并返回**: 早先这里遇到 OSError 只是返回一个标记字符串,
    调用方无从知道发生过读取失败 —— 于是「两侧同名文件都是 000 权限、内容其实不同」
    会摘要相等、unreadable 为空、退出码 0。那是假绿, 比误报危险。

    两处「摘要在编码之前就丢信息」的坑(round-4 复审抓到, 换编码器救不回来):
      1. **软链目标必须用 `os.readlink` 取原文**。`str(Path.readlink())` 会做路径规范化 ——
         `payload/` → `payload`(尾斜杠是「目标必须是目录」的语义)、`x//y` 与 `x/./y` 也被
         并成 `x/y` —— 于是语义不同的两个目标判等。
      2. **非「软链/普通文件/目录」的条目必须带类型位**。FIFO、Unix socket、设备节点
         原先一律记成同一个 `"?:unknown"`, 两个不同类型的特殊文件因此判等。

    单次 `lstat` 决定分支, 不再用会吞 OSError 的 `is_*()` 谓词(那几个在权限不足时
    **全部返回 False**, 会一路落到末尾的兜底分支且 bad=False)。
    """
    try:
        st = os.lstat(path)
    except OSError:
        return "U:unreadable", True
    if stat.S_ISLNK(st.st_mode):
        try:
            target = os.readlink(path)
        except OSError:
            return "U:unreadable", True
        return "L:" + hashlib.sha256(target.encode("utf-8", "surrogatepass")).hexdigest(), False
    if stat.S_ISREG(st.st_mode):
        try:
            data = path.read_bytes()
        except OSError:
            return "U:unreadable", True
        return "F:" + hashlib.sha256(data).hexdigest(), False
    if stat.S_ISDIR(st.st_mode):
        return "D:", False
    return "?:%06o" % stat.S_IFMT(st.st_mode), False


def _probe_regular_readable(path: Path) -> tuple[bool, str]:
    """generate 件的形态+可读性探测: 必须是**不经软链**的普通文件, 且真能读到第一个字节。

    两处都不能省(Codex round-3 MEDIUM):
      1. `is_file()` **跟随软链** —— 一条指向别处普通文件的链会判 True, 而 `_leaf_digest`
         对链只读 `readlink` 原文、永远 bad=False ⇒ 「链到 chmod 000 文件」记 match、rc=0。
         生成件按定义是脚本自己写出来的实体文件, 用 `lstat` + `S_ISREG` 判。
      2. 可读性要**真开一次**。但只读 1 字节就够 —— 早先复用 `_leaf_digest` 会把整份文件
         读进内存做哈希、结果又不使用(16 MiB 生成件 ⇒ 同量级分配峰值), 纯浪费。

    **它证明什么、不证明什么**(Codex round-4 LOW, 如实收窄):
      证明 = 末级路径项本身是普通文件(不经软链) + `open()` 成功 + 第一次 `read(1)` 不抛。
      **不**证明 = 整件可读(首字节之后坏块/截断的网络文件仍会放行; 空文件也放行,
      那是合法形态), 也**不**排除**祖先目录**是软链(只看末级项自己的 lstat)。
    """
    try:
        st = os.lstat(path)
    except OSError as exc:
        return False, f"读不到条目状态 ({exc.__class__.__name__})"
    if stat.S_ISLNK(st.st_mode):
        return False, "生成件是软链 (应为脚本写出的实体文件)"
    if not stat.S_ISREG(st.st_mode):
        return False, "生成件不是普通文件 (应为脚本生成的单文件)"
    try:
        with open(path, "rb") as fh:
            fh.read(1)
    except OSError as exc:
        return False, f"生成件在位但读不动 ({exc.__class__.__name__})"
    return True, ""


def _digest_pairs(
    path: Path,
    excluder: ExcludeMatcher | None = None,
    base: Path | None = None,
    unreadable: list[str] | None = None,
    generated: ExcludeMatcher | None = None,
    follow_root: bool = False,
) -> list[tuple[str, str]]:
    """产出 (相对 base 的路径, 叶子摘要) 对。非目录时只有一条。只读, 单次遍历。

    key 一律取「相对 base」(没给 base 就退回相对 path) —— 两侧同一 item 的 key 完全一致,
    `_fold()` 的 skip 集才能在两侧同时生效。

    给了 excluder + base 时, **被 exclude 覆盖的子孙整棵剔除** —— 否则
    「模板源里有 __pycache__ / 归档队列, 目标按脚本剪掉了」这种**正确部署**会被
    判成 content-drift。读不进去的条目写成 U: 参与摘要, 并登记到 unreadable。
    """
    root_key = ""
    if base is not None and path != base:
        try:
            root_key = path.relative_to(base).as_posix()
        except ValueError:  # pragma: no cover — path 总在 base 之下
            root_key = path.name

    def _note(key: str) -> None:
        if unreadable is not None:
            unreadable.append(key)

    if follow_root and path.is_symlink():
        # 与 install-vault.sh 的 `cp -R -H` 对齐: 那条命令**跟随操作数软链**, 把内容复制
        # 成实体目录。若这里仍按「链记 readlink 原文」摘要, 源侧是 L:、目标侧是内容摘要
        # ⇒ **完全正确的复制也报 content-drift**(Codex round-3 MEDIUM)。只跟随**根**这一
        # 层, 与 -H 的语义一致 —— 目录内部的链两侧都仍记原文(那是 _leaf_digest 的既有语义,
        # 只证明「链接原文相同」, 不证明解引用后的内容相同)。
        try:
            path = Path(os.path.realpath(path, strict=True))
        except OSError:
            _note(root_key or path.name)
            return [(root_key, "U:unreadable")]

    if path.is_symlink() or not path.is_dir():
        digest, bad = _leaf_digest(path)
        if bad:
            _note(root_key or path.name)
        return [(root_key, digest)]

    pairs: list[tuple[str, str]] = []
    for rel, kind in sorted(_walk(path)):
        child = path / rel if rel else path
        key = f"{root_key}/{rel}" if root_key and rel else (root_key or rel)
        if excluder is not None and base is not None and excluder.is_under_exclusion(base, key, unreadable):
            continue
        if generated is not None and base is not None and generated.is_under_exclusion(base, key):
            # generate 项按定义**每个 vault 都不同**(密钥/绑定值/按 vault 重生), 它的内容
            # 不参与任何**父目录**的内容摘要 —— 否则「脚本刚生成了 data.json」会被报成
            # 父插件目录的 content-drift。条目自身的 generate 不评 drift 是既有规则,
            # 这里只是把它推广到嵌套形态(generate 项落在 copy 目录里面)。
            continue
        if kind == "unreadable":
            _note(key)
            pairs.append((key, "U:unreadable"))
            continue
        leaf, bad = _leaf_digest(child)
        if bad:
            _note(key)
        pairs.append((key, leaf))
    return pairs


def _fold(pairs: list[tuple[str, str]], skip: frozenset[str] = frozenset()) -> str:
    """把 (路径, 叶子摘要) 对折成一个摘要; `skip` 里的路径整条排除。

    `skip` 的用处: 把**任一侧**读不动的那些位置从两侧**同时**剔掉。否则
    「两侧内容其实相同、只有一侧读不动」会因为一边是 U: 标记而摘要不同,
    被报成 content-drift —— 把「读取能力的差异」说成「字节的差异」, 会把人引到
    错误的排查方向。剔掉之后, 剩下能读的部分若仍不同, 那才是真漂移。
    """
    if len(pairs) == 1 and not pairs[0][0]:
        return pairs[0][1]
    acc = hashlib.sha256()
    for key, leaf in pairs:
        if key in skip:
            continue
        acc.update(f"{key}\0{leaf}\n".encode("utf-8", "surrogatepass"))
    return "D:" + acc.hexdigest()


def _digest(
    path: Path,
    excluder: ExcludeMatcher | None = None,
    base: Path | None = None,
    unreadable: list[str] | None = None,
) -> str:
    """目录按 (相对路径, 叶子摘要) 的稳定聚合; 非目录直接取叶子摘要。只读。"""
    return _fold(_digest_pairs(path, excluder, base, unreadable))


# ── 报告落点与落盘 ───────────────────────────────────────────────────


SYMLINK_FOLLOW_DEPTH = 4


def _forbidden_roots(tree: Path) -> tuple[list[Path], list[str]]:
    """返回 (禁写根列表, 扫描没跑完的位置)。

    报告落点不能只按「路径是否在 tree 前缀下」判: vault 里一条指向树外目录的软链,
    会让一个「树外」路径其实就是 vault 里看得见的文件。而且**得递归展开** ——
    `vault/link → A` 且 `A/link → B` 时, 只解析一层就漏掉 B, 报告写进 B 照样能被
    vault 看见。按目录身份去重, 天然处理软链成环。

    扫描不动的地方(比如权限 0111 的目录: 能按名字访问、不能列目录)必须**如实上报**,
    调用方据此拒绝落盘 —— 扫不完就不能声称安全。
    已知边界: 深度上限 SYMLINK_FOLLOW_DEPTH; 这一遍之后新建的别名不在覆盖范围内。
    """
    roots: list[Path] = []
    failures: list[str] = []
    seen: set[tuple[int, int]] = set()
    queue: list[tuple[Path, int]] = [(tree, 0)]
    while queue:
        cur, depth = queue.pop()
        ident = _fs_identity(cur)
        if ident is not None:
            if ident in seen:
                continue
            seen.add(ident)
        roots.append(cur)
        if depth >= SYMLINK_FOLLOW_DEPTH:
            failures.append(f"{cur} (软链展开超过 {SYMLINK_FOLLOW_DEPTH} 层, 未继续)")
            continue
        for rel, kind in _walk(cur):
            if kind == "unreadable":
                failures.append(f"{cur}/{rel}" if rel else str(cur))
                continue
            if kind != "symlink":
                continue
            link = cur / rel
            try:
                target = link.resolve()
            except OSError:
                # 实测(本机 Python 3.14.4): 悬空软链**不走这里** —— resolve() 会返回那个
                # 尚不存在的目标路径; 自环也不抛, 返回一个没完全解析开的路径。
                # 这个分支实际覆盖的是别的 OSError(权限等), 留着是因为拿不到目标就
                # 无法判断它是否出树, 必须计入 failures 让调用方拒绝落盘。
                failures.append(str(link))
                continue
            if target.is_dir():
                queue.append((target, depth + 1))
            else:
                roots.append(target)
    return roots, failures


def _write_report(path: Path, text: str, guard: LocationGuard | None = None) -> None:
    """写新 inode 再换目录项 —— 绝不原地覆盖一个已经存在的 inode。

    原地 `write_text` 会顺着任何别名写穿: 硬链接、`/dev/fd/N`(它 resolve 成自身、
    stat 又返回被打开文件的属性且 nlink=1)。`os.replace` 换的是目录项, 旧 inode 的
    其它名字仍指向旧内容。

    三条纪律, 每条都对应一个实测出来的坏结果:
      - 临时名带 pid + 随机串, 且**临时落点也过一遍 guard** —— 它同样是一次真实写入;
      - `O_EXCL` 失败意味着那个文件**不是本次创建的**, 绝不能清理它
        (实测过: 无条件 unlink 会删掉别人的文件, 让指向它的软链变悬空);
      - `os.write` 会短写(实测 RLIMIT_FSIZE 下只写进 1 字节却正常返回),
        必须循环写满才换目录项, 否则会发布一份截断的报告。
    """
    data = text.encode("utf-8")
    tmp = path.parent / f".{path.name}.tmp-{os.getpid()}-{os.urandom(4).hex()}"
    if guard is not None:
        problem = guard(tmp)
        if problem is not None:
            raise ReportWriteError(f"临时落点不安全: {problem}")
    fd = None
    created = False
    try:
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        written = 0
        while written < len(data):
            chunk = os.write(fd, data[written:])
            if chunk <= 0:  # pragma: no cover — 正常内核不会返回 0
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
        if created:  # 只清理本次真正创建的那一个
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
    # 摘要过滤用: exclude 项 + generate 项都不参与父目录摘要(见 _digest_pairs)。
    generated = ExcludeMatcher(tuple(i for i in manifest.items if i.action == "generate"))
    scan_failures_seen: set[str] = set()

    for item in manifest.items:
        if item.action == "exclude":
            scan_failures: list[str] = []
            hits = excluder.hits_for(vault, item, scan_failures)
            for rel in scan_failures:
                # 同一个读不动的目录会被多条 exclude 的前缀扫到, 只登记一次。
                if rel in scan_failures_seen:
                    continue
                scan_failures_seen.add(rel)
                report.unreadable.append(
                    Finding(
                        path=rel,
                        category="unreadable",
                        action=item.action,
                        role=item.role,
                        detail="exclude 覆盖面读不进去, 无法确认这条排除项在不在目标里",
                    )
                )
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
        target_state = _entry_state(target)
        if target_state == "unreadable":
            # 「问不出来」不是「不在」: 降级成 missing 会给出 rc=1(只缺东西), 而实情是
            # 这一项根本没被核对过。归 unreadable ⇒ rc=2, 并在报告里说清原因。
            report.unreadable.append(
                Finding(
                    path=item.path,
                    category="unreadable",
                    action=item.action,
                    role=item.role,
                    detail="查询不到(祖先目录不可搜索等), 无法判断它在不在目标里",
                )
            )
            continue
        if target_state == "absent":
            detail = ""
            if item.action == "copy" and source is not None:
                src_state = _entry_state(source / item.path)
                if src_state == "absent":
                    detail = "模板源也没有这一项 (install-vault.sh 会打 ⚠️ 跳过)"
                elif src_state == "unreadable":
                    detail = "模板源那一项查询不到, 不能断言「模板源也没有」"
                    # 已经发生的查询失败必须进四档分类, 不能只躺在 missing 的说明里 ——
                    # 否则整轮可能 unreadable=0、rc=1, 看上去「只是缺东西」。
                    report.unreadable.append(
                        Finding(
                            path=item.path,
                            category="unreadable",
                            action=item.action,
                            role=item.role,
                            detail="模板源那一项查询不到, 无法判断它在不在模板源里",
                        )
                    )
            if item.optional:
                # 声明为 optional 的项缺失 ⇒ 只报告, 不进退出码。
                # 它仍留在 declared_paths 里 —— 在位时不会被反过来报成 extra。
                report.optional_missing.append(
                    Finding(
                        path=item.path,
                        category="optional-missing",
                        action=item.action,
                        role=item.role,
                        detail=detail or "声明为 optional, 允许缺失 (不计退出码)",
                    )
                )
                continue
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
        # 但**形态**仍要查: digest 侧会把 generate 路径从父目录摘要整棵剔掉(见
        # _digest_pairs 的 generated 过滤), 若不在这里查, 「data.json 被误建成目录」
        # 这类形态错误就完全没有信号 —— 存在即 match, 父摘要又看不见它。
        # (Codex round-1 MEDIUM)
        if item.action == "generate":
            ok, why = _probe_regular_readable(target)
            if not ok:
                report.unreadable.append(
                    Finding(
                        path=item.path,
                        category="unreadable",
                        action=item.action,
                        role=item.role,
                        detail=why,
                    )
                )
                continue
        if item.action == "copy" and source is not None:
            src = source / item.path
            if not src.exists():
                # 目标有、模板源没有 ⇒ 两侧无从比较。**不能记 match** —— match 读起来就是
                # 「核对过, 一致」, 而这一项根本没比过。归 unreadable(「看不见不等于一致」
                # 的同一条纪律), 计入阻断并在报告里说清原因。
                report.unreadable.append(
                    Finding(
                        path=item.path,
                        category="unreadable",
                        action=item.action,
                        role=item.role,
                        detail="模板源没有这一项, 无法证明内容一致 (install-vault.sh 会 ⚠️ 跳过它)",
                    )
                )
                continue
            src_unreadable: list[str] = []
            tgt_unreadable: list[str] = []
            src_pairs = _digest_pairs(src, excluder, source, src_unreadable, generated, follow_root=True)
            tgt_pairs = _digest_pairs(target, excluder, vault, tgt_unreadable, generated)
            unreadable_here = src_unreadable + tgt_unreadable
            # 把**任一侧**读不动的位置从两侧同时剔掉再比 —— 否则「两侧内容其实相同、
            # 只有一侧读不动」会因为一边是 U: 标记而摘要不同, 被报成 content-drift,
            # 把「读取能力的差异」说成「字节的差异」。
            skip = frozenset(src_unreadable) | frozenset(tgt_unreadable)
            src_digest = _fold(src_pairs, skip)
            tgt_digest = _fold(tgt_pairs, skip)
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
            # 顺序要紧: **先判漂移再判读不动**。反过来写(读不动就直接 continue)会把
            # 同一项里**已经看得见的**内容差异一起吃掉 —— 报告的 content-drift 变成 0,
            # 退出码虽仍是 2, 分类信息却退化了。
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
            if unreadable_here:
                # 摘要相等但有读不动的条目 ⇒ 这一项**没被证明一致**, 不能记 match。
                # (两侧都写同一个 U: 标记会让它们「判等」—— 那正是假绿的来源。)
                continue

        report.match.append(Finding(path=item.path, category="match", action=item.action, role=item.role))

    _collect_extra(vault, manifest, report, excluder)
    _check_hotkeys(vault, report)
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
        if _entry_state(scan_dir) == "unreadable":
            # 覆盖面的根问不出来 ⇒ 不能说「这里没有清单外的东西」。
            report.unreadable.append(
                Finding(
                    path=scan.dir or ".",
                    category="unreadable",
                    action="-",
                    role="-",
                    detail="extra 覆盖面的根查询不到, 无法证明没有清单外的东西",
                )
            )
            continue
        resolved = _resolved_kind(scan_dir)
        if resolved == "unreadable":
            report.unreadable.append(
                Finding(
                    path=scan.dir or ".",
                    category="unreadable",
                    action="-",
                    role="-",
                    detail="extra 覆盖面的根跟随软链后查询不到, 无法证明没有清单外的东西",
                )
            )
            continue
        if resolved != "dir":
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
            allowed_by = next((a for a in manifest.extra_allow if _pattern_covers(a, rel)), None)
            if allowed_by is not None:
                report.allowed_extra.append(
                    Finding(
                        path=rel,
                        category="allowed-extra",
                        action="-",
                        role="-",
                        detail=f"由 extra_allow 的 {allowed_by!r} 放行 (只报告, 不计退出码)",
                    )
                )
                continue
            report.extra.append(
                Finding(
                    path=rel,
                    category="extra",
                    action="-",
                    role="-",
                    detail=f"位于覆盖面 {scan.dir}/{scan.match} 内但不在 manifest",
                )
            )


def _check_hotkeys(vault: Path, report: Report) -> None:
    """hotkeys.json 绑的命令 id 必须在同一 vault 的 main.js 里真实存在 (CARD-RV-G2-6)。

    只看**同一个 vault 内**的两份文件, 不去读仓库源码 —— 校验的是「这个 vault 自洽」,
    而不是「这个 vault 和某棵开发树一致」。真相源 (`frontend/obsidian-plugin/src/main.ts`
    恰 10 个命令 id) 由测试层单独钉住, 那是**开发树**的约束, 不是**部署产物**的约束。

    三条早退各自说清楚为什么, 不静默:
      - 没有 hotkeys.json: 无可核对 (它本身是 copy 项, 缺了会另行报 missing);
      - 没有 main.js: 它是 gitignored 的构建产物, 未构建的树里本就没有 ⇒ `not evaluated`,
        **不计退出码**。把「没法查」记成「查过没问题」是假绿, 所以报告里必须留这行字。
      - 读不动 / 不是合法 JSON / 顶层不是对象: 记 unreadable (计入阻断) —— 看不见不等于一致。
    无 `canvas-learning-system:` 前缀的键是别的插件的快捷键, 一律忽略。
    """
    hotkeys_path = vault / HOTKEYS_REL
    main_js_path = vault / PLUGIN_MAIN_JS_REL

    def _unreadable(path_rel: str, detail: str, note: str) -> None:
        report.unreadable.append(Finding(path=path_rel, category="unreadable", action="-", role="-", detail=detail))
        report.hotkeys_note = note

    hotkeys_state = _entry_state(hotkeys_path)
    main_js_state = _entry_state(main_js_path)
    # 「查询不到」与「确实没有」必须分开: 前者是 unreadable(计入阻断), 后者才是
    # 「无可核对 / 构建产物没生成」这类不计 rc 的说明。把前者说成后者 = 把「没法查」
    # 记成「查过了没问题」。
    for state, rel, what in (
        (hotkeys_state, HOTKEYS_REL, "快捷键清单"),
        (main_js_state, PLUGIN_MAIN_JS_REL, "插件构建产物"),
    ):
        if state == "unreadable":
            _unreadable(rel, f"{what}查询不到, 无法核对快捷键", f"not evaluated ({rel} 查询不到)")
            return
    if hotkeys_state == "absent":
        report.hotkeys_note = f"not evaluated (无 {HOTKEYS_REL})"
        return
    # ⚠️ 顺序要紧: hotkeys **自身**的结构必须先独立验完, 再看 main.js 在不在。
    # 反过来写(缺 main.js 就直接 not evaluated)会让「hotkeys 顶层是数组/字符串」这类
    # 结构错误在树源部署下完全无声 —— 两层检查同时放行, rc=0(Codex round-4 MEDIUM)。
    try:
        raw = hotkeys_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _unreadable(HOTKEYS_REL, f"快捷键文件读不进去: {exc}", "not evaluated (读不进去)")
        return
    try:
        bindings = json.loads(raw)
    except ValueError as exc:
        _unreadable(HOTKEYS_REL, f"不是合法 JSON, 无法核对快捷键: {exc}", "not evaluated (JSON 非法)")
        return
    if not isinstance(bindings, dict):
        _unreadable(
            HOTKEYS_REL,
            f"顶层不是对象 (实为 {type(bindings).__name__}), 无法核对快捷键",
            "not evaluated (结构非法)",
        )
        return

    if main_js_state == "absent":
        report.hotkeys_note = f"not evaluated ({PLUGIN_MAIN_JS_REL} 缺 — gitignored 构建产物)"
        return
    main_js_kind = _resolved_kind(main_js_path)
    if main_js_kind == "unreadable":
        # lstat 成功但跟随软链后查不到 —— 「问不出来」不得说成「产物没生成」。
        _unreadable(
            PLUGIN_MAIN_JS_REL,
            "插件构建产物跟随软链后查询不到, 无法核对快捷键",
            f"not evaluated ({PLUGIN_MAIN_JS_REL} 查询不到)",
        )
        return
    if main_js_kind != "file":
        report.hotkeys_note = f"not evaluated ({PLUGIN_MAIN_JS_REL} 不是普通文件)"
        return
    try:
        source = main_js_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError) as exc:
        _unreadable(PLUGIN_MAIN_JS_REL, f"插件产物读不进去: {exc}", "not evaluated (读不进去)")
        return

    known = {m.group(2) for m in COMMAND_ID_RE.finditer(source)}
    bound = sorted(k for k in bindings if k.startswith(HOTKEY_PREFIX))
    if bound and not known:
        # 一条命令 id 都没解析出来, 而快捷键确实绑了东西 —— 更可能是产物格式变了,
        # 不是「插件真的一个命令都没有」。此时把每条绑定都报成 orphan, 会给出 N 条
        # **说错原因**的结论: 阻断是对的, 理由却是假的。改报「没法核对」。
        # 代价如实声明: 插件真的零命令而快捷键有陈旧绑定时, 也会归到这一档。
        _unreadable(
            PLUGIN_MAIN_JS_REL,
            f"没解析出任何命令 id 字面量, 无法核对 {len(bound)} 条快捷键绑定",
            f"not evaluated (产物里 0 个命令 id, {len(bound)} 条绑定未核对)",
        )
        return
    for key in bound:
        if key[len(HOTKEY_PREFIX) :] not in known:
            report.hotkey_orphan.append(
                Finding(
                    path=key,
                    category="hotkey-orphan",
                    action="-",
                    role="-",
                    detail=f"{PLUGIN_MAIN_JS_REL} 里没有这个命令 id (产物内共 {len(known)} 个)",
                )
            )
    report.hotkeys_note = f"{len(bound)} 绑定 / {len(known)} 命令 / {len(report.hotkey_orphan)} orphan"


# ── 报告渲染 ─────────────────────────────────────────────────────────


def _printable(text: str) -> str:
    """把无法编码成 UTF-8 的字符转义成可见形式, 保证报告一定落得下去。

    报告里的字符串有两个来源: **manifest**(加载阶段已被 `_require_encodable` 挡过) 与
    **被查 vault 本身**(hotkeys.json 的键、`os.scandir` 给出的文件名)。后者没有任何
    可编码性保证 —— JSON 里那个 6 字符的代理转义 (反斜杠 u d 8 0 0) 会被 `json.loads`
    解成孤立代理字符, 文件系统的
    非法字节会被 surrogateescape 解成同一类字符。它们一旦进了报告文本, 落盘时抛的
    `UnicodeEncodeError` 会**逃出** `ReportWriteError` 的捕获面(那里只捕 `OSError`),
    调用方拿到的是 traceback 而不是承诺的退出码。

    这正是 round-3 MEDIUM 已经修过的形态, 只是换了个输入面重开 —— 所以这次收在
    **输出边界**上, 一处覆盖全部来源, 而不是给每个新桶各补一道。
    """
    return text.encode("utf-8", "backslashreplace").decode("utf-8")


def render(report: Report, manifest: Manifest) -> str:
    lines = [
        "# vault-install verification report (CARD-G2-6, read-only)",
        f"# manifest : {report.manifest_path} (version {manifest.version}, source {manifest.source})",
        f"# vault    : {report.vault}",
        f"# source   : {report.source if report.source else '(未提供 — content-drift 未评估)'}",
        "# 语义     : exclude 项按各自模式的静态前缀子树扫描; extra 只看 manifest",
        "#            extra_scan 声明的覆盖面 (根级文档不在覆盖面内, 故不报 extra);",
        "#            读不进去的条目记 unreadable 并计入退出码 —— 看不见不等于一致;",
        "#            extra_allow 放行的项进 allowed-extra, 只报告不计退出码;",
        "#            声明为 optional 的项缺失进 optional-missing, 同样不计退出码;",
        "#            退出码 0 ok / 1 只缺 / 2 多出·漂移·读不动·快捷键孤儿 / 3 用法错。",
        "-" * 66,
        f"match                  : {len(report.match)}",
        f"missing                : {len(report.missing)}",
        f"extra                  : {len(report.extra)}",
        "content-drift          : "
        + (str(len(report.content_drift)) if report.drift_evaluated else "not evaluated (无 --source)"),
        f"intentionally-excluded : {len(report.intentionally_excluded)}",
        f"allowed-extra          : {len(report.allowed_extra)}",
        f"optional-missing       : {len(report.optional_missing)}",
        f"unreadable             : {len(report.unreadable)}",
        f"hotkeys                : {report.hotkeys_note}",
        f"hotkey-orphan          : {len(report.hotkey_orphan)}",
    ]
    for title, findings in (
        ("missing", report.missing),
        ("extra", report.extra),
        ("content-drift", report.content_drift),
        ("unreadable", report.unreadable),
        ("hotkey-orphan", report.hotkey_orphan),
        ("intentionally-excluded", report.intentionally_excluded),
        ("allowed-extra", report.allowed_extra),
        ("optional-missing", report.optional_missing),
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
    return _printable("\n".join(lines) + "\n")


# ── CLI ──────────────────────────────────────────────────────────────


class _Parser(argparse.ArgumentParser):
    """把 argparse 的参数错误出口从 2 改成 EXIT_USAGE。

    argparse 默认 `sys.exit(2)` —— 而 rc=2 在四档语义里是 **mismatch**(「多出来 / 对不上」)。
    不改就会出现「命令行都没写对, 调用方却读成『vault 有多余文件』」。
    """

    def error(self, message: str):  # noqa: ANN201 — 与基类同签名, 不返回
        self.print_usage(sys.stderr)
        print(f"❌ 参数错误: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="verify_vault_install.py",
        description="只读校验一个 vault 是否符合 vault-install-manifest.json 声明的部署边界。",
    )
    parser.add_argument("--vault", required=True, help="待校验的 vault 目录 (只读)")
    parser.add_argument("--source", help="模板源 vault, 给了才评 content-drift (只读)")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="清单路径")
    parser.add_argument("--report", help="报告落盘路径, 缺省写 stdout; 不得落在被查树里")
    return parser


def _expanduser(raw: str) -> tuple[Path | None, str | None]:
    """`~未知用户名` 会让 `expanduser()` 抛 `RuntimeError` —— 它不在任何捕获面里,
    CLI 会以 1 退出(而 1 在四档里是「只有 missing」)。统一归用法错档。"""
    try:
        return Path(raw).expanduser(), None
    except RuntimeError as exc:
        return None, f"路径展开失败: {raw!r} — {exc}"


def _resolve_dir(raw: str, label: str) -> tuple[Path | None, str | None]:
    path, err = _expanduser(raw)
    if err is not None or path is None:
        return None, f"{label} {err or '路径展开失败'}"
    if not path.is_dir():
        return None, f"{label} 不是存在的目录: {path}"
    return path.resolve(), None


def _fs_identity(path: Path) -> tuple[int, int] | None:
    """文件系统认的同一性: (st_dev, st_ino)。取不到就 None。

    比路径字符串强得多 —— 大小写差异(macOS 默认不敏感)、软链、硬链接、`.`/`..`
    冗余段, 在这个维度上全都自动归一。**但不宣称穷尽所有别名**(挂载/绑定挂载等未验)。
    """
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_dev, st.st_ino)


def _check_report_location(report_path: Path, trees: list[tuple[Path | None, str]]) -> str | None:
    """报告落点是否安全。返回错误消息, None 表示可以写。

    第一道**按身份判**: resolve() 不做大小写规范化, 而本机文件系统默认大小写不敏感 ——
    目录实际叫 `Vault` 时 `--report vault/x` 的 is_relative_to 为 False, 但两者的
    (st_dev, st_ino) 完全相同, 写下去就是写穿。路径这个维度本身不成立。
    第二道是路径前缀比较(错误信息更直观)。两道都不通过才放行。
    """
    forbidden: dict[tuple[int, int], str] = {}
    scan_failures: list[str] = []
    for tree, label in trees:
        if tree is None:
            continue
        roots, failures = _forbidden_roots(tree)
        scan_failures.extend(f"{label}: {f}" for f in failures)
        for root in roots:
            ident = _fs_identity(root)
            if ident is not None:
                forbidden.setdefault(ident, label)

    if scan_failures:
        head = "; ".join(scan_failures[:3])
        more = f" (共 {len(scan_failures)} 处)" if len(scan_failures) > 3 else ""
        return f"安全性扫描没跑完, 无法确认 --report 落点在被审树之外, 拒绝落盘: {head}{more}"

    # report 本身可能还不存在, 逐级向上找第一个 stat 得到的祖先
    probe = report_path
    while True:
        ident = _fs_identity(probe)
        if ident is not None and ident in forbidden:
            return (
                f"--report 落点位于 {forbidden[ident]} 树内 (按文件系统身份判定, "
                f"不是按路径字符串): {report_path} 的 {probe} 与被审树是同一个对象"
            )
        if probe.parent == probe:
            break
        probe = probe.parent

    for tree, label in trees:
        if tree is None:
            continue
        roots, _ = _forbidden_roots(tree)
        for root in roots:
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
        expanded, err = _expanduser(args.report)
        if err is not None or expanded is None:
            print(f"❌ --report {err or '路径展开失败'}", file=sys.stderr)
            return EXIT_USAGE
        report_path = expanded.resolve()
        trees = [(vault, "--vault"), (source, "--source")]
        problem = _check_report_location(report_path, trees)
        if problem:
            print(f"❌ {problem}", file=sys.stderr)
            return EXIT_USAGE

    manifest_path, err = _expanduser(args.manifest)
    if err is not None or manifest_path is None:
        print(f"❌ --manifest {err or '路径展开失败'}", file=sys.stderr)
        return EXIT_USAGE
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print(f"❌ manifest 不可用: {exc}", file=sys.stderr)
        return EXIT_USAGE

    report = verify(vault, manifest, source_dir=source, manifest_path=manifest_path)
    text = render(report, manifest)
    if report_path is not None:
        try:
            _write_report(report_path, text, lambda p: _check_report_location(p, trees))
        except ReportWriteError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return EXIT_USAGE
        print(f"报告已写入 {report_path}")
    else:
        sys.stdout.write(text)
    return report.exit_code


class _ClosedStdout:
    """下游把管道关掉之后顶替 `sys.stdout` 的哑对象。

    用它而不是 `os.dup2(os.open(os.devnull, ...))`: 后者是一次**可写调用**, 会让
    「所有写调用都收敛在 _write_report 内」那道 AST 门变红 —— 为了让自己的收尾代码
    过关去放宽零写门是本末倒置。两种写法实测同为 rc=3 且无退出期噪音。
    """

    def write(self, _data: str) -> int:
        return 0

    def flush(self) -> None:
        return None


if __name__ == "__main__":  # pragma: no cover
    # **输出流的可写性不在四档契约的保护范围内**, 但它照样能把退出码搅乱, 而且
    # **断在哪一步取决于缓冲**(这一点让我第一版修复漏了一半):
    #   - `PYTHONIOENCODING=ascii` 下报告正文编码失败 ⇒ 实测 rc=1, 被读成「只有 missing」;
    #   - 默认缓冲 + 下游关管道: 小报告先进管道缓冲, 直到退出期 flush 才炸 ⇒ 实测 rc=120;
    #   - `-u` 无缓冲 + 下游关管道: `sys.stdout.write(text)` **当场**抛, 异常从 main()
    #     里逃出来 ⇒ 实测 rc=1;
    #   - stderr 关掉后触发参数错误: 同样从 main() 里逃出来 ⇒ 实测 rc=120。
    # 四种都要接住 —— 只包 flush 或只测 `--help` 都只覆盖其中一条路径。
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            pass
    try:
        _rc = main()
    except SystemExit as _exc:
        # `--help` 从 argparse 内部就 sys.exit(0) 出来了, 不接住就走不到下面的 flush。
        _rc = _exc.code if isinstance(_exc.code, int) else EXIT_USAGE
    except BrokenPipeError:
        # 无缓冲 / stderr 断管: 写当场就抛。**只捕这一种**, 不捕宽泛的 OSError ——
        # 那会把校验逻辑里真正的意外错误静默成用法错档。
        sys.stdout = _ClosedStdout()  # type: ignore[assignment]
        _rc = EXIT_USAGE
    # 默认缓冲: 写进了缓冲区, 到这一步才炸。**两个流都要收** —— 只 flush stdout 时,
    # 「stderr 断管 + 参数错误」仍会在解释器退出期炸并把退出码改成 120(实测)。
    # 同时把炸掉的那个流换成哑对象, 挡住退出期的第二次 flush。
    for _name in ("stdout", "stderr"):
        try:
            getattr(sys, _name).flush()
        except (BrokenPipeError, OSError):
            setattr(sys, _name, _ClosedStdout())
            _rc = EXIT_USAGE
    sys.exit(_rc)
