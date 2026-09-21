# 04 — CARD-G8-7 授权走查旅程日志（authorized window）

> **授权记录**：用户 2026-09-20 13:1x（PDT）在标签页回复选项「1」= 「授权：我说口令，你来起服务（推荐）」⇒ 视为当次发出「G8-7 授权走查」授权。执行分工：六环节界面操作 = 用户（Obsidian / Claudian / 浏览器）；车道 = 只读采证（shasum / 快照 / 截图登记）。
> **窗口口径**：出题板 = `CS 61B`（默认）；只答 1 题；env 全默认不动；车道零 cp / 零部署 / 零改 live vault。

## T-1 服务恢复（车道执行；非 vault 写入）

| 时刻 | 动作 | 证据 |
|---|---|---|
| 13:13 | `open -a Docker` → 守护进程就绪（server 29.3.1） | 本文件；docker info |
| 13:13 | Docker Desktop 按 restart policy 原样恢复 3 容器（未重建）：`canvas-learning-system-backend`(8011->8001)、`-neo4j`(7691->7687)、`-neo4j-test` | `docker ps` 输出见下 |
| 13:15 | 只读 GET `http://127.0.0.1:8011/api/v1/review/overview/page` → **http=200**（28967 bytes） | `/tmp/g87-overview-pre.html` |
| 13:14 | 容器来源自证（无需 compose 重建）：`com.docker.compose.project=feature-obsidian-hybrid-dev`，image=`feature-obsidian-hybrid-dev-backend` | `docker inspect` 输出 |

```
canvas-learning-system-backend	Up (healthy)	127.0.0.1:8011->8001/tcp
canvas-learning-system-neo4j	Up (healthy)	127.0.0.1:7478->7474/tcp, 127.0.0.1:7691->7687/tcp
canvas-learning-system-neo4j-test	Up (healthy)	127.0.0.1:7479->7474/tcp, 127.0.0.1:7692->7687/tcp
```

## T0 跑前快照（只读，2026-09-20 13:14:36 PDT）

- 产物：`02-live-snapshot-before-authorized.txt`（四目录 + 主仓 daily-review state；`wc -l` = **50 行** = 1 行头注 + 49 条；头部 HEAD=`d9d64ea1`）
- 口径 = 卡文 §二.4 同命令（`find 原白板 节点 检验白板 outputs -type f -not -path '*/.trash/*' -print0 | sort -z | xargs -0 shasum -a 256`）

## T1..T6 六环节（用户执行，逐条补登）

> 状态：**终版**（2026-09-20 整改轮封口，M-1）。逐环节细节见下方 T-1.x–T-3.5 各节 + `manifest.json`（assertions / execution.commands / artifacts **59 件**：35 授权窗口 + 13 整改轮裁判 + 9 截图登记 + 2 判据补跑/重建（权威 = manifest））+ `artifacts-sha-authorized-*.txt`；本表只作索引，不再逐格补登。

| # | 用户动作（pi 会话，命令原文见 T-3.x） | 产物 | sha256 | 截图 | 判据（终版） |
|---|---|---|---|---|---|
| ① | 节点批注 + `（G8-7 走查批注）` marker | `节点/csm-tutoring-unit-credit.md` | 见 artifacts-sha 台账 | 有 | **pass** |
| ② | `/board-recap CS 61B` | 回顾三件（md + manifest + scan） | `cef0ab0e…` / `30df61da…` | 无图（未留影） | **pass**（Step5.5 VERIFY PASS） |
| ③ | `search_notes("G8-7 走查批注")` | 返回原文（0 命中） | — | — | **fail**（T-3.3） |
| ④ | `/start-exam-board from CS 61B` | `检验白板/CS 61B-2026-09-20-2235.md` | `c55ec46d…` | 无图（未留影） | **Artifact pass / Context fail** |
| ⑤ | 手答 + `/quiz-answer` | 节点 `mastery_*`/`fsrs_*` + ledger `answer_scored` | 见 T-3.x | 无图（未留影） | **pass** |
| ⑥ | 车道只读 GET `/api/v1/review/overview/page` | `overview-page-*.html` / `overview-curl-*.txt` | `52adabc3…` / `43e9317c…` | 失败页 ×2 已登记（`screenshots/user-06-refresh-503-1544*.png`），成功页仍缺 | 车道侧 pass / 整段 **fail**（用户侧实见 503） |

## T-1.2 批注机制深挖 + UAT 步骤①升级（13:3x）

- 用户指令：「UAT 文档应该生成在主路径上」+ 要求深挖批注打法 ⇒ 车道已把 UAT 副本同步到主树 `feature-obsidian-hybrid-dev/_bmad-output/验收单/`（供 Obsidian 阅读），并把步骤①改写为可照抄的热键流程（`Cmd+Shift+A` → 4 标签 → 3 态理解度 → `✍️ 我的理解：` 补句）。
- 批注机制证据（只读）：live 插件 `.obsidian/plugins/canvas-learning-system/main.js`（`wrapSelection` 模板 / `TAG_OPTIONS` tips|error|question|keypoint / `UNDERSTANDING_OPTIONS` 3 态 / `%%cb-…%%` 稳定 id / POST `/api/v1/tips` 上报 / callout-sync 白名单 `节点/`、`原白板/`）+ `.obsidian/hotkeys.json`（Cmd+Shift+A / Cmd+Shift+S / Cmd+Shift+D）+ Story-1.16 验收单。
- 待办影响：①完成后产物=板文件本体（callout + frontmatter `tips` 回填），快照差集中应表现为 `原白板/CS 61B.md` 一行变化（白名单内）。

## T-1.3 口径更正：批注落点 = 节点，不是原白板（用户指正）

- 用户指正：`原白板` 是「节点集合/索引」（Karpathy index.md 形态），不该作为批注对象。
- 实测裁定（写卡级复核）：①`原白板/CS 61B.md` frontmatter `migrated_from: wiki/canvases/cs-61b/index.md`（旧 index 的直接前身）+ 板内 info callout 自述「本文档即白板本身（不是白板目录的索引）」，成员在 `节点/` 扁平池；②`board_manifest_service.py` 的 `list_node_files()` 只列 `节点/`，`tips` 只从节点 frontmatter 读（:642）⇒ 板上批注不进 board-recap 计数；③live 实测：板文件**无** `tips` 字段、两成员节点（`cs-61b-csm` / `csm-tutoring-unit-credit`）**有** `tips` 字段 ⇒ 现网工作件面就是节点。
- 处置：UAT ① 由「在板上批注」改为「在 `节点/csm-tutoring-unit-credit.md` 打批注」（备选：新建节点 md）；该口径差登记进 `03-breakpoints.md` §B（归属 G5 待裁，非阻断）。

## T-1.4 ① 首试失败：批注报「请先选中文本再批注」（2026-09-20 14:10）

- **现象**：用户在 `节点/csm-tutoring-unit-credit.md` 中选中文本后按 `Cmd+Shift+A`，插件 Notice 报「请先选中文本再批注」；截图 `截屏2026-09-20 下午2.10.18.png`（用户提供）。
- **源码定位**（live 插件 `main.js`，handler `handleAnnotateCallout`）：第一道 `if (!editor) → "编辑器未激活"`（未触发）⇒ 第二道 `editor.getSelection()` 空 ⇒ 报出该 Notice。即：**编辑器存在但读到空选区**。
- **候选因（待定）**：① 笔记处于**阅读视图**（渲染层 DOM 选区不进 CM6 编辑器）——插件代码 **0 处**视图模式判断（`getMode()` / `getActiveViewOfType` 引用数 = 0），阅读视图下必然走这条静默失败路径；② 选区不在正文编辑器（右侧 Claudian 面板 / 属性区 / 渲染块）。
- **候选缺陷**：**阅读视图下批注静默失败 + 报错文案误导（"请先选中"）** → 归属 **G5（插件/skills 面）**；本卡只登记不修（走查窗口冻结）。
- **处置**：用户改走「切编辑模式（Cmd+E）→ 正文拖选」或 `Cmd+Shift+S`（插入空白 question callout，同为批注体系 tag=question）；两条均满足 ① 判据。

## T-1.4 更正（GLM-5.3 独立检查，2026-09-20 14:2x）

- **车道原表述被证伪**：T-1.4 把「阅读视图」列为首要候选属**无效推断**（"插件 0 处 mode 判断" ≠ 当时是阅读视图）。
- **GLM-5.3 反证**（报告：`glm53-check-annotation-20260920T141358.md`）：近事故 `workspace.json:497-504` 该 leaf state = `{mode:"source", source:false}` = **live preview**（Obsidian 1.12.7 状态栏代码把 `source:false`→live-preview）；用户亦明确否认阅读视图。**阅读视图只能算"该 Notice 的一种机制"，不是本案事实根因。**
- **GLM 的根因排序**：①（高）选区位于正文 CM6 读不到的区域（属性区/标题/渲染 callout/widget）——插件注册的是 **generic `callback`**（`main.js:1563-1567`）因而绕过 Obsidian 对 properties/title 的 editor-command gating；该笔记有 22 条属性 + 渲染 callout；②（中低）`activeEditor` 指向的编辑器≠实际选区所在；③（低）热键链路/其他插件清选区（静态扫描无竞争 Mod+Shift+A）；④ Obsidian 1.12.7 API 变更——**基本排除**（bundle 仍实现 `activeEditor`，且 editor 非 null）。
- **判别实验**（已附报告 §C）：30 秒 = 在 `## 核心概念` 普通正文选一段 → `Cmd+Shift+A` → 预期弹 TagTypeModal（Esc 即零写入）；2 分钟 = DevTools 只读 snippet（同时打印 CM6 selection / DOM selection / `.metadata-container`/`.callout` 归属）。
- **修复形状**（登记，不实施）：保持 `activeEditor`；失败分支按 DOM 选区来源分型给诚实文案；可选改 `editorCallback`（有代价）；⛔ 不得把 DOM Selection 直接当写入 fallback（modal 后续走 `replaceSelection`，`main.js:3416`）。

## T-1.5 用户第二次定位：选区落点 = 渲染态「问题块」（question callout）内部

- 用户指正原话：「他这个是问题块，但是他没有渲染出来，你们的原因都没有找对」。
- 车道复核（只读）：①源码 `节点/csm-tutoring-unit-credit.md:71-74` = 形态完好的 `> [!question]+ 待剖析 · 源自 [[检验白板/CS 61B-2026-08-11-1349]]（2026-08-11）`（插件 parser 已把它收进 frontmatter `tips`，`source: callout_parse`，`:38-46`）；②用户截图放大（`/tmp/g87-crop-callout.png`）：Obsidian **确实渲染**该块——❓圆图标 + 标题 + 右侧折叠 chevron + 缩进正文 + 链接药丸；③⇒「没渲染」若指"块没渲染成 callout"不成立；若指**拖选时选区高亮不出现**，与"渲染态 callout 是块级 widget、其内部文字拖选不产生 CM6 选区"一致（GLM 报告 §B.1 候选① callout 子类机制同向）。
- **修正后的根因**：① 批注失败 = **选区落点在"渲染态 callout（问题块）"内部**——Live Preview 把 callout 渲染为块级 widget，其内部文字拖选不进 CM6 ⇒ `editor.getSelection()` 读空 ⇒ 报「请先选中文本再批注」。此前「阅读视图」「属性区/标题」均非本案落点。
- 处置：批注请选**普通正文**；若要批注 callout 内文字 → 先点进块内使其退回源码态再拖选（或 `Cmd+Shift+S` 另写疑问块）。
- 缺陷登记（G5 插件面）：渲染态块级 widget（callout）内选区 → 静默失败 + 文案误导（无分型诊断）。

## T-1.6 GLM-5.3 复核「callout 之前正常渲染、现在不正常」（报告：`glm53-render-check-20260920T144631.md`）

- **裁决：不是渲染故障**——两块截图里的块都是**渲染态 callout**（❓图标 + 标题 + 折叠 chevron + 缩进正文）。观感"没有盒"的直接根因 = **Obsidian 1.12.7 默认 `--callout-border-width: 0px` + Underwater 1.6.61 的 question=pink/love 低对比配色**（10% 淡底叠在奶油白 `#faf4ed` 上 ≈ `#f3e6e2`；正文 `#575279` 紫/靛；标题/图标 `rgb(180,99,122)`）——截图转录逐项对上。
- 粉色药丸 = Underwater 对 **resolved** internal-link 的样式（`theme.css:1098-1110`），不是 unresolved；`</>` 图标 = **Live Preview 渲染块 hover 时的 edit-block affordance**（`app.css:3809-3820 / 11052-11070`），14:10 有它 = 当时确为 Live Preview 渲染 widget。
- 模式变化（14:12 live-preview → 现在 `mode:"preview"` 阅读视图）**只解释 `</>` 的出现/消失**，不解释"盒感"差异。
- "之前正常"最强候选（**未证实**）：`appearance.json` mtime = **2026-09-20 12:59:21**（今天）被重写——可能是主题/外观切换（如默认主题→Underwater）或浅/深色变化；无历史可比（.obsidian 未进 git），不能写实。
- 已排除（对当前视觉）：笔记语法坏 / 链接 unresolved / app 升级（1.12.7 自 2026-03 未变）/ 主题文件版本升级（2026-04-18）/ 插件 CSS（静态扫描 0 命中）/ 当前阅读视图本身 / 焦点退化（机制存在但截图非该现象）。
- 修复建议（未实施）：① CSS snippet（`question-callout-box.css`：给 question callout 补 1px 边框 + 18% 底色）；或 ② 外观切回 Default 主题；⛔ 不要改 callout 语法（`main.js:51-53` parser 只认 `[!type]` + `+/-`）。

## T-1.7 根因定案：Obsidian 已实际运行 1.13.7 更新包 × Underwater 1.6.61（4 月版）三元组失效

- **决定性证据（Obsidian 自身日志 `~/Library/Application Support/obsidian/obsidian.log`）**：`Loaded updated app package …/obsidian-1.13.7.asar` 自 **2026-08-22 07:19** 起每次启动都加载（今天 12:59 PDT / 14:42 PDT 两次；包 mtime 2026-08-12，sha256 `a52a7daf…`）。⇒ 用户实际跑的是 **1.13.7**，而 `CFBundleShortVersionString` 仍是 1.12.7（自动更新以 app-support 里的 asar 覆盖运行）——车道与 GLM 此前两次按 plist/旧 asar 判断版本，**均属误判，特此更正**。
- **破坏性变更（包内实测）**：1.13.7 asar 中 `rgba(var(--callout-color)` / `rgb(var(--callout-color))` 出现次数 **0/0**（1.12.7 包里 3/5）；背景改 `color-mix(in oklch, var(--callout-color) 10%, transparent)` ⇒ `--callout-color` **必须为完整 CSS 颜色**（社区同证：AnuPpuccin #384 / ITS #430 / callout-manager #54 / Reddit PSA）。
- **本机主题版本**：Underwater **1.6.61（2026-04-18）**，`theme.css:1193-1195` 仍是 `--callout-color: var(--color-pink-rgb)`（RGB 三元组）⇒ 在 1.13 下声明无效 ⇒ callout 底色/边框/图标色静默失效。**像素实测**：块内左内边距 `(254,250,244)` 与页面底色**逐通道相等（差 0）**⇒ 底色确实未绘制。
- **「之前正常」的时间线**：8/22 之前实际运行 1.12.7（三元组有效）；上游主题 **7/31 提交「Fixed callout colors」**（改为 `--callout-color: var(--color-pink)`）+ **9/3「Compatibility Obsidian 1.13」**——作者已修，本机从未更新。
- **修复选项**：① CSS snippet 五条（bookmark/time/person/media/question 用 `rgb(var(--color-*-rgb))` 包裹）；② 用上游 main 的 theme.css 替换本机（差 N 行，待裁）；③ 等作者发新 release（当前 release 1.6.62=5/25，**不含** 7/31 修复）。⛔ 已排除：前台 app/主题文件/插件 CSS/文档语法/链接失效——本案是 **Obsidian 更新包 × 主题旧版** 的组合缺陷。

## T-1.8 用户授权修复：更新 Underwater 主题（方案①，2026-09-20 15:06）

- **用户指令**：「更新主题（推荐）」⇒ 车道执行（`set -e` 全程）：
  1. 备份：`theme.css.bak-20260920-150650`（123108B）/ `manifest.json.bak-20260920-150650`（231B）；
  2. 拉上游 `Seniblue/Underwater@main`（含 7/31「Fixed callout colors」+ 9/3「Compatibility Obsidian 1.13」）→ 替换 `theme.css`（新 sha256 `ea792fce…`，121695B）；
  3. `manifest.json` 合并保版本 → **1.6.62**（sha `0f2bdfba…`）。
- **验证**：5 处 `--callout-color` 已从三元组改为完整色（`var(--color-pink/purple/cyan/yellow)`）；另 6 处 `--canvas-color-*` 也补了 `rgb()` 包裹（同为 1.13 兼容面）；与旧版差异 99 行（其余为 padding/margin 简写清理）。
- **边界登记**：本次写入位置 = live vault `.obsidian/themes/**`，**不在六环节声明写入面**（原白板/节点/检验白板/outputs），也不在零静默改写快照面（四目录+state）；为用户当次指令下的环境修复，如实登记备查。
- 回滚方法（如需）：`cp theme.css.bak-20260920-150650 theme.css && cp manifest.json.bak-20260920-150650 manifest.json`。

## T-2.1 pi 实机轮（用户自跑）+ 联合验收（DeepSeek＋GLM-5.3）

- 用户 14:04 PDT 在 pi（cwd=canvas-vault，`opencode-go/deepseek-v4.1-flash`，thinking=off）实跑走查：②④⑤ **产物级全通**（② VERIFY PASS；④ 出板 `检验白板/CS 61B-2026-09-20-2235.md` + `exam_created`；⑤ mastery 0.01→0.02 + fsrs_* 六件 + calibration + 归纳疑问块 + `## Concepts` 同步 + `answer_scored`）；①的批注已落（含 %%cb-muad37hsmsm6%%）但**缺 UAT 约定的 marker**；③ 因 marker 缺失 0 命中；⑥ 未跑。
- **联合裁决（GLM 独立复算 + 车道复核一致）**：
  - **BLOCKER-current ×2**：I-1 ③ marker 未写入（全 vault 0 命中；对照探针证明索引可返节点）；I-2 ④ HARD-ISO 上下文前提被同会话 ③ 诊断 `cat` 节点正文污染（产物无定义泄漏 ⇒ Artifact PASS / Context FAIL，两档拆记）。
  - **HIGH ×2**：I-3 `decay_beta.update_after_idle` 在低证据+久闲置下**答错（grade=0）μ 反升**（GLM 独立复算：f=0.666536、a 被 FLOOR 抬 0.05、b→3.219565，μ 0.013333→0.015293，与落盘 3.2196/0.02 完全一致；`effective()` 无 FLOOR，缺陷由 `update()` 逐坐标 FLOOR 引入）；I-4 零静默改写门**漏扫 vault 根 `learning_events.jsonl`**（false-negative 覆盖缺口，非 outside≠0——快照面本就不含它）。
  - **MEDIUM**：I-5 插件 `FrontmatterTipsSync` 为已知第二写者（重序列化 `ts` 去引号 / `grade_norm: 0` / `self_confidence_norm:` 空；归因代码路径 + 第三条 `source: callout_parse` tips 为决定证据）；I-6 UAT ③ 期望路径笔误（写 `原白板/CS 61B.md`，应为 `节点/csm-tutoring-unit-credit.md`）；I-7 pi MCP 工具名差异（canonical `mcp__canvas-learning-mcp__*` 33 处 vs pi 实际 `canvas-learning-mcp_search_notes`/`mcp()` 代理）；I-8 pi agent 宽 grep 卡顿（体验）；I-9 长窗口快照内另有 9 改 2 增（含 今日复习/mindmaps/state，写者未证实）；I-10 ⑤ 判据只看 2 位小数；I-13 UAT 证据表待填。
  - **LOW**：I-11 Step 4.5 `degraded:true/node_not_found` 属正常降级；I-12 `self_confidence_raw: "null"` 字符串化。
- 产物 sha（车道实测）：节点 `a539c015…`（4719B/15:39:01）、检验白板 `c55ec46d…`（1810B）、回顾 `cef0ab0e…`（6818B）、ledger `214e43a1…`（25 行/8179B）。

## T-2.2 总览页 503（test-vault）联合审核（DeepSeek 读图 + GLM-5.3 读码复算）

- 用户截图：`/review/overview/refresh` → 「刷新失败 · test-vault」HTTP 503 · pick_failed；GLM 通道**读不了图**（自证回执）；车道转写逐项对上错误页实现（`review_overview.py:3027-3051`）。
- **根因（GLM 只读复算）**：`test-vault` 是 **CARD-C2 演示 fixture**（`test-vault/outputs/今日复习.json:2` 自述"测试数据…删除无副作用"；历史卡 `2026-08-25-第二批小goal卡` :130）——只有 `.obsidian/` + fixture JSON；缺 `.claude/scripts/decay_beta.py` ⇒ `load_decay()`（`daily_review_pick.py:1262-1268`）import 失败 ⇒ 503（**设计内 fail-closed**，`:2172-2183` 映射，回归测试锁 `test_review_overview.py:1635-1650`）。
- **「到期 2/新卡 2/待剖析 1」来源**：该库**自己的 fixture 快照**（非跨库串读/state 复用）：`stats.due_nodes=2`；两条 `due_reason="new"`（≠`stats.new=1` 口径）；`ineligible.placeholder=["演示积压节点"]`。live GET 复核 entry：`status=stale / date=2026-08-25 / recommended_board=演示白板 / bucket_counts=null`。
- **真产品缺口（MEDIUM，建议开卡 P5/G6-8 面）**：库枚举只看"非隐藏目录 + `.obsidian/`"（`:785-794`）＋ 四态卡片**无条件**渲染刷新按钮（`:1726-1731`）⇒ 摆出**必然失败**的入口；测试只锁"失败给人话"未锁"别给死入口"。
- **动作建议**：先**排除/归档 test-vault**（不要在 fixture 上"补两个文件"当真库用）；要真库 → 新建并走 `deploy-vault.sh`（`install-vault.sh:71-89` 铺骨架 + `.claude/scripts`，`:189` 自检 decay+fsrs）。
- 「投影完全建立」三层清单已由 GLM 列全（refresh 硬前置 6 项 / 五桶有意义数据 8 项 / 正规部署系统件）；报告：`glm53-503-review-20260920T161652.md`。

## T-3.1 授权窗口收口采证：after 快照 + 零静默改写门 + ⑥ 车道侧 GET（2026-09-20 18:0x）

- **after 快照**：`04-live-snapshot-after-authorized.txt`（51 行；同 before 口径）。
- **零静默改写门（空格安全路径提取，修正卡文 `awk $3` 截断坑）**：`changed=11`，白名单外 **`outside=2`**：
  | # | 路径 | mtime | 归类 |
  |---|---|---|---|
  | 1 | `outputs/思维导图-CS 61B.excalidraw.md` | 14:05:52 | **集外（待归因）**：自述"一次性导出快照 · v3 · 系统不会回头读它" |
  | 2 | `outputs/思维导图-特征值与特征向量.excalidraw.md` | 14:05:52 | 同上（两文件同秒写入 ⇒ 批量导出） |
  其余 9 项全部 ⊆ 声明写入面：回顾三件 / 今日复习两件 / state / `原白板/CS 61B.md`（Concepts 同步+批注）/ `检验白板/CS 61B-2026-09-20-2235.md` / `节点/csm-tutoring-unit-credit.md`。
- **写者排查（未闭合）**：live 插件 main.js 无"思维导图/excalidraw/\\u 转义"命中；`.claude/skills/**`、`.claude/scripts/**`、repo `scripts/`+`backend/app`、claudian 插件均 0 命中；"一次性导出 · v3"文本全盘 grep 未命中 ⇒ **疑似窗口内由用户本人/另一会话按一次性脚本导出**（待用户确认后按"已知写者"归因，否则按卡文口径属阻断级登记候选）。
- **ledger（假阴性覆盖缺口，已登记）**：`learning_events.jsonl` 25 行，窗口内 +3（callout_ingested / exam_created / answer_scored）——均为声明写入面内，但**不在快照面**。
- **⑥ 车道侧**：只读 GET `http://127.0.0.1:8011/api/v1/review/overview/page` → `overview-curl-*.txt` + `overview-page-*.html`（http 码与 sha 在案）；用户侧截图 **2026-09-20 19:09 已补登记（T-3.6）**，内容为 503 失败页；成功页与体验段仍待补。

## T-3.2 思维导图写者归因（收窄排查完成）

- 写者 = **自研「思维导图-Excalidraw 生成器」（v3，"一次性导出"语义）**，设计与迭代记录在案：`_bmad-output/研究/2026-08-15-思维导图-Excalidraw-需求与迭代记录.md`（该轮 "dataviewjs / ExcaliBrain / 自研 Excalidraw 生成 | DONE"）。
- 窗口内 14:05:52 两个文件同秒写入 = 该生成器的批量一次导出；**非本卡六环节 skill 的写入面，也非"未知静默写者"**。
- 归类维持：**集外变化 ×2（已知写者：自研导出器；触发者待用户一句确认）**；不因此放宽白名单（卡文 (e) 口径）。
- 产物 sha 台账（本窗口）：`artifacts-sha-authorized-<ts>.txt`（含 ②④⑤ 产物、ledger、两个 mindmap、pi 会话、5 份 GLM 报告、4 路调研 findings）。

## T-3.3 ③ 重跑（用户在 pi 执行，16:0x-16:08）→ 0 命中，根因重新定位（**撤回** T-2.1 的"marker 缺失"判断）

- **原始返回（逐字，pi 会话 L110-115）**：`search_notes("G8-7 走查批注")` → `results: [] / total_count: 0 / source_status: ok_empty / degraded_reason: all_filtered_below_threshold / top_score: 0.0`——**marker 已于 16:07:06 补进节点**（frontmatter `:50` + 正文 `:95`）后仍为 0。
- **排除项（附证据）**：① marker 未落盘 → 否（两处命中）；② 索引滞后 → 否（探针 `我的理解` top1=该节点，返回 chunk 正文**逐字含 marker**）；③ MCP/后端故障 → 否（同会话 `scheduler.csmentors.org` → ok_nonempty / 该节点 top1）；④ `max_results` 太小 → 否（=10 仍 0）。
- **机制（pi agent 五轮有界探针，L116-127）**：fast 路径 = **dense 先滤 → FTS 只做候选确认**，**不是召回并集**：
  | 探针 | count | fts | top1 |
  |---|---|---|---|
  | `G8-7 走查批注` / `走查批注` / `走查` / `G8-7` | 0 | 0 | — |
  | `批注` | 1 | 0 | 不含该词的 `节点/代理决策分析-0303().md` |
  | `代理`（常见词） | 6 | **6** | CJK FTS 本身正常 |
  | `scheduler.csmentors.org` | 2 | 2 | **该节点 (0.877)** |
  | `走查批注 + ASCII 锚点` | 5 | 2 | **该节点 (0.839, fts=true)** |
  ⇒ dense 候选被阈值全滤时 FTS 无机会出手；只要同 chunk 存在语义锚点，该节点立即回 top1 并被 FTS 确认。`fusion_strategy` 在 fast 路径被忽略（仅 extended 生效）。
- **判定**：③ **判据设计缺陷（假阴性）**（"唯一标记串"探针在当前 fast 路径结构性必挂）＋ **一条真缺陷登记**：默认 fast 路径无关键词/稀有串/UUID 标记的召回通道（G4-RAG 面）；另 ③ 期望落点写 `原白板/CS 61B.md` 与 ① 口径（节点）不一致，建议一并改。
- ③ 状态：**不通过（如实记录）**；本轮用户侧零换词重试遮掩，车道零文件写入。

## T-3.4 manifest 填实 + 校验器绿（2026-09-20 18:1x）

- `manifest.json` 更新：`provenance.mode=live`（按 S10 不列推定字段）；`execution` 补 6 条授权窗口命令；六断言按实测填 **①pass ②pass ③fail ④fail(artifact pass/context fail 两档拆) ⑤pass ⑥fail(车道侧 pass, 用户截图待补)**；`evidence_level=E2`；`signoff=pending`；artifacts 19→**31**（新增授权窗口证据 12 件，并重算全部 sha）；`known_limitations` 4→8 条。
- **校验器（核心裁判）**：`b15-g8-7/journeys/J06/manifest.json`（live 版对照件）→ **rc=0 PASS**（`manifest-green-authorized-*.txt`）；根件仍按卡文缺陷恒红于 `journey_id` 结构层（在案）。
- **三条 schema 语义门实测教训（值得记入批次知识）**：① `assertions[].result` 枚举只有 pass/fail/not_run（无 partial，两档拆分写 note）；② `mode=live` 时 `candidate.dirty` 必须 false（实录须跑在干净树上 ⇒ 与"单卡独立 commit 后树净"时序对齐）；③ `unproven_fields` 为 schema 必填但 live 下必须为空数组（"确有推定则应为 reconstructed"）。
- 待办不变：③ 判据若按"带锚点"修订后重跑可改判；⑥ 用户截图；思维导图触发确认；用户签字后填 signoff → 最终 commit → GLM -r4 / JEV。

## T-3.5 承重裁判四件（授权窗口终版重跑，2026-09-20 18:3x）

| # | 裁判 | 结果 | 存档 |
|---|---|---|---|
| 1 | manifest 先红（J06 结构内副本 result→pass） | rc=1，**红在 S3**：`result=pass 与断言实况矛盾 — 非 pass 断言: G8-7-3, G8-7-4, G8-7-6` | `manifest-red-authorized-*.txt` |
| 2 | 负控②（signoff=approved 无 user/at） | rc=1，红在 signoff 必填（`'user'/'at' is a required property`） | `negctl2-authorized-*.txt` |
| 3 | 负控①（篡改 before 副本 1 行 = `原白板/CS.md`） | 红在**指定文件**：`hits=1`、`mutated_lines=1`、`changed_total=12`、`orig_same=1`；⚠️ 首跑踩「同值 no-op」坑（第 64 位本为 f）已按取反值重打 | `negctl1-authorized-*.txt` |
| 4 | skill dev↔live 双列（第三跑） | **DIFF=8**（与前两跑一致）；`fsrs_bridge.py`/`decay_beta.py` 两侧逐字节同（a766fbcc… / 3bf4ed94…） | `skill-versions-<ts>.txt` |

## T-3.6 截图登记入包（2026-09-20 19:09，整改轮后补）

- **背景**：r6 收口后核查发现证据包内**零截图文件**（`find $EV -name '*.png'` = 0），而卡文 (c)⑥ / (o) 要求「截图 `shot-<n>-<ts>.png` 由用户/主 session 存入 `$EV`，车道只 shasum 登记」⇒ 按 AND 条件补登记。
- **用户侧 4 件**（原件来源见括号；车道只读复制，不改原件）：
  | 登记名 | 原件出处 | 内容 |
  |---|---|---|
  | `screenshots/user-01-annotate-context-144003.png` | 桌面 `截屏2026-09-20 下午2.40.03.png` | 节点 `csm-tutoring-unit-credit` + 「berkeley-cs-support-resources 未创建」悬浮提示 |
  | `screenshots/user-01-callout-rendered-144005.png` | 桌面 `…下午2.40.05.png` | 渲染态 question callout（① 用户尝试拖选处） |
  | `screenshots/user-06-refresh-503-154428.png` | 桌面 `…下午3.44.28.png` | `/overview/refresh` → 刷新失败·test-vault / 503 / pick_failed |
  | `screenshots/user-06-refresh-503-154449.png` | `feature-obsidian-hybrid-dev` worktree（主干树）的 `_bmad-output/截屏2026-09-20 下午3.44.49.png`（= 该树 UAT §1⑥ 内嵌引用件） | 同上，21 秒后第二次留影 |
- **车道侧 4 件**（源 `/tmp/g87-*.png`，其中 `g87-annotate-issue.png`(14:13) 是 14:10:18 原件的存活衍生件——**原件已不在盘上**，journey L53 引用的 `截屏2026-09-20 下午2.10.18.png` 经全盘 find 未找到）：`lane-01-annotate-issue-1413.png` / `lane-01-selection-read-empty-crop-1442.png` / `lane-render-compare-crop-1444.png` / `lane-06-503-testvault-1613.png`。
- **台账**：`artifacts-sha-screenshots-20260920T190917.txt`（8 件 sha256 + 来源注记）；manifest artifacts 48 → **57**。
- **口径修正**：UAT §2 截图列此前对 ②/④/⑤ 写「用户侧有」，实测**无对应文件** ⇒ 改「无图（未留影）」（诚实登记，不装齐）。⑥ 判据维持 fail（用户侧实见 503 失败页；成功页截图仍缺）。
- **隐私口径**：用户侧截图含用户 Obsidian/浏览器画面（原样收录、未脱敏；仅本地仓库、本卡不 push；G1-8 若要对外引用须自行脱敏）。

## T-3.7 判据覆盖缺口补跑/重建（2026-09-20 19:37）

- **背景**：r8 收口后按卡文 §一/§二逐条自审，发现两条判据此前**未落档**：(m) 的 fsrs_bridge/decay_beta 出现面 grep、§二.1 第 0 分钟判据集。
- **(m) 补跑** `fsrs-decay-scope-20260920T193722.txt`：形态判据红（超范围命中逐条分类 = 缺陷登记/索引说明 03/04/05 共 7 行、第三方报告 glm53-*/digest 共 15 行、允许面 00/01 共 5 行，**无一为写入命令**）；**意图判据绿**（`cp|mv|install` 形态 0 命中、`tee|cat|shutil.copy` 形态 0 命中）；支撑 = 两文件 dev==live 2/2 SAME、本卡全 diff 触碰 0 行、live 现值 a766fbcc…/3bf4ed94… 在案。首版 intent-grep 自匹配（含自身+Markdown 引用块）已作废重跑，更正记录在档内。
- **§二.1 重建** `minute0-reconstruct-20260920T193730.txt`：HEAD=9d4f7bf0（源 = 当时落档的 `00-prefix-red-*.txt:2` 头部）、分支 card/p3-deploy（现复核）、BASE `grep -vc '^#'` = 33 / sha256 `726e998a…42cb4`（⚠️ 首跑引号转义败录，errata 见档内 v2 节；现复核值已实证）、pyright 不适用（卡文 (h)）、board-recap/quiz-answer/start-exam-board 三条 sed 现复核符预期、docker ps 以 T-1 段为等价证据；**当时 status 与 §〇 sed 深核两条未落档**（如实登记，不冒充当场存档）。
- **口径**：两条均登记为「判据覆盖缺口」（非产物缺陷、非判定翻面）；manifest artifacts 57 → **59**。

## T-3.8 r9 发现处置 + 卡文 (g)② 三件齐登记（2026-09-20 19:5x）

- **r9（绑 49247d54）= B0/H1/M1/L3**，全部指向本轮两份新存档的内部准确性，逐条处置：**H1** = minute0 第 4 条首跑败录被当成「可重建」⇒ 档内追加 ERRATA v2（现复核 33 / sha256 726e998a…，原文不改写），下游「sha256 在案」表述由 errata 兜底；**M1** = fsrs 档 B(2) 意图段登记后出现自引用命中（manifest description 文本）⇒ 档内补注复现口径（须排除 description 行），实质不变；**L1** = 03/04/05 计数 6→7 时点差已在档内注明；**L2** = 「允许面 5 行」含 01:37 结论段的宽贷已在档内注明；**L3** = 伴随件 `_bmad-output/审查/evidence-g87/jev-triage-1464de1f.json`（0 代码文件）已记入 UAT §6 台账。
- **卡文 (g)② 三件齐登记（自查新增，交主 session 裁定）**：(g)② 要求六环节各自「产物存在 + sha + 截图」三件齐，缺一记 partial 不记 pass。现网事实：① 有截图（用户 2 + 车道 2）；③ 无（本就 fail）；④ 无（本就 fail）；**⑥ 有失败页截图**（成功页缺）；**②⑤ 无截图** ⇒ 按 (g)② 该两环节**环境级应为 partial**。本件处置：manifest `assertions[G8-7-2/5]` 的 statement（回顾三件 / mastery·FSRS 更新+落账）**均成立故保持 pass**；**环境级评分改记于 UAT 4-C 为 🔶 partial（缺截图）**，并写入 `known_limitations`；**是否将 assertions 收紧为 fail(partial) 由主 session 裁定**（schema 无 partial 枚举，二值化会丢信息）。
