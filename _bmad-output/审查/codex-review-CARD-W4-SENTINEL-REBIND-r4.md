> 批次: BATCH-2026-09-11-第十四批 · 车道 T9 · 卡 CARD-W4-SENTINEL-REBIND round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`（`codex --version` 实测）
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-W4-SENTINEL-REBIND-r4.md)"`
> 审查绑定: `6adea906`（该轮审时即 HEAD）
> 会话头自证（抄 .stderr 前几行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（.stderr:2） / `model: gpt-6-astra`（.stderr:5） / `provider: openai`（.stderr:6） / `sandbox: read-only`（.stderr:8）

---

**BLOCKER：0；HIGH：1。另有 4 项 MEDIUM、2 项 LOW。本轮 HIGH-1 尚不能关闭。**

审查对象核对为 `6adea9064c44abdd6f09a3db41ac13dcd9a94ebf`；结束时 HEAD 与源码绑定仍一致。复现仅在内存执行当前 parser 和获准的 formatter 片段，未修改文件、运行 pytest/hook 或连接数据库端口。

1. **HIGH-1 — 首条记录定位仍会吞掉真实记录的首段。**  
   位置：[w4_sentinel_identity.py:280](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:280)。

   **负控输入**：给真实 formatter 实现传入 `address="\n- tail"`；**对照输入**：`address="tail"`。线程均为 `worker`，两块均自报 1 条，四元组均为 `(1,1,0,0)`。负控正文成为：

   ```text
     - 
   - tail on thread worker (owner=x)
   ```

   首行被 `.strip()` 变成 `"-"`，不满足 `startswith("- ")`，因此被当说明行跳过。两份最终身份均为 `{"tail on thread worker"}`，**实际 CLI main 返回 `CONSISTENT / rc=0`**；`\r` 变体结果相同。

   这具体证伪了本轮“多行地址必拒判”的闭合主张：第一条记录之前的扫描仍然开放。现有 `ADDR-A\n- tail` 测试没有覆盖空首段。

2. **MEDIUM-2 — 缺块兜底在 `blocked>0` 时也可能失效。**  
   位置：[w4_sentinel_identity.py:305](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:305)，以及 `:271–276`。

   **未被拦下的输入**：两档各有一个相同的正常 C 块，另一个 C 块抬头发生相同文案漂移、地址分别为 `ADDR-A`／`ADDR-B`，四元组同为 `(2,2,0,0)`。实测不同身份被遗漏，**rc=0**。

   更小的对照是：漂移的 C 块之后保留合法 A 型 `blocked=1 unaccounted=0 reported_status=0` 抬头；两档均得到空身份集、**rc=0**。所以代价应扩大登记为：**只要还识别到任何一个块，包括零条块，其他块的消失就接不住。**

3. **MEDIUM-3 — A/B 抬头的漂移测试没有绑定真实运行期整行。**  
   位置：[test_w4_sentinel_rebind.py:510](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:510)、`:515–516`、`:522–524`、`:550–554`。

   **门未覆盖的路径**：B 的第一段字面量末尾增加一个空格，运行期变为 `次拦截 无人结账`。内存负控确认：两个源码子串锚仍为真，实际抬头正则却不匹配；手拼运行期测试继续使用旧串。A 将 `unaccounted=` 改为 `unaccounted_count=`，前缀源码锚也仍成立。

   C 的直接 formatter 往返成立；A/B 尚不足以支撑“产出方改一个字，这里就该红”。

4. **MEDIUM-4 — B 型抬头仍接受任意前缀，存在新的假红输入。**  
   位置：[w4_sentinel_identity.py:117](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:117)。

   **负控输入**：全零存档前加入普通输出 `*** cache —— 1 次拦截无人结账`；**对照输入**：原全零存档。前者被误认成缺正文的正式块，实际 **rc=2**，对照为 **rc=0**。C 已锚死 `BLOCK_REASON`，B 尚未同样收紧。

5. **MEDIUM-5 — 缺四元组测试发生覆盖回归，实际门仍正常。**  
   位置：[test_w4_sentinel_rebind.py:240](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:240)。

   **负控输入**：保持该测试原样，仅在内存删除 parser `:388–394` 的缺四元组门，测试仍得到 **rc=2**。原因是测试的 B 档仍为“裸记录＋blocked=1 汇总”，先被新增缺块门拦住，根本没有到达目标分支。

   **对照输入核对通过**：让两档都含正常 C 块、仅 A 缺四元组，实际门明确返回 `UNCHECKED／没有汇总行、advisory 未知`，rc=2。

6. **LOW-6 — advisory 措辞尚有遗漏。**  
   位置：[test_w4_sentinel_rebind.py:220](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/test_w4_sentinel_rebind.py:220)。

   **对照输入**：`(12,0,12,0)` 只能证明 12 次连接尝试被放行；断言文案仍写“真连现网 12 次”。

7. **LOW-7 — 真实 E2E 说明把旧判据误报写成了漏报。**  
   位置：[real-archive-e2e-20260915T001036.txt:18](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/real-archive-e2e-20260915T001036.txt:18)。

   **对照输入**：`SAMPLE_R4/R4B` 的旧 nodeid 集不同、新不变量相同，证明的是旧判据因归属漂移而误判不同；不能支撑该行“旧判据会漏”的表述。

对三个结构前提，结论如下：

| 前提 | 核对结果 |
|---|---|
| 三个指定产出点自报条数 | **核对通过**：[A:1545](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1545)、[B:176](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/conftest.py:176)、[C:1588](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/live_port_guard.py:1588)。是否存在第四处或绕过抬头的调用路径，限定读取面不足以排除。 |
| 块内 N 行连续 | **仅部分成立**。C 将列表拼成一个字符串；A/B 分别逐条 `print`。两条记录之间插入 `INFO` 的负控确实 rc=2，但本轮没有真实交错证据，不能把构造输入宣布为已发生的真实假红。真实 c 档只有一条记录，无法验证此条件。 |
| A 的 `unaccounted` 等于正文条数 | **部分核对**。获准片段确认抬头使用 `unaccounted`，循环使用 `ledger["unaccounted_records"]`；两者同源构造的位置 `:443–444` 不在读取面内，未独立核实。A 型真实存档也仍缺席。 |

以下项目**核对通过**：

- `final >= summary`、算术自洽、重复汇总和总账冲突：[parser:157](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:157)、`:180–220`。
- portal 归一、正常相邻块及跨块重复身份去重：[parser:146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:146)、`:302–303`。
- 非法 UTF-8 拒判：[parser:346](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:346)；裸 `0x80`／`0x81` 均 rc=2。
- 三态纯函数及 conftest 静态路由：[hygiene_snapshot_tristate.py:53](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/hygiene_snapshot_tristate.py:53)、[unit/conftest.py:324](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/unit/conftest.py:324)。未见本轮逻辑回归。

存档方面，最终 **61 → 16 failed／45 passed → 61** 及 parser 恢复 SHA **核对通过**；实际承重文件名是 [w4sr-negctl-r4b-20260914T235256.txt:232](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/_bmad-output/审查/evidence-w4-sentinel-rebind/w4sr-negctl-r4b-20260914T235256.txt:232)。三份作废标记也成立。

真实 c/d 存档用当前 CLI 重算为 **DIFFER／rc=1**，C 型身份确实被读出。不过 blocked、四元组、正文同时不同，这一对不能独立证明正文比较分支承重，也不覆盖 A/B、多记录或交错输出。你给出的 zsh 命令本机结果为 `1`，这一事实核对通过；追加第二更正的文本未在本次读取面内核验。

另登记一个**门未覆盖的路径**：[parser:298](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t9-w4/backend/tests/support/w4_sentinel_identity.py:298) 只检查紧随其后且能匹配 `_BODY_RE` 的一行。额外畸形行、或隔空行出现的额外记录仍会被忽略，因此“多一行一律拒判”的表述也超过实现能力。


