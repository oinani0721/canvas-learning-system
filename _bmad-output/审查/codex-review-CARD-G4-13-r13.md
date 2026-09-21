# CARD-G4-13 r13 独立复核（只读 · 绑 `fe8952de`，父 `07d5c34b`）

**绑定/方法**：HEAD=`fe8952de`（工作树两文件与 commit 逐字一致；未跟踪仅任务前已存在的 r13 review/prompt 两文件，我未改任何文件）。r12/r13 两版 `gold_set_manifest_tool.py` 由 `git show 07d5c34b:` 载入**同进程**、同一批 fixture 直调 `verify_gold_set_file()`（真路径在位，仅内存替换 load_yaml/sha 输入）；runner 侧用**真纯函数**（`norm_text`/`grade_of`/`forbidden_violations`/`is_contaminated`/`ndcg_at_k`，无 HTTP、无库、无落盘）复算。四真金集走未打补丁的真 verify + 独立重算 sha。承重门 `test_gold_set_manifest_g413.py` 沙箱外实跑一次（80 passed，`-p no:cacheprovider -B`，仓库零写入——跑后 `git status` 复核不变）。未连 7691/7687/8011，未跑任何 runner（含 shadow）。

---

## ① M1/M2 与 LOW-1/2/3 逐条复算（r12 源码 → r13 源码，同 fixture）

| 族 | fixture（节选） | r12 | r13 | 判定 |
|---|---|---|---|---|
| **M1** | `forbidden.markers:[" "]` / `["\u3000"]` / `["\u00a0"]` / `["\u2028"]` | T | **F** | 真关闭 |
| M1 | `contamination.path_globs:[" "]`、`doc_types:[" "]`、`forbidden.path_globs:[""]`、`markers:["TestConcept"," "]` | T | **F** | 真关闭 |
| M1 | `expect_hit:[{file:" "}]`；`id/query/language:" "`；`expect_not_hit.path_glob:" "` | T | **F** | 真关闭 |
| M1 | `expect_any:[" "]`、`leak_markers:[" "]`/`["\u3000"]`（memory） | T | **F** | 真关闭 |
| **M2** | `max_in_top_k:10**400` | T | **F** | 真关闭（数字卫生面） |
| M2 边界 | `10**6`→T；`10**6+1`→F；`-1/True`→F（两版同） | — | — | 边界正确 |
| **LOW-1** | `grade:"²"`、`"２"`、`2000`、`11` | T | **F** | 真关闭（`int("²")` 实测 ValueError、`ndcg_at_k([2000])` 实测 OverflowError） |
| LOW-1 对照 | `3/"2"/2.0/0/10`→T；`2.5/True/-1/None`→F（两版同） | — | — | 无误收 |
| **LOW-2** | `contains:""`/`" "`/`null`/`{}`/`5` | T | **F** | 真关闭（r12 侧 runner 实测：`contains` 假值静默跳过、按声明 grade 计） |
| LOW-2 对照 | `contains:"0"`、`contains:"x"`+`grade:3` | T | **T** | 无误拒 |
| **LOW-3** | `hard_cap:10**400` / `10**6+1` | T | **F**；`10**6`→T | 真关闭 |

文案同步：`expect_hit` 报「file/contains 须非空 str、grade 须 0..10」（`tool:541`）、边界报「不在 [0, 10^6]」（`tool:614`）——与实测接收面一致。

## ② 误拒核查（四真金集 / 未来扩展）

- **四真金集零误拒（独立复算，非引 artifact）**：四份真 verify 全 `True`，sha 独立重算与 manifest **逐字同**（vault 75 / memory 28 / vault-shadow 2 / memory-shadow 0）。vault 8 处 `contains`（含 `"0"`）全非空 str；markers 三条、leak_markers 四条/三条、三组路径/类型列表全非空 str；`delivery{min_relevance:0.50, elbow:0.25, hard_cap:10}`、`max_in_top_k` 实值 0..4 全 T；`contains` 缺失的多数条目走「键不存在不检查」分支，零误拒。
- **未来合法扩展（相对 runner 契约过严，见 LOW-2）**：runner 会 `int()` 收下的 `grade:"２"/" 5"/"+5"`、runner 会强转或默认的 `contains:5`、缺 `max_in_top_k`（runner `:303` 默认 0）——r13 一律拒（fail-closed 方向，非 fail-open）。

## ③ 新路径扫描（守卫 T 但 runner rc=1 / fail-open / 恒真）

- **Unicode 空白**：对全部 1 114 112 个码点暴力验证——**不存在**「非空白但 norm_text 归一后为空」的字符；`_nonempty_str`（strip）与 runner `norm_text`（NFKC+casefold+split）在空白面完全对齐。`U+200B/U+FEFF/U+180E` 仍被守卫收，但实测 `norm_text` 保留非空（marker 只按字面命中，非恒真），不构成 fail-open。
- **全角数字**：`grade:"２"` 现 F（守卫比 runner 严，方向 fail-closed）；`max_in_top_k` 非 int 直接 F。
- **`expect_not_hit` 多条目**：逐元素校验；两条均合法 T、第二条含空白 glob → F；runner 逐条循环无误。
- **`max_in_top_k=0` 语义**：守卫 T；runner `over=max(0,n_hit-0)=n_hit` = 零容忍，与金集注释一致（正确）。
- **`doc_types` 含空白**：contamination/forbidden 两处→F（实测）。
- **`contains`+`grade` 组合**：合法组合 T；r12 侧假值 contains 会静默按满 grade 计（`grade_of` 实测返回 3），该路径现被前置拦截。
- **残余未拦**：`config.group_id:" "`/`vault_id:""`（守卫 T，见 LOW-3）；合法 `max_in_top_k ∈ [10,10⁶]` 与 `10**400` 在 runner 里逐字等价（`over≡0`，`vault runner:303-315`，top10 内 n_hit≤10）——r12 已明示「≥10 均等价」，属注解语义自由度，非本轮新增门。

## ④ 5 个新 case 判别力 + 数字自洽

- 用 test 文件**原字面量**（AST 提取，含 `"9"*400`）复算：5 case 在 r12 源码 **ok=True**（断言 `ok is False` 必红）→ r13 **False 且 fragment 命中**（`whitespace-forbidden-marker`/`whitespace-expect-any`/`huge-max-in-top-k`/`grade-over-ten`/`contains-empty`，`test:1252-1284`）→ **真判别、无空转**；parametrize 30 case 无重名。
- AST 独立计数：测试文件 **75 → 80**（+5）；沙箱外实跑 HEAD 得 **80 passed**（复现 artifact）。
- 目录级：artifact `2000 collected = 1993 passed + 6 skipped + 1 xfailed` 自洽；r12→r13 我实核 **runner 两文件与四金集逐字节未动**，故 +5 只能来自新 case。链：gate 56→62→70→75→80、目录 1969→1975→1983→1988→1993，逐环 delta 与 UAT §17–§20 行一致（r9–r13 我抽验 artifact 尾行，逐字同）。

## ⑤ UAT §二十 / §19.3 登记

- **LOW-4（verdict_at）claim 真**：未引号 ISO 时间戳→`datetime`→`json.dumps` TypeError→守卫 F（实测）；`_yaml_scalar("2026-09-20T12:00:00Z")` 实测输出带引号、读回仍是 str ⇒「真实写回路径不受影响」成立。
- **LOW-5 / L-5 维持登记**：§20.1「仍未关」三句与 r12 原文一一对应，无 overclaim；§20.3 三项未证明如实。
- **LOW-6 仅部分关闭**（见 LOW-4 判定）：内部键消息无「空表为何拒」的理由（只在注释 `tool:595-596`）；`r13-immutability` 仍 3 行，§20.2 的「12 判分函数 AST same=True」在 artifact 里不可见（claim 真，我以两 runner 逐字节未动做了更强验证）。

---

## 逐条判定

- **BLOCKER**：未发现。
- **HIGH**：未发现。
- **MEDIUM**：未发现。
- **LOW-1 — `_grade_ok` 名实残留**：`tool:404` 与 `test:1475-1476` 的 docstring 仍写「非负 int / 整值 float / 数字串 接受」，与 r13 的 0..10+ASCII 实际面前不符（复现：`_grade_ok(2000)` → False 而文档说非负 int 收）。r13 只同步了错误文案，没同步函数/测试文档串。
- **LOW-2 — 相对 runner 契约过严（未来扩展误拒）**：`contains` 真值非 str（如 `5`，runner `:132/:280` 会 `str()` 强转）与缺 `max_in_top_k`（runner `:303` 默认 0）被 `tool:534/548-550` 拒；`grade` 数字串限 ASCII 拒掉 runner `int()` 可收的 `"２"/" 5"/"+5"`（`tool:412`）。复现见②表。方向 fail-closed，非缺陷放大，但会把「runner 本可跑」的形状挡在门外（缺 key 一条承袭 r12，非本轮新增）。
- **LOW-3 — `group_id`/`vault_id` 空白面未收口**：`tool:586-588` 只查「str 或 null」；实测 `group_id:" "`、`group_id:""`、`vault_id:""` 守卫 T。memory runner `:135,150-151` 会把 `" "` 当真值转发成真实 group 过滤；vault runner `:197` 把 `""` 经 `config.py:1015-1036` 映射到字面量 `default`（**不是** declared `canvas_vault`）。同 M1 家族；因禁连 8011、未离线证明落 rc=1 还是 rc=2（有「全零返回=rc2」哨兵 `:510` 兜底），只按 LOW 登记。
- **LOW-4 — §20.1 LOW-6 行部分 overclaim**：`tool:608` 的内部键消息没有「空表会让门恒空」理由（该理由只在 `tool:595-596` 注释；只有 `leak_markers` 消息 `:623` 写明了）；`r13-immutability-*.txt` 仍 3 行，§20.2 的「12 判分函数」明细不可见（r12 LOW-6① 未改善）。
- **LOW-5 — 证据卫生**：`r13-gate-green-20260920T161522.txt:63-64` 是**红运行**（1 failed / 79 passed，失败于 `empty-query-string` 的「空串→空白串」fixture 改名中间态，HEAD 测试文件已无「空串」字面量），与绿运行同名 glob；UAT `:683` 引用 `r13-gate-green-*.txt` 未区分/未注记，读者可能误读为 HEAD 门红。

**未被拦下的输入**：`group_id:" "`/`vault_id:""`（LOW-3）；合法 `max_in_top_k ∈ [10,10⁶]`（与 10**400 在 runner 内逐字等价，配额门对该 query 恒空——r12 已明示的注解语义自由度）；`U+200B/U+FEFF/U+180E` 作为 marker/file（收下但 norm_text 非空，非恒真，属正常字面量）。
**对照输入**：合法 `contains:"0"`/`"x"+grade`、`grade:"2"/2.0/0/10`、`delivery{0.5,10}`、`max_in_top_k 0/4`、`expect_not_hit` 多条目、四真金集（verify rc=0、sha 逐字）→ 两版全 T，无误拒。
**负控输入**：5 个新 case 原字面量在 r12 源码全 True（无判别则 r13 测试无从变红）→ r13 False+fragment；`\u3000/\u00a0/\u2028` 空白变体 r12 T→r13 F（超出提交 case 的判别）；`U+200B/U+FEFF` 两版同 T（无判别且无需判别）。提交物内**无** r13 自带的候选父版红灯快照——本轮判别力由本复核同 fixture 复算提供。
**门未覆盖的路径**：`hard_cap` 上界（UAT 已如实标注「代码」无 case，`tool:611-614`）、`grade` ASCII 分支（只有 `grade:2000` case，无 `"²"/"２"` case）、`contains` 非 str/null（只有 `contains:""` case）、ASCII 空格以外的 Unicode 空白、`group_id`/`vault_id` 空白、`max_in_top_k ∈[10,10⁶]` 的语义效应——均无专属门；目录级 1993 未重跑（artifact+算术核对，未跑 5.5 分钟套件）。

**本轮总评：B=0 / H=0 / M=0 / L=5**

r13 如实完成自述：M1 空白面 12+ 站点全量收口（含 Unicode 全码点证明与 runner `norm_text` 对偶）、M2/LOW-1/2/3 逐条真关闭、5 门真判别、80/1993 数字链自洽、四真金集零误拒；残余集中在与 runner 契约相比的过严面、`group_id`/`vault_id` 空白未收口、`_grade_ok` 文档串残留、以及 §20.1/§20.2 的登记可见性与红日志卫生。
