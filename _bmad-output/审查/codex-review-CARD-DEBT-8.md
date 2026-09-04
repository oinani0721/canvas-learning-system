审查对象不是暂存区：最终 `git diff --cached -- backend/` 为空。审查期间 HEAD 从 `ca116f51` 前移到 `a3c41075`，但三个目标 blob 始终稳定且目标文件 clean：

```text
review_service.py  91002cf6a2f2a2b25b03b8160f82e657befa17bc
fsrs_manager.py    3f86e24e7545d77857d14098b1144ef0845a9d7c
regression test    5de677c5e2c3b66e30d870553cc0adcf8e39ddcb
```

以下 PASS 仅针对这三个已提交 blob，不代表存在可审核的 staged patch。

## BLOCKER

未发现。

## HIGH

未发现。

## MEDIUM

1. 缺少 `library_available` 属性时 fail-open，会复活原谎报

位置：[review_service.py:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/services/review_service.py:257)、[review_service.py:282](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/services/review_service.py:282)、[review_service.py:320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/services/review_service.py:320)。

失败场景：屏蔽 py-fsrs，通过现有公开 DI 参数注入一个委托给真实 fallback `FSRSManager`、但没有新属性的兼容 manager。构造器把任意非 `None` manager 视为 runtime OK，`getattr(..., True)` 随后返回真。

实际探针核心命令：

```text
cd backend
env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c '<屏蔽 fsrs；注入缺 library_available、委托真实 fallback manager 的兼容对象；调用三入口>'
```

真实输出：

```text
prereq False False False True
helper True
record fsrs-4.5 None
schedule fsrs-4.5 None
state None None
```

正常 factory 创建的当前 [fsrs_manager.py:122](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/lib/memory/temporal/fsrs_manager.py:122) 一定有属性，所以这是 DI/旧实例兼容边缘，未定 HIGH；但缺省值确实应 fail-closed，不能用 `True` 表示未经证明的真库可用性。

2. py-fsrs 缺失时，既有 CARD-D3 测试门确定性回归

位置：[review_service.py:1093](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/services/review_service.py:1093)、[test_review_service_fsrs.py:665](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_review_service_fsrs.py:665)、[test_review_service_fsrs.py:689](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/unit/test_review_service_fsrs.py:689)。

实际命令：

```text
cd backend
env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c '
import sys, pytest
sys.modules["fsrs"] = None
raise SystemExit(pytest.main([
  "-p", "no:cacheprovider",
  "tests/unit/test_review_service_fsrs.py::TestCardStatePersistHonestyD3", "-q"
]))
'
```

真实输出：

```text
collected 6 items
FF.FF.
4 failed, 2 passed
```

具体冲突：

```text
expected None
actual   fsrs_library_missing

expected empty_concept_id_not_persisted
actual   fsrs_library_missing,empty_concept_id_not_persisted

expected fsrs-4.5
actual   fsrs-fallback-scheduler
```

仓内生产代码没有等值解析消费者，因此不是生产解析故障；但项目明确支持缺库 fallback，该环境下既有测试套件已不自洽。

3. 新“真实库零变化”探针不能证明其 docstring 宣称的全键、全值契约

位置：[test_debt8_fsrs_fallback_honest.py:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/regression/test_debt8_fsrs_fallback_honest.py:165)。

实际命令使用 `importlib` 加载该测试，仅在内存中向 `_PROBE_PRELUDE` 追加三个返回值包装器，再直接调用 `test_real_library_responses_unchanged()`；未改源码。包装器新增键并篡改 `interval_days/status/reps`。

真实输出：

```text
NEG|record|extra=record|interval_days=-999
NEG|schedule|extra=schedule|status=BROKEN
NEG|state|extra=state|reps=-999
SURVIVED|real-response-key-and-value-drift
```

同样，把 helper 改为直接读取 `fm.FSRS_AVAILABLE`、完全绕过实例属性后，5 个探针仍全部 `SURVIVED`。因此测试能抓恒 True 谎报，但没有锁住所要求的实例真相源，也没有真正逐键逐值比较。

## LOW

1. [test_debt8_fsrs_fallback_honest.py:106](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/regression/test_debt8_fsrs_fallback_honest.py:106) 只检查两个 substring。内存负控制删除逗号后仍通过：

```text
NEG|degraded_reason=fsrs_library_missingcard_state_write_failed|contains_comma=False
SURVIVED|missing-comma-delimiter
```

当前实现的逗号拼接正确；缺陷在测试 oracle。

2. [schemas.py:1013](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/models/schemas.py:1013) 声称 `degraded_reason` 仅在持久化失败时出现且只有两个单值；现在保存成功也可能返回 `fsrs_library_missing`，双降级会返回复合值。[review.py:1125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/api/v1/endpoints/review.py:1125) 会原样转发。这是硬边界外的新契约漂移证据。

## 未发现

- 底层真值链：正常 factory 缺库路径得到 `review_service.FSRS_AVAILABLE=True`、底层 `False`、实例属性 `False`、helper `False`；三个入口均返回 `fsrs-fallback-scheduler + fsrs_library_missing`，`log_decision` 也写 `fallback`。
- 第三个模块级标志：未发现。当前 grep 与 `git show HEAD:...` 逐行相同，仅命中既有第 `95/97/105` 等行。
- 真实库路径：未发现变化。固定时间、调用真实 py-fsrs 6.3.1，与 `a63fadd3^` 对照输出：

```text
schedule_review_equal=True
record_review_result_equal=True
get_fsrs_state_equal=True
write_failure_equal=True reason=card_state_write_failed
empty_id_equal=True reason=empty_concept_id_not_persisted
```

- `degraded_reason` 生产等值消费者：未发现；生产路径只原样转发。
- 子进程隔离：有效。`sys.modules["fsrs"]=None` 前提自证有效，状态文件位于系统 tmp，仓库 `backend/data/fsrs_card_states.json` 未生成。
- 实跑结果：新回归文件 `5 passed`；相关 FSRS manager/review service 既有测试在真库环境 `87 passed`。未把现有 mutation 10/10 记录当作独立证明。
- 用户列出的三项既有范围外移交未重复计缺陷。未访问 Neo4j；当前环境未提供 `graphiti-canvas.search_memory_facts`。

总判定：PASS（无 BLOCKER/HIGH；存在 3 MEDIUM、2 LOW，且当前没有 staged 审查对象）。


