"""CARD-RED-A1-sentinel — /system/* 的 status_code_conformance 定向探针（带负控）。

为什么需要它（⛔ 这一段是本探针存在的全部理由，删掉它就没人知道门是瞎的）
------------------------------------------------------------------------
卡文 (c) 要求用 ``tests/contract/test_openapi_contract.py`` 做 before/after 对照，
证明「router 级依赖一挂，/system/* 不会返回 schema 里没声明的 403」。

实测（``contract-sys-before-20260909T165510.txt``）：改动**之前**那 4 个 operation
就已经全红，而拒因是 ``hypothesis.errors.DeadlineExceeded``（18-19s vs 10s 上限），
``status_code_conformance`` 在整份存档里出现 **0 次**。

⚠️ **不要把这读成「用例还没走到 schema 校验就先超时了」**（本文件初版如此写过，
Codex round-1 LOW 打回）：Hypothesis 是**先执行测试函数体、再判耗时**并抛
``DeadlineExceeded``（``hypothesis/core.py:1016`` 执行、``:1041`` 判定），所以那些
检查很可能**已经跑过**；日志里没出现检查名只能说明**它们没有报告失败**，不能证明
它们没执行。可以确证的只有：**这 4 个 operation 的最终判定被 DeadlineExceeded 占据，
存档里没有任何 status_code_conformance 结论**。

⇒ 因此 before/after 差集为空**证明不了**没有引入未声明的状态码——那道门在这条性质上
没有给出结论。本探针补的正是这一格。

本探针证明什么
--------------
对当前树上 ``app.openapi()`` 里每一个 ``/api/v1/system/*`` operation：
**不带 key** 发一次请求，观察实际返回码，断言该码在该 operation 的 ``responses`` 里有声明。
（这正是 schemathesis ``status_code_conformance`` 的语义，只把面收窄到本卡改到的 /system/*。）

本探针不证明什么
----------------
- 不覆盖 /system/* 以外的 190 个 operation（本卡未证明，见验收单 §5.8）。
- 不做 schema/content-type/headers 三项一致性（只做 status code 这一项）。
- 不发**带正确 key** 的请求 ⇒ ⛔ 不触发任何端点函数体 ⇒ 不会去连 7691。
  这是刻意的：本卡的硬边界之一就是禁连现网 Neo4j。

负控（⛔ 没有它，PASS 只说明「探针跑完了」，不说明「探针看得见缺陷」）
-------------------------------------------------------------------
第二遍用**同一套观测到的状态码**，但把 spec 副本里每个 /system/* operation 的
``403`` 声明摘掉，再判一次。它**必须全部 FAIL**——若仍 PASS，说明本探针根本没在读声明，
判据不成立，PASS 一律作废。

⚠️ **本文件初版曾声称「真实声明变异必然要执行端点函数体、会去连 7691，所以做不了」
——那句不成立**（Codex round-1 LOW 打回）。于是本版**补了第二道负控**：保留鉴权依赖
不动，只在内存里的 ``app.routes`` 对象上删掉 403 声明并清掉 ``app.openapi_schema``
缓存，然后**原样重跑一遍真实观测**。它同样必须全部 FAIL，且全程不连数据库。

两道负控的力度不同，都保留：
  · 负控 A（spec 副本变异）—— 证明判定函数会读 403 声明；
  · 负控 B（路由对象变异 + 重新观测）—— 证明**在一棵真的缺声明的应用上**，
    这套探针会红。B 强于 A；A 保留是因为它不改任何进程状态。

⛔ **还原自证不能只问「有没有未声明码」**（Codex round-2 LOW，已用受控反例复现）：
在还原后把 ``/system/*`` 的 paths 全删掉，观测结果为**空**，「没有未声明码」照样成立，
`VERDICT` 会误判 PASS。所以本版把还原自证改成**逐条比对完整指纹**
``(method, path) → (实际状态码, 声明集合)``，并要求非空；负控 B 也从「条数相同」
收紧为「**键集与正判逐条相同**」——数量相同挡不住换人。

用法: cd backend && .venv/bin/python ../_bmad-output/审查/evidence-red-a1-sentinel/status_conformance_probe.py
"""

from __future__ import annotations

import copy
import sys

sys.path.insert(0, ".")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from tests.support.authed_client import authed_settings_override  # noqa: E402
from tests.support.lifespan import no_lifespan  # noqa: E402
from app.config import get_settings  # noqa: E402

SYSTEM_PREFIX = "/api/v1/system/"
_HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def _declared(responses: dict, status: int) -> bool:
    """状态码是否在该 operation 的 responses 里有声明（含 4XX 这类区间键）。"""
    if str(status) in responses:
        return True
    return f"{status // 100}XX" in responses


def _observe() -> list[tuple[str, str, int, dict]]:
    """对每个 /system/* operation 发一次**不带 key** 的请求，收集 (method, path, status, responses)。"""
    spec = app.openapi()
    rows: list[tuple[str, str, int, dict]] = []

    previous = app.dependency_overrides.get(get_settings)
    app.dependency_overrides[get_settings] = authed_settings_override
    try:
        with no_lifespan(app), TestClient(app, raise_server_exceptions=False) as client:
            for path, item in sorted(spec["paths"].items()):
                if not path.startswith(SYSTEM_PREFIX):
                    continue
                for method in _HTTP_METHODS:
                    op = item.get(method)
                    if not isinstance(op, dict):
                        continue
                    # 路径参数用一个固定占位值填掉，只为让路由匹配得上；
                    # 不带 key ⇒ 鉴权在端点函数体之前就拒，占位值永远到不了业务逻辑。
                    url = path.replace("{record_id}", "probe-placeholder")
                    resp = client.request(method.upper(), url, json={})
                    rows.append((method.upper(), path, resp.status_code, op.get("responses", {})))
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_settings, None)
        else:
            app.dependency_overrides[get_settings] = previous
    return rows


def _mutate_routes_drop_403():
    """负控 B: 在真实 ``app.routes`` 上删掉 /system/* 的 403 声明, 返回还原用的快照。

    ⛔ 不动鉴权依赖 —— 所以端点函数体依旧一次都不执行, 不会去连 7691。
    """
    saved: list[tuple[object, dict]] = []
    for route in app.routes:
        path = getattr(route, "path", "")
        responses = getattr(route, "responses", None)
        if not path.startswith(SYSTEM_PREFIX) or not isinstance(responses, dict):
            continue
        if 403 in responses or "403" in responses:
            saved.append((route, dict(responses)))
            responses.pop(403, None)
            responses.pop("403", None)
    app.openapi_schema = None  # 逼 FastAPI 重新生成 spec
    return saved


def _restore_routes(saved) -> None:
    for route, original in saved:
        route.responses.clear()
        route.responses.update(original)
    app.openapi_schema = None


def main() -> int:
    rows = _observe()
    if not rows:
        print("PROBE ABORT: 一个 /system/* operation 都没找到 —— 判据面为空，不算通过。")
        return 2

    print(f"# 观测到 {len(rows)} 个 /api/v1/system/* operation（不带 key 各发一次请求）\n")

    print("## 正判：实际返回码必须在该 operation 的 responses 里有声明")
    bad = []
    for method, path, status, responses in rows:
        ok = _declared(responses, status)
        print(f"  {'PASS' if ok else 'FAIL'}  {method:6} {path:52} -> {status}  declared={sorted(responses)}")
        if not ok:
            bad.append((method, path, status))
    print(f"  => 正判 {'PASS' if not bad else 'FAIL'}：未声明的返回码 {len(bad)} 个 {bad}\n")

    print("## 负控：把 spec 副本里每个 /system/* operation 的 403 声明摘掉，同一批观测必须全部 FAIL")
    still_pass = []
    mutated_total = 0
    for method, path, status, responses in rows:
        mutated = copy.deepcopy(responses)
        removed = mutated.pop("403", None)
        if removed is None:
            print(f"  SKIP  {method:6} {path:52} 该 operation 本来就没声明 403，无可摘")
            continue
        mutated_total += 1
        if _declared(mutated, status):
            still_pass.append((method, path, status))
    print(f"  => 摘掉 403 的 operation {mutated_total} 个；其中仍判 PASS 的 {len(still_pass)} 个 {still_pass}")
    neg_a_ok = mutated_total > 0 and not still_pass
    print(f"  => 负控 A {'成立（判定函数确实在读 403 声明）' if neg_a_ok else '不成立 —— 正判作废'}\n")

    # ⛔ 键集必须逐条绑住, 不能只比条数 (Codex round-2 LOW: 「数量相同」挡不住换人)。
    baseline_keys = {(m, p) for m, p, _, _ in rows}
    baseline_fingerprint = {(m, p): (s, tuple(sorted(r))) for m, p, s, r in rows}

    print("## 负控 B（更强）：在真实 app.routes 上删掉 403 声明 + 清 schema 缓存，**原样重跑观测**")
    saved = _mutate_routes_drop_403()
    try:
        mutated_rows = _observe()
        b_bad = [(m, p, s) for m, p, s, r in mutated_rows if not _declared(r, s)]
        b_declared_still = [(m, p, s) for m, p, s, r in mutated_rows if _declared(r, s)]
        mutated_keys = {(m, p) for m, p, _, _ in mutated_rows}
        print(f"  变异后观测到 {len(mutated_rows)} 个 operation；其中判 FAIL（未声明）{len(b_bad)} 个")
        print(f"  仍判 PASS 的 {len(b_declared_still)} 个 {b_declared_still}")
        print(f"  键集与正判**逐条相同** = {mutated_keys == baseline_keys}")
        neg_b_ok = bool(mutated_keys) and mutated_keys == baseline_keys and not b_declared_still
    finally:
        _restore_routes(saved)
    print(f"  => 负控 B {'成立（真的缺声明时这套探针会红）' if neg_b_ok else '不成立 —— 正判作废'}")

    # ⛔ 还原自证不能只问「有没有未声明码」——空观测同样满足那个条件, 会把
    #    「路由被删光了」误判成 PASS (Codex round-2 LOW, 已用受控反例复现)。
    #    改为逐条比对 (method, path) → (实际状态码, 声明集合) 的**完整指纹**。
    restored = _observe()
    restored_fingerprint = {(m, p): (s, tuple(sorted(r))) for m, p, s, r in restored}
    restored_ok = bool(restored_fingerprint) and restored_fingerprint == baseline_fingerprint
    missing = sorted(baseline_fingerprint.keys() - restored_fingerprint.keys())
    changed = sorted(
        k for k in baseline_fingerprint.keys() & restored_fingerprint.keys()
        if baseline_fingerprint[k] != restored_fingerprint[k]
    )
    print(f"  => 还原自证：观测到 {len(restored)} 个 operation（正判时 {len(rows)} 个）")
    print(f"     缺失 {len(missing)} 个 {missing}；指纹变化 {len(changed)} 个 {changed}")
    print(f"     指纹逐条相同 = {restored_ok}\n")

    verdict = (not bad) and neg_a_ok and neg_b_ok and restored_ok
    print(f"VERDICT={'PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
