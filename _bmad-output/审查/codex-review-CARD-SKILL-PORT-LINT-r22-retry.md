复核绑定 **`7fc33b617ee95dbd3ebe4ef432b82bc22e96a5b2`**，测试文件 blob：`03125650e00f43ea7ddac32ce05fe12f5a422657`。期间工作区发生外部修改，动态验证已固定使用提交中的内存源码。未修改文件、运行 pytest、读取禁读正文或连接服务。

**BLOCKER：未发现。**

**HIGH：3 条。** 以下三组坏形态与安全对照均经复现：九项计数相同，七组附加结果全部 `[] → []`，包括块指纹。

1. **HIGH — [test_skill_portability_lint.py:1136](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1136)：源码行序不能代表执行顺序，循环回边会漏掉真实重赋值。**

   ```python
   for i in (0, 1):
       if i:
           P = "/etc/passwd"
           break
       P = "/t" + "mp/cls-exam/x"
   ```

   首轮赋命名空间路径，次轮覆盖为 `/etc/passwd`；判据却因外部路径的源码行在前而放行。安全对照仅将上方 `P` 换成 `Q`；内存执行确认两者最终路径不同。

   你担心的互斥分支也确实误报：**即使 `if/else` 两支都赋命名空间内常量，仍报两处**。因此，“整块按直线看”同时存在漏报与误报。

2. **HIGH — [test_skill_portability_lint.py:1250](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1250)：整块不是合法 Python 时，新增补查跳过，普通 heredoc 仍然漏检。**

   放入一个 shell fence：

   ```sh
   python3 - <<'PYEOF'
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   PYEOF
   ```

   安全对照只把第二次赋值目标改为 `Q`。这是**同一 fence、同一 Python 执行区**的相邻赋值，不能归为跨 fence 边界。

3. **HIGH — [test_skill_portability_lint.py:1104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1104)：写入枚举遗漏模式匹配捕获，`case P` 可以静默覆盖路径。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   match "/etc/passwd":
       case P:
           pass
   ```

   `MatchAs.name` 不属于目前收集的目标；安全对照为 `case Q`。内存执行确认坏形态最终 `P == "/etc/passwd"`。

**MEDIUM：8 条。**

1. **[test_skill_portability_lint.py:1104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1104)：跨作用域按裸名字合并，函数局部写入被误认成模块变量重赋值。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   def f():
       P = "/etc/passwd"
   ```

   函数没有调用，局部 `P` 也不重绑模块 `P`，当前仍报红；class 局部同名写入同样误报。这里与 HIGH-1 的控制流问题是不同修点。

2. **[test_skill_portability_lint.py:1975](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1975)：顶层转义字符仍标为未保护，导致真命令被当成注释删掉。**

   ```sh
   printf %s \ #; unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   转义空格属于词内，后面的 `#` 不是注释；当前却截断为 `printf %s \ `。将 `unset CLS_BACKEND_URL` 换成 `:` 后，九计数及七组附加结果完全相同。转义分号也会被 `_sh_segments()` 错切。

3. **[test_skill_portability_lint.py:1995](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1995)：命令替换栈遗漏反引号及内部括号结构，提前恢复外层引号后会错误截注释。**

   ```sh
   echo "$( (:) ; printf %s " #")"; unset CLS_BACKEND_URL
   echo "`printf '%s' " #"`"; unset CLS_BACKEND_URL
   ```

   第一行把 `(:)` 的 `)` 当成 `$()` 结束；第二行没有建立反引号子层。两者都会截掉真实 `unset`；追加正常缺省 URL 后，仍能构成全部判据同值的安全／坏对照。`case` 分支的 `)` 也复现同根问题。

4. **[test_skill_portability_lint.py:2070](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2070)、[2072](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2072)：URL 边界按字符判断，仍会把 path/query 当地址起点，也会漏掉引号后的 `@`。**

   以下三条均被放行：

   ```sh
   curl "http://localhost:80/path?target=${CLS_BACKEND_URL:-http://localhost:8011}/x"
   curl "http://localhost:80/""${CLS_BACKEND_URL:-http://localhost:8011}/x"
   curl "${CLS_BACKEND_URL:-http://localhost:8011}"@localhost/x
   ```

   它们与正常缺省 URL 的九计数相同，七组附加全空。`=` 可以属于 query，相邻引号会拼成同一参数，结束引号也不能隔断 userinfo 后缀。

   对你问的分隔符：`; & | < >` 只有在对应 shell 层未引用、未转义时才是结构字符；反引号要按命令替换处理。**遗漏通常造成误报，直接扩大白名单则可能新增漏报**，不能继续仅补字符。

5. **[test_skill_portability_lint.py:2073](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2073)、[2115](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2115)：一处受控展开就放行整词，推翻了删除 env 分支的“恒不决定结果”依据。**

   ```sh
   env -i bash -c "curl \${CLS_BACKEND_URL:-http://localhost:8011}/x; curl ${CLS_BACKEND_URL:-http://localhost:8011}/y"
   ```

   第一处留给清环境后的子 shell 展开，第二处由外层展开；第二处使整个脚本词被放行，env 判据又排除双引号脚本，最终全漏。安全对照只删除第一处反斜杠：九计数相同、七组附加全空。

6. **[test_skill_portability_lint.py:716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:716)、[766](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:766)：bytes 域内单射修好了，但与 str 汇合后的身份仍会碰撞。**

   ```python
   P = b"/t" + b"mp/\xff/x"
   P = "/t" + r"mp/\xff/x"
   ```

   前者含实际 `0xff` 字节，后者含字面反斜杠；两者却生成同一个越界条目。九计数及其他判据也相同，因此登记一个后仍可静默换成另一个。隐式拼接同样复现。

7. **[test_skill_portability_lint.py:1939](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1939)：新增 printf 正则跨越命令边界，把后续 `test -v` 误认成写变量。**

   ```sh
   printf '%s' x; test -v CLS_BACKEND_URL
   ```

   当前返回覆盖命中；实际上这里只输出文本、检查变量存在。`printf -- -v CLS_BACKEND_URL` 等参数文本也误报。

8. **[test_skill_portability_lint.py:2096](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2096)、[2107](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2107)：env 参数识别仍有双向缺口。**

   - `env -i bash -l -c 'curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'` 漏报；合并成 `-lc` 才命中。
   - `env -i bash -c 'true' "${CLS_BACKEND_URL:-http://localhost:8011}/x"` 误报；实际脚本仅为 `true`，变量位于外层已展开的 `$0` 参数。

   两者都是字面参数边界问题，不需要脚本变量数据流分析。

**LOW：1 条。**

- **[test_skill_portability_lint.py:1180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1180)：旧无序 Counter 仍在，最终值合规的相同顺序会因分号／换行不同而改变结果。**  
  `P="/etc/passwd"; P="/t"+"mp/cls-exam/x"` 报红，换成两行即绿；新增断言只验证了换行版本。

其余指定维度：

| 维度 | 结论 |
|---|---|
| 已补六类直接写入目标 | **未发现这些指定形态的残留漏检**；缺少的 `match` 另见 HIGH。 |
| `${var/#pat/rep}` 中的 `#` | **未发现**；安全／加 `unset` 对照正常。 |
| `$((…))` | 确认存在提前出栈、错误切段；属于 MEDIUM-3 同根，最小算术样本未形成额外完整绕过。 |
| 无 `$(` 的普通顶层 `)` | **未发现**空栈弹出问题。 |
| 未闭合引号 | **未发现**可执行单行的新绕过；跨物理行闭合仍属已登记边界。 |
| `_decode_bytes()` 的 bytes 输入域 | **未发现**单射问题；跨类型汇合见 MEDIUM-6。 |
| 删除旧 bytes 叶分支 | **未发现**问题，已有折叠分支覆盖它。 |
| 直接 `-lc`、简单 `$'…'` 样本 | **未发现**残留问题；两条新增纯回归断言均通过。 |
| 性能整改 | 未发现计时入口问题；按禁读边界，**未独立重测**九份正文的耗时。 |

**正确边界应是“同一执行区内的实际绑定与可达执行关系”。** 单个 Python heredoc 应保留跨语句关系；模块、函数、class 的同名局部绑定应区分，`global/nonlocal` 另按实际绑定处理。相邻 fence 可能是不同示例或不同进程，**不应仅凭同名默认串联**。

现有四项残余清单不完整。本轮三个 HIGH，以及上述普通单行词法、参数边界和身份编码问题，应在本卡处理。若跨函数调用导致的 `global/nonlocal` 写入也暂不分析，应另行明确登记；它不能由“脚本变量数据流”含糊代指。

**本轮 BLOCKER 0 条，HIGH 3 条。**
