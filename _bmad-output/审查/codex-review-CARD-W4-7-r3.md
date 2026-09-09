**BLOCKER 0 / HIGH 0。残留 MEDIUM 2、LOW 2；三项整改未全部闭合。**

审 SHA：`ad4c853baac769b50ae68c3ca8527ec448d6cfd5`。仅核对指定增量与本地归档；未运行测试、探针或负控，未连接端口。以下反例均为静态推导。

1. **MEDIUM｜MEDIUM-1 部分闭合：旧反例已覆盖，仍缺一个有实际意义的组合。**

   **依据：**[test_live_port_guard_contract.py:758](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/unit/test_live_port_guard_contract.py:758) 将 `_Denier` 参数化为根名和子模块；779–786 行恒否认；810–821 行的 `_Affirmer` 则只验证 `"json"`。

   以下错误实现对普通字符串行为正确，也能通过这三组输入：

   ```python
   return str.__eq__(name, "uvloop") is True or (
       str.startswith(name, "uvloop.") and not (name == "uvloop")
   )
   ```

   `_Denier("uvloop")` 由第一项拦截；`_Denier("uvloop.loop")` 的真实前缀为真、重载相等为假，仍被拦截；`_Affirmer("json")` 的真实前缀为假，正确放行。但是 **`_Affirmer("uvloop.loop")` 会因重载相等返回真而被错误放行**。这只是对子模块分支冗余地排除根名，没有按测试类名特判。

   原 `r2-med1` 确已覆盖：`negctl_patch_w47.py:58–66` 是所述变异；`r1-high-negctl-r2-med1-after3-20260909T122817.txt:5–9` 明确记录 `[uvloop.loop]` 因 `DID NOT RAISE` 失败，同时另一参数通过。

   **建议：**交叉 `_Denier`／`_Affirmer` 与 `"uvloop"`／`"uvloop.loop"`／`"json"`。两个被禁名称足以覆盖根名和前缀分支；当前缺口在**子类行为与真实值的组合**，增加更多子模块名称并不直接解决它。

2. **MEDIUM｜MEDIUM-2 原证据缺失已闭合，但新增基线判据可能接受不完整序列。**

   **依据：**[m4-importlib-probe.py:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-probe.py:101) 的无门导入捕获所有异常，随后仍正常输出裁定行；185–193 行仅要求事件列表非空，**没有要求基线成功导入**。因此，若记录 `uvloop.includes` 后加载失败，子进程仍可正常退出，部分序列仍会被称为“完整序列”，最终返回 0。

   **建议：**增加明确的 `import_succeeded` 字段；基线必须成功导入且观察到事件，否则返回 2。

   就本次归档而言，五事件记录有依据：[m4-importlib-after3-20260909T122817.txt:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/m4-importlib-after3-20260909T122817.txt:28) 至 33 行同时记录成功导入、模块路径、五个事件和 rc=0。探针39–44行只注册一次旁观 hook，每次匹配回调只追加一次；未见人为重复计数。54–58行的 `STATE` 桩只为113行提供账本读取，未见它影响导入判定；其零账本不能作为网络行为证据。

   两处 docstring 的版本限定已明显收窄，但还应精确到**本次观察窗口和归档环境**：

   - [live_port_guard.py:711](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/backend/tests/support/live_port_guard.py:711) 与测试709–717行引用 `m4-importlib-r3-*.txt`，名称与本轮提供的 `after3` 归档不一致。
   - 归档2、30行标明解释器和包来自 `card-v5-lance/backend/.venv`，未记录 uvloop 精确版本。
   - “观察到 `uvloop.loop` 两次”可信；两次各由哪个 loader／阶段发出、是否存在观察窗口外事件，**未验证**。

3. **LOW｜LOW-3 部分闭合；测试改法正确，跑器仍有两处 LOW 缺口。**

   **测试本身闭合。**测试123–133行捕获异常后断言 `escaped is None`，再要求 `got is None`，仍准确验证“不让异常逸出且返回 None”，没有吞掉异常后直接通过。[HIGH-1 归档:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl-r1-high1-after3-20260909T122817.txt:5) 至18行也确实包含三个参数及各自异常类型，pytest rc=1。

   **LOW：失败理由仍未逐参数绑定。**[r1-high-negctl.sh:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl.sh:67) 至74行只计算函数叶名的 FAILED 总数，并要求全部 `^E` 中至少一次命中理由。三个参数都失败、但只有一个因预期理由失败，仍可返回0。18–26行的固定数量也不能证明覆盖完整：新增通过／跳过参数可能继续 PASS；新增应失败参数则因旧常量产生维护性假红。`r2-med1` 当前实际是“一失败、一通过”，其 `1/1` 不能解释为整个测试参数全红。

   **建议：**核对完整参数 ID 与各自预期结果，逐参数绑定失败理由；要求 pytest rc=1，拒绝意外 ERROR／中断。新增参数时同步更新预期映射。

   **LOW：信号退出仍可能伪装成功。**同跑器31–47行将 `restore` 同时绑定 EXIT、INT、TERM，并原样返回进入时的 `$?`。若前一命令成功、验收尚未完成时收到信号，可能还原后以0退出。该路径**未实跑**，是否本轮引入也无法从获准增量判断。

   **建议：**EXIT 负责还原；INT／TERM 显式退出130／143。

4. **无新增 BLOCKER/HIGH｜本轮增量未改变 guard 的可执行实现。**

   **依据：**`001a8271..ad4c853` 中，`live_port_guard.py` 的变化仅位于 docstring；测试新增的异常捕获断言及拒绝／放行断言均非恒真。

   新增的条件性误通过位于第2条基线判据；第1、3条是测试组合和跑器裁定范围不足。**未发现当前 guard 实现因此新增绕过路径。**

   **建议：**分别补齐上述测试组合与证据裁定条件，无需据此扩大修改到生产业务代码。

5. **原 HIGH-1／HIGH-2：维持闭合结论，限本轮只读证据。**

   **依据：**HIGH-1 归档5–18行显示三个异常参数均按指定理由失败；[HIGH-2 归档:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u7-w4guard/_bmad-output/审查/evidence-w47/r1-high-negctl-r1-high2-after3-20260909T122817.txt:5) 至13行显示 `[uvloop]`、`[uvloop.loop]` 均因 `DID NOT RAISE` 失败，pytest rc=1。结合 guard 可执行代码未变，本轮没有推翻前两轮 HIGH 闭合的依据。

   **建议：**保留两个 HIGH 的闭合状态，另行处理上述 MEDIUM／LOW。当前审 SHA 的重新执行结果，按只读边界记为**未验证**。
