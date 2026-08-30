# UAT — CARD-DEBT-5 活动插件 CI build/test 门

> **批次**: BATCH-2026-08-28-第五批 / CARD-DEBT-5（车道 S8）
> **worktree**: `.claude/worktrees/card-s8-ci`（分支 `card/s8-ci`）
> **卡定义**: 总账 v2 §DEBT-5（2h · wave 1 · 防暗坑）
> **执行日**: 2026-08-28

## 一句话

Obsidian 插件（`frontend/obsidian-plugin/`）此前**完全没有 CI 门**，本卡新增独立 workflow `plugin-ci.yml`（npm ci → build → test），并在装门过程中发现插件测试**在 main 上就是红的**（301 测试 / 7 条 fail，最早自 2026-05-14 起红了 3 个半月无人知）——7 条逐条溯源处置后本地全绿。

## Claude 已代跑的技术验证（用户不用管）

| 判据 | 结果 |
|---|---|
| 本地等价裁判 `npm ci && npm run build && npm test` | ✅ 全链 exit 0（存档 `_bmad-output/审查/debt5-evidence-2026-08-28/local-judge-npm-ci-build-test.txt`） |
| 测试计数 | 301 测试 / **295 pass / 0 fail** / 6 todo 债务哨兵 / 39 suites |
| 装门前基线（同命令，改动前实测） | 301 测试 / 294 pass / **7 fail** / exit 1 |
| 硬边界 `test.yml` 零改动 | ✅ HEAD 与 index blob 相同（Codex 双轮复核） |
| 硬边界 `readme-claims.yml` 零改动 | ✅ 同上 |
| 硬边界 `backend/.gitignore` 禁改（S4 独占） | ✅ 该文件在 HEAD/index/工作树均不存在，零接触 |
| Codex 对抗审查 | 2 轮，round-1 提 1 BLOCKER + 1 HIGH + 2 MEDIUM + 1 LOW → round-2 **BLOCKER/HIGH 全部 CLOSED**（存档 `_bmad-output/审查/codex-review-CARD-DEBT-5-round1.md` / `-round2.md`） |
| CI 真跑 | ⏳ push 后由主 session 盯（本卡不 push，按批次纪律） |

## 做了什么

### 1. 新增 `.github/workflows/plugin-ci.yml`（独立 workflow）

仿 `readme-claims.yml` 的小型独立 job 先例，`test.yml` 零改动：

- 触发：`push` / `pull_request`，paths 限 `frontend/obsidian-plugin/**` + workflow 自身；
- 步骤：`actions/checkout@v4` → `actions/setup-node@v4`（node 24，npm 缓存指向插件 lockfile）→ `npm ci --no-audit --no-fund` → `npm run build` → `npm test`；
- `permissions: contents: read`（最小权限）；
- 头部写明 **DEBT-7 交接注记**：本 workflow 用 `paths` 过滤，若把 `build-test` 设为**全局 required check**，被 paths 跳过的 PR 会永远 Pending（GitHub 官方行为）。DEBT-7 启用 required 时须改 always-run + job 内条件跳过，或用 path-scoped required 策略。

### 2. `package-lock.json` 入库（插件 `.gitignore` 放行）

`npm ci` 强制要求 lockfile，原 `.gitignore` 把它挡在库外 → CI 必然失败。移除该行并提交 lockfile（624 行，lockfileVersion 3，devDependencies 与 package.json 完全一致，含 Linux esbuild 平台包）。

### 3. 7 条陈旧失败测试逐条溯源处置

装门必须先让门能绿。**没有删红改绿**——逐条查 git 考古定性：

| 条数 | 文件 | 定性 | 处置 |
|---|---|---|---|
| 2 | `exam-quick.test.ts` | **断言过时**（`inferVaultId` 正则要求单独 import 块，但该块后来长成多符号；`startExam(Notice)` 直连在 31c1f8f6 改走 `handleQuickExamAbsorbed`） | 按现役行为重写断言 |
| 6→todo | `vault-indicator.test.ts` | **未完成需求债务**，非已退役功能 | 标 `node:test` todo 债务哨兵，**不删除** |

vault-indicator 6 条的考古结论（Codex round-1 HIGH 指出并经复核确认）：

- wiring 自 `3d10a02b`（2026-05-14 story-2.4）移除，此后持续 FAIL；
- α-5 的 `StatusBarController`（f860f57f）只渲染 Tips/导航路径，**没有**接替 vault 三态 / mismatch / Notice 前缀行为；
- α-5 当时把这些失败明确登记为「Wave-5 Stage A 待补 wiring」（`_bmad-output/_status/mvp-alpha-broadcast-session-b.yaml:114-117`）；
- UAT 至今仍要求 `[vault:]` Notice 前缀（`_bmad-output/验收单/Story-2.2+2.9-FINAL-comprehensive-UAT-2026-05-13.md` Step 1「必跑」）。

→ 若直接删除，等于把一笔独立的产品债务"洗绿"。改用 `todo` 标记：失败在 CI 输出里**照常可见**（`⚠` 行 + `failing tests` 段落 + `todo 6` 计数），但 `fail=0`、exit 0，门可落地。这与后端 G2-1 真库门测试用 `xfail(strict)` 固化写身份债务是同一手法。

**诚实声明（Codex round-2 记录的非阻断盲区）**：这 6 条 wiring 范围内的新增/复发回归**不会**让门变红。除此之外的安装失败、build 失败、任何普通测试回归都会照常阻断。

## ⛔ 待用户裁决（1 项）

**vault-indicator wiring 债务的最终去向**——两条路，本卡不代裁：

- **A. 补 wiring**：恢复 `[vault:]` Notice 前缀 + status bar vault 三态（ok/mismatch/down）+ 点击开设置。UAT 要求过、用户当时确认过"明确分隔开来"的诉求，功能本身仍有价值（跨 vault 是主 goal 刚需）。补完后把 6 条 todo 摘掉即自动转为真门。
- **B. 正式退役**：判定 α-5 的 Tips/导航状态栏已够用，vault 三态不再做。则须同步删除 `src/vault-indicator.ts`（当前为 orphan 模块，无 main.ts 调用方）、删测试、并在 Story-2.2+2.9 UAT 上标注该条已撤销——**不能只删测试**。

在裁决前，6 条 todo 就是这笔债务在仓内的唯一活体记录。

## 遗留 / 交接

- **DEBT-7（required checks 启用）**：见上方 workflow 头部注记，paths 过滤与 required check 的 Pending 冲突需在那张卡处理。
- **CI 首跑验证**：本卡按纪律不 push。push 后需确认 `Plugin CI / build-test` 真绿（readme-claims 首跑教训：本地绿 ≠ CI 绿，环境自足性已尽力预防：node 版本显式 setup、无本地依赖假设、lockfile 入库）。
- **click handler 断言的 spec-as-test 局限**（Codex round-2 MEDIUM，已知非阻断）：断言已锚定到 `addStatusBarItem()` 的接收变量，但若未来实现把 handler 抽成独立方法（如 `openPluginSettings()`），断言会漏报。补 wiring 时一并改写。
