> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-OPENCODE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-OPENCODE.md)"`
> 审查绑定: `836b1b7d`（该轮 HEAD；round-1 结论 BLOCKER=0 / HIGH=2 / MEDIUM=2 / LOW=0，四条全部采纳，整改在 `c228b745`）
> 会话头自证（抄 `.stderr` 中含 codex 版本 / `model:` / `reasoning effort` 的三行，括注实测行号；stderr 本身不入库）:
> `L2:OpenAI Codex v0.153.3`  /  `L5:model: gpt-6-astra`  /  `L9:reasoning effort: ultra`

---

**本轮 BLOCKER=0，HIGH=2，MEDIUM=2，LOW=0。**

复核绑定 HEAD：`836b1b7d9a399220a2e87adf22216c63fcb4725e`；限定文件与 HEAD 一致。以下复现均为静态推演，没有执行写入操作。

## HIGH

### H1 — `.agents` 祖先软链未被拒绝，会改变写入位置及技能落点

位置：[scripts/deploy-vault.sh:1004](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1004)，关联 `:611`、`:637`、`:1022`、`:1045`。

前置 `-L` 检查针对 `.agents/skills`，没有检查 `.agents` 本身；路径判据允许指向普通非保护目录的祖先软链。因此：

- `.agents → /tmp/ext/agents` 时，叶子实际写入 `/tmp/ext/agents/skills/<n>`。
- 相对目标解析成 `/tmp/ext/.claude/skills/<n>`，偏离 vault。
- 生成后只检查 `-L`，不能发现这个错误。

**复现思路：**在 B4b 入口保留正常技能源目录，令 `.agents` 指向普通外部目录，核对生成位置与叶子最终解析目标。

这是绑定函数的确定性输入缺口；本轮未验证 installer 是否允许这种旧 vault 从完整入口进入。

### H2 — 临时文件写入与 `mv` 发布存在对象替换窗口

位置：[scripts/deploy-vault.sh:1034](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1034)，关联 `:1028`、`:1040`、`:1075`。

`assert_writable_now` 检查后，重定向重新打开路径，没有绑定已检查的文件对象；期间替换成软链或硬链接，可以截断保护对象。最终 `mv` 同样没有绑定标记检查时的目标身份：

- 期间出现的无标记手写 `AGENTS.md` 会被覆盖。
- 目标变成目录时，会写入未登记的 `AGENTS.md/AGENTS.md.tmp`；末尾检查失败也撤不回写入。

**复现思路：**分别在临时文件检查后替换其链接、在标记检查后创建手写目标或同名目录，观察重定向及 `mv` 实际作用对象。

## MEDIUM

### M1 — MCP 指引遗漏 `/mcp`，按文案填写会得到错误端点

位置：[scripts/deploy-vault.sh:1069](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1069)。

正文要求配置“指向上面那个地址”，但给的是 `http://127.0.0.1:$PORT`；限定 [manifest:325](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:325) 登记的 MCP 地址包含 `/mcp`。OpenCode 的配置需要 `mcp.<name>.type="remote"` 和完整服务 URL。[官方说明](https://opencode.ai/docs/mcp-servers/#remote)

**复现思路：**将文案提供的根地址填入 remote MCP 的 `url`，静态对照 manifest 即可看到端点不一致。

### M2 — 新增 dry 测试不能证明“整个 tmp 根零写”

位置：[backend/tests/unit/test_deploy_vault_sh.py:4229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:4229)。

断言只搜索 `.agents` 和 `AGENTS.md`，漏掉其它文件、目录、`AGENTS.md.tmp`、原文件改写及创建后删除的临时文件。

**复现思路：**在 opencode dry 分支临时加入 `: > "$HARNESS/stray.txt"`，该测试的现有断言仍会通过。

这属于验收覆盖缺口，**不代表发现了实际 dry 写入**。

## 对问题 0—7 的结论

**0．发现语义成立，但“最终一份”不等于“只读取一次”。**  
当前官方源码扫描 `.claude`、`.agents`，跟随目录软链；发现阶段按路径字符串收集，两条别名路径都可能解析，注册阶段再按 frontmatter `name` 去重并记录重名警告。最终只有一个该名称的技能，不能承诺保留哪侧的 `location`。[技能源码](https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/opencode/src/skill/index.ts)、[软链扫描实现](https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/core/src/util/glob.ts)  
此结论基于本轮官方 `dev` 源码、有效 frontmatter 且外部技能发现开启；没有绑定本机 OpenCode 版本。

**1．新增 dry 路径未发现可达写入。**  
host 切分仍是纯参数展开，没有新增 heredoc/here-string；步 3 在 `:1090` 返回，B4b 不可达。没有独立重跑作者的系统级零写实验，测试不足见 M2。

**2．非注释行禁串检查通过。**  
`opencode.json` 字面命中为零，当然也没有 `opencode.jsonc`。运行拼接的 `cfg` 只进入 AGENTS.md 文案，没有作为配置写入目标。当前没有因此产生配置写入旁路；这种拆字符串方式只是适应词法门的权宜手法，不能作为运行时零写证明。

**3．D-26(i) 专用登记确实只有 `cls_forbidden_paths.py:270`。**  
删掉它后，普通、无其它保护重叠的两个路径会失去保护；但 `.config` 指入其它禁面、live 覆盖该目录等情况仍会被通用规则拒绝。`under()` 明确处理根 `/`，CLI 也补查空路径段列表，未发现所问根退化旁路。

**4．文案没有诱导写用户级硬禁面。**  
生成正文明确给出项目根 `opencode.jsonc`，并禁止修改用户级配置；问题是 M1。生成标记确在首行，但覆盖检查实际是**全文子串匹配**，不是首行精确匹配。

**5．`.git` 是目录还是文件，不改变相对软链落点。**  
父目录均为真实目录时，两级回跳都回到 `$VAULT`；H1 中的祖先软链才会改变这个结论。

**6．正常路径的登记结构完整，执行时保护尚未闭合。**  
根、AGENTS.md、临时文件已登记；叶子逐项补判；`mkdir -p` 中间段也会经过判据。缺的是 H1 的祖先形态约束，以及 H2 的检查与写入对象绑定。

**7．三条门的更新属于按原意登记，没有改松集合比较。**  
独立复算得到 **17 个 label，精确相等**；条件 append 仍在原扫描切片内。`codex`／`dsh`／`claude,codex` 的 rc 64、E-1 断言和三个剩余禁件检查仍保留，manifest 的两个生成项及归属例外也对应一致。

正常 `--hosts claude` dry 输出与 PREV 等价符合静态控制流；不能扩大为“所有行为逐字相同”，因为 `--help` 已随头注改变。

**验证边界：**完成 Bash 语法检查、内存判据核验及静态门复算；未运行部署脚本、pytest、数据库或模型，未修改文件。

