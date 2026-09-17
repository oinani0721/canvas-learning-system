> 批次: BATCH-2026-09-11-第十四批 · 车道 T4-B · 卡 CARD-G6-10 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-10-r3.md)"`
> 审查绑定: `52bab59e0d43b2fca444a958410a8f07177fab89`（该轮的 HEAD；其后有整改 commit）
> 会话头自证（抄 .stderr 含 model 行，stderr 本身不入库）:
> L2: `OpenAI Codex v0.153.3` / L5: `model: gpt-6-astra` / L9: `reasoning effort: ultra`

---

复核绑定 **HEAD `52bab59e0d43b2fca444a958410a8f07177fab89`**。基线差异仅新增本卡两个文件；未修改文件、未运行 canary/pytest、未连接数据库。

**⓪ 结论：`--share-state` 确实制造了同一个 state 文件。** 两库父目录不同、basename 相同；生产 `_vault_key` 将 `resolve().name` 交给 `send_bark.vault_key`，相同输入得到相同 key，再由同一个 `BACKUPS` 拼出相同路径。最终失败判据比较 B 文件实际 SHA，没有替换 `_vault_key` 或翻转断言。

## BLOCKER

无。

## HIGH

### H1 — tempfile 兜底路径仍然先写后验，round-2 HIGH 未完全修复

**位置：** [g610_dual_vault_interaction_canary.py:315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:315)

只预验 `TMPDIR/TEMP/TMP`，平台默认目录和 cwd 仍等 `gettempdir()` 写完探针后才检查，因此 rc=2 不能保证受保护位置零写入。

**负控输入：** 三个变量未设或指向安全但不可用目录，平台默认临时目录均不可写，cwd 位于受保护 worktree/live vault；探针先在 cwd 写入、删除，随后才被拒绝。本轮无写检查也确认当前 cwd 在 tempfile 候选列表中。

## MEDIUM

### M1 — 禁写字节码晚于第一批 import

**位置：** [g610_dual_vault_interaction_canary.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:91)

`argparse/json/pathlib/tempfile` 等先导入，直到 :105 才设置 `sys.dont_write_bytecode=True`，仍存在守卫之前的字节码落盘窗口。

**负控输入：** 未开启解释器 `-B`，将 `PYTHONPYCACHEPREFIX` 指向真 `backups/` 下的新目录；首次导入可能在禁写生效前生成缓存，解释器启动阶段还可能更早发生写入。

### M2 — 本文件的两层 7691 检查都只判断字符串

**位置：** [test_g610_dual_vault_isolation.py:81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:81)、同文件 :359。

探针与自证都用 `":7691"` 子串判断，没有检查解析后的实际端口。

**未被拦下的输入：** `bolt://127.0.0.1:07691`；无网络解析确认其端口为 **7691**，但两处子串检查均放行。此结论仅针对本文件，**不代表已证明仓库 W4 也可被绕过**。

### M3 — Episode 正向对照不能证明本次确实新增了复习记录

**位置：** [test_g610_dual_vault_isolation.py:332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:332)、同文件 :390。

seed 分数检查只覆盖 LEARNED，Episode 只要求非空；A 的正控又只检查是否存在 95 分，没有排除它在复习前已经存在。

**门未覆盖的路径：** seed 的 Episode 错写为 95，随后复习只更新 LEARNED，Episode 写返回成功却不新增；旧 95 足以通过正控，而两条负控仍可在 LEARNED 第一项命中预期异常，整门可能绿。

### M4 — 总账 :983 的字面要求仍未闭合

**位置：** [g610_dual_vault_interaction_canary.py:596](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:596)、[test_g610_dual_vault_isolation.py:127](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:127)。

canary 导入的是标识常量，随后仍新建 tmp fixture vault；门文件另建字面量，故尚未满足所引述的“禁止另建 tmp fixture vault／强制复用”字面要求。

**对照输入：** 按总账原句逐项验收，两处仍应记为未满足，不能由“已经登记待裁”替代通过；避免共享容器互删的理由在机制上合理，但不足以自行批准例外，G2-9 实际清理语句也不在本轮读取面内。

## LOW

### L1 — 7691 自证仍被整文件 skipif 覆盖

**位置：** [test_g610_dual_vault_isolation.py:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:104)、同文件 :357。

环境自证与数据库测试一起跳过，仍不能独立提供拒绝现网的执行证据。

**对照输入：** URI 为字面 7691，或容器不可达，自证测试同样 skip；所述外部证据文件不在本轮读取范围，未予采信。

### L2 — 帮助输出仍能产生非隔离原因的 rc=1

**位置：** [g610_dual_vault_interaction_canary.py:685](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:685)

`parse_args()` 位于新增输出异常边界之外，中文帮助输出失败仍会以 rc=1 结束。

**负控输入：** `PYTHONIOENCODING=ascii … --share-state --help`；隔离流程尚未开始便发生编码异常，本轮仅用独立标准库示例确认了该异常及退出码。

## 其余问题的核对结论

- **① 生产写路径复用正确。** loader 的同模块对象核验成立，显式 vault 参数贯穿 state、锁和写辅助，`BACKUPS` 补丁覆盖已读到的 state 与锁路径；但 `_state_tmp_path` 定义不在指定区间，不能宣称已独立重算全部临时件落点，H1/M1 也使“所有写之前均通过白名单”不成立。
- **② 负控失败归因可信。** 两处 `pytest.raises` 只包 `_assert_group_b_intact`，写入、采样、fixture 和连接异常均在外；marker 足以区分这些错误。手写读与生产读分开验证的边界已明确声明。
- **③ skip 文案清楚。** :50–51 明写“skip 不是 pass／本卡未证明”；消费方是否错误地只看退出码，不在本轮范围。
- **⑤ canary 的 P1/P2 有效。** SHA 变化加实际 JSON 值回读，排除了“两库都没写”；P3 是自报一致性检查，单独不足，但没有替代 P1/P2。门的 Episode 正控仍有 M3。
- **⑥ 只能确认手工派生链，不能确认完整生产派生。** canary 使用 `sanitize_vault_id(vault.name)`，注释明确限定无 `.canvas-config.yaml` 情形；获准读取面未包含 `Settings.vault_id` 与兼容转换定义，因此未将“真实 vault 必然同 group”判为已证。
- **其余整改：** Episode 先清、Node 后清的顺序已修正，无范围孤儿删除已移除；但 `record_score_history` 实现不在读取面，无法独立确认“本门绝不产生无 group 且无边残渣”的绝对声明。进程级禁写字节码对独立 canary 未见改变业务语义的副作用，主要缺陷是生效太晚。

**计数：BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 2。**


