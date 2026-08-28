# CARD-G5-4 / CARD-G5-9 — round-4 发现处置对照表

> **来源**: `codex-review-CARD-G5-4-round4.md`（Codex ultra 第四轮，落款 **BLOCKER 0 / HIGH 9 / MEDIUM 3+ / LOW…**，裁决 FAIL；
> round-3 的 19 项判为 6 PASS / 9 PARTIAL / 4 FAIL）。
> **处置状态**: 全部已处置，逐条附亲手复现验证。判据见文末。

## HIGH（9/9 处置）

| # | 发现 | 处置 | 复现验证 |
|---|---|---|---|
| H1 | fallback role 仍不等价后端 YAML truthiness：`relationships: false/0/""/{}/[]`、带注释的 `created_from`、块 mapping 等分叉 | ① `_strip_note_ref` 的 falsy 集合与后端 `yaml.safe_load` 对齐（补 `false/0/""/{}/[]`）；② `relationships` 改**内容判定**（inline 非 falsy ∨ 次行有缩进列表项/mapping 键），并剥行尾注释 | 新增 `test_falsy_derived_from_matches_backend`（6 形态）与 `test_relationships_truthiness_matches_backend`（4 形态），均 import 后端 `_node_role` 对拍 |
| H2 | 「无据行零数字」被 `共有壹条`、Arabic-Indic `٩`、上标绕过 | **字符黑名单换成 Unicode 数值属性检测**：`unicodedata.category ∈ {Nd,Nl,No}` + 显式补全汉字数字（Lo 类，unicodedata 不认）小写/大写/表量三组 | 反例「共有壹条」实测 exit 1；参数化补 5 变体（大写汉字/Arabic-Indic/上标/罗马/分数） |
| H3 | 尾部禁数字仍是 ASCII/全角字符类 → `九九/九九`、`٩٩/٩٩`、`⁹⁹/⁹⁹` 可追加第二组数字 | 标准式尾部改具名捕获 `(?P<tail>[^【】]*)`，对 tail 跑 `_has_numeric` | 反例「九九/九九」实测 exit 1；参数化 4 变体 |
| H4 | 「结构级禁令」实为关键词禁令 → `后代节点数量为零` 仍 PASS | 改**整行模板白名单**：fallback 台账「### 种子」小节每行必须整行匹配 `- <节点> — 批注 N 条` 或 `— 无批注`，任何自由叙述一律 FAIL（不再判断"是不是在说派生"） | 反例「后代节点数量为零」实测 exit 1；参数化 3 变体（含完全不含"派生"二字的说法） |
| H5 | `--expect-content-sha` 仍可省略（SKILL 说必传、脚本可选），测试 helper 自己也在省略 | argparse 改 **`required=True`**；测试 helper `do_create` 改为先跑 preview 取 sha 再 create（走真实 skill 流程） | 省略参数实测 argparse 报错退出；新增 `test_create_requires_expect_content_sha` |
| H6 | `os.link` no-replace 本身对，但 fd 关闭后按 tmp **路径** link → 期间 tmp 被替换会发布他人内容 | 写入 fd 保持打开取 `fstat` 记 (dev,ino)，link 之后立刻核对 target 是同一 inode，不符则撤销发布并报错 | 覆盖在既有 tmp symlink/占用两条回归锁 + 新 inode 核对分支 |
| H7 | 两次 inode 复核挡不住**同 inode 原地改写**（编辑器就地写）→ undo 删掉用户新内容 | 删除前改为**重读内容比对 sha**（inode 一并核），覆盖"替换"与"原地改写"两种形态 | 既有 sha 不符拒绝锁 + 留痕 sha 断言 |
| H8/新增 | preview **不是零写侧**：importlib 加载在 vault 内 `.claude/skills/.../__pycache__` 落 .pyc（证据快照只覆盖四个数据目录才没发现） | `sys.dont_write_bytecode = True` 包住 `exec_module` 并恢复 | 新增 `test_preview_writes_no_pycache_into_vault`：把脚本副本放进 vault 内（真实部署形态）跑 preview，断言**全 vault 零新增文件**；实测 4→4 文件、0 个 `__pycache__` |
| H9/WF-2 | 幽灵 id 含换行/反引号时突破 Markdown 隔离，在产物里生成独立注入行 | 新增 `_sanitize_ghost_id`：折叠空白 + 剔除 `` ` `` `[` `]` `\|` `<` `>` `\` + 只留可打印字符 + 120 字截断 | 幽灵段只回显标识串，不承载格式 |

## MEDIUM（3/3 处置）

| # | 发现 | 处置 |
|---|---|---|
| M3 | ③ 段边界仍不严：空标题 `##`、四空格缩进块、fenced code 内的信号行均 PASS | 终止正则认**空标题**（`^#{2,3}(?:[^\S\n]\|$)`）；新增 `_strip_code_blocks` 在校验前整体剔除 fenced 与缩进代码块（行数保持不变） |
| 新增 | signal schema 非 fail-closed：`percentile_ref=null` 时报告写 `None/None/None` 仍通过 | schema 校验年龄信号有数档必须有 dict 分位且三个分位是整数；信号行渲染前再兜一层 |
| — | （M2 bool 修复 round-4 判 PASS，无需再动） | — |

## 处置后判据（本地复跑）

- `test_recap_scan_signals.py` **86 passed** / `test_g5_9_recap_exam.py` **28 passed**
- 合并跑 `test_recap_scan_signals + test_board_manifest_contracts + tests/skills/`：**212 passed**
- ROUTING 校验 66/66；`ruff check` 干净
- Codex round-4 的五条关键反例逐条亲手复现，全部 exit 1 / 拒绝

## 未处置的诚实边界（登记不装通）

- **`_fm_scalar` 仍是正则近似而非 YAML 解析**：块标量值、引号值后带注释、整份 frontmatter 缩进两格等形态与后端仍可能分叉。
  这是 fallback 模式的固有设计边界（脚本纯 stdlib、无 yaml 依赖），报告对该模式一律标【推定】/【文件】档。
  最关键的 role 口径由两组 import 后端 `_node_role` 的对拍测试锁定（共 15 个形态），但**不宣称全形态等价**。
- **祖先目录分量的 TOCTOU / bind-mount 覆盖**：未用 `dir_fd` 全链绑定（需要整套 openat 重写），沿用 G5-2 的同款声明边界。
- **undo 的 unlink 与最终内容校验之间仍有纳秒级窗口**：已压到"读内容比对 sha → 立即 unlink"，进一步消除需 `unlinkat` + fd 语义支持。
