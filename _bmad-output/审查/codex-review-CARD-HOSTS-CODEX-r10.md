> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-10
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r10.md)"`
> 审查绑定: `c847d58c`（本轮**代码零改动**，审查者自证 `b47eea11..c847d58c` 排除 `_bmad-output` 后代码 diff = 0）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）
>
> **BLOCKER = 0**（r9 已降级）。本轮把我的归属取证**逐条打回**，复核后**它全对** ——
> 我的更正写在 `evidence-hosts-codex/codex-home-write-attribution-*.txt` 末尾。

---

**结论：新增取证不足以排除历史探针归属。原 HIGH 保留为本卡历史探针的验收事项；审查调用的写入另归批级执行环境，不能据此整体转移该 HIGH。**

已确认 `b47eea11..c847d58c` 排除 `_bmad-output` 后代码零改动。

**BLOCKER：无。**

**HIGH：1 条，历史项，收窄理由。**

- **“最后修改于 06:53”不能推出“03:12 前的探针没有写过”。**  
  位置：[归属取证:27](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/codex-home-write-attribution-20260917T065932.txt:27)、[排他结论:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/codex-home-write-attribution-20260917T065932.txt:46)。  
  怎么看出来的：**探针先写，r9 再重装同一批文件**，最终也会全部显示 06:53；无需假设有人刻意修改时间戳。

  而且，[03:16 存档:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/hard-boundaries-codex-attribution-20260917T031631.txt:5) 已列出 60 个 skills 文件，该记录在早期提交 `ef0cf1a9` 中就存在。[03:09 探针 stderr:17](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/codex-readonly-negctl-20260917T030951.txt:17) 还记录了删除既有系统 skills 目录时失败，证明探针触发过这条路径；失败也不能证明没有部分副作用。

  **证据边界同样要收紧：**旧统计窗口较宽，也没有进程级写入记录，因此不能反过来断言这 60 个文件全由探针写成。能确认的是：新证据没有排除历史探针贡献。

  **r9 将 `sessions/**` 一并作为 HIGH 理由不准确，应删除该理由。**它已获明确授权；保留项只涉及非豁免的 skills 历史写面，不代表发现了新的部署脚本缺陷。

**MEDIUM：1 条，沿用 r9，登记不阻断。**

- 并发搬移后的写入残留不变。位置：[deploy-vault.sh:1920](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1920)。场景：落点检查后目录被搬走，后续写入仍跟随原 inode。本轮不重新定级。

**LOW：无。**

本卡边界内尚能做的是：

1. 将“时间上不可能／确定不是探针”订正为“末次修改时间与 r9 窗口相符；历史探针贡献无法排除”，保留历史未知和验收裁定。
2. 核对“四次真 home”的时间线：02:52 的 schema 记录及 03:12 的模板解析记录都明写使用重定向 `CODEX_HOME`，与新增文档存在冲突。
3. 订正“必须改协议才能避免审查写入”的说法：[主干协议:22](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.claude/rules/card-batch-protocol.md:22) 固定了命令，**没有要求真实 `CODEX_HOME`**。审查环境隔离可交批级统一处理。

不需要重跑真实 home 探针，也不要求补证无法追溯的历史整目录零写。本轮未修改文件、运行测试或启动 Codex，未连接数据库。
