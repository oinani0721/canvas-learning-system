# CARD-G8-2 独立对抗审查（round-4 · 用户授权定向续轮）

你是独立审查者。round-1/2/3 存档于 codex-review-CARD-G8-2*.md；round-3 终轮你判
0 BLOCKER + 4 HIGH。**用户授权本定向续轮**（主 goal 总账「主 session 补发 Codex 定向续轮」机制），
专门复核 round-3 四个 HIGH 的整改。工作目录 =
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w9-lint`。
**只读审查，不要修改任何文件。**

## 一、round-3 四个 HIGH 的整改声明（证伪优先，不成立标 REGRESSED）

| # | round-3 发现 | 声明的整改 | 验证要点 |
|---|---|---|---|
| H1a + H2 | 嵌套目录 symlink 后代被 rglob 静默吞；chmod 000 子树整棵消失 | **放弃 rglob**：`_walk_md` 复用 G8-1 `cvr._walk_vault`（os.walk onerror + dangling 单列 + os.access），目录 symlink 记盲区「后代不在扫描面」 | `节点/sub -> 外目录`：sub 必须出现在 blind_detail 且 x 仍报孤儿；`节点/locked`(chmod000)：locked 必须在 blind_detail；--only orphan JSON 的 blind_spots ≥ 1 |
| H1b | `原白板 -> 节点/` 目录别名：同一物理文件以别名贡献入链绕过自身排除 | 入链来源与豁免判定都改用 **os.path.realpath 物理路径**作键 | 你的 `原白板 -> 节点/` + A 只有自链 fixture：A 必须仍报孤儿 |
| H1c | recap 越界记盲区但检查仍 ok | `raw_derived` 盲区存在 → 至少 warn（与 orphan 规则对齐） | 你的 `回顾-outside.md -> vault 外` fixture：应 WARN |
| H1d | `outputs -> vault 外目录`：freshness 读外部投影 | `_projection_status` 前置 `_resolves_inside_vault` + symlink 检查，越界判 corrupt | 你的 `outputs -> 外目录(当天投影)` fixture：应 corrupt 且不读外部内容 |
| H3 | code span 开闭反引号必须等长（`` ``foo` [[A]]`` `` 逃逸） | span 正则改 `` (`+)[^`]*\1 ``（反向引用等长） | 该 fixture：A 必须仍报孤儿 |
| H4 | MANIFEST 未绑定 transcripts 与 G8-1 测试文件 | MANIFEST 改 `find -type f` 全覆盖（含子目录 15 份 transcript + test_vault_doc_roles.py），排除 .old-* 备份 | 核对 MANIFEST 条目数与实际文件 |

## 二、新增变异 M15-M18（对应四修复的判别门）

M15 入链来源退回相对路径（杀 test_orphan_directory_alias_self_link_uses_realpath）/
M16 span 等长退回（杀 test_code_span_equal_length_runs）/ M17 投影越界检查拆除（杀
test_projection_symlink_outside_is_corrupt）/ M18 枚举盲区并入拆除（杀
test_orphan_unreadable_subtree_is_blind）。transcripts/ 已存档；终轮你实测过 15/15，
本轮请复核 19/19（新增 4 个）与两个修正的旧锚（M11 物理路径形态、M13 两行锚更新）。

## 三、整改如实申报

- **结构性冗余消除**：`节点/` 曾被枚举两次（nodes 一次 + 入链源循环一次），枚举盲区两路
  并入互为冗余——M18 首跑 SURVIVED 的真凶。已改为 nodes 复用 NODE_DIR 源循环的枚举结果，
  盲区并入只剩一处，M18 对唯一路径承重。
- **反向差异如实登记**：越界投影本实现判 corrupt 而 oracle 直接读（比 oracle 严）——
  同源锁只锁合法 v3 投影，`test_projection_symlink_outside_is_corrupt` 不再断言 oracle 等值，
  差异方向（更安全）写进 `_projection_status` docstring 与验收单 §6。
- **H4 时序澄清**：round-3 审查期间 MANIFEST 已重生成（format 后字节），你看到的 25 条目版
  本为旧态；现行 MANIFEST 为全覆盖版。请按现行版复核。

## 四、终态裁判（当前字节，MANIFEST 绑定）

181 passed（62 本卡 + G8-1 119 零回归，referee1-pytest-full-round4.txt）+ 19/19 mutant
KILLED + live 第四轮取证 sha `a82e3af0…` 前后逐字相同 rc=0 + 禁改门空。MANIFEST 生成时间与
源码 sha 见 MANIFEST.txt。

## 五、输出格式

分级 BLOCKER/HIGH/MEDIUM/LOW + file:line + 具体失败场景 + 实跑命令与输出。
round-3 四条若整改不成立标 REGRESSED。最后一行：
`BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否（BLOCKER: n, HIGH: m）`。
