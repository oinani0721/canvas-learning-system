# CARD-RV-G2-6 (b) — `c4e6b165` 零外审整改逐条定性表

> 复审对象：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'` = 2 files **+453/−50**（Codex r3 审的是 `ff105706`，此后的整改**未再送外审**）。
> ⚠️ **绑定限定（Codex round-1 LOW 更正）**：下表的 file:line 与「旧 rc」是 **`da690bf8` 开工快照**上的实测值 —— 那一刻 HEAD 的四个代码文件与 `c4e6b165` **逐字节相同**（两路交叉证：`git diff --stat` 空 + `git show "c4e6b165:<path>" | shasum` 四条 SAME，见 `minute0-head-proof-20260908T064317.txt`）。本卡随后改动了其中三个文件，**最终 HEAD 已不再与 `c4e6b165` 逐字节相同**；下表行号一律按开工快照读，不按末态读。
> 定性口径：**P1** = 整改不成立 / 缺陷仍在（本卡修）；**P2** = 整改成立但引入或残留新边界（本卡修或登记，逐条写明选哪个）；**登记** = 成立且无新边界。


> **本文档结构**（卡文 (b) 的交付物 = §〇~§五 的定性表；§六~§十 是过程附录，不是交付物）：
> - **§〇** UAT 三套口径矛盾的裁定（本卡取 8 + 17）
> - **§一** 定性表·**指控维度** —— Codex r3 的 10 条结论逐条：级别 / 原指控 / 落点 file:line / P1·P2·登记 / 复现
> - **§一.b** 定性表·**整改维度** —— 8 条代码整改逐条：落点 file:line / 锁它的门 / 定性 / 复现
> - **§三** 定性表·**门维度** —— 17 条新门逐条：nodeid + file:line / 锁哪条整改 / 定性 / **机械变异复现**
> - **§四 + §四.b** 定性表·**登记维度** —— #19/#25 + 全部「成立但不修」项（16 条）逐条：位置 / 不修的理由 / 转给谁
> - **§五** 结论汇总
> - **§六~§十** Codex round-1~5 的逐轮整改过程（含我自己引入的缺陷），供追溯，**不替代上面的定性表**
## 〇 先解 UAT 自身的三套口径矛盾（本卡取 8 + 17）

| 口径 | UAT 位置 | 说法 | 本卡裁定 |
|---|---|---|---|
| 整改条数 | `:522` | 「其中 8 条是代码/清单缺陷，2 条 LOW 是门缺口」 | ✅ **取 8**（代码缺陷口径） |
| 整改条数 | `:656` | 「这一轮**十条**整改 + 17 条新门」 | ⚠️ 「十条」是**含 2 条门缺口的全部结论条数**（3B+1H+3M+3L=10），不是代码缺陷数——非笔误，是口径不同 |
| 新门条数 | `:577` | 「八条整改 + **16** 条新门」 | ❌ **笔误**。实测 12 个新 `def test_`，其中 2 个参数化展开成 4+3 ⇒ 12−2+7 = **17**；`68+17 = 85` 与 `:562`/`:87` 的「85 passed（42→68→85）」同源 |
| 新门条数 | `:562` / `:87` | 「测试 68 → 85 条」= +17 | ✅ **取 17**（实测口径，见下 §三） |

判据（本卡实测 2026-09-08）：`pytest --collect-only` 全文件 **85 tests collected**；12 个新 `def` 的 collected 逐条为 1/1/1/1/1/1/**4**/**3**/1/1/1/1，合计 **17**。

## 一 Codex r3 十条结论 × 在 HEAD 上的复现定性

复现脚本 = `evidence-g26/g26_verify_r3_claims.py.txt` 复制到 scratch 去后缀跑一次；**唯一改动 = `WT` 由 `card-y9-maingoal` 改指 `card-u3-deploy`**（diff 只 1 行，已存档），断言一字未改。跑前做过一次辅助检查：`grep -n 'canvas-vault' <脚本>` → **0 命中**。⚠️ **这条只证明「脚本里没有该字面量」，不足以证明「只访问了临时夹具」**（路径若来自变量就不必出现字面量）——Codex round-2 LOW 更正。真正承重的是脚本正文：全部路径来自 `tempfile.TemporaryDirectory()` 与 `WT` 常量，而 `WT` 指向车道树、不指向 live vault；`WT` 那一行就是本卡唯一改过的一行，diff 已存档。输出：`evidence-rv-g26/r3-claims-on-HEAD-20260908T064916.txt`。

| # | 级别 | 原指控（一句） | 整改落点 HEAD file:line | 定性 | 依据（复现输出行） |
|---|---|---|---|---|---|
| R3-1 | BLOCKER | 大小写目录别名（`--vault …/vault --report …/VAULT/x`）绕过禁写检查，rc=0 且报告落进 vault | `scripts/verify_vault_install.py:835` `_fs_identity`（`(st_dev,st_ino)`）+ `:876-880` 身份优先判 | **登记** | `R3-1 不成立 — 已拒绝`：`rc=2  vault 内被新建 report.txt = False  Dashboard 未变 = True` |
| R3-2 | BLOCKER | `O_EXCL` 失败后 `unlink(tmp)` 删掉**别人的**文件，rc=2 但原文件已毁 | `:590`（临时名带 pid+`os.urandom(4)`）、`:596/:599` `created` 标志、`:615` 只清本次创建 | **登记** | `R3-2 不成立 — 没删别人的文件`：`rc=0  别人的临时文件还在 = True`。⚠️ **依据收窄（Codex r1 LOW 更正）**：这条 `rc=0` 只证明「那个预置文件没被删」，**没有证明发生过 `O_EXCL` 碰撞** —— 整改给临时名加了随机串，脚本预置的 `.report.txt.tmp-<pid>` 撞不上，`except` 分支压根没走到（正是 UAT §十二 记的 M18 教训）。真正走到碰撞分支的是 `c4e6b165` 补的门 `test_exclusive_create_failure_does_not_delete_someone_elses_file`（它把随机串固定住再预置同名文件）；Codex round-1 独立复跑碰撞样例亦通过。⇒「整改成立」的结论仍站得住，站不住的是我原来引的那一条证据。 |
| R3-3 | BLOCKER | 禁写根不覆盖两层软链；扫描失败被忽略。两例均 rc=0 且改变被审树可见内容 | `:522` `SYMLINK_FOLLOW_DEPTH=4`、`:525-...` `_forbidden_roots` 递归+身份去重、`:857/:862/:868-870` 扫描没跑完即拒绝落盘 | **登记** | ① `rc=2  vault 经两层链看到新文件 = False`；② `rc=2 >>> 不成立 — 扫不完就拒绝` |
| R3-4 | HIGH | 两侧同名普通文件均 `000` 权限、内容不同 ⇒ `drift=[]`、`unreadable=[]`、**rc=0**（假绿） | `:452` `_leaf_digest` 改返 `(摘要, 是否读不动)`；`:494-496` 顶层分支登记、`:512-514` 循环内登记 | **登记** | `drift=0  unreadable=2  exit=1` → `R3-4 不成立 — 已登记并阻断` |
| R3-5 | MEDIUM | 单次 `os.write()` 忽略短写，`RLIMIT_FSIZE=1` 下发布 1 字节的截断报告 | `:601-602` `while written < len(data)` 循环写满后才 `os.replace` | **登记** | `RESULT raised 报告落盘失败: …` → `R3-5 不成立 — 短写被发现并报错` |
| R3-6 | MEDIUM | 清单 `source="\ud800"` 逃出 rc=2（写报告时 `UnicodeEncodeError`）并留下临时文件 | `:154` `_require_encodable` + 五个调用点 `:234/:250/:255/:287` | **登记** | `rc=2  落点目录残留 = []` → `R3-6 不成立` |
| R3-7 | MEDIUM | `extra_scan.dir="."`/`"./"`/`".//"` 拼出 `./a`，已声明条目被误报 extra、rc=1 | `:192` `if normalized == ".":` 归一为根 `""` | **登记** | 三态全 `extra=[]` |
| R3-8 | LOW | 悬空软链形态的精确 exclude（`learning_events.jsonl` / `workspace.json`）不登记，后者还被 extra 豁免、rc=0 | `:439` `present = target.exists() or target.is_symlink()` | **登记** | 两项 `= True`，`extra=[] exit=0` → `R3-8 不成立` |
| R3-9 | LOW | **门缺口**：删掉清单 `raw/**`/`templates/**` 后当时 68 条仍全绿 | 补门 `backend/tests/unit/test_vault_install_manifest.py:1094` `test_skeleton_content_excludes_are_pinned` | **登记** | 本卡变异 **M-LOW9**：删这两条 ⇒ 点名门 **KILLED**，`^E` 行 = `AssertionError: raw 下的遗留内容必须被登记为「故意不复制」` / `assert 'raw/**' in []`；跑前跑后两文件 sha 逐个 SAME |
| R3-10 | LOW | **门缺口**：方括号测试的集成部分用的是 `outputs/**`，没有真正含 `[` 的声明 ⇒ 「变异变红」不证明行为回归 | 补门 `…test_vault_install_manifest.py:1111` `test_bracket_exclude_declaration_works_end_to_end` | **P2 → 选「登记」** | 本卡变异 **M-LOW10**（`GLOB_CHARS "*?"→"*?["`）：补门 **SURVIVED**。**正控证明变异确实生效**——同一变异把既有门 `:867` `test_bracket_is_literal_in_both_places` 打红（`^E AssertionError: \`[\` 不再算通配符`）。见 §二 |

**小计：8 条代码缺陷整改全部成立（R3-1~R3-8 = 登记），2 条门缺口 1 条 KILLED、1 条 P2 登记。P1 = 0。**

## 一.b 8 条代码整改 × 落点 file:line × 锁它的门（定性表·整改维度）

UAT-CARD-G2-6 `:522` 的口径：r3 的 10 条结论里 **8 条是代码/清单缺陷**（= R3-1~R3-8），
另 2 条 LOW 是门缺口（= R3-9/R3-10，见 §三 第 15/16 行）。这 8 条的**落点**逐条如下 ——
行号取 `da690bf8` 开工快照（= 与 `c4e6b165` 逐字节同的那一刻，见 §一 上方的绑定限定）。

| 整改 | 对应指控 | 落点 `scripts/verify_vault_install.py` | 锁它的门 | 定性 | 复现 |
|---|---|---|---|---|---|
| ① 落点按 `(st_dev,st_ino)` 身份判 | R3-1 | `:835` `_fs_identity` + `:876-880` 身份优先判 | §三-1 | **登记** | 脚本 `R3-1 不成立 — 已拒绝`；变异 M1 KILLED |
| ② 只清理本次真正创建的临时文件 | R3-2 | `:590` 临时名带 pid+`urandom` / `:596`,`:599` `created` / `:615` 条件清理 | §三-2 | **登记** | 脚本 `R3-2 不成立`；变异 M2 KILLED。⚠️ 依据收窄见 §一 R3-2 行 |
| ③ 禁写根递归展开 + 扫不完即拒绝 | R3-3 | `:522` `SYMLINK_FOLLOW_DEPTH` / `:525-` 递归+身份去重 / `:857`,`:862`,`:868-870` | §三-3, §三-4 | **登记** | 脚本两例均 `rc=2`；变异 M3、M4 双 KILLED |
| ④ 叶子摘要传播读取状态 | R3-4 | `:452` `_leaf_digest` 返 `(摘要, bad)` / `:494-496` 顶层 / `:512-514` 循环内 | §三-5, §三-17 | **登记** | 脚本 `drift=0 unreadable=2 exit=1`；变异 M5c、M12 双 KILLED |
| ⑤ 循环写满才换目录项 | R3-5 | `:601-602` `while written < len(data)` | §三-6 | **登记** | 脚本 `RESULT raised 报告落盘失败`；变异 M6 KILLED |
| ⑥ 加载阶段校验可编码性 | R3-6 | `:154` `_require_encodable` + 调用点 `:234`,`:250`,`:255`,`:287` | §三-7~10 | **登记** | 脚本 `rc=2 残留=[]`；变异 M7 四条全 KILLED |
| ⑦ `.` 归一为根 | R3-7 | `:192` `if normalized == ".":` | §三-11~13 | **登记** | 脚本三态全 `extra=[]`；变异 M8 三条全 KILLED |
| ⑧ 精确 exclude 含悬空软链 | R3-8 | `:439` `present = target.exists() or target.is_symlink()` | §三-14 | **登记** | 脚本两项 `= True`、`extra=[] exit=0`；变异 M9 KILLED |

**8/8 全部成立（P1 = 0）**，且**每一条都有一个被机械变异证明承重的门**。

## 二 R3-10 的 P2 详解（唯一非纯登记项）

- **为什么 SURVIVED 是真的**：补门声明的规则是 `outputs/[draft].json`。`GLOB_CHARS="*?"` 时 `_has_glob` 为 False ⇒ 走 `hits_for` 的**精确分支**（`:437-441`）；`GLOB_CHARS="*?["` 时为 True ⇒ 走**glob 分支**（`:442-448`），而 `_pattern_to_regex` 对 `[` 走 `re.escape`（`:329`）当字面量、`_static_prefix` 在 `[draft].json` 处 break 得到前缀 `outputs`。**两条路径对该输入产出同一结果**，所以这条门物理上看不见这个变异——不是门写坏了，是**输入选得不能翻转**。
- **r3 的修复建议是三维**（分类 / 摘要过滤 / `a.json` 负例），补门覆盖了**分类 + 负例两维**，**「摘要过滤」那一维未覆盖**。
- **承重的仍是既有门 `:867`**（`assert not vv._has_glob("outputs/[abc].json")`）——Codex r3 说的「常量断言」指的就是它；HEAD 与 `ff105706` 全文件 `grep -n 'GLOB_CHARS'` 都**只有一处 docstring 命中**（`:863`），**没有**独立的常量相等断言。
- **本卡选「登记」不修**：修它要么改补门的声明输入（会动 `c4e6b165` 的门语义、超出本卡 (c)-(f) 范围），要么加第 11 条门（卡文 (g) 钉死 ①~⑩）。登记进「未证明」与台账。

## 三 17 条新门 × **逐条承重验证**（定性表·门维度）

判据：给每条门配一个**只拆它所锁那一层**的机械变异，要求**点名的那条门**变红。
三态 KILLED / SURVIVED / INVALID；跑前对 `verify_vault_install.py` 与 `vault-install-manifest.json`
记 sha 基线，`finally` 无条件还原，跑后逐个复核 —— 实测**两文件跑后 sha 与跑前逐个 SAME**。
harness `gate17-mutation-probe-20260908T093014.py.txt` / 输出 `gate17-mutation-20260908T093014.txt`。

| # | 门 nodeid（HEAD file:line） | 锁住的整改 | 定性 | 复现（变异 → 判定） |
|---|---|---|---|---|
| 1 | `test_case_insensitive_alias_is_refused`（test:972） | 整改① 落点按 `(st_dev,st_ino)` 身份判 | **登记** | M1 `_fs_identity` 恒 None → **KILLED** |
| 2 | `test_exclusive_create_failure_does_not_delete_someone_elses_file`（test:988） | 整改② 只清理本次真正创建的临时文件 | **登记** | M2 `if created:`→`if True:` → **KILLED** |
| 3 | `test_two_hop_symlink_target_is_refused`（test:1019） | 整改③a 禁写根递归展开 | **登记** | M3 不再递归展开软链 → **KILLED** |
| 4 | `test_incomplete_safety_scan_refuses_to_write`（test:1032） | 整改③b 扫描没跑完即拒绝落盘 | **登记** | M4 忽略 `scan_failures` → **KILLED** |
| 5 | `test_both_sides_unreadable_plain_files_still_block`（test:1053） | 整改④ 顶层叶子传播读取失败 | **登记** | M5c `read_bytes` 失败点 `bad=False` → **KILLED**（`^E AssertionError: 读不动的普通文件必须被登记`） |
| 6 | `test_short_write_is_detected`（test:1073） | 整改⑤ 循环写满才换目录项 | **登记** | M6 单次 `os.write` → **KILLED** |
| 7–10 | `test_unencodable_string_in_manifest_exits_2[source\|role\|origin\|note]`（test:1098） | 整改⑥ 加载阶段可编码性校验 | **登记** | M7 取消 `_require_encodable` → **四条全 KILLED** |
| 11–13 | `test_extra_scan_dot_is_normalized_to_root[.\|./\|.//]`（test:1117） | 整改⑦ `.` 归一为根 | **登记** | M8 取消归一分支 → **三条全 KILLED** |
| 14 | `test_dangling_symlink_exclude_is_registered`（test:1127） | 整改⑧ 精确 exclude 含悬空软链 | **登记** | M9 改回 `target.exists()` → **KILLED** |
| 15 | `test_skeleton_content_excludes_are_pinned`（test:1139） | 门缺口 R3-9（`raw/**`、`templates/**` 未钉住） | **登记** | M10 清单删这两条 → **KILLED**（`^E AssertionError: raw 下的遗留内容必须被登记…`） |
| 16 | `test_bracket_exclude_declaration_works_end_to_end`（test:1156） | 门缺口 R3-10（方括号声明端到端） | **P2 → 登记** | M11 精确 exclude 一律不命中 → **KILLED**（`^E …字面方括号声明应当精确命中`）；⚠️ 但对 `GLOB_CHARS` 变异**不可区分**，见 §二 |
| 17 | `test_unreadable_leaf_inside_directory_is_registered`（test:1180） | 整改④ 目录循环内叶子登记 | **登记** | M12 循环内不再 `_note` → **KILLED** |

**合计 17 条，KILLED 17 / SURVIVED 0。** 这条结论替换本卡早先「其余 15 条只核了存在与 collected 数、
未逐条做变异」的登记 —— 那一条**已兑现**。

### ⚠️ 首轮 M5 是**假 SURVIVED**，如实记

第一次跑 M5 时报 SURVIVED。按「SURVIVED 须先证明变异生效」查：`_leaf_digest` 在 round-5 重写后有
**三个** `OSError` 返回点（`lstat` / `readlink` / `read_bytes` 失败），我的 4 空格缩进锚点命中的是
**`lstat` 那个**，而这条门用的是两侧 000 权限的**普通文件** —— `lstat` 成功、`read_bytes` 才失败。
**变异根本没打在该门走的那条路径上。** 逐个返回点重打后 M5c KILLED。

⇒ **锚点会随我自己的重构漂移**：M5 的锚点是照 round-3 的 `_leaf_digest` 写的，round-5 我把那个函数
改成单次 `lstat` 分派，锚点就指到别处去了，而 `count == 1` 的自检**照样通过**（它只证唯一，不证正确）。

**顺带照出两处真实覆盖缺口（登记，未修）**：M5a（`lstat` 失败点 `bad=False`）与
M5b（`readlink` 失败点 `bad=False`）**均 SURVIVED** —— 没有任何门锁住这两条路径。

## 四 UAT「未证明」#19 / #25 的处置

| # | 内容 | 本卡处置 |
|---|---|---|
| #19 | 测试文件头注写于 round-1，未随钉死点扩充更新；UAT 说「留到 round-3 有结论之后再补一个纯注释 commit」——**该 commit 从未做** | **本卡 (i) 还上**：头注按现状重写并列出本卡新增门。已不存在「改它会让 round-3 绑定失效」的理由（round-3 早已结束且本卡就是它的复审） |
| #25 | `_iter_relative()` 丢弃遍历错误类型：读不动的目录里藏着 exclude 项不会被报出来 | ⚠️ **本行的原处置「登记，不修」已作废** —— Codex round-1 把它判为 HIGH，**round-2 已修**（`_iter_relative` 增 `unreadable` 出参并透传到 `hits_for` → `verify()`，跨 exclude 项去重）；round-3 进一步补上了「祖先目录不可搜索 ⇒ 连扫描根都 stat 不到」这个更早的入口（见 §六）。详见 §六与 §七 |

## 四.b 「登记」项汇总（定性表·登记维度）

卡文 (b) 要求的「登记」不止 #19/#25。本卡全部**成立但不修**的条目集中在这里，
每条给出：来源 → 现状 file:line → 为什么不修 → 转给谁。

| # | 登记项 | 现状位置 | 为什么不在本卡修 | 转给 |
|---|---|---|---|---|
| L1 | UAT #19 测试头注未随钉死点更新 | — | **已修**（本卡 (i) 还上，头注按现状重写并列出本卡新增门） | — |
| L2 | UAT #25 `_iter_relative` 丢弃遍历错误类型 | — | **已修**（round-2 增 `unreadable` 出参；round-3 补上「连扫描根都 stat 不到」的更早入口） | — |
| L3 | R3-10 方括号门对 `GLOB_CHARS` **不可区分** | 门 `test:1156` | 两条实现路径对该输入语义等价，是**输入选得不能翻转**；改它要动 `c4e6b165` 的门语义 | 下一卡 |
| L4 | r3 建议的「摘要过滤」维度未覆盖 | 同上 | 同 L3 | 下一卡 |
| L5 | `extra_allow` 重叠判定是**字面层面**近似 | `verify:_overlapping_declaration` | 两个 glob 之间的语言包含判定需要正则交集 | 下一卡 |
| L6 | hotkeys 字面量法的**假放行**（注释 / 普通字符串里的同形 id） | `verify:COMMAND_ID_RE` | 需要 JS 语法分析 | 下一卡 |
| L7 | hotkeys 的**假拦下**：JS 转义写法、拼接表达式 | 同上 | 同 L6。⚠️ 本卡曾把它写成「只有 JS 转义一种」，Codex r4 更正为至少两类 | 下一卡 |
| L8 | `main.js` 缺时 `not evaluated` **不计 rc** 的部署态盲区 | `verify:_check_hotkeys` | 这是卡文 (e) 钉死的语义 | 主 session 裁 |
| L9 | `.obsidian/*.json` 覆盖面只看 `.json`（UAT #18） | manifest `extra_scan` | 改覆盖面 = 改卡文定义 | 下一卡 |
| L10 | 禁写链三处身份/类型查询失败未全部显式登记 | `verify:820,1371,1383` | 该链已 fail-closed；**最后一轮动本卡最重的防线风险大于收益**。⚠️ Codex r5 指出我「最坏多拒一次」的说法**比证据宽**，该收窄的是表述 | 主 session 裁 |
| L11 | skeleton 的 `is_dir()`：软链目标查不到仍说「不是目录」 | `verify:973-980` | 同 L10（但 Codex r5 明确指出它**不属于**禁写防线，不能用同一理由搪塞） | 主 session 裁 |
| L12 | `_leaf_digest` 的 `lstat` / `readlink` 失败点**无门覆盖** | `verify:_leaf_digest` | 本次 17 门变异照出（M5a/M5b SURVIVED），轮次已满 | 下一卡 |
| L13 | 「单射」表述须全域收窄 | 本表 + UAT 全文 | SHA-256 非数学单射、十样本不证全域 —— **已在文中逐处收窄为「在这一族已知有损变换上不碰撞」** | — |
| L14 | 十叶子性质门抓不到 `ignore`/`replace` 退化 | 门 `test:1769` | Codex r5 实测两种策略下十摘要仍两两不同 ⇒ **我原来的「只要出现就会红」不成立**，已收窄表述 | 下一卡 |
| L15 | 无缓冲 `--help` 断管返回 0（同形默认缓冲为 3） | `verify:__main__` | 输出失败口径未统一，不声称检查过 vault | 下一卡 |
| L16 | `census-stderr.txt` 逃出 `*.stderr*` 忽略规则 | 仓根 `.gitignore` | 既有文件，非本卡引入 | 下一卡 |

## 五 结论

- **指控维度（§一，10 条）**：**P1 = 0**（无「整改不成立 / 缺陷仍在」）；**P2 = 1**（R3-10，选登记）；**登记 = 9**。
- **整改维度（§一.b，8 条）**：**8/8 成立**，且每一条都有一个被机械变异证明承重的门。
- **门维度（§三，17 条）**：**KILLED 17 / SURVIVED 0**。跑前跑后两文件 sha 逐个 SAME。
  > ⚠️ 首轮 M5 报 SURVIVED 是**假 SURVIVED**（锚点随我自己在 round-5 的重构漂移，
  > 打中了该门不走的那个返回点）。逐返回点重打后 KILLED，详见 §三 末。
- **登记维度（§四 + §四.b，16 条）**：#19 与 #25 **已修**；其余 14 条逐条写明位置、不修的理由与去向。

### 本卡在复审面上**未做**的（如实）

1. r3「其余核对结果」里的 AST 门评述、`resolve()` 版本相关观察**未独立复验**。
2. 17 条门各自只做了**一个**变异（拆它所锁的那一层）；没有做交叉变异矩阵，
   因此证明的是「每条门锁住了它声称锁的那条整改」，**不是**「这 17 条门覆盖了全部缺陷面」。
3. `_leaf_digest` 的 `lstat` / `readlink` 两个失败返回点**没有任何门覆盖**（M5a/M5b 均 SURVIVED），
   已登记为 L12。

## 六 Codex round-1 之后（round-2 整改，2026-09-08）

round-1 绑 `523c10f0`，结论 **0 BLOCKER / 2 HIGH / 5 MEDIUM / 5 LOW**。
它独立复核了 §一 那 8 条历史整改（15 个隔离样例，**全部通过**）与 rc 的 **128 种桶组合**
（与本卡 `no-downgrade-proof-*.txt` 的枚举同结论）。按 D-15，HIGH 必须清零。逐条处置：

| 级别 | 问题 | 处置 |
|---|---|---|
| HIGH | 给了 `--source` 而源端缺该 copy 项时，未比较的目标仍记 **match** | **修**。改记 `unreadable`（「看不见不等于一致」同一纪律），计入阻断。门 `test_copy_item_missing_on_source_is_not_reported_as_match` |
| HIGH | exclude 扫描失败仍可能静默返回 0（= UAT-CARD-G2-6 #25） | **修**。`_iter_relative` 增 `unreadable` 出参并透传到 `hits_for` → `verify()` 登记（跨 exclude 项去重）。门 `test_unreadable_dir_in_exclude_scan_surface_is_registered`。**本卡原登记「不修」的 #25 就此收口** |
| MEDIUM | `main.js` 未评估仍 rc=0，部署核验留盲区 | **登记不修**：这是卡文 (e) 钉死的语义（不计 rc、不静默）。盲区写进「未证明」与台账 |
| MEDIUM | 命令字面量法假放行/假拦下；`main.ts` 数量门不证明注册语义 | **修一半**：正则改认三种引号 —— 只消除了**引号风格**造成的假拦下，⚠️ **不是「消除假拦下」**（Codex round-2 MEDIUM 更正）：产物里写成 JS 转义的注册（如 `"canvas:\u0061"`）仍提取不到，而其它 id 提取成功会让集合非空、绕过零命令分支，于是那条真实绑定被报成 orphan。`main.ts` 门已绑到 `addCommand({ id:` 注册点。**假放行**（注释里的同形字面量）与**转义形态的假拦下**都仍在，登记 |
| MEDIUM | 新 hotkeys 输入重开了未捕获的 `UnicodeEncodeError`（实测 rc=**1**，被误归「只有 missing」档） | **修**。`_printable()` 在 **render 输出边界**统一收口，一处覆盖全部来源 |
| MEDIUM | `argparse` 参数错误仍 rc=**2**，与新语义的 mismatch 撞车 | **修**。`_Parser.error()` 抛 `SystemExit(EXIT_USAGE)` |
| MEDIUM | `:117` 仍把 `SKILL.md` **是目录**的半成品计为完成；测试只查命令字符串 | **修**。判据加 `-type f`（仍一行、157 行不变）；门补**行为断言**（真跑抽出的两行）+ `SKILL.md` 为目录的负控 |
| LOW | 重叠门未锁反向覆盖（删两处 `_pattern_covers(path, allow)` 仍全绿） | **修**。补两个反向参数 |
| LOW | `not evaluated` 断言借用 content-drift 段的同一词 | **修**。断言锁到 `hotkeys ` 那一行 |
| LOW | orphan / 非法 JSON 两门没排除其他阻断桶 | **修**。各补「其余桶为空」 |
| LOW | 方括号门对 `GLOB_CHARS` 不可区分 | **同意，维持登记**（Codex 明确认可本表 §二 的登记准确） |
| LOW | 本表 HEAD 绑定与 R3-2 证据表述过宽 | **修**，见 §一 上方两处 ⚠️ |

Codex 另指出两条口径需要限定，已采纳：

1. **「绝不读取树外」不成立** —— 既有扫描路径与新增 hotkeys 读取都会跟随软链，树外软链目标确实会被读。
   本卡的承诺应表述为「**不写**被审树」，不是「不读树外」。
2. **「任何原先 1 都不会变 0」必须加限定** —— 只在**空白名单**下成立；`extra_allow` 非空时把 extra
   从阻断变成 0 **正是设计行为**，翻转表 ① 就是验证它的。

### round-2 后的复核状态

`_iter_relative` 的收口把 UAT #25 从「登记不修」变成「已修」——
本表 §四 的 #25 行与 §五「未证明」相应条目按此更新（见 UAT §十二）。

---

## 七 Codex round-2 之后（round-3 整改，2026-09-08）

round-2 绑 `6bdb0fab`，结论 **0 BLOCKER / 1 HIGH / 4 MEDIUM / 5 LOW**。
它明确写了「本轮**未确认整改新引入的运行时缺陷**」，并独立复核确认：源端缺项整改无问题、
新出参调用链无遗漏且跨项去重成立、四档桶优先级 **128 种组合全部通过**、
`_Parser.error()` 四种参数错误实测 `SystemExit(3)` 且 `--help` 保持 0、
render 正文转义有效、零命令处理没把真问题放绿、收紧后的主要门都能针对相应退化承重。

| 级别 | 问题 | 处置 |
|---|---|---|
| **HIGH** | **整改遗漏**：exclude 的存在性谓词吞 `OSError`，扫描根/精确目标 stat 不到时提前返回，**根本没进** round-2 建的 unreadable 透传链 ⇒ 仍可返回 0 | **修**。新增三态谓词 `_entry_state()`（`present`/`absent`/`unreadable`，用 `os.lstat`），`_iter_relative` 入口与 `hits_for` 精确分支两处都换掉。门 `test_unreachable_exclude_scan_root_is_registered_not_treated_as_absent`（glob 与精确两个入口各一条断言） |
| MEDIUM | **遗留**：两侧都读不动、摘要标记相等时，同一 copy 项仍计入 match | **修**。`unreadable_here` 非空即 `continue`，不再记 match。门 `test_both_sides_unreadable_is_not_counted_as_match` |
| MEDIUM | **遗留**：`_printable()` 挡不住 render **之前**的摘要编码异常（文件名 / 软链目标文本） | **修**（⚠️ **round-3 的修法本身有缺陷，已由 round-4 更正**）：round-3 改成 `backslashreplace`，理由写的是「摘要只需确定性，转义不影响可比性」—— **这句话是错的**，Codex round-3 HIGH-1 推翻并本机复现：确定性是必要条件不是充分条件，摘要还必须**单射**。`backslashreplace` 有损，`os.fsdecode(b"bad\xff")` 与字面转义串编码后逐字节相同 ⇒ 两个不同的软链目标判等 = **假绿**。round-4 改用 `surrogatepass`（单射且不抛）。门 `test_digest_encoding_is_injective_not_merely_total`（AST 判据）+ `test_two_different_symlink_targets_do_not_collide`（行为判据） |
| MEDIUM | **遗留**：`expanduser()` 对 `~未知用户名` 抛 `RuntimeError`，CLI 以 1 结束 | **修**。抽 `_expanduser()` 统一归用法错档，`--vault`/`--source`/`--report`/`--manifest` 四处共用。门 `test_tilde_expansion_failure_uses_the_usage_exit_code` |
| MEDIUM | **整改不完整**：三种引号没有消除「部分命令解析失败」的假拦下；本表「消除假拦下」表述过宽 | **改表述 + 登记**。⚠️ **round-4 再次更正**：假拦下**不止 JS 转义**一种形态，而且我原先举的例子在 Markdown 里丢了反斜杠、写成了一个能被正常提取的串（Codex round-3 LOW 指出）。实际形态至少两类：① 转义写法 `` `"canvas:\u0061"` ``（反斜杠 u 0 0 6 1）提取不到；② **拼接表达式** `` `{id:"canvas:open-"+"dashboard"}` `` 会提取出 `canvas:open-` —— 于是真实的 `canvas:open-dashboard` 被报 orphan（假拦下），而从未注册的 `canvas:open-` 反被放行（假放行）。两类都**未修、登记**：真修需要 JS 语法分析，超出本卡范围 |
| LOW | `SKILL.md` 目录负控**没有单独承重**（去掉 `-type f` 也只有 7 个 ⇒ 照样红） | **修**。改成 7 合格文件 + 1 目录入口：不区分类型时数到 8 会放行、加 `-type f` 是 7 而拦下。另加前提断言 + 外部对照实测（带 `-type f`→NO / 去掉→OK） |
| LOW | 「单一真相源」门只比 helper 与调用 helper 的 property = **自证**，没检验加载侧 | **修**。改成**行为门**：`extra_allow=[".canvas-config.yaml"]`（唯一的 `generate` 项）必须被拒 —— 加载侧若漏掉 generate 就会错误接受 |
| LOW | exclude unreadable 门**没锁跨项去重**（`any()`/`next()` 允许重复登记） | **修**。改数次数：`.claude/hooks` 同时落在两条 exclude 的扫描面里，断言**恰好一次** |
| LOW | 文档旧口径冲突：本表 `:67` 仍写 #25「登记，不修」；代码注释仍称配置/报告错误返回 2 | **修**（⚠️ **round-3 只清了一半，round-4 补齐**）：`:67` 已改写；代码里「退出码 2」四处改完后，`load_manifest` docstring 仍留着「拿到的是 1 而不是承诺的 **2**」这一处旧口径（Codex round-3 LOW 抓到），round-4 一并改成「承诺的用法错档(EXIT_USAGE=3)」。现 `grep '承诺的 2'` 与 `grep '退出码 2'` **均 0 命中** |
| LOW | 本表 `:20` 把 `grep 'canvas-vault'` 零命中当成「只访问临时夹具」的**自证** | **修**。降级为辅助检查，并写明真正承重的是脚本正文（全部路径来自 `TemporaryDirectory()` 与 `WT` 常量） |

### 一句话总结这一轮

round-2 的 HIGH 修法**只覆盖了「已经进入遍历」的失败**，没覆盖「**连遍历都没开始**」的失败 ——
`Path.exists()` / `is_dir()` / `is_file()` / `is_symlink()` / `rglob()` 都会把「问不出来」返回成
「不存在 / 空」。这份被测代码的 `_walk` docstring 早就为 `rglob` 写过同一条教训，
而同一份代码在另外两个入口照样用了 `exists()` —— **写下教训 ≠ 变成判据**。

---

## 八 Codex round-3 之后（round-4 整改，2026-09-08）

round-3 绑 `736eb490`，结论 **0 BLOCKER / 3 HIGH / 4 MEDIUM / 4 LOW**。
**三条 HIGH 里有一条是 round-3 的修法自己引入的**，另加两条新引入的 MEDIUM ——
这一轮把「修复链会自我繁殖」演示得最彻底。全部五条我都**本机独立复现后才动手**
（`evidence-rv-g26/verify-r3-claims-*.txt`），不采信结论本身。

| 级别 | 问题 | 处置 |
|---|---|---|
| **HIGH【新引入】** | `backslashreplace` **不单射** ⇒ 两个不同的软链目标判等 = 假绿 | **修**。改 `surrogatepass`（单射且不抛）。⚠️ 根因是我 round-3 写的那句理由「摘要只需确定性」—— **确定性是必要条件不是充分条件**，摘要还必须单射。两道门：AST 判据（摘要函数里的 `encode` 不得用 `backslashreplace`，带验伪锚）+ 行为判据（两个不同软链目标必须给出不同摘要） |
| **HIGH【遗漏】** | 还有四个「查不到即不存在／不扫描」的入口：item 目标 `exists()`、extra 覆盖面根 `is_dir()`、hotkeys 两处 | **修**。四处全换 `_entry_state`。item 目标问不出来时归 unreadable（原会降级成 missing ⇒ rc=1「只缺东西」）；覆盖面根问不出来时登记（原静默跳过）；hotkeys 两处把「查不到」与「确实没有」分开 |
| **HIGH【遗漏】** | `_leaf_digest` 在类型谓词全失败时落到 `"?:unknown"` 且 `bad=False`；`_kind_ok` 把查询失败当成 `nondir` | **修**。`_leaf_digest` 先用 `_entry_state` 探一次；`_kind_ok` 问不出类型时对**所有** kind 返回 False（原 `nondir` 分支在谓词被吞时恒 True） |
| MEDIUM【新引入】 | `_entry_state` 把 `ENOTDIR` 错归 unreadable ⇒ exclude 被误阻断 | **修**。`NotADirectoryError` 归 `absent`（它是**确定的**否定答案） |
| MEDIUM【新引入】 | `unreadable_here` 的提前 `continue` 把同一项里**已经看得见的**内容差异也遮掉了 | **修**。调换顺序：先判漂移、再判读不动 |
| MEDIUM【遗留】 | stdout 编码失败（rc=1）/ 断管退出期 flush 失败（rc=120）脱离四档 | **修**。`__main__` 里先 `reconfigure(errors=...)`，再接住 `SystemExit` 与 `BrokenPipeError`。⚠️ **没有为此放宽零写门**：`os.dup2(os.open(os.devnull,…))` 会让 AST 零写门变红，改用哑对象替换 `sys.stdout`，两种写法实测同为 rc=3 且无退出期噪音 |
| MEDIUM【遗留】 | hotkeys 假拦下不止 JS 转义；我举的例子在 Markdown 里丢了反斜杠 | **改表述 + 登记**（见 §一 那一行）。新增登记：**拼接表达式**同时造假拦下与假放行 |
| LOW ×4 | 入口门缺正常/不存在对照 / 去重门没证两个来源都到达 / 编码门与展开门覆盖不全 / 表述三处 | **全部已修**：入口门的对照由 `test_entry_state_maps_enotdir_to_absent` 承担（`_entry_state` 恒返 unreadable 会打红它）；去重门补「覆盖 `.claude/hooks` 的 exclude ≥2 条」前提断言；编码门改 AST 覆盖全部摘要 `encode`；展开门覆盖四个调用点；表述三处见 §一 |

### 这一轮的方法论教训

1. **给哈希选编码器，判据是单射性，不是「不抛异常」。** 我 round-3 只验了「不抛」。
2. **修一类缺陷要枚举同类入口，不能顺着 finding 往下走。** `_entry_state` 是 round-3 引入的，
   但 round-3 只换了两个被点名的入口；剩下四个是 round-4 才补的。
3. **文本判据在源码上不可靠 —— 本卡被注释误伤三次**（标签里的 `ls `、docstring 里的代理转义、
   注释里的 `backslashreplace`）。判据一律绑 AST。
4. **门因自己的代码变红时，先找不需要豁免的实现。** 断管收尾的三种写法里，
   有一种不含可写调用且效果相同，于是零写门原样保留。

---

## 九 Codex round-4 之后（round-5 整改，2026-09-08）—— **卡族轮次上限**

round-4 绑 `977d1e6d`，结论 **0 BLOCKER / 4 HIGH / 3 MEDIUM / 2 LOW**（HIGH 从 3 涨到 4）。
七条全部本机独立复现后才动手（探针 `verify-r4-claims-probe-*.py.txt`）。
**协议 §1 的轮次上限是 5 —— 这是最后一轮。**

| 级别 | 问题 | 处置 |
|---|---|---|
| **HIGH【遗留】** | 软链目标经 `str(Path.readlink())` **规范化**后判等：`payload` 与 `payload/`、`x//y` 与 `x/./y` 摘要相同。**摘要在编码之前就丢了信息，换编码器救不回来** | **修**。改 `os.readlink()` 取原文 |
| **HIGH【遗漏】** | FIFO / Unix socket / 设备节点一律记 `"?:unknown"` 且 `bad=False` ⇒ 两种不同类型的特殊文件判等 | **修**。非「软链/普通文件/目录」的条目记 `stat.S_IFMT` 类型位（实测 FIFO `?:010000` vs socket `?:140000`） |
| **HIGH【新引入】** | round-4 让 `_kind_ok` 一律返回 False ⇒ 丢了失败原因（调用方无从登记 unreadable），且会把条目从「故意不复制」翻成「清单外的 extra」= 误报 | **修**。改**三态** `bool \| None`；`matches_exact` / `is_under_exclusion` / `hits_for` 全部接三态并透传失败位置 |
| **HIGH【遗漏】** | `lstat` 成功不代表**跟随软链后**查得到：扫描根或 `main.js` 是指向不可搜索目录的软链时，`is_dir()`/`is_file()` 仍返回 False ⇒ 扫描被跳过 / 产物被说成「没生成」 | **修**。新增 `_resolved_kind()`（`dir`/`file`/`other`/`unreadable`），extra 覆盖面根与 `main.js` 两处都用它 |
| MEDIUM【新引入】 | 先比总摘要 ⇒ 「两侧内容相同、只一侧不可读」被报成 content-drift（把读取能力差异说成字节差异） | **修**。`_digest` 拆成 `_digest_pairs()` + `_fold(pairs, skip)`；`verify()` 取**两侧 unreadable 的并集**做 skip，两侧同时剔掉后再比 |
| MEDIUM【遗漏】 | 目标 missing 时，源端的查询失败只写进 `missing.detail`，没进四档分类 ⇒ 整轮可能 `unreadable=0`、rc=1 | **修**。同时登记 unreadable |
| MEDIUM【整改不完整】 | 断管保护只覆盖最后的 stdout flush：`-u` 无缓冲下 write 当场抛（rc=1）、stderr 断管（rc=120）都没接住 | **修**。`main()` 外层加 `except BrokenPipeError`；收尾**两个流都 flush** 并各自换哑对象。九种形态实测：ascii `--help`=0 / 默认·无缓冲 × stdout·stderr·双断=全 3 / 正常 run=2 / 正常 `--help`=0 / 正常参数错=3 |
| LOW | 摘要门**按名字**判（「不许出现 backslashreplace」），换成 `ignore`/`replace` 照样有损而门不红 | **修**。改成**性质门**：10 个两两不同、历史上会被各种有损变换压到一起的叶子（尾斜杠 / 冗余分隔 / 非法字节 / 字面转义串 / FIFO / socket / 普通文件 / 目录）喂进真实摘要，断言两两不同 |
| LOW | 去重门只证「有两条配置」，没证「两个失败来源都实际到达」 | **修**。改成**逐条单独跑** `hits_for`，每条都必须登记到该位置 |

### 这一轮我**没有**做的（如实声明）

- Codex round-4 列的「真漏」清单里，`V:738` / `V:1246` / `V:1258`（`_forbidden_roots` 与报告落点的
  身份/类型查询）**未改**。理由：那条链上的策略已经是 **fail-closed**（扫描没跑完就拒绝落盘），
  查询失败最坏的后果是「多拒一次」而不是「放行一次」；Codex 本人也写了「未实证写穿」。
  改它会动本卡最重的那道禁写防线，在**最后一轮**动它风险大于收益。**登记，转下一张卡。**
- `V:880` skeleton 的 `is_dir()`（软链目标查不到时归 missing）**未改**，同上理由，登记。
- hotkeys 的假放行/假拦下（注释、拼接表达式、JS 转义）**未改**，需要 JS 语法分析，超出本卡范围。

---

## 十 Codex round-5 —— **轮次用满，车道停手，交主 session 人审**

round-5 绑 **`ee18eb44` = 本卡最终 HEAD**（`git diff --stat ee18eb44 HEAD -- . ':(exclude)_bmad-output'`
输出 0 字节 ⇒ 审后**未再改代码**，本存档**绑合并态**）。
结论 **0 BLOCKER / 2 HIGH / 6 MEDIUM / 2 LOW**。

**协议 §1：轮次上限 5，第 5 轮仍有 HIGH → 停下交主 session 人审。**
车道**不自判通过**。这里不是「快到点了所以收工」，而是：**继续改会让本卡以「整改未复审」收尾 ——
而这张卡存在的全部理由，就是上一次的整改未复审（`c4e6b165`）。** 再犯同一个错没有意义。

### 两条 HIGH（本机独立复现，存档 `verify-r5-claims-*.txt`）

| # | 问题 | 我的复现结果 | 我对归属的判断（**供裁定，非自判**） |
|---|---|---|---|
| H1 | `kind=file` 的 `_kind_ok` 走 `path.is_file()`，它**跟随软链**；目标查不到时返回 False 而**不产生 None** ⇒ `hits_for` 既不算命中也不登记 = 静默漏报 | `_entry_state(x)='present'`、`_resolved_kind(x)='unreadable'`、`_kind_ok(kind=file)=**False**`、`hits=[] unreadable=[]` —— **成立** | **本卡范围内应修**：这是本轮三态整改的直接遗漏，改动面就是 `_kind_ok` 的 `file` 分支 |
| H2 | 特殊节点摘要只保留 `S_IFMT`，**丢了 `st_rdev`** ⇒ 两个不同的字符设备判等 | 只读 `/dev`：`/dev/null` 与 `/dev/zero` 摘要同为 `?:020000`、`st_rdev` 分别 50331650 / 50331651 —— **成立** | **两条路都合理，请裁**：(甲) 补 `st_rdev` 进摘要；(乙) 把契约明确收窄为「特殊节点只比较类型」并登记。⚠️ 选乙就**不能**再宣称「摘要消除了所有有损处理」 |

### 六条 MEDIUM 里，**两条是我这一轮新引入的**（如实）

| # | 问题 | 复现 |
|---|---|---|
| M1 | `_resolved_kind` 把**确定不存在**（ENOENT）与 ENOTDIR 都归 `unreadable` ⇒ 扫描根确实不存在时被误报 unreadable、rc 由 1 抬成 2 | `_entry_state(不存在)='absent'` 而 `_resolved_kind(不存在)='unreadable'` —— **成立** |
| M4 | `_fold` 的 skip 会把**已经可证明的类型差异**一起剔除（一侧不可读普通文件 vs 对侧空目录 ⇒ 判等） | Codex 内存对照，我未单独复现（属同一 skip 粒度问题，与 M3 同源） |

> ⛔ **M1 是同一个错误犯第二次**：round-4 我刚把 `_entry_state` 的 ENOTDIR 从 unreadable 改成 absent，
> 还写了门 `test_entry_state_maps_enotdir_to_absent` 钉住它；round-5 我新写**姊妹谓词** `_resolved_kind`
> 时又原样犯了一遍 —— 那道门只盯着 `_entry_state`，看不见新函数。
> **加门时要问「这条约束该管住哪一族函数」，不是「该管住我刚写的这一个」。**

其余四条 MEDIUM：M2（extra 最终消费端仍丢 None ⇒ 误报 extra）、M3（目录不可列举时 skip 只跳目录 key，
对侧子孙仍参与摘要 ⇒ 仍误报 drift，**我已复现成立**）、M5（skeleton 软链目标查不到仍说「不是目录」）、
M6（本表 `:193-196` 的「已 fail-closed，最坏多拒一次」**说得比证据宽**，应收窄）。

### 两条 LOW

- **十叶子性质门抓不到 `ignore`/`replace` 退化**：Codex 实测那两种策略下十个摘要**仍两两不同**
  ⇒ 我写的「新的有损写法只要出现就会红」**不成立**，应收窄为「拒绝了 `backslashreplace` 并挡住这一族已知碰撞」。
- **无缓冲 `--help` 断管返回 0**（同形默认缓冲为 3）——输出失败口径未统一。

### Codex round-5 明确核对为「无问题」的部分

base key 与 exclude 对齐、`os.readlink` + `surrogatepass` 消除已知转义碰撞、
FIFO/socket 已区分、三个三态调用点**内部**确实接住了已产生的 None、
退出码桶优先级 **128 种组合**全部符合契约、源端 unreadable 登记的源码传播正确、
逐条 `hits_for` 去重门「补上了少扫一路冒充去重的漏洞」、
结论表的历史行号快照限定 / R3-2 证据收窄 / 方括号门解释 / **12 个新增函数展开 17 条测试** 均与 diff 一致。

⚠️ 它同时提醒：**SHA-256 本身并非数学上的单射，十个样本也不能证明全域单射** ——
本表凡出现「单射」处，应读作「在这一族已知的有损变换上不碰撞」。

### 给主 session 的三个裁定点

1. **是否放行第 6 轮**（只修 H1 + M1 这两条改动面很小、且都是本轮遗漏/新引入的），还是就此转卡。
2. **H2 选甲（补 `st_rdev`）还是选乙（契约收窄 + 登记）。**
3. **禁写链那三处（`V:820/1371/1383`）是否本卡处理** —— 我在最后一轮**刻意没动**，
   理由是那条链已 fail-closed、Codex 也写了「未实证写穿」，在最后一轮动本卡最重的防线风险大于收益；
   但 Codex 指出我「最坏多拒一次」这个说法**比证据宽**，该收窄的是表述，不是防线本身。
