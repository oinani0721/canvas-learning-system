> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX.md)"`
> 审查绑定: `ef0cf1a9ff7bb8abee3485ca2981b2948dafa488`（送审时 HEAD；本轮整改后 HEAD 已前进到 532cfed7，见 round-2）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

**BLOCKER**

- **新增发布器仍能沿祖先软链写入 `$HOME/.codex` 禁写区。**  
  位置：[scripts/deploy-vault.sh:1714](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1714)，AGENTS 发布器同类问题在 `:1840`。  
  场景：部署 `/tmp/cx-parent/skills`，在 `:1941` 的复查完成后，将 `/tmp/cx-parent` 换成指向 `$HOME/.codex` 的软链；末段 `skills` 是真实目录，`O_NOFOLLOW` 不拦祖先，随后便能创建 `$HOME/.codex/skills/.codex/config.toml`。这违反整目录禁写约束；并非声称现存根 `config.toml` 会被覆盖。

**HIGH**

- **证据探针已经写过禁写目录，采用了本轮未授权的“运行期状态例外”。**  
  位置：[hard-boundaries-codex-attribution-20260917T031631.txt:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/hard-boundaries-codex-attribution-20260917T031631.txt:32)。  
  怎么看出来的：证据明确承认探针启动 Codex 后写入 `sessions/**`、重装 `skills/.system/**`，并登记为“不阻断”。`config.toml` SHA 相同不能证明整个 `$HOME/.codex` 零写。这是探针问题，不等于部署脚本调用了 Codex。

**MEDIUM**

- **manifest 的 `exclude` 登记使生成物损坏逃过正式校验。**  
  位置：[scripts/vault-install-manifest.json:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:89)。  
  场景：部署后把 `.codex/config.toml` 换成目录，再做独立校验；该项只被记为 `intentionally-excluded`，不会因形态错误失败。`optional generate` 原本会检查普通文件与可读性，因此这里不只是避免三条测试变红。

以下两项是**发布器再次进入已有文件分支时**的缺陷。真实部署原地重跑会先被现有安装器拒绝，不能据此声称整条部署重跑会假成功。

- **模板写入失败留下的空文件会被接受为正常模板。**  
  位置：[scripts/deploy-vault.sh:1742](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1742)。  
  场景：写入或 `fsync` 失败后，`:1776` 将新文件截成零字节；再次进入发布器时无条件返回 `kept`，`:1971` 的普通文件检查也会通过。

- **AGENTS 追加在首锚写完整之前失败，残件无法被识别。**  
  位置：[scripts/deploy-vault.sh:1885](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1885)。  
  场景：只追加了 `\n<!-- cls-codex` 就短写失败；再次进入时找不到完整首锚，直接追加新段并报告成功，不会给出“不完整”诊断。新增测试只覆盖完整首锚已经落盘的情况。

**LOW：无。**

其余核对结果：`030951` 原始事件确有一次完成且退出码为零的命令执行；`030813` 的空阴性已明确撤回，未见把模型自述当执行凭据。但未提供解析程序源码，无法独立核验所有判据分支。首次生成模板直接使用 `$PORT`；生成后在位判的落点合理；三门改例保留了原有形状；步 1 新增写入对象登记对应且无重复。

本次未修改文件，未运行部署、测试或探针，未连接数据库。
