# CARD-G2-5 round-4b 定向复核（只读审查；round-4 首发被内容过滤器拦截后的缩小范围重发）

你是对抗性代码审查员。工作区根目录:
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance

⛔ 本轮纪律（与上轮不同）:
- **以文字推理描述潜在绕过, 不构造可执行攻击脚本** —— 上轮的 /tmp 对抗样本
  触发了内容过滤器; 你 round-4 抢救出的三个绕过样本已被修复并固化为篡改门,
  直接读测试文件核对即可, 无需自行重演。
- 读取范围严格限定, 不要读其它文件。
- 允许跑 `backend/.venv/bin/pytest backend/tests/unit/test_g25_journal_namespace.py -q`
  这一条验证命令（写 tmp 不算改工作区; ⛔ 不得写 backend/app/data）。

## 上下文（你 round-3/round-4 的结论）

round-3 判 HIGH-3 STILL-OPEN（recover 竞态）+ HIGH-4 三门绕过 + d②③⑥ 死门;
round-4 首发你实测: e③ 旧 6 篡改样本全 REJECT, 但新构造 3 绕过全 ACCEPT
（反问句「难道…没有」/「六十秒保证达到一致」/「新结论：约60秒内必然收敛」语境伪造）,
随后审查被过滤器拦截, 无最终判决。

## round-4b 整改声明（验收单 §9.6）

- 反问句: 疑问标记表 +「难道/岂/怎能/怎么会」（句级检查）;
- 中文数字与同义断言: claim 正则族三支——`(60|六十)秒…必(然)?收敛` /
  `一分钟…必(然)?收敛` / `(六十|60)秒…(保证|确保|必然|一定)?(达到一致|保持一致|一致)`;
- 语境伪造: 新增**活断言引导词**检查——命中断言 ±30 字符内含「新结论/结论是/
  因此/所以/现在可以确认」一律拒绝（引用语境的合法形态不含这些词）;
- 三个抢救样本逐字固化为篡改门（6→9 条）, 本地复现全部 REJECT;
  `pytest backend/tests/unit/test_g25_journal_namespace.py -q` → 27 passed。
- 竞态修复（锁内合并语义 + test_lance_recover_preserves_concurrent_appends + B1 变异红）
  与 d②③⑥ 堵口（B2/B3/B5 变异红）、e① 行为探针（B4 红）维持 round-4 声明
  （验收单 §九）, 全部 11 个变异见 evidence-g24/g25-mutations-round5.txt。

## 读取范围 (严格限定)

1. backend/tests/unit/test_g25_journal_namespace.py（重点: `_assert_convergence_wording`
   与 `test_convergence_wording_has_no_unqualified_60s_claim`, 行 901-1010 附近;
   竞态锁与 d②③⑥ 锁段）
2. backend/app/services/lancedb_index_service.py 的 recover_pending/_merge_journal_entries
   （仅竞态修复相关行段）
3. backend/app/core/vault_state_paths.py 与 backend/scripts/migrate_index_journals_g25.py
   （仅两段被检文本是否仍满足门——三段真实文本的另两段在测试内以
   docstring/ast 方式读取, 无需另行核对行号）
4. 验收单 _bmad-output/验收单/UAT-CARD-G2-5-索引journal命名空间-2026-08-31.md §9.6

## 任务

1. **HIGH-4 e③ 是否 CONFIRMED-CLOSED**: 读 helper 现判据, 以**文字推理**给出
   仍可能误放的文本形态（如有）, 并判断三段真实文本 + 9 条篡改门是否覆盖;
   跑那一条 pytest 命令确认 27 passed。
2. **HIGH-3 竞态是否 CONFIRMED-CLOSED**: 读合并实现, 以文字推理审「旧行集合
   残影」判据的新洞（含你 round-4 提示词里我们主动列出的「并发 append 行恰好
   与旧快照逐字相同」场景——给出触发条件与真实性判断）。
3. **e①② 与 d②③⑥ 堵口维持性核对**（读测试代码, 不再重演变异）。
4. 新问题分级（BLOCKER/HIGH/MEDIUM/LOW）。

## 输出格式 (严格遵守)

- 逐条 CONFIRMED-CLOSED/STILL-OPEN + 证据 file:line + 文字推理说明
- 新问题分级清单
- 末行必须是: `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`
