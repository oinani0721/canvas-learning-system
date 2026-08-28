#!/usr/bin/env python3
"""G2-3 变异负控: 把每处修复改坏, 确认对应门必红 (防假绿).

用法 (需 7692 测试容器在跑):
    cd backend && .venv/bin/python scripts/g23_mutation_negative_controls.py

每条变异会**临时**改写源文件、跑对应门、再原样还原 (finally 保证),
最后复跑基线确认还原干净。exit 0 = 全部变异都被抓; exit 1 = 有假绿。
"""

import pathlib
import re
import subprocess
import sys

#: 相对本脚本定位 backend 根 — 合并到主仓/其他 worktree 后仍可运行
BACKEND = pathlib.Path(__file__).resolve().parents[1]
PYTEST = str(BACKEND / ".venv/bin/pytest")

CLIENT = BACKEND / "app/clients/neo4j_client.py"
MIGRATE = BACKEND / "scripts/migrate_write_identity_g23.py"
FALLBACK = BACKEND / "app/services/fallback_sync_service.py"

GATE = "tests/integration/test_cypher_contract_gate.py"
MIG_GATE = "tests/integration/test_migrate_write_identity_g23.py"
UNIT = "tests/unit/test_neo4j_client.py"


def mut_single_key(s: str) -> str:
    """M1: create_learning_relationship 退回单键 + 事后 SET 归属."""
    old = (
        "MERGE (c:Concept {name: $concept, group_id: $groupId})\n"
        "        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)"
    )
    new = "MERGE (c:Concept {name: $concept})\n        SET c.group_id = $groupId\n        MERGE (u)-[r:LEARNED]->(c)"
    assert old in s
    return s.replace(old, new, 1)


def mut_delete_unscoped(s: str) -> str:
    """M2: 删边 fail-closed 换成静默 DEFAULT 降级 (契约禁止的最坏回归)."""
    old = (
        "            logger.error(\n"
        '                "[G2-3 W2 fail-closed] delete_edge_relationship refused: "\n'
        '                "unresolved group_id (edge_id=%s) — unscoped delete forbidden",\n'
        "                edge_id,\n"
        "            )\n"
        "            return False"
    )
    assert old in s
    return s.replace(old, '            physical_group_id = "vault__default"', 1)


def mut_assoc_downgrade(s: str) -> str:
    """M5: 关联 update/delete 的 fail-closed 换成静默 DEFAULT 降级."""
    out = s
    for op, tag in (("update_canvas_association", "W5"), ("delete_canvas_association", "W2")):
        old = (
            f"            logger.error(\n"
            f'                "[G2-3 {tag} fail-closed] {op} refused: unresolved group_id (association_id=%s)",\n'
            f"                association_id,\n"
            f"            )\n"
            f"            return False"
        )
        assert old in out, op
        out = out.replace(old, '            physical_group_id = "vault__default"', 1)
    return out


def mut_ctxvar_branch(s: str) -> str:
    """M6: 解析链 ContextVar 正向分支坏掉."""
    old = "        ctx_value = get_current_subject_id()\n"
    assert old in s
    return s.replace(old, "        ctx_value = None\n", 1)


def mut_canvas_path_branch(s: str) -> str:
    """M7: 解析链 canvas_path 推导分支坏掉."""
    old = "        elif canvas_path:\n            subject = extract_subject_from_canvas_path(canvas_path)"
    assert old in s
    return s.replace(old, "        elif False:\n            subject = extract_subject_from_canvas_path(canvas_path)", 1)


def mut_migrate_no_lww(s: str) -> str:
    """M3: 迁移器 split 退回无条件 `SET r2 += properties(r)` (无 LWW/无聚合)."""
    pattern = re.compile(r"_APPLY_SPLIT = \(.*?\n\)\n", re.S)
    replacement = (
        "_APPLY_SPLIT = (\n"
        '    "MATCH (u:User)-[r:LEARNED {group_id: $gid}]->(c:Concept {name: $name}) "\n'
        "    \"WHERE coalesce(c.group_id, '') <> $gid \"\n"
        '    "MERGE (c2:Concept {name: $name, group_id: $gid}) "\n'
        '    "MERGE (u)-[r2:LEARNED {group_id: $gid}]->(c2) "\n'
        '    "SET r2 += properties(r) "\n'
        '    "DELETE r "\n'
        '    "RETURN count(r2) AS identities, count(r2) AS moved, '
        'count(r2) AS applied_source, 0 AS kept_target"\n'
        ")\n"
    )
    out, n = pattern.subn(replacement, s, count=1)
    assert n == 1, "M3 pattern miss"
    return out


def mut_migrate_no_dedup(s: str) -> str:
    """M4: 无组边回填退回裸 SET (无聚合/无去重 → 造重复同身份边)."""
    pattern = re.compile(r"_APPLY_NULL_EDGE_BACKFILL = \(.*?\n\)\n", re.S)
    replacement = (
        "_APPLY_NULL_EDGE_BACKFILL = (\n"
        '    "MATCH ()-[r:LEARNED]->(c:Concept {name: $name, group_id: $gid}) "\n'
        '    "WHERE r.group_id IS NULL "\n'
        '    "SET r.group_id = $gid "\n'
        '    "RETURN count(r) AS identities, count(r) AS backfilled, '
        'count(r) AS applied_source"\n'
        ")\n"
    )
    out, n = pattern.subn(replacement, s, count=1)
    assert n == 1, "M4 pattern miss"
    return out


def mut_migrate_no_identity_dedupe(s: str) -> str:
    """M13: 去掉同身份重复边收敛 pass (重复边永久留存)."""
    old = '        for item in plan["pending"].get("duplicate_identity_edges", []):'
    assert old in s
    return s.replace(old, "        for item in []:  # mutated: dedupe pass disabled", 1)


def mut_fallback_single_key(s: str) -> str:
    """M8: fallback replay (scoring) 退回单键 + 事后 SET."""
    old = (
        "        MERGE (c:Concept {name: $concept, group_id: $groupId})\n"
        "        MERGE (u)-[r:LEARNED {group_id: $groupId}]->(c)\n"
        "        WITH r,\n"
    )
    assert s.count(old) == 2, s.count(old)
    new = (
        "        MERGE (c:Concept {name: $concept})\n"
        "        SET c.group_id = $groupId\n"
        "        MERGE (u)-[r:LEARNED]->(c)\n"
        "        WITH r,\n"
    )
    return s.replace(old, new, 1)  # 只坏第一个 (scoring replay)


def mut_migrate_port_substring(s: str) -> str:
    """M9: 现网拒绝退回子串启发式."""
    old = "        parsed = urlsplit(uri)\n        port = parsed.port"
    assert old in s
    return s.replace(old, '        return ":7691" in uri\n        port = None', 1)


def mut_drop_degenerate_validation(s: str) -> str:
    """M10: 去掉退化输入的输入/输出双向校验 (空白串会静默降级 DEFAULT)."""
    old = "    resolved = group_id.strip() if isinstance(group_id, str) else group_id"
    assert old in s
    out = s.replace(old, "    resolved = group_id", 1)
    old2 = "    if not _is_valid_physical_group_id(physical):"
    assert old2 in out
    return out.replace(old2, "    if False:", 1)


def mut_drop_identity_gate(s: str) -> str:
    """M11: 去掉库身份闸 (只留端口闸 → 端口转发可绕过)."""
    old = '    known_live = os.getenv("NEO4J_LIVE_STORE_ID", KNOWN_LIVE_STORE_IDENTITY)'
    assert old in s
    return s.replace(old, "    known_live = None  # mutated: identity gate disabled", 1)


def mut_blank_group_is_valid(s: str) -> str:
    """M12: 空串组视为合法身份 (退回 IS NOT NULL 口径)."""
    old = "_NO_GROUP = \"coalesce(trim({alias}.group_id), '') = ''\""
    assert old in s
    out = s.replace(old, '_NO_GROUP = "{alias}.group_id IS NULL"', 1)
    old2 = "_HAS_GROUP = \"coalesce(trim({alias}.group_id), '') <> ''\""
    assert old2 in out
    return out.replace(old2, '_HAS_GROUP = "{alias}.group_id IS NOT NULL"', 1)


def mut_drop_blank_explicit_guard(s: str) -> str:
    """M14: 去掉"显式空白不回退"守卫 (空白会静默落到 ContextVar 的 vault)."""
    old = "    if isinstance(group_id, str) and not group_id.strip():"
    assert old in s
    return s.replace(old, "    if False:", 1)


def mut_drop_segment_validation(s: str) -> str:
    """M15: 去掉物理值段级校验 (vault____x 空段可通过)."""
    old = '    return all(seg for seg in suffix.split("__"))'
    assert old in s
    return s.replace(old, "    return True", 1)


def mut_partial_property_migration(s: str) -> str:
    """M16: 迁移只搬四个白名单字段 (其余 LEARNED 属性丢失)."""
    old = '    "SET r2 += CASE WHEN take_source THEN properties(best) ELSE {} END, "\n    "    r2.group_id = $gid "'
    assert s.count(old) >= 1
    new = (
        '    "SET r2.score = CASE WHEN take_source THEN best.score ELSE r2.score END, "\n'
        '    "    r2.timestamp = CASE WHEN take_source THEN best.timestamp ELSE r2.timestamp END "'
    )
    return s.replace(old, new)


def mut_hardcode_read_enforced(s: str) -> str:
    """M17: 拒写探针退化成硬编码 (证据变回断言).

    变异点打在**探针函数本身**: 调用点写死 True 与真实探针在"READ 确实
    拒写"的库上黑盒不可区分 (两者都得 True) —— 可强制的那条线是"探针
    函数必须真的测量", 由 test_read_access_probe_actually_measures 锁死
    (它在 WRITE 会话里要求返回 False)。
    """
    old = '    """实测 READ 模式会话是否被服务端拒写'
    assert old in s
    return s.replace(old, '    return True  # mutated: hardcoded\n    """实测 READ 模式会话是否被服务端拒写', 1)


def mut_drop_duplicate_node_pending(s: str) -> str:
    """M18: 逻辑重复概念节点不计入 manual (工具会在有重复时报 OK)."""
    old = "    manual_total = len(manual) + len(dup_nodes)"
    assert old in s
    return s.replace(old, "    manual_total = len(manual)", 1)


def mut_empty_string_falls_through(s: str) -> str:
    """M19: 空串 group_id 漏回推导链 (与空白串口径分裂)."""
    old = "    if isinstance(group_id, str) and not group_id.strip():"
    assert old in s
    return s.replace(old, "    if isinstance(group_id, str) and group_id and not group_id.strip():", 1)


def mut_probe_any_error_is_enforced(s: str) -> str:
    """M20: 探针把任意异常当拒写 (连接抖动可伪造零写入结论)."""
    old = '        if getattr(exc, "code", None) == _ACCESS_MODE_ERROR_CODE:\n            return True\n        return None'
    assert old in s
    return s.replace(old, "        return True", 1)


def mut_integrity_failure_ignored(s: str) -> str:
    """M21: 零写入结论为假不影响退出码 (自证失败还报成功)."""
    old = '        success = plan["pending"]["total"] == 0 and (args.apply or integrity_ok)'
    assert old in s
    return s.replace(old, '        success = plan["pending"]["total"] == 0', 1)


def mut_no_duplicate_skip(s: str) -> str:
    """M22: 逻辑重复身份不跳过自动 apply (MERGE 会多匹配扇出写入)."""
    old = "        if (name, gid) in dup_identities:"
    assert old in s
    return s.replace(old, "        if False:", 1)


def mut_bind_unstripped_gid(s: str) -> str:
    """M23: 去掉"带空白 group_id 跳过"守卫 (脏组进身份键或静默空转)."""
    old = "        if raw_gid != raw_gid.strip():"
    assert old in s
    return s.replace(old, "        if False:", 1)


def mut_probe_text_fallback(s: str) -> str:
    """M24: 探针退回"异常文本含 read access mode 也算拒写" (可被伪装)."""
    old = '        if getattr(exc, "code", None) == _ACCESS_MODE_ERROR_CODE:'
    assert old in s
    new = '        if getattr(exc, "code", None) == _ACCESS_MODE_ERROR_CODE or "read access mode" in str(exc).lower():'
    return s.replace(old, new, 1)


def mut_uri_counts_as_authorization(s: str) -> str:
    """M25: 任意非默认 live-uri 又算"授权表态" (等于没有门)."""
    old = '        supplied_fingerprint = bool(os.getenv("NEO4J_LIVE_STORE_ID"))'
    assert old in s
    new = '        supplied_fingerprint = bool(os.getenv("NEO4J_LIVE_STORE_ID")) or live_uri != DEFAULT_LIVE_URI'
    return s.replace(old, new, 1)


MUTATIONS = [
    ("M24 探针退回文本匹配", MIGRATE, mut_probe_text_fallback, [MIG_GATE]),
    ("M25 不可达 URI 当授权", MIGRATE, mut_uri_counts_as_authorization, [MIG_GATE]),
    ("M19 空串漏回推导链", CLIENT, mut_empty_string_falls_through, [UNIT]),
    ("M20 探针任意异常当拒写", MIGRATE, mut_probe_any_error_is_enforced, [MIG_GATE]),
    ("M21 零写入失败不影响退出码", MIGRATE, mut_integrity_failure_ignored, [MIG_GATE]),
    ("M22 逻辑重复不跳过 apply", MIGRATE, mut_no_duplicate_skip, [MIG_GATE]),
    ("M23 去掉脏组跳过守卫", MIGRATE, mut_bind_unstripped_gid, [MIG_GATE]),
    ("M14 去掉显式空白守卫", CLIENT, mut_drop_blank_explicit_guard, [UNIT]),
    ("M15 去掉物理值段级校验", CLIENT, mut_drop_segment_validation, [UNIT]),
    ("M16 迁移只搬白名单字段", MIGRATE, mut_partial_property_migration, [MIG_GATE]),
    ("M17 拒写探针改硬编码", MIGRATE, mut_hardcode_read_enforced, [MIG_GATE]),
    ("M18 逻辑重复不计 manual", MIGRATE, mut_drop_duplicate_node_pending, [MIG_GATE]),
    ("M13 去掉同身份重复边收敛", MIGRATE, mut_migrate_no_identity_dedupe, [MIG_GATE]),
    ("M11 去掉库身份闸", MIGRATE, mut_drop_identity_gate, [MIG_GATE]),
    ("M12 空串组当合法身份", MIGRATE, mut_blank_group_is_valid, [MIG_GATE]),
    ("M10 去掉退化输入校验", CLIENT, mut_drop_degenerate_validation, [UNIT]),
    ("M1 concept 写身份退回单键+SET", CLIENT, mut_single_key, [GATE]),
    ("M2 删边 fail-closed 降级 DEFAULT", CLIENT, mut_delete_unscoped, [GATE]),
    ("M3 迁移器去掉 LWW 守卫", MIGRATE, mut_migrate_no_lww, [MIG_GATE]),
    ("M4 迁移器去掉去重守卫", MIGRATE, mut_migrate_no_dedup, [MIG_GATE]),
    ("M5 关联 update/delete 降级 DEFAULT", CLIENT, mut_assoc_downgrade, [UNIT, GATE]),
    ("M6 解析链 ContextVar 分支坏", CLIENT, mut_ctxvar_branch, [GATE]),
    ("M7 解析链 canvas_path 分支坏", CLIENT, mut_canvas_path_branch, [GATE]),
    ("M8 fallback scoring replay 退回单键", FALLBACK, mut_fallback_single_key, [GATE]),
    ("M9 现网拒绝退回子串匹配", MIGRATE, mut_migrate_port_substring, [MIG_GATE]),
]


def run_tests(selectors):
    r = subprocess.run(
        [PYTEST, *selectors, "-q", "-x", "--no-header", "-p", "no:cacheprovider"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0


def main() -> int:
    # 基线必须全绿
    if not run_tests([GATE, MIG_GATE, UNIT]):
        print("BASELINE RED — 变异负控无意义, 先修基线")
        return 1
    print("baseline: GREEN")

    failures = []
    for name, path, mutate, selectors in MUTATIONS:
        original = path.read_text()
        try:
            path.write_text(mutate(original))
        except AssertionError as e:
            print(f"MUT-SKIP     {name}: 变异锚点失配 ({e})")
            path.write_text(original)
            failures.append(name)
            continue
        try:
            green = run_tests(selectors)
        finally:
            path.write_text(original)
        if green:
            print(f"MUT-FAIL(假绿) {name}")
            failures.append(name)
        else:
            print(f"MUT-OK(能红)   {name}")

    # 复原后必须仍全绿
    if not run_tests([GATE, MIG_GATE, UNIT]):
        print("RESTORE RED — 变异未干净复原!")
        return 1
    print("restored: GREEN")
    print(f"\n结果: {len(MUTATIONS) - len(failures)}/{len(MUTATIONS)} 变异被抓")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
