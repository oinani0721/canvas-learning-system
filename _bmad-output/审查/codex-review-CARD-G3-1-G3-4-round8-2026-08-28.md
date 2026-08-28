终裁：**需九轮，不可验收 CARD-G3-1。CARD-G3-4 继续保持 CONFIRMED-CLOSED。**  
当前 `HEAD=a917964bea6876c0623cf362f30bd1f01562d451`。本卡残留 **BLOCKER 清零，HIGH ×4**。

## 逐点裁定

1. **duplicate 等价面：原项 CONFIRMED-CLOSED；NEW-FINDING / MEDIUM / 本卡**

   同一 `event_id` 下，除 `recorded_at` 外其余五个顶层事实字段均已纳入，[schema A4.5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:173) 的字段集合完整；排除 `recorded_at` 正确。

   但适用范围仍不清楚：通用 `append_event()` 在未传 `effective_at` 时每次以新 `now` 填充，[4/5 个 backend 调用点都省略该参数](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/services/learning_event_log.py:90)。若 envelope 门全局应用，合法重试会因 `effective_at=t1/t2` 被误判冲突。应明确只约束 `review/1`，或冻结默认值的比较语义。另 `json.dumps` 会把同一瞬间的 `Z`/offset 表示判为不同，属于保守误拒。

2. **fencing 接管：CONFIRMED-CLOSED（契约层）；生产 STILL-OPEN / 已移交 G3-3**

   [稳定锁身份、epoch、发布前复核](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:155) 加上 [conditional takeover CAS](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:161)，已封住 B/C 使用陈旧死亡证明覆盖新 owner 的竞态。真死亡证明对具体进程身份不可逆，因此 CAS 后没有旧 owner 恢复发布窗口。

   G3-3 实现不得用 `os.replace()` 替换被加锁的 sidecar inode；那会直接违反稳定锁对象条款，但属于生产实现审查，不回算本卡。

3. **三态可执行域：STILL-OPEN / HIGH / 本卡**

   `S=68949`、difficulty `[1,10]`、`"1.0"` 整数词法和重复键责任边界均已闭合。但“任意有限正 stability”仍过宽：

   ```text
   S=1.7976931348623157e308, D=5, state=2
   classify_card_state → normal
   真实 bridge Hard/Good/Easy → OverflowError:
   cannot convert float infinity to integer
   ```

   原因是 [classifier 只验有限且大于零](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:249)，并不等价于真实 FSRS 路径可执行。

   另有 MEDIUM：5000 位纯整数字段使 [_int_lexeme()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:198) 自身抛 `ValueError`，未返回 degraded；文档允许 `Review.fsrs_step: null`，当前 bridge 文本解析却会得到 `"null"` 并抛错，此生产偏差尚需登记给 G3-2/G3-3。

4. **A7 两档上界：原反例 CONFIRMED-CLOSED；NEW-FINDING / HIGH / 本卡**

   `review_time=9000-01-01Z` 产生的 `due=9000-01-09Z` 已被接受并判 normal，七轮误报确已解决。

   但 `fsrs_last_review` 仍按 9500 一般上界验证：

   ```text
   W=9400-01-01Z → classifier normal
   任意合法后继必须 review_time > W
   review_time 又必须 <= 9000 → 不存在合法后继
   ```

   [classifier](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:226)、[review 输入门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:439) 与 [A3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:153) 三者不自洽。`W=9000` 时 `W+1s` 也立即越界。

5. **vault_id 解析：STILL-OPEN / HIGH / 本卡**

   极简策略仍会静默错绑。完整反例：

   ```yaml
   vault_id: fake
   vault_id : real
   ```

   backend 的 [PyYAML 真值](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/app/config.py:780) 为 `real`；[_vault_id_of()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/backend/scripts/validate_learning_events.py:344) 只统计第一种词法并返回 `fake`。账本声明 `vault_id:"fake"` 时实测 **exit 0、零 WARN**。空行后的 plain-scalar 续行、多行引号体和 YAML 隐式类型裸词也可错绑。

   现网配置仍是 [双引号 `canvas_vault`](/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.canvas-config.yaml:10)，当前绑定正确。

6. **幂等语义与移交：CONFIRMED-CLOSED（主文）**

   [§一](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:11)、[§二](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:23) 与 [§九](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:221) 已一致区分幂等键语义和 parsed-field 判定方式；子串实现被正确标为缺陷。

   parsed 查重/bridge 时间/producer 精度归 G3-2，并发原子化归 G3-3，归属总体准确。LOW：所谓 a917“新增四条”不精确，9 类注释登记自首笔已存在；a917 实增三行。

7. **degraded reducer/proof：STILL-OPEN / HIGH / 本卡**

   精度常量、tie 和最终 bytes 可随 G3-2 真实 bridge 落地后锁定；但 proof schema 是契约职责，不能一并移交。

   [现有 proof 清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:187) 仍未定义：

   - 同源快照绑定的六字段、W 与 canonical hash；
   - 祖先 proof schema、终止条件和防循环规则；
   - prefix hash 的起止 bytes，以及是否包含 E 的终止 LF。

   这些行在 a917 中没有修改；仅 [§九新增了精度移交](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/docs/learning-events-schema-v1.md:224)。两个不同起点仍可满足同一清单并折叠出不同结果，无法机械唯一验真。

8. **回归与一致性：行为面 CONFIRMED-CLOSED；证据文案仍有 MEDIUM**

   实测复现：

   - 契约：`47 passed + 1 skipped`
   - golden：`13 passed`
   - 既有账本：`6 passed`
   - 合跑：`66 passed + 1 skipped`，10 条环境弃用 warning
   - 现网：23 行、exit 0、零 WARN/FAIL、`vault_id='canvas_vault'`
   - 账本前后 SHA256：`f78b99f…c11de`
   - 八提交 blob 恒定：
     - `learning_event_log.py`：`28cdaa18602b…`
     - `fsrs_manager.py`：`980b3758758b…`

   两份 UAT 主计数正确，但：

   - [G3-4 UAT:121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-4-FSRS-golden-vectors-2026-08-28.md:121) 称负验证绑定当前 HEAD，实际 [存证仍为 026d0735](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/审查/g3-4-evidence/g3-4-negative-verification.txt:3)。当前 bytes SHA 相同且 13/13 已独立复现，因此不重开 G3-4 语义。
   - [G3-1 UAT:173](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-s3-events/_bmad-output/验收单/UAT-CARD-G3-1-事件账schema冻结-2026-08-28.md:173) 的“round-7 全部点名反例通过”不实：存证未覆盖 degraded proof。
   - live 存证称含“完整命令”，实际未记录命令文本，属 LOW。

## 残留 BLOCKER/HIGH

- **BLOCKER：0**
- **HIGH ×4，均属 CARD-G3-1**
  1. 极大但有限 stability 被误判可执行；
  2. `fsrs_last_review` 与 A7 review 域冲突，产生无合法后继的 normal 卡；
  3. vault_id 极简解析仍可静默错绑并 exit 0；
  4. degraded 快照/祖先 proof/prefix exact-bytes 未冻结。

工作树未被本轮修改；唯一状态项是审阅前已有的空白未跟踪 round8 文件。`graphiti-canvas` 本会话未暴露，未能执行其记忆检索协议；其余结论均在当前 HEAD 与真实入口重新验证。

**最终裁定：需九轮。CARD-G3-1 不可验收；CARD-G3-4 保持 CONFIRMED-CLOSED。**


