你是资深代码审查者。请对下面这张卡的改动做**只读**对抗性审查，重点是找出作者自述里比证据宽的部分。

---

## 〇 本轮性质：卡范围已被用户缩小，请按**新范围**审查

前五轮（r1–r5）的 HIGH/MEDIUM/LOW **全部接受并改，无一驳回**。r5 仍报 HIGH 1 / MEDIUM 6 / LOW 1，触发协议「轮次上限 5 仍有 HIGH ⇒ 交人审」。

**人审结论（用户 2026-09-09 裁定）：缩小本卡范围。** 依据是五轮里的一个模式——每一轮的修复都在长出新边界，而**问题全部集中在 legacy 兼容层**，核心键化一次都没被推翻：

| 修复 | 该修复自身引入的新缺陷 |
|---|---|
| r2 H4：加 `_orphan_legacy` 隔离区 | r3 H1/H2/M1 |
| r3：改用保留键独立命名空间 | r4 H1/H2/H3 |
| r4：隔离区列表化 + 迁移器认领 | r5 H1/M1/M3/M4/M5/M6 |

### 已回退（移交下一张卡）

- `_orphan_legacy` 隔离区（含 `__slots__` 字段、`to_nested` 写回、`total_cards` 计入）
- `__g35_orphan_legacy__` 保留键命名空间（含 service 侧撞名守卫、迁移器侧 `--vault-id` 拒绝）
- 隔离区列表化（多份候选）与迁移器「认领」（`classify` 的 `n_isolated`、`build_migrated` 的认领分支、数量判据里的 `claimed_from_isolation`）
- 毒条目预检（`_json_writable` / `_keep_writable`）
- 上述各面对应的 10 条回归门

⇒ **r5 的 8 条里有 7 条（H1、M1、M3、M4、M5、M6，以及 M2 所依附的预检）随之不存在**；剩 L1 是注释与已删测试的矛盾，也随之消失。

### 本卡保留的范围（请只审这些）

1. **键化核心**：`_VaultScopedCardStates` 嵌套分桶、Mapping 协议代理到当前 vault 桶、`__eq__` 与 dict 比较当前桶；
2. **fail-closed**：`_resolve_vault` 走 `require_read_group(None)` 捕 `VaultScopeUnresolved`；写入口 `_card_states_try_set` 据其返回值不推进投影；`_dirty_key` / `_is_unpersisted` 按 `(vault, concept)` 记 dirty；
3. **legacy 的最小处置**（本卡只保证「不丢」这一条性质）：
   - 逐条分形态（混合快照不把已迁桶降级成 concept）；
   - **作用域解析得出来** ⇒ 按当前作用域**推定**归桶 + warning（归属是推定不是证明，反例已写进 docstring）；同名冲突**保留桶内那份**（明确身份优先于推定），legacy 那份未载入；
   - **作用域解析不出来** ⇒ **抛 `VaultScopeUnresolved` 拒绝构造**（fail-fast）。理由：只"这次不加载"会让下一次成功写入的全量快照把它们从磁盘永久删除（r2 H4）；拒绝启动则**文件原样躺在磁盘上没人动它**，数据零风险，且口径只剩一处。
4. **迁移器**：互斥模式组、`--dry-run` 不改输入不产备份、`--apply` 双备份 + 重读校验 + 失败还原（rc=1 已回滚 / rc=3 回滚也失败）、现网闸（inode + 路径 + `st_nlink>1` 三判据）、`--out` 与 `--file`/备份路径的别名检测、`--vault-id` 形态校验、数量判据区分「迁完」与「本来就空」。

**本轮请判断**：① 回退是否干净（有没有残留的半截逻辑、悬空引用、与已删门对应的死代码）；② **fail-fast 这个新行为**是否真的比"不加载"更安全，有没有把正常启动路径也误伤（例如现网那份 220 B 单键文件在正常配置下会不会导致拒绝启动）；③ 缩小后的范围内，键化核心与迁移器还有没有未覆盖的缺陷；④ 「本卡只保证不丢」这个收窄声明是否与代码实际行为一致。

---

## 一 背景 + 最小读取面（写死，只读这些）

**卡**: CARD-G3-5「FSRS 投影状态的 vault 维度」 · 批次 `[BATCH-2026-09-07-第十三批 / CARD-G3-5]`
**树**: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u9-mastery`（分支 `card/u9-mastery`）
**基线**: `155d3361`（U9-B `CARD-G3-7-R2` 末 commit）

**要解决的缺陷**: `review_service._card_states` 原以**裸 `concept_id`** 为键，落盘 `backend/data/fsrs_card_states.json` 也是扁平 `{concept_id: card}`。两个 vault 的同名 concept 撞同一条内存记录与同一个 JSON 键，**后写覆盖先写**。

**本卡做法**: 在 **service 侧**把存储改成 vault 分桶嵌套 `{vault_id: {concept_id: card}}`，调用面保持裸 `concept_id` 语义；vault 从 ContextVar 解析，解析不出来 fail-closed 不推进投影。**不改 HTTP 契约**（端点早有 `vault_id` Query 且已注入 ContextVar）。

### 最小读取面

1. **本卡 diff**：`git diff 155d3361 -- . ':(exclude)_bmad-output'`（工作区，尚未 commit 时用 `git status --porcelain` + 逐文件读）
2. `backend/app/services/review_service.py` 的：
   - `:105-135`（`_CARD_STATES_FILE` 常量 + CARD-G3-5/G3-7 注释）
   - `:350-610`（新增的 `_VaultScopedCardStates` 类 `:355`、`_resolve_vault` `:389`、`try_set` `:430`、`from_persisted` `:523`，以及三个模块级 helper `_card_states_try_set` `:572` / `_card_states_payload` `:590` / `_card_states_count` `:597`）
   - `:795-930`（`self._card_states` 声明 `:801`、`_load_card_states` `:821`、`_save_card_states` `:846`）
   - `:2670-2760`（`get_cached_card_states` `:2677`、`get_fsrs_state` 内的 TOCTOU 注释改写 `:2739`）
3. `backend/app/api/v1/endpoints/review.py`：`:26-62`（`_resolve_vault_group_id`）、`:1382-1435`（`get_fsrs_state` 端点，含 `vault_id` Query `:1395-1399`、注入 `:1424`、调用 `:1430`）—— **本卡未改此文件**
4. `backend/app/core/vault_scope.py`：`:260-330`（`current_group_id` / `current_vault_id`，含后者**恒不抛**的回落分支）+ `:355-460`（`VaultScopeUnresolved` `:359` / `require_read_group` `:388`）—— fail-closed 判据取自这里
5. `backend/app/services/frontmatter_signals.py`：`:28-45`（真相源 reader 的**进程级** `CANVAS_BASE_PATH`）
6. `backend/scripts/migrate_fsrs_card_states_vault_key_g35.py`（新文件，全文）
7. `backend/tests/regression/test_g3_5_vault_keyed_card_states.py`（新文件，全文）
8. `backend/scripts/migrate_neo4j_data.py:150-205`（备份/校验/还原的参照先例）
9. `_bmad-output/审查/evidence-g35/branch-decision-20260909T113301.md`（分支裁定）
10. `_bmad-output/审查/evidence-g37r2/census-20260908T073936.md`（U9-B 的消费方 census，§0 口径 + §六 结论）

---

## 二 作者自述，请独立核对（不要采信，去代码里验）

1. **「端点已有 vault 维度，键化不必改 HTTP 契约」**：`review.py:1395-1399`（`vault_id` Query）+ `:1424`（`_resolve_vault_group_id` 注入 ContextVar）+ `:1430`（`get_fsrs_state(concept_id)` 不传 vault）这三处，是否**真的**能推出「service 侧读 ContextVar 即可，openapi.json 不必变」？有没有别的入口不经过这条注入链？

2. **分支选择**：census 结论 `N = 1`，判据「N ≥ 1 ⇒ 走甲（键化实现）」。请核对 `branch-decision` 里的口径论证是否自洽，特别是：把端点层 `review.py` 计入「在线消费方」是否合理？作者声称「乙支仍可达（N 能取到 0）」，这个说法成立吗？作者对 `/goal` 括注「走乙」的处置（判为失效预期）是否比证据宽？

3. **fail-closed 是不是死分支**：作者用 `require_read_group(None)` 抛 `VaultScopeUnresolved` 作为「解析不出来」的唯一判据，并声称**不能**用 `current_vault_id()`（它恒不抛）。请核对 `vault_scope.py:294-320` 是否真的恒不抛；再核对负控 N2（拆掉 `try_set` 的守卫）红在点名断言上这件事，是否**足以**证明该分支非死分支。

4. **迁移器**：`--dry-run` 是否真的零写入？`--apply` 的数量判据（`gained == n_old - len(clobbered)` 且 `n_new_after > 0`；`n_old == 0` 时 exit 0 不产生 `.bak`）能否把「迁完」与「本来就空」分开？备份/重读校验/失败还原路径在**写盘中途失败**时是否真能还原？现网闸 `assert_target_is_not_live` 用 `resolve()` 比对，有没有它拦不住的等价写法？

5. **既有测试的两处断言改动**：作者改了 `tests/unit/test_review_service_fsrs.py:777-783` 与 `tests/regression/test_g3_7_truth_source.py:265-271` 两处**落盘形状**断言（从 `on_disk[cid]` 改成「某个 vault 桶里含 cid」），声称「两条用例原意一字不减」。请核对这个说法：改动后它们是否仍在测原来那件事，有没有被削弱成更弱的判据？

---

## 三 按重要性排序的问题

1. **嵌套字典与既有形状假设的冲突**：`_VaultScopedCardStates` 的 Mapping 协议（`__getitem__` / `__setitem__` / `__contains__` / `__len__` / `__bool__` / `__iter__` / `get` / `pop` / `items` / `keys` / `values` / `__eq__`）是否覆盖了 `review_service.py` 里**全部**既有调用点？特别是 `get_history` 里 `if not all_records and self._card_states:` + `for key, card_data in self._card_states.items()` 这一段（当前作用域桶 vs 全部桶的语义差别），以及 `get_cached_card_states` 的「all」语义收窄，是否有调用方会因此拿到与预期不同的结果？

2. **无请求上下文的路径**：从 ContextVar 取 vault，在**后台任务 / CLI / scheduler / 启动期 `__init__`** 下会走到哪条分支？会不会静默落进某个缺省桶？`from_persisted` 对 legacy 扁平快照「归当前解析到的 vault 桶」这个处置，在一进程多 vault 或配置漂移时会造成什么后果？作者声称「解析不出来就不加载」是 fail-closed，这条在启动期真的会被走到吗？

3. **真相源侧的进程级前提**：`frontmatter_signals._node_md_path` 的 `CANVAS_BASE_PATH` 是进程级配置，使「不同 vault 的同名 concept 由目录天然隔离」只在一进程一 vault 时成立。本卡对这个缺口只做了登记（代码注释 + 验收单）。这个登记是否覆盖了真实边界？有没有本卡的改动**加重**了这个缺口？

4. **备份与回滚**：迁移器的 `.json.bak.<ts>` + `.json.bak` 双备份、写盘、重读校验、失败 `shutil.copy2(stamped_backup, path)` 还原 —— 这条链在磁盘满 / 权限变化 / 备份本身写失败时的行为是什么？还原后返回 1，调用者能否分辨「还原成功」与「还原也失败」？

5. **未证明声明的覆盖面**：作者在验收单声明本卡「未闭合 TOCTOU」「未迁移 Neo4j 侧 mastery 数据」「未证明仓外消费方为零」「未证明一进程多 vault 下投影键化足够」。`review_service.py:2739` 的 TOCTOU 注释改写是否与实际做到的一致（作者称键化**不**闭合该窗口）？还有哪些本卡实际未证明、但读者会误以为已证明的地方？

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与具体理由。
另单列一节「**已核实成立的部分**」——你独立验过、确认作者说法属实的条目。

---

## 五 边界

- **只读**，不要修改任何文件。
- 不连任何数据库（Neo4j 7691/7687 一律不碰）。
- 不跑变异 harness、不跑测试套件。
- **不评** `backend/app` 的 pyright 存量（归 U1/U2 另卡；本卡判据只要求「本卡新增 = 0」，实测已达成）。
- **不评** U9-B 已交付的 `save_card_state` 退役与主 spec 处置。
- 不评 `backend/app/api/v1/endpoints/review.py` 的既有实现质量（本卡未改它）。
