#!/usr/bin/env python3
"""CARD-G8-10 引用可解引用性核对（标准库 + PyYAML；对真实文件跑；不进代码地盘）v4.9。

v4.9（CARD-G8-10 r11 整改：r10-M1 + r10-L1）：
  ①（r10-M1）SHA provenance 的形态判定**去掉长度上限**：任何 `^[0-9A-Za-z]+$` token（白名单除外）
     要么是 8–40 位小写 hex OID（可解引用），要么 `sha-missing` 红 —— 41+ 位畸形 token 不再逃逸。
  ②（r10-L1）`outcome` **键**也做标量归一化（node 层 `_node_scalar_text(k)`、constructed 层
     `_iter_key_values` 内 str/bytes 归一）：`{ !!binary b3V0Y29tZQ==: pass }` 这类「binary 编码键名」
     不再漏判。

v4.8（CARD-G8-10 r10 整改：r9-M1 + r9-M2 + r9-M3）：
  ①（r9-M1）node 层对 `outcome` 值做**三分类**（pass / 非标量 / 枚举外），不再只找 pass：
     被 merge（`<<`）消费掉的内层源值若是 `!!int 123` / `!!binary Ym9ndXM=` / 空值等，
     同样 `outcome-enum` / `outcome-type` 红（constructed 面看不到这些被覆盖的源值）。
  ②（r9-M2）引用路径归一化改用 `posixpath.normpath`（`.//_bmad-output/…`、`a/./b`、重复斜杠
     一并归一化），归一化后以 `_bmad-output` 为**边界**（`_bmad-output` 或 `_bmad-output/…`）
     者进入 evidence 存在性 + 内容 digest 面。
  ③（r9-M3）SHA provenance 形态判定放宽到 **1–40 位纯字母数字 token**（白名单除外）：
     `abc` 之类 1–3 位畸形值不再逃逸；非 8–40 位小写 hex ⇒ `sha-missing` 红。

v4.7（CARD-G8-10 r9 整改：r8-H1 + r8-M1 + r8-M2）：
  ①（r8-H1）`!!binary` 形态穿透：node 层对 `tag:yaml.org,2002:binary` 标量先 base64 解码再比对；
     constructed 层用 `_scalar_text()` 归一化 str / bytes / bytearray；**任何非字符串标量的
     `outcome` 值 ⇒ `outcome-type` fail-closed 红**；`outcome` 值不在 {pass,fail,not_yet} ⇒
     `outcome-enum` 红（覆盖 "PASS"/未知词/二进制解码残留等）。
  ②（r8-M1）平文 SHA provenance 只接受 **immutable 8–40 位小写 hex OID**：可变 symbolic ref
     （`HEAD` / `main` 等）或畸形值一律 `sha-missing` 红（不再"能 rev-parse 就算数"）。
  ③（r8-M2）引用路径先归一化再判：剥前导 `./`；绝对路径 / 含 `..` 段直接红；归一化后仍以
     `_bmad-output/` 开头者做存在性 + 内容进 digest（`./_bmad-output/…` 变体不再逃逸）。

v4.6（CARD-G8-10 r8 整改：r7-H1 + r5-M1 + r5-M2 + r6-M1 + r7-L1）：
  ①（r7-H1）**StrictSafeLoader 拒绝同一 mapping 的重复显式 key** ⇒ `yaml-duplicate-key` 红（PyYAML
     `safe_load()` 默认 last-write-wins：早先写入的 `outcome: pass` 会被静默折叠）；并新增
     `yaml.compose_all` **node 层扫描**：mapping 键 `outcome` 的值节点（含 alias 解析到 anchor 源、
     含被 merge 消费掉的内层映射）标量 strip 后 == pass ⇒ `pass-unsupported`（覆盖 anchor/merge 源）；
     v4.5 的 constructed-data 扫描保留（覆盖 merge 结果与直接 alias 解析值）。
  ②（r5-M1）nodeid 路径与 file:line 引用**同口径归一化**（`_resolve_under_root`）：绝对路径 / 含 `..`
     段 / 解析后越根 ⇒ 红；归一化后必须仍在 `backend/tests/` 下（`backend/tests/../app/…` 不再穿透）。
  ③（r5-M2）无行号 evidence 目录引用必须**可解引用**（存在）且其内容逐文件进 digest；
     平文 SHA provenance 必须可解引用为 commit **且其 tree OID 进 digest**；形态判定放宽为
     「`^[0-9A-Za-z]+$` 且不在 `_ALNUM_NON_SHA_ALLOW`」⇒ 畸形 / 替换值不再逃逸（v4.9-r12 文案校正为不限长）。
  ④（r6-M1）owner ID 必须是**独立 token**：`path:line` 引用（含文件名内的 ID 子串）不贡献 ID。
  ⑤（r7-L1）输出区分 tracked / untracked dirty：`dirty=… dirty_tracked=… dirty_untracked=…`。

v4.5（Codex r6-H1 整改：pass 扫描从正则改为真 YAML 解析）：
  ① 顶部 `import yaml`（PyYAML 6.0.3）；import 失败 ⇒ `yaml-missing` 红，**禁静默回退正则**；
  ② 提取底账内全部 ```yaml / ```yml fenced block（含 §3 与未来追加块；info string 大小写不敏感）；0 块 ⇒ `yaml-blocks` 红；
  ③ 每块 `yaml.safe_load`；解析失败 ⇒ `yaml-parse-error` 红；
  ④ 递归遍历解析对象：凡 dict 键 `outcome` 的值解析后 == 字符串 "pass" ⇒ `pass-unsupported` 红
     （只认 `outcome` 键，不误伤 `meta.outcome_states` 枚举值）；覆盖转义双引号 / anchor / block
     scalar / 引号内空白 / 标签（`!!str`）等有效标量语法（r6-H1 两个显形输入：
     `outcome: "pa\\u0073s"` 与 `outcome: &not_yet pass`）。判等口径 = **strip 归一化**：
     block scalar（`>` / `|`）会带尾换行，去包裹空白后等于 "pass" 即红（比卡文字面 `== "pass"`
     更严一档，已在 UAT 登记，属 fail-closed 方向）；
  ⑤ 原正则扫描保留为**非 YAML / 散文面次级检查**（含去反引号口径）；v4.4 的引号正则与
     `_owner_scan_text()` 两条 r6 修复原地保留（r6-H2 定向闭合不得回退）。

v4.4（Codex r5 整改）：① pass 扫描识别**引号标量**（`outcome[:=]<sp>*["']?pass`；锚 A/F 复跑同红）；
  ② owner 白名单与 `_ID_RE` 同口径：**反引号内容保留参与分词**，唯 `path:line` 引用与 ID token 由
     各自专项检查（_check_refs / 允许集精确比对）覆盖后剔除——伪 owner 藏于反引号内不再逃逸；
  ③ usage 修正 `--expect-digest <32hex>`（原文档写 16hex，实现/输出一直是 32 hex）。

v4.3（Codex r4 整改）：① `pass` 扫描=**全底账 any-line**（去反引号后 `outcome[:=]<sp>pass`）；② owner 引号外词元走**白名单**（防伪 owner 与真 owner 并存）；③ nodeid 名须非空且标识符 grammar；④ 引用路径禁绝对/`..`、须解析在 root 内；⑤ digest 32 hex + 全 40 位 HEAD + dirty 计数回显。\n\nv4（r3 整改）：
  ① **pass 不在本脚本认证范围**：记录 `outcome=pass` ⇒ 直接红 `pass-unsupported`
     （§1 的 pass = candidate 树上完整证据 + 主 session 裁定，非记录自证；对齐 r2/r3
     复核「本脚本是必要的一致性检查、不是充分的 pass 门」的表述）；
  ② owner：链名→允许集快照 + 非空 + 仅 ID grammar（`owner-missing` / `owner-invalid`）；
  ③ nodeid：仅认 `backend/tests/**` 路径 + 非 skill 链每行**必须**有 nodeid 判据；
  ④ SHA：8–40 位 hex + 必须是 **commit**（`sha-missing`）；
  ⑤ quote：全句在出处行区间内 + 长度 ≥24 + **出处不得为底账自身**；
  ⑥ `expose=无` 分支仅限 `skill 链`；行号必须 ≥1；
  ⑦ digest = 底账 + 全部引用源文件 + nodeid 测试文件 + 脚本自身 + HEAD 的**原字节**
     sha256 组合；`--expect-digest` **必填**，输出回显 `expect_digest`。

用法: python3 check_g810_refs.py --ledger <底账> --root <树根> --expect-digest <32hex>
退出码: 0 = 全过；1 = 有失败项（逐条打印）。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import posixpath
import re
import subprocess
from pathlib import Path

try:
    import yaml  # PyYAML（卡文 §3.1：import 失败必须红，禁静默回退正则）
    import yaml.nodes as _yaml_nodes
except ImportError:  # pragma: no cover - 缺 PyYAML 环境走 yaml-missing 红分支
    yaml = None
    _yaml_nodes = None


if yaml is not None:

    class StrictSafeLoader(yaml.SafeLoader):
        """SafeLoader + 拒绝同一 mapping 的重复**显式** key（v4.6 / r7-H1）。

        SafeLoader 对重复 key 执行 last-write-wins（后者覆盖前者）：`outcome: "pa\u0073s", outcome:
        not_yet` 在解析结果里只剩 not_yet —— 早先写入 pass 记录被静默吞掉。这里在构造 mapping 前按
        显式 key 检重；`<<` merge 键除外（merge 语义由 flatten_mapping 处理：显式 key 覆盖 merge 源，
        是合法 YAML，不是重复 key）。
        """

        def construct_mapping(self, node, deep=False):
            if not isinstance(node, yaml.MappingNode):
                raise yaml.constructor.ConstructorError(
                    None, None, f"expected a mapping node, but found {node.id}", node.start_mark
                )
            seen: list = []
            for key_node, _value_node in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    continue
                key = self.construct_object(key_node, deep=deep)
                try:
                    hash(key)
                except TypeError as exc:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping", node.start_mark,
                        f"found unhashable key ({exc})", key_node.start_mark,
                    )
                if key in seen:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping", node.start_mark,
                        f"found duplicate key {key!r}", key_node.start_mark,
                    )
                seen.append(key)
            return super().construct_mapping(node, deep=deep)

else:  # pragma: no cover - 缺 PyYAML 时走 yaml-missing 红分支
    StrictSafeLoader = None


def _collect_anchors(node, out: dict, _stack: set | None = None) -> None:
    """doc 节点图 → {anchor 名: 节点}（v4.6；含递归 anchor 防护）。

    注：PyYAML 的 composer 在 compose 阶段就把 alias 解析为**同一节点对象**（没有 AliasNode 类），
    因此 alias 形态在 node 层扫描中天然可见；本函数只用于把 anchor 名登记进证据面。
    """
    if _yaml_nodes is None or node is None:
        return
    if _stack is None:
        _stack = set()
    if id(node) in _stack:
        return
    _stack = _stack | {id(node)}
    if getattr(node, "anchor", None):
        out.setdefault(node.anchor, node)
    if isinstance(node, _yaml_nodes.MappingNode):
        for k, v in node.value:
            _collect_anchors(k, out, _stack)
            _collect_anchors(v, out, _stack)
    elif isinstance(node, _yaml_nodes.SequenceNode):
        for v in node.value:
            _collect_anchors(v, out, _stack)


def _scalar_text(value: object) -> str | None:
    """YAML 标量值 → 归一化文本（str 原样；bytes/bytearray 按 utf-8 解码）；非标量 ⇒ None（v4.7 / r8-H1）。"""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    return None


def _node_scalar_text(node) -> str | None:
    """ScalarNode → 归一化文本；`!!binary` 标量先 base64 解码（v4.7 / r8-H1）。

    非标量节点 ⇒ None（调用方据此判 `outcome-type`）。
    """
    if _yaml_nodes is None or not isinstance(node, _yaml_nodes.ScalarNode):
        return None
    if node.tag == "tag:yaml.org,2002:binary":
        raw = node.value if isinstance(node.value, str) else ""
        try:
            return base64.b64decode(raw, validate=False).decode("utf-8", errors="replace")
        except Exception:  # binascii.Error / UnicodeDecodeError：解析层另有 fail-closed 分支
            return raw
    return node.value if isinstance(node.value, str) else None


def _scan_node_outcome_pass(node, anchors: dict, found: list, path: str = "$", _stack: set | None = None) -> None:
    """node 层扫描：mapping 键 `outcome` 的值节点标量 strip == pass ⇒ 记路径（v4.6 / r7-H1）。

    覆盖 constructed-data 扫描看不到的面：① 被 merge（`<<`）消费掉的内层映射（其键值不进
    constructed 结果）；② anchor 源节点本身（即使其值随后被同一 mapping 的显式 key 覆盖）。
    alias 由 composer 解析为同一节点对象（见 `_collect_anchors`），故形态自动覆盖；`_stack`
    防自指 anchor 造成的无限递归（含环 ⇒ 不展开已在本链上的节点）。
    """
    if _yaml_nodes is None or node is None:
        return
    if _stack is None:
        _stack = set()
    if id(node) in _stack:
        return
    _stack = _stack | {id(node)}
    if isinstance(node, _yaml_nodes.MappingNode):
        for i, (k, v) in enumerate(node.value):
            _ktext = _node_scalar_text(k)                       # v4.9：binary/编码键名同样归一化
            kname = _ktext if _ktext is not None else f"<key#{i}>"
            kp = f"{path}.{kname}"
            if _ktext is not None and _ktext == "outcome":
                _vtext = _node_scalar_text(v)
                if _vtext is None:
                    found.append((kp, "type"))
                elif _vtext.strip() == "pass":
                    found.append((kp, "pass"))
                elif _vtext.strip() not in _OUTCOMES:
                    found.append((kp, "enum"))
            _scan_node_outcome_pass(v, anchors, found, kp, _stack)
    elif isinstance(node, _yaml_nodes.SequenceNode):
        for i, v in enumerate(node.value):
            _scan_node_outcome_pass(v, anchors, found, f"{path}[{i}]", _stack)

_V2_REL = "_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md"
_LEDGER_BASENAME = "2026-08-28-G8-9-统一验收门底账.md"
_FULL_REF_RE = re.compile(r"^([^`\s]+?):(\d+)(?:-(\d+))?$")
_CONT_REF_RE = re.compile(r"^:(\d+)(?:-(\d+))?$")
_QUOTE_RE = re.compile(r"「([^」]+)」")
_QUOTE_REF_RE = re.compile(r"^（\s*`([^`\s]+?):(\d+)(?:-(\d+))?`")
_SEP_RE = re.compile(r"^\|[\s:\-|]+\|$")
_ID_RE = re.compile(r"(?:G\d+(?:-\w+)?|DEBT-\d+|R-[A-Z0-9]+)")
_SHA_RE = re.compile(r"^[0-9a-f]{8,40}$")
_EXPECT_CHAINS = ("检索链", "复习链", "部署链", "skill 链", "投影 freshness", "DLQ 链")
_EXPECT_OBJ = ("CI", "observability", "backup-restore", "benchmark", "dogfood")
_EXPECT_OWNERS = {
    "检索链": {"G4-3"},
    "复习链": {"G6-9"},
    "部署链": {"G2-8"},
    "skill 链": {"G5-7"},
    "投影 freshness": {"G8-2"},
    "DLQ 链": {"G8-3"},
    "CI": {"DEBT-1", "DEBT-4", "DEBT-5"},
    "observability": {"G8-10"},
    "backup-restore": {"G8-5", "R-J10"},
    "benchmark": {"R-SLO"},
    "dogfood": {"G8-6", "R-DOG"},
}
_PREVIEW_REL = "canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py"
_OUTCOMES = ("pass", "fail", "not_yet")
_OWNER_ALLOW_OUTSIDE = {"总账", "v2", "本表", "本车道", "未合主干", "P6-C", "P9-B", "P10-C"}
_WORD_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\-]*")
_COVERAGES = ("none", "partial", "complete")


def _block(lines: list[str]) -> list[str]:
    start = next((i for i, ln in enumerate(lines) if ln.startswith("### 2.13")), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return lines[start:end]


def _tables(block: list[str]) -> list[list[str]]:
    runs: list[list[str]] = []
    cur: list[str] = []
    for ln in block:
        if ln.startswith("|"):
            cur.append(ln)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def _data_rows(run: list[str]) -> list[str]:
    rows = [r for r in run if not _SEP_RE.match(r.strip())]
    return rows[1:] if rows else []


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _owner_scan_text(owner_cell: str) -> str:
    """owner cell → 白名单扫描文本（v4.4）。

    反引号只是装饰：**内容保留**（仅去反引号字符）后交 `_WORD_RE.findall` 分词，使藏在
    反引号内的伪 owner 也进入白名单扫描。两类反引号内容先整段剔除，因为它们各有专项检查：
    `path:line` 引用（v4.3 起按树根边界校验，见 `_check_refs`）；ID token（由允许集精确比对，
    §3 行同口径）。非反引号文本原样保留（与 v4.3 同）。
    """
    def _keep(m: re.Match[str]) -> str:
        tok = m.group(1)
        if _FULL_REF_RE.match(tok) or _CONT_REF_RE.match(tok) or _ID_RE.fullmatch(tok):
            return ""
        return tok
    return re.sub(r"`([^`]*)`", _keep, owner_cell)


def _owner_ids(owner_cell: str) -> set[str]:
    """owner cell → **独立 token** 的 ID 集（v4.6 / r6-M1）。

    只认「整段即 ID」的 token：反引号包裹的完整 ID，或反引号外的裸词 token。
    `path:line` 引用与任何含 ID **子串** 的文件名 / 路径 / 组合词都不贡献 ID——owner 语义要求
    owner 是独立 token，而不是恰好出现在证据文件名里的字符序列。
    """
    ids: set[str] = set()
    for tok in re.findall(r"`([^`]*)`", owner_cell):
        t = tok.strip()
        if _FULL_REF_RE.match(t) or _CONT_REF_RE.match(t) or "::" in t:
            continue
        if _ID_RE.fullmatch(t):
            ids.add(t)
    outside = re.sub(r"`[^`]*`", " ", owner_cell)
    for tok in _WORD_RE.findall(outside):
        if _ID_RE.fullmatch(tok):
            ids.add(tok)
    return ids


_ALNUM_TOKEN_RE = re.compile(r"^[0-9A-Za-z]+$")          # v4.9：不限长（超长畸形 token 不再逃逸）
# 反引号内出现的、**非 SHA** 的纯字母数字 token（底账既有 prose / 代码标识符）——白名单封闭：
# 新 token 要么必须可解引用为 commit，要么由授权改动加词进本表（并重送一轮复核）。
_ALNUM_NON_SHA_ALLOW = {
    "degraded",              # §2.13 露出面 / 缺口措辞里的裸词（非 SHA 形态）
    "unavailable",
    "renderBoardDoneResult", # 代码标识符（前端渲染函数名）
}
_EVIDENCE_TREE_PREFIX = "_bmad-output/"


def _check_provenance_tokens(root: Path, block_lines: list[str], failures: list[str], used: set) -> None:
    """§2.13 段「无行号 evidence 目录引用」+「平文 SHA provenance」核对（v4.6 / r5-M2）。

    - `_bmad-output/` 根的 evidence 路径（无 `:line`）：必须存在 ⇒ 否则 `ref-missing`；
      文件本身 / 目录内全部文件**逐文件进 digest**（内容绑定；目录被移走 / 内容被改 ⇒ 红或 digest 变）。
    - 平文 SHA：`^[0-9A-Za-z]+$` 的 token（白名单外）必须**既是 8–40 位小写 hex、又**可解引用为 commit
      ⇒ 否则 `sha-missing`（v4.9 起**不限长度上限**；短 / 超长 / 非 hex 畸形值一律红）；
      commit 的 tree OID 进 digest（↔ 换一个 commit 值 ⇒ digest 变，替换不再无痕）。
    - 其它形态（`path:line` / `:line` / nodeid `::` / ID / 其它散文 token）不属本项。
    - 白名单项在 §2.13 内 0 命中 ⇒ `token-allow-dead` 红（白名单必须最小、无死项）。
    """
    hit_allow: set = set()
    for tok in re.findall(r"`([^`]*)`", "\n".join(block_lines)):
        t = tok.strip()
        if not t or _FULL_REF_RE.match(t) or _CONT_REF_RE.match(t) or "::" in t or _ID_RE.fullmatch(t):
            continue
        if "/" in t:
            _p = Path(t)
            if _p.is_absolute():
                failures.append(f"ref-missing: 引用路径为绝对路径 {t}（越出树根）")
                continue
            if ".." in _p.parts:
                failures.append(f"ref-missing: 引用路径含 .. 段 {t}（越出树根）")
                continue
            _norm = posixpath.normpath(t)                       # `./`、`.//`、`a/./b`、重复斜杠统一归一
            if not (_norm == "_bmad-output" or _norm.startswith(_EVIDENCE_TREE_PREFIX)):
                # 产品树散文路径（frontend/ 等）：本项不覆盖（UAT §十.26 已声明边界）
                continue
            t = _norm
            rp, why = _resolve_under_root(root, t.rstrip("/"))
            if rp is None:
                failures.append(f"ref-missing: evidence 路径越界 {t}（{why}）")
                continue
            if not rp.exists():
                failures.append(f"ref-missing: evidence 引用不可解 {t}")
                continue
            rr = root.resolve()
            files = [rp] if rp.is_file() else sorted(p for p in rp.rglob("*") if p.is_file())
            for f in files:
                used.add((f.relative_to(rr).as_posix(), hashlib.sha256(f.read_bytes()).hexdigest()))
            continue
        if _ALNUM_TOKEN_RE.match(t):
            if t in _ALNUM_NON_SHA_ALLOW:
                hit_allow.add(t)
                continue
            if not _SHA_RE.fullmatch(t):                              # v4.7 / r8-M1：只认 immutable hex OID
                failures.append(
                    f"sha-missing: {t} (非 8–40 位小写 hex：平文 SHA provenance 只接受不可变 commit OID；"
                    "可变 ref（HEAD/main 等分支名）、短/超长 token 或畸形值一律红)"
                )
                continue
            r = _git(root, "rev-parse", "--verify", f"{t}^{{commit}}")
            full = r.stdout.strip()
            if r.returncode != 0 or not full:
                kind = "hex 形态" if _SHA_RE.fullmatch(t) else "非 hex 形态"
                failures.append(f"sha-missing: {t} ({kind} 平文 SHA provenance 不可解引用为 commit)")
                continue
            tr = _git(root, "rev-parse", f"{full}^{{tree}}")
            used.add((f"commit-tree:{full}", tr.stdout.strip() if tr.returncode == 0 else "?"))
            continue
    for tok in sorted(_ALNUM_NON_SHA_ALLOW):
        if tok not in hit_allow:
            failures.append(f"token-allow-dead: {tok} 白名单项在 §2.13 内 0 命中（白名单必须最小）")


_YAML_FENCE_RE = re.compile(r"^```(?:yaml|yml)\s*$", re.IGNORECASE)


def _yaml_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """提取全部 ```yaml / ```yml fenced block（大小写不敏感）→ [(内容首行行号(1-based), 内容行)]（v4.5）。

    info string 只认 yaml / yml（含大小写变体）；裸 ``` 与其它 info string（json 等）不在此列
    ——那是已声明边界（见 UAT「本卡未证明什么」）。
    """
    out: list[tuple[int, list[str]]] = []
    i = 0
    while i < len(lines):
        if _YAML_FENCE_RE.match(lines[i].strip()):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append((i + 2, lines[i + 1 : j]))
            i = j + 1
        else:
            i += 1
    return out


def _iter_key_values(node: object, key: str, path: str = "$") -> list[tuple[str, object]]:
    """递归遍历 safe_load 结果，收集全部「dict 键 == key」的 (JSON 路径, 值)（v4.5）。

    只认键名精确相等：`meta.outcome_states` 之类的枚举键不受影响。
    """
    found: list[tuple[str, object]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            ktxt = k if isinstance(k, str) else _scalar_text(k)   # v4.9：bytes 键名（!!binary）归一化
            kp = f"{path}.{ktxt}"
            if ktxt == key:
                found.append((kp, v))
            found.extend(_iter_key_values(v, key, kp))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found.extend(_iter_key_values(v, key, f"{path}[{i}]"))
    return found


def _resolve_under_root(root: Path, rel: str) -> tuple[Path | None, str | None]:
    """rel → (解析后绝对路径, None)；越界/非法 ⇒ (None, 原因)（v4.6：refs 与 nodeid 同口径，r5-M1）。

    拒绝：空 / 绝对路径 / 含 `..` 段 / resolve 后不在 root 内。
    """
    if not rel:
        return None, "空路径"
    p = Path(rel)
    if p.is_absolute():
        return None, "绝对路径"
    if ".." in p.parts:
        return None, "含 .. 段"
    try:
        rp = (root / p).resolve()
        rr = root.resolve()
    except OSError as exc:  # pragma: no cover
        return None, f"resolve 失败 {exc}"
    if not rp.is_relative_to(rr):
        return None, "越出树根"
    return rp, None


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60)


def _check_refs(root: Path, rows: list[str], table: str, failures: list[str], used: set[tuple[str, str]]) -> None:
    for i, row in enumerate(rows, 1):
        for cell in _cells(row):
            cur: str | None = None
            for tok in re.findall(r"`([^`]+)`", cell):
                m = _FULL_REF_RE.match(tok)
                cont = _CONT_REF_RE.match(tok)
                if m:
                    cur = m.group(1)
                    path, l1, l2 = m.group(1), m.group(2), m.group(3)
                elif cont and cur:
                    path, l1, l2 = cur, cont.group(1), cont.group(2)
                else:
                    continue
                src, why = _resolve_under_root(root, path)
                if src is None:
                    failures.append(f"ref-missing: {table}{i} 越出树根 {path}:{l1}（{why}）")
                    continue
                if not src.is_file():
                    failures.append(f"ref-missing: {table}{i} {path}:{l1}")
                    continue
                n = len(src.read_text(encoding="utf-8", errors="replace").splitlines())
                a, b = int(l1), int(l2 or l1)
                if a < 1 or b > n or a > b:
                    failures.append(f"ref-missing: {table}{i} {path}:{l1}")
                    continue
                used.add((path, hashlib.sha256(src.read_bytes()).hexdigest()))


def _check_quotes(root: Path, rows: list[str], failures: list[str]) -> None:
    for i, row in enumerate(rows, 1):
        cols = _cells(row)
        quote_cell = cols[3] if len(cols) > 3 else ""
        for m in _QUOTE_RE.finditer(quote_cell):
            q = m.group(1)
            if len(q) < 24:
                failures.append(f"quote-miss: row{i} (文句过短)")
                continue
            ref = _QUOTE_REF_RE.match(quote_cell[m.end() :])
            if ref is None:
                failures.append(f"quote-miss: row{i} (无紧邻出处)")
                continue
            if _LEDGER_BASENAME in ref.group(1):
                failures.append(f"quote-miss: row{i} (出处为底账自身)")
                continue
            src = root / ref.group(1)
            if not src.is_file():
                failures.append(f"quote-miss: row{i} (出处不可解: {ref.group(1)})")
                continue
            lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
            a, b = int(ref.group(2)), int(ref.group(3) or ref.group(2))
            if a < 1 or b > len(lines) or not any(q in ln for ln in lines[a - 1 : b]):
                failures.append(f"quote-miss: row{i}")


def _check_nodeids(root: Path, rows: list[str], table: str, failures: list[str], used: set[tuple[str, str]]) -> None:
    for i, row in enumerate(rows, 1):
        cols = _cells(row)
        chain = cols[0] if cols else ""
        mech_cell = cols[4] if len(cols) > 4 else ""
        found = 0
        for cell in _cells(row):
            cur: str | None = None
            for tok in re.findall(r"`([^`]+)`", cell):
                if ".py::" in tok and not tok.startswith("::"):
                    cur = tok.split("::", 1)[0]
                    names = tok.split("::")[1:]
                elif tok.startswith("::") and cur:
                    names = tok[2:].split("::")
                else:
                    continue
                found += 1
                if not names or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _n) for _n in names):
                    failures.append(f"nodeid-missing: {table}{i} 空/非法测试名 {tok!r}")
                    continue
                src_path, why = _resolve_under_root(root, cur)
                if src_path is None:
                    failures.append(f"nodeid-missing: {table}{i} 路径越界 {cur}（{why}）")
                    continue
                try:
                    rel_norm = src_path.relative_to(root.resolve()).as_posix()
                except ValueError:  # pragma: no cover - _resolve_under_root 已保证在 root 内
                    rel_norm = cur
                if not rel_norm.startswith("backend/tests/"):
                    failures.append(f"nodeid-missing: {table}{i} 非测试路径 {cur}")
                    continue
                if not src_path.is_file():
                    failures.append(f"nodeid-missing: {table}{i} {cur}")
                    continue
                text = src_path.read_text(encoding="utf-8", errors="replace")
                for name in names:
                    if not re.search(rf"(def|class) {re.escape(name)}\b", text):
                        failures.append(f"nodeid-missing: {table}{i} {cur}::{name}")
                used.add((rel_norm, hashlib.sha256(src_path.read_bytes()).hexdigest()))
        if table == "row" and chain != "skill 链" and ".py::" not in mech_cell:
            failures.append(f"nodeid-missing: row{i} 机械判据缺 nodeid（.py::）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--expect-digest", required=True)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    ledger_path = Path(args.ledger).resolve()
    lines = ledger_path.read_text(encoding="utf-8").split("\n")
    block = _block(lines)
    tables = _tables(block)
    chain_rows = _data_rows(tables[0]) if tables else []
    obj_rows = _data_rows(tables[1]) if len(tables) > 1 else []
    failures: list[str] = []
    used: set[tuple[str, str]] = set()
    if len(chain_rows) < 6:
        failures.append(f"chains<6: {len(chain_rows)}")
    elif len(chain_rows) > 6:
        failures.append(f"chains-extra: {len(chain_rows)}")
    if len(obj_rows) != 5:
        failures.append(f"obj07!=5: {len(obj_rows)}")
    chain_names = {_cells(r)[0] for r in chain_rows if _cells(r)}
    missing = [n for n in _EXPECT_CHAINS if n not in chain_names]
    if missing or len(chain_names) != 6:
        failures.append(f"chain-missing: {missing or sorted(chain_names)}")
    obj_names = {_cells(r)[0] for r in obj_rows if _cells(r)}
    if obj_names != set(_EXPECT_OBJ):
        failures.append(f"obj-set: {sorted(obj_names)}")
    _check_refs(root, chain_rows, "row", failures, used)
    _check_refs(root, obj_rows, "obj", failures, used)
    _check_quotes(root, chain_rows, failures)
    _check_nodeids(root, chain_rows, "row", failures, used)
    _check_nodeids(root, obj_rows, "obj", failures, used)
    _check_provenance_tokens(root, block, failures, used)
    v2_lines = (root / _V2_REL).read_text(encoding="utf-8").splitlines() if (root / _V2_REL).is_file() else []
    v2_txt = "\n".join(v2_lines)
    sec5 = v2_txt[v2_txt.find("## 五"):] if "## 五" in v2_txt else ""
    for i, r in enumerate(chain_rows, 1):
        cols = _cells(r)
        chain = cols[0] if cols else ""
        owner_cell = cols[1] if len(cols) > 1 else ""
        ids = _owner_ids(owner_cell)
        allowed = _EXPECT_OWNERS.get(chain, set())
        if not ids:
            failures.append(f"owner-missing: row{i} ({chain}) 非空 ID 缺失")
        if ids != allowed:
            failures.append(f"owner-invalid: row{i} ({chain}) 实见={sorted(ids)} 允许={sorted(allowed)}")
        for _tok in _WORD_RE.findall(_owner_scan_text(owner_cell)):
            if _tok not in _OWNER_ALLOW_OUTSIDE:
                failures.append(f"owner-invalid: row{i} ({chain}) 非白名单描述词 {_tok!r}")
        for tok in ids:
            if f"#### {tok} " not in v2_txt:
                failures.append(f"owner-invalid: {tok} 无 #### 档案节")
            elif re.search(rf"^\| {re.escape(tok)} ", sec5, re.M):
                failures.append(f"owner-invalid: {tok} 在 §五 DONE")
    for i, r in enumerate(obj_rows, 1):
        cols = _cells(r)
        item = cols[0] if cols else ""
        owner_cell = cols[1] if len(cols) > 1 else ""
        ids = _owner_ids(owner_cell)
        allowed = _EXPECT_OWNERS.get(item, set())
        if not ids:
            failures.append(f"owner-missing: obj{i} ({item}) 非空 ID 缺失")
        if ids != allowed:
            failures.append(f"owner-invalid: obj{i} ({item}) 实见={sorted(ids)} 允许={sorted(allowed)}")
        for _tok in _WORD_RE.findall(_owner_scan_text(owner_cell)):
            if _tok not in _OWNER_ALLOW_OUTSIDE:
                failures.append(f"owner-invalid: obj{i} ({item}) 非白名单描述词 {_tok!r}")
        for tok in ids:
            if f"#### {tok} " not in v2_txt:
                failures.append(f"owner-invalid: {tok} 无 #### 档案节")
            elif re.search(rf"^\| {re.escape(tok)} ", sec5, re.M):
                failures.append(f"owner-invalid: {tok} 在 §五 DONE")
    for i, row in enumerate(chain_rows, 1):
        cols = _cells(row)
        chain = cols[0] if cols else ""
        expose = cols[2] if len(cols) > 2 else ""
        quote_cell = cols[3] if len(cols) > 3 else ""
        gap = cols[6] if len(cols) > 6 else ""
        if expose.startswith("**无**"):
            if chain != "skill 链":
                failures.append(f"ref-missing: row{i} 仅 skill 链可用「露出=无」分支")
                continue
            refs = re.findall(r"`([^`\s]+?):(\d+)(?:-(\d+))?`", row)
            if _PREVIEW_REL not in [p for p, _a, _b in refs]:
                failures.append(f"ref-missing: row{i} 露出=无 行缺 preview 文件引用")
                continue
            src = root / _PREVIEW_REL
            hits = sum(1 for ln in src.read_text(encoding="utf-8", errors="replace").splitlines() if "degraded" in ln or "unavailable" in ln)
            if hits != 0:
                failures.append(f"expose-overclaim: row{i} preview 命中 {hits}（声称 0）")
            if not any(_V2_REL in p for p, _a, _b in refs):
                failures.append(f"ref-missing: row{i} 缺口行缺总账 v2 行引用")
            continue
        if not _QUOTE_RE.search(quote_cell):
            failures.append(f"quote-miss: row{i}")
        if gap.strip() not in ("—", "-", ""):
            if not any(_V2_REL in p for p, _a, _b in re.findall(r"`([^`\s]+?):(\d+)(?:-(\d+))?`", row)):
                failures.append(f"ref-missing: row{i} 缺口行缺总账 v2 行引用")
    yaml_line = next((ln for ln in lines if "dim: observability" in ln), "")
    my = re.search(r"outcome:\s*(\w+)", yaml_line)
    myc = re.search(r"coverage:\s*(\w+)", yaml_line)
    summary = next((ln for ln in block if "outcome=" in ln and "coverage=" in ln), "")
    ms = re.search(r"outcome=\s*(\w+)", summary)
    msc = re.search(r"coverage=\s*(\w+)", summary)
    if not (my and ms) or my.group(1) != ms.group(1):
        failures.append(f"yaml-mismatch: yaml={my.group(1) if my else None} summary={ms.group(1) if ms else None}")
    if my and my.group(1) not in _OUTCOMES:
        failures.append(f"outcome-enum: {my.group(1)}")
    if myc and myc.group(1) not in _COVERAGES:
        failures.append(f"coverage-enum: {myc.group(1)}")
    if not (myc and msc) or (myc and msc and myc.group(1) != msc.group(1)):
        failures.append(f"coverage-mismatch: yaml={myc.group(1) if myc else None} summary={msc.group(1) if msc else None}")
    _scan = "\n".join(re.sub(r"`[^`]*`", "", _ln) for _ln in lines)
    if re.search(r"""outcome[:=]\s*["']?pass""", _scan):
        failures.append("pass-unsupported: 本脚本只做记录一致性核对；§1 的 pass 认证需 candidate 树证据与主 session 裁定，机械门拒绝自证（全底账 any-line 扫描）")
    # ---- v4.5：```yaml fenced block 真解析（pass 认证的机械判据）----
    if yaml is None:
        failures.append("yaml-missing: PyYAML 不可用（真解析要求 import yaml 成功；禁静默回退正则）")
    else:
        yblocks = _yaml_blocks(lines)
        if not yblocks:
            failures.append("yaml-blocks: 底账内 0 个 ```yaml fenced block（结构缺失 ⇒ 红）")
        for _start, _body in yblocks:
            _txt = "\n".join(_body)
            # ① node 层扫描（anchor 源 / 被 merge 消费的内层映射）——先于构造，保证重复 key 块也能扫到
            try:
                _docs = list(yaml.compose_all(_txt, Loader=StrictSafeLoader))
            except yaml.YAMLError as _exc:
                failures.append(f"yaml-parse-error: block@{_start} {type(_exc).__name__}")
                _docs = []
            for _doc in _docs:
                _anchors: dict = {}
                _collect_anchors(_doc, _anchors)
                _nodes_found: list = []
                _scan_node_outcome_pass(_doc, _anchors, _nodes_found)
                for _jpath, _kind in _nodes_found:
                    if _kind == "pass":
                        failures.append(
                            f"pass-unsupported: {_jpath}@{_start} node 层（anchor/merge 源扫描）"
                            "——§1 的 pass 认证需 candidate 树证据与主 session 裁定，机械门拒绝自证"
                        )
                    elif _kind == "type":
                        failures.append(f"outcome-type: {_jpath}@{_start} node 层非标量 outcome 值（fail-closed 红）")
                    else:
                        failures.append(
                            f"outcome-enum: {_jpath}@{_start} node 层值不在 {list(_OUTCOMES)}（fail-closed 红）"
                        )
            # ② constructed-data 扫描（StrictSafeLoader：重复显式 key ⇒ yaml-duplicate-key 红）
            try:
                _parsed = yaml.load(_txt, Loader=StrictSafeLoader)
            except yaml.YAMLError as _exc:
                _msg = str(_exc).strip()
                _problem = getattr(_exc, "problem", None) or (_msg.splitlines()[-1] if _msg else type(_exc).__name__)
                if "duplicate key" in _msg:
                    failures.append(f"yaml-duplicate-key: block@{_start} {_problem}")
                else:
                    failures.append(f"yaml-parse-error: block@{_start} {type(_exc).__name__}: {_problem}")
                continue
            for _jpath, _val in _iter_key_values(_parsed, "outcome"):
                _txt = _scalar_text(_val)                            # v4.7：str / bytes / bytearray 归一化
                if _txt is None:
                    failures.append(
                        f"outcome-type: {_jpath}@{_start} 值类型 {type(_val).__name__}（非字符串标量 ⇒ fail-closed 红）"
                    )
                elif _txt.strip() == "pass":                          # strip = block scalar（> / |）尾换行归一化
                    failures.append(f"pass-unsupported: {_jpath}@{_start} 解析值=pass（真 YAML 解析）——§1 的 pass 认证需 candidate 树证据与主 session 裁定，机械门拒绝自证")
                elif _txt.strip() not in _OUTCOMES:
                    failures.append(f"outcome-enum: {_jpath}@{_start} 值 {_txt.strip()!r} 不在 {list(_OUTCOMES)}（fail-closed 红）")
    if "预留行" in yaml_line:
        failures.append("yaml-note-reserved: dim: observability 行仍含「预留行」")
    try:
        _led_rel = str(ledger_path.relative_to(root))
    except ValueError:
        _led_rel = str(ledger_path)
    used.add((_led_rel, hashlib.sha256(ledger_path.read_bytes()).hexdigest()))
    used.add(("check_g810_refs.py", hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    _porcelain = [_l for _l in _git(root, "status", "--porcelain").stdout.splitlines() if _l.strip()]
    dirty = len(_porcelain)
    dirty_untracked = len([_l for _l in _porcelain if _l.startswith("??")])
    dirty_tracked = dirty - dirty_untracked
    digest = hashlib.sha256("|".join(f"{p}:{h}" for p, h in sorted(used)).encode("utf-8") + f"|HEAD:{head}".encode()).hexdigest()[:32]
    if args.expect_digest != digest:
        failures.append(f"digest-drift: expect={args.expect_digest} actual={digest}")
    for fd in failures:
        print(fd)
    print(
        f"chains={len(chain_rows)} obj07={len(obj_rows)} failures={len(failures)} "
        f"source_digest={digest} expect_digest={args.expect_digest} head={head} "
        f"dirty={dirty} dirty_tracked={dirty_tracked} dirty_untracked={dirty_untracked}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
