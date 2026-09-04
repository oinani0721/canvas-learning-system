"""G2-4 归档器行为门 (BATCH-2026-08-29-第七批 / CARD-G2-4).

对 ``backend/scripts/archive_legacy_lance_tables_g24.py`` 在临时 LanceDB 上验证:

1. dry-run: 裸表被裁定成 pending, exit 2, 且**目录逐字节不变**（零写入不是
   "我没调写 API"的自述, 是前后文件树指纹对账）;
2. ``--apply``: 归档 Parquet 与源表逐项相同（行数 + Arrow schema + 类型化内容
   指纹）, 全部核对通过后才 drop, 复查 pending 归零;
3. 单 vault 部署（active vault 归一后 = default/空）: 裸表**不是** legacy;
4. ``--apply`` 对现网数据面路径硬拒绝（live 只读铁律）。

Codex round-1 抓出的四条硬伤, 每条都在这里留了回归锁:

- **BLOCKER-1** ``file://`` 双解释绕过 live 闸 → ``test_uri_db_path_is_refused``
- **BLOCKER-2** 归档副本被后端启动 schema 自愈 drop → ``test_archive_survives_client_schema_repair``
- **HIGH-1** ``str()`` 指纹把 ``1`` 与 ``"1"`` 判成相同 → ``test_digest_is_type_sensitive``
- **HIGH-2** 未复用应用 sanitizer 导致误删单实例裸表 → ``test_capitalized_default_is_single_vault``
- **HIGH-3** 契约外的裸表被报成 clean → ``test_unknown_bare_table_is_pending_not_clean``
- **MEDIUM-5** ``--out`` 落进 DB 树 / 多表部分失败 → 末两条

⚠️ 与 g23 迁移器门同款纪律: 全部数据在 tmp_path, 不碰任何真实库。
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

lancedb = pytest.importorskip("lancedb")

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "archive_legacy_lance_tables_g24.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("archive_legacy_lance_tables_g24", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_script_module()

_DIM = 4


def _rows(prefix: str, n: int = 3, *, doc_type: str | None = "note"):
    out = []
    for i in range(n):
        row = {
            "doc_id": f"{prefix}-{i}",
            "content": f"{prefix} content {i}",
            "vector": [0.1 * (i + 1)] * _DIM,
            "canvas_file": f"{prefix}/f{i}.md",
        }
        if doc_type is not None:
            row["doc_type"] = doc_type
        out.append(row)
    return out


def _tree_fingerprint(root: Path) -> str:
    """目录逐字节指纹 — 相对路径 + 大小 + 内容哈希。

    只比 mtime 会被"重写同样内容"骗过, 只比文件名会被"内容改了"骗过。
    """
    parts = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            parts.append(f"{p.relative_to(root)}:{p.stat().st_size}:{hashlib.sha256(p.read_bytes()).hexdigest()}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


@pytest.fixture
def multi_vault_db(tmp_path):
    """裸表 + vault 前缀表并存 (多 vault 部署的残留形态)。"""
    path = tmp_path / "db" / "lancedb"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(path))
    db.create_table("vault_notes", data=_rows("LEGACY"))
    db.create_table("v1_vault_notes", data=_rows("V1", 2))
    return path


def _run(argv, monkeypatch):
    monkeypatch.setattr("sys.argv", ["archive_legacy_lance_tables_g24.py", *argv])
    return mod.main()


# ── 分类判据 ────────────────────────────────────────────────────────────────


def test_classify_table_is_decidable():
    assert mod.classify_table("vault_notes", single_vault=False) == "bare_legacy"
    assert mod.classify_table("file_fingerprints", single_vault=False) == "bare_legacy"
    assert mod.classify_table("edge_rationales", single_vault=False) == "bare_legacy"
    assert mod.classify_table("canvas_explanations", single_vault=False) == "bare_legacy"
    assert mod.classify_table("v1_vault_notes", single_vault=False) == "vault_scoped"
    assert mod.classify_table("canvas_vault_file_fingerprints", single_vault=False) == "vault_scoped"
    # 契约外的裸表 = 说不清归属, 不是"干净"
    assert mod.classify_table("test_table", single_vault=False) == "unknown_bare"


def test_unknown_bare_table_is_pending_not_clean(tmp_path, monkeypatch, capsys):
    """⛔ Codex round-1 HIGH-3 回归锁: 契约外的裸表必须进 pending 并 exit 2。

    round-1 的实证反例正是 ``canvas_explanations``（tool_executor 在用, 却漏在
    白名单外）—— 旧实现把它判成 ``unknown`` 后当作"干净"、exit 0, 于是一张真
    受旧 B0.7 影响的生产表被静默留在库里。
    """
    path = tmp_path / "db" / "lancedb"
    path.parent.mkdir(parents=True)
    db = lancedb.connect(str(path))
    db.create_table("v1_vault_notes", data=_rows("V1", 2))
    db.create_table("mystery_table", data=[{"k": 1}])

    rc = _run(["--db-path", str(path), "--active-vault", "v1"], monkeypatch)
    report = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert [t["name"] for t in report["pending"]] == ["mystery_table"]
    assert report["pending"][0]["kind"] == "unknown_bare"


# ── 指纹强度 ────────────────────────────────────────────────────────────────


def test_digest_is_type_sensitive(tmp_path):
    """⛔ Codex round-1 HIGH-1 回归锁: ``1`` 与 ``"1"`` 的指纹必须不同。

    旧实现把每个值 ``str()`` 后再哈希, 于是 int 1 与 str "1" 指纹逐字相同 ——
    对账"通过"之后源表就被 drop 了。本条同时锁 schema 参与摘要。
    """
    db = lancedb.connect(str(tmp_path / "d"))
    t_int = db.create_table("t_int", data=[{"x": 1}])
    t_str = db.create_table("t_str", data=[{"x": "1"}])

    d_int = mod.table_digest(t_int)
    d_str = mod.table_digest(t_str)
    assert d_int["content_sha256"] != d_str["content_sha256"], "类型不同的同值不得同指纹"
    assert d_int["schema_repr"] != d_str["schema_repr"]

    # 正向对照: 真正相同的两张表指纹必须相同 (否则"不等"是恒真的, 门等于没有)
    t_same = db.create_table("t_same", data=[{"x": 1}])
    assert mod.table_digest(t_same)["content_sha256"] == d_int["content_sha256"]


# ── HIGH-1 round-3: metadata 纳入摘要 (BATCH-2026-09-01-第八批 / CARD-G2-4) ──


def _int_table(md_field=None, md_schema=None):
    """同 ``x:int64`` 同数据 ``[1]``, 只有 metadata 可变 —— HIGH-1 最小反例载体。"""
    import pyarrow as pa

    schema = pa.schema([pa.field("x", pa.int64(), metadata=md_field)], metadata=md_schema)
    return pa.table({"x": pa.array([1], pa.int64())}, schema=schema)


def test_digest_distinguishes_schema_metadata():
    """⛔ Codex round-2 HIGH-1 回归锁 (b)①: 仅 schema 级 metadata 不同 → 摘要必不同。

    round-2 最小反例: 同 ``x:int64`` 同数据, 仅 ``Schema.metadata`` 不同,
    ``equals(check_metadata=True)`` 为 False, 旧摘要却逐字相同 —— 对账判同后
    源表就被 drop。metadata 差异只该体现在 schema 摘要, 不该污染内容指纹。
    """
    d_plain = mod._arrow_digest(_int_table())
    d_tagged = mod._arrow_digest(_int_table(md_schema={b"origin": b"vaultA"}))
    assert d_plain["schema_repr"] != d_tagged["schema_repr"], "schema 级 metadata 必须参与摘要"
    assert d_plain["schema_sha16"] != d_tagged["schema_sha16"]
    assert d_plain["content_sha256"] == d_tagged["content_sha256"], "metadata 差异不得改变内容指纹"


def test_digest_distinguishes_field_metadata():
    """⛔ Codex round-2 HIGH-1 回归锁 (b)②: 仅 field 级 metadata 不同 → 摘要必不同。"""
    d_plain = mod._arrow_digest(_int_table())
    d_tagged = mod._arrow_digest(_int_table(md_field={b"unit": b"cm"}))
    assert d_plain["schema_repr"] != d_tagged["schema_repr"], "field 级 metadata 必须参与摘要"
    assert d_plain["schema_sha16"] != d_tagged["schema_sha16"]
    assert d_plain["content_sha256"] == d_tagged["content_sha256"]


def test_digest_equal_for_identical_and_key_order_permuted_metadata():
    """(b)③ 正向对照: metadata 逐字相同 → 摘要相同; 键顺序不同的同集合 → 摘要相同。

    没有这条, ①② 的"不等"可以由一个恒不等的摘要(如掺时间戳)假满足;
    键序对照锁"确定性渲染 = 按 key 字节序排序", 与
    ``equals(check_metadata=True)`` 的顺序无关语义对齐。
    """
    md = {b"a": b"1", b"b": b"2"}
    d1 = mod._arrow_digest(_int_table(md_schema=dict(md), md_field={b"u": b"cm"}))
    d2 = mod._arrow_digest(_int_table(md_schema=dict(md), md_field={b"u": b"cm"}))
    assert d1["schema_repr"] == d2["schema_repr"]
    assert d1["schema_sha16"] == d2["schema_sha16"]

    d_permuted = mod._arrow_digest(_int_table(md_schema={b"b": b"2", b"a": b"1"}, md_field={b"u": b"cm"}))
    assert d_permuted["schema_sha16"] == d1["schema_sha16"], "键顺序不同的同集合必须同摘要"


def test_digest_equality_tracks_arrow_check_metadata():
    """(b)④ 一致性锁: 摘要等价 ⇔ ``Schema.equals(check_metadata=True)``。

    pair 集只用非 list 类型 —— list 内层 item/element 标签归一是摘要已声明的
    唯一有意偏离 (见 ``_LIST_ELEM_LABELS``), 在 list 类型上两侧语义本就不同。

    ⛔ Codex round-3 MEDIUM 整改: 旧 pair 集漏「同 value 不同 key」与「nested
    子字段 metadata」两类差异 —— 它实证把渲染改成「只按 value 排序、完全忽略
    key」后旧 ④ 仍全绿 (死门)。本 pair 集必须含这两类, 使 key-blind 与
    nested-blind 变体都转红。
    """

    def _struct_table(child_md=None):
        import pyarrow as pa

        child = pa.field("x", pa.int64(), metadata=child_md)
        return pa.table(
            {"n": pa.array([{"x": 1}], pa.struct([child]))},
            schema=pa.schema([pa.field("n", pa.struct([child]))]),
        )

    pairs = [
        (_int_table(), _int_table()),  # 无 vs 无
        (_int_table(), _int_table(md_schema={b"o": b"A"})),  # 无 vs 有 (schema 级)
        (_int_table(), _int_table(md_field={b"u": b"cm"})),  # 无 vs 有 (field 级)
        (  # 有 vs 键顺序不同的同集合
            _int_table(md_schema={b"a": b"1", b"b": b"2"}),
            _int_table(md_schema={b"b": b"2", b"a": b"1"}),
        ),
        (_int_table(md_schema={b"a": b"1"}), _int_table(md_schema={b"a": b"2"})),  # 有 vs 值不同
        (_int_table(md_schema={}), _int_table()),  # {} vs None (schema 级)
        (_int_table(md_field={}), _int_table()),  # {} vs None (field 级)
        # ⛔ key-only 差异 (同 value 不同 key) —— Codex round-3 key-blind 变异死门补丁
        (_int_table(md_schema={b"a": b"1"}), _int_table(md_schema={b"z": b"1"})),
        # ⛔ nested struct 子字段 metadata 差异 —— round-3 HIGH 残余反例原样
        (_struct_table(), _struct_table(child_md={b"unit": b"cm"})),
        (_struct_table(child_md={b"unit": b"cm"}), _struct_table(child_md={b"unit": b"m"})),
        # nested 子字段 key-only 差异
        (_struct_table(child_md={b"a": b"1"}), _struct_table(child_md={b"z": b"1"})),
    ]
    for t1, t2 in pairs:
        arrow_eq = t1.schema.equals(t2.schema, check_metadata=True)
        digest_eq = mod._arrow_digest(t1)["schema_sha16"] == mod._arrow_digest(t2)["schema_sha16"]
        assert arrow_eq == digest_eq, (
            f"摘要与 pyarrow 语义分叉: arrow={arrow_eq} digest={digest_eq} ({t1.schema!r} vs {t2.schema!r})"
        )


def test_digest_renders_nested_struct_child_metadata():
    """(b)⑦ round-3 HIGH 残余回归锁: nested struct 子字段 metadata 必须参与摘要。

    Codex round-3 实证: 只渲染顶层 f.metadata 时, ``struct<x:int64>`` 子字段
    metadata ``{unit:cm}`` vs ``{unit:m}`` 的两张表 ``equals(check_metadata=True)``
    为 False 而 schema_sha16 逐字相同 —— 对账判同后源表被 drop。本条同 ①② 形态:
    差异必须体现在 schema 摘要, 不得污染内容指纹。
    """

    def _struct_table(child_md):
        import pyarrow as pa

        child = pa.field("x", pa.int64(), metadata=child_md)
        return pa.table(
            {"n": pa.array([{"x": 1}], pa.struct([child]))},
            schema=pa.schema([pa.field("n", pa.struct([child]))]),
        )

    d_plain = mod._arrow_digest(_struct_table(None))
    d_cm = mod._arrow_digest(_struct_table({b"unit": b"cm"}))
    d_m = mod._arrow_digest(_struct_table({b"unit": b"m"}))

    assert d_plain["schema_sha16"] != d_cm["schema_sha16"], "nested 子字段有/无 metadata 必须不同"
    assert d_cm["schema_sha16"] != d_m["schema_sha16"], "nested 子字段 metadata 值不同必须不同"
    assert d_cm["content_sha256"] == d_m["content_sha256"] == d_plain["content_sha256"], "metadata 差异不得改变内容指纹"
    # 正向对照: 同 metadata (键顺序无关) 的 nested 表摘要相同
    d_cm2 = mod._arrow_digest(_struct_table({b"unit": b"cm"}))
    assert d_cm2["schema_sha16"] == d_cm["schema_sha16"]

    # ⛔ round-4 Codex MEDIUM 堵口: 双层 struct —— 深层孙字段的 metadata 必须参与
    # （「只扁平渲染直接子字段、不继续递归」的变异在单层 pair 下全绿, 实测可绕过）
    def _nested2_table(leaf_md):
        import pyarrow as pa

        leaf = pa.field("x", pa.int64(), metadata=leaf_md)
        mid = pa.field("m", pa.struct([leaf]))
        return pa.table(
            {"o": pa.array([{"m": {"x": 1}}], pa.struct([mid]))},
            schema=pa.schema([pa.field("o", pa.struct([mid]))]),
        )

    assert (
        mod._arrow_digest(_nested2_table(None))["schema_sha16"]
        != mod._arrow_digest(_nested2_table({b"unit": b"cm"}))["schema_sha16"]
    ), "双层 struct 的孙字段 metadata 必须参与摘要（递归必须走到底）"


def test_digest_renders_nested_list_child_metadata_and_elem_label():
    """(b)⑧ round-3 补充锁: list 容器 value field 的 metadata/nullable 参与摘要。

    value field 的名字按已声明偏离统一渲染成 ``elem`` (Lance=item / Parquet=
    element, 2026-09-01 实测) —— 所以**仅名字差异**必须判同, 而 value field 的
    metadata 差异必须判异 (普通 list 与 fixed_size_list 各测一遍)。nullable 差异
    是 Arrow 层真差异 (round-3 实测两侧往返保真), 也必须判异。
    """
    import pyarrow as pa

    def _table(ty):
        return pa.table({"v": pa.array([[1]], ty)}, schema=pa.schema([pa.field("v", ty)]))

    # 仅 value-field 名字 item vs element (Lance vs Parquet 往返形态) → 摘要必须相同
    t_item = _table(pa.list_(pa.field("item", pa.int64())))
    t_elem = _table(pa.list_(pa.field("element", pa.int64())))
    assert mod._arrow_digest(t_item)["schema_sha16"] == mod._arrow_digest(t_elem)["schema_sha16"], (
        "value field 名字 item/element 是已声明归一, 不得判异"
    )

    # value field metadata 差异 → 摘要必须不同 (普通 list)
    ty_cm = pa.list_(pa.field("item", pa.int64(), metadata={b"u": b"cm"}))
    t_meta = _table(ty_cm)
    assert mod._arrow_digest(t_item)["schema_sha16"] != mod._arrow_digest(t_meta)["schema_sha16"], (
        "list value field metadata 必须参与摘要"
    )

    # fixed_size_list (vector 列现网同型) 同规则 —— 数据须每列表恰 2 元素
    fsl_plain = pa.list_(pa.int32(), 2)
    t_fsl = pa.table({"v": pa.array([[1, 2]], fsl_plain)}, schema=pa.schema([pa.field("v", fsl_plain)]))
    fsl_cm_ty = pa.list_(pa.field("item", pa.int32(), metadata={b"u": b"cm"}), 2)
    t_fsl_meta = pa.table({"v": pa.array([[1, 2]], fsl_cm_ty)}, schema=pa.schema([pa.field("v", fsl_cm_ty)]))
    assert mod._arrow_digest(t_fsl)["schema_sha16"] != mod._arrow_digest(t_fsl_meta)["schema_sha16"], (
        "fixed_size_list value field metadata 必须参与摘要"
    )

    # value field nullable 差异 → 摘要必须不同 (round-3 实测 nullable 两侧往返保真)
    ty_nn = pa.list_(pa.field("item", pa.int64(), nullable=False))
    t_nn = _table(ty_nn)
    assert mod._arrow_digest(t_item)["schema_sha16"] != mod._arrow_digest(t_nn)["schema_sha16"], (
        "list value field nullable 必须参与摘要"
    )

    # ⛔ round-4 Codex MEDIUM 堵口: struct 内嵌 list —— 递归层的名字归一必须生效
    # （「仅顶层归一 item/element」的变异在只测顶层 list 的断言下全绿, 实测可绕过）
    s_item = pa.schema([pa.field("n", pa.struct([pa.field("v", pa.list_(pa.field("item", pa.int64())))]))])
    s_elem = pa.schema([pa.field("n", pa.struct([pa.field("v", pa.list_(pa.field("element", pa.int64())))]))])
    t_n_item = pa.table({"n": pa.array([{"v": [1]}], s_item.field(0).type)}, schema=s_item)
    t_n_elem = pa.table({"n": pa.array([{"v": [1]}], s_elem.field(0).type)}, schema=s_elem)
    assert mod._arrow_digest(t_n_item)["schema_sha16"] == mod._arrow_digest(t_n_elem)["schema_sha16"], (
        "递归层 value field 名字 item/element 同样必须归一"
    )


def test_apply_reconciles_and_drops_metadata_bearing_table(tmp_path, monkeypatch, capsys):
    """(b)⑤ 端到端正向对照: 带 metadata 的裸表照常归档 + drop, 回读保 metadata。

    证明纳入 metadata **不会**让正常 apply 对账假红 (Lance 与 Parquet 两侧
    均保 metadata, 2026-09-01 实测)。回读断言用原始 schema 对象 +
    ``equals(check_metadata=True)`` 做独立 oracle, 不经被测摘要。
    """
    import pyarrow as pa
    import pyarrow.parquet as _pq

    path = tmp_path / "db" / "lancedb"
    path.parent.mkdir(parents=True)
    db = lancedb.connect(str(path))
    schema = pa.schema(
        [
            pa.field("doc_id", pa.string(), metadata={b"unit": b"cm"}),
            pa.field("content", pa.string()),
        ],
        metadata={b"origin": b"vaultA"},
    )
    db.create_table(
        "vault_notes",
        data=pa.table({"doc_id": ["a", "b"], "content": ["c1", "c2"]}, schema=schema),
    )
    db.create_table("v1_vault_notes", data=_rows("V1", 2))

    rc = _run(["--db-path", str(path), "--active-vault", "v1", "--apply"], monkeypatch)
    report = json.loads(capsys.readouterr().out)

    assert rc == 0
    rec = report["archived"][0]
    assert rec["source"] == "vault_notes"
    assert rec["reconciled"] is True
    assert rec["source_dropped"] is True

    back = _pq.read_table(rec["archive_file"])
    assert back.schema.equals(schema, check_metadata=True), "归档回读必须原样保住 schema+field metadata"


# ── vault 身份归一 ──────────────────────────────────────────────────────────


def test_capitalized_default_is_single_vault(multi_vault_db, monkeypatch, capsys):
    """⛔ Codex round-1 HIGH-2 回归锁: 走应用的 sanitizer, 不自造归一化。

    ``ACTIVE_VAULT="Default"`` 经 ``app.config.sanitize_vault_id`` 归一后是
    ``"default"`` = 单实例部署, 裸表合法。旧实现按原字符串比较, 判成多 vault,
    ``--apply`` 会把正在使用的裸表归档 + drop。
    """
    from app.config import sanitize_vault_id

    assert sanitize_vault_id("Default") == "default", "本锁的前提: 应用确实会归一化大小写"

    for raw in ("Default", "DEFAULT", "  default  "):
        rc = _run(["--db-path", str(multi_vault_db), "--active-vault", raw], monkeypatch)
        report = json.loads(capsys.readouterr().out)
        assert rc == 0, f"{raw!r} 归一后是单 vault, 不该有 pending"
        assert report["single_vault"] is True
        assert report["active_vault_raw"] == raw
        assert report["active_vault_canonical"] == "default"


# ── 安全闸 ──────────────────────────────────────────────────────────────────


def test_uri_db_path_is_refused(multi_vault_db, monkeypatch, capsys):
    """⛔ Codex round-1 BLOCKER-1 回归锁: 带 scheme 的路径一律拒绝。

    ``lancedb.connect("file://X")`` 连到 X, 而 ``Path("file://X").resolve()``
    得到 ``$CWD/file:/X`` —— 安全闸与连接看的不是同一个库, live 拒绝闸被绕过。
    """
    before = _tree_fingerprint(multi_vault_db)
    rc = _run(["--db-path", f"file://{multi_vault_db}", "--active-vault", "v1", "--apply"], monkeypatch)
    err = capsys.readouterr().err
    assert rc == 1
    assert "scheme" in err or "URI" in err
    assert _tree_fingerprint(multi_vault_db) == before, "被拒的调用必须零动作"


def test_apply_refuses_live_store(multi_vault_db, monkeypatch, capsys):
    """live 只读铁律: 目标被判为现网数据面时 --apply 硬拒绝且零动作。"""
    before = _tree_fingerprint(multi_vault_db)
    monkeypatch.setenv("LANCEDB_DATA_PATH", str(multi_vault_db))

    rc = _run(["--db-path", str(multi_vault_db), "--active-vault", "v1", "--apply"], monkeypatch)
    capsys.readouterr()

    assert rc == 1
    assert _tree_fingerprint(multi_vault_db) == before, "被拒的 apply 必须零动作"


def test_targets_live_store_is_not_substring_match(tmp_path, monkeypatch):
    """路径判定走 resolve 比对, 不是子串 —— ``/lancedb-copy`` 不该被误判现网。"""
    monkeypatch.delenv("LANCEDB_DATA_PATH", raising=False)
    assert mod.targets_live_store(Path("/lancedb")) is True
    assert mod.targets_live_store(Path("/lancedb-copy")) is False
    assert mod.targets_live_store(tmp_path) is False


def test_out_inside_db_tree_is_refused(multi_vault_db, monkeypatch, capsys):
    """⛔ Codex round-1 MEDIUM-5 回归锁: 证据文件不得落进 DB 目录树。

    否则 dry-run 自己就往 DB 树里写了文件, "零写入"当场不成立。
    """
    before = _tree_fingerprint(multi_vault_db)
    rc = _run(
        ["--db-path", str(multi_vault_db), "--active-vault", "v1", "--out", str(multi_vault_db / "evidence.json")],
        monkeypatch,
    )
    assert rc == 1
    assert "out" in capsys.readouterr().err
    assert _tree_fingerprint(multi_vault_db) == before


def test_archive_dir_inside_db_tree_is_refused(multi_vault_db, monkeypatch, capsys):
    rc = _run(
        [
            "--db-path",
            str(multi_vault_db),
            "--active-vault",
            "v1",
            "--archive-dir",
            str(multi_vault_db / "arch"),
            "--apply",
        ],
        monkeypatch,
    )
    assert rc == 1
    assert "archive-dir" in capsys.readouterr().err


# ── dry-run: pending 裁定 + 结构性零写入 ─────────────────────────────────────


def test_dry_run_flags_bare_table_and_writes_nothing(multi_vault_db, tmp_path, monkeypatch, capsys):
    before = _tree_fingerprint(multi_vault_db)
    out = tmp_path / "evidence.json"

    rc = _run(
        ["--db-path", str(multi_vault_db), "--active-vault", "v1", "--out", str(out)],
        monkeypatch,
    )
    capsys.readouterr()

    assert rc == 2, "发现 pending 的 dry-run 必须 exit 2 (需人工裁定)"
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["mode"] == "dry-run"
    assert report["pending_count"] == 1
    assert [t["name"] for t in report["pending"]] == ["vault_notes"]
    # 正向对照: 普查确实读到了内容 (否则"零写入"可能只是因为压根没跑起来)
    assert report["pending"][0]["rows"] == 3
    assert report["pending"][0]["content_sha256"]

    assert _tree_fingerprint(multi_vault_db) == before, "dry-run 必须逐字节零写入"


def test_dry_run_exit_zero_when_no_bare_table(tmp_path, monkeypatch, capsys):
    """反向对照: 库里只有 vault 前缀表 → pending=0 + exit 0。

    这条证明 exit 2 不是恒定输出 (否则上一条的 rc==2 不成立于'因为有裸表')。
    """
    path = tmp_path / "db" / "clean"
    path.parent.mkdir(parents=True)
    db = lancedb.connect(str(path))
    db.create_table("v1_vault_notes", data=_rows("V1", 2))

    rc = _run(["--db-path", str(path), "--active-vault", "v1"], monkeypatch)
    capsys.readouterr()
    assert rc == 0


def test_live_shaped_fixture_flags_bare_fingerprints(tmp_path, monkeypatch, capsys):
    """复刻 2026-08-31 现网 /lancedb 的实际形态, 让那条发现可复现。

    实测三张表: canvas_vault_vault_notes (2203 行) / canvas_vault_file_fingerprints
    (64) / **裸 file_fingerprints (77)**。卡文预期"现网无裸表→零动作"只对了一半:
    裸 vault_notes 确实不存在, 但裸 file_fingerprints 在。
    """
    path = tmp_path / "db" / "live-shaped"
    path.parent.mkdir(parents=True)
    db = lancedb.connect(str(path))
    db.create_table("canvas_vault_vault_notes", data=_rows("NOTES", 2))
    fp_rows = [
        {"file_path": f"节点/n{i}.md", "content_hash": f"h{i}", "last_indexed": "2026-05-09", "chunk_count": i}
        for i in range(3)
    ]
    db.create_table("canvas_vault_file_fingerprints", data=fp_rows[:2])
    db.create_table("file_fingerprints", data=fp_rows)

    rc = _run(["--db-path", str(path), "--active-vault", "canvas_vault"], monkeypatch)
    report = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert [t["name"] for t in report["pending"]] == ["file_fingerprints"]
    assert report["pending"][0]["rows"] == 3
    kinds = {t["name"]: t["kind"] for t in report["tables"]}
    assert kinds["canvas_vault_vault_notes"] == "vault_scoped"
    assert kinds["canvas_vault_file_fingerprints"] == "vault_scoped", (
        "vault 前缀的指纹表不得被误判成裸表 — 误判会让归档器提议删掉在用的指纹表"
    )


# ── apply ───────────────────────────────────────────────────────────────────


def test_apply_exports_parquet_outside_db_then_drops(multi_vault_db, monkeypatch, capsys):
    db = lancedb.connect(str(multi_vault_db))
    src_digest = mod.table_digest(db.open_table("vault_notes"))

    rc = _run(["--db-path", str(multi_vault_db), "--active-vault", "v1", "--apply"], monkeypatch)
    report = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert len(report["archived"]) == 1
    rec = report["archived"][0]
    assert rec["source"] == "vault_notes"
    assert rec["reconciled"] is True
    assert rec["source_dropped"] is True
    assert rec["before"]["content_sha256"] == rec["after"]["content_sha256"] == src_digest["content_sha256"]
    assert rec["before"]["schema_repr"] == rec["after"]["schema_repr"]
    assert report["pending_after"] == 0

    archive_file = Path(rec["archive_file"])
    assert archive_file.exists()
    assert not str(archive_file).startswith(str(multi_vault_db) + "/"), "归档必须落在 DB 目录树之外"

    db2 = lancedb.connect(str(multi_vault_db))
    names = mod._table_names(db2)
    assert "vault_notes" not in names
    assert "v1_vault_notes" in names, "vault 前缀表不得被误伤"


def test_archive_survives_client_schema_repair(tmp_path, monkeypatch, capsys):
    """⛔ Codex round-1 BLOCKER-2 回归锁: 归档必须活过后端启动的 schema 自愈。

    ``LanceDBClient.initialize()`` → ``_cache_tables()`` 会对每张非指纹表跑
    ``_check_and_fix_dimension_mismatch()``, **缺 doc_type 列或向量维度不符就
    直接 drop**。旧裸表恰恰就是缺 doc_type 的那一批 —— 若归档副本留在同一个
    LanceDB 里, 下次启动源表与归档会双双消失。

    本条用**真实**的 `_cache_tables()`（不是替身）跑一遍"重启", 再断言归档
    Parquet 仍在、内容指纹不变。
    """
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
    from agentic_rag.clients.lancedb_client import LanceDBClient

    path = tmp_path / "db" / "lancedb"
    path.parent.mkdir(parents=True)
    db = lancedb.connect(str(path))
    # 刻意缺 doc_type —— 正是会被启动自愈 drop 的那种旧表
    db.create_table("vault_notes", data=_rows("LEGACY", doc_type=None))
    db.create_table("v1_vault_notes", data=_rows("V1", 2))
    # 正向对照用: 一张同样缺 doc_type 的 **vault 前缀**表 (不进 pending, 归档后
    # 仍留在库里), 用来证明启动自愈这条路径真的会 drop 东西。
    db.create_table("v1_canvas_nodes", data=_rows("NODES", 2, doc_type=None))

    rc = _run(["--db-path", str(path), "--active-vault", "v1", "--apply"], monkeypatch)
    report = json.loads(capsys.readouterr().out)
    assert rc == 0
    archive_file = Path(report["archived"][0]["archive_file"])
    digest_before = report["archived"][0]["after"]["content_sha256"]
    assert archive_file.exists()

    # ——「重启一次后端」: 真实的启动自愈路径
    client = LanceDBClient(db_path=str(path), embedding_dim=_DIM, vault_id="v1")
    client._db = lancedb.connect(str(path))
    asyncio.run(client._cache_tables())

    # 正向对照: 证明这条自愈路径确实会删东西 —— 否则本测试锁的是个不存在的威胁
    db3 = lancedb.connect(str(path))
    names_after = mod._table_names(db3)
    assert "v1_canvas_nodes" not in names_after, "前提失效: _cache_tables 没有 drop 缺 doc_type 的表, 本锁需重新校准"
    assert "v1_vault_notes" in names_after, "带 doc_type 的正常表不该被自愈误删"

    assert archive_file.exists(), "归档 Parquet 必须活过启动自愈"
    import pyarrow.parquet as _pq

    assert mod._arrow_digest(_pq.read_table(archive_file))["content_sha256"] == digest_before


def test_apply_aborts_without_dropping_when_reconciliation_fails(multi_vault_db, monkeypatch, capsys):
    """⛔ Codex round-1 MEDIUM-5 回归锁: 两阶段 —— 任一张对账失败就一张都不 drop。"""
    db = lancedb.connect(str(multi_vault_db))
    db.create_table("canvas_nodes", data=_rows("NODES", 2))  # 第二张裸表

    real_export = mod.export_table
    calls = {"n": 0}

    def flaky_export(dbc, name, archive_dir, stamp):
        calls["n"] += 1
        rec = real_export(dbc, name, archive_dir, stamp)
        if calls["n"] == 2:
            rec["reconciled"] = False  # 模拟第二张回读对账失败
        return rec

    monkeypatch.setattr(mod, "export_table", flaky_export)
    rc = _run(["--db-path", str(multi_vault_db), "--active-vault", "v1", "--apply"], monkeypatch)
    report = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert "apply_aborted" in report
    names = mod._table_names(lancedb.connect(str(multi_vault_db)))
    assert "vault_notes" in names and "canvas_nodes" in names, "对账未全过时不得 drop 任何源表"
