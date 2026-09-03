# CARD-DEBT-8 对抗性代码审查（round-1）

你在审查一个 git worktree 里的修复。worktree 根目录（所有路径基于此）：
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope

## 背景

缺陷：backend/app/services/review_service.py 顶部 `FSRS_AVAILABLE`(:95) 只判 `memory.temporal.fsrs_manager` 模块能否 import——该模块自带 fallback 类所以恒 True；而 backend/lib/memory/temporal/fsrs_manager.py 的模块级 `FSRS_AVAILABLE`(:24) 才判 py-fsrs 真库。py-fsrs 缺失时底层走 `_fallback_review` 简单倍率调度，但上层在 manager 存在时无条件返回 `"algorithm": "fsrs-4.5"` ⇒ 谎报。

修复（已落地在**暂存区**，看 diff 用 `git diff --cached -- backend/`，工作树与暂存区可能有差异时以 `git status` 输出为准）：
1. FSRSManager.__init__ 新增实例属性 `library_available = FSRS_AVAILABLE`（fsrs_manager.py:118-122 附近）；
2. ReviewService 新增 `_fsrs_library_ok()` helper（review_service.py:312-320 附近）；
3. schedule_review / record_review_result / get_fsrs_state 三处按它决定 algorithm 值，fallback 时加性写 `degraded_reason="fsrs_library_missing"`（record_review_result 与 CARD-D3 既有 degraded_reason 逗号拼接）；schedule_review 的 log_decision reason 同步诚实化（:893-897 附近）；
4. 新测试 backend/tests/regression/test_debt8_fsrs_fallback_honest.py（5 个子进程隔离探针）。

## 审查重点（按优先级）

1. **是否真判到了底层库**：三个消费点的分支判据是 `library_available`（实例属性，取自底层模块级 FSRS_AVAILABLE）还是仍然被某个恒真标志短路？`getattr(..., True)` 缺省值的选向会不会重新制造谎报？
2. **是否引入第三个模块级标志**：契约要求 FSRS_RUNTIME_OK 仍是唯一 runtime 真相源、不得新增模块级标志。`grep -n 'FSRS_RUNTIME_OK\|FSRS_AVAILABLE\|FSRS_LIB' backend/app/services/review_service.py` 的结果必须与 HEAD 版完全一致（逐行比对 `git show HEAD:backend/app/services/review_service.py` 的同名 grep）。
3. **真实库路径零变化**：py-fsrs 在位时，schedule_review / record_review_result / get_fsrs_state 三个响应的键集合与取值必须与 HEAD 完全相同（get_fsrs_state 不得新增键；record_review_result 的 degraded_reason 语义不变）。逐键核对新增代码路径在 lib_ok=True 时是否严格 no-op。
4. degraded_reason 逗号拼接是否破坏既有 `degraded_reason == "card_state_write_failed"` 类等值消费方（全仓 grep 消费方并核实）。
5. 新测试文件本身的质量：探针前提自证是否有效、断言是否恒真、子进程隔离是否真隔离（_CARD_STATES_FILE 指 tmp）。

## 约束与事实（审查时须知）

- 卡文硬边界：只许改 review_service.py + lib/memory/temporal/fsrs_manager.py + 新测试；exam_service.py / verification_service.py / memory_service.py / .gitignore 禁改；Neo4j 7691 只读。
- 已知范围外移交项（勿重复上报为本次缺陷，但如你发现新证据可补充）：GET /api/v1/review/fsrs-state 端点 review.py:1437 用显式白名单构造响应，service 层新键透不到 HTTP（response model 无字段）；/api/v1/health components.fsrs 在 py-fsrs 缺失时仍报 "ok"；RecordReviewResponse.algorithm 描述未含第三值。
- 证据目录：_bmad-output/审查/evidence-debt8/（基线与改后 pytest 输出、先红后绿记录、10 条变异负控制运行记录 mutation-run-v2.txt——变异脚本为机械变异负控制工具，是质量保障设施本身，不是被审业务代码）。
- 环境事实：本机 py-fsrs 6.3.1 在位；探针用 `sys.modules['fsrs']=None` 屏蔽。Python 3.14.4。

## 输出格式

按 severity 分级列出发现（BLOCKER / HIGH / MEDIUM / LOW），每条给：file:line、失败场景（具体输入→具体错误输出）、你实际跑过的验证命令与真实输出。没有缺陷的维度明确说"未发现"。最后给一行总判定：PASS（无 BLOCKER/HIGH）或 FAIL（列出必须整改项）。禁止风格建议与"建议加更多测试"类空话。
