# CARD-G2-5 round-3 定向复核（只读审查）

你是对抗性代码审查员。工作区根目录:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance

本轮是 CARD-G2-5 的 round-3 定向复核, 不是全量审查。只读, 不修改任何文件。
允许只读沙箱内用 backend/.venv/bin/python 与 backend/.venv/bin/pytest 实跑
(pytest 写 tmp 不算改工作区; ⛔ 任何情况下不得写 backend/app/data)。

## 背景

round-2 存档 _bmad-output/审查/codex-review-CARD-G2-4-G2-5-round2.md 的「CARD-G2-5
round-2」判 4 条: HIGH-1/HIGH-2 = CONFIRMED-CLOSED; 第 3 条 HIGH-3 = STILL-OPEN
(orchestrator `_persist_sync` 失败只记日志仍返回 accepted; Lance 同型; 生产反例
state_dir 指向普通文件 → status=accepted journal_exists=False); 第 4 条 HIGH-4 =
STILL-OPEN (「约 60 秒必收敛」文案已改但 backend/tests 零回归锁)。

round-3 整改声明见验收单
_bmad-output/验收单/UAT-CARD-G2-5-索引journal命名空间-2026-08-31.md 的
「## 八、第八批 round-3 整改 (HIGH-3 / HIGH-4)」:
- orchestrator: PendingPersistError 类型化异常; enqueue 失败返回 persist_failed
  (新条目弹回/已有条目保留内存变更) + durability 三键进 freshness; 批处理点捕获;
  API POST /index/refresh-changed 任一路径失败 → 503 + 完整 body (durable=false)。
- lancedb_index_service: _persist_pending 返回 bool; intent-lost ERROR;
  _rewrite_journal 原子化 (调用方持锁, tmp=*.jsonl.tmp); recover 返回 dict 加性
  persist_failed; durable_status() 只读。
- HIGH-4 三道口径锁 (事实绑定/行为门/文案门+篡改门×3), 文案门对三段真实文本跑。
- 回归锁 (d)①-⑦ + (e)①-③ 共 10 条新增, g25 文件 16→26 passed。
- 变异 M1-M6 各杀指定门, 还原逐字节一致 (evidence-g24/g25-mutations.txt)。
- 附带修复: test_vault_scope_409.py + test_wave5_stageb*.py 的 TestClient/lifespan
  会写真 app/data journal (HIGH-2 同型既有缺陷, 新 -k 口径首次暴露) —— 加隔离 fixture。

## 读取范围 (限定)

1. backend/app/services/vault_index_orchestrator.py
2. backend/app/services/lancedb_index_service.py
3. backend/app/api/v1/endpoints/index.py
4. backend/app/core/vault_state_paths.py
5. backend/tests/unit/test_g25_journal_namespace.py
6. backend/tests/unit/test_vault_scope_409.py 与 tests/unit/test_wave5_stageb*_vault_id_injection.py (仅隔离 fixture 部分)
7. 验收单 §八 (其余章节仅交叉核对时看)
8. round-2 存档 CARD-G2-5 部分
9. evidence-g24/g25-mutations.txt, six-file-baseline-g25.txt, six-file-post-g25.txt,
   g25-head-baseline.txt, g25-post-suite.txt

## 任务

1. **HIGH-3 是否 CONFIRMED-CLOSED**: 用 round-2 的生产反例 (state_dir=普通文件)
   实测 orchestrator enqueue 与 Lance _persist_pending 的失败反馈; 审 503 契约
   (完整 body/成功路径保持模型返回/counts 初始化); 审 coalesced 路径与新条目路径
   的内存回滚语义。给证据行号。
2. **HIGH-4 是否 CONFIRMED-CLOSED**: 审 (e) 三道门是否真锁住口径 —— 尤其
   文案门 helper 的「有没有周期反熵」lookbehind 是否可绕、60s 正则否定词窗口、
   篡改门是否真能误放行形态全部红。
3. **回归检查 HIGH-1/HIGH-2 未重开**: 特别审 `_rewrite_journal` 原子化与
   O_EXCL 隔离件的交互 (tmp 名不撞 .pre-g25.bak[.N]; 失败时 journal 不动+无残片;
   空条目 unlink 语义保留——三条「journal 应被删除」断言仍绿)。
4. **专审 (d)(e) 是否死门**: 必须尝试构造「恢复吞异常/无条件 accepted 仍全绿」
   与「绕过 (e) 门」的复现 (拷到 /tmp 改后跑)。给不出复现才算有效。
5. **503 契约消费方**: 独立 grep refresh-changed 消费方, 核对「无活消费方」
   前提 (注意 endpoints/metadata.py 里可能存在的过期注释是否已改)。
6. 证据引用核对 (8.3 的六组裁判输出与 evidence 文件相符)。

## 输出格式 (严格遵守)

- `1. HIGH-3 … — CONFIRMED-CLOSED/STILL-OPEN` + 证据 file:line + 说明
- `2. HIGH-4 … — CONFIRMED-CLOSED/STILL-OPEN` + 同上
- 回归检查 HIGH-1/HIGH-2 各一行
- (d)⑦(e)③ 死门审查: 每条 `有效` / `死门` + 尝试的复现路径
- 新问题按 BLOCKER/HIGH/MEDIUM/LOW 分级
- 末行必须是: `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`
