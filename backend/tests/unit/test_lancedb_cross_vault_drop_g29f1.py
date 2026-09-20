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

5. 门⑤ 族 —— ``test_prefix_overlap_premises_hold`` (归属规则门) +
   ``test_prefix_overlap_not_touched_by_cache_tables`` /
   ``test_prefix_overlap_not_touched_by_drop_vault_tables`` (两条消费路径各一:
   启动自愈与显式删索引), 各按 ``page-inner`` / ``page-outer`` 参数化,
   drop 侧再按重叠表种 (数据表 / 指纹表) 参数化。
   锁的面: 短 id 的 vault **单向**认领长 id vault 的表 (需下划线边界;
   ``ab_x`` 与 vault ``a`` 不碰撞)。``page-outer`` 各例是 F1 的分页收口新打开的
   可达面 —— ``da690bf8`` 因默认分页看不到那张表所以不碰, 全量枚举后会碰。

   ⚠️ **CARD-G2-9-F2 (BATCH-2026-09-11-第十四批) 已闭合该缺陷**: 归属改为
   ``_table_owner`` 的**最长前缀优先** (``t`` 归 ``vid`` ⟺ ``vid`` 是已知 vault
   集合 V 中使 ``t.startswith(v + "_")`` 成立的最长那个 v；⛔ **无** ``t == v`` 支)。
   于是本族三条**由缺陷锁 (``xfail(strict=True)``) 翻转成正向隔离门** ——
   标记已删, 它们现在红了就是**真回归**, 不是"缺陷仍在"。
   同步翻转的还有前提门: 它从"断言 ``a_b_*`` 仍归 ``a``"改成断言互前缀两侧
   各归各家 (见该用例 docstring)。

6. 门⑥ ``test_dual_vault_mutual_prefix_isolation`` (F2 新增, 承重) —— 互前缀双
   vault 的**双向**隔离: vault ``a`` 与 ``a_b`` 在同一个库里各自初始化/删索引,
   都不得碰对方的表; 且各自**自己的**漂移表仍被自愈 (正向对照)。

7. 门⑦ ``test_drop_vault_tables_accounts_for_swallowed_failures`` (F2 新增) ——
   ``drop_vault_tables`` 的返回值必须是**实删数**而不是"尝试数": 单表删除失败
   不再被 ``except: pass`` 吞掉, 而是进 ``_last_drop_failures`` + ``logger.error``。

⚠️ default 口径以 ``list_vault_tables:845`` **逐字**为准: ``"_" not in t or
t == FINGERPRINT_TABLE`` —— 判据是"表名**不含任何下划线**", 不是"没有 vault
前缀"。所以裸表 ``canvas_nodes`` (含下划线) 按既有口径**不归 default**, 而
``notes`` (无下划线) 归。本文件的表名按实测口径选取, 并各配一条断言把这个
区别钉住 (2026-09-07 于 lancedb 0.30.2 实测)。

⚠️ 全部数据在 ``tmp_path``, 不碰任何真实库 (与 g23/g24 门同款纪律)。
"""

from __future__ import annotations

import asyncio
import contextlib
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


def _fingerprint_rows(prefix: str, n: int = 2):
    """**真实**指纹表的行 —— 与 ``LanceDBClient._update_fingerprint`` 的 record 同 schema。

    CARD-G2-9-F2 (F1 验收单 B-3 MEDIUM): 旧夹具拿 ``_rows()`` 的普通向量行冒充指纹表,
    于是"指纹表被连带删掉"这条断言证的只是"一张**叫**这个名字的表没了", 证不到
    RAG-S1 H3 原话的那件事 —— **健康可用的变更检测基线**被抹掉。改用真 schema 后,
    门可以在删表之后直接调 ``_get_all_fingerprints()`` 断言基线**读得出来**。
    """
    return [
        {
            "file_path": f"{prefix}/note-{i}.md",
            "content_hash": f"{i:064x}",
            "last_indexed": "2026-09-14T00:00:00",
            "chunk_count": i + 1,
        }
        for i in range(n)
    ]


def _assert_fingerprint_shape(db, name: str, *, rows: int) -> None:
    """前提断言: 指纹表**真的**是指纹 schema, 不是顶着这个名字的向量表。"""
    tbl = db.open_table(name)
    cols = set(tbl.schema.names)
    assert {"file_path", "content_hash", "last_indexed", "chunk_count"} <= cols, (
        f"夹具形态不符: {name} 不是真实指纹 schema; 实际列 = {sorted(cols)}"
    )
    assert "vector" not in cols, f"夹具形态不符: 真实指纹表不该有 vector 列; 实际列 = {sorted(cols)}"
    assert tbl.count_rows() == rows, f"夹具形态不符: {name} 有 {tbl.count_rows()} 行, 预期 {rows}"


def _client(db_path: Path, *, vault_id: str | None, dim: int = _DIM) -> LanceDBClient:
    """g24 :617-618 同法: 直连 tmp 库, **不调** ``initialize()``。"""
    client = LanceDBClient(db_path=str(db_path), embedding_dim=dim, vault_id=vault_id)
    client._db = lancedb.connect(str(db_path))
    return client


@pytest.fixture(scope="module", autouse=True)
def vault_registry_root(tmp_path_factory):
    """让 vault ``a`` 与 ``a_b`` 都被**生产的** vault 发现路径看见 (CARD-G2-9-F2)。

    F2 的最长前缀优先归属要消歧就必须知道"有哪些 vault"(``_known_vault_ids``)。
    本卡选定的**主来源**是 ``VAULTS_ROOT`` 目录枚举 —— 候选规则逐字沿用仓内既有的
    两处生产站点 (``GET /vault/list`` 与 ``review_overview._list_vault_dirs``):
    非隐藏目录 + 含 ``.obsidian/``。所以这里在 tmp 下把两个 vault **真的建出来**,
    走的是生产发现路径本身, 不是往客户端里注入一份现成名单 (注入式夹具只能证明
    "给了名单就能用", 证不到"名单拿得到")。

    ⚠️ ``autouse`` 且 module scope 的第二个理由: 不接管 ``VAULTS_ROOT`` 时, V 会含
    **本机真实**存在的 vault, 本文件全部用例的归属判定就随开发机上有哪些库而变
    (门①③④ 用的 ``a`` / ``b`` / ``notes`` 之类短名尤其危险)。指向 tmp 后行为恒定。

    ⚠️ 全部在 tmp_path_factory 下, 不碰任何现网目录; env 由 MonkeyPatch 上下文恢复,
    ``get_settings`` 的 lru_cache 进出各清一次 —— 否则本模块的 VAULTS_ROOT 会顺着
    缓存漏给同进程后跑的其它测试 (目录级跑时是真实风险)。
    """
    root = tmp_path_factory.mktemp("vaults-root")
    with _vaults_root_override(root, ("a", "a_b")):
        yield root


@contextlib.contextmanager
def _vaults_root_override(root: Path, names):
    """把 ``VAULTS_ROOT`` 指向 ``root`` 并在其下建出 ``names`` 各自的 vault 目录。

    ⚠️ 用**独立**的 ``pytest.MonkeyPatch`` 实例 + 自己 ``undo()``, 不碰调用方的
    ``monkeypatch`` fixture —— 在共享实例上调 ``undo()`` 会把 fixture 自己布下的
    隔离一并撤掉 (踩过: 后续写入落到真实路径)。
    ``get_settings`` 是 lru_cache, 进出各清一次: 出的时候必须在 env **恢复之后**清,
    否则本次的 VAULTS_ROOT 会顺着缓存漏给同进程后跑的其它测试。
    """
    from app.config import get_settings

    for name in names:
        (root / name / ".obsidian").mkdir(parents=True, exist_ok=True)

    mp = pytest.MonkeyPatch()
    mp.setenv("VAULTS_ROOT", str(root))
    get_settings.cache_clear()
    try:
        # 前提: 接管真的生效了 —— 否则下面所有"互不相认"的断言都在证别的东西
        assert Path(get_settings().VAULTS_ROOT).resolve() == root.resolve(), (
            f"VAULTS_ROOT 接管失败: 实为 {get_settings().VAULTS_ROOT!r}"
        )
        yield root
    finally:
        mp.undo()
        get_settings.cache_clear()


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
# 门⑤ 族 —— 互前缀归属门（CARD-G2-9-F2 已把缺陷闭合，两条锁翻转成正向隔离门）
#
# 【历史】F1 期这三条是缺陷锁：归属口径只看"以 {vid}_ 开头"，短 id 的 vault 会
# **单向认领**长 id vault 的表，两条消费路径各一条 xfail(strict=True)，前提门
# 不带 xfail 把守。F2 改成最长前缀优先后缺陷闭合，标记已删。
#
# 【F2 去标时的 XPASS 成因分辨（必须留档，否则后人只会按第一种解读）】
#   (1) 归属被修好 —— 缺陷锁与同族前提门**一起**变色；
#   (2) 有人撤掉了 F1 的分页收口 —— 只有 page-outer 那几例 XPASS，前提门仍绿；
#   (3) 删除本身失败而异常被生产代码吞掉（旧 drop_vault_tables 的 except: pass）
#       —— 表因此保留，归属与分页都没变，只有 drop 侧那几条变绿。
#   F2 实测命中的是 (1)：6 条锁与 6 条前提门同时变色，且门①②③④ 全绿
#   （门③ 仍绿 ⇒ 分页收口在，排除 (2)；(3) 由新增的门⑦ 单独钉住并已排除）。
#   证据见 evidence-g29f2/g29f2-xpass-*.txt。
#
# 三个维度：
#
#   形态（表在不在默认分页内）
#     page-inner  重叠表在默认分页内 → da690bf8 与本卡**都**会碰（既有缺陷）
#     page-outer  重叠表在默认分页外 → da690bf8 **碰不到**、本卡**会碰**
#                                      ⇒ **本卡的分页收口打开的新可达面**
#   消费路径（谁去碰它）
#     cache  启动自愈 _cache_tables  —— 需要该表有 schema 漂移才会被 drop；
#            且 :966 的 endswith(FINGERPRINT_TABLE) 会豁免指纹表
#     drop   DELETE /index → drop_vault_tables → list_vault_tables
#            —— ⚠️ **不需要 schema 漂移**，纯表名归属误判即删（Codex r3 A-2），
#               且**没有**指纹表豁免
#   表种（仅 drop 路径需要区分）
#     canvas_nodes       普通数据表
#     file_fingerprints  ⚠️ 变更检测基线。RAG-S1 H3 的原话是「一次抹掉所有 vault 的
#                        变更检测」—— 它没了比丢一张数据表更重，而 drop 路径不豁免它
#
# 实测存档：high1-r2-pagination-widens-overlap-*.txt（cache 路径）
#           a2-dropvault-path-*.txt（drop 路径，用**健康**表）
#           fingerprint-drift-gap-*.txt（两条路径对指纹表的豁免差别）
# ═══════════════════════════════════════════════════════════════════════════

#: (形态 id, 填充表数量)。填充表是本 vault 的健康表，用来把重叠表挤出默认分页。
#: ⚠️ page-outer 用 **12** 而不是刚好 10（Codex round-2 MEDIUM-4）：填充表恰好 10 张时
#: 它们**全在第一页**，页外只剩本来就该保留的重叠表 —— 此时把 ``list_vault_tables``
#: 退回默认十张枚举，drop 门的正向对照（本 vault 的表一张不剩 + 实删数对得上）照样全绿，
#: 等于没测到分页。12 张时 ``a_10`` / ``a_11`` 落在页外，枚举一退化就当场剩两张。
_OVERLAP_SHAPES = [("page-inner", 0), ("page-outer", 12)]
#: (消费路径, 重叠表名)。指纹表只在 drop 侧单列 —— ``_cache_tables:1045`` 的
#: ``endswith(FINGERPRINT_TABLE)`` 豁免它，而 ``drop_vault_tables`` **不**豁免
#: （``fingerprint-drift-gap-*.txt`` 实测）。
#: ⚠️ 每个 (形态 × 消费路径 × 表) 一个**独立**库：它们跑的都是**有副作用**的操作
#: （删表），共享库会让后跑的用例看到先跑的结果 —— 负控 8 当场抓到过这个串扰
#: （共享时变异体下只有第一条 XPASS，第二条被第一条的残局改掉了语义）。
_OVERLAP_CASES = [
    ("cache", "a_b_canvas_nodes"),
    ("drop", "a_b_canvas_nodes"),
    ("drop", "a_b_file_fingerprints"),
]
#: drop 侧覆盖的两张表（供 drop 锁参数化用）
_OVERLAP_DROP_TABLES = [t for c, t in _OVERLAP_CASES if c == "drop"]

#: CARD-G2-9-F2: 互前缀两侧的 vault id。``a`` 是短 id、``a_b`` 是长 id ——
#: 缺陷的方向是**单向**的（``a`` 会认领 ``a_b_*``，``a_b`` 不会认领 ``a_*``），
#: 所以门必须把两个方向分别断言，只测一边会漏掉半个面。
#: ⚠️ 这两个 id 必须与 ``vault_registry_root`` 在 tmp 下建出来的目录名一致 ——
#: 归属规则靠"已知 vault 集合"消歧，集合里没有 ``a_b`` 时规则会退化成朴素前缀。
_SHORT_VAULT = "a"
_LONG_VAULT = "a_b"


@pytest.fixture(scope="module")
def overlap_envs(tmp_path_factory):
    """一次建好全部 (形态 × 消费路径) 的库并**当场自检**；四种组合各一个独立库。

    ⚠️ **为什么是 module scope、且与前提门共用同一实例**：F1 期这三条里有两条带
    ``xfail``，而 ``xfail`` 会吞掉用例内**任何**失败，**fixture setup 阶段也不例外**
    （实测：setup 抛异常的 xfail 用例照样报 ``xfailed``，不是 ``ERROR``）。让**不带**
    xfail 的前提门用同一个 fixture 实例，setup 失败就会在**它**那里报 ``ERROR``。
    F2 去标后三条都不带 xfail 了，共用实例的理由退化为"建库一次、三条共用"，
    但下面那条顺序纪律**仍然成立**，别因为标记没了就把实时查询搬回用例里。

    ⚠️ **依赖库状态的前提全部在这里查完，不放进前提门**（r5 修正）：隔离门会**改库**
    （``_cache_tables`` / ``drop_vault_tables`` 都删表），而它与前提门共用同一实例 ——
    若执行顺序与定义顺序不同（随机化插件；⚠️ ``-k`` 只做**筛选**不重排，F1 原文说它
    "会打乱执行顺序"过宽 —— B-9），前提门里那次**实时** ``open_table``
    会读到已被删掉的表而**假红**（实测存档
    ``evidence-g29f1/order-dependency-of-shared-fixture-*.txt``：把隔离门定义在前，
    前提门当场 ``ValueError: Table ... was not found``）。在 fixture 里查则**一定**
    发生在任何用例改库之前。前提门于是只剩**不依赖库当前状态**的断言。

    隔离门用例内因此也**只做**「跑被测操作 + 用本 fixture 的 db 句柄枚举 + 断言」，
    不再自己 ``lancedb.connect``（实测旧句柄在 drop 后反映最新状态）。

    ⚠️ CARD-G2-9-F2 (B-3)：重叠**指纹**表改用**真实指纹 schema**
    （``_fingerprint_rows``），不再拿向量行冒充 —— 否则"指纹表被连带删"证到的只是
    "一张同名表没了"，证不到 RAG-S1 H3 说的**健康可用的变更检测基线**被抹掉。
    """
    envs = {}
    for shape, filler in _OVERLAP_SHAPES:
        for consumer, table in _OVERLAP_CASES:
            path = tmp_path_factory.mktemp(f"ov-{shape}-{consumer}-{table[-6:]}") / "db"
            db = lancedb.connect(str(path))
            for i in range(filler):
                db.create_table(f"a_{i:02d}", data=_rows(f"FILL{i}"))
            # drop 路径用**健康**表（它不靠 schema 漂移）；cache 路径要漂移才会被 drop
            is_fingerprint = table.endswith(LanceDBClient.FINGERPRINT_TABLE)
            dim = _DIM if consumer == "drop" else _DRIFT_DIM
            if is_fingerprint:
                db.create_table(table, data=_fingerprint_rows(f"AB-{table}"))
            else:
                db.create_table(table, data=_rows(f"AB-{table}", dim=dim))
            client = _client(path, vault_id=_SHORT_VAULT)
            before = _all_names(db)

            # ── 依赖库状态的前提：此刻查，此刻库还没被任何用例动过 ──────────
            tag = f"[{shape}/{consumer}/{table}]"
            assert len(before) == filler + 1, f"{tag} 夹具表数不符: 期望 {filler + 1}，实得 {len(before)}"
            assert table in before, f"{tag} 夹具没建成重叠表: {sorted(before)}"
            if is_fingerprint:
                _assert_fingerprint_shape(db, table, rows=2)
            else:
                _assert_table_shape(db, table, dim=dim, has_doc_type=True)
            in_page = table in set(db.table_names())
            if shape == "page-inner":
                assert in_page, f"{tag} 前提失效: 重叠表竟然不在默认分页内"
            else:
                assert not in_page, (
                    f"{tag} 前提失效: 重叠表仍在默认分页内 —— 填充表没把它挤出去"
                    f"（默认分页 {len(db.table_names())} 张），就区分不出「本卡打开的新可达面」"
                )

            envs[(shape, consumer, table)] = {
                "db": db,
                "path": path,
                "client": client,
                "before": before,
                "shape": shape,
                "filler": filler,
                "consumer": consumer,
                "table": table,
                "dim": dim,
                "is_fingerprint": is_fingerprint,
                # 供前提门复述 —— 建库当时的快照，不随后续用例改库而变
                "premises_checked": True,
                "in_default_page": in_page,
            }
    return envs


@pytest.mark.parametrize(("consumer", "table"), _OVERLAP_CASES)
@pytest.mark.parametrize(("shape", "filler"), _OVERLAP_SHAPES)
def test_prefix_overlap_premises_hold(overlap_envs, shape, filler, consumer, table):
    """门⑤ 族的归属前提 —— 夹具坏了、或归属规则被改坏，都必须以红色暴露。

    CARD-G2-9-F2 前后这条断言**整个翻了个面**：
    - F1 期（缺陷仍在）断言的是 ``_owns_table(a_b_*, "a")`` 为**真**（锁住缺陷）；
    - F2 起（缺陷已闭合）断言互前缀两侧**各归各家**。

    与隔离门共用 ``overlap_envs``（见该 fixture 的 docstring），因此本条通过就
    等于隔离门那一份夹具也建成了。可区分的两态：夹具坏 → 本条 ERROR/FAILED；
    归属规则被改坏（退回朴素前缀 / 已知 vault 集合被打空）→ **本条** FAILED。
    ⚠️ 不要再写成「本条与隔离门**一起**红」（Codex round-7 LOW 更正）：自 round-4 起
    ``drop_vault_tables`` / ``_cache_tables`` 都有「判不出主人就不碰」的闸，归属被改坏时
    它仍能保住 ``a_b_canvas_nodes``，隔离门因此**可能继续绿**。负控报告必须按**实际红点**
    解释，不能把「前提门红」说成「跨 vault 删除已经发生」。
    （⚠️ F1 原 docstring 写"三态两两可区分"——那是 F1 自己 §五 已撤回的说法：
    xfail 会吞掉同一用例内**任何**失败，"夹具坏"与"缺陷仍在"在缺陷锁**那一侧**
    本就不可区分，可区分性全靠本条不带 xfail。A-4，CARD-G2-9-F2 同步更正。）

    ⚠️ **本条只做不依赖库当前状态的事**（r5 修正）：复述 fixture 的自检结果、
    以及查归属关系（``_owns_table`` 只看表名、vault id 与已知 vault 集合，不读库内容）。
    依赖库状态的检查（表在不在、schema、分页位置）全部在 fixture 里做完 ——
    因为隔离门会把库改掉，而两者共用同一实例，执行顺序一旦与定义顺序不同，写在这里
    的实时查询就会读到被删的表而**假红**（实测见 fixture docstring 引的存档）。
    """
    env = overlap_envs[(shape, consumer, table)]
    client = env["client"]

    assert env["premises_checked"] is True, "fixture 的建库自检没通过"
    assert env["in_default_page"] is (shape == "page-inner"), (
        f"分页位置前提与形态不符: shape={shape} 却 in_default_page={env['in_default_page']}"
    )

    rule = (
        "归属规则 = 最长前缀优先: t 归 vid ⟺ vid 是**已知 vault 集合 V** 中使 "
        "`t.startswith(v + '_')` 成立的**最长**那个 v（无 `t == v` 支）。"
        f"V 的主来源是 VAULTS_ROOT 目录枚举（本文件由 vault_registry_root fixture 在 tmp 下"
        f"建出 {_SHORT_VAULT}/ 与 {_LONG_VAULT}/ 两个含 .obsidian 的目录），"
        "另并入 active vault 与指纹表反推。V 里少了 "
        f"{_LONG_VAULT} 时规则会退化成朴素前缀，本条与隔离门会一起红。"
    )
    assert not client._owns_table(table, _SHORT_VAULT), (
        f"{table} 又被短 id 的 vault {_SHORT_VAULT!r} 认领了（跨 vault 删表的根因）。{rule}"
    )
    assert client._owns_table(table, _LONG_VAULT), (
        f"{table} 没归到它真正的主人 vault {_LONG_VAULT!r} —— 这一侧红说明规则收得过紧，"
        f"该 vault 会删不掉/扫不到自己的表。{rule}"
    )
    assert client._owns_table(f"{_SHORT_VAULT}_canvas_nodes", _SHORT_VAULT), (
        f"vault {_SHORT_VAULT!r} 连自己的 {_SHORT_VAULT}_canvas_nodes 都不认了 —— "
        f"最长前缀优先**只该减少**认领别人的表，不该减少认领自己的表。{rule}"
    )


@pytest.mark.parametrize(("shape", "filler"), _OVERLAP_SHAPES)
def test_prefix_overlap_not_touched_by_cache_tables(overlap_envs, shape, filler):
    """启动自愈路径：vault ``a`` 的 ``_cache_tables`` 不得删掉 vault ``a_b`` 的表。

    CARD-G2-9-F2 起本条**不再带 xfail**（缺陷已由最长前缀优先闭合）——
    它现在是正向隔离门，红了就是真回归。
    """
    env = overlap_envs[(shape, "cache", "a_b_canvas_nodes")]
    asyncio.run(env["client"]._cache_tables())
    after = _all_names(env["db"])
    assert "a_b_canvas_nodes" in after, (
        f"vault {_SHORT_VAULT} 的启动自愈碰了 vault {_LONG_VAULT} 的表：归属把 "
        f"a_b_canvas_nodes 认成了自己的; 形态={shape}; 消失的表 = {sorted(env['before'] - after)}"
    )


@pytest.mark.parametrize("table", _OVERLAP_DROP_TABLES)
@pytest.mark.parametrize(("shape", "filler"), _OVERLAP_SHAPES)
def test_prefix_overlap_not_touched_by_drop_vault_tables(overlap_envs, shape, filler, table):
    """显式删索引路径（``DELETE /index/{vault_id}`` → ``drop_vault_tables``）。

    CARD-G2-9-F2 起本条**不再带 xfail**（同上）。

    ⚠️ 与启动自愈那条的两点差别：
    1. 重叠表是**健康**的（无 schema 漂移）—— ``drop_vault_tables`` 直接删
       ``list_vault_tables`` 的结果，**不看 schema**，所以触发条件少一条；
    2. **没有指纹表豁免** —— ``_cache_tables`` 里 ``endswith(FINGERPRINT_TABLE)``
       的跳过在这条路径上不存在，所以 ``a_b_file_fingerprints`` 也会被删掉，
       那等于抹掉 vault ``a_b`` 的**变更检测基线**（RAG-S1 H3）。指纹表用例因此
       在删表之后再断言基线**读得出来**（B-3：真 schema 才证得到"健康可用"）。

    ⚠️ 每个 ``table`` 参数有**自己独立**的库 —— 共享会串扰：本用例跑的
    ``drop_vault_tables`` 有副作用，共享时后跑的参数看到的是先跑那个的残局
    （负控 8 当场抓到：共享时变异体下只有第一条 XPASS）。

    ⚠️ **正向对照必须覆盖 page-outer**（Codex round-1 MEDIUM-5）：只断言「对方的表还在」
    时，把 ``list_vault_tables`` 退回默认十张枚举也能全绿（前十张填充表被删、排在页外的
    重叠表本来就该留）。所以这里同时断言**本 vault 的填充表一张不剩**且返回的实删数
    等于填充表数 —— 页外那张若扫不到，实删数当场对不上。
    """
    env = overlap_envs[(shape, "drop", table)]
    dropped = env["client"].drop_vault_tables(_SHORT_VAULT)
    after = _all_names(env["db"])
    assert table in after, (
        f"删 vault {_SHORT_VAULT} 的索引连带删掉了 vault {_LONG_VAULT} 的表 {table}："
        f"list_vault_tables({_SHORT_VAULT!r}) 把它算成了自己的; 形态={shape}; "
        f"消失的表 = {sorted(env['before'] - after)}"
    )
    # 正向对照：本 vault 的填充表（page-outer 形态下有 10 张）必须全被删掉
    own_left = {t for t in after if t.startswith(f"{_SHORT_VAULT}_") and t != table}
    assert not own_left, (
        f"删 vault {_SHORT_VAULT} 的索引没删干净它自己的表: 还剩 {sorted(own_left)}; 形态={shape} "
        "—— 若这里只剩页外那几张，说明表名枚举退回了默认 limit=10 分页"
    )
    assert dropped == filler, (
        f"实删数 {dropped} != 本 vault 的表数 {filler}（形态={shape}）—— "
        "枚举面或记账口径不对；页外的表没被扫到时这个数会偏小"
    )
    if env["is_fingerprint"]:
        # B-3：表还在不等于基线还能用 —— 用 a_b 自己的客户端把指纹读回来
        long_client = _client(env["path"], vault_id=_LONG_VAULT)
        baseline = long_client._get_all_fingerprints()
        assert len(baseline) == 2, (
            f"vault {_LONG_VAULT} 的变更检测基线读不出来了（实回 {baseline!r}）—— "
            "表名还在但内容/schema 已不可用，等于 RAG-S1 H3 说的那件事照样发生了"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 门⑥ 互前缀双 vault 的**双向**隔离（CARD-G2-9-F2 新增，承重）
#
# 缺陷方向是单向的（短 id 认领长 id），但"修好了"必须两个方向都成立：
#   正向  a  的自愈/删索引不碰 a_b 的表  ← 缺陷面本身
#   反向  a_b 的自愈/删索引不碰 a  的表  ← 防"修过头"（把归属收成谁都不认）
# 每个场景一个**独立**库：自愈与删索引都有副作用，共享库会让后一个场景
# 看到前一个的残局（同 _OVERLAP_CASES 的教训）。
# ═══════════════════════════════════════════════════════════════════════════


def _seed_mutual(db_path: Path, *, a_dim: int, ab_dim: int):
    """建互前缀双 vault 的三张表：a 的一张 + a_b 的两张（含**真实** schema 的指纹表）。"""
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-NODES", dim=a_dim))
    db.create_table(f"{_LONG_VAULT}_canvas_nodes", data=_rows("AB-NODES", dim=ab_dim))
    db.create_table(f"{_LONG_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("AB"))
    before = _all_names(db)
    assert before == {
        f"{_SHORT_VAULT}_canvas_nodes",
        f"{_LONG_VAULT}_canvas_nodes",
        f"{_LONG_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}",
    }, f"夹具没建成预期的三张表, 后面的断言全部不可信: {sorted(before)}"
    _assert_fingerprint_shape(db, f"{_LONG_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", rows=2)
    return db, before


def test_dual_vault_mutual_prefix_isolation(tmp_path, vault_registry_root):
    """互前缀的 ``a`` 与 ``a_b`` 各自初始化 / 删索引，都不得碰对方的表。

    ⚠️ 本门与门⑤ 族的分工：门⑤ 族证的是**归属判定**与两条消费路径在 page-inner /
    page-outer 两种形态下的行为；本门证的是**两个 vault 真的并存**时的双向隔离
    （含"自己的表仍被处理"这一侧的正向对照 —— 否则把 ``_owns_table`` 写成恒 False
    也能让"不碰对方"全绿）。

    ⚠️ 前提：两个 vault 都必须被**已知 vault 集合**看见。``vault_registry_root``
    已在 tmp 下把 ``a/`` 与 ``a_b/`` 两个含 ``.obsidian`` 的目录建出来，这里显式
    断言集合里两个都在 —— 集合缺一个，最长前缀优先就退化成朴素前缀（缺陷复活），
    而那种失败若不显式断言就会以"某张表莫名其妙没了"的形式出现，难以归因。
    """
    fp_table = f"{_LONG_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}"

    # ── 前提：发现路径真的把两个 vault 都找出来了 ──────────────────────────
    probe = _client(tmp_path / "probe-db", vault_id=_SHORT_VAULT)
    known = probe._known_vault_ids()
    assert {_SHORT_VAULT, _LONG_VAULT} <= known, (
        f"已知 vault 集合缺成员: {sorted(known)} —— 主来源是 VAULTS_ROOT 目录枚举"
        f"（{vault_registry_root}），少了谁谁的表就会被 id 更短的 vault 认领"
    )

    # ── 场景 1: a 的启动自愈 ──────────────────────────────────────────────
    db1, before1 = _seed_mutual(tmp_path / "db-cache-a", a_dim=_DRIFT_DIM, ab_dim=_DRIFT_DIM)
    asyncio.run(_client(tmp_path / "db-cache-a", vault_id=_SHORT_VAULT)._cache_tables())
    after1 = _all_names(db1)
    assert f"{_LONG_VAULT}_canvas_nodes" in after1, (
        f"vault {_SHORT_VAULT} 的启动自愈删掉了 {_LONG_VAULT} 的数据表; 消失的表 = {sorted(before1 - after1)}"
    )
    assert fp_table in after1, (
        f"vault {_SHORT_VAULT} 的启动自愈删掉了 {_LONG_VAULT} 的指纹表（变更检测基线）; "
        f"消失的表 = {sorted(before1 - after1)}"
    )
    assert f"{_SHORT_VAULT}_canvas_nodes" not in after1, (
        f"正向对照失败: vault {_SHORT_VAULT} **自己**的漂移表没被自愈 —— 归属可能被收成了恒 False, "
        "此时「不碰对方」是白给的，本门什么也没证明"
    )

    # ── 场景 2: a_b 的启动自愈（反向） ────────────────────────────────────
    db2, before2 = _seed_mutual(tmp_path / "db-cache-ab", a_dim=_DRIFT_DIM, ab_dim=_DRIFT_DIM)
    asyncio.run(_client(tmp_path / "db-cache-ab", vault_id=_LONG_VAULT)._cache_tables())
    after2 = _all_names(db2)
    assert f"{_SHORT_VAULT}_canvas_nodes" in after2, (
        f"反向：vault {_LONG_VAULT} 的启动自愈删掉了 {_SHORT_VAULT} 的表; 消失的表 = {sorted(before2 - after2)}"
    )
    assert f"{_LONG_VAULT}_canvas_nodes" not in after2, f"正向对照失败: vault {_LONG_VAULT} **自己**的漂移表没被自愈"
    assert fp_table in after2, "指纹表被自愈路径删了 —— endswith(FINGERPRINT_TABLE) 豁免失效"

    # ── 场景 3: drop_vault_tables("a") 不得删 a_b 的表 ────────────────────
    db3, before3 = _seed_mutual(tmp_path / "db-drop-a", a_dim=_DIM, ab_dim=_DIM)
    client3 = _client(tmp_path / "db-drop-a", vault_id=_SHORT_VAULT)
    dropped3 = client3.drop_vault_tables(_SHORT_VAULT)
    after3 = _all_names(db3)
    assert {f"{_LONG_VAULT}_canvas_nodes", fp_table} <= after3, (
        f"删 vault {_SHORT_VAULT} 的索引连带删了 {_LONG_VAULT} 的表; 消失的表 = {sorted(before3 - after3)}"
    )
    assert f"{_SHORT_VAULT}_canvas_nodes" not in after3, (
        f"正向对照失败: 删 vault {_SHORT_VAULT} 的索引没删掉它**自己**的表"
    )
    assert dropped3 == 1, f"实删数应为 1（只有 {_SHORT_VAULT} 自己那张），实为 {dropped3}"
    # 指纹基线不只是"表还在"，而是**读得出来**（B-3）
    baseline3 = _client(tmp_path / "db-drop-a", vault_id=_LONG_VAULT)._get_all_fingerprints()
    assert len(baseline3) == 2, f"vault {_LONG_VAULT} 的变更检测基线读不出来了: {baseline3!r}"

    # ── 场景 4: drop_vault_tables("a_b") 不得删 a 的表（反向） ────────────
    db4, before4 = _seed_mutual(tmp_path / "db-drop-ab", a_dim=_DIM, ab_dim=_DIM)
    client4 = _client(tmp_path / "db-drop-ab", vault_id=_LONG_VAULT)
    dropped4 = client4.drop_vault_tables(_LONG_VAULT)
    after4 = _all_names(db4)
    assert f"{_SHORT_VAULT}_canvas_nodes" in after4, (
        f"反向：删 vault {_LONG_VAULT} 的索引连带删了 {_SHORT_VAULT} 的表; 消失的表 = {sorted(before4 - after4)}"
    )
    assert not ({f"{_LONG_VAULT}_canvas_nodes", fp_table} & after4), (
        f"正向对照失败: 删 vault {_LONG_VAULT} 的索引没删掉它自己的两张表; 现存 = {sorted(after4)}"
    )
    assert dropped4 == 2, f"实删数应为 2（{_LONG_VAULT} 自己的数据表 + 指纹表），实为 {dropped4}"


# ═══════════════════════════════════════════════════════════════════════════
# 门⑦ drop_vault_tables 记账不吞（CARD-G2-9-F2 新增）
# ═══════════════════════════════════════════════════════════════════════════


class _DropFailsOn:
    """真库句柄 + 只在**指定表**上让 ``drop_table`` 抛的薄包装。

    ⚠️ 这是**故障注入**不是 mock：被测对象仍是真 ``drop_vault_tables`` + 真 LanceDB
    库 + 真表，只在"删这一张时 I/O 失败"这一个点上注入（同款做法在邻近门
    ``test_g24_lance_legacy_table_removal.py`` 里已有先例）。
    真去造一张"删得动的表突然删不动"在文件系统层面不可稳定复现，而这条门锁的正是
    "删失败时会不会被静默吞掉"，没有失败就没有门。
    """

    def __init__(self, db, boom: str):
        self._db = db
        self._boom = boom

    def __getattr__(self, item):
        return getattr(self._db, item)

    def drop_table(self, name, *args, **kwargs):
        if name == self._boom:
            raise RuntimeError(f"injected I/O failure while dropping {name}")
        return self._db.drop_table(name, *args, **kwargs)


def test_drop_vault_tables_accounts_for_swallowed_failures(tmp_path):
    """删表失败必须记账，返回值必须是**实删数**而不是"尝试数"。

    改前 ``drop_vault_tables`` 的循环是 ``except Exception: pass`` 且
    ``return len(tables)``：一张都没删成也会回一个非零计数，而
    ``DELETE /index/{vault_id}``（``endpoints/index.py``）把它当 ``tables_dropped``
    回给调用方 —— 调用方据此认为索引已清，实际全留着。

    这同时也是门⑤ 族 XPASS 成因(3)（"删除本身失败而异常被吞掉"）的单独把守点：
    有本门在，成因(3) 就不可能伪装成成因(1)。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-NODES"))
    db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-NOTES"))
    db.create_table(f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("A"))
    db.create_table("b_canvas_nodes", data=_rows("B-NODES"))
    before = _all_names(db)
    assert len(before) == 4, f"夹具没建成 4 张表: {sorted(before)}"

    boom = f"{_SHORT_VAULT}_vault_notes"
    client = _client(db_path, vault_id=_SHORT_VAULT)
    attempted = client.list_vault_tables(_SHORT_VAULT)
    assert len(attempted) == 3, f"前提失效: vault {_SHORT_VAULT} 名下应有 3 张表, 实为 {sorted(attempted)}"
    assert boom in attempted, f"前提失效: 要注入失败的表不在待删清单里: {sorted(attempted)}"

    client._db = _DropFailsOn(db, boom)
    dropped = client.drop_vault_tables(_SHORT_VAULT)

    assert dropped == 2, f"返回值应是**实删数** 2（3 张里 1 张失败），实为 {dropped}"
    assert dropped != len(attempted), (
        "返回值仍等于**尝试数** —— 旧实现正是把 len(tables) 当结果返回, "
        "于是「全部删失败」也会回非零、DELETE /index 回一个骗人的 200"
    )
    assert [name for name, _ in client._last_drop_failures] == [boom], (
        f"被吞的表名没进记账: _last_drop_failures={client._last_drop_failures!r}"
    )
    assert "RuntimeError" in client._last_drop_failures[0][1], (
        f"记账里没带上异常类型/文案: {client._last_drop_failures!r}"
    )

    after = _all_names(db)
    assert boom in after, f"注入失败的表居然被删掉了, 本门的前提不成立; 现存 = {sorted(after)}"
    assert "b_canvas_nodes" in after, f"别的 vault 的表被删了: 现存 = {sorted(after)}"
    assert not ({f"{_SHORT_VAULT}_canvas_nodes", f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}"} & after), (
        f"其余两张本该删掉的表没删成, 一张失败不该拖垮整轮; 现存 = {sorted(after)}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 门⑧ 族 —— CARD-G2-9-F2 初版三个回归的锁（Codex round-1 HIGH-2/3/4）
#
# 这三条锁的都是**本卡初版实现自己踩的坑**，不是 F1 遗留面。没有它们，修复只是
# 一次性的，下一个人照着"设计稿原口径"重写一遍就会把同样的洞打回来。
# ═══════════════════════════════════════════════════════════════════════════


def test_owns_table_does_not_claim_name_equal_to_vault_id(tmp_path):
    """归属规则**不含** ``name == vid`` 那一支（Codex round-1 HIGH-3）。

    设计稿原口径写的是「``t == v`` 或 ``t.startswith(v + "_")``」。加上 ``t == v``
    会出两件事，方向相反但都错：

    1. **认领面变大**（推翻"本卡只减少认领"）：裸指纹表 ``file_fingerprints``
       在旧口径下不归任何叫这个名字的 vault（``startswith("file_fingerprints_")``
       为假），加了这一支就归了 —— ``drop_vault_tables("file_fingerprints")``
       会去删 default 的变更检测基线；
    2. **主人判错**：表名恰等于某 vault id 只可能是**别人**拼出来的 —— vault
       ``a_b`` 的表恒为 ``a_b_<逻辑名>``，永远不会恰是 ``a_b``；而 vault ``a`` 的
       逻辑表 ``b`` 解析出来正好是 ``a_b``。所以 ``a_b`` 的主人是 ``a``。
    """
    client = _client(tmp_path / "db", vault_id=_SHORT_VAULT)

    assert not client._owns_table(LanceDBClient.FINGERPRINT_TABLE, LanceDBClient.FINGERPRINT_TABLE), (
        "裸指纹表被一个与它同名的 vault 认领了 —— 归属规则又长出了 `name == vid` 那一支，"
        "drop_vault_tables('file_fingerprints') 会删掉 default 的变更检测基线"
    )
    assert not client._owns_table(_LONG_VAULT, _LONG_VAULT), (
        f"表 {_LONG_VAULT!r} 被 vault {_LONG_VAULT!r} 认领了 —— 它拼不出这个名字（它的表恒为 {_LONG_VAULT}_<逻辑名>）"
    )
    assert client._owns_table(_LONG_VAULT, _SHORT_VAULT), (
        f"表 {_LONG_VAULT!r} 没归 vault {_SHORT_VAULT!r} —— 它正是 {_SHORT_VAULT} 的逻辑表 'b' 解析出来的名字"
    )


def test_resolve_table_name_stays_idempotent_with_longer_vault(tmp_path):
    """``resolve(resolve(x)) == resolve(x)`` 必须**无条件**成立（Codex round-1 HIGH-4）。

    幂等守卫若改成归属判定，只要库里存在 id 更长的 vault（``a`` 与 ``a_vault`` 并存），
    ``a`` 解析 ``vault_notes`` 得 ``a_vault_notes``，而该名按最长前缀归 ``a_vault``，
    于是**第二次**解析再前缀成 ``a_a_vault_notes``。生产上真的会二次解析：
    ``index_vault_notes`` 解析后把结果传给 ``add_documents``，后者又解析一次 ——
    删除走旧名、写入走新名，读写目标当场分裂，而指纹照常更新，增量索引会认为该文件没变。

    ⚠️ 本用例**自带** VAULTS_ROOT（含 ``a`` 与 ``a_vault``），不用模块级那份 ——
    往模块级 root 里加目录会改掉同模块其它用例的已知 vault 集合。
    """
    with _vaults_root_override(tmp_path / "roots", (_SHORT_VAULT, "a_vault")):
        client = _client(tmp_path / "db", vault_id=_SHORT_VAULT)
        known = client._known_vault_ids()
        assert {_SHORT_VAULT, "a_vault"} <= known, f"前提失效: 已知 vault 集合 = {sorted(known)}"

        once = client.resolve_table_name("vault_notes")
        twice = client.resolve_table_name(once)
        assert once == f"{_SHORT_VAULT}_vault_notes", f"首次解析结果不符预期: {once!r}"
        assert twice == once, (
            f"resolve 不再幂等: 第一次 {once!r}、第二次 {twice!r} —— 幂等守卫被换成了归属判定，"
            "生产的二次解析链（index_vault_notes → add_documents）会让删除与写入落到两张表"
        )


def test_known_vault_ids_cache_does_not_outlive_the_connection(tmp_path):
    """未连库时算出的**缺项**集合不得跨连接沿用（Codex round-1 HIGH-2）。

    指纹来源要读库；``_db`` 还是 ``None`` 时它恒为空集。若把这份结果按 TTL 缓存下来，
    随后 ``connect`` + 启动自愈会在 TTL 内继续用它 —— 库里明明已有别的 vault 的指纹表
    也保护不到（不需要新建 vault，也不需要等索引跑完）。

    这里让目录来源**查不到** ``a_b``（自带一个只含 ``a`` 的 VAULTS_ROOT），于是
    ``a_b`` 能否进集合完全取决于指纹来源，也就完全取决于缓存有没有跨连接沿用。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_LONG_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("AB"))

    with _vaults_root_override(tmp_path / "roots", (_SHORT_VAULT,)):
        # 未连库：此刻指纹来源无从读起
        client = LanceDBClient(db_path=str(db_path), embedding_dim=_DIM, vault_id=_SHORT_VAULT)
        assert client._db is None, "前提失效: 本用例要的是**未连库**的客户端"
        before_connect = client._known_vault_ids()
        assert _LONG_VAULT not in before_connect, (
            f"前提失效: 未连库时就发现了 {_LONG_VAULT}（实得 {sorted(before_connect)}）—— "
            "目录来源没被收窄成只含 a，本用例证不到缓存的事"
        )

        # 立刻连库（远在 TTL 之内）后再问一次
        client._db = lancedb.connect(str(db_path))
        after_connect = client._known_vault_ids()
        assert _LONG_VAULT in after_connect, (
            f"连库后仍未发现 {_LONG_VAULT}（实得 {sorted(after_connect)}）—— "
            "未连库时算出的缺项集合被 TTL 缓存沿用了；此时 vault "
            f"{_SHORT_VAULT} 的启动自愈/删索引会连带处理 {_LONG_VAULT} 的表"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 门⑨ 指纹表的默认分页盲区（Codex round-2 MEDIUM-4/5）
# ═══════════════════════════════════════════════════════════════════════════


def test_fingerprint_baseline_readable_beyond_default_page(tmp_path):
    """指纹表排在 ``table_names()`` 默认 ``limit=10`` **之外**时基线仍读得出来。

    ``_fingerprint_table_exists`` 原先查的是 ``self._db.table_names()``（默认只回前
    10 张）。库里超过 10 张表且指纹表排在页外时它恒答"不存在" ⇒
    ``_get_all_fingerprints`` 回空基线 ⇒ 全库文件都被判成新文件重新索引，而
    ``_update_fingerprint`` 又会走 create_table 分支去建一张**已经存在**的表。

    ⚠️ 这条必须**独立**成门：门⑤ 族 drop 侧的指纹读回发生在本 vault 的表被删光之后，
    那时库里只剩指纹表一张，默认分页也找得到它 —— 证不到分页这件事
    （Codex round-2 MEDIUM-4 点名）。所以这里不删任何表，只把指纹表挤到页外。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    # ⚠️ 填充表名必须按字典序排在 ``a_file_fingerprints`` **之前**，指纹表才会落到页外。
    # （初版写 ``a_t00..`` —— "a_f" < "a_t"，指纹表反而在第一页，本门的前提断言当场抓到。）
    for i in range(12):
        db.create_table(f"{_SHORT_VAULT}_a{i:02d}", data=_rows(f"T{i}"))
    fp_name = f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}"
    db.create_table(fp_name, data=_fingerprint_rows("A"))

    # 前提：分页盲区真的存在（否则本门锁的是个不存在的盲区）
    assert fp_name not in set(db.table_names()), (
        f"前提失效: 指纹表仍在默认分页内（默认分页 {len(db.table_names())} 张），本门证不到分页"
    )
    assert fp_name in _all_names(db), "前提失效: 指纹表根本没建成"

    client = _client(db_path, vault_id=_SHORT_VAULT)
    assert client._fingerprint_table_exists(), (
        "指纹表明明在库里却被判成不存在 —— _fingerprint_table_exists 走了 table_names() 的"
        "默认 limit=10 分页；后果是变更检测基线读空、全库重索引"
    )
    baseline = client._get_all_fingerprints()
    assert len(baseline) == 2, f"变更检测基线读空/读残（实回 {baseline!r}）"


# ═══════════════════════════════════════════════════════════════════════════
# 门⑩ drop 的两道整次拒绝闸（Codex round-2 HIGH-1 / HIGH-3）
# ═══════════════════════════════════════════════════════════════════════════


def test_drop_refuses_when_vault_registry_is_degraded(tmp_path):
    """vault 清单主来源失败时，``drop_vault_tables`` 必须**整次拒绝**（round-2 HIGH-1）。

    主来源（VAULTS_ROOT 目录枚举）失败 ⇒ 归属退回朴素前缀 ⇒ 短 id 的 vault 又会认领
    长 id vault 的表。此刻删索引就是在拿别人的数据赌。删索引可以晚点做，删错没法撤。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A"))
    db.create_table(f"{_LONG_VAULT}_canvas_nodes", data=_rows("AB"))

    # 把 VAULTS_ROOT 指向一个**不存在**的路径 → 主来源失败（不是"扫到了但是空的"）
    missing = tmp_path / "no-such-root"
    from app.config import get_settings

    mp = pytest.MonkeyPatch()
    mp.setenv("VAULTS_ROOT", str(missing))
    get_settings.cache_clear()
    try:
        client = _client(db_path, vault_id=_SHORT_VAULT)
        dropped = client.drop_vault_tables(_SHORT_VAULT)
        assert client._vault_registry_degraded is True, "主来源失败却没有置降级标志 —— 拒绝闸的前提读不到真实状态"
        assert dropped == 0, f"清单降级时仍删了 {dropped} 张表"
        assert client._last_drop_refusal and "降级" in client._last_drop_refusal, (
            f"拒绝原因没记下来: {client._last_drop_refusal!r}"
        )
        after = _all_names(db)
        assert after == {f"{_SHORT_VAULT}_canvas_nodes", f"{_LONG_VAULT}_canvas_nodes"}, (
            f"拒绝了却还是删掉了东西: 现存 {sorted(after)}"
        )
    finally:
        mp.undo()
        get_settings.cache_clear()


def test_drop_refuses_when_fingerprint_would_be_orphaned(tmp_path):
    """指纹表会被留下、内容表被删时，必须**整次拒绝**（round-2 HIGH-3）。

    vault ``a`` 与 vault ``a_file`` 并存时，``a`` 的规范指纹名 ``a_file_fingerprints``
    按最长前缀归了 ``a_file``。若照常删索引：``a`` 的内容表删了、指纹表留着 ⇒ 之后一次
    普通增量索引会把每个文件都判成 unchanged，内容**再也长不回来**。

    ⚠️ 这是**本卡引入**的拆开（改前 ``a_file_fingerprints`` 以 ``a_`` 开头会被一起删掉），
    所以必须由本卡挡住，不能拿"长 vault 以前也可能误删它"抵消。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-NOTES"))
    fp_name = f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}"
    db.create_table(fp_name, data=_fingerprint_rows("A"))
    before = _all_names(db)

    # a_file 只需是个**空** vault（连表都不用有）就足以把 a 的指纹名抢走
    with _vaults_root_override(tmp_path / "roots", (_SHORT_VAULT, "a_file")):
        client = _client(db_path, vault_id=_SHORT_VAULT)
        assert client._table_owner(fp_name, _SHORT_VAULT) == "a_file", (
            f"前提失效: {fp_name} 没被 a_file 抢走（实归 {client._table_owner(fp_name, _SHORT_VAULT)!r}），"
            "本门证不到拆开这件事"
        )
        dropped = client.drop_vault_tables(_SHORT_VAULT)
        assert dropped == 0, f"指纹与内容会被拆开时仍删了 {dropped} 张表"
        assert client._last_drop_refusal and "指纹" in client._last_drop_refusal, (
            f"拒绝原因没记下来: {client._last_drop_refusal!r}"
        )
        assert _all_names(db) == before, f"拒绝了却还是删掉了东西: 现存 {sorted(_all_names(db))}，原有 {sorted(before)}"
        # 基线仍可用 —— 拒绝的意义正在于此
        assert len(client._get_all_fingerprints()) == 2, "拒绝之后变更检测基线反而读不出来了"


# ═══════════════════════════════════════════════════════════════════════════
# 门⑪ 族 —— round-3 三条：拒绝闸的失败分支 / 内容表拆分 / 破坏性路径不吃缓存
# ═══════════════════════════════════════════════════════════════════════════


class _ListTablesFails:
    """真库句柄 + 让**第 n 次**表名枚举抛错的薄包装（只影响 list_tables / table_names）。

    ⚠️ 必须能指定**第几次**：``drop_vault_tables`` 一次调用里会枚举三轮 ——
    ① 刷 vault 清单（指纹来源）② 碰撞预检 ③ ``list_vault_tables`` 取删除集合。
    若让第 ① 轮失败，指纹来源会置降级标志，于是走的是**降级闸**而不是预检的失败分支,
    门就测不到它声称的那一层（初版写 ``fail_times=1`` 正是这样假绿的：降级文案里也含
    「枚举」二字，连断言都一起骗过去了）。
    """

    def __init__(self, db, *, fail_on: int):
        self._db = db
        self._fail_on = fail_on
        self._calls = 0

    def __getattr__(self, item):
        return getattr(self._db, item)

    def _maybe_boom(self):
        self._calls += 1
        if self._calls == self._fail_on:
            raise RuntimeError("injected catalog failure while listing tables")

    def list_tables(self, *args, **kwargs):
        self._maybe_boom()
        return self._db.list_tables(*args, **kwargs)

    def table_names(self, *args, **kwargs):
        self._maybe_boom()
        return self._db.table_names(*args, **kwargs)


def test_drop_refuses_when_table_listing_fails(tmp_path):
    """枚举表名失败时必须**整次拒绝**，不能当成"这些表不存在"放行（round-3 HIGH-1）。

    round-2 那道指纹闸把枚举异常吞成空集：前置检查因此判"指纹表不存在"而放行，
    随后 ``list_vault_tables`` 又枚举成功、照常删内容表 —— 内容删了、基线留着，
    正是这道闸本来要挡的后果。「问不出来」不能当「不存在」。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-NOTES"))
    db.create_table(f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("A"))
    before = _all_names(db)

    client = _client(db_path, vault_id=_SHORT_VAULT)
    # 只让**碰撞预检**那一次（第 2 轮枚举）失败，前后两轮都正常 —— 正是 round-2 漏洞的形态：
    # 预检因异常判「表不存在」而放行，随后第 3 轮枚举成功、照常删内容表。
    client._db = _ListTablesFails(db, fail_on=2)
    dropped = client.drop_vault_tables(_SHORT_VAULT)

    assert dropped == 0, f"枚举失败时仍删了 {dropped} 张表"
    # ⛔ 断言必须绑**预检**那条文案：降级闸的文案里也含「枚举」二字，用它当判据会让
    #    「其实走的是降级闸」也算通过（本门初版就这么假绿过）。
    assert client._last_drop_refusal and "无法枚举表名" in client._last_drop_refusal, (
        f"拒绝原因不是预检的枚举失败分支（可能被降级闸先拦下了）: {client._last_drop_refusal!r}"
    )
    assert client._vault_registry_degraded is False, (
        "本门要的是**预检**枚举失败这条路径，但 vault 清单被判成了降级 —— 注入落在了第 1 轮"
    )
    assert _all_names(db) == before, f"拒绝了却还是删掉了东西: 现存 {sorted(_all_names(db))}"


def test_drop_refuses_when_a_content_table_would_be_orphaned(tmp_path):
    """**内容表**被抢走时同样整次拒绝，不只指纹表（round-3 MEDIUM-1）。

    V = {a, a_vault} 时 ``a_vault_notes``（vault ``a`` 的逻辑表 ``vault_notes``）按最长
    前缀归了 ``a_vault``。round-2 的闸只看指纹表，于是删 ``a`` 会返回 2、却留下一张
    确实由 ``a`` 写出的内容表 —— "只减少认领别人的表"在内容表这一侧同样不成立。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-NODES"))
    db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-NOTES"))
    db.create_table(f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("A"))
    before = _all_names(db)

    with _vaults_root_override(tmp_path / "roots", (_SHORT_VAULT, "a_vault")):
        client = _client(db_path, vault_id=_SHORT_VAULT)
        assert client._table_owner(f"{_SHORT_VAULT}_vault_notes", _SHORT_VAULT) == "a_vault", (
            "前提失效: a_vault_notes 没被 a_vault 抢走，本门证不到内容表拆分"
        )
        dropped = client.drop_vault_tables(_SHORT_VAULT)
        assert dropped == 0, f"内容表会被拆开时仍删了 {dropped} 张表"
        assert client._last_drop_refusal and "拆开删一半" in client._last_drop_refusal, (
            f"拒绝原因没记下来: {client._last_drop_refusal!r}"
        )
        assert _all_names(db) == before, f"拒绝了却还是删掉了东西: 现存 {sorted(_all_names(db))}"


def test_drop_does_not_reuse_a_stale_vault_registry(tmp_path):
    """破坏性路径必须**强制重算** vault 清单，不吃 TTL 缓存（round-3 HIGH-2）。

    某个 vault 的目录**暂时**看不见（``.obsidian`` 被挪走 / 挂载抖动）时，一次普通的归属
    查询会把缺项集合按 TTL 缓存下来。它的表一直都在，不需要等索引跑完，所以
    「五秒内物理上不可能有表」这条理由不成立：目录恢复后若仍在窗口内，删索引照旧越界。

    本门在**同一个客户端、同一个连接**上按时间顺序走：先在 ``a_b`` 不可见时问一次归属
    （把缺项集合装进缓存），再恢复目录，然后立刻删 —— 中间不等待。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A"))
    db.create_table(f"{_LONG_VAULT}_canvas_nodes", data=_rows("AB"))  # 无指纹表：只能靠目录来源发现
    before = _all_names(db)

    root = tmp_path / "roots"
    with _vaults_root_override(root, (_SHORT_VAULT,)):  # 此刻只有 a 可见
        client = _client(db_path, vault_id=_SHORT_VAULT)
        stale = client._known_vault_ids()
        assert _LONG_VAULT not in stale, f"前提失效: {_LONG_VAULT} 此刻就不该可见（实得 {sorted(stale)}）"

        # 目录恢复（同一次 VAULTS_ROOT 接管内，客户端与连接都没换）
        (root / _LONG_VAULT / ".obsidian").mkdir(parents=True)

        dropped = client.drop_vault_tables(_SHORT_VAULT)
        after = _all_names(db)
        assert f"{_LONG_VAULT}_canvas_nodes" in after, (
            f"删 vault {_SHORT_VAULT} 时沿用了陈旧的 vault 清单，连带删掉了 {_LONG_VAULT} 的表; "
            f"消失的表 = {sorted(before - after)}"
        )
        assert dropped == 1, f"实删数应为 1（只有 {_SHORT_VAULT} 自己那张），实为 {dropped}"


# ═══════════════════════════════════════════════════════════════════════════
# 门⑫ 族 —— round-4 四条：模糊表名 / 降级不自愈 / 清单钉住 / 降级结果不缓存
# ═══════════════════════════════════════════════════════════════════════════


def test_drop_refuses_tables_whose_owner_cannot_be_determined(tmp_path):
    """删除集合里出现"判不出主人"的表名时整次拒绝（round-4 H1）。

    这条堵的是已知 vault 集合的**定义域边界**：vault ``a_b`` 的目录被移走（或
    ``.obsidian`` 暂时不见）且它**没有指纹表**时，两条来源都补不回来，扫描却一切正常、
    不置降级 —— 于是 ``a_b_canvas_nodes`` 又归了 ``a``。

    表名本身仍给得出线索：本 vault 自己的表恒为 ``{vid}_{逻辑名}``，而 ``b_canvas_nodes``
    这种"余名里还有下划线、又不是任何逻辑名"的余名，更像另一个 vault 的表。判不出来就不删。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A"))
    db.create_table(f"{_LONG_VAULT}_canvas_nodes", data=_rows("AB"))  # 无指纹表
    before = _all_names(db)

    # 只有 a 的目录 —— a_b 完全不可发现（且它没有指纹表）
    with _vaults_root_override(tmp_path / "roots", (_SHORT_VAULT,)):
        client = _client(db_path, vault_id=_SHORT_VAULT)
        assert _LONG_VAULT not in client._known_vault_ids(), "前提失效: a_b 此刻不该可被发现"
        assert client._vault_registry_degraded is False, (
            "前提失效: 本门要的是**扫描正常但缺项**，不是降级（那条另有门）"
        )

        dropped = client.drop_vault_tables(_SHORT_VAULT)
        assert dropped == 0, f"判不出主人的表在删除集合里，却仍删了 {dropped} 张"
        assert client._last_drop_refusal and "判不出主人" in client._last_drop_refusal, (
            f"拒绝原因不是模糊表名这条: {client._last_drop_refusal!r}"
        )
        assert _all_names(db) == before, f"拒绝了却还是删掉了东西: 现存 {sorted(_all_names(db))}"


def test_cache_tables_skips_healing_when_registry_is_degraded(tmp_path):
    """vault 清单降级时启动自愈**不做维度修复**（round-4 H2）。

    降级 ⇒ 归属退回朴素前缀 ⇒ 自愈会把别的 vault 的漂移表也 drop 掉。自愈是优化，
    晚一轮没有代价；删错没法撤。表句柄照常装载（读侧不受影响），只跳过修复。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A", dim=_DRIFT_DIM))
    db.create_table(f"{_LONG_VAULT}_canvas_nodes", data=_rows("AB", dim=_DRIFT_DIM))
    before = _all_names(db)

    from app.config import get_settings

    mp = pytest.MonkeyPatch()
    mp.setenv("VAULTS_ROOT", str(tmp_path / "no-such-root"))
    get_settings.cache_clear()
    try:
        client = _client(db_path, vault_id=_SHORT_VAULT)
        asyncio.run(client._cache_tables())
        assert client._vault_registry_degraded is True, "前提失效: 主来源没被判成失败"
        assert _all_names(db) == before, f"清单降级时启动自愈仍 drop 了表: 消失的 = {sorted(before - _all_names(db))}"
        assert set(client._tables_cache) == before, (
            f"表句柄装载被一起跳过了（读侧不该受影响）: {sorted(client._tables_cache)}"
        )
    finally:
        mp.undo()
        get_settings.cache_clear()


def test_pinned_vault_ids_freezes_the_registry(tmp_path):
    """``_pinned_vault_ids`` 期间清单不变，退出后立刻恢复跟随（round-4 H3 机制面）。

    ⚠️ 窗口内必须**把 TTL 打到过期**再问：不然把钉住那段查询拿掉，``_known_vault_ids``
    会落到刚刚 ``force_refresh`` 装进去的那份 TTL 缓存上、照样返回同一个集合 —— 门就成了
    空门（本门初版正是这样：负控把钉住查询删掉，它仍 PASSED）。而 H3 说的本来就是
    「TTL 在一次破坏性操作的**中途**到期」，所以这里模拟的正是那一刻。
    """
    root = tmp_path / "roots"
    with _vaults_root_override(root, (_SHORT_VAULT,)):
        client = _client(tmp_path / "db", vault_id=_SHORT_VAULT)
        with client._pinned_vault_ids() as pinned:
            assert _LONG_VAULT not in pinned, f"前提失效: 钉住时就不该有 {_LONG_VAULT}"
            (root / _LONG_VAULT / ".obsidian").mkdir(parents=True)  # 钉住期间目录出现
            client._known_vaults_cached_at = 0.0  # 模拟 TTL 在操作中途到期
            assert client._known_vault_ids() == pinned, (
                "钉住期间清单变了 —— 一次破坏性操作的中途会拿到两份不同的 V，入口处的降级/碰撞检查就管不住后面的删除"
            )
        assert _LONG_VAULT in client._known_vault_ids(force_refresh=True), (
            "解钉之后清单没有恢复跟随目录 —— 钉住漏了还原"
        )


class _RecordPinDuringDrop:
    """真库句柄 + 在每次 ``drop_table`` 时记下"此刻清单是否钉住"。"""

    def __init__(self, db, client):
        self._db = db
        self._client = client
        self.pinned_at_drop = []

    def __getattr__(self, item):
        return getattr(self._db, item)

    def drop_table(self, name, *args, **kwargs):
        self.pinned_at_drop.append(self._client._known_vaults_pinned is not None)
        return self._db.drop_table(name, *args, **kwargs)


def test_drop_runs_under_a_pinned_registry(tmp_path):
    """真正删表的那一刻，清单必须处在钉住状态（round-4 H3 行为面）。

    只测机制不够 —— 得证明 ``drop_vault_tables`` **用上了**它。这里在每次真实
    ``drop_table`` 发生时记录钉住状态，删完再断言全程为真。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A"))
    db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-NOTES"))

    client = _client(db_path, vault_id=_SHORT_VAULT)
    spy = _RecordPinDuringDrop(db, client)
    client._db = spy
    dropped = client.drop_vault_tables(_SHORT_VAULT)

    assert dropped == 2, f"前提失效: 本该删掉 2 张，实删 {dropped}（拒绝原因 {client._last_drop_refusal!r}）"
    assert spy.pinned_at_drop == [True, True], (
        f"删表时清单没有钉住: {spy.pinned_at_drop} —— TTL 可以在流程中段把 V 重算成缺项的"
    )
    assert client._known_vaults_pinned is None, "操作结束后没有解钉"


def test_degraded_registry_result_is_not_cached(tmp_path):
    """降级算出的缺项集合**不进缓存**：来源一恢复，下一次查询立刻正确（round-4 M2）。

    ⚠️ 与 ``test_drop_does_not_reuse_a_stale_vault_registry`` 的分工：那条测的是
    "破坏性路径强制重算"，即使降级结果被缓存了它也会绿（因为它总是 force_refresh）。
    本条测的是缓存本身的性质 —— **不**用 force_refresh，只看普通查询。
    """
    db_path = tmp_path / "db"
    root = tmp_path / "roots"
    (root / _SHORT_VAULT / ".obsidian").mkdir(parents=True)
    (root / _LONG_VAULT / ".obsidian").mkdir(parents=True)

    from app.config import get_settings

    mp = pytest.MonkeyPatch()
    mp.setenv("VAULTS_ROOT", str(tmp_path / "no-such-root"))  # 先失效
    get_settings.cache_clear()
    try:
        client = _client(db_path, vault_id=_SHORT_VAULT)
        degraded = client._known_vault_ids()
        assert client._vault_registry_degraded is True, "前提失效: 主来源没被判成失败"
        assert _LONG_VAULT not in degraded, f"前提失效: 降级时不该发现 {_LONG_VAULT}"

        # 来源恢复（同一客户端、同一连接、远在 TTL 之内），用**普通**查询
        mp.setenv("VAULTS_ROOT", str(root))
        get_settings.cache_clear()
        assert _LONG_VAULT in client._known_vault_ids(), (
            "来源已恢复但清单仍是降级时那份 —— 降级结果被 TTL 缓存住了，「来源已恢复、保护还没恢复」会持续整个窗口"
        )
    finally:
        mp.undo()
        get_settings.cache_clear()


def test_cache_tables_skips_tables_whose_owner_cannot_be_determined(tmp_path):
    """启动自愈同样不碰"判不出主人"的表（Codex round-5 HIGH-1）。

    ⚠️ 与 ``test_drop_refuses_tables_whose_owner_cannot_be_determined`` 是**同一条判据的
    两个入口**：r4 把这道闸只加在了 ``drop_vault_tables``，于是同一个缺项形态
    （vault ``a_b`` 的目录暂时不可见 + 它没有指纹表）还能从**启动自愈**漏过去 ——
    扫描一切正常、不置降级，``a_b_canvas_nodes`` 又归了 ``a``，有漂移就被 drop。

    ⚠️ 与降级那条门的分工：本条要的是「**扫描正常但缺项**」，所以显式断言
    ``_vault_registry_degraded is False`` —— 否则这条门可能是被降级闸挡住的，
    证不到模糊表名这一层（同款假绿在 round-3 的枚举失败门上真发生过）。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    # a 自己的漂移表 —— 正向对照，必须仍被自愈
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A", dim=_DRIFT_DIM))
    # a_b 的漂移表 + 无指纹表 ⇒ 两条来源都补不回来
    db.create_table(f"{_LONG_VAULT}_canvas_nodes", data=_rows("AB", dim=_DRIFT_DIM))
    before = _all_names(db)

    with _vaults_root_override(tmp_path / "roots", (_SHORT_VAULT,)):
        client = _client(db_path, vault_id=_SHORT_VAULT)
        assert _LONG_VAULT not in client._known_vault_ids(), "前提失效: a_b 此刻不该可被发现"
        assert client._vault_registry_degraded is False, (
            "前提失效: 本门要的是**扫描正常但缺项**，不是降级（那条另有门）"
        )

        asyncio.run(client._cache_tables())
        after = _all_names(db)

        assert f"{_LONG_VAULT}_canvas_nodes" in after, (
            f"vault {_SHORT_VAULT} 的启动自愈删掉了判不出主人的表 {_LONG_VAULT}_canvas_nodes —— "
            f"drop 侧有这道闸、自愈侧漏了; 消失的表 = {sorted(before - after)}"
        )
        assert f"{_SHORT_VAULT}_canvas_nodes" not in after, (
            f"正向对照失败: vault {_SHORT_VAULT} **自己**的漂移表（余名是规范逻辑名）没被自愈 —— "
            "这道闸收得过宽，会把正常自愈一起挡掉"
        )
        # 读侧不该受影响：判不出主人的表**句柄照常装载**，只是不进维度修复。
        # ⚠️ 不能断言 `_tables_cache == before` —— 本 vault 自己那张漂移表被自愈 drop 掉后，
        #    会一并从句柄缓存里移除（初版这么写，被本门当场抓到）。
        assert f"{_LONG_VAULT}_canvas_nodes" in client._tables_cache, (
            f"判不出主人的表连句柄都没装载（读侧被误伤）: {sorted(client._tables_cache)}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 门⑬ 族 —— 裸表口径不该被「V 可能缺项」的那几道闸拖累（Codex round-6 MEDIUM-2）
#
# default / 空 vault 走的是裸表口径（`"_" not in name or name == FINGERPRINT_TABLE`），
# 它**根本不查已知 vault 集合**，也就没有任何跨 vault 暴露面：别的 vault 的表恒含
# `{vid}_` 前缀、必然含下划线，一开始就不归 default。所以清单降级拒绝与「判不出主人
# 就不碰」对它是纯代价 —— 单 vault 部署把 VAULTS_ROOT 配错就会连自己的自愈与删索引
# 一起失去。两个入口各锁一条。
# ═══════════════════════════════════════════════════════════════════════════


def test_default_scope_still_drops_when_registry_is_degraded(tmp_path):
    """``VAULTS_ROOT`` 配错时，default 的 ``DELETE /index`` 仍须照常删（round-6 M2）。"""
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table("notes", data=_rows("BARE-NOTES"))  # 无下划线 → 归 default
    db.create_table(LanceDBClient.FINGERPRINT_TABLE, data=_fingerprint_rows("FP"))  # 裸指纹表
    db.create_table("b_canvas_nodes", data=_rows("B"))  # 别 vault 的表 —— 必须不被碰

    from app.config import get_settings

    mp = pytest.MonkeyPatch()
    mp.setenv("VAULTS_ROOT", str(tmp_path / "no-such-root"))
    get_settings.cache_clear()
    try:
        client = _client(db_path, vault_id="default")
        dropped = client.drop_vault_tables("default")
        assert client._vault_registry_degraded is True, "前提失效: 主来源没被判成失败"
        assert client._last_drop_refusal is None, (
            f"裸表口径被清单降级闸拦了（它根本不查 V）: {client._last_drop_refusal!r}"
        )
        assert dropped == 2, f"default 名下两张裸表应被删，实删 {dropped}"
        after = _all_names(db)
        assert after == {"b_canvas_nodes"}, f"要么没删干净、要么碰了别的 vault 的表; 现存 {sorted(after)}"
    finally:
        mp.undo()
        get_settings.cache_clear()


def test_default_scope_still_heals_when_registry_is_degraded(tmp_path):
    """``VAULTS_ROOT`` 配错时，default 的启动自愈仍须修自己的漂移表（round-6 M2）。"""
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table("notes", data=_rows("BARE-NOTES", dim=_DRIFT_DIM))  # 归 default 的漂移表
    db.create_table("b_canvas_nodes", data=_rows("B", dim=_DRIFT_DIM))  # 别 vault 的漂移表
    before = _all_names(db)

    from app.config import get_settings

    mp = pytest.MonkeyPatch()
    mp.setenv("VAULTS_ROOT", str(tmp_path / "no-such-root"))
    get_settings.cache_clear()
    try:
        client = _client(db_path, vault_id="default")
        assert client.active_vault_id in ("", "default"), (
            f"夹具没构成 default 场景: active_vault_id={client.active_vault_id!r}"
        )
        asyncio.run(client._cache_tables())
        assert client._vault_registry_degraded is True, "前提失效: 主来源没被判成失败"
        after = _all_names(db)
        assert "notes" not in after, (
            "清单降级把 default 自己的自愈也停了 —— 裸表口径不查 V，没有被保护的必要，单 vault 部署会因此永远修不了维度"
        )
        assert "b_canvas_nodes" in after, f"default 的自愈碰了别的 vault 的表; 消失的表 = {sorted(before - after)}"
    finally:
        mp.undo()
        get_settings.cache_clear()


# ═══════════════════════════════════════════════════════════════════════════
# 门⑨ 族 —— CARD-LANCE-INDEX-DELETE-CONTRACT (BATCH-2026-09-18-第十五批)
#
# 三件事各自成门:
#   (c) drop_vault_tables_report 的五态互斥完备 + int 包装仍是实删数;
#   (e1) 建表即建指纹表 —— 收口 Codex r7 既有 HIGH「V 缺项且余名恰为规范逻辑名」;
#   (e2) 指纹来源形态核 + 配置后缀守卫 —— 收口 r5-M2 伪 vault;
#   (e3) 自愈链默认分页 4 站点归零。
# ═══════════════════════════════════════════════════════════════════════════


class _DropAlwaysFails:
    """真库句柄 + **每一张**表的 ``drop_table`` 都抛 —— all_failed 态用。

    与 ``_DropFailsOn`` 分成两个类而不是把后者的 ``==`` 改成 ``in``: ``in`` 作用在字符串
    上是**子串**匹配, 会把 ``a_vault`` 这种前缀名一并吃掉, 等于悄悄放宽既有门⑦的注入面。
    """

    def __init__(self, db):
        self._db = db

    def __getattr__(self, item):
        return getattr(self._db, item)

    def drop_table(self, name, *args, **kwargs):
        raise RuntimeError(f"injected io failure while dropping {name}")


@contextlib.contextmanager
def _config_env_override(**env: str):
    """接管若干 env 并让 ``get_settings`` 的 lru_cache 进出各清一次。

    与 ``_vaults_root_override`` 同纪律: **独立** MonkeyPatch 实例, 出的时候在 env 恢复
    **之后**清缓存 (否则本次取值会顺着缓存漏给同进程后跑的其它测试)。
    """
    from app.config import get_settings

    mp = pytest.MonkeyPatch()
    for key, value in env.items():
        mp.setenv(key, value)
    get_settings.cache_clear()
    try:
        yield
    finally:
        mp.undo()
        get_settings.cache_clear()


def test_drop_report_outcomes_are_disjoint(tmp_path):
    """五态互斥且完备, 且 ``drop_vault_tables`` 的 ``int`` 值仍是**实删数**。

    改前这五种情形在返回值上只有 ``0`` 与非 ``0`` 两档, ``DELETE /index`` 因此把
    "拒绝 / 全失败 / 没有表"合并成同一个 404。本门把五态一次全建出来, 断言
    ``outcome`` 两两不同 —— 少了这条, 某两态映射到同一个字符串也能让端点门分别绿。

    ⚠️ **每个场景建两个等价的库** (Codex r1 MEDIUM-6): 一个跑 ``drop_vault_tables_report``,
    另一个跑 ``int`` 包装 ``drop_vault_tables``。初版对 ``dropped`` / ``partial`` 两格图省事
    直接写 ``len(report.dropped)``, 于是"int 包装仍是实删数"这条主张在那两格是**空洞**的 ——
    把包装改成「先跑 report 再恒回 0」, 初版照样绿。删一次表就没了, 所以只能用双库。
    """
    from pathlib import Path

    def _plain(path: Path):
        db = lancedb.connect(str(path))
        db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-N"))
        db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-V"))
        return _client(path, vault_id=_SHORT_VAULT)

    def _empty(path: Path):
        lancedb.connect(str(path))
        return _client(path, vault_id=_SHORT_VAULT)

    def _partial(path: Path):
        db = lancedb.connect(str(path))
        db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-N"))
        db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-V"))
        db.create_table(f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("A"))
        c = _client(path, vault_id=_SHORT_VAULT)
        c._db = _DropFailsOn(db, f"{_SHORT_VAULT}_vault_notes")
        return c

    def _all_fail(path: Path):
        db = lancedb.connect(str(path))
        db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-N"))
        db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-V"))
        c = _client(path, vault_id=_SHORT_VAULT)
        c._db = _DropAlwaysFails(db)
        return c

    def _refused(path: Path):
        db = lancedb.connect(str(path))
        db.create_table(f"{_SHORT_VAULT}_x_y", data=_rows("AXY"))
        return _client(path, vault_id=_SHORT_VAULT)

    cases = [
        ("no_tables", _empty, 0),
        ("dropped", _plain, 2),
        ("partial", _partial, 2),
        ("all_failed", _all_fail, 0),
        ("refused", _refused, 0),
    ]

    seen: dict[str, int] = {}
    reports = {}
    for name, build, expect_int in cases:
        rep = build(tmp_path / f"db-{name}-report").drop_vault_tables_report(_SHORT_VAULT)
        client_int = build(tmp_path / f"db-{name}-int")
        got_int = client_int.drop_vault_tables(_SHORT_VAULT)
        assert got_int == expect_int, (
            f"[{name}] int 包装不是实删数: 实得 {got_int}, 预期 {expect_int} (report.dropped={rep.dropped!r})"
        )
        assert len(rep.dropped) == expect_int, f"[{name}] 回执实删数不符: {rep.dropped!r}"
        seen[rep.outcome] = got_int
        reports[name] = rep

    assert set(seen) == {"no_tables", "dropped", "partial", "all_failed", "refused"}, f"五态没有两两互斥/完备: {seen!r}"
    assert seen == {"no_tables": 0, "dropped": 2, "partial": 2, "all_failed": 0, "refused": 0}, (
        f"int 包装不再是实删数: {seen!r}"
    )

    # 逐态的结构断言
    assert reports["no_tables"].attempted == () and reports["no_tables"].refusal_kind is None
    assert reports["dropped"].failures == ()
    boom = f"{_SHORT_VAULT}_vault_notes"
    assert reports["partial"].failures == ((boom, "RuntimeError"),), (
        f"失败回执只许带表名 + 异常类型名: {reports['partial'].failures!r}"
    )
    assert len(reports["all_failed"].failures) == 2 and reports["all_failed"].dropped == ()
    r5 = reports["refused"]
    assert r5.refusal_kind == "ambiguous" and r5.ambiguous == (f"{_SHORT_VAULT}_x_y",)
    assert r5.refusal and "整次拒绝" in r5.refusal, "完整 refusal 文案必须留在回执里 (只进日志, 不进响应体)"

    # 既有诊断字段的语义零变化 —— 在 partial 的 int 那一跑上就地核
    c_diag = _partial(tmp_path / "db-diag")
    assert c_diag.drop_vault_tables(_SHORT_VAULT) == 2
    assert [name for name, _ in c_diag._last_drop_failures] == [boom], (
        f"既有诊断字段 _last_drop_failures 的语义被改动了: {c_diag._last_drop_failures!r}"
    )
    assert "RuntimeError: " in c_diag._last_drop_failures[0][1], (
        f"既有诊断字段仍须带异常**原文**(类型名 + ': ' + message), 与回执的脱敏形态分工不同: "
        f"{c_diag._last_drop_failures!r}"
    )

    assert _all_names(lancedb.connect(str(tmp_path / "db-refused-int"))) == {f"{_SHORT_VAULT}_x_y"}, (
        "整次拒绝时一张都不许删"
    )


def test_first_content_table_creates_fingerprint_table_for_scoped_vault(tmp_path):
    """(e1) scoped vault 建第一张内容表时, 指纹表**同时**被建出来 (空表, 真 schema)。

    这是 Codex r7 既有 HIGH 的收口手段: ``index_canvas`` 全程不写指纹, 于是"只索引过
    canvas 且目录不可发现"的 vault 在 ``_known_vault_ids`` 的三条来源里全都看不见 ——
    它的表就会被 id 更短的 vault 认领。建表即建指纹表之后, 任何写过内容表的 scoped
    vault 恒有指纹表 ⇒ 来源③ 覆盖它。

    ⚠️ default 必须 **no-op**: ``test_g24_lance_legacy_table_removal.py:246`` 钉死
    "default vault 不得凭空造 prefixed 表", 且裸 ``file_fingerprints`` 是全局共享面。
    """
    db_path = tmp_path / "db"
    lancedb.connect(str(db_path))
    client = _client(db_path, vault_id=_SHORT_VAULT)
    assert asyncio.run(client.add_documents("canvas_nodes", _rows("A-NODES"))) == 2

    db = lancedb.connect(str(db_path))
    fp = f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}"
    assert _all_names(db) == {f"{_SHORT_VAULT}_canvas_nodes", fp}, (
        f"建内容表时没有把指纹表一起建出来: 现存 {sorted(_all_names(db))}"
    )
    tbl = db.open_table(fp)
    assert set(tbl.schema.names) == {"file_path", "content_hash", "last_indexed", "chunk_count"}, (
        f"指纹表 schema 与 _update_fingerprint 的 record 不同列: {tbl.schema.names}"
    )
    assert "vector" not in tbl.schema.names, "指纹表不该有 vector 列"
    assert tbl.count_rows() == 0, "建出来的应是**空**指纹表, 不许伪造基线行"
    # 建出来就必须能被生产的来源③ 认回来 —— 否则这张表白建
    assert _SHORT_VAULT in client._vault_ids_from_fingerprint_tables(), (
        "新建的指纹表没有被 _vault_ids_from_fingerprint_tables 认出来"
    )

    # default 侧: 一张都不许多建
    d_path = tmp_path / "db-default"
    lancedb.connect(str(d_path))
    dclient = _client(d_path, vault_id="default")
    assert dclient.active_vault_id in ("", "default"), f"夹具没构成 default 场景: {dclient.active_vault_id!r}"
    assert asyncio.run(dclient.add_documents("vault_notes", _rows("D"))) == 2
    assert _all_names(lancedb.connect(str(d_path))) == {"vault_notes"}, (
        "default vault 被凭空造出了指纹表 (test_g24:246 的同一条契约)"
    )


def test_index_only_vault_survives_shorter_id_drop_and_heal_when_undiscoverable(tmp_path):
    """**r7 HIGH 锁**: 目录不可发现、只写过内容表的长 id vault 不再被短 id vault 认领。

    场景逐字取自 Codex r7: vault ``a_canvas`` 只索引过 canvas ⇒ 它的表叫
    ``a_canvas_nodes``, 余名 ``canvas_nodes`` **恰好**是规范逻辑名 ⇒ 闸④ 的模糊名判据
    看不出问题; 而它的目录不在 ``VAULTS_ROOT`` 下 ⇒ 来源② 也看不见它。改前 V = {a},
    ``a_canvas_nodes`` 被判给 ``a``, drop 与启动自愈两条路径都会把它删掉。

    (e1) 之后 ``a_canvas`` 写内容表时顺带留下 ``a_canvas_file_fingerprints`` ⇒ 来源③
    把它补回 V ⇒ 归属回到 ``a_canvas``。两条路径同时闭合, 本门各断一次。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    # vault a 自己的漂移表 —— 自愈侧的正向对照 (证明自愈路径真的跑到了)
    db.create_table(f"{_SHORT_VAULT}_vault_notes", data=_rows("A-V", dim=_DRIFT_DIM))

    root = tmp_path / "vaults-only-a"
    with _vaults_root_override(root, (_SHORT_VAULT,)):
        # vault a_canvas 只走内容表写入 (index_canvas 同型), 全程不写指纹记录
        ac = _client(db_path, vault_id="a_canvas", dim=_DRIFT_DIM)
        assert asyncio.run(ac.add_documents("nodes", _rows("AC", dim=_DRIFT_DIM))) == 2

        names = _all_names(lancedb.connect(str(db_path)))
        assert {f"{_SHORT_VAULT}_vault_notes", "a_canvas_nodes"} <= names, f"夹具形态不符: {sorted(names)}"
        rows_before = lancedb.connect(str(db_path)).open_table("a_canvas_nodes").count_rows()
        assert rows_before == 2

        client_a = _client(db_path, vault_id=_SHORT_VAULT)
        assert "a_canvas" not in client_a._discover_vault_ids_from_root(), (
            "前提失效: a_canvas 竟然是目录可发现的, 本门锁的就不是 r7 那个场景了"
        )

        # 路径一: 显式删索引 —— 先断**表还在**, 再断"拒绝是可见的"。
        # ⛔ 顺序不可换: 把机制断言 (V 里有没有 a_canvas) 放前面, 负控就会红在机制上,
        # 读不出"锁住的那张表到底有没有被删"。
        report = client_a.drop_vault_tables_report(_SHORT_VAULT)
        mid = _all_names(lancedb.connect(str(db_path)))
        assert "a_canvas_nodes" in mid, (
            f"删 vault {_SHORT_VAULT} 的索引连带删掉了 vault a_canvas 的表 a_canvas_nodes "
            f"(它余名恰是规范逻辑名 canvas_nodes, 闸④ 看不出问题); 消失的表 = {sorted(names - mid)}"
        )
        assert report.refusal_kind == "collision", (
            f"a 的 canvas_nodes 逻辑位被 a_canvas 占着, 应当**可见地**整次拒绝而不是静默不作为: {report!r}"
        )
        assert report.dropped == (), f"整次拒绝时一张都不许删: {report.dropped!r}"
        assert "a_canvas" in client_a._known_vault_ids(force_refresh=True), (
            "指纹来源没把 a_canvas 补回 V —— (e1) 没生效, 归属会退回朴素前缀"
        )

        # 路径二: 启动维度自愈 (a_canvas_nodes 是 16 维, 对 8 维的 a 来说是漂移表)
        asyncio.run(client_a._cache_tables())

    after_db = lancedb.connect(str(db_path))
    after = _all_names(after_db)
    assert "a_canvas_nodes" in after, (
        f"vault {_SHORT_VAULT} 认领并删掉了 vault a_canvas 的表 a_canvas_nodes; 现存 = {sorted(after)}"
    )
    assert after_db.open_table("a_canvas_nodes").count_rows() == rows_before, (
        "a_canvas_nodes 还在, 但行数变了 —— 被当成自己的漂移表重建过"
    )
    assert f"a_canvas_{LanceDBClient.FINGERPRINT_TABLE}" in after, (
        f"a_canvas 的变更检测基线被连带删掉了; 现存 = {sorted(after)}"
    )
    # 正向对照: a 自己的漂移表仍被自愈 drop —— 否则本门锁的是一条压根没跑到的路径
    assert f"{_SHORT_VAULT}_vault_notes" not in after, (
        f"前提失效: 启动自愈没有 drop 掉 {_SHORT_VAULT} 自己的漂移表, 本门需重新校准; 现存 = {sorted(after)}"
    )


def test_configured_name_ending_with_fingerprints_does_not_forge_vault(tmp_path):
    """**M2 锁**: 配置名撞上指纹表后缀时, 不得凭空反推出一个伪 vault。

    Codex r5-M2: ``LANCEDB_INDEX_TABLE_NAME=custom_file_fingerprints`` 时 vault ``a``
    的普通向量表叫 ``a_custom_file_fingerprints``, 而来源③ 改前**只看名字后缀**, 于是
    把 ``a_custom`` 当成一个真 vault 塞进 V ⇒ 删 ``a`` 的索引被闸③ 当成命名碰撞整次拒绝,
    vault ``a`` 永远删不掉自己的索引。

    改后两件事: 形态核 (有 ``vector`` 列 ⇒ 不是指纹表) 把伪 vault 挡在 V 外; 配置守卫
    让这个名字不并入逻辑名。⇒ 闸③ 不再误拒。

    ⚠️ 如实声明**终态**（Codex r2 HIGH-B 整改后已变，r3 LOW-1 点名此处说明滞后）:
    那张占名表带 ``vector``, 形态核排除它时**同时置降级**, 于是落的是**闸①**
    ``registry_degraded``, 不是闸④ ``ambiguous``。两者都是「整次拒绝」, 而 registry_degraded
    更准确 —— 问题本来就是「V 不可信」。把"配置名与指纹命名空间撞车"定性为**配置错误**
    并让它响, 而不是让系统去猜。本门把终态钉死, 不留"以为能删"的错觉。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    forged = f"{_SHORT_VAULT}_custom_{LanceDBClient.FINGERPRINT_TABLE}"
    db.create_table(forged, data=_rows("A-CUSTOM"))  # **真**向量表, 不是指纹表
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("A-N"))
    assert "vector" in db.open_table(forged).schema.names, "前提失效: 它必须是带 vector 的普通表"

    with _config_env_override(LANCEDB_INDEX_TABLE_NAME=f"custom_{LanceDBClient.FINGERPRINT_TABLE}"):
        client = _client(db_path, vault_id=_SHORT_VAULT)
        known = client._known_vault_ids(force_refresh=True)
        assert f"{_SHORT_VAULT}_custom" not in known, (
            f"普通向量表 {forged!r} 被按名字后缀反推成了伪 vault a_custom; V = {sorted(known)}"
        )
        assert client._vault_registry_degraded is True, (
            "形态核排除这张占名表时没有置降级 —— 那会让补建钩子的「名字在就早退」与形态核的"
            "「按 schema 排除」互相抵消, 该 vault 从 V 里消失而它的内容表还在 (Codex r2 HIGH-B)"
        )
        report = client.drop_vault_tables_report(_SHORT_VAULT)
        assert report.refusal_kind != "collision", f"闸③ 仍在误拒 (r5-M2 症状未消失): {report.refusal!r}"
        # 终态钉死。⚠️ Codex r2 HIGH-B 整改后它从 `ambiguous` 变成 `registry_degraded`:
        # 形态核排除这张占名表的同时置降级, 闸① 因此先于闸④ 开火。两者都是「整次拒绝」,
        # 而 registry_degraded 更准确 —— 问题本来就是「V 不可信」, 不是「某张表判不出主人」。
        assert report.refusal_kind == "registry_degraded", f"终态变了, 本门需重新校准: {report!r}"
        assert report.dropped == () and client.drop_vault_tables(_SHORT_VAULT) == 0

    assert _all_names(lancedb.connect(str(db_path))) == {forged, f"{_SHORT_VAULT}_canvas_nodes"}, (
        "整次拒绝时一张都不许删"
    )


def test_canonical_logicals_drop_fingerprint_suffixed_config(tmp_path):
    """配置守卫: 撞指纹后缀的配置名不并入逻辑名; 正常配置名照并 (控制组)。

    没有控制组的话, 一个"永远返回内置集"的实现也能让上面两条断言全绿 —— 那会让
    ``LANCEDB_INDEX_TABLE_NAME`` 配出来的真实表名在闸③/闸④ 里彻底失明。
    """
    db_path = tmp_path / "db"
    lancedb.connect(str(db_path))
    client = _client(db_path, vault_id=_SHORT_VAULT)
    builtin = LanceDBClient._BUILTIN_LOGICAL_TABLES

    with _config_env_override(LANCEDB_INDEX_TABLE_NAME=f"custom_{LanceDBClient.FINGERPRINT_TABLE}"):
        assert client._canonical_logical_tables() == builtin, "撞指纹后缀的配置名不得并入逻辑名"
    # ⚠️ **这一格是空洞的, 如实标注** (Codex r1 MEDIUM-4): `file_fingerprints` 本来就在
    # `_BUILTIN_LOGICAL_TABLES` 里, 所以"并不并入"对结果毫无影响 —— 把守卫的相等分支整个
    # 删掉, 下面第一条断言照样绿。它唯一的实际效果是多打一条 logger.error。
    # 真正有判别力的是上一格(`custom_file_fingerprints`)。
    # ⛔ 随之更正一条过强表述: 配置恰为 `file_fingerprints` 时**没有** 409 终态 ——
    # `{vid}_file_fingerprints` 就是本 vault 的规范指纹表, 会被正常删掉并回 200。
    with _config_env_override(LANCEDB_INDEX_TABLE_NAME=LanceDBClient.FINGERPRINT_TABLE):
        assert client._canonical_logical_tables() == builtin, "配成裸指纹表名同样不得并入"
        assert LanceDBClient._fingerprint_namespace_clash(LanceDBClient.FINGERPRINT_TABLE) is True, (
            "守卫的相等分支被删掉了 —— 它对 logical 集合没有影响, 但那条 logger.error 是运维唯一能看到的信号"
        )
    # 控制组: 正常配置名必须并进来
    with _config_env_override(LANCEDB_INDEX_TABLE_NAME="custom_nodes"):
        assert "custom_nodes" in client._canonical_logical_tables(), (
            "守卫写成了恒不并入 —— 配置出来的真实表名会在闸③/闸④ 里失明"
        )


def _indexable_rows(prefix: str, n: int = 2, *, canvas_file: str, dim: int = _DIM):
    """与 ``add_documents`` 落盘后**同列**的行 —— 供直接建表用。

    列集合必须与 ``add_documents`` 产出的 ``lance_doc`` 逐字一致, 否则后续
    ``table.add()`` 会因 schema 不符抛错, 本门就测不到"走的是 add 分支"。
    """
    from agentic_rag.clients.lancedb_client import _jieba_tokenize

    return [
        {
            "doc_id": f"{prefix}-{i}",
            "content": f"{prefix} content {i}",
            "content_tokenized": _jieba_tokenize(f"{prefix} content {i}"),
            "vector": [0.1 * (i + 1)] * dim,
            "canvas_file": canvas_file,
            "timestamp": f"2026-09-18T00:00:0{i}",
            "doc_type": "note",
        }
        for i in range(n)
    ]


def test_stats_add_count_see_beyond_default_page(tmp_path):
    """(e3) 三个默认分页站点的盲区已收口 —— 第 11+ 张表也看得见。

    ``table_names()`` 默认 ``limit=10``。改前 ``get_all_vault_stats`` / ``add_documents``
    的两处存在性判断 / ``count_documents_by_canvas`` 都走它:
      - stats 少算整页之外的表 (``GET /index/stats`` 的数字直接不对);
      - ``add_documents`` 把**已存在**的表判成不存在 ⇒ 走 create_table ⇒ 抛错 ⇒ 静默回 0
        (写入全丢, 调用方看到的是"加了 0 条");
      - ``count_documents_by_canvas`` 对页外的表恒答 0 条。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    for i in range(12):
        db.create_table(f"a{i:02d}_pad", data=[{"k": i}])
    target = "zz_canvas_nodes"
    canvas = "notes/z.md"
    db.create_table(target, data=_indexable_rows("ZZ", canvas_file=canvas))

    # 正向对照: 默认分页确实只给 10 张 (否则本门锁的是个不存在的问题)
    assert len(list(db.table_names())) == 10, "lancedb 默认分页行为变了, 本门需重新校准"
    assert len(_all_names(db)) == 13, "夹具没建成 13 张表"
    assert target not in set(db.table_names()), "前提失效: 目标表必须落在默认分页**之外**"

    client = _client(db_path, vault_id="zz")
    client._initialized = True  # 不让 count_documents_by_canvas 去 initialize() 加载 bge-m3

    stats = client.get_all_vault_stats()
    assert sum(v["tables"] for v in stats.values()) == 13, f"get_all_vault_stats 只看到默认分页的前 10 张: {stats!r}"
    assert stats.get("zz", {}).get("tables") == 1, f"页外那张表没进 stats: {stats!r}"

    counted = asyncio.run(client.count_documents_by_canvas(canvas, table_name=target))
    assert counted["count"] == 2, f"count_documents_by_canvas 对页外的表答了 0: {counted!r}"

    before_names = _all_names(db)
    added = asyncio.run(client.add_documents("canvas_nodes", _rows_for_add("ZZ2", canvas_file=canvas)))
    assert added == 2, "add_documents 把已存在的表判成不存在, 走了 create_table 并静默回 0"
    after_db = lancedb.connect(str(db_path))
    assert after_db.open_table(target).count_rows() == 4, (
        "新行没有落进已存在的那张表 —— 走 create 分支会对同名表抛错, 行数不会变成 4"
    )
    # ⚠️ 判据**不能**写成「表数不变」(初版如此): Codex r1 HIGH-1 整改后 (e1) 的钩子挂在
    # 两个分支之外, 于是这次 add 会顺带补建 zz 的指纹表 —— 表数从 13 变 14 是**预期**的。
    # 改断「新增集合恰好只有指纹表」: 它同时排除了「多建了一张内容表」。
    assert _all_names(after_db) - before_names == {f"zz_{LanceDBClient.FINGERPRINT_TABLE}"}, (
        f"本次写入新增的表不止 (e1) 的指纹表: {sorted(_all_names(after_db) - before_names)}"
    )


def _rows_for_add(prefix: str, *, canvas_file: str, n: int = 2, dim: int = _DIM):
    """喂给 ``add_documents`` 的入参 —— 不带 ``content_tokenized`` (由它自己补)。"""
    return [
        {
            "doc_id": f"{prefix}-{i}",
            "content": f"{prefix} content {i}",
            "vector": [0.1 * (i + 1)] * dim,
            "canvas_file": canvas_file,
            "timestamp": f"2026-09-18T01:00:0{i}",
            "doc_type": "note",
        }
        for i in range(n)
    ]


def test_add_documents_recreates_table_dropped_by_drift_guard(tmp_path):
    """漂移守卫把表 drop 掉之后, ``add_documents`` 必须走 **create** 分支把数据写进去。

    CARD-LANCE-INDEX-DELETE-CONTRACT 的自伤锁: 本卡把 ``add_documents`` 里两次
    ``table_names()`` 枚举合成一次 ``_all_table_names()`` 快照(为收口默认分页)。但两次枚举
    **之间**夹着 ``_check_and_fix_dimension_mismatch`` —— 它检测到 schema 漂移时会
    **把表 drop 掉**(docstring 原话: "True if the table was dropped (caller should create new)")。
    沿用漂移检查之前的快照 ⇒ 下面去 ``open_table`` 一张刚被删掉的表 ⇒ 异常被 ``add_documents``
    外层的 ``except`` 吞成**返回 0**, 调用方看到的是"添加了 0 条", 数据静默全丢。

    改前的实现是靠"第二次重新查一遍 ``table_names()``"歪打正着地躲开这一点; 合并枚举之后
    必须显式接住守卫的返回值。本门就锁这一点。

    ⚠️ 断言必须落在**行数**上: 只断"表还在"不够 —— 走 create 分支和走坏掉的 add 分支
    最后都可能留下一张同名表, 区别在于**数据有没有进去**。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    # 旧表: 16 维, 对 8 维的客户端来说是漂移 ⇒ 守卫会 drop 它
    db.create_table(f"{_SHORT_VAULT}_canvas_nodes", data=_rows("OLD", dim=_DRIFT_DIM))
    _assert_table_shape(db, f"{_SHORT_VAULT}_canvas_nodes", dim=_DRIFT_DIM, has_doc_type=True)

    client = _client(db_path, vault_id=_SHORT_VAULT, dim=_DIM)
    added = asyncio.run(client.add_documents("canvas_nodes", _rows("NEW", n=3, dim=_DIM)))

    assert added == 3, (
        "漂移表被守卫 drop 之后, add_documents 仍按旧快照走了 add 分支 —— open_table 一张"
        f"已删掉的表, 异常被吞成'添加了 0 条', 写入静默全丢。实得 {added}"
    )
    after = lancedb.connect(str(db_path))
    assert f"{_SHORT_VAULT}_canvas_nodes" in _all_names(after), "表没被重建出来"
    tbl = after.open_table(f"{_SHORT_VAULT}_canvas_nodes")
    assert tbl.count_rows() == 3, f"新数据没落盘: 实有 {tbl.count_rows()} 行"
    vectors = tbl.head(1).to_pydict().get("vector", [])
    assert vectors and len(vectors[0]) == _DIM, (
        f"重建出来的表维度不对: {len(vectors[0]) if vectors else '无行'}, 预期 {_DIM}"
    )


class _CreateFailsOn:
    """真库句柄 + 只在**指定表**上让 ``create_table`` 抛的薄包装（故障注入，非 mock）。"""

    def __init__(self, db, boom: str):
        self._db = db
        self._boom = boom

    def __getattr__(self, item):
        return getattr(self._db, item)

    def create_table(self, name, *args, **kwargs):
        if name == self._boom:
            raise RuntimeError(f"injected io failure while creating {name}")
        return self._db.create_table(name, *args, **kwargs)


def test_fingerprint_table_is_retried_on_later_writes_after_a_failed_creation(tmp_path):
    """**Codex r1 HIGH-1 锁**: 指纹表第一次建失败后, 后续写入必须**继续补建**。

    初版把 (e1) 的钩子只挂在 ``add_documents`` 的**建表分支**里。于是:
    第一次写 ⇒ 建内容表成功 + 建指纹表失败(只记日志不抛) ⇒ 之后每次追加都走 add 分支,
    **再也不会重试** ⇒ 那个 vault 在 ``_known_vault_ids`` 的三条来源里永久看不见 ⇒
    它的表被 id 更短的 vault 认领。这是「保护前提没建立起来, 却没有任何后续机会补救」。

    修法: 钩子挂到两个分支**之外**, 每次写入都补一次。已有时的代价是**一次全量表名枚举 +
    一次 ``open_table`` 读 schema**（Codex r2 HIGH-B 之后早退判据要与形态核同口径,
    所以不止枚举那一下；r3 LOW-1 点名此处说明滞后）。本门锁「失败之后还会不会补」这一点。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    fp = f"{_SHORT_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}"

    # 第一次写: 内容表建得成, 指纹表建失败
    client = _client(db_path, vault_id=_SHORT_VAULT)
    client._db = _CreateFailsOn(db, fp)
    assert asyncio.run(client.add_documents("canvas_nodes", _rows("A1"))) == 2, "内容写入不该被指纹表失败拖垮"
    assert fp not in _all_names(lancedb.connect(str(db_path))), (
        "前提失效: 指纹表竟然建出来了, 本门锁的就不是「建失败之后」那个场景"
    )

    # 第二次写: 走 add 分支(表已存在), 指纹表必须在这里被补上
    client2 = _client(db_path, vault_id=_SHORT_VAULT)
    assert asyncio.run(client2.add_documents("canvas_nodes", _rows("A2"))) == 2

    after = lancedb.connect(str(db_path))
    assert fp in _all_names(after), (
        "第一次建指纹表失败后就再也没补过 —— 该 vault 在 V 里永久看不见, "
        f"它的表会被 id 更短的 vault 认领; 现存 = {sorted(_all_names(after))}"
    )
    assert after.open_table(fp).count_rows() == 0, "补建出来的应是**空**指纹表"
    # 正向对照: 内容确实追加了两次 ⇒ 补指纹没有把写入路径搞坏
    assert after.open_table(f"{_SHORT_VAULT}_canvas_nodes").count_rows() == 4


def test_fingerprint_source_keeps_a_real_table_with_an_older_schema(tmp_path):
    """**Codex r1 HIGH-2 锁**: 列不齐的**真**指纹表不得被形态核排除（漏报方向 = 丢数据）。

    初版形态核的通过条件是「四列齐全 **且** 无 vector」。于是一张 schema 较旧、少一列
    (这里缺 ``chunk_count``) 的真指纹表会被判成"不是指纹表" ⇒ 它的 vault 从 V 里消失 ⇒
    表被 id 更短的 vault 认领 ⇒ **丢数据**。这正是本方法 docstring 自己写的
    「漏报方向才丢数据」, 初版实现自己踩了。

    现在唯一**确凿**的排除理由是「带 ``vector`` 列」(那是普通向量表)。列不齐只报不排。

    ⚠️ 排他断言同时保留: 带 vector 的那张仍必须被排除 —— 否则本门就退化成
    「形态核被整个拆掉」也能绿。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    # 旧 schema 的**真**指纹表: 缺 chunk_count, 但没有 vector 列
    legacy = [
        {"file_path": f"a_canvas/n{i}.md", "content_hash": f"{i:064x}", "last_indexed": "2026-01-01"} for i in range(2)
    ]
    db.create_table(f"a_canvas_{LanceDBClient.FINGERPRINT_TABLE}", data=legacy)
    # 对照: 名字像指纹表的**普通向量表**, 必须仍被排除
    forged = f"{_SHORT_VAULT}_custom_{LanceDBClient.FINGERPRINT_TABLE}"
    db.create_table(forged, data=_rows("FORGED"))

    cols = set(db.open_table(f"a_canvas_{LanceDBClient.FINGERPRINT_TABLE}").schema.names)
    assert "chunk_count" not in cols and "vector" not in cols, f"夹具形态不符: {sorted(cols)}"

    client = _client(db_path, vault_id=_SHORT_VAULT)
    derived = client._vault_ids_from_fingerprint_tables()

    assert "a_canvas" in derived, (
        "列不齐的**真**指纹表被形态核排除了 —— 它的 vault 从 V 里消失, "
        f"表会被 id 更短的 vault 认领(漏报方向 = 丢数据); 实得 {sorted(derived)}"
    )
    assert f"{_SHORT_VAULT}_custom" not in derived, (
        f"排他断言失败: 带 vector 的普通表仍被反推成伪 vault; 实得 {sorted(derived)}"
    )


def test_content_table_squatting_the_fingerprint_name_degrades_instead_of_losing_the_vault(tmp_path):
    """**Codex r2 HIGH-B 锁**: 指纹表名被一张带 vector 的内容表占着时, 必须降级而不是丢 vault。

    这条锁的是**本卡引入的回归**。两个判据不同口径 ⇒ 互相抵消:

    - ``_ensure_vault_fingerprint_table`` 的早退看**名字**(``_fingerprint_table_exists``);
    - ``_looks_like_fingerprint_table`` 的排除看 **schema**。

    vault ``a_canvas`` 若用逻辑名 ``file_fingerprints`` 写过内容, 库里就有一张**带 vector** 的
    ``a_canvas_file_fingerprints``: 补建钩子看到名字在、恒早退, 真指纹表永远建不出来; 形态核又把
    ``a_canvas`` 排除出 V。两件事叠加 = ``a_canvas`` 从 V 里消失, 而它的 ``a_canvas_nodes`` 还在
    ⇒ 短 vault ``a`` 的**启动自愈**把它当自己的规范内容表删掉。
    ⚠️ 改前的纯后缀反推会**保留** ``a_canvas`` —— 所以这层保护是本卡自己弄丢的。

    修法取 fail-closed: 形态核排除这张占名表时**同时置降级**, 于是 drop 走闸①整次拒绝、
    启动自愈整段跳过。本门的**承重**断言是「``a_canvas_nodes`` 仍在且行数不变」。
    """
    db_path = tmp_path / "db"
    lancedb.connect(str(db_path))

    root = tmp_path / "vaults-only-a"
    with _vaults_root_override(root, (_SHORT_VAULT,)):
        # a_canvas 走**生产写入方法**, 逻辑名就叫 file_fingerprints ⇒ 表名占住指纹命名空间
        ac = _client(db_path, vault_id="a_canvas", dim=_DRIFT_DIM)
        assert asyncio.run(ac.add_documents(LanceDBClient.FINGERPRINT_TABLE, _rows("SQUAT", dim=_DRIFT_DIM))) == 2
        assert asyncio.run(ac.add_documents("nodes", _rows("AC", dim=_DRIFT_DIM))) == 2

        squat = f"a_canvas_{LanceDBClient.FINGERPRINT_TABLE}"
        names = _all_names(lancedb.connect(str(db_path)))
        assert {squat, "a_canvas_nodes"} <= names, f"夹具形态不符: {sorted(names)}"
        assert "vector" in set(lancedb.connect(str(db_path)).open_table(squat).schema.names), (
            "前提失效: 占名的那张表没有 vector 列, 本门锁的就不是这个形态"
        )
        rows_before = lancedb.connect(str(db_path)).open_table("a_canvas_nodes").count_rows()

        client_a = _client(db_path, vault_id=_SHORT_VAULT)
        assert "a_canvas" not in client_a._discover_vault_ids_from_root(), (
            "前提失效: a_canvas 目录可发现, 那 V 本来就补得回来, 本门什么都没测"
        )
        client_a._known_vault_ids(force_refresh=True)
        assert client_a._vault_registry_degraded is True, (
            "形态核排除占名表时没有置降级 —— a_canvas 从 V 里消失而它的表还在, "
            "短 vault a 的自愈会把 a_canvas_nodes 当自己的规范内容表删掉"
        )

        report = client_a.drop_vault_tables_report(_SHORT_VAULT)
        assert report.refusal_kind == "registry_degraded", f"删索引应整次拒绝: {report!r}"
        assert report.dropped == ()

        # 承重: 启动维度自愈也不许碰 (a_canvas_nodes 是 16 维, 对 8 维的 a 是漂移表)
        asyncio.run(client_a._cache_tables())

    after_db = lancedb.connect(str(db_path))
    after = _all_names(after_db)
    assert "a_canvas_nodes" in after, (
        f"vault {_SHORT_VAULT} 的启动自愈删掉了 vault a_canvas 的表 a_canvas_nodes; 消失的表 = {sorted(names - after)}"
    )
    assert after_db.open_table("a_canvas_nodes").count_rows() == rows_before, "行数变了 —— 被当成漂移表重建过"
    assert squat in after, f"占名的那张表也被删了; 现存 = {sorted(after)}"


def test_rebuild_index_leaves_no_content_table_without_a_fingerprint_table(tmp_path):
    """**Codex r2 HIGH-A 锁**: 重建之后不得留下「有内容表、没有指纹表」的 vault。

    ``rebuild_index`` 先 ``drop_table(fp_table)`` 再 ``drop_table(table_name)``, 然后调
    ``index_vault_notes``。若该 vault 下**没有 Markdown**, 它一行都不写 ⇒ 不经
    ``_update_fingerprint`` ⇒ 指纹表不再存在; 而**别的逻辑名**的内容表(这里
    ``a_canvas_nodes``, 由 ``index_canvas`` 同型写入产生)压根不在本次删除范围里, 仍在库中。
    ⇒ 该 vault 变成 r7 那个形态, 而且是一条**正常生命周期路径**走出来的, 不需要故障注入。

    修法: ``rebuild_index`` 返回前无条件补一次。本门的承重断言是重建后指纹表**仍在**,
    且 ``a_canvas_nodes`` 经短 vault ``a`` 的 drop 与自愈之后**仍在、行数不变**。
    """
    db_path = tmp_path / "db"
    lancedb.connect(str(db_path))
    empty_vault_dir = tmp_path / "no-markdown-here"
    empty_vault_dir.mkdir()

    root = tmp_path / "vaults-only-a"
    with _vaults_root_override(root, (_SHORT_VAULT,)):
        ac = _client(db_path, vault_id="a_canvas", dim=_DRIFT_DIM)
        assert asyncio.run(ac.add_documents("nodes", _rows("AC", dim=_DRIFT_DIM))) == 2
        fp = f"a_canvas_{LanceDBClient.FINGERPRINT_TABLE}"
        assert fp in _all_names(lancedb.connect(str(db_path))), "前提失效: (e1) 没把指纹表建出来"
        rows_before = lancedb.connect(str(db_path)).open_table("a_canvas_nodes").count_rows()

        # 重建: vault 目录下没有任何 .md ⇒ index_vault_notes 一行都不写
        ac._initialized = True  # 不让 rebuild_index 去 initialize() 加载 bge-m3
        asyncio.run(ac.rebuild_index(vault_path=str(empty_vault_dir)))

        mid = _all_names(lancedb.connect(str(db_path)))
        assert "a_canvas_nodes" in mid, f"前提失效: 重建把 canvas 内容表也删了, 本门场景不成立: {sorted(mid)}"
        assert fp in mid, (
            "重建删掉指纹表后没有补回来 —— 这个 vault 变成「有内容表、没有指纹表」, "
            f"会被 id 更短的 vault 认领; 现存 = {sorted(mid)}"
        )

        # 承重: 短 vault a 的两条破坏性路径都不许碰 a_canvas_nodes
        client_a = _client(db_path, vault_id=_SHORT_VAULT)
        assert "a_canvas" in client_a._known_vault_ids(force_refresh=True), "补回来的指纹表没把 a_canvas 带回 V"
        client_a.drop_vault_tables_report(_SHORT_VAULT)
        asyncio.run(client_a._cache_tables())

    after_db = lancedb.connect(str(db_path))
    assert "a_canvas_nodes" in _all_names(after_db), (
        f"重建后的 a_canvas_nodes 被 vault {_SHORT_VAULT} 处理掉了; 现存 = {sorted(_all_names(after_db))}"
    )
    assert after_db.open_table("a_canvas_nodes").count_rows() == rows_before, "行数变了"


def test_rebuild_index_keeps_the_fingerprint_table_when_the_rebuild_itself_blows_up(tmp_path):
    """**Codex r3 HIGH 锁**: 重建**中途抛异常**时也不得留下「有内容表、没有指纹表」的 vault。

    r2 的修法只把补建放在**正常返回路径**上 —— Codex r3 指出它覆盖不到:

    - ``progress_callback`` 抛异常 / 任务被取消 ⇒ 直接越过补建;
    - 即便最终会补, 重建**期间**(向量化有 await 让出点)指纹表也是缺的, 另一个客户端
      此时跑 drop 或启动自愈就能认领这个 vault 的内容表。

    修法两件: ① 删掉旧指纹表后**立刻**补一张空的(窗口压到最小; 重建本就要清空指纹基线,
    空表正是它要的状态) ② 整个重建包 ``try/finally``, 退出路径再补一次。
    本门用 ``progress_callback`` 抛异常制造那条退出路径。
    """
    db_path = tmp_path / "db"
    lancedb.connect(str(db_path))
    vault_dir = tmp_path / "vault-with-one-md"
    vault_dir.mkdir()
    (vault_dir / "note.md").write_text("# hello\n\nsome content\n", encoding="utf-8")

    root = tmp_path / "vaults-only-a"
    with _vaults_root_override(root, (_SHORT_VAULT,)):
        ac = _client(db_path, vault_id="a_canvas", dim=_DRIFT_DIM)
        assert asyncio.run(ac.add_documents("nodes", _rows("AC", dim=_DRIFT_DIM))) == 2
        fp = f"a_canvas_{LanceDBClient.FINGERPRINT_TABLE}"
        assert fp in _all_names(lancedb.connect(str(db_path))), "前提失效: (e1) 没把指纹表建出来"
        rows_before = lancedb.connect(str(db_path)).open_table("a_canvas_nodes").count_rows()

        def _boom(*args, **kwargs):
            raise RuntimeError("injected failure from progress_callback")

        ac._initialized = True  # 不让 rebuild_index 去 initialize() 加载 bge-m3
        with pytest.raises(Exception) as exc:
            asyncio.run(ac.rebuild_index(vault_path=str(vault_dir), progress_callback=_boom))
        assert "injected failure" in str(exc.value) or isinstance(exc.value, RuntimeError), (
            f"前提失效: 抛出来的不是注入的那个异常, 本门没走到退出路径: {exc.value!r}"
        )

        mid = _all_names(lancedb.connect(str(db_path)))
        assert "a_canvas_nodes" in mid, f"前提失效: 重建把 canvas 内容表也删了: {sorted(mid)}"
        assert fp in mid, (
            "重建中途抛异常后指纹表没了 —— 这个 vault 变成「有内容表、没有指纹表」, "
            f"会被 id 更短的 vault 认领; 现存 = {sorted(mid)}"
        )

        # 承重: 短 vault a 的两条破坏性路径都不许碰 a_canvas_nodes
        client_a = _client(db_path, vault_id=_SHORT_VAULT)
        assert "a_canvas" in client_a._known_vault_ids(force_refresh=True), "指纹表没把 a_canvas 带回 V"
        client_a.drop_vault_tables_report(_SHORT_VAULT)
        asyncio.run(client_a._cache_tables())

    after_db = lancedb.connect(str(db_path))
    assert "a_canvas_nodes" in _all_names(after_db), (
        f"异常退出后的 a_canvas_nodes 被 vault {_SHORT_VAULT} 处理掉了; 现存 = {sorted(_all_names(after_db))}"
    )
    assert after_db.open_table("a_canvas_nodes").count_rows() == rows_before, "行数变了"


@pytest.mark.asyncio
async def test_ensure_fingerprint_refuses_a_name_owned_by_another_vault(tmp_path):
    """归属不是自己的指纹表名 ⇒ **不建也不认领**（独立对抗审查 2026-09-19 HIGH）。

    vault ``a`` 与 ``a_file`` 并存时, ``a`` 拼出的 ``a_file_fingerprints`` 按最长前缀
    归 ``a_file``（``_fingerprint_table_name`` 只 ``_warn_namespace_collision`` 后照样
    返回该名）。本卡的建表钩子若照建, 会**新造**两条改前不存在的破坏——改前这张表
    压根不会被建出来:

    ① ``DELETE /index/a`` 从 200 变**永久 409 collision**: 碰撞预检遍历 ``{a}_{逻辑名}``
       时这张 owner 非 ``a`` 的表现在"存在"了;
    ② ``DELETE /index/a_file`` 会把它删掉（``_owns_table`` 为真、模糊闸不拦）,
       即销毁 vault ``a`` 的指纹基线 —— 正是本钩子要防的那类数据丢失的镜像。

    ⛔ 本门期望"那张表**不存在**"。这类否定式判据必须配**控制组**: 一个不撞名的
    vault 的指纹表必须**建得出来**, 否则"钩子整个坏掉"也会让本门空洞地绿。
    """
    db_path = tmp_path / "db"
    root = tmp_path / "vaults"
    with _vaults_root_override(root, ["a", "a_file"]):
        ca = _client(db_path, vault_id="a")
        # 前提: 碰撞真的构造出来了 —— 否则下面在证别的东西
        assert ca._table_owner("a_file_fingerprints", "a") == "a_file", (
            f"前提不成立: a_file_fingerprints 归 {ca._table_owner('a_file_fingerprints', 'a')!r}, 期望 'a_file'"
        )
        await ca.add_documents("canvas_nodes", _rows("a", 2))

        # 控制组: vault a_file 自己的指纹名 a_file_file_fingerprints 归属就是它自己
        cb = _client(db_path, vault_id="a_file")
        assert cb._table_owner("a_file_file_fingerprints", "a_file") == "a_file"
        await cb.add_documents("canvas_nodes", _rows("af", 2))

    db = lancedb.connect(str(db_path))
    names = _all_names(db)

    assert "a_canvas_nodes" in names, f"被测侧内容写入就失败了, 本门在证别的东西: {sorted(names)}"
    assert "a_file_canvas_nodes" in names, f"控制组内容写入失败: {sorted(names)}"
    assert "a_file_file_fingerprints" in names, (
        f"控制组的指纹表没建出来 ⇒ 建表钩子本身坏了, 本门对归属闸无辨别力。现存 = {sorted(names)}"
    )
    assert "a_file_fingerprints" not in names, (
        "vault a 建出了归属 a_file 的指纹表 ⇒ a 的删索引永久 409 collision, "
        f"且 a_file 的删索引会销毁 a 的指纹基线。现存 = {sorted(names)}"
    )
