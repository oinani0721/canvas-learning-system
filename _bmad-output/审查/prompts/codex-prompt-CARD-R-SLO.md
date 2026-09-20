# CARD-R-SLO 复核请求（BATCH-2026-09-18-第十五批 · 车道 P10 末张）

## ① 背景与最小读取面（写死，请只读这些）

本卡 = 文档/证据卡（零 `.py` 改动）。产出：`docs/release-evidence/slo-manifest.yaml`（versioned SLO manifest，9 项指标 + 每项可复跑命令 + 一次现网只读实测）+ README 反向引用小节 + 验收单；schema / 校验器 / J08 示例件零改动。

审查绑定：`a03f0ce3`（PREV）→ `8e36c412`（commit A，本轮审的就是它；后续 commit B 只加 `_bmad-output` 存档）。树根 = 本仓 worktree。

请读（路径均相对树根；「本卡 diff」一条请真跑）：
1. 本卡 diff：`git --no-pager diff --no-color a03f0ce3 8e36c412 -- . ':(exclude)_bmad-output'`（应只含 `docs/release-evidence/slo-manifest.yaml` 与 `docs/release-evidence/README.md`）
2. `docs/release-evidence/slo-manifest.yaml` 全文
3. `docs/release-evidence/README.md`：新增小节「### SLO manifest（CARD-R-SLO）」与「已知边界」末条；另读「字段速查」表与「与计划书 L596 的对照（裁剪记录）」第 4 条
4. `docs/release-evidence/manifest.schema.json` :475-530（`slo` 块）
5. `backend/scripts/validate_release_manifest.py` :76-77（E3 集合）与 :359-477、:594-644（S3/S4/S9/S10/S16）
6. `_bmad-output/审查/evidence-rslo/` 关键存档：`measure-review_overview_first_paint-*.txt`、`measure-rag_warm-*.txt`、`measure-rag_cold-*.txt`、`measure-kg_read-*.txt`、`measure-review_rebuild-*.txt`、`measure-stats-summary-*.txt`、`validate-export-e2-*.txt`、`validate-export-e3-*.txt`、`rev-check-post-*.txt`、`pre-consumer-*.txt`、`negctl-1-*.txt`、`negctl-2-*.txt`、`desens-final-*.txt`、`landgate-*.txt`
7. `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md` 全文
8. 上下文（只读，供口径核对）：`../feature-obsidian-hybrid-dev/_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md`（§12.5 L592 附近）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md`（:405-410 owner 裁定）、`../feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P5-C.md`（§一(e) 的 E 级阶梯消费口径）

## ② 作者自述（请独立核对，逐条给成立/不成立/无法核）

1. schema 字段齐：机器 / OS / 模型版本 / 数据规模·SHA / 冷热 / 并发 / 时区 / 种子 / 重复次数 / 统计量 / 裁决人，每项在 yaml 里真实存在且取值有据（对照 evidence-rslo 存档与 `environment` 字段）。
2. 每项指标都有可复跑采集命令；命令不含用户绝对路径与任何 key 值。
3. `measured` 数字全部来自 evidence-rslo 存档（n=20；重建 n=5），非估计；`not_measured`（cold + 写侧四项）原因与 owner 卡如实、未填估计值。
4. 导出五键（metric/threshold/measured/method/meets）与 schema `additionalProperties:false` 相容；`measured: "not_measured"` 过 minLength；`export_shape` 的映射文字与实际导出行为一致。
5. revision 形态 `slo-manifest@<日期>-r<N>` 与校验器测试内既有形态同；`status: draft`（用户未授权锁版）与 `decision.locked_by: null` 自洽。
6. 现网零写：8011 只打 GET + `/rag/query` 一个读查询；7691 全部经 8011；写端点零打；live vault 只读（重建写 tmp 副本，live outputs 前后 shasum 同）。
7. 负控两段红在指定断言（`revision 不在 yaml`；schema 拒收 `note`），前后 shasum 逐字同、还原后 `git status --porcelain -- docs/release-evidence` 为空。
8. 地盘：`a03f0ce3..8e36c412` 非 `_bmad-output` 面只有 yaml + README；README 纯新增（`-` 行数 = 0）。

## ③ 按重要性排序的重点问题（请优先回答）

- ⓪ **yaml 是否「自洽但不实」**：`threshold.candidate` 的 `threshold_source` 是否真能追溯到实测数字或明标「无依据」；`cache_state` / cold·warm 的「进程未重启」口径是否在 yaml 内写明（而不是只能从验收单得知）。
- ① **导出映射是否会让 J manifest 的 `meets` 在 `not_measured` 项被误填 `true`**（应只能 `false`，并触发校验器 S9 链）；E2/E3 两跑对照（`validate-export-e2/e3-*.txt`）是否支持该结论。
- ② README 的锁版规则（draft 只可被 ≤E2 引用 / E3+ 需 locked）与校验器 S9「只查非 null」的实况是否一致；该限制是否已如实写进「已知边界」。
- ③ 实测样本是否含非 200 被剔除（cold 的 1×000 是否如实保留并导致该项 `not_measured`）；p95 口径（`statistics.quantiles(n=20)[18]`）与 n=5 的重建项口径是否写明。
- ④ 负控两段是否红在**指定断言**（而非其他原因）；`validate-export-e2` 的 rc=0 达成条件（result=fail 出口）是否被如实披露（对照 `partial` 版实测 [S9]×5）。

## ④ 输出要求

按 **BLOCKER / HIGH / MEDIUM / LOW** 分级；每条给 `文件:行`（或存档名）与最小证据；不要复述卡片摘要；无法核实的写 `UNVERIFIED` 并说明原因；对 ② 的每条自述给出核对结论。

## ⑤ 边界

只读复核：不要执行任何写操作、不要改动任何文件。若某文件不可读，如实标注后继续。历史语境词约定：描述未被执行或未被拦下的路径时，请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」这类表述。
