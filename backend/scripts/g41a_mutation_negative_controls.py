#!/usr/bin/env python3
"""CARD-G4-1a 假绿防线 — 读侧作用域门的机械变异负控。

> 批次: BATCH-2026-08-29-第六批 / 车道 T1
> 起因: Codex round-1 判定"验收单里的变异计数不可复现、无脚本无回执" ——
>       口头声称"门能红"不算证据, 必须能被任何人一条命令复跑。
> 参考: `backend/scripts/g23_mutation_negative_controls.py`(G2-3 同型先例)

做什么
------
逐个把**被测源码**改坏 (mutation), 跑对应的门, 断言该门**确实变红**; 然后
还原并逐字节比对。一条变异若跑完仍全绿, 说明那道门是死门 —— 它锁不住任何东西。

⚠️ 必须串行 (记忆教训 `变异脚本必须串行`): 脚本原地改被测文件, 并发跑会让
后一个变异的还原把前一个的 mutation 写回, 而测试照样全绿。

覆盖的变异类
------------
全局方向 (证明"整体方向"锁得住):
  eq-only      : 前缀语义退回等值        → 保召回门必红
  always-true  : 过滤恒真 (= 不过滤)      → 零泄漏/保隔离门必红
  mem-eq-only  : 内存侧退回等值          → 内存保召回门必红
  mem-always   : 内存侧恒真              → 内存零泄漏门必红
逐 alias (Codex round-1 H-4: 全同组 fixture 杀不掉单 alias 变异):
  alias-c / alias-r / alias-n / alias-cn / alias-e / alias-neighbor
                                        → 对应 alias 的异组负门必红
fail-closed (证明"配置坏了会说话"):
  no-fail-closed : 解析失败改为返回污染桶而不是抛 → fail-closed 门必红
  no-shape-check : 去掉形状校验                  → 形状门必红

用法
----
    cd backend && .venv/bin/python scripts/g41a_mutation_negative_controls.py
    # 只跑某几类:
    cd backend && .venv/bin/python scripts/g41a_mutation_negative_controls.py eq-only alias-r

需 7692 测试容器可达 (真库门); 不可达时真库门会 skip, 脚本按 skip 计入并
显式提示 —— skip 不算"能红"。
"""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
SCOPE = BACKEND / "app" / "core" / "vault_scope.py"
CLIENT = BACKEND / "app" / "clients" / "neo4j_client.py"
TARGETS = (SCOPE, CLIENT)
PYTEST = BACKEND / ".venv" / "bin" / "pytest"

GATE_FILE = "tests/integration/test_cypher_contract_gate.py"
UNIT_SCOPE = "tests/unit/test_vault_scope_read_g41a.py"
UNIT_MEM = "tests/unit/test_memory_read_scope_g41a.py"
UNIT_CALLERS = "tests/unit/test_read_scope_callers_g41a.py"

# ── 变异原料 ────────────────────────────────────────────────────────────────

_FILTER_BODY = '''    clauses = [
        f"{alias}.group_id = $group_id",
        f"{alias}.group_id STARTS WITH $group_prefix",
    ]'''

_INSCOPE_BODY = """    return cand_phys == scope_phys or cand_phys.startswith(
        scope_phys + _PHYSICAL_SEPARATOR
    )"""


def _alias_noop(alias: str) -> tuple[str, str]:
    """把**单个** alias 的过滤片段变成恒真, 其余 alias 不动。"""
    return (
        _FILTER_BODY,
        f'''    if alias == {alias!r}:
        return "(true)"
{_FILTER_BODY}''',
    )


@dataclass(frozen=True)
class Mutation:
    name: str
    #: (原文, 替换文) 列表 — 全部必须命中且唯一; 默认改 vault_scope.py
    edits: list = field(default_factory=list)
    #: 期望变红的测试选择器 (pytest 参数)
    expect_red: list = field(default_factory=list)
    why: str = ""
    #: 被改的文件 (默认 vault_scope.py)
    target: Path = SCOPE


MUTATIONS: list[Mutation] = [
    Mutation(
        name="eq-only",
        edits=[
            (
                _FILTER_BODY,
                '''    clauses = [
        f"{alias}.group_id = $group_id",
    ]''',
            ),
            (_INSCOPE_BODY, "    return cand_phys == scope_phys"),
        ],
        expect_red=[GATE_FILE, UNIT_SCOPE, UNIT_MEM],
        why="前缀语义退回等值 ⇒ vault 根组读不到 canvas/semantic/punycode 子组",
    ),
    Mutation(
        name="always-true",
        edits=[
            (_FILTER_BODY, _FILTER_BODY.replace("clauses = [", 'clauses = ["true", ')),
            (_INSCOPE_BODY, "    return True"),
        ],
        expect_red=[GATE_FILE, UNIT_SCOPE, UNIT_MEM],
        why="过滤恒真 ⇒ 他 vault 与兄弟白板全部可见",
    ),
    Mutation(
        name="mem-eq-only",
        edits=[(_INSCOPE_BODY, "    return cand_phys == scope_phys")],
        expect_red=[UNIT_MEM],
        why="内存侧退回等值 ⇒ Tier3/内存兜底看不到子组 (与 Cypher 侧可见面不一致)",
    ),
    Mutation(
        name="mem-always",
        edits=[(_INSCOPE_BODY, "    return True")],
        expect_red=[UNIT_MEM],
        why="内存侧恒真 ⇒ 他 vault 的内存 episode 可见",
    ),
    Mutation(
        name="no-fail-closed",
        edits=[
            (
                "        raise VaultScopeUnresolved(\n"
                "            f\"read scope unresolved [context: {context}]: derived scope is the \"",
                "        return _DEFAULT_POLLUTION_GROUP  # MUTATED\n"
                "        raise VaultScopeUnresolved(\n"
                "            f\"read scope unresolved [context: {context}]: derived scope is the \"",
            )
        ],
        expect_red=[UNIT_SCOPE, GATE_FILE],
        why="推导出污染桶不再抛 ⇒ 配置故障被伪装成正常空结果 (静默断读)",
    ),
    Mutation(
        name="no-shape-check",
        edits=[
            (
                '    value = group_id.strip()\n\n    if not value.startswith("vault:"):',
                '    value = group_id.strip()\n    return value  # MUTATED\n\n'
                '    if not value.startswith("vault:"):',
            )
        ],
        expect_red=[UNIT_SCOPE],
        why="去掉形状校验 ⇒ 'vault:' / 'vault__' / 污染桶都被当成有效作用域",
    ),
    *[
        Mutation(
            name=f"alias-{a}",
            edits=[_alias_noop(a)],
            expect_red=[GATE_FILE],
            why=f"单独放行 alias {a!r} ⇒ 该 alias 的异组负门必须现形",
        )
        # c/r: review+history; n/cn/e: score-history; neighbor: inheritance
        for a in ("c", "r", "n", "cn", "e", "neighbor")
    ],
    # ── Codex round-2 反证对应的三类 ────────────────────────────────────
    Mutation(
        name="no-collision-check",
        edits=[
            (
                "    if any(_PHYSICAL_SEPARATOR in seg for seg in segments):",
                "    if False:  # MUTATED",
            )
        ],
        expect_red=[UNIT_CALLERS],
        why="去掉物理 ID 碰撞校验 ⇒ vault:a__board 与 vault:a:board 共用可见面",
    ),
    Mutation(
        name="json-review-unscoped",
        target=CLIENT,
        edits=[
            (
                "            if not group_in_read_scope(rel.get(\"group_id\"), scope):\n"
                "                continue\n\n"
                "            # Check if due for review",
                "            # MUTATED (filter removed)\n\n"
                "            # Check if due for review",
            )
        ],
        expect_red=[UNIT_CALLERS],
        why="JSON 降级模式的复习建议不过滤 ⇒ 把 Neo4j 弄挂就能绕过封堵",
    ),
    Mutation(
        name="json-concept-id-unscoped",
        target=CLIENT,
        edits=[
            (
                "                                if c[\"name\"] == rel[\"concept_name\"]\n"
                "                                and group_in_read_scope(c.get(\"group_id\"), scope)",
                "                                if c[\"name\"] == rel[\"concept_name\"]",
            )
        ],
        expect_red=[UNIT_CALLERS],
        why="concept 反查不过 scope ⇒ 取到他 vault 同名概念的 id (标识符串读)",
    ),
    Mutation(
        name="ctxvar-treated-as-derived",
        edits=[
            (
                "        return _validate_scope_shape(\n"
                "            canonical_group_id(ctx), context=context, explicit=True\n"
                "        )",
                "        return _validate_scope_shape(\n"
                "            canonical_group_id(ctx), context=context, explicit=False\n"
                "        )",
            )
        ],
        expect_red=[UNIT_CALLERS],
        why="把 ContextVar 注入值当成推导 ⇒ deprecated 兼容层在读侧被打断",
    ),
    Mutation(
        name="json-score-unscoped",
        target=CLIENT,
        edits=[
            (
                "                if not group_in_read_scope(record.get(\"group_id\"), scope):\n"
                "                    continue\n",
                "                pass  # MUTATED (filter removed)\n",
            )
        ],
        expect_red=[UNIT_CALLERS],
        why="JSON 降级模式的历史分数不过滤 ⇒ 两 vault 同名节点互读",
    ),
]


# ── 执行 ────────────────────────────────────────────────────────────────────


def _apply(text: str, edits) -> str:
    for old, new in edits:
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"变异原料失配: 期望恰 1 处命中, 实得 {count}\n---\n{old[:200]}\n---\n"
                "(被测源码改过 ⇒ 请同步更新本脚本的变异原料, 否则负控是假的)"
            )
        text = text.replace(old, new)
    return text


def _run(selectors: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [str(PYTEST), *selectors, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


_SUMMARY_RE = re.compile(r"(\d+) failed|(\d+) passed|(\d+) skipped|(\d+) error")


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

        # 前置: 未变异时必须全绿 (否则"变红"没有对照意义)
        code, out = _run([GATE_FILE, UNIT_SCOPE, UNIT_MEM, UNIT_CALLERS])
        print(f"[baseline] {_summary(out)}")
        if code != 0:
            print("⛔ 基线就不是全绿 — 先修好再跑负控", file=sys.stderr)
            return 2
        if "skipped" in out and "passed" in out and " 0 skipped" not in out:
            print("⚠️  有 skip (7692 容器不可达?) — skip 不构成'能红'证据")

        results = []
        for m in chosen:
            try:
                m.target.write_text(_apply(originals[m.target], m.edits))
                code, out = _run(m.expect_red)
                summary = _summary(out)
                red = code != 0 and " failed" in out
                results.append((m.name, red, summary, m.why))
                print(f"[{m.name:16}] {'RED  ✅' if red else 'GREEN ⛔'}  {summary}")
            finally:
                # 还原 + 逐字节比对 (串行铁律)。注意: 不在 finally 里 return ——
                # 那会吞掉正在传播的异常 (SyntaxWarning 'return in finally')。
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
