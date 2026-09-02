裁决：`13b12f97` 不通过。当前为 **0 个 BLOCKER、2 个 HIGH**。两条已裁决产品行为均未作为缺陷升级。

## 一、历史反例

### 1. 前七轮 105 件主体样本：排除裁决面后 PASS

复跑核心命令：

```sh
for g in \
  g1_round1 g2_round2 g3_u2063_family g4_round4_matrix \
  g5_splitlines g6_comments g7_old_regressions g8_heading_spaces \
  g9_c4_history g10_more_invisible g11_more_comments g12_nested_c4 \
  g13_u2063_guard g14_visual_cross
do
  python3 -B <inbox_preview.py> \
    --vault "/private/tmp/card-g56c-r6-history.ji6dnd/$g/vault" \
    --now 2026-09-01T00:00:00+08:00 \
    --out-dir "/private/tmp/card-g56c-r6-current/$g" \
    --batch-size 10
done
```

逐字汇总，列为 `group / total / C6 / 建议删且true`：

```text
g1_round1	10	10	0
g2_round2	10	10	0
g3_u2063_family	9	9	0
g4_round4_matrix	10	9	1
g5_splitlines	8	0	8
g6_comments	10	9	1
g7_old_regressions	8	7	1
g8_heading_spaces	9	9	0
g9_c4_history	5	5	0
g10_more_invisible	10	10	0
g11_more_comments	10	8	2
g12_nested_c4	1	1	0
g13_u2063_guard	3	3	0
g14_visual_cross	2	1	1
105	91	14
```

14 件删除中：

- 10 件是 U+3164/U+2800、各类 `splitlines()` 字符落到 C4 的标题忽略面，属于用户裁决②。
- 4 件是空注释、真实精确重复等正向控制。
- 排除以上后，105 件危险重现为 0。

### 2. HIGH：前轮已登记的 ISBN/DOI 键名反例仍未闭合

前报告已记录该输入仍被删除：[final3:296](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/codex-review-CARD-G5-6c-final3.md:296)。

最小输入：

```yaml
---
ISBN_978-7-111-54742-6:
---
```

复现：

```sh
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/codex-g56c-13b12f97.zaZm0R/keyinfo/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/codex-g56c-13b12f97.zaZm0R/keyinfo/out
```

逐字输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/codex-g56c-13b12f97.zaZm0R/keyinfo/out/inbox-preview-_待处理.json / /private/tmp/codex-g56c-13b12f97.zaZm0R/keyinfo/out/inbox-preview-_待处理.md
  _待处理/ 共 2 件，本批全取（2 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 2 件 · 拿不准 0 件 · 建议删 2 件
```

```json
{"name":"doi-key-c4.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/canonical.md","basis":"归一化正文与 节点/canonical.md 逐字相等（sha256 相同）","conflicts":[{"kind":"frontmatter_metadata_present","detail":"本件 frontmatter 还带有元数据键（DOI_10_1000_hidden），正文重复证据不覆盖它们 —— 执行删除前请过目"}],"uncertain_reason":null}
{"name":"isbn-key-c3.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"exact_duplicate_of":null,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（35 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）","conflicts":[],"uncertain_reason":null}
```

根因：

- [frontmatter_pairs()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:616) 保留了 `(信息型键名, "")`。
- 安全兜底 [unknown_value_pairs](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1444) 只检查非空 value，不检查 key 是否承载信息。
- 随后分别从 [C3](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1539) 和 [C4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1565) 确定删除。

这不是标题裁决的连带：C3 单独即可穿透；ISBN 来源标识真实存在。依本轮规则定 **HIGH**。

## 二、新构造

### HIGH：`||` 被当成纯结构删除

输入字节：

```text
7c7c0a
```

复现命令：

```sh
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/codex-g56c-13b12f97.zaZm0R/fidelity/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/codex-g56c-13b12f97.zaZm0R/fidelity/out \
  --batch-size 10
```

逐字输出：

```text
本批 10 件 · 拿不准 2 件 · 建议删 8 件
01-logic-or.md | C3_empty_or_skeleton | 建议删 | true | exact= None | 剥离 frontmatter / HTML 注释后实质正文 0 字符（3 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）
```

`||` 可以直接表示逻辑或，不是 CommonMark 分隔线，也不属于用户钦定的五种空材料。根因是 [_is_structural_line()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:456) 把只含一种 `-=*_|:#>` 字符的行全部忽略，再由 [has_substantive_content()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:776) 判空。

裁判甚至把它命名为“对照逻辑或”并锁成 C3：[test_g5_6_clear_inbox.py:2666](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2666)、[2677](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2677)。这是有内容材料的确定删除，定 **HIGH**。

另有不含实质信息、但证明“五种”不是排他集合的额外 C3 面：

```text
02-empty-list.md | C3_empty_or_skeleton | 建议删 | true
03-empty-fence.md | C3_empty_or_skeleton | 建议删 | true
04-empty-comment.md | C3_empty_or_skeleton | 建议删 | true
05-empty-fm.md | C3_empty_or_skeleton | 建议删 | true
```

这些单独按 MEDIUM 的规格偏离登记。

## 三、决策忠实度

### C3：FAIL

五个点名正面均可达，但不是“只剩五种”。

逐字正面输出：

```json
{"name":"01-零字节.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
{"name":"02-纯空行.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
{"name":"03-纯分隔线.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
{"name":"04-空标题模板.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
{"name":"05-只有引用符.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true}
```

但裁判同时强制空围栏、全空值 frontmatter、空列表、`||` 必须 C3：[test:2207](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2207)、[test:2650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2650)。因此门会让真正收窄到五种的修正反而变红。

### C4：PARTIAL；已裁决连带不升级

纯函数复现：

```text
ATX_H1 => '共同正文'
ATX_H2 => '共同正文'
Setext => '独有标题\n===\n共同正文'
HTML_comment => '共同正文'
empty_frontmatter => '共同正文'
```

端到端：

```text
08-atx-title-dup.md | C4_exact_duplicate | 建议删 | true
09-h2-dup.md | C4_exact_duplicate | 建议删 | true
10-setext-title.md | C6_undecided | 拿不准 | false
```

结论：

- 围栏外 ATX H1–H6 全丢，包括承载“适用范围”等独有信息的 H2。这是用户裁决②的连带，只登记，不判 HIGH。
- Setext/HTML 标题不丢。因此“C4 不看标题”过宽；精确口径是“不看匹配 `_HEADING_RE` 的围栏外 ATX 标题行”。
- [dup_body()](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:755) 还会经前置解析丢 frontmatter 和 HTML 注释。非空值/非空注释通常由护栏接住；信息写在空值 key 时就是第一节 HIGH。

## 四、门强度

### 92 门：真实执行，PASS

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp \
backend/.venv/bin/pytest \
backend/tests/skills/test_g5_6_clear_inbox.py \
-q -p no:cacheprovider
```

逐字摘要：

```text
collected 92 items
backend/tests/skills/test_g5_6_clear_inbox.py .......................... [ 28%]
..................................................................       [100%]
======================= 92 passed, 10 warnings in 5.97s ========================
```

### 12 条变异：对指定回退真实承重，PASS

未在 worktree 执行；仅在 `/private/tmp` 隔离副本复算。

```text
源码基线 sha256 = e79861e38b0fd0a8dd0ad3996cfbd465aef3d7c14508eab93d7b73591452e52f
✅ M-NBSP       ... rc=1 | 2 failed, 90 passed | 还原 sha 一致
✅ M-CLAIMBOUND ... rc=1 | 1 failed, 91 passed | 还原 sha 一致
✅ M-ZEROWIDTH  ... rc=1 | 2 failed, 90 passed | 还原 sha 一致
✅ M-GENSIGNAL  ... rc=1 | 3 failed, 89 passed | 还原 sha 一致
✅ M-SRCALIAS   ... rc=1 | 1 failed, 91 passed | 还原 sha 一致
✅ M-DOIVAL     ... rc=1 | 2 failed, 90 passed | 还原 sha 一致
✅ M-PAIRS      ... rc=1 | 1 failed, 91 passed | 还原 sha 一致
✅ M-FALLBACK   ... rc=1 | 2 failed, 90 passed | 还原 sha 一致
✅ M-INVISENUM  ... rc=1 | 1 failed, 91 passed | 还原 sha 一致
✅ M-COMMENT    ... rc=1 | 3 failed, 89 passed | 还原 sha 一致
✅ M-HEADING    ... rc=1 | 1 failed, 91 passed | 还原 sha 一致
✅ M-STRUCT     ... rc=1 | 1 failed, 91 passed | 还原 sha 一致
finally 还原后 sha256 = e79861e38b0fd0a8dd0ad3996cfbd465aef3d7c14508eab93d7b73591452e52f (与基线逐字节相同)
G56C_NEGATIVE_CONTROL: PASS （12/12 变异的实际失败集合等于预先声明集合）
```

判据确实：

- 同时解析 `FAILED`、`ERROR`：[g56c_mutations.py:230](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:230)。
- 要求失败集合相等且 `rc == 1`：[g56c_mutations.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:283)。
- 要求 12 条均执行及源码最终还原。

潜在绕过为 LOW：不锁每轮 collected/pass/skip 总数。

探针逐字输出：

```text
extra_ERROR failed= ['test_gate', 'test_other'] ok= False
rc_2 failed= ['test_gate'] ok= False
91_skipped failed= ['test_gate'] ok= True
```

当前 12 轮每轮均合计 92，未实际触发该绕过。另因规则明确把 FAILED/ERROR 合并，同名 setup ERROR 可以证明“节点变红”，但不能独立证明目标断言因果。

总体门结论：**对登记的 12 个回退承重；不覆盖 ISBN-key 或 `||`，且 92 门对 `||` 是主动锁错，不足以支持清零。**

## 五、措辞

核对命令：

```sh
nl -ba canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
nl -ba _bmad-output/审查/evidence-g56c/README-取证说明.md
nl -ba _bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md
```

- **生产文件头：PARTIAL**

  - 偏差 18 的 5→1、标题独有信息丢失及 C3/C4 刻意不一致描述基本准确：[207–213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:207)。
  - [214–218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:214) 仍称多行 HTML/YAML 注释“未修”，已被当前实现证伪；又把真实形态写成“空键名”，实际是“非空信息型 key、value 为空”，淡化了 HIGH。
  - [875–882](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:875) 仍称标题不算正文、U+3164/U+2800 会落 C3，与现实现矛盾。
  - [1022–1024](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1022) 写“只剩三种”，另一处写五种，实际还有更多。

- **生成 MD §七：FAIL · MEDIUM**

  [2137–2146](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2137) 逐字只列“①……⑧”，漏：

  - ⑨ 任意非空 frontmatter value；
  - ⑩ 被剥掉的闭合 HTML/YAML/fence-info 内容；
  - C3 五种产品口径；
  - 偏差 18 的 C4 标题代价。

  因此标题“如实声明”比实际披露面更宽。

- **UAT：FAIL · MEDIUM**

  决策描述在 [125–126](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:125)、[192–195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:192)准确；但当前文档同时声称：

  ```text
  line 5:   终态 92 门 / 12 条变异全中
  line 62:  终态 88 条测试全绿
  line 95:  88 passed
  line 99:  本版 8 条回退 / 8/8
  line 214: 裁判 88 条
  line 221: 3 条回退变异
  ```

  [252–253](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:252) 还把已修注释路径写作未修；line 195 对“属性/注释信息保得住”的概括也宽于证据。

- **evidence README：PARTIAL/FAIL · MEDIUM**

  - §§9–10 对五个指定面、偏差 18 和 5→1 量化基本准确。
  - [37–42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:37) 仍写三条变异、`1 failed, 81 passed`、恰好一门红；[104](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:104) 仍写 8/8。
  - [57](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:57) 的“本版”SHA 为旧值 `cba6e464…`，当前生产 SHA-256 为 `e79861e…`。
  - [144–147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:144) 写三种，后文写五种，两处都漏实际额外面。
  - runner 文件头仍称“八条回退变异”。

## 六、登记

| ID | 级别 | 状态 | 内容 |
|---|---:|---|---|
| G56C-H1 | HIGH | OPEN | ISBN/DOI 信息写在非空 key、value 为空时，C3/C4 双出口确定删除 |
| G56C-H2 | HIGH | OPEN | `||` 逻辑或被当纯结构，落 C3 确定删除 |
| G56C-M1 | MEDIUM | OPEN | C3 五个指定面都在，但还有空列表、空围栏、空注释、空值 FM 等额外面 |
| G56C-M2 | MEDIUM | 已裁决连带 | C4 忽略所有 ATX H1–H6，但不忽略 Setext/HTML 标题；偏差 18 应限定标题语法 |
| G56C-M3 | LOW | OPEN | 变异 runner 不锁 collected/skipped 总数 |
| G56C-M4 | MEDIUM | OPEN | 生产头、MD §七、UAT、README 存在上述陈旧、互斥或过宽声明 |
| G56C-P1 | PASS | CLOSED | 105 件主体历史反例排除裁决面与正控后无危险重现 |
| G56C-P2 | PASS_WITH_LIMITS | CLOSED | 92 门全绿；12/12 指定变异失败集合相等、rc=1、源码还原 |

给定 diff 的七个目标 blob 均与当前文件逐字匹配；未额外读取提交对象，因此只证明“当前字节 = `13b12f97` diff 目标字节”。未联网、未碰 live vault、未写 worktree，也未跑全仓 CI。

BLOCKER/HIGH 清零: 否


