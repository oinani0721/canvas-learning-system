# CARD-RV-G2-6 (b) — `c4e6b165` 零外审整改逐条定性表

> 复审对象：`git diff ff105706 c4e6b165 -- . ':(exclude)_bmad-output'` = 2 files **+453/−50**（Codex r3 审的是 `ff105706`，此后的整改**未再送外审**）。
> ⚠️ **绑定限定（Codex round-1 LOW 更正）**：下表的 file:line 与「旧 rc」是 **`da690bf8` 开工快照**上的实测值 —— 那一刻 HEAD 的四个代码文件与 `c4e6b165` **逐字节相同**（两路交叉证：`git diff --stat` 空 + `git show "c4e6b165:<path>" | shasum` 四条 SAME，见 `minute0-head-proof-20260908T064317.txt`）。本卡随后改动了其中三个文件，**最终 HEAD 已不再与 `c4e6b165` 逐字节相同**；下表行号一律按开工快照读，不按末态读。
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
| #25 | `_iter_relative()` 丢弃遍历错误类型：读不动的目录里藏着 exclude 项不会被报出来 | ⚠️ **本行的原处置「登记，不修」已作废** —— Codex round-1 把它判为 HIGH，**round-2 已修**（`_iter_relative` 增 `unreadable` 出参并透传到 `hits_for` → `verify()`，跨 exclude 项去重）；round-3 进一步补上了「祖先目录不可搜索 ⇒ 连扫描根都 stat 不到」这个更早的入口（见 §六）。详见 §六与 §七 |

## 五 结论

- **P1 = 0**（无「整改不成立/缺陷仍在」）；**P2 = 1**（R3-10，选登记）；**登记 = 9**。
- `c4e6b165` 的 8 条代码整改在 HEAD 上**逐条复现为「指控不成立」**，17 条新门数目与实跑对齐，其中被本卡机械变异实证承重的 1 条（M-LOW9 KILLED）、实证不可区分的 1 条（M-LOW10 SURVIVED + 正控）。
- **本卡未做的复审面（如实）**：其余 15 条新门只核了「存在 + collected 数 + 锁哪条整改」，**没有逐条做变异**证明它们各自承重；r3「其余核对结果」里的 AST 门评述、`resolve()` 版本相关观察未独立复验。

---

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
