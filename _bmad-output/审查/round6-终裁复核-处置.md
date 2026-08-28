# CARD-G5-4 / CARD-G5-9 — round-6 终裁复核处置对照表

> **来源**: 多视角 workflow 终裁复核（3 视角 fan-out + 逐条实跑证伪，20 agent、2.15M tokens、528 次工具调用）。
> **结果**: 22 条发现，**全部 verify real=True**（每条都由独立 agent 实跑复现，含对照组消融实验）。
> **处置状态**: 全部已处置。判据见文末。
>
> 本轮之所以关键：它抓到了一条**贯穿五轮 Codex 都没发现的 BLOCKER**——那条缺陷是前面
> 所有信号防线的**总开关**。也抓到了三条**误伤**：round-5 的收紧让"按 SKILL 逐字写的合法报告"反而过不了。

## BLOCKER（1/1 处置）

| 发现 | 处置 |
|---|---|
| **段落存在性检查与下游定位的口径不一致 = 所有数字绑定的总开关**：存在性检查用**前缀**匹配（`^## AI 侧对账`），下游 tips 绑定与 signals 绑定用**整行**正则定位。给标题加任意后缀（`## AI 侧对账 · 本轮`）→ 存在性检查照样判"段落在场"，下游正则匹配不上 → `_verify_numbers` **bare return** → **tips 两数绑定 + 整块 signals 绑定全部跳过**。实测：四条信号行整体删除、数字随意改、有数信号谎标「无据」、tips 填 999/888，全部 `VERIFY PASS`。五个后缀变体（`x`/`.`/`：`/` ·`/`（本轮）`）无一例外 | ① 新增 `_SECTION_RE(section)` 作为**唯一**口径（段名后只允许行尾或全角括号补充——模板自带的 `## 台账（种子/派生）` 必须放行），**存在性检查与下游定位共用它**，缝隙消失；② `_verify_numbers` 的 recon 缺失改为**记 problem 并继续跑 signals 绑定**，不再 bare return；③ 新增 `_verify_signals_if_present` 保证信号绑定在**每条**返回路径上执行 |

同源第二处：`## 你现在可以做的` 加后缀同样让动作段白名单整块跳过 → 同一修复覆盖。

## HIGH（3/3 处置）

| 发现 | 处置 |
|---|---|
| **规模自陈五元组取首个匹配**：无唯一性约束 → 在报告更早处放一行带真数字的诱饵（散文行，甚至代码围栏里），可见的 callout 就能写 `120 成员/350 批注` 并 PASS。对照实验证明是"首个匹配"机制：诱饵移到 callout 之后即 FAIL | 改为**全文所有五元组逐条校验且必须恰好一条**——诱饵行自己也会被校验，无处可藏 |
| **误伤**：round-5 的「含派生的行必须整行匹配白名单」漏掉 SKILL 自己规定的白名单动作句（`…Cmd+Shift+D 派生新节点`）→ **按 SKILL 逐字写的合法 fallback 报告无法 PASS** | 白名单补动作句形态 |
| **自相矛盾**：`_NODATA_REASONS` 的 `本板无派生角色成员` 内含子串 `无派生`，而 `_VERIFY_FALLBACK_DERIVE` 含 `无派生` 且全文无条件命中 → 自家两条规则打架，写白名单文案必 FAIL | 从词表移除 `无派生`（它是白名单文案真子串）；白名单补「无来源结论无据行」形态 |

## MEDIUM（6/6 处置）

| 发现 | 处置 |
|---|---|
| `_strip_code_blocks` 只对信号行生效，剔除是**双向**的：挡住"藏行"却放行"在围栏里追加第二组造假信号"（围栏内容在 Obsidian 里照常渲染给读者） | 被剔除的文本里**不得出现任何信号 label**，否则 FAIL |
| 数字终核的**绑定对象由报告自己指定**：scan JSON 路径 = frontmatter 的 board 值，从不校验它与报告文件名一致 → 报告可绑定**另一块板**的 scan JSON | 校验文件名 `回顾-<board>-<日期>.md` 与 frontmatter board 一致 |
| tips 两数只绑段内**首个**匹配，段内第二条同形句与段外任何位置都不受检 | 改为**全文逐条**校验 + 段内必须各恰好一条 |
| 全局「派生」白名单⑤ `^.*派生角色成员.*$` 是无条件自由文本放行，可夹带任意子女数断言 | 收紧为两条固定句式 |
| 全文子串禁词误伤：`子节点` 是「种**子节点**」的真子串 → fallback 报告里「这块板只有 1 个种子节点」被判违规，而「种子/派生」正是本 skill 核心术语 | 从词表移除（结构性防线由行白名单承担） |
| **G5-9**：`cmd_undo` 完全缺少 create 侧已有的目录 symlink 越界守卫 → `检验白板/` 被 symlink 带出 vault 后 containment 仍判通过 | 补同款目录级守卫；回归锁 `test_undo_refuses_when_exam_dir_symlinked_out` |
| **G5-9**：跨板成员在「阶段数字」里重复计数（`节点/` 是一 vault 一学科的**扁平共享池**，同一节点被两板列出是正常形态），产物还重复列成员链接，零去重零声明 | 总计按 node_id 去重 + 显式声明 `跨板重复成员 N 个`；preview `totals` 加 `members_listed`/`duplicate_members`；回归锁 `test_cross_board_members_deduped_in_totals` |

## 消费面冲突（2/2 处置 —— 第四、第五个未申报消费方）

| 发现 | 处置 |
|---|---|
| **Dashboard「🗂️ 考察历史」把阶段回顾板当成一场已完成考察计入统计**：`type: exam_board` + `status: done` + 无 `questions` → `isDone` 为真 → 场次数与完成数被污染（这是此前四轮都没识别出的**第四个消费方**） | `Dashboard.md` 的考察历史查询按 `recap_kind !== "stage_recap"` 排除，并注明原因 |
| **阶段回顾板劫持 `/quiz-answer` 的无参默认目标**：定位级联第三档取「`检验白板/` 里最近修改的一张」，而刚创建的阶段回顾板恒为最新 → 用户答完真考卷后做一次阶段回顾、再裸输 `/quiz-answer` 就会命中它 | `quiz-answer/SKILL.md` 定位级联显式排除 `recap_kind: stage_recap` 并给出替代指引 |

两者共用产物已有的 `recap_kind: stage_recap` 标记；新增 `test_consumers_can_distinguish_stage_recap` 与
`test_declared_consumers_exclude_stage_recap`（改回去即红）。

## LOW（5/5 处置）

`]`/`[` 补进 wikilink 语义字符护栏 · 两份验收单的裁判数按 `--collect-only` 实测改（G5-4 105 / G5-9 31 / 合并 236） ·
分位数按证据实际值改（78 天，p25/p50/p75 = 77/77/77——原写 78/78/78） · 两个证据包 README 的快照口径改为
**全 vault**（G5-4 324 文件 / G5-9 69 文件，含 `.claude/`；原写「48 文件」且只覆盖四个数据目录，正是漏掉
`__pycache__` 写侧的原因） · SKILL.md 表格管道符转义与 `undo_hint` 说明如实化。

## 处置后判据

- `test_recap_scan_signals.py` **105 passed** / `test_g5_9_recap_exam.py` **31 passed**
- 合并跑：**236 passed**；ROUTING 66/66；`ruff check` 干净
- BLOCKER 与 HIGH 的原始复现路径逐条亲手复跑，全部 exit 1

## 累计（五轮 Codex + 三轮 workflow）

| 轮次 | 实质发现 |
|---|---|
| Codex r1 / workflow r1 | 6 / 5（含 1 BLOCKER） |
| Codex r2 / r3 / r4 / r5 | 9 / 19 / 12 / 5 类 |
| workflow r2 / **r3（终裁）** | 2 / **22（含 1 BLOCKER，全部 real=True）** |
| **合计** | **80 条，全部处置** |
