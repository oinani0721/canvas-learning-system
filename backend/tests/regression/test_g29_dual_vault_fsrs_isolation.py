"""CARD-G2-9 (c) — 双 vault 的 FSRS frontmatter 与通知链互不影响。

沿 ``test_daily_review_run.py::test_two_vaults_same_day_push_and_state_isolated``
(C1a, :386) 的形态扩一条。C1a 锁的是 **state 隔离**（vault A 当日推送后 B 仍
能推、两个 state 文件独立、互跑后缓存门仍 cached）；本条往前一步锁**投影内容
本身**：

  1. **FSRS frontmatter 只影响本 vault 的到期判定** —— A 的节点无 ``fsrs_due``
     （New 卡即刻到期），B 的节点 ``fsrs_due`` 在远未来（未到期）。A 的投影里
     有到期节点、B 的没有；把 B 的 ``fsrs_due`` 翻成过去之后 B 才有，而 A 的
     投影**逐字不变**。
  2. **两边的投影产物逐字节无交叉** —— A 的 今日复习.json / .md / state 文件
     里不得出现 B 的任何独有标识（节点名 / 板名 / vault 名），反之亦然。
  3. **通知链各自独立** —— send 侧拿到的 ``vault_id`` 分别是 A / B，且 A 的
     推送不会让 B 当日 skip。

已知局限（与 C1a 同源，如实声明）：本测两库跑在**同一 Python 进程**，证的是
投影与 state 的隔离，**不证**生产「一库一进程」契约 —— 后者由 wrapper shell
层循环保证。

⛔ ``send_bark.send`` 必须 monkeypatch 掉：``daily_review_run`` 在推送窗口内
会**真发 Bark 通知**（历史上探针脚本因此发出过真实推送）。
"""

import json
import os
import shutil
import sys
from datetime import time as dtime
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WT / "scripts"))

import daily_review_run as runner  # noqa: E402  # pyright: ignore[reportMissingImports]
#   ^ 仓库根 scripts/ 由上面的 sys.path.insert 接入，静态分析器看不到

NOW_ARG = "2026-07-30T10:00:00+08:00"

#: A 与 B 各自的**独有**标识。交叉断言就是拿这些串去对方的产物里 grep。
A_NODE, B_NODE = "甲A节点", "乙B节点"
A_BOARD, B_BOARD = "A专属板", "B专属板"
FUTURE_DUE = "2099-01-01T00:00:00Z"
PAST_DUE = "2020-01-01T00:00:00Z"


def _node(board: str, fsrs_due: str = "") -> str:
    extra = f"fsrs_due: {fsrs_due}\n" if fsrs_due else ""
    return f'---\ntype: concept\nsource_board: "[[原白板/{board}]]"\n{extra}---\n真实内容。\n'


def _vault(tmp_path: Path, nodes: dict, name: str) -> Path:
    vault = tmp_path / name
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    (vault / "节点").mkdir()
    shutil.copy(WT / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py", scripts)
    for fname, content in nodes.items():
        (vault / "节点" / f"{fname}.md").write_text(content, encoding="utf-8")
    return vault


def _projection_texts(vault: Path, backups: Path) -> dict[str, str]:
    """本 vault 的全部投影产物文本（json / md / state）。**缺文件即断言失败**。

    ⛔ 初版把缺失的文件读成空串（Codex round-1 LOW-4）：下游的交叉排除断言是
    ``foreign not in text``，而 ``foreign not in ""`` **恒真** —— 投影一旦没生成，
    "两库产物无交叉"就变成一句在空字符串上做的、永远成立的话。
    2026-09-05 实测三份产物都确实生成（md 1115 字节且含本库节点名），所以当时
    没有真的假绿；但判据不能靠"碰巧生成了"站住，前提要自己断言。
    """
    out = {}
    for rel in ("outputs/今日复习.json", "outputs/今日复习.md"):
        p = vault / rel
        assert p.exists(), f"{vault.name} 的投影 {rel} 没生成——交叉排除断言会在空串上恒真"
        text = p.read_text(encoding="utf-8")
        assert text.strip(), f"{vault.name} 的投影 {rel} 是空文件——同上"
        out[rel] = text
    state = backups / f"daily-review.{vault.name}.state.json"
    assert state.exists(), f"{vault.name} 的 state 文件没生成"
    out["state"] = state.read_text(encoding="utf-8")
    return out


def _due_node_names(vault: Path) -> set:
    payload = json.loads((vault / "outputs" / "今日复习.json").read_text(encoding="utf-8"))
    return {d["node"] for d in payload["due_nodes"]}


def test_two_vaults_fsrs_and_notification_chain_isolated(tmp_path, monkeypatch, capsys):
    """(c) FSRS frontmatter 与通知链在两个 vault 之间互不影响。"""
    vault_a = _vault(tmp_path, {A_NODE: _node(A_BOARD)}, name="vaultA")
    vault_b = _vault(tmp_path, {B_NODE: _node(B_BOARD, fsrs_due=FUTURE_DUE)}, name="vaultB")
    backups = tmp_path / "backups"
    monkeypatch.setattr(runner, "BACKUPS", backups)
    # runner.main 会改写模块全局 VAULT —— 先登记原值，teardown 恢复（C1a M1）
    monkeypatch.setattr(runner, "VAULT", runner.VAULT)
    # 窗口门放行（机器时区无关）：本测锁投影隔离，不锁窗口语义
    monkeypatch.setattr(runner, "PUSH_WINDOW", (dtime(0, 0), dtime(23, 59, 59)))

    sent = []
    monkeypatch.setattr(
        runner.send_bark,
        "send",
        lambda noti, vault_id=None: sent.append((noti["id"], vault_id)) or 0,
    )

    def _run(vault: Path) -> str:
        monkeypatch.setattr(sys, "argv", ["daily_review_run.py", "--now", NOW_ARG, "--vault", str(vault)])
        assert runner.main() == 0
        return capsys.readouterr().out

    # ── 1. FSRS 到期判定各自独立 ──
    out_a = _run(vault_a)
    out_b = _run(vault_b)
    assert "generate:new" in out_a and "generate:new" in out_b

    assert _due_node_names(vault_a) == {A_NODE}, "A 的无 fsrs_due 节点是 New 卡，必须即刻到期"
    assert _due_node_names(vault_b) == set(), f"B 的节点 fsrs_due={FUTURE_DUE} 远未到期，不该出现在 B 的投影里"

    # ── 2. 投影产物逐字节无交叉 ──
    texts_a = _projection_texts(vault_a, backups)
    texts_b = _projection_texts(vault_b, backups)
    # 排除异库标识之前，先确认每份产物**确实含本库内容**——否则"不含对方"
    # 可能只是因为它什么都不含（LOW-4 的另一半）。
    assert A_NODE in texts_a["outputs/今日复习.json"], "A 的 json 里没有 A 自己的节点"
    assert A_NODE in texts_a["outputs/今日复习.md"], "A 的 md 里没有 A 自己的节点"
    # ⚠️ state 的 **内容里没有 vault 名**——vault 维度在**文件名**上
    # （daily-review.<vault>.state.json）。所以下面交叉排除里的 `"vaultB" not in
    # state_a` 是一条**空断言**（两份 state 都不含任何 vault 名），真正承重的是
    # 板名那一项：state 内容含 board_last_recommended，A 的板名不该出现在 B 的
    # state 里。这条前提断言就是钉住"板名确实在里面"，免得空断言被当成证据。
    assert A_BOARD in texts_a["state"], "A 的 state 里没有 A 自己的板名（交叉断言会落空）"
    # B 侧同样要有本库标识，否则 B→A 方向的交叉排除也是空断言（round-2 复核 LOW）。
    assert B_NODE in texts_b["outputs/今日复习.json"], "B 的 json 里没有 B 自己的节点"
    assert B_BOARD in texts_b["outputs/今日复习.json"], "B 的 json 里没有 B 自己的板名"
    # ⚠️ **B 的 state 刻意不加这条前提，如实说明为什么**：本场景里 B 的节点
    #    fsrs_due 在远未来 ⇒ B 无到期节点 ⇒ `board_last_recommended` 是 `{}`，
    #    B 的 state 天然不含任何板名。所以 B→A 方向**在 state 这一栏上**的交叉
    #    排除是空断言——不是漏写，是这一栏本来就没有可泄漏的载体。承重的是
    #    B 的 json / md 两栏（上面两条前提钉住了它们确有 B 的标识）。
    #    第四轮（下面 fsrs_due 翻成过去之后）B 才会有板名进 state。
    for rel, text in texts_a.items():
        for foreign in (B_NODE, B_BOARD, "vaultB"):
            assert foreign not in text, f"A 的 {rel} 里出现了 B 的独有标识 {foreign!r}"
    for rel, text in texts_b.items():
        for foreign in (A_NODE, A_BOARD, "vaultA"):
            assert foreign not in text, f"B 的 {rel} 里出现了 A 的独有标识 {foreign!r}"
    # 两个 state 文件必须真的是两个文件（不是同一份被轮流覆盖）
    assert (backups / "daily-review.vaultA.state.json").exists()
    assert (backups / "daily-review.vaultB.state.json").exists()
    assert texts_a["state"] != texts_b["state"]

    # ── 3. 通知链各自独立：A 推过之后 B 当日仍可推 ──
    assert [v for _, v in sent] == ["vaultA", "vaultB"]

    # ── 4. 翻转 B 的 FSRS 状态：B 变有到期，A 的投影逐字不变 ──
    a_json_before = texts_a["outputs/今日复习.json"]
    (vault_b / "节点" / f"{B_NODE}.md").write_text(_node(B_BOARD, fsrs_due=PAST_DUE), encoding="utf-8")
    # 让 B 的节点池比 payload 新 → 触发同日重扫（A3 缓存失效语义）
    payload_mtime = (vault_b / "outputs" / "今日复习.json").stat().st_mtime
    for p in (vault_b / "节点" / f"{B_NODE}.md", vault_b / "节点"):
        os.utime(p, (payload_mtime + 200, payload_mtime + 200))

    _run(vault_b)
    assert _due_node_names(vault_b) == {B_NODE}, (
        "B 的 fsrs_due 翻成过去后必须到期（证明 FSRS 判定读的是 B 自己的 frontmatter）"
    )
    assert (vault_a / "outputs" / "今日复习.json").read_text(encoding="utf-8") == a_json_before, (
        "改 B 的 frontmatter 不得让 A 的投影发生任何变化"
    )
    assert _due_node_names(vault_a) == {A_NODE}


def test_vault_a_push_does_not_consume_vault_b_same_day_slot(tmp_path, monkeypatch, capsys):
    """(c) 通知链：两 vault 同日各推一次，第二轮各自 skip-done，互不串扰。

    与 C1a :386 的第二轮同语义，但这里两个 vault 的**节点集完全不同**，
    额外核对 log 行里两条 vault 记录并存（单一全局 state 会只剩一条）。
    """
    vault_a = _vault(tmp_path, {A_NODE: _node(A_BOARD)}, name="vaultA")
    vault_b = _vault(tmp_path, {B_NODE: _node(B_BOARD)}, name="vaultB")
    backups = tmp_path / "backups"
    monkeypatch.setattr(runner, "BACKUPS", backups)
    monkeypatch.setattr(runner, "VAULT", runner.VAULT)
    monkeypatch.setattr(runner, "PUSH_WINDOW", (dtime(0, 0), dtime(23, 59, 59)))
    sent = []
    monkeypatch.setattr(
        runner.send_bark,
        "send",
        lambda noti, vault_id=None: sent.append((noti["id"], vault_id)) or 0,
    )

    def _run(vault: Path) -> str:
        monkeypatch.setattr(sys, "argv", ["daily_review_run.py", "--now", NOW_ARG, "--vault", str(vault)])
        assert runner.main() == 0
        return capsys.readouterr().out

    assert "push:accepted" in _run(vault_a)
    assert "push:accepted" in _run(vault_b), "A 推过后 B 同日必须仍可推送（state 全局单例会误判 skip-done）"
    assert len(sent) == 2

    # 第二轮：节点池钉到 payload 之前 → 各自走缓存 + 同日去重
    for vault in (vault_a, vault_b):
        payload_ts = (vault / "outputs" / "今日复习.json").stat().st_mtime
        for p in list((vault / "节点").glob("*.md")) + [vault / "节点"]:
            os.utime(p, (payload_ts - 100, payload_ts - 100))
    out_a2, out_b2 = _run(vault_a), _run(vault_b)
    assert "generate:cached" in out_a2 and "push:skip-done" in out_a2
    assert "generate:cached" in out_b2 and "push:skip-done" in out_b2
    assert len(sent) == 2, "第二轮不得再发推送"

    log_text = (backups / "daily-review.log").read_text(encoding="utf-8")
    assert "vault=vaultA" in log_text and "vault=vaultB" in log_text
