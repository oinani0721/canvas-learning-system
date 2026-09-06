> 批次: BATCH-2026-09-05-第十二批 · 车道 Y9 · 卡 CARD-G2-6 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-6-r2.md)"`
> 审查绑定: `249de2fe`（送审时 HEAD = round-1 后的代码 commit）
> ⚠️ **本轮之后代码又改了**：7 条经本机独立复现**全部成立**，已逐条整改
> （`evidence-g26/codex-r2-claims-verified-*.txt` 复现 / `codex-r2-claims-AFTER-FIX-*.txt` 与
> `codex-r2-and-audit-AFTER-FIX-*.txt` 修复后）。故本存档**不绑合并态**，以最终 HEAD 为准。
> 会话头自证（抄 .stderr 头部含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

**本轮仍不能通过：1 BLOCKER、1 HIGH、3 MEDIUM、2 LOW。** 四组回归确实能检测对应修复被撤销，但尚不能证明四条意见全部闭环。

- **BLOCKER：`st_nlink` 只堵住了稳定的普通硬链接，报告仍能写穿被审文件。**

  **依据：**[verify_vault_install.py:541](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:541) 至 `:562` 检查路径及链接数，最后在 `:574` 原地写入。

  在本机 macOS 用真实 CLI 独立复现：将合成树内文件的可写文件描述符传给子进程，指定 `--report /dev/fd/N`。该路径 `resolve()` 后仍在树外、不是符号链接、`st_nlink=1`；**分别以 vault/source 文件为被写对象，两次均退出 0，原 inode 内容被报告覆盖**。这个反例不需要竞争条件。

  此外，检查与写入之间包含完整校验过程；在这个窗口创建硬链接、替换报告路径或替换父目录，也能绕过检查。已用临时树中的确定性调度复现。

  **修复位置：**报告输出分支。应在受控的树外目录独占创建新文件，并通过同一文件描述符写入；如需覆盖报告，应写新 inode 后替换目录项，同时明确父目录的并发边界。继续给原地覆盖增加一次 `stat()` 不能闭环。

  对问题①各形态的结论是：

  | 报告形态 | 当前行为 |
  |---|---|
  | 不存在的普通路径 | 跳过链接数检查；父目录稳定且随后没有路径替换时，可以安全创建 |
  | 指向树内的符号链接，包括指向尚不存在的树内路径 | `resolve()` 后由树内路径检查拒绝 |
  | 指向树外的符号链接 | 检查解析后的目标；并不能证明该目标没有其他访问别名 |
  | 与被审树位于不同文件系统 | 普通硬链接不能跨文件系统创建；这不消除文件描述符别名或路径替换问题 |

- **HIGH：目录枚举不完整时仍可能报告一致，摘要确实存在漏报。**

  **依据：**[verify_vault_install.py:334](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:334) 使用 `rglob("*")`。本机 Python 3.14.4 会抑制遍历中的 `PermissionError`。

  已运行真实 CLI：源 `.claude/hooks/child/hidden.txt` 存在，但 `child` 权限为 `000`；目标对应 `child` 是可读空目录。结果为 **match=1、content-drift=0、exit=0**。不可见内容被当成不存在。

  **修复位置：**目录枚举及错误传播。使用能明确报告遍历失败的实现；无法完整读取时，不得归入 match 或返回 0。

  普通可读树的结构没有因“叶子摘要”而丢失：每个目录仍记录相对路径及 `D:`，空目录增删、层级变化可以区分。上述不可读目录是已确认的判等反例；未读取旧实现，不能断言它一定始于本轮。

- **MEDIUM：增加 `kind` 的方向正确，但把 `rm -f` 等同于 `is_file()` 是错误映射。**

  **依据：**[verify_vault_install.py:254](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:254) 中，`dir` 判定与 [install-vault.sh:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/install-vault.sh:84) 的默认 `find -type d` 对齐：两者均不把目录符号链接算作目录。

  但 `:265` 的 `is_file()` 与安装脚本 `:86` 不等价：

  | 条目 | `is_file()` | `rm -f` |
  |---|---:|---|
  | 普通文件、指向普通文件的链接 | True | 删除 |
  | 指向目录的链接、悬空链接、FIFO | False | 删除 |
  | 真实目录 | False | 不删除 |

  后三种可删除条目均在临时目录实测；源含这些归档队列条目、目标已正确删除时，校验器仍报 `.claude/hooks` drift、退出 1。

  另外，[manifest:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/vault-install-manifest.json:53) 和 `:56` 给 `learning_events.jsonl`、`workspace.json` 增加了 `kind=file`，脚本按路径“不复制”的声明没有这个条件。实测同名 `workspace.json` 目录会被报 extra。

  **修复位置：**类型枚举、`_kind_ok()` 和上述清单项。为 `rm -f` 明确表达“非目录条目”，用 `lstat` 区分链接与真实目录；删除两个纯路径排除项不必要的类型限制。`原白板/**`、`检验白板/**`、`节点/**`、`outputs/**` 留空是恰当的。

- **MEDIUM：共享匹配器仍会错误排除名称末尾带换行的条目，导致漏报 drift。**

  **依据：**[verify_vault_install.py:225](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:225) 使用 `$`，`:283`、`:302` 使用 `match()`；`$` 可以匹配最后一个换行之前的位置。

  实测源文件名为 `"pending_archives_keep.jsonl\n"`、目标缺少该文件时，校验器将其排除并返回 **drift=[]、exit=0**；安装脚本的 shell 模式不会匹配它。`"__pycache__\n"` 也有同类问题。

  **修复位置：**模式编译及全部匹配调用点，改为严格完整匹配，例如 `fullmatch()`；补两个尾随换行反例。

- **MEDIUM：action 原反例已修好，但“非法清单统一退出 2”仍不成立。**

  **依据：**[verify_vault_install.py:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:134) 的读取捕获面有限；`:191-194` 对 `extra_scan` 只检查键存在，未校验值。真实 CLI 结果如下：

  | 输入 | 当前结果 |
  |---|---|
  | `action: [] / {} / 123 / null` | 正确抛 `ManifestError`，退出 2 |
  | `extra_scan.dir: [] / {} / 123 / null` | 加载放行，随后 `TypeError`，退出 1 |
  | `extra_scan.match: ["*"] / 123 / null` | `AttributeError` 或 `TypeError`，退出 1 |
  | `extra_scan.match: [] / {}` | 静默接受，可退出 0，扫描实际失效 |
  | `extra_scan.dir` 为绝对路径或 `../outside` | 接受并扫描临时树外目录；前者可随后抛 `ValueError` |
  | 非 UTF-8 清单、5000 位 JSON 整数 | 分别为 `UnicodeDecodeError`、`ValueError`，退出 1 |
  | `path` 含孤立代理字符 `\ud800` | 加载通过，写报告时 `UnicodeEncodeError`，退出 1 |
  | `path` 含 NUL、单段长 300 字符 | 本机运行时按 missing 处理，退出 1 |

  **修复位置：**加载阶段完整校验扫描字段、路径字符及扫描范围；规范化路径后检查重复；将读取、解码和解析失败转换成 `ManifestError`。同时限制输入大小，避免错误消息无界展开。已测的 2000 层嵌套非法字段仍正确退出 2，不能笼统声称“嵌套必然逃逸”。

- **LOW：三处共用类，但对子孙是否豁免的语义仍不完全一致。**

  **依据：**[verify_vault_install.py:288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/scripts/verify_vault_install.py:288) 的祖先检查用于摘要，extra 在 `:439` 仅调用 `matches_exact()`。

  使用合法自定义 `extra_scan` 扫描 `.claude/hooks/__pycache__/*` 时，目录被列为 excluded、子文件从摘要剔除，却仍报该子文件 extra。**现行清单的三个扫描根不会触发此问题。**

  **修复位置：**extra 同样考虑已排除祖先，或在 schema 明确限制扫描根。祖先排除本身是正确的：目录被剪除，其子孙即使自身不匹配目录规则也应剔除；仅孩子被排除时，父目录应保留。

- **LOW：回归测试承重真实，但尚未保护三个使用点和符号链接语义。**

  **依据：**[test_vault_install_manifest.py:445](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-y9-maingoal/backend/tests/unit/test_vault_install_manifest.py:445) 只断言 excluded 分类；`:211-224` 的合成树只创建普通文件和目录。

  独立将 `matches_exact()` 中的类型判断移除，**42/42 仍通过**；仅移除目录判定里的 `not is_symlink()`，也是 **42/42 通过**。

  **修复位置：**类型回归补精确 drift、extra 断言，并覆盖指文件、指目录、悬空链接；配套补上述不可读目录、严格匹配和报告别名反例。

独立变异验证的完整结果如下。基线为 **42 passed**：

| 单独撤销的修复 | 确切失败集合 |
|---|---|
| 硬链接拒写分支 | `test_report_hardlinked_into_vault_is_refused`，1 条 |
| 摘要排除过滤 | `test_normally_deployed_vault_is_not_reported_as_drift`，1 条 |
| `_kind_ok()` 恒为 True | `test_exclude_kind_matches_script_type_conditions`，1 条 |
| action 字符串检查 | `test_non_string_action_still_exits_2` 的 `[]`、`{}`，2 个参数实例 |

前三组确实各只有一条变红；第四组不是所有参数都承重，`123`、`None` 原本就会被枚举检查拒绝。失败均直接命中目标断言，没有靠其他分类兜住。硬链接用例先在退出码断言失败，后面的字节保全断言尚未执行。另将祖先检查改成只检查自身，正确部署测试也会唯一变红，说明其中的非空 `__pycache__` 确实验证了子树剔除。

总评：实际核对了三个送审文件、安装脚本相关语义及 round-1 原文；在隔离临时目录运行了全部 42 条测试、独立变异及上述反例，未修改仓库、未运行安装脚本、未访问真实 vault。结论绑定本次读到的文件内容；未读取 round-1 历史实现或你们的变异证据文件，因此独立验证的是“局部撤销当前整改”的结果，不能签认历史实验记录。现网五个 extra、G2-7 和 G2-8 均未裁定。
