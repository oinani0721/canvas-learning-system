> 批次: BATCH-2026-09-05-第十一批 · Z6-B · CARD-G3-2c-E round-1（首部由主 session 2026-09-05 按协议 §2.1 补记，正文一字未改）
> 模型: `gpt-6-astra`（stderr 实测） · reasoning_effort: `ultra`（stderr 实测） · codex: 未自证（stderr 无版本行）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt>)"`（第十一批手册规定形态；实参见车道 stderr）
> 审查绑定: 见正文；LOW 整改后 `_run_gate` except OSError 未复核（台账 §一.b）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `workdir: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c` / `model: gpt-6-astra`

---

需整改

[LOW] [backend/scripts/g32cb_mutation_gates.py:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/g32cb_mutation_gates.py:80) — 环境变量路径只检查存在，未规范化或验证可执行性，仍会绕过“明确报错”而抛裸异常。

独立实测：

- 指向本仓库脚本文件：选择器接受，随后 `PermissionError(errno=13)`，没有回落。
- 从工作树根设置 `G32CB_PYTEST=backend/.venv/bin/pytest`：该路径存在，但执行时第 214 行切换到 `backend/`，随后 `FileNotFoundError(errno=2)`。
- 建议：先将路径解析为绝对路径，检查 `is_file()` 和执行权限；捕获启动时的 `OSError`，错误明确包含变量名、解析路径和原因。在变异前验证 pytest 身份，避免把配置错误报成防线失效。

未发现本 diff 引入评分少记、多记的缺陷；M9 的实际承重成立。七项复核如下。

1. **M9 承重，失败确实在①。**  
   按第 184 行锚点仅改 `ensure_ascii=True → False`，新门 pytest `rc=1`，首个失败是 [test_g3_2_review_ledger.py:6371](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6371) 的 `r.returncode == 0`。另行直接运行写点得到：`writer rc=1`、账本 **0 行**、节点 SHA 不变；stderr 明确为 `半\x85懂` “无法编码成能原样读回的 YAML 标量”。

2. **不挂 depth 层成立，但不能解释成没有其他检查参与。**  
   拒写来自 [SKILL.md:1274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:1274) 的第二次往返自证，这是 `q_()` 内部预期机制。第 2727 行落账前预演调用它，第 2728 行原样传播 `SystemExit`。未发现外部 depth 或字符轴贡献此次击杀；外围 YAML 重建检查尚未执行到。

3. **两种失败身份确实不同。**  
   拆自证使用真实 E4 替换：将第一条往返比较条件改成 `if True`。

   | 对照 | pytest rc | 写点 rc | 账本行数 | 首个失败 |
   |---|---:|---:|---:|---|
   | 无变异 | 0 | 0 | 1 | 无 |
   | M9：拆回落 | 1 | 1 | 0 | ①，第 6371 行 |
   | E4：绕过自证 | 1 | 0 | 1 | ②，[第 6382 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6382)，缺少 `\u0085` |

   基线 receipt 为 `"\u534a\u0085\u61c2"`，读回原值；E4 写出裸 NEL，读回变成 **“半 懂”**。E4 没有先被别的拒写路径拦住。

4. **当前输入没有被无关原因“喂饱”。**  
   [test_g3_2_review_ledger.py:6357](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/tests/regression/test_g3_2_review_ledger.py:6357) 重置新节点和空账本；第 6379 行按 `"\n"` 分行，不会误把 NEL 当行界。第 260 行的恢复重试只匹配“恢复已落定”，此次 M9 不匹配。基线直接观测为 `fsrs=applied`、库版本 `6.3.1`、`attempt_count=1`，不是依赖缺失造成的假降级。

5. **三段选择与 g32b 同形态，但错误提示覆盖不完整。**  
   未设变量、变量指向不存在路径，两者均选择本车道 venv；在内存中令本地路径也不存在，得到预期中文 `SystemExit`。与 [g32b_mutation_gates.py:497](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/g32b_mutation_gates.py:497) 的对应分支行为一致。
   
   对真实非 pytest 程序运行完整脚本：`/usr/bin/true`、`/bin/echo` 均让绿态前提通过，但最终 **0/9 KILLED、脚本 rc=1**；`/usr/bin/false` 在前提阶段中止，脚本 `rc=2`。这些误配没有误报整体成功，但诊断不能明确指出“配置的不是 pytest”。

6. **四段防护没有改动。**  
   我将当前源码与 `git show e22ad10a:…` 逐字符比较：[g32cb_mutation_gates.py:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/g32cb_mutation_gates.py:223) 的 `_self_heal` 起至文件末尾，结果 **完全相同**。因此第 300 行 SHA 基线、第 307 行绿态前提、第 328 行 KILLED 判据、第 339 行还原及第 341 行跑后复核均未改。`_run_gate` 也仅有指定的选择器替换。独立字符串计数为旧车道字面量 **0**、`G32CB_PYTEST` **3**。

7. **当前可达性支持采用 M9；历史因果不据此追认。**  
   [validate_learning_events.py:1648](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/backend/scripts/validate_learning_events.py:1648) 实际五路径为 `event_id`、`node_id`、`payload.vault_id`、`payload.concept_id`、`payload.exam_board`。实调字符检查：顶层或 payload 内的 `self_confidence_raw="半\u0085懂"` 都返回 `[]`；放进 `payload.exam_board` 则明确拒绝 `U+0085`。
   
   [SKILL.md:2711](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x7-ledger-c/canvas-vault/.claude/skills/quiz-answer/SKILL.md:2711) 的真实落账 payload 恰有 **11 键**：`schema_ext`、`vault_id`、`concept_id`、`rating`、`grade_norm`、`review_time`、`scored_at`、`fsrs_library_version`、`fsrs_params_hash`、`exam_board`、`attempt_count`。没有 `self_confidence_raw`；该值在第 1320 行直接进入 `q_()`。所以当前载体可达，但仅凭当前文件不能证明“历史上恰因字符轴收窄才首次可达”。

完整独立运行结果为 **rc=0、9/9 KILLED**。测试在真实文件的隔离副本运行，使用本地开发配置完成应用收集；源文件未修改。两组对照和全量运行后，`SKILL.md` SHA 均为：

```text
dd6d4e4b8d6b47f4ab57dc64f32f00982a4558848141c7c4434015c8cfa73dbf
```

[独立证据与复现说明](/tmp/g32ce-independent-dr3n62hd/README.md) · [归因观测](/tmp/g32ce-independent-dr3n62hd/attribution-results.json) · [全量运行输出](/tmp/g32ce-independent-dr3n62hd/full-g32cb.txt)
