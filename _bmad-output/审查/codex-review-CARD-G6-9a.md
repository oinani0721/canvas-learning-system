> 批次: BATCH-2026-09-05-第十二批 · 车道 Y3 · 卡 CARD-G6-9a round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`/opt/homebrew/bin/codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-9a.md)"`
> 审查绑定: **不绑最终版本 / 审工作区**。Codex 自述读取版本 534 行、SHA-256 `9c52291d…08b0109`；本卡定稿版本 SHA-256 `8d803c277ff754b9676079c1067c9f011c2188bc25336960c911f4c1ce3b212a`（7 条整改后），commit `d393fd2e`。差异 = 本轮 7 条整改**未经复核**（失绑，已登记于验收单「台账待登记条目」#7 与「本卡未证明什么」#15）。
> 会话头自证（抄 `.stderr` 含 model 行，stderr 本身不入库，`.gitignore:261` 覆盖）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**暂不建议本卡收官：发现 3 项 HIGH、2 项 MEDIUM、2 项 LOW，未另列 BLOCKER。**

复核期间文件从 497 行变为 **534 行**；以下按最后稳定读取的版本定位，SHA-256 为 `9c52291d…08b0109`。本次未修改文件、未运行完整 pytest、未触发通知或定时任务；另在独立子进程中验证了原时区夹具和矩阵字面值。

1. **HIGH — 8 条已登记用例逻辑上不可能 XPASS，`strict=True` 没有实现修复提醒。**  
   位置：[测试:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g6_9_boundary_matrix.py:147)，以及 178、182 行。  
   事实：178 行要求实际日期对等于登记的两个**不同**日期；182 行又要求实际两个日期**相同**。两条断言不可能同时通过。整条用例的 xfail 还会吞掉登记过期、显示侧交叉验证失败等非预期错误。因此，即使接入真实 runner 并统一时钟，也会先在旧登记核验处失败，仍成为 XFAIL。裁判输出 70–77 行展示的是预设 reason，不能证明具体失败落在最终日期比较。  
   **建议：**限定 xfail 只接收“已核实的已知分叉”；登记不符应普通失败，日期统一后应允许测试通过，从而触发严格 XPASS。

2. **HIGH — TZ 确实改变了进程时区，但矩阵没有测真实 runner 的归日结果。**  
   位置：[测试:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g6_9_boundary_matrix.py:162)，生产 `daily_review_run.py:214–220`。  
   事实：矩阵在 163–164 行自行执行 `instant.astimezone().date()`，没有调用 runner；167–168 行也复制了显示换算公式，只有 `_sh_day` 是真实生产 helper。修改 runner 的 215–216 行不会改变矩阵观测。  
   **建议：**保留夹具自证，通过临时 vault 调用真实 runner，并读取其落账日期；当前矩阵只能证明所复制公式的边界。

3. **HIGH — 裁判输出没有绑定当前提交审查的测试版本。**  
   位置：[环境绑定证据:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g69/env-and-binding-20260906T104742.txt:13)。  
   事实：证据声明全部输出绑定 `27483f5d…65df`，当前文件却是 `9c52291d…08b0109`，且新增了缓存失效和 Bark 内容检查。因此原来的 **15 passed、8 xfailed** 及静态检查结果不能直接证明新版通过。  
   **建议：**稳定最终测试文件后，重新生成与其 SHA 绑定的裁判输出。

4. **MEDIUM — launchd 门只确认两份仓内源码没有显式 TZ，完整运行链结论读取面不足。**  
   位置：[测试:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g6_9_boundary_matrix.py:205)，wrapper 3–5、16–17、112 行，plist 12–15 行。  
   事实：plist 指向已安装的 wrapper；仓内 wrapper 自述只是源码副本，并调用另一个 worktree 的 `daily-review-push.sh`。这些实际执行对象没有被该门绑定。PATH/XML 锚只能证明读到了相应文本；字符串搜索也不验证有效赋值。Web 侧 1317 行的强制赋值确实存在。  
   **建议：**结论收窄为“本 checkout 的这两份资产未显式设置 TZ”；“整条已部署链没有任何 TZ 固定”标记为**读取面不足**。

5. **MEDIUM — 四关键词零命中不能证明 UI／JSON 完全不可见，正面锚也未验证“不碰”的含义。**  
   位置：[测试:499](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g6_9_boundary_matrix.py:499)，513–532 行。  
   事实：runner 锚可以发现关键词在生产者中消失，却不能证明消费者必须使用这四个字面量；通用 state 透传、别名或扫描范围外的消费不受约束。532 行只查文件名，即便注释改成“读取该文件”也能通过。  
   **建议：**将门及结论限定为“四个专属字符串在 backend/app 的 Python 文件中零引用”。实际 UI／响应的全面不可见性，**读取面不足**；不能由该扫描代替行为证据。

6. **LOW — 零产品源码变更有支持，但不能扩张成测试期间零文件写入。**  
   位置：[零改动证据:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/_bmad-output/审查/evidence-g69/no-product-code-and-live-untouched-20260906T104908.txt:5)，以及 7、13–18 行。  
   事实：diff 和 status **都明确覆盖 backend/lib 与 scripts**，本次复查也为空；但普通 status 不观察 ignored 缓存或写后恢复。测试顶层导入 scripts 模块，是可能产生字节码的路径；缓存证据只检查 live vault。当前两目录确有 ignored `__pycache__`，但**无法归因于本次测试**。两个 live SHA 相同也只证明最终内容相同。  
   **建议：**保留“零产品源码变更、两份 live 产物前后字节一致”的准确表述。

7. **LOW — 新版 Bark 注释误判了存在性断言，并过度声称能检出非原子写入。**  
   位置：[测试:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-z5-canary/backend/tests/regression/test_g6_9_boundary_matrix.py:443)，444–451 行。  
   事实：新 tmp vault 初始没有 outputs，遗漏写入或将发送提前，会使存在性断言变红；它并非没有回归约束。另一方面，同步直写若在发送前完成，发送时 JSON 仍可解析，因此新增解析检查不能保证“换成直写就红”。  
   **建议：**说明该门证明发送时文件存在、JSON 含预期节点；不声称验证了原子写机制。

其余关键问题的判断：

- **夹具恢复成立。** 99–112 行用 `try/finally` 恢复 TZ 的原值或原先不存在的状态，并重新 `tzset()`。独立执行原夹具、自证用例及注入断言失败后的恢复检查均通过；16 组合中的 **8 个分叉元组逐条符合登记值**。
- **补跑②有实质约束。** 386–393 行同时检查缓存日志、生成时间、mtime 和一次发送。生产器 1023 行使用当前 `now`，08:00 到 10:00 的正常重生成会改变时间字段。mtime 不是绝对写入审计，但结合当前生产路径，足以支持缓存命中。SHA、未跨 next_due、节点池 mtime 是 **AND 条件**，不是其中某一道独自解释通过；新版 404–421 行另约束了节点池更新后的失效行为。
- **Bark 落账绑定成立。** 457 行返回 1，进入 runner 257–259 行；476–480 行从磁盘 state 核验两个失败字段及当天未 accepted，确实测到了目标分支。
- **午夜覆盖成立，但范围是分别生成。** 331 行分别生成两个时刻的真实 payload，298–303 行调用真实门禁 helper。它没有验证“23:59 的旧投影在 00:01 被重新读取”；286 行说明应相应收窄。

**整体结论：分叉事实、夹具机制和缓存／失败落账证据基本成立，但矩阵的生产绑定、xfail 设计及最终版本证据尚不足以支撑“可执行回归门已完成”。**
