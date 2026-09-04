> ⚠️ 本文件是 CARD-G3-2c-C（边界）的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十批手册 §三 X7-C 块。
> 批次标记 `[BATCH-2026-09-04-第十批 / CARD-G3-2c-C]`。前提：X7-B 已独立 commit。勘探 2026-09-04。

# CARD-G3-2c-C — 边界：字符轴 / 递归深度 / markerless legacy 一律 validator 硬拒绝（不再逐个修）

## 〇 原则
G3-2b 的 17 轮证明：字符轴（U+0085 / U+2028 / U+2029 / C1 / 代理对）与递归深度（500/512/640）是**开放集合**，每轮修一个就再生一个。本卡不再「支持」这些输入，而是把它们定义为**非规范输入**：validator 与写点同一判据、同为拒绝、拒绝时报真因；已存在的合法条目走**验证式 YAML emitter**（写→读回逐字节相等才落盘）。

## 一 事实（round-17 @56bfe9d4）
| 缺陷 | 位置 | 锚 |
|---|---|---|
| B② `q_` 字符轴只保护新条目；重建旧 receipt 时 U+0085 退化为空格（根因 `json.dumps(ensure_ascii=False)`） | `SKILL.md:1332`（`:1337`） | `_rebuilt.append(f"{_pfx}{_k}: {json.dump` |
| markerless 旧 receipt 迁移解析：`exam_board=1e+300` 裸值三处（validator / 写点 / 重跑）结论不一致 | round-17 MEDIUM | — |
| 「A hostile → B 追加 → 删 A 账本行 → 原样重跑 A」二次计分（attempt_count 2→3） | round-16/17 R-项 | — |
| 变异门 138/138 含 2 条语法错误假杀 + M141 等价性未证 | `g32b_mutation_gates.py` | — |

## 二 完成条件（AND）
- (a) 先红：板名 / event_id / 任一字符串字段含 U+0085、U+2028、U+2029、C1 控制符、孤立代理对时——validator 拒绝（报真因 + 码点），写点同判据拒绝；**不做** transliteration。
- (b) 验证式 YAML emitter：重建**已有**条目也走「emit → parse → 逐字节比对」，不等则拒绝并保留原文件（不止新条目）。
- (c) 先红：「A hostile → B 追加 → 删 A 账本行 → 原样重跑 A」必须 writer=1 拒写，禁二次计分。
- (d) 递归深度门：`exam_board` 32/384/512/640/768 层在 validator 与写点两侧结论一致（同上限、同为拒绝——与 B 卡 (d) 的常量同源，禁两处各写一个数）；禁「首写 0 / 重跑 1」不可恢复窗。
- (e) markerless 旧 receipt：`exam_board=1e+300` 裸值三处同结论（默认：按 legacy 解析规则显式定义并冻结进 §6.3 加性条款）。
- (f) 发布前类型敏感比对：`_reparsed["calibration_log"][:-1]` 与原 `_cur` 全部键值逐项相等（含类型），断言恰好新增一项。
- (g) 变异门清理：去掉 2 条语法错误假杀（判据须比失败身份，同一条断言才算杀）；M141 等价性给出证明或退役；输出杀灭表进验收单。
- (h) `docs/learning-events-schema-v1.md` §6.1 加性「字符轴规范输入集」+ §6.3 加性「markerless legacy 解析规则」，同批更新 195 门。
- (i) Codex 一轮（族累计上限已用，**本卡 1 轮**；只审边界 diff + 变异清理；附已裁决清单：开放集合不计、核心状态机已由 B 卡审）。

## 三 裁判命令
1. 同 B 卡裁判 1（四文件）全绿。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py -k "charaxis or depth or markerless or replay or emitter"` → 先红后绿。
3. `PYTHONDONTWRITEBYTECODE=1 …/.venv/bin/python scripts/validate_learning_events.py <各非规范 fixture>; echo rc=$?` → 每个非 0 且报码点/深度。
4. 变异脚本（串行、EXIT trap、逐字节还原）输出：指定门变红，无假杀。
5. live 零写同 B 卡裁判 5。

## 四 禁改与隔离 / Codex / 默认裁决 / 验收单
同 B 卡（live 只读、不部署、禁目录级 pytest、`*.stderr*` 不入库、不动台账、不 push）。Codex 命令换文件名 `codex-prompt-CARD-G3-2c-C.md` / `codex-review-CARD-G3-2c-C.md`，一轮为限。默认裁决：D1 非规范字符拒绝不转写；D2 上限常量与 B 卡同源单点；D3 markerless 规则冻结进 §6.3；D4 假杀变异退役。验收单 `UAT-CARD-G3-2c-C-边界硬拒绝-<日期>.md`：4-B「奇怪字符/超深结构会被明确拒绝并告诉你原因，而不是写坏账本」；「本卡未证明什么」必填（并发面 = G3-3）；「台账待登记条目」：三卡合入后 §一 G3-2b 行移 §二，`card/w7-ledger` 打 `merged-squash/w7-ledger-c-only`。
