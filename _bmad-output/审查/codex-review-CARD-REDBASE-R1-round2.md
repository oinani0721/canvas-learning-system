增量结论：**M1 成立；M2 环境隔离整改成立，但“唯一路径证明”不成立；L1 成立。新增 2 条 LOW，未找到 BLOCKER/HIGH/MEDIUM。**

审查绑定 `HEAD=304f03cadaec165bb9c13dcb145b4f6aac0cf50c`，当前五文件 diff SHA-256：

```text
0a8ee996ac5efb74de16be74635669aba91ca4542f9d0aeb86a19d9b0b6b0d38
```

仓库保持只读；变异仅在进程内执行，测试临时目录已清理。

**M1：整改成立，未找到整改引入的新问题。**

a) 复跑同一类变异：真实构造函数执行后，把当前 vault 固化到 `_vault_id_override`。新门在[第二次断言 :81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:81)抓住它：

```text
current_test_unmutated=PASS
current_test_constructor_freeze_mutation=FAIL assertion_line=81
current_test_resolve_lru_cache_mutation=FAIL assertion_line=81
```

b) 把缓存移到 `resolve_table_name` 层，普通的 `(self, table_name)` 缓存也会被抓住，如上第三行。但**配置 getter 内的冻结仍检测不到**：给真实 [`get_current_vault_id()`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/config.py:1051)加缓存后，底层 settings 已改变，它仍返回旧值；测试内部的 patch 会替换掉这个变异 getter：

```text
upstream_getter_cache_mutation first=upstream_before second=upstream_before
current_test_with_upstream_getter_cache_mutation=PASS
```

这是该门的覆盖边界：它验证 client 跟随 getter 返回值变化，不能单独证明真实配置刷新链正确。未找到现行实现存在上述缓存缺陷。

c) **第二个 `with` 仍走 Level-3。** [token/reset :72–83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:72)包住两个块，reset 在第二次解析之后；实测原 ContextVar 未绑定、已绑定两种初态，均为同一 client、两次 `_vault_id_override=None`、两次 ContextVar=`general`，结束后均完整恢复。

**M2：环境整改成立；新增 LOW——路径证明表述过强。**

a) **全部输入已固定，未找到遗漏。** [`active_vault_aliases():124–131`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/core/vault_scope.py:124)只有三个输入：稳定 ID、`settings.ACTIVE_VAULT`、`settings.CANVAS_BASE_PATH`；[_pinned_settings :26–28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/regression/test_write_side_group_guard.py:26)固定后两项，测试同时 patch 稳定 ID。不存在第三个 settings 字段。分别将真实 `ACTIVE_VAULT`、目录 basename、两者同时设为 `some_other_vault`，直接运行两条仓内测试函数均 PASS。

b) **未找到 patch 意外影响。** 当前调用链仅别名扩展读取该 settings 替身；退出后还原检查原文：

```text
get_settings fields actually read=['ACTIVE_VAULT', 'ACTIVE_VAULT', 'CANVAS_BASE_PATH']
get_settings restored=True
config.settings identity unchanged=True
original get_settings cache_info unchanged=True
```

c) **“只有别名命中→归一”不成立。** 新数据确实排除了直接采用 `sanitize("CS 61B")` 的实现，但[测试 :74–76、:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/regression/test_write_side_group_guard.py:74)的路径证明过强：真实 resolver 的[双缺失分支 :191–202](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/core/vault_scope.py:191)也返回相同稳定 ID。

内存变异仅在两个参数同时提供时丢弃二者，再调用真实 resolver；两条门仍通过：

```text
test_explicit_vault_id_still_wins=PASS
mutant_source=active-vault
test_explicit_foreign_vault_id_raises_409=PASS
```

此项记 **LOW：新增说明超出断言能力**；未将变异当成现行生产缺陷。

**L1：三处整改均成立，未找到仍超出证据的表述。**

已核对 [LanceDB :99](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:99)、[metadata :317](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:317)、[resolver 测试 :400](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:400)：三处均准确区分 D16 与四段组合；[实施计划 :77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md:77)确实明列四段为 `Phase A0.5-N ship`，[实现 :201–205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/services/subject_resolver.py:201)也确实先构造 subject base，再追加 canvas。

另外两点：

1. **归属判定正确，未加重**：[yaml 用例及相邻缓存用例 :138–245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_vault_switch.py:138)与基线逐字节相同，本卡修改的用例在 finally 恢复环境并 reload。
2. **104 passed、ruff check 全过属实，但格式红点“与基线逐行相同”不成立，新增 LOW**：同版本 Ruff 对当前和基线内容逐行比较，发现 [_pinned_settings 前 :19–20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/regression/test_write_side_group_guard.py:19)新增一个空行差异；其余格式增删内容相同。

新增格式差异原文：

```diff
@@ -17,6 +17,7 @@
 # patch 注入, 不硬编码仓内 vault 字面量 (环境无关)。
 _PROBE_ACTIVE_VAULT = "probe_active_vault"
 
+
 # ⛔ Codex round-1 M2 整改: 只 patch get_current_vault_id **不够** ——
```

五文件实跑及 lint 输出：

```text
104 passed, 10 warnings in 1.06s
All checks passed!
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
```

BLOCKER/HIGH 清零: 是


