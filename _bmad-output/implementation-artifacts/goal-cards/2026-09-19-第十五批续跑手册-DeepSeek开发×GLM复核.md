# 第十五批续跑手册 —— DeepSeek V4.1 Flash 开发 × GLM-5.3 复核（2026-09-19）

> **批次**：BATCH-2026-09-18-第十五批（**续跑段**）· **原手册**：`2026-09-18-第十五批开跑手册-11车道33卡.md`（⛔ 不改写，历史保留）· **替换模型裁定 D-43（2026-09-19）**：开发 = OpenCode + `opencode-go/deepseek-v4.1-flash`；复核 = Codex CLI + z.ai GLM Coding Plan `glm-5.3`（`--profile zai`，`max` 档）· **本手册只覆盖**：**10 张未开卡** goal 块（§三）+ **复核补审清单**（§二）
> **续跑原则**：**不从 `9c4e7e82` 重开**——各车道原地续跑，起点 = 该车道现 HEAD（见 §一）；已完成的 22 卡与其历史 Codex 存档（`gpt-6-astra`）原地保留、不改写。
> **粘贴顺序**：每车道一个终端标签页 → 粘 §四 的 cd/opencode 行 → **把 §三 第一块作为普通消息粘贴**（⛔ 不要加 `/goal` 前缀——实测多行参数会被截到只剩第 1 行；普通消息会被插件**自动设为 goal**（objective=全文）并注入续跑）→ 前一卡独立 commit 且工作树干净后粘下一块。取块：`python3 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/show_goal_b15b.py <块名> | pbcopy`。

## 零、换模型配置（已落地，2026-09-19）+ 批级事件登记

### 零.1 复核侧：Codex CLI + GLM-5.3（z.ai 原生 Responses 端点）

- **机器级三件套（已建）**：
  1. `~/.codex/zai.config.toml` —— `[model_providers.ZAI]`：`base_url="https://api.z.ai/api/v1"`（**Codex 专用 Responses 端点**）、`env_key="ZAI_API_KEY"`、`wire_api="responses"`；profile 内 `model="glm-5.3"`、`model_reasoning_effort="max"`、`model_catalog_json="/Users/Heishing/.codex/models.json"`。
  2. `~/.codex/models.json` —— glm-5.3 catalog（1M 上下文 / low·high·max / parallel tool calls）。
  3. `~/.codex/zai.env` —— `chmod 600`，`export ZAI_API_KEY=…`（**密钥不进 config.toml / 不进仓库 / 不进 zshrc**；命令用 `source` 载入）。
- **复核命令**（替换原手册的 gpt-6-astra 命令，见协议 §2.4）：
  `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat …codex-prompt-<CARD>[-rN].md)" > …codex-review-<CARD>[-rN].md 2> …codex-review-<CARD>[-rN].stderr </dev/null`
- **⛔ 端点告诫**：`/api/coding/paas/v4` 是 chat 线，codex 0.153.3 已硬移除 `wire_api="chat"`（2026-02，openai/codex#7782 / PR#10157）——用错端点 = 起不来，**不是模型不可用**。
- **档位**：GLM-5.3 只有 `low/high/max`，用 `max`（旧 `ultra` 停用）。
- **实测（2026-09-19，本 session）**：`codex exec --profile zai …` rc=0；stderr 会话头三行齐（`OpenAI Codex v0.153.3` / `model: glm-5.3` / `reasoning effort: max`）；工具调用实测（读文件并回报 `FOUND=…`）正常。
- **配额**：GLM Coding Plan 为点数制、非高峰 50%（无固定 5 小时窗）；多卡多轮送审前先核余量。

### 零.2 开发侧：OpenCode + DeepSeek V4.1 Flash + `/goal`

- **模型**：`opencode-go/deepseek-v4.1-flash`（车道启动 `opencode -m opencode-go/deepseek-v4.1-flash`）；硬卡可临时换 `opencode-go/deepseek-v4-pro`（同命令改 `-m`）。
- **goal 机制（已落地）**：`~/.omo/omo.jsonc` 的 `[opencode]` 段内 `"goal": { "enabled": true, "auto_start": false, "default_max_iterations": 100 }`（备份 `~/.omo/omo.jsonc.pre-goal.<ts>`）。**实测（2026-09-19）**：开启后**任何用户消息都会被自动设为 goal** 并注入 idle 续跑。
- ⛔ **投递方式（实测三连坑后的定论）**：① `/goal <多行>` 参数被截到只剩第 1 行；② **整块多行粘贴（≈2-4KB）会静默丢弃**（chip 出现→回车→输入清空但什么都没提交，10 车道多轮复现）；③ 唯一 100% 可靠 = **文件指针短消息**：
  `执行任务「<块名>」：请先用 Read 工具读取 ~/.b15b-drive/blocks/<块名>.txt 的全文——那是你的完整任务指令，逐条严格执行，不得凭摘要行动。`（≈150 字符；块文件由 `show_goal_b15b.py <块名> > ~/.b15b-drive/blocks/<块名>.txt` 生成）
  首次读取弹「外部目录权限」→ 选 **Allow always**（或已在 `~/.config/opencode/opencode.jsonc` 预放行 `~/.b15b-drive/**`）。
- **实测（2026-09-19，本 session）**：多行粘贴 → `[Pasted ~4 lines]` → 7 行块完整进 `<user-task>`；`create_goal` 落 `.omo/goal/<ses>.json`；`update_goal[status=complete]` 生效；idle 续跑 prompt 已由插件注册。
- **工作树免脏**：`.omo/`（goal 状态 / run-continuation / ulw-loop）会落在车道工作树 → 已写入 `<common git dir>/info/exclude` 的 `.omo/`（全 worktree 生效，实测 `git check-ignore --no-index .omo/x` 命中）。**⛔ 不要**把 `.omo/` 写进 tracked `.gitignore`。

### 零.3 补审通道：ZCode CLI（zcode-app-cli）+ GLM-5.3（用户 2026-09-19 裁定「补审用 zcode」）

- **安装**：`npm i -g zcode-app-cli@latest`（非官方终端客户端，MIT；实测 `zcode-app-cli 3.12.3-26` + `zcode-runtime 0.16.5`；Node ≥22.19）。
- **配置**：`~/.zcode/v2/provider_config.json`（600，已写）——`providerId=zai-coding-plan` / `templateId=zai-api` / `access.type=zhipu-coding-plan-api-key`（复用同一把 z.ai key）/ `defaultModelSelection = glm-5.3 + max`。
- **补审命令（只读强制）**：`zcode --prompt "$(cat <prompt>)" --cwd <车道树> --mode build --no-color --json > <存档>.md 2> <存档>.stderr`
  - **实测（2026-09-19）**：`--prompt` rc=0；工具读文件正常（`FOUND=ZCODE_TOOL_OK_7777`）；`--json` 输出 `sessionId/traceId/turnId/usage`；**`--mode build` 下写工具（Edit/Write）恒被阻断；Bash 部分可用**（实测 2026-09-19：`git`/`grep` 通过、`python3`/`git apply` 被拦）——只读性由「写工具全拦 + 评审者不改文件」共同保证（补审实测外部可证：评审零写盘）。
  - ⚠️ build 模式无 Bash ⇒ prompt 内**必须内嵌** `git diff <PREV> <审SHA> --no-color` 输出（车道先跑 git、把 diff 贴进 prompt 再送审）。
- **zcode 存档首部（协议 §2.4.2）**：`模型: glm-5.3` · `工具: zcode-app-cli 3.12.3-26 / runtime 0.16.5` · `命令:` 全文 · `审查绑定: <审SHA>` · `自证: --json 的 sessionId/traceId 原文`（缺 sessionId / JSON 解析失败 = 不计轮次）。
- **通道分工**：10 张新 goal 的开发复核走 codex+zai（§零.1）；**补审**（§二）走本通道；同一卡同一轮只走一条。

### 零.4 批级事件登记行（协议 §2.3）

`2026-09-19 <时刻> 复核工具链换 GLM-5.3（~/.codex/zai.config.toml + models.json + zai.env；协议新增 §2.4）；开发 harness 换 OpenCode + opencode-go/deepseek-v4.1-flash（~/.omo/omo.jsonc goal.enabled=true）；影响面：本批 10 张未开卡的复核命令与 D-15 固定串（已就地改）、22 张已跑卡冻结不动；补审通道 zcode-app-cli（--mode build 只读）；P5/P7 未跟踪档归档 commit 57d29464 / df05f9f8`

### 零.5 Jev 审查分诊（送审前必跑）

- 包装器：`bash ~/.b15b-drive/jev_triage.sh <git-ref> <outdir>`（内部 `source ~/.config/jev/env` 的 `TYPESAFE_API_KEY`，在 feature 树运行；lane 分支 SHA 同库可解析；产出 `<outdir>/jev-triage-<short>.json`）。
- 用法：**送审前**对「本卡末 commit / 审SHA」跑一次 → 分诊表（urgency 降序、REVIEW 标记者优先）进 prompt ③ 问题清单排序；JSON 落该卡 evidence 目录。
- 校准：每积累 20-30 张卡跑 `scripts/jev_triage_calibration.py` 复校阈值（8 卡校准基线：高危召回 7/7）。
- harness 接线：Claude Code=fast-jev-compaction 插件（/compact）；OpenCode=`jev-review` MCP（opencode.jsonc）；Codex=`mcp_servers.jev-review`（env_vars 透传 JEV_API_KEY）；ZCode=`~/.zcode/cli/setting.json` `mcp.servers`。

### 零.6 起点锚容忍判据（补审/开发任意顺序安全）

块内「起点锚 <sha>」的完整判据：`git merge-base --is-ancestor <sha> HEAD` 为真 **且** `<sha>..HEAD` 只许 `_bmad-output` 归档类 commit，即
`git --no-pager log --oneline <sha>..HEAD -- . ':(exclude)_bmad-output'` 输出为空；不符则停下报主 session。

## 一、车道现状与续跑起点（2026-09-19 实测；并行 3 agent 审计）

| 车道 | 分支 | 现 HEAD | 本批已完成卡（复核轮次） | 剩余卡（本手册 §三） |
|---|---|---|---|---|
| P1 storage | card/p1-storage | `c33240fa` | LANCE-DUALWRITE(r5) · LANCE-INDEX-DELETE(r4) · G4-5(**人审替代**) | **P1-D**（CARD-DEBT-11） |
| P2 outbox | card/p2-outbox | `d2ebf694` | DEADLETTER(✓) · STAGING-WRITERS(r5-retry❌) | **P2-C**（CARD-REPLAY-REWRITE） |
| P3 deploy | card/p3-deploy | `9d4f7bf0` | G2-11(r4) · DEBT-10(✓) | **P3-C**（CARD-G8-7） |
| P4 fsrs | card/p4-fsrs | `858582d3` | CARD-STATES(r5) · G3-8(r3-retry2❌) · G8-4(retry❌) | —（全开，补审见 §二） |
| P5 review | card/p5-review | `57d29464` | G6-9c-R3(r2 + **ABORTED-401**) | **P5-B**（CARD-REVIEW-CHAIN-PUSH-STATE）→ **P5-C**（CARD-G6-13） |
| P6 skills-w | card-p6-skills-w | `5e305b28` | SEB(r2) · HARNESS(r5-retry❌) | **P6-C**（CARD-G8-3）→ **P6-D**（CARD-G8-10） |
| P7 skills-x | card-p7-skills-x | `df05f9f8` | G5-7(r6❌ 存档未提交) | **P7-B**（CARD-G5-10）→ **P7-C**（CARD-G5-12） |
| P8 backend | card-p8-backend | `16fd1e4e` | EXC-HANDLER(r5) · PYRIGHT-TAIL(r2) · G1-1(r1b❌) | —（全开，补审见 §二） |
| P9 testinfra | card-p9-testinfra | `96da70c6` | W4-GUARD(✓) · DEBT-1(r3❌) · G4-13(**人审替代**) | —（全开，补审见 §二） |
| P10 docs | card-p10-docs | `a03f0ce3` | G1-3(r6) · R-RC(r2) | **P10-C**（CARD-R-SLO） |
| P2b outbox-wave2 | — | — | 未创建（第二波） | 待 P2 三卡进候选树后由主 session 切树 |

**开跑前置处置（否则第 0 分钟的「工作树干净」门不过）**：
1. ✅ 已处置（2026-09-19 主 session）：`codex-review-CARD-G5-7-r6.md`（0 字节失败档）已归档 commit `df05f9f8`；补审接 `-r7`。
2. ✅ 已处置（2026-09-19 主 session）：`_bmad-output/审查/ABORTED-401-codex-review-CARD-G6-9c-R3-r2-20260918T215100.md.empty`（实路径 `审查/`，前稿笔误）已归档 commit `57d29464`；补审接 `-r3`。
3. 其余 8 车道实测 0 脏、HEAD = 上表值。

## 二、复核补审清单（末轮为 retry / ABORTED / 人审替代的卡）

> 判据：该卡末份复核存档不是 `.md`（真审）而是 `.stderr`（失败/重试），或该卡以「人审替代」结案。**补审是主 session 裁定项**：确认要计入 D-15 轮次才补，否则按原裁定登记。

| 卡 | 车道 | 末轮现状（实测） | 建议 |
|---|---|---|---|
| CARD-G4-5 | P1 | rev=0（人审替代结案） | 若需绑 HEAD 的一轮 B/H=0 → 补审 |
| CARD-STAGING-WRITERS-BOUNDED | P2 | `codex-review-…-r5-retry.stderr` | 补审（接 `-r6`） |
| CARD-G3-8 | P4 | `…-r3-retry2.stderr` | 补审（接 `-r4`） |
| CARD-G8-4 | P4 | `codex-review-…-retry.stderr` | 补审（接 `-r2`） |
| CARD-G6-9c-R3 | P5 | `-r2.md` + `ABORTED-401…empty`（已归档 `57d29464`） | 补审（接 `-r3`，zcode） |
| CARD-HARNESS-TREE-PARSE-R2 | P6 | `…-r5-retry.stderr` | 补审（接 `-r6`） |
| CARD-G5-7 | P7 | `…-r6.stderr`（r6 0 字节档已归档 `df05f9f8`） | 补审（接 `-r7`，zcode） |
| CARD-G1-1 | P8 | `…-r1b.stderr` | 补审（接 `-r2`） |
| CARD-DEBT-1 | P9 | `…-r3.stderr` | 补审（接 `-r4`） |
| CARD-G4-13 | P9 | rev=0（人审替代） | 若需绑 HEAD → 补审 |

**补审 goal 块（逐卡已生成，见 §三 `补审-*` 十条）**：SHA/文件集/轮次已按 2026-09-19 实测填死；取块 `python3 …/show_goal_b15b.py 补审-<CARD> | pbcopy`。校验见 `gate_goal_length_b15b.py`。
```

## 三、goal 块（10 张未开卡 + 10 条补审；唯一真相源 = 本节，由 show_goal_b15b.py 读取）

### P1-D（CARD-DEBT-11）

> 📋 复制下面代码块粘进 `P1` 标签页的 /goal；完整卡文 `第十五批-goals/P1-D.md`。

```
完成 CARD-DEBT-11：把 5-ge-1 的 C-1 写入契约 CanvasGraphEpisodeV1（canvas_episode.py:208，2026-06-03 后零改动、3 个生产消费方在用）正式冻结——裁 Task 3/4/5 归属（Task 3 落点全在 P2 地盘 ⇒ 移交；Task 4/5 表/端点候选树零存在 ⇒ 废弃）、复跑 test_canvas_episode_v1.py 19 用例存档、spec + py 头注释写冻结声明（版本 + 15 字段 + 禁改规则，D-32 纯注释）、spec→review、sprint-status→review、同 commit 把 1-16-callout-graphiti-hook / 2-10-wikilink-graphiti-sync 两旧 spec 改 superseded；为什么现在：DEBT-12 依赖本卡，spec/yaml 状态三处矛盾、协同硬规则 2 悬空已三个月。[BATCH-2026-09-18-第十五批 / CARD-DEBT-11]（4h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage（分支 card/p1-storage，续跑起点 HEAD = c33240fa，venv symlink + backend/.env 就位），本车道第 4/4 张（续跑）。第 0 分钟：核 pwd/分支：起点锚 c33240fa（容忍判据见 §零.6）/`git status --porcelain` 空；unit 红基线 evidence-b15/unit-red-baseline-9c4e7e82.txt = 33 自证（跑法与基线头第 3 行逐字同）；pyright 绝对路径 test -x。前提：P1-C CARD-G4-5 已独立 commit 且工作树干净。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P1-D.md——① 默认零代码：canvas_episode.py 只加 # 注释行（不加模块 docstring/常量/不改 Literal 值），D-32 用 ast.dump 机器比对 True；任何非 # 行进 diff 即转有代码改动口径；② 不实现 Task 3、不建表/端点、不改 5-ge-3、不碰 episode_worker.py/memory_service.py（P2 地盘）；③ 负控两段在改任何文件前、工作树干净时跑，pyright 保持 0 且禁 LEFTHOOK_EXCLUDE=python-typecheck。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟；(b) 先红（冻结 grep 0/0、状态现状、复跑门 19 passed、AST sha 基线、两段负控）；(c) Task 3 移交 / 4/5 废弃裁定进 spec 带证据；(d) spec 冻结段 + review；(e) py 头 # 冻结块 + sprint-status review + 两旧 spec superseded（annotate-callout-hotkey 零改动）；(f) 结构判据成对 + AST True + 验伪 False；(g) 复跑门收工 + tests/regression 目录级；(h) pyright 保持 0；(i) 套件不回退 + tests/unit 只减；(j) 不改端点不适用；(k) 负控两段；(l) 地盘核；(m) 现网只读；(n) Codex；(o) 单 commit；(p) 未证明/台账各 ≥4。
核心裁判：1. 复跑门 ( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider -rfE tests/unit/test_canvas_episode_v1.py ) 开工/收工各 19 passed（核收集数）；2. 负控段① :246 raise→pass ⇒ 恰 2 FAILED（DID NOT RAISE）、段② :214 Literal 改 V2 ⇒ test_callout_added_valid 红 + D32-AST-EQUAL= False，各段 git show HEAD:<path> 还原 + shasum 前后逐字同；3. D-32：ast.dump(git show <PREV>:py) == ast.dump(工作树) → True 且 diff 非 # 行计数 0，验伪锚 probe.py 加一行 → False；4. grep -c -i -e freeze -e 冻结 spec/py 0/0→≥1/≥1 + 状态前后成对；5. pyright (cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')=0 errors + ruff zsh 数组 rc=0 + F821 锚 rc=1；6. 地盘 git --no-pager diff --name-only --no-color <PREV> HEAD -- . ':(exclude)_bmad-output' 恰 canvas_episode.py，_bmad 侧 ⊆ 白名单，services/openapi.json 变更 0；unit/regression 目录级 nodeid diff 只减。
硬边界：禁写 live vault；禁连 7691/7687（本卡无 7692 门）；禁碰 fsrs_bridge.py/decay_beta.py；禁改 models/**、main.py、security.py、lefthook.yml、openapi.json、conftest、别车道文件；不实现 Task 3/4/5、不开 V2 类、不改 AC 原文与 supersedes 列表、不改 5-ge-3；test_canvas_episode_v1.py 只复跑不改；禁用 stash 与 checkout-HEAD 类还原；批中不装不升包；不改台账；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（零代码路径 1 轮；转代码口径则上限 5、审后改代码必再送一轮带 -rN；首部按协议 §2.4；0 字节存档不进 commit；prompt 五分节最小读取面 = 本卡 diff + canvas_episode.py:1-30,208-265 + spec 全文 + yaml 四段 + 测试全文 + d32/negctl 存档；措辞用负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；裁判输出 tee 进 evidence-debt11/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-DEBT-11-<日期>.md DoD-3 双段 + 「本卡未证明什么」「台账待登记条目」各 ≥4；commit header ≤100 含批次标记且含卡号 CARD-DEBT-11；*.stderr* 不入库；不 push；P1 车道末张，送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P1」。
```

### P2-C（CARD-REPLAY-REWRITE）

> 📋 复制下面代码块粘进 `P2` 标签页的 /goal；完整卡文 `第十五批-goals/P2-C.md`。

```
完成 CARD-REPLAY-REWRITE：把 Story 38.8 的 failed_writes.jsonl 回灌算法（fallback_sync_service.py :273-427）从「位置游标+长度比较+试过即成功」重写成「稳定记录身份 + 来源 vault 落盘 + 写完读回执才算成功 + 身份日志崩溃恢复幂等 + 扫回 .overflow.* 代际（默认扫回，对比段交用户裁）」，G2-2 并入；为什么现在：第十四批裁定书 §1.8 ④ 判剩余 HIGH 属算法层，§1.5 A/B 与 §二.3 都是数据丢失或错归属面。[BATCH-2026-09-18-第十五批 / CARD-REPLAY-REWRITE]（7h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox（分支 card/p2-outbox，续跑起点 HEAD = d2ebf694，venv symlink+.env 就位），本车道第 3/3 张（续跑）。第 0 分钟：核 pwd/分支：起点锚 d2ebf694（容忍判据见 §零.6）/`git status --porcelain` 空；BASE=evidence-b15/unit-red-baseline-9c4e7e82.txt（主干树绝对路径见卡文），grep -vc '^#' → 33；pyright 绝对路径 test -x 自证；开工 tests/unit 目录级落基线（跑法与基线第 3 行逐字同，无 --ignore）。前提：P2-B 已独立 commit、工作树干净。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P2-C.md——① main.py 零改动（:387/:420/:423/:463 启动门保持，需改则出 patch）、neo4j_client.py 只新增函数（既有四函数 AST 逐字同）、memory_service.py 只动 :502-522 与 :2855-2886（禁 :1788-2060）；② 缺 vault_id 的历史条目默认隔离不猜 vault（仅 CLS_REPLAY_LEGACY_NOSCOPE_VAULT 显式点名才归属），live backend/data 与 DEAD_LETTER_STORE_FULL_BODY 默认不动，现网迁移归 G4-6，未授权即 SKIP 登记；③ pyright 保持 0，禁 LEFTHOOK_EXCLUDE=python-typecheck。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）(a) 第 0 分钟 + 核 §〇 file:line（P2-A/B 后必漂，以符号名为准）；(b) 先红（overflow 零引用、contiguous_end >0、record_id/vault_id 0 行、7692 门三用例红、新单测红）；(c) 写侧身份戳接三写者；(d) 算法重写（身份代替位置、确认日志、legacy sha256 身份、来源 vault 只用条目自带值、回执比对、缺 timestamp 不用 now()、Episode 按 record_id 去重）；(e) overflow 代际扫回后走 .synced 30 天 retention；(f) 结构判据成对 + AST 门；(g) 7692 门 ≥7 用例；(h) pyright 保持 0；(i) 点名套件 + tests/regression 目录级 + tests/unit 只减（test_story_38_8 越界只改数据/断言并登记）；(j) 不改端点不适用；(k) 负控 ≥2 段；(l) 地盘核；(m) 现网只读；(n) Codex 多轮；(o) 提交；(p) 两清单各 ≥4。
核心裁判：1. 结构成对 grep -c 'overflow_siblings' fallback_sync_service.py 0→≥1、grep -c 'contiguous_end' >0→0、git --no-pager grep -n -F 'record_id' 三文件 0→各≥1；2. 7692 门 ( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/integration/test_replay_rewrite_7692.py -rA ) 改前三用例 FAILED 于图内断言、改后全 passed（核 collected ≥7；不可达即 skipped 并登记）；3. 负控：回执比对恒 True → 缺 timestamp 用例红；确认日志改 finalize 才记 → 崩溃恢复用例红；trap git show HEAD:<path> 还原+shasum 同；4. pyright (cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')=0 errors；5. 地盘 git --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output' ⊆ 卡文 (l) 白名单+验伪锚；6. tests/regression 与 tests/unit 目录级 diff 只许 <（单文件变量，禁 glob）。git 输出一律 --no-color；含 cd/exit 的块包 ( … )；ruff zsh 数组 + F821 锚。
硬边界：禁写 live vault；禁连 7691/7687（门只走 7692，不可达即 skip，注入锚 + URI 白名单照 t6b 门）；禁碰 fsrs_bridge.py/decay_beta.py/models/**/main.py/security.py/lefthook.yml/conftest/台账（零写者）；不重写 canvas_events/learning_memories 两链、不改 failure_counters.py 有界原语与 /traces 字段形状、不做 G4-6 迁移；禁用 stash 与 checkout HEAD -- 还原；批中不装不升包（P9-B DEBT-1 装 pytest-timeout 是唯一例外，须 §2.3 通告+主 session 批）；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（上限 5 轮；审后改代码必再送一轮并在当前 HEAD 重跑全套承重裁判；首部按协议 §2.4；prompt 五分节、最小读取面写死；措辞用负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；裁判输出 tee 进 evidence-replay-rewrite/（.txt，末行 rc=$pipestatus[1]）；验收单 UAT-CARD-REPLAY-REWRITE-<日期>.md DoD-3 双段+扫回 vs 丢弃对比段+「本卡未证明什么」「台账待登记条目」各 ≥4；commit header ≤100 含批次标记与卡号；*.stderr* 不入库；不 push；本车道末卡，送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P2」。
```

### P3-C（CARD-G8-7）

> 📋 复制下面代码块粘进 `P3` 标签页的 /goal；完整卡文 `第十五批-goals/P3-C.md`。

```
完成 CARD-G8-7：用当前已上线能力真实走一遍两白板（原白板→检验白板）全旅程——vault 准备→/board-recap→检索 search_notes→/start-exam-board 出题→/quiz-answer 本地 mastery_*→次日总览页 /api/v1/review/overview/page，每环节命令/产物 sha256/截图/skill 版本 hash（dev↔live 双列，实测 8 处不同）/用户签字落 _bmad-output/审查/evidence-g87-journey/，断点归属切片，零静默改写用户文件（live 跑前/跑后 shasum 差集 ⊆ 声明写入面）；不做 ChatGPT 终审（G1-8）；为什么现在：除 D5 单环节盲测与 J06 底稿外没有任何端到端旅程证据，R-J*/G1-8 全在纸上。[BATCH-2026-09-18-第十五批 / CARD-G8-7]（6h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy（分支 card/p3-deploy，续跑起点 HEAD = 9d4f7bf0，backend/.venv symlink → card-v5-lance/backend/.venv、backend/.env 已拷），第 3/3 张（零代码 ledger，续跑）。第 0 分钟：核 pwd/分支：起点锚 9d4f7bf0（容忍判据见 §零.6）/`git status --porcelain` 空；BASE=…/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b15/unit-red-baseline-9c4e7e82.txt 的 grep -vc '^#' 自证 33；pyright 绝对路径 test -x 自证；tests/unit 目录级开工基线（跑法与基线头第 3 行逐字同，不带 --ignore）；核主 session docker ps 存档 8011 在线。前提：P3-B CARD-DEBT-10 已 commit 且工作树干净。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md——① 真实旅程写 live vault 只能由用户当次授权（标签页说「G8-7 授权走查」）并在 vault 内会话执行（readonly guard R2 拦车道 session），未授权即 not_run + SKIP 登记，不得用旧存档顶替；② 走查窗口冻结部署：车道零 cp/零改 live/零改 skills，8 处 dev↔live 差异只双列登记；③ 零静默改写门：live 跑前/跑后 shasum 差集 ⊆ 10 类声明写入面，集外任何变化 = 阻断级登记，不靠放宽白名单消掉。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟 + 核 §〇 file:line；(b) 先红（目录/验收单 grep 0 + manifest 校验红绿成对）；(c) 车道侧产物 00~03/05 + manifest 骨架；(d) 授权侧六环节采证；(e) after 快照 + 差集对账 + manifest 填实（evidence_level ≤E3、signoff 用户勾选后才 approved）；(f) 结构判据成对 + 验伪锚；(g) 承重门；(h) 不改 backend/app pyright 不适用；(i) tests/unit diff 只许减；(j) 不改端点不适用；(k) 负控两段；(l) 地盘 diff 空；(m) 现网只读；(n) Codex；(o) 提交；(p) 本卡未证明什么/台账待登记各 ≥4。
核心裁判：1. skill 版本表 dev↔live sha256 逐文件（预期 DIFF=8）；2. live 跑前/跑后快照（四目录 + 主仓 daily-review state，只读）→ silent-rewrite-gate outside=0；3. manifest 先红（assertions 全 not_run 而 result pass ⇒ S3）后绿（validate_release_manifest.py rc=0）；4. 负控①篡改 before 副本一行 sha ⇒ diff 恰多出 原白板/CS.md 且原件 sha 同；负控② signoff 改 approved 不填 user/at ⇒ 校验红含 signoff；5. 地盘 git --no-pager diff --stat --no-color <P3-B 末 commit> HEAD -- . ':(exclude)_bmad-output' 为空 + 验伪锚（quotepath=false 去 exclude 命中）；6. tests/unit 开工/收工 nodeid diff 只许 <。git 输出一律 --no-pager … --no-color；含 exit/cd 的块包 ( … )；ruff zsh 数组预期 files=0 + F821 验伪锚 rc=1。
硬边界：禁写 live vault（车道侧；旅程写入只由用户 vault 内会话）；禁连 7691/7687（观察只经 http://127.0.0.1:8011 只读 GET）；禁碰 fsrs_bridge.py/decay_beta.py（实测 dev==live）；不跑 deploy-vault.sh、不手动触发 daily_review_run.py（P5 面）；证据不进 docs/release-evidence（P10 唯一写者）；不改 backend/app、skills、conftest、别车道文件；不做 G1-8/G6-13/G8-6/C1-02 的活；禁用 stash 与 checkout HEAD -- 还原（负控只动 scratch 副本）；批中不装不升包；不改台账；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（零代码卡 1 轮；送审后补跑授权环节改了 evidence/manifest 则再送 -r2 绑新 HEAD；首部按协议 §2.4；prompt 五分节最小读取面=本卡 diff --stat+evidence-g87-journey 五份 md+manifest+门/负控存档+schema/SKILL/总账关键行（卡文 §四）；禁用四措辞改说负控输入/对照输入/未被拦下的输入/门未覆盖的路径；0 字节存档不进 commit）；裁判输出 tee 进 evidence-g87-journey/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-G8-7-<日期>.md DoD-3 双段（4-B 零技术词 + 「旅程体验」勾选 = 签字位）+「本卡未证明什么」「台账待登记条目」各 ≥4；承重存档逐文件 git add；commit header ≤100 含批次标记且含卡号 CARD-G8-7；*.stderr* 不入库；不 push；P3 末张，commit 后工作树干净；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P3」。
```

### P5-B（CARD-REVIEW-CHAIN-PUSH-STATE）

> 📋 复制下面代码块粘进 `P5` 标签页的 /goal；完整卡文 `第十五批-goals/P5-B.md`。

```
完成 CARD-REVIEW-CHAIN-PUSH-STATE：每日复习推送链「三态谎报」修复——runner rc==2（Bark key 未配置）不写 last_result，昨天的「pushed」留在 state，两张总览页照样显示已推送；同卡收 last_error 截断、G6-8 模板冻结绑最终模板（Codex r5 HIGH-1）、交互壳同款降级徽标（默认实施，可退）；inbox_preview.py:430 +08:00 按默认不改（零代码登记）。为什么现在：合入=上线，G6-13 跨日旅程前用户可感面须先说实话。[BATCH-2026-09-18-第十五批 / CARD-REVIEW-CHAIN-PUSH-STATE]（6h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review（分支 card/p5-review，续跑起点 HEAD = 57d29464，venv symlink → card-v5-lance + backend/.env 就位）。第 0 分钟：核 pwd/分支：起点锚 57d29464（容忍判据见 §零.6）/`git status --porcelain` 空/merge-base 含 9c4e7e82；unit 红基线 evidence-b15/unit-red-baseline-9c4e7e82.txt grep -vc '^#' = 33（跑法与其第 3 行逐字同）；pyright 绝对路径 test -x；tests/regression 目录级落开工基线。前提：P5-A CARD-G6-9c-R3 已独立 commit 且工作树干净。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P5-B.md——runner :749-753 新枚举 generated_push_skipped_nokey/bark-nokey + review_overview._read_push_status 一行 elif + test_g6_9_boundary_matrix EXPECTED_HITS 1→2 必须同一 commit（登记门会红）；g68 冻结集 2 条不变、只加「_PAGE_TEMPLATE 单一绑定 + 运行期锚」两道门；inbox_preview.py 零 diff（用户当次裁 D-18 才改，未授权即 SKIP 登记）；pyright 保持 0 且禁 LEFTHOOK_EXCLUDE=python-typecheck。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，见卡文同字母段）：(a) 第 0 分钟；(b) 先红（结构 0 / EXPECTED_HITS 1 行 / 六门改前红 / g68 再绑定负控改前不抛）；(c) 缺陷① runner+读侧+登记门同 commit（默认：未配置 key = 降级 True + bark-nokey，待用户确认）；(d) last_error 截 200（utf-8 门之后）；(e) g68 单一绑定门 + 运行期锚 fail-closed；(e′) review_app 徽标三处同进同退；(f′) inbox_preview 零改动；(f) 结构对 + AST 冻结面 2==2；(g) 六道承重门（不连库）；(h) pyright 保持 0；(i) 六套件 + regression/unit 目录级只减；(j) 不改端点契约，commit 不含 openapi.json；(k) 负控两段；(l) 地盘九文件；(m) 现网只读；(n) Codex；(o) 独立 commit；(p) 未证明/待登记各 ≥4。
核心裁判：1. git --no-pager grep -c --no-color 'generated_push_skipped_nokey' -- runner/review_overview/boundary 改前 0/0/0 改后 ≥1/≥1/≥2 + EXPECTED_HITS 1→2 行；2. 六门显式文件 -q -rfE -k 定向贴 selected 数，改前红改后绿（runner skip_nokey / overview skipped_nokey+truncated / g68 binds_final_template / review_app push_degraded_badge / boundary 8 条）；3. 负控：删 runner 两行→runner 门红、注释 g68 Store 计数→冻结门红，git show HEAD:<path> 还原 + shasum 前后；4. pyright (cd backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ')=0 errors（改前改后，禁用 tail 取汇总）；5. git -c core.quotepath=false --no-pager diff --stat --no-color "$PREV" HEAD -- . ':(exclude)_bmad-output' ⊆ 九文件且 canvas-vault/ 零 diff；6. regression/unit 目录级 nodeid diff 只许 <（贴 W4 blocked= 行）。含 exit/cd 的块包 ( … )；ruff zsh 数组 + F821 锚。
硬边界：禁写 live vault；禁连 7691/7687；禁碰 fsrs_bridge.py/decay_beta.py；禁改 local_tz.py/display_tz.py/daily_review_pick.py（P5-A）、skill_portability_lint.py（P6）、conftest（P9）、main.py/models/security.py/lefthook.yml/openapi.json、别车道文件；不改 push 日志字面 skip-nokey、反转门/去重/兜底语义；不做五面对账（G6-13）；禁 stash / checkout-HEAD 式还原；批中不装包；不改台账；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（D-15；上限 5，第 5 轮仍有 HIGH 交主 session；审后改代码必再送一轮并在当前 HEAD 重跑全套承重裁判；首部按协议 §2.4；prompt 五分节最小读取面=本卡 diff+卡文 §四 列的行段+新测试；措辞只用负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；tee 进 evidence-review-chain-push-state/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-REVIEW-CHAIN-PUSH-STATE-<日期>.md DoD-3 双段（4-B 零技术词）+ 未证明/待登记各 ≥4；commit header ≤100 含批次标记且含卡号；*.stderr* 不入库；不 push；独立 commit 后继续 P5-C；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P5」。
```

### P5-C（CARD-G6-13）

> 📋 复制下面代码块粘进 `P5` 标签页的 /goal；完整卡文 `第十五批-goals/P5-C.md`。

```
完成 CARD-G6-13：J07 次日复习旅程开发门验收——用户在真实 vault 跨日走一遍（前一日答题→次日四桶→10 分钟回炉→snooze→完成→精确开板/节点），车道只读采集三面（页面/Markdown/API）对账排序，亲跑 G6-8 五面契约 0 分歧，验收单用户签字，证据落 docs/release-evidence/<rc>/journeys/J07/manifest.json 过校验器；为什么现在：G6-3..G6-8 已合却零 J07 证据，G6-8 自认「未跑完整复习链/未对现网对账」，P5-A/B 刚修完跨日边界与推送三态。[BATCH-2026-09-18-第十五批 / CARD-G6-13]（5h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review（分支 card/p5-review，续跑（起点 = 前卡 P5-B 末 commit），venv symlink + .env 就位），第 3/3 张。第 0 分钟：核 pwd/分支/HEAD=P5-B CARD-REVIEW-CHAIN-PUSH-STATE 末 commit（PREV=$(git rev-parse HEAD)）/status 空；unit 红基线 33 自证（grep -vc '^#' evidence-b15/unit-red-baseline-9c4e7e82.txt，跑法与其头第 3 行逐字同、不带 --ignore）；pyright 绝对路径 test -x 自证。前提：P5-B 已独立 commit 且工作树干净；先读 P5-B diff 确认 inbox tz 与 g68 已登记分歧现状。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P5-C.md——旅程写 live vault/live state 只由用户经产品 UI/skill 完成且须当次授权（口令「G6-13 授权 J07 窗口」；未授权 = 用户步骤全部 not_run + SKIP 登记 + 只做 fixture 半边，不能当隐含前提），车道只 GET/cp/rsync/shasum、⛔ 不 POST /overview/*、不写 live；预期零代码，地盘只新增 docs/release-evidence/<rc>/journeys/J07/**（默认 rc 自命名 dev-b15-p5、notes 写明非 RC；README/schema/校验器是 P10 地盘只读只跑）；evidence_level 按阶梯从低取（任一 not_run ⇒ E2/partial），not_run 不得写 pass。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟 + 核 §〇 file:line；(b) 先红（J07 目录 0、验收单 0、--all 只 1 份、契约在 PREV 上 PASS）；(c) 授权跨日旅程（只读采集 + 原库 hash 只在作答节点变）；(d) fixture 半边（契约四档 PASS + 副本三面对账 + tests/regression 目录级）；(e) 脱敏证据 + manifest 15 键 + 五桶偏差声明 + 验收单；(f) 结构判据 0→1 成对 + 验伪锚；(g) 校验器 rc=0 产物真验、契约门 24 passed；(h) 不改 backend/app；(i) 点名套件不回退 + unit 只减；(j) 不改端点不适用；(k) 负控两段；(l) 地盘核；(m) 现网只读 + 脱敏 grep 0；(n) Codex 1 轮绑最终 HEAD；(o) docs commit A/B；(p) 未证明/台账各 ≥4。
核心裁判：1. backend/.venv/bin/python backend/scripts/validate_release_manifest.py <J07 manifest> → rc=0 零 [S/[A 行（不加 --skip-artifact-verify）；--all 的 manifest 路径 1→2；2. g68_five_view_contract.py --now <带偏移> --tz <tz> 两时刻×两时区四次 verdict=PASS + test_g68_five_view_contract.py 显式路径 24 passed（核收集数）；3. rsync 只读 live → tmp，picker 面 --write 到副本、API 面按 g68 做法注入 VAULTS_ROOT+runner.BACKUPS 后调 review_overview._collect()（⛔ 不 import app.main）、Markdown 面副本 outputs/今日复习.md，比 (板,节点,桶) 集合与 ranked 板序 → three_face_equal=True 且集合 ≥1；4. 负控：板序对调→对账红、manifest sha256 翻位→校验器 rc=1 含 [A（trap git show HEAD:<path> 还原 + shasum 前后同）；5. 地盘 git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output' ⊆ {docs/release-evidence/<rc>/journeys/J07/**} + 验伪锚；6. tests/unit 目录级 diff 只许 <。git 输出一律 git --no-pager <cmd> --no-color；含 exit/cd 的块包 ( … ) 子 shell。
硬边界：禁写 live vault 与仓库树 backups/（live state）；禁连 7691/7687；禁碰 fsrs_bridge.py/decay_beta.py；禁改任何 .py / README / schema / 校验器 / openapi.json / conftest / 别车道文件（见卡文 §三）；不做 R-J07 RC 复跑、G8-6 dogfood，不代用户 POST snooze/done，不部署 live；禁 stash 类暂存与 checkout-HEAD 类还原；批中不装包；不改台账/手册/协议；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（D-15：零代码 1 轮，仍须绑 commit B；触及 .py 即转多轮上限 5；首部按协议 §2.4；prompt 五分节见卡文 §四；禁用四措辞改说负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；裁判输出 tee 进 evidence-g613/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-G6-13-J07-<日期>.md DoD-3 双段（4-B 零技术词）+「本卡未证明什么」「台账待登记条目」各 ≥4；commit header ≤100 含批次标记且含卡号 CARD-G6-13；*.stderr* 不入库；0 字节存档不入库；不 push；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P5」。
```

### P6-C（CARD-G8-3）

> 📋 复制下面代码块粘进 `P6` 标签页的 /goal；完整卡文 `第十五批-goals/P6-C.md`。

```
完成 CARD-G8-3：给 backend/scripts/vault_lint.py 加第二批四检查——annotation_coverage（**User：** 未答数与最老年龄）/ dlq_backlog（复制 traces.py:80-93 八条路径做文件级计数，⛔ 不 import app.*、不调端点）/ backup_freshness（backup.log 最近 OK: 时间）/ recap_unsourced（子进程复用 recap_scan.py）；输入面不可用报 degraded（warn + details.degraded=true，不伪装）；四反例先红后绿；现网只读跑一次。为什么现在：四项输入面在位却无人接进生产门，G8-10 要引用本卡输出。[BATCH-2026-09-18-第十五批 / CARD-G8-3]（5h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w（分支 card/p6-skills-w，续跑起点 HEAD = 5e305b28，venv symlink + .env 就位），第 3/4 张（续跑）。第 0 分钟：核 pwd/分支：起点锚 5e305b28（容忍判据见 §零.6）/`git status --porcelain` 空；unit 红基线 33 自证（evidence-b15/unit-red-baseline-9c4e7e82.txt）；pyright 绝对路径 test -x；两目标文件对 9c4e7e82 diff 空；tests/unit 目录级落开工基线（不带 --ignore）。前提：P6-B CARD-HARNESS-TREE-PARSE-R2 已独立 commit 且工作树干净。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P6-C.md——vault_lint.py 保持「import 零重依赖」（grep -c '^from app\|^import app' 恒 0，DLQ 八条只复制口径 + 单测子进程同源锁）；degraded = warn + details.degraded=true，不加第四种 status、不改三旧检查/exit_code/report_to_json/render_text；零写铁律（新代码只许 open("rb")/stat/iterdir/read_text；live vault / 主干树 _bmad-output / 现网 backups/neo4j 只读并贴前后 digest）。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟 + 核 §〇；(b) 先红（结构 0/3/75/0 + 四反例 4 selected 全 FAILED + 三旧检查对照输入）；(c) 四检查函数各带 degraded 分支；(d) 接线（CHECKS +4、run_checks 参数、main 五新参、_EPILOG）；(e) ≥16 新 test（反例/干净/degraded/同源锁两层/--help/live）；(f) 结构 0→4、3→7、DLQ 键 8、零 app import；(g) 零 mock 零库；(h) 不改 backend/app，pyright 不适用；(i) 点名套件 + tests/unit 只减；(j) 不适用；(k) 负控 ≥2 段各只拆一层；(l) 地盘恰两文件；(m) 现网只读；(n) Codex 多轮；(o) 单卡 commit；(p) 未证明/待登记各 ≥4。
核心裁判：1. 结构 grep -cE '^    "(annotation_coverage|dlq_backlog|backup_freshness|recap_unsourced)":' 0→4 + grep -c '^def check_' 3→7 + app import 恒 0（验伪锚：副本追加一键 → 1）；2. 四反例 -k 'counterexample and (annotation or dlq or backup or recap)' 改前 4 FAILED / 改后 0，收集数必核；3. DLQ 同源锁：AST 键集相等 + 子进程 import traces.BACKLOG_FILES 解析后 8 条绝对路径逐条相等（cwd=backend，前后 git status --porcelain 空，失败 fail 不 skip）；4. 负控四段：恒 True 已答 / 恒 0 行数 / 恒新鲜 / value>10**9，各只红指定反例，trap 用 git show HEAD:<path> 还原、shasum 前后同；5. 现网只读 --vault $LIVE/canvas-vault --bmad-root $MAIN/_bmad-output --backend-dir $MAIN/backend --backups-dir $LIVE/backups/neo4j --recap-scan <live 副本> --json → live-lint-after-<ts>.json，三处 digest 前后同，三旧检查结论逐字同；6. tests/unit diff 只许 <；ruff zsh 数组 + F821 探针。git 输出一律 git --no-pager <cmd> --no-color；含 exit/cd 的块包 ( … )。
硬边界：禁写 live vault / 主干树 _bmad-output / 现网 backups；禁连 7691/7687/7692；禁碰 fsrs_bridge.py / decay_beta.py / models/** / main.py / security.py / lefthook.yml；不改 traces.py（C2-02 唯一写者，只复制口径）/ recap_scan.py / backup-neo4j.sh / skill_portability_lint.py / conftest / 别车道文件；不做 G8-2c 复跑、G8-10 归属、D-41/D-42 对账；不下沉 BACKLOG_FILES、不加 --fix；禁用 stash / 禁用 checkout 还原；批中不装不升包；不改台账；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（上限 5 轮，第 5 轮仍有 HIGH 交主 session；审后改代码必再送一轮并在当前 HEAD 重跑全套承重裁判，存档带 -rN；首部按协议 §2.4；prompt 五分节最小读取面按卡文 §四；措辞用负控输入/对照输入/未被拦下的输入/门未覆盖的路径；0 字节存档不入 commit）；裁判输出 tee 进 evidence-g83/（末行 rc=$pipestatus[1]）；验收单 UAT-CARD-G8-3-<日期>.md DoD-3 双段 + 终态字段收工重算 + 未证明/待登记各 ≥4；commit header ≤100 含批次标记与卡号 CARD-G8-3；*.stderr* 不入库；不 push；独立 commit 后接 P6-D；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P6」。
```

### P6-D（CARD-G8-10）

> 📋 复制下面代码块粘进 `P6` 标签页的 /goal；完整卡文 `第十五批-goals/P6-D.md`。

```
完成 CARD-G8-10：把 G8-9 统一验收门底账 §2.13 observability「预留行」填成故障可见面逐链归属表——检索 / 复习 / 部署 / skill / 投影 freshness / DLQ 六链，每链指认归属卡 + 露出面 file:line + 逐字判据文句 + 机械判据 nodeid，缺口只登记为附加判据提名；OBJ-07 五项交付（CI / observability / backup-restore / benchmark / dogfood）逐一指认归属卡；§3 YAML :227 同步 + §5 append。为什么现在：OBJ-07 五项里唯一无归属的一项，且本车道 P6-C 刚落的 DLQ 只读检查正好补齐第六链露出面。[BATCH-2026-09-18-第十五批 / CARD-G8-10]（2h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w（分支 card/p6-skills-w，续跑（起点 = 前卡 P6-C 末 commit），venv symlink + .env 就位）。第 0 分钟：核 pwd/分支/HEAD = P6-C CARD-G8-3 末 commit/git status 空；unit 红基线 evidence-b15/unit-red-baseline-9c4e7e82.txt 自证 33，开工 tests/unit 目录级跑法与基线头第 3 行逐字同；pyright 绝对路径 test -x 自证（本卡不改 backend/app）；ls evidence-g83 实测 P6-C 存档在不在位。前提：P6-C 已独立 commit 且工作树干净；本卡零代码纯台账、不需用户授权、不连库、live 只读。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P6-D.md——①只改一份文件 _bmad-output/implementation-artifacts/2026-08-28-G8-9-统一验收门底账.md（:160 预留行 + :227 YAML + §5 append），不动 :6 基线行 / :156 source_criterion / 其余十二维，总账 v2 与台账只读；②「判据文句」逐字来自已合入主干的代码/测试/脚本注释/验收单（不得引卡文、草案、手册或本卡自己的话），owner 只引总账 v2 有 #### 档案节且不在 §五 DONE 的卡，outcome 默认维持 not_yet（§1 fail-closed；已知两缺口：检索 UI 半边 6337e320 改动 0 frontend 文件 / skill 链 inbox_preview.py degraded·unavailable 0 命中）；③核对脚本 evidence-g810/check_g810_refs.py 先红（chains<6）后绿 + 验伪锚 ref-missing。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟 + 核 §〇 file:line（含两勘误：BACKLOG_FILES 实测 :80-93 八项；复习链锚 G6-9b 非 G6-7）；(b) 先红（§2.13 表 3 行、脚本 rc=1 红在 chains<6）；(c) 六链表 7 列 ≥6 行；(d) OBJ-07 五项子表 5 行；(e) YAML :227 同步 + §5 append（not_yet→not_yet / none→partial）；(f) 脚本改前红改后绿 + 验伪锚；(g) 每链 nodeid --collect-only 收集数 ≥1；(h) pyright 不适用；(i) test_vault_lint.py 开工/收工同 + tests/unit 目录级只减；(j) 不适用；(k) 负控三段；(l) 地盘核为空；(m) 现网只读；(n) Codex 1 轮；(o) ≤2 commit；(p) 本卡未证明什么/台账待登记各 ≥4。
核心裁判：1. python3 $CHK --ledger $LED --root $(pwd)：改前 rc=1 含 chains<6、改后 rc=0、验伪锚副本改一处 path:line 为不存在 → rc=1 含 ref-missing；2. nodeid 可解引用：(cd backend && … --collect-only <文件> -k <用例>) 逐条 collected 1（no tests collected/rc=5 不是绿）；3. 负控三段（trap 用 git show HEAD:<底账路径> > <底账路径> 还原、shasum 前后同）：改路径→ref-missing、改 :227 outcome→yaml-mismatch、改文句→quote-miss；4. 地盘 git --no-pager diff --stat --no-color <P6-C 末 commit> HEAD -- . ':(exclude)_bmad-output' 为空（去掉 exclude 后含底账路径 = 验伪锚）；5. tests/unit 目录级 nodeid diff 只许 <；6. grep -c -e fsrs_bridge -e decay_beta 底账 = 0、grep -c 7691 = 0。git 输出一律 --no-color；含 exit/cd 的块包 ( … ) 子 shell；tee 末行 rc=$pipestatus[1]。
硬边界：零代码——任何 backend/**、canvas-vault/**、scripts/** 改动即越界先撤回；禁写 live vault；禁连 7691/7687；禁碰 fsrs_bridge.py/decay_beta.py/models/**/main.py/conftest；不改总账 v2、台账、手册、P6-A/B/C 存档；不实现任何监控/露出代码；缺口只提名不冒充达成；禁用暂存栈与从 HEAD 检出单文件式还原；批中不装不升包；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（零代码卡 1 轮；该轮报 BLOCKER/HIGH 并改底账则再送一轮带 -rN，上限 5；首部按协议 §2.4；0 字节存档不入 commit；prompt 五分节最小读取面 = 底账 diff + §1/§2.13/§3/§5 行段 + 总账 v2 :556-561 + 六链源行段 + 核对脚本 + 存档；禁用四措辞改说负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；裁判输出 tee 进 evidence-g810/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-G8-10-<日期>.md DoD-3 双段（4-B 零技术词）+「本卡未证明什么」「台账待登记条目」各 ≥4 + 终态字段收工重算；commit ≤2 个、header ≤100 含批次标记且含卡号 CARD-G8-10、type docs；*.stderr* 不入库；不 push；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P6」。
```

### P7-B（CARD-G5-10）

> 📋 复制下面代码块粘进 `P7` 标签页的 /goal；完整卡文 `第十五批-goals/P7-B.md`。

```
完成 CARD-G5-10：board-split 执行侧（scripts-only，不加 SKILL.md）——新增 split_apply.py 消费 split-preview-<board>.json + stable id，确认后原子创建 节点/ 派生 md（frontmatter 含 source_board + split_stable_id，真 scan_vault 判 derived 不落孤儿），可选 wikilink callout 逐行确认（默认关），复用 P7-A 备份 + undo journal；为什么现在：G5-3 定版契约后 split_preview.py 仍只读（无 apply 模式），用户看得见拆分预览却拆不了，G5-11/R-J03/R-J08 全卡在它。[BATCH-2026-09-18-第十五批 / CARD-G5-10]（8h）
车道：NEW /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x（分支 card/p7-skills-x，续跑起点 HEAD = df05f9f8，venv+env 就位）。第 0 分钟：pwd/分支：起点锚 df05f9f8（容忍判据见 §零.6）/`git status --porcelain` 空（r6 已归档 df05f9f8）；BASE=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b15/unit-red-baseline-9c4e7e82.txt 的 grep -vc '^#' = 33；pyright 绝对路径 test -x；undo_journal.py（P7-A 产物）在位；tests/unit + tests/skills 目录级开工落基线（跑法同基线头第 3 行）；零写者 shasum pre 档。前提：P7-A CARD-G5-7 已独立 commit 且工作树干净，之后串 P7-C CARD-G5-12。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P7-B.md——① identity_ambiguous 候选拒绝持久化 split_stable_id、vault_fingerprint 与现场重算不符即过期拒绝，两门零产物；② 不加 SKILL.md（矩阵登记 planned，加即 T3 FAIL）、不改 split_preview.py / board_manifest_service.py / skill_portability_lint.py，零物理删除（AST 门：删除类调用只在 undo 函数内）；③ 真实板全链需用户当次授权，未授权即 SKIP 登记、live 只读。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟 + 核 §〇；(b) 先红；(c) 准入五门 + 节点 frontmatter；(d) O_EXCL 原子创建 + journal intent→done + undo 全树逐字节还原 + 中断重跑幂等；(e) --insert-callout 逐行确认默认关（形态照 split_preview.py:1002）；(f) 结构判据成对 + AST 删除门；(g) 新测试 ≥12 条全走真 split_preview.py 与真 scan_vault；(h) 不改 backend/app，pyright 不适用；(i) 点名套件 + tests/skills 目录级 + tests/unit 只减；(j) 不改端点；(k) 负控 ≥2 段；(l) 地盘核；(m) 现网只读；(n) Codex 多轮；(o) 提交；(p) 未证明/台账各 ≥4。
核心裁判：1. test_g5_10_split_apply.py 先红（全 FAILED、收集 ≥12）→ 改后全 passed，-k manifest selected ≥1 且断言 role == "derived" 且不在 orphans（验伪锚：删 source_board 后判孤儿）；2. AST 删除门 non_undo_calls= 0 且 undo_calls ≥1（副本插 os.remove 变 1）；3. 负控三段（歧义放行 / fingerprint 恒通过 / journal 先写后记 → 各自用例红）trap git show HEAD:<path> 还原 + shasum 前后同；4. tests/skills 目录级 + 两份 board_manifest 测试收工同开工，tests/unit nodeid diff 只 <；5. 地盘 git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output' ⊆ {两新文件, undo_journal.py 仅末尾追加}；6. grep -e 7691 -e 7687 -e bolt:// 于两新文件 = 0 + 零写者 shasum pre/post 同。git 一律 --no-color；ruff zsh 数组 + F821 探针；-k 核收集数；含 cd 的块包 ( … )。
硬边界：只改 3 文件（两 NEW + undo_journal.py 只追加，P7-A 测试收工必绿）；不加 SKILL.md；不改 split_preview.py / board_manifest_service.py / models/board_manifest.py / skill_portability_lint.py / inbox_preview.py / inbox_apply.py / sync_board_concepts.py / conftest；不写 Concepts 托管块、不写 Neo4j/LanceDB/backend；禁写 live vault、禁连 7691/7687、禁碰 fsrs_bridge.py/decay_beta.py；禁 stash 类暂存与 checkout HEAD -- 类还原；批中不装包；不改台账/手册；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（上限 5 轮，第 5 轮仍有 HIGH 交主 session；审后改代码必再送一轮并在当前 HEAD 重跑全套承重裁判；存档带 -rN、首部按协议 §2.4；prompt 五分节见卡文 §四；措辞用负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；tee 进 evidence-g510/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-G5-10-<日期>.md DoD-3 双段（终态字段收工重算）+「本卡未证明什么」「台账待登记条目」各 ≥4；commit header ≤100 含批次标记且含卡号 CARD-G5-10；0 字节存档不入 commit；*.stderr* 不入库；不 push；独立 commit 后继续 P7-C；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P7」。
```

### P7-C（CARD-G5-12）

> 📋 复制下面代码块粘进 `P7` 标签页的 /goal；完整卡文 `第十五批-goals/P7-C.md`。

```
完成 CARD-G5-12：sync_board_concepts.py sentinel 区间「连坐删除用户文字」收口——写入方枚举清单证据包（四层：托管块改写者唯一 / 字面量发射者 2 / 段内游离行写者 1 / 只读消费者 4）+ h1/h1b 回归测试加用户文字区 sha256 前后逐字节断言为承重判据 + helper 敏感性自测 + 回归测试显式路径进裁判命令；脚本本体零改动，§三(b) 合同点不并入（G2-2/G4-2 语义）。为什么现在：缺陷已在 867112af/334f316a 修复但门只到子串级，计划书 L66 仍 STILL-OPEN、G8-9 底账 §8 挂 G5-12 无证据。[BATCH-2026-09-18-第十五批 / CARD-G5-12]（2h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x（分支 card/p7-skills-x，续跑（起点 = 前卡 P7-B 末 commit），venv symlink + backend/.env 就位），第 3/3 张（末卡）。第 0 分钟：核 pwd/分支/HEAD=P7-B CARD-G5-10 末 commit（此刻一次取 PREV=$(git rev-parse HEAD) 写进 evidence，之后不重取）/status 空；unit 红基线 33 自证（grep -vc '^#' evidence-b15/unit-red-baseline-9c4e7e82.txt，跑法同其头第 3 行、不带 --ignore）；pyright 绝对路径 test -x；sync_board_concepts.py shasum = 282b7a96…。前提：P7-B 已独立 commit 且工作树干净；本卡不需用户当次授权。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P7-C.md——① 脚本本体零改动（hash 门若在当前脚本上红 ⇒ 停下交主 session，自改会打红 P6 地盘 skill_portability_lint.py:3217 digest）；② _user_region 只排除四类机器行（sentinel 头只丢 --> 之前部分、尾巴保留 / _CONCEPT_LINE 行 / _EMPTY_HINT），多排一行 = 门假绿，且必须有敏感性自测；③ 先红只来自 (k) 负控输入，验收单不得写「本卡修复了连坐删除」。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文同字母段）：(a) 第 0 分钟 + PREV 钉值 + 核 §〇；(b) 先红（hashlib/_user_region 计数 0、证据包不存在、回归门开工 40 passed）；(c) 证据包 evidence-g512/writers-census.md 六节；(d) h1/h1b sha256 断言 + 验伪锚 + 自测四分支；(e) 回归测试进裁判命令；(f) 结构 0→≥8、测试名 25→26；(g) 收工 41 passed/collected 41；(h) 不改 backend/app；(i) 点名套件 + regression/skills/unit 目录级只减；(j) 不改端点不适用；(k) 负控两段；(l) 地盘恰 1 文件；(m) 现网只读 + 零写者 shasum；(n) Codex 多轮；(o) 单 commit；(p) 未证明/台账各 ≥4。
核心裁判：1. ( cd backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider -rfE tests/regression/test_sync_board_concepts.py ) 开工 40 → 收工 41 passed，核 collected；2. 负控：段① :456 去 `- (protected or set())` ⇒ h1b[begin_note_line] FAILED 于 hexdigest 断言、[end_sentinel] passed；段② :342 `if tail.strip():`→`if False:` ⇒ 两 param FAILED、h1 passed；trap `git show HEAD:<path> > <path>` 还原，跑前跑后 shasum = 282b7a96…；3. census git -c core.quotepath=false --no-pager grep -c --no-color -F 'AUTO-GENERATED' -- . ':(exclude)_bmad-output' ':(exclude)*.md' → 11 文件 + 验伪锚；4. 结构 grep -c -e hashlib -e _user_region 改前 0/改后 ≥8；5. 地盘 git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output' 恰 1 文件；ruff zsh 数组 files=1 rc=0 + 仓内 F821 探针 rc=1；6. 目录级 nodeid diff 只许 <。git 输出一律 --no-color；含 exit/cd 的块包 ( … ) 子 shell；变异窗口不与目录级长跑重叠。
硬边界：禁写 live vault；禁连 7691/7687；禁碰 fsrs_bridge.py/decay_beta.py（收官贴 shasum）；禁改 sync_board_concepts.py 本体 / 三份 SKILL.md 调用点 / skill_portability_lint.py、vault_lint.py（P6）/ 四个只读枚举文件（卡文 §三）/ exam_service.py（P8）/ verification_service.py / backend/app/** / conftest（P9）/ lefthook.yml / openapi.json / P7-A、P7-B 文件；不并入 §三(b)；不加 SKILL.md；禁 stash 类暂存与 checkout-HEAD 类还原；批中不装包；不改台账/手册；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（有代码改动 ⇒ 上限 5 轮；审后改代码必再送一轮并在当前 HEAD 重跑 (g)(i)(k)(l)；首部按协议 §2.4；prompt 五分节最小读取面见卡文 §四；禁用四措辞改说负控输入/对照输入/未被拦下的输入/门未覆盖的路径）；裁判输出 tee 进 evidence-g512/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-G5-12-<日期>.md DoD-3 双段（4-B 零技术词）+「本卡未证明什么」「台账待登记条目」各 ≥4；commit header ≤100 含批次标记且含卡号 CARD-G5-12；*.stderr* 不入库；0 字节存档不入库；不 push；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P7」。
```

### P10-C（CARD-R-SLO）

> 📋 复制下面代码块粘进 `P10` 标签页的 /goal；完整卡文 `第十五批-goals/P10-C.md`。

```
完成 CARD-R-SLO：起草 versioned SLO manifest 单文件 docs/release-evidence/slo-manifest.yaml（首次索引 / RAG cold·warm p95 / Review 首屏·重建 p95 / Graphiti ACK·replay / 恢复时间；schema 字段本卡锁定：机器/OS/模型版本/数据规模·SHA/冷热/并发/时区/种子/重复次数/统计量/裁决人）+ 每项可复跑采集命令 + 一次现网只读实测 + 用户签字锁版位 + README slo.manifest_revision 反向引用；为什么现在：校验器 S9 要求 E3 引用本卡 revision（README :94/:152），G8-8/G2-10/G4-14/G6-11/R-J0x 全等它，没有它全批 J manifest 停在 E2。[BATCH-2026-09-18-第十五批 / CARD-R-SLO]（6h）
车道：/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs（分支 card/p10-docs，续跑起点 HEAD = a03f0ce3，venv symlink + backend/.env 就位），本车道第 3/3 张（续跑）。第 0 分钟：pwd/分支：起点锚 a03f0ce3（容忍判据见 §零.6）/`git status --porcelain` 空/merge-base 含 9c4e7e82；unit 红基线 evidence-b15/unit-red-baseline-9c4e7e82.txt 非注释 33；pyright 绝对路径 test -x；backend/.venv/bin/python -c "import yaml" 自证（失败停下、不装包）；docker ps 只读存档（8011 不在 ⇒ 现网实测整段 not_measured，不起停容器）。前提：P10-B 已独立 commit 且工作树干净。
⛔ 开工第一件事：通读并逐条执行卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P10-C.md——① 零代码：不改 manifest.schema.json/ 校验器 / J08 示例件，不建任何 .py；② 现网只读：8011 只打 GET + /rag/query 读查询，7691 只经 8011 或白名单两条 execute_read 语句，写端点一个不打，写侧四项如实 not_measured + 原因 + owner 卡，禁填估计值；③ 锁版只在用户口令「R-SLO 授权锁版」+ 逐项裁定后写 status: locked / r2，未授权一律 draft + SKIP 登记。协议 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md；手册 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-09-18-第十五批开跑手册-11车道33卡.md（§零/§一/§四）。
完成条件（AND，细节见卡文）：(a) 第 0 分钟 + 核 §〇 file:line；(b) 先红（slo-manifest 0 命中、yaml 不存在、README 0 引用、revision 对照脚本红）；(c) yaml ≥8 项指标 + 固定键 + export_shape 五键；(d) 现网只读实测（4 项 n=20、重建 n=5）；(e) README 小节 + 锁版规则 + 签字位；(f) 结构判据成对落档 + 验伪锚；(g) 消费契约门（导出五键塞 tmp J08 过校验器）+ 147 passed；(h) 不改 backend/app；(i) 套件不回退 + tests/unit 只减；(j) 不改端点；(k) 负控两段；(l) 地盘核；(m) 现网只读 + 脱敏 0；(n) Codex 1 轮绑最终 HEAD；(o) commit A/B（授权时 C 再送一轮）；(p) 未证明/台账各 ≥4。
核心裁判：1. test -e docs/release-evidence/slo-manifest.yaml rc 1→0；grep -c slo-manifest.yaml README 0→≥1；2. revision 对照脚本 → rev_check=OK + 验伪锚红；3. backend/.venv/bin/python backend/scripts/validate_release_manifest.py $TMP/j08.json --skip-artifact-verify → rc=0 且零 [S 行；4. curl -w '%{http_code} %{time_total}' 各 20 次，quantiles(n=20)[18] 取 p95，n=20 全 200，live outputs/今日复习.json 前后 shasum 同；5. 负控 trap 用 git show HEAD:<path> > <path> 还原、前后 shasum 同、红在指定断言；6. git --no-pager diff --stat --no-color $PREV HEAD -- . ':(exclude)_bmad-output' 只列 yaml + README 且 README 的 - 行数 = 0，验伪锚去掉 exclude 多出 _bmad-output/。git 输出一律 --no-color；含 exit/cd 的块包 ( … ) 子 shell；tee 末行 rc=$pipestatus[1]。
硬边界：禁写 live vault 与仓库树 backups/；7691 只读、禁 7687、7692 不用、不 import app.main；禁碰 fsrs_bridge.py/decay_beta.py；禁改 schema / 校验器 / J08 / P10-A ledger / P10-B 骨架与 freeze 脚本/ openapi.json / conftest / 别车道文件；不建 runner（G4-14/G8-8）、不做 J manifest；key 与密码不进 evidence，yaml 零 /Users/ 绝对路径；禁 stash 类暂存 / checkout-HEAD 类还原；批中不装包；不改台账/手册/协议；不 push。
收尾：Codex glm-5.3 max 多轮直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（零代码 1 轮仍须绑最终 HEAD；锁版 commit C 后再送 -r2；触及 .py 转多轮上限 5；首部按协议 §2.4；prompt 五分节最小读取面 = 本卡 diff + yaml 全文 + README 新增段 + schema :475-530 + 校验器 :76-77/:430-475 + evidence-rslo 存档 + 验收单；禁用四措辞改说负控输入/对照输入/未被拦下的输入/门未覆盖的路径；0 字节存档不入 commit）；裁判输出 tee 进 evidence-rslo/（.txt 末行 rc=$pipestatus[1]）；验收单 UAT-CARD-R-SLO-<日期>.md DoD-3 双段 + 锁版签字位 +「本卡未证明什么」「台账待登记条目」各 ≥4；commit header ≤100 含批次标记且含卡号 CARD-R-SLO；*.stderr* 不入库；不 push；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P10」。
```



### 补审-CARD-G4-5（CARD-G4-5 · 接 -r1· 补审）

> 📋 复制下面代码块粘进 `P1` 标签页的 /goal；卡文 `第十五批-goals/P1-C.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G4-5（车道 card-p1-storage，接 -r1）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（写读组族收敛到单一 builder），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G4-5]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p1-storage、分支、起点锚 c33240fa（`git merge-base --is-ancestor c33240fa HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G4-5-r1.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P1-C.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color d4c19c06 bbd2a9fb -- backend/app/graphiti/group_id_compat.py backend/app/services/episode_worker.py backend/app/services/memory_service.py backend/tests/unit/test_group_family_builder.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G4-5-r1.md 2> _bmad-output/审查/zcode-review-CARD-G4-5-r1.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 bbd2a9fb / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color bbd2a9fb HEAD -- backend/app/graphiti/group_id_compat.py backend/app/services/episode_worker.py backend/app/services/memory_service.py backend/tests/unit/test_group_family_builder.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G4-5-2026-09-19.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=d4c19c06 · 审SHA=bbd2a9fb · 文件集 = backend/app/graphiti/group_id_compat.py backend/app/services/episode_worker.py backend/app/services/memory_service.py backend/tests/unit/test_group_family_builder.py；存档 `zcode-review-CARD-G4-5-r1.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g4-5` 新建）；单 commit（message 含 CARD-G4-5）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P1」。
```

### 补审-CARD-STAGING-WRITERS-BOUNDED（CARD-STAGING-WRITERS-BOUNDED · 接 -r6· 补审）

> 📋 复制下面代码块粘进 `P2` 标签页的 /goal；卡文 `第十五批-goals/P2-B.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-STAGING-WRITERS-BOUNDED（车道 card-p2-outbox，接 -r6）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（暂存 JSONL 写侧有界化），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-STAGING-WRITERS-BOUNDED]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p2-outbox、分支、起点锚 d2ebf694（`git merge-base --is-ancestor d2ebf694 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-STAGING-WRITERS-BOUNDED-r6.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P2-B.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color ac0993b4 d2ebf694 -- backend/app/core/failed_writes_constants.py backend/app/core/failure_counters.py backend/app/services/agent_service.py backend/app/services/episode_worker.py backend/app/services/fallback_sync_service.py backend/app/services/memory_service.py backend/tests/unit/test_staging_writers_bounded.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md 2> _bmad-output/审查/zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 d2ebf694 / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color d2ebf694 HEAD -- backend/app/core/failed_writes_constants.py backend/app/core/failure_counters.py backend/app/services/agent_service.py backend/app/services/episode_worker.py backend/app/services/fallback_sync_service.py backend/app/services/memory_service.py backend/tests/unit/test_staging_writers_bounded.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-STAGING-WRITERS-BOUNDED-2026-09-18.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=ac0993b4 · 审SHA=d2ebf694 · 文件集 = backend/app/core/failed_writes_constants.py backend/app/core/failure_counters.py backend/app/services/agent_service.py backend/app/services/episode_worker.py backend/app/services/fallback_sync_service.py backend/app/services/memory_service.py backend/tests/unit/test_staging_writers_bounded.py；存档 `zcode-review-CARD-STAGING-WRITERS-BOUNDED-r6.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-staging-writers-bounded` 新建）；单 commit（message 含 CARD-STAGING-WRITERS-BOUNDED）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P2」。
```

### 补审-CARD-G3-8（CARD-G3-8 · 接 -r4· 补审）

> 📋 复制下面代码块粘进 `P4` 标签页的 /goal；卡文 `第十五批-goals/P4-B.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G3-8（车道 card-p4-fsrs，接 -r4）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（next_review 对账迁移器），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G3-8]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs、分支、起点锚 858582d3（`git merge-base --is-ancestor 858582d3 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G3-8-r4.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P4-B.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color 49e42626 ce81e5fa -- backend/scripts/migrate_next_review_g38.py backend/tests/unit/test_migrate_next_review_g38.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G3-8-r4.md 2> _bmad-output/审查/zcode-review-CARD-G3-8-r4.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 ce81e5fa / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color ce81e5fa HEAD -- backend/scripts/migrate_next_review_g38.py backend/tests/unit/test_migrate_next_review_g38.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G3-8-2026-09-19.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=49e42626 · 审SHA=ce81e5fa · 文件集 = backend/scripts/migrate_next_review_g38.py backend/tests/unit/test_migrate_next_review_g38.py；存档 `zcode-review-CARD-G3-8-r4.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g3-8` 新建）；单 commit（message 含 CARD-G3-8）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P4」。
```

### 补审-CARD-G8-4（CARD-G8-4 · 接 -r2· 补审）

> 📋 复制下面代码块粘进 `P4` 标签页的 /goal；卡文 `第十五批-goals/P4-C.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G8-4（车道 card-p4-fsrs，接 -r2）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（复习完成率周汇总（只读）），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G8-4]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p4-fsrs、分支、起点锚 858582d3（`git merge-base --is-ancestor 858582d3 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G8-4-r2.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P4-C.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color f05f7a58 9f852a76 -- backend/tests/unit/test_review_weekly_report.py scripts/review_weekly_report.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G8-4-r2.md 2> _bmad-output/审查/zcode-review-CARD-G8-4-r2.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 9f852a76 / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color 9f852a76 HEAD -- backend/tests/unit/test_review_weekly_report.py scripts/review_weekly_report.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G8-4-2026-09-19.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=f05f7a58 · 审SHA=9f852a76 · 文件集 = backend/tests/unit/test_review_weekly_report.py scripts/review_weekly_report.py；存档 `zcode-review-CARD-G8-4-r2.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g8-4` 新建）；单 commit（message 含 CARD-G8-4）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P4」。
```

### 补审-CARD-G6-9c-R3（CARD-G6-9c-R3 · 接 -r3· 补审）

> 📋 复制下面代码块粘进 `P5` 标签页的 /goal；卡文 `第十五批-goals/P5-A.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G6-9c-R3（车道 card-p5-review，接 -r3）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（local_tz 解析器 R3 重写），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G6-9c-R3]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review、分支、起点锚 57d29464（`git merge-base --is-ancestor 57d29464 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G6-9c-R3-r3.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P5-A.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color 9c4e7e82 d062e2b1 -- backend/app/api/v1/endpoints/review_overview.py backend/app/core/display_tz.py backend/openapi.json backend/tests/regression/test_daily_review_pick.py backend/tests/regression/test_daily_review_run.py backend/tests/regression/test_g6_9_boundary_matrix.py backend/tests/regression/test_g6_9c_single_tz_source.py backend/tests/regression/test_local_tz_negctl_r3.py backend/tests/unit/test_review_overview.py scripts/daily_review_pick.py scripts/local_tz.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G6-9c-R3-r3.md 2> _bmad-output/审查/zcode-review-CARD-G6-9c-R3-r3.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 d062e2b1 / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color d062e2b1 HEAD -- backend/app/api/v1/endpoints/review_overview.py backend/app/core/display_tz.py backend/openapi.json backend/tests/regression/test_daily_review_pick.py backend/tests/regression/test_daily_review_run.py backend/tests/regression/test_g6_9_boundary_matrix.py backend/tests/regression/test_g6_9c_single_tz_source.py backend/tests/regression/test_local_tz_negctl_r3.py backend/tests/unit/test_review_overview.py scripts/daily_review_pick.py scripts/local_tz.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G6-9c-R3-2026-09-18.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=9c4e7e82 · 审SHA=d062e2b1 · 文件集 = backend/app/api/v1/endpoints/review_overview.py backend/app/core/display_tz.py backend/openapi.json backend/tests/regression/test_daily_review_pick.py backend/tests/regression/test_daily_review_run.py backend/tests/regression/test_g6_9_boundary_matrix.py backend/tests/regression/test_g6_9c_single_tz_source.py backend/tests/regression/test_local_tz_negctl_r3.py backend/tests/unit/test_review_overview.py scripts/daily_review_pick.py scripts/local_tz.py；存档 `zcode-review-CARD-G6-9c-R3-r3.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g6-9c-r3` 新建）；单 commit（message 含 CARD-G6-9c-R3）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P5」。
```

### 补审-CARD-HARNESS-TREE-PARSE-R2（CARD-HARNESS-TREE-PARSE-R2 · 接 -r6· 补审）

> 📋 复制下面代码块粘进 `P6` 标签页的 /goal；卡文 `第十五批-goals/P6-B.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-HARNESS-TREE-PARSE-R2（车道 card-p6-skills-w，接 -r6）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（harness 树解析 R2 收口），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-HARNESS-TREE-PARSE-R2]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p6-skills-w、分支、起点锚 5e305b28（`git merge-base --is-ancestor 5e305b28 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-HARNESS-TREE-PARSE-R2-r6.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P6-B.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color a05732c9 43bea775 -- backend/tests/regression/test_g3_2_review_ledger.py backend/tests/skills/skill_portability_lint.py backend/tests/skills/test_harness_tree_parse_r2.py canvas-vault/.claude/skills/quiz-answer/SKILL.md` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.md 2> _bmad-output/审查/zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 43bea775 / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color 43bea775 HEAD -- backend/tests/regression/test_g3_2_review_ledger.py backend/tests/skills/skill_portability_lint.py backend/tests/skills/test_harness_tree_parse_r2.py canvas-vault/.claude/skills/quiz-answer/SKILL.md` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-HARNESS-TREE-PARSE-R2-2026-09-18.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=a05732c9 · 审SHA=43bea775 · 文件集 = backend/tests/regression/test_g3_2_review_ledger.py backend/tests/skills/skill_portability_lint.py backend/tests/skills/test_harness_tree_parse_r2.py canvas-vault/.claude/skills/quiz-answer/SKILL.md；存档 `zcode-review-CARD-HARNESS-TREE-PARSE-R2-r6.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-harness-tree-parse-r2` 新建）；单 commit（message 含 CARD-HARNESS-TREE-PARSE-R2）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P6」。
```

### 补审-CARD-G5-7（CARD-G5-7 · 接 -r7· 补审）

> 📋 复制下面代码块粘进 `P7` 标签页的 /goal；卡文 `第十五批-goals/P7-A.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G5-7（车道 card-p7-skills-x，接 -r7）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（clear-inbox 执行侧 + undo journal），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G5-7]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x、分支、起点锚 df05f9f8（`git merge-base --is-ancestor df05f9f8 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G5-7-r7.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P7-A.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color 9c4e7e82 10a2799e -- backend/tests/skills/test_g5_7_inbox_apply.py canvas-vault/.claude/scripts/undo_journal.py canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G5-7-r7.md 2> _bmad-output/审查/zcode-review-CARD-G5-7-r7.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 10a2799e / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color 10a2799e HEAD -- backend/tests/skills/test_g5_7_inbox_apply.py canvas-vault/.claude/scripts/undo_journal.py canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G5-7-2026-09-18.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=9c4e7e82 · 审SHA=10a2799e · 文件集 = backend/tests/skills/test_g5_7_inbox_apply.py canvas-vault/.claude/scripts/undo_journal.py canvas-vault/.claude/skills/clear-inbox/scripts/inbox_apply.py；存档 `zcode-review-CARD-G5-7-r7.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g5-7` 新建）；单 commit（message 含 CARD-G5-7）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P7」。
```

### 补审-CARD-G1-1（CARD-G1-1 · 接 -r2· 补审）

> 📋 复制下面代码块粘进 `P8` 标签页的 /goal；卡文 `第十五批-goals/P8-C.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G1-1（车道 card-p8-backend，接 -r2）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（批注只读检索脚本），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G1-1]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend、分支、起点锚 16fd1e4e（`git merge-base --is-ancestor 16fd1e4e HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G1-1-r2.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P8-C.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color 86dc726c 4a6524aa -- backend/tests/unit/test_annotation_search.py scripts/annotation_search.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G1-1-r2.md 2> _bmad-output/审查/zcode-review-CARD-G1-1-r2.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 4a6524aa / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color 4a6524aa HEAD -- backend/tests/unit/test_annotation_search.py scripts/annotation_search.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G1-1-2026-09-19.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=86dc726c · 审SHA=4a6524aa · 文件集 = backend/tests/unit/test_annotation_search.py scripts/annotation_search.py；存档 `zcode-review-CARD-G1-1-r2.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g1-1` 新建）；单 commit（message 含 CARD-G1-1）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P8」。
```

### 补审-CARD-DEBT-1（CARD-DEBT-1 · 接 -r4· 补审）

> 📋 复制下面代码块粘进 `P9` 标签页的 /goal；卡文 `第十五批-goals/P9-B.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-DEBT-1（车道 card-p9-testinfra，接 -r4）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（pytest-timeout + 路径自动 marker），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-DEBT-1]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra、分支、起点锚 96da70c6（`git merge-base --is-ancestor 96da70c6 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-DEBT-1-r4.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P9-B.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color a7341ca4 9d270cdf -- backend/pytest.ini backend/tests/conftest.py backend/tests/unit/test_debt1_default_gate.py` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-DEBT-1-r4.md 2> _bmad-output/审查/zcode-review-CARD-DEBT-1-r4.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 9d270cdf / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color 9d270cdf HEAD -- backend/pytest.ini backend/tests/conftest.py backend/tests/unit/test_debt1_default_gate.py` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-DEBT-1-2026-09-18.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=a7341ca4 · 审SHA=9d270cdf · 文件集 = backend/pytest.ini backend/tests/conftest.py backend/tests/unit/test_debt1_default_gate.py；存档 `zcode-review-CARD-DEBT-1-r4.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-debt-1` 新建）；单 commit（message 含 CARD-DEBT-1）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P9」。
```

### 补审-CARD-G4-13（CARD-G4-13 · 接 -r1· 补审）

> 📋 复制下面代码块粘进 `P9` 标签页的 /goal；卡文 `第十五批-goals/P9-C.md`。

```
完成第十五批复核补审（zcode 通道 · 只读）：CARD-G4-13（车道 card-p9-testinfra，接 -r1）——按协议 §2.4.2 用 ZCode CLI + GLM-5.3 复核本卡最终态（金集 103 条 + manifest 冻结），直到绑最终 HEAD 的一轮 BLOCKER/HIGH = 0（本轮只审不改判；报 B/H 停下交主 session）[BATCH-2026-09-18-第十五批 / CARD-G4-13]（补审）
第 0 分钟：核 pwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra、分支、起点锚 96da70c6（`git merge-base --is-ancestor 96da70c6 HEAD` 为真；不符停下报主 session）、`git status --porcelain` 空；`zcode --version`（应含 zcode-app-cli 3.12.3-26 + zcode-runtime 0.16.5）与 `test -f ~/.zcode/v2/provider_config.json && echo cfg-ok` 落档。
⛔ 只审不改判、不写任何代码：① 生成 `_bmad-output/审查/prompts/zcode-review-prompt-CARD-G4-13-r1.md`——五分节从卡文 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P9-C.md 的 §一(n) 与 §四 逐条转写（最小读取面写死），并把 `git --no-pager diff --no-color 47c94bab d06f7127 -- backend/scripts/gold_set_manifest_tool.py backend/scripts/run_memory_retrieval_regression.py backend/scripts/run_vault_retrieval_regression.py backend/tests/regression/gold_set_manifest.yaml backend/tests/regression/memory_gold_set.yaml backend/tests/regression/test_gold_set_manifest_g413.py backend/tests/regression/vault_gold_set.yaml backend/tests/regression/vault_gold_set_shadow.yaml` 输出**内嵌**（build 模式无 Bash，评审者读不了 git）；② 送审 `zcode --prompt "$(cat …prompt…)" --cwd $(pwd) --mode build --no-color --json > _bmad-output/审查/zcode-review-CARD-G4-13-r1.md 2> _bmad-output/审查/zcode-review-CARD-G4-13-r1.stderr`；③ 首部 blockquote 按协议 §2.4.2（模型 glm-5.3 / 工具 zcode-app-cli 3.12.3-26 + runtime 0.16.5 / 命令全文 / 审查绑定 d06f7127 / 自证 = JSON sessionId+traceId 原文）。
完成条件（AND）：首部五字段齐 + JSON `sessionId` 非空；绑定声明 `git --no-pager diff --stat --no-color d06f7127 HEAD -- backend/scripts/gold_set_manifest_tool.py backend/scripts/run_memory_retrieval_regression.py backend/scripts/run_vault_retrieval_regression.py backend/tests/regression/gold_set_manifest.yaml backend/tests/regression/memory_gold_set.yaml backend/tests/regression/test_gold_set_manifest_g413.py backend/tests/regression/vault_gold_set.yaml backend/tests/regression/vault_gold_set_shadow.yaml` 为空（串行车道口径：本卡文件自本卡末 commit 后零改动）；B/H/M/L 全文与计数落档；结论写进 `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19-裁定清单.md` 追加「补审（GLM-5.3 × ZCode，协议 §2.4.2）」节并收工重算终态字段；**报 BLOCKER/HIGH ⇒ 不改代码，停下报主 session**。
关键输入（写死）：PREV=47c94bab · 审SHA=d06f7127 · 文件集 = backend/scripts/gold_set_manifest_tool.py backend/scripts/run_memory_retrieval_regression.py backend/scripts/run_vault_retrieval_regression.py backend/tests/regression/gold_set_manifest.yaml backend/tests/regression/memory_gold_set.yaml backend/tests/regression/test_gold_set_manifest_g413.py backend/tests/regression/vault_gold_set.yaml backend/tests/regression/vault_gold_set_shadow.yaml；存档 `zcode-review-CARD-G4-13-r1.md`（与既有轮次同目录）。
硬边界：只读（zcode --mode build 天然禁 Bash/Write）；不连 7691/7687；不 push；`*.stderr*` 不入库；存档逐文件 `git add`；JSON 0 字节 / sessionId 缺失重发一次、再失败交主 session；不改台账/手册/协议/卡文/他卡文件。
收尾：tee 进 `_bmad-output/审查/` 该卡既有 evidence 目录（找不到用 `evidence-g4-13` 新建）；单 commit（message 含 CARD-G4-13）；送审前跑 `~/.b15b-drive/jev_triage.sh <审SHA> <ev>` 分诊表按 urgency 进 prompt③（§2.4.3/§零.5）；跑完说「复核第十五批 P9」。
```

## 四、开跑步骤（逐车道）

1. **复核工具自证（一次，任意终端）**：
   `source ~/.codex/zai.env && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "Reply exactly: ZAI_OK" </dev/null` → 应回 `ZAI_OK`，stderr 会话头含 `model: glm-5.3`。
1b. **补审工具自证（一次）**：`zcode --version`（应含 `zcode-app-cli` 与 `zcode-runtime` 两行）→ `zcode --prompt "Reply exactly: ZCODE_OK" --cwd /tmp --mode build --no-color` 应回 `ZCODE_OK`。
2. **开发车道启动**（每车道一个终端标签页）：
   `cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-<车道> && opencode -m opencode-go/deepseek-v4.1-flash`
   > 首次在该树启动若提示 `external_directory`（跨树只读主干手册/协议/基线），选 `always` 放行 feature 主干树路径；`.omo/` 已 exclude，不脏树。
3. **长度门（复制前必跑）**：
   `python3 /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/gate_goal_length_b15b.py` → `GATE: PASS`
4. **发任务**：用**文件指针短消息**（见 §零.2；⛔ 不要直接粘贴整块——会静默丢弃）。块文件：`python3 …/show_goal_b15b.py <块名> > ~/.b15b-drive/blocks/<块名>.txt`。
5. **串行纪律**：前一卡独立 commit（message 含卡号）且 `git status --porcelain` 空后才粘下一块；顺序照 §一「剩余卡」列箭头（P5-B→P5-C、P6-C→P6-D、P7-B→P7-C）。
6. **先处置 §一 的「开跑前置处置」两条未跟踪文件**（否则第 0 分钟门红）。

## 五、承继项（不改写，引用原手册）

- **用户当次授权项**：原手册 §二.1 全表继续有效（P3 G8-7 走查、P5 G6-13 J07 窗口、P3 DEBT-10 ~/Library 实装、P4 G3-8 apply、P2 G4-6 outbox 迁移、P7 G5-7/G5-10 真实板全链、P9 G4-13 标注、P10 R-SLO 锁版、P8 C1-07 α 口径、P5 C1-04 T3-B、P8 C2-13 T-new-7、P2 REPLAY-REWRITE overflow 口径、P6 C2-05 PyYAML 半态）——**未授权即按原手册默认 + SKIP 登记**。
- **产品裁定项**：原手册 §二.3 全表继续有效。
- **不排本批**：原手册 §二.2 全表继续有效（含 P2b G4-6 第二波：P2 三卡进候选树后由主 session 切树通告）。
- **D-40 整仓 ruff-format / openapi.json 再生 / 协议回写**：仍由主 session 在全部车道收官后末位执行。

## 六、本手册不做什么

- 不改写原手册 / 22 张已跑卡文 / 其历史 `gpt-6-astra` 存档（协议 §2 / §2.1 历史保留）。
- 不重开 base `9c4e7e82`、不 rebase、不 merge（合并仍由主 session 逐卡 squash，队列照原手册 §二）。
- 不代用户做 §五 的授权/裁定。
