> ⚠️ 本文件是 CARD-REDBASE-R1 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z4-A 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-REDBASE-R1]`。车道：NEW `card-z4-redbase`（从 `304f03ca` 切，`.env` / `prompts/` / venv symlink 就位）。同车道串行 **Z4-A → Z4-B**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-REDBASE-R1 — 主干既有红一次清账：6 条 + 4 条同根因隐藏红全部定性为「测试过时」→ 按 D16 `vault:` 格式 + 去环境耦合改期望

## 〇 事实
| 事实 | 位置 |
|---|---|
| 6 条主干既有红（`67abca34` / `304f03ca` 复现）：`test_lancedb_vault_isolation.py` ×3、`test_write_side_group_guard.py` ×2、`test_metadata_subject_mapping.py::test_metadata_group_id_format` ×1；**全部是测试过时，零实现回归** | 台账 §一.b 全批行 |
| **D16 原文**：根 `CLAUDE.md`「Graphiti group_id 命名规约（Story 2.5.Y D16 锁定 2026-05-05）」：`vault:<vault_id>` / `vault:<vault_id>:<subject_id>` / `vault:<vault_id>:<canvas_name>`，构造走 `build_vault_group_id(vault_id, subject_id, canvas_path)`；`subject_resolver._make_group_id`（`:201-206`）产出四段 `vault:<vault_id>:<subject>:<canvas>` = 规约的组合形态。**若你实测发现四段与 D16 文档口径冲突，登记不擅改** | CLAUDE.md + subject_resolver.py |
| 格式演进时间线：`vault:` 前缀由 `def3a27a`（2026-05-05）+ `ecf16f2c`（2026-05-10）落地；`test_group_id_has_vault_prefix` 写于 `43294c38`（2026-04-17），`test_metadata_group_id_format` 写于 `8222daef`（2026-02-11）——早于演进 | git blame |
| 环境耦合根因：`Settings.vault_id` 优先读 `CANVAS_BASE_PATH/.canvas-config.yaml` 的 `vault_id`（`config.py:765-795`，`:781-790` yaml 分支，`:795` 才 fallback ACTIVE_VAULT），仓内 yaml 在位且写死 `vault_id: "canvas_vault"` → `reload_settings({'ACTIVE_VAULT': ...})` 恒失效（引入于 `b345e02b`） | config.py |
| 同根因已有先例裁定：同文件姊妹测试 `test_active_vault_id_fallback_when_no_contextvar`（`:155-163` 注释 + `:177-180`）被 CARD-G2-2 翻新为 patch `app.config.get_current_vault_id`——这就是整改姿势 | test_lancedb_vault_isolation.py |
| 红① `test_dynamic_vault_id_follows_config`（`:47-57`）：期望 `cs_61b_vault_notes` 实得 `canvas_vault_vault_notes`；红② `test_group_id_has_vault_prefix`（`:64-76`）：`startswith("cs61b:")` 两处过时叠加（reload 无效 + 裸 `subject:` 旧格式）；红③ `test_active_vault_id_level2_runtime_error_falls_through`（`:323-347`）：意图与实现一致（`lancedb_client.py:730` 窄 except 含 RuntimeError），只在 `:341` reload 被 yaml 覆盖 | 三条 |
| 红④ `test_missing_vault_and_group_derives_current_vault`（`test_write_side_group_guard.py:14-23`）：patch `default_vault_group_id` 断言 called，但新实现（`vault_scope.py:266-274`）调的是 `build_vault_group_id(active_vault, …)` 从不调它；红⑤ `test_explicit_vault_id_still_wins`（`:26-28`）：`vault_id="cs_61b"` 现在按 CARD-G2-2 契约 2 抛 `HTTPException(409)`（`vault_scope.py:162-176`，别名集 `:120-134`）；两者新契约已有环境无关覆盖：`tests/unit/test_vault_scope_409.py:77 / :95 / :118 / :126` | 两条 |
| 红⑥ `test_metadata_group_id_format`（`test_metadata_subject_mapping.py:308-315`）：端点直返 `info.group_id`（`metadata.py:152`），实得 `vault:canvas_vault:math54:线性代数`，期望旧 `math54:线性代数` | 一条 |
| **同根因隐藏红 4 条**（台账未登记）：`test_subject_resolver.py:380/:388/:394`（裸 `math54:离散数学` / `custom:path` / `general:random`）与 `test_vault_switch.py:253`（reload ACTIVE_VAULT="CS 61B" 断言 cs_61b）；两文件无 skip/xfail | 勘探 |
| 裁判环境：红⑥ 起 TestClient；2026-09-05 现网 7691 曾 Errno 61；本树有 W4 门，门下跑即可 | 注意 |

## 一 完成条件（AND）
- (a) 先红存证：改动前逐条贴 10 条的实际 assert 差值（期望 vs 实得），写进验收单 §先红。
- (b) 环境耦合三条（`:47-57` / `:64-76` / `:323-347`）一律去掉 `reload_settings(overrides={'ACTIVE_VAULT': ...})`，改 `unittest.mock.patch("app.config.get_current_vault_id", return_value=...)`（照 `:177-180` 姿势）；docstring 保留原意图并加一行「改法依据 = CARD-G2-2 先例 :155-163」。
- (c) 格式条（`:71`、`test_metadata_subject_mapping.py:315`、`test_subject_resolver.py:380/:388/:394`）期望改为 D16 `vault:<vault_id>[:<subject>][:<canvas>]`；**断言值必须由 `get_current_vault_id()` 或 patch 返回值动态组装，禁止硬编码 `canvas_vault` 字面量**。
- (d) `test_write_side_group_guard.py` 两条**改写而非直删**：前者改 patch `app.config.get_current_vault_id` 断言 `resolve_vault_group_id(None, None) == f"vault:{patched}"` 且 `!= "vault:default"`（契约 3 语义保留）；后者改 `pytest.raises(HTTPException)` + `status_code == 409`。
- (e) 隐藏红 `test_vault_switch.py:249-255`：monkeypatch `CANVAS_BASE_PATH` 到 tmp_path（无 yaml）后再 reload，或直接断言 yaml-first 优先级（与 `:146-166` 既有 schema-v2 用例不重复）。
- (f) **零实现改动**：`git diff --name-only 304f03ca..HEAD` 100% 落在 `backend/tests/` 下。
- (g) 负控假绿门：改动前后 `grep -c 'def test_'` 对六个受影响文件逐一比对，**测试函数数只增不减**；确需删任何一条 → 验收单列「被删条 → `test_vault_scope_409.py:<行>` 取代条」一一映射。
- (h) 环境无关性证明：`ACTIVE_VAULT=zzz_probe_vault` 再跑一遍全部受影响文件仍全绿。
- (i) 一轮 Codex（gpt-6-astra ultra），审查面 = 本卡 diff；§四 已裁决写入 D16 口径出处与「零实现改动」。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/unit/test_lancedb_vault_isolation.py` → 原 3 红转绿，其余不回归。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_write_side_group_guard.py` → 4 绿（含静态守卫）。
3. `… $PYTEST -q -p no:cacheprovider tests/api/v1/endpoints/test_metadata_subject_mapping.py` → 绿（门下；7691 拒连若报 collection/connection error 先查 fixture 是否触连）。
4. `… $PYTEST -q -p no:cacheprovider tests/unit/test_subject_resolver.py tests/unit/test_vault_switch.py` → 4 隐藏红转绿。
5. `ACTIVE_VAULT=zzz_probe_vault … $PYTEST -q -p no:cacheprovider <上述 5 文件>` → 全绿。
6. `git diff --name-only 304f03ca HEAD | grep -v '^backend/tests/' | grep -v '^_bmad-output/'` → 空；`grep -c 'def test_'` 前后表贴验收单。
7. 门下目录级：`… $PYTEST -q -p no:cacheprovider tests/unit tests/api tests/regression` → 既有红 **0**（这是本卡对下批所有目录级裁判的交付物）。

## 三 禁改与隔离
禁改任何实现文件（`subject_resolver.py`、`subject_config.py`、`vault_scope.py`、`lancedb_client.py`、`metadata.py`、`config.py`）；禁改 OpenAPI 契约面（`metadata_models.py` example/description——那是 Z4-B）；⛔ 禁改 `canvas-vault/.canvas-config.yaml` 的 `vault_id` 或 `.env` 的 `ACTIVE_VAULT`（会把已落库的 `vault:canvas_vault:*` 数据全部孤儿化 = 阻断级数据丢失）；禁碰 Neo4j 7691；禁用「删测试」当默认解法；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-REDBASE-R1.md` → `codex-review-CARD-REDBASE-R1.md`，1 轮）。验收单 `…/验收单/UAT-CARD-REDBASE-R1-<日期>.md`：DoD-3 双段；4-B「无变化（把几条早就过期、每次都误报的旧检查改成按现在的规则检查）」；「本卡未证明什么」必填（`lancedb_client.py:785` 行号锚脆弱耦合登记 backlog）；「台账待登记条目」必填（全批行 6 条 → 10 条清零）。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z4-B。**
