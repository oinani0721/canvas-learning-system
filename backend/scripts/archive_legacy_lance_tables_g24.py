#!/usr/bin/env python3
"""G2-4 LanceDB 裸表归档器 (BATCH-2026-08-29-第七批 / CARD-G2-4).

背景: CARD-G2-4 删除了 ``resolve_table_name`` 的 B0.7 裸表回退与
``supplementary_search_service`` 的 tier-2 裸表直开分支。在线路径从此
**不再有任何分支**会读写裸表 (``vault_notes`` / ``file_fingerprints`` 这类
无 vault 前缀的表)。多 vault 部署里残留的裸表因而变成"库里躺着、没人读"的
孤儿数据 —— 必须由显式工具处置, 而不是让检索路径顺手兜底 (那正是被删掉的
fail-open)。

三段式 (与 ``migrate_write_identity_g23.py`` 同骨架):

1. **census (只读)**: 列出全部表, 分类成 vault_scoped / bare_legacy /
   unknown_bare, 逐表给 rows + Arrow schema + **类型化**内容指纹。
2. **pending 裁定**: bare_legacy 与 unknown_bare 都进 pending。``--apply``
   未给时零写入; pending>0 → exit 2 (需人工过目), pending==0 → exit 0。
3. **--apply (可选)**: 两阶段 —— 先把每张 pending 表导出成 **DB 目录之外**的
   Parquet + manifest 并逐张回读核对 (schema + 类型化内容指纹 + 行数),
   **全部核对通过后**才统一 drop 源表。对**现网**数据面硬拒绝 (live 只读铁律)。

⚠️ 为什么归档到 DB **外面** (Codex round-1 BLOCKER-2 实证):
``LanceDBClient.initialize()`` → ``_cache_tables()`` 会对每张非指纹表调用
``_check_and_fix_dimension_mismatch()``, 后者发现**缺 doc_type 列或向量维度不符**
就直接 ``drop_table``。旧裸表恰恰就是缺 doc_type 的那一批 —— 把归档副本留在同一个
LanceDB 里, 下一次后端启动就会把它当成 schema drift 一并删掉, 结果源表和归档
双双消失。Parquet 不在 LanceDB 目录树里, 不受启动自愈影响。

⚠️ 单 vault 部署 (active vault 为 ``default`` 或空) 的裸表**不是** legacy ——
它就是该部署的正常命名空间 (``resolve_table_name`` 保留了这条映射)。此时
本工具恒报 pending=0 并明示原因, 绝不建议归档。

用法::

    # 只读普查 (任何环境都安全), 证据 JSON 落盘 (须落在 DB 目录之外)
    python scripts/archive_legacy_lance_tables_g24.py \\
        --db-path /lancedb --active-vault canvas_vault --out /tmp/evidence.json

    # 在隔离/测试库上执行归档
    python scripts/archive_legacy_lance_tables_g24.py \\
        --db-path /tmp/testdb --active-vault v1 --apply

Exit codes: 0 = pending==0 (或 apply 全部完成且复查归零); 2 = dry-run 发现
pending>0 (需人工裁定); 1 = 运行错误 / 被安全闸拒绝 / apply 未能全部完成。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import lancedb
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover - 环境缺依赖时显式失败
    print("ERROR: lancedb / pyarrow not installed", file=sys.stderr)
    raise


# ── 表名契约 ────────────────────────────────────────────────────────────────
#
# 全部经 resolve_table_name 前缀化的业务表基名。来源: `grep -rE
# 'table_name\\s*[=:]\\s*"[a-z_]+"' backend/app backend/lib` 的实测全集
# (2026-08-31) + FINGERPRINT_TABLE 常量。
#
# ⛔ 这份清单**不可能自证完整** (Codex round-1 HIGH-3): 漏一个基名, 那张裸表
# 就会被判成 unknown。所以 unknown 不再等于 clean —— 见 classify_table。
KNOWN_BASE_TABLES = (
    "vault_notes",
    "canvas_nodes",
    "multimodal_content",
    "file_fingerprints",
    "edge_rationales",
    "canvas_explanations",
)

# 归档目录默认放在 DB 目录的**兄弟位置**, 绝不进 DB 树 (见模块 docstring)。
DEFAULT_ARCHIVE_DIRNAME = "g24-lance-archive"

# 现网数据面标记路径 (docker-compose.yml:161 `LANCEDB_DATA_PATH=/lancedb`,
# :205 挂 named volume canvas-lancedb-data)。
LIVE_PATH_MARKERS = ("/lancedb",)


class GuardRefused(RuntimeError):
    """安全闸拒绝 —— 调用方必须 exit 1, 且不得已执行任何写。"""


def canonical_db_path(raw: str) -> Path:
    """把 ``--db-path`` 归一成**唯一一条** canonical 文件系统路径。

    ⛔ 拒绝任何带 scheme 的写法 (Codex round-1 BLOCKER-1 实证):
    ``lancedb.connect("file:///lancedb")`` 会连到 ``/lancedb``, 而
    ``Path("file:///lancedb").resolve()`` 得到的是 ``$CWD/file:/lancedb`` ——
    安全闸按普通路径解释、连接按 URI 解释, 两边看的不是同一个库, live 拒绝闸
    就被绕过了。这里一律拒绝 scheme, 并把**同一个** Path 对象同时交给闸和
    ``lancedb.connect``, 消灭"双解释"这一整类绕过。
    """
    if "://" in raw:
        raise GuardRefused(
            f"--db-path 只接受普通文件系统路径, 收到带 scheme 的写法: {raw!r}。"
            "URI 会让安全闸与 lancedb.connect() 解释成不同的库 (双解释绕过)。"
        )
    try:
        return Path(os.path.expanduser(raw)).resolve()
    except (OSError, RuntimeError) as e:
        raise GuardRefused(f"--db-path 无法解析: {raw!r} ({e})") from e


def resolve_vault_id(raw: str) -> str:
    """走**应用自己的** sanitizer, 与 ``resolve_table_name`` 同口径。

    ⛔ Codex round-1 HIGH-2 实证: ``ACTIVE_VAULT="Default"`` 经
    ``app.config.sanitize_vault_id`` 归一后是 ``"default"`` (= 单 vault, 裸表
    合法), 但脚本若按原始字符串判断就会认为这是多 vault 部署, 于是把一张
    **正在被使用的**裸表判成 legacy 并归档掉。任何"脚本自己实现一套归一化"的
    写法都会与应用漂移, 所以这里只接受应用的实现; 导不到就 fail closed。
    """
    # `python scripts/x.py` 只把 scripts/ 放进 sys.path, backend/ 不在里面 ——
    # 与 backend 下的其它脚本同样需要显式补一条。
    backend_root = str(Path(__file__).resolve().parents[1])
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    try:
        from app.config import sanitize_vault_id
    except ImportError as e:  # pragma: no cover - 仅在脱离后端环境时触发
        raise GuardRefused(
            f"无法导入 app.config.sanitize_vault_id ({e}) —— 拒绝用脚本自造的归一化"
            "规则判断 vault 身份 (与应用漂移 = 误删正常裸表)。请在 backend/ 下运行。"
        ) from e
    return sanitize_vault_id(raw)


def classify_table(name: str, *, single_vault: bool) -> str:
    """``vault_scoped`` / ``bare_legacy`` / ``unknown_bare``。

    单 vault 部署下裸表是正常命名空间, 由调用方统一按 pending=0 处理,
    分类本身仍如实标注。
    """
    if name in KNOWN_BASE_TABLES:
        return "bare_legacy"
    for base in KNOWN_BASE_TABLES:
        if name.endswith(f"_{base}") and len(name) > len(base) + 1:
            return "vault_scoped"
    # ⛔ 不在契约里的裸表 = **说不清归属**, 不是"干净"。报 clean 会让漏登记的
    # 生产表 (round-1 HIGH-3 的 canvas_explanations 就是这么漏的) 静默留在库里。
    return "unknown_bare"


def targets_live_store(db_path: Path) -> bool:
    """现网数据面判定 (fail-closed): 解析后逐一比对标记路径与 env。"""
    for marker in LIVE_PATH_MARKERS:
        try:
            if db_path == Path(marker).resolve(strict=False):
                return True
        except (OSError, RuntimeError):
            return True
    env_path = os.getenv("LANCEDB_DATA_PATH")
    if env_path:
        if "://" in env_path:
            return True  # 拿不准就当现网
        try:
            if db_path == Path(os.path.expanduser(env_path)).resolve(strict=False):
                return True
        except (OSError, RuntimeError):
            return True
    return False


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve(strict=False).relative_to(parent)
        return True
    except (ValueError, OSError, RuntimeError):
        return False


# ── 只读普查 ────────────────────────────────────────────────────────────────


def _table_names(db) -> List[str]:
    """全量表名。

    ⛔ 必须显式给 limit (Codex round-1 MEDIUM-1 实证, lancedb 0.30.2):
    ``table_names(page_token=None, limit=10)`` **默认只返回前 10 张**, 库里
    表一多, 归档器就会漏看后面的表并报"干净"。
    """
    if hasattr(db, "list_tables"):
        raw = db.list_tables(limit=None)
        return list(getattr(raw, "tables", raw))
    return list(db.table_names(limit=10_000))


def _cell(v: Any) -> str:
    """类型化单元格渲染 —— ``1`` 与 ``"1"`` 必须给出不同的字符串。

    ⛔ Codex round-1 HIGH-1 实证: 旧实现用 ``str(v)``, 于是 int 1 与 str "1"
    指纹完全相同, 对账"通过"之后源表就被删了。
    """
    if v is None:
        return "\x00null"
    return f"{type(v).__name__}\x00{v!r}"


def table_digest(tbl) -> Dict[str, Any]:
    """表的**类型化**摘要: Arrow schema + 行数 + 内容指纹。

    schema 单独出摘要并参与 apply 对账 —— 只比内容会让"同值不同类型"
    或"少一列全 null"这类差异溜过去。
    """
    at = tbl.to_arrow() if hasattr(tbl, "to_arrow") else tbl.to_lance().to_table()
    return _arrow_digest(at)


#: Parquet 往返会把 list 的**内层字段标签**从 Arrow 默认的 ``item`` 改写成
#: Parquet 规范用的 ``element`` (2026-08-31 实测:
#: ``fixed_size_list<item: float>[4]`` → ``fixed_size_list<element: float>[4]``)。
#: 这是容器标签差异, 不是数据或类型差异 —— 若不归一, schema 对账会对**每一张**
#: 带 vector 列的表恒判失败, 归档器直接不可用。只归一这一个已知标签, 元素类型
#: 与维度仍逐字参与比对。
_LIST_ELEM_LABELS = ("<item: ", "<element: ")


def _normalize_type_repr(type_repr: str) -> str:
    out = type_repr
    for label in _LIST_ELEM_LABELS:
        out = out.replace(label, "<elem: ")
    return out


def _metadata_repr(md) -> str:
    """metadata 的确定性渲染 —— None 与 ``{}`` 归一为 ``meta=-``。

    非空时按 key **字节序**排序 (与 ``equals(check_metadata=True)`` 的顺序无关
    语义对齐), 每对渲染成 ``repr(k)=repr(v)`` —— bytes repr 不解码, 非 UTF-8
    的 value 不会在这里炸掉。
    """
    if not md:
        return "meta=-"
    return "meta=" + ",".join(f"{k!r}={md[k]!r}" for k in sorted(md))


def _render_field(f, label: Optional[str] = None) -> str:
    """递归渲染一个 Arrow field —— **nested 子字段的 metadata 同样参与**。

    ⛔ Codex round-3 HIGH 残余实证: 只渲染顶层 ``f.metadata`` 时, ``struct<x:int64>``
    子字段 metadata ``{unit:cm}`` vs ``{unit:m}`` 的两张表 ``equals(check_metadata=True)``
    为 False 而摘要逐字相同, 对账判同后源表被 drop。

    - ``label`` 非 None 时覆盖字段名渲染 —— 仅用于 list 容器的 value field:
      Lance 侧名恒 ``item`` / Parquet 读回恒 ``element`` (2026-09-01 实测), 统一成
      ``elem``, 与 ``_LIST_ELEM_LABELS`` 的标签归一**同一语义同一声明**; 其
      nullable/metadata 如实参与 (实测两侧保真)。
    - struct 子字段用真名 (``equals`` 本就区分, 两侧往返保真)。
    - map 在 Lance 建表即 RustPanic (2026-09-01 实测, lance-encoding 未实现),
      本归档器场景不可达; 仍渲染 key/item 子字段 (pyarrow 子字段名恒 key/value)
      只为对 Parquet 侧输入的完整性。
    - dictionary 等其余容器无子 field metadata 面 (无 ``value_field``), 不递归。
    """
    name = label if label is not None else f.name
    parts = [
        name,
        _normalize_type_repr(str(f.type)),
        "null" if f.nullable else "notnull",
        _metadata_repr(f.metadata),
    ]
    t = f.type
    if pa.types.is_struct(t):
        parts.append("{" + ",".join(_render_field(t.field(i)) for i in range(t.num_fields)) + "}")
    elif pa.types.is_map(t):
        parts.append("{" + _render_field(t.key_field) + "," + _render_field(t.item_field) + "}")
    elif pa.types.is_list(t) or pa.types.is_large_list(t) or pa.types.is_fixed_size_list(t):
        parts.append("{" + _render_field(t.value_field, label="elem") + "}")
    return ":".join(parts)


def _arrow_digest(at) -> Dict[str, Any]:
    """schema 摘要与 ``pyarrow.Schema.equals(check_metadata=True)`` 同语义 (顺序无关)。

    每个字段经 ``_render_field`` **递归**渲染 name/type/nullable/field metadata
    (含 nested 子字段), 末尾追加 **schema 级 metadata** —— 仅 metadata 不同的
    两张表必须给出不同的 ``schema_sha16`` (⛔ Codex round-2 HIGH-1 + round-3 残余:
    漏 metadata / 只渲染顶层都会让对账判同后 drop 源表)。
    唯一有意偏离 = list 内层标签 item/element 归一 (见 ``_LIST_ELEM_LABELS`` 与
    ``_render_field``, 顶层与递归层同语义)。
    ⛔ 不用 ``schema.serialize()`` 整体哈希 —— 它会把 item/element 标签差异带
    回来, 让每张 vector 表的 Parquet 对账恒失败。
    """
    schema_repr = "|".join(_render_field(f) for f in at.schema) + f"||schema:{_metadata_repr(at.schema.metadata)}"
    rows = at.to_pylist()
    payload = sorted(json.dumps({k: _cell(v) for k, v in sorted(r.items())}, ensure_ascii=False) for r in rows)
    content = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "rows": at.num_rows,
        "columns": [f.name for f in at.schema],
        "schema_repr": schema_repr,
        "schema_sha16": hashlib.sha256(schema_repr.encode("utf-8")).hexdigest()[:16],
        "content_sha256": content,
    }


def census(db, canonical_vault: str, single_vault: bool) -> Dict[str, Any]:
    """只读普查 —— 全程不调用任何写 API。"""
    tables: List[Dict[str, Any]] = []
    for name in sorted(_table_names(db)):
        entry: Dict[str, Any] = {"name": name, "kind": classify_table(name, single_vault=single_vault)}
        try:
            entry.update(table_digest(db.open_table(name)))
        except Exception as e:  # noqa: BLE001 — 单表读失败不该中断普查
            entry["error"] = f"{type(e).__name__}: {e}"
        tables.append(entry)
    return {
        "active_vault_raw": None,  # 由调用方填
        "active_vault_canonical": canonical_vault,
        "single_vault": single_vault,
        "tables": tables,
    }


def pending_from_census(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """待裁定清单 —— 单 vault 部署恒空 (裸表是它的正常命名空间)。"""
    if report["single_vault"]:
        return []
    return [t for t in report["tables"] if t["kind"] in ("bare_legacy", "unknown_bare")]


# ── apply (仅隔离库, 两阶段) ────────────────────────────────────────────────


def export_table(db, name: str, archive_dir: Path, stamp: str) -> Dict[str, Any]:
    """阶段一: 导出到 DB 目录**之外**的 Parquet, 并回读逐项核对。不 drop。"""
    src = db.open_table(name)
    at = src.to_arrow() if hasattr(src, "to_arrow") else src.to_lance().to_table()
    before = _arrow_digest(at)

    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / f"{name}__{stamp}.parquet"
    pq.write_table(at, target)

    back = _arrow_digest(pq.read_table(target))
    reconciled = (
        before["rows"] == back["rows"]
        and before["schema_repr"] == back["schema_repr"]
        and before["content_sha256"] == back["content_sha256"]
    )
    return {
        "source": name,
        "archive_file": str(target),
        "before": before,
        "after": back,
        "reconciled": reconciled,
        "source_dropped": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="G2-4 LanceDB 裸表归档器 (默认只读)")
    ap.add_argument(
        "--db-path",
        default=os.getenv("LANCEDB_DATA_PATH", "data/lancedb"),
        help="LanceDB 目录 (只接受普通路径, 不接受 URI)",
    )
    ap.add_argument(
        "--active-vault",
        default=os.getenv("ACTIVE_VAULT", "") or os.getenv("VAULT_ID", "") or "default",
        help="当前激活 vault (经 app.config.sanitize_vault_id 归一后判定)",
    )
    ap.add_argument("--archive-dir", help="Parquet 归档目录 (默认: DB 目录的兄弟目录)")
    ap.add_argument("--apply", action="store_true", help="执行归档 (对现网数据面硬拒绝)")
    ap.add_argument("--out", help="证据 JSON 落盘路径 (不得位于 DB 目录树内)")
    args = ap.parse_args()

    try:
        db_path = canonical_db_path(args.db_path)
        if not db_path.exists():
            raise GuardRefused(f"db-path 不存在: {db_path}")

        canonical_vault = resolve_vault_id(args.active_vault)
        single_vault = not canonical_vault or canonical_vault == "default"

        archive_dir = (
            Path(os.path.expanduser(args.archive_dir)).resolve()
            if args.archive_dir
            else db_path.parent / DEFAULT_ARCHIVE_DIRNAME
        )
        if _is_inside(archive_dir, db_path):
            raise GuardRefused(
                f"--archive-dir 不得位于 DB 目录树内 ({archive_dir} ⊂ {db_path}) —— "
                "留在 LanceDB 目录里的归档会被后端启动时的 schema 自愈 drop 掉。"
            )
        if args.out and _is_inside(Path(os.path.expanduser(args.out)), db_path):
            raise GuardRefused(f"--out 不得位于 DB 目录树内 ({args.out}) —— 会破坏 dry-run 的零写入性质。")

        live = targets_live_store(db_path)
        if args.apply and live:
            raise GuardRefused(f"{db_path} 判定为现网数据面 —— live 只读铁律, 拒绝 --apply。请在隔离副本上执行。")
    except GuardRefused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1

    db = lancedb.connect(str(db_path))
    report = census(db, canonical_vault, single_vault)
    report["active_vault_raw"] = args.active_vault
    report["db_path"] = str(db_path)
    report["archive_dir"] = str(archive_dir)
    report["targets_live_store"] = live
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["mode"] = "apply" if args.apply else "dry-run"

    pending = pending_from_census(report)
    report["pending"] = pending
    report["pending_count"] = len(pending)

    if single_vault:
        report["note"] = (
            "active vault 归一后为 default/空 = 单 vault 部署 —— 裸表是它的正常命名空间 "
            "(resolve_table_name 保留该映射), 恒判 pending=0, 不建议归档。"
        )

    rc = 2 if pending else 0

    if args.apply and pending:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        # 阶段一: 全部导出 + 回读核对, 一张不过就整批不 drop。
        exported = [export_table(db, t["name"], archive_dir, stamp) for t in pending]
        report["archived"] = exported
        if not all(e["reconciled"] for e in exported):
            report["apply_aborted"] = "至少一张表回读对账失败 — 未 drop 任何源表"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if args.out:
                Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 1
        # 阶段二: 统一 drop。
        for e in exported:
            db.drop_table(e["source"], ignore_missing=True)
            e["source_dropped"] = e["source"] not in _table_names(db)
        report["post_census"] = census(db, canonical_vault, single_vault)
        report["pending_after"] = len(pending_from_census(report["post_census"]))
        rc = 0 if report["pending_after"] == 0 else 1

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
