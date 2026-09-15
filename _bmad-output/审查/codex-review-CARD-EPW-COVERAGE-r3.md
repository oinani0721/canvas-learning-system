> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t10-red · 卡 CARD-EPW-COVERAGE round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-EPW-COVERAGE.md)"`
> 审查绑定: `a8e31623`（送审时 HEAD = `a8e31623`；本轮 BLOCKER=0 / HIGH=0。
> 之后按 r3 的 MEDIUM 1 + LOW 3 又改了**代码**，故 r3 不绑最终 HEAD，按 D-15 再送 r4）
> 会话头自证（抄 `.stderr` 里含 codex 版本行 + `model:` 行 + `reasoning effort` 行的那三行，
> 逐行括注各自行号；⛔ 不是机械抄前三行；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（`.stderr:2`） / `model: gpt-6-astra`（`.stderr:5`） / `reasoning effort: ultra`（`.stderr:9`）

---

**结论：BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 3。** 按你给定的 B0/H0 通过线仍可通过，但尚未关闭全部测试缺口。

复核基准：`15fddbc1 → a8e31623`。全程只读，未跑 pytest、未连接服务；下述变异均为静态对照，未实际修改生产代码。

## BLOCKER

该级 0 条。

## HIGH

该级 0 条。

## MEDIUM

### 1. 固定 1/4 点仍不能证明 sleep 使用了抽样结果

**位置：** [test_episode_worker_coverage_epw.py:411](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:411)、同文件 `:430`。

**事实：** 保留生产中的抽样调用，仅将实际 sleep 改为以下写法，两组断言仍成立：

```python
backoff = task.backoff_seconds  # 保留，日志仍使用它
# 原日志代码保持
await asyncio.sleep(min(2**task.retry_count, 60) * 0.25)
```

此时 `uniform_calls` 仍是 `[(0,2),(0,4),(0,8)]`，sleep 仍是 `[0.5,1,2]`，但实际退避已经丢弃随机结果。

**为何 MEDIUM：** r2 的错误下界反例确实关闭了，但“实际重试使用抽样值”这一承重声明仍存在行为退化而测试不红的路径。建议使用不同比例的返回样本，核对 sleep 逐次接收这些样本。

负控存档改的是**断言期望值**；它证明这些等式确实执行并能变红，不能证明上述数据流变异会被识别。

## LOW

### 1. 封顶测试观察了抽样上界，却丢弃属性返回值

**位置：** [test_episode_worker_coverage_epw.py:447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:447)。

**事实：** 将属性返回表达式静态替换为：

```python
return min(random.uniform(0, cap), 5.0)
```

现有相关断言仍满足：直接返回值测试只取 `1/2/4`，实际重试样本只有 `0.5/1/2`，封顶测试记录的 `high` 不变，真实采样也仍落在 `[0,60]`。

**为何 LOW：** 较大退避值被错误截成 5 秒仍无法发现；属于局部返回值观察缺口。封顶用例应同时断言属性返回序列。

### 2. 路径门仍放行纯字符串拼接出的默认死信路径

**位置：** [epw_path_gate.py:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py:93)。

**事实：** 在新增测试文件中加入以下写法，门会放行：

```python
store = DeadLetterStore(
    file_path=str("data/" + "dead_letter_" + "episodes.jsonl")
)
store.store(_make_task(), RuntimeError("probe"))
```

三个字符串常量分别不含完整危险片段，`file_path` 关键字也在场；实际求值却指向 `backend/data/dead_letter_episodes.jsonl`。已通过内存 AST 检查确认 helper 返回允许，未执行落盘代码。

**为何 LOW：** 当前测试没有这种写法，故不是已发生的污染；但它是门的具体漏检，且不属于文档已列出的变量中转或间接入口局限。

### 3. 矩阵附录及退避说明未同步到 r3

**位置：** [coverage-matrix-20260915T121111.md:100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:100)、同文件 `:112`；测试文件 `:394`。

**事实：**

- 附录仍写 **32 个函数／46 条／161 个 assert**；当前 AST 为 **33 个函数／168 个 assert**，匹配当前文件 SHA 的恢复存档记录 **47 passed**。
- F 组漏列新增的 metrics 序列化用例。
- 附录仍称实际 sleep 为 `2/4/8`，测试 docstring 也残留“返回上界”；当前实际期望是 `0.5/1/2`。

**为何 LOW：** 不影响代码执行，但影响覆盖数量和退避证据的准确解释。

## 已核实的整改与边界

- **矩阵集合正确：** 37 个 nodeid 与指定来源的 33＋4 完全同集合，无缺失、额外或重复；`21＋0＋15＋1＝37` 成立。
- **重叠表 8／6／7 成立：** #1 的失败计数等式、#20 的 `RuntimeError` 重试均有参照断言支持。“同题”按主题理解：#13 的参照路径是三次失败后成功，#30 只涉及已声明的记账半程。
- **r2 LOW-1、LOW-4 已关闭：** 非零深度和耗时有确定值断言；三条 warning 分别核对 `1/3、2/3、3/3`。
- **r2 LOW-2 的两个指定反例已关闭：** `str("完整危险字面量")` 和跨模块导入别名均能拦截，但仍有上述拼接漏检。
- **去标与地盘符合要求：** 累计代码 diff 只有两份指定测试文件；38_6 仅改指定类及导入行，`backend/app` diff 为零。两条改写明确说明测的是退避上界；删除每次尝试超时用例的理由与直接 `await add_episode` 的事实一致。
- **显式构造路径隔离成立：** 两文件合计 4 处 worker、5 处 store 均沿 `tmp_path` 派生；无单例工厂直调。T10-C 的类级 skip 缺失可由当前 AST 确认，另一处由允许读取的开工存档支持；未评价其重写质量。
- **间接隔离不能靠门独立证明：** 例如删掉 38_6 `:258` 用例的 `ready_worker` 参数、保留 fixture 定义及 patch 字符串，门即使使用 `--strict-ms` 仍会通过。这是已披露局限，不重复计为新问题。

## 总评

这份文件有实质覆盖，能够作为迁移后 worker 语义的承接基础；**目前不能认定它已完整替代原 22 条的全部保证**。五项迁移声明与生产事实一致，首次成功日志变化及恢复循环只覆盖记账半程也已局部声明；#16 可以登记“旧符号退役＋新接线移交”，不能算接线缺口关闭。

本卡证据仍支撑不了：随机样本必然传给 sleep、较大退避返回值正确、完整恢复与合并流程、调用方接线闭环，以及所有间接入口的运行期隔离。
