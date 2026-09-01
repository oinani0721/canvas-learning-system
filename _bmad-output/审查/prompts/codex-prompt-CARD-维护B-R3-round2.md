# Codex 定向复核 · CARD-维护B-R3（只审中文数词与计数的取值口径）

你是对抗复核者。历史：round-1 FAIL(3B/5H/3M)；round-2/round-4/本卡 R3 round-1
三次被你侧内容过滤器截断、无终裁；round-3 FAIL(2B/4H) 已整改；round-5 判
**A ✅PASS / B ✅PASS / C ⚠️HIGH**。本轮只复核 C。

工作树: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v2-recapfix

## ⛔ 硬限（三次被截断的教训，请严格遵守）

1. **不要运行 `git diff` / `git show` / `git log -p`**。前一轮就是因为把整段改动
   读进上下文而被中断。只**按下面给出的 file:line 静态阅读当前 HEAD 的文件内容**。
2. **不要构造或运行任何探针 / 变异 / 临时脚本**。车道已提供全部实测数据。
3. **不读 `fixtures/` 下任何 `.md`/`.json` 正文**。
4. 只做两件事：**按行号读代码与测试** + **跑下面两条既有命令**。
5. **报告第一行**：「BLOCKER/HIGH 清零：是/否（就 C 取值口径而言）」。

## round-5 对 C 的判词（属实）

> 提取字符集与映射表完全相同 ⇒「无法验证」分支静态不可达；连续数字字仅反复
> 覆盖 `digit`，可能只保留末位并按**错误的小值**去数值池比对；若发生池碰撞，
> 同类允许式仍可通过。

## 车道两次整改（本轮被审对象）

| # | 车道实测到的问题 | 整改 |
|---|---|---|
| 1 | `c754b043` 只改了 fallback 一侧；`_verify_prose_counts` 仍调多位解析器 `_cjk_to_int`，`本板共有一零个子节点。` 得 0（0 恒在池内，`abs(a-a)`）⇒ exit 0 | 删 `_cjk_to_int`；两处共用 `_cjk_single_to_int`（只认单字，值=映射）；提取字符类由 `_CJK_NUM ∪ _CJK_UNIT` 机械派生 |
| 2 | 整改 1 之后仍有：`本板共有九十八万**五**个子节点。`（Markdown 粗体，渲染出来是「九十八万五个」）只取到尾片 `五`，5 在池内 ⇒ exit 0。ASCII 同形 `980 005个` 只取到 `005` | 数串**跨连接字符整体取出**再剥掉连接字符后判值；CJK 与 ASCII 同一口径；诊断打印还原后的完整数串 |
| 3 | 整改 2 自带的新问题：行级「前导零归一化」与整体取出相冲，`1 000个`（渲染=1000）被剥成 `1 0` 拼成 `10` 落进池内 ⇒ exit 0 | 删除行级剥零，归一化下沉到 `int(token)` |

⚠️ 车道如实声明：问题 2 在 `c754b043` 上**同样存在**，是存量、不是本卡引入；
但本卡的门与 docstring 曾宣称「多字中文数词一律 fail-closed」，被一个 `**`
击穿 = **声明比证据宽**，按本仓口径算真缺陷，故闭合。

车道还删掉了一条**永不触发**的"左边界守卫"（能命中它的形态都先被整体取出吞掉），
理由：死分支冒充防线正是 round-5 判过的病。

## 请按行号阅读（`canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py`）

- `:1355-1391` — `_D2_NOISE_ONE` / `_INVISIBLE_ONE` / `_D2_JOIN_ONE` / `_join_free`
  / `_D2_COUNT_RE`（连接语义与 ASCII 取数口径）
- `:1481-1536` — `_CJK_NUM` / `_CJK_UNIT` / `_CJK_NUM_CHARS` / `_CJK_NUM_RUN_PAT`
  / `_cjk_single_to_int` **实现体**
- `:1650-1685` — D2 叙述段的两个取数循环（CJK 与 ASCII）与前导零口径注释
- `:1915-1935` — fallback 允许式的取数循环

**请回答的三个问题**：
1. 还有没有别的路径能让「进池比对的值」≠「读者在渲染后看到的数」？
2. `_D2_JOIN_ONE`（连接集）、`_D2_QUANT`（量词表）、`_CJK_NUM`（数词表）三张封闭表
   的边界，车道在下面「已登记残余」里写得诚实吗？有没有被低估的？
3. possessive `*+` 是否改变了匹配语义（而不只是性能）？

## 请按行号阅读（`backend/tests/regression/test_recap_scan_signals.py`）

`:3124` 判据契约（注意：期望值已改为**独立写死**——原版
`for ch, want in _CJK_NUM.items()` 是自抄期望，把映射改成 7 也全绿）、
`:3184` 与 `:3364` 两道合成 scan 单元门、`:3216`、`:3251`、
`:3288` 切断矩阵门（含放行面），以及既有 `:3088`。

**请回答**：有无空洞断言（不改实现也恒真）？有无比实现宽的措辞？
`assert "九十八万五" in r.stdout` 这类「诊断须还原完整数串」的断言够不够强？

## 两条命令（只跑这两条）

1. `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
   tests/regression/test_recap_scan_signals.py -q -p no:cacheprovider`
   —— 开工基线 249，现应为 **255**。
2. `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
   tests/regression/recap_domain_negverify.py` —— 应为 **14** 条变体全部如期变红。
   其中 survivor-13（数串不再跨连接字符）只杀切断矩阵门 1 条。
   **请判断**：survivor-13 / survivor-14 是否真的禁掉了该性质的全部防线，
   还是被别处纵深兜住而误判承重？

## 车道已登记的残余（请判断登记是否诚实）

- 连接集是封闭表：`九十八万x五个`、`九十八万、五个`、`[[目标|]]` 残留的 `|]]`
  仍会断开。车道判词：这些断点**渲染后可见**；>22 字符的 HTML 注释是真残余。
- D2 只覆盖「数字**紧邻**量词」的计数形态：`共有节点九十八万，其中种子五个。`
  中的 `九十八万` 无量词 ⇒ 不进检查面（ASCII 同形同样不进），docstring 早已声明。
- 数词表封闭在 17 字：壹貳參、廿卅、仨俩 不在提取面内。
- `:1311` 与 `:1319` 另有两份手抄的中文数词字符类，未随机械派生（当前字符集相同）。
- 新代价：`本板共有一两个 / 三五个 / 十来个子节点` 现在硬 FAIL（旧实现分别得
  2/5/10，多在池内而放行）。按卡文默认「无法确定语法的中文数词一律 fail-closed」。

## 输出格式

- 第一行：「BLOCKER/HIGH 清零：是/否（就 C 取值口径而言）」。
- 逐项 ✅/⚠️/❌ + `file:line` 判词。**新问题不限于「本卡引入」**——存量未闭合的
  也请报，并标注是哪一类。
- 写出你实际跑出的两条命令结果，以及 `git rev-parse HEAD`（只跑这一条 git 命令）。
- 报告一次给出；先写正文再补过程。
