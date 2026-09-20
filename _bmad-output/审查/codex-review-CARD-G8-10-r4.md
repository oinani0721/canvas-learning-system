> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p6-skills-w · 卡 CARD-G8-10 round-4
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r4.md)" > _bmad-output/审查/codex-review-CARD-G8-10-r4.md 2> _bmad-output/审查/codex-review-CARD-G8-10-r4.stderr </dev/null`（rc=0；2026-09-20 01:56:47 → 2026-09-20 02:11:29 -0700）
> 审查绑定: `4120e0b6`（各轮时点绑定；amend 血缘与终态见验收单 §八/§九.6）
> 会话头自证（行号按 .stderr 原文）: 第 2 行 `OpenAI Codex v0.153.3` / 第 5 行 `model: glm-5.3` / 第 9 行 `reasoning effort: max`

---

只读审查完成：未改动任何文件、未连接数据库、未访问网络服务。审查结论绑定用户指定的底账终态 **`4120e0b65668250e2582d994daebfa34e8a34e28`**；底账 sha256 复核为 **`cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`**，脚本 sha256 为 **`d37e2da5a2be4fb79697c0b1e0ec0215a22259135de831517a63b63f84e95ace`**。

> 现场注意：审查过程中车道 HEAD 被外部推进到 `c53069d3`；该 commit 仅新增 unrelated 的 `evidence-harness-tree-r2/jev-triage-HARNESS-43bea775.json`。我没有改工作区。以下仍按本轮指定的 `4120e0b6` 审查。

## BLOCKER

无。

## HIGH

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:273-288`；底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:265`** — 脚本声明“记录出现 `outcome=pass` 一律红”，但实现只检查第一条 `dim: observability` YAML 行的 outcome，不扫描 §2.13 全部记录、附加表或后续 YAML 重复行。  
  显形：**未被拦下的输入**——保留真实 summary/YAML 为 `not_yet`，在 §2.13 后追加一条含 `outcome=pass` 的附加记录或第二条 observability YAML，并按新底账重锚 `--expect-digest`，脚本不会输出 `pass-unsupported`。

- **HIGH — `_bmad-output/审查/evidence-g810/check_g810_refs.py:34` / `:217-246`** — owner 检查只是 `_ID_RE.findall()` 后比较集合，非 ID grammar 的文本会被静默丢弃，因此“非空 + 仅 ID grammar + 允许集”并没有覆盖“伪 owner 与合法 owner 并存”的记录。  
  显形：**未被拦下的输入**——把检索链 owner cell 改成 `张三 / G4-3（总账 v2 …:500）` 并重锚 digest，提取集仍是 `{G4-3}`，脚本仍绿；现有 bypassD 只测纯 `张三` / 空，未测混合形态。

- **HIGH — 底账 `_bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md:266`；`_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:4-7` / `:107-118`；脚本 `_bmad-output/审查/evidence-g810/check_g810_refs.py:1`** — r4 终态的自指登记和“commit ② 登记脚本 sha256”当前并未发生：`4120e0b6` 树中没有脚本、证据包或更新后的 UAT，未跟踪 UAT 仍绑定 r3 的 `6624a1b4` 且脚本 SHA 是 `PENDING_SCRIPT_SHA`。  
  显形：**门未覆盖的路径**——`git ls-tree -r --name-only 4120e0b6 _bmad-output/审查/evidence-g810` 为空，`git status` 显示脚本/UAT/证据仍未跟踪；因此 r4 当前只能说“承诺后续 commit ②”，不能说登记已如实完成。

## MEDIUM

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:151-173`** — nodeid 语法没有要求非空测试名，`backend/tests/<real>.py::` 会生成空 name，而空 name 的 `(def|class) \b` 检查可命中文件中任意函数或类。  
  显形：**未被拦下的输入**——把某行机械判据改成任一真实 `backend/tests/` 文件路径加尾随 `::`，重锚 digest 后仍满足“.py:: 存在”和静态 def/class 检查，不产生 `nodeid-missing`。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:29-32` / `:105-114` / `:133-139`** —引用路径没有限制必须留在 `--root` 内、必须是 tracked 文件或生产源文件，绝对路径会被 `Path` joining 保留，`../` 也可逃出树根。  
  显形：**未被拦下的输入**——构造 `../fake-g810.py:1` 或 `/tmp/fake-g810.py:1`，让该文件包含同一句 ≥24 字文句并重锚 digest，quote/ref 检查仍可绿。

- **MEDIUM — `_bmad-output/审查/evidence-g810/check_g810_refs.py:295-303`** — `source_digest` 只保留 16 hex（64 bit），输出 HEAD 只保留 8 hex（32 bit），且脚本不校验工作区 clean / referenced path tracked / index blob 与 HEAD 一致，档案行自身也不是充分自证。  
  显形：**对照输入**——在同一 HEAD 下用未 tracked 或 modified 的引用源满足文句并重算 expect，脚本仍可绿；这说明它适合漂移检测和人工复核锚，不是独立密码学闭合证据。

## LOW

无。

## 逐项独立核对结论

### ⓪ 六链“判据文句”假归属独立核对

**当前底账六链本身未发现假归属；六条判定文本均逐字命中其标注源行。**

| 链 | 独立核对结果 |
|---|---|
| 检索链 | `ServiceStatus.UNAVAILABLE must carry an empty items payload` 逐字命中 `backend/app/models/service_status.py:108`；`G4-3` 在总账 v2 `:500` 有档案节，行内同时保留 G4-2 provenance，未把 G4-2 文句冒充 G4-3 交付。 |
| 复习链 | `review_overview.py:1044` 与 `:2463` 两句逐字命中；`review_app.py:582-592` 确为用户可见 503/失败渲染，`test_review_overview.py:3248` 与 `test_review_app.py:2674` 均存在。 |
| 部署链 | `每阶段一行 stage=… rc=… …` 判据逐字命中 `scripts/deploy-vault.sh:3079`；`:12` 与 `:3129` 露出面也存在。 |
| skill 链 | `inbox_preview.py` 实际 2479 行，`degraded|unavailable` 命中数为 0；底账没有伪造 quote，而是登记“露出=无”并挂缺口。 |
| 投影 freshness | `mapped = {"ok": OK, …}[status]` 逐字命中 `backend/scripts/vault_lint.py:887`；底账如实说明卡文旧行号 `:872/:882/:901` 漂移到现值 `:877/:887/:906`。 |
| DLQ 链 | `traces.py:405-406` 两句逐字命中；父提交无、`b8c6e4922` 有，`git log -S` 也指向 `b8c6e4922`，r3-L1 补记属实。 |

“已合入主干”一词需要限定：这些文本在本地集成车道 / `batch14/integ2` / `worktree-feature-obsidian-hybrid-dev` ref 可见，但不在本地 Git `main` / `origin/main`。底账自己在 DLQ 行标明“本车道 P6-C，未合主干”，所以底账没有冒充；若作者自述把“主干”理解为 Git `main`，该措辞不准确。

### ① r3 两条 HIGH 的处置

- **r3-H1 主路径已按新边界处置**：canonical summary/YAML 双改 `pass` 会红，`g810-bypassA-v42` 确实出现 `pass-unsupported`；脚本不再声称 candidate-SHA 可自证 pass。  
  但“任何 pass 记录一律红”的实现范围小于声明，见 HIGH-1。
- **r3-H2 主路径已处置**：空 owner、纯非 ID owner、有效但错误归属 ID 分别由 bypassD/B/C 变红；六链和 OBJ-07 的允许集硬编码且当前与 v2 档案节一致。  
  但混合伪 owner 仍可被忽略，见 HIGH-2。
- SHA 检查现在要求本地 Git object 类型为 commit，且不再承担 pass/candidate 认证；这与声明边界相符。

### ② 定位为“一致性核对”后，是否还有声称与实际不符

有。核心残面是：

1. pass 扫描范围小于“任何记录”声明；
2. owner 语法检查小于“仅 ID grammar”声明；
3. nodeid 语法接受空节点名；
4. 引用源没有 repo/tracked 边界；
5. digest 是强人工复核锚，但不是独立档案自证。

语义级故障露出、测试真实执行、记录诚实性本来就不在本脚本声称范围内，这些不另降分。

### ③ 底账内容是否如实

- `r4 = 4120e0b6` 的底账 SHA 与用户给定值一致。
- `7538275c → 3f32e861 → 6624a1b4 → 4120e0b6` 四个对象的 parent 均为 `cb21f1fe`，author time 相同、committer time 递增，符合 amend 血缘描述。
- `cb21f1fe..4120e0b6` 仅底账一个 tracked 文件变更，符合零代码卡声明。
- `6624a1b4..4120e0b6` 只有两处实质变化：DLQ 行补 `b8c6e4922` provenance，以及 §5 说明 pass 认证边界；前者属实，后者实现覆盖面见 HIGH-1。
- 六链 + OBJ-07 五项、`not_yet/partial`、两项缺口、skill 0 命中、检索 UI 半边未普查，均与当前文件和 Git 对象相符。
- 但 r4 自指 UAT / commit ② 登记当前未完成，见 HIGH-3。

### ④ digest / expect / head 回显是否足以支撑终态重跑档案

- 在不改动工作区的情况下，我把脚本读到的 HEAD 值按 `4120e0b6` 复算，得到 `source_digest=638713e44b9047dc`，与 `g810-green-v42-*.txt` 一致；这证明存档与 `4120` 的底账、引用源、nodeid 文件、脚本字节和 HEAD 组合相容。
- 五个 bypass 存档均出现指定红项；三段负控存档均有 before/after ledger sha 相同、mutation 指定红项、恢复后 rc=0 的文字。
- 但档案行本身没有命令、脚本 SHA、ledger SHA、clean-tree/full HEAD 输出，且 digest 截断为 64 bit；因此它足以支持复核和漂移检测，不足以单独作为密码学自证。commit ② 必须实际入库脚本和证据后，Git 对象才能提供外层绑定。
- 当前 live HEAD 已被 unrelated `c53069d3` 推进；原地重跑 v4.2 会因 HEAD 变化得到 `digest-drift`（actual `0f01ba49deeb5520`），这不是卡内回归，而是 digest 绑定 HEAD 的预期表现。若在 `c53069d3` 之后收口，需要重新锚定或明确以 `4120e0b6` checkout 复跑。

### ⑤ 其它重要结论

- `collect-final-batch` 覆盖 9 组 nodeid，`collect-reviewapp` 补第 10 组，均为 ≥1 collected；`vault-lint` open/close 均 112 passed；unit open/close 均为既有 rc=1 失败集，close 多 1 个失败，不能用来宣称全量测试改善。
- `jev-triage-7538275c.json` 绑定 r1 SHA 且 `files=[]`，与零代码描述一致，但它不能证明 r4 终态。
- 当前工作区仍有整包 G8-10 审查/证据/UAT 未跟踪；在 commit ② 实际完成前，不能以当前 Git 终态宣称档案链闭合。
