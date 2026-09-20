你是一位对抗性代码审查者。只读审查，不要改动任何文件，不要连接任何数据库或网络服务。工作目录 = 车道树；可用 `git --no-pager …` 读命令与 `sed` / `grep`。

# ① 背景

本卡 CARD-G8-10（BATCH-2026-09-18-第十五批，纯台账卡、零代码）——**r18 = 用户 2026-09-20「追加修复，直到审核说没有问题而通过」授权的第 3 个预算外轮**。闸门：**绑最终 HEAD 的一轮 B/H/M/L = 0/0/0/0** 才说「复核第十五批 P6」并释放合并门。

上一轮 **r17 = B0/H0/M1/L2**（存档 `codex-review-CARD-G8-10-r17.md`，绑 `4569aef4`）：M-1 行-JSON 互核未核首列文件名与 verdict（克隆数值 + 改名可恒绿）；L-1 审计控制件**内写文件**标题仍写 v2.6.1；L-2 r17 prompt 引用计数 20/20 与实含 UAT 的 21 件不符。

- **本轮绑定**：`5b581b0c6da2d57c491b2cb72c5d86885bf4ab37`（r18 develop commit；父 = `4569aef4`）。
  - **已入库（该 SHA 树内；本 prompt 逐条 `git cat-file -e 5b581b0c:<path>` 校核过：14/14 通过）**：`g810-r12-artifact-audit.zsh`（v2.6.3，未改）、`g810-r8-sidecar.py`（v4.9-r18）、`g810-r15-audit-ctl.zsh`（C1–C9，标题已同步）、`g810-r15-sidecar-negctl.zsh`（N1–N12+T+P1）；`audit-ctl-r15-20260920T161235-99941.txt`、`sidecar-negctl-r15-20260920T161236-99894.txt`；`codex-review-CARD-G8-10-r17.md`、`prompts/codex-prompt-CARD-G8-10-r17.md`（计数已校正为 21/21）、`jev-triage-4569aef4.json`、`jev-triage-4569aef4-run-20260920T160350.txt`、`sidecar-g810-r17-4569aef4.json`、`g810-green-r11-20260920T160348.txt`、`artifact-audit-r12-20260920T160348-95809.txt`、UAT。
  - **未入库（收尾阶段新增；本 prompt 不据其数字作论断）**：`g810-green-r11-20260920T161317.txt`、`artifact-audit-r12-20260920T161317-936.txt`、`jev-triage-5b581b0c.json`、`jev-triage-5b581b0c-run-20260920T161319.txt`、`sidecar-g810-r18-5b581b0c.json`、本 prompt、本审查存档。
- **r18 修法（§九.73，3 项）**：①（M-1）数据行**另核行首列含 JSON `files[0]` basename**（`row-file` 红；N12 控制）；**并声明词级边界**（§十.65：verdict 词只能转录 stdout，JSON 无独立 verdict 字段 ⇒ 把真实行 `REVIEW` 改 `PASS` 属上游自述篡改、本工具不可检测）；②（L-1）审计控制件内写文件标题 → v2.6.3 控制组 C1–C9；③（L-2）r17 prompt 计数 → 21/21。
- **product code diff = 0**（`git --no-pager diff --stat 4120e0b6 5b581b0c -- . ':(exclude)_bmad-output'` 空）；底账 sha256 恒 `cbfd619d2e79b4fce07a52864f3f64f6de455c5dc25f27423c8eba0836329bb9`。

# ② 请独立核对（不要采信）

1. r17 的 1 M + 2 L 是否闭合（尤其：`row-file` 检查是否真能拦「克隆数值 + 改名」；词级变体是否**按声明**为不可检测而非未声明恒绿）。
2. 控制件：审计 C1–C9（9/9，标签命中，含新标题）；sidecar N1–N12（含 N11 `row-churn`、N12 `row-file`）+ 孪生 T + P1（真实 r16）是否可在存档件中逐条对上。
3. 已入库清单 14/14 与未入库清单是否与 `5b581b0c` 树一致（可 `git cat-file -e` 复算）。
4. 声明边界（§十.36–67）里，`verdict 词级`（§十.65）与 `行首列 basename/第 2..N 行`（§十.66）是否属「可接受」；若你认为它们应计 M/L，请给最小反例。

# ③ 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话问题 + 一句话说明怎么让它显形（用「**未被拦下的输入**」「**对照输入**」「**负控输入**」「**门未覆盖的路径**」四种说法）。某级无条目写「无」。

**若四级全无，请在开头写 `BLOCKER: 无 / HIGH: 无 / MEDIUM: 无 / LOW: 无`**（该行是本 goal 释放合并门的依据）；否则给分级与最小反例。

# ④ 边界

只读；不连任何库；只评生成器 v4.9-r18 + 审计 v2.6.3 + r18 证据面 + 上述闭合项；不重评底账内容本体（r1–r5 五轮独立核对未发现假归属，且 r18 未改底账）；不评各 owner 卡本体；不重裁 §1 判定纪律；不要求把已声明边界在**本轮**扩面——若你认为需扩面，记为 M/L 并指出准确边界。
