# CARD-G4-13 r18 独立复核 — commit `97c71428`（开发/证据面）

**方法与绑定**：HEAD = `97c71428802e9e2818b1bc2c8f37dbfc7835927b`，被核两文件与 commit 逐字一致。只读静态复算 + 在 `/tmp` 干净副本上独立复算：G413 门（副本 87 passed/2 skipped[git 依赖] + worktree 2 条 git 用例 passed = **89**）、9 组定向变异、真实 103 条副本全链、tmp 失败负控、symlink/class_key 边界。全程仓库内 5 个关键文件 sha 不变（`GIT_STATUS` 仅既有的 r18 空稿/prompt 未跟踪文件）；未连 7691/7687/8011，未跑非 shadow runner，未写任何评审文件。

---

## 一、逐条裁定

**BLOCKER：未发现**

**HIGH：未发现** —— 原 H-1/H-2 均已实测收口：
- H-1：7 条 approve 测试全部走 `_approve_fixture` tmp 根（`test_gold_set_manifest_g413.py:1551-1627`）；在副本上跑完整 G413 门后，副本里真 manifest / 四份金集与仓库逐字节相同。**真 manifest 不再被任何测试路径写入。**
- H-2：pending 门只扫 `MAIN_SETS`（`gold_set_manifest_tool.py:772-787`）。真实 103 条副本上主集清零、shadow 2 条仍 pending 时，`approve` rc=0、`verify` rc=0、shadow 文件与 verdict 均未被改动。**shadow pending 场景真能签成。**

### MEDIUM

**M-4（新）｜签字不随 revision 失效：`build --bump-revision` 继承 `approved`，而 `approve` 又拒重签 ⇒ 新内容无新签字却 verify 全绿 approved（同时是放行与误拒）**
`gold_set_manifest_tool.py:218-223`（`build` 原样保留 `prev_adj`：`"adjudication": prev_adj` 在 `:236`）、`:763-770`（已 approved 一律拒）。
一句话复现（合成 B 与真实 103 条副本 C2 均实测）：pending → `approve` rc=0（signed_at=12:30）→ 改一份金集 yaml → `build --bump-revision --reason …` rc=0，`revision` +1 但 `status` 仍是 `approved`、`signed_at` 仍是旧的 12:30 → `verify` rc=0 → 再 `approve` rc=1（“已 approved”）。即：**新 revision 的内容在没有任何新用户签字的情况下被 verify 全绿地标成 approved，且工具自述的改签路径（`:767`“要改需先走 build --bump-revision”）实际走不通**（build 不会把 adjudication 重置为 pending）。
最小修法：`build_manifest` 升版时把 `adjudication` 重置回 `pending`（可把旧签名/理由记进 `revision_history` 项），新 revision 必须重签；否则 approve 需识别“签名 revision ≠ 当前 revision”并要求重签。若 G4-14 把 `adjudication` 当作与内容绑定消费，本条应升 HIGH。

### LOW

**L-1｜registry 缩水测试不判别（M-1 的回归保护为零）**
`test_gold_set_manifest_g413.py:1698-1715` 用 `main_verdict="pending"`（`:1704`），所以即使删掉 registry 块，pending 门也会拒。
复现：删 `gold_set_manifest_tool.py:753-761` → `pytest -k refuses_when_registry_shrinks` **1 passed**，整个 approve 套件 **7 passed**；把 fixture 改成 `main_verdict="relevant"` 后，同一突变体返回 rc=0 并写出 approved（= 该修法才判别）。建议同时断言 stderr 含“registry 完整性”。

**L-2｜空签名测试仍不判别（UAT §26.1 L-3②“真判别”未达成）**
`test:1656-1666`；删掉 `tool:723-725` 的空签名守卫后，该测试仍 **1 passed** —— 写后复验（`tool:808-813`：approved 但签名缺失 ⇒ rc=1）把断言“兜住”了：rc≠0、原文件不动、status=pending 全部照样成立。要判别须断言 stderr 含“--signed-by 不能为空”，或证明未创建 tmp / 未进入写入路径。

**L-3｜approve 的 verify 门无任何判别用例；旧 ④ 实际被删，UAT §26.1 L-3④“保留”不实**
pre-write 门 `tool:742-747`、post-write 门 `tool:808-813`。定向变异显示：**任删其一，approve 7 条测试全绿**（M7/M8）。旧 `test_approve_refuses_when_manifest_inconsistent`（`5af89d03:1632-1670`，r17 指出的不区分分支者）在新文件里已不存在，且无等价的“verify 红 ⇒ 拒签”用例；正向测试 `:1669-1682` 只验终态合法，不证明“先验后换”真的执行。

**L-4｜`--at` 合法面不过窄，但过宽且有损**
`tool:694-702` 实测接受：`"2026-09-20"`（date-only）、`"20260920"`（basic）、`"2026-09-20T12"`（partial hour）、`"2026-09-20 12:00:00"`（空格分隔）；`.987654` 被静默截成整秒；naive 时间被默默当作 UTC。`verify_all` 只要求非空 str（`tool:375-382`），不会复核 `signed_at` 形态。建议要求完整时间戳（或保留微秒/显式拒绝亚秒），并在 docstring 说明 naive=UTC。

**L-5｜证据/UAT 卫生仍有 residual overclaim（L-4 未全收口）**
- `evidence-g413/r19-*` 无 HEAD/SHA 绑定（`r19-shas-*` 只列四份金集；无 commit 行）。我的重跑绑定 `97c71428`：副本 87 passed + worktree git 用例 2 passed = 89，与 `r19-gate-green-…172517` 的 89 一致。
- `r19-dryrun-fullflow-20260920T172547.txt` 停在 build/verify（末行 `adjudication: pending`），**没有跑 approve**；即 UAT §26.3 第 3 步“approve 现在真能走通”未被该“全链路”证据覆盖（我独立补跑：103→approve rc=0、verify rc=0，结论为真，但证据标签 overclaim）。
- `r18-gate-green-…171035.txt`（1 failed/85 passed，`TypeError` 中间态）仍以 `gate-green` 命名提交；虽已内文注明，glob 仍会命中红跑。UAT:877 称 ②/④ 已收口，与上面 L-1/L-2/L-3 的变异结果不符。UAT §26.1 写“r19/r20 前缀”，实际无 r20 证据。

---

## 二、未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下**：① 已 approved 后的 revision bump（M-4，旧签字随新内容继续 verify 绿）。② `class_key` 元数据篡改：把 `files[0].class_key` 从 `query_type` 改成 `category`（attack totals 已是 0）→ `verify_all` rc=0、`approve` rc=0、status=approved（实测）。原因是 `verify_all` 用 manifest 自己的 `class_key` 重算 attack（`tool:349-359`），属自证；registry 完整性只比 `path`（`tool:753-754`），不锁 class_key/计数。③ 预置 `.approve.tmp` 符号链接：`approve` rc=0，manifest 路径本身变成指向仓外目标文件的 symlink，`verify` 仍 rc=0（实测；r17 已列“门未覆盖”，M-2 只兜 OSError，不防 symlink 跟随）。④ `--checklist` 只查存在、内容与 verdict 无绑定；相对路径按调用时 cwd 原样记录，换个 cwd 可能不可解析。⑤ `verify_all` 与 `load_yaml` 之间的 TOCTOU（`tool:742,749`）可让并发改写以未捕获 YAML/OSError 收场；固定 tmp 名亦可并发互踩。⑥ `signed_by` 仍是自由文本，手改 manifest + verify 绿同样能造 approved（r17 已记，未变）。
- **对照输入**：干净 103 条副本全链 PASS —— `checklist n=103` → `changed=103 / problems=[]` → shadow 两份逐字节未动 → `build` rc=0（revision=3，adjudication 仍 pending）→ `approve` rc=0（status=approved, signed_by=user, checklist 记录）→ `verify` rc=0。registry 缩水（主集 relevant）对照：现行工具 rc=1 且报“registry 完整性”；删掉该块的突变体 rc=0 并写出 approved ⇒ 该块是承重的。
- **负控输入**：把 `<manifest>.approve.tmp` 预置成目录 → rc=1、stderr 有“临时文件写不动”、无 traceback、原文件逐字节不变、目录保留。重复签署（同 revision）→ rc=1、字节不变、signed_by 保持 `user`。坏 `--at` / 不存在的 `--checklist` → rc=1、字节不变。verify 红的 manifest → 写后复验以“新内容 verify 不为 0”拒绝（见 L-2/L-3 变异）。
- **门未覆盖的路径**：`rel_to_repo` 为 None 时 registry 的 `want_paths` 在 `tool:753` 被静默过滤（生产不可达：四份金集都由 `Path(__file__).resolve()` 派生，必在仓内；但失败形态是误导性的“registry 不一致”而非明确的“金集在仓外”）；pending 循环对 None 回退 `str(path)`（`:774`）。其余：并发/固定 tmp 名、symlink、无 fsync 崩溃持久性、`verify_gold_set_file` runner 侧仍只验“目标文件已登记”（registry 完整性只在 approve 侧加固）、checklist 语义与 `signed_by` 可信度。

---

## 三、核对点裁定

1. **r17 逐条复算**：H-1 PASS（tmp 隔离 + 全门跑后真 manifest 字节不变）；H-2 PASS（只扫 MAIN_SETS；103 条 = 75+28，manifest `main_set_queries=103`，checklist n=103，shadow 2+0 声明在用户 session 面外）；M-1 行为 PASS / 测试 FAIL（缩水与仓外/mismatch 被拒，但测试不判别，L-1）；M-2 行为 PASS / 无测试（负控为文案 + rc1、无 traceback）；M-3 PASS（同 revision 重复签署真拒），但其“build 升版改签”路径实际不通（M-4）；L-1 PASS（坏值拒，但合法面过宽，L-4）；L-2 PASS（存在性校验生效，positive path 也实测通过）。
2. **新放行/误拒/崩溃**：新放行 + 新误拒 = M-4（approval 不随 revision 失效 + 无法重签）；CLI 面未发现新崩溃；残余崩溃面为 `signed_at`/`checklist` 非 str 的直接 API 调用（AttributeError/RepresenterError）与 verify→load 的 TOCTOU。`MAIN_SETS` 与 goal 103 一致；`finally` unlink 与 `tmp.replace` 后 tmp 不存在均实测正常。
3. **端到端**：真实 103 条干净副本 勾选→apply-verdicts→build→approve→verify 第一轮全链 PASS（我独立复算）；第二次 revision 周期被 M-4 卡死。r19 证据本身未演示 approve 步骤。
4. **gate 89 / 目录级 2002 自洽**：89 = 82 + 7（副本 87 + git 依赖 2），approve 7 passed；目录级 `2002 passed / 6 skipped / 1 xfailed`，collected 2009 = 2002+6+1，相对 r17 的 1999/2006 恰 +3（approve 测试 4→7），计数自洽（我未重跑 5m41s 目录级，仅核证据与计数）。7 条 approve 测试判别力：5 条能杀对应变异（主集 pending、shadow pending、重复签署、坏 --at、缺 checklist），2 条不能（空签名 L-2、registry 缩水 L-1）；两条 verify 门完全无判别用例（L-3）。
5. **UAT §二十六 overclaim**：H-1/H-2/M-1/M-2/L-1/L-2 的功能收口基本属实；但 §26.1 L-3 行对 ②/④ 的“收口”与变异结果不符（L-2/L-3）；§26.2 dryrun 行称“全链路”但未含 approve；§26.3“approve 现在真能走通”只对首个 pending→approved 周期成立，重签周期被 M-4 证伪；证据未绑 HEAD/SHA。§26.4 的三条“未证明”是诚实且准确的。

**本轮总评：B=0 / H=0 / M=1 / L=5**
