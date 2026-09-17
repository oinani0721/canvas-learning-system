> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-8 round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-8-r1.md)"`
> 审查绑定: `d6ecd4edf8a24cbcfc3a5420d4257abf6932558f`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: gpt-6-astra`（stderr :5） / `reasoning effort: ultra`（stderr :9）

---

**结论：FAIL，当前不足以作为 G6 退出门。** 审查绑定 `d6ecd4edf8a24cbcfc3a5420d4257abf6932558f`。

隔离运行指定回归文件，原版 **13/13 通过**；以下四组负控副本也各 **13/13 通过**：通知缺失、inbox 日期改为 2099 年、overview 撤掉 snoozed 及其声明、overview 响应日期改为 1970 年。

1. **HIGH — 声明产出方仍可静默退出比较。**  
   [g68_five_view_contract.py:465](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:465)  
   对照输入：通知缺失时，`face_notification` 返回 `NOT_PRODUCED`；声明对账只检查字段键存在，比较器随后过滤该值，最终零分歧。picker 单板 `bucket=NOT_PRODUCED` 也未被拦下。

2. **HIGH — 日期豁免无条件覆盖整个 inbox 日期字段。**  
   [g68_five_view_contract.py:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:461)  
   对照输入：其余面为 `2026-09-12`，inbox 为 `2099-01-01`，仍只进已登记分歧；仅删除 inbox 一板的日期、保留另一板日期，产生的 `MISSING` 也被豁免。匹配实际只用“面＋字段”，未验证理由、时区或具体日期关系。

3. **HIGH — AST 门未检查字典字段读取。**  
   [g68_five_view_contract.py:319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:319)  
   对照输入：保留共享导入，新增 `def local_due(node, now): return node["fsrs_due"] <= now`，真实检查返回 `offenders=[]`；使用 `node.get("fsrs_due")` 同样未被拦下。现有负控依赖局部变量恰好命名为 `fsrs_due`。

4. **HIGH — overview 日期列未绑定实际响应。**  
   [g68_five_view_contract.py:260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:260)  
   对照输入：把真实 `_collect()` 结果中的 `projection["date"]` 改为 `1970-01-01`，整门仍通过。提取层重新调用 `_display_today(_display_now())`，没有观察响应日期的变化。

5. **MEDIUM — 声明与实现同步缩减时，对账仍通过。**  
   [g68_five_view_contract.py:440](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:440)  
   对照输入：将 `FIELD_PRODUCERS["snoozed"]` 改为仅 picker，同时删除 overview 的 snoozed 字段，整门仍通过。测试没有独立锁定该列的产出方集合，也没有要求至少两个面参与比较。

6. **MEDIUM — snooze/done 实际消费结果未被观察，范围超过 D-37 并存顺序。**  
   [g68_five_view_contract.py:217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:217)  
   静态对照输入：让返回的 `ranked` 把已完成板排首，保持 buckets/date 不变；契约丢弃 `_ranked`，仍从输入重算 done/snoozed，通知标题也只写入 census。因此连单独完成状态的消费失效都未覆盖。**这不构成要求修改 D-37 的依据，本轮未证成该处 T3 生产分歧。**

7. **MEDIUM — 负控文本锚未绑定实际失败断言。**  
   [g68_negctl.py:185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:185)  
   对照输入：inbox 分叉正常，另加入 notification 未登记分歧。真实 pytest 在测试第 125 行失败，但 traceback 同时展示此前已通过断言中的“竟然相同”；原判据实得 `rc=1、FAILED=True、anchor=True、ok=True`。

其余重点核对：

| 对照输入／检查 | 结果 |
|---|---|
| notification 改为 inbox 的分叉日期，形成 2:2 | 判红 |
| picker 单板删除日期字段 | 判红 |
| picker／overview 多出不存在的板 | 判红 |
| bucket 两面 1:1 | 双方均报告；本提交已修复任意归属 |
| recap 的 importlib 加载 | 已先注册 `sys.modules`，再执行模块 |

板集合只取 picker／overview 并集；其他面在集合外新增的行不会参与比较。当前 notification 适配器仅广播日期，其标题中的板身份没有一致性判据。

全程未修改仓库文件、未联网或连接数据库、未跑完整复习链；运行时写入限定在临时目录。上述测试结果不代表完整 CI 验收。

