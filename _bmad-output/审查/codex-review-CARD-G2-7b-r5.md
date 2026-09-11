> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7b round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-r5.md)"`
> 审查绑定: `6b9ef8ce`（= HEAD `5f9c6917` 的代码面；`git diff --stat 6b9ef8ce HEAD -- . ':(exclude)_bmad-output'` 为空，其间两个 commit 只动 `_bmad-output`）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（另 `sandbox: read-only`；session `01a0859a-94c7-7fe3-9037-5cbd1c72383c`）

> 裁定: **4 BLOCKER / 3 HIGH / 5 MEDIUM / 0 LOW**。
> 车道复核后**全部认下、无一驳回**（逐条评估与现实暴露面见验收单 §十三 round-5）。
> ⛔ 本轮 = D-15 轮次上限第 5 轮且仍有 BLOCKER/HIGH ⇒ **停下交主 session 人审，车道不再改代码**。

---

**仍不建议通过；第五次同型回归已确认。** 当前五个被审文件均逐字节等于 `6b9ef8ce`，该提交到 HEAD 的代码 diff 为空。以下反例通过源码审查及内存核验确认，未实际写入目标、运行 pytest、连接数据库或启停容器。

[BLOCKER] **B-1：改回词法前缀时，丢掉了 HOME 本身为软链的物理别名轴。**  
  `scripts/cls_forbidden_paths.py:125,256`  
  为什么成立：HOME 指向另一目录时，物理 HOME 下尚不存在的 `.claude-new` 既未被枚举，也不匹配词法 HOME 前缀。  
  怎么看到：令 HOME=`/homealias → /homephys`，输入 `/homephys/.claude-new/probe`；同一内存拓扑下，`8f525887` 判 HIT，`6b9ef8ce` 判 OK——这是有前后版本对照的新回归。

[BLOCKER] **B-2：`resolve_chain` 仍漏掉目标路径的中间软链，并再次在解链前折叠了 `..`。**  
  `scripts/cls_forbidden_paths.py:143,150,178`  
  为什么成立：它只追完整路径的末段软链；目标中的祖先软链不会递归遍历，而 `normpath` 又会提前删除需要检查的段。  
  怎么看到：下面两种拓扑在当前逐段判据中均全部 OK，但落点属于 `.git` 的实际目录：

- `alias → hop/sub`，`hop → repo/.git`，`.git → external/meta`：链记录止于 `hop/sub`，漏掉里面的 `.git`。
- `alias → /repo/.git/../sub`，`.git → /external/meta/sub`：实际落点仍是 `/external/meta/sub`，记录却被折成 `/repo/sub`。

[BLOCKER] **B-3：HOME 可枚举但不可搜索子项时，外部保护目标仍会漏登记。**  
  `scripts/cls_forbidden_paths.py:77,106,115,323`  
  为什么成立：`listdir` 成功不代表解链成功；HOME 有读权限但无执行权限时，`realpath(strict=False)` 可吞掉 EACCES、返回未解析路径，而 `enumerate_failed` 仍为 False。  
  怎么看到：令其中的 `.claude-cache` 指向独立可写的 `/external/cache`，直接检查该外部目录；保留真实 `realpath`、在内存注入上述权限错误后，当前判据返回 OK，写入路径本身无需经过 HOME。

[BLOCKER] **B-4：检查 TMPDIR 根不足以阻止源镜像中的软链写穿。**  
  `scripts/deploy-vault.sh:860,868,874`  
  为什么成立：`cp -R` 会保留源树子目录软链，随后 `sed -i` 直接写镜像中的文件，未重新检查这些文件的实际路径。  
  怎么看到：让源树 `.claude/hooks` 指向保护目录，里面存在 `session-end-archive.py`；镜像根合法，但镜像中的 hooks 仍指向保护目录，端口模板化会写到那里，**无需竞争窗口**。

[HIGH] **H-1：两处 Python 写入不能整体宣称为“原子防护”。**  
  `scripts/deploy-vault.sh:733,736,769`  
  为什么成立：`O_NOFOLLOW` 只原子拒绝末段软链，仍跟随祖先软链；`fstat` 与 `ftruncate` 之间也仍有新增硬链接的窗口。  
  怎么看到：在 preflight 后替换父目录，令目标成为保护区内链接数为 1 的普通文件，两处检查仍能通过；因此残留窗口不仅存在于已声明的 Bash 写入。

[HIGH] **H-2：单段相对 vault 修好了安装位置，却没有统一 compose 挂载的解析基准。**  
  `scripts/deploy-vault.sh:300,532,917`；`docker-compose.yml:218`  
  为什么成立：installer 按调用 cwd 解释 `.`，生成的 `VAULTS_ROOT=.` 却由 compose 按 `--project-directory "$HARNESS"` 解释。  
  怎么看到：从不同于 harness 的目录部署 `--vault course`，新库在调用目录，compose 挂载来源却是 harness；当前 config 断言只验名称和端口，抓不到此错配。

[HIGH] **H-3：已有 `.env.<vault>` 权限较宽时，新密钥先写入，权限随后才收紧。**  
  `scripts/deploy-vault.sh:769,778,783`  
  为什么成立：`os.open(..., 0o600)` 不会改变既存文件权限；已有 0644 文件会在写入、flush、fsync 期间保持可读，失败还可能使该状态持续存在。  
  怎么看到：预置内容与参数一致的普通 0644 env 文件，追踪 B4 写入至后置 `chmod` 的顺序；这不要求目标 vault 预先存在。

[MEDIUM] **M-1：`nlink` 判据仍会把部分查询失败翻译为通过。**  
  `scripts/deploy-vault.sh:196,203,209`  
  为什么成立：没有检查 Python 返回码；纯数字检查也没有覆盖零值和 Bash 整数溢出。  
  怎么看到：提取原函数只读执行，查询输出 `1` 后返回非零，函数仍返回 0；超长纯数字通过 `case` 后令 `-gt` 返回 2，函数同样放行，而 `2`、非数字控制组正确拒绝。

[MEDIUM] **M-2：三条新源码门仍允许关键退化存活。**  
  `backend/tests/unit/test_deploy_vault_sh.py:1198,1206,1600`  
  为什么成立：这些门检查文本存在或计数，没有验证检查对象、执行顺序及数组元素保真。  
  怎么看到：以下变异均已在内存中通过对应原门，**不代表整套测试已重跑**：

- 把两处 `ftruncate` 移到 `fstat` 前，“写前复查”门仍绿。
- 把 `lnk="${item#*:}"` 改为 `lnk="$ENV_FILE"`，单一清单门仍绿。
- 去掉 `want_vals` 中 `$VAULT_PARENT` 的双引号，数组源码门仍绿；空格行为门只跑 dry-run，根本不到 A3。

[MEDIUM] **M-3：合法父路径中的字面引号仍会导致安装后误拒。**  
  `scripts/deploy-vault.sh:648`  
  为什么成立：`tr -d` 删除值内所有单双引号，而非只解析外围引用。  
  怎么看到：使用含 `O'Brien` 的父目录，seed 保存原值，A3 却比较 `OBrien`，返回 73；`%q` 修复不了这一层。

[MEDIUM] **M-4：九类变异存档不足以独立核验红因和最终代码绑定。**  
  `_bmad-output/审查/evidence-g27b/mutation-r4-20260909T171918.txt:6`  
  为什么成立：存档只有结果摘要，没有确切变异 diff、指定 nodeid、失败正文及代码哈希；还原仅声明与未提交的变异前状态相同。  
  怎么看到：第 7 行尤其需要澄清——仅删除当前 `lex_key` 比较、保留词法前缀，并不会让 `claude-baseball` 被误拦，必须知道实际还改了什么。

[MEDIUM] **M-5：红集三步判别支持哨兵漂移，但不足以断言“本卡引入 0”。**  
  `_bmad-output/审查/evidence-g27b/dir-red-diff-r4fix.txt:12`  
  为什么成立：总量相同不证明事件来源相同，隔离重跑移除了用例间交互，没有直接引用也不能排除顺序、共享状态或时序的间接影响。  
  怎么看到：仍需在匹配的环境、顺序及进程条件下对照基线与最终代码，并关联哨兵事件来源；限定读取面内只有摘要，不能独立复核被引用的 raw。

LOW：无新增。

其余重点核对结果：

- **删掉 `hits()` 层的直接 `chain_hits()`，在当前逐段入口下没有发现独立损失。** 每个前缀自身都会启动祖先检查；加回那次调用也修不好 B-2。
- **`lex_key` 折叠显式输入中的 `..`，没有单独造成所担心的中间段漏检。** `.claude-new/../safe` 中的 `.claude-new` 已先被逐段检查。
- **`[ -d "$p" ] && return 0` 没有所怀疑的 `set -e` 回归。** `%q` 对 Bash 参数可往返、可粘贴；复杂字符在部分 locale 下会降低可读性。
- **`.claudeXXX` 会被拦，这是既定规则的直接代价。** 在本卡已明确选择保守方向的前提下，应保留该覆盖；它与 B-1 的物理 HOME 漏面是两件事。
- **`PENDING_WRITES` 不是全部写入面的证明。** 参数目录可由逐段判覆盖，动态镜像可单独登记，installer 内部按既定契约处理；但本脚本自己的模板化文件、镜像后实际对象不能仅凭根目录合法就放行。
- **假 Python 机关在当前夹具下有区分力。** 非数字负控检查了具体错误消息，并有数字正控；但包装器恒返回 0，没有覆盖 M-1 的“有输出但执行失败”。
- **循环、超过跳数上限、实际写入路径不可搜索，不能直接算作已证实写穿。** 内核通常会拒绝该次访问；B-3 则是保护目标登记失败、写入走独立路径，性质不同。
- 漏传 `PYTHONDONTWRITEBYTECODE=1` 的运行不应参与同条件对账，这一处置方向正确。Compose 五个默认字符串确实与旧常量相同，但 config 等价不能独立证明现有容器不会因其他运行态差异重建。允许读取的证据中未发现疑似明文密钥。
