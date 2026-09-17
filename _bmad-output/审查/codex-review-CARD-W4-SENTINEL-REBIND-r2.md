> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-SENTINEL-REBIND round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-SENTINEL-REBIND-r2.md)"`
> 审查绑定: `5c696c92`（该轮审时即 HEAD）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `provider: openai`（.stderr:6） / `sandbox: read-only`（.stderr:8）

---

**本轮 BLOCKER：0；HIGH：2。审查 SHA：`5c696c924c4eb4636bff553e2ea16d2bf8dffea5`。目前不能判定复核通过。**

round-1 原例的整改结果成立，但 HIGH-1、HIGH-3 各有一条同型假绿仍未封住。复现直接调用该 SHA 的真实 `main()`，输入置于内存；未修改文件、运行 pytest/hook 或连接数据库。

1. **HIGH — 缺失四元组仍被当作可比较，HIGH-1 尚未完整封住。**

   位置：[w4_sentinel_identity.py:290](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:290)、`:296`。

   **未被拦下的输入：** A、B 都有相同正文及合法 `final blocked=1`；只有 B 带汇总四元组 `(13,1,12,0)`。实测 A 为 `quad=None`，但 CLI **rc=0 / CONSISTENT**。

   `quad_vals` 排除了 `None`，因此只有 B 的四元组参与比较，A 的 advisory 实际未知。建议 CLI 遇到缺四元组返回 `2`；这不妨碍 `blocked_count()` 单独支持 final-only。

2. **HIGH — 合法线程名前导换行仍让正文静默消失，HIGH-3 尚未完整封住。**

   位置：[w4_sentinel_identity.py:105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:105)、`:217-221`。

   **未被拦下的输入：** 保留 round-1 的 IPv6 `7691`／IPv4 `7687` 两个不同地址和相同 `blocked=1` 汇总，把线程名设为 `"\nworker"`。实测两份 **`bodies=[]`，rc=0 / CONSISTENT**。

   已确认 `threading.Thread(name="\nworker").name` 原样保留该名称，未启动线程。输出被换行切开后，首行经 `strip()` 止于 `on thread`；候选正则要求后面还有空格，于是主体和候选都不匹配。普通线程名对照则返回 `1`。本卡至少应对此拒判，无须支持任意多行身份解析。

3. **MEDIUM — 新候选规则会误伤合法存档中的普通输出。**

   位置：[w4_sentinel_identity.py:105](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:105)、`:221-228`。

   **对照／负控输入：** 正常汇总中加入 captured stdout 的普通日志 `- waiting on thread worker`，实测变成 **rc=2 / CONFLICT**。规则没有限定哨兵正文区段，把普通日志认成畸形记录。

   合法线程名 `"worker\ncontinued"` 也会被拒判。这属于新增假红；指定目录存档没有证明这些形态已实际出现。

4. **MEDIUM — `CONSISTENT-ZERO` 实际只检查 blocked，不是全零。**

   位置：[w4_sentinel_identity.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:307)、`:315-317`。

   **负控输入：** 两份均为 `(12,0,12,0)`，实测 **rc=0 / CONSISTENT-ZERO**，并打印“全零”。

   一致性比较返回 `0` 合理，但“全零”错误。应按完整四元组判断全零，或明确称为“零阻断”。这属于本轮 HIGH-2 输出整改的直接缺口，建议本卡修正。

5. **MEDIUM — round-1 MEDIUM-4 仍在，可登记移交，但不能声称任意身份跨跑恒定。**

   位置：[w4_sentinel_identity.py:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:101)、`:129-137`。

   **负控／对照输入：** `Thread-1→Thread-2`、裸 repr 中 `0x1234→0x5678`，分别仍返回 `1`。你特别要求的分隔符边界，独立结果如下：

   | 输入形态 | 实测结果 |
   |---|---|
   | owner 含 `a on thread b (owner=c)` | 正确排除 owner，**核对通过** |
   | 地址仅含 `ADDR (owner=decoy)` | 地址完整保留，**核对通过** |
   | 多个 ` (owner=` 均位于真实 owner 内 | 正确排除，**核对通过** |
   | 线程名为 `worker (owner=A)`／`worker (owner=B)` | 都截成 `worker`，同汇总下 **rc=0** |
   | 地址为 `ADDR on thread Decoy (owner=A)`／`…B)` | 都截成 `ADDR on thread Decoy`，**rc=0** |

   因此，“多个分隔符”是否安全取决于其所在字段。最后两项是解析成功但切错边界，候选异常分支无法兜住；可合并进既有歧义债务登记。

6. **MEDIUM — round-1 MEDIUM-5 仍在，按已声明的来源限制移交合理。**

   位置：[w4_sentinel_identity.py:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:88)、`:190-203`。

   **负控／未被拦下的输入：**

   - 总账截到 `reported_status=garbage；`，仍能取出 blocked；同档比较 **rc=0**。
   - 对照保留裸 summary/body，负控增加带 `stderr_tail = ` 前缀的更大 final，仍 **rc=0**。
   - A 跑的 `summary=2` 拼 B 跑的 `final=3`，仍返回 **3**。

   这三条继续按 MEDIUM 移交恰当。尤其不能为拦混档而改成 `final == summary`，那会破坏合法增长；来源一致需要额外运行绑定。

7. **LOW — advisory 的文字仍把“尝试获放行”说成“实际连接成功”。**

   位置：[w4_sentinel_identity.py:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:39)、`:255`。

   **门未覆盖的路径：** advisory 尝试获放行后仍可能连接失败。指定锚 `live_port_guard.py:230` 支持“只记不拦”，不能证明成功连上现网。

**round-1 原例及回归项的核对结果：**

| 项目 | 本轮独立结果 |
|---|---|
| HIGH-1：advisory `0` 对 `12` | **核对通过：rc=1**；接线在 `identity.py:261、296-304` |
| HIGH-2：两个全零档，含额外 `installed=False` 的变体 | **核对通过：rc=0，明确打印能力边界**；`:307-319` |
| HIGH-3：原含空格线程名、不同地址 | **核对通过：身份均非空，rc=1**；`:101、218-220` |
| 含空格线程名，只有 owner 漂移 | **核对通过：rc=0** |
| R4/R4B；两个 portal 地址 | **核对通过：均 rc=0**；portal 与 MainThread 对照为 `rc=1` |
| `final >= summary` | **核对通过**：`2→3` 返回 `3`，`2→2` 返回 `2`，`5→2` 抛冲突；`:190-203` |
| 四元组算术门、重复汇总／总账 | **核对通过**：算术不自洽和重复记录均抛冲突；`:150-159、170-175` |
| sha 三态及 conftest 实际分流 | **核对通过**：五种组合均正确；[三态函数:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/hygiene_snapshot_tristate.py:53)、[conftest.py:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/conftest.py:324) |
| LOW-7 指定 docstring | **核对通过**：任一侧 None 明确为 unchecked；[conftest.py:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/conftest.py:83) |

对 **HIGH-2 的权衡**，我倾向保留 **`rc=0 + 明示仅比较一致`**。本工具可以比较合法的零连接运行；零值本身不应导致比较失败。目录级判据可以据此报告“提取到的计数和身份一致”，安装状态、运行来源、worker 覆盖则仍需独立证据。这个限制对非零档也成立。**原 HIGH-2 可按能力声明收窄关闭，但上面第 4 条标签错误应修正。**

**MEDIUM-6 版本绑定核对通过。** 独立计算的 Git blob 与工作文件 SHA256 一致，分别为 `c52a8a5b…ece81f`、`e21500b4…09ffab`；与[负控存档:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/w4sr-negctl-r2-20260914T230950.txt:5)、`:14、17、20` 及[目录存档:3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/unit-close-r2-20260914T231032.txt:3) 对应。四文件范围及三份守卫未改也已核对。

目录存档可独立数出 **64 条唯一红项＝35 FAILED＋29 ERROR，本卡测试零红；34 个通过点成立**。但[目录 diff 存档:9](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/unit-close-diff-r2-20260914T231646.txt:9) 只有比较结果，授权面内没有原始基线集合，故不能声称本轮独立重算了“与基线逐项完全相同”。负控和目录跑属于存档核验，未在本轮执行。


