# CARD-G5-10 独立复核 round-1（绑 `db9fc54f`）—— board-split 执行侧 split_apply

## ① 背景与最小读取面（请只读下面列出的东西，不要漫游全仓）

仓根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p7-skills-x`
本轮审查绑定：**`db9fc54f`**（= 送审时 HEAD；tracked 工作树干净，改动只在本卡两个新文件里）。

上游卡（G5-3）只交付了**只读**的拆分预览引擎 `split_preview.py`（看得到拆分建议，拆不了）。
本卡补**执行侧** `split_apply.py`：消费 preview JSON + 用户逐条拍板的 `--confirm <stable_id>`，
在**准入五门**全过之后原子创建 `节点/` 派生 md（provenance frontmatter 含 `source_board` +
`split_stable_id`，经真 `board_manifest_service.scan_vault` 解析为 board members、role=derived、
不落孤儿），落一本**可一键撤销**的账（复用 P7-A 的 `canvas-vault/.claude/scripts/undo_journal.py`）。
**默认路径 0 物理删除**（`os.remove` 只许出现在 undo 分支且只作用于账上记录的自建文件）。
可选 wikilink callout 插入**默认关**、逐行显式确认。

本卡 diff（两份新文件）：
```
git --no-pager diff --no-color a357194b db9fc54f -- . ':(exclude)_bmad-output'
```
- `canvas-vault/.claude/skills/board-split/scripts/split_apply.py`（NEW，766 行，执行侧 CLI）
- `backend/tests/skills/test_g5_10_split_apply.py`（NEW，13 条承重行为用例）

`split_apply.py` 终态全文：`cat canvas-vault/.claude/skills/board-split/scripts/split_apply.py`。

为读懂契约的**既有**文件（本卡只读/零改动）：
- `canvas-vault/.claude/skills/board-split/scripts/split_preview.py`
  `:38-52`（stable id 铁律）/ `:124-130`（namespace）/ `:433-449`（`_DERIVED_CALLOUT`）/
  `:521-560`（`compute_stable_id`）/ `:608-660`（候选字段）/ `:815-870`（`vault_fingerprint` 算式与落盘）/
  `:1090-1140`（`load_preview_json` 校验）/ `:1734-1832`（写侧防御）/ `:1846-1882`（preview 模式与缺省 out-dir）
- `backend/app/services/board_manifest_service.py` `:132-145`（`resolve_node_id`）/ `:457-500`（`_node_relation`/`_node_role`）/
  `:525-560`（`scan_vault` 入口）/ `:645-677`（`source_board` → members / orphans 归类）
- `canvas-vault/.claude/scripts/undo_journal.py` 全文（P7-A 复用面：`BatchJournal` / `backup` / 行状态机 / `atomic_write_bytes` / `undo`）
- `canvas-vault/.claude/skills/ai-linked-doc/SKILL.md` `:140-158`（frontmatter 先例）
- `backend/tests/regression/skill_trigger_matrix.yaml` `:41-44`（board-split = planned ⇒ 不加 SKILL.md）
- 第十五批开跑手册 §零.8 / §零.16（保守默认）；本卡文 `第十五批-goals/P7-B.md` §一(c)-(e)

**jev 分诊（协议 §2.4.3，绑 `db9fc54f`；③ 的问题清单按 urgency 降序）**：

| FILE | CHURN | URG | REVIEW | TEST | RISK | VERDICT |
|---|---|---|---|---|---|---|
| `canvas-vault/.claude/skills/board-split/scripts/split_apply.py` | +766/-0 | 3.24 | 0.90 | 0.54 | logic | REVIEW |
| `backend/tests/skills/test_g5_10_split_apply.py` | +480/-0 | 1.72 | 0.70 | 0.91 | test_or_docs | REVIEW |

## ② 作者自述请独立核对（当成**待验证的命题**，不是事实）

1. 创建的节点经**真 `scan_vault`** 判 `role == "derived"`、进该板 `members`、**不在** orphans、parse_errors 为空（按 node_id / source_board 逐字段断言）；
2. `identity_ambiguous=true` 候选**零持久化**（拒绝、rc≠0、零产物）；
3. 过期 preview **零产物**拒绝（三层：vault 指纹 / 候选集 / 逐候选内容指纹与行号）；
4. `--undo` 后 vault 全树 `{路径: sha256}` 与 apply 前**逐项相等**；用户改过的文件**拒删并列出**（rc≠0）；
5. **默认路径 0 物理删除**（AST 门数 `Call` 节点：非 undo 函数内 = 0）；
6. callout 插入**默认关**；非 TTY 未给 `--confirm-insert` = 全跳过（不静默插）；已存在同形 callout 不重复插；
7. `split_preview.py` / `board_manifest_service.py` / `models/board_manifest.py` **零改动**；
8. **不加 SKILL.md**（scripts-only）。

已跑裁判（作者声明，存档在 `_bmad-output/审查/evidence-g510/`）：13/13 绿；负控 3 段各自点名红（歧义放行 / 门①恒通过 / 撤销不看 sha）+ 逐字还原；AST 删除门 `undo_calls=1 non_undo_calls=0`；真解析门 + 验伪锚（删 `source_board` 行 → `no_source_board`）；ruff rc=0。

## ③ 按重要性排序的问题（按分诊 urgency 降序）

0. **过期检测三层是否各自足够、又是否过宽**：`vault_fingerprint`（= vault 路径哈希，对内容零敏感）＋候选 `stable_id` 集＋逐候选内容指纹（在**账上行号处**重算）。唯一容忍 = 「本候选自己那条 callout 已逐字插入」（去掉这些行后指纹相符）。问：这个容忍分支会不会掩盖别的漂移（比如别人手改了正文又恰好插了同名 callout）？callout 使 `line_end` 漂移但行号不再单独比对，留缝吗？
1. **`O_CREAT|O_EXCL|O_NOFOLLOW` + journal「intent→done」**：进程被杀于两者之间后重跑，判定「目标存在且 sha 匹配 → 补记 done / 已存在同 id → 认领」——sha 匹配是否足够？会不会把**别人的**同名同字节文件当成自己的？
2. **undo 的半途收口**：用户改过的文件拒删（refused）后，该件保持 `done`、其余标 `undone`，重跑 `--undo` 只重试 refused——这个半 undo 是否真可重入、账状态是否一致？
3. **callout 用 `line_start` 定位**：preview 产出后板文件被改（但过了门①的情况）会不会插错行？同文件多条按行号**降序**插入是否排除了互相顶行号？整文件 `split("\n")` 重写是否保持 CRLF / 尾换行字节不变？
4. **`resolved_name` 直接作文件名**的路径安全：`member_name_ok` 同族口径（`/`、`..`、控制字符、前导点）+ 长度上限 + `safe_join` + symlink 门；NFC/NFD 等价未判定（如实声明）——有没有绕过的输入？
5. **新测试是否全部真跑**：每条用例先真跑 `split_preview.py` CLI 产 preview（不手造 JSON）？有没有断言其实绿在更早判据上、夹具在断言前就抛、或只断言 rc 的用例（特别是 ⑥ callout / ⑨ 幂等 / ⑩ 续跑）？
6. **动态加载**：`split_apply.py` 用不写 `__pycache__` 的 loader 加载兄弟模块；新测试**不**动态加载任何脚本（subprocess-only）——是否还有 `sys.modules`/dataclass 类隐患没被覆盖？
7. **撤销侧对 `planned`（无 done）行的处置**（作者的扩展，请重点审）：按 `sha256_planned` 认领并删除——卡文的口径是「只删 done 且 sha 匹配」，这条放宽是否正确、有没有更宽的洞？
8. **`batch_id` 派生** = `sha256(preview 文件字节 + 排序后的 confirm 集)`：同内容不同路径 → 同批次；confirm 重排 → 同批次。落点固定 `<vault>/outputs/board-split/<batch_id>/`——`outputs/` 是否会被下一轮 preview 当成语料（本卡断言不会，请核）？

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
- `file:line`
- 一句话说明缺陷是什么
- 一句复现思路：**未被拦下的输入** / **对照输入** / **负控输入** / **门未覆盖的路径**

结尾给出计数行：`BLOCKER n / HIGH n / MEDIUM n / LOW n`。没找到问题就明说「无」——「没找到」是有价值的结论，凑数不是。请用中文输出。不要用「构造攻击载荷 / 可复现的利用片段 / 打穿 / 绕过防护」这类措辞。

## ⑤ 边界

- **只读**；不连任何数据库或网络；不运行写盘命令。
- 不评 P7-C 的 Concepts 托管块 sentinel 面、不评 G5-11 UAT / R-J03 / R-J08 旅程。
- 不评 P7-A `inbox_apply.py` 本体（只评它对 `undo_journal.py` 的复用面）。
- `split_preview.py` / `board_manifest_service.py` 是别的面的既有实现（本卡零改动）：对它们内部实现的意见请标注「移交」，不计本卡 BLOCKER/HIGH。
