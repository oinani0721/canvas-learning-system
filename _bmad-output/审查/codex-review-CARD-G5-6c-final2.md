裁定：`57712c59` 不通过最终清零。历史未获产品裁决豁免的反例均闭合，C1/C2 未扩面，C3 五种删除面仍可达；但新构造发现 1 条 HIGH：frontmatter 行尾 YAML 注释中的唯一来源会被清洗器静默丢弃，C3、C4 两个出口均重新出现 `建议删 + confident=true`。

## 一、历史反例复核

复跑命令：

```sh
for g in \
  g1_round1 g2_round2 g3_u2063_family g4_round4_matrix \
  g5_splitlines g6_comments g7_old_regressions g8_heading_spaces \
  g9_c4_history g10_more_invisible g11_more_comments g12_nested_c4 \
  g13_u2063_guard g14_visual_cross
do
  python3 -B canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
    --vault /private/tmp/card-g56c-r6-history.ji6dnd/$g/vault \
    --now 2026-09-01T00:00:00+08:00 \
    --out-dir /private/tmp/card-g56c-r6-history.ji6dnd/$g/out \
    --batch-size 10
done
```

105 件汇总，逐字输出：

```json
{
  "groups": 14,
  "total_items": 105,
  "delete_true": 14,
  "c6_false": 91
}
```

完整历史输出如下，列依次为 `group / name / criterion / verdict / confident / exact_duplicate_of`：

<details>
<summary>展开 105 件逐字 TSV</summary>

```text
g10_more_invisible	01-by双下划线.md	C6_undecided	拿不准	false	null
g10_more_invisible	02-by破折号.md	C6_undecided	拿不准	false	null
g10_more_invisible	03-U200C.md	C6_undecided	拿不准	false	null
g10_more_invisible	04-U200D.md	C6_undecided	拿不准	false	null
g10_more_invisible	05-U2060.md	C6_undecided	拿不准	false	null
g10_more_invisible	06-UFEFF.md	C6_undecided	拿不准	false	null
g10_more_invisible	07-U00AD.md	C6_undecided	拿不准	false	null
g10_more_invisible	08-U200B词间.md	C6_undecided	拿不准	false	null
g10_more_invisible	09-U200C-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g10_more_invisible	10-中文U200D-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g11_more_comments	01-DOI注释-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g11_more_comments	02-generated注释-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g11_more_comments	03-多行注释-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g11_more_comments	04-嵌套注释-C4.md	C6_undecided	拿不准	false	null
g11_more_comments	05-行内相邻-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g11_more_comments	06-多注释.md	C6_undecided	拿不准	false	null
g11_more_comments	07-普通注释.md	C6_undecided	拿不准	false	null
g11_more_comments	08-空多行注释.md	C3_empty_or_skeleton	建议删	true	null
g11_more_comments	09-围栏精确.md	C4_exact_duplicate	建议删	true	节点/围栏正本.md
g11_more_comments	10-围栏独有.md	C6_undecided	拿不准	false	null
g12_nested_c4	嵌套注释-C4.md	C6_undecided	拿不准	false	节点/nested-canonical.md
g13_u2063_guard	01-u2063英文.md	C6_undecided	拿不准	false	null
g13_u2063_guard	02-u2063中文.md	C6_undecided	拿不准	false	null
g13_u2063_guard	03-u2063-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g14_visual_cross	01-U3164-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md
g14_visual_cross	02-U2800-C3.md	C6_undecided	拿不准	false	null
g1_round1	01-NBSP.md	C6_undecided	拿不准	false	null
g1_round1	02-GPT4声明.md	C6_undecided	拿不准	false	null
g1_round1	03-DOI来源.md	C6_undecided	拿不准	false	null
g1_round1	04-长模型名.md	C6_undecided	拿不准	false	null
g1_round1	05-英文冒号.md	C6_undecided	拿不准	false	null
g1_round1	06-英文词间零宽.md	C6_undecided	拿不准	false	null
g1_round1	07-重复DOI.md	C6_undecided	拿不准	false	null
g1_round1	08-重复URL.md	C6_undecided	拿不准	false	null
g1_round1	09-ISBN.md	C6_undecided	拿不准	false	null
g1_round1	10-title-ISBN.md	C6_undecided	拿不准	false	null
g2_round2	01-by下划线.md	C6_undecided	拿不准	false	null
g2_round2	02-by下划线-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g2_round2	03-拆generated.md	C6_undecided	拿不准	false	null
g2_round2	04-拆by.md	C6_undecided	拿不准	false	null
g2_round2	05-拆生成.md	C6_undecided	拿不准	false	null
g2_round2	06-拆by-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g2_round2	07-title唯一.md	C6_undecided	拿不准	false	null
g2_round2	08-alias馆藏.md	C6_undecided	拿不准	false	null
g2_round2	09-date原始.md	C6_undecided	拿不准	false	null
g2_round2	10-tags唯一.md	C6_undecided	拿不准	false	null
g3_u2063_family	01-U2063.md	C6_undecided	拿不准	false	null
g3_u2063_family	02-U200E.md	C6_undecided	拿不准	false	null
g3_u2063_family	03-U200F.md	C6_undecided	拿不准	false	null
g3_u2063_family	04-U061C.md	C6_undecided	拿不准	false	null
g3_u2063_family	05-U034F.md	C6_undecided	拿不准	false	null
g3_u2063_family	06-UFE0F.md	C6_undecided	拿不准	false	null
g3_u2063_family	07-U2062.md	C6_undecided	拿不准	false	null
g3_u2063_family	08-U180E.md	C6_undecided	拿不准	false	null
g3_u2063_family	09-U202E.md	C6_undecided	拿不准	false	null
g4_round4_matrix	01-Cf-U2064.md	C6_undecided	拿不准	false	null
g4_round4_matrix	02-Cf-U1BCA0-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g4_round4_matrix	03-Cf-UE0001.md	C6_undecided	拿不准	false	null
g4_round4_matrix	04-Mn-U0301.md	C6_undecided	拿不准	false	null
g4_round4_matrix	05-Mn-U1AB0-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g4_round4_matrix	06-Mn-UE0100.md	C6_undecided	拿不准	false	null
g4_round4_matrix	07-Cc-U0001.md	C6_undecided	拿不准	false	null
g4_round4_matrix	08-Zs-U200A.md	C6_undecided	拿不准	false	null
g4_round4_matrix	09-Lo-U3164.md	C6_undecided	拿不准	false	null
g4_round4_matrix	10-So-U2800-C4.md	C4_exact_duplicate	建议删	true	节点/库内正本.md
g5_splitlines	01-U000B-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	02-U000C-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	03-U001C-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	04-U0085-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	05-U001D-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	06-U001E-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	07-U2028-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g5_splitlines	08-U2029-C4.md	C4_exact_duplicate	建议删	true	节点/canon-1.md
g6_comments	01-URL单行.md	C6_undecided	拿不准	false	null
g6_comments	02-DOI单行.md	C6_undecided	拿不准	false	null
g6_comments	03-ISBN单行.md	C6_undecided	拿不准	false	null
g6_comments	04-generated单行.md	C6_undecided	拿不准	false	null
g6_comments	05-多行来源.md	C6_undecided	拿不准	false	null
g6_comments	06-fm-YAML注释.md	C6_undecided	拿不准	false	null
g6_comments	07-URL注释-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g6_comments	08-嵌套注释.md	C6_undecided	拿不准	false	null
g6_comments	09-空注释.md	C3_empty_or_skeleton	建议删	true	null
g6_comments	10-围栏注释正文.md	C6_undecided	拿不准	false	null
g7_old_regressions	01-B3四反引号.md	C6_undecided	拿不准	false	null
g7_old_regressions	02-H1空host端口.md	C6_undecided	拿不准	false	null
g7_old_regressions	03-H1空host用户.md	C6_undecided	拿不准	false	null
g7_old_regressions	04-H2版权话题.md	C6_undecided	拿不准	false	null
g7_old_regressions	05-H2由字话题.md	C6_undecided	拿不准	false	null
g7_old_regressions	06-H2评测话题.md	C6_undecided	拿不准	false	null
g7_old_regressions	07-H3裸URL行.md	C6_undecided	拿不准	false	null
g7_old_regressions	08-H4第三份.md	C4_exact_duplicate	建议删	true	归档/乙本.md
g8_heading_spaces	01-NBSP.md	C6_undecided	拿不准	false	null
g8_heading_spaces	02-EM.md	C6_undecided	拿不准	false	null
g8_heading_spaces	03-IDEOGRAPHIC.md	C6_undecided	拿不准	false	null
g8_heading_spaces	04-NNBSP.md	C6_undecided	拿不准	false	null
g8_heading_spaces	05-OGHAM.md	C6_undecided	拿不准	false	null
g8_heading_spaces	06-三空格NBSP.md	C6_undecided	拿不准	false	null
g8_heading_spaces	07-无分隔.md	C6_undecided	拿不准	false	null
g8_heading_spaces	08-TAB标题.md	C6_undecided	拿不准	false	null
g8_heading_spaces	09-空格标题.md	C6_undecided	拿不准	false	null
g9_c4_history	01-重复DOI-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g9_c4_history	02-重复URL-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g9_c4_history	03-ISBN-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g9_c4_history	04-title独有-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
g9_c4_history	05-alias馆藏-C4.md	C6_undecided	拿不准	false	节点/库内正本.md
```

</details>

14 件 `建议删 + true` 的解释：

- 10 件是产品裁决②明确接受的 C4 面：U+3164、U+2800，以及 U+000B/U+000C/U+001C/U+0085/U+001D/U+001E/U+2028/U+2029 八种 `splitlines` 形态。
- 4 件是正向控制：空单行注释、空多行注释、真实 H4 精确重复、围栏字面量真实精确重复。
- 除以上裁决面和正向控制外，历史危险反例重新出现确定删除的数量为 `0`。

15 道历史定向门：

```text
...............                                                          [100%]
15 passed, 10 warnings in 1.22s
```

### C1/C2 与 `969844ef` 对比

在 `/private/tmp` 反向应用所给 diff 重建开工版：

```sh
sed -n '2122,$p' \
  _bmad-output/审查/CARD-G5-6c-diff-969844ef-to-57712c59.txt |
  patch -R -p1 \
    -d /private/tmp/card-g56c-r6-history.ji6dnd/baseline-root
```

输出：

```text
patching file 'canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py'
```

哈希：

```text
baseline=4b873b61f588c7aab56b19374a13f183a9e5433f9efdd16ff9be3f0eaafcb7fd
final=77ae58dfdbeeaaafcb3324a25e8d2c7b84412b429f8f6e795037a31fd01f8673
```

逐件对跑输出：

```text
c1_matrix_old_hits=['01-lower.md', '02-upper-scheme.md', '03-quoted-comment.md', '05-first-valid.md', '09-space-before-colon.md']
c1_matrix_final_hits=['01-lower.md', '02-upper-scheme.md', '03-quoted-comment.md', '05-first-valid.md', '09-space-before-colon.md']
c1_matrix_hit_set_equal=True
c1_matrix_hit_payload_equal=True

c2_matrix_old_hits=['01-deep-cn.md', '02-deep-en.md', '03-ai-cn.md', '04-ai-en.md', '05-case-tab.md', '06-punct.md']
c2_matrix_final_hits=['01-deep-cn.md', '02-deep-en.md', '03-ai-cn.md', '04-ai-en.md', '05-case-tab.md', '06-punct.md']
c2_matrix_hit_set_equal=True
c2_matrix_hit_payload_equal=True
```

相关 C1/C2 函数和常量的 AST 对比：

```text
_is_primary_source_url_source_equal=True
frontmatter_span_source_equal=True
head_window_source_equal=True
_norm_ai_line_source_equal=True
_find_marker_pos_source_equal=True
find_ai_marker_source_equal=True
HEAD_SCAN_LINES_equal=True
AI_MARKERS_equal=True
_MARKER_BOUNDARY_PUNCT_equal=True
URL_RE_equal=True
frontmatter_map_cases_equal=True
```

判定：C1/C2 命中集合和命中 payload 均与开工版完全一致，护栏加宽没有扩大确定提名面。

## 二、新构造

### R6-H1 — HIGH：行尾 YAML 注释中的唯一来源被静默丢弃

最小复现：

```sh
repro=/private/tmp/card-g56c-inline-comment.mor4bW
mkdir -p "$repro/vault/_待处理" "$repro/vault/节点" "$repro/vault/原白板" "$repro/out"

printf '%s' '---
title: "" # source: https://inline.example/only
---
' > "$repro/vault/_待处理/C3-inline.md"

printf '%s' '唯一正文与库内逐字相同。
第二行也相同。
' > "$repro/vault/节点/库内正本.md"

printf '%s' '---
title: "" # source: https://inline.example/only
---
唯一正文与库内逐字相同。
第二行也相同。
' > "$repro/vault/_待处理/C4-inline.md"

python3 -B \
  canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault "$repro/vault" \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir "$repro/out" \
  --batch-size 10
```

逐字 CLI 输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-inline-comment.mor4bW/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-inline-comment.mor4bW/out/inbox-preview-_待处理.md
  _待处理/ 共 2 件，本批全取（2 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 2 件 · 拿不准 0 件 · 建议删 2 件
```

```sh
jq -c '.items[] |
  {name,criterion,verdict,confident,exact_duplicate_of,uncertain_reason,basis}' \
  "$repro/out/inbox-preview-_待处理.json"
```

逐字输出：

```json
{"name":"C3-inline.md","criterion":"C3_empty_or_skeleton","verdict":"建议删","confident":true,"exact_duplicate_of":null,"uncertain_reason":null,"basis":"剥离 frontmatter / HTML 注释后实质正文 0 字符（56 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）"}
{"name":"C4-inline.md","criterion":"C4_exact_duplicate","verdict":"建议删","confident":true,"exact_duplicate_of":"节点/库内正本.md","uncertain_reason":null,"basis":"归一化正文与 节点/库内正本.md 逐字相等（sha256 相同）"}
```

根因动态取证：

```sh
python3 -B -c '
import importlib.util
p="canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py"
s=importlib.util.spec_from_file_location("ip",p)
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)
fm=["title: \"\" # source: https://inline.example/only"]
print("frontmatter_pairs=",m.frontmatter_pairs(fm))
print("unparsed_fm=",[x.strip() for x in fm if x.strip() and not x.strip().startswith("#") and not m._FM_KEY_RE.match(x)])
print("fm_comment_lines=",[x.strip() for x in fm if x.strip().startswith("#") and x.strip("# \t")])
'
```

输出：

```text
frontmatter_pairs= [('title', '')]
unparsed_fm= []
fm_comment_lines= []
```

根因链：

- [`_clean_fm_value()` 第 593 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:593) 用 `\s+#.*$` 丢掉整段注释。
- [`frontmatter_pairs()` 第 620 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:620) 只留下空 `title`。
- [`fm_comment_lines` 第 1284 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1284) 只认整行以 `#` 开头的 YAML 注释。
- 因此 [`unknown_value_pairs` 第 1413 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1413) 和信号⑩的 [`commented_out` 第 1418 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:1418) 均为空，C3/C4 护栏同时失效。
- 现有 inline 门只测 `source: URL # 普通说明`，URL 本身仍是值；没有测试“空值后的注释才是唯一来源”，见 [test_g5_6_clear_inbox.py:571](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:571)。整行 YAML 注释门见 [test_g5_6_clear_inbox.py:2486](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/backend/tests/skills/test_g5_6_clear_inbox.py:2486)。

这是与第五轮 YAML 注释 HIGH 同源的保护面缺口：解析器主动丢弃非空来源内容，同时两个删除出口都给出确定删除，故定为 HIGH。它不属于“C4 不看标题”的产品裁决面。

扩展 7 件矩阵：

```text
01-inline-url-c3.md	C3_empty_or_skeleton	建议删	true	-
02-inline-isbn-c3.md	C3_empty_or_skeleton	建议删	true	-
03-inline-url-c4.md	C4_exact_duplicate	建议删	true	节点/canonical.md
04-full-line-yaml.md	C6_undecided	拿不准	false	-
05-multiline-html.md	C6_undecided	拿不准	false	-
06-empty-inline-comment.md	C3_empty_or_skeleton	建议删	true	-
07-unquoted-empty-comment.md	C6_undecided	拿不准	false	-
```

这同时验证：

- 多行闭合 HTML 注释和整行 YAML 注释的第五轮修复有效。
- 围栏内独有内容为 C6；真实围栏精确重复才为 C4。
- 缺口集中在“成对空引号值 + 行尾非空 YAML 注释”；DOI/ISBN/普通说明同样可穿透，并非 URL 特例。

## 三、C3 可达面

命令：

```sh
python3 -B canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  --vault /private/tmp/card-g56c-r6-main/c3-five/vault \
  --now 2026-09-01T00:00:00+08:00 \
  --out-dir /private/tmp/card-g56c-r6-main/c3-five/out \
  --batch-size 10
```

输出：

```text
✓ preview 已生成（只读引擎, 未动 vault 任何既有文件）: /private/tmp/card-g56c-r6-main/c3-five/out/inbox-preview-_待处理.json / /private/tmp/card-g56c-r6-main/c3-five/out/inbox-preview-_待处理.md
  _待处理/ 共 10 件，本批全取（10 件）。 Sleeping/ 未建立，无睡眠台账。
  本批 10 件 · 拿不准 3 件 · 建议删 7 件
```

逐件输出：

```text
01-zero-byte.md	C3_empty_or_skeleton	建议删	true	0 字节空文件
02-blank-lines.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（4 字节文件：标题 0 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
03-separator.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（12 字节文件：标题 0 行、纯结构行 3 行、代码围栏 0 行、其余皆空行或注释）
04-empty-heading.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（7 字节文件：标题 2 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
05-only-quotes.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（8 字节文件：标题 0 行、纯结构行 3 行、代码围栏 0 行、其余皆空行或注释）
06-table-separator.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（16 字节文件：标题 0 行、纯结构行 1 行、代码围栏 0 行、其余皆空行或注释）
07-empty-frontmatter.md	C3_empty_or_skeleton	建议删	true	剥离 frontmatter / HTML 注释后实质正文 0 字符（24 字节文件：标题 1 行、纯结构行 0 行、代码围栏 0 行、其余皆空行或注释）
08-text-heading.md	C6_undecided	拿不准	false	无机械判据可施加
09-u3164-heading.md	C6_undecided	拿不准	false	无机械判据可施加
10-u2800-heading.md	C6_undecided	拿不准	false	无机械判据可施加
```

判定：

- 用户裁决规定的五种面全部仍可达：0 字节、纯空行、纯分隔线、空标题模板、只有引用符。
- 表格分隔线属于纯分隔线同族；空 frontmatter/空标题仍是空骨架，不是新增删除语义。
- 普通文字标题、U+3164、U+2800 标题均为 C6，裁决①在 C3 侧成立。
- C3 没有判死。

合理但语义为空的 YAML 形态：

```text
01-empty-list.md	C6_undecided	拿不准	false
02-empty-map.md	C6_undecided	拿不准	false
03-null.md	C6_undecided	拿不准	false
04-tilde.md	C6_undecided	拿不准	false
05-spaced-list.md	C6_undecided	拿不准	false
06-double-quoted-empty.md	C3_empty_or_skeleton	建议删	true
07-bare-empty.md	C3_empty_or_skeleton	建议删	true
08-empty-html.md	C3_empty_or_skeleton	建议删	true
09-empty-multiline-html.md	C3_empty_or_skeleton	建议删	true
10-empty-yaml-comment.md	C3_empty_or_skeleton	建议删	true
```

`[]`、`{}`、`null`、`~`、`[ ]` 被原始文本扫描当作非空值，形成安全方向的少删。定为 MEDIUM 产品边界，不是毁损风险；若坚持“五种面”而非完整 YAML 语义，这个取舍可接受，但应写入边界。

## 四、门强度

### 91 门

命令：

```sh
env TMPDIR=/private/tmp \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  backend/.venv/bin/pytest \
  -c /dev/null -p no:cacheprovider \
  backend/tests/skills/test_g5_6_clear_inbox.py \
  -q --basetemp=/private/tmp/card-g56c-r6-pytest
```

逐字结果：

```text
........................................................................ [ 79%]
...................                                                      [100%]
91 passed, 10 warnings in 6.06s
```

AST 计数：

```text
module_level_test_defs= 91
unique_test_names= 91
duplicates= []
mutation_count= 11
unique_expected_gate_names= 13
expected_missing_from_suite= []
```

结论：91 门确实收集并全绿；但 11 个变异只覆盖 13 个唯一门名，不能表述为“91 门逐门均经变异证明承重”。新 HIGH 也直接证明 91 门缺少该 frontmatter 边界。

### 当前 11 条变异

在 `/private/tmp` 的逐字节副本运行，未原地改 worktree。逐字摘要：

```text
M-NBSP       rc=1  2 failed, 89 passed  actual==expected  restore==baseline
M-CLAIMBOUND rc=1  1 failed, 90 passed  actual==expected  restore==baseline
M-ZEROWIDTH  rc=1  2 failed, 89 passed  actual==expected  restore==baseline
M-GENSIGNAL  rc=1  3 failed, 88 passed  actual==expected  restore==baseline
M-SRCALIAS   rc=1  1 failed, 90 passed  actual==expected  restore==baseline
M-DOIVAL     rc=1  2 failed, 89 passed  actual==expected  restore==baseline
M-PAIRS      rc=1  1 failed, 90 passed  actual==expected  restore==baseline
M-FALLBACK   rc=1  2 failed, 89 passed  actual==expected  restore==baseline
M-INVISENUM  rc=1  1 failed, 90 passed  actual==expected  restore==baseline
M-COMMENT    rc=1  2 failed, 89 passed  actual==expected  restore==baseline
M-HEADING    rc=1  1 failed, 90 passed  actual==expected  restore==baseline

finally 还原后 sha256 = 77ae58dfdbeeaaafcb3324a25e8d2c7b84412b429f8f6e795037a31fd01f8673 (与基线逐字节相同)

G56C_NEGATIVE_CONTROL: PASS （11/11 变异的实际失败集合等于预先声明集合）
```

已登记形态的信号归属断言是承重的；例如关闭注释信号、全量 pairs、AI 结构信号都会让对应 reason 门变红。但 inline YAML 注释根本不进入这些集合，因此门覆盖仍为 PARTIAL。

### runner 绕过面

[`g56c_mutations.py:220`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:220) 同时收集 `FAILED`/`ERROR`，[`第 276 行`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/g56c_mutations.py:276) 要求集合相等且 `rc == 1`。多红、少红、collection error 的 rc 2/3/4/5 均不能假通过。

但它丢失失败类型。同名测试由 assertion FAIL 退化成 setup ERROR，仍能通过：

```sh
python3 -B -c '
out="ERROR tests/skills/test_g5_6_clear_inbox.py::test_source_inside_closed_html_comment_blocks_deletion - setup failed\n"
failed={ln.split("::")[1].split(" ")[0].strip() for ln in out.splitlines()
        if (ln.startswith("FAILED ") or ln.startswith("ERROR ")) and "::" in ln}
expected={"test_source_inside_closed_html_comment_blocks_deletion"}
rc=1
print("parsed=",sorted(failed))
print("expected=",sorted(expected))
print("runner_ok=",failed == expected and rc == 1)
'
```

输出：

```text
parsed= ['test_source_inside_closed_html_comment_blocks_deletion']
expected= ['test_source_inside_closed_html_comment_blocks_deletion']
runner_ok= True
```

另有两项 MEDIUM 证据缺口：

- runner 没断言每轮 `collected/executed == 91`；未来发生 skip/deselect 时，只要预期红集不变仍可能通过。
- 文件头称 expected 是独立预先写死、不是从输出反抄；但第 78–84、147–152 行明确记录 `M-ZEROWIDTH`、`M-FALLBACK` 都在首跑后按实际红集改过。当前集合是静态的，但“全部有独立先验来源”只能判 PARTIAL。

## 五、措辞

取证命令形态：

```sh
nl -ba canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
nl -ba _bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md
nl -ba _bmad-output/审查/evidence-g56c/README-取证说明.md
```

### 生产文件头

| 位置 | 逐字关键原文 | 判定 |
|---|---|---|
| [24–25](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:24) | `当前登记九类；数字随轮次增长，此处不再写死` | FAIL · MEDIUM：已有⑩，且“九类”本身就是写死。 |
| [40–46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:40) | `已发现项的登记，不是穷尽性证明` | PASS。 |
| [127–174](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:127) | 共用护栏只登记①–⑨；后文仍说`白名单本身也可能收窄得不对` | PARTIAL · MEDIUM：漏⑩，并残留已取消白名单措辞。 |
| [183–205](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:183) | `⑨白名单兜底`、`不在白名单且值非空` | FAIL · LOW：实现已改为任意非空值。 |
| [207–213](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:207) | `C4「精确重复」不看标题`、用户裁决不改 | PASS。 |
| [214–218](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:214) | `多行闭合 HTML 注释、frontmatter 里的 YAML 注释……未修` | FAIL · MEDIUM：两条已修；splitlines 也没限定为 C4/裁决②。 |
| [851–858](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:851) | `仍会落 C3 建议删`、`现在标题不算实质正文` | FAIL · MEDIUM：与当前标题裁决实现直接矛盾。 |

### 人读 MD §七

| 位置 | 原文/缺口 | 判定 |
|---|---|---|
| [2096–2100](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2096) | 只说逐字重复，未披露归一化丢标题 | PARTIAL · MEDIUM。 |
| [2102–2111](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2102) | `这八条是已知形态的登记表` | FAIL · MEDIUM：漏⑨和⑩。 |
| [2090–2125](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2090) | 整节未登记裁决①五种 C3 面、裁决②/C4 标题偏差及偏差19当前状态 | FAIL · MEDIUM。 |
| [2113–2121](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py:2113) | 已登记/未登记 AI 形态的范围限定 | PASS。 |

### 验收单

[UAT](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/验收单/UAT-CARD-G5-6-clear-inbox只读盘点提名preview-2026-08-31.md:1) 的核心“到顶不合并”仍正确，但不是当前最终态快照：

- 第 3–5 行仍写 v5/v6、自称“又一轮无独立复核”；已有第四、第五和本轮审查。FAIL · MEDIUM。
- 第 58–67、94–100、145、203–213 行仍写 `88` 门、`8/8`、`3 条`、总计 `38`；当前为 `91` 门、`11/11`、旧 29 + 当前 11 = 40。FAIL · MEDIUM。
- 第 125 行标题裁决和五种 C3 面准确。PASS。
- 第 126、241–243 行 C4 不跟进/偏差18准确。PASS。
- 第 244–245 行仍说多行注释、YAML 注释未修，并漏空键名 DOI/ISBN。FAIL · MEDIUM。
- 第 215–235 行写“17 条偏差”“九类信号”“C3 只剩三种”，当前应为 19 条、含⑩、五种面。FAIL · MEDIUM。

### 取证 README

实际文件已有 §10，因此“README 第 1–9 节记录全过程”本身已陈旧。

- [35–42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:35)：仍称三条、各 `1 failed, 81 passed`；当前 11/91。FAIL · MEDIUM。
- [56–73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:56)：把“本版”绑定到旧生产 hash `cba6e464…`，不能证明当前 `77ae58…` 字节。PARTIAL · MEDIUM。
- [262–285](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:262)：标题裁决五种面准确，但“BLOCKER 随之关闭”没限定 C3，已被第五轮 C4 反例证伪。PARTIAL · MEDIUM。
- [306–342](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:306)：正确收窄为只关闭 C3，并登记裁决②。PASS。
- [344–371](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v6-inbox/_bmad-output/审查/evidence-g56c/README-取证说明.md:344)：同节先写偏差19“未修”，后又写两条 HIGH 已修；370–371 对 splitlines 的 C4 限定准确，但段内状态互相冲突。PARTIAL · MEDIUM。
- 第 333–338 行 `5/5 → 1/5` 在限定取证包内没有逐件命令和原始输出，只能视为历史自报。PARTIAL · LOW。
- 新 HIGH 又证伪第 358 行“信号⑩覆盖面补全”在一般 YAML 注释面上的宽表述。

措辞轨最高级别为 MEDIUM；没有仅凭文档措辞单独成立的 BLOCKER/HIGH，但四份面向归档的说明都不是最终态干净快照。

## 六、登记

当前对象确认：

```sh
git rev-parse --short=8 HEAD
shasum -a 256 \
  canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py \
  backend/tests/skills/test_g5_6_clear_inbox.py \
  _bmad-output/审查/evidence-g56c/g56c_mutations.py \
  _bmad-output/审查/evidence-g56c/g56c_mutations_output.txt
```

逐字输出：

```text
57712c59
77ae58dfdbeeaaafcb3324a25e8d2c7b84412b429f8f6e795037a31fd01f8673  canvas-vault/.claude/skills/clear-inbox/scripts/inbox_preview.py
54a6776f12f3453787e717e0e19f2010fa57fb0e035803a2d210c1b74cbf1be0  backend/tests/skills/test_g5_6_clear_inbox.py
6d27d6d6c736f0d7a9f5927a6b6840864ee945310ca4afdf1e612d75ca04a4e8  _bmad-output/审查/evidence-g56c/g56c_mutations.py
75810642f4aae7ae91f1950ff316e43bec9060a6674202031cd0e809928d6bd9  _bmad-output/审查/evidence-g56c/g56c_mutations_output.txt
```

登记表：

| ID | 级别 | 状态 | 内容 |
|---|---:|---|---|
| R6-H1 | HIGH | OPEN | 成对空引号值后的行尾 YAML 注释被清洗器丢弃，C3/C4 双出口确定删除。 |
| R6-M1 | MEDIUM | OPEN | runner 合并 FAILED/ERROR 类型，且不锁每轮 collected/executed=91。 |
| R6-M2 | MEDIUM | OPEN | 11 个变异只覆盖 13/91 门；两组 expected 曾按实跑红集修订，独立先验声明过宽。 |
| R6-M3 | MEDIUM | OPEN | 生产头、MD §七、UAT、README 均有终态陈旧或互相矛盾的归档措辞。 |
| R6-M4 | MEDIUM | 已知边界 | YAML 语义空值 `[]/{}/null/~` 落 C6；安全方向少删，C3 本身未判死。 |
| R6-L1 | LOW | OPEN | 整行 YAML 注释的 `uncertain_reason` 仍称其为“HTML 注释”。 |

最终归档裁定：

- BLOCKER：0。
- HIGH：1。
- 历史未获裁决豁免的危险反例：全部闭合。
- C1/C2：与 `969844ef` 命中面一致。
- C3：五种产品裁决面均可达，未判死。
- `91 passed` 与 `11/11` 不能覆盖本轮新 HIGH。
- `57712c59` 只能按“第六轮未清零／到顶不合并”归档，不能按验收通过或最终清零归档。

BLOCKER/HIGH 清零: 否


