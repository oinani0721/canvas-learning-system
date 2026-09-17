> 批次: BATCH-2026-09-11-第十四批 · 车道 T9-D（`card-t9-w4`） · 卡 CARD-RUNTIME-SHA-SURFACE round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-RUNTIME-SHA-SURFACE.md)"`
> 审查绑定: `5fa2d401..b191a085`（该轮 HEAD = `b191a085`；⚠️ 本卡最终 HEAD 是 `1f63d216`，
> 末轮绑定见 `codex-review-CARD-RUNTIME-SHA-SURFACE-r2.md`）
> 会话头自证（抄 `.stderr` 的 codex 版本行 / model 行 / reasoning 行，括注行号；`.stderr` 本身不入库）:
> `:2 OpenAI Codex v0.153.3` / `:5 model: gpt-6-astra` / `:9 reasoning effort: ultra`

---

## 结论

**PARTIAL：扩面执行代码通过静态复核；新增注释有 1 项 MEDIUM、1 项 LOW。未发现 BLOCKER / HIGH。**

审查结束时 HEAD 仍为 `b191a0853ac1d2290978a5b114f939617e82c30f`。本轮没有修改、暂存文件，也没有运行测试、探针或 hook。以下区分源码核验与历史存档，未将存档当成本轮动态复现。

## 本卡问题（按级别排序）

### 1. MEDIUM — Python 配方没有严格判断“结论行”，也没有传递退出码

**文件：** [lifespan_isolation_runtime_sha.sh:135](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:135)

**依据：**

- 第 136 行仅判断 `"RUNTIME-FILES:"` 子串。计数失败产生的 `RUNTIME-FILES: GATE-BROKEN…` 同样满足，却没有合法的 `unchanged / CHANGED` 结论行。
- 配方没有传递 `p.returncode`。若直接作为完整调用方粘贴，门返回 `CHANGED/1`，或被包裹命令失败，都可能正常走到 Python 代码结尾。
- [noexec_contract.py:20](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/noexec_contract.py:20) 复制了这个宽判据；其负例只有空输出，没有 `GATE-BROKEN`、前缀碎片和退出码传播检查。

**建议：** 精确匹配整行合法结论；缺失即退出 1，存在后仍传递 `p.returncode`。明确“发现结论行”只是额外检查，不能代表门通过。Shell 配方已经保留这一区分。

### 2. LOW — WAL 注释的定性超出了现有实测

**文件：** [lifespan_isolation_runtime_sha.sh:521](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:521)

**依据：** 新注释将未来 WAL 或其他写者直接定性为“假红面”，但 SQLite 实验没有设置、验证 WAL 模式；[收窄存档:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/narrowness-after-20260915T182319.txt:5) 只证明单独写 `llm_call_logs.db-wal` 不受监视。

**建议：** 改成“仅比较主 `.db` 文件字节；WAL/SHM 不在清单，日志模式或并发条件变化后需重新验证覆盖与误报、漏报边界”。**实际 WAL 行为未验证，不据此判当前扩面实现有缺陷。**

## 六项核对

### 1. 扩面是否只加不放宽：PASS

独立比较两版执行代码，除去注释和空行，变化**恰为新增三项及两个计数值**。

| 新监视项 | 生产路径与真实写点 |
|---|---|
| `app/data/lancedb_pending_index__*.jsonl` | [service:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/services/lancedb_index_service.py:73) 确定默认目录、stem；[namespaced_state_path:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/core/vault_state_paths.py:91) 构造双下划线路径；[service:526](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/services/lancedb_index_service.py:526) 实际追加写入。 |
| `data/neo4j_memory.json` | [DEFAULT_STORAGE_PATH:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/clients/neo4j_client.py:54) 与 [写入:480](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/clients/neo4j_client.py:480) 对应。 |
| `data/llm_call_logs.db` | [默认路径:34](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/middleware/cost_tracker.py:34)、[默认值采用:205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/middleware/cost_tracker.py:205) 与 [提交写入:285](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/middleware/cost_tracker.py:285) 对应。 |

既有三个固定项和原 glob 全部保留。门自证、计数拒绝、compgen 自检、glob 排序及首尾判定分支均未改成放行。

**建议：** 保留当前窄清单。

### 2. 计数是否同步：PASS

[门:524](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:524) 实际为 **5 fixed / 2 glob**，与第 564–565 行常量一致。

[第 569 行起](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:569) 的自检在首次快照、执行被包裹命令之前运行；不一致即对应 `GATE-BROKEN`、退出 1。[计数负控存档:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/count-selfcheck-20260915T182320.txt:1) 也记录了正常门及两种独立改错结果。

**建议：** 无需调整。

### 3. noexec 是否诚实：边界 PASS，Python 配方需修正

[门:126](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:126) 明确说明脚本不执行、内部无法补救、强制应在调用方；本卡没有新增伪装成内部防御的可执行分支。

[noexec 存档:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/noexec-after-20260915T182335.txt:1) 记录了真门及 shell 调用方在 noexec 下均为 `rc=0 / 零输出`，Python 对空输出判 1。**配方缺陷见上述 MEDIUM。**

### 4. 对照与未拦输入是否落盘：所列样本齐全

| 证据 | 核对结果 |
|---|---|
| [注入 before:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/inject-before-20260915T120909.txt:1) / [after:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/inject-after-20260915T182248.txt:1) | 三面由 `unchanged/0` 变成 `CHANGED/1`；未监视文件两版均 `unchanged/0`。 |
| [原清单正锚:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/posctl-before-20260915T120935.txt:1) | 原四种形态全部 `CHANGED/1`。 |
| [收窄证据:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/narrowness-after-20260915T182319.txt:1) | 五种旁文件均放行；真正命名空间文件被拦。 |
| [SQLite 实验:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/sqlite_sha_stability.py:31) / [输出:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/sqlite-sha-stability-20260915T121115.txt:1) | 实际读取二进制全文件、比较完整摘要；三个 SELECT 不变，真 INSERT 改变，另核对 shasum 与 hashlib 一致。 |

`gate-before.sh` 与基线 Git blob 逐字节相同；当前门与 HEAD blob 相同，摘要均匹配注入日志第 7 行。

**LOW｜证据限制：** 存档未纳入绑定提交；注入日志第 7 行只证明**门文件** SHA 前后相同。另有 [realtree-before:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-runtime-sha-surface/realtree-before-20260915T182504.txt:1)，没有配对 after，不能据此证明“整个工作树一字节未碰”。

**建议：** 将结论限定于这些临时库样本和明确文件集合。全树历史不变、生产 SQLite 完整生命周期稳定性均为**未验证**；分别需要配对摘要清单和对应生产条件的独立实验记录。

### 5. 是否出地盘、破坏探针锚：源码范围 PASS

绑定区间只有门脚本一个文件变化。指定的三个耦合文件、`backend/app/**`、`backend/tests/**` 的受控内容均与基线一致；当前 `backend` 也无受控未提交差异。

按 [花名册规则:1238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_guard_probes.py:1238) 静态重算：

- 声明、AST 实际集合、注释清单均为 **19**，无遗漏或多列；原声明区逐字未改。
- 原 glob 字符串、glob 展开代码、`snapshot()` 定义三个文本锚各匹配一次。

**LOW｜证据限制：** 前后 `152 passed` 确有存档，但 [契约测试:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_live_port_guard_contract.py:1) 检查的是 `live_port_guard`，**没有调用那 19 条 shell 探针**。

**建议：** 不将 `152 passed` 当作 shell/glob 探针执行证明；这些探针动态结果本轮**未验证**，需要绑定门摘要的执行存档。

### 6. 开头边界注释：PASS

[门:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:48) 正确说明 `5+2`、具名默认路径及配置覆盖后的盲区；[门:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_runtime_sha.sh:62) 正确区分 Neo4j 库内状态与磁盘 JSON。

残留“不在清单”文字均明确引用**旧版历史**，不是当前边界声明。除上述 WAL 文案外，没有发现把覆盖范围说成包含非默认路径。

## 移交建议——不计本卡缺陷

- **MEDIUM｜镜像不一致：** [negative_control.py:128](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/scripts/lifespan_isolation_negative_control.py:128) 仍声称与门一致，实际保持 `3+1`。移交所属车道同步新增三项及边界说明。
- **MEDIUM｜另一个已存在的清单外写路径：** [lancedb_index_service.py:226](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/services/lancedb_index_service.py:226) 会在恢复时隔离裸名 `lancedb_pending_index.jsonl`，经 [vault_state_paths.py:197](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/app/core/vault_state_paths.py:197) 改名为 `.pre-g25.bak[.N]`；这些均不受当前门监视。另卡决定是否增加精确项，保留本卡双下划线 glob。


