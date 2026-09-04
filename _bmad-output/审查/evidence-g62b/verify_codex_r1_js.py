"""CARD-CX-G6-2b-R1 · Codex HIGH-1「反馈归属」的独立复现（完成条件 g）。

报告称：`inflight` 在 POST 完成后即清除，所以同一个库可以连点两次刷新；
第一次重建成功挂下的 pending，会在**第二次刷新失败之后**由那轮补发的 GET 结算，
把第二次的失败反馈覆盖成第一次的「数字已更新」。

时序（全部由测试驱动，沙箱的 setTimeout 只记录不执行，所以没有 sleep 竞态）：

    GET1(gen=1) 完成
    → 点刷新①：POST1 返回 rebuilt → pendingSync{gen:1} → 补发 GET2(gen=2)，挂起
    → 点刷新②：POST2 返回 HTTP 503 → 卡片显示「刷新失败」
    → GET2 返回成功 → startGen=2 > n.gen=1 → 判据放行 → 结算成「数字已更新」
      ⇒ 第二次操作的失败反馈**消失**

判据行 `:402` 在这里**没有做错任何事**：GET2 确实启动于第一次重建完成之后，
代际比较完全合法。缺的是另一个维度——**这条 pending 还该不该代表用户「当前」那次操作**。
所以这是漏掉的第四个前提（反馈归属），不是代际锚的缺陷。

跑法（从 backend/ 起）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g62b/verify_codex_r1_js.py

不落盘生产文件；TestClient 裸构造（不带 with）→ 不起 lifespan、不连 7691。
"""

from __future__ import annotations

import hashlib
import re
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

const OK = {vaults: [{vault_id: "cs_61b", status: "ok", error: null,
  projection: {due_count: 3, due_new_count: 0, placeholder_backlog: 0, bucket_counts: null,
    generated_at: "g", next_upcoming: null, boards: []}}]};

test("HIGH-1: 第一次重建的 pending 覆盖掉第二次刷新的失败反馈", async () => {
  const gets = [];
  let postCount = 0;
  const b = boot({
    getJson: () => {
      let r;
      const p = new Promise(x => { r = x; });
      gets.push({resolve: r});
      return {ok: true, status: 200, json: () => p};
    },
    postJson: () => {
      postCount += 1;
      if (postCount === 1) {
        return {ok: true, status: 200,
          json: async () => ({rebuilt: true, reason: "rebuilt", rebuild_count: 5})};
      }
      return {ok: false, status: 503, json: async () => ({detail: "后端不可用"})};
    },
    hidden: false,
  });
  const btn = mkNode("btn"); btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note"); note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  const click = () => b.handlers["cards::click"](
    {target: {closest: sel => (matches(btn, sel) ? btn : null)}});

  // ① GET1(gen=1) 完成
  assert.equal(b.calls.get, 1, "前提: 启动发首轮 GET");
  gets.pop().resolve(OK);
  await flush();

  // ② 点刷新① → POST1 rebuilt → 挂 pending(gen=1) → 补发 GET2(gen=2) 并挂起
  await click();
  await flush();
  assert.equal(b.calls.post, 1);
  assert.equal(b.calls.get, 2, "前提: rebuilt 后补发了一轮 GET(gen=2)");
  const g2 = gets.pop();
  assert.match(note.innerHTML, /正在同步最新数字/, "前提: 第一次刷新挂着 pending");

  // ③ 点刷新② → POST2 返回 503。inflight 已在 POST1 的 finally 里清掉, 所以点得进去。
  await click();
  await flush();
  assert.equal(b.calls.post, 2, "前提: 第二次 POST 发出去了 (inflight 没挡住)");
  assert.match(note.innerHTML, /刷新失败/,
    "前提: 第二次操作的失败反馈此刻是可见的 —— 少了这条断言, 后面的「消失」无从谈起");
  const afterSecondClick = note.innerHTML;

  // ④ GET2 返回成功 → 判据 startGen(2) > n.gen(1) → 结算第一次的 pending
  g2.resolve(OK);
  await flush();

  assert.notEqual(note.innerHTML, afterSecondClick, "GET2 结算确实改写了反馈");
  assert.match(note.innerHTML, /数字已更新/, "被改写成了第一次重建的成功反馈");
  assert.ok(!note.innerHTML.includes("刷新失败"),
    "⇒ HIGH-1 成立: 用户最新一次操作失败了, 页面却显示上一次操作的成功");
  assert.ok(!b.els["cards"].innerHTML.includes("刷新失败"),
    "整块卡片重绘后同样不含第二次的失败");
});

test("对照: 只点一次时结算是正确的 —— 上一条不是「结算整个坏掉」", async () => {
  const gets = [];
  const b = boot({
    getJson: () => {
      let r;
      const p = new Promise(x => { r = x; });
      gets.push({resolve: r});
      return {ok: true, status: 200, json: () => p};
    },
    postJson: () => ({ok: true, status: 200,
      json: async () => ({rebuilt: true, reason: "rebuilt", rebuild_count: 5})}),
    hidden: false,
  });
  const btn = mkNode("btn"); btn._attrs["data-refresh-vault"] = "cs_61b";
  const note = mkNode("note"); note._attrs["data-note-for"] = "cs_61b";
  b.els["cards"]._desc = [btn, note];
  gets.pop().resolve(OK);
  await flush();
  await b.handlers["cards::click"](
    {target: {closest: sel => (matches(btn, sel) ? btn : null)}});
  await flush();
  gets.pop().resolve(OK);
  await flush();
  assert.match(note.innerHTML, /数字已更新/, "单次刷新: 结算成功是正确行为");
});
"""


def _tap(stdout: str, key: str) -> str:
    m = re.search(rf"^[ℹ#]\s*{key}\s+(\d+)\s*$", stdout, flags=re.M)
    return m.group(1) if m else "-1"


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True
    sha_before = hashlib.sha256(PROD_PY.read_bytes()).hexdigest()

    ns: dict = {"__file__": str(TEST_PY), "__name__": "_g62b_verify_js"}
    exec(compile(TEST_PY.read_text(encoding="utf-8"), "<gate:vjs>", "exec"), ns)  # noqa: S102

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
        print("❌ node 不可用 — fail-closed, 不静默 skip", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="g62b_vjs_") as td:
        d = Path(td)
        (d / "page-script.js").write_text(script, encoding="utf-8")
        (d / "boot.mjs").write_text(ns["_BOOT_MJS"], encoding="utf-8")
        (d / "case.test.mjs").write_text(CASE, encoding="utf-8")
        proc = subprocess.run(
            [node, "--test", "case.test.mjs"], cwd=d, capture_output=True, text=True, timeout=120
        )

    sha_after = hashlib.sha256(PROD_PY.read_bytes()).hexdigest()
    n_pass, n_fail, n_skip = (_tap(proc.stdout, k) for k in ("pass", "fail", "skipped"))
    counts_ok = (n_pass, n_fail, n_skip) == ("2", "0", "0")
    ok = proc.returncode == 0 and sha_before == sha_after and counts_ok

    body = [
        "# CARD-CX-G6-2b-R1 · Codex HIGH-1「反馈归属」独立复现（完成条件 g）",
        "",
        "## 报告的主张",
        "",
        "同一个库连点两次刷新时，第一次重建挂下的 pending 会在**第二次刷新失败之后**由那轮",
        "补发的 GET 结算，把第二次的失败反馈覆盖成第一次的「数字已更新」。",
        "",
        "## 复现时序（沙箱 setTimeout 只记录不执行 ⇒ 时序完全由测试驱动，无 sleep 竞态）",
        "",
        "```",
        "GET1(gen=1) 完成",
        "→ 点刷新①：POST1 rebuilt → pendingSync{gen:1} → 补发 GET2(gen=2)，挂起",
        "→ 点刷新②：POST2 → HTTP 503 → 卡片显示「刷新失败」   ← 先断言它此刻可见",
        "→ GET2 返回成功 → startGen(2) > n.gen(1) → 判据放行 → 结算成「数字已更新」",
        "⇒ 第二次操作的失败反馈消失",
        "```",
        "",
        "配一条**对照**：只点一次时结算成功是正确行为 —— 否则「结算把反馈改写了」这条",
        "可能来自「结算整个坏掉」，而不是报告指出的归属问题。",
        "",
        "## 结果",
        "",
        f"- node 退出码 `{proc.returncode}`，TAP 计数 pass={n_pass} fail={n_fail} skipped={n_skip}"
        f"（判据要求恰 `2/0/0`——只看退出码的话零收集也是 rc=0）",
        f"- 生产文件 sha256 跑前跑后 → {'逐字节相同 ✅' if sha_before == sha_after else '不同 ❌'}",
        f"- **结论：HIGH-1 {'复现成立，予以采信' if ok else '未能复现（详见下方输出）'}**",
        "",
        "```",
        proc.stdout.strip()[:3000],
        "```",
    ]
    if proc.stderr.strip():
        body += ["", "stderr:", "```", proc.stderr.strip()[:1500], "```"]
    body += [
        "",
        "## 判据行 `:402` 有没有做错",
        "",
        "**没有。** GET2 确实启动于第一次重建完成之后，代际比较 `startGen(2) > n.gen(1)` 完全合法。",
        "缺的是另一个维度：**这条 pending 还该不该代表用户「当前」那次操作**。",
        "所以这是本卡 (a) 三前提之外**漏掉的第四个前提（反馈归属）**，",
        "不是代际锚的缺陷，也不需要改回时间戳或引入第二套锚 —— 与本卡硬边界不冲突。",
        "",
        "修复方向（交后续卡）：同库新一次刷新开始时，让被取代的 pending 失去改写当前反馈的权利",
        "（例如按 vault 记一个「反馈世代」，或在 `onRefreshClick` 入口作废旧 pending）。",
    ]
    (HERE / "codex-verify-r1-js.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    print("\n".join(body))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
