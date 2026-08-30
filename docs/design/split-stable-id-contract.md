# 拆分稳定 ID 与 diff 契约（split-anchor/v1）

> **卡片**: BATCH-2026-08-29-第六批 / CARD-G5-3 拆分稳定 ID 映射与 diff 契约
> **实现**: `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` v4.0
> **裁判**: `backend/tests/skills/test_split_stable_id.py`
> **取证**: `_bmad-output/审查/g5-3-evidence/`
> **上游**: CARD-G5-2（只读 preview 引擎） · **下游**: CARD-G5-10（确认创建派生节点）
> **执行级别**: 引擎实现 + 裁判测试硬门。本文档是规范正文，引擎 docstring 是它的摘要。

---

## 一、这份契约解决什么问题

拆分 preview 每跑一次就是一份「建议拆成哪些节点」的清单。没有稳定 ID 时，两次 preview 之间
唯一能对上号的东西是**行号**——而行号是所有属性里最不稳定的一个：在文件开头加一行注释，
全板候选的行号就整体位移，naive 比对会把「什么都没变」报成「全部都变了」。

所以本卡给每条候选一个**分层身份**：

| 层 | 名字 | 回答的问题 | 变化含义 |
|---|---|---|---|
| L1 | `stable_id` | **它是谁** | 变了 = 这已经是另一个来源单元（provenance 断开） |
| L2 | `content_fingerprint` | **它变了没有** | 变了 = 同一个来源单元，内容被改过 |

两层分开是关键：单靠 L1 无法区分「没动」和「内容改了」，单靠 L2 无法区分「改了内容」和
「删了旧的、加了个新的」。四态 diff（added / changed / removed / moved）正是这两层的组合。

---

## 二、L1 身份键：`stable_id`

### 2.1 计算公式（可被第三方独立复算）

```
segs    = [NS, NFC(file_rel), *path, str(occurrence), basis]
payload = "\0".join(f"{len(seg)}:{seg}" for seg in segs)        # 长度前缀，对任意字节单射
stable_id = "bsa1-" + sha256(payload.encode("utf-8")).hexdigest()[:16]
```

- `NS` = `split-anchor/v1`（命名空间常量 `STABLE_ID_NAMESPACE`）
- `file_rel` = 来源文件相对 vault 根的路径，如 `原白板/CS188 lecture 2.md` 或 `节点/lecture 2.md`
- `path` = **归一化标题路径**（见 §2.2），从最外层祖先到自身标题
- `occurrence` = 同一文件内、归一化标题路径**逐字相同**的小节的出现序号（1-based，文档序）
- `basis` = 候选来源形态（`board-body-section` / `seed-note-section` / `seed-note-whole`）。
  进键的实证理由：种子笔记从 `# 讲义 + 正文` 变成 `## 讲义 + 同正文` 时，归一化路径同为
  `["讲义"]`、内容逐字不变，只有 `basis` 变——不进键的话 diff 报 `unchanged`，
  而 §4.1 #7 声明的是 removed+added。进键即让声明成真
  （Codex round-1 HIGH-2 实证；硬门 `TestReviewRegressions::test_seed_whole_to_section_changes_id_via_basis`）
- 编码用**长度前缀**（`len:段`，段间以 `U+0000` 相连）。不用「靠分隔符不会出现在内容里」
  这类假设——Codex round-2 指出「标题正文不可能含 U+0000」并不成立（UTF-8 文件可以含它并
  构造拼接碰撞）。长度前缀让编码对任意字节内容都单射，`(["a","b"],1)` 与 `(["a\0b"],1)`
  必然得到不同载荷（硬门 `TestRound2Regressions::test_payload_encoding_is_injective_under_nul_bytes`）

四个输入全部落进产物的 `stable_id_basis` 字段，任何人可以拿它们自己算一遍对账。
裁判 `TestStableIdShape::test_stable_id_is_pure_function_of_basis` 钉死了这条可复算性。

**⛔ 载荷里没有任何行号。** 「行号漂移不换 ID」因此是结构性保证，不是巧合——
裁判 `TestStableIdShape` 里有一条 `assert "line" not in json.dumps(basis)` 结构性守着它。

### 2.2 标题路径归一化

```
normalize_heading_text(text) = trim(collapse_js_whitespace(NFC(clean_heading(text))))
```

`clean_heading` 是 G5-2 已有的函数，做两件事：

| 剥离项 | 正则 | 锚定 | 例 |
|---|---|---|---|
| 标题编号 | `^(?:[一二三四五六七八九十百]+、\|\d+(?:\.\d+)*[.、]?\s+)` | **行首** | `2.1 反射代理` → `反射代理` |
| 时间戳标记 | `\s*\[\d{1,2}:\d{2}(?::\d{2})?\]\(\)\s*$` | **行尾** | `理性代理 [08:54]()` → `理性代理` |

为什么必须吸收编号：真实讲义板中间插一节导致后面全体重编号，是高频操作。不吸收，
「稳定 ID」名存实亡。

⚠ **锚定边界（诚实声明）**：时间戳只在**行尾**被吸收。标题写成
`## 2.3 规划代理 [14:59]() 补充` 时，`[14:59]()` 不在行尾 → 不被剥离 → 它参与身份键，
改这个时间戳就会换 ID。四态实景演示里给标题追加 `（修订版）` 后节点名变成
`规划代理-(Planning-Agents)-1459()（修订版）`，就是这条边界的实拍
（见 `_bmad-output/审查/g5-3-evidence/four-state-demo-summary.txt`）。

NFC 归一的必要性：macOS 落盘会把带调拼音等分解成 NFD，同一个标题两种字节形态
必须归一到同一个 ID（裁判 `TestUnicodeNormalization`）。

### 2.3 occurrence 序号

同一文件里可以有**逐字相同**的标题路径（`## 例题` 出现两次且同父）。不加序号，
两条候选会撞成同一个 ID —— 候选↔ID 的双射破裂，diff 会把两条互相吞掉。

序号按**全部小节**计数，不是只按候选计数。这样「原本正文不足没成为候选的重复小节，
后来补了正文成为候选」不会连累它后面的同名小节改号。

---

## 三、L2 内容指纹：`content_fingerprint`

```
body  = [NFC(rstrip(line)) for line in lines[line_start : line_end] if rstrip(line)]
fp    = "cf1-" + sha256("\n".join(body).encode("utf-8")).hexdigest()[:16]
```

- 范围 = 1-based 区间 `(line_start, line_end]`，即 `source_anchor` 声明的整段，**不含标题行本身**
- 归一化只做无语义项：每行 rstrip → 丢纯空行 → NFC
- **排除机器生成段**：frontmatter / AUTO-GENERATED 对 / Recent Activity 节（`machine` 掩码）

### 3.1 覆盖面：为什么含代码块、又为什么不含机器生成段

指纹回答的问题是「**这段内容变了没有**」，与候选判定的「**够不够格成为一个节点**」不是同一个问题。
所以指纹**不**照搬 G5-2 的剥离掩码，而是拆成两半：

| 行的种类 | 进不进指纹 | 理由 |
|---|---|---|
| 普通正文 | ✅ 进 | 不解释 |
| 代码 fence 内容 | ✅ 进 | 是用户内容。跟着剥离掩码走的话，小节内代码块被整块改写时指纹纹丝不动，diff 会一本正经地报「无变化」而实际全变了——那是掩饰 |
| HTML 注释 | ✅ 进 | 同上 |
| frontmatter / AUTO-GENERATED 对 / Recent Activity 节 | ⛔ 不进 | 它们是**机器**刷新的，不是用户改的 |

最后一行不是洁癖，是实测出来的：板尾的 `## Recent Activity` 被剥离后不算标题，
于是**前一节的 `end` 一路吞到 EOF**，机器写的活动日志就落进了最后一条候选的 span。
不排除的话，每派生一次节点、每刷新一次尾块，就凭空多一条 `changed(content)`——
指纹作为「内容变了没有」的信号会被噪声淹没。

两条边界各有一道硬门看着：`TestFingerprintCoverage`（代码块/注释改动**必须**被感知）
与 `TestReviewRegressions::test_machine_generated_tail_does_not_pollute_fingerprint`
（机器尾块刷新**必须不**被感知）。

⚠ 分类本身还有一条易踩的边：`Recent Activity` 的识别**必须先避开普通 HTML 注释**。
注释里写着 `## Recent Activity` 时，若把它当真标题，RA 扫描会一路吞到下一个同级标题为止，
**连同注释后面的真实用户正文一起**——被吞的正文不进指纹，用户改了它 diff 报「无变化」。
这是最难察觉的一类失败：不是报错，是**沉默**。
硬门 `TestRound2Regressions::test_commented_out_recent_activity_does_not_swallow_user_text`
（Codex round-2 HIGH-1 实证）。

### 3.2 嵌套后果（声明，不是缺陷）

`line_end` 是小节的**完整** span（含子小节），与 `source_anchor` 对齐。当父小节与子小节
**都**达标成为候选时，二者 span 嵌套 —— 改子小节正文会让父子**两条**候选都判 changed。

这是「候选可嵌套」这一 G5-2 既有事实的后果，不是指纹引入的新问题。选 `end` 而不是
`direct_end` 的理由：指纹范围必须与 `source_anchor` 声明的区间一致，否则「锚点说这段，
指纹算另一段」本身就是名实不符。

---

## 四、诚实边界：哪些操作会换 ID、哪些不会

> 这是本卡验收的重点。稳定 ID 的价值全在于边界被说清——一个没有边界声明的
> 「稳定 ID」等于一句无法证伪的宣传。

### 4.1 **会**换 ID（不稳定面）

| # | 操作 | 后果 | 为什么不做得更好 |
|---|---|---|---|
| 1 | 改标题实词（`反射代理` → `反射式代理`） | 旧 ID removed + 新 ID added，provenance 在此断开 | 相似度改名识别要引入阈值与非确定性，与「同输入二跑逐字节相等」硬门直接冲突。改名承接交给 G5-10 人工指认（§7.4） |
| 2 | 改**祖先**标题实词 | 该子树下全部候选换 ID | 祖先链是身份的一部分：同名子标题挂到不同父下就是不同来源 |
| 2b | **同一份笔记里换父**（把 `子小节` 从 `父甲` 挪到 `父乙`，自己的标题一字未动） | 换 ID | 同 #2：变的是祖先链。⚠ 这条原先漏列（Codex round-6 指出），而它是**高频**操作——整理笔记时经常发生。硬门 `TestRound6Regressions::test_moving_section_to_another_parent_changes_id` |
| 3 | 小节搬到另一个文件（板 ↔ 种子笔记，或种子之间） | `file_rel` 变 → 换 ID（⚠ 不含 NFC/NFD 等价改名，见 §4.2） | 跨文件搬家等于换来源，不做跨文件内容追踪 |
| 4 | 调整标题层级且**改变了祖先链**（`### X` 提为 `## X` 后父不同了） | 换 ID | 同 #2 |
| 5 | 同名同父小节被增删，导致后面同名者 `occurrence` 位移 | 位移的那些换 ID，**且会继承前一个的 ID**（见下方 ⚠） | 见 §2.3：不加序号会双射破裂，两害相权取其轻 |
| 6 | 板文件改名（`原白板/X.md` → `原白板/Y.md`） | **只有板体候选换 ID**；种子笔记候选**不换**（见下方 ⚠）。同样不含 NFC/NFD 等价改名 | 同 #3 |
| 7 | 种子笔记从「整篇回退候选」变成有达标 `##+` 小节 | 整篇候选 removed，新小节候选 added | 回退候选的标题路径是 level-1 标题，与新出现的 level-2 候选路径不同 |
| 8 | 标题里**非行尾**的时间戳标记被改 | 换 ID | `_TS_MARK` 锚定行尾，见 §2.2 |
| 9 | 在同名同父小节**前面插入**一条同名小节 | 后面那条的 `occurrence` +1 → 换 ID，且它原来的 ID 被新插入的那条接管 | #5 的镜像，同一根因（§4.4） |
| 10 | 给标题行**加行内 HTML 注释**（`## 甲 <!-- 备注 -->`） | 该行被注释掩码吃掉 → 不再算标题 → 该小节整体消失，其子树祖先链改变 → 整棵换 ID | 注释掩码是 G5-2 的既有语义（「注释是说明不是内容」），本卡不改它，只如实列出后果 |

> ⚠ **#6 原来写的是「全板换 ID」，实测不成立（Codex round-5 证伪，已改正）**：
> 身份键里的 `file_rel` 是**候选自己的来源文件**，不是板文件。种子笔记候选的
> `file_rel` 是 `节点/种子.md`，压根不含板名 —— 改板名它们的 ID 纹丝不动。
> 只有 `原白板/<板名>.md` 里的板体候选才会换。
> 之前的裁判只用了纯板体候选，造成**假完备感**；现已用混合构造（板体+种子）钉死真实行为：
> `TestRound5Regressions::test_board_rename_changes_only_board_body_candidates`。
>
> ⚠ **#5 最坏情况必须说清（实测钉死于 `TestUnstableSurface::test_deleting_earlier_duplicate_shifts_occurrence`）**：
> 文件里有两个标题路径逐字相同的小节 `X#1` / `X#2`，删掉 `X#1` 之后，`X#2` 的
> `occurrence` 从 2 变 1 —— 它拿到的**不是一个全新 ID，而正是 `X#1` 原来的 ID**。
> 后果：diff 会把这件事报成「`X#2` 的 ID 消失了（removed）+ `X#1` 的 ID 内容变了（changed）」，
> 而实际发生的是「删了一个、留了一个」。如果此时 `X#1` 已经被 G5-10 派生成节点，
> 那个节点的 `split_stable_id` 现在会指向 `X#2` 的内容 —— **provenance 被静默错配**。
>
> 这是 occurrence 方案的真实代价，不加掩饰。缓解手段（本卡不实施，留给 G5-10 与后续卡）：
> 派生节点 frontmatter 里存的 `split_source_fingerprint_baseline`（§7.1），
> 一旦 ID 未变而指纹变了，就该提示「来源可能已被替换，请人工确认」。
> 根治要等 `split-anchor/v2` 引入不依赖序号的判别维度（§十）。
> **在此之前，同一文件里出现完全同名同父的小节是已知风险区。**

### 4.2 **不**换 ID（稳定面）

| 操作 | 依据 |
|---|---|
| **非结构性**行号漂移（增删的是正文/空行/注释等**不含标题**的行，且不改本小节内容） | 身份键不含行号（§2.1）。⚠ 措辞收紧（Codex round-6）：原文写「文件任意位置增删行」过宽——插入的若是**标题行**，就可能改变别人的祖先链（#2b）或同名小节的 occurrence（#9） |
| 本小节正文任意改动 | 正文进 L2 指纹，不进 L1 身份键 |
| 小节整体前后调序（限**同一父路径内**、且**非歧义**候选） | 身份键不含文档序。⚠ 措辞收紧（Codex round-6）：换父即换 ID（#2b）；重复标题组另受 §4.4 支配（调序会让身份跟着槽位走） |
| 标题编号变化（`2.1` → `3.4`）、**行尾**时间戳标记变化 | `clean_heading` 吸收（§2.2） |
| 中文 NFC / NFD 字节形态差异 | 归一化含 NFC（§2.2） |
| 行尾空白、空行增删 | 指纹归一化含 rstrip + 丢空行（§三） |
| 文件名 NFC / NFD **等价**改名（`café.md` 两种字节形态互改） | 身份键对 `file_rel` 也做 NFC（§2.1）——所以 #3/#6 的「改名必换 ID」**不含**这种改名（Codex round-1 MEDIUM 实证） |
| 机器刷新板尾 Recent Activity / AUTO-GENERATED 段 | 指纹排除机器生成段（§3.1） |
| `resolved_name` 因 `节点/` 池变化而改（`X` → `X_2`） | 重名解析是输出层，不进身份键 |
| 标题层级调整但**祖先链不变**（`## 甲小节` → `### 甲小节`，父仍是同一个） | 身份键用祖先链而非层级数字（`TestStableSurface::test_heading_level_change_keeping_ancestors_keeps_id`） |

### 4.3 候选集合本身会变（与 ID 稳定性无关，但会出现在 diff 里）

内容门（`MIN_PLAIN_LINES=2` / `MIN_PLAIN_CHARS=60`）是**动态**判据：给一个原本不达标的
小节补几句正文，它就跨过门槛成为**新候选** → diff 报 `added`。

四态实景演示里就出现了这一幕：给「课程概述与理性代理」补一句正文，
同时把它的子小节「理性代理 (Rational Agents)」推过了内容门 → 一条 `changed` 带出一条 `added`。
这不是 ID 不稳定，是候选集合本身变了。读 diff 时要能分辨这两件事。

### 4.4 ⛔ 身份先天歧义：同一文件里的重复标题路径

> Codex round-1 把这一条判为 BLOCKER，理由是准确的：**ID 绑的是「同路径第 N 个槽位」，
> 不是内容单元**。本节把它的全部后果摆开，并说明 v1 为什么这样收口。

设一个文件里有两条归一化标题路径**逐字相同**的小节 `X#1` / `X#2`：

| 你做的事 | 实际发生 | diff 报什么 |
|---|---|---|
| 交换两条的位置 | 身份留在槽位，两份**指纹对调** | `changed × 2`（不是 `moved`）——每条都"内容变了" |
| 删掉 `X#1` | `X#2` 升为 occurrence 1，**继承 `X#1` 的 ID** | `removed`（X#2 的旧 ID）+ `changed`（X#1 的 ID） |
| 把中间某条改名成 `X` 塞进重复组 | 新来的按文档序占槽位，可能**直接继承**已有 ID | 看起来像"某条内容变了" |

如果 `X#1` 已被 G5-10 派生成节点，那个节点的 `split_stable_id` 此后会指向 `X#2` 的内容
—— **provenance 被静默错配**。

**为什么 v1 不"修好"它。** 单跑的 preview 只能拿到当前文件，区分两条同名小节的信息只有
两样：位置、内容。选位置 → 调序换身份（现状）；选内容 → 正文一改就换 ID，
那等于放弃这张卡的全部价值。二者必居其一，没有第三条路——除非引入跨 preview 的匹配，
而那要引入阈值与非确定性，与「同输入二跑逐字节相等」硬门冲突。

**v1 的收口方式：不假装它没问题，而是把判据摆出来、把禁令写清楚。**
（⚠ 措辞纠正：原文写的是「让它无法被误用」——过头了。见下方第 3 条：
这是**契约约束**，不是运行时强制。）

1. 引擎给这些候选打 `identity_ambiguous: true` + `ambiguous_group_size`；
2. diff 在 `warnings` 里显式告警，并在人读 MD 的每一行打 `⚠身份歧义` 标记；
3. **契约层面：这些候选的 `stable_id` 不具 provenance 效力**——
   §7 的「`split_stable_id` 是权威身份」只对 `identity_ambiguous == false` 的候选成立；
   G5-10 **不得**为歧义候选持久化 `split_stable_id`（§7.6）。

硬门：`TestReviewRegressions::test_duplicate_paths_are_flagged_as_identity_ambiguous`
（同时钉死上表第一行的实际行为与三处标记）。

真正的根治留给 `split-anchor/v2`（§十）：需要一个不依赖文档序、也不依赖正文的判别维度。

---

## 五、schema v2 加性契约

`schema_version` 1 → 2，**纯加性**：v1 的每一个字段都原样保留，只追加新键。
裁判 `TestSchemaV2Additive` 把 v1 字段清单逐个钉死，防未来重构悄悄删字段。

### 顶层新增

| 键 | 值 | 说明 |
|---|---|---|
| `stable_id_namespace` | `"split-anchor/v1"` | 命名空间，升版时改这里 |
| `id_stability` | `"split_anchor_v1"` | 本引擎的 ID 稳定性自陈（⚠ 与 board_manifest 的不同，见 §六） |
| `vault_fingerprint` | `"vf1-<16hex>"` | vault 物理路径的哈希。`stable_id` 只含 vault **内**相对路径，不带这一维的话，两个不同 vault 的同名板可以互比、凭空造出一份编辑史。落哈希而非路径本身，避免把用户机器上的目录结构写进可分享的产物。**diff 侧必填**：缺了会让跨 vault 比对静默通过 |

### 每条候选新增

| 键 | 例 | 说明 |
|---|---|---|
| `stable_id` | `bsa1-e77719c20b7c29d9` | L1 身份键 |
| `stable_id_basis` | `{namespace, file, heading_path_normalized, occurrence, basis}` | 复算 `stable_id` 的四个输入，全部公开 |
| `content_fingerprint` | `cf1-5a537e76869deb7d` | L2 内容指纹 |
| `identity_ambiguous` | `false` | `true` = 该候选处在重复标题路径组里，其 ID 不具 provenance 效力（§4.4） |
| `ambiguous_group_size` | `1` | 同路径小节的总数；`1` 即无歧义 |

⚠ `source_anchor.heading_path` 保持 **原文**（含编号与时间戳标记），
`stable_id_basis.heading_path_normalized` 是**归一化后**的。两者并存是有意的：
前者给人看「这段在讲义里长什么样」，后者给机器算 ID。消费方要对 ID 语义做判断时
必须读后者。

### 引擎自检

同一份 preview 内 `stable_id` 若出现重复 → 引擎 `SystemExit` 拒绝输出，
**不**产出一份双射破裂的 preview。自检有三点要说清：

1. **跑在规模门截断之前**。只查截断后的 `kept` 的话，截断把撞车的两条切开时自检直接失效，
   一份双射破裂的 preview 会照常落盘（审查发现的旁路）。
2. **错误信息列出撞车两条的锚点**（file:line + 标题路径），并点名最常见成因是
   「同一来源文件被扫了两次」，而不是只印一串哈希让人无从下手。
3. **它不能区分「身份键缺维」与「64-bit 截断真碰撞」**——两者的表征相同。
   本文档不宣称自检能判别成因；`_HASH_HEX=16`（64 bit）在单板数百候选的量级下
   碰撞概率可忽略，但那是**概率性**论断，不是证明。跨 preview 的一致性由 diff 侧的
   `stable_id_basis` 相等校验兜底（§8.2）。

最常见的触发源已在源头消除：`## Concepts` 里同一份种子被列两行（含 NFC/NFD 两种写法）
会让同一文件被扫两遍必然撞车——现在按 NFC 归一去重，被跳过的那行在 `sources` 留痕。
（这是审查发现的**可用性倒退**：G5-2 对同样输入能正常出图，G5-3 首版会整块板 exit 1。）

---

## 六、与 `board_manifest_service.ID_STABILITY` 的命名空间关系

`backend/app/services/board_manifest_service.py:57` 有：

```python
ID_STABILITY = "basename_v1_will_upgrade_in_1_5"
```

**两者不是同一层键，不可互换：**

| | board_manifest | 本契约 |
|---|---|---|
| 键 | `node_id` / `board_id` = **文件 basename** | `stable_id` = **来源锚点** |
| 指向 | 已经存在的 `.md` 文件 | 原板/种子里的一段，**还不是文件** |
| 自陈值 | `basename_v1_will_upgrade_in_1_5` | `split_anchor_v1` |
| 谁生成 | 扫 vault 时从文件名取 | preview 引擎从标题路径算 |

裁判 `TestStableIdShape::test_prefix_namespace_and_basis` 显式断言
`id_stability != "basename_v1_will_upgrade_in_1_5"` —— 防两套 ID 在日志/产物里互相冒充。

**桥在 G5-10**：确认创建节点时把 `stable_id` 写进新节点 frontmatter（§七），
于是 basename ↔ 来源锚点之间建立起可迁移的映射。board_manifest 将来真的从
`basename_v1` 升级时，这个 frontmatter 字段就是现成的迁移源。

⛔ **本卡不改 board_manifest 任何行为**，也不主张替换它的 `node_id`。

---

## 七、与 CARD-G5-10（确认创建）的接口契约

> G5-10 是下游卡：用户在 preview 里逐条确认后，真正创建派生节点、可选向原板插链。
> 本节是 G5-10 落地时必须遵守的接口，先在这里锁定，避免它自造一套 ID 语义。

### 7.1 创建节点时写入的 frontmatter 字段

```yaml
---
# ——— 既有字段（G5-10 不得改动其语义）———
type: concept
source_board: "[[原白板/CS188 lecture 2]]"

# ——— split-anchor/v1 provenance（本契约新增，G5-10 负责写入）———
split_id_namespace: split-anchor/v1
split_stable_id: bsa1-e77719c20b7c29d9
split_source_anchor:
  file: 节点/lecture 2.md              # 来源文件相对 vault 根路径
  heading_path: ["CS 188：人工智能搜索", "二、代理类型：反射与规划", "2.2 反射代理 (Reflex Agents) [12:06]()"]
  heading_path_normalized: ["CS 188：人工智能搜索", "代理类型：反射与规划", "反射代理 (Reflex Agents)"]
  occurrence: 1
  basis: seed-note-section             # 身份键的第四个输入，必填（§2.1）
# ⛔ 两个指纹, 不是一个（Codex round-1 BLOCKER-2）
split_source_fingerprint_at_confirm: cf1-5a537e76869deb7d   # 你按下确认时看到的那份内容
split_source_fingerprint_baseline:   cf1-e4f76718f60e99d7   # 写完(含插链)后重跑 preview 的指纹
split_created_from_preview:
  file: split-preview-CS188 lecture 2.json
  sha256: <该 preview JSON 的 sha256>      # 不可变身份, basename 会被下一次 preview 覆盖
split_batch: <本次确认批次 id>
---
```

字段语义约定：

1. **`split_stable_id` 是权威身份**。文件 basename 可以被用户随手改名（Obsidian 里改文件名
   是一秒钟的事），basename 一改 `board_manifest` 的 `node_id` 就变了，但
   `split_stable_id` 不变 —— 这正是「重命名不断 provenance」的落点。
2. **指纹必须存两个，不能只存一个。** 这是 Codex round-1 抓到的时序矛盾：
   §7.2 要求 G5-10 插链后重跑 preview 落新基线，而插链本身就改了来源小节的内容
   → 只存"确认时刻指纹"的话，**创建刚完成就会被判为「来源已漂移」**（实测
   `cf1-6eea325e0f0aa5ca` → `cf1-e4f76718f60e99d7`，ID 不变）。
   所以分开存：
   - `split_source_fingerprint_at_confirm` —— **用户确认时看到的内容**，审计用，永不更新；
   - `split_source_fingerprint_baseline` —— **写完（含插链）后 re-baseline 的指纹**，
     漂移检测拿它比。后续若用户真的改了来源正文，`baseline` 与当前 preview 不一致，
     那才是真漂移。
   两者在创建那一刻通常**不相等**（差的正是那条派生 callout），这是正常的、预期的。
3. `split_created_from_preview` 存**文件名 + 该 JSON 的 sha256**。只存 basename 没有意义：
   下一次 preview 会原地覆盖同名文件，事后无法证明当时确认的是哪一版。
4. `heading_path` 与 `heading_path_normalized` **两个都写**。前者可读，后者可复算 ID。
   `split_source_anchor` 里还须写 `basis`——它是身份键的第四个输入（§2.1）。
5. `split_id_namespace` 必须写。将来出 `split-anchor/v2` 时，读侧靠它区分算法代。

### 7.2 re-baseline 规则（⛔ 硬要求）

G5-10 若向原板/种子笔记插入派生 callout（`> [!relation/…]+ 已派生为 [[节点/X]]`），
那一行**是内容**，会进 L2 指纹 —— 下一次 preview 必然把被插入的小节判 `changed`。

因此：**G5-10 写完（含插链）必须立即重跑一次 preview 落新基线**，并把这份新基线
作为后续 diff 的「旧侧」。diff 永远比较**同一写代之间**的两份 preview，
不跨写操作比较。不遵守这条，用户每次拆完节点都会看到一堆自己造成的假 `changed`。

### 7.3 重名与冲突

- 落盘文件名用 preview 的 `resolved_name`（已含 `_2..._9` 后缀解析），**不是** `suggested_name`。
- 若目标 basename 已存在，且该文件 frontmatter 的 `split_stable_id` **与当前候选不同** →
  这是两个不同来源撞名，必须继续走后缀解析，**不得覆盖**。
- 若已存在文件的 `split_stable_id` **与当前候选相同** → 同一来源已经派生过，
  应走「更新/跳过」而不是再建一个 `_2`。
- `conflict_unresolvable`（9+ 重名）的候选，G5-10 **不得**自动创建，必须先由人改名。

### 7.4 改名承接（provenance 断点的人工修复路径）

按 §4.1 #1，改标题会让 diff 报一条 `removed` + 一条 `added`。当用户判定这两条其实是
同一个来源单元时，G5-10 应提供「指认承接」动作，落地为：

```yaml
split_stable_id: bsa1-<新 id>
split_stable_id_prev: ["bsa1-<旧 id>"]   # 数组，可多次承接，最新的在最后
```

读侧回溯 provenance 时沿 `split_stable_id_prev` 链向前查。
⛔ 承接必须是**用户显式确认**的动作，引擎不得自动猜测——自动猜测就是把非确定性
引进了确定性引擎。

### 7.5 G5-10 **不**该做的事

- 不得自造第二套候选 ID（例如按行号或按创建时间戳）。
- 不得把 `stable_id` 当文件名或文件名的一部分（它是身份，不是命名）。
- 不得在未 re-baseline 的情况下把 diff 结果直接呈现给用户。
- ⛔ **不得为 `identity_ambiguous == true` 的候选持久化 `split_stable_id`**（见 §7.6）。

### 7.6 ⛔ 权威身份的适用范围（对 §7.1 第 1 条的收窄）

§7.1 说「`split_stable_id` 是权威身份」——这句话**只对 `identity_ambiguous == false` 的候选成立**。

对歧义候选（§4.4），preview 已经在 JSON、`warnings` 和人读 MD 三处标了红旗。G5-10 遇到它们时：

1. **不写** `split_stable_id`（写了就是把一个会跟着槽位漂移的值当 provenance 用）；
2. 改为提示用户「这块板里有多个标题完全相同的小节，拆分前请先把标题改得可区分」——
   这也是**用户侧最简单的根治**：把 `## 例题` 改成 `## 例题：最小生成树`，歧义当场消失；
3. 若用户坚持创建，节点 frontmatter 写
   `split_identity: ambiguous_no_stable_id`，并保留 `split_source_anchor`（含 occurrence）
   作为**弱**锚点，明确标注它不可用于自动漂移检测。

这是本卡对 Codex round-1 BLOCKER-1 的收口：不假装 v1 解决了重复标题的身份问题，
而是**把权威性的边界画在能站住的地方**：引擎给出红旗、契约明令禁止、diff 产物里
带着可判据的字段。⚠ 这是**契约约束**不是运行时强制——G5-10 若无视 `identity_ambiguous`
照样能写 `split_stable_id`。本卡不实现跨卡的运行时拦截（G5-10 还不存在），
但把判据字段和禁令都摆在了它面前，越界就是明知故犯而不是不知情。

---

## 八、diff 契约

### 8.1 调用

```bash
python3 split_preview.py --diff OLD.json NEW.json [--out-dir DIR]
```

- 与 `--vault/--board` **互斥**：diff 模式不读 vault，只比对两份 JSON。
- `--out-dir` 缺省 = `NEW.json` 所在目录。
- 产物：`split-diff-<板名>.json` + `split-diff-<板名>.md`，diff 自己的
  `schema_version = 1`（与 preview 的 schema 独立编号）。

### 8.2 输入守卫（全部在建 out-dir **之前**完成 → 拒绝路径零产物）

| 守卫 | 拒绝理由 |
|---|---|
| `schema_version < 2` | 稳定 ID 自 v2 起提供，v1 产物没有 ID 可比 |
| 两份 preview 的 `board` 不同 | 跨板比对无意义 |
| `board` 不是非空字符串 | 它会被拼进产物文件名；`None` / 数字被 `str()` 成 `"None"` / `"123"` 会悄悄落盘 |
| `board` 含非法字符或路径逃逸 | 同上，且校验**必须在建 out-dir 之前**（否则「拒绝但已建空目录」） |
| 缺 `stable_id_namespace`，或两侧不等 | 跨身份键代际不可比（§十） |
| 任一候选缺 `stable_id` / `content_fingerprint` / `index` / `suggested_name` / `resolved_name` / `basis` | 产物被外部改坏 |
| 任一候选的 `source_anchor` 不完整 | 原先要到 MD 渲染期才 `KeyError`，那时 JSON 已落盘 → 半份产物 |
| 同一 `stable_id` 在两侧的 `stable_id_basis` 不同 | 要么产物被改过、要么真发生截断碰撞——两种情况把它们当同一候选比都是错的（原实现会报 `unchanged`） |
| 单份 preview 内 `stable_id` 重复 | 双射破裂 |
| 产物文件名字节数 > 255 | 否则「先建好 out-dir、写入时 ENAMETOOLONG」→ 拒绝但已留空目录 |
| 任一候选缺 `identity_ambiguous` / `ambiguous_group_size` / `stable_id_basis`，或顶层缺 `vault_fingerprint` | 这三处是**安全字段**：缺失会让歧义投影成 `false`、跨 vault 不告警、basis 守卫因 `None == None` 被绕过——三道处置同时 fail-open（Codex round-2 HIGH-2 实证） |
| 任一字段类型不对（`index` 非正整数、`suggested_name` 非字符串、`occurrence < 1`、`heading_path` 非字符串数组…） | 只查「键在不在」不够，坏 schema 会一路走到渲染期 |
| 整数字段收到 JSON `true` / `false` | ⛔ Python 里 `isinstance(True, int)` 为真 —— 用 `isinstance(v, int)` 会把布尔当整数放行（Codex round-3 用 166 组畸形 schema 实证有 8 组靠这个漏洞 rc=0）。判据必须是 `isinstance(v, int) and not isinstance(v, bool)` |
| `identity_ambiguous` 与 `ambiguous_group_size` 自相矛盾 | 产物被人为篡改的直接信号 |
| `stable_id` / `content_fingerprint` 格式不合（非 `bsa1-`/`cf1-` + 16 位小写十六进制） | 同上 |
| `source_anchor` 行区间倒置（`line_end < line_start`） | 同上 |
| `stable_id_basis` 的 `namespace` / `basis` / `file` 与顶层、候选 `basis`、`source_anchor.file` 不一致 | **交叉绑定**：字段各自类型都对、但互相对不上 = 产物被改过 |
| **`stable_id` 与其 `stable_id_basis` 复算不符** | 最强的一道：`stable_id_basis` 带齐了身份键的四个输入，可直接复算对账。它在语义上兜住了上面几条（那几条保留的价值是**诊断精度**——复算只会说「对不上」，它们能点出是哪个字段坏了） |
| `source_anchor.heading_path` **正向归一化后** ≠ `heading_path_normalized`，或为空/含空元素 | ⚠ 措辞纠正（Codex round-5）：round-4 这里写的是「归一化有损所以只能绑层数」——**那是错的**。不需要从归一化反推原文，把原文**再正向归一化一遍**比对即可；只绑层数时，同层数的伪造标题（`["完全伪造的父标题","完全伪造的子标题"]`）能静默通过并把伪造锚点送进 diff |
| `board_file != f"原白板/{board}.md"` | 只重标 `board` 不改 `board_file`，同样是无需读 vault 就能发现的不一致 |
| `scale_gate` 与候选数/阈值不自洽（`kept != len(candidates)`、`total < kept`、`threshold < 1`、`over_threshold != (total > threshold)`） | **截断告警会被静默压掉**——把 `total_candidates` 改大、`over_threshold` 改 false 即可 |
| 顶层 `stable_id_namespace` 不等于**引擎自身常量** | 两侧 namespace **协同**改成别的代际时，同侧绑定、跨侧相等、复算三道全过。本引擎只能校验自己这一代的产物 |
| `vault_fingerprint` 格式不合（非 `vf1-` + 16 位小写十六进制） | 空白串等能绕过「非空」判据 |
| 文件读不到 / 非合法 JSON / 缺 `candidates` 数组 | 不是 preview 产物 |

### ⛔ 信任边界：内部一致性 ≠ 真实性

上面这些守卫检的全是**内部一致性**。必须说清它们检不了什么：

> **preview 产物没有签名。** 凡是能编辑这个 JSON 的人，都可以把 `stable_id_basis`
> 与 `stable_id` **一起重算**成自洽的一份（`file`、`heading_path`、`heading_path_normalized`、
> `stable_id` 全部改成互相对得上的一套）——一致性检查按定义无法与引擎产出的真品区分。
> diff 模式不读 vault（这是它的设计前提），所以它**没有任何办法**验证锚点指向的
> 内容真的存在、真的长那样。

⚠ **界限要划准**（Codex round-5 / round-6 两次指正，两次都是我把可查的东西算进了边界）：
下面这些**都不属于**这条边界，因为无需读 vault 就能从 JSON 内部对账出来，现已全部堵上：

| 曾被我误算进边界的 | 实际怎么查出来 |
|---|---|
| 同层数的伪造标题路径 | 把原文路径**正向再归一化一遍**比对 |
| 板体候选的 `file` 重绑到 `节点/` | `basis` 与来源目录前缀必须自洽（`board-body-section` ⇒ `原白板/<board>.md`） |
| 伪造的 `basis` 取值 | 必须是三个已知取值之一 |
| 伪造的 `suggested_name` | 可由 `source_anchor.heading_path[-1]` **复算** |
| 伪造的 `id_stability`、清空的 `sources`、不在 `sources` 里的来源文件 | 顶层常量比对 / 清单成员检查 |

真正落在这条边界里的，只有「改完之后**每一处都互相对得上**」的伪品
（来源文件、`basis`、`sources`、标题路径、`stable_id`、`suggested_name` 全部重新签成一套），
以及**只有读 vault 才能证伪**的那两类：伪造的 `content_fingerprint`、伪造的行号。

**把本可检查的不一致算进「信任边界」，就是拿边界当挡箭牌。** 这话我犯了两次，记在这里。

也就是说：这些守卫防的是「产物被改坏 / 被改乱」，**不是**「产物被伪造」。
要防伪造需要签名机制（HMAC 或 detached signature），本卡不做——
但把这条边界写成了**可执行的断言**：
`TestRound4Regressions::test_declared_limit_consistent_forgery_is_NOT_detectable`
构造一份自洽伪品并断言它**被接受**。哪天真加了签名，那条测试会变红，
提醒后来者回来改这一节。

⚠ `namespace` 的绑定原本是**两跳传递**的（同侧内部一致 + 跨侧相等），复算不校验它；
round-4 补的「必须等于引擎自身常量」把这条补成了直接绑定。

每一种拒绝都有对应的裁判断言**零产物**（连空目录都不留），不只断言 exit code。

**成对发布**：两份产物不只是「都渲染完再动 out-dir」，写入本身也是先把两个目标的
准入（`O_NOFOLLOW` 打开 + `nlink` 检查）全部验完再落笔；任一不过则一份都不写，
且**撤销本次新建的空文件**（`O_CREAT` 会把目标建出来，留个 0 字节文件同样是半份产物）。
硬门 `TestRound2Regressions::test_second_product_rejection_leaves_no_first_product`。
已知边界（如实声明）：准入通过之后写入过程中的 I/O 错误（磁盘满等）仍可能只落一份——
本机制消除的是**可预见的拒绝**造成的半份产物，不是所有失败模式。

### 8.3 四态定义与优先级

状态**互斥**，一条候选只出现在一个状态里（避免同一条被两处计数）。优先级
`changed > moved > unchanged`：

| 状态 | 判据 |
|---|---|
| `added` | `stable_id` 只在新侧 |
| `removed` | `stable_id` 只在旧侧 |
| `changed` | 两侧都有，且 `change_reasons` 非空（位置是否也变了记在 entry 的 `moved` 布尔上） |
| `moved` | 两侧都有，`change_reasons` 为空，但不在 LCS 保留集里 |
| `unchanged` | 两侧都有，无 reason，且在 LCS 保留集里（单列在 `diff["unchanged"]`，不进 `entries`） |

`change_reasons` 取值（字典序输出，确定性）：

| reason | 含义 |
|---|---|
| `conflict` | 重名标志位变（撞池 / 撞本轮前序 / 9+ 不可解） |
| `content` | L2 内容指纹变 |
| `name` | `resolved_name` 变 —— 确认创建时实际会落到**不同文件名** |
| `overlap` | `derived_overlap` 变 —— 这段**已经被拆过了**（小节里出现/消失了「已派生为 [[节点/X]]」） |

把 `name` / `conflict` 也算 changed 是有意的：内容没变但落盘文件名会变，
这是 G5-10 必须重看的差异。`overlap` 单列而不是混进 `content` 的理由：
「正文改了」和「这段已经被拆过了」是两件事，后者恰恰是 G5-10 最该知道的信号
（原实现把它吞进 content，读 diff 的人分不出来）。

### 8.4 moved 语义（⚠ 声明的取舍）

`moved` = 共同候选序列的 **LCS 补集**（最小移动集，git 式）。确定性 tie-break：
回溯时 `dp[i-1][j] >= dp[i][j-1]` 退 i。

**交换相邻两条只会标记其中一条为 moved**，另一条作为 LCS 锚点视为未动。
这是最小移动集的定义使然，不是漏判。裁判 `TestReorder` 把这个集合**精确钉死**
（`[A,B,C]` → `[A,C,B]` 时 moved 恰为 `{C}`），而不是弱断言「非空」。

为什么不用「秩比较法」（共同集内序号变了就算 moved）：它会把「末项拖到最前」
报成**全员 moved**，过报等于信号失效。少报可由每条 entry 同时输出的
`old.rank` / `new.rank`（共同集内 0-based 秩）补齐，想看完整位移图景的读这两个字段。

### 8.4a entry 上的红旗字段

| 字段 | 含义 |
|---|---|
| `truncation_suspect` | 任一侧 preview 被规模门截断时，`added`/`removed` 打此标记——它可能只是"被窗口挤出去了"而非真的增删（§8.6） |
| `new.identity_ambiguous` / `old.identity_ambiguous` | 该候选处在重复标题路径组里，本条 diff 结论不具 provenance 效力（§4.4） |

两者都在人读 MD 的「标记」列渲染成 `⚠截断嫌疑` / `⚠身份歧义`。
**只写进 JSON 等于没写**——读 diff 的人看的是 MD。

⚠ `truncation_suspect` 的口径是**保守**的：任一侧被截断时，**全部** `added`/`removed`
都打标，而不是只标窗口边界附近的那几条。理由是「窗口边界附近」本身不可靠定义
（两侧候选集合不同，边界随插入位置漂移），宁可多提醒也不漏——
漏掉一条就意味着有人会把「被窗口挤出去」读成「被删掉了」。

### 8.4b diff 顶层 `warnings`

产物带一个 `warnings` 数组，人读 MD 里渲染成总览**之前**的 `> [!warning]+` 块：

| 触发条件 | 告警 |
|---|---|
| 两侧 `scale_gate.threshold` 不同 | 阈值不一致，removed/added 里掺了被阈值切掉的条目 |
| 任一侧 `over_threshold` | 即使两侧阈值相同，板体跨过阈值也会把尾部未动的小节挤出窗口（§8.6） |
| 两侧 `vault_fingerprint` 不同 | 跨 vault 比同名板会凭空造出编辑史。**告警不硬拒**——拿隔离副本比 live 是合法用法（本卡的四态演示就是） |
| 存在 `identity_ambiguous` 候选 | 列出条数，声明这些条目的判定不具 provenance 效力 |

### 8.5 entries 排序

`added` / `changed` / `moved` 按**新侧文档序**输出，`removed` 按**旧侧文档序**追加在后。
确定性排序保证同输入二跑逐字节相等（裁判 `test_diff_is_byte_identical_on_rerun`）。

### 8.6 规模门与 diff 的交互（声明）

preview 的 `--max-units` 规模门会按文档序截断候选。两次 preview 若用了**不同的**
`--max-units`，被截掉的候选会在 diff 里显示为 `removed`（新侧没有它）——**这不是内容变化**。

光把这条写进文档是不够的：读 diff 的人不会先来翻文档。所以 diff 产物带一个
`warnings` 数组，命中下列任一条件时当场告警，人读 MD 里渲染成总览**之前**的
`> [!warning]+` 块：

⚠ **两侧阈值相同也会踩**——这是 5 个独立审查镜头同时命中的一点，原文档只声明了
「用了不同 `--max-units`」一种成因，那条自查建议在下面这个场景里恒为绿灯：

> 板体候选数跨过阈值（如现网 `CS188 lecture 2` 已 27/30，再加 4 节即到）后，
> 在**前部**插入一节，尾部一条「仍在板上、一字未动」的小节就被挤出窗口，
> diff 报一条 `removed`，还附一个指向未改动文件的具体锚点。

所以告警条件是 `over_threshold`（而不只是阈值不等），并且每条可疑的
`added`/`removed` 都打 `truncation_suspect` 标记（§8.4a）。
硬门：`TestDiffGuards::test_mismatched_scale_gate_raises_a_visible_warning`
与 `TestReviewRegressions::test_truncation_suspect_flagged_when_board_grows_past_same_threshold`。

---

## 九、裁判与证据

| 项 | 位置 |
|---|---|
| 裁判测试（**110 条**，含 §4 边界矩阵 `TestUnstableSurface`/`TestStableSurface` 与三轮对抗审查回归门 `TestReviewRegressions`/`TestRound2Regressions`/`TestRound3Regressions`） | `backend/tests/skills/test_split_stable_id.py` |
| 对抗审查存档（Codex + 6 镜头 workflow） | `_bmad-output/审查/codex-review-CARD-G5-3.md` |
| G5-2 存量裁判（34 条，本卡只改 1 行版本断言） | `backend/tests/skills/test_split_preview.py` |
| 先红存证 | `_bmad-output/审查/g5-3-evidence/red-before-impl.txt` |
| live 真实板取证（两板两跑 + diff + 基线对账） | `_bmad-output/审查/g5-3-evidence/run_live_evidence.sh` 与同目录产物 |
| 四态实景演示（真实内容） | `_bmad-output/审查/g5-3-evidence/run_four_state_demo.sh` / `four-state-demo-summary.txt` |

---

## 十、升级路径（`split-anchor/v2` 时怎么办）

改动参与 §2.1 载荷计算的东西（命名空间、归一化规则、occurrence 计数口径、编码方式、
截断长度）会让 ID 变化。⚠ 措辞纠正（Codex round-5）：并非「全部 ID 都变」——
改命名空间/编码/截断长度确实全变，但改归一化规则或 occurrence 口径**只影响受该规则波及的键**
（例如只有含编号标题的、或处在重复标题组里的候选才会变）。无论哪种都按下面走：

1. 必须同时把 `STABLE_ID_NAMESPACE` 提升到 `split-anchor/v2`、`ID_STABILITY` 提升到
   `split_anchor_v2`、前缀提升到 `bsa2-`；
2. 同步更新**校验规则**：`_ID_RE` 目前硬编码 `^bsa1-[0-9a-f]{16}$`，且
   `load_preview_json` 要求顶层 `stable_id_namespace` **等于引擎自身常量**——
   v2 落地时这三处（前缀正则、命名空间常量、自陈值）必须一起改，
   否则 v2 引擎会拒收自己的产物；
3. 已落盘节点 frontmatter 的迁移靠 `split_id_namespace` 字段识别代际，
   按 §7.4 的 `split_stable_id_prev` 链承接。

**跨命名空间比对守卫已就位**（不留到 v2 那天再补）：`--diff` 要求两侧
`stable_id_namespace` 存在且相等，不等即拒绝比对。理由是失败模式很难看——
两代 ID 之间毫无可比性，不拒的话会产出一份「全部候选互报 removed + added」的假 diff，
读起来像整块板被重写了。硬门：`TestDiffGuards::test_rejects_cross_namespace_compare`
与 `::test_rejects_missing_namespace`。
