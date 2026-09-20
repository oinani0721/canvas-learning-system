> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G2-11 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-11.md)"`
> 审查绑定: `104c3e2da70ce4cc1b964b605123fa76ccdc0f80`（⚠️ HEAD 已前进到 `da861210`：本轮之后按本轮意见改过代码，**本轮不绑最终 HEAD**）
> 会话头自证（抄 .stderr 中含 codex 版本 / model / reasoning effort 的三行，括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`

---

审查绑定 `104c3e2da70ce4cc1b964b605123fa76ccdc0f80`；文件 SHA 与所给证据一致。仅做只读检查、语法检查和内存负控，未运行部署、容器或数据库操作。

BLOCKER：本级无。未发现受支持的普通输入能在未授权或隔离预检红时执行 `up`：第一趟固定 `env -u`，第二趟受隔离结果和双授权约束；`set -e` 提前退出不会跳入授权分支。

[HIGH] [scripts/j01_e2e.sh:552](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:552) Docker 查询失败被当成零容器，可能删除仍运行实例的挂载源。  
何以成立：负控输入为启动后 `down` 失败、`docker ps` 非零且无输出；`grep -c … || :` 仍得到 `alive=0`，随后执行递归删除。

[HIGH] [scripts/j01_e2e.sh:540](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:540) 拆除只检查旧的 `THROWAWAY_OK`，没有重新确认删除对象的物理路径。  
何以成立：门未覆盖的路径是 TMPDIR 的**中间段软链**在初检后改指受保护目录，且那里存在同名 `j01-*` 子目录；第 558 行仍按原逻辑路径删除，初检的 realpath 结果不再约束实际对象。

[HIGH] [scripts/j01_e2e.sh:816](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:816) 不足 12 字符的真实密钥被跳过，可使明文证据获准复制。  
何以成立：负控输入为参照 `NEO4J_PASSWORD=s3cr3t123`，证据包含 `NEO4J_AUTH: <redacted>` 和下一行 `  neo4j/s3cr3t123`；真实值检查跳过短值，键名检查过滤首行，第 838 行因此复制且断言报绿。

[HIGH] [scripts/j01_e2e.sh:930](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:930) stats 的 HTTP 错误响应会被当成“本 vault 已无表”。  
何以成立：负控输入为删除前 stats 正常、DELETE 返回 200、删除后 stats 返回 503 和 `{"detail":"Service Unavailable"}`；curl 不检查 HTTP 状态，解析器输出 `null`，`table-diff` 因而假绿。

[MEDIUM] [scripts/j01_e2e.sh:265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:265) 原始 env 右值未经解析，语义相同的引号变体能绕过旧密钥检查。  
何以成立：未被拦下的输入为参照 `OLD_SECRET="0123456789abcdef"`、目标 `INTERNAL_API_KEY=0123456789abcdef`；保留引号使 SHA 不同，第 822 行的证据真实值检查也会寻找带引号字符串而漏掉明文。

[MEDIUM] [scripts/j01_e2e.sh:316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:316) 部分目录枚举失败被吞掉，输入计数非零不能证明扫描完整。  
何以成立：负控输入为一个可读的新值 `.env`，另有不可遍历子目录藏着旧密钥或绝对路径；第 316、363、436 行均不接住 `find` 的失败，未扫描子树不会计入 `unreadable`，两条断言仍可绿。

[MEDIUM] [scripts/j01_e2e.sh:316](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:316) 相对软链形式的 env 完全绕过旧值扫描。  
何以成立：未被拦下的输入为普通 `.env` 存新值、`payload.txt` 存旧密钥、`.env.extra -> payload.txt`；`-type f` 排除该 env 软链，而绝对路径扫描只检查其 target 是否含 `/Users/`。

[MEDIUM] [scripts/j01_e2e.sh:914](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:914) Docker 查询失败产生双行哨兵，绕过不可读状态检查。  
何以成立：负控输入为前后两次 `docker compose ls` 都失败且无输出；Python 和管道失败分支各输出一次 `<unreadable>`，第 965 行的单行匹配失效，配合 `docker ps` 失败归零，可记录 `rollback-down rc=0`。

[MEDIUM] [scripts/j01_e2e.sh:1002](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:1002) 第二趟部署的失败退出码没有进入最终失败判定。  
何以成立：负控输入为第二趟前五步成功、第六步失败返回 76；健康和索引成功记录已经存在，首趟证据也仍存在，其后探针与拆除成功时，`deploy-rc` 保留首趟的 0，13 条完整性检查不会发现这次漏判。

[MEDIUM] [scripts/j01_e2e.sh:594](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:594) `state-diff` 只统计默认证据目录数量，漏掉既有目录内的内容变化。  
何以成立：负控输入为已存在的 `evidence-deploy-j01tw*` 目录在运行中被误用、文件被新增或覆盖；目录数量不变，且 `_bmad-output` 被 porcelain 排除，S0/S1 仍可相同；第 587 行也同样无法发现已处于修改状态的文件再次改变内容。

[MEDIUM] [scripts/j01_e2e.sh:638](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:638) `isolation-check` 会把 Compose 短格式字段过滤为空后判绿。  
何以成立：负控输入采用安全容器名和网络名、`backend: {}`、`ports: ['7478:7474']`、`volumes: ['/Users/x:/data']`；原始列表计数非零，但字典投影为空，两项检查零次执行仍绿；**当前 live 生产者输出长格式，因此这不证明 live 的授权门已被绕过。**

[MEDIUM] [scripts/j01_e2e.sh:1037](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p3-deploy/scripts/j01_e2e.sh:1037) `search-hit` 轮询未遵守配置的时间上限。  
何以成立：未被拦下的输入 `CLS_DEPLOY_LANCE_READY_TIMEOUT=1` 遇到迟滞响应，固定 30 秒 curl 再加固定 3 秒 sleep，可让轮询耗时约 33 秒。

LOW：本级无。

其余核对：未见 `no-old-secret` 直接打印值；空参照会判红，正常原始值能够匹配，并非恒绿。白名单确实只匹配根目录 `.canvas-config.yaml` 的两个键名行；二进制跳过有计数。两份指定 `.env` 的内容变化有 SHA 覆盖。DELETE 404 明确判红，vault 名与首个 `_` 分桶相容。未发现主要计数器因管道子 shell 丢失、中文或空格路径词分割，以及正常 `run` 漏 emit 却退出 0 的路径。

既有问题登记、不要求本卡修改：`deploy-vault.sh:176` 的脱敏不覆盖块标量后续行；`index.py:85` 在客户端不可用时返回 `{}`。`refresh-changed` 的实现不在允许读取片段内，未对其内部同步／异步语义作确定结论。

BLOCKER=0 HIGH=4 MEDIUM=8 LOW=0


