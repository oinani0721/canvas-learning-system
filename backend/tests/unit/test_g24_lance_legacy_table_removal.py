"""CARD-G2-4 行为门 — 真 LanceDB 临时库, 不 mock 存储层。

场景 (卡文钉死): ``{vault}_vault_notes`` **缺失** + 裸 ``vault_notes`` **存在且
含异 vault 的行**。删除 B0.7 回退前, 这个场景下 vault X 的读写都会落到裸表 ——
读到别人的笔记, 写把自己的数据混进别人的表。本文件锁死删除后的行为:

- 读: 抛 ``TableMissingError``, 且**从未打开**裸表 (不是"结果里碰巧没有");
- 上层: ``search_supplementary`` 透出 ``degraded=True`` + ``status=unavailable``
  + 非空 reason (带缺失表名);
- 写: 建 ``{vault}_vault_notes`` 新表, 裸表**逐行不变**;
- 单 vault 部署 (vault_id 为 ``default``/空): 裸表仍是它的正常命名空间 —
  这条正向对照防"为了隔离把单 vault 部署炸掉"。

⚠️ 门设计说明 (防死门): 每条"不应发生"的断言都配了一条"确实会发生"的正向
对照 —— 裸表真的有行、default vault 真的能读到它、写真的落了盘。否则
「search 没返回裸表的行」在一个空库上恒真, 门等于没有。
"""

from __future__ import annotations

import asyncio
import hashlib
import json

import pytest

lancedb = pytest.importorskip("lancedb")

from agentic_rag.clients.lancedb_client import (  # noqa: E402
    LanceDBClient,
    TableMissingError,
)

_DIM = 4
_OTHER_VAULT_ROWS = [
    {
        "doc_id": f"other-{i}",
        "content": f"OTHER VAULT 私有内容 {i}",
        "content_tokenized": f"OTHER VAULT 私有内容 {i}",
        "vector": [0.1 * (i + 1)] * _DIM,
        "canvas_file": f"OTHER_VAULT/secret-{i}.md",
        "timestamp": "2026-08-31T00:00:00",
        # ⚠️ doc_type 必须种进 fixture: 缺列会命中 RAG-P0 A5 的 schema-drift
        # 自动 drop+recreate (_check_and_fix_dimension_mismatch), 那是另一条
        # 既有行为, 混进来会让"裸表被改动"的归因失真 (首跑实测踩到)。
        "doc_type": "note",
    }
    for i in range(3)
]


def _rows_fingerprint(tbl) -> str:
    """裸表内容指纹 — 用于证明写路径「一个字节都没碰它」。"""
    rows = tbl.to_pandas().to_dict(orient="records")
    payload = json.dumps(
        [{k: str(v) for k, v in sorted(r.items())} for r in rows],
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@pytest.fixture
def legacy_db(tmp_path):
    """临时库: 只有裸 ``vault_notes`` (含异 vault 行), 无任何 prefixed 表。"""
    path = tmp_path / "lancedb"
    db = lancedb.connect(str(path))
    db.create_table("vault_notes", data=list(_OTHER_VAULT_ROWS))
    assert set(db.table_names()) == {"vault_notes"}
    return str(path)


def _client(db_path: str, vault_id: str) -> LanceDBClient:
    """构造 client 并直接接管 ``_db`` — 绕开 embedding 权重加载。

    ⛔ 这个测试缝只跳过模型初始化, **不** 替换任何被测逻辑:
    resolve_table_name / _is_table_absent / search / add_documents 全是生产实现。
    """
    client = LanceDBClient(db_path=db_path, embedding_dim=_DIM, vault_id=vault_id)
    client._db = lancedb.connect(db_path)
    client._initialized = True
    return client


# ═══════════════════════════════════════════════════════════════════════════════
# 正向对照 — 证明 fixture 里的裸表真的有货、真的可达
# ═══════════════════════════════════════════════════════════════════════════════


def test_bare_table_really_holds_other_vault_rows(legacy_db):
    """对照 1: 裸表确实有 3 行异 vault 数据 (否则后面的"不返回"恒真)。"""
    db = lancedb.connect(legacy_db)
    tbl = db.open_table("vault_notes")
    assert tbl.count_rows() == 3
    paths = {r["canvas_file"] for r in tbl.to_pandas().to_dict(orient="records")}
    assert paths == {f"OTHER_VAULT/secret-{i}.md" for i in range(3)}


def test_default_vault_still_maps_to_bare_table(legacy_db):
    """对照 2 (⛔ 保留的窄映射): 单 vault 部署 (``default`` / 空) 的表就是裸表。

    卡文明示: 误删这条映射会炸单 vault 部署。判据同
    ``test_lancedb_vault_isolation.py:23/:35``, 这里再从"真库能读到"这一侧钉一遍。
    """
    for vid in ("default", ""):
        client = _client(legacy_db, vid)
        assert client.resolve_table_name("vault_notes") == "vault_notes"
        assert client._db.open_table(client.resolve_table_name("vault_notes")).count_rows() == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 读侧 — B0.7 回退删除
# ═══════════════════════════════════════════════════════════════════════════════


def test_prefixed_missing_no_longer_falls_back_to_bare(legacy_db):
    """B0.7 删除锁: prefixed 不存在 + 裸表存在 → 仍返回 prefixed 名。

    删除前该条件正是回退触发条件, 会返回 ``"vault_notes"``。
    """
    client = _client(legacy_db, "xvault")
    assert "xvault_vault_notes" not in client._db.table_names()
    assert "vault_notes" in client._db.table_names()
    assert client.resolve_table_name("vault_notes") == "xvault_vault_notes"


def test_search_raises_table_missing_and_never_opens_bare_table(legacy_db):
    """读侧 fail-closed: 抛 TableMissingError, 且裸表**从未被打开**。

    "从未打开"比"结果里没有裸表的行"强 —— 后者在异常路径上恒真, 证明不了
    没有绕道读过。
    """
    client = _client(legacy_db, "xvault")
    opened: list[str] = []
    real_open = client._db.open_table

    def spy_open(name, *a, **kw):
        opened.append(name)
        return real_open(name, *a, **kw)

    client._db.open_table = spy_open  # type: ignore[method-assign]

    with pytest.raises(TableMissingError) as excinfo:
        asyncio.run(client.search(query="私有内容", table_name="vault_notes", num_results=5))

    assert excinfo.value.table_name == "xvault_vault_notes"
    assert "vault_notes" not in opened, f"裸表被打开了: {opened}"
    assert opened == ["xvault_vault_notes"], f"只应尝试 prefixed 表, 实际 {opened}"


def test_table_missing_penetrates_enable_fallback_swallow_gate(legacy_db):
    """``enable_fallback=True`` (默认) 也必须让表缺失穿透 — 这是本卡的核心。

    反向对照在同一条 search 上: 别的异常仍被吞成 [] (契约不变)。
    """
    client = _client(legacy_db, "xvault")
    assert client.enable_fallback is True
    with pytest.raises(TableMissingError):
        asyncio.run(client.search(query="q", table_name="vault_notes", num_results=3))

    # 反向对照: 表**存在**但查询本身炸了 → 旧契约不变, 吞成 []
    boom = _client(legacy_db, "default")

    def exploding_open(name, *a, **kw):
        raise RuntimeError("table is there but the read blew up")

    boom._db.open_table = exploding_open  # type: ignore[method-assign]
    assert asyncio.run(boom.search(query="q", table_name="vault_notes", num_results=3)) == []


def test_search_supplementary_surfaces_unavailable(legacy_db):
    """上层透出: degraded=True + status=unavailable + 非空 reason(含表名)。"""
    from app.services import supplementary_search_service as svc

    client = _client(legacy_db, "xvault")
    result = asyncio.run(svc.search_supplementary(query="私有内容", lancedb_client=client))

    assert result["materials"] == []
    assert result["degraded"] is True
    assert result["status"] == "unavailable"
    assert result["reason"] and "xvault_vault_notes" in result["reason"]


# ═══════════════════════════════════════════════════════════════════════════════
# 写侧 — 拒落裸表
# ═══════════════════════════════════════════════════════════════════════════════


def test_write_creates_prefixed_table_and_leaves_bare_byte_identical(legacy_db):
    """写侧同场景: 建 prefixed 新表, 裸表**逐行指纹不变**。

    删除 B0.7 前, 同一次 add_documents 会因"prefixed 不存在、裸表存在"落进
    裸表 —— 新 vault 的数据混进别人的表, 且无任何日志区分。
    """
    client = _client(legacy_db, "xvault")
    before = _rows_fingerprint(client._db.open_table("vault_notes"))

    n = asyncio.run(
        client.add_documents(
            "vault_notes",
            [
                {
                    "doc_id": "x-1",
                    "content": "XVAULT 自己的内容",
                    "vector": [0.9] * _DIM,
                    "canvas_file": "XVAULT/mine.md",
                    "doc_type": "note",
                }
            ],
        )
    )
    assert n == 1, "写入本身必须成功 (否则下面的'裸表没变'是因为压根没写)"

    db = lancedb.connect(legacy_db)
    assert "xvault_vault_notes" in db.table_names(), "新 vault 的数据必须落进自己的表"
    assert db.open_table("xvault_vault_notes").count_rows() == 1

    after_tbl = db.open_table("vault_notes")
    assert after_tbl.count_rows() == 3
    assert _rows_fingerprint(after_tbl) == before, "裸表内容必须逐行不变"


def test_default_vault_write_still_targets_bare_table(tmp_path):
    """对照 3: 单 vault 部署的写仍落裸表 — 隔离不得以炸单 vault 为代价。"""
    path = str(tmp_path / "lancedb-default")
    db = lancedb.connect(path)
    db.create_table("vault_notes", data=list(_OTHER_VAULT_ROWS))

    client = _client(path, "default")
    n = asyncio.run(
        client.add_documents(
            "vault_notes",
            [
                {
                    "doc_id": "d-1",
                    "content": "单 vault 部署写入",
                    "vector": [0.5] * _DIM,
                    "canvas_file": "notes/d.md",
                    "doc_type": "note",
                }
            ],
        )
    )
    assert n == 1
    db2 = lancedb.connect(path)
    assert db2.table_names() == ["vault_notes"], "default vault 不得凭空造 prefixed 表"
    assert db2.open_table("vault_notes").count_rows() == 4


# ═══════════════════════════════════════════════════════════════════════════════
# _is_table_absent 分流 — 不得把"打不开"误判成"不存在"
# ═══════════════════════════════════════════════════════════════════════════════


def test_is_table_absent_distinguishes_missing_from_unopenable(legacy_db):
    client = _client(legacy_db, "xvault")
    assert client._is_table_absent("xvault_vault_notes") is True
    assert client._is_table_absent("vault_notes") is False

    # 列举本身失败 → fail-safe 判 False (走旧 RuntimeError 契约, 不误报缺失)
    def exploding_list(*a, **kw):
        raise RuntimeError("catalog unavailable")

    client._db.list_tables = exploding_list  # type: ignore[method-assign]
    assert client._is_table_absent("whatever") is False


def test_is_table_absent_sees_past_default_pagination(tmp_path):
    """⛔ Codex round-1 MEDIUM-1 回归锁: 目录超过 10 张表也必须看得见。

    lancedb 0.30.2 的 ``DBConnection.table_names(page_token=None, limit=10)``
    **默认只返回前 10 张**。若 ``_is_table_absent`` 走它, 第 11 张之后的表会被
    判成"不存在", 一个明明在的表就被本卡的 fail-closed 通道当成缺表抛出去 ——
    比它要修的 fail-open 更糟 (功能直接不可用)。

    本条的失败方向: 把实现换回 ``table_names()`` 无参调用, 立刻变红。
    """
    path = str(tmp_path / "manytables")
    db = lancedb.connect(path)
    for i in range(12):
        db.create_table(f"a{i:02d}_pad", data=[{"k": i}])
    db.create_table("zz_vault_notes", data=list(_OTHER_VAULT_ROWS))

    # 正向对照: 证明默认分页确实只给 10 张 (否则本测试锁的是个不存在的问题)
    assert len(list(db.table_names())) == 10, "lancedb 默认分页行为变了, 本锁需重新校准"

    client = _client(path, "zz")
    assert len(client._all_table_names()) == 13
    assert client._is_table_absent("zz_vault_notes") is False, "第 11+ 张表不得被误判成不存在"
    assert client._is_table_absent("zz_not_there") is True
