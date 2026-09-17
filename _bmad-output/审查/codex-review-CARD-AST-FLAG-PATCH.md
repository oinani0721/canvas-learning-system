> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t8-tools · 卡 CARD-AST-FLAG-PATCH round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-AST-FLAG-PATCH.md)"`
> 审查绑定: `20abe003`（本卡终审绑定 = round-4 的 `a22254ab`；其后仅 `_bmad-output` 改动，代码树逐字同）
> 会话头自证（抄 .stderr，括注行号；.stderr 本身不入库）:
> L4 `OpenAI Codex v0.153.3` / L7 `model: gpt-6-astra` / L11 `reasoning effort: ultra`

---

复核 `20abe003`：**BLOCKER 0、HIGH 2、MEDIUM 1、LOW 1，建议修正后再通过。** 作者的三条负控修复和现有扫描结果均复现，但存在新增漏报。

1. **HIGH — 根 lambda 改动引入生产应用漏报。**  
   [lifespan_isolation_negative_control.py:836](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:836)，联动 `:2033–2059`。

   新版停止收集 lambda 体内绑定，却仍扫描体内调用，也没有建立 lambda 局部作用域，因而会错误借用外层同名变量的来源。

   ```python
   import contextlib
   from fastapi import FastAPI
   from app.main import app as production
   from fastapi.testclient import TestClient

   app = FastAPI()
   def t(cb=lambda s: ((app := production),
                      s.enter_context(TestClient(app)))):
       with contextlib.ExitStack() as stack:
           cb(stack)
   t()
   ```

   **复现：**将此源码分别交给父版、新版 `analyze_source`；父版返回违规，新版返回 `[]`。lambda 局部 `app` 实际绑定生产应用，进入客户端时没有隔离。

   同一缺陷也能新增误报：lambda 内先 `(a := FastAPI())` 再 `enter_context(TestClient(a))`，作为 `def` 默认参数时，父版 CLEAN、新版报来源未知。**27 条对照中没有任何 Lambda 节点**，未覆盖该回归。

2. **HIGH — “每条 yield”仍漏掉默认参数中的外层让出。**  
   [lifespan_isolation_negative_control.py:1540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:1540)，关联 `_walk_same_scope:472/:479`。

   ```python
   @contextlib.contextmanager
   def isolated(a, quick):
       if quick:
           def unused(x=(yield a)):
               pass
       else:
           with no_lifespan(a):
               yield a

   with isolated(app, True), TestClient(app):
       pass
   ```

   **复现：**补齐标准 imports 后交给分析器，父版、新版均返回 `[]`；编译确认外层函数有两个 `YIELD_VALUE`，新 `all_yields` 只收录隔离内那个。

   默认参数在外层执行，True 分支确实在隔离外让出。此项是**本卡全面覆盖修复的残缺**，底层 walker 问题沿袭旧版。`id()` 比较本身没有问题。

3. **MEDIUM — 局部重绑定的 `setattr` 被误认为内建属性写入。**  
   [lifespan_isolation_negative_control.py:503](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:503)。

   分支只检查函数名字，不检查绑定来源，会错误增加写路径并撤销 C4。

   **复现：**在有 `TestClient` import 的模块中，`import threading as mod`；局部定义 `setattr(obj, name, value)` 仅返回 `getattr(obj, name)`，调用 `setattr(mod, "_active_limbo_lock", None)` 后进入 `with mod._active_limbo_lock:`。父版 CLEAN，新版记录该属性被写并报违规，实际没有属性写入。

4. **LOW — 证据索引引用不存在的定稿日志。**  
   [README.md:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/README.md:12)，同见 `:13/:14/:21/:22`。

   **复现：**用 `rg --files` 对照索引：所列 `090106`／`090121` 文件不存在，对应现存件为 `090018`／`090032`。实际绿色日志的 SHA256 与当前脚本一致，问题在索引准确性。

其余核对结果：

- **三条修复成立：**同一输入父版均放行、新版均拦下；当前 51 条全抓、27 条全净，对照表内容未变。
- **消费面成立：**两份指定源码前后均 `[]`；父版、新版完整扫描均为 `(0, [], 401)`。
- **lambda 默认参数遍历本身正确：**与 `def` 默认参数作用域一致，不泄漏 lambda 体；问题是第 1 项所述后续来源解析。
- **yield 分支并集成立：**两支分别隔离同一形参仍 CLEAN；身份集合能正确去重。
- **`setattr` 范围：**非常量属性名确实不收；对象别名只形成字面路径，不做身份归一。同族动态写法可以单独移交，但不能据此宣称动态属性写已完整覆盖；未评价你排除的组合形态。
- **不动点成立：**承重输入实测 3 轮，78 条控制最多 3 轮，当前 401 文件最多 2 轮；上限 8 对当前面充足。`prefix.py` 唯一差异确为缺少耗尽时抛错的两行；先红的②③失败、①④⑤通过符合自检目的。③原本得到普通 `unknown` 违规，检测的是“未收敛原因是否明确报出”。
- **证据局限：**轮数 instrument 存档的改前扫描实际为 **0 文件**，不能用它单独证明改前 401 文件轮数；当前扫描面的结论已独立复算。
- **符号兼容成立：**列出的六个符号均保留，动态加载路径未被此次改动打断。

全程只读；未执行样例源码、CLI `main` 或变异 harness，未连接服务、未写文件。
