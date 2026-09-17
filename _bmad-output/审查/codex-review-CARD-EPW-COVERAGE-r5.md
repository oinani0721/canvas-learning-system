> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t10-red · 卡 CARD-EPW-COVERAGE round-5（**末轮**）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-EPW-COVERAGE.md)"`
> 审查绑定: `99958aa8` = **最终 HEAD**。本轮 **BLOCKER=0 / HIGH=0 / MEDIUM=0**（LOW 5 登记不阻断）
> ⇒ 满足 D-15「末轮绑最终 HEAD 且 B=0、H=0」。
> 终审绑定实测：`git -c core.quotepath=false diff --stat --no-color 99958aa8 HEAD -- . ':(exclude)_bmad-output'`
> **为空**（存档 `evidence-epw-coverage/epw-binding-final-*.txt`）。
> ⚠️ 本轮之后**只改了 `_bmad-output`**（按 r5 LOW-1/LOW-2/LOW-4/LOW-5 修门脚本、负控存档命名与
> 矩阵数字），按 D-32 不占轮次、不破坏绑定；两条需要动 `backend/tests` 的 LOW（r5 LOW-3 调用端
> 低值透传）已达轮次上限 5，**登记不阻断**，见验收单 §8.4。
> 会话头自证（抄 `.stderr` 里含 codex 版本行 + `model:` 行 + `reasoning effort` 行的那三行，
> 逐行括注各自行号；⛔ 不是机械抄前三行；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（`.stderr:2`） / `model: gpt-6-astra`（`.stderr:5`） / `reasoning effort: ultra`（`.stderr:9`）

---

**结论：B0 / H0 / M0 / L5。** 本轮四项指定修正已落实，另有以下低风险缺口。

审查基线为 `15fddbc1 → 99958aa8`；全程只读，未跑 pytest，未连接网络或数据库。

## BLOCKER

该级 0 条。

## HIGH

该级 0 条。

## MEDIUM

该级 0 条。

## LOW

1. **包装函数别名仍能绕过路径门。**  
   [epw_path_gate.py:119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py:119) 把包装别名 `P` 当成路径来源变量。以下对照输入经完整静态门实测 **PASS**：
   ```python
   from pathlib import Path as P
   GraphitiEpisodeWorker(
       dead_letter_path=P("data/" + "dead_" + "letter_" + "episodes.jsonl")
   )
   ```
   实际仍指向默认相对死信路径，与“纯字面量任意切分一律 FAIL”的声明冲突。**定 LOW**：真实三份文件没有此写法，且门已声明不是充分条件。

2. **“tmp_path 派生不会被误杀”的声明仍过强。**  
   [epw_path_gate.py:109](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py:109) 的声明受保留的危险片段检查限制：  
   `GraphitiEpisodeWorker(dead_letter_path=str(tmp_path / "dead_letter_episodes.jsonl"))` 实测 **FAIL**，尽管路径位于临时目录内。**定 LOW**：r4 指定的拼接反例已修复，这是保留规则的误杀及本轮文案不准确。

3. **低值样本尚未贯穿实际 sleep 调用。**  
   [test_episode_worker_coverage_epw.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:415) 的实际重试哨兵仍为 `[0.37, 1.23, 4.56]`；新增 `0.001` 只读取属性。静态对照：若调用端改为 `await asyncio.sleep(max(backoff, 0.1))`，三个哨兵不变，属性低值断言也不会观察到这处加工。**定 LOW**：属性内部抬升下限的指定缺口已关闭，剩余是调用端低值透传的覆盖边界；此结论为静态推导，未运行变异。

4. **18 次负控只有 14 份独立详细红档。**  
   [驱动存档:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw-negctl-driver-r5-20260916T013836.txt:24) 记录低值负控红，但对应[详细红档:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw-negctl-test_backoff_upper_bound_is_monotonic_and_capped_at_60-20260916T013836.txt:16) 留下的是另一条 `returned == [b + 1 …]` 的失败。同函数多次负控共用文件名，四次仅剩驱动摘要。**定 LOW**：影响逐断言证据复核，不否定新增断言本身有效；18 个驱动块确实存在。

5. **附录“终稿”断言总数未同步。**  
   [coverage-matrix-20260915T121111.md:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:106) 仍写 **169 assert**，当前 AST 实测为 **171**。33 个测试函数、参数展开 47 条正确。**定 LOW**：属于统计文档过期，不影响测试行为。

## 本轮四项修正核对

| r4 项 | r5 结论 |
|---|---|
| LOW-1：属性下限抬升 | 已关闭：精确断言三个 `0.001` |
| LOW-2：四段拼接与指定误杀 | 已关闭指定反例：四段常量 FAIL；`str(tmp_path / ("data/" + "dead_letter.jsonl"))` PASS；真实三文件均 PASS |
| LOW-3：死信精确计数 | 已关闭：补有 `episodes_dead_lettered == 1` |
| LOW-4：关停版本边界 | 已关闭测试侧问题：条件 skip 与版本说明一致；Python 3.11 分支仍属移交 |

## 总评

**可按已声明的迁移范围承接其中 21 项，不能宣称旧 22 条全部等价闭合。**

- 矩阵 **37 行、37 个唯一 nodeid** 与指定来源完全同集合，`21 + 0 + 15 + 1 = 37`；相对既有 retry 文件确有新增观察点。
- 五项迁移声明与代码一致；额外的日志分级变化、完整周期只覆盖失败记账半程，也已声明。#16 的准确结论是“旧符号退役、新接线覆盖移交”，调用方接线缺口仍未验证。
- 三条 xfail 的处置仅发生于测试侧：两条改写真属性，一条删除无现实现等价物的每次尝试超时断言。代码差异只有指定两份测试，`backend/app` 零差异；构造路径均显式来自 tmp_path，无单例工厂直调。
- T10-C 的 15 项归属数量成立；本轮源码独立核实了 `TestAC3StartupRecovery` 无 skip，另一文件采用用户提供事实及存档，不评价其重写质量。
- 门已如实声明危险路径变量中转及 `memory_service` 字符串启发式的盲区。静态门 PASS、历史 47 passed、负控修改断言后变红，均不足以证明完整调用链隔离或所有语义变异都会失败。


