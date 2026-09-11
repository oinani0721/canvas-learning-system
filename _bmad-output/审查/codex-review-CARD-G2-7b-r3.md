> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7b round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-r3.md)"`
> 审查绑定: `560bf59f`（送审时的 HEAD；本轮整改在其后另开 commit）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（另 `sandbox: read-only`）

> 裁定: **4 BLOCKER / 4 HIGH / 5 MEDIUM / 1 LOW**，全部成立、无一驳回。
> 逐条处置见 UAT §十三 round-3（含 MEDIUM-4/5 门加强，未留给下一卡）。

---

**仍有 BLOCKER，整改尚未闭环。** 本轮未修改文件、运行部署或测试套件；以下复现结论来自限定代码、证据和纯内存语义核验。

[BLOCKER] 最终 `realpath` 不能代表 `mkdir -p` 的完整写入面，且会抹掉原始 `.git` 命名。
  [scripts/cls_forbidden_paths.py:147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:147)
  为什么成立：`--env-dir="$HOME/.codex/new/../../deploy_env"` 最终解析到合法目录，但 `mkdir -p` 会先创建受保护的 `.codex/new`；普通目录不会触发祖先软链检查。另有 `.git -> /external/meta` 时，解析后的路径丢失 `.git` 段，祖先检查也不补查这个命名规则。
  怎么看到：令 `new` 不存在，判据预期 rc=0，而步 2 已写保护区；将 `.git` 设为外部目录软链，其下路径同样预期被放行。

[BLOCKER] 证据目录过检不代表证据文件过检，新加的日志预创建可以截断保护文件。
  [scripts/deploy-vault.sh:470](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:470)
  为什么成立：291–302 行没有提交 `install-$TS.txt`、verify/compose 报告、deploy 报告及其 tmp；合法 evidence 目录中的既有日志软链会被 `: > "$ilog"` 沿链截断。
  怎么看到：预置对应时间戳的 install 日志软链，指向保护文件；preflight 通过后，installer 尚未执行，截断已经发生，不需要并发替换。

[BLOCKER] `outputs` 豁免了任意解析目标的 env 文件名，遗漏的 tmp 软链拒绝让它变成实际绕过。
  [scripts/deploy-vault.sh:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:297)
  为什么成立：`ENV_FILE.tmp -> /safe/existing.env` 被 outputs 放行，而 309–310 行的 `-L` 列表没有 tmp；419 行随后截断旧 env，448 行还会把软链本身发布为 `ENV_FILE`。
  怎么看到：在独立合法 env 目录预置上述 tmp 链，目标 vault 保持不存在；判据预期 rc=0，步 2 即破坏旧文件。

这里“**只跳过 env 文件名规则**”在代码分支上成立；问题是豁免没有限定为脚本拥有的那个文件。key、插件、build 产物也进入同一豁免组，并不必要。

[BLOCKER] 判据保住了 argv 的换行，调用 installer 时仍会把父目录末尾换行剥掉。
  [scripts/deploy-vault.sh:473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:473)
  为什么成立：对 `/safe/link<LF>/ok_name`，判据检查的是含 LF 的安全目录，`"$(dirname "$VAULT")"` 却变成 `/safe/link`；若后者链接到保护目录，installer 收到的落点已经改变。
  怎么看到：纯内存 Bash 已确认这次字符串变化；配置上述两个不同目录名即可让保护检查与安装实参分裂。436 行生成 `VAULTS_ROOT` 也有相同问题。

[HIGH] `.claude*` 外部目标登记仍会因枚举失败或大小写不同而静默缺失。
  [scripts/cls_forbidden_paths.py:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:93)
  为什么成立：HOME 有执行权限但无目录读取权限时，已知子路径仍可访问，`listdir` 却失败并被 `pass`；此外 `name.startswith(".claude")` 本身大小写敏感。两种情况都可能丢掉外部软链目标，HOME 前缀无法补救。
  怎么看到：已有 `.claude -> /external/claude` 但 HOME 不可枚举，或实际条目为 `.CLAUDE-cache -> /external/cache`；直接指定外部目标下的新目录，预期 rc=0。

[HIGH] Unicode 等价路径仍可能产生不同 key；此项依赖保护根的实际名称。
  [scripts/cls_forbidden_paths.py:81](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/cls_forbidden_paths.py:81)
  为什么成立：`realpath(...).lower()` 不统一 NFC/NFD 拼写；在将两种拼写视为同一对象的 APFS 上，保护根或其软链目标含 `课程-é` 时，`课程-e\u0301` 可以比较不相等。
  怎么看到：用两种规范化拼写分别作为保护根和待写路径，字符串判据预期放行；本轮未构造磁盘样本，不能声称已完成 APFS 实地复现。普通、不含可分解字符的汉字路径不因此自动受影响。

[HIGH] 步 3 的 Python 写入可能在缓冲刷新时失败，却仍继续发布 key。
  [scripts/deploy-vault.sh:604](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:604)
  为什么成立：604–605、625 行的 `open(...).write(...)`／`json.dump(..., open(...))` 没有显式关闭文件；延迟至文件对象析构的写入错误可以成为被忽略的异常，而 Python 仍返回成功。
  怎么看到：纯内存缓冲流已复现“写 API 返回、析构时报错、进程继续”；因此外层检查 Python rc 不足以证明三处同值。步 4 是否另行发现损坏，不能据此保证。

[HIGH] 既有 env 的一致性检查仍允许读取失败、缺键和空值通过。
  [scripts/deploy-vault.sh:522](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:522)
  为什么成立：读取管道不检查 rc，且只有 `have` 非空才比较；已有文件不会经过 seed 的六键回读，`VAULTS_ROOT` 也不在此处比较范围内。423 行白名单读取失败仍被记作 skipped。
  怎么看到：已有 env 缺少 `API_PORT`／`ACTIVE_VAULT`，或者读取失败产生空输出，A3 仍通过；六键回读只验证新 seed 文件的键名存在，补不上这个分支。

[MEDIUM] 本轮新增的 `printf … || exit 1` 绕过了步骤返回码，是明确回归。
  [scripts/deploy-vault.sh:435](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:435)
  为什么成立：`{ …; }` 在当前 shell 执行，内部 `exit 1` 直接结束部署，外围错误处理与 `run_step` 的 72／73 映射均不会执行。
  怎么看到：纯内存同构 Bash 已得到进程 rc=1，未出现步骤 FAIL 行；失败发生时也到不了新加的六键回读循环。

[MEDIUM] `_sha_fail` 仍以非空输出代替成功，而且失败证据仍发布 `rc=0`。
  [scripts/deploy-vault.sh:867](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:867)
  为什么成立：hash 管道 rc 没有检查；非空输出加非零退出仍算成功。空输出虽设置失败标记，却先在 879 行写入 `rc=0`、发布文件，然后才返回 76；外层大括号也不能捕获此前任意一次 `printf` 失败。
  怎么看到：纯内存已复现“摘要非空、命令退出 1、步骤仍返回 0”；空输出分支则直接存在证据与进程返回码矛盾。

[MEDIUM] 步 1 的 skills 数量仍可能把部分读取结果当成完整结果。
  [scripts/deploy-vault.sh:373](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/scripts/deploy-vault.sh:373)
  为什么成立：`find | wc | tr` 的退出码被忽略，只比较最终数量。
  怎么看到：让 find 输出达到阈值后报读取错误，preflight 仍可打印树完整并返回成功。

[MEDIUM] 专门的授权剥离门没有调用 `_run`，无法锁住真实剥离行为。
  [backend/tests/unit/test_deploy_vault_sh.py:869](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:869)
  为什么成立：测试自己重新构造并剥离环境，再直接执行探针。
  怎么看到：仅删除 `_run` 的 67–68 行，保留 `_STRIP_ENV`，这个专门门的执行结果完全不变。

[MEDIUM] 新判据门未覆盖祖先保护与 `.claude*`，产出对象门仍只验证标签。
  [backend/tests/unit/test_deploy_vault_sh.py:1005](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1005)
  为什么成立：现有软链样本最终都落在 `prot`，在祖先检查之前已经命中；没有 `.claude*` 两条规则的定向输入。1136 行起仍只检查对象标签，未核对实际路径。
  怎么看到：删除祖先检查调用、删除 `.claude*` 两条规则，现有这组样本仍满足断言；保留 `plugin-data:` 标签却传入安全父目录，源码门也不会红。

[MEDIUM] 新内容比较门能杀 M9，但不能排除目标与自身比较。
  [backend/tests/unit/test_deploy_vault_sh.py:1172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1172)
  为什么成立：`content-drift=0`、`match>0` 和“源镜像”文案，没有证明基准独立于目标。
  怎么看到：把 `src="$SRC_MIRROR"` 改成 `src="$VAULT"` 并保留文案，自比较仍满足这些观察条件；目前没有目标漂移负控来排除它。此逃逸是静态推导，未运行变异。

[LOW] 通配符门没有验证判定结果，不能证明“不展开 glob”。
  [backend/tests/unit/test_deploy_vault_sh.py:1098](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u3-deploy/backend/tests/unit/test_deploy_vault_sh.py:1098)
  为什么成立：允许 rc=0 或 1，只要求输出一行。
  怎么看到：对所有含 `*` 的输入固定返回一行 HIT，该门仍通过。

你点名的路径边界，补充结论如下。表中 rc 指 **helper**；命中后部署入口会映射为 71。`P` 为保护目录，`S` 为安全目录。

| 形态及示例 | 预期判定 |
|---|---|
| `S/alias/x`，alias 指向 P | rc=1 |
| `S/link/../x`，link 指向 P/sub；含多重链接亦同 | rc=1 |
| P 的 ASCII 大小写别名 | rc=1 |
| 相对路径、普通空格，最终落在 P | rc=1 |
| 字面 `~/x` | rc=1，明确拒绝 |
| `//…/P/x/` | 本案 POSIX 语义下未发现独立绕过 |
| 名称中 LF | helper 保真；后续 `dirname` 重建仍有上述 BLOCKER |
| 循环软链 | 可能 rc=0，但稳定状态下实际写入会遭遇 ELOOP；不能直接当成写穿证据 |
| 不可遍历中间段 | 可能 rc=0，但实际写入也受权限阻挡；不同于 HOME 仅不可枚举 |
| NFC/NFD 等价拼写 | 条件性漏拦，见 HIGH |
| 祖先检查超过 64 层 | 上限数的是**路径段回退次数**；深尾路径可让检查尚未抵达保护软链就结束 |

密钥中间态仍然不是事务，作者本轮关于重跑的更正准确：

| 失败位置 | key 文件 | env | data.json |
|---|---|---|---|
| B2 | 未写新 key | 原值／seed 空值 | key 未同步，端口可能部分修改 |
| B3 | 未写新 key | 原值／空值 | 可能旧值、新值或损坏 |
| B4 | 未写新 key | 可能旧值、新值或损坏 | 已写选定 key |
| B5 | 尚未发布或已经发布 | 已写选定 key | 已写选定 key |

正常入口重跑会先被 install 拦为 72，不能自动收敛。A4 已有 key 的读取 rc、格式检查，以及 B5 回读 rc，确实修复了此前“读残缺值却保留完整旧 key”的具体问题。

其余核对：

- 步 4、步 5 的主要动作已有显式失败传播；75／76 入口负控仍缺。`lsof` 的 rc=1 和命令不存在都仍被放行，本轮没有验证其真实错误码契约，不能仅凭三分支宣告完整。
- `_logical_lines` 有有效的续行验伪锚，并非恒真；旧清单计数门和源镜像源码门仍可被保留无效字符串绕过。`assert yaml is not None` 仍是已登记的恒真断言。
- M9–M13 的最终变异记录与当前脚本/helper 哈希相符，M14 明确为 NOGATE；这些证明所列变异被杀，不证明上述未测分支。
- Compose 门覆盖五个名称及渲染等价，不能独自保证实际容器不重建。指定 diff 实际只有 deploy、helper、测试三个文件，compose/install 改动不在这两个提交之间。
- harness 推断对零个／多个 running 项目返回 64；非 running 前缀不计入；大小写不敏感；唯一 running 项目含多份 ConfigFiles 时拒绝推断。
- 授权范围内 46 个证据文件未发现疑似明文凭据；部分旧正控仍使用旧开关，不能直接证明当前入口行为。
