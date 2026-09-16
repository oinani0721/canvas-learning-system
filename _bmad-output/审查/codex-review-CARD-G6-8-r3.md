> 批次: BATCH-2026-09-11-第十四批 · 车道 T3 · 卡 CARD-G6-8 round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G6-8-r3.md)"`
> 审查绑定: `ca443a517cb9a2ab45f8a42752cdd5c75c9e01d8`（本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 前三行含 model 行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（stderr :2） / `model: gpt-6-astra`（stderr :5） / `reasoning effort: ultra`（stderr :9）

---

**round-3：FAIL。BLOCKER=0，HIGH=2，MEDIUM=5，LOW=1。**

绑定最终 HEAD：`ca443a517cb9a2ab45f8a42752cdd5c75c9e01d8`。受审文件与该 HEAD 一致，工作树未修改。

原版实跑 **23/23**；下述五组完整对照副本也各 **23/23**。本轮仍未满足 D-15。

1. **HIGH — 普通 due 读取仍未被 AST 门拦下。**  
   [g68_five_view_contract.py:428](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:428)  
   对照输入：在合法共享 import 后加入 `match node` → `case SimpleNamespace(fsrs_due=value): return value <= now`，静态门返回 `offenders=[]`，实际函数能判断到期。字段名位于 `ast.MatchClass.kwd_attrs`。另一个常规输入 `re.search(r"^fsrs_due: *(.*)$", text, re.M)` 也未被拦下，因为字符串检查仅接受整串相等；两者均未拼接字段名。

2. **HIGH — 板级锚未覆盖板内节点缺失。**  
   [g68_five_view_contract.py:232](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:232)  
   对照输入：共用 `_board_bucket_rows()` 仅跳过节点“同板未来”，保留“板-到期”的另一个节点。两面的该节点同时退出比较，`FIXTURE_BOARDS` 仍完整；实得 **23/23、verdict=PASS、未登记分歧=[]**。需要核验提取前后的节点身份完整性。

3. **MEDIUM — 清单对子集缩减不敏感。**  
   [g68_five_view_contract.py:786](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:786)、[test_g68_five_view_contract.py:229](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g68_five_view_contract.py:229)  
   对照输入：从 `FIXTURE_BOARDS` 删除“板-未来”，fixture 继续创建它，同时共用提取层不返回该板；两处 `<=` 都通过，完整测试 **23/23**。当前方向只能发现清单多报，不能发现漏报，至少应对账完整集合相等。

4. **MEDIUM — 队列只剩让位板时，完整性检查仍退化。**  
   [g68_five_view_contract.py:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:266)  
   对照输入：真实 picker 返回后，仅保留“板-学习中／板-脏日期”，通知同步点名新的第一块；`require_in_ranked` 全满足，`all(...)` 直接返回，完整测试 **23/23**。固定 fixture 中本应存在的非让位板没有独立在场要求。

5. **MEDIUM — fixture 仍不能证明 snooze 被消费。**  
   [g68_five_view_contract.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:295)、[g68_five_view_contract.py:312](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:312)  
   对照输入：只把传给真实 picker 的参数改为 `snoozed={}`，完整测试仍 **23/23**。“板-脏日期”原本就在队尾，矩阵又从原始输入重算推迟状态，因此在场和顺序检查均无法区分消费是否发生。对称的 `board_done={}` 会被拦下，实得 **8 failed、15 passed**。

6. **MEDIUM — 任意短前缀仍被认作通知点名。**  
   [g68_five_view_contract.py:872](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/scripts/g68_five_view_contract.py:872)  
   对照输入：标题改成 `📚 今日复习 · 板`，没有省略号，也无法区分任何 fixture 板，完整测试仍 **23/23**。`startswith()` 没有限定为真实截断形态和长度。

7. **MEDIUM — captured stdout 的 `E ` 行会被认作失败原因。**  
   [g68_negctl.py:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/_bmad-output/审查/evidence-g68/scripts/g68_negctl.py:336)  
   负控输入：保留原目标 nodeid，测试先 `print("E 独立 due 算法")`，再 `assert False, "UNRELATED_FAILURE"`。真实 pytest 输出经原判据得到 **`rc=1、FAILED=True、anchor_hit=True、runner_ok=True`**；指定锚实际来自 captured stdout，失败归因仍不成立。

8. **LOW — 正常 FAIL 的诊断仍在 pytest 包装层丢失。**  
   [test_g68_five_view_contract.py:49](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t3-review/backend/tests/regression/test_g68_five_view_contract.py:49)  
   对照输入：契约计算期打印唯一诊断，再制造日期分歧；直接 CLI 的 stderr 保留诊断，同一副本经主测试判红时，完整 pytest 输出不含诊断。`_run()` 在报告存在时丢弃 stderr，L10 尚未覆盖 pytest/CI 路径。

其余重点问题的结论：

- **inbox 文本锚与豁免：**当前入口产物与固定 `+08:00` 谓词一致，已实测 `15:59:59Z → 09-12`、`16:00:00Z → 09-13`。措辞变化确实可能造成 `MISSING` 误红；目前未发现由此产生的已证漏红。就本门用途，漏红风险更大。
- **400 字符豁免：**长度不是有效语义边界；当前整串相等检查对不足 400 字符的正则读取也漏检，不能把遗漏范围限定为长字符串或运行期拼接。
- **pytest 输出形态：**`pytest.fail(..., pytrace=False)` 的失败正文可没有 `E `；`--tb=line` 没有所需的失败块标题；`--tb=short` 可识别。前两者作为格式边界，不另计缺陷。
- **确定性：**当前产物文件名固定，每次契约使用新临时目录；真实入口同输入两次的 MD 也逐字节相等。现有二跑测试只约束报告 stdout，不能据此宣称所有产物均确定。


