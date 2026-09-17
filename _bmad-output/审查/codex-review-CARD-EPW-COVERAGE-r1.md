> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t10-red · 卡 CARD-EPW-COVERAGE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-EPW-COVERAGE.md)"`
> 审查绑定: `65a84a91`（送审时 HEAD = `65a84a91`，绑定成立；本轮之后按 r1 意见改了**代码**，
> 故 r1 不再绑最终 HEAD，已按 D-15 再送 r2）
> 会话头自证（抄 `.stderr` 里含 codex 版本行 + `model:` 行 + `reasoning effort` 行的那三行，
> 逐行括注各自行号；⛔ 不是机械抄前三行——`model:` 在第 5 行；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（`.stderr:2`） / `model: gpt-6-astra`（`.stderr:5`） / `reasoning effort: ultra`（`.stderr:9`）

---

**结论：可作为有实质增量的部分覆盖，尚不能认定这 22 条缺口全部闭合。**

复核基于提交 `65a84a91`，全程只读，未运行 pytest、生产模块、数据库或网络。下述生产代码变更均为**静态对照推演**，未实际修改。

## BLOCKER

该级 0 条。

## HIGH

### 1. 退避公式测对了，但实际重试使用该公式没有被钉住

**位置：** [test_episode_worker_coverage_epw.py:354](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:354)、[test_story_38_6_scoring_reliability.py:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_story_38_6_scoring_reliability.py:80)。

属性测试确实断言了 `random.uniform` 的真实实参及 `min(2**retry_count, 60)` 上界；但实际重试用例只检查 `sleep` 次数。即使把 worker 的 `await asyncio.sleep(backoff)` 换成 `await asyncio.sleep(0)`，这些断言仍会成立，参照文件的区间断言也允许零。

此外，worker **先递增** `retry_count` 再取退避值，实际前三次重试上界是 **2/4/8**；38_6 第 80 行却把计数为零时的 `[0,1]` 称为“首次重试”。这是文件头未明确声明的时序差别。

**定级理由：** 矩阵 #13/#14 承接的核心退避行为可以被取消而不被发现，直接影响本卡闭合条件。

## MEDIUM

### 1. “重试成功日志”由两个不完整场景拼接，实际没有断言

**位置：** [coverage-matrix-20260915T121111.md:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:36)。

#22 引用的日志测试只执行首次成功；引用的重试成功测试又不检查日志。若成功 `info` 仅在 `retry_count == 0` 时输出，两条承接测试仍会通过，重试成功日志已经消失。

**定级理由：** 一条明确登记的承接语义仍缺少观察点，且未声明这项收窄。

### 2. 身份测试不能证明每次处理的都是同一个对象

**位置：** [test_episode_worker_coverage_epw.py:827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:827)。

断言检查原任务最终计数、时间戳及死信字段，没有检查每次处理对象的身份。具体对照：前三次处理原对象，第三次失败将其计数增至 3 后，最后一次入队使用 `copy.copy(task)`；现有断言仍全部成立，第四次处理却已经换了对象。

**定级理由：** 时间戳与最终计数有覆盖，但文件头、函数名承诺的“同一对象”强于实际断言。

### 3. #16 可以登记移交，不能据此判定接线语义永久消失

**位置：** [coverage-matrix-20260915T121111.md:30](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:30)。

旧私有方法删除，支持退役针对旧符号的测试；但“不允许直调单例工厂”并不证明调用方接线没有等价测试。38_6 第 227–232 行已经展示了 `tmp_path` worker 加工厂替换的隔离方式。

**定级理由：** 当前依据支持“调用方覆盖超出本卡范围，移交未验证”，不足以支持“接线语义已删、缺口闭合”。这与删除无 worker 等价物的 per-attempt timeout 桩测试不同。

### 4. 路径门的 PASS 不能证明隔离成立

**位置：** [epw_path_gate.py:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py:47)、同文件第 71 行。

已仅在内存运行原静态门验证：即使开启 `--strict-ms`，以下对照仍全部 PASS，未执行对照代码：

- **危险路径值：** `GraphitiEpisodeWorker(dead_letter_path="data/dead_letter_episodes.jsonl")`；门只检查关键字存在。
- **别名绕过：** `from app.services.episode_worker import get_episode_worker as get_w` 后调用 `get_w()`；门不解析别名。
- **间接入口失去替换：** 仅删除 38_6 第 248 行的 `ready_worker` 参数，保留 fixture 定义和其中的目标字符串；门仍 PASS，但该测试不会启动替换 fixture。甚至注释中的 `get_episode_worker` 也能满足字符串条件。

**定级理由：** 存在具体漏检路径，门不能独立承担隔离验收；**当前两文件未发现这些危险写法，不能据此认定已经污染死信目录。**

## LOW

### 1. 矩阵的用例数量与覆盖增量说明不准确

**位置：** [coverage-matrix-20260915T121111.md:85](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:85)、同文件第 65 行。

附录写“26 条”，实际为 **31 个测试函数、参数展开后 45 条**；“剩余 14 行参照文件均未触及”也不成立，例如 #2 的耗尽死信及 #30 的 hash/length/body，参照文件已有断言。

**定级理由：** 夸大增量、影响审查说明准确性，但不改变 37 行来源集合。

### 2. 指标快照测试没有验证全部十个字段的值

**位置：** [test_episode_worker_coverage_epw.py:622](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:622)。

docstring 声称十字段“各自取到真值”，实际只断言七个字段值；`queue_depth`、平均耗时、最大耗时只验证键存在，返回错误值仍可通过本用例。

**定级理由：** 局部覆盖声明过强，不影响已验证的主要计数器。

## 总评

- **集合与范围通过：** 37 个唯一 nodeid 与来源的 33+4 同集合；`21+0+15+1=37` 成立。本卡提交除 `_bmad-output` 外只有指定两份测试代码，`backend/app` 差分为空；38_6 差分只涉及导入及 AC1 类。
- **去标与隔离：** 三条去标确为“两条改写、一条删除”。删除 per-attempt timeout 桩测试的 worker 侧依据成立；两条退避改写确实读取生产属性，但存在上述时序表述和调用链覆盖缺口。新文件 3 处 worker、5 处死信 store，以及 38_6 的 1 处 worker 均显式使用 `tmp_path` 派生路径；无单例工厂直调。
- **T10-C 仅核事实：** 当前 AC3 无 skip；开工裁判存档也显示另一目标文件已执行而非整文件跳过。未评价前一卡重写质量，不能从“skip 已删”推导 15 条原语义均已恢复。
- **负控有效但有限：** 存档确实红在被修改的目标断言，恢复后的文件 SHA 与当前文件一致；它证明断言执行及当时观测值。例如“耗尽→死信”负控实际改的是调用次数 `4→5`，并未单独验证死信落盘断言的敏感性。
- **替代结论：** 新用例并非空测试；但 #30 已明确只承接记账半程，不能证明恢复、合并视图或实际可重放。结合上述退避、日志、身份及接线缺口，**不能把“21 条映射＋1 条退役”认定为旧 22 条语义全部闭合**。
