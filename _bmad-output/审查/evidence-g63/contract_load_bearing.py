"""CARD-G6-3 · (b) 四条轮询契约断言的**承重验证**。

「加了四条断言」不等于「这四条断言拦得住东西」。本脚本逐条把被测的那个契约
在**内存里的 JS 副本**上打坏，再跑同一份测试代码：只有对应那条断言变红、
其余仍绿，才算它独家承重。

不碰磁盘上的产品代码：从真实响应里取出 `<script>` 原文，字符串替换后写进
tmp 的 `page-script.js`，沙箱 `boot.mjs` 加载的是那份副本。
跑完对 `review_app.py` 做 sha256 前后比对自证。

跑法（从 backend/ 起）:
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \\
      .venv/bin/python ../_bmad-output/审查/evidence-g63/contract_load_bearing.py
"""

from __future__ import annotations

import hashlib
import os
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

#: 变异名 → (JS 原文, 替换成, 预期变红的断言序号, 说明)
#: 序号对应测试里的 ①②③④。
MUTATIONS: list[tuple[str, str, str, int, str]] = [
    ("M1-下限失效", "const POLL_MIN_MS = 5000;", "const POLL_MIN_MS = 1000;", 1,
     "把 clamp 下限从 5s 调到 1s：2 秒后到期的卡会排 2000ms，打后端的频率翻数倍"),
    ("M2-上限失效", "const POLL_MAX_MS = 60000;", "const POLL_MAX_MS = 600000;", 2,
     "把 clamp 上限从 60s 放到 600s：无近期到期时十分钟才问一次，页面等于睡死"),
    ("M3-回前台不拉", "  if (act.pollNow) poll();", "  if (false) poll();", 3,
     "visibilityAction 仍返回 pollNow:true，但接线端不再调 poll —— 纯函数测试看不见这种坏法"),
    # ⚠ 初版这条写成 `await fetch(GET) || await fetch(POST)` —— `fetch` 返回的对象
    # 恒为 truthy，`||` 短路让 POST **永不执行**，于是「四条全绿」被误读成
    # 「第 ④ 条不承重」。变异必须真的把被测行为打坏，否则量的是变异自己写错了。
    ("M4-轮询发POST", 'const resp = await fetch(URLS.overview, {cache: "no-store"});',
     'await fetch(URLS.refresh, {method: "POST"});\n'
     '    const resp = await fetch(URLS.overview, {cache: "no-store"});', 4,
     "在轮询路径上**无条件**先发一次 POST refresh —— 正是默认裁决② 禁止的行为。"
     "既有那道门数的是源码里 `method: \"POST\"` 出现几次（静态文本）；本条验证的是"
     "运行时行为门（沙箱实际收到的 POST 计数）同样抓得到"),
]

TEST_NAME = "test_js_poll_contract_wiring_g63"


def _extract_case_src(test_src: str) -> str:
    """从测试文件里取出该门喂给 node 的 JS（_BOOT_PRELUDE + 那段 r-string）。"""
    m = re.search(
        rf"def {TEST_NAME}\(node_harness\):.*?_BOOT_PRELUDE\s*\+\s*r\"\"\"(.*?)\"\"\",\s*\n\s*\)",
        test_src, re.S,
    )
    assert m, "取不到该门的 JS 片段 —— 测试结构变了, 本脚本需同步更新"
    return m.group(1)


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    sys.dont_write_bytecode = True
    sha_before = hashlib.sha256(PROD_PY.read_bytes()).hexdigest()

    ns: dict = {"__file__": str(TEST_PY), "__name__": "_g63_lb"}
    test_src = TEST_PY.read_text(encoding="utf-8")
    exec(compile(test_src, "<g63lb>", "exec"), ns)  # noqa: S102

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app, base_url="http://127.0.0.1:8011")
    try:
        resp = client.get(ns["APP_PATH"])
        assert resp.status_code == 200
        real_js = ns["_extract_script"](resp.text)
    finally:
        client.close()

    node = ns["_NODE"]
    if not node:
        print("❌ node 不可用 — fail-closed", file=sys.stderr)
        return 1

    case_js = ns["_BOOT_PRELUDE"] + _extract_case_src(test_src)

    def run(js: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory(prefix="g63_lb_") as td:
            d = Path(td)
            (d / "page-script.js").write_text(js, encoding="utf-8")
            (d / "boot.mjs").write_text(ns["_BOOT_MJS"], encoding="utf-8")
            (d / "case.test.mjs").write_text(case_js, encoding="utf-8")
            p = subprocess.run([node, "--test", "case.test.mjs"], cwd=d,
                               capture_output=True, text=True, timeout=120)
            return p.returncode, p.stdout

    def failed_ids(out: str) -> set[int]:
        """哪几条断言红了 —— 认测试名开头的 ①②③④ 记号。"""
        marks = {"①": 1, "②": 2, "③": 3, "④": 4}
        got = set()
        for line in out.splitlines():
            if line.strip().startswith("✖"):
                for ch, n in marks.items():
                    if ch in line:
                        got.add(n)
        return got

    bad: list[str] = []
    # 验伪锚: 未变异的真实 JS 必须四条全绿。少了它，「变异后变红」可由一个恒红的门平凡满足。
    rc0, out0 = run(real_js)
    if rc0 != 0 or failed_ids(out0):
        bad.append(f"验伪锚失败: 未变异的真实 JS 就有断言红 (rc={rc0}, 红={sorted(failed_ids(out0))})")

    rows = []
    for name, old, new, expect_id, note in MUTATIONS:
        if real_js.count(old) != 1:
            bad.append(f"{name}: 变异锚点在真实 JS 里命中 {real_js.count(old)} 次 (须恰 1) — 定位失败")
            rows.append((name, expect_id, "定位失败", note))
            continue
        rc, out = run(real_js.replace(old, new, 1))
        got = failed_ids(out)
        rows.append((name, expect_id, f"rc={rc}, 红={sorted(got) or '无'}", note))
        if rc == 0:
            bad.append(f"{name}: 打坏了契约, 四条断言却全绿 — 这条断言不承重")
        elif expect_id not in got:
            bad.append(f"{name}: 变红的不是第 {expect_id} 条 (实红 {sorted(got)}) — 抓到它的是别的断言")

    sha_after = hashlib.sha256(PROD_PY.read_bytes()).hexdigest()
    if sha_before != sha_after:
        bad.append("落盘自证失败: review_app.py 的 sha 变了")

    L = [
        "# CARD-G6-3 · (b) 四条轮询契约断言的承重验证",
        "",
        "> 「加了四条断言」≠「这四条拦得住东西」。逐条把被测契约在**内存里的 JS 副本**上打坏，",
        "> 再跑同一份测试：只有对应那条变红、且**红的就是它**，才算独家承重。",
        "> 磁盘上的 `review_app.py` 一个字节没碰（下方 sha 自证）。",
        "",
        f"验伪锚（未变异的真实 JS）：{'✅ 四条全绿' if rc0 == 0 and not failed_ids(out0) else '❌ 见自检'}",
        f"`review_app.py` sha256 跑前跑后：{'逐字节相同 ✅' if sha_before == sha_after else '不同 ❌'}",
        "",
        "| 变异 | 应变红 | 实测 | 说明 |",
        "|---|---|---|---|",
    ]
    for name, eid, got, note in rows:
        L.append(f"| `{name}` | 第 {eid} 条 | {got} | {note} |")
    L += ["", "## 自检", ""]
    L += [f"- ❌ {b}" for b in bad] or [
        "- ✅ 四条变异各自打红了**对应**的那条断言，无一条靠别的断言兜住；验伪锚成立"
    ]
    (HERE / "contract-load-bearing.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
