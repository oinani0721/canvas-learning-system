"""G2-9-F1 跨 vault 连带删表行为门 (BATCH-2026-09-07-第十三批 / CARD-G2-9-F1).

锁的缺陷 (canary CONFIRMED, ``_bmad-output/审查/evidence-g29/
canary-report-20260906T021427Z.json:213-222``): ``LanceDBClient._cache_tables``
把 ``db.table_names()`` 的**全部**表 (含**别的 vault 前缀**的表) 送进
``_check_and_fix_dimension_mismatch``, 于是 vault A 的启动自愈会 drop 掉
schema 与 A 的期望不符的 **vault B 的表** —— 一个 vault 的进程能删掉另一个
vault 的数据。

单点表名前缀单测照不出这条 (``test_lancedb_vault_isolation.py``
``grep -c "lancedb.connect" `` = 0): 它证的是"写去哪张表", 不是"初始化会碰谁
的表"。所以这里全部走**真实** LanceDB (tmp_path) + 真实 ``_cache_tables()``,
路径与 g24 的 ``test_archive_survives_client_schema_repair:617-619`` 同法
(``client._db = lancedb.connect(...)`` + ``asyncio.run(client._cache_tables())``,
**不调** ``initialize()`` —— 它还会去加载 bge-m3)。

四条门:

1. ``test_cache_tables_never_touches_other_vault`` —— 主门。A 的启动自愈不得
   碰 B 的表; **正向对照** A 自己的 drift 表仍被 drop (否则本门锁的是个不存
   在的威胁)。
2. ``test_cache_tables_default_vault_only_touches_bare_tables`` —— default
   vault 的空前缀不得退化成全表扫描, 也不得恒空 (归 default 的 drift 表仍
   自愈)。
3. ``test_cache_tables_scans_beyond_default_page`` —— ``table_names()`` 的
   ``limit=10`` 默认分页盲区已收口 (>10 张表时第 11 张也进扫描)。
4. ``test_list_vault_tables_explicit_none_keeps_bare_scope`` —— 语义反转门:
   ``list_vault_tables(None)`` 必须仍是**裸表口径**, 不得被新增的
   ``_owns_table`` 解析成 active vault。这条是既有承重契约
   ``tests/regression/test_rag_stage1_index_contracts.py:484-490`` 在本卡地盘
   内的**本地副本**, 让"哨兵默认值写错"在本卡自己的门上就红。

5. ``test_prefix_overlap_premises_hold`` + ``test_prefix_overlap_vault_is_not_isolated``
   —— 前者是**不带** xfail 的前提门, 后者是 ``xfail(strict=True)`` 的缺陷锁, 两条各
   参数化为 ``page-inner`` / ``page-outer``。锁住本卡**未闭合**的面 (Codex round-1 与
   round-2 的 HIGH-1): 归属口径 ``startswith(f"{vid}_")`` 让短 id 的 vault **单向**
   认领长 id vault 的表 (需下划线边界; ``ab_x`` 与 vault ``a`` 不碰撞)。其中
   ``page-outer`` 一例是**本卡的分页收口新打开**的可达面 —— ``da690bf8`` 因默认分页
   看不到那张表所以不删, 本卡全量枚举后会删。移交 CARD-G2-9-F2。
   ⚠️ 前提**必须**待在不带 xfail 的那一条里: xfail 会吞掉同一用例内所有失败, 既让
   「夹具坏」与「缺陷仍在」不可区分, 也让 F2 修好后的结果停在 XFAIL 而非承诺的
   ``XPASS(strict)``。

⚠️ default 口径以 ``list_vault_tables:845`` **逐字**为准: ``"_" not in t or
t == FINGERPRINT_TABLE`` —— 判据是"表名**不含任何下划线**", 不是"没有 vault
前缀"。所以裸表 ``canvas_nodes`` (含下划线) 按既有口径**不归 default**, 而
``notes`` (无下划线) 归。本文件的表名按实测口径选取, 并各配一条断言把这个
区别钉住 (2026-09-07 于 lancedb 0.30.2 实测)。

⚠️ 全部数据在 ``tmp_path``, 不碰任何真实库 (与 g23/g24 门同款纪律)。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

lancedb = pytest.importorskip("lancedb")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

from agentic_rag.clients.lancedb_client import LanceDBClient  # noqa: E402

#: A 侧客户端期望的向量维度。与 ``_DRIFT_DIM`` 不同 = schema drift。
_DIM = 8
#: 制造维度漂移用的维度 (``_check_and_fix_dimension_mismatch`` 的第一个 drop 条件)。
_DRIFT_DIM = 16


def _rows(prefix: str, n: int = 2, *, dim: int = _DIM, doc_type: str | None = "note"):
    """建表用的行。``doc_type=None`` 制造第二个 drop 条件 (缺 doc_type 列)。"""
    out = []
    for i in range(n):
        row = {
            "doc_id": f"{prefix}-{i}",
            "content": f"{prefix} content {i}",
            "vector": [0.1 * (i + 1)] * dim,
        }
        if doc_type is not None:
            row["doc_type"] = doc_type
        out.append(row)
    return out


def _all_names(db) -> set[str]:
    """读回全部表名 —— **显式**越过 ``table_names()`` 的 limit=10 默认分页。

    与 ``LanceDBClient._all_table_names:833`` 同法。判据自己若走默认分页, 门③
    就只能看见前 10 张, 等于给自己蒙眼。
    """
    return set(db.table_names(limit=10_000))


def _assert_table_shape(db, name: str, *, dim: int, has_doc_type: bool) -> None:
    """前提断言：夹具**真的**建成了预期 schema —— 不是只建成了「一张表」。

    只断言「表在」不够: 门锁的是 ``_check_and_fix_dimension_mismatch`` 的两个 drop
    条件（:3660 维度不符 / :3665-3672 缺 doc_type 列）。若 ``_rows(dim=16)`` 或
    ``doc_type=None`` 没按预期落盘，门就在锁一个不存在的形态 —— 照样「绿」，却什么
    也没证明（fixture 形态 != 目标形态）。所以这里从库里**读回** schema 与向量长度。
    """
    tbl = db.open_table(name)
    cols = set(tbl.schema.names)
    assert ("doc_type" in cols) is has_doc_type, (
        f"夹具形态不符: {name} 的 doc_type 列"
        f"{'应存在但没有' if has_doc_type else '应缺失但存在'}; 实际列 = {sorted(cols)}"
    )
    vectors = tbl.head(1).to_pydict().get("vector", [])
    assert vectors, f"夹具形态不符: {name} 没有可采样的行，维度检查路径根本不会触发"
    assert len(vectors[0]) == dim, f"夹具形态不符: {name} 的向量维度是 {len(vectors[0])}，预期 {dim}"


def _client(db_path: Path, *, vault_id: str | None, dim: int = _DIM) -> LanceDBClient:
    """g24 :617-618 同法: 直连 tmp 库, **不调** ``initialize()``。"""
    client = LanceDBClient(db_path=str(db_path), embedding_dim=dim, vault_id=vault_id)
    client._db = lancedb.connect(str(db_path))
    return client


# ═══════════════════════════════════════════════════════════════════════════
# 门① 主门 —— A 的启动自愈不得碰 B 的表
# ═══════════════════════════════════════════════════════════════════════════


def test_cache_tables_never_touches_other_vault(tmp_path):
    """vault A 的 ``_cache_tables()`` 不得 drop vault B 的任何表。

    B 的两张表各覆盖一个 drop 条件 (``_check_and_fix_dimension_mismatch``
    :3660 维度不符 / :3665-3672 缺 doc_type 列), 证明过滤挡住的是**整条**
    自愈路径, 不是只挡住其中一个条件。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    # B 的表: 维度 16 != A 期望的 8 → 命中 :3660
    db.create_table("b_canvas_nodes", data=_rows("B-NODES", dim=_DRIFT_DIM))
    # B 的表: 维度**相同**但缺 doc_type 列 → 命中 :3665-3672
    #   (维度对上也照删 = 光比维度的过滤挡不住它)
    db.create_table("b_vault_notes", data=_rows("B-NOTES", dim=_DIM, doc_type=None))
    # A 自己的 drift 表 —— 正向对照, 必须仍被 drop
    db.create_table("a_canvas_nodes", data=_rows("A-NODES", dim=_DRIFT_DIM))

    before = _all_names(db)
    assert before == {"b_canvas_nodes", "b_vault_notes", "a_canvas_nodes"}, (
        f"夹具没建成预期的三张表, 后面的断言全部不可信: {sorted(before)}"
    )
    # 形态前提: 两个 drop 条件各自真的被构造出来了（只断言「表在」证明不了这一点）
    _assert_table_shape(db, "b_canvas_nodes", dim=_DRIFT_DIM, has_doc_type=True)
    _assert_table_shape(db, "b_vault_notes", dim=_DIM, has_doc_type=False)
    _assert_table_shape(db, "a_canvas_nodes", dim=_DRIFT_DIM, has_doc_type=True)

    client = _client(db_path, vault_id="a")
    asyncio.run(client._cache_tables())

    after = _all_names(lancedb.connect(str(db_path)))

    assert "b_canvas_nodes" in after, (
        "vault a 的启动自愈碰了 vault b 的表: b_canvas_nodes (16 维, 有 doc_type) 被 drop 了; "
        f"本次消失的表 = {sorted(before - after)}"
    )
    assert "b_vault_notes" in after, (
        "vault a 的启动自愈碰了 vault b 的表: b_vault_notes (8 维, 缺 doc_type 列) 被 drop 了; "
        f"本次消失的表 = {sorted(before - after)}"
    )
    # 正向对照: 本 vault 的 drift 表仍自愈 —— 否则本门锁的是个不存在的威胁
    assert "a_canvas_nodes" not in after, (
        "前提失效: _cache_tables 没有 drop 本 vault 自己的 drift 表 a_canvas_nodes "
        "(16 维 != 期望的 8 维), 说明自愈路径压根没跑到, 本门需重新校准"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 门② default vault —— 空前缀既不许退化成全表, 也不许恒空
# ═══════════════════════════════════════════════════════════════════════════


def test_cache_tables_default_vault_only_touches_bare_tables(tmp_path):
    """default vault 的扫描面必须与 ``list_vault_tables:845`` 逐字同语义。

    ⛔ 只保留 ``vault_id="default"`` 一例: ``vault_id=None`` **不是** default
    场景 —— ``active_vault_id`` 会经 ``.env`` 的 ``ACTIVE_VAULT`` /
    ``.canvas-config.yaml`` 解析出**真 vault 前缀** (本树实测 ``canvas_vault``),
    三张预置表一张都不归它。

    四张表覆盖 :845 口径的三个分支 + endswith 跳过:
      - ``notes``           无下划线 → **归** default → drift 必须仍被 drop
                            (证明过滤没写成恒空/恒 False)
      - ``canvas_nodes``    含下划线 → 按 :845 **不归** default → 必须仍在
      - ``b_canvas_nodes``  别 vault 前缀 → 必须仍在 (证明没退化成全表扫描)
      - ``file_fingerprints`` == FINGERPRINT_TABLE → 被 :966 的 endswith 跳过
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table("notes", data=_rows("BARE-NOTES", dim=_DRIFT_DIM))
    db.create_table("canvas_nodes", data=_rows("BARE-NODES", dim=_DRIFT_DIM))
    db.create_table("b_canvas_nodes", data=_rows("B-NODES", dim=_DRIFT_DIM))
    db.create_table("file_fingerprints", data=_rows("FP", dim=_DRIFT_DIM))

    before = _all_names(db)
    assert before == {"notes", "canvas_nodes", "b_canvas_nodes", "file_fingerprints"}, (
        f"夹具没建成预期的四张表, 后面的断言全部不可信: {sorted(before)}"
    )
    # 四张都必须是 drift 形态，否则「没被 drop」可能只是因为它们本来就合规
    for _n in ("notes", "canvas_nodes", "b_canvas_nodes", "file_fingerprints"):
        _assert_table_shape(db, _n, dim=_DRIFT_DIM, has_doc_type=True)

    client = _client(db_path, vault_id="default")
    assert client.active_vault_id in ("", "default"), (
        f"夹具没构成 default 场景: active_vault_id={client.active_vault_id!r}"
        "（.env 的 ACTIVE_VAULT / .canvas-config.yaml 会把它解析成真 vault 前缀）"
    )

    asyncio.run(client._cache_tables())
    after = _all_names(lancedb.connect(str(db_path)))

    assert "notes" not in after, (
        "default vault 的自愈没跑到归它的裸表 notes (无下划线, 16 维 != 期望的 8 维): "
        "过滤对 default 写成了恒空/恒 False, 单 vault 部署将永远不自愈"
    )
    assert "canvas_nodes" in after, (
        "default 的扫描面越过了 list_vault_tables:845 的逐字口径: canvas_nodes 含下划线, "
        '按 `"_" not in t or t == FINGERPRINT_TABLE` 不归 default, 却被 drop 了'
    )
    assert "b_canvas_nodes" in after, (
        "default vault 的启动自愈碰了别的 vault 的表 b_canvas_nodes: "
        f"空前缀退化成了全表扫描; 本次消失的表 = {sorted(before - after)}"
    )
    assert "file_fingerprints" in after, (
        "指纹表被 drop 了 —— :966 的 endswith(FINGERPRINT_TABLE) 跳过失效 (RAG-S1 F1 回归)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 门③ 分页盲区 —— >10 张表时第 11 张也要进扫描
# ═══════════════════════════════════════════════════════════════════════════


def test_cache_tables_scans_beyond_default_page(tmp_path):
    """``table_names()`` 默认 ``limit=10`` 的分页盲区必须已收口。

    12 张表按字典序排: ``a_t01..a_t11`` + ``b_zz``。默认分页只回前 10 张,
    于是 drift 的 ``a_t11`` 落在盲区里 —— 库大到 11 张表的部署, 启动自愈就
    永远修不到它。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    for i in range(1, 11):  # a_t01..a_t10 —— 非 drift, 不该被碰
        db.create_table(f"a_t{i:02d}", data=_rows(f"A{i}", dim=_DIM))
    db.create_table("a_t11", data=_rows("A11", dim=_DRIFT_DIM))  # 本 vault 的 drift, 在盲区里
    db.create_table("b_zz", data=_rows("BZZ", dim=_DRIFT_DIM))  # 别 vault 的 drift, 也在盲区里

    before = _all_names(db)
    assert len(before) == 12, f"夹具没建成 12 张表: {sorted(before)}"
    # 前提: 分页边界真的存在 —— 否则本门锁的是个不存在的盲区
    assert len(db.table_names()) == 10, (
        f"前提失效: table_names() 默认没有停在 10 张 (实回 {len(db.table_names())} 张), "
        "lancedb 换了默认 limit, 本门需重新校准"
    )
    assert "a_t11" not in set(db.table_names()), "前提失效: a_t11 不在默认分页的盲区里"
    # 形态前提: a_t11/b_zz 真的是 drift，a_t01 真的不是 —— 否则「谁被删」说明不了问题
    _assert_table_shape(db, "a_t11", dim=_DRIFT_DIM, has_doc_type=True)
    _assert_table_shape(db, "b_zz", dim=_DRIFT_DIM, has_doc_type=True)
    _assert_table_shape(db, "a_t01", dim=_DIM, has_doc_type=True)

    client = _client(db_path, vault_id="a")
    asyncio.run(client._cache_tables())
    after = _all_names(lancedb.connect(str(db_path)))

    assert "a_t11" not in after, (
        "分页盲区未收口: 本 vault 的 drift 表 a_t11 排在 table_names() 默认 limit=10 之外, "
        "启动自愈没扫到它 (应改用 _all_table_names())"
    )
    assert "b_zz" in after, (
        "vault a 的启动自愈碰了 vault b 的表 b_zz: 分页收口后扫描面扩大到全库, "
        f"前缀过滤必须同时生效; 本次消失的表 = {sorted(before - after)}"
    )
    assert "a_t01" in after, "非 drift 的本 vault 表 a_t01 被误删了"


# ═══════════════════════════════════════════════════════════════════════════
# 门④ 语义反转门 —— list_vault_tables(None) 必须仍是裸表口径
# ═══════════════════════════════════════════════════════════════════════════


def test_list_vault_tables_explicit_none_keeps_bare_scope(tmp_path):
    """``list_vault_tables(None)`` 的**裸表口径**不得被本卡改坏。

    这条在改代码**之前就必须是绿的** —— 它锁的不是本卡的新增能力, 而是
    "(c) 的哨兵默认值有没有把既有语义改反"。既有裁判是
    ``tests/regression/test_rag_stage1_index_contracts.py:484-490``
    (``vault_id="testvault"`` 的 client 上 ``list_vault_tables(None)`` 不含
    ``testvault_file_fingerprints``), 那个文件本卡禁改, 所以这里放一份本地副本。

    ⛔ 若 ``_owns_table`` 写成 ``vid = vault_id if vault_id is not None else
    self.active_vault_id``, 显式传入的 ``None`` 会被解析成 active vault,
    本门与上面那条既有门会**一起**变红。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table("a_file_fingerprints", data=_rows("AFP"))
    db.create_table("a_canvas_nodes", data=_rows("ANODES"))
    db.create_table("file_fingerprints", data=_rows("FP"))
    db.create_table("notes", data=_rows("NOTES"))
    db.create_table("canvas_nodes", data=_rows("NODES"))

    client = _client(db_path, vault_id="a")
    assert client.active_vault_id == "a", (
        f"夹具没构成'client 有自己的 vault'场景: active_vault_id={client.active_vault_id!r}"
    )

    bare = set(client.list_vault_tables(None))
    msg = (
        "显式 None = 裸表口径, 不得解析成 active vault "
        "(否则打红 tests/regression/test_rag_stage1_index_contracts.py:489-490)"
    )
    assert "a_file_fingerprints" not in bare, f"{msg}; 实回 {sorted(bare)}"
    assert "a_canvas_nodes" not in bare, f"{msg}; 实回 {sorted(bare)}"
    assert "file_fingerprints" in bare, f"{msg}; 裸指纹表反而丢了, 实回 {sorted(bare)}"
    assert "notes" in bare, f"{msg}; 无下划线的裸表反而丢了, 实回 {sorted(bare)}"
    # :845 逐字口径是 `"_" not in t`, 不是"没有 vault 前缀" —— 含下划线的裸表不归 default
    assert "canvas_nodes" not in bare, (
        'list_vault_tables:845 的既有口径被改宽了: 判据是 `"_" not in t or '
        "t == FINGERPRINT_TABLE`, 含下划线的裸表 canvas_nodes 不归 default; "
        f"实回 {sorted(bare)}"
    )

    owned = set(client.list_vault_tables("a"))
    assert {"a_file_fingerprints", "a_canvas_nodes"} <= owned, f"显式传本 vault 时前缀表反而丢了; 实回 {sorted(owned)}"
    assert not ({"file_fingerprints", "notes", "canvas_nodes"} & owned), (
        f"显式传本 vault 时把裸表也算了进来; 实回 {sorted(owned)}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 门⑤ 未闭合面锁 —— 前缀重叠（xfail strict，跨卡交接给 CARD-G2-9-F2）
#
# 两种形态**可达性不同**，必须分开锁：
#   page-inner  重叠表在默认分页内 → da690bf8 与本卡**都**会删（既有缺陷，本卡未改变）
#   page-outer  重叠表在默认分页外 → da690bf8 **不**删、本卡**会**删
#                                    ⇒ 这是**本卡的分页收口打开的新可达面**
# 后者是 Codex round-2 HIGH-1 的反例，实测存档
# ``evidence-g29f1/high1-r2-pagination-widens-overlap-*.txt``（改前 True / 改后 False）。
# ═══════════════════════════════════════════════════════════════════════════

#: 门⑤ 的两种形态：(id, 填充表数量)。填充表是本 vault 的健康表，用来把重叠表挤出默认分页。
_OVERLAP_SHAPES = [("page-inner", 0), ("page-outer", 10)]


def _overlap_fixture(db_path, filler: int):
    """门⑤ 与其前提门共用的夹具。``filler`` 张健康表用来把重叠表挤出默认分页。"""
    db = lancedb.connect(str(db_path))
    for i in range(filler):
        db.create_table(f"a_{i:02d}", data=_rows(f"FILL{i}"))
    # vault "a_b" 的漂移表 —— 前缀 "a_b_" 恰好以 vault "a" 的前缀 "a_" 开头
    db.create_table("a_b_canvas_nodes", data=_rows("AB-NODES", dim=_DRIFT_DIM))
    client = _client(db_path, vault_id="a")
    return db, client, _all_names(db)


@pytest.mark.parametrize(("shape", "filler"), _OVERLAP_SHAPES)
def test_prefix_overlap_premises_hold(tmp_path, shape, filler):
    """门⑤ 的前提 —— **不带 xfail**，夹具坏了必须以 FAILED 暴露。

    ``xfail`` 会吞掉用例里**所有**的失败，前提断言的也一样。实测（存档
    ``evidence-g29f1/xfail-swallows-premise-*.txt``）：同一个 ``xfail(strict=True)``
    用例里，「夹具没建成」与「缺陷仍在」**都报 xfailed**，不可区分 —— 夹具哪天悄悄坏掉，
    门⑤ 会继续安静地 xfail，看起来一切正常。更要紧的是：F2 把归属修好之后，写在
    xfail 用例里的前提断言会**先失败**，于是结果仍是 XFAIL 而**不是**承诺的
    ``XPASS(strict)``（Codex round-2 MEDIUM）。所以前提必须待在**不带** xfail 的用例里。

    三态由此两两可区分（存档 ``xfail-split-premise-fix-*.txt``）：夹具坏 → 本条 FAILED；
    缺陷仍在 → 本条 passed + 门⑤ xfailed；缺陷修好 → 本条 **FAILED**（归属断言翻转，
    正是它告诉维护者「该去删 xfail 标记了」）+ 门⑤ XPASS(strict)。
    """
    db, client, before = _overlap_fixture(tmp_path / "db", filler)
    assert "a_b_canvas_nodes" in before, f"夹具没建成重叠表，门⑤ 的断言不可信: {sorted(before)}"
    assert len(before) == filler + 1, f"夹具表数不符: 期望 {filler + 1}，实得 {len(before)}"
    _assert_table_shape(db, "a_b_canvas_nodes", dim=_DRIFT_DIM, has_doc_type=True)

    # 分页位置前提 —— 两种形态的**可达性**差别全在这里
    in_default_page = "a_b_canvas_nodes" in set(db.table_names())
    if shape == "page-inner":
        assert in_default_page, "前提失效: page-inner 形态里重叠表竟然不在默认分页内"
    else:
        assert not in_default_page, (
            "前提失效: page-outer 形态里重叠表仍在默认分页内 —— "
            f"填充表没把它挤出去（默认分页 {len(db.table_names())} 张），"
            "本条就区分不出「本卡打开的新可达面」"
        )

    assert client._owns_table("a_b_canvas_nodes", "a"), (
        "前提失效：a_b_canvas_nodes 已经不归 vault a 了 —— 前缀口径可能已被修好，"
        "此时应删掉门⑤ 的 xfail 标记而不是保留它"
    )


@pytest.mark.parametrize(("shape", "filler"), _OVERLAP_SHAPES)
@pytest.mark.xfail(
    strict=True,
    reason=(
        "CARD-G2-9-F1 未闭合面（Codex round-1 HIGH-1 / round-2 HIGH-1）：归属口径是 "
        'startswith(f"{vid}_")，短 id 的 vault 会**单向**认领长 id vault 的表 —— '
        '"a_b_canvas_nodes".startswith("a_") 为真（需要下划线边界，"ab_x" 不碰撞）。'
        "本仓可达：sanitize_vault_id 产出的 id 含下划线（canvas-vault→canvas_vault、"
        "cs 61b→cs_61b）。page-outer 那一例还是**本卡分页收口新打开**的可达面。"
        "修它需要拿到全部 vault 列表做最长前缀优先，超出本卡范围 —— 移交 CARD-G2-9-F2。"
        "修好后本门 XPASS(strict) 会报红，那时请连同前提门的归属断言一起更新。"
    ),
)
def test_prefix_overlap_vault_is_not_isolated(tmp_path, shape, filler):
    """vault ``a`` 不得删掉 vault ``a_b`` 的表 —— 当前**做不到**，故 xfail(strict)。

    这不是「未来可能出问题」的假想：``sanitize_vault_id`` 产出的 vault id 含下划线
    （实测 ``canvas-vault`` → ``canvas_vault``、``cs 61b`` → ``cs_61b``），本项目真实
    用的就是 ``cs_61b``。只要再存在一个 id 为 ``cs`` 的 vault，它的启动自愈就会删掉
    ``cs_61b_*`` 的漂移表。

    夹具与全部前提由 ``test_prefix_overlap_premises_hold`` 独立把守 —— 本用例里
    **不放**任何前提断言，否则 xfail 会把它们的失败一并吞掉。
    """
    db, client, before = _overlap_fixture(tmp_path / "db", filler)
    asyncio.run(client._cache_tables())
    after = _all_names(lancedb.connect(str(tmp_path / "db")))

    assert "a_b_canvas_nodes" in after, (
        "vault a 的启动自愈碰了 vault a_b 的表：前缀口径 startswith('a_') 把 "
        f"a_b_canvas_nodes 认成了自己的; 形态={shape}; 本次消失的表 = {sorted(before - after)}"
    )
