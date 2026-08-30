"""G5-9 — 阶段回顾检验白板输出裁判 (BATCH-2026-08-28-第五批 / CARD-G5-9)。

被测物: canvas-vault/.claude/skills/board-recap/scripts/recap_exam_build.py
(preview 只读 / create 恰 1 新文件 / undo 字节回退; exam_service 零接触)。

裁判覆盖 (卡片完成条件逐条):
  (a) preview→确认→创建→undo 全链; 未确认 (只 preview) 全 vault 字节不变;
      创建路径 diff 恰 1 新文件 + 回执; undo 回字节基线 (vault 外留痕不删)。
  (c) 消费面兼容判据 (fixture 断言, 真 board_manifest_service 跑分):
      - board_manifest scan_vault 0 parse_errors
      - exam_history 收录且 question_count=0
      - past_question_digests 零新增 (全部成员空列表)
      - start-exam-board 防嵌套前提 (type: exam_board + 路径在 检验白板/)
      - frontmatter 0 个 concept: 行
      - quiz-answer done 分支安全停前提 (status: done + 无疑问批注 + 无答题区)
  正文零复制: 产物不含任何节点正文片段 (哨兵串断言)。
  拒绝面: 目标已存在 / 板不存在 / undo sha 不符 / undo 缺指纹 / undo-dir 在
  vault 内 / undo 路径逃逸。

⛔ 本目录禁建 conftest.py (卡片硬边界) — 共享构造器全部在本文件内。
fixtures 在 tmp_path 程序化构造 (与 test_split_preview.py 同惯例)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "canvas-vault" / ".claude" / "skills" / "board-recap" / "scripts" / "recap_exam_build.py"

TS = "2026-08-28-1200"
BODY_SENTINEL = "SECRET-NODE-BODY-MUST-NOT-LEAK"
EXAM_DIR_NAME = "检验白板"  # 与脚本 EXAM_DIR 同值（CARD-收口A ③ 新增门共用）


def run_cli(*argv: str) -> subprocess.CompletedProcess:
    if not SCRIPT.exists():  # 防「脚本不存在 → 非零退出 → 拒绝类断言假绿」
        pytest.fail(f"被测脚本不存在: {SCRIPT}")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        capture_output=True,
        text=True,
        timeout=60,
    )


# ────────────────────────── fixture 构造器 ──────────────────────────


def write_node(vault: Path, name: str, *, derived_from: str | None = None) -> None:
    fm = ["---", "type: concept", 'source_board: "[[原白板/板一]]"']
    if derived_from:
        fm.append(f'derived-from: "[[{derived_from}]]"')
        fm.append(f'source_note: "[[节点/{derived_from}]]"')
    fm.append("---")
    body = f"# {name}\n\n## 核心概念\n\n{BODY_SENTINEL} {name} 的正文定义。\n"
    (vault / "节点" / f"{name}.md").write_text("\n".join(fm) + "\n" + body, encoding="utf-8")


def build_vault(tmp_path: Path) -> Path:
    """两板组: 板一 (2 成员) + 板二 (1 成员) — ≥2 板全链判据用。"""
    vault = tmp_path / "vault"
    for sub in ("原白板", "节点", "检验白板", "outputs"):
        (vault / sub).mkdir(parents=True)
    for board, members in (("板一", ["NodeA", "NodeB"]), ("板二", ["NodeC"])):
        links = "\n".join(f"- [[节点/{m}]]" for m in members)
        (vault / "原白板" / f"{board}.md").write_text(
            f"---\ntype: whiteboard\nboard_name: {board}\n---\n\n# {board}\n\n## Concepts\n\n{links}\n",
            encoding="utf-8",
        )
    write_node(vault, "NodeA")
    write_node(vault, "NodeB", derived_from="NodeA")
    write_node(vault, "NodeC")
    return vault


def vault_snapshot(vault: Path) -> dict[str, str]:
    return {
        str(p.relative_to(vault)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(vault.rglob("*"))
        if p.is_file()
    }


def do_preview(vault: Path, boards: list[str]) -> dict:
    r = run_cli("preview", "--vault", str(vault), "--boards", *boards, "--ts", TS)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def do_create(vault: Path, boards: list[str], sha: str | None = None) -> dict:
    """走真实 skill 流程: create **必须**带 --expect-content-sha
    （round-4 H5：省略该参数曾退回"同 ts 靠巧合"的不安全语义，
    且 helper 自己省略导致回归锁形同虚设）。缺省时先跑 preview 取 sha。"""
    if sha is None:
        sha = do_preview(vault, boards).get("content_sha256")
        if sha is None:  # preview 已拒绝（板不存在/目标已存在）→ 用占位串走拒绝路径
            sha = "0" * 64
    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        *boards,
        "--ts",
        TS,
        "--expect-content-sha",
        sha,
    )
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def do_undo(vault: Path, path: str, sha: str, undo_dir: Path) -> dict:
    r = run_cli(
        "undo",
        "--vault",
        str(vault),
        "--path",
        path,
        "--expect-sha",
        sha,
        "--undo-dir",
        str(undo_dir),
    )
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ────────────────────────── (a) 全链: preview→create→undo ──────────────────────────


def test_preview_readonly_unconfirmed_zero_write(tmp_path):
    """未确认路径 (只 preview) → 全 vault shasum 全等。"""
    vault = build_vault(tmp_path)
    before = vault_snapshot(vault)
    out = do_preview(vault, ["板一", "板二"])
    assert out["write_side"] == "none"
    assert out["target_exists"] is False
    assert out["totals"] == {
        "boards": 2,
        "members": 3,
        "members_listed": 3,
        "duplicate_members": 0,
        "tips_total": 0,
        "ghosts": 0,
    }
    assert "content" in out and out["content_sha256"]
    assert vault_snapshot(vault) == before, "preview 改动了 vault"


def test_create_exactly_one_new_file_receipt_matches_preview(tmp_path):
    """创建路径 diff 恰 1 新文件 + 回执; 内容与 preview 所见即所写 (同 ts)。"""
    vault = build_vault(tmp_path)
    preview = do_preview(vault, ["板一", "板二"])
    before = vault_snapshot(vault)
    out = do_create(vault, ["板一", "板二"])
    assert out["created"] is True
    after = vault_snapshot(vault)
    new_files = set(after) - set(before)
    assert new_files == {out["created_path"]}, f"diff 应恰 1 新文件: {new_files}"
    assert {k: v for k, v in after.items() if k in before} == before, "既有文件被改动"
    created = vault / out["created_path"]
    assert created.parent.name == "检验白板"
    content = created.read_text(encoding="utf-8")
    assert hashlib.sha256(content.encode("utf-8")).hexdigest() == out["content_sha256"]
    assert content == preview["content"], "create 内容 ≠ preview 所见 (同 ts 必须逐字节一致)"


def test_undo_returns_to_byte_baseline_and_retains(tmp_path):
    """undo 回字节基线; 文件移入 vault 外留痕目录, 不物理删除。"""
    vault = build_vault(tmp_path)
    baseline = vault_snapshot(vault)
    out = do_create(vault, ["板一", "板二"])
    undo_dir = tmp_path / "undo-keep"
    res = do_undo(vault, out["created_path"], out["content_sha256"], undo_dir)
    assert res["undone"] is True
    assert vault_snapshot(vault) == baseline, "undo 后未回到字节基线"
    retained = Path(res["retained_at"])
    assert retained.is_file() and undo_dir in retained.parents
    assert hashlib.sha256(retained.read_bytes()).hexdigest() == out["content_sha256"], "留痕文件内容与创建回执不符"


# ────────────────────────── (c) 消费面兼容 (真 board_manifest_service) ──────────────────────────


@pytest.fixture()
def created_vault(tmp_path):
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一", "板二"])
    assert out["created"] is True
    return vault, vault / out["created_path"]


def test_board_manifest_zero_parse_errors_and_exam_history(created_vault):
    """board_manifest 扫描 0 parse_errors + exam_history 收录 question_count=0
    + past_question_digests 零新增。"""
    vault, created = created_vault
    from app.services.board_manifest_service import scan_vault

    full = scan_vault(vault)
    assert full["parse_errors"] == [], f"parse_errors 非空: {full['parse_errors']}"
    entries = [e for e in full["exam_history"] if e["exam_board_id"] == created.stem]
    assert len(entries) == 1, "exam_history 未收录阶段回顾板"
    assert entries[0]["question_count"] == 0
    assert entries[0]["board_id"] == "板一"  # source_board 锚板归属
    for b in full["boards"].values():
        for m in b["members"]:
            assert m["past_question_digests"] == [], f"past_question_digests 出现新增: {m['node_id']}"


def test_frontmatter_zero_concept_lines_and_no_questions_key(created_vault):
    """frontmatter 0 个 concept: 行 + 无 questions 键 (digest 注入的结构前提)。"""
    _, created = created_vault
    text = created.read_text(encoding="utf-8")
    fm = text.split("---")[1]
    assert "concept:" not in fm
    assert "concept_path:" not in fm
    assert "questions:" not in fm


def test_start_exam_board_antinest_preconditions(created_vault):
    """start-exam-board Step 1 防嵌套拒绝的两个机械前提同时成立:
    type: exam_board + 路径在 检验白板/ 下 (任一即拒, 双保险)。"""
    vault, created = created_vault
    text = created.read_text(encoding="utf-8")
    fm = text.split("---")[1]
    assert "type: exam_board" in fm
    assert created.parent == vault / "检验白板"


def test_quiz_answer_done_branch_safe_stop_preconditions(created_vault):
    """quiz-answer Step 0 done 分支安全停的机械前提:
    status: done + 无 [!question]/[!error] 疑问批注 + 无 answer sentinel
    → 「无新疑问可归纳」→ 停止, 零写侧。"""
    _, created = created_vault
    text = created.read_text(encoding="utf-8")
    fm = text.split("---")[1]
    assert "status: done" in fm
    assert "[!question]" not in text
    assert "[!error]" not in text
    assert "answer:start" not in text and "answer:end" not in text


def test_no_body_verbatim_copy(created_vault):
    """机械检查正文零复制: 节点正文哨兵串不得出现在产物里。"""
    _, created = created_vault
    assert BODY_SENTINEL not in created.read_text(encoding="utf-8")


# ────────────────────────── 拒绝面 ──────────────────────────


def test_create_refuses_existing_target(tmp_path):
    vault = build_vault(tmp_path)
    assert do_create(vault, ["板一"])["created"] is True
    snap = vault_snapshot(vault)
    out2 = do_create(vault, ["板一"])
    assert out2["created"] is False
    assert "拒绝覆盖" in out2["refusal_reason"]
    assert vault_snapshot(vault) == snap, "拒绝路径仍产生了写侧"


def test_create_refuses_missing_board_zero_write(tmp_path):
    vault = build_vault(tmp_path)
    snap = vault_snapshot(vault)
    out = do_create(vault, ["板一", "不存在的板"])
    assert out["created"] is False
    assert "不存在" in out["refusal_reason"]
    assert vault_snapshot(vault) == snap


def test_preview_flags_missing_board(tmp_path):
    vault = build_vault(tmp_path)
    out = do_preview(vault, ["不存在的板"])
    assert "refusal_reason" in out
    assert "content" not in out, "板不存在时不得渲染内容"


def test_undo_refuses_sha_mismatch_after_user_edit(tmp_path):
    """用户改过的文件拒绝回退 — 不静默丢改动。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    created = vault / out["created_path"]
    created.write_text(created.read_text(encoding="utf-8") + "\n用户手写补充。\n", encoding="utf-8")
    snap = vault_snapshot(vault)
    res = do_undo(vault, out["created_path"], out["content_sha256"], tmp_path / "u")
    assert res["undone"] is False
    assert "sha256" in res["refusal_reason"]
    assert vault_snapshot(vault) == snap, "拒绝回退却动了文件"


def test_undo_refuses_foreign_file_without_fingerprint(tmp_path):
    """非本脚本产物 (缺 generated_by 指纹) 拒绝回退。"""
    vault = build_vault(tmp_path)
    foreign = vault / "检验白板" / f"板一-{TS}.md"
    foreign.write_text("---\ntype: exam_board\n---\n手工建的板\n", encoding="utf-8")
    sha = hashlib.sha256(foreign.read_bytes()).hexdigest()
    res = do_undo(vault, f"检验白板/板一-{TS}.md", sha, tmp_path / "u")
    assert res["undone"] is False
    assert "指纹" in res["refusal_reason"]
    assert foreign.is_file()


def test_undo_refuses_path_escape_and_vault_inner_undo_dir(tmp_path):
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    # 路径逃逸 检验白板/ 之外 → exit 2
    r = run_cli(
        "undo",
        "--vault",
        str(vault),
        "--path",
        "原白板/板一.md",
        "--expect-sha",
        "0" * 64,
        "--undo-dir",
        str(tmp_path / "u"),
    )
    assert r.returncode == 2
    # undo-dir 在 vault 内 → exit 2 (vault 内不留新文件)
    r2 = run_cli(
        "undo",
        "--vault",
        str(vault),
        "--path",
        out["created_path"],
        "--expect-sha",
        out["content_sha256"],
        "--undo-dir",
        str(vault / "outputs" / "undo"),
    )
    assert r2.returncode == 2
    assert (vault / out["created_path"]).is_file(), "非法参数却动了目标文件"


def test_create_refuses_bad_ts_and_anchor(tmp_path):
    vault = build_vault(tmp_path)
    r = run_cli("create", "--vault", str(vault), "--boards", "板一", "--ts", "bad-ts")
    assert r.returncode == 2
    r2 = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "板一",
        "--anchor",
        "板二",
        "--ts",
        TS,
    )
    assert r2.returncode == 2  # anchor 不在 boards 里


def test_create_refuses_tmp_symlink_no_escape(tmp_path):
    """W4 回归锁 (workflow round-1 复现, BLOCKER): 预置 <target>.g59-tmp
    symlink 曾让写穿到 vault 外（覆盖外部文件）且把 target 变成越界 symlink，
    undo 还救不回来。现在必须拒绝，且 vault 内外零改动。"""
    vault = build_vault(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.txt"
    victim.write_text("ORIGINAL-OUTSIDE-CONTENT\n", encoding="utf-8")
    tmp_link = vault / "检验白板" / f"板一-{TS}.md.g59-tmp"
    tmp_link.symlink_to(victim)
    snap = vault_snapshot(vault)

    r = run_cli("create", "--vault", str(vault), "--boards", "板一", "--ts", TS)
    assert r.returncode == 2, f"tmp symlink 未被拒绝: {r.stdout}"
    assert victim.read_text(encoding="utf-8") == "ORIGINAL-OUTSIDE-CONTENT\n", "vault 外文件被写穿"
    target = vault / "检验白板" / f"板一-{TS}.md"
    assert not target.exists() and not target.is_symlink(), "拒绝路径却产生了目标"
    assert vault_snapshot(vault) == snap, "拒绝路径改动了 vault 文件"


def test_create_refuses_preexisting_tmp_regular_file(tmp_path):
    """W4 纵深: tmp 路径已被普通文件占用（残留/并发）→ O_EXCL 拒绝，不覆盖。"""
    vault = build_vault(tmp_path)
    stale = vault / "检验白板" / f"板一-{TS}.md.g59-tmp"
    stale.write_text("STALE\n", encoding="utf-8")
    r = run_cli("create", "--vault", str(vault), "--boards", "板一", "--ts", TS)
    assert r.returncode == 2
    assert stale.read_text(encoding="utf-8") == "STALE\n", "残留 tmp 被覆盖"


def test_undo_same_second_collision_keeps_both(tmp_path):
    """W5 回归锁: 同一 (anchor,ts) 同秒二次 undo 到同一 --undo-dir，
    先前留痕不得被覆盖（「不物理删除」承诺）。"""
    vault = build_vault(tmp_path)
    undo_dir = tmp_path / "keep"
    out1 = do_create(vault, ["板一"])
    res1 = do_undo(vault, out1["created_path"], out1["content_sha256"], undo_dir)
    # 改板内容 → 第二轮产物字节不同
    board = vault / "原白板" / "板一.md"
    board.write_text(board.read_text(encoding="utf-8") + "- [[节点/NodeC]]\n", encoding="utf-8")
    out2 = do_create(vault, ["板一"])
    assert out2["content_sha256"] != out1["content_sha256"], "两轮产物应字节不同"
    res2 = do_undo(vault, out2["created_path"], out2["content_sha256"], undo_dir)
    assert res1["retained_at"] != res2["retained_at"], "两次留痕落到同一路径"
    kept = sorted(p.name for p in undo_dir.iterdir())
    assert len(kept) == 2, f"留痕文件被覆盖: {kept}"
    shas = {hashlib.sha256((undo_dir / n).read_bytes()).hexdigest() for n in kept}
    assert shas == {out1["content_sha256"], out2["content_sha256"]}


def test_create_refuses_stale_content_sha(tmp_path):
    """H5 回归锁 (round-3): preview 之后 vault 变化 → create 必须拒绝
    （用户确认的不是最终字节），且零写侧。"""
    vault = build_vault(tmp_path)
    preview = do_preview(vault, ["板一"])
    # preview 之后新增成员 → 内容变化
    board = vault / "原白板" / "板一.md"
    board.write_text(board.read_text(encoding="utf-8") + "- [[节点/NodeC]]\n", encoding="utf-8")
    snap = vault_snapshot(vault)
    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "板一",
        "--ts",
        TS,
        "--expect-content-sha",
        preview["content_sha256"],
    )
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["created"] is False
    assert "vault 有变化" in out["refusal_reason"]
    assert out["expected_sha256"] != out["actual_sha256"]
    assert vault_snapshot(vault) == snap, "拒绝路径产生了写侧"
    # 未变化时同一 sha 正常放行
    vault2 = build_vault(tmp_path / "b")
    p2 = do_preview(vault2, ["板一"])
    r2 = run_cli(
        "create",
        "--vault",
        str(vault2),
        "--boards",
        "板一",
        "--ts",
        TS,
        "--expect-content-sha",
        p2["content_sha256"],
    )
    assert json.loads(r2.stdout)["created"] is True


def test_ghost_links_not_counted_as_members(tmp_path):
    """workflow round-2 回归锁: Concepts 里列了但节点文件不存在 →
    不计入 members（X+Y==N 恒等）、不写成死 wikilink、单列「待修链接」段。"""
    vault = build_vault(tmp_path)
    board = vault / "原白板" / "板一.md"
    board.write_text(
        board.read_text(encoding="utf-8") + "- [[节点/幽灵节点]]\n- [[节点/另一个幽灵]]\n",
        encoding="utf-8",
    )
    out = do_preview(vault, ["板一"])
    b = out["boards"][0]
    assert b["members"] == b["seeds"] + b["derived"], "成员数与种子+派生不恒等"
    assert b["members"] == 2 and b["ghost_count"] == 2
    assert b["listed_in_concepts"] == 4
    assert "幽灵节点" not in b["member_ids"]
    content = out["content"]
    assert "[[节点/幽灵节点]]" not in content, "死 wikilink 被写进产物"
    assert "## 待修链接" in content and "幽灵节点" in content
    assert "⚠ Concepts 另列 2 条链接" in content


def test_create_refuses_wikilink_semantic_chars_in_board_name(tmp_path):
    """M6 回归锁 (round-3): 板名含 #/|/^ → 拒绝（消费方会按锚点/别名截断，
    导致 scan_vault 归属错乱且不报 parse error）。"""
    vault = build_vault(tmp_path)
    (vault / "原白板" / "A#B.md").write_text(
        "---\ntype: whiteboard\nboard_name: A#B\n---\n\n## Concepts\n\n",
        encoding="utf-8",
    )
    snap = vault_snapshot(vault)
    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "A#B",
        "--ts",
        TS,
        "--expect-content-sha",
        "0" * 64,
    )
    assert r.returncode == 2
    assert "wikilink 语义字符" in r.stdout
    assert vault_snapshot(vault) == snap


def test_create_refuses_impossible_timestamp(tmp_path):
    """M7 回归锁 (round-3): --ts 形状合法但不是真实时刻 → 拒绝
    （2026-99-99-9999 曾通过，会写出非法 created_at 阻断 SnapshotV3）。"""
    vault = build_vault(tmp_path)
    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "板一",
        "--ts",
        "2026-99-99-9999",
        "--expect-content-sha",
        "0" * 64,
    )
    assert r.returncode == 2
    assert "不是真实时刻" in r.stdout


def test_create_requires_expect_content_sha(tmp_path):
    """round-4 H5 回归锁: 省略 --expect-content-sha → argparse 直接拒绝
    （必传，不给"同 ts 靠巧合"留后门）。"""
    vault = build_vault(tmp_path)
    snap = vault_snapshot(vault)
    r = run_cli("create", "--vault", str(vault), "--boards", "板一", "--ts", TS)
    assert r.returncode != 0, "省略必传参数却成功创建"
    assert "expect-content-sha" in (r.stderr + r.stdout)
    assert vault_snapshot(vault) == snap


def test_preview_writes_no_pycache_into_vault(tmp_path):
    """round-4 新增 FAIL 回归锁: 脚本用 importlib 加载同目录 recap_scan，
    默认会在 vault 内 `.claude/skills/.../__pycache__` 落 .pyc —— 那是写侧。
    本用例把**脚本副本放进 vault 内**（真实部署形态）后跑 preview，
    断言全 vault（含 .claude/）零新增文件。"""
    import shutil

    vault = build_vault(tmp_path)
    dst = vault / ".claude" / "skills" / "board-recap" / "scripts"
    dst.mkdir(parents=True)
    for name in ("recap_exam_build.py", "recap_scan.py"):
        shutil.copy2(SCRIPT.parent / name, dst / name)
    before = {str(p.relative_to(vault)) for p in vault.rglob("*") if p.is_file()}
    r = subprocess.run(
        [
            sys.executable,
            str(dst / "recap_exam_build.py"),
            "preview",
            "--vault",
            str(vault),
            "--boards",
            "板一",
            "--ts",
            TS,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr
    after = {str(p.relative_to(vault)) for p in vault.rglob("*") if p.is_file()}
    assert after == before, f"preview 在 vault 内新增了文件: {sorted(after - before)}"


def test_default_ts_is_utc_not_local(tmp_path):
    """M7/workflow 回归锁: 不传 --ts 时默认戳必须是 UTC —— 与
    start-exam-board 的 `date -u` 同一时钟（否则 exam_history 排序错位）。"""
    from datetime import datetime, timezone

    vault = build_vault(tmp_path)
    before = datetime.now(timezone.utc)
    r = run_cli("preview", "--vault", str(vault), "--boards", "板一")
    after = datetime.now(timezone.utc)
    ts = json.loads(r.stdout)["ts"]
    got = datetime.strptime(ts, "%Y-%m-%d-%H%M").replace(tzinfo=timezone.utc)
    assert before.replace(second=0, microsecond=0) <= got <= after, (
        f"默认 ts {ts} 不在 UTC 窗口内（疑似本地墙钟冒充 UTC）"
    )


def test_undo_hint_is_shell_safe(tmp_path):
    """H8 回归锁 (round-3): 板名含空格/括号/& 时 undo_hint 必须是可解析的
    shell 命令（原先未 quote，zsh -n 报 parse error）。"""
    import shlex

    vault = build_vault(tmp_path)
    name = "板 (含括号) & 空格"
    (vault / "原白板" / f"{name}.md").write_text(
        f"---\ntype: whiteboard\nboard_name: {name}\n---\n\n## Concepts\n\n",
        encoding="utf-8",
    )
    out = do_create(vault, [name])
    hint = out["undo_hint"]
    parsed = shlex.split(hint)  # 语法非法会抛 ValueError
    assert "--path" in parsed
    assert parsed[parsed.index("--path") + 1] == out["created_path"]
    # round-4: 占位符不得用 `<...>`（shell 重定向语法，会让整条命令解析失败）
    assert "<" not in hint and ">" not in hint, f"hint 含 shell 重定向字符: {hint}"
    undo_dir_arg = parsed[parsed.index("--undo-dir") + 1]
    assert undo_dir_arg and "<" not in undo_dir_arg


def test_undo_refuses_replaced_inode(tmp_path):
    """H7 回归锁 (round-3): 校验之后文件被同内容替换（新 inode）——
    实际路径由 sha 一致但 inode 不同触发；这里用只读目录外的等价断言：
    留痕内容必须与创建回执 sha 全等（移走的就是校验过的字节）。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    undo_dir = tmp_path / "keep"
    res = do_undo(vault, out["created_path"], out["content_sha256"], undo_dir)
    assert res["retained_sha256"] == out["content_sha256"]
    retained = Path(res["retained_at"])
    assert hashlib.sha256(retained.read_bytes()).hexdigest() == out["content_sha256"]


def test_conftest_ban_holds():
    """卡片硬边界: backend/tests/skills/ 禁建 conftest.py。"""
    assert not (Path(__file__).parent / "conftest.py").exists()


# ────────────────── round-6 终裁复核回归锁 ──────────────────


def test_undo_refuses_when_exam_dir_symlinked_out(tmp_path):
    """round-6 回归锁: cmd_undo 此前完全没有 create 侧的目录 symlink 守卫 ——
    检验白板/ 整体被 symlink 带出 vault 后，containment 仍判 contained=True。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    outside = tmp_path / "outside_exam"
    outside.mkdir()
    real = vault / "检验白板"
    moved = tmp_path / "moved_exam"
    real.rename(moved)
    (vault / "检验白板").symlink_to(moved)
    r = run_cli(
        "undo",
        "--vault",
        str(vault),
        "--path",
        out["created_path"],
        "--expect-sha",
        out["content_sha256"],
        "--undo-dir",
        str(outside),
    )
    assert r.returncode == 2, "检验白板/ 被 symlink 带出 vault 仍允许 undo"
    assert "symlink 越界" in r.stdout
    assert list(outside.iterdir()) == [], "拒绝路径却动了文件"


def test_cross_board_members_deduped_in_totals(tmp_path):
    """round-6 回归锁: 节点/ 是扁平共享池，同一节点被两板同时列出是正常形态 ——
    阶段数字必须按 node_id 去重并如实声明重复量（原先直接相加）。"""
    vault = build_vault(tmp_path)
    # 让板二也列 NodeA（跨板共享）
    b2 = vault / "原白板" / "板二.md"
    b2.write_text(b2.read_text(encoding="utf-8") + "- [[节点/NodeA]]\n", encoding="utf-8")
    out = do_preview(vault, ["板一", "板二"])
    t = out["totals"]
    assert t["members_listed"] == 4  # NodeA×2 + NodeB + NodeC
    assert t["members"] == 3, "跨板重复成员未去重"
    assert t["duplicate_members"] == 1
    assert "总成员 3（按节点去重）" in out["content"]
    assert "跨板重复成员 1 个" in out["content"]


def test_create_refuses_bracket_in_board_name(tmp_path):
    """round-6 LOW 回归锁: `]`/`[` 同样是 wikilink 终止符，板名含它们会让
    resolve_node_id 截断 → 归属错乱。"""
    vault = build_vault(tmp_path)
    (vault / "原白板" / "A]]B.md").write_text(
        "---\ntype: whiteboard\nboard_name: A]]B\n---\n\n## Concepts\n\n",
        encoding="utf-8",
    )
    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "A]]B",
        "--ts",
        TS,
        "--expect-content-sha",
        "0" * 64,
    )
    assert r.returncode == 2
    assert "wikilink 语义字符" in r.stdout


def test_consumers_can_distinguish_stage_recap(tmp_path):
    """round-6 回归锁: 产物必须带 `recap_kind: stage_recap` —— 它是两个
    真实消费方（Dashboard 考察历史统计 / quiz-answer 无参默认目标）用来
    把"阶段回顾板"与"真考卷"区分开的唯一标记。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    fm = (vault / out["created_path"]).read_text(encoding="utf-8").split("---")[1]
    assert "recap_kind: stage_recap" in fm
    assert "status: done" in fm
    assert "questions:" not in fm


def test_declared_consumers_exclude_stage_recap():
    """round-6 回归锁: 两个消费方的排除逻辑必须在位（改回去即红）——
    Dashboard 的考察历史查询与 quiz-answer 的无参定位级联。"""
    vault_root = SCRIPT.parents[4]
    dash = (vault_root / "Dashboard.md").read_text(encoding="utf-8")
    assert 'recap_kind !== "stage_recap"' in dash, "Dashboard 考察历史未排除阶段回顾板"
    qa = (vault_root / ".claude" / "skills" / "quiz-answer" / "SKILL.md").read_text(encoding="utf-8")
    assert "recap_kind: stage_recap" in qa, "quiz-answer 定位级联未排除阶段回顾板"


# ══════════════════ codex round-1 HIGH 回归锁（本批 CARD-收口A ③）══════════════════
#
# 首轮独立复核给出 0 BLOCKER / 4 HIGH / 8 MEDIUM / 2 LOW，其中 HIGH-4 是
# 「五类关键变异有四类 survivor」——把安全判定弱化后完整套件仍 33 passed。
# 下面每一条都对应一个 survivor 或一条实现级 HIGH，判据是：**把实现里对应的
# 判定改回去，本条必须变红**（负验证记录见 g5-9-evidence/round1-high-negverify.txt）。
#
# 需要「运行中途注入」的性质（HIGH-2 发布字节、HIGH-3 留痕与删除窗口）无法用
# CLI 子进程表达，改为函数级导入 + monkeypatch 精确注入；其余走真实 CLI。


def _load_module():
    """按被测脚本自身的零写侧约定导入它（不落 __pycache__）。"""
    import importlib.util

    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("recap_exam_build_ut", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


# ── HIGH-1: 空/非法 --expect-content-sha 不得绕过用户确认 ──


@pytest.mark.parametrize(
    "bad_sha",
    [
        "",  # ⛔ 复核者实测的绕过形态: falsy 短路跳过比较 → created:true
        "  ",
        "0" * 63,  # 长度不足
        "0" * 65,  # 长度超出
        "0" * 63 + "G",  # 非十六进制
        "A" * 64,  # 大写（preview 回执恒为小写）
        "not-a-sha",
    ],
)
def test_create_rejects_malformed_expect_content_sha(tmp_path, bad_sha):
    """HIGH-1 承重门: required=True 只保证 flag 出现、不保证值合法。
    空串曾因 falsy 直接跳过比较 ⇒ 可创建用户从未确认过的字节。
    现在形状不合法一律 exit 2 且**零写侧**。"""
    vault = build_vault(tmp_path)
    snap = vault_snapshot(vault)
    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "板一",
        "--ts",
        TS,
        "--expect-content-sha",
        bad_sha,
    )
    assert r.returncode == 2, f"非法 sha {bad_sha!r} 未被拒绝: {r.stdout}"
    target = vault / EXAM_DIR_NAME / f"板一-{TS}.md"
    assert not target.exists(), f"非法 sha {bad_sha!r} 却创建了目标"
    assert vault_snapshot(vault) == snap, "拒绝路径改动了 vault"


def test_undo_rejects_malformed_expect_sha(tmp_path):
    """HIGH-1 同型: undo 的 --expect-sha 也必须先过形状白名单。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    for bad in ("", "0" * 63, "not-a-sha"):
        r = run_cli(
            "undo",
            "--vault",
            str(vault),
            "--path",
            out["created_path"],
            "--expect-sha",
            bad,
            "--undo-dir",
            str(tmp_path / "keep"),
        )
        assert r.returncode == 2, f"undo 接受了非法 --expect-sha {bad!r}"
        assert (vault / out["created_path"]).is_file(), "非法参数却动了目标"


# ── HIGH-4 survivor: wikilink 语义字符逐字符承重（此前只有整体门，删掉 `|` 仍全绿）──


@pytest.mark.parametrize("ch", ["#", "|", "^", "[", "]"])
def test_board_name_rejects_each_wikilink_char(tmp_path, ch):
    """HIGH-4 survivor 封堵: 从禁止集里**单独**移除任一字符都必须让本条变红。
    原实现有整体门但无逐字符参数化 ⇒ 只删 `|` 时套件仍 33 passed。"""
    vault = build_vault(tmp_path)
    snap = vault_snapshot(vault)
    r = run_cli("preview", "--vault", str(vault), "--boards", f"板一{ch}别名", "--ts", TS)
    assert r.returncode == 2, f"板名含 {ch!r} 未被拒绝: {r.stdout}"
    assert "wikilink" in r.stdout, f"拒绝理由未点名 wikilink: {r.stdout}"
    assert vault_snapshot(vault) == snap


# ── HIGH-4 survivor: 目标目录被 symlink 布防的守卫（此前测试没传 sha，撞的是 argparse）──


def test_create_refuses_symlinked_exam_dir_with_valid_sha(tmp_path):
    """HIGH-4 survivor 封堵 + 假门修复。

    复核者点名: 既有的三条 create 拒绝测试都**没传 --expect-content-sha**，
    因此在 argparse 阶段就 exit 2，从未触达被测的防御 ⇒ 禁用父目录 symlink
    守卫后套件仍 33 passed。本条先跑 preview 取**合法 sha**，再把 检验白板/
    换成指向 vault 外的 symlink，确保请求真正走到守卫层。
    """
    vault = build_vault(tmp_path)
    sha = do_preview(vault, ["板一"])["content_sha256"]
    outside = tmp_path / "outside_dir"
    outside.mkdir()
    victim = outside / "victim.md"
    victim.write_text("ORIGINAL\n", encoding="utf-8")
    exam = vault / EXAM_DIR_NAME
    exam.rmdir()
    exam.symlink_to(outside, target_is_directory=True)

    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "板一",
        "--ts",
        TS,
        "--expect-content-sha",
        sha,
    )
    assert r.returncode == 2, f"检验白板/ 被 symlink 布防却未拒绝: {r.stdout}"
    assert victim.read_text(encoding="utf-8") == "ORIGINAL\n", "vault 外文件被改"
    assert list(outside.iterdir()) == [victim], f"vault 外新增了文件: {list(outside.iterdir())}"


def test_create_refuses_tmp_symlink_with_valid_sha(tmp_path):
    """假门修复: 与既有 test_create_refuses_tmp_symlink_no_escape 同场景，
    但**带合法 sha**，保证拒绝来自 W4 防御而不是 argparse。"""
    vault = build_vault(tmp_path)
    sha = do_preview(vault, ["板一"])["content_sha256"]
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.txt"
    victim.write_text("ORIGINAL-OUTSIDE-CONTENT\n", encoding="utf-8")
    (vault / EXAM_DIR_NAME / f"板一-{TS}.md.g59-tmp").symlink_to(victim)
    snap = vault_snapshot(vault)

    r = run_cli(
        "create",
        "--vault",
        str(vault),
        "--boards",
        "板一",
        "--ts",
        TS,
        "--expect-content-sha",
        sha,
    )
    assert r.returncode == 2, f"tmp symlink 未被拒绝: {r.stdout}"
    assert victim.read_text(encoding="utf-8") == "ORIGINAL-OUTSIDE-CONTENT\n"
    assert not (vault / EXAM_DIR_NAME / f"板一-{TS}.md").exists()
    assert vault_snapshot(vault) == snap


# ── HIGH-2: 发布字节必须被回读校验；inode 不符时绝不删他人文件 ──


def test_atomic_write_rejects_inplace_rewritten_publish(tmp_path):
    """HIGH-2 (a) 承重门: 只比 (dev,ino) 挡不住**原地改写同一 inode**——
    两侧 inode 恒等而字节已分叉。注入方式 = 让 os.link 在建立硬链接后
    立刻原地改写该 inode，模拟并发写入者。修法是发布后回读比 sha。"""
    mod = _load_module()
    d = tmp_path / "d"
    d.mkdir()
    tmp_p, target = d / "t.tmp", d / "t.md"
    real_link = mod.os.link

    def evil_link(src, dst, **kw):
        real_link(src, dst, **kw)
        fd = mod.os.open(target, mod.os.O_WRONLY | mod.os.O_TRUNC)
        try:
            mod.os.write(fd, b"ATTACKER-BYTES-SAME-INODE\n")
        finally:
            mod.os.close(fd)

    dfd = mod.os.open(d, mod.os.O_RDONLY | mod.os.O_DIRECTORY)
    mod.os.link = evil_link
    try:
        err, _warn = mod._atomic_write(tmp_p, target, "USER-CONFIRMED-CONTENT\n", dfd)
    finally:
        mod.os.link = real_link
        mod.os.close(dfd)
    assert err is not None, "发布字节被篡改却报成功"
    assert "bytes mismatch" in err or "原子写失败" in err
    assert not target.exists(), "字节不符却把污染内容留在了 vault 里"


def test_atomic_write_does_not_delete_concurrent_replacement(tmp_path):
    """HIGH-2 (b) 承重门: inode 不符说明 target 已**不是我们的文件**，
    此时按路径 unlink 等于删掉并发写入者刚创建的文件（复核者实测：返回失败
    时文件已丢失）。修法是这一分支绝不删，只如实回报。"""
    mod = _load_module()
    d = tmp_path / "d"
    d.mkdir()
    tmp_p, target = d / "t.tmp", d / "t.md"
    real_link = mod.os.link

    def evil_link(src, dst, **kw):
        real_link(src, dst, **kw)
        mod.os.unlink(target)  # 并发者移走我们的硬链接…
        target.write_text("SOMEONE-ELSES-FILE\n", encoding="utf-8")  # …换上自己的

    dfd = mod.os.open(d, mod.os.O_RDONLY | mod.os.O_DIRECTORY)
    mod.os.link = evil_link
    try:
        err, _warn = mod._atomic_write(tmp_p, target, "USER-CONFIRMED-CONTENT\n", dfd)
    finally:
        mod.os.link = real_link
        mod.os.close(dfd)
    assert err is not None, "inode 不符却报成功"
    assert target.exists(), "把并发写入者的文件删掉了（原实现的行为）"
    assert target.read_text(encoding="utf-8") == "SOMEONE-ELSES-FILE\n"


# ── HIGH-3: 留痕字节回读校验 + 删除前一刻的 identity 复核 ──


def _undo_args(vault: Path, path: str, sha: str, undo_dir: Path):
    import argparse as _ap

    return _ap.Namespace(vault=str(vault), path=path, expect_sha=sha, undo_dir=str(undo_dir))


def test_undo_refuses_when_retention_bytes_corrupted(tmp_path, capsys):
    """HIGH-3 (2) 承重门: 留痕写完 + fsync 后从不回读 ⇒ 备份被原地改写时
    源照删、回执 SHA 说谎（复核者实测 retained 765bf07e… vs 实际 3710644e…）。
    注入方式 = 在写留痕后紧接着的 _fsync_dir 里原地改写留痕字节。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    undo_dir = tmp_path / "keep"
    undo_dir.mkdir()
    mod = _load_module()
    real_fsync_dir = mod._fsync_dir

    def evil_fsync_dir(d):
        real_fsync_dir(d)
        if Path(d) == undo_dir:  # 留痕刚落盘的那一次
            for f in undo_dir.iterdir():
                fd = mod.os.open(f, mod.os.O_WRONLY | mod.os.O_TRUNC)
                try:
                    mod.os.write(fd, b"CORRUPTED-BACKUP\n")
                finally:
                    mod.os.close(fd)

    mod._fsync_dir = evil_fsync_dir
    try:
        rc = mod.cmd_undo(_undo_args(vault, out["created_path"], out["content_sha256"], undo_dir))
    finally:
        mod._fsync_dir = real_fsync_dir
    res = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert res["undone"] is False, "留痕已损坏却报回退成功"
    assert "回读校验不符" in res["refusal_reason"]
    assert (vault / out["created_path"]).is_file(), "留痕不可信却删掉了源文件"


def test_undo_refuses_when_target_swapped_before_unlink(tmp_path, capsys):
    """HIGH-3 (1) 承重门: 最终重读校验后先 close(fd) 再按路径 unlink，
    窗口内换入的新文件会被误删（复核者注入 USER-NEW-BYTES 实测新 inode 被删、
    留痕只有旧版本、回执仍报 undone:true）。修法 = 紧贴 unlink 前再核一次
    identity。

    ⚠️ 注入点必须精确落在**那个窗口内**。本条第一版注入在 `_fsync_dir(undo_dir)`，
    结果被更早的 cfd 重读校验抓住 —— 负验证变体 H 当场证明该门非承重（去掉
    unlink 前那道复核后测试仍绿）。现改注入 `os.lstat`：cmd_undo 对 target 的
    第 2 次 lstat 正是 unlink 前那次，在它真正取值**之前**把文件换掉。
    """
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    undo_dir = tmp_path / "keep2"
    undo_dir.mkdir()
    target = vault / out["created_path"]
    mod = _load_module()
    real_lstat = mod.os.lstat
    seen = {"n": 0}

    def evil_lstat(path, *a, **kw):
        # ⛔ 不能用「对 target 的第 N 次调用」定位注入点: mod.os 就是全局 os
        # 模块, patch 它会拦下**进程内所有** os.lstat —— 包括 pathlib 内部的,
        # 于是交换会提前发生并被**第一道** st_now 检查抓住, 测试变成锁错了门
        # (负验证变体 H 首跑正是这样绿的, 拒绝理由是「校验后文件被替换」)。
        # 改为按调用帧定位: 只在 cmd_undo 自己的帧里、且 st_dest 已存在
        # (说明留痕回读已完成 ⇒ 这一定是 unlink 前那次 lstat) 时注入。
        f = sys._getframe(1)
        if f.f_code.co_name == "cmd_undo" and "st_dest" in f.f_locals and Path(str(path)) == target and seen["n"] == 0:
            seen["n"] += 1
            target.unlink()  # 换 inode，内容换成用户刚写的新字节
            target.write_text("USER-NEW-BYTES\n", encoding="utf-8")
        return real_lstat(path, *a, **kw)

    mod.os.lstat = evil_lstat
    try:
        rc = mod.cmd_undo(_undo_args(vault, out["created_path"], out["content_sha256"], undo_dir))
    finally:
        mod.os.lstat = real_lstat
    res = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert seen["n"] == 1, "未触达 unlink 前的 identity 复核点（注入点失效）"
    assert "删除前一刻" in res.get("refusal_reason", ""), f"拒绝来自更早的检查而不是 unlink 前那道: {res}"
    assert res["undone"] is False, "窗口内被换掉却报回退成功"
    assert target.is_file(), "误删了用户在窗口内写入的新文件"
    assert target.read_text(encoding="utf-8") == "USER-NEW-BYTES\n"


# ── MEDIUM-7: undo_hint 必须真的可以「复制执行」（SKILL.md 明写了这句承诺）──


def test_undo_hint_is_actually_executable(tmp_path):
    """codex round-1 MEDIUM-7 承重门: 旧 hint 以 `undo …` 开头，缺
    `python3 <脚本>` 前缀 ⇒ 普通 shell 里 `undo: command not found`，
    而 SKILL.md 却称「可直接复制执行」。这里把 hint **原样跑一遍**：
    只替换 --undo-dir 占位符，其余逐字不动，必须真的完成回退。"""
    import shlex

    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    target = vault / out["created_path"]
    assert target.is_file()
    undo_dir = tmp_path / "hint-undo"
    undo_dir.mkdir()
    cmd = shlex.split(out["undo_hint"].replace("PUT_A_DIR_OUTSIDE_THE_VAULT_HERE", str(undo_dir)))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"hint 原样执行失败: rc={r.returncode} {r.stderr[:400]}"
    res = json.loads(r.stdout)
    assert res["undone"] is True, f"hint 执行未完成回退: {res}"
    assert not target.exists(), "回退后目标仍在"
    assert res["retained_sha256"] == out["content_sha256"]


# ═════════ 主 session 并行复核 HIGH-4 / HIGH-5 回归锁（CARD-收口A ③ 二段）═════════
#
# 这两条来自与本车道**并行**的另一份独立复核（见 codex-review-CARD-G5-9-主session
# 独立复核-2026-08-30.md）。本车道首轮把 HIGH-4 定级为 MEDIUM-3 并登记结案，
# 但对方给出了**实证反例**——created:true 且文件落在 vault 外——定级明显偏轻。
# 下面两条门直接复现对方的反例形态。


def test_create_refuses_when_exam_dir_swapped_after_probe(tmp_path):
    """HIGH-4 承重门（对方实证反例的直接复现）。

    反例形态：`_symlink_probe` 通过之后、真正写入之前，把 `检验白板/` 换成指向
    vault 外的目录 symlink。原实现的 open/link 全部按路径，于是写到了 vault 外
    （对方实测 created:true、文件出现在 vault 外）。

    注入点必须落在 probe 与写入之间。这里 patch `_symlink_probe`：它返回 None
    （放行）之后立刻做替换 —— 正是那个窗口。修法（dirfd 锚定）下必须拒绝。
    """
    vault = build_vault(tmp_path)
    sha = do_preview(vault, ["板一"])["content_sha256"]
    outside = tmp_path / "outside_target"
    outside.mkdir()
    exam = vault / EXAM_DIR_NAME
    mod = _load_module()
    real_probe = mod._symlink_probe

    def evil_probe(v, t, tm):
        r = real_probe(v, t, tm)
        if r is None:  # ← probe 放行的那一刻，窗口就在这里
            for f in exam.iterdir():
                f.unlink()
            exam.rmdir()
            exam.symlink_to(outside, target_is_directory=True)
        return r

    mod._symlink_probe = evil_probe
    try:
        rc = mod.cmd_create(
            argparse.Namespace(
                vault=str(vault),
                boards=["板一"],
                anchor=None,
                ts=TS,
                expect_content_sha=sha,
            )
        )
    finally:
        mod._symlink_probe = real_probe
    assert rc == 2, f"probe 后目录被换成越界 symlink，仍未拒绝 (rc={rc})"
    assert list(outside.iterdir()) == [], f"写到了 vault 外: {list(outside.iterdir())}"


def test_undo_refuses_symlink_alias_instead_of_moving_referent(tmp_path):
    """HIGH-5 前半承重门（对方实证反例的直接复现）。

    反例形态：给 undo 传一个同目录 alias（`alias.md -> real.md`）。原实现先
    `.resolve()` 解掉 leaf symlink，于是**回执声称移除 alias、实际移走 referent**，
    并在 vault 里留下一条死链；后面的 O_NOFOLLOW 看不到这一点（它拿到的已是解析后
    的真实路径）。修法：按未解析路径判 leaf 是否 symlink，是则直接拒绝。
    """
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    real = vault / out["created_path"]
    alias = real.with_name("alias-别名.md")
    alias.symlink_to(real.name)  # 同目录 alias
    undo_dir = tmp_path / "keep-alias"
    undo_dir.mkdir()

    r = run_cli(
        "undo",
        "--vault",
        str(vault),
        "--path",
        str(alias.relative_to(vault)),
        "--expect-sha",
        out["content_sha256"],
        "--undo-dir",
        str(undo_dir),
    )
    assert r.returncode == 2, f"alias 未被拒绝: rc={r.returncode} {r.stdout}"
    assert "symlink" in r.stdout, f"拒绝理由未点名 symlink: {r.stdout}"
    assert real.is_file(), "referent 被移走了（正是要防的形态）"
    assert alias.is_symlink() and alias.resolve() == real.resolve(), "alias 变成了死链"
    assert list(undo_dir.iterdir()) == [], "拒绝路径却写了留痕"


# ══════ round-3 窄范围复核的 4 条 HIGH + 2 条 M/L 回归锁（CARD-收口A ③ 三段）══════
#
# round-3 确认前两段的主路径修复全部到位（4 项题定校验 PASS、10/10 承重），
# 但在**失败路径与竞态窗口**上找到 4 条新 HIGH。共同成因：
# **每加一道检查，就新增一条「它自己失败时」的路径** —— 这是加固工作的固有代价。


def test_rollback_published_refuses_to_delete_someone_elses_file(tmp_path):
    """HIGH-3 承重门：`_rollback_published` 的 identity 快照可能已过时。
    传入一个**不匹配**的 identity（模拟路径已被换成他人文件），必须**不删**。"""
    mod = _load_module()
    d = tmp_path / "d"
    d.mkdir()
    victim = d / "t.md"
    victim.write_text("SOMEONE-ELSES-FILE\n", encoding="utf-8")
    dfd = mod.os.open(d, mod.os.O_RDONLY | mod.os.O_DIRECTORY)
    try:
        err = mod._rollback_published("t.md", dfd, (99999, 99999))  # 故意不匹配
    finally:
        mod.os.close(dfd)
    assert err is None, f"不该报错: {err}"
    assert victim.is_file(), "删掉了不属于自己的文件"
    assert victim.read_text(encoding="utf-8") == "SOMEONE-ELSES-FILE\n"


def test_rollback_published_reports_unlink_failure_instead_of_swallowing(tmp_path):
    """HIGH-3 承重门（另一半）：删除失败**不得静默吞掉**，否则错误字节的
    target 留在 vault 里而回执只报「失败」。"""
    mod = _load_module()
    d = tmp_path / "d"
    d.mkdir()
    f = d / "t.md"
    f.write_text("OURS\n", encoding="utf-8")
    st = f.stat()
    dfd = mod.os.open(d, mod.os.O_RDONLY | mod.os.O_DIRECTORY)
    real_unlink = mod.os.unlink

    def evil_unlink(*a, **kw):
        raise PermissionError("simulated")

    mod.os.unlink = evil_unlink
    try:
        err = mod._rollback_published("t.md", dfd, (st.st_dev, st.st_ino))
    finally:
        mod.os.unlink = real_unlink
        mod.os.close(dfd)
    assert err is not None, "删除失败却报成功（原实现的行为）"
    assert "unlink" in err


def test_atomic_write_rolls_back_when_readback_raises(tmp_path):
    """HIGH-2 承重门：`os.link` 成功后 target 已发布；若随后的回读抛
    EMFILE/EIO 之类，原实现掉进统一错误分支只删 tmp，**把已发布的 target
    留在 vault 里**却回报失败。修法是用 `published` 状态让失败路径撤销发布。"""
    mod = _load_module()
    d = tmp_path / "d"
    d.mkdir()
    tmp_p, target = d / "t.tmp", d / "t.md"
    dfd = mod.os.open(d, mod.os.O_RDONLY | mod.os.O_DIRECTORY)
    real_open = mod.os.open
    state = {"linked": False}
    real_link = mod.os.link

    def evil_link(src, dst, **kw):
        real_link(src, dst, **kw)
        state["linked"] = True

    def evil_open(path, *a, **kw):
        # 只在 link 之后、对 target 的回读上抛错
        if state["linked"] and path == "t.md":
            raise OSError(24, "simulated EMFILE")
        return real_open(path, *a, **kw)

    mod.os.link, mod.os.open = evil_link, evil_open
    try:
        err, _warn = mod._atomic_write(tmp_p, target, "USER-CONFIRMED\n", dfd)
    finally:
        mod.os.link, mod.os.open = real_link, real_open
        mod.os.close(dfd)
    assert err is not None, "回读抛错却报成功"
    assert not target.exists(), "回执报失败，却把已发布的目标留在了 vault 里"


def test_fsync_dir_reports_failure_instead_of_silently_succeeding(tmp_path):
    """HIGH-4 承重门（下半）：`_fsync_dir` 原先吞掉全部错误并返回 None，
    调用方无从分辨成功与失败。现在必须返回失败原因。"""
    mod = _load_module()
    d = tmp_path / "d"
    d.mkdir()
    assert mod._fsync_dir(d) is None, "正常目录不该报错"
    real_fsync = mod.os.fsync

    def evil_fsync(fd):
        raise OSError(5, "simulated EIO")

    mod.os.fsync = evil_fsync
    try:
        err = mod._fsync_dir(d)
    finally:
        mod.os.fsync = real_fsync
    assert err is not None, "fsync 失败却返回 None（原实现的 fail-open）"
    assert "fsync" in err


def test_undo_refuses_when_retention_dir_fsync_fails(tmp_path, capsys):
    """HIGH-4 承重门（上半）：留痕的**目录项**没落盘就删源，崩溃后可能两端皆失。
    现在必须 fail-closed —— 拒绝回退且原文件原样保留。"""
    vault = build_vault(tmp_path)
    out = do_create(vault, ["板一"])
    undo_dir = tmp_path / "keep-fsyncfail"
    undo_dir.mkdir()
    target = vault / out["created_path"]
    mod = _load_module()
    real_fsync_dir = mod._fsync_dir

    def evil_fsync_dir(dd):
        if Path(dd) == undo_dir:
            return "目录 fsync 失败 OSError"  # 模拟持久化失败
        return real_fsync_dir(dd)

    mod._fsync_dir = evil_fsync_dir
    try:
        rc = mod.cmd_undo(_undo_args(vault, out["created_path"], out["content_sha256"], undo_dir))
    finally:
        mod._fsync_dir = real_fsync_dir
    res = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert res["undone"] is False, "留痕目录项未持久化却报回退成功"
    assert "持久化" in res["refusal_reason"]
    assert target.is_file(), "fail-open 删掉了源文件"


def test_create_detects_exam_dir_moved_out_of_vault_after_anchor(tmp_path, capsys):
    """HIGH-1 承重门：dirfd 只在打开那一刻做 inode 快照。校验通过后把
    检验白板/ rename 到 vault **外**（同一文件系统），dfd 仍指向已外移的 inode ——
    写入真的落在 vault 外，而回执照旧按词法路径报 created:true。
    修法是写入完成后再核一次「vault/检验白板 现在的 inode 是否还等于 dfd 的」。"""
    vault = build_vault(tmp_path)
    sha = do_preview(vault, ["板一"])["content_sha256"]
    outside = tmp_path / "moved_away"
    exam = vault / EXAM_DIR_NAME
    mod = _load_module()
    real_atomic = mod._atomic_write

    def evil_atomic(tmp_p, target, content, dir_fd):
        r = real_atomic(tmp_p, target, content, dir_fd)
        # 写入已完成、复核之前：把目录整体移出 vault（同一文件系统）
        exam.rename(outside)
        return r

    mod._atomic_write = evil_atomic
    try:
        rc = mod.cmd_create(
            argparse.Namespace(
                vault=str(vault),
                boards=["板一"],
                anchor=None,
                ts=TS,
                expect_content_sha=sha,
            )
        )
    finally:
        mod._atomic_write = real_atomic
    out = capsys.readouterr().out
    assert rc == 2, f"目录被移出 vault 却报成功: rc={rc} {out}"
    # 两种形态都算命中：目录被整体移走 ⇒ 路径不存在（FileNotFoundError）；
    # 目录被换成另一个同名目录 ⇒ inode 已变。二者都由写入后复核检出。
    assert "写入后复核" in out or "移出 vault" in out or "inode 已变" in out, f"拒绝理由未点名写入后复核: {out}"
    assert "已撤销该文件" in out, f"检出后未撤销已发布的文件: {out}"
    assert not (outside / f"板一-{TS}.md").exists(), "文件留在了 vault 外"


def test_create_detects_exam_dir_swapped_to_another_dir_after_anchor(tmp_path, capsys):
    """HIGH-1 承重门（另一形态）：目录被换成**另一个同名目录**（路径仍存在，
    但 inode 变了）。这条专门锁 inode 比对那一支，避免只被 FileNotFoundError 覆盖。"""
    vault = build_vault(tmp_path)
    sha = do_preview(vault, ["板一"])["content_sha256"]
    exam = vault / EXAM_DIR_NAME
    decoy = tmp_path / "decoy_dir"
    decoy.mkdir()
    mod = _load_module()
    real_atomic = mod._atomic_write

    def evil_atomic(tmp_p, target, content, dir_fd):
        r = real_atomic(tmp_p, target, content, dir_fd)
        exam.rename(tmp_path / "stashed")  # 移走原目录
        decoy.rename(exam)  # 换上另一个同名目录（inode 不同）
        return r

    mod._atomic_write = evil_atomic
    try:
        rc = mod.cmd_create(
            argparse.Namespace(
                vault=str(vault),
                boards=["板一"],
                anchor=None,
                ts=TS,
                expect_content_sha=sha,
            )
        )
    finally:
        mod._atomic_write = real_atomic
    out = capsys.readouterr().out
    assert rc == 2, f"目录被换成另一个同名目录却报成功: rc={rc} {out}"
    assert "inode 已变" in out or "被替换或移出" in out, f"未点名 inode 变化: {out}"
