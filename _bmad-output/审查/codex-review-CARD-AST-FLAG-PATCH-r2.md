> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-AST-FLAG-PATCH round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-AST-FLAG-PATCH-r2.md)"`
> 审查绑定: `6564fc09`（本卡终审绑定 = round-4 的 `a22254ab`；其后仅 `_bmad-output` 改动，代码树逐字同）
> 会话头自证（抄 .stderr，括注行号；.stderr 本身不入库）:
> L2 `OpenAI Codex v0.153.3` / L5 `model: gpt-6-astra` / L9 `reasoning effort: ultra`

---

绑定 **`6564fc09ff14a29f0cef3bfc73ea090ac0f682eb`**：**BLOCKER 0 / HIGH 4 / MEDIUM 2 / LOW 1，建议整改后再复核。**

四个原始代码输入确实得到 **CAUGHT / CLEAN / CAUGHT / CLEAN**；但表外反例表明，整改尚未全面闭合。

1. **HIGH — HIGH-1 的撤回不彻底：根 lambda 含嵌套默认参数时，仍新增生产应用漏放。**

   [lifespan_isolation_negative_control.py:918](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:918)，关联 `:924–925`。

   ```python
   from app.main import app
   from fastapi import FastAPI
   from fastapi.testclient import TestClient

   def test():
       def unused(cb=lambda: (lambda x=(app := FastAPI()): x)):
           pass
       with TestClient(app):
           pass
   ```

   **复现：**同一源码交给三版分析器，`B14_BASE`、`20abe003` 均 CAUGHT，定稿 CLEAN。

   两个 lambda 都没有被调用，运行时 `app` 仍为生产应用；新增递归却把里面的海象记入 `test` 作用域。直接对根表达式 `lambda: (lambda x=(a := 1): x)` 调 `_own_exprs`，基线不产出海象，定稿产出 `a`，因此**根位置行为并非普遍等价**。

   child 路径也成立：将函数内定义换成 `unused = lambda cb=lambda: (app := FastAPI()): cb`，同样由 CAUGHT 变 CLEAN。原 HIGH-1 两个输入已修，但同类来源污染经新增路径重新出现。

2. **HIGH — `_walk_same_scope` 会进入默认值 lambda 的体，凭空授予隔离资格。**

   [lifespan_isolation_negative_control.py:510](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:510)，消费点 `:1623`、`:1653`。

   补齐 `contextlib`、生产 `app`、`TestClient`、`no_lifespan` 的标准 imports：

   ```python
   def isolated(a):
       with no_lifespan(a):
           def unused(cb=lambda: (yield a)):
               pass
       return contextlib.nullcontext(a)

   def test():
       with isolated(app), TestClient(app):
           pass
   ```

   **复现：**基线、round-1 均 CAUGHT、包装器表为空；定稿 CLEAN，并登记 `{'<module>.isolated': 0}`。

   `stack.extend(...)` 把返回表达式直接入栈，没有再次经过 `push`。默认值自身为 lambda 时，其体内 `yield` 因而被当作外层让出。编译对象确认 `isolated` **不是生成器，外层零条 `YIELD_VALUE`**；返回 `nullcontext` 前隔离已经退出。

   同根因也会误报：把这个未调用的 lambda 放在真正安全包装器的隔离块之前，定稿又会因“隔离外 yield”撤销资格。**这是 HIGH-2 整改新增的双向回归。**

3. **HIGH — HIGH-2 仍漏掉函数注解中的外层求值，适用于项目支持的 Python 3.11。**

   [lifespan_isolation_negative_control.py:462](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:462)。

   **复现：**把新增 HIGH-2 样例的 `def unused(x=(yield a))` 改为 `def unused(x: (yield a))`，或 `def unused() -> (yield a)`，定稿仍 CLEAN。

   已在 **Python 3.11.15** 编译确认：外层函数实际有两条 `YIELD_VALUE`，walker 只收到隔离内那条。`quick=True` 仍会在隔离外让出。项目 [CI:50](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/.github/workflows/test.yml:50) 支持 3.11/3.12。

   缺项是参数 `.annotation` 和函数 `.returns`。这一结论限定于未启用延迟注解的相应版本；3.14 的注解作用域规则不同，不能无条件把注解加入外层遍历。[Python 注解求值规则](https://docs.python.org/3.13/reference/compound_stmts.html#function-definitions)、[3.14 规则变化](https://docs.python.org/3.14/reference/executionmodel.html#annotation-scopes)。

4. **HIGH — 全模块 `setattr` 开关重新打开本卡 C4 漏放面。**

   [lifespan_isolation_negative_control.py:566](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:566)，关联 `:570–571`。

   ```python
   import threading as mod
   from app.main import app
   from fastapi.testclient import TestClient

   def unrelated():
       global setattr

   setattr(mod, "client", TestClient(app))
   with mod.client:
       pass
   ```

   **复现：**round-1 CAUGHT，定稿 CLEAN；删除无关函数后，定稿恢复 CAUGHT。

   `global setattr` 没有重绑定任何对象，实际调用仍是内建函数。无关函数的同名参数也会触发。这里“收得宽”会扩大 **C4 放行范围**，并非防漏报方向的保守处理。原 MEDIUM 输入虽然修好，修法却部分回退了本卡 `setattr` 修复。

5. **MEDIUM — round-1 MEDIUM 仍未覆盖字符串字段形式的真实遮蔽。**

   [lifespan_isolation_negative_control.py:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:530)。

   ```python
   import threading as mod
   from fastapi.testclient import TestClient

   match (lambda obj, name, value: getattr(obj, name)):
       case setattr:
           setattr(mod, "_active_limbo_lock", None)
           with mod._active_limbo_lock:
               pass
   ```

   **复现：**源码可编译，定稿却返回违规；`_module_binds_name` 返回 False，错误收录锁属性写路径。

   实际调用只读取现有锁。检测遗漏 `MatchAs.name`、`MatchStar.name`、`MatchMapping.rest`、`ExceptHandler.name`，它们不是 `Name(Store)`；`except … as setattr` 的只读可调用对象也复现了相同误判。

6. **MEDIUM — 绑定提交中的单测存档不足以支持“定稿与基线 diff 空”。**

   [README.md:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/README.md:20)。

   **复现：**读取 `git show 6564fc09:…/unit-close-20260917T091749.txt`，日志在第 220 行、约 **67%** 处结束，没有最终摘要或退出码；两份 `nodeids` 的最后修改提交均为 `20abe003`。

   这证明的是**该 SHA 的闭合证据不足**，不是测试失败。工作树后续增长的日志不能代替绑定提交内的完整证据。

7. **LOW — round-1 LOW 的索引修复仍留有不存在的引用。**

   [README.md:18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/README.md:18)。

   **复现：**按提交树查找 `territory-<最终 ts>.txt`，不存在；已提交的 `territory-20260917T090124.txt` 绑定旧 HEAD。所述“逐个存在性自动核”没有覆盖这一占位引用。

其余核对结果：

| 核对项 | 结论 |
|---|---|
| 53/29、零误报 | 独立复现；旧表条目完整保留 |
| 新增四条表项 | 预期正确；`R1-M3` 确实只读现有锁，CLEAN 合理 |
| 两个真实消费文件、401 文件扫描 | 改前分析器与定稿均为空违规集；本卡期间测试扫描文件未改 |
| 六处定向负控 | 静态核对编辑锚和目标标签均唯一，未发现指定输入靠无关机制变红；按边界未运行 harness |
| 控制组为空 | 支持这 82 个样例的差异可归因，不能证明整类语法完整或没有回归 |
| 三项原始盲区 | 三个原始锚仍全部 CAUGHT；但 lambda 有新增越界、`setattr` 部分回退、逐条 yield 的集合仍不可靠 |
| 不动点与符号 | 承重输入默认 3 轮收敛；显式上限 1 会抛未收敛；既有符号保留 |

全程只读，未运行变异 harness、未执行含项目导入的危险样例、未连接数据库、未写文件。上述问题均未涉及你排除的组合写法或 Lambda 独立作用域实现方案。


