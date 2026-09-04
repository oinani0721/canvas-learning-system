# UAT — CARD-REDBASE-R1「主干既有红一次清账」

> 批次 `[BATCH-2026-09-05-第十一批 / CARD-REDBASE-R1]`
> 车道 `card/z4-redbase`（从主干 `304f03ca` 切）
> 卡文 `_bmad-output/implementation-artifacts/goal-cards/第十一批-goals/Z4-A.md`
> 审查面 = `git diff 304f03ca -- backend/tests/`（5 个测试文件，零实现改动）

---

## 4-B 用户可感（先看这段）

**这次改了什么，对你意味着什么：无变化。**

把几条早就过期、每次跑测试都误报的旧检查，改成按现在的规则检查。

具体点说：这些检查是一两年前写的，当时系统给学习记录打的"归属标签"长这样
`math54:线性代数`；后来（2026-05-05）标签格式统一加了 `vault:` 前缀，变成
`vault:canvas_vault:math54:线性代数`，好让不同 vault 的数据不会混在一起。
代码早就改完并且一直在正确工作，只有这几条**检查**忘了跟着改，于是每次跑
测试它们都举手说"不对"——而实际上不对的是它们自己。

另有几条检查想验证"切换 vault 后系统会跟着切"，但它们切 vault 的方式
（改环境变量）在 2026 年某次改动后就失效了：现在 vault 名优先从 vault 目录里的
`.canvas-config.yaml` 读，环境变量只是兜底。所以这些检查其实一直在测"仓库里的
那个配置文件"，而不是在测系统行为。

**产品行为一行没改。你不需要做任何事。**

价值在于：这批噪音清掉之后，下一批卡再跑整目录测试时，红的就是真的红。

---

## 4-A 技术验收

### 一 先红存证（卡文 (a)）

改动前在 `304f03ca` 车道树实测，命令：

```
cd backend && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/pytest -q -p no:cacheprovider \
  tests/unit/test_lancedb_vault_isolation.py tests/regression/test_write_side_group_guard.py \
  tests/api/v1/endpoints/test_metadata_subject_mapping.py tests/unit/test_subject_resolver.py \
  tests/unit/test_vault_switch.py
→ 12 failed, 91 passed, 10 warnings in 1.11s
```

⚠️ **实测 12 条，卡文 §〇 登记 10 条**——多出的 2 条见 §二偏差登记。

| # | 用例（file:line） | 期望（旧断言） | 实得（现实现） | 根因 |
|---|---|---|---|---|
| 1 | `test_lancedb_vault_isolation.py:55` `test_dynamic_vault_id_follows_config` | `cs_61b_vault_notes` | `canvas_vault_vault_notes` | 环境耦合 |
| 2 | `test_lancedb_vault_isolation.py:72` `test_group_id_has_vault_prefix` | `.startswith("cs61b:")` → True | `'vault:canvas_vault:math:test_canvas'.startswith('cs61b:')` = False | 环境耦合 + D16 格式 |
| 3 | `test_lancedb_vault_isolation.py:345` `test_active_vault_id_level2_runtime_error_falls_through` | `level3_target` | `canvas_vault` | 环境耦合 |
| 4 | `test_write_side_group_guard.py:21` `test_missing_vault_and_group_derives_current_vault` | `mock_derive.called` = True | `<MagicMock …>.called` = False | G2-2 契约收敛 |
| 5 | `test_write_side_group_guard.py:27` `test_explicit_vault_id_still_wins` | `vault:cs_61b` | `HTTPException 409: vault 未激活: cs_61b (当前挂载: canvas_vault)` | G2-2 契约收敛 |
| 6 | `test_metadata_subject_mapping.py:315` `test_metadata_group_id_format` | `math54:线性代数` | `vault:canvas_vault:math54:线性代数` | D16 格式 |
| 7 | `test_subject_resolver.py:89` `test_manual_override_highest_priority` | `"custom-subject" in group_id` | `'vault:canvas_vault:custom_subject:离散数学'`（连字符被 sanitize 成下划线） | D16 格式 ⚠️卡文未登记 |
| 8 | `test_subject_resolver.py:118` `test_manual_requires_both_subject_and_category` | `source != MANUAL` | `MetadataSource.MANUAL` | **Story 1.9 契约演进** ⚠️卡文未登记，第四类根因 |
| 9 | `test_subject_resolver.py:380` `test_group_id_format_config` | `math54:离散数学` | `vault:canvas_vault:math54:离散数学` | D16 格式 |
| 10 | `test_subject_resolver.py:389` `test_group_id_format_manual` | `custom:path` | `vault:canvas_vault:custom:path` | D16 格式 |
| 11 | `test_subject_resolver.py:394` `test_group_id_format_default` | `general:random` | `vault:canvas_vault:general:random` | D16 格式 |
| 12 | `test_vault_switch.py:253` `test_vault_id_changes_after_reload` | `cs_61b` | `canvas_vault` | 环境耦合 |

原始输出：`scratchpad/baseline-red.txt`（会话临时目录，未入库）。

### 二 偏差登记（卡文前提与实测不符，如实不擅改）

**偏差 1 — 条数：卡文 10 条，实测 12 条。**
`test_subject_resolver.py` 实际红 5 条（卡文只登记 `:380/:388/:394` 三条），
多出 `:89 test_manual_override_highest_priority` 与
`:118 test_manual_requires_both_subject_and_category`。前者同 D16 根因（台账/卡文漏登），
后者是**卡文完全没有的第四类根因**。

**偏差 2 — 第四类根因：Story 1.9 契约演进（非格式、非环境、非 G2-2）。**
`test_manual_requires_both_subject_and_category` 断言「只给 `manual_subject` 不给
`manual_category` → 不走 manual 分支」。而 `app/services/subject_resolver.py:207-210`
现行代码写着：

```python
# 1. Manual override (highest priority)
# Story 1.9: Accept manual_subject alone (category defaults to subject)
if manual_subject:
    category = manual_category or manual_subject
```

即实现已在 Story 1.9 主动改成「接受单独 manual_subject，category 缺省取 subject」。
这条红同样是「测试过时、零实现回归」，但根因类别与卡文列的三类都不同。
处置：改断言到实际契约，并按 DD-13 名实一致把函数名改为
`test_manual_subject_alone_defaults_category_to_subject`（**改名不是删除**，计数不减，见 §五）。

**偏差 3 — 裁判 7 的前提不成立（重大）。**
卡文裁判 7 写「门下 `tests/unit tests/api tests/regression` 既有红 = 0（本卡对下批目录级裁判的交付物）」。
实测**远不止本卡这 12 条**——详见 §六。本卡无法交付「目录级既有红 = 0」，只能交付
「**本卡定性的这 12 条**清零，且本卡零引入」。这不是本卡范围内可解决的问题，登记移交。

### 三 逐条改法与依据（卡文 (b)(c)(d)(e)）

| # | 改法 | 卡文条款 |
|---|---|---|
| 1 | 去 `reload_settings`，改 `patch("app.config.get_current_vault_id")`；ContextVar 先置 `DEFAULT_SUBJECT_ID` 使解析落到 Level-3。**Codex M1 整改后**：复用同一个 client，在 `vault_before_switch` / `vault_after_switch` 两次 patch 下各解析一次，要求表名跟着变（保住旧版「先建 client 再切配置」的鉴别力） | (b) |
| 2 | 同上 patch；期望改 D16 `f"vault:{switched_vault}:math:test_canvas"`（vault 段来自 patch 返回值） | (b)(c) |
| 3 | 同上 patch 取代 `reload_settings`，其余（`sys.modules` 替换、窄 except 语义）一字未动 | (b) |
| 4 | 不再断言 `default_vault_group_id` 被调用（该函数已被 G2-2 取代），改断言**行为**：`resolve_vault_group_id(None, None) == f"vault:{patched}"` 且 `!= "vault:default"`（契约 3 语义保留） | (d) |
| 5 | 拆成两条：保留 `test_explicit_vault_id_still_wins`（改证「显式 vault_id 优先于 legacy_group_id」）+ 新增 `test_explicit_foreign_vault_id_raises_409`（`pytest.raises(HTTPException)` + `status_code == 409`）。**Codex M2/5a 整改后**：两条都用 `_pinned_settings()` 固定别名集输入；稳定 ID 设为 `cs61b_stable` ≠ 目录名 `CS 61B`，使「别名命中 → 归一到稳定 ID」成为唯一能满足断言的路径 | (d) |
| 6 | 期望改 `f"vault:{get_current_vault_id()}:math54:线性代数"` | (c) |
| 7 | 断言改 `":custom_subject:" in result.group_id`（归一化后形态） | (c) |
| 8 | 改断言到 Story 1.9 实际契约 + 函数改名（见 §二偏差 2） | — |
| 9-11 | 三条期望改 `f"vault:{_PROBE_VAULT}:<subject>:<canvas>"`，vault 段用模块级哨兵 `_PROBE_VAULT = "probe_vault_id"` 经 patch 注入 | (c) |
| 12 | `monkeypatch` 换成手工 try/finally：`reload_settings({"CANVAS_BASE_PATH": tmp_path/无 yaml, "ACTIVE_VAULT": "CS 61B"})` → 断言 `get_current_vault_id() == "cs_61b"`；finally 还原 env 后再 `reload_settings()` 重建缓存 | (e) |

每条改动的 docstring 都保留了原意图并加了「CARD-REDBASE-R1 翻新 + 改法依据」段。

**关于 (c) 的「禁硬编码 canvas_vault」**：diff 内 `canvas_vault` 字面量出现次数 = 0（§五 有 grep 证据）。
9-11 三条特意用**独立哨兵值** `_PROBE_VAULT` 而不是 `get_current_vault_id()`，
避免「期望值与被测实现同源」的自证；第 6 条（TestClient 走真实端点）无法注入哨兵，
用了 `get_current_vault_id()`，该条的鉴别力仅覆盖**格式**不覆盖**vault 取值正确性**，
如实登记（vault 取值由第 2 条以 patch 哨兵覆盖）。

### 四 裁判命令逐条

| # | 裁判 | 结果 |
|---|---|---|
| 1 | `pytest -q -p no:cacheprovider tests/unit/test_lancedb_vault_isolation.py` | **15 passed**（原 3 红转绿，12 条既有绿不回归；含 Codex M1 整改后的「同一 client 两次解析」版） |
| 2 | `… tests/regression/test_write_side_group_guard.py` | **5 passed**（原 2 红转绿 + 1 新增 409 条 + 2 条既有绿含静态守卫） |
| 3 | `… tests/api/v1/endpoints/test_metadata_subject_mapping.py` | **19 passed**（门下，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`） |
| 4 | `… tests/unit/test_subject_resolver.py tests/unit/test_vault_switch.py` | **65 passed**（5 隐藏红转绿，非卡文说的 4 条） |
| 1-4 合跑 | 五文件 | **104 passed, 10 warnings in 1.27s**（先红时为 12 failed + 91 passed = 103，多的 1 条是新增的 409 覆盖） |
| 5 | `ACTIVE_VAULT=zzz_probe_vault …` 五文件 | **104 passed** |
| 5' | **强探针**（自加，见 §七） | **104 passed** |
| 5'' | **对撞探针**（Codex M2 后自加，见 §七） | **104 passed** |
| 6 | diff 面 + `def test_` 前后表 | 见 §五 |
| 7 | 门下目录级 `tests/unit tests/api tests/regression` | 见 §六（**前提不成立**） |

### 五 零实现改动 + 负控假绿门（卡文 (f)(g)）

```
$ git diff --name-only 304f03ca HEAD | grep -v '^backend/tests/' | grep -v '^_bmad-output/'
（空）
```

`def test_` 前后表（六个受影响文件，卡文 (g)）：

| 文件 | 改前 | 改后 | 判定 |
|---|---|---|---|
| `tests/unit/test_lancedb_vault_isolation.py` | 15 | 15 | 不变 |
| `tests/regression/test_write_side_group_guard.py` | 4 | **5** | **+1**（新增 409 条） |
| `tests/api/v1/endpoints/test_metadata_subject_mapping.py` | 21 | 21 | 不变 |
| `tests/unit/test_subject_resolver.py` | 39 | 39 | 不变（`:118` 是**改名**不是删除） |
| `tests/unit/test_vault_switch.py` | 26 | 26 | 不变 |
| `tests/unit/test_vault_scope_409.py` | 38 | 38 | 未改动（仅在 docstring 里被引用为取代条） |

⚠️ **计数口径如实声明**：`grep -c 'def test_'` 是**上界**，不等于 pytest 收集数。
`test_metadata_subject_mapping.py` 的 21 里有 2 个是**名字以 `test_` 开头的 fixture**
（`:27 def test_config_path` / `:48 def test_resolver`，均带 `@pytest.fixture`），
实际 collect = **19**（`--collect-only` 实测）。已核对该文件无同名 `def` 重复定义
（`grep -o 'def test_[a-zA-Z0-9_]*' | sort | uniq -d` 输出为空），排除「后一个静默覆盖前一个」。
作为「只增不减」的**相对**判据，前后用同一条 grep 比较仍然成立。

**只增不减成立，无一条被删。** 两处**改名**（非删除）逐条列出：

| 原名 | 新名 | 依据 |
|---|---|---|
| `test_manual_requires_both_subject_and_category` | `test_manual_subject_alone_defaults_category_to_subject` | 原名描述的是 Story 1.9 之前的契约，DD-13 名实一致 |
| （无删除，`test_explicit_vault_id_still_wins` 保留原名，语义拆分后新增 `test_explicit_foreign_vault_id_raises_409`） | — | 卡文 (d)「改写而非直删」 |

新契约的环境无关既有覆盖（卡文点名，本卡未改动该文件）：
`tests/unit/test_vault_scope_409.py:77`（`test_explicit_mismatch_raises_409`）、
`:95`（`test_explicit_match_derives_and_injects`）、
`:118`（`test_double_missing_derives_active_vault`）、
`:126`（`test_double_missing_keeps_secondary_levels`）。

### 六 裁判 7：门下目录级（前提不成立，如实登记）

卡文裁判 7 的前提是「主干既有红 = 6 条」。实测**完全不成立**。

在 `304f03ca` 另开只读 worktree 跑**同一条命令**做基线对照：

| 树 | 命令 | 结果 |
|---|---|---|
| 基线 `304f03ca`（scratch worktree，同 venv / 同 `.env`） | `pytest -q -p no:cacheprovider tests/unit tests/api tests/regression` | **225 failed, 6175 passed, 7 skipped, 1 xfailed, 38 errors** in 558.51s |
| 本卡树 `card/z4-redbase`（Codex 整改前） | 同上，逐字相同 | **213 failed, 6188 passed, 7 skipped, 1 xfailed, 38 errors** in 527.46s |
| 本卡树（Codex M1/M2/L1 整改**后**复跑） | 同上，逐字相同 | **213 failed, 6188 passed, 7 skipped, 1 xfailed, 38 errors** in 490.09s |

整改前后的目录级 FAILED/ERROR nodeid 集合**逐条完全相同**
（`diff` 输出为空 → `IDENTICAL_BEFORE_AND_AFTER_REMEDIATION`），
即 M1/M2/L1 整改没有动到本卡五文件以外的任何一条。下面的 nodeid 对比对两次跑均成立。

**逐条 nodeid 差异（这是「本卡零引入」的判据，不是看总数）**：

```
$ diff <(基线 FAILED/ERROR nodeid | sort) <(本卡树 FAILED/ERROR nodeid | sort)
40d39
< FAILED tests/api/v1/endpoints/test_metadata_subject_mapping.py::TestGetMetadata::test_metadata_group_id_format
45,46d43
< FAILED tests/regression/test_write_side_group_guard.py::test_explicit_vault_id_still_wins
< FAILED tests/regression/test_write_side_group_guard.py::test_missing_vault_and_group_derives_current_vault
146,148d142
< FAILED tests/unit/test_lancedb_vault_isolation.py::…::test_active_vault_id_level2_runtime_error_falls_through
< FAILED tests/unit/test_lancedb_vault_isolation.py::…::test_group_id_has_vault_prefix
< FAILED tests/unit/test_lancedb_vault_isolation.py::…::test_dynamic_vault_id_follows_config
231,235d224
< FAILED tests/unit/test_subject_resolver.py::TestGroupIdFormat::test_group_id_format_config
< FAILED tests/unit/test_subject_resolver.py::TestGroupIdFormat::test_group_id_format_default
< FAILED tests/unit/test_subject_resolver.py::TestGroupIdFormat::test_group_id_format_manual
< FAILED tests/unit/test_subject_resolver.py::TestPriorityResolution::test_manual_override_highest_priority
< FAILED tests/unit/test_subject_resolver.py::TestPriorityResolution::test_manual_requires_both_subject_and_category
258d246
< FAILED tests/unit/test_vault_switch.py::TestReloadSettings::test_vault_id_changes_after_reload
```

**全部 17 行 diff 都是 `<`（基线有、本卡树没有），零条 `>`。**
即：本卡精确清零 12 条，**没有让任何一条原本绿的变红**，也没有让任何一条原本红的换个形态继续红。
（225 - 12 = 213 ✓；6175 + 12 + 1 新增用例 = 6188 ✓）

**剩余 213 failed + 38 errors 的分布**（本卡范围外，主干既有）：

| 目录 | FAILED | ERROR |
|---|---|---|
| `tests/unit` | 206 | 38 |
| `tests/unit/grouping` | 2 | 0 |
| `tests/regression` | 3 | 0 |
| `tests/api/v1/endpoints` | 2 | 0 |

密度最高的几个文件：`test_memory_service_write_retry.py` ×18、`test_chat_endpoint.py` ×16、
`test_story_30_13_batch_idempotency.py` ×11(ERROR)、`test_story_30_11_batch_parallel.py` ×10(ERROR)、
`test_supplementary_reranker.py` / `test_config_neo4j.py` / `test_agent_templates_smoke.py` 各 ×9。

**结论：裁判 7 判 FAIL（前提不成立），本卡无法交付「目录级既有红 = 0」。**
本卡实际交付的是：**台账定性的这一族（12 条）清零 + 逐条 nodeid 证明零引入**。
其余 213 条是台账从未登记过的另一片存量，规模远超一张卡，需主 session 独立排卡定性。

W4 门在两次目录级跑中均生效：本卡树 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=12 (blocked=12, advisory=0, unaccounted=0)`
——12 次真连尝试全部被门拦下，零漏网。

### 七 环境无关性证明（卡文 (h) + 自加强探针）

卡文 (h) 要求的 `ACTIVE_VAULT=zzz_probe_vault` 是**弱探针**——正因为本批红的根因之一就是
`Settings.vault_id` yaml-first，单改 `ACTIVE_VAULT` 根本改不动 `get_current_vault_id()`。
验伪锚实测：

```
默认环境        : vault_id = canvas_vault
仅 ACTIVE_VAULT : vault_id = canvas_vault   ← 弱探针无效（这正是根因现场）
强探针          : vault_id = zzz_probe_vault ← CANVAS_BASE_PATH 指向 tmp vault（yaml vault_id=zzz_probe_vault）
```

因此本卡额外跑了**强探针**（把 `CANVAS_BASE_PATH` 指到临时 vault 目录，其
`.canvas-config.yaml` 写 `vault_id: "zzz_probe_vault"`）。

⚠️ Codex round-1 M2 之后又补了第三条**对撞探针**——强探针也有盲区：它用
`zzz_probe_vault` 作 vault 名，与测试里写死的 foreign 名 `some_other_vault` 恰好不撞。
**探针取值必须与被测断言里的字面量对撞才有鉴别力。**

| 探针 | 环境 | 结果 |
|---|---|---|
| 弱（卡文 (h) 要求） | `ACTIVE_VAULT=zzz_probe_vault` | **104 passed**（但 `vault_id` 仍是 `canvas_vault`，见上表 → 探针本身无效） |
| 强 | `CANVAS_BASE_PATH=<tmp vault, yaml vault_id=zzz_probe_vault>` + `ACTIVE_VAULT=zzz_probe_vault` | **104 passed**（`vault_id` 实测切到 `zzz_probe_vault`） |
| 对撞 | `CANVAS_BASE_PATH=<…/some_other_vault>` + `ACTIVE_VAULT=some_other_vault`（= 测试里的 foreign 名） | **104 passed**（整改前此环境下 `test_explicit_foreign_vault_id_raises_409` 会 `DID NOT RAISE`） |

**全字面量对撞（自加，比 Codex 的单点反例更强）**：把五个测试文件里出现的**每一个**
vault 字面量都轮流当作环境 vault（`CANVAS_BASE_PATH` 指向同名 tmp vault，其
`.canvas-config.yaml` 写 `vault_id: <该字面量>`，同时 `ACTIVE_VAULT` 也设成它）：

```
$ grep -ohE '"(cs_61b|cs61b_stable|some_other_vault|probe_active_vault|probe_vault_id|
   vault_before_switch|vault_after_switch|CS 61B|cs61b)"' <五文件> | sort -u
"CS 61B" "cs_61b" "cs61b_stable" "cs61b" "probe_active_vault" "probe_vault_id"
"some_other_vault" "vault_after_switch" "vault_before_switch"
```

| 环境 vault | 结果 |
|---|---|
| `cs_61b` | 104 passed |
| `cs61b_stable` | 104 passed |
| `some_other_vault` | 104 passed |
| `probe_active_vault` | 104 passed |
| `probe_vault_id` | 104 passed |
| `vault_before_switch` | 104 passed |
| `vault_after_switch` | 104 passed |
| `cs61b` | 104 passed |

**8 / 8 全绿。** 这直接回应 M2 暴露的探针盲区：不再依赖「选一个看起来不一样的值」，
而是把断言里的字面量**穷举**出来逐个对撞。

### 八 格式门（本卡零新增漂移 — 判据经 Codex round-2 LOW-2 修正后重验）

`ruff format --diff`（`line-length = 120`，ruff 0.15.9）对五文件报
「2 files would be reformatted」——**基线 `304f03ca` 逐行完全相同**。

存量漂移共 **6 处 hunk 分布在 2 个文件**（都是历史按更短行宽格式化的遗留，本卡一处未碰）：

| 文件 | 漂移处 |
|---|---|
| `test_write_side_group_guard.py` | `test_no_default_group_id_fallback_in_write_paths` 里的列表推导折行、`assert offending == [], (…)` 折行 |
| `test_lancedb_vault_isolation.py` | `with patch(…"fallback_vault")` 折行、`raise AttributeError(…)` 折行、`monkeypatch.setitem(…broken_subject_config)` 折行、Level-4 `assert result == "default", (…)` 折行 |

本卡初稿曾引入 2 处**新**漂移（自己写的折行），已就地改回单行；M2 整改时又引入
1 处（`_pinned_settings` 前少一个空行，由 Codex round-2 LOW-2 抓到），也已补上。

⚠️ **判据本身修正过一次**（§九 LOW-2）。曾用的
`grep -E '^[+-][^+-]'` 要求 `+` 后跟一个非 `+/-` 字符，**看不见空行的增删**，
对空行漂移会假通过。现用无盲区版本：

```
$ diff <(grep -E '^[+-]' fmt-baseline.txt | grep -vE '^(\+\+\+|---) ') \
       <(grep -E '^[+-]' fmt-current.txt  | grep -vE '^(\+\+\+|---) ')
NO_NEW_DRIFT_vs_BASELINE (空行也算)
```

`ruff check` 五文件 **All checks passed**。存量漂移属既有债，本卡不顺手修
（修它会把 6 处与本卡无关的格式 hunk 揉进 diff，违反「不混合不相关变更」；
且这是全仓性的 ruff 版本/行宽演进问题，该由独立卡统一处理）。

**commit 门处置（如实登记，不含糊）**：`lefthook` 的 `pre-commit::python-lint`
（glob `{backend,src}/**/*.py`）会跑两步，我在 stage 后手动逐步预演过：

```
ruff check <5 staged files>          → All checks passed!            check_rc=0
ruff format --check <5 staged files> → 2 files would be reformatted  format_rc=1
```

第二步 rc=1 会阻断 commit。本卡用 `LEFTHOOK_EXCLUDE=python-lint` 绕过**这一个** hook，
依据是上面两条已手动执行的实测 + §八 的逐行基线对比（红点与 `304f03ca` 完全相同）——
即「被绕过的门会说什么」已经验过，不是盲绕。其余 pre-commit 门（spec-sync /
python-typecheck / ghost-files）与 commit-msg 门（commitlint / spec-reference）照常执行。

### 九 Codex 复核（卡文 (i) 写 1 轮，实跑 2 轮，理由见本节末）

命令（协议 §2，1 轮）：

```
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat …/prompts/codex-prompt-CARD-REDBASE-R1.md)" \
  > …/codex-review-CARD-REDBASE-R1.md 2> …/codex-review-CARD-REDBASE-R1.stderr </dev/null
```

⚠️ 第一次执行用 PATH 上的 homebrew `codex-cli 0.147.0`，产出 **0 字节 + rc=1**，
stderr 尾部原文：

```
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",
"message":"The 'gpt-6-astra' model requires a newer version of Codex. …"}}
```

改用 `npx -y @openai/codex@0.153.3`（未升级全局 CLI）重跑，rc=0，正文 14031 字节。详见 §十.5。

### 终审结论

**`BLOCKER/HIGH 清零: 是`** — 2 MEDIUM + 1 LOW，按协议 §1 均为「登记不阻断」。
Codex 自行复现了 12 条基线红（`12 failed, 91 passed`）与本卡态（`104 passed`），
两次均 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`；并核对了主张 B（diff 面）与 C（计数非减）为 PASS。
它对「是否有实现缺陷被当成过时测试掩盖」的裁定是 **PASS，未找到**——
其中 `manual_subject alone` 一条它独立查了 `git show 9f554748`（2026-03-18）与
Story 1.9 归档，确认是有意演进（并指出 `subject_resolver.py:169` 的 "both" 是未同步注释）。

### 三条发现全部整改（不是登记了事）

| 级别 | 发现 | 我方核实 | 整改 |
|---|---|---|---|
| **M1** | 新版 `test_dynamic_vault_id_follows_config` 覆盖被削弱：初版「先 patch 再建 client，只取一次表名」，丢掉了旧版「先建 client 再切配置」才能抓的「构造时把 vault 冻进 `_vault_id_override`」回归。Codex 用进程内变异实证：`baseline_test_with_constructor_freeze_mutation=FAIL` / `new_test_with_constructor_freeze_mutation=PASS` | **属实**，且我的 docstring 写了「AC #3 原意图不变」= 声明比证据宽 | 改成**复用同一个 client**，在 `vault_before_switch` / `vault_after_switch` 两次 patch 下各解析一次并要求结果跟着变 |
| **M2** | 新增的 409 用例只固定了稳定 ID，`active_vault_aliases()`(`vault_scope.py:120-134`) 仍读真实 `ACTIVE_VAULT` 与 `CANVAS_BASE_PATH` basename → foreign 名不保证 foreign。实测 `ACTIVE_VAULT=some_other_vault …::test_explicit_foreign_vault_id_raises_409` → `DID NOT RAISE`（实现按合法别名放行是**正确**的，误红来自测试） | **属实，已在本树复现同一行输出** | 新增 `_pinned_settings()` 替身，把别名集读的两个 settings 字段一起固定；`test_explicit_vault_id_still_wins` 同样固定 |
| **L1** | 四段格式出处表述过宽：根 `CLAUDE.md:33` 只列二段/三段，`build_vault_group_id` 里 subject/canvas **互斥**；四段的真实依据是 Phase A0.5-N | **属实**，我实查了 `CLAUDE.md:31-38`（确只三种形态）与 `round-23-multi-vault-implementation-plan-2026-05-10.md:77`（`vault:<vault_id>:<subject>:<canvas>` = 「✅ Phase A0.5-N ship」） | 三处 docstring 措辞改为「D16 前缀 + Phase A0.5-N 四段组合」，并点名 subject/canvas 互斥 |

Codex 另外两条措辞类意见也已采纳：
- **5a**「`CS 61B` sanitize 后已等于 `cs_61b`，不能证明目录别名归一化」→ 把稳定 ID 改成
  与目录名**不同**的 `cs61b_stable`，请求传目录名 `"CS 61B"`，只有走完
  「别名命中 → 归一到稳定 ID」才能得到 `vault:cs61b_stable`，并加 `!= "vault:cs_61b"` 反向断言。
- **5c**「『原意图不变』不精确，旧测试没传 legacy」→ docstring 已改为陈述新断言实际证的东西。

Codex 指出的 **「六文件」实际只有五个 diff 文件** 属实：第六个 `test_vault_scope_409.py`
本卡未改动，只在 §五表里作为「取代条来源」列出并标注未改动。
它指出的 `test_vault_switch.py:145-232` 相邻 yaml 用例 teardown 只还原 env、
可污染 `test_cache_clear_picks_up_new_value` —— **基线既有，非本卡引入**，登记不修（本卡不扩面）。

### 整改后的负控（证明整改承重，不是改了措辞）

**M1 负控** — 进程内注入「构造时冻结 vault」变异（pytest 插件，不改生产文件）：

```
无变异  : 1 passed
带变异  : MUTANT_INSTALLED=constructor_freeze
          assert client.resolve_table_name("vault_notes") == f"{vault_after}_vault_notes"
          E   AssertionError: assert 'vault_before...h_vault_notes' == 'vault_after_...h_vault_notes'
          1 failed
```

判据绑定的是**失败身份**：红在新加的那一条 `vault_after` 断言上，而不是「某处失败」。

**M1 负控变体 2**（自加）— 换一种「表名解析被提前固化」的形态：不动 `__init__`，
改成在 `resolve_table_name` 层按 table_name 缓存结果：

```
MUTANT_INSTALLED=resolve_table_name_cache
tests/unit/test_lancedb_vault_isolation.py:81: in test_dynamic_vault_id_follows_config
    assert client.resolve_table_name("vault_notes") == f"{vault_after}_vault_notes"
E   AssertionError: assert 'vault_before...h_vault_notes' == 'vault_after_...h_vault_notes'
1 failed
```

**两种固化形态都 KILLED，且红在同一条断言（`:81`）。** 说明这道门守的是
「同一个 client 跨配置切换后表名必须跟着变」这个**语义**，而不是某一个具体实现细节。

### 审查绑定与轮次（卡文写 1 轮，本卡跑 2 轮，理由如下）

round-1 在正文里自记了审查面：`HEAD=304f03ca…`，最终测试 diff 的
`SHA-256 = 82aa19f0581cab5f8edf562c5d5442a253014c3960cf0683489ae7b88b8fe2db`。
**本卡在它出结论之后按 M1/M2/L1 改了代码树**，因此协议 §1 的「终审绑定看代码树」
判据（`git diff --stat <审SHA> HEAD -- . ':!_bmad-output'` 为空）对 round-1 **不成立**——
而卡文 (i) 要求的是「审查面 = 本卡 diff」。

M1/M2 的整改不是措辞，是实质改了测试逻辑（M1 改成同一 client 两次解析、
M2 加了 settings 替身并把稳定 ID 与目录名拆开）。只靠本方负控背书不够。
故加跑 **round-2 增量确认**（卡族轮次 2/3，协议 §1 上限 3）。
round-2 的 prompt 明确限定「**只审 M1/M2/L1 的整改，不重开 round-1 已 PASS 的面**」，
避免第八九批那种「每次整改都重开全面审 → 无限回归 → 永远合不了」的僵局。

### round-2 结论（增量确认）

**`BLOCKER/HIGH 清零: 是`** — M1 成立、M2 环境隔离成立、L1 成立；
**新增 2 条 LOW，无 BLOCKER / HIGH / MEDIUM**。审查绑定 `HEAD=304f03ca…`，
它记录的五文件 diff `SHA-256 = 0a8ee996ac5efb74de16be74635669aba91ca4542f9d0aeb86a19d9b0b6b0d38`。

| 项 | round-2 裁定 | 证据摘录 |
|---|---|---|
| M1 (a) 同一变异 | **成立** | `current_test_unmutated=PASS` / `current_test_constructor_freeze_mutation=FAIL assertion_line=81` / `current_test_resolve_lru_cache_mutation=FAIL assertion_line=81` |
| M1 (b) 其它固化形态 | 成立，但**给出覆盖边界** | 「给真实 `get_current_vault_id()` 加缓存」这一形态**检测不到**（测试内的 patch 会替换掉那个被变异的 getter）：`current_test_with_upstream_getter_cache_mutation=PASS`。它明确说这不是现行实现的缺陷，而是该门的边界 |
| M1 (c) 第二个 `with` 仍走 Level-3 | **成立** | 实测 ContextVar 未绑定/已绑定两种初态，均「同一 client、两次 `_vault_id_override=None`、两次 ContextVar=`general`」，结束后完整恢复 |
| M2 (a) 输入覆盖完整 | **成立，未找到遗漏** | `active_vault_aliases()` 只读三个输入，`_pinned_settings` 固定后两项 + 测试 patch 稳定 ID；分别把真实 `ACTIVE_VAULT` / 目录 basename / 两者同时设为 `some_other_vault`，两条测试均 PASS |
| M2 (b) patch 作用范围 | **未找到意外影响** | `get_settings fields actually read=['ACTIVE_VAULT','ACTIVE_VAULT','CANVAS_BASE_PATH']`；`get_settings restored=True`；`config.settings identity unchanged=True`；`original get_settings cache_info unchanged=True` |
| M2 (c) 「唯一路径」 | **不成立 → LOW-1** | 见下 |
| L1 三处措辞 | **成立，未找到仍超出证据的表述** | 它独立核了 `实施计划:77` 与 `subject_resolver.py:201-205` |
| 附问 1（相邻 yaml 用例污染归属） | **归属判定正确，本卡未加重** | `test_vault_switch.py:138-245` 与基线**逐字节相同** |
| 附问 2（格式红点与基线逐行相同） | **不成立 → LOW-2** | 见下 |

### round-2 两条 LOW 也已整改（不是登记了事）

**LOW-1 — 我把鉴别力说过头了。** 我在 `test_explicit_vault_id_still_wins` 的 docstring 里写
「**只有**走完『别名命中 → 归一到稳定 ID』才能得到 `vault:cs61b_stable`」。
Codex 用内存变异证伪：让实现在两个参数都提供时**把两者都丢掉**、落到双缺失分支
（`vault_scope.py:191-202`），该分支同样返回 `vault:<active_vault>`，**本条断言照样 PASS**。

⚠️ 这也打脸了我自己在 round-2 等待期做的那次源码变异——我变的是「用 `requested` 而非
`active_vault`」（`vault:cs_61b` ≠ `vault:cs61b_stable` → **KILLED**，源码 sha 逐字节还原），
于是我以为「唯一路径」成立。**我的变异只覆盖了一种实现走样，Codex 换一种就活下来了**
——典型的「变异覆盖不完整 ⇒ 把 KILLED 误读成唯一性证明」。

整改：docstring 改成陈述**边界**——它排除的是「直接采用 sanitize 后的请求值」这一类实现
（附上我那次变异的实测结果），**不能**排除「丢弃参数走双缺失分支」；并写明后者由本文件的
409 用例（跨 vault 显式值必须 409，双缺失分支不会）与 `test_vault_scope_409.py:95` 兜底。

**LOW-2 — 我的「格式红点与基线逐行相同」判据有盲区，结论是错的。**
我用 `grep -E '^[+-][^+-]'` 提取 diff 的增删行——该模式要求 `+` 后面跟一个**非 `+/-` 字符**，
而**空行的 `+` 后面什么都没有**，于是「新增/删除空行」的漂移在我的视野里完全不存在。
Codex 用同版本 ruff 逐行比对，抓到 `_pinned_settings` 前多了一个空行（我 M2 整改时写的）。

复核（换成无盲区判据 `grep -E '^[+-]' | grep -vE '^(\+\+\+|---) '`）：

```
旧判据（有空行盲区）→ NO_NEW_DRIFT       ← 假通过
正确判据           → 0a1
                     > +                 ← 真有一处新增空行
```

整改：补上 ruff 要求的第二个空行；用**无盲区判据**重跑对比 →
`NO_NEW_DRIFT_vs_BASELINE (空行也算)`。§八 的结论以此为准。

整改后：五文件 **104 passed**，`ruff check` **All checks passed**，
格式漂移（含空行）与基线 `304f03ca` 逐行相同。

⚠️ **round-2 的两条 LOW 整改同样未再经复审**（卡族轮次已用 2/3）。
两处都是小改（一个空行 + 一段 docstring 措辞），且 LOW-2 的整改由无盲区判据实测背书、
LOW-1 是把结论改弱到与证据一致（方向上只会更保守）。

**M2 负控** — 用 Codex 的反例环境重跑，并进一步让 `CANVAS_BASE_PATH` basename 也叫
`some_other_vault`（三个别名输入全部与测试里的 foreign 名对撞）：

```
ACTIVE_VAULT=some_other_vault                                   → 5 passed
ACTIVE_VAULT=some_other_vault + CANVAS_BASE_PATH=…/some_other_vault → 5 passed
```

⚠️ **自我登记**：M2 也打脸了我原来的「环境无关性证明」——我的强探针用
`zzz_probe_vault` 作 vault 名，与测试里写死的 foreign 名 `some_other_vault` 恰好不撞，
所以全绿。**探针取值必须与被测断言里的字面量对撞才有鉴别力**，单值探针天然覆盖不到。
§七的探针表已补上第三条「对撞探针」。

### 十 本卡未证明什么

1. **`lancedb_client.py:785` 行号锚脆弱耦合（backlog 登记）**。
   `lib/agentic_rag/clients/lancedb_client.py` 的 `resolve_table_name` docstring 写着
   「判据钉死在 `tests/unit/test_lancedb_vault_isolation.py:23` 与 `:35`」——这是
   **实现文件用行号引用测试文件**的脆弱耦合：测试文件在第 23/35 行之前插入任何一行，
   这条 docstring 就静默失效（不会有任何门报红）。
   本卡的全部改动都落在 `:47` 之后，改前改后 `sed -n '23p;35p'` 输出逐字节相同
   （均为 `assert client.resolve_table_name("vault_notes") == "vault_notes"`），
   **锚点当前仍成立**。但这只是本卡碰巧没踩到，**本卡没有加任何门去守它**——
   下一张动这个文件头部的卡仍会静默弄断它。建议独立卡：把行号锚换成
   `::test_default_vault_no_prefix` / `::test_empty_vault_id_no_prefix` 函数名锚。
   （改 `lancedb_client.py` 是实现文件，本卡硬边界禁改。）

2. **目录级「既有红 = 0」未达成**，见 §六。本卡只证明了这 12 条清零 + 本卡零引入。

3. **`test_metadata_group_id_format` 的自证成分**：该条期望值调
   `get_current_vault_id()`，与被测端点同源，因此它只能鉴别**格式**（`vault:` 前缀 +
   四段结构），不能鉴别 vault 段取值是否正确。vault 取值的鉴别由第 2 条以 patch
   哨兵覆盖，但那是 `SubjectResolver` 直调路径，**不是**端点 HTTP 路径。
   端点路径的 vault 取值正确性本卡未证明。

4. **目录级跑会写真实 `backend/data/`**（TestClient lifespan，主干既有行为，非本卡引入）。
   三次 shasum 对账（同一条命令、同一 `LC_ALL=C`）：

   | 时点 | 文件数 | 变化 |
   |---|---|---|
   | 跑目录级之前 | 340 | — |
   | 第一次目录级之后 | 344 | 新建 `failed_edge_syncs.jsonl` / `failed_writes.jsonl` / `learning_memories.json` / `neo4j_memory.json` |
   | 整改后第二次目录级之后 | 344 | 文件数不再增，但 `failed_edge_syncs.jsonl` 与 `failed_writes.jsonl` 的 sha **变了**（每跑一次追加） |

   四个文件都被 `.gitignore` 覆盖，不进 commit，`git status` 也看不见它们——
   **这正是「git 判据对这类污染恒绿」的形态**，只有主动 shasum 对账才看得到。
   本卡未修此污染面（改的是断言，不是 lifespan），登记移交。

5. **两处「唯一路径 / 逐行相同」的结论曾经比证据宽，已被 Codex 各打回一次**——
   分别见 §九 的 LOW-1（我的变异只覆盖一种走样，换一种就活）与 LOW-2（我的 diff 判据
   看不见空行）。两处都已改到与证据一致。**未证明的是**：还有没有第三处同类型的
   「结论宽于证据」我和 Codex 都没抓到。
   两轮 Codex 的整改（M1/M2/L1 + LOW-1/LOW-2）本身**未再经复审**，卡族轮次已用 2/3。

6. **Codex CLI 版本约束（新环境事实）**：本机 PATH 上的 `codex` 是 homebrew
   `codex-cli 0.147.0`，它**不支持** `gpt-6-astra`，直接报
   `400 invalid_request_error: The 'gpt-6-astra' model requires a newer version of Codex`
   并产出 **0 字节正文 + rc=1**。这是 0 字节的**第四种成因**（既有教训只记了
   网络 / cyber 拦截 / 额度三种）。本卡改用 `npx -y @openai/codex@0.153.3` 跑通，
   **未升级全局 CLI**（避免影响其它并行车道）。后续车道若直接用 PATH 上的 codex
   跑 `gpt-6-astra` 会全部拿到 0 字节 —— 建议主 session 统一处置。

### 十一 台账待登记条目（本卡不改台账）

1. **§一.b 全批行（现第 38 行）**：主干既有红从「6 条」更正为「**12 条**」，
   本卡（`card/z4-redbase` / CARD-REDBASE-R1）已全部清零。新增登记的 6 条：
   `test_subject_resolver.py` ×5（`:89` / `:118` / `:380` / `:389` / `:394`）+
   `test_vault_switch.py:253` ×1。
2. **新增一行（第四类根因）**：`test_manual_requires_both_subject_and_category`
   的根因是 Story 1.9 契约演进，不属于卡文列的 D16 格式 / 环境耦合 / G2-2 三类。
3. **新增 backlog 行**：`lancedb_client.py:785` docstring 行号锚 → 函数名锚（见 §十.1）。
4. **新增 backlog 行**：目录级 `tests/unit tests/api tests/regression` 的既有红
   （§六实测数字），远超台账登记的 6 条，需独立排卡定性。
5. **新增环境行**：homebrew `codex-cli 0.147.0` 不支持 `gpt-6-astra`（§十.5）。
