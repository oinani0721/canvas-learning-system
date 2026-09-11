复核绑定 **`55330069e0bab181d71e7f63c117d63265154a1a`**；收尾时测试文件与提交 blob `b85dd99f16077505f616ceb15044d473895d98a2` 一致。未修改文件、运行 pytest、读取禁读正文或连接网络／数据库。

**仍有 2 条 HIGH。没有发现第四个仍只看叶常量的可达 AST 消费端，但重赋值检查还有两个独立缺口，原文 `/tmp` 指纹也接不住它们。**

**BLOCKER：未发现。**

**HIGH：2 条。**

1. **HIGH — [test_skill_portability_lint.py:1103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1103)：同一单元内，重赋值统计只认直接 `Name` 目标，解包、赋值表达式及增量赋值仍可漏检。**

   ```python
   P = "/t" + "mp/cls-exam/x"; P, = ("/etc/passwd",)
   ```

   安全对照只把第二个 `P` 改成 `Q`。两者九项计数全部为零，越界、可疑、动态、父目录、opaque、URL、块指纹全部 **`[] → []`**，但最终 `P` 从命名空间内变成 `/etc/passwd`。

   同单元的 `(P := "/etc/passwd")`、`P *= 0; P += "/etc/passwd"` 也实证漏检。**本轮修好了赋值值的折叠口径，没有补齐写入目标的识别。**

2. **HIGH — [test_skill_portability_lint.py:1165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1165)：同一 fence 的普通相邻赋值被分开检查，两次写入从未同时进入重赋值判据。**

   ```python
   P = "/t" + "mp/cls-exam/x"
   P = "/etc/passwd"
   ```

   安全对照只把第二行 `P` 改成 `Q`；仍是九项计数和七组附加结果全部相同。

   `_parse_units()` 返回两个单元，`_has_dynamic_tmp_join()` 每次只看到一次赋值。这需要修检查范围，与 HIGH-1 的目标识别是不同修点。**这是同 fence 的普通相邻语句，不是已声明的跨块数据流边界。**

   两条 HIGH 都因源码没有连续 `/tmp`，绕过了 `:2014` 的块指纹入口。

**MEDIUM：5 条。URL 类沿用上一轮的 MEDIUM 评级。**

1. **MEDIUM — [test_skill_portability_lint.py:1969](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1969)：按原文分号切命令段，会切开单引号脚本，造成新回归。**

   ```sh
   env -i bash -c 'true; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"'
   ```

   当前 URL 判据返回 `[]`；去掉 `-i` 的安全对照与它**全部指标、附加结果相同**。第一段留下 `env -i`，第二段才有目标变量，两者关联丢失。原本能抓的单引号脚本，只加 `true;` 就漏。

   同一子 shell 识别面还漏：

   - `bash -c $'curl …'`
   - `bash -c "curl \${CLS_BACKEND_URL:-…}"`：转义的 `$` 留给子 shell 展开。
   - `bash -lc 'curl …'`
   - 先 `SCRIPT='curl …'`，再 `env -i bash -c "$SCRIPT"`。

   前三种是局部词法／选项识别；最后一种需要关联脚本变量。它们不能都归因于 CommonMark 容器栈。

2. **MEDIUM — [test_skill_portability_lint.py:1876](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1876)：新注释状态机不跟踪参数展开和嵌套引用，仍会把有效代码截掉。**

   ```sh
   : ${OTHER:- #}; unset CLS_BACKEND_URL; curl "${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   `_strip_sh_comment()` 截成 `: ${OTHER:- `，真实的 `unset` 消失。安全对照把 `unset CLS_BACKEND_URL` 换成 `:`，全部指标仍相同。本地仅用 Bash 内建命令验证：该展开合法，后面的 `unset` 确实执行。

   同根反例也已复现：

   - `$'a\' #'`：ANSI-C 引号里的转义单引号被误当结束。
   - `echo "$(printf '%s' " #")"; unset CLS_BACKEND_URL`：内外层双引号混淆。
   - 跨物理行的双引号内容第二行以 `#` 开始：状态被逐行重置，后面的 `unset` 漏掉。

   普通词首注释、`${#VAR}`、简单单／双引号案例已修好，**不能据此认定整个状态机正确**。

3. **MEDIUM — [test_skill_portability_lint.py:1964](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1964)：端口文本落在目标展开内，仍不等于目标变量控制实际主机。**

   ```sh
   curl "${CLS_BACKEND_URL:-http://localhost:8011}@localhost/x"
   ```

   与正常 `…}/x` 形态相比，全部指标、附加结果相同。配置为 `https://configured.example:9443` 时，实际 URL 的主机仍是 `localhost`，配置值进入了 userinfo。

   更直接的同根形式也放行：

   ```sh
   curl "http://localhost:80/${CLS_BACKEND_URL:-http://localhost:8011}/x"
   ```

   此处目标展开整体位于路径中。新判准修了上一轮的特定 path 反例，**仍未建立 URL 地址部分的绑定**。

4. **MEDIUM — [test_skill_portability_lint.py:1865](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:1865)：目标变量写入只覆盖直接赋值和部分 `unset/env`，普通数组赋值及 `printf -v` 可架空配置。**

   以下前缀接正常的缺省 URL 命令，URL 判据均为空：

   ```sh
   CLS_BACKEND_URL[0]=''
   printf -v CLS_BACKEND_URL %s ''
   ```

   分别把目标名换成 `OTHER`，得到全部指标相等的安全对照。本地 Bash 内建展开确认，两种坏形态都会使随后的 `:-` 使用缺省值。这不是引号拼接变量名的已登记边界。

5. **MEDIUM — [test_skill_portability_lint.py:704](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:704)、`:754`：`backslashreplace` 仍不是保身份编码。**

   以下是两份独立输入：

   ```python
   P = b"/t" + b"mp/\xff/x"
   P = b"/t" + b"mp/\\xff/x"
   ```

   第一份含无效 UTF-8 字节，第二份含字面反斜杠文本；两者却产生相同的越界候选。九项计数及其余附加结果、块指纹也相同，登记其中一份后仍能被另一份静默替换。

   **`\xff` 与 `\xfe` 的旧碰撞已修；生成的 `\xNN` 与原有 ASCII 文本之间的碰撞未修。**

**LOW：1 条。**

- **LOW — [test_skill_portability_lint.py:2506](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts/backend/tests/skills/test_skill_portability_lint.py:2506)：bytes 身份断言只覆盖显式 `+` 链，没有钉住叶常量解码。**

  仅把 `:754` 的 `backslashreplace` 内存回退为 `replace`，**95 次纯函数用例仍全部通过**；但隐式拼接的 `b"/t" b"mp/\xff/x"` 与 `…\xfe…` 已再次同归 U+FFFD。当前叶分支实现正确，缺的是这一分支的防回归断言。

**折叠及目标变量消费端完整清单**

下表列判据实现入口，不把测试样本和基线常量重复算作消费端。行号均属同一测试文件。

| 判定点 | 实际口径 | 复核结论 |
|---|---|---|
| `:229 / :1662 / :1664` 正文总数、命名空间数 | 源码字面 | 明确的计数契约 |
| `:1685` scripts `/tmp` 计数 | 源码字面 | 独立 scripts 没有 Python 折叠保护 |
| `:355 / :1002` 裸 token | 源码字面 | 与解析候选并收 |
| `:529` 嵌入 span 所在词含 `/tmp` | 原始词文本 | 不折叠、不执行 shell |
| `:722–754` Python 候选生产 | 叶值＋最外层完整折叠值 | 收集口径已统一；身份问题见 MEDIUM-5 |
| `:979` 越界候选含 `/tmp` | Python 值／shell 词／span 内容／裸 token | 取决于来源 |
| `:1119` `tmp_targets` | **折叠值** | 本轮修复成立 |
| `:1131` 动态起点 `starts` | **折叠值** | 未发现叶常量遗漏 |
| `:1136` 旧 bytes `replace` 分支 | 叶值 | 上面的 `_fold_str()` 已覆盖其命中条件，属冗余分支 |
| `:1176 / :1177 / :1178 / :1182` 动态预筛 | delta＋整段折叠值＋源码／bytes 兜底 | 整段预筛修复成立 |
| `:1227 / :1239 / :1251 / :1253 / :1257 / :1271` opaque | 原始 span／词／行／续行组 | 不折叠 Python |
| `:1292 / :1294` 可疑行 | 原始逻辑行中的 `/tmp`、`..`、`$` | 文本证据判据 |
| `:2014 / :2029` 块／段指纹入口 | **源码字面 `/tmp`** | 普通拆分常量也能绕过，实际影响见两条 HIGH |
| `:2151` 父目录散文 | 原始散文行 | 文本证据判据 |
| `:1108–1122` 重复赋值的目标名 | AST 直接 `Name.id` | 覆盖缺口见 HIGH-1 |
| `:1953` URL 赋值 | 剥注释后的源码正则 | 见 MEDIUM-2、4 |
| `:1970 / :1972` URL `unset` | 原始命令段正则 | 不是 shell 参数解析 |
| `:1932 / :1933 / :1938` `env` 清环境及脚本含变量 | 选项／脚本源码文本 | 见 MEDIUM-1 |
| `:1964–1966` URL 缺省展开 | 源码位置包含关系 | 见 MEDIUM-3 |

因此，对“第四个消费端”的准确回答是：**未发现第四个漏用折叠值的可达 AST `/tmp` 判断；存在仍只看原文的外围入口，尤其第十条，不能把它宣传成覆盖所有折叠形态的兜底。**

注释处理也不应机械统一：计数、内容指纹本就绑定原文；Python AST 自然忽略 Python 注释；可疑／opaque 是保守文本证据。它们不统一调用 `_strip_sh_comment()` 本身不是新缺陷，**URL 语义判据使用一个不完整的 shell 注释器才是本轮确认的问题**。

**其余问题逐项结论**

| 维度 | 结果 |
|---|---|
| 长短单元 Counter 差值 | **未发现扣丢。** 短单元同值一次、长单元同值两次，最终准确贡献两次。 |
| `grown is None`、`seen`、跳过覆盖行 | **未发现新问题。** 已收 delta 保留，失败尾部从 `cur_j + 1` 继续处理；没有复现重叠候选重复计数。 |
| 40 行及固定次数上限 | 当前代码已无这些上限。题目中的旧限制不适用于最终 HEAD。 |
| 续接词冒号、`pass` 探针 | 当前正则只是 `elif/else/except/finally/case`；旧 `_has_continuation_after()` 无调用。不能按旧探针推断当前行为。 |
| heredoc 结束符、长单元并集 | 指定的歧义形态回归断言通过；**未发现本轮新增候选丢失**。宽触发仍可增加解析成本。 |
| `With`、装饰器、默认参数、推导式、`keyword/Starred/NamedExpr` 的常量上溯 | 对含路径常量的有效表达式，**未发现新节点放行**；`NamedExpr` 改写另一个既有变量的问题已列 HIGH-1。 |
| 未闭合语法吞到块尾 | 在验证的形态中，**未发现后续候选永久丢失**；失败后仍会降级、继续扫描。未证明任意畸形输入的成本上界。 |
| `_normalize_span()` | **未发现新回归。** 换行和首尾一对空格归一化符合目标语义；原文指纹仍区分源码变动。 |
| 两处 `normalize=False` | 用于跨行判断和原文定位，合理。当前生产调用只有 `:999/:1007/:1226/:1251`，交接函数没有直接调用它。 |
| backtick 掩码、opening／closing | 与本地 CommonMark 解析器比较 **488,280** 个短串，**未发现差异**；不是对完整 Markdown 文档的证明。 |
| 无容器 fence 字符、长度、缩进及 tab | **12,000** 组 CommonMark 对照未发现双向错误。 |
| fence 内以 `- ` 开头的代码 | 散文分段先跳过 fence 体，**未发现被列表段边界误切的新问题**。 |
| 原文 slice 与容器剥离 | **未发现行号错位。** 剥前缀不删物理行，原文 slice 保持对应。 |
| 指纹行序、空白、换行 | 当前是 **sha16、不 `strip()`**；行序、行内及行尾空格变化会改摘要。CRLF/LF 和末尾换行归一化；尾部纯空行可等值，未复现由此新增普通代码债。 |
| 缓存纯度／污染 | **未发现。** 内部 tuple 及字符串不可变，外部修改返回 list 不污染下一次结果；不读取业务外部状态。 |
| `_shell_words()` | 仍不能充当完整 shell lexer：转义引号、未闭引号、反引号内空格及 `$'…'` 有边界；且 `\s` 实际也切 Unicode 空白。URL 后果见上述 MEDIUM，含原文 `/tmp` 的改动通常另被指纹接住。 |
| `${X-…}`、`${X:?…}`、数组展开、`printf` 拼端口 | 目标变量无冒号 `-` 可过 URL 判据，但 `p8011_ns` 会变化；`:?`、数组展开当前会报 URL；`printf … 8011` 也会报。**未发现这些直接替换整体静默**，但数组写入另见 MEDIUM-4。 |
| 引号内只是说明文字 | `printf '%s' 'unset CLS_BACKEND_URL'` 仍误报；正则没有区分命令与数据。单引号包住整个缺省 URL 又会被当作有效展开。 |
| 来源 `fence:`／`prose:` | 格式调整改变来源或提取次数可以报红；表示基线提取结构变化，不能直接解释为新增同等数量的物理路径债。 |
| U5-B／U6 常量 | 常量覆盖及交接正反形态通过，**未发现新问题**。U5-B 仍需同步相关附加基线；U6 scripts 维持独立计数契约。 |

**容器和跨块边界：维持转分块卡的处置，不重复计本轮 HIGH。**

closing 尚未全面正确，双向反例都存在：

- `:421 / :555`：`-    ~~~py\n     A=1\n       ~~~\nP=1`，CommonMark 第三行闭合，模块继续吞到末尾；列表 marker 后的合法填充未完整计入基线。
- `:421 / :443`：` > ~~~py\n > A=1\n>\t  ~~~\n > P=1\n > ~~~`，模块在第三行提前闭合，CommonMark 不在这里闭合。
- `:283`：合法的 `>    ~~~py` 被拒绝开启。
- `:626`：剥前缀没有按实际层级限次，`>> P=1` 的额外 `>` 可以被剥掉。

列表／引用、setext、HTML 的段边界因此不能认定完整正确。按你提供的“当前九份不用这些结构”，不能声称现有正文已经受影响；但新增引用或调整列表缩进就能触发，**不是只存在于刻意构造中的理论问题**。

不含 `/tmp` 的块里改变量用途，或改变这些块的划分，指纹仍可完全不变。这个已声明边界覆盖普通变量传递、后续重赋值、命令参数改变，实际面远大于特殊编码；本轮两条 HIGH 进一步证明，**甚至无需跨块**。

**成本和断言承重**

合成 1,000 个普通赋值单元的实测如下；未读取九份正文做性能测试。

| 对照 | 中位耗时 | parse 次数 |
|---|---:|---:|
| 当前完整动态判据，冷缓存 | 15.04 ms | 1,000 |
| 仅禁用字符串缓存 | 24.02 ms | 2,000 |
| 当前完整动态判据，暖缓存 | 0.785 ms | 0 |
| 内存移除整段预筛，暖缓存 | 0.333 ms | 0 |

该暖路径增加约 **0.453 ms**；缓存命中时已经不是“每单元多一次 parse”。当前性能哨兵确实覆盖完整动态路径，但其真实树耗时未验证。

- 大形态表当前 **51 行**，指名坏形态红、安全对照绿；三判据分工表当前 **16 行**。**未发现指名判据选错。**
- 块指纹独立复算为 **45/51**。未区分的六例实际是 **4 个 URL＋2 个源码没有连续 `/tmp` 的 Python 拼接**，并非全部 URL。
- 当前 r13 兜底表只有 **8 例，8/8 接住**。缺少历史第九例，不能独立确认“8/9”。
- 两处历史内存变异——去掉 fence 同字符条件、恢复分号截断——都使指名断言失败。
- 本轮多个整改分支逐个回退，指名断言确实变红；但这不能覆盖 LOW 中单独回退仍绿的叶解码分支，也不能代替未执行的整树性能验证。
- `:3832`“至少有人红”由前面的指名断言逻辑蕴含，没有额外承重；属于已知冗余。

收尾判断：**残余风险尚未完整声明，仍有普通写法即可触发、可静态确定的漏检。** 同 fence 重赋值和简单 `env` 脚本切段值得在本卡处理；更广的容器解析、脚本变量数据流可以另卡，但应明确其覆盖限制，不能统称为 CommonMark 问题。

**本轮 BLOCKER 0 条，HIGH 2 条。**
