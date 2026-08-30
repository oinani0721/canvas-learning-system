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
    assert asyncio.run(b.recover_pending(str(tmp_path / "vb"))) == {"recovered": 0, "pending": 0}
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
    assert result == {"recovered": 1, "pending": 0}
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
        assert asyncio.run(svc.recover_pending(str(tmp_path / "va"))) == {"recovered": 0, "pending": 0}

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
