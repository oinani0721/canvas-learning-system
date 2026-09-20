# UAT — CARD-REVIEW-CHAIN-PUSH-STATE（每日复习推送链「三态谎报」修复）

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-REVIEW-CHAIN-PUSH-STATE]` · 车道 `card-p5-review`（分支 `card/p5-review`），本车道第 **2/3** 张（P5-A → **本卡** → P5-C）
> **基线**：`PREV = 6d8ca202`（= P5-A 末 commit / 本卡起点）· 更早基线 `9c4e7e82`（B15_BASE）
> **代码定稿 SHA**：`626d5416`（`git diff --stat 626d5416 HEAD -- . ':(exclude)_bmad-output'` 恒空）
> **commit 数**：**4**（PREV 之后：2 代码 = `9922d0bf` 主改动 9 文件 +266/−23、`626d5416` 注释行号更正 3 文件；2 存档 = `94f9f52a` 证据/验收单、本补注）
> **Codex 轮次**：**r1 达成 D-15** —— 绑 `626d5416`（= 最终 HEAD）判 **BLOCKER 0 / HIGH 0** / MEDIUM 2 / LOW 4（登记不阻断，§七）· 轮次 1/5
> **证据目录**：`_bmad-output/审查/evidence-review-chain-push-state/`

---

## 一 这张卡到底做了什么

1. **推送链「三态谎报」修复（缺陷①）**：`daily_review_run.py` 在 Bark key 未配置（rc==2）时
   只写日志 `push:skip-nokey`、**state 零落账** ⇒ 昨日 `last_result: "pushed"` 原样留存 ⇒
   `/overview` 与交互页照显示「一切正常」，而用户手机什么都没收到。修法三处**同一 commit**
   （`9922d0bf`）：runner 新增 `generated_push_skipped_nokey` + `bark-nokey`（:754/:755，
   +2 行）；`_read_push_status` 新增**精确** `elif`；登记门 `RUNNER_ONLY_KEYS`/`EXPECTED_HITS`
   （1 行 → 2 行）同 commit 扩面。
2. **`last_error` 截断（缺陷②）**：`_LAST_ERROR_MAX_LEN = 200`（:807）；切点在
   `err.encode("utf-8")` 门**之后**（:2638 `return (degraded, err[:_LAST_ERROR_MAX_LEN])`）。
3. **G6-8 模板冻结绑最终模板（关闭 Codex r5 HIGH-1）**：判据① 单一绑定（Name-Store 恰 1 +
   alias/global 遮蔽面 + 顶层字符串常量，:488/:515）+ 判据② 运行期锚（importlib 对拍，
   fail-closed，:645/:655）；冻结集 2 条不变。
4. **交互壳同款降级徽标（默认实施，可退）**：`review_app.py` import 共享文案 + 占位符注入 +
   卡头第二枚徽标（严格 `=== true`，:541-551）；白名单两处（`test_review_app._ALLOWED_IMPORTS`
   / `g68._APP_SHARED_IMPORTS`）同 commit 登记。
5. **`inbox_preview.py:430` 零改动**（按默认；用户当次裁 D-18 才改）；只核 G6-8 契约声明与源码一致
   （:430 `_TZ_SHANGHAI` 实测一致；`canvas-vault/` 零 diff）。

---

## 二 §〇 事实核对（开工逐条实测；卡文撰写于 9c4e7e82，P5-A 已使 review_overview +20 行）

| 卡文 §〇 说 | 实测 | 判定 |
|---|---|---|
| 起点 HEAD = `67d66672`/卡文写 57d29464 | 本树开工 HEAD = **`6d8ca202`**（P5-A 末 commit，subject 含 `CARD-G6-9c-R3`；= 57d29464 + P5-A 补审 commit，仅 `_bmad-output`） | ✓ 容忍（卡文 (a) 判据成立） |
| runner `:739/:746/:749-753/:768` | **逐行全同**（本卡唯一零漂移文件）；改后新增 `:754/:755` | ✓ |
| review_overview `def _read_push_status` `:2528` | **:2553**（P5-A +20 后本卡再 +5；def→末尾 = :2553-2628） | ⚠️ 漂移 +25 |
| 其内 `last_result = st.get(...)` `:2572` | **:2601**（+29） | ⚠️ |
| `:2596 def _push_status` | **:2630** | ⚠️ |
| docstring runner 行号 `:745/:746`（⚠️ 卡文自标已漂） | 本卡已更正为 `:752/:753`（失败）×`:755`（新）×`:746`（成功）—— 终态自洽 | ✓ 已修 |
| 兜底条目 `[:200]` `:1156` | **:1181**（本卡常量插入 +5；本卡自引已更正，见 `626d5416`） | ⚠️ 已修 |
| review_app `:60-66` import / `:84 _PAGE_TEMPLATE` / `:183-191` 占位符 / `:541` badge / `:1025-1032` 替换链 | `:60-67`（+1）/ **:85** / `:191-194` / `:541-551`（新 JS 插入）/ `:1031-1042` | ⚠️ 漂移 |
| g68 `:445-450` 冻结集 / `:591-600` 提取 / `:602-611` sites / `:421` 白名单 | `:446-451` / **已重构**（判据① `:488`、判据② `:645`）/ `:653-661` / `:422-429`；调用点 `:1058-1061 → :1107` | ⚠️ 漂移+重构 |
| boundary `:632-637` / `:651-653` / `:661-663`；`def test_`=8 | `:634-641` / `:654-658`（2 行）/ `:664-668`；**收集数 24**（参数化展开，非 8） | ⚠️ 漂移+口径 |
| 「既有红 `test_push_failure_is_invisible_to_backend_app`」 | 实测 `9c4e7e82` 已转正改名（T3-C），本卡开工全绿 | ✓ 卡文已知 |
| T3-C UAT 引 runner `:743-746` | 实测 `:749-753`（T3-D 改后漂移） | ⚠️ 已登记 |
| `inbox_preview.py:430 _TZ_SHANGHAI` | 仍在 `:430`，本卡零 diff（Codex r1 独立复核一致） | ✓ |

---

## 三 (b) 先红（改代码前落档，全部红在指定断言）

| 项 | 存档 | 结果 |
|---|---|---|
| ① 结构改前 | `struct-before-20260919T234130.txt` | `generated_push_skipped_nokey` **0/0/0**；验伪锚 `generated_push_failed` 命中 1/2/5；`push_degraded`=0；`_LAST_ERROR_MAX_LEN`=0；EXPECTED_HITS **1 行** |
| ② runner 门先红 | `red-runner-20260919T234015.txt` | **1 failed**（`assert st2["last_result"]` 实得 `"pushed"`，+74 deselected）rc=1 |
| ③ overview 门先红 | `red-overview-20260919T234015.txt` | **2 failed**（`push_degraded` 实得 None；1000 ≠ 200），rc=1 |
| ④ g68 门先红 | `red-g68-20260919T234051.txt` | **1 failed**（`result.get("template_binding")` 实得 None —— 改前门未覆盖「再绑定」的**先红点**）rc=1 |
| ⑤ review_app 门先红 | `red-review-app-20260919T234051.txt` | **1 failed**（占位符不在模板）rc=1 |
| ⑥ pyright 改前 | `pyright-before-20260919T234130.txt` | **`0 errors, 81 warnings`** |

---

## 三附 完成条件 (a)-(p) 逐条

| 条 | 要求 | 结论 | 依据 |
|---|---|---|---|
| (a) | 第 0 分钟 + 核 §〇 | ✅ | pwd/branch/HEAD `6d8ca202`（含 CARD-G6-9c-R3）/status 0 行/merge-base 祖先；pytest+env+pyright `test -x`；BASE=**33**；开工基线：`unit-open`（35 failed / 5731 passed —— = BASE 33 + 本卡 3 新红 − 1 已知 flaky）、`regression-open`（**2167 passed / 0 failed**）；§〇 逐条核（漂移见 §二） |
| (b) | 先红六项 | ✅ | 结构 0/0/0 + 四门红在指定断言 + g68 再绑定负控**改前不抛**（先红点）+ pyright 改前 0 errors（§三） |
| (c) | 缺陷① 三处同 commit（不可退） | ✅ | `9922d0bf`：runner `:754/:755`（+2 行，精确匹配卡文“新写入两行”）；读侧精确 `elif`（默认口径：未配 key = 降级 True + `bark-nokey`）；登记门 `RUNNER_ONLY_KEYS`+`EXPECTED_HITS` 1→2。向后兼容：旧 state 无新值 → 读侧不变；旧读侧遇新值 → (None, None) 不谎报；合入=上线 ⇒ 同 commit |
| (d) | last_error 截 200（utf-8 门之后） | ✅ | `_LAST_ERROR_MAX_LEN=200` :807；:`2638` 在 `encode` 门之后切片；坏串（surrogate）仍 → None；Codex r1 独立复核「str 按码点切片、不会二次编码」 |
| (e) | g68 单一绑定门 + 运行期锚 fail-closed | ✅ | 判据① `:488`（Store/alias/global/顶层常量四查；r5 再绑定与 `"".join([...])` 双负控）；判据② `:645`（importlib 对拍，异常/不等都 ContractError）；冻结集 **2==2**（AST）；返回 dict 增 `template_binding` |
| (e′) | review_app 徽标三处同进同退 | ✅ | import（:64）/占位符（:194）/模板+替换链（:541-551/:1042）+ 白名单两处；默认实施未触发退出条件；新增行无 due 字段名、`_PAGE_TEMPLATE` 仍单一绑定 |
| (f′) | inbox_preview 零改动 | ✅ | `canvas-vault/` diff 空；G6-8 契约 `:107-116` 声明与源码 `:430` 一致（Codex r1 实测复核） |
| (f) | 结构对 + AST 冻结面 2==2 | ✅ | 改后 `generated_push_skipped_nokey` **1/3/4**（≥1/≥1/≥2）；EXPECTED_HITS 2 行；AST `stores=[85]`、`sites==frozen: True n=2`（改前改后同）；验伪锚（r5 副本）`stores=2`；`push_degraded`=1；`_LAST_ERROR_MAX_LEN`=2（struct-after / ast-freeze-after） |
| (g) | 六道承重门（不连库） | ✅ | ①runner `-k skip_nokey` **1 passed**（selected=1）；②overview **2 passed**（selected=2）；④g68 `-k binds_final_template` **1 passed**；⑤review_app `-k push_degraded_badge` **1 passed**；⑥登记门整文件 **24 passed**；g68 整文件 **34 passed**；boundary 整文件 24 passed（1:35）；全部 `-rfE` 无 FAILED/ERROR，`selected` 非 0、rc≠5 |
| (h) | pyright 保持 0 | ✅ | 改前/改后 **`0 errors, 81 warnings`**（绝对路径 + 结构锚取汇总，禁 tail）；本卡新增 ignore=**0**；零 `LEFTHOOK_EXCLUDE=python-typecheck` |
| (i) | 六套件 + 目录级只减 | ✅ | 六套件收工 **440 passed / 0 failed rc=0**（= 开工 435 + 本卡新增 5：75−1+74−1… 逐文件 74/117/99/33/24/88 → 75/119/100/34/24/88）；`regression` open↔close nodeid **完全相同（零红）**；`unit` close vs BASE **仅 1 条 `<`**（已知 flaky）、open→close **仅 3 条 `<`**（本卡新门转绿）；每份存档贴 W4 `blocked=0`。⚠️ 六套件「开工 bundle」缺席的处置见 §六.8 |
| (j) | openapi 不入 commit | ✅ | `git show --stat HEAD | grep -c backend/openapi.json` = **0**；`diff PREV..HEAD -- backend/openapi.json` 空；两 commit 均 `LEFTHOOK_EXCLUDE=spec-sync-flat,spec-sync-root`（hook 输出贴 `commit-code-*.txt` / `commit-citefix-*.txt`）；待主 session 集成期再生 |
| (k) | 负控 ≥2 段 | ✅ | **三段**：①删 runner 新写入两行 → `assert 'pushed' == 'generated_push_skipped_nokey'` 红；②拆 g68 判据①（条件 `if False`）→ `DID NOT RAISE` 红；③删读侧新 elif → `assert None is True` 红。三段各：`git show HEAD:` 还原 + 跑前/跑后 sha256 **逐字同** + `git status` 空（除未跟踪 evidence 目录）。⚠️ 首跑段 ①-③ 输出被 `tail` 截掉缺正文 → 全量重跑（`…001108` 为正式存档，`…000909` 留痕） |
| (l) | 地盘九文件 | ✅ | `diff --stat 6d8ca202..626d5416 -- . ':(exclude)_bmad-output'` **恰九文件**；runner hunk 恰落 `:751-755`（+2 行）；`canvas-vault/` 零 diff；无 inbox_preview/local_tz/display_tz/pick/conftest/openapi/lefthook。⚠️ 验伪锚（去 exclude 多出 `_bmad-output/`）在 evidence 入库前为 **0 = 空洞**（P5-A §五.9-bis 同款）→ 存档 commit 后复跑登记 |
| (m) | 现网只读 | ✅ | 零连库；env 无 7691/7687；**新增行** fsrs_bridge/decay_beta = 0、7691/7687 = 0；九文件 base=head 命中数**逐行相同**（8/1/2/1/14 等为既有）。合入=上线：主 session 合入后核一档 launchd `push:` 与 state 新枚举（§七.8） |
| (n) | Codex | ✅ | **r1 = BLOCKER 0 / HIGH 0** / M2 / L4，绑 `626d5416`（= 最终 HEAD）⇒ **D-15 达成（1/5 轮）**。首部按 §2.4 六行（模型 `glm-5.3` / `reasoning_effort: max` / `codex-cli 0.153.3` + 会话头自证 `L2/L5/L9`）；M/L 按 §1 登记不修（逐条 §七） |
| (o) | 独立 commit | ✅ | 2 个代码 commit（header 95 / 99 字符 ≤100，均含批次标记与卡号；type=fix/docs）；`*.stderr*` 不入库（`.gitignore:264` 覆盖）；存档逐文件 `git add`；不 push |
| (p) | 未证明 ≥4 / 待登记 ≥4 | ✅ | §六 **8 条** / §七 **13 条** |

---

## 四 DoD-3

### 4-A 技术验收（逐条贴证据）

| # | 判据 | 存档 | 末行 / 结果 |
|---|---|---|---|
| 1 | 第 0 分钟 | `min0-prelim-*` / `facts-*` | pwd/branch/HEAD=`6d8ca202`/status 0；`PREV=6d8ca202…`；BASE=33；pyright `test -x`；§〇 逐条（漂移表 §二） |
| 2 | 先红四门 | `red-runner-* / red-overview-* / red-g68-* / red-review-app-*` | runner 1F（`"pushed"`）· overview 2F（None；1000≠200）· g68 1F（None）· review_app 1F；全 rc=1 |
| 3 | 结构改前→改后 | `struct-before-* / struct-after-*` | 0/0/0 → **1/3/4**；EXPECTED_HITS 1 行 → **2 行**；`push_degraded` 0→1；`_LAST_ERROR_MAX_LEN` 0→2 |
| 4 | AST 冻结面对照 | `ast-freeze-after-*` | `stores=[85]`（1 处）；`sites==frozen: True n=2`；验伪锚 r5 副本 `stores=2` |
| 5 | 六门后绿 + 全文件 | `green-runner-* / green-overview-* / green-g68-retry-* / green-review-app-* / green-boundary-* / green-g68full-*` | 1 passed · 2 passed · 1 passed · 1 passed · 24 passed · 34 passed（1:21）；⚠️ 中途 `green-g68-*000057` 1F 为**误导性红**事件（§五.2），留痕 |
| 6 | pyright 改前/改后 | `pyright-before-* / pyright-after-*` | **`0 errors, 81 warnings`** ×2（同数） |
| 7 | ruff（zsh 数组 + F821 锚） | `ruff-* / ruff-afterfmt-*` | check **rc=0**（9 文件）；format 首检 2 文件漂移 → 修复后 **9/9 already formatted**；F821 验伪锚 rc=1（探针跑后即删、status 无残留） |
| 8 | 负控三段 | `negctl-{1,2,3}-*001108.txt`（正式） | 红在指定断言（见 §三附 (k)）；跑前/跑后 sha256 四行逐字同 |
| 9 | 六套件收工 | `suites-close-*` | **440 passed / 0 failed rc=0**（95.97s）＝开工 435 + 新增 5 |
| 10 | regression 目录级 | `regression-open-* / regression-close-* / *.nodeids` | open **2167/0F** → close **2169/0F**（+2 新门）；nodeid diff **全同**；W4 `blocked=0` |
| 11 | unit 目录级 | `unit-open-* / unit-close-* / *.nodeids / base.nodeids` | open 35F/5731P（含 3 新红）→ close **32F/5734P**；close vs BASE 仅 1 `<`；open→close 仅 3 `<`；W4 `blocked=0` |
| 12 | 地盘门 | `static-judges-* / m-fixed-*` | 九文件 ⊆；runner hunk `:751-755`；`canvas-vault/` 空；⚠️ 验伪锚入库前空洞（收工后复跑见 §八索引）；(m) 全过 |
| 13 | openapi / 提交 | `commit-code-* / commit-citefix-*` | commit `9922d0bf`（9 文件 +266/−23）+ `626d5416`（3 文件 +3/−3）；两 commit 均不含 openapi.json；spec-sync 双钩排除输出落档 |
| 14 | Codex | `codex-review-CARD-REVIEW-CHAIN-PUSH-STATE-r1.md`（首部 §2.4 六行） | **BLOCKER=0 HIGH=0** MEDIUM=2 LOW=4；绑 `626d5416`（送审时 HEAD 同）；prompt `def04890…`；存档 pre-header `5ec8da73…` / 全文 `45d620b8…` / 首部 `91086928…` |

### 4-B 用户验收（零技术词）

哪天推送通知的钥匙没配好，复习总览页不再拿昨天的「已推送」糊弄我，会亮一枚红色小标提醒「没推出去」并写明原因；我感觉这页终于说实话了。

**felt-sense**：以前看到页面上「一切正常」，我会不放心地再瞄一眼手机——确认真的收到提醒了没有。现在不用了：该推没推出去的时候，那枚红色小标会替我把话说清楚，原因也写在上面。我可以直接信这一页。

---

## 五 本卡的实质发现

### 5.1 五门先红后绿的算术闭环（三个目录级口径互相咬合）

- 六套件 440 passed = 开工 435 + 新增 5（逐文件 74/117/99/33/24/88 → 75/119/100/34/24/88）；
- regression 2167 → 2169 = +2（本卡 2 个 regression 新门）；
- unit 5731 → 5734 = +3（本卡 3 个 unit 新门），且 open 的 3 条新红在 close 全部转绿（open→close diff 恰 3 条 `<`）。
三组数字同时成立，是「先红后绿 + 无回退」的交叉证据。

### 5.2 g68 判据① 的**排序**是承重的：join 形态会先炸在误导性的门上

先红阶段实测：`_PAGE_TEMPLATE = "".join([...])` 形态下，模板不再是 `ast.Constant`
⇒ 既有的**按身份豁免**（`exempt_nodes`）失效 ⇒ 模板正文里的 `humanizeDue(n.fsrs_due…)`
先触发「独立 due 算法」门 —— 负控② 的红**不是**判据① 的红。这不是测试瑕疵，是门序问题：
**结构门（单一绑定）必须先于内容门（豁免/冻结）**，否则模板一旦不是「单一最终常量」，
其后所有按身份判据都失去前提。处置：判据① 上移至 import 检查之后（`g68 :488`），
负控② 从此精确红在「不再是模块级字符串常量赋值」。`green-g68-*000057`（修前的 1F）
与 `green-g68-faildetail-*`（红点正文）均留痕。

### 5.3 三态语义的三条边界（Codex r1 与我们独立一致）

- **`skip-done` 不是谎报**：「今日已 accepted」时留存 `"pushed"` 是真话，不应降级；
- **`skip-empty` / `skip-window` 不落账**是「最近一次结果**没有观察时间戳**」的口径边界
  （state 记的是「最近一次到点尝试的结果」，不是「今天肯定推过」）—— 登记，不默认改降级；
- 本卡修住的正是中间那一档：**到窗口、有内容、真尝试、rc==2**（key 未配置）。

### 5.4 卡文事实的漂移全貌（撰写于 9c4e7e82，P5-A 使 review_overview +20）

本卡全部行号按**符号名**重锚；`626d5416` 又更正了三处自引行号（`:1176→:1181` ×2、
`:60-66→:60-67`）—— 常量插入自身会推动其下方的行号，**引用与被引在同一次改动里互相移动**，
是这类注释最易漂的形态。另：卡文「boundary `def test_`=8」实为收集 24（参数化展开）。

---

## 六 本卡未证明什么（≥4）

1. 未证明现网 live state 里已存在的陈旧 `"pushed"` 会在合入后第一档被覆盖 —— 修复在 fixture
   上证明（`test_skip_nokey_overwrites_stale_pushed_state`），真实时序（launchd 每小时、当天走哪条
   rc 路径）未在 live 观测。
2. 未证明 review_app 徽标在**真实浏览器**里渲染正确（无 JS 执行环境，只做模板/注入断言）；
   Codex r1 MEDIUM-2 进一步指出：连 `renderVaultCard` 的行为门都没有（删 `pushBadge` 仍绿）。
3. 未证明 `_LAST_ERROR_MAX_LEN = 200` 是产品正确上限（沿用 entry.error 既有口径；200 是码点数不是字节数）。
4. 未证明 `inbox_preview.py:430` 与 display_tz 的日期分叉在真实跨日场景无影响（按默认不改，待用户裁 D-18）。
5. 「完整复习链五面对账」不在本卡（归 P5-C G6-13）。
6. 运行期锚只证 **import 时刻** `_PAGE_TEMPLATE` 等于 AST 常量，不证请求期不被 monkeypatch。
7. `skip-empty`/`skip-window` 三档不落账的语义只评估未修（§5.3 口径边界，登记 §七.11）。
8. 六套件「开工 bundle」缺席（本卡在写新测试后直接进入先红/改造，未单跑开工 bundle）——
   回退面无损的证明由两条目录级开工基线承担（regression-open 0 红 / unit-open 含本卡 3 新红），
   收工对比见 §4-A #9-#11；此为口径选择，如实登记。

---

## 七 台账待登记条目（≥4）

1. 修复 sha（`9922d0bf` + `626d5416`）+ 先红后绿六门 nodeid + 结构对（`0/0/0 → 1/3/4`、EXPECTED_HITS 1→2）。
2. **产品口径默认**「Bark key 未配置 = 降级 True + `bark-nokey`」待用户确认（若裁「不算降级」只改读侧一行归 `(None, None)`）。
3. `inbox_preview.py:430` 零代码登记（manifest `defaults` 与 `user_touchpoints` 方向相反，已按 defaults；用户裁 D-18 即另立小卡，含 lint digest 重算）。
4. Codex G6-8 r5 HIGH-1「模板冻结未绑最终模板」**关闭**（判据①+② 落地）；裁定书 §二 T3-B 行「登记」项可销。
5. T3-C 台账 #9（last_error 截断）、#10/#17（skip-nokey 无能为力）两条**关闭**（本卡正面修）。
6. review_app 徽标**已做**（若后续裁退，须知 import/占位符/白名单三处同撤）。
7. `backend/openapi.json` 待主 session 集成期再生（本卡两 commit 均不含；spec-sync 双钩排除输出落档）。
8. **合入 = 上线**：主 session 合入后核一档 launchd 日志 `push:` 值与 live state 新枚举（wrapper `WT=feature 主干树`）。
9. `review_overview.py` 自引行号漂移已在本卡更正（`:2553` 区 docstring → `:752/:753/:746/:755`；`:1176→:1181`）。
10. Codex 各轮存档路径、绑定 SHA、B/H/M/L 计数（r1：`codex-review-CARD-REVIEW-CHAIN-PUSH-STATE-r1.md`，绑 `626d5416`，B0 H0 M2 L4）。
11. **Codex r1 的 M2 + L4 逐条登记**（登记不修，防「修一条已判通过的 M/L = 打破终审绑定」）：
    - M1 `test_g68_five_view_contract.py` 运行期锚缺失败面负控（删 `:655-656` 比较后仍绿；补法=加「运行期模板被改 → 抛不逐字节相同」的负控）；
    - M2 `test_review_app.py` 徽标缺真实渲染行为门（保留字面、删 `pushBadge` 拼接仍绿；补法=node harness 喂 true/false/None）；
    - L1 `_PUSH_DEGRADED_LABEL` 未入 `_BANNED_REBINDS`（与 `_DONE_NOTE`/`_SNOOZE_NOTE` 纪律不同步）；
    - L2 `review_overview.py:2611`（注释）仍称「两个明确枚举」，终态为三个（注释漂移）；
    - L3 `test_g6_9_boundary_matrix.py:618` docstring 仍写「四个键/零命中」（终态五键/两行登记）；
    - L4 `skip-empty`/`skip-window` 不落账 → 登记为「最近一次结果无观察时间戳」口径边界（不默认改降级）。
12. 六套件开工口径：以两条目录级开工基线承担（§六.8），若复查需要可补跑「逐文件开工 bundle」。
13. 负控段 ①-③ 首跑 tail 截断缺正文 → 全量重跑（`…001108` 正式，`…000909` 留痕）；教训=负控存档必须全量。

---

## 八 命令与存档索引

见 `_bmad-output/审查/evidence-review-chain-push-state/`（66 份，逐文件 `git add` 入库）。要点：

| 组 | 文件（代表） | 说明 |
|---|---|---|
| 第 0 分钟 / 事实实测 | `min0-prelim-*`, `facts-*` (×15) | §〇 逐条 + 漂移全量表 |
| 先红 | `red-runner-*`, `red-overview-*`, `red-g68-*`, `red-review-app-*`, `struct-before-*` | §三 |
| 后绿 | `green-runner-*`, `green-overview-*`, `green-g68-retry-*`, `green-review-app-*`, `green-boundary-*`, `green-g68full-*`, `struct-after-*`, `ast-freeze-after-*` | §4-A #5 |
| 负控 | `negctl-{1,2,3}-*001108.txt`（正式）+ `…000909.txt`（截断留痕） | §三附 (k) |
| 收工长跑 | `suites-close-*` / `regression-{open,close}-*` + `.nodeids` / `unit-{open,close}-*` + `.nodeids` / `base.nodeids` | §4-A #9-11；W4 `blocked=0` 在每份 |
| 静态 | `static-judges-*`, `m-fixed-*`, `pyright-{before,after}-*`, `ruff-*` | §4-A #6-7/#12 |
| 提交 | `commit-code-*`, `commit-citefix-*`（首提被 commitlint 拦 109 字符 header 的留痕 + 复核重提） | §4-A #13 |
| 分诊 / 送审 | `jev-triage-9922d0bf.json`, `codex-prompt-check-*`, `codex-r1-archive-sha-*` | §2.4.3 / §2.4 |

### 收工后补跑（evidence 入库后）

- 地盘门验伪锚（§三附 (l) 的空洞项）：存档 commit 后重跑
  `git -c core.quotepath=false --no-pager diff --name-only --no-color 6d8ca202 HEAD | grep -c '^_bmad-output/'`
  → **67**（>0，锚成立；**提交前实测为 0 = 空洞**，与 P5-A §五.9-bis 同款，两态均留档）。
  证据 `final-anchor-*.txt`；同次带 exclude 重跑仍**恰九文件**（+267/−24 净 diff；`626d5416` 对一行既有 g68 注释的 +1/−1 已并入）。
- 绑定性终检：`git diff --stat 626d5416 HEAD -- . ':(exclude)_bmad-output'` → **空**（存档 commit 只动 `_bmad-output`）。
- 0 字节存档处置：`regression-{open,close}.nodeids`（空 = 零红）按「0 字节不入库」规**不入档**；
  零红事实以源日志（2167→2169 passed / **0 failed**）为证。
