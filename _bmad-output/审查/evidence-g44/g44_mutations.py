#!/usr/bin/env python3
"""CARD-G4-4 变异负控制 — 串行; 每变异后立即还原 + SHA 逐字节比对。

纪律: 判据 = 指定门变红 (不是「某处有失败」); 还原以字节为准。
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(os.environ["G44_BACKEND"]).resolve()

RAG = BACKEND / "app/api/v1/endpoints/rag.py"
NODES = BACKEND / "lib/agentic_rag/nodes.py"
UNIT = BACKEND / "tests/unit/test_agentic_rag_vault_scope.py"

TARGETS = (RAG, NODES, UNIT)
BACKUP = {p: p.read_bytes() for p in TARGETS}
SHA0 = {p: hashlib.sha256(b).hexdigest() for p, b in BACKUP.items()}

def run_gate(test_id: str) -> int:
    if test_id.startswith(("TestInner", "TestDual", "TestCurrent")):
        f = "tests/unit/test_agentic_rag_vault_scope.py"
    else:
        f = "tests/api/v1/endpoints/test_rag_vault_scope_api.py"
    r = subprocess.run(
        [".venv/bin/pytest", f"{f}::{test_id}", "-q", "-p", "no:cacheprovider"],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=600,
    )
    return r.returncode

def restore_and_verify(step: str):
    for p in TARGETS:
        p.write_bytes(BACKUP[p])
    for p in TARGETS:
        now = hashlib.sha256(p.read_bytes()).hexdigest()
        if now != SHA0[p]:
            print(f"!!! [{step}] 还原后 SHA 不一致: {p.name} — 硬失败")
            sys.exit(2)
    print(f"[{step}] 还原逐字节一致 ✓")

MUTATIONS = []

def m1():
    s = RAG.read_text()
    old = '''    vault_id: str = Field(
        ...,
        min_length=1,'''
    new = '''    vault_id: Optional[str] = Field(
        None,
        min_length=1,'''
    assert old in s, "M1 anchor not found"
    RAG.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M1-去422", "TestVaultIdRequired::test_missing_vault_id_rejected_with_422", m1))

def m2():
    s = RAG.read_text()
    old = """    _scope = resolve_vault_scope(
        request.vault_id,
        subject_id=request.subject_id,
        canvas_path=request.canvas_file,
    )"""
    new = """    if request.subject_id:
        from app.core.subject_config import set_current_subject_id
        set_current_subject_id(request.subject_id)"""
    assert old in s, "M2 anchor not found"
    RAG.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M2-去409-恢复旁路", "TestVaultConflict::test_mismatched_vault_rejected_with_409", m2))

def m3():
    s = NODES.read_text()
    old = "memory_group_id = build_vault_group_id(current_vault_id())"
    new = ("from app.config import get_current_vault_id as _g44_proc\n"
           "                memory_group_id = build_vault_group_id(_g44_proc())")
    assert old in s, "M3 anchor not found"
    NODES.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M3-内链改回进程级", "TestInnerChainReadsRequestScope::test_compress_context_memory_group_uses_request_scope", m3))

def m4():
    s = UNIT.read_text()
    old = '''        "vault_b_canvas_nodes": ['''
    new = '''        "vault_a_canvas_nodes": [
            {
                "doc_id": "b_unique",
                "content": "贝尔不等式的量子纠缠判据",
                "vector": _vec(0.10),
                "content_tokenized": _jieba_tokens("贝尔不等式的量子纠缠判据"),
                "canvas_file": "b.canvas",
            },
        ],  # M4 同组化变异: B 独有笔记复制进 A 表
        "vault_b_canvas_nodes": ['''
    assert old in s, "M4 anchor not found"
    UNIT.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M4-fixture同组化", "TestDualVaultIsolationOnTmpLanceDB::test_vault_a_query_has_zero_results_from_b", m4))

def m5():
    """加验: 哨兵改静默 → 一致性告警门死。"""
    s = NODES.read_text()
    old = '"[%s] state.subject=%r 与请求级 VaultScope 二级 %r 不一致 — "'
    new = '"[%s] state.subject=%r 与请求级 VaultScope 二级 %r (debug) "'
    assert old in s, "M5 anchor not found"
    NODES.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M5-哨兵降级debug", "TestSubjectScopeSentinel::test_mismatch_warns", m5))

failed = []
for name, gate, fn in MUTATIONS:
    fn()
    rc = run_gate(gate)
    restore_and_verify(name)
    if rc == 0:
        failed.append(name)
        print(f"[{name}] ✗✗✗ STILL GREEN — 死门")
    else:
        print(f"[{name}] ✓ 指定门变红 (exit={rc})")

print()
if failed:
    print(f"FAILED MUTATIONS: {failed}")
    sys.exit(1)
print(f"ALL {len(MUTATIONS)} MUTATIONS KILLED THEIR GATES ✓")
