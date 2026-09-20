> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G2-11 round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-11-r4.md)"`
> 审查绑定: `36105cb1aefd2e585582c6492ec86b5cc5db962c`（⚠️ HEAD 已前进到 `da861210`：本轮之后按本轮意见改过代码，**本轮不绑最终 HEAD**）
> 会话头自证（抄 .stderr 中含 codex 版本 / model / reasoning effort 的三行，括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

绑定已核对：`36105cb1aefd2e585582c6492ec86b5cc5db962c`，工作区脚本与该 SHA 一致。全程只读，未起容器、未连数据库。

未发现**缺少双授权或隔离预检已红时仍执行 up** 的控制流；配置缺失、为空、解析失败均拒绝。未发现正常 `run` 漏发断言却返回 0 的路径。指定两份运行日志均绑定当前 SHA、各有 13 条不同断言；负控文件确为 `MATCH=43`。

BLOCKER：本级无。

[HIGH] scripts/j01_e2e.sh:767 登记①的删除竞态仍存在，而且可以在本文件内修复。  
何以成立：负控在身份复检后改指 ROOT 的中间段软链，路径式递归删除仍可能作用于另一个目录。**可修：**同文件内嵌 Python，打开目录 fd 后以 `fstat` 核对 ROOT_ID，递归删除使用 fd 相对操作；本机 Python 已具备相关能力，“bash 没有原语”不足以支持不修。

[HIGH] scripts/j01_e2e.sh:1147 新实例密钥只检查主日志，复制部署证据时仍然漏检。  
何以成立：负控让新密钥仅出现在部署证据的 `diagnostic: <新密钥>` 行；复制分支只比旧参照值，键名兜底也不命中，最终复制明文并报告 `evidence-redacted rc=0`。**可修：**所有待入库文件共用包含旧参照值和新实例密钥的扫描函数。

[HIGH] scripts/j01_e2e.sh:224 新增注释归一会截断引号内部的 ` #`，同时绕过旧值比较和证据明文检测。  
何以成立：只读内存实测，参照 `PASSWORD="same # secret" # comment` 只产生原样值及 `"same`；目标 `INTERNAL_API_KEY="same # secret"` 产生的两个值与其均不相同。证据中的 `diagnostic: same # secret` 也漏检。**可修：**仅在引号外识别注释。

[MEDIUM] scripts/j01_e2e.sh:791 紧急清理依赖日志写入成功，日志故障可再次中止 EXIT trap。  
何以成立：负控为 up 后日志磁盘写满或失去写权限；进入 trap 后同一个 `log` 再次失败，`set -e` 使后面的 `down` 无法执行。**可修：**清理日志允许失败，清理动作独立捕获退出码。

[MEDIUM] scripts/j01_e2e.sh:745 Docker 客户端不可用时跳过容器检查，仍可能删除运行中容器的挂载源。  
何以成立：负控为实际 up 后客户端被移除或失去执行权限；容器仍运行，但 `command -v docker` 失败令整个检查分支跳过。**可修：**`UP_ATTEMPTED=1` 时，客户端不可用也必须拒删。

[MEDIUM] scripts/j01_e2e.sh:1661 两条密钥／绝对路径断言只覆盖第一趟部署，没有检查授权态最终产物。  
何以成立：负控仅让第二趟完整 `--apply --activate` 引入旧密钥或绝对路径；第一趟扫描仍绿，第二趟之后没有重扫。**可修：**在最后一次部署后扫描，或累计两次结果、统一 emit。

[MEDIUM] scripts/j01_e2e.sh:422 禁带键检查没有采用新增的 env 归一，合法语法仍能绕过。  
何以成立：对照 `OPENAI_API_KEY=newvalue` 被拦，负控 `export OPENAI_API_KEY=newvalue`、`OPENAI_API_KEY = newvalue` 不被拦；新值不在参照集合时，复用检查也不会补救。**可修：**对归一后的键名执行禁带检查。

[MEDIUM] scripts/j01_e2e.sh:1190 主日志计数掩盖部署证据空面及枚举失败。  
何以成立：负控提供存在但为空的 DEPLOY_EV 和正常 LOG；主日志已令 `inspected=1`，零份部署证据仍可判绿，`find` 失败也未捕获。**可修：**分别检查部署证据枚举退出码、部署文件数及读取成功状态。

[MEDIUM] scripts/j01_e2e.sh:825 登记②“两次同错”可以通过独立的快照有效性判据修复。  
何以成立：负控让 S0、S1 的目录枚举均失败，相同错误标记得到相同哈希，最后仍可宣称零差异。**可修：**任一快照采集失败即禁止 `state-diff` 判绿；不能仅比较错误标记是否相同。

[MEDIUM] scripts/j01_e2e.sh:813 对 porcelain 文本取哈希，不能发现已经脏的文件再次改变内容。  
何以成立：负控让同一个已修改的普通 tracked 文件在部署期间再次变化；前后仍是同一条 ` M <path>`，且不属于另行哈希的 vault／env 面，快照保持相同。**可修：**对所声明保护范围增加内容摘要，或先明确拒绝不支持的脏状态。

[MEDIUM] scripts/j01_e2e.sh:1318 登记③的接口歧义属实，但本脚本仍可避免把它判成删除成功。  
何以成立：负控为删除前有键、DELETE 200、随后 client 不可用而返回 HTTP 200 `{}`；当前转换成 `null`，`table-diff` 判绿。**可修：**将空对象标为不可确认并拒绝成功结论；接口修复继续登记给 P1。

[MEDIUM] scripts/j01_e2e.sh:1579 vault 名已随机化，默认运行证据目录仍会同秒冲突。  
何以成立：未被拦下的输入是同秒启动两个相同 mode 的运行；两者共享 LOG、快照及 SHA256SUMS，并相互截断、覆盖。进程内的断言计数无法识别混写。**可修：**证据目录也使用每次运行唯一的标识。

[MEDIUM] scripts/j01_e2e.sh:902 短格式相对宿主 bind 会被隔离验伪锚错误放行。  
何以成立：其余四面隔离，仅输入 `volumes: ["./data:/data"]`，解析后输入计数非零，但 `/*` 检查不命中；绝对路径对照则红。**可修：**识别相对 bind，或拒绝未归一的配置。此项影响 `isolation-check`，不声称当前真实 Compose 渲染路径直接绕过 up 门。

[LOW] scripts/j01_e2e.sh:1479 注释仍宣称验证“首索引前无键”，与已接受的收窄范围不符。  
何以成立：实际首次 stats 采集发生在索引、检索之后。登记④的三态收窄可以接受；**可修：**注释改为“删除前有键 → DELETE 200 → 删除后无键”。

登记⑤中，容器端口／匿名卷两种偏红误判的说明成立，但不能覆盖上述相对 bind 的偏绿情况。

其余核对：根文件白名单确实只匹配 `.canvas-config.yaml`；软链、二进制跳过均有计数；DELETE 404 明确判红；随机 vault 名与首个 `_` 分桶相容。第二趟部署前读取鉴权 key 另有时序疑点，但限定读取面不足以确认重复部署是否必然换 key，本次未将其计为确定发现。未重跑部署，也未越界读取 SHA256SUMS 文件验证整包校验和。

BLOCKER=0 HIGH=3 MEDIUM=10 LOW=1


