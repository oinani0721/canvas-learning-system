# CARD-RV-G2-6 (b) — `c4e6b165` 零外审整改逐条定性表

> 复审对象：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'` = 2 files **+453/−50**（Codex r3 审的是 `ff105706`，此后的整改**未再送外审**）。
> HEAD 与 `c4e6b165` 的四个代码文件**逐字节相同**（两路交叉证：`git diff --stat` 空 + `git show "c4e6b165:<path>" | shasum` 四条 SAME），故下表的 HEAD file:line 就是 `c4e6b165` 的位置。证据 `evidence-rv-g26/minute0-head-proof-20260908T064317.txt`。
> 定性口径：**P1** = 整改不成立 / 缺陷仍在（本卡修）；**P2** = 整改成立但引入或残留新边界（本卡修或登记，逐条写明选哪个）；**登记** = 成立且无新边界。

## 〇 先解 UAT 自身的三套口径矛盾（本卡取 8 + 17）

| 口径 | UAT 位置 | 说法 | 本卡裁定 |
|---|---|---|---|
| 整改条数 | `:522` | 「其中 8 条是代码/清单缺陷，2 条 LOW 是门缺口」 | ✅ **取 8**（代码缺陷口径） |
| 整改条数 | `:656` | 「这一轮**十条**整改 + 17 条新门」 | ⚠️ 「十条」是**含 2 条门缺口的全部结论条数**（3B+1H+3M+3L=10），不是代码缺陷数——非笔误，是口径不同 |
| 新门条数 | `:577` | 「八条整改 + **16** 条新门」 | ❌ **笔误**。实测 12 个新 `def test_`，其中 2 个参数化展开成 4+3 ⇒ 12−2+7 = **17**；`68+17 = 85` 与 `:562`/`:87` 的「85 passed（42→68→85）」同源 |
| 新门条数 | `:562` / `:87` | 「测试 68 → 85 条」= +17 | ✅ **取 17**（实测口径，见下 §三） |

判据（本卡实测 2026-09-08）：`pytest --collect-only` 全文件 **85 tests collected**；12 个新 `def` 的 collected 逐条为 1/1/1/1/1/1/**4**/**3**/1/1/1/1，合计 **17**。

## 一 Codex r3 十条结论 × 在 HEAD 上的复现定性

复现脚本 = `evidence-g26/g26_verify_r3_claims.py.txt` 复制到 scratch 去后缀跑一次；**唯一改动 = `WT` 由 `card-y9-maingoal` 改指 `card-u3-deploy`**（diff 只 1 行，已存档），断言一字未改。跑前自证读取面：`grep -n 'canvas-vault' <脚本>` → **0 命中**（只造 tmp 夹具，不碰 live）。输出：`evidence-rv-g26/r3-claims-on-HEAD-20260908T064916.txt`。

| # | 级别 | 原指控（一句） | 整改落点 HEAD file:line | 定性 | 依据（复现输出行） |
|---|---|---|---|---|---|
| R3-1 | BLOCKER | 大小写目录别名（`--vault …/vault --report …/VAULT/x`）绕过禁写检查，rc=0 且报告落进 vault | `scripts/verify_vault_install.py:835` `_fs_identity`（`(st_dev,st_ino)`）+ `:876-880` 身份优先判 | **登记** | `R3-1 不成立 — 已拒绝`：`rc=2  vault 内被新建 report.txt = False  Dashboard 未变 = True` |
| R3-2 | BLOCKER | `O_EXCL` 失败后 `unlink(tmp)` 删掉**别人的**文件，rc=2 但原文件已毁 | `:590`（临时名带 pid+`os.urandom(4)`）、`:596/:599` `created` 标志、`:615` 只清本次创建 | **登记** | `R3-2 不成立 — 没删别人的文件`：`rc=0  别人的临时文件还在 = True` |
| R3-3 | BLOCKER | 禁写根不覆盖两层软链；扫描失败被忽略。两例均 rc=0 且改变被审树可见内容 | `:522` `SYMLINK_FOLLOW_DEPTH=4`、`:525-...` `_forbidden_roots` 递归+身份去重、`:857/:862/:868-870` 扫描没跑完即拒绝落盘 | **登记** | ① `rc=2  vault 经两层链看到新文件 = False`；② `rc=2 >>> 不成立 — 扫不完就拒绝` |
| R3-4 | HIGH | 两侧同名普通文件均 `000` 权限、内容不同 ⇒ `drift=[]`、`unreadable=[]`、**rc=0**（假绿） | `:452` `_leaf_digest` 改返 `(摘要, 是否读不动)`；`:494-496` 顶层分支登记、`:512-514` 循环内登记 | **登记** | `drift=0  unreadable=2  exit=1` → `R3-4 不成立 — 已登记并阻断` |
| R3-5 | MEDIUM | 单次 `os.write()` 忽略短写，`RLIMIT_FSIZE=1` 下发布 1 字节的截断报告 | `:601-602` `while written < len(data)` 循环写满后才 `os.replace` | **登记** | `RESULT raised 报告落盘失败: …` → `R3-5 不成立 — 短写被发现并报错` |
| R3-6 | MEDIUM | 清单 `source="\ud800"` 逃出 rc=2（写报告时 `UnicodeEncodeError`）并留下临时文件 | `:154` `_require_encodable` + 五个调用点 `:234/:250/:255/:287` | **登记** | `rc=2  落点目录残留 = []` → `R3-6 不成立` |
| R3-7 | MEDIUM | `extra_scan.dir="."`/`"./"`/`".//"` 拼出 `./a`，已声明条目被误报 extra、rc=1 | `:192` `if normalized == ".":` 归一为根 `""` | **登记** | 三态全 `extra=[]` |
| R3-8 | LOW | 悬空软链形态的精确 exclude（`learning_events.jsonl` / `workspace.json`）不登记，后者还被 extra 豁免、rc=0 | `:439` `present = target.exists() or target.is_symlink()` | **登记** | 两项 `= True`，`extra=[] exit=0` → `R3-8 不成立` |
| R3-9 | LOW | **门缺口**：删掉清单 `raw/**`/`templates/**` 后当时 68 条仍全绿 | 补门 `backend/tests/unit/test_vault_install_manifest.py:1094` `test_skeleton_content_excludes_are_pinned` | **登记** | 本卡变异 **M-LOW9**：删这两条 ⇒ 点名门 **KILLED**，`^E` 行 = `AssertionError: raw 下的遗留内容必须被登记为「故意不复制」` / `assert 'raw/**' in []`；跑前跑后两文件 sha 逐个 SAME |
| R3-10 | LOW | **门缺口**：方括号测试的集成部分用的是 `outputs/**`，没有真正含 `[` 的声明 ⇒ 「变异变红」不证明行为回归 | 补门 `…test_vault_install_manifest.py:1111` `test_bracket_exclude_declaration_works_end_to_end` | **P2 → 选「登记」** | 本卡变异 **M-LOW10**（`GLOB_CHARS "*?"→"*?["`）：补门 **SURVIVED**。**正控证明变异确实生效**——同一变异把既有门 `:867` `test_bracket_is_literal_in_both_places` 打红（`^E AssertionError: \`[\` 不再算通配符`）。见 §二 |

**小计：8 条代码缺陷整改全部成立（R3-1~R3-8 = 登记），2 条门缺口 1 条 KILLED、1 条 P2 登记。P1 = 0。**

## 二 R3-10 的 P2 详解（唯一非纯登记项）

- **为什么 SURVIVED 是真的**：补门声明的规则是 `outputs/[draft].json`。`GLOB_CHARS="*?"` 时 `_has_glob` 为 False ⇒ 走 `hits_for` 的**精确分支**（`:437-441`）；`GLOB_CHARS="*?["` 时为 True ⇒ 走**glob 分支**（`:442-448`），而 `_pattern_to_regex` 对 `[` 走 `re.escape`（`:329`）当字面量、`_static_prefix` 在 `[draft].json` 处 break 得到前缀 `outputs`。**两条路径对该输入产出同一结果**，所以这条门物理上看不见这个变异——不是门写坏了，是**输入选得不能翻转**。
- **r3 的修复建议是三维**（分类 / 摘要过滤 / `a.json` 负例），补门覆盖了**分类 + 负例两维**，**「摘要过滤」那一维未覆盖**。
- **承重的仍是既有门 `:867`**（`assert not vv._has_glob("outputs/[abc].json")`）——Codex r3 说的「常量断言」指的就是它；HEAD 与 `ff105706` 全文件 `grep -n 'GLOB_CHARS'` 都**只有一处 docstring 命中**（`:863`），**没有**独立的常量相等断言。
- **本卡选「登记」不修**：修它要么改补门的声明输入（会动 `c4e6b165` 的门语义、超出本卡 (c)-(f) 范围），要么加第 11 条门（卡文 (g) 钉死 ①~⑩）。登记进「未证明」与台账。

## 三 17 条新门 × 各自锁住哪条整改

| # | 门 nodeid（HEAD 行号） | collected | 锁住的整改 |
|---|---|---|---|
| 1 | `test_case_insensitive_alias_is_refused` (:927) | 1 | R3-1 身份比较 |
| 2 | `test_exclusive_create_failure_does_not_delete_someone_elses_file` (:943) | 1 | R3-2 只清本次创建 |
| 3 | `test_two_hop_symlink_target_is_refused` (:974) | 1 | R3-3① 递归展开 |
| 4 | `test_incomplete_safety_scan_refuses_to_write` (:987) | 1 | R3-3② 扫不完拒绝落盘 |
| 5 | `test_both_sides_unreadable_plain_files_still_block` (:1008) | 1 | R3-4 顶层叶子登记 |
| 6 | `test_short_write_is_detected` (:1028) | 1 | R3-5 循环写满 |
| 7-10 | `test_unencodable_string_in_manifest_exits_2[source|role|origin|note]` (:1053) | **4** | R3-6 可编码校验（四个字段各一） |
| 11-13 | `test_extra_scan_dot_is_normalized_to_root[.|./|.//]` (:1072) | **3** | R3-7 `.` 归一（三种写法各一） |
| 14 | `test_dangling_symlink_exclude_is_registered` (:1082) | 1 | R3-8 悬空软链存在性 |
| 15 | `test_skeleton_content_excludes_are_pinned` (:1094) | 1 | R3-9 门缺口（本卡 M-LOW9 证承重） |
| 16 | `test_bracket_exclude_declaration_works_end_to_end` (:1111) | 1 | R3-10 门缺口（本卡 M-LOW10 证**对 GLOB_CHARS 不可区分**） |
| 17 | `test_unreadable_leaf_inside_directory_is_registered` (:1135) | 1 | R3-4 循环内叶子登记（UAT 记的 M21「变异与测试路径不匹配」的补门） |
| | **合计** | **17** | 68 + 17 = **85**，与实跑一致 |

## 四 UAT「未证明」#19 / #25 的处置

| # | 内容 | 本卡处置 |
|---|---|---|
| #19 | 测试文件头注写于 round-1，未随钉死点扩充更新；UAT 说「留到 round-3 有结论之后再补一个纯注释 commit」——**该 commit 从未做** | **本卡 (i) 还上**：头注按现状重写并列出本卡新增门。已不存在「改它会让 round-3 绑定失效」的理由（round-3 早已结束且本卡就是它的复审） |
| #25 | `_iter_relative()` 丢弃遍历错误类型：读不动的目录里藏着 exclude 项不会被报出来（`:376-386`，与 `_digest` 的 unreadable 登记不同口径） | **登记，不修**。落点检查那条路径已因 `_forbidden_roots` 的 failures 拒绝落盘；exclude 分类这一路仍静默跳过。修它要改 `_iter_relative` 签名并波及 `hits_for`，超出本卡 (c)-(f) 范围 ⇒ 进「未证明」与台账 |

## 五 结论

- **P1 = 0**（无「整改不成立/缺陷仍在」）；**P2 = 1**（R3-10，选登记）；**登记 = 9**。
- `c4e6b165` 的 8 条代码整改在 HEAD 上**逐条复现为「指控不成立」**，17 条新门数目与实跑对齐，其中被本卡机械变异实证承重的 1 条（M-LOW9 KILLED）、实证不可区分的 1 条（M-LOW10 SURVIVED + 正控）。
- **本卡未做的复审面（如实）**：其余 15 条新门只核了「存在 + collected 数 + 锁哪条整改」，**没有逐条做变异**证明它们各自承重；r3「其余核对结果」里的 AST 门评述、`resolve()` 版本相关观察未独立复验。
