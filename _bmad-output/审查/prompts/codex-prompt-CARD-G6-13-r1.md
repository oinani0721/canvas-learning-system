# CARD-G6-13 · J07 次日复习旅程（开发门）独立审查请求（round-1）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`（P5 车道末张）。本卡基线 `PREV = f0cacff6`（P5-B 末 commit）；
**审查绑定 `00553b4e`**（= commit A：J07 证据 + manifest + 验收单；其后 commit B 只加负控与
Codex 存档等 `_bmad-output` 面，不碰代码面 —— 绑定判据以 `git diff --stat 00553b4e HEAD -- .
':(exclude)_bmad-output'` 为准）。
批次 `[BATCH-2026-09-18-第十五批 / CARD-G6-13]`。

本卡性质（**零代码 · 验收/证据卡**）：

1. **fixture 半边（已执行）**：G6-8 五面契约 **2 时刻 × 2 时区四档**跑通（verdict=PASS）；
   真实数据**三面对账**：live vault 只读 `rsync` 到 tmp 副本后，picker `--write` / API
   `review_overview._collect()`（g68 同款注入、时钟 pin、⛔ 不 import `app.main`）/ Markdown
   三面 **(板,节点,桶) 集合与 ranked 板序一致**（`three_face_equal=True`）；校验器单份 rc=0
   零 `[S`/`[A`；`tests/regression` 2169 passed、点名套件 1216 passed。
2. **用户旅程（未执行 · 卡文 (c) 整段 SKIP）**：跨日旅程（Day0 作答 / Day1 四桶 / 回炉 /
   snooze / 完成 / 深链 / 原库 hash 门）需**用户当次授权**（口令「G6-13 授权 J07 窗口」）+
   主 session 先合入部署 P5-A/P5-B；两者均未发生 ⇒ **全部 `not_run` + SKIP 登记**，
   `evidence_level=E2` / `result=partial` / `signoff=pending`。⛔ 车道未代用户 POST 任何
   `/overview/*`、未写 live、未请求 readonly 旁路。
3. **负控两段（已执行，commit B 落档）**：① 把已提交 `picker-final.json` 的 `top_boards`
   首两板对调 → 对账红在「ranked 板序不等」（集合判据仍 True，隔离干净）；② `manifest`
   `artifacts[0].sha256` 末位翻位 → 校验器 rc=1 含 `[A2] artifact checksum 不符`（非
   `[load]`/非 rc=2）。两段均 `git show HEAD:` 还原 + shasum 前后逐字同。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color f0cacff6 00553b4e -- . ':(exclude)_bmad-output'
    （本卡代码面净 diff = 新增 docs/release-evidence/dev-b15-p5/journeys/J07/ 15 文件）
docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json         （全文, 核心被审对象）
docs/release-evidence/dev-b15-p5/journeys/J07/ 其余 14 件            （artifact; 抽查）
docs/release-evidence/README.md:38-79（三步操作 / 退出码）与 :100-124（S1-S17/A0-A3 表）
backend/scripts/validate_release_manifest.py:263-300（_semantic_checks / is_e3_plus）与 :430-504（S9/S10）
backend/scripts/g68_five_view_contract.py:1-30（契约自述）与 :103-119（已登记分歧）
backend/app/api/v1/endpoints/review_overview.py:360-376（五桶口径）与 :1127-1150（_collect 读投影）
_bmad-output/验收单/UAT-CARD-G6-13-J07-2026-09-20.md                 （全文）
_bmad-output/审查/evidence-g613/three-face-compare.py               （对账脚本全文）
_bmad-output/审查/evidence-g613/three-face-20260920T010118.txt      （对账输出）
_bmad-output/审查/evidence-g613/validate-j07-*.txt / validate-all-post-*.txt
_bmad-output/审查/evidence-g613/negctl-1-*.txt / negctl-2-*.txt
_bmad-output/审查/evidence-g613/jev-triage-00553b4e.json
_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:596-612（J07 定义 + :611 授权条款）
_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md（:899 G6-13/R-J07 分工, :965 分层裁定）
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:143-144
```

行号为送审时实测；漂移以符号名为准。

**jev 分诊（jev-1.13.0，绑 `00553b4e`；③ 的问题顺序按其 urgency 降序）**：

| 文件 | urgency | P(review) | risk |
|---|---|---|---|
| （_bmad-output）evidence-g613/build-j07-manifest.py | 1.78 | 0.82 | test_or_docs |
| three-face-compare.py | 1.64 | 0.58 | test_or_docs |
| sanitize.py | 1.61 | 0.57 | security |
| _tmp_cmp.py（three-face-compare 的误入副本，将于 commit B 移出） | 1.37 | 0.60 | test_or_docs |

（全表见 `evidence-g613/jev-triage-00553b4e.json`；J07 产物本身未被分诊工具当作代码面。）

## ② 作者自述（请独立核对，勿直接采信）

1. `manifest.json` 15 键齐（required 差集 `[]`），过校验器**产物真验默认档**（不加
   `--skip-artifact-verify`）：单份 rc=0 零 `[S`/`[A`；`--all` rc=0 且 2 份（J07+J08）。
2. `evidence_level=E2` 按阶梯**从低取**、未 overclaim：`provenance.mode=reconstructed` +
   `unproven_fields` 6 条逐条列；`signoff=pending`（S10 禁止回填件 approved）；
   `skips_or_mocks.declared=true` 与 not_run 联动（S4）。
3. 三面对账**真比板序**：集合 6=6=6；`ranked` picker 3 前缀 = api/md 4 全长；且 picker 与
   API 的**投影同源**（API 读 `outputs/今日复习.json` 再自派生）已在
   `known_limitations` 如实声明。
4. 五桶（new/learning_queue/due_now/due_today/future，relearning 并入 learning_queue）偏差
   已写进 manifest（对计划书 J07「四桶」口径），未改产品口径。
5. 车道**零写 live**：live 只经 `rsync` 只读复制（`.canvas-config.yaml` 双端 sha 同）；
   未 POST `/overview/*`；未写仓库 `backups/`；未连 7691/7687。J07 全目录 `grep '/Users/'`=0。
6. 负控两段红在指定位置（见 ①-3）；两份被变异文件 shasum 前后逐字同、`git status --
   docs/release-evidence` 0 行。
7. 本卡零 `.py` 改动（ruff 判据集合空 ⇒ 判据作废，如实写）；`openapi.json` 不在任何 commit。

## ③ 按重要性排序的问题（逐项给结论；顺序 = jev urgency 降序 + 卡文清单）

- **⓪ manifest 有无「自洽但不实」**：逐条核 —— ①`not_run` 是否被写成 `pass`（J07-1/2/3/4/5/8
  应为 not_run；J07-6/7 为 pass 且**范围**已在 note 里限定）；②`skips_or_mocks` 与 E 级是否
  联动（S4）；③`signoff.user` 是否等于 `execution.operator`（S15；本卡 pending 应不触发）；
  ④`candidate.sha` 用的是**本车道树 HEAD**（f0cacff6…）而**非** 8011 执行期树 —— 该替身是否
  在 `unproven_fields` 被如实列？（作者主张「是」；请核措辞是否够强。）
- **① 三面对账是否真绑在三份独立产物上**：picker 面 vs API 面**同源**（API 读 picker 输出）
  ⇒ 作者承认「独立渲染面只有 Markdown 链」。请核：`three-face-compare.py` 的提取路径是否
  只是把同一 JSON 换三种读法（若是，价值边界应如何表述才不给读者过高预期）？集合为空的
  作废分支（rc=2）是否写对？
- **② 原库 hash 门的处置**：本卡未执行（not_run）是否被清晰登记为「未授权 ⇒ 不产生
  live-before/after」，而不是用别的东西（如副本 sha）冒名顶替？「live 零写入」的主张其证据
  面（rsync 只读 + copy-fidelity + 全程零写命令）是否够支撑？
- **③ `candidate.dirty` 口径**：卡文写死 `git status --porcelain -- . exclude
  docs/release-evidence exclude _bmad-output` 空 ⇒ `false`。作者实测 0 行 ⇒ `dirty=false`。
  但**未跟踪的 J07 产物本身**在该命令下被 exclude 掉、`_bmad-output` 也被 exclude —— 这个
  口径是否如实（notes 是否写明）？还是说发布证据本应把「新增未跟踪件」也计入？
- **④ 负控两段是否红在指定断言**：①板序对调是否只让 ranked 判据红（集合判据不应受影响）；
  ②sha 翻位是否必为 `[A` 产物不符而**非** `[load]`/rc=2？请对着 `negctl-*.txt` 原文核。
- **⑤ 验收单 4-B 是否零技术词、felt-sense 是否在场**：本卡未授权 ⇒ 4-B 写的是「预置、待确认」
  的用户语言 + 明示「这不是已发生的感受」。请核：有没有把「待确认」冒充成「已确认」？
- **⑥ 其它真问题**按 ④ 格式照报。

## ④ 输出格式

- 发现清单，每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复跑思路>`；
- 复跑思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 末尾必须有一行自检汇总：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写）；
- 用中文输出；结论先行（一两句裁决），再列发现。

## ⑤ 边界

- **只读**：不得修改任何文件（`--sandbox read-only`）；不连库（7691/7687/7692）；不 push。
- **不评**（范围外）：P5-A 时区解析器面 / P5-B 推送三态面（均已各自收口）；R-J07 的 RC 复跑
  与 `--require-complete`（那是冻结 RC 上的门）；G8-6 dogfood；D-37 三个产品口径；
  `inbox_preview.py:430` +08:00 产品口径本身（T3-B 待用户裁）。
- 本轮只审 `00553b4e` 所钉的树态（含其证据与文档）；commit B 的增量（负控存档等）以文件面为准。
