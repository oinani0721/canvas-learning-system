你是资深代码审查者。请对下面这张卡的改动做**只读**对抗性审查，重点是找出作者自述里比证据宽的部分。

---

## 〇 round-1 处置说明（本轮请重点复核这些改动是否真的解决了问题）

round-1 报 BLOCKER 0 / HIGH 4 / MEDIUM 2 / LOW 2。**四条 HIGH 与两条 MEDIUM 全部接受并已改**，无驳回。逐条：

- **HIGH-1（legacy 归桶依据 + 混合快照 + 文档矛盾）**：`from_persisted` 改为**逐条**分形态（dict 值 = vault 桶，其余 = legacy 裸键），与迁移器 `classify()` 同口径 —— 混合快照不再把已迁桶降格成 concept。归属措辞从「唯一可证的归属」改为「**推定**，可能错」，并写入你给的反例（旧进程服务 A、配置改成 B 后重启）。「没有请求上下文会保护启动加载」这句已删除并改写成「正常启动**不会**因缺上下文拒载」。文件顶部常量注释与 `_load_card_states` docstring 两处「legacy 不加载」的矛盾表述已同步。新增门 `TestLoadMixedSnapshot`（2 条）。
- **HIGH-2（`--out` 可覆写输入乃至现网）**：新增 `assert_out_is_safe()`，`--out` 现在**两种模式都过闸**（现网身份 + 与 `--file` 同一文件的别名检测，路径与 inode 双判）。新增门 `test_out_aliasing_file_is_refused_in_dry_run` / `test_out_pointing_at_live_file_is_refused`。
- **HIGH-3（写盘中途失败不回滚 / 退出码不可分）**：`write_text` 移入 `try`；新增内部 `_restore()`，**区分 rc=1（已安全回滚）与 rc=3（回滚也失败，文件可能损坏）**；备份阶段自身加了失败处置与「备份读回校验」（没有可用备份就不开始写）。退出码约定写进模块 docstring。新增门 `test_write_failure_rolls_back_and_reports_distinct_code`。
- **HIGH-4（`resolve()` 挡不住硬链接）**：现网闸改为**双判据** —— `(st_dev, st_ino)` 文件身份（认得出硬链接）+ 路径包含（覆盖尚不存在因而没有 inode 的目标）。`_resolved()` 的注释已改，不再声称它绑 inode。新增门 `test_hardlink_of_live_file_is_refused`。
- **MEDIUM-1（`_unpersisted_concepts` 仍是裸 concept 身份）**：改为 `(vault_id, concept_id)` 二元组，新增 `_dirty_key()` / `_is_unpersisted()`。
- **MEDIUM-2（两处旧断言弱于新身份）**：两处都改为**定点查当前 vault 桶**并显式断言桶是 dict（不再用 `any(...)`，也不绑定具体 vault 名——vault 从 `svc._dirty_key(cid)[0]` 取）。
- **LOW-1**：`branch-decision` 里「把三串检索搬到 `backend/app` 也仍然零命中」确属错误（`review.py:1383` 就含 `fsrs-state`），已改。乙支可达性与 `/goal` 括注两处措辞已收窄为「按引用的条件式选择甲自洽」，不再声称已证明括注是失效预测。
- **LOW-2**：「`current_vault_id()` 恒不抛」已改为「正常情况下回落 active vault，不能用缺 ContextVar 作失败判据」。

**本轮请判断**：① 这些改动是否真的解决了 round-1 指出的问题，有没有引入新问题；② 新增的 6 条门是否真能锁住对应缺陷（而不是探针避开了缺陷显形点）；③ 还有没有 round-1 未覆盖的面。

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
