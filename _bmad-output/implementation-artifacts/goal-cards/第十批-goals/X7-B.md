> ⚠️ 本文件是 CARD-G3-2c-B（核心）的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十批手册 §三 X7-B 块。
> 批次标记 `[BATCH-2026-09-04-第十批 / CARD-G3-2c-B]`。前提：X7-A 的移植快照 commit 已在本车道落地。勘探 2026-09-04。

# CARD-G3-2c-B — quiz-answer write-ahead 核心：fsrs_applied 全分支生命周期 + 写序锚方向自洽 + 深层/非规范输入 fail-closed **拒绝而非解析**

## 〇 要闭合的三条 BLOCKER + 一条 HIGH（round-17 绑 `56bfe9d4`；行号对**已提交版**，工作树版已漂移——按锚文本定位）
| # | 缺陷 | 位置@56bfe9d4 | 锚 |
|---|---|---|---|
| B① | `fsrs_applied` truthiness：`bool("false")` 判已应用 → rc=0 打印「已完整应用，幂等跳过」但 W=None、payload 被删（少记/多记一次复习） | `SKILL.md:1878` | `_rc_dup_applied = _rc_dup.get("fsrs_applied") if isinsta` |
| B③ | 深层 JSON（512 层 exam_board）首写 rc=0 但崩溃窗重跑 RecursionError 未捕获 → 一次评分永久未 apply（**数据丢失路径**） | `SKILL.md:578` `_canon_tree` 递归 | 工作树已改显式栈 + 20 万节点预算（`:622` 注释），**尚未审** |
| H | foreign degraded 恢复不提升事件级凭据、两阶段不收敛：E1 degraded 首写 rc=0 → E2 恢复 E1 → 再跑 E1 仍 rc=1「false + W 已覆盖」，用户永远卡住 | `SKILL.md:2277`（提升代码只在 `:2381-2403`，foreign 路径 `:2283-2294` 因 `_already_` 为真跳过） | `_rc_pl_ = _o.get("payload") or {}` |
| M | 写序锚 pred_id 方向不可证明仍被信任（round-16 引入、round-17 R30 FAIL） | `_anchor_ok_f1` | — |
（B② 字符轴归 C 卡。）

## 一 完成条件（AND；每条先红后绿；fixture 逐字抄生产写侧形态）
- (a) 先红：`fsrs_applied` 为 `"false"/"true"/0/1` 四种非 bool 值时一律 fail-closed（判据 `type(v) is bool`，禁 `v in (True, False)`——`1 == True`）；round-17 门 `test_round17_fsrs_applied_must_be_strict_bool` 先红后绿。
- (b) 先红：foreign degraded 两阶段收敛门——E1 degraded 首写 rc=0 → E2 第一阶段恢复后 E1 receipt 必须升 `true` → 再跑 E1 必须 rc=0；实现：foreign 路径也走提升（`:2283-2294` 的 `_already_` 短路改为「已应用但凭据未提升 → 提升」）。
- (c) 先红：写序锚方向可证门——pred_id 命中但无时间/严格 ordinal 证据时 `_anchor_ok_f1` 不得为 True，须走歧义回退（不得 writer=0 零写并声称完整）。
- (d) 深层/非规范输入 **fail-closed 拒绝而非解析**：validator（`backend/scripts/validate_learning_events.py`）与首次 append 前共用同一硬上限（默认深度 64 / 节点 20 万，进 §6.1 加性条款）；禁「首写成功后才在恢复期拒」；含自引用结构报真因而非死循环；工作树的显式栈实现保留但改为**超限即拒**（不是「尽力解析」）。
- (e) 六格状态机 6 格全绿复跑（UAT 实测 1/2/3/5/6 FAIL，仅 4 PASS），每格给 rc / W / ledger 三元组实测值进验收单。
- (f) fixture 形态逐字抄生产写侧（MEMORY：fixture 形态 ≠ 生产形态；被归一化的字段直接构造账本行）；先断言预置真产生了目标形态。
- (g) 变异串行 ≥4：truthiness 回退 / foreign 提升去掉 / 锚方向校验去掉 / 深度上限去掉 → 各指定门红；还原逐字节；EXIT trap。
- (h) `docs/learning-events-schema-v1.md` §6.1 **加性**追加「输入硬上限」与 R6 身份键排除裁决条款，同批更新 `test_learning_events_schema_contract.py`（195 门）。
- (i) Codex 一轮（本族累计已 20 轮 → **本卡 1 轮**，只审 `git diff <移植快照SHA>..HEAD -- SKILL.md test_g3_2_review_ledger.py validate_learning_events.py docs/learning-events-schema-v1.md`，附已裁决清单：A1-A6 主序已 VERIFIED、A4.1 锁归 G3-3、字符轴归 C 卡、开放集合边界不计）。停轮后主 session 按阻断级判（数据丢失路径 = 阻断）。

## 二 裁判命令
1. `cd …/card-x7-ledger-c/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression/test_learning_events_schema_contract.py tests/regression/test_fsrs_bridge.py tests/regression/test_learning_event_log.py tests/regression/test_g3_2_review_ledger.py` → 211 + 车道数 + 新增全绿。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py -k "round17 or fsrs_applied or anchor or canon_tree or foreign"` → 先红（贴）后绿。
3. `PYTHONDONTWRITEBYTECODE=1 …/.venv/bin/python scripts/validate_learning_events.py <tmp fixture vault>/learning_events.jsonl; echo rc=$?` → 合法 rc=0；深层/自引用 fixture → 非 0 且报真因。
4. 变异脚本输出 + 还原 shasum。
5. live 零写：`shasum -a 256 …/canvas-learning-system/canvas-vault/learning_events.jsonl` 与节点 md 全集 sha 开工/收工同；`cmp` live `fsrs_bridge.py` 与车道版 rc=1（未部署）。

## 三 禁改与隔离
live vault 只读；不 cp 到 live；`learning_event_log.py` 只许查重最小修正；不实现任何锁（G3-3）；`review_service.py`（W8 面）、`daily_review_pick.py`（X5-B 面）禁改；禁目录级 pytest；`*.stderr*` 不入库；不动台账；不 push。

## 四 Codex 冻结命令 / 默认裁决 / 验收单
`codex exec --sandbox read-only -m gpt-5.6-sol -c model_reasoning_effort="ultra" "$(cat …/card-x7-ledger-c/_bmad-output/审查/prompts/codex-prompt-CARD-G3-2c-B.md)" > …/_bmad-output/审查/codex-review-CARD-G3-2c-B.md 2> …/codex-review-CARD-G3-2c-B.stderr </dev/null`；一轮为限，0 字节重发一次后人审。默认裁决：D1 深度 64 / 节点 20 万上限；D2 超限即拒不解析；D3 foreign 路径提升；D4 fixture 直接构造账本行。验收单 `UAT-CARD-G3-2c-B-核心状态机-<日期>.md`：4-A 裁判 1-5 + 六格三元组表；4-B「评分中途断电后重开 quiz-answer 会自动补齐上一次；奇怪的输入会被明确拒绝而不是悄悄吞掉」（仍未部署，如实降级）；「本卡未证明什么」必填（并发面、字符轴）。commit header ≤100 含批次标记，body 行 ≤100；不 push。
