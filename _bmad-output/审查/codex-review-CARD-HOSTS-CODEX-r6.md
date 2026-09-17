> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r6.md)"`
> 审查绑定: `3967da9c0b4417638d7d26a30fb7d65da791fd6f`（**本轮首次绑最终 HEAD**；审查者自证「三份送审文件均与该提交逐字一致」）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）
>
> ⚠️ 为什么有第 6 轮：卡文 §四「**审后再改代码必再送一轮**」是硬要求，而「第 5 轮停下交人审」的
> 触发条件是 **HIGH ≠ 0** —— r5 的 HIGH 是 0，且 r5 之后确实又改了代码。先前把「上限 5」读成
> 「不得再送」是我读错了协议，已更正。

---

本轮绑定 **`3967da9c0b4417638d7d26a30fb7d65da791fd6f`**；三份送审文件均与该提交逐字一致。

**结论：BLOCKER 2 / HIGH 2 / MEDIUM 2 / LOW 0，不能通过。** 其中 HIGH-2 属历史探针的验收口径问题。全程未修改文件、未运行部署或写盘探针、未连接数据库。

**BLOCKER**

1. **检查通过后，目录仍可被 rename 到禁写面，后续 fd 写入照常发生。只能交人裁。**  
   位置：[scripts/deploy-vault.sh:1896](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1896)，另见 `1791–1798`、`2103–2104`、`2127–2168`。  
   怎么看出来的：1896 检查通过后，将 `.codex` 搬入 `$HOME/.codex/`，1897 仍向原 inode 写入；事后身份检查或失败清理不能撤销越界写。`O_NOFOLLOW_ANY` 约束打开时的路径解析，不能固定已打开对象的位置。  
   **对不受约束的并发 rename，本卡内无可落地方案。** 本轮没有找到已验证、保持功能且符合限定修改面的原子闭合方式；需主 session 裁定目录稳定性或隔离前提。

2. **非 Darwin 静默降级重新开放中间段软链漏洞，应 fail-closed。本卡可修。**  
   位置：[scripts/deploy-vault.sh:1716](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1716)，重复定义在 `1986`，创建点在 `1845`。  
   怎么看出来的：非 Darwin 环境中，1811 的检查通过后，将 `.codex` 换成指向用户级目录的软链；1845 的 `O_CREAT | O_NOFOLLOW` 仍可沿中间段创建空 `config.toml`，随后拒绝已经太晚。  
   最小修法是在 Codex 发布器发生任何 `mkdir/open` 写入前拒绝非 Darwin；“macOS 专用”的注释不能代替执行门。

**HIGH**

1. **`refused` 漏掉守卫自身抛异常的路径，无法确认落点时仍会清理写入。本卡可修。**  
   位置：[scripts/deploy-vault.sh:1896](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1896)、`1915–1930`；AGENTS 对应 `2103`、`2183–2189`。  
   怎么看出来的：`_fd_realpath()` 获取路径失败抛出 `OSError`，没有调用 `_refuse()`，所以 `refused` 仍为 False；配置发布器继续截断并写失败标记，AGENTS 新建分支继续截断。已有文件追加分支此时 `keep_size` 尚为空，不受此分支影响。  
   最小修法是默认禁止清理写入，只有整个守卫正常返回后才解除；这是确定的异常控制流缺口，本轮未做故障注入。

2. **历史负控使用了“运行状态写入豁免”，与本轮整目录硬禁写约束冲突。需人裁验收证据。**  
   位置：[hard-boundaries-codex-attribution-20260917T031631.txt:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-hosts-codex/hard-boundaries-codex-attribution-20260917T031631.txt:32)。  
   怎么看出来的：记录明确承认探针启动 Codex 后写入真实 `~/.codex/sessions`、`skills` 等，再按运行状态面豁免；本轮没有授权该豁免。`config.toml` 前后 SHA 相同不能证明整个目录零写。  
   这是探针边界问题，不是部署脚本调用 Codex 的证据；历史写入不能靠修改说明追认合规。

**MEDIUM**

1. **新增安全 flag 门无法发现 `_NOFOLLOW_ANY` 被直接删除。本卡可修。**  
   位置：[backend/tests/unit/test_deploy_vault_sh.py:5612](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5612)。  
   怎么看出来的：删除四处 `open` 参数里的 `| _NOFOLLOW_ANY`，保留常量定义，两个拒绝条件及末尾断言仍能通过；对应行为测试又被步 1 的提前拒绝遮蔽。应正向检查每处 flags，并增加删除 flag 的反例。

2. **常量不可达剪枝仍漏掉 `if True` 的 `else`；r5 MEDIUM-1 仅部分关闭。本卡可修。**  
   位置：[backend/tests/unit/test_deploy_vault_sh.py:5318](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:5318)。  
   怎么看出来的：仅在内存中调用现有计数函数，`if False: guard()` 得到 0，但 `if True: pass; else: guard()` 仍得到 1。这个对称分支不需要一般可达性分析，可以直接补齐；一般控制流、间接调用和 `exec` 可以保留为已披露限制，但不能据此声称运行时守卫必然执行。

**LOW：无。**

其余问题核对如下：

| 核对项 | 结论 |
|---|---|
| 四处 `open` 替换 | 全部使用 `_NOFOLLOW_ANY`，无遗漏；其中模板的两处是真正多段路径。 |
| 显式拒绝后的清理 | `_refuse()` 正常被调用时，两个发布器的清理均会跳过；异常缺口见 HIGH-1。 |
| read-only 负控 | `030813` 已明确作废。`030951` 记录新目录跑前、跑后 trust 命中均为 0；原始 JSONL 第 5 行确有已完成且退出码为 0 的命令事件，因此不是“没跑起来”的空判据。 |
| 执行凭据 | 没有把 `agent_message` 当执行证据；零事件只判未测出是正确方向。SHA 结论限于该次运行前后内容相同。 |
| 端口 | 新模板及 Codex 段直接使用 `$PORT`，首跑不会漏替换 `:8011`；已有模板和完整段按设计保留原文。 |
| 生成后在位判 | 放在生成后合理，缺文件或叶子软链会失败；它不能承担并发路径安全证明。 |
| AGENTS 追加 | 静态状态下拒手写文件、软链及已有多硬链接文件；协作锁覆盖判重、追加和回滚，能识别已覆盖的半截段。并发命名空间变化仍受 BLOCKER-1 限制。 |
| manifest | `exclude` 确实丢失部署后形态检查，已明确披露；按要求不重复计入旧 MEDIUM-2。 |
| 步 1 清单、旧门换例 | 新增三个写入对象对应正确，双宿主 AGENTS 只登记一次；旧门保留了单值及合法值与未实现值组合。 |
| 调用 Codex | 未发现部署脚本执行 Codex；相关命令是生成给用户阅读的文本。但不能因此宣称所有间接写入路径已关闭。 |

现有文件级证据的脚本、测试 SHA 与最终提交匹配，记录为 **242 passed / 9 skipped**；本轮未重跑测试。


