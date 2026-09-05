> ⚠️ 本文件是 CARD-CX-G3-2c-C-R1 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z6-A 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-CX-G3-2c-C-R1]`。车道：复用 `card-x7-ledger-c`（主 session 已预合主干 `304f03ca`，venv symlink 已建）。同车道串行 **Z6-A（本卡）→ Z6-B（g32cb 去硬编码 + q_ 承重）→ Z6-C（g32b 138 全量表）**。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-CX-G3-2c-C-R1 — X7-C `991ae914` + `ae53fa05` 补审：字段级字符轴判据自洽 + emitter 门承重（1 轮 Codex）

## 〇 事实
| 事实 | 位置 |
|---|---|
| 两 commit 均为整改后**无复审**：`991ae914`（6 文件 338+/100-；代码面 `validate_learning_events.py` 104 行、`test_g3_2_review_ledger.py` 140 行、`g32cb_mutation_gates.py` 6 行、`docs/learning-events-schema-v1.md` 8 行）与 `ae53fa05`（emitter 门换承重载体） | `git show --stat` |
| `991ae914` 把 `value_charset_problems` 从「遍历整条 record 每个字符串（含 dict 键）」收窄为只查 `CHARSET_STRICT_FIELDS` 五路径：event_id / node_id / payload.vault_id / payload.concept_id / payload.exam_board（`validate_learning_events.py:1618-1624`）——收窄的原因是整条 record 判据实测复现**数据丢失路径**（多行批注 → 该节点从此评不了分） | validate_learning_events.py |
| **判据自相矛盾**：收窄分界写的是「该字段会不会逐字进入 YAML receipt 或参与身份比较」（`:1613-1615` 注释），而 `ae53fa05` 的门 docstring 明写 `self_confidence_raw`「会逐字进入 receipt（经 q_() 编码）但不在账本 payload 键集里，因此不受 §6.1 约束」——存在满足判据前件却不在严格字段表内的字段 | `:1613-1615` vs `test_g3_2_review_ledger.py:6035-6055` |
| `value_charset_problems` 对非 dict 入参直接返回空列表（`:1662-1663`）——record 不是 dict 时静默放行 | validate_learning_events.py |
| `ae53fa05` 的逐字节判据是**子串包含** `assert _snap_A in nd_after`——行被复制或位移仍会绿 | test_g3_2_review_ledger.py |
| M8 变异靠**硬编码源码字面量**匹配 SKILL 一行（`g32cb_mutation_gates.py:127-136`，含前导 20 空格）；缩进变动会让变异静默失配，8/8 KILLED 变假绿 | g32cb |
| ⚠️ 若 (a) 判成「需扩表」，会撞上 `991ae914` 修掉的数据丢失路径的反方向——扩表可能重新误拒真实输入。**先出「扩表后 65 个真实路径拒绝数仍为 0」实证再动手** | 风险 |

## 一 完成条件（AND）
- (a) 判据自洽性定性（核心）：把「逐字进入 YAML receipt 或参与身份比较」穷举展开——列出所有逐字进 receipt 的字段（至少含 `self_confidence_raw`），与 `CHARSET_STRICT_FIELDS` 五项做差集；差集非空即判据与实现不一致。三选一落定并写理由：① 扩表（须先过「65 真实路径拒绝数 = 0」实证）；② 改判据措辞收窄成「身份键 + payload 内 receipt 载体」；③ 如实登记为已知缺口。不得含糊。
- (b) 收窄是否放过真实缺陷：对差集里每个字段实测「写得进 receipt、读不回原值」是否可达（沿用 U+0085 载体形态），rc 与账本行数逐条落证据；可达则定性（数据丢失 / 召回损失 / 仅显示畸形）。
- (c) `:1662` 非 dict 静默放行：给出调用点 `:1715` 是否可能收到非 dict 的实证；不可达也要写「为什么不可达」。
- (d) 子串包含判据：构造「A 行被复制成两行」与「A 行位移」两个变异实测门是否仍绿；绿则补「行序 + 出现次数」判据。
- (e) M8 硬编码字面量：加「变异串必须在目标文件恰好命中 1 次，否则脚本非零退出」自检。
- (f) 一轮 Codex（gpt-6-astra ultra）绑本卡最终 tip，审查面显式钉 `git show 991ae914 -- <3 代码文件>` 与 `git show ae53fa05`；§四 已裁决写入 X7-B D1-D7（按默认）与 §6.2 duplicate/markerless 已移交。

## 二 裁判命令
1. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py` → 335 passed + 1 skipped 不回退（新门只增）。
2. `… $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py -k "charset or emitter or charaxis"` → 全绿（含 (d) 新判据先红后绿）。
3. `cd <树> && G32CB_PYTEST=<venv>/pytest <venv>/python backend/scripts/g32cb_mutation_gates.py` → 8/8 KILLED；跑前跑后 `shasum -a 256` 目标文件相同（**若 Z6-B 尚未做，`:47-49` 仍硬编码 card-v5-lance venv，该路径目前存在可跑**）。
4. `shasum -a 256 /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/学习事件/learning_events.jsonl 2>/dev/null || echo NOFILE` → 开工与收工两次输出相同（live 零写）。
5. `… $PYTEST -q -p no:cacheprovider tests/skills` → 369 绿起（本卡若碰 SKILL.md 必跑；不碰也跑一次取证）。

## 三 禁改与隔离
禁把字符轴改回「整条 record」（已实测数据丢失路径）；禁改 §6.2 duplicate / markerless 语义面（已移交）；禁改 `docs/learning-events-schema-v1.md` §6.1 契约而不同步改门与一致性断言；禁改 quiz-answer SKILL.md 语义与 `learning_event_log.py`（Z2 面）；变异脚本跑完无条件还原 + sha 对比；**变异 harness 时段与 Z6-B/C 串行（同车道自然满足）**；live vault 只读；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-CX-G3-2c-C-R1.md` → `codex-review-CARD-CX-G3-2c-C-R1.md`，1 轮）。验收单 `…/验收单/UAT-CARD-CX-G3-2c-C-R1-<日期>.md`：DoD-3 双段；4-B「无变化（把上批自己改的两处请第三方看了一遍，并把说法和代码对齐）」；「本卡未证明什么」必填；「台账待登记条目」必填。commit header ≤100 含批次标记，body 行 ≤100；不 push。**commit 后同车道继续 Z6-B。**
