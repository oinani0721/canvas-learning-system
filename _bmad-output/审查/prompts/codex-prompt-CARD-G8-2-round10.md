# CARD-G8-2 独立对抗审查（round-10 · 用户授权定向续轮第七轮）

你是独立审查者。round-1..9 存档于 codex-review-CARD-G8-2*.md；round-9 你判
0 BLOCKER + 3 HIGH + 7 MEDIUM。本轮复核 round-9 全部发现的整改。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-9 三条 HIGH 的整改声明（证伪优先，不成立标 REGRESSED）

### H1：AUTO 盲化行破坏 list 容器上下文 + 坏 info string 泄漏
整改：`_blind_auto_lines` 的盲化行**保留原行前导空白**（列 0 注释不再终止 list 容器）；
fence 保留谓词改 `re.fullmatch(r"(\`{3,}|~{3,})[^`]*", stripped)`——info string 含反引号
的行（`` ```bad` [[A]] `` ）不是 fence，**随段盲化**不保留。新门
`test_auto_blinding_preserves_list_container`（你的 list 容器反例）+
`test_auto_bad_info_string_not_fence`（你的 info string 反例）。

### H2：布尔状态机不能处理嵌套 BEGIN
整改：布尔 `in_auto` 改**深度计数**——AUTO 段内再遇 BEGIN 深度 +1、END 深度 -1、
归零才退出。你的嵌套 BEGIN 反例（outer + inner + END + [[A]]）下 [[A]] 仍在深度 ≥1
段内 → 盲 → A 报孤儿。新门 `test_nested_auto_begin_depth`。变异 M23（嵌套 +1 拆除）。

### H3：has_raw_open 绑定整个 inline token 不绑定逐 match
整改：改为**逐 match 原文裸 target 集合绑定**——`_raw_wikilink_targets_in_lines`
收集 token 原文行区间内全部**未被转义**（反斜杠奇偶判定）的裸 wikilink target；
decoded match 的 target **必须在该集合中**才采纳。你的三个反例：
- `` `[[B]]` \[\[A\]\] ``：裸集合={b}，decoded a ∉ → 拒 → A 报孤儿
- `[[B]] and \[\[A\]\]`：裸={b}，a 拒；b ∈ → 采 → B 不报 A 报
- `[[A\]\]]` / `[[A&#93;&#93;`：原文无完整裸 wikilink 含 a → 拒 → A 报
新门 `test_decoded_match_binds_to_raw_target`。变异 M25 演进史如实申报：两代锚实测
均不改变行为（escaped 拒绝由 mdit 转义处理直接承重）→ **M25 删除**归库语义（与
M16/M21/M22 同类），声明在 harness 内。

## 二、round-9 七条 MEDIUM 顺带整改

- M1：`_md_parser` ImportError → LintConfigError 已有；requirements 显式声明移交
  DEBT-1（批次约定），UAT §7 登记（r10 已核实在案）。
- M2：UAT 全文统一 round-10 终态（201 passed / 21 mutant / SHA 见 MANIFEST）；
  历史段标注时点快照；顶部「终态裁定」重写。
- M3：live sha 覆盖面收窄声明落位 §6（basename 排除任意目录 + symlink 不覆盖）。
- M4：**orphan 权威口径声明**落入 `_wikilink_targets` docstring 与 UAT：按
  **markdown-it-py 4.0.0 可渲染文本**裁判；生产图（wikilink_graph_service.Vault.connect）
  与 Obsidian 渲染口径差异为已声明边界（HTML 标签内 wikilink 在 mdit 判 html_inline
  不扫——你 r8 的 `<span>[[A]]</span>` 反例即此口径）。
- M5（新）：行模型统一——`_blind_auto_lines` 与 `_wikilink_targets` 均按 `\n` 分割
  （splitlines 的 VT/FF/NEL 行界与 mdit map 不一致）；新门
  `test_wikilink_row_model_matches_mdit`。
- M6（新）：M20/M23 同锚异门拆分为两个独立变异（M20 BEGIN 分支 / M23 嵌套深度）；
  harness 头注更新 round-8；「22 轮锚位 / 21 mutant」表述已在 UAT 顶部声明。
- M7（新）：反斜杠**奇偶**判定实现于 `_raw_wikilink_targets_in_lines`（成对反斜杠后
  是真链接）；新门 `test_double_backslash_escape_is_real_link`。fail-closed 残面
  （三连反斜杠）登记「不比什么」。

## 三、终态裁判（当前字节，MANIFEST 绑定）

referee1-pytest-full-round10.txt = **201 passed**（82 本卡 + G8-1 119 零回归）+
21/21 mutant KILLED（M25 删除后；M20/M23/M24/M25 均重锚至 round-9 后形态）+
live 第十一轮取证（round-10b：09-02 凌晨结构性 stale 窗口，rc=2，sha `a82e3af0…`
前后逐字相同）+ 禁改门空 + MANIFEST 全覆盖时序正确。

## 四、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-9 各条若整改不成立标 REGRESSED；重点对抗：盲化缩进/深度计数/裸 target 集合
绑定的**新面**（缩进 TAB 混用、深度计数与 fence 行交叠、raw 集合跨行归并）。
最后一行：`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
