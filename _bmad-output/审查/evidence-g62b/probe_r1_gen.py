"""CARD-CX-G6-2b-R1 · 完成条件 (a) 前提② 的判别实验。

前提② 的原话是「POST 侧 `:508` 记的 `n.gen` 是**发 POST 那一刻**已启动的最新
GET 代际」。`review_app.py:507` 的注释也是这么写的（「gen = 发 POST 这一刻的
最新代际」）。但代码里这一行在 `await fetch(URLS.refresh, …)` **之后**执行，
读到的是 **POST 响应返回那一刻**的 `state.pollGen`。

两说在一个场景下预测**相反**，所以可以判别，不必争论：

    POST 在飞期间，轮询又启动了一轮 GET（gen=2）——它启动于服务端重建完成
    **之前**，看到的是重建前投影。

    A 说（注释）: n.gen = 1（发 POST 那一刻）→ startGen 2 > 1 → **结算**「数字已更新」
    B 说（代码）: n.gen = 2（POST 返回那一刻）→ startGen 2 <= 2 → **不结算**，pending 留着

A 说会让重建前投影冒充重建后状态 —— 与整条因果锚要防的正是同一件事。所以
这不只是「代码比注释保守」，而是**注释描述了一个有缺陷的语义，代码实现了正确的
那个**。本实验落实哪一说为真。

配一条对照：紧接着让一轮**启动于 POST 返回之后**的 GET（gen=3）结算成功。少了它，
「没结算」可能来自 harness 根本观察不到结算（那样第一条断言由一个坏 harness 平凡
满足），也证不了前提③ 的「不会永久饿死」。

跑法（从 backend/ 起）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g62b/probe_r1_gen.py

不落盘生产文件；TestClient 裸构造（不带 with）→ 不起 lifespan、不连 7691。
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "backend"
TEST_PY = BACKEND / "tests" / "unit" / "test_review_app.py"
PROD_PY = BACKEND / "app" / "api" / "v1" / "endpoints" / "review_app.py"

CASE = r"""
import test from "node:test";
import assert from "node:assert/strict";
import {boot, flush, mkNode, matches} from "./boot.mjs";

// 重建**前**的投影 — 两条 case 里 GET 返回的都是它
const PRE = {vaults: [{vault_id: "cs_61b", status: "ok", error: null,
  projection: {due_count: 3, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "pre-rebuild", next_upcoming: null, boards: []}}]};

function setup() {
  const gets = [];
  let postResolve;
  const b = boot({
    getJson: () => {
      let r;
      const p = new Promise(x => { r = x; });
      gets.push({resolve: r});
      return {ok: true, status: 200, json: () => p};
    },
    postJson: () => ({ok: true, status: 200, json: () => new Promise(x => { postResolve = x; })}),
    hidden: false,
  });
  const btn = mkNode("btn"); btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note"); note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  const click = () => b.handlers["cards::click"](
    {target: {closest: sel => (matches(btn, sel) ? btn : null)}});
  return {b, gets, note, click, post: v => postResolve(v)};
}

test("POST 在飞期间启动的 GET 无权结算 → n.gen 取的是 POST **返回**时刻的代际", async () => {
  const {b, gets, note, click, post} = setup();

  // ① 启动: 脚本尾部的 poll() 自动发首轮 GET (gen=1)
  assert.equal(b.calls.get, 1, "前提: 启动时发一轮 GET (gen=1)");
  gets.pop().resolve(PRE);
  await flush();

  // ② 点刷新 → POST 发出并挂起
  const clickP = click();
  await flush();
  assert.equal(b.calls.post, 1, "前提: POST 已发出且尚未返回");

  // ③ POST 在飞期间, 轮询到点 → 新 GET (gen=2) 启动。它启动于服务端重建完成**之前**。
  b.handlers["document::visibilitychange"]();
  await flush();
  assert.equal(b.calls.get, 2, "前提: POST 在飞期间又启动了一轮 GET (gen=2)");
  const g2 = gets.pop();

  // ④ 切后台 —— 这样 POST 返回后 `if (!document.hidden) poll()` 不再启动 gen=3,
  //    gen=2 才仍是最新代际、能通过 poll() 里的过期检查走到 settlePendingSync。
  //    (否则 gen=2 会在过期检查处被整包丢弃, 判别实验根本走不到判据行。)
  b.document.hidden = true;
  post({rebuilt: true, reason: "rebuilt", rebuild_count: 9});
  await clickP;
  await flush();
  assert.match(note.innerHTML, /正在同步最新数字/, "前提: rebuilt 只发「正在同步」, 不预先声称");

  // ⑤ gen=2 返回重建前投影 —— 判据行在这里执行
  g2.resolve(PRE);
  await flush();

  assert.ok(!note.innerHTML.includes("数字已更新"),
    "gen=2 启动于重建完成之前, 无权结算。若它结算了 → n.gen 记的是发 POST 那一刻(A说), " +
    "重建前投影冒充了重建后状态");
  assert.match(note.innerHTML, /正在同步最新数字/, "pending 必须留着, 等下一轮更晚的 GET");
});

test("对照: 启动于 POST 返回之后的 GET (gen=3) 结算成功 → harness 观察得到结算, 且不饿死", async () => {
  const {b, gets, note, click, post} = setup();
  assert.equal(b.calls.get, 1);
  gets.pop().resolve(PRE);
  await flush();

  const clickP = click();
  await flush();
  b.handlers["document::visibilitychange"]();
  await flush();
  const g2 = gets.pop();
  b.document.hidden = true;
  post({rebuilt: true, reason: "rebuilt", rebuild_count: 9});
  await clickP;
  await flush();
  g2.resolve(PRE);
  await flush();
  assert.ok(!note.innerHTML.includes("数字已更新"), "同上: gen=2 无权结算");

  // 回前台 → visibilitychange → poll() 启动 gen=3 (启动于 POST 返回之后)
  b.document.hidden = false;
  b.handlers["document::visibilitychange"]();
  await flush();
  assert.equal(b.calls.get, 3, "前提: 回前台启动了 gen=3");
  gets.pop().resolve(PRE);
  await flush();

  assert.match(note.innerHTML, /数字已更新/,
    "gen=3 启动晚于 n.gen → 有权结算。这条同时证明: (i) harness 观察得到结算, " +
    "上一条的「没结算」不是平凡真; (ii) pending 不会永久饿死 (前提③)");
});
"""


def _tap(stdout: str, key: str) -> str:
    """从 node --test 摘要里取计数；取不到返回 -1（判据随即不成立 = fail-closed）。

    node 默认 spec reporter 打的是 `ℹ pass 2`，`--test-reporter=tap` 才是 `# pass 2`；
    两种都认。初版只写了 `#` 那一种，于是计数恒 -1、判据变红 —— 这正是「取不到就
    fail-closed」该有的表现：判据自己坏掉时报红，而不是悄悄放行（假绿）。
    """
    import re

    m = re.search(rf"^[ℹ#]\s*{key}\s+(\d+)\s*$", stdout, flags=re.M)
    return m.group(1) if m else "-1"


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True
    sha_before = hashlib.sha256(PROD_PY.read_bytes()).hexdigest()

    ns: dict = {"__file__": str(TEST_PY), "__name__": "_g62b_r1_gen"}
    exec(compile(TEST_PY.read_text(encoding="utf-8"), "<gate:gen>", "exec"), ns)  # noqa: S102

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app, base_url="http://127.0.0.1:8011")  # 裸构造: 不起 lifespan
    try:
        resp = client.get(ns["APP_PATH"])
        assert resp.status_code == 200, resp.text
        script = ns["_extract_script"](resp.text)
    finally:
        client.close()

    node = ns["_NODE"]
    if not node:
        print("❌ node 不可用 — 本探针 fail-closed, 不静默 skip", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="g62b_r1_gen_") as td:
        d = Path(td)
        (d / "page-script.js").write_text(script, encoding="utf-8")
        (d / "boot.mjs").write_text(ns["_BOOT_MJS"], encoding="utf-8")
        (d / "case.test.mjs").write_text(CASE, encoding="utf-8")
        proc = subprocess.run(
            [node, "--test", "case.test.mjs"], cwd=d, capture_output=True, text=True, timeout=120
        )

    sha_after = hashlib.sha256(PROD_PY.read_bytes()).hexdigest()
    # 判据不能只看退出码: `node --test` 在**零条 test 被收集**时同样 rc=0,
    # 那样「实验通过」由一个空跑平凡满足。计数必须对上。
    n_pass = int(_tap(proc.stdout, "pass"))
    n_fail = int(_tap(proc.stdout, "fail"))
    n_skip = int(_tap(proc.stdout, "skipped"))
    counts_ok = (n_pass, n_fail, n_skip) == (2, 0, 0)
    ok = proc.returncode == 0 and sha_before == sha_after and counts_ok
    verdict = "B 说成立（代码正确）" if (proc.returncode == 0 and counts_ok) else "A 说成立或实验失败"

    body = [
        "# CARD-CX-G6-2b-R1 · 前提② 判别实验（`n.gen` 记的是哪一刻的代际）",
        "",
        "## 命题",
        "",
        "| | n.gen 的取值 | gen=2 的 GET（启动于重建完成**之前**）| 后果 |",
        "|---|---|---|---|",
        "| **A 说**（`review_app.py:507` 注释：「发 POST 这一刻」）| 1 | `2 > 1` → **结算** | "
        "重建前投影冒充重建后状态 ❌ |",
        "| **B 说**（代码实际：`:508` 在 `await fetch` 之后，读 POST **返回**那一刻）| 2 | "
        "`2 <= 2` → **不结算** | pending 留给更晚的 GET ✅ |",
        "",
        "两说在同一场景下预测相反 → 跑一次即可分胜负，不必争论。",
        "",
        "## 实验",
        "",
        "构造：启动 GET(gen=1) 完成 → 点刷新，POST 挂起 → **POST 在飞期间**触发一轮 "
        "GET(gen=2) → 切后台（使 POST 返回后不再启动 gen=3，让 gen=2 仍是最新代际、"
        "能走到判据行）→ POST 返回 rebuilt → gen=2 返回重建前投影。",
        "",
        "对照：随后回前台启动 gen=3（启动于 POST 返回之后）并让它返回 —— 必须结算成功。"
        "少了对照，第一条的「没结算」可能由一个观察不到结算的坏 harness 平凡满足。",
        "",
        "## 结果",
        "",
        f"- node 退出码 `{proc.returncode}`，TAP 计数 pass={n_pass} fail={n_fail} skipped={n_skip} "
        f"（判据要求恰 `2/0/0` —— 只看退出码的话，**零条 test 被收集**也是 rc=0）"
        f"→ **{verdict}**",
        f"- 生产文件 sha256 跑前跑后：`{sha_before[:16]}…` / `{sha_after[:16]}…` → "
        f"{'逐字节相同 ✅' if sha_before == sha_after else '不同 ❌'}",
        "",
        "```",
        proc.stdout.strip()[:4000],
        "```",
    ]
    if proc.stderr.strip():
        body += ["", "stderr:", "```", proc.stderr.strip()[:2000], "```"]
    # 结论段必须跟着实验结果走 (Codex round-1 LOW): 原先无条件写「B 说是对的」，
    # 实验失败时退出码虽然照样报错，单读报告却会得到与结果相反的判断。
    if not ok:
        body += [
            "",
            "## 结论",
            "",
            f"⚠ **实验未成立（rc={proc.returncode}，计数 {n_pass}/{n_fail}/{n_skip}，"
            f"sha {'一致' if sha_before == sha_after else '不一致'}），本节不给判定。**",
            "先看上面的 node 输出定位失败原因，修好再跑；在那之前，",
            "A 说与 B 说孰是孰非**没有**被本实验分出胜负。",
        ]
        (HERE / "prem2-gen-semantics.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        print("\n".join(body))
        return 1

    body += [
        "",
        "## 结论",
        "",
        "**代码（B 说）是对的，`:507` 的注释措辞（A 说）描述的是一个有缺陷的语义。**",
        "把「记录时刻」定在 POST **返回**之后，才能把「POST 处理期间启动的 GET」也算作",
        "「启动于重建完成之前」而挡掉 —— 那正是同毫秒盲区之外的第二类因果错位。注释若被",
        "后人当作规格照着改（把读 `state.pollGen` 提到 `await fetch` 之前），本实验的第一条",
        "断言立刻变红。",
        "",
        "本卡是只读复核卡，**不改** `:507` 注释（改注释不改语义，但仍是对代际锚区域动手，",
        "与硬边界「不改代际语义」的意图相冲突，且 Z1-B/C/D 就要改这个文件）→ 登记为移交项。",
    ]
    (HERE / "prem2-gen-semantics.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    print("\n".join(body))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
