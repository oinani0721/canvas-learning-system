# CARD-G6-9c-R3 独立审查请求（round-1）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`，基线 `9c4e7e82`，审查绑定 `967cf4cf78ef68164d64d2ab8bc87995de417d4b`。
批次 `[BATCH-2026-09-18-第十五批 / CARD-G6-9c-R3]`。

这张卡做三件事：

1. **移植**：第十四批 T3-A 的五文件代码面躺在未合分支 `card/t3-review @ a8cefab4`（整卡因 Codex r12 仍留 4 条 HIGH、末 commit 未送审而不合），本卡把它原样移植到 `9c4e7e82` 之上（commit ①），逐字节不改。
2. **去 3.11+ 正则语法**：R2 用 Python 3.11+ 的占有量词 `[0-9]++` / `*+` 与原子组 `(?>…)` 修 r12 的四条 HIGH。但本项目在 launchd 链上有一条**兜底解释器**路径——`scripts/daily-review-push.sh:10-11` 在 venv 缺席时改用系统自带的 `/usr/bin/python3`（本机 3.9.6），而 `:149` 直接跑 `scripts/daily_review_run.py`。R2 那一版在 3.9.6 上 **import 即 `re.error: unknown extension ?>`**。本卡撤掉这些语法，改以 **`std_off` 在正则里必填**消除「std 名与 dst 名瓜分同一串名字字符」的歧义分割点来保住线性。
3. **三件尾巴**：`daily_review_pick.py` 的模块级 `_DISPLAY_TZ` 改每次现取（用户裁定 D-18）；负控 runner 入树；补一处 r12 H4 的漏网入口。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color 9c4e7e82 967cf4cf78ef68164d64d2ab8bc87995de417d4b -- . ':(exclude)_bmad-output'
scripts/local_tz.py                                   （终态全文）
backend/app/core/display_tz.py                        （只看它与 scripts/local_tz.py 的 diff，应仅 docstring 首段）
backend/app/api/v1/endpoints/review_overview.py:375-575
scripts/daily_review_pick.py:243-265（_display_tz 定义与那段设计说明）, 390-415, 1018-1040, 1128-1140, 1310-1320
backend/tests/regression/test_local_tz_negctl_r3.py    （新文件，全文）
backend/tests/regression/test_g6_9c_single_tz_source.py:2265-2641  （本卡新增段，共 9 条用例 + 2 个辅助）
    以及 :1880-:2180 的 5 组 picker 夹具（本卡把 `picker._DISPLAY_TZ = …` 改成了 `picker._display_tz = lambda …`）
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
另：作者新加的 `_load_module_from_scripts("daily_review_pick")` 用**真实模块名**写
`sys.modules`，与同文件里 4 处 `import daily_review_pick as picker` 共存 —— 请判断两种
加载路径拿到的是不是同一个模块对象，以及测试执行顺序变化（`-k` / `-p xdist`）会不会让夹具失效。

⑤ **`.key` 的 UTF-8 严格性是否有旁路？** 例如 `CANVAS_TZ` 那一档（它走 `ZoneInfo(name)` 而不是 `parse_posix_tz`）、或 `/etc/localtime` 那一档。

⑥ **pyright `0 errors` 是否靠 `# pyright: ignore` 掩盖？** 本卡自称零新增 ignore。

⑦ 本卡删掉了生产代码里的 ⑥（`if not g["std_off"]: return None`，正则改必填后不可达），却**保留**了测试辅助 `_declared_narrowing` 里的同名检查（理由写成「那里的职责换成了类型收窄」）。这个「同一类情形两种处置」的辩解是否站得住？

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
