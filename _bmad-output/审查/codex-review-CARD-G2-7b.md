> 批次: BATCH-2026-09-07-第十三批 · 车道 U3 · 卡 CARD-G2-7b round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-7b.md)"`
> 审查绑定: `a6978b58`（送审时的 HEAD；本轮整改在其后另开 commit）
> 会话头自证（抄 .stderr 含 model 行的三行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`（另 `sandbox: read-only`）

> 裁定: **2 BLOCKER / 4 HIGH / 3 MEDIUM / 2 LOW**，七条全部成立、无一驳回。
> 逐条处置与复验见 `_bmad-output/验收单/UAT-CARD-G2-7b-2026-09-09.md` §十三。

---

存在 BLOCKER。以下是限定代码与证据的只读审查结果；未执行部署、测试或 Docker，所读证据未见疑似明文密钥。

[BLOCKER] 禁写判据会漏掉大小写别名和不存在路径中的 `..`，三个参数共用判据并不等于覆盖完整。
  
  `scripts/deploy-vault.sh:112、125、158、167、283`
  
  为什么成立：缺失后缀原样拼回，比较区分大小写，而且解析结果没有替换后续实际使用的路径。
  
  怎么看到：对合法新 vault 做静态分支推演，以下两个漏拦输入在 apply 时可让 `.env.<vault>` 写入 `.codex`。

下面统一以 **`--env-dir` 的值**为输入，假定 harness 完整、vault 尚不存在且名字合法、端口空闲；rc 是**整个脚本 dry-run 的预期值**，不是实测值。判据自身“命中”返回 0，脚本对应 71。

| 形态 | 输入及前提 | 判据／预期 rc |
|---|---|---|
| 目录软链 | `/tmp/link/probe`，link → `$HOME/.codex` | 命中／71 |
| 大小写差异 | `$HOME/.CODEX/probe`，大小写不敏感 APFS | **漏拦／0** |
| `..`，前段存在 | `$HOME/Desktop/../.codex/probe` | 命中／71 |
| `..`，前段不存在 | `$HOME/missing/../.codex/probe`，missing 不存在 | **漏拦／0** |
| 相对路径 | 当前 cwd 下 `../../../../../../.codex/probe` | 命中／71 |
| 未展开 `~` | 字面量 `'~/.codex/probe'` | 检查时展开，命中／71 |
| 空格 | `$HOME/.codex/has space/probe` | 命中／71 |
| 内嵌换行 | `$HOME/.codex/has`＋LF＋`line/probe` | 命中／71 |
| 多重目录软链 | `/tmp/link2/probe`，link2 → link → `.codex` | 命中／71 |
| 指向父目录的软链 | `/tmp/parent/.codex/probe`，parent → `$HOME` | 命中／71 |

另有三个缺口：

- `:134–135` 只登记**已存在**的 `$HOME/.claude*`；不存在的 `$HOME/.claude-new/probe` 漏拦，预期 dry-run rc 0。
- `:105–106` 只在检查时展开 `~`。例如 `'~/safe'` 检查 `$HOME/safe`，实际写入却使用 cwd 下字面量 `~/safe`；若 cwd 的 `~` 是指向保护目录的软链，检查与写入对象分离。
- 普通文件软链的最终目标未解析；末尾换行还会被命令替换剥掉。因此不能把上述目录软链正例推广成“完整 realpath、字节保真”。

[BLOCKER] `--apply` 在禁写检查之前就创建 evidence 目录。
  
  `scripts/deploy-vault.sh:740、742、289`
  
  为什么成立：顶层 `mkdir -p "$EVIDENCE_DIR"` 先于 preflight，之后返回 71 也不能撤销已经发生的写入。
  
  怎么看到：推演 `--apply --evidence-dir "$HOME/.codex/new_probe"`：可先创建目录再被拒绝；现有禁写负控没有 `--apply`，覆盖不到这条路径。

[HIGH] 已有目标的 dry-run 仍然写入，零写承诺不成立。
  
  `scripts/deploy-vault.sh:575、579、583、604`
  
  为什么成立：步 4 只判断 vault 是否存在，没有判断 APPLY，随后创建 evidence 目录、请求写报告，非 8011 还会创建并修改源镜像。
  
  怎么看到：沿“合法已有 vault、不传 `--apply`”分支检查；`dryrun-zerowrite-20260909T135409.txt:6` 仅覆盖目标不存在的情况。

[HIGH] 步 5 并非固定只执行 config；`--apply --activate` 缺省会进入真实 up/down。
  
  `scripts/deploy-vault.sh:58、671、678、683`
  
  为什么成立：`CLS_DEPLOY_NO_DOCKER_UP` 缺省为 0，只有显式为 1 才在断言后 SKIP，注释中的额外授权没有执行闸门。
  
  怎么看到：沿开关未设置的 activate 分支即可看到 `up -d backend` 和失败后的 `down`；`step3-phaseAB-20260909T140616.txt:9` 只证明设置为 1 的那次运行跳过了 up。

[HIGH] 多处命令失败会被后续返回值覆盖，打印成 OK，个别 apply 路径还会错误 SKIP。
  
  `scripts/deploy-vault.sh:256`
  
  为什么成立：`"$fn" || rc=$?` 确实抑制函数体内 errexit，但并非每条重要命令都有显式失败处理。
  
  怎么看到：逐步令下列命令失败，再追踪函数尾部的返回值。

| 步骤 | 未正确处理的失败 | 最终可能显示 |
|---|---|---|
| 1 | `:365–368` 的 mkdir/cp 失败仍返回 0；`:343` 的 find 部分失败但仍计到足够数量 | OK，甚至称 main.js 已就位 |
| 2 | `:383–402` 派生 env 的写入、mv、chmod，以及 `:413` 调用结果均未检查 | installer 返回 0 时仍 OK |
| 3 | `:463` 读取失败被当成空值；缺失绑定字段也放行；`:539` env chmod 失败未处理 | OK，权限或绑定未达成 |
| 4 | `:568–569` 清理失败仍清空镜像变量；`:575–577` 在 apply 中目标消失也返回 2 | 清理失败仍 OK；未验证却 SKIP |
| 5 | `:688–689` curl 失败前已输出含 vault 名的部分响应，追加空串不会清除它 | 健康检查仍可能 OK |
| 6 | `:726、731–734` 哈希、报告重定向、追加 rc 行失败均未处理 | evidence OK，最终 rc 0 |

步 5 的 **config 管道、Python 断言和 up 命令本身**有显式返回码检查，不能笼统说它们都会假绿；但 `:684、692` 忽略 down 失败，仍声称“已回滚”。

[HIGH] 密钥同步不是原子操作，Phase B 失败后整脚本重跑不能自动收敛。
  
  `scripts/deploy-vault.sh:473、492、508、521、546`
  
  为什么成立：三个文件分次原地写入，没有事务或恢复入口，而已有目标会在再次进入步 3 前被拒绝。
  
  怎么看到：从首次部署、key 尚不存在的状态，分别停在 B2/B3/B4/B5 写入失败处检查三份状态。

令 K 为 A4 生成的新值，E0/D0 为进入 Phase B 前的密钥值：

| 失败位置 | key 文件 | `.env.<vault>` | `data.json` |
|---|---|---|---|
| B2 | 不存在 | E0 | 密钥仍 D0，端口修改可能部分完成 |
| B3 | 不存在 | E0 | D0、截断/损坏，或已写 K 后失败 |
| B4 写入 | 不存在 | E0、截断，或已写 K 后失败 | K |
| B5 | 不存在、空文件、部分 K，或完整 K 但权限不合格 | K | K |

这些显式写失败通常返回 **73**；B4 后的 env `chmod` 失败却可能继续成功。

整脚本重跑会先返回 **72**；使用默认 `ENV_DIR=HARNESS` 时，还可能先因自己生成的 `ACTIVE_VAULT` 记录而返回 **71**。即使单独重入步 3，损坏 JSON 也不会自动修复，非空残缺 key 则可能被当成合法旧值。

用户所问“旧 key 保留、另两处变新”存在一个精确条件：`:474` 的 `cat` **输出非空前缀 K′ 后失败**，返回码被忽略，于是 B3/B4 写 K′，B5 因“已存在”保留原文件 K，chmod 成功便报 OK。正常读取成功且无并发时，旧 key 会同步到另两处，**不会凭这段逻辑另生成一个新 key**。

[MEDIUM] rc 表、六行输出和“六步都有负控”的主张没有完整成立。
  
  `scripts/deploy-vault.sh:229、262、719、740`  
  `_bmad-output/审查/evidence-g27b/neg-envmismatch-cfgassert-20260909T140204.txt:9`
  
  为什么成立：部分失败发生在 `run_step` 外，失败分支立即退出，证据写入时也尚未加入第六步状态。
  
  怎么看到：顶层 mkdir 或推断 harness 的 cd 失败通常直接 rc 1；第 N 步失败只输出到第 N 行；成功报告中的“六行状态”实际只有前五行。

限定证据中的步 5 负控只是单独运行断言得到 **rc 1**，没有经过部署入口证明 **75**；未找到步 6 的 **76** 负控。`neg-step1-willbuild-…:3、9` 实际还是 OK／rc 0。旧记录中的非 ASCII 崩溃已有后续修复证据，不能作为当前同一缺陷继续报错。

[MEDIUM] harness 推断只取第一份配置的目录，会静默丢弃多配置上下文。
  
  `scripts/deploy-vault.sh:218、225、229、630`
  
  为什么成立：筛选条件是区分大小写的 `startswith("running")`，然后只取 `${_cfg%%,*}`，后续固定使用该目录的 `docker-compose.yml`。
  
  怎么看到：分别代入以下 compose ls 结果即可确定分支。

| 输入状态 | 行为 |
|---|---|
| 0 个 running 前缀项目 | rc 64 |
| 2 个 running 前缀项目 | rc 64 |
| 总计 2 个项目，只有 1 个符合前缀 | 采用那一个 |
| `created(1), running(1)`、`Running(...)` | 不计入；无其他合格项目则 64 |
| `running(1), exited(1)` | 仍计入 |
| `ConfigFiles=/a/base.yml,/b/override.yml` | 只取 `/a`，忽略 override |
| 第一配置父目录无法 cd | 通常直接 rc 1 |
| 恰一个合格项目但 ConfigFiles 为空 | rc 64 |

[MEDIUM] 两条源码门只证明文本存在，不能证明清单共享、镜像实参或严格失败传播。
  
  `backend/tests/unit/test_deploy_vault_sh.py:744、762`
  
  为什么成立：清单门统计全文件字串，镜像门只检查三个文本片段，没有检查它们之间的数据流和控制流。
  
  怎么看到：以下实现改动都能躲过对应源码门。

- 删除步 4 的模板化循环：步 3 已有三处真实清单引用，另有注释引用，仍满足 `refs >= 3`。
- 把 `src="$SRC_MIRROR"` 改回原源：`--source`、`SRC_MIRROR`、严格 rc 比较文本仍存在。
- 在判断失败前添加 `rc=0`：严格比较仍在，但失败已经被清掉。
- 删除真实 `--source` 参数，仅保留同名注释：文本断言仍可通过。

这些门不是形式上的恒真，而是**对上述关键功能退化不敏感**；mutation 证据中的 M3、M6 明确是 SKIP/MANUAL。

[LOW] 非 ASCII 门不是恒真，但逐物理行扫描可以被续行躲过；PyYAML 断言才是导入后恒真。
  
  `backend/tests/unit/test_deploy_vault_sh.py:707、722、730、794`
  
  为什么成立：非 ASCII 正则有正反样本和实际 KILLED 记录，但没有处理 Bash 续行；`yaml` 则早在第 38 行成功导入。
  
  怎么看到：用反斜杠续行把 `$abs` 与全角括号分到两个物理行，扫描漏掉逻辑相邻关系；测试解释器装有 PyYAML、harness 解释器没有时，`assert yaml is not None` 仍通过。

另外，`:645–646` 未检查 `docker ps` 返回码，查询失败的空输出也能通过“没有容器”断言；`:409` 的零写断言允许新建空 env 目录。

[LOW] compose 五处默认值确实等于旧常量，但 config 等价不能证明现网下一次 up 绝不会重建。
  
  `docker-compose.yml:22、65、104、146、250`  
  `backend/tests/unit/test_deploy_vault_sh.py:433、497`
  
  为什么成立：diff 的五个 fallback 均逐字一致，全 profile 门覆盖五处渲染，但没有核对运行中容器、镜像和实际部署上下文。
  
  怎么看到：五个变量未设置或为空、其他条件不变时，这次参数化本身没有引入名称变化；不能据此排除其他重建原因。

五个旧值分别是 `canvas-learning-system-neo4j`、`canvas-learning-system-neo4j-test`、`canvas-learning-system-ollama`、`canvas-learning-system-backend`、`claude-dev`。另须限定“不传变量”的含义：测试继承整个 `os.environ`，没有清除这五个变量，因此并非完全隔离的默认环境。
