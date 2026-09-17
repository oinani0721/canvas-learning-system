# 独立复核请求 round-4 — CARD-AILINKED-4TH-WRITER（绑定最终 HEAD）

## 一 本轮性质与最小读取面

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills`
分支 `card/t7-skills`。**本轮审查绑定 `HEAD = 341a88b6`**。

round-3 已给出 **B0 / H0 / M0 / L0**（绑 `12f85104`）。本轮之所以再送一次，是因为我采纳了
round-3 的「清洁附注」并**动了代码**，而本仓规矩是「审后再改代码必再送一轮」。

**本轮唯一改动**（`git diff 12f85104 341a88b6 -- . ':(exclude)_bmad-output'`）：
`backend/tests/skills/test_ai_linked_doc_writer.py` 里 2 个**裸** U+2028 改为字面转义写法
` `。成因是写文件时 JSON 解码把转义序列变成了真实码点；讽刺的是这 2 个字符正好落在
「⛔ 源码里用 ` ` 转义写，不敲裸码点」那条注释和它下面的反例里 —— 名实不符。
Python 解析字面 ` ` 后仍是同一码点，门④(ii) 的输入不变。

请读：

1. `git diff 12f85104 341a88b6 -- . ':(exclude)_bmad-output'`（**本轮全部改动**）
2. `git diff d5ad6fca 341a88b6 -- . ':(exclude)_bmad-output'`（本卡全部代码改动，5 文件）

## 二 请核对的三点

1. **本轮改动是否真的行为等价**：门④(ii) 那个参数化子用例喂给写点的 `event_id` 是否仍是
   `derive:测试` + U+2028 + `节点`（12 个码点）？注释与实际写法现在是否一致？
2. **不可见字符复查**：地盘五文件里还有没有裸的 U+2028 / U+2029 / U+0085 / C0 / DEL？
   作者侧实测结果是：四个文件 0 处；`backend/tests/regression/test_learning_events_schema_contract.py:369`
   有一处 `U+001C`，但那是 `d5ad6fca` 就存在的既有测试输入（刻意喂坏行用），**非本卡引入**，
   且不在本卡可改范围（不在 `test_real_producer_ai_linked_doc_writer` 函数体内），故未动。
   请独立确认这个判断。
3. **round-3 的全部结论在新 HEAD 上是否依然成立**（若无变化可简短确认即可）：
   UTF-8 坏行隔离 / parsed-field 相等 / fd 生命周期 / LF 守卫 / 形态门码点集 /
   门⑪ 集合 4 份 / 两处 `<>` 占位 / producer 门只动了一个函数 / backend 仅改注释。

## 三 作者侧本轮实测

- `tests/skills` 目录级 **555 passed**（基线 546 + 本卡 9）；本文件五门单跑 **9 passed**。
- `SKILL.md` 本轮**未改动**，其 `sha256` 与 `test_skill_portability_lint.py` 里的基线指纹
  仍逐字相同（`f3673ca9…`）。
- `ruff check` 与 `ruff format --check` 均通过。
- 因 SKILL.md、`backend/app/**`、`tests/unit` 面本轮均未触及，`pyright`（上轮 `0 errors,
  81 warnings`）、四个 regression 文件（`569 passed / 1 skipped`）与 `tests/unit`
  （红集与 64 条基线逐条相同）未重跑 —— 如你认为该重跑请指出。

## 四 输出格式与边界

- 按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句定位思路；没有的分级写「无」。
- **只读**，不修改任何文件；不连任何数据库（7691 / 7687 不碰）。
- `pyright` 若在你的环境仍启动失败（前三轮报缺 `libllhttp.9.3.dylib`），如实写「未复证」即可。
- 不评 `start-exam-board/SKILL.md:477` 的同类子串残留（已登记移交，非本卡面）。
