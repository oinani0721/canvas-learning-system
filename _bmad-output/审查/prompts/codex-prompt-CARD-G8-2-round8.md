# CARD-G8-2 独立对抗审查（round-8 · 用户授权定向续轮第五轮）

你是独立审查者。round-1..7 存档于 codex-review-CARD-G8-2*.md；round-7 你判
0 BLOCKER + 5 HIGH——全部集中在手写 Markdown 解析（AUTO/fence 互斥状态机、盲区内
反引号串扰、转义 run 粒度、fence 容器嵌套、MANIFEST 时序）。本轮复核终局整改。
工作目录 = `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、终局整改声明：**放弃全部手写 Markdown 解析，改用 markdown-it-py token 流**

你 round-7 的 5 个 HIGH 证明：在 lint 里手写 CommonMark 解析（rounds 2-7 四代实现：
正则反向引用 → maximal run 配对 → 字符偏移区间 → 互斥状态机）每轮修 N 个洞开 M 个新洞。
终局方案重演 G8-1 教训「不重新实现解析」：

- `_strip_nonsemantic` / `_strip_code_spans` / `_semantic_blind_intervals` /
  `_code_span_intervals` **全部删除**；
- `_wikilink_targets` 重写为 token 流：`_auto_segments`（项目自定义 AUTO 哨兵段先行切分，
  AUTO 段整段盲）→ 每段 `markdown_it.MarkdownIt().parse()` → 只扫 `inline` token 的
  `text` children；`code_inline` / `html_inline` / fence / code_block / html_block 全部
  不扫——**closer 等长 / 转义反引号 / maximal run / 跨段落 / 容器嵌套全部由库内正确处理**；
- markdown-it-py 4.0.0 为 venv 既有依赖（freeze 1d1dc542 内），lazy import，不新增依赖。

### 你的 round-7 反例逐条对照（mdit 4.0.0 实测 token 流）

| r7 反例 | mdit 解析 | 整改后行为 |
|---|---|---|
| AUTO/fence 交叉（r7 H1） | html_block + fence 两块 | AUTO 段整段盲 + fence 块不扫；fence 后真实 [[A]] **采纳** → A 报孤儿（互斥状态机已删除，无吞 opener 问题） |
| `<!-- \` -->` + `` \` [[A]] \` ``（r7 H2） | html_block + code_inline('[[A]]') | code_inline 不扫 → A 报孤儿 |
| `\`\`\`[[A]]\``（r7 H3） | **text('```[[A]]`')——mdit 4.0.0 判全转义普通文本** | [[A]] 是真链接 → A **不**报（与你 round-7 预期「A 在 code 内」不同——以 venv 内 mdit 4.0.0 实测为准，声明为口径差异非缺陷） |
| `> ~~~text` blockquote fence（r7 H4） | blockquote_open + fence（容器内） | fence 不扫 → A 报孤儿 |
| 4 空格缩进 `~~~`（r7 H4 反向） | code_block + paragraph | code_block 不扫；后续 [[A]] 是真文本 → 采纳 |
| `` \`x\n   \n[[A]]\` ``（r7 M1） | 两个 paragraph，第二段 text('[[A]]`') | [[A]] 真链接采纳 → A 不报 |

新门 4 个（3f 节）：span 在 wikilink 内 / 注释在括号间 / escaped backtick / 跨空行——
全部在 token 流实现下通过。

### 变异面收敛声明

M16/M21/M22 删除（closer 等长 / 转义 / 跨段落语义在库内，外部依赖不可变异），行为由
3 个集成测试锁定；可变异面收敛到 **M7**（text-token 过滤拆除）与 **M20**（AUTO 段跳过
拆除）两个本卡自有决策点。现行 harness 19 个 mutant 全杀（transcripts/ 存档）。

### MANIFEST 时序整改（r7 H5）

MANIFEST 生成移到**全部证据（含 live-window）落定之后**的最后一步；本轮 MANIFEST 时间
晚于其列出的每个文件 mtime。请独立复算 77+ 文件哈希与 comm -3。

### 其余顺带整改（r7 M2/M3、LOW）

UAT 全文统一 round-8 终态（190 passed / 19 mutant / SHA ffa51514…）；轮次史补 r6/r7；
live sha 门覆盖面收窄声明落入 §6.11；help 盲区断言精确到 raw_derived 专属句。

## 二、终态裁判（当前字节，MANIFEST 绑定）

referee1-pytest-full-round8.txt = **190 passed**（71 本卡 + G8-1 119 零回归）+
19/19 mutant KILLED + live 第八轮 sha `a82e3af0…` 前后逐字相同 rc=0 + 禁改门空。

## 三、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
重点对抗：token 流法的新面（AUTO 切分边界 / mdit 与 Obsidian 渲染差异的声明充分性 /
lazy parser 的零写声明 / text token 里 AUTO 字样的直写场景）。最后一行：
`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
