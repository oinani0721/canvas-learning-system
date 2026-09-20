你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景

CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r19 = 用户 2026-09-20「追加修复，直到审核说没有问题而通过」授权的第 4 个预算外轮**。闸门：**绑最终 HEAD 的一轮 B/H/M/L = 0/0/0/0** 才说「复核第十五批 P6」并释放合并门。

上一轮 **r18 = B0/H0/M1/L2**（存档 `codex-review-CARD-G8-10-r18.md`，绑 `5b581b0c`）：M-1 `row-file` 用**子串包含**，`evil-<basename>` 仍通过；L-1 sidecar 控制件标题/矩阵仍写 N1–N11；L-2 同文件 P1 注释仍写「真实 r14」。

- **本轮绑定**：`e8aec46f0b3b76db432acb18119ad3511e7d4e45`（r19 develop commit；父 = `5b581b0c`）。
  - **已入库（该 SHA 树内；逐条 `git cat-file -e e8aec46f:<path>` 校核过：14/14 通过）**：`g810-r12-artifact-audit.zsh`（v2.6.3）、`g810-r8-sidecar.py`（v4.9-r19）、`g810-r15-audit-ctl.zsh`（C1–C9）、`g810-r15-sidecar-negctl.zsh`（N1–N13+T+P1）；`audit-ctl-r15-20260920T161919-6361.txt`、`sidecar-negctl-r15-20260920T161931-6704.txt`；`codex-review-CARD-G8-10-r18.md`、`prompts/codex-prompt-CARD-G8-10-r18.md`、`jev-triage-5b581b0c.json`、`jev-triage-5b581b0c-run-20260920T161319.txt`、`sidecar-g810-r18-5b581b0c.json`、`g810-green-r11-20260920T161317.txt`、`artifact-audit-r12-20260920T161317-936.txt`、UAT。
  - **未入库（收尾阶段新增；本 prompt 不据其数字作论断）**：`g810-green-r11-20260920T162006.txt`、`artifact-audit-r12-20260920T162006-7047.txt`、`jev-triage-e8aec46f.json`、`jev-triage-e8aec46f-run-20260920T162007.txt`、`sidecar-g810-r19-e8aec46f.json`、本 prompt、本审查存档。
- **r19 修法（§九.76，3 项）**：①（M-1）`row-file` 改**路径边界后缀**（取首列去尾引号后最后一次 basename 出现处，其前须为 `/` 或行首）⇒ `evil-` 前缀不再通过（N13 控制；真实截断形式仍在面内）；②（L-1）控制件标题/矩阵 → **N1–N13 + 孪生 T + 正控 P1**；③（L-2）P1 注释 → 真实 r16。
- **控制件标题约定（供你判定，非未声明项）**：存档件首行的 `r15 → rNN` / `v3` 是**历史前缀标记**，判据 = 标题中的**版本与条目数**（审计 = `v2.6.3` + `C1–C9`；sidecar = `v3` 且矩阵行含 `N13`）与实跑一致。若你认为该约定本身应计 M/L，请指明。
- **product code diff = 0**；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。

# ② 请独立核对

1. r18 的 1 M + 2 L 是否闭合（`row-file` 边界后缀是否真拦 `evil-` 变体；标题/注释是否与实跑一致）。
2. 控制件：审计 C1–C9（9/9 标签命中）；sidecar N1–N13（含 N12/N13 均 `row-file`）+ T `rc=0/partial=true` + P1（真实 r16）`rc=0`。
3. 已入库 14/14 与未入库清单是否与 `e8aec46f` 树一致（可 `git cat-file -e` 复算）。
4. 声明边界（§十.36–69）是否仍属「可接受」；若需计 M/L，给最小反例。

# ③ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」）。某级无条目写「无」。

**若四级全无，请在开头写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`**（该行是本 goal 释放合并门的依据）；否则给分级与最小反例。

# ④ 边界

只读；不连任何库；只评生成器 v4.9-r19 + 审计 v2.6.3 + r19 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r19 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面。
