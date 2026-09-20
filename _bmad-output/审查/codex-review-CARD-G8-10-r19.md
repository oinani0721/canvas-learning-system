BLOCKER: 无 / HIGH: 无 / MEDIUM: 1 / LOW: 1

**结论：`B/H/M/L = 0/0/1/1`，不满足 `0/0/0/0`；本轮不能说「复核第十五批 P6」，合并门继续锁定。**

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py:154-159` — `row-file` 只检查 `rfind(basename)` 的 occurrence 前面是否为 `/` 或行首，没有检查 `_pos0 + len(_fn0) == len(_head0)`，因此并没有实现宣称的“basename 后缀”，而是仍然接受“路径组件前缀 + 任意尾串”。  
   **未被拦下的输入**：保持 JSON、churn、三数值、risk、verdict 全部不变，只把 stdout 数据行首列改成同目录伪文件 `_bmad-output/审查/evidence-g810/g810-r8-sidecar.py-junk"`；当前算法得到 `pos=30`、前一字符为 `/`，判定为 true，不会产生 `row-file`，生成器应退出 0。静态复算结果为 `pos+len(fn)=48 < len(head)=53` 且边界检查仍为 `True`。这不能用 §十.68 的“目录层级不核对 / 第 2..N 行不核对”吸收，因为这是同一目录下的第 1 行最终文件名本身不相等。

## LOW

1. `_bmad-output/验收单/UAT-CARD-G8-10-2026-09-19.md:469` — UAT 声称“真实行（r17/r18 两轮 JEV）= rc=0”，但 `e8aec46f` 树内没有把这两对真实 JEV 输入绑定到 v4.9-r19 生成器 SHA `797c99…` 的干净复跑件。  
   **门未覆盖的路径**：树内 `sidecar-g810-r17-4569aef4.json` 与 `sidecar-g810-r18-5b581b0c.json` 只记录泛化 generator 名、不记录生成器 SHA，生成时间也早于 r19 控制件；r19 sidecar 控制存档的干净正控 P1 是真实 r16。要用树内证据支撑该行，需用 exact `797c99…` 版本分别复跑 unchanged r17/r18 JEV 并归档两个 `rc=0` 结果，或收窄 UAT 声明。

## 独立核对摘要

- **绑定**：当前 `HEAD = e8aec46f0b3b76db432acb18119ad3511e7d4e45`，父提交确为 `5b581b0c6da2d57c491b2cb72c5d86885bf4ab37`，commit tree 为 `531a4866d03ad5837441fff700bd2026e3791c7e`。
- **r18 闭合状态**：
  - r18-M1：具体 `evil-<basename>` 变体已被 N13 拦下，但如上所述，“路径边界后缀”仍有尾串绕过，M 未完全闭合。
  - r18-L1：已闭合。`g810-r15-sidecar-negctl.zsh:2` 写明 `N1–N13 + T + P1=r16`，实际运行矩阵在 `:97-110` 覆盖 N1–N13；存档 `sidecar-negctl-r15-20260920T161931-6704.txt:40-42` 显示 N13 `row-file`、`rc=1 assert=yes`。
  - r18-L2：已闭合。`g810-r15-sidecar-negctl.zsh:16` 写“P1 真实 r16”，`:112` 实际使用 `jev-triage-884af91a.json` 且 `--round r16`；存档 `:46-48` 显示 SHA `884af91a…`、`rc=0`。
- **控制件复算**：
  - `audit-ctl-r15-20260920T161919-6361.txt`：C1–C9 逐项存在，全部 `rc=1 assert=yes`，末尾 `verdict_bad=0`。
  - `sidecar-negctl-r15-20260920T161931-6704.txt`：N1–N13 逐项存在，N12/N13 均命中 `row-file`；T 为 `rc=0` 且 `partial=true`；P1 为真实 r16、`rc=0`；末尾 `verdict_bad=0`。
  - sidecar 存档记录的 generator SHA `797c99baaed9f783ab4b6e332b85bc88aa3eb10a51131d216d91b9143931ba47` 与 `e8aec46f` 树内 `g810-r8-sidecar.py` SHA 一致。
  - 审计 runner 在 `e8aec46f` 树内 SHA 为 `e7b1ce48e68811c61b9f803b248f231200c70bd94d2d6f4bdbb963ac6b56bff7`，与 v2.6.3/C1–C9 口径一致。控制件在 develop commit 前执行、审计 REF 显示父提交 `5b581b0c`，但审计 runner blob 在父/本提交未变，且 sidecar 控件以生成器 SHA 绑定，实际版本与条目数相符。
- **清单与范围**：
  - 已入库 14/14 均可从 `e8aec46f:<path>` 解析；其中 prompt 中的 `prompts/codex-prompt-CARD-G8-10-r18.md` 实际树路径为 `_bmad-output/审查/prompts/codex-prompt-CARD-G8-10-r18.md`。
  - 当前未入库集合恰好是列出的 7 件：r19 green、r19 artifact audit、r19 JEV JSON/run、r19 sidecar、r19 prompt、r19 review 存档；本轮未据其数字作论断。
  - `5b581b0c..e8aec46f` 共 12 个 changed paths，全部在 `_bmad-output/**` 下；因此 product code diff = 0。
- **标题约定**：不将历史前缀 `r15 → rNN` 本身计 M/L。按用户给定的判据看版本与条目数：审计为 v2.6.3 + C1–C9，sidecar 为 v3 且实际矩阵含 N13，均与实跑一致。
- **§十.36–69 边界**：目录层级不还原、第 2..N 行不逐行互核、verdict 词只能转录 stdout、未合并/未集成/未触发真实故障/未验现网等声明，在“纯台账卡、零代码”的口径下仍可接受；但 §十.68 宣称的“basename 以路径边界结尾出现”没有被实现完全覆盖，已按 MEDIUM 计。

**Now / Prohibited / Unlock when**

- **Now**：r19 = `B0/H0/M1/L1`。
- **Prohibited**：不得宣告「复核第十五批 P6」，不得释放合并门。
- **Unlock when**：修正 `row-file` 的真正末端后缀判定并加同目录尾串负控；补齐或收窄 v4.9-r19 对真实 r17/r18 输入的干净复跑证据；然后在绑最终 HEAD 的新审查轮取得 `B/H/M/L = 0/0/0/0`。
