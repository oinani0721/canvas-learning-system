#!/usr/bin/env python3
"""CARD-G4-1b 假绿防线 — client 层读收口门的机械变异负控。

> 批次: BATCH-2026-08-31-第七批 / 车道 V1
> 同型先例: `g23_mutation_negative_controls.py`(G2-3) /
>           `g41a_mutation_negative_controls.py`(G4-1a)

做什么
------
逐个把**被测源码**改坏 (mutation), 跑对应的门, 断言该门**确实变红**; 然后
还原并逐字节比对。一条变异若跑完仍全绿, 说明那道门是死门 —— 它锁不住任何东西。

⚠️ 必须串行 (记忆教训 `变异脚本必须串行`): 脚本原地改被测文件, 并发跑会让
后一个变异的还原把前一个的 mutation 写回, 而测试照样全绿。

覆盖的变异类
------------
concept-history (名实一致 + 逐 alias):
  ch-json-simulator : 退回"永远读 JSON 模拟器"    → 名实一致门必红
  ch-drop-c / ch-drop-r : 单个 alias 放行           → 对应逐 alias 负门必红
recovery / episodes:
  episodes-unscoped      : Cypher 侧全库扫回归      → 作用域门 + 恢复门必红
  episodes-json-unscoped : episodes 镜像不过滤       → unit 镜像门 + 真库对拍门必红
                           (**不**会红误路由门 —— 那条走 `_handle_query_history`,
                            不经过 `_get_all_recent_episodes_json`)
  recovery-contextvar    : 恢复改用请求级作用域     → 进程级缓存收窄门必红
误路由:
  history-handler-warn-only : 退回 G4-1a 的"告警不拒绝" → fail-closed 门必红
关联族 (双料僵尸, 只有契约门):
  assoc-drop-target / assoc-json-unscoped
  canvas-concepts-drop-n / canvas-concepts-json-unscoped
  common-drop-c2

用法
----
    cd backend && .venv/bin/python scripts/g41b_mutation_negative_controls.py
    cd backend && .venv/bin/python scripts/g41b_mutation_negative_controls.py ch-drop-c

需 7692 测试容器可达 (真库门); 不可达时真库门会 skip, skip **不算**"能红"。
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
CLIENT = BACKEND / "app" / "clients" / "neo4j_client.py"
MEMSVC = BACKEND / "app" / "services" / "memory_service.py"
TARGETS = (CLIENT, MEMSVC)
PYTEST = BACKEND / ".venv" / "bin" / "pytest"

GATE = "tests/integration/test_cypher_contract_gate.py"
UNIT_CLIENT = "tests/unit/test_neo4j_client.py"
UNIT_RECOVERY = "tests/unit/test_story_38_2_episode_recovery.py"
ALL_SUITES = [GATE, UNIT_CLIENT, UNIT_RECOVERY]


@dataclass(frozen=True)
class Mutation:
    name: str
    edits: list = field(default_factory=list)
    #: 跑哪些套件
    expect_red: list = field(default_factory=list)
    #: **必须**出现在失败清单里的测试名片段。Codex round-1 MEDIUM 整改:
    #: 只看"整个文件有测试失败"证明不了**声称的那道门**红了 —— 变异可能
    #: 撞红了另一条无关用例, 而真正该锁住它的门仍是死门。
    expect_red_tests: list = field(default_factory=list)
    why: str = ""
    target: Path = CLIENT


_CH_FILTERS = """          AND {read_group_filter("r")}
          AND {read_group_filter("c")}{user_clause}"""

_EPISODES_WHERE = """        MATCH (u:User)-[r:LEARNED]->(c:Concept)
        WHERE {read_group_filter("r")}
          AND {read_group_filter("c")}
        RETURN u.id as user_id,"""

MUTATIONS: list[Mutation] = [
    Mutation(
        name="ch-json-simulator",
        edits=[
            (
                "        if self._use_json_fallback:\n"
                "            results = await self._handle_query_history(params)\n"
                "            return results[:limit]",
                "        results = await self._handle_query_history(params)  # MUTATED\n        return results[:limit]",
            )
        ],
        expect_red=[GATE],
        expect_red_tests=["test_g41b_concept_history_is_not_reading_the_json_simulator"],
        why="get_concept_history 退回'永远读 JSON 模拟器' ⇒ 端点恒空 (名实不符原状)",
    ),
    Mutation(
        name="ch-and-not-or",
        edits=[
            (
                '_CONCEPT_ID_MATCH_CYPHER = "(c.id = $conceptId OR c.name = $conceptId)"',
                '_CONCEPT_ID_MATCH_CYPHER = "(c.id = $conceptId AND c.name = $conceptId)"',
            ),
            (
                '    return rel.get("concept_id") == concept_id or rel.get("concept_name") == concept_id',
                '    return rel.get("concept_id") == concept_id and rel.get("concept_name") == concept_id',
            ),
        ],
        expect_red=[GATE, UNIT_CLIENT],
        expect_red_tests=[
            "test_g41b_concept_history_matches_production_shape_without_c_id",
            "test_concept_id_match_is_id_or_name_on_both_sides",
        ],
        why="点查从 id OR name 退化为 AND ⇒ 生产形态 (c.id 为 null) 端点重新恒空",
    ),
    Mutation(
        name="ch-drop-c",
        # ⚠️ 指定的是**逐 alias** 门而不是 recall/isolation 门: 后者的 fixture
        # 把 concept 与 LEARNED 边放在同一个 group, 丢掉 `c` 的过滤仍被 `r`
        # 兜住 —— 结构上就杀不掉单 alias 变异 (门 6 的 H-4 教训)。首跑把它
        # 写成期望门, 脚本立刻报"未红的指定门", 判据自身被验伪了一次。
        expect_red_tests=[
            "test_g41b_concept_history_per_alias[g21gate_g41a_xc-False]",
            "test_cypher_filters_every_alias[get_concept_history-kwargs4-branch_aliases4]",
        ],
        edits=[(_CH_FILTERS, '          AND {read_group_filter("r")}{user_clause}')],
        expect_red=[GATE, UNIT_CLIENT],
        why="概念节点 alias 不过滤 ⇒ 他 vault 同名概念的历史现形",
    ),
    Mutation(
        name="ch-drop-r",
        expect_red_tests=[
            "test_g41b_concept_history_per_alias[g21gate_g41a_xr-False]",
            "test_cypher_filters_every_alias[get_concept_history-kwargs4-branch_aliases4]",
        ],
        edits=[(_CH_FILTERS, '          AND {read_group_filter("c")}{user_clause}')],
        expect_red=[GATE, UNIT_CLIENT],
        why="LEARNED 边 alias 不过滤 ⇒ 边归属跨组的记录现形",
    ),
    Mutation(
        name="episodes-unscoped",
        expect_red_tests=["test_g41b_all_recent_episodes_scoped", "test_g41b_recovery_loads_only_active_vault_family"],
        edits=[
            (
                _EPISODES_WHERE,
                "        MATCH (u:User)-[r:LEARNED]->(c:Concept)\n"
                "        WHERE true  // MUTATED\n"
                "        RETURN u.id as user_id,",
            )
        ],
        expect_red=[GATE, UNIT_CLIENT],
        why="恢复源查询退回全库扫 ⇒ 他 vault 的 episode 进进程级缓存",
    ),
    Mutation(
        name="episodes-json-unscoped",
        # Codex round-2 Q6: 只指 unit 镜像门的话, 真库对拍门 (7.5) 即使是死门
        # 脚本也会判 RED。两条都要求红 —— 镜像不过滤时, 对拍门的两侧集合必然
        # 不等, 它**应当**红。
        expect_red_tests=[
            "test_all_recent_episodes_json_mirror_is_scoped",
            "test_g41b_json_mirror_visibility_equals_cypher",
        ],
        edits=[
            (
                '        rels = self._data.get("relationships", [])\n'
                "        results = []\n"
                "        for rel in rels:\n"
                '            if not group_in_read_scope(rel.get("group_id"), scope):\n'
                "                continue",
                '        rels = self._data.get("relationships", [])\n'
                "        results = []\n"
                "        for rel in rels:  # MUTATED (filter removed)",
            )
        ],
        expect_red=[GATE, UNIT_CLIENT, UNIT_RECOVERY],
        why="episode 镜像不过滤 ⇒ 把 Neo4j 弄挂就能绕过封堵",
    ),
    Mutation(
        name="history-handler-warn-only",
        expect_red_tests=[
            "test_g41b_handle_query_history_fail_closed_without_scope",
            "test_handle_query_history_fail_closed",
        ],
        edits=[
            (
                "                concept_id,\n            )\n            return []",
                "                concept_id,\n            )  # MUTATED (fail-closed removed)",
            ),
            (
                # 锚点用"概念点查 + group 过滤"这对相邻行 —— 只有本 handler 有
                # `_concept_id_matches`, 唯一性由它保证 (Codex round-2 的 Q3
                # 整改在 group 过滤之后插入了 date/concept 过滤, 原来跨到
                # `results.append` 的锚点因此失配)。
                "            if concept_id and not _concept_id_matches(rel, concept_id):\n"
                "                continue\n"
                '            if not group_in_read_scope(rel.get("group_id"), scope):\n'
                "                continue\n",
                "            if concept_id and not _concept_id_matches(rel, concept_id):\n"
                "                continue\n"
                '            if scope and not group_in_read_scope(rel.get("group_id"), scope):\n'
                "                continue\n",
            ),
        ],
        expect_red=[GATE, UNIT_CLIENT],
        why="_handle_query_history 退回 G4-1a 的'告警不拒绝' ⇒ 中途降级整库倾倒",
    ),
    Mutation(
        name="misroute-drops-group-id",
        edits=[
            (
                # ⚠️ 必须**替换**这一行, 不能在它前面插一个同名键 —— Python dict
                # 字面量里重复键**后者胜**, 前插等于空操作, 变异脚本实测判 GREEN
                # 并点名了这条(判据自身又验伪了一次)。
                "                    \"group_id\": desanitize_group_id_from_graphiti(\n"
                "                        rel.get(\"group_id\") or \"\"\n"
                "                    ),\n",
                "                    # MUTATED (退回不返回归属)\n",
            )
        ],
        expect_red=[UNIT_CLIENT],
        expect_red_tests=[
            "test_misroute_handler_returns_same_keys_as_json_mirror",
            "test_midflight_recovered_episode_stays_visible",
        ],
        why="降级落点不返回 group_id ⇒ 恢复的 episode 无归属, 被每一次作用域读永久挡掉",
    ),
    Mutation(
        name="no-temporal-normalization",
        edits=[
            (
                "        # 独立审计 HIGH: temporal → ISO 串, 否则响应模型校验失败 → 端点 500\n"
                "        return _iso_timestamps(results or [])[:limit]",
                "        return (results or [])[:limit]  # MUTATED (退回裸 temporal)",
            )
        ],
        expect_red=[GATE],
        expect_red_tests=[
            "test_g41b_production_shape_reaches_api_response_model",
            "test_g41b_learned_reads_return_same_timestamp_type_as_json_mirror",
        ],
        why="Cypher 读回的 temporal 不归一 ⇒ 响应模型 ValidationError ⇒ 端点一有数据就 500",
    ),
    Mutation(
        name="review-count-none-not-defaulted",
        target=MEMSVC,
        edits=[
            (
                # ⚠️ 必须**替换**那一行, 不能前插同名键 —— dict 字面量重复键后者胜,
                # 前插=空操作。这个错在本轮连犯两次(misroute 与本条), 两次都由
                # "指定门必须变红"的判据当场抓出。
                # 锚点带上前面的注释块保证唯一 (recovery 那处也写 `or 0`)。
                '                    # → 端点 500。本卡把这条路径从"恒空"变成"真有数据"之后,\n'
                '                    # 这个既有缺陷才第一次可达, 故随本卡一并收。\n'
                '                    "review_count": record.get("review_count") or 0,',
                '                    "review_count": record.get("review_count", 0),  # MUTATED',
            )
        ],
        expect_red=[GATE],
        expect_red_tests=["test_g41b_production_shape_reaches_api_response_model"],
        why="`.get(k, 0)` 只在键缺失时兜底; Cypher 对不存在的属性返回 None ⇒ 响应模型收到 None",
    ),
    Mutation(
        name="history-handler-bound-parse-lenient",
        edits=[
            (
                "                if (start_date and lo is None) or (end_date and hi is None):",
                "                if False:  # MUTATED (边界解析失败时静默跳过过滤)",
            )
        ],
        expect_red=[UNIT_CLIENT],
        expect_red_tests=["test_degraded_unparseable_date_bound_fails_closed"],
        why="畸形日期边界不再拒绝 ⇒ 过滤悄悄消失、记录全放行",
    ),
    Mutation(
        name="history-handler-string-time-compare",
        edits=[
            (
                '                ts = _as_utc(rel.get("timestamp"))\n',
                '                ts = rel.get("timestamp")  # MUTATED (回到字符串比较)\n',
            ),
            (
                "                lo = _as_utc(start_date) if start_date else None\n"
                "                hi = _as_utc(end_date) if end_date else None\n",
                "                lo = start_date  # MUTATED\n                hi = end_date\n",
            ),
        ],
        expect_red=[UNIT_CLIENT],
        expect_red_tests=["test_degraded_date_filter_is_timezone_correct"],
        why="日期过滤退回 ISO 字典序 ⇒ 混合时区偏移下边界条数静默错",
    ),
    Mutation(
        name="history-handler-drop-date-concept",
        edits=[
            (
                "            if start_date or end_date:",
                "            if False:  # MUTATED",
            ),
            (
                "            if concept_filter:",
                "            if False:  # MUTATED (concept)",
            ),
        ],
        expect_red=[GATE],
        expect_red_tests=["test_g41b_midflight_fallback_misroute_stays_scoped"],
        why="中途降级丢 startDate/endDate/concept ⇒ 降级前后返回的条数与内容不同",
    ),
    Mutation(
        name="recovery-contextvar",
        expect_red_tests=["test_recovery_passes_active_vault_group_not_contextvar"],
        target=MEMSVC,
        edits=[
            (
                "                records = await self.neo4j.get_all_recent_episodes(\n"
                "                    limit=1000, group_id=recovery_scope\n"
                "                )",
                "                records = await self.neo4j.get_all_recent_episodes(\n"
                "                    limit=1000\n"
                "                )  # MUTATED",
            )
        ],
        expect_red=[GATE, UNIT_RECOVERY],
        why="恢复改用请求级 ContextVar ⇒ 进程级缓存被板级作用域永久收窄",
    ),
    Mutation(
        name="assoc-drop-target",
        expect_red_tests=["test_cypher_filters_every_alias[get_canvas_associations-kwargs0-branch_aliases0]"],
        edits=[
            (
                "        conditions = [\n"
                '            read_group_filter("source"),\n'
                '            read_group_filter("r"),\n'
                '            read_group_filter("target"),\n'
                "        ]",
                "        conditions = [\n"
                '            read_group_filter("source"),\n'
                '            read_group_filter("r"),\n'
                "        ]  # MUTATED",
            )
        ],
        expect_red=[UNIT_CLIENT],
        why="关联的 target 端不过滤 ⇒ 依赖'关联两端不跨组'这个不可证前提 (R1 CONDITIONAL)",
    ),
    Mutation(
        name="assoc-json-unscoped",
        expect_red_tests=["test_associations_json_mirror_is_scoped"],
        edits=[
            (
                "        for assoc in associations:\n"
                "            # Apply filters\n"
                '            if not group_in_read_scope(assoc.get("group_id"), scope):\n'
                "                continue",
                "        for assoc in associations:\n            # Apply filters  # MUTATED",
            )
        ],
        expect_red=[UNIT_CLIENT],
        why="关联镜像不过滤 ⇒ 降级后同名 canvas 的关联跨 vault 可见",
    ),
    Mutation(
        name="canvas-concepts-drop-n",
        expect_red_tests=["test_cypher_filters_every_alias[get_canvas_concepts-kwargs1-branch_aliases1]"],
        edits=[
            (
                '          AND {read_group_filter("cn")}\n'
                '          AND {read_group_filter("n")}\n'
                "        RETURN DISTINCT n.text as concept_name\n        UNION",
                '          AND {read_group_filter("cn")}\n'
                "        RETURN DISTINCT n.text as concept_name\n        UNION",
            )
        ],
        expect_red=[UNIT_CLIENT],
        why="节点 alias 不过滤 ⇒ 同名 canvas 下他 vault 的节点文本现形",
    ),
    Mutation(
        name="canvas-concepts-json-unscoped",
        # 只指作用域门。路径对称门 `test_mirror_path_match_is_exact_like_cypher`
        # 的两条 fixture 记录**都在作用域内**, 去掉 group 过滤不改变它的结果 ——
        # 把它列为期望红是我的映射错误, 精确判据当场报了"未红的指定门"。
        expect_red_tests=["test_canvas_concepts_json_mirror_is_scoped"],
        edits=[
            (
                "        # Check relationships for concepts linked to this canvas\n"
                '        for rel in self._data.get("relationships", []):\n'
                '            if not group_in_read_scope(rel.get("group_id"), scope):\n'
                "                continue\n",
                "        # Check relationships for concepts linked to this canvas\n"
                '        for rel in self._data.get("relationships", []):  # MUTATED\n',
            )
        ],
        expect_red=[UNIT_CLIENT],
        why="canvas 概念镜像不过滤 ⇒ find_common_concepts 会跨 vault 凑出'共同概念'",
    ),
    Mutation(
        name="common-drop-c2",
        expect_red_tests=["test_cypher_filters_every_alias[find_common_concepts-kwargs2-branch_aliases2]"],
        edits=[
            (
                '          AND {read_group_filter("c2")}\n          AND {read_group_filter("cn2")}',
                '          AND {read_group_filter("cn2")}',
            )
        ],
        expect_red=[UNIT_CLIENT],
        why="第二块白板的 Canvas alias 不过滤 ⇒ 交集的一边越出作用域",
    ),
]


def _apply(text: str, edits) -> str:
    for old, new in edits:
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"变异原料失配: 期望恰 1 处命中, 实得 {count}\n---\n{old[:240]}\n---\n"
                "(被测源码改过 ⇒ 请同步更新本脚本的变异原料, 否则负控是假的)"
            )
        text = text.replace(old, new)
    return text


def _run(selectors: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [str(PYTEST), *selectors, "-q", "--no-header", "-rf", "-p", "no:cacheprovider", "-p", "no:randomly"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _failed_tests(out: str) -> list[str]:
    """从 `-rf` 短摘要里抽出失败的测试 nodeid。"""
    return [
        line.split(" - ", 1)[0].removeprefix("FAILED ").strip()
        for line in out.splitlines()
        if line.startswith("FAILED ")
    ]


def _test_matches(spec: str, nodeid: str) -> bool:
    """指定门是否命中某条失败 nodeid。

    ⚠️ Codex round-2 Q6 整改: 原来是**子串**匹配, 于是
    ``test_foo`` 会被 ``test_foo_bar`` 满足 —— 判据比它声称的松。这里改成
    在 ``::`` 之后做**整段**比较: spec 不带 ``[...]`` 时比函数名整体,
    带 ``[...]`` 时比含参数 id 的完整名 (可精确指定参数化的某一条)。

    ⚠️ **仍存的上限(如实声明, 不宣称已解决)**: 判据的粒度是"这条测试红了",
    不是"红在我期望的那句断言上"。同一条测试里另一处断言先失败, 依然算命中。
    要再收紧就得比对失败信息文本, 那会把门与断言措辞耦死, 得不偿失。
    """
    tail = nodeid.rsplit("::", 1)[-1]
    if "[" in spec:
        return tail == spec
    return tail.split("[", 1)[0] == spec


def _summary(out: str) -> str:
    for line in reversed(out.strip().split("\n")):
        if "passed" in line or "failed" in line or "error" in line:
            return line.strip("= ")
    return "(no summary)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="*", help="只跑这些变异名 (默认全跑)")
    args = ap.parse_args()

    chosen = [m for m in MUTATIONS if not args.only or m.name in args.only]
    if args.only and len(chosen) != len(args.only):
        raise SystemExit(f"未知变异名: {set(args.only) - {m.name for m in chosen}}")

    originals = {t: t.read_text() for t in TARGETS}
    with tempfile.TemporaryDirectory() as tmp:
        backups = {}
        for t in TARGETS:
            b = Path(tmp) / (t.name + ".orig")
            b.write_text(originals[t])
            backups[t] = b

        code, out = _run(ALL_SUITES)
        print(f"[baseline] {_summary(out)}")
        if code != 0:
            print("⛔ 基线就不是全绿 — 先修好再跑负控", file=sys.stderr)
            return 2
        if "skipped" in out:
            print("⚠️  有 skip (7692 容器不可达?) — skip 不构成'能红'证据")

        results = []
        for m in chosen:
            try:
                m.target.write_text(_apply(originals[m.target], m.edits))
                code, out = _run(m.expect_red)
                summary = _summary(out)
                failed = _failed_tests(out)
                red = code != 0 and " failed" in out
                missing = [want for want in m.expect_red_tests if not any(_test_matches(want, nid) for nid in failed)]
                if missing:
                    # 有失败但**不是**声称的那道门 —— 按死门处理并点名
                    red = False
                    summary = f"{summary} | 未红的指定门: {missing}"
                results.append((m.name, red, summary, m.why))
                print(f"[{m.name:30}] {'RED  ✅' if red else 'GREEN ⛔'}  {summary}")
            finally:
                shutil.copyfile(backups[m.target], m.target)
                restored_ok = filecmp.cmp(backups[m.target], m.target, shallow=False)
            if not restored_ok:
                print("⛔ 还原后字节不一致 — 立即人工检查!", file=sys.stderr)
                return 3

    dead = [r for r in results if not r[1]]
    print()
    print(f"结果: {len(results) - len(dead)}/{len(results)} 变异被杀 (门能红)")
    for name, _red, summary, why in dead:
        print(f"  ⛔ 死门: {name} — {why}\n      实得: {summary}")
    return 1 if dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
