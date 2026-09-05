"""CARD-G6-3 · 「答错 → 到期 → UI 可见」端到端时序取证（完成条件 a）。

零产品代码改动：本脚本只**读**生产链路（真实 `py-fsrs` 对象、真实生产器
`scripts/daily_review_pick.py`、真实 `GET /api/v1/review/overview` 端点），
在 tmp vault 上跑，不碰 live vault、不连 7691。**禁 FakeCard** —— 到期时刻由
真实 `fsrs.Scheduler().review_card(Card(), Rating.Again, T0)` 算出。

链路事实（开工勘探所得，决定了本脚本为什么要量**两条**路径）
------------------------------------------------------------
UI 的数据源 `GET /overview` → `_collect()` → `_vault_entry()` 读的是 vault 里
**预生成的** `outputs/今日复习.json`；`_summarize()` 的 docstring 写明
「**不重算到期口径**」。而生产器 `daily_review_pick.py:561` 是
`"due_now": (not fsrs_due) or fsrs_due <= now_z` —— 到期与否在**投影生成那一刻**
就定死了。

⇒ 自动轮询再快也只是把同一个 JSON 重读一遍。一张卡答错后新排的到期时刻，
   只有在**投影被重建之后**才可能出现在 UI 数据源里。

所以「5 秒可见」这个问题必须拆成两条路径分别量，否则结论会骗人：

- **路径 A（真实默认场景）**：答错 → 到期 → 只有自动轮询在跑（UI 的自动轮询
  **绝不** POST refresh，这是产品的默认裁决②）。量：到 due+5s 为止，UI 数据源
  里到底有没有这张卡。
- **路径 B（有人触发重建）**：到期后重建投影，再量从 due 到「UI 数据源含该卡」
  的时延。这条量的是**重建 + 读取**本身有多快。

两条都跑三轮，逐轮把实测时延写进本目录。

跑法（从 backend/ 起）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g63/e2e_relearn_visibility.py

退出码 0 = 三轮都跑完且各自的观测自洽（**不代表 due+5s 达标**——达标与否是
本脚本要如实报告的**结论**，不是它的通过条件；把结论塞进退出码就成了
「边做边降标准」）。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "backend"
PICKER = REPO / "scripts" / "daily_review_pick.py"
DECAY = REPO / "canvas-vault" / ".claude" / "scripts" / "decay_beta.py"

#: 正式取证跑 3 轮（卡文要求）。`G63_ROUNDS=1` 只用于开发期烟测，
#: 验收单里引用的数字一律来自 3 轮那次。
ROUNDS = int(os.environ.get("G63_ROUNDS", "3"))
NODE_NAME = "重学卡"
BOARD = "闭环取证板"
#: 自动轮询的 clamp 下限（review_app.py:159 `POLL_MIN_MS = 5000`）——
#: 路径 A 就按这个最快节奏轮询，给产品最有利的假设。
POLL_MIN_S = 5.0
#: 观测窗口：到期后再多观察这么久。卡文的目标是 due+5s。
WATCH_AFTER_DUE_S = 5.0


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_vault(root: Path, name: str, fsrs_due: str, fsrs_state: int) -> Path:
    """一个最小但**真实**的 vault：含 .obsidian/（端点的候选判据）、节点 md、
    生产器要 import 的 decay_beta.py。结构照搬 tests/regression/test_daily_review_pick.py。"""
    vault = root / name
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "节点").mkdir()
    scripts = vault / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(DECAY, scripts)
    (vault / "节点" / f"{NODE_NAME}.md").write_text(
        "---\n"
        "type: concept\n"
        f'source_board: "[[原白板/{BOARD}]]"\n'
        f"fsrs_due: {fsrs_due}\n"
        f"fsrs_state: {fsrs_state}\n"
        "---\n"
        "答错过的内容。\n",
        encoding="utf-8",
    )
    return vault


def _rebuild(vault: Path, now: datetime | None = None) -> tuple[float, int]:
    """跑真实生产器 --write，返回 (耗时秒, rc)。"""
    cmd = [sys.executable, str(PICKER), "--vault", str(vault), "--write"]
    if now is not None:
        cmd += ["--now", _iso_z(now)]
    t0 = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    dt = time.monotonic() - t0
    if p.returncode != 0:
        print(f"  ⚠ 生产器 rc={p.returncode}\n{p.stdout[-800:]}\n{p.stderr[-800:]}", file=sys.stderr)
    return dt, p.returncode


def _due_node_names(client, vault_name: str) -> tuple[list[str], int]:
    """从 UI 数据源（GET /overview）取该库的到期节点名与权威 due_count。"""
    r = client.get("/api/v1/review/overview")
    r.raise_for_status()
    for v in r.json()["vaults"]:
        if v["vault_id"] != vault_name:
            continue
        proj = v.get("projection")
        if not proj:
            return [], 0
        # 节点明细挂在**板行下**（_summarize 顶层只有 due_count / boards），
        # 板行里的 nodes 就是 review_overview._node_detail_html 渲染给用户看的那批。
        nodes = [
            n["node"]
            for b in (proj.get("boards") or [])
            for n in (b.get("nodes") or [])
        ]
        return nodes, int(proj.get("due_count") or 0)
    return [], 0


def main() -> int:  # noqa: C901
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True

    import tempfile

    import app.config as config_mod
    import app.main as main_mod
    from app.config import reload_settings
    from fastapi.testclient import TestClient
    from fsrs import Card, Rating, Scheduler

    scheduler = Scheduler()
    print(f"真实 py-fsrs learning_steps = {scheduler.learning_steps}")

    rounds: list[dict] = []
    saved = {k: os.environ.get(k) for k in ("VAULTS_ROOT", "ACTIVE_VAULT")}
    tmp = tempfile.TemporaryDirectory(prefix="g63_e2e_")
    root = Path(tmp.name)
    try:
        reload_settings(overrides={"VAULTS_ROOT": str(root), "ACTIVE_VAULT": "r1"})
        main_mod.settings = config_mod.settings
        from app.main import app

        client = TestClient(app, base_url="http://127.0.0.1:8011")  # 裸构造: 不起 lifespan
        try:
            for i in range(1, ROUNDS + 1):
                name = f"r{i}"
                print(f"\n=== 第 {i}/{ROUNDS} 轮 ===")

                # ── ① 真实 FSRS：答错一张新卡 ──
                t0 = datetime.now(timezone.utc)
                card_after, _log = scheduler.review_card(Card(), Rating.Again, t0)
                due = card_after.due
                state = int(card_after.state)
                lead_s = (due - t0).total_seconds()
                print(f"  答错 → due={_iso_z(due)} state={state} (距今 {lead_s:.1f}s)")

                vault = _build_vault(root, name, _iso_z(due), state)

                # ── ② 在**到期之前**生成一次投影（真实场景：上一次定时重建） ──
                gen_dt, rc = _rebuild(vault, now=t0)
                if rc != 0:
                    return 1
                pre_nodes, pre_due = _due_node_names(client, name)
                print(f"  到期前投影: due_count={pre_due} nodes={pre_nodes} (生成耗时 {gen_dt:.2f}s)")

                # ── ③ 路径 A：只靠自动轮询（不重建），一路轮询到 due+5s ──
                a_visible_at: float | None = None
                polls = 0
                deadline = due.timestamp() + WATCH_AFTER_DUE_S
                while time.time() < deadline:
                    nodes, cnt = _due_node_names(client, name)
                    polls += 1
                    if NODE_NAME in nodes and a_visible_at is None:
                        a_visible_at = time.time() - due.timestamp()
                        break
                    time.sleep(min(POLL_MIN_S, max(0.2, deadline - time.time())))
                # 到 due+5s 这一刻再看最后一眼
                nodes_a, cnt_a = _due_node_names(client, name)
                polls += 1
                if NODE_NAME in nodes_a and a_visible_at is None:
                    a_visible_at = time.time() - due.timestamp()
                print(
                    f"  路径A(仅轮询, {polls} 次): "
                    + (f"due+{a_visible_at:.2f}s 可见" if a_visible_at is not None
                       else f"到 due+{WATCH_AFTER_DUE_S:.0f}s 仍不可见 (due_count={cnt_a})")
                )

                # ── ④ 路径 B：到期后触发一次真实重建 ──
                # ⚠ 度量口径：本脚本是在路径 A 的观察窗口跑满（due+5s）之后才触发重建的，
                # 所以「可见的绝对时刻」里有 5s 是**我的观察窗口**占掉的，不是重建慢。
                # 必须把「什么时候触发」与「触发后多快」拆成两个数分别报，
                # 混成一个 `due+5.06s` 会被读成「重建路径要 5 秒」——那是假的。
                b_trigger_offset = time.time() - due.timestamp()
                t_trigger = time.monotonic()
                rb_dt, rc = _rebuild(vault)
                if rc != 0:
                    return 1
                nodes_b, cnt_b = _due_node_names(client, name)
                b_react_s = time.monotonic() - t_trigger      # 触发 → 可见（重建 + 读取）
                b_abs_offset = time.time() - due.timestamp()  # due → 可见（含我的观察窗口）
                visible_b = NODE_NAME in nodes_b
                print(
                    f"  路径B: 触发于 due+{b_trigger_offset:.2f}s（=我的观察窗口）, "
                    + (f"触发后 {b_react_s:.3f}s 可见（重建 {rb_dt:.3f}s）, "
                       f"绝对 due+{b_abs_offset:.2f}s, due_count={cnt_b}"
                       if visible_b else f"重建后仍不可见 (due_count={cnt_b}) ← 异常, 需查")
                )

                rounds.append({
                    "round": i, "due": _iso_z(due), "fsrs_state": state,
                    "lead_s": round(lead_s, 2),
                    "pre_due_count": pre_due, "pre_nodes": pre_nodes,
                    "gen_s": round(gen_dt, 3),
                    "a_polls": polls,
                    "a_visible_after_due_s": None if a_visible_at is None else round(a_visible_at, 2),
                    "a_due_count": cnt_a,
                    "rebuild_s": round(rb_dt, 3),
                    "b_trigger_offset_s": round(b_trigger_offset, 2),
                    "b_react_s": None if not visible_b else round(b_react_s, 3),
                    "b_abs_offset_s": None if not visible_b else round(b_abs_offset, 2),
                    "b_due_count": cnt_b,
                })
        finally:
            client.close()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        reload_settings()
        main_mod.settings = config_mod.settings
        tmp.cleanup()

    # ── 报告 ──
    a_ok = [r for r in rounds if r["a_visible_after_due_s"] is not None]
    b_ok = [r for r in rounds if r["b_react_s"] is not None]
    b_lat = [r["b_react_s"] for r in b_ok]
    (HERE / "e2e-rounds.json").write_text(json.dumps(rounds, ensure_ascii=False, indent=2), encoding="utf-8")

    L = [
        "# CARD-G6-3 · 「答错 → 到期 → UI 可见」端到端时序（完成条件 a）",
        "",
        "> 真实 `py-fsrs`（`Scheduler().review_card(Card(), Rating.Again, T0)`，"
        f"learning_steps={scheduler.learning_steps}）+ 真实生产器 `scripts/daily_review_pick.py`"
        " + 真实 `GET /api/v1/review/overview`。tmp vault，**禁 FakeCard**，不碰 live、不连 7691。",
        "",
        "## 为什么量两条路径",
        "",
        "UI 数据源 `GET /overview` → `_collect()` → `_vault_entry()` 读的是 vault 里**预生成的**",
        "`outputs/今日复习.json`；`_summarize()` docstring 写明「**不重算到期口径**」。生产器",
        "`daily_review_pick.py:561` 的 `\"due_now\": (not fsrs_due) or fsrs_due <= now_z` 说明",
        "到期与否在**投影生成那一刻**定死。⇒ 自动轮询只是把同一个 JSON 重读一遍。",
        "",
        "- **路径 A**＝真实默认场景：只有自动轮询在跑（产品裁决②：自动轮询**绝不** POST refresh）。",
        "- **路径 B**＝有人触发重建之后，量「due → UI 可见」的时延。",
        "",
        "## 逐轮实测",
        "",
        "| 轮 | 答错后 due | 到期前投影 due_count | 路径A（仅轮询，到 due+5s） | 路径B：触发时刻 | 路径B：触发后多久可见 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rounds:
        a = (f"✅ due+{r['a_visible_after_due_s']}s 可见"
             if r["a_visible_after_due_s"] is not None
             else f"❌ {r['a_polls']} 次轮询全部不可见（due_count={r['a_due_count']}）")
        b1 = f"due+{r['b_trigger_offset_s']}s（=观察窗口，非重建耗时）"
        b2 = (f"✅ **{r['b_react_s']}s**（重建 {r['rebuild_s']}s + 读取），due_count={r['b_due_count']}"
              if r["b_react_s"] is not None else "❌ 重建后仍不可见")
        L.append(f"| {r['round']} | `{r['due']}` | {r['pre_due_count']} | {a} | {b1} | {b2} |")

    L += [
        "",
        "## 结论",
        "",
        f"- **路径 A：{len(a_ok)}/{ROUNDS} 轮在 due+{WATCH_AFTER_DUE_S:.0f}s 内可见。**",
    ]
    if not a_ok:
        L += [
            f"  {ROUNDS} 轮**全部不可见**。这不是轮询太慢——轮询按 clamp 下限 5s 跑满了整个窗口，",
            "  每次都拿到同一份到期前生成的投影。**「5 秒可见」在当前架构下，只靠自动轮询不可达。**",
            "  瓶颈是投影重建的触发时机，不是前端节奏。",
        ]
    if b_ok:
        L += [
            f"- **路径 B：{len(b_ok)}/{ROUNDS} 轮可见。触发后可见耗时 "
            f"{min(b_lat):.3f}s ~ {max(b_lat):.3f}s**（重建 + 读取）。",
            "  ⚠ 表里「触发时刻」那列是 due+5s 左右，那是**本脚本的观察窗口**占掉的",
            "  （路径 A 要跑满才轮到路径 B），**不是重建慢**。真正回答「触发后多快」的是",
            "  上面这个毫秒级数字。⇒ 只要重建被触发，5 秒绰绰有余；瓶颈完全在**触发时机**。",
        ]
    L += [
        "",
        "> ⚠ 本脚本的退出码只表示三轮都跑完且观测自洽，**不表示 due+5s 达标**。",
        "> 达标与否是要如实报告的结论，把它塞进退出码就成了「边做边降标准」。",
    ]
    (HERE / "e2e-timing.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[-14:]))
    return 0 if len(rounds) == ROUNDS else 1


if __name__ == "__main__":
    raise SystemExit(main())
