# CARD-G6-9c-R3 独立审查请求（round-2）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`，基线 `9c4e7e82`，审查绑定 `d062e2b145bc4faa244324228cc29697854158cb`。
批次 `[BATCH-2026-09-18-第十五批 / CARD-G6-9c-R3]`。

这张卡做三件事：

1. **移植**：第十四批 T3-A 的五文件代码面躺在未合分支 `card/t3-review @ a8cefab4`（整卡因 Codex r12 仍留 4 条 HIGH、末 commit 未送审而不合），本卡把它原样移植到 `9c4e7e82` 之上（commit ①），逐字节不改。
2. **去 3.11+ 正则语法**：R2 用 Python 3.11+ 的占有量词 `[0-9]++` / `*+` 与原子组 `(?>…)` 修 r12 的四条 HIGH。但本项目在 launchd 链上有一条**兜底解释器**路径——`scripts/daily-review-push.sh:10-11` 在 venv 缺席时改用系统自带的 `/usr/bin/python3`（本机 3.9.6），而 `:149` 直接跑 `scripts/daily_review_run.py`。R2 那一版在 3.9.6 上 **import 即 `re.error: unknown extension ?>`**。本卡撤掉这些语法，改以 **`std_off` 在正则里必填**消除「std 名与 dst 名瓜分同一串名字字符」的歧义分割点来保住线性。
3. **三件尾巴**：`daily_review_pick.py` 的模块级 `_DISPLAY_TZ` 改每次现取（用户裁定 D-18）；负控 runner 入树；补一处 r12 H4 的漏网入口。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color 9c4e7e82 d062e2b145bc4faa244324228cc29697854158cb -- . ':(exclude)_bmad-output'
scripts/local_tz.py                                   （终态全文）
backend/app/core/display_tz.py                        （只看它与 scripts/local_tz.py 的 diff，应仅 docstring 首段）
backend/app/api/v1/endpoints/review_overview.py:375-575
scripts/daily_review_pick.py:243-265（_display_tz 定义与那段设计说明）, 390-415, 1018-1040, 1128-1140, 1310-1320
backend/tests/regression/test_local_tz_negctl_r3.py    （新文件，全文）
backend/tests/regression/test_g6_9c_single_tz_source.py
    ⚠️ **按符号名定位，不要按行号** —— 本卡多轮改动后文件已 2760 行，任何写死的行区间都已失实
    （作者上一轮就在自己的注释里踩过这个）。本卡新增/改动的符号：
      · `test_r12_h1_*` / `test_r12_h2_*` / `test_r12_h3_*` / `test_r12_h4_*`
      · `test_r3_leading_colon_*` / `test_r3_non_ascii_digits_*`（×2）
      · `test_r3_both_copies_import_on_the_fallback_interpreter`
      · `test_r3_pick_side_reevaluates_display_tz_every_call`
      · `test_r1_dst_quoted_name_never_falls_back_to_bare_name`
      · 辅助（本卡在**该文件**新增的全部 7 个）：`_module_level_assignments` / `_grid_specs` /
        `_libc_accepts` / `_libc_utcoffset` / `_declared_narrowing` / `_parser_of` /
        `_module_with_widened_digit_class`
        （`_oracle_h3_linear` 在 `test_local_tz_negctl_r3.py`，不在本文件）
      · 5 组直接赋值 `picker._display_tz = …` 的夹具（grep `picker._display_tz`）
    精确面以 `git diff 9c4e7e82 HEAD -- <该文件>` 为准。
_bmad-output/审查/evidence-g69cr3/r12-input.md         （第十四批 Codex r12 存档原文，本卡的输入）
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md
    ⚠️ 必须读 **feature 主干树那一份（241 行）**，不是本车道树里的同名文件（111 行、只有 T6-B 一张卡）。
    相关内容在 `## 二、第十四批全批复核与合并`：第 119 行「T3-A 不合」的裁定
    （负控 runner 红、COLONPOSIX 变异存活 rc=0、r12 四条 HIGH、`a8cefab4` 未送审、轮次 12 > 5）、
    第 121 行「T3-B/C/D 脱离 T3-A 合入」（含 hunk 区域不重叠的实证：T3-A :385–:555 / T3-C :797+ / T3-D :1945+）、
    第 225 行 `CARD-G6-9c-R3` 的必排条目。
    （卡文写的「§2.1 / §2.7」与该文件的实际章节号对不上，本卡按内容定位，已在验收单登记。）
.claude/rules/card-batch-protocol.md                   §1 合并门 / §2.1 存档首部
```

## ①-bis 上一轮（round-1）的处置 —— 请独立核对每一条是否真的收口

round-1 判 **BLOCKER 0 / HIGH 2 / MEDIUM 1 / LOW 2**，存档
`_bmad-output/审查/codex-review-CARD-G6-9c-R3-r1.md`（请读它，本节只是索引）。
五条**全部已改**，改动集中在一处正则 + 若干门。请逐条核对，不要采信本节说法。

### HIGH-1：dst 引用名退回裸名

**上一轮给的未被拦下的输入**：`A1<B>>2` / `A1<B>C>2` / `A1<B><C>2`
（libc 全年 UTC，当时本实现给冬 −01:00 夏 −02:00，dst 名打成 `B>`）。

**改法**：dst 裸名分支加 `(?!<)`，与 std 第三支同形。

**请核**：这一族现在是否与 libc 同拒？有没有**新的**误拒（合法引用名被一起拒掉）？
`AAA1<>2`（空引用名）、`A1<B>2`（正常闭合）这类对照输入是否仍收？

### HIGH-2：数字字段之间的平方回溯

**上一轮给的负控输入**：`parse_posix_tz("A" + "1"*n + "+")`，n=3232 约 0.40 s。

**改法**：dst 名量词 `*` → `+`，另开 `(?=[+-])` 一支表示「空名但下一个是符号」。
依据是「空 dst 名后面必须跟符号 —— 否则两串数字连着，本来就该被 std_off 一次吃完」
（`AAA111` 的偏移是 `111` 而不是 `11`+`1`）。空名不能直接删：r12 M1 实测 `AAA1+2` 是
dst 名空 + 偏移 `+2` 的合法形态。

**改后的 dst 组**：`(?P<dst><[^>\x00]*>|(?!<)[^0-9+,\-\x00]+|(?=[+-]))`

**请核**：
- 平方是否真的消失（请自己计时，报形态与数值）？
- 还有没有**别的**「两个相邻同类贪婪段 + 中间可空项」的分割点？

  ⚠️ 作者这次没有等你指出来才补 —— 上一轮的教训是「被指出一处补一处」，
  所以本轮**按结构枚举**了这个形状的全部候选。

  ⛔ **但第一版枚举错了，作者自己的对抗自审抓出来的，这里如实交代**：
  v1 按「**同角色**组」配对（std/dst、std_off/dst_off、stime/etime、start/end），
  可回溯发生在**文本相邻**的衔接处 —— 这四对之间都隔着别的组，根本不接触。
  8 个组的真实串接顺序是 `std → std_off → dst → dst_off → start → stime → end → etime`，
  共 **7 个相邻衔接点**，v1 表里只覆盖到 1 个（dst→dst_off）。
  而且 v1 写的判据「两个相邻同类贪婪段 + 中间可空项」**自相矛盾** —— 相邻就没有中间项。
  **v1 的结论（没有第三处平方）是对的，论证不成立。** 这正是最难自查的一类：
  绿灯会让人不再回头看论证。

  v2 换成一条能机械施行的判据：每个衔接点上
  **前一个贪婪段吃的字符类 ∩ 后继的 FIRST 集 = 空集**
  （不相交 ⇒ 前段贪婪吃到底后，每个回退位置上后继的首字符检查立刻失败 ⇒ 每步回溯 O(1)）。
  落在 `_bmad-output/审查/evidence-g69cr3/g69cr3-split-point-enumeration-v2-20260918T222356.txt`
  （v1 的 `…-20260918T210703.txt` 保留在库里，作为「结论对但论证错」的留痕，**不作依据**）：

  | 衔接点 | 分隔符 | 字符类∩FIRST | n=202 | n=3232 | 比(理论16) |
  |---|---|---|---|---|---|
  | std→std_off | (无) | ∅ | 0.000004 | 0.000059 | 13.5 |
  | std_off→dst | (无) | **{`:`}** | 0.000018 | 0.000285 | 15.7 |
  | dst→dst_off | (无) | ∅ | 0.000014 | 0.000216 | 15.1 |
  | dst_off→start | `,` | ∅ | 0.000010 | 0.000153 | 14.7 |
  | start→stime | `/` | ∅ | 0.000006 | 0.000080 | 14.0 |
  | stime→end | `,` | ∅ | 0.000007 | 0.000098 | 13.6 |
  | end→etime | `/` | ∅ | 0.000007 | 0.000094 | 13.4 |

  另测 5 处**组内部**形态（std_off 冒号 / dst_off 冒号 / stime 冒号 / 引用名内部 /
  规则 M 小数点段），n=3232 最慢 0.000256 s。合计 12 种形态全部线性，门限 0.05 s。

  ⚠️ `std_off→dst` 的交集**不空**（交出 `:`），判据在这里给了保守的假阳性；实测把它挡了回来 ——
  因为 std_off 的冒号被 `(?::[0-9]+(?::[0-9]+)?)?` 这个**有界**结构吃掉，不是无界贪婪段。

  **请核**：v2 的判据本身站不站得住？「前段字符类 ∩ 后继 FIRST」对**有界重复**
  （如 std_off 的三段冒号）是不是根本不适用，需要另一条判据？7 个衔接点 + 5 处组内部，
  是不是就是全部？分支内部（std 的三支之间、dst 的三支之间）算不算独立的分割点？
- 计时门现已覆盖 5 维（`name-arabic` / `name-ascii` / `digits` / `digits-colon` /
  `digits-after-name`）。这 5 维够不够？有没有第 6 维？

### MEDIUM：H4 扩展入口只断言「不抛」

**改法**：改为断言「返回非 None」且**逐串对 libc 偏移**，新增 `_libc_utcoffset` oracle。

⚠️ 作者第一版把三个串套了同一句写死断言 `== timedelta(hours=-1)`，结果被自己的门判红 ——
`AAA1,J…,J365` 几乎全年 DST，冬季落在窗口**内**，该给 dst 偏移 0 而不是 std 的 −01:00。
**三个串本来就都与 libc 一致，错的是断言。** 现在改成逐串问 libc。

⛔ **第二处自审抓出的问题，也在这里交代**：作者新写的 `_libc_utcoffset` **口径写反了**。
它按「**UTC 瞬时**」算偏移（`naive.replace(tzinfo=utc).astimezone().utcoffset()`），
却拿去和 `tz.utcoffset(dt)` 的「**墙钟**」语义比。反例 `AAA5,J15/9,J300` 在 01-15：
实现给 −20:00，这个 oracle 给 −19:00 —— **门会把正确的实现判红**。
已改成 `time.localtime(time.mktime(naive.timetuple())).tm_gmtoff`（墙钟口径），12/12 对齐。
这条与上面「断言写死常量」是同一个根因的两次发作：**新写的判据本身没有被任何东西检验**。

**请核**：改后的 oracle 口径对不对？墙钟口径在 DST 切换的**重叠小时**（同一墙钟时刻对应
两个 UTC 瞬时）上，`mktime` 的 `tm_isdst=-1` 会挑哪一侧，这个歧义会不会让门在某些串上
不稳定？`_libc_utcoffset` 与既有 `_libc_accepts` 的 TZ 保存/还原是否一致？有没有在某个
副本参数下泄漏进程 TZ？两处新加的 `try/except RuntimeError`（无 `tzset` 的平台）会不会
把「门根本没跑」伪装成「门通过了」？

### 两条 LOW

negctl 三段说明改为实际失败位置；picker 说明更正了「谁持有旧实例」的方向
（是**测试模块自身**持旧实例，runner 在函数内 import 取到新实例）。

**请核**：说明现在与代码是否一致？还有没有别的名实不符的说明？

### 上一轮作者未采纳的建议（请判断是否该坚持）

`expect_msg` 加固（给 negctl 每段声明关键词、断言它出现在失败消息里）**本轮未做**，
理由是 round-1 已实测「当前九段没有发现红在无关对照输入上的情况」，加固会再断一次终审绑定。
请判断这个取舍是否成立。

## ①-ter 送审前的独立自审（commit `d062e2b1`）—— 请把它当作**未经外部检验**的一轮

round-1 收口后（`6242aff4`），作者没有直接送 round-2，而是先跑了一轮自己的对抗自审
（6 个视角各自找问题、每条再由 3 个独立视角尝试**反驳**，只有反驳失败的才留下）。
它找出 **4 处真问题**，全部修在 `d062e2b1`：

1. `_libc_utcoffset` 口径反了（详见上文 MEDIUM 段）—— 会把正确实现判红。
2. **H4（长数字剥零）的门只钉了 5 个调用点中的 2 个**。`int(x.lstrip("0") or "0")`
   这个形态在两副本里共 5 处：②的两处范围检查、`_parse_rule` 的 `mon/week/dow` 与 `n`。
   原门只探到 2 处 ⇒ 另外 3 处退回 `int(x.lstrip("0"))` 也不会红。探针 2 → 7，逐调用点各一条。
3. **`_display_local` 把配置断裂吞成 `None`**（`scripts/daily_review_pick.py`）。
   `_display_tz()` 原先在 `try` **内部**调用，而 `local_tz.display_tz()` 对无效 `CANVAS_TZ`
   抛 `ValueError`（D-18:「配置断裂要说话，不静默退化」），这个 `try` 的 `except` 正好含
   `ValueError` ⇒ 无效时区被静默压成「这条时间戳解析不出来」，整页安静地少几行。
   已把取时区提到 `try` 之外。实测（两解释器一致）：`CANVAS_TZ=Not/AZone` ⇒ 抛 `ValueError`；
   `CANVAS_TZ=Asia/Tokyo` ⇒ 正例不受影响。
4. 分割点枚举 v1 的论证错误（详见上文 HIGH-2 段）+ 两处文案与代码不符。

⚠️ **这一轮没有任何外部检验** —— 自审的 6 个视角和 3 票反驳都是同一个作者的产物。
上面 4 条既是「作者已经知道的问题」，也是**最值得你怀疑作者还漏了同型第二处**的地方。
特别是第 2 条：一道门只覆盖了它声称覆盖的面的 40%，而门是绿的。

**请核**：这 4 条改对了吗？同型的第二处还有没有？
尤其 —— **本卡新写的每一条判据（oracle / 探针 / 计数门），谁来检验它？**

---

## ② 作者自述，请独立核对

以下每一条都请自己复现，不要采信本节的说法：

1. **四条 HIGH 在移植后就已经是绿的**。本卡在移植后、改任何一行之前用 libc（`time.tzset()` 四元组）实测四组输入全部与 libc 一致（存档 `evidence-g69cr3/g69cr3-red-high-pre-*.txt`）。所以本卡在这四条上的贡献是「**保住**它们同时去掉 3.11+ 语法依赖」，不是修复。请核对这个归属是否属实。
2. **正则改写与 R2 语义等价**。31 万条组合样本上 `parse_posix_tz` 的返回语义（None / key + 冬夏偏移 + tzname）与 `a8cefab4` 分歧 0；候选正则在 3.9.6 与 3.14.4 两个解释器上对同一样本集的判定指纹逐字节相同。请自行以 `time.tzset()` 组合对拍，**报形态而不是只报 rc**。
3. **线性性质换了承载层**。R2 靠占有量词（引擎禁止回溯），本卡靠 `std_off` 必填（文法消除歧义分割点）。请核对这个推理是否成立，以及计时门是否真能抓回溯。
4. **三段 R2 存活变异的真因**。本卡实测它们不是空操作：`COLONPOSIX` 拆的是一道与正则前瞻**互为冗余**的检查（单拆任一层零观测差异）；`ASCII` / `RULEA` 拆的是在当前正则下**恒真**的两道 `isascii()`（192 条匹配样本触发 0 次），但把正则的 `[0-9]` 放宽成 `\d` 之后它们**会**接住 —— 即它们是真正的纵深第二层。请核对这两个判断。
5. **pick 改现取零产出变化**、两副本逐字节同源、3.9.6 / 3.14.4 双解释器 import 通过。
6. ⚠️ **作者在这张卡上栽过一次，主动交代**：卡文 §〇 说「测试侧钉住 `_DISPLAY_TZ` 的 **5 处**」，
   那个清单是在**移植之前**的主干代码上数的。移植进来的 R2 版 `test_g6_9c_single_tz_source.py`
   自带**另外 5 组**直接属性赋值（`picker._DISPLAY_TZ = ZoneInfo(...)` + try/finally 还原），
   `tests/unit/test_review_overview.py` 还有**第 6 处** monkeypatch —— 合计漏改 6 处，
   承重套件首跑 **11 failed**（`AttributeError: module 'daily_review_pick' has no attribute '_DISPLAY_TZ'`）。
   修复 commit `feb5a593`，判据同时升级为 **AST 级全仓扫描**
   （`ast.Attribute` / `ast.Name` / `ast.Constant` 三态一起数）：`_DISPLAY_TZ` 代码引用 **0**，
   验伪锚同一扫描器对 `_display_tz` **53**。
   **请独立核**：全仓是否真的再无 `_DISPLAY_TZ` 的代码引用？还有没有别的
   「卡文 §〇 的计数在移植后失效」的地方（例如别的文件里对 pick 模块级状态的依赖）？
7. ⚠️ **第二跤，也主动交代**：pick 现取门第一版用 `spec_from_file_location("daily_review_pick", …)`
   + `sys.modules[...] = mod` 重新 exec 了 pick，而 `daily_review_run` 在**它自己的 import 期**
   已持有旧实例 ⇒ 后续 `test_daily_review_run` 的夹具钉新实例、runner 用旧实例，**静默失效**。
   表现：`test_g67r_runner_save_does_not_clobber_web_written_board_done` **单跑绿、多文件同跑红**
   （`assert {} == {'A板': '2026-07-30'}`）。已改成与本文件其余 4 处同形的普通 `import`
   （commit `c6a7f446`），并删掉那个辅助。
   **请独立核**：本文件里还有没有别的会污染 `sys.modules` / 全局状态的写法？
   `tests/regression` 目录级同跑时，本卡新增的 9 条用例有没有给别的文件留下副作用？
8. ⚠️ **第三跤**：(k)① 负控的 trap 还原第一版用相对路径，而 trap 在 `cd backend` 之后执行 ⇒
   `> scripts/local_tz.py` 静默创建了 `backend/scripts/local_tz.py`，真生产文件留在**变异态**。
   由跑后 `git status` + `shasum` 自证判据当场抓出并立即还原；脚本已改绝对路径并加了
   「变异标记残留」「误建文件核」两道判据。
   **请独立核**：现在两段负控的还原是否在**所有退出路径**上都执行得到（含 pytest 非零退出、
   Python 脚本抛异常、trap 自身失败）？存档里的 sha256 对照是否足以证明生产文件没被改过？

## ③ 请按重要性回答这些问题

⓪ **解析器的接受域是否仍与 libc 有可观测分歧？** 请自行以 `TZ=<串>` + `time.tzset()` 组合对拍，报具体形态（哪个串、libc 给什么、本实现给什么），不要只报通过/失败。特别关注本卡改动引入的新形态：`std_off` 必填之后，原先「匹配成功但被校验层 ⑥ 拒」的那一族现在走「根本不匹配」这条路——这两条路的返回值是否在**所有**输入上都相同？

① **计时门是否真能抓回溯？** 本卡把判据改成了「n=3232 绝对门 ≤0.05s + 相邻比 ≤3 + min-of-5」，并在注释里声明卡文原写的 `t(808)/t(202) ≤ 3` 对真正线性的实现也会红（长度是 4 倍，线性耗时本来就 ≈4，实测基线 3.55）。这个更正是否成立？把 `std_off` 改回可选之后这道门是否真红？

② **negctl 的空操作预检能否被「old 与 new 只差注释」骗过？** 预检用的是「去 docstring 后的 `ast.dump`」。注释不进 AST、docstring 被剥 —— 但还有没有别的「改了源码而 AST 指纹不变」的写法能混过去？

③ **negctl 的主判据只验「抛了 AssertionError」，不验「抛的是哪一条断言」** —— 作者已自查并如实登记（验收单 §五.11）：预检④排除了「oracle 本身坏了」，`_load_source` 抛非 AssertionError 排除了「变异体加载失败」，但**同一个 oracle 内部多条断言时，变异可能红在不是它设计要红的那一条上**。请判断：这个缺口在当前 9 段变异上是否**实际可达**（哪一段、红在哪条断言）？如果可达，给出最小加固（作者的候选是给每段声明 `expect_msg` 关键词并断言它出现在失败消息里）。

④ **pick 改现取后，全部 11 处夹具是否仍真钉住时区**（而不是给一个不存在的名字赋值）？
两种钉法都要看：`monkeypatch.setattr(picker, "_display_tz", lambda …)`（6 处）与
直接属性赋值 `picker._display_tz = lambda …` + `try/finally` 还原（5 组）。
`monkeypatch.setattr` 对不存在的属性默认会抛，但请核对是否有 `raising=False` 或等价旁路；
直接赋值那 5 组没有这层保护，请特别核它们的还原是否在所有路径上都执行到。
另：第一版那个 `spec_from_file_location` + `sys.modules[...]` 的辅助已在 `c6a7f446` **删除**
（全仓 grep 该名 = 0）。请核：删干净了吗？本文件与 `test_daily_review_run.py` /
`test_g6_9_boundary_matrix.py` 现在拿到的是不是**同一个** `daily_review_pick` 模块对象？
测试执行顺序变化（`-k` 子集 / `-p xdist` 分发 / 单文件跑 vs 目录级跑）会不会让某一组夹具失效？
⚠️ 这一条作者已经栽过一次（见 §② 第 7 跤：单跑绿、多文件同跑红），请当成**高危面**核。

另：11 处钉法的构成，作者实测为 **6 处 `monkeypatch.setattr(picker, "_display_tz", …)`**
（`test_review_overview.py` / `test_daily_review_run.py` / `test_daily_review_pick.py` /
`test_g6_9_boundary_matrix.py` ×3）**+ 5 组直接赋值**（全在 `test_g6_9c_single_tz_source.py`）。
AST 全仓扫描另有 1 处 `monkeypatch.setattr(vl, "_display_tz", …)`（`test_vault_lint.py:666`），
那是 **`vault_lint` 自己的** `_display_tz`，与 pick 无关、不在本卡改动面 —— 请核这个归类对不对。

⑤ **`.key` 的 UTF-8 严格性是否有旁路？** 例如 `CANVAS_TZ` 那一档（它走 `ZoneInfo(name)` 而不是 `parse_posix_tz`）、或 `/etc/localtime` 那一档。

⑥ **pyright `0 errors` 是否靠 `# pyright: ignore` 掩盖？** 本卡自称零新增 ignore。

⑦ 本卡删掉了生产代码里的 ⑥（`if not g["std_off"]: return None`，正则改必填后不可达），却**保留**了测试辅助 `_declared_narrowing` 里的同名检查（理由写成「那里的职责换成了类型收窄」）。这个「同一类情形两种处置」的辩解是否站得住？

⑧ **本卡新写的判据，谁检验它？** 自审这一轮 4 条里有 2 条（`_libc_utcoffset` 口径、
H4 门只覆盖 2/5）都是「**新加的门本身是错的**」，而门是绿的、套件是过的。请把
`test_g6_9c_single_tz_source.py` 与 `test_local_tz_negctl_r3.py` 里**本卡新增**的每一条
oracle / 探针 / 计数门当成被审对象：它断言的那件事，和它实际能观测到的那件事，是不是同一件？
哪一条在「被测实现变坏」时**不会**红？

⑨ **分割点枚举 v2 的判据（前段字符类 ∩ 后继 FIRST = 空集）对有界重复是否适用？**
详见上文 HIGH-2 段。若不适用，正确的判据该是什么？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给 `file:line` 与一句复现思路。

措辞只用这四个词：**负控输入** / **对照输入** / **未被拦下的输入** / **门未覆盖的路径**。

## ⑤ 边界

- 只读，不要修改任何文件。
- 不连数据库（本卡零连库；7691 / 7687 / 7692 都不适用）。
- **不评** P5-B 的面：`review_overview.py:2572+` 的三态、`review_app.py` 的徽标、`daily_review_run.py:748-753` 的 skip-nokey、`canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:430` 的固定 +08:00、G6-8 模板冻结。
- **不评** r12 的 13 条 MEDIUM / 2 条 LOW（含 `review_overview.py` 的 `+15:00` 误拒与 `future` 单调假设）——已登记，本卡只收口 HIGH 面。
- `display_tz()` 的三档解析次序（CANVAS_TZ > TZ > /etc/localtime > 固定偏移）是用户裁定的 D-18 语义，不在本卡讨论范围。
- 2007..2037 之外的年份与 C 库有**已声明**的分歧（C 库在区间外用 posixrules 的历史转换表 / 32 位表止于 2037），不算缺陷。
