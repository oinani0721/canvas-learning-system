> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G2-11 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-11-r3.md)"`
> 审查绑定: `d24485cd1222444342fd15718768771b1b11baae`（⚠️ HEAD 已前进到 `da861210`：本轮之后按本轮意见改过代码，**本轮不绑最终 HEAD**）
> 会话头自证（抄 .stderr 中含 codex 版本 / model / reasoning effort 的三行，括注行号；stderr 本身不入库）:
> `(L4) OpenAI Codex v0.153.3` / `(L7) model: gpt-6-astra` / `(L11) reasoning effort: ultra`

---

绑定 SHA 已核对为 `d24485cd1222444342fd15718768771b1b11baae`。全程只读，未运行部署、容器或数据库连接。

限定读取面内，**未发现未授权或隔离预检红时仍进入 up 的控制流**；缺失、空白、解析失败的配置均判红。未发现漏 emit 后仍正常返回 `rc=0` 的完整性绕过。

BLOCKER：本级无。

[HIGH] scripts/j01_e2e.sh:711 inode 复检与删除仍未绑定同一个对象，TOCTOU 殮留。
  何以成立：负控在第 642 行身份检查通过后、等待第 700 行 `docker ps` 返回期间，改指 `$TMPDIR` 的中间软链；最终 `rm -rf "$ROOT"` 会删除新目标下同名目录，此时不再检查 inode 或保护路径。

[HIGH] scripts/j01_e2e.sh:1467 秒级 vault 名会让并发运行共用项目、容器和数据库分桶。
  何以成立：未被拦下的输入是同一秒启动两个已授权 live，分别使用不同端口、证据目录；ROOT 不同但 `VAULT_NAME` 相同，任一运行的 DELETE/down 都可能清理另一运行的资源。

[HIGH] scripts/j01_e2e.sh:1067 `evidence-redacted` 未覆盖最终主日志，存在直接进入证据的旁路。
  何以成立：负控让被测 deploy 的 stdout 输出参照密钥；第 1488 行先将其写入 `$LOG`，复查只枚举 `$DEPLOY_EV`，仍可报告脱敏通过；新实例 `$ENV_FILE` 的密钥也未加入真实值复查集合。

[HIGH] scripts/j01_e2e.sh:235 收窄后的候选筛选仍会排除真实凭据。
  何以成立：负控参照 `DATABASE_URL=https://example.invalid/?token=<真实令牌>`，证据原样包含该 URL；它没有 userinfo，因普通 URL 分支被跳过，键名兜底也不命中；同型输入 `password=abc` 配证据 `note: abc` 亦绕过大小写敏感的筛选。

[MEDIUM] scripts/j01_e2e.sh:205 env 值未按合法注释、空白和 export 写法归一，仍可漏掉旧密钥复用。
  何以成立：负控参照 `PASSWORD="audit_only_value" # comment`、目标 `INTERNAL_API_KEY=audit_only_value`，原解析器只输出带引号和注释的值，sha 不相等；内存复核确认 CRLF、末行无换行已修，但这类等价写法仍漏检。

[MEDIUM] scripts/j01_e2e.sh:204 补换行操作吞掉参照文件读取失败，部分参照仍能冒充完整参照。
  何以成立：负控提供两个参照 env，其中一个不可读、另一个含有效值；`cat` 失败被后续 `printf` 覆盖为成功，文件数和值数仍非零，旧密钥仅在不可读文件中时可判绿。

[MEDIUM] scripts/j01_e2e.sh:408 非密钥的固定字段仍被当作旧密钥，五键排除没有消除误红。
  何以成立：对照输入为参照 `.env` 含 `API_PORT=8187`、本次合法使用空闲端口 8187 且密钥全新；API_PORT 不在排除集合，仍因同值 sha 命中而令 `no-old-secret` 判红。

[MEDIUM] scripts/j01_e2e.sh:640 首次 inode 获取失败会关闭对象身份保护。
  何以成立：负控让第 1465 行首次 stat 临时失败，`ROOT_ID` 得到空串；路径恢复后其他检查可以通过，但此处因空值跳过全部身份比对，没有 fail-closed。

[MEDIUM] scripts/j01_e2e.sh:754 快照把读取错误纳入哈希，却仍允许“两次同错”判零差异。
  何以成立：负控令某缺省证据目录在 S0/S1 均无法枚举，中间内容发生变化；两侧均产生相同 `LSRC 1`，哈希相等，`state-diff` 仍绿；模板树第 743 行吞错也有同型问题。

[MEDIUM] scripts/j01_e2e.sh:772 `.env` 家族实际只快照两个固定文件，漏掉实例 env。
  何以成立：负控让部署误在 harness 根生成或改写 `.env.j01tw…`；该路径已核实被 Git 忽略，porcelain 不记录，此循环也不扫描，S0/S1 可以相同。

[MEDIUM] scripts/j01_e2e.sh:1304 `search-hit` 没有检查 HTTP 状态。
  何以成立：负控响应为 HTTP 503，但正文含匹配路径和正常 `source_status`；curl 未使用 `--fail`，下游只解析正文，仍可 HIT。

[MEDIUM] scripts/j01_e2e.sh:1316 响应状态检查仍接受空状态，并可能遮蔽顶层错误。
  何以成立：内存执行原解析器，item 的 `source_status=null`、空串，以及顶层同时含 `source_status="ok_nonempty"`、`status="error"`，均返回 HIT/0。

[MEDIUM] scripts/j01_e2e.sh:1192 HTTP 200 的 stats 不可用路径仍被解释为“无表”。
  何以成立：允许读取的 `index.py:85-87` 在 client 不可用时返回 `{}`；负控在 DELETE=200 后进入该路径，解析器回 `null`，`table-diff` 仍绿。此处登记既有接口的歧义，不要求本卡修改接口。

[MEDIUM] scripts/j01_e2e.sh:1350 `table-diff` 没有采集所声称的“首索引前无键”。
  何以成立：未被拦下的输入是运行前已有同名 vault 表；唯一 before 查询发生在部署、索引和搜索之后，随后 DELETE=200、after=null 即通过，无法证明本轮新建。

[MEDIUM] scripts/j01_e2e.sh:1285 up 后普通命令失败会跳过 down，留下运行中的容器。
  何以成立：负控令创建或写入探针因权限、磁盘满等失败；`set -e` 直接退出，后面的 down 不执行，EXIT trap 只因容器尚在而拒删 ROOT，不尝试停止容器。

[MEDIUM] scripts/j01_e2e.sh:468 软链读取失败仍被当作没有绝对路径。
  何以成立：负控在枚举完成后令软链所在目录不可访问；`readlink` 失败被转为空串，不增加 `n_unread`，其余可读文件满足非空门后，`no-abs-path` 可以判绿。

[LOW] scripts/j01_e2e.sh:817 短格式解析混淆容器端口与发布端口，也混淆匿名卷与 bind。
  何以成立：对照输入 `ports: ["7478"]` 只指定容器端口，却被判为宿主端口冲突；`volumes: ["/data"]` 是匿名卷，却被第 827 行判成宿主 bind。真实 deploy 的规范化长格式不受此误红影响。

其余已核：根目录 `.canvas-config.yaml` 才进入文件名白名单；二进制跳过有计数；DELETE 404 明确判红；vault 名不含 `_`，与给定分桶口径相容。未发现相关计数器因管道子 shell 丢失。

证据确有 38 MATCH，两份运行日志绑定当前 SHA；但负控汇总和隔离验伪锚本身没有 SHA 标记。SHA256SUMS 及 `refresh-changed` 实现不在允许读取面，本轮未独立验证其自洽性与接口语义。

BLOCKER=0 HIGH=4 MEDIUM=12 LOW=1


