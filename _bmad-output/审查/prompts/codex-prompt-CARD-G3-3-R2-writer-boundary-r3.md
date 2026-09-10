# 独立代码复核请求（round-3）— CARD-G3-3-R2-writer-boundary

## 一 背景与最小读取面

仓库根（只读）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

round-2（存档 `_bmad-output/审查/codex-review-CARD-G3-3-R2-writer-boundary-r2.md`，绑定 `b060259b`）
给出 BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 1。作者逐条独立复现后全部整改。本次复核**整改后的最终态**；
round-2 起累计三轮，本轮重点是被改过的三处。

**请只读以下范围**（不要运行任何写操作）：

1. `git diff b060259b 23b26e6e -- . ':(exclude)_bmad-output'` —— round-2 整改的全部代码改动（2 文件）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:290-440`
   （`_harness_tree` 裸值 `#` 语义修复——round-2 M1'；注释记录了两轮判据演化）
3. 同文件 `:1480-1620`（行号已按你的提示放宽：读 `:1521`、复放 `:1535`、拼 `:1609`——三行仍未改）
4. `backend/tests/regression/test_g3_2_review_ledger.py` 的 `:6760-7040`
   （零写指纹的 symlink 维度——M2'；锁豁免按形态匹配——L3'；
   两端点对照的 `#` 回归用例——M1'）

## 二 作者自述（round-2 整改声明）——请独立核对，不要采信

1. **M1'**：裸值注释判据 = 「`#` 前有空白，或 `#` 是值的第一个字符」。依据：
   键值正则 `^harness_tree:\s*(.*?)\s*$` 的 `\s*` 已吃掉冒号后空白，故
   `harness_tree: # reset` 的值区首字符就是 `#` ⇒ 以 `#` 开头 ⇒ 空值回退；
   `/repo#alt` 的 `#` 前无空白 ⇒ 保留为路径（fail-closed 或采用，取决于树是否存在）；
   `/repo # 注释` 剥注释。作者声称这与 YAML 1.1/1.2 标量规则一致。
2. **M2'**：指纹函数先 `is_symlink()`（不跟随）记 `("symlink", None, os.readlink(q))`，
   再 `is_dir()`、最后按文件读内容。判据自证探针之二：造目录链接、换一次指向，
   两次指纹必须不同（防指纹函数对该维度失明的空真）。
3. **L3'**：`_allowed_entries` 把期望**形态**写死——`.locks` 必须是 `("dir", None, None)`，
   锁文件必须是 `("file", 0, sha256(b""))`；`_allowed_entries.get(k) != v` 即 unexpected。
   于是「`.locks` 被建成非空普通文件」与「锁文件非空」都会被拒。
4. round-2 你确认无需改动的项（M1 引号形态、M4 caplog 固定实参、写点数值门分支、
   L7/L8）本轮**未再改动**。

## 三 请按重要性排序回答的问题

1. M1' 修复后的判据有没有**第三种**错误形态？特别看：值首字符是 `#` 但用户本意是
   路径（`harness_tree: #hashtag-dir`——以 `#` 开头的目录名）；值中间 `#` 前是
   制表符/全角空格等非 ASCII 空白（`\s` 在 Python re 里对 Unicode 空白的覆盖）。
   这些形态下行为分别是什么、是否与注释声明一致。
2. M2' 的 symlink 指纹对**断链**（dangling symlink，readlink 成功但目标不存在）的
   行为；以及 `rglob("*")` 对 symlink 指向目录时是否会枚举**链接目标内部**的条目
   （Python 的 `Path.rglob` 对目录 symlink 默认不递归——若递归，`backend-disabled`
   类条目会被算进指纹）。
3. L3' 的形态约束在「锁文件已存在于 `_before`」（重跑场景）时是否仍然成立——
   此时它不出现在 `_added` 里，`_changed` 判据能否看见它被写入内容。
4. 三轮累计之后，你对这张卡整体（写点门 + 形态门 + E-2 解析）还有没有**新**的
   BLOCKER/HIGH 级别问题。MEDIUM/LOW 若属测试判据可收紧项，请标注「登记即可」。

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：

- 级别
- `file:line`
- 一句话说明问题
- 一句话说明如何观察到它

没有问题的级别请明确写「无」。

## 五 边界

- 只读复核，不要修改任何文件，不要运行测试或任何写操作。
- 不要连接任何数据库或网络服务。
- 不评审 `start-exam-board` 与 `ai-linked-doc` 写点（登记项）。
- 不评审变异 harness 全量覆盖率（U8-B 的面）。
- `_bmad-output/` 下除 round-1/round-2 存档与 L7 探针存档外不必阅读。
