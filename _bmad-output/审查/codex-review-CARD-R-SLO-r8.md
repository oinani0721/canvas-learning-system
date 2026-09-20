# r8 复核结论

**绑定核验：通过，但锁版收口不通过。**

- 当前 `HEAD = f27531a9be438350360cfbf40160f588380be5c3`，父链为 `d0e8b989 → 08cf6bf7 → f27531a9`。
- `08cf6bf7` 只改 UAT + `slo-manifest.yaml`；`f27531a9` 只新增锁版存档。
- 累计非 `_bmad-output` diff 只有 `README.md +13/0` 与 `slo-manifest.yaml +269/0`；backend/schema/validator/J08 零改动。
- `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680` 独立复核为 commit，且是当前 HEAD 祖先。
- 工作树有两个未跟踪 r8 prompt/review 文件，不属于被审 HEAD。本轮未改任何文件。

## 最终分级

**0 BLOCKER / 2 HIGH / 1 MEDIUM / 3 LOW**

---

## HIGH-1 · UAT §15 被多处引用，但在被审 HEAD 中不存在

**证据**

- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:8` 称「§12 已签 / §15 锁版记录」。
- 同文件 `:267`、`:278`、`:280` 均声称 code_sha 裁定或授权原文见 §15。
- `_bmad-output/审查/evidence-rslo/slo-lock-20260920T140356.txt:2` 也写「原文见 UAT §15」。
- 但当前 UAT 实际到 `:311` 结束，最后一节是 §14；不存在 `## 15`。
- 复跑：
  - `git grep -n '^## 15' f27531a9 -- '_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md'` 无命中。
  - `git log --all --oneline -S'## 15' -- '_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md'` 无历史引入记录。

**影响**

`slo-manifest.yaml:15` 中 9 项裁定、统计量/repeats/并发/时区确认、code_sha 裁定、`locked_at` 等授权细节无法从仓库内授权原文逐字核对。数值本体与本次请求描述一致，但锁版授权证据链不完整，且存档作出了不存在的原文指针。

**最小后续补证（零 `.py`）**

新增 docs-only 后续 commit：在 UAT 追加真实 §15，逐字保存用户授权消息、9 项裁定、5 个 owner 分派、code_sha 裁定与时间；再重跑 yaml SHA、locked 自检、rev_check、validator，并把新 HEAD 绑定到补充存档。不要改 4 个 locked 阈值或 measured 数字。

---

## HIGH-2 · 锁版后 UAT 活动面仍保留「draft / 未授权 / E3 不可达」的相反结论

**证据**

- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:14`：仍说「阈值全部是 candidate（draft），等用户口令锁版」。
- `:237`：仍说 9 项阈值全是 candidate，锁版前没有生产力标准。
- `:240`：仍说 `code_sha: null`、主 session 未公布。
- `:248`：仍说「阈值仍未锁版」。
- `:254-255`：仍登记 r1/draft，并说「R-SLO 授权锁版未发生 ⇒ 全批 J manifest 只能引用 draft revision ⇒ E3 不可达」。
- `:293-295`：§14 标题和状态仍说「未锁版」「`status: draft` 维持」。

这些不是已被清晰标记为 historical/as-of 的段落，而是当前 UAT 的摘要、未证明事项与台账活动面；与 `docs/release-evidence/slo-manifest.yaml:6-7,33-42` 及 UAT 顶部 `:8` 直接矛盾。

**影响**

消费者同时会得到两套结论：manifest 说 locked/r2/code_sha 已绑定，UAT 台账却说未授权、draft、E3 不可达。即使 yaml 本体正确，也会破坏锁版后的审计一致性。

**最小修复**

docs-only 后续 commit：更新上述活动陈述，或将 §10/§11/§14 明确标记为「as-of d0e8b989 历史记录，已被 r2 锁版 superseded」，并新增当前状态汇总。不要重写不可变历史存档。

---

## MEDIUM-1 · `degrade_rule` 的「不计判据」与 S9/导出消费链存在字面冲突

**证据**

- 9 处 `degrade_rule` 均写入「无候选、locked=null 项维护为 not_measured+owner，新 revision 起草前不计判据」，例如 `docs/release-evidence/slo-manifest.yaml:65,88,112,135,158,182,206,230,254`。
- 但导出口径要求全部 9 项导出，且 `not_measured ⇒ meets=false`：
  - `docs/release-evidence/slo-manifest.yaml:260-266`
  - `docs/release-evidence/README.md:271`
- validator 实际语义是：任何 `meets=false` 在整体 result 不是 `fail` 且无 waiver 时报 S9：
  - `backend/scripts/validate_release_manifest.py:457-466`

**判断**

如果「不计判据」读成“可忽略”，则与 legA 结果相反：`slo-lock-20260920T140356.txt:22-29` 中 partial + 5 项 not_measured 得 rc=1/S9×5；只有整体 result=fail 才 rc=0/S9×0。较精确语义应是：

> locked=null 项没有阈值比较判据，但导出为 `not_measured + meets=false` 时，仍触发 S9 的 result=fail 或用户 waiver 链；不能静默忽略。

**最小修复**

优先加 docs/evidence erratum 澄清，不应在未升 revision/未获用户确认时静默改 locked r2 文案。若要改 manifest 文案本身，需按版本规则处理。

---

## LOW-1 · r1→r2 版本化未真正落成 README 要求的 `superseded_by`

**证据**

- `docs/release-evidence/README.md:197`：「旧 revision 不删，只标 `superseded_by` 指向新值。」
- 当前单文件模式只在 `slo-manifest.yaml:5,15` 用注释/decision.note 指向 git 历史 `8e36c412`，没有 `superseded_by` 字段或独立版本索引。
- `8e36c412` 下确实可取回 r1/draft，但旧 r1 对象本身无法被追加 `superseded_by`。

**判断**

A3 只能算部分成立：git 历史可追溯，但未满足 README 字面上的 supersession 标记。可用 docs-only 的 history index 或 README 单文件例外规则收口。

---

## LOW-2 · UAT 顶部 commit 计数在最终 HEAD `f27531a9` 上少 1

**证据**

- `_bmad-output/验收单/UAT-CARD-R-SLO-2026-09-19.md:6` 只计数到锁版 commit `08cf6bf7`，合计 16 个 `a03f0ce3..08cf6bf7` commit。
- 实际 `git rev-list --count a03f0ce3..f27531a9` = 17；`f27531a9` 是新增锁版存档的额外 commit。
- 「锁版 1（本 commit）」在当前 HEAD 上也不再是“本 commit”。

顶部已有 `git rev-parse HEAD` 兜底，因此仅是元数据漂移，不是对象绑定失败。

---

## LOW-3 · r2 消费腿 legA/legB 缺少可字节复现的输入存档

**证据**

- `_bmad-output/审查/evidence-rslo/slo-lock-20260920T140356.txt:22-29` 只有结果摘要：legA partial rc=1/S9×5，legB fail rc=0/S9×0。
- 未存本次临时 J08 的 SHA、完整 JSON 输入或生成命令。旧 `negctl-3-inputs-A/B` 绑定 r1，不能直接证明 r2 输入逐字节形态。

结果与当前 export_shape 语义自洽，但严格复跑只能重建等价输入，不能复验同一输入。

---

# 作者自述逐条核验

| # | 结论 | 核验 |
|---|---|---|
| A1 锁版精确执行用户裁定 | **部分成立** | 核心对象精确：r2/locked；4 个 locked 阈值分别 ≤500ms/≤5000ms/≤500ms/≤30s；5 项 null；`decision`/`adjudicator` 填实；PyYAML 比较 `d0e8b989` 与 `08cf6bf7` 的 `measured`、`method` 完全一致。但 `decision.note` 的授权转述无法对照缺失的 §15 原文，且「9 项 candidate 全部照准」对 5 个无候选项表述不够精确。 |
| A2 code_sha 绑定扎实 | **成立** | `git cat-file -t` = commit；`9c4e7e82` 是 HEAD 祖先。复算 `tree(9c4e7e82:backend)` 与 FE HEAD `59e1f494:backend` 均为 `a5cd759a...`；本车道 `d0e8b989:backend` 不同，`daily_review_pick.py` blob 相同。`lane_sha=d0e8b989` 正确对应锁版 commit 父提交，最终 HEAD 由 `08cf6bf7→f27531a9` 链绑定。 |
| A3 r1→r2 版本化 | **部分成立** | r1 可从 `8e36c412` 取回；但未实现 README `:197` 的 `superseded_by` 标记，只靠当前 r2 note/git 历史。 |
| A4 配套措辞无语义变化 | **部分成立** | 未改阈值数字、实测、统计量或导出映射；但 `degrade_rule` 新句引入“不计判据”与 S9 fail/waiver 链的字面歧义。 |
| A5 门证据齐全 | **部分成立** | yaml SHA、schema 指纹、validator rc=0、9/4/5/4/5 结构均独立复核成立；但授权原文 §15 缺失，UAT 自相矛盾，legA/B 输入未存。 |
| A6 README 与 schema 零改动 | **成立** | 累计非 `_bmad-output` 面仅 README +13/0 与 yaml 新增；`d0e8b989..f27531a9` 对 backend/README/schema 零 diff。 |

---

# r8 焦点逐项回答

## ⓪ 锁版是否精确执行用户裁定

**核心数值执行：是；授权与文档收口：否。**

- 4 个 measured 项 locked 值与请求裁定一致。
- 5 个无候选项保持 null，没有填估计值，纪律成立。
- measured/method 与 draft 完全一致。
- 但 `decision.note` 无法与缺失的 §15 授权原文逐字核对；UAT 还残留“未授权/draft/E3 不可达”的相反活动陈述。

## ① code_sha 与 lane_sha

**code_sha basis 未发现超证据扩大。**

- 绑定值存在、为 commit、为 HEAD 祖先。
- FE backend tree 等同、脚本 blob 等同、本车道整棵 backend 不等同、同进程连续性未证、ignored 面不入口径，这些均与两份证据档一致。
- `lane_sha=d0e8b989` 是锁版 commit 的直接父提交；最终 HEAD 通过后续 `f27531a9` 存档 commit 绑定。该解释在 yaml 中已写明。

## ② degrade_rule 语义

**存在 MEDIUM-1 的字面冲突/歧义。** locked=null 项不是阈值判据，但导出后仍会作为 `meets=false` 进入 S9 的 fail/waiver 链；“不计判据”必须收窄，不能读成可忽略。

## ③ 锁版后 export_shape 与 legA/B

**对象映射自洽，但措辞需澄清。**

- 4 项导出 locked 阈值原样。
- 5 项 threshold 导出 `(未定)`，measured 导出 `not_measured`。
- legA partial 被 S9×5 拦截，legB 整体 fail 通过，这正是 `consumption_note` 与 validator 行为的组合结果。
- 不自洽点仅在 `degrade_rule` 的“不计判据”字面读法。

## ④ 过期/超证据措辞残留

**有，构成 HIGH-2。** 主要在 UAT `:14`、`:237`、`:240`、`:248`、`:254-255`、`:293-295`。另有 `decision.note` 的“9 项 candidate 全部照准”措辞欠精确。

## ⑤ HIGH 的最小后续补证

零 `.py`，仅 docs/evidence 面：

1. 追加真实 UAT §15 授权原文与逐项裁定、code_sha 裁定、时间。
2. 更新或标记 UAT 中仍称 draft/未授权/E3 不可达的活动段落。
3. 新增锁版后补充存档：yaml SHA、locked 自检、rev_check r2、validator、最终 HEAD、地盘门。
4. 可选同步澄清 `degrade_rule` 语义：null threshold 不比较，但 `not_measured+meets=false` 仍触发 fail/waiver 链。
5. 不改 4 个 locked 阈值、5 个 null、measured 数字、schema、validator、backend。

---

# 独立复算摘要

- `slo-manifest.yaml` SHA256 = `2ae5225ecd943d23fc8014c51035e444a97f7329f5085a2409f04550798e3006`，与锁档一致。
- schema SHA256 = `4456e1ad629108d618284d6bd5b717f484a712aa8685615e31f940327922c547`，与 `SCHEMA_SHA256` 一致。
- `backend/.venv/bin/python backend/scripts/validate_release_manifest.py --all` → `合计 1 份 manifest, 失败 0 份`，rc=0。
- YAML 结构：metrics 9、measured 4、not_measured 5、locked 4/null 5。
- `d0e8b989` 与 `08cf6bf7` 的所有 metric `measured` 与 `method` 对象完全相同。
- `tree(9c4e7e82:backend)` = `tree(59e1f494:backend)` = `a5cd759a1f2d46737e337b87cefcf577a353c62c`。
- `tree(d0e8b989:backend)` = `78a352945f5d9627c667483fa9e224bdbef216e3`，与勘误档一致。
- `blob(...:scripts/daily_review_pick.py)` 两边同为 `2d6c745ad7468c6e529299da1a2af7d250c0e0aa`。

# UNVERIFIED

- 用户授权原文的完整逐字内容：仓库内 §15 缺失；本轮只能核对请求摘要，不能证明 `decision.note` 是逐字转述。
- 8011 测量窗口同进程/无重启连续性：未重探 Docker；仅核对既有证据与已披露边界。
- r2 legA/legB 的精确临时输入字节：锁档未保存输入 SHA/JSON，只能从映射与输出重建等价输入。
