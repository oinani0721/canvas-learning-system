> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7b round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-r4.md)"`
> 审查绑定: `8f525887`（送审时的 HEAD；本轮整改在其后另开 commit）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（另 `sandbox: read-only`）

> 裁定: **4 BLOCKER / 2 HIGH / 6 MEDIUM / 1 LOW**，全部成立、无一驳回。
> 其中 **B-1 / H-2 / M-1 / M-3 四条是我 r3 自己引入的回归**。

---

仍有 **4 BLOCKER / 2 HIGH / 6 MEDIUM / 1 LOW**。第四次同型回归已经出现，且不止一处。

审查限定在指定文件与 46 份证据。未修改文件、未运行部署或 pytest、未连接数据库或启动容器；完成了语法检查、无写 Bash 展开验证和内存路径模型核对。证据中未发现疑似明文凭据。

[BLOCKER] B-1：`.claude*` 的词法保护再次被 `realpath` 消掉。
  [scripts/cls_forbidden_paths.py:119](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:119)
  为什么成立：新增的 `k()` 会解析 `$HOME/.claude`；若它指向 `/external/claude-base`，尚不存在的 `$HOME/.claude-new/probe` 就失去前缀保护。
  怎么看到：内存模型中该输入返回判据 rc=0；`/external/claude-baseball/probe` 反而被误拦，说明“词法前缀”被搬到了外部目标。

[BLOCKER] B-2：两层软链可以隐藏解链途中经过的 `.git`，原始路径与最终物理路径两条检查同时落空。
  [scripts/cls_forbidden_paths.py:195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:195)
  为什么成立：`/safe/alias → /repo/.git → /external/meta` 时，原始串只有 `alias`，`realpath` 结果只有 `meta`；祖先检查也只比较最终目标。
  怎么看到：内存模型中 `/repo/.git/ev` 返回 rc=1，而访问同一对象的 `/safe/alias/ev` 返回 rc=0；不需要并发替换。

[BLOCKER] B-3：步 4 的源镜像仍是完全未经过禁写判据的显式写入面。
  [scripts/deploy-vault.sh:772](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:772)
  为什么成立：脚本直接使用继承的 `TMPDIR` 创建镜像，随后复制、修改、删除；preflight 的产出清单没有这个根目录。
  怎么看到：令 `TMPDIR` 指向保护目录，其余参数合法且端口非 8011，步 4 就会在保护目录创建镜像；事后删除撤不回已经发生的写入。
  
  这是显式 `mktemp/cp/sed/rm` 路径，不属于已登记的 here-string／字节码隐式写面。

[BLOCKER] B-4：固定临时文件的硬链接可以无竞争地绕过判据和 `-L`。
  [scripts/deploy-vault.sh:451](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:451)
  为什么成立：合法目录中的 `.env.<vault>.tmp` 若与保护区普通文件共享 inode，`realpath` 仍得到合法路径，`-L` 为假，但截断会修改共享 inode。
  怎么看到：同文件系统上预置这样的硬链接，追踪 preflight 到 `: > "$ENV_FILE.tmp"`；无需触碰目标 vault，也不会先被 installer 的已有目标闸门拦住。

[HIGH] H-1：新增 `-L` 不能保证写入时仍访问检查过的对象，而且仅 install 日志补了临写检查。
  [scripts/deploy-vault.sh:511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:511)
  为什么成立：检查与打开文件分离，515 行截断后，521 行又重新打开；日志本身或任一父目录都可能在窗口内被替换。
  怎么看到：在检查后或两次打开之间替换路径即可写穿；其他尚无临写复核的点包括 451、665、691、714、796、825、949 行，build 两个输出也未进入 `-L` 清单。

[HIGH] H-2：新增 `VAULTS_ROOT` 比较会让合法含空格路径在安装完成后失败。
  [scripts/deploy-vault.sh:565](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:565)
  为什么成立：`for kv in $want_pairs` 拆词，seed 写入完整父路径，A3 却拿截断值比较。
  怎么看到：无写 Bash 验证 `/tmp/course vaults/course` 会产生 `VAULTS_ROOT=/tmp/course` 和额外的 `vaults` 项；入口会在安装后 rc=73，重跑再被 rc=72 拦住。

[MEDIUM] M-1：失败证据整改又吞掉了证据发布失败。
  [scripts/deploy-vault.sh:953](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:953)
  为什么成立：追加 `rc=76` 和 `mv` 均改为 `|| true`，随后无条件宣称“证据已标 rc=76”。
  怎么看到：令 shasum 失败后再让追加或发布失败；进程返回 76，但正式报告可能不存在或仍为旧报告。
  
  此外，919 行大括号内早期 `printf` 的失败仍可能被后续成功覆盖。

[MEDIUM] M-2：seed 白名单读取仍把“读取失败”当成“没有该键”。
  [scripts/deploy-vault.sh:455](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:455)
  为什么成立：`grep | tail` 的任何非零状态都进入 skipped 分支，没有区分 rc=1 与读取错误。
  怎么看到：让读取错误发生在 preflight 通过后的 seed 读取阶段，固定六键仍可写齐并返回成功，白名单值却静默回退。

[MEDIUM] M-3：参数展开替换没有保持单段相对路径和尾斜杠语义。
  [scripts/deploy-vault.sh:252](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:252)
  为什么成立：`VAULT=course` 得到 `VAULT_PARENT=course`，installer 目标变为 `course/course`；`/tmp/course/` 则得到空 vault 名。
  怎么看到：无写展开即可确认；入口没有执行头注的“必须绝对路径”约束，dry-run 的 494 行还使用旧 `dirname`，展示与实际参数不同。

[MEDIUM] M-4：M-5 路径表达式门仍漏钉六个实际对象。
  [backend/tests/unit/test_deploy_vault_sh.py:1152](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1152)
  为什么成立：断言没有覆盖 key tmp、两个 build 输出、verify 报告、compose 报告及正式 deploy 报告。
  怎么看到：分别删除这些对象的判据参数，该门仍绿；已列表达式也只是子串检查，留在注释或不可达代码中仍能满足断言。

[MEDIUM] M-5：`.claude*` 外部目标登记门仍不能证明登记行为存在。
  [backend/tests/unit/test_deploy_vault_sh.py:1294](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1294)
  为什么成立：测试只查两个源码字符串，没有访问合成 HOME 中 `.CLAUDE-cache` 对应的外部目标。
  怎么看到：保留大小写条件、删除判据 108 行的 `raw.append(...)`，该门仍绿；不存在前缀门及 HOME 枚举失败门也不能捕获这次退化。

[MEDIUM] M-6：逐段创建与原始 `.git` 两项核心整改仍缺定向行为门。
  [backend/tests/unit/test_deploy_vault_sh.py:1025](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1025)
  为什么成立：现有样本缺少“中间创建进入保护区、最终落点安全”和“`.git` 指向外部安全名字”两种拓扑。
  怎么看到：将逐段列表退回 `[path]`，或删掉原始 `.git` 检查，相应旧样本仍能靠最终落点通过；本轮两个修复没有被锁住。

[LOW] L-1：HOME 不可枚举门没有验证它制造的权限故障确实成立。
  [backend/tests/unit/test_deploy_vault_sh.py:1320](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1320)
  为什么成立：`chmod(0o111)` 不保证特权测试进程无法枚举目录。
  怎么看到：以能绕过该权限限制的身份运行，正确实现可以成功枚举 HOME，测试却要求 rc=1。

其余重点核对结果：

- **逐段模型方向正确，但不是实际写入清单。** 保留 `..` 能覆盖先创建再回退，跳过 `.` 不遗漏目录创建；中间段放 outputs 不会让普通 `.env` 文件成为可穿过的目录。模型也检查已存在且仅被遍历的祖先，因此会多拦。循环软链、不可搜索目录处，判据可能给出未完全解析的结果，但权限和链稳定时实际操作也会失败，不能仅据判据 OK 宣称写穿。`//` 被压成 `/`，跨系统等价性并未由本轮在机测试证明。
- **HOME fail-closed 本身没有发现正常可枚举时恒拒的回归。** HOME 不可枚举时，即使部署目标合法，也会持续 rc=71；这是当前安全证明依赖 HOME 枚举的明确代价。B-1 的前缀错误是另一回事。
- **M-4 反向锚有效。** 删除 `_run` 的环境剥离会暴露 `ALLOW=1`。`lsof` 的 rc=2／rc=1 两门也有效，能分别捕获“错误当空闲”和“永远拒绝”；但没有 rc=0 占用样本，不能称完整三态覆盖。
- **源码门不等于恒真。** 非 ASCII 门有正反样本和续行样本；清单计数门不能证明两步骤实际共用清单，镜像源码门不能证明实际 source 绑定。已登记的 `assert yaml is not None` 才是导入成功后的恒真断言。
- **证据不能替代本轮执行。** 最新允许读取的 mutation 记录绑定 r2；本轮没有据此宣称当前代码的测试或变异检查已通过。

密钥中间态仍如当前注释所述，`fsync` 提升错误可见性，没有形成三文件事务：

| 失败位置 | key 正式文件 | `.env` 中 key | 插件中 key |
|---|---|---|---|
| B2 | 尚未发布 | 原值／空 | 原值／空，端口可能部分更新 |
| B3 | 尚未发布 | 原值／空 | 可能旧值、部分文件或新值 |
| B4 | 尚未发布 | 可能旧值、部分文件或新值 | 新值 |
| B5 | 可能未发布或已发布 | 新值 | 新值 |

稳定状态下，A4 读取已有 key 的 rc／格式检查已修复旧的残缺读取问题；并发替换仍属于 H-1。整脚本重跑不能自动收敛，这项声明准确。

Compose 五个默认值与证据中的原常量一致，all-profiles 门覆盖了五处配置渲染；**配置等价不能单独证明现网执行 `up` 不会重建容器**。`--harness` 推断对零个／多个 running 项目返回 64，非 running 前缀项目不计入，多个 `ConfigFiles` 也拒绝推断；这些分支与整改说明一致。
