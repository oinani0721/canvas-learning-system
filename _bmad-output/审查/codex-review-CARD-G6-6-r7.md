> 批次: BATCH-2026-09-07-第十三批 · 车道 card-u6-reviewtime · 卡 CARD-G6-6 round-7（U6-C 收口轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-6-r7.md)"`
> 审查绑定: `9fb119b97ebc4b3bd942f55ff7f5017962c13932..64d18ecfa9d20c1109e4071ca9745077dfa4a408`（**绑最终 HEAD**；期间 HEAD 前进到 `c7f34e66`，Codex 自行核对该提交只涉及 `_bmad-output`、被审代码相同）
> 会话头自证（抄 .stderr 会话头含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `provider: openai` / `sandbox: read-only` / `reasoning effort: ultra`

---

**本轮结论：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 0。** 收紧有效，未发现新增缺陷；但不能把它解释为完整的子进程执行证明。

审查范围为 `9fb119b9 → 64d18ecf`。期间 HEAD 前进到 `c7f34e666b77979826530552744fd9ca065910d3`；已核对新增提交只涉及 `_bmad-output`，被审代码相同。全程只读，未联网、未连接数据库，未重跑会写盘的 pytest。

- **BLOCKER：无。**
- **HIGH：无。**
- **MEDIUM：无。**
- **LOW：无。**

六项核对结果如下。

1. **注释基本准确，`--now` 那句仍建议收窄。**

   [daily_review_pick.py:966](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_pick.py:966) 的 `until > now` 是共用的时间有效性判定；`:1024–1028` 只按活跃集合执行 snooze 让位。Web、runner 复用此判定，runner 还会在越过唤醒点后使缓存失效。过期键可以留账，没有发现另行维持过期 snooze 让位的逻辑。

   因此“不让位才对”应理解为“**不再因为这条 snooze 让位**”，不保证恢复榜首，也不保证旧页面立即重绘。

   [测试注释:3980](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_overview.py:3980) 的“也统一不了什么”字面过强，但下一句已经承认“只合上其中一道缝”，结合上下文不另判 LOW。建议改成：

   > 不能统一三次请求的读钟；refresh 内共享参照时刻仍可能有局部收益，但不是本次测试修复的必要生产改动。

   还要区别：**仅在 `_run_pick` 新采样并传 `--now`，连整个 refresh 都没有统一**，[`_read_entry:2001`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/app/api/v1/endpoints/review_overview.py:2001) 仍独立读钟。例如 picker 参照 `23:59:59.999`，读回发生在次日 `00:00:00.001`，仍可能分日；让两者共享同一次采样才有这方面收益。

2. **`expected_runs=2` 是合理的前提断言，有明确的维护耦合。**

   两门在测试文件 `:4420/:4480` 明设 TTL 为零，fixture 也设一次；生产判断是单调钟差值 `< TTL`，正常串行请求不会去抖。两个同步 `client.post` 串行执行，独立临时目录隔离 key，刷新在 `finally` 释放锁，正常用例不会自己触发 `in_progress`。

   将来增加第三次 refresh 却不更新期望值，会报告测试前提变化。这是确定性的维护要求，不是当前随机变红的脆断言。

3. **指定缺口确实堵住，但记录仍未绑定最终执行。**

   第二次改走 `Popen`，若仍正常生成投影并返回 HTTP 200，先在 [测试文件:4022](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/backend/tests/unit/test_review_overview.py:4022) 红：

   ```text
   起子进程的次数不是 2 次 (实为 1): [...]
   ```

   第二次仍经包装、只是没钉钟，则在 `:4024` 红：

   ```text
   第 2 次子进程 argv 里没有 --now (钉子没落上): [...]
   ```

   两种结果均已提取原 helper 做纯内存执行确认。若 `Popen` 改法同时破坏返回协议，则可能先红 HTTP 200 断言。

   残余边界仍存在：第二次绕过包装，同时一个带正确 `--now` 的无关调用补足记录，检查可以绿；下游复制 argv 后只修改执行副本，也无法从 `seen` 察觉；重复 `--now` 时只检查首次出现。这些都是原有包装与观测方式的边界，当前调用窗口没有发现这些路径，不计本轮新增缺陷。

4. **改动范围与自述完全一致。**

   独立 Git、源码和 AST 对比确认：单文件 **+41 / −21**；只有 docstring、断言 helper 及两个关键字实参变化。`_pin_child_now` 可执行部分逐字相同；两条门原有的 **12 条、6 条 assert 全部相同**。在内存撤销所述变化后，整个模块 AST 与基线一致。

5. **证据大体一致，但 MUT-4 不能逐例定位。**

   [MUT-4 存档:43](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g66/mutation-u6c-timebomb-r6-20260911T085133.txt:43) 保存了四例失败、目标断言“出现 True”和 `rc=1`，没有逐例 traceback。因此只能确认摘要报告目标出现，不能确认四例分别都红在该处。具体反例是“三例因其他异常失败、一例命中目标”，也会产生相同摘要。UAT `:715` 已承认这一限制。

   前后两文件 SHA 与当前内容相符，最终基线及末行 `rc=0` 符合存档；但这些不能复证每轮立即还原的全部操作历史。

   [两份 pyright 全文:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/_bmad-output/审查/evidence-g66/lint-typecheck-u6c-r6-20260911T085324.txt:10) 的多重集确实都是 **1 ArgumentType / 1 UnusedFunction / 8 UnusedVariable**，具体诊断消息、列号及对应源行也一致。[runner:604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime/scripts/daily_review_run.py:604) 的 import、`:613` 的进程内调用准确。

   另外，mtime 改写仍不足以证明“作业期间无写入”：保留时间戳的复制或恢复也可留下旧 mtime。这是既有证据限度，未算作本轮代码缺陷。

6. **未发现新增 lint、类型或命名问题。**

   当场无缓存执行 `ruff check`、`ruff format --check` 均通过。直接调用本地 pyright 得到与存档相同的 **9 errors / 1 warning**：结论是零新增，不是类型检查全绿。必填关键字 `expected_runs` 与实际检查行为相符。


