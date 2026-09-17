# 独立复核请求（round-2）— CARD-RUNTIME-SHA-SURFACE（BATCH-2026-09-11-第十四批 / 车道 T9-D）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4`

**审查绑定：`5fa2d401..1f63d216`（`1f63d216` = 当前 HEAD，本卡最终状态）。**
- `b191a085` — 扩面（清单 +3 项、两个计数常量 3→5 / 1→2，其余为注释）
- `1f63d216` — 本轮新增：**纯注释改动**，针对 round-1 的 MEDIUM-1 与 LOW-2

**被改文件仍只有一个**：`backend/scripts/lifespan_isolation_runtime_sha.sh`

`b191a085..1f63d216` 的非注释行改动为**空**（作者自证命令：
`git --no-pager diff --no-color -U0 b191a085 1f63d216 -- <门> | grep -E '^[+-]' |
grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]#' | grep -vE '^[+-]\s*$'`，输出空；
同一过滤器对 `5fa2d401..b191a085` 会打印出三个新监视项，作为该过滤器可用性的验伪锚）。

## 二 round-1 两条意见的处置（请核对是否真的修好，以及有没有引入新问题）

### MEDIUM-1（已采纳并修改）— Python 配方判据过宽 + 不传 rc

round-1 原文指出：配方只判 `"RUNTIME-FILES:"` 子串，`RUNTIME-FILES: GATE-BROKEN …`
同样满足；且没有传播 `p.returncode`。**两条都成立**。现在门内注释的配方改为：

```
VERDICT = re.compile(r'^RUNTIME-FILES: (unchanged|CHANGED)$', re.M)
p = subprocess.run(["bash", GATE, "--", *cmd], capture_output=True, text=True)
if not VERDICT.search(p.stdout + p.stderr):
    raise SystemExit(f"门未自报结论行 ⇒ 门没跑或已损坏；rc={p.returncode} 不作数")
raise SystemExit(p.returncode)   # 有结论行只说明门跑过了，过没过仍看 rc
```

并在配方下方写明两点承重理由（整行精确匹配的必要性；「有结论行 ≠ 通过」、rc 必须传播）。

判据脚本 `_bmad-output/审查/evidence-runtime-sha-surface/noexec_contract.py` 同步收紧，
新增你点名的负例并实测（存档 `r2-judges-*.txt`）：

| 输入 | 断言判定 | 期望 |
|---|---|---|
| 空输出 | 1 | 1 |
| `RUNTIME-FILES: unchanged` | 0 | 0 |
| `RUNTIME-FILES: CHANGED` | 0 | 0 |
| `RUNTIME-FILES: GATE-BROKEN — 固定监视项有 3 个, 期望 5 个` | **1** | 1 |
| `RUNTIME-FILES: unchanged-ish`（前缀碎片） | **1** | 1 |
| `foo RUNTIME-FILES: unchanged`（非行首） | **1** | 1 |
| `=== RUNTIME-FILES before (x) ===`（快照表头） | **1** | 1 |

rc 传播实测：`CHANGED→1` / `unchanged→0` / 被包裹命令 `rc=7→7`。

### LOW-2（已采纳并修改）— WAL 措辞超出实测

改为：只比**主 `.db` 文件**字节；`-wal` / `-shm` 边车不在清单；实测限默认 journal 模式、
单连接、无并发，换日志模式或出现并发写者后覆盖面与误报/漏报边界**需要重新验证**，本卡未测；
并写明「到那时也不要靠放宽本清单来消化问题」。

### round-1 两条「证据限制」的补正（请核对这两条现在是否已闭合）

1. **你写「`realtree-before` 没有配对 after」**——当时确实只有 before：那份 after 是在你开始
   审查之后、目录级长跑结束时才落盘的。现在两份都在
   （`realtree-before-20260915T182504.txt` / `realtree-after-20260915T182504.txt`，`diff` 为空）。
   ⚠️ 作者**不**据此主张「整个工作树一字节未碰」——那三行里两行跑前跑后都是 `absent`，
   只有 `neo4j_memory.json` 是「存在且未变」的实证。验收单 §五.2 已如实登记这条限制。
2. **你写「152 passed 不能当 shell/glob 探针执行证明」——完全正确**，作者复核确认
   `test_live_port_guard_contract.py` 里对 `lifespan_isolation_guard_probes.py` 的两处提及
   都在 docstring 中，它不调用 `probe_shell_injections()`。现补一份**绑定门 sha 的执行存档**：
   `run_gate_probes.py` 只 import（不改）guard_probes，只调用与本门有关的那几支——
   `probe_shell_injections()`（19 条）+ selftest / can-report-changed / 五条 runtime-glob +
   legacy-journal，**刻意不跑 socket / 端口族探针**。
   结果 `GATE-PROBES total=27 failed=0`，含
   `shell-probe-roster-matches-declared-count` 与全部 M15 glob 探针
   （存档 `gate-probes-final-*.txt`，首行与末行各记一次门 sha，两者相同）。

## 三 本轮请回答

1. `1f63d216` 相对 `b191a085` 是否**确为纯注释**（无任何可执行行变化）？
2. 新配方是否真正修好了 MEDIUM-1 的两个点？有没有新的过宽/过窄问题（例如
   `re.M` 下的匹配面、GATE-BROKEN 被判红是否是正确语义、rc 传播是否与门的退出码表一致）？
3. 新的 WAL 措辞是否仍有超出实测的定性？
4. round-1 的其余五项核对结论（扩面只加不放宽 / 计数同步 / noexec 诚实 / 未出地盘、
   探针锚未破 / 开头边界注释）在最终 HEAD 上是否依然成立？
5. 补充的 `run_gate_probes.py` 这份执行存档，是否足以支撑「本卡的扩面没有弄坏那 19 条
   shell 探针与 M15 glob 探针族」这一主张？它自身有没有把话说得比证据宽？

## 四 输出格式

逐条给：**级别**（BLOCKER / HIGH / MEDIUM / LOW）+ **文件:行** + **依据** + **建议**。
只读环境下判不了的，请写「未验证」并说明需要什么才能判。

## 五 边界

- 只读审查：不要修改任何文件、不要暂存文件、不要跑 git hook、不要跑测试套件。
- `guard_probes.py` / `negative_control.py` / `test_live_port_guard_contract.py` /
  `backend/app/**` / 其余 `backend/tests/**` **不在本卡改面**——它们的问题请写成移交建议。
- round-1 的两条移交（negctrl 镜像 3+1 未同步；`lancedb_index_service.py` 恢复路径隔离出的
  裸名与 `.pre-g25.bak[.N]` 不在监视面）作者已收进验收单「台账待登记」，本轮不必重复展开，
  除非你发现它们其实属于本卡必修。
