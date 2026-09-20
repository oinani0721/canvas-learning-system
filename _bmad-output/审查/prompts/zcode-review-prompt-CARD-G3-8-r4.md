# CARD-G3-8 独立补审请求 round-4（BATCH-2026-09-18-第十五批 · 车道 card-p4-fsrs · ZCode/GLM-5.3 通道）

你是独立复核者。只读审查：不要修改任何文件，不要连接任何数据库或网络服务。

仓库根（同时也是你的工作目录）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs`

- **审查绑定**：`ce81e5fa`（本卡最后一个代码 commit）。其后的 HEAD 只新增 `_bmad-output` 文档，两个受审文件与之逐字节相同（已由送审方实测）。
- **送审模式**：build 模式（无 Bash、无写工具）——因此「本卡改动全文」已**内嵌**在本节 §① 内（逐字节原文）；其余参考文件请用读文件工具在树内打开。
- **轮次语境**：本卡此前两轮独立复核（round-1 / round-2）的全部条目已核对成立并整改；本轮 round-4 为目标轮——绑最终 HEAD 的一轮 **BLOCKER/HIGH = 0**。

---

## ① 最小读取面（只读这些，不要泛读全仓）

**1. 本卡改动全文（两个新文件的完整 diff：PREV `49e42626` → 审SHA `ce81e5fa`，逐字节内嵌如下）：**

==== BEGIN EMBEDDED DIFF ====
diff --git a/backend/scripts/migrate_next_review_g38.py b/backend/scripts/migrate_next_review_g38.py
new file mode 100644
index 00000000..99aee538
--- /dev/null
+++ b/backend/scripts/migrate_next_review_g38.py
@@ -0,0 +1,1769 @@
+#!/usr/bin/env python3
+"""CARD-G3-8 — 把旧 ``next_review`` 对账到 frontmatter ``fsrs_due`` 真相源.
+
+[BATCH-2026-09-18-第十五批 / CARD-G3-8]
+
+**为什么需要对账**: 同一个 concept 的「下次复习时间」在系统里由**三个互不相同
+的公式**各自算了一份, D0 T1 裁定 frontmatter 为唯一真相源之后, 旧值从未对过账::
+
+    ① frontmatter fsrs_due          —— FSRS 真相源 (整秒 UTC-Z)
+       vault 侧 FSRS 桥脚本 —— 逐条来源见 census 文档 §一 表格 ①
+    ② Neo4j LEARNED 边 固定 +1 天   —— 与 FSRS 调度完全无关
+       app/clients/neo4j_client.py:1034  r.next_review = datetime() + duration('P1D')
+       app/services/fallback_sync_service.py:774        (重放侧同式)
+       app/clients/neo4j_client.py:718                  (JSON 镜像同式)
+    ③ last_interaction_ts + stability 天 —— 派生式, 不落盘
+       app/services/learning_context_service.py:96-102
+
+本迁移器把 ① 的值对账进 ②。③ 是读时派生, 不在写入面。
+
+**本迁移器绝不做的事** (硬边界):
+
+* **永不写 frontmatter** —— 它是真相源, 反向回填是用户裁定项, 默认不做;
+* **永不写 backend/data/fsrs_card_states.json** —— G3-7 已把它降为投影缓存,
+  本脚本只在报告里列它的 ``due`` 与 ``fsrs_due`` 的分歧计数 (``--card-states-file``);
+* **永不连现网库** —— 端口闸按**解析后的端口**拒 7691 / 7687 (不是子串匹配);
+* **永不写 live vault 子树 / 主仓 JSON 镜像** —— inode 身份 + 路径包含双闸。
+
+设计参照 (DD-04): 备份/校验/还原/互斥模式组抄
+``scripts/migrate_fsrs_card_states_vault_key_g35.py:104-160,350-520,577-660``;
+现网端口与 store identity 双闸抄 ``scripts/migrate_write_identity_g23.py:52-118``;
+frontmatter 字段正则与整秒归一口径抄 ``app/services/review_service.py:146-163``
+(该处又与 vault 侧 FSRS 桥脚本 / ``scripts/daily_review_pick.py:341`` 同款;
+逐条 file:line 见 census 文档 `_bmad-output/审查/evidence-g38/next_review-census.md` §一)。
+
+用法::
+
+    # 只读只报 (除 --out 外零写入)
+    python scripts/migrate_next_review_g38.py --dry-run \\
+        --vault-dir /tmp/vault-copy --group-id vault__cs_61b \\
+        --json-file /tmp/neo4j_memory.copy.json --out /tmp/g38-report.json
+
+    # 实际对账 (双备份 + pre-image + 写完读回 + 失败还原)
+    python scripts/migrate_next_review_g38.py --apply \\
+        --vault-dir /tmp/vault-copy --group-id vault__cs_61b \\
+        --neo4j-uri bolt://127.0.0.1:7692 --backup-dir /tmp/g38-bak \\
+        --out /tmp/g38-apply.json
+
+    # 回滚 (从 pre-image / .bak 逐条还原并读回校验)
+    python scripts/migrate_next_review_g38.py --rollback /tmp/g38-bak/preimage-<ts>.json \\
+        --group-id vault__cs_61b --json-file /tmp/neo4j_memory.copy.json
+
+**退出码约定** (与 g35 :30-38 同口径, 1 与 3 必须分得开)::
+
+    0  成功 (含 "无可写行" 的幂等路径)
+    1  未写入或**已回滚到备份** —— 目标处于迁移前的可信状态
+    2  参数 / 闸拒绝 (组 id 形态非法、目标是现网、--out 与目标同一文件、输入读不出)
+    3  **回滚也失败** —— 目标可能半写, 备份路径在 stderr 里, 需人工处置
+"""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import os
+import re
+import shutil
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any, Dict, List, Optional, Sequence, Tuple
+from urllib.parse import urlsplit
+
+# ── 现网闸常量 ──────────────────────────────────────────────────────────────
+#: 主仓 —— 现网运行时读写的那一棵树。
+LIVE_REPO_ROOT = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system")
+#: live vault —— 落在它下面的**写入**一概拒绝 (部署铁律)。只读扫描不过这道闸。
+LIVE_VAULT_DIR = LIVE_REPO_ROOT / "canvas-vault"
+#: 主仓 JSON 镜像 —— ``neo4j_client.DEFAULT_STORAGE_PATH`` (:54) 指向的那一份。
+LIVE_JSON_MIRROR = LIVE_REPO_ROOT / "backend" / "data" / "neo4j_memory.json"
+#: FSRS 投影缓存 —— 本脚本**只读**它做分歧计数, 任何写入目标落在它上面都拒。
+LIVE_CARD_STATES = LIVE_REPO_ROOT / "backend" / "data" / "fsrs_card_states.json"
+
+#: 现网库端口。7691 = 现网 Neo4j; 7687 = 驱动默认端口 (本机现网开发库也监听它)。
+#: ⚠️ 判据是 ``urlsplit`` **解析后的整数端口**, 不是子串 —— ``:07691`` 与
+#: ``:7691`` 是同一个端口的两种写法, 子串判据只拦得住后者。
+LIVE_DB_PORTS = frozenset({7691, 7687})
+
+#: 可判定去向的 bolt/neo4j scheme。其余 scheme 无法判断落到哪 ⇒ fail-closed 拒。
+ALLOWED_URI_SCHEMES = frozenset({"bolt", "bolt+s", "bolt+ssc", "neo4j", "neo4j+s", "neo4j+ssc"})
+
+#: 现网 (7691) 的 store identity 指纹 —— 抄 g23 :106-108 实测值。端口闸挡不住
+#: 端口转发, 指纹闸挡不住库重建; 两道闸各自覆盖对方的盲区。可用环境变量覆盖。
+KNOWN_LIVE_STORE_IDENTITY = (
+    "C43B910072C97DA5907C9687316EBBCA7F05731C606638B4689AB43B5BC39759::neo4j::2026-05-06T16:44:07.865Z"
+)
+
+#: 节点 ``.md`` 的目录约定 —— 与 ``app/services/frontmatter_signals.py:30``
+#: ``_NODE_DIR_PREFIXES`` 同序 (节点/ 优先, 退 原白板/)。⛔ 不另立目录约定 (D0 T3)。
+NODE_DIR_PREFIXES: Tuple[str, ...] = ("节点", "原白板")
+
+# ── frontmatter 解析 (与生产 reader 逐字同口径) ─────────────────────────────
+#: 只在 frontmatter **块内**取字段 —— 作用在整份 .md 上会把正文里顶格的
+#: ``fsrs_due:`` 当成权威 due (review_service.py:309-311 同款说明)。
+_FM_BLOCK_RE = re.compile("^\\ufeff?" + r"---\r?\n(.*?)\r?\n---\r?\n?(.*)$", re.S)
+#: 字段正则 —— review_service.py:156 / vault 侧 FSRS 桥脚本 / daily_review_pick.py:341
+#: 三处逐字相同。特意不走 PyYAML: live frontmatter 的 fsrs_due 未加引号, PyYAML 的
+#: timestamp resolver 会解析成 datetime, 而整条复习投影链按 UTC-Z **字符串**比较。
+_FM_FIELD_RE = r'^{key}:\s*"?([^"\n]+?)"?\s*$'
+#: 形态门禁 + 解析 —— review_service.py:159-160 同口径。
+_FM_DUE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
+_FM_DUE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
+
+#: 物理格式组 id (``vault__<id>``, 双下划线)。⛔ 本脚本**不自造拼接**组 id
+#: (G4-5 P1 地盘), 只校验调用方给的形态 —— 传错组是跨 vault 写的唯一入口。
+_GROUP_ID_RE = re.compile(r"^vault__[A-Za-z0-9][A-Za-z0-9_\-]*$")
+
+#: vault 自报身份的配置文件 (round-11 扁平架构固化: Skill 一律从它读 vault_id)。
+_VAULT_CONFIG_NAME = ".canvas-config.yaml"
+#: 只取 ``vault_id`` 一个字段 —— 纯 stdlib, 不引 PyYAML (与 frontmatter 读法同策)。
+_VAULT_ID_RE = re.compile(r'^vault_id:\s*"?([^"\n#]+?)"?\s*(?:#.*)?$', re.M)
+#: 能由本脚本自行物理化的 vault_id 形态。非该形态 (如中文 vault 名需 punycode)
+#: 本脚本**算不出**物理组名 —— 算不出就不能假装验过, 按 fail-closed 处理。
+#: ⚠️ 额外排除含 ``__`` 的 vault_id (Codex r2 BLOCKER-1): ``__`` 同时是 vault 内
+#: 二级作用域的分隔符, 于是 ``vault__alpha__beta`` 既可能是 vault ``alpha`` 的
+#: ``beta`` 板, 也可能是 vault ``alpha__beta`` 的根组 —— 单看字符串**分不开**。
+_PLAIN_VAULT_ID_RE = re.compile(r"^(?!.*__)[A-Za-z0-9][A-Za-z0-9_\-]*$")
+#: 二级作用域名同样禁止内嵌 ``__``, 否则同一个歧义在下一层复发。
+_GROUP_SCOPE_RE = re.compile(r"^(?!.*__)[A-Za-z0-9][A-Za-z0-9_\-]*$")
+
+#: ISO 小数秒归一 —— Neo4j ``toString(datetime)`` 给到纳秒 (9 位),
+#: ``datetime.fromisoformat`` 只收 3 / 6 位。
+_ISO_FRACTION_RE = re.compile(r"(\.\d{1,9})")
+
+COUNT_KEYS: Tuple[str, ...] = (
+    "rows_without_target",
+    "governed",
+    "ungoverned",
+    "matched",
+    "unmatched",
+    "unmatched_no_target",
+    "unmatched_no_frontmatter",
+    "noop",
+    "set",
+    "backfill",
+    "ambiguous",
+    "malformed_fsrs_due",
+)
+
+RC_OK = 0
+RC_NOT_WRITTEN = 1
+RC_REFUSED = 2
+RC_ROLLBACK_FAILED = 3
+
+#: 写 UTC-Z (tz-aware) 进 JSON 镜像的**已知下游后果** —— 见 :func:`_json_mirror_warning`。
+WARN_JSON_MIRROR_AWARE_READER = "W-JSON-MIRROR-AWARE-READER"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 路径 / 身份工具 (抄 g35 :66-101)
+# ═══════════════════════════════════════════════════════════════════════════
+def _resolved(path: Path) -> Path:
+    """真实路径 —— 消解符号链接、``..`` 回绕与相对路径。
+
+    ⚠️ 它只解析路径, **不是文件身份**: 同一份文件的硬链接有不同的 resolved 路径
+    却是同一个 inode, 纯路径比对会放行它。文件身份判据见 :func:`_identity`。
+    """
+    try:
+        return path.resolve()
+    except OSError:
+        return path.absolute()
+
+
+def _identity(path: Path) -> Optional[Tuple[int, int]]:
+    """文件身份 = ``(st_dev, st_ino)``; 不存在的文件没有身份 (返回 None)。"""
+    try:
+        st = path.stat()
+    except OSError:
+        return None
+    return (st.st_dev, st.st_ino)
+
+
+def _protected_identities() -> List[Tuple[int, int]]:
+    out: List[Tuple[int, int]] = []
+    for p in (LIVE_JSON_MIRROR, LIVE_CARD_STATES):
+        ident = _identity(p)
+        if ident is not None:
+            out.append(ident)
+    return out
+
+
+def _sha256_file(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def _now_stamp() -> str:
+    return datetime.now().strftime("%Y%m%d_%H%M%S")
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 现网闸 —— 路径面 + 库面的**单一入口**
+# ═══════════════════════════════════════════════════════════════════════════
+def _path_refusal(target: Path, what: str) -> Optional[str]:
+    """路径面: inode 身份 + 路径包含 + 多名字 三道判据 (抄 g35 :104-155)。"""
+    resolved = _resolved(target)
+
+    ident = _identity(target)
+    if ident is not None and ident in _protected_identities():
+        return (
+            f"{what} {resolved} 与**主仓现网**文件是同一个文件 (dev/inode {ident}, "
+            "硬链接或同路径) — 本卡硬边界禁改它。请 cp 到临时目录后指向副本。"
+        )
+
+    for guarded in (LIVE_JSON_MIRROR, LIVE_CARD_STATES):
+        if resolved == _resolved(guarded):
+            return f"{what} {resolved} 是**主仓现网**文件 — 本卡硬边界禁改它。请指向临时副本。"
+
+    live_vault = _resolved(LIVE_VAULT_DIR)
+    if resolved == live_vault or live_vault in resolved.parents:
+        return f"{what} {resolved} 落在 live vault ({live_vault}) 内 — 写它会触发部署铁律, 拒绝执行。"
+
+    if resolved.exists() and not resolved.is_file():
+        return f"{what} {resolved} 不是普通文件, 拒绝执行。"
+
+    # 多名字判据 (g35 :140-155): 受保护 inode 集只收得进**已知**的那几个文件;
+    # 已存在的写入目标若 st_nlink > 1, 它还有别的名字, 而我们无法证明另一个名字
+    # 不在受保护区 —— 拒绝, 而不是带着不确定去截断。正常临时副本 nlink == 1。
+    try:
+        nlink = target.stat().st_nlink
+    except OSError:
+        nlink = 1
+    if nlink > 1:
+        return (
+            f"{what} {resolved} 的硬链接数为 {nlink} — 它在文件系统里还有别的名字, "
+            "无法证明另一个名字不在 live vault / 现网面内。请指向一个独占的普通文件。"
+        )
+    return None
+
+
+def _uri_refusal(uri: str, what: str) -> Optional[str]:
+    """库面: 按**解析后的端口**判现网, 不是子串匹配 (抄 g23 :57-75)。
+
+    子串 ``":7691" in uri`` 会被等价写法绕过 (``:07691`` 数值同端口、URL 编码、
+    大小写主机名)。解析失败 / 无显式端口 / 未知 scheme 一律按"是现网"处理
+    (fail-closed: 拿不准就拒绝)。
+    """
+    try:
+        parsed = urlsplit(uri)
+    except ValueError as exc:
+        return f"{what} {uri!r} 无法解析为 URI ({exc}) — 拿不准去向, 拒绝。"
+
+    scheme = (parsed.scheme or "").lower()
+    if scheme not in ALLOWED_URI_SCHEMES:
+        return (
+            f"{what} {uri!r} 的 scheme {scheme!r} 不在可判定清单 "
+            f"{sorted(ALLOWED_URI_SCHEMES)} 内 — 无法判断它落到哪个库, 拒绝。"
+        )
+
+    try:
+        port = parsed.port
+    except ValueError as exc:
+        return f"{what} {uri!r} 的端口非法 ({exc}) — 拒绝。"
+
+    if port is None:
+        return (
+            f"{what} {uri!r} 未显式指定端口 — 驱动会走默认 7687, 而 7687 在现网端口集 "
+            f"{sorted(LIVE_DB_PORTS)} 内, 拒绝。请写明非现网端口。"
+        )
+    if port in LIVE_DB_PORTS:
+        return (
+            f"{what} {uri!r} 解析后的端口是 {port}, 落在现网端口集 {sorted(LIVE_DB_PORTS)} 内 — 本卡禁连现网库, 拒绝。"
+        )
+    return None
+
+
+def assert_target_is_not_live(
+    target: Optional[Path] = None,
+    uri: Optional[str] = None,
+    what: str = "写入目标",
+) -> Optional[str]:
+    """现网闸的**单一入口** —— 路径面与库面都从这里走.
+
+    做成单一入口而不是两个平行函数, 是为了让"闸恒放行"这一类负控输入能一次性
+    把**全部**闸用例 (live 子树 / 硬链接 / 7691 / :07691 / 省略端口) 打红; 两个
+    平行函数会让负控只覆盖其中一半, 另一半仍绿 = 门未覆盖的路径。
+
+    Returns:
+        None 表示放行; 非 None 为拒绝原因字符串。
+    """
+    if uri is not None:
+        refusal = _uri_refusal(uri, what)
+        if refusal is not None:
+            return refusal
+    if target is not None:
+        refusal = _path_refusal(Path(target), what)
+        if refusal is not None:
+            return refusal
+    return None
+
+
+def read_vault_id(vault_dir: Path) -> Tuple[Optional[str], Optional[str]]:
+    """从 ``<vault>/.canvas-config.yaml`` 读 vault 自报的 ``vault_id``。
+
+    Returns: ``(vault_id, 读不到的原因)``; 两者恰有一个为 None。
+    """
+    cfg = vault_dir / _VAULT_CONFIG_NAME
+    try:
+        text = cfg.read_text(encoding="utf-8")
+    except (OSError, UnicodeDecodeError) as exc:
+        return None, f"{cfg} 读不出 ({type(exc).__name__}: {exc})"
+    m = _VAULT_ID_RE.search(text)
+    if not m or not m.group(1).strip():
+        return None, f"{cfg} 里没有 vault_id 字段"
+    return m.group(1).strip(), None
+
+
+def assert_group_matches_vault(
+    vault_dir: Path,
+    group_id: str,
+    *,
+    scope: Optional[str],
+    allow_unbound: bool,
+) -> Optional[str]:
+    """把 ``--group-id`` 绑到 ``--vault-dir`` **自报**的身份上 (Codex r1 BLOCKER-1).
+
+    形态校验只能证明 ``--group-id`` 长得像个物理组名, **证明不了它属于这个
+    vault**: ``--vault-dir A --group-id vault__B`` 两个参数各自都合法, 合起来却把
+    A 的 ``fsrs_due`` 写进 B 的边。传错组是跨 vault 写的唯一入口, 所以这里要求
+    vault 自己说出它是谁, 再与调用方给的组名对表。
+
+    判据: ``group_id`` 必须**逐字等于** ``vault__<vault_id>``; 要写 vault 内的二级
+    作用域 (D16 的白板级 / 学科级) 必须显式给 ``--group-scope <name>``, 届时判据
+    变成逐字等于 ``vault__<vault_id>__<name>``。
+
+    ⚠️ **为什么不能用前缀放行** (Codex r2 BLOCKER-1): ``__`` 既是 ``vault__`` 的
+    分隔符, 又是二级作用域的分隔符。若按 ``startswith(vault__<id>__)`` 放行, 那么
+    vault ``alpha`` 拿着 ``--group-id vault__alpha__beta`` 会被当成"A 的 beta 板"
+    放行 —— 而它同时**也是** vault ``alpha__beta`` 的根组名。单看字符串这两者分不开,
+    于是逃生门一次都不用开, A 的 due 就落进了 B。逐字相等 + 显式 ``--group-scope``
+    把"我要写哪一层"从推断变成声明。
+
+    ⚠️ **算不出就不放行**: 本脚本不引 app (零 app 导入), 因此无法复用生产的
+    ``to_physical_group_id()`` 的 punycode 物理化。若 ``vault_id`` 不是纯
+    ``[A-Za-z0-9_-]`` 形态 (如中文 vault 名), 本闸**算不出**它的物理组名 ——
+    这种情况按 fail-closed 拒绝, 要放行必须显式 ``--allow-unbound-vault``,
+    而不是默默当成"验过了"。
+    """
+    if scope is not None and not _GROUP_SCOPE_RE.fullmatch(scope):
+        return (
+            f"--group-scope {scope!r} 形态非法 (须 [A-Za-z0-9] 开头, 且**不得内嵌 __**"
+            " —— 内嵌 __ 会让同一个歧义在下一层复发)。"
+        )
+    vault_id, err = read_vault_id(vault_dir)
+    if vault_id is None:
+        if allow_unbound:
+            return None
+        return (
+            f"无法确认 --vault-dir {vault_dir} 的身份: {err}。"
+            " 拿不准这个目录属于哪个 vault 就不能往某个组里写 —— 拒绝执行。"
+            " 确知配对正确时可显式加 --allow-unbound-vault。"
+        )
+    if not _PLAIN_VAULT_ID_RE.fullmatch(vault_id):
+        if allow_unbound:
+            return None
+        return (
+            f"--vault-dir 自报的 vault_id {vault_id!r} 本脚本算不出确定的物理组名"
+            " (非纯 ASCII 时物理化含 punycode, 属 app 侧能力, 本脚本零 app 导入;"
+            " 内嵌 __ 时它与二级作用域分隔符撞车, 单看字符串分不开是哪一层)。"
+            " 算不出就不能假装验过 —— 拒绝执行。确知配对正确时可显式加 --allow-unbound-vault。"
+        )
+    expected = f"vault__{vault_id}" if scope is None else f"vault__{vault_id}__{scope}"
+    if group_id == expected:
+        return None
+    hint = "" if scope is not None else " 要写 vault 内的二级作用域请显式给 --group-scope。"
+    return (
+        f"--group-id {group_id!r} 与 --vault-dir 自报的 vault_id {vault_id!r} 不匹配"
+        f" (应逐字等于 {expected!r})。{hint}"
+        " 这正是把 A vault 的 due 写进 B vault 的那条路径, 拒绝执行。"
+    )
+
+
+def assert_write_path_is_safe(
+    path: Optional[Path],
+    *,
+    vault_dir: Optional[Path],
+    read_inputs: Sequence[Path],
+    label: str,
+) -> Optional[str]:
+    """**所有**写入路径的统一闸 (Codex r1 HIGH-2).
+
+    此前只有 ``--out`` 与写入目标过闸, 于是 ``--dry-run --out <vault>/节点/A.md``
+    会把报告覆盖到源节点上 —— frontmatter 是真相源, 它是本脚本最不该写的东西。
+    备份/pre-image 同理 (它们也是写入路径, 且可以是指向只读输入的符号链接)。
+
+    三道判据:
+      1. 现网闸 (:func:`assert_target_is_not_live`);
+      2. **不得落在 ``--vault-dir`` 子树内** —— 整个子树是只读输入面, 覆盖整棵树
+         比逐个列举扫到的 ``.md`` 更宽 (没被扫到的文件同样不该被写);
+      3. 不得与任何只读输入是同一个文件 (路径相同或 inode 相同)。
+    """
+    if path is None:
+        return None
+    refusal = assert_target_is_not_live(target=path, what=label)
+    if refusal is not None:
+        return refusal
+    resolved = _resolved(path)
+    if vault_dir is not None:
+        vd = _resolved(vault_dir)
+        if resolved == vd or vd in resolved.parents:
+            return f"{label} {resolved} 落在 --vault-dir ({vd}) 子树内 —— 那是**只读**输入面, 拒绝写入。"
+    ident = _identity(path)
+    for other in read_inputs:
+        if _resolved(other) == resolved or (ident is not None and _identity(other) == ident):
+            return f"{label} {resolved} 与只读输入 {other} 是同一个文件, 拒绝写入。"
+    return None
+
+
+def assert_write_dir_is_safe(
+    path: Optional[Path],
+    *,
+    vault_dir: Optional[Path],
+    label: str,
+) -> Optional[str]:
+    """写入**目录**的闸 (Codex r2 MEDIUM-6).
+
+    不能复用 :func:`assert_write_path_is_safe` —— 它内含"已存在且不是普通文件就拒"
+    的判据, 而备份目录第二次跑时**本来就应该已经存在**。那条判据会把正常的第二次
+    apply 拒在门外, 并让幂等负控提前红在 ``rc == 0`` 而不是它声称的计数断言上。
+    """
+    if path is None:
+        return None
+    resolved = _resolved(path)
+    live_vault = _resolved(LIVE_VAULT_DIR)
+    if resolved == live_vault or live_vault in resolved.parents:
+        return f"{label} {resolved} 落在 live vault ({live_vault}) 内 — 写它会触发部署铁律, 拒绝执行。"
+    for guarded in (LIVE_JSON_MIRROR, LIVE_CARD_STATES):
+        g = _resolved(guarded)
+        if resolved == g or g in resolved.parents:
+            return f"{label} {resolved} 与主仓现网文件重叠, 拒绝执行。"
+    if vault_dir is not None:
+        vd = _resolved(vault_dir)
+        if resolved == vd or vd in resolved.parents:
+            return f"{label} {resolved} 落在 --vault-dir ({vd}) 子树内 —— 那是**只读**输入面, 拒绝写入。"
+    if resolved.exists() and not resolved.is_dir():
+        return f"{label} {resolved} 已存在且不是目录, 拒绝执行。"
+    return None
+
+
+def assert_out_is_safe(out: Optional[Path], *others: Optional[Path]) -> Optional[str]:
+    """``--out`` 的写入闸 (抄 g35 :156-205).
+
+    ``--out`` 是**写入路径**: ``--dry-run --json-file X --out X`` 会让报告 JSON
+    覆盖输入快照 —— "dry-run 零写入"不成立, 且没有备份。
+    """
+    if out is None:
+        return None
+    refusal = assert_target_is_not_live(target=out, what="--out 的目标")
+    if refusal is not None:
+        return refusal
+    out_ident = _identity(out)
+    if out_ident is None:
+        out_resolved = _resolved(out)
+        for other in others:
+            if other is not None and _resolved(other) == out_resolved:
+                return f"--out {out_resolved} 与输入/目标是同一个路径 — 报告会覆盖它, 拒绝。"
+        return None
+    for other in others:
+        if other is None:
+            continue
+        if _identity(other) == out_ident:
+            return f"--out {_resolved(out)} 与输入/目标是同一个文件 (dev/inode {out_ident}) — 报告会覆盖它, 拒绝。"
+    return None
+
+
+def fetch_store_identity(driver: Any, database: Optional[str]) -> Optional[str]:
+    """取库的稳定身份 (``db.info().id`` = store id, 与端口/主机无关, g23 :77-93)。"""
+    try:
+        kwargs = {"database": database} if database else {}
+        with driver.session(**kwargs) as session:
+            rec = session.run("CALL db.info() YIELD id, name, creationDate RETURN id, name, creationDate").single()
+        if not rec:
+            return None
+        return f"{rec['id']}::{rec['name']}::{rec['creationDate']}"
+    except Exception:  # noqa: BLE001 — 任何失败都视为"无法自证身份"
+        return None
+
+
+def assert_store_is_not_live(driver: Any, database: Optional[str], allow_unverified: bool) -> Optional[str]:
+    """库身份闸 (g23 :105-160): 端口不是数据库身份, 端口转发能让非现网端口落到现网库。"""
+    known = os.environ.get("NEO4J_LIVE_STORE_ID", KNOWN_LIVE_STORE_IDENTITY)
+    target_id = fetch_store_identity(driver, database)
+    if target_id is None:
+        if allow_unverified:
+            return None
+        return "目标库的 store identity 读不到 — 无法自证它不是现网库, 拒绝写入 (可用 --allow-unverified-target 显式放行)。"
+    if target_id == known:
+        return f"目标库的 store identity 与已知现网库相同 ({target_id}) — 拒绝写入。"
+    return None
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# frontmatter 真相源
+# ═══════════════════════════════════════════════════════════════════════════
+def _whole_second_utc(value: Optional[datetime]) -> Optional[datetime]:
+    """归一到整秒 UTC —— 比较精度必须等于**真相源本身的分辨率**.
+
+    frontmatter 的 fsrs_due 按构造就是整秒 UTC-Z (vault 侧 FSRS 桥脚本的 ``_whole_second()``
+    归一后写出), 而目标侧的值带微秒/纳秒。逐字节比较会让分歧**恒真**, 变成一个
+    永远在响的警报 —— 那比没有信号更糟 (review_service.py:163-176 同款说明)。
+    """
+    if value is None:
+        return None
+    return value.astimezone(timezone.utc).replace(microsecond=0)
+
+
+def parse_frontmatter_due(text: str) -> Dict[str, Any]:
+    """从 ``.md`` 全文抽 ``fsrs_due``。
+
+    Returns:
+        governed:  是否由 frontmatter 真相源管辖 (有 ``fsrs_due`` 即 True)
+        fsrs_due:  原始字符串 (无字段则 None)
+        due:       解析出的 tz-aware datetime; 形态非规范时为 None
+        reason:    'no_fsrs_due' / 'malformed_fsrs_due' / None
+    """
+    out: Dict[str, Any] = {"governed": False, "fsrs_due": None, "due": None, "reason": "no_fsrs_due"}
+    block = _FM_BLOCK_RE.match(text)
+    fm = block.group(1) if block else ""
+    m = re.search(_FM_FIELD_RE.format(key="fsrs_due"), fm, re.M)
+    raw = m.group(1).strip() if m else ""
+    if not raw:
+        return out
+    out["governed"] = True
+    out["fsrs_due"] = raw
+    if not _FM_DUE_SHAPE.fullmatch(raw):
+        out["reason"] = "malformed_fsrs_due"
+        return out
+    try:
+        out["due"] = datetime.strptime(raw, _FM_DUE_FORMAT).replace(tzinfo=timezone.utc)
+        out["reason"] = None
+    except ValueError:
+        # 形态过门但日历非法 (如 2026-13-45T00:00:00Z)
+        out["reason"] = "malformed_fsrs_due"
+    return out
+
+
+def scan_vault(vault_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, str]]]:
+    """扫 ``<vault>/节点/*.md`` 与 ``<vault>/原白板/*.md``, concept_key = 文件 stem.
+
+    同 stem 同时出现在两个目录时按 ``NODE_DIR_PREFIXES`` 的顺序取第一个 (与
+    ``frontmatter_signals._node_md_path`` 同序), 被遮蔽的那份**必须显形**
+    (返回值第二项), ⛔ 不静默丢弃。
+    """
+    entries: Dict[str, Dict[str, Any]] = {}
+    shadowed: List[Dict[str, str]] = []
+    for prefix in NODE_DIR_PREFIXES:
+        sub = vault_dir / prefix
+        if not sub.is_dir():
+            continue
+        for path in sorted(sub.glob("*.md")):
+            stem = path.stem
+            if stem in entries:
+                shadowed.append(
+                    {
+                        "concept_key": stem,
+                        "kept_path": entries[stem]["path"],
+                        "shadowed_path": str(path),
+                    }
+                )
+                continue
+            try:
+                text = path.read_text(encoding="utf-8")
+            except (OSError, UnicodeDecodeError) as exc:
+                # 载体在但内容未知 ⇒ 按"归 frontmatter 管"处理 (fail-closed):
+                # 读不出来 ⇒ **不知道**它说了什么 ⇒ 不能假设它没话说, 更不能
+                # 拿一个读不出的节点去覆盖目标 (review_service.py:298-306 同款)。
+                entries[stem] = {
+                    "path": str(path),
+                    "rel_path": f"{prefix}/{path.name}",
+                    "governed": True,
+                    "fsrs_due": None,
+                    "due": None,
+                    "reason": f"node_file_unreadable: {exc}",
+                }
+                continue
+            parsed = parse_frontmatter_due(text)
+            parsed["path"] = str(path)
+            parsed["rel_path"] = f"{prefix}/{path.name}"
+            entries[stem] = parsed
+    return entries, shadowed
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 目标侧
+# ═══════════════════════════════════════════════════════════════════════════
+def _normalize_iso(value: str) -> str:
+    """把 Neo4j 的纳秒小数秒截到 6 位, ``Z`` 换成 ``+00:00``。"""
+    text = value.strip()
+    if text.endswith(("z", "Z")):
+        text = text[:-1] + "+00:00"
+
+    def _trim(match: "re.Match[str]") -> str:
+        return match.group(1)[:7]
+
+    return _ISO_FRACTION_RE.sub(_trim, text, count=1)
+
+
+def parse_target_value(
+    value: Any,
+    *,
+    naive_tz: str,
+    target_kind: str,
+) -> Tuple[Optional[datetime], Optional[bool], Optional[str]]:
+    """解析目标侧的 ``next_review``。
+
+    Returns:
+        (aware_datetime | None, 是否 naive | None, 失败原因 | None)
+
+    **naive 值的解释口径** (Codex 常问的那条): JSON 镜像里的 naive 值语义是
+    **本地时间** —— ``neo4j_client.py:717-718`` 用 naive 的 ``datetime.now()``
+    写, ``:793/:806`` 又用 naive 的 ``datetime.now()`` 读来比大小, 两侧同为
+    naive 本地 ⇒ 这是该文件代码可证的契约, 不是猜测。可用 ``--json-naive-tz utc``
+    显式改口径, 报告里会写明用的是哪一种。
+
+    Neo4j 目标不享受这条契约: 驱动返回的 ``datetime`` 恒 tz-aware, 真拿到 naive
+    值说明有未知写方 ⇒ 判 ``ambiguous`` **不写**, 而不是猜一个时区。
+    """
+    if value is None or value == "":
+        return None, None, "missing"
+    if not isinstance(value, str):
+        return None, None, f"unexpected_type:{type(value).__name__}"
+    try:
+        parsed = datetime.fromisoformat(_normalize_iso(value))
+    except ValueError:
+        return None, None, "unparsable"
+    if parsed.tzinfo is not None:
+        return parsed, False, None
+    if target_kind == "json" and naive_tz == "utc":
+        return parsed.replace(tzinfo=timezone.utc), True, None
+    if target_kind == "json" and naive_tz == "local":
+        # ⚠️ 夏令时边界上, naive 本地时刻**本身就不是一个确定的时刻**
+        # (Codex r1 MEDIUM-8)。秋令回拨那一小时出现两次, 两次相差整 1 小时;
+        # 春令跳过的那一小时根本不存在。默默归一会把一小时的**真分歧**判成
+        # noop —— 那正是本卡要消灭的那种静默。判据: fold=0 与 fold=1 落到不同
+        # 的 UTC 时刻 ⇒ 这个本地串对应不止一个时刻 ⇒ 不写, 显形为 ambiguous。
+        fold0 = parsed.replace(fold=0).astimezone(timezone.utc)
+        fold1 = parsed.replace(fold=1).astimezone(timezone.utc)
+        if fold0 != fold1:
+            # 再区分是"重复"还是"不存在": 不存在的本地时刻往返回来会变成别的值。
+            roundtrip = parsed.astimezone().replace(tzinfo=None)
+            why = "nonexistent_local_time" if roundtrip != parsed else "ambiguous_local_time"
+            return None, True, why
+        return fold0, True, None
+    return None, True, "naive_without_proven_contract"
+
+
+def collect_json_targets(
+    raw: Dict[str, Any],
+    group_id: str,
+    user_id: Optional[str],
+) -> List[Dict[str, Any]]:
+    """JSON 镜像目标行 —— 行身份 = ``(user_id, concept_name, group_id)`` 三元组.
+
+    与写方 ``neo4j_client.py:721-726`` 的匹配键逐字同。``--user-id`` 未给时枚举
+    全部用户, 每条关系各出一行 (行身份仍是三元组, 不是把不同用户的边揉成一条)。
+    ``group_id`` 是**等值**过滤而不是前缀: 这是写身份面 (W1), 不是读召回面。
+    """
+    rows: List[Dict[str, Any]] = []
+    for position, rel in enumerate(raw.get("relationships", [])):
+        if not isinstance(rel, dict):
+            continue
+        if rel.get("group_id") != group_id:
+            continue
+        if user_id is not None and rel.get("user_id") != user_id:
+            continue
+        rows.append(
+            {
+                "concept_key": rel.get("concept_name"),
+                "user_id": rel.get("user_id"),
+                "group_id": rel.get("group_id"),
+                "value": rel.get("next_review"),
+                # ⚠️ 行身份带**位置**而不是只带三元组: 旧数据里可能存在重复的
+                # (user_id, concept_name, group_id) —— 写方 :721-726 用 next(...)
+                # 只更新第一条, 于是重复行能长期并存。按三元组建索引会把它们塌成
+                # 一条, 结果是"判 noop 的那一条被连带写入、报告里却没有它"。
+                "target_index": position,
+            }
+        )
+    return rows
+
+
+_NEO4J_READ_QUERY = (
+    "MATCH (u:User)-[r:LEARNED]->(c:Concept) "
+    "WHERE c.group_id = $gid AND r.group_id = $gid "
+    "AND ($uid IS NULL OR u.id = $uid) "
+    "RETURN u.id AS user_id, c.name AS concept_key, "
+    "toString(r.next_review) AS next_review"
+)
+
+_NEO4J_WRITE_QUERY = (
+    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $cname}) "
+    "WHERE c.group_id = $gid AND r.group_id = $gid "
+    "SET r.next_review = datetime($due) "
+    "RETURN toString(r.next_review) AS next_review"
+)
+
+_NEO4J_CLEAR_QUERY = (
+    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept {name: $cname}) "
+    "WHERE c.group_id = $gid AND r.group_id = $gid "
+    "REMOVE r.next_review "
+    "RETURN toString(r.next_review) AS next_review"
+)
+
+
+def collect_neo4j_targets(session: Any, group_id: str, user_id: Optional[str]) -> List[Dict[str, Any]]:
+    """Neo4j ``LEARNED`` 边目标行 —— ``c`` 与 ``r`` **两个 alias 都过滤** (R1 全覆盖)。"""
+    rows: List[Dict[str, Any]] = []
+    for rec in session.run(_NEO4J_READ_QUERY, gid=group_id, uid=user_id):
+        rows.append(
+            {
+                "concept_key": rec["concept_key"],
+                "user_id": rec["user_id"],
+                "group_id": group_id,
+                "value": rec["next_review"],
+                "ref": None,
+            }
+        )
+    return rows
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 分类
+# ═══════════════════════════════════════════════════════════════════════════
+def _row(
+    concept_key: str,
+    entry: Optional[Dict[str, Any]],
+    target: Optional[Dict[str, Any]],
+    *,
+    action: str,
+    unmatched_kind: Optional[str] = None,
+    reason: Optional[str] = None,
+    target_naive: Optional[bool] = None,
+    new_next_review: Optional[str] = None,
+) -> Dict[str, Any]:
+    return {
+        "node_id": (entry or {}).get("rel_path"),
+        "concept_key": concept_key,
+        "user_id": (target or {}).get("user_id"),
+        "group_id": (target or {}).get("group_id"),
+        "frontmatter_fsrs_due": (entry or {}).get("fsrs_due"),
+        "target_next_review": (target or {}).get("value"),
+        # 身份映射是否对上 —— 与 action 正交的一维 (Codex r1 MEDIUM-10):
+        # due 坏掉的节点归 malformed_fsrs_due, 但"它在目标侧也没有边"这件事
+        # 不能因此消失。每行都带这个标, 任何 action 下都看得见。
+        "target_missing": target is None,
+        "target_index": (target or {}).get("target_index"),
+        "target_naive": target_naive,
+        "action": action,
+        "unmatched_kind": unmatched_kind,
+        "reason": reason,
+        "new_next_review": new_next_review,
+    }
+
+
+def classify_rows(
+    entries: Dict[str, Dict[str, Any]],
+    targets: Sequence[Dict[str, Any]],
+    *,
+    naive_tz: str,
+    target_kind: str,
+) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
+    """把 frontmatter 侧与目标侧做**并集**枚举并逐行定性.
+
+    并集而不是单向枚举: 身份映射可能在**两个方向**失败 —— governed 节点在目标
+    侧没有边 (``no_target``), 目标侧的边没有任何 ``.md`` 载体 (``no_frontmatter``)。
+    两种都必须显形为 ``unmatched``, ⛔ 不静默跳过 (少了哪一边都会让"对账"漏掉
+    真实存在的孤儿数据)。
+    """
+    counts: Dict[str, int] = {k: 0 for k in COUNT_KEYS}
+    rows: List[Dict[str, Any]] = []
+
+    by_key: Dict[str, List[Dict[str, Any]]] = {}
+    for tgt in targets:
+        by_key.setdefault(str(tgt["concept_key"]), []).append(tgt)
+
+    for key in sorted(entries):
+        entry = entries[key]
+        matched = by_key.get(key, [])
+        if not entry["governed"]:
+            counts["ungoverned"] += 1
+            rows.append(
+                _row(
+                    key,
+                    entry,
+                    matched[0] if matched else None,
+                    action="ungoverned",
+                    reason=entry.get("reason"),
+                )
+            )
+            continue
+
+        counts["governed"] += 1
+        if entry.get("due") is None:
+            counts["malformed_fsrs_due"] += 1
+            rows.append(
+                _row(
+                    key,
+                    entry,
+                    matched[0] if matched else None,
+                    action="malformed_fsrs_due",
+                    reason=entry.get("reason"),
+                )
+            )
+            continue
+
+        if not matched:
+            counts["unmatched"] += 1
+            counts["unmatched_no_target"] += 1
+            rows.append(_row(key, entry, None, action="unmatched", unmatched_kind="no_target"))
+            continue
+
+        counts["matched"] += 1
+        for tgt in matched:
+            parsed, naive, why = parse_target_value(tgt["value"], naive_tz=naive_tz, target_kind=target_kind)
+            if why == "missing":
+                counts["backfill"] += 1
+                rows.append(
+                    _row(key, entry, tgt, action="backfill", target_naive=naive, new_next_review=entry["fsrs_due"])
+                )
+                continue
+            if parsed is None:
+                counts["ambiguous"] += 1
+                rows.append(_row(key, entry, tgt, action="ambiguous", reason=why, target_naive=naive))
+                continue
+            if _whole_second_utc(parsed) == _whole_second_utc(entry["due"]):
+                counts["noop"] += 1
+                rows.append(_row(key, entry, tgt, action="noop", target_naive=naive))
+            else:
+                counts["set"] += 1
+                rows.append(_row(key, entry, tgt, action="set", target_naive=naive, new_next_review=entry["fsrs_due"]))
+
+    for key in sorted(by_key):
+        if key in entries:
+            continue
+        for tgt in by_key[key]:
+            counts["unmatched"] += 1
+            counts["unmatched_no_frontmatter"] += 1
+            rows.append(_row(key, None, tgt, action="unmatched", unmatched_kind="no_frontmatter"))
+
+    # 与 action 正交的一维: 有多少行在目标侧压根没有对应的边。
+    # `unmatched_no_target` 只数**有效 due** 的那些; 本计数把 malformed /
+    # 读不出的 governed 节点也算进来, 于是"身份没对上"不会因为节点自身的
+    # 毛病而从报告里消失 (Codex r1 MEDIUM-10)。
+    counts["rows_without_target"] = sum(1 for r in rows if r["target_missing"])
+
+    return rows, counts
+
+
+def card_states_divergence(path: Path, entries: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
+    """**只读**统计 ``fsrs_card_states.json`` 的 ``due`` 与 ``fsrs_due`` 的分歧.
+
+    G3-7 已把该文件降为**投影缓存**, 本脚本只报数、⛔ 永不写它。
+    """
+    out: Dict[str, Any] = {"file": str(path), "compared": 0, "diverged": 0, "unparsable": 0, "concepts": []}
+    try:
+        raw = json.loads(path.read_text(encoding="utf-8"))
+    except (OSError, ValueError) as exc:
+        out["error"] = f"{type(exc).__name__}: {exc}"
+        return out
+    if not isinstance(raw, dict):
+        out["error"] = "顶层不是对象"
+        return out
+    for bucket in raw.values():
+        if not isinstance(bucket, dict):
+            continue
+        for concept_id, card_json in bucket.items():
+            entry = entries.get(concept_id)
+            if entry is None or entry.get("due") is None:
+                continue
+            try:
+                card = json.loads(card_json) if isinstance(card_json, str) else card_json
+                due_raw = card.get("due") if isinstance(card, dict) else None
+                parsed = datetime.fromisoformat(_normalize_iso(str(due_raw)))
+            except (ValueError, AttributeError, TypeError):
+                out["unparsable"] += 1
+                continue
+            if parsed.tzinfo is None:
+                parsed = parsed.replace(tzinfo=timezone.utc)
+            out["compared"] += 1
+            if _whole_second_utc(parsed) != _whole_second_utc(entry["due"]):
+                out["diverged"] += 1
+                out["concepts"].append(concept_id)
+    return out
+
+
+def _json_mirror_warning() -> Dict[str, str]:
+    """写 UTC-Z (tz-aware) 进 JSON 镜像的**已知下游后果** —— 显形而不是静默制造。
+
+    ``neo4j_client.py:806-808`` 用 naive 的 ``datetime.now()`` 与读出的值比大小;
+    值是 tz-aware 时抛 ``TypeError``, 被 ``:833`` 的
+    ``except (ValueError, TypeError): continue`` **静默跳过** —— 该 concept 会从
+    JSON 降级路径的复习建议里消失。修那一侧属 P1/P2 地盘, 不在本卡范围, 所以
+    在报告里如实报出来。
+    """
+    return {
+        "code": WARN_JSON_MIRROR_AWARE_READER,
+        "detail": (
+            "写入 JSON 镜像的值是整秒 UTC-Z (tz-aware); "
+            "app/clients/neo4j_client.py:806-808 用 naive 的 datetime.now() 与它比大小会抛 TypeError, "
+            "被 :833 的 except (ValueError, TypeError): continue 静默跳过 —— "
+            "该 concept 会从 JSON 降级路径的复习建议里消失。"
+            "修读方属 P1/P2 地盘, 不在 CARD-G3-8 范围, 此处只如实报出。"
+        ),
+    }
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 报告
+# ═══════════════════════════════════════════════════════════════════════════
+def build_report(
+    mode: str,
+    *,
+    group_id: str,
+    user_id: Optional[str],
+    target_kind: str,
+    target_ref: str,
+    vault_dir: Optional[Path],
+    naive_tz: str,
+    entries: Dict[str, Dict[str, Any]],
+    json_file: Optional[Path],
+    rows: List[Dict[str, Any]],
+    counts: Dict[str, int],
+    shadowed: List[Dict[str, str]],
+) -> Dict[str, Any]:
+    inputs: Dict[str, str] = {}
+    for entry in entries.values():
+        path = Path(entry["path"])
+        try:
+            inputs[entry["rel_path"]] = _sha256_file(path)
+        except OSError:
+            inputs[entry["rel_path"]] = "<unreadable>"
+    if json_file is not None:
+        try:
+            inputs["__json_file__"] = _sha256_file(json_file)
+        except OSError:
+            inputs["__json_file__"] = "<unreadable>"
+
+    warnings: List[Dict[str, str]] = []
+    if target_kind == "json" and (counts["set"] + counts["backfill"]) > 0:
+        warnings.append(_json_mirror_warning())
+
+    return {
+        "card": "CARD-G3-8",
+        "mode": mode,
+        "group_id": group_id,
+        "user_id": user_id,
+        "target_kind": target_kind,
+        "target": target_ref,
+        "vault_dir": str(vault_dir) if vault_dir is not None else None,
+        "naive_interpretation": naive_tz,
+        "inputs_sha256": inputs,
+        "counts": counts,
+        "rows": rows,
+        "shadowed": shadowed,
+        "warnings": warnings,
+    }
+
+
+def write_report_checked(
+    ctx: "_Context",
+    bundle: Optional[Dict[str, Any]],
+    payload: Dict[str, Any],
+) -> Tuple[bool, Optional[str]]:
+    """写报告前**用扫到的真实节点清单**再核一次 ``--out`` (Codex r2 HIGH-4).
+
+    ``main`` 里那次核查发生在扫描之前, 手里只有 ``--card-states-file``; 而
+    ``vault/节点/A.md`` 可以是指向 vault **外**某个文件的符号链接 —— 那个文件既
+    不在 ``--vault-dir`` 子树内, 也不在当时的只读输入清单里, 于是
+    ``--out <那个文件>`` 能穿过第一道核查, 在报告落盘时覆盖真相源。
+    扫完之后我们才真正知道读了哪些文件, 这一次核查用的是那份实测清单。
+    """
+    refusal = assert_write_path_is_safe(
+        ctx.out,
+        vault_dir=ctx.vault_dir,
+        read_inputs=_read_inputs(ctx, bundle),
+        label="--out 的目标",
+    )
+    if refusal is not None:
+        return False, refusal
+    return write_report(ctx.out, payload), None
+
+
+def write_report(out: Optional[Path], payload: Dict[str, Any]) -> bool:
+    if out is None:
+        return False
+    try:
+        out.parent.mkdir(parents=True, exist_ok=True)
+        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+    except OSError as exc:
+        print(f"ERROR: 报告写入失败 {out}: {exc}", file=sys.stderr)
+        return False
+    return True
+
+
+def _print_summary(title: str, ctx: "_Context", counts: Dict[str, int]) -> None:
+    print("=" * 68)
+    print(title)
+    print("=" * 68)
+    print(f"vault    : {ctx.vault_dir if ctx.vault_dir is not None else '(未给, rollback 模式)'}")
+    print(f"group_id : {ctx.group_id}")
+    print(f"user_id  : {ctx.user_id if ctx.user_id else '(全部)'}")
+    print(f"目标     : {ctx.target_kind} {ctx.target_ref}")
+    print(f"naive 解释: {ctx.naive_tz}")
+    print("-" * 68)
+    for key in COUNT_KEYS:
+        print(f"  {key:<26}: {counts[key]}")
+    print("=" * 68)
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 运行上下文
+# ═══════════════════════════════════════════════════════════════════════════
+class _Context:
+    """一次运行需要的全部解析结果 —— 三个 ``run_*`` 共用。"""
+
+    def __init__(self, args: argparse.Namespace) -> None:
+        self.group_id: str = args.group_id
+        self.user_id: Optional[str] = args.user_id
+        self.vault_dir: Optional[Path] = Path(args.vault_dir) if args.vault_dir else None
+        self.json_file: Optional[Path] = Path(args.json_file) if args.json_file else None
+        self.neo4j_uri: Optional[str] = args.neo4j_uri
+        self.neo4j_user: Optional[str] = args.neo4j_user
+        self.neo4j_password: Optional[str] = args.neo4j_password
+        self.neo4j_database: Optional[str] = args.neo4j_database
+        self.naive_tz: str = args.json_naive_tz
+        self.out: Optional[Path] = Path(args.out) if args.out else None
+        self.backup_dir: Optional[Path] = Path(args.backup_dir) if args.backup_dir else None
+        self.allow_unverified: bool = args.allow_unverified_target
+        self.allow_unbound_vault: bool = args.allow_unbound_vault
+        self.group_scope: Optional[str] = args.group_scope
+        self.card_states_file: Optional[Path] = Path(args.card_states_file) if args.card_states_file else None
+
+    @property
+    def target_kind(self) -> str:
+        return "json" if self.json_file is not None else "neo4j"
+
+    @property
+    def target_ref(self) -> str:
+        return str(self.json_file) if self.json_file is not None else str(self.neo4j_uri)
+
+
+def _neo4j_driver(ctx: "_Context") -> Any:
+    """延迟 import —— 只有真给了 ``--neo4j-uri`` 才需要驱动 (纯 stdlib 原则)。
+
+    URI 为空时**当场炸**而不是把 None 交给驱动: 驱动拿到 None 会用它自己的默认
+    路由 (7687 = 现网端口集内), 等于绕过了 :func:`assert_target_is_not_live` ——
+    fail-closed 比让驱动"帮忙猜一个地址"安全。
+    """
+    from neo4j import GraphDatabase
+
+    if not ctx.neo4j_uri:
+        raise ValueError("内部错误: 没有 --neo4j-uri 却要建驱动 — 拒绝让驱动走默认路由。")
+    auth = None
+    if ctx.neo4j_user is not None:
+        auth = (ctx.neo4j_user, ctx.neo4j_password or "")
+    return GraphDatabase.driver(ctx.neo4j_uri, auth=auth)
+
+
+def _session(driver: Any, ctx: "_Context") -> Any:
+    return driver.session(database=ctx.neo4j_database) if ctx.neo4j_database else driver.session()
+
+
+def _open_verified_driver(ctx: "_Context") -> Tuple[Any, Optional[str]]:
+    """建驱动并**在任何业务读之前**核库身份 (Codex r1 HIGH-5).
+
+    端口不是数据库身份: 端口转发 / 路由种子可以让 ``7692`` 落到现网库。此前
+    身份闸只在写之前跑, 而 ``--dry-run`` 与 ``--apply`` 的 ``_gather`` 都已经
+    先读了一轮业务数据 —— 「禁连现网」被读侧绕开了。现在**每一条**进出库的路径
+    都从这里拿驱动, 身份不过关就拿不到可用的连接。
+
+    唯一先于身份闸发生的查询是 ``CALL db.info()`` 自身 (身份证据只能从库里取),
+    它不读任何业务数据。
+    """
+    driver = _neo4j_driver(ctx)
+    refusal = assert_store_is_not_live(driver, ctx.neo4j_database, ctx.allow_unverified)
+    if refusal is not None:
+        driver.close()
+        return None, refusal
+    return driver, None
+
+
+def _load_json_mirror(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
+    try:
+        raw = json.loads(path.read_text(encoding="utf-8"))
+    except OSError as exc:
+        return None, f"JSON 镜像读不出 {path}: {exc}"
+    except ValueError as exc:
+        return None, f"JSON 镜像不是合法 JSON {path}: {exc}"
+    if not isinstance(raw, dict) or not isinstance(raw.get("relationships"), list):
+        return None, f"JSON 镜像形态非法 (缺 relationships 列表): {path}"
+    return raw, None
+
+
+def _gather(ctx: "_Context") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
+    """扫 frontmatter + 读目标 + 定性。返回 (bundle, 错误)。"""
+    if ctx.vault_dir is None or not ctx.vault_dir.is_dir():
+        return None, f"--vault-dir 不是目录: {ctx.vault_dir}"
+    entries, shadowed = scan_vault(ctx.vault_dir)
+
+    raw: Optional[Dict[str, Any]] = None
+    if ctx.json_file is not None:
+        raw, err = _load_json_mirror(ctx.json_file)
+        if err is not None:
+            return None, err
+        assert raw is not None
+        targets = collect_json_targets(raw, ctx.group_id, ctx.user_id)
+        rows, counts = classify_rows(entries, targets, naive_tz=ctx.naive_tz, target_kind="json")
+    else:
+        driver, refusal = _open_verified_driver(ctx)
+        if refusal is not None:
+            return None, refusal
+        try:
+            with _session(driver, ctx) as session:
+                targets = collect_neo4j_targets(session, ctx.group_id, ctx.user_id)
+        finally:
+            driver.close()
+        rows, counts = classify_rows(entries, targets, naive_tz=ctx.naive_tz, target_kind="neo4j")
+
+    return {"entries": entries, "shadowed": shadowed, "rows": rows, "counts": counts, "raw": raw}, None
+
+
+def _report_for(ctx: "_Context", mode: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
+    report = build_report(
+        mode,
+        group_id=ctx.group_id,
+        user_id=ctx.user_id,
+        target_kind=ctx.target_kind,
+        target_ref=ctx.target_ref,
+        vault_dir=ctx.vault_dir,
+        naive_tz=ctx.naive_tz,
+        entries=bundle["entries"],
+        json_file=ctx.json_file,
+        rows=bundle["rows"],
+        counts=bundle["counts"],
+        shadowed=bundle["shadowed"],
+    )
+    if ctx.card_states_file is not None:
+        report["card_states_divergence"] = card_states_divergence(ctx.card_states_file, bundle["entries"])
+    return report
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 模式 ①: dry-run —— 除 --out 外零写入
+# ═══════════════════════════════════════════════════════════════════════════
+def run_dry_run(ctx: "_Context") -> int:
+    bundle, err = _gather(ctx)
+    if err is not None:
+        print(f"ERROR: {err}", file=sys.stderr)
+        return RC_REFUSED
+    assert bundle is not None
+    report = _report_for(ctx, "dry-run", bundle)
+    _print_summary("CARD-G3-8 next_review 对账 — DRY-RUN (零写入)", ctx, bundle["counts"])
+    for warning in report["warnings"]:
+        print(f"⚠️ {warning['code']}: {warning['detail']}")
+    wrote, refusal = write_report_checked(ctx, bundle, report)
+    if refusal is not None:
+        print(f"ERROR: {refusal}", file=sys.stderr)
+        return RC_REFUSED
+    if wrote:
+        print(f"报告已写: {ctx.out} (本次唯一的文件写入)")
+    return RC_OK
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 模式 ②: apply —— pre-image → 写 → 读回校验 → 失败还原
+# ═══════════════════════════════════════════════════════════════════════════
+def _read_inputs(ctx: "_Context", bundle: Optional[Dict[str, Any]] = None) -> List[Path]:
+    """本次运行的**只读**输入文件清单 —— 任何写入路径都不得与它们重合。"""
+    out: List[Path] = []
+    if bundle is not None:
+        out.extend(Path(e["path"]) for e in bundle["entries"].values())
+    if ctx.card_states_file is not None:
+        out.append(ctx.card_states_file)
+    return out
+
+
+def _write_preimage(
+    ctx: "_Context",
+    payload: Dict[str, Any],
+    read_inputs: Sequence[Path],
+) -> Tuple[Optional[Path], Optional[str]]:
+    assert ctx.backup_dir is not None
+    path = ctx.backup_dir / f"preimage-{_now_stamp()}.json"
+    # ⚠️ 闸必须排在 mkdir **前面** (Codex r1 MEDIUM-9): 先建目录再检查, 等于
+    # 已经在 live vault 里落了一个目录才说"这里不能写"。
+    # ⚠️ 备份**目录**不能走 assert_write_path_is_safe —— 它含"已存在且不是普通文件
+    # 就拒"的判据, 会把第二次 apply 时**本来就应该存在**的目录拒在门外
+    # (Codex r2 MEDIUM-6)。目录用目录闸。
+    refusal = assert_write_dir_is_safe(ctx.backup_dir, vault_dir=ctx.vault_dir, label="--backup-dir")
+    if refusal is not None:
+        return None, refusal
+    refusal = assert_write_path_is_safe(
+        path, vault_dir=ctx.vault_dir, read_inputs=read_inputs, label="pre-image 的目标"
+    )
+    if refusal is not None:
+        return None, refusal
+    try:
+        ctx.backup_dir.mkdir(parents=True, exist_ok=True)
+    except OSError as exc:
+        return None, f"备份目录建不出来 {ctx.backup_dir}: {exc}"
+    # pre-image 也是**写入路径**, 同样怕别名 (g35 的 --out 别名教训同型):
+    # 报告在 apply 末尾才写, 若 --out 指到同一个位置, 它会**在写入成功之后**
+    # 把刚落盘的 pre-image 覆盖成统计报告 —— 回滚依据就没了。
+    for other, label in ((ctx.out, "--out"), (ctx.json_file, "--json-file")):
+        if other is not None and _resolved(other) == _resolved(path):
+            return None, f"pre-image 路径 {_resolved(path)} 与 {label} 是同一个位置 — 回滚依据会被覆盖, 拒绝执行。"
+    try:
+        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+    except OSError as exc:
+        return None, f"pre-image 落盘失败 {path}: {exc}"
+    return path, None
+
+
+def _apply_json(ctx: "_Context", bundle: Dict[str, Any], writable: List[Dict[str, Any]]) -> int:
+    assert ctx.json_file is not None
+    target = ctx.json_file
+    before_sha = _sha256_file(target)
+
+    # 双备份 (抄 g35 :404-440): 备份自身失败 = 还没动源文件就停手。
+    # 备份路径也是**写入路径**, 必须过同一道闸。
+    stamped = target.with_suffix(f"{target.suffix}.bak.{_now_stamp()}")
+    simple = target.with_suffix(f"{target.suffix}.bak")
+    if _resolved(stamped) == _resolved(simple):
+        print("ERROR: 时间戳备份与简单备份指向同一位置 — 双备份会退化成一份, 已中止。", file=sys.stderr)
+        return RC_REFUSED
+    read_inputs = _read_inputs(ctx, bundle)
+    # --out 在 apply **末尾**才写: 它若别名到本次备份, 一次成功的迁移结束时
+    # 回滚依据已被统计报告顶掉 (Codex r2 MEDIUM-8, 与 pre-image 同型)。
+    for backup in (stamped, simple):
+        if ctx.out is not None and _resolved(ctx.out) == _resolved(backup):
+            print(
+                f"ERROR: --out {_resolved(ctx.out)} 与本次备份是同一个位置 — 报告会覆盖回滚依据, 拒绝执行。",
+                file=sys.stderr,
+            )
+            return RC_REFUSED
+    for backup in (stamped, simple):
+        refusal = assert_write_path_is_safe(
+            backup, vault_dir=ctx.vault_dir, read_inputs=read_inputs, label="备份的目标"
+        )
+        if refusal is not None:
+            print(f"ERROR: {refusal}", file=sys.stderr)
+            return RC_REFUSED
+    try:
+        shutil.copy2(target, stamped)
+        shutil.copy2(target, simple)
+    except OSError as exc:
+        print(f"ERROR: 备份失败 ({exc}) — 源文件未改动, 已中止。", file=sys.stderr)
+        return RC_NOT_WRITTEN
+
+    preimage_payload = {
+        "card": "CARD-G3-8",
+        "mode": "pre-image",
+        "group_id": ctx.group_id,
+        "user_id": ctx.user_id,
+        "target_kind": "json",
+        "target_path": str(target),
+        "target_sha256_before": before_sha,
+        "backups": {"stamped": str(stamped), "simple": str(simple)},
+        "rows": [
+            {
+                "concept_key": row["concept_key"],
+                "user_id": row["user_id"],
+                "old_next_review": row["target_next_review"],
+                "new_next_review": row["new_next_review"],
+            }
+            for row in writable
+        ],
+    }
+    preimage_path, err = _write_preimage(ctx, preimage_payload, read_inputs)
+    if err is not None:
+        print(f"ERROR: {err} — pre-image 落盘成功才允许开写, 源文件未改动。", file=sys.stderr)
+        return RC_NOT_WRITTEN
+
+    raw = bundle["raw"]
+    relationships = raw.get("relationships", [])
+    for row in writable:
+        position = row["target_index"]
+        if position is None or not isinstance(position, int) or position >= len(relationships):
+            print(f"ERROR: 行 {row['concept_key']} 的位置索引失效 ({position}) — 还原到备份。", file=sys.stderr)
+            return _restore_json(target, stamped, before_sha)
+        relationships[position]["next_review"] = row["new_next_review"]
+
+    try:
+        target.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
+    except OSError as exc:
+        print(f"ERROR: 写入失败 {target}: {exc}", file=sys.stderr)
+        return _restore_json(target, stamped, before_sha)
+
+    # 写完**读回执**, 不用"没抛异常即成功" (G-FAKE 教训)。
+    verified, err = _load_json_mirror(target)
+    if err is not None or verified is None:
+        print(f"ERROR: 写后重读失败 ({err}) — 还原到备份。", file=sys.stderr)
+        return _restore_json(target, stamped, before_sha)
+    reread = verified["relationships"]
+    bad = [
+        f"{row['user_id']}/{row['concept_key']}@{row['target_index']}"
+        for row in writable
+        if row["target_index"] >= len(reread)
+        or reread[row["target_index"]].get("next_review") != row["new_next_review"]
+    ]
+    if bad:
+        print(f"ERROR: 写后读回与期望不符 {bad} — 还原到备份。", file=sys.stderr)
+        return _restore_json(target, stamped, before_sha)
+
+    print(f"已写 {len(writable)} 行; 备份: {stamped} / {simple}; pre-image: {preimage_path}")
+    bundle["preimage_path"] = str(preimage_path)
+    return RC_OK
+
+
+def _restore_json(target: Path, backup: Path, expected_sha: str) -> int:
+    try:
+        shutil.copy2(backup, target)
+        if _sha256_file(target) != expected_sha:
+            raise OSError("还原后的 sha256 与迁移前不符")
+    except OSError as exc:
+        print(
+            f"CRITICAL: 回滚也失败 ({exc}) — 目标 {target} 可能半写, 备份在 {backup}, 需人工处置。",
+            file=sys.stderr,
+        )
+        return RC_ROLLBACK_FAILED
+    print(f"已回滚到备份 {backup} — 目标处于迁移前的可信状态。", file=sys.stderr)
+    return RC_NOT_WRITTEN
+
+
+def _restore_neo4j(session: Any, group_id: str, rows: Sequence[Dict[str, Any]]) -> List[str]:
+    """按 pre-image 逐条把 ``next_review`` 放回去, 返回**没能还原**的行标识.
+
+    读回执用**精确时刻**比 (不是整秒): 还原要证明的是"回到原样", 原值可能带
+    亚秒精度, 整秒比较会把丢掉的小数秒当成还原成功 (Codex r1 Q1 末段)。
+    """
+    failed: List[str] = []
+    for row in rows:
+        old = row.get("old_next_review")
+        ident = f"{row.get('user_id')}/{row.get('concept_key')}"
+        params: Dict[str, Any] = {
+            "uid": row.get("user_id"),
+            "cname": row.get("concept_key"),
+            "gid": group_id,
+        }
+        query = _NEO4J_CLEAR_QUERY if old in (None, "") else _NEO4J_WRITE_QUERY
+        if old not in (None, ""):
+            params["due"] = old
+        try:
+            rec = session.run(query, **params).single()
+        except Exception as exc:  # noqa: BLE001 — 还原期任何异常都算没还原成功
+            failed.append(f"{ident} ({type(exc).__name__}: {exc})")
+            continue
+        got = rec["next_review"] if rec is not None else None
+        ok = (rec is not None and got is None) if old in (None, "") else _same_instant_exact(got, old)
+        if not ok:
+            failed.append(ident)
+    return failed
+
+
+def _apply_neo4j(ctx: "_Context", bundle: Dict[str, Any], writable: List[Dict[str, Any]]) -> int:
+    driver, refusal = _open_verified_driver(ctx)
+    if refusal is not None:
+        print(f"ERROR: {refusal}", file=sys.stderr)
+        return RC_REFUSED
+    try:
+        preimage_payload = {
+            "card": "CARD-G3-8",
+            "mode": "pre-image",
+            "group_id": ctx.group_id,
+            "user_id": ctx.user_id,
+            "target_kind": "neo4j",
+            "target_uri": ctx.neo4j_uri,
+            "database": ctx.neo4j_database,
+            "rows": [
+                {
+                    "concept_key": row["concept_key"],
+                    "user_id": row["user_id"],
+                    "old_next_review": row["target_next_review"],
+                    "new_next_review": row["new_next_review"],
+                }
+                for row in writable
+            ],
+        }
+        preimage_path, err = _write_preimage(ctx, preimage_payload, _read_inputs(ctx, bundle))
+        if err is not None:
+            print(f"ERROR: {err} — pre-image 落盘成功才允许开写, 库未改动。", file=sys.stderr)
+            return RC_NOT_WRITTEN
+
+        # ⚠️ 还原集合必须是 **pre-image 形状**的行 (Codex r2 HIGH-2): 分类行带的是
+        # `target_next_review`, pre-image 行带的是 `old_next_review`。此前把分类行
+        # 直接喂给 _restore_neo4j, 它取 `old_next_review` 恒得 None ⇒ 走 REMOVE ⇒
+        # **把原值清空**, 读回执还通过, 然后报告「迁移前的可信状态」。
+        preimage_by_key = {(r["user_id"], r["concept_key"]): r for r in preimage_payload["rows"]}
+        failed: List[str] = []
+        attempted: List[Dict[str, Any]] = []
+        with _session(driver, ctx) as session:
+            for row in writable:
+                # ⚠️ **下笔前**记账 (Codex r2 HIGH-3): 若写已提交而取回执时连接断了,
+                # 事后记账会把这一行漏出还原集合 —— rc=1 声称「未改动」却证明不了。
+                # 多还原一行无害 (再写一次原值), 漏还原一行不是。
+                attempted.append(preimage_by_key[(row["user_id"], row["concept_key"])])
+                try:
+                    rec = session.run(
+                        _NEO4J_WRITE_QUERY,
+                        uid=row["user_id"],
+                        cname=row["concept_key"],
+                        gid=ctx.group_id,
+                        due=row["new_next_review"],
+                    ).single()
+                except Exception as exc:  # noqa: BLE001 — 写入期异常与回执不符同路处置
+                    failed.append(f"{row['user_id']}/{row['concept_key']} ({type(exc).__name__}: {exc})")
+                    break
+                # 写完读回执: 拿 SET 之后 RETURN 的实值逐条比, 不用"没抛异常即成功"。
+                if rec is None or not _same_instant(rec["next_review"], row["new_next_review"]):
+                    failed.append(f"{row['user_id']}/{row['concept_key']}")
+                    break
+
+            if failed:
+                # ⚠️ 逐条写入不是原子的: 到这里库里已经有若干行被改过了
+                # (Codex r1 HIGH-3)。此前直接返回 1, 而 1 的语义是「目标处于迁移前
+                # 的可信状态」—— 那是谎报。必须先按 pre-image 把下过笔的那些放回去,
+                # 放得回去才配叫 1, 放不回去是 3。
+                print(
+                    f"ERROR: 写入/读回执失败 {failed} — 已下笔 {len(attempted)} 行, 正按 pre-image 还原。",
+                    file=sys.stderr,
+                )
+                restore_failed = _restore_neo4j(session, ctx.group_id, attempted)
+                if restore_failed:
+                    print(
+                        f"CRITICAL: 回滚也失败 {restore_failed} — 库可能半写, pre-image 在 {preimage_path}, 需人工处置。",
+                        file=sys.stderr,
+                    )
+                    return RC_ROLLBACK_FAILED
+                print(f"已按 pre-image 还原 {len(attempted)} 行 — 库处于迁移前的可信状态。", file=sys.stderr)
+                return RC_NOT_WRITTEN
+        print(f"已写 {len(writable)} 行; pre-image: {preimage_path}")
+        bundle["preimage_path"] = str(preimage_path)
+        return RC_OK
+    finally:
+        driver.close()
+
+
+def _fraction_digits(value: str) -> str:
+    """取 ISO 串里的小数秒**全部**位数 (右侧补零到 9 位, 便于逐位比)。"""
+    m = _ISO_FRACTION_RE.search(value)
+    return (m.group(1)[1:] if m else "").ljust(9, "0")
+
+
+def _same_instant_exact(got: Any, expected: Optional[str]) -> bool:
+    """**精确**时刻相等 —— 还原校验用。
+
+    ⚠️ 不能只比 ``datetime``: :func:`_normalize_iso` 把小数秒截到 6 位 (因为
+    ``fromisoformat`` 只收 6 位), 于是 ``.123456999Z`` 与 ``.123456001Z`` 会被判
+    相等 (Codex r2 MEDIUM-7)。还原要证明的是"回到原样", 把纳秒差异吞掉就证明不了。
+    故在 datetime 相等之外**另比一次原始小数秒位**。
+    """
+    if expected is None:
+        return got is None
+    if not isinstance(got, str):
+        return False
+    try:
+        a = datetime.fromisoformat(_normalize_iso(got))
+        b = datetime.fromisoformat(_normalize_iso(expected))
+    except ValueError:
+        return False
+    if a.tzinfo is None or b.tzinfo is None:
+        return False
+    if a.astimezone(timezone.utc) != b.astimezone(timezone.utc):
+        return False
+    return _fraction_digits(got) == _fraction_digits(expected)
+
+
+def _same_instant(got: Any, expected: Optional[str]) -> bool:
+    if expected is None:
+        return got is None
+    if not isinstance(got, str):
+        return False
+    try:
+        a = datetime.fromisoformat(_normalize_iso(got))
+        b = datetime.fromisoformat(_normalize_iso(expected))
+    except ValueError:
+        return False
+    if a.tzinfo is None or b.tzinfo is None:
+        return False
+    return _whole_second_utc(a) == _whole_second_utc(b)
+
+
+def run_apply(ctx: "_Context") -> int:
+    if ctx.backup_dir is None:
+        print("ERROR: --apply 必须给 --backup-dir (没有有效 pre-image 就不该开始写)。", file=sys.stderr)
+        return RC_REFUSED
+
+    refusal = assert_target_is_not_live(
+        target=ctx.json_file,
+        uri=ctx.neo4j_uri,
+        what="--apply 的目标",
+    )
+    if refusal is not None:
+        print(f"ERROR: {refusal}", file=sys.stderr)
+        return RC_REFUSED
+
+    bundle, err = _gather(ctx)
+    if err is not None:
+        print(f"ERROR: {err}", file=sys.stderr)
+        return RC_REFUSED
+    assert bundle is not None
+
+    writable = [r for r in bundle["rows"] if r["action"] in ("set", "backfill")]
+    _print_summary("CARD-G3-8 next_review 对账 — APPLY", ctx, bundle["counts"])
+
+    rc = RC_OK
+    if not writable:
+        # 「已经对齐」与「本来就没数据」都走这条 —— 不产生备份、不写一个字节。
+        print("无可写行 (set + backfill = 0) — 未做任何写入, 未产生备份。")
+    elif ctx.json_file is not None:
+        rc = _apply_json(ctx, bundle, writable)
+    else:
+        rc = _apply_neo4j(ctx, bundle, writable)
+
+    report = _report_for(ctx, "apply", bundle)
+    report["preimage_path"] = bundle.get("preimage_path")
+    report["written"] = len(writable) if rc == RC_OK else 0
+    wrote, refusal = write_report_checked(ctx, bundle, report)
+    if refusal is not None:
+        # 数据侧已按 rc 处置完毕; 报告写不得只影响报告, 不改变数据侧结论。
+        print(f"ERROR: 报告未写 — {refusal}", file=sys.stderr)
+    elif wrote:
+        print(f"报告已写: {ctx.out}")
+    return rc
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 模式 ③: rollback —— 从 .bak / pre-image 逐条还原并读回校验
+# ═══════════════════════════════════════════════════════════════════════════
+def run_rollback(ctx: "_Context", preimage_file: Path) -> int:
+    try:
+        payload = json.loads(preimage_file.read_text(encoding="utf-8"))
+    except (OSError, ValueError) as exc:
+        print(f"ERROR: pre-image 读不出 {preimage_file}: {exc}", file=sys.stderr)
+        return RC_REFUSED
+    if not isinstance(payload, dict) or payload.get("card") != "CARD-G3-8":
+        print(f"ERROR: {preimage_file} 不是 CARD-G3-8 的 pre-image。", file=sys.stderr)
+        return RC_REFUSED
+    if payload.get("group_id") != ctx.group_id:
+        print(
+            f"ERROR: pre-image 的 group_id {payload.get('group_id')!r} 与 --group-id {ctx.group_id!r} 不同 — 拒绝跨组回滚。",
+            file=sys.stderr,
+        )
+        return RC_REFUSED
+
+    refusal = assert_target_is_not_live(target=ctx.json_file, uri=ctx.neo4j_uri, what="--rollback 的目标")
+    if refusal is not None:
+        print(f"ERROR: {refusal}", file=sys.stderr)
+        return RC_REFUSED
+
+    if payload.get("target_kind") == "json":
+        return _rollback_json(ctx, payload)
+    return _rollback_neo4j(ctx, payload)
+
+
+def _rollback_json(ctx: "_Context", payload: Dict[str, Any]) -> int:
+    if ctx.json_file is None:
+        print("ERROR: pre-image 是 JSON 目标, 但没给 --json-file。", file=sys.stderr)
+        return RC_REFUSED
+    # ⚠️ pre-image 必须绑回**它自己那个目标** (Codex r1 HIGH-4): 备份是整份镜像,
+    # 把 A 的备份倒进同组的另一份 B, 逐条校验照样全过 —— 它校验的是"内容等于
+    # 备份", 而不是"这是不是该还原的那个文件"。同组不等于同目标。
+    recorded = payload.get("target_path")
+    if not recorded or _resolved(Path(recorded)) != _resolved(ctx.json_file):
+        print(
+            f"ERROR: pre-image 记录的目标是 {recorded!r}, 而 --json-file 指向 "
+            f"{_resolved(ctx.json_file)} — 拒绝把一份备份还原到别的文件上。",
+            file=sys.stderr,
+        )
+        return RC_REFUSED
+    expected = payload.get("target_sha256_before")
+    backup = Path(payload.get("backups", {}).get("stamped", ""))
+    if not backup.is_file():
+        print(f"ERROR: pre-image 记录的备份不存在: {backup}", file=sys.stderr)
+        return RC_NOT_WRITTEN
+    try:
+        actual = _sha256_file(backup)
+    except OSError as exc:
+        print(f"ERROR: 备份 {backup} 读不出 ({exc}) — 无法证明它是迁移前那一份, 目标未改动。", file=sys.stderr)
+        return RC_NOT_WRITTEN
+    if actual != expected:
+        # 备份被改动过 ⇒ 它不再是"迁移前那一份" ⇒ 拿它覆盖目标就是拿不可信的数据
+        # 覆盖可信的数据。目标保持现状, 交人工处置。
+        print(
+            f"ERROR: 备份 {backup} 的 sha256 ({actual}) 与 pre-image 记录的 ({expected}) 不符 — 拒绝用它覆盖目标。",
+            file=sys.stderr,
+        )
+        return RC_NOT_WRITTEN
+    try:
+        shutil.copy2(backup, ctx.json_file)
+    except OSError as exc:
+        print(f"CRITICAL: 回滚写入失败 ({exc}) — 目标 {ctx.json_file} 可能半写, 备份在 {backup}。", file=sys.stderr)
+        return RC_ROLLBACK_FAILED
+    # 读回校验 —— 读不出来与读出来不对**同样**是"还没还原成功", 都归 3。
+    try:
+        readback = _sha256_file(ctx.json_file)
+    except OSError as exc:
+        print(f"CRITICAL: 回滚后读不回目标 ({exc}) — {ctx.json_file} 需人工处置, 备份在 {backup}。", file=sys.stderr)
+        return RC_ROLLBACK_FAILED
+    if readback != expected:
+        print(f"CRITICAL: 回滚后读回的 sha256 与迁移前不符 — 目标 {ctx.json_file} 需人工处置。", file=sys.stderr)
+        return RC_ROLLBACK_FAILED
+    print(f"已从 {backup} 回滚 {ctx.json_file}, 读回 sha256 = {expected}")
+    return RC_OK
+
+
+def _rollback_neo4j(ctx: "_Context", payload: Dict[str, Any]) -> int:
+    if ctx.neo4j_uri is None:
+        print("ERROR: pre-image 是 Neo4j 目标, 但没给 --neo4j-uri。", file=sys.stderr)
+        return RC_REFUSED
+    # 同 _rollback_json 的理由 (Codex r1 HIGH-4): 另一个非现网库若恰好有同组同名
+    # 的边, 逐条校验会全过 —— 它证明的是"值写成了 pre-image 里的样子", 不是
+    # "这是当初被改的那个库"。
+    recorded_uri = payload.get("target_uri")
+    if recorded_uri != ctx.neo4j_uri or payload.get("database") != ctx.neo4j_database:
+        print(
+            f"ERROR: pre-image 记录的目标是 {recorded_uri!r}/{payload.get('database')!r}, "
+            f"而本次指向 {ctx.neo4j_uri!r}/{ctx.neo4j_database!r} — 拒绝把一份 pre-image 还原到别的库上。",
+            file=sys.stderr,
+        )
+        return RC_REFUSED
+    driver, refusal = _open_verified_driver(ctx)
+    if refusal is not None:
+        print(f"ERROR: {refusal}", file=sys.stderr)
+        return RC_REFUSED
+    try:
+        with _session(driver, ctx) as session:
+            failed = _restore_neo4j(session, ctx.group_id, payload.get("rows", []))
+        if failed:
+            print(f"CRITICAL: 回滚后读回与 pre-image 不符 {failed} — 需人工处置。", file=sys.stderr)
+            return RC_ROLLBACK_FAILED
+        print(f"已按 pre-image 回滚 {len(payload.get('rows', []))} 行, 逐条读回校验通过。")
+        return RC_OK
+    finally:
+        driver.close()
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# CLI
+# ═══════════════════════════════════════════════════════════════════════════
+def build_parser() -> argparse.ArgumentParser:
+    parser = argparse.ArgumentParser(
+        prog="migrate_next_review_g38.py",
+        description="CARD-G3-8 — 把旧 next_review 对账到 frontmatter fsrs_due 真相源",
+    )
+    mode = parser.add_mutually_exclusive_group(required=True)
+    mode.add_argument("--dry-run", action="store_true", help="只读只报 (除 --out 外零写入)")
+    mode.add_argument("--apply", action="store_true", help="实际对账 (备份 + pre-image + 写完读回)")
+    mode.add_argument("--rollback", metavar="PREIMAGE", help="从 pre-image / .bak 逐条还原")
+
+    parser.add_argument("--vault-dir", help="frontmatter 源目录 (只读; 扫 节点/ 与 原白板/)")
+    parser.add_argument("--group-id", required=True, help="物理格式组 id, 形如 vault__cs_61b")
+    parser.add_argument("--user-id", default=None, help="只处理该 user 的边 (不给则全部用户)")
+    parser.add_argument(
+        "--group-scope",
+        default=None,
+        help="要写的是 vault 内二级作用域 (白板级/学科级) 时显式给它的名字; "
+        "届时 --group-id 必须逐字等于 vault__<vault_id>__<name>",
+    )
+    parser.add_argument("--json-file", default=None, help="目标: neo4j_memory.json 的**副本**")
+    parser.add_argument("--neo4j-uri", default=None, help="目标: bolt/neo4j URI (⛔ 现网端口一律拒)")
+    parser.add_argument("--neo4j-user", default=None)
+    parser.add_argument("--neo4j-password", default=None)
+    parser.add_argument("--neo4j-database", default=None)
+    parser.add_argument("--out", default=None, help="报告 JSON 路径 (dry-run 时是唯一写口)")
+    parser.add_argument("--backup-dir", default=None, help="--apply 的备份/pre-image 目录")
+    parser.add_argument(
+        "--json-naive-tz",
+        choices=("local", "utc"),
+        default="local",
+        help="JSON 镜像里 naive 值的解释口径 (默认 local, 与该文件写/读两侧的契约一致)",
+    )
+    parser.add_argument("--from-report", default=None, help="dry-run 报告; 给了则断言 group_id 一致")
+    parser.add_argument("--card-states-file", default=None, help="fsrs_card_states.json 副本 (**只读**, 只报分歧计数)")
+    parser.add_argument(
+        "--allow-unbound-vault",
+        action="store_true",
+        help="--vault-dir 说不出自己的 vault_id (或其形态本脚本算不出物理组名) 时仍允许执行 (默认 fail-closed 拒)",
+    )
+    parser.add_argument(
+        "--allow-unverified-target",
+        action="store_true",
+        help="目标库 store identity 读不到时仍允许写 (默认 fail-closed 拒)",
+    )
+    return parser
+
+
+def _validate(args: argparse.Namespace) -> Optional[str]:
+    if not _GROUP_ID_RE.fullmatch(args.group_id or ""):
+        return (
+            f"--group-id {args.group_id!r} 不是物理格式 —— 必须形如 vault__<id> (双下划线, 无冒号)。"
+            " D16 的冒号格式 vault:<id> 是逻辑格式, 库里存的是物理格式。"
+        )
+    if args.json_file and args.neo4j_uri:
+        return "--json-file 与 --neo4j-uri 只能给一个目标。"
+    if not args.json_file and not args.neo4j_uri:
+        return "必须给一个目标: --json-file 或 --neo4j-uri。"
+    if not args.rollback and not args.vault_dir:
+        return "--dry-run / --apply 必须给 --vault-dir。"
+    if args.from_report:
+        try:
+            report = json.loads(Path(args.from_report).read_text(encoding="utf-8"))
+        except (OSError, ValueError) as exc:
+            return f"--from-report 读不出 {args.from_report}: {exc}"
+        if report.get("group_id") != args.group_id:
+            return (
+                f"--from-report 的 group_id {report.get('group_id')!r} 与 --group-id {args.group_id!r} 不同 —"
+                " apply 必须与 dry-run 同组, 拒绝执行。"
+            )
+    return None
+
+
+def main(argv: Optional[List[str]] = None) -> int:
+    args = build_parser().parse_args(argv)
+
+    err = _validate(args)
+    if err is not None:
+        print(f"ERROR: {err}", file=sys.stderr)
+        return RC_REFUSED
+
+    ctx = _Context(args)
+
+    # dry-run 也要过库面闸: "禁连 7691/7687"是硬边界, 读也不行。
+    if ctx.neo4j_uri is not None:
+        refusal = assert_target_is_not_live(uri=ctx.neo4j_uri, what="--neo4j-uri")
+        if refusal is not None:
+            print(f"ERROR: {refusal}", file=sys.stderr)
+            return RC_REFUSED
+
+    # 组 ↔ vault 身份绑定 (Codex r1 BLOCKER-1)。rollback 没有 --vault-dir,
+    # 它的绑定靠 pre-image 自带的 group_id 与 target_path/target_uri。
+    if ctx.vault_dir is not None:
+        bind_refusal = assert_group_matches_vault(
+            ctx.vault_dir,
+            ctx.group_id,
+            scope=ctx.group_scope,
+            allow_unbound=ctx.allow_unbound_vault,
+        )
+        if bind_refusal is not None:
+            print(f"ERROR: {bind_refusal}", file=sys.stderr)
+            return RC_REFUSED
+
+    out_refusal = assert_write_path_is_safe(
+        ctx.out, vault_dir=ctx.vault_dir, read_inputs=_read_inputs(ctx), label="--out 的目标"
+    )
+    if out_refusal is None:
+        out_refusal = assert_out_is_safe(ctx.out, ctx.json_file, ctx.card_states_file)
+    if out_refusal is not None:
+        print(f"ERROR: {out_refusal}", file=sys.stderr)
+        return RC_REFUSED
+
+    if args.rollback:
+        return run_rollback(ctx, Path(args.rollback))
+    if args.apply:
+        return run_apply(ctx)
+    return run_dry_run(ctx)
+
+
+if __name__ == "__main__":  # pragma: no cover
+    sys.exit(main())
diff --git a/backend/tests/unit/test_migrate_next_review_g38.py b/backend/tests/unit/test_migrate_next_review_g38.py
new file mode 100644
index 00000000..b5fbf06a
--- /dev/null
+++ b/backend/tests/unit/test_migrate_next_review_g38.py
@@ -0,0 +1,1266 @@
+"""CARD-G3-8 — ``scripts/migrate_next_review_g38.py`` 行为门.
+
+[BATCH-2026-09-18-第十五批 / CARD-G3-8]
+
+被测对象是**旧 ``next_review`` 对账迁移器**: 把 frontmatter ``fsrs_due``
+(D0 T1 裁定的唯一真相源) 对账到目标侧的 ``next_review`` (Neo4j ``LEARNED``
+边 / JSON 镜像 ``relationships[].next_review``)。
+
+加载方式抄 ``tests/regression/test_g3_5_vault_keyed_card_states.py:295-310``
+(``scripts/`` 不是包 ⇒ 按路径 ``spec_from_file_location`` + **先注册
+``sys.modules`` 再 ``exec_module``**)。
+
+⚠️ **先红纪律 (卡文 (b)③④)**: :func:`_migrator` 与 :func:`_script_source`
+的第一条语句都是显式断言「尚不存在」。脚本未写时本文件**每一条**用例都红在
+那条断言上, 而不是裸 ``ImportError`` / 夹具错 —— 后两者也可能来自 conftest
+崩了或路径写错, 说明不了「实现确实缺席」。7692 真库组同理: 可达性探针排在
+:func:`_migrator` **之后**, 否则脚本缺席时该组会 skip 而不是红。
+"""
+
+from __future__ import annotations
+
+import hashlib
+import importlib.util
+import json
+import os
+import pathlib
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+from types import SimpleNamespace
+from typing import Any, Dict, Optional
+
+import pytest
+
+# ── 被测脚本 ────────────────────────────────────────────────────────────────
+_BACKEND = Path(__file__).resolve().parents[2]
+SCRIPT_PATH = _BACKEND / "scripts" / "migrate_next_review_g38.py"
+
+#: 先红断言的**唯一**文案 —— 卡文 (b)③ 的 `grep -c '尚不存在'` 锚在这个串上。
+_ABSENT_MSG = "migrate_next_review_g38.py 尚不存在"
+
+
+def _migrator():
+    """按路径加载迁移器 (``scripts/`` 不是包)。"""
+    assert SCRIPT_PATH.is_file(), _ABSENT_MSG
+    spec = importlib.util.spec_from_file_location("g38_migrator", SCRIPT_PATH)
+    assert spec and spec.loader
+    mod = importlib.util.module_from_spec(spec)
+    # 先注册再 exec —— 动态加载的模块若含模块级自省 (dataclass 等) 会取
+    # sys.modules[cls.__module__]; 保持这个安全写法 (Python 3.14 起必需)。
+    sys.modules["g38_migrator"] = mod
+    spec.loader.exec_module(mod)
+    return mod
+
+
+def _script_source() -> str:
+    """只读脚本文本 (AST / 字面量门用)。缺席时红在同一条断言上。"""
+    assert SCRIPT_PATH.is_file(), _ABSENT_MSG
+    return SCRIPT_PATH.read_text(encoding="utf-8")
+
+
+# ── 现网常量 (只做字符串比对, 绝不拿它们做 I/O) ─────────────────────────────
+_LIVE_REPO_ROOT = "/Users/Heishing/Desktop/canvas/canvas-learning-system"
+_LIVE_VAULT_DIR = _LIVE_REPO_ROOT + "/canvas-vault"
+_LIVE_JSON_MIRROR = _LIVE_REPO_ROOT + "/backend/data/neo4j_memory.json"
+_LIVE_CARD_STATES = _LIVE_REPO_ROOT + "/backend/data/fsrs_card_states.json"
+
+
+# ── fixture 工具 ────────────────────────────────────────────────────────────
+def _sha(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def _tree_sha(root: Path) -> Dict[str, str]:
+    """目录下全部普通文件的 {相对路径: sha256} —— dry-run 零写入的判据。"""
+    return {str(p.relative_to(root)): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}
+
+
+def _utc_z_to_naive_local(iso_z: str) -> str:
+    """UTC-Z 串 → **naive 本地** ISO —— 与 JSON 镜像写方同款形态.
+
+    ``neo4j_client.py:717-718`` 写的是 ``datetime.now()`` (naive 本地) 加一天后
+    ``.isoformat()``; ``:793`` 的读方同样拿 naive 的 ``datetime.now()`` 比大小。
+    两侧同为 naive 本地 ⇒ 该文件里 naive 值的语义是**本地时间**, 这是代码可证的
+    契约, 不是猜测。
+    """
+    dt = datetime.strptime(iso_z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
+    return dt.astimezone().replace(tzinfo=None).isoformat()
+
+
+def _write_vault_config(vault: Path, vault_id: str) -> Path:
+    """写 ``<vault>/.canvas-config.yaml`` —— vault 自报身份的唯一载体。
+
+    迁移器用它把 ``--group-id`` 绑到这个目录上: 两个参数各自合法、合起来指向
+    不同 vault 时（``--vault-dir A --group-id vault__B``）就是跨 vault 写。
+    """
+    vault.mkdir(parents=True, exist_ok=True)
+    cfg = vault / ".canvas-config.yaml"
+    cfg.write_text(
+        f'# 测试 vault\nvault_id: "{vault_id}"\nsubject: g38-fixture\n',
+        encoding="utf-8",
+    )
+    return cfg
+
+
+def _write_node(vault: Path, stem: str, fsrs_due: Optional[str], sub: str = "节点") -> Path:
+    """在 ``<vault>/<sub>/`` 下造一个节点 ``.md``; ``fsrs_due=None`` ⇒ ungoverned。"""
+    d = vault / sub
+    d.mkdir(parents=True, exist_ok=True)
+    p = d / f"{stem}.md"
+    if fsrs_due is None:
+        body = f"---\ntitle: {stem}\nfsrs_state: 0\n---\n\n正文 {stem}\n"
+    else:
+        body = f"---\ntitle: {stem}\nfsrs_due: {fsrs_due}\nfsrs_state: 2\nfsrs_stability: 3.5\n---\n\n正文 {stem}\n"
+    p.write_text(body, encoding="utf-8")
+    return p
+
+
+_DUE_A = "2026-09-20T03:00:00Z"
+_DUE_B = "2026-09-21T04:00:00Z"
+
+
+def _mirror_payload(gid: str, uid: str) -> Dict[str, Any]:
+    """JSON 镜像形态 —— 抄 ``neo4j_client.py:305`` 的 ``self._data`` 与 :745-749 的行形态。"""
+    return {
+        "users": [{"id": uid, "name": uid}],
+        "concepts": [
+            {"id": "c-a", "name": "concept-a", "group_id": gid},
+            {"id": "c-b", "name": "concept-b", "group_id": gid},
+            {"id": "c-c", "name": "concept-c", "group_id": gid},
+            {"id": "c-d", "name": "concept-d", "group_id": gid},
+        ],
+        "relationships": [
+            {
+                "id": "learned-1",
+                "user_id": uid,
+                "concept_id": "c-a",
+                "concept_name": "concept-a",
+                "timestamp": "2026-09-01T10:00:00",
+                "last_score": 80,
+                "next_review": "2026-09-02T10:00:00",
+                "review_count": 3,
+                "group_id": gid,
+            },
+            {
+                "id": "learned-2",
+                "user_id": uid,
+                "concept_id": "c-b",
+                "concept_name": "concept-b",
+                "timestamp": "2026-09-01T11:00:00",
+                "last_score": 70,
+                "next_review": _utc_z_to_naive_local(_DUE_B),
+                "review_count": 2,
+                "group_id": gid,
+            },
+            {
+                "id": "learned-3",
+                "user_id": uid,
+                "concept_id": "c-c",
+                "concept_name": "concept-c",
+                "timestamp": "2026-09-01T12:00:00",
+                "last_score": 60,
+                "next_review": "2026-09-02T12:00:00",
+                "review_count": 1,
+                "group_id": gid,
+            },
+            {
+                "id": "learned-4",
+                "user_id": uid,
+                "concept_id": "c-d",
+                "concept_name": "concept-d",
+                "timestamp": "2026-09-01T13:00:00",
+                "last_score": 50,
+                "next_review": "2026-09-02T13:00:00",
+                "review_count": 1,
+                "group_id": gid,
+            },
+        ],
+        "metadata": {"created_at": "2026-09-01T00:00:00", "version": "2.0"},
+    }
+
+
+@pytest.fixture
+def scene(tmp_path):
+    """三段 fixture: 3 个 ``.md`` (governed 不等 / governed 相等 / ungoverned)
+    + 1 条**只在 JSON 里有**的 ``concept-d`` 边 (unmatched)。"""
+    vault = tmp_path / "vault"
+    _write_vault_config(vault, "g38fix")
+    _write_node(vault, "concept-a", _DUE_A)  # governed, 与目标不等 → set
+    _write_node(vault, "concept-b", _DUE_B)  # governed, 与目标相等 → noop
+    _write_node(vault, "concept-c", None)  # 无 fsrs_due       → ungoverned
+    gid = "vault__g38fix"
+    uid = "user-g38"
+    json_file = tmp_path / "mirror.json"
+    json_file.write_text(
+        json.dumps(_mirror_payload(gid, uid), ensure_ascii=False, indent=2),
+        encoding="utf-8",
+    )
+    out_dir = tmp_path / "out"
+    out_dir.mkdir()
+    return SimpleNamespace(
+        tmp=tmp_path,
+        vault=vault,
+        json_file=json_file,
+        gid=gid,
+        uid=uid,
+        out=out_dir / "report.json",
+        backup_dir=tmp_path / "backups",
+    )
+
+
+def _dry_run_argv(sc) -> list:
+    return [
+        "--dry-run",
+        "--vault-dir",
+        str(sc.vault),
+        "--group-id",
+        sc.gid,
+        "--json-file",
+        str(sc.json_file),
+        "--out",
+        str(sc.out),
+    ]
+
+
+def _apply_argv(sc, out: Optional[Path] = None) -> list:
+    return [
+        "--apply",
+        "--vault-dir",
+        str(sc.vault),
+        "--group-id",
+        sc.gid,
+        "--json-file",
+        str(sc.json_file),
+        "--backup-dir",
+        str(sc.backup_dir),
+        "--out",
+        str(out or sc.out),
+    ]
+
+
+def _rel(payload: Dict[str, Any], name: str) -> Dict[str, Any]:
+    return next(r for r in payload["relationships"] if r["concept_name"] == name)
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 段 ① dry-run
+# ═══════════════════════════════════════════════════════════════════════════
+class TestDryRun:
+    def test_dry_run_writes_only_the_report(self, scene):
+        """``--out`` 之外零写入 —— 跑前/跑后整棵 tmp 树的 sha256 映射逐键比。
+
+        判据是**映射相等**而不是「文件数没变」: 等数量的原地改写 (改了内容不改
+        个数) 在计数判据下看不出来。
+        """
+        m = _migrator()
+        before = _tree_sha(scene.tmp)
+        rc = m.main(_dry_run_argv(scene))
+        assert rc == 0, "dry-run 应成功"
+        after = _tree_sha(scene.tmp)
+        report_key = str(scene.out.relative_to(scene.tmp))
+        assert report_key in after, "报告没写出来 —— 判据本身失效"
+        expected = dict(before)
+        expected[report_key] = after[report_key]
+        assert after == expected, f"dry-run 动了 --out 之外的文件: {set(after) ^ set(before)}"
+
+    def test_dry_run_counts_are_exact(self, scene):
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        assert rep["counts"] == {
+            "rows_without_target": 0,
+            "governed": 2,
+            "ungoverned": 1,
+            "matched": 2,
+            "unmatched": 1,
+            "unmatched_no_target": 0,
+            "unmatched_no_frontmatter": 1,
+            "noop": 1,
+            "set": 1,
+            "backfill": 0,
+            "ambiguous": 0,
+            "malformed_fsrs_due": 0,
+        }
+
+    def test_dry_run_row_actions_are_exact(self, scene):
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        by_key = {r["concept_key"]: r for r in rep["rows"]}
+        assert by_key["concept-a"]["action"] == "set"
+        assert by_key["concept-a"]["frontmatter_fsrs_due"] == _DUE_A
+        assert by_key["concept-a"]["new_next_review"] == _DUE_A
+        assert by_key["concept-b"]["action"] == "noop"
+        assert by_key["concept-c"]["action"] == "ungoverned"
+        assert by_key["concept-c"]["new_next_review"] is None
+        assert by_key["concept-d"]["action"] == "unmatched"
+        assert by_key["concept-d"]["unmatched_kind"] == "no_frontmatter"
+
+    def test_dry_run_records_input_hashes(self, scene):
+        """报告要能自证它读的是哪几份输入 (卡文 (d) ``inputs_sha256``)。"""
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        hashes = rep["inputs_sha256"]
+        assert hashes["__json_file__"] == _sha(scene.json_file)
+        assert hashes["节点/concept-a.md"] == _sha(scene.vault / "节点" / "concept-a.md")
+        assert len([k for k in hashes if k.endswith(".md")]) == 3
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 段 ② apply
+# ═══════════════════════════════════════════════════════════════════════════
+class TestApply:
+    def test_apply_sets_target_to_frontmatter_fsrs_due(self, scene):
+        """``set`` 行写成 frontmatter 的 ``fsrs_due`` **逐字节同串**; 其余行不动。"""
+        m = _migrator()
+        before_payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        before_sha = _sha(scene.json_file)
+
+        rc = m.main(_apply_argv(scene))
+        assert rc == 0, "apply 应成功"
+
+        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        assert _rel(after, "concept-a")["next_review"] == _DUE_A
+        assert _rel(after, "concept-b")["next_review"] == _rel(before_payload, "concept-b")["next_review"]
+        assert _rel(after, "concept-c")["next_review"] == _rel(before_payload, "concept-c")["next_review"]
+        assert _rel(after, "concept-d")["next_review"] == _rel(before_payload, "concept-d")["next_review"]
+
+        simple_bak = scene.json_file.with_suffix(".json.bak")
+        assert simple_bak.is_file(), "简单备份缺席"
+        assert _sha(simple_bak) == before_sha, "备份不是改前那一份"
+
+    def test_apply_leaves_frontmatter_untouched(self, scene):
+        """迁移器**永不写 frontmatter** (D0 T1: 它才是真相源)。"""
+        m = _migrator()
+        fm_before = _tree_sha(scene.vault)
+        assert m.main(_apply_argv(scene)) == 0
+        assert _tree_sha(scene.vault) == fm_before, "apply 改了 frontmatter —— 越界"
+
+    def test_apply_is_idempotent(self, scene):
+        """第二次 apply 的 ``set + backfill`` 必须为 0。"""
+        m = _migrator()
+        assert m.main(_apply_argv(scene)) == 0
+        second = scene.tmp / "out" / "report2.json"
+        assert m.main(_apply_argv(scene, out=second)) == 0
+        rep2 = json.loads(second.read_text(encoding="utf-8"))
+        assert rep2["counts"]["set"] + rep2["counts"]["backfill"] == 0, "第二次 apply 又写了 —— 非幂等"
+        assert rep2["counts"]["noop"] == 2, "两条 governed 行都应归 noop"
+
+    def test_apply_backfills_missing_next_review(self, scene):
+        """目标缺 ``next_review`` ⇒ ``backfill`` 而不是 ``unmatched``。"""
+        m = _migrator()
+        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        _rel(payload, "concept-a").pop("next_review")
+        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+
+        assert m.main(_apply_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        assert rep["counts"]["backfill"] == 1
+        assert rep["counts"]["set"] == 0
+        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        assert _rel(after, "concept-a")["next_review"] == _DUE_A
+
+    def test_apply_requires_backup_dir(self, scene):
+        """没有备份目录就不许开写 —— 没有有效 pre-image 就不该动目标。"""
+        m = _migrator()
+        before = _sha(scene.json_file)
+        rc = m.main(
+            [
+                "--apply",
+                "--vault-dir",
+                str(scene.vault),
+                "--group-id",
+                scene.gid,
+                "--json-file",
+                str(scene.json_file),
+                "--out",
+                str(scene.out),
+            ]
+        )
+        assert rc == 2, "缺 --backup-dir 必须 rc=2"
+        assert _sha(scene.json_file) == before, "被拒的 apply 仍改了目标"
+
+    def test_dry_run_preview_equals_apply_outcome(self, scene):
+        """预览 = 实际（g35 :496 同口径）。
+
+        g35 当年的缺陷是**两种模式对同一个参数做了不同的归一化**（apply strip 了
+        空白、dry-run 没有）——于是预览说要写 A 桶、实际写进了 B 桶，而两边各自
+        都"成功"。本迁移器对 ``--group-id`` **零归一化**（形态不合直接 rc=2），
+        这条门把该性质钉死：dry-run 报告里的桶名、要写的行，必须与 apply 实际
+        落地的逐条一致。
+        """
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        preview = json.loads(scene.out.read_text(encoding="utf-8"))
+        planned = sorted(
+            (r["concept_key"], r["new_next_review"]) for r in preview["rows"] if r["action"] in ("set", "backfill")
+        )
+        assert planned, "预览里一条要写的行都没有 —— 本门会空洞地通过"
+
+        applied_out = scene.tmp / "out" / "applied.json"
+        assert m.main(_apply_argv(scene, out=applied_out)) == 0
+        applied = json.loads(applied_out.read_text(encoding="utf-8"))
+        assert applied["group_id"] == preview["group_id"], "两种模式认定的桶不同"
+
+        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        for key, expected in planned:
+            assert _rel(after, key)["next_review"] == expected, f"{key} 实际落地值与预览不符"
+        assert applied["written"] == len(planned), "实写行数与预览不符"
+
+    @pytest.mark.parametrize("gid", [" vault__g38fix", "vault__g38fix ", "vault__g38fix\n"])
+    def test_group_id_is_never_silently_normalized(self, scene, gid):
+        """带空白的组 id **不做静默 strip** —— 归一化本身就是两种模式分道的来源。"""
+        m = _migrator()
+        before = _sha(scene.json_file)
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--group-id") + 1] = gid
+        assert m.main(argv) == 2, f"未被拦下的输入: {gid!r}"
+        assert _sha(scene.json_file) == before
+
+    def test_apply_group_id_must_match_dry_run_report(self, scene, capsys):
+        """``--apply`` 与 ``--dry-run`` 必须同 ``--group-id`` (g35 :496 口径)。"""
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        before = _sha(scene.json_file)
+        # ⚠️ 换的组必须**仍然通过 vault 绑定闸**（同 vault 的二级作用域），
+        # 否则这条门会绿在更早那道判据上、证明不了 --from-report 真的生效。
+        argv = _apply_argv(scene, out=scene.tmp / "out" / "r3.json")
+        argv[argv.index("--group-id") + 1] = "vault__g38fix__otherboard"
+        argv += ["--group-scope", "otherboard", "--from-report", str(scene.out)]
+        rc = m.main(argv)
+        assert rc == 2, "与 dry-run 报告不同组的 apply 必须被拒"
+        err = capsys.readouterr().err
+        assert "--from-report" in err, f"拒绝的不是 --from-report 那道门, 实得: {err[-300:]}"
+        assert _sha(scene.json_file) == before
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 段 ③ rollback
+# ═══════════════════════════════════════════════════════════════════════════
+class TestRollback:
+    def test_rollback_restores_target_bytes(self, scene):
+        m = _migrator()
+        before = _sha(scene.json_file)
+        assert m.main(_apply_argv(scene)) == 0
+        assert _sha(scene.json_file) != before, "apply 没改动目标 —— 回滚判据会空洞地通过"
+
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        preimage = Path(rep["preimage_path"])
+        assert preimage.is_file()
+
+        rc = m.main(
+            [
+                "--rollback",
+                str(preimage),
+                "--group-id",
+                scene.gid,
+                "--json-file",
+                str(scene.json_file),
+            ]
+        )
+        assert rc == 0, "回滚应成功"
+        assert _sha(scene.json_file) == before, "回滚后目标不是改前那一份"
+
+    def test_rollback_refuses_tampered_backup(self, scene):
+        """备份自身与 pre-image 记录的 sha 对不上 ⇒ 拒绝回滚, 目标保持现状。"""
+        m = _migrator()
+        assert m.main(_apply_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        preimage = Path(rep["preimage_path"])
+        applied_sha = _sha(scene.json_file)
+
+        bak = Path(json.loads(preimage.read_text(encoding="utf-8"))["backups"]["stamped"])
+        bak.write_text('{"users": [], "concepts": [], "relationships": []}', encoding="utf-8")
+
+        rc = m.main(
+            [
+                "--rollback",
+                str(preimage),
+                "--group-id",
+                scene.gid,
+                "--json-file",
+                str(scene.json_file),
+            ]
+        )
+        assert rc == 1, "备份被改动过仍回滚 = 拿不可信的数据覆盖目标"
+        assert _sha(scene.json_file) == applied_sha, "被拒的回滚仍动了目标"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 闸用例
+# ═══════════════════════════════════════════════════════════════════════════
+class TestGuards:
+    def test_guard_refuses_target_inside_live_vault(self, scene, tmp_path, monkeypatch):
+        """落在 live vault 子树内的写目标一律拒。
+
+        ⚠️ 用 tmp 下的**替身** live vault 而不是真路径 (g35 Codex r2 H5 同款):
+        闸一旦回归成放行, 这条门自己就会往现网 vault 里写东西 —— 缺陷显形时
+        测试本身违反「禁写 live vault」。真常量的正确性由
+        :meth:`TestBoundaries.test_script_pins_live_path_literals` 单独锁。
+        """
+        m = _migrator()
+        stand_in_vault = tmp_path / "standin-vault"
+        (stand_in_vault / "节点").mkdir(parents=True)
+        monkeypatch.setattr(m, "LIVE_VAULT_DIR", stand_in_vault)
+        target = stand_in_vault / "节点" / "mirror.json"
+        target.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid)), encoding="utf-8")
+        before = _sha(target)
+
+        argv = _apply_argv(scene)
+        argv[argv.index("--json-file") + 1] = str(target)
+        rc = m.main(argv)
+
+        assert rc == 2, "落在 live vault 内的目标必须 rc=2"
+        assert _sha(target) == before, "被拒的目标仍被改写"
+        assert not target.with_suffix(".json.bak").exists(), "闸拒之后仍产生了 .bak"
+
+    def test_guard_refuses_hardlink_to_protected_file(self, scene, tmp_path, monkeypatch):
+        """硬链接 = 同 inode 不同路径 —— 纯路径比对放行它, 身份判据必须认得出。"""
+        m = _migrator()
+        protected = tmp_path / "standin-mirror.json"
+        protected.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid)), encoding="utf-8")
+        monkeypatch.setattr(m, "LIVE_JSON_MIRROR", protected)
+        alias = tmp_path / "innocent-looking.json"
+        os.link(protected, alias)
+        before = _sha(protected)
+
+        argv = _apply_argv(scene)
+        argv[argv.index("--json-file") + 1] = str(alias)
+        rc = m.main(argv)
+
+        assert rc == 2, "指向受保护 inode 的硬链接必须 rc=2"
+        assert _sha(protected) == before
+
+    @pytest.mark.parametrize(
+        "uri",
+        [
+            "bolt://localhost:7691",
+            "bolt://localhost:07691",
+            "bolt://127.0.0.1:7687",
+            "bolt://localhost",
+            "http://localhost:7692",
+        ],
+    )
+    def test_guard_refuses_live_db_uri(self, uri):
+        """现网库闸: 按**解析后的端口**判, 不是子串匹配。
+
+        ``:07691`` 与 ``:7691`` 是同一个端口的两种写法, 子串判据只拦得住后者;
+        省略端口的 URI 会被驱动路由到 7687 (本机现网开发端口) ⇒ 同样拒;
+        非 bolt/neo4j scheme 无法判定去向 ⇒ fail-closed 拒。
+        """
+        m = _migrator()
+        refusal = m.assert_target_is_not_live(uri=uri)
+        assert refusal is not None, f"未被拦下的输入: {uri}"
+        if uri.endswith(("7691", "07691")):
+            assert "7691" in refusal, "拒绝文案未给出解析后的端口, 无法自证不是子串判据"
+
+    @pytest.mark.parametrize("uri", ["bolt://127.0.0.1:7692", "neo4j://127.0.0.1:7692", "bolt+s://db.example:7692"])
+    def test_guard_allows_non_live_db_uri(self, uri):
+        """对照输入: 合法 scheme + 非现网端口必须放行 —— 否则闸是恒拒的哑闸。"""
+        m = _migrator()
+        assert m.assert_target_is_not_live(uri=uri) is None, f"对照输入被误拒: {uri}"
+
+    @pytest.mark.parametrize("gid", ["vault:cs_61b", "cs188", "vault__", "", "vault__a:b"])
+    def test_guard_refuses_bad_group_id(self, scene, gid):
+        """``--group-id`` 必须是**物理格式** ``vault__<id>``; 冒号格式一律拒。
+
+        组 id 本卡不自造拼接 (G4-5 P1 地盘), 只做形态校验 —— 传错组是跨 vault
+        写的唯一入口。
+        """
+        m = _migrator()
+        before = _sha(scene.json_file)
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--group-id") + 1] = gid
+        assert m.main(argv) == 2, f"未被拦下的输入: {gid!r}"
+        assert _sha(scene.json_file) == before
+
+    def test_guard_refuses_out_aliasing_preimage(self, scene, monkeypatch):
+        """``--out`` 与 pre-image 同位置 ⇒ 报告会覆盖回滚依据, 拒。
+
+        报告在 apply 末尾才写, 时序上排在 pre-image 落盘**之后** —— 别名不拦住
+        的话, 一次成功的 apply 结束时回滚依据已经被统计报告顶掉了。
+        时间戳定死才能让两个路径真的相撞 (否则撞不上 = 判据空洞)。
+        """
+        m = _migrator()
+        monkeypatch.setattr(m, "_now_stamp", lambda: "20260919_000000")
+        collide = scene.backup_dir / "preimage-20260919_000000.json"
+        before = _sha(scene.json_file)
+        argv = _apply_argv(scene)
+        argv[argv.index("--out") + 1] = str(collide)
+        rc = m.main(argv)
+        assert rc == 1, "别名的 pre-image 路径必须在开写前被拒 (rc=1 未写入)"
+        assert _sha(scene.json_file) == before, "被拒的 apply 仍改了目标"
+
+    def test_guard_refuses_out_aliasing_target(self, scene):
+        """``--out`` 与 ``--json-file`` 同一个文件 ⇒ 报告会覆盖输入, 拒。"""
+        m = _migrator()
+        before = _sha(scene.json_file)
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--out") + 1] = str(scene.json_file)
+        assert m.main(argv) == 2
+        assert _sha(scene.json_file) == before, "输入快照被报告覆盖 —— dry-run 非零写入"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 只读边界 / 结构门
+# ═══════════════════════════════════════════════════════════════════════════
+_ALLOWED_IMPORT_ROOTS = frozenset(
+    {
+        "__future__",
+        "argparse",
+        "datetime",
+        "hashlib",
+        "json",
+        "os",
+        "pathlib",
+        "re",
+        "shutil",
+        "sys",
+        "typing",
+        "urllib",
+        "neo4j",  # 只在给了 --neo4j-uri 时函数内延迟 import
+    }
+)
+
+_REQUIRED_FUNCTIONS = frozenset(
+    {
+        "assert_target_is_not_live",
+        "run_dry_run",
+        "run_apply",
+        "run_rollback",
+        "build_parser",
+        "main",
+    }
+)
+
+
+class TestBoundaries:
+    def test_script_imports_only_stdlib_allowlist(self):
+        """AST 级只读边界自证 —— 比逐字 grep 强: 连「没人想到的那个库」也拦得住。"""
+        import ast
+
+        roots = set()
+        for node in ast.walk(ast.parse(_script_source())):
+            if isinstance(node, ast.Import):
+                roots.update(a.name.split(".")[0] for a in node.names)
+            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
+                roots.add(node.module.split(".")[0])
+        assert roots <= _ALLOWED_IMPORT_ROOTS, f"脚本导入了允许清单外的模块: {sorted(roots - _ALLOWED_IMPORT_ROOTS)}"
+
+    def test_script_has_no_app_imports(self):
+        """⛔ 零 ``app`` 导入 —— 迁移器必须能在没有后端环境的机器上跑。"""
+        import ast
+
+        offenders = []
+        for node in ast.walk(ast.parse(_script_source())):
+            if isinstance(node, ast.Import):
+                offenders += [a.name for a in node.names if a.name.split(".")[0] == "app"]
+            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "app":
+                offenders.append(node.module)
+        assert offenders == [], f"脚本导入了 app: {offenders}"
+
+    def test_script_defines_required_functions(self):
+        """AST 函数名集合 ⊇ 必备集 —— 切片改代码静默删掉整个函数时这里会红。"""
+        import ast
+
+        names = {n.name for n in ast.walk(ast.parse(_script_source())) if isinstance(n, ast.FunctionDef)}
+        assert _REQUIRED_FUNCTIONS <= names, f"缺函数: {sorted(_REQUIRED_FUNCTIONS - names)}"
+
+    def test_script_pins_live_path_literals(self):
+        """闸常量必须钉在**真**现网路径上 (闸用例用的是 tmp 替身, 锁不住这一点)。"""
+        m = _migrator()
+        assert str(m.LIVE_VAULT_DIR) == _LIVE_VAULT_DIR
+        assert str(m.LIVE_JSON_MIRROR) == _LIVE_JSON_MIRROR
+        assert str(m.LIVE_CARD_STATES) == _LIVE_CARD_STATES
+        assert set(m.LIVE_DB_PORTS) == {7691, 7687}
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 语义门: naive 解释 / 显形 / 反向回填
+# ═══════════════════════════════════════════════════════════════════════════
+class TestSemantics:
+    def test_naive_json_value_is_interpreted_as_local_and_flagged(self, scene):
+        """JSON 镜像的 naive 值按**本地**解释, 且逐行打标 —— 解释口径永不隐形。"""
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        assert rep["naive_interpretation"] == "local"
+        by_key = {r["concept_key"]: r for r in rep["rows"]}
+        assert by_key["concept-b"]["target_naive"] is True
+        assert by_key["concept-b"]["action"] == "noop", "同一时刻的 naive 本地值应判 noop"
+
+    def test_naive_utc_interpretation_changes_the_verdict(self, scene):
+        """换成 ``--json-naive-tz utc`` 结论必须改变 —— 证明这个开关真的接上了。"""
+        if datetime.now().astimezone().utcoffset().total_seconds() == 0:
+            pytest.skip("本机 UTC 偏移为 0, local/utc 两种解释不可区分")
+        m = _migrator()
+        argv = _dry_run_argv(scene) + ["--json-naive-tz", "utc"]
+        assert m.main(argv) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        by_key = {r["concept_key"]: r for r in rep["rows"]}
+        assert by_key["concept-b"]["action"] == "set", "utc 解释下同一个值应判为分歧"
+
+    def test_report_warns_about_json_mirror_aware_reader(self, scene):
+        """写 UTC-Z 进 JSON 镜像有**已知下游后果**, 报告必须自己说出来。
+
+        ``neo4j_client.py:806-808`` 拿 naive 的 ``datetime.now()`` 与读出的值比
+        大小; 值是 tz-aware 时抛 ``TypeError``, 被 ``:833`` 的
+        ``except (ValueError, TypeError): continue`` **静默跳过** —— 该 concept
+        会从 JSON 降级路径的复习建议里消失。本卡不能改 ``neo4j_client.py``
+        (P1/P2 地盘), 所以把后果显形在报告里, 而不是静默制造回归。
+        """
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        codes = [w["code"] for w in rep["warnings"]]
+        assert "W-JSON-MIRROR-AWARE-READER" in codes, "已知下游后果没有显形"
+
+    def test_unmatched_no_target_is_surfaced(self, scene):
+        """governed 却在目标侧找不到边 ⇒ ``unmatched``, ⛔ 不静默跳过。"""
+        m = _migrator()
+        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        payload["relationships"] = [r for r in payload["relationships"] if r["concept_name"] != "concept-a"]
+        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        by_key = {r["concept_key"]: r for r in rep["rows"]}
+        assert by_key["concept-a"]["action"] == "unmatched"
+        assert by_key["concept-a"]["unmatched_kind"] == "no_target"
+        assert rep["counts"]["unmatched_no_target"] == 1
+
+    def test_ungoverned_never_backfills_frontmatter(self, scene):
+        """``ungoverned`` 行既不动目标, 也**不反向回填** frontmatter (默认不做)。"""
+        m = _migrator()
+        node_c = scene.vault / "节点" / "concept-c.md"
+        before_fm = _sha(node_c)
+        before_target = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        assert m.main(_apply_argv(scene)) == 0
+        assert _sha(node_c) == before_fm, "ungoverned 节点的 frontmatter 被写了"
+        after_target = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        assert _rel(after_target, "concept-c")["next_review"] == _rel(before_target, "concept-c")["next_review"]
+
+    def test_shadowed_node_files_are_surfaced(self, scene):
+        """同 stem 同时出现在 ``节点/`` 与 ``原白板/`` ⇒ 取 ``节点/``, 但必须显形。"""
+        m = _migrator()
+        _write_node(scene.vault, "concept-a", "2027-01-01T00:00:00Z", sub="原白板")
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        assert any("原白板/concept-a.md" in s["shadowed_path"] for s in rep["shadowed"])
+        by_key = {r["concept_key"]: r for r in rep["rows"]}
+        assert by_key["concept-a"]["frontmatter_fsrs_due"] == _DUE_A, "应取 节点/ 那份 (与 _node_md_path 同序)"
+
+    def test_duplicate_triples_are_written_positionally(self, scene):
+        """重复的 ``(user_id, concept_name, group_id)`` 三元组必须**逐行**处置。
+
+        旧数据里可能并存重复行: 写方 ``neo4j_client.py:721-726`` 用 ``next(...)``
+        只更新第一条, 于是第二条长期停在旧值。若迁移器按三元组建索引, 两条会塌成
+        一条 —— 判 ``noop`` 的那条被连带写入, 而报告里没有它 (一次门未覆盖的写)。
+        判据: 与 frontmatter 同刻的那条**逐字节不变**, 不同刻的那条被改写。
+        """
+        m = _migrator()
+        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        dup = dict(_rel(payload, "concept-a"))
+        dup["id"] = "learned-1-dup"
+        dup["next_review"] = _utc_z_to_naive_local(_DUE_A)  # 与真相源同刻 ⇒ noop
+        payload["relationships"].append(dup)
+        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+
+        assert m.main(_apply_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        assert rep["counts"]["set"] == 1, "重复行被塌成一条 —— set 计数失真"
+        assert rep["counts"]["noop"] == 2, "同刻的重复行应判 noop"
+
+        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        rows = [r for r in after["relationships"] if r["concept_name"] == "concept-a"]
+        assert len(rows) == 2
+        assert rows[0]["next_review"] == _DUE_A, "应写的那条没写成 fsrs_due"
+        assert rows[1]["next_review"] == dup["next_review"], "判 noop 的重复行被连带写入了"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# Codex round-1 整改的行为门
+# ═══════════════════════════════════════════════════════════════════════════
+class TestVaultGroupBinding:
+    """BLOCKER-1: 形态合法的**错误**组能把 A vault 的 due 写进 B。"""
+
+    def test_group_from_another_vault_is_refused(self, scene, capsys):
+        """`--vault-dir A --group-id vault__B` —— 两个参数各自合法, 合起来是跨 vault 写。"""
+        m = _migrator()
+        before = _sha(scene.json_file)
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--group-id") + 1] = "vault__someothervault"
+        assert m.main(argv) == 2, "未被拦下的输入: 属于别的 vault 的组名"
+        err = capsys.readouterr().err
+        assert "vault_id" in err, f"拒绝的不是 vault 绑定那道门: {err[-300:]}"
+        assert _sha(scene.json_file) == before
+
+    def test_vault_subscope_requires_explicit_scope(self, scene, capsys):
+        """二级作用域必须**显式声明**, 不能靠前缀推断 (Codex r2 BLOCKER-1)。
+
+        `vault__alpha__beta` 既像 vault `alpha` 的 `beta` 板, 也像 vault
+        `alpha__beta` 的根组 —— 单看字符串分不开。所以默认逐字相等, 要写二级
+        作用域就得说出"我要写哪一层"。
+        """
+        m = _migrator()
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--group-id") + 1] = "vault__g38fix__someboard"
+        assert m.main(argv) == 2, "未被拦下的输入: 靠前缀推断的二级作用域"
+        assert "逐字等于" in capsys.readouterr().err
+
+    def test_vault_subscope_with_explicit_scope_is_allowed(self, scene):
+        """对照输入: 说清楚是哪一层就放行, 否则闸恒拒 = 哑闸。"""
+        m = _migrator()
+        argv = _dry_run_argv(scene) + ["--group-scope", "someboard"]
+        argv[argv.index("--group-id") + 1] = "vault__g38fix__someboard"
+        assert m.main(argv) == 0, "显式声明的二级作用域被误拒 —— 闸过严"
+
+    def test_another_vault_rooted_at_a_subscope_name_is_refused(self, scene, capsys):
+        """r2 BLOCKER-1 的那条路径: vault B 的**根组**恰好长得像 vault A 的二级组。
+
+        vault A 自报 `g38fix`, vault B 自报 `g38fix__beta`。拿着 A 的目录 +
+        `--group-id vault__g38fix__beta`（= B 的根组名）, 前缀放行的写法会把它
+        当成"A 的 beta 板"接受 —— 逃生门一次都不用开, A 的 due 就落进了 B。
+        """
+        m = _migrator()
+        before = _sha(scene.json_file)
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--group-id") + 1] = "vault__g38fix__beta"
+        assert m.main(argv) == 2, "未被拦下的输入: 另一个 vault 的根组名"
+        assert _sha(scene.json_file) == before
+
+    def test_vault_id_containing_the_separator_fails_closed(self, scene, capsys):
+        """vault 自报的 id 内嵌 `__` ⇒ 与二级分隔符撞车 ⇒ 算不出确定组名 ⇒ 拒。"""
+        m = _migrator()
+        _write_vault_config(scene.vault, "alpha__beta")
+        assert m.main(_dry_run_argv(scene)) == 2
+        assert "算不出确定的物理组名" in capsys.readouterr().err
+
+    # ⚠️ 不用 "-bad": argparse 会把前导 `-` 当成选项名, 抛 SystemExit 而不是走到
+    # 形态判据 —— 那条用例会绿/红在更早的一层上, 证明不了本门。
+    @pytest.mark.parametrize("scope", ["a__b", "_bad", "", "有中文"])
+    def test_group_scope_shape_is_enforced(self, scene, scope):
+        """`--group-scope` 自己也不得内嵌 `__`, 否则同一个歧义在下一层复发。"""
+        m = _migrator()
+        argv = _dry_run_argv(scene) + ["--group-scope", scope]
+        argv[argv.index("--group-id") + 1] = f"vault__g38fix__{scope}"
+        assert m.main(argv) == 2, f"未被拦下的输入: --group-scope {scope!r}"
+
+    def test_vault_without_config_fails_closed(self, scene, capsys):
+        """vault 说不出自己是谁 ⇒ 拿不准配对 ⇒ 拒, 而不是默认"应该没事"。"""
+        m = _migrator()
+        (scene.vault / ".canvas-config.yaml").unlink()
+        assert m.main(_dry_run_argv(scene)) == 2
+        assert "无法确认" in capsys.readouterr().err
+
+    def test_allow_unbound_vault_is_an_explicit_escape(self, scene):
+        """逃生门必须是**显式**的 —— 默认 fail-closed, 加了才放行。"""
+        m = _migrator()
+        (scene.vault / ".canvas-config.yaml").unlink()
+        assert m.main(_dry_run_argv(scene) + ["--allow-unbound-vault"]) == 0
+
+    def test_non_ascii_vault_id_is_not_silently_vouched_for(self, scene, capsys):
+        """算不出物理组名就不能假装验过 (物理化含 punycode, 属 app 侧能力)。"""
+        m = _migrator()
+        _write_vault_config(scene.vault, "数学101")
+        assert m.main(_dry_run_argv(scene)) == 2
+        assert "算不出" in capsys.readouterr().err
+
+
+class TestWritePathSafety:
+    """HIGH-2: 输出口此前没有保护**全部**只读输入。"""
+
+    def test_out_inside_vault_is_refused(self, scene, capsys):
+        """`--out <vault>/节点/A.md` 会把报告覆盖到源节点上 —— frontmatter 是真相源。"""
+        m = _migrator()
+        node = scene.vault / "节点" / "concept-a.md"
+        before = _sha(node)
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--out") + 1] = str(node)
+        assert m.main(argv) == 2, "未被拦下的输入: --out 指向源节点"
+        assert "--vault-dir" in capsys.readouterr().err
+        assert _sha(node) == before, "源节点被报告覆盖了"
+
+    def test_out_anywhere_in_vault_subtree_is_refused(self, scene):
+        """判据覆盖整棵 `--vault-dir` 子树, 而不是只覆盖扫到的那几个 `.md`。"""
+        m = _migrator()
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--out") + 1] = str(scene.vault / "没被扫到的子目录" / "r.json")
+        assert m.main(argv) == 2
+
+    def test_backup_symlinked_into_vault_is_refused(self, scene):
+        """备份也是**写入路径**: `.bak` 若是指向源节点的符号链接, 复制就覆盖了它。"""
+        m = _migrator()
+        node = scene.vault / "节点" / "concept-a.md"
+        before = _sha(node)
+        scene.json_file.with_suffix(".json.bak").symlink_to(node)
+        assert m.main(_apply_argv(scene)) == 2
+        assert _sha(node) == before, "源节点被备份复制覆盖了"
+
+    def test_backup_dir_in_live_vault_creates_no_directory(self, scene, tmp_path, monkeypatch):
+        """MEDIUM-9: 闸必须排在 mkdir **前面**, 否则已经在 live vault 里落了目录。"""
+        m = _migrator()
+        stand_in = tmp_path / "standin-live-vault"
+        stand_in.mkdir()
+        monkeypatch.setattr(m, "LIVE_VAULT_DIR", stand_in)
+        target_dir = stand_in / "g38-backups"
+        argv = _apply_argv(scene)
+        argv[argv.index("--backup-dir") + 1] = str(target_dir)
+        rc = m.main(argv)
+        assert rc == 1, f"落在 live vault 的 --backup-dir 必须在开写前被拒, 实得 rc={rc}"
+        assert not target_dir.exists(), "闸拒之后目录仍被建出来了"
+
+    def test_plain_multi_hardlink_file_is_refused_on_its_own(self, scene, tmp_path, monkeypatch):
+        """MEDIUM-11: 让受保护 inode 判据够不着, 单独证明 `st_nlink > 1` 那一条。"""
+        m = _migrator()
+        monkeypatch.setattr(m, "LIVE_JSON_MIRROR", tmp_path / "nonexistent-mirror.json")
+        monkeypatch.setattr(m, "LIVE_CARD_STATES", tmp_path / "nonexistent-states.json")
+        monkeypatch.setattr(m, "LIVE_VAULT_DIR", tmp_path / "nonexistent-vault")
+        innocent = tmp_path / "plain.json"
+        innocent.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid)), encoding="utf-8")
+        os.link(innocent, tmp_path / "second-name.json")
+
+        refusal = m.assert_target_is_not_live(target=innocent, what="测试目标")
+        assert refusal is not None, "未被拦下的输入: 普通多硬链接文件"
+        assert "硬链接数" in refusal, f"拒绝的不是多名字那条判据: {refusal}"
+
+
+class TestRollbackBinding:
+    """HIGH-4: pre-image 必须绑回它自己那个目标。"""
+
+    def test_rollback_to_a_different_file_is_refused(self, scene, tmp_path, capsys):
+        m = _migrator()
+        assert m.main(_apply_argv(scene)) == 0
+        preimage = Path(json.loads(scene.out.read_text(encoding="utf-8"))["preimage_path"])
+
+        other = tmp_path / "another-mirror.json"
+        other.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid), ensure_ascii=False), encoding="utf-8")
+        before_other = _sha(other)
+
+        rc = m.main(["--rollback", str(preimage), "--group-id", scene.gid, "--json-file", str(other)])
+        assert rc == 2, "未被拦下的输入: 把一份备份还原到别的文件上"
+        assert "pre-image 记录的目标" in capsys.readouterr().err
+        assert _sha(other) == before_other, "被拒的回滚仍覆盖了别的文件"
+
+
+def _force_la_timezone(monkeypatch, scene) -> None:
+    """切到洛杉矶时区, 并**在切换之后**重建 fixture 里依赖本地时区的那个值。
+
+    ⚠️ Codex r2 LOW-10: fixture 是在**进程启动时区**下造 `concept-b` 的 naive
+    本地串的; 用例随后切到洛杉矶再断言 `noop/set` 计数 —— 本机恰好是 PDT 所以
+    碰巧绿, 换一台 UTC 机器同一条门就红。门的前提条件不能依赖跑它的环境。
+    """
+    import time
+
+    monkeypatch.setenv("TZ", "America/Los_Angeles")
+    time.tzset()
+    payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+    _rel(payload, "concept-b")["next_review"] = _utc_z_to_naive_local(_DUE_B)
+    scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+
+
+class TestDaylightSaving:
+    """MEDIUM-8: 夏令时边界上 naive 本地时刻**本身**就不是一个确定的时刻。"""
+
+    @pytest.mark.parametrize(
+        ("local_value", "expected_reason"),
+        [("2026-11-01T01:30:00", "ambiguous_local_time"), ("2026-03-08T02:30:00", "nonexistent_local_time")],
+    )
+    def test_dst_boundary_local_values_are_not_silently_normalized(
+        self, scene, monkeypatch, local_value, expected_reason
+    ):
+        _force_la_timezone(monkeypatch, scene)
+        m = _migrator()
+        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        _rel(payload, "concept-a")["next_review"] = local_value
+        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        row = {r["concept_key"]: r for r in rep["rows"]}["concept-a"]
+        assert row["action"] == "ambiguous", "歧义的本地时刻被默默归一成了一个确定时刻"
+        assert row["reason"] == expected_reason
+        assert rep["counts"]["ambiguous"] == 1
+        assert rep["counts"]["set"] == 0, "ambiguous 行不得进写入集合"
+
+    def test_ordinary_local_value_still_compares(self, scene, monkeypatch):
+        """对照输入: 非边界日期照常比较, 否则上一条门可能只是"什么都判 ambiguous"。"""
+        _force_la_timezone(monkeypatch, scene)
+        m = _migrator()
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        assert rep["counts"]["ambiguous"] == 0
+        assert rep["counts"]["noop"] == 1 and rep["counts"]["set"] == 1
+
+
+class TestIdentityMissDimension:
+    """MEDIUM-10: due 坏掉的节点也可能同时"在目标侧没有边", 后者不能因此消失。"""
+
+    def test_malformed_node_without_target_still_shows_the_miss(self, scene):
+        m = _migrator()
+        _write_node(scene.vault, "concept-e", "不是一个合法时间戳")
+        assert m.main(_dry_run_argv(scene)) == 0
+        rep = json.loads(scene.out.read_text(encoding="utf-8"))
+        row = {r["concept_key"]: r for r in rep["rows"]}["concept-e"]
+        assert row["action"] == "malformed_fsrs_due"
+        assert row["target_missing"] is True, "身份没对上这件事被 malformed 盖掉了"
+        assert rep["counts"]["rows_without_target"] == 1
+
+
+class TestCodexRound2Fixes:
+    """round-2 提出的 HIGH/MEDIUM 各自的门。"""
+
+    def test_out_cannot_overwrite_a_node_reached_through_a_symlink(self, scene, tmp_path, capsys):
+        """HIGH-4: `vault/节点/A.md` 可以是指向 vault **外**某文件的软链。
+
+        那个文件既不在 `--vault-dir` 子树内, 也不在扫描前的只读输入清单里 ——
+        `--out <它>` 能穿过 main 里那道核查, 在报告落盘时覆盖真相源。
+        扫完之后才知道真正读了哪些文件, 所以写报告前必须用实测清单再核一次。
+        """
+        m = _migrator()
+        outside = tmp_path / "outside-truth-source.md"
+        outside.write_text(f"---\ntitle: concept-a\nfsrs_due: {_DUE_A}\n---\n正文\n", encoding="utf-8")
+        node = scene.vault / "节点" / "concept-a.md"
+        node.unlink()
+        node.symlink_to(outside)
+        before = _sha(outside)
+
+        argv = _dry_run_argv(scene)
+        argv[argv.index("--out") + 1] = str(outside)
+        assert m.main(argv) == 2, "未被拦下的输入: --out 指向软链背后的真相源"
+        assert "只读输入" in capsys.readouterr().err
+        assert _sha(outside) == before, "软链背后的真相源被报告覆盖了"
+
+    def test_existing_backup_dir_is_accepted(self, scene):
+        """MEDIUM-6: 第二次 apply 时备份目录**本来就应该存在**, 不能被拒。
+
+        此前备份目录走了"已存在且不是普通文件就拒"的判据, 于是正常的二次写入
+        被拒 —— 幂等负控也因此提前红在 `rc == 0` 而不是它声称的计数断言上。
+        """
+        m = _migrator()
+        scene.backup_dir.mkdir(parents=True)
+        (scene.backup_dir / "旧的遗留文件.json").write_text("{}", encoding="utf-8")
+        assert m.main(_apply_argv(scene)) == 0, "已存在的备份目录被误拒"
+
+    def test_second_apply_with_writable_rows_still_succeeds(self, scene):
+        """同上, 但走的是"第二次仍有可写行"这条真实路径 (负控正是踩这里)。"""
+        m = _migrator()
+        assert m.main(_apply_argv(scene)) == 0
+        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
+        _rel(payload, "concept-b")["next_review"] = "2020-01-01T00:00:00"
+        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
+        second = scene.tmp / "out" / "second.json"
+        assert m.main(_apply_argv(scene, out=second)) == 0, "第二次有可写行时被备份目录闸拒了"
+        assert json.loads(second.read_text(encoding="utf-8"))["counts"]["set"] == 1
+
+    def test_out_cannot_alias_the_stamped_backup(self, scene, monkeypatch):
+        """MEDIUM-8: 报告在 apply 末尾写, 别名到备份就把回滚依据顶掉了。"""
+        m = _migrator()
+        monkeypatch.setattr(m, "_now_stamp", lambda: "20260919_010203")
+        collide = scene.json_file.with_suffix(".json.bak.20260919_010203")
+        before = _sha(scene.json_file)
+        argv = _apply_argv(scene)
+        argv[argv.index("--out") + 1] = str(collide)
+        assert m.main(argv) == 2, "未被拦下的输入: --out 别名到本次备份"
+        assert _sha(scene.json_file) == before
+
+    @pytest.mark.parametrize(
+        ("a", "b", "same"),
+        [
+            ("2026-01-01T00:00:00.123456999Z", "2026-01-01T00:00:00.123456001Z", False),
+            ("2026-01-01T00:00:00.123456789Z", "2026-01-01T00:00:00.123456789Z", True),
+            ("2026-01-01T00:00:00Z", "2026-01-01T00:00:00.000000000Z", True),
+        ],
+    )
+    def test_restore_comparison_does_not_swallow_nanoseconds(self, a, b, same):
+        """MEDIUM-7: `fromisoformat` 只收 6 位小数, 截断会把纳秒差异判成相等。
+
+        还原要证明的是"回到原样"; 把纳秒差吞掉就证明不了。
+        """
+        m = _migrator()
+        assert m._same_instant_exact(a, b) is same
+
+    def test_restore_uses_preimage_shaped_rows(self, scene):
+        """HIGH-2: 还原函数取 `old_next_review`; 喂它分类行会恒得 None ⇒ 走清空。
+
+        这里直接对 `_restore_neo4j` 的入参形状做断言 —— 真库不可达时这条仍成立,
+        因为它锁的是**调用方给了什么形状**, 不是库的行为。
+        """
+        m = _migrator()
+        src = pathlib.Path(m.__file__ if hasattr(m, "__file__") else SCRIPT_PATH).read_text(encoding="utf-8")
+        assert "preimage_by_key" in src, "还原集合没有改成 pre-image 形状"
+        assert "attempted.append(preimage_by_key[" in src, "还原集合不是按 pre-image 行装的"
+        # 下笔前记账: attempted.append 必须排在 session.run 之前
+        i_append = src.index("attempted.append(preimage_by_key[")
+        i_run = src.index("rec = session.run(", i_append)
+        assert i_append < i_run, "记账排在了写入之后 —— 回执失败的那一行会漏出还原集合"
+
+
+# ═══════════════════════════════════════════════════════════════════════════
+# 7692 真库门 (共享容器; 身份一律 g38gate_ 前缀, 清理不得宽于自己的前缀)
+# ═══════════════════════════════════════════════════════════════════════════
+_NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
+_NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
+_NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")
+
+
+def _test_db_reachable(m) -> bool:
+    """可达性探针 —— 现网判定**复用被测迁移器自己的闸**(Codex r1 HIGH-6)。
+
+    此前这里是子串判定 (``":7691" in uri``)，而 ``bolt://host:07691`` 与
+    ``bolt://host``(驱动默认 7687) 都能从子串判定底下走过去 —— 探针会先连上去
+    并在用例体里 ``MERGE/SET``，之后才轮到迁移器那道正确的闸。门自己把现网写了，
+    再由被测代码拒绝，已经晚了。
+    """
+    if m.assert_target_is_not_live(uri=_NEO4J_TEST_URI) is not None:
+        return False
+    try:
+        from neo4j import GraphDatabase
+
+        driver = GraphDatabase.driver(
+            _NEO4J_TEST_URI,
+            auth=(_NEO4J_TEST_USER, _NEO4J_TEST_PASSWORD),
+            connection_timeout=3.0,
+        )
+        try:
+            driver.verify_connectivity()
+            return True
+        finally:
+            driver.close()
+    except Exception:  # noqa: BLE001 — 任何失败都视为不可达
+        return False
+
+
+class TestRealNeo4jGate:
+    def test_g38gate_neo4j_roundtrip(self, scene):
+        """真库往返: dry-run ``set=1`` → apply → 读回 = ``fsrs_due`` → 幂等 → 回滚。
+
+        ⚠️ 可达性探针排在 :func:`_migrator` **之后**: 脚本缺席时这条也必须红在
+        「尚不存在」而不是 skip (卡文 (b)④)。
+        """
+        m = _migrator()
+        if not _test_db_reachable(m):
+            pytest.skip(f"测试容器不可达或未通过现网闸, 跳过真库门: {_NEO4J_TEST_URI}")
+
+        import uuid
+
+        from neo4j import GraphDatabase
+
+        # MEDIUM-9: 身份必须能证明"属于本次运行" —— 固定名字在共享容器里会与
+        # 遗留数据 / 并行跑的另一份自己撞上, 然后被本用例改写并删除。
+        run_tag = f"g38gate_{uuid.uuid4().hex}"
+        uid = f"{run_tag}_user"
+        cname = f"{run_tag}_concept"
+        gid = "vault__g38gate"
+        vault = scene.tmp / "gatevault"
+        _write_vault_config(vault, "g38gate")
+        _write_node(vault, cname, _DUE_A)
+        old_value = "2026-01-01T00:00:00Z"
+
+        driver = GraphDatabase.driver(_NEO4J_TEST_URI, auth=(_NEO4J_TEST_USER, _NEO4J_TEST_PASSWORD))
+        try:
+            # ⚠️ HIGH-5: **先核库身份, 再下第一笔**。此前探针只验端口与可达性,
+            # 用例直接 MERGE/SET, 要等调用迁移器时才轮到身份闸 —— 若 7692 被转发
+            # 到现网库, 门自己已经把现网写了, 再拒绝已经晚了。
+            store_refusal = m.assert_store_is_not_live(driver, None, False)
+            if store_refusal is not None:
+                pytest.skip(f"测试库未通过 store identity 闸, 不下笔: {store_refusal}")
+
+            with driver.session() as s:
+                s.run(
+                    "MERGE (u:User {id: $uid}) "
+                    "MERGE (c:Concept {name: $cname, group_id: $gid}) "
+                    "MERGE (u)-[r:LEARNED {group_id: $gid}]->(c) "
+                    "SET r.next_review = datetime($old)",
+                    uid=uid,
+                    cname=cname,
+                    gid=gid,
+                    old=old_value,
+                )
+
+            base = [
+                "--vault-dir",
+                str(vault),
+                "--group-id",
+                gid,
+                "--neo4j-uri",
+                _NEO4J_TEST_URI,
+                "--neo4j-user",
+                _NEO4J_TEST_USER,
+                "--neo4j-password",
+                _NEO4J_TEST_PASSWORD,
+            ]
+            out1 = scene.tmp / "out" / "gate-dry.json"
+            assert m.main(["--dry-run", *base, "--out", str(out1)]) == 0
+            assert json.loads(out1.read_text(encoding="utf-8"))["counts"]["set"] == 1
+
+            out2 = scene.tmp / "out" / "gate-apply.json"
+            assert m.main(["--apply", *base, "--backup-dir", str(scene.backup_dir), "--out", str(out2)]) == 0
+            with driver.session() as s:
+                got = s.run(
+                    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept) "
+                    "WHERE c.group_id = $gid AND r.group_id = $gid AND c.name = $cname "
+                    "RETURN toString(r.next_review) AS nr",
+                    uid=uid,
+                    gid=gid,
+                    cname=cname,
+                ).single()
+            assert got is not None and got["nr"].startswith("2026-09-20T03:00:00")
+
+            out3 = scene.tmp / "out" / "gate-apply2.json"
+            assert m.main(["--apply", *base, "--backup-dir", str(scene.backup_dir), "--out", str(out3)]) == 0
+            rep3 = json.loads(out3.read_text(encoding="utf-8"))
+            assert rep3["counts"]["set"] + rep3["counts"]["backfill"] == 0
+
+            preimage = json.loads(out2.read_text(encoding="utf-8"))["preimage_path"]
+            assert (
+                m.main(
+                    [
+                        "--rollback",
+                        preimage,
+                        "--group-id",
+                        gid,
+                        "--neo4j-uri",
+                        _NEO4J_TEST_URI,
+                        "--neo4j-user",
+                        _NEO4J_TEST_USER,
+                        "--neo4j-password",
+                        _NEO4J_TEST_PASSWORD,
+                    ]
+                )
+                == 0
+            )
+            with driver.session() as s:
+                got = s.run(
+                    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept) "
+                    "WHERE c.group_id = $gid AND r.group_id = $gid AND c.name = $cname "
+                    "RETURN toString(r.next_review) AS nr",
+                    uid=uid,
+                    gid=gid,
+                    cname=cname,
+                ).single()
+            assert got is not None and got["nr"].startswith("2026-01-01T00:00:00")
+        finally:
+            # 清理只删**本次这一条身份**, 不删「前缀匹配的一切」(Codex r1 HIGH-7):
+            # 7692 是共享容器, `STARTS WITH 'g38gate_'` 会连同名但**别的组**的
+            # Concept 一起删; 而 DETACH DELETE 还会顺手删掉那些节点上挂的全部关系
+            # —— 删到的就不只是"自己的前缀"了。
+            try:
+                with driver.session() as s:
+                    s.run(
+                        "MATCH (:User {id: $uid})-[r:LEARNED {group_id: $gid}]->(:Concept {name: $cname, group_id: $gid}) "
+                        "DELETE r",
+                        uid=uid,
+                        gid=gid,
+                        cname=cname,
+                    )
+                    s.run(
+                        "MATCH (c:Concept {name: $cname, group_id: $gid}) WHERE NOT (c)--() DELETE c",
+                        gid=gid,
+                        cname=cname,
+                    )
+                    s.run("MATCH (u:User {id: $uid}) WHERE NOT (u)--() DELETE u", uid=uid)
+            finally:
+                driver.close()

==== END EMBEDDED DIFF ====

**2. census 文档（树内可读）**：`_bmad-output/审查/evidence-g38/next_review-census.md`

**3. 闸的参照实现（只读，不要评价它们本身）：**
- `backend/scripts/migrate_fsrs_card_states_vault_key_g35.py` 第 50–160 行（路径面闸范式）
- `backend/scripts/migrate_write_identity_g23.py` 第 52–118 行（端口解析闸 + store identity 指纹闸）

**4. 目标侧写/读的生产代码（只读事实，不要评价它们的处置）：**
- `backend/app/clients/neo4j_client.py` 第 985–1040 行（`LEARNED` 的 MERGE 身份键与 `P1D` 写）
- `backend/app/clients/neo4j_client.py` 第 716–746 行（JSON 镜像的行匹配键与写法）
- `backend/app/clients/neo4j_client.py` 第 790–835 行（JSON 镜像读方与其时区比较）

**5. 真相源与比较口径：**
- `backend/app/services/review_service.py` 第 160–170 行（整秒归一）与第 223–300 行（governed 四态、frontmatter 正则）
- `docs/fsrs-truth-source-d0-revision.md` 第 10–49 行（T1/T5）

**6. 第十四批裁定书 T4-C 行**：源文件 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md`（车道树内为旧版快照；以下为主版本 §2.3 逐卡裁定表 `:149` 摘录）：
> `| T4-C U9B-OPENSPEC | ad1e8a70 | 收官 | 4 / B0 H0 | 0 | 合 |`

---

## ② 作者自述（请独立核对，不要默认接受）

我声称本卡的实现满足下列性质。请逐条独立验证，**不要以我的措辞为准**：

- **A1** 迁移器永不写 frontmatter，也永不写 `backend/data/fsrs_card_states.json`（后者只读、只报分歧计数）。
- **A2** 现网库闸按 `urlsplit` **解析后的整数端口**判定，不是字符串包含判定；`bolt://h:07691` 与 `bolt://h:7691` 结论相同；省略端口的 URI 被拒。
- **A3** `--apply` 第二次执行时 `set + backfill == 0`（幂等）。
- **A4** 身份映射失败在**两个方向**都显形为 `unmatched`（`no_target` / `no_frontmatter`），不静默跳过。
- **A5** `--dry-run` 除 `--out` 之外零写入（判据是跑前/跑后整棵 tmp 树的 sha256 映射逐键相等，不是文件计数）。
- **A6** 迁移器零 `app` 导入，纯标准库（`neo4j` 仅在给了 `--neo4j-uri` 时函数内延迟导入）。

---

## ③ 请按重要性排序回答的问题

- **Q0（最高）** 身份映射：`--vault-dir` 下的文件 stem ↔ `Concept.name` + `group_id`。在真实数据上，是否存在一条路径会把 A vault 的 `fsrs_due` 写到 B vault 的 `LEARNED` 边上？读侧与写侧的 Cypher 是否对 `c`、`r` 两个 alias 都做了 group 过滤（R1 全覆盖 / W5 scoped update）？`--group-id` 的形态校验是否是唯一防线，够不够？
- **Q1** 整秒归一比较：除了「同秒不同微秒」之外，它是否还会把**真分歧**吞成 `noop`？特别是时区处理——naive 输入、Neo4j 纳秒精度、`--json-naive-tz` 的两种口径、跨夏令时边界的 naive 本地值。
- **Q2** pre-image 落盘失败时，`--apply` 是否**真的不开写**？`--rollback` 是否做了读回校验？备份被改动过时的处置是否正确（rc 语义 1 与 3 是否分得开）？
- **Q3** 闸对下列输入分别给什么结论，是否都正确：`neo4j://host:7692`、`bolt+s://host:7692`、`bolt://host`（省略端口）、`bolt://host:07691`、`http://host:7692`、以及路径面的 live vault 子树 / 受保护 inode 的硬链接 / `st_nlink > 1` 的普通文件。
- **Q4** 7692 真库门的清理查询是否只删它自己的 `g38gate_` 前缀身份？有没有可能删到共享容器里别人的数据？（本卡执行期容器未启动，该门为 SKIPPED，请按代码判断。）
- **Q5** 负控输入（把闸改成恒放行 / 把 `noop` 比较改成恒假）是否真的会让**指定的那几条**用例变红，还是会红在门未覆盖的路径上？有没有哪条门实际上绿在了更早的一道判据上？

---

## ④ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给：

- 一句话结论
- `file:line`
- 一句复现思路（描述哪种输入会让它出问题即可）

措辞请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这组词，不要用其他等价说法。

---

## ⑤ 审查边界（请不要越过）

- 只读。不要修改文件，不要连接数据库、不要发起网络请求。
- **不要评价** `neo4j_client.py:1034` / `fallback_sync_service.py:774` 的 `P1D` 写方、以及 `learning_context_service.py:96-102` 派生式**该如何处置** —— 它们属别的车道地盘，本卡只做 census 登记，明确不改。
- **不要评价** 是否应该对现网执行 `--apply` —— live 执行需用户当次授权，本批只做 dry-run。
- **不要评价** `backend/app/**` 里任何一行的写法 —— 本卡对这 14 个文件零改动，只读它们做 census。
- census 文档 `next_review-census.md` 的事实陈述属审查面（请核对它与代码是否一致）；台账与验收单不属审查面。
