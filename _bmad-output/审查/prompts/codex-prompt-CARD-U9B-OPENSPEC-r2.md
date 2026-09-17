# CARD-U9B-OPENSPEC 独立复核请求 round-2（BATCH-2026-09-11-第十四批 / 车道 T4-C）

你是独立审查者。只读，不改任何文件，不连接任何数据库。

---

## ① 背景

OpenSpec capability `concept-identity` 此前**唯一**的 Requirement
`FSRS Card State Legacy Bucket Preservation On Save` 是**悬空的**——它描述的双桶模型
（`self._card_states` + `self._legacy_card_states`，按 `is_uuid_v4(key)` 分桶）在 `backend/app`
下零命中；它的 Scenario 3 调用的公共方法 `save_card_state` 已于第十三批 CARD-G3-7-R2 退役，
主干已无其定义。

把这条 Requirement 整条 `## REMOVED` 掉会让 `openspec archive` 撞
`Spec must have at least one requirement` 而中止（⚠️ 该中止**退出码是 0**，判据必须看
主 spec 的 sha 而不是 rc）。所以本卡按设计稿 §4 T4-C 的口径，改为
**补一条如实描述已实现行为的替代 Requirement**，让 spec 既非空又真实。

⚠️ 口径提醒：`openspec validate concept-identity --type spec --strict` 在**改动之前就已经
PASS**（结构合法：1 Requirement + 3 个 4 井号 Scenario）。所以 validate **不是**本卡的鉴别
裁判；鉴别裁判是「archive 不再撞 SPEC_NO_REQUIREMENTS」。

---

## ② 改动面（本卡地盘 = 恰好 3 个文件）

审查基线：`git diff 02f59e5f9b52c1431f42c0bd59b3c7784f4d4cbe 1c8d315f8e86e2d94dfbaf64b1c47c6843a44b40 -- . ':(exclude)_bmad-output'`

1. `openspec/specs/concept-identity/spec.md` —— 悬空 Requirement 整段替换为
   `FSRS Card State Projection Snapshot Persistence`（1 Requirement + 4 个 4 井号 Scenario）。
2. `docs/project-status/fr-exploration/A6-phase0-reference-card.md` —— 「当前内容」描述块
   更新为新 Requirement/Scenario 名 + 一条替换记录。
3. `backend/tests/regression/test_g3_7_truth_source.py` —— **仅第 14 行模块 docstring** 的
   `save_card_state` → `_save_card_states`，无逻辑改动。

archive 的先红/后绿证明**全部在仓外 `mktemp -d` scratch 拷贝上跑**，真实树内既不建 change
也不跑 archive（`openspec/changes/` 的 diff 为空）。

---

## ③ 作者自述（请独立核对，不要采信）

1. 替代 Requirement **只**陈述 `ReviewService._save_card_states()` 已实现、且可在
   `backend/app/services/review_service.py` 里逐条验证的不变式，**没有发明新契约**（DD-01/DD-04）。
2. 它引用的都是**符号名**（`_save_card_states` / `_card_states` / `_card_states_lock` /
   `_CARD_STATES_FILE` / `_card_states_payload`），不引行号，且全文不出现裸 `save_card_state`。
3. 4 个 Scenario 都是 **4 个井号**（3 个井号会静默失败）。
4. `## Purpose` 占位符**一字未动**（A6 的用户裁定：phase1 change 归档时再填，不在本卡 scope）。
5. 裸名字在**地盘三文件**里已归零（3/1/1 → 0/0/0）；地盘外 5 处与 `changes/archive/` 档案 6 处
   是**故意保留**的（退役防复活断言 + 不可变历史档案），判据因此收窄到三文件。
6. 本卡零触 `backend/app/**`（含 `models/mastery_state.py` 的 `ConceptState.fsrs_*`，只登记不改）。

---

## ④ 请按重要性排序回答的问题

**⓪（最重要）替代 Requirement 是否有任何一句超出代码实际做的事？** 请拿它与
`review_service.py` 的 `_save_card_states` 逐句对。特别核这几句：
- 「全量快照、非增量」「payload 经 `_card_states_payload()` → `to_nested()` 的 vault 两级嵌套」；
- 「临时文件 + 原子替换；目标路径从不被本方法以写模式打开」；
- 「整个方法体（含 `pending` mutation）在 `_card_states_lock` 临界区内」；
- 「作用域解析不出来 ⇒ fail-closed，在 `try:` 之前就 return，连父目录 `mkdir` 都不跑」；
- 「`TypeError`/`ValueError` 额外回滚 `pending` 的内存 mutation；`OSError` 保留内存」；
- 「成功后无条件清空 `_unpersisted_concepts`」；
- 「投影/缓存非 FSRS 调度真相源，`persisted` 不得冒充 `truth_source`」。

**①** 有没有哪一句把**调用点**的行为写成了**本方法**的保证？（例如真相源门锁其实在调用点，
不在 `_save_card_states` 内。）

**②** 替代 Requirement 有没有反过来**漏掉**某条它本该覆盖、且代码确实保证的关键不变式，
以致这条 spec 仍然挡不住一个会破坏该行为的改动？

**③** 三文件之外有没有被误改？`changes/archive/` 的不可变档案、地盘外故意保留的裸名字
（`test_review_service_fsrs.py` 的退役防复活断言等）是否都原样未动？

**④** `test_g3_7_truth_source.py:14` 把裁定④ 的主语从 `save_card_state` 换成 `_save_card_states`，
在该文件所锁定的 decision.md 语义下是否成立？有没有把「公共方法退役」说成「私有方法承担同一裁定」
而造成新的名实不符（DD-13）？

**⑤** 4 个 Scenario 是否每条都可被测试复现（Given/When/Then 具体到能写成断言），
还是有哪条其实无法判定？

---

## ⑤ 最小读取面（写死，请只读这些）

- `openspec/specs/concept-identity/spec.md`（本卡新内容，全文）
- `docs/project-status/fr-exploration/A6-phase0-reference-card.md`
- `backend/tests/regression/test_g3_7_truth_source.py`
- `backend/app/services/review_service.py` —— 重点 `_save_card_states` 方法全文、
  `_CARD_STATES_FILE` / `_card_states_lock` 的模块级定义、`_card_states_payload` /
  `_card_states_count` / `_card_states_try_set` 三个 helper、`_VaultScopedCardStates` 类、
  以及 `_save_card_states` 的两个调用点（`record_review_result` / `get_fsrs_state`）
- `_bmad-output/审查/evidence-u9b-openspec/*.txt`（先红/后绿/归零/地盘的存档）
- `openspec/changes/archive/2026-04-07-a6-phase0-fsrs-card-state-bucket-preservation/**`
  （**只读对照**：悬空 Requirement 的原始措辞来源，本卡一字未动）

---

## ⑥ 输出格式

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级，每条给：`file:line` + 一句话问题 +
一句话说明你会怎么让它显形（措辞用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这一类）。
某级别为空请明写「无」。结尾给 BLOCKER/HIGH/MEDIUM/LOW 计数。

## ⑦ 边界

- 只读，不改文件，不连接任何数据库。
- **不评** `review_service.py` 生产逻辑本身的对错——本卡只读它、把它写成契约，不改它。
- **不评** `## Purpose` 占位符（用户已裁定不在本卡 scope）。
- 只评这 3 个文件的改动内容，以及「替代 Requirement 是否忠实于代码」这件事。

---

## ⑧ round-1 的处置（请核对是否真的修好，以及有没有修出新问题）

round-1 计数 = BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2。三条都已在 `1c8d315f` 落地整改：

| r1 条目 | 处置 |
|---|---|
| M1「heals all previously failed writes at once」超出代码保证 | 该句原是**照抄生产代码注释**（`review_service.py` 里「全量快照已落盘 → 所有历史写失败的 concept 同时被治愈」）。已改写为：clear 是**无条件**的、不核对条目是否真在本次快照里；清的是**标记**不是**数据**；作用域失败/回滚过的值不会被任何后续快照补回，并明写本 spec 不得被读成后者。Scenario 4 同步改为可判定形态（回滚过的值在一次成功快照之后**仍不在**盘上） |
| L1 A6 摘要把两个失败分支压成一句 | 补上分支差异：`TypeError`/`ValueError` **回滚**内存 mutation，`OSError` **保留**内存值 |
| L2「entire method body」字面不准（`_missing = object()` 在锁外） | 收窄为「所有 card-state 访问与 I/O（读旧值、应用 mutation、序列化、两步落盘）在锁内」 |

另：r1 问题④（`test_g3_7:14` 裁定主语替换）你判为「无法独立确认」，因为 `decision.md` 不在读取面内。
本轮把它加进读取面：`_bmad-output/审查/evidence-g37/decision.md`（若存在）。请据此判定该替换是否造成新的名实不符。

请重点核对：① 三条整改是否真的闭合；② 新措辞有没有反过来**过度收窄**（把代码确实保证的东西说成不保证）；
③ 整改有没有引入与代码不符的新句子。
