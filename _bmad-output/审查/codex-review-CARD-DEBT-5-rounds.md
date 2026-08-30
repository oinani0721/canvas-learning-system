# Codex 对抗审查存档 — CARD-DEBT-5 插件 CI build/test 门

> **批次**: BATCH-2026-08-28-第五批 / CARD-DEBT-5
> **审查者**: `codex exec --sandbox read-only`（codex-cli 0.147.0），静态只读，全程未执行 build/test
> **轮次**: 2 轮（round-1 提 1 BLOCKER + 1 HIGH + 2 MEDIUM + 1 LOW → round-2 BLOCKER/HIGH 全部 CLOSED）
> **base HEAD**: `37387a8662e9dd646fad5628841679d777cb7eae`（`card/s8-ci`）

## 裁定汇总

| # | 级别 | 发现 | round-2 状态 | 整改 |
|---|---|---|---|---|
| 1 | BLOCKER | 补丁未含 `package-lock.json`，CI 的 npm 缓存 hash 与 `npm ci` 必然失败 | ✅ CLOSED | lockfile git add 入同一 commit；Codex 复核 JSON 有效 / lockfileVersion 3 / devDeps 与 package.json 一致 / 含 Linux esbuild 平台包 |
| 2 | HIGH | 5 条 vault-indicator 断言不能以「α-5 已接替」为由删除——α-5 的 StatusBarController 只渲染 Tips/导航，**未**接替 vault 三态；α-5 状态账登记为「待补 wiring」；UAT 仍要求 `[vault:]` 前缀。删除 = 把独立债务洗绿 | ✅ CLOSED | 改为不删除，6 条全标 `node:test` todo 债务哨兵（输出可见、fail=0、exit=0），文件头写考古结论 + 移交裁决条款；Codex round-2 复核考古结论成立、todo 语义对照实验通过 |
| 3 | MEDIUM | 保留的 "setting.open" 断言是假阳性：全文件 grep 命中设置页「打开快捷键设置」按钮（main.ts:2188），与 status bar click 无关 | ✅ CLOSED（round-2 判 PARTIAL 后再整改） | round-2 确认 main.ts:2188 假阳性已消除（该处用 `.onClick()` 不在模式内）；按 round-2 建议进一步锚定：先正则捕获 `addStatusBarItem()` 的接收变量名，再要求**该变量**上注册 click（含 `registerDomEvent(el,"click",…)` 形态）且 800 字符窗口内出现 `setting.open()` / `openTabById` |
| 4 | MEDIUM | 若 `Plugin CI / build-test` 设为全局 required check，被 `paths` 跳过的 PR 会永远 Pending（GitHub 官方行为） | 🔀 交接 DEBT-7 | workflow 头部写明 DEBT-7 交接注记（不改触发方式）；round-2 判定「成功交接、未技术修复」，且当前仓库 ruleset 是否已要求该 check 静态不可验证 |
| 5 | LOW | 未显式最小化 token 权限 | ✅ CLOSED | 加 `permissions: contents: read` |
| 6 | LOW（round-2 新增） | 文件头移交引用 `UAT-CARD-DEBT-5-*.md` 悬空（当时未创建） | ✅ CLOSED | 验收单已建，引用改为精确路径 + 章节 |
| 7 | LOW（round-2 新增） | 送审 patch ≠ staged 集合（lockfile 仅 stat 行、证据 txt 未入 patch） | ℹ️ 说明 | 有意为之：lockfile 624 行不内联以免淹没审阅；Codex 已在当前 checkout 额外核对全部 staged 内容，不影响功能结论 |

## round-2 明确 PASS 项

- workflow YAML 语法、`working-directory`、步骤失败传播、缓存子目录路径；
- `todo` 语义对照实验：6 条全部出现在 `⚠` 与 `failing tests` 明细中；普通非-todo 失败的对照为 fail 1 / exit 1（即 todo 不掩盖真回归）；
- exam-quick 两条改写成立：`inferVaultId` 确从 `./error-candidate-helpers` 导入（main.ts:78）；`canvas:start-quick-exam` 的 callback 确调 `handleQuickExamAbsorbed()`（main.ts:430），handler 行为与「吸收进检验白板」一致（main.ts:607）；
- 硬边界：`test.yml` / `readme-claims.yml` 的 HEAD 与 index blob 相同；`backend/.gitignore` 在 HEAD/index/工作树均不存在（实际存在的是 `backend/data/.gitignore`），零接触；
- `git diff --check` / `git diff --cached --check` 无错误。

## round-2 记录的非阻断盲区（诚实声明）

> "todo 不会让整个门形同虚设：workflow 仍会阻断安装、build 和所有普通测试回归；但这 6 个 wiring 范围内的新增/复发回归不会变红。这是明确、局部的非阻断盲区。"

以及 click 断言的 spec-as-test 局限：若未来实现把 handler 抽成独立方法（`openPluginSettings()`）或超出字符窗口，断言会漏报——补 wiring 时一并改写测试。已记入验收单遗留节。
