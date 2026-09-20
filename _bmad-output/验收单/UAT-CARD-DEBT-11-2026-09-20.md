# UAT — CARD-DEBT-11（5-ge-1 CanvasGraphEpisodeV1 schema 冻结 · 零代码路径）

> 批次: `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage`（分支 `card/p1-storage`）· 本车道第 **4/4** 张
> `PREV`（P1-C 末 commit，含 ZCode 补审）: `6f25de8b` · 起点锚 `c33240fa`（§零.6 容忍判据满足：锚为祖先 + 锚→HEAD 非 `_bmad-output` commit = 0）
> 最终代码 SHA: `4cc89ab3`（③；prod 面自 `f21cd421` 起逐字节未变——r3 绑定轮所审）· 本卡 commit 数: **4**（①`27743808` 实质 / ②`f21cd421` r1 整改+证据 / ③`4cc89ab3` r2 整改+证据 / ④本收尾）· Codex 轮次: **r1 / r2 / r3（r3 = 绑最终态的一轮，BLOCKER=0 / HIGH=0 达成）** · evidence 文件数: **72**（`_bmad-output/审查/evidence-debt11/`）
> 路径声明: **零代码路径**（prod 唯一改动 = `canvas_episode.py` 12 行 `#` 注释；D-32 `ast.dump` 逐字同 = `True`；diff 非 `#` 行 = 0）

---

## 一 本卡做了什么

把 C-1 写入契约 `CanvasGraphEpisodeV1`（`backend/app/graphiti/canvas_episode.py:208`；2026-06-03 后零改动；3 处生产消费方）正式冻结：

1. **裁 Task 3/4/5 归属**（全部带 file:line 证据进 spec）：Task 3 = 移交（落点全在 P2 outbox 地盘）；Task 4/5 = 废弃于本 story（表/端点候选树零存在）；Task 7 `[~]`→`[x]` + 注；
2. 复跑 `test_canvas_episode_v1.py` **19 用例**（开工 / 收工 / ③ 三档，存档）；
3. py 头注释 + spec `## Schema 冻结声明`（版本 + 15 字段 + 逐键冻结面 + 禁改规则 + 解冻路径）；
4. spec `in-progress`→`review`；sprint-status `STORY-5-ge-1` `ready-for-dev`→`review` + `schema_frozen`；
5. 两旧 spec（`1-16-callout-graphiti-hook` / `2-10-wikilink-graphiti-sync`）→ `superseded`（frontmatter+正文）；sprint-status 对应块加 `superseded_by`/`superseded_at`（`status` 回退见 §六.7）。

## 二 DoD-3

### 4-A Claude 已代验（技术证据）

**第 0 分钟**：pwd/分支 ✓；`PREV=6f25de8b`；锚 `c33240fa` 容忍判据 ✓；status 净（唯一未跟踪 = 自建 evidence 目录，澄清档在案）；pyright `test -x` ✓；红基线 `grep -vc '^#'` = **33** ✓。

**先红（工作树干净时）**：冻结 grep `spec:0 / py:0`（验伪锚 = 卡文 11 ≥1）；状态现状 `in-progress`×2 / yaml `ready-for-dev` / 两旧 spec `ready-for-dev`；复跑门 **19 passed**（collected 19）；AST dump sha 基线 `56200aca…`。

**负控两段**（段① `:246` raise→pass；段② `:214` Literal→V2；各 `git show HEAD:<path> > <path>` 还原 + shasum 前后逐字同）：

| 段 | 注入自证 | 结果 | 红在指定断言 | shasum 前=后 |
|---|---|---|---|---|
| ① | `pass  # NEGCTL-1` count=1 | **2 failed / 17 passed** | `DID NOT RAISE`×2（`test_narrative_empty_string_raises` / `test_narrative_whitespace_only_raises`） | `bc3b87da…` = 同 |
| ② | `Literal["…V2"] = "…V2"`；`D32-AST-EQUAL= False` | **1 failed / 18 passed** | `test_callout_added_valid`：`assert 'CanvasGraphEpisodeV2' == 'CanvasGraphEpisodeV1'` | `bc3b87da…` = 同 |

两段还原后 `py-restored-clean=ok`、`porcelain-nonself=0`。**②/③ 后重跑**（行号因 +11/+12 行插入改为 `:258`/`:226`，逻辑同）：① 仍恰 2 `DID NOT RAISE`、② 仍恰 `test_callout_added_valid` + `D32=False`，shasum `7b2f8f19…` 前=后、restored-ok。（存档：`negctl1-*`/`negctl2-*`/`negctl1-r2-*`/`negctl2-r2-*`）

**D-32（三档 + 验伪锚）**：`ast.dump(PREV:py) == ast.dump(worktree)` → **`True`**（绑 ①②③ 三次全 True）；`git diff PREV..③` 非 `#` 行 = **0**；验伪锚 probe（当前 prod 副本 + `X_PROBE = 1`，diff 恰 +1 行）→ `PROBE-EQUAL= False`。

**结构判据成对**：`grep -c -i -e freeze -e 冻结` **0/0 → 9/4**；spec `status: "review"` / `Status: review`；yaml STORY-5-ge-1 `status: review` + `schema_frozen`；两旧 spec frontmatter+正文 `superseded`；yaml `status: superseded` 0→2→**0**（回退见 §六.7）、`superseded_by:` = **2**。

**承重行为门**：复跑门 开工/收工/③ **19 passed ×3**；消费方集合（`test_belief_version_chain` / `test_canvas_episode_v1` / `test_graphiti_structured_writer`）**48 passed**；`tests/regression` 开工 1913 / 收工 1913 / ③ 1913 passed（nodeids diff 全空）；`tests/unit` 开工 **32 failed / 5787 passed**、收工 32 / 5787、③ 重验 **33 / 5786**（33 = 基线 33，集合逐项相等；本卡零引入红）。

**pyright**：开工 / ① 后 / ② 后 = **`0 errors` ×3**（80 warnings，与 P1-C 收工同值）；本卡零新增 ignore。

**ruff**：改动面（zsh 数组，17 文件）`All checks passed!` rc=0；F821 锚 rc=1（见 §六.2）。

**地盘门**：`27743808..4cc89ab3` 非 `_bmad` = 恰 `backend/app/graphiti/canvas_episode.py`；`_bmad-output` 侧 ⊆ 白名单（offwhite=0）；`services/openapi.json` = 0；验伪锚（去 exclude）多出 `_bmad-output/` 路径 ✓。

**现网只读**：本卡 `+` 行对 `fsrs_bridge` / `decay_beta` / `7691` / `7687` / `canvas-vault/` 命中 **0**；spec `+` 行 `7691` = 0；本卡不连任何库（无 7692 门）。

**blocked 说明（诚实登记）**：unit-open/close 档 `blocked=0`；③ 重验档 `=1 (blocked=1)`——哨兵归因 `owner=tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`（已知 flaky 本档转红、其路径尝试建 driver 被哨兵拦下）。该测试属基线 33 之一，本卡零行为改动（D-32 True）⇒ 判为既有噪声，登记不阻断。

### 4-B 用户能感知的变化（零技术词）

学习记录进知识库时的那份「登记表」格式从今天起**定版**——以后任何人想改格式，都得开新版本、走审批：我之前写进去的批注和双链，不会哪天因为格式被悄悄改了而读不回来。

我做了一次「把抽屉规则贴到墙上并上锁」的动作 → 我看到复跑检查 19 项全绿、两段故意拆锁的演练都被当场抓住、复原得一模一样 → 我感觉这份记录真的稳了，终于不用再靠「应该没问题吧」来安慰自己。

## 三 Codex 三轮（结论 + 处置对照）

| 轮 | 审 SHA | 结论 | 处置 |
|---|---|---|---|
| r1 | `27743808` | B0 / **H4** / M3 / L1 | H1 冻结面逐键展开；H2 证据入 commit（②）；H3 剩余面补漏；H4 `superseded` 回退（validator 枚举实测）；M1 登记；M2 Dev Notes 注解；M3 以 spec 为准；L1 行号订正 |
| r2 | `f21cd421` | B0 / **H2** / M1 / L2 | H1 edge payload 字段级冻结（v3）+ MAP 键对；H2 二轮证据全入 ③；M offset/anchor 引 belief resolver `:62-67`；L1 probe 重生成；L2 `:186/:187`、`:620` |
| **r3** | **`4cc89ab3`** | **B0 / H0 / M0 / L3 —— PASS（绑最终态达成）** | L1 默认值语义 + L2 `:226` 已于收尾修正（docs）；L3（py `:80` description 串陈旧）**不修**：修复需改字符串（非 `#` 行）⇒ 破零代码口径，登记（§四.2 / §五.7） |

存档：`codex-review-CARD-DEBT-11.md` / `-r2.md` / `-r3.md`（首部 blockquote 六字段齐、会话头自证三行行号括注；`.stderr` 不入库）。Jev 分诊三档（①`27743808` / ②`f21cd421` / ③`4cc89ab3`）JSON 在 evidence 目录。

## 四 本卡未证明什么（≥4）

1. **未证明 `edge_type_map` 透传后 Graphiti custom ontology 真生效**（Task 3 移交，本卡零 Graphiti 调用）。
2. **未证明冻结声明能被工具链强制**：只有文字 + 复跑门；字段集合快照结构门归后续卡（r3-L3 即例证——py `:80` description 串的陈旧描述在本卡口径下**无法**修）。
3. **未证明现网 7691 存量 episode body 全部符合 V1 15 字段**（本卡不连库、不做 census）。
4. **未证明旧 spec 剩余面（plugin 采集 / sweep / e2e 等）有人接手**（仅登记；正式 owner 需主 session）。
5. **未证明 unit ③ 档 `blocked=1` 不会在其它环境重现**（归因已知 flaky + 本卡零行为改动；未跨环境重验）。
6. **未证明 r1/r2 的 LOW 已全消**（L1/L2 处置、L3 登记；M1/M3 为登记性质的部分修）。

## 五 台账待登记条目（≥4）

1. **`[Decision-Review] PENDING`：三条裁定 + 证据 file:line** —— ① Task 3 移交（归属候选 DEBT-12 facade 卡或 P2 后续）；② Task 4/5 废弃于本 story；③ 两旧 spec supersede。
2. **5-ge-3 spec `:32`「(5-ge-1 建)」与 5-ge-1 D5 互指、无 owner**：不在本批地盘，登记待 5-ge-3 改。
3. **sprint-status 枚举**：`status: superseded` 实测被 BMAD sprint-status validator 判 invalid（合法值 = backlog/ready-for-dev/in-progress/review/done）⇒ 本卡按卡文预留路径回退为 `backlog` + `superseded_by`/`superseded_at`；若主 session 决定正式引入 `superseded` 枚举，需同步修改 validator 合法值表。
4. **LITE-4-3 / LITE-5-6 的 `depends_on` 仍指向已 supersede 的 2-10**（本卡 yaml 地盘仅三块，不能改）⇒ 依赖重定向待主 session。
5. **冻结面结构门候选卡**：字段集合 / enum 值 / 边类键快照测试（`test_schema_frozen_fields.py` 类）。
6. **`memory_service.py` `:476/:645/:1657` 入队点仍传旧 `CANVAS_EDGE_TYPES`**（D4 双本体并存）→ 随 Task 3 移交一并裁。
7. **py `:80` offset description 串陈旧（r3-L3）**：`sha256(node_path+offset)` 缺 `:` 与 `[:16]`；修复需非 `#` 行 ⇒ 破零代码口径；候选落点 = 后续「有代码改动」卡或 D-40 式尾扫。
8. **Codex 三轮存档路径 / 绑定 SHA / B-H-M-L 计数**：见 §三（r3 结案 = B/H=0）。

## 六 偏差与实测更正（登记）

1. **negctl trap 相对路径**：实测 `cd backend` 后 trap 内相对 `$PY` 还原会写错位置（TRAP-CWD=backend）⇒ 还原目标改绝对路径（机制仍是 `git show HEAD:<path> > <path>`）。
2. **F821 锚**：卡文要求仓内临时文件 + `rm` 清理；本环境 GUARD 拦截 `rm` ⇒ 改 `--stdin-filename` 免落盘（判据等价：rc=1、零残留）。
3. **negctl 行号**：① 态 `:246/:214` 与卡文一致；②/③ 后因注释块 +11/+12 行 → `:258`/`:226`（重跑用新行号）。
4. **卡文 (o) 预期 python-lint 必绿；实测 PREV 即 format-dirty**（D-40 整仓 462 之一）⇒ 协议 §2.3 过渡条款带证据 `LEFTHOOK_EXCLUDE=python-lint`（**未**排除 python-typecheck）；证据 = `lint-exclude-justification*` / `format-diff-*`（三件 + refresh 二件）。
5. **spec-reference hook**：含 `backend/app` 改动时要求 `@spec:` / `FR-` / `PLAN-` / `Co-Authored-By` ⇒ commit 带 `Co-Authored-By` trailer（P1 车道先例同款）。
6. **「单卡一个独立 commit」→ 实测 4 个 commit**：① 实质 / ② r1 整改 + 证据 / ③ r2 整改 + 证据 / ④ 收尾 docs；原因 = 两轮 B/H>0 整改 + r1/r2-H2「证据须入绑定 commit」；主 session squash 时按卡归并。
7. **`status: superseded` 实验收束**：卡文 (e)④ 要求首次引入；r2-H4 实测 validator 判 invalid ⇒ 回退（台账 3）。旧 spec md frontmatter 的 `superseded` 保留（archive 先例）。
8. **r1-L1 / r2-L1 / r3-L1,L2 处置**：行号订正（`:12/:186/:187`、`:620`、`:225→:226`）、probe 重生成（diff 恰 +1 行）、`schema_version` 默认值语义显式化——均在 ②/③/④ 内完成。
