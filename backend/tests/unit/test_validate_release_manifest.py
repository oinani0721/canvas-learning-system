# ⚠️ CARD-R-EVD (BATCH-2026-08-28-第五批) — Release 证据 manifest 校验器的裁判
#
# 被测物: backend/scripts/validate_release_manifest.py + docs/release-evidence/manifest.schema.json
# 规范真相源: 计划书 §12.6 L596 (manifest 必含字段) / §12.5 (E0-E5 等级、SLO 锁版、降级规则)
#
# 本文件**完全自足** (只用 stdlib + pytest + jsonschema), 可用
#   python -m pytest backend/tests/unit/test_validate_release_manifest.py --noconftest -q
# 单独跑 —— 与 CARD-G1-5 的 conftest 隔离先例同口径 (backend/tests/unit/conftest.py
# 会拉起整个 app 栈, CI 小型 job 装不起)。
#
# 钉死点:
#   1. 真示例 (D5 回填) 必须 PASS, 且 --verify-artifacts 也 PASS
#   2. 每条语义规则 S1..S13 与产物规则 A0..A3 各有畸形 fixture 打红, 报错含规则编号
#   3. 结构层缺字段/错类型/错枚举/if-then 打红
#   4. schema 指纹: schema 单边改一个字节 = 退出 2 (不是伪绿也不是普通失败)
#   5. 退出码三档严格: 0 通过 / 1 内容不合格 (含 JSON 合法但形状不对) / 2 配置环境错
#   6. 结构层不过时不跑语义层 (防 KeyError 噪声淹没真因)
#   7. Codex round-1 两个 BLOCKER 的**原样复现**必须被挡 (test_codex_round1_*)
#
# ⚠️ 基底诚实声明 (Codex round-1 HIGH "假绿覆盖" 整改): _minimal_manifest() 是**合成
# fixture**, 其 SHA/索引值是占位符, 不代表真实证据。它的作用是给语义规则提供一个
# "结构干净的起点", 好让每条负例只变动一个维度。真实性由 test_repo_example_* 系列
# 对仓内示例件把关, 那份才与磁盘 checksum 逐字比对。

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import validate_release_manifest as vrm  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = REPO_ROOT / "docs" / "release-evidence" / "example-backfill-d5" / "journeys" / "J08" / "manifest.json"
SCHEMA = REPO_ROOT / "docs" / "release-evidence" / "manifest.schema.json"

_ART_BODY = b"artifact-body\n"
_ART_SHA = hashlib.sha256(_ART_BODY).hexdigest()


# ─────────────────────────────────────────────────────────────
# 合成基底 —— 语义 fixture 的共同起点 (见文件头诚实声明)
# ─────────────────────────────────────────────────────────────


def _minimal_manifest() -> dict:
    return {
        "schema_version": "1.0.0",
        "journey_id": "J01",
        "journey_title": "新 vault bootstrap",
        "rc": "rc-test",
        "provenance": {"mode": "live", "unproven_fields": []},
        "candidate": {
            "sha": "1234567890abcdef1234567890abcdef12345678",
            "branch": "main",
            "dirty": False,
        },
        "environment": {
            "host_os": "darwin 25.5.0",
            "runtimes": {"python": "3.14.4"},
            "models": [],
            "index_sha": "idx-placeholder-合成fixture",
        },
        "execution": {
            "started_at": "2026-08-28T10:00:00+08:00",
            "finished_at": "2026-08-28T10:30:00+08:00",
            "operator": "tester",
            "commands": [{"cmd": "echo ok", "cwd": ".", "exit_code": 0}],
            "skips_or_mocks": {"declared": False, "items": []},
        },
        "assertions": [
            {
                "id": "A1",
                "statement": "backend ready",
                "method": "curl /health",
                "result": "pass",
                "evidence": "out.txt",
            }
        ],
        "rollback": {"performed": True, "method": "git checkout", "result": "pass"},
        "artifacts": [
            {
                "path": "out.txt",
                "sha256": _ART_SHA,
                "bytes": len(_ART_BODY),
                "redacted": True,
            }
        ],
        "slo": {"manifest_revision": None, "measurements": []},
        "signoff": {"status": "pending"},
        "evidence_level": "E2",
        "result": "pass",
    }


def _e5_manifest() -> dict:
    """一份**结构与语义都干净**的 E5 —— E5 负例都从它单点变异而来。

    时间线必须自洽且全在过去 (S2 拒未来事件, S11 拒未结束的 dogfood 窗口):
      执行 07-20 → dogfood 08-01→08-14 → 恢复演练 08-14 → 用户签字 08-20。
    """
    m = _minimal_manifest()
    m["execution"]["started_at"] = "2026-07-20T10:00:00+08:00"
    m["execution"]["finished_at"] = "2026-07-20T12:30:00+08:00"
    m["evidence_level"] = "E5"
    m["signoff"] = {
        "status": "approved",
        "user": "onani",
        "at": "2026-08-20T09:00:00+08:00",
    }
    m["slo"] = {
        "manifest_revision": "slo-manifest@2026-08-28-r1",
        "measurements": [
            {
                "metric": "首次索引时长",
                "threshold": "≤ 15min",
                "measured": "11m42s",
                "method": "time python -m app.scripts.index_vault",
                "meets": True,
            }
        ],
    }
    m["release_gates"] = {
        "dogfood": {
            "protocol_revision": "dogfood-v2@G8-6",
            "rc_sha": m["candidate"]["sha"],
            "start_date": "2026-08-01",
            "end_date": "2026-08-14",
            "days_required": 14,
            "days_completed": 14,
            "activity_counts": {"learning_sessions": 12, "ingest_to_board": 6},
            "activity_minimums": {"learning_sessions": 10, "ingest_to_board": 5},
            "missed_days": 0,
        },
        "recovery_drill": {
            "performed": True,
            "method": "从 nightly 备份恢复 Neo4j + Lance 后继续复习闭环",
            "result": "pass",
            "at": "2026-08-14T21:00:00+08:00",
        },
    }
    return m


def _write(
    tmp_path: Path,
    manifest: dict,
    *,
    rc: str = "rc-test",
    jid: str = "J01",
    with_artifact: bool = True,
) -> Path:
    """按 <rc>/journeys/<Jxx>/manifest.json 结构落盘 (S6 依赖真实路径)。"""
    target = tmp_path / rc / "journeys" / jid / "manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if with_artifact:
        (target.parent / "out.txt").write_bytes(_ART_BODY)
    return target


@pytest.fixture()
def schema() -> dict:
    return vrm.load_schema()


def _problems(tmp_path: Path, mutate, *, rc: str = "rc-test", jid: str = "J01", base=None) -> list[str]:
    manifest = (base or _minimal_manifest)()
    mutate(manifest)
    path = _write(tmp_path, manifest, rc=rc, jid=jid)
    return vrm.validate_manifest(path, vrm.load_schema())


def _codes(problems: list[str]) -> set[str]:
    """抽出每条问题的规则编号, 便于断言'恰好命中哪几条'。"""
    return {p.split("]")[0].lstrip("[") for p in problems if p.startswith("[")}


# ─────────────────────────────────────────────────────────────
# 1. 真示例 —— 必须 PASS 且与磁盘一致
# ─────────────────────────────────────────────────────────────


def test_repo_example_manifest_passes(schema: dict) -> None:
    assert vrm.validate_manifest(EXAMPLE, schema) == []


def test_repo_example_artifact_checksums_match_disk(schema: dict) -> None:
    # 示例声明的 sha256/bytes 必须与磁盘实际一致 (含 repo:// 前缀解析)
    assert vrm.validate_manifest(EXAMPLE, schema, verify_artifacts=True) == []


def test_repo_example_is_declared_reconstructed(schema: dict) -> None:
    # 诚实性锚: 示例是事后回填, 必须自陈 mode=reconstructed 且列出推定字段。
    # 若有人把它改成 live 冒充实录, 本条与 S10 会同时打红。
    doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert doc["provenance"]["mode"] == "reconstructed"
    assert doc["provenance"]["unproven_fields"], "回填件必须逐条列出无证据支撑的字段"
    assert doc["evidence_level"] in {"E0", "E1", "E2"}
    assert doc["signoff"]["status"] != "approved"


def test_repo_example_candidate_sha_is_not_the_archiving_commit(schema: dict) -> None:
    # Codex round-1 HIGH: 首版把"归档证据的那个 commit" (c823a35f, 06:21:32) 当候选
    # SHA, 但它晚于 finished_at (06:20), 执行时根本不存在。回归钉死。
    doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert not doc["candidate"]["sha"].startswith("c823a35f"), (
        "candidate.sha 不能是归档证据的提交 —— 它在执行期尚不存在"
    )


def test_discover_finds_the_example() -> None:
    found = vrm.discover_manifests()
    assert EXAMPLE.resolve() in {p.resolve() for p in found}


def test_minimal_and_e5_bases_are_clean(tmp_path: Path, schema: dict) -> None:
    # 基底本身必须干净, 否则下面每条负例都在测噪声
    assert vrm.validate_manifest(_write(tmp_path, _minimal_manifest()), schema) == []
    assert vrm.validate_manifest(_write(tmp_path / "e5", _e5_manifest()), schema, verify_artifacts=True) == []


# ─────────────────────────────────────────────────────────────
# 2. Codex round-1 BLOCKER 原样复现 —— 必须被挡
# ─────────────────────────────────────────────────────────────


def test_codex_round1_blocker1_repo_path_traversal(tmp_path: Path, schema: dict) -> None:
    """`repo://../../../../etc/passwd` = 任意文件读取 + checksum 回显 hash oracle。"""
    problems = _problems(
        tmp_path,
        lambda m: m.update(
            artifacts=[
                {
                    "path": "repo://../../../../../../../../etc/passwd",
                    "sha256": "0" * 64,
                    "bytes": 1,
                    "redacted": True,
                }
            ],
            assertions=[{"id": "A1", "statement": "s", "method": "m", "result": "pass"}],
        ),
    )
    assert problems, "路径穿越必须被拒"
    # ⚠️ 变异审计教训: 原断言 `any("path" in p)` 被 schema 报错里的 JSON 指针
    # "artifacts/0/path" 满足, 于是这条测试**只测到了 schema 正则**, A0 那层
    # 防御深度全程没被触碰 (A0 的三条子规则当时全部在变异测试中存活)。
    assert all(p.startswith("[schema]") for p in problems)
    # 再直接考 A0 层: 用一条能过 schema 正则、只有 A0 拦得住的路径
    fake = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    with pytest.raises(vrm._ArtifactPathError, match="逃出|上跳|控制字符"):
        vrm.resolve_artifact_path("sub/../../../../etc/passwd", fake)


def test_codex_round1_blocker2_hollow_e5_semantic_layer(tmp_path: Path, schema: dict) -> None:
    """空心 E5: 结构层全合法, 但 rollback fail / 无 dogfood / SLO 无实测 /
    evidence 悬空 / signoff 时间非法 —— 语义层必须逐条点名。

    分两步: 先证明结构层放行 (即这不是靠 schema 兜住的), 再证明语义层拦下。
    """
    m = _minimal_manifest()
    m["evidence_level"] = "E5"
    m["result"] = "pass"
    m["rollback"] = {"performed": True, "method": "x", "result": "fail"}
    m["signoff"] = {"status": "approved", "user": "someone", "at": "not-a-date"}
    m["slo"] = {"manifest_revision": "x", "measurements": []}
    m["assertions"][0]["evidence"] = "ghost.txt"
    path = _write(tmp_path, m)

    from jsonschema import Draft202012Validator

    assert list(Draft202012Validator(schema).iter_errors(m)) == [], (
        "本用例意在测语义层; 若结构层已拦下, 说明用例失去针对性"
    )

    codes = _codes(vrm.validate_manifest(path, schema))
    for expected in {"S2", "S3", "S9", "S11", "S12"}:
        assert expected in codes, f"空心 E5 应命中 {expected}, 实际命中 {sorted(codes)}"


# ─────────────────────────────────────────────────────────────
# 3. 结构层 (schema) 打红
# ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("field", "why"),
    [
        ("candidate", "缺 candidate = 无 SHA, L596 首要必含字段"),
        ("assertions", "缺断言 = 没验什么"),
        ("rollback", "缺回滚结果"),
        ("signoff", "缺用户签字位"),
        ("environment", "缺环境/模型/index SHA"),
        ("artifacts", "缺产物 checksum"),
        ("slo", "缺 SLO 引用与实测"),
        ("provenance", "缺 manifest 自身出处声明"),
    ],
)
def test_missing_required_top_level_field_fails(tmp_path: Path, schema: dict, field: str, why: str) -> None:
    manifest = _minimal_manifest()
    del manifest[field]
    problems = vrm.validate_manifest(_write(tmp_path, manifest), schema)
    assert problems, why
    assert any("[schema]" in p for p in problems)


def test_abbreviated_sha_rejected(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m["candidate"].update(sha="c823a35"))
    assert any("[schema]" in p and "candidate/sha" in p for p in problems)


def test_dirty_true_rejected_for_live_evidence(tmp_path: Path, schema: dict) -> None:
    # L596: dirty=false 是硬要求, 脏树上的证据不成立。
    # schema 早先用 const false 强制, 但那逼得诚实回填只能写假话 (见 S17 注释);
    # 现在由语义层 S17 把住 live/E3+ 这条线。
    problems = _problems(tmp_path, lambda m: m["candidate"].update(dirty=True))
    assert any(p.startswith("[S17]") for p in problems), problems


def test_unknown_top_level_field_rejected(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m.update(mystery_field="x"))
    assert any("[schema]" in p for p in problems)


def test_bad_evidence_level_enum_rejected(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m.update(evidence_level="E9"))
    assert any("evidence_level" in p for p in problems)


def test_bad_artifact_checksum_format_rejected(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["artifacts"].append({"path": "x.log", "sha256": "notahash", "bytes": 1, "redacted": True}),
    )
    assert any("sha256" in p for p in problems)


def test_empty_assertions_rejected(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m.update(assertions=[]))
    assert any("[schema]" in p for p in problems)


def test_empty_artifacts_rejected(tmp_path: Path, schema: dict) -> None:
    # Codex round-1 HIGH: 零产物会把 L596 的 checksum 要求架空成真空通过
    problems = _problems(
        tmp_path,
        lambda m: m.update(
            artifacts=[],
            assertions=[{"id": "A1", "statement": "s", "method": "m", "result": "pass"}],
        ),
    )
    assert any("artifacts" in p for p in problems)


@pytest.mark.parametrize(
    "bad_path",
    [
        "/etc/passwd",
        "~/secrets.txt",
        "../outside.txt",
        "sub/../../outside.txt",
        "repo://../../etc/passwd",
        "windows\\style.txt",
    ],
)
def test_unsafe_artifact_paths_rejected_by_schema(tmp_path: Path, schema: dict, bad_path: str) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m.update(
            artifacts=[{"path": bad_path, "sha256": "0" * 64, "bytes": 1, "redacted": True}],
            assertions=[{"id": "A1", "statement": "s", "method": "m", "result": "pass"}],
        ),
    )
    assert problems, f"不安全路径应被拒: {bad_path}"


def test_approved_signoff_requires_user_and_time(tmp_path: Path, schema: dict) -> None:
    # Codex round-1 BLOCKER-2 的一环: 光一个 "approved" 字符串不算签字
    problems = _problems(tmp_path, lambda m: m.update(signoff={"status": "approved"}, evidence_level="E2"))
    assert any("signoff" in p for p in problems)


def test_reconstructed_requires_source(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m.update(provenance={"mode": "reconstructed", "unproven_fields": ["candidate.dirty"]}),
    )
    assert any("reconstructed_from" in p for p in problems)


def test_structural_failure_short_circuits_semantic_layer(tmp_path: Path, schema: dict) -> None:
    # 同时制造结构错 (缺 environment) 与语义错 (finished < started):
    # 只应报结构问题, 语义层不跑 —— 否则字段缺失会以 KeyError 炸掉
    manifest = _minimal_manifest()
    del manifest["environment"]
    manifest["execution"]["finished_at"] = "2026-08-28T09:00:00+08:00"
    problems = vrm.validate_manifest(_write(tmp_path, manifest), schema)
    assert problems
    assert all(p.startswith("[schema]") for p in problems)


# ─────────────────────────────────────────────────────────────
# 4. 语义层 S1..S13 逐条打红
# ─────────────────────────────────────────────────────────────


def test_s1_unsupported_schema_major_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m.update(schema_version="2.0.0"))
    assert "S1" in _codes(problems)


def test_s2_naive_timestamp_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m["execution"].update(started_at="2026-08-28T10:00:00"))
    assert "S2" in _codes(problems)


def test_s2_finished_before_started_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["execution"].update(finished_at="2026-08-28T09:00:00+08:00"),
    )
    assert any(p.startswith("[S2]") and "早于" in p for p in problems)


def test_s2_bogus_signoff_time_fails(tmp_path: Path, schema: dict) -> None:
    # jsonschema 的 format:date-time 默认只是注解不校验 —— 手验必须补上
    problems = _problems(
        tmp_path,
        lambda m: m.update(signoff={"status": "approved", "user": "u", "at": "not-a-date"}),
    )
    assert any(p.startswith("[S2]") and "signoff.at" in p for p in problems)


def test_s2_naive_signoff_time_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m.update(signoff={"status": "approved", "user": "u", "at": "2026-09-01T10:00:00"}),
    )
    assert any(p.startswith("[S2]") and "signoff.at" in p for p in problems)


def test_s2_accepts_zulu_timezone(tmp_path: Path, schema: dict) -> None:
    # Z 后缀是合法 ISO 8601 时区标记, 不该误杀
    problems = _problems(
        tmp_path,
        lambda m: m["execution"].update(started_at="2026-08-28T02:00:00Z", finished_at="2026-08-28T02:30:00Z"),
    )
    assert problems == []


def test_s3_failing_assertion_cannot_be_overall_pass(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["assertions"][0]["result"] = "fail"
        m["result"] = "pass"

    assert "S3" in _codes(_problems(tmp_path, mutate))


def test_s3_rollback_fail_cannot_be_overall_pass(tmp_path: Path, schema: dict) -> None:
    # Codex round-1 BLOCKER-2 的一环
    problems = _problems(
        tmp_path,
        lambda m: m.update(rollback={"performed": True, "method": "x", "result": "fail"}),
    )
    assert any(p.startswith("[S3]") and "rollback" in p for p in problems)


def test_s3_failing_assertion_with_honest_result_passes(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["assertions"][0]["result"] = "fail"
        m["result"] = "fail"

    assert _problems(tmp_path, mutate) == []


def test_s4_declared_skip_without_items_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m["execution"]["skips_or_mocks"].update(declared=True))
    assert "S4" in _codes(problems)


def test_s4_items_without_declaration_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["execution"]["skips_or_mocks"]["items"].append({"what": "mock backend", "why": "偷懒"}),
    )
    assert "S4" in _codes(problems)


def test_s4_e3_with_declared_skip_fails(tmp_path: Path, schema: dict) -> None:
    # §12.5: E3 = 无 skip 的黑盒 E2E。带 skip 声明还想标 E3 = 洗级
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤1s",
                    "measured": "0.5s",
                    "method": "time x",
                    "meets": True,
                }
            ],
        }
        m["execution"]["skips_or_mocks"] = {
            "declared": True,
            "items": [{"what": "Graphiti 用 fixture", "why": "服务未起"}],
        }

    assert "S4" in _codes(_problems(tmp_path, mutate))


def test_s5_e4_without_signoff_fails(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E4"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤1s",
                    "measured": "0.5s",
                    "method": "time x",
                    "meets": True,
                }
            ],
        }

    assert "S5" in _codes(_problems(tmp_path, mutate))


def test_s5_e4_with_full_signoff_passes(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E4"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤1s",
                    "measured": "0.5s",
                    "method": "time x",
                    "meets": True,
                }
            ],
        }
        m["signoff"] = {
            "status": "approved",
            "user": "onani",
            "at": "2026-08-28T12:00:00+08:00",
        }

    assert _problems(tmp_path, mutate) == []


def test_s6_journey_id_directory_mismatch_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m.update(journey_id="J02"), jid="J01")
    assert "S6" in _codes(problems)


def test_s6_rc_directory_mismatch_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m.update(rc="rc-other"), rc="rc-test")
    assert "S6" in _codes(problems)


def test_s6_wrong_directory_layout_fails(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    stray = tmp_path / "somewhere" / "J01" / "manifest.json"
    stray.parent.mkdir(parents=True)
    stray.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    assert "S6" in _codes(vrm.validate_manifest(stray, schema))


def test_s7_nonzero_exit_without_expected_failure_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["execution"]["commands"].append({"cmd": "pytest -x", "cwd": "backend", "exit_code": 1}),
    )
    assert "S7" in _codes(problems)


def test_s7_declared_expected_failure_passes(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["execution"]["commands"].append(
            {
                "cmd": "curl http://localhost:9/health",
                "cwd": ".",
                "exit_code": 7,
                "expected_failure": True,
                "note": "故障注入断言, 预期连不上",
            }
        ),
    )
    assert problems == []


def test_s8_null_index_sha_without_reason_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m["environment"].update(index_sha=None))
    assert "S8" in _codes(problems)


def test_s8_null_index_sha_with_reason_passes(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["environment"].update(index_sha=None, index_sha_null_reason="本旅程不涉检索索引"),
    )
    assert problems == []


def test_s8_duplicate_artifact_path_fails(tmp_path: Path, schema: dict) -> None:
    art = {"path": "out.txt", "sha256": _ART_SHA, "bytes": len(_ART_BODY), "redacted": True}
    problems = _problems(tmp_path, lambda m: m["artifacts"].append(copy.deepcopy(art)))
    assert any(p.startswith("[S8]") and "同一份文件" in p for p in problems), problems


@pytest.mark.parametrize(
    ("rollback", "must_say"),
    [
        # ⚠️ 变异审计教训: 原版只断言 "S8" in codes, 于是 rollback0 实际是被
        # "not_applicable 必须给 reason" 那条顺手满足的 —— 把"performed=true 与
        # not_applicable 矛盾"整条删掉测试照样绿。现在逐条钉死消息。
        (
            {"performed": True, "method": "x", "result": "not_applicable", "reason": "r"},
            "performed=true 与 result=not_applicable 矛盾",
        ),
        ({"performed": False, "result": "pass"}, "却宣称 result=pass"),
        ({"performed": False, "result": "fail"}, "却宣称 result=fail"),
        ({"performed": False, "result": "not_applicable"}, "必须给 reason"),
        ({"performed": True, "result": "pass"}, "必须给 method"),
    ],
)
def test_s8_rollback_self_contradiction_fails(tmp_path: Path, schema: dict, rollback: dict, must_say: str) -> None:
    problems = _problems(tmp_path, lambda m: m.update(rollback=rollback))
    assert any(p.startswith("[S8]") and must_say in p for p in problems), problems


def test_s9_e3_without_slo_revision_fails(tmp_path: Path, schema: dict) -> None:
    # §12.5 L592: E3 之前必须锁定 SLO, 不得事后降门槛
    problems = _problems(tmp_path, lambda m: m.update(evidence_level="E3"))
    codes = _codes(problems)
    assert "S9" in codes
    assert sum(1 for p in problems if p.startswith("[S9]")) == 2, "缺 revision 与缺 measurements 应各报一条"


def test_s9_e3_with_revision_but_no_measurements_fails(tmp_path: Path, schema: dict) -> None:
    # Codex round-1 HIGH: 只填一个 revision 字符串证明不了"记录了阈值与实测"
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["slo"] = {"manifest_revision": "slo-v1", "measurements": []}

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S9]") and "measurements" in p for p in problems)


def test_s9_e3_with_measurements_passes(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "slo-manifest@2026-08-28-r1",
            "measurements": [
                {
                    "metric": "RAG cold p95",
                    "threshold": "≤ 2.5s",
                    "measured": "1.8s",
                    "unit": "s",
                    "method": "python backend/scripts/run_vault_retrieval_regression.py --p95",
                    "meets": True,
                }
            ],
        }

    assert _problems(tmp_path, mutate) == []


def test_s9_unmet_threshold_cannot_be_pass_without_waiver(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "RAG cold p95",
                    "threshold": "≤ 2.5s",
                    "measured": "4.1s",
                    "method": "…",
                    "meets": False,
                }
            ],
        }
        m["result"] = "pass"

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S9]") and "未达标" in p for p in problems)


def test_s9_unmet_threshold_with_user_waiver_passes(tmp_path: Path, schema: dict) -> None:
    # §12.5: 未达标只能判失败, 或经用户事前/书面接受后降级为限制
    def mutate(m: dict) -> None:
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "RAG cold p95",
                    "threshold": "≤ 2.5s",
                    "measured": "4.1s",
                    "method": "…",
                    "meets": False,
                    "waiver": {
                        "reason": "冷启动含模型加载, 用户接受并入 Known limitations",
                        "accepted_by": "onani",
                        "at": "2026-08-20T12:00:00+08:00",
                    },
                }
            ],
        }
        m["result"] = "pass"
        m["known_limitations"] = ["RAG cold p95 未达标, 用户已书面接受并降级为限制"]

    assert _problems(tmp_path, mutate) == []


def test_s9_unmet_threshold_with_honest_fail_result_passes(tmp_path: Path, schema: dict) -> None:
    # 红队 R7 整改后: 只有如实判 fail 才免 waiver; partial 也要 waiver+已知限制
    def mutate(m: dict) -> None:
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤ 1s",
                    "measured": "3s",
                    "method": "…",
                    "meets": False,
                }
            ],
        }
        m["result"] = "fail"
        m["assertions"][0]["result"] = "fail"

    assert _problems(tmp_path, mutate) == []


def test_s10_reconstructed_cannot_claim_e3(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["provenance"] = {
            "mode": "reconstructed",
            "reconstructed_from": "旧归档",
            "unproven_fields": ["candidate.dirty"],
        }
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤1s",
                    "measured": "0.5s",
                    "method": "…",
                    "meets": True,
                }
            ],
        }

    codes = _codes(_problems(tmp_path, mutate))
    assert "S10" in codes and "S13" in codes


def test_s10_reconstructed_cannot_be_signed_off(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["provenance"] = {
            "mode": "reconstructed",
            "reconstructed_from": "旧归档",
            "unproven_fields": ["candidate.dirty"],
        }
        m["signoff"] = {
            "status": "approved",
            "user": "onani",
            "at": "2026-08-28T12:00:00+08:00",
        }

    assert any(p.startswith("[S10]") and "signoff" in p for p in _problems(tmp_path, mutate))


def test_s10_reconstructed_with_empty_unproven_fields_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m.update(
            provenance={
                "mode": "reconstructed",
                "reconstructed_from": "旧归档",
                "unproven_fields": [],
            }
        ),
    )
    assert any(p.startswith("[S10]") and "unproven_fields" in p for p in problems)


def test_s10_live_with_unproven_fields_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m.update(provenance={"mode": "live", "unproven_fields": ["candidate.dirty"]}),
    )
    assert "S10" in _codes(problems)


def test_s11_e5_without_release_gates_fails(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m.pop("release_gates")

    problems = _problems(tmp_path, mutate, base=_e5_manifest)
    assert any(p.startswith("[S11]") and "release_gates" in p for p in problems)


def test_s11_e5_with_short_dogfood_window_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["release_gates"]["dogfood"].update(days_completed=9),
        base=_e5_manifest,
    )
    assert any(p.startswith("[S11]") and "未跑满" in p for p in problems)


def test_s11_e5_with_missed_days_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["release_gates"]["dogfood"].update(missed_days=2),
        base=_e5_manifest,
    )
    assert any(p.startswith("[S11]") and "漏日" in p for p in problems)


def test_s11_e5_dogfood_on_different_sha_fails(tmp_path: Path, schema: dict) -> None:
    # §12.6: 影响产品行为的修改须从新 SHA 重开 14 天
    problems = _problems(
        tmp_path,
        lambda m: m["release_gates"]["dogfood"].update(rc_sha="f" * 40),
        base=_e5_manifest,
    )
    assert any(p.startswith("[S11]") and "rc_sha" in p for p in problems)


def test_s11_e5_without_recovery_drill_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(
        tmp_path,
        lambda m: m["release_gates"]["recovery_drill"].update(result="fail"),
        base=_e5_manifest,
    )
    assert any(p.startswith("[S11]") and "恢复演练" in p for p in problems)


def test_s11_release_gates_on_lower_level_fails(tmp_path: Path, schema: dict) -> None:
    # 别用 E5 字段给低等级镀金
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E2"
        m["signoff"] = {"status": "pending"}
        m["slo"] = {"manifest_revision": None, "measurements": []}

    problems = _problems(tmp_path, mutate, base=_e5_manifest)
    assert any(p.startswith("[S11]") and "只属 E5" in p for p in problems)


def test_s12_dangling_evidence_reference_fails(tmp_path: Path, schema: dict) -> None:
    problems = _problems(tmp_path, lambda m: m["assertions"][0].update(evidence="ghost.txt"))
    assert "S12" in _codes(problems)


def test_s12_evidence_matching_artifact_passes(tmp_path: Path, schema: dict) -> None:
    # ⚠️ 变异审计教训: 原版是 `_problems(tmp_path, lambda m: None) == []`, 与基底
    # 干净性测试逐字重复, 对 S12 零断言。现在换成"多产物 + 各断言引用不同产物"的
    # 真实形状, 确保 S12 的放行分支被走到。
    def mutate(m: dict) -> None:
        m["artifacts"].append({"path": "second.txt", "sha256": _ART_SHA, "bytes": len(_ART_BODY), "redacted": True})
        m["assertions"].append(
            {"id": "A2", "statement": "s2", "method": "m2", "result": "pass", "evidence": "second.txt"}
        )

    manifest = _minimal_manifest()
    mutate(manifest)
    path = _write(tmp_path, manifest)
    (path.parent / "second.txt").write_bytes(_ART_BODY)
    assert vrm.validate_manifest(path, schema) == []


def test_s13_e3_requires_live_provenance(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤1s",
                    "measured": "0.5s",
                    "method": "…",
                    "meets": True,
                }
            ],
        }
        m["provenance"] = {
            "mode": "reconstructed",
            "reconstructed_from": "旧归档",
            "unproven_fields": ["candidate.sha"],
        }

    assert "S13" in _codes(_problems(tmp_path, mutate))


# ─────────────────────────────────────────────────────────────
# 5. 产物层 A0..A3
# ─────────────────────────────────────────────────────────────


def test_a0_symlink_artifact_rejected(tmp_path: Path, schema: dict) -> None:
    """schema 正则拦不住 symlink —— A0 解析层必须拒绝跟随。"""
    manifest = _minimal_manifest()
    manifest["artifacts"] = [{"path": "link.txt", "sha256": _ART_SHA, "bytes": len(_ART_BODY), "redacted": True}]
    manifest["assertions"][0]["evidence"] = "link.txt"
    path = _write(tmp_path, manifest, with_artifact=False)
    # ⚠️ 目标必须在 manifest 目录**内**: 指向外部时 containment 规则会先开火,
    # symlink 分支根本执行不到 (这正是变异审计发现该规则零覆盖的原因)。
    inside = path.parent / "real.txt"
    inside.write_bytes(_ART_BODY)
    (path.parent / "link.txt").symlink_to(inside)
    problems = vrm.validate_manifest(path, schema)
    # ⚠️ 变异审计教训: 原断言写作 `"symlink" in p`, 而 pytest 的 tmp_path 目录名里就带
    # 测试函数名 "…symlink…", 于是**报错消息里的路径**就能满足它 —— 删掉整条 symlink
    # 规则测试照样绿。改断言 A0 的中文措辞, 它只可能来自校验器本身。
    assert any(p.startswith("[A0]") and "含 symlink" in p for p in problems), problems
    # 越界条目只报一次 A0, 不因开了产物真验就重复
    verified = vrm.validate_manifest(path, schema, verify_artifacts=True)
    assert sum(1 for p in verified if p.startswith("[A0]")) == 1
    # 且绝不能真去读它 —— A1/A2/A3 都不该出现
    assert not any(p.startswith(("[A1]", "[A2]", "[A3]")) for p in verified)


def test_a0_symlinked_parent_dir_rejected(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    manifest["artifacts"] = [
        {
            "path": "sub/out.txt",
            "sha256": _ART_SHA,
            "bytes": len(_ART_BODY),
            "redacted": True,
        }
    ]
    manifest["assertions"][0]["evidence"] = "sub/out.txt"
    path = _write(tmp_path, manifest, with_artifact=False)
    real_dir = tmp_path / "elsewhere"
    real_dir.mkdir()
    (real_dir / "out.txt").write_bytes(_ART_BODY)
    (path.parent / "sub").symlink_to(real_dir, target_is_directory=True)
    problems = vrm.validate_manifest(path, schema, verify_artifacts=True)
    assert any(p.startswith("[A0]") for p in problems)


def test_resolve_artifact_path_rejects_traversal_directly() -> None:
    fake_manifest = REPO_ROOT / "docs" / "release-evidence" / "x" / "journeys" / "J01" / "manifest.json"
    for bad in ["../out.txt", "/etc/passwd", "repo://../../etc/passwd", "~/x"]:
        with pytest.raises(vrm._ArtifactPathError):
            vrm.resolve_artifact_path(bad, fake_manifest)


@pytest.mark.parametrize(
    "sneaky",
    [
        "ok.txt\n../../etc/passwd",  # schema 正则的 .* 不跨行, 靠 A0 兜住
        "ok.txt\n/etc/passwd",
        "repo://ok\n../../../../etc/passwd",
        "tab\there.txt",
    ],
)
def test_a0_rejects_control_chars_in_path(sneaky: str) -> None:
    fake_manifest = REPO_ROOT / "docs" / "release-evidence" / "x" / "journeys" / "J01" / "manifest.json"
    with pytest.raises(vrm._ArtifactPathError):
        vrm.resolve_artifact_path(sneaky, fake_manifest)


def test_a0_percent_encoding_is_not_decoded_so_stays_contained() -> None:
    # %2e%2e 不会被文件系统解码 —— 它是字面目录名, 解析后仍在 manifest 目录内。
    # 记录这一行为以防日后有人"顺手"加解码而引入真逃逸。
    fake_manifest = REPO_ROOT / "docs" / "release-evidence" / "x" / "journeys" / "J01" / "manifest.json"
    got = vrm.resolve_artifact_path("%2e%2e/escape.txt", fake_manifest)
    assert got.is_relative_to(fake_manifest.parent.resolve())


def test_resolve_artifact_path_accepts_repo_prefix() -> None:
    fake_manifest = REPO_ROOT / "docs" / "release-evidence" / "x" / "journeys" / "J01" / "manifest.json"
    got = vrm.resolve_artifact_path("repo://README.md", fake_manifest)
    assert got == (REPO_ROOT / "README.md").resolve()


def test_a1_artifact_pointing_at_directory_reported_precisely(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    manifest["artifacts"].append({"path": "adir", "sha256": "c" * 64, "bytes": 0, "redacted": True})
    path = _write(tmp_path, manifest)
    (path.parent / "adir").mkdir()
    problems = vrm.validate_manifest(path, schema, verify_artifacts=True)
    assert any(p.startswith("[A1]") and "目录" in p for p in problems)


def test_verify_artifacts_detects_missing_file(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    manifest["artifacts"].append({"path": "ghost.log", "sha256": "b" * 64, "bytes": 5, "redacted": True})
    path = _write(tmp_path, manifest)
    assert any(p.startswith("[A1]") for p in vrm.validate_manifest(path, schema))
    # 显式弃权时才不看磁盘 (声明层与实证层分离)
    assert vrm.validate_manifest(path, schema, verify_artifacts=False) == []


def test_verify_artifacts_detects_tampered_content(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    path = _write(tmp_path, manifest)
    assert vrm.validate_manifest(path, schema, verify_artifacts=True) == []
    (path.parent / "out.txt").write_bytes(b"tampered-body\n")  # 同长度, 只有内容变
    problems = vrm.validate_manifest(path, schema, verify_artifacts=True)
    assert any(p.startswith("[A2]") for p in problems)


def test_verify_artifacts_detects_size_drift(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    manifest["artifacts"][0]["bytes"] = 999
    path = _write(tmp_path, manifest)
    problems = vrm.validate_manifest(path, schema, verify_artifacts=True)
    assert any(p.startswith("[A3]") for p in problems)


# ─────────────────────────────────────────────────────────────
# 6. RC 完整性门
# ─────────────────────────────────────────────────────────────


def test_rc_completeness_flags_missing_journeys(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    for jid in ["J01", "J02"]:
        m = _minimal_manifest()
        m["journey_id"] = jid
        m["rc"] = "rc-1"
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [{"metric": "x", "threshold": "≤ 1s", "measured": "0.5s", "method": "t", "meets": True}],
        }
        target = root / "rc-1" / "journeys" / jid / "manifest.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    problems = vrm.check_rc_completeness("rc-1", root=root)
    assert len(problems) == 8, f"J03-J10 应各报一条缺失, 实际: {problems}"
    assert all(p.startswith("[RC]") for p in problems)


def test_rc_completeness_rejects_reconstructed_manifests(tmp_path: Path) -> None:
    # 一份格式演示件不能让 RC 门长绿 (Codex round-1 MEDIUM)
    root = tmp_path / "evidence"
    for jid in vrm.ALL_JOURNEYS:
        m = _minimal_manifest()
        m["journey_id"] = jid
        m["rc"] = "rc-1"
        m["provenance"] = {
            "mode": "reconstructed",
            "reconstructed_from": "旧归档",
            "unproven_fields": ["candidate.dirty"],
        }
        target = root / "rc-1" / "journeys" / jid / "manifest.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    problems = vrm.check_rc_completeness("rc-1", root=root)
    live_hits = [p for p in problems if "live 实录" in p]
    assert len(live_hits) == 10, problems


def test_rc_completeness_passes_when_all_live(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    for jid in vrm.ALL_JOURNEYS:
        m = _minimal_manifest()
        m["journey_id"] = jid
        m["rc"] = "rc-1"
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "slo-v1",
            "measurements": [{"metric": "x", "threshold": "≤ 1s", "measured": "0.5s", "method": "t", "meets": True}],
        }
        target = root / "rc-1" / "journeys" / jid / "manifest.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    assert vrm.check_rc_completeness("rc-1", root=root) == []


def test_rc_completeness_on_unknown_rc(tmp_path: Path) -> None:
    problems = vrm.check_rc_completeness("nope", root=tmp_path)
    assert len(problems) == 1 and "无任何证据" in problems[0]


def test_example_rc_does_not_satisfy_release_gate() -> None:
    # 仓内示例件是回填 J08 —— RC 门必须照样红 (缺 9 条 + 该条非 live)
    problems = vrm.check_rc_completeness("example-backfill-d5")
    assert problems, "格式演示件不得让 RC 完整性门通过"


# ─────────────────────────────────────────────────────────────
# 7. schema 指纹契约 + 装载期错误分档
# ─────────────────────────────────────────────────────────────


def test_schema_sha256_constant_matches_repo_schema() -> None:
    actual = hashlib.sha256(SCHEMA.read_bytes()).hexdigest()
    assert actual == vrm.SCHEMA_SHA256, (
        "schema 文件与 validate_release_manifest.py::SCHEMA_SHA256 失同步 — 改 schema 必须同 commit 更新常量"
    )


def test_tampered_schema_is_config_error(tmp_path: Path) -> None:
    fake = tmp_path / "manifest.schema.json"
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))
    data["required"] = [r for r in data["required"] if r != "candidate"]  # 单边放水
    fake.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(vrm.ConfigError, match="指纹"):
        vrm.load_schema(fake)


def test_malformed_json_is_config_error(tmp_path: Path, schema: dict) -> None:
    path = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(vrm.ConfigError, match="合法 JSON"):
        vrm.validate_manifest(path, schema)


def test_missing_manifest_is_config_error(tmp_path: Path, schema: dict) -> None:
    with pytest.raises(vrm.ConfigError, match="不存在"):
        vrm.validate_manifest(tmp_path / "nope.json", schema)


def test_non_object_manifest_is_validation_failure_not_config_error(tmp_path: Path, schema: dict) -> None:
    # Codex round-1 MEDIUM: 合法 JSON 但顶层是数组 = 形状不对 = 退出码 1, 不是环境错
    path = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text("[]", encoding="utf-8")
    problems = vrm.validate_manifest(path, schema)
    assert problems and problems[0].startswith("[json]")


def test_duplicate_json_keys_rejected(tmp_path: Path, schema: dict) -> None:
    # {"dirty": true, "dirty": false} 会被标准库静默取后值 —— 直接拒收
    path = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    path.parent.mkdir(parents=True)
    raw = json.dumps(_minimal_manifest(), ensure_ascii=False)
    raw = raw.replace('"dirty": false', '"dirty": true, "dirty": false', 1)
    path.write_text(raw, encoding="utf-8")
    problems = vrm.validate_manifest(path, schema)
    assert any("重复" in p for p in problems)


def test_non_utf8_manifest_is_config_error(tmp_path: Path, schema: dict) -> None:
    path = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b'{"schema_version": "\xff\xfe1.0.0"}')
    with pytest.raises(vrm.ConfigError, match="UTF-8"):
        vrm.validate_manifest(path, schema)


# ─────────────────────────────────────────────────────────────
# 8. CLI 退出码三档 (裁判命令直接用的就是它)
# ─────────────────────────────────────────────────────────────


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "validate_release_manifest.py"), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def test_cli_exit_0_on_repo_example() -> None:
    proc = _cli(str(EXAMPLE))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout


def test_cli_all_exit_0() -> None:
    proc = _cli("--all", "--verify-artifacts")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_cli_exit_1_on_malformed_fixture(tmp_path: Path) -> None:
    manifest = _minimal_manifest()
    manifest["candidate"]["dirty"] = True  # 脏树证据
    manifest["execution"]["skips_or_mocks"] = {"declared": True, "items": []}
    path = _write(tmp_path, manifest)
    proc = _cli(str(path))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FAIL" in proc.stdout


def test_cli_exit_1_on_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text("[]", encoding="utf-8")
    assert _cli(str(path)).returncode == 1


def test_cli_exit_1_on_missing_file(tmp_path: Path) -> None:
    # 红队整改: 单份文件装载失败按"内容不合格"(1) 报并继续下一份,
    # 退出码 2 只留给 schema 指纹/依赖缺失这类真环境问题。
    proc = _cli(str(tmp_path / "nope.json"))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "[load]" in proc.stdout


def test_cli_exit_1_on_syntax_error(tmp_path: Path) -> None:
    path = tmp_path / "rc-test" / "journeys" / "J01" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text("{oops", encoding="utf-8")
    proc = _cli(str(path))
    assert proc.returncode == 1
    assert "[load]" in proc.stdout


def test_cli_exit_2_on_schema_fingerprint_mismatch(tmp_path: Path) -> None:
    fake = tmp_path / "manifest.schema.json"
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))
    data["required"] = [r for r in data["required"] if r != "candidate"]
    fake.write_text(json.dumps(data), encoding="utf-8")
    proc = _cli(str(EXAMPLE), "--schema", str(fake))
    assert proc.returncode == 2, proc.stdout + proc.stderr


def test_cli_require_complete_fails_on_example_rc() -> None:
    proc = _cli("--require-complete", "example-backfill-d5")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RC 完整性门 FAIL" in proc.stdout


def test_cli_requires_target() -> None:
    proc = _cli()
    assert proc.returncode == 2  # argparse error


# ─────────────────────────────────────────────────────────────
# 9. 红队整改回归 (5 轴对抗实测确认的 24 条, 逐条钉死)
#    来源: _bmad-output/审查/revd-redteam-2026-08-28.md
# ─────────────────────────────────────────────────────────────


def _e5(tmp_path: Path, mutate, **kw) -> list[str]:
    return _problems(tmp_path, mutate, base=_e5_manifest, **kw)


def test_redteam_e5_cannot_set_its_own_dogfood_bar(tmp_path: Path, schema: dict) -> None:
    """R1 BLOCKER: days_required 由作者自填, 写 1 就满足「14 天门」。"""
    manifest = _e5_manifest()
    manifest["release_gates"]["dogfood"].update(
        days_required=1, days_completed=1, start_date="2026-08-01", end_date="2026-08-01"
    )
    path = _write(tmp_path, manifest)
    problems = vrm.validate_manifest(path, schema)
    assert problems, "days_required=1 必须被拒 —— 下限由 §12.6 钉死, 不由 manifest 自定"
    assert any("days_required" in p or "14" in p for p in problems), problems


def test_redteam_dogfood_days_floor_is_pinned_in_validator(tmp_path: Path, schema: dict) -> None:
    """即使 schema 那道 minimum 被绕过, 语义层也要独立守住 14 天下限。"""
    assert vrm.DOGFOOD_MIN_DAYS == 14
    problems = _e5(tmp_path, lambda m: m["release_gates"]["dogfood"].update(days_completed=13, missed_days=0))
    assert any(p.startswith("[S11]") and "不足协议下限" in p for p in problems), problems


def test_redteam_e5_activity_counts_cannot_be_all_zero(tmp_path: Path, schema: dict) -> None:
    """R2 BLOCKER: 十四天里 0 次学习 session 也能过。"""
    problems = _e5(
        tmp_path,
        lambda m: m["release_gates"]["dogfood"].update(activity_counts={"learning_sessions": 0, "ingest_to_board": 0}),
    )
    assert any(p.startswith("[S11]") and "活动量" in p for p in problems), problems


def test_redteam_activity_minimums_key_set_must_match(tmp_path: Path, schema: dict) -> None:
    """只报达标项 = 自选考卷。"""
    problems = _e5(
        tmp_path,
        lambda m: m["release_gates"]["dogfood"].update(
            activity_counts={"learning_sessions": 12},
            activity_minimums={"learning_sessions": 10, "backup_recovery": 1},
        ),
    )
    assert any(p.startswith("[S11]") and "项目不一致" in p for p in problems), problems


@pytest.mark.parametrize(
    ("start", "end", "completed", "must_say"),
    [
        ("2026-08-01", "2026-08-02", 14, "装不下"),  # R3: 2 天窗口报 14 天
        ("2026-08-30", "2026-08-01", 14, "早于"),  # R3b: end 早于 start
    ],
)
def test_redteam_dogfood_window_cross_checked(
    tmp_path: Path, schema: dict, start: str, end: str, completed: int, must_say: str
) -> None:
    problems = _e5(
        tmp_path,
        lambda m: m["release_gates"]["dogfood"].update(start_date=start, end_date=end, days_completed=completed),
    )
    assert any(p.startswith("[S11]") and must_say in p for p in problems), problems


def test_redteam_dogfood_window_cannot_end_in_the_future(tmp_path: Path, schema: dict) -> None:
    manifest = _e5_manifest()
    manifest["release_gates"]["dogfood"].update(start_date="2099-01-01", end_date="2099-01-14")
    path = _write(tmp_path, manifest)
    problems = vrm.validate_manifest(path, schema)
    assert any(p.startswith("[S11]") and "在未来" in p for p in problems), problems


def test_redteam_s14_e3_plus_requires_overall_pass(tmp_path: Path, schema: dict) -> None:
    """R6: 断言全红 + 回滚失败的旅程仍可标 E4/E5 并带签字。"""
    problems = _e5(tmp_path, lambda m: m.update(result="fail"))
    assert any(p.startswith("[S14]") for p in problems), problems


def test_redteam_s14_allows_e2_partial(tmp_path: Path, schema: dict) -> None:
    # 反向守卫: 低等级的 partial 是合法的诚实表达, 不该误杀 (仓内示例就是 E2/partial)
    assert _problems(tmp_path, lambda m: m.update(result="partial", evidence_level="E2")) == []


def test_redteam_s15_operator_cannot_sign_off_for_the_user(tmp_path: Path, schema: dict) -> None:
    """R17: 执行者给自己签发 E5 用户验收。"""

    def mutate(m: dict) -> None:
        m["signoff"] = {
            "status": "approved",
            "user": m["execution"]["operator"],
            "at": "2026-08-20T09:00:00+08:00",
        }

    problems = _e5(tmp_path, mutate)
    assert any(p.startswith("[S15]") and "execution.operator" in p for p in problems), problems


def test_redteam_s15_model_cannot_sign_off(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["environment"]["models"] = [{"role": "judge", "name": "some-model-5"}]
        m["signoff"] = {
            "status": "approved",
            "user": "some-model-5",
            "at": "2026-08-20T09:00:00+08:00",
        }

    problems = _e5(tmp_path, mutate)
    assert any(p.startswith("[S15]") and "模型" in p for p in problems), problems


def test_redteam_s2_signoff_cannot_predate_finish(tmp_path: Path, schema: dict) -> None:
    """R8/R15: 用户在旅程结束前就"验收"了它的结果。"""
    problems = _problems(
        tmp_path,
        lambda m: m.update(signoff={"status": "approved", "user": "u", "at": "2026-08-28T09:00:00+08:00"}),
    )
    assert any(p.startswith("[S2]") and "早于 execution.finished_at" in p for p in problems), problems


@pytest.mark.parametrize(
    "field_setter",
    [
        lambda m: m["execution"].update(
            started_at="2099-03-01T10:00:00+08:00", finished_at="2099-03-01T12:00:00+08:00"
        ),
        lambda m: m.update(signoff={"status": "approved", "user": "u", "at": "2099-03-02T09:00:00+08:00"}),
    ],
)
def test_redteam_s2_rejects_future_events(tmp_path: Path, schema: dict, field_setter) -> None:
    """R19: 整条旅程记录在 2099 年仍判合格。"""
    problems = _problems(tmp_path, field_setter)
    assert any(p.startswith("[S2]") and "在未来" in p for p in problems), problems


def test_redteam_s2_finished_at_must_be_tz_aware(tmp_path: Path, schema: dict) -> None:
    """变异审计: 原套件只 naive 化 started_at, finished_at 那条规则删掉也全绿。"""
    problems = _problems(tmp_path, lambda m: m["execution"].update(finished_at="2026-08-28T10:30:00"))
    assert any(p.startswith("[S2]") and "finished_at" in p for p in problems), problems


def test_redteam_s2_waiver_at_must_be_tz_aware(tmp_path: Path, schema: dict) -> None:
    """变异审计: waiver.at 的时区检查此前零覆盖 —— 它恰是用户书面接受的时间戳。"""

    def mutate(m: dict) -> None:
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤ 1s",
                    "measured": "3s",
                    "method": "t",
                    "meets": False,
                    "waiver": {"reason": "r", "accepted_by": "onani", "at": "2026-08-29T10:00:00"},
                }
            ],
        }
        m["known_limitations"] = ["x 未达标, 已接受"]

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S2]") and "waiver.at" in p for p in problems), problems


def test_redteam_s2_recovery_drill_at_must_be_tz_aware(tmp_path: Path, schema: dict) -> None:
    """变异审计: recovery_drill.at 的时区检查此前零覆盖。"""
    problems = _e5(tmp_path, lambda m: m["release_gates"]["recovery_drill"].update(at="2026-08-14T21:00:00"))
    assert any(p.startswith("[S2]") and "recovery_drill.at" in p for p in problems), problems


def test_redteam_s10_live_cannot_carry_reconstructed_from(tmp_path: Path, schema: dict) -> None:
    """R12: 一边宣称实录, 一边在相邻字段承认是回填件。"""
    problems = _problems(
        tmp_path,
        lambda m: m.update(provenance={"mode": "live", "unproven_fields": [], "reconstructed_from": "旧归档"}),
    )
    assert problems, "live + reconstructed_from 必须被拒"


def test_redteam_s7_expected_failure_on_zero_exit(tmp_path: Path, schema: dict) -> None:
    """R9b: 「这条命令预期失败」与「它退出码为 0」并存。"""
    problems = _problems(
        tmp_path,
        lambda m: m["execution"]["commands"].append(
            {"cmd": "pytest -q", "cwd": ".", "exit_code": 0, "expected_failure": True, "note": "n"}
        ),
    )
    assert any(p.startswith("[S7]") and "exit_code=0" in p for p in problems), problems


def test_redteam_expected_failure_requires_reason(tmp_path: Path, schema: dict) -> None:
    """R9: expected_failure 不能是无理由的万能牌。"""
    problems = _problems(
        tmp_path,
        lambda m: m["execution"]["commands"].append({"cmd": "x", "cwd": ".", "exit_code": 1, "expected_failure": True}),
    )
    assert problems, "expected_failure=true 缺 note 必须被拒"


def test_redteam_s8_artifact_path_aliases_are_one_file(tmp_path: Path, schema: dict) -> None:
    """R20: run.log 与 ./run.log 冒充两份独立证据。"""
    problems = _problems(
        tmp_path,
        lambda m: m["artifacts"].append(
            {"path": "./out.txt", "sha256": _ART_SHA, "bytes": len(_ART_BODY), "redacted": True}
        ),
    )
    assert any(p.startswith("[S8]") and "同一份文件" in p for p in problems), problems


def test_redteam_s8_zero_bytes_needs_empty_digest(tmp_path: Path, schema: dict) -> None:
    """R21: bytes=0 配一个非空串摘要, 算术上不可能同时成立。"""
    problems = _problems(
        tmp_path,
        lambda m: m["artifacts"].append({"path": "empty.txt", "sha256": "c" * 64, "bytes": 0, "redacted": True}),
    )
    assert any(p.startswith("[S8]") and "算术上不可能" in p for p in problems), problems


def test_redteam_s8_performed_true_not_applicable_has_own_message(tmp_path: Path, schema: dict) -> None:
    """变异审计: 该子规则此前被"必须给 reason"顺手满足, 单删不掉测试。"""
    problems = _problems(
        tmp_path,
        lambda m: m.update(rollback={"performed": True, "method": "m", "result": "not_applicable", "reason": "r"}),
    )
    assert any("performed=true 与 result=not_applicable 矛盾" in p for p in problems), problems


def test_redteam_s9_numeric_cross_check(tmp_path: Path, schema: dict) -> None:
    """R18: 实测 47s 对阈值 ≤2.5s 却写 meets=true。"""
    problems = _problems(
        tmp_path,
        lambda m: m.update(
            slo={
                "manifest_revision": "v1",
                "measurements": [
                    {
                        "metric": "p95",
                        "threshold": "p95 ≤ 2.5s",
                        "measured": "p95 = 47.0s",
                        "method": "t",
                        "meets": True,
                    }
                ],
            }
        ),
    )
    assert any(p.startswith("[S9]") and "自带数字矛盾" in p for p in problems), problems


def test_redteam_s9_numeric_cross_check_stays_quiet_when_unparseable(tmp_path: Path, schema: dict) -> None:
    # 抠不出数字或判不出方向时必须闭嘴, 否则会误杀正常 manifest
    problems = _problems(
        tmp_path,
        lambda m: m.update(
            slo={
                "manifest_revision": "v1",
                "measurements": [
                    {
                        "metric": "视觉一致性",
                        "threshold": "人工评审通过",
                        "measured": "通过",
                        "method": "人工",
                        "meets": True,
                    }
                ],
            }
        ),
    )
    assert problems == [], problems


def test_redteam_s9_partial_no_longer_launders_slo_miss(tmp_path: Path, schema: dict) -> None:
    """R7: SLO 未达标经 result=partial 洗白 (旧版 waiver 要求只在 pass 时生效)。"""

    def mutate(m: dict) -> None:
        m["result"] = "partial"
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [
                {"metric": "x", "threshold": "≤ 2.5s", "measured": "47.0s", "method": "t", "meets": False}
            ],
        }

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S9]") and "无用户 waiver" in p for p in problems), problems


def test_redteam_s9_unmet_requires_known_limitation(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤ 2.5s",
                    "measured": "47.0s",
                    "method": "t",
                    "meets": False,
                    "waiver": {"reason": "r", "accepted_by": "onani", "at": "2026-08-29T10:00:00+08:00"},
                }
            ],
        }
        m["known_limitations"] = []

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S9]") and "known_limitations" in p for p in problems), problems


def test_redteam_s9_waiver_cannot_be_self_signed(tmp_path: Path, schema: dict) -> None:
    """R16: waiver.accepted_by 与 execution.operator 同一人。"""

    def mutate(m: dict) -> None:
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [
                {
                    "metric": "x",
                    "threshold": "≤ 2.5s",
                    "measured": "47.0s",
                    "method": "t",
                    "meets": False,
                    "waiver": {
                        "reason": "r",
                        "accepted_by": m["execution"]["operator"],
                        "at": "2026-08-29T10:00:00+08:00",
                    },
                }
            ],
        }
        m["known_limitations"] = ["x 未达标"]

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S9]") and "自己开免责" in p for p in problems), problems


def test_redteam_s16_mock_marker_in_command(tmp_path: Path, schema: dict) -> None:
    """R5 BLOCKER: 命令行写满 mock/skip 开关, 只要 declared=false 就能拿 E3。"""

    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [{"metric": "x", "threshold": "≤ 1s", "measured": "0.5s", "method": "t", "meets": True}],
        }
        m["execution"]["commands"].insert(
            0, {"cmd": "SKIP_NEO4J=1 GRAPHITI_MOCK=1 pytest -q", "cwd": ".", "exit_code": 0}
        )

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S16]") for p in problems), problems


def test_redteam_s16_mock_admission_in_note(tmp_path: Path, schema: dict) -> None:
    """R13: 命令 note 自陈「实际用 mock 跑的」而 declared=false。"""

    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [{"metric": "x", "threshold": "≤ 1s", "measured": "0.5s", "method": "t", "meets": True}],
        }
        m["execution"]["commands"][0]["note"] = "实际是用 mock 的 Neo4j client 跑的"

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S16]") and "note" in p for p in problems), problems


def test_redteam_s16_quiet_below_e3(tmp_path: Path, schema: dict) -> None:
    # E2 上不扫 —— 低等级本就允许 mock, 扫了只会制造噪声
    problems = _problems(
        tmp_path,
        lambda m: m["execution"]["commands"][0].update(note="这一步用了 mock 客户端"),
    )
    assert not any(p.startswith("[S16]") for p in problems), problems


def test_redteam_s17_dirty_tree_only_in_low_grade_backfill(tmp_path: Path, schema: dict) -> None:
    """example-fidelity O4: schema 曾把 dirty 写死 const false, 逼诚实回填说假话。
    现在放开, 但 live / E3+ 仍必须 false。"""
    problems = _problems(tmp_path, lambda m: m["candidate"].update(dirty=True))
    assert any(p.startswith("[S17]") and "reconstructed" in p for p in problems), problems


def test_redteam_s17_dirty_allowed_in_reconstructed_e2(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["candidate"]["dirty"] = True
        m["provenance"] = {
            "mode": "reconstructed",
            "reconstructed_from": "旧归档",
            "unproven_fields": ["execution.commands"],
        }

    assert _problems(tmp_path, mutate) == []


def test_redteam_s17_dirty_blocks_e3(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["candidate"]["dirty"] = True
        m["evidence_level"] = "E3"
        m["provenance"] = {
            "mode": "reconstructed",
            "reconstructed_from": "旧归档",
            "unproven_fields": ["x"],
        }
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [{"metric": "x", "threshold": "≤1s", "measured": "0.5s", "method": "t", "meets": True}],
        }

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S17]") and "E2" in p for p in problems), problems


def test_redteam_a0_repo_prefix_cannot_reach_into_evidence_tree() -> None:
    """R25: 拿别的 RC 的产物给自己背书。"""
    fake = REPO_ROOT / "docs" / "release-evidence" / "rc-x" / "journeys" / "J01" / "manifest.json"
    with pytest.raises(vrm._ArtifactPathError, match="证据树内部"):
        vrm.resolve_artifact_path("repo://docs/release-evidence/example-backfill-d5/journeys/J08/before.txt", fake)


def test_redteam_a0_dotdot_and_containment_are_independently_tested() -> None:
    """变异审计: A0 的 ..、containment、symlink 三条互相遮蔽, 单独删任一条都不掉测试。
    这里各给一条只有它能拦的输入。"""
    fake = REPO_ROOT / "docs" / "release-evidence" / "rc-x" / "journeys" / "J01" / "manifest.json"
    # 只有 ".." in parts 拦得住 (containment 对 sub/../.. 之后仍在 base 内的形态无感)
    with pytest.raises(vrm._ArtifactPathError, match="上跳"):
        vrm.resolve_artifact_path("sub/../out.txt", fake)


def test_redteam_a2_does_not_echo_digest_for_repo_artifacts(tmp_path: Path, schema: dict) -> None:
    """R29: A2/A3 回显实际摘要 → CI 日志变成任意仓内文件的 hash/size oracle。"""
    manifest = _minimal_manifest()
    manifest["artifacts"].append({"path": "repo://README.md", "sha256": "e" * 64, "bytes": 1, "redacted": True})
    path = _write(tmp_path, manifest)
    problems = vrm.validate_manifest(path, schema, verify_artifacts=True)
    a2 = [p for p in problems if p.startswith("[A2]")]
    assert a2, problems
    assert "不回显" in a2[0]
    real_digest = hashlib.sha256((REPO_ROOT / "README.md").read_bytes()).hexdigest()
    assert real_digest not in "\n".join(problems), "实际摘要不得出现在输出里"


def test_redteam_a1_verified_by_default(tmp_path: Path, schema: dict) -> None:
    """R26: artifact 真验此前是 opt-in, 文档给的单文件命令根本不看产物存不存在。"""
    manifest = _minimal_manifest()
    manifest["artifacts"].append({"path": "ghost.log", "sha256": "b" * 64, "bytes": 5, "redacted": True})
    path = _write(tmp_path, manifest)
    assert any(p.startswith("[A1]") for p in vrm.validate_manifest(path, schema))
    assert vrm.validate_manifest(path, schema, verify_artifacts=False) == []


# ── RC 发布门 ──


def test_redteam_rc_gate_rejects_path_argument(tmp_path: Path) -> None:
    """R-BLOCKER: --require-complete 接受任意文件系统路径, 仓外伪造件也能满足发布门。"""
    problems = vrm.check_rc_completeness("../../tmp/whatever", root=tmp_path)
    assert problems and "不是合法的 rc 名" in problems[0], problems


def _seed_rc(root: Path, *, mode="live", level="E3", result="pass", sha=None, jids=None):
    for jid in jids or vrm.ALL_JOURNEYS:
        m = _minimal_manifest()
        m["journey_id"], m["rc"] = jid, "rc-1"
        m["provenance"] = (
            {"mode": "live", "unproven_fields": []}
            if mode == "live"
            else {"mode": mode, "reconstructed_from": "x", "unproven_fields": ["y"]}
        )
        m["evidence_level"], m["result"] = level, result
        if sha:
            m["candidate"]["sha"] = sha(jid) if callable(sha) else sha
        target = root / "rc-1" / "journeys" / jid / "manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")


def test_redteam_rc_gate_rejects_mixed_shas(tmp_path: Path) -> None:
    """R4 BLOCKER: 十条旅程跑在十个不同 commit 仍 PASS。"""
    _seed_rc(tmp_path, sha=lambda jid: f"{int(jid[1:]):040d}".replace("0", "a", 1))
    problems = vrm.check_rc_completeness("rc-1", root=tmp_path)
    assert any("同一个候选 SHA" in p for p in problems), problems


def test_redteam_rc_gate_rejects_failed_journeys(tmp_path: Path) -> None:
    """R4: 十条旅程全 result=fail、全 E0 仍 PASS。"""
    _seed_rc(tmp_path, level="E0", result="fail")
    problems = vrm.check_rc_completeness("rc-1", root=tmp_path)
    assert any("evidence_level" in p for p in problems), problems
    assert any("未通过的旅程" in p for p in problems), problems


def test_redteam_rc_gate_rejects_symlinked_journeys(tmp_path: Path) -> None:
    """R-HIGH: 一条真旅程软链九次即可"齐全"。"""
    _seed_rc(tmp_path, jids=["J01"])
    real = tmp_path / "rc-1" / "journeys" / "J01"
    for jid in vrm.ALL_JOURNEYS[1:]:
        (tmp_path / "rc-1" / "journeys" / jid).symlink_to(real, target_is_directory=True)
    problems = vrm.check_rc_completeness("rc-1", root=tmp_path)
    assert sum(1 for p in problems if "symlink" in p) == 9, problems


def test_redteam_rc_gate_passes_on_a_real_rc(tmp_path: Path) -> None:
    _seed_rc(tmp_path)
    assert vrm.check_rc_completeness("rc-1", root=tmp_path) == []


def test_redteam_discover_is_recursive(tmp_path: Path) -> None:
    """R28: 单层 glob 让深层嵌套的合法 manifest 对 CI 全扫永久隐形。"""
    nested = tmp_path / "2026-Q3" / "rc-nested" / "journeys" / "J01" / "manifest.json"
    nested.parent.mkdir(parents=True)
    nested.write_text("{}", encoding="utf-8")
    assert nested in vrm.discover_manifests(root=tmp_path)


def test_redteam_cli_one_bad_file_does_not_abort_the_batch(tmp_path: Path) -> None:
    """R-LOW: 一个手抖的逗号让整批中断, 且被报成"环境错误", 藏掉后面所有违规。"""
    good = _write(tmp_path, _minimal_manifest(), jid="J01")
    bad = tmp_path / "rc-test" / "journeys" / "J02" / "manifest.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("{oops", encoding="utf-8")
    proc = _cli(str(bad), str(good))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "[load]" in proc.stdout
    assert "PASS" in proc.stdout, "坏文件之后的好文件仍须被校验并报告"


def test_redteam_cli_skip_artifact_verify_is_announced(tmp_path: Path) -> None:
    proc = _cli(str(EXAMPLE), "--skip-artifact-verify")
    assert proc.returncode == 0
    assert "已弃权" in proc.stdout


def test_repo_example_declares_dirty_truthfully() -> None:
    """example-fidelity O4 回归: D5 执行期工作树确实是脏的, 示例必须如实写 true。"""
    doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert doc["candidate"]["dirty"] is True
    assert any("dirty" in k for k in doc["known_limitations"])


# ─────────────────────────────────────────────────────────────
# 10. 变异测试补漏 —— 这 9 条规则删掉后套件仍全绿, 说明零覆盖。
#     其中 4 条是 schema 先拦下的**防御深度**层, 用直达语义层的调用来考它们:
#     schema 与语义层是两道独立的门, 只测外面那道等于没测里面那道。
# ─────────────────────────────────────────────────────────────


def _semantic_only(manifest: dict, tmp_path: Path, *, jid: str = "J01") -> list[str]:
    """绕过结构层, 直接考语义层 (schema 先拦下的规则只能这样测)。"""
    target = tmp_path / manifest["rc"] / "journeys" / jid / "manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return vrm._semantic_checks(manifest, target)


def test_mutation_s1_non_ascii_version_caught_by_semantic_layer(tmp_path: Path) -> None:
    m = _minimal_manifest()
    m["schema_version"] = "１.٠.٠"  # 全角 1 + 两个阿拉伯-印度 0
    problems = _semantic_only(m, tmp_path)
    assert any(p.startswith("[S1]") and "非 ASCII" in p for p in problems), problems


def test_mutation_s2_zero_duration_journey_at_e3(tmp_path: Path, schema: dict) -> None:
    def mutate(m: dict) -> None:
        m["evidence_level"] = "E3"
        m["execution"]["finished_at"] = m["execution"]["started_at"]
        m["slo"] = {
            "manifest_revision": "v1",
            "measurements": [{"metric": "x", "threshold": "≤ 1s", "measured": "0.5s", "method": "t", "meets": True}],
        }

    problems = _problems(tmp_path, mutate)
    assert any(p.startswith("[S2]") and "耗时为 0" in p for p in problems), problems


def test_mutation_s10_live_with_reconstructed_from_caught_by_semantic_layer(
    tmp_path: Path,
) -> None:
    m = _minimal_manifest()
    m["provenance"] = {"mode": "live", "unproven_fields": [], "reconstructed_from": "旧归档"}
    problems = _semantic_only(m, tmp_path)
    assert any(p.startswith("[S10]") and "reconstructed_from" in p for p in problems), problems


def test_mutation_s11_unparseable_dogfood_dates_caught_by_semantic_layer(
    tmp_path: Path,
) -> None:
    m = _e5_manifest()
    m["release_gates"]["dogfood"].update(start_date="whenever", end_date="banana")
    problems = _semantic_only(m, tmp_path)
    assert any(p.startswith("[S11]") and "无法解析" in p for p in problems), problems


def test_mutation_s12_zero_byte_evidence_rejected(tmp_path: Path, schema: dict) -> None:
    """空文件不能当断言证据 (红队指出零字节产物满足'至少一件'的收窄)。"""
    manifest = _minimal_manifest()
    manifest["artifacts"] = [{"path": "empty.txt", "sha256": vrm._EMPTY_SHA256, "bytes": 0, "redacted": True}]
    manifest["assertions"][0]["evidence"] = "empty.txt"
    path = _write(tmp_path, manifest, with_artifact=False)
    (path.parent / "empty.txt").write_bytes(b"")
    problems = vrm.validate_manifest(path, schema)
    assert any(p.startswith("[S12]") and "0 字节" in p for p in problems), problems


def test_mutation_a1_unreadable_artifact_reported(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    path = _write(tmp_path, manifest)
    payload = path.parent / "out.txt"
    payload.chmod(0o000)
    try:
        # ⚠️ 先**独立探测**环境, 再无条件断言。早先写的是"problems 为空就 skip",
        # 结果规则被删掉时 problems 恰好为空 → 测试自己跳过 → 变异体存活。
        # skip 的判据必须来自环境本身, 不能来自被测物的输出。
        try:
            payload.read_bytes()
        except OSError:
            readable = False
        else:
            readable = True
        if readable:  # root 或某些文件系统上 chmod 无效
            pytest.skip("当前环境下 chmod 000 仍可读, 无法构造读取失败")
        problems = vrm.validate_manifest(path, schema)
    finally:
        payload.chmod(0o644)
    assert any(p.startswith("[A1]") and "读取失败" in p for p in problems), problems


def test_mutation_a3_repo_artifact_size_mismatch_does_not_echo(tmp_path: Path, schema: dict) -> None:
    manifest = _minimal_manifest()
    real_bytes = (REPO_ROOT / "README.md").read_bytes()
    manifest["artifacts"].append(
        {
            "path": "repo://README.md",
            "sha256": hashlib.sha256(real_bytes).hexdigest(),  # checksum 对, 只有字节数错
            "bytes": len(real_bytes) + 1,
            "redacted": True,
        }
    )
    path = _write(tmp_path, manifest)
    problems = vrm.validate_manifest(path, schema)
    a3 = [p for p in problems if p.startswith("[A3]")]
    assert a3, problems
    assert "不回显" in a3[0]
    assert str(len(real_bytes)) not in a3[0], "repo:// 目标的真实字节数不得回显"


def test_mutation_rc_gate_reports_unloadable_manifest(tmp_path: Path) -> None:
    _seed_rc(tmp_path, jids=vrm.ALL_JOURNEYS[1:])
    bad = tmp_path / "rc-1" / "journeys" / "J01" / "manifest.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("{oops", encoding="utf-8")
    problems = vrm.check_rc_completeness("rc-1", root=tmp_path)
    assert any("J01 装载失败" in p for p in problems), problems


def test_mutation_rc_gate_reports_non_object_manifest(tmp_path: Path) -> None:
    _seed_rc(tmp_path, jids=vrm.ALL_JOURNEYS[1:])
    bad = tmp_path / "rc-1" / "journeys" / "J01" / "manifest.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("[]", encoding="utf-8")
    problems = vrm.check_rc_completeness("rc-1", root=tmp_path)
    assert any("J01 顶层不是对象" in p for p in problems), problems
