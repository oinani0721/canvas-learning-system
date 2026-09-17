> 批次: BATCH-2026-09-11-第十四批 · 车道 T4-B · 卡 CARD-G6-10 round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-10-r5.md)"`
> 审查绑定: `4da1eb24e797b9f0525ec02b1879480b3dc15786`（= 本卡最终 HEAD，绑定按同一 commit 成立）
> 会话头自证（抄 .stderr 含 model 行，stderr 本身不入库）:
> L2: `OpenAI Codex v0.153.3` / L5: `model: gpt-6-astra` / L9: `reasoning effort: ultra`

---

复核 HEAD：`4da1eb24e797b9f0525ec02b1879480b3dc15786`。未改文件、未运行 canary/pytest、未连接数据库；基线 diff 确认只有两个新增文件。

**⓪ 结论：`--share-state` 确实制造了同一个 state 文件。** canary 创建不同父目录、相同 basename；`daily_review_run.py:78` 取 `resolve().name`，`send_bark.py:61–66` 对相同输入生成相同 key，随后使用同一 BACKUPS。最终红因来自 B 文件 SHA 改变，没有替换 `_vault_key` 或翻转断言。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

### M1：切回 A 的生产读仍可能夹带 B 的账而全绿

- **位置**：[test_g610_dual_vault_isolation.py:479](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:479)
- **问题**：新增正控只检查 A 的生产读包含 `95`，没有排除 B 的记录；生产 seed 检查也仅要求非空，因此 round-4 M1 只闭合了“看得到新写”。
- **门未覆盖的输入**：A 的生产读返回 `A95 + B40`，B 的生产读始终正确返回 `B40`，手写 scoped 查询保持正确——现有正例和两条负控仍全部通过。

### M2：复用常量没有满足“不另建 tmp fixture vault”

- **位置**：[g610_dual_vault_interaction_canary.py:633](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:633)、[test_g610_dual_vault_isolation.py:23](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:23)
- **问题**：canary 确实重新创建并填充临时 vault，门文件也使用自有资产常量；按你提供的总账原文，这仍是实质偏离，登记待裁不等于已经获得豁免。
- **对照输入**：G2-9 集合发生变更时，canary 的导入常量会同步，但门文件的 `g610gate` 常量不会同步，且 canary 依然另建 fixture。

避免共享容器清理互删的工程理由合理；限定读取面不包含 G2-9 清理语句，具体互删范围本轮无法独立确认。

## LOW

### L1：匹配行数加一仍不等于新增 Episode 实体

- **位置**：[test_g610_dual_vault_isolation.py:468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:468)
- **问题**：`:320–339` 的查询返回 `SCORED` 匹配行，不返回 Episode 身份，故 `len + 1` 与旧元组保留不能证明新增 Episode。
- **门未覆盖的路径**：复用原 Episode，保留 `40` 分边，再添加 `95` 分的 `SCORED` 边；“有 95、行数加一、旧记录仍在”全部满足。

### L2：“全部落盘经过 tmp_root 白名单”仍超过实际覆盖

- **位置**：[g610_dual_vault_interaction_canary.py:631](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:631)
- **问题**：第三方 import 发生在创建 `tmp_root` 和执行白名单之前，只受 `tmp_base` 检查与临时目录设置约束，不能归入全部路径均经过 `_assert_write_surface_is_tmp` 的声明。
- **门未覆盖的路径**：第三方 import 使用所钉的 `tmp_base` 创建缓存时，缓存位于 `tmp_root` 外，也不受最后仅清理 `tmp_root` 的操作覆盖。

这不是已证明会写真 backups 的漏洞。

### L3：7691 自证门仍不是独立第三层

- **位置**：[test_g610_dual_vault_isolation.py:404](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:404)
- **问题**：自证测试仍受模块级 `skipif` 控制，危险 URI 被拒时，其自身断言也不会执行；代码已如实披露，但覆盖缺口仍在。
- **负控输入**：`NEO4J_TEST_URI=bolt://127.0.0.1:07691`，模块拒跑同时跳过自证测试。

## 其余问题核对

- **① 写入边界**：已核实 runner 对象复用、BACKUPS 补丁以及 state/lock 路径检查；round-4 的 `TMPDIR=/System + TEMP=<生产 backups>` 会在 import 前被拒。`_state_tmp_path` 定义不在允许区间，不能把“临时件同目录”认作本轮已逐行验证的实现。
- **② 负控红因**：成立。两个 `raises` 块内都只有隔离断言调用；import、fixture、连接和取样在块外，异常类型加 marker 足以区分这些失败。
- **③ skip**：文件明确写了“skip 不是 pass”“本卡未证明”，表述清楚；验收不能仅凭 pytest 退出码判绿。
- **⑤ 正控**：canary 的 P1/P2 读取真实文件，能排除完全未写；P3 单独属于自报对照，但未被独自用作落盘证据。门的原始查询也证明 A 确有变化，残留见 M1、L1。
- **⑥ group 派生**：代码证明的是自行构造的 basename 派生场景；docstring 提到了无 `.canvas-config.yaml` 的条件，但没有调用生产 vault 身份解析入口。限定读取面缺少该解析实现，因此本轮不能确认它与真实 `Settings.vault_id` 完全一致，也不能推广为“同 state 必然同 group”。

**计数：BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 3。**


