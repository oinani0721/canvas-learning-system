# Codex 对抗性审查 Round-2（增量确认）— CARD-REDBASE-R1 [BATCH-2026-09-05-第十一批]

你是独立对抗审查者。LANE = 你的当前工作目录（车道 `card/z4-redbase`，基线 `304f03ca`）。

**本轮只审 round-1 三条发现的整改，不要重开 round-1 已判 PASS 的面。**
round-1 结论：`BLOCKER/HIGH 清零: 是`，2 MEDIUM + 1 LOW。三条已全部整改，本轮请判定整改是否成立、
以及整改本身有没有引入新问题。round-1 全文在 `_bmad-output/审查/codex-review-CARD-REDBASE-R1.md`。

## 整改清单（逐条判定 成立 / 不成立 / 引入新问题）

**M1 — LanceDB 动态切换覆盖被削弱。**
round-1 指出初版「先 patch 再建 client，只取一次表名」放过了「`__init__` 把 vault 冻进
`_vault_id_override`」的回归（你当时的变异实验：旧门 FAIL、新门 PASS）。
整改：`backend/tests/unit/test_lancedb_vault_isolation.py::TestVaultIdFromConfig
::test_dynamic_vault_id_follows_config` 现在**复用同一个 client**，在 `vault_before_switch` /
`vault_after_switch` 两次 patch 下各解析一次并要求结果跟着变。
请判定：
a) 该门现在是否能抓住你 round-1 用的那个同一变异（请复跑一次你的变异实验）；
b) 还有没有别的「表名解析被提前固化」的形态是这道门检测不到的（例如把结果缓存在
   `resolve_table_name` 层而不是 `__init__` 层）；
c) ContextVar 置 `DEFAULT_SUBJECT_ID` 再 reset 的写法，在第二个 `with` 块里是否仍然
   保证解析走 Level-3。

**M2 — 409 用例受真实别名环境影响。**
round-1 实测 `ACTIVE_VAULT=some_other_vault` 下 `test_explicit_foreign_vault_id_raises_409`
`DID NOT RAISE`。整改：`backend/tests/regression/test_write_side_group_guard.py` 新增
`_pinned_settings()` 替身，把 `active_vault_aliases()` 读的 settings 字段一起固定；
`test_explicit_vault_id_still_wins` 同时改成「稳定 ID `cs61b_stable` ≠ 目录名 `CS 61B`」
以证明别名归一化真的发生（round-1 的 5a 意见）。
请判定：
a) `_pinned_settings` 是否覆盖了 `active_vault_aliases()` 实际读取的**全部**输入——
   若还有第三个输入没被固定，指出它以及能让本用例误红的环境取值；
b) `patch("app.config.get_settings", ...)` 的作用范围有没有意外影响本用例其它环节；
c) `test_explicit_vault_id_still_wins` 现在的断言是否真的只能由「别名命中 → 归一到稳定 ID」
   这条路径满足，还是存在别的路径也能得到 `vault:cs61b_stable`。

**L1 — 四段格式出处表述过宽。**
整改：三处 docstring（`test_lancedb_vault_isolation.py` 红②、`test_metadata_subject_mapping.py`、
`test_subject_resolver.py::TestGroupIdFormat`）改述为「D16 只列二段/三段且 subject/canvas 互斥；
四段是 `subject_resolver._make_group_id` 的组合形态，依据 Phase A0.5-N 实施计划 `:77`」。
请判定改后的表述是否仍有比证据宽的地方。

## 另外两点（只需一句结论）

1. round-1 提到 `test_vault_switch.py:145-232` 相邻 yaml 用例 teardown 只还原 env、
   可污染 `test_cache_clear_picks_up_new_value`。本卡判定为**基线既有、不归责本卡、不修**。
   请确认这个归属判定正确（即整改后本卡确实没有加重它）。
2. 整改后五文件仍 `104 passed`；`ruff check` 全过；`ruff format --diff` 的红点与基线
   `304f03ca` **逐行相同**（存量债）。请核对最后这一条。

## 纪律

- **只读**。复现用 `LANE/backend/.venv/bin/python` 与
  `PYTHONDONTWRITEBYTECODE=1 LANE/backend/.venv/bin/pytest -q -p no:cacheprovider <文件>`。
  禁连 Neo4j 7691 / 7687。
- 每条结论给 `file:line` 或命令输出原文。新发现按 BLOCKER / HIGH / MEDIUM / LOW 分级。
- 判断不出来就写「未找到」，不要硬造。
- 末行必须给：`BLOCKER/HIGH 清零: 是|否`。
