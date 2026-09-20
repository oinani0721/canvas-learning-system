BLOCKER: 无 / HIGH: 无

## MEDIUM

1. `_bmad-output/审查/evidence-g810/g810-r11-artifact-audit.zsh:21-23` — 产物审计声称覆盖「UAT 引用的 evidence-g810 产物名」，但实现先施加一组未在 UAT §十.358-360 声明的前缀白名单，导致不带这些前缀的 evidence-g810 引用名被静默排除；当前 `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:375` 引用的 `check_g810_refs.py` 就不在审计结果里，且 UAT:360 仍写 32 条、post 审计实为 42 条。  
   **门未覆盖的路径**：让目标 REF 缺失一个被 UAT 引用但不带 `g810-` / `sidecar-` / `jev-triage-` 等前缀的 evidence-g810 文件（例如 `manifest-r11.json`，或目标 REF 中缺失 `check_g810_refs.py`），该文件不会进入 `names`，审计仍可 `rc=0 / missing=0`。

2. `_bmad-output/审查/evidence-g810/g810-r11-artifact-audit.zsh:15-21` — 审计对象 REF 是参数化 git tree，但名字来源总是当前工作区 UAT，而不是 `REF:<UAT>`，也没有记录 UAT blob/hash 或 clean 状态，因此“对某个 REF 审计”的名字面可被后来或临时的 UAT 文本改变。  
   **负控输入**：在工作区 UAT 中删掉一个实际缺失 artifact 的反引号文件名后运行，审计会因名字面缩窄而 `rc=0`；我未改动文件，仅用已提交对象复核——按 `74d58d14:UAT` + `74d58d14` 得到历史口径 32 条/仅缺 r9 sidecar，但用当前 `1db667ba:UAT` + `74d58d14` 会得到 42 条/11 缺，证明该脚本的两个输入没有绑定在同一 REF 上。

## LOW

1. `_bmad-output/审查/evidence-g810/g810-r11-green.zsh:3` 与 `_bmad-output/审查/evidence-g810/g810-r11-green.zsh:16` — r11 runner 注释仍写默认 `ca597bbf` / r8，实际默认已是 `74d58d14` / r10；UAT `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:289` 还把修复写成改成 `9a22c33b`，与实际 r11 默认值不一致。  
   **对照输入**：并排读取第 3 行注释与第 16 行 `PREV=${1:-74d58d14}`，或无参数执行并核对 `PREVS`，即可显形名实不一致。

2. `_bmad-output/审查/evidence-g810/check_g810_refs.py:333` — `_check_provenance_tokens()` 的函数说明仍写「4–40 位纯字母数字 token」，而 `_ALNUM_TOKEN_RE` 在 :317 已是 `+`，顶部 v4.9 说明 :4-6 也明确「不限长」。  
   **对照输入**：并排读取 :317 regex、:333 函数说明与 :4-6 版本说明；同一实现被描述成两个不同长度口径。

3. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r11.md:20` — 待收尾 r11 prompt 引用 `jev-triage-1db667ba-run-20260920T141638.txt`，但实际文件和 `_bmad-output/审查/evidence-g810/sidecar-g810-r11-1db667ba.json:9` 都指向 `...141639.txt`。  
   **对照输入**：列出 evidence-g810 下 `jev-triage-1db667ba*`，再对照 sidecar `source_stdout`，可见 141638 不存在、141639 存在。

4. `_bmad-output/审查/evidence-g810/negctl-r11-post-20260920T141449.txt:1-68` — 当前有一个未引用、未入库且不完整的 post 负控输出，只含 5/27 case、没有收尾 `verdict_bad`；完整且入库的是 `...141457.txt`。  
   **对照输入**：`grep -c '^--- case:'` 对 141449 得 5、对 141457 得 27，且 `git status --short` 显示 141449 仍为 untracked；该件不属于 §九.47 的预期 PENDING 收尾产物。

## ① 四项 open finding 闭合判定

- **r10-M1：按声明闭合。**  
  `_ALNUM_TOKEN_RE` 现为 `^[0-9A-Za-z]+$`；41×`a` 在 post 相位两条 `sha-missing`，41×`A` 与 1,000,000×`a` 也在函数级判定中红。canonical 底账当前仍无假红，`abc` 继续红，既有合法 hex OID `6337e320` 继续 rc=0。新的纯字母数字散文 token 会被 fail-closed 要求白名单，这是 UAT §十.27/43 已声明口径，不是未声明假红。

- **r10-L1：按声明闭合。**  
  我用内存 YAML 直接调用 v4.9 两层扫描，覆盖 direct key、merge source、mapping alias、nested mapping；`!!binary b3V0Y29tZQ==` 均归一为 `outcome`，node/constructed 两层均命中 `pass`。alias/merge 源没有残留穿透；其它键名仍按 §十.44 为声明边界。

- **r10-M2：事实性闭合，但新审计工具有两个 MEDIUM。**  
  `sidecar-g810-r9-9a22c33b.json` 现在确实存在于 `1db667ba` 树内；使用 `74d58d14:UAT` 作为名字面时，预修审计口径可复现为 32 条、唯一 missing 正是该 sidecar；post 输出对 `1db667ba` 为 42/0。r10 原 M2 的“对象不存在”已修，但产物审计本身的“全量名字”与“REF 绑定”仍不牢。

- **r10-L2：未闭合。**  
  green runner 注释与 checker 函数说明仍各有一处旧口径，见 LOW-1/2；因此 UAT:289「文案一并校正」不成立。

## ② v4.9 恒绿面与 UAT 声明边界

- §十.36–44 的既有边界——fenced YAML 面、其它自定义 tag/未来 PyYAML 行为不普查、非 fence YAML、产品树散文路径、非 `outcome` 键名、带 `_`/`-`/`::`/`.`/`/` 的 token——本轮可接受，不计新 finding。
- §十.45 的「只审存在、不校验内容哈希、不含上级审查 md」本身可接受；但“UAT 引用的 evidence-g810 产物名”实际被前缀过滤和可变工作区 UAT 缩窄，这两项仍需计 MEDIUM。
- 未发现 r11 两项行为修复引入新的未声明恒绿面；也没有发现 canonical 底账因不限长 token 或 binary key 归一化产生假红。

## ③ r11 证据链独立核对

- **绑定/血缘**：`1db667ba` 的唯一父是 `74d58d14`；r11 commit 26 个路径全部在 `_bmad-output/`；`4120e0b6..1db667ba -- . ':(exclude)_bmad-output'` diff 为空；底账在 `4120e0b6`、`74d58d14`、`1db667ba` 三点 sha256 均为 `cbfd619d…9bb9`。
- **脚本哈希**：`1db667ba` 树内 checker 与工作区均为 `59935c2c…7d6c4`；v4.8 为 `7dcfd394…a4098`；JEV 的 +16/−7 与 git numstat 一致。
- **负控/回归**：pre/post 各 27 case；R11 两条 pre rc=0、post rc=1；25 条旧用例两相位同型，24 红 + F2 rc=0；F2 digest `7ec785d3… → 0b548bf5…`，`digest_changed_vs_canonical=yes`；两相位每 case `sha_equal=yes`、对照 rc=0、`verdict_bad=0`。
- **锚群/YAML**：anchor 8/8 rc=1 + 对照 rc=0；YAML 5/5 rc=1 + 对照 rc=0。
- **digest 两代链**：precommit `v4.8@74 = eb60d83e…` → `v4.9@74 = 7ec785d3…`；postcommit `v4.8@1db = b33cd1bf…` → `v4.9@1db = 43c417e7…`。我在当前 `1db667ba` 只读复跑，实际 source digest 也是 `43c417e7…`。
- **产物审计两相位**：按各自 UAT blob 复算，`74d58d14` 是 31 tracked / 1 missing 且 missing 恰为 r9 sidecar；`1db667ba` 是 42 tracked / 0 missing。post 审计文件目前是 PENDING 未跟踪件。
- **PENDING-R11**：post green、post artifact audit、JEV JSON/stdout、sidecar、r11 prompt/review 均不在 `1db667ba` 树内，这符合 §九.47 的“develop + 收尾 commit”结构，但还不能当最终闭合证据。
- **r9/r10 顺延存档**：两轮 prompt、审查、JEV JSON/stdout、sidecar、post green 都已在 `1db667ba`；r11 树内没有 tracked `*.stderr`。

## ④ 收口判定

**不满足 B/H/M/L = 0/0/0/0。本轮为 B/H/M/L = 0/0/2/4。**

最小修复面不是重开底账或产品代码，而是：

1. 收窄/如实声明 artifact audit 的名字面，并让名字来源与被审 REF 绑定或记录 UAT hash/clean 证明；
2. 修正两处 r10-L2 文案；
3. 修正待收尾 prompt 的 JEV stdout 文件名；
4. 处置未引用的 141449 不完整负控件；
5. 完成收尾 commit 后在新的最终 HEAD 重跑 digest/产物审计，并由下一轮审查绑定该 HEAD 判定 0/0/0/0。

当前也不应释放合并门：除上述 finding 外，worktree 还有 8 个 untracked PENDING/杂项文件，其中只有 §九.47 列出的收尾件可进入下一个 commit，141449 不应入库。


