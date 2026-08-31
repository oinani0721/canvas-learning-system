#!/usr/bin/env python3
"""CARD-G4-4 变异负控制 v2 — 串行; 每变异后立即还原 + SHA 逐字节比对。

v2 (Codex round-1 整改):
- 判据收紧: 只有 exit==1 (pytest 真失败) 算杀门; exit==4 等 usage error
  一律硬失败 (v1 的「任意非零当 kill」证据缺陷)。
- M5 改为真降级 (warning → debug), 不再只改文案。
- 新增 M6: expand_neighbors 表名改回裸 "vault_notes" → 杀 BLOCKER-1 门。
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

def run_gate(test_id: str):
    if test_id.startswith(("TestInner", "TestDual", "TestCurrent", "TestAgent", "TestSubject")):
        f = "tests/unit/test_agentic_rag_vault_scope.py"
    else:
        f = "tests/api/v1/endpoints/test_rag_vault_scope_api.py"
    r = subprocess.run(
        [".venv/bin/pytest", f"{f}::{test_id}", "-q", "-p", "no:cacheprovider"],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=600,
    )
    return r.returncode, (r.stdout + r.stderr)[-300:]

def restore_and_verify(step: str):
    for p in TARGETS:
        p.write_bytes(BACKUP[p])
    for p in TARGETS:
        if hashlib.sha256(p.read_bytes()).hexdigest() != SHA0[p]:
            print(f"!!! [{step}] 还原后 SHA 不一致: {p.name}")
            sys.exit(2)

MUTATIONS = []

def m1():
    s = RAG.read_text()
    old = '''    vault_id: str = Field(
        ...,
        min_length=1,'''
    new = '''    vault_id: Optional[str] = Field(
        None,
        min_length=1,'''
    assert old in s
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
    assert old in s
    RAG.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M2-去409-恢复旁路", "TestVaultConflict::test_mismatched_vault_rejected_with_409", m2))

def m3():
    s = NODES.read_text()
    old = "memory_group_id = build_vault_group_id(current_vault_id())"
    new = ("from app.config import get_current_vault_id as _g44_proc\n"
           "                memory_group_id = build_vault_group_id(_g44_proc())")
    assert old in s
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
        ],  # M4 同组化变异
        "vault_b_canvas_nodes": ['''
    assert old in s
    UNIT.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M4-fixture同组化", "TestDualVaultIsolationOnTmpLanceDB::test_vault_a_query_has_zero_results_from_b", m4))

def m5():
    """真降级: 哨兵 mismatch 分支 warning → debug (v1 只改文案是假变异)。"""
    s = NODES.read_text()
    old = '''        if len(parts) >= 3 and parts[2] and parts[2] != sanitize_subject_name(str(subject)):
            logger.warning('''
    new = '''        if len(parts) >= 3 and parts[2] and parts[2] != sanitize_subject_name(str(subject)):
            logger.debug('''
    assert old in s
    NODES.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M5-哨兵降级debug", "TestSubjectScopeSentinel::test_mismatch_warns", m5))

def m6():
    """Codex round-1 BLOCKER-1 的门: expand 表名改回裸 vault_notes。"""
    s = NODES.read_text()
    old = 'table_name=client.resolve_table_name("canvas_nodes"),'
    new = 'table_name="vault_notes",  # M6 裸表旁路变异'
    assert old in s
    NODES.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M6-expand裸表旁路", "TestDualVaultIsolationOnTmpLanceDB::test_wikilink_neighbor_expansion_stays_in_vault", m6))

def m7():
    """空白 vault_id validator 失效 (Codex round-1 HIGH-2 的门)。"""
    s = RAG.read_text()
    old = '''        if not v or not v.strip():
            raise ValueError("vault_id 不能为空白")
        return v'''
    new = '''        return v'''
    assert old in s
    RAG.write_text(s.replace(old, new, 1))
MUTATIONS.append(("M7-空白validator失效", "TestVaultIdRequired::test_whitespace_only_vault_id_rejected_with_422", m7))

failed = []
for name, gate, fn in MUTATIONS:
    fn()
    rc, tail = run_gate(gate)
    restore_and_verify(name)
    if rc == 1:
        print(f"[{name}] ✓ 指定门变红 (exit=1)")
    elif rc == 0:
        failed.append(name)
        print(f"[{name}] ✗✗✗ STILL GREEN — 死门")
    else:
        failed.append(name)
        print(f"[{name}] ✗✗✗ exit={rc} 非 pytest 真失败 (usage/collection error): {tail}")

print()
if failed:
    print(f"FAILED MUTATIONS: {failed}")
    sys.exit(1)
print(f"ALL {len(MUTATIONS)} MUTATIONS KILLED THEIR GATES (exit=1 only) ✓")
