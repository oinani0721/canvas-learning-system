> 批次: BATCH-2026-09-07-第十三批 · 车道 U10 (`card-u10-red-a`) · 卡 CARD-HYGIENE-conftest round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HYGIENE-conftest-r5.md)"`
> 审查绑定: `bbdf19ea`（= 本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 实测行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

## 结论

**不建议原样合并。BLOCKER 0 / HIGH 1 / MEDIUM 4 / LOW 0。** 本轮未发现新增代码门失效；P1-green 确实交付，且所测 conftest 的内容与 `bbdf19ea` 一致。但 round-4 七条没有全部闭环：验收单仍保留已宣布撤回的宽判据，r4 验收偏离也尚待限定例外裁定。**最小阻断项是统一验收口径并取得该项裁定，不需要扩面修改 W4 或默认补跑二十轮。**依据：U:657、689–696、890–894。

本次确认 HEAD 为 `bbdf19ea122a57e4efa8809878bb45b15c78daf0`，工作区 conftest 与该提交一致。下文缩写：

- **C**：[backend/tests/unit/conftest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py)
- **U**：[验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md)
- **E/**：[_bmad-output/审查/evidence-hyg-conftest/](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-hyg-conftest)
- **R1**：[round-1 原审](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/codex-review-CARD-HYGIENE-conftest.md)

## 发现

### [HIGH] 撤回宽判据未落实到待登记条目，限定例外仍未完成裁定

- **位置**：U:679–681、689–696、887–894。
- **问题**：§三·八的处置已正确收窄，但后文仍提出更宽的协议建议。
- **依据**：U:691–694 明确承认“计数＋失败正文”扩大接受范围，仅申请一次限定例外；U:890–892 却仍要求 **W4 哨兵失败改绑连接次数和失败正文、不绑 nodeid，一增一减按 flaky 处理**。U:679–680 也仍写“要真正排除，需要……n≥10”，与 U:695–696 的撤回冲突。
- **影响**：主 session 若采纳待登记条目，仍可能放行不同原因造成的增减。r4b/r5 空 diff 不能注销 r4 的既有偏离；`E/red-diff-r4.txt:1–4` 仍保留该一增一减。
- **建议**：撤回上述残留表述，统一引用 U:689–696。限定例外申请的姿态恰当，但**申请不等于获准**；获准前，该验收偏离仍阻断放行。无需把它升级为数据安全类 BLOCKER。

### [MEDIUM] 最终版本的证据登记仍不准确，但 P1-green 实跑缺口已经补上

- **位置**：`E/negctl-p1-green-r5-20260908T091401.txt:2–5、13–15、58–59`；`E/static-gates-r4-20260908T084107.txt:1–12`。
- **问题**：“r5 全部裁判绑定 `bbdf19ea`”不能按原话确认。
- **依据**：P1-green 抬头 HEAD 实为 **`ce5bc6e9…`**；但其 conftest SHA256：
  `2dcad68cdbc72c08374ca15770381b234ce322b30544ef5672295ff83cc8498a`
  与我独立计算的 `bbdf19ea` 文件对象及当前文件完全一致。它确实运行目标测试的八个用例，结果 `8 passed / rc=0`，无 `ERROR tests/`。此外，允许目录中的 ruff 原始存档只有 r4 版本，绑定 `d2c713…`，未找到最终内容的独立 r5 ruff 存档。
- **影响**：可以确认“测试了最终 conftest 内容”，不能确认“在最终 HEAD 上运行全部裁判”。**这不是 P1-green 未交付或自指探针冒充，也不足以判定作者没运行 r5 ruff。**
- **建议**：保留原始日志，补充“运行时 HEAD／所测文件 SHA／最终提交文件 SHA”的对应说明，并补齐最终 ruff 存档或收窄其交付声明。最终 conftest 内容已有独立绑定，因此此项按登记问题处理，不单独认定代码验收失效。

### [MEDIUM] 文本搜索与 AST 的盲区更正仍有反向残留

- **位置**：U:47–51、734–745。
- **问题**：开头正确说明覆盖范围不同，未证明清单仍沿用旧理由。
- **依据**：U:744–745 仍称 `grep 'test-vault'`“同样看不见上述形态”；上述列表包含 bytes、分段路径等，而 U:49–50 已正确说明这些形态可以被相应 grep 命中。
- **影响**：不改变当前 AST 行为，但“技术性更正已同步”的闭环结论不成立。
- **建议**：将 U:744–745 改为引用 U:47–51，仅保留“两者均不能穷尽写者，覆盖范围不同”。

### [MEDIUM] warning 原意见的原因仍被部分章节窄化

- **位置**：U:128–135、984–986；R1:78。
- **问题**：源码和主要说明已经修正，末尾对原审原因的转述仍未同步。
- **依据**：U:985 仍写“直接原因就是它不在允许读取面内”；R1:78 同时明确指出启动参数及运行期过滤器可能升级或隐藏 warning。C:258–261 已正确保留这些边界。
- **影响**：没有新增运行风险，但不能宣布相关文档全部闭环。
- **建议**：同步 U:984–986，明确读到 ini 只能核验仓库配置，不能建立普遍保证。

### [MEDIUM] 历史空 diff 引用仍指向被复用的文件

- **位置**：U:207；`E/red-diff-after.txt:1–4`。
- **问题**：每轮独立文件已交付，历史引用没有全部修正。
- **依据**：U:207 仍称 `red-diff-after.txt`“零行，无 `>` 也无 `<`”；该文件实际包含 r4 的一增一减，与 `red-diff-r4.txt` 相同。
- **影响**：引用与所述证据直接冲突。不过我从对应原始日志重算，历史 N2′ 空差集本身成立。
- **建议**：该行改引对应历史运行的独立证据，保留 r4 原始差异。

## 作者自述逐条核对

| # | 主张 | 成立? | 依据 |
|---|---|---|---|
| 1 | round-4 HIGH #1 已闭环 | **否** | U:689–696 正确；U:679–680、890–892 仍保留撤回内容。限定例外待裁定。 |
| 2 | P1-green 真跑并交付 | **是** | `E/negctl-p1-green-r5-20260908T091401.txt:13–15、58–59`；不是 selfprobe。 |
| 3 | P1-green 绑定 SHA 与 `bbdf19ea` 一致 | **文件内容一致；HEAD 标签不同** | 同档 :2–4。conftest SHA 独立重算一致；target SHA 仅与 red :76–79 的还原记录互证。 |
| 4 | 清理脚本修复现可核验 | **核心修复成立** | `E/cleanup-script-fix-20260908T091401.txt:10–25`。我从开工存档独立重算旧 13、新 12，多项仅 `/tmp/test-vault*`。完整 scratchpad 脚本未读。 |
| 5 | grep／AST 盲区错误已更正 | **部分** | U:47–51 已更正，U:744–745 残留。 |
| 6 | warning 旧保证及原因已同步撤回 | **部分** | C:258–261、U:128–135 正确；U:984–986 残留。`backend/pytest.ini:19–21` 确实只有 `-v --tb=short`，全文无相关过滤配置。 |
| 7 | 独立 diff 文件及历史引用都已修正 | **文件成立；引用未全修** | 各轮独立文件存在；U:207 与 `E/red-diff-after.txt:1–4` 冲突。 |
| 8 | “最常见”已收窄 | **成立** | C:336–338；r5 P2 实际输出见 `E/negctl-p2-red-20260908T091645.txt:29–31`。 |
| 9 | r5 目录级 202 条、空 diff、尝试 12、卫生门失败及干扰均 0 | **成立** | 独立抽取原始日志的状态＋nodeid 多重集，与基线相等；`E/unit-after-r5-20260908T091741.txt:2837、2839–3042`。该跑实际仍为 `rc=1`。 |
| 10 | r5 P2、7c、N3b/N3c 有效交付 | **所述结果成立** | P2 :24–31、74–82；两个 r5 selfprobe :61–67；N3b `…091728.txt:12–24`；N3c `…091717.txt:8–13、28–34、77–85`。 |
| 11 | 本轮没有新增控制流回归，卫生 fixture 无文件副作用、不依赖 cwd、不新增 `app.*` | **成立，限审查范围** | r4→r5 将字符串内容归一化后 AST 完全相同；变化仅 C:258–261、336–338。根定位 C:66–73、179–180；新增扫描 C:185–232。 |
| 12 | 骨架／tracked sha 两个硬 fail 面未放宽 | **成立** | 快照函数与基线一致，比较分支 C:283–293、失败出口 C:363–368 保留；P2 覆盖骨架。未发现因保留旧 `None` 边界新增的真假红路径。 |
| 13 | 没有再次发生“声称交付但找不到” | **不能全肯定，也不能说又没跑 P1** | 请求中的 P1-red `…091401.txt` 不存在，真实文件是 `…091349.txt:7、24–25、72–79`；属于错引。r5 ruff 独立存档未找到，见发现二。 |

**第 10 处确有登记**：`E/cleanup-script-fix-20260908T091401.txt:27–37`。此外，“七条全部整改”仍被 U:890–892 反证，这是同型问题继续存在的明确实例。是否另编号为第 11 处，取决于把它算作复发还是旧问题未闭合。**计数只适合记录发现历史，不能证明穷尽或合并就绪**；U:810–814 自己也承认这一点。

除 HIGH 项涉及的验收口径与待裁定例外外，上述 MEDIUM 项可登记处理，**不要求为它们扩面修改代码**。

## 我没有检查的面

- 未读取 target 测试源码、实际 cleanup 脚本、W4 实现、contract 属性输入链或生产代码；未评 202 条存量红的原因。
- 未读取 round-2／3／4 原审全文；round-4 七条按本次请求所列内容核对。
- 未重新运行 pytest、并发探针或 ruff；完成的是允许存档检查、提交文件哈希及 AST 比较、红 nodeid 多重集与清理抽取的独立重算。
- 未核验实际符号链接／权限布局、xdist、外部 warning 策略，以及主 session 是否已在读取面之外作出限定例外裁定。


