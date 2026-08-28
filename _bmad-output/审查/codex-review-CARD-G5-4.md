# Codex 审查存档 — CARD-G5-4（round-1）

> **状态**: round-1 分析完成、终稿输出被 Codex 平台内容过滤器误拦（`ERROR: This content was flagged for possible cybersecurity risk`，
> 与 MEMORY `reference_codex_exec_gotchas` 记录的已知误拦一致——审阅提示词含"对抗/篡改"类词汇触发）。
> 本文档发现清单由 round-1 完整 transcript（193,604 tokens，`tasks/bo3hzlzed.output`，6932 行）提取，
> 每条附 transcript 内的复现证据位置；round-2 以中性措辞重跑做修复验证（见 codex-review-CARD-G5-4-round2.md）。

## Round-1 发现与处置（全部处置完毕）

| # | 级别 | 发现 | 复现证据（transcript） | 处置 |
|---|---|---|---|---|
| F1 | HIGH | fallback 不解析 `derived-from` 作来源锚点 → 同一 vault 两模式信号分叉：真 `build_manifest` 下 source_coverage 2/3 / unsourced 0/2，fallback 却 1/3 / 1/2（假"无来源"警报） | L6626-6650：Codex 用真 build_manifest 复现 `actual_manifest_DerivedC_relation={'type':'derived_from',...}`，两模式数值并排打印 | `_ledger_from_local` 抄录 `derived-from`/`derived_from` → `relation_target`+`relation_type`（对齐 manifest `_node_relation` 退路分支）；新增回归锁 `test_cross_mode_signal_consistency_real_manifest`（用真 build_manifest 断言两模式全等） |
| F2 | BLOCKER 候选 | 信号行前插未闭合 `<!--` → 渲染视图隐藏其后内容，verifier 剥闭合注释后照常看见隐藏行 → PASS（可见文本与校验文本分叉） | L6563-6584：`unclosed-html-comment-before-signals exit=0 VERIFY PASS` 实测复现；L6585 "Classifying card verifier failure as blocker" | verifier 剥闭合注释后正文残留 `<!--` 即 FAIL；SKILL.md 规则 10 同步；回归锁 `test_verify_unclosed_html_comment_fails` |
| F3 | HIGH | 无据信号行可夹带编造的 X/N 计数不被拦（"无据"子串在场即放行） | L4019-4023 "Detecting verifier bypass on no-data availability / Identifying signal number tampering vulnerabilities" | 无据行命中 `\d+/\d+` 或年龄标准格式 → FAIL；回归锁 `test_verify_nodata_line_with_numbers_fails` |
| F4 | MEDIUM | `source_note: null`（YAML null 字面量经正则抄录成字符串 "null"）被算成来源锚点 | L6650 前后 "Inspecting source_note parsing bug / Testing source_note null handling" | `_strip_note_ref` 把 null/~/none 字面量按空处理；manifest 透传侧同样过 `_strip_note_ref` 归一（幂等）；回归锁 `test_null_literal_provenance_not_counted` |
| F5a | MEDIUM | scan JSON `signals` 键存在但非 dict → verifier 静默跳过绑定（fail-open） | L4021 "Exposing verifier skip on malformed signals" | 键存在而形状非对象 → FAIL；键完全缺失才走旧 JSON 兼容；回归锁 `test_verify_signals_key_wrong_shape_fails` |
| F5b | MEDIUM | tips 文本 200 字截断（M9 口径）可把仅在 200 字后不同的两条 tips 折成假重复 | L6917 "Identifying false duplicates from tip truncation" | 诚实口径：`duplicate_accumulation.note` 显式声明"200字截断后全等"（截断本身是 C5 M9 既有净化纪律，不回退） |
| F6 | MEDIUM | 手搓测试 manifest 漏 DerivedC 的 relation 字段，与真 build_manifest 形状不符（fixture 失真） | L6587 "Identifying test manifest inconsistency" + 真 manifest 对照输出 | `make_manifest` 补 relation 镜像真形状；另加 F1 的真 build_manifest 交叉测试兜底 |
| L1 | LOW | 证据包 scan JSON 含 live vault 用户批注原文（仓库内、用户自有数据，风险面为 repo 可见性） | L6633-6636 "Identifying potential data privacy risks / Noting sensitive data in evidence package" | 登记不改：证据留仓是批次纪律，数据属用户本人、tips 文本已经 `_oneline` 200 字截断 |
| L2 | LOW | 空文本 tips 不参与重复分组但计入分母 | L6921 "Noting empty text impact on duplication count" | 既有 note 已声明"空文本不参与"，as-designed |

## Round-1 已核实无发现的面（transcript 证据）

- 证据一致性：3 板 scan JSON 的 5 组信号恒等式（denominator 与 counts.* 对账、asof==scan_at_utc）jq 全 true；board_sha256 与 shasum-before 逐板 BOUND（L6520-6545）。
- 既有回归零破坏：Codex 亲跑 `test_board_manifest_contracts.py` 64/64、`test_recap_scan_signals.py` 24/24（修复前基线）全绿。
- 措辞两模式通杀：fallback 模板派生词禁令与「偏离」禁词 0 命中（"Verifying fallback template term compliance...Confirming no forbidden terms in new signals"）。
- Unicode 混淆绕过：全角数字/异体 label 均落 fail-closed（缺行/格式不符 FAIL）。

## 并行独立复核（多视角 workflow，与 Codex 互补，round-1 同期）

5 视角 fan-out（verifier 逃逸 / 信号数学 / G5-9 写侧安全 / G5-9 消费面 / SKILL 一致性），
3 个视角因 session limit 中断，2 个完成并交出 5 条发现，全部亲手复现确认：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| W1 | MEDIUM | fallback role 判定只认 `derived-from` 连字符，与新抄录逻辑（收下划线）分叉 → seed 却带 relation_target、`relation_types` 聚合 > `counts.derived` | 与 Codex round-2 H1 同源，一并修（键存在检测 + 两种拼写 + created_from） |
| W2 | MEDIUM（既有 v1 缺陷，被新信号放大） | **空 frontmatter 键从下一行捏造值**：`_fm_scalar` 的 `:\s*` 在 re.M 下跨换行，`derived-from:`（空）+ 次行 `mastery_score: 0.5` → `relation_target='mastery_score: 0.5'`，来源覆盖率虚高（实测复现 1/1） | 正则改同行夹逼 `[^\S\n]*`；回归锁 `test_empty_key_does_not_fabricate_anchor` |
| W3 | LOW | role 是裸子串测试，frontmatter **值**里出现 "derived-from" 文本（如批注原话）即翻 role → 新信号会点名一个无派生元数据的节点 | 同 W1 修复覆盖；回归锁 `test_role_not_flipped_by_frontmatter_text_mention` |
| **W4** | **BLOCKER（实测复现）** | `recap_exam_build.py` create 的 tmp 路径未做 symlink 预检：预置 `<target>.g59-tmp` symlink → 内容写穿到 **vault 外**（覆盖任意外部文件），`os.replace` 让 `检验白板/<target>` 变成越界 symlink，且 undo 的 resolve 逃出 exam_root 无法回退 | tmp 纳入 symlink 预检 + `O_CREAT\|O_EXCL\|O_NOFOLLOW` 原子写（内核级封 TOCTOU）；回归锁 `test_create_refuses_tmp_symlink_no_escape` + `test_create_refuses_preexisting_tmp_regular_file` |
| W5 | LOW | undo 留痕名只含秒级时间戳 + 固定 target.name，同秒二次 undo 同一 (anchor,ts) 被 `shutil.move` 覆盖 → 先前留痕字节丢失（违反「不物理删除」） | 碰撞顺延 `-2/-3…`，绝不覆盖；回归锁 `test_undo_same_second_collision_keeps_both` |

## 处置后判据（本地复跑）

- `test_recap_scan_signals.py` **41 passed** / `test_g5_9_recap_exam.py` **23 passed**
- `test_board_manifest_contracts.py` 64 + `tests/skills/` 全量（**162 total 合并跑全绿**）
- ROUTING 校验 66/66；ruff check/format 干净
- live 三板证据第三次重取：shasum 前后全等（SHASUM-IDENTICAL），信号值见 g5-4-evidence/README.md
- W2/W4 两条按原始复现步骤复跑验证已堵死（锚点归 None 且掌握度抄录未误伤；create 拒绝 exit 2 且 vault 外文件原样）

## 后续轮次

- round-2：`codex-review-CARD-G5-4-round2.md`（**BLOCKER 0 / HIGH 4 / MEDIUM 3 / LOW 2**，九项全部处置，见该文件与上表）
- round-3：`codex-review-CARD-G5-4-round3.md`（验证 round-2 九项处置 + CARD-G5-9 首审）
