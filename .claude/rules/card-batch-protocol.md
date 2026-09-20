# 卡批次协议（排批 / 车道 / 复核 / 合并）

> **来源**：第八～十批实战沉淀（`_bmad-output/审查/2026-09-04-第八九批合并僵局诊断与开发清单.md` v2、`2026-09-05-第十批复核裁定与待裁决登记.md`）。台账 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` §三 是本文的执行侧。
> **执行级别**：主 session 排批与复核时逐条对照；车道 goal/卡文引用本文而不是重抄。

## 1. 合并门（唯一口径）

- **阻断级 = 0 即可合**：数据丢失 / live vault 或 Neo4j 7691 写入 / 安全 / 指定裁判红 / 负控假绿（窄口径：负控本身谎报 PASS）。其余 BLOCKER/HIGH/MEDIUM/LOW **登记不阻断**。
- Codex 的 PASS/FAIL 字样**不进门**，但台账 §二 必须如实抄录（含模型名）。
- 终审绑定看**代码树**：`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空即仍绑定；纯注释尾巴由主 session 逐行核后可判等价（写明）。⚠️ 写法必须是 `':(exclude)…'`——`':!…'` 在 zsh 下被吃掉、在本机 git 2.50 下报 `Unimplemented pathspec magic`，rc=128 且 stdout 空，「为空即绑定」会把没跑成读成绿（第十一批复核实测）。
- **串行车道的绑定口径**：一条车道串多张卡时，前面的卡在后面的卡改代码后必然「失绑」——按**本卡 diff 面**判：`git diff --stat <审SHA> <本卡末commit> -- <本卡改过的代码文件>` 为空即仍绑定；跨卡后续 commit 不算破坏。但**同一卡内**审后再改（如「按 Codex 意见整改」那次 commit）就是真失绑，须登记「整改未复审」。
- **轮次（用户 2026-09-07 裁定 D-15，自第十三批起）**：有代码改动的卡 Codex **多轮，直到确认没有问题 goal 才通过**——最后一轮必须绑最终 HEAD（`git diff --stat <审SHA> HEAD -- . ':(exclude)_bmad-output'` 为空）且该轮 **BLOCKER = 0、HIGH = 0**（MEDIUM/LOW 登记）；审后再改代码 ⇒ 必再送一轮（只改 `_bmad-output` 不算）；车道对 HIGH 的驳回要写理由但**不能自判通过**，由主 session 复核时裁定，裁定前该卡按未完成；轮次上限 5，第 5 轮仍有 HIGH → 停下交主 session 人审。零代码卡（纯复审/文档）仍 1 轮。改卡号不重置。0 字节存档重发一次，再 0 字节 → 主 session 人审替代，不等配额。（第十二批及以前的「≤3 轮 + 整改未复审只登记」口径作废；第十一/十二批 11/13、14/23 失绑是本条的由来。）
- 主 session **人判合入**（终审「FAIL」但阻断级 0）必写：依据逐条对门、revert 点（单 squash SHA）、下批必排的修复卡。
- **不入库的复核不作依据（第十二批 §五.5，自第十三批起）**：验收单/卡文里「内部对抗复核 N agents」「N 路交叉核」之类**没有入库 journal**（无 evidence 文件、无 Codex 存档）的说法不得作为验收依据引用；主 session 复核时按「未复核」处理。要算数就落盘（`evidence-<卡短名>/` 或 Codex 存档），落不了盘就别写。

- **D-32 纯注释 / docstring 尾巴不占轮次不重置**（用户 2026-09-11 裁，自第十四批起）：审后只改注释 / docstring 的 commit 由主 session 逐行等价核（非注释行 diff 为空 + AST 相同）并在台账写明「判等价」，不计入 D-15 轮次、不触发再审；混入任何非注释行 = 真失绑，必再送一轮。
- **候选树合入门（第十四批起）**：全量 `pyright app` = **0 errors**（绝对路径跑，见 §2.2）。语义车道**必须保持 0**：hook `python-typecheck` 正常拦，本卡新增的 error 由本卡自己清（`# pyright: ignore[rule]  # <一行理由>`），**不得 `LEFTHOOK_EXCLUDE=python-typecheck`**；§2.3 过渡只剩 `python-lint` 的格式漂移一项。

## 2. Codex 复核命令（2026-09-05 起）

```bash
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-<CARD>.md)" \
  > <树>/_bmad-output/审查/codex-review-<CARD>.md 2> <树>/_bmad-output/审查/codex-review-<CARD>.stderr </dev/null
```

- 模型固定 `gpt-6-astra` + `ultra`（用户 2026-09-05 裁定）；新卡文/手册 `grep -c 'gpt-5.6'` 必须为 0。
- prompt 里禁止出现「构造 / 可复现片段 / 打穿 / 绕过」类请求（cyber 拦截在任务边界，不在措辞）。
- `*.stderr*` **永不入库**（`.gitignore` 已覆盖）；squash 时以 `ls-tree` 实数剔除。

### 2.1 存档首部模板（2026-09-05 起硬规则；第十二批 RV-F 落地）

每份 `_bmad-output/审查/codex-review-<CARD>[-rN][-pM].md` **首部**必须是下面的 blockquote（车道直接复制改字段），随后一行 `---`，再接 Codex 正文：

```
> 批次: BATCH-<日期>-第N批 · 车道 <Yx> · 卡 <CARD-ID> round-<N>[ prompt-<M>]
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `<codex --version 实测值，如 codex-cli 0.153.3>`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat <prompt 路径>)"`
> 审查绑定: `<审SHA 或 A..B>`（HEAD 若不同须如实写「不绑合并态 / 审工作区」）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，**行号不限、括注行号**；codex 0.153.3 把 `model:` 排在会话头第 5 行，字面抄前三行会漏自证字段——U2 第十三批 r3 实测，2026-09-11 修订；stderr 本身不入库）:
> `<line1>` / `<line2>` / `<line3>`
```

- **牙齿**：首部缺 `模型` / `reasoning_effort` / `codex` 任一字段，该轮**不计入**卡族轮次配额（等于没审），主 session 复核时按此判。
- 第十一批 9 份存档由主 session 于 2026-09-05 补首部（只加 blockquote + `---`，正文一字不改）；能从 `.stderr` 自证的字段填实测值，不能自证的写「未自证」，不追认。

### 2.2 裁判输出落盘（长跑卡 / 变异卡 / 复审卡）

- 所有承重裁判的 stdout+stderr 一律 `2>&1 | tee _bmad-output/审查/evidence-<卡短名>/<name>-$(date +%Y%m%dT%H%M%S).txt`，**末行写 `rc=$?`**。⚠️ 后缀用 `.txt` 不用 `.log`：仓根 `.gitignore` 有全局 `*.log`，`.log` 存档会被静默忽略、commit 里没有（第十二批排批实测 `git check-ignore`）（`tee` 会吞退出码：用 `set -o pipefail` 或 `${PIPESTATUS[0]}` / zsh `$pipestatus[1]` 取被测命令的 rc）。
- 验收单只**引用**路径与末行，不自述数字（Z6-B 教训：run-r2/r3 存档逐字节相同、无时间戳无 rc，不可区分轮次）。
- **判据里 git 输出一律 `git --no-pager <cmd> --no-color`**（⚠️ `--no-color` 是 **git** 的 flag，不是 grep 的——第十四批 T2-D 曾写 `grep --no-color` 即假绿，R-B14-11；第十二批 Y5-C 实测：多 worktree 共用同一 `.git/config`，作业期内 `color.ui`/`color.diff` 被并发改写，`git diff | grep '^@@'`、`grep '^+'` 类判据会因 ANSI 前缀静默归零，同一判据前后跑结论相反；重定向到文件不豁免）。写法：`git --no-pager diff --no-color …` / `git -c color.ui=never …`；判据旁必带同次执行的验伪锚（先证 grep 能命中一条已知正例）。
- 变异 / 换文件类裁判须同时落**跑前 / 跑后**全文件 `shasum -a 256`（不是 grep 变异标记字面量——变异体文本可不含该字样；且本文件不在 `mutant-residue-scan` 允许名单，写字面量会被门拦）。

- **pyright 一律绝对路径 + `test -x` 自证**（第十四批波 0 实测）：主干树 `backend/.venv` 是指向主仓 venv 的软链且**无 pyright**，`cd backend && .venv/bin/pyright app` 报 `no such file` 但 shell **rc=0** = 现成假绿。写法：`P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright; test -x "$P" || { echo 缺席; exit 1; }; "$P" app 2>&1 | grep -E '^[0-9]+ errors?, '`。**禁 `| tail -1`** 取汇总（pyright 1.1.411 末行是版本升级提示，取到的是警告不是 `N errors, …`，且不报错——U1 §十六.2）。
- **判据块含 `exit` 或 `cd` 时一律包进 `( … )` 子 shell**（交互 zsh 里 `|| { …; exit 1; }` 会直接关掉车道自己的 shell——第十四批 T2-E 实测，R-B14-11；顺序粘多条时第一条的 `cd backend` 会漏出，下一条 `cd backend && …` 失败被 `&&` 短路 = 什么都没跑 = 假绿——第十四批 T3-A/T3-B 实测，手册 §一.1.11）。
- **`grep -E` 里 `\|` 不是交替**：ERE 交替是裸 `|`，`\|` 在 macOS BSD grep / ugrep 下匹配字面竖线 ⇒ 判据恒 0 命中 = 假阴性（第十四批 T8-C 实测：三条原写法 0、改 `-e` 多模式后 5；全批扫出 26 处，多为写者为 markdown 表格转义 `|` 所致）。判据一律写 `grep -E -e 'a' -e 'b'`（表格内不出现竖线），或表格外裸 `|`；写完必在主干树实测期望值（手册 §一.1.12）。
- **zsh 下手写 ruff 判据必须数组**：`F=(${(f)"$(git diff --name-only --diff-filter=AM <base> HEAD -- 'backend/**/*.py')"}); print -r -- "files=${#F}"; (( ${#F} )) || exit 1; ruff check -- "${F[@]}"; echo rc=$?`，并带验伪锚（喂一个已知含 F401 的文件必须 rc=1）。裸 `$F` 在 zsh 不做词分割：53 个文件连成一个参数，`File name too long (os error 63)` 后仍打印 `All checks passed!` 且 rc=0（U1 第十三批 §五.2 实测）。同族：`cd backend` 后再写 `-- backend/app/x.py` 指向不存在的 `backend/backend/…` 静默空集——判据旁必打印集合大小。
- **承重存档逐文件 `git add`**（禁整目录 `git add _bmad-output`），入库前自检本次新增存档：0 字节、正文含 `No such file` / `does not exist` 的一律不入库；验收单引用写**全文件名**不用 glob（U1 第十三批 `b34600fd` 混入两份失败运行产物，glob 引用变歧义，波 0 集成期剔除 `08100483`）。
- **`-k` 定向裁判必须核收集数**：`N deselected` 且 selected=0 / pytest **rc=5**（no tests collected）不是绿；`… | tail -N; echo rc=$?` 取到的是 `tail` 的 rc（第十三批 `contract-targeted-*.txt` 的 `pytest_rc=0` 即此假绿；第十四批波 0 复测 `-k setup-wizard` 在 U5-D 写端点 exclude 后恒零收集）。
- **`tests/contract` 目录级会在候选树挂起**（pact provider 面等真服务；第十三批 `contract-integ-*.txt` 0 行、第十四批波 0 >10 分钟被中止）：候选树只跑 4 个非 pact 文件 `test_openapi_contract.py test_openapi_snapshot_drift.py test_node_id_patterns.py test_health_contract.py -v --hypothesis-seed=0`，跑后 `git status --porcelain backend/` 必空。

### 2.3 批级环境变更通告

- 任何改**共享运行环境**的动作（往 `card-v5-lance/backend/.venv` 装工具 / 升 codex / 升 lefthook / 改全局 hook）= 批级事件：动手前在手册 §零 追加一行「<时刻> <动作> <影响面>」并通知全部在跑车道；事后写进复核报告 §五。
- 反例：第十一批 Z7-B 07:42 往共享 venv 装 pyright，5 张卡随即用 `LEFTHOOK_EXCLUDE=python-typecheck` 绕过提交且无存档。凡用 `LEFTHOOK_EXCLUDE` 提交，验收单必须贴被跳过 hook 的原始输出与「报错不在本卡改动行」的证明；改 `backend/app/**` 的卡不得绕过 `python-typecheck`。**过渡（用户 2026-09-07 裁 D-16 甲；第十三批排批落地为两车道 + 末位）**：`backend/app` 存量 pyright 报错由第十三批 **U1 PYRIGHT-DEBT-services / U2 PYRIGHT-DEBT-rest 两条并行车道**清（阶段 1 只清无其他车道写者的文件；阶段 2 在语义卡全部进候选树后于候选树上清共享文件），合并队列**末位**（不是队首——注解 hunk 必须叠在语义改动之上，否则每张语义卡都要 rebase 穿过注解噪音）；GATE 卡（U2-B）全批最后一条合入时把本条改回硬禁。两卡合入前的过渡口径：改 `backend/app/**` 被 `python-typecheck` 拦下的语义卡允许**带存档**的 `LEFTHOOK_EXCLUDE=python-typecheck` 提交，存档判据 = **基线树多重集对照 = 0 新增**（`git archive <CODE_BASE> backend/app` 到临时目录跑 pyright 得基线多重集，键 = 按 `/backend/app/` 锚点截取的路径 + rule + 消息文本、不含行号，与工作树多重集相减为空；行号交集不充分，见第十二批 Y9-B 卡文）；**语义车道禁止顺手修存量**类型错误（那是 U1/U2 的面，顺手修 = 同文件双写者 = 集成冲突）。清不掉的存量（需改契约 / 第三方 stub）登记进 PYRIGHT-TAIL（第十四批）。

- **过渡条款状态（第十四批波 0，2026-09-11）**：U1-A / U2-A 阶段 2 已合入（`622f3a5d` / `b4705dde`），候选树 `pyright app` = 0 errors / 81 warnings。自第十四批起 `python-typecheck` **恢复硬禁**（见 §1 合入门）；`python-lint` 里 `ruff format --check` 的主干既有 **462 文件漂移**条款已于第十四批 T8-G GATE 合入时**关闭**（CARD-PYRIGHT-GATE 2026-09-17 回写）：`python-lint` 的 `ruff format --check` 自此**恢复硬禁**，改动行的格式漂移不再允许带存档跳过；462 文件整仓 format 由第十五批末位主 session 单独一 commit（D-40）。上文「U1 PYRIGHT-DEBT-services / U2 PYRIGHT-DEBT-rest 两条并行车道清」已完成，历史保留。
- **通告撤回登记**：`dcaaaef9`「Codex 配额耗尽至 09-15」批级通告被 `f8dd5903` 实测推翻（24 分钟后即恢复）→ 撤回（R-05）。教训：**外部服务的「重置时间」是一次观测不是不变量**——接手因限流停下的卡先花几千 token 复测，别继承结论。

### 2.4 GLM-5.3 复核（ZAI profile；2026-09-19 起，D-43）

> **背景（批级事件登记）**：2026-09-18/19 第十五批运行中 Codex `gpt-6-astra` 复核中断——P5 存档 `ABORTED-401-codex-review-CARD-G6-9c-R3-r2-*.empty`、P4 提交记「Codex 四模型交叉探针 — 账号形态整体不可用」、多卡末轮停在 `-retry/-retry2.stderr`、P1 G4-5 / P9 G4-13 走「人审替代」。用户 2026-09-19 裁定（D-43）：**复核改用 z.ai GLM Coding Plan 的 `glm-5.3`，仍走 Codex CLI**（z.ai 原生 Responses 端点），`--profile zai`。

**命令**（替换 §2 的 gpt-6-astra 命令；工具仍是 Codex CLI，故 `codex-review-*` / `codex-prompt-*` 文件前缀不变）：

```bash
source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 \
  -c model_reasoning_effort="max" \
  "$(cat <树>/_bmad-output/审查/prompts/codex-prompt-<CARD>.md)" \
  > <树>/_bmad-output/审查/codex-review-<CARD>.md 2> <树>/_bmad-output/审查/codex-review-<CARD>.stderr </dev/null
```

- 前置（一次性，机器级）：`~/.codex/zai.config.toml`（`[model_providers.ZAI]`：`base_url=https://api.z.ai/api/v1`、`env_key=ZAI_API_KEY`、`wire_api="responses"`）+ `~/.codex/models.json`（glm-5.3 catalog）+ `~/.codex/zai.env`（600，`ZAI_API_KEY`）。
- **端点必须是 `/api/v1`**：`/coding/paas/v4` 是 chat 线，codex 0.153.3 已硬移除 chat 协议（2026-02，openai/codex#7782 / PR#10157）。错端点 = 起不来，不是模型问题。
- 档位：GLM-5.3 只有 `low/high/max`，用 **`max`**（旧 `ultra` 停用）。
- 实测（2026-09-19）：rc=0；stderr 会话头 `OpenAI Codex v0.153.3` / `model: glm-5.3` / `reasoning effort: max`；工具调用（读文件并回报）正常。
- 配额：GLM Coding Plan 为点数制、非高峰 50%（无固定 5 小时窗）；多卡多轮送审前先核余量。

**§2.4.1 存档首部（GLM 版）**——字段与齿牙同 §2.1，取值改为：

```
> 批次: BATCH-<日期>-第N批 · 车道 <Yx> · 卡 <CARD-ID> round-<N>[ prompt-<M>]
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat <prompt 路径>)"`
> 审查绑定: `<审SHA 或 A..B>`（HEAD 若不同须如实写「不绑合并态 / 审工作区」）
> 会话头自证（抄 .stderr 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，行号括注；codex 0.153.3 实测 `model:` 在第 5 行、`reasoning effort:` 在第 9 行；stderr 本身不入库）:
> `<line1>` / `<line2>` / `<line3>`
```

- **牙齿**：首部缺 `模型` / `reasoning_effort` / `codex` 任一字段 ⇒ 该轮**不计入**轮次配额（同 §2.1）。
- **§2.4.2 补审通道（ZCode CLI；2026-09-19 起，D-43 附款）**——用户裁定「补审用 zcode」：

- 前置（已落地）：`npm i -g zcode-app-cli@latest`（非官方终端客户端；实测 `zcode-app-cli 3.12.3-26` + `zcode-runtime 0.16.5`）+ `~/.zcode/v2/provider_config.json`（600；`providerId=zai-coding-plan` / `templateId=zai-api` / `access.type=zhipu-coding-plan-api-key` / `defaultModelSelection=glm-5.3+max`）。
- 命令：`zcode --prompt "$(cat <prompt 路径>)" --cwd <车道树> --mode build --no-color --json > <树>/_bmad-output/审查/zcode-review-<CARD>[-rN].md 2> <树>/_bmad-output/审查/zcode-review-<CARD>[-rN].stderr`
- **实测（2026-09-19）**：`--prompt` rc=0；工具读文件正常（`FOUND=ZCODE_TOOL_OK_7777`）；`--json` 输出 `sessionId/traceId/turnId/usage`；**`--mode build` 下 Bash 与 Write 全被「No permission client configured」阻断 = 强制只读**（yolo 可跑 git——补审不用）。
- ⚠️ build 模式 Bash **部分可用（2026-09-19 G1-1 补审实测更正）**：`git` / `grep` 等只读命令可通过，`python3` / `git apply` 等被拦；写工具（Edit/Write）恒被「No permission client configured」阻断。⇒ prompt 内**仍必须内嵌** `git --no-pager diff --no-color <PREV> <审SHA> -- . ':(exclude)_bmad-output'` 输出（评审者偶可自跑 git，但不得依赖）。
- 存档首部（zcode 版）：`模型: glm-5.3（provider_config.defaultModelSelection）` · `工具: zcode-app-cli 3.12.3-26 / runtime 0.16.5` · `命令:` 全文 · `审查绑定: <审SHA 或 A..B>` · `自证: --json 的 sessionId/traceId 原文（抄）`。
- **牙齿**：缺 `sessionId`（或 JSON 解析失败）该轮**不计入**轮次配额；其余轮次/绑定规则同 §2.1 / §2.2。
- **通道分工**：开发复核默认 codex+zai（§2.4）；补审走本通道；同一卡同一轮只走一条通道，轮次编号沿用 `-rN`（接既有最大轮次之后）。

**§2.4.3 Jev 审查分诊（2026-09-19 起）**——送审前风险排序（用户裁定全批采用）：

- 工具：`scripts/jev_review_triage.py`（Typesafe System One，jev-1.13.0；对卡级 diff 按文件出 urgency/REVIEW/TEST/risk；8 卡校准基线：高危召回 7/7）。
- 包装：`bash ~/.b15b-drive/jev_triage.sh <git-ref> <outdir>`（source `~/.config/jev/env`；在 feature 树运行，lane SHA 同库可解析；产出 `jev-triage-<short>.json`）。
- 用法：**送审前**对「本卡末 commit / 审SHA」跑一次；分诊表按 urgency 降序嵌入审查 prompt ③ 问题清单排序；JSON 落该卡 evidence 目录。
- 校准：每 20-30 张卡跑一次 `scripts/jev_triage_calibration.py` 复校阈值。
- harness 接线：Claude Code=fast-jev-compaction 插件；OpenCode=`jev-review` MCP；Codex=`mcp_servers.jev-review`（env_vars 透传）；ZCode=`setting.json` `mcp.servers`。

**历史保留**：§2 / §2.1 的 `gpt-6-astra + ultra` 记录**不改写**（第十五批前半段史实）；自本条生效起新送审一律走 GLM。启用属批级事件 ⇒ 已记手册 §零。

## 3. 车道裁判的最低覆盖

- 卡自己点名的裁判（显式文件）之外，**改了什么面就必须跑那个面的目录级套件**：改 `canvas-vault/.claude/skills/**` 脚本 → `tests/skills` 目录级；改 `backend/app/**` → 对应 `tests/api` / `tests/unit` 子集 **+ `tests/regression` 目录级**（第十四批 T3-C 漏跑，G6-9 边界矩阵登记门按设计翻红，主 session 集成修复 `9c4e7e82`）；改 `tests/support` / conftest → 全部门下目录级。
- **串行整改后每一轮 = 在当前 HEAD 重跑全套承重裁判**（端到端门 + 负控 + 地盘 + 目录级），只重跑上一轮点名的判据不算（第十四批 T6-B (g)/(k) 只在早期 commit 跑过、T5-B 负控绑 r9 而代码到 r11、T3-A 末 commit 未送审也未跑负控 runner——三卡同病；复核时按「未验证」处理，主 session 补跑或退卡）。验收单文首终态字段（最终代码 SHA / commit 数 / 轮次 / evidence 数）**收工时必须重算**，写卡时的数字一律过期。
  - 教训：第十批 X6 改 `recap_scan.py` 加了模块级 dataclass，生产加载点 `recap_exam_build.py` 崩，`tests/skills` 117 红，卡裁判与两轮 Codex 都没跑到（`5322043f` 集成修复）。
- 动态加载（`importlib.util.spec_from_file_location` + `exec_module`）的目标含 `@dataclass` → **必须先 `sys.modules[name] = mod`**（Python 3.14 dataclass 自省取 `sys.modules[cls.__module__].__dict__`）。修坑时 grep 全部加载站点，不只修自己的测试。
- 无 W4 门的树上**禁目录级 pytest**（`test_vault_scope_409.py` 等 25 个 real-app 文件在收集/执行期起 lifespan 连 7691）；主干已含门（第十批起）可跑，但 `tests/integration` / `tests/e2e` 走 advisory 仍会真连。
- **改 `canvas-vault/.claude/scripts/{fsrs_bridge,decay_beta}.py` 的卡 = 合入当天必须部署 live**：`daily-review-wrapper.sh` 对这两份文件做开发树↔live 逐字节 `cmp`，不一致 → exit 78，整条复习链停摆（2026-09-05 09:05/10:05 已发生）。部署由主 session 在用户**当次显式授权**后执行：先备份 live 旧副本到 `canvas-vault/backups/` 记 sha → cp → `cmp` → 等下一个 :05 档核 `launchctl list` 归 0 → 证据落 `_bmad-output/审查/evidence-deploy/`。只部署 wrapper 门覆盖的文件，**不顺手部署 SKILL.md**。squash 与部署须在同一 session 内连做（中间每一档都在停摆）。
- 新车道 `backend/.venv` 缺席时建目录级 symlink 指向 `card-v5-lance/backend/.venv`（`.gitignore` 覆盖），否则 lefthook `python-lint` rc=127 阻断 commit。

- **W4 哨兵判据绑 `blocked=` 次数 + 失败正文，不绑 nodeid**（R-08/R-10，第十四批起）：同一代码状态下哨兵红会在 nodeid 之间翻转（U10-A r4/r4b 实测：`candidate422` ↔ `mock_warning`，经 U1 第十三批验收单 §五.9-ter 转述落盘），逐 nodeid diff 自带 flaky。判据：`grep -c "blocked=" <存档>` 恒定 + `grep -oF "('::1', 7691, 0, 0) on thread MainThread" <存档> | sort -u | wc -l` = 1；红总数仍对基线，但不对具体哪条 nodeid 承 W4 身份。汇总行 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=<n> (blocked=<m>…)` 是该哨兵的**总账标签**，不是判据开关（第十五批 §七 更正）：未设该 env 时 `blocked=0`（候选树常态），探针显式设置攻击次数时按「恒 12」口径核——两态都写明。

## 4. 合并程序（主 session）

1. 集成候选树从主干 HEAD 切（scratch worktree），按手册队列 **逐卡 squash**（单卡多 commit 用 `cherry-pick --no-commit <range>`；整枝用 `merge --squash`），每步剔 `*.stderr*` + 断言干净。**禁止用「主干→车道全树 diff 套用」实现 squash**（会删掉车道没有的主干新文件、回滚台账）。
2. 树等价：每车道改过的每个代码文件在候选树上与车道 tip 逐字节相同；跨车道代码文件交集须为空或已声明。
3. 候选树补 gitignored `backend/.env` 后**重跑全部卡裁判 + 门下目录级**；红分三类：主干既有（在主干 HEAD 复现）/ 门抓到的既有偷连 / 本批引入（阻断）。
4. 集成期修复走**独立 commit**（不揉进卡的 squash），台账 §二 写「+ 集成修复 `<sha>`」，§一.b 写根因与卡方声明不实之处。
5. 主干 `--ff-only` 到候选尾；原分支 tag `merged-squash/<branch>`（部分抽取 `-<卡号>-only`）；台账 §一/§一.b/§二 更新；推送 origin 与 backup（**tag 逐个推**，zsh 不分词）。
6. guard hook 对 force-push 的正则会跨整条命令匹配 ` -f `：含推送的那条命令里不得再写 `[ -f x ]` 之类，改用 `test -e`。

## 5. 排批（主 session）

- `/goal` 正文硬限 4000 字符 → 短 goal（≤3800，长度门脚本必跑）+ 卡文（无限制，车道必读）分层。
- 卡文事实必须在**当前主干**实测；主干前进后复用旧卡文前重验（第十批 X8：7 条事实在新主干上失效）。
- 台账是全部卡的共同写入面 → **只有主 session 改**；卡在验收单写「台账待登记条目」。
- **tests/unit 既有红基线**：主 session 每批开跑前落一份 nodeid 口径的基线（`_bmad-output/审查/evidence-b<N>/unit-red-baseline-<主干SHA>.txt`），车道开工/收工各跑一次目录级并 `diff`，差集才算本卡引入或修复；「298/289」这类含日志噪音的行数不得作分母。
- 每张卡的完成条件含「本卡未证明什么」必填；数字与命令输出一致（`wc -m` 计字符非字节）。
- **开卡必跑批注检索**（G1-1；自 `scripts/annotation_search.py` 合入主干之后的下一批起——第十五批本身不追溯，该脚本正是本批 G1-1 的产物）：主 session 排批写卡文前、车道开工第 0 分钟各跑一次 `PYTHONDONTWRITEBYTECODE=1 python3 scripts/annotation_search.py --story <卡号> --story <src 总账条目号> --keyword <主题词≥1> 2>&1 | tee _bmad-output/审查/evidence-<卡短名>/annotation-search-<ts>.txt; echo rc=$pipestatus[1] | tee -a 同一文件`（⚠️ 必须 `2>&1`：命中数汇总行走 stderr，只重定向 stdout 会得到一份 0 字节存档，撞 §2.2「0 字节不入库」）。0 命中也落档、rc=1 如实记。引用口径：**有命中**时卡文 §〇 / 验收单引用该存档的命中数与至少一条 `file:line`；**0 命中**时引用该存档的 `rc=1` 与汇总行的 `files_scanned` / `marker_hits`，不得为凑出 file:line 反复放宽 `--keyword`。私人 root 默认排除；`--include-private` 只在用户当次显式授权后使用，不得为凑命中自行加（A01 当前只声明边界、不提供授权流程，授权即用户本人的一次裁定）。替代 A01/A02 全量考古（总账 v2 G1-1）。
- **每卡收官须更新 ledger 行（CARD-G1-3，自第十六批起）**：改了能力面（入口 / 依赖 / schema / UI）的卡在验收单写「ledger 待登记行」（id / E 级 / 证据 / 限制 / 降级触发面），与「台账待登记条目」同口径由**主 session 合入时**落 `docs/release-evidence/capability-ledger.md`；车道不得直改 ledger（多车道并行 = 合并冲突）；E 级不得高于证据（§12.5，E3+ 须指 live manifest，本版恒 0）。

## 6. 第十五批回流条款（2026-09-20 主 session 回写）

> 来源：第十五批排批草案/开跑手册 §七「协议回写候补」（本批多卡实测各踩一次）。只收尚未写入 §1–§5 的条款；已写入的不重复。

- **ruff 验伪锚一律 F821、探针文件必须放仓内**（第十五批 T1-A/T2-A/T2-E/T4-B/T5-B/T10-C/T10-D 七卡同踩）：`backend/ruff.toml` 的 select 不含 F401，F401 锚恒不触发；scratchpad 里的探针吃不到本仓 ruff 配置。
- **`--tb=line` 对 setup ERROR 不带 file:line**（T10-A）：以 file:line 作判据在 setup 错误上恒 0 命中 = 假阴性。
- **被中断的 pytest 存档先断言汇总行存在**（T10-D）：`=+ … in …s =+` 不存在时「0 条红」是假绿，不得读红数。
- **W4 哨兵自证防子进程吞行**（T5-E）：`subprocess.run(capture_output=True)` 套 pytest 时哨兵行不进存档 ⇒ 存档无法自证零连库；W4 判据口径见 §3。
- **本机 urllib 会把 127.0.0.1 交给系统代理**（T4-A）：任何自连判据必须 `ProxyHandler({})` 直连。
- **`find -newer` 类只读判据会被并发车道打成假红**（T4-A/T3-C）：非 0 时逐文件归因，不得直接判违规。
- **含中文路径的 `git diff --name-only` / `grep -c '^_bmad-output/'` 类判据须 `-c core.quotepath=false`**（T4-A/T10-D/T9-B/T7-A 四卡）。
- **lefthook `spec-sync-flat` glob 在本机 Go 引擎下跨目录**（T3-A/T3-C/T3-D/T5-A/T5-E 五卡）：任何触及 `backend/app` 的提交都会被自动塞进 `backend/openapi.json`；标准处置 = 单独一个只含 `openapi.json` 的还原 commit（零 `LEFTHOOK_EXCLUDE`、零 `--no-verify`）。
- **卡文里的 openspec 命令一律仓内绝对路径**（T4-C）：`npx --no-install openspec` 在仓外跑不通，写 `<repo>/node_modules/.bin/openspec`。
- **完整 SHA 必 `git rev-parse` 取 + `git cat-file -t` 验存在**（T7-C 缺陷 6）：禁手工补全；**存档自报 `rc=` 不能当承重判据**（T7-B）。
- **本机 awk（20200816）不认 `--`**（T8-A）；**零暂存面下 lefthook 整块 skip、不打印 `[Mutant-Scan] OK`**（T8-A）——「干净暂存面应见 OK」是死判据；**zsh 无引号 `$TARGETS` 不做词分割**，sha 判据必带 `grep -cE '^[0-9a-f]{64}  '` = 文件数的验伪锚（T8-B）。
- **多版本同名存档须有机器可读「当前版」标记；「回应声称已改 vs 原件未改」须有对账机制**（T10-E 一卡七次）。
- **驳回的正确形态**（T8-B）：实测推翻复核方前提 + 下一轮复核方明文确认——不是车道自判通过。
- **基线数字必须附产出它的完整命令**（T8-B 三次口径错跑）；**目录级跑法须与基线头第 2 行逐字同**（T10-A）。
- **lefthook 双版本口径**（T8-A/T8-E）：`--no-auto-install` 在 1.x 是全局 flag、在 2.x 是子命令 flag；验证一律用绝对路径裸调用。
- **「登记不阻断」同样适用于「要不要为它新增一处能力」**（T8-D）：不能因 MEDIUM 逼车道扩门。
- **轮次上限与「审后改代码必再送一轮」的互斥场景**（T3-A）：修 ⇒ 必再送、不计上限；不修 ⇒ 登记（以 §1 轮次条为准）。
- **合入主干 = 上线**（第十五批 §七）：`daily-review-wrapper.sh` 以 feature 树为工作树、`daily-review-push.sh` 直接执行该树 `scripts/daily_review_run.py` ⇒ `scripts/` 面卡合入 feature 后下一个 :05 档即执行新代码；`fsrs_bridge.py` / `decay_beta.py` 的部署门见 §3。
