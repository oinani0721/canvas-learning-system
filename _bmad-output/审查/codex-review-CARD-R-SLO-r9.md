# r9 复核结论

**绑定核验：通过。**

- 当前 `HEAD = 90b8db846a6bf69c948a61ec9d501cd2932e14fa`，父提交确为 `f27531a9be438350360cfbf40160f588380be5c3`。
- `08cf6bf7` 是 `90b8db84` 祖先。
- `f27531a9..90b8db84` 只触达 `_bmad-output` 与 `docs/release-evidence/README.md`；无 `.py`、schema、validator、J08 示例件改动。
- 工作树 tracked 面干净；另有 4 个未跟踪 r9 prompt/review/evidence 文件，不属于被审 `90b8db84`。
- 本轮未改任何文件。

## 最终分级

**0 BLOCKER / 0 HIGH / 0 MEDIUM / 0 LOW**

---

## 作者自述逐条核验

| # | 结论 | 核验 |
|---|---|---|
| A1 HIGH-1 | **成立（仓库证据面）** | `UAT §15` 现已真实存在：`UAT:315-326`。其中含补录原因/首版脚本写错变量说明、 purported verbatim 授权原文、①-⑨ 对照、code_sha 裁定、yaml 变更、r2 腿结果、r8 六项处置清单。UAT 顶部、§10、§11、§12、§14 与锁版存档中的 `§15` 指针均能落到该节；`slo-lock-20260920T140356.txt:2` 的指针也可解。 |
| A2 HIGH-2 | **成立** | 指定活动面已更新：`UAT:14` 为 r2/locked 事实；`UAT:235-248` 条目 1/4/12 不再称未锁版或 `code_sha=null`；`UAT:252-260` 条目 1/2/7 改为已授权、r2 可供 E3+ 引用；`UAT:293-295` 将 §14 明确标为 `as-of d0e8b989` 且已被 r2 superseded。 |
| A3 MEDIUM-1 | **成立** | 勘误档 `slo-lock-20260920T140356-erratum-degrade-rule-20260920T141118.txt:1-5` 明确：`locked=null` 只是没有阈值比较依据，不得读作可忽略；导出为 `(未定)+not_measured+meets=false` 后仍进 S9 fail/waiver 链。locked yaml 文案未被静默修改。 |
| A4 LOW-1 | **成立** | `README.md:197` 已补单文件版本化例外：旧 revision 正文由 git 历史保留，`superseded_by` 语义由 revision 链 + `decision.note` + git 历史承载。`8e36c412` 确认可取回 r1/draft yaml。 |
| A5 LOW-2 | **成立** | `UAT:6` 现已计入 `08cf6bf7`、`f27531a9` 与本 r8 整改 commit。独立计数：`a03f0ce3..08cf6bf7=16`，`..f27531a9=17`，`..90b8db84=18`，与顶部叙述相符。 |
| A6 LOW-3 | **成立** | legA/legB JSON 已落档；独立 `sha256` 复算逐字匹配索引档：legA `27dbdd55…fe709`，legB `68129a48…a1f9`。两文件 `slo` 对象完全相同，均引用 r2、9 项测量；legA `result=partial`，legB `result=fail`。 |
| A7 无回归 | **成立** | `git diff 08cf6bf7..90b8db84 -- docs/release-evidence/slo-manifest.yaml` 为空；两处 blob 均为 `f7eb13e101cb1819cfa8919954dc2a7a130d635a`。当前 yaml SHA256 仍为锁档值 `2ae5225ecd943d23fc8014c51035e444a97f7329f5085a2409f04550798e3006`。结构复算：9 metrics / 4 measured / 5 not_measured / 4 locked / 5 null，revision r2、status locked。validator `--all` 当前仍为 `合计 1 份 manifest, 失败 0 份`，rc=0。 |

---

## 独立复跑与对象核对

- `git diff --stat f27531a9..90b8db84`：8 files，`287 insertions / 14 deletions`；仅 r8 review/prompt、勘误与腿输入、UAT、README。
- README 本 commit 增量为 `+1/-1`；但累计 `a03f0ce3..90b8db84 -- docs/release-evidence` 仍为：
  - `README.md +13/0`
  - `slo-manifest.yaml +269/0`
- 当前 yaml 与 `08cf6bf7` 的 blob 完全一致，未发生 r8 后漂移。
- `d0e8b989` draft 与 `08cf6bf7` locked 比较：metric id、9 个 `measured` 对象、9 个 `method` 对象均相同；locked 结构仍为 4/5。
- 直接用 validator 校验已归档 leg JSON 时，因裸文件不在 `<rc>/journeys/J08/` 结构下额外出现 2 个 S6 路径错误；但相关 S9 语义完全复现：legA 为 5 条 not_measured S9，legB 为 0 条 S9。这与 `slo-lock-20260920T140356.txt:22-29` 的消费腿结论一致。

---

## r9 焦点逐项回答

### ⓪ r8 六项是否全部闭环、是否有新矛盾

**六项全部闭环；在被审活动面未发现新矛盾。**

- HIGH-1 → `UAT §15` 补录并使既有指针可解。
- HIGH-2 → 指定当前摘要/未证明事项/台账/§14 均改为锁版后事实或明确 as-of。
- MEDIUM-1 →勘误档澄清 S9 fail/waiver 语义。
- LOW-1 → README 单文件版本化例外成立。
- LOW-2 →顶部 commit 计数补齐。
- LOW-3 → legA/legB 字节输入与 SHA 已落档。

§15 与 yaml `decision.note` 的核心裁定一致：4 项 locked 阈值、5 项 null、code_sha 候选值、owner 分派、统计口径均相符。

### ① §15 授权原文 / ①-⑨ 对照是否与 yaml 相符

**相符。**

- ① first_paint：`≤500ms` locked
- ② warm：`≤5000ms` locked
- ③ cold：null / not_measured / G4-14
- ④ kg_read：`≤500ms` locked
- ⑤ rebuild：`≤30s` locked
- ⑥ first_index：null / G2-10
- ⑦ graphiti_ack：null / G4-14/7692
- ⑧ graphiti_replay：null / R-J10
- ⑨ recovery_time：null / R-J10

code_sha 均为 `9c4e7e82f2c80ab45a7eb4facfc95c1e6dadb680`。

### ② README 例外句是否消解 LOW-1

**消解。**`README.md:197` 不再要求单文件模式下物理保留旧正文；它明确旧 revision 由 git 历史承载，并说明 `superseded_by` 在该模式下的语义实现。与当前 yaml `r2 取代 r1` 的 note 不冲突。

### ③ 勘误档是否足以消除 MEDIUM-1

**足以闭环。**勘误档明确禁止把“不计判据”读成“可忽略 / 静默 pass”，并给出正确链路：`threshold=(未定)`、`measured=not_measured`、`meets=false` 仍触发 S9 的整体 fail 或用户 waiver 要求。该口径也与 yaml `export_shape/consumption_note` 和 legA/legB 实证一致。

孤立只读 9 条 `degrade_rule` 字面仍可能误读，但 locked 对象不被静默修改是正确约束；相邻 export/consumption 口径、README 已知边界与勘误档已形成可审计解释链。

### ④ 若仍发现 HIGH 的最小后续补证

**无 HIGH，无需后续补证。**

---

## UNVERIFIED

- §15 所称“用户授权原文逐字”的外部对话来源无法仅凭仓库对象自证；本轮只能核对它与 yaml `decision.note`、请求中的裁定摘要及锁版存档一致。
- 未重探 8011/Docker 运行时连续性；该边界已由 `code_sha_basis` 和 UAT 明示为“同进程连续性未证”，且不属于本轮整改对象。
