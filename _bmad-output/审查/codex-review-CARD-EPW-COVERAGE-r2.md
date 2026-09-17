> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t10-red · 卡 CARD-EPW-COVERAGE round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-EPW-COVERAGE.md)"`
> 审查绑定: `366835b8`（送审时 HEAD = `366835b8`，绑定成立；本轮 BLOCKER=0 / HIGH=0，
> 已达 D-15 通过线。之后仍按 r2 的 MEDIUM 1 + LOW 4 改了**代码**，故 r2 不再绑最终 HEAD，
> 按 D-15「审后改代码必再送一轮」再送 r3）
> 会话头自证（抄 `.stderr` 里含 codex 版本行 + `model:` 行 + `reasoning effort` 行的那三行，
> 逐行括注各自行号；⛔ 不是机械抄前三行；`.stderr` 本身不入库）:
> `OpenAI Codex v0.153.3`（`.stderr:2`） / `model: gpt-6-astra`（`.stderr:5`） / `reasoning effort: ultra`（`.stderr:9`）

---

复核结果：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 4**。

基于 `366835b8`；全程只读，未运行 pytest、未连接服务。代码差异确实只有指定两份测试文件，`backend/app` 零改动。

## BLOCKER

该级 0 条。

## HIGH

该级 0 条。原 HIGH-1 的 `sleep(0)` 漏洞已关闭，属性层 `1/2/4` 与实际重试 `2/4/8` 的区别也已明确声明。

## MEDIUM

### 1. 实际退避的断言仍不足以证明完整公式接线

[test_episode_worker_coverage_epw.py:409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:409)：桩只返回上界，`:415` 验证 `[2,4,8]`，无法发现实际重试丢失 full jitter 下半区间。

具体静态对照：假设 `_handle_failure` 将取值改为：

```python
cap = min(2**task.retry_count, 60)
backoff = random.uniform(cap / 2, cap)
```

属性实现保持原样，新用例仍得到 `[2,4,8]`；参照文件的范围断言也接受 `[cap/2,cap]`。因此，**上界公式与 `sleep(0)` 防线成立，但“实际重试完整使用 `backoff_seconds`”仍说得过满**。

定为 MEDIUM：这是核心退避语义的剩余覆盖缺口。可增加非上界返回值及实际调用的 `(low, high)` 断言，无需修改生产代码。

## LOW

### 1. metrics 整改仍允许错误常量通过

[test_episode_worker_coverage_epw.py:711](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:711)：`queue_depth` 只在排空后验证为零，平均耗时只验证 `0 <= avg <= max`。

若 `to_dict()` 的这两个字段分别恒返 `0`、`0.0`，仍能通过；队满用例检查的是 metrics 属性，不能补上序列化观察点。定为 LOW：已有实质补强，但“十字段真值已验证”仍超过证据，原 LOW-2 仅部分关闭。

### 2. 路径门的“已封”范围仍有遗漏

[epw_path_gate.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/epw_path_gate.py:59)、`:70`、`:127`：以下两份独立对照输入，在内存中交给原门、启用 `--strict-ms`，均得到 **rc=0 / PASS**：

```python
from app.services.episode_worker import GraphitiEpisodeWorker
GraphitiEpisodeWorker(
    dead_letter_path=str("data/dead_letter_episodes.jsonl")
)
```

`str(...)` 属于表达式，被直接接受。

```python
from app.services.memory_service import get_episode_worker as get_w
get_w()
```

别名收集不覆盖该导入来源，而 import 自身又满足了字符串启发式。

定为 LOW：当前测试没有这些危险写法，文档也已承认门不能独立证明隔离；这是“写死路径／import 别名已封”表述仍过宽。原两个精确输入确实已封，声明的三类剩余限制也确实存在。

### 3. 重叠表仍低估参照文件覆盖

[coverage-matrix-20260915T121111.md:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/_bmad-output/审查/evidence-epw-coverage/coverage-matrix-20260915T121111.md:69)：

- #1 被称为“只”有 `episodes_failed >= 4`，但 [参照文件:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_retry.py:224) 已直接断言尝试数和失败数均为 4。
- #20 被列为“未触及”，但参照文件 `:159–189` 已覆盖三次 `RuntimeError` 后成功，并验证三次退避。

定为 LOW：不影响矩阵集合，却夸大新增覆盖量。原 LOW-1 的数量部分已关闭，重叠说明尚未完全关闭。

### 4. warning“逐次编号”少验中间一次

[test_episode_worker_coverage_epw.py:767](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red/backend/tests/unit/test_episode_worker_coverage_epw.py:767)：只检查第一条 `attempt 1/3` 和第三条 `attempt 3/3`，而矩阵 #12 声称三条各含对应编号。

具体对照：第二条错误输出 `attempt 1/3`，现断言仍通过。定为 LOW：日志追踪的小缺口，未影响已覆盖的重试次数。

## 已核实的整改与边界

- **日志、身份整改有效**：重试成功路径现在直接观察 info；死信入口直接断言 `is task`，原 MEDIUM-1、MEDIUM-2 的具体漏洞已关闭。
- **矩阵账目正确**：37 个 nodeid 与来源双向差集为空；`21 + 0 + 15 + 1 = 37`；32 函数、46 条参数展开、161 个 assert 均对上。
- **去标与隔离成立**：两条改写读取真实属性，删除的 per-attempt timeout 用例在当前 worker 确无对应语义；新文件的 3 处 worker、5 处 store，以及 38_6 唯一 worker，均显式使用 `tmp_path` 派生路径，没有单例直调。38_6 其余类未改。
- **负控证明有限但真实**：新增红档确实命中相应断言；恢复档记录 46 passed，文件哈希与当前新文件一致。不过它们修改的是期望值，不能当作已经执行生产变异测试的证明。
- **T10-C 边界**：直接确认了 38_6 类级 skip 已删；另一模块仅由开工存档支持已执行，未越过读取面复查其源码或评价重写质量。

## 总评

**可以作为当前 worker 行为的覆盖承接，不能宣称完整替代全部 22 条旧语义。** #16 已准确改为“旧符号退役、新接线移交未验证”，原 MEDIUM-3 的过强结论已收回；#30 明确只承接记账半程。五项迁移声明基本符合代码，额外的日志分级变化和半程覆盖也已声明。

本卡证据仍不足以支持“21 条全部完整等价”“调用方接线缺口已关闭”“恢复→合并全循环已验证”“外层超时覆盖真实重试总耗时”，或“静态门 PASS 即完整隔离”。
