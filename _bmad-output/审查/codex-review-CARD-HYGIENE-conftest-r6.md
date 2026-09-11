> 批次: BATCH-2026-09-07-第十三批 · 车道 U10 (`card-u10-red-a`) · 卡 CARD-HYGIENE-conftest round-6
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli v0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-HYGIENE-conftest-r6.md)"`
> 审查绑定: `475f2bee`（= 本轮送审时的 HEAD）
> 会话头自证（抄 .stderr 实测行，stderr 本身不入库）:
> `OpenAI Codex v0.153.3` / `model: gpt-6-astra` / `reasoning effort: ultra`

---

## 结论

**暂不能合，应停交主 session 人审。**本轮绑定 `475f2bee09e3772d627414a3bc76f70d02b5b93a`；conftest 实算 SHA-256 与送审值完全一致，允许文件与该提交无差异。**总计：BLOCKER 0 / HIGH 1 / MEDIUM 2 / LOW 1；其中代码层 BLOCKER/HIGH = 0。**

D-15 的五轮已经用尽，docs-only 括注不能扣除已经完成的 round-5。本轮可以作为人审的补充证据，不能自行重计为“第五个代码审”。最小阻断是按 D-15 转人工处理最终 HEAD，并取得既有 W4 限定例外裁定；W4 已如实登记为获准前阻断。其余发现按登记类处理，不新增独立合并阻断。依据：验收单第 1094、1098、999、1120–1123 行。

以下简写：

- **C**：[conftest.py](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py)
- **U**：[验收单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md)
- **R1**：[round-1 外审](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/codex-review-CARD-HYGIENE-conftest.md)
- **E/**：[证据目录](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/审查/evidence-hyg-conftest)

## 发现

### [HIGH] docs-only 豁免不能把已完成的第五轮从计数中扣掉

- **位置**：[U:1120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md:1120)，U:1090–1099、1116–1123。
- **问题**：将“不计 docs-only 整改”推导为“round-6 是第五个代码审”，不成立。
- **依据**：U:1090–1094 已列出五次完成的审查；U:1098 明确“轮次已用尽”。括注约束的是**审后修改是否触发重审**，没有规定按发现属于代码还是文档来扣除审查轮次。`0491b12a` 的 docs-only 整改本身没有产生新轮，因此也没有一轮可以减掉。
- **影响**：“审后再改代码必审”不能自动解除“五轮仍有 HIGH 就转人审”。U:1123 的“唯一待裁事项”遗漏了这一停止条件。
- **建议**：明确本轮为交主 session 人审的补充复核；停止车道自主续轮，由主 session 处理最终 HEAD 和 W4 例外。

### [MEDIUM] 目录目标为扫描根的大小写别名时，会被误记为越界

- **位置**：[C:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/backend/tests/unit/conftest.py:211)，根因 C:125；失败出口 C:322、377–388。
- **问题**：身份回退从 `target.parent` 开始，跳过目标自身。新增调用传入的是目录；当目录恰好就是扫描根的大小写别名时，会漏掉其真实身份。
- **依据**：从最终文件提取原函数，在本机真实目录上只读执行得到：

  ```text
  root = .../backend/tests/unit
  alias = .../backend/tests/UNIT
  alias.samefile(root) = True
  alias.is_relative_to(root) = False
  _hygiene_within_root(alias, root) = False
  _hygiene_within_root(root, root) = True
  ```

  因此，链接目标若为 `../UNIT`，C:214 会加入 `unchecked`。N4 的对照实际指向 `tests/api`，没有覆盖这一分支（`E/negctl-n4-dirlink-fixed-20260908T112758.txt:24–26`）。
- **影响**：合法目录别名导致保守假红；本次未确认由此产生静默放行。
- **建议**：目录目标先检查其自身与扫描根的文件系统身份，再做父级回退；身份检查失败仍保留“无法判定”。本轮仅复现了 helper 反例，未创建链接进行端到端测试。

### [MEDIUM] 最终验收单仍混有历史状态与当前事实

- **位置**：[U:214](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md:214)，U:729–730、775–776、897–898、1051、1105–1107。
- **问题**：以下残留使“最终文档已全部闭环”不能成立。
- **依据**：

  | 残留 | 对照证据 |
  |---|---|
  | U:897 写“至少十五次”，下一行仍写“十四” | U:903–939 已列齐第 1–15 次 |
  | U:730 称第 13 次首次落到代码行为、此前均为文档 | U:917 明写第 1 次在代码里；U:926–928 也记载实际诊断出口错误 |
  | U:214 将 r1 运行指向“该轮独立证据”`red-diff-n2p-r3.txt` | r1 原始汇总为 `E/unit-n2p-20260908T071312.txt:3052`；r3 是 `…082024.txt:3062`，时长和 warning 数不同 |
  | U:1107 仍称 `bbdf19ea → HEAD` 的 backend diff 为空 | 本次实查该范围已有目录链接补丁；空 diff 只适用于截至 `0491b12a` |
  | U:1051 仍称“revert 点＝本卡单 commit” | U:1090–1094、1116–1119 已记录多个提交阶段 |
  | U:775–776 笼统称驳回理由均接受 | U:772 及 `E/selfaudit-missing5-r6.txt:62–68` 明示其中有四条零票，另有边缘项复核后仍修 |

- **影响**：影响历史追溯、整改核销及回退指引；这些残留本身不推翻 r6 的原始测试结果。
- **建议**：历史陈述锁定明确提交端点；修正计数和证据指针；将零票归为“未达确认阈值”，明确实际回退范围。

### [LOW] “跑分类存档末行 rc=”仍不成立，可能混淆测试与还原结果

- **位置**：[U:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a/_bmad-output/验收单/UAT-CARD-HYGIENE-conftest-2026-09-08.md:6)，U:790。
- **问题**：收窄到 `negctl-/selfprobe-` 等前缀后，仍不能统一按末行读取测试退出码。
- **依据**：`E/negctl-p1-red-20260908T115408.txt:74` 是测试 `rc=1`，末行 `:79` 却是**还原一致性** `rc=0`；`E/negctl-n3b-enum-denied-samefixture-20260908T115612.txt:24` 没有末行 rc。另 P1-green 的 `:3` 指向不存在的含 `r6` 的 red 文件名，实际还原证据在上述 P1-red 的 `:76–79`。
- **影响**：索引或取尾行脚本可能把还原成功误当测试成功；原始结果仍可正确辨读。
- **建议**：明确“测试结果后记录测试 rc，随后可能附清理与还原记录”；探针按各自判据读取，并修正 P1-green 指针。

## 作者自述逐条核对

| # | 主张 | 成立? | 依据 |
|---|---|---|---|
| 1 | 最终 HEAD 与 conftest hash 绑定 | **成立** | 起止两次核验一致；`E/unit-after-r6-20260908T114233.txt:2`、`E/static-gates-r6-20260908T115803.txt:2–4` 的所测 hash 与最终文件一致。属于内容绑定，运行时 HEAD 仍是 `0491b12a`。 |
| 2 | docs-only 括注使 r6 成为合法第五轮 | **不成立** | U:1090–1099、1116–1123；见 HIGH。 |
| 3 | dirlink 的 `is True` 才跳过，`None` 记账 | **分流成立，身份判定有遗漏** | C:207–214；见目录别名 MEDIUM。稳定目录结构下未发现新增递归或死循环路径，C:195。 |
| 4 | N4 正控仍抓到、被测改为记账 | **成立** | 修前 VOID `:10、16–23`；修后 `E/negctl-n4-dirlink-fixed-20260908T112758.txt:13、19–22`。 |
| 5 | “树内链接同样记账” | **限定成立** | N4 修后 `:24–26` 指向同 worktree 的 `tests/api`，仍在扫描根 `tests/unit` 外；不能证明扫描根内合法目录链的跳过行为。 |
| 6 | 脚本先断言 sha 已变；探针零残留 | **只能部分确认** | N4 修后 `:6–7` 的 hash 确实不同，但没有断言脚本正文；`:32` 只明确记录 dirlink 删除，不能单独证明全部探针零残留。 |
| 7 | 五个失败视角已经补跑 | **结果材料存在，算术成立** | U:761–772；`E/selfaudit-missing5-r6.txt:3–8、61–78`：17 条、10 条达确认阈值、去重 7 根因；18 次失败及四条零票已登记。未独立见证原始 agent 执行。 |
| 8 | round-5 五条全部闭环 | **部分确认** | W4 宽建议已撤回；warning 原因已更正，ruff 存档存在。但历史 diff 指针仍错，且 r5 原审全文不在允许面，不能逐字核销全部五条。U:1100–1104、214。 |
| 9 | W4 待裁事项已如实登记 | **成立** | U:697–705 与 994–1003 一致；U:999 明写获准前阻断，后续空 diff 不注销 r4。未发现第三处仍作为当前建议的宽判据；历史探针中的旧建议不能视为现行授权。 |
| 10 | r6 四目录结果成立 | **成立，限红 nodeid 口径** | 全部 138 份 txt 已读入核验。unit 原始 `E/unit-after-r6-20260908T114233.txt:2839–3040` 重算为相同的 202 条；api `:102–103`、regression `:190–191`、skills `:66–67`（同时间戳对应文件）均零红、rc=0。 |
| 11 | P1、P2、7c、N3b/c、静态裁判已补跑 | **存档支持** | P1-red `…115408.txt:72–79`、green `…115820.txt:7–9`；P2 `…115422.txt:74–82`；7c 两档 `…115439/115458.txt:61–67`；N3b `…115612.txt:15–24`、N3c `…115510.txt:30–34、77–85`；静态 r6 `:7–19`。 |
| 12 | 本轮未重跑 N2′，已披露 | **成立** | U:755–758；最新 N2′ `E/unit-n2p-20260908T082024.txt:2` 仍是旧 hash。最终代码另有 N1′ `…115736.txt:58–69、74–77` 证明告警出口；不能称最终 HEAD 已直接完成真双树实跑。 |
| 13 | 骨架 / tracked sha 硬门未放宽；旧 `None ↔ hash` 可移交 | **条件逻辑成立** | 基线对照保留 C:76–98、307–317 的检查条件；收集变量与诊断文本有改动，并非整段“一字未动”。未确认不修旧问题导致本卡新增真假红。 |
| 14 | round-1 告警意见只是因为没读 ini | **不成立；文档已纠正** | R1:78 同时指出外部参数和运行期过滤器；`backend/pytest.ini:19–21` 只能证明仓库 addopts。U:128–136 已准确收窄，当前 prompt 仍误述原因。 |

## 我没有检查的面

- 未运行 pytest、ruff、双树并发或落盘探针；测试结论来自存档重算，目录别名反例来自原 helper 的只读执行。
- 未创建真实目录链接验证完整 teardown；未验证并发换链、瞬时权限变化等情况。
- 未读取 round-2 至 round-5 外审原文、原始自审会话或 N4 验证脚本；不能将汇总存档等同于独立执行见证。
- 未评 contract 输入链、W4 实现、202 条既有红的原因或生产代码。
- 边界偏离披露：子审曾额外查看标准库谓词的运行时字节码，已停止，未用于本报告任何发现。
