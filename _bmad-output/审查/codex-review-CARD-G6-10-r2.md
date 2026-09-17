> 批次: BATCH-2026-09-11-第十四批 · 车道 T4-B · 卡 CARD-G6-10 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-10-r2.md)"`
> 审查绑定: `ca5a50ad3142e1813a969b7dd8c27a65920e008b`（该轮的 HEAD；其后有整改 commit）
> 会话头自证（抄 .stderr 含 model 行，stderr 本身不入库）:
> L4: `OpenAI Codex v0.153.3` / L7: `model: gpt-6-astra` / L11: `reasoning effort: ultra`

---

当前 HEAD 为 `ca5a50ad`。**同 state 文件的负控构造可信，但落盘安全整改尚未闭合。**本次仅做静态复核，未改文件、未运行 canary／测试、未连接数据库；以下负控输入均未执行。

**BLOCKER：无。**

**HIGH：1**

- [backend/scripts/g610_dual_vault_interaction_canary.py:267](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:267)：`tempfile.gettempdir()` 首次选择临时目录时会创建探测文件、写入内容再删除，因此 `:271` 的拒绝仍晚于首次落盘，r1 HIGH-1 未完全修好。  
  **负控输入**：新进程中将 `TMPDIR` 指向可写的受保护目录；即使最终 rc=2，该目录也已经发生探测写入。

**MEDIUM：4**

- [backend/scripts/g610_dual_vault_interaction_canary.py:237](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:237)：禁写字节码只覆盖 runner 的 `exec_module`，未覆盖 `:112`、`:122` 的顶层 import，以及恢复开关后的 `:553`，这些路径仍可向真实仓库写 `.pyc`。  
  **对照输入**：普通 Python 启动，未设置 `-B`／`PYTHONDONTWRITEBYTECODE`，且相关模块没有有效缓存；项目 import 即可在白名单之外创建 `__pycache__` 文件。

- [backend/scripts/g610_dual_vault_interaction_canary.py:647](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:647)：异常归类只包住 `run()`，报告输出仍在外面，输出异常可以让隔离成立的运行以 rc=1 退出，r1 MEDIUM-3 未完全修好。  
  **负控输入**：设置 `PYTHONIOENCODING=ascii` 并重定向 stdout，中文报告触发未捕获的 `UnicodeEncodeError`，其 rc=1 与隔离失败重合。

- [backend/tests/integration/test_g610_dual_vault_isolation.py:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:157)：新增孤儿清理没有 `g610gate` 范围条件，会删除共享容器中其他任务的无 group、无边 scoring Episode，是整改引入的越界清理。  
  **对照输入**：容器中预置一条属于其他任务的此类 Episode，本卡 fixture 的前置或后置清理都会删除它。

- [backend/scripts/g610_dual_vault_interaction_canary.py:555](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/scripts/g610_dual_vault_interaction_canary.py:555)、[backend/tests/integration/test_g610_dual_vault_isolation.py:128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:128)：按所提供总账原文，canary 导入常量后仍另建 tmp fixture vault，门又自行定义资产标识，尚未满足“强制复用、禁止另建”的要求，r1 MEDIUM-7 仍未闭合。  
  **对照输入**：只调整 G2-9 的攻击用例常量，canary 会跟随，门仍使用旧的自有定义；避免并发互删的理由不能自行替代总账约束。

**LOW：1**

- [backend/tests/integration/test_g610_dual_vault_isolation.py:350](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-g3/backend/tests/integration/test_g610_dual_vault_isolation.py:350)：7691 自证测试仍受模块级 `skipif` 控制，不能算独立执行的第三层门，r1 LOW-1 保留。  
  **负控输入**：`NEO4J_TEST_URI=bolt://127.0.0.1:7691`；文件内探针返回 False 后，自证测试也被 skip，外层 W4 若先阻断则它同样不会执行。

其余重点核对结论：

- **⓪ 碰撞成立。** canary `:323–325` 只改变 B 的 basename；生产 `_vault_key` 取 `resolve().name`，`send_bark.vault_key` 对相同输入给出相同 key，再由同一个 `BACKUPS` 拼出同一路径。隔离失败最终来自 B 文件 SHA 变化，并非把路径相等断言直接当作 rc=1。
- **① 显式 state／锁路径受补丁覆盖。** `state_locked` 的父目录创建及 `O_CREAT` 使用该锁路径；但“全部落盘已检查”被上述启动路径反例否定。`save_state` 的临时件委托 `_state_tmp_path(state)`，其定义不在允许读取范围内，本轮不能独立确认全部临时件路径。
- **② 负控失败位置已正确限定。** 两处 `pytest.raises` 只包 `_assert_group_b_intact`，连接、fixture、读写异常均在外；指定 marker 足以区分这些错误。读侧前后均用无 scope 快照，另有带 scope 对照，r1 HIGH-2 已修。两条负控会在 LEARNED 比较处先抛错，不能据此宣称另外两个 facet 的负控敏感性也各自得到验证。
- **③ skip 声明清楚。** `:50–51` 明写“skip 不是 pass／本卡未证明”；但全 skip 仍可能返回 pytest rc=0，不能只凭退出码验收。
- **④ 并发互删理由有工程合理性，但未获独立证实。** 指定的 G2-9 读取片段不含清理实现；即使理由成立，也未消除上述总账偏离。
- **⑤ 正向对照有效。** canary P1/P2 同时检查实际文件变化和两笔预期内容；P3 单独只是返回路径一致性证据。门内 A 的两类复习分数均有回读检查，B seed 也检查非空，排除了“两边都没写”的假绿。
- **⑥ group 生产派生尚未证明。** canary 确实手工将 `va.name`／`vb.name` 送入派生链；docstring 限定了无配置文件的回退情形，但允许读取面不含 `Settings.vault_id` 实现，无法独立确认其描述。`_snapshot_raw` 已明确声明手写查询并与生产读取分开验证，不能据此视为两者语义等价。

指定 diff 确认仅新增两个目标文件，生产文件没有改动。

**计数：BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 1。**
