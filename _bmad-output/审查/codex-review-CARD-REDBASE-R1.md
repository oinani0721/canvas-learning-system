本轮发现 **2 条 MEDIUM、1 条 LOW；未找到 BLOCKER/HIGH**。12 条基线红均已复现，未找到其中有实现缺陷被此次断言改写掩盖；但新测试存在覆盖缩减和残留环境耦合，不能据“104 条全绿、函数数量未减”宣称完整通过。

审查绑定：`HEAD=304f03cadaec165bb9c13dcb145b4f6aac0cf50c`。最终测试 diff 的 SHA-256：

```text
82aa19f0581cab5f8edf562c5d5442a253014c3960cf0683489ae7b88b8fe2db
```

仅做读取与临时进程复现，未修改仓库。指定五文件合跑，以及从 Git 在内存载入基线测试的结果分别为：

```text
104 passed, 10 warnings in 1.13s
12 failed, 91 passed, 10 warnings in 1.75s
```

两次均输出：

```text
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
```

**1. 实现缺陷是否被当成过时测试掩盖：PASS，未找到。但新门的覆盖保持检查 FAIL。**

12 条逐条核对如下。“归因 PASS”仅判断旧红原因，不表示改写后的覆盖完整。

| 用例 | 旧红归因及新断言鉴别力 | 裁定 |
|---|---|---|
| LanceDB `test_dynamic_vault_id_follows_config` | yaml 优先级使旧配置方式失效；新版只检验构造后的单次配置取值 | 归因 PASS；覆盖 FAIL，见 M1 |
| LanceDB `test_group_id_has_vault_prefix` | 旧裸前缀过时；新测独立注入 vault，并验证完整四段及 canvas 归一化 | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:94) |
| LanceDB `test_active_vault_id_level2_runtime_error_falls_through` | 旧 Level-3 设置受 yaml 覆盖；新测仍真实触发 Level-2 RuntimeError，再验证 Level-3 结果 | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:369) |
| write guard `test_missing_vault_and_group_derives_current_vault` | 旧 `.called` 针对已移除调用链；新测独立验证 active vault 组和非 default | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/regression/test_write_side_group_guard.py:44) |
| write guard `test_explicit_vault_id_still_wins` | 原跨 vault 直接采用已被 409 契约取代；新测验证显式参数胜过不同 legacy 值 | PASS，替代测试有 M2 |
| metadata `test_metadata_group_id_format` | 旧裸格式过时；新测仍验证完整返回格式，vault 选择存在同源盲区 | PASS，有边界，见第 2 项 |
| resolver `test_manual_override_highest_priority` | group_id 的 subject 已要求归一化；原始 subject/category/source 断言仍保留 | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:93) |
| resolver `test_manual_subject_alone_defaults_category_to_subject` | Story 1.9 有意改变 manual 条件，详见下文 | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:121) |
| resolver `test_group_id_format_config` | 独立哨兵＋已知 config subject/canvas | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:405) |
| resolver `test_group_id_format_manual` | 独立哨兵＋请求中的 manual subject/canvas | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:411) |
| resolver `test_group_id_format_default` | 独立哨兵＋已知默认 subject/canvas | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:421) |
| vault switch `test_vault_id_changes_after_reload` | 无 yaml 临时目录使测试确实进入 ACTIVE_VAULT fallback，检查真实 reload/accessor | PASS，[证据](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_vault_switch.py:269) |

**M1 — MEDIUM：LanceDB 动态切换覆盖被削弱。**

新版在 [test_lancedb_vault_isolation.py:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:67) 先 patch、再创建 client，只取一次表名；旧版先创建 client、再切配置。

我在进程内临时包装真实 `LanceDBClient.__init__`，令其构造时将当前 vault 冻结到 `_vault_id_override`，并排除旧测试的 yaml 干扰。原文结果：

```text
unmutated_same_client_after_switch=after_switch_vault_notes
baseline_test_with_constructor_freeze_mutation=FAIL
new_test_with_constructor_freeze_mutation=PASS
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
```

因此“AC #3 原意图不变”不成立。当前实现仍在 [lancedb_client.py:744](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/lib/agentic_rag/clients/lancedb_client.py:744) 动态读取，问题是新门放过了构造时冻结的回归。应让**同一个 client** 在 getter 返回 A、B 时各解析一次并验证变化。

**manual_subject alone 的裁定：有意演进。**

归档 [Story 1.9:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/_bmad-archive/legacy-stories/1-9-multi-subject-kg-isolation.md:22) 允许用户手动指定学科，`:119` 描述仅选择学科的下拉操作，`:145` 要求 resolver 手动优先。

`git show 9f554748 -- backend/app/services/subject_resolver.py`，2026-03-18 的原文：

```diff
-        if manual_subject and manual_category:
+        # Story 1.9: Accept manual_subject alone (category defaults to subject)
+        if manual_subject:
+            category = manual_category or manual_subject
```

旧测试则来自 `8222daef`，2026-02-11。因此 [subject_resolver.py:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/services/subject_resolver.py:169) 的 “both” 是未同步注释。**Story 逐字规定 `category=subject` 的文本未找到**；该具体默认方式的证据是历史实施决定。

**L1 — LOW：四段格式的出处表述过宽。**

新注释把根 CLAUDE 的格式转写成两个独立可选段，例如 [test_subject_resolver.py:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_subject_resolver.py:397)。但根 [CLAUDE.md:33](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/CLAUDE.md:33) 只列二段、三段；[构造器:222](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/core/subject_config.py:222) 明确 subject/canvas 互斥。

四段格式本身有独立依据：[2026-05-10 实施计划:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/_bmad-output/research/round-23-multi-vault-implementation-plan-2026-05-10.md:77) 明列其为 `Phase A0.5-N ship`，`ecf16f2c` 也明确实施该组合。应准确引用为 **D16 前缀＋Phase A0.5-N 四段组合**。

**2. 动态组装与 metadata 自证程度：字面量检查 PASS；metadata 的 vault 正确性独立验证 FAIL。**

完整 diff 检索 `canvas_vault`，原文仅两处，均为删除行：

```text
52:-        return_value="vault:canvas_vault",
82:-    assert derived == "vault:canvas_vault"
```

新增的七处 `f"vault:..."` 来源全部可追：

| 位置 | vault 段来源 |
|---|---|
| write guard `:46` | patch 注入 `_PROBE_ACTIVE_VAULT` |
| LanceDB `:99、:102` | patch 注入 `switched_vault` |
| resolver `:409、:419、:425` | patch 注入 `_PROBE_VAULT` |
| metadata `:329` | 真实 `get_current_vault_id()` 返回值 |

前三类是受控测试输入，不是仓内 vault 的变相硬编码。

[metadata 测试:322](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:322) 与 resolver [实现:188](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/services/subject_resolver.py:188) 确实读取同一 getter。若 getter 稳定返回一个**错误但已归一化**的 ID，两侧会一致出错并通过。

但整条门并非恒真：它仍能发现缺少 `vault:`、subject/canvas 错误、额外或遗漏分段，以及端点错误返回 group_id。它验证的是格式与传递一致性，不能独立证明选中了正确 vault。

**3. patch 点：可达性 PASS；未发现过宽替换，但隔离完整性 FAIL。**

实际绑定路径：

- resolver：每次 `resolve()` 在 `subject_resolver.py:188` 延迟 import。
- LanceDB：每次属性读取在 `lancedb_client.py:744` 延迟 import。
- write guard：`memory.py:69` 导出包装函数，经 `vault_scope.py:224`，在 `:157` 延迟 import；别名函数在 `:122` 再次延迟 import。

新 patch 没有替换 builder、resolver 或预期值组装逻辑。问题在于下面这处输入没有完全隔离。

**M2 — MEDIUM：新增 409 用例仍受真实别名环境影响。**

[test_write_side_group_guard.py:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/regression/test_write_side_group_guard.py:76) 只固定稳定 ID 为 `cs_61b`；[vault_scope.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/core/vault_scope.py:124) 仍读取真实 `ACTIVE_VAULT` 和挂载目录 basename。因此 `some_other_vault` 不保证是 foreign。

在 `LANE/backend` 直接复现：

```sh
ACTIVE_VAULT=some_other_vault PYTHONDONTWRITEBYTECODE=1 \
.venv/bin/pytest -q -p no:cacheprovider \
tests/regression/test_write_side_group_guard.py::test_explicit_foreign_vault_id_raises_409
```

关键输出原文：

```text
tests/regression/test_write_side_group_guard.py:77: in test_explicit_foreign_vault_id_raises_409
    with pytest.raises(HTTPException) as exc_info:
E   Failed: DID NOT RAISE <class 'fastapi.exceptions.HTTPException'>
```

当前实现按合法别名放行是正确行为，误红来自新测试。应固定完整 settings 输入，使请求值确定不在别名集合内。

**4. 三处新增状态恢复：PASS，未找到新增污染。**

- regression fixture [`:24–28`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/regression/test_write_side_group_guard.py:24) 和 LanceDB [`:65–71`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_lancedb_vault_isolation.py:65)：token/reset 恢复原值，也恢复“原本未绑定”状态。同步路径实探覆盖这两种初态，均恢复成功。
- vault switch [`:272–287`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/tests/unit/test_vault_switch.py:272)：先恢复两项 env，再 reload；[config.py:1064](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/backend/app/config.py:1064) 重建缓存、`config.settings` 和 `DEFAULT_GROUP_ID`。成功与断言异常路径的恢复探针均通过。

这不代表整个旧文件无污染：相邻 yaml 测试 `test_vault_switch.py:145–232` teardown 只还原 env。执行 `test_invalid_yaml_silently_falls_back` → `test_cache_clear_picks_up_new_value` 时，后者可在 `:239` 读到缓存中的 `broken-fallback`，再于 `:245` 写回 env。**此问题基线已有，不能归责于本卡。**

**5. 改写与替代：5a PASS；5b 契约替代 PASS、环境独立性 FAIL；5c PASS。**

- **5a：** 新显式优先用例同时提供 `CS 61B` 和不同的 `vault:some_other_group`；若错误采用 legacy，断言会失败，有非退化鉴别力。但它不能证明“与稳定 ID 不同的目录别名归一化”，因为 `CS 61B` sanitize 后已等于 `cs_61b`。
- **5b：** 跨 vault 请求的现行结果确为 409，有独立 [CARD-G2-2 任务书:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z4-redbase/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-第五批开跑手册-8车道13卡.md:47) 支持。旧触发场景已用新预期替代，但 M2 使这个替代门尚不稳健。该用例调用的是 `memory.py` 导出的 helper，不能扩称为完整 HTTP 写入及副作用验证。
- **5c：** `test_explicit_vault_id_still_wins` 与当前“显式参数优先于 legacy”的断言相符，未找到 DD-13 违规；不过“原意图不变”不精确，旧测试没有传 legacy。

**6. 主张 B / C 命令核对。**

**B：PASS。** 指定命令：

```sh
git diff --name-only 304f03ca -- . ':(exclude)_bmad-output'
```

stdout 原文：

```text
backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py
backend/tests/regression/test_write_side_group_guard.py
backend/tests/unit/test_lancedb_vault_isolation.py
backend/tests/unit/test_subject_resolver.py
backend/tests/unit/test_vault_switch.py
```

**C：数量非减 PASS；“六文件” FAIL，实际仅五个，第六个未找到；覆盖非减 FAIL。**

对各文件基线内容和当前文件分别执行 `grep -c 'def test_'`，结果原文：

```text
file | baseline | current
backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py | 21 | 21
backend/tests/regression/test_write_side_group_guard.py | 4 | 5
backend/tests/unit/test_lancedb_vault_isolation.py | 15 | 15
backend/tests/unit/test_subject_resolver.py | 39 | 39
backend/tests/unit/test_vault_switch.py | 26 | 26
```

未发现直接删掉测试函数，但 **M1 已证明函数数量不减仍可丢失原有鉴别力**。

BLOCKER/HIGH 清零: 是


