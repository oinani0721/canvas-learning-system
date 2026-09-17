> 批次: BATCH-2026-09-11-第十四批 · 车道 T2 · 卡 CARD-G2-8 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-8-r4.md)"`
> 审查绑定: `9526cfca`（该轮 HEAD；本轮后有 r4 整改 commit，故本档**不绑**最终 HEAD）
> 会话头自证（抄 .stderr，行号如实标；.stderr 本身不入库）:
> `.stderr:2` `OpenAI Codex v0.153.3` / `.stderr:5` `model: gpt-6-astra` / `.stderr:9` `reasoning effort: ultra`

---

复核绑定 **`9526cfca75fca457ddada46d0961bc4d65c03999`**，首尾 HEAD 一致。结论：**1 HIGH、1 LOW；未发现 BLOCKER / MEDIUM。r3 四条具体处置均核对通过，但开账仍有一个未覆盖窗口。**

1. **HIGH — [scripts/deploy-vault.sh:444](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:444)**：负控条件是复查通过后、打开 fd 前路径对象发生变化；`exec 9>>` 仍重新解析路径，现有门只覆盖复查之前和开账之后，未覆盖这个窗口。
2. **LOW — [backend/tests/unit/test_deploy_vault_sh.py:3321](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3321)**：兄弟实例存活对照只覆盖健康断言失败，没有 `CLS_FAKE_UP_RC≠0` 输入覆盖脚本第 1378 行的另一处回滚分支。

其余自述逐项核对如下：

| 项目 | 结论 |
|---|---|
| 回滚只拆本实例 | **健康失败路径核对通过**。[测试:3064](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3064) 的兄弟端口结果确实取决于 Docker 共用项目清单；第 3332、3336～3338 行核对运行前后状态，非恒 200。 |
| index journal 隔离 | **核对通过**。[脚本:1428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1428) 导入 harness 的真实模块，计算两条路径及 legacy、兄弟 key 对照；测试复制真实模块。 |
| Lance 计时、进度与上限 | **核对通过**。[脚本:1346](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1346) 的原校验块经纯内存对照：前导零按十进制，零、超界、超长、非 ASCII 数字等均拒绝；空环境值按第 121 行回退 120。轮询请求和间隔均受剩余预算约束，未发现取值导致上限取消或无限循环；阶段记录耗时和 `table_count`。 |
| Graphiti readiness | **核对通过**。[测试:3412](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3412) 覆盖不可达、缺字段、非就绪、非法 JSON、嵌套和截断响应；同时要求跳过原因出现、全账无 `result=ready`，并有成功正控。未发现上述失败面报 ready。 |
| `--also-push` | **核对通过**。[脚本:1593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1593) 对混合分隔、缺键、空值及引号按消费口径处理；命中已有项在截断、写入之前退出。非目标字节保留，CRLF 对照使用整文件字节比较。 |
| 未授权激活的 SKIP | **核对通过**。[脚本:1316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1316) 返回 2，步状态明确为 SKIP，evidence 明确未进入真激活；整跑 `rc=0` 表示流程正常结束，不能解读为激活已执行。 |
| 步 1～4及名称口径 | **核对通过**。[脚本:511](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:511) 起至步 5 前的 **41,549 字节完全一致**；连字符拒绝、下划线放行门使用真实 harness。 |
| 新增写面与计数 | **核对通过，范围须说准确**。[脚本:536](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:536) 已申报阶段账及报告对象；`.env` 是清单外的新增目标，但第 1545 行起另行经过禁写判据、复查、`open_pinned`、硬链接检查和 `write_all`，直接写保护同级。四个计数确实随第三处写入从 2 增至 3；全局禁止字节码缓存。 |

r3 四条处置的专项结论：

- **HIGH 原问题核对通过**：[脚本:1333](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1333) 开账失败立即返回；三处 up/down 输出全部走 fd 9，成功开账后没有业务文件的按路径写入。关闭 fd 9 的纯 Bash 对照得到 `Bad file descriptor`、返回非零且命令本体不执行；当前开账失败路径到不了这些命令，失败退出会释放脚本 fd。此前述处置不消除本轮 HIGH 窗口。
- **MEDIUM 引号判重核对通过**：[脚本:1593](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1593) 的纯内存源码执行覆盖 `'beta'`、`"alpha","beta"`、`a,'b' c` 和转义引号；反斜杠保留、引号删除，与给定 `tr` 口径一致。后两类未列入提交的参数门，但本轮补核通过。
- **LOW-2 核对通过**：[测试:3901](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3901) 同时钉住头注与实现的原串 20 位、剥零后 5 位。
- **LOW-1「等价、非缺陷」核对通过**：[脚本:1608](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1608) 两版分隔符条件等价，保留行尾的拆分再拼接恒还原原字节；五种指定形态及额外字节串对照均相同，没有找到不同输出。最终负控确实针对删除分隔符造成的键粘连。

“双处落账”只能限定为**流程继续到步 6**：[测试:3339](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/backend/tests/unit/test_deploy_vault_sh.py:3339) 明确要求步 5 失败时没有 deploy 报告，失败阶段账只在 compose-config 中。

负控存档核对通过：[最终存档:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/negctl-final-15seg-20260914T234549.txt:307) 确为 **15 段全 KILLED**，恢复哈希与当前脚本一致。README 对旧 case 覆盖、断言锚错误、过期锚及多转义的解释与存档吻合；其中 Lance 当时已经测试失败，只是负控判定锚选错。ACTIVE 旧变异“无效果”须限定于当时选中的输入：已有键且追加新名字的动态门仍只核清单，未核其他字节；不能把最终 15 段解释为全部路径覆盖。

本轮未修改文件、未连接 Docker／Neo4j，也未重跑 pytest；[187 passed、9 skipped](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/unit-deploy-r3fix-20260914T234955.txt:55) 是存档结果，不是真态验收。


