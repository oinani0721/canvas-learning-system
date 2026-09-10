你是资深代码审查者。请对下面这张卡的改动做**只读**对抗性审查，重点是找出作者自述里比证据宽的部分。

---

## 〇 前两轮处置说明（本轮请重点复核这些改动，并判断是否引入新问题）

**round-1**：BLOCKER 0 / HIGH 4 / MEDIUM 2 / LOW 2 —— 全部接受并已改，无驳回。
**round-2**：BLOCKER 0 / HIGH 5 / MEDIUM 3 / LOW 2 —— **同样全部接受并已改，无驳回**。逐条：

- **r2 H1（备份路径没过闸，`.bak` 若是现网软/硬链接就覆写现网）**：两条派生备份路径现在都过 `assert_target_is_not_live()`，任一被拒即在**动源文件之前**返回 rc=2。新增门 `test_backup_path_pointing_at_protected_file_is_refused`（用 monkeypatch 把受保护路径指到 tmp 替身，再对 `.bak` 建硬链接做成反例输入）。
- **r2 H2（`UnicodeEncodeError` 在截断后逃逸回滚，rc=1 却文件已空）**：写盘 `except` 改为 `(OSError, ValueError, TypeError)`。注释里点明这与本仓 `_save_card_states` 的 CARD-D3 Codex HIGH-3 是同一个坑。新增门 `test_encoding_failure_does_not_escape_rollback`（输入用转义的孤立代理字符键）。
- **r2 H3（混合快照仍用推定归属覆盖已有明确 vault 身份）**：同名冲突时**保留桶内那份**（明确身份），legacy 那份进隔离区不覆盖也不丢。新增门 `test_legacy_does_not_overwrite_existing_bucket_entry`（形态与你给的 `{"A":{"c":"A-new"},"c":"legacy-unknown"}` 一致）。
- **r2 H4（拒载的 legacy 会被后续一次成功写入从磁盘永久删除）**：容器新增 `_orphan_legacy` 隔离区，`to_nested()` 每次落盘**原样写回**。新增门 `test_unadopted_legacy_survives_a_later_successful_save`（复现你给的完整触发链：启动推导失败 → 未归入任何桶 → 后续合法作用域成功写入 → 检查磁盘上 legacy 还在）。
- **r2 H5（拒绝现网的测试自身会覆写现网）**：改用 tmp 替身受保护文件 + monkeypatch，与硬链接那条门同一隔离方式，并断言替身内容未变。
- **r2 M1（写失败门没测到真正的中途失败与 rc=3）**：改成**先真截断再抛**；另加 `test_restore_failure_reports_rc3` 让备份成功、还原失败，断言 rc=3。
- **r2 M2（报告写失败破坏退出码约定）**：`write_report()` 捕获异常、返回 bool、只告警不冒泡。
- **r2 M3（迁移器接受 service 选不中的桶键）**：`--vault-id` 拒绝含 `:` `/` `\\` 的值，理由写在错误信息里。新增门 `test_vault_id_with_colon_is_refused`。
- **r2 L1**：dry-run 的表述改为「不改输入快照、不产生 .bak；给了 --out 才写那一份报告」，并在输出里显式说明报告是唯一文件写入。
- **r2 L2**：`branch-decision` 已把与限定相反的断言本身改掉（不再从「单个调用表达式不含检索串」推出「字符串方法判不出」的过强结论），并把括注处置降为「交主 session 复核，不宣布作废」。

**一件必须如实告知的事故**：新增 H4 门的初版用了 `monkeypatch.undo()` 来恢复作用域打断，而 `undo()` 会撤销同一测试内**全部** patch —— 包括 `states_file` fixture 设的 `_CARD_STATES_FILE`。那一跑因此把投影写到了车道树真实的 `backend/data/` 下（零写门破）。已改为定点保存/恢复那两个符号，泄漏文件已移出并留证（`evidence-g35/incident-zero-write-leak.txt`），复跑零写门为 ok。请一并检查**其余测试**有没有同类的「patch 作用域比预期宽」问题。

**本轮请判断**：① 这些改动是否真的解决了 r2 指出的问题；② 新增/改写的门是否真锁得住对应缺陷（探针有没有避开显形点）；③ `_orphan_legacy` 这个隔离区设计本身有没有引入新风险（例如它与 vault_id 同名、或在多进程/并发落盘下的行为）；④ 还有没有前两轮都没覆盖的面。

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
