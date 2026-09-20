# UAT · CARD-R-SLO — SLO manifest 起草 + README 反向引用 + 现网只读实测

> **批次**：`[BATCH-2026-09-18-第十五批 / CARD-R-SLO]` · 车道 `card-p10-docs`（分支 `card/p10-docs`），本车道第 **3/3** 张（末张）
> **`<PREV>`**（P10-B CARD-R-RC 末 commit）：`a03f0ce3`（`a03f0ce34de9a9c4652310d45eae283f78d11451`）
> **最终代码 SHA**：`a03f0ce34de9a9c4652310d45eae283f78d11451`（本卡零代码：commit A/B 只改 `docs/release-evidence/` 与 `_bmad-output/`；代码面 SHA 恒等于 P10-B 末 commit）
> **commit 数**：A/B 5（A = yaml + README + 本验收单 + evidence-rslo；A2/A3/A4 = 三轮整改；B = 负控 + Codex 存档 + 收工裁判） + 补审归档 1（`b0ac7192`） + 锁版前置 6（`090dc4b5`→`67d0555c`→`29d578e5`→`9ed914e5`→`f01dc9a3`→`7f6dfeb8`） + r5 整改 1（`e90fc46c`） + r6 整改 1（`4f80542f`） + r7 收口 1（`d0e8b989`） + 锁版 1（`08cf6bf7`） + 锁版存档 1（`f27531a9`） + r8 整改 1（`90b8db84`） + r9 收口 1（`aa72d7ba`） + r9 记录补录 1（紧随其后）**；若用户当次锁版另有 C —— 当前 HEAD 以 `git rev-parse HEAD` 为准。
> **Codex 轮次**：r1（绑 A）：0B/4H/1M/1L ⇒ 整改（A2）；r2（绑 A2）：0B/1H/1M/1L ⇒ 整改（A3）；r3（绑 A3）：0B/1H/1M/1L ⇒ 整改（A4）；**r4（绑 A4）：0B/0H/0M/2L ⇒ 通过**（L1→台账 #10；L2→§6 evidence index；绑定核在 B 后 = 非 `_bmad-output` 面空 diff）；r5（绑 `7f6dfeb8`）：0B/0H/2M/1L ⇒ 整改（勘误+脱敏+元数据）；**r6（绑 `e90fc46c`）：0B/0H/0M/2L ⇒ 整改（L1 措辞收窄 + L2 顶部元数据补全）**。另：ZCode/GLM-5.3 通道（绑 `e4ef1ebf`）：0B/0H/0M/3L（已随锁版前置处置，见 §14）。 r7（绑 `4f80542f`）：0B/0H/0M/0L ⇒ 锁版前置面收口；**r8（绑 `f27531a9`，锁版轮）：0B/2H/1M/3L ⇒ 整改（§15 补录 + 过期陈述更新 + degrade_rule 勘误 + 腿输入存档）；**r9（绑 `90b8db84`）：0B/0H/0M/0L ⇒ 锁版面收口（交主 session）**。
> **签字**：✅ 2026-09-20 用户口令「R-SLO 授权锁版」+ 9 项逐项裁定（含 5 项 not_measured owner 分派）⇒ `status: locked` / `revision: slo-manifest@2026-09-20-r2`（§12 已签 / §15 锁版记录）

---

## 0 一句话

整批 J manifest 卡在 E2 的那块拼图落成单文件 `docs/release-evidence/slo-manifest.yaml`：9 项指标、每项可复跑命令、**4 项现网只读实测**（首屏 / RAG warm / kg 读 / 复习重建）、1 项因样本含超时如实 `not_measured`（cold）、4 项写侧只读不可测项如实 `not_measured` + 指定 owner 卡；README 补 `slo.manifest_revision` 反向引用段与锁版规则，并加一条「S9 不查 draft/locked」的已知边界。阈值：4 项 measured 已由用户 2026-09-20 锁版照准（`threshold.locked`，revision `slo-manifest@2026-09-20-r2`），5 项无候选保持 `null`（not_measured + owner 卡）；锁版记录见 §15。

---

## 1 第 0 分钟（完成条件 a）

| 项 | 期望 | 实测 |
|---|---|---|
| `pwd` / 分支 | `…/worktrees/card-p10-docs` / `card/p10-docs` | ✅ 同 |
| `HEAD` | P10-B 末 commit（message 含 `CARD-R-RC`） | ✅ `a03f0ce3` / `grep -c CARD-R-RC` = 1 |
| `git status --porcelain` | 空 | ✅ 0 行 |
| `merge-base --is-ancestor 9c4e7e82 HEAD` | rc=0 | ✅ 0；`a03f0ce3` 亦为 HEAD（`a03f0ce3..HEAD -- . ':(exclude)_bmad-output'` = 0 行） |
| 基线 `grep -vc '^#' "$BASE"` | **33** | `33`（跑法头第 3 行逐字同） |
| venv pytest / `.env` / pyright `test -x` / `import yaml` | 在场 / 6.x | ✅ 全部；`yaml 6.0.3`（失败即停的条款未触发） |
| `docker ps` 只读存档 | —— | ✅ 三容器 healthy；**8011 在跑** ⇒ 现网只读实测执行（非 not_measured 整段） |

**手册地盘核**（`grep -nF -e 'CARD-R-SLO' -e 'card-p10-docs' <手册>` 命中 P10 行，抄原文）：
- 手册 `:38`：`| **P10 release-evidence** | `card-p10-docs（NEW @ B15_BASE（= 主干 ff 后 SHA，草案时点 9c4e7e82））` | G1-3（总账，8h） → R-RC（总账，5h） → R-SLO（总账，6h） | 19 |`
- 手册 `:897`：`### P10-C（CARD-R-SLO）`；`:903`：「车道：…card-p10-docs…本车道第 3/3 张…前提：P10-B 已独立 commit 且工作树干净。」
- ⛔ 未改手册（零写者）。

### §〇 file:line 核对（README 经 P10-A/P10-B 已漂，按标题文本重定位）

| 卡文引用 | 实测 | 说明 |
|---|---|---|
| schema `:475/:476/:485`；validator `:76/:430-439/:442-475/:323-326`；`SCHEMA_SHA256` `:63` | **未漂** | 逐条 `sed -n` 核过，内容与卡文一致；指纹 `4456e1ad…c547` 逐字同 |
| 校验器测试 `:120/:668` 的 `slo-manifest@2026-08-28-r1` 形态；`def test_` = 147 | **未漂** | 供 revision 命名形态与计数口径 |
| J08 示例件 `:177-180` `manifest_revision: null` | **未漂** | 本卡零改动 |
| 8011 端点行号（health `:59-60/:423-424/:945/:947/:953-954/:1081-1082`；rag `:46/:49/:265-266/:277/:503-504/:565/:595`；review `:1185-1186/:1741-1742/:3064`；index `:81/:123`；router `:69/:151-152/:238/:467`） | **未漂** | `require_internal_api_key` 计数：health 0 / rag 0 / index 0 / review 1（docstring） |
| README 卡文 `:59` / `:75` / `:94` / `:152` / `:164` / `:166` | 实测 `:151` / `:167` / `:186` / `:244` / `:256` / `:258` | P10-A/P10-B 插入段落后整体下移（`## 字段速查` 现 `:173`；`## 语义与产物规则` 现 `:192`） |
| README `:34-36` 示例件说明 | 实测 `:36-38` | 同上 |

---

## 2 先红（完成条件 b；存档 `pre-20260919T170257.txt` / `pre-consumer-20260919T171717.txt`）

| # | 判据 | 期望 | 实测 |
|---|---|---|---|
| ① | `git grep -n 'slo-manifest' -- docs backend/scripts scripts \| wc -l` | 0（验伪锚 `-- backend/tests` = 2） | `0` / 锚 `2` ✅ |
| ② | `test -e docs/release-evidence/slo-manifest.yaml; echo rc` | 1 | `rc=1` ✅ |
| ③ | `grep -c 'slo-manifest.yaml' README` | 0 | `0` ✅ |
| ④ | `validate_release_manifest.py --all` | rc=0（份数如实） | `rc=0`，**1 份**（J08 一份；P10-B 未建 `<rc>/` 骨架）✅ |
| ⑤ | 消费契约先红：tmp J08（首条指标五键）+ validator + 对照脚本 | validator 绿 / 对照脚本红 FileNotFoundError | ✅ 见下 |

⑤ 明细（`pre-consumer-20260919T171717.txt`）：tmp J08 的 `slo` 换成 `{manifest_revision: slo-manifest@2026-09-19-r1, measurements:[review_overview_first_paint_p95_ms 五键]}` 后——
- **validator 绿**（`rc=0`，仅 `⚠️ 已弃权 artifact checksum` 一行）——证明「校验器绿 ≠ revision 存在」；
- **对照脚本必红**：`FileNotFoundError: docs/release-evidence/slo-manifest.yaml`（rc=1）——本卡新增的 revision↔yaml 对照门是唯一把两者钉在一起的门。

⚠️ 形状修正（卡文 :X → 实测 :Y，详见 §9）：`$TMP/j08.json` 裸文件按校验器 S6 结构门必红，故文件实体放 `$TMP/example-backfill-d5/journeys/J08/manifest.json`（结构合规），`$TMP/j08.json` 以 symlink 指入——`resolve()` 跟 symlink，rev-check 与 validator 均按卡文命令路径执行。

---

## 3 实现 ①：`docs/release-evidence/slo-manifest.yaml`（9 指标）

- `revision: slo-manifest@2026-09-19-r1` · `status: draft` · `decision.locked_by/locked_at: null` · `schema_version: 1.0.0`
- 固定键齐：`id / metric / unit / description / threshold{locked,candidate,threshold_source} / method{command,repeat,statistic,environment_ref} / measured{status,value,p50,p95,n,at,reason?,evidence} / degrade_rule / owner_consumer`
- `export_shape` 写死五键映射（metric / threshold（candidate 带 `(candidate)` 标记）/ measured（`p95=…` 或 `not_measured`）/ method / meets；unit 可选）
- `environment`：Apple M5 Max / 128GiB / macOS 26.5 arm64 / Python 3.14.4 / git 2.50.1 / 模型栈各端自报（ollama unreachable；12341 qwen3.5-35b-a3b-q4_k_s；18012 bge-reranker-v2-m3；health/ai=LLM_AUTH_FAILED 自报）/ data_scale（md=214；index/stats `{}`；kg 0/0/0）/ `data_sha=df036977…` / **`code_sha: null` + 理由**（`evidence-b15/` 无 code_sha 公布，实测三件仅 docker-ps/lanes-created/unit-red-baseline）/ `lane_sha=a03f0ce3…` / 并发 1 / PDT(America/Los_Angeles) / seed=`rag-queries.txt` sha256 `4dd05b33…` / repeats 20·5 / 统计量 `median + quantiles(n=20)[18]` / adjudicator null
- `not_in_scope`：索引 freshness → G2-10/G4-14；gold-set 七指标 → G4-14

| 指标 | candidate | measured | n | p50 | p95 | 存档 |
|---|---|---|---|---|---|---|
| review_overview_first_paint_p95_ms | ≤ 500ms | **measured** | 20 | 9.9ms | 39.1ms | `measure-review_overview_first_paint-20260919T171124.txt` |
| rag_query_warm_p95_ms | ≤ 5000ms | **measured** | 20 | 1668.7ms | 1866.5ms | `measure-rag_warm-20260919T171144.txt` |
| rag_query_cold_p95_ms | null（无有效样本） | **not_measured** | —— | —— | —— | `measure-rag_cold-20260919T171226.txt` |
| kg_read_p95_ms | ≤ 500ms | **measured** | 20 | 3.6ms | 27.1ms | `measure-kg_read-20260919T171134.txt` |
| review_rebuild_p95_s | ≤ 30s | **measured** | 5 | 0.05s | 0.05s | `measure-review_rebuild-20260919T171556.txt` |
| first_index_seconds | null | not_measured（G2-10） | —— | —— | —— | —— |
| graphiti_ack_ms | null | not_measured（G4-14/7692） | —— | —— | —— | —— |
| graphiti_replay_s | null | not_measured（R-J10） | —— | —— | —— | —— |
| recovery_time_s | null | not_measured（R-J10） | —— | —— | —— | —— |

实现 ②（实测）要点：
- 8011 全部 **GET + `/rag/query` 一个 POST 读查询**；**20/20 全 200** 的项：首屏（body=30187B 非空锚）、warm、kg；重建 **5/5 rc=0**。
- **cold 整项 why-not-measured**（规则内判定，不剔除样本）：20 条互异串的第 4 条 `http_code=000`（curl -m 120 → 120.0037s）；其余 19/20=200（p50≈3.29s、p95≈5.36s 仅作描述）；同串复打一次 1.67s 通过（`probe-cold4-replay-20260919T171547.txt`）⇒ 瞬态挂起。
- 重建只写 **tmp rsync 副本**；live `outputs/今日复习.json` 前后 shasum 逐字同（`105f563c…` ×2，`live-outputs-before/after.txt`）；仓库树无意外写入（`git status` 唯一未跟踪项 = 本卡自己的 `evidence-rslo/`）。
- 统计汇总 `measure-stats-summary-20260919T171634.txt`（首跑脚本 glob 失误的就地重写版，文件头已自述）。
- 实测窗口 **2026-09-19 17:11–17:16 PDT**；门跑于 17:19–20:4x（其间约 3 小时墙钟间隔，系统时钟前后一致、无回拨，如实登记）。

---

## 4 实现 ③：README 反向引用段（`### SLO manifest（CARD-R-SLO）`，插在「字段速查」表后 /「语义与产物规则」前）

含：① 位置；② `slo.manifest_revision` = yaml `revision` 字面（形态 `slo-manifest@<日期>-r<N>`）；③ 锁版规则（draft 只可被 ≤E2 引用；E3+ 需 locked + locked_by 非 null；⚠️ 无机器门）；④ 版本化（改阈值 = 新 r<N+1>、旧标 `superseded_by`）；⑤ 现网只读口径（8011 GET + 7691 白名单只读语句，不经 pytest、不写）；⑥ J08 示例 `null` 是 ≤E2 合法形态。
「已知边界」段**新增一条**（纯追加）：R-SLO 锁版状态无机器门（S9 只查非 null）。
README 改动 = **纯新增**（`-` 行数 = 0）。
> P10-B 未在树内冻结 rc 名（无 `<rc>/` 目录入库，真 rc 由主 session 在候选 SHA 冻结）⇒ 本卡 README 段落不引用具体 rc，沿 README 既有 `<rc>` 约定。

---

## 5 结构判据 (f) / 消费契约门 (g) / 套件 (i)

### (f)（权威组：`yaml-check-20260919T211540.txt` / `rev-check-post-20260919T211540.txt`（A3 轮重跑，r3 复核通过）；过程档 `f12-struct-…171903` / `yaml-check-…202309` / `rev-check-post-…171908`）。⚠️ 落地时机（ZCode LOW-2 补注）：本行 211540 组随 **commit B（`c2b1fac3`）** 入库。

| # | 判据 | 结果 |
|---|---|---|
| ① | `test -e …/slo-manifest.yaml` | `rc 1 → 0` ✅ |
| ② | `grep -c 'slo-manifest.yaml' README` | `0 → 2`（A 期）；**锁版前置重测 2026-09-20：行计数 3、出现 5 次**（≥1 满足；ZCode 记 4 为计数口径差异）✅ |
| ③ | revision 对照脚本 | `rev_check=OK slo-manifest@2026-09-19-r1 9`（rc=0）；**验伪锚**：tmp revision 改 `…1999-01-01-r9` → 红在 `('revision 不在 yaml', …)`（rc=1）；还原后 rc=0 ✅ |
| ④ | yaml 自检 | `yaml_ok metrics=9 measured=4 not_measured=5 status=draft`；**验伪锚**：删一条 `reason` 再跑 → 红（`AssertionError: rag_query_cold`）✅ |
| ⑤ | schema 指纹 | `shasum` 与校验器 `SCHEMA_SHA256` 两值逐字同 `4456e1ad…c547` ✅ |

### (g) ① 消费契约门（存档 `validate-export-e2-20260919T202340.txt` / `validate-export-e3-20260919T202346.txt`）

- **E2·对照输入 A（J08 原状 result=partial）**：全量 9 项五键导出 → `[S9]×5`（cold + 4 写侧，`meets=false` 且无 waiver）rc=1 —— 即「携带 not_measured 项的 manifest 在 partial 下被 S9 拦」。
- **E2·对照输入 B（§12.5 合法出口：result=fail）**：`rc=0`、`grep -c '[S'` = **0** —— 五键导出形态与 schema `additionalProperties:false` 相容、`measured: "not_measured"` 过 minLength（本轮达成卡文期望的 rc=0 零 `[S`；达成条件与卡文差异见 §9）。
- **E3 变体·字面清单**（evidence_level=E3 / mode=live / unproven=[] / dirty=false / result=pass / declared=false）：撞 **schema 级**拒绝（`provenance` 残留 `reconstructed_from`，`mode=live` 不允许）——字面清单不足以完成 live 化。
- **E3 变体·清理版**（另去 `reconstructed_from` + `skips_or_mocks.items` 置空）：`[S9]×5`，**全部**为「未达标（实测 not_measured）且无用户 waiver」相关；另 `[S3]×1` 为 J08 自身 D5-6 断言 `not_run` 的既有属性（与导出无关）→「E3 需 waiver 或全测」实证达成。

### (i) 套件

| 项 | 期望 | 实测 | 存档 |
|---|---|---|---|
| `tests/unit/test_validate_release_manifest.py` 显式路径 | 「147」 | **168 passed**（147 = `def test_` 计数口径；pytest 实收集含参数化）rc=0 | `named-validate-alone-20260919T202507.txt` |
| + P10-B `test_freeze_release_candidate.py` 一并 | 0 failed | **208 passed**（168+40）rc=0，开工/收工各一次 | `named-open-20260919T202409.txt` / `named-close-20260919T203835.txt` |
| `tests/unit` 目录级开工 | 差集只允许 `<` | 32 failed（基线 33），diff 仅 `<` 1 条（已知 flaky `…_422`） | `unit-open-20260919T170315.txt` / `open.nodeids` |
| `tests/unit` 目录级收工 | 同上 | 32 failed（5771 passed），diff 仅 `<` 1 条（同 flaky） | `unit-close-full-20260919T203241.txt` / `close.nodeids` / `unit-close-diff-20260919T203835.txt` |

> 注：`unit-close-20260919T202638.txt` 为同数据的 tail-6 摘要版（首个 tee 写法只截了尾部），规范归档以 `unit-close-full-*` 为准。
> 注（权威组）：A3 轮重跑起为本表权威证据——`validate-export-e2/e3-20260919T211540.txt`、`named-close3-20260919T212159.txt`、`unit-close3-full-20260919T211555.txt` + `unit-close3-diff-20260919T212159.txt`；A4 轮（负控 3 输入侧证据）重跑组见 §6 指针。早期组仅作过程对照。

### (j) openapi / pyright

本卡不改端点（commit 不含 `backend/openapi.json`）；不改 `backend/app` ⇒ pyright 不适用（第 0 分钟环境自证通过即可）。

---

## 6 负控（k）与 Codex（n）—— 按卡片顺序在 **commit A 之后**执行，存档随 commit B 入库

- **负控两段**（提交后对已跟踪文件做；`git show HEAD:<path>` 还原 + 前后 `shasum` 逐字同）：
  - 段 1：yaml `revision` 末位 `r1→r7` → 重跑对照脚本 → 须红在 `('revision 不在 yaml', …)`；
  - 段 2：`export_shape` 临时多导出一键（`note`）→ 重跑 E2 导出 + 校验器 → 须 rc=1 且含 `note`（schema 拒收），非 `[load]`/rc=2。
  - 段 3（补充；回应 r1 H3 / r2 H-R2-1）：**未被拦下的输入**配对演示——固定 `result=partial`，同一导出只 A/B `meets`：`meets=false` 5 项 ⇒ `[S9]×5`；`meets=true` 5 项 ⇒ 0 条 `[S9]`（S9 放行路径，缺口归因于 meets 单变量）。首版（把 result 一并改 fail）不具区分度，已被 r2 判定并重做；两版存档并存。
  - 存档（权威组）：`negctl-1/2/3-20260919T211541.txt`（配对版；绑定 A3）+ A4 轮重跑组（负控 3 含输入侧证据）；每组含还原后 `git status --porcelain -- docs/release-evidence` 输出，回应 L1。首版 `negctl-3-20260919T205702.txt` 仅作历史对照——r2 已判定其设计不具区分度，**不作承重证据**。
- **Codex 四轮**（`glm-5.3` / `max`）：r1 绑 A / r2 绑 A2 / r3 绑 A3 各出 1×HIGH 均逐轮整改；**r4 绑 A4：0B/0H/0M/2L ⇒ 通过**（L1 登记台账 #10；L2 以 A4 evidence index 处置）。轮次 4 ≤ 上限 5（零代码卡本应 1 轮；因前轮 HIGH 触发逐轮整改）。
  - 存档：`codex-review-CARD-R-SLO.md` / `-r2.md` / `-r3.md` / `-r4.md`（各带 §2.4.1 首部）+ prompts 四份，随 commit B 入库。
  - **A4 evidence index（r4 L2 处置）**：
    - 负控：`negctl-1/2/3-20260919T213522.txt` + `negctl-3-inputs-A/B-20260919T213522.json`（首版 `negctl-3-20260919T205702.txt` 仅历史对照）
    - 结构/契约：`yaml-check / rev-check-post / validate-export-e2 / validate-export-e3 -20260919T213532.txt`
    - 地盘/脱敏：`landgate-20260919T213532.txt` / `desens-final-20260919T213533.txt`
    - 套件：`unit-close4-full-20260919T213539.txt` + `unit-close4-diff-20260919T214207.txt`（修正版；`214133` 版为空表提取失误，作废）+ `named-close4-20260919T214207.txt`
    - Codex：`codex-review-CARD-R-SLO-r4.md`（绑 `e4ef1ebf`）
- **地盘门 (l)** 亦于 commit A 后跑：`$PREV..HEAD -- . ':(exclude)_bmad-output'` 只列 `docs/release-evidence/slo-manifest.yaml`（新）+ `README.md`；README `-` 行数 = 0；`*.py`/schema/openapi/ledger 命中 0；验伪锚去掉 exclude 多出 `_bmad-output/`。存档 `landgate-*.txt`（随 B）。

---

## 7 脱敏与只读门 (m)（权威组：`desens-final-20260919T211549.txt`（A3 轮）；过程档 `desens-final-20260919T202600.txt`；`neo4j-ro-20260919T202618.txt`）。⚠️ 落地时机（ZCode LOW-2 补注）：211549 组随 **commit B（`c2b1fac3`）** 入库。

| 判据 | 实测 |
|---|---|
| yaml 内用户主目录绝对路径（形如斜杠 U-s-e-r-s 的机器路径） | `0` ✅ |
| `fsrs_bridge` / `decay_beta` 引用 | `0` ✅ |
| 内部 API key 值泄漏（卡文口径 `INTERNAL_API_KEY`） | **实测该变量不在 `backend/.env`（0 行）⇒ 不适用**；补充：`NEO4J_PASSWORD` 值命中 0、`GOOGLE_API_KEY` 值命中 0 ✅ |
| 敏感字段名字面（NEO4J 密码字段+等号） | `0`（首版脱敏档自指污染已就地重写，见 §9）✅ |
| live outputs before/after | 逐字同 `105f563c…` ✅ |
| `measure-*.txt` 内写端点字样 | `0`（写端点一个未打）✅ |
| 7691 触达 | 全部经 8011 只读 GET；白名单直连语句**未使用**（存档贴语句原文与 `READ_ACCESS` 形态）；7687 未触达 / 7692 未用 ✅ |

> 补充（r5 M2 脱敏登记）：新增取证档 `code-sha-runtime-tree-20260920T131615.txt` 含 bind 源宿主绝对路径（原始档保留、复核用途）；**消费面以 `code-sha-runtime-tree-erratum-20260920T133330.txt` 的 redacted 表示为准**。README/yaml 面 `/Users/` 命中仍 = 0（两文件不变）。

---

## 8 执行侧收尾（o）

- commit A：`docs(r-slo): SLO manifest 起草 + README 反向引用 + 现网只读实测 [BATCH-2026-09-18-第十五批 / CARD-R-SLO]`（yaml + README + 本验收单 + `evidence-rslo/**` 逐文件 `git add`，⛔ 非整目录）。
- commit B：`docs(r-slo): 负控 + Codex 存档 …`（negctl 存档 + Codex 存档/prompt + landgate + 上述收尾裁判存档）。
- `*.stderr*` 不入库（本卡 evidence 内实测 0 个；四轮 Codex 的 `.stderr` 均留在工作区不入库）；0 字节文件不入库（实测 0 个）；不 push；末 commit 后工作树干净即收工（本卡全部产物随 A/A2/A3/A4/B 入库，见 §6）。
- **终态（收工重算，B 时点）**：代码面 SHA = `a03f0ce3`（本卡零代码；非 `_bmad-output` 面自 PREV 后零改动）；commit 数 = **5**（A/A2/A3/A4/B）；Codex 轮次 = **4**（r1-r4；r4 绑 A4 且 BLOCKER/HIGH = 0）；evidence-rslo 文件数 = **82**（B 入库时点 ≤；含四轮存档组）。

---

## 9 卡文 :X → 实测 :Y 偏差表（须主 session 知悉）

| # | 卡文 | 实测/处置 |
|---|---|---|
| 1 | README 行号 `:59/:75/:94/:152/:164/:166` | 实测 `:151/:167/:186/:244/:256/:258`（P10-A/B 插入所漂），按标题重定位，本单 §1 已列 |
| 2 | §二.5 `$TMP/j08.json` 裸路径 | 校验器 **S6** 要求 `<rc>/journeys/<Jxx>/` 结构 ⇒ 实体放结构合规路径、`j08.json` symlink 指入（两条路径同一文件，已披露） |
| 3 | §一(b)⑤ / §二.6 (g)① 预期「rc=0 零 `[S`」 | 全量导出保持 `partial` 时实测 `[S9]×5` rc=1（机器行为：`meets=false` 在任意等级触发 S9 链）；rc=0 零 `[S` 经 §12.5 合法出口 **result=fail** 达成（对照输入 A/B 两跑都落档）。E3 字面清单另撞 schema（`reconstructed_from` 残留），清理版得 `[S9]×5`（全部为 meets=false/无 waiver 相关） |
| 4 | §一(g)③/§二.7「收集 147」 | 147 = `def test_` 计数；pytest 实收集 **168**（含参数化）；合并 freeze 文件共 **208 passed** |
| 5 | §一(d)③ 查询串源 `节点/ head -20` | 该目录实测仅 **14** 文件 ⇒ 扩至 `节点×14 + 原白板×6 = 20` 条互异串（仍为 live vault 文件名只读；seed sha 见 yaml） |
| 6 | §一(d)③ cold 预期 20/20；§一(g)② 任一非 200 ⇒ not_measured | 实测 19/20=200 + 1×000（120s 超时）⇒ **整项 not_measured**（样本不剔除）；复打 probe 1.67s |
| 7 | §一(m) K=`INTERNAL_API_KEY` | 该变量实测不在 `backend/.env` ⇒ 子项不适用；以两个真实敏感值做同口径补充（命中皆 0） |
| 8 | 收尾命令模型 | 手册 §三 P10-C 行仍为换代前旧模型串（D-43 已换）；按卡文 §四 + 协议 §2.4（D-43）执行 = **`glm-5.3` `max`**（本卡 4 轮：r1-r4；零代码未触发上限 5） |
| 9 | —— | 实测窗口 17:11–17:16 与门跑 17:19–20:4x 之间有约 3 小时墙钟间隔（系统时钟一致、无回拨），非证据缺失 |
| 10 | —— | 两处就地重写均已在文件头自述：`measure-stats-summary-…T171634.txt`（首跑 zsh glob 失误）、`desens-20260919T202508.txt`（首版标签自指污染） |

### 9b 首轮 Codex（r1，绑 commit A）4×HIGH 的整改记录（落地于 commit A2）

| 项 | r1 指摘 | 整改 |
|---|---|---|
| H1 | cold 非「20 条首见」（seed 第 1 条已先被 warm 预跑）；命令缺实际用的 `-m 120` | yaml `cache_state` / cold `description` 改为「20 条互异串各一次，实为 19 条首见+1 条已暖」；warm/cold 命令补 `-m 120`（首屏/ kg 各补 `-m 60`/`-m 30`，与实测一致） |
| H2 | 「现网零写/只读」强于证据面（service 层未审、live 无全量前后 SHA） | README 新段与验收单收窄为「发起命令面 + 已核对锚点（outputs 前后同）」；service 层副作用与全量 SHA 列入未证明（§10） |
| H3 | `not_measured+meets=true` 是门未覆盖路径；S9 不强制覆盖集；无对应演示 | 新增**负控段 3**（未被拦下的输入，演示 S9 放行）；yaml `export_shape` 补两条纪律说明；README「已知边界」新增一条 |
| H4 | `(未定)` 三态未写进 `export_shape.mapping` | mapping 的 threshold 行补「两者皆 null ⇒ `(未定)`（占位, minLength=1）」；README 导出 bullet 同步 |
| M1 | 写侧 `method.command` 是 sketch 而非可直接复跑 | 四项 command 均补 `method sketch：实参/实例由 owner 卡在其环境补全` 注记 |
| L1 | 负控还原后 status 未落档 | 负控重跑组（绑定 A2）在存档内直接输出 `git status --porcelain -- docs/release-evidence` |

### 9c 次轮 Codex（r2，绑 A2）1×HIGH + 1×MEDIUM + 1×LOW 的整改记录（落地于 commit A3）

| 项 | r2 指摘 | 整改 |
|---|---|---|
| H-R2-1 | 负控 3 同时改了 `meets` 与 `result`，rc=0 不能归因于 `meets=true` | 重做为**配对演示**：固定 `result=partial`，仅 A/B `meets`（false ⇒ `[S9]×5`；true ⇒ 0 条 `[S9]`），新档 `negctl-3-*.txt`（新时间戳）；UAT §6 同步改述 |
| M-R2-1 | cold「其余 19 条首见」过度确定（进程历史命中未证） | `cache_state` 与 cold `description` 改述为「19 条未由本卡 warm 环节预跑+1 条已暖；其余 19 条历史命中未证（只读约束拿不到查询历史）」 |
| L-R2-1 | yaml 写「E3+ 至少一条实测」与机器语义有差 | `consumption_note` 改为「measurements 非空；『至少一条真实实测』是消费纪律、非机器门」 |

### 9d 三轮 Codex（r3，绑 A3）1×HIGH + 1×MEDIUM + 1×LOW 的整改记录（落地于 commit A4）

| 项 | r3 指摘 | 整改 |
|---|---|---|
| H-R3-1 | 配对负控 3 缺输入侧证据（A/B manifest、hash、逐字段 diff、pre-assert 输出） | A4 轮重跑为**输入落档版**：A/B 两份 manifest 写入证据区 + sha256 + 归一化逐字段 diff（应恰好 5 处 `meets` false→true）+ pre-assert 输出全部落档（新档 `negctl-3-*.txt`；`negctl-3-inputs-A/B.json`） |
| M-R3-1 | UAT 指针仍指 A2 旧组 | 本单 §5/§6/§7 指针改为 A3/A4 权威组；首版 `205702` 明标「历史对照，不作承重」 |
| L-R3-1 | README 既有行「至少一条实测」句式歧义 | 既有行受「纯新增（`-` 行数=0）」硬约束**不可删改**；在本卡新增 bullet 内加澄清一句 + 台账登记交主 session 批级统一句面 |

### 9e 四轮 Codex（r4，绑 A4）结论 —— 通过

**0 BLOCKER / 0 HIGH / 0 MEDIUM / 2 LOW**（D-15 条件满足；B 只动 `_bmad-output` ⇒ 绑定核在 B 后 = 非 `_bmad-output` 面空 diff）。
- L1（README 概括 vs `method sketch`）⇒ 台账 #10 登记（后续句面统一时处理）；
- L2（A4 指针可再精确）⇒ §6 已加 A4 evidence index。

---

## 10 本卡未证明什么（≥4；as-of `d0e8b989`——锁版后条目 1/4/12 已更新，其余仍适用）

1. **未证明任何阈值「合理」**（锁版 ≠ 证明合理）——4 项 `threshold.locked` 是用户 2026-09-20 照准的起草值（实测×余量，单机单时段证据）；5 项无候选（not_measured）；用户可经新 revision 逐项改。
2. **写侧四项未实测**——首次索引 / Graphiti ACK / replay / 恢复时间只给了在指定环境（G2-10 / 7692 / R-J10）可复跑的命令与 owner 卡，`not_measured`，⛔ 未填估计值。
3. **RAG「cold」是「进程未重启的首见串」口径**——未证明进程冷启动后的真实首查延迟（现网禁重启）；且本次 cold 因 1 次超时整体 `not_measured`，连该口径的结论也未成立。
4. **单机 / 单时段 / 并发 1 / n=20（重建 n=5）**——不证明跨机、跨日、并发下的分布；也不证明「8011 当时运转的代码树 = 本车道树」（`code_sha` 已随 r2 绑为 `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680`——绑定为取证件收窄口径，同进程连续性未证；见 §15）。
5. **`/rag/query` 的 service 层写点未审、且未做 live vault 全量跑前/跑后 SHA**——端点文件内无写点已核；service 层是否记录查询/学习事件未审（若有，本卡 40 次官方查询 + 2 次探针查询已在现网留痕），移交 G4-14 或 P8 census；「只读」目前只到发起命令面 + outputs 锚点（README 已同步收窄措辞）。
6. **README 锁版规则没有机器门**——校验器 S9 只查非 null、不查 draft/locked 与 revision 存在性；靠 G1-6 审计链与 R-J0x 人工核。
7. **重建耗时在 tmp 副本上测得**——未证明等于 live 目录上的耗时（磁盘/缓存位置不同）。
8. **真实 J 卡消费未端到端证明**——(g) 契约门用 J08 演示件做载体（其 `[S3]`/schema 既有属性已单列）；A/B 两跑的 S9 语义结论对任何消费卡成立，但「某张真 R-J 卡引用本 revision 直到 E3」的全链未发生。
9. **导出纪律无全量机器门**——`not_measured ⇒ meets=false` 与「9 项全导出」只是纪律：S9 在 `meets=true` 时直接放行、且只要求 ≥1 条测量；负控段 3 已把该未被拦下的输入落档（README 已知边界同登）。
10. **cold 的唯一一次 120s 超时未定位到根因**——复打通过仅说明当时呈瞬态；其触发条件（并发/负载/特定串）未证明。
11. **README 既有行（「三步操作」第 2 步）句面残留**——r3 L-R3-1：该句「至少一条实测」易被读成机器门；受本卡「纯新增（`-` 行数=0）」硬约束不可删改，已在本卡新增 bullet 内澄清并登记台账（批级统一句面修订项）。
12. **锁版前置（2026-09-20）只清复核 LOW 与文档口径**——不新增任何实测、不改任何 candidate/measured 数字；5 项 not_measured 依旧未测。**后续（同日）已执行锁版：4 项 `threshold.locked` + r2（见 §15）。**

---

## 11 台账待登记条目（≥4；条目 1/2/7 已更新至锁版后，其余为 as-of `d0e8b989`）

1. `docs/release-evidence/slo-manifest.yaml`：**`revision=slo-manifest@2026-09-20-r2`、`status=locked`**（2026-09-20 用户锁版；此前 r1=draft）、9 指标（4 measured / 5 not_measured，**4×`threshold.locked` / 5×null**）+ 每项 p95（首屏 39.1ms、warm 1866.5ms、kg 27.1ms、重建 0.05s）——供 G8-8 / G2-10 / G4-14 / G6-11 / R-J0x 引用（E3+ 现可引用）。
2. **锁版授权状态**：**已发生（2026-09-20）**（口令 + 9 项逐项裁定 + code_sha 裁定，原文见 §15）⇒ 全批 J manifest 可引用 `slo-manifest@2026-09-20-r2`（locked）⇒ **E3 引用可行**；写侧 5 项仍按 not_measured+waiver 链（S9 不变）。
3. 写侧四项 owner 回填：G2-10（首次索引）/ G4-14（ACK 在 7692）/ R-J10（replay + 恢复时间），并在总账对应卡「做什么」里回填「复用 R-SLO 条目 id」；cold 复测亦归 G4-14。
4. 清单更正：`manifest.schema.json` 与 J08 示例件**零改动**；「查询 7691 只读」收窄为「经 8011 GET 或白名单两条 `execute_read`（本卡实际未用直连）」。
5. `/rag/query` service 层写点未审 → 移交 G4-14 或 P8 census（本卡 42 次查询已在现网留痕，如 service 层记账则含本次）。
6. README 行号漂移实测表（本单 §1）并入台账备注；「S9 不查 draft/locked」的已知边界已写进 README。
7. Codex 轮次（glm-5.3 max）r1–r8 + ZCode 通道 rc：存档路径/绑定 SHA/计数见 §14（r1–r7）与 §15（r8 锁版轮）；r9 为本整改的复核轮。
8. 卡文偏差表（本单 §9 共 10 条）需主 session 知悉；测时窗口与门跑之间的 3 小时墙钟间隔一并登记备查。
9. README「三步操作」第 2 步既有句「至少一条实测」（受「纯新增」约束本卡未改）——批级统一句面修订时与 R-EVD 原文一并处理（r3 L-R3-1）。
10. r4 L1：README `:198` 概括写侧为「可复跑命令」略强于 yaml `method sketch` 事实——**锁版前置已就地改**（该句属本卡新增 bullet，非既有行）：改称「method sketch（owner 补实例/实参后复跑）」。
11. ZCode LOW-1 处置：README 既有行「校验器不做数值比较」与 S9 数值交叉核对并存的歧义——既有行不改（纯新增约束），已在 `## 已知边界` 新增并存口径澄清条；批级统一句面修订时再处理既有行。
12. ZCode LOW-2 处置：§5/§7 权威组补「随 commit B（`c2b1fac3`）入库」；§5 (f)② 终版重测计数（行 3 / 出现 5）；§6 A4 evidence index 随 commit B 落地。
13. ZCode LOW-3 处置：新增 `evidence-rslo/measure-stats-summary-v2-20260920T131200.txt`（同批原始样本重算 + 5 个 raw_sha256；cold 描述统计限 19 条 200 样本、全样本 max=120.0037 单列）；v1 原档保留不改。
14. **`code_sha` 公布请求（锁版前置；2026-09-20 已只读取证）**：总 goal 要求锁版时 `code_sha` 非 null；卡文 §一(c) 规定该字段 = 主 session 公布的「8011 进程代码树 SHA」。**取证已补齐**（存档 `evidence-rslo/code-sha-runtime-tree-20260920T131615.txt`）：docker inspect 实证 8011 = FE 树（`feature-obsidian-hybrid-dev`）`backend/` 的 live bind（镜像 `feature-obsidian-hybrid-dev-backend` digest `sha256:64aecd97…` 被 bind 遮蔽、不作代码身份）；FE 树 `67d66672..HEAD` **0 个 commit 触达 `backend`/`src`**，`tree(HEAD:backend) == tree(9c4e7e82:backend) == a5cd759a…` ⇒ **tracked backend 树**口径下，8011 所服务 `backend` == 批次代码面 `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680` 的 `backend`（tree `a5cd759a…`；车道侧 `git cat-file -t` = commit ✓）；窗口内各次 8011 探测均 200/健康、**未做连续 uptime 监控**（同进程/无重启连续性未证；r5 M1 / r6 L1）；唯一 **tracked** backend/src 脏文件 = 测试 fixture（mtime 2026-08-19、非运行时面），ignored 运行时面（`.env`/`.hypothesis`/`data/*` 等，含 `llm_call_logs.db` 窗口内 17:15 变动）不入 code_sha 口径；重建项仅 `scripts/daily_review_pick.py` blob 等同（`2d6c745a…`），本车道整棵 backend tree ≠ 代码面（r5 M1）。**候选绑定值 = `9c4e7e82f2c8…`（语义收窄详见 `code-sha-runtime-tree-erratum-20260920T133330.txt`）；待主 session 公布/用户裁定后由车道绑入**，未公布前维持 null + 理由（禁估计值/禁拿本车道树冒名）。**已裁定（2026-09-20）：用户采用候选值 → 锁版 commit 已绑入（见 §15）。**
15. **JEV 复核待重跑（绑最终 HEAD；2026-09-20 机制核实）**：`evidence-rslo/jev-triage-R-SLO-e4ef1ebf.json` 的 `code_files`/`files`/`usage` 全空。机制：`scripts/jev_review_triage.py` 默认 pathspec = `*.py/*.ts/*.tsx/*.sh/*.js`（代码扩展名）——**本卡零代码 ⇒ 默认跑法必然 0 文件 0 调用（PARTIAL）**，不得据此无限重跑。锁版 commit 后建议双跑并存档：(a) 标准 wrapper `bash ~/.b15b-drive/jev_triage.sh <final-HEAD> <outdir>`（协议 §6 原样，如实记 0 调用 = PARTIAL）；(b) 对实际交付面出分诊：`python3 scripts/jev_review_triage.py <final-HEAD> --out <outdir>/jev-triage-<short>.docs.json --pathspec docs/release-evidence --pathspec _bmad-output/验收单`（凭据名已就位：`~/.config/jev/env` 含 `TYPESAFE_API_KEY`（值不落盘）；`--help` 可用），使 `files/usage` 非空、B/H/M/L 口径可判。最终以主 session 对「零代码卡的 JEV 口径」裁定为准（本卡不自判）。 机制实证（2026-09-20）：`evidence-rslo/jev-triage-f01dc9a3.docs-prelock.json`（calls=1、usage 非空、verdict=REVIEW/test_or_docs）——**非门证据**，仅证 docs-pathspec 跑法可行；门证据须绑锁版 commit。

---

## 12 锁版签字位（用户节点，手册 `:353` 原文：「【P10 R-SLO】SLO 阈值锁版需用户签字（卡可先开工做采集命令 + 一次现网只读实测；锁版环节等用户）」）

> 口令：**「R-SLO 授权锁版」** + 逐项阈值裁定。
> 授权后车道将：`threshold.locked` 逐项填实 → `status: locked` → `revision` 升 `r2` → `decision.locked_by/locked_at` 填实（带时区）→ commit C（+ Codex `-r2` 再送一轮绑最终 HEAD）。

- ✅ 已裁定并绑入（2026-09-20）：`code_sha` = `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680`（用户裁定采用候选值；yaml `environment.code_sha` 已填，`code_sha_basis` 记依据；`git cat-file -t` = commit ✓）。
- ☑ 我同意以上阈值（可逐项批注修改）：**全部照准**（2026-09-20 口令授权原文见 §15；无修改项）
- 签字（用户）：Heishing　日期：2026-09-20
- **授权状态**：2026-09-20 已授权（「R-SLO 授权锁版」+ 逐项裁定）⇒ 锁版已执行：`status: locked` / `revision: slo-manifest@2026-09-20-r2`（见 §15）。

---

## 13 4-B 用户视角（零技术词）

- 我打开复习总览页 → 一秒内就看到今天要复习什么 → 我感觉它是随时可用的，不是要等它想。
- 我在白板里问一个概念 → 第二次问同一个问题明显比第一次快 → 我感觉它记住了我刚问过什么。
- 我看到一张表，上面写着「这些速度要多快才算合格」、每一项旁边有今天量出来的真实数字、还有一个空着的「我签字」位 → 我感觉标准是我定的，不是它自己说自己达标。
- 有几项写着「今天没量、原因是……、以后在哪儿量」 → 我感觉它没糊弄我。

---

## 14 锁版前置（A5-prep，2026-09-20；**as-of `d0e8b989` 历史记录——已被 r2 锁版 superseded，见 §15**）

> 状态（as-of `d0e8b989`）：当时 `status: draft`；本段只清复核遗留 LOW，不触发锁版。锁版已于 2026-09-20 完成（§15）。

- 触发：Codex r4（绑 `e4ef1ebf`）0B/0H/0M/**2L** + ZCode/GLM-5.3（绑 `e4ef1ebf`）0B/0H/0M/**3L**；goal 门 = 绑最终 HEAD 的 B/H/M/L 全 0。
- 处置（docs/evidence-only；yaml / schema / 校验器 / J08 零改动）：
  1. r4 L1：README 本卡新增 bullet 内「可复跑命令」→「method sketch（owner 补实例/实参后复跑）」（新增行，非既有行）。
  2. ZCode L1：README `## 已知边界` 新增一条并存口径澄清（纯新增；既有行不改）。
  3. r4 L2 / ZCode L2：§5/§7 权威组补落地时机（commit B `c2b1fac3`）+ (f)② 终版重测计数；§6 已含 A4 evidence index。
  4. ZCode L3：`evidence-rslo/measure-stats-summary-v2-20260920T131200.txt`（同批样本重算；cold 描述统计限 19 条 200、全样本 max=120.0037 单列）。
- 复核：`validate_release_manifest.py --all` rc=0（1 份 J08）；rev-check 对照 `rev_check=OK slo-manifest@2026-09-19-r1 9`；README 纯新增（`-` 行 = 0）；schema 指纹未动。
- 存档：`_bmad-output/审查/evidence-rslo/slo-prep-20260920T131200.txt`（本段全套命令输出）。
- 追加（2026-09-20 13:16）：`code_sha` 运行时树只读取证 → `evidence-rslo/code-sha-runtime-tree-20260920T131615.txt`（§11.14 候选值）。
- r5（绑 `7f6dfeb8`）：**0B/0H/2M/1L** ⇒ 本轮整改：①M1 → 新增收窄勘误档 `evidence-rslo/code-sha-runtime-tree-erratum-20260920T133330.txt`（容器连续性未证 / tracked 脏文件口径 / 重建项仅脚本 blob / ignored 面不入 code_sha）；②M2 → 脱敏补充（原始取证档保留绝对路径，消费面以 erratum 的 redacted 表示为准；§7 已登记）；③L1 → 本单顶部元数据更新；yaml `code_sha_null_reason` 于锁版 commit 按裁定改写（绑定 ⇒ 换绑定值+备注；维持 null ⇒ 理由改「候选已取证、待裁定」）。
- r5 存档：`codex-review-CARD-R-SLO-r5.md` + prompt（随整改 commit 入库）。
- r6（绑 `e90fc46c`）：**0B/0H/0M/2L** ⇒ 本轮整改：①L1 → 「窗口内 8011 连续可用」收窄为「各次探测均 200/健康；未做连续 uptime 监控；同进程连续性未证」（勘误档 + §11.14/§12 同步）；②L2 → 顶部元数据补全（含 `b0ac7192`；Codex 轮次补至 r5/r6）。
- r6 存档：`codex-review-CARD-R-SLO-r6.md` + prompt（随整改 commit 入库）。
- r7（绑 `4f80542f`）：**0B/0H/0M/0L** ⇒ 锁版前置面收口；后续只剩：用户口令/逐项裁定 + code_sha 裁定 → 锁版 commit → 锁版轮复核（目标同 0/0/0/0）。
- r7 存档：`codex-review-CARD-R-SLO-r7.md` + prompt（随本 commit 入库）。

---

## 15 锁版记录（2026-09-20；用户口令节点完成；r8 复核后补录）

> 补录说明（HIGH-1 处置）：首版锁版 commit（`08cf6bf7`）的 §15 追加脚本写错变量（写入未含 §15 的旧文本），§15 实际未落而 §12/顶部/存档已引用之；r8 复核（`codex-review-CARD-R-SLO-r8.md` HIGH-1）指出后，于 r8 整改 commit 补录本节。yaml 的 locked 对象不受影响（r8 已独立复核 4×locked/5×null、measured/method 与 draft 逐字一致）。

- **授权原文**（用户，2026-09-20，逐字）：
  > R-SLO 授权锁版。9 项 candidate 全部照准；5 项 not_measured owner 分派确认（③冷启 G4-14 复测 / ⑥首次索引 G2-10 / ⑦ACK G4-14 / ⑧replay R-J10 / ⑨恢复时间 R-J10）；code_sha 用候选值 9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680。
- **逐项裁定对照**（①-⑨ = yaml 指标顺序 first_paint / warm / cold / kg / rebuild / first_index / ack / replay / recovery）：① ≤500ms 照准；② ≤5000ms 照准；③ 无候选（整项 not_measured；owner=G4-14 复测后以新 revision 起草）；④ ≤500ms 照准；⑤ ≤30s 照准；⑥ 无候选（owner=G2-10）；⑦ 无候选（owner=G4-14/7692）；⑧ 无候选（owner=R-J10）；⑨ 无候选（owner=R-J10）——9 项全部照准，含 5 项 owner 分派。统计量（p50 median + p95 quantiles(n=20)[18]、rebuild n=5 同式）、repeats 20/5、并发 1、时区 PDT 一并确认。
- **code_sha 裁定**：采用候选值 `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680`（`git cat-file -t`=commit；binding basis 见 yaml `code_sha_basis`；证据 `code-sha-runtime-tree-20260920T131615.txt` + 收窄勘误 `…-erratum-20260920T133330.txt`）。
- **yaml 变更**（锁版 commit）：r1→r2；draft→locked；4×`threshold.locked` 填实（= 照准值）；5×`threshold.locked` 保持 null（⛔ 不填估计值）；`decision.locked_by/locked_at`、`environment.adjudicator` 填实；`environment.code_sha` 绑定 + `code_sha_null_reason`→`code_sha_basis`（null 条件消失）；`lane_sha` 更新为 `d0e8b989…`；4×`threshold_source` 与 9×`degrade_rule` 配套措辞更新（未改任何阈值数字/实测/统计量/导出映射）。
- **r2 消费腿（绑 r2）**：legA（partial）rc=1/[S9]×5；legB（整体 fail）rc=0/[S9]×0——输入与 sha 见 `slo-lock-legs-inputs-20260920T141118.txt`（LOW-3 处置）。
- **r8 复核与整改（锁版轮）**：r8 = 0B/**2H**/1M/3L ⇒ 本 commit 整改：① HIGH-1 → 本节补录；② HIGH-2 → §0/§10/§11/§14 过期活动陈述更新或 as-of 标注；③ MEDIUM-1 → `degrade_rule` 口径勘误档 `slo-lock-20260920T140356-erratum-degrade-rule-20260920T141118.txt`（按 r8 建议不改 locked 文案）；④ LOW-1 → README 版本化单文件例外句；⑤ LOW-2 → 顶部计数补至锁版存档 commit；⑥ LOW-3 → 腿输入档补齐。
- **后续**：r9 复核本整改（绑本 commit 后 HEAD，目标 0/0/0/0）；通过后说「复核第十五批 P10」交主 session。
- **r9 复核（绑 `90b8db84`）**：**0B/0H/0M/0L ⇒ 锁版面收口**（存档 `codex-review-CARD-R-SLO-r9.md`；随 `aa72d7ba` 入库）。
- **JEV 双跑（绑锁版 commit `08cf6bf7`）**：wrapper（协议 §6 原样）0 调用 = PARTIAL（零代码卡机制必然，见 §11.15 机制档）；docs-pathspec 变体 2 文件 triage、usage 非空（`jev-triage-08cf6bf7.json` / `jev-triage-08cf6bf7.docs.json`）——两文件 risk=test_or_docs、REVIEW 标记（= 推荐人工复审；两文件已经 r1–r9 + ZCode 多轮人审），无缺陷级发现。
- **交主 session**：说「复核第十五批 P10」；锁版面（`docs/release-evidence/`）已冻结——后续仅 `_bmad-output` 存档/记录 commit，`git diff 90b8db84..HEAD -- . ':(exclude)_bmad-output'` 为空。
