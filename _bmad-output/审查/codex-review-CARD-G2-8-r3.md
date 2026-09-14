> 批次: BATCH-2026-09-11-第十四批 · 车道 T2 · 卡 CARD-G2-8 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-8-r3.md)"`
> 审查绑定: `321bbeae`（该轮 HEAD；本轮后有 r3 整改 commit，故本档**不绑**最终 HEAD）
> 会话头自证（抄 .stderr，行号如实标；.stderr 本身不入库）:
> `.stderr:2` `OpenAI Codex v0.153.3` / `.stderr:5` `model: gpt-6-astra` / `.stderr:9` `reasoning effort: ultra`

---

审查绑定 `321bbeaec9c5f28fdb0df4123ce31d8d9b78451d`。**发现 1 HIGH、1 MEDIUM、2 LOW；无 BLOCKER。**

- **HIGH — [scripts/deploy-vault.sh:1329](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1329)**：开账复查已经拒绝路径的负控，若 Docker 有普通非空输出，后续 `1369/1374/1401` 仍会按该路径重定向写入；现有测试 `:3747` 只检查没有 `stage=`，且桩 up/down 没有普通输出，未覆盖此组合。
- **MEDIUM — [scripts/deploy-vault.sh:1582](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1582)**：输入 `DAILY_REVIEW_VAULTS='beta'`、本次名为 `beta` 时仍生成 `'beta',beta`，带引号混合清单的首尾名称也会重复追加；现有测试 `:3774` 仅覆盖无引号输入。
- **LOW — [scripts/deploy-vault.sh:1594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:1594)**：缺少 DAILY 键且 `ACTIVE_VAULT` 是无行尾的最后一行时，会给该行补 LF，不满足逐字节不变；现有字节门 `:3756` 仅使用已有 CRLF 行尾的输入。
- **LOW — [scripts/deploy-vault.sh:70](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/scripts/deploy-vault.sh:70)**：11～20 位、剥零后合法的输入会通过 `:1346` 校验，但头注仍声明原串最多 10 位，现有门未覆盖这处口径差异。

其余自述逐项核对如下；下表测试行号均指 `backend/tests/unit/test_deploy_vault_sh.py`。

| 核对项 | 结论与定位 |
|---|---|
| r2 HIGH：每行重新解析窗口、fd 生命周期 | **核对通过。** 脚本 `:443/:466` 开一次后只写 fd 9，脚本内没有其他使用者；成功必经 `:1513` 关闭，失败返回由 `run_step:503` 退出释放；上述 HIGH 是复查拒绝后的另一条写入路径。 |
| 失败只拆本实例、兄弟判据 | **核对通过。** 测试 `:3064` 的兄弟 curl 依赖同一运行清单，`:3332–3338` 有前后存活对照；动态证据覆盖健康失败回滚，up 失败分支的项目限定由源码核对。 |
| Graphiti readiness、r2 LOW-1 | **核对通过。** 脚本 `:1493–1507` 分别处理 curl 非零、解析失败、缺字段及非就绪值；测试 `:3448/:3452` 同时核 skipped 存在、ready 不存在，`:3455` 有就绪正控，`:3423` 包含合法对象缺 `status`。 |
| Lance 校验、r2 MEDIUM-1 | **核对通过。** 脚本 `:1339–1364` 的实际代码经无文件验证：`08/09/010→8/9/10`，`000/0` 拒绝，`00086400→86400`，`86401` 拒绝；输入到达数值比较前已限定为安全十进制范围，未出现 rc=2。 |
| Lance 轮询、r2 MEDIUM-2 | **核对通过。** 脚本 `:1457–1481` 限制探测和休眠预算；抽取实际轮询代码、以内存函数返回探测失败，预算 `1/2/3` 秒均对应退出，合法取值本身不会取消上限。 |
| index journal、阶段账写面 | **核对通过。** 脚本 `:1421–1434` 调 harness 真模块计算两条路径并对照 legacy／兄弟 key；测试 `:3157/:3379–3382` 使用真模块副本并核结果；阶段账及步 6 报告复用 `PENDING_WRITES:535–537` 的对象。 |
| also-push 指定输入与硬化 | **指定三类无引号输入核对通过。** 混合分隔、缺键、空值均有门；脚本 `:1538–1599` 保留同判据、写前复查、`open_pinned`、链接数检查和 `write_all`，新增 `.env` 虽不在步 1 清单内，实际写前仍受相同禁写约束；完整字节承诺受上述 LOW 限制。 |
| 未授权 activate 的 SKIP | **核对通过。** 脚本 `:1315` 返回 2，`:500` 明确打印 SKIP，`:1646` 标记未进入真 activate；整跑 rc=0 未被记录成激活成功。 |
| 步 1～4、名称口径 | **核对通过。** 两个 SHA 的步 1～4 区段共 753 行逐字节相同；测试 `:3576/:3600` 分别钉住连字符拒绝和下划线放行。 |
| 三处既有门调整 | **核对通过。** 测试 `:1274/:1277/:1283/:1284` 的严格计数 3 对应真实第三处写入；`:983` 保留旧目录并增加新目录；`:3569` 仅排除整行注释，行为断言与负控仍保留。 |

**r2 LOW-2 的存档整改核对通过。** [11 段版:28](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/negctl-r2fix-11seg-20260914T231734.txt:28) 的 readiness 变异被后续原分支覆盖；同文件 `:173` 的 Lance 测试其实已经失败，只是外层断言锚选错。[12 段版:183](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/negctl-r2fix-12seg-20260914T232040.txt:183) 修正了这些问题，12 段均含变异 diff、失败断言及 KILLED，恢复摘要与当前脚本一致。

本轮未写文件、未连接服务、未重跑 pytest；仅进行了源码／存档复核和无文件逻辑验证。[182 passed、9 skipped](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t2-deploy/_bmad-output/审查/evidence-g2-8/unit-deploy-r2fix-20260914T232339.txt:55) 是存档结果，不代表真态验收。


