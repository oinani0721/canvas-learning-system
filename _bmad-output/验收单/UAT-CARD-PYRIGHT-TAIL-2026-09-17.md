# UAT — CARD-PYRIGHT-TAIL（pyright TAIL 存量逐条 census + 只改注释·死配置·冗余 ignore）

> 批次：`[BATCH-2026-09-11-第十四批 / CARD-PYRIGHT-TAIL]`　车道：`card-t8-tools`（分支 `card/t8-tools`，本车道第 6/7 张，串在 T8-E 之后、T8-G 之前）
> `BASE_F` = `f493a4e170a88b5eb2c4af05b275055d005adfe9`（= 前一卡 T8-E `CARD-TOOLCHAIN-UNIFY` 末 commit）
> 本卡 commit：`d1c40998`（代码 + census）→ `bcd487db`（纯 `_bmad-output` 证据追加）
> 主交付：`_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md`
> 证据目录：`_bmad-output/审查/evidence-pyright-tail/`
> **未 push。**

---

## 〇 第 0 分钟自证

| 项 | 期望 | 实测 |
|---|---|---|
| `pwd` | `…/worktrees/card-t8-tools` | ✅ 一致 |
| 分支 | `card/t8-tools` | ✅ |
| `HEAD`（记为 `BASE_F`） | 前一卡 T8-E 末 commit | ✅ `f493a4e1 docs(toolchain): 回填收官绑定核 [… / CARD-TOOLCHAIN-UNIFY]`（`grep -F 'CARD-TOOLCHAIN-UNIFY'` rc=0） |
| `git status --porcelain` | 空 | ✅ 空（前卡已独立 commit 且干净） |
| `test -x <card-v5-lance>/backend/.venv/bin/pyright` | 可执行 | ✅ `pyright 1.1.411` |
| `backend/.venv/bin/pytest` / `backend/.env` | 在 | ✅ 两者都在 |
| 基线（**R-B14-2 唯一口径** `grep -vc '^#'`） | **64** | ✅ **64** |

### 〇.1 卡文 §〇 逐条 file:line 复核 —— **零漂移**

`pyrightconfig.json` include 的 `src` 在 `:4`、旧注释 `:48`；`git ls-files src` = 0；`dependencies.py` ignore 在 `:1035`、陈旧注释块 `:1031-1033`；`review_service.py` 两处「生产零调用方」在 `:1240` / `:2135`；`canvas_service.py` 「落地路径逐字不变」在 `:341`；`exam_service.py` 「模块顶层的猴子补丁挂载」在 `:80`；`exam_service_ext.py` def `:932` / 赋值 `:956-966` / 调用 `:970`。**全部与卡文 §〇 实测值逐字一致，无一处需写「卡文 :X → 实测 :Y」。**

---

## 一 本卡改了什么（地盘 = 恰 5 文件，12 增 13 删）

```
 backend/app/dependencies.py            | 5 +----
 backend/app/services/canvas_service.py | 2 +-
 backend/app/services/exam_service.py   | 9 ++++++---
 backend/app/services/review_service.py | 6 +++---
 pyrightconfig.json                     | 3 +--
 5 files changed, 12 insertions(+), 13 deletions(-)
```

1. **死配置**：`pyrightconfig.json` 的 `include` 删掉 `src` 条目（`git ls-files src` = 0，它匹配 0 个文件 ⇒ 分析面不变）；`:48` 旧注释「本卡只登记不改」改为「已清除」，且**新注释里不再逐字带引号写该目录名**——否则全文件判据恒 ≥1、后绿作废。
2. **冗余 ignore**：`dependencies.py` 原 `:1035` 行尾的 `# pyright: ignore[reportArgumentType]` 已被 pyright 自己标成 `reportUnnecessaryTypeIgnoreComment`（U1 把 `canvas_service.py:69` 改成 `Optional[str] = None` 之后它就不再承重），删；连同 `:1031-1033` 那段自己写着「阶段 2 复核时清理」的注释块一并删（那件事就是本卡在做）。
3. **注释措辞三处**（U1 §二十.2 M-2 / L-1 + U2 r3 L1）：
   - `review_service.py:1240` / `:2135-2136`：「生产零调用方 / 传递性零曝光」→「未发现直接生产调用(grep + AST 口径), 动态可达性未证」/「传递性曝光面同样未证(不等于零曝光)」。
   - `canvas_service.py:341`：「落地路径逐字不变」→「走同一 fallback 分支; 但 assert 无消息 ⇒ `f"...: {e}"` 的原因文本会变空, 非逐字不变(生产不可达, 仅影响日志文本)」。
   - `exam_service.py:80-82`：「由 exam_service_ext.py **模块顶层的**猴子补丁挂载」→ 赋值在 `attach_to_exam_service()` **函数体内**（`:956-966`，def `:932`），由该模块顶层 `:970` 的调用执行；并附一行 D-29 crossover 说明。
4. **census**：`_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md`，四档处置逐条可判。

### 一.1 ⛔ 一个刻意的设计：两个文件**逐行等量替换**

`canvas_service.py` 与 `review_service.py` 的 `numstat` 是 `1 1` 与 `3 3` —— **行数一个不增不减**。这不是巧合：这两个文件的行号被**别处的注释引用着**，而引用方 `question_generator.py:208`（引 `canvas_service.py` 的行号）**不在本卡地盘**，本卡改不了它。若本卡顺手把注释重排成更好看的换行，就会让一份自己无权修的文件里的引用**当场失实**。收工复核：`read_canvas` 仍在 `:620`、`asyncio.Semaphore` 仍在 `:567`（实测）。

`exam_service.py` 则**有意**接受 +3 行（挂载点说明要写准必须多两行、D-29 一行）——代价是文件末尾的副作用 `import` 由 `:556` 移到 **`:559`**，如实登记（全仓 tracked 文件里**没有任何代码/测试**引用 `exam_service.py:NNN`，唯一引用它行号的是 PRD `:1917` 的 `:69-83`，而那条**在本卡动手前就已失实**——`:69-83` 现在是类文档串 + `TYPE_CHECKING` 块，不是 PRD 说的 `create_session`）。

---

## 四-A 🤖 Claude 已代验（证据全在 `_bmad-output/审查/evidence-pyright-tail/`）

### 四-A.1 常驻硬门：pyright `app` 改前 / 改后

| 时点 | 汇总行 | 存档 |
|---|---|---|
| 改前 (b) | **`0 errors, 81 warnings, 0 informations`** | `pyright-app-before-20260917T135402.txt` |
| 改后 (k) | **`0 errors, 80 warnings, 0 informations`** | `pyright-app-after-20260917T135717.txt` |

差额恰 **1 warning** = 被清掉的那条冗余 ignore。跑法固定 `( cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' )`（R-B14-10 的 cwd 要求 + 子 shell 不漏 `cd`），**⛔ 不用 `| tail -1`**——pyright 1.1.411 的末行是 `v1.1.411 -> v1.1.414` 升级提示，位置锚会取到它。
**验伪锚**：`P2=/nonexistent/pyright; test -x "$P2"` → rc=1，证明「pyright 缺席时守卫会喊停」，不是静默给 0。

### 四-A.2 先红后绿逐条回执

| 判据 | 改前 | 改后 | 验伪锚 |
|---|---|---|---|
| `dependencies.py` 的 `reportUnnecessaryTypeIgnoreComment` 计数 | **1**（原文 `:1035:63 - warning: Unnecessary "# pyright: ignore" rule: "reportArgumentType"`） | **0** | 同跑打印原文诊断行，非空 |
| `pyrightconfig.json` 全文件带引号的目录名计数 | **2**（`:4` include 条目 + `:48` 旧注释里逐字引用） | **0** | `grep -cF '"backend/app"'` = **1**（证 `grep -cF` 对带引号项真能命中） |
| 同上 **include 面**（承重，对行号漂移免疫） | **1** | **0** | 同上 |
| `review_service.py` 旧串「生产零调用方」 | **2** | **0** | 新串「未发现直接生产调用」= **2** |
| `canvas_service.py` 旧串「落地路径逐字不变」 | **1** | **0** | 新串「非逐字不变」= **1** |
| `exam_service.py` 旧串「模块顶层的猴子补丁挂载」 | **1** | **0** | `grep -cF 'structlog'` = **2→3**（证 grep 非恒 0）；新串 `attach_to_exam_service()` = **2** |

### 四-A.3 地盘门 (i) + R-B14-4 附加约束自证

- `git --no-pager diff --stat --no-color "$BASE_F" HEAD -- . ':(exclude)_bmad-output'` → **恰 5 个文件**（`--name-only` 复核同样 5 行）。
- **不碰 T8-A~E 邻块**：`lefthook.yml` / `mutation_kill_identity.py` / 四套 `g32*`·`g33` harness / `lifespan_isolation_negative_control.py` / `package.json` / `package-lock.json` / `ruff.toml` 的 diff = **0 行**；同命令换成本卡确改的 `pyrightconfig.json` = **21 行**（证命令能出输出）。
- **⛔ R-B14-4「只准增删 ignore 注解与注释行，禁改任何语义行」**：`diff -U0` 的非注释 `+`/`-` 行 **恰 2 行**，且就是同一处 `canvas_base_path=canvas_base_path,`（`-` 带行尾 ignore / `+` 不带，代码本体逐字相同）。验伪锚：去掉最后一级 `grep -v` 得 **22** 行（证 `^[-+][^-+]` 真能命中）。

### 四-A.4 census-only 零改动自证 (g)

`git diff --name-only "$BASE_F" HEAD -- 'backend/app/*.py'` → **恰 4 行**。census 里被判「只登记 / 第十五批 / 本批其他卡」的 12 个文件 + `endpoints/review.py` **命中数全 0**（逐个列在 `g-census-only-*.txt`）；验伪锚 `canvas_service.py` = 1。
⛔ pathspec 必须写 `'backend/app/*.py'`：git 的 `*` 跨 `/`，而 `'backend/app/**/*.py'` 对**顶层** `backend/app/*.py` 覆盖为 **0**（同跑实测），用 `**/` 写法 `dependencies.py` 与明令禁改的 `main.py` 都永远不会出现在结果里。

### 四-A.5 新增 error 自清 负控 (h) —— 证明这道门不是恒 0 的假门

| 步骤 | 实测 |
|---|---|
| 起点 `git status --porcelain -uno` | **0** |
| 注入前 `shasum -a 256 dependencies.py` | `f0c21654ac7a…fc49` |
| 注入一条返回类型不匹配的函数后 `pyright app` | **`1 error, 81 warnings`** ✅ 门真能抓到新增 error |
| 还原（`git show HEAD:<file> > tmp && cp`，⛔ 禁 `git checkout` / `git stash`） | — |
| 还原后 shasum | `f0c21654ac7a…fc49` **逐字相同** ✅ |
| 还原后 `pyright app` | **`0 errors, 80 warnings`** ✅ |
| 还原后 `git status --porcelain -uno` | **0** ✅ |

注入期间挂了 `trap ... EXIT` 兜底还原，保证即便中途失败也不会把探针留在树上。

### 四-A.6 `tests/unit` 目录级 (j) —— 与基线**逐条相同**

`( cd backend && … pytest tests/unit -q -p no:cacheprovider --ignore tests/unit/test_deploy_vault_sh.py )`（⛔ `--ignore` 用**相对路径**，R-B14-3；写成 `backend/tests/unit/…` 会匹配不到任何被收集文件 = 空操作，那份重型文件仍会真跑）。
结果 `35 failed, 5161 passed, 48 skipped, 23 xfailed, 29 errors`，nodeid 口径 **64 条**，与基线 64 条 `diff` **完全为空**（既无 `>` 也无 `<`）⇒ 本卡零新红、零修复。承重那一跑的文件名固定成变量 `RUN`，**没有**用 `unit-close-*.txt` 这种 glob（≥2 份会给每行加文件名前缀、把 diff 变成全假阻断）。

### 四-A.7 ruff (step 11)

`files=4`（恰本卡 4 个 `.py`）→ `All checks passed!` rc=0。
**⛔ 验伪锚被本卡换掉了**：卡文写「喂一个已知含 F401 的文件必 rc=1」，但 `backend/ruff.toml` 的 `select` 只有 `["E9","F63","F7","F82"]` ⇒ **F401 在本仓根本不启用**，该锚**恒不触发 = 假锚**。实测：F401 探针 rc=**0**、F821 探针 rc=**1**（`F821 Undefined name`）⇒ 改用 **F821** 作锚。

### 四-A.8 ⛔ 如实登记：卡文的一条验伪锚**结构上恒 0**，已定位根因并更正

卡文 (i) 写「验伪锚：去掉 exclude 的同命令应多出 `_bmad-output/` 路径」。**首跑得 0**。本卡没有把它当绿放过去，而是查了根因：

> `git diff --stat` 会把**过长路径的首段缩写成 `.../`**——`_bmad-output/审查/…` 在输出里变成 `.../2026-09-13-PYRIGHT-TAIL-census.md`，`_bmad-output/` 这个字面量**根本不出现**。所以该锚在本仓**永远是 0**，那不是「没多出路径」。

（顺带排除了另一个更常见的嫌疑：不是中文路径的 `core.quotepath` 转义——`--name-only` 下路径确实被转义成 `"_bmad-output/\345\256\241…"`，但 `_bmad-output/` 前缀是 ASCII、照样能被命中。）

**更正后**：改用 `--name-only`（不缩写）→ 带 exclude = **0**、去掉 exclude = **13**；`--stat=300` 同样 = **13**。锚这才真的在测它声称要测的东西。
同跑还实测了协议 §1 点名的错误写法：`':!_bmad-output'` 在本机 `git 2.50.1 (Apple Git-155)` 下 **rc=128**、stdout 空——若拿它当判据，「为空即绑定」就会把「没跑成」读成绿。

### 四-A.9 `python-lint` 的豁免有据，`python-typecheck` **零豁免**

首次 `git commit` 被 `python-lint` 的 `ruff format --check` 拦下（`python-typecheck` 同一跑里 **exit 0 通过**）。按协议 §2.3 过渡条款取证后，**仅**豁免 `python-lint`：

- **比区间不相交之外，本卡给了更强的证据**：把 `BASE_F` 版文件喂进 `ruff format --check --stdin-filename`，`dependencies.py` rc=**1**、`exam_service.py` rc=**1**、`canvas_service.py` rc=**0**、`review_service.py` rc=**0** —— 与**工作树态逐文件相同** ⇒ 漂移集在本卡动手前就是这两个文件，**不是本卡引入**。
- ⚠️ 这里也差点被假绿骗到：stdin 模式**不打印** `1 file already formatted`，首跑四个文件输出**全是空串**。空输出不能读成「无漂移」——改用 `rc` 当判据，并配「明知未格式化的输入必须 rc=1 / 已格式化必须 rc=0」的验伪锚才站得住。
- 卡文要求的区间不相交也做了，且是**机械判**不是肉眼：`dependencies.py` 漂移 14 段 vs 本卡 2 段 `[(1031,1033),(1035,1035)]`（最近的漂移段是 `(1017,1025)` 与 `(1041,1049)`）；`exam_service.py` 漂移 8 段（最小 `(185,193)`）vs 本卡 1 段 `[(80,82)]`。脚本内含「构造一对必然相交的对照必须判 True」的验伪锚，排除相交检测恒假。
- 工作树形 `git diff -U0 "$BASE_F" -- <文件>`（⛔ **不带 HEAD**）——此刻 commit 尚未落地、`HEAD == BASE_F`，带 HEAD 会恒空 = 「漂移不在改动行」恒真的假绿。同跑打印了 `HEAD == BASE_F` 的相等自证。

---

## 四-B 👤 你来验（2 分钟，只读这一段）

打开项目，翻到 `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md`。

那份一直挂在那里、谁也说不清还剩多少的「待清理」清单，现在被逐条点清了：哪几条这一轮顺手就清掉了、哪几条已经交给同一批里的别人、哪几条要留到下一轮单独开一张单子、哪几条是**明知如此但就该这样**（属于类型系统的既定例外，不是欠账）——每一条都写明白了，也写清了它到底有没有人在用、有没有测试盯着。

还有两条是这一轮**新翻出来**的：一条是同一个文件里另一处说法不准的注释，一条是注释里那些「见某文件第几行」的指路牌**整批指错了地方**（合并一次就集体失准，而且没有任何自动检查会发现）。它们没有被顺手改掉——因为这一轮的授权范围里没有它们——但都白纸黑字记下来了，谁也不会当没看见。

**你该有的感觉**：心里有数、不再担心它悄悄变坏。这份清单从「一团说不清的欠账」变成了「一张每条都知道归谁、什么时候还」的账。

---

## 五 本卡未证明什么

1. **未证明**被判「第十五批立卡」的 T1 / T3 / T14 / T-new-1·2·3·5·6·7·8 的**具体修法正确**——本卡只登记处置，这些文件一行没改。
2. **未重测 T11**（`backend/tests` + 仓根 `tests/` 的 pyright 存量），沿用 U2 §五 的登记口径；本批**没有跑** `"$P" tests`。
3. ~~未证明删掉 ignore 后在其他 `include` 面没有连带新 error~~ —— **Codex round-1 之后已实测关闭（限 include 面）**：全 include 面 305 文件上，BASE_F 版 `165 errors, 82 warnings` vs 本卡版 `165 errors, 81 warnings`，**errors 一条未增**（四-A.10）。⛔ **仍未证明** `backend/tests`（509 个 `.py`）—— 实测它**根本不在 `pyrightconfig.json` 的 include 面内**（`include` 的 `tests` 相对仓根解析 = 仓根 `tests/` 41 个文件，`305 − 264 = 41` 恰好对上），这一面本卡既没测、也不在该配置覆盖范围。
4. **未证明** `exam_service.py` 的 `if TYPE_CHECKING` 块内 11 个方法声明与 `exam_service_ext.py` 的真实 `def` **逐字签名一致**——那是 U1 面，本卡只改了挂载点的措辞。
5. census 的「生产调用方 = 0」基于 **grep + AST 口径**，**覆盖不到**别名取用 / 回调注册 / 字符串反射 / 路由注入这些动态可达路径 ⇒ 只能说「未发现直接生产调用」，**不能说「零曝光」**（这也正是本卡改注释措辞的原因）。
6. **未证明**「测试覆盖」那一列的命中数 = **真覆盖到缺陷行**：`generate_verification_canvas` 在 `backend/tests` 的 15 处命中全是 mock 用例，是否真执行到会崩的那一行未逐条验。
7. **未证明** `pyrightconfig.json` 的 `exclude` / `extraPaths` / 各 `report*` 键里**没有别的死枝**——本卡只清了 `include` 的一处，其余配置面未逐键复核。
8. **未证明** F-6（`multimodal_service.py` 的 Pillow 说法）的更正**对任何读者已生效**——那条错误在 commit message 里，commit message 不可变，本卡只能在 census 登记事实。

---

## 六 台账待登记条目

1. **本卡 commit**：`d1c40998`（代码 + census，5 文件 12 增 13 删）+ `bcd487db`（纯 `_bmad-output` 证据追加）。census 路径 `_bmad-output/审查/2026-09-13-PYRIGHT-TAIL-census.md`。**未 push。**
2. **地盘扩充落账**：裁定 **R-B14-4** 已把 `dependencies.py` / `review_service.py` / `canvas_service.py` / `exam_service.py` / `exam_service_ext.py` 增列进 T8-F 地盘（约束「只准增删 ignore 注解与注释行」）。本卡**实改其中 4 个**，`exam_service_ext.py` **获批但未动**。⚠️ 设计稿 §3 正文**仍是旧清单**（只有手册 §一 已同步）——请主 session 回写设计稿。
3. **第十五批立卡候选**（逐条见 census §四）：T1 rollback 退役裁定 / T3 review 死码 / T-new-1·2·3·5·6 行为变化 / **T-new-7 `learning_context_service.py:205` 活路径（优先级最高：`exam_quick.py:116` 端点在用，该数据源从未供过数据）** / T-new-8 multimodal 向量搜索退役 / T14 provider_factory OPENAI 字段产品裁定。
4. **只登记的类型例外**：T6 `exception_handlers.py:309-311` cast / T8 `neo4j_client.py:616` cast / T10 lib 侧 `extraPaths`；**T11**（`backend/tests` 1350 错 / 仓根 `tests/` 168 错）沿用 U2 口径、**本批未重测**。
5. **U1 §十六.2 三条方法论回写**已在本卡落地（弃用 `PHASE0_PENDING` 启发式 / 禁 `| tail -1` 改结构锚 / 「死路径」拆「生产调用方」「测试覆盖」两列）——**协议层回写**（写进 `card-batch-protocol.md`）不在本卡面，归 **T8-G / 第十五批**。
6. **⛔ 卡文判据缺陷两条（请主 session 批级复查同型写法）**：
   - (i) 的验伪锚 `git diff --stat … | grep -c '_bmad-output/'` **结构上恒 0**——`--stat` 会把长路径首段缩写成 `.../`，字面量消失。改 `--name-only`（或 `--stat=300`）后得 **13**。
   - step 11 的验伪锚「喂含 **F401** 的文件必 rc=1」在本仓**恒不触发**——`backend/ruff.toml` 的 `select` 只有 `E9/F63/F7/F82`。改 **F821** 后 rc=1。（此条与第十三批已登记的同型教训重合，说明模板还没改干净。）
7. **本卡新发现两条（登记不改，见 census §六）**：
   - **T-new-9** `exam_service.py:553-556`（改后 `:556-559`）有与本卡 F-5 **同型**的不精确措辞，因原串被换行切断故 `grep -cF '模块顶层的猴子补丁挂载'` 命中不到它；卡文只授权 `:80-81` ⇒ 未改。
   - **T-new-10** 注释/文档里的 `file:line` 引用**成批漂移**且**无任何自动门**看守（实测：`review_service.py:1238` 指 `canvas_service.py:616` 而 `read_canvas` 在 `:620`；`:1239` 指 `:1249` 而首个 `try:` 在 `:1255`；`:2139` 指「2138/2141」而四个 kwarg ignore 在 `:2142-2145`；`question_generator.py:208` 指 `:598` 而 `asyncio.Semaphore` 在 `:567`；`docs/stories/33.9.story.md:30` 指的符号已整段删除；PRD `:1917` 的 `exam_service.py:69-83` 也已失实）。建议第十五批立 `CARD-COMMENT-LINEREF-GATE`。
8. **锚点漂移登记**：`exam_service.py` 因新增 3 行注释，文件末尾的副作用 `import app.services.exam_service_ext` 由 **`:556` → `:559`**（卡文 §三 的 `:556` 锚点相应更新）。`canvas_service.py` / `review_service.py` **刻意零位移**。
9. **`python-lint` 豁免一次（带存档）**：`ruff format --check` 的漂移集 = {`dependencies.py`, `exam_service.py`}，实测**在 `BASE_F` 上即已漂移**（stdin 模式 rc 两侧逐文件相同），非本卡引入；`python-typecheck` **零豁免**且同跑 exit 0。存档 `ruff-format-drift-preexisting-*.txt` / `ruff-format-hunks-*.txt` / `ruff-format-nonintersect-*.txt`。
10. **`tests/unit` 目录级**：64 条红与 `08100483` 基线**逐条相同**（diff 空，0 新增 0 消失）；pyright warnings **81→80** 的差额来源 = 被清的那条冗余 ignore。
11. **Codex round-1**：`gpt-6-astra` · `ultra` · codex-cli `0.153.3`，绑定 `bcd487db`（= 最终 HEAD），**BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 1** ⇒ **D-15 一轮达成**。存档 `_bmad-output/审查/codex-review-CARD-PYRIGHT-TAIL.md`（首部六行含 codex 版本 / model / reasoning_effort 三字段及其在 `.stderr` 的实际行号 L2/L5/L9），prompt `_bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-TAIL.md`。
12. **⛔ MEDIUM-2 登记不改，请主 session 在下一张同族卡里收紧卡文的规定措辞**：Codex 指出 `exam_service.py` 的「文件内无读 logging 代码 ⇒ 无业务回归」与 `canvas_service.py:341` 的「生产不可达」仍是超出证据的结论——**这个批评在类型上成立**，但这两段是**卡文 §一(e) 逐字规定的新措辞**（源自 U2 r3 L1 与 U1 §二十.2 L-1 的裁定原文），不是车道自拟；协议 §1 对 MEDIUM 是登记不阻断，且 D-15 已达成，改注释会打破 `bcd487db` 的字节级绑定。**源头在裁定原文，不在车道。**
13. **本卡在复审后新增的三项实测**（均为 `_bmad-output` 改动，不动代码）：① `src` 条目贡献 0 文件（受控两跑 `filesAnalyzed` 均 305 + 控制组去掉 `tests` 得 264）；② 删 ignore 在全 include 面 errors 零新增（165 → 165）；③ **`backend/tests` 不在 include 面内**（`include` 的 `tests` = 仓根 `tests/`）——这条澄清了 U2 §五「backend/tests 1350 错」的那个数字**不在本配置的覆盖面上**，请主 session 在 T11 登记时一并注明取值面。
14. **⛔ 又一条判据自伤（第四条，已作废不作依据）**：为验证 MEDIUM-3，本卡先在 scratchpad 造了两份 `include` 用**绝对路径**的探针配置，两侧 `filesAnalyzed` 都得 **0** —— 那不是「没变化」而是**没跑成**：pyright 报 `Ignoring path "..." because it is not relative`，绝对路径被整条忽略。改用「临时改配置 + `git show`/`cp` 还原」的安全模式才拿到真结论。**同型提醒**：凡把配置搬离原位再跑的判据，都要先证它还在读你以为的那份配置。

---

## 七 Codex 独立审查（`gpt-6-astra` · `ultra` · 依 D-15 多轮直到绑最终 HEAD 的一轮 B/H = 0）

### round-1 —— 绑定 `bcd487db`，**BLOCKER 0 / HIGH 0 / MEDIUM 3 / LOW 1**

命令与存档见台账第 11 条。Codex 自述「全程只读，未运行 pyright／pytest／ruff，未连接数据库」。

| 级别 | 条目 | 本卡处置 |
|---|---|---|
| BLOCKER | **无** | — |
| HIGH | **无** | — |
| MEDIUM-1 | census 的「生产调用方」列**混用口径**（实际调用数 / import 命中 / 裸名命中），且部分格只有「有／混合／活」没有数字 ⇒「每条都有实测数字」不成立 | ✅ **采纳并更正**：§一 改为「生产侧使用点」并强制每格自带 `调用式` / `混合命中` / `定性` 三种口径标签之一；§四 逐格补标签。另作废初版定义的「双零」一词——**表里没有任何一行两列都是 0**，留着会让读者以为存在「已证死透」的条目 |
| MEDIUM-2 | 新注释仍有超出证据的结论（`exam_service.py` 的「无业务回归」、`canvas_service.py:341` 的「生产不可达」未限定到所述上游调用链） | ⚠️ **登记不改**（理由三条见 census §十.4 / 台账第 12 条）：措辞是**卡文 §一(e) 逐字规定**的、源自裁定原文；协议 §1 对 MEDIUM 是登记不阻断；D-15 已达成，改注释会打破字节级绑定。**批评在类型上成立，源头在裁定原文** |
| MEDIUM-3 | `git ls-files src = 0` 只证明「无受跟踪文件」，不能独证**分析文件集不变** | ✅ **采纳，并用直接实测关闭**：见下方四-A.10 |
| LOW-1 | 全 diff 的非注释增删行实际是 **3** 行（多出 `pyrightconfig.json` 被删的 include 条目），不是 2 行 | ✅ **采纳并更正**：复核属实——是**取值面与主张不一致**（4 个 `.py` 文件面 = 恰 2，全 5 文件面 = 3），不是数字算错。census §二 末尾已改为完整清单并写明两个面各自的数字 |

### 四-A.10 复审后补的三项实测（`_bmad-output` 改动，不动代码 ⇒ 绑定不破）

用的是本卡 (h) 已验证过的安全模式：临时改文件 → 跑 → `git show HEAD:` + `cp` 还原（⛔ 禁 `git checkout` / `git stash`），每次还原后核 `shasum` 逐字相同 + `git status --porcelain -uno` = 0。

| 实验 | 结果 |
|---|---|
| `src` 条目是否贡献文件（**不带 path 参数**，否则 path 会覆盖 `include`） | 本卡版 `include:["backend/app","tests"]` → `filesAnalyzed` **305**；BASE_F 等价 `[...,"src",...]` → **305** ⇒ **贡献 0 文件** |
| ⛔ **控制组**（排除「恒 305」的假绿） | 临时再去掉 `tests` → `filesAnalyzed` **264** ≠ 305 ⇒ `include` 数组**确实驱动**分析集，上面的「相同」是真结论 |
| 删 ignore 是否在 `app` 之外新冒 error（全 include 面 305 文件） | BASE_F 版 `dependencies.py`：**`165 errors, 82 warnings`**；本卡版：**`165 errors, 81 warnings`** ⇒ **errors 零新增**，warnings 恰少 1 |
| 仓根 `src` 的文件系统层自证（回应「ls-files 只覆盖受跟踪文件」） | `ls -d ./src` rc=**1**（不存在）；验伪锚 `ls -d ./backend` rc=**0**。深度 ≤2 同名目录只有 `./frontend/src`（前端 TS），而 pyright `include` 相对**仓根**解析取不到它 |

⛔ **取值面写明**：`include` 里的 `tests` 是**仓根 `tests/`**（41 个 `.py`；`305 − 264 = 41` 恰好对上），**`backend/tests`（509 个 `.py`）根本不在 include 面内**。所以上表关闭的是「include 面零新增 error」；`backend/tests` 仍留在 §五 未证明清单。

### D-15 达成判定

round-1 **绑定 `bcd487db` = 本卡最终 HEAD**，且该轮 **BLOCKER = 0、HIGH = 0** ⇒ 依 D-15 **一轮达成**，不需再送。
之后的全部改动**只在 `_bmad-output`**（census §十、本验收单、evidence），按协议 §1「终审绑定看代码树」**不破坏绑定**——绑定核见下。
