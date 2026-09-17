绑定 **`a22254ab`**：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 4**。以下为本轮新增复核项；已接受移交的旧误判不重复计数。未发现此前 HIGH 的指定失效路径复发。

1. **MEDIUM — 恒收还有超出“自定义 setattr”的误判：不同作用域的同名对象被合并。**

   [lifespan_isolation_negative_control.py:598](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/backend/scripts/lifespan_isolation_negative_control.py:598)，关联 `:611`、`:1169`。

   ```python
   import threading as mod
   from types import SimpleNamespace
   from fastapi.testclient import TestClient

   def unrelated(mod):
       setattr(mod, "_active_limbo_lock", None)

   unrelated(SimpleNamespace())
   with mod._active_limbo_lock:
       pass
   ```

   **复现：**同一源码交给改前／现版 `analyze_source`，分别为 `[]`／违规。实际写入独立对象，收集器却按字面路径 `mod._active_limbo_lock` 撤销模块锁的 C4。

   此处 `setattr` 始终是内建函数，不涉及已排除的遮蔽实现。另已复现：死分支中的调用、捕获 `TypeError` 的两参数调用也被当成属性写入。**这些是本卡相对改前新增的误报，并非本轮撤回新引入。**

2. **LOW — 索引把失败日志标成“全 PASS”。**

   [README.md:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/README.md:27)。

   **复现：**所引 [readme-selfcheck-20260917T095015.txt:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/readme-selfcheck-20260917T095015.txt:10) 明写 `README-SELFCHECK: FAIL`，首行列出八个缺失文件。当前 README 的这些时间戳已改正，但引用的存档仍不能支持“全 PASS”。

3. **LOW — 索引存在性检查仍会跳过部分文件引用。**

   [readme_selfcheck.py:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/readme_selfcheck.py:16)。

   **复现：**分别输入反引号包裹的 `missing/report.txt`、`no such.txt`、` no-such.txt `、`NO-SUCH.TXT`，提取结果全部为 `[]`；另外两条规则也不命中。

   文件主体大小写变化、仍保留小写 `.txt` 时能够提取；**扩展名大写**才会绕过。`:26` 的验伪锚直接检查集合成员关系，没有经过引用提取器，因此不能发现这些漏检。原 LOW-5 的具体省略号引用已修，完整性声明仍不成立。

4. **LOW — 验收单仍保留已撤回开关的现行说明。**

   [验收单:104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/验收单/UAT-CARD-AST-FLAG-PATCH-2026-09-17.md:104)，同见 `:326–328`。

   **复现：**这些段落仍写“模块绑过 setattr 就整条不收”“且模块未遮蔽”，与当前恒收代码及同文 `:339–342` 相矛盾。生产文件里的删除和注释已清理，尾巴在验收文档。

5. **LOW — “否则四条锚会当场红”的保证过宽。**

   [验收单:369](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/验收单/UAT-CARD-AST-FLAG-PATCH-2026-09-17.md:369)，对应 [negctl.py:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-ast-flag/negctl.py:27)。

   **复现思路，未运行变异：**若回装一个仅识别顶层 `def setattr` 的全模块开关，当前全部 91 条样例都不会触发它；但危险调用之后再出现该定义，仍会造成执行顺序漏放。

   四条新锚本身名实相符；现变异证明当前 `any(ast.walk)` 开关及作用相同的实现会被杀，不能保证所有模块级开关都会被杀。

其余核对结果：

| 核对项 | 结论 |
|---|---|
| 撤回生产代码 | `_module_binds_name` 定义和引用均已删除，无残余开关 |
| lambda／注解／yield | 相关六处实现相对 round-3 未改；状态传递、默认值递归、递归 `push` 和逐条 yield 覆盖未见回归 |
| 三条原始盲区 | 三个原始锚仍全部 CAUGHT |
| LOW-4 | **已关闭**：九个目标 ID 各唯一；九项变异均不修改样例表，唯一性在变异后保持 |
| 静态样例 | 独立复算 **63／28，MISSED=0、FALSE POSITIVE=0**，仅代表表内样例 |
| 消费面／完整扫描 | 独立复算改前、现版均为两文件 `[]`，完整扫描均 `(0, [], 401)` |
| 单测证据 | 1185 行完整；提取的 **64 条失败／错误**与两份 nodeids 精确一致。日志为 `rc=1`，不是全绿 |
| 地盘／符号 | 公共符号保留，`backend/app` 零触及；`e9b36cb3 → a22254ab` 仅更新地盘回执 |

前三轮的 **R1 MEDIUM-3、R2 MEDIUM-5、R3 MEDIUM-3**，应统一记为“接受 fail-closed 误判并移交”，不能记成已恢复 CLEAN；尤其 R3 MEDIUM-3 的现版日志仍明确为 CAUGHT。其余旧 finding 的指定失效路径已关闭；索引检查的剩余问题见上述 LOW。

全程只读。仅做源码、存档核对及内存中的静态分析；未运行变异 harness、未重跑 pytest、未连接 7691／7687、未写文件。
