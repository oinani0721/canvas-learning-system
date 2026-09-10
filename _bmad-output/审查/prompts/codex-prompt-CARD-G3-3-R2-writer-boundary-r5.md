# 独立代码复核请求（round-5，末轮）— CARD-G3-3-R2-writer-boundary

## 一 背景与最小读取面

仓库根（只读）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

round-4（存档 `_bmad-output/审查/codex-review-CARD-G3-3-R2-writer-boundary-r4.md`，绑定 `aa4a89fc`）
给出 BLOCKER 0 / HIGH 0 / MEDIUM 1（`.strip()` 与 `:391` 的同源遗漏，判为「整改未闭合」）/ LOW 1
（TAB 那条 docstring 措辞误述）。两条均已整改。本轮绑最终 HEAD `61590b3b`，是本卡末轮。

**请只读以下范围**（不要运行任何写操作）：

1. `git diff aa4a89fc 61590b3b -- . ':(exclude)_bmad-output'` —— round-4 整改的全部代码改动（2 文件）
2. `canvas-vault/.claude/skills/quiz-answer/SKILL.md` 的 `:385-445`
   （`_harness_tree` 的三处 s-white 口径：键值正则两侧、注释分隔、末尾 strip、引号分支）
3. `backend/tests/regression/test_g3_2_review_ledger.py` 的 `:6960-7060`
   （TAB 三态 docstring 措辞更正；值首 Unicode 空白的新增参数化用例）

## 二 作者自述（round-4 整改声明）——请独立核对，不要采信

1. **M1'''**：同一函数的四处空白判据现已统一到 YAML s-white（SP/TAB）：
   - 键值正则：`^harness_tree:[ \t]*(.*?)[ \t]*$`
   - 引号分支：`^(['\"])(.*?)\1[ \t]*(?:#.*)?$`
   - 注释分隔：`re.sub(r'[ \t]+#.*$', '', _raw)`
   - 末尾：`.strip(" \t")`
   作者声称：round-4 表格里的四条形态在已修版上复验通过，其中
   `/repo<U+3000><SP>#alt` 现在保留 `U+3000` 后 fail-closed 拒（不再静默换树）；
   `harness_tree: <U+3000>#alt` 现在按相对路径处理后拒（不再静默回退父目录）。
2. **L1'''**：TAB 那一态的 docstring 已改为「正则层剥掉不拒，拒来自更下游的 config
   读取层」，只钉端到端不静默，并写明读取层若容忍 TAB 该用例会报红而非假绿。
3. 新增参数化用例断言：值首 `U+3000` / `U+00A0` + `#` 时 rc≠0、拒因含 `harness_tree`、
   **拒因里能看到那个不可见字符与 `#alt`**、账本零行、写入面逐字节不变。

## 三 请按重要性排序回答的问题

1. 四处 s-white 收窄之后，`_harness_tree` 还有没有**任何**剩余路径会把用户写的值
   静默改成另一个值（换树）或静默当作没写（回退）？请把它当作一次穷举检查：
   引号分支、值首 `#`、注释剥除、strip、expanduser、相对路径拼接、normpath —— 逐段说明
   哪些字符会被改动、是否可能改变「指向哪棵树」这一结论。
2. `os.path.normpath` 与 `expanduser` 这两步本身会不会引入同类问题（例如 `..` 归约
   把路径指到另一棵存在的树、`~` 展开在无 HOME 环境下的行为）？
3. 新增的「值首 Unicode 空白」用例，其断言 `f"{_lead}#alt" in stderr` 是否真的承重——
   有没有可能在**门没修好**的情况下这条断言仍然通过？
4. 末轮总检：对这张卡的三件产物（`self_confidence_norm` 写点门、`event_id` 形态门、
   `harness_tree` 解析）以及配套测试判据，是否还有 BLOCKER/HIGH。
   若只剩 MEDIUM/LOW，请明确标注哪些是「登记即可」、哪些仍属「必须闭合」。

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
- `_bmad-output/` 下除前四轮存档外不必阅读。
