# Obsidian 原生块引用 / 标题引用 + Obsidian CLI —— 对 CLS「原白板 ↔ 节点 ↔ 批注」关系梳理的收益评估

> 日期：2026-09-11 起调研，2026-09-12 成文 · 工作树 feature-obsidian-hybrid-dev · 主 session 实测 + 5 镜头并行调研（152 条发现，一手 URL / file:line）+ 12 条核心主张 × 3 路对抗核验
> 触发：用户 2026-09-11 提问「Obsidian 原生支持 `![[#^]]` 引用块、不同 `##` 下的文本，也提供 CLI；原生就能看到各文本的双向链接联系——这对 CLS 梳理原白板下节点、批注之间的联系是不是原生就很有帮助？请深度调研，可安装 CLI，有明显收益就列入分 goal」
> 状态：§0 / §8 / §9 由核验综合填写；§1–§7 为事实底账（每条都能回到 file:line 或一手 URL）；§11 = 2026-09-13 CLI 只读探针实测（用户裁定：D-A 维持延后，D-E 执行）
> ⚠️ 环境事实：本 session Context7 与 graphiti-canvas MCP 均连接失败；Context7 的角色由 obsidian.md/help 与 docs.obsidian.md 一手抓取替代，Graphiti 的角色由本地 memory + `_bmad-output/研究` 历史决策替代。

---

## 0. 一句话裁决

两件事分开裁，结论相同：**收益不明显**。

| 对象 | 裁决 | 一句话依据（只用 §8 幸存主张） |
|---|---|---|
| **Obsidian CLI 通道** | 收益不明显 | 两条收益主张（C1「让 harness/后端读到原生图」、C4「补活架构规划的 CLI 层」）各被 2/3 反驳：CLI 的 `backlinks/links/orphans/deadends/outline` 只暴露**文件级**图，而这份图 harness 今天已经通过插件 `resolvedLinks` 邻居注入、MCP `get_neighbors`、对 30 个 md 的毫秒级 grep 拿到；标题/块级双向边 CLI 没有命令暴露；容器化后端与 launchd 链根本调不到它（C5）；退出码恒 0（C6）与 vault 定位静默回落（C12）是真实风险 |
| **批注埋原生 `^cb-xxx` 块 id** | 收益不明显，**维持 2026-06-13「延后」** | 收益主张 C2 被 3/3 推翻；幸存的 C3 说明节点↔批注联系已被 frontmatter `tips[]` / Graphiti 自环边 / callout 内嵌原文三形态覆盖，净增量只剩「整条 callout 可被 `[[节点/X#^cb]]` 跳到 / 嵌入 / `[[^^` 搜到 / `obsidian://` 深链」，且官方明言不能链到 callout 内部；C8 证明可见成本真实（Live Preview 每条批注多一行 `^cb-…`、两处光标算术、列表内批注不可寻址）；C10 证明阶段 2 触发条件未满足（DD-10 蔓延）；C11 证明学术侧只支持「导航 / 核验」不支持「提升理解」 |

**你的直觉里对的部分**：Obsidian 内部确实有块级双向链接的全部原料（`getFileCache().links` + `parseLinktext`），而且项目的 `cb-<base36>` id 天生就是合法块 id、插件解析器对多一行 `^cb-xxx` 零影响（§5 实验 2）。**不对的部分**：这些原料没有任何现成 UI / 插件 / CLI 命令把它展示成「块级双向联系」，vault 里今天一条块级链接都没有，而 CLS 已经用另外三种形态把「批注属于哪个节点、锚在哪段原文」记全了。

**调研顺带抓到的三个真问题**（与提问无关，但建议排卡，见 §9）：① 后端 `obsidiantools` 自建图在 `newLinkFormat=absolute` 下把同一笔记拆成两个键，出边与度数丢一半（C7 事实三票一致）；② `react_agent` 的三个 CLI 工具是 macOS 恒死的遗留管道，却被系统提示词标为「优先使用的主搜索工具」，每次解释 / 评分先空跑一轮再回落；③ `wikilink_context_service` 的批注 kind 集缺 `tips`/`keypoint`，插件写的批注在这条摘录通道里被静默丢弃（既有漂移）。

---

## 1. 用户问题与初衷锚点

**用户想要的**：在 Obsidian 里原生看到「各文本」（原白板段落 / 节点 / 批注）之间的双向联系，让 CLS 梳理关系时少造轮子。

**本项目已有的相关决策（DD-08 初衷检索，全部一手）**：

| 时间 | 文档 | 与今天问题的关系 |
|---|---|---|
| 2026-06-13 | `研究/2026-06-13-同步契约-务实方案-待ChatGPT审查.md` §3 表 + §4 | 把「callout 埋原生稳定 block-id `^cb-xxx`」（方案 E 的一部分）判为**延后**：「累积用户极少编辑，改内容保留身份收益小；content-hash uuid 已够」。**阶段 2 触发条件**写死为「实测出题需要完整演化史，或用户开始频繁改删」 |
| 2026-06-26 | A+-prime 落地（`frontend/obsidian-plugin/src/callout.ts:57-70`） | 用 Obsidian **注释语法** `%%cb-<base36>%%` 作批注稳定身份——不是原生块 id，原生 `[[#^]]` 链不到它 |
| 2026-07-20 | `研究/2026-07-20-V2未实现功能全景盘点-代码实况裁决版.md:170` | FR-RET-13「块级可点击双向链接（文件/章节/块级）」判「🗑 架构降级后已无意义：被 Obsidian 原生 wikilink 跳转取代」。FR 原文（`planning-artifacts/prd-v0-original-tauri.md:819`）要求「**零侵入，不修改用户笔记**；章节级精度为默认推荐」 |
| 架构 | `planning-artifacts/architecture.md:35` | 六路物理通道之二 = **「CLI 层（Obsidian CLI 图遍历 + Vault 笔记搜索）2 通道」**——用户今天的提议里「CLI 部分」是项目早已规划、但在 macOS 上从未接通的通道 |
| MVP | `_decisions/mvp-plan.md` #10 | 「笔记精准检索返回」按**标题级**精度定义；14 项里没有「块引用」或「CLI」条目 |
| Skills | `chat-with-context/SKILL.md:117-121`、`study-question/SKILL.md:83` | AI 回答里的引用**必须** `[[file#heading]]` 或 `[[file#^block]]`，禁止 `[[file]]` 全文级——这是对 AI 输出的规则，不是 vault 存量 |

---

## 2. 本机与线上 vault 实况（主 session 2026-09-11 实测）

### 2.1 Obsidian 与 CLI

| 项 | 实测 |
|---|---|
| Obsidian 安装器版本 | **1.12.7**（`Info.plist`）；App 核心已自动升到 **1.13.7**（`~/Library/Application Support/obsidian/obsidian-1.13.7.asar`）；官方最新 1.14.1（2026-09-08） |
| 运行方式 | 一直从挂载的 DMG `/Volumes/Obsidian 1.12.7-universal/Obsidian.app` 经 **AppTranslocation** 临时路径运行（`ps` 实测 pid 79171 路径含 `/T/AppTranslocation/…/d/Obsidian.app`），`/Applications/Obsidian.app` 原本不存在 |
| CLI 二进制 | 随 1.12.7 安装器捆绑：`<App>/Contents/MacOS/obsidian-cli`（135824 B，universal） |
| CLI 通信 | 二进制 → Unix socket `~/.obsidian-cli.sock`（`strings` 实测）；运行中的 App **已在监听**该 socket（`lsof` fd 21u） |
| CLI 开关 | **未开**：直接调二进制返回 `Command line interface is not enabled. Please turn it on in Settings > General > Advanced.`，**rc=0**。从 `obsidian-1.13.7.asar` 反读：开关 = 主进程配置 `D.cli`，持久化到 `obsidian.json` 的 `"cli"` 键（当前该文件除 `vaults` 外无任何键）；socket 服务与开关无关，每条命令执行前检查 `D.cli` |
| macOS「Register」按钮 | `osascript … with administrator privileges` 执行 `ln -sf <App>/Contents/MacOS/obsidian-cli /usr/local/bin/obsidian`，并清掉旧版写进 `~/.zprofile` 的 PATH 行（asar 反读）。**在 AppTranslocation 状态下注册会指向下次启动就消失的路径** |
| 主 session 已做 | `codesign --verify --deep --strict` + `spctl -a` 通过（Developer ID: Dynalist Inc.）后 `ditto` 拷入 **`/Applications/Obsidian.app`**（482 MB），清除副本的 quarantine 标记，复验签名通过。**未**退出用户正在运行的实例，**未**开 CLI 开关（GUI 操作 + 需重启 App）|
| 待用户做 | 退出 Obsidian → 从 /Applications 重开 → Settings > General > Advanced 打开「Command line interface」。之后可用全路径调 `obsidian-cli`，Register 步骤可选 |

### 2.2 线上 vault `canvas-vault`（⛔ 只读扫描）

| 项 | 计数 |
|---|---|
| 原白板 / 节点 / 检验白板 | 6 / 14 / 10 个 md |
| 原生块 id 行（`^xxx` 行尾） | **0** |
| `[[x#heading]]` 标题级链接 | **0**（143 条 `[[lecture 2.mp4#t=…]]` 是视频时间戳，不是标题） |
| `[[x#^block]]` 块级链接 | **0**（仅 2 处出现在 skills 文档里） |
| 普通 `[[wikilink]]` | 283 |
| 用户批注 callout（`[!tips/error/question/keypoint][+-]`） | **12**：question 6、tips 5、error 1；节点 10、检验白板 2、原白板 0 |
| 其中带 `%%cb-xxx%%` 稳定 id | **3**（其余 9 条是 A+-prime 之前的历史批注，无 id） |
| 列表内形态 `* > [!tips]+` | 5 行 |
| 检验白板写回节点的 `[!question]+ 待剖析 · 源自 [[检验白板/…]]` | 3（文件级链接） |
| 其它 callout | `[!info]` 15、`[!tip]`（单数，模板「💬 围绕这个概念讨论」）8、`[!quote]` 8、`[!exam_question]` 9、`[!relation/*]` 8、`[!warning]` 2、`[!error-candidate]` 1 |
| app.json | `newLinkFormat: absolute`、`alwaysUpdateLinks: true`、`useMarkdownLinks: false` |
| 已装插件 | templater、claudian、dataview、breadcrumbs、canvas-learning-system、excalidraw、excalibrain |

**含义**：用户说的「原生看到双向联系」今天在这个 vault 里**只到文件级**。块级 / 标题级的原生反链是空集，不是因为 Obsidian 不支持，而是 vault 里一条这样的链接都没有。

---

## 3. Obsidian 原生能力边界（一手文档，obsidian.md/help + docs.obsidian.md + changelog）

### 3.1 块引用 / 标题引用

| 能力 | 一手口径 | 对 CLS 的含义 |
|---|---|---|
| 简单段落块 id | 行尾 ` ^id`；自动补全 `[[^` 生成 6 位 id | 节点正文段落可直接锚 |
| **结构块（列表 / 引用 / callout / 表格）** | `^id` **单独成行，前后各一个空行**（help/links；0.9.5 changelog 原话相同） | CLS 批注是 callout，id 只能挂在 callout **之后**一行 |
| 列表项 | id 可直接放在 bullet 行尾；**子列表不支持**（staff 2020-11-27） | 列表内批注 `* > [!tips]+` 的 id 位置官方无定义 |
| **callout 内部** | **「We do not support links to specific parts of quotations, callouts, and tables」**（help/links；feature request 98676 仍开） | 批注里的「✍️ 我的理解」行、理解度 checkbox **不能单独被链接**，粒度上限 = 整条 callout |
| id 字符集 | 只允许 Latin 字母 / 数字 / 短横（0.9.6 起允许 `-`） | 项目的 `cb-<base36>` **已是合法块 id**，无需转换 |
| 嵌入 | `![[note#^id]]` 完整渲染整条 callout（含标题、折叠、样式；论坛 72455 实测） | 可把某条批注嵌进原白板 / 检验白板 |
| 全库搜索 | `[[^^…]]` 搜块、`[[## …]]` 搜标题 | 今天 vault 里 0 个块 id，搜出来是空 |
| 标题改名传播 | **只**通过右键「Rename heading」命令传播（0.12.14/0.12.19）；直接改标题文字**不会**更新 `[[note#heading]]`；多级 `[[N#H1#H2]]` 连命令都只部分实现（staff 2025-07-26） | skills 要求的 `[[file#heading]]` 引用在用户改标题后会断 |
| 块 id 改名传播 | 只通过右键「Rename block ID」（0.14.13-0.14.15）；手改 `^id` 不传播；块移到别的文件链接全断（论坛 45658，无原生方案） | 派生 / 写回都在文件间搬文本，块级链接会跟着断 |
| 重复 id | 同一文件允许重复 id，链接只解析到其中一个，无警告（论坛 93311） | 全库唯一性要 CLS 自己保证 |
| Live Preview 渲染 | `^id` 以 `.cm-blockid` 文本可见（用户需 CSS 隐藏，论坛 77682/79035）；阅读模式一般隐藏；紧贴内容无空行时阅读模式也会露出（论坛 66586） | 非技术用户会在每条批注下看到一行 `^cb-ms03p2v9bzhb` |
| 可移植性 | 0.9.5 发布说明原话：「isn't portable Markdown (no other tools support it yet)」 | Codex / OpenCode 直接读文件时 `^cb-xxx` 是字面噪音；`%%…%%` 至少读起来像注释 |

### 3.2 反向链接的数据模型

| 层 | 粒度 | 一手依据 |
|---|---|---|
| `metadataCache.resolvedLinks` / `unresolvedLinks` | **文件级**：`Record<src, Record<dst, count>>`，`[[A]]`/`[[A#h]]`/`[[A#^b]]` 折成同一目标计数 3 | docs.obsidian.md/…/resolvedLinks |
| `getFileCache(file).links[]` | **保留子路径**：`LinkCache.link` 是原始 linktext；`parseLinktext()` → `{path, subpath}`；`resolveSubpath()` → 块 / 标题的精确位置 | obsidian.d.ts 1.12.3 :4652 / :5328 |
| `getFileCache(file).blocks / headings / sections / listItems` | 每文件的块 id、标题、段落类型（含 `callout`）与位置 | obsidian.d.ts :1284-1440, :5496-5510 |
| `getBacklinksForFile` | **非公开 API**（d.ts 无、docs 404），运行时存在，返回带子路径的 LinkCache | 论坛 81638 |
| Backlinks 面板 | 文件级列表 + 上下文行；子路径只作为原文文本出现，无子路径分组 | help/plugins/backlinks |
| Dataview | `file.outlinks` 保留 subpath（`meta(link).subpath/.type`），**`file.inlinks` 只到文件级**（index 只存 `l.path`） | dataview 源码 index.ts / markdown.ts |
| Breadcrumbs | 只吃 typed links（frontmatter / `field:: [[X]]`），**先 `split("#")[0]` 丢子路径** | breadcrumbs `src/utils/obsidian.ts` |
| ExcaliBrain | 只读 `resolvedLinks`（文件级） | excalibrain `src/graph/Pages.ts` |

**结论**：Obsidian 内部确实有块级反链的原料（每文件 `links[]` + `parseLinktext`），但**任何现成 UI / 插件 / CLI 命令都只把「双向联系」展示到文件级**；块级双向要自己写聚合。

### 3.3 CLI 命令面（help/cli 1.12.4+ 全量表，主 session 抓取）

| 族 | 命令 | 对关系梳理的价值 |
|---|---|---|
| 链接与图 | `backlinks [file\|path\|counts\|total\|format=json\|tsv\|csv]`、`links [file\|path\|total]`、`unresolved`、`orphans`、`deadends` | **文件级**；无 subpath / 行号 / 链接文本参数（对照 `unresolved` 有 `verbose`，`backlinks` 没有）；JSON 字段 schema 一手无样例，**接通后必须先本机实测一次** |
| 结构 | `outline [file\|path\|format=tree\|md\|json\|total]` | 标题树；**没有任何列块 id / sections 的命令** |
| 搜索 | `search query= [path\|limit\|format=text\|json\|total\|case]`（返回路径）、`search:context`（grep 风格 `path:line: text`）、`search:open` | `react_agent._format_cli_results` 的正则 `^(.+?\.md):(\d+):\s*(.*)` 与官方格式一致；是否支持 `tag:/path:/file:` 操作符官方沉默，论坛有 exit 127 / 冷启动空结果的未定论报告（113399） |
| 读写 | `read`、`create`、`append`、`prepend`、`move`（自动改链）、`rename`、`delete`、`properties/property:*`、`tasks/task`、`tags/tag`、`daily:*`、`templates/template:*`、`bases/base:query` | 写命令对本议题非必需 |
| 脚本 | **`eval code=<js>`** —— App 上下文执行任意 JS，可达 `app.metadataCache.getFileCache()` | **块级 / 标题级双向联系唯一的 CLI 通路**；同时也是任意读写全权（§4.6） |
| 开发 | `dev:screenshot / dev:console / dev:dom / dev:cdp`、`plugin:reload` | 插件开发循环 |
| 其它 | `vault/vaults`、`commands/command id=`、`hotkeys`、`--copy` | `hotkeys`/`commands` 对 G2-6 四件套校验有用（旁支） |

### 3.4 CLI 运行约束（一手 + 三方实测，已标注来源级别）

| 约束 | 来源 |
|---|---|
| **非 headless**：必须有运行中的 GUI；App 未运行时第一条命令会把它拉起来 | help/cli 原话；obsidian-headless 只做 Sync/Publish，Docker headless 请求「Closed as not planned」 |
| **退出码恒 0**，错误印在 stdout `Error: …` | 论坛 112242（staff：「unimplemented feature」）；主 session 实测未启用横幅 rc=0 |
| ~~每命令 ~1 s 往返~~ **本机实测 0.030 s/命令（33 条，§11）**；禁并发（eval/move 并发会串输出） | dsebastien 2026-07-25（三方，已被本机实测推翻）；官方沉默 |
| `vault=` 必须首参；省略时取 cwd 所在 vault 或「当前活动 vault」；放错位置静默回落到聚焦 vault | help/cli；论坛 112217（1.12.4 实报） |
| `file=` 按 wikilink 同款解析（不看 alias、大小写不敏感、重名取 best match）；`path=` 精确路径 | help/cli；论坛 113902（staff 确认不看 alias） |
| 需 1.12+ **安装器**（不是自动升级的 App 核心）；DMG 安装的安装器不自动升级 | help/cli；论坛 111419 |
| 桌面限定；沙箱化 harness（Codex）调用 socket 不可达时会拉起第二个 App 进程并崩溃（staff：Claude Code 不复现） | 论坛 113099 |

---

## 4. CLS 现状：关系是怎么记的

### 4.1 关系清单（写方 → 落盘形态 → 粒度 → 读方）

| 关系 | 写方 | 落盘形态 | 当前粒度 | 读方 |
|---|---|---|---|---|
| 原白板 → 成员节点 | `sync_board_concepts.py`（`## Concepts` AUTO-GENERATED） | `- [[节点/X]] — 种子/派生 · …` | 文件级 | 原白板 dataviewjs `## 🔗 节点关系图（v2.8）`、`board_manifest_service` |
| 节点 → 所属原白板 | `node-derivation.ts` | frontmatter `source_board: "[[原白板/B]]"`、`up`、`derived-from`、`source_note` | 文件级 | dataviewjs（按 `source_board` 过滤）、后端 `_node_role` |
| 节点 ↔ 派生关系 | `ai-linked-doc.ts` / `node-derivation.ts` | 源笔记 `> [!relation/<key>]+ 已派生为 [[节点/X]] · 扩展` callout + 新节点 frontmatter `relationships[{type,target,description}]` | 文件级（callout 锚在源文本**之后**，但链接本身不带子路径） | `relationship_sync_service`、`board_manifest_service`、Graphiti CANVAS_EDGE |
| 批注 → 节点 | 插件 Cmd+Shift+A（`main.ts` wrapSelection） | `> [!tips]+ 💡 Tips %%cb-xxx%%` + 理解度 checkbox + 选中原文 + `> ✍️ 我的理解：` | **批注内嵌原文**（位置即锚），身份 `%%cb-xxx%%` 不可原生链接 | 插件 `frontmatter-tips-sync.ts` → frontmatter `tips[]`；`callout-sync.ts` → `POST /tips/batch`；后端 `vault_backfill.extract_callouts`、`wikilink_context_service._extract_user_callouts`、LanceDB 分块器；Graphiti RELATES_TO 自环边（annotation_id） |
| 检验白板 → 节点 | `quiz-answer/SKILL.md` 4c（静态 python） | `> [!question]+ 待剖析 · 源自 [[检验白板/<name>]]（日期）` | 文件级 | `review_overview.py`「待剖析」列 |
| AI 回答 → 材料 | `chat-with-context` / `study-question` 规则 14 / 9 | 对话里的 `[[file#heading]]`（不落盘） | 标题级（规则），块级允许 | 用户点击跳转 |
| 后端图 | `wikilink_graph_service.py`（obsidiantools + NetworkX） | 内存图 | **文件级**（§5 实验 1：子路径被丢弃） | `get_neighbors` MCP、`wikilink_context_service.enrich_from_wikilink_graph`、RetrievalTrace |

### 4.2 批注身份的三层链与四份平行解析器

- **身份链**：插件 `%%cb-<base36>%%`（`callout.ts:61-70`）→ 节点 frontmatter `tips[].id`（`frontmatter-tips-sync.ts:35-42`，按 id 匹配保留 `added_at`）→ 后端 `POST /tips/batch` / `callout_direct` → Graphiti 边 `annotation_id`（`2026-07-20 地图` line 80：RELATES_TO 40 条实测）。`graphiti_belief_service.make_callout_belief_key(node_id, node_path, offset)` 全仓**无调用点**（死代码，offset 身份不构成风险）。
- **四份解析器**（不是三份）：`callout.ts parseCalloutsFromContent`（只认 4 个复数 tag + `+/-` 后缀，body = 连续 `>` 行）、`vault_backfill.extract_callouts`（允许列表前缀）、`wikilink_context_service._extract_user_callouts`（kind 集 = `{question, tip, error, hint, note, warning, info}`，:189-197——含**单数 `tip`** 与模板类 `info/note`，却**缺插件实际写出的 `tips` 与 `keypoint`**，即插件批注在这条摘录通道里被静默丢弃、模板 `[!info]` 反被当用户批注）、`backend/lib/agentic_rag/clients/lancedb_client.py:2772 head_pattern`（无列表前缀允许）。它们对同一 vault 已经给出不同的「用户批注」集合——这是**既有**漂移，与块 id 无关，但任何新身份层都会乘上它。
- **列表内批注既有缺口**（§5 实验 2）：`* > [!tips]+` 若续行带缩进 `  > `，插件解析器返回 0 条——无论有没有块 id。

### 4.3 后端自建图（obsidiantools）的两个缺陷

1. **子路径全丢**（§5 实验 1）：`[[B#^cb]]`、`[[B#标题]]`、`[[B]]` 全折成 `B`。后端图**永远看不见**块级 / 标题级联系，即使 vault 里写了。
2. **absolute 链接格式下的幽灵节点**（cli 镜头只读实测，`digest cli[24]`）：vault `newLinkFormat=absolute` 写出 `[[节点/X]]`，obsidiantools 只剥 `|alias` 与 `#subpath`、保留文件夹前缀，又用 stem 作笔记键 → 反链堆到幽灵节点 `节点/X`（被归为 nonexistent_notes，实测 72 个），真实节点 `X` 入度 **0**（6 个抽样 `in(stem)=0`，`in('节点/stem')=4/5/1/3/2/1`）。`wikilink_graph_service.py:161-171` 的 basename 回退注释承认「同一物理文件有两个图节点」，但只挑「有邻居的那个键」，无法把出边与入边合到一起。→ **对本 vault，后端的 backlink 语义当前就是错的**；Obsidian 原生 `resolvedLinks` 不会犯这个错（插件侧 `configure-whiteboard.ts:88-96` 已在用它做反向引用检测，「200 笔记 < 10ms」）。

### 4.4 react_agent 的 CLI 三工具（架构规划的「CLI 层」）在 macOS 从未通过

`backend/app/services/react_agent.py:376-490`：`search_obsidian_cli`（`search:context`）、`get_note_outline`（`outline`）、`find_backlinks`（`backlinks`）三个 `@tool`，`REACT_TOOLS` :641 把 `search_obsidian_cli` 标为「Primary search」，`agent_service.py:1617` 系统提示写「优先使用 search_obsidian_cli」。两处根因：
- 二进制路径写死 Windows：`os.path.join(os.environ.get("LOCALAPPDATA",""), "Programs", "Obsidian", "Obsidian.com")`（:390/:428/:463）→ macOS 恒 `[Error] Obsidian CLI not available`；
- `vault=` 传 `_resolve_effective_group_id().upper()`（如 `VAULT:CS_61B:ALGORITHMS`）且放第 3 个参数——既不是 vault 名（`canvas-vault`）也不是 vault id（`0a302bd176301457`），也不在首参位 → 即便路径修好也会静默落到「当前聚焦 vault」。
- 成功判定 `returncode == 0 and stdout.strip()`（:405-411 / :447-449 / :482-484）与「退出码恒 0 + 错误印 stdout」冲突：会把 `Error: File … not found.` 当成大纲 / 反链正文喂给 LLM。

### 4.5 部署拓扑对 CLI 的硬约束

`docker-compose.yml:142-175`：backend 在容器里跑（`build: ./backend`，vault bind-mount 到 `/vaults`）。容器内既没有 `~/.obsidian-cli.sock` 也没有 App 包内二进制 → **容器化后端调不到 CLI**。launchd 每小时复习链（`scripts/launchd/daily-review-wrapper.sh`）若调 CLI，会在 App 未运行时把 GUI 拉起来。CLI 通道只对**宿主侧 harness**（Claude Code / Codex / OpenCode 在用户桌面上跑）成立。

### 4.6 只读纪律的绕过面

`.claude/hooks/pretool-guard.js:15-26` 只检查 Edit / Write 工具。开启 CLI 后，`obsidian eval code=…` 以 App 全权执行任意 JS（可读写任何 vault 文件 / 设置），经 Bash 调用不过 guard——线上 vault 只读、PRD 只读锚定都会被绕过。启用 CLI 的同时需要给 guard 加 `obsidian eval|create|append|prepend|move|rename|delete|property:set` 类命令的 Bash 拦截。

---

## 5. 实验记录（主 session，全部在 scratchpad 临时 vault / 打包产物上做，未动仓库与线上 vault）

| # | 实验 | 结果 |
|---|---|---|
| 1 | 临时 vault：`A.md` 含 `[[B#^cb-abc123]]`、`[[B#核心概念]]`、`[[B]]`；用 `card-v5-lance/backend/.venv` 的 obsidiantools `Vault.connect()` | `get_wikilinks('A') = ['B','B','B']`，`graph.edges = [(A,B)×3]`，`get_backlinks('B') = ['A','A','A']` → **子路径完全丢失** |
| 2 | 用插件自己的 esbuild 把 `src/callout.ts` 打成探针，喂 5 组样本 | callout 之后「空行 + `^cb-abc123`」：输出与基线**逐字节相同**（tag/id/understanding/content/contentHash）；无空行同样不受影响；两条 callout 各带 id 行 → 2 条正确；列表内 `* > [!tips]+` + 缩进续行 `  > ` → **有无 id 都是 0 条**（既有缺口）；续行不缩进 → 有无 id 都正常 |
| 3 | grep 生产路径对 `ParsedWikilink.heading/.block_id` 的消费 | **无消费者**（只在 `wikilink_parser.py` 内）；`context_enrichment_service.extract_and_resolve_wikilinks` 自己 `split("#",1)` 抽标题段（:206-207），把 `^block` 当标题查 → 查不到 |

---

## 6. 社区先例：两族身份设计（precedents 镜头，一手 README / 论坛）

| 族 | 产品 | 身份形态 | 教训 |
|---|---|---|---|
| **同步身份**（不需要被链接） | Obsidian Spaced Repetition（`<!--SR:…-->` 位置锚定注释）、Obsidian_to_Anki（`<!--ID: …-->`）、Yanki（frontmatter noteId） | 不可见注释 / frontmatter | SR 把注释挪到同一行就丢卡（issue 1182）；无 id 重跑就重复（Obsidian_to_Anki #148）；删 noteId 就孤儿 |
| **可链接身份**（用户要 `[[#^]]` 到它） | Zotero Integration（`^{{entry.id}}` 每条 PDF 批注）、ZotLit v1（callout + block-id，「never delete the block-id」）、Readwise（`^rw{{highlight_id}}`）、Omnivore 补丁、Kindle Highlights（内容哈希块引用）、flashcards-obsidian（`^q-xxxx` + 受管 frontmatter） | 原生 `^id`，**永远由导入器写入，不让用户手写** | ZotLit v1 的「每条 callout 一个 block-id 增量更新」在用户把批注重组成列表后**崩了**，v2（2026-07）改成 `%%zt-managed%%` 整段重建；Zotero persist 区易丢手写内容 |
| **块即身份**（另一种世界观） | Logseq（`id:: uuid`，块级反链计数）、Roam（`((uid))`） | DB 为主 | Logseq 文件从磁盘重载会丢块引用（issue 7362）；uuid 噪音；Obsidian 社区把 Logseq 式块反链搬进来的插件只有 12 star |
| Agent 侧 | kepano/obsidian-skills（官方 CEO 的 skill）：教 agent 用 `obsidian backlinks file=…`、教 `^block-id` 语法与「结构块后单独一行」规则；MCP 包装器（ZethicTech/obsidian-mcp、stonematt）暴露 get_backlinks/get_links/orphans | 全部**文件级** | 公开案例里**没有**块级反链遍历；报告的收益是 token（orphan 检测 7M → ~100 token）与速度（grep 15.6 s → 0.26 s） |

CLS 的 `%%cb-xxx%%` 落在第一族；用户今天的提议等于把它升到第二族——代价与收益结构和 Zotero/Readwise 一样：id 必须由插件 / 迁移脚本写，callout 后多一行，改删 / 搬动时链接会断。

---

## 7. 学术实证（DD-01，academic 镜头，只收一手）

| 方向 | 一手来源 | 结论 |
|---|---|---|
| RAG 引用粒度 | Anthropic Citations API（句级分块，内部评估 recall +15%，引用保证指向真实文本）；Liu et al. 2023（arXiv 2304.09848：生成式搜索仅 51.5% 句子被引用完全支持）；ALCE（arXiv 2305.14627：最佳模型 50% 缺完整引用支持）；Contextual Retrieval（细块若无上下文，top-20 检索失败率可差 35-67%） | **支持**「AI 回答引用要到标题 / 块级」——印证 skills 现有规则；也提醒块级索引必须带上文（板名 / 标题） |
| 学习科学 | Karpicke & Blunt 2011（d=1.50，机制是检索本身）；Karpicke 2017（给更多检索线索会**缩小**检索练习效应）；Ponce, Mayer & Méndez 2022 元分析（学习者自己高亮：记忆 d=0.36、**理解 0.20 不显著**）；CiteRead IUI 2022（n=12，把评论定位到原文段落比文件级列表更利于理解与保留）；Zellweger CHI 2000（n=6，就地注释省时间但理解无差异） | **没有任何一手研究把「链回精确源块」当变量**。块引用只能按「导航 / 核验」收益论证，**不能按「提升理解」论证**；在检验白板作答时暴露精确源块链接反而可能削弱检索练习效应，应放到作答后的回顾视图 |
| 超文本理论 | Nelson 1990 / 1999（transclusion = 引用片段不失上下文；字符级双向链接） | 设计愿景，不是实证；对应 `![[note#^id]]` 嵌入优于复制粘贴 |
| 批注锚定标准 | Hypothes.is fuzzy anchoring（三级选择器回退）、W3C Web Annotation（同一片段多选择器冗余） | CLS callout「内嵌原文 + `%%cb%%`」已是双选择器；原生 `^id` 是第三个，与标准的冗余建议一致；真正的风险是**解析器漂移**不是锚漂移 |
| Obsidian 设计意图 | 0.9.5 / 0.9.6 changelog（在文件内的 `^id`、不可移植、结构块单独成行）；kepano「file over app」 | 身份应留在 .md 文件里而不是只在 Neo4j / LanceDB——`%%cb%%` 与 `^id` 都满足 |

---

## 8. 核验结果（12 条核心主张 × 3 路反驳）

### 8.1 方法与如实声明

- 第一轮工作流（6 镜头 sweep + 41 条主张 × 3 路核验 + 批评 + 综合，131 agent）：**5 个镜头完成，codebase 镜头与全部 123 个核验、批评、综合因「session limit」失败**——核验层等于没跑。codebase 镜头的内容由主 session 侦察（§4）与 risks 镜头的代码实读补齐。
- 第二轮（本节）：把 41 条 benefit/risk 归并为 12 条**决定裁决方向**的核心主张，每条 3 个视角（来源保真 / 用户价值 / 成本破坏）各一个反驳者，37 agent **全部完成，0 失败**。判据：≥2 票反驳 = 未幸存；3 票全反驳 = 已推翻。裁决只用幸存主张。
- 核验 agent 全程只读（未开 CLI、未写仓库 / vault）；引用一律 file:line 或 URL+原文。
- 局限：`obsidian links` 输出是否带 `#subpath`、CLI backlinks 对 `[[节点/X]]` 的解析行为，只有开 CLI 实测才能关闭（卡 a）；线上「用户从不改删批注」只能靠 git（不追踪线上日常编辑）+ 用户自述。

### 8.2 逐条结果

| # | 类型 | 主张（缩写） | 反驳票 | 结果 | 幸存 / 修正后的表述 |
|---|---|---|---|---|---|
| C1 | benefit | CLI 净增量 = 让 harness/后端读到原生文件级图 | 2/3 | 未幸存 | 事实半句三票一致（CLI 链接命令只有文件级参数，块/标题级只能 `eval` 自聚合，`links` 输出格式文档未载）；**收益半句被驳**：harness 已有同粒度数据，容器后端调不到，出题依赖 frontmatter 类型化 `relationships[]` 而非反链计数 |
| C2 | benefit | `cb-<base36>` 已合法，追加一行 `^cb-xxx` 即可让每条批注可链接；解析器零影响 | **3/3** | **已推翻** | 幸存为事实的部分：字符集兼容、`parseCalloutsFromContent` 逐字节不变、顶层 callout 可整条被链。被驳：「每条」不成立（线上 5 条列表内批注无逐条块 id，staff「We don't support sub-list blockid linking」）；「只需一行」不成立（`main.ts` 两处光标算术、两条后端文本管道会吞该行、双身份无对账、9/12 无 id、vault 只读）；「零影响」只对一份解析器成立；CLS 无任何消费者读块 id |
| C3 | risk | 节点↔批注联系已三形态覆盖，块 id 净增量只剩整条 callout 可寻址 | 0/3 | **幸存** | 修正：`tips[]` 只同步 `节点/`、`原白板/`（`frontmatter-tips-sync.ts:28`），检验白板的 2 条与 Dashboard 的 callout 不进 `tips[]`；「40 条 RELATES_TO」是主图总数；净增量补上 `obsidian://open?file=Note%23%5Ecb` URI 深链（vault 外 / 跨 vault Web UI 可指到具体批注）；稳定 id 只覆盖插件写的批注（3/12），`quiz-answer` 写的 callout 无 id；补 id 会重置历史批注 `added_at`（`frontmatter-tips-sync.ts:117-121`） |
| C4 | benefit | 修 `react_agent` 三 CLI 工具 = 补活架构既有管道，落在 MVP #10/#5 | 2/3 | 未幸存 | 事实三票一致（`architecture.md:35` 规划、三工具 macOS 恒死、`agent_service.py:1617` 仍令优先用）。被驳：Hybrid 插件与全部 skills 不经 react 路径，且该路径一轮内回落 LanceDB；`mvp-plan.md` #10/#5 未提 CLI；容器拓扑下改路径无效；复活 = 拓扑改动 + rc 判定 + vault 映射 + eval 写面守卫 = 新集成面。**处置应为退役**（卡 b） |
| C5 | risk | CLI 非 headless；容器后端不可达；launchd 会拉起 GUI | 0/3 | **幸存** | 修正：vault bind-mount 在 `docker-compose.yml:218`；「不能给容器后端用」→「不能直接用，除非经 `host.docker.internal` 宿主 shim（compose 对 Ollama 已用同模式），而 shim 只换来 obsidiantools 已有的文件级反链，不值得建」；launchd 今天不调 CLI，一行 `pgrep -x Obsidian` 守卫可消除 |
| C6 | risk | 退出码恒 0 + `react_agent` 成功判定 → 错误当正文 | 1/3 | 幸存 | 修正：只在「路径 + vault= 首参 + 容器拓扑」三者都改后才成为活风险；rc 双向不可靠（forum 113399 exit 127 / 冷启动 exit 0 空输出），修复须解析 `Error:` 前缀 + `format=json`；现无测试钉住该判定；对今天用户体验零影响（死路径） |
| C7 | risk | obsidiantools absolute 幽灵节点 → 后端 backlink 语义当前是错的 | 2/3 | 未幸存 | 机制三票一致（`md_utils.py:376-380` 不剥文件夹前缀、`api.py:1088` stem 作键 → 同一笔记拆成 `节点/X`（承接全部入边）与 `X`（承接全部出边）两键；11/14 非重名节点 `in(stem)=0`；Fundamentals 反链 7:1 分裂；重名 stem 键规则反转）。**「反链错」措辞被驳**：生产调用方（`chat.py:298`、`wikilink_tools.py:58`）传 vault 路径，恰落在持有全部入边的键上，14/14 节点 hop=1 反链正确；丢的是**出边**与 `get_degree` 半计数（影响 `chat.py:434-442` hub_penalty）。十余行键归一可修（卡 c） |
| C8 | risk | 每条批注多一行可见 `^cb-xxx` 的成本 | 0/3 | **幸存** | 修正：两处光标算术的尾行不同（`> ✍️ 我的理解：` / `> ✍️ 我的疑问：`），不变量是「最后一行 = 提示行」；行尾误输入后果是链接失效不丢数据（四份解析器都忽略该行）；LanceDB/摘录污染与 kind 漂移是 `%%cb%%` 现状已有问题，只应计增量；可用插件内置 CSS `:not(.cm-active) > .cm-blockid{display:none}` 弱化（`display:none` 全隐会破坏方向键导航）；列表内 / 嵌套 callout = 官方不支持，**阻断** |
| C9 | risk | 开 CLI 后 `eval` 绕过只读纪律 | 2/3 | 未幸存 | `eval` 全权属实；被驳的是「绕过」：**今天没有任何 hook 对 Bash 写线上 vault / PRD 做阻断**——`pretool-guard.js` 只查 Edit/Write 的 DD-03 stub 正则、无路径检查；只读从来是文本级纪律；CLI 自带 `create/delete/move/append/property:set` 写命令，eval 不是唯一口子。**真正的行动项**：修正根 CLAUDE.md「pretool-guard.js hook 强制阻断」的失实承诺，补 Bash 路径级 PreToolUse 守卫（含 `obsidian eval|create|delete|move|append|property:set` 模式）——与开不开 CLI 无关 |
| C10 | risk | 2026-06-13 阶段 2 触发条件未满足；FR-RET-13「零侵入」；MVP #10 标题级 → DD-10 蔓延 | 0/3 | **幸存** | 修正：`question_generator.py` 引用应为 :342-353、:1054-1058（「当前态读 frontmatter 真相源，Graphiti 降为历史事件流」）；标题级精度出自 `architecture.md:35` 与 prd:819，`mvp-plan.md:258` 未定精度；「无改删」证据弱但未被证伪；**该延后是 Claude 提案「待 ChatGPT 审查」（doc :8），研究目录里无用户明示追认**——若用户今天裁定，性质是「首次明确裁定」而非「翻转」 |
| C11 | benefit | 学术侧只支持「导航/核验」，不支持「提升理解」 | 1/3 | 幸存 | 修正：Anthropic 的 `up to 15%` 是内建 Citations API 相对 custom prompt-based 实现的优势，CLS 的 skills 规则 + `agent_graph.py:522` 正则抽引用**正是被比下去的基线**；「提升理解」不能写成「没有任何研究」——CiteRead（n=12 科学家）以段落级定位 vs 文件级列表为变量报告理解 / 保持提升，Ponce 2022 教师提供锚点有 0.44 理解增益（学习者自生成 0.20 无）；同时有反向一手证据（Karpicke 2017 更多检索线索缩小检索练习效应；Niederhauser 2000 链接密度抑制学习）→ 表述为「理解收益证据薄弱且未在学习情境复现」 |
| C12 | risk | CLI vault 定位静默回落 = 跨 vault 泄漏面 | 0/3 | **幸存** | 修正：本机 obsidian.json 当前 `open` 的是开发文档 vault `_bmad-output` 与私人 vault，**线上 canvas-vault 未 open**——任何无 `vault=` 的调用会落到开发文档 vault；`react_agent.py:397` 已踩这个坑；三套身份（`.canvas-config.yaml` 的 `vault_id: canvas_vault` ≠ 文件夹名 `canvas-vault` ≠ obsidian.json hex id `0a302bd176301457`）；缓解 = 单一 harness 侧 wrapper：以 vault 根 realpath 查 hex id → `vault=<hex>` 首参 → 调用前 `vault info=path` 回验 |

**幸存计数**：benefit 1（C11，且只剩「导航 / 核验」半句、在 CLS 内尚未兑现）；risk 6（C3、C5、C6、C8、C10、C12）。

---

## 9. 裁决与分 goal 卡建议

### 9.1 已有形态对照：用户想要的「原生看到各文本的双向联系」今天靠什么实现

| 形态 | 粒度 | CLS 里谁在用 | 备注 |
|---|---|---|---|
| Obsidian 原生 Backlinks 面板 / Graph View / `metadataCache.resolvedLinks` | 文件级 | 插件 Cmd+Shift+C 取 1-hop 邻居经剪贴板注入 harness（`main.ts:491,537-545`）；`configure-whiteboard.ts:88-96` 反向引用检测 | **这已经是「原生双向联系」本身**，用户今天在 Obsidian 里就看得到 |
| 后端 `wikilink_graph_service`（obsidiantools）经 MCP `get_neighbors` | 文件级（子路径全丢） | `study-question` 2-hop、`chat.py:298` enrich、hub_penalty | 有入/出边分裂缺陷（C7，卡 c） |
| 节点 frontmatter `tips[]` / `relationships[]` | 批注级 + 类型化关系（`up` / `derived-from` + description） | 出题当前态真相源（`frontmatter_signals.py`、`start-exam-board` SKILL） | 只同步 `节点/` `原白板/` |
| Graphiti RELATES_TO 自环边（SelfAnnotation，node_id + annotation_id） | 批注级 | `graphiti_structured_writer.py:140,180` | 依赖 POST 成功 |
| callout 内嵌用户选中原文 + `%%cb-xxx%%` | 批注级（阅读模式隐藏） | `callout.ts` | 12 条中 3 条带 id |
| skills 引用规则 `[[file#heading]]` | 标题级 | `study-question` / `chat-with-context` | MVP #10 精度口径的实际落点 |

**块引用的净增量**：只有「整条 callout 可寻址」（vault 内 `[[节点/X#^cb]]` 跳转 / 嵌入、`[[^^` 搜块、vault 外 `obsidian://…%23%5Ecb` 深链）。Obsidian 内部可见，CLS 无任何消费方；不能链到 callout 内部；线上 0 条。
**CLI 的净增量**：对宿主 harness = Obsidian 原生解析正确性（大小写不敏感、`节点/X` 解析到真实文件——正是 obsidiantools 出错的地方）+ 免费 orphans / deadends / unresolved + outline 标题树 + `search:context` 行级命中；代价 ~1 s/条、不可并发、rc 恒 0、`vault=` 必首参。对容器后端 = 0。对子文件粒度双向边 = 0。

### 9.2 分 goal 卡（4 张，按建议优先级）

| 卡 | 名称 | 建议 | 范围一句话 | 触碰文件 | 完成条件 | 本卡未证明什么 | 依赖「重开 App + 开 CLI」 |
|---|---|---|---|---|---|---|---|
| **(c) WLGRAPH-KEY-NORM** | obsidiantools absolute 链接下的入/出边分裂修复 | **建议做**（小卡，正确性修复，与提问无关） | 建图时把链接目标归一到文件键（stem / relpath，按 obsidiantools 重名规则）或查询时合并两键的 in/out；`get_degree` 同步；不改 MCP schema、不升 obsidiantools | `wikilink_graph_service.py:113-118,127-128,161-183,283-303`；`tests/unit/test_wikilink_graph_service.py`（补 path 形态）；参考不动：`wikilink_context_service.py:466-475`、`wikilink_tools.py:16-20,58` | fixture 复现三形态（`[[节点/X]]` 绝对、裸 `[[X]]` 混用 7:1、vault 内重名 stem）；每节点 `get_neighbors(path,hop=1)` 同时返回入边与出边、`get_neighbors(path) == get_neighbors(stem)`、`get_degree(path) == in+out`；线上只读探针复跑 14/14 节点 `in(stem)` 不再为 0 或两键已合并；tests/unit 红基线 diff 为空 | 对出题 / 检索的可感知变化（14 节点 vault 上 hop=2 经原白板回流已召回兄弟节点，损失接近零） | 否 |
| **(b) REACT-CLI-DEMOTE** | `react_agent` 三个 Obsidian CLI 工具的处置 | **建议按 G-PIPE 处置卡「退役」**（方案 A）；修复（方案 B）只在用户明确要保留 CLI 层且后端出容器 / 加宿主 shim 时成立 | A：把 `search_obsidian_cli` / `get_note_outline` / `find_backlinks` 移出 `REACT_TOOLS` / `SCORING_TOOLS`（:641-656），删 `agent_service.py:1617`「优先使用 search_obsidian_cli」指令，函数体整体删除（DD-13：不留恒报错的「主搜索工具」），补单测断言注册表不含 CLI 工具 | `react_agent.py:376-484,528-556,641-656`；`agent_service.py:1617`；新增 `tests/unit/test_react_tools_registry.py` | A：定向 pytest 绿 + `grep -n search_obsidian_cli backend/app` = 0 命中 + tests/unit 红基线 diff 为空 | 对用户体验 / 出题质量的任何增量（三票一致：该路径无生产入口） | A：否；B：是，且额外依赖后端出容器或 shim |
| **(a) CLI-PROBE-0** | 启用 CLI + 线上 vault 只读实测 `backlinks/links/outline/search:context` JSON schema | **可选 · 低优先级**（零代码）。唯一用途 = 关掉两个未验事实（`links` 是否带 `#subpath`；backlinks 对 `[[节点/X]]` 与大小写的解析）并给 `architecture.md:35`「CLI 层」一份实测依据；若用户接受本裁决并同意把该行改为「已弃用」，本卡可不排 | 用户开 CLI 后，主 session 对线上 canvas-vault **只跑读命令**（`vault info`、`backlinks format=json`、`links`、`unresolved`、`orphans`、`deadends`、`outline format=json`、`search:context`、`files`），落盘 stdout + rc + 耗时；禁 `eval/create/delete/move/append/property:set/plugin:install/bookmark` | 只读：obsidian.json、canvas-vault 抽样 5 个 md；新增 `_bmad-output/审查/evidence-cli-probe/<name>-<时间戳>.txt`（末行 `rc=`） | obsidian.json 出现 `cli` 键；canvas-vault 在 Obsidian 内已打开；`vault=0a302bd176301457` 首参 + `vault info=path` 回验 = canvas-vault realpath；对不存在文件跑 backlinks 记录 `Error:` 文本 + rc（预期 0，C6 验伪锚）；写明 `links` 是否带 `#subpath`、backlinks JSON 字段名、`[[节点/X]]` 与裸 `[[X]]` 反链是否合并；跑前/跑后 `git status --porcelain canvas-vault/` 一致 + 抽样 shasum 一致 | 任何用户可感知收益；子文件粒度的边（线上 0）；容器后端可用性（C5 已判不可达） | **是** |
| **(d) CALLOUT-BLOCKID** | 批注埋原生 `^cb-xxx` | **不建议现在做**（维持延后）。仅在用户对 §10 D-A～D-D 逐条裁定「做」后按最小范围排 | 只对插件新写入的顶层 callout（`wrapSelection` / `buildNewQuestionCallout`）在正文后追加 `\n\n^<与 %%cb-xxx%% 完全相同的 id>`（单一身份）；改两处光标算术 + 8/30 用例；插件内置 CSS 隐藏非活动行 `.cm-blockid`；后端摘录与分块剥 `^cb-` 行；**不迁移**线上 12 条既有批注（vault 只读、9 条无 id、5 条列表内不可寻址）；`quiz-answer` 等 skill 写手不动 | `callout.ts:224-247,260-271`；`main.ts:1547-1550,2760-2783`；`tests/callout.test.ts`；`wikilink_context_service.py:300-311`；`lancedb_client.py:2772-2782` | 新批注 Live Preview 非活动行不显示 `^id`、阅读模式不显示；`[[^^` 能搜到；`[[节点/X#^cb-…]]` 跳到整条 callout；四份解析器对同一文件输出与加行前逐字节相同（除被剥掉的 `^` 行）；线上 vault 零写入 | 对理解 / 出题质量的任何增益（C11）；列表内 / 嵌套 callout 永远不可逐条寻址 | 否 |

**DD-10 对照**：(c) 与 (b) 是既有管道的正确性修复 / 退役，不是新功能；(a) 是探针不是功能；(d) 不在 MVP 14 项内，需用户裁定。

### 9.3 与 2026-06-13 决策的关系

- 触发条件 1「出题需要完整演化史」：**未满足**——`question_generator.py:342`「当前态（批注/错误/原因）读 frontmatter 真相源，非 Graphiti」、`:1054-1058`「Graphiti 降为历史事件流」；`targeting_material_service.py:7`「Graphiti 是历史流」。
- 触发条件 2「用户频繁改删」：**未满足**（证据面偏弱）——主仓 `git log --since=2026-06-13 -G'\[!(question|tips|error)\]' -- canvas-vault/{节点,原白板,检验白板}` = 0 提交；未提交 diff 里 callout 头只有 +1 条生成器写回，0 条用户改删；线上共 12 条批注。git 不追踪线上日常编辑，最终以用户自述为准。
- **建议：维持「延后」。** 06-13 以来的新证据：降成本（三份解析器对尾随 `^id` 行逐字节不敏感，解析器一项可从成本估算里下调）、新增量（`obsidian://` URI 深链）、新成本（可见 `^id` 行 + 光标算术 + 分块污染 + 列表内不可寻址 + 双身份无对账）、新反向（学习科学侧无正向变量研究且有线索 / 密度的反向一手证据）——没有一条构成触发。
- 程序性提醒：该延后是 Claude 提案「待 ChatGPT 审查」（doc :8），研究目录里 06-14 → 07-20 无用户明示追认；所以若用户今天裁定，性质是**首次明确裁定**。按 CLAUDE.md 铁律应记 `[Decision-Review] PENDING`——本 session graphiti-canvas MCP 连接失败，先记在本文 §10 与本地 memory，待 MCP 恢复后补写。

---

## 10. 未证明清单 / 需要你决定的事

### 10.1 仍未证明（没有任何卡覆盖，或只有卡 a 能关闭）

1. ~~`obsidian links` 输出是否携带 `#subpath`~~ **已关闭（§11）：不携带**，输出是去重后的解析目标。
2. ~~CLI `backlinks` 对 `[[节点/X]]` 与大小写的解析~~ **已关闭（§11）：合并到同一文件**，大小写不敏感，frontmatter 嵌套链接也计入。
3. 线上 vault「用户从不改删批注」——git 不追踪线上日常编辑，只能靠你自述。
4. `eval` 通道的实际风险面（C9 未幸存，本次未做任何 eval 实验）。
5. 块级引用对「理解」的任何影响（学习情境无一手研究，本综合不立项）。
6. 根 CLAUDE.md「PRD 只读，`pretool-guard.js` hook 强制阻断」——**主 session 复核**：本 worktree `.claude/settings.json` 的 `hooks` 为 `{}`；主仓 PreToolUse 只对 `Edit|Write` 挂 `pretool-guard.js`（脚本头注释「Only keeps DD-03: blocks lazy stub patterns」，`:18` 非 Edit/Write 直接放行，无任何路径检查）与 `mock-import-guard.js`。即**没有任何 hook 按路径拦截对 PRD 或线上 vault 的写入**，Bash 侧 `sed -i` / 重定向 / python 写入本来就畅通。这与开不开 CLI 无关，但 CLAUDE.md 的承诺失实，应单独修正（补 Bash 路径级守卫或改文案）。

### 10.2 需要你决定的事（按 CLAUDE.md 铁律 4：用户是甲方，AI 只给最成熟方案）

| # | 决定 | 我的建议 | 若你选另一边 |
|---|---|---|---|
| **D-A** | 「批注埋原生 `^cb-xxx`」：维持 2026-06-13 延后，还是现在做？ | **维持延后**（§0 / §9.3） | 选「做」→ 排卡 (d) 最小范围，并同时裁 D-B / D-C / D-D |
| D-B | （仅 D-A=做）接受 Live Preview 里每条批注下多一行可见 `^cb-…`（CSS 可弱化，编辑态不能消除）？ | — | 不接受 → (d) 不可行 |
| D-C | （仅 D-A=做）接受 FR-RET-13「零侵入不修改用户笔记」被再突破一次（`%%cb%%` 已是一处）？ | — | 不接受 → (d) 不可行 |
| D-D | （仅 D-A=做）是否授权**一次性写线上 vault** 迁移 9 条无 id 批注（必须保留 `added_at`）？ | 不迁移，只对新批注生效 | 授权 → 独立迁移脚本 + 备份 + `cmp` 证据 |
| **D-E** | 是否排卡 (a) CLI-PROBE-0（需要你先退出 Obsidian → 从 /Applications 重开 → Settings > General > Advanced 打开 Command line interface，并在 Obsidian 里打开 canvas-vault）？ | 可选，低优先级；若你接受「收益不明显」，可不排，并把 `architecture.md:35` 的「CLI 层 2 通道」改为「已弃用」 | 排 → 我只跑只读命令，证据落 `_bmad-output/审查/evidence-cli-probe/` |
| **D-F** | 是否排卡 (b) 退役 `react_agent` 三个 CLI 工具（方案 A）？ | **排**（G-PIPE 处置，消除每次解释 / 评分先空跑一轮） | 保留并修（方案 B）→ 需后端出容器或宿主 shim，属新集成面 |
| **D-G** | 是否排卡 (c) obsidiantools 入/出边分裂修复？ | **排**（正确性小卡） | 不排 → 记入 known-gotchas |
| D-H | 是否单独立卡修正「hook 强制阻断」失实 + 补 Bash 路径级守卫（§10.1 #6）？ | 排（与本议题无关但是真缺口） | 不排 → 至少改 CLAUDE.md 文案 |

### 10.3 与本议题无关但顺带确认的既有缺陷（建议进 known-gotchas 或独立卡）

- `wikilink_context_service._USER_ANNOTATION_KINDS` = `{question, tip, error, hint, note, warning, info}`——缺插件实际写出的 `tips` / `keypoint`，模板 `[!info]` / `[!note]` 反被当用户批注（§4.2）。
- 插件 `parseCalloutsFromContent` 对列表内批注的**缩进续行** `  > ` 不识别 → 该批注整条丢失（§5 实验 2；线上 5 行列表内形态）。
- `backend/lib/agentic_rag/clients/lancedb_client.py:2772` 是第四份 callout 解析器，无列表前缀允许；`%%cb-xxx%%` 标记已被它当正文索引（无注释剥离）。
- 三套 vault 身份并存：`.canvas-config.yaml` `vault_id: canvas_vault` ≠ 文件夹名 `canvas-vault` ≠ obsidian.json hex id `0a302bd176301457`（C12）。

---

## 11. CLI-PROBE-0 实测结果（2026-09-13，用户裁定 D-A 延后、D-E 执行）

### 11.1 前置与方法

- 用户已在 Obsidian 里打开「Command line interface」（`obsidian.json` 出现 `"cli": true`）并打开了 canvas-vault。Obsidian 进程仍从 AppTranslocation 路径运行（重开时用的仍是 DMG 里的 App，不影响探针：socket 相同）。调用二进制 = `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`，`version` 回 `1.13.7 (installer 1.12.7)`。
- 33 条**只读**命令，`vault=0a302bd176301457` 一律首参，cwd=`/private/tmp`（避开「cwd 是 vault 就用它」规则），stdin=/dev/null，40 s alarm，串行、间隔 1 s。每条一份 `_bmad-output/审查/evidence-cli-probe/<name>-<时间戳>.txt`（头 4 行注释 + stdout/stderr + `# elapsed_s=` + 末行 `rc=`）。禁用命令：`eval create delete move rename append prepend property:set plugin:* bookmark theme:* sync:* publish:*`。
- **零写入证明**：`zero-write-before-20260913T124936.txt` 与 `zero-write-after-20260913T125012.txt`（主仓 `git status --porcelain canvas-vault/` + 5 份样本 sha256 + md 计数）去掉首行 diff 为空；跑前跑后 Obsidian 实例数均为 1（无第二实例被拉起）。

### 11.2 结果

| 问题 | 结果 | 证据文件（全名） |
|---|---|---|
| C12 回验 | `vault info=path` = `/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault`；`info=name` = canvas-vault；`info=files` = 178 | `vault-path-20260913T124942.txt`、`vault-name-20260913T124940.txt`、`vault-files-20260913T124943.txt` |
| `backlinks` JSON 结构 | `[{"file": "<vault 相对路径>"}]`；加 `counts` → 多一个 `"count": "4"`（**字符串**，不是数字）；默认 tsv = 每行一路径；`total` = 纯数字 | `backlinks-Fundamentals-json-20260913T124945.txt`、`backlinks-Fundamentals-json-counts-20260913T124946.txt`、`backlinks-Fundamentals-tsv-20260913T124947.txt`、`backlinks-total-20260913T124953.txt` |
| `[[节点/X]]` 与裸 `[[X]]` 是否合并到同一文件 | **合并**。`file=Fundamentals`、`path=节点/Fundamentals.md`、`file=fundamentals`（小写）三者输出逐字相同，且包含只用 `[[节点/Fundamentals]]` 链接的原白板——Obsidian 原生解析做到了 obsidiantools 做不到的事（§4.3 缺陷 2） | `backlinks-Fundamentals-path-json-20260913T124948.txt`、`backlinks-fundamentals-lower-json-20260913T124949.txt` |
| 重名 stem 解析 | vault 内有两份 `lecture 2.md`（`节点/` 与 `raw/…/`），`file=lecture 2` 与 `path=节点/lecture 2.md` 输出相同 → best match 取 `节点/` 下那份 | `backlinks-lecture2-json-counts-20260913T124950.txt`、`backlinks-lecture2-path-json-20260913T124952.txt` |
| frontmatter **嵌套**链接是否计入反链 | **计入**：每个派生节点对 lecture 2 的 count=6 = 4 条 frontmatter（`source_note` / `up` / `derived-from` / **`relationships[0].target`**）+ 2 条正文（awk 分割核对）。关闭 §3.2 里「嵌套 YAML 链接是否索引」的未知项 | 同上 + 主 session 核对 |
| `links` 是否带 `#subpath` | **不带**。输出 = 去重后的解析目标，`节点/lecture 2.md` 里 143 条 `[[lecture 2.mp4#t=…]]` 折成 1 行 `lecture 2.mp4 (unresolved)`；`total`=175 个唯一目标；无 `format=` 参数；LaTeX `[[1,1],[0,1]]` 被当链接 `1,1],[0,1 (unresolved)`。关闭 §10.1 #1 | `links-lecture2-path-20260913T124955.txt`、`links-lecture2-total-20260913T124956.txt`、`links-Fundamentals-20260913T124954.txt` |
| `outline` JSON | `[{"level","heading","line"}]`，`line` **1 基**（与 `grep -n` 一致）；默认 tree 视图 | `outline-board-json-20260913T125001.txt`、`outline-board-tree-20260913T125003.txt`、`outline-Fundamentals-json-20260913T125004.txt` |
| `search` | `search format=json` = 路径字符串数组（无行号）；`search:context` = `path:line: text`（1 基），与 `react_agent._format_cli_results` 的正则一致；`%%cb-` 可作查询词，命中 4 条批注 | `search-json-20260913T125005.txt`、`search-context-20260913T125006.txt`、`search-context-cbmarker-20260913T125007.txt`、`search-json-limit-20260913T125008.txt` |
| C6 验伪锚 | 对不存在文件跑 `backlinks` / `read` → stdout `Error: File "does-not-exist-zzz-2026" not found.`，**rc=0**。三方说法本机证实 | `neg-backlinks-missing-20260913T125009.txt`、`neg-read-missing-20260913T125010.txt` |
| **C12 泄漏实证** | `vault=` 放第 3 参 → 命令**静默由当前聚焦 vault 回答**：本次是 `/Users/Heishing/Desktop/canvas`（注册 id `f8fbba7dda4e945c`，当时 open），结果路径变成 `canvas-learning-system/canvas-vault/…`，并混入**另一个项目**的文件 `deeptutor-vanilla/data/knowledge_bases/测试/raw/特征值与特征向量.md`。跨 vault 泄漏从文档推断升为本机复现 | `neg-vault-misplaced-20260913T125011.txt` |
| vault 级图 | `unresolved` 1607 条（含 `raw/` 里 README 的 `./docs/…` 相对链接、LaTeX 碎片、时间戳 `01:19`）；`orphans` 121；`deadends` 124（含 `backups/*.bak`、`CLAUDE.md`）——对 CLS 无直接用途，噪音大 | `unresolved-json-20260913T124957.txt`、`unresolved-counts-20260913T124958.txt`、`orphans-20260913T124959.txt`、`deadends-20260913T125000.txt` |
| 延迟 | 33 条 mean **0.030 s**，max 0.038 s。三方指南「~1 s/命令」在本机 1.13.7 核心上**不成立**（1.12.7 changelog：「made Obsidian CLI even faster」）；§3.4 该行按此修正 | 各文件 `# elapsed_s=` 行 |

### 11.3 对裁决的影响

- **不改变「收益不明显」**：探针证实 CLI 给的仍是文件级图，`links` 连子路径都不保留；线上子文件粒度的边仍为 0。
- **修正两条口径**：① 延迟成本从「~1 s」下调为 0.03 s，串行图遍历对 14 节点 vault 是毫秒级；② Obsidian 原生解析把 `[[节点/X]]`、裸 `[[X]]`、大小写、frontmatter 嵌套链接全部合并到同一文件——卡 (c) 修 obsidiantools 时应以 CLI 的 `backlinks … counts` 输出为**基准真值**（`backlinks-Fundamentals-json-counts-…`、`backlinks-lecture2-json-counts-…` 可直接当 fixture 期望值）。
- **C12 升级**：任何 CLI 调用必须 `vault=<obsidian.json hex id>` 首参 + 调用前 `vault info=path` 回验；本机大 vault `Desktop/canvas` 常开，放错一次就把另一个项目的文件混进来。
- **本卡未证明**：任何用户可感知收益；子文件粒度的边；容器后端可用性（C5 已判不可达）；`eval` 通道（未跑）。

---

## 附 A. 一手来源清单（节选，全量 152 条见调研 digest）

- obsidian.md/help/links · obsidian.md/help/cli · obsidian.md/help/plugins/backlinks · obsidian.md/help/plugins/outgoing-links · obsidian.md/help/uri · obsidian.md/help/obsidian-flavored-markdown
- docs.obsidian.md：MetadataCache/resolvedLinks · CachedMetadata · parseLinktext · resolveSubpath · BlockCache · HeadingCache · getFirstLinkpathDest；本地 `frontend/obsidian-plugin/node_modules/obsidian/obsidian.d.ts`（1.12.3）
- changelog：0.9.5 / 0.9.6 / 0.12.14 / 0.12.19 / 0.14.13 / 0.14.14 / 1.4.5 / 1.8.1 / 1.12.0 / 1.12.4 / 1.12.7 / 1.13.4
- forum.obsidian.md：98676 · 72455 · 81962 · 77682 · 66586 · 83195 · 79035 · 7669 · 93311 · 45658 · 9108 · 111399 · 97060 · 52803 · 101505 · 18545 · 38014 · 81638 · 45314 · 112242 · 112217 · 113902 · 113099 · 111419 · 112486 · 113399 · 52331 · 75146 · 61645 · 674
- github.com/kepano/obsidian-skills（obsidian-cli / obsidian-markdown SKILL.md）· dsebastien.net CLI 完整指南（2026-07-25，三方）· jackal092927/obsidian-official-cli-skills（三方实测）
- 插件源码：dataview（index.ts / markdown.ts / value.ts）· breadcrumbs（utils/obsidian.ts）· excalibrain（graph/Pages.ts）· copy-block-link（main.ts）· obsidian-spaced-repetition（data-storage 文档 + issue 1182 / PR 1577）· obsidian-spaced-repetition-recall README · Obsidian_to_Anki wiki · yanki README · flashcards-obsidian README · obsidian-zotero-integration Templating.md · obsidian-zotlit（issue 109 / discussion 175）· readwise changelog · obsidian-kindle-plugin discussion 27 · obsidian-block-link-plus · obsidian-block-reference-enhancer · logseq/docs Markdown.md · logseq issue 7362
- 学术：claude.com/blog/introducing-citations-api · platform.claude.com/docs/…/citations · anthropic.com/news/contextual-retrieval · arXiv 2304.09848 · arXiv 2305.14627 · arXiv 2509.20859 · Karpicke & Blunt 2011 Science（Purdue PDF）· Karpicke 2017（ERIC ED599273）· Ponce, Mayer & Méndez 2022 Educ Psychol Rev · CiteRead IUI 2022（DOI 10.1145/3490099.3511162）· Zellweger et al. CHI 2000（DOI 10.1145/332040.332440）· Niederhauser et al. 2000（DOI 10.2190/81bg-rpdj-9fa0-q7pa）· Nelson 1990 / 1999 · web.hypothes.is/blog/fuzzy-anchoring · w3.org/TR/annotation-model · stephango.com/file-over-app
