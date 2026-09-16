> 批次: BATCH-2026-09-11-第十四批 · 车道 T7 skills-writer · 卡 CARD-G2-7a-TAIL round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7a-TAIL-r2.md)"`
> 审查绑定: `3735b565b2ada7606aa1294c2d82e0520d7b3a64`（Codex 自述「结束时 HEAD 未变，两个地盘文件无未提交差异」；本轮 MEDIUM-1/2 与 LOW-1 整改后 HEAD 再次前进，故需 round-3 重绑）
> 会话头自证（抄 .stderr 中含 codex 版本 / `model:` / `reasoning effort:` 的三行，括注行号；stderr 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

复核绑定 **`3735b565b2ada7606aa1294c2d82e0520d7b3a64`**；结束时 HEAD 未变，两个地盘文件无未提交差异。本轮展开修补有效，但零写门仍有以下漏检。验证采用源码、diff 和内存 AST／参数签名对照；未运行 pytest、真实 FIFO、hook 或写入操作。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM：5 条。**

1. **`os.open` 被重绑定后，仍能把发生位置偏移的写调用判为只读。**  
   位置：[test_vault_install_manifest.py:827](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:827)。未被拦下的输入：

   ```python
   import functools, os
   os.open = functools.partial(os.open, p)
   os.open(os.O_WRONLY | os.O_TRUNC, os.O_RDONLY)
   ```

   实际绑定为 `path=p, flags=O_WRONLY|O_TRUNC, mode=0`，helper 却读取表面的第二个参数并返回 `True`。PREV／round-1／本轮判值为 **False／True／True**：这是**本卡新增、并非本轮新增**的缺口。重新绑定 `os` 或旗标属性也属于未验证绑定来源的问题。

2. **把所有 Attribute 调用当作绑定方法，会直接放行模块级 `open` 的写模式。**  
   位置：[test_vault_install_manifest.py:837](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:837)。输入 `io.open("log", "w")` 或 `builtins.open("log", "w")` 时，helper 把 `"log"` 当模式；因为不含 `wax+`，返回 `True`，真正的 `"w"` 被忽略。三版均存在。

3. **调用名称筛选会跳过别名、动态调用及名单遗漏的写 API。**  
   位置：[test_vault_install_manifest.py:724](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:724)。以下未被拦下的输入都不进入只读判定：

   ```python
   _open = os.open
   _open(p, os.O_WRONLY | os.O_TRUNC)

   getattr(os, "open")(p, os.O_WRONLY | os.O_TRUNC)

   functools.partial(os.open, p, os.O_WRONLY | os.O_TRUNC)()

   os.ftruncate(fd, 0)
   ```

   三版均存在；因此 `:647` 的“`os.*` 全族”覆盖声明也不成立。这与第 1 条不同：这里是**未选中调用**，第 1 条是**选中后误豁免**。

4. **非普通 `main.js` 仍只记说明，不登记检查失败。**  
   位置：[verify_vault_install.py:1384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1384)。输入为合法普通 hotkeys JSON、配上 FIFO／目录等非普通 `main.js` 时，该分支只设置 `hotkeys_note` 后返回，不添加 `unreadable`。这是既有问题；本检查本身不贡献阻断，最终退出码还取决于其他检查。

5. **`main.js` 的形态检查与内容读取仍存在并发替换窗口。**  
   位置：[verify_vault_install.py:1388](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/scripts/verify_vault_install.py:1388)。普通 `main.js` 通过 `:1375` 检查后被换成无写端 FIFO，随后的 `read_text()` 仍可能阻塞。两组 diff 均确认这段未改，**不是本卡新引入**；本轮没有重新实测用户提到的另外两个读点。

**LOW：1 条。**

1. **FIFO 报告断言没有把准确路径与形态原因绑定到同一条 finding。**  
   位置：[test_vault_install_manifest.py:3279](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills/backend/tests/unit/test_vault_install_manifest.py:3279)，以及 `:3282`。负控报告在 `unreadable` 段只包含：

   ```text
   <HOTKEYS_REL>.bak 读不进去
   other-file 不是普通文件(FIFO/设备等特殊文件)
   ```

   再保留预期汇总行和 `rc=2`，现有断言仍全部通过：第一条满足路径前缀，第二条满足原因字符串。已用内存输入确认；这是回归门的判据缺口，未据此发现当前生产输出错误。

对五个问题的直接回答：

- **① 展开拒绝本身完整。** 显式 `*args` 对应 `ast.Starred`，`**kwargs` 对应 `keyword.arg is None`，前置检查覆盖两者。原两条负控均为 **False／True／False**。但它没有解决上述调用绑定、签名识别与筛选范围问题。
- **② 会假红，符合你接受的保守口径。** 例如 `open(*[p, "rb"])`、`os.open(p, os.O_RDONLY, **{})` 确实只读，也被拒绝。另外，真实 `os.open` 中，`**kw` 不能覆盖已经绑定的 `flags`；重复传参会报 `TypeError`。所以第二条锚应理解为保守拒绝，不能解释成成功覆盖写旗标的实例。
- **③ 16 条锚没有空判据，但不等于 16 种独立性质。** 当前为 **4 正、12 反，16/16 通过**。仅移除新 guard，只有 `:711、:714、:717` 失败；`:715、:716、:718` 仍被其他分支拒绝。工程覆盖有重叠；严格逻辑上，各输入不同，并不存在某条必被其余条蕴含。
- **④ `offenders == []` 的证明边界没有扩大。** 它只表示：表面调用名在名单内的 AST 调用，扣除语法只读豁免、stdio 豁免及 `_write_report` 行号范围后，没有剩余项。新 guard 缩小了豁免集合，仍不能证明不存在其他写调用或运行时副作用。
- **⑤ 本轮未改变 FIFO／hotkeys 逻辑。** diff 确为测试文件 **+22／−0**；生产文件两版 blob 完全相同，FIFO 回归门也未变。上述既有问题仍保留；未发现本轮对同一 fd 的 hotkeys 检查路径引入回归。

BLOCKER=0 HIGH=0 MEDIUM=5 LOW=1
