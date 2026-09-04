#!/usr/bin/env python3
"""CARD-G4-4b 变异负控 — 串行; 每条变异后立即还原 + 全文件 SHA 逐字节比对。

相对 CARD-G4-4a 的 g44_mutations.py 修了它被 Codex round-4 点名的三处 (HIGH-3
「留存粒度不足」+ 无 __main__ 守卫 + SIGTERM 绕过 finally):

1. **记录失败身份**: kill 时不只记 exit code, 还保存 nodeid 与 pytest 的 `^E `
   行。只记 exit code 无法回溯「红的是哪一条断言」—— 4a 的 M6 就踩过这个
   (报 KILLED, 但红的是门里更靠前的另一条断言, 真正的探针被短路挡住)。
2. **__main__ 守卫**: 无守卫时 `import` 本文件 = 直接对生产源码施加变异。
3. **SIGTERM/SIGINT 处理**: 默认处置不做栈展开, finally 不执行, 变异体会留在
   工作树里。这里把它们转成异常, 让 finally 跑到。

用法: `G44B_BACKEND=<lane>/backend python g44b_mutations.py`
"""
import hashlib
import os
import signal
import subprocess
import sys
from pathlib import Path


def _die_on_signal(signum, _frame):
    raise SystemExit(f"收到信号 {signum}，中止（finally 将还原）")


def build_mutations(CLIENT, NODES):
    """返回 [(名称, 指定门 nodeid, 变异函数)]。变异函数只做替换, 断言锚点唯一。"""

    def m1_drop_subject_clause():
        """去掉 where 的 subject 子句 → 跨 subject 泄漏回归。"""
        s = CLIENT.read_text(encoding="utf-8")
        old = '''                    if subject:
                        where_clause += f" AND subject = '{self._escape_sql(subject)}'"'''
        new = '''                    if subject:
                        pass  # MUTANT-M1: subject 子句被去掉'''
        assert s.count(old) == 1, f"M1 锚点 {s.count(old)}"
        CLIENT.write_text(s.replace(old, new), encoding="utf-8")

    def m2_drop_escape():
        """去掉 _escape_sql → 单引号注入撑开 where。"""
        s = CLIENT.read_text(encoding="utf-8")
        old = """where_clause += f" AND subject = '{self._escape_sql(subject)}'\""""
        new = """where_clause += f" AND subject = '{subject}'\"  # MUTANT-M2: 去转义"""
        assert s.count(old) == 1, f"M2 锚点 {s.count(old)}"
        CLIENT.write_text(s.replace(old, new), encoding="utf-8")

    def m3_drop_passthrough():
        """nodes.py 调用点不再透传 subject → 链路级泄漏回归。"""
        s = NODES.read_text(encoding="utf-8")
        old = "            subject=state.get(\"subject\"),\n"
        assert s.count(old) == 1, f"M3 锚点 {s.count(old)}"
        NODES.write_text(s.replace(old, "", 1), encoding="utf-8")

    U = "tests/unit/test_agentic_rag_vault_scope.py"
    return [
        (
            "M1-去subject子句",
            f"{U}::TestExpandNeighborsSubjectFilter::test_subject_math_drops_physics_neighbor",
            m1_drop_subject_clause,
        ),
        (
            "M2-去转义",
            f"{U}::TestExpandNeighborsSubjectFilter::"
            "test_single_quote_injection_does_not_break_where",
            m2_drop_escape,
        ),
        (
            "M3-调用点不透传",
            f"{U}::TestDualVaultIsolationOnTmpLanceDB::"
            "test_neighbor_expansion_respects_subject_boundary",
            m3_drop_passthrough,
        ),
    ]


def main() -> int:
    signal.signal(signal.SIGTERM, _die_on_signal)
    signal.signal(signal.SIGINT, _die_on_signal)

    BACKEND = Path(os.environ["G44B_BACKEND"]).resolve()
    CLIENT = BACKEND / "lib/agentic_rag/clients/lancedb_client.py"
    NODES = BACKEND / "lib/agentic_rag/nodes.py"
    TARGETS = (CLIENT, NODES)
    BACKUP = {p: p.read_bytes() for p in TARGETS}
    SHA0 = {p: hashlib.sha256(b).hexdigest() for p, b in BACKUP.items()}

    def restore(step: str) -> None:
        """无条件还原 + 对**全部**被变异文件逐个复核 (不是只盯一个)。"""
        for p in TARGETS:
            p.write_bytes(BACKUP[p])
        for p in TARGETS:
            if hashlib.sha256(p.read_bytes()).hexdigest() != SHA0[p]:
                print(f"!!! [{step}] 还原后 SHA 不一致: {p}", file=sys.stderr)
                raise SystemExit(2)

    def run_gate(nodeid: str):
        r = subprocess.run(
            [
                str(BACKEND / ".venv/bin/pytest"), nodeid,
                "-q", "-p", "no:cacheprovider", "--tb=line", "-rf",
            ],
            cwd=str(BACKEND), capture_output=True, text=True, timeout=900,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        out = r.stdout + r.stderr
        # 失败身份: pytest 的 `^E ` 行 (--tb=line 下是「文件:行: 断言消息」)
        ident = [ln.strip() for ln in out.splitlines() if ln.startswith("E ")]
        return r.returncode, ident

    mutations = build_mutations(CLIENT, NODES)
    failed = []
    print(f"CARD-G4-4b 变异负控 — {len(mutations)} 条, 串行\n")
    for name, nodeid, fn in mutations:
        try:
            fn()
            rc, ident = run_gate(nodeid)
        finally:
            restore(name)
        short = nodeid.split("::")[-1]
        if rc == 1:
            print(f"[{name}] ✓ 指定门变红 (exit=1)")
            print(f"    门: {short}")
            for line in ident[:2]:
                print(f"    失败身份: {line[:150]}")
        elif rc == 0:
            failed.append(name)
            print(f"[{name}] ✗✗✗ STILL GREEN — 死门 ({short})")
        else:
            failed.append(name)
            print(f"[{name}] ✗✗✗ exit={rc} 非 pytest 真失败 (usage/collection error)")
        print()

    if failed:
        print(f"FAILED MUTATIONS: {failed}")
        return 1
    print(f"ALL {len(mutations)} MUTATIONS KILLED THEIR GATES (exit=1 only) ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
