> 批次: BATCH-2026-09-11-第十四批 · 车道 T8 · 卡 CARD-TOOLCHAIN-UNIFY round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-TOOLCHAIN-UNIFY.md)"`
> 审查绑定: `99e15a4e08c4749500a59584c12edbaafcff0f3e`（= 本卡唯一 commit；审后代码零改动，仍绑最终 HEAD）
> 会话头自证（抄 `.stderr` 中含 codex 版本行 + `model:` 行 + `reasoning effort` 行的三行，括注行号；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

复核绑定 **`99e15a4e08c4749500a59584c12edbaafcff0f3e`**，父提交正确，排除 `_bmad-output` 后确实只改三个文件。发现 **1 项 MEDIUM、1 项 LOW**；未发现新增阻断项。

**⓪ 不能确认“install-free 下不存在统一路径”。**  
位置：[package.json:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/package.json:19)、[package-lock.json:14](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/package-lock.json:14)。

从约束上看，**把 npm 声明及完整 lock 解析元数据对齐已有 brew 版本，可以是纯文件变更**，并不必然要求当场安装。因此，保留跨 runner 分叉可以是本批授权范围的选择，不能仅归因为 install-free 下技术上无路可走。但当前 npm runner 根本不存在，禁止安装意味着不能完成“两套实际 runner 同版”的实测验收。本次未展开或验证备选 lock 的执行方案。

**BLOCKER：无。**

**HIGH：无。**

**MEDIUM**

- **“单星不含子目录”的覆盖结论错误，且把递归 94 个误记为顶层 94 个。**  
  位置：[lefthook.yml:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:118)、[rootsurface-before-after-v2-20260917T125857.txt:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-toolchain-unify/rootsurface-before-after-v2-20260917T125857.txt:31)。  
  独立读取 Git 文件名元数据得到：`scripts/` **顶层 52 个、子目录 42 个、递归 94 个**。Lefthook 1.13.6、2.1.6 的默认 matcher 均未给 gobwas 指定 `/` 分隔符，`*` 可以跨目录；2.1.6 的固定版本测试也明确验证了这一点。因此，`scripts/spec-tools/api-reality-dashboard.py` 这样的对照输入**会被 glob 选中**，不能登记为门未覆盖的路径。这是两次更正之后仍存在的第三处判据问题。[2.1.6 实现与测试](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/run/controller/filter/filter_test.go#L39-L43)、[1.13.6 实现](https://github.com/evilmartians/lefthook/blob/v1.13.6/internal/run/controller/filters/filters.go#L73)。

**LOW**

- **文件头“Lint rules temporarily disabled”与实际配置不符，属于文案债。**  
  位置：[ruff.toml:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/ruff.toml:2)，实际启用声明在同文件 `:40`。  
  维护者只读文件头判断规则状态时会被误导；执行规则不受影响。考虑本卡只允许改 `select` 及其上方注释，登记后续更正合适，不应因此擅自扩地盘，也不构成本卡阻断。

其余问题逐项核定：

- **① 存在真实的 runner／hook 生成路径分叉，而且早于本卡存在。**  
  位置：[package.json:7](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/package.json:7)、[共享 pre-commit:13](/Users/Heishing/Desktop/canvas/canvas-learning-system/.git/hooks/pre-commit:13)。默认安装 devDependencies、启用生命周期脚本时，`npm ci` 的 `prepare` 使用前置于 PATH 的本地 **1.13.6** 执行 `lefthook install`；无全局 runner 的环境随后也运行本地版本。本机普通 Git 环境则优先运行 brew **2.1.6**。**生成 hook 的版本不等于随后执行 hook 的版本。** 当前 `runner-of-record` 判定成立，但它与版本 grep 不能证明跨环境行为一致；也不能仅凭版本不同断言已有具体作业结果不同。[npm 生命周期](https://docs.npmjs.com/cli/v11/using-npm/scripts/#life-cycle-operation-order)、[PATH 前置实现](https://github.com/npm/run-script/blob/main/lib/set-path.js#L30-L35)。

- **② 288 的计数成立；两条 F821 在提供的报告内穷尽，但不能无条件称为完整运行时治理面。**  
  位置：[v2 evidence:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-toolchain-unify/rootsurface-before-after-v2-20260917T125857.txt:6)。独立文件名核算确认，这是全部非 `backend/` 的 tracked `.py`；tracked 配置文件中也未发现另一份子目录 Ruff 配置。报告 `:14–25` 的 `131 invalid-syntax + 2 F821` 与两条定位一致，没有报告第三条新增必错级命中。  
  但 Ruff 实际范围取决于入口：目录发现、显式文件参数、忽略规则及未跟踪文件会产生不同集合。因此 **288 应称“本次 tracked `.py` 普查集合”**，不能泛化为所有运行入口的完整治理面。[Ruff 文件发现规则](https://docs.astral.sh/ruff/configuration/#python-file-discovery)。

  两次更正均成立：中文路径 quoting 能解释 129 条 E902；内联覆写能保留配置发现。第二处的精确原因是 **显式传入配置文件会停止缺省 `target-version` 推断**，不只是临时目录位置不对。[Ruff 版本推断规则](https://docs.astral.sh/ruff/configuration/#inferring-the-python-version)。另外，`131→131` 只能证明数量相同，不能单独证明逐条诊断相同；此次按限定读取面没有重新读取 288 个源码文件运行 Ruff，故不声称已独立复跑穷尽验证。

- **③ 登记 `technology` 的存量 F821、不在本卡修复，恰当。**  
  位置：`scripts/validate-source-citations.py:392`，定位见 [v2 evidence:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/_bmad-output/审查/evidence-toolchain-unify/rootsurface-before-after-v2-20260917T125857.txt:25)；[台账 Z7-A:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:53)已明确登记该 F821。将来暂存该文件且保持现状时，新规则会拦下它；这是启用检查后的预期影响，不是本卡制造了未定义名。禁止修改 `.py` 的范围应保持。

- **④ 三个非 `.py` 文件不会启动该 `python-lint` 作业，静态推断成立。**  
  位置：[lefthook.yml:118](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/lefthook.yml:118)、`:123`。这三个对照输入过滤后 `{staged_files}` 为空；正常、未强制运行时，2.1.6 在构造命令阶段直接跳过，**不会把空参数交给 `ruff check` 扫描全仓**。这是固定版本源码支持的结论，未运行 hook。[跳过逻辑](https://github.com/evilmartians/lefthook/blob/v2.1.6/internal/run/controller/command/build_command.go#L27-L29)。

- **⑤ 本次范围收紧不会造成 lefthook 的 manifest／lock 失配。**  
  位置：[package-lock.json:1490](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools/package-lock.json:1490)、`package.json:19`。独立 JSON 比较确认：lockfileVersion 为 3；除 root 声明这一处预期编辑外，整个 lock 内容相同；已解析版本正好满足 exact `1.13.6`，URL、integrity、10 个平台 optionalDependencies 均未变。因此无需通过重新安装来使此次编辑自洽；这不等于未经执行的完整 `npm ci` 已通过。[npm ci 一致性要求](https://docs.npmjs.com/cli/v11/commands/npm-ci/)。

全程未修改文件、未安装、未运行 hook 或连接数据库。`tests/unit` 的“64 条红逐条相同”仅核对了所列汇总 evidence，未独立复跑。
