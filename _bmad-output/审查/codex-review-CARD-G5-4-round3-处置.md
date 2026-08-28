# CARD-G5-4 / CARD-G5-9 — round-3 发现处置对照表

> **来源**: `codex-review-CARD-G5-4-round3.md`（Codex ultra 第三轮，落款 **BLOCKER 0 / HIGH 8 / MEDIUM 7 / LOW 4**，
> 裁决 FAIL）+ 同期多视角 workflow 第二轮复核（17 agent 全成功，2 条 confirmed）。
> **处置状态**: 全部 21 条已处置或如实登记；判据见文末。

## HIGH（8/8 处置）

| # | 发现 | 处置 |
|---|---|---|
| H1 | fallback role 与真实 manifest 分叉：`derived-from: null` fallback 判 derived、后端判 seed（YAML truthiness）；带行尾注释的 `created_from` 同样分叉 | role 判定改为**与后端 `_node_role` 同构的 truthiness 三支**（可解析的 derived 目标 ∨ `relationships:` 块 ∨ `created_from==ai_linked_doc`）；`_fm_scalar` 增剥 YAML 行尾注释 + 键必须顶格 + 块标量起始符不当标量。回归锁 `test_role_matches_backend_node_role_exactly`（**直接 import 后端 `_node_role` 对同一 frontmatter 对拍**，5 参数化形态） |
| H2 | 无据行「零数字」漏表量字「两」：`无据（共有两条）` 曾 PASS | `_ANY_DIGIT_RE` 补 `两俩半双廿卅`；回归锁参数化补两条变体 |
| H3 | 信号行只查首个匹配 + 档位"出现过" → 正确串后追加 `99/99【实测】` 仍 PASS | 改为**整行严格模板 fullmatch**（前缀装饰 + 标准式 + 档位标注，其后不许有任何非空白残留）——词表/首匹配竞赛结构性终结；回归锁 `test_verify_trailing_second_number_group_fails` |
| H4 | 同义断言可无限改写绕过词表：`派生数量为零` 仍 PASS | 改**结构级禁令**：fallback 下台账「### 种子」小节整段禁「派生」二字（子女数在 fallback 恒无据，该断言只可能出现在此段）；规模自陈与 ③ 段 relation_types 引用不受影响。回归锁 `test_verify_fallback_seed_section_derivation_words_fail` |
| H5 | preview 未绑定 create：期间 vault 变化时 create 照样成功，用户确认的不是最终字节 | 新增 `--expect-content-sha`（SKILL.md 定为**必传**）：不符即**零写侧拒绝**并要求重跑 preview。回归锁 `test_create_refuses_stale_content_sha`（含"未变化时放行"正例） |
| H6 | `os.replace(tmp, target)` 会覆盖预检之后才出现的 target | 落盘改 **`os.link` no-replace**（目标存在 → 内核 EEXIST，原子且永不覆盖）+ unlink tmp；回归锁沿用既有"目标已存在拒绝"用例 + 新 tmp 占用用例 |
| H7 | undo 校验的字节与最终移走的字节未绑定（期间被替换则移走未校验版本） | 改 **fd + (dev,ino) 绑定**：`O_NOFOLLOW` 打开 → 从 fd 读校验 → 移动前复核 inode 未变，不符即拒；留痕改为**目的端 `O_EXCL` 写校验过的字节 + fsync 后才 unlink 源**（耐久、跨文件系统安全）。回执增 `retained_sha256` |
| H8 | `undo_hint` 未 shell-quote：板名含空格/括号/& 时是语法错误的命令（zsh -n parse error） | 逐参数 `shlex.quote`；回归锁 `test_undo_hint_is_shell_safe` 用 `shlex.split` 反解并比对路径 |

## MEDIUM（7/7 处置）

| # | 发现 | 处置 |
|---|---|---|
| M1 | `_strip_note_ref` 不幂等：`[[节点/null]]` → `"null"` → 再调用 → `None` | manifest 侧改用新的 `_passthrough_note_ref`（只对**仍带 wikilink 标记**的值归一，后端 resolve 过的裸 stem 原样透传）→ 幂等成立。回归锁 `test_manifest_note_normalization_is_idempotent` |
| M2 | `isinstance(True, int)` 为真 → `value: true` 配报告 `1/N` 通过 | schema 校验显式排除 `bool`；回归锁 `test_verify_bool_value_rejected` |
| M3 | `##\t附录`（tab 分隔的合法标题）不终止 ③ 段 | 终止正则空白改 `[^\S\n]`；回归锁 `test_verify_tab_heading_section3_boundary` |
| M4 | undo 目的端 `exists()` 后 `shutil.move` 有竞态，跨文件系统退化 copy+unlink | 见 H7（目的端 O_EXCL + fsync + 后删源） |
| M5 | 只 fsync 文件不 fsync 父目录；tmp 清理失败被静默吞掉 | 新增 `_fsync_dir` 用于目标父目录与 undo-dir；tmp 清理失败改为**回执 `warning` 字段如实上报**（SKILL.md 要求转告） |
| M6 | 板名含 `#`/`\|` 时产物 wikilink 被消费方按锚点/别名截断，`scan_vault` 归属错乱且不报 parse error | `_prepare` 显式拒绝 `#`/`\|`/`^`（exit 2）；回归锁 `test_create_refuses_wikilink_semantic_chars_in_board_name` |
| M7 | `--ts` 只验形状（`2026-99-99-9999` 通过）；默认取**本地墙钟**却贴 `Z`（Asia/Shanghai 快 8h，与 start-exam-board 的 `date -u` 分属两个时钟 → `exam_history` 排序错位） | `datetime.strptime` 真校验日历时刻；默认 ts 改 `datetime.now(timezone.utc)`；`_created_at` docstring 写明"调用方必须保证 ts 是 UTC"；SKILL.md 标注 `date -u`。回归锁 `test_create_refuses_impossible_timestamp` + `test_default_ts_is_utc_not_local`（UTC 窗口断言） |

## LOW（4/4 处置）

| # | 发现 | 处置 |
|---|---|---|
| L1 | preview 对既有目标只给 `target_exists:true`，无 SKILL 承诺的 `refusal_reason` | 补 `refusal_reason`（含换 `--ts` 或先 undo 的指引） |
| L2 | docstring「正文根本不进内存」不实（`_ledger_from_local` 读全文判 is_stub） | 改为诚实表述：保证的是"**不写进产物**"（哨兵串断言锁的正是前者），不是"不读取" |
| L3 | `mkdir`/`shutil.move` 等 I/O 异常未归一，可能 traceback + exit 1 | 两处 mkdir 与留痕写入全部归一到 `JSON + exit 2` 契约 |
| L4 | 证据/验收单过度声明：G5-4 README 声称 null 幂等已修；G5-9 验收单写 23 条而实际收集 19 条，并称已"封 TOCTOU" | 验收单数字按 `--collect-only` 实测改为 **G5-4 57 条 / G5-9 26 条**；"封 TOCTOU" 改为"内核标志封住 lstat→写之间的窗口"（如实限定）；README 幂等表述按 M1 实际修复重写 |

## workflow 第二轮 confirmed（2/2 处置）

| # | 发现 | 处置 |
|---|---|---|
| WF-1 | `created_at` 本地墙钟冒充 UTC（与 M7 同源，另实证了 `exam_history` 排序错位的完整链路） | 见 M7 |
| WF-2 | 幽灵链接（Concepts 列了但节点不存在）静默计入成员 → 产物写出「成员 3（1 种子 + 0 派生）」自相矛盾数字 + 死 wikilink 零标记 | `_scan_board` 分开统计：`members` 只数可解析成员（`members == seeds + derived` 恒等），新增 `listed_in_concepts`/`ghost_links`/`ghost_count`；产物把幽灵单列「## 待修链接」段用**反引号**列出（不写成 wikilink）；SKILL.md 加硬约束。回归锁 `test_ghost_links_not_counted_as_members` |

## round-4 中断前口头提出的四点 + 一项自查（全部处置）

Codex round-4 在被平台过滤器误拦中断前，已在 transcript 里明确提出四点，本轮一并修复：

| # | 发现 | 处置 |
|---|---|---|
| R4-1 | `relationships:` 仍按**键存在**判定，而后端取 truthiness（`relationships:` 空值 → None → seed） | 改为内容判定：键后有非空流式值（非 `null`/`~`/`[]`）或次行起有缩进 `- ` 列表项才算派生。回归锁 `test_relationships_truthiness_matches_backend`（4 形态与后端对拍） |
| R4-2 | 有数信号行尾部通配段 `[^【】]*` 仍可容纳第二组数字（`2/3 成员含来源锚点 99/99`） | 收紧为 `[^【】0-9０-９]*`（说明文字可留，数字不许再现）。回归锁 `test_verify_trailing_number_in_tail_text_fails` |
| R4-3 | `undo_hint` 的 `<vault外目录>` 占位符是 shell 重定向语法 → 整条命令 `zsh -n` 仍解析失败（quote 了路径但没管占位符） | 占位符改为引号串 `'PUT_A_DIR_OUTSIDE_THE_VAULT_HERE'`；回归锁断言 hint 内无 `<`/`>` 且 `shlex.split` 可解析 |
| R4-4 | undo 在 inode 复核到最终 `unlink` 之间仍有窗口（留痕写入耗时内文件可能被替换） | 紧贴 `unlink` **再复核一次** inode，不符则保留 vault 内文件并如实回执（留痕已在 vault 外，不丢字节） |
| R4-5（自查补） | 零宽/双向控制字符可让"渲染所见"与"正则所校"分叉 | verifier 直接拒收该类字符；回归锁 `test_verify_zero_width_chars_fail` |

## 处置后判据（本地复跑）

- `test_recap_scan_signals.py` **63 passed** / `test_g5_9_recap_exam.py` **26 passed**（`--collect-only` 实测数）
- 合并跑 `test_recap_scan_signals + test_board_manifest_contracts + tests/skills/`：**187 passed**
- ROUTING 校验 66/66；`ruff check` / `ruff format --check` 干净
- live 三板证据重取：shasum 前后全等；G5-9 两组真实板组全链（含 `--expect-content-sha` 绑定）全过、`.g59-tmp` 残留 0

## 未处置的诚实边界（登记不装通）

- `_fm_scalar` 仍是**正则近似**而非完整 YAML 解析：重复键取首个、锚点/别名不解析、复杂块标量不支持。
  这是 fallback 模式的既有设计边界（无 yaml 库依赖），报告对该模式的字段一律标【推定】/【文件】档。
  与后端 YAML 的等价性由 `test_role_matches_backend_node_role_exactly` 在 role 这一最关键口径上直接对拍锁定。
- Codex round-3 指出的「祖先目录分量 TOCTOU / bind-mount 覆盖」类攻击面：本卡未用 `dir_fd` 全链绑定，
  沿用 G5-2 同款声明边界（该面需要整套 openat 重写，超出本卡范围）。
