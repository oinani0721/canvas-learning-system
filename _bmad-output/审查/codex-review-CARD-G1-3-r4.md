**结论：BLOCKER 0 / HIGH 1 / MEDIUM 6 / LOW 1。HIGH 尚未堵住。** MEDIUM 包含两项已如实登记、仍未修复的旧限制。

审查绑定 `9198c9380639225272388719c438958b45e315ae`。全程只读，未连接数据库或服务。负控输入在内存中构造，调用正式 `main()`，保留真实 Git 与文件检查；结束时 HEAD、受版本控制文件未变。

1. **HIGH — 同一张合法能力表仍能有六行完全不受检查。**  
   [ledger_lint.py:162](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:162) 遇到不以 `|` 开头的数据行就停止解析，但 `:229–233` 的全文扫描继续把这些行算在原表中。

   **具体负控输入**：保留前十五行；将原台账 `:77–82` 六行的第五格改成 `E5`，仅删除各行最前面的 `|`，其余内容不变、不补 manifest。

   实测结果：

   ```text
   rows=15
   L3 PASS - (0 rows)
   L13 PASS - 全文表格结构符合契约：{2: 1, 11: 1}
   LINT: PASS
   rc=0
   ```

   本地 Markdown 渲染仍显示同一张能力表、六个 `E5` 单元格；另一审查分线独立复验得到相同结果。

   另外五种形态也实测未被拦下：

   | 负控输入形态 | 门检查的能力行 | 结果 |
   |---|---:|---|
   | 后六行放进每行带 `>` 的引用表格 | 15 | rc=0 |
   | 后六行改成普通列表，明确保留能力与 E5 声明 | 15 | rc=0 |
   | 后六行改成现有两列规则表中的能力登记行 | 15 | rc=0 |
   | 第二张表前放一行以三个反引号包住的行内代码 | 15 | rc=0 |
   | 在规则表单元格内放含 E5 的 HTML 表格 | 21 | rc=0，HTML 标签计数为 0 |

   原因分别包括引用容器未识别、只约束表格数量、错误切换 fenced 状态，以及扫描表体时跳过 HTML 检查。**原四种负控输入被堵住，不等于能力行检查范围已封闭。**

2. **MEDIUM — L13 对合法说明文字和代码示例仍有假红。**  
   [ledger_lint.py:191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:191) 的分隔行识别过宽，`:215` 又只用布尔值切换代码块状态。

   以下对照输入均保留原来的 21 行能力，结果都是**仅 L13 失败、rc=1**：

   - 追加 `说明 A | 说明 B`，下一行写 `-------------`：实际是 Setext 标题，却被计成新增两列表。
   - 用四个反引号包住包含三个反引号及示例表的代码块：合法代码块被误拆，示例表被计入。
   - 在规则表表头文字中使用合法的 `\|`：实际仍为两列，扫描器计成三列。
   - 普通说明写“请不要使用行内代码 `<table>` 标签”：代码文字被当成 HTML 表格标签。

   `{2:1, 11:1}` 可以作为当前版本的显式契约，**固定值本身不另判缺陷**；但新增说明表或能力列必须同步改契约，而且数量相等不能证明扫描器与能力解析器检查的是同一批内容。

3. **MEDIUM — M-8 改写仍把实际失败条件写成“不阻断”，并扩大了扫描范围。**  
   [capability-ledger.md:74](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:74) 写“集合漂移只报告、不阻断”；实际 `skill_portability_lint.py:2336–2340` 将漂移加入 `problems`，正式测试 `test_skill_portability_lint.py:234` 执行 `assert not problems`，因此会红。目录枚举只适用于 frontmatter 层；正文和越界检查在 `:2382`、`:2411` 仍遍历各自 baseline。**发现新增 skill，不等于其正文进入全部判据。** fenced Python/shell 解析这一处改写属实。

4. **MEDIUM — 新抽查的部署超时行把已覆盖路径写成门未覆盖的路径。**  
   [capability-ledger.md:63](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:63) 声称超时“只覆盖测试侧、不覆盖运维手跑脚本”，但 `scripts/deploy-vault.sh:921–948` 的 Perl `alarm` 实际包住 `npm run build`，所引部署超时验收单 `:78–108` 也明确记录脚本侧实现。应区分 **build 已有上限**与**整条六步部署没有统一上限**。

5. **MEDIUM — 新验收单混用了旧证据、旧输出和旧审查状态。**  
   [UAT-CARD-G1-3-2026-09-18.md:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/验收单/UAT-CARD-G1-3-2026-09-18.md:54) 起，共引用 **14 个在绑定提交中不存在的不同 `.txt` 文件名**；实际文件已换成 `180956`／`180924` 版本。另有：

   - `:55` 保留旧 L13 输出格式；`:64` 写负控⑦红七条，当前存档实际三条。
   - `:5` 要求从 §7 最后一行核最终绑定，但 `:135` 仍是“r3／本卡最终 SHA／待审”。
   - `:104` 前半段介绍新结构契约，后半段仍声称不同列数无法识别。
   - `:70` 仍写“原件未被负控触碰”，与 `:107` 承认两点比较局限相冲突。
   - `:92` 的“现在都堵上了”与本轮 HIGH 实测不符。

   验收单确已交付，但不能按当前正文判为整改说明完全准确。

6. **MEDIUM — L9 的主干身份仍由调用方保证；本轮登记属实，未修。**  
   [ledger_lint.py:311](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:311) 默认 `HEAD`。实测以部署行为基础构造十五个唯一 id，核验 SHA=`7e1d6b53`、证据 SHA=`79134975`，同时传入 `--trunk=7e1d6b53`，整体 **rc=0**。这不否定固定可信 trunk 后的祖先检查；验收单 §4.11 对边界的说明准确。

7. **MEDIUM — L12 的依赖交集与 tag 错配两条旧路径仍在；登记属实，未修。**  
   [ledger_lint.py:496](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/_bmad-output/审查/evidence-g13/ledger_lint.py:496) 仍将 `⇩` 后的降级触发面纳入入口集合，`:455–458` 对 tag 只查存在。分别把索引删除行证据 SHA 换成只命中依赖的 `8f3ee155`、把部署行 tag 换成 `merged-squash/card/t5-bugs-CARD-T-SWITCHVAULT`，均实测 **rc=0**。验收单 §4.12 没有把它们写成已修复。

8. **LOW — 内部鉴权行的一份具名测试链接错配，但 E1 仍有其他证据。**  
   [capability-ledger.md:75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p10-docs/docs/release-evidence/capability-ledger.md:75) 引用的 `test_api_key_security.py:4–23` 测的是 ProviderConfig／provider 凭据保护；同列 `evidence-sec-dangling/auth-behavior-tests-20260916T194754.txt:6–9、30` 才记录真正内部鉴权测试的 30 passed。因此是具体链接不准确，不能据此否定 E1。

**M-6、M-7 的本轮明确整改点已到位。** `review_overview.py:771–776、1097–1098、1714–1718` 支持四态、stale 保留数据、无投影解释文案；`inbox_preview.py:1766–1768、1826、2445–2462` 支持 C3/C4 删除提名及默认写 `<vault>/outputs`。C4 比较的是归一化正文，不能扩读为整文件字节相同。“终局 Web UI 尚未完成”的整体产品完成度未由这些代码片段独立核实。

本轮新增五行反查，与 r2、r3 均不重复：

| 行 | 入口与证据正文核对 | 结论 |
|---|---|---|
| CAP-DEPLOY-01 | `deploy-vault.sh:5` 是六步说明；测试 `test_deploy_vault_sh.py:637、666` 真跑脚本，存档有 196 passed／9 skipped | E2 按台账本地脚本口径有据；激活未端到端验证已登记 |
| CAP-DEPLOY-TMO-02 | 测试文件 `:59` 是兜底说明；脚本另有真实 build 超时实现 | E1 有据；限制描述有上述 MEDIUM |
| CAP-SYS-AUTH-14 | `security.py:74` 为正式鉴权入口，`:194` 为 WebSocket 入口 | E1 有据；具名测试链接有上述 LOW |
| CAP-README-LINT-18 | `check_readme_claims.py:83` 确实只列 README；测试真调 main／Git，存档有 120 passed | PASS，范围与措辞限制有据 |
| CAP-VAULT-SCOPE-21 | `vault_scope.py:388` 为 `require_read_group`；存档有 49 passed、两组负控及恢复结果 | PASS，调用范围与前缀限制基本准确 |

这五份入口文件在基线与绑定提交间字节相同，所列相关 SHA 均为基线祖先。

**验收单的限制登记多数诚实，但遗漏分类不能全部确认。** §5.7 新补的 snooze/unsnooze、交互复习壳、board-recap，以及其余具名卡的合入锚均可核实；唯独 **`undo_journal` 未核实**：该精确标识在绑定树中只命中新验收单，近似描述只找到规划内容，不能直接归为“已合但未入账”，也不能据此断言功能不存在。`:84` 的历史“全程未连服务”未获所引地盘文件的连接审计证据，亦标未核实。

哈希整改的字节事实成立：台账实际 SHA256 为 `70235e13…a2aa7a3`，与提交内新原件记录一致；补充的 `ledger-sha-at-commit-20260918T181053.txt` 三项哈希也全部匹配，但它是**提交外的未跟踪补件**。不能再说定稿字节仍未匹配；两时刻比较也仍不能证明全过程未触碰。

**十二段负控未发现红在别的原因上。** 按描述重建后：

| 段 | 实际失败判据 |
|---|---|
| ①～⑩ | 依次仅 L4、L3、L3、L1、L11、L12、L13、L9、L3、L4 |
| ⑪四种负控输入 | 均仅 L13，rc=1 |
| ⑪ fenced 对照输入 | PASS，rc=0 |
| ⑫绝对路径／上跳路径 | 均仅 L3，rc=1 |

原始负控副本未交付，因此这是按描述独立重建，**不是逐字回放历史输入**。尤其⑧须同时替换核验 SHA 与证据 SHA；只改核验 SHA 会额外红 L11。


