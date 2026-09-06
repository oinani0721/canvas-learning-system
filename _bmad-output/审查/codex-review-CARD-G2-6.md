> 批次: BATCH-2026-09-05-第十二批 · 车道 Y9 · 卡 CARD-G2-6 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-6.md)"`
> 审查绑定: `249de2fe`（送审时 HEAD = 代码 commit `249de2fe`）
> ⚠️ **本轮之后代码已改**：四条指控经本机独立复现**全部成立**，已逐条整改（证据
> `evidence-g26/codex-r1-claims-verified-*.txt` 复现 / `codex-r1-claims-AFTER-FIX-*.txt` 修复后）。
> 故本存档**不再绑定合并态**，须以 round-2 的复审为准。
> 会话头自证（抄 .stderr 头部含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

本卡暂不能通过：**27 项清单覆盖等价成立，但“只读”边界存在可写穿路径，排除项也会错误触发内容漂移。**

- **BLOCKER：树外报告若是树内文件的硬链接，会覆盖被审对象。**  
  **依据：**[verify_vault_install.py:474](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:474) 仅检查解析后的路径是否位于两棵树内；[同文件:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:496) 用 `write_text()` 原地覆盖报告。若树外 `report.txt` 与 vault 或 source 内的 `Dashboard.md` 共享 inode，检查通过后，树内文件也被覆盖。这个反例不需要竞争条件。  
  AST 判据有盲区：[test_vault_install_manifest.py:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py:419) 的调用名清单无法识别对象别名、`.open("w")`、`.write()` 或间接调用；`:445-450` 也只确认唯一一次 `write_text` 位于 `main()`，不能证明接收者安全。当前硬链接漏洞完全满足该断言。  
  **修复位置：**报告输出分支 `:472-496`，避免原地写入已有 inode，例如在经过校验的树外位置独占创建新报告；补充分别指向 vault/source 文件的硬链接负控。通读未发现其他显式目录创建、临时文件或目标树写入分支。正常直接执行主脚本也未发现独立的目标树 `__pycache__` 落盘路径；测试导入时在 `:65-74` 明确禁用了字节码写入。

- **HIGH：目录摘要未应用排除规则，正常部署剪除的文件会被误报为 `content-drift`。**  
  **依据：**[verify_vault_install.py:257](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:257) 对目录全部子孙计算摘要，`:338-350` 据此分类；exclude 分支没有参与过滤。源 vault 若含 `.claude/scripts/__pycache__/cached.pyc` 或 `.claude/hooks/pending_archives_2026.jsonl`，目标按安装脚本正常剪除后，两个父目录仍会被报 drift，退出 1。  
  [test_vault_install_manifest.py:316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py:316) 恰好暴露测试缺口：它仅向目标添加这两类排除件，却只断言 excluded 和 extra，遗漏 `content_drift` 与退出码。原校验函数的纯内存反例得到 **match 26、drift 2、excluded 2、exit 1**。  
  **修复位置：**摘要函数对源、目标统一应用排除规则，并剪除被排除目录的全部子孙；上述测试改用完整桶断言并检查退出码 0，另补“仅源含排除件”的场景。

- **MEDIUM：两个隐含排除模式的路径范围基本正确，但没有完整表达脚本的文件类型条件。**  
  **依据：**[manifest:57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json:57) 的 `.claude/**/__pycache__` 经当前正则解释，覆盖 `.claude` 下零层、一层及多层目录位置，不覆盖 `.obsidian`，这一点正确。但 [install-vault.sh:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh:84) 有 `-type d` 条件，而 [verify_vault_install.py:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:233) 至 `:251` 将文件、目录等条目统一按路径匹配：同名普通文件也会被判 excluded。  
  同理，`:86` 的 `rm -f` 不删除目录，manifest 的 `pending_archives*.jsonl` 却也会匹配同名目录。**因此不能签认完整语义逐项等价。**模式只列目录根、未逐个列出子孙，本身不构成缺陷；目录根可以代表被剪除子树。  
  **修复位置：**清单增加明确的类型条件，校验器的 excluded 分类、extra 豁免及摘要过滤共同遵守该条件；补普通文件、目录和符号链接反例。

- **MEDIUM：非法清单不总能得到承诺的退出码 2。**  
  **依据：**[verify_vault_install.py:165](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:165) 直接执行集合成员判断，`action: []` 或 `{}` 会抛出 `TypeError`；`:487-491` 只捕获 `ManifestError`，直接 CLI 执行会产生 traceback 并退出 1。  
  **修复位置：**`load_manifest()` 先验证 action 类型，再检查枚举，将非法配置统一转换为 `ManifestError`；增加对应退出码负控。

**LOW：无。**

其余问题的复核结论如下：

- **① 数组覆盖通过。**独立展开得到 `6 / 8 / 6 / 5 / 2` 项；与清单比较，路径及 `copy/skeleton` 动作均一致，两侧差集为空，无重复。实际合计为 **21 copy + 6 skeleton + 8 exclude + 1 generate = 36**。依据：[install-vault.sh:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh:63)、[manifest:12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json:12)。`.canvas-config.yaml` 的单条 `generate` 及说明同时保留了“不从源复制”和“按 vault 重新生成”，没有必要重复登记 exclude；依据：[manifest:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json:62)。校验器目前仅检查生成项存在，不验证 YAML 内容。
- **③ 密钥登记通过。**[manifest:25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json:25) 和 [:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json:34) 两项只有 `path / role / action / origin / note`，角色均为 `secret-or-local`，未见内容或摘要。未读取两个密钥文件。
- **④ 当前表达式的行为明确，历史一致性未证实。**[install-vault.sh:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh:16) 在 `CLS_REPO` 未设置或为空时，均取 `/Users/Heishing/Desktop/canvas/canvas-learning-system`；`:17-19` 的三个变量由此派生。设置覆盖值时，三者都会随之改变，其中固定的 worktree 后缀仍保留。旧版本不在读取面内，不能独立签认“历史逐字节一致、diff 仅一行”；`:51-55` 也未列入允许读取的段落，无法核对模板源解析。按你描述的薄壳职责，将 skill 的绝对入口收敛留待后续处理是合理的，不会直接造成本卡清单与校验器不一致；但 `CLS_REPO` 不会改变实际调用哪个脚本。未查看 skill 或交接记录，不能确认已登记。
- **⑤ 四个主反例确实分别承重，嵌套排除补充例过松。**[测试:270](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py:270) 至 `:313` 精确比较目标桶完整路径列表，并要求其他三桶为空，无法靠另一类别的非零退出码兜住；这些期望对当前 fixture 合适。`:349-360` 的骨架目录被文件占位反例也能独立检测类型分支。问题限定在上述 `:316-330` 的漏断言。五次变异的具体补丁、失败集合和摘要复原证据未提供，不能认定已独立复核通过。

总评：实际核对了指定清单、校验器全文、测试全文、安装脚本指定段落和报告，并进行了集合计算、模式检查及纯内存反例验证；没有运行安装脚本或磁盘 pytest，也没有修改文件。[live-diff.txt:8](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/_bmad-output/审查/evidence-g26/live-diff.txt:8) 确实记载 `28 / 0 / 5 / 8、exit=1`，但未提供 source，内容漂移未评估；本次确认的是报告文本，未重新核实现网，也未裁定五项 extra 的归属。
