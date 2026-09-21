# CARD-G4-13 r12 独立复核（只读 · 绑 `07d5c34b`，父 `191de457`）

**绑定/方法**：`HEAD=07d5c34b`，diff 与源码取自该 commit；r11/r12 两版 `gold_set_manifest_tool.py` 由 `git show 191de457:` 载入同进程、同一批 fixture 直调 `verify_gold_set_file()`（真路径在位，仅内存替换 load_yaml/sha 输入）；runner 侧用**真函数**微复算（无 HTTP、无库、无落盘）；四真金集走**未打补丁**的真 verify（sha 独立重算）；5 个新门在沙箱外实跑一次 pytest（5 passed/70 deselected；已禁 bytecode 与 cache，仓库零写入）。未连 7691/7687/8011，未跑非 shadow runner，未评 G4-14/R-SLO/L-5/103 条语义。工作树唯一未跟踪 = 任务前已存在的 r12 review/prompt 两文件——**我未改任何文件**。

---

## ① M1 与 LOW-1/2/3/7 逐条复算（r11 源码 → r12 源码，同 fixture）

| 族 | fixture（节选） | r11 | r12 | 判定 |
|---|---|---|---|---|
| **M1** | `forbidden.path_globs:"secret/**"` / `"qqq"`（str） | T | **F**（`不是非空字符串列表`） | 真关闭 |
| M1 | `contamination.path_globs:"raw/*"`；`forbidden.doc_types:5`；`markers:5`；`path_globs:[5]` | T | **F** | 真关闭 |
| M1 | `contamination.doc_types:[]`；`forbidden.markers:[""]`；`path_globs:["","*"]` | T | **F** | 真关闭 |
| **LOW-1** | `top_k/max_results/version = 10**400` | T | **F** | 真关闭 |
| LOW-1 边界 | `top_k:10**6 / 10**6+1`；`version:0 / -1` | T / T | **T / F；T / F** | 边界正确 |
| **LOW-2** | `grade:2.0 / "2"` | F | **T** | 真放宽（方向对） |
| LOW-2 对照 | `True / -1 / 2.5 / null / "x"` | F | F | 无误收 |
| **LOW-7** | vault `:36` / memory `:28` docstring | 旧文案 | `2 = 环境或输入错（…最外层兜底…）` | 名实一致 |
| 对照 | 合法五键列表、`forbidden:{}`、`grade:3/0`、四真金集 | T | **T** | 无误拒 |

M1 的 runner 侧危机实测可复现（真函数）：`forbidden_violations({"source_path":"notes/x.md"}, {"path_globs":"secret/**"})` → **2 条硬禁**（rc=1 假硬禁）；`"qqq"` → `[]`（恒空 fail-open）——r12 后用守卫在 rc=2 前拦截。四真金集独立复算：`verify rc=0`、四 sha 与 manifest **逐字同**、`class_key` 一致（query_type/category）⇒ **无误拒**。
M1/LOW-1/LOW-2 的直收口为真；但 LOW-1 的"上界"只覆盖 3 键、LOW-2 的 `_grade_ok` 引入新边角（见 M/L 清单）。

## ② 内部键守卫 vs 四真金集 / 空表语义

- 四真金集的 `contamination/forbidden` 全表均为**非空 str 列表**（`raw/*`、`video_transcript`、`TestConcept/UAT-/m3-e2e`…），新增守卫**零误拒**；`contamination.markers` 非 runner 消费键（两 runner 均不读），无需守卫；`forbidden` 三键与 vault runner 消费面一一对应。
- 未来合法扩展：想"不设禁"须**删键**而不是 `[]`——规则已写进 §19.1（"非空 str 列表"）；但"空表为何拒"（空表=硬禁/配额门恒空）只在代码注释里部分出现（注释只讲 str 逐字符迭代），**理由未登记**。
- ⚠️ 口径漏洞：守卫判"非空"用的是真值 `not x`，而两个 runner 的匹配前先 `norm_text`（NFKC+casefold+**去空白**）——`" "` 是真值但归一后为空（见 M-1）。

## ③ 新路径扫描：守卫 T 但 runner rc=1 / fail-open

- **空白串顶穿（M-1）**：`forbidden.markers:[" "]` 守卫 **T** → 真函数返回「命中硬禁标记 ' '」对每个材料 ⇒ **rc=1 假硬禁**；同根 `expect_hit:[{file:" "}]` ⇒ `"" in path_n` 恒真、任意材料按声明 grade 计（实测 `grade_of` 返回 3）；`leak_markers:[" "]` ⇒ 每条算泄漏；`expect_any:[" "]` ⇒ 恒 relevant（实测 True）；`path_glob:" "` ⇒ 配额恒空。
- **`max_in_top_k` 无上界（M-2）**：`10**400` 守卫 **T**；runner `over=max(0,n_hit-allowed)`，n_hit≤10 ⇒ 恒 0 ⇒ 该 query 污染永不计数（fail-open 掩蔽回退；任何 ≥10 等价）。
- `contains`（L-2）：`""/[]/{}` 短路内容校验；非 str 被 `str()` 强转。**markers 空串/`doc_types` 含空串已关**；`verdict_at`（L-4）过度拒绝仍在；`_grade_ok`（L-1）与 `hard_cap`（L-3）见下。
- 非 glob 语义形态（`"["`、`"a{b"`、`"**"`）：fnmatch 实测不抛异常；`path.startswith(g.rstrip("*"))` 属既有匹配语义，无新 crash 路径。

## ④ 5 个新门判别力 + 数字自洽

- 3 个 parametrize（用提交里**原 YAML 字面量**复算）：r11 `ok=True`（测试红）→ r12 `False` 且 fragment 命中（绿）⇒ **真判别**；`test_grade_ok…`：r11 无该名（AttributeError 红）⇒ 真判别。
- `test_runner_wrapper_does_not_swallow_keyboard_interrupt`：r10/r11/r12 **三版真源码**同探针下 KI 均透传 ⇒ 对父提交**零判别**，是防未来 `except BaseException` 的回归锁（断言非空转，但非本轮回退判别）。
- AST 独立计数：`70 → 75`（parametrize 46→49，+2 独立）= `r12-gate-green`"collected 75 / **75 passed**"✓；目录级 `1990→1995 collected / 1983→1988 passed`（+5）✓ 自洽；我另实跑 5 门 = `5 passed, 70 deselected`。

## ⑤ UAT §十九 / §19.3

- §19.1 六行整改、§19.4 未证明三项、LOW-4/LOW-5/L-5 登记**逐条为真、无 overclaim**：LOW-4 仍成立（`print_report` `:521` 在硬禁判定 `:523` 前；baseline 非原子）；LOW-5 忠实（`r12-verify/shas/immutability/dryrun` 与 r11 **逐字节相同**＝确定性重放，§19.3 已明示零判别力）。
- 小缺口：`r12-immutability` 仅 3 行（`AST diffs = 0`），§19.2"12 判分函数 AST same=True"的明细不可见（claim 真：r11→r12 两 runner 仅 docstring 变更，已逐 hunk 核对）；§16.2 未编辑、靠 §19.1 指针覆盖（可接受，单读仍误导）。

---

## 逐条判定

- **BLOCKER**：未发现。
- **HIGH**：未发现。
- **MEDIUM-1** — 空白串顶穿「非空 str」口径：`gold_set_manifest_tool.py:529,552-563,591-606,617-621`（真值判空）＋ `run_vault_retrieval_regression.py:154-155,130`、`run_memory_retrieval_regression.py:110-115`。一句话复现：`forbidden.markers:[" "]` ⇒ 守卫 T、每个材料命中硬禁 ⇒ rc=1 假硬禁；`file/expect_any/leak_markers: " "` 同根变恒真 fail-open。修法：判 `x.strip()`/norm_text 后非空。
- **MEDIUM-2** — `max_in_top_k` 无上界 ⇒ 配额污染门恒空：`gold_set_manifest_tool.py:543-546`＋`run_vault_retrieval_regression.py:303,311,364`。复现：`max_in_top_k:10**400` ⇒ 守卫 T、`over` 恒 0 ⇒ `contamination_at_10/polluted_query_rate` 被稀释（≥10 均等价）。
- **LOW-1** — `_grade_ok` 放宽副作用：`tool:398-411`＋`runner:131,163,279`。复现 a：`grade:"²"(U+00B2)` → isdigit True 守卫 T、`int()` ValueError ⇒ rc=2；复现 b：grade 无上界，`grade:2000` ⇒ ndcg `2**g` OverflowError ⇒ rc=2；`:536` 文案"≥0 int"与新接受面（2.0/"2"）不符。
- **LOW-2** — `expect_hit[i].contains` 形态未守：`tool:524-537`＋`runner:132,280,349`。复现：`contains:""`/`[]`/`{}` ⇒ 守卫 T、内容校验静默跳过、按声明 grade 计（r11 已列未拦下，r12 未处理/未登记）。
- **LOW-3** — `delivery.hard_cap` 无上界：`tool:609-612`＋`runner:331-334`。复现：`hard_cap:10**400` ⇒ 守卫 T、直传检索参数（fail-loud/性能面，非 fail-open）。
- **LOW-4** — `verdict_at` 过度拒绝未登记：`tool:494-496`。复现：`verdict_at: 2026-09-20T12:00:00Z`（未引号⇒datetime，双 runner 不消费该键）⇒ 全文档 json 检查拒 ⇒ rc=2。
- **LOW-5** — LOW-3 只部分关闭：`tests:1450-1466`。复现：同探针在 r10/r11/r12 均 KI 透传 ⇒ 新钉零判别力；SystemExit 与"rc=1 保留"仍无门（§19.1 已如实注记）。
- **LOW-6** — 登记/证据可见性：§19.2 引 3 行 artifact 支撑"12 判分函数"明细不可见（claim 真）；空表被拒理由未登记；§16.2 旧文未编辑（指针覆盖）。

**未被拦下的输入**：上表 M-1/M-2/L-1/L-2/L-3/L-4 全部输入（守卫 T 放行）；`forbidden:{}`/缺键（有意关闸，属设计）；拼写错键（如 `pathglob:`）静默走 `.get` 默认（schema 完整性面，历代不拒）。
**对照输入**：合法五键列表/空 dict/`grade:3,0`/`top_k:10⁶`/`version:0,10⁶`/四真金集（verify rc=0、sha 逐字）→ r12 全 T，无误拒。
**负控输入**：3 个新 parametrize case 在 r11 上 `ok=True`（红）→r12 绿+fragment；`_grade_ok` 在 r11 上不存在（红）→r12 绿；KI 钉三版同绿（无判别）。
**门未覆盖的路径**：空白族、`contains` 形态、`verdict_at`、`max_in_top_k`/`hard_cap`/grade 越界均无 case；目录级 1988/1995 为 artifact+算术核对（未重跑 6 分钟套件）；两 runner 真全流程未跑（边界）。

**本轮总评：B=0 / H=0 / M=2 / L=6**

r12 如实完成自述：M1 九态收口、LOW-1 三键边界、LOW-2 方向性放宽、LOW-7 名实修正、3 门真判别、75/1988 自洽、四真金集零误拒。残余集中在"非空"口径被空白串顶穿（rc=1 假硬禁 + 恒真 fail-open）、`max_in_top_k` 无上界致配额门恒空，以及 6 条 LOW（`_grade_ok` 边角、`contains` 形态、`hard_cap` 上界、`verdict_at` 过度拒绝、KI 钉零判别、登记可见性）。


