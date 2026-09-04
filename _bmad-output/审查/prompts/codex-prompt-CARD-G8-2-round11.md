# CARD-G8-2 独立对抗审查（round-11 · 用户授权定向续轮第八轮）

你是独立审查者。round-1..10 存档于 codex-review-CARD-G8-2*.md；round-10 你判
0 BLOCKER + 3 HIGH + 4 MEDIUM。本轮复核 round-10 全部发现的整改。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-10 三条 HIGH 的整改声明（证伪优先，不成立标 REGRESSED）

### H1：fence 保留谓词破坏容器/围栏语义
整改双轨：
a. **谓词收严**——保留谓词从 `(\`{3,}|~{3,})[^`]*` 改为 `fullmatch(r"(\`{3,}|~{3,})[^`]*")`
   （`` ```lang\`` `` info 含反引号 → 不再保留，随段盲化，fail-closed）；
b. **anomalies 披露**——AUTO 段内出现 fence 标记行/疑似标记行 → 记入 anomaly，
   check_orphan_nodes 转 notes 显式披露 + 状态 ≥ warn（新门
   `test_auto_structure_anomaly_is_disclosed`）。
你的两个反例：`~~~lang\``（H1 tilde info 反引号）→ 随段盲化（fail-closed，A 报孤儿）；
`- ~~~text` 容器前缀（H1 list 场景）→ 盲化行保留原行前导空白（r9 H1 修复保持）→
容器不破坏。

### H2：畸形 END（`/AUTO-GENERATEDNESS`）提前归零 + fence 内 END 误关
整改：`_AUTO_END_RE` 加 lookahead 词边界 `(?=$|\s|-->|-)`——NESS 不再匹配；
fence 内的 END 注释行：round-10 后 fence 标记行**原样保留**、段内其余行盲化为
注释——fence 内的 END 行（非标记行）盲化为 `<!--x-->` 且深度照减——**如实申报
剩余面**：fence 内 END 仍减深度（你的反例 2 修复不完整），但 fence 内内容在 mdit
中本就不扫描，盲化行的 [[A]] 不会泄漏（泄漏方向已闭）；深层嵌套误关的残面登记。
新门 `test_malformed_end_does_not_close`（NESS 场景）。

### H3：裸 target 集合绑定粒度
整改（两项）：
a. **实体解码同基**——`_raw_wikilink_targets_in_lines` 的 inner 加 `html.unescape`
   （`X&#65;` 解码 = `XA` 与 mdit decoded 同基）；新门
   `test_entity_decoded_target_matches_unescaped_raw`（你的 `[[X&#65;]] \[\[X&\]\]`
   反例：XA 不再误报，X& 不豁免）。
b. **同名碰撞（code span 内 [[A]] + 转义假）如实申报为口径边界**——mdit text
   token 无字符级 srcmap，decoded content 已消费转义，位置级绑定结构性不可达；
   登记验收单「不比什么」+ 权威口径裁决点（r8 M4 升级）。

## 二、round-10 四条 MEDIUM 顺带整改

- M1：requirements 显式声明移交 DEBT-1 已在 UAT §7 登记（核对措辞与位置）。
- M2：UAT 全文统一 round-11 终态（205 passed / 22 锚位 / SHA 6b1e573d…）；
  顶部「终态裁定」重写为唯一权威入口，历史段标注时点快照。
- M3：live sha 覆盖面收窄声明核对 §6（basename 排除 + symlink）。
- M4：权威口径声明已入 `_wikilink_targets` docstring + UAT（见上）；
  `<span>[[A]]</span>` 场景 mdit 实测 children=html_inline,text,html_inline——
  text 内 [[A]] **被扫**（r10 你实测 targets=['a'] 正确）——docstring 声明的是
  「与生产图口径可能不同」而非「HTML 内一律不扫」。

## 三、终态裁判（当前字节，MANIFEST 绑定）

referee1-pytest-full-round11.txt = **205 passed**（86 本卡 + G8-1 119 零回归）+
22/22 锚位 KILLED + live 第十二轮（round-11）sha `a82e3af0…` 前后逐字相同 rc=2
（09-02 凌晨结构性 stale）+ 禁改门空 + MANIFEST 全覆盖。

## 四、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-10 各条若整改不成立标 REGRESSED；重点对抗：盲化缩进保留后的容器语义、
深度计数与 fence 行交叠、`\Q` 转换器、H3 口径边界的登记充分性。最后一行：
`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
