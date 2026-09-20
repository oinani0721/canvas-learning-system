"""``DELETE /api/v1/index/{vault_id}`` 五态契约行为门.

BATCH-2026-09-18-第十五批 / CARD-LANCE-INDEX-DELETE-CONTRACT.

锁的缺陷 (CARD-G2-9-F2 Codex r4-M3 / r5-M / r7-MEDIUM 三次点名): 改前端点只看
``drop_vault_tables`` 的 ``int`` 返回值, 而**四道整次拒绝闸**与"本来就没有表"和
"每一张都删失败"在返回值上全是 ``0`` —— 三件性质完全不同的事对调用方长得一样, 都回
``404 No tables found``。部分失败更糟: 回 ``200`` 且不带任何失败清单, 调用方据此认为
索引已清, 实际还留着几张。

本文件把端点的五态钉死 (各按 status_code **与**响应体逐字段断言, ⛔ 不用"非 404 即可"):

==========  ========================================  ==========================
outcome     语义                                      HTTP
==========  ========================================  ==========================
no_tables   本 vault 名下一张表都没有                 404 (detail 文案不变)
refused     四道闸之一整次拒绝                        409 + refusal_kind + 清单
all_failed  每一张都 drop 失败                        500 + tables_failed
partial     删成一部分                                207 + 失败清单 + partial
dropped     全删成                                    200 (体不变)
==========  ========================================  ==========================

⚠️ **DD-03 禁 mock**: 全部用例走 ``tmp_path`` 下的**真** LanceDB 库 + 真
``LanceDBClient`` + 真 ``drop_vault_tables_report``。``monkeypatch.setattr`` 换掉的只有
``index._get_lancedb_client`` —— 它返回的是上面那个**真客户端**, 这是依赖注入不是 mock。
唯一的注入点是 ``_DropFailsOn`` 让**指定表**的 ``drop_table`` 抛 (同款做法见
``test_lancedb_cross_vault_drop_g29f1.py::_DropFailsOn``): 真去造一张"删得动的表突然删
不动"在文件系统层面不可稳定复现, 而 207/500 两态锁的正是删失败怎么报, 没有失败就没有门。

⚠️ 本文件零 Neo4j（现网端口与测试容器端口一个都不连）、不碰任何现网目录; ``VAULTS_ROOT`` 只在用例内
MonkeyPatch 到 tmp 并 ``get_settings.cache_clear()`` 进出各一次 (范式取自
``test_lancedb_cross_vault_drop_g29f1.py::_vaults_root_override``)。

⚠️ 脱敏口径 (卡文 (d)): 响应体只许出现**表名 / refusal_kind / error_type**。异常原文
(闸② 的文案里带 ``{e}``, 可能含绝对路径) 与完整 refusal 文案只进服务端日志 ——
``test_409_and_500_bodies_carry_no_exception_text_or_paths`` 是这条的把守点。
"""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

lancedb = pytest.importorskip("lancedb")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

from agentic_rag.clients.lancedb_client import LanceDBClient  # noqa: E402

#: 本文件的向量维度 —— 与维度自愈无关, 只为让建表有个 vector 列。
_DIM = 8

#: 被测 vault。与 ``VAULTS_ROOT`` 下真建出来的目录同名 (走生产发现路径)。
_VAULT = "a"


def _rows(prefix: str, n: int = 2, *, dim: int = _DIM):
    """普通向量表的行。"""
    return [
        {
            "doc_id": f"{prefix}-{i}",
            "content": f"{prefix} content {i}",
            "vector": [0.1 * (i + 1)] * dim,
            "doc_type": "note",
        }
        for i in range(n)
    ]


def _fingerprint_rows(prefix: str, n: int = 2):
    """**真实**指纹 schema 的行 —— 与 ``LanceDBClient._update_fingerprint`` 同列同型。"""
    return [
        {
            "file_path": f"{prefix}/note-{i}.md",
            "content_hash": f"{i:064x}",
            "last_indexed": "2026-09-18T00:00:00",
            "chunk_count": i + 1,
        }
        for i in range(n)
    ]


def _all_names(db) -> set[str]:
    """读回全部表名 —— **显式**越过 ``table_names()`` 的 limit=10 默认分页。"""
    return set(db.table_names(limit=10_000))


def _client(db_path: Path, *, vault_id: str | None, dim: int = _DIM) -> LanceDBClient:
    """直连 tmp 库, **不调** ``initialize()`` (它会去加载 bge-m3)。"""
    client = LanceDBClient(db_path=str(db_path), embedding_dim=dim, vault_id=vault_id)
    client._db = lancedb.connect(str(db_path))
    return client


@contextlib.contextmanager
def _settings_env(**env: str):
    """把若干 env 接管掉并让 ``get_settings`` 的 lru_cache 进出各清一次。

    ⚠️ 用**独立**的 ``pytest.MonkeyPatch`` 实例 + 自己 ``undo()``, 不碰调用方的
    ``monkeypatch`` fixture —— 在共享实例上调 ``undo()`` 会把 fixture 自己布下的隔离
    一并撤掉。出的时候必须在 env **恢复之后**清缓存, 否则本次的取值会顺着缓存漏给同
    进程后跑的其它测试。
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


@contextlib.contextmanager
def _vaults_root(root: Path, names=(_VAULT,)):
    """在 ``root`` 下真建出 ``names`` 各自的 vault 目录并把 ``VAULTS_ROOT`` 指过去。

    候选规则由生产侧 ``_discover_vault_ids_from_root`` 决定 (非隐藏目录 + 含
    ``.obsidian/``), 这里**真的**把目录建出来而不是往客户端注入一份现成名单 ——
    注入式夹具只能证明"给了名单就能用", 证不到"名单拿得到"。
    """
    from app.config import get_settings

    for name in names:
        (root / name / ".obsidian").mkdir(parents=True, exist_ok=True)
    with _settings_env(VAULTS_ROOT=str(root)):
        assert Path(get_settings().VAULTS_ROOT).resolve() == root.resolve(), (
            f"VAULTS_ROOT 接管失败: 实为 {get_settings().VAULTS_ROOT!r}"
        )
        yield root


class _DropFailsOn:
    """真库句柄 + 只在**指定表**上让 ``drop_table`` 抛的薄包装 (故障注入, 非 mock)。

    ``boom`` 传 ``"*"`` 表示每一张都失败 (all_failed 态)。
    """

    #: 注入异常的文案 —— 断言"它不出现在响应体里"时用的锚。
    MESSAGE = "injected io failure while dropping"

    def __init__(self, db, boom):
        self._db = db
        self._boom = boom

    def __getattr__(self, item):
        return getattr(self._db, item)

    def drop_table(self, name, *args, **kwargs):
        if self._boom == "*" or name in self._boom:
            raise RuntimeError(f"{self.MESSAGE} {name} at {self._db.uri}")
        return self._db.drop_table(name, *args, **kwargs)


@contextlib.contextmanager
def _endpoint_with(client, monkeypatch, vault_id: str = _VAULT):
    """把端点的 LanceDB 取用点换成 ``client``, 并让 CARD-G2-2 的 409 一致性门放行。

    ``delete_vault_index`` 首行 ``resolve_vault_group_id(vault_id)``: 显式 vault 与进程
    active vault 不一致时 fail-closed 抛 409, 与本文件要测的删除契约无关 ——
    与 ``test_wave5_stageb_continued_vault_id_injection.py`` 逐字同法把 active 对齐。
    """
    from app.api.v1.endpoints import index as index_module

    monkeypatch.setattr(index_module, "_get_lancedb_client", lambda: client)
    with patch("app.config.get_current_vault_id", return_value=vault_id):
        yield index_module


async def _call_delete(vault_id: str = _VAULT):
    from app.api.v1.endpoints.index import delete_vault_index

    return await delete_vault_index(vault_id=vault_id)


# ═══════════════════════════════════════════════════════════════════════════
# 态① no_tables → 404 (文案一字不改)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_no_tables_404_detail_unchanged(tmp_path, monkeypatch):
    """名下一张表都没有 → 404, 且 detail 文案与改前**逐字**相同。

    这是本卡唯一保留 404 的分支: 改前 404 同时背着"拒绝 / 全失败 / 没有表"三种意思,
    改后它只剩"没有表"一种。文案不变是为了不打断已经在读这句话的调用方。
    """
    db_path = tmp_path / "db"
    lancedb.connect(str(db_path))  # 空库
    with _vaults_root(tmp_path / "vaults"):
        client = _client(db_path, vault_id=_VAULT)
        assert _all_names(client._db) == set(), "前提失效: 库里不该有表"
        with _endpoint_with(client, monkeypatch):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                await _call_delete()

    assert exc.value.status_code == 404, f"没有表必须是 404, 实为 {exc.value.status_code}"
    assert exc.value.detail == f"No tables found for vault_id '{_VAULT}'", f"404 文案被改动了: {exc.value.detail!r}"


# ═══════════════════════════════════════════════════════════════════════════
# 态② dropped → 200 (体一字不改)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_all_dropped_200_body_unchanged(tmp_path, monkeypatch):
    """全删成 → 200 且体仍是 ``{vault_id, tables_dropped}``。

    正向对照: 表**真的**从库里消失了 —— 只断状态码会让"回 200 但一张没删"照样绿。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))
    db.create_table(f"{_VAULT}_vault_notes", data=_rows("A-NOTES"))
    db.create_table(f"{_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("A"))
    db.create_table("b_canvas_nodes", data=_rows("B-NODES"))
    assert len(_all_names(db)) == 4, "夹具没建成 4 张表"

    with _vaults_root(tmp_path / "vaults", names=(_VAULT, "b")):
        client = _client(db_path, vault_id=_VAULT)
        with _endpoint_with(client, monkeypatch):
            result = await _call_delete()

    assert result == {"vault_id": _VAULT, "tables_dropped": 3}, f"200 体变了: {result!r}"
    after = _all_names(lancedb.connect(str(db_path)))
    assert after == {"b_canvas_nodes"}, f"该删的没删干净或删多了: 现存 {sorted(after)}"


# ═══════════════════════════════════════════════════════════════════════════
# 态③ partial → 207 + 失败清单
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_partial_failure_207_lists_failed_tables_with_error_type_only(tmp_path, monkeypatch):
    """部分失败 → 207 且体里逐表列出失败的表名 + 异常**类型名**。

    改前这里回 200 + 一个非零 ``tables_dropped``, 失败的表连名字都不露 —— 调用方拿不到
    任何"还剩哪几张"的线索。⛔ 体里只许有表名与 ``error_type``, 异常原文 (带库路径) 不许进。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))
    db.create_table(f"{_VAULT}_vault_notes", data=_rows("A-NOTES"))
    db.create_table(f"{_VAULT}_{LanceDBClient.FINGERPRINT_TABLE}", data=_fingerprint_rows("A"))
    boom = f"{_VAULT}_vault_notes"

    with _vaults_root(tmp_path / "vaults"):
        client = _client(db_path, vault_id=_VAULT)
        attempted = client.list_vault_tables(_VAULT)
        assert len(attempted) == 3 and boom in attempted, f"前提失效: 待删清单 = {sorted(attempted)}"
        client._db = _DropFailsOn(db, {boom})
        with _endpoint_with(client, monkeypatch):
            result = await _call_delete()

    from fastapi.responses import JSONResponse

    assert isinstance(result, JSONResponse), f"部分失败必须回 JSONResponse, 实为 {type(result)!r}"
    assert result.status_code == 207, f"部分失败必须是 207, 实为 {result.status_code}"
    body = json.loads(result.body)
    assert body["vault_id"] == _VAULT
    assert body["tables_dropped"] == 2, f"实删数应为 2: {body!r}"
    assert body["partial"] is True, f"207 体必须自称 partial: {body!r}"
    assert body["tables_failed"] == [{"table": boom, "error_type": "RuntimeError"}], (
        f"失败清单不对 (只许表名 + 异常类型名): {body['tables_failed']!r}"
    )
    after = _all_names(lancedb.connect(str(db_path)))
    assert after == {boom}, f"删失败的表该留下、其余该删掉: 现存 {sorted(after)}"


# ═══════════════════════════════════════════════════════════════════════════
# 态④ all_failed → 500
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_all_failed_500(tmp_path, monkeypatch):
    """每一张都删失败 → 500, ⛔ 不是 404。

    改前这条路径回 404 "No tables found" —— 表**全都在**却告诉调用方"没有表", 是本卡要
    拆掉的三合一 404 里最危险的一支 (调用方据此认为已清干净)。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))
    db.create_table(f"{_VAULT}_vault_notes", data=_rows("A-NOTES"))

    with _vaults_root(tmp_path / "vaults"):
        client = _client(db_path, vault_id=_VAULT)
        client._db = _DropFailsOn(db, "*")
        with _endpoint_with(client, monkeypatch):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                await _call_delete()

    assert exc.value.status_code == 500, f"全部删失败必须是 500, 实为 {exc.value.status_code}"
    detail = exc.value.detail
    assert detail["vault_id"] == _VAULT
    assert sorted(detail["tables_failed"], key=lambda r: r["table"]) == [
        {"table": f"{_VAULT}_canvas_nodes", "error_type": "RuntimeError"},
        {"table": f"{_VAULT}_vault_notes", "error_type": "RuntimeError"},
    ], f"失败清单不对: {detail['tables_failed']!r}"
    after = _all_names(lancedb.connect(str(db_path)))
    assert len(after) == 2, f"一张都没删成时表必须都还在: 现存 {sorted(after)}"


# ═══════════════════════════════════════════════════════════════════════════
# 态⑤ refused → 409 (两道闸各一条)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_registry_degraded_409_kind_not_404(tmp_path, monkeypatch):
    """闸① vault 清单降级 → 409 + ``refusal_kind == "registry_degraded"``, ⛔ 不是 404。

    ``VAULTS_ROOT`` 不是目录 ⇒ 归属判定退回朴素前缀 ⇒ 此刻删表可能连带删掉别的 vault
    的数据 ⇒ 整次拒绝。改前调用方看到的是 404 "没有表" —— 于是"系统为了保护别人主动
    没删"被伪装成"你本来就没东西可删", 而表一张没少。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))
    missing_root = tmp_path / "does-not-exist"
    assert not missing_root.exists(), "前提失效: 这个路径必须不存在"

    with _settings_env(VAULTS_ROOT=str(missing_root)):
        client = _client(db_path, vault_id=_VAULT)
        with _endpoint_with(client, monkeypatch):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                await _call_delete()

    assert exc.value.status_code == 409, f"清单降级必须是 409, 实为 {exc.value.status_code}"
    detail = exc.value.detail
    assert detail["refusal_kind"] == "registry_degraded", f"refusal_kind 不对: {detail!r}"
    assert detail["vault_id"] == _VAULT
    assert detail["ambiguous_tables"] == [], f"闸① 不该带模糊表清单: {detail!r}"
    after = _all_names(lancedb.connect(str(db_path)))
    assert after == {f"{_VAULT}_canvas_nodes"}, f"整次拒绝时一张都不许删: 现存 {sorted(after)}"


@pytest.mark.asyncio
async def test_ambiguous_409_exposes_ambiguous_tables(tmp_path, monkeypatch):
    """闸④ 模糊表名 → 409 且体里**列出**判不出主人的那几张表。

    ``a_x_y`` 的余名 ``x_y`` 还含下划线又不是任何逻辑名 ⇒ 更像某个未被发现的长 id vault
    (``a_x``) 的表 ⇒ 整次拒绝。清单必须回给调用方, 否则他只知道"删不了"却不知道删不了
    的是哪几张、该去查谁 (r5-M1: 本卡**只暴露不放宽**)。
    """
    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_x_y", data=_rows("AXY"))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))

    with _vaults_root(tmp_path / "vaults"):
        client = _client(db_path, vault_id=_VAULT)
        with _endpoint_with(client, monkeypatch):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                await _call_delete()

    assert exc.value.status_code == 409, f"模糊表名必须是 409, 实为 {exc.value.status_code}"
    detail = exc.value.detail
    assert detail["refusal_kind"] == "ambiguous", f"refusal_kind 不对: {detail!r}"
    assert detail["ambiguous_tables"] == [f"{_VAULT}_x_y"], f"模糊表清单不对: {detail!r}"
    after = _all_names(lancedb.connect(str(db_path)))
    assert len(after) == 2, f"整次拒绝时一张都不许删: 现存 {sorted(after)}"


class _ListTablesFails:
    """真库句柄 + 表名枚举恒抛 —— 闸② ``listing_failed`` 用 (故障注入, 非 mock)。"""

    MESSAGE = "injected io failure while listing tables"

    def __init__(self, db):
        self._db = db

    def __getattr__(self, item):
        return getattr(self._db, item)

    def list_tables(self, *args, **kwargs):
        raise RuntimeError(self.MESSAGE)

    def table_names(self, *args, **kwargs):
        raise RuntimeError(self.MESSAGE)


@pytest.mark.asyncio
async def test_listing_failed_409_distinct_from_registry_degraded(tmp_path, monkeypatch):
    """闸② 表名枚举失败 → 409 ``listing_failed``, 且与闸① 的 ``registry_degraded`` 分得开。

    为什么需要这条: ``refusal_kind`` 有四个取值, ``listing_failed`` 原本没有任何门。

    ⚠️ **主张已收窄** (Codex r1 MEDIUM-3 更正): 初版这条门叫
    "…_is_only_reachable_for_bare_scope", 声称 scoped vault 上打不到闸②。那是**过强**的 ——
    恒抛输入只证明了「枚举**持续**失败时闸① 抢先」。枚举**瞬时**失败(刷新 V 那次成功、
    碰撞预检那次才失败)照样能在 scoped vault 上走到闸②, 见下一条
    ``test_listing_failed_reachable_on_scoped_vault_with_a_transient_failure``。

    本门现在只主张: **恒抛**输入下, 裸表口径落 ``listing_failed``、scoped 落
    ``registry_degraded``, 两者**分得开**。⛔ 不是"两个都是 409 就算过" ——
    那样把闸序换掉本门也照样绿。
    """
    from fastapi import HTTPException

    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table("vault_notes", data=_rows("BARE"))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))

    with _vaults_root(tmp_path / "vaults"):
        bare = _client(db_path, vault_id="default")
        assert bare.active_vault_id in ("", "default"), f"夹具没构成裸表口径: active_vault_id={bare.active_vault_id!r}"
        bare._db = _ListTablesFails(db)
        with _endpoint_with(bare, monkeypatch, vault_id="default"):
            with pytest.raises(HTTPException) as exc_bare:
                await _call_delete("default")

        scoped = _client(db_path, vault_id=_VAULT)
        scoped._db = _ListTablesFails(db)
        with _endpoint_with(scoped, monkeypatch):
            with pytest.raises(HTTPException) as exc_scoped:
                await _call_delete()

    assert exc_bare.value.status_code == 409, f"枚举失败必须是 409, 实为 {exc_bare.value.status_code}"
    assert exc_bare.value.detail["refusal_kind"] == "listing_failed", (
        f"裸表口径下应由闸② 拒绝: {exc_bare.value.detail!r}"
    )
    assert exc_bare.value.detail["ambiguous_tables"] == []
    blob = json.dumps(exc_bare.value.detail, ensure_ascii=False)
    assert _ListTablesFails.MESSAGE not in blob and str(tmp_path) not in blob, (
        f"闸② 的文案里嵌着异常原文(可能带库路径), 不得进响应体: {blob}"
    )

    assert exc_scoped.value.status_code == 409
    assert exc_scoped.value.detail["refusal_kind"] == "registry_degraded", (
        f"scoped 侧同一注入应先被闸① 拦下 (枚举失败也让 V 降级): {exc_scoped.value.detail!r}"
    )

    after = _all_names(lancedb.connect(str(db_path)))
    assert after == {"vault_notes", f"{_VAULT}_canvas_nodes"}, f"整次拒绝时一张都不许删: 现存 {sorted(after)}"


class _ListTablesFailsAfter:
    """真库句柄 + 表名枚举**第 N 次起**才抛 —— 瞬时故障（故障注入，非 mock）。

    闸② 在 scoped vault 上的可达面需要这个形态: 刷新 V 那几次枚举成功(所以不置降级、
    闸① 放行), 碰撞预检那次才失败。恒抛的包装做不到这一点 —— 它会先把 V 打降级。
    """

    MESSAGE = "injected transient io failure while listing tables"

    def __init__(self, db, ok_calls: int):
        self._db = db
        self._left = ok_calls
        self.calls = 0

    def __getattr__(self, item):
        return getattr(self._db, item)

    def _tick(self):
        self.calls += 1
        if self._left > 0:
            self._left -= 1
            return True
        return False

    def list_tables(self, *args, **kwargs):
        if self._tick():
            return self._db.list_tables(*args, **kwargs)
        raise RuntimeError(self.MESSAGE)

    def table_names(self, *args, **kwargs):
        if self._tick():
            return self._db.table_names(*args, **kwargs)
        raise RuntimeError(self.MESSAGE)


@pytest.mark.asyncio
async def test_listing_failed_reachable_on_scoped_vault_with_a_transient_failure(tmp_path, monkeypatch):
    """闸② 在 **scoped** vault 上也可达 —— 只要枚举是**瞬时**失败而不是持续失败。

    Codex r1 MEDIUM-3: 上一条门用恒抛包装, 只能证明「持续故障时闸① 抢先」, 证明不了
    「``listing_failed`` 只在裸表口径可达」。本门给出那个**未被上一条门覆盖的输入**:
    枚举前几次成功(刷新 V 不降级 ⇒ 闸① 放行), 碰撞预检那次才抛 ⇒ 落到闸②。

    ⚠️ 前提断言把「闸① 确实放行了」钉住(``_vault_registry_degraded is False``) ——
    没有它, 本门对「refusal_kind 是哪一个」的断言就可能是闸① 顺手给的。
    """
    from fastapi import HTTPException

    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))

    with _vaults_root(tmp_path / "vaults"):
        client = _client(db_path, vault_id=_VAULT)
        # 先量一次「刷新 V 要几次枚举」—— 写死次数会随实现漂移(Codex r1 的同族教训)
        counter = _ListTablesFailsAfter(db, ok_calls=10_000)
        client._db = counter
        client._known_vault_ids(force_refresh=True)
        v_refresh_calls = counter.calls
        assert v_refresh_calls >= 1, "前提失效: 刷新 V 一次枚举都没做, 本门的注入点无从对齐"

        # 正式跑: 让刷新 V 的那几次成功, 之后(碰撞预检)第一次枚举就抛
        client2 = _client(db_path, vault_id=_VAULT)
        client2._db = _ListTablesFailsAfter(db, ok_calls=v_refresh_calls)
        with _endpoint_with(client2, monkeypatch):
            with pytest.raises(HTTPException) as exc:
                await _call_delete()

        assert client2._vault_registry_degraded is False, "前提失效: V 还是被打成降级了 ⇒ 这一跑落的是闸①, 不是闸②"

    assert exc.value.status_code == 409
    assert exc.value.detail["refusal_kind"] == "listing_failed", (
        f"scoped vault 上的瞬时枚举失败应落闸②: {exc.value.detail!r}"
    )
    blob = json.dumps(exc.value.detail, ensure_ascii=False)
    assert _ListTablesFailsAfter.MESSAGE not in blob and str(tmp_path) not in blob, (
        f"闸② 的文案里嵌着异常原文, 不得进响应体: {blob}"
    )
    assert _all_names(lancedb.connect(str(db_path))) == {f"{_VAULT}_canvas_nodes"}, "整次拒绝时一张都不许删"


# ═══════════════════════════════════════════════════════════════════════════
# 脱敏 —— 响应体只许有表名 / refusal_kind / error_type
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_409_and_500_bodies_carry_no_exception_text_or_paths(tmp_path, monkeypatch):
    """409 与 500 的体里不得出现异常原文、完整 refusal 文案或任何库路径。

    闸② 的 refusal 文案里嵌着 ``{e}``, 而 LanceDB 的异常常带库的**绝对路径**; 注入的
    RuntimeError 同理。把它们照搬进响应体 = 把服务器磁盘布局回给调用方。原文只进
    ``logger``, 体里只留表名 / ``refusal_kind`` / ``error_type``。
    """
    from fastapi import HTTPException

    db_path = tmp_path / "db"
    db = lancedb.connect(str(db_path))
    db.create_table(f"{_VAULT}_canvas_nodes", data=_rows("A-NODES"))

    # 409 侧 (闸①)
    with _settings_env(VAULTS_ROOT=str(tmp_path / "nope")):
        client = _client(db_path, vault_id=_VAULT)
        with _endpoint_with(client, monkeypatch):
            with pytest.raises(HTTPException) as exc409:
                await _call_delete()

    # 500 侧 (注入异常原文里带 db uri)
    with _vaults_root(tmp_path / "vaults"):
        client2 = _client(db_path, vault_id=_VAULT)
        client2._db = _DropFailsOn(db, "*")
        with _endpoint_with(client2, monkeypatch):
            with pytest.raises(HTTPException) as exc500:
                await _call_delete()

    # 207 侧 (部分失败; Codex r1 MEDIUM-5: 初版脱敏门只查 409/500, 把 207 整条漏在外面)
    db.create_table(f"{_VAULT}_vault_notes", data=_rows("A-NOTES"))
    with _vaults_root(tmp_path / "vaults"):
        client3 = _client(db_path, vault_id=_VAULT)
        client3._db = _DropFailsOn(db, {f"{_VAULT}_vault_notes"})
        with _endpoint_with(client3, monkeypatch):
            result207 = await _call_delete()
    from fastapi.responses import JSONResponse

    assert isinstance(result207, JSONResponse) and result207.status_code == 207, (
        f"前提失效: 没有构成部分失败态, 207 这一格什么都没测: {result207!r}"
    )

    class _Body:
        """把 207 的 body 包成与 HTTPException 同形, 好走同一套脱敏断言。"""

        def __init__(self, raw):
            self.detail = json.loads(raw)

    class _Exc:
        def __init__(self, v):
            self.value = v

    for label, exc in (("409", exc409), ("500", exc500), ("207", _Exc(_Body(result207.body)))):
        blob = json.dumps(exc.value.detail, ensure_ascii=False)
        assert str(tmp_path) not in blob, f"{label} 体里泄漏了库路径: {blob}"
        assert _DropFailsOn.MESSAGE not in blob, f"{label} 体里泄漏了异常原文: {blob}"
        assert "整次拒绝" not in blob, f"{label} 体里泄漏了完整 refusal 文案: {blob}"
        assert "Traceback" not in blob, f"{label} 体里出现了 Traceback: {blob}"

    # 正向对照: 结构化字段**确实**在 —— 否则"什么都没有"也能让上面四条全绿
    assert exc409.value.detail["refusal_kind"] == "registry_degraded"
    assert exc500.value.detail["tables_failed"][0]["error_type"] == "RuntimeError"
    assert json.loads(result207.body)["tables_failed"][0]["error_type"] == "RuntimeError"


# ═══════════════════════════════════════════════════════════════════════════
# openapi 声明面
# ═══════════════════════════════════════════════════════════════════════════


def test_openapi_declares_409_207_500():
    """端点装饰器必须把 409 / 207 / 500 声明进 openapi。

    ⛔ 只挂 ``index_router`` 自己建一个 ``FastAPI()``, **不** import ``app.main``
    (它会拉起整条 lifespan)。router include 级的 404/503 由 ``api/v1/router.py`` 声明,
    本卡零改动, 所以这里只断新增的三个。
    """
    from fastapi import FastAPI

    from app.api.v1.endpoints.index import index_router

    app = FastAPI()
    app.include_router(index_router, prefix="/index")
    responses = app.openapi()["paths"]["/index/{vault_id}"]["delete"]["responses"]

    for code in ("409", "207", "500"):
        assert code in responses, f"openapi 里没有声明 {code}: 实有 {sorted(responses)}"
    assert "200" in responses, f"200 不该被挤掉: 实有 {sorted(responses)}"
