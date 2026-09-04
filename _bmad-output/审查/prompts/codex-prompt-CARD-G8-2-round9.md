# CARD-G8-2 独立对抗审查（round-9 · 用户授权定向续轮第六轮）

你是独立审查者。round-1..8 存档于 codex-review-CARD-G8-2*.md；round-8 你判
0 BLOCKER + 3 HIGH + 4 MEDIUM。本轮复核 round-8 全部发现的整改。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-8 三条 HIGH 的整改声明（证伪优先，不成立标 REGRESSED）

### H1：AUTO 段切分吞 fence opener，跨段 fence 状态丢失
整改：**放弃切分逐段解析**，改 `_blind_auto_lines(body)`——等行数盲化（AUTO 段内普通行
替换为 `<!--x-->` 注释行；**fence 标记行原样保留**以维持 Markdown 连续性），整文喂 mdit。
你的反例（AUTO 头 + ~~~text + END + [[A]] + ~~~）下 mdit 看到完整 fence → [[A]] 在 fence 内
→ A 报孤儿。fence 标记行保留拆除 = 变异 M24。

### H2：未闭合 AUTO 段到 EOF 被降级普通正文
整改：`_blind_auto_lines` 的 in_auto 状态到 EOF 期间所有行都已盲化（无降级路径）。
你的反例（AUTO 头 + `- [[A]]` 无 END）→ [[A]] 在注释行内 → 盲 → A 报孤儿。
BEGIN 状态机入口拆除 = 变异 M23。

### H3：text.content 是 mdit 解码后文本，转义/实体假 [[ 逃逸
整改：inline token 的 `map` 给出原文行区间——采纳前回**原文行**断言存在
`(?<!\\)\[\[`（未被反斜杠转义的裸 `[[`）。你的两个反例：
- `\[\[A\]\]`：原行全转义，无裸 `[[` → 不采纳 → A 报孤儿（真无链 baseline）
- `&#91;&#91;A&#93;&#93;`：原行无裸 `[[`（实体字面）→ 不采纳 → A 报孤儿
  （⚠️ 口径申报：Obsidian 对实体形式的渲染行为未定，本实现取 fail-closed 多报孤儿方向，
  差异登记验收单「不比什么」）
map 回原文判定拆除 = 变异 M25（恒 True 全采纳 → escaped 用例红）。

## 二、round-8 四条 MEDIUM 顺带整改

- M1：`_md_parser` 的 ImportError → `LintConfigError`（CLI rc=3）；新门
  `test_missing_markdown_it_is_config_error`（builtins.__import__ 注入模拟缺包，
  锁 _md_parser 与 run_checks 接线；CLI 跨进程不可注入，如实声明）。
  requirements.txt 显式声明按批次约定移交 DEBT-1（第九批），UAT §7 登记。
- M2/M3：UAT 全文统一 round-9 终态（195 passed / 22 mutant / SHA b6ee8a1a…）；§6.11
  live sha 门覆盖面收窄声明已落位（basename 排除 + symlink 不覆盖）。
- M4：orphan 权威口径声明——UAT「本卡未证明什么」明确：orphan 按 **markdown-it-py
  可渲染文本**裁判，与生产图（obsidiantools connect 建图）口径可能不同；HTML 内
  `[[A]]`（mdit 判 html_inline → 不扫）在生产图中是否成边未验证，登记为口径边界。

## 三、终态裁判（当前字节，MANIFEST 绑定）

referee1-pytest-full-round9.txt = **195 passed**（76 本卡 + G8-1 119 零回归）+
22/22 mutant KILLED（M23 BEGIN 入口 / M24 fence 行保留 / M25 回原文判定为 r8 新防线）+
live 第九轮 sha `a82e3af0…` 前后逐字相同 rc=0 + 禁改门空 + MANIFEST 全覆盖（时序：生成于
全部证据落定之后）。

## 四、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-8 各条若整改不成立标 REGRESSED；区间/AUTO 重构引入的新面请重点对抗
（等行数盲化的 mdit 交互 / map 跨段偏移 / `\Q` 转换器）。最后一行：
`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
