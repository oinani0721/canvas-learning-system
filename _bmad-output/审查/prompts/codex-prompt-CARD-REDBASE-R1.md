# Codex 对抗性审查 Round-1 — CARD-REDBASE-R1 [BATCH-2026-09-05-第十一批]

你是独立对抗审查者。LANE = 你的当前工作目录（车道 `card/z4-redbase`，基线 `304f03ca`）。
本轮审查面 = **本卡 diff**，即 `git diff 304f03ca -- backend/tests/` 的全部内容，共 5 个测试文件：

- `backend/tests/unit/test_lancedb_vault_isolation.py`（3 条）
- `backend/tests/regression/test_write_side_group_guard.py`（2 条改写 + 1 条新增）
- `backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py`（1 条）
- `backend/tests/unit/test_subject_resolver.py`（5 条）
- `backend/tests/unit/test_vault_switch.py`（1 条）

## 本卡的主张（请逐条证伪）

主张 A：这 12 条基线即红**全部是测试过时，零实现回归**。三类根因：
1. **D16 格式演进** — `vault:` 前缀由 `def3a27a`(2026-05-05) / `ecf16f2c`(2026-05-10) 落地，
   D16 口径出处 = 仓库根 `CLAUDE.md`「Graphiti group_id 命名规约（Story 2.5.Y D16 锁定
   2026-05-05）」，统一组装函数 `app/core/subject_config.py::build_vault_group_id`；
   `subject_resolver.py:201-206` 产出的四段 `vault:<vault_id>:<subject>:<canvas>` 是该规约的组合形态。
2. **环境耦合** — `Settings.vault_id`（`app/config.py:764-795`）优先读
   `CANVAS_BASE_PATH/.canvas-config.yaml` 的显式 `vault_id`，仓内 yaml 在位时
   `reload_settings({'ACTIVE_VAULT': ...})` 恒失效，于是断言测的是环境不是实现。
3. **CARD-G2-2 契约收敛** — 解析收敛进 `app/core/vault_scope.py`，双缺失分支直接调
   `build_vault_group_id`（`:199-201`）不再经 `default_vault_group_id`；显式跨 vault
   请求改为 `HTTPException(409)`（`:162-176`，别名集 `:120-134`）。

主张 B：**零实现改动** —— `git diff --name-only 304f03ca -- . ':(exclude)_bmad-output'`
的结果 100% 落在 `backend/tests/` 下。

主张 C：**没有靠删测试凑绿** —— 六个受影响文件的 `grep -c 'def test_'` 只增不减
（`test_write_side_group_guard.py` 4→5，其余不变）。

## 验证清单（每项 PASS / FAIL + 证据）

1. **是否有任何一条红其实是实现缺陷被当成「测试过时」掩盖掉。** 逐条比对新断言与被测
   实现的当前行为：新断言表达的是实现**应该**做的事，还是仅仅抄录了实现**正在**做的事？
   重点看 `test_subject_resolver.py` 里由
   `test_manual_requires_both_subject_and_category` 改名而来的
   `test_manual_subject_alone_defaults_category_to_subject` —— 它把「只给 subject
   不算 manual」改成了「只给 subject 也算 manual」。请判定 `subject_resolver.py:207-216`
   的现行行为是有意契约（Story 1.9）还是缺陷，并给出你的依据。

2. **动态组装是否真的动态。** 卡文禁止在断言里硬编码仓内 vault 字面量 `canvas_vault`。
   请在 diff 范围内检索该字面量，并判断每个 `f"vault:{...}"` 的 vault 段来源是
   patch 注入值 / `get_current_vault_id()` 返回值，还是变相硬编码。
   特别看 `test_metadata_subject_mapping.py` 的那条 —— 它的期望值调用
   `get_current_vault_id()`，与被测端点读的是同一个函数。请判断这构成「自证」
   （两侧同源导致门恒真）到什么程度、该门还剩下什么真实鉴别力。

3. **patch 点是否可达、是否过宽。** 各处 `patch("app.config.get_current_vault_id", ...)`
   依赖被测代码在函数内延迟 import。请确认每个被测路径确实在调用时才绑定该名字；
   并判断 patch 的作用范围是否意外覆盖了断言本身应当独立验证的环节。

4. **测试间污染。** 新增的 `_subject_contextvar_hygiene` autouse fixture、
   `test_lancedb_vault_isolation.py` 里的 `_current_subject_id` token 存取、以及
   `test_vault_switch.py::test_vault_id_changes_after_reload` 手工 try/finally 还原
   `CANVAS_BASE_PATH`/`ACTIVE_VAULT` 后 `reload_settings()` —— 这三处是否真的把全局
   状态还原干净。若某处还原不全，指出它会在什么执行顺序下影响别的用例。

5. **改写 vs 直删。** `test_explicit_vault_id_still_wins` 被保留了函数名但换了断言内容
   （改为「显式 vault_id 优先于 legacy_group_id」），另加
   `test_explicit_foreign_vault_id_raises_409`。请判定：
   a) 保留下来的那条在新契约下是否还有非退化的鉴别力；
   b) 原用例「跨 vault 显式 id 直接采用」的语义是否被 409 那条完整取代；
   c) 函数名与实际断言是否名实一致（DD-13）。

6. **主张 B / C 的核对。** 用命令实测，给出输出原文。

## 纪律

- **只读**。复现用 `LANE/backend/.venv/bin/python` 与
  `PYTHONDONTWRITEBYTECODE=1 LANE/backend/.venv/bin/pytest -q -p no:cacheprovider <文件>`。
  禁连 Neo4j 7691 / 7687。
- 每条结论给 `file:line` 或命令输出原文。新发现按 BLOCKER / HIGH / MEDIUM / LOW 分级。
- 判断不出来就写「未找到」，不要硬造。
- 末行必须给：`BLOCKER/HIGH 清零: 是|否`。
