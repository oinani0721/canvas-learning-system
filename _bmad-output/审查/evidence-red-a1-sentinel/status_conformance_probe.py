"""CARD-RED-A1-sentinel — /system/* 的 status_code_conformance 定向探针（带负控）。

为什么需要它（⛔ 这一段是本探针存在的全部理由，删掉它就没人知道门是瞎的）
------------------------------------------------------------------------
卡文 (c) 要求用 ``tests/contract/test_openapi_contract.py`` 做 before/after 对照，
证明「router 级依赖一挂，/system/* 不会返回 schema 里没声明的 403」。

实测（``contract-sys-before-20260909T165510.txt``）：改动**之前**那 4 个 operation
就已经全红，而拒因是 ``hypothesis.errors.DeadlineExceeded``（18-19s vs 10s 上限），
``status_code_conformance`` 在整份存档里出现 **0 次**——W4 端口门让每次真实请求变慢，
用例还没走到 schema 校验就先超时了。

⇒ **那道门对本卡要验的性质是瞎的**：它红在别的原因上，before/after 都红，
差集为空也**证明不了**没有引入未声明的状态码。本探针补的正是这一格。

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
    neg_ok = mutated_total > 0 and not still_pass
    print(f"  => 负控 {'成立（探针确实在读 403 声明）' if neg_ok else '不成立 —— 正判作废'}\n")

    verdict = (not bad) and neg_ok
    print(f"VERDICT={'PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
