# 独立复核请求 — CARD-SKILL-PORT-LINT（BATCH-2026-09-07-第十三批 / 车道 U4 / round-27）

## 一 背景与最小读取面（只读这些，不要扩大）

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u4-hosts`
分支 `card/u4-hosts`。**本轮绑最终 HEAD**：`fcab3216` → **`9c29aacb`**。

轮次说明：r5 是 D-15 的 5 轮上限，用户随后授权继续，故有 r6/r7/r8/r9。
本轮唯一代码 commit `9c29aacb` 是按你 r9 的 5 HIGH + 2 MEDIUM + 3 LOW 全部整改。

**请只读下面这些**：

1. r8 之后的整改 diff（**本轮重点**）：`git -C <树根> diff 6540e409 9c29aacb -- . ':(exclude)_bmad-output'`
2. 全区间代码 diff：`git -C <树根> diff 9303201a 9c29aacb -- . ':(exclude)_bmad-output'`
3. 新测试全文：`backend/tests/skills/test_skill_portability_lint.py`
4. 你上一轮的报告：`_bmad-output/审查/codex-review-CARD-SKILL-PORT-LINT-r8.md`

**不要读**：`quiz-answer/SKILL.md` 正文（3076 行，本卡一字节未改）、live vault 下的文件、
其它车道的卡文。

## 二 round-26 的处置

⛔ 你指出我 r25 的**修法方向**不对（「结束标记存在仍不足以证明 heredoc 解释成立」），
这条我照收 —— 判别换成**引号**：

| 形态 | 判别 |
|---|---|
| `<<'A'` / `<<"A"` 带引号 | **一定**是 heredoc（Python 里 `x << 'A'` 毫无意义，shell 里无歧义） |
| `<<A` 不带引号 | 看这一行本身能不能当合法 Python 解析（`N = 1 << 2` 能 ⇒ 左移；`python3 - <<A` 不能 ⇒ heredoc） |

缺结束标记时正文取到**块尾**，不再整个丢掉。

| 你的意见 | 整改 |
|---|---|
| **HIGH-1（回归）** 缺结束标记时真执行区被丢弃 | 见上 |
| **HIGH-2（回归）** 整词搜 `c`/`m` 侵入带参数选项的参数 | 短选项**逐字符按序**扫，遇 `W`/`X`/`Q` 停止把余下字符当选项 |
| **HIGH-3（回归）** `(P): str` 被误收为局部绑定 | 要求 `AnnAssign.simple` |
| **HIGH-4（既存）** 命名空间写入仍有静默形态 | 目标补 `Attribute`；`_NS_MUTATORS` 补 `__ior__`/`__delitem__`；`del globals()[…]` |
| **MEDIUM-1（误报）** 反射识别混淆方法名/读取来源/写入目标 | 六处收窄（`vars()` 必须无参数、`sys.modules` 接收者必须是 `sys`、`X.__dict__` 递归判、`.reload` 只认 `importlib`、命名空间作参数只在未绑定 `dict.update` 算写、目标必须在 **Store/Del** 上下文） |
| **MEDIUM-2（误报）** `unset` 不是命令词也被算 | `unset` 必须是该段命令词（只允许 `VAR=值` 前缀）；选项词一并去引号 |

**回退验证 14 处全部承重**，其中**第三次**照出「验过没钉住」（`(P): str` 只在临时探针
验过、没进断言），已补。

⛔ **我把你一直在替我做的事收进了流程**：新增
`_bmad-output/审查/evidence-skill-lint/self-regression-diff.py` —— 送审前自己跑
**逐 commit 对照**（35 个历代形态 × 7 判据 + 13 条 URL 行 = 258 个观测点，逐条比两个
版本）。本轮首次实测 `6540e409 → 9c29aacb`：11 处差异，5 处是本轮修的漏检、6 处是本轮消的
误报，**全部有出处**。以后每轮送审前先跑它，不再让你替我找我自己的回归。

判据仍 **10 条**，测试 169 → **171**。真实树 冷 391ms / 暖 173ms。

## 三 请按重要性排序回答的问题

1. **heredoc 的「引号判别」这个口径本身对吗**？（这一问最重要 —— 它替换的是判别式）
   - 带引号一律认：有没有 shell 里 `<<'X'` **不是** heredoc 的情形（比如 `[[ $a << 'b' ]]`、
     `case` 模式、`$(( 1 << 2 ))` 算术里）？
   - 不带引号才看 Python 可解析性：`python3 - <<EOF` 之外，有没有**能**当 Python 解析
     的**真** heredoc 开启行（那样会被误否）？
2. **本轮又引入回归了吗**？我自己跑的 258 点对照没发现意料之外的差异，但我的语料
   只有 35 个形态 —— **它显然不完备**。请优先对照 **`6540e409` 能抓、`9c29aacb` 漏掉**。
   另外：我该往语料里补哪些形态，才能让这个自检下次真的替我挡住？
3. **`_is_namespace_expr()` 六处收窄，有没有收过头**？现在
   `vars()` 必须无参数、`sys.modules` 接收者必须字面是 `sys`、`.reload` 只认 `importlib`
   —— `import sys as s; s.modules[…]`、`from importlib import reload; reload(…)`、
   `m = globals(); m["P"] = …` 这三种现在分别是什么结果？方向是漏还是误？
4. **`_provably_last()` 的沉默条件**到本轮为止够严了吗？还有什么形态**满足**
   「必经 + 非延迟求值 + 源码在后 + 非搬运」却仍能让合规值被覆盖？
5. 分界：**本卡应修完**与**可另立卡**，到这一轮为止划对了吗？

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出 `file:line` + 一句话说明**在什么输入
或什么改动下这条会出问题**。没有问题的维度请明确写「未发现」，不要省略。
最后单独给一句结论：本轮 BLOCKER 与 HIGH 各几条。

## 五 边界

- 只读，不要修改任何文件；不要连任何数据库或网络服务。
- 不要跑 pytest（`sandbox` fixture 会复制大文件）。可直接用树内
  `backend/.venv/bin/python` 动态加载被测模块，调用 `_body_counts()` / `_fence_blocks()` /
  `_is_inline_span()` / `_strip_quote_prefix()` / `_backtick_spans()` /
  `_has_embedded_span_near_tmp()` / `_py_needs_more()` / `_sh_needs_more()` /
  `_parse_units()` / `_py_strings()` / `_sh_words()` / `_fold_str()` / `_quiet_parse()` /
  `_has_dynamic_tmp_join()` / `escaping_tmp_paths()` / `suspicious_tmp_lines()` /
  `dynamic_tmp_join_lines()` / `parent_dir_prose_lines()` / `opaque_tmp_lines()` /
  `_script_counts()` / `check_handoff_constants()` / `_discover_out_of_scope_8011()` 等纯函数。
- 不评二线宿主（Codex / OpenCode / dsh）的可跑性 —— 那是另一张卡的范围。
- 不评 `quiz-answer/SKILL.md` 的内容质量 —— 本卡对它只钉计数、一字节未改。
- 不评 `_bmad-output/` 下的文档措辞。
