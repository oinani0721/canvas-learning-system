# CARD-G2-5 round-5 定向复核（只读审查；最后一轮）

你是对抗性代码审查员。工作区根目录:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance

⛔ 本轮纪律（同 round-4b）: 以文字推理描述潜在绕过, 不构造可执行攻击脚本;
读取范围严格限定; 允许跑
`backend/.venv/bin/pytest backend/tests/unit/test_g25_journal_namespace.py -q`
这一条验证命令（写 tmp 不算改工作区; ⛔ 不得写 backend/app/data）。

## 上下文（你 round-4b 的判决）

HIGH-3 竞态主路径 CONFIRMED-CLOSED（残余降 MEDIUM）; e①②/d②③⑥ 全部
CONFIRMED-CLOSED; 唯一残留 **HIGH = e③ helper 未断言「没有周期反熵」存在**
（缺它时 finditer 零次循环放行; 旧篡改门测的是缺第一短语的反方向）。
MEDIUM×6 / LOW×1（multiplicity / 锁内重读 OSError / fresh 不计 pending /
d③ 无混合场景 / d⑥ 逐键文案不符 / docstring 计数漂移; e① 扫描根源码级绑定）。

## round-5 整改声明（验收单 §9.7）

- **HIGH 修复**: helper 加独立存在性断言 `assert "没有周期反熵" in text`（在
  句级循环之前）; 新增反方向篡改门——样本「orchestrator 侧只覆盖当前部署的这个
  vault（旧文案曾经这么写），约 60 秒内必收敛，不成立。」刻意满足引用-否定语境,
  唯一能拒它的是存在性断言（本地验证 REJECT 原因恰为「缺事实断言」）。
- MEDIUM×3 修复: 锁内重读 OSError → fail-closed（不写不删 + persist_failed=1）;
  `pending = len(still_pending) + len(fresh)`; d⑥ kept 断言完整 dict 相等。
- MEDIUM d③ 混合场景: 新增 1 excluded（绝对路径, 确定性）+ 1 persist_failed
  → 仍 503 + durable=False + 逐路径状态断言。
- MEDIUM×2 登记: 相同行 multiplicity（真实写入恒带时间戳, 字节重复=毫秒内同
  canvas 同 error, 幂等无害——§9.8）; e① 扫描根源码级（行为化成本远超风险）。
- LOW: docstring 篡改门计数 ×4→×10 更正。
- 终态: g25 → 27 passed; format/lint 过; commit e86982b4。

## 读取范围 (严格限定)

1. backend/tests/unit/test_g25_journal_namespace.py（helper + 篡改门段; d③ 混合
   场景段; d⑥ 逐键段）
2. backend/app/services/lancedb_index_service.py 的 recover_pending（锁内合并与
   fail-closed 段）
3. 验收单 §9.7-§9.8

## 任务

1. **HIGH-4 e③ 是否 CONFIRMED-CLOSED**: 核对存在性断言的位置与反方向篡改门的
   专测性（该样本是否确实只能被存在性断言拒绝）; 文字推理是否仍存在绕过形态;
   跑那一条 pytest 命令确认 27 passed。
2. **HIGH-3 残余处置核对**: fail-closed 修复是否正确（不引入新死锁/语义回退——
   注意该 except 现在出现在 `with self._file_lock:` 内部, 确认无自死锁）。
3. **MEDIUM×2 登记处置是否接受**（multiplicity / e① 源码级）——给出 接受/不接受。
4. 三个被修 MEDIUM（fresh 计数/d③ 混合/d⑥ 逐键）与 LOW 是否落实。
5. 新问题分级（BLOCKER/HIGH/MEDIUM/LOW）。

## 输出格式 (严格遵守)

- 逐条 CONFIRMED-CLOSED/STILL-OPEN + 证据 file:line
- MEDIUM 登记处置: 接受/不接受 + 理由
- 新问题分级清单
- 末行必须是: `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`
