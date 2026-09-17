> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t10-red · 卡 CARD-EPW-COVERAGE round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-EPW-COVERAGE.md)"`
> 审查绑定: `f3190f13`（送审时 HEAD = `f3190f13`；本轮 **BLOCKER=0 / HIGH=0 / MEDIUM=0**，
> 仅 LOW 4 条。其中两条是本卡自己引入的真缺陷（路径门误杀 + 新用例依赖 Python≥3.13），
> 故仍按 r4 意见改了**代码**，r4 不绑最终 HEAD，按 D-15 再送 r5 作为末轮）
> 会话头自证（抄 `.stderr` 里含 codex 版本行 + `model:` 行 + `reasoning effort` 行的那三行，
> 逐行括注各自行号；⛔ 不是机械抄前三行；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（`.stderr:2`） / `model: gpt-6-astra`（`.stderr:5`） / `reasoning effort: ultra`（`.stderr:9`）

---

**结论：BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4。**  
复核锚定 `f3190f13`；全程只读，未运行 pytest、连接服务或修改文件。

## BLOCKER

该级 0 条。

## HIGH

该级 0 条。

## MEDIUM

该级 0 条。

## LOW

### 1. 退避样本仍漏掉对抽样结果低端的加工

**位置：**[test_episode_worker_coverage_epw.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:415)、[同文件:473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:473)。

具体对照实现：

```python
return max(random.uniform(0, cap), 0.1)
```

它把 `[0, 0.1)` 的抽样结果全部抬到 `0.1`，但上界桩最小为 `1`、哨兵最小为 `0.37`，加工后均不变；真实采样和参照文件也只检查范围。因此，现有断言不能完整支撑“属性原样返回抽样值、不得再加工”。

**定 LOW：**r3 指定的缺口已经关闭；这是低端样本缺失。`returned == bounds` 确实能抓住原来的 `min(uniform(...), 5.0)`，哨兵组合也能抓住此前的上界／四分之一重算。

### 2. 路径门的常量拼接仍有漏检，并新增误杀

**位置：**[epw_path_gate.py:95](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py:95)。

纯 AST、内存执行已复现：

```python
# 实际指向默认死信路径，门却 PASS
GraphitiEpisodeWorker(
    dead_letter_path=str("data/" + "dead_" + "letter_" + "episodes.jsonl")
)

# 实际位于 tmp_path 内，门却 FAIL
GraphitiEpisodeWorker(
    dead_letter_path=str(tmp_path / ("data/" + "dead_letter.jsonl"))
)

# 用户指定的正常写法仍 PASS
GraphitiEpisodeWorker(dead_letter_path=str(tmp_path / "dead_letter.jsonl"))
```

原因是 `ast.walk` 按广度遍历，第一例取到的常量顺序为：

```text
episodes.jsonl、letter_、data/、dead_
```

这既不是表达式求值顺序，也没有表达路径是否归属 `tmp_path`。

**定 LOW：**门确有缺陷，但当前受审文件的所有构造器均已人工追到 `tmp_path`，没有发现实际污染路径。

### 3. 矩阵 #2 多声明了一条承接用例没有的等式

**位置：**[coverage-matrix-20260915T121111.md:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:16)、[test_episode_worker_coverage_epw.py:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:503)。

矩阵称该用例检查 `episodes_dead_lettered == 1`，实际只等待 `>= 1`，随后没有精确计数断言。把生产计数从每次加 `1` 改为加 `2`，这一承接用例仍会通过。

**定 LOW：**套件其他用例会抓住该变异，属于逐条映射说明夸大，不是整体计数覆盖缺失。

### 4. 关停后拒绝入队的覆盖需要限定 Python 版本〔移交项〕

**位置：**[test_episode_worker_coverage_epw.py:798](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:798)、[episode_worker.py:467](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/app/services/episode_worker.py:467)。

新用例无条件要求 `stop()` 后 `enqueue()` 返回 `False`；但 Python `<3.13` 的生产分支只投停止哨兵，`enqueue()` 没有关闭状态检查，正常空队列关停后仍可返回 `True`。恢复绿档运行于 **Python 3.14.4**。

**定 LOW：**这是已有生产兼容分支的移交事项，不要求本卡修改生产；现有存档不能证明该新增用例在 Python 3.11 上也通过。

## 核实结果与总评

- **范围通过：**相对 `15fddbc1`，业务代码只改指定两份测试文件；`backend/app` 无改动。三条 xfail 的处理确为测试侧“两条改写、一条删除”。
- **矩阵通过：**37 个 nodeid 与指定来源完全同集合，`21 + 0 + 15 + 1 = 37`；AST 独立核得 **33 函数／47 参数展开项／169 assert**，与附录及收集存档一致。
- **隔离通过：**新文件的 3 个 worker、5 个死信 store，以及 38_6 的 1 个 worker，均显式使用临时路径；两文件无单例工厂直调。
- **r4 主要修复成立：**未发现合理的、完全丢弃抽样返回值的通用区间重算还能通过哨兵组合；指定的属性二次截断也会被新断言抓住。五项迁移声明与生产事实一致。
- **T10-C 仅核事实：**AC3 当前无类级 skip；另一文件在开卡存档中已有实际执行结果。本轮没有越出读取面复评其质量，也没有直接重新读取其模块装饰器。

**可以按已声明的迁移边界承接当前 worker 的对应语义，不能宣称旧 22 条已完整等价恢复。**#16 实际是“旧符号退役、新调用方接线移交未验证”；#30 只承接记账半程，未证明恢复与合并。路径门也不能单独证明隔离：例如删除 38_6 回放用例的 `ready_worker` 参数、保留 fixture 中的 patch 字符串，门仍会 PASS。负控存档证明的是指定断言被执行且错误期望会变红；16 次执行记录中存在同目标函数红档覆盖，不能据此声称保存了 16 份独立失败现场，更不能扩大为生产语义变异的完备检出证明。
