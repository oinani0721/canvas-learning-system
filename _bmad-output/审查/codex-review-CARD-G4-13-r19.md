# CARD-G4-13 r19 独立复核 — commit `c6782824`（开发/证据面）

**方法与绑定**：HEAD = `c6782824f2e2797929a06cc64822c82a00f02f70`（与复核对象逐字一致）。仓库内只读；独立复算在 `/tmp/g413-r19-review-20260920T175624/` 副本上做（r18/r22 两版工具 + 同 fixture；真 103 条内容副本；行为门与变异）。全程仓库 7 个关键文件 sha 不变（`REPO KEY FILES UNCHANGED`，git status 仅既有 r19 空稿/prompt 未跟踪）；未连 7691/7687/8011，未跑非 shadow runner。真 manifest `verify` rc=0、四 sha 与 `r21-shas` 逐字同（我重算）。

---

## 一、逐条裁定

**BLOCKER：未发现**
**HIGH：未发现**
**MEDIUM：未发现**

### LOW

**L-1｜生命周期测试不判别「保留 checklist_path」子声明（§27.1 的第二个卖点无钉子）**
`test_gold_set_manifest_g413.py:1730-1756`（approve 未带 `--checklist`，fixture 的 `checklist_path=None`；断言只查 status/signed_by/history.signed_by），实现 `gold_set_manifest_tool.py:233`。
一句话复现：把 `:233` 的 `(_old or {}).get("checklist_path")` 换成 `None` → `pytest -k test_build_bump_resets_signature_and_forces_resign` 仍 **1 passed**（我实跑 M-C）。行为本身我已验真：带真 checklist approve → bump 后 `pending.checklist_path` 保留 ✓——缺的只是测试判别力。

**L-2｜升版保留的 checklist_path 会被重签带入新 revision 的 approved 记录，无任何新鲜度校验**
`tool:224-234`（保留）+ `tool:807-813`（重签未带 `--checklist` 时 `setdefault` 保留旧值）。
一句话复现（我实跑 S5，双源同 fixture）：`approve --checklist cl.md` → 改内容 → `bump` → pending 的 checklist_path=cl.md → 重签（不带 --checklist）rc=0，最终 approved 仍指旧内容的 cl.md。修复前该状态只能手改达到，修复后成为正常流程中间态；approve 不要求/不校验清单与 revision 对应（r18 L-4 残余在此放大）。

**L-3｜bump 会把畸形（非映射）adjudication 静默洗回 pending：旧版保留畸形值（verify 红），新版无声变绿**
`tool:224-234`（`_old` 只做 isinstance 判别即重置，不记录、不告警；`:216` 无条件置位）。
一句话复现（我实跑 S4 双源对照）：把 manifest 的 adjudication 写成裸字符串 `approved` → **旧源**：pre-verify=1 → build rc=0 → 仍 `approved`、post-verify=1；**新源**：build rc=0 → 干净 pending、post-verify=0。非放行（仍需重签），但「manifest 曾被写坏」的信号被静默清除且 history 无记录。

**L-4｜§27.3 的「按 §22.3/§26.4 登记」未落地：本 commit 对 UAT 只追加 §27，两节无 r18 五项残余的处置记录**
`UAT:934`（声明）vs `UAT:766-781`（§22.3 仍是 r15 口径）/ `UAT:898-903`（§26.4 三条）。
一句话复现：`git show --stat c6782824`（UAT 仅 +32 行 = §27 追加）；在 UAT 里 grep 上一轮残余（registry 缩水测试/空签名测试/approve verify 门/`--at`/证据绑定）无任何条目。L-5 类证据问题本轮复发（见下）——按该句自己的口径也属「与本段有交集」，本应处置而非仅登记。

**L-5｜r21 证据卫生：无 reviewed-HEAD 绑定；`fullflow` 仍不含 approve；gate 用 `r20-` 前缀而其余用 `r21-`**
`evidence-g413/r21-shas-*.txt:1-4`（仅四份金集）；`r21-dryrun-fullflow-*.txt:1-10`（止于 build/verify）；`r20-gate-green-*` vs `r21-*`。
一句话复现：`grep -nE "[0-9a-f]{40}|HEAD" r20-*.txt r21-*.txt` 只命中金集 sha；dryrun 副本主集仍 101/103 pending，本就无法走到 approve。UAT §27.2 的行描述与文件内容一致（overclaim 限于「全链路/fullflow」命名与绑定缺口，属 r18 L-5 复发；`r18-gate-green-…171035` 红跑也仍在该命名下）。

---

## 二、核对点裁定

1. **M-4 复算（同 fixture 双源对照，PASS）**：合成 fixture 与真 103 条内容副本上——r18 源：approved(12:30) → 改内容 → bump → **仍 approved/12:30、verify rc=0、重签 rc=1**（放行+误拒原样复现）；r22 源：同步骤 → **pending**、`history[-1].prev_adjudication` 整块（status/signed_by/signed_at/checklist_path）留痕、verify rc=0、重签 rc=0（13:30）。留痕完整（`dict(old_adj)` 整块复制）；`checklist_path` 保留 ✓（S5）；fixture 本就无 `revision_history`，legacy manifest 追加正常（`tool:204-216`）。
2. **新问题**：首次 build 双源输出逐字同（revision=1/pending/无 history/verify 0）；未签 bump 等价 pending、无副作用、approve 仍可签（S3）；history 不被 verify 读取，全仓 grep `adjudication` 仅出现于工具与门测试（**无下游消费者，无误读面**）；bump 后 pending verify rc=0 ✓。新增两个 LOW 级行为面 = L-2/L-3。
3. **放行/误拒/崩溃**：无新放行（唯一状态变化是把畸形值收紧为 pending）；无新误拒（原 M-4「无法重签」已消除，approve 新增拒绝面为零）；无新崩溃（新代码仅 isinstance 判别+dict 复制；第二次 load 的异常面与修复前相同）。四真金集仍 T：真 verify rc=0、gate 90/90、双源 103 副本全绿。
4. **gate 90 / 目录级 2003 自洽**：gate 90 = 89 + 1（文件 41 个 test 函数经 6 处 parametrize 展开；我实跑 worktree 90 passed，副本 88 passed+2 skipped[git]）；目录级 collected 2010 = 2003+6+1，相对 r18 基线 2009 恰 +1。**生命周期测试判别力**：M-A（换 r18 工具）FAILED、M-B（删 prev_adjudication 写入）FAILED ⇒ 真判别；M-C（删 checklist 保留）PASSED ⇒ 判别力缺口（L-1）。
5. **UAT §27 诚实性**：§27.1/§27.2 行为描述与实测一致（除「保留 checklist_path」无测试钉子）；§27.3 登记说法未落地（L-4）。§22.3（LOW-4/L-5/vault_id/上界/证据重放/nan-inf 已处置）与 §26.4（用户裁定未证明、shadow 处置登记、下一轮复核待跑）的既有条目本身仍诚实、与现状无冲突，但都未记录 r18 五项残余。

---

## 三、未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

**未被拦下**：① 畸形 adjudication 经 bump 静默归一（L-3）；② pending 携带的旧 checklist_path 流入新 approved（L-2）；③ 手改 manifest 的 `revision_history/prev_adjudication`（删/改）→ verify 完全不读 history，rc 仍 0（留痕不具可检篡改性，与「signed_by 自由文本」同级既有残余）；④ 窄并发窗口：build 两次 load 之间被外部 approve，该签字会被重置且不留痕（旧版反而保留；未构造实跑）。

**对照输入**：无 manifest 首次 build（双源同）；未签就 bump（pending→pending、无 prev_adjudication、verify 0、approve 可签）；干净真 103 内容副本 `build→approve→verify` rc=0，改内容后 sweep 到 `pending+留痕+verify 0+重签 rc=0`——同一 fixture 的 r18 版本在最后两步以 `verify=0, reapprove=1` 收场（M-4 关键负控）。

**负控输入**：换 r18 工具跑新测试 FAILED；删 prev_adjudication 写入 FAILED；删 checklist 保留 PASSED（缺口）。真 103 副本 step2 双源对照如上。

**门未覆盖的路径**：`revision_history` 无结构校验、`prev_adjudication` 无消费者也无析取语义（「revision N 的签字」藏在 N+1 的条目里，靠 `entry.revision-1` 约定）；checklist 与内容/ revision 无绑定；build 不先 verify 旧 manifest（S4 由此进入）；既有并发/`.approve.tmp`/symlink 等 r18 已登记项未变化，不重复计。

---

**本轮总评：B=0 / H=0 / M=0 / L=5**

（M-4 修复本身在双源同 fixture 上实测收口、无回归；剩余 5 条 LOW = 测试判别力 1、行为残余 2、UAT 登记 1、证据卫生 1。）


