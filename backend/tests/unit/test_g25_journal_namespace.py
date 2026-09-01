"""CARD-G2-5 行为门 — 索引 journal 的 vault 命名空间 (BATCH-2026-08-29-第七批).

被修的事故形态 (计划书 L115): 两处 durable pending journal 写在固定文件名上,
条目只有相对路径、无 vault 维度。于是 vault A 攒下的 pending 会在切到 vault B
之后被 ``recover()`` 当成 B 的文件重放 —— 把 A 的路径索引进 B, 或按 A 的删除
意图去删 B 的索引行。

本文件锁死:

1. 两个 vault 的 journal **文件名不同**且各自带 key;
2. A 写下 pending (含 **delete 意图**) → 以 B 重建 → ``recover()==0`` 且
   **A 的文件逐字节没被碰过**; 切回 A → ``recover()==N`` 且 delete 意图仍在;
3. ``lancedb_index_service`` 同型;
4. G2-5 之前的**无维度**旧 journal 被改名隔离 (``.pre-g25.bak``) 且**不加载**,
   内容逐字节保留;
5. key 只跟**部署期** ``settings.vault_id`` 走 —— 注入 per-request ContextVar
   不得让它漂移。

⚠️ 隔离纪律: 生产路径落在真实的 ``backend/app/data/``。测试只把**目录**换成
tmp_path, **文件名照用生产代码算出来的那个** —— 命名空间契约仍由被测代码产出,
但不污染真实数据目录。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import pytest


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _switch_vault(vault_root: Path, vault_name: str):
    """把部署期身份切到某个 vault (无 .canvas-config.yaml → 走 ACTIVE_VAULT)。"""
    from app.config import reload_settings

    vault_root.mkdir(parents=True, exist_ok=True)
    return reload_settings(overrides={"CANVAS_BASE_PATH": str(vault_root), "ACTIVE_VAULT": vault_name})


@pytest.fixture
def restore_settings():
    from app.config import get_settings, reload_settings

    original = {
        "CANVAS_BASE_PATH": get_settings().CANVAS_BASE_PATH,
        "ACTIVE_VAULT": get_settings().ACTIVE_VAULT,
    }
    yield
    reload_settings(overrides=original)


def _assert_production_state_dir(obj, module) -> None:
    """⛔ Codex round-1 LOW-11: 只锁 basename 会让"生产目录算错"也照样绿。

    在把 journal 搬进 tmp 之前, 先断言**未注入**时它确实落在生产的
    ``backend/app/data``。这样测试同时锁住了目录与文件名两半。
    """
    expected = Path(module.__file__).resolve().parent.parent / "data"
    assert obj._pending_file.parent == expected, f"生产 journal 目录不再是 {expected}, 实际 {obj._pending_file.parent}"


def _orchestrator(vault_root: Path, vault_name: str, journal_dir: Path):
    from app.services import vault_index_orchestrator as mod
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    _switch_vault(vault_root, vault_name)
    _assert_production_state_dir(VaultIndexOrchestrator(vault_path=str(vault_root)), mod)
    journal_dir.mkdir(parents=True, exist_ok=True)
    # 显式注入 state_dir —— 文件名仍由生产代码算, legacy 路径由它自己派生
    return VaultIndexOrchestrator(vault_path=str(vault_root), state_dir=str(journal_dir))


def _index_service(vault_root: Path, vault_name: str, journal_dir: Path):
    from app.services import lancedb_index_service as mod
    from app.services.lancedb_index_service import LanceDBIndexService

    _switch_vault(vault_root, vault_name)
    _assert_production_state_dir(LanceDBIndexService(), mod)
    journal_dir.mkdir(parents=True, exist_ok=True)
    return LanceDBIndexService(state_dir=str(journal_dir))


# ═══════════════════════════════════════════════════════════════════════════════
# 1) 命名空间本身
# ═══════════════════════════════════════════════════════════════════════════════


def test_journal_filenames_carry_vault_key(tmp_path, restore_settings):
    a = _orchestrator(tmp_path / "va", "Vault A", tmp_path / "ja")
    b = _orchestrator(tmp_path / "vb", "Vault B", tmp_path / "jb")

    assert a._pending_file.name != b._pending_file.name
    assert "vault_a" in a._pending_file.name and a._pending_file.name.endswith(".jsonl")
    assert "vault_b" in b._pending_file.name
    # 旧的无维度名仍被记住 (供隔离), 但不是工作文件
    assert a._legacy_pending_file.name == "vault_index_pending.jsonl"
    assert a._pending_file.name != a._legacy_pending_file.name


def test_deployment_key_ignores_request_contextvar(tmp_path, restore_settings):
    """⛔ key 只跟部署期身份走。

    journal 是**进程级**资源, worker 循环在请求边界之外读写它。若 key 取
    per-request ContextVar, 同一个文件名会随请求漂移 —— 那不是隔离, 是随机分桶。
    """
    from app.core.subject_config import set_current_subject_id
    from app.core.vault_state_paths import deployment_vault_key

    _switch_vault(tmp_path / "vdep", "Deploy Vault")
    baseline = deployment_vault_key()
    assert baseline == "deploy_vault"

    # ⛔ Codex round-1 MEDIUM-6: 只测 helper 是死门 —— 把两个服务改成读
    # ContextVar, 旧写法照样全绿。所以必须在 hostile ContextVar **存续期间**
    # 真正构造这两个服务, 断言它们算出来的文件名。
    set_current_subject_id("vault:some_other_vault")
    try:
        assert deployment_vault_key() == baseline, "ContextVar 不得影响 journal 命名空间"

        orch = _orchestrator(tmp_path / "vdep", "Deploy Vault", tmp_path / "j1")
        svc = _index_service(tmp_path / "vdep", "Deploy Vault", tmp_path / "j2")
        for f in (orch._pending_file, svc._pending_file):
            assert baseline in f.name, f"{f.name} 应带部署期 key {baseline}"
            assert "some_other_vault" not in f.name, f"{f.name} 沾上了 per-request ContextVar 的身份"
    finally:
        set_current_subject_id("")


# ═══════════════════════════════════════════════════════════════════════════════
# 2) 跨 vault 不重放 (orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════


def test_vault_a_pending_is_not_replayed_under_vault_b(tmp_path, restore_settings):
    journals = tmp_path / "journals"
    a = _orchestrator(tmp_path / "va", "Vault A", journals)

    # A 攒下两条意图, 其中一条是 delete (卡文点名要覆盖的语义)
    assert a.enqueue("delete", "节点/gone.md") == "accepted"
    assert a.enqueue("delete", "原白板/dropped.md") == "accepted"
    assert a._pending_file.exists()
    a_sha = _sha(a._pending_file)
    a_bytes = a._pending_file.read_bytes()
    assert b'"op": "delete"' in a_bytes

    # 切到 B 重建 —— B 不该看到 A 的任何东西
    b = _orchestrator(tmp_path / "vb", "Vault B", journals)
    assert b._pending_file != a._pending_file
    assert b.recover() == 0, "B 不得重放 A 的 pending"
    assert b._pending == {}

    # A 的 journal 一个字节都没被碰过
    assert a._pending_file.exists()
    assert _sha(a._pending_file) == a_sha

    # 切回 A —— 它自己的意图仍在, 且 delete 语义保留
    a2 = _orchestrator(tmp_path / "va", "Vault A", journals)
    assert a2.recover() == 2
    assert set(a2._pending) == {"节点/gone.md", "原白板/dropped.md"}
    assert {e.op for e in a2._pending.values()} == {"delete"}


def test_index_service_pending_is_not_replayed_under_vault_b(tmp_path, restore_settings):
    journals = tmp_path / "journals"
    a = _index_service(tmp_path / "va", "Vault A", journals)
    a._persist_pending("canvas-a", "boom")
    assert a._pending_file.exists()
    a_sha = _sha(a._pending_file)

    b = _index_service(tmp_path / "vb", "Vault B", journals)
    assert b._pending_file != a._pending_file
    _r = asyncio.run(b.recover_pending(str(tmp_path / "vb")))
    # CARD-G2-5 round-3: 返回 dict 加性含 persist_failed（整 dict 相等改逐键, 原语义保留）
    assert (_r["recovered"], _r["pending"], _r["persist_failed"]) == (0, 0, 0)
    assert _sha(a._pending_file) == a_sha, "A 的 journal 不得被 B 改写"

    # 切回 A: 它自己的条目会被真正消费 (替身 index 成功 → recovered=1)
    a2 = _index_service(tmp_path / "va", "Vault A", journals)

    async def _ok(canvas_name, base_path):
        return 1

    calls = []

    async def _record(canvas_name, base_path):
        calls.append((canvas_name, base_path))
        return 1

    a2._do_index_with_retry = _record
    result = asyncio.run(a2.recover_pending(str(tmp_path / "va")))
    # ⛔ Codex round-1 MEDIUM-6: 只看 recovered 计数是死门 —— "不索引、只删文件
    # 然后返回 1" 也能让旧断言通过。必须钉住"真的按这条 canvas 调了索引"以及
    # "journal 被消费掉了"。
    # CARD-G2-5 round-3: persist_failed 加性键 —— 逐键断言（原语义保留）
    assert (result["recovered"], result["pending"], result["persist_failed"]) == (1, 0, 0)
    assert calls == [("canvas-a", str(tmp_path / "va"))]
    assert not a2._pending_file.exists(), "全部恢复后 journal 应被删除"


# ═══════════════════════════════════════════════════════════════════════════════
# 3) 旧的无维度 journal: 隔离, 不加载
# ═══════════════════════════════════════════════════════════════════════════════


def test_legacy_dimensionless_journal_is_quarantined_not_loaded(tmp_path, restore_settings, caplog):
    import logging

    journals = tmp_path / "journals"
    orch = _orchestrator(tmp_path / "va", "Vault A", journals)

    legacy = orch._legacy_pending_file
    legacy.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            {"rel_path": "节点/mystery.md", "op": "delete", "state": "pending", "enqueued_at": "2026-08-01T00:00:00"},
            ensure_ascii=False,
        )
        + "\n"
    )
    legacy.write_text(payload, encoding="utf-8")
    legacy_sha = _sha(legacy)

    with caplog.at_level(logging.WARNING):
        assert orch.recover() == 0, "无维度旧 journal 的条目不得被当成本 vault 的意图加载"

    assert orch._pending == {}
    assert not legacy.exists(), "旧文件必须被改名隔离"
    quarantined = journals / (legacy.name + ".pre-g25.bak")
    assert quarantined.exists()
    assert _sha(quarantined) == legacy_sha, "隔离只改名, 内容逐字节保留 (delete 意图仍可复盘)"

    text = " ".join(r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING)
    assert "pre-g25" in text or "隔离" in text


def test_index_service_legacy_journal_is_quarantined_not_loaded(tmp_path, restore_settings, caplog):
    """⛔ Codex round-1 MEDIUM-6(b): 之前只测了 orchestrator 这一侧的 legacy 入口。

    lancedb_index_service 的隔离入口是**另一段代码**, 必须各自锁。
    """
    import logging

    journals = tmp_path / "journals"
    svc = _index_service(tmp_path / "va", "Vault A", journals)

    legacy = svc._legacy_pending_file
    legacy.write_text(json.dumps({"canvas_name": "mystery", "error": "x"}) + "\n", encoding="utf-8")
    legacy_sha = _sha(legacy)

    with caplog.at_level(logging.WARNING):
        _r = asyncio.run(svc.recover_pending(str(tmp_path / "va")))
        assert (_r["recovered"], _r["pending"], _r["persist_failed"]) == (0, 0, 0)  # G2-5 round-3 加性键

    assert not legacy.exists()
    kept = journals / (legacy.name + ".pre-g25.bak")
    assert kept.exists() and _sha(kept) == legacy_sha


def test_quarantine_never_clobbers_any_existing_backup(tmp_path):
    """⛔ Codex round-1 HIGH-1 回归锁: 连"同一秒的时间戳备份"都不能被覆盖。

    旧实现只检查基础 ``.pre-g25.bak``, 存在就换成秒级时间戳名, 却**不检查
    时间戳名是否也存在**, 然后直接 rename —— 同一秒的第二次隔离会把上一份
    隔离件连同里面的 delete 意图覆盖掉。
    """
    from app.core.vault_state_paths import LEGACY_QUARANTINE_SUFFIX, quarantine_legacy_state_file

    d = tmp_path / "d"
    d.mkdir()
    base = d / ("vault_index_pending.jsonl" + LEGACY_QUARANTINE_SUFFIX)
    base.write_text("FIRST\n", encoding="utf-8")

    survivors = {"FIRST\n"}
    for i in range(3):
        legacy = d / "vault_index_pending.jsonl"
        payload = f"ROUND{i}\n"
        legacy.write_text(payload, encoding="utf-8")
        target = quarantine_legacy_state_file(legacy, context="test")
        assert target is not None
        survivors.add(payload)

    kept = {p.read_text(encoding="utf-8") for p in d.iterdir() if p.is_file()}
    assert kept == survivors, f"每一份隔离件都必须留存, 实际 {sorted(kept)}"


def test_filename_stays_within_linux_name_max(tmp_path, restore_settings):
    """⛔ Codex round-1 HIGH-3 回归锁: 长 CJK vault 名不得撑爆 Linux NAME_MAX。

    ``sanitize_vault_id`` 按**字符**截到 200; 200 个汉字 = 600 字节, 加上
    stem/后缀后 basename 达 631 字节 > ext4/overlayfs 的 255。旧实现下
    ``_persist_sync`` 会 ENAMETOOLONG, 而 ``enqueue()`` 仍返回 accepted ——
    durable 意图静默丢失。
    """
    from app.core.vault_state_paths import fs_safe_key, namespaced_state_path

    long_cjk = "一" * 200
    # 正向对照: 不压缩的话确实超预算 (否则本锁锁的是个不存在的问题)
    raw_name = f"vault_index_pending__{long_cjk}.jsonl.tmp"
    assert len(raw_name.encode("utf-8")) > 255

    safe = fs_safe_key(long_cjk, stem="vault_index_pending", suffix=".jsonl.tmp")
    assert safe != long_cjk and len(safe) < len(long_cjk)

    path = namespaced_state_path(tmp_path, "vault_index_pending", vault_key=long_cjk)
    for name in (path.name, path.with_suffix(".jsonl.tmp").name):
        assert len(name.encode("utf-8")) <= 255, f"{name} = {len(name.encode())} bytes"

    # 真写一次 —— 名字算得对不对, 文件系统说了算
    path.write_text("x", encoding="utf-8")
    assert path.exists()

    # 短 key 必须原样保留 (可读性不能被无差别摘要化)
    assert fs_safe_key("cs_61b", stem="vault_index_pending", suffix=".jsonl.tmp") == "cs_61b"

    # 不同的长 key 压缩后仍必须互不相同
    other = "二" * 200
    assert fs_safe_key(long_cjk, stem="s", suffix=".jsonl") != fs_safe_key(other, stem="s", suffix=".jsonl")


def test_quarantine_does_not_clobber_an_existing_backup(tmp_path):
    from app.core.vault_state_paths import LEGACY_QUARANTINE_SUFFIX, quarantine_legacy_state_file

    d = tmp_path / "d"
    d.mkdir()
    legacy = d / "vault_index_pending.jsonl"
    legacy.write_text("second\n", encoding="utf-8")
    first_backup = d / ("vault_index_pending.jsonl" + LEGACY_QUARANTINE_SUFFIX)
    first_backup.write_text("first\n", encoding="utf-8")

    target = quarantine_legacy_state_file(legacy, context="test")
    assert target is not None and target != first_backup
    assert first_backup.read_text(encoding="utf-8") == "first\n", "已有的隔离件不得被覆盖"
    assert target.read_text(encoding="utf-8") == "second\n"


def test_quarantine_returns_none_when_nothing_to_do(tmp_path):
    """正向对照: 没有旧文件时不造文件、不报错 (否则上面的断言可能只是巧合)。"""
    from app.core.vault_state_paths import quarantine_legacy_state_file

    d = tmp_path / "empty"
    d.mkdir()
    assert quarantine_legacy_state_file(d / "nope.jsonl", context="test") is None
    assert list(d.iterdir()) == []


# ═══════════════════════════════════════════════════════════════════════════════
# 4) 存量隔离器 (dry-run 零写入)
# ═══════════════════════════════════════════════════════════════════════════════


def _migrator():
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts" / "migrate_index_journals_g25.py"
    spec = importlib.util.spec_from_file_location("migrate_index_journals_g25", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _dir_fingerprint(root: Path) -> str:
    parts = [
        f"{p.name}:{p.stat().st_size}:{hashlib.sha256(p.read_bytes()).hexdigest()}"
        for p in sorted(root.iterdir())
        if p.is_file()
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def test_migrator_dry_run_flags_legacy_and_writes_nothing(tmp_path, monkeypatch, capsys):
    mod = _migrator()
    d = tmp_path / "data"
    d.mkdir()
    (d / "vault_index_pending.jsonl").write_text('{"rel_path": "a.md", "op": "delete"}\n', encoding="utf-8")
    (d / "vault_index_pending__v1.jsonl").write_text('{"rel_path": "b.md", "op": "upsert"}\n', encoding="utf-8")
    (d / "unrelated.json").write_text("{}", encoding="utf-8")
    before = _dir_fingerprint(d)

    monkeypatch.setattr("sys.argv", ["migrate_index_journals_g25.py", "--data-dir", str(d)])
    rc = mod.main()
    report = json.loads(capsys.readouterr().out)

    assert rc == 2, "有待隔离项的 dry-run 必须 exit 2"
    assert [x["name"] for x in report["legacy_dimensionless"]] == ["vault_index_pending.jsonl"]
    assert [x["vault_key"] for x in report["namespaced"]] == ["v1"]
    assert _dir_fingerprint(d) == before, "dry-run 必须逐字节零写入"


def test_migrator_dry_run_exit_zero_when_clean(tmp_path, monkeypatch, capsys):
    """反向对照: 没有无维度旧件时 exit 0 (证明 exit 2 不是恒定输出)。"""
    mod = _migrator()
    d = tmp_path / "clean"
    d.mkdir()
    (d / "vault_index_pending__v1.jsonl").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["migrate_index_journals_g25.py", "--data-dir", str(d)])
    assert mod.main() == 0
    capsys.readouterr()


def test_migrator_apply_quarantines_preserving_bytes(tmp_path, monkeypatch, capsys):
    mod = _migrator()
    d = tmp_path / "data"
    d.mkdir()
    payload = '{"rel_path": "节点/gone.md", "op": "delete"}\n'
    legacy = d / "lancedb_pending_index.jsonl"
    legacy.write_text(payload, encoding="utf-8")
    legacy_sha = hashlib.sha256(legacy.read_bytes()).hexdigest()

    monkeypatch.setattr("sys.argv", ["migrate_index_journals_g25.py", "--data-dir", str(d), "--apply"])
    rc = mod.main()
    report = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert report["pending_after"] == 0
    assert report["quarantine_actions"][0]["sha_preserved"] is True
    assert not legacy.exists()
    kept = d / "lancedb_pending_index.jsonl.pre-g25.bak"
    assert hashlib.sha256(kept.read_bytes()).hexdigest() == legacy_sha


def test_migrator_flags_legacy_tmp_crash_residue(tmp_path, monkeypatch, capsys):
    """⛔ Codex round-1 MEDIUM-7 回归锁: 崩溃残留的无维度 .jsonl.tmp 也是旧件。

    `_persist_sync` 走 tmp + os.replace，崩在中间就会留下
    `vault_index_pending.jsonl.tmp`；它同样无 vault 维度、同样可能带 delete 意图，
    而且被 .gitignore 藏着。只认 canonical `.jsonl` 会把它报成 clean。
    """
    mod = _migrator()
    d = tmp_path / "data"
    d.mkdir()
    (d / "vault_index_pending.jsonl.tmp").write_text('{"rel_path": "a.md", "op": "delete"}\n', encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["migrate_index_journals_g25.py", "--data-dir", str(d)])
    rc = mod.main()
    report = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert [x["name"] for x in report["legacy_dimensionless"]] == ["vault_index_pending.jsonl.tmp"]
    assert report["legacy_dimensionless"][0]["residue"] is True


def test_migrator_census_is_not_over_broad(tmp_path, monkeypatch, capsys):
    """⛔ Codex round-1 LOW-12 回归锁: 分类不能宽到把异常件当成合法类别。"""
    mod = _migrator()
    d = tmp_path / "data"
    d.mkdir()
    (d / "vault_index_pending__.jsonl").write_text("{}\n", encoding="utf-8")  # 空 key
    (d / "unrelated.pre-g25.bak").write_text("x\n", encoding="utf-8")  # 不是我们的 stem
    (d / "vault_index_pending__v1.jsonl").write_text("{}\n", encoding="utf-8")  # 合法

    monkeypatch.setattr("sys.argv", ["migrate_index_journals_g25.py", "--data-dir", str(d)])
    rc = mod.main()
    report = json.loads(capsys.readouterr().out)

    assert rc == 0, "本目录没有无维度旧件"
    assert [x["vault_key"] for x in report["namespaced"]] == ["v1"], "空 key 不得算合法命名空间件"
    assert report["quarantined"] == [], "非本卡 stem 的 .pre-g25.bak 不得算我们的隔离件"
    assert [x.get("why") for x in report["unclassified"]] == ["empty vault_key"]


def test_quarantine_never_eats_the_active_journal(tmp_path):
    """⛔ 自查回归锁: 绝不隔离**正在用的那份 journal**。

    legacy 路径由 `_pending_file.parent` 派生（HIGH-2 修法）。若调用方把工作
    journal 直接命名成无维度老名字（既有集成测试就是这么做的），两条路径会重合 ——
    没有这条守卫，recover 会先把自己要读的文件改名走，然后恒返回 0。
    这条是我改完 HIGH-2 后跑相邻套件才发现的（当场 2 条新增失败）。
    """
    from app.core.vault_state_paths import quarantine_legacy_state_file

    d = tmp_path / "d"
    d.mkdir()
    active = d / "lancedb_pending_index.jsonl"
    active.write_text('{"canvas_name": "c"}\n', encoding="utf-8")

    assert quarantine_legacy_state_file(active, context="test", active_path=active) is None
    assert active.exists(), "正在用的 journal 不得被搬走"
    assert list(d.iterdir()) == [active], "也不得留下任何隔离件"

    # 正向对照: 路径不重合时照常隔离 (否则这条守卫可能是"永远跳过")
    other = d / "vault_index_pending.jsonl"
    other.write_text("x\n", encoding="utf-8")
    target = quarantine_legacy_state_file(other, context="test", active_path=active)
    assert target is not None and not other.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# 5) CARD-G2-5 round-3 (BATCH-2026-09-01-第八批): durable 写失败必须可见 (HIGH-3)
#    + 口径三锁 (HIGH-4)。故障注入只有「state_dir 指向普通文件」一种 (卡文铁律)。
# ═══════════════════════════════════════════════════════════════════════════════


def _bad_state_dir(tmp_path) -> Path:
    """构造「普通文件充当 state_dir」的故障注入点 (⛔ 唯一允许的 OS 注入形态)。"""
    bad = tmp_path / "not_a_dir"
    bad.write_text("i am a file, not a directory\n", encoding="utf-8")
    return bad


def _plain_orchestrator(vault_root: Path, state_dir: Path):
    from app.services import vault_index_orchestrator as mod
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    # LOW-11 门的精神: 注入前先确认未注入时确实落在生产 data 目录
    _assert_production_state_dir(VaultIndexOrchestrator(vault_path=str(vault_root)), mod)
    return VaultIndexOrchestrator(vault_path=str(vault_root), state_dir=str(state_dir))


def test_orchestrator_enqueue_reports_persist_failed_when_state_dir_is_a_file(tmp_path):
    """(d)① ⛔ HIGH-3 主锁: journal 写不进去时 enqueue 必须报 persist_failed。

    round-2 的生产反例: state_dir 指向普通文件 → mkdir 抛 → 被吞 → 仍返回
    accepted、journal 不存在 —— 用户看到成功, 意图实际丢了。正向对照同测试内
    换成好目录, 证明 persist_failed 不是恒定输出。
    """
    d = tmp_path / "vault"
    d.mkdir()
    bad = _bad_state_dir(tmp_path)
    orch = _plain_orchestrator(d, bad)

    assert orch.enqueue("upsert", "节点/a.md") == "persist_failed"
    # 既没 durable 也不算 accepted: 不进内存 pending, journal 不存在
    assert "节点/a.md" not in orch._pending
    assert not orch._pending_file.exists()
    f = orch.freshness()
    assert f["durable_degraded"] is True
    assert f["durable_write_failures"] == 1
    assert f["last_durable_error"] and "Errno" in f["last_durable_error"]

    # 正向对照: 好目录 → accepted + 文件落盘 + 未降级
    good = _plain_orchestrator(d, tmp_path / "good_state")
    assert good.enqueue("upsert", "节点/a.md") == "accepted"
    assert good._pending_file.exists()
    assert good.freshness()["durable_degraded"] is False


def test_orchestrator_coalesce_path_also_reports_persist_failed(tmp_path):
    """(d)② coalesced 路径同样必须报 persist_failed (不能只修新条目半边)。

    ⛔ round-3 Codex 死门整改: 失败时**回滚**既有条目的字段改写也全绿 ——
    现用不同 op 的第二次 enqueue (upsert→delete) 并断言失败后 op 仍为 delete
    (内存变更保留是卡文写死的语义)。
    """
    d = tmp_path / "vault"
    d.mkdir()
    good_dir = tmp_path / "good_state"
    orch = _plain_orchestrator(d, good_dir)
    assert orch.enqueue("upsert", "节点/a.md") == "accepted"

    # 原地变坏: journal 目录换成坏路径 (既有测试同款属性直改手法)
    orch._pending_file = _bad_state_dir(tmp_path) / "vault_index_pending__x.jsonl"
    assert orch.enqueue("delete", "节点/a.md") == "persist_failed"
    # 已有条目保留内存变更 (worker 尽力而为), 但对外不报成功
    assert "节点/a.md" in orch._pending
    assert orch._pending["节点/a.md"].op == "delete", "失败后内存变更必须保留 (不得回滚成 upsert)"
    assert orch._durable_degraded is True


async def _drive_refresh_changed(paths, orch):
    from app.api.v1.endpoints.index import refresh_changed_paths
    from app.api.v1.endpoints.index import RefreshChangedRequest

    import app.services.vault_index_orchestrator as orch_mod

    orig = orch_mod.get_vault_index_orchestrator
    orch_mod.get_vault_index_orchestrator = lambda: orch
    try:
        return await refresh_changed_paths(RefreshChangedRequest(paths=paths))
    finally:
        orch_mod.get_vault_index_orchestrator = orig


def test_refresh_changed_endpoint_returns_503_when_journal_unwritable(tmp_path):
    """(d)③ ⛔ 真实 handler 直调: 任一路径落盘失败 → 503 + 完整 body。

    ⛔ patch 点必须是 vault_index_orchestrator 模块 —— handler 在函数体内局部
    import (patch index 端点模块完全无效, 会拿生产单例写真 data 目录)。
    """
    d = tmp_path / "vault"
    d.mkdir()
    paths = ["节点/a.md", "节点/b.md"]
    bad = _plain_orchestrator(d, _bad_state_dir(tmp_path))

    resp = asyncio.run(_drive_refresh_changed(paths, bad))
    assert resp.status_code == 503
    body = json.loads(resp.body)
    # ⛔ round-3 Codex 死门整改: 「完整 body」必须逐键断言 —— 旧版只看三个键,
    # 删掉其余四个字段的变异仍全绿
    assert set(body) == {
        "accepted",
        "coalesced",
        "excluded",
        "results",
        "orchestrator_enabled",
        "persist_failed",
        "durable",
    }, f"503 body 必须是完整七字段契约, 实际: {sorted(body)}"
    assert body["persist_failed"] == len(paths)
    assert body["durable"] is False
    assert body["accepted"] == 0 and body["coalesced"] == 0 and body["excluded"] == 0
    assert body["orchestrator_enabled"] is True
    assert [r["status"] for r in body["results"]] == ["persist_failed"] * len(paths)

    # 正向对照: 好实例 → 200 语义 (RefreshChangedResponse, durable=True)
    good = _plain_orchestrator(d, tmp_path / "good_state")
    ok = asyncio.run(_drive_refresh_changed(paths, good))
    assert isinstance(ok, dict) is False  # 保持 pydantic 模型, 不是 JSONResponse
    assert ok.durable is True
    assert ok.persist_failed == 0
    assert [r.status for r in ok.results] == ["accepted"] * len(paths)

    # ⛔ round-4b Codex MEDIUM: 混合场景——部分路径 excluded 部分 persist_failed
    # → 仍必须 503 (任何 durable 失败都不许被成功/排除路径稀释)
    (tmp_path / "m").mkdir()
    mixed_orch = _plain_orchestrator(d, _bad_state_dir(tmp_path / "m"))
    mixed_resp = asyncio.run(_drive_refresh_changed(["节点/ok.md", "/abs/x.md"], mixed_orch))
    # "/abs/x.md" 绝对路径 → enqueue 首道守卫直接 excluded (确定性, 不依赖黑名单);
    # "节点/ok.md" 走 enqueue → persist_failed
    assert mixed_resp.status_code == 503
    mixed_body = json.loads(mixed_resp.body)
    assert mixed_body["persist_failed"] == 1
    assert mixed_body["durable"] is False
    assert sorted(r["status"] for r in mixed_body["results"]) == ["excluded", "persist_failed"]


def test_lance_persist_pending_returns_false_when_state_dir_is_a_file(tmp_path):
    """(d)④ Lance service 同型锁: _persist_pending 返回 False + 计数可见。"""
    from app.services.lancedb_index_service import LanceDBIndexService

    bad = _bad_state_dir(tmp_path)
    svc = LanceDBIndexService(state_dir=str(bad))
    assert svc._persist_pending("canvas-x", "boom") is False
    assert svc.durable_status()["failures"] == 1
    assert svc.durable_status()["last_error"]
    assert not svc._pending_file.exists()

    # 正向对照: 好目录 → True + journal 落盘
    good = LanceDBIndexService(state_dir=str(tmp_path / "good_state"))
    assert good._persist_pending("canvas-x", "boom") is True
    assert good._pending_file.exists()


def test_lance_debounced_index_logs_intent_lost_when_persist_fails(tmp_path, caplog, monkeypatch):
    """(d)⑤ durable 也写失败时必须有一条 ERROR「intent lost」与 WARNING 区分。

    _do_index_with_retry 替身抛异常 = 被测方法的输入 (允许); journal 落盘走
    真实 _persist_pending 在坏 state_dir 上真失败。
    """
    import logging
    from unittest.mock import AsyncMock

    from app.services.lancedb_index_service import LanceDBIndexService

    svc = LanceDBIndexService(state_dir=str(_bad_state_dir(tmp_path)))
    svc._do_index_with_retry = AsyncMock(side_effect=RuntimeError("index backend down"))
    monkeypatch.setattr(svc, "_debounce_seconds", 0.01)

    with caplog.at_level(logging.ERROR):
        asyncio.run(svc._debounced_index("my_canvas", str(tmp_path / "vault")))

    lost = [r for r in caplog.records if "intent lost" in r.getMessage() and "my_canvas" in r.getMessage()]
    assert lost, f"必须有一条含 intent lost + canvas 名的 ERROR, 实际: {[r.getMessage() for r in caplog.records]}"
    assert all(r.levelno == logging.ERROR for r in lost)


def test_lance_recover_pending_keeps_journal_when_rewrite_fails(tmp_path, monkeypatch):
    """(d)⑥ 两半门: helper 半证「失败被识别 + 不留残片」, recover 半证「返回值
    传递 + 原 journal 逐字节不动」。两者合起来仍不证明端到端 OS 失败链 (如实)。
    """
    from app.services.lancedb_index_service import LanceDBIndexService

    # —— 半 1 (helper 门): 坏 state_dir 下 _rewrite_journal 返回 False 且不留残片
    bad_file = _bad_state_dir(tmp_path)
    bad_svc = LanceDBIndexService(state_dir=str(bad_file))
    ok = bad_svc._rewrite_journal([{"canvas_name": "c", "error": "e"}])
    assert ok is False
    assert not (bad_file.parent / (bad_file.name + ".tmp")).exists(), "不得留 tmp 残片"

    # —— 半 2 (传递门): 好目录 journal + 一条恢复失败 + 重写强制失败
    good_dir = tmp_path / "good_state"
    good_dir.mkdir()
    entries = [
        {"canvas_name": "canvas-a", "error": "e1"},
        {"canvas_name": "canvas-b", "error": "e2"},
    ]
    journal = good_dir / "lancedb_pending_index__vk.jsonl"
    journal.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")
    before = journal.read_bytes()

    svc = LanceDBIndexService(state_dir=str(good_dir))
    svc._pending_file = journal

    calls: list[str] = []

    async def _flaky(canvas_name: str, base_path: str) -> int:
        if canvas_name == "canvas-a":
            raise RuntimeError("index backend down")
        calls.append(canvas_name)
        return 1

    svc._do_index_with_retry = _flaky
    # 最小注入: 重写这一步强制失败 (与替身同级; 真 OS 失败半已由半 1 证明)
    monkeypatch.setattr(svc, "_rewrite_journal", lambda entries: False)

    result = asyncio.run(svc.recover_pending(str(tmp_path / "vault")))
    assert result["persist_failed"] == 1
    assert result["recovered"] == 1 and result["pending"] == 1
    assert journal.read_bytes() == before, "重写失败时原 journal 必须逐字节不动"

    # —— 正向对照 (round-3 Codex 死门整改: 「好目录假 True 且零写」变异绕过
    # 旧两半) —— 真实 _rewrite_journal 在好目录必须**真的写**: journal 收缩为
    # still-pending 那一条。
    good_dir2 = tmp_path / "good_state2"
    good_dir2.mkdir()
    entries2 = [
        {"canvas_name": "canvas-a", "error": "e1"},
        {"canvas_name": "canvas-b", "error": "e2"},
    ]
    journal2 = good_dir2 / "lancedb_pending_index__vk.jsonl"
    journal2.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries2), encoding="utf-8")
    svc2 = LanceDBIndexService(state_dir=str(good_dir2))
    svc2._pending_file = journal2

    async def _flaky2(canvas_name: str, base_path: str) -> int:
        if canvas_name == "canvas-a":
            raise RuntimeError("index backend down")
        return 1

    svc2._do_index_with_retry = _flaky2
    result2 = asyncio.run(svc2.recover_pending(str(tmp_path / "vault")))
    assert result2["persist_failed"] == 0
    kept = [json.loads(ln) for ln in journal2.read_text(encoding="utf-8").strip().splitlines() if ln.strip()]
    # ⛔ round-4b Codex MEDIUM: 逐键断言 (旧版只比 canvas_name, 字段丢失/改变仍绿)
    assert kept == [{"canvas_name": "canvas-a", "error": "e1"}], (
        f"真实重写必须把 journal 收缩为 still-pending 条目 (内容逐键), 实际: {kept}"
    )


def test_lance_recover_preserves_concurrent_appends(tmp_path):
    """⛔ round-3 Codex HIGH 竞态回归锁: recover 锁外重放期间的并发 append
    不得被旧快照覆盖/unlink 静默删除。

    复现载体: 替身在恢复 canvas-a 时**真实调用** _persist_pending 追加
    canvas-new (模拟另一 canvas 的 fire-and-forget 失败在 recover 窗口内
    append 成功)。修复后合并语义必须保留它; 变异 (恢复旧快照 rewrite) 下
    journal 会丢 canvas-new → 本锁红。
    """
    from app.services.lancedb_index_service import LanceDBIndexService

    good_dir = tmp_path / "good_state"
    good_dir.mkdir()
    entries = [
        {"canvas_name": "canvas-a", "error": "e1"},
        {"canvas_name": "canvas-b", "error": "e2"},
    ]
    journal = good_dir / "lancedb_pending_index__vk.jsonl"
    journal.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")

    svc = LanceDBIndexService(state_dir=str(good_dir))
    svc._pending_file = journal

    async def _concurrent_append(canvas_name: str, base_path: str) -> int:
        if canvas_name == "canvas-a":
            # 模拟重放窗口内另一 task 的 durable 失败 append (成功落盘)
            assert svc._persist_pending("canvas-new", "boom during recovery") is True
            raise RuntimeError("index backend down")
        return 1

    svc._do_index_with_retry = _concurrent_append
    result = asyncio.run(svc.recover_pending(str(tmp_path / "vault")))

    assert result["persist_failed"] == 0
    kept_names = [
        json.loads(ln)["canvas_name"] for ln in journal.read_text(encoding="utf-8").strip().splitlines() if ln.strip()
    ]
    assert "canvas-new" in kept_names, f"重放期间成功落盘的并发 append 不得被旧快照抹掉, journal 实际: {kept_names}"
    assert "canvas-a" in kept_names, "恢复失败的条目 (still_pending) 必须保留"
    assert "canvas-b" not in kept_names, "恢复成功的条目应被消费掉"


def test_long_cjk_key_accepted_through_real_orchestrator_enqueue(tmp_path, restore_settings):
    """(d)⑦ 200 汉字 key 走**真实** orchestrator: accepted 且文件真的落盘。

    沿用既有 test_filename_stays_within_linux_name_max (helper 级) 的场景,
    补真实服务级一锁 (既有 :288 只测 helper)。
    """
    from app.services import vault_index_orchestrator as mod
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    long_cjk = "一" * 200
    state_dir = tmp_path / "j"
    _switch_vault(tmp_path / "vault", long_cjk)
    _assert_production_state_dir(VaultIndexOrchestrator(vault_path=str(tmp_path / "vault")), mod)
    orch = VaultIndexOrchestrator(vault_path=str(tmp_path / "vault"), state_dir=str(state_dir))

    assert orch.enqueue("delete", "节点/a.md") == "accepted"
    assert orch._pending_file.exists(), "fs_safe_key 压缩后的名字必须真能落盘"
    assert len(orch._pending_file.name.encode("utf-8")) <= 255


# ── (e) HIGH-4 口径三锁 ────────────────────────────────────────────────────────


def test_convergence_wording_facts_are_bound_to_code():
    """(e)① 事实绑定门: 口径文案的每条事实必须钉在代码上。

    ⛔ round-3 Codex 绕过整改: 旧版只 hasattr —— 把 ``_scan_loop`` 改成立即
    返回的空壳仍绿。现加**源码级绑定**: 周期反熵必须真的由 reconcile +
    sleep(interval) 组成, 且扫描作用域就是 self.vault_path。

    注意: model_fields 断言只锁**声明默认值** (settings 实例可被 env/.env
    覆盖, 本门不锁运行期取值 —— 如实声明, 不比证据宽)。
    """
    import inspect
    import re

    from app.config import Settings
    from app.services.lancedb_index_service import LanceDBIndexService
    from app.services.vault_index_orchestrator import VaultIndexOrchestrator

    assert hasattr(VaultIndexOrchestrator, "reconcile")
    assert hasattr(VaultIndexOrchestrator, "_scan_loop")
    scan_files_src = inspect.getsource(VaultIndexOrchestrator._scan_vault_md_files)
    assert "self.vault_path" in scan_files_src, "扫描作用域必须是 self.vault_path (只覆盖当前部署)"
    assert Settings.model_fields["VAULT_INDEX_SCAN_INTERVAL_S"].default == 60
    hit = [n for n in dir(LanceDBIndexService) if re.search(r"reconcile|scan|anti_entropy|_loop", n)]
    assert not hit, f"LanceDBIndexService 不得出现周期反熵入口, 命中: {hit}"

    # ⛔ 行为级绑定 (round-4 自查: getsource 检测会被「return 短路 + 留死代码」
    # 的变异骗过) —— 真跑 _scan_loop 两个周期, reconcile 必须被调用 ≥2 次。
    import asyncio
    import tempfile

    d = Path(tempfile.mkdtemp(prefix="g25-e1-"))
    orch = VaultIndexOrchestrator(vault_path=str(d), state_dir=str(d / "j"))
    orch._scan_interval = 0.02
    calls = {"n": 0}

    async def _counting_reconcile(force=False):
        calls["n"] += 1
        return {}

    orch.reconcile = _counting_reconcile

    async def _probe():
        task = asyncio.create_task(orch._scan_loop())
        await asyncio.sleep(0.09)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(_probe())
    assert calls["n"] >= 2, f"_scan_loop 必须周期性调用 reconcile (≥2 次/2 周期), 实际 {calls['n']} 次"


def test_lance_quarantined_intent_has_no_automatic_reentry(tmp_path, monkeypatch):
    """(e)② 行为门: 隔离后的意图没有任何自动重回入口 —— 事件循环跑**远超**
    debounce 周期的观察窗口后替身调用恒 0 且调度表为空; 正向对照 schedule_index
    一次 → 恰 1 次 (>=0 会把 flag 关闭时的空转也放行, 必须 ==1)。

    ⛔ round-3 Codex 绕过整改: 旧窗口 0.04s —— 0.20s 延迟的自动重入能逃过窗口。
    现窗口 1.0s (覆盖默认 0.5s debounce 的两个完整周期) + 断言
    ``svc._pending_tasks == {}`` (「无自动重入」的本质: 隔离不得调度任何 task)。
    """
    import logging
    import time as _time

    from app.services.lancedb_index_service import LanceDBIndexService

    state_dir = tmp_path / "j"
    state_dir.mkdir()
    legacy = state_dir / "lancedb_pending_index.jsonl"
    legacy.write_text(json.dumps({"canvas_name": "mystery", "error": "x"}) + "\n", encoding="utf-8")

    svc = LanceDBIndexService(state_dir=str(state_dir))
    monkeypatch.setattr(svc, "_debounce_seconds", 0.01)  # 构造后 patch 实例属性 (settings 只在 __init__ 读)

    calls: list[str] = []

    async def _stub(canvas_name: str, base_path: str) -> int:
        calls.append(canvas_name)
        return 1

    svc._do_index_with_retry = _stub

    async def _scenario():
        result = await svc.recover_pending(str(tmp_path / "vault"))
        assert result["recovered"] == 0, "无维度旧 journal 不得被加载"
        quarantined = list(state_dir.glob("*.pre-g25.bak*"))
        assert len(quarantined) == 1 and quarantined[0].exists(), "隔离件必须存在"
        assert svc._pending_tasks == {}, "隔离不得调度任何 debounce task (自动重入的本质载体)"
        # 负向: 观察窗口 1.0s —— 覆盖默认 debounce (0.5s) 的两个完整周期,
        # 任何 ≤0.2s 延迟的自动重入都落在窗口内
        await asyncio.sleep(1.0)
        assert calls == [], f"隔离后不得自动重试, 实际调用: {calls}"
        # 正向对照: 真实调度一次 → 恰好 1 次 (证明替身链路本身是通的)
        svc.schedule_index("canvas-c", str(tmp_path / "vault"))
        deadline = _time.monotonic() + 2.0
        while not calls and _time.monotonic() < deadline:
            await asyncio.sleep(0.005)
        await asyncio.sleep(0.02)
        assert calls == ["canvas-c"], f"正向对照必须恰好 1 次, 实际: {calls}"

    asyncio.run(_scenario())


def _assert_convergence_wording(text: str) -> None:
    """(e)③ helper: 一段口径文本必须同时含两个限定短语, 且收敛断言必须处于引用-否定语境。

    ⛔ round-3 Codex 绕过整改后的判据 (旧判据的三个洞逐一封死):

    - 「没有周期反熵」的命中**所在句**不得含疑问标记 —— 旧 lookbehind
      ``(?<!有)`` 只挡「有没有」, 挡不住「是否没有」「有 没有周期反熵」。
    - 收敛断言正则扩到等价措辞: 「一分钟内必收敛」「60秒内必然收敛」与
      「60秒内必收敛」同义, 旧正则会漏。
    - 收敛断言命中处的前文必须是**引用-否定语境** (旧文案/原文案/原文/旧说法/
      曾写/原话 + 不成立) —— 旧否定词表含裸「不是」, 会被「不是偶尔, 而是约
      60 秒内必收敛」这种肯定性修辞误放。
    """
    import re

    assert "只覆盖当前部署" in text, "缺作用域限定「只覆盖当前部署」"
    # ⛔ round-4b Codex HIGH: 存在性断言必须独立于句级循环 —— 缺「没有周期反熵」
    # 时 finditer 零次循环会静默放行 (旧版正是这个洞, 且旧篡改门测的是缺第一
    # 短语的反方向)
    assert "没有周期反熵" in text, "缺事实断言「没有周期反熵」"

    question_marks = ("？", "?", "吗", "呢", "是否", "有没有", "难道", "岂", "怎能", "怎么会")
    for m in re.finditer(r"没有周期反熵", text):
        start = text.rfind("。", 0, m.start())
        end = text.find("。", m.start())
        sentence = text[start + 1 : end if end != -1 else len(text)]
        hit = [q for q in question_marks if q in sentence]
        assert not hit, f"「没有周期反熵」出现在疑问/反问句中: {sentence!r} (疑问标记 {hit})"

    # 收敛断言的等价形态族 (round-4 Codex 绕过整改: 中文数字/「保证…一致」/
    # 「必然收敛」均为同义改写)
    claim_res = (
        r"(约|在)?\s*(60|六十)\s*(秒|s)\s*(内|之内)?\s*必(然)?收敛",
        r"(一分钟|1分钟)\s*(内|之内)?\s*必(然)?收敛",
        r"(六十|60)\s*秒\s*(内|之内)?\s*(保证|确保|必然|一定)?\s*(达到一致|保持一致|一致)",
    )
    quote_marks = ("旧文案", "原文案", "原文", "旧说法", "曾写", "原话")
    negation_marks = ("不成立", "是错的", "错误", "不对", "不实", "错的")
    # ⛔ 语境伪造标记 (round-4 Codex 绕过: 「旧文案错误已澄清；新结论：约60秒内
    # 必然收敛」—— 引用与否定标记都被伪造成彩翼, 但「新结论」暴露这是活断言)
    assertion_marks = ("新结论", "结论是", "因此", "所以", "本文结论", "现在可以确认")
    for cre in claim_res:
        for m in re.finditer(cre, text):
            window = text[max(0, m.start() - 24) : m.start()]
            span = text[max(0, m.start() - 40) : m.end() + 16]
            near = text[max(0, m.start() - 30) : m.end() + 30]
            assert not any(a in near for a in assertion_marks), (
                f"收敛断言带活断言引导词 (新结论/因此…), 不得以引用语境放行: {near!r}"
            )
            assert any(w in window for w in quote_marks) and any(n in span for n in negation_marks), (
                f"收敛断言必须处于「引用旧文案并否定」语境, 前文: {window!r}"
            )


def test_convergence_wording_has_no_unqualified_60s_claim(tmp_path, caplog):
    """(e)③ 文案门: 三段真实口径文本逐段过 helper; 十条篡改门必须 AssertionError。"""
    import ast as _ast
    import logging

    from app.core.vault_state_paths import quarantine_legacy_state_file
    from app.services.lancedb_index_service import LanceDBIndexService

    # 段 1: quarantine docstring (禁改面, 只做措辞微调后的形态)
    _assert_convergence_wording(quarantine_legacy_state_file.__doc__)

    # 段 2: migrator 模块 docstring —— ast 零副作用加载 (importlib 会写
    # __pycache__ 进 vault 并在测试进程里改 sys.path)
    migrator_path = Path(__file__).resolve().parents[2] / "scripts" / "migrate_index_journals_g25.py"
    module_doc = _ast.get_docstring(_ast.parse(migrator_path.read_text(encoding="utf-8"))) or ""
    _assert_convergence_wording(module_doc)

    # 段 3: 实际发出的隔离 warning 全文 (caplog 捕获, 非 logger 调用点的字面量)
    state_dir = tmp_path / "j"
    state_dir.mkdir()
    (state_dir / "lancedb_pending_index.jsonl").write_text(
        json.dumps({"canvas_name": "mystery", "error": "x"}) + "\n", encoding="utf-8"
    )
    svc = LanceDBIndexService(state_dir=str(state_dir))
    with caplog.at_level(logging.WARNING):
        asyncio.run(svc.recover_pending(str(tmp_path / "vault")))
    warnings_text = "\n".join(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "已隔离" in warnings_text, f"隔离 warning 必须发出, 实际: {warnings_text!r}"
    _assert_convergence_wording(warnings_text)

    # 篡改门 ×10: 每道放行门配**专测那道半**的同语料篡改门 (round-3 Codex:
    # 旧第一条同时缺两短语, 删掉 60s 检查它照样红 —— 没有专测 60s 半;
    # round-4 抢救三绕过 + round-4b 缺第二短语反方向, 共 10 条)
    with pytest.raises(AssertionError):
        _assert_convergence_wording("旧 journal 在约 60 秒内必收敛, 无需处理。")  # 全缺
    with pytest.raises(AssertionError):
        _assert_convergence_wording("两个 journal 有没有周期反熵? 只覆盖当前部署的范围。")  # 疑问句
    with pytest.raises(AssertionError):
        _assert_convergence_wording("lancedb 侧没有周期反熵。")  # 缺另一短语
    # ⛔ round-4b Codex HIGH 堵口: 反方向篡改——只缺「没有周期反熵」。样本刻意
    # 满足引用-否定语境 (能过语境检查), 唯一能拒它的是第二短语存在性断言
    # (旧版此处无测试, helper 对第二短语缺失零次循环静默放行)
    with pytest.raises(AssertionError):
        _assert_convergence_wording(
            "orchestrator 侧只覆盖当前部署的这个 vault（旧文案曾经这么写），约 60 秒内必收敛，不成立。"
        )
    # 专测 60s 语境半: 含两短语、收敛断言不带引用-否定 → 必须红
    with pytest.raises(AssertionError):
        _assert_convergence_wording(
            "orchestrator 侧只覆盖当前部署的这个 vault; lancedb 侧没有周期反熵。旧结论: 约 60 秒内必收敛。"
        )
    # 等价措辞漏判堵口: 「一分钟内必收敛」「60秒内必然收敛」同属未限定收敛断言
    with pytest.raises(AssertionError):
        _assert_convergence_wording("只覆盖当前部署的范围; 没有周期反熵。一分钟内必收敛, 不成立也无所谓。")
    # 肯定性修辞误放堵口: 「不是偶尔, 而是…」的「不是」不得充当否定
    with pytest.raises(AssertionError):
        _assert_convergence_wording("只覆盖当前部署的范围; 没有周期反熵。不是偶尔, 而是约 60 秒内必收敛。")
    # ⛔ round-4 Codex 三个新绕过 (stderr 抢救样本逐字固化): 反问句 / 中文数字
    # 「保证…一致」变体 / 引用语境伪造 (「新结论」引导的活断言)
    with pytest.raises(AssertionError):
        _assert_convergence_wording("orchestrator 只覆盖当前部署；难道 lancedb 没有周期反熵。")
    with pytest.raises(AssertionError):
        _assert_convergence_wording("orchestrator 只覆盖当前部署；lancedb 没有周期反熵。最多六十秒保证达到一致。")
    with pytest.raises(AssertionError):
        _assert_convergence_wording(
            "orchestrator 只覆盖当前部署；lancedb 没有周期反熵。旧文案错误已澄清；新结论：约60秒内必然收敛。"
        )
