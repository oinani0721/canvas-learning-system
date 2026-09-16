> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 skills-writer · 卡 CARD-G2-7a-TAIL round-5（**D-15 上限轮 / 终审**）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-TAIL-r5.md)"`
> 审查绑定: `dcb8c0458032d5223236cc2e8ce46ba11aea278f` = **本卡最终 HEAD 的代码树**（本轮之后只改 `_bmad-output`，代码面 diff 为空）
> 会话头自证（抄 .stderr 中含 codex 版本 / `model:` / `reasoning effort:` 的三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核绑定 **`dcb8c0458032d5223236cc2e8ce46ba11aea278f`**。本轮未发现新增 BLOCKER／HIGH／MEDIUM；确认两种新增 LOW 输入：AnnAssign 局部变量假红、空白归一化造成路径身份假绿。

**r4 的 M1、M4 原输入仍然通过，不能称为行为已关闭；它们随撤回归入已移交缺口。M2、M3 的原输入现在被拒绝。** 以下按当前剩余问题分类计数，新输入并入对应项，避免重复计数。

**BLOCKER：无。**

**HIGH：无。**

1. **MEDIUM｜已移交：零写门仍不能完整确定调用身份，撤回恢复了模块级 open 的误豁免。**  
   [test_vault_install_manifest.py:901](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:901)，交叉 `:738`、`:793`。  
   输入 `import io; io.open("log","w")` 时，**r4 拒绝→r5 通过**；`_open`、`getattr`、直接调用 `partial(...)()`、`os.ftruncate` 等已移交路径仍未覆盖。重绑定检查也未扫描 lambda 参数，不能将其表述为“所有重绑定均被拒绝”。

2. **MEDIUM｜已移交：旗标属性被改值后，仍只凭属性名字判定只读。**  
   [test_vault_install_manifest.py:850](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:850)，交叉 `:735`、`:899`。  
   输入 `os.O_RDONLY = os.O_WRONLY | os.O_TRUNC; os.open("log", os.O_RDONLY)` 时，**r4／r5 均通过**。

3. **MEDIUM｜已移交 main.js M4：非普通文件仍只记 note，不进入失败桶。**  
   [verify_vault_install.py:1384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1384)。  
   hotkeys 合法、main.js 为目录或 FIFO、其余检查没有错误时，该分支仍允许退出码为零；**r4／r5 相同**。

4. **MEDIUM｜已移交 main.js M5：路径判型与路径读取仍存在两次访问之间的替换窗口。**  
   [verify_vault_install.py:1388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1388)，交叉 `:1375`。  
   普通文件通过判型后、读取前被换成无写端 FIFO，仍可能阻塞；**r4／r5 相同**，本轮未执行并发替换。

5. **LOW｜本轮扩大：全行空白归一化会抹掉路径自身的有效空白，产生身份假绿。**  
   [test_vault_install_manifest.py:3359](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:3359)，交叉生产 renderer `verify_vault_install.py:1482`。  
   输入为 `path=HOTKEYS_REL+" "`、正确 detail、`role="-"` 的真实 finding 时，报告没有精确目标路径，断言却 **r4 拒绝→r5 通过**；前导空格、尾 tab／NBSP 同样。此项并入 r4 LOW-11 的渲染身份碰撞问题。

6. **LOW｜本轮扩大：AnnAssign 新扫描范围会把推导式的局部绑定当成 API 重绑定。**  
   [test_vault_install_manifest.py:726](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:726)，交叉 `:733`。  
   输入 `obj[[os for os in ()]]: object` 或 `obj[(open for open in ())]: object` 时，**r4 通过→r5 拒绝**；这些局部绑定不改变外层 API。此项并入重绑定检查不区分作用域的假红问题。

7. **LOW｜r4 LOW-10 部分保留：提及计数仍会把无关 finding 算作重复目标。**  
   [test_vault_install_manifest.py:3363](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:3363)。  
   正确 hotkeys finding 之外，另一个 finding 的 detail 提到 `HOTKEYS_REL`，或路径为其 `.bak` 时，**r4／r5 均因 mentions=2 拒绝**；归一化只解决了展示空白假红。

四处修改的实际判值如下。“通过／拒绝”指对应门的结果。

| 修改／负控或对照输入 | r4 | r5 | 判断 |
|---|---|---|---|
| 删模块识别：`import io; io.open("log","w")` | 拒绝 | 通过 | 恢复既有误豁免 |
| 删模块识别：`import io; io.open(p,"rb")` | 通过 | 拒绝 | 也恢复既有只读假红：把路径当 mode |
| r4 M1：`import io; io: object; io.open("log","w")` | 通过 | 通过 | 未关闭，归入移交 |
| r4 M2：导入 `_io`，再由形参 `_io` 遮蔽并调用 `.open("w")` | 通过 | 拒绝 | 已拦住 |
| r4 M4：`import os as io; io.open("log",io.O_WRONLY\|io.O_CREAT)` | 通过 | 通过 | 未关闭，归入移交 |
| 收窄敏感名：`def label(io)`、局部 `io=1`、`for io in []` | 拒绝 | 通过 | 三类假红消除 |
| 收紧 import 判断：`import io as os` | 通过 | 拒绝 | 错误 owner 绑定被拒绝 |
| AnnAssign：对象表达式内海象重绑 `open`，随后 `open("w")` | 通过 | 拒绝 | r4 M3 已拦住 |
| AnnAssign：单纯 `os.open: object` | 通过 | 通过 | 无值注解仍获准 |
| FIFO：仅增加缩进或行尾空格 | 拒绝 | 通过 | 展示假红消除 |
| FIFO：finding 路径自身增加尾空格 | 拒绝 | 通过 | 新身份假绿 |

**保留的四件：前三件的指定用例成立；FIFO 第二条需缩小表述。**

- **`os.open` 旗标分支保留**：只读字面旗标通过；写旗标、变量旗标、缺旗标拒绝。
- **参数展开拒绝保留**：检查仍位于所有分支之前，六条展开锚均成立。
- **直接重绑定拒绝保留**：`os.open = partial(os.open,"log")` 在 r4／r5 均被 `:735` 的 `Attribute(Store)` 拦住，**不依赖敏感名集合是否包含 `io/builtins`**。但不能外推为完整的调用解析证明。
- **FIFO 的 `mentions==1` 保留**；第二条现在证明的是“归一化后相同”，已经不证明原文逐字相同。重复 role、错误理由、缺目标仍拒绝。

**空白归一化确实会同时折叠 detail 内部空白。** 当前固定中文理由中，逗号后的单空格换成多个空格或 tab，都是 **r4 拒绝→r5 通过**。本次没有证据表明该固定理由因此改变语义，所以不另计缺陷；路径空白具有明确身份意义，已计入 LOW。

**16 条验伪锚没有因删减变成空判据。** 实数确认是 **r4 22 条、r5 16 条**；提取真实判据后，16 条全部通过。将分类器改为恒真会失败 12 条，改为恒假会失败 4 条。它们验证的是调用分类器，未覆盖重绑定扫描或完整 FIFO 行为。

**生产脚本自 r1 起一行未改，三件事仍成立。** r1／r4／r5 的脚本 blob 均为 `6727b2992c4676bf65dd4b6f02ce6c3a76b00050`，中间历史也无修改：

- `:1328`：`O_RDONLY | O_NONBLOCK` 打开。
- `:1334`：对同一 `hotkeys_fd` 执行 `fstat`／普通文件判定。
- `:1354–1355`：经 `fdopen` 从同一 fd 读取。

本轮仅执行只读 Git 核验、源码分析及内存中的判据／真实 renderer 对照；未执行负控写操作、FIFO 集成测试、hook、数据库或网络访问，工作树未改。

**BLOCKER=0 HIGH=0 MEDIUM=4 LOW=3**


