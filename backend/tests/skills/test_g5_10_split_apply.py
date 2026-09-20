# -*- coding: utf-8 -*-
"""CARD-G5-10 承重行为门：board-split 执行侧 `split_apply.py`。

全程真跑（DD-03 禁 mock）：
- 每条用例先用真 `split_preview.py` CLI 产出 preview（不手造 JSON）；
- 再用 subprocess 真跑 `split_apply.py`（--dry-run / --apply / --undo）；
- 结构/解析面用真 `board_manifest_service.scan_vault`（在 backend cwd 下 import）。

先红形态：`split_apply.py` 不存在时，所有走 CLI 的用例在 `_run_script` 里
`pytest.fail`（照 test_split_preview.py:47-48 的形态），不会被「rc≠0」类
断言误吞成假绿。
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import frontmatter as fm_lib
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SPLIT_PREVIEW = REPO_ROOT / "canvas-vault" / ".claude" / "skills" / "board-split" / "scripts" / "split_preview.py"
SPLIT_APPLY = REPO_ROOT / "canvas-vault" / ".claude" / "skills" / "board-split" / "scripts" / "split_apply.py"

# ── CLI 调用 ─────────────────────────────────────────────────────────────


def _run_script(script: Path, *args: str) -> subprocess.CompletedProcess:
    if not script.exists():  # ⛔ 防「脚本不存在 → rc≠0 → 拒绝类断言假绿」
        pytest.fail(f"被测脚本不存在: {script}")
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, timeout=180)


def run_preview(vault: Path, board: str, out_dir: Path, *extra: str) -> subprocess.CompletedProcess:
    return _run_script(SPLIT_PREVIEW, "--vault", str(vault), "--board", board, "--out-dir", str(out_dir), *extra)


def run_apply(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return _run_script(SPLIT_APPLY, "--vault", str(vault), *args)


def out2(r: subprocess.CompletedProcess) -> str:
    return r.stdout + r.stderr


# ── fixture 构造器（形态抄 test_split_preview.py::make_vault / test_split_stable_id.py） ──

BODY1 = "反射代理只看当前感知就决定行动，不保存历史也不预测未来，是最简单的一类代理。"
BODY2 = "第二行正文：代理函数把感知历史映射到行动，这是分析一切代理行为的数学起点。"
BODY_ALT = "第二行正文（微调版）：代理函数把感知历史映射到行动，这是分析代理的数学起点。"


def section(heading: str, body: list[str] | None = None, level: int = 2) -> str:
    body = body if body is not None else [BODY1, BODY2]
    return "#" * level + f" {heading}\n\n" + "\n".join(body) + "\n\n"


def board_doc(sections: list[str]) -> str:
    return "---\ntype: whiteboard\n---\n\n# 主板\n\n" + "".join(sections)


def make_vault(tmp_path: Path, tag: str, doc: str, nodes: dict[str, str] | None = None, board: str = "板A") -> Path:
    vault = tmp_path / f"vault-{tag}"
    for d in ("原白板", "节点", "检验白板", "outputs"):
        (vault / d).mkdir(parents=True, exist_ok=True)
    (vault / "原白板" / f"{board}.md").write_text(doc, encoding="utf-8")
    for name, body in (nodes or {}).items():
        (vault / "节点" / f"{name}.md").write_text(body, encoding="utf-8")
    return vault


def preview(vault: Path, board: str, out_dir: Path, tag: str = "p") -> tuple[Path, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    r = run_preview(vault, board, out_dir)
    assert r.returncode == 0, f"preview 应成功: {out2(r)}"
    pj = out_dir / f"split-preview-{board}.json"
    assert pj.is_file(), f"preview JSON 未生成: {pj}"
    return pj, json.loads(pj.read_text(encoding="utf-8"))


def _cands(data: dict, basis: str | None = None) -> list[dict]:
    out = data["candidates"]
    if basis is not None:
        out = [c for c in out if c["basis"] == basis]
    return out


def tree_map(vault: Path, exclude_top: tuple[str, ...] = ("outputs",)) -> dict[str, str]:
    """vault 全树 {相对路径: sha256}（排除工具产物区 outputs/ —— 批次账本/备份必须留痕，
    否则与「undo 留痕」语义自相矛盾；P7-A 的 UAT 同口径声明「outputs/ 在树外」）。"""
    out: dict[str, str] = {}
    for p in sorted(vault.rglob("*")):
        rel = p.relative_to(vault)
        if rel.parts and rel.parts[0] in exclude_top:
            continue
        if p.is_symlink() or not p.is_file():
            continue
        out[str(rel)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def batch_root(vault: Path) -> Path:
    return vault / "outputs" / "board-split"


def batch_dirs(vault: Path) -> list[Path]:
    root = batch_root(vault)
    return sorted(p for p in root.glob("*") if p.is_dir()) if root.is_dir() else []


# ══════════════════════════ ① dry-run ══════════════════════════


def test_dry_run_prints_plan_and_leaves_vault_untouched(tmp_path):
    """默认（不给 --apply）= dry-run：打印计划、vault 全树零变化、连批次目录都不建。"""
    vault = make_vault(tmp_path, "dry", board_doc([section("甲小节"), section("乙小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "dry")
    ids = [c["stable_id"] for c in data["candidates"]][:2]
    names = [c["resolved_name"] for c in data["candidates"]][:2]

    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids))
    assert r.returncode == 0, f"dry-run 应 rc=0: {out2(r)}"
    assert "dry-run" in out2(r), "计划里应说明这是 dry-run"
    for n in names:
        assert n in r.stdout, f"计划里应列出目标 {n}"
    assert tree_map(vault) == before, "dry-run 不得写任何文件"
    assert batch_dirs(vault) == [], "dry-run 不得建批次目录"

    # 显式 --dry-run 同语义
    r2 = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--dry-run")
    assert r2.returncode == 0 and tree_map(vault) == before


# ══════════════════════════ ② apply + frontmatter ══════════════════════════


def test_apply_creates_two_nodes_with_full_frontmatter(tmp_path):
    """--apply --confirm <两个正常 id> → 两个节点生成，frontmatter 全键读回。"""
    vault = make_vault(tmp_path, "apply", board_doc([section("甲小节"), section("乙小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "apply")
    picked = _cands(data, basis="board-body-section")[:2]
    ids = [c["stable_id"] for c in picked]

    r = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--apply")
    assert r.returncode == 0, f"apply 应 rc=0: {out2(r)}"
    assert "created=2" in out2(r)

    for c in picked:
        f = vault / "节点" / f"{c['resolved_name']}.md"
        assert f.is_file(), f"节点未生成: {f}"
        post = fm_lib.load(str(f))
        md = post.metadata
        assert md["type"] == "concept"
        assert md["created_from"] == "board_split"
        assert md["source_board"] == "[[原白板/板A]]"
        assert md["split_stable_id"] == c["stable_id"]
        assert md["split_stable_id_basis"] == c["stable_id_basis"], "basis 应逐字抄 preview"
        created_at = md["created_at"]
        ca_str = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        assert "T" in ca_str, f"created_at 应是 ISO 8601（YAML 会把它解析为时间戳）: {created_at!r}"
        rel = md["relationships"]
        assert isinstance(rel, list) and len(rel) >= 1
        assert rel[0]["type"] == "split_from"
        assert rel[0]["target"] == "[[原白板/板A]]"
        assert rel[0]["derived_at"] == created_at
        body = post.content
        assert body.startswith(f"# {c['resolved_name']}")
        assert BODY1 in body, "正文应含 source_anchor 区间原文"


# ══════════════════════════ ③ 真解析门（scan_vault） ══════════════════════════


def test_created_nodes_are_manifest_members_derived_and_not_orphan(tmp_path):
    """新节点经真 board_manifest_service 解析：进该板 members、role=derived、不在 orphans、
    parse_errors 为空（按 node_id / source_board 逐字段断言）。"""
    from app.services.board_manifest_service import scan_vault

    vault = make_vault(tmp_path, "scan", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "scan")
    c = _cands(data, basis="board-body-section")[0]
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode == 0, f"apply 应 rc=0: {out2(r)}"

    full = scan_vault(vault)
    members = full["boards"]["板A"]["members"]
    hit = [m for m in members if m["node_id"] == c["resolved_name"]]
    assert hit, "新节点必须进该板 members"
    assert hit[0]["role"] == "derived", f"role 应为 derived，实得 {hit[0]['role']}"
    assert c["resolved_name"] not in [o["node_id"] for o in full["orphans"]], "不得落孤儿"
    assert full["parse_errors"] == [], f"解析错误必须为空: {full['parse_errors']}"
    post = fm_lib.load(str(vault / "节点" / f"{c['resolved_name']}.md"))
    assert post.metadata["source_board"] == "[[原白板/板A]]", "source_board 原文须逐字"


# ══════════════════════════ ④ 歧义拒绝 ══════════════════════════


def test_ambiguous_candidate_is_rejected_zero_products(tmp_path):
    """identity_ambiguous=true 的候选：拒绝、rc≠0、报文含标记、零产物。"""
    doc = board_doc([section("例题", [BODY1, BODY2]), section("例题", [BODY1, BODY_ALT])])
    vault = make_vault(tmp_path, "amb", doc)
    pj, data = preview(vault, "板A", vault / "outputs", "amb")
    amb = [c for c in data["candidates"] if c["identity_ambiguous"]]
    assert amb, "构造前提：必须有 identity_ambiguous 候选"
    sid = amb[0]["stable_id"]

    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", sid, "--apply")
    assert r.returncode != 0, "歧义候选必须拒绝"
    assert "identity_ambiguous" in out2(r)
    assert tree_map(vault) == before, "拒绝必须零产物"
    assert batch_dirs(vault) == [], "拒绝必须连批次目录都不建"


# ══════════════════════════ ⑤ 过期拒绝 ══════════════════════════


def test_stale_preview_is_rejected_zero_products(tmp_path):
    """preview 产出后板文件被改（追加一个小节）→ apply 用旧 preview：拒绝、报文含「过期」、零产物。"""
    vault = make_vault(tmp_path, "stale", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "stale")
    c = _cands(data, basis="board-body-section")[0]

    board = vault / "原白板" / "板A.md"
    board.write_text(board.read_text(encoding="utf-8") + section("后加小节"), encoding="utf-8")
    before = tree_map(vault)

    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0, "过期 preview 必须拒绝"
    assert "过期" in out2(r)
    assert tree_map(vault) == before, "拒绝必须零产物"
    assert batch_dirs(vault) == []


# ══════════════════════════ ⑥ callout 插入（默认关 + 幂等） ══════════════════════════


def test_callout_insertion_is_opt_in_and_idempotent(tmp_path):
    """--insert-callout 默认关；未给 --confirm-insert（非 TTY）=全跳过；给了才插；
    已存在同形 callout 不重复插；插后再跑 preview → derived_overlap.overlapping=true。"""
    vault = make_vault(tmp_path, "callout", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "callout")
    c = _cands(data, basis="board-body-section")[0]
    sid, name = c["stable_id"], c["resolved_name"]
    board = vault / "原白板" / "板A.md"
    callout_line = f"> [!relation/related_to]+ 已派生为 [[节点/{name}]] · 相关"

    # 阶段 A：不带 --insert-callout → 只建节点，板字节不变
    sha0 = hashlib.sha256(board.read_bytes()).hexdigest()
    r = run_apply(vault, "--preview", str(pj), "--confirm", sid, "--apply")
    assert r.returncode == 0 and hashlib.sha256(board.read_bytes()).hexdigest() == sha0

    # 阶段 B：带 --insert-callout 但不给 --confirm-insert（非 TTY）→ 仍不得插
    r = run_apply(vault, "--preview", str(pj), "--confirm", sid, "--apply", "--insert-callout")
    assert r.returncode == 0, out2(r)
    assert hashlib.sha256(board.read_bytes()).hexdigest() == sha0, "未确认不得静默插入"

    # 阶段 C：--confirm-insert → 插入
    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        sid,
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        sid,
    )
    assert r.returncode == 0, f"callout 插入应成功: {out2(r)}"
    lines = board.read_text(encoding="utf-8").split("\n")
    idx = c["source_anchor"]["line_start"]  # 0-based 下标 = 1-based 标题行的下一行
    assert lines[idx] == callout_line, f"callout 必须逐字插在标题行之后: 实得 {lines[idx]!r}"
    sha1_ = hashlib.sha256(board.read_bytes()).hexdigest()

    # 阶段 D：同参数重跑 → 已存在同形 callout，跳过不重复插
    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        sid,
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        sid,
    )
    assert r.returncode == 0, out2(r)
    assert hashlib.sha256(board.read_bytes()).hexdigest() == sha1_, "不得重复插入"

    # 阶段 E：再跑一次 preview → 该候选 derived_overlap 认到
    _, data2 = preview(vault, "板A", vault / "outputs" / "again", "callout2")
    c2 = [x for x in data2["candidates"] if x["stable_id"] == sid][0]
    assert c2["derived_overlap"]["overlapping"] is True
    assert c2["derived_overlap"]["existing_nodes"] == [name]


# ══════════════════════════ ⑦ undo 全树逐字节还原 ══════════════════════════


def test_undo_restores_vault_tree_byte_exact(tmp_path):
    """apply（含 callout 插入）→ undo：全树 {路径: sha256} 与 apply 前逐项相等。"""
    vault = make_vault(tmp_path, "undo", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "undo")
    c = _cands(data, basis="board-body-section")[0]
    sid = c["stable_id"]
    before = tree_map(vault)

    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        sid,
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        sid,
    )
    assert r.returncode == 0, out2(r)
    assert tree_map(vault) != before, "构造前提：apply 应改变树"

    batches = batch_dirs(vault)
    assert len(batches) == 1, f"应有恰一个批次目录: {batches}"
    r = run_apply(vault, "--undo", batches[0].name)
    assert r.returncode == 0, f"undo 应 rc=0: {out2(r)}"
    after = tree_map(vault)
    assert after == before, (
        "undo 后全树必须逐项相等\n only-before: "
        + str(sorted(set(before) - set(after)))
        + "\n only-after: "
        + str(sorted(set(after) - set(before)))
        + "\n diff: "
        + str(sorted(k for k in set(before) & set(after) if before[k] != after[k]))
    )


# ══════════════════════════ ⑧ undo 保护：用户改过的不删 ══════════════════════════


def test_undo_refuses_user_modified_node_but_restores_rest(tmp_path):
    """apply 后手改一个新建节点再 undo：该文件拒删仍在、其余还原、rc≠0 且报文列出该路径。"""
    vault = make_vault(tmp_path, "undo2", board_doc([section("甲小节"), section("乙小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "undo2")
    picked = _cands(data, basis="board-body-section")[:2]
    ids = [c["stable_id"] for c in picked]
    before = tree_map(vault)

    r = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--apply")
    assert r.returncode == 0, out2(r)

    victim = vault / "节点" / f"{picked[0]['resolved_name']}.md"
    victim.write_text(victim.read_text(encoding="utf-8") + "\n用户后来补了一句。\n", encoding="utf-8")

    batch = batch_dirs(vault)[0]
    r = run_apply(vault, "--undo", batch.name)
    assert r.returncode != 0, "有拒删项时 rc 必≠0"
    assert victim.is_file(), "被用户改过的文件必须保留"
    assert str(victim.relative_to(vault)) in out2(r), "报文必须列出该路径"
    other = vault / "节点" / f"{picked[1]['resolved_name']}.md"
    assert not other.exists(), "其余自建文件应已撤销"
    restored = {k: v for k, v in tree_map(vault).items() if k != str(victim.relative_to(vault))}
    expect = {k: v for k, v in before.items() if k != str(victim.relative_to(vault))}
    assert restored == expect, "除拒删件外的全树应逐字节还原"


# ══════════════════════════ ⑨ 幂等 ══════════════════════════


def test_apply_is_idempotent_second_run_skips(tmp_path):
    """同 preview 同 confirm 连跑两次：第二次 created=0 / skipped=2，文件 sha 与 mtime 不变。"""
    vault = make_vault(tmp_path, "idem", board_doc([section("甲小节"), section("乙小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "idem")
    picked = _cands(data, basis="board-body-section")[:2]
    ids = [c["stable_id"] for c in picked]

    r1 = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--apply")
    assert r1.returncode == 0, out2(r1)
    stats = {}
    for c in picked:
        st = (vault / "节点" / f"{c['resolved_name']}.md").stat()
        stats[c["resolved_name"]] = (st.st_mtime_ns,)

    r2 = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--apply")
    assert r2.returncode == 0, f"第二次应 rc=0: {out2(r2)}"
    assert "created=0" in out2(r2) and "skipped=2" in out2(r2), f"实得: {out2(r2)}"
    for name, (mtime0,) in stats.items():
        st = (vault / "节点" / f"{name}.md").stat()
        assert st.st_mtime_ns == mtime0, f"已建文件 {name} 的 mtime 不得被改"


# ══════════════════════════ ⑩ 中断重跑（补记 done） ══════════════════════════


def test_rerun_after_missing_done_marker_catches_up(tmp_path):
    """删掉 journal 里第二条的 done 行（模拟半途）再 --apply：目标存在且 sha 匹配
    ⇒ 补记 done、不重建、rc=0。"""
    vault = make_vault(tmp_path, "resume", board_doc([section("甲小节"), section("乙小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "resume")
    picked = _cands(data, basis="board-body-section")[:2]
    ids = [c["stable_id"] for c in picked]
    r1 = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--apply")
    assert r1.returncode == 0, out2(r1)

    batch = batch_dirs(vault)[0]
    jp = batch / "journal.jsonl"
    rows = [json.loads(ln) for ln in jp.read_text(encoding="utf-8").split("\n") if ln.strip()]
    drop = [i for i, row in enumerate(rows) if row.get("seq") == 2 and row.get("state") == "done"]
    assert drop, "构造前提：第二条应有 done 行"
    kept_rows = [row for i, row in enumerate(rows) if i != drop[-1]]
    jp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept_rows), encoding="utf-8")

    f2 = vault / "节点" / f"{picked[1]['resolved_name']}.md"
    mtime0 = f2.stat().st_mtime_ns

    r2 = run_apply(vault, "--preview", str(pj), "--confirm", ",".join(ids), "--apply")
    assert r2.returncode == 0, f"续跑应 rc=0: {out2(r2)}"
    assert f2.stat().st_mtime_ns == mtime0, "续跑不得重建已存在的文件"
    rows2 = [json.loads(ln) for ln in jp.read_text(encoding="utf-8").split("\n") if ln.strip()]
    assert any(r.get("seq") == 2 and r.get("state") == "done" for r in rows2), "应补记 done 行"


# ══════════════════════════ ⑪ 同名不同 stable_id → 拒绝 ══════════════════════════


def test_existing_node_with_different_stable_id_refuses_batch(tmp_path):
    """目标位置已有一份同名节点且 split_stable_id ≠ 本候选 → 整批拒绝、零产物。"""
    vault = make_vault(tmp_path, "fork", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "fork")
    c = _cands(data, basis="board-body-section")[0]

    # preview 之后才出现的"别人"的同名节点（分辨率当时看不到它）
    intruder = vault / "节点" / f"{c['resolved_name']}.md"
    intruder.write_text(
        "---\ntype: concept\nsplit_stable_id: bsa1-0000000000000000\n---\n\n# 别家的\n",
        encoding="utf-8",
    )
    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0, "同名不同源必须拒绝"
    assert "已存在" in out2(r) and "split_stable_id" in out2(r)
    assert tree_map(vault) == before, "拒绝必须零产物"
    assert batch_dirs(vault) == []


# ══════════════════════════ ⑫ 节点目录 symlink → 拒绝 ══════════════════════════


def test_symlinked_node_dir_is_rejected_zero_products(tmp_path):
    """节点/ 目录本身是 symlink → 拒绝、零产物。"""
    vault = make_vault(tmp_path, "sym", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "sym")
    c = _cands(data, basis="board-body-section")[0]

    real = vault / "节点-real"
    (vault / "节点").rename(real)
    (vault / "节点").symlink_to(real, target_is_directory=True)
    assert (vault / "节点").is_symlink()
    n_real = len(list(real.glob("*.md")))

    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0 and "symlink" in out2(r)
    assert len(list(real.glob("*.md"))) == n_real, "零产物"
    assert batch_dirs(vault) == []


# ══════════════════════════ ⑬ 未知 confirm id → 拒绝（准入②） ══════════════════════════


def test_unknown_confirm_id_is_rejected(tmp_path):
    vault = make_vault(tmp_path, "unk", board_doc([section("甲小节")]))
    pj, _ = preview(vault, "板A", vault / "outputs", "unk")
    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", "bsa1-ffffffffffffffff", "--apply")
    assert r.returncode != 0
    assert "不在" in out2(r) or "未知" in out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == []


# ══════════════════════════ ⑭ 中断重跑不得认领外来文件（BLOCKER-1） ══════════════════════════


def test_resume_does_not_claim_foreign_same_id_file(tmp_path):
    """目标同 id 但内容与账上计划不符（外部文件）→ 拒绝认领、不补记 done；undo 也删不了它。"""
    vault = make_vault(tmp_path, "claim", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "claim")
    c = _cands(data, basis="board-body-section")[0]
    r1 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r1.returncode == 0, out2(r1)
    node = vault / "节点" / f"{c['resolved_name']}.md"
    node.write_text(node.read_text(encoding="utf-8") + "\n外部插入的一行。\n", encoding="utf-8")

    jp = batch_dirs(vault)[0] / "journal.jsonl"
    rows = [json.loads(ln) for ln in jp.read_text(encoding="utf-8").split("\n") if ln.strip()]
    kept = [row for row in rows if not (row.get("seq") == 1 and row.get("state") == "done")]
    assert len(kept) < len(rows), "构造前提：应有 done 行可删"
    jp.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in kept), encoding="utf-8")

    r2 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r2.returncode != 0, "内容与账上计划不符时不得认领"
    rows2 = [json.loads(ln) for ln in jp.read_text(encoding="utf-8").split("\n") if ln.strip()]
    assert not any(row.get("seq") == 1 and row.get("state") == "done" for row in rows2), "不得补记 done"

    batch = batch_dirs(vault)[0]
    r3 = run_apply(vault, "--undo", batch.name)
    assert r3.returncode != 0 and node.is_file(), "只有 intent 没有 done 的行不得删文件"


# ══════════════════════════ ⑮ 被改写的安全标志必须被拦（HIGH-1） ══════════════════════════


def test_tampered_security_flags_are_rejected(tmp_path):
    """手改 preview：歧义标志 / conflict 标志 / basis 三类改写都必须被拦下（零产物）。

    覆盖分层说明（与实现一致）：identity 对账由门① 与重算比对；conflict 改 true 由门④
    fail-closed 拦；basis 一致改写由载入期交叉绑定拦 —— 三类各有承重层。"""
    doc = board_doc([section("例题", [BODY1, BODY2]), section("例题", [BODY1, BODY_ALT])])
    vault = make_vault(tmp_path, "tamper", doc)
    pj, data = preview(vault, "板A", vault / "outputs", "tamper")
    amb = [c for c in data["candidates"] if c["identity_ambiguous"]][0]
    clean = json.loads(pj.read_text(encoding="utf-8"))

    def rewrite(sid, transform):
        d = json.loads(json.dumps(clean))
        hit = [c for c in d["candidates"] if c["stable_id"] == sid]
        assert hit, f"构造前提：{sid} 在 preview 里"
        transform(hit[0])
        pj.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = tree_map(vault)

    # ① identity_ambiguous / ambiguous_group_size 改小 → 门① 与重算对账后拒绝
    rewrite(amb["stable_id"], lambda c: c.update(identity_ambiguous=False, ambiguous_group_size=1))
    r = run_apply(vault, "--preview", str(pj), "--confirm", amb["stable_id"], "--apply")
    assert r.returncode != 0 and ("过期" in out2(r) or "不符" in out2(r)), out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == []

    # ② conflict_unresolvable 被改成 true → fail-closed 拒绝
    rewrite(amb["stable_id"], lambda c: c.update(conflict_unresolvable=True))
    r = run_apply(vault, "--preview", str(pj), "--confirm", amb["stable_id"], "--apply")
    assert r.returncode != 0, "conflict 标志改写必须被拦"
    assert tree_map(vault) == before and batch_dirs(vault) == []

    # ③ basis 两处一致改写 → 载入期身份复算（交叉绑定）拒绝
    rewrite(
        amb["stable_id"],
        lambda c: (c.update(basis="seed-note-whole"), c["stable_id_basis"].update(basis="seed-note-whole")),
    )
    r = run_apply(vault, "--preview", str(pj), "--confirm", amb["stable_id"], "--apply")
    assert r.returncode != 0, "basis 改写必须被拦"
    assert tree_map(vault) == before and batch_dirs(vault) == []


# ══════════════════════════ ⑯ 写后中断的 callout 修改可还原（HIGH-2） ══════════════════════════


def test_undo_restores_interrupted_callout_modify(tmp_path):
    """callout 写完成但 done 未落账（删 done 行模拟）→ undo 按 sha256_planned 认账并还原。"""
    vault = make_vault(tmp_path, "crashmod", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "crashmod")
    c = _cands(data, basis="board-body-section")[0]
    sid = c["stable_id"]
    before = tree_map(vault)
    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        sid,
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        sid,
    )
    assert r.returncode == 0, out2(r)

    jp = batch_dirs(vault)[0] / "journal.jsonl"
    rows = [json.loads(ln) for ln in jp.read_text(encoding="utf-8").split("\n") if ln.strip()]
    kept = [row for row in rows if not (row.get("op") == "split_modify" and row.get("state") == "done")]
    assert len(kept) < len(rows), "构造前提：应有 modify done 行可删"
    jp.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in kept), encoding="utf-8")

    batch = batch_dirs(vault)[0]
    r2 = run_apply(vault, "--undo", batch.name)
    assert r2.returncode == 0, f"写后中断（缺 done）应可按计划 sha 还原: {out2(r2)}"
    assert tree_map(vault) == before, "全树应逐字节还原"


# ══════════════════════════ ⑰ CRLF 保持（HIGH-3） ══════════════════════════


def test_callout_insertion_preserves_crlf_bytes(tmp_path):
    """CRLF 板文件插入 callout 后：只多一行 CRLF，其余行尾逐字节不变。"""
    vault = make_vault(tmp_path, "crlf", "")
    board = vault / "原白板" / "板A.md"
    doc = board_doc([section("甲小节")]).replace("\n", "\r\n")
    board.write_bytes(doc.encode("utf-8"))
    pj, data = preview(vault, "板A", vault / "outputs", "crlf")
    cands = _cands(data, basis="board-body-section")
    assert cands, "构造前提：CRLF 板应能产出候选"
    c = cands[0]

    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        c["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        c["stable_id"],
    )
    assert r.returncode == 0, out2(r)
    before = doc.encode("utf-8")
    after = board.read_bytes()
    callout = f"> [!relation/related_to]+ 已派生为 [[节点/{c['resolved_name']}]] · 相关"
    assert after.count(b"\r\n") == before.count(b"\r\n") + 1, "只应新增一行 CRLF"
    assert after.replace((callout + "\r\n").encode("utf-8"), b"", 1) == before, "其余字节逐字不变"


# ══════════════════════════ ⑱ 嵌套 callout 重跑不被父候选过期门挡下（HIGH-4） ══════════════════════════


def test_nested_callout_rerun_not_blocked_by_parent_freshness(tmp_path):
    """父小节 span 含子小节 callout：同命令重跑必须能过门①（容忍只剔 callout 形态行）。"""
    doc = board_doc([section("父小节") + section("子小节", level=3)])
    vault = make_vault(tmp_path, "nested", doc)
    pj, data = preview(vault, "板A", vault / "outputs", "nested")
    cands = _cands(data, basis="board-body-section")
    assert len(cands) == 2, f"构造前提：父+子两条候选, 实得 {len(cands)}"
    ids = [c["stable_id"] for c in cands]
    args = (
        "--preview",
        str(pj),
        "--confirm",
        ",".join(ids),
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        ",".join(ids),
    )
    r1 = run_apply(vault, *args)
    assert r1.returncode == 0, out2(r1)
    board = vault / "原白板" / "板A.md"
    n1 = sum(1 for ln in board.read_text(encoding="utf-8").split("\n") if "已派生为" in ln)
    assert n1 == 2, f"应有两条 callout, 实得 {n1}"
    sha1 = hashlib.sha256(board.read_bytes()).hexdigest()

    r2 = run_apply(vault, *args)
    assert r2.returncode == 0, f"嵌套重跑不得被门① 挡下: {out2(r2)}"
    assert "过期" not in out2(r2)
    assert hashlib.sha256(board.read_bytes()).hexdigest() == sha1


# ══════════════════════════ ⑲ 代码块里的字样不算已插（MEDIUM-1） ══════════════════════════


def test_fenced_derived_mention_does_not_false_skip(tmp_path):
    """来源文件代码 fence 里有「已派生为 [[节点/X]]」字样：不得误判已存在，真插入照做。"""
    body = [BODY1, BODY2, "```", "示例：已派生为 [[节点/甲小节]] · 相关", "```"]
    vault = make_vault(tmp_path, "fence", board_doc([section("甲小节", body)]))
    pj, data = preview(vault, "板A", vault / "outputs", "fence")
    c = _cands(data, basis="board-body-section")[0]
    assert c["resolved_name"] == "甲小节", "构造前提：stub 即标题原文"

    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        c["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        c["stable_id"],
    )
    assert r.returncode == 0, out2(r)
    assert "callout_inserted=1" in out2(r), f"真插入不得被 fence 字样误跳过: {out2(r)}"

    # HTML 注释里的字样同样不算已插（与 derived_names_in 同口径）
    body2 = [BODY1, BODY2, "<!-- 已派生为 [[节点/乙小节]] · 相关 -->"]
    vault2 = make_vault(tmp_path, "fence2", board_doc([section("乙小节", body2)]))
    pj2, data2 = preview(vault2, "板A", vault2 / "outputs", "fence2")
    c2 = _cands(data2, basis="board-body-section")[0]
    assert c2["resolved_name"] == "乙小节", "构造前提：stub 即标题原文"
    r2 = run_apply(
        vault2,
        "--preview",
        str(pj2),
        "--confirm",
        c2["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        c2["stable_id"],
    )
    assert r2.returncode == 0, out2(r2)
    assert "callout_inserted=1" in out2(r2), f"注释字样不得误跳过真插入: {out2(r2)}"
    lines = (vault / "原白板" / "板A.md").read_text(encoding="utf-8").split("\n")
    assert lines[c["source_anchor"]["line_start"]] == (f"> [!relation/related_to]+ 已派生为 [[节点/甲小节]] · 相关")


# ══════════════════════════ ⑳ --undo 批次 id 形状（MEDIUM-2） ══════════════════════════


def test_undo_rejects_weird_batch_id(tmp_path):
    """--undo 只收 bs-<16 hex>：路径逃逸/绝对路径/异形一律拒绝。"""
    vault = make_vault(tmp_path, "wid", board_doc([section("甲小节")]))
    for bad in ("../escape", "/tmp/whatever", "bs-zzzz", "bs-0123456789abcdef00"):
        r = run_apply(vault, "--undo", bad)
        assert r.returncode != 0, f"应拒绝 {bad!r}"
        assert "形状" in out2(r), f"坏形状应报「形状不对」而不是被后续存在性检查吞掉: {bad!r} -> {out2(r)}"
    r2 = run_apply(vault, "--undo", "bs-deadbeefdeadbeef")
    assert r2.returncode != 0 and "找不到" in out2(r2)


# ══════════════════════════ ㉑ 互换/改名必须被锚点映射拦下（r2-HIGH-1） ══════════════════════════


def test_swapped_identical_sections_and_tampered_names_are_rejected(tmp_path):
    """两节正文逐字相同但互换位置 → 行号映射对不上；改 resolved_name → 重算名不符；都须拒绝零产物。"""
    sec_a = section("甲小节")
    sec_b = section("乙小节")
    vault = make_vault(tmp_path, "swap", board_doc([sec_a, sec_b]))
    pj, data = preview(vault, "板A", vault / "outputs", "swap")
    ca = [c for c in data["candidates"] if c["resolved_name"] == "甲小节"][0]

    board = vault / "原白板" / "板A.md"
    swapped = board.read_text(encoding="utf-8").replace(sec_a + sec_b, sec_b + sec_a, 1)
    assert swapped != board.read_text(encoding="utf-8"), "构造前提：互换必须真的改字节"
    board.write_text(swapped, encoding="utf-8")
    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", ca["stable_id"], "--apply")
    assert r.returncode != 0 and ("过期" in out2(r) or "不符" in out2(r)), f"互换应被行号映射拦下: {out2(r)}"
    assert tree_map(vault) == before and batch_dirs(vault) == []

    board.write_text(board_doc([sec_a, sec_b]), encoding="utf-8")
    d = json.loads(pj.read_text(encoding="utf-8"))
    for c in d["candidates"]:
        if c["stable_id"] == ca["stable_id"]:
            c["resolved_name"] = "被改名的目标"
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    before2 = tree_map(vault)
    r2 = run_apply(vault, "--preview", str(pj), "--confirm", ca["stable_id"], "--apply")
    assert r2.returncode != 0 and ("过期" in out2(r2) or "不符" in out2(r2)), out2(r2)
    assert tree_map(vault) == before2 and batch_dirs(vault) == []


# ══════════════════════════ ㉒ undo 不跟随 symlink 批次目录（r2-HIGH-2） ══════════════════════════


def test_undo_rejects_symlinked_batch_dir(tmp_path):
    """批次/journal 目录链任一环被换成 symlink → undo 拒绝（不把账或删除带到 vault 外）。"""
    for variant in ("batch", "workroot", "outputs", "journal"):
        vault = make_vault(tmp_path, f"bsym-{variant}", board_doc([section("甲小节")]))
        pj, data = preview(vault, "板A", vault / "outputs", f"bsym-{variant}")
        c = _cands(data, basis="board-body-section")[0]
        r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
        assert r.returncode == 0, out2(r)

        batch = batch_dirs(vault)[0]
        outside = tmp_path / f"outside-{variant}"
        if variant == "batch":
            batch.rename(outside)
            batch.symlink_to(outside, target_is_directory=True)
            jp = outside / "journal.jsonl"
        elif variant == "workroot":
            workroot = batch.parent
            workroot.rename(outside)
            workroot.symlink_to(outside, target_is_directory=True)
            jp = outside / batch.name / "journal.jsonl"
        elif variant == "outputs":
            outputs = vault / "outputs"
            outputs.rename(outside)
            outputs.symlink_to(outside, target_is_directory=True)
            jp = outside / "board-split" / batch.name / "journal.jsonl"
        else:  # journal
            outside.mkdir()
            jp = outside / "journal.jsonl"
            jp.write_bytes((batch / "journal.jsonl").read_bytes())
            (batch / "journal.jsonl").rename(batch / "journal.jsonl.real")
            (batch / "journal.jsonl").symlink_to(jp)
        before_rows = len(jp.read_text(encoding="utf-8").split("\n"))

        r2 = run_apply(vault, "--undo", batch.name)
        assert r2.returncode != 0 and "symlink" in out2(r2), f"{variant}: {out2(r2)}"
        assert len(jp.read_text(encoding="utf-8").split("\n")) == before_rows, f"{variant}: 外部账本不得被追加"


# ══════════════════════════ ㉓ 裸 CR 行尾拒绝（r2-MEDIUM-1） ══════════════════════════


def test_bare_cr_source_is_rejected_with_clear_message(tmp_path):
    """裸 CR 与 splitlines-only 分隔符精确拒绝；混合行尾时插入行随局部上一行风格。"""
    vault = make_vault(tmp_path, "cr", "")
    board = vault / "原白板" / "板A.md"
    doc = board_doc([section("甲小节")]).replace("\n", "\r")
    board.write_bytes(doc.encode("utf-8"))
    pj, data = preview(vault, "板A", vault / "outputs", "cr")
    assert data["candidates"], "构造前提：裸 CR 板仍可 preview 出候选"
    c = data["candidates"][0]
    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0 and "裸 CR" in out2(r), f"应报精确理由而不是含糊的过期: {out2(r)}"
    assert tree_map(vault) == before and batch_dirs(vault) == []

    vault2 = make_vault(tmp_path, "sep", "")
    board2 = vault2 / "原白板" / "板A.md"
    doc2 = board_doc([section("甲小节")]).replace("\n", "\u2028")
    board2.write_text(doc2, encoding="utf-8")
    pj2, data2 = preview(vault2, "板A", vault2 / "outputs", "sep")
    assert data2["candidates"], "构造前提：U+2028 板仍可 preview 出候选"
    c2 = data2["candidates"][0]
    r2 = run_apply(vault2, "--preview", str(pj2), "--confirm", c2["stable_id"], "--apply")
    assert r2.returncode != 0 and "行分隔" in out2(r2), f"U+2028 应被同一契约拒绝: {out2(r2)}"

    # 混合行尾：CRLF 区插入行用 CRLF、LF 区用 LF（局部上一行决定）
    mixed = (
        "---\ntype: whiteboard\n---\n\n# 主板\n\n"
        + "## 甲小节\r\n\r\n"
        + BODY1
        + "\r\n"
        + BODY2
        + "\r\n\r\n"
        + "## 乙小节\n\n"
        + BODY1
        + "\n"
        + BODY2
        + "\n\n"
    )
    vault3 = make_vault(tmp_path, "mix", "")
    board3 = vault3 / "原白板" / "板A.md"
    board3.write_text(mixed, encoding="utf-8")
    pj3, data3 = preview(vault3, "板A", vault3 / "outputs", "mix")
    ids3 = [c["stable_id"] for c in data3["candidates"]]
    assert len(ids3) == 2, f"构造前提：甲乙两条候选, 实得 {len(ids3)}"
    r3 = run_apply(
        vault3,
        "--preview",
        str(pj3),
        "--confirm",
        ",".join(ids3),
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        ",".join(ids3),
    )
    assert r3.returncode == 0, out2(r3)
    after = board3.read_bytes()
    before3 = mixed.encode("utf-8")
    for c3 in data3["candidates"]:
        callout = f"> [!relation/related_to]+ 已派生为 [[节点/{c3['resolved_name']}]] · 相关"
        expected_nl = b"\r\n" if c3["resolved_name"] == "甲小节" else b"\n"
        assert (callout.encode("utf-8") + expected_nl) in after, f"{c3['resolved_name']} 的插入行应随局部风格"
    assert after.count(b"\r\n") == before3.count(b"\r\n") + 1
    assert after.count(b"\n") == before3.count(b"\n") + 2


# ══════════════════════════ ㉔ --confirm-insert 未知 id 零写拒绝（r2-MEDIUM-2） ══════════════════════════


def test_unknown_confirm_insert_id_refuses_before_any_write(tmp_path):
    """--confirm-insert 不在本批 --confirm 里 → 在任何写盘之前拒绝（零产物）。"""
    vault = make_vault(tmp_path, "insunk", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "insunk")
    c = _cands(data, basis="board-body-section")[0]
    before = tree_map(vault)
    r = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        c["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        "bsa1-ffffffffffffffff",
    )
    assert r.returncode != 0 and "不在本批" in out2(r), out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == []


# ══════════════════════════ ㉕ 创建与插入用映射后行号（r3-HIGH-1） ══════════════════════════


def test_create_uses_fresh_mapped_lines_after_other_callout(tmp_path):
    """先给甲插 callout 再用同一 preview 建乙：乙的正文与插入点必须用映射后的当前行号。"""
    doc = board_doc([section("甲小节"), section("乙小节")])
    vault = make_vault(tmp_path, "freshmap", doc)
    pj, data = preview(vault, "板A", vault / "outputs", "freshmap")
    ca = [c for c in data["candidates"] if c["resolved_name"] == "甲小节"][0]
    cb = [c for c in data["candidates"] if c["resolved_name"] == "乙小节"][0]

    r1 = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        ca["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        ca["stable_id"],
    )
    assert r1.returncode == 0, out2(r1)

    r2 = run_apply(
        vault,
        "--preview",
        str(pj),
        "--confirm",
        cb["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        cb["stable_id"],
    )
    assert r2.returncode == 0, out2(r2)

    nb = (vault / "节点" / "乙小节.md").read_text(encoding="utf-8")
    assert BODY1 in nb and BODY2 in nb, f"乙正文应完整（映射后行号）: {nb}"
    assert "已派生为" not in nb, "乙正文不得含 callout 行"

    board_lines = (vault / "原白板" / "板A.md").read_text(encoding="utf-8").split("\n")
    idx = [i for i, ln in enumerate(board_lines) if ln.startswith("## 乙小节")][0]
    assert board_lines[idx + 1] == "> [!relation/related_to]+ 已派生为 [[节点/乙小节]] · 相关", (
        "乙的 callout 必须紧跟乙标题（映射后行号）"
    )


# ══════════════════════════ ㉖ 同基错误后缀必须被重放拦下（r4-LOW-2） ══════════════════════════


def test_same_base_wrong_suffix_tamper_is_rejected(tmp_path):
    """池里已有 甲小节/甲小节_2 → 期望 甲小节_3；手改成空闲的 甲小节_9 必须被重放拦下。"""
    vault = make_vault(
        tmp_path,
        "suffix",
        board_doc([section("甲小节")]),
        nodes={
            "甲小节": "---\ntype: concept\n---\n\n# 甲小节\n",
            "甲小节_2": "---\ntype: concept\n---\n\n# 甲小节_2\n",
        },
    )
    pj, data = preview(vault, "板A", vault / "outputs", "suffix")
    c = _cands(data, basis="board-body-section")[0]
    assert c["resolved_name"] == "甲小节_3", f"构造前提：期望名 甲小节_3, 实得 {c['resolved_name']}"

    d = json.loads(pj.read_text(encoding="utf-8"))
    for cc in d["candidates"]:
        if cc["stable_id"] == c["stable_id"]:
            cc["resolved_name"] = "甲小节_9"
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0 and ("重放" in out2(r) or "过期" in out2(r)), out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == []


# ══════════════════════════ ㉗ 残留 fail-closed：改名 / 子目录（r5-HIGH-2 · r7-HIGH-1） ══════════════════════════


def test_rename_residue_symlink_and_long_frontmatter_are_rejected(tmp_path):
    """池内归属**无法安全判定**的残留必须 fail-closed（拒绝）, 而不是从减法中消失：
    A) symlink 残留; B) split_stable_id 被 >199 行 frontmatter 推到 200 行之后的改名残留。"""
    # ── 路径 A: symlink 残留不得被跳过 ──
    vault = make_vault(tmp_path, "residA", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "residA")
    c = _cands(data, basis="board-body-section")[0]
    r1 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r1.returncode == 0, out2(r1)
    node = vault / "节点" / "甲小节.md"
    assert node.is_file(), "构造前提：先有本 preview 产物"

    moved = tmp_path / "moved-甲小节.md"
    node.rename(moved)
    (vault / "节点" / "改名.md").symlink_to(moved)
    before = tree_map(vault)
    r2 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r2.returncode != 0, f"symlink 残留不得放行重建同 id 副本: {out2(r2)}"
    assert "symlink" in out2(r2), out2(r2)
    assert tree_map(vault) == before, "拒绝路径必须零产物"
    assert not node.exists(), "旧名不得被当作「空闲」再建"
    assert len(batch_dirs(vault)) == 1, "拒绝路径不得再建批次目录"

    # ── 路径 B: >199 行 frontmatter 之后的 id 也必须被读出来 ──
    vault2 = make_vault(tmp_path, "residB", board_doc([section("甲小节")]))
    pj2, data2 = preview(vault2, "板A", vault2 / "outputs", "residB")
    c2 = _cands(data2, basis="board-body-section")[0]
    r3 = run_apply(vault2, "--preview", str(pj2), "--confirm", c2["stable_id"], "--apply")
    assert r3.returncode == 0, out2(r3)
    node2 = vault2 / "节点" / "甲小节.md"
    lines = node2.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "---", "构造前提：节点以 frontmatter 开头"
    pad = [f"pad_{i}: x" for i in range(220)]
    node2.write_text("\n".join([lines[0], *pad, *lines[1:]]), encoding="utf-8")
    node2.rename(vault2 / "节点" / "改名2.md")
    before2 = tree_map(vault2)
    r4 = run_apply(vault2, "--preview", str(pj2), "--confirm", c2["stable_id"], "--apply")
    assert r4.returncode != 0, f"超长 frontmatter 的改名残留不得放行重建: {out2(r4)}"
    assert "同 stable_id 的残留节点" in out2(r4), out2(r4)
    assert tree_map(vault2) == before2, "拒绝路径必须零产物"
    assert len(batch_dirs(vault2)) == 1, "拒绝路径不得再建批次目录"


# ══════════════════════════ ㉘ 预览时真实 callout 形态行：绝不静默剔行（r5-HIGH-3） ══════════════════════════


def test_preview_era_callout_line_is_never_silently_dropped(tmp_path):
    """preview 时已是正文的真实内容行（形如「已派生为 [[节点/某]]」, 已进内容指纹）:
    要么拒绝（零产物）、要么原样保留 —— 绝不允许静默剔行产出一个少行的节点。
    （当前实测: 该形态被门① 的行号对账保守拒绝, 故「只在容差路径剔行」由 ㉙ 在函数面钉住。）"""
    real_line = "备注：已派生为 [[节点/某]]，必须保留"
    doc = board_doc([section("甲小节", [BODY1, BODY2, real_line])])
    vault = make_vault(tmp_path, "pvcallout", doc)
    pj, data = preview(vault, "板A", vault / "outputs", "pvcallout")
    c = _cands(data, basis="board-body-section")[0]
    before = tree_map(vault)
    node = vault / "节点" / f"{c['resolved_name']}.md"

    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    if r.returncode == 0:
        nb = node.read_text(encoding="utf-8")
        assert real_line in nb and BODY1 in nb and BODY2 in nb, f"接受路径必须原样保留真实行: {nb}"
    else:
        assert tree_map(vault) == before and not node.exists(), f"拒绝路径必须零产物: {out2(r)}"


# ══════════════════════════ ㉙ 门① 两层判定必须区分（r5-HIGH-3 函数面钉） ══════════════════════════


def _load_apply_module():
    spec = importlib.util.spec_from_file_location("g510_split_apply_uut", SPLIT_APPLY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_span_drift_reason_distinguishes_exact_from_callout_tolerance(tmp_path):
    """原字节指纹精确相符 ⇒ (None, False)：run_create 不得剔行（预览时的真实 callout 形态行
    属于内容单元）; 本候选 callout 插入后 ⇒ (None, True)：容差解释生效, 才可燃行。"""
    mod = _load_apply_module()
    real_line = "备注：已派生为 [[节点/某]]，必须保留"
    vault_a = make_vault(tmp_path, "modeA", board_doc([section("甲小节", [BODY1, BODY2, real_line])]))
    pj_a, data_a = preview(vault_a, "板A", vault_a / "outputs", "modeA")
    ca = _cands(data_a, basis="board-body-section")[0]
    assert mod._span_drift_reason(vault_a, ca, ca["content_fingerprint"]) == (None, False)

    vault_b = make_vault(tmp_path, "modeB", board_doc([section("甲小节")]))
    pj_b, data_b = preview(vault_b, "板A", vault_b / "outputs", "modeB")
    cb = _cands(data_b, basis="board-body-section")[0]
    board = vault_b / "原白板" / "板A.md"
    lines = board.read_text(encoding="utf-8").split("\n")
    ls = cb["source_anchor"]["line_start"]
    board.write_text("\n".join(lines[:ls] + [mod.callout_line(cb["resolved_name"])] + lines[ls:]), encoding="utf-8")
    assert mod._span_drift_reason(vault_b, cb, cb["content_fingerprint"]) == (None, True)


# ══════════════════════════ ㉚ 指纹绑定：改板正文 + 只抄新指纹必须被拒（r5-HIGH-1） ══════════════════════════


def test_board_edit_with_copied_fingerprint_is_rejected(tmp_path):
    """r5 复现：甲小节 preview → 正文 BODY2 改 BODY_ALT → 新 preview 的新指纹只抄进旧 JSON
    → 用旧 stable_id apply：必须拒绝、零产物（旧代码会放行并建出改后正文）。"""
    vault = make_vault(tmp_path, "fpbind", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "fpbind")
    c = _cands(data, basis="board-body-section")[0]

    board = vault / "原白板" / "板A.md"
    board.write_text(board.read_text(encoding="utf-8").replace(BODY2, BODY_ALT), encoding="utf-8")
    _, data2 = preview(vault, "板A", tmp_path / "out2", "fpbind2")
    fresh_fp = [x for x in data2["candidates"] if x["stable_id"] == c["stable_id"]][0]["content_fingerprint"]
    d = json.loads(pj.read_text(encoding="utf-8"))
    for x in d["candidates"]:
        if x["stable_id"] == c["stable_id"]:
            x["content_fingerprint"] = fresh_fp
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0, f"改板 + 抄指纹不得放行: {out2(r)}"
    assert "过期" in out2(r), out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == [], "拒绝必须零产物"


# ══════════════════════════ ㉛ 指纹绑定：种子笔记同洞（r5-HIGH-1 的 board-only 反例） ══════════════════════════


def test_seed_note_edit_with_copied_fingerprint_is_rejected(tmp_path):
    """锚文件是种子笔记（basis=seed-note-section）时同一个洞必须同样被堵：改种子正文 +
    只抄新指纹 → 拒绝、零产物。"""
    doc = (
        "---\ntype: whiteboard\n---\n\n# 主板\n\n## Concepts\n\n"
        "- [[节点/种子甲]] — 种子 · 掌握度 — · 未考\n\n" + section("甲小节")
    )
    seed = "---\ntype: concept\n---\n\n# 种子讲义\n\n" + section("一节")
    vault = make_vault(tmp_path, "seedfp", doc, nodes={"种子甲": seed})
    pj, data = preview(vault, "板A", vault / "outputs", "seedfp")
    c = _cands(data, basis="seed-note-section")[0]
    assert c["source_anchor"]["file"] == "节点/种子甲.md", f"构造前提：种子锚, 实得 {c['source_anchor']['file']}"

    seed_path = vault / "节点" / "种子甲.md"
    seed_path.write_text(seed_path.read_text(encoding="utf-8").replace(BODY2, BODY_ALT), encoding="utf-8")
    _, data2 = preview(vault, "板A", tmp_path / "out2", "seedfp2")
    fresh_fp = [x for x in data2["candidates"] if x["stable_id"] == c["stable_id"]][0]["content_fingerprint"]
    d = json.loads(pj.read_text(encoding="utf-8"))
    for x in d["candidates"]:
        if x["stable_id"] == c["stable_id"]:
            x["content_fingerprint"] = fresh_fp
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0, f"种子正文改动 + 抄指纹不得放行: {out2(r)}"
    assert "过期" in out2(r), out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == [], "拒绝必须零产物"


# ══════════════════════════ ㉜ 字节锚容差面：preview 时既存的非本轮 callout 不得被误剔 ══════════════════════════


def test_byte_anchor_tolerance_spares_non_candidate_callouts(tmp_path):
    """板上 preview 时就存在的精确形态 callout（在本轮候选名之外, 且落在机器 fence 里）不得被
    本轮容忍面误剔：本轮自己的插入 + 重跑必须放行（strip-all 会把既存那条一并剔掉 → 永久拒绝）。
    注：不构造「重跑 preview 后再 apply」的多轮形态 —— 那会先撞 r5-LOW-1 的改名残留门（既有行为）。"""
    trail = "## 尾注\n\n```\n> [!relation/related_to]+ 已派生为 [[节点/旧轮产物]] · 相关\n```\n\n"
    vault = make_vault(tmp_path, "anchor", board_doc([section("甲小节")]) + trail)
    pj, data = preview(vault, "板A", vault / "outputs", "anchor")
    c = _cands(data, basis="board-body-section")[0]
    assert c["resolved_name"] == "甲小节", f"构造前提：stub 即标题原文, 实得 {c['resolved_name']}"
    cmd = (
        "--preview",
        str(pj),
        "--confirm",
        c["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        c["stable_id"],
    )
    r1 = run_apply(vault, *cmd)
    assert r1.returncode == 0, out2(r1)
    assert "callout_inserted=1" in out2(r1), out2(r1)
    r2 = run_apply(vault, *cmd)
    assert r2.returncode == 0, f"字节锚容忍面不得误剔 preview 时既存的 callout: {out2(r2)}"
    assert "过期" not in out2(r2)


# ══════════════════════════ ㉝ 字节锚自洽：sources[] 与 board_sha256 双写必须一致 ══════════════════════════


def test_inconsistent_sources_board_sha_is_rejected(tmp_path):
    """把 sources[] 里板记录的 sha256 改花（board_sha256 不动）→ 内部自洽对账必须拒绝。"""
    vault = make_vault(tmp_path, "selfct", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "selfct")
    c = _cands(data, basis="board-body-section")[0]

    d = json.loads(pj.read_text(encoding="utf-8"))
    d["sources"][0]["sha256"] = "0" * 64
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = tree_map(vault)
    r = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r.returncode != 0, f"双写不自洽不得放行: {out2(r)}"
    assert "过期" in out2(r), out2(r)
    assert tree_map(vault) == before and batch_dirs(vault) == [], "拒绝必须零产物"


# ══════════════════════════ ㉞ 残留：移入子目录 + 改名（r6-HIGH-1） ══════════════════════════


def test_residue_in_subdirectory_is_rejected(tmp_path):
    """把本 preview 产物移进 节点/子目录/ 后：旧顶层名不得被当「空闲」再建同 id 副本。"""
    vault = make_vault(tmp_path, "subdir", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "subdir")
    c = _cands(data, basis="board-body-section")[0]
    r1 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r1.returncode == 0, out2(r1)
    node = vault / "节点" / "甲小节.md"
    assert node.is_file(), "构造前提：先有本 preview 产物"

    arch = vault / "节点" / "archive"
    arch.mkdir()
    node.rename(arch / "改名.md")
    before = tree_map(vault)
    r2 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r2.returncode != 0, f"子目录残留不得放行重建同 id 副本: {out2(r2)}"
    assert "同 stable_id 的残留节点" in out2(r2), out2(r2)
    assert tree_map(vault) == before, "拒绝路径必须零产物"
    assert not node.exists(), "旧顶层名不得被当作「空闲」再建"


# ══════════════════════════ ㉟ 字节锚容忍面：机器 fence 里的同形行不得被误剔（r6-MEDIUM-1） ══════════════════════════


def test_fenced_same_name_callout_does_not_break_rerun(tmp_path):
    """fence 里的同形行（preview 时既存, 且引用**本轮候选名**）不得被字节锚容忍面误剔：
    插入 + 重跑必须放行（与 derived_names_in 的机器段口径一致）。"""
    fenced = "```\n> [!relation/related_to]+ 已派生为 [[节点/甲小节]] · 相关\n```"
    doc = board_doc([section("甲小节")]) + "## 尾注\n\n" + fenced + "\n\n"
    vault = make_vault(tmp_path, "fenced", doc)
    pj, data = preview(vault, "板A", vault / "outputs", "fenced")
    c = _cands(data, basis="board-body-section")[0]
    assert c["resolved_name"] == "甲小节", f"构造前提：stub 即标题原文, 实得 {c['resolved_name']}"
    cmd = (
        "--preview",
        str(pj),
        "--confirm",
        c["stable_id"],
        "--apply",
        "--insert-callout",
        "--confirm-insert",
        c["stable_id"],
    )
    r1 = run_apply(vault, *cmd)
    assert r1.returncode == 0, out2(r1)
    assert "callout_inserted=1" in out2(r1), out2(r1)
    r2 = run_apply(vault, *cmd)
    assert r2.returncode == 0, f"fence 里的同形行不得让字节锚误拒重跑: {out2(r2)}"
    assert "过期" not in out2(r2)


# ══════════════════════════ ㊱ 残留：移入子目录 + 保持原名（r7-HIGH-1） ══════════════════════════


def test_residue_in_subdirectory_with_same_name_is_rejected(tmp_path):
    """产物移进 节点/子目录/ 但**保持原名**时 stem 与账上名相等 —— 仍必须拒绝：只有 canonical
    顶层路径 节点/<账上名>.md 才算自家产物，其余位置一律 fail-closed。"""
    vault = make_vault(tmp_path, "subdir2", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "subdir2")
    c = _cands(data, basis="board-body-section")[0]
    r1 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r1.returncode == 0, out2(r1)
    node = vault / "节点" / "甲小节.md"
    assert node.is_file(), "构造前提：先有本 preview 产物"

    arch = vault / "节点" / "archive"
    arch.mkdir()
    node.rename(arch / "甲小节.md")  # 只改路径、保持原名（stem 与账上名相等）
    before = tree_map(vault)
    r2 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r2.returncode != 0, f"子目录同名残留不得放行重建同 id 副本: {out2(r2)}"
    assert "同 stable_id 的残留节点" in out2(r2), out2(r2)
    assert tree_map(vault) == before, "拒绝路径必须零产物"
    assert not node.exists(), "旧顶层路径不得被当作「空闲」再建"


# ══════════════════════════ ㊲ 残留：不可列举子目录 + 保持原名（r8-HIGH-1） ══════════════════════════


def test_residue_in_unlistable_subdirectory_is_rejected(tmp_path):
    """子目录 chmod 000（不可列举）时不得静默漏过：枚举失败必须 fail-closed 拒绝整批
    （`rglob` 会静默吞掉遍历 `OSError` —— 本用例钉住显式 `scandir` 走法）。权限在 finally 恢复。"""
    if os.geteuid() == 0:
        pytest.skip("root 不受 chmod 000 限制, 本用例不适用")
    vault = make_vault(tmp_path, "unlistable", board_doc([section("甲小节")]))
    pj, data = preview(vault, "板A", vault / "outputs", "unlistable")
    c = _cands(data, basis="board-body-section")[0]
    r1 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    assert r1.returncode == 0, out2(r1)
    node = vault / "节点" / "甲小节.md"
    assert node.is_file(), "构造前提：先有本 preview 产物"

    arch = vault / "节点" / "archive"
    arch.mkdir()
    node.rename(arch / "甲小节.md")  # 保持原名藏进子目录, 再令其不可列举
    n_batches = len(batch_dirs(vault))
    os.chmod(arch, 0o000)
    try:
        r2 = run_apply(vault, "--preview", str(pj), "--confirm", c["stable_id"], "--apply")
    finally:
        os.chmod(arch, 0o700)
    assert r2.returncode != 0, f"不可列举目录必须 fail-closed: {out2(r2)}"
    assert "无法枚举" in out2(r2), out2(r2)
    assert not node.exists(), "旧顶层路径不得被当作「空闲」再建"
    assert len(batch_dirs(vault)) == n_batches, "拒绝路径不得再建批次目录"
