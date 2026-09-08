# CARD-G2-7a (b) — 部署清单逐项裁定表

> 树 `card-u3-deploy` @ U3-A 末 commit `086771d3`。live 只读。
> 裁定档位：**copy**（新增到脚本数组 + manifest copy）/ **generate**（按 vault 生成）/
> **optional**（声明但允许缺失，进 optional-missing 不计 rc）/ **retire**（不部署）/ **allow**（进 extra_allow）。

## 〇 分母是怎么算出来的（不是照抄卡文表）

卡文 (b) 明确要求「开工先跑 `git ls-files` + live `ls` 的并集逐项对照，本表初稿就漏过
`themes/Underwater/**`，出现本表没有的项**先补行再往下走**」。照做了，用**确定性集合运算**而非人工浏览：

| 步骤 | 判据 | 结果 |
|---|---|---|
| 脚本五数组展开 | 按各自前缀拼成完整路径集 | 27 项 |
| manifest 条目 | `action` 分组 | 38 条（declared 28 / exclude 10） |
| git 追踪 vault 文件 | `git -c core.quotepath=false ls-files -z canvas-vault` | **66** |
| live 并集 | `.obsidian` / `.claude` / `.obsidian/plugins` / 根级点文件 只读 `ls` | — |
| 差集 | 追踪文件 − (manifest 覆盖 ∪ 脚本数组 ∪ 卡文已裁 ∪ 主 session 已发现) | **5 项未裁** |

> ⚠️ **审计脚本 v1 自己有缺陷**：用 `.split()` 切 `git ls-files` 输出，
> `原白板/CS 61B.md` 与 `原白板/递归与分治 (Recursion & Divide-Conquer).md` 两个**含空格的路径被切碎**，
> 报出 3 个空条目、把 66 报成 70。v2 改 `-z` + `split("\0")` 才对。
> **判据坏了结论就不能信** —— 存档 `completeness-audit.txt`（v1，留着看错在哪）与 `completeness-audit-v2.txt`。

## 一 卡文原表 16 行（照裁，不复述依据）

| 项 | 裁定 |
|---|---|
| 根级 `.mcp.json` | **copy**（新增 `ROOT_FILES`；Claude Code CLI 唯一 MCP 注册件，http/8011） |
| `.claude/mcp.json` | **retire**（sse + `_claudian`；后端只 `mount_http()`，实测 `server.py:145` 无 `mount_sse` ⇒ 对后端是死配置） |
| `.obsidian/cls-internal-key.txt` | **retire 复制 → generate + optional**（E-3 各 vault 各 key；`:123` 自检反向判） |
| `.claude/settings.local.json` | **generate + optional**（键名**已核到**，见 §三） |
| `plugins/canvas-learning-system/data.json` | **generate + optional**（4 键，live 实测 `activeVaultName/backendUrl/internalApiKey/nodePathPrefixes`） |
| `.obsidian/templates/{concept,exam-board}.md` | **copy ×2**（git 追踪却不在任何清单） |
| `plugins/templater-obsidian/data.json` | **generate + optional**（只写 `templates_folder`；live 该文件 17 键，值不抄） |
| `.obsidian/{app,appearance,core-plugins}.json` | **optional**（Obsidian 首次打开自建） |
| `plugins/claudian` | **retire** |
| `plugins/{dataview,breadcrumbs,templater-obsidian}` | **optional** |
| `plugins/canvas-learning-system/main.js` | 目录条不变；`:121` cmp 改为「源有则比、源无则 ❌ 提示先 build」 |
| `.claude/{agents,commands}` | **optional** |
| `graph.json` / `types.json` / `.claude/cache` / `excalibrain` / `obsidian-excalidraw-plugin` | **allow**（`extra_allow` 5 项逐字列，不用 glob——会与 declared 重叠触发 ManifestError） |
| `.obsidian/themes/Underwater/{manifest.json,theme.css}` | **copy ×2** |
| `Dashboard.md` | 不动（已在清单，决策页 §零 ③ 与实测不符，验收单更正） |

## 二 ⛔ 本卡新补的行（卡文表没有）

### 2.1 主 session 开工时发现的 3 项

| 项 | 今天来源 | 裁定 | 依据 | 落到哪 |
|---|---|---|---|---|
| `.claudian/**`（**8 个 git 追踪文件**：`claudian-settings.json` + 7 个 `sessions/*.meta.json`） | git 树 + live | **retire**（manifest 加 `exclude` 条） | ① Claudian 已弃（决策页前提 ②）；② 内容是**上一个 vault 的会话历史**，复制进新库 = Y9-A 转 G2-7 ① 要停的行为；③ 不在任何 `extra_scan` 覆盖面 ⇒ **今天漏了也不会有门报警** | manifest 新增 exclude |
| `.quarantine/**` | 仅 live（未追踪） | **retire**（exclude + 登记） | 运维隔离区（含 `UAT-2.5.X-test.md`），非系统件 | manifest 新增 exclude |
| `.trash/**` | 仅 live（`.gitignore:218`） | **retire**（exclude + 登记） | Obsidian 用户删除区 | manifest 新增 exclude |

### 2.2 ⛔⛔ 交叉真相源找出的**真部署缺口**（本表最重要的一行）

| 项 | 裁定 | 依据 |
|---|---|---|
| `wiki/concepts` / `wiki/canvases` | **新增 skeleton ×2** | 见下 |
| `outputs/exam_boards` | **⛔ 登记，本卡不加** —— 与既有 `outputs/**` exclude **冲突** | 见下方 ⚠️ |

**后端有第二份「新 vault 需要什么」的定义**：`backend/app/services/vault_init_service.py:19-24`
的 `VAULT_DIRECTORIES = ["raw", "wiki/concepts", "wiki/canvases", "outputs/exam_boards"]`。

两个来源的集合差（实测）：

| 来源 | 建哪些目录 |
|---|---|
| `vault_init_service.VAULT_DIRECTORIES` | `raw` / `wiki/concepts` / `wiki/canvases` / `outputs/exam_boards` |
| `install-vault.sh SKELETON_DIRS` | `原白板` / `检验白板` / `节点` / `outputs` / `raw` / `templates` |
| **⛔ 后端建、脚本不建** | **`wiki/concepts`、`wiki/canvases`、`outputs/exam_boards`** |
| ⚠️ 脚本建、后端不建 | `原白板`、`检验白板`、`节点`、`outputs`、`templates`（登记，见 §四） |

**它是活的，不是死管道**（三条独立证据）：
1. `backend/app/api/v1/system.py:464` `from app.services.vault_init_service import VaultInitService` —— 有 API 端点在用；
2. 有自己的测试套件 `backend/tests/unit/test_vault_init_service.py`（**正是本卡邻近套件裁判里那一个**）；
3. skills 与 MCP 工具都引用这些路径：`ai-linked-doc/SKILL.md:343`、`configure-whiteboard/SKILL.md:322`
   的映射表写 `wiki/concepts/` → `节点/`；`backend/app/mcp/tools/wikilink_tools.py:18,39` 的
   参数说明举例 `wiki/concepts/decision-tree.md`。

树与 live **都有**这三个目录（`wiki/canvases` live 有 3 个条目），只有**新部署的 vault 会缺**。
`SKELETON_DIRS` 的循环是 `mkdir -p "$TARGET/$d"`（`:84`），**嵌套路径安全**，可以直接加。

> **这条缺口是怎么找到的**：不是靠再扫一遍文件（`wiki/*/.gitkeep` 看起来就是个占位符），
> 而是问「**谁还定义了同一件事**」。文件清扫找不到语义缺口，交叉真相源可以。

### ⚠️ `outputs/exam_boards` 为什么本卡不加（初稿写的是「新增 skeleton ×3」，实测后缩范围）

加进去之后**每一条既有测试都多出一个 findings**：`outputs/exam_boards` 同时被
新增的 skeleton 声明**和**既有的 `outputs/**` exclude 命中 ⇒ 每次跑都多一条
`intentionally-excluded: outputs/** — 目标里存在: outputs/exam_boards`。
20 条既有门因此变红（实测）。

两条出路，都不好：

| 出路 | 代价 |
|---|---|
| 把 `outputs/**` 改成 `kind: "nondir"`（只排除文件、不排除目录） | **悄悄改变 intentionally-excluded 的报告面** —— outputs 下其它嵌套目录从此不再被报，而它们也不在 `extra_scan` 覆盖面内 ⇒ 变成新的无声盲区。为塞进一个新条目去动一条既有语义，代价不对等 |
| 只加进脚本数组、不进 manifest | 集合等价门（双向差集）必红 |

⇒ **本卡缩范围：只加 `wiki/concepts` 与 `wiki/canvases`（无冲突），`outputs/exam_boards` 登记转下一张卡。**
影响面评估：`outputs` 骨架目录本身**会**被创建，消费方 `mkdir -p outputs/exam_boards` 即可；
`configure-whiteboard/SKILL.md:323` 显示它在当前设计里确实有用途（只放输出、不放白板本身），
所以这条缺口**是真的**，只是修它需要先想清楚 `outputs/**` 的类型语义 —— **那个冲突本身就是下一张卡需要的信息**。

### 2.3 vault 根级 3 个 `.md`

| 项 | 今天来源 | 裁定 | 依据 |
|---|---|---|---|
| `2111.md`（266B，线性代数片段）/ `Untitled.md`（538B，Obsidian 默认新建）/ `未命名.md`（29KB，转学规划报告） | git 树 + live | **登记，不加 manifest 条目** | 都是**用户学习内容/临时件**，不是系统件。`ROOT_FILES=(CLAUDE.md Dashboard.md)` ⇒ **今天本就不会被部署**，行为无需改动 |

> **为什么不加 `exclude` 条目**（初稿写的是「加一条 exclude 把语义写下来」，实测后改口径）：
> - 逐个列 `2111.md` / `未命名.md` = 把**用户内容的文件名**写进部署清单，抽象层次错了，
>   而且下次用户新建一个临时笔记它又漏了；
> - 用 glob `*.md` 则会**连带命中已声明的 `CLAUDE.md` 与 `Dashboard.md`** ——
>   `ExcludeMatcher.hits_for("*.md")` 会把这两个系统件报成 intentionally-excluded，是错的；
>   而 exclude 的模式**没有「except」写法**。
> ⇒ 正确处置是**登记这个盲区**（vault 根级不在 `extra_scan` 覆盖面内，多出来的 `.md` 不会被报），
>   而不是硬塞一条会制造新错误的条目。覆盖面本身是否该扩，归下一张卡。

## 三 `.claude/settings.local.json` 的键名分支裁定

卡文把这条写成条件分支：键名核到 ⇒ `generate + optional`（generate 计数 5、optional-missing 12）；
核不到 ⇒ `exclude`（4 / 11）。⛔ 卡文同时禁止降级为 `copy`。

**实测：核到了**，三个独立来源互证 ——

1. `claude --version` = **2.1.263 (Claude Code)**；
2. 仓根 `.claude/settings.local.json` 顶层键含 `enabledMcpjsonServers` / `enableAllProjectMcpServers` / `permissions.allow`；
3. **live vault 的 `.claude/settings.local.json` 恰好只有一个键 `enabledMcpjsonServers`** —— 最直接的生产形态证据。

服务器名 `canvas-learning-mcp`（树内与 live 的 `.mcp.json` 一致）。
⇒ 生成的最小件 = `{"enabledMcpjsonServers": ["canvas-learning-mcp"]}`。

⚠️ **不抄 live 的值**：live 那 5 个条目里有 4 个是用户全局开发用 MCP
（`sequential-thinking` / `context7` / `codebase-memory` / `graphiti-canvas`），复制进新库正是要停的行为。

⇒ **落在「核到」态：generate 计数 = 5，(g)⑥ / 裁判 7 的 optional-missing 预期 = 12 项。**

> 为什么卡文禁止降级为 `copy`：`copy` 会**同时**踩两个坑 —— 既让
> `test_manifest_matches_install_arrays` 的双向差集必红（(e) 无条件把它从 `CLAUDE_ITEMS` 删掉），
> 又会把上一个 vault 的私有批准清单复制进新库。**一个看似最保守的选择，同时违反两条不同约束。**

## 四 本表未裁 = 0 的对账

- 追踪文件 66 个，逐个过「manifest 覆盖 ∪ 脚本数组 ∪ 本表」三重判据后，**未裁 = 0**。
- 卡文原表 16 行 + 本卡新补 2.1 的 3 行 + 2.2 的 3 项（合 1 行）+ 2.3 的 1 行 = **21 行**。
- **登记不改行为**的项（写下来但不动代码）：
  - `install-vault.sh` 建而 `vault_init_service` 不建的 5 个目录（`原白板`/`检验白板`/`节点`/`outputs`/`templates`）——
    这是两个真相源的**另一个方向**的差。它们是中文白板体系（较新），`vault_init_service` 的
    `CLAUDE_MD_SKELETON` 里还写着 Claudian 与 quickadd/meta-bind（较旧）⇒ 后端那份骨架定义**本身可能已过时**。
    **本卡不改 `backend/app`（硬边界）**，只登记：两份骨架定义需要一次统一，归下一张卡。
  - `.obsidian/*.json` 覆盖面看不见非 json 件（UAT-CARD-G2-6 #18）——覆盖面本身不改。
