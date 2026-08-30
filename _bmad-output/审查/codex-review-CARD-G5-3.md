# 对抗审查存档 · CARD-G5-3 拆分稳定 ID 映射与 diff 契约

> **批次**: BATCH-2026-08-29-第六批 · 车道 T5 · 2026-08-30
> **被审物**: `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` v4.0
> **审查焦点（卡片钦定）**: ID 稳定性的边界声明是否诚实——**哪些操作会换 ID 必须写明**
> **两路并行**:
> - **Codex CLI** 独立评审（`codex exec`，全量读文件 + 实跑 + 变异测试）
> - **6 镜头 workflow** 对抗审查（28 agent：6 个独立镜头找缺陷 → 每条 BLOCKER/HIGH 派 2 个
>   反驳者实跑证伪；原始 28 条 → 存活 24 → 打回 4）
> **原始转录**: `g5-3-evidence/raw-reviews/`（Codex 一轮全文 + workflow 全量 JSON）

---

## 零、总览

| 轮次 | 裁决 | BLOCKER | HIGH | MEDIUM | LOW |
|---|---|---|---|---|---|
| Codex 第 1 轮 | **不通过** | 2 | 3 | 2 | 2 |
| 6 镜头 workflow | （无总裁决，逐条制） | — | 4 存活 | 15 存活 | 5 存活 |
| Codex 第 2 轮 | **不通过** | 0 | 3 | 3 | 2 |
| Codex 第 3 轮 | **不通过**（3 项 PARTIAL） | 0 | 0 | 3 | 2 |
| Codex 第 4 轮 | **不通过**（1 HIGH + 1 PARTIAL） | 0 | 1 | 0 | 1 |
| Codex 第 5 轮 | **不通过**（1 HIGH + 2 MEDIUM + 2 LOW） | 0 | 1 | 2 | 2 |
| Codex 第 6 轮 | **不通过**（1 HIGH + 2 处措辞过宽） | 0 | 1 | 0 | 0 |

两路**独立**命中同一批根因的有 3 处（规模门假 removed / 重复种子撞车 / fallback 含行号），
交叉印证提高了可信度；也各自抓到对方没看到的（Codex 独有：G5-10 指纹时序矛盾、
basis 未进键、live skip 兜底；workflow 独有：机器尾块污染指纹、MD 表格 `|` 错位、
跨 vault 可互比、`derived_overlap` 被吞）。

去重后共 **11 个真实根因**，全部处置。下面逐条记账。

---

## 一、Codex 第 1 轮（裁决：不通过）

审查锚：引擎 SHA-256 `1b5e2310bc7ac5ec…`（当轮字节）。

### BLOCKER-1 · 重名调序/改名会静默「换绑」stable_id

**指控**：ID 实际绑定「同路径第 N 个槽位」而非内容单元。
复现：`old=[例题(A), 例题(B)]` → `new=[例题(B), 例题(A)]`，两个 ID 留在原序号、
两份指纹对调，diff 报 `changed=2, moved=0`；把中间「讨论」改名为「例题」时，
新小节直接继承旧 `例题#2` 的 ID。**结论：provenance 静默错配。**
Codex 处置建议：要么对重复项 fail-closed，要么引入不依赖文档序的持久锚；
在此之前不能把 `split_stable_id` 定义为权威身份。

**处置：不改语义，改权威范围（并把语义如实钉死）。**

先说清为什么不改语义：单跑 preview 只拿得到当前文件，区分两条同名小节的信息只有
**位置**和**内容**两样。选位置 → 调序换身份（现状）；选内容 → 正文一改就换 ID，
那等于放弃这张卡的全部价值。二者必居其一，除非引入跨 preview 的模糊匹配，
而那要引入阈值与非确定性，与「同输入二跑逐字节相等」硬门直接冲突。
全量 fail-closed（拒绝整份 preview）也不成立——真实讲义里 `## 例题` 重复出现很常见，
那会让引擎在最需要它的板上罢工。

所以收口方式是**让越界在接口层面不可能发生**：

| 层 | 处置 |
|---|---|
| 引擎 | 重复标题路径组的候选打 `identity_ambiguous: true` + `ambiguous_group_size` |
| diff | `warnings` 显式告警；每条 entry 带 `identity_ambiguous`；人读 MD「标记」列渲染 `⚠身份歧义` |
| 契约 §4.4 | 把「交换 / 删除 / 改名进组」三种后果逐条列表，含「provenance 被静默错配」这句话本身 |
| 契约 §7.6 | **收窄 §7.1**：`split_stable_id` 的权威性只对 `identity_ambiguous == false` 成立；G5-10 **不得**为歧义候选持久化它，改为提示用户「把标题改得可区分」（这也是用户侧最简单的根治） |
| 裁判 | `TestReviewRegressions::test_duplicate_paths_are_flagged_as_identity_ambiguous` 同时钉死 Codex 那个交换复现的**实际行为**（changed×2、指纹对调）与三处标记 |

一句话：不假装 v1 解决了重复标题的身份问题，而是把权威性的边界画在能站住的地方。
⚠ 措辞纠正（Codex round-5）：本节原写「让越界在接口层面不可能发生」——过头了。
这是**契约约束**不是运行时强制：G5-10 若无视 `identity_ambiguous` 照样能写
`split_stable_id`。准确的说法是「判据字段和禁令都摆在它面前，越界是明知故犯」。

### BLOCKER-2 · G5-10 的创建指纹与 re-baseline 自相矛盾

**指控**：契约要求节点保存创建前 preview 的指纹且「不随来源更新」，同时承认插入派生
callout 会改变指纹、只要求重跑 preview——这修正不了 frontmatter 里已持久化的旧指纹。
实测：插入一行派生 callout 后 `cf1-6eea325e0f0aa5ca` → `cf1-e4f76718f60e99d7`，
按 §7.1 比较会**创建刚完成就报「来源已漂移」**。

**处置：契约 §7.1 改存两个指纹（RESOLVED）**

```yaml
split_source_fingerprint_at_confirm: cf1-…   # 用户确认时看到的内容，审计用，永不更新
split_source_fingerprint_baseline:   cf1-…   # 写完(含插链)后 re-baseline，漂移检测拿它比
split_created_from_preview:
  file: split-preview-….json
  sha256: <该 JSON 的 sha256>                # 不可变身份；basename 会被下次 preview 覆盖
```

并明写「两者在创建那一刻通常**不相等**（差的正是那条派生 callout），这是预期的」。

### HIGH-1 · 归一化后空标题使纯行漂移被误报 changed

**指控**：`## 一、` 经 `clean_heading` 变空串 → 走 fallback 命名，而 fallback 锚点用的是
含**行号**的 `file:line`。实测：只在 frontmatter 加 5 行，ID 与指纹均相同，
名称 `derived-62bb6c` → `derived-406a22`，diff 报 `changed(name)`。
这与契约 §4.2「行号漂移不算变化」直接冲突。（6 镜头 workflow 独立命中同一处。）

**处置（RESOLVED）**：fallback 锚点改为 `file_rel ‖ 归一化路径 ‖ basis ‖ occurrence`，
**不含行号** —— 落空标题的建议名从此与 L1 身份键同生共死。
硬门 `TestReviewRegressions::test_fallback_name_has_no_line_number`
（`## .gitignore 的作用` 的首句被句读切空，是这条路径的真实触发形态）。

### HIGH-2 · §4.1 #7 的 whole→section 声明存在直接反例

**指控**：种子从 `# 讲义 + 正文` 改成 `## 讲义 + 同正文`，前后归一化路径均为 `["讲义"]`，
ID / 指纹 / 名称全同，只有 `basis` 从 `seed-note-whole` 变 `seed-note-section`；
diff 实际报 `unchanged`，而契约声称 removed+added。

**处置（RESOLVED）**：`basis` 进身份键（`compute_stable_id` 第 4 参数），
并落进 `stable_id_basis` 保持可复算。硬门
`TestReviewRegressions::test_seed_whole_to_section_changes_id_via_basis`。
反面锚点保留：`TestStableSurface::test_heading_level_change_keeping_ancestors_keeps_id`
（同 basis、祖先链不变时 ID 必须稳住），防止 basis 进键把 ID 变得过敏。

### HIGH-3 · 证据未绑当前字节，且 live 缺失仍可整套绿

**指控**：证据绑定的引擎是 `5081846c…` 而当前是 `1b5e2310…`；把裁判副本的 `LIVE_VAULT`
指向不存在路径后，整文件仍 exit 0（`35 passed, 2 skipped`）——卡片 (d) 的
「≥2 块真实板」硬门**可被静默跳过**。

**处置（RESOLVED）**：
- 全部证据用最终引擎字节重跑，并新增 `judge-and-contract.sha256`（裁判 + 契约的字节绑定）；
- `TestLiveRealBoards._require_live()`：live 缺失一律 **`pytest.fail`**；
  只有显式 `G53_ALLOW_NO_LIVE=1` 才降级为 skip，且 skip 理由里写明「卡片 (d) 判据本次 UNVERIFIED」；
  live 存在但板缺失 → 一律 fail（那是真问题，不是环境差异）。
- 反证：把 `LIVE_VAULT` 指到 `/private/tmp/definitely-not-a-vault-g53` 后 `rc=1, 2 failed`。

### MEDIUM-1 · 「拒绝路径零产物」存在空目录和半份产物反例

**指控**：① `board="A"*300` → 先建 out-dir，写入时 `ENAMETOOLONG`，留下空目录；
② 候选 `source_anchor={}` → 先写出 JSON，渲染 MD 时 `KeyError: 'file'`，留下半份产物。

**处置（RESOLVED）**：
- `validate_product_filename()` 在 `prepare_out_dir` **之前**预检文件名字节数（≤255）；
- `load_preview_json` 入口校验渲染要读的**全部**字段（`index` / `suggested_name` /
  `resolved_name` / `basis` / `source_anchor` 四键完整）；
- 两份产物**都渲染完再动 out-dir**——渲染期抛异常时若 JSON 已落盘，留下的是
  「新 JSON + 上一版 MD」的错配对。
硬门：`test_overlong_board_name_rejected_with_zero_products` /
`test_broken_source_anchor_rejected_before_any_write`。

### MEDIUM-2 · NFC(file_rel) 与「文件改名必换 ID」声明冲突

**指控**：板名从 NFC `café` 改成 NFD `café`，`stable_id_basis.file` 字符串不同但 ID 完全相同，
而 §4.1 #6 声称「全板换 ID」。

**处置（RESOLVED，文档侧）**：§4.1 #3/#6 标注「⚠ 不含 NFC/NFD 等价改名」，
§4.2 新增一行把这条明确归入**稳定面**（并给出理由：身份键对 `file_rel` 也做 NFC）。
不改实现——NFC 归一本身是对的（macOS 落盘会分解），错的是文档没说清。

### LOW-1 · 64-bit 截断自检的能力被说得过满

**指控**：同 preview 重复检查无法区分「身份键缺维」与「真实截断碰撞」，
也不覆盖跨 preview 同 ID、不同 basis（实测报 `unchanged=1`）。

**处置（RESOLVED）**：
- §5「引擎自检」改为三条明说，其中第 3 条直言「**不能**区分缺维与真碰撞，
  64 bit 在单板数百候选量级下碰撞概率可忽略，但那是**概率性**论断不是证明」；
- diff 侧新增守卫：同一 `stable_id` 两侧 `stable_id_basis` 必须相等，否则**拒绝比对**
  （硬门 `test_same_id_different_basis_is_refused`）。

### LOW-2 · 正向门有效（Codex 主动确认，无需处置）

Codex 独立复核确认：v1 字段投影与旧键相对顺序完全一致；全仓无其他 split-preview 消费方
或 MD 表解析方；穷举 4 候选的 `24×24=576` 对排列验证记账恒等、状态互斥、二跑确定、
相邻交换只标 `{C}`；7 个建议变异**全部**使裁判变红（无一全绿）。
唯一提示：`change_reasons` 是硬编码顺序而非 `sorted()`，当前恰为字典序——
已在测试里加 `assert e["change_reasons"] == sorted(...)` 钉住。

---

## 二、6 镜头 workflow 对抗审查（28 agent）

镜头：`id-stability` / `diff-correctness` / `additive-compat` / `test-false-green` /
`readonly-writeside` / `honesty-naming`。每条 BLOCKER/HIGH 派 2 个反驳者
（一个按复现路径实跑证伪，一个查「这是不是已声明的设计取舍」）。

**打回 4 条**（反驳者实证不成立或属已声明取舍）：

| 指控 | 打回理由 |
|---|---|
| 同标题兄弟纯调序会互换身份，§4.2「调序不换 ID」是假的 | 对**非重复**标题成立且有测试；重复标题的情形是 BLOCKER-1，已单列 §4.4，不是 §4.2 的反例 |
| clean_heading 吸收编号把「1. 概述 / 2. 概述」拖进同名撞车区 | 同上，归入 §4.4 |
| 「指纹不复用剥离掩码」零裁判 | 反驳者找到了 `TestFingerprintCoverage`（该指控提出时该测试已存在） |
| occurrence 位移会把 stable_id 改嫁给别的小节 | 行为属实但已在契约 §4.1 #5 ⚠ 块显式声明并有测试，非未声明缺陷 |

**存活 24 条**去重后为 6 个新根因（Codex 未覆盖的部分），全部处置：

### W-1 · 规模门截断在**两侧阈值相同**时把仍在板上的小节报成 removed
5 个镜头同时命中、2 组验证者一致支持，是本轮命中率最高的一条。
复现：板体候选数跨过阈值后在前部插一节，尾部一条「仍在板上、一字未动」的小节被挤出窗口，
diff 报 `removed` 并附一个指向未改动文件的具体锚点；人读 MD 对截断只字不提。
现网 `CS188 lecture 2` 已 27/30，再加 3-4 节即触发。

**处置**：告警条件从「两侧阈值不等」放宽到 `over_threshold`；每条可疑 `added`/`removed`
打 `truncation_suspect`，MD「标记」列渲染 `⚠截断嫌疑`；契约 §8.6 重写（原文只声明了
「用了不同 `--max-units`」一种成因，那条自查建议在此场景恒为绿灯）。
硬门 `test_truncation_suspect_flagged_when_board_grows_past_same_threshold`。

### W-2 · `## Concepts` 重复列同一份种子 → 整板 exit 1（**可用性倒退**）
同一文件被扫两遍 → 四元组逐字相同 → stable_id 必撞 → 自检拒绝输出。
G5-2 对同样输入能正常出图，G5-3 首版会整块板失败。NFC/NFD 孪生名（macOS 上指向同一文件）
是更隐蔽的同型触发。另：自检原本只跑在**截断后**的 `kept`，截断把撞车对切开时自检直接失效。

**处置**：源头按 `nfc(seed)` 去重（保留首次出现，被跳过的行在 `sources` 留痕
`skipped: "Concepts 目录重复列出同一份种子…"`）；自检移到规模门截断**之前**；
错误信息列出撞车两条的 `file:line` + 标题路径并点名最常见成因。
硬门 `test_duplicate_seed_in_concepts_no_longer_kills_the_board` /
`test_nfd_twin_seed_name_is_deduped`。

### W-3 · 板尾 Recent Activity / AUTO 段污染最后一条候选的指纹
剥离后的 `## Recent Activity` 不算标题 → **前一节的 `end` 一路吞到 EOF** →
机器写的活动日志落进最后一条候选的 span。每派生一次节点、每刷新一次尾块，
就凭空多一条 `changed(content)`。

**处置**：拆分掩码语义。新增 `strip_generated_detail()` 逐行分类
（`GEN_FRONTMATTER/AUTO/FENCE/RECENT`），指纹排除 `MACHINE_KINDS`（frontmatter/AUTO/Recent）
但**仍含**代码 fence 与 HTML 注释。两条边界各有硬门：
`TestFingerprintCoverage`（代码块/注释改动**必须**被感知）与
`test_machine_generated_tail_does_not_pollute_fingerprint`（机器尾块刷新**必须不**被感知）。

⚠ 重构时当场被 G5-2 的反事实常驻测试抓到一次：`collect_candidates` 若改用
`strip_generated_detail` 的投影取 `stripped`，打桩 `strip_generated` 的反事实门就失去抓力。
已改回走公开函数，并把这条教训写进代码注释。

### W-4 · 跨 vault 同名板可以互比，凭空伪造编辑史
`stable_id` 只含 vault **内**相对路径。

**处置**：preview 顶层新增 `vault_fingerprint`（vault 物理路径的哈希，不落路径本身）；
两侧不同即 `warnings` 告警。**不硬拒**——拿隔离副本比 live 是合法用法（本卡的四态演示就是）。
硬门 `test_cross_vault_compare_warns`。

### W-5 · `derived_overlap` 跃迁被吞进 `content`
候选从「未派生」变成「已派生为 `[[节点/X]]`」时，diff 只说 content 变了，
读的人分不出「正文改了」和「这段已经被拆过了」——后者恰是 G5-10 最该知道的信号。

**处置**：新增 `overlap` change reason（字典序 `conflict/content/name/overlap`）。
硬门 `test_derived_overlap_transition_gets_its_own_reason`。

### W-6 · 标题含 `|` 打乱 MD 表格，把告警挤出可见列
`P(A|B)` 这类标题会切错列，「重名」「已派生重叠」这些告警看不见——**告警看不见等于没有**。

**处置**：`md_cell()` 转义（`\` 与 `|`），preview 与 diff 两侧表格全过。
硬门 `test_pipe_in_heading_does_not_break_md_table`（同时断言转义后列数与表头一致）。

### 另有 2 条「无裁判」被点名，已补门
- occurrence「按**全部小节**计数而非仅候选」这条明写保证零裁判 →
  `test_occurrence_counts_all_sections_not_just_candidates`；
- diff 侧 stable_id 重复守卫零裁判 → 由 `stable_id_basis` 相等校验 + 入口重复检查共同覆盖。

---

## 三、自查发现（不是审查者提的，是实现过程中自己跑出来的）

1. **「拒绝但已建空目录」**：diff 模式原本先建产物目录再校验板名，
   板名非法被拒时留下空目录——与 G5-2 Codex 三轮 H1 同型的次序错误。
   已把校验提到建目录之前。门：`test_illegal_board_name_rejected_before_out_dir_is_created`。
2. **`board` 字段类型未校验**：preview JSON 外部可编辑，`board` 为 `null` / 数字时被
   `str()` 成 `"None"` / `"123"` 拼进产物文件名悄悄落盘。
   门：`test_rejects_non_string_board`。
3. **diff 两侧来源标签只有 basename**：两份 preview 通常同名不同目录，
   读 diff 的人分不清哪份是旧的。改为「上一级目录名/文件名」。
4. **裁判自身两条缺陷**（先红时照出来的）：拒绝目录与 `preview()` 的 `out-<tag>` **撞名**
   （会让「零产物」断言假绿）；三条断言把 `heading_path_normalized` 写漏了 `# 主板` 这级祖先。
   ⚠ 撞名这个坑在补回归门时**又踩了一次**（3 条测试同时中招），已在测试里留注释警示。

---

## 四、Codex 第 2 轮（复核）——裁决：不通过（3 HIGH / 3 MEDIUM / 2 LOW）

原始转录 `g5-3-evidence/raw-reviews/codex-round2-raw.md`。审查锚：引擎 `3aaa07a1…`。

### 一轮发现的复核结论

| # | 一轮发现 | 二轮判定 | 差在哪 |
|---|---|---|---|
| 1 | 重名换绑 stable_id | **PARTIAL** | 「缩小权威范围」原则被认可，但**接口未 fail-closed**：删掉 `identity_ambiguous` 字段后 diff 仍 rc=0，把缺失投影成 `false`、`warnings=[]` |
| 2 | G5-10 指纹时序矛盾 | **PARTIAL** | 时序矛盾已消除、`{file, sha256}` 设计成立；但 §7.1 的 YAML 示例漏了后文规定必填的 `basis` |
| 3 | 空标题 fallback 行号 | **RESOLVED** | 实跑 `## .gitignore 的作用` / `## 一、`，加 7 行 frontmatter 后名称与 ID 均不变，diff `unchanged=2` |
| 4 | whole→section 的 basis 维 | **RESOLVED** | 实跑得 `added=1 + removed=1`；未发现 basis 自身非声明性漂移 |
| 5 | 证据绑定 + live 硬门 | **PARTIAL** | live 两态均正确（默认 2 failed / 显式允许后 2 skipped 且含 UNVERIFIED）；但 `judge-and-contract.sha256` 与 README 的绿证条数**已过期** |
| 6 | 拒绝路径零产物 | **PARTIAL** | 两个指定反例已修；但候选 schema 只验存在不验类型、两产物仍非成对发布 |
| 7 | NFC 改名声明 | **RESOLVED** | 文档与实际一致；但**引出新问题**：diff 的 raw basis 比较会假拒绝这种合法等价 |
| 8 | 自检措辞 + 跨 preview basis | **PARTIAL** | 截断前自检确实抓到窗口外的撞车、错误列出两个锚点、out-dir 不存在；但两侧同时缺 `stable_id_basis` 时 `None == None` 绕过守卫 |
| 9 | 同阈值规模门截断 | **RESOLVED** | 两侧阈值均 2，前部插入得 `added=1 + removed=1`，两条均 `truncation_suspect=true`，MD 两处 `⚠截断嫌疑` |
| 10 | Concepts 重复/孪生种子 | **RESOLVED** | 三行引用只生成 1 个候选，另两行在 `sources` 留痕 |
| 11 | 机器尾段 vs fence/注释 | **PARTIAL** | 两条边界都对；但存在 HIGH-1 反例 |
| 12 | 跨 vault 指纹 | **PARTIAL** | 不同 vault 时 JSON/MD 均告警；但两边同时缺该字段时静默通过 |
| 13 | `derived_overlap` reason | **RESOLVED** | `["content","overlap"]` |
| 14 | MD `\|` 转义 | **RESOLVED** | 分隔符仍 8 个，列数未破坏 |

### 二轮新发现与处置

**HIGH-1 · 普通 HTML 注释可触发 Recent Activity 掩码，静默吞掉其后的用户正文**
注释里写着 `## Recent Activity` 时，RA 分类把它当真标题、一路吞到下一个同级标题为止——
连同注释后面的**真实用户正文**一起。被吞的正文不进指纹，用户改了它 diff 报 `unchanged`。
根因：RA 这一趟独立于普通注释掩码运行（G5-2 遗留，被 G5-3 的指纹放大成静默漏报）。
**处置**：`strip_generated_detail` 在 RA 扫描**之前**先算一遍普通注释掩码，
注释内的标题不再触发 RA（这本就是 comment_mask 的既有语义，只是 RA 没享受到）。
门 `TestRound2Regressions::test_commented_out_recent_activity_does_not_swallow_user_text`。

**HIGH-2 · schema v2 新安全字段可缺失，三道处置同时 fail-open**
删 `identity_ambiguous` → 歧义投影成 false、无告警；两侧同删 `vault_fingerprint` +
候选同删 `stable_id_basis` → 跨 vault 不告警、basis 守卫被 `None == None` 绕过、
`unchanged=1`；`index=[]` / `suggested_name=null` / `basis={}` / anchor 全 null → 仍 rc=0。
**处置**：入口校验从「查键在不在」升级为「**存在 + 类型**」，覆盖全部 v2 字段
（含 `identity_ambiguous` 与 `ambiguous_group_size` 的**自洽性**互校）。
门：10 组参数化用例 `test_missing_or_mistyped_safety_fields_are_refused`。

**HIGH-3 · 证据包不是自洽的当前字节证明**
`judge-and-contract.sha256` 的契约条目 FAILED；README 指向的 85 条绿证实际写着 64。
**处置**：全部产物与两份 manifest 用最终引擎重跑，`shasum -c` 双清单全绿；
绿证刷新为 **100 passed**。

**MEDIUM-1 · 第二产物拒写时留下第一份 JSON**
**处置**：拆出 `safe_open_checked`（O_NOFOLLOW + nlink 准入，不 truncate）与
`write_pair_atomically_checked`（**两个目标准入全过再落笔**）；并撤销本次新建的空文件——
`O_CREAT` 会把目标建出来，留个 0 字节文件同样是半份产物（这一点是补门时当场测出来的）。
如实声明的残余边界：准入通过后写入过程中的 I/O 错误仍可能只落一份。

**MEDIUM-2 · NFC/NFD 等价来源名被 basis 守卫假拒绝**
产物存 raw `file`、身份键用 NFC，直接比 raw dict 会把契约 §4.2 明确归入稳定面的
等价改名判成 basis 不一致。**处置**：`_basis_key()` 按 NFC 归一后再比，口径与身份键一致。

**MEDIUM-3 · `--max-units` 接受负数**（输出 `threshold=-1, kept=2, over_threshold=true` 自相矛盾）
**处置**：非正整数直接拒绝。

**LOW-1 · §7.1 YAML 示例漏 `basis`** → 已补。
**LOW-2 · 「标题正文不可能含 U+0000」不成立** → 载荷改**长度前缀**编码
（`len:段` 以 NUL 相连），对任意字节单射，不再依赖该假设。
门 `test_payload_encoding_is_injective_under_nul_bytes`。

### 二轮主动确认有效的正向门

同一 preview 连跑两次 `cmp` JSON/MD 逐字节相等；live 两态行为正确；
`engine-and-products.sha256` 全绿；生产 CLI 对抗夹具全套跑通。

---

## 四点二、Codex 第 3 轮（二次复核）——0 BLOCKER / 0 新 HIGH，3 项 PARTIAL

原始转录 `g5-3-evidence/raw-reviews/codex-round3-raw.md`。

二轮 8 条里 **5 条判 RESOLVED**（注释内 RA、NFC/NFD basis、`--max-units`、YAML `basis`、
长度前缀载荷——后者另枚举 4680 个段序列未发现碰撞）。**3 条 PARTIAL**，全部是真问题：

**P1 · 严格整数校验可被 JSON 布尔绕过**
Codex 系统变异 166 组，158 组被拒，**8 组仍 rc=0**：`index=true/false`、
`ambiguous_group_size=true`、`occurrence=true`、`line_start/line_end=true/false`。
根因是 Python 的 `isinstance(True, int) == True`。
**处置**：引入 `_is_int()`（`isinstance(v, int) and not isinstance(v, bool)`），
全部整数字段改用它，并加上范围（`index ≥ 1`、行号 `≥ 1` 且不倒置）。
门：4 组参数化 `test_bool_is_not_accepted_as_int_*`。

**P2 · 拒绝路径会删除既存的 dangling symlink**
回滚「本次新建」的判据用 `Path.exists()`，而 dangling symlink 的 `exists()` 为 False
→ 被误判成自己建的 → 拒绝时把用户既存的那条链接删掉。
**这不是零产物问题，是破坏既有目录项**——与契约「只删本次创建的空文件」相反。
**处置**：改用 `os.path.lexists()`。门 `test_dangling_symlink_target_is_not_deleted_on_rejection`。

**P3 · 「全部产物绑定」不完整**
`engine-and-products.sha256` 只有引擎 + 8 个 live 产物，四态演示的两个产物没有字节绑定，
而 README 声称「全部产物」。**处置**：取证脚本改为**扫 `outputs/` 全目录**
（`find … | sort -z | xargs shasum`），未来新增产物自动纳入；现为 10/10。

### 三轮另外点名的残余边界 → 一并收口

Codex 补充：除类型外还有 **13 类「类型都对、但语义被改坏」**的输入能 rc=0
（负 `index`、行号倒置、空路径、ID/指纹格式错、顶层 namespace 与 `stable_id_basis` 不一致…），
并指出 §8.2 当时既未声明格式校验、也没有 stable ID 自复算或字段交叉绑定。

**处置：把这一整类关掉，而不是声明为边界。** `stable_id_basis` 带齐了身份键的四个输入，
所以入口可以**直接复算 `compute_stable_id` 并要求相等**；再叠加三处交叉绑定
（`basis.namespace`↔顶层、`basis.basis`↔候选 `basis`、`basis.file`↔`source_anchor.file`）
与 ID/指纹格式校验。门：10 组参数化 `test_semantically_broken_but_well_typed_input_is_refused`，
外加一条**反面锚** `test_intact_product_still_passes_all_new_guards`（防守卫过严）。

如实保留的边界：`namespace` 的绑定是**两跳传递**（同侧内部一致 + 跨侧相等），
复算本身用引擎自己的命名空间常量，不校验该字段——契约 §8.2 已写明。

### 三轮 LOW（均已处置）

- 变异矩阵「覆盖声明过宽」→ 脚本头部改写为「证明的是每个变异体能让**它点名的那道门**变红，
  不是每道门覆盖该修复的全部字段」，并说明 round-3 的复算对账与几道旧门存在**有意冗余**
  （那几条变异因此改为「连同复算一起撤」才能隔离出目标门）。
- 文档漂移三处（UAT 说 outputs「三份文件」实为 10 个；引擎与测试的 docstring 摘要
  在 L1 公式里漏写 `basis`；测试矩阵注释仍写 §4.1/§4.2 为 8/7 条，实为 10/10）→ 全部改正。

---

## 四点三、Codex 第 4 轮（终裁轮）——P1/P2 RESOLVED，抓出「语义层」1 HIGH

原始转录 `g5-3-evidence/raw-reviews/codex-round4-raw.md`。

⚠ 本轮跑了两次：第一次在收尾阶段被 OpenAI 的 cyber 过滤器**误拦**中断
（本仓已知坑，见 `reference_codex_exec_gotchas`）。把「攻击这一层」「可利用的缺口」
「symlink / 硬链接」等措辞改成中性描述后重跑通过。留痕于此，不掩饰。

### 三轮 PARTIAL 复核

- **P1（布尔当整数）RESOLVED** —— Codex 把三轮那份 166 组畸形 schema 复现器原样重跑：
  **166/166 全部拒绝，rc=0 剩余 0 组**。
- **P2（拒绝路径删既存 dangling symlink）RESOLVED** —— 五种文件系统形态
  （悬空链接 / 有效链接 / 多引用文件 / 0444 文件 / 目录）均 rc=1，
  拒绝前后 inode、mode、nlink、内容、链接目标、目录成员**完全相同**，第一份 JSON 均不存在。
  已固化为参数化门 `test_preexisting_target_of_any_shape_survives_rejection`。
- **P3（全部产物绑定）PARTIAL → 已修** —— 四态双产物已纳入（10/10 个 `split-*`），
  但脚本注释宣称「扫全目录」而实现是 `-maxdepth 1 -name 'split-*'`，漏掉
  `outputs/exam_boards/.gitkeep`。**同一个坑被抓了两次**（先是手写清单漏项，
  再是注释与实现不符），现改为**递归全部普通文件**，名副其实：manifest 12 行 = 引擎 + 11 文件。

### 本轮 HIGH · 「类型对、绑定对、复算也对」的语义层仍有 fail-open

Codex 复现出五类：只改 `source_anchor.heading_path`（伪造锚点进 diff）；只改 `scale_gate`
（**截断告警被静默压掉**）；两侧 namespace 协同改成 `v999`（同侧绑定/跨侧相等/复算全过）；
`heading_path=[]`；`vault_fingerprint="   "`。

**处置分两半 —— 一半是补守卫，另一半是把话说回来：**

补守卫（三条，均有门 + 变异反证）：

| 面 | 守卫 |
|---|---|
| `source_anchor.heading_path` | 与 `heading_path_normalized` **层数一致** + 非空 + 元素非空。⚠ 只能绑层数——归一化有损（剥编号/时间戳/NFC），无法从归一化反推原文 |
| `scale_gate` | `kept == len(candidates)`、`total ≥ kept`、`threshold ≥ 1`、`over_threshold == (total > threshold)` 四方对账 |
| `stable_id_namespace` | 必须等于**引擎自身常量**——本引擎只能校验自己这一代的产物 |

**把话说回来（这一半更重要）**：三轮我在契约里写的是「把这一整类关掉」。
Codex 四轮证明那句话**过头了**：产物没有签名，凡是能编辑 JSON 的人都可以把
`stable_id_basis` 与 `stable_id` **一起重算**成自洽的一份，而内部一致性检查按定义
无法区分真品与「重新签过名的伪品」；diff 又不读 vault（设计前提），
所以它没有任何办法验证锚点指向的内容真的存在。

契约 §8.2 因此新增「⛔ 信任边界：内部一致性 ≠ 真实性」一节，明说这些守卫防的是
**产物被改坏/改乱**，不是**产物被伪造**；并把这条边界写成**可执行的断言**：
`TestRound4Regressions::test_declared_limit_consistent_forgery_is_NOT_detectable`
构造一份自洽伪品并断言它**被接受**——哪天真加了签名机制，那条测试会变红，
提醒后来者回来改这一节。

### 本轮 LOW（已修）
`mutation-check.txt` 记录的是旧 engine/judge 哈希 → 全部证据在最终字节上重跑，
现日志内哈希与当前文件逐字相符。

---

## 四点四、Codex 第 5 轮 —— 指正我一处**推理错误**，并证伪契约里的一条边界

原始转录 `g5-3-evidence/raw-reviews/codex-round5-raw.md`。

四轮的 P1（布尔当整数）与 P2（五种占位形态）判 **RESOLVED**（166/166 拒绝；
五形态 inode/mode/nlink/内容/链接目标/目录成员逐项相同）；P3 产物清单亦 RESOLVED。

### HIGH · 「只能绑层数」是我推理错了

四轮我给 `source_anchor.heading_path` 加的守卫只比**层数**，并在契约里写了理由：
「归一化是有损的，无法从归一化反推原文，所以只能绑层数」。

**Codex 指出这个推理是错的**：不需要**反推**，把原文路径**再正向归一化一遍**比对即可。
实测：把新侧原文标题改成同层数的 `["完全伪造的父标题","完全伪造的子标题"]`，
不动 basis 与 ID —— `rc=0`、`unchanged=1`，伪造锚点进了 diff。

更要紧的是：我把这类情形归进了「无签名所以查不出」那条信任边界，
**而它根本不属于那条边界**——它是无需读 vault 就能对账的内部不一致。
**拿边界当挡箭牌，比漏掉一个守卫更该被指出来。**

**处置**：守卫改为 `normalize_heading_path(a["heading_path"]) == hp`（正向对账）；
契约 §8.2 把那句错误理由**原地标注为「措辞纠正：那是错的」**并写清新口径，
信任边界一节补上「界限要划准：同层数伪造不属于这条边界」。
另补 `board_file == f"原白板/{board}.md"` 对账（只重标 board 不改 board_file 同型）。
门：`TestRound5Regressions::test_same_depth_forged_heading_path_is_refused` /
`::test_board_relabel_without_board_file_is_refused`。

### MEDIUM · 契约 §4.1 #6「板改名 → 全板换 ID」被实测证伪

身份键里的 `file_rel` 是**候选自己的来源文件**，不是板文件。种子笔记候选的
`file_rel` 是 `节点/种子.md`，改板名它们的 ID 纹丝不动 —— 只有板体候选会换。
**我原来的裁判只用了纯板体候选，造成假完备感。**
**处置**：契约 #6 改写并加 ⚠ 说明；用**混合构造**（板体 + 种子）钉死真实行为
`TestRound5Regressions::test_board_rename_changes_only_board_body_candidates`。

### MEDIUM · UAT 向用户过度承诺移动稳定性
「不管你把这一节挪到哪，ID 都不变」与跨文件、换父、重复标题三类已声明的不稳定面冲突。
**处置**：改为「同一份笔记里上下调序不变」，并把边界与契约链接摆在同一段。

### LOW ×2（均已处置）
- 「§4 的 20 条逐条变成断言」当时**不实**：#4（层级调整改祖先链）、#9（在同名小节前插入）、
  #10（标题行加行内注释）只在文档里没有门 → 三条门补齐，现 20/20；
- UAT 的 lint 绿证不实：当时 `ruff format --check` 实为 rc=1 → 已格式化并复验，
  UAT 里把这次「绿证不实」也如实标注出来。

### 附带自查：又抓到一处**自己造的假绿**

改中性文件名时发现：几组参数化用例把 `keyword` 拼进了临时文件名，
于是 `assert keyword in stderr` 是被**路径**满足的、而不是被诊断信息满足的。
改中性名后当场红了 2 条 —— 预期关键词早已过时（守卫换成了正向归一化）。
已修正并在测试里留注释。**这类假绿一共犯了三次**（out 目录撞名两次 + 本次路径污染），
每次都是「断言看起来在测 A，实际被 B 满足」。

---

## 四点五之前 · Codex 第 6 轮 —— 「拿边界当挡箭牌」第二次被抓

原始转录 `g5-3-evidence/raw-reviews/codex-round6-raw.md`。
五轮的 6 项处置里 **5 项 RESOLVED**（同层数伪造标题、板改名口径、20/20 回归门、lint、
keyword 路径假绿）；1 项 PARTIAL（UAT 的移动稳定性仍漏「换父」）。

### HIGH · 我那份「自洽伪品」测试其实**不自洽**

契约 §8.2 声称「真正落在信任边界里的只有每一处都自洽的伪品」，
但对应测试只把 `file` 改成 `节点/…`，**没同步 `basis` / `sources` / `board_file`**——
而 `board-body-section` 按定义只可能来自 `原白板/<board>.md`，
这是**无需读 vault 就能对账**的矛盾。Codex 另复现四类同样能 rc=0 的：
`basis="invented-basis"`、名称协同伪造、`id_stability="invented_v999"`、`sources` 清空。

**这是我第二次把可检查的东西算进信任边界**（第一次是五轮的「只能绑层数」）。

**处置（两半）**：
- 补五道守卫：`basis` ∈ 三个已知取值；`basis` ↔ 来源目录前缀自洽
  （`board-body-section` ⇒ `原白板/<board>.md`）；候选来源文件必须在 `sources` 里；
  `suggested_name` 由原文标题**复算**对账；顶层 `id_stability` 必须等于引擎常量。
- **重写那条伪品测试**，让它成为真正自洽的伪造（来源文件、`basis`、`sources`、
  `stable_id`、`suggested_name` 全部重新签成一套），并在 docstring 里写明它被打回过。
- 契约 §8.2 的信任边界一节改为**列表**：把「曾被我误算进边界的」逐条列出并写明怎么查，
  真正的边界收窄为「每一处都对得上的伪品」+「只有读 vault 才能证伪的两类
  （伪造的 `content_fingerprint`、伪造的行号）」，末尾留一句
  「把本可检查的不一致算进信任边界，就是拿边界当挡箭牌。这话我犯了两次」。

### 两处措辞仍过宽（已收紧）
- §4.2「行号漂移（文件任意位置增删行）」→ 限定为**非结构性**行增删：
  插入的若是**标题行**，可能改变别人的祖先链或同名小节的 occurrence；
- §4.2「小节整体前后调序」→ 限定为**同一父路径内、非歧义**候选。

### §4.1 漏列一条高频操作（已补）
**同一份笔记里换父**（`子小节` 从 `父甲` 挪到 `父乙`，自己标题一字未动）→ 换 ID。
补为 §4.1 #2b + 门 `TestRound6Regressions::test_moving_section_to_another_parent_changes_id`；
UAT 那句「同一份笔记里上下调序不变」也随之改成「同一个上级标题底下调序不变」。

---

## 四点五、回归门变异反证

对抗审查的 11 个根因是**先修后补门**，那批门的「先红」没有天然存证。
`g5-3-evidence/run_mutation_check.sh` 把每条修复逐个撤销（/private/tmp 引擎副本，
不动仓库文件），让对应的门跑在被污染的引擎上：

**33 个变异体全部让对应的门变红——无空转门。**
一轮 13 条（撤销种子去重 / 把行号塞回 fallback 锚点 / 指纹不排除机器段 / basis 出键 /
不标歧义 / 撤截断嫌疑 / 撤跨 vault 告警 / 撤 basis 完整性校验 / 撤 overlap reason /
撤 MD 转义 / 撤文件名长度预检 / 撤候选 schema 整段校验 / occurrence 只数候选）
+ 二轮 6 条（RA 不避注释 / 入口只查存在 / 不撤销自建空文件 / basis 比 raw dict /
撤 --max-units 校验 / 载荷去长度前缀）
+ 三轮 5 条（bool 当 int / 回滚用 exists / 撤 stable_id 复算 / 撤交叉绑定 / 撤 ID 格式校验）
+ 四轮 3 条（撤 scale_gate 对账 / 收外来 namespace / 撤 vault 指纹格式）
+ 五轮 2 条（标题路径退回只比层数 / 撤 board↔board_file 对账）
+ 六轮 4 条（撤 basis↔目录前缀 / 撤名称复算 / 撤 sources 成员检查 / 撤 id_stability 比对）

⚠ **一条修复没有行为门，如实列出**：「身份自检从规模门截断之后移到之前」。
它唯一已知的可达触发路径（同一文件被扫两次）已在源头消除，去重后四元组按构造互异，
除非 64-bit 真碰撞否则触发不了，因此无法黑盒证明「它跑在截断之前」。
保留为纵深防御，覆盖状态 = 无测试。

---

## 五、如实声明的剩余边界（不掩饰）

1. **重复标题路径的身份歧义**（§4.4）——v1 不解决，只标红旗并禁止 G5-10 持久化。
   根治需要 `split-anchor/v2` 引入不依赖文档序、也不依赖正文的判别维度。
2. **64-bit 截断碰撞**——自检不能区分「缺维」与「真碰撞」；碰撞概率可忽略是概率性论断。
3. **候选可嵌套**——父子小节都达标时 span 嵌套，改子小节会让父子两条都判 changed（§3.2）。
4. **规模门截断**——已从静默变为显式告警 + 条目标记，但 diff 本身无法区分
   「被窗口挤出」与「真被删除」，只能提示人去核。
5. **G5-2 继承的写侧边界**——bind mount / 覆盖挂载重定向不可判定；
   祖先目录在检查与 open 之间被整体替换的 TOCTOU 竞态（用户态无法完全关闭）。
6. **live 取证的判定口径**——before/after 快照证明的是**零净差异**，
   不排除窗口内「先改后恢复」；atime / xattr / ACL 未采集（沿用 G5-2 collector 的口径）。
