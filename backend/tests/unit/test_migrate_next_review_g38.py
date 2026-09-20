"""CARD-G3-8 — ``scripts/migrate_next_review_g38.py`` 行为门.

[BATCH-2026-09-18-第十五批 / CARD-G3-8]

被测对象是**旧 ``next_review`` 对账迁移器**: 把 frontmatter ``fsrs_due``
(D0 T1 裁定的唯一真相源) 对账到目标侧的 ``next_review`` (Neo4j ``LEARNED``
边 / JSON 镜像 ``relationships[].next_review``)。

加载方式抄 ``tests/regression/test_g3_5_vault_keyed_card_states.py:295-310``
(``scripts/`` 不是包 ⇒ 按路径 ``spec_from_file_location`` + **先注册
``sys.modules`` 再 ``exec_module``**)。

⚠️ **先红纪律 (卡文 (b)③④)**: :func:`_migrator` 与 :func:`_script_source`
的第一条语句都是显式断言「尚不存在」。脚本未写时本文件**每一条**用例都红在
那条断言上, 而不是裸 ``ImportError`` / 夹具错 —— 后两者也可能来自 conftest
崩了或路径写错, 说明不了「实现确实缺席」。7692 真库组同理: 可达性探针排在
:func:`_migrator` **之后**, 否则脚本缺席时该组会 skip 而不是红。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional

import pytest

# ── 被测脚本 ────────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parents[2]
SCRIPT_PATH = _BACKEND / "scripts" / "migrate_next_review_g38.py"

#: 先红断言的**唯一**文案 —— 卡文 (b)③ 的 `grep -c '尚不存在'` 锚在这个串上。
_ABSENT_MSG = "migrate_next_review_g38.py 尚不存在"


def _migrator():
    """按路径加载迁移器 (``scripts/`` 不是包)。"""
    assert SCRIPT_PATH.is_file(), _ABSENT_MSG
    spec = importlib.util.spec_from_file_location("g38_migrator", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # 先注册再 exec —— 动态加载的模块若含模块级自省 (dataclass 等) 会取
    # sys.modules[cls.__module__]; 保持这个安全写法 (Python 3.14 起必需)。
    sys.modules["g38_migrator"] = mod
    spec.loader.exec_module(mod)
    return mod


def _script_source() -> str:
    """只读脚本文本 (AST / 字面量门用)。缺席时红在同一条断言上。"""
    assert SCRIPT_PATH.is_file(), _ABSENT_MSG
    return SCRIPT_PATH.read_text(encoding="utf-8")


# ── 现网常量 (只做字符串比对, 绝不拿它们做 I/O) ─────────────────────────────
_LIVE_REPO_ROOT = "/Users/Heishing/Desktop/canvas/canvas-learning-system"
_LIVE_VAULT_DIR = _LIVE_REPO_ROOT + "/canvas-vault"
_LIVE_JSON_MIRROR = _LIVE_REPO_ROOT + "/backend/data/neo4j_memory.json"
_LIVE_CARD_STATES = _LIVE_REPO_ROOT + "/backend/data/fsrs_card_states.json"


# ── fixture 工具 ────────────────────────────────────────────────────────────
def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha(root: Path) -> Dict[str, str]:
    """目录下全部普通文件的 {相对路径: sha256} —— dry-run 零写入的判据。"""
    return {str(p.relative_to(root)): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def _utc_z_to_naive_local(iso_z: str) -> str:
    """UTC-Z 串 → **naive 本地** ISO —— 与 JSON 镜像写方同款形态.

    ``neo4j_client.py:717-718`` 写的是 ``datetime.now()`` (naive 本地) 加一天后
    ``.isoformat()``; ``:793`` 的读方同样拿 naive 的 ``datetime.now()`` 比大小。
    两侧同为 naive 本地 ⇒ 该文件里 naive 值的语义是**本地时间**, 这是代码可证的
    契约, 不是猜测。
    """
    dt = datetime.strptime(iso_z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone().replace(tzinfo=None).isoformat()


def _write_vault_config(vault: Path, vault_id: str) -> Path:
    """写 ``<vault>/.canvas-config.yaml`` —— vault 自报身份的唯一载体。

    迁移器用它把 ``--group-id`` 绑到这个目录上: 两个参数各自合法、合起来指向
    不同 vault 时（``--vault-dir A --group-id vault__B``）就是跨 vault 写。
    """
    vault.mkdir(parents=True, exist_ok=True)
    cfg = vault / ".canvas-config.yaml"
    cfg.write_text(
        f'# 测试 vault\nvault_id: "{vault_id}"\nsubject: g38-fixture\n',
        encoding="utf-8",
    )
    return cfg


def _write_node(vault: Path, stem: str, fsrs_due: Optional[str], sub: str = "节点") -> Path:
    """在 ``<vault>/<sub>/`` 下造一个节点 ``.md``; ``fsrs_due=None`` ⇒ ungoverned。"""
    d = vault / sub
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{stem}.md"
    if fsrs_due is None:
        body = f"---\ntitle: {stem}\nfsrs_state: 0\n---\n\n正文 {stem}\n"
    else:
        body = f"---\ntitle: {stem}\nfsrs_due: {fsrs_due}\nfsrs_state: 2\nfsrs_stability: 3.5\n---\n\n正文 {stem}\n"
    p.write_text(body, encoding="utf-8")
    return p


_DUE_A = "2026-09-20T03:00:00Z"
_DUE_B = "2026-09-21T04:00:00Z"


def _mirror_payload(gid: str, uid: str) -> Dict[str, Any]:
    """JSON 镜像形态 —— 抄 ``neo4j_client.py:305`` 的 ``self._data`` 与 :745-749 的行形态。"""
    return {
        "users": [{"id": uid, "name": uid}],
        "concepts": [
            {"id": "c-a", "name": "concept-a", "group_id": gid},
            {"id": "c-b", "name": "concept-b", "group_id": gid},
            {"id": "c-c", "name": "concept-c", "group_id": gid},
            {"id": "c-d", "name": "concept-d", "group_id": gid},
        ],
        "relationships": [
            {
                "id": "learned-1",
                "user_id": uid,
                "concept_id": "c-a",
                "concept_name": "concept-a",
                "timestamp": "2026-09-01T10:00:00",
                "last_score": 80,
                "next_review": "2026-09-02T10:00:00",
                "review_count": 3,
                "group_id": gid,
            },
            {
                "id": "learned-2",
                "user_id": uid,
                "concept_id": "c-b",
                "concept_name": "concept-b",
                "timestamp": "2026-09-01T11:00:00",
                "last_score": 70,
                "next_review": _utc_z_to_naive_local(_DUE_B),
                "review_count": 2,
                "group_id": gid,
            },
            {
                "id": "learned-3",
                "user_id": uid,
                "concept_id": "c-c",
                "concept_name": "concept-c",
                "timestamp": "2026-09-01T12:00:00",
                "last_score": 60,
                "next_review": "2026-09-02T12:00:00",
                "review_count": 1,
                "group_id": gid,
            },
            {
                "id": "learned-4",
                "user_id": uid,
                "concept_id": "c-d",
                "concept_name": "concept-d",
                "timestamp": "2026-09-01T13:00:00",
                "last_score": 50,
                "next_review": "2026-09-02T13:00:00",
                "review_count": 1,
                "group_id": gid,
            },
        ],
        "metadata": {"created_at": "2026-09-01T00:00:00", "version": "2.0"},
    }


@pytest.fixture
def scene(tmp_path):
    """三段 fixture: 3 个 ``.md`` (governed 不等 / governed 相等 / ungoverned)
    + 1 条**只在 JSON 里有**的 ``concept-d`` 边 (unmatched)。"""
    vault = tmp_path / "vault"
    _write_vault_config(vault, "g38fix")
    _write_node(vault, "concept-a", _DUE_A)  # governed, 与目标不等 → set
    _write_node(vault, "concept-b", _DUE_B)  # governed, 与目标相等 → noop
    _write_node(vault, "concept-c", None)  # 无 fsrs_due       → ungoverned
    gid = "vault__g38fix"
    uid = "user-g38"
    json_file = tmp_path / "mirror.json"
    json_file.write_text(
        json.dumps(_mirror_payload(gid, uid), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    return SimpleNamespace(
        tmp=tmp_path,
        vault=vault,
        json_file=json_file,
        gid=gid,
        uid=uid,
        out=out_dir / "report.json",
        backup_dir=tmp_path / "backups",
    )


def _dry_run_argv(sc) -> list:
    return [
        "--dry-run",
        "--vault-dir",
        str(sc.vault),
        "--group-id",
        sc.gid,
        "--json-file",
        str(sc.json_file),
        "--out",
        str(sc.out),
    ]


def _apply_argv(sc, out: Optional[Path] = None) -> list:
    return [
        "--apply",
        "--vault-dir",
        str(sc.vault),
        "--group-id",
        sc.gid,
        "--json-file",
        str(sc.json_file),
        "--backup-dir",
        str(sc.backup_dir),
        "--out",
        str(out or sc.out),
    ]


def _rel(payload: Dict[str, Any], name: str) -> Dict[str, Any]:
    return next(r for r in payload["relationships"] if r["concept_name"] == name)


# ═══════════════════════════════════════════════════════════════════════════
# 段 ① dry-run
# ═══════════════════════════════════════════════════════════════════════════
class TestDryRun:
    def test_dry_run_writes_only_the_report(self, scene):
        """``--out`` 之外零写入 —— 跑前/跑后整棵 tmp 树的 sha256 映射逐键比。

        判据是**映射相等**而不是「文件数没变」: 等数量的原地改写 (改了内容不改
        个数) 在计数判据下看不出来。
        """
        m = _migrator()
        before = _tree_sha(scene.tmp)
        rc = m.main(_dry_run_argv(scene))
        assert rc == 0, "dry-run 应成功"
        after = _tree_sha(scene.tmp)
        report_key = str(scene.out.relative_to(scene.tmp))
        assert report_key in after, "报告没写出来 —— 判据本身失效"
        expected = dict(before)
        expected[report_key] = after[report_key]
        assert after == expected, f"dry-run 动了 --out 之外的文件: {set(after) ^ set(before)}"

    def test_dry_run_counts_are_exact(self, scene):
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        assert rep["counts"] == {
            "rows_without_target": 0,
            "governed": 2,
            "ungoverned": 1,
            "matched": 2,
            "unmatched": 1,
            "unmatched_no_target": 0,
            "unmatched_no_frontmatter": 1,
            "noop": 1,
            "set": 1,
            "backfill": 0,
            "ambiguous": 0,
            "malformed_fsrs_due": 0,
        }

    def test_dry_run_row_actions_are_exact(self, scene):
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        by_key = {r["concept_key"]: r for r in rep["rows"]}
        assert by_key["concept-a"]["action"] == "set"
        assert by_key["concept-a"]["frontmatter_fsrs_due"] == _DUE_A
        assert by_key["concept-a"]["new_next_review"] == _DUE_A
        assert by_key["concept-b"]["action"] == "noop"
        assert by_key["concept-c"]["action"] == "ungoverned"
        assert by_key["concept-c"]["new_next_review"] is None
        assert by_key["concept-d"]["action"] == "unmatched"
        assert by_key["concept-d"]["unmatched_kind"] == "no_frontmatter"

    def test_dry_run_records_input_hashes(self, scene):
        """报告要能自证它读的是哪几份输入 (卡文 (d) ``inputs_sha256``)。"""
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        hashes = rep["inputs_sha256"]
        assert hashes["__json_file__"] == _sha(scene.json_file)
        assert hashes["节点/concept-a.md"] == _sha(scene.vault / "节点" / "concept-a.md")
        assert len([k for k in hashes if k.endswith(".md")]) == 3


# ═══════════════════════════════════════════════════════════════════════════
# 段 ② apply
# ═══════════════════════════════════════════════════════════════════════════
class TestApply:
    def test_apply_sets_target_to_frontmatter_fsrs_due(self, scene):
        """``set`` 行写成 frontmatter 的 ``fsrs_due`` **逐字节同串**; 其余行不动。"""
        m = _migrator()
        before_payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
        before_sha = _sha(scene.json_file)

        rc = m.main(_apply_argv(scene))
        assert rc == 0, "apply 应成功"

        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
        assert _rel(after, "concept-a")["next_review"] == _DUE_A
        assert _rel(after, "concept-b")["next_review"] == _rel(before_payload, "concept-b")["next_review"]
        assert _rel(after, "concept-c")["next_review"] == _rel(before_payload, "concept-c")["next_review"]
        assert _rel(after, "concept-d")["next_review"] == _rel(before_payload, "concept-d")["next_review"]

        simple_bak = scene.json_file.with_suffix(".json.bak")
        assert simple_bak.is_file(), "简单备份缺席"
        assert _sha(simple_bak) == before_sha, "备份不是改前那一份"

    def test_apply_leaves_frontmatter_untouched(self, scene):
        """迁移器**永不写 frontmatter** (D0 T1: 它才是真相源)。"""
        m = _migrator()
        fm_before = _tree_sha(scene.vault)
        assert m.main(_apply_argv(scene)) == 0
        assert _tree_sha(scene.vault) == fm_before, "apply 改了 frontmatter —— 越界"

    def test_apply_is_idempotent(self, scene):
        """第二次 apply 的 ``set + backfill`` 必须为 0。"""
        m = _migrator()
        assert m.main(_apply_argv(scene)) == 0
        second = scene.tmp / "out" / "report2.json"
        assert m.main(_apply_argv(scene, out=second)) == 0
        rep2 = json.loads(second.read_text(encoding="utf-8"))
        assert rep2["counts"]["set"] + rep2["counts"]["backfill"] == 0, "第二次 apply 又写了 —— 非幂等"
        assert rep2["counts"]["noop"] == 2, "两条 governed 行都应归 noop"

    def test_apply_backfills_missing_next_review(self, scene):
        """目标缺 ``next_review`` ⇒ ``backfill`` 而不是 ``unmatched``。"""
        m = _migrator()
        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
        _rel(payload, "concept-a").pop("next_review")
        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        assert m.main(_apply_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        assert rep["counts"]["backfill"] == 1
        assert rep["counts"]["set"] == 0
        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
        assert _rel(after, "concept-a")["next_review"] == _DUE_A

    def test_apply_requires_backup_dir(self, scene):
        """没有备份目录就不许开写 —— 没有有效 pre-image 就不该动目标。"""
        m = _migrator()
        before = _sha(scene.json_file)
        rc = m.main(
            [
                "--apply",
                "--vault-dir",
                str(scene.vault),
                "--group-id",
                scene.gid,
                "--json-file",
                str(scene.json_file),
                "--out",
                str(scene.out),
            ]
        )
        assert rc == 2, "缺 --backup-dir 必须 rc=2"
        assert _sha(scene.json_file) == before, "被拒的 apply 仍改了目标"

    def test_dry_run_preview_equals_apply_outcome(self, scene):
        """预览 = 实际（g35 :496 同口径）。

        g35 当年的缺陷是**两种模式对同一个参数做了不同的归一化**（apply strip 了
        空白、dry-run 没有）——于是预览说要写 A 桶、实际写进了 B 桶，而两边各自
        都"成功"。本迁移器对 ``--group-id`` **零归一化**（形态不合直接 rc=2），
        这条门把该性质钉死：dry-run 报告里的桶名、要写的行，必须与 apply 实际
        落地的逐条一致。
        """
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        preview = json.loads(scene.out.read_text(encoding="utf-8"))
        planned = sorted(
            (r["concept_key"], r["new_next_review"]) for r in preview["rows"] if r["action"] in ("set", "backfill")
        )
        assert planned, "预览里一条要写的行都没有 —— 本门会空洞地通过"

        applied_out = scene.tmp / "out" / "applied.json"
        assert m.main(_apply_argv(scene, out=applied_out)) == 0
        applied = json.loads(applied_out.read_text(encoding="utf-8"))
        assert applied["group_id"] == preview["group_id"], "两种模式认定的桶不同"

        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
        for key, expected in planned:
            assert _rel(after, key)["next_review"] == expected, f"{key} 实际落地值与预览不符"
        assert applied["written"] == len(planned), "实写行数与预览不符"

    @pytest.mark.parametrize("gid", [" vault__g38fix", "vault__g38fix ", "vault__g38fix\n"])
    def test_group_id_is_never_silently_normalized(self, scene, gid):
        """带空白的组 id **不做静默 strip** —— 归一化本身就是两种模式分道的来源。"""
        m = _migrator()
        before = _sha(scene.json_file)
        argv = _dry_run_argv(scene)
        argv[argv.index("--group-id") + 1] = gid
        assert m.main(argv) == 2, f"未被拦下的输入: {gid!r}"
        assert _sha(scene.json_file) == before

    def test_apply_group_id_must_match_dry_run_report(self, scene, capsys):
        """``--apply`` 与 ``--dry-run`` 必须同 ``--group-id`` (g35 :496 口径)。"""
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        before = _sha(scene.json_file)
        # ⚠️ 换的组必须**仍然通过 vault 绑定闸**（同 vault 的二级作用域），
        # 否则这条门会绿在更早那道判据上、证明不了 --from-report 真的生效。
        argv = _apply_argv(scene, out=scene.tmp / "out" / "r3.json")
        argv[argv.index("--group-id") + 1] = "vault__g38fix__otherboard"
        argv += ["--group-scope", "otherboard", "--from-report", str(scene.out)]
        rc = m.main(argv)
        assert rc == 2, "与 dry-run 报告不同组的 apply 必须被拒"
        err = capsys.readouterr().err
        assert "--from-report" in err, f"拒绝的不是 --from-report 那道门, 实得: {err[-300:]}"
        assert _sha(scene.json_file) == before


# ═══════════════════════════════════════════════════════════════════════════
# 段 ③ rollback
# ═══════════════════════════════════════════════════════════════════════════
class TestRollback:
    def test_rollback_restores_target_bytes(self, scene):
        m = _migrator()
        before = _sha(scene.json_file)
        assert m.main(_apply_argv(scene)) == 0
        assert _sha(scene.json_file) != before, "apply 没改动目标 —— 回滚判据会空洞地通过"

        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        preimage = Path(rep["preimage_path"])
        assert preimage.is_file()

        rc = m.main(
            [
                "--rollback",
                str(preimage),
                "--group-id",
                scene.gid,
                "--json-file",
                str(scene.json_file),
            ]
        )
        assert rc == 0, "回滚应成功"
        assert _sha(scene.json_file) == before, "回滚后目标不是改前那一份"

    def test_rollback_refuses_tampered_backup(self, scene):
        """备份自身与 pre-image 记录的 sha 对不上 ⇒ 拒绝回滚, 目标保持现状。"""
        m = _migrator()
        assert m.main(_apply_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        preimage = Path(rep["preimage_path"])
        applied_sha = _sha(scene.json_file)

        bak = Path(json.loads(preimage.read_text(encoding="utf-8"))["backups"]["stamped"])
        bak.write_text('{"users": [], "concepts": [], "relationships": []}', encoding="utf-8")

        rc = m.main(
            [
                "--rollback",
                str(preimage),
                "--group-id",
                scene.gid,
                "--json-file",
                str(scene.json_file),
            ]
        )
        assert rc == 1, "备份被改动过仍回滚 = 拿不可信的数据覆盖目标"
        assert _sha(scene.json_file) == applied_sha, "被拒的回滚仍动了目标"


# ═══════════════════════════════════════════════════════════════════════════
# 闸用例
# ═══════════════════════════════════════════════════════════════════════════
class TestGuards:
    def test_guard_refuses_target_inside_live_vault(self, scene, tmp_path, monkeypatch):
        """落在 live vault 子树内的写目标一律拒。

        ⚠️ 用 tmp 下的**替身** live vault 而不是真路径 (g35 Codex r2 H5 同款):
        闸一旦回归成放行, 这条门自己就会往现网 vault 里写东西 —— 缺陷显形时
        测试本身违反「禁写 live vault」。真常量的正确性由
        :meth:`TestBoundaries.test_script_pins_live_path_literals` 单独锁。
        """
        m = _migrator()
        stand_in_vault = tmp_path / "standin-vault"
        (stand_in_vault / "节点").mkdir(parents=True)
        monkeypatch.setattr(m, "LIVE_VAULT_DIR", stand_in_vault)
        target = stand_in_vault / "节点" / "mirror.json"
        target.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid)), encoding="utf-8")
        before = _sha(target)

        argv = _apply_argv(scene)
        argv[argv.index("--json-file") + 1] = str(target)
        rc = m.main(argv)

        assert rc == 2, "落在 live vault 内的目标必须 rc=2"
        assert _sha(target) == before, "被拒的目标仍被改写"
        assert not target.with_suffix(".json.bak").exists(), "闸拒之后仍产生了 .bak"

    def test_guard_refuses_hardlink_to_protected_file(self, scene, tmp_path, monkeypatch):
        """硬链接 = 同 inode 不同路径 —— 纯路径比对放行它, 身份判据必须认得出。"""
        m = _migrator()
        protected = tmp_path / "standin-mirror.json"
        protected.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid)), encoding="utf-8")
        monkeypatch.setattr(m, "LIVE_JSON_MIRROR", protected)
        alias = tmp_path / "innocent-looking.json"
        os.link(protected, alias)
        before = _sha(protected)

        argv = _apply_argv(scene)
        argv[argv.index("--json-file") + 1] = str(alias)
        rc = m.main(argv)

        assert rc == 2, "指向受保护 inode 的硬链接必须 rc=2"
        assert _sha(protected) == before

    @pytest.mark.parametrize(
        "uri",
        [
            "bolt://localhost:7691",
            "bolt://localhost:07691",
            "bolt://127.0.0.1:7687",
            "bolt://localhost",
            "http://localhost:7692",
        ],
    )
    def test_guard_refuses_live_db_uri(self, uri):
        """现网库闸: 按**解析后的端口**判, 不是子串匹配。

        ``:07691`` 与 ``:7691`` 是同一个端口的两种写法, 子串判据只拦得住后者;
        省略端口的 URI 会被驱动路由到 7687 (本机现网开发端口) ⇒ 同样拒;
        非 bolt/neo4j scheme 无法判定去向 ⇒ fail-closed 拒。
        """
        m = _migrator()
        refusal = m.assert_target_is_not_live(uri=uri)
        assert refusal is not None, f"未被拦下的输入: {uri}"
        if uri.endswith(("7691", "07691")):
            assert "7691" in refusal, "拒绝文案未给出解析后的端口, 无法自证不是子串判据"

    @pytest.mark.parametrize("uri", ["bolt://127.0.0.1:7692", "neo4j://127.0.0.1:7692", "bolt+s://db.example:7692"])
    def test_guard_allows_non_live_db_uri(self, uri):
        """对照输入: 合法 scheme + 非现网端口必须放行 —— 否则闸是恒拒的哑闸。"""
        m = _migrator()
        assert m.assert_target_is_not_live(uri=uri) is None, f"对照输入被误拒: {uri}"

    @pytest.mark.parametrize("gid", ["vault:cs_61b", "cs188", "vault__", "", "vault__a:b"])
    def test_guard_refuses_bad_group_id(self, scene, gid):
        """``--group-id`` 必须是**物理格式** ``vault__<id>``; 冒号格式一律拒。

        组 id 本卡不自造拼接 (G4-5 P1 地盘), 只做形态校验 —— 传错组是跨 vault
        写的唯一入口。
        """
        m = _migrator()
        before = _sha(scene.json_file)
        argv = _dry_run_argv(scene)
        argv[argv.index("--group-id") + 1] = gid
        assert m.main(argv) == 2, f"未被拦下的输入: {gid!r}"
        assert _sha(scene.json_file) == before

    def test_guard_refuses_out_aliasing_preimage(self, scene, monkeypatch):
        """``--out`` 与 pre-image 同位置 ⇒ 报告会覆盖回滚依据, 拒。

        报告在 apply 末尾才写, 时序上排在 pre-image 落盘**之后** —— 别名不拦住
        的话, 一次成功的 apply 结束时回滚依据已经被统计报告顶掉了。
        时间戳定死才能让两个路径真的相撞 (否则撞不上 = 判据空洞)。
        """
        m = _migrator()
        monkeypatch.setattr(m, "_now_stamp", lambda: "20260919_000000")
        collide = scene.backup_dir / "preimage-20260919_000000.json"
        before = _sha(scene.json_file)
        argv = _apply_argv(scene)
        argv[argv.index("--out") + 1] = str(collide)
        rc = m.main(argv)
        assert rc == 1, "别名的 pre-image 路径必须在开写前被拒 (rc=1 未写入)"
        assert _sha(scene.json_file) == before, "被拒的 apply 仍改了目标"

    def test_guard_refuses_out_aliasing_target(self, scene):
        """``--out`` 与 ``--json-file`` 同一个文件 ⇒ 报告会覆盖输入, 拒。"""
        m = _migrator()
        before = _sha(scene.json_file)
        argv = _dry_run_argv(scene)
        argv[argv.index("--out") + 1] = str(scene.json_file)
        assert m.main(argv) == 2
        assert _sha(scene.json_file) == before, "输入快照被报告覆盖 —— dry-run 非零写入"


# ═══════════════════════════════════════════════════════════════════════════
# 只读边界 / 结构门
# ═══════════════════════════════════════════════════════════════════════════
_ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "__future__",
        "argparse",
        "datetime",
        "hashlib",
        "json",
        "os",
        "pathlib",
        "re",
        "shutil",
        "sys",
        "typing",
        "urllib",
        "neo4j",  # 只在给了 --neo4j-uri 时函数内延迟 import
    }
)

_REQUIRED_FUNCTIONS = frozenset(
    {
        "assert_target_is_not_live",
        "run_dry_run",
        "run_apply",
        "run_rollback",
        "build_parser",
        "main",
    }
)


class TestBoundaries:
    def test_script_imports_only_stdlib_allowlist(self):
        """AST 级只读边界自证 —— 比逐字 grep 强: 连「没人想到的那个库」也拦得住。"""
        import ast

        roots = set()
        for node in ast.walk(ast.parse(_script_source())):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
        assert roots <= _ALLOWED_IMPORT_ROOTS, f"脚本导入了允许清单外的模块: {sorted(roots - _ALLOWED_IMPORT_ROOTS)}"

    def test_script_has_no_app_imports(self):
        """⛔ 零 ``app`` 导入 —— 迁移器必须能在没有后端环境的机器上跑。"""
        import ast

        offenders = []
        for node in ast.walk(ast.parse(_script_source())):
            if isinstance(node, ast.Import):
                offenders += [a.name for a in node.names if a.name.split(".")[0] == "app"]
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "app":
                offenders.append(node.module)
        assert offenders == [], f"脚本导入了 app: {offenders}"

    def test_script_defines_required_functions(self):
        """AST 函数名集合 ⊇ 必备集 —— 切片改代码静默删掉整个函数时这里会红。"""
        import ast

        names = {n.name for n in ast.walk(ast.parse(_script_source())) if isinstance(n, ast.FunctionDef)}
        assert _REQUIRED_FUNCTIONS <= names, f"缺函数: {sorted(_REQUIRED_FUNCTIONS - names)}"

    def test_script_pins_live_path_literals(self):
        """闸常量必须钉在**真**现网路径上 (闸用例用的是 tmp 替身, 锁不住这一点)。"""
        m = _migrator()
        assert str(m.LIVE_VAULT_DIR) == _LIVE_VAULT_DIR
        assert str(m.LIVE_JSON_MIRROR) == _LIVE_JSON_MIRROR
        assert str(m.LIVE_CARD_STATES) == _LIVE_CARD_STATES
        assert set(m.LIVE_DB_PORTS) == {7691, 7687}


# ═══════════════════════════════════════════════════════════════════════════
# 语义门: naive 解释 / 显形 / 反向回填
# ═══════════════════════════════════════════════════════════════════════════
class TestSemantics:
    def test_naive_json_value_is_interpreted_as_local_and_flagged(self, scene):
        """JSON 镜像的 naive 值按**本地**解释, 且逐行打标 —— 解释口径永不隐形。"""
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        assert rep["naive_interpretation"] == "local"
        by_key = {r["concept_key"]: r for r in rep["rows"]}
        assert by_key["concept-b"]["target_naive"] is True
        assert by_key["concept-b"]["action"] == "noop", "同一时刻的 naive 本地值应判 noop"

    def test_naive_utc_interpretation_changes_the_verdict(self, scene):
        """换成 ``--json-naive-tz utc`` 结论必须改变 —— 证明这个开关真的接上了。"""
        if datetime.now().astimezone().utcoffset().total_seconds() == 0:
            pytest.skip("本机 UTC 偏移为 0, local/utc 两种解释不可区分")
        m = _migrator()
        argv = _dry_run_argv(scene) + ["--json-naive-tz", "utc"]
        assert m.main(argv) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        by_key = {r["concept_key"]: r for r in rep["rows"]}
        assert by_key["concept-b"]["action"] == "set", "utc 解释下同一个值应判为分歧"

    def test_report_warns_about_json_mirror_aware_reader(self, scene):
        """写 UTC-Z 进 JSON 镜像有**已知下游后果**, 报告必须自己说出来。

        ``neo4j_client.py:806-808`` 拿 naive 的 ``datetime.now()`` 与读出的值比
        大小; 值是 tz-aware 时抛 ``TypeError``, 被 ``:833`` 的
        ``except (ValueError, TypeError): continue`` **静默跳过** —— 该 concept
        会从 JSON 降级路径的复习建议里消失。本卡不能改 ``neo4j_client.py``
        (P1/P2 地盘), 所以把后果显形在报告里, 而不是静默制造回归。
        """
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        codes = [w["code"] for w in rep["warnings"]]
        assert "W-JSON-MIRROR-AWARE-READER" in codes, "已知下游后果没有显形"

    def test_unmatched_no_target_is_surfaced(self, scene):
        """governed 却在目标侧找不到边 ⇒ ``unmatched``, ⛔ 不静默跳过。"""
        m = _migrator()
        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
        payload["relationships"] = [r for r in payload["relationships"] if r["concept_name"] != "concept-a"]
        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        by_key = {r["concept_key"]: r for r in rep["rows"]}
        assert by_key["concept-a"]["action"] == "unmatched"
        assert by_key["concept-a"]["unmatched_kind"] == "no_target"
        assert rep["counts"]["unmatched_no_target"] == 1

    def test_ungoverned_never_backfills_frontmatter(self, scene):
        """``ungoverned`` 行既不动目标, 也**不反向回填** frontmatter (默认不做)。"""
        m = _migrator()
        node_c = scene.vault / "节点" / "concept-c.md"
        before_fm = _sha(node_c)
        before_target = json.loads(scene.json_file.read_text(encoding="utf-8"))
        assert m.main(_apply_argv(scene)) == 0
        assert _sha(node_c) == before_fm, "ungoverned 节点的 frontmatter 被写了"
        after_target = json.loads(scene.json_file.read_text(encoding="utf-8"))
        assert _rel(after_target, "concept-c")["next_review"] == _rel(before_target, "concept-c")["next_review"]

    def test_shadowed_node_files_are_surfaced(self, scene):
        """同 stem 同时出现在 ``节点/`` 与 ``原白板/`` ⇒ 取 ``节点/``, 但必须显形。"""
        m = _migrator()
        _write_node(scene.vault, "concept-a", "2027-01-01T00:00:00Z", sub="原白板")
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        assert any("原白板/concept-a.md" in s["shadowed_path"] for s in rep["shadowed"])
        by_key = {r["concept_key"]: r for r in rep["rows"]}
        assert by_key["concept-a"]["frontmatter_fsrs_due"] == _DUE_A, "应取 节点/ 那份 (与 _node_md_path 同序)"

    def test_duplicate_triples_are_written_positionally(self, scene):
        """重复的 ``(user_id, concept_name, group_id)`` 三元组必须**逐行**处置。

        旧数据里可能并存重复行: 写方 ``neo4j_client.py:721-726`` 用 ``next(...)``
        只更新第一条, 于是第二条长期停在旧值。若迁移器按三元组建索引, 两条会塌成
        一条 —— 判 ``noop`` 的那条被连带写入, 而报告里没有它 (一次门未覆盖的写)。
        判据: 与 frontmatter 同刻的那条**逐字节不变**, 不同刻的那条被改写。
        """
        m = _migrator()
        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
        dup = dict(_rel(payload, "concept-a"))
        dup["id"] = "learned-1-dup"
        dup["next_review"] = _utc_z_to_naive_local(_DUE_A)  # 与真相源同刻 ⇒ noop
        payload["relationships"].append(dup)
        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        assert m.main(_apply_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        assert rep["counts"]["set"] == 1, "重复行被塌成一条 —— set 计数失真"
        assert rep["counts"]["noop"] == 2, "同刻的重复行应判 noop"

        after = json.loads(scene.json_file.read_text(encoding="utf-8"))
        rows = [r for r in after["relationships"] if r["concept_name"] == "concept-a"]
        assert len(rows) == 2
        assert rows[0]["next_review"] == _DUE_A, "应写的那条没写成 fsrs_due"
        assert rows[1]["next_review"] == dup["next_review"], "判 noop 的重复行被连带写入了"


# ═══════════════════════════════════════════════════════════════════════════
# Codex round-1 整改的行为门
# ═══════════════════════════════════════════════════════════════════════════
class TestVaultGroupBinding:
    """BLOCKER-1: 形态合法的**错误**组能把 A vault 的 due 写进 B。"""

    def test_group_from_another_vault_is_refused(self, scene, capsys):
        """`--vault-dir A --group-id vault__B` —— 两个参数各自合法, 合起来是跨 vault 写。"""
        m = _migrator()
        before = _sha(scene.json_file)
        argv = _dry_run_argv(scene)
        argv[argv.index("--group-id") + 1] = "vault__someothervault"
        assert m.main(argv) == 2, "未被拦下的输入: 属于别的 vault 的组名"
        err = capsys.readouterr().err
        assert "vault_id" in err, f"拒绝的不是 vault 绑定那道门: {err[-300:]}"
        assert _sha(scene.json_file) == before

    def test_vault_subscope_requires_explicit_scope(self, scene, capsys):
        """二级作用域必须**显式声明**, 不能靠前缀推断 (Codex r2 BLOCKER-1)。

        `vault__alpha__beta` 既像 vault `alpha` 的 `beta` 板, 也像 vault
        `alpha__beta` 的根组 —— 单看字符串分不开。所以默认逐字相等, 要写二级
        作用域就得说出"我要写哪一层"。
        """
        m = _migrator()
        argv = _dry_run_argv(scene)
        argv[argv.index("--group-id") + 1] = "vault__g38fix__someboard"
        assert m.main(argv) == 2, "未被拦下的输入: 靠前缀推断的二级作用域"
        assert "逐字等于" in capsys.readouterr().err

    def test_vault_subscope_with_explicit_scope_is_allowed(self, scene):
        """对照输入: 说清楚是哪一层就放行, 否则闸恒拒 = 哑闸。"""
        m = _migrator()
        argv = _dry_run_argv(scene) + ["--group-scope", "someboard"]
        argv[argv.index("--group-id") + 1] = "vault__g38fix__someboard"
        assert m.main(argv) == 0, "显式声明的二级作用域被误拒 —— 闸过严"

    def test_another_vault_rooted_at_a_subscope_name_is_refused(self, scene, capsys):
        """r2 BLOCKER-1 的那条路径: vault B 的**根组**恰好长得像 vault A 的二级组。

        vault A 自报 `g38fix`, vault B 自报 `g38fix__beta`。拿着 A 的目录 +
        `--group-id vault__g38fix__beta`（= B 的根组名）, 前缀放行的写法会把它
        当成"A 的 beta 板"接受 —— 逃生门一次都不用开, A 的 due 就落进了 B。
        """
        m = _migrator()
        before = _sha(scene.json_file)
        argv = _dry_run_argv(scene)
        argv[argv.index("--group-id") + 1] = "vault__g38fix__beta"
        assert m.main(argv) == 2, "未被拦下的输入: 另一个 vault 的根组名"
        assert _sha(scene.json_file) == before

    def test_vault_id_containing_the_separator_fails_closed(self, scene, capsys):
        """vault 自报的 id 内嵌 `__` ⇒ 与二级分隔符撞车 ⇒ 算不出确定组名 ⇒ 拒。"""
        m = _migrator()
        _write_vault_config(scene.vault, "alpha__beta")
        assert m.main(_dry_run_argv(scene)) == 2
        assert "算不出确定的物理组名" in capsys.readouterr().err

    # ⚠️ 不用 "-bad": argparse 会把前导 `-` 当成选项名, 抛 SystemExit 而不是走到
    # 形态判据 —— 那条用例会绿/红在更早的一层上, 证明不了本门。
    @pytest.mark.parametrize("scope", ["a__b", "_bad", "", "有中文"])
    def test_group_scope_shape_is_enforced(self, scene, scope):
        """`--group-scope` 自己也不得内嵌 `__`, 否则同一个歧义在下一层复发。"""
        m = _migrator()
        argv = _dry_run_argv(scene) + ["--group-scope", scope]
        argv[argv.index("--group-id") + 1] = f"vault__g38fix__{scope}"
        assert m.main(argv) == 2, f"未被拦下的输入: --group-scope {scope!r}"

    def test_vault_without_config_fails_closed(self, scene, capsys):
        """vault 说不出自己是谁 ⇒ 拿不准配对 ⇒ 拒, 而不是默认"应该没事"。"""
        m = _migrator()
        (scene.vault / ".canvas-config.yaml").unlink()
        assert m.main(_dry_run_argv(scene)) == 2
        assert "无法确认" in capsys.readouterr().err

    def test_allow_unbound_vault_is_an_explicit_escape(self, scene):
        """逃生门必须是**显式**的 —— 默认 fail-closed, 加了才放行。"""
        m = _migrator()
        (scene.vault / ".canvas-config.yaml").unlink()
        assert m.main(_dry_run_argv(scene) + ["--allow-unbound-vault"]) == 0

    def test_non_ascii_vault_id_is_not_silently_vouched_for(self, scene, capsys):
        """算不出物理组名就不能假装验过 (物理化含 punycode, 属 app 侧能力)。"""
        m = _migrator()
        _write_vault_config(scene.vault, "数学101")
        assert m.main(_dry_run_argv(scene)) == 2
        assert "算不出" in capsys.readouterr().err


class TestWritePathSafety:
    """HIGH-2: 输出口此前没有保护**全部**只读输入。"""

    def test_out_inside_vault_is_refused(self, scene, capsys):
        """`--out <vault>/节点/A.md` 会把报告覆盖到源节点上 —— frontmatter 是真相源。"""
        m = _migrator()
        node = scene.vault / "节点" / "concept-a.md"
        before = _sha(node)
        argv = _dry_run_argv(scene)
        argv[argv.index("--out") + 1] = str(node)
        assert m.main(argv) == 2, "未被拦下的输入: --out 指向源节点"
        assert "--vault-dir" in capsys.readouterr().err
        assert _sha(node) == before, "源节点被报告覆盖了"

    def test_out_anywhere_in_vault_subtree_is_refused(self, scene):
        """判据覆盖整棵 `--vault-dir` 子树, 而不是只覆盖扫到的那几个 `.md`。"""
        m = _migrator()
        argv = _dry_run_argv(scene)
        argv[argv.index("--out") + 1] = str(scene.vault / "没被扫到的子目录" / "r.json")
        assert m.main(argv) == 2

    def test_backup_symlinked_into_vault_is_refused(self, scene):
        """备份也是**写入路径**: `.bak` 若是指向源节点的符号链接, 复制就覆盖了它。"""
        m = _migrator()
        node = scene.vault / "节点" / "concept-a.md"
        before = _sha(node)
        scene.json_file.with_suffix(".json.bak").symlink_to(node)
        assert m.main(_apply_argv(scene)) == 2
        assert _sha(node) == before, "源节点被备份复制覆盖了"

    def test_backup_dir_in_live_vault_creates_no_directory(self, scene, tmp_path, monkeypatch):
        """MEDIUM-9: 闸必须排在 mkdir **前面**, 否则已经在 live vault 里落了目录。"""
        m = _migrator()
        stand_in = tmp_path / "standin-live-vault"
        stand_in.mkdir()
        monkeypatch.setattr(m, "LIVE_VAULT_DIR", stand_in)
        target_dir = stand_in / "g38-backups"
        argv = _apply_argv(scene)
        argv[argv.index("--backup-dir") + 1] = str(target_dir)
        rc = m.main(argv)
        assert rc == 1, f"落在 live vault 的 --backup-dir 必须在开写前被拒, 实得 rc={rc}"
        assert not target_dir.exists(), "闸拒之后目录仍被建出来了"

    def test_plain_multi_hardlink_file_is_refused_on_its_own(self, scene, tmp_path, monkeypatch):
        """MEDIUM-11: 让受保护 inode 判据够不着, 单独证明 `st_nlink > 1` 那一条。"""
        m = _migrator()
        monkeypatch.setattr(m, "LIVE_JSON_MIRROR", tmp_path / "nonexistent-mirror.json")
        monkeypatch.setattr(m, "LIVE_CARD_STATES", tmp_path / "nonexistent-states.json")
        monkeypatch.setattr(m, "LIVE_VAULT_DIR", tmp_path / "nonexistent-vault")
        innocent = tmp_path / "plain.json"
        innocent.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid)), encoding="utf-8")
        os.link(innocent, tmp_path / "second-name.json")

        refusal = m.assert_target_is_not_live(target=innocent, what="测试目标")
        assert refusal is not None, "未被拦下的输入: 普通多硬链接文件"
        assert "硬链接数" in refusal, f"拒绝的不是多名字那条判据: {refusal}"


class TestRollbackBinding:
    """HIGH-4: pre-image 必须绑回它自己那个目标。"""

    def test_rollback_to_a_different_file_is_refused(self, scene, tmp_path, capsys):
        m = _migrator()
        assert m.main(_apply_argv(scene)) == 0
        preimage = Path(json.loads(scene.out.read_text(encoding="utf-8"))["preimage_path"])

        other = tmp_path / "another-mirror.json"
        other.write_text(json.dumps(_mirror_payload(scene.gid, scene.uid), ensure_ascii=False), encoding="utf-8")
        before_other = _sha(other)

        rc = m.main(["--rollback", str(preimage), "--group-id", scene.gid, "--json-file", str(other)])
        assert rc == 2, "未被拦下的输入: 把一份备份还原到别的文件上"
        assert "pre-image 记录的目标" in capsys.readouterr().err
        assert _sha(other) == before_other, "被拒的回滚仍覆盖了别的文件"


def _force_la_timezone(monkeypatch, scene) -> None:
    """切到洛杉矶时区, 并**在切换之后**重建 fixture 里依赖本地时区的那个值。

    ⚠️ Codex r2 LOW-10: fixture 是在**进程启动时区**下造 `concept-b` 的 naive
    本地串的; 用例随后切到洛杉矶再断言 `noop/set` 计数 —— 本机恰好是 PDT 所以
    碰巧绿, 换一台 UTC 机器同一条门就红。门的前提条件不能依赖跑它的环境。
    """
    import time

    monkeypatch.setenv("TZ", "America/Los_Angeles")
    time.tzset()
    payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
    _rel(payload, "concept-b")["next_review"] = _utc_z_to_naive_local(_DUE_B)
    scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class TestDaylightSaving:
    """MEDIUM-8: 夏令时边界上 naive 本地时刻**本身**就不是一个确定的时刻。"""

    @pytest.mark.parametrize(
        ("local_value", "expected_reason"),
        [("2026-11-01T01:30:00", "ambiguous_local_time"), ("2026-03-08T02:30:00", "nonexistent_local_time")],
    )
    def test_dst_boundary_local_values_are_not_silently_normalized(
        self, scene, monkeypatch, local_value, expected_reason
    ):
        _force_la_timezone(monkeypatch, scene)
        m = _migrator()
        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
        _rel(payload, "concept-a")["next_review"] = local_value
        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        row = {r["concept_key"]: r for r in rep["rows"]}["concept-a"]
        assert row["action"] == "ambiguous", "歧义的本地时刻被默默归一成了一个确定时刻"
        assert row["reason"] == expected_reason
        assert rep["counts"]["ambiguous"] == 1
        assert rep["counts"]["set"] == 0, "ambiguous 行不得进写入集合"

    def test_ordinary_local_value_still_compares(self, scene, monkeypatch):
        """对照输入: 非边界日期照常比较, 否则上一条门可能只是"什么都判 ambiguous"。"""
        _force_la_timezone(monkeypatch, scene)
        m = _migrator()
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        assert rep["counts"]["ambiguous"] == 0
        assert rep["counts"]["noop"] == 1 and rep["counts"]["set"] == 1


class TestIdentityMissDimension:
    """MEDIUM-10: due 坏掉的节点也可能同时"在目标侧没有边", 后者不能因此消失。"""

    def test_malformed_node_without_target_still_shows_the_miss(self, scene):
        m = _migrator()
        _write_node(scene.vault, "concept-e", "不是一个合法时间戳")
        assert m.main(_dry_run_argv(scene)) == 0
        rep = json.loads(scene.out.read_text(encoding="utf-8"))
        row = {r["concept_key"]: r for r in rep["rows"]}["concept-e"]
        assert row["action"] == "malformed_fsrs_due"
        assert row["target_missing"] is True, "身份没对上这件事被 malformed 盖掉了"
        assert rep["counts"]["rows_without_target"] == 1


class TestCodexRound2Fixes:
    """round-2 提出的 HIGH/MEDIUM 各自的门。"""

    def test_out_cannot_overwrite_a_node_reached_through_a_symlink(self, scene, tmp_path, capsys):
        """HIGH-4: `vault/节点/A.md` 可以是指向 vault **外**某文件的软链。

        那个文件既不在 `--vault-dir` 子树内, 也不在扫描前的只读输入清单里 ——
        `--out <它>` 能穿过 main 里那道核查, 在报告落盘时覆盖真相源。
        扫完之后才知道真正读了哪些文件, 所以写报告前必须用实测清单再核一次。
        """
        m = _migrator()
        outside = tmp_path / "outside-truth-source.md"
        outside.write_text(f"---\ntitle: concept-a\nfsrs_due: {_DUE_A}\n---\n正文\n", encoding="utf-8")
        node = scene.vault / "节点" / "concept-a.md"
        node.unlink()
        node.symlink_to(outside)
        before = _sha(outside)

        argv = _dry_run_argv(scene)
        argv[argv.index("--out") + 1] = str(outside)
        assert m.main(argv) == 2, "未被拦下的输入: --out 指向软链背后的真相源"
        assert "只读输入" in capsys.readouterr().err
        assert _sha(outside) == before, "软链背后的真相源被报告覆盖了"

    def test_existing_backup_dir_is_accepted(self, scene):
        """MEDIUM-6: 第二次 apply 时备份目录**本来就应该存在**, 不能被拒。

        此前备份目录走了"已存在且不是普通文件就拒"的判据, 于是正常的二次写入
        被拒 —— 幂等负控也因此提前红在 `rc == 0` 而不是它声称的计数断言上。
        """
        m = _migrator()
        scene.backup_dir.mkdir(parents=True)
        (scene.backup_dir / "旧的遗留文件.json").write_text("{}", encoding="utf-8")
        assert m.main(_apply_argv(scene)) == 0, "已存在的备份目录被误拒"

    def test_second_apply_with_writable_rows_still_succeeds(self, scene):
        """同上, 但走的是"第二次仍有可写行"这条真实路径 (负控正是踩这里)。"""
        m = _migrator()
        assert m.main(_apply_argv(scene)) == 0
        payload = json.loads(scene.json_file.read_text(encoding="utf-8"))
        _rel(payload, "concept-b")["next_review"] = "2020-01-01T00:00:00"
        scene.json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        second = scene.tmp / "out" / "second.json"
        assert m.main(_apply_argv(scene, out=second)) == 0, "第二次有可写行时被备份目录闸拒了"
        assert json.loads(second.read_text(encoding="utf-8"))["counts"]["set"] == 1

    def test_out_cannot_alias_the_stamped_backup(self, scene, monkeypatch):
        """MEDIUM-8: 报告在 apply 末尾写, 别名到备份就把回滚依据顶掉了。"""
        m = _migrator()
        monkeypatch.setattr(m, "_now_stamp", lambda: "20260919_010203")
        collide = scene.json_file.with_suffix(".json.bak.20260919_010203")
        before = _sha(scene.json_file)
        argv = _apply_argv(scene)
        argv[argv.index("--out") + 1] = str(collide)
        assert m.main(argv) == 2, "未被拦下的输入: --out 别名到本次备份"
        assert _sha(scene.json_file) == before

    @pytest.mark.parametrize(
        ("a", "b", "same"),
        [
            ("2026-01-01T00:00:00.123456999Z", "2026-01-01T00:00:00.123456001Z", False),
            ("2026-01-01T00:00:00.123456789Z", "2026-01-01T00:00:00.123456789Z", True),
            ("2026-01-01T00:00:00Z", "2026-01-01T00:00:00.000000000Z", True),
        ],
    )
    def test_restore_comparison_does_not_swallow_nanoseconds(self, a, b, same):
        """MEDIUM-7: `fromisoformat` 只收 6 位小数, 截断会把纳秒差异判成相等。

        还原要证明的是"回到原样"; 把纳秒差吞掉就证明不了。
        """
        m = _migrator()
        assert m._same_instant_exact(a, b) is same

    def test_restore_uses_preimage_shaped_rows(self, scene):
        """HIGH-2: 还原函数取 `old_next_review`; 喂它分类行会恒得 None ⇒ 走清空。

        这里直接对 `_restore_neo4j` 的入参形状做断言 —— 真库不可达时这条仍成立,
        因为它锁的是**调用方给了什么形状**, 不是库的行为。
        """
        m = _migrator()
        src = pathlib.Path(m.__file__ if hasattr(m, "__file__") else SCRIPT_PATH).read_text(encoding="utf-8")
        assert "preimage_by_key" in src, "还原集合没有改成 pre-image 形状"
        assert "attempted.append(preimage_by_key[" in src, "还原集合不是按 pre-image 行装的"
        # 下笔前记账: attempted.append 必须排在 session.run 之前
        i_append = src.index("attempted.append(preimage_by_key[")
        i_run = src.index("rec = session.run(", i_append)
        assert i_append < i_run, "记账排在了写入之后 —— 回执失败的那一行会漏出还原集合"


# ═══════════════════════════════════════════════════════════════════════════
# 7692 真库门 (共享容器; 身份一律 g38gate_ 前缀, 清理不得宽于自己的前缀)
# ═══════════════════════════════════════════════════════════════════════════
_NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI", "bolt://127.0.0.1:7692")
_NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER", "neo4j")
_NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD", "testpassword")


def _test_db_reachable(m) -> bool:
    """可达性探针 —— 现网判定**复用被测迁移器自己的闸**(Codex r1 HIGH-6)。

    此前这里是子串判定 (``":7691" in uri``)，而 ``bolt://host:07691`` 与
    ``bolt://host``(驱动默认 7687) 都能从子串判定底下走过去 —— 探针会先连上去
    并在用例体里 ``MERGE/SET``，之后才轮到迁移器那道正确的闸。门自己把现网写了，
    再由被测代码拒绝，已经晚了。
    """
    if m.assert_target_is_not_live(uri=_NEO4J_TEST_URI) is not None:
        return False
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            _NEO4J_TEST_URI,
            auth=(_NEO4J_TEST_USER, _NEO4J_TEST_PASSWORD),
            connection_timeout=3.0,
        )
        try:
            driver.verify_connectivity()
            return True
        finally:
            driver.close()
    except Exception:  # noqa: BLE001 — 任何失败都视为不可达
        return False


class TestRealNeo4jGate:
    def test_g38gate_neo4j_roundtrip(self, scene):
        """真库往返: dry-run ``set=1`` → apply → 读回 = ``fsrs_due`` → 幂等 → 回滚。

        ⚠️ 可达性探针排在 :func:`_migrator` **之后**: 脚本缺席时这条也必须红在
        「尚不存在」而不是 skip (卡文 (b)④)。
        """
        m = _migrator()
        if not _test_db_reachable(m):
            pytest.skip(f"测试容器不可达或未通过现网闸, 跳过真库门: {_NEO4J_TEST_URI}")

        import uuid

        from neo4j import GraphDatabase

        # MEDIUM-9: 身份必须能证明"属于本次运行" —— 固定名字在共享容器里会与
        # 遗留数据 / 并行跑的另一份自己撞上, 然后被本用例改写并删除。
        run_tag = f"g38gate_{uuid.uuid4().hex}"
        uid = f"{run_tag}_user"
        cname = f"{run_tag}_concept"
        gid = "vault__g38gate"
        vault = scene.tmp / "gatevault"
        _write_vault_config(vault, "g38gate")
        _write_node(vault, cname, _DUE_A)
        old_value = "2026-01-01T00:00:00Z"

        driver = GraphDatabase.driver(_NEO4J_TEST_URI, auth=(_NEO4J_TEST_USER, _NEO4J_TEST_PASSWORD))
        try:
            # ⚠️ HIGH-5: **先核库身份, 再下第一笔**。此前探针只验端口与可达性,
            # 用例直接 MERGE/SET, 要等调用迁移器时才轮到身份闸 —— 若 7692 被转发
            # 到现网库, 门自己已经把现网写了, 再拒绝已经晚了。
            store_refusal = m.assert_store_is_not_live(driver, None, False)
            if store_refusal is not None:
                pytest.skip(f"测试库未通过 store identity 闸, 不下笔: {store_refusal}")

            with driver.session() as s:
                s.run(
                    "MERGE (u:User {id: $uid}) "
                    "MERGE (c:Concept {name: $cname, group_id: $gid}) "
                    "MERGE (u)-[r:LEARNED {group_id: $gid}]->(c) "
                    "SET r.next_review = datetime($old)",
                    uid=uid,
                    cname=cname,
                    gid=gid,
                    old=old_value,
                )

            base = [
                "--vault-dir",
                str(vault),
                "--group-id",
                gid,
                "--neo4j-uri",
                _NEO4J_TEST_URI,
                "--neo4j-user",
                _NEO4J_TEST_USER,
                "--neo4j-password",
                _NEO4J_TEST_PASSWORD,
            ]
            out1 = scene.tmp / "out" / "gate-dry.json"
            assert m.main(["--dry-run", *base, "--out", str(out1)]) == 0
            assert json.loads(out1.read_text(encoding="utf-8"))["counts"]["set"] == 1

            out2 = scene.tmp / "out" / "gate-apply.json"
            assert m.main(["--apply", *base, "--backup-dir", str(scene.backup_dir), "--out", str(out2)]) == 0
            with driver.session() as s:
                got = s.run(
                    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept) "
                    "WHERE c.group_id = $gid AND r.group_id = $gid AND c.name = $cname "
                    "RETURN toString(r.next_review) AS nr",
                    uid=uid,
                    gid=gid,
                    cname=cname,
                ).single()
            assert got is not None and got["nr"].startswith("2026-09-20T03:00:00")

            out3 = scene.tmp / "out" / "gate-apply2.json"
            assert m.main(["--apply", *base, "--backup-dir", str(scene.backup_dir), "--out", str(out3)]) == 0
            rep3 = json.loads(out3.read_text(encoding="utf-8"))
            assert rep3["counts"]["set"] + rep3["counts"]["backfill"] == 0

            preimage = json.loads(out2.read_text(encoding="utf-8"))["preimage_path"]
            assert (
                m.main(
                    [
                        "--rollback",
                        preimage,
                        "--group-id",
                        gid,
                        "--neo4j-uri",
                        _NEO4J_TEST_URI,
                        "--neo4j-user",
                        _NEO4J_TEST_USER,
                        "--neo4j-password",
                        _NEO4J_TEST_PASSWORD,
                    ]
                )
                == 0
            )
            with driver.session() as s:
                got = s.run(
                    "MATCH (u:User {id: $uid})-[r:LEARNED]->(c:Concept) "
                    "WHERE c.group_id = $gid AND r.group_id = $gid AND c.name = $cname "
                    "RETURN toString(r.next_review) AS nr",
                    uid=uid,
                    gid=gid,
                    cname=cname,
                ).single()
            assert got is not None and got["nr"].startswith("2026-01-01T00:00:00")
        finally:
            # 清理只删**本次这一条身份**, 不删「前缀匹配的一切」(Codex r1 HIGH-7):
            # 7692 是共享容器, `STARTS WITH 'g38gate_'` 会连同名但**别的组**的
            # Concept 一起删; 而 DETACH DELETE 还会顺手删掉那些节点上挂的全部关系
            # —— 删到的就不只是"自己的前缀"了。
            try:
                with driver.session() as s:
                    s.run(
                        "MATCH (:User {id: $uid})-[r:LEARNED {group_id: $gid}]->(:Concept {name: $cname, group_id: $gid}) "
                        "DELETE r",
                        uid=uid,
                        gid=gid,
                        cname=cname,
                    )
                    s.run(
                        "MATCH (c:Concept {name: $cname, group_id: $gid}) WHERE NOT (c)--() DELETE c",
                        gid=gid,
                        cname=cname,
                    )
                    s.run("MATCH (u:User {id: $uid}) WHERE NOT (u)--() DELETE u", uid=uid)
            finally:
                driver.close()
