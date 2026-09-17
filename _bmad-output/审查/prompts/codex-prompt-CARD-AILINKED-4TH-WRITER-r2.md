# 独立复核请求 round-2 — CARD-AILINKED-4TH-WRITER

## 一 背景与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
分支 `card/t7-skills`。**本轮审查绑定 `HEAD = 65e3f333`**（round-1 审的是 `41629ec3`）。
前一卡 tip `PREQ = d5ad6fca`。

round-1 结论为 **0 BLOCKER / 0 HIGH / 2 MEDIUM / 1 LOW**，三条已全部整改（见下）。本轮请
**优先核对整改是否到位、有没有引入新问题**，然后再做一次全面复核。

请读：

1. `git diff 41629ec3 65e3f333 -- . ':(exclude)_bmad-output'`（**本轮整改的全部改动**）
2. `git diff d5ad6fca 65e3f333 -- . ':(exclude)_bmad-output'`（本卡全部代码改动，5 文件）
3. `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` 的 **Step 5.5** 小节（写点 PYEOF 块，:214-348）
4. `backend/tests/skills/test_ai_linked_doc_writer.py` 全文（四门）
5. `backend/app/services/learning_event_log.py:188-343`（backend 侧参照实现，只读）
6. `backend/tests/regression/test_learning_events_schema_contract.py::test_real_producer_ai_linked_doc_writer`

## 二 round-1 三条的整改内容（请独立核对）

### MEDIUM-1 → 坏行的代价必须只限于那一行
查重循环的异常捕获从 `except ValueError` 改为 `except (ValueError, RecursionError)`
（SKILL.md 查重循环内）。理由采纳你的实测：深层嵌套坏行在部分 Python 版本上抛的是
`RecursionError`，它一旦逸出到外层 `except Exception`，本次事件就**不落账**了。
请核对：还有没有别的异常类型能从逐行解析里逸出并吃掉整次落账？

### MEDIUM-2 → 计时起点与夹具健康断言
原先 `t0` 在「两个写者就绪之后」才取，而 `HOLD_S` 从持锁方报 `held` 就开始走 ——
准备耗时若过长，**正确实现**也会被 ③ 判红。现改为：记 `t_held`（持锁开始）与 `t0`
（写者放行）两个时刻，`elapsed` 仍从 `t0` 起算，但增加夹具健康断言
`prep = t0 - t_held < HOLD_S * 0.25`，超出即明确报「夹具问题，判据不可比」，
不混进写规判据。实测 `prep ≈ 0.03s`，上限 `1.0s`。
请核对：这个处理是否同时挡住了「准备慢 ⇒ 正确实现假红」与「准备慢 ⇒ 缺陷实现假绿」
两个方向？`HOLD_S * 0.25` 的取法有没有别的漏洞？

### LOW-1 → 让「两写者各补一次 LF」那条并发面真的有人测
你指出门③ 只有单写者、门② 的账本又都是空文件或正常 LF 结尾，所以那条
`"\n\n" not in raw` 此前没有任何并发场景喂给它。现在：
- 门② 的档 B 预置内容**最后一条不带尾随 LF**（`truncated_tail=True`）；
- 门② 从三条判据增为**四条**，新增 ④「账本无空行」，判的是档 B 的账本原文；
- 门③ 里那条 `"\n\n"` 的注释改为如实说明它只是单写者形态的廉价回归。

负控实测（五段，每段前后 `shasum -a 256` 逐字相同）：
- 段②（去掉 `fcntl.lockf`）→ 门② **4/4 全红**（档A n=2 / 档B n=2 / size=462 / elapsed=0.01s / 有空行）
- 段⑤（锁内同 fd 读换成二次 `open`）→ 门② **红 ①④、而 ②③ 仍绿**
  （档A n=1，档B n=2，**size-at-release=0**，**elapsed=3.99s**）
  —— 即：写点确实等到了锁、确实没在别人持锁时抢写，却照样重复落账并造出空行。

请核对：段⑤ 这组数字是否确实支持「①（恰一条）不可被 ②③ 替代」这个结论？

## 三 你在 round-1 指出但我**未**采纳的一点，请确认判断

你提到「外层使用四个反引号即可容纳内层三个，因此『fence 绝不能嵌套』的理由不准确」。
这一点你是对的，措辞我已在 commit message 与验收单里收敛为「三反引号 fence 不能套三反引号
fence」。但写点仍然移到了 Step 5.5，理由改为**位置正确性**而非纯技术不可行：那条 bullet
是给 Skill 执行者的 Bash 动作（原文「新节点写入成功后」），此前被放在 Step 3 给**生成器**的
System Prompt 模板里；Step 5 才是「写新节点文件」。
请判断：这个理由是否足以支撑该移动？留在模板里的其余 bullet 是否仍然自洽？

## 四 仍需复核的原有问题（若 round-1 的结论在新 HEAD 上依然成立，可简短确认）

⓪ parsed-field 相等是否覆盖「历史行中非 event_id 字段的值恰等于新 evid」这条此前未被拦下的输入。
① fd 生命周期：锁内是否全程同一个 fd、`close` 是否在锁内、有无隐式重开账本的路径。
② LF 守卫是否在锁内、`raw` 为空时不补 LF 是否正确。
③ 形态门：首尾空白拒写不 strip、码点集与校验器 `validate_learning_events.py:426` 是否同集、
   门④ 三类反例在 `derive:` 前缀下是否都可达。
④ 外形与提取：`learning_events.jsonl` 字面量是否仍在（门⑪ 集合 4 份）、块正文无行首 `PYEOF`、
   两处 `<>` 占位逐字保留、producer 门是否只动了 ai-linked-doc 那一个函数。
⑤ backend `learning_event_log.py` 是否仅改注释（去 docstring 后 AST 与 PREQ 相同）。

## 五 输出格式与边界

- 按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句定位思路；没有的分级写「无」。
- **只读**，不修改任何文件；不连任何数据库（7691 / 7687 不碰）。
- round-1 你报告 `pyright app` 在你的环境启动失败（Node 缺 `libllhttp.9.3.dylib`，退出 250）。
  作者侧实测为 `0 errors, 81 warnings`（cwd=`backend/`）。若你本轮仍跑不起来，如实写「未复证」即可。
- 不评 `start-exam-board/SKILL.md:477` 的同类子串残留（已登记移交，非本卡面）。
- 不评「完整 vault 里真实跑一次 ai-linked-doc skill」——本卡只逐字提取写点模板用 subprocess 跑。
