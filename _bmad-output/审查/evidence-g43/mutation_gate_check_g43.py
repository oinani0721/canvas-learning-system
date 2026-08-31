#!/usr/bin/env python
"""CARD-G4-3 变异门验证 — 证明四态门是承重的, 不是摆设。

用法 (必须从 backend/ 跑):
    cd backend && .venv/bin/python \
        ../_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py

设计约束 (踩过的坑, 逐条对应):

1. **严格串行**。变异是原地改被测源文件, 并发跑会让 B 的还原把 A 的变异写回,
   而测试照样全绿 —— 假绿。本脚本一次只施加一个变异。
2. **finally 无条件还原 + `cmp` 级逐字校验**。中途断言失败不能留下半截变异,
   否则后续所有结论都建立在污染的工作树上。还原后逐字节比对备份, 不相同即
   非零退出。
3. **锚点命中必须先断言**。`str.replace` 不命中不报错 —— 变异"没打上"和
   "打上了但门抓不住"在结果上同形 (都是全绿), 会被误读成"门是死的"。
4. **期望值是"必须变红"**。这是本脚本存在的全部意义: 一个变异若全绿, 说明
   对应的门根本不承重 —— 那才是要修的东西 (M2 首跑正是如此)。
"""

from __future__ import annotations

import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple

BACKEND = Path.cwd()
if not (BACKEND / "app" / "api" / "v1" / "endpoints" / "memory.py").exists():
    sys.exit("必须从 backend/ 目录运行 (cwd 里找不到 app/api/v1/endpoints/memory.py)")

PYTEST: List[str] = [
    ".venv/bin/pytest",
    "tests/api",
    "-q",
    "-k",
    "memory or rag",
    "-p",
    "no:cacheprovider",
    "--override-ini=addopts=",
]

MEMORY_EP = "app/api/v1/endpoints/memory.py"
RAG_EP = "app/api/v1/endpoints/rag.py"
SCHEMAS = "app/models/memory_schemas.py"
TRACKER = "app/core/decision_tracker.py"

#: (变异名, 说明, [(文件, 原串, 新串), ...])
#: (变异名, 说明, [(文件, 原串, 新串), ...], 预期该变红的 nodeid 片段)
MUTATIONS: List[Tuple[str, str, List[Tuple[str, str, str]], List[str]]] = [
    (
        "M1",
        "四态字段从可选改必填 —— 破坏加性",
        [
            (
                SCHEMAS,
                '    retrieval_status: Optional[ServiceStatus] = Field(\n        None,\n        description=(\n            "检索四态 (G4-2 统一枚举): ok=有结果 / empty=真空 / "',
                '    retrieval_status: ServiceStatus = Field(\n        ...,\n        description=(\n            "检索四态 (G4-2 统一枚举): ok=有结果 / empty=真空 / "',
            )
        ],
        [
            "TestMemorySchemaRequiredSetsFrozen::test_required_set_unchanged[LearningHistoryResponse]",
            "TestMemorySchemaRequiredSetsFrozen::test_new_status_fields_are_optional_everywhere",
        ],
    ),
    (
        "M2",
        "trace 去掉枚举归一 —— 会写出 'ServiceStatus.DEGRADED'",
        [(TRACKER, "        output=normalized,", "        output=status,")],
        [
            "TestMemoryTraceEnumNormalization::test_enum_valued_status_normalizes_in_trace_and_body",
        ],
    ),
    (
        "M3",
        "端点在状态缺失时自作主张补 'empty' —— 发明状态",
        [
            (
                MEMORY_EP,
                '        retrieval_status = result.get("retrieval_status")',
                '        retrieval_status = result.get("retrieval_status") or "empty"',
            ),
            (
                RAG_EP,
                '        retrieval_status = result.get("retrieval_status")',
                '        retrieval_status = result.get("retrieval_status") or "empty"',
            ),
        ],
        [
            "TestEpisodesFourState::test_absent_service_keys_yield_null_not_invented_status",
            "TestRagQueryFourStatePassthrough::test_missing_status_stays_null_not_invented",
        ],
    ),
    (
        "M4",
        "/review-suggestions 信封回退成裸 list",
        [
            (
                MEMORY_EP,
                "    response_model=ReviewSuggestionsResponse,",
                "    response_model=List[ReviewSuggestionResponse],",
            ),
            (
                MEMORY_EP,
                "        return ReviewSuggestionsResponse(\n            items=[",
                "        return [",
            ),
            (
                MEMORY_EP,
                "                for s in result.items\n            ],\n"
                "            retrieval_status=result.status,\n"
                "            retrieval_status_reason=result.reason,\n        )",
                "                for s in result.items\n            ]",
            ),
            (
                MEMORY_EP,
                ") -> ReviewSuggestionsResponse:",
                ") -> List[ReviewSuggestionResponse]:",
            ),
        ],
        [
            "TestReviewSuggestionsEnvelope::test_envelope_carries_status[<lambda>-ok-None]",
            "TestMemoryAdditiveContract::test_review_suggestions_envelope_is_declared_breaking_not_additive",
        ],
    ),
    (
        "M6",
        "端点用 .get(k, 'low') 而非 `or 'low'` —— 真实 fallback 的 None 撞响应模型 (Codex BLOCKER-1)",
        [
            (
                RAG_EP,
                'quality_grade=result.get("quality_grade") or "low",',
                'quality_grade=result.get("quality_grade", "low"),',
            )
        ],
        [
            "TestRagRealFallbackEntrypoint::test_real_ainvoke_none_fallback_returns_200_unavailable",
            "TestRagProductionStateShapesAllReturn200::test_create_initial_state_shape_returns_200",
        ],
    ),
    (
        "M7",
        "trace 落账去掉 fail-open —— 观测面异常升成业务 500 (Codex HIGH-1)",
        [
            (
                TRACKER,
                "    try:\n        return log_decision(\n"
                "            function=function,\n"
                "            input_summary=input_summary,\n"
                "            output=normalized,\n"
                '            reason=reason or f"retrieval_status={normalized} reported without reason",\n'
                "        )",
                "    if True:\n        return log_decision(\n"
                "            function=function,\n"
                "            input_summary=input_summary,\n"
                "            output=normalized,\n"
                '            reason=reason or f"retrieval_status={normalized} reported without reason",\n'
                "        )",
            ),
            # 同批删掉配套的 except 块, 否则是**语法错误**而非行为变异 ——
            # 语法错误会让 pytest collection error, rc!=0, 被弱 runner 误判成
            # "门抓住了" (Codex round-2 MEDIUM-1 实证: 旧 M7 正是这种假杀)。
            (
                TRACKER,
                "    except Exception:  # noqa: BLE001 — 观测面刻意兜底, 见上\n"
                "        try:\n"
                "            logger.exception(\n"
                '                "retrieval status decision logging failed (fail-open); "\n'
                '                "function=%s status=%s",\n'
                "                function,\n"
                "                normalized,\n"
                "            )\n"
                "        except Exception:  # noqa: BLE001\n"
                "            # 兜底的兜底: 若 logging 后端本身就是坏的, 上面这行同样会抛。\n"
                "            # 观测彻底失效仍不得波及业务响应 —— 这是本函数的唯一硬要求。\n"
                "            pass\n"
                "        return None\n",
                "",
            ),
        ],
        [
            "TestMemoryTraceFailOpen::test_trace_sink_failure_does_not_break_response[/api/v1/memory/episodes?user_id=u-get_learning_history-<lambda>-unavailable-neo4j down]",
            "TestRagTraceFailOpen::test_trace_sink_failure_does_not_break_the_response",
        ],
    ),
    (
        "M8",
        "只删 fail-open 的**二级**兜底 (logger.exception 自身抛错时的保护)",
        [
            (
                TRACKER,
                "        try:\n"
                "            logger.exception(\n"
                '                "retrieval status decision logging failed (fail-open); "\n'
                '                "function=%s status=%s",\n'
                "                function,\n"
                "                normalized,\n"
                "            )\n"
                "        except Exception:  # noqa: BLE001\n"
                "            # 兜底的兜底: 若 logging 后端本身就是坏的, 上面这行同样会抛。\n"
                "            # 观测彻底失效仍不得波及业务响应 —— 这是本函数的唯一硬要求。\n"
                "            pass\n",
                "        logger.exception(\n"
                '            "retrieval status decision logging failed (fail-open); "\n'
                '            "function=%s status=%s",\n'
                "            function,\n"
                "            normalized,\n"
                "        )\n",
            )
        ],
        [
            "TestMemoryTraceFailOpen::test_both_sink_and_fallback_logger_failing_still_returns_200[/api/v1/memory/episodes?user_id=u-get_learning_history-<lambda>-unavailable-neo4j down]",
        ],
    ),
    (
        "M9",
        "helper 提前 return, 根本不落账 (门若只断言 200 就抓不住这种退化)",
        [
            (
                TRACKER,
                "    if status is None:\n        return None\n",
                "    if status is None or True:\n        return None\n",
            )
        ],
        [
            "TestMemoryTraceFailOpen::test_trace_sink_failure_does_not_break_response[/api/v1/memory/episodes?user_id=u-get_learning_history-<lambda>-unavailable-neo4j down]",
            "TestMemoryTraceAlignment::test_degraded_logs_decision_with_enum_value",
        ],
    ),
    (
        "M10",
        "把 EMPTY 加进落账集合 —— round-3 实证的**真存活**变异 (正常流量污染决策日志)",
        [
            (
                TRACKER,
                "frozenset({ServiceStatus.DEGRADED.value, ServiceStatus.UNAVAILABLE.value})",
                "frozenset({ServiceStatus.EMPTY.value, ServiceStatus.DEGRADED.value, ServiceStatus.UNAVAILABLE.value})",
            )
        ],
        [
            # 精确到 **[empty]** 参数实例: 该变异真正应当杀死的是 empty 那条,
            # 只有 [ok] 失败说明红的原因不对 (Codex round-4 MEDIUM-1)。
            "TestMemoryTraceAlignment::test_healthy_states_do_not_spam_trace[empty]",
            "TestRagTraceAlignment::test_healthy_states_do_not_log_decision[empty]",
        ],
    ),
    (
        "M11",
        "信封的 items 键改名 —— 条目载荷契约被破坏",
        [
            (
                SCHEMAS,
                "    items: List[ReviewSuggestionResponse] = Field(",
                "    entries: List[ReviewSuggestionResponse] = Field(",
            ),
            (
                MEMORY_EP,
                "        return ReviewSuggestionsResponse(\n            items=[",
                "        return ReviewSuggestionsResponse(\n            entries=[",
            ),
        ],
        [
            "TestReviewSuggestionsEnvelope::test_items_payload_shape_unchanged",
        ],
    ),
    (
        "M12",
        "retrieval_status 字段类型从枚举退回裸 str —— OpenAPI 值域约束消失",
        [
            (
                SCHEMAS,
                '    retrieval_status: Optional[ServiceStatus] = Field(\n        None,\n        description=(\n            "检索四态 (G4-2 统一枚举): ok=有结果 / empty=真空 / "',
                '    retrieval_status: Optional[str] = Field(\n        None,\n        description=(\n            "检索四态 (G4-2 统一枚举): ok=有结果 / empty=真空 / "',
            )
        ],
        [
            "TestMemorySchemaRequiredSetsFrozen::test_status_field_value_domain_is_the_unified_enum[LearningHistoryResponse]",
        ],
    ),
    (
        "M12a",
        "ConceptHistoryResponse 的 retrieval_status 退回裸 str (round-4 实证的同型真存活变异)",
        [
            (
                SCHEMAS,
                "    # ── CARD-G4-3 加性四态字段 ────────────────────────────────────────\n"
                '    # 本端点是四态最"值钱"的地方: 空 timeline 此前既可能是「这个概念真没学\n'
                "    # 过」也可能是「Neo4j 挂了」, 两者在 HTTP 面上完全同形。\n"
                "    retrieval_status: Optional[ServiceStatus] = Field(",
                "    # ── CARD-G4-3 加性四态字段 ────────────────────────────────────────\n"
                '    # 本端点是四态最"值钱"的地方: 空 timeline 此前既可能是「这个概念真没学\n'
                "    # 过」也可能是「Neo4j 挂了」, 两者在 HTTP 面上完全同形。\n"
                "    retrieval_status: Optional[str] = Field(",
            )
        ],
        [
            "TestMemorySchemaRequiredSetsFrozen::test_status_field_value_domain_is_the_unified_enum[ConceptHistoryResponse]",
        ],
    ),
    (
        "M12b",
        "ReviewSuggestionsResponse 的 retrieval_status 退回裸 str (同上)",
        [
            (
                SCHEMAS,
                "    retrieval_status: Optional[ServiceStatus] = Field(\n"
                "        None,\n"
                "        description=(\n"
                '            "检索四态 (G4-2 统一枚举)。unavailable 时 items 恒空且**不可信** —— "',
                "    retrieval_status: Optional[str] = Field(\n"
                "        None,\n"
                "        description=(\n"
                '            "检索四态 (G4-2 统一枚举)。unavailable 时 items 恒空且**不可信** —— "',
            )
        ],
        [
            "TestMemorySchemaRequiredSetsFrozen::test_status_field_value_domain_is_the_unified_enum[ReviewSuggestionsResponse]",
        ],
    ),
    (
        "M5",
        "unavailable 升成 503 —— 破坏「200 语义不变」",
        [
            (
                MEMORY_EP,
                "        return ReviewSuggestionsResponse(",
                '        if result.status == "unavailable":\n'
                "            raise HTTPException(status_code=503, detail=result.reason)\n"
                "        return ReviewSuggestionsResponse(",
            ),
        ],
        [
            "TestReviewSuggestionsEnvelope::test_unavailable_returns_200_with_empty_items",
        ],
    ),
]


#: 基线收集数 —— 由第一次运行填充, 之后每次变异必须收集到**同样多**的用例。
_BASELINE_COLLECTED: Optional[int] = None


def _collected_count() -> Optional[int]:
    """当前选择集能收集到多少用例 (收集失败或零命中返回 None)。

    ⚠️ **不要**往 PYTEST 后面再追加 ``-q``: PYTEST 里已经有一个, 再加一个就是
    ``-q -q``, pytest 会把收集清单**整个抑制掉**, 于是本函数恒返回 0 ——
    "收集数不变" 就退化成 ``0 == 0`` 的恒真检查, 又是一道死门。
    (2026-08-31 实测: 单 -q → 75 条, 双 -q → 0 条。本脚本上一版正是这么写的,
    第一次跑出来 baseline collected=0 才发现。)

    这就是"每加一道检查, 就新增一条它自己失败时的路径"的活例 —— 新检查装上后
    必须先验伪一次, 不能装上就信。
    """
    args = [a for a in PYTEST if a != "-q"] + ["--collect-only", "-q"]
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    n = sum(1 for ln in proc.stdout.splitlines() if "::" in ln)
    # 0 条 = 选择集没选中任何用例, 与"收集失败"同样不可用作基线
    return n if n > 0 else None


class RunResult(NamedTuple):
    rc: int
    failed: List[str]  # FAILED nodeid 列表
    collected: Optional[int]
    tail: str
    errors: List[str] = []  # ERROR nodeid (fixture/收集期崩溃, 不算 kill)


def run_pytest() -> RunResult:
    proc = subprocess.run(PYTEST, capture_output=True, text=True)
    out = proc.stdout
    # ⚠️ 按 " - " 切, **不能**按空格切: parametrize 的 id 里可以含空格
    # (本卡就有 "…-unavailable-neo4j down]"), 按空格切会把 nodeid 砍成两截,
    # 于是精确匹配恒不成立 —— 预期门明明变红了却判"没变红"。
    # (2026-08-31 实测: M7/M8/M9 三个真杀被此 bug 误判成死门。)
    # pytest -q 的短摘要行形如 "FAILED <nodeid>" 或 "FAILED <nodeid> - <原因>"。
    failed = [
        ln[len("FAILED ") :].split(" - ", 1)[0].rstrip()
        for ln in out.splitlines()
        if ln.startswith("FAILED ")
    ]
    # ERROR 行 = fixture / 收集期崩溃。它也让 rc!=0, 但"环境炸了"不等于
    # "门抓住了缺陷" —— judge_kill 会因此拒绝判杀 (Codex round-4 MEDIUM-1)。
    # ⚠️ 只认 **pytest 的 ERROR 摘要行** (形如 "ERROR path.py::Test::test_x"),
    # 不能只看 startswith("ERROR ") —— 被捕获的**日志输出**也长这样
    # ("ERROR    app.api.v1.endpoints.memory:memory.py:268 Failed to ..."),
    # 那是被测代码正常记录的错误日志, 不是测试崩溃。
    # (2026-08-31 实测: 不加这个判别时, M1/M4/M5/M7/M8 因为被测代码打了一行
    #  ERROR 日志就被判成"环境炸了", 5 个真杀被误判为死门。)
    errors = [
        tok
        for ln in out.splitlines()
        if ln.startswith("ERROR ")
        for tok in [ln[len("ERROR ") :].strip().split(" ")[0]]
        if "::" in tok
    ]
    tail = [
        ln
        for ln in out.splitlines()
        if ln.startswith("FAILED")
        or ln.startswith("ERROR ")
        or " passed" in ln
        or " failed" in ln
    ]
    return RunResult(
        proc.returncode, failed, _collected_count(), "\n".join(tail), errors
    )


def judge_kill(
    baseline_collected: int, r: RunResult, expect: Optional[Sequence[str]] = None
) -> Tuple[bool, str]:
    """判定一个变异是否**真的被对应的门杀死**。

    ⚠️ 这是本脚本最容易自欺的地方, 已经错过两版:

    **第一版** 只看 ``rc != 0`` —— 于是一个把 ``try:`` 换成 ``if True:`` 却留下
    ``except`` 的变异体产生 SyntaxError, pytest 连收集都没完成、一条 FAILED 都
    没有, 却被记成"✓ 被抓住"。**那是把「测试根本没跑起来」当成「测试抓住了缺陷」。**

    **第二版** 加了"收集数不变", 但 ``_collected_count()`` 里多传了一个 ``-q``
    (``PYTEST`` 里本来就有一个), pytest 抑制收集清单 → 恒返回 0 →
    ``0 == 0`` 恒真, 新检查装上就死。

    **第三版**(本版, Codex round-3 MEDIUM-1) 补最后一个洞: 前两版只要求
    "有任意 FAILED", 于是**改一条无关测试的断言**制造红灯也能判 ✓ ——
    红灯与变异之间没有因果绑定。现在每个变异登记它**预期该杀死的门**,
    实际 FAILED 集合必须**覆盖**这批预期 nodeid。

    四条同时成立才算 kill:
    1. **收集成功** —— 变异体语法/导入合法, 测试真跑起来了;
    2. **收集数 == 基线** —— 没因导入错误少收一批;
    3. **rc == 1** —— pytest 的"有测试失败", 而非 2(中断)/3(内部错)/4(用法错);
    4. **实际 FAILED ⊇ 预期 nodeid** —— 红的是**该红的那些门**, 不是随便哪条。
    """
    if r.collected is None:
        return False, "✗ 收集失败 (语法/导入错误) —— 这不是门抓住了, 是测试没跑起来"
    if r.collected != baseline_collected:
        return (
            False,
            f"✗ 收集数变了 {baseline_collected} → {r.collected} —— 变异破坏了收集, 判据不可读",
        )
    if r.rc != 1:
        return False, f"✗ rc={r.rc} 不是 1 —— pytest 不是因为「有测试失败」而退出的"
    if not r.failed:
        return False, "✗ 零 FAILED nodeid —— 没有任何门变红"
    if r.errors:
        return False, (
            f"✗ 有 {len(r.errors)} 条 ERROR (fixture/收集期崩溃) —— "
            "红的原因可能是环境炸了而不是门抓住了缺陷"
        )
    if expect:
        actual = set(r.failed)

        # ⚠️ **精确匹配 nodeid 后缀**, 不用子串包含 (Codex round-4 MEDIUM-1):
        # 子串匹配下, 预期 "…::test_healthy_states_do_not_spam_trace" 会被
        # "…::test_healthy_states_do_not_spam_trace[ok]" 满足 —— 但该变异真正
        # 应当杀死的是 **[empty]** 那个参数实例。于是"只有错误的参数失败"也判 ✓。
        # 现在预期串必须与某条 nodeid 的 "::" 之后部分**完全相等**。
        # 预期串写的是 "Class::test_name[params]" (2 段), 而 pytest 的 nodeid 是
        # "path.py::Class::test_name[params]" (3 段)。**不能**两边各切一次 "::"
        # —— 那会把 actual 切成 "Class::test_name[...]"、expect 切成
        # "test_name[...]", 两边不同形, 于是恒不相等、全判 ✗。
        # (2026-08-31 实测: 14/14 全被误判成死门, 而 FAILED 行与预期逐字一致。)
        # 正确做法: 预期串必须是某条 actual nodeid 的**完整后缀**, 且断点在 "::" 上。
        def _matches(expected: str, nodeid: str) -> bool:
            return nodeid == expected or nodeid.endswith("::" + expected)

        missing = [e for e in expect if not any(_matches(e, a) for a in actual)]
        if missing:
            return False, (
                f"✗ 预期的门没精确变红: {missing} —— 红的是别的测试/别的参数实例, "
                "红灯与本变异之间没有因果关系"
            )
    return True, f"✓ 被抓住 ({len(r.failed)} 条门变红, 含全部预期门)"


def main() -> int:
    print("=" * 78)
    print("CARD-G4-3 变异门验证 (严格串行)")
    print("=" * 78)

    # ── 开跑前先校验全部锚点 (2026-08-31 教训) ──────────────────────────
    # 上一版 M10 的锚点是照着"格式化前"的多行文本写的, 而 ruff format 把它合成
    # 了一行 —— 脚本跑到第 10 个变异 (约 18 分钟后) 才 AssertionError 中止。
    # 锚点校验是纯字符串比对, 一秒就能做完; 放在最前面, 让"写错锚点"这类错误
    # 在第 1 秒暴露而不是第 18 分钟。
    anchor_bad = []
    for name, _desc, patches, _expect in MUTATIONS:
        for f, old, _new in patches:
            n = Path(f).read_text().count(old)
            if n != 1:
                anchor_bad.append(f"{name}: {f} 命中 {n} 次 (需恰好 1 次)")
    if anchor_bad:
        print("\n✗ 锚点预校验失败, 未施加任何变异:")
        for b in anchor_bad:
            print("   -", b)
        return 2
    print(f"\n[锚点预校验] {len(MUTATIONS)} 个变异的全部锚点均恰好命中 1 次 ✓")

    base = run_pytest()
    print(f"\n[基线] rc={base.rc} collected={base.collected}\n{base.tail}")
    if base.rc != 0 or base.failed:
        print("\n✗ 变异前基线就不是全绿 —— 先修好再跑变异, 否则结论不可读")
        return 2
    if base.collected is None:
        print("\n✗ 基线连收集都失败 —— 环境有问题")
        return 2
    baseline_collected = base.collected

    failures: List[str] = []
    for name, desc, patches, expect in MUTATIONS:
        touched = sorted({f for f, _, _ in patches})
        tmpdir = Path(tempfile.mkdtemp(prefix=f"g43-{name}-"))
        backups = {f: tmpdir / Path(f).name for f in touched}
        for f, b in backups.items():
            shutil.copy2(f, b)
        try:
            for f, old, new in patches:
                p = Path(f)
                s = p.read_text()
                # 坑 3: 锚点不命中必须当场炸, 不能静默跳过
                if s.count(old) != 1:
                    raise AssertionError(
                        f"{name}: 锚点在 {f} 中出现 {s.count(old)} 次 (需恰好 1 次)"
                    )
                p.write_text(s.replace(old, new, 1))

            r = run_pytest()
            caught, verdict = judge_kill(baseline_collected, r, expect)
            print(f"\n[{name}] {desc}\n  → {verdict}")
            print(f"  collected={r.collected} (基线 {baseline_collected})  rc={r.rc}")
            print("  " + r.tail.replace("\n", "\n  "))
            if not caught:
                failures.append(f"{name}: {desc} —— {verdict}")
        finally:
            # 坑 2: 无条件还原 + 逐字校验
            for f, b in backups.items():
                shutil.copy2(b, f)
                if not filecmp.cmp(b, f, shallow=False):
                    print(
                        f"  ✗ {f} 还原后与备份不逐字相同 —— 工作树已污染, 立即人工检查"
                    )
                    return 3
            print(f"  还原逐字相同 ✓ ({', '.join(Path(f).name for f in touched)})")

    fin = run_pytest()
    print(f"\n[还原后复跑] rc={fin.rc} collected={fin.collected}\n{fin.tail}")
    rc = fin.rc if not fin.failed and fin.collected == baseline_collected else 1

    print("\n" + "=" * 78)
    if failures or rc != 0:
        print("✗ 存在未被抓住的变异 (= 死门):")
        for f in failures:
            print("   -", f)
        return 1
    print(f"✓ {len(MUTATIONS)} 个变异全部被门抓住, 且还原后仍全绿")
    return 0


if __name__ == "__main__":
    sys.exit(main())
