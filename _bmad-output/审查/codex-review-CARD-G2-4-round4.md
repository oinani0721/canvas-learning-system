1. round-3 HIGH 残余 — CONFIRMED-CLOSED

[脚本:249-284](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:249>) 已递归渲染 struct 子字段 metadata，[脚本:299-310](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:299>) 据此生成摘要。原反例实跑：

- 无/cm/m 的 `schema_sha16`：`b19120254fb27bf2` / `853b523c38faaffd` / `75a5c84144ebee53`
- Arrow 的“无 vs cm”“cm vs m”均为 `False`，摘要也均判异；三者内容指纹相同。
- 强制把 `{unit:cm}` 回读成无子字段 metadata：[脚本:343-358](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:343>) 返回 `reconciled=False`，before/after 为 `853b…` / `b191…`；[脚本:435-449](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/scripts/archive_legacy_lance_tables_g24.py:435>) 会整批 abort，不进入 drop。回归锁见[测试:251-280](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:251>)。

回归检查

- BLOCKER-1 — CONFIRMED-CLOSED（未重开）— URI fail-closed 见脚本:95-113；零动作锁见测试:392-403，本轮通过。
- BLOCKER-2 — CONFIRMED-CLOSED（未重开）— DB 树内归档拒绝及两阶段 drop 仍在脚本:394-403、435-449；真实 schema-repair 锁见测试:559-606，本轮通过。
- BLOCKER-3 — CONFIRMED-CLOSED（未重开，限定证据）— round-3 存档:28 记录 exact-byte 未变；round-4 宽套件中 `test_vault_doc_roles` 全绿见 `post-fix-suite-round4.txt:542-660`。按读取边界未重开范围外三文件复算。
- HIGH-2 — CONFIRMED-CLOSED（未重开）— 应用 sanitizer/fail-closed 见脚本:116-137；测试:369-386 通过。
- HIGH-3 — CONFIRMED-CLOSED（未重开）— `unknown_bare` 与 pending 见脚本:140-153、333-337；测试:108-125 通过。
- round-3 顶层 metadata — CONFIRMED-CLOSED — 脚本:237-246、266-272；测试:162-182 通过。
- ⑤端到端 — CONFIRMED-CLOSED — 独立 Arrow metadata oracle、归档和 drop 断言见测试:327-363，本轮通过。
- 定向整文件实跑：`22 passed, 16 warnings`；不等同全 CI 通过。

⑦⑧④ 死门审查

- ⑦ — 死门（针对“递归”声明；原一层反例本身有效）— `/tmp/card-g24-r4-mutations.voPyOv/flat_struct/` 只扁平渲染直接 struct 子字段、不继续递归，完整测试仍 `22 passed`。双层 struct 实测 Arrow=False、canonical 摘要判异，但变异摘要同为 `cc76acc2c763c87c`。
- ⑧ — 死门（递归层；顶层锁有效）— `/tmp/card-g24-r4-mutations.voPyOv/top_level_elem/` 仅顶层归一 `item/element`，完整测试仍 `22 passed`。真实嵌套 list Parquet 往返 canonical 摘要相同 `03224a4e644f8114`，变异却为 `0dd659eacb8120b1` / `66d9eaf92fca250b`。
- ④ — 死门（总体；key-only 子维度有效）— 上述 `flat_struct` 绕过④且全绿，证明[测试:202-248](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/tests/unit/test_archive_legacy_lance_tables_g24.py:202>)仍未锁全深度递归。另一种 key-blind 变异 `/tmp/.../key_blind/` 则使④按预期红：`1 failed, 21 passed`，故 key 修复有效。

LOW×3 处置

- export_table 行号 — 未落实：UAT:388-389、545-546 写“现位于 306-321”，当前实际为脚本:343-366，对账为:347-358。
- “297 collected” — 已落实：UAT:441 已改为 `4542 collected / 297 selected`。
- 变异 SHA 对照 — 未落实：当前脚本完整 SHA-256 确为 UAT:537 声明的 `cc5b…704d05`；但 `c-mutation-red-round4.txt:6` 仅有 `restore-identical=True` 和 16 位前缀，没有前后完整 hash、命令或四次恢复记录，证据包仍不能独立复算。

证据引用核对

- 四文件均存在；核心结果与 §8.8 字面相符。
- `a-judge-probe-round4.txt:1` 为 `True`，但没有输入/命令绑定。
- `c-mutation-red-round4.txt:2-5` 的四组失败数相符；自检信息不完整。
- `post-fix-suite-round4.txt:7,370-391,661-674` 证明 304 selected、G24 22项通过、最终 `13 failed / 291 passed`。
- `comm-new-failures-round4.txt` 为 0 bytes，符合“0行”，但自身没有 baseline 或比较命令绑定。

新问题分级

- BLOCKER：无。
- HIGH：无。
- MEDIUM：⑦/④可被单层扁平 struct 绕过；⑧可被仅顶层 elem 归一绕过。均为回归门缺口，当前生产实现实测正确，未重开 HIGH。
- LOW：export_table 行号仍漂移；变异证据不自包含；UAT:543 的 `291 = 284 + ⑦⑧` 少算 round-3 新增5项，正确为 `284+5+2=291`；四份新证据未绑定 UAT:541 所称 grep gate `rc=0`。

BLOCKER/HIGH 清零：是


