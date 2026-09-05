#!/usr/bin/env python3
"""Canvas Learning System — vault 部署清单只读校验器 (CARD-G2-6)。

拿 `scripts/vault-install-manifest.json` 声明的部署边界, 去比对一个**已存在**的
vault 目录, 回答三个问题: 该有的在不在 (match / missing)、覆盖面内有没有清单外的
东西 (extra)、以及给了模板源时内容有没有漂 (content-drift)。清单里显式声明「不
复制」的项若在目标里出现, 单独记 intentionally-excluded —— 那通常是人工放的或
Obsidian 自己生成的, 不算缺陷, 只是要让审计者看见。

**只读**: 本脚本对 --vault / --source 只做 stat / 列目录 / 读字节, 没有任何写入
分支, 也没有 --fix 之类的开关。--report 若落在这两棵树里直接拒绝执行 (退出 2),
免得「审计动作本身」变成写入。

**「活 vault 即模板」**(install-vault.sh:2-6): manifest 只声明 path/role/action,
不带任何内容或哈希基线 —— 内容的参照永远是 --source 指向的那个活 vault, 本仓不
维护第二份模板。所以不给 --source 时, content-drift 一律报 "not evaluated",
而不是拿某个内置基线冒充。

退出码:
  0  没有 missing / extra / content-drift (intentionally-excluded 不进退出码)
  1  有 missing / extra / content-drift
  2  用法或配置错 (manifest 非法、目录不存在、--report 落在被查树里)

用法:
  python3 scripts/verify_vault_install.py --vault <dir> [--source <dir>]
                                          [--manifest <path>] [--report <path>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXIT_OK = 0
EXIT_DIFF = 1
EXIT_USAGE = 2

VALID_ACTIONS = frozenset({"copy", "generate", "skeleton", "exclude"})
REQUIRED_ITEM_KEYS = ("path", "role", "action")
GLOB_CHARS = "*?["

DEFAULT_MANIFEST = Path(__file__).resolve().parent / "vault-install-manifest.json"


class ManifestError(Exception):
    """manifest 结构或取值非法 —— 一律走退出码 2, 不与内容差异混为一谈。"""


@dataclass(frozen=True)
class Item:
    path: str
    role: str
    action: str
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

    @property
    def exit_code(self) -> int:
        blocking = len(self.missing) + len(self.extra) + len(self.content_drift)
        return EXIT_DIFF if blocking else EXIT_OK


# ── manifest 加载与校验 ───────────────────────────────────────────────


def _check_path_field(raw: object, seen: set[str]) -> None:
    # 形参标 object 而不是 str: 值来自 JSON, 运行时什么类型都可能, isinstance
    # 这道检查是真的在挡东西 (标成 str 会让类型检查器以为它多余)。
    if not isinstance(raw, str) or not raw:
        raise ManifestError(f"item 的 path 必须是非空字符串: {raw!r}")
    if raw.startswith("/") or Path(raw).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", raw):
        raise ManifestError(f"item 的 path 必须相对 vault 根, 不得是绝对路径: {raw!r}")
    if ".." in Path(raw).parts:
        raise ManifestError(f"item 的 path 不得含 .. 逃逸段: {raw!r}")
    if raw in seen:
        raise ManifestError(f"item 的 path 重复声明: {raw!r}")
    seen.add(raw)


def load_manifest(path: Path | str) -> Manifest:
    """读并校验 manifest。任何结构/取值问题都抛 ManifestError。"""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest 不存在: {path}") from exc
    except json.JSONDecodeError as exc:
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
        _check_path_field(entry["path"], seen)
        if not isinstance(entry["role"], str) or not entry["role"]:
            raise ManifestError(f"items[{index}] 的 role 必须是非空字符串")
        if entry["action"] not in VALID_ACTIONS:
            raise ManifestError(f"items[{index}] 的 action {entry['action']!r} 不在枚举 {sorted(VALID_ACTIONS)} 内")
        items.append(
            Item(
                path=entry["path"],
                role=entry["role"],
                action=entry["action"],
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
        scan.append(ScanRoot(dir=entry["dir"], match=entry["match"]))

    return Manifest(version=version, source=source, items=tuple(items), extra_scan=tuple(scan))


# ── glob 语义 ────────────────────────────────────────────────────────


def _pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """把 manifest 的 path 模式编译成相对路径正则。

    语义: `**/` 跨任意层目录, 结尾 `/**` = 该目录下的全部子孙, `*` 不跨 `/`。
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
    return re.compile("^" + "".join(out) + "$")


def _static_prefix(pattern: str) -> str:
    """取模式中第一个通配段之前的目录前缀 —— 用它限定遍历面, 不做全树扫描。"""
    parts = Path(pattern).parts
    keep: list[str] = []
    for part in parts:
        if any(ch in part for ch in GLOB_CHARS):
            break
        keep.append(part)
    return "/".join(keep)


def _has_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in GLOB_CHARS)


def _iter_relative(root: Path, base: Path) -> list[str]:
    """列出 root 子树里全部条目 (目录 + 文件) 相对 base 的 POSIX 路径。"""
    if not root.exists():
        return []
    out = [root.relative_to(base).as_posix()] if root != base else []
    if root.is_dir() and not root.is_symlink():
        for child in root.rglob("*"):
            out.append(child.relative_to(base).as_posix())
    return out


def _matches_in_vault(vault: Path, pattern: str) -> list[str]:
    """pattern 在 vault 里实际命中的相对路径 (已按静态前缀限定遍历面)。"""
    if not _has_glob(pattern):
        return [pattern] if (vault / pattern).exists() else []
    prefix = _static_prefix(pattern)
    scan_root = vault / prefix if prefix else vault
    regex = _pattern_to_regex(pattern)
    return sorted(rel for rel in _iter_relative(scan_root, vault) if regex.match(rel))


# ── 内容摘要 ─────────────────────────────────────────────────────────


def _digest(path: Path) -> str:
    """文件按字节, 目录按 (相对路径, 类型, 字节摘要) 的稳定聚合。只读。"""
    if path.is_symlink():
        return "L:" + hashlib.sha256(str(path.readlink()).encode("utf-8")).hexdigest()
    if path.is_file():
        return "F:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        return "?:unknown"
    acc = hashlib.sha256()
    children = sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix())
    for child in children:
        rel = child.relative_to(path).as_posix()
        acc.update(f"{rel}\0{_digest(child)}\n".encode("utf-8"))
    return "D:" + acc.hexdigest()


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

    for item in manifest.items:
        if item.action == "exclude":
            hits = _matches_in_vault(vault, item.path)
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
            if src.exists() and _digest(src) != _digest(target):
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

    _collect_extra(vault, manifest, report)
    return report


def _collect_extra(vault: Path, manifest: Manifest, report: Report) -> None:
    """覆盖面内、既不在 declared_paths 也不被 exclude 覆盖的直接子项 = extra。"""
    declared = manifest.declared_paths
    exclude_regexes = [
        (_pattern_to_regex(i.path) if _has_glob(i.path) else None, i.path) for i in manifest.exclude_items
    ]

    def is_excluded(rel: str) -> bool:
        for regex, literal in exclude_regexes:
            if regex is not None:
                if regex.match(rel):
                    return True
            elif rel == literal:
                return True
        return False

    seen: set[str] = set()
    for scan in manifest.extra_scan:
        scan_dir = vault / scan.dir
        if not scan_dir.is_dir():
            continue
        name_regex = _pattern_to_regex(scan.match)
        for child in sorted(scan_dir.iterdir(), key=lambda p: p.name):
            if not name_regex.match(child.name):
                continue
            rel = child.relative_to(vault).as_posix()
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
        "#            extra_scan 声明的覆盖面 (根级文档不在覆盖面内, 故不报 extra)。",
        "-" * 66,
        f"match                  : {len(report.match)}",
        f"missing                : {len(report.missing)}",
        f"extra                  : {len(report.extra)}",
        "content-drift          : "
        + (str(len(report.content_drift)) if report.drift_evaluated else "not evaluated (无 --source)"),
        f"intentionally-excluded : {len(report.intentionally_excluded)}",
    ]
    for title, findings in (
        ("missing", report.missing),
        ("extra", report.extra),
        ("content-drift", report.content_drift),
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


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    vault, err = _resolve_dir(args.vault, "--vault")
    if err is not None or vault is None:
        print(f"❌ {err or '--vault 解析失败'}", file=sys.stderr)
        return EXIT_USAGE
    source: Path | None = None
    if args.source:
        source, err = _resolve_dir(args.source, "--source")
        if err:
            print(f"❌ {err}", file=sys.stderr)
            return EXIT_USAGE

    report_path: Path | None = None
    if args.report:
        report_path = Path(args.report).expanduser().resolve()
        for tree, label in ((vault, "--vault"), (source, "--source")):
            if tree is not None and report_path.is_relative_to(tree):
                print(
                    f"❌ --report 不得落在 {label} 树内 (审计不写被审对象): {report_path}",
                    file=sys.stderr,
                )
                return EXIT_USAGE
        if not report_path.parent.is_dir():
            print(f"❌ --report 的上级目录不存在: {report_path.parent}", file=sys.stderr)
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
        report_path.write_text(text, encoding="utf-8")
        print(f"报告已写入 {report_path}")
    else:
        sys.stdout.write(text)
    return report.exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
