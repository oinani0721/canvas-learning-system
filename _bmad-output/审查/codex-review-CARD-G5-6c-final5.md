裁决：`67aeabc1` 不能清零。两项用户裁决均未作为缺陷升级；本轮另发现 **0 个 BLOCKER、3 个 HIGH**。

## 一、历史反例

结论：**PASS_WITH_LIMITS**。按前七轮报告保存的逐字片段、hex 和根因族重建 9 组 84 件，覆盖 C3/C4 两个出口；84/84 均降为 `C6 / 拿不准 / false`。

复跑命令：

```sh
for g in \
  old_regressions r1_r2_fm_c3 r1_r2_fm_c4 r2_metadata_c3 \
  r3_invis_c4 r4_invis_more_c4 r5_r7_comments_c3 \
  r5_r8_comments_c4 r7_r8_struct_keys
do
  python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
    --vault "/private/tmp/card-g56c-r9-history.KK3488/$g/vault" \
    --now 2026-09-01T00:00:00+08:00 \
    --out-dir "/private/tmp/card-g56c-r9-history.KK3488/$g/out" \
    --batch-size 10
done
```

汇总命令及逐字输出：

```text
{
  "groups": 9,
  "total_items": 84,
  "c6_false": 84,
  "delete_true": 0
}
```

本批点名的两项修复也闭合：

```text
03-logic-or.md	C6_undecided	拿不准	false
04-double-hyphen.md	C6_undecided	拿不准	false
05-isbn-key.md	C6_undecided	拿不准	false
06-doi-key.md	C6_undecided	拿不准	false
```

实现链位于 [inbox_preview.py:458–472](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:458)、[662–757](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:662)、[1304–1336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1304)、[1459–1586](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1459)。

限制：旧报告只保存了 105 件结果，没有保存全部输入 bytes/构造器。因此不能诚实声称“旧 105 件 byte-for-byte replay”；84 件证明的是报告中全部危险根因族已按所存证据重建并闭合。

## 二、新构造

统一真实 CLI：

```sh
python3 -B /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-r9-impl-fuzz.VKtO8A/vault2 \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-r9-impl-fuzz.VKtO8A/vault2/out \
  --batch-size 10
```

### 1. HIGH｜C4 抹掉有语义空白

`dup_body()` 除已裁决的标题外，还在 [780–783](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:780) 对每行 `rstrip()`、删除所有空行。Markdown 行尾双空格是硬换行，空行是段落边界；围栏代码里的空格和空行更是字面内容。

纯函数逐字输出：

```text
hardbreak: raw_equal=False; inbox=616c70686120200a626574610a; canon=616c7068610a626574610a; dup_equal=True; dup='alpha\nbeta'
paragraph: raw_equal=False; inbox=706172612d6f6e650a0a706172612d74776f0a; canon=706172612d6f6e650a706172612d74776f0a; dup_equal=True; dup='para-one\npara-two'
fenced-spaces: raw_equal=False; inbox=6060600a6b657920200a6060600a; canon=6060600a6b65790a6060600a; dup_equal=True; dup='```\nkey\n```'
fenced-blank: raw_equal=False; inbox=6060600a610a0a620a6060600a; canon=6060600a610a620a6060600a; dup_equal=True; dup='```\na\nb\n```'
```

端到端逐字输出：

```text
01-hardbreak.md	C4_exact_duplicate	建议删	true	节点/canon-hardbreak.md
02-paragraph-break.md	C4_exact_duplicate	建议删	true	节点/canon-paragraph.md
01-fenced-trailing-spaces.md	C4_exact_duplicate	建议删	true	节点/canon-fenced-spaces.md
02-fenced-blank-line.md	C4_exact_duplicate	建议删	true	节点/canon-fenced-blank.md
```

这不属于“C4 不看标题”；根因是“精确重复”的比较形态本身有损。

### 2. HIGH｜唯一来源写在文件名时 C4 无护栏

文件名进入 item 于 [1802–1809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1802)，但 `nominate()` 只用它判断 `R{n}`；[未消化信号](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1504)完全不检查文件名。

复现命令同上，`--vault` 换成 `.../vault3`。逐字输出：

```json
{"name":"ISBN_978-7-111-54742-6.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/generic-a.md","basis":"归一化正文与 节点/generic-a.md 逐字相等（sha256 相同）","conflicts":[],"uncertain_reason":null}
{"name":"DOI_10.1000_xyz.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/generic-b.md","basis":"归一化正文与 节点/generic-b.md 逐字相等（sha256 相同）","conflicts":[],"uncertain_reason":null}
{"name":"source_https_example.test_article.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/generic-c.md","basis":"归一化正文与 节点/generic-c.md 逐字相等（sha256 相同）","conflicts":[],"uncertain_reason":null}
```

偏差 18 明确绑定 `dup_body()` 丢标题行，不能自动扩张成“文件名里的 ISBN/DOI/来源也允许丢”。

### 3. HIGH｜C3 仍删除可见井号内容

[标题内容判断](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:804)用 `lstrip(" \t#")`，没有真正分离 ATX opening/content/closing；[结构行判断](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:458)又把七个 `#` 当结构。

逐字输出：

```text
content=23202320230a substantive=False dup=''
content=232323232323230a substantive=False dup='#######'

03-hash-visible-heading.md	C3_empty_or_skeleton	建议删	true	-
04-seven-hashes.md	C3_empty_or_skeleton	建议删	true	-
```

`# # #` 的中间 `#` 是可见标题内容；`#######` 超过 ATX H6 上限，是普通文本，不是空标题模板。这是对 C3 用户裁决的实现偏差，不是要求推翻裁决。

## 三、决策忠实度

C4 标题裁决：**PARTIAL，已裁决连带不升级**。

实际边界是：仅丢围栏外、匹配 `_HEADING_RE` 的 ATX H1–H6 行，而且内部章节 H2 也丢；Setext、HTML、H7、围栏内 `#` 不丢。

复核逐字输出：

```text
05-setext-title.md	C6_undecided	拿不准	false
06-html-title.md	C6_undecided	拿不准	false
07-h1-title.md	C4_exact_duplicate	建议删	true
08-h6-title.md	C4_exact_duplicate	建议删	true
09-h7-not-heading.md	C6_undecided	拿不准	false
10-code-heading.md	C6_undecided	拿不准	false
```

历史裁决连带组：

```sh
jq -r '.items[] | [.criterion,.verdict,(.confident|tostring)] | @tsv' \
  /private/tmp/card-g56c-r9-history.KK3488/adjudicated_c4/out2/inbox-preview-_待处理.json |
  sort | uniq -c
```

```text
  10 C4_exact_duplicate	建议删	true
```

这 10 件含 U+3164/U+2800 和 8 个 `splitlines()` 标题构造，按偏差 18 只登记、不升级。

C3 五个点名面：**PASS；但安全边界 FAIL**。

```text
06-zero.md	C3_empty_or_skeleton	建议删	true
07-blank.md	C3_empty_or_skeleton	建议删	true
08-separators.md	C3_empty_or_skeleton	建议删	true
09-empty-heading.md	C3_empty_or_skeleton	建议删	true
10-quotes-only.md	C3_empty_or_skeleton	建议删	true
```

空围栏、空列表、全空值 frontmatter 等额外“一个字也没写”的结构面不是误伤；真正的第六类误伤是上一节的可见井号内容。

## 四、门强度

### 基线

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp \
backend/.venv/bin/pytest \
backend/tests/skills/test_g5_6_clear_inbox.py \
-q -p no:cacheprovider
```

逐字关键输出：

```text
collected 93 items
backend/tests/skills/test_g5_6_clear_inbox.py .......................... [ 27%]
...................................................................      [100%]
======================= 93 passed, 10 warnings in 6.57s ========================
```

所以最终态实际是 **93 门，不是 92 门**。

### 变异

只在 `/private/tmp/card-g56c-r9-mut.eB9MLG` 隔离副本执行：

```sh
python3 -B _bmad-output/审查/evidence-g56c/g56c_mutations.py \
  /private/tmp/card-g56c-r9-mut.eB9MLG
```

逐字结果：

```text
finally 还原后 sha256 = 1ec73ea2a0dd533f0ee2487c1807c09634b198f458ca1bcc7c7ff5484cea34f7 (与基线逐字节相同)

G56C_NEGATIVE_CONTROL: PASS （13/13 变异的实际失败集合等于预先声明集合）
```

13 轮均为 `rc=1`，失败数加通过数均为 93；当前实际是 **13 条变异，不是 12 条**。判据确实同时收 `FAILED/ERROR`，并要求失败集合相等、`rc==1`、源码恢复，见 [runner:251–265](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:251) 与 [304–307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:304)。

门仍为 **PARTIAL**：

```text
1_failed_92_skipped: failed=['test_gate'] ok=True
setup_ERROR_same_name: failed=['test_gate'] ok=True
extra_ERROR: failed=['test_gate', 'test_other'] ok=False
rc_2: failed=['test_gate'] ok=False
empty_mutations: allok=True count=0/0
```

因此：

- 额外 ERROR 和 `rc=2` 会被正确拒绝。
- 同名 setup ERROR 可代替目标断言失败，因果归属不独立。
- 不锁 collected/skipped，`1 failed + 92 skipped` 仍可 PASS。
- [最终聚合](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:328)不钉固定数量，清空清单会 `PASS（0/0）`。
- 当前真实 13 轮没有触发这些绕过；但 93 门未覆盖本轮三个 HIGH，且 [C4 正例门](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:292)主动锁定了“吸收空行/行尾空白”的错误 oracle。

## 五、措辞

结论：四类文档均非最终态干净快照，最高 **MEDIUM**。

- 生产文件：偏差 18 的 5→1、标题信息代价和 C3/C4 刻意不一致在 [207–213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:207)基本准确，但“标题”应限定为“围栏外 ATX H1–H6”。[766–773](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:766)称空行和 `rstrip` 是“无语义归一”，已被硬换行、段落及围栏代码反例证伪。另有：

```text
25: 当前登记九类
214: 本卡交付时的其余已知缺陷（第五轮终审登记，未修）
895-897: U+3164/U+2800 会落 C3；标题不算实质正文
1037-1039: C3 的可达面……只剩……三种
```

这些分别与当前⑩、已修注释/键名路径、标题裁决及当前性质口径矛盾。

- 生成 MD §四/§七：真实产物仍写：

```text
- **01-fenced-trailing-spaces.md** · 逐字相同 → 正本 `节点/canon-fenced-spaces.md`
- 建议删有两个出口……①……⑧……
  ⚠️ 这八条是**已知形态的登记表**……
```

§四的 raw bytes 实际不同；§七生成点 [2186–2195](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2186)漏⑨任意非空/未知空值键、⑩被剥内容、C3 性质边界和偏差 18 代价。

- UAT：C3 的性质描述在 [125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:125)、[240–243](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:240)已正确改成非穷举；偏差 18 在 [251–253](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:251)基本准确。但同一文件仍并存 `88/8/3`、`92/12` 多套数字，且 [254–255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:254)把已修多行 HTML/YAML 注释写成未修。

- README/runner：README [144–147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:144)已写明不应数“剩几种”，但 [290–292](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:290)仍写“五种”，[453–468](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:453)又写 `92/12` 和“四处已全部改”。runner [第 2 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:2)仍称“八条回退变异”。

## 六、登记

当前允许读取的 7 个目标文件均与给定 diff 目标 blob 匹配：

```text
881100a1642e738acc16dd36b86d1f976d2312eb
94bb29f1fa32daa0bf20fd61ec591cb529613441
c07f60c1a06b368dc686f32fed5ac2923ddc2b37
14127ec3591a6a8899f55af20a67188aeeef368c
6032ec3013ef6da39c7342eeb353472c2a758a52
2f3942de2356b0a3b249c8cee4585467c62a9bbf
e2eaf8d467f992d11b6ae959c008351a95419722
```

| ID | 级别 | 状态 | 登记 |
|---|---:|---|---|
| R9-H1 | HIGH | OPEN | C4 的 `rstrip`/空行删除把 Markdown 与围栏代码的有语义差异压成“精确重复” |
| R9-H2 | HIGH | OPEN | 文件名中的 ISBN/DOI/来源不进护栏，重复正文时确定删除且无 conflict |
| R9-H3 | HIGH | OPEN | C3 把可见 `#` 标题内容及 H7 普通文本判成空骨架 |
| R9-M1 | MEDIUM | OPEN | 93 门包含错误 C4 oracle，且未覆盖上述三条 |
| R9-M2 | MEDIUM | OPEN | 生产、MD、UAT、README 的当前状态与数字仍互斥或过宽 |
| R9-L1 | LOW | OPEN | 变异清单可 0/0 真空 PASS |
| R9-L2 | LOW | OPEN | runner 不锁 collected/skipped，同名 setup ERROR 可替代目标断言 |
| R9-P1 | PASS_WITH_LIMITS | CLOSED | 84 件重建历史危险根因全部安全；原 105 件缺 exact bytes，不能冒充逐字重放 |
| R9-P2 | PASS_WITH_LIMITS | CLOSED | 两项产品裁决按其精确语法实现；其代价不升级 |

判据形状结论：R9-H1、R9-H2 不是再补一条样本即可闭合的问题。C4 当前把“正文的有损投影相等”当作“整件材料可删除”：投影既抹掉语义空白，又不覆盖文件名。继续枚举 hard-break、ISBN、DOI 只会重演前八轮；需要重新定义 C4 的证据域与允许忽略的字段。R9-H3 则是可局部修复的 Markdown 标题/结构解析错误。

BLOCKER/HIGH 清零: 否
