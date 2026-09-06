> 批次: BATCH-2026-09-05-第十二批 · 车道 Y9 · 卡 CARD-G2-6 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-6-r3.md)"`
> 审查绑定: `ff105706`（送审时 HEAD = round-2 整改 commit）
> ⚠️ **本轮之后代码又改了**：8 条经本机独立复现**全部成立**，已逐条整改
> （`evidence-g26/codex-r3-claims-AFTER-FIX-*.txt` 显示修复前后的行为翻转）。
> **卡族轮次已用满 3 轮**，这一轮整改**未再送外审**，登记为「整改未复审」——
> 详见验收单 §十二。故本存档亦**不绑合并态**。
> 会话头自证（抄 .stderr 头部含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**结论：本轮仍不能收口。** 现有测试实跑 **68 passed**，但隔离夹具复现了三个报告写入阻断项，以及普通文件不可读时返回 0 的假绿。

行号简称：V＝[verify_vault_install.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py)，M＝[vault-install-manifest.json](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json)，T＝[test_vault_install_manifest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py)，S＝[install-vault.sh](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh)。

- **BLOCKER：大小写目录别名可以直接绕过禁写检查。**  
  本机实测 `--vault …/vault --report …/VAULT/report.txt`：两个目录名指向同一目录，`resolve()` 保留大小写差异，检查放行，**返回 0，报告实际出现在 vault 内**。无需硬链接或软链。  
  **依据：**V:758、V:726–728。  
  **修复：**在 `_check_report_location()` 补充现存祖先目录的文件系统身份校验，并覆盖临时落点；不能用简单转小写代替，也不能宣称只加 inode 比较就穷尽所有别名。

- **BLOCKER：独占创建失败后，会删除不属于本次调用的临时文件。**  
  预先创建外部 `.report.txt.tmp-<PID>`，让 vault 内软链指向它；报告最终路径检查通过，`O_EXCL` 失败后却执行 `unlink(tmp)`。实测 **返回 2，但原文件已被删除，vault 内软链变成悬空**。  
  **依据：**V:488–506；落点检查只针对最终报告路径，见 V:759。  
  **修复：**记录临时文件是否由本次调用成功创建，仅清理自己拥有的文件；同时校验临时落点，改用随机独占临时名。

- **BLOCKER：禁写根没有覆盖完整可达范围，扫描失败也被忽略。**  
  两种静态布局均已复现：
  ① `vault/link → outsideA`，而 `outsideA/link → outsideB`，报告写入 `outsideB` 后，vault 经两层链接看到的内容改变；  
  ② vault 内目录权限为 `0111`，允许按已知名字访问、禁止列目录，里面已有指向外部的软链。扫描产生 `unreadable` 后仍放行写报告。  
  两例均 **返回 0 并改变被审树可见内容**，与已声明的 TOCTOU 无关。  
  **依据：**V:320–335、V:470–477、V:726–728。  
  **修复：**补齐可达目录的别名扫描，按目录身份去重、处理环；无法完成安全性扫描时拒绝落盘。

- **HIGH：两侧普通文件均不可读时，`unreadable` 阻断失效。**  
  分别对两侧 `CLAUDE.md`、两侧 `.claude/hooks/leaf.txt` 设置 `000` 权限，文件内容故意不同。两种布局都得到：`content_drift=[]`、`unreadable=[]`、**rc=0**。  
  **依据：**`_leaf_digest()` 在 V:420–421 返回标记，但 V:438–439、V:456 都没有登记不可读状态；只有 `_walk` 的标记在 V:450–454 被登记。  
  **修复：**让叶子摘要同时传播读取状态，顶层文件和目录内叶子统一登记；补双侧普通文件不可读的回归测试。

- **MEDIUM：单次 `os.write()` 忽略短写，可能成功发布截断报告。**  
  在隔离子进程中设置 `RLIMIT_FSIZE=1`，调用 `_write_report(path, "ABCDE")`，实测函数正常返回，最终文件只有 `b'A'`。没有使用模拟写函数。  
  **依据：**V:492–495。  
  **修复：**循环写满全部字节，成功后才执行替换。

- **MEDIUM：清单中的孤立代理字符仍能逃出预期错误处理，并留下临时文件。**  
  仅把清单 `source` 改成 JSON 字符串 `"\ud800"`：`load_manifest()` 接受，随后写报告抛出 **UnicodeEncodeError**，没有返回约定的 2，且留下已创建的临时文件。  
  **依据：**V:203–205、V:664、V:491–496。  
  **修复：**校验会进入报告的字符串可编码性；创建临时文件前完成编码，并统一管理异常与资源清理。`role` 也需要同类处理。

- **MEDIUM：`extra_scan.dir="."` 仍造成规范化后的误报。**  
  实测同一份根目录扫描，`dir=""` 返回 0；改成 `"."`、`"./"` 或 `".//"`，已声明的 `a` 被报告为 extra `./a`，返回 1。  
  **依据：**V:165–168、V:622、V:643–644。  
  **修复：**根扫描统一表示为 `""`，或用相对路径运算构造扫描结果，避免字符串拼接产生 `./`。

- **LOW：不限类型的精确 exclude 仍漏登记悬空软链。**  
  实测悬空的 `learning_events.jsonl`、`.obsidian/workspace.json` 都没有进入 `intentionally_excluded`；后者又被 extra 豁免，最终返回 0。去掉 `kind` 的方向正确，存在性判断尚未补齐。  
  **依据：**V:397–399、V:643–644；M:53、M:60。  
  **修复：**精确 exclude 使用包含悬空链接的存在性判断，例如 `lstat()` 或 `exists() or is_symlink()`。

- **LOW：新增的 `raw/**`、`templates/**` 没有被现有测试钉住。**  
  我在临时副本中删除这两条，重新运行，仍然 **68 passed**。  
  **依据：**M:56–59；T:133–140、T:497–498 未覆盖这两条，fixture 也未向其下放入内容。  
  **修复：**加入两目录存在内容时的精确排除分类断言。

- **LOW：方括号测试的集成部分不能证明“含方括号的声明”正确工作。**  
  T:863–866 的辅助函数断言有效，但 T:869–873 使用的实际规则是 `outputs/**`，没有含 `[` 的清单声明。恢复旧 `GLOB_CHARS="*?["` 会打红常量断言，但字面模式 `outputs/[abc].json` 仍可正确匹配；因此“变异变红”不能单独证明这里存在行为回归。  
  **依据：**T:856–873、V:379–405。  
  **修复：**用真实含方括号的 exclude 声明，验证分类、摘要过滤以及 `a.json` 的负例。

其余指定问题的核对结果：

- **临时文件与并发：**稳定布局下，临时文件和报告位于同一父目录，不会正常产生跨文件系统替换。两个独立进程 PID 不同，临时名通常不冲突；写同一报告时后替换者覆盖前者。同 PID 重入、PID 复用后的残留仍受上述误删问题影响。父目录确实位于被审树内且路径表示一致时，现有前缀门会拒绝。
- **`resolve()`：**本机 Python **3.14.4** 实测，悬空软链返回未来目标路径并加入禁写根；内部软链增加冗余根；自环返回未完全解析的路径，没有进入 `except OSError`。V:476 将悬空软链作为异常例子的注释不准确。其他 Python 版本未运行验证。
- **`unreadable`：**`_walk` 捕获 `scandir` 打开、迭代和条目类型查询的 `OSError`，不读取文件字节，也不跟随软链目录。`_leaf_digest` 的同名标记属于另一条错误路径，目前没有汇入阻断列表。另有 `_iter_relative()` 丢弃错误类型、无 `--source` 时不读取 copy 文件内容的范围限制。
- **清单与脚本：**按 S:63、S:74 补 `raw/**`、`templates/**` 正确；`nondir` 与 S:86 的类型集合一致：普通文件、各类软链、FIFO 等非目录条目，真实目录除外。去掉两个路径排除项的 `kind` 也正确。
- **匹配与规范化：**怪异括号等经过 `re.escape()`，不会直接变成正则语法注入；实测含 `/`、NUL、孤立代理字符的 `match` 也被接受，但可能静默零命中。普通 `//`、`./` 的归并没有发现误合并不同 POSIX 条目；本机反斜杠是字面字符，`a\b` 与 `a/b` 不合并。`fullmatch()` 的整改正确。
- **AST 门：**豁免在语法上足够窄，只接受字面的 `sys.stdout.write`、`sys.stderr.write`。但它不验证文件描述符身份，也不是完整的写能力证明；T:598“标准输出不碰文件系统”的注释说得过满。

独立变异结果如下；这不是对原有 16 条记录的认证：

| 本次变异 | 结果 |
|---|---|
| 移除 unreadable 的退出码贡献 | 仅 `test_unreadable_alone_still_blocks` 失败 |
| 移除软链目标禁写根 | 仅 `test_report_behind_vault_symlink_is_refused` 失败 |
| 恢复 `GLOB_CHARS="*?["` | 仅方括号测试失败 |
| 删除 `raw/**`、`templates/**` | 68 条全部通过 |

总评：本轮核对了指定四文件、68 条测试、上述真实文件系统反例和四项独立变异；没有修改工作树或运行安装脚本，也未读取原有 16 条变异的脚本、记录，因此不能确认其完整映射。原子替换、显式遍历和清单修正的方向正确，但 **V:18“第三道才承重、前两道只是早退”的论证不成立**：换 inode 能保护旧 inode 的其他名字，不能保护通过目录别名看到的目录项，也不能阻止错误清理删除旧文件。落点检查和写入资源管理仍然必须共同承重。
