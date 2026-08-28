"""CARD-G4-9: census_dead_letter_episodes.py 只读契约回归测试。

BATCH-2026-08-28-第五批 / CARD-G4-9（Codex round-9 必需项④）。

背景：该 census 脚本经 8 轮 Codex 对抗审查、37 项 findings 整改，其中 20+ 条
反例此前只在临时命令中验证过，未固化——round-9 明确指出"当前仓库没有任何测试
引用该生成器"。本文件把**每一条被实测封死的绕过**固化为回归测试，防止后续
改动（尤其 G4-10 复用时）悄悄回退。

每个用例的注释标注它对应哪一轮的哪条 finding，便于追溯。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "census_dead_letter_episodes.py"


def run_census(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def make_record(**overrides) -> dict:
    body = "x" * 200
    import hashlib

    rec = {
        "name": "session-archive:aaaaa11111",
        "episode_body": body,
        "group_id": "g",
        "source_description": "s",
        "reference_time": "t",
        "retry_count": 0,
        "created_at": "c",
        # 声明 sha 与 inline 不同 → truncated_prefix（模拟生产 [:200] 截断）
        "episode_body_sha256": hashlib.sha256((body + "more").encode()).hexdigest(),
        "episode_body_length": 500,
        "error": "e",
        "error_type": "BadRequestError",
        "failed_at": "f",
        "request_id": "r1",
    }
    rec.update(overrides)
    return rec


@pytest.fixture
def env(tmp_path: Path):
    """标准布局：dlq + transcripts 根（含一个匹配的 transcript）。"""
    proj = tmp_path / "proj" / "p"
    proj.mkdir(parents=True)
    transcript = proj / "aaaaa11111x.jsonl"
    transcript.write_text("{}\n", encoding="utf-8")
    dlq = tmp_path / "dlq.jsonl"
    dlq.write_text(json.dumps(make_record()) + "\n", encoding="utf-8")
    return {
        "tmp": tmp_path,
        "dlq": dlq,
        "root": tmp_path / "proj",
        "transcript": transcript,
        "out": tmp_path / "ledger.json",
    }


# ── 只读契约：静态自证 ────────────────────────────────────────────────


def test_no_truncation_calls_in_source():
    """round-7 架构整改：全文不得有任何截断调用（写出走 O_EXCL tmp + replace）。"""
    src = SCRIPT.read_text(encoding="utf-8")
    code_lines = [ln for ln in src.splitlines() if not ln.strip().startswith("#")]
    joined = "\n".join(code_lines)
    assert "os.ftruncate" not in joined
    assert ".truncate(" not in joined


def test_imports_are_stdlib_only():
    """卡面判据 (a)：无 Neo4j/Graphiti driver、无 app.* 依赖。"""
    src = SCRIPT.read_text(encoding="utf-8")
    import_lines = [ln for ln in src.splitlines() if ln.startswith(("import ", "from "))]
    joined = " ".join(import_lines).lower()
    for forbidden in ("neo4j", "graphiti", "bolt", "app."):
        assert forbidden not in joined, f"import 行不得出现 {forbidden}"


def test_no_apply_flag():
    """卡面判据 (a)：无 --apply（脚本不得有任何重放/写回入口）。"""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "add_argument" in src
    assert not any("apply" in ln for ln in src.splitlines() if "add_argument" in ln)


# ── --out 保护：不得截断任何输入或恢复源 ──────────────────────────────


def test_out_equal_to_dlq_refused(env):
    """round-1 BLOCKER-1：--out 指向 DLQ 自身必须拒绝且 DLQ 完好。"""
    before = env["dlq"].read_bytes()
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(env["dlq"]))
    assert r.returncode == 2
    assert env["dlq"].read_bytes() == before


def test_out_hardlink_to_dlq_refused(env):
    """round-2 BLOCKER-1：hardlink 别名绕过（resolve 字符串比较失效）。"""
    link = env["tmp"] / "hard.jsonl"
    os.link(env["dlq"], link)
    before = env["dlq"].read_bytes()
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(link))
    assert r.returncode == 2
    assert env["dlq"].read_bytes() == before


def test_out_inside_transcripts_root_refused(env):
    """round-6 架构整改：恢复源区域整体禁写（不依赖枚举完整性）。"""
    target = env["root"] / "p" / "aaaaa11111x.jsonl"
    before = target.read_bytes()
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(target))
    assert r.returncode == 2
    assert target.read_bytes() == before


def test_out_symlink_inside_root_refused(env):
    """round-8 BLOCKER③：POSIX rename 不解析末级 symlink —— 根内 symlink
    指向根外时，replace 替换的是根内目录项，须按父目录语义拒绝。"""
    outside = env["tmp"] / "outside.json"
    outside.write_text("OUTSIDE\n", encoding="utf-8")
    link = env["root"] / "p" / "link.json"
    link.symlink_to(outside)
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(link))
    assert r.returncode == 2
    assert link.is_symlink(), "根内 symlink 不得被 replace 替换"


def test_out_fifo_refused(env):
    """round-4 MEDIUM：非常规文件（FIFO）作 --out 须拒绝且不阻塞。"""
    fifo = env["tmp"] / "fifo_out"
    os.mkfifo(fifo)
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(fifo))
    assert r.returncode == 2


def test_out_hardlink_to_transcript_does_not_damage_source(env):
    """round-7 架构整改的核心保证：即便 --out 是指向恢复源的 hardlink，
    O_EXCL tmp + os.replace 也只重绑定该名字，**源 inode 内容不受损**。"""
    env["transcript"].write_text("IMPORTANT-SOURCE\n", encoding="utf-8")
    link = env["tmp"] / "outside_hardlink.jsonl"
    os.link(env["transcript"], link)
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(link))
    assert r.returncode == 0
    assert env["transcript"].read_text(encoding="utf-8") == "IMPORTANT-SOURCE\n"


# ── 可见性 fail-closed ────────────────────────────────────────────────


def test_missing_transcripts_root_refused(env):
    """round-3 HIGH-3：源不可见时拒绝裁定（不得产出 unrecoverable 假象）。"""
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["tmp"] / "nope"), "--out", str(env["out"]))
    assert r.returncode == 2


def test_scan_blocked_refuses_even_without_out(env):
    """round-8 HIGH：扫描受阻时 stdout 模式同样不得输出台账
    （拒绝条件不得写成 `scan_blocked and args.out`）。"""
    locked = env["root"] / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    try:
        r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]))
        assert r.returncode == 2
    finally:
        locked.chmod(0o755)


def test_unreadable_candidate_not_treated_as_source(env):
    """round-3/4：不可读候选不得被当作可用恢复源（须 fail-closed）。"""
    env["transcript"].chmod(0o000)
    try:
        r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(env["out"]))
        assert r.returncode == 0
        ledger = json.loads(env["out"].read_text(encoding="utf-8"))
        rec = ledger["records"][0]
        assert rec["recoverability"] == "unverifiable"
        assert rec["transcript_match_count"] == 0
    finally:
        env["transcript"].chmod(0o644)


# ── 判定 fail-closed ──────────────────────────────────────────────────


def test_anomaly_not_promoted_by_full_body(env, tmp_path):
    """round-4 HIGH-1：sha 对但声明长度矛盾的记录不得被判 byte_exact。"""
    import hashlib

    body = "abc"
    rec = make_record(
        episode_body=body,
        episode_body_full=body,
        episode_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        episode_body_length=999,
    )
    dlq = tmp_path / "anom.jsonl"
    dlq.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    out = tmp_path / "l.json"
    r = run_census("--dlq", str(dlq), "--transcripts-dir", str(env["root"]), "--out", str(out))
    assert r.returncode == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["records"][0]["inline_state"] == "anomaly"
    assert ledger["records"][0]["recoverability"] != "byte_exact"


def test_bool_length_rejected(env, tmp_path):
    """round-5 LOW：bool 是 int 子类 —— episode_body_length=True 不得过长度门。"""
    import hashlib

    body = "abc"
    rec = make_record(
        episode_body=body,
        episode_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        episode_body_length=True,
    )
    dlq = tmp_path / "b.jsonl"
    dlq.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    out = tmp_path / "l.json"
    r = run_census("--dlq", str(dlq), "--transcripts-dir", str(env["root"]), "--out", str(out))
    assert r.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["records"][0]["inline_state"] == "anomaly"


def test_bad_json_line_does_not_kill_census(env, tmp_path):
    """round-2 BLOCKER：单行毒药不得让整份 census 拒诊。"""
    dlq = tmp_path / "mixed.jsonl"
    dlq.write_text(json.dumps(make_record()) + "\nNOT-JSON\n\nnull\n", encoding="utf-8")
    out = tmp_path / "l.json"
    r = run_census("--dlq", str(dlq), "--transcripts-dir", str(env["root"]), "--out", str(out))
    assert r.returncode == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["total_records"] == 1
    reasons = {u["reason"].split(":")[0] for u in ledger["unparseable_lines"]}
    assert "json_error" in reasons or "blank_line" in reasons
    assert any("not_a_json_object" in u["reason"] for u in ledger["unparseable_lines"])


def test_invalid_utf8_line_is_unparseable(env, tmp_path):
    """round-4 MEDIUM：非法 UTF-8 不得经 errors=replace 冒充有效记录。"""
    dlq = tmp_path / "bad.jsonl"
    dlq.write_bytes(b'{"a":"\xff"}\n')
    out = tmp_path / "l.json"
    r = run_census("--dlq", str(dlq), "--transcripts-dir", str(env["root"]), "--out", str(out))
    assert r.returncode == 0
    ledger = json.loads(out.read_text(encoding="utf-8"))
    assert ledger["total_records"] == 0
    assert any("utf8_decode_error" in u["reason"] for u in ledger["unparseable_lines"])


def test_lone_lf_counts_as_one_line(env, tmp_path):
    """round-5 LOW：单独一个 LF 是一个空行，不是 0 行。"""
    dlq = tmp_path / "lf.jsonl"
    dlq.write_bytes(b"\n")
    out = tmp_path / "l.json"
    r = run_census("--dlq", str(dlq), "--transcripts-dir", str(env["root"]), "--out", str(out))
    assert r.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["dlq_file"]["line_count"] == 1


# ── 输出与运行不变量 ──────────────────────────────────────────────────


def test_output_is_private_and_no_tmp_left(env):
    """round-4/8：台账 mode 0600 且无 .census-tmp-* 残留。"""
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(env["out"]))
    assert r.returncode == 0
    assert env["out"].stat().st_mode & 0o777 == 0o600
    assert not list(env["out"].parent.glob(".*census-tmp-*"))


def test_inputs_unchanged_after_run(env):
    """卡面判据 (e)：运行前后输入文件字节不变（零写入）。"""
    import hashlib

    def digest(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    before = {p: digest(p) for p in (env["dlq"], env["transcript"])}
    r = run_census("--dlq", str(env["dlq"]), "--transcripts-dir", str(env["root"]), "--out", str(env["out"]))
    assert r.returncode == 0
    assert {p: digest(p) for p in before} == before
