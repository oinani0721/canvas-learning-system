#!/usr/bin/env python3
"""CARD-G3-8 — 把旧 ``next_review`` 对账到 frontmatter ``fsrs_due`` 真相源.

[BATCH-2026-09-18-第十五批 / CARD-G3-8]

**为什么需要对账**: 同一个 concept 的「下次复习时间」在系统里由**三个互不相同
的公式**各自算了一份, D0 T1 裁定 frontmatter 为唯一真相源之后, 旧值从未对过账::

    ① frontmatter fsrs_due          —— FSRS 真相源 (整秒 UTC-Z)
       vault 侧 FSRS 桥脚本 —— 逐条来源见 census 文档 §一 表格 ①
    ② Neo4j LEARNED 边 固定 +1 天   —— 与 FSRS 调度完全无关
       app/clients/neo4j_client.py:1034  r.next_review = datetime() + duration('P1D')
       app/services/fallback_sync_service.py:774        (重放侧同式)
       app/clients/neo4j_client.py:718                  (JSON 镜像同式)
    ③ last_interaction_ts + stability 天 —— 派生式, 不落盘
       app/services/learning_context_service.py:96-102

本迁移器把 ① 的值对账进 ②。③ 是读时派生, 不在写入面。

**本迁移器绝不做的事** (硬边界):

* **永不写 frontmatter** —— 它是真相源, 反向回填是用户裁定项, 默认不做;
* **永不写 backend/data/fsrs_card_states.json** —— G3-7 已把它降为投影缓存,
  本脚本只在报告里列它的 ``due`` 与 ``fsrs_due`` 的分歧计数 (``--card-states-file``);
* **永不连现网库** —— 端口闸按**解析后的端口**拒 7691 / 7687 (不是子串匹配);
* **永不写 live vault 子树 / 主仓 JSON 镜像** —— inode 身份 + 路径包含双闸。

设计参照 (DD-04): 备份/校验/还原/互斥模式组抄
``scripts/migrate_fsrs_card_states_vault_key_g35.py:104-160,350-520,577-660``;
现网端口与 store identity 双闸抄 ``scripts/migrate_write_identity_g23.py:52-118``;
frontmatter 字段正则与整秒归一口径抄 ``app/services/review_service.py:146-163``
(该处又与 vault 侧 FSRS 桥脚本 / ``scripts/daily_review_pick.py:341`` 同款;
逐条 file:line 见 census 文档 `_bmad-output/审查/evidence-g38/next_review-census.md` §一)。

用法::

    # 只读只报 (除 --out 外零写入)
    python scripts/migrate_next_review_g38.py --dry-run \\
        --vault-dir /tmp/vault-copy --group-id vault__cs_61b \\
        --json-file /tmp/neo4j_memory.copy.json --out /tmp/g38-report.json

    # 实际对账 (双备份 + pre-image + 写完读回 + 失败还原)
    python scripts/migrate_next_review_g38.py --apply \\
        --vault-dir /tmp/vault-copy --group-id vault__cs_61b \\
        --neo4j-uri bolt://127.0.0.1:7692 --backup-dir /tmp/g38-bak \\
        --out /tmp/g38-apply.json

    # 回滚 (从 pre-image / .bak 逐条还原并读回校验)
    python scripts/migrate_next_review_g38.py --rollback /tmp/g38-bak/preimage-<ts>.json \\
        --group-id vault__cs_61b --json-file /tmp/neo4j_memory.copy.json

**退出码约定** (与 g35 :30-38 同口径, 1 与 3 必须分得开)::

    0  成功 (含 "无可写行" 的幂等路径)
    1  未写入或**已回滚到备份** —— 目标处于迁移前的可信状态
    2  参数 / 闸拒绝 (组 id 形态非法、目标是现网、--out 与目标同一文件、输入读不出)
    3  **回滚也失败** —— 目标可能半写, 备份路径在 stderr 里, 需人工处置
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlsplit

# ── 现网闸常量 ──────────────────────────────────────────────────────────────
#: 主仓 —— 现网运行时读写的那一棵树。
LIVE_REPO_ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system")
#: live vault —— 落在它下面的**写入**一概拒绝 (部署铁律)。只读扫描不过这道闸。
LIVE_VAULT_DIR = LIVE_REPO_ROOT / "canvas-vault"
#: 主仓 JSON 镜像 —— ``neo4j_client.DEFAULT_STORAGE_PATH`` (:54) 指向的那一份。
LIVE_JSON_MIRROR = LIVE_REPO_ROOT / "backend" / "data" / "neo4j_memory.json"
#: FSRS 投影缓存 —— 本脚本**只读**它做分歧计数, 任何写入目标落在它上面都拒。
LIVE_CARD_STATES = LIVE_REPO_ROOT / "backend" / "data" / "fsrs_card_states.json"

#: 现网库端口。7691 = 现网 Neo4j; 7687 = 驱动默认端口 (本机现网开发库也监听它)。
#: ⚠️ 判据是 ``urlsplit`` **解析后的整数端口**, 不是子串 —— ``:07691`` 与
#: ``:7691`` 是同一个端口的两种写法, 子串判据只拦得住后者。
LIVE_DB_PORTS = frozenset({7691, 7687})

#: 可判定去向的 bolt/neo4j scheme。其余 scheme 无法判断落到哪 ⇒ fail-closed 拒。
ALLOWED_URI_SCHEMES = frozenset({"bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"})

#: 现网 (7691) 的 store identity 指纹 —— 抄 g23 :106-108 实测值。端口闸挡不住
#: 端口转发, 指纹闸挡不住库重建; 两道闸各自覆盖对方的盲区。可用环境变量覆盖。
KNOWN_LIVE_STORE_IDENTITY = (
    "C43B910072C97DA5907C9687316EBBCA7F05731C606638B4689AB43B5BC39759::neo4j::2026-05-06T16:44:07.865Z"
)

#: 节点 ``.md`` 的目录约定 —— 与 ``app/services/frontmatter_signals.py:30``
#: ``_NODE_DIR_PREFIXES`` 同序 (节点/ 优先, 退 原白板/)。⛔ 不另立目录约定 (D0 T3)。
NODE_DIR_PREFIXES: Tuple[str, ...] = ("节点", "原白板")

# ── frontmatter 解析 (与生产 reader 逐字同口径) ─────────────────────────────
#: 只在 frontmatter **块内**取字段 —— 作用在整份 .md 上会把正文里顶格的
#: ``fsrs_due:`` 当成权威 due (review_service.py:309-311 同款说明)。
_FM_BLOCK_RE = re.compile("^\\ufeff?" + r"---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.S)
#: 字段正则 —— review_service.py:156 / vault 侧 FSRS 桥脚本 / daily_review_pick.py:341
#: 三处逐字相同。特意不走 PyYAML: live frontmatter 的 fsrs_due 未加引号, PyYAML 的
#: timestamp resolver 会解析成 datetime, 而整条复习投影链按 UTC-Z **字符串**比较。
_FM_FIELD_RE = r'^{key}:\s*"?([^"\n]+?)"?\s*$'
#: 形态门禁 + 解析 —— review_service.py:159-160 同口径。
_FM_DUE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_FM_DUE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

#: 物理格式组 id (``vault__<id>``, 双下划线)。⛔ 本脚本**不自造拼接**组 id
#: (G4-5 P1 地盘), 只校验调用方给的形态 —— 传错组是跨 vault 写的唯一入口。
_GROUP_ID_RE = re.compile(r"^vault__[A-Za-z0-9][A-Za-z0-9_\-]*$")

#: vault 自报身份的配置文件 (round-11 扁平架构固化: Skill 一律从它读 vault_id)。
_VAULT_CONFIG_NAME = ".canvas-config.yaml"
#: 只取 ``vault_id`` 一个字段 —— 纯 stdlib, 不引 PyYAML (与 frontmatter 读法同策)。
_VAULT_ID_RE = re.compile(r'^vault_id:\s*"?([^"\n#]+?)"?\s*(?:#.*)?$', re.M)
#: 能由本脚本自行物理化的 vault_id 形态。非该形态 (如中文 vault 名需 punycode)
#: 本脚本**算不出**物理组名 —— 算不出就不能假装验过, 按 fail-closed 处理。
#: ⚠️ 额外排除含 ``__`` 的 vault_id (Codex r2 BLOCKER-1): ``__`` 同时是 vault 内
#: 二级作用域的分隔符, 于是 ``vault__alpha__beta`` 既可能是 vault ``alpha`` 的
#: ``beta`` 板, 也可能是 vault ``alpha__beta`` 的根组 —— 单看字符串**分不开**。
_PLAIN_VAULT_ID_RE = re.compile(r"^(?!.*__)[A-Za-z0-9][A-Za-z0-9_\-]*$")
#: 二级作用域名同样禁止内嵌 ``__``, 否则同一个歧义在下一层复发。
_GROUP_SCOPE_RE = re.compile(r"^(?!.*__)[A-Za-z0-9][A-Za-z0-9_\-]*$")

#: ISO 小数秒归一 —— Neo4j ``toString(datetime)`` 给到纳秒 (9 位),
#: ``datetime.fromisoformat`` 只收 3 / 6 位。
_ISO_FRACTION_RE = re.compile(r"(\.\d{1,9})")

COUNT_KEYS: Tuple[str, ...] = (
    "rows_without_target",
    "governed",
    "ungoverned",
    "matched",
    "unmatched",
    "unmatched_no_target",
    "unmatched_no_frontmatter",
    "noop",
    "set",
    "backfill",
    "ambiguous",
    "malformed_fsrs_due",
)

RC_OK = 0
RC_NOT_WRITTEN = 1
RC_REFUSED = 2
RC_ROLLBACK_FAILED = 3

#: 写 UTC-Z (tz-aware) 进 JSON 镜像的**已知下游后果** —— 见 :func:`_json_mirror_warning`。
WARN_JSON_MIRROR_AWARE_READER = "W-JSON-MIRROR-AWARE-READER"


# ═══════════════════════════════════════════════════════════════════════════
# 路径 / 身份工具 (抄 g35 :66-101)
# ═══════════════════════════════════════════════════════════════════════════
def _resolved(path: Path) -> Path:
    """真实路径 —— 消解符号链接、``..`` 回绕与相对路径。

    ⚠️ 它只解析路径, **不是文件身份**: 同一份文件的硬链接有不同的 resolved 路径
    却是同一个 inode, 纯路径比对会放行它。文件身份判据见 :func:`_identity`。
    """
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def _identity(path: Path) -> Optional[Tuple[int, int]]:
    """文件身份 = ``(st_dev, st_ino)``; 不存在的文件没有身份 (返回 None)。"""
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_dev, st.st_ino)


def _protected_identities() -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for p in (LIVE_JSON_MIRROR, LIVE_CARD_STATES):
        ident = _identity(p)
        if ident is not None:
            out.append(ident)
    return out


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ═══════════════════════════════════════════════════════════════════════════
# 现网闸 —— 路径面 + 库面的**单一入口**
# ═══════════════════════════════════════════════════════════════════════════
def _path_refusal(target: Path, what: str) -> Optional[str]:
    """路径面: inode 身份 + 路径包含 + 多名字 三道判据 (抄 g35 :104-155)。"""
    resolved = _resolved(target)

    ident = _identity(target)
    if ident is not None and ident in _protected_identities():
        return (
            f"{what} {resolved} 与**主仓现网**文件是同一个文件 (dev/inode {ident}, "
            "硬链接或同路径) — 本卡硬边界禁改它。请 cp 到临时目录后指向副本。"
        )

    for guarded in (LIVE_JSON_MIRROR, LIVE_CARD_STATES):
        if resolved == _resolved(guarded):
            return f"{what} {resolved} 是**主仓现网**文件 — 本卡硬边界禁改它。请指向临时副本。"

    live_vault = _resolved(LIVE_VAULT_DIR)
    if resolved == live_vault or live_vault in resolved.parents:
        return f"{what} {resolved} 落在 live vault ({live_vault}) 内 — 写它会触发部署铁律, 拒绝执行。"

    if resolved.exists() and not resolved.is_file():
        return f"{what} {resolved} 不是普通文件, 拒绝执行。"

    # 多名字判据 (g35 :140-155): 受保护 inode 集只收得进**已知**的那几个文件;
    # 已存在的写入目标若 st_nlink > 1, 它还有别的名字, 而我们无法证明另一个名字
    # 不在受保护区 —— 拒绝, 而不是带着不确定去截断。正常临时副本 nlink == 1。
    try:
        nlink = target.stat().st_nlink
    except OSError:
        nlink = 1
    if nlink > 1:
        return (
            f"{what} {resolved} 的硬链接数为 {nlink} — 它在文件系统里还有别的名字, "
            "无法证明另一个名字不在 live vault / 现网面内。请指向一个独占的普通文件。"
        )
    return None


def _uri_refusal(uri: str, what: str) -> Optional[str]:
    """库面: 按**解析后的端口**判现网, 不是子串匹配 (抄 g23 :57-75)。

    子串 ``":7691" in uri`` 会被等价写法绕过 (``:07691`` 数值同端口、URL 编码、
    大小写主机名)。解析失败 / 无显式端口 / 未知 scheme 一律按"是现网"处理
    (fail-closed: 拿不准就拒绝)。
    """
    try:
        parsed = urlsplit(uri)
    except ValueError as exc:
        return f"{what} {uri!r} 无法解析为 URI ({exc}) — 拿不准去向, 拒绝。"

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_URI_SCHEMES:
        return (
            f"{what} {uri!r} 的 scheme {scheme!r} 不在可判定清单 "
            f"{sorted(ALLOWED_URI_SCHEMES)} 内 — 无法判断它落到哪个库, 拒绝。"
        )

    try:
        port = parsed.port
    except ValueError as exc:
        return f"{what} {uri!r} 的端口非法 ({exc}) — 拒绝。"

    if port is None:
        return (
            f"{what} {uri!r} 未显式指定端口 — 驱动会走默认 7687, 而 7687 在现网端口集 "
            f"{sorted(LIVE_DB_PORTS)} 内, 拒绝。请写明非现网端口。"
        )
    if port in LIVE_DB_PORTS:
        return (
            f"{what} {uri!r} 解析后的端口是 {port}, 落在现网端口集 {sorted(LIVE_DB_PORTS)} 内 — 本卡禁连现网库, 拒绝。"
        )
    return None


def assert_target_is_not_live(
    target: Optional[Path] = None,
    uri: Optional[str] = None,
    what: str = "写入目标",
) -> Optional[str]:
    """现网闸的**单一入口** —— 路径面与库面都从这里走.

    做成单一入口而不是两个平行函数, 是为了让"闸恒放行"这一类负控输入能一次性
    把**全部**闸用例 (live 子树 / 硬链接 / 7691 / :07691 / 省略端口) 打红; 两个
    平行函数会让负控只覆盖其中一半, 另一半仍绿 = 门未覆盖的路径。

    Returns:
        None 表示放行; 非 None 为拒绝原因字符串。
    """
    if uri is not None:
        refusal = _uri_refusal(uri, what)
        if refusal is not None:
            return refusal
    if target is not None:
        refusal = _path_refusal(Path(target), what)
        if refusal is not None:
            return refusal
    return None


def read_vault_id(vault_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """从 ``<vault>/.canvas-config.yaml`` 读 vault 自报的 ``vault_id``。

    Returns: ``(vault_id, 读不到的原因)``; 两者恰有一个为 None。
    """
    cfg = vault_dir / _VAULT_CONFIG_NAME
    try:
        text = cfg.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"{cfg} 读不出 ({type(exc).__name__}: {exc})"
    m = _VAULT_ID_RE.search(text)
    if not m or not m.group(1).strip():
        return None, f"{cfg} 里没有 vault_id 字段"
    return m.group(1).strip(), None


def assert_group_matches_vault(
    vault_dir: Path,
    group_id: str,
    *,
    scope: Optional[str],
    allow_unbound: bool,
) -> Optional[str]:
    """把 ``--group-id`` 绑到 ``--vault-dir`` **自报**的身份上 (Codex r1 BLOCKER-1).

    形态校验只能证明 ``--group-id`` 长得像个物理组名, **证明不了它属于这个
    vault**: ``--vault-dir A --group-id vault__B`` 两个参数各自都合法, 合起来却把
    A 的 ``fsrs_due`` 写进 B 的边。传错组是跨 vault 写的唯一入口, 所以这里要求
    vault 自己说出它是谁, 再与调用方给的组名对表。

    判据: ``group_id`` 必须**逐字等于** ``vault__<vault_id>``; 要写 vault 内的二级
    作用域 (D16 的白板级 / 学科级) 必须显式给 ``--group-scope <name>``, 届时判据
    变成逐字等于 ``vault__<vault_id>__<name>``。

    ⚠️ **为什么不能用前缀放行** (Codex r2 BLOCKER-1): ``__`` 既是 ``vault__`` 的
    分隔符, 又是二级作用域的分隔符。若按 ``startswith(vault__<id>__)`` 放行, 那么
    vault ``alpha`` 拿着 ``--group-id vault__alpha__beta`` 会被当成"A 的 beta 板"
    放行 —— 而它同时**也是** vault ``alpha__beta`` 的根组名。单看字符串这两者分不开,
    于是逃生门一次都不用开, A 的 due 就落进了 B。逐字相等 + 显式 ``--group-scope``
    把"我要写哪一层"从推断变成声明。

    ⚠️ **算不出就不放行**: 本脚本不引 app (零 app 导入), 因此无法复用生产的
    ``to_physical_group_id()`` 的 punycode 物理化。若 ``vault_id`` 不是纯
    ``[A-Za-z0-9_-]`` 形态 (如中文 vault 名), 本闸**算不出**它的物理组名 ——
    这种情况按 fail-closed 拒绝, 要放行必须显式 ``--allow-unbound-vault``,
    而不是默默当成"验过了"。
    """
    if scope is not None and not _GROUP_SCOPE_RE.fullmatch(scope):
        return (
            f"--group-scope {scope!r} 形态非法 (须 [A-Za-z0-9] 开头, 且**不得内嵌 __**"
            " —— 内嵌 __ 会让同一个歧义在下一层复发)。"
        )
    vault_id, err = read_vault_id(vault_dir)
    if vault_id is None:
        if allow_unbound:
            return None
        return (
            f"无法确认 --vault-dir {vault_dir} 的身份: {err}。"
            " 拿不准这个目录属于哪个 vault 就不能往某个组里写 —— 拒绝执行。"
            " 确知配对正确时可显式加 --allow-unbound-vault。"
        )
    if not _PLAIN_VAULT_ID_RE.fullmatch(vault_id):
        if allow_unbound:
            return None
        return (
            f"--vault-dir 自报的 vault_id {vault_id!r} 本脚本算不出确定的物理组名"
            " (非纯 ASCII 时物理化含 punycode, 属 app 侧能力, 本脚本零 app 导入;"
            " 内嵌 __ 时它与二级作用域分隔符撞车, 单看字符串分不开是哪一层)。"
            " 算不出就不能假装验过 —— 拒绝执行。确知配对正确时可显式加 --allow-unbound-vault。"
        )
    expected = f"vault__{vault_id}" if scope is None else f"vault__{vault_id}__{scope}"
    if group_id == expected:
        return None
    hint = "" if scope is not None else " 要写 vault 内的二级作用域请显式给 --group-scope。"
    return (
        f"--group-id {group_id!r} 与 --vault-dir 自报的 vault_id {vault_id!r} 不匹配"
        f" (应逐字等于 {expected!r})。{hint}"
        " 这正是把 A vault 的 due 写进 B vault 的那条路径, 拒绝执行。"
    )


def assert_write_path_is_safe(
    path: Optional[Path],
    *,
    vault_dir: Optional[Path],
    read_inputs: Sequence[Path],
    label: str,
) -> Optional[str]:
    """**所有**写入路径的统一闸 (Codex r1 HIGH-2).

    此前只有 ``--out`` 与写入目标过闸, 于是 ``--dry-run --out <vault>/节点/A.md``
    会把报告覆盖到源节点上 —— frontmatter 是真相源, 它是本脚本最不该写的东西。
    备份/pre-image 同理 (它们也是写入路径, 且可以是指向只读输入的符号链接)。

    三道判据:
      1. 现网闸 (:func:`assert_target_is_not_live`);
      2. **不得落在 ``--vault-dir`` 子树内** —— 整个子树是只读输入面, 覆盖整棵树
         比逐个列举扫到的 ``.md`` 更宽 (没被扫到的文件同样不该被写);
      3. 不得与任何只读输入是同一个文件 (路径相同或 inode 相同)。
    """
    if path is None:
        return None
    refusal = assert_target_is_not_live(target=path, what=label)
    if refusal is not None:
        return refusal
    resolved = _resolved(path)
    if vault_dir is not None:
        vd = _resolved(vault_dir)
        if resolved == vd or vd in resolved.parents:
            return f"{label} {resolved} 落在 --vault-dir ({vd}) 子树内 —— 那是**只读**输入面, 拒绝写入。"
    ident = _identity(path)
    for other in read_inputs:
        if _resolved(other) == resolved or (ident is not None and _identity(other) == ident):
            return f"{label} {resolved} 与只读输入 {other} 是同一个文件, 拒绝写入。"
    return None


def assert_write_dir_is_safe(
    path: Optional[Path],
    *,
    vault_dir: Optional[Path],
    label: str,
) -> Optional[str]:
    """写入**目录**的闸 (Codex r2 MEDIUM-6).

    不能复用 :func:`assert_write_path_is_safe` —— 它内含"已存在且不是普通文件就拒"
    的判据, 而备份目录第二次跑时**本来就应该已经存在**。那条判据会把正常的第二次
    apply 拒在门外, 并让幂等负控提前红在 ``rc == 0`` 而不是它声称的计数断言上。
    """
    if path is None:
        return None
    resolved = _resolved(path)
    live_vault = _resolved(LIVE_VAULT_DIR)
    if resolved == live_vault or live_vault in resolved.parents:
        return f"{label} {resolved} 落在 live vault ({live_vault}) 内 — 写它会触发部署铁律, 拒绝执行。"
    for guarded in (LIVE_JSON_MIRROR, LIVE_CARD_STATES):
        g = _resolved(guarded)
        if resolved == g or g in resolved.parents:
            return f"{label} {resolved} 与主仓现网文件重叠, 拒绝执行。"
    if vault_dir is not None:
        vd = _resolved(vault_dir)
        if resolved == vd or vd in resolved.parents:
            return f"{label} {resolved} 落在 --vault-dir ({vd}) 子树内 —— 那是**只读**输入面, 拒绝写入。"
    if resolved.exists() and not resolved.is_dir():
        return f"{label} {resolved} 已存在且不是目录, 拒绝执行。"
    return None


def assert_out_is_safe(out: Optional[Path], *others: Optional[Path]) -> Optional[str]:
    """``--out`` 的写入闸 (抄 g35 :156-205).

    ``--out`` 是**写入路径**: ``--dry-run --json-file X --out X`` 会让报告 JSON
    覆盖输入快照 —— "dry-run 零写入"不成立, 且没有备份。
    """
    if out is None:
        return None
    refusal = assert_target_is_not_live(target=out, what="--out 的目标")
    if refusal is not None:
        return refusal
    out_ident = _identity(out)
    if out_ident is None:
        out_resolved = _resolved(out)
        for other in others:
            if other is not None and _resolved(other) == out_resolved:
                return f"--out {out_resolved} 与输入/目标是同一个路径 — 报告会覆盖它, 拒绝。"
        return None
    for other in others:
        if other is None:
            continue
        if _identity(other) == out_ident:
            return f"--out {_resolved(out)} 与输入/目标是同一个文件 (dev/inode {out_ident}) — 报告会覆盖它, 拒绝。"
    return None


def fetch_store_identity(driver: Any, database: Optional[str]) -> Optional[str]:
    """取库的稳定身份 (``db.info().id`` = store id, 与端口/主机无关, g23 :77-93)。"""
    try:
        kwargs = {"database": database} if database else {}
        with driver.session(**kwargs) as session:
            rec = session.run("CALL db.info() YIELD id, name, creationDate RETURN id, name, creationDate").single()
        if not rec:
            return None
        return f"{rec['id']}::{rec['name']}::{rec['creationDate']}"
    except Exception:  # noqa: BLE001 — 任何失败都视为"无法自证身份"
        return None


def assert_store_is_not_live(driver: Any, database: Optional[str], allow_unverified: bool) -> Optional[str]:
    """库身份闸 (g23 :105-160): 端口不是数据库身份, 端口转发能让非现网端口落到现网库。"""
    known = os.environ.get("NEO4J_LIVE_STORE_ID", KNOWN_LIVE_STORE_IDENTITY)
    target_id = fetch_store_identity(driver, database)
    if target_id is None:
        if allow_unverified:
            return None
        return "目标库的 store identity 读不到 — 无法自证它不是现网库, 拒绝写入 (可用 --allow-unverified-target 显式放行)。"
    if target_id == known:
        return f"目标库的 store identity 与已知现网库相同 ({target_id}) — 拒绝写入。"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# frontmatter 真相源
# ═══════════════════════════════════════════════════════════════════════════
def _whole_second_utc(value: Optional[datetime]) -> Optional[datetime]:
    """归一到整秒 UTC —— 比较精度必须等于**真相源本身的分辨率**.

    frontmatter 的 fsrs_due 按构造就是整秒 UTC-Z (vault 侧 FSRS 桥脚本的 ``_whole_second()``
    归一后写出), 而目标侧的值带微秒/纳秒。逐字节比较会让分歧**恒真**, 变成一个
    永远在响的警报 —— 那比没有信号更糟 (review_service.py:163-176 同款说明)。
    """
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0)


def parse_frontmatter_due(text: str) -> Dict[str, Any]:
    """从 ``.md`` 全文抽 ``fsrs_due``。

    Returns:
        governed:  是否由 frontmatter 真相源管辖 (有 ``fsrs_due`` 即 True)
        fsrs_due:  原始字符串 (无字段则 None)
        due:       解析出的 tz-aware datetime; 形态非规范时为 None
        reason:    'no_fsrs_due' / 'malformed_fsrs_due' / None
    """
    out: Dict[str, Any] = {"governed": False, "fsrs_due": None, "due": None, "reason": "no_fsrs_due"}
    block = _FM_BLOCK_RE.match(text)
    fm = block.group(1) if block else ""
    m = re.search(_FM_FIELD_RE.format(key="fsrs_due"), fm, re.M)
    raw = m.group(1).strip() if m else ""
    if not raw:
        return out
    out["governed"] = True
    out["fsrs_due"] = raw
    if not _FM_DUE_SHAPE.fullmatch(raw):
        out["reason"] = "malformed_fsrs_due"
        return out
    try:
        out["due"] = datetime.strptime(raw, _FM_DUE_FORMAT).replace(tzinfo=timezone.utc)
        out["reason"] = None
    except ValueError:
        # 形态过门但日历非法 (如 2026-13-45T00:00:00Z)
        out["reason"] = "malformed_fsrs_due"
    return out


def scan_vault(vault_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, str]]]:
    """扫 ``<vault>/节点/*.md`` 与 ``<vault>/原白板/*.md``, concept_key = 文件 stem.

    同 stem 同时出现在两个目录时按 ``NODE_DIR_PREFIXES`` 的顺序取第一个 (与
    ``frontmatter_signals._node_md_path`` 同序), 被遮蔽的那份**必须显形**
    (返回值第二项), ⛔ 不静默丢弃。
    """
    entries: Dict[str, Dict[str, Any]] = {}
    shadowed: List[Dict[str, str]] = []
    for prefix in NODE_DIR_PREFIXES:
        sub = vault_dir / prefix
        if not sub.is_dir():
            continue
        for path in sorted(sub.glob("*.md")):
            stem = path.stem
            if stem in entries:
                shadowed.append(
                    {
                        "concept_key": stem,
                        "kept_path": entries[stem]["path"],
                        "shadowed_path": str(path),
                    }
                )
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                # 载体在但内容未知 ⇒ 按"归 frontmatter 管"处理 (fail-closed):
                # 读不出来 ⇒ **不知道**它说了什么 ⇒ 不能假设它没话说, 更不能
                # 拿一个读不出的节点去覆盖目标 (review_service.py:298-306 同款)。
                entries[stem] = {
                    "path": str(path),
                    "rel_path": f"{prefix}/{path.name}",
                    "governed": True,
                    "fsrs_due": None,
                    "due": None,
                    "reason": f"node_file_unreadable: {exc}",
                }
                continue
            parsed = parse_frontmatter_due(text)
            parsed["path"] = str(path)
            parsed["rel_path"] = f"{prefix}/{path.name}"
            entries[stem] = parsed
    return entries, shadowed


# ═══════════════════════════════════════════════════════════════════════════
# 目标侧
# ═══════════════════════════════════════════════════════════════════════════
def _normalize_iso(value: str) -> str:
    """把 Neo4j 的纳秒小数秒截到 6 位, ``Z`` 换成 ``+00:00``。"""
    text = value.strip()
    if text.endswith(("z", "Z")):
        text = text[:-1] + "+00:00"

    def _trim(match: "re.Match[str]") -> str:
        return match.group(1)[:7]

    return _ISO_FRACTION_RE.sub(_trim, text, count=1)


def parse_target_value(
    value: Any,
    *,
    naive_tz: str,
    target_kind: str,
) -> Tuple[Optional[datetime], Optional[bool], Optional[str]]:
    """解析目标侧的 ``next_review``。

    Returns:
        (aware_datetime | None, 是否 naive | None, 失败原因 | None)

    **naive 值的解释口径** (Codex 常问的那条): JSON 镜像里的 naive 值语义是
    **本地时间** —— ``neo4j_client.py:717-718`` 用 naive 的 ``datetime.now()``
    写, ``:793/:806`` 又用 naive 的 ``datetime.now()`` 读来比大小, 两侧同为
    naive 本地 ⇒ 这是该文件代码可证的契约, 不是猜测。可用 ``--json-naive-tz utc``
    显式改口径, 报告里会写明用的是哪一种。

    Neo4j 目标不享受这条契约: 驱动返回的 ``datetime`` 恒 tz-aware, 真拿到 naive
    值说明有未知写方 ⇒ 判 ``ambiguous`` **不写**, 而不是猜一个时区。
    """
    if value is None or value == "":
        return None, None, "missing"
    if not isinstance(value, str):
        return None, None, f"unexpected_type:{type(value).__name__}"
    try:
        parsed = datetime.fromisoformat(_normalize_iso(value))
    except ValueError:
        return None, None, "unparsable"
    if parsed.tzinfo is not None:
        return parsed, False, None
    if target_kind == "json" and naive_tz == "utc":
        return parsed.replace(tzinfo=timezone.utc), True, None
    if target_kind == "json" and naive_tz == "local":
        # ⚠️ 夏令时边界上, naive 本地时刻**本身就不是一个确定的时刻**
        # (Codex r1 MEDIUM-8)。秋令回拨那一小时出现两次, 两次相差整 1 小时;
        # 春令跳过的那一小时根本不存在。默默归一会把一小时的**真分歧**判成
        # noop —— 那正是本卡要消灭的那种静默。判据: fold=0 与 fold=1 落到不同
        # 的 UTC 时刻 ⇒ 这个本地串对应不止一个时刻 ⇒ 不写, 显形为 ambiguous。
        fold0 = parsed.replace(fold=0).astimezone(timezone.utc)
        fold1 = parsed.replace(fold=1).astimezone(timezone.utc)
        if fold0 != fold1:
            # 再区分是"重复"还是"不存在": 不存在的本地时刻往返回来会变成别的值。
            roundtrip = parsed.astimezone().replace(tzinfo=None)
            why = "nonexistent_local_time" if roundtrip != parsed else "ambiguous_local_time"
            return None, True, why
        return fold0, True, None
    return None, True, "naive_without_proven_contract"


def collect_json_targets(
    raw: Dict[str, Any],
    group_id: str,
    user_id: Optional[str],
) -> List[Dict[str, Any]]:
    """JSON 镜像目标行 —— 行身份 = ``(user_id, concept_name, group_id)`` 三元组.

    与写方 ``neo4j_client.py:721-726`` 的匹配键逐字同。``--user-id`` 未给时枚举
    全部用户, 每条关系各出一行 (行身份仍是三元组, 不是把不同用户的边揉成一条)。
    ``group_id`` 是**等值**过滤而不是前缀: 这是写身份面 (W1), 不是读召回面。
    """
    rows: List[Dict[str, Any]] = []
    for position, rel in enumerate(raw.get("relationships", [])):
        if not isinstance(rel, dict):
            continue
        if rel.get("group_id") != group_id:
            continue
        if user_id is not None and rel.get("user_id") != user_id:
            continue
        rows.append(
            {
                "concept_key": rel.get("concept_name"),
                "user_id": rel.get("user_id"),
                "group_id": rel.get("group_id"),
                "value": rel.get("next_review"),
                # ⚠️ 行身份带**位置**而不是只带三元组: 旧数据里可能存在重复的
                # (user_id, concept_name, group_id) —— 写方 :721-726 用 next(...)
                # 只更新第一条, 于是重复行能长期并存。按三元组建索引会把它们塌成
                # 一条, 结果是"判 noop 的那一条被连带写入、报告里却没有它"。
                "target_index": position,
            }
        )
    return rows


_NEO4J_READ_QUERY = (
    "MATCH (u:User)-[r:LEARNED]->(c:Concept) "
    "WHERE c.group_id = $gid AND r.group_id = $gid "
    "AND ($uid IS NULL OR u.id = $uid) "
    "RETURN u.id AS user_id, c.name AS concept_key, "
    "toString(r.next_review) AS next_review"
)

_NEO4J_WRITE_QUERY = (
    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $cname}) "
    "WHERE c.group_id = $gid AND r.group_id = $gid "
    "SET r.next_review = datetime($due) "
    "RETURN toString(r.next_review) AS next_review"
)

_NEO4J_CLEAR_QUERY = (
    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $cname}) "
    "WHERE c.group_id = $gid AND r.group_id = $gid "
    "REMOVE r.next_review "
    "RETURN toString(r.next_review) AS next_review"
)


def collect_neo4j_targets(session: Any, group_id: str, user_id: Optional[str]) -> List[Dict[str, Any]]:
    """Neo4j ``LEARNED`` 边目标行 —— ``c`` 与 ``r`` **两个 alias 都过滤** (R1 全覆盖)。"""
    rows: List[Dict[str, Any]] = []
    for rec in session.run(_NEO4J_READ_QUERY, gid=group_id, uid=user_id):
        rows.append(
            {
                "concept_key": rec["concept_key"],
                "user_id": rec["user_id"],
                "group_id": group_id,
                "value": rec["next_review"],
                "ref": None,
            }
        )
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# 分类
# ═══════════════════════════════════════════════════════════════════════════
def _row(
    concept_key: str,
    entry: Optional[Dict[str, Any]],
    target: Optional[Dict[str, Any]],
    *,
    action: str,
    unmatched_kind: Optional[str] = None,
    reason: Optional[str] = None,
    target_naive: Optional[bool] = None,
    new_next_review: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "node_id": (entry or {}).get("rel_path"),
        "concept_key": concept_key,
        "user_id": (target or {}).get("user_id"),
        "group_id": (target or {}).get("group_id"),
        "frontmatter_fsrs_due": (entry or {}).get("fsrs_due"),
        "target_next_review": (target or {}).get("value"),
        # 身份映射是否对上 —— 与 action 正交的一维 (Codex r1 MEDIUM-10):
        # due 坏掉的节点归 malformed_fsrs_due, 但"它在目标侧也没有边"这件事
        # 不能因此消失。每行都带这个标, 任何 action 下都看得见。
        "target_missing": target is None,
        "target_index": (target or {}).get("target_index"),
        "target_naive": target_naive,
        "action": action,
        "unmatched_kind": unmatched_kind,
        "reason": reason,
        "new_next_review": new_next_review,
    }


def classify_rows(
    entries: Dict[str, Dict[str, Any]],
    targets: Sequence[Dict[str, Any]],
    *,
    naive_tz: str,
    target_kind: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """把 frontmatter 侧与目标侧做**并集**枚举并逐行定性.

    并集而不是单向枚举: 身份映射可能在**两个方向**失败 —— governed 节点在目标
    侧没有边 (``no_target``), 目标侧的边没有任何 ``.md`` 载体 (``no_frontmatter``)。
    两种都必须显形为 ``unmatched``, ⛔ 不静默跳过 (少了哪一边都会让"对账"漏掉
    真实存在的孤儿数据)。
    """
    counts: Dict[str, int] = {k: 0 for k in COUNT_KEYS}
    rows: List[Dict[str, Any]] = []

    by_key: Dict[str, List[Dict[str, Any]]] = {}
    for tgt in targets:
        by_key.setdefault(str(tgt["concept_key"]), []).append(tgt)

    for key in sorted(entries):
        entry = entries[key]
        matched = by_key.get(key, [])
        if not entry["governed"]:
            counts["ungoverned"] += 1
            rows.append(
                _row(
                    key,
                    entry,
                    matched[0] if matched else None,
                    action="ungoverned",
                    reason=entry.get("reason"),
                )
            )
            continue

        counts["governed"] += 1
        if entry.get("due") is None:
            counts["malformed_fsrs_due"] += 1
            rows.append(
                _row(
                    key,
                    entry,
                    matched[0] if matched else None,
                    action="malformed_fsrs_due",
                    reason=entry.get("reason"),
                )
            )
            continue

        if not matched:
            counts["unmatched"] += 1
            counts["unmatched_no_target"] += 1
            rows.append(_row(key, entry, None, action="unmatched", unmatched_kind="no_target"))
            continue

        counts["matched"] += 1
        for tgt in matched:
            parsed, naive, why = parse_target_value(tgt["value"], naive_tz=naive_tz, target_kind=target_kind)
            if why == "missing":
                counts["backfill"] += 1
                rows.append(
                    _row(key, entry, tgt, action="backfill", target_naive=naive, new_next_review=entry["fsrs_due"])
                )
                continue
            if parsed is None:
                counts["ambiguous"] += 1
                rows.append(_row(key, entry, tgt, action="ambiguous", reason=why, target_naive=naive))
                continue
            if _whole_second_utc(parsed) == _whole_second_utc(entry["due"]):
                counts["noop"] += 1
                rows.append(_row(key, entry, tgt, action="noop", target_naive=naive))
            else:
                counts["set"] += 1
                rows.append(_row(key, entry, tgt, action="set", target_naive=naive, new_next_review=entry["fsrs_due"]))

    for key in sorted(by_key):
        if key in entries:
            continue
        for tgt in by_key[key]:
            counts["unmatched"] += 1
            counts["unmatched_no_frontmatter"] += 1
            rows.append(_row(key, None, tgt, action="unmatched", unmatched_kind="no_frontmatter"))

    # 与 action 正交的一维: 有多少行在目标侧压根没有对应的边。
    # `unmatched_no_target` 只数**有效 due** 的那些; 本计数把 malformed /
    # 读不出的 governed 节点也算进来, 于是"身份没对上"不会因为节点自身的
    # 毛病而从报告里消失 (Codex r1 MEDIUM-10)。
    counts["rows_without_target"] = sum(1 for r in rows if r["target_missing"])

    return rows, counts


def card_states_divergence(path: Path, entries: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """**只读**统计 ``fsrs_card_states.json`` 的 ``due`` 与 ``fsrs_due`` 的分歧.

    G3-7 已把该文件降为**投影缓存**, 本脚本只报数、⛔ 永不写它。
    """
    out: Dict[str, Any] = {"file": str(path), "compared": 0, "diverged": 0, "unparsable": 0, "concepts": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    if not isinstance(raw, dict):
        out["error"] = "顶层不是对象"
        return out
    for bucket in raw.values():
        if not isinstance(bucket, dict):
            continue
        for concept_id, card_json in bucket.items():
            entry = entries.get(concept_id)
            if entry is None or entry.get("due") is None:
                continue
            try:
                card = json.loads(card_json) if isinstance(card_json, str) else card_json
                due_raw = card.get("due") if isinstance(card, dict) else None
                parsed = datetime.fromisoformat(_normalize_iso(str(due_raw)))
            except (ValueError, AttributeError, TypeError):
                out["unparsable"] += 1
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            out["compared"] += 1
            if _whole_second_utc(parsed) != _whole_second_utc(entry["due"]):
                out["diverged"] += 1
                out["concepts"].append(concept_id)
    return out


def _json_mirror_warning() -> Dict[str, str]:
    """写 UTC-Z (tz-aware) 进 JSON 镜像的**已知下游后果** —— 显形而不是静默制造。

    ``neo4j_client.py:806-808`` 用 naive 的 ``datetime.now()`` 与读出的值比大小;
    值是 tz-aware 时抛 ``TypeError``, 被 ``:833`` 的
    ``except (ValueError, TypeError): continue`` **静默跳过** —— 该 concept 会从
    JSON 降级路径的复习建议里消失。修那一侧属 P1/P2 地盘, 不在本卡范围, 所以
    在报告里如实报出来。
    """
    return {
        "code": WARN_JSON_MIRROR_AWARE_READER,
        "detail": (
            "写入 JSON 镜像的值是整秒 UTC-Z (tz-aware); "
            "app/clients/neo4j_client.py:806-808 用 naive 的 datetime.now() 与它比大小会抛 TypeError, "
            "被 :833 的 except (ValueError, TypeError): continue 静默跳过 —— "
            "该 concept 会从 JSON 降级路径的复习建议里消失。"
            "修读方属 P1/P2 地盘, 不在 CARD-G3-8 范围, 此处只如实报出。"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 报告
# ═══════════════════════════════════════════════════════════════════════════
def build_report(
    mode: str,
    *,
    group_id: str,
    user_id: Optional[str],
    target_kind: str,
    target_ref: str,
    vault_dir: Optional[Path],
    naive_tz: str,
    entries: Dict[str, Dict[str, Any]],
    json_file: Optional[Path],
    rows: List[Dict[str, Any]],
    counts: Dict[str, int],
    shadowed: List[Dict[str, str]],
) -> Dict[str, Any]:
    inputs: Dict[str, str] = {}
    for entry in entries.values():
        path = Path(entry["path"])
        try:
            inputs[entry["rel_path"]] = _sha256_file(path)
        except OSError:
            inputs[entry["rel_path"]] = "<unreadable>"
    if json_file is not None:
        try:
            inputs["__json_file__"] = _sha256_file(json_file)
        except OSError:
            inputs["__json_file__"] = "<unreadable>"

    warnings: List[Dict[str, str]] = []
    if target_kind == "json" and (counts["set"] + counts["backfill"]) > 0:
        warnings.append(_json_mirror_warning())

    return {
        "card": "CARD-G3-8",
        "mode": mode,
        "group_id": group_id,
        "user_id": user_id,
        "target_kind": target_kind,
        "target": target_ref,
        "vault_dir": str(vault_dir) if vault_dir is not None else None,
        "naive_interpretation": naive_tz,
        "inputs_sha256": inputs,
        "counts": counts,
        "rows": rows,
        "shadowed": shadowed,
        "warnings": warnings,
    }


def write_report_checked(
    ctx: "_Context",
    bundle: Optional[Dict[str, Any]],
    payload: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """写报告前**用扫到的真实节点清单**再核一次 ``--out`` (Codex r2 HIGH-4).

    ``main`` 里那次核查发生在扫描之前, 手里只有 ``--card-states-file``; 而
    ``vault/节点/A.md`` 可以是指向 vault **外**某个文件的符号链接 —— 那个文件既
    不在 ``--vault-dir`` 子树内, 也不在当时的只读输入清单里, 于是
    ``--out <那个文件>`` 能穿过第一道核查, 在报告落盘时覆盖真相源。
    扫完之后我们才真正知道读了哪些文件, 这一次核查用的是那份实测清单。
    """
    refusal = assert_write_path_is_safe(
        ctx.out,
        vault_dir=ctx.vault_dir,
        read_inputs=_read_inputs(ctx, bundle),
        label="--out 的目标",
    )
    if refusal is not None:
        return False, refusal
    return write_report(ctx.out, payload), None


def write_report(out: Optional[Path], payload: Dict[str, Any]) -> bool:
    if out is None:
        return False
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: 报告写入失败 {out}: {exc}", file=sys.stderr)
        return False
    return True


def _print_summary(title: str, ctx: "_Context", counts: Dict[str, int]) -> None:
    print("=" * 68)
    print(title)
    print("=" * 68)
    print(f"vault    : {ctx.vault_dir if ctx.vault_dir is not None else '(未给, rollback 模式)'}")
    print(f"group_id : {ctx.group_id}")
    print(f"user_id  : {ctx.user_id if ctx.user_id else '(全部)'}")
    print(f"目标     : {ctx.target_kind} {ctx.target_ref}")
    print(f"naive 解释: {ctx.naive_tz}")
    print("-" * 68)
    for key in COUNT_KEYS:
        print(f"  {key:<26}: {counts[key]}")
    print("=" * 68)


# ═══════════════════════════════════════════════════════════════════════════
# 运行上下文
# ═══════════════════════════════════════════════════════════════════════════
class _Context:
    """一次运行需要的全部解析结果 —— 三个 ``run_*`` 共用。"""

    def __init__(self, args: argparse.Namespace) -> None:
        self.group_id: str = args.group_id
        self.user_id: Optional[str] = args.user_id
        self.vault_dir: Optional[Path] = Path(args.vault_dir) if args.vault_dir else None
        self.json_file: Optional[Path] = Path(args.json_file) if args.json_file else None
        self.neo4j_uri: Optional[str] = args.neo4j_uri
        self.neo4j_user: Optional[str] = args.neo4j_user
        self.neo4j_password: Optional[str] = args.neo4j_password
        self.neo4j_database: Optional[str] = args.neo4j_database
        self.naive_tz: str = args.json_naive_tz
        self.out: Optional[Path] = Path(args.out) if args.out else None
        self.backup_dir: Optional[Path] = Path(args.backup_dir) if args.backup_dir else None
        self.allow_unverified: bool = args.allow_unverified_target
        self.allow_unbound_vault: bool = args.allow_unbound_vault
        self.group_scope: Optional[str] = args.group_scope
        self.card_states_file: Optional[Path] = Path(args.card_states_file) if args.card_states_file else None

    @property
    def target_kind(self) -> str:
        return "json" if self.json_file is not None else "neo4j"

    @property
    def target_ref(self) -> str:
        return str(self.json_file) if self.json_file is not None else str(self.neo4j_uri)


def _neo4j_driver(ctx: "_Context") -> Any:
    """延迟 import —— 只有真给了 ``--neo4j-uri`` 才需要驱动 (纯 stdlib 原则)。

    URI 为空时**当场炸**而不是把 None 交给驱动: 驱动拿到 None 会用它自己的默认
    路由 (7687 = 现网端口集内), 等于绕过了 :func:`assert_target_is_not_live` ——
    fail-closed 比让驱动"帮忙猜一个地址"安全。
    """
    from neo4j import GraphDatabase

    if not ctx.neo4j_uri:
        raise ValueError("内部错误: 没有 --neo4j-uri 却要建驱动 — 拒绝让驱动走默认路由。")
    auth = None
    if ctx.neo4j_user is not None:
        auth = (ctx.neo4j_user, ctx.neo4j_password or "")
    return GraphDatabase.driver(ctx.neo4j_uri, auth=auth)


def _session(driver: Any, ctx: "_Context") -> Any:
    return driver.session(database=ctx.neo4j_database) if ctx.neo4j_database else driver.session()


def _open_verified_driver(ctx: "_Context") -> Tuple[Any, Optional[str]]:
    """建驱动并**在任何业务读之前**核库身份 (Codex r1 HIGH-5).

    端口不是数据库身份: 端口转发 / 路由种子可以让 ``7692`` 落到现网库。此前
    身份闸只在写之前跑, 而 ``--dry-run`` 与 ``--apply`` 的 ``_gather`` 都已经
    先读了一轮业务数据 —— 「禁连现网」被读侧绕开了。现在**每一条**进出库的路径
    都从这里拿驱动, 身份不过关就拿不到可用的连接。

    唯一先于身份闸发生的查询是 ``CALL db.info()`` 自身 (身份证据只能从库里取),
    它不读任何业务数据。
    """
    driver = _neo4j_driver(ctx)
    refusal = assert_store_is_not_live(driver, ctx.neo4j_database, ctx.allow_unverified)
    if refusal is not None:
        driver.close()
        return None, refusal
    return driver, None


def _load_json_mirror(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"JSON 镜像读不出 {path}: {exc}"
    except ValueError as exc:
        return None, f"JSON 镜像不是合法 JSON {path}: {exc}"
    if not isinstance(raw, dict) or not isinstance(raw.get("relationships"), list):
        return None, f"JSON 镜像形态非法 (缺 relationships 列表): {path}"
    return raw, None


def _gather(ctx: "_Context") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """扫 frontmatter + 读目标 + 定性。返回 (bundle, 错误)。"""
    if ctx.vault_dir is None or not ctx.vault_dir.is_dir():
        return None, f"--vault-dir 不是目录: {ctx.vault_dir}"
    entries, shadowed = scan_vault(ctx.vault_dir)

    raw: Optional[Dict[str, Any]] = None
    if ctx.json_file is not None:
        raw, err = _load_json_mirror(ctx.json_file)
        if err is not None:
            return None, err
        assert raw is not None
        targets = collect_json_targets(raw, ctx.group_id, ctx.user_id)
        rows, counts = classify_rows(entries, targets, naive_tz=ctx.naive_tz, target_kind="json")
    else:
        driver, refusal = _open_verified_driver(ctx)
        if refusal is not None:
            return None, refusal
        try:
            with _session(driver, ctx) as session:
                targets = collect_neo4j_targets(session, ctx.group_id, ctx.user_id)
        finally:
            driver.close()
        rows, counts = classify_rows(entries, targets, naive_tz=ctx.naive_tz, target_kind="neo4j")

    return {"entries": entries, "shadowed": shadowed, "rows": rows, "counts": counts, "raw": raw}, None


def _report_for(ctx: "_Context", mode: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
    report = build_report(
        mode,
        group_id=ctx.group_id,
        user_id=ctx.user_id,
        target_kind=ctx.target_kind,
        target_ref=ctx.target_ref,
        vault_dir=ctx.vault_dir,
        naive_tz=ctx.naive_tz,
        entries=bundle["entries"],
        json_file=ctx.json_file,
        rows=bundle["rows"],
        counts=bundle["counts"],
        shadowed=bundle["shadowed"],
    )
    if ctx.card_states_file is not None:
        report["card_states_divergence"] = card_states_divergence(ctx.card_states_file, bundle["entries"])
    return report


# ═══════════════════════════════════════════════════════════════════════════
# 模式 ①: dry-run —— 除 --out 外零写入
# ═══════════════════════════════════════════════════════════════════════════
def run_dry_run(ctx: "_Context") -> int:
    bundle, err = _gather(ctx)
    if err is not None:
        print(f"ERROR: {err}", file=sys.stderr)
        return RC_REFUSED
    assert bundle is not None
    report = _report_for(ctx, "dry-run", bundle)
    _print_summary("CARD-G3-8 next_review 对账 — DRY-RUN (零写入)", ctx, bundle["counts"])
    for warning in report["warnings"]:
        print(f"⚠️ {warning['code']}: {warning['detail']}")
    wrote, refusal = write_report_checked(ctx, bundle, report)
    if refusal is not None:
        print(f"ERROR: {refusal}", file=sys.stderr)
        return RC_REFUSED
    if wrote:
        print(f"报告已写: {ctx.out} (本次唯一的文件写入)")
    return RC_OK


# ═══════════════════════════════════════════════════════════════════════════
# 模式 ②: apply —— pre-image → 写 → 读回校验 → 失败还原
# ═══════════════════════════════════════════════════════════════════════════
def _read_inputs(ctx: "_Context", bundle: Optional[Dict[str, Any]] = None) -> List[Path]:
    """本次运行的**只读**输入文件清单 —— 任何写入路径都不得与它们重合。"""
    out: List[Path] = []
    if bundle is not None:
        out.extend(Path(e["path"]) for e in bundle["entries"].values())
    if ctx.card_states_file is not None:
        out.append(ctx.card_states_file)
    return out


def _write_preimage(
    ctx: "_Context",
    payload: Dict[str, Any],
    read_inputs: Sequence[Path],
) -> Tuple[Optional[Path], Optional[str]]:
    assert ctx.backup_dir is not None
    path = ctx.backup_dir / f"preimage-{_now_stamp()}.json"
    # ⚠️ 闸必须排在 mkdir **前面** (Codex r1 MEDIUM-9): 先建目录再检查, 等于
    # 已经在 live vault 里落了一个目录才说"这里不能写"。
    # ⚠️ 备份**目录**不能走 assert_write_path_is_safe —— 它含"已存在且不是普通文件
    # 就拒"的判据, 会把第二次 apply 时**本来就应该存在**的目录拒在门外
    # (Codex r2 MEDIUM-6)。目录用目录闸。
    refusal = assert_write_dir_is_safe(ctx.backup_dir, vault_dir=ctx.vault_dir, label="--backup-dir")
    if refusal is not None:
        return None, refusal
    refusal = assert_write_path_is_safe(
        path, vault_dir=ctx.vault_dir, read_inputs=read_inputs, label="pre-image 的目标"
    )
    if refusal is not None:
        return None, refusal
    try:
        ctx.backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return None, f"备份目录建不出来 {ctx.backup_dir}: {exc}"
    # pre-image 也是**写入路径**, 同样怕别名 (g35 的 --out 别名教训同型):
    # 报告在 apply 末尾才写, 若 --out 指到同一个位置, 它会**在写入成功之后**
    # 把刚落盘的 pre-image 覆盖成统计报告 —— 回滚依据就没了。
    for other, label in ((ctx.out, "--out"), (ctx.json_file, "--json-file")):
        if other is not None and _resolved(other) == _resolved(path):
            return None, f"pre-image 路径 {_resolved(path)} 与 {label} 是同一个位置 — 回滚依据会被覆盖, 拒绝执行。"
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        return None, f"pre-image 落盘失败 {path}: {exc}"
    return path, None


def _apply_json(ctx: "_Context", bundle: Dict[str, Any], writable: List[Dict[str, Any]]) -> int:
    assert ctx.json_file is not None
    target = ctx.json_file
    before_sha = _sha256_file(target)

    # 双备份 (抄 g35 :404-440): 备份自身失败 = 还没动源文件就停手。
    # 备份路径也是**写入路径**, 必须过同一道闸。
    stamped = target.with_suffix(f"{target.suffix}.bak.{_now_stamp()}")
    simple = target.with_suffix(f"{target.suffix}.bak")
    if _resolved(stamped) == _resolved(simple):
        print("ERROR: 时间戳备份与简单备份指向同一位置 — 双备份会退化成一份, 已中止。", file=sys.stderr)
        return RC_REFUSED
    read_inputs = _read_inputs(ctx, bundle)
    # --out 在 apply **末尾**才写: 它若别名到本次备份, 一次成功的迁移结束时
    # 回滚依据已被统计报告顶掉 (Codex r2 MEDIUM-8, 与 pre-image 同型)。
    for backup in (stamped, simple):
        if ctx.out is not None and _resolved(ctx.out) == _resolved(backup):
            print(
                f"ERROR: --out {_resolved(ctx.out)} 与本次备份是同一个位置 — 报告会覆盖回滚依据, 拒绝执行。",
                file=sys.stderr,
            )
            return RC_REFUSED
    for backup in (stamped, simple):
        refusal = assert_write_path_is_safe(
            backup, vault_dir=ctx.vault_dir, read_inputs=read_inputs, label="备份的目标"
        )
        if refusal is not None:
            print(f"ERROR: {refusal}", file=sys.stderr)
            return RC_REFUSED
    try:
        shutil.copy2(target, stamped)
        shutil.copy2(target, simple)
    except OSError as exc:
        print(f"ERROR: 备份失败 ({exc}) — 源文件未改动, 已中止。", file=sys.stderr)
        return RC_NOT_WRITTEN

    preimage_payload = {
        "card": "CARD-G3-8",
        "mode": "pre-image",
        "group_id": ctx.group_id,
        "user_id": ctx.user_id,
        "target_kind": "json",
        "target_path": str(target),
        "target_sha256_before": before_sha,
        "backups": {"stamped": str(stamped), "simple": str(simple)},
        "rows": [
            {
                "concept_key": row["concept_key"],
                "user_id": row["user_id"],
                "old_next_review": row["target_next_review"],
                "new_next_review": row["new_next_review"],
            }
            for row in writable
        ],
    }
    preimage_path, err = _write_preimage(ctx, preimage_payload, read_inputs)
    if err is not None:
        print(f"ERROR: {err} — pre-image 落盘成功才允许开写, 源文件未改动。", file=sys.stderr)
        return RC_NOT_WRITTEN

    raw = bundle["raw"]
    relationships = raw.get("relationships", [])
    for row in writable:
        position = row["target_index"]
        if position is None or not isinstance(position, int) or position >= len(relationships):
            print(f"ERROR: 行 {row['concept_key']} 的位置索引失效 ({position}) — 还原到备份。", file=sys.stderr)
            return _restore_json(target, stamped, before_sha)
        relationships[position]["next_review"] = row["new_next_review"]

    try:
        target.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: 写入失败 {target}: {exc}", file=sys.stderr)
        return _restore_json(target, stamped, before_sha)

    # 写完**读回执**, 不用"没抛异常即成功" (G-FAKE 教训)。
    verified, err = _load_json_mirror(target)
    if err is not None or verified is None:
        print(f"ERROR: 写后重读失败 ({err}) — 还原到备份。", file=sys.stderr)
        return _restore_json(target, stamped, before_sha)
    reread = verified["relationships"]
    bad = [
        f"{row['user_id']}/{row['concept_key']}@{row['target_index']}"
        for row in writable
        if row["target_index"] >= len(reread)
        or reread[row["target_index"]].get("next_review") != row["new_next_review"]
    ]
    if bad:
        print(f"ERROR: 写后读回与期望不符 {bad} — 还原到备份。", file=sys.stderr)
        return _restore_json(target, stamped, before_sha)

    print(f"已写 {len(writable)} 行; 备份: {stamped} / {simple}; pre-image: {preimage_path}")
    bundle["preimage_path"] = str(preimage_path)
    return RC_OK


def _restore_json(target: Path, backup: Path, expected_sha: str) -> int:
    try:
        shutil.copy2(backup, target)
        if _sha256_file(target) != expected_sha:
            raise OSError("还原后的 sha256 与迁移前不符")
    except OSError as exc:
        print(
            f"CRITICAL: 回滚也失败 ({exc}) — 目标 {target} 可能半写, 备份在 {backup}, 需人工处置。",
            file=sys.stderr,
        )
        return RC_ROLLBACK_FAILED
    print(f"已回滚到备份 {backup} — 目标处于迁移前的可信状态。", file=sys.stderr)
    return RC_NOT_WRITTEN


def _restore_neo4j(session: Any, group_id: str, rows: Sequence[Dict[str, Any]]) -> List[str]:
    """按 pre-image 逐条把 ``next_review`` 放回去, 返回**没能还原**的行标识.

    读回执用**精确时刻**比 (不是整秒): 还原要证明的是"回到原样", 原值可能带
    亚秒精度, 整秒比较会把丢掉的小数秒当成还原成功 (Codex r1 Q1 末段)。
    """
    failed: List[str] = []
    for row in rows:
        old = row.get("old_next_review")
        ident = f"{row.get('user_id')}/{row.get('concept_key')}"
        params: Dict[str, Any] = {
            "uid": row.get("user_id"),
            "cname": row.get("concept_key"),
            "gid": group_id,
        }
        query = _NEO4J_CLEAR_QUERY if old in (None, "") else _NEO4J_WRITE_QUERY
        if old not in (None, ""):
            params["due"] = old
        try:
            rec = session.run(query, **params).single()
        except Exception as exc:  # noqa: BLE001 — 还原期任何异常都算没还原成功
            failed.append(f"{ident} ({type(exc).__name__}: {exc})")
            continue
        got = rec["next_review"] if rec is not None else None
        ok = (rec is not None and got is None) if old in (None, "") else _same_instant_exact(got, old)
        if not ok:
            failed.append(ident)
    return failed


def _apply_neo4j(ctx: "_Context", bundle: Dict[str, Any], writable: List[Dict[str, Any]]) -> int:
    driver, refusal = _open_verified_driver(ctx)
    if refusal is not None:
        print(f"ERROR: {refusal}", file=sys.stderr)
        return RC_REFUSED
    try:
        preimage_payload = {
            "card": "CARD-G3-8",
            "mode": "pre-image",
            "group_id": ctx.group_id,
            "user_id": ctx.user_id,
            "target_kind": "neo4j",
            "target_uri": ctx.neo4j_uri,
            "database": ctx.neo4j_database,
            "rows": [
                {
                    "concept_key": row["concept_key"],
                    "user_id": row["user_id"],
                    "old_next_review": row["target_next_review"],
                    "new_next_review": row["new_next_review"],
                }
                for row in writable
            ],
        }
        preimage_path, err = _write_preimage(ctx, preimage_payload, _read_inputs(ctx, bundle))
        if err is not None:
            print(f"ERROR: {err} — pre-image 落盘成功才允许开写, 库未改动。", file=sys.stderr)
            return RC_NOT_WRITTEN

        # ⚠️ 还原集合必须是 **pre-image 形状**的行 (Codex r2 HIGH-2): 分类行带的是
        # `target_next_review`, pre-image 行带的是 `old_next_review`。此前把分类行
        # 直接喂给 _restore_neo4j, 它取 `old_next_review` 恒得 None ⇒ 走 REMOVE ⇒
        # **把原值清空**, 读回执还通过, 然后报告「迁移前的可信状态」。
        preimage_by_key = {(r["user_id"], r["concept_key"]): r for r in preimage_payload["rows"]}
        failed: List[str] = []
        attempted: List[Dict[str, Any]] = []
        with _session(driver, ctx) as session:
            for row in writable:
                # ⚠️ **下笔前**记账 (Codex r2 HIGH-3): 若写已提交而取回执时连接断了,
                # 事后记账会把这一行漏出还原集合 —— rc=1 声称「未改动」却证明不了。
                # 多还原一行无害 (再写一次原值), 漏还原一行不是。
                attempted.append(preimage_by_key[(row["user_id"], row["concept_key"])])
                try:
                    rec = session.run(
                        _NEO4J_WRITE_QUERY,
                        uid=row["user_id"],
                        cname=row["concept_key"],
                        gid=ctx.group_id,
                        due=row["new_next_review"],
                    ).single()
                except Exception as exc:  # noqa: BLE001 — 写入期异常与回执不符同路处置
                    failed.append(f"{row['user_id']}/{row['concept_key']} ({type(exc).__name__}: {exc})")
                    break
                # 写完读回执: 拿 SET 之后 RETURN 的实值逐条比, 不用"没抛异常即成功"。
                if rec is None or not _same_instant(rec["next_review"], row["new_next_review"]):
                    failed.append(f"{row['user_id']}/{row['concept_key']}")
                    break

            if failed:
                # ⚠️ 逐条写入不是原子的: 到这里库里已经有若干行被改过了
                # (Codex r1 HIGH-3)。此前直接返回 1, 而 1 的语义是「目标处于迁移前
                # 的可信状态」—— 那是谎报。必须先按 pre-image 把下过笔的那些放回去,
                # 放得回去才配叫 1, 放不回去是 3。
                print(
                    f"ERROR: 写入/读回执失败 {failed} — 已下笔 {len(attempted)} 行, 正按 pre-image 还原。",
                    file=sys.stderr,
                )
                restore_failed = _restore_neo4j(session, ctx.group_id, attempted)
                if restore_failed:
                    print(
                        f"CRITICAL: 回滚也失败 {restore_failed} — 库可能半写, pre-image 在 {preimage_path}, 需人工处置。",
                        file=sys.stderr,
                    )
                    return RC_ROLLBACK_FAILED
                print(f"已按 pre-image 还原 {len(attempted)} 行 — 库处于迁移前的可信状态。", file=sys.stderr)
                return RC_NOT_WRITTEN
        print(f"已写 {len(writable)} 行; pre-image: {preimage_path}")
        bundle["preimage_path"] = str(preimage_path)
        return RC_OK
    finally:
        driver.close()


def _fraction_digits(value: str) -> str:
    """取 ISO 串里的小数秒**全部**位数 (右侧补零到 9 位, 便于逐位比)。"""
    m = _ISO_FRACTION_RE.search(value)
    return (m.group(1)[1:] if m else "").ljust(9, "0")


def _same_instant_exact(got: Any, expected: Optional[str]) -> bool:
    """**精确**时刻相等 —— 还原校验用。

    ⚠️ 不能只比 ``datetime``: :func:`_normalize_iso` 把小数秒截到 6 位 (因为
    ``fromisoformat`` 只收 6 位), 于是 ``.123456999Z`` 与 ``.123456001Z`` 会被判
    相等 (Codex r2 MEDIUM-7)。还原要证明的是"回到原样", 把纳秒差异吞掉就证明不了。
    故在 datetime 相等之外**另比一次原始小数秒位**。
    """
    if expected is None:
        return got is None
    if not isinstance(got, str):
        return False
    try:
        a = datetime.fromisoformat(_normalize_iso(got))
        b = datetime.fromisoformat(_normalize_iso(expected))
    except ValueError:
        return False
    if a.tzinfo is None or b.tzinfo is None:
        return False
    if a.astimezone(timezone.utc) != b.astimezone(timezone.utc):
        return False
    return _fraction_digits(got) == _fraction_digits(expected)


def _same_instant(got: Any, expected: Optional[str]) -> bool:
    if expected is None:
        return got is None
    if not isinstance(got, str):
        return False
    try:
        a = datetime.fromisoformat(_normalize_iso(got))
        b = datetime.fromisoformat(_normalize_iso(expected))
    except ValueError:
        return False
    if a.tzinfo is None or b.tzinfo is None:
        return False
    return _whole_second_utc(a) == _whole_second_utc(b)


def run_apply(ctx: "_Context") -> int:
    if ctx.backup_dir is None:
        print("ERROR: --apply 必须给 --backup-dir (没有有效 pre-image 就不该开始写)。", file=sys.stderr)
        return RC_REFUSED

    refusal = assert_target_is_not_live(
        target=ctx.json_file,
        uri=ctx.neo4j_uri,
        what="--apply 的目标",
    )
    if refusal is not None:
        print(f"ERROR: {refusal}", file=sys.stderr)
        return RC_REFUSED

    bundle, err = _gather(ctx)
    if err is not None:
        print(f"ERROR: {err}", file=sys.stderr)
        return RC_REFUSED
    assert bundle is not None

    writable = [r for r in bundle["rows"] if r["action"] in ("set", "backfill")]
    _print_summary("CARD-G3-8 next_review 对账 — APPLY", ctx, bundle["counts"])

    rc = RC_OK
    if not writable:
        # 「已经对齐」与「本来就没数据」都走这条 —— 不产生备份、不写一个字节。
        print("无可写行 (set + backfill = 0) — 未做任何写入, 未产生备份。")
    elif ctx.json_file is not None:
        rc = _apply_json(ctx, bundle, writable)
    else:
        rc = _apply_neo4j(ctx, bundle, writable)

    report = _report_for(ctx, "apply", bundle)
    report["preimage_path"] = bundle.get("preimage_path")
    report["written"] = len(writable) if rc == RC_OK else 0
    wrote, refusal = write_report_checked(ctx, bundle, report)
    if refusal is not None:
        # 数据侧已按 rc 处置完毕; 报告写不得只影响报告, 不改变数据侧结论。
        print(f"ERROR: 报告未写 — {refusal}", file=sys.stderr)
    elif wrote:
        print(f"报告已写: {ctx.out}")
    return rc


# ═══════════════════════════════════════════════════════════════════════════
# 模式 ③: rollback —— 从 .bak / pre-image 逐条还原并读回校验
# ═══════════════════════════════════════════════════════════════════════════
def run_rollback(ctx: "_Context", preimage_file: Path) -> int:
    try:
        payload = json.loads(preimage_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: pre-image 读不出 {preimage_file}: {exc}", file=sys.stderr)
        return RC_REFUSED
    if not isinstance(payload, dict) or payload.get("card") != "CARD-G3-8":
        print(f"ERROR: {preimage_file} 不是 CARD-G3-8 的 pre-image。", file=sys.stderr)
        return RC_REFUSED
    if payload.get("group_id") != ctx.group_id:
        print(
            f"ERROR: pre-image 的 group_id {payload.get('group_id')!r} 与 --group-id {ctx.group_id!r} 不同 — 拒绝跨组回滚。",
            file=sys.stderr,
        )
        return RC_REFUSED

    refusal = assert_target_is_not_live(target=ctx.json_file, uri=ctx.neo4j_uri, what="--rollback 的目标")
    if refusal is not None:
        print(f"ERROR: {refusal}", file=sys.stderr)
        return RC_REFUSED

    if payload.get("target_kind") == "json":
        return _rollback_json(ctx, payload)
    return _rollback_neo4j(ctx, payload)


def _rollback_json(ctx: "_Context", payload: Dict[str, Any]) -> int:
    if ctx.json_file is None:
        print("ERROR: pre-image 是 JSON 目标, 但没给 --json-file。", file=sys.stderr)
        return RC_REFUSED
    # ⚠️ pre-image 必须绑回**它自己那个目标** (Codex r1 HIGH-4): 备份是整份镜像,
    # 把 A 的备份倒进同组的另一份 B, 逐条校验照样全过 —— 它校验的是"内容等于
    # 备份", 而不是"这是不是该还原的那个文件"。同组不等于同目标。
    recorded = payload.get("target_path")
    if not recorded or _resolved(Path(recorded)) != _resolved(ctx.json_file):
        print(
            f"ERROR: pre-image 记录的目标是 {recorded!r}, 而 --json-file 指向 "
            f"{_resolved(ctx.json_file)} — 拒绝把一份备份还原到别的文件上。",
            file=sys.stderr,
        )
        return RC_REFUSED
    expected = payload.get("target_sha256_before")
    backup = Path(payload.get("backups", {}).get("stamped", ""))
    if not backup.is_file():
        print(f"ERROR: pre-image 记录的备份不存在: {backup}", file=sys.stderr)
        return RC_NOT_WRITTEN
    try:
        actual = _sha256_file(backup)
    except OSError as exc:
        print(f"ERROR: 备份 {backup} 读不出 ({exc}) — 无法证明它是迁移前那一份, 目标未改动。", file=sys.stderr)
        return RC_NOT_WRITTEN
    if actual != expected:
        # 备份被改动过 ⇒ 它不再是"迁移前那一份" ⇒ 拿它覆盖目标就是拿不可信的数据
        # 覆盖可信的数据。目标保持现状, 交人工处置。
        print(
            f"ERROR: 备份 {backup} 的 sha256 ({actual}) 与 pre-image 记录的 ({expected}) 不符 — 拒绝用它覆盖目标。",
            file=sys.stderr,
        )
        return RC_NOT_WRITTEN
    try:
        shutil.copy2(backup, ctx.json_file)
    except OSError as exc:
        print(f"CRITICAL: 回滚写入失败 ({exc}) — 目标 {ctx.json_file} 可能半写, 备份在 {backup}。", file=sys.stderr)
        return RC_ROLLBACK_FAILED
    # 读回校验 —— 读不出来与读出来不对**同样**是"还没还原成功", 都归 3。
    try:
        readback = _sha256_file(ctx.json_file)
    except OSError as exc:
        print(f"CRITICAL: 回滚后读不回目标 ({exc}) — {ctx.json_file} 需人工处置, 备份在 {backup}。", file=sys.stderr)
        return RC_ROLLBACK_FAILED
    if readback != expected:
        print(f"CRITICAL: 回滚后读回的 sha256 与迁移前不符 — 目标 {ctx.json_file} 需人工处置。", file=sys.stderr)
        return RC_ROLLBACK_FAILED
    print(f"已从 {backup} 回滚 {ctx.json_file}, 读回 sha256 = {expected}")
    return RC_OK


def _rollback_neo4j(ctx: "_Context", payload: Dict[str, Any]) -> int:
    if ctx.neo4j_uri is None:
        print("ERROR: pre-image 是 Neo4j 目标, 但没给 --neo4j-uri。", file=sys.stderr)
        return RC_REFUSED
    # 同 _rollback_json 的理由 (Codex r1 HIGH-4): 另一个非现网库若恰好有同组同名
    # 的边, 逐条校验会全过 —— 它证明的是"值写成了 pre-image 里的样子", 不是
    # "这是当初被改的那个库"。
    recorded_uri = payload.get("target_uri")
    if recorded_uri != ctx.neo4j_uri or payload.get("database") != ctx.neo4j_database:
        print(
            f"ERROR: pre-image 记录的目标是 {recorded_uri!r}/{payload.get('database')!r}, "
            f"而本次指向 {ctx.neo4j_uri!r}/{ctx.neo4j_database!r} — 拒绝把一份 pre-image 还原到别的库上。",
            file=sys.stderr,
        )
        return RC_REFUSED
    driver, refusal = _open_verified_driver(ctx)
    if refusal is not None:
        print(f"ERROR: {refusal}", file=sys.stderr)
        return RC_REFUSED
    try:
        with _session(driver, ctx) as session:
            failed = _restore_neo4j(session, ctx.group_id, payload.get("rows", []))
        if failed:
            print(f"CRITICAL: 回滚后读回与 pre-image 不符 {failed} — 需人工处置。", file=sys.stderr)
            return RC_ROLLBACK_FAILED
        print(f"已按 pre-image 回滚 {len(payload.get('rows', []))} 行, 逐条读回校验通过。")
        return RC_OK
    finally:
        driver.close()


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migrate_next_review_g38.py",
        description="CARD-G3-8 — 把旧 next_review 对账到 frontmatter fsrs_due 真相源",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="只读只报 (除 --out 外零写入)")
    mode.add_argument("--apply", action="store_true", help="实际对账 (备份 + pre-image + 写完读回)")
    mode.add_argument("--rollback", metavar="PREIMAGE", help="从 pre-image / .bak 逐条还原")

    parser.add_argument("--vault-dir", help="frontmatter 源目录 (只读; 扫 节点/ 与 原白板/)")
    parser.add_argument("--group-id", required=True, help="物理格式组 id, 形如 vault__cs_61b")
    parser.add_argument("--user-id", default=None, help="只处理该 user 的边 (不给则全部用户)")
    parser.add_argument(
        "--group-scope",
        default=None,
        help="要写的是 vault 内二级作用域 (白板级/学科级) 时显式给它的名字; "
        "届时 --group-id 必须逐字等于 vault__<vault_id>__<name>",
    )
    parser.add_argument("--json-file", default=None, help="目标: neo4j_memory.json 的**副本**")
    parser.add_argument("--neo4j-uri", default=None, help="目标: bolt/neo4j URI (⛔ 现网端口一律拒)")
    parser.add_argument("--neo4j-user", default=None)
    parser.add_argument("--neo4j-password", default=None)
    parser.add_argument("--neo4j-database", default=None)
    parser.add_argument("--out", default=None, help="报告 JSON 路径 (dry-run 时是唯一写口)")
    parser.add_argument("--backup-dir", default=None, help="--apply 的备份/pre-image 目录")
    parser.add_argument(
        "--json-naive-tz",
        choices=("local", "utc"),
        default="local",
        help="JSON 镜像里 naive 值的解释口径 (默认 local, 与该文件写/读两侧的契约一致)",
    )
    parser.add_argument("--from-report", default=None, help="dry-run 报告; 给了则断言 group_id 一致")
    parser.add_argument("--card-states-file", default=None, help="fsrs_card_states.json 副本 (**只读**, 只报分歧计数)")
    parser.add_argument(
        "--allow-unbound-vault",
        action="store_true",
        help="--vault-dir 说不出自己的 vault_id (或其形态本脚本算不出物理组名) 时仍允许执行 (默认 fail-closed 拒)",
    )
    parser.add_argument(
        "--allow-unverified-target",
        action="store_true",
        help="目标库 store identity 读不到时仍允许写 (默认 fail-closed 拒)",
    )
    return parser


def _validate(args: argparse.Namespace) -> Optional[str]:
    if not _GROUP_ID_RE.fullmatch(args.group_id or ""):
        return (
            f"--group-id {args.group_id!r} 不是物理格式 —— 必须形如 vault__<id> (双下划线, 无冒号)。"
            " D16 的冒号格式 vault:<id> 是逻辑格式, 库里存的是物理格式。"
        )
    if args.json_file and args.neo4j_uri:
        return "--json-file 与 --neo4j-uri 只能给一个目标。"
    if not args.json_file and not args.neo4j_uri:
        return "必须给一个目标: --json-file 或 --neo4j-uri。"
    if not args.rollback and not args.vault_dir:
        return "--dry-run / --apply 必须给 --vault-dir。"
    if args.from_report:
        try:
            report = json.loads(Path(args.from_report).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return f"--from-report 读不出 {args.from_report}: {exc}"
        if report.get("group_id") != args.group_id:
            return (
                f"--from-report 的 group_id {report.get('group_id')!r} 与 --group-id {args.group_id!r} 不同 —"
                " apply 必须与 dry-run 同组, 拒绝执行。"
            )
    return None


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    err = _validate(args)
    if err is not None:
        print(f"ERROR: {err}", file=sys.stderr)
        return RC_REFUSED

    ctx = _Context(args)

    # dry-run 也要过库面闸: "禁连 7691/7687"是硬边界, 读也不行。
    if ctx.neo4j_uri is not None:
        refusal = assert_target_is_not_live(uri=ctx.neo4j_uri, what="--neo4j-uri")
        if refusal is not None:
            print(f"ERROR: {refusal}", file=sys.stderr)
            return RC_REFUSED

    # 组 ↔ vault 身份绑定 (Codex r1 BLOCKER-1)。rollback 没有 --vault-dir,
    # 它的绑定靠 pre-image 自带的 group_id 与 target_path/target_uri。
    if ctx.vault_dir is not None:
        bind_refusal = assert_group_matches_vault(
            ctx.vault_dir,
            ctx.group_id,
            scope=ctx.group_scope,
            allow_unbound=ctx.allow_unbound_vault,
        )
        if bind_refusal is not None:
            print(f"ERROR: {bind_refusal}", file=sys.stderr)
            return RC_REFUSED

    out_refusal = assert_write_path_is_safe(
        ctx.out, vault_dir=ctx.vault_dir, read_inputs=_read_inputs(ctx), label="--out 的目标"
    )
    if out_refusal is None:
        out_refusal = assert_out_is_safe(ctx.out, ctx.json_file, ctx.card_states_file)
    if out_refusal is not None:
        print(f"ERROR: {out_refusal}", file=sys.stderr)
        return RC_REFUSED

    if args.rollback:
        return run_rollback(ctx, Path(args.rollback))
    if args.apply:
        return run_apply(ctx)
    return run_dry_run(ctx)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
