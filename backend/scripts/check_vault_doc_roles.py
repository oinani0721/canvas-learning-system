#!/usr/bin/env python3
"""CARD-G8-1 — vault 文档角色台账机械裁判 (report / enforce 两档)。

真相源: 同目录 `vault_doc_roles.yaml` (锚点见该文件头部)。

本脚本对 **live vault 只读扫描**, 报告**十一类** finding (G1-G11):

  G1 unregistered_dir             live 目录未被任何 vault_entries.dir_glob 命中
  G2 unregistered_root_file       vault 根级文件未被任何 root_files.file_glob 命中
  G3 unregistered_frontmatter_type  md 的 frontmatter `type:` 不在其归属条目的
                                  frontmatter_type 白名单内 (无 type 记作 `(none)`)
  G4 doc_type_whitelist_violation frontmatter type 出现在 rag_index: true 的条目
                                  覆盖面下, 却不在 doc_type_whitelist 内
                                  —— 写侧 frontmatter 直通无校验, 这是野值入库面
  G5 admission_mismatch           台账声明的 rag_index / memory_write 与**真实函数**
                                  对 live 路径的求值不符。口径: 两列描述的是该类
                                  **Markdown 文档**的准入; 非 md 文件由两面共有的
                                  not_markdown 规则统一拒 (与 per-type 策略无关),
                                  故对非 md 改判 surface 级不变量 —— 若非 md 被放行
                                  照样判红, 不是豁免
  G6 undeclared_divergence        真实函数给出分歧, 但该分歧不属任何已登记的
                                  by_design_divergences 模式 (按**类**核对, 不按实例)
  G7 stale_divergence             条目声明了分歧, 但命中它的 live 文件实测均无分歧
  G10 scan_blind_spot             枚举/读取失败的对象: 不可读子树 (权限)、不可读文件、
                                  dangling/self 指向的 symlink (既非 dir 也非 file, 两轮
                                  枚举都过滤掉了)、超长路径。这些此前一律静默 —— "0 finding"
                                  又一次变成"没看见"
  G11 vault_escape                文件解析到 **vault 之外**。除了判红, 本脚本**拒绝读取**
                                  它的正文 —— 一个只读的 vault 审计器不该跨出 vault 边界
                                  去读别人的文件 (round-4 实证: `检验白板/external.md`
                                  指向 vault 外, 其 frontmatter 曾被照读)
  G9 unregistered_root_md         根级 md 落到兜底行 `root-loose-md`, 但不在该行的
                                  `known_instances` 里 —— 兜底行只能断言**准入行为**
                                  (它如实镜像"未命中文件名黑名单即放行"), 断不了
                                  owner/role/retention。每个新根级 md 必须逐个登记,
                                  否则会被静默泛化成"用户 wiki / 不可重建"
  G8 unscanned_symlinked_dir      目录是符号链接 —— `Path.rglob` **不递归**进去 (实测),
                                  其后代整棵子树不在扫描面内。不跟进 (会成环), 但必须
                                  显式报出: 否则 "0 finding" 是"没看见"而不是"没问题"

⛔ 反软化契约 (本卡的存在理由, 与 yaml 头部一致):
  - 双准入面分歧是 **by-design 登记对象**, 不是 bug。登记的是**类** (pattern),
    新增同类文件不判红; 出现**新类**分歧才判 G6。
  - `known_gaps` 只能豁免 G1/G2/G3 三类"未登记类型"。
    G4/G5/G6/G7 是"台账与代码不符", **永不可被豁免** —— 见 GAP_EXEMPTIBLE。
  - known_gaps.literal 必须是**字面量** (禁通配符), 且必须带 reason + owner_card。
  - dir_glob / file_glob 禁止裸通配 ("*" / "**" / "**/*" / "/**")。

⛔ 零写入铁律 —— 作用域 = **live vault**, 如实收窄 (Codex round-1 HIGH):
   - 对 vault 只有 `os.walk` / `stat` / 只读 `open`, 没有任何写路径
     (不存在 --fix / --write 参数)。`VaultIndexOrchestrator.__init__` 已核源码:
     只做属性赋值, `_pending_file` 仅构造 Path 对象不落盘, LanceDB 连接在
     `_get_client()` 里而本脚本从不调用它。
     验收证据 = 跑前跑后 live vault 全量 shasum 逐字节相同。
   - ⚠️ **但 import 链会在系统临时目录写缓存**: `--probe` 档 import
     `app.services.*` → `app/services/__init__.py` → `lancedb_client` 的
     `jieba.initialize()`, 实测产生 `<tmp>/jieba.cache` 与 `torchinductor_<user>/`。
     这些**不在 vault 内**, 但"零写入"若不加限定就是过宽的声明。
   - 完全只读的环境 (无可写临时目录) 下该 import 会失败 —— 本脚本捕获并以
     退出码 2 + 明确提示收场, 且提供 `--no-probe` 档: 跳过真实准入函数求值,
     只做 schema / 登记面检查 (G1-G4 与 G8-G11 照跑, 只放弃 G5/G6/G7), 零 import 副作用。

配置面钉死 (仿 backend/scripts/check_readme_claims.py 先例):
  - `ROLES_SHA256` 钉死 yaml 全文 SHA-256, **指纹比对先于 yaml 解析** ——
    伪绿无法由 yaml 单边达成; 改一行就必须同 commit 改本文件常量 (双文件, 审查可见)。
    刷新: python3 backend/scripts/check_vault_doc_roles.py --print-roles-sha
  - `EXPECTED_SECTIONS` 钉死 yaml 顶层节名与顺序。
  - `EXPECTED_DOC_TYPES` 钉死 doc_type 六取值的 (value, role, census_verdict_tag) 序列。
  - `EXPECTED_LAST_ROOT_FILE_ID` 钉死 root_files 兜底行必须在最后
    (它是 `*.md` 宽匹配, 排前面会抢走所有黑名单行的命中)。

匹配语义:
  - glob: `**/` = 任意层前缀, 结尾 `/**` = 任意层后缀, `*` = 段内任意, `?` = 段内单字符。
  - **顺序敏感, 先匹配先命中** (防火墙式 ruleset)。
  - 文件归属解析顺序: root_files (按 yaml 序, scope 感知) → derived_artifacts.file_glob
    → vault_entries.dir_glob (对文件所在目录求值)。

退出码: 0 通过 / 纯报告 · 1 有非豁免 finding · 2 配置或环境错误
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"

ROLES_YAML = Path(__file__).with_name("vault_doc_roles.yaml")

#: 规则文件全文 SHA-256 指纹 — 任何字节变化都必须同 commit 更新此常量。
#: 刷新: python3 backend/scripts/check_vault_doc_roles.py --print-roles-sha
ROLES_SHA256 = "2a68d4cd8091dd7def01d3539a68cb9fb1efd458be2f8882459791312cf46648"

#: yaml 顶层节名与顺序契约
EXPECTED_SECTIONS = (
    "schema_version",
    "card",
    "batch",
    "live_vault",
    "roles",
    "admission_surfaces",
    "vault_entries",
    "root_files",
    "derived_artifacts",
    "doc_type_whitelist",
    "frontmatter_types_outside_doc_type",
    "repo_docs",
    "known_gaps",
)

#: doc_type 六取值契约 — (value, role, census_verdict_tag), 与 yaml 逐条逐序一致。
#: 卡片 (c) 点名的六取值。第六个 `dashboard` 与 G4-16 census §4 第六行
#: ("空串/自由值") 是**不同的东西** —— yaml 的 census_verdict 里如实登记了该差异,
#: census 那一行另存为 doc_type_whitelist.value_domain_closed / unclosed_surface。
#: ⛔ roles 是**列表**不是单值 (对抗审查 HIGH): 一个 doc_type 取值可以横跨多个
#: 角色的条目 —— `note` 既出现在 wiki 的 `节点/`, 也出现在 raw 的 `raw/`、
#: 根级课程目录与 multimodal。写单值必然对其中一半撒谎。
#: 契约: roles 必须**恰好等于** registered_by 所指条目的角色集合 (脚本复算)。
EXPECTED_DOC_TYPES = (
    ("note", ("raw", "wiki"), "wired"),
    ("whiteboard", ("raw",), "wired"),
    ("exam_board", ("raw", "wiki"), "wired"),
    ("video_transcript", ("raw",), "wired"),
    ("concept", ("schema", "wiki"), "value_wired_weight_key_unreachable"),
    ("dashboard", ("derived",), "card_added__census_absent"),
)

#: root_files 兜底行 id — 必须是最后一行 (宽匹配 `*.md`)
EXPECTED_LAST_ROOT_FILE_ID = "root-loose-md"

#: 四值角色枚举 (卡片 (b) 钉死)
VALID_ROLES = ("raw", "wiki", "schema", "derived")

#: rag_retrieval 四值 (round-6 增 conditional)
#: `conditional` = 同一条目下**部分**文档被读侧排除 (round-6 HIGH: `节点/**` 里
#: 无 `type` 且含 `exam_question_id` 的考察文件会被写侧推断为 exam_board 从而被
#: exclude_doc_types 挡掉)。用 included 一刀切就是对信息隔离面撒谎。
#: 取该值时必须另填 rag_retrieval_note 说明"哪部分、为什么"。
VALID_RETRIEVAL = ("included", "excluded_by_doc_type", "not_indexed", "conditional")

#: ⛔ known_gaps 只能豁免这三类。G4/G5/G6/G7 = 台账与代码不符, 豁免它们
#: 等于把台账做软来凑绿, 因此永不可豁免。
GAP_EXEMPTIBLE = frozenset({"G1", "G2", "G3"})

#: 全部 finding code (供报告与测试穷举)
ALL_FINDING_CODES = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11")

#: derived_artifacts 的产物落点面。vault_file 走 file_glob 机械识别;
#: store / http_response 不落 vault 文件, 必须改用 identifier 显式登记身份面
#: (Codex round-1 HIGH: 空 match 且不可核对 = 该行等于没登记)。
VALID_SURFACES = ("vault_file", "store", "http_response")

#: root_files 的 any_level 行必须声明治理作用域 —— 它们按 basename 在**任意层级**
#: 命中, 会抢在容器行之前 (resolve_file_entry 的顺序), 于是
#: `.quarantine/UAT-x.md` 会拿到"可安全删除"而不是隔离区的"保留至人工处置"。
#: 该顺序对**准入两列**是正确的 (文件名黑名单确实盖过目录), 但对 owner/retention
#: 就是撒谎。故 any_level 行必须写 `governance_scope: root_only`, 明示
#: "本行只贡献准入两列; 深层实例的 owner/retention 以所在容器行为准"。
VALID_GOVERNANCE_SCOPES = ("root_only", "any_level")

#: by_design_divergences.scope 的合法取值 (拼错会静默按 any 处理)
VALID_DIVERGENCE_SCOPES = ("root", "any")

#: repo_docs 另节的必填字段 —— 字段集比 vault 侧轻 (无准入面 glob), 但同样受裁判
#: (Codex round-1 HIGH: repo_docs 原本完全绕过 _verify_contract)
REQUIRED_REPO_FIELDS = (
    "id",
    "role",
    "path_glob",
    "owner",
    "editable_by",
    "rag_index",
    "memory_write",
    "rag_retrieval",
    "provenance",
    "retention",
)

#: 每行必填字段 (卡片 (b))
REQUIRED_ENTRY_FIELDS = (
    "id",
    "role",
    "match",
    "owner",
    "editable_by",
    "rag_index",
    "memory_write",
    "rag_retrieval",
    "provenance",
    "retention",
)

#: catch-all 探针集 —— 一个 pattern 若把**全部**探针都吃下, 它就是 catch-all,
#: 会让 G1/G2 恒绿。用**语义判定**而非字面量黑名单: 字面量集拦不住 `?*` /
#: `**/?*` 这类等价写法 (对抗审查实证)。下方 BARE_WILDCARDS 仅保留作文档与快路径。
CATCH_ALL_PROBES = (
    "a",
    "a/b",
    "a/b/c.md",
    ".hidden",
    ".hidden/x",
    "节点/x.md",
    "raw/CS188/videos/z.md",
    "Dashboard.md",
)

#: 单段探针 —— 吃下全部 = 顶层 catch-all (吞掉所有一级目录)
SINGLE_SEGMENT_PROBES = ("a", ".hidden", "Dashboard.md", "节点")

#: 已知的裸通配写法 (快路径 + 文档; 语义判定见 is_catch_all / is_union_catch_all)
BARE_WILDCARDS = frozenset({"*", "**", "**/*", "/**", "*/**", "**/**"})

#: 必须是**非空字符串**的文本类字段 —— 其余为 bool / mapping / list, 各有专门校验。
#: (round-3 实证: 原来用 `str(v).strip()` 验 truthiness, `None` / `[]` / `{}`
#:  字符串化后都非空, 全部被放行。)
_TEXT_FIELDS = frozenset({"id", "role", "owner", "editable_by", "rag_retrieval", "provenance", "retention"})


def names_something(pat: str) -> bool:
    """glob 是否至少**命名了一样东西** —— 含至少一个字母/数字/CJK 字面量字符。

    ⛔ 这是对"跨行并集 catch-all"的正面回答 (round-4 HIGH)。逐行并集判定拦不住
    把 `["**/.*", "**/[!.]*"]` 拆成两条 entry —— 而"检查全体行的并集"也不成立:
    一份**完整**台账的 glob 并集本来就该覆盖一切, 那正是覆盖率的目标。
    真正能区分"如实穷举"与"两行糊住全场"的, 是**每条 glob 有没有指名道姓**:
    只由通配符与字符类拼成的模式 (`.*` / `[!.]*` / `[!x]*`) 不标识任何一类文档,
    它只是在圈地。故要求每条 glob 至少含一个字面量的字母/数字/CJK 字符。
    (`.` `_` `-` 这类纯标点不算 —— `[!.]*` 正是靠它们伪装成"具体"的。)
    """
    stripped = re.sub(r"\[[^\]]*\]", "", pat)  # 去掉字符类整体
    return any(ch.isalnum() for ch in stripped)


def is_union_catch_all(pats: list[str]) -> bool:
    """一组 glob 的**并集**是否吃下全部探针。

    ⛔ 逐条判定拦不住并集 (round-3 实证): `["**/.*", "**/[!.]*"]` 每条都不是
    catch-all, 合起来却覆盖一切 —— G1/G2 照样恒绿。故必须对整行的 glob 列表求 OR。
    """
    if not pats:
        return False
    try:
        rxs = [glob_to_regex(p) for p in pats]
    except re.error:
        return False
    if all(any(rx.match(probe) for rx in rxs) for probe in CATCH_ALL_PROBES):
        return True
    return all(any(rx.match(probe) for rx in rxs) for probe in SINGLE_SEGMENT_PROBES)


def is_catch_all(pat: str) -> bool:
    """pattern 是否为 catch-all —— 三条判据取或。

    1. 命中已知裸通配字面量 (快路径 / 文档);
    2. 吃下**全部**探针 = 全局 catch-all (`**` / `**/*` / `**/?*` / `*/**`);
    3. 吃下全部**单段**探针 = 顶层 catch-all (`*` / `?*`) —— 单段模式吃不下
       `a/b`, 但作为 dir_glob 会吞掉全部一级目录, G1 照样恒绿。
    """
    if pat in BARE_WILDCARDS:
        return True
    try:
        rx = glob_to_regex(pat)
    except re.error:
        return False
    if all(rx.match(probe) for probe in CATCH_ALL_PROBES):
        return True
    return all(rx.match(probe) for probe in SINGLE_SEGMENT_PROBES)


#: frontmatter 里"无 type 字段"的登记记号
NO_TYPE = "(none)"

#: 写侧 frontmatter 解析器的惰性缓存 (None = 不可用)
_UNSET = object()
_WRITER_FM: Any = _UNSET

#: (已移除手写正则读取: frontmatter 一律走真 YAML 解析, 解析失败即 (none) ——
#:  与写侧 lancedb_client._parse_frontmatter 的失败语义逐字对齐)


# ---------------------------------------------------------------------------
# glob → regex (自带实现: 不依赖 PurePath.full_match 的版本差异, 且可单测)
# ---------------------------------------------------------------------------
def glob_to_regex(pat: str) -> re.Pattern[str]:
    """把台账 glob 编译成 anchored regex。

    `**/` = 任意层前缀 (含零层); 结尾 `/**` = 任意层后缀 (**含零层** ——
    `节点/**` 同时匹配 `节点` 自身与其后代; 台账里成对写 ["节点", "节点/**"]
    是冗余但显式的写法, 便于人读);
    其余 `**` = 任意字符; `*` = 段内任意; `?` = 段内单字符;
    `[...]` = 段内字符类 (支持 `!`/`^` 取反) —— DIV-2 的大小写模式依赖它,
    缺了会被 re.escape 转成字面量而永不命中。
    ⚠️ DIV-2 实际用的是**两个较窄**的 pattern (`**/*.M[Dd]` / `**/*.[Mm]D`),
    刻意**不用** `*.[Mm][Dd]` —— 后者会连全小写 `.md` 一起吃掉从而遮蔽 G6, 见 YAML。
    """
    out: list[str] = []
    i, n = 0, len(pat)
    while i < n:
        if pat.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pat.startswith("/**", i) and i + 3 == n:
            out.append("(?:/.*)?")
            i += 3
        elif pat.startswith("**", i):
            out.append(".*")
            i += 2
        elif pat[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pat[i] == "?":
            out.append("[^/]")
            i += 1
        elif pat[i] == "[":
            close = pat.find("]", i + 1)
            if close == -1:  # 无闭合 → 退化为字面量 `[`
                out.append(re.escape(pat[i]))
                i += 1
                continue
            body = pat[i + 1 : close]
            if body.startswith(("!", "^")):
                body = "^" + body[1:]
            # 字符类内只允许字面量与 `-`; `/` 不得进类 (段边界不可跨)
            out.append("[" + body.replace("\\", "\\\\").replace("/", "") + "]")
            i = close + 1
        else:
            out.append(re.escape(pat[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def glob_match(rel: str, pat: str) -> bool:
    return glob_to_regex(pat).match(rel) is not None


# ---------------------------------------------------------------------------
# findings
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    code: str
    subject: str  # 出问题的路径 / 类型字面量
    detail: str
    exempted_by: str = ""

    @property
    def blocking(self) -> bool:
        return not self.exempted_by


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    files_seen: int = 0
    dirs_seen: int = 0
    probe_should_index_ok: int = 0
    probe_check_vault_path_ok: int = 0
    probe_divergent: list[str] = field(default_factory=list)
    probe_skipped: bool = False


class ConfigError(RuntimeError):
    """配置或环境错误 → 退出 2。"""


# ---------------------------------------------------------------------------
# 载入 + 契约校验 (指纹先于解析)
# ---------------------------------------------------------------------------
def load_rules(yaml_path: Path = ROLES_YAML, *, verify_sha: bool = True) -> dict[str, Any]:
    if not yaml_path.is_file():
        raise ConfigError(f"台账文件不存在: {yaml_path}")
    raw = yaml_path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if verify_sha and actual_sha != ROLES_SHA256:
        raise ConfigError(
            f"台账指纹不匹配 (双文件契约): {yaml_path.name}\n"
            f"  期望 (脚本 ROLES_SHA256): {ROLES_SHA256}\n"
            f"  实际:                     {actual_sha}\n"
            f"  改台账必须同 commit 更新脚本常量。刷新: "
            f"python3 {Path(__file__).name} --print-roles-sha"
        )
    try:
        import yaml  # noqa: PLC0415  (延迟导入: --print-roles-sha 不需要它)
    except ImportError as exc:  # pragma: no cover - 环境缺依赖
        raise ConfigError(f"缺少 PyYAML: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        # round-8: 非法 UTF-8 此前在 decode 处抛出, 越过 CLI 的 ConfigError-only 捕获
        raise ConfigError(f"台账不是合法 UTF-8: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"台账 YAML 解析失败: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("台账根节点必须是 mapping")
    # round-7 MEDIUM: 契约校验此前不是总函数 —— 畸形 glob/pattern 会抛
    # TypeError/AttributeError, 而 CLI 只捕 ConfigError → 用户看到的是 traceback
    # 而不是"配置错误, 退出 2"。这里统一收口。
    try:
        _verify_contract(data)
    except ConfigError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"台账结构异常 ({exc.__class__.__name__}): {exc}") from exc
    return data


def _verify_contract(data: dict[str, Any]) -> None:
    ledger_entries = list(iter_entries(data))
    sections = tuple(data.keys())
    if sections != EXPECTED_SECTIONS:
        raise ConfigError(f"顶层节名/顺序与 EXPECTED_SECTIONS 不符\n  期望: {EXPECTED_SECTIONS}\n  实际: {sections}")

    values = data["doc_type_whitelist"].get("values") or []
    actual = tuple((v.get("value"), tuple(v.get("roles") or ()), v.get("census_verdict_tag")) for v in values)
    if actual != EXPECTED_DOC_TYPES:
        raise ConfigError(f"doc_type 六取值与 EXPECTED_DOC_TYPES 不符\n  期望: {EXPECTED_DOC_TYPES}\n  实际: {actual}")

    # roles 必须恰好等于 registered_by 所指条目的角色集合 —— 防"取值横跨多角色
    # 却只写一个角色"那类撒谎 (对抗审查 HIGH)。
    by_id = {e["id"]: e for e in ledger_entries}
    for v in values:
        refs = v.get("registered_by") or []
        missing = [r for r in refs if r not in by_id]
        if missing:
            raise ConfigError(f"doc_type {v.get('value')} 的 registered_by 引用了不存在的条目 {missing}")
        # round-8 新 HIGH: 此前只验"已列引用的角色", 不验**引用完整性** ——
        # exam_board 的写侧推断不限目录, 凡"允许无 type 且进索引"的条目都能产出它,
        # 却可以不出现在 registered_by 里。
        if v.get("value") == "exam_board":
            producers = {
                e["id"]
                for e in ledger_entries
                if NO_TYPE in ((e.get("match") or {}).get("frontmatter_type") or []) and e.get("rag_index")
            }
            missing_prod = sorted(producers - set(refs))
            if missing_prod:
                raise ConfigError(
                    f"doc_type exam_board 的 registered_by 漏了可产出它的条目 {missing_prod} —— "
                    f"写侧的 exam_board 推断(无 type + exam_question_id)不限目录"
                )
        actual_roles = tuple(sorted({by_id[r]["role"] for r in refs}))
        if tuple(v.get("roles") or ()) != actual_roles:
            raise ConfigError(
                f"doc_type {v.get('value')} 的 roles={v.get('roles')} 与 registered_by 实际角色集 "
                f"{list(actual_roles)} 不符 —— 角色映射必须由条目复算, 不许手写"
            )

    for rf in data.get("root_files") or []:
        # round-7 MEDIUM: scope 拼错会静默按 root 处理
        if rf.get("scope", "root") not in ("root", "any_level"):
            raise ConfigError(f"root_files {rf.get('id')} 的 scope={rf.get('scope')!r} 不在 ('root', 'any_level')")
        if rf.get("scope") == "any_level":
            gs = rf.get("governance_scope")
            if gs not in VALID_GOVERNANCE_SCOPES:
                raise ConfigError(
                    f"root_files {rf.get('id')} 是 any_level 行, 必须声明 "
                    f"governance_scope ∈ {VALID_GOVERNANCE_SCOPES} —— 它会按 basename 抢在容器行"
                    f"之前命中, 不声明就会用根级的 owner/retention 覆盖深层容器的治理规则"
                )

    for rf in data.get("root_files") or []:
        if rf.get("id") != EXPECTED_LAST_ROOT_FILE_ID:
            continue
        ki = rf.get("known_instances")
        # ⛔ round-4 HIGH: 没有结构校验时可写成标量字符串, 而 `rel in "a.md,b.md"`
        #    是**子串**判定 —— 任意单字符文件名都会被判为"已登记", G9 整条失效。
        if not isinstance(ki, list) or not ki or not all(isinstance(x, str) and x.strip() for x in ki):
            raise ConfigError(
                f"root_files {rf.get('id')} 的 known_instances 必须是**非空字符串列表** "
                f"(标量会让成员判定退化成子串匹配, G9 形同虚设), 实际 {ki!r}"
            )

    root_files = data.get("root_files") or []
    if not root_files or root_files[-1].get("id") != EXPECTED_LAST_ROOT_FILE_ID:
        last = root_files[-1].get("id") if root_files else None
        raise ConfigError(f"root_files 末行必须是 {EXPECTED_LAST_ROOT_FILE_ID} (宽匹配兜底行), 实际: {last}")

    seen_ids: set[str] = set()
    # round-7 HIGH: 唯一性/格式此前只覆盖三个 ledger 节, repo_docs 内重复与
    # 跨节重复均被接受。改为**全体 id 同一命名空间**。
    for entry in ledger_entries:
        _verify_entry(entry)
    for entry in ledger_entries + list(data.get("repo_docs") or []):
        eid = entry.get("id")
        if not _nonempty_str(eid):
            raise ConfigError(f"条目缺 id 或 id 非字符串: {entry.get('id')!r}")
        # round-6 HIGH: 头部声明"id 全局唯一 / kebab-case", 但契约此前不校验,
        # 重复 id 副本可在 --enforce 下拿到 0 finding。
        if eid in seen_ids:
            raise ConfigError(f"条目 id 重复: {eid} (头部声明 id 必须全局唯一)")
        seen_ids.add(eid)
        # round-7: 原正则允许 `foo-bar.baz` / 连续点 / 尾点, 不是 kebab-case
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", eid):
            raise ConfigError(f"条目 id {eid!r} 不符 kebab-case (头部声明的格式契约)")

    for art in data.get("derived_artifacts") or []:
        surface = art.get("surface")
        if surface not in VALID_SURFACES:
            raise ConfigError(f"derived_artifacts {art.get('id')} 的 surface={surface!r} 不在 {VALID_SURFACES}")
        globs = (art.get("match") or {}).get("file_glob") or []
        if surface == "vault_file":
            if not globs:
                raise ConfigError(f"derived_artifacts {art.get('id')} surface=vault_file 但 file_glob 为空")
        elif not _is_nonempty_str_mapping(art.get("identifier")):
            # store / http_response 不落 vault 文件, glob 必然为空 —— 但不能因此
            # 变成"空且不可核对"。强制 identifier 显式登记其身份面。
            raise ConfigError(
                f"derived_artifacts {art.get('id')} surface={surface} 无 file_glob 时必须有 identifier, "
                f"且必须是**非空 mapping、每个值为非空字符串** "
                f"(对抗审查: 只验 truthiness 时 identifier='x' 这种标量也能过, "
                f"该行照样既无法机械识别也无法人工复核)"
            )

    for rd in data.get("repo_docs") or []:
        for fld in REQUIRED_REPO_FIELDS:
            if fld not in rd:
                raise ConfigError(f"repo_docs {rd.get('id')} 缺必填字段 {fld}")
            if fld in _TEXT_FIELDS and (not isinstance(rd[fld], str) or not rd[fld].strip()):
                raise ConfigError(f"repo_docs {rd.get('id')} 的 {fld} 必须是非空字符串, 实际 {rd[fld]!r}")
        # 结构校验 (对抗审查 H3): 只验 truthiness 时 path_glob=[] 与
        # rag_index="false" (字符串真值) 都能蒙混过关。
        globs = rd.get("path_glob")
        if not isinstance(globs, list) or not globs or not all(isinstance(g, str) and g.strip() for g in globs):
            raise ConfigError(f"repo_docs {rd.get('id')} 的 path_glob 必须是非空字符串列表")
        for col in ("rag_index", "memory_write"):
            if not isinstance(rd[col], bool):
                raise ConfigError(f"repo_docs {rd.get('id')} 的 {col} 必须是 bool, 实际 {rd[col]!r} (字符串伪布尔恒真)")
        if rd["role"] not in VALID_ROLES:
            raise ConfigError(f"repo_docs {rd['id']} role={rd['role']!r} 不在 {VALID_ROLES}")
        if rd["rag_retrieval"] not in VALID_RETRIEVAL:
            raise ConfigError(f"repo_docs {rd['id']} rag_retrieval={rd['rag_retrieval']!r} 不在 {VALID_RETRIEVAL}")
        # round-8: 这两条此前只管 ledger 三节, repo_docs 是绕过口
        if rd["rag_retrieval"] == "conditional" and not _nonempty_str(rd.get("rag_retrieval_note")):
            raise ConfigError(f"repo_docs {rd['id']}: rag_retrieval=conditional 必须另填非空字符串 rag_retrieval_note")
        if "surface" in rd:
            raise ConfigError(f"repo_docs {rd['id']} 不许声明 surface (那是 derived_artifacts 的字段)")

    for div in data["admission_surfaces"].get("by_design_divergences") or []:
        pats = div.get("patterns")
        if not pats or not isinstance(pats, list):
            raise ConfigError(f"by_design_divergences {div.get('id')} 缺 patterns 列表")
        for pat in pats:
            if is_catch_all(pat):
                raise ConfigError(f"by_design_divergences {div.get('id')} 含裸通配 {pat!r} —— 会遮蔽全部新分歧类")
            if not names_something(pat):
                raise ConfigError(
                    f"by_design_divergences {div.get('id')} 含不指名道姓的模式 {pat!r} —— 拆成两条就能遮蔽全部新分歧类"
                )
        if is_union_catch_all(pats):
            raise ConfigError(
                f"by_design_divergences {div.get('id')} 的 patterns 并集构成 catch-all {pats} —— 会遮蔽全部新分歧类"
            )
        # ⛔ 反软化: `requires_resolution_stable` 若可缺省或被单边置 false, 就等于
        #    把 round-2 BLOCKER 的那道绑定在 yaml 侧一键关掉。故要求**显式声明**;
        #    置 false 时必须另附 resolution_unstable_rationale 逐条论证
        #    "这一类分歧对 symlink 路径同样成立", 否则拒。
        if "requires_resolution_stable" not in div:
            raise ConfigError(
                f"by_design_divergences {div.get('id')} 必须显式声明 requires_resolution_stable "
                f"—— 缺省会让路径解析稳定性绑定形同虚设"
            )
        if div["requires_resolution_stable"] is not True:
            if not _nonempty_str(div.get("resolution_unstable_rationale")):
                raise ConfigError(
                    f"by_design_divergences {div.get('id')} 把 requires_resolution_stable 置为非 True, "
                    f"必须另附 resolution_unstable_rationale 论证该类分歧对 symlink 路径同样成立 "
                    f"(否则等于单边关掉绑定)"
                )
        # round-6 HIGH: scope 拼错会被当成 "any" 处理, 静默把分歧豁免扩到任意层级。
        if div.get("scope") not in VALID_DIVERGENCE_SCOPES:
            raise ConfigError(
                f"by_design_divergences {div.get('id')} 的 scope={div.get('scope')!r} "
                f"不在 {VALID_DIVERGENCE_SCOPES} —— 拼错会静默扩大豁免范围"
            )
        for rk in ("rag_reason", "memory_reason"):
            if not _nonempty_str(div.get(rk)):
                raise ConfigError(
                    f"by_design_divergences {div.get('id')} 缺 {rk} —— "
                    f"只绑布尔对会让同向不同因的新分歧被静默吞掉 (G6 失效)"
                )
        if not _nonempty_str(div.get("rationale")):
            raise ConfigError(f"by_design_divergences {div.get('id')} 缺 rationale (分歧是登记对象, 必须写明依据)")
        for col in ("rag_index", "memory_write"):
            if not isinstance(div.get(col), bool):
                raise ConfigError(f"by_design_divergences {div.get('id')} 的 {col} 必须是 bool")

    for gap in data.get("known_gaps") or []:
        literal = str(gap.get("literal", ""))
        if any(ch in literal for ch in "*?["):
            raise ConfigError(f"known_gaps.literal 必须是字面量 (禁通配符): {literal!r}")
        if not gap.get("reason") or not gap.get("owner_card"):
            raise ConfigError(f"known_gaps 缺 reason / owner_card: {gap.get('id')}")
        for code in gap.get("finding_codes") or []:
            if code not in GAP_EXEMPTIBLE:
                raise ConfigError(
                    f"known_gaps {gap.get('id')} 试图豁免 {code} —— "
                    f"只有 {sorted(GAP_EXEMPTIBLE)} 可豁免; "
                    f"G4/G5/G6/G7 是台账与代码不符, 豁免它们等于把台账做软来凑绿"
                )


def _verify_entry(entry: dict[str, Any]) -> None:
    eid = entry.get("id", "<no-id>")
    for fld in REQUIRED_ENTRY_FIELDS:
        if fld not in entry:
            raise ConfigError(f"条目 {eid} 缺必填字段 {fld}")
        # ⛔ 文本类字段必须是**非空字符串** (round-3 实证: 原来用 str(v).strip()
        #    验 truthiness, `None` / `[]` / `{}` 字符串化后都非空, 全部放行)。
        if fld in _TEXT_FIELDS and (not isinstance(entry[fld], str) or not entry[fld].strip()):
            raise ConfigError(f"条目 {eid} 的 {fld} 必须是非空字符串, 实际 {entry[fld]!r}")
    if entry["role"] not in VALID_ROLES:
        raise ConfigError(f"条目 {eid} role={entry['role']!r} 不在 {VALID_ROLES}")
    for col in ("rag_index", "memory_write"):
        if not isinstance(entry[col], bool):
            raise ConfigError(f"条目 {eid} 的 {col} 必须是 bool, 实际 {entry[col]!r}")
    if entry["rag_retrieval"] not in VALID_RETRIEVAL:
        raise ConfigError(f"条目 {eid} rag_retrieval={entry['rag_retrieval']!r} 不在 {VALID_RETRIEVAL}")
    if not entry["rag_index"] and entry["rag_retrieval"] != "not_indexed":
        raise ConfigError(f"条目 {eid}: rag_index=false 时 rag_retrieval 必须是 not_indexed")
    if entry["rag_retrieval"] == "conditional" and not _nonempty_str(entry.get("rag_retrieval_note")):
        raise ConfigError(
            f"条目 {eid}: rag_retrieval=conditional 必须另填**非空字符串** rag_retrieval_note "
            f"(round-7: null/[]/{{}}/123 此前都被 str().strip() 放行)"
        )
    # round-7 HIGH: 写侧的 exam_board 推断 (无 type + 含 exam_question_id) **不限目录**,
    # 所以任何"允许无 type 且进索引"的条目都可能承载被读侧排除的考察文件 ——
    # 一律不许一刀切声明 included。
    if NO_TYPE in ((entry.get("match") or {}).get("frontmatter_type") or []) and entry["rag_index"]:
        if entry["rag_retrieval"] != "conditional":
            raise ConfigError(
                f"条目 {eid}: 允许无 type 的文档且 rag_index=true, 则 rag_retrieval 必须是 conditional "
                f"—— 写侧对'无 type + exam_question_id'的 exam_board 推断不限目录, 声明 included 会对信息隔离面撒谎"
            )

    diverges = entry["rag_index"] != entry["memory_write"]
    reason = str(entry.get("divergence_reason", "") or "").strip()
    if diverges and len(reason) < 20:
        raise ConfigError(f"条目 {eid} 双列分歧但 divergence_reason 缺失或过短 (分歧是登记对象, 必须写明依据)")
    if not diverges and reason:
        raise ConfigError(f"条目 {eid} 双列一致却填了 divergence_reason (陈旧断言)")

    match = entry.get("match")
    if not isinstance(match, dict):
        raise ConfigError(f"条目 {eid} 的 match 必须是 mapping")
    # round-6 HIGH: 头部声明"match 结构必填", 但空 match 此前被接受 —— 一个
    # 既无 dir_glob 又无 file_glob 的行等于没登记任何东西。
    # (store / http_response 行由 derived_artifacts 的 identifier 契约兜底)
    if entry.get("_section") != "derived_artifacts" and "surface" in entry:
        raise ConfigError(
            f"条目 {eid} 不在 derived_artifacts 却声明了 surface —— "
            f"round-7: 普通行自报 surface: store 即可绕过 match 必填检查"
        )
    if not (match.get("dir_glob") or match.get("file_glob")) and entry.get("surface") in (None, "vault_file"):
        raise ConfigError(f"条目 {eid} 的 match 既无 dir_glob 也无 file_glob —— 该行不登记任何东西")
    for key in ("dir_glob", "file_glob"):
        raw_pats = match.get(key)
        # round-8: `dir_glob: []` 显式空列表此前被 `or []` 悄悄放行 (只要 sibling 非空)
        if isinstance(raw_pats, list) and not raw_pats:
            raise ConfigError(f"条目 {eid} 的 {key} 是显式空列表 —— 要么写非空列表, 要么整个键别写")
        if raw_pats is not None and not isinstance(raw_pats, list):
            raise ConfigError(f"条目 {eid} 的 {key} 必须是列表, 实际 {raw_pats!r} (标量此前被静默接受)")
        pats = raw_pats or []
        if not all(_nonempty_str(p) for p in pats):
            raise ConfigError(
                f"条目 {eid} 的 {key} 含非字符串/空元素: {pats!r} (此前 [null] 抛 TypeError 而非 ConfigError)"
            )
        for pat in pats:
            if is_catch_all(pat):
                raise ConfigError(f"条目 {eid} 的 {key} 含裸通配 {pat!r} —— catch-all 会让未登记检查恒绿")
            if not names_something(pat):
                raise ConfigError(
                    f"条目 {eid} 的 {key} 含**不指名道姓**的模式 {pat!r} —— 只由通配符/字符类拼成的 glob "
                    f"不标识任何一类文档, 拆成两行就能糊住全场 (`**/.*` + `**/[!.]*`)"
                )
        if is_union_catch_all(pats):
            raise ConfigError(
                f"条目 {eid} 的 {key} **并集**构成 catch-all {pats} —— 逐条都不是通配, "
                f"合起来却覆盖一切, 未登记检查同样恒绿"
            )


def _nonempty_str(val: Any) -> bool:
    """非空字符串。⛔ 不要用 `str(v).strip()` —— `None` / `[]` / `{}` / `123`
    字符串化后都非空, round-7 实测这四种全被放行。"""
    return isinstance(val, str) and bool(val.strip())


def _is_nonempty_str_mapping(val: Any) -> bool:
    """非空 mapping 且每个值都是非空字符串/非空列表 —— 用于 identifier 的结构校验。"""
    if not isinstance(val, dict) or not val:
        return False
    for v in val.values():
        if isinstance(v, str):
            if not v.strip():
                return False
        elif isinstance(v, list):
            if not v or not all(isinstance(x, str) and x.strip() for x in v):
                return False
        else:
            return False
    return True


def iter_entries(data: dict[str, Any]):
    """遍历三个带完整字段契约的条目节 (repo_docs 是另节, 字段集不同)。

    顺带把所属节名注入 `_section` (仅内存, 不写回 yaml) —— 契约需要区分
    "derived_artifacts 行可以有 surface" 与 "普通行不许自报 surface"。
    """
    for section in ("vault_entries", "root_files", "derived_artifacts"):
        for entry in data.get(section) or []:
            # ⛔ 必须**覆盖**而不是 setdefault (round-8): yaml 里自报
            #    `_section: derived_artifacts` 即可骗过"普通行不许有 surface"那道门。
            entry["_section"] = section
            yield entry


# ---------------------------------------------------------------------------
# 归属解析
# ---------------------------------------------------------------------------
def _entry_matches_file(entry: dict[str, Any], rel: str, *, is_root: bool, section: str) -> bool:
    match = entry.get("match") or {}
    globs = match.get("file_glob") or []
    if not globs:
        return False
    if section == "root_files":
        scope = entry.get("scope", "root")
        if scope == "any_level":
            return any(glob_match(Path(rel).name, pat) for pat in globs)
        return is_root and any(glob_match(rel, pat) for pat in globs)
    return any(glob_match(rel, pat) for pat in globs)


def resolve_file_entry(data: dict[str, Any], rel: str) -> dict[str, Any] | None:
    """文件 → 台账条目。顺序: root_files → derived_artifacts → vault_entries(目录)。"""
    is_root = "/" not in rel
    for section in ("root_files", "derived_artifacts"):
        for entry in data.get(section) or []:
            if _entry_matches_file(entry, rel, is_root=is_root, section=section):
                return entry
    parent = str(Path(rel).parent)
    if parent in (".", ""):
        return None
    return resolve_dir_entry(data, parent)


def resolve_dir_entry(data: dict[str, Any], rel_dir: str) -> dict[str, Any] | None:
    for entry in data.get("vault_entries") or []:
        for pat in (entry.get("match") or {}).get("dir_glob") or []:
            if glob_match(rel_dir, pat):
                return entry
    return None


def _writer_frontmatter_parser():
    """写侧真正在用的 frontmatter 解析器 (`LanceDBClient._parse_frontmatter`)。

    ⛔ 手写块提取一定会漂 (round-3 实证漏判 3 类 / 假阳性 2 类: 首尾分隔符带尾随空白、
    frontmatter 超过行数上限、`...` 结束符、缺结束符)。唯一不会漂的做法是**直接调用
    写侧那一个函数** —— 与 "不重新实现准入判定" 同一条原则。
    返回 None 表示不可用 (严格只读 / 无 venv), 此时回落到本模块的保守解析并如实标注。
    """
    global _WRITER_FM
    if _WRITER_FM is not _UNSET:
        return _WRITER_FM
    try:
        from agentic_rag.clients.lancedb_client import LanceDBClient  # noqa: PLC0415

        _WRITER_FM = LanceDBClient._parse_frontmatter
    except Exception:  # noqa: BLE001 - 无 venv / 严格只读
        _WRITER_FM = None
    return _WRITER_FM


def read_frontmatter_type(path: Path, *, parser: Any = _UNSET) -> str:
    """读 frontmatter 的 `type`, 语义与写侧**逐字相同**。无 frontmatter / 无 type → `(none)`。

    默认直接调用写侧 `LanceDBClient._parse_frontmatter`; 取值规则同 `lancedb_client.py:2740`
    的 `str(frontmatter.get("type", "") or "").lower().strip()` (精确小写 key、值 lower/strip、
    解析失败返回 {} → 视为无 type)。
    如实声明的建模边界: 写侧另有 `exam_question_id` 推断 `exam_board`、路径启发推断
    `video_transcript` 两条**非 frontmatter**来源, 本函数只建模 frontmatter 直通面。
    """
    try:
        # ⛔ 严格 UTF-8, 与写侧一致 (round-4 相邻 HIGH): 写侧 `lancedb_client.py:1979`
        #    用严格解码并在失败时**整条跳过该文件** (不索引)。此前这里用
        #    errors="replace" 硬读, 对非法 UTF-8 文件会得出一个写侧根本不会产生的
        #    doc_type。解码失败 → 该文件写侧不入库 → 无 doc_type → (none)。
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return NO_TYPE
    except OSError:
        return NO_TYPE

    # parser 显式传 None = 明确要求走回落 (降级档); 不传 = 自行取写侧解析器
    fn = _writer_frontmatter_parser() if parser is _UNSET else parser
    if fn is not None:
        try:
            fm, _body = fn(content)
        except Exception:  # noqa: BLE001 - 写侧自己会吞异常返回 {}, 这里同样不中断扫描
            return NO_TYPE
        if isinstance(fm, dict):
            return str(fm.get("type", "") or "").lower().strip() or NO_TYPE
        return NO_TYPE

    return _fallback_frontmatter_type(content)


def _fallback_frontmatter_type(content: str) -> str:
    """写侧解析器不可用时的保守回落 (仅 --no-probe / 无 venv 路径会走到)。

    刻意保守: 只认首行恰为 `---`(允许尾随空白)、以 `---`/`...` 结束的块, 交给 PyYAML;
    解析不了就当无 type。与写侧可能有细微差异, 故 scan() 会在 info 里如实标注。
    """
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return NO_TYPE
    block: list[str] = []
    for line in lines[1:]:
        if line.strip() in ("---", "..."):
            break
        block.append(line)
    if not block:
        return NO_TYPE
    try:
        import yaml  # noqa: PLC0415

        parsed = yaml.safe_load("\n".join(block))
    except Exception:  # noqa: BLE001
        return NO_TYPE
    if not isinstance(parsed, dict):
        return NO_TYPE
    return str(parsed.get("type", "") or "").lower().strip() or NO_TYPE


# ---------------------------------------------------------------------------
# 真实准入函数 (不重新实现 —— 台账双列必须对真实代码可证伪)
# ---------------------------------------------------------------------------
def load_admission_fns(vault_root: Path):
    """返回 (should_index, check_vault_path) 两个真实函数的 (rel)->bool 包装。"""
    backend_root = Path(__file__).resolve().parent.parent
    for p in (str(backend_root), str(backend_root / "lib")):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        from app.core.vault_admission import check_vault_path
        from app.services.vault_index_orchestrator import VaultIndexOrchestrator
    except Exception as exc:  # pragma: no cover - 环境缺依赖 / 无可写临时目录
        raise ConfigError(
            f"无法导入真实准入函数 (需 backend venv): {exc}\n"
            f"  提示: import 链含 jieba.initialize(), 需要可写的系统临时目录。"
            f"严格只读环境请改用 --no-probe (只做 schema/登记面检查, 零 import 副作用)。"
        ) from exc

    # __init__ 只做属性赋值 (已核源码: _pending_file 仅构造 Path 不落盘,
    # LanceDB 连接在 _get_client() 里, 本脚本从不调用) → 零写入。
    orch = VaultIndexOrchestrator(str(vault_root))

    def rag(rel: str) -> tuple[bool, str]:
        return orch.should_index(rel)

    def mem(rel: str) -> tuple[bool, str]:
        return check_vault_path(rel, vault_root)

    # ⛔ 预热 (round-2 HIGH-5): 两个函数内部都有**惰性 import**
    # (should_index → lancedb_client → jieba.initialize())。不预热的话, 严格只读
    # 环境下异常会在扫描中途的首次调用抛出, 绕过本函数的 try → 退出码变成 1 而不是
    # 契约声明的 2。在这里先各调一次, 把惰性 import 的失败收进同一个捕获面。
    try:
        rag("__admission_warmup__.md")
        mem("__admission_warmup__.md")
    except Exception as exc:  # pragma: no cover - 严格只读环境
        raise ConfigError(
            f"真实准入函数首次调用失败 (惰性 import 需要可写临时目录): {exc}\n"
            f"  严格只读环境请用 --no-probe --allow-degraded (只做 schema/登记面检查)。"
        ) from exc

    return rag, mem


# ---------------------------------------------------------------------------
# 扫描
# ---------------------------------------------------------------------------
def _gap_exemption(data: dict[str, Any], code: str, subject: str) -> str:
    if code not in GAP_EXEMPTIBLE:
        return ""
    for gap in data.get("known_gaps") or []:
        if code in (gap.get("finding_codes") or []) and gap.get("literal") == subject:
            return str(gap.get("id", ""))
    return ""


def scan(data: dict[str, Any], vault_root: Path, *, with_probe: bool = True) -> ScanResult:
    if not vault_root.is_dir():
        raise ConfigError(f"vault 根目录不存在: {vault_root}")
    res = ScanResult()
    res.probe_skipped = not with_probe
    rag_fn = mem_fn = None
    if with_probe:
        rag_fn, mem_fn = load_admission_fns(vault_root)

    # round-6 MEDIUM: `--no-probe` 自称"零 import 副作用", 但此前无条件调用写侧
    # parser (其模块初始化会跑 jieba.initialize() 并写系统临时缓存)。降级档只用回落解析。
    fm_parser = _writer_frontmatter_parser() if with_probe else None
    if fm_parser is None:
        res.info.append(
            "写侧 frontmatter 解析器不可用 (无 venv / 严格只读), G3/G4 走本模块的保守回落解析 "
            "—— 与写侧可能有细微差异, 结论按此打折"
        )
    doc_types = {v["value"] for v in data["doc_type_whitelist"]["values"]}
    declared_divs = data["admission_surfaces"].get("by_design_divergences") or []
    diverging_entry_ids = {e["id"] for e in iter_entries(data) if e["rag_index"] != e["memory_write"]}
    entries_with_live_files: set[str] = set()
    entries_with_live_divergence: set[str] = set()
    observed_types: dict[str, set[str]] = {}

    def add(code: str, subject: str, detail: str) -> None:
        res.findings.append(Finding(code, subject, detail, _gap_exemption(data, code, subject)))

    # ── 枚举 (可报错): rglob 会静默吞掉不可读子树与 dangling symlink ────────
    dirs, files, blind = _walk_vault(vault_root)
    for rel, why in blind:
        add("G10", rel, why)

    # ── 目录 ────────────────────────────────────────────────────────────
    for d in dirs:
        rel = d.relative_to(vault_root).as_posix()
        if rel.split("/")[0] == ".git":
            continue
        res.dirs_seen += 1
        if d.is_symlink():
            # ⛔ round-3 BLOCKER: 目录 symlink 的后代不被递归枚举 (本仓 Python 3.14 实测;
            #    其后代整棵子树静默不在扫描面内, 而生产刷新端点
            #    (endpoints/index.py) 会把任意相对路径直接交给 orchestrator ——
            #    盲区是可达的。不跟进 (会成环), 但必须判红。
            try:
                target = os.path.realpath(str(d))
            except OSError:
                target = "<unresolvable>"
            add("G8", rel, f"目录是符号链接 (→ {target}); rglob 不递归其后代, 该子树整棵不在扫描面内")
        if resolve_dir_entry(data, rel) is None:
            add("G1", rel, "live 目录未被任何 vault_entries.dir_glob 命中")

    # ── 文件 ────────────────────────────────────────────────────────────
    for f in files:
        rel = f.relative_to(vault_root).as_posix()
        if rel.split("/")[0] == ".git":
            continue
        res.files_seen += 1
        is_root = "/" not in rel
        # ⛔ G11 必须**先于**归属解析 (round-5 trace 指出的顺序缺口):
        #    原来放在 `entry is None → continue` 之后, 于是"未登记目录里的外逃链接"
        #    永远走不到这一步; 若该目录恰被合法 known_gaps 豁免 G1, 整条门就一个
        #    blocking finding 都不产生。越界是**路径事实**, 与能否归属无关。
        escaped = not _resolves_inside_vault(vault_root, rel)
        if escaped:
            add("G11", rel, "该路径解析到 vault 之外 —— 已判红并**拒绝读取其正文**")

        entry = resolve_file_entry(data, rel)

        if entry is None:
            if is_root:
                add("G2", rel, "vault 根级文件未被任何 root_files.file_glob 命中")
            else:
                add("G1", str(Path(rel).parent), f"文件 {rel} 所在目录未被登记")
            continue
        entries_with_live_files.add(entry["id"])
        if is_root and entry["id"] == EXPECTED_LAST_ROOT_FILE_ID:
            # ⛔ round-3 HIGH: 兜底行镜像的是**准入规则**, 不是来源与归属。
            #    一个机器生成的报告落在根目录, 会被静默读成"用户手写 wiki、不可重建"。
            #    故每个落到兜底行的根级 md 必须逐个登记 (登记动作 = 写进 known_instances)。
            known = entry.get("known_instances")
            if rel not in set(known if isinstance(known, list) else []):
                add(
                    "G9",
                    rel,
                    f"根级 md 落到兜底行 {entry['id']}, 但未登记在其 known_instances —— "
                    f"兜底行只能断言准入行为(rag_index={entry['rag_index']}/"
                    f"memory_write={entry['memory_write']}), 断不了 owner/role/retention",
                )
        if not is_root and entry.get("governance_scope") == "root_only":
            container = resolve_dir_entry(data, str(Path(rel).parent))
            res.info.append(
                f"{rel} 的准入两列取自 any_level 行 {entry['id']}(文件名黑名单盖过目录), "
                f"但其 owner/retention 只描述根级实例 —— 本文件的治理以容器行 "
                f"{container['id'] if container else '<未登记>'} 为准"
            )

        # G3 / G4 —— 只对 md 判定 frontmatter type
        if f.suffix.lower() == ".md" and not escaped:
            ftype = read_frontmatter_type(f, parser=fm_parser)
            observed_types.setdefault(entry["id"], set()).add(ftype)
            allowed = (entry.get("match") or {}).get("frontmatter_type") or []
            if ftype not in allowed:
                add(
                    "G3",
                    ftype,
                    f"{rel} 的 frontmatter type={ftype!r} 不在条目 {entry['id']} 的白名单 {allowed}",
                )
            if entry["rag_index"] and ftype != NO_TYPE and ftype not in doc_types:
                add(
                    "G4",
                    ftype,
                    f"{rel} 在 rag_index=true 的条目 {entry['id']} 覆盖下, "
                    f"但 type={ftype!r} 不在 doc_type_whitelist —— 写侧 frontmatter 直通无校验, 会成为野值",
                )

        if not with_probe:
            continue

        # G5 / G6 —— 对真实函数求值
        rag_ok, rag_reason = rag_fn(rel)  # type: ignore[misc]
        mem_ok, mem_reason = mem_fn(rel)  # type: ignore[misc]
        resolution_stable = _is_resolution_stable(vault_root, rel)
        res.probe_should_index_ok += int(rag_ok)
        res.probe_check_vault_path_ok += int(mem_ok)

        if f.suffix.lower() != ".md":
            # 非 md: 两面共有的 not_markdown 规则统一拒 (已登记在
            # admission_surfaces.*.reject_reasons), 与条目的 per-type 策略无关。
            # 不跳过而是断言该 surface 级不变量 —— 若哪天非 md 被放行, 照样判红。
            if rag_ok or mem_ok:
                add(
                    "G5",
                    rel,
                    f"非 Markdown 文件被准入面放行, 违反 surface 级 not_markdown 不变量: "
                    f"should_index={rag_ok}({rag_reason})/check_vault_path={mem_ok}({mem_reason})",
                )
        else:
            covered = _covered_by_declared_divergence(
                declared_divs, rel, is_root, rag_ok, rag_reason, mem_ok, mem_reason, resolution_stable
            )
            if rag_ok != entry["rag_index"] or mem_ok != entry["memory_write"]:
                if covered:
                    # ⛔ 已登记的分歧类 (Codex round-1 BLOCKER-1): 条目声明的是该类
                    # 文档的**常态**, by_design_divergences 声明的是其**例外**。
                    # 例外命中时判 G5 = 把「登记对象」当成 bug 报, 正是本卡明令禁止的。
                    res.info.append(
                        f"{rel} 偏离条目 {entry['id']} 的常态声明, 但命中已登记分歧类 —— "
                        f"should_index={rag_ok}({rag_reason})/check_vault_path={mem_ok}({mem_reason})"
                    )
                else:
                    add(
                        "G5",
                        rel,
                        f"条目 {entry['id']} 声明 rag_index={entry['rag_index']}/"
                        f"memory_write={entry['memory_write']}, 真实函数得 "
                        f"should_index={rag_ok}({rag_reason})/check_vault_path={mem_ok}({mem_reason})",
                    )

        if rag_ok != mem_ok:
            res.probe_divergent.append(rel)
            entries_with_live_divergence.add(entry["id"])
            if not _covered_by_declared_divergence(
                declared_divs, rel, is_root, rag_ok, rag_reason, mem_ok, mem_reason, resolution_stable
            ):
                add(
                    "G6",
                    rel,
                    f"真实分歧 should_index={rag_ok}({rag_reason}) vs check_vault_path={mem_ok}({mem_reason}) "
                    f"不属任何已登记的 by_design_divergences 模式 —— 出现了**新类**分歧",
                )

    # ── G7 陈旧分歧 ─────────────────────────────────────────────────────
    for eid in sorted(diverging_entry_ids):
        if not with_probe:
            continue
        if eid in entries_with_live_files and eid not in entries_with_live_divergence:
            add("G7", eid, "条目声明双列分歧, 但命中它的 live 文件实测均无分歧 (陈旧断言)")
        elif eid not in entries_with_live_files:
            res.info.append(f"条目 {eid} 声明双列分歧, live vault 当前 0 文件命中 (不判红: 登记的是类不是实例)")

    # ── 过度声明 (INFO): 声明了某 frontmatter type 但 live 该条目下无实例。
    #    不判红 —— 值可能只是暂时无实例 (例: 空目录)。判红的门在契约测试
    #    test_frontmatter_type_lists_are_tight 里 (它只对有 live md 的条目断言)。
    for eid, seen in sorted(observed_types.items()):
        entry = next((e for e in iter_entries(data) if e["id"] == eid), None)
        if entry is None:
            continue
        declared = set((entry.get("match") or {}).get("frontmatter_type") or [])
        extra = declared - seen
        if extra:
            res.info.append(f"条目 {eid} 过度声明 frontmatter_type {sorted(extra)} (live 无实例) —— 会放宽 G3")

    # ── 快照漂移 (INFO, 不判红: vault 是活的) ────────────────────────────
    snap = data["live_vault"].get("admission_probe") or {}
    if with_probe:
        for key, actual in (
            ("total_files", res.files_seen),
            ("should_index_ok", res.probe_should_index_ok),
            ("check_vault_path_ok", res.probe_check_vault_path_ok),
            ("divergent_files", len(res.probe_divergent)),
        ):
            if key in snap and snap[key] != actual:
                res.info.append(f"勘测快照漂移 {key}: 台账 {snap[key]} → 实测 {actual}")
    return res


def _resolves_inside_vault(vault_root: Path, rel: str) -> bool:
    """`rel` 解析后是否仍落在 vault 内 (含 vault 根自身)。"""
    try:
        base = os.path.realpath(str(vault_root))
        actual = os.path.realpath(os.path.join(str(vault_root), rel))
    except OSError:
        return False
    return actual == base or actual.startswith(base + os.sep)


def _walk_vault(vault_root: Path) -> tuple[list[Path], list[Path], list[tuple[str, str]]]:
    """枚举 vault, 并把**枚举不下去的地方**如实带出来。

    ⛔ 为什么不用 `rglob` (round-4 BLOCKER): 它会静默吞掉
      - 权限不可读的子树 (整棵消失, files_seen 直接少);
      - dangling / self 指向的 symlink (`is_dir()` 与 `is_file()` 都为 False,
        两轮过滤把它们一起滤没了);
      - 超长路径 (本机 macOS/py3.14 实测 relative_chars=1307 时枚举不到)。
    这些静默点都会让 "0 finding" 变成 "没看见"。本函数用 `os.walk(onerror=...)`
    收集错误, 并把"既非 dir 也非 file"的条目单列, 交由 G10 判红。
    """
    dirs: list[Path] = []
    files: list[Path] = []
    blind: list[tuple[str, str]] = []
    base = str(vault_root)

    def _onerror(err: OSError) -> None:
        try:
            rel = os.path.relpath(getattr(err, "filename", base) or base, base)
        except ValueError:  # pragma: no cover - 跨卷等异常
            rel = str(getattr(err, "filename", "<unknown>"))
        blind.append((rel, f"枚举失败, 该子树整棵不在扫描面内: {err.__class__.__name__}: {err}"))

    for dirpath, dirnames, filenames in os.walk(base, topdown=True, onerror=_onerror, followlinks=False):
        for name in list(dirnames) + list(filenames):
            full = Path(dirpath) / name
            try:
                rel = full.relative_to(vault_root).as_posix()
            except ValueError:  # pragma: no cover
                continue
            if rel.split("/")[0] == ".git":
                continue
            try:
                is_dir, is_file = full.is_dir(), full.is_file()
            except OSError as exc:
                blind.append((rel, f"无法判定类型 (stat 失败): {exc.__class__.__name__}: {exc}"))
                continue
            if is_dir:
                dirs.append(full)
            elif is_file:
                if not os.access(full, os.R_OK):
                    blind.append((rel, "文件不可读 (权限), 其 frontmatter 无法核对"))
                files.append(full)
            else:
                blind.append((rel, f"既非目录也非普通文件 (symlink={full.is_symlink()}) —— rglob 会静默漏掉这类条目"))
    return sorted(dirs), sorted(files), sorted(set(blind))


def _is_resolution_stable(vault_root: Path, rel: str) -> bool:
    """vault 内的 `rel` 是否"解析稳定" —— 路径上没有任何一段 symlink 改变了它的身份。

    判据 = `realpath(vault/rel)` 等于 `realpath(vault)/rel`。
    **必须以 realpath(vault) 为基准**而不是拿 `realpath(p) == p` 硬比: macOS 上
    `/tmp` 本身就是指向 `/private/tmp` 的 symlink, 硬比会把临时 fixture 里的
    每个文件都误判成不稳定, 从而让已登记分歧类在测试里全部失效。

    为什么要这个判据: 路径含 symlink 时, `should_index` 判的是 **lexical** 路径、
    `check_vault_path` 判的是 **resolved** 路径 —— 两者看的是**两个不同的对象**,
    已登记的分歧类 (都只为普通文件论证过) 不适用, 必须交回 G5/G6 如实报出。
    """
    try:
        base = os.path.realpath(str(vault_root))
        expected = os.path.normpath(os.path.join(base, rel))
        actual = os.path.realpath(os.path.join(str(vault_root), rel))
    except OSError:
        return False
    return actual == expected


def _covered_by_declared_divergence(
    declared: list[dict[str, Any]],
    rel: str,
    is_root: bool,
    rag_ok: bool,
    rag_reason: str,
    mem_ok: bool,
    mem_reason: str,
    resolution_stable: bool = True,
) -> bool:
    """路径的实测 (放行, reason) 二元组是否落在某个已登记的分歧类里。

    ⛔ reason 必须逐一相等 (Codex round-1 BLOCKER-2)：只比布尔对会让**同向但
    不同因**的新分歧被静默视为已登记。实测反例：根级 symlink
    `alias.md -> 节点/x.txt` 同样是 (True, False)，但 reason 是
    (ok, not_markdown)，与 DIV-1 论证的 (ok, root_level) 是两回事，必须判 G6。
    """
    for div in declared:
        # ⛔ 绑定路径解析稳定性 (round-2 BLOCKER): `检验白板/x.MD -> 节点/y.md` 与
        # DIV-2 的 pattern / scope / 布尔对 / reason 对**四者全等**, 但成因是
        # 「check_vault_path 对 resolved 路径判黑名单、should_index 对 lexical 路径判」
        # 这个第三类现象, 不是 DIV-2 论证的后缀大小写。两条已登记分歧都只为
        # **解析稳定的普通文件**论证过 → symlink 改变路径身份时一律不覆盖。
        if div.get("requires_resolution_stable", True) and not resolution_stable:
            continue
        if bool(div.get("rag_index")) != rag_ok or bool(div.get("memory_write")) != mem_ok:
            continue
        if str(div.get("rag_reason", "")) != rag_reason or str(div.get("memory_reason", "")) != mem_reason:
            continue
        scope = div.get("scope", "any")
        pats = div.get("patterns") or []
        if not pats:
            continue
        if scope == "root":
            if is_root and any(glob_match(rel, p) for p in pats):
                return True
        elif any(glob_match(rel, p) for p in pats):
            return True
    return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _default_vault() -> Path:
    import os

    env = os.environ.get("CANVAS_BASE_PATH")
    if env:
        return Path(env)
    dotenv = Path(__file__).resolve().parents[2] / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            if line.startswith("CANVAS_BASE_PATH="):
                return Path(line.split("=", 1)[1].strip())
    raise ConfigError("无法确定 live vault 路径: 设 CANVAS_BASE_PATH 或传 --vault")


def _print(res: ScanResult, data: dict[str, Any], vault: Path) -> None:
    print(f"{DIM}台账{RESET} {ROLES_YAML}")
    print(f"{DIM}vault{RESET} {vault}  ({res.dirs_seen} 目录 / {res.files_seen} 文件, 只读)")
    if res.probe_divergent:
        print(f"{DIM}双准入面实测分歧{RESET} {len(res.probe_divergent)} 条: {', '.join(res.probe_divergent[:5])}")
    for msg in res.info:
        print(f"{DIM}  info  {msg}{RESET}")
    if res.probe_skipped:
        print(
            f"{YELLOW}⚠ --no-probe: 已跳过 G5/G6/G7 (需真实准入函数求值) —— "
            f"本次仍跑 G1-G4 与 G8-G11 及全部契约检查。{RESET}"
        )
    if not res.findings:
        if res.probe_skipped:
            # ⛔ 对抗审查 SURVIVED: 原文案在 --no-probe 下字面为假 ——
            #    没跑 probe 就不能声称"台账双列与真实函数一致"。
            print(f"{GREEN}✓ 登记面无 finding{RESET}{YELLOW}（双列与真实函数是否一致：本次未验证）{RESET}")
        else:
            print(f"{GREEN}✓ 无 finding —— live vault 全部类型已登记, 且台账双列与真实函数一致{RESET}")
        return
    by_code: dict[str, list[Finding]] = {}
    for fd in res.findings:
        by_code.setdefault(fd.code, []).append(fd)
    for code in sorted(by_code):
        items = by_code[code]
        blocking = sum(1 for i in items if i.blocking)
        color = RED if blocking else YELLOW
        print(f"{color}{code}{RESET}  {len(items)} 条 (阻断 {blocking})")
        for fd in items:
            tag = f" {YELLOW}[gap:{fd.exempted_by}]{RESET}" if fd.exempted_by else ""
            print(f"    - {fd.subject}{tag}\n      {fd.detail}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CARD-G8-1 vault 文档角色台账裁判 (live vault 只读)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--report", action="store_true", help="全量报告, 恒退出 0")
    mode.add_argument("--enforce", action="store_true", help="有非豁免 finding 即退出 1")
    mode.add_argument("--print-roles-sha", action="store_true", help="打印台账全文 SHA-256 (刷新指纹用)")
    ap.add_argument("--vault", type=Path, default=None, help="live vault 根目录 (默认取 CANVAS_BASE_PATH)")
    ap.add_argument(
        "--no-probe",
        action="store_true",
        help="跳过真实准入函数求值: 保留 G1-G4 与 G8-G11 及全部契约检查, 只放弃 G5/G6/G7 "
        "(严格只读环境用 —— probe 的 import 链需要可写临时目录)",
    )
    ap.add_argument(
        "--allow-degraded",
        action="store_true",
        help="显式声明接受降级门: --enforce 与 --no-probe 同用时必须带它, 否则退出 2 (防把只跑了登记面的绿当成全量绿)",
    )
    ap.add_argument("--json", action="store_true", help="以 JSON 输出 finding")
    args = ap.parse_args(argv)

    if args.print_roles_sha:
        print(hashlib.sha256(ROLES_YAML.read_bytes()).hexdigest())
        return 0

    if args.enforce and args.no_probe and not args.allow_degraded:
        print(
            f"{RED}[拒绝执行]{RESET} --enforce 与 --no-probe 同用会跳过 G5/G6/G7 "
            f"(脚本契约称其'永不可豁免'), 退出 0 会被误读成全量通过。\n"
            f"  确需在严格只读环境跑降级门, 请显式加 --allow-degraded。",
            file=sys.stderr,
        )
        return 2

    try:
        data = load_rules()
        vault = args.vault or _default_vault()
        # 导入 app.* 会触发 structlog 往 stdout 打 INFO 行 (实测
        # "RAGService: LangGraph/Agentic RAG available"), 会把 --json 档污染成
        # 不可解析。扫描全程把 stdout 改道 stderr, 报告在其后才写真 stdout。
        with contextlib.redirect_stdout(sys.stderr):
            res = scan(data, vault, with_probe=not args.no_probe)
    except ConfigError as exc:
        print(f"{RED}[配置/环境错误]{RESET} {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "vault": str(vault),
                    "probe_skipped": res.probe_skipped,
                    # round-6 MEDIUM: 原来写死 G1-G4, 但 no-probe 下 G8/G9/G10/G11
                    # 照样跑 —— 只有需要真实函数求值的 G5/G6/G7 被跳过。
                    "checks_run": [c for c in ALL_FINDING_CODES if not (res.probe_skipped and c in ("G5", "G6", "G7"))],
                    "checks_skipped": ["G5", "G6", "G7"] if res.probe_skipped else [],
                    "dirs_seen": res.dirs_seen,
                    "files_seen": res.files_seen,
                    "divergent_files": res.probe_divergent,
                    "info": res.info,
                    "findings": [
                        {"code": f.code, "subject": f.subject, "detail": f.detail, "exempted_by": f.exempted_by}
                        for f in res.findings
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print(res, data, vault)

    if args.enforce and any(f.blocking for f in res.findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
