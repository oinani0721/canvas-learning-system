> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 skills-writer · 卡 CARD-G2-7a-TAIL round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-TAIL-r4.md)"`
> 审查绑定: `2358f9e0b3597471380d2def00c270f854889cc5`（该轮跑完时 HEAD 与之相同；本轮处置为**做减法**、撤回超范围修复，HEAD 再次前进，故送 round-5 重绑）
> 会话头自证（抄 .stderr 中含 codex 版本 / `model:` / `reasoning effort:` 的三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核绑定 **`2358f9e0b3597471380d2def00c270f854889cc5`**。确认 **4 项本轮新增 MEDIUM 回归**。下面“通过／拒绝”均指执行对应版本的完整零写门，负控源码只供 AST 分析，未执行其中的写操作。

全程未改文件、未运行 hook、未联网或连接数据库；FIFO 部分验证了实际 renderer 与报告断言，未运行需要创建文件的集成测试。

**BLOCKER：无。**

**HIGH：无。**

1. **MEDIUM｜新增：无值注解被重绑定检查豁免，却被 owner 提取器当成重新赋值，真实模块写调用因此获准通过。**  
   位置：[test_vault_install_manifest.py:858](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:858)，交叉 `:720–726`。

   ```python
   import io
   io: object
   io.open("log", "w")
   ```

   **r3 拒绝 → r4 通过**。r4 的 `owners` 为空、`rebinds=[]`；随后把 `"log"` 当绑定方法的 mode，因为不含 `wax+` 而放行。无值注解实际没有覆盖 `io` 模块。

2. **MEDIUM｜新增：模块别名识别扩展了，但形参重绑定检查仍只认四个固定名字，别名被局部遮蔽后继续享受模块豁免。**  
   位置：[test_vault_install_manifest.py:733](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:733)，交叉 `:856–860`。

   ```python
   import io as _io
   from pathlib import Path

   def f(_io):
       _io.open("w")

   f(Path("log"))
   ```

   **r3 拒绝 → r4 通过**。`ast.arg` 不会被 owner 的 `Name(Store)` 扫描剔除，`_io` 又不在敏感名集中；写模式 `"w"` 被当成模块调用的路径，缺少第二参数遂判为默认只读。

3. **MEDIUM｜新增：排除无值注解的整个 target 子树，会跳过其中真实执行的海象赋值。**  
   位置：[test_vault_install_manifest.py:720](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:720)。

   ```python
   import functools
   (open := functools.partial(open, "log")).open: object
   open("w")
   ```

   **r3 拒绝 → r4 通过**。注解虽不赋值给外层属性，仍会执行其对象表达式，将 `open` 改成预绑定路径的 `partial`；最后的 `"w"` 实际是写模式，门却按内置 `open` 的缺省模式放行。

4. **MEDIUM｜新增：`os` 导入为 `io`／`builtins` 被允许，但随后既不按模块 open，也不按 os.open 判定。**  
   位置：[test_vault_install_manifest.py:739](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:739)，交叉 `:856`、`:891`、`:955`。

   ```python
   import os as io
   io.open("log", io.O_WRONLY | io.O_CREAT)
   ```

   **r3 拒绝 → r4 通过**。import 检查因原模块是 `os` 而放行；owner 集却不收录它，最终再次把 `"log"` 当只读 mode。不能因“别名已移交”而忽略这个明确新增的判值反转。

5. **MEDIUM｜既有：旗标属性可以被改值，门仍只凭属性名字证明只读。**  
   位置：[test_vault_install_manifest.py:903](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:903)，交叉 `:729`、`:952`。  
   输入 `os.O_RDONLY = os.O_WRONLY | os.O_TRUNC; os.open("log", os.O_RDONLY)` 时，属性赋值不命中 `write_names`，旗标分析仍认可名字 `O_RDONLY`；**r3／r4 均通过**。

6. **MEDIUM｜既有 M3：表面调用名与 owner 假设仍留下未覆盖的写路径。**  
   位置：[test_vault_install_manifest.py:800](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:800)。  
   `getattr(os,"open")(...)`、`functools.partial(os.open,...)()`、`os.ftruncate(fd,0)` 均未被拦下；`import io; Path = io; Path.open("log","w")` 也通过，换成 `pathlib`、`functools` 同样如此。以上均为 **r3／r4 通过**，所以敏感名只有四个确实不足以维护调用解析前提。

7. **MEDIUM｜既有 M4：非普通 main.js 只记 note，未计入失败桶。**  
   位置：[verify_vault_install.py:1384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1384)。  
   hotkeys 合法、main.js 为目录或 FIFO、其余检查无错误时，此分支允许退出码为零；**r3／r4 相同**。

8. **MEDIUM｜既有 M5：main.js 的形态检查和读取仍针对两次路径访问。**  
   位置：[verify_vault_install.py:1388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1388)，交叉 `:1375`。  
   普通文件通过检查后，若路径在 `read_text()` 打开前被替换为无写端 FIFO，仍可能阻塞；**r3／r4 相同**，本轮未执行并发替换。

9. **LOW｜新增：重绑定检查不区分作用域与实际用途，合法只读代码新增假红。**  
   位置：[test_vault_install_manifest.py:727](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:727)，交叉 `:733–744`。  
   无害的 `def label(io): return io`、函数内部 `io = 1`、空循环 `for io in []`，以及 `from io import open; open("log","rb")`，均为 **r3 通过 → r4 拒绝**。普通局部 Store 还会错误剔除全局模块 owner，但整门先被 `rebinds` 拦住，不能把这一例单独算作新增放行。

10. **LOW｜新增：FIFO 断言额外耦合展示格式和其它 finding 的文字，生产行为正确也会假红。**  
    位置：[test_vault_install_manifest.py:3409](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:3409)，交叉 `:3410–3414`。  
    正确行仅改成四空格缩进或增加尾空格，即 **r3 通过 → r4 拒绝**；正确 hotkeys finding 之外，另一 unreadable 行的路径为 `.obsidian/hotkeys.json.bak`，或 detail 顺带提到 `HOTKEYS_REL`，FIFO 报告断言也发生相同反转。若额外行同时存在于普通文件对照报告，旧 `:3379` 已会拒绝，不能算作整条测试的新变化。

11. **LOW｜既有 LOW-1 未完全关闭：整行相同仍不能证明结构化路径身份。**  
    位置：[test_vault_install_manifest.py:3414](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:3414)，交叉生产 renderer `:1480–1482`。  
    令 finding 的实际 `path = HOTKEYS_REL + "  — " + D`、`detail=""`、`role="-"`，其中 `D` 是当前完整形态说明，实际 renderer 会输出完全相同的 expected row；真实 hotkeys finding 为零，**r3／r4 仍均通过**。

其余指定问题的结论：

- **`id()` 没有生命周期复用问题。** AST 根一直持有节点，扫描期间没有回收或替换。共享 `ast.Store` 上下文也不会让其它 Name／Attribute 父节点一起被跳过。Tuple 注解 target 是语法错误；Subscript 合法，其索引里的海象绑定同样会被多跳，问题在“排除整棵子树”，见 MEDIUM-3。
- **实际 `_verdict` 锚是 r3 19 条、r4 22 条，并非 24 条。** 新增净数量为三条。相关五类输入的作用如下：

  | 锚 | 能抓住的错误实现 | 限制 |
  |---|---|---|
  | 真模块 io 写 | 把所有属性 open 都当绑定方法 | 不验证 import 推导 |
  | 真模块 io 只读 | 一律拒绝模块 open | `"log"`／`"rb"` 均无写字符，单独不能区分参数位置 |
  | `_io` 别名写 | 忽略传入别名集合、仍用字面白名单 | owner 集是手工传入 |
  | 变量 io 写 | 仅凭名字 `io` 就认作模块 | 不覆盖源码中的重绑定检查 |
  | 变量 io 只读 | 一律拒绝未知 owner | 单独不能区分模块／绑定方法 |

  **整组不是恒真的空判据，但对 owner 提取器没有覆盖。** 内存负控中将 `_module_open_owners()` 改为恒返回空集，所有这些锚仍通过。

- **两条结论没有逻辑循环，但前提不充分。** `rebinds == []` 只证明没有命中其有限扫描规则；`offenders == []` 只证明表面名单中的调用，经现有豁免后，没有落在允许区间之外。后者依赖 owner／API／flags 解析正确，而前者未能完整建立这些前提。
- **生产脚本自 r1 未改，三步 hotkeys fd 链仍成立。** r1、r3、r4 的脚本 blob 均为 `6727b2992c4676bf65dd4b6f02ce6c3a76b00050`：`:1328` 非阻塞打开，`:1334` 对同一 fd 判形态，`:1354–1355` 从同一 fd 读取。这是源码与 Git 对象核验结论，不冒充本轮 FIFO 集成实测。

**BLOCKER=0 HIGH=0 MEDIUM=8 LOW=3**


