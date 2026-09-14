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
   集合 V 中使 ``t == v`` 或 ``t.startswith(v + "_")`` 成立的最长那个 v)。
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
    from app.config import get_settings

    root = tmp_path_factory.mktemp("vaults-root")
    for name in ("a", "a_b"):
        (root / name / ".obsidian").mkdir(parents=True)

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("VAULTS_ROOT", str(root))
        get_settings.cache_clear()
        # 前提: 接管真的生效了 —— 否则下面所有"互不相认"的断言都在证别的东西
        assert Path(get_settings().VAULTS_ROOT).resolve() == root.resolve(), (
            f"VAULTS_ROOT 接管失败: 实为 {get_settings().VAULTS_ROOT!r}"
        )
        yield root
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
_OVERLAP_SHAPES = [("page-inner", 0), ("page-outer", 10)]
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
    归属规则被改坏（退回朴素前缀 / 已知 vault 集合被打空）→ 本条与隔离门**一起** FAILED。
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
        "`t == v 或 t.startswith(v + '_')` 成立的**最长**那个 v。"
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
    """
    env = overlap_envs[(shape, "drop", table)]
    env["client"].drop_vault_tables(_SHORT_VAULT)
    after = _all_names(env["db"])
    assert table in after, (
        f"删 vault {_SHORT_VAULT} 的索引连带删掉了 vault {_LONG_VAULT} 的表 {table}："
        f"list_vault_tables({_SHORT_VAULT!r}) 把它算成了自己的; 形态={shape}; "
        f"消失的表 = {sorted(env['before'] - after)}"
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
