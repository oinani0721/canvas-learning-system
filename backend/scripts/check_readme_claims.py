#!/usr/bin/env python3
"""CARD-G1-5 — README 禁夸大声明机械裁判 (report / enforce / staged-diff 三档).

真相源: 计划书 §12.7 L633 的 11 类禁夸大声明, 逐条映射在同目录 readme_claims_rules.yaml
(id C1..C11 与原文语序一致)。

配置面完整钉死:
  - (id, severity, l633) 序列与 scan_paths 由 EXPECTED_RULES / EXPECTED_SCAN_PATHS 钉死
  - 规则文件**全文 SHA-256** 由 RULES_SHA256 钉死 (指纹先于 yaml 解析比对) — 改任何
    正则/legacy 条目都必须同 commit 改本文件常量, 否则退出 2。伪绿无法由 yaml 单边达成。

三档:
  --report       全量扫 scan_paths 白名单, 打印全部命中 (含 [escaped]/[legacy] 标), 恒退出 0
  --enforce      全量扫, 存在有效命中 (非 escaped 非 legacy) 即退出 1   ← CI workflow 用
  --staged-diff  只扫 git staged **新增行**, 有效命中即退出 1           ← lefthook pre-commit 用
                 (存量失实不阻断新 commit; staged 新增行**永不享受 legacy**; 字节级解析
                  只按 \\n 分行防 U+2028 类断行错位; --text 强制文本 diff; 变更文件与
                  解析结果交叉核对; 扫描目标出现 D/T/unmerged staged 状态 = 退出 2)

匹配语义:
  - 规则匹配在**剥离 HTML 注释后的可见文本**上进行 (全量档含跨行注释块状态; 藏在注释里
    的否定词/标记不影响裁判, 注释内文本对读者不可见也不构成声明); 匹配前再剥离行内
    Markdown 强调符 (` * __ ~~) — code span/加粗内文本对读者可见, 仍是声明面, 且强调
    排版切不断声明 (单个下划线保留, recall_at_5 类标识符照常匹配)
  - 行先按分句边界 ([;；。] 与后随空白/行尾的英文句号) 切分, 复合规则的 conjunct 必须
    落在**同一分句**内 — 跨分句拼接 conjunct 不判
  - 否定守卫 (仅 NEGATION_GUARD_RULES): 谓词捕获组 (?P<v>) 的**否定尾绑定**——
    否定词必须紧邻谓词 (中间只允许 be/被 类助词, _NEG_TAIL_RE 锚定检测), 无关谓词的
    not 不解除阳性; C11 量词为惰性, 取最早谓词防贪婪跨度吞掉未否定谓词——
    「do not fail but indicate success」「mean success but are not treated」均照拦,
    「Skipped is not treated as success.」放行

逃逸语法 (evidence-escapable 类): 命中行**同一行**带 `[Cx:E3](docs/evidence/…)` 证据
标注, E 级 ∈ {E3, E3+, E4, E5}。放行条件全部满足: 标记未被反斜杠转义、不藏在 HTML
注释/code span 内; x = 被命中规则编号; 链接位于 EVIDENCE_DIR (docs/evidence/) 之下、
在 git index 中以 stage-0 普通 blob 存在 (非 intent-to-add、非空 blob)、worktree 中为
非空非 symlink 普通文件、不是被扫描文件自身。EVIDENCE_DIR 已纳入 workflow paths,
证据文件的增删改会重新触发 CI 门 (生命周期闭合)。
⚠️ 诚实边界: 本裁判只验证标记与链接文件的机械性质, **不裁决证据内容成立**——E 级真伪由
G1-3 能力证据台账与 G1-6 逐声明审计链负责。

hard-forbidden (C6 hit@k 误名 recall、C11 skipped/degraded=成功):
证据标注与 legacy 登记**均不放行**, 只能改写。
C6 政策裁定 (README 范围, Codex 三轮已裁定为可接受设计决定): 本仓检索指标实为
hit rate (G4-12 正名), README 中一切 recall@k 型指标声明一律拦截——含自称"真 recall"
的表述与 Top-k recall 定义式; 未来经审计的 recall 指标走双文件指纹契约修改。
C9 政策声明: 规则目标是**双位数 Agent 阵容宣称** (README 基线三行 = 12-14/14/14,
其中两行无「协同」字样) — 不限定恰为 14, 也不要求协同字样, 属有意声明的裁定范围。

legacy_allowlist: G1-4 勘探实锤的存量失实行登记 (report 照常计数并打 [legacy] 标,
这是「已知失实待 G1-6 重写」的登记, 不是洗白)。绑定: 精确整行文本 + 文件 +
registered_line **精确行号** (容差 0 — README 改动须经用户批准, 行号漂移时走双文件
契约重钉) + 5 行上下文 SHA-256 指纹 + max_occurrences 配额。staged-diff 档完全不吃
legacy。G1-6 重写时必须删空。

已知机械边界 (诚实声明): 逐行+分句正则, 不做完整语义分析——谓词前窗未覆盖的否定修辞
仍会命中 (改写措辞即可); staged 档对跨行 HTML 注释无块状态 (单行剥离), 全量档有。

退出码: 0 通过/纯报告 · 1 有效命中 · 2 配置或环境错误

扩面同步契约: 修改 scan_paths / 规则 / legacy 时必须**同 commit** 更新: 本文件常量
(EXPECTED_*, RULES_SHA256) + readme_claims_rules.yaml + lefthook.yml readme-claims-lint
的 glob + .github/workflows/readme-claims.yml 的 paths + 单测契约用例
(test_check_readme_claims.py 有跨文件同步断言)。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

HARD_FORBIDDEN = "hard-forbidden"
EVIDENCE_ESCAPABLE = "evidence-escapable"

#: 白名单契约 — 只有这些文件会被扫; 与 lefthook glob / workflow paths 同步维护
EXPECTED_SCAN_PATHS = ("README.md",)

#: L633 十一条契约 (id, severity, L633 原文) — yaml 必须逐条逐序完全一致
EXPECTED_RULES = (
    ("C1-production-ready", EVIDENCE_ESCAPABLE, "production-ready"),
    ("C2-any-vault-one-click", EVIDENCE_ESCAPABLE, "任意 vault 一键可用"),
    ("C3-multi-vault-safe", EVIDENCE_ESCAPABLE, "完整 multi-vault safe"),
    ("C4-graphiti-full-rebuild", EVIDENCE_ESCAPABLE, "Graphiti 永久且全量可重建"),
    ("C5-multisource-rag-default", EVIDENCE_ESCAPABLE, "full multi-source RAG 是默认主链"),
    ("C6-hit-at-k-as-recall", HARD_FORBIDDEN, "把 hit@k 写成 recall"),
    ("C7-fsrs-ui-consistent", EVIDENCE_ESCAPABLE, "FSRS/UI 已完全一致"),
    ("C8-canvas-excalidraw-lossless", EVIDENCE_ESCAPABLE, "Canvas↔Excalidraw 无损双向"),
    ("C9-agent-collab", EVIDENCE_ESCAPABLE, "14 个 Agent 协同"),
    ("C10-mobile-ready", EVIDENCE_ESCAPABLE, "移动端可用"),
    ("C11-skipped-as-success", HARD_FORBIDDEN, "skipped/degraded 等同成功"),
)

#: 规则文件全文 SHA-256 指纹 — readme_claims_rules.yaml 的任何字节变化都必须同 commit
#: 更新此常量 (指纹比对先于 yaml 解析)。刷新:
#:   python3 backend/scripts/check_readme_claims.py --print-rules-sha
RULES_SHA256 = "4825e71a58e2bc8ce7167815bb58085278a8f422065e21a22fbcc4f48881aded"

#: 证据文件目录契约 — 逃逸链接必须位于其下; 该目录已纳入 workflow paths (生命周期闭合)
EVIDENCE_DIR = "docs/evidence/"

#: 逃逸标记契约 (钉死在脚本, 不从 yaml 读): [C<n>:E3|E3+|E4|E5](路径), 反斜杠转义不算
ESCAPE_RE = re.compile(r"(?<!\\)\[C(\d{1,2}):(E3\+?|E4|E5)\]\(([^)\s]+)\)")

#: 行内隐藏文本 (HTML 注释 / code span / <code> 块)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->")
_CODE_SPAN_RE = re.compile(r"`{1,3}[^`]+`{1,3}|<code>.*?</code>", re.IGNORECASE)

#: 分句边界: 中文句号/分号, 以及后随空白或行尾的英文句号 (不切 0.92 这类小数点)
_CLAUSE_SPLIT_RE = re.compile(r"[;；。]|\.(?=\s|$)")

#: 否定守卫: 仅这些规则做「谓词否定尾绑定」检测 — 否定词必须紧邻谓词
#: (中间只允许 be/being/get/to/被/再/会/能/应/得 类助词), 无关谓词的 not 不解除阳性
#: (Codex 四轮 B1: "do not fail but indicate success" 的 not 修饰 fail, indicate 照拦)
NEGATION_GUARD_RULES = frozenset({"C11-skipped-as-success"})
_NEG_TAIL_RE = re.compile(
    r"(?:(?<![a-z0-9_])(?:not|never|cannot|can't|must\s+not|does\s+not|doesn't|don't|isn't|aren't|won't|wasn't|weren't|no\s+longer)(?![a-z0-9_])"
    r"|不|并非|绝不|决不|≠)"
    r"\s*(?:be|being|get|getting|to|被|再|会|能|应|得)?\s*$",
    re.IGNORECASE,
)
#: 谓词前窗宽度 (字符)
_NEG_WINDOW = 16

#: legacy 行号锚容差 — 0 = 精确匹配 (README 改动须经用户批准, 漂移时走契约重钉)
LEGACY_LINE_TOLERANCE = 0

#: legacy 上下文指纹窗口: 目标行前后各 2 行 (共 5 行)
_CONTEXT_RADIUS = 2

#: git 空 blob 的 SHA-1 — 不接受为证据
_EMPTY_BLOB_SHA = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


class ClaimsConfigError(Exception):
    """配置/环境错误 — 统一走退出码 2 (与 0=通过 / 1=命中 语义分离)."""


@dataclass(frozen=True)
class Rule:
    rule_id: str
    l633: str
    severity: str
    patterns: tuple[re.Pattern[str], ...]


@dataclass(frozen=True)
class LegacyEntry:
    file: str
    line: str
    registered_line: int
    context_sha256: str
    max_occurrences: int
    reason: str


@dataclass(frozen=True)
class RulesConfig:
    scan_paths: tuple[str, ...]
    rules: tuple[Rule, ...]
    legacy: tuple[LegacyEntry, ...]


@dataclass(frozen=True)
class Hit:
    file: str
    line_no: int
    line: str
    rule_id: str
    l633: str
    severity: str
    escaped: bool
    legacy: bool

    @property
    def effective(self) -> bool:
        return not self.escaped and not self.legacy


def context_digest(all_lines: list[str], line_no: int) -> str:
    """5 行窗口 (目标行 ±2, 越界截断) 的 SHA-256 — legacy 搬移指纹."""
    start = max(0, line_no - 1 - _CONTEXT_RADIUS)
    end = min(len(all_lines), line_no + _CONTEXT_RADIUS)
    window = "\n".join(line.rstrip("\n") for line in all_lines[start:end])
    return hashlib.sha256(window.encode("utf-8")).hexdigest()


def strip_html_comments(all_lines: list[str]) -> list[str]:
    """整文件级剥离 HTML 注释 (含跨行注释块), 返回逐行可见文本 (行数不变)."""
    out: list[str] = []
    in_block = False
    for raw in all_lines:
        line = raw
        result = ""
        while line:
            if in_block:
                close = line.find("-->")
                if close == -1:
                    line = ""
                else:
                    line = line[close + 3 :]
                    in_block = False
            else:
                open_ = line.find("<!--")
                if open_ == -1:
                    result += line
                    line = ""
                else:
                    result += line[:open_]
                    rest = line[open_:]
                    close = rest.find("-->", 4)
                    if close == -1:
                        in_block = True
                        line = ""
                    else:
                        line = rest[close + 3 :]
        out.append(result)
    return out


def _rule_number(rule_id: str) -> str:
    match = re.match(r"C(\d{1,2})-", rule_id)
    if not match:
        raise ClaimsConfigError(f"规则 id 不符合 C<n>-<slug> 形态: {rule_id}")
    return match.group(1)


def _compile(rule_id: str, patterns: object) -> tuple[re.Pattern[str], ...]:
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ClaimsConfigError(f"规则 {rule_id} patterns 必须是字符串列表")
    try:
        return tuple(re.compile(p, re.IGNORECASE) for p in patterns)
    except re.error as exc:
        raise ClaimsConfigError(f"规则 {rule_id} 正则非法: {exc}") from exc


_ALLOWED_RULE_KEYS = {"id", "l633", "severity", "patterns"}
_ALLOWED_LEGACY_KEYS = {
    "file",
    "line",
    "registered_line",
    "context_sha256",
    "max_occurrences",
    "reason",
}


def _strict_positive_int(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ClaimsConfigError(f"{what} 必须是正整数: {value!r}")
    return value


def load_rules(path: Path) -> RulesConfig:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - 环境缺 PyYAML
        raise ClaimsConfigError(f"PyYAML 不可用: {exc}") from exc
    if not path.is_file():
        raise ClaimsConfigError(f"规则文件不存在: {path}")
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise ClaimsConfigError(f"规则文件读取失败: {exc}") from exc
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != RULES_SHA256:
        raise ClaimsConfigError(
            "规则文件指纹与脚本 RULES_SHA256 不一致 — yaml 单边改动被拒绝。"
            f"\n  实际: {digest}\n  契约: {RULES_SHA256}"
            "\n  如系有意修改: 同 commit 更新脚本常量并过审 (扩面同步契约见 docstring)。"
        )
    try:
        raw = yaml.safe_load(raw_bytes.decode("utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError, RecursionError) as exc:
        raise ClaimsConfigError(f"规则文件解析失败: {exc}") from exc
    if not isinstance(raw, dict):
        raise ClaimsConfigError("规则文件顶层必须是 mapping")
    sv = raw.get("schema_version")
    if type(sv) is not int or sv != 2:
        raise ClaimsConfigError(f"schema_version 必须是整数 2: {sv!r}")
    unknown_top = {str(k) for k in raw} - {"schema_version", "scan_paths", "legacy_allowlist", "rules"}
    if unknown_top:
        raise ClaimsConfigError(f"规则文件含未知顶层字段: {sorted(unknown_top)}")

    scan_paths = raw.get("scan_paths")
    if not isinstance(scan_paths, list) or not all(isinstance(s, str) for s in scan_paths):
        raise ClaimsConfigError("scan_paths 必须是字符串列表")
    if tuple(scan_paths) != EXPECTED_SCAN_PATHS:
        raise ClaimsConfigError(f"scan_paths 与脚本契约不一致: yaml={scan_paths!r} 契约={list(EXPECTED_SCAN_PATHS)!r}")
    for rel in scan_paths:
        if Path(rel).is_absolute() or ".." in Path(rel).parts or any(ch in rel for ch in "*?["):
            raise ClaimsConfigError(f"scan_paths 含绝对路径/越级/通配: {rel!r}")

    raw_rules = raw.get("rules")
    if not isinstance(raw_rules, list):
        raise ClaimsConfigError("rules 必须是列表")
    rules: list[Rule] = []
    for entry in raw_rules:
        if not isinstance(entry, dict):
            raise ClaimsConfigError(f"规则条目必须是 mapping: {entry!r}")
        unknown = {str(k) for k in entry} - _ALLOWED_RULE_KEYS
        if unknown:
            raise ClaimsConfigError(f"规则 {entry.get('id')!r} 含未知字段 {sorted(unknown)} — 已废除的机制不得残留")
        rule_id = str(entry.get("id", ""))
        severity = str(entry.get("severity", ""))
        if severity not in (HARD_FORBIDDEN, EVIDENCE_ESCAPABLE):
            raise ClaimsConfigError(f"规则 {rule_id!r} severity 非法: {severity!r}")
        rules.append(
            Rule(
                rule_id=rule_id,
                l633=str(entry.get("l633", "")),
                severity=severity,
                patterns=_compile(rule_id, entry.get("patterns")),
            )
        )
    actual = tuple((r.rule_id, r.severity, r.l633) for r in rules)
    if actual != EXPECTED_RULES:
        raise ClaimsConfigError(
            "规则集与脚本契约 (EXPECTED_RULES) 不一致 — 禁止增删/换序/改 severity/改 L633 标注。"
            f"\n  yaml : {[a[0] + '/' + a[1] for a in actual]}"
            f"\n  契约 : {[e[0] + '/' + e[1] for e in EXPECTED_RULES]}"
        )
    for rule in rules:
        _rule_number(rule.rule_id)
        if not rule.patterns:
            raise ClaimsConfigError(f"规则 {rule.rule_id} patterns 为空")

    raw_legacy = raw.get("legacy_allowlist", [])
    if not isinstance(raw_legacy, list):
        raise ClaimsConfigError("legacy_allowlist 必须是列表")
    legacy: list[LegacyEntry] = []
    for entry in raw_legacy:
        if not isinstance(entry, dict):
            raise ClaimsConfigError(f"legacy 条目必须是 mapping: {entry!r}")
        unknown = {str(k) for k in entry} - _ALLOWED_LEGACY_KEYS
        if unknown:
            raise ClaimsConfigError(f"legacy 条目含未知字段 {sorted(unknown)}")
        for key in ("file", "line"):
            if key in entry and not isinstance(entry[key], str):
                raise ClaimsConfigError(f"legacy {key} 必须是字符串: {entry[key]!r}")
        if "reason" in entry and not isinstance(entry["reason"], str):
            raise ClaimsConfigError(f"legacy reason 必须是字符串: {entry['reason']!r}")
        try:
            legacy.append(
                LegacyEntry(
                    file=str(entry["file"]),
                    line=str(entry["line"]),
                    registered_line=_strict_positive_int(entry["registered_line"], "registered_line"),
                    context_sha256=str(entry["context_sha256"]),
                    max_occurrences=_strict_positive_int(entry["max_occurrences"], "max_occurrences"),
                    reason=str(entry.get("reason", "")),
                )
            )
        except KeyError as exc:
            raise ClaimsConfigError(f"legacy 条目缺字段 {exc}: {entry!r}") from exc
        if not re.fullmatch(r"[0-9a-f]{64}", legacy[-1].context_sha256):
            raise ClaimsConfigError(f"legacy context_sha256 必须是 64 位 hex: {legacy[-1].context_sha256!r}")
        if legacy[-1].file not in scan_paths:
            raise ClaimsConfigError(f"legacy 条目 file 不在 scan_paths 内: {legacy[-1].file!r}")
    return RulesConfig(tuple(scan_paths), tuple(rules), tuple(legacy))


def _escape_surface(visible_text: str) -> str:
    """逃逸标记的匹配面: 可见文本再剥离 code span (藏在反引号里的标记不算)."""
    return _CODE_SPAN_RE.sub("", visible_text)


def _match_surface(visible_text: str) -> str:
    """规则匹配面: 剥离行内 Markdown 强调符 (` * __ ~~) — 强调排版切不断声明
    (Codex 七轮 B2: `Hit@k` is equivalent / **==** 等 token 内分隔旁路)。
    保留单个下划线 (recall_at_5 类标识符是 C6 的匹配对象)。"""
    return visible_text.replace("`", "").replace("**", "").replace("~~", "").replace("*", "").replace("__", "")


def _git_index_blobs(root: Path) -> dict[str, str]:
    """git index 中 stage-0 普通文件 → blob sha (拒绝 intent-to-add / 空 blob / 非 0 stage)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "-z"],
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise ClaimsConfigError(f"git ls-files --stage 失败: {exc}") from exc
    if proc.returncode != 0:
        raise ClaimsConfigError(f"git ls-files --stage 失败: {proc.stderr.strip()}")
    blobs: dict[str, str] = {}
    for record in proc.stdout.split("\0"):
        if not record:
            continue
        meta, _, rel = record.partition("\t")
        parts = meta.split()
        if len(parts) != 3:
            continue
        mode, sha, stage = parts
        if stage != "0" or mode not in ("100644", "100755"):
            continue
        if set(sha) == {"0"} or sha == _EMPTY_BLOB_SHA:
            continue  # intent-to-add / 空 blob 不算证据
        blobs[rel] = sha
    return blobs


def _line_escapes(visible_text: str, rule: Rule, rel_file: str, root: Path, index_blobs: dict[str, str]) -> bool:
    """evidence-escapable 命中行是否被同行合法证据标注放行 (条件见 docstring)."""
    if rule.severity == HARD_FORBIDDEN:
        return False
    want = _rule_number(rule.rule_id)
    root_resolved = root.resolve()
    for match in ESCAPE_RE.finditer(_escape_surface(visible_text)):
        if match.group(1) != want:
            continue
        link = match.group(3)
        if Path(link).is_absolute() or link == rel_file:
            continue
        if not link.startswith(EVIDENCE_DIR):
            continue  # 证据必须位于受控目录 (已纳入 workflow paths)
        if link not in index_blobs:
            continue  # index 中无真实 blob (未 add / intent-to-add / 空文件) 不算证据
        target = root / link
        try:
            target.resolve().relative_to(root_resolved)
        except ValueError:
            continue
        if target.is_symlink() or not target.is_file():
            continue
        try:
            if target.stat().st_size == 0:
                continue
        except OSError:
            continue
        return True
    return False


def _rule_fires(rule: Rule, visible_text: str) -> bool:
    """规则是否成立: 逐分句匹配 (conjunct 不得跨分句); 否定守卫看谓词前窗."""
    guard = rule.rule_id in NEGATION_GUARD_RULES
    for clause in _CLAUSE_SPLIT_RE.split(visible_text):
        if not clause:
            continue
        for pattern in rule.patterns:
            if not guard or "v" not in pattern.groupindex:
                if pattern.search(clause):
                    return True
                continue
            # 否定守卫: 被否定的谓词打掩码后重扫, 逐个评估同分句的每个谓词候选
            # (防惰性/贪婪匹配吞掉相邻谓词 — Codex 四轮 B1)
            work = clause
            while True:
                match = pattern.search(work)
                if not match:
                    break
                verb_start, verb_end = match.start("v"), match.end("v")
                if verb_start == -1:
                    return True
                window = work[max(0, verb_start - _NEG_WINDOW) : verb_start]
                if _NEG_TAIL_RE.search(window):
                    work = work[:verb_start] + "\x00" * (verb_end - verb_start) + work[verb_end:]
                    continue  # 否定词紧邻本谓词 → 掩码后找下一个谓词
                return True
    return False


def scan_lines(
    rel_file: str,
    numbered_lines: list[tuple[int, str]],
    cfg: RulesConfig,
    root: Path,
    *,
    apply_legacy: bool = True,
    all_lines: list[str] | None = None,
    visible_lines: dict[int, str] | None = None,
) -> list[Hit]:
    """对 (行号, 行文本) 列表跑全部规则。

    staged-diff 档以 apply_legacy=False 调用 (无跨行注释状态, 单行剥离);
    legacy 判定需要 all_lines (整文件原始行) 计算上下文指纹与精确文本匹配。"""
    legacy_quota: dict[str, int] = {}
    legacy_entries: dict[str, LegacyEntry] = {}
    if apply_legacy:
        if all_lines is None:
            raise ClaimsConfigError("apply_legacy=True 需要 all_lines 计算上下文指纹")
        for entry in cfg.legacy:
            if entry.file == rel_file:
                legacy_quota[entry.line] = entry.max_occurrences
                legacy_entries[entry.line] = entry
    index_blobs: dict[str, str] | None = None
    hits: list[Hit] = []
    for line_no, raw_line in numbered_lines:
        raw_text = raw_line.rstrip("\n")
        if visible_lines is not None and line_no in visible_lines:
            visible = visible_lines[line_no]
        else:
            visible = _HTML_COMMENT_RE.sub("", raw_text)
        matched = [r for r in cfg.rules if _rule_fires(r, _match_surface(visible))]
        if not matched:
            continue
        line_is_legacy = False
        if raw_text in legacy_entries and all_lines is not None:
            entry = legacy_entries[raw_text]
            in_anchor = abs(line_no - entry.registered_line) <= LEGACY_LINE_TOLERANCE
            context_ok = context_digest(all_lines, line_no) == entry.context_sha256
            if legacy_quota[raw_text] > 0 and in_anchor and context_ok:
                legacy_quota[raw_text] -= 1
                line_is_legacy = True
        needs_escape = any(r.severity == EVIDENCE_ESCAPABLE for r in matched) and ESCAPE_RE.search(
            _escape_surface(visible)
        )
        if needs_escape and index_blobs is None:
            index_blobs = _git_index_blobs(root)
        for rule in matched:
            hard = rule.severity == HARD_FORBIDDEN
            hits.append(
                Hit(
                    file=rel_file,
                    line_no=line_no,
                    line=raw_text,
                    rule_id=rule.rule_id,
                    l633=rule.l633,
                    severity=rule.severity,
                    escaped=bool(index_blobs is not None and _line_escapes(visible, rule, rel_file, root, index_blobs)),
                    legacy=(not hard) and line_is_legacy,
                )
            )
    return hits


def _validate_scan_targets(root: Path, cfg: RulesConfig) -> None:
    root_resolved = root.resolve()
    for rel in cfg.scan_paths:
        target = root / rel
        if target.is_symlink():
            raise ClaimsConfigError(f"scan_paths 目标是 symlink, 拒绝: {target}")
        if not target.is_file():
            raise ClaimsConfigError(f"scan_paths 文件不存在: {target} — 检查 --root 是否指错")
        try:
            target.resolve().relative_to(root_resolved)
        except ValueError as exc:
            raise ClaimsConfigError(f"scan_paths 目标越出仓库根: {target}") from exc


def scan_scan_paths(root: Path, cfg: RulesConfig) -> list[Hit]:
    """全量档: 扫 scan_paths 白名单 (白名单外永不扫)。目标缺失/symlink = 配置错误."""
    _validate_scan_targets(root, cfg)
    hits: list[Hit] = []
    for rel in cfg.scan_paths:
        target = root / rel
        try:
            content = target.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ClaimsConfigError(f"读取 {target} 失败: {exc}") from exc
        all_lines = content.split("\n")  # 只按 \n 分行, 防 U+2028 类断行错位
        visible = strip_html_comments(all_lines)
        visible_map = dict(enumerate(visible, start=1))
        numbered = list(enumerate(all_lines, start=1))
        hits.extend(scan_lines(rel, numbered, cfg, root, all_lines=all_lines, visible_lines=visible_map))
    return hits


_HUNK_RE = re.compile(rb"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def staged_added_lines(root: Path, cfg: RulesConfig) -> dict[str, list[tuple[int, str]]]:
    """解析 git staged diff, 只取 scan_paths 文件的**新增行** (语义见 docstring)."""
    git_base = ["git", "-C", str(root), "-c", "color.ui=false", "-c", "core.quotepath=false"]
    try:
        toplevel = subprocess.run([*git_base, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if toplevel.returncode != 0:
            raise ClaimsConfigError(f"--root 不是 git 仓库: {toplevel.stderr.strip()}")
        if Path(toplevel.stdout.strip()).resolve() != root.resolve():
            raise ClaimsConfigError(f"--root 必须是仓库根: root={root} toplevel={toplevel.stdout.strip()}")
        status = subprocess.run(
            [*git_base, "diff", "--cached", "--name-status", "--no-renames", "-z", "--", *cfg.scan_paths],
            capture_output=True,
            text=True,
        )
        if status.returncode != 0:
            raise ClaimsConfigError(f"git diff --name-status 失败: {status.stderr.strip()}")
        tokens = [t for t in status.stdout.split("\0") if t]
        changed_files: set[str] = set()
        for code, path in zip(tokens[::2], tokens[1::2]):
            kind = code[:1]
            if kind in ("D", "T", "U"):
                raise ClaimsConfigError(f"扫描目标存在 {kind} 类 staged 变更 (删除/类型变更/未合并), 拒绝裁决: {path}")
            if kind in ("A", "C", "M", "R"):
                changed_files.add(path)
        proc = subprocess.run(
            [
                *git_base,
                "diff",
                "--cached",
                "--text",
                "--unified=0",
                "--inter-hunk-context=0",
                "--no-color",
                "--no-ext-diff",
                "--no-textconv",
                "--no-renames",
                "--src-prefix=a/",
                "--dst-prefix=b/",
                "--diff-filter=ACMR",
                "--",
                *cfg.scan_paths,
            ],
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise ClaimsConfigError(f"git 调用失败: {exc}") from exc
    if proc.returncode != 0:
        raise ClaimsConfigError(f"git diff --cached 失败: {proc.stderr.decode(errors='replace').strip()}")
    allowed = set(cfg.scan_paths)
    by_file: dict[str, list[tuple[int, str]]] = {}
    parsed_files: set[str] = set()
    current: str | None = None
    in_hunk = False
    new_line_no = 0
    for raw in proc.stdout.split(b"\n"):
        if raw.startswith(b"diff --git"):
            current, in_hunk = None, False
        elif not in_hunk and raw.startswith(b"+++ b/"):
            candidate = raw[len(b"+++ b/") :].decode("utf-8", errors="replace")
            current = candidate if candidate in allowed else None
        elif raw.startswith(b"@@"):
            match = _HUNK_RE.match(raw)
            if not match:
                raise ClaimsConfigError(f"无法解析 hunk 头: {raw!r}")
            in_hunk = True
            new_line_no = int(match.group(1))
            if current is not None:
                parsed_files.add(current)
        elif in_hunk:
            if raw.startswith(b"+"):
                if current is not None:
                    by_file.setdefault(current, []).append((new_line_no, raw[1:].decode("utf-8", errors="replace")))
                new_line_no += 1
            elif raw.startswith(b"-") or raw.startswith(b"\\"):
                pass  # 删除行 / "\ No newline" 不推进新文件行号
            else:
                new_line_no += 1  # 理论上无上下文行, 防御性推进
    unparsed = changed_files - parsed_files
    if unparsed:
        raise ClaimsConfigError(f"以下 staged 扫描目标无法解析出文本 hunk (二进制伪装/异常 diff?): {sorted(unparsed)}")
    return by_file


def _print_hits(hits: list[Hit], *, only_effective: bool) -> None:
    for hit in hits:
        if only_effective and not hit.effective:
            continue
        flags = "".join([" [escaped]" if hit.escaped else "", " [legacy]" if hit.legacy else ""])
        color = YELLOW if (hit.escaped or hit.legacy) else RED
        print(
            f"{color}{hit.file}:{hit.line_no}{RESET} [{hit.rule_id}/{hit.severity}]{flags}"
            f" 禁夸大(L633): {hit.l633}\n    {hit.line[:160]}"
        )


def _summary(hits: list[Hit]) -> str:
    effective = sum(1 for h in hits if h.effective)
    escaped = sum(1 for h in hits if h.escaped)
    legacy = sum(1 for h in hits if h.legacy)
    return f"TOTAL={len(hits)} effective={effective} escaped={escaped} legacy={legacy}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--report", action="store_true", help="全量报告, 恒退出 0")
    mode.add_argument("--enforce", action="store_true", help="全量门禁, 有效命中退出 1")
    mode.add_argument("--staged-diff", action="store_true", help="只扫 staged 新增行, 有效命中退出 1")
    mode.add_argument("--print-rules-sha", action="store_true", help="打印规则文件当前 SHA-256 (维护用)")
    parser.add_argument("--rules", type=Path, default=Path(__file__).parent / "readme_claims_rules.yaml")
    parser.add_argument("--root", type=Path, default=None, help="仓库根 (默认 git toplevel; 无 git 时必须显式指定)")
    args = parser.parse_args(argv)

    if args.print_rules_sha:
        try:
            print(hashlib.sha256(args.rules.read_bytes()).hexdigest())
        except OSError as exc:
            print(f"{RED}[readme-claims] 读取规则文件失败: {exc}{RESET}", file=sys.stderr)
            return 2
        return 0

    try:
        cfg = load_rules(args.rules)
        root = args.root
        if root is None:
            try:
                proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            except (OSError, subprocess.SubprocessError) as exc:
                raise ClaimsConfigError(f"无 --root 且 git 不可用: {exc}") from exc
            if proc.returncode != 0:
                raise ClaimsConfigError("无 --root 且当前目录不是 git 仓库 — 请显式传 --root")
            root = Path(proc.stdout.strip())
        if not root.is_dir():
            raise ClaimsConfigError(f"--root 不是有效目录: {root}")

        if args.staged_diff:
            _validate_scan_targets(root, cfg)
            by_file = staged_added_lines(root, cfg)
            hits = [
                h
                for rel, lines in sorted(by_file.items())
                for h in scan_lines(rel, lines, cfg, root, apply_legacy=False)
            ]
        else:
            hits = scan_scan_paths(root, cfg)
    except ClaimsConfigError as exc:
        print(f"{RED}[readme-claims] 配置/环境错误: {exc}{RESET}", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError, ValueError, subprocess.SubprocessError, RecursionError) as exc:
        print(f"{RED}[readme-claims] 环境异常: {exc}{RESET}", file=sys.stderr)
        return 2

    mode_name = "report" if args.report else ("enforce" if args.enforce else "staged-diff")
    _print_hits(hits, only_effective=not args.report)
    print(f"[readme-claims] mode={mode_name} {_summary(hits)}")

    if args.report:
        return 0
    effective = [h for h in hits if h.effective]
    if effective:
        print(
            f"{RED}[readme-claims] ❌ {len(effective)} 条禁夸大声明 (计划书 §12.7 L633)。"
            f"处置: 改写为诚实措辞, 或对 evidence-escapable 类在同行附"
            f" [Cx:E3](docs/evidence/… 已入库的非空证据文件); hard-forbidden 名实类必须改写。{RESET}"
        )
        return 1
    print(f"{GREEN}[readme-claims] OK{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
