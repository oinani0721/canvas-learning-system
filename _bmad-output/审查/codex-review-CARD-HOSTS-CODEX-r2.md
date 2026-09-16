> 批次: BATCH-2026-09-11-第十四批 · 车道 card-t2-deploy · 卡 CARD-HOSTS-CODEX round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HOSTS-CODEX-r2.md)"`
> 审查绑定: `532cfed7`（送审时 HEAD；本轮整改后 HEAD 再前进，见 round-3）
> 会话头自证（抄 .stderr，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: gpt-6-astra`（:5） / `reasoning effort: ultra`（:9）

---

结论：**BLOCKER 1 / HIGH 1 / MEDIUM 2 / LOW 无**。round-1 尚未全部闭合。审查以 `532cfed7` 为准；未修改文件，未运行部署、探针或写盘测试。

**BLOCKER**

1. **只校验 vault 目录，仍可能把新配置写进 `$HOME/.codex`。**  
   位置：[scripts/deploy-vault.sh:1723](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1723)，后续写入在 1735、1752。  
   怎么看出来的：例如 `HOME=/home/alice`、vault 为 `/safe/redirect/alice`；在 1997 的输出路径检查之后，把祖先 `redirect` 换成指向 `/home` 的软链。`open_pinned(vault)` 检查的是 HOME 本身，因此允许；随后相对该 fd 创建 `.codex` 或缺失的 `config.toml`，就写入了禁写面。**“父目录允许”不代表其 `.codex` 子路径允许**；生成后的普通文件检查也不能撤销已经发生的写入。

**HIGH**

1. **追加回滚没有互斥，会截掉并发写者的内容；同一缺口也允许重复追加。**  
   位置：[scripts/deploy-vault.sh:1971](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1971)，长度采样及追加在 1917、1938–1939。  
   怎么看出来的：采样长度后，另一进程追加正文；本次写入随后因 `fsync` 失败而回滚，`ftruncate(fd, keep_size)` 会一并删除对方的正文。`O_APPEND` 只保证每次写到末尾，不保护整个“读取→判断→追加→回滚”过程。两个写者同时读到“尚无 Codex 段”，也能各追加一次并通过检查。注释声明不假设并发，不能实际排除这个场景。

**MEDIUM**

1. **失败清理再次失败时，留下的短标记仍会被已有文件分支误接受。**  
   位置：[scripts/deploy-vault.sh:1770](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1770)，标记写入及异常处理在 1806–1811；AGENTS 回滚在 1971–1973。  
   怎么看出来的：正文短写失败后，清理截空成功，但 `INCOMPLETE` 标记也只写入 `# <!-- I` 就再次失败；以后处理该文件时，它既非空，也不匹配完整标记，因而报 `kept`。纯内存核对已确认这两个拒绝条件均不命中。AGENTS 的回滚若失败并留下半个首锚，后续同样识别不到残件。整改只覆盖了**清理成功**的情况。

2. **manifest 的 `exclude` 仍放弃了模板形态校验，补充说明没有修复这一缺口。**  
   位置：[scripts/vault-install-manifest.json:89](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/vault-install-manifest.json:89)。  
   怎么看出来的：部署后把 `.codex/config.toml` 换成目录或软链，独立校验器仍按 `intentionally-excluded` 处理，不因形态错误失败。部署当次的检查不能覆盖之后的漂移。这是本卡新增登记方式的后果；移交记录可解释为何未修，但不能视为关闭。

**LOW：无。**

其余核对结果：

- **负控不是全部空判据。** `030813` 尾注确已撤销失败结论；`030951` 原始事件流确有一条完成的 `command_execution`，状态完成、退出码 0，未把模型自述计入执行。记录也包含目录跑前、跑后未进入 trust 表。
- **重定向证据的边界仍需保留。** 临时 `CODEX_HOME` 与真实 HOME 的等同性确已列为未证明；只有 `config.toml` 哈希，不能证明整个用户级目录零写，尤其 auth 仍软链到真实文件。
- **结构门不是此前那种恒绿假门。** 单行裸 `os.open` 回退确实使它失败；但两向锚只证明该词法形状，不能证明所有 `dir_fd` 来源和子路径安全，因此不能据此关闭上述 BLOCKER。
- **正常新建时端口正确**：模板和说明直接使用 `$PORT`；三条旧门的宿主替换保留了原有测试形状。新增写面清单与目录、配置、AGENTS.md 对应，双宿主去重正确。生成后再做在位判的时机合理，但该判据只检查文件形态。生成代码中未发现执行 Codex 命令的语句。
