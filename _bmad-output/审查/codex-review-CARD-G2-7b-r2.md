> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7b round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b-r2.md)"`
> 审查绑定: `970c4668`（送审时的 HEAD；本轮整改在其后另开 commit）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（另 `sandbox: read-only`）

> 裁定: **4 BLOCKER / 2 HIGH / 4 MEDIUM / 2 LOW**，七条全部成立、无一驳回。
> 逐条处置、行为门替换与 r2 变异验证见 UAT §十三 round-2。

---

本轮仍有 BLOCKER，禁写面修复不完整。以下依据限定代码与 44 份证据；未运行部署或测试套件，未读取环境文件、密钥或 live vault。限定证据中未见疑似明文密钥。

**[BLOCKER] 路径解析仍可能让所有候选解释同时偏离实际写入位置。**  
file:line：`scripts/deploy-vault.sh:125,131,157,243-251`  
为什么成立：`cd` 默认采用逻辑路径；折叠 `..` 后不再解软链；命令替换会剥掉末尾换行；`set -- $p` 还会展开通配符。  
怎么看到：下列输入都存在判据放行、实际写入保护目录的条件：

- `/safe/link/../probe`，其中 `link → $HOME/.codex/sub`：实际落点是 `.codex/probe`，但默认 `cd -L` 和字符串折叠都得到 `/safe/probe`。**`pwd -P` 无法恢复此前已经折掉的路径。**
- `/safe/missing/../alias/probe`：`missing` 不存在，`alias → $HOME/.codex`；折叠得到 `/safe/alias/probe` 后，没有再次解析 `alias`。
- `/safe/link<LF>/probe`：`link<LF>` 是保护目录软链，另有安全目录 `/safe/link`；`dirname` 的命令替换丢掉路径末尾换行，转而解析错误目录。
- 字面路径 `"$HOME/*/../.codex/probe"`：`norm_path` 可以把 `*` 展开为当前工作目录中的多个名字，而后续带引号的写入操作将其当作字面目录名。
- 字面 `"~/probe"`：只有判据展开 `~`，实际操作仍使用原字符串；若当前目录下名为 `~` 的目录是保护目录软链，两者落点不同。

纯函数核验也确认：以 `/private` 为保护目录时，`/var/../probe` 被判 MISS；`cd -P /var/..` 得到 `/private`，脚本的 `cd /var/..; pwd -P` 得到 `/`。

**[BLOCKER] 大小写归一没有覆盖 `.git` 和环境文件名规则。**  
file:line：`scripts/deploy-vault.sh:198-208`  
为什么成立：虽然计算了 `lc`，这两处仍比较原始 `cand`、`seg`，因此 `.GIT`、`.ENV` 等没有经过大小写比较。  
怎么看到：纯函数中 `/safe/.GIT/probe`、`/safe/.ENV.local` 均 MISS，而对应小写形式命中；在大小写不敏感文件系统上不能据此保护同一对象。

**[BLOCKER] 新的 `.claude*` 前缀规则丢失了已有软链物理目标的保护。**  
file:line：`scripts/deploy-vault.sh:177-190,224-228`  
为什么成立：旧实现登记已有 `.claude*` 的解析结果，新实现只留下 HOME 下的词法前缀。  
怎么看到：若 `$HOME/.claude → /external/claude`，传入 `/external/claude/probe` 或另一条指向它的软链，三种解释都不含 HOME 前缀，因而漏拦。新增前缀规则不能替代已有目标的登记。

**[BLOCKER] 三个目录参数通过检查，不代表后续实际写入对象通过检查。**  
file:line：`scripts/deploy-vault.sh:375-381,449-460,481,661`  
为什么成立：没有检查生成文件及临时文件的软链落点；此外，preflight 的构建会写入未纳入检查的 harness。  
怎么看到：合法 `--env-dir` 内预置 `.env.probe.tmp` 指向保护文件，步 2 的 `: >` 就会沿链截断；已有 `.env.probe` 的软链也会被 B4 跟随写入。另将完整 harness 放在保护目录、显式把三个参数放到安全位置，缺少 main.js 时仍会执行构建写入。这些问题均不依赖 installer 复制逻辑。

路径问题的预期 rc 如下。这里统一使用 `--env-dir`，假设其他预检正常；**0 表示 dry-run 未被禁写面拒绝，不表示 apply 一定成功**。

| 形态与输入 | 当前预期 rc |
|---|---:|
| 普通软链 `/safe/alias/probe`，alias 指向 `.codex` | 71 |
| `$HOME/.CODEX/probe` | 71 |
| `/safe/.GIT/probe` | 0，漏拦 |
| `$HOME/missing/../.codex/probe`，没有组合软链 | 71 |
| 相对 `../.codex/probe`，cwd 为 `$HOME/safe` | 71 |
| 字面 `~/.codex/probe` | 71 |
| `.codex/space name/probe` | 71 |
| `.codex/a<LF>b/probe` | 71 |
| 多重普通软链最终指向 `.codex` | 71 |
| `$HOME/safe/up/.codex/probe`，up 指向父目录 HOME | 71 |
| 上述 `link/..`、缺失段后软链、末尾换行软链 | 0，漏拦 |

**确实会误拦合法物理路径**：例如 `$HOME/.codex/out/../probe`，其中 `out → /safe/sub`，物理落点是 `/safe/probe`，但 `norm(raw)` 命中 `.codex`，返回 71。你明确接受“多拦”，因此这里不另列缺陷。

`lower()` 依赖 locale：本机纯函数核验中，`en_US.UTF-8` 将 `ÄÖÉİΣ` 转为 `äöéiσ`，`LC_ALL=C` 则保持原样。普通中文不需要大小写转换；但这个 `tr` 不能证明与 APFS 的 Unicode 等价规则完全一致。

**[HIGH] “默认不启动容器”的测试继承宿主授权开关，可能先执行真实启动再报红。**  
file:line：`backend/tests/unit/test_deploy_vault_sh.py:58-65,586,652`  
为什么成立：`_run()` 继承整个环境，`_apply()` 没有移除 `CLS_DEPLOY_ALLOW_DOCKER_UP`；宿主值为 1 时会进入真实 `up/down` 分支。  
怎么看到：沿 `_apply → _run → step5` 追踪该变量即可；测试中的 SKIP 断言发生在脚本执行之后，无法阻止启动。这是开关整改后留下的新回归。

**[HIGH] 14 处失败判定仍不完整，配置生成和证据摘要都存在失败后报 OK 的路径。**  
file:line：`scripts/deploy-vault.sh:482-500,895-905`  
为什么成立：`seed_env_file` 的追加操作没有逐项判 rc；证据里的 `shasum` 失败被外层成功的 `printf` 掩盖，后续仍写 `rc=0`。  
怎么看到：让某次白名单追加失败、后续固定字段及 `mv/chmod` 成功，或者让一个摘要读取失败，当前函数仍可返回 0。

按步骤核对如下：

| 步骤 | 剩余失败传播问题 |
|---|---|
| 1 | `413` 的 grep 读错被当作无碰撞；`427` 的 lsof 异常被当作空闲；`435` 的 find 管线即使返回非零，只要部分计数够大仍能 OK。 |
| 2 | `482、486、490-497` 的写入失败未可靠传播，最后 `mv/chmod` 可以将其掩盖。 |
| 3 | `572` 的读取失败可变成空值通过；`625、627` 将 grep rc 2 当作无残留；B5 回读漏判 rc，见下一条。 |
| 4 | 正常路径的复制、模板化、校验和清理已有判定；但准备镜像时提前失败后，EXIT 清理失败只设置变量，没有再输出该错误。此时仍是 74，不是成功。 |
| 5 | `776` 的 mkdir 未判；后续 config 重定向通常会兜底，不能仅据此断言假绿。`up/down/curl` 的主要返回码已分别检查。 |
| 6 | 摘要失败被外层 printf 掩盖；整个 `{…}` 的失败判断也不等于检查其中每条命令。 |

`run_step` 对**实际返回到它的状态**映射正确：0→OK，2→SKIP，其余→70+N。问题是内部错误可能没有传播出来；顶层 shell 错误也不保证经过这个映射。

**[MEDIUM] B5 回读仍漏判 `cat` 返回码，但 r1 的“旧 key＋两处新值”顺序执行漏洞已经关闭。**  
file:line：`scripts/deploy-vault.sh:587-604,635-686`  
为什么成立：A4 已检查读取 rc 和格式；B5 却只比较输出，完整输出后非零仍会继续 `mv`；B3/B4 仍直接覆盖原文件。  
怎么看到：临时 key 的 `cat` 输出完整值后失败，当前比较仍相等；回读不一致后的 `rm` 若失败，也仍宣称“已丢弃”。

令 K 为 A4 选定值，三处失败态如下：

| 失败点 | key 文件 | `.env` 的 key | `data.json` |
|---|---|---|---|
| B2 | 原样或缺失 | 原样／步 2 新建空值 | key 未同步，端口可能部分改变 |
| B3 | 原样或缺失 | 原样 | 可能原样、截断、部分写入或已为 K |
| B4 | 原样或缺失 | 可能原样、截断、部分写入或已为 K | 已为 K |
| B5，mv 前 | 新建分支仍缺失；已有分支仍为 K | K | K |
| B5，mv 后 chmod 失败 | 已为 K，但权限检查未通过 | K | K |

因此，**tmp＋回读＋mv 只涉及单个 key 文件发布，不是三文件事务**。已有合法旧 key 时，K 就是该旧值，正常顺序执行不会另生成新值；要出现旧文件与另外两处不同，还需要并发替换等额外条件。

完整重跑仍先被 install 拦为 72，不能自动收敛。你已接受 adopt 留给下一卡，不因此新增阻断项；但 `672` 的“重跑自愈”注释仍与当前入口不符。

**[MEDIUM] 新增门没有充分约束新增行为，其中 docker 查询失败分支确实恒真。**  
file:line：`backend/tests/unit/test_deploy_vault_sh.py:319-355,656-670,797-817`  
为什么成立：路径用例只覆盖旧解析器已能处理的输入；源码门检查字符串数量或存在性；docker 查询失败后重复之前已经成立的断言。  
怎么看到：

- 删除两个 `norm_path` 分支并让 `lower` 原样返回，现有路径用例仍不足以杀死变异。
- 将 step4 清单改成仅 `.mcp.json`，或把 `src="$SRC_MIRROR"` 改回源树，两个源码门仍绿。
- 把失败判断改成 `if false && [ "$rc" != 0 ]`，严格 rc 的源码门仍绿。
- `docker ps` 非零分支重复已通过的 `m.group(1) == "SKIP"`，不会新增失败条件；成功分支也只检查 `cls-probe_a5` 前缀。

以上源码变异已在内存核验。部分错误可能被另一个实际 apply 用例捕获，不能因此说这些源码门本身承重。

**[MEDIUM] 严格意义上的“preflight 前零写／dry-run 零写”仍未成立。**  
file:line：`scripts/deploy-vault.sh:282,304,308,393`  
为什么成立：参数解析的 here-string 在本机 Bash 3.2 使用临时文件；Python 调用没有禁止字节码缓存。  
怎么看到：`<<< "$HOSTS"` 位于 preflight 之前；harness 推断中的 Python 导入及 preflight 的项目导入，在缓存缺失且可写时也可能产生缓存文件。

已删除的顶层 evidence mkdir 确实没有被另一个显式 mkdir 替代。上述属于隐式写入；本轮没有执行它们来制造写入证据。

**[MEDIUM] 限定存档不能支持“六步各有完整负控，且整改已复验”的主张。**  
file:line：`_bmad-output/审查/evidence-g27b/neg-envmismatch-cfgassert-20260909T140204.txt:9-14`；`mutation-20260909T141527.txt:15-16,30-31`；`step3-phaseAB-20260909T140616.txt:9`  
为什么成立：步 5 存档只证明重复执行的断言逻辑返回 1，没有证明部署入口返回 75；限定文件中未见步 6 返回 76 的负控；M3/M6 明记 SKIP，正控仍使用旧开关。  
怎么看到：区分“辅助判据拒绝”“真实步骤拒绝”及“当前整改代码复验”，不能将它们合并成六步验收通过。

**[LOW] `_logical_lines` 能抓普通续行，但仍有确定漏检，并非完整 Bash 逻辑行解析。**  
file:line：`backend/tests/unit/test_deploy_vault_sh.py:742-769`  
为什么成立：它会折叠注释末尾的反斜杠，而 Bash 不会；`splitlines()` 还把 U+2028 当作换行。  
怎么看到：在 `MSG="$abs）"` 前加一行末尾带反斜杠的注释，合并后整行被跳过，门得到空错误列表；真实 Bash 仍会报 unbound。普通变量续行的新验伪锚确实能报红，所以整条门不是恒真。

**[LOW] “六行状态”与 PyYAML 可用性检查都有名实不符。**  
file:line：`scripts/deploy-vault.sh:348-354,888`；`backend/tests/unit/test_deploy_vault_sh.py:40,845-847`  
为什么成立：第六步状态在文件写完后才追加，因此落盘只有前五行；`import yaml` 成功后再断言模块非空恒成立，也没有检查 harness 的解释器。  
怎么看到：追踪状态追加时序；或让测试解释器具有 PyYAML、harness venv 缺失它，该断言仍通过。失败入口也只打印已执行前缀，不会补齐六步状态。

其余两项核对结论：

- **compose**：五个默认值与证据中的旧常量一致，覆盖全部 profiles、默认等价和单变量覆盖的门都有有效判别力。仅这五处参数化，在插值环境相同时不会引入渲染差异；但门没有核实现网容器、镜像和项目状态，不能承诺现场 `up -d backend` 必不重建。
- **harness 推断**：0 个或 2 个 running 项目均为 64；Status 不满足大小写无关的 `running` 前缀就不计入；唯一项目的 ConfigFiles 含逗号则为 64。单个配置被接受后，只保留其目录，后续仍使用该目录的 `docker-compose.yml`，没有保留原配置文件名。
