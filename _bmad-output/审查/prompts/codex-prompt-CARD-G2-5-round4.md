# CARD-G2-5 round-4 定向复核（只读审查）

你是对抗性代码审查员。工作区根目录:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance

本轮是 CARD-G2-5 的 round-4 定向复核（回应你 round-3 的判决），不是全量审查。
只读, 不修改任何文件。允许只读沙箱内用 backend/.venv/bin/python 与
backend/.venv/bin/pytest 实跑（pytest 写 tmp 不算改工作区; ⛔ 不得写 backend/app/data）。

## 你 round-3 的判决（_bmad-output/审查/codex-review-CARD-G2-5-round3.md）

- HIGH-3 STILL-OPEN: recover 锁外重放期间并发 append 被旧快照覆盖/unlink（你 /tmp 实测）;
  顶层反例/503/coalesced 本身已确认正确。
- HIGH-4 STILL-OPEN: e①空壳绕过 / e② 0.20s 重入逃过 0.04s 窗 / e③ lookbehind 与
  60s 措辞与否定词三个洞（8 passed 绕过文件）。
- (d)②③⑥ 死门（回滚字段/删 body 四字段/好目录假 True 零写）。
- MEDIUM: 批处理写失败 durable_degraded 仍 false; 证据未绑定当前 bytes。
- LOW: metadata 过期注释; §8.3 grep 数字。
- HIGH-1/HIGH-2 CONFIRMED-CLOSED（未重开）。

## round-4 整改声明（验收单 §九）

- 竞态修复: recover 重写分支改锁内合并语义——重读当前 journal, 只取**不在旧快照
  行集合**的行（旧行=残影, 由 still_pending/unlink 接管）, 与 still_pending 按
  canvas_name 取 timestamp 最新合并, 原子写; append 与 rewrite 同锁互斥且
  「重读→replace」为连续同步代码。新锁 test_lance_recover_preserves_concurrent_appends
  （替身在恢复期间真实 _persist_pending append）。变异 B1（合并短路）→ 该锁红。
- e① 行为探针: 真跑 _scan_loop 两周期（interval=20ms, reconcile 替身）≥2 次。
  getsource 检测已被我们自查证伪（死代码可骗）而弃用。变异 B4（空壳）红。
- e② 窗口 1.0s + `_pending_tasks == {}` 断言。
- e③ helper 重写: 句级疑问标记检查（？?吗呢是否有没有）; 正则扩一分钟/必然收敛;
  语境=引用标记（旧文案/原文案/原文/旧说法/曾写/原话）∧ 否定标记（不成立/是错的/
  错误/不对/不实/错的）; 篡改门 3→6。
- d② op 变更断言（upsert→delete 失败后 op 仍 delete）; d③ body 键集合恰七字段;
  d⑥ 正向对照段（真实 _rewrite_journal 好目录真写、journal 收缩为 still-pending）。
- MEDIUM: _durable_degraded 置位进 _persist_sync（覆盖全部路径）; 变异证据
  round-5 重跑绑定当前 bytes（g25-mutations-round5.txt, 11 变异全红, restore True）。
- LOW: metadata.py 注释更正; §8.3 grep 数字更正为 18。

## 读取范围 (限定)

1. backend/app/services/vault_index_orchestrator.py（enqueue/_persist_sync/recover 竞态修复段）
2. backend/app/services/lancedb_index_service.py（recover_pending 合并/_read/_merge/_rewrite_journal）
3. backend/app/api/v1/endpoints/index.py
4. backend/app/core/vault_state_paths.py
5. backend/tests/unit/test_g25_journal_namespace.py
6. 验收单 §九（其余章节仅交叉核对）
7. 你 round-3 存档; evidence-g24/g25-mutations-round5.txt 与 8.3 引用的对照文件

## 任务

1. **HIGH-3 竞态是否 CONFIRMED-CLOSED**: 复用你 round-3 的 /tmp 竞态复现手法
   （append during recovery）实测合并语义; 审「旧行集合残影」判据是否有新洞
   （例: 并发 append 的行恰好与旧快照某行逐字相同 → 被当残影跳过——给出触发条件
   与真实性判断）。变异 B1 必须仍能杀竞态锁。
2. **HIGH-4 三门是否 CONFIRMED-CLOSED**: 重新尝试你的绕过（空壳/延迟重入/
   lookbehind 类疑问句/等价措辞/肯定性修辞/删 body 字段/好目录假 True/回滚字段）,
   并尝试**新**绕过（行为探针的时序边界、句级切分的误判、引用-否定语境的伪造）。
3. 回归: HIGH-1/HIGH-2/round-2 已 CLOSED 项未重开; unlink 语义（三条 journal 删除
   断言）仍绿。
4. 证据核对: g25-mutations-round5.txt 与当前四文件 bytes 绑定（shasum）。
5. 新问题分级（BLOCKER/HIGH/MEDIUM/LOW）。

## 输出格式 (严格遵守)

- 逐条 CONFIRMED-CLOSED/STILL-OPEN + 证据 file:line + 说明
- (d)(e) 死门复查: 每条 `有效` / `死门` + 复现路径
- 新问题分级清单
- 末行必须是: `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`
