# r6 复核结论

**绑定核验：通过。** 当前分支 `card/p10-docs`，`HEAD = e90fc46cd9fc6c9dd147a00631c3554f01993f29`，parent 为 `7f6dfeb8bb174d81eb8cf7cec53aa02bb2def663`。本轮只读，未改文件。  
注意：工作树中还有本轮未跟踪的 `codex-review-CARD-R-SLO-r6.md` 与 r6 prompt，不属于被审 commit `e90fc46c`。

**最终分级：0 BLOCKER / 0 HIGH / 0 MEDIUM / 2 LOW。**

---

## BLOCKER

无。

## HIGH

无。因此无需 HIGH 级后续补证。

## MEDIUM

无。

## LOW

### L1 · “窗口内 8011 连续可用”仍比证据略强，应改成“各次探测均可用”

**位置：**

- `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-erratum-20260920T133330.txt:6-7`
- `_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-erratum-20260920T133330.txt:14`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:267`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:277`

**事实：** 勘误档第 6 行的证据面是“窗口内 8011 探针全部 200/健康”，这是离散探测事实；第 14 行与 UAT §11.14/§12 概括为“窗口内 8011 连续可用”。虽然已明确“同进程/无重启连续性未证”，但“连续可用”仍可能被读成“窗口内每一时刻均被监测且可用”。

**最小 docs-only 后续措辞：** 改为“窗口内各次 8011 探测均 200/健康；未做连续 uptime 监控；同进程/无重启连续性未证”。

### L2 · UAT 顶部终态元数据仍不完整：未列 `b0ac7192`，Codex 轮次行也未更新 r5

**位置：**

- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:6-7`
- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:306-307`

**复跑事实：** `a03f0ce3..e90fc46c` 实际有 13 个 commit：A/A2/A3/A4/B 共 5 个，之后另有 `b0ac7192` 补审归档、`090dc4b5..7f6dfeb8` 6 个锁版前置 commit、`e90fc46c` r5 整改 commit。顶部叙述列了 5 + 6 + “r5 后另追加”，但漏列 `b0ac7192`；第 7 行 Codex 轮次也仍止于 r4，而 §14 已登记 r5。

**影响：** §14 与 `git rev-parse HEAD` 兜底使消费面仍能取得正确状态，不影响 draft 面；但单独读顶部会得到不完整终态。

**最小 docs-only 后续措辞：** 顶部改为“A/B 5 + 补审归档 1 + 锁版前置 6 + r5 整改 1”，并把 Codex 轮次补至 r5。

---

# ② 作者自述逐条核验

| # | 结论 | 核验 |
|---|---|---|
| A1 r5 M1 处置 | **成立** | 勘误档 :6-14 明确收窄容器连续性、tracked 脏文件口径、ignored runtime 面、重建项仅脚本 blob。原取证档在 `9ed914e5..e90fc46c` 与 `7f6dfeb8..e90fc46c` 均无 diff。UAT §11.14 :267、§12 :277 已同步。仅剩 L1 的“连续可用”措辞略强。 |
| A2 r5 M2 处置 | **成立** | 勘误档 :16-23 给出 `<FE-worktree>` / `<repo-root>` 消费面，并声明原始档保留绝对路径作复核用途；UAT §7 :172 同步。README/yaml 在 r5 增量零改动，且两文件 `/Users/` 命中为 0。r5 新增 review/prompt/erratum/UAT 中也未命中实际 `/Users/Heishing` 路径。 |
| A3 r5 L1 处置 | **成立，但顶部仍有 L2 残余** | UAT :6 已补“A/B 5 + 锁版前置 6 + 当前 HEAD 以 `git rev-parse HEAD` 为准”；yaml `code_sha_null_reason` 仍为测量期 draft 措辞；§14 :306 已登记锁版 commit 时按裁定改写。该处置本身到位。 |
| A4 无回归 | **成立** | `a03f0ce3..e90fc46c` 非 `_bmad-output` 面仅：README `13 insertions / 0 deletions`、yaml `269 insertions / 0 deletions`。`7f6dfeb8..e90fc46c` 不触 README/yaml/schema/validator/J08。yaml 仍 `status=draft`、`revision=r1`、`code_sha=null`，9 个 `threshold.locked` 全为 null。注意 git 文件状态是 README `M`、yaml `A`；“均为新增”应理解成内容均为本卡新增/纯插入。 |
| A5 勘误档无新强主张 | **部分** | tree/blob/diff/0-commit 事实均复算成立；“连续可用”仍略强，见 L1。ignored 面 mtime 与 causality 未独立重跑，见 UNVERIFIED。 |

---

# ③ r6 焦点逐项回答

## ⓪ r5 三项是否闭环、是否新矛盾

**实质闭环。**

- **M1：** 四类收窄均落地；原档未重写；UAT 消费面同步。
- **M2：** 原始档保留、勘误档作为 redacted 消费面的关系清楚；README/yaml 零改动且无宿主路径。
- **L1：** 顶部元数据已按 r5 建议补底，但仍有 L2 的不完整问题。

未发现新的 MEDIUM/HIGH 级矛盾。

## ① 收窄后的候选语义是否仍超出证据

**核心语义可支持，但建议按 L1 微调“连续可用”。**

独立复算：

- `tree(7f6dfeb8:backend) = 78a352945f5d9627c667483fa9e224bdbef216e3`
- `tree(9c4e7e82:backend) = a5cd759a1f2d46737e337b87cefcf577a353c62c`
- `scripts/daily_review_pick.py` 在两 ref 下 blob 均为 `2d6c745ad7468c6e529299da1a2af7d250c0e0aa`
- `9c4e7e82..7f6dfeb8 -- backend` 仅新增：
  - `backend/scripts/freeze_release_candidate.py`
  - `backend/tests/unit/test_freeze_release_candidate.py`
- 顶层 `scripts` diff 为空。

额外强于勘误档明文的复核：窗口前 FE reflog anchor `61b85b5b`、窗口后 `59e1f494` 与 `9c4e7e82` 的 backend tree 均同为 `a5cd759a...`；`67d66672..59e1f494 -- backend src` 无 commit。因此“tracked backend tree candidate”没有找到更强反例。

## ② 脱敏补充是否充分

**充分。**

- 原始 Docker inspect 档 :15-19 保留绝对路径，且用途已声明为复核。
- 勘误档 :17-23 是消费面 redacted 表示。
- UAT §7 :172 明确“原始档保留、消费面以勘误档为准”。
- README/yaml `/Users/` 命中 0。
- r5 新增其他文档面未发现实际 `/Users/Heishing` 路径。

## ③ UAT 顶部 / §7 / §11 / §12 / §14 是否自洽

**主体自洽。**

- §7 :172 与勘误档 :16-23 对齐。
- §11.14 :267 已按 tracked tree、同进程未证、ignored 面、脚本 blob 口径收窄。
- §12 :277 与 §11.14 候选语义一致，仍等待裁定。
- §14 :306-307 正确登记 r5 2M+1L 与处置。
- §6(f)② 计数复算成立：README 中 `slo-manifest.yaml` 命中 3 行、出现 5 次。
- 剩余问题仅在顶部元数据完整性，见 L2。

## ④ 若发现 HIGH 的最小补证

无 HIGH。两个 LOW 的最小动作均为 docs-only 措辞修正，不需要新增 `.py` 或证据采集。

---

# 关键复算记录

- 累计非 `_bmad-output` 面：仅 README + yaml。
- README：`13/0`。
- yaml：`269/0`。
- r5 整改增量：仅 r5 review、r5 prompt、erratum、UAT，共 4 文件；README/yaml 未动。
- 原始 `code-sha-runtime-tree-20260920T131615.txt` 自引入以来未改。
- yaml 当前关键值：
  - `revision: slo-manifest@2026-09-19-r1`
  - `status: draft`
  - `code_sha: null`
  - 9× `threshold.locked: null`
  - `decision.locked_by/locked_at: null`

上下文读取说明：请求中的 `2026-08-28-主goal全量分goal台账-v2.md` 按原文件名不存在；同名语义文件实际为 `2026-08-28-主goal全量分goal总账-v2.md`，已读 :405-410，与 R-SLO owner/锁版要求一致。

# UNVERIFIED

- **窗口内连续 uptime / 同进程无重启：** 现有证据只有前后 Docker 状态与离散 HTTP 探针，不能证明全程连续；本轮也未访问 Docker socket。
- **ignored 文件分类与 mtime：** `.env`、`.hypothesis`、`__pycache__`、`llm_call_logs.db` 等 ignored/mtime 事实未在本轮重跑，只核对勘误档与 r5 记录；不验证 mtime 变动与测量的因果关系。
- **FE reflog 时间戳本身：** 本轮用 Git 对象/tree/diff 复算，但没有重读 FE worktree reflog 原文；时间戳以已入库取证档为准。
- **原始 Docker live mount 状态：** 只核对存档，不做当前 Docker inspect。
