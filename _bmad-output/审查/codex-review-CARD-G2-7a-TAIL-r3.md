> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 skills-writer · 卡 CARD-G2-7a-TAIL round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-TAIL-r3.md)"`
> 审查绑定: `25feb21d699ea8dae1e30975f74534d1ec69fa55`（Codex 自述「两个审查文件与该 HEAD 一致」；本轮 MEDIUM-1/2 与 LOW-1/2 整改后 HEAD 再次前进，故需 round-4 重绑）
> 会话头自证（抄 .stderr 中含 codex 版本 / `model:` / `reasoning effort:` 的三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

本轮绑定 **`25feb21d699ea8dae1e30975f74534d1ec69fa55`**，两个审查文件与该 HEAD 一致。按所给 D-15，本轮 **BLOCKER/HIGH=0**；以下问题仍须保留。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：5 条。**

1. **重绑定拒绝仍漏掉能改变调用解析的形态。** [test_vault_install_manifest.py:714](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:714)  
   未被拦下的输入：
   ```python
   (os.open,) = (functools.partial(os.open, p),)
   os.open(os.O_WRONLY | os.O_TRUNC, os.O_RDONLY)
   ```
   完整门通过，但实际 flags 是写入／截断。`for`、`with … as`、海象赋值、import／参数绑定及 owner 替换也有未覆盖路径；`os.O_RDONLY` 被重新赋值同样未拦。`global` 声明本身不改绑定，后续直接 `open = …` 仍会被拦。

2. **模块白名单仅认变量名，本轮新增绑定方法误放行。** [test_vault_install_manifest.py:816](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:816)、[同文件:893](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:893)  
   `io = Path("log"); io.open("w")` 被错当模块调用，因缺少 `args[1]` 而判只读；完整门 **round-2 拒绝、round-3 通过**，`builtins` 同理。反方向，`import io as _io; _io.open("log","w")` 仍把 `"log"` 当模式而放行。  
   `from io import open` 后的裸调用则正确走 `mode_index=1`：`"w"` 拒绝、`"rb"` 放行。

3. **表面调用名筛选仍漏写操作，修改 docstring 没有消除缺口。** [test_vault_install_manifest.py:762](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:762)  
   函数别名 `_open(...)`、`getattr(os,"open")(...)`、`functools.partial(os.open,...)()` 和名单外 `os.ftruncate(fd,0)` 的写入负控均通过完整门。此项不同于上一条：`_io.open(...)` **会进入** `open` 判据，只是位置判断错误。

4. **非普通 `main.js` 仍可能不阻断。** [verify_vault_install.py:1384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1384)  
   hotkeys 合法、`main.js` 是目录／FIFO 且其他检查通过时，只设置 note，没有登记 `unreadable`，退出码仍可为 0。

5. **`main.js` 的形态检查与读取仍有并发替换窗口。** [verify_vault_install.py:1375](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1375)、[同文件:1388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1388)  
   路径被判为普通文件后、`read_text()` 前替换成无写端 FIFO，仍会阻塞。

**LOW：2 条。**

1. **FIFO 断言已绑定同一渲染行，但未可靠绑定 finding 的真实路径及唯一性。** [test_vault_install_manifest.py:3341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:3341)  
   旧 LOW-1 的两行负控已正确拒绝；仍有以下未被拦下的输入：

   - finding 的真实路径为 `.obsidian/hotkeys.json  —.bak`，detail 含形态理由：实际 hotkeys finding 为 **0 条**，却选中 **1 条**并通过。
   - 同一路径各有 `role="-"`、`role="config"` 一条：实际 **2 条**，却只选中第一条，通过“恰好一条”。

   三个指定边界的结果是：

   | 输入 | 当前结果 |
   |---|---|
   | detail 为空 | 路径匹配，理由断言失败；正确拒绝 |
   | detail 自身含 `"  —"` | 首次分割仍取正确路径 |
   | role 非 `-` | `[role]` 留在路径比较项中，合法行被漏选 |

2. **无值类型注解被误判成 API 重绑定。** [test_vault_install_manifest.py:716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:716)  
   `os.open: object; os.open("log", os.O_RDONLY)` 没有修改调用绑定，却被完整门拒绝；对照为 **round-2 通过、round-3 拒绝**。当前生产源码确实没有触发该误报。

④ **19 条锚未发现空判据。** 当前为 5 正、14 负；恒 `True` 实现失败 14 条，恒 `False` 失败 5 条。新增两条写模式锚能抓住旧错位实现；新增只读锚在旧实现下也通过，但能抓住“一律拒绝只读”的回归，因此不是空判据。

⑤ 已确认本轮仅测试文件 **`+70/−7`**，生产脚本从 round-1 到本轮 diff 为空。hotkeys 的非阻塞打开、同 fd 形态检查和读取未变；上述两条 `main.js` 问题仍成立。本轮依据只读 AST／报告对照，未改工作树，未运行 pytest 或真实 FIFO 回归。

BLOCKER=0 HIGH=0 MEDIUM=5 LOW=2
