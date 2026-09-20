> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G2-11 round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G2-11-r2.md)"`
> 审查绑定: `986a22bdf8e607e4c3dd3809524932166be4d907`（⚠️ HEAD 已前进到 `da861210`：本轮之后按本轮意见改过代码，**本轮不绑最终 HEAD**）
> 会话头自证（抄 .stderr 中含 codex 版本 / model / reasoning effort 的三行，括注行号；stderr 本身不入库）:
> `(L2) OpenAI Codex v0.153.3` / `(L5) model: gpt-6-astra` / `(L9) reasoning effort: ultra`

---

绑定 SHA 已核实。未发现**未授权或隔离预检已红仍进入 up** 的路径，也未发现漏 emit 断言却以 rc=0 完成的路径。Bash 3.2 语法检查通过。

指定运行证据仍绑定 `104c3e2d`，负控文件仍为 `MATCH=24`，不能证明本轮整改已完成验证。

BLOCKER：本级无。

[HIGH] scripts/j01_e2e.sh:640 删除前复检没有绑定最初 mktemp 创建的对象，仍可能删除另一目录。  
  何以成立：负控输入令 `TMPDIR=/tmp/link` 起初指向 `/tmp/a`，创建 `j01-X` 后改指 `/tmp/b`；若后者已有 `j01-X`，复检得到的新 ROOT/TMPDIR 仍满足从属关系和黑名单，随后删除非本次创建的目录。

[HIGH] scripts/j01_e2e.sh:221 无条件排除 URL，会放过含凭据的 URL 明文。  
  何以成立：未被拦下的输入 `OLLAMA_HOST=https://alice:ExampleSecret123@api.example.test` 属于 deploy 白名单，compose 会展开；生产脱敏和本脚本键名检查均不匹配，真实值检查又跳过 URL，最终复制进证据；其他断言红也不阻止复制。

[HIGH] scripts/j01_e2e.sh:194 `env_kv_of` 漏掉无末尾换行的赋值，并保留 CRLF 的 `\r`，导致旧密钥漏检。  
  何以成立：内存负控中，参照 `SAFE=control-value\nOLD=oldsecret123456789` 的最后一行被吞，参照面仍非空，目标复用 OLD 却匹配不到；CRLF 参照与 LF 目标也实测漏检，证据真实值扫描同受影响。

[MEDIUM] scripts/j01_e2e.sh:964 敏感键仍有四字符下限，“任何长度均检查”的整改未落实。  
  何以成立：负控参照 `PASSWORD=abc`、证据 `renamed: abc`，真实值检查跳过，键名兜底不命中，明文可被复制。

[MEDIUM] scripts/j01_e2e.sh:1304 授权态回滚会把两次不可读的项目集合当作恢复成功。  
  何以成立：负控令 before/after 均为 `<unreadable>`，同时 down 成功、docker ps 成功且零残留；原样判断分支实测输出 `rollback-down rc=0`，这里漏了非授权分支已有的哨兵检查。

[MEDIUM] scripts/j01_e2e.sh:1241 `search-hit` 忽略顶层错误状态，并接受缺失状态的结果项。  
  何以成立：负控响应 `{"source_status":"error","results":[{"file_path":"节点/j01-probe-TEST.md"}]}` 经原样检测器实测得到 HIT、rc=0，因为它读取的是 item 状态，缺字段默认空串。

[MEDIUM] scripts/j01_e2e.sh:701 默认证据目录快照仍吞掉枚举和哈希失败，可把未检查到的变化判为零差异。  
  何以成立：门未覆盖的路径是已有、可写可遍历但不可列目录的证据目录；S0/S1 都只记录同一目录名，内部新增证据被 `find` 错误与 `|| :` 隐去，哈希仍相同。

[MEDIUM] scripts/j01_e2e.sh:375 所有配置值都被当作旧密钥，误拒 deploy 明确允许复制的配置。  
  何以成立：对照输入 `.env` 含 `OLLAMA_HOST=http://localhost:11434` 或 `NEO4J_HTTP_PORT=7478`，deploy 按白名单正常复制后，扫描必报旧值复用；指定 fixture 恰好跳过了全部五个白名单键。

[MEDIUM] scripts/j01_e2e.sh:649 本轮拒删修复让纯 fixture 拆除也依赖 Docker daemon。  
  何以成立：对照输入为已安装 Docker CLI、daemon 未启动；fixture 从未尝试 up，但 docker ps 失败仍导致拒删，留下 throwaway vault 并使 state-diff 红。

[MEDIUM] scripts/j01_e2e.sh:1508 `--keep-root` 会在计算 SHA256SUMS 后继续修改日志。  
  何以成立：未被拦下的合法输入 `run --mode fixture --keep-root` 完成哈希后，EXIT trap 再次调用 teardown，追加“保留 ROOT”日志，导致日志校验和失配。

[MEDIUM] scripts/j01_e2e.sh:908 网络检查对子串及逻辑键判红，误拒实际名称独立的网络。  
  何以成立：对照输入实际网络名为 `canvas-learning-network-j01`，或逻辑键为 `canvas-learning-network`、实际名为 `j01-isolated`；代码对拼接后的 `key:name` 做包含匹配，两者都会误判共享。

LOW：本级无。

其余核验：根文件白名单确实仅限 `.canvas-config.yaml` 的指定键；二进制跳过有计数，软链单独检查；DELETE 404 判红，vault 名与分桶规则相容，轮询内 curl/sleep 均受剩余时间限制。

既有契约登记，不计本卡缺陷：`index.py:85` 在客户端不可用时也返回 HTTP 200 `{}`；当前删除后检查仍无法据此区分“不可用”和“确实无表”。

BLOCKER=0 HIGH=3 MEDIUM=8 LOW=0
