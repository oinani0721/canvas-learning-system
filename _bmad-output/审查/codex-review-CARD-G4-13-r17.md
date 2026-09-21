# CARD-G4-13 独立复核 — commit `5af89d03`（开发/证据面）

**复核面**：HEAD = `5af89d031ac4a10ccc3e094171a98fe132b04e68`，被核两文件 working tree 与 commit 逐字一致（`git diff HEAD -- …` 空）。方法 = 逐行读码 + 在 `/tmp` 副本上构造反例/突变（S1–S6、E1–E6）+ 在 worktree 只读复跑行为门（**86 passed**，跑前/跑后 `shasum` 比对：仓库文件零改动 `G413-REPO-FILES-UNCHANGED`）。注：任务书标题写 r17，本 commit 的证据面编号是 r18，同一轮，不另计。

---

## 一、逐条裁定

**BLOCKER：未发现**

### HIGH

**H-1｜新增测试①把仓库真 manifest 当写入目标 —— 目标态下会用 `"someone"` 覆盖真签名**
`backend/tests/regression/test_gold_set_manifest_g413.py:1551-1560`（`MANIFEST`= 真仓内路径，`:55`），违反同文件 `:29`「所有写操作都在 `tmp_path` 里」。
一句话复现：把 pending 清零（= 本卡目标态，实测 S6：105→0）→ `approve` 不再被拒 → 测试① 的 `assert rc != 0` 失败，但 `approve_manifest` **已经原子替换**了真 manifest：实测副本 `adjudication={'status':'approved','signed_by':'someone','signed_at':'2026-09-21T00:21:48Z'}`。若用户已先签字，`signed_by`/`signed_at` 被改成 `someone`+当时时间（S2 已证重复 approve 是覆写语义）。CLAUDE.md 规定 hook 编辑后自动跑测试 ⇒ 该写入会自动发生。

**H-2｜UAT §25.3「完整收尾链（现在全部有受控命令）」不成立：shadow 2 条 pending 没有受控回写通道，链条必然在第 3 步被拒**
`backend/scripts/gold_set_manifest_tool.py:703-704`（宣称「四份金集没有任何 pending」）、`:726-741`（扫描范围 = manifest 登记的四份，含 shadow）、`:1217`（checklist 只喂 `MAIN_SETS`）、`:1221`（apply-verdicts 只喂 `MAIN_SETS`）；`vault_gold_set_shadow.yaml` 的 `vq-f06/vq-h07` 为 `user_verdict: pending`；UAT `:847-853`。
一句话复现：照 §25.3 跑完 1+2（主集 103 条全清、`verify` rc=0）→ `approve` 仍 rc=1，报 `vault_gold_set_shadow.yaml: 2`。S1 现场实测输出即 `75 / 28 / 2`（合计 **105**，UAT `:832` 只称 103）⇒ 门比 goal 宽 2 条，而 CLI 无任何命令能回写这 2 条：用户 session 必然卡死，或被迫手改 manifest/yaml——正是本卡要消灭的路径。

### MEDIUM

**M-1｜approve 的 pending 门只覆盖「manifest 登记了什么」，不核对「是否等于四份金集」⇒ 105 条全 pending 下也能签出 verify 全绿的 approved**
`:726`（遍历 `m["files"]`）、`:272-278`（verify_all 只要求 `files` 为**非空** list）、`:662` / `:115-126`（仓相对路径与「未登记即拒」只写在 runner 侧 `rel_to_repo`）。
一句话复现（S3/E4）：把 `files[]` 缩成唯一一份 0 pending 的 shadow（或登记一个**仓外绝对路径**、totals 同步改 0）→ `verify_all` rc=0 → `approve --signed-by impostor` rc=0，105 条 pending 分毫未动。这是 r3 时代 verify 的旧缺口（旧复核已记「空 registry」），但 5af89d03 是工具**第一次自己写出** approved 产物。缓解故不升 HIGH：测试③ `test_gold_set_manifest_g413.py:261-275`（恰 4 条 + 逐份 sha）会抓 registry 缩减，runner 侧对未登记文件拒跑（实测 `(False,"…未登记在 manifest 里")`）——即该不变式只被**测试层**保住。

**M-2｜临时文件写入失败路径异常逃逸：无文案、rc 语义污染、finally 二次异常盖掉原始错因**
`:752-766`。
一句话复现（E5）：把 `<manifest>.approve.tmp` 占成目录 → 真 CLI `approve` exit 1 + traceback，stderr 末行是 finally 里 `tmp.unlink()` 的 `PermissionError`，**原始的 IsADirectoryError 被掩盖**，tmp 残留；原 manifest 未改（这一半正确）。与工具自定口径（`verify_gold_set_file` docstring `:449-467`「环境/输入错一律文案、不以异常逃逸」，r1-H-2 的整改标准）冲突，且 exit 1 与 runner 的「指标回退」档同码。

**M-3｜重复 approve 静默覆写签名（含回溯时间），不留 revision/history 痕迹**
`:743-750`（无条件覆盖 `status/signed_by/signed_at`）对照 `:166-238`（build 才要求 `--bump-revision --reason`）。
一句话复现（S2）：已 approved 后再 `approve --signed-by impostor --at 1999-01-01T00:00:00Z` → rc=0、`verify` 仍 rc=0，`revision` 3→3、`revision_history` 3→3，签名变成 impostor + 回溯 1999。与文件头「改它要留下痕迹」的哲学双标。

### LOW

- **L-1** `--at` 任意字符串照签：`:746` + `:379-382`（verify 只要求非空 str）。实测 `--at "not-a-date"` → rc=0、verify rc=0、`signed_at: not-a-date`。
- **L-2** `--checklist` 任意路径照记：`:747-749`（不校验存在/在仓内）。实测 `checklist_path: does/not/exist.md` → rc=0、verify rc=0。
- **L-3** 4 条新测试判别力：①（`:1551`）现场过但**非自足**（见 H-1），docstring「103 条 pending」与工具实报 105 不符；②（`:1563-1569`）**不判别**——突变删掉空签名守卫 `:709-711` 后仍 rc=1（走的是 pending 分支，S4）；④（`:1632-1670`）**不区分分支**——删掉写前 verify `:717-722` 后由写后复验 `:757-762` 照样「拒 + 原文件不动」（S5），且写后复验分支在门里无独立覆盖；③（`:1572`）是真判别（唯一在 `tmp_path` 正向走通并复验 rc=0）。
- **L-4** 证据面卫生：`evidence-g413/r18-gate-green-20260920T171035.txt` 实为**红**（`1 failed, 85 passed`，`TypeError: approve_manifest() got an unexpected keyword argument 'at'`）却按 `gate-green` 命名（前几轮红跑用 `gate-red-*`），UAT `:839` 用 glob 声称 86 passed；`:844` 的「r17 的 1995」实为 **r16** 的目录级证据（r17 只跑 82 的门）；`:843` 的 `dryrun-fullflow` 在 approve **之前**停，未演示链条第 3 步（而按 H-2 也走不通）。计数本身自洽：`collected 2006 = 1999+6+1`、`86 = 82+4`。

---

## 二、未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下**：registry 缩减或含仓外绝对路径的 manifest（verify rc=0 → approve rc=0，105 pending 全在）· 重复/回溯签名 · `--at` 垃圾值 · `--checklist` 不存在路径 · `.approve.tmp` 被预置（目录/符号链接）· 写路径 OSError（异常逃逸，无 rc=2 文案）· 目标态下测试①自动写出 `signed_by="someone"`。
- **对照输入**：干净副本（105→0 pending）→ approve rc=0 且 `verify` 仍 rc=0、revision 不涨（S2）；行为门独立复跑 **86 passed**；`66485acb` 版与 HEAD 版 `build` 在同一输入 + 冻结时钟下输出**逐字节同（2864 B）**；`MANIFEST_HEADER` 与 66485acb 内联字面量逐字同、现 manifest 以该头开始且 body 往返逐字节同 ⇒ 核对点 2 可复算、`header identical: True` 成立。
- **负控输入**：manifest 缺 → rc=1 有文案；非映射 → verify rc=2 → approve rc=1、原文件逐字节不变；`files: []` → rc=2；sha 篡改 → 拒且原文件不变（写前/写后任一条都能拦，S5）。
- **门未覆盖的路径**：写后复验分支无独立用例 · finally `unlink` 二次异常 · 并发 approve（固定 tmp 名 + 无条件 unlink）· tmp 预置符号链接（`replace` 会把符号链接装成 manifest）· `verify_all` 与 `verify_gold_set_file` 验收面不一致（前者收仓外绝对路径/不完整 registry）· 无 fsync 的崩溃持久性 · 「签名不可伪」本质不存在（`signed_by` 只是自由文本，手改 manifest + verify 绿同样能造 approved）。

---

## 三、核对点裁定

1. **三道前置与原子性 — PASS（含口径缺陷）**：反例逐条复算；同目录 `os.replace` 确原子，失败路径原文件逐字节不变（S1/S4/S5/E2/E5 全 True）；但「四份金集」实为「manifest 登记面」（M-1），写失败不 fail-closed 到 rc=2+文案（M-2）。
2. **header 重构 — PASS**：新旧 build 同输入逐字节同；`header identical: True` 可复算。
3. **新放行/误拒 — PARTIAL**：approve 后 verify 仍 rc=0、status 口径守住、无 pending 时不误拒；但存在 M-1 的新放行面与 H-2 的必然误拒；重复 approve 行为不合理（M-3）。
4. **4 条新测试与计数 — PARTIAL**：③ 真判别、86/1999 自洽且可复现；① 非自足且有仓库写副作用、② 不判别、④ 不区分分支（L-3）。
5. **UAT §二十五 — 有 overclaim**：`:832`「当前 103 pending」与工具实报 105 混用；`:847`「现在全部有受控命令」被 H-2 反驳；`:839/:844` 证据引用有误（L-4）。

**本轮总评：B=0 / H=2 / M=3 / L=4**
