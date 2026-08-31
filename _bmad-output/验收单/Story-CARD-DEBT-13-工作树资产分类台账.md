# CARD-DEBT-13 验收单 — 工作树资产分类台账

> **批次**: BATCH-2026-08-31-第七批 · **车道**: V7 (`card-v7-debt`)
> **基线**: `9cf0fb85`（本 worktree HEAD）
> **性质**: 只读盘点 + 台账文档，零代码行为改动
> **产出**:
> - `scripts/census_worktree_assets.py`（新增，只读盘点器）
> - `_bmad-output/审查/2026-08-31-DEBT-13-工作树资产分类台账.{md,json}`（台账）
> - `_bmad-output/审查/2026-08-31-DEBT-13-复跑diff.{md,json}`（复跑证据）
> - `_bmad-output/审查/codex-review-CARD-DEBT-13.md`（审查存档）

---

## 一、完成条件逐条对照

### (a) 只读盘点脚本 + 台账 + 机械对账

| 要求 | 状态 | 证据 |
| --- | --- | --- |
| 新建 `scripts/census_worktree_assets.py`（只读） | ✅ | 脚本对被盘点仓只执行 `status`/`rev-parse`/`ls-tree`/`cat-file`/`hash-object`/`log`，全部带 `--no-optional-locks` |
| `--pin-sha` 基线校验 | ✅ | `--pin-sha main=a55db2ab --pin-sha feature=7f5095fd` 通过；**验伪**：故意传 `ctrl=deadbeef` → `rc=2` + `ASSERTION FAILED: --pin-sha 基线校验失败` |
| `--baseline` diff | ✅ | `2026-08-31-DEBT-13-复跑diff.md` §八；**验伪见 §三 正向对照** |
| feature worktree + 主仓全部 tracked 变更与 untracked 逐条分类 | ✅ | main 2027 条 / feature 106 条，全部落四类 |
| 四类归类 | ✅ | 用户资产 / 审查产物 / 应提交代码 / 临时物；规则表 28 条（顺序敏感，每条记录标注命中的规则 id） |
| 台账 md + 机读 json 落 `_bmad-output/审查/` | ✅ | 两份同名文件已落盘 |
| 分类计数与 `git status --porcelain -uall -z` 机械相等，脚本内置 exit 2 断言 | ✅ | 见下方断言矩阵（Codex round-1 后扩到 7 条）；各门承重性由变异测试实证（§三） |
| 每条「应提交代码」标 owner 卡/批次 | ✅（带诚实保留） | 应提交代码条目**无一条缺 owner 字段**；少数 owner 值是显式的 `未分配·需裁定`（逐条列在 §四），不是遗漏 |

### (b) 只登记，禁删除禁移动

| 要求 | 状态 | 证据 |
| --- | --- | --- |
| 脚本跑前跑后两次 porcelain sha256 相等 | ✅ | 定稿台账：main `58a84013026f200a…` == `58a84013026f200a…`；feature `7d8aed4dec7c3fa3…` == `7d8aed4dec7c3fa3…`。⚠️ main 的值在作业期间由 `86f44f5a…` 变为 `58a84013…`——不是脚本改动，是**夜间 Neo4j 备份轮转**（2 个 08-24 dump 出、2 个 08-31 dump 入，记录数仍 2027、HEAD 未动）。这次真实变化正好让复跑 diff 有了非零内容，见 §三 |
| 主仓 869 条 tracked 删除标注为「未决搬迁」而非「已决归档」 | ✅ | 台账「⛔ 使用前必读」第 1 条 + §四全节；每条删除带内容级取证 |
| 全程不清理 `~/.claude/auto-sync.lock.d` | ✅ | 该路径在本卡全部作业中零触碰；台账「必读」第 2 条把它写成硬警告 |
| 不碰主仓工作树内容 | ✅（带如实登记） | 产出全部落**本 worktree**（`card-v7-debt`）的 `_bmad-output/审查/` 与 `scripts/`。⚠️ 本 worktree 物理上位于主仓目录树内，但被主仓 gitignore 排除、不进其 porcelain——脚本已把这一点从「静默通过」改为**显式前置检查 + 台账登记**（json `out_dir_nested_in_target_but_gitignored`），不再笼统宣称「零交集」 |

### (c) 裁判

| 要求 | 状态 | 证据 |
| --- | --- | --- |
| 台账零漏项（对账断言过） | ✅ | 两目标 × **七条**断言全 PASS |
| 可复跑（`--baseline` 二跑 diff 说明变化） | ✅ | 定稿复跑以作业中途（04:13）的台账为基线，**diff 有真实非零内容**：main 新增 2 / 消失 2 / 改类 1 / **整条 entry 有任一字段变化 89 条**。⚠️ 这 89 条**不是工作树变了 89 处**，而是各轮整改改变了判定/字段：`feature_branch_state` 79 条（F2 新增字段）、`owner` 75 条、`disposition` 79 条、`relocation` 6 条（F5/F6）、`category`+`rule` 各 1 条（B-2）。真正的工作树变化只有 added 2 / removed 2（夜间 Neo4j 备份轮转）。基线内容身份已绑定：sha256 `f8ee049256ed9585…`、2201641 字节，**同一份读入的字节既用于算 digest 也用于本次 diff**（round-5 F4 促成）。另有两条正向对照证明 diff 在有变化时会红（§三） |

---

## 二、断言矩阵（实跑结果）

**12 条断言，两目标全 PASS**（原 8 条 + 第 6 轮新增 4 条），且全部列入 `REQUIRED_ASSERTIONS`
必需清单——**缺任何一条即 FAIL**（此前某条门的赋值被删掉后 rc 仍是 0、矩阵格子退化成 `n/a`，
与「pin 未传」的合法 n/a 无法区分）：

| # | 断言 | 挡什么 |
| --- | --- | --- |
| 1 | `pin_sha_ok` | HEAD 不是预期基线 |
| 2 | `parsed_count_matches_independent_count` | 记录数与**独立命令**不符 |
| 3 | `orig_field_iff_rename_or_copy` | orig 挂错记录（⚠️ 对数据恒真，只对解析器代码有鉴别力） |
| 4 | `xy_sequence_matches_independent_parse` | 字段分组错但字节序不变 |
| 5 | `count_equals_porcelain_records` | 有记录没进分类 |
| 6 | **`entries_preserve_record_identity`** | **records → Entry 的 `(xy, path, orig)` 三元组整列写错**（第 6 轮 A1） |
| 7 | **`content_evidence_independently_recomputable`** | **内容取证层整体失效**——独立重算 OID 比对（第 6 轮 A2） |
| 8 | **`relocation_evidence_self_consistent`** | 判定与证据字段自相矛盾（第 6 轮 A2） |
| 9 | `roundtrip_bytes_identical` | 互相抵消的解析错误（⚠️ 同为对数据恒真） |
| 10 | **`feature_ref_resolvable_or_declared`** | **feature 三态证据源静默缺席**（第 6 轮 F2-A） |
| 11 | `filter_drivers_absent_or_accepted` | 自定义 filter 驱动会在取证时被执行 |
| 12 | `readonly_porcelain_unchanged` | 盘点改动了被盘点工作树 |

外加 `--rule-coverage` 自检：两目标全部 tracked 路径（main 4325 / feature 5423）catch-all 命中 **0 条**。

（`orig⇔R/C` 由 round-2 A-3 促成；「filter 无或已接受」原名 `no_custom_filter_drivers`，
round-4 指出 allow 模式下它把「风险被接受」说成「驱动不存在」，已更名为如实语义。）

（`orig⇔R/C` 一列由 Codex round-2 A-3 促成；round-3 又指出 md 矩阵漏列了它，已补。）

外加 `--rule-coverage` 自检：把两个目标的**全部 tracked 路径**（main 4325 / feature 5423）喂进规则表，
catch-all 命中 **0 条**（整改前 1772 条）。`--strict-rules` 下命中即 exit 2。

每道门各挡一类错误：

- **独立计数** — 记录数取自不带 `-z` 的 `git status --porcelain -uall` 行数，**不从解析结果自己推导**。
- **orig⇔R/C** — `orig is not None` 当且仅当 XY 含 R 或 C。挡「XY 序列、字节往返、计数三门同时成立，但 orig 挂错了记录」（Codex round-2 A-3 促成新增；变异 M11 证明只有这道门能抓住它）。
- **XY 序列** — 每条记录的两字符状态码序列 ⟷ 同一条独立命令的逐行行首。挡「字段分组错但字节序不变」（Codex round-1 A-3 促成新增）。
- **分类对账** — 分类条目数 == 记录数，挡「有记录没进分类」。
- **字节往返** — 解析结果重新序列化回 `-z`，与 git 原始输出逐字节相同，挡「少解析一条 + 多分一条」这类互相抵消、计数看不出来的错误。
- **无自定义 filter** — `--no-optional-locks` 不是只读沙箱；自定义 clean/process 驱动会在取证时被 git 执行、可留下副作用（且副作用若被 gitignore 覆盖，前后 porcelain sha256 仍相等 → 只读取证假绿）。检出即 exit 2（Codex round-1 A-2 促成新增）。
- **只读取证** — 前后 porcelain sha256 相等。**它只证明两个时点的 `(XY, path[, orig])` 字节相同**，不证明内容/ignored 文件/refs/配置未变，也无法归因；真正的只读保证靠「脚本无写路径 + filter 断言 + 产出目录前置检查」三者合力。

---

## 三、门的承重性实证（变异测试 + 正向对照）

变异全部作用在脚本**副本**上（`scratchpad/mutant.py`），原文件字节自始至终未变（跑完 sha256 复核）；串行执行。

| 变异 | 注入的错误 | rc | 触发的门 |
| --- | --- | --- | --- |
| M1 | `parse_porcelain` 丢掉最后一条记录 | 2 ✅ | 独立计数 + XY 序列 + 分类对账 + 字节往返 |
| M2 | `Record.serialize` 漏掉结尾 NUL | 2 ✅ | 字节往返 |
| M3 | 盘点后的 porcelain 被追加内容 | 2 ✅ | 只读取证 |
| M4 | 分类循环丢掉最后一条记录 | 2 ✅ | 分类对账 |
| M5 | 记录数改回从解析结果推导（**阴性对照**：只削弱门的独立性，不产生实际错误） | 0 | 无——**正确的绿**，证明变异套件不是恒红 |
| M6 | M1 + M5 叠加 | 2 ✅ | XY 序列 + 字节往返 |
| M7 | XY 序列门的期望值改为自比（**阴性对照**：门失效但输出仍正确） | 0 | 无——同为正确的绿 |
| M8 | 解析器不消费 rename 的来源字段（分组错、字节序不变） | 2 ✅ | 独立计数 + orig⇔R/C + XY 序列 + 分类对账；**字节往返此时是绿的** |
| M14 | feature 三态的 OID 比对失效，退回「存在即同内容」 | 输出对照 ✅ | `diverged` 由 **20 变 0**——20 条内容分歧全被说成同内容。证明这段比对承重（round-5 F2 促成） |
| M15 | `path=(r.orig or r.path)`：Entry 的 path 整列换成 orig | 2 ✅ | `entries_preserve_record_identity`。**整改前八门全 PASS**——台账把 rename 的目的地整条换掉而无人知晓 |
| M16 | `path=r.path[:-1]`：Entry 的 path 整列截尾 | 2 ✅ | 同上 |
| M17 | `unt_blobs = {u: None …}`：内容取证整体瞎掉 | 2 ✅ | `content_evidence_independently_recomputable`。**整改前八门全 PASS**——`moved_identical` 翻成 `no_candidate` 而无人知晓 |
| M19 | 内容索引被污染（全换成假 OID） | 2 ✅ | 同上 |
| M18 | 删掉一条门的赋值 | 2 ✅ | 「缺失必需断言」——此前断言可以**静默消失**，rc 仍是 0 |

**16 项全符合预期，0 条不符。**
| M9 | `orig⇔R/C` 门改为恒真（**阴性对照**） | 0 | 无——正确的绿 |
| M10 | filter 检测恒返回空，在**配了 `filter.side.clean` 的真仓**上跑 | 2→0 ✅ | 未变异时 rc=2；变异后该仓放行 → **证明这道门承重** |
| M11 | 让 `??` 记录也吞下一个字段（orig 挂错记录） | 2 ✅ | **只有 `orig⇔R/C` 一门变红**——正是它存在的理由 |

**M6 / M8 / M17 是最有信息量的三条**：
- M6 说明期望值一旦不独立，两条计数门同时哑火——这就是脚本坚持用独立命令取记录数的理由。
- M8 说明字节往返**不是万能**：分组错而字节序不变时它照常绿，只有 XY 序列门能抓住。
- **M17 说明「内部一致性」不是证明**：`content_evidence_independently_recomputable` 的第一版只查
  内部一致性，实测**没抓住** M17——取证瞎掉后的输出内部是自洽的（它只是说「没找到副本」，
  而这在没有独立信息源时无法证伪）。重做成「另起一次 `git hash-object` 独立重算」后才变红。
  **我在计数门上学会「期望值必须来自被验证对象之外」，却在取证层又犯了一次。**

三条阴性对照（M5/M7/M9）保持绿，证明这套变异不是恒红。

**复跑 diff 的两条正向对照**（临时仓，不碰真实仓库）：

1. **路径集合变化**：建 2 条记录的仓 → 跑 1 → 新增 1 个 untracked + 删除 1 个 tracked → 跑 2 带 `--baseline`。结果：porcelain sha 由 `c53af5af…` 变为 `00a62991…`，记录数 2 → 4，diff 正确列出新增 `docs/new.md` 与 `backend/b.py`。
2. **只有内容变、porcelain 字节不变**（Codex round-2 指出的漏检面）：只把一个未跟踪文件的**内容**改成与被删文件相同——porcelain sha、记录数、category 全部不变，而 entry 级 diff 正确报出 2 条变化（`docs/x.md`: disposition+relocation；`archive/zzz.md`: disposition+owner+relocation）。原来只比 path+category 的实现在这里是全零的。

### 解析器边界实测（临时仓，两个真实仓里没有这些形态）

| 形态 | 实测结果 |
| --- | --- |
| **rename（`RM`）** | `-z` 实际输出 `RM renamed.md\0orig.md\0`（新路径在前、原路径在后），解析器的 path/orig 赋值与之一致；非 `-z` 输出 `RM orig.md -> renamed.md` 占 1 行 → **独立计数与 `-z` 记录数一致**，rename 不会让计数门误报 |
| **未合并冲突态（`UU`）** | 单字段单记录，解析与分类正常 |
| **路径含换行符** | 非 `-z` 侧 git 会加引号转义成 `"we\nird.md"` 占 1 行，`-z` 侧逐字输出 → **两侧记录数仍相等**；但含换行的路径走不了 git 的按行 batch 协议。首版实现是直接 `raise` 中止整个盘点——已改为**只降级取证、不降级覆盖**：该条目照常进分类与对账，只是没有内容级搬迁/副本取证，并在台账与控制台显式登记条数与路径。取证拿不到可以接受；整份台账因为一个文件名不产出不可接受。 |

两个真实目标本次均无含换行路径（`evidence_skipped_newline_paths` 为空）。

---

## 三·五、Codex round-1 的 1 BLOCKER + 5 HIGH 与整改

审查存档：`_bmad-output/审查/codex-review-CARD-DEBT-13.md`（round-1 原文 + 逐条整改回执 + round-2）。
round-1 判 **A=FAIL/BLOCKER · B=FAIL · C=FAIL**，全部整改并各配正向对照。三条最该被看到的：

**C-1（HIGH）— 首版台账里有一条假陈述。** 原 8MB 哈希上限把
`docs/architecture/backend-overview.png`（16,420,168 字节）排除在内容索引之外，于是它被 basename
兜底判成 `same_name_diff_content` 写进了台账——而它与归档区同名文件的 blob sha **同为 `d7b8cb4d`，
本是内容同一的位移**。整改：上限提到 128MB；更要紧的是**超限不再退回内容判定**，改走独立判定
`evidence_skipped_size`（语义 = 「本台账对该条没有内容结论」）。正向对照：把上限改回 8MB 重跑，
该 PNG 判 `evidence_skipped_size`；128MB 下判 `moved_identical / content_sha`。

**A-1（BLOCKER）— 只读硬边界有确定性绕过路径。** `--out-dir` 与 `--target` 原先无任何检查，
`--target victim=X --out-dir X` 会在只读取证取完**之后**往被盘点工作树写台账，PASS 是假绿。
整改时我把判据比 Codex 提的更收紧了一档：真正的不变量不是「路径是否嵌套」，而是
**「产出会不会进该目标的 porcelain」**——用 `git -C <target> check-ignore -q` 判定，未被排除 → 在跑
任何 git 命令之前 exit 2；被排除 → 放行但**如实登记**，不再宣称「零交集」。这一改让本卡自己的
默认跑法（out-dir 在主仓目录树内、但被主仓 gitignore 排除）从「静默通过」变成「显式登记的例外」。

**A-3（HIGH）— 三门可以全绿而语义漏掉 rename。** 一个把 NUL 字段**分组错**的解析器，只要字节序不变，
就能同时骗过计数门和字节往返门。整改：新增独立门 `xy_sequence_matches_independent_parse`。
**正向对照按 Codex 给的形态造了真仓**：文件旧名字面上就是 `?? fake`，rename 后 `-z` 输出恰为
`b'A  aaa\x00R  zzz\x00?? fake\x00?? yyy\x00'`；把解析器 rename 分支改成 `if False` 后实测——
**字节往返仍绿**，XY 序列门与独立计数门同时变红。这条正向对照本身就是「字节往返不是万能」的实证。

**整改中我自己踩的一次规则碰撞（如实登记）**：B-2 拆 `.obsidian/` 时，U9 的密钥子串启发式
（`key`/`secret`/`token`）排在 C11 精确文件名白名单之前，`hotkeys.json` 的 basename 含子串 `key`，
于是这份 `.gitignore` 明令保留受控的配置被判成了设备密钥。已把精确白名单前置并把教训写进代码注释。

整改后断言矩阵扩到 7 条，两目标 **7×2 全 PASS**。

---

## 三·六、Codex round-2 的第二轮 BLOCKER/HIGH 与整改

round-2 判 **FAIL**：A-1 仍 BLOCKER，A-4/B-2/C-1 为 HIGH，另抓出两条我方自己没看见的问题。
逐条整改见审查存档的「我方 Round-2 整改回执」表。最该被记住的四条：

**又一条台账不实陈述。** 首版「必读」第 3 条写「untracked 文件不在任何 git 对象里，一旦被清理
就没有任何还原路径」——**台账自己的数据就否证了它**：主仓 1139 条未跟踪里，位移目的地 863 条
加已受控内容副本 72 条，内容都与 HEAD 中某个 blob 完全相同，那部分是可以还原的。已改为如实分档。
同批改掉的还有：`readonly: true` 这个无条件断言（换成分层的 `readonly_guarantees`，显式列出
**不能证明**的六项）、「在任何 git 命令之前」（判定自身就要调 `git check-ignore`，改为「任何**盘点**
命令之前」）、写着 `rev-parse` 实际用 `cat-file --batch-check`、PNG「本是位移」（blob 相等只证明
内容同一、不证明因果方向）、以及僵尸锁「唯一阻挡」（改标为**转述**，本卡按只读边界未读 home 目录，
该点在本卡内属 UNVERIFIABLE）。

**复跑 diff 是个漏检面。** 它只比 path 与 category，于是同一路径的 `relocation.verdict` 从
`no_candidate` 变成 `moved_identical` 也照样显示「改类 0」——而未跟踪文件的**内容**改变根本
不会改动 porcelain 字节。已改为比较整条规范化 entry（10 个字段）。**正向对照**：造仓只改一个
未跟踪文件的内容，porcelain sha 与记录数完全不变、category 也不变，新 diff 正确报出 2 条变化。

**「无结论」的枚举原来不完整。** 首版只把「超限且同名」记为无结论，而 symlink、非普通文件、
`stat` 失败、含换行路径这些候选缺席时，仍会给出 `no_candidate` 这种**肯定性结论**。现在引入
**未哈希池**（逐条记原因），**只要池非空就一律降级为 `evidence_incomplete_pool`**。
两个真实目标的池当前为空——所以现有结论有效，但这句话现在是被验证过的，不是默认的。

**类别继承直接废除。** round-1 我把 A-INHERIT 收窄成三条件，round-2 指出收窄挡不住反例
（65 字节的 `workspace.json` 就能把归档区目的地继承成「临时物」），而且根子上是循环论证——
用内容相等反推来源、再用来源覆盖目的地类别。索性整体废除：目的地一律用自身路径规则判别。
**实测废除后两目标四类计数逐一不变**（原 729 条继承项全是代码→代码），即零代价消掉一整类失败模式。

---

## 三·七、Codex round-3：一条不实回执，以及由此改掉的做法

round-3 判 FAIL（A-1 BLOCKER；A-2/A-4/B-2/C-1 HIGH）。**本轮最该记住的不是代码问题，是我方回执不实**：

> round-3 的整改回执里，B-2 的四项（U11 / C12 / U9 词边界 / C11 限深）被我宣称"已做"，
> 实际上那个补丁脚本在一个锚点上 `assert` 失败、**整体没有写入任何内容**，我却按"已应用"汇报了。
> 复核当场用 `grep` 证伪：`U11`/`C12` 命中 0，U9 仍是裸子串，C11 仍只看 basename。
> 这正是本项目 MEMORY 里记过的「heredoc 批量补丁原子性陷阱」——原子性本身救了代码
> （没有写入半套），但我把它升级成了**「把没发生的事报成已完成」**，那比代码缺陷严重。

**做法已改**：自 round-3 整改起，每个补丁写盘后**逐条回读验证并打印 ✅/❌，全绿才继续**。
本轮 4 个补丁脚本共 24 项回读检查全绿。整改中还自曝一次：B-2 的路径段索引写错一位
（`.obsidian` 在 index 1 不是 2），导致 `manifest.json` 掉进 E6——是回读后的逐条归类实测抓到的。

其余整改要点：

- **A-1 三处**：containment 改用 **st_dev/st_ino 身份**（`os.path.normcase` 在 macOS/Linux 是恒等函数，
  `/Users`↔`/users` 别名因此绕过——实测整改前 rc=0、整改后 rc=2）；`--show-toplevel` 的结果
  **替换回 targets** 贯穿全部取证（原来只保护预检、Python `stat` 仍用 CLI path）；
  sink 改 **`O_NOFOLLOW` 原子打开 + fstat 复核**（实测：预摆符号链接 → rc=2 且目标文件未被覆盖）。
- **C-1**：新增 `evidence_incomplete_head`——HEAD 侧拿不到 blob（含换行路径、gitlink）时一律无结论。
- **brief baseline**：基线无 entries 时不再按空集合算，否则会把全部条目假报成 added（实测假报 2027/106）。
- **「不可还原」表述再修一次**：round-2 我改成「内容不在 HEAD 里的才不可还原」，round-3 指出
  同内容 blob 可能在**别的 ref** 里。最终口径：**本台账能证明「可还原」，不能证明「不可还原」**。

---

## 三·八、Codex round-4：把「边界」和「没修」分清楚

round-4 判 FAIL（A-1 BLOCKER；A-2/A-4/B-2 HIGH）。本轮先确认了 round-3 的补丁**确实落盘**，
问题转为「只修了主路径，没闭合敌对交错与报告面」。可低成本修的全部修了：

- **sink 顺序反了**：原来带 `O_TRUNC` 打开、之后才 `fstat`——若 sink 被换成受害文件的硬链接，
  等发现 `nlink>1` 时对方已被清空。改为**不带 `O_TRUNC` 打开 → 验身份 → 通过后才 `ftruncate`**；
  `nlink` 由「拒 >1」改「必须恰好 ==1」（并发 unlink 后的 0 原本会被放行）；短写循环补齐；
  两份内容先全渲染再落盘（原来 md 渲染失败就只剩半份 json）。
- **`git_text().strip()`** 会把仓路径末尾的空格/NBSP 裁掉，让「解析出的真实根」悄悄换个仓。已改。
- **`no_candidate` 证不出否定命题**：新增判定 `content_still_in_head`——被删 blob 若仍在 HEAD 的
  另一个 tracked 路径上，就是「内容可还原，风险是删除被提交」。处置文案里所有「不可由归档区还原」删除。
- **规则面**：删掉重复的 U10（round-3 只做了"复制到前面"、没删旧的）；C11 补 `canvas-vault` 根段约束；
  E10 改按 `images/` 之下**首段**匹配以对齐 `.gitignore`；R4 收窄为 `logs/audit/`、新增 E11 收其余 `logs/`。
- **报告面**：`evidence_incomplete_head` 接入 md 汇总与「无结论的**四种**来源」枚举；
  目的地新增 `content_sha_multi_source_low_entropy`（当前真实数据 3 条）；
  断言更名；label 改**入口约束**字符集；反引号改可见记号；brief 判据改 `isinstance(..., list)`。

**明确声明为边界、没有修的**（bind/nullfs 子树别名、父目录 symlink 替换、并发 unlink）：
台账文首新增「威胁模型」节，写清本脚本的「只读」防的是**误伤**，不防「与本脚本并发运行且对产出目录
有写权限的攻击者」；并明写**「这是声明的边界，不是已解决的问题」**、指出敌对环境下的正解是
`openat` 系绑定目录句柄、属另一张卡的工作量。
（我在别的卡上犯过「拿边界当挡箭牌」，所以这里的判据是：**能低成本修的一律修，只把真正需要换实现路线的
留作边界，并把代价写出来**。round-5 专门请审查者检验这条边界是否诚实。）

---

## 三·九、Codex round-5：台账在 20 条上说了假话

round-5 判 FAIL，价值集中在两条**当前台账的实质事实错误**上。第一条尤其严重：

### ⛔ F2：「主仓落后」在拓扑上根本不成立

台账把 75 条「同路径也在 feature 分支受控」的未跟踪文件一律判为「主仓落后」。
Codex 实测其中 **20 条内容不同**。我方独立复算完全一致，并补出一条更硬的事实：

```
HEAD 是 worktree-feature-obsidian-hybrid-dev 的祖先: 否
worktree-feature-obsidian-hybrid-dev 是 HEAD 的祖先: 否
```

**两个 HEAD 互不为祖先**——「落后」这个说法不只是在 20 条上说错了，而是**整个说法没有依据**。
后果是实的：按它单向覆盖（`-X theirs` 之类）会丢掉主仓侧的改动，其中包括
`canvas-vault/.claude/skills/board-recap/SKILL.md` 与 `recap_scan.py` ——正在被别的卡使用的文件。

整改：存在性布尔 `branch_has_path()` → OID 比对 `branch_blob_oid()` + `worktree_blob_oid()`，
判定拆三态 **`same_blob` / `diverged` / `present_local_unhashable`**；`diverged` 的处置明写
「**禁止单向覆盖，`-X ours/theirs` 一律不适用，须逐 hunk 人审**」；台账新增专节把 20 条分歧逐条列出。

实测 **`same_blob: 59` / `diverged: 20`**，与独立复算 **0 条不一致**。
新增变异 **M14**：去掉 OID 比对退回布尔判定 → `diverged` 由 20 变 0，证明这段比对承重。

### F3：「脚本对目标无写入代码路径」与产出位置自相矛盾

json 里写着 `script_has_no_mutating_code_path_into_targets: true`，而台账**自己**登记了
out-dir 位于主仓的 ignored 子树内——脚本确实对该目标的文件系统执行了 mkdir/open/write。
`check-ignore` 只证明这些写入 **git 看不见**，不等于没写。已删掉那个无条件布尔，
改为 `writes_into_targets`（如实说明仅限 out-dir 产出）+ `porcelain_proof_scope`
（说明 ignored 子树写入不在 porcelain 的证明域内）。

### 其余七条

F1 成对发布（渲染**和编码**全部前移到写盘之前、拒 FIFO、零写报错）· F4 baseline 只读一次 bytes
且产物记 digest/size · F5 `no_candidate` 措辞限定证明域 · F6 HEAD twin 正证据前移 ·
F7 E10 对齐 `core.ignorecase` · F8 baseline entries 三态 fail-closed · F9 label 唯一 ·
F10 allow-mode 文案双含义 · F11 五处漂移。

**留作另立卡**（Codex 自己也划在「需另立卡」）：bind/nullfs mount provenance、
对同目录写权限敌对进程的防护、崩溃下的双文件耐久事务、ignored 内容全扫描。

---

## 三·十、第 6 轮改用多维度并行验证

连续五轮单体外审后，边际发现已从「判据错误」降到「文案漂移」。第 6 轮我改了方法：
**6 个独立验证者并行**（台账事实 / sink 安全 / feature 三态 / 证据链与证明域 / 分类规则 / 断言证明力），
每条 finding 再交给**独立的证伪者**（默认怀疑、不确定即判证伪、已声明边界不算缺陷）。
这比再来一轮同构审查更能覆盖不同失败模式，也能挡住「审查者误读代码」这类噪声。

---

## 三·十一、第 6 轮多维并行验证：八道门只约束「行数」

36 个 agent / 367 万 token / 29 分钟，30 条 finding → **19 条被证伪 / 11 条存活**（证伪率 63%）。

**最重的发现是一个结构性洞**：此前的八道门只把「台账行数」绑回 porcelain，
**完全不约束「行里写的是什么」**。三条独立存活的 HIGH 指向同一处：

| 变异 | 后果 | 整改前 |
| --- | --- | --- |
| `path=(r.orig or r.path)` | 台账把 rename 的**目的地整条换掉** | **八门全 PASS，rc=0** |
| `unt_blobs = {u: None …}` | 内容取证整体瞎掉，`moved_identical` 翻成 `no_candidate` | **八门全 PASS，rc=0** |
| 规则 U5 类别 `CAT_USER → CAT_EPHEMERAL` | 用户资产整类翻成「可安全忽略」 | `catchall_hits` 仍 0，**八门全 PASS** |

已补四道门（见 §二），M15/M16/M17/M18/M19 五条变异逐一证明它们承重。

**另一条不该忽略的**：F1-R1 用 `chmod 444` 与 `ulimit -f 40` **实测复现**了半对产物——
新 json + 旧 md，以及新 json + 被截断的半截 md（且截断后的 md 头部带着**本次的新时间戳**，
让「两份 generated_at 一致」这条自然对账反而通过）。**都不需要并发攻击者**，不属已声明边界。
已改为 tmp + `fsync` + `os.replace` 原子发布。

**台账自己也被抓到一条**：三处仍写「对被盘点仓只做读操作」，与它**自己登记**的嵌套事实矛盾——
本次运行确实往主仓写了 4 个文件，只是被 gitignore 排除、git 看不见。已改为随嵌套事实变文案。

---

## 四、台账实质发现

### 主仓（2027 条 = 19 modified + 869 deleted + 1139 untracked）

| 类别 | 条数 |
| --- | ---: |
| 应提交代码 | 1849 |
| 用户资产 | 126 |
| 审查产物 | 42 |
| 临时物 | 10 |

**⛔ 869 条 tracked 删除是未决搬迁，不是已决归档。** 内容级取证（`git rev-parse HEAD:<path>` 的 blob sha ⟷ 未跟踪文件的 `git hash-object`，同一套 git 内容身份）：

| 判定 | 条数 | 含义 |
| --- | ---: | --- |
| `moved_identical` | 863 | 内容同一副本已落地未跟踪区，搬迁未提交 |
| `same_name_diff_content` | 2 | 同名但内容不同，**不能按搬迁处理**，逐条需人审 |
| `no_candidate` | 3 | 无内容同一副本，**不可由归档区还原**，需用户显式裁定 |
| `evidence_skipped_empty_blob` | 1 | **无结论**：HEAD 侧是空文件，空 blob sha 全仓恒等、无鉴别力，需人工比对 |

> 口径要紧：前三行是**有内容结论**的判定，`evidence_skipped_*` 是**明确的「无结论」**，不得读成任何一种内容判定。这正是 Codex round-1 C-1 抓到的病根——首版把「未取证」混进了「内容不同」，于是一条真实位移被写成了假陈述。

3 条 `no_candidate` 逐条（这是本卡最该被看到的部分）：

- `.claude/skills/research-pack/references/agent-prompts.md`
- `.claude/skills/research-pack/references/keyword-guide.md`
- `_bmad-output/验收单/批注回复/Round-12-Graphiti-vs-Wikilink-双轨检索.md` — **用户批注回复文档**（规则 U7 归用户资产）

2 条 `same_name_diff_content`：`.claude/skills/research-pack/SKILL.md`、`frontend/sidecar/sidecar.js`。
1 条 `evidence_skipped_empty_blob`：`docs/stories/4.5.story.md`（HEAD 侧为空文件）。

**`docs/architecture/backend-overview.png` 已从这张表里移出**——它现在正确判为 `moved_identical / content_sha`（两侧 blob sha 同为 `d7b8cb4d`）。首版把它列在 `same_name_diff_content` 里是假陈述，详见 §三·五 C-1。

> 这些删除的内容仍在 HEAD 里，`git checkout -- <path>` 可原样还原——风险是「删除被提交」而不是「内容已丢」。未跟踪文件则完全不在任何 git 对象里，一旦清理没有还原路径。台账「必读」第 3 条把这条区分写死。

### 未跟踪文件中「已受控内容的副本」

同一套判据反向用一次：main 的 1139 条未跟踪里 **72 条（6%）与 HEAD 中当前仍受控的路径 git blob 身份相同**（即 clean filter 之后的内容同一）——例如 `archive/legacy-tauri-v0/frontend/src/App.tsx` 与 `frontend/src/App.tsx` 同 blob。它们是副本，不是「未入库的新代码」。没有这一步，台账会得出「有大量代码没提交」的错误结论。

### 仍未分配 owner 的 15 条（诚实登记，非遗漏）

| 路径 | 为什么没法自动定 owner |
| --- | --- |
| `archive/legacy-docs/stories/4.5.story.md` | 对应删除项 HEAD 侧为空文件，内容匹配无鉴别力 |
| `archive/legacy-tauri-v0/README.md` | 归档区独有内容，无受控对应 |
| `archive/legacy-tauri-v0/frontend/sidecar/sidecar.js` | 与 tracked 同名但内容不同 |
| `backend/vault/CLAUDE.md` + 4 个 `.gitkeep` | fixture vault 骨架，从未受控、无 commit 可追 |
| `canvas-vault/.obsidian/plugins/*/manifest.json`（6 个） | `.gitignore` 明令保留受控（规则 C11），但当前未跟踪且无 commit 可追 |
| `docs/README.md` | 从未受控、不在任何分支 |

> `canvas-vault/.claude/hooks/pending_archives.jsonl` 已不在此列——Codex round-1 B-1 指出它是**未送达的用户学习会话队列**，现判用户资产（规则 U10），不再要求指认提交 owner。

### feature worktree（106 条 = 8 modified + 5 deleted + 93 untracked）

审查产物 96 / 应提交代码 4 / 用户资产 4 / 临时物 2。5 条删除全部 `no_candidate`（3 个 research-pack skill 文件与 2 份 ChatGPT 任务书/指令）。

### 卡文基线数与本次实测数的漂移（如实登记）

卡文（第六批勘探）记 worktree `99/104`、主仓 `986/2027`。本次实测：feature `13 tracked / 93 untracked / 106 合计`，主仓 `888 tracked / 1139 untracked / 2027 合计`。主仓合计数 2027 与卡文一致，tracked/untracked 的切分口径与卡文不同——卡文数字为参考基线，**本台账以实跑 porcelain 为准**（这正是卡文「动态重数」的要求）。

---

## 五、判别口径与已知边界

**保守优先原则**：分类不确定时归入更受保护的类别。把用户数据错判成「临时物」不可逆；反向只是多留一份。

**踩到并修掉的坑**（记录在案，防复现）：

1. **空文件 blob sha 全仓恒等** — `docs/stories/4.5.story.md` 在 HEAD 里是空文件；不排除的话它会「匹配」工作树里全部 16 个空的未跟踪文件（含用户笔记 `canvas-vault/未命名 1.md`），把用户资产误标成搬迁目的地。已在匹配前剔除，该删除项判 `evidence_skipped_empty_blob`（无结论，不是「内容不同」）。
2. **按 basename 配对是一对多** — 仓里有几十个 `index.md`；首版按 basename 配对时 869 条删除只对上 768 个不同候选，配错就是假证据。改为以内容 blob sha 为准，basename 仅在内容不匹配时用于降级说明。
3. **计数期望值不能来自被验证对象** — 见 §三 M6。
4. **「未取证」不能混进「有结论」** — Codex round-1 C-1：8MB 上限把一条真实位移写成了「同名内容不同」。现在超限走独立判定 `evidence_skipped_size`，语义就是「没有结论」。
5. **内容相等 ≠ 位移因果** — Codex round-1 C-2：低熵内容（`.gitkeep` 之类）会让不相干的两棵树互相配对，再用它反推来源、用来源覆盖目的地类别就是循环论证。现在低熵匹配不驱动继承，`A-INHERIT` 收窄为「目的地在 `archive/` 下 + 来源唯一 + `match_kind == content_sha`」三条件同时成立。
6. **精确规则必须排在启发式之前** — 整改 B-2 时自踩：`hotkeys.json` 的 basename 含子串 `key`，被排在前面的密钥启发式吃掉。

**7. 存在性 ≠ 同内容** — Codex round-5 F2：`cat-file -e` 只证明「feature 分支也有这个路径」，
   却被用来下「主仓落后」的结论。实测 20 条内容不同，且两个 HEAD 互不为祖先。**判据必须匹配结论的强度**。

**8. 正证据不该被无关的缺证据压掉** — Codex round-5 F6：「同内容 blob 就在 HEAD 另一个受控路径上」
   这句话的成立与否，和未跟踪池完不完整毫无关系；把它排在全局 unhashed 门之后，
   一个无关的 symlink 就能把确凿的正证据降级成「证据不全」。

**已知边界（未在本卡解决，逐条声明）**：

| 边界 | 当前实况 |
| --- | --- |
| 未跟踪文件哈希上限 **128 MB** | 超限走 `evidence_skipped_size` = **无结论**（不是 `no_candidate`、也不是「内容不同」）。本次实测 `unhashed_untracked_with_reason` 两目标均为空，即无条目触及。⚠️ 台账不落盘「当前最大未跟踪文件多少 MB」——那是会过期的数值（本轮 Neo4j dump 已比上轮大近 3 MB） |
| **不扫描 ignored 子树** | 候选池 = porcelain 可见且非 ignored 的未跟踪文件 + 本仓 HEAD 的其他路径。实测本仓三条 `no_candidate` 在 ignored 的 worktree 子树里都有同内容物理副本——所以台账只说「本次可见范围内没找到」，**绝不说「不可还原」** |
| **不做全 ref 可达性分析** | 同内容对象可能存在于别的分支。本台账**能证明「可还原」，不能证明「不可还原」** |
| 内容命中多于一条 **133 条** | 标 `content_sha_ambiguous*`，对应目的地标 `content_sha_multi_source*` 并**全列来源**。位移方向由 DEBT-14 人审确定，本卡不替它选 |
| 低熵匹配（blob ≤ 64 字节） | 来源侧 `content_sha_low_entropy` 2 条 / `content_sha_ambiguous_low_entropy` 3 条；目的地侧 `content_sha_multi_source_low_entropy` 3 条。登记为证据，**不驱动任何分类** |
| **类别继承已整体废除** | 首版让归档区目的地继承来源类别，Codex round-2 C-2 指出是循环论证（用内容相等反推来源、再用来源覆盖目的地）。round-3 收窄成三条件仍挡不住反例，**round-3 整体废除**——目的地一律用自身路径规则判别。实测废除后两目标四类计数逐一不变 |
| **不防并发攻击者** | bind/nullfs mount 别名、父目录 symlink 替换、并发 unlink 三类交错挡不住。台账文首「威胁模型」节明写**「这是声明的边界，不是已解决的问题」**，并指出敌对环境下的正解是 `openat` 系绑定目录句柄——属另一张卡。Codex round-5 也把这几条划在「需另立卡」 |
| 只读取证的证明力 | 两次 porcelain sha256 相等只证明两个时点的 `(XY, path[, orig])` 字节相同；不证明文件内容 / ignored 文件 / refs / object DB / git 配置未变，也无法归因 |

> 关于边界的自律：本卡在别处犯过「拿边界当挡箭牌」。这一轮的判据是——
> **能低成本修的一律修，只把真正需要换实现路线的留作边界，并把代价写出来**；
> round-5 的提示词里专门请审查者检验这条边界是否诚实。

---

## 六、硬边界遵守情况

| 边界 | 遵守 |
| --- | --- |
| 全程只读（除新脚本/台账/文档） | ✅ 写入仅限本 worktree 的 `scripts/census_worktree_assets.py` 与 `_bmad-output/` 下 4 个产出文件 |
| 禁清僵尸锁 `~/.claude/auto-sync.lock.d` | ✅ 零触碰，且在台账里立为硬警告 |
| 不碰主仓工作树内容 | ✅ 前后 porcelain sha256 相等取证 |
| G8-9 底账按 append 更新不重排 | 本卡未触碰 G8-9 底账（该项属 DEBT-16 范围） |
| 不 push | ✅ |
| 审查存档完整 | ✅ 5 轮 Codex 外审 + 第 6 轮多维并行验证，逐轮原文与整改回执全部存档于 `codex-review-CARD-DEBT-13.md` |

---

## 七、复跑命令（验收者自行核对）

```bash
cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v7-debt

# 复跑并与本台账 diff
python3 scripts/census_worktree_assets.py \
  --pin-sha main=a55db2ab --pin-sha feature=7f5095fd \
  --baseline "_bmad-output/审查/2026-08-31-DEBT-13-工作树资产分类台账.json" \
  --out-stem "复跑核对-$(date +%H%M)" --brief

# 验伪 pin 门（应 rc=2）
python3 scripts/census_worktree_assets.py --pin-sha main=deadbeef --print-only; echo "rc=$?"
```

预期：断言矩阵全 PASS；两目标 porcelain sha 前后相等；diff 段列出自本台账生成以来的实际变化（若主仓期间无人改动则为 0/0/0）。
