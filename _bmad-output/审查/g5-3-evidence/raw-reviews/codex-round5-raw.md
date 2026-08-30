# Codex 审查 · CARD-G5-3（第 5 轮 · 确认）

## 裁决

**不通过** —— 四轮点名的具体变体、P3 清单和陈旧哈希均已修复，但仍存在可由现有字段正向复算发现的语义 fail-open；核心“会换 ID”清单也有一条实测错误。

## 四轮发现逐条复核

- **PARTIAL · HIGH 语义层 fail-open**

  - 原第三轮 166 组畸形 schema：**166/166 拒绝**。
  - 原 13 类语义矩阵：**13/13 拒绝，rc=0 剩余 0**。
  - 第四轮补充的 11 组矩阵原样重跑：**4 组拒绝、7 组仍 rc=0**。被拒的是 namespace 协同重标、不同层数假标题、空白 vault 指纹、自相矛盾 scale gate。
  - 7 组接受项为：合法正行号伪造、合法格式假内容指纹、board 重标、歧义标志协同伪造、名称伪造、自洽文件重绑、自洽标题重绑。其中真正需要 vault/签名才能识别的自洽伪品，确属已声明边界。

  但标题守卫只比较层数，仍可绕过：[split_preview.py:1244](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1244)。

  实跑把新侧原文标题改成同层数的 `["完全伪造的父标题","完全伪造的子标题"]`，不改 basis 或 ID：

  - `normalize_heading_path(伪造原文) != heading_path_normalized`
  - `--diff` 仍 `rc=0`
  - `summary={unchanged:1}`
  - 伪造锚点进入 `unchanged.new`

  这不是“无签名所以无法识别”：对原文路径做**正向归一化**即可发现不一致，无需从归一化结果反推原文。因此契约所说“归一化有损，所以只能绑层数”不成立，[契约:467](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:467)。

  “无签名 + 自洽伪品可通过”的声明和负向测试本身是诚实的；全套测试也确实执行并接受了不存在的伪造来源，[测试:1260](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:1260)。问题是当前仍混入了**可检查的内部不一致**，所以信任边界没有完全划准。

- **RESOLVED · P3 产物清单**

  - `run_live_evidence.sh` 已使用递归 `find "$OUT" -type f`，[脚本:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/run_live_evidence.sh:54)。
  - `outputs/` 实际 11 个普通文件；manifest 12 行＝引擎＋11 文件。
  - manifest 与 `find` 的路径集合差异为空。
  - 两份 manifest 全部 `shasum -c` 通过，包括 `outputs/exam_boards/.gitkeep`。

- **RESOLVED · LOW 变异日志字节陈旧**

  - 当前引擎：`79979454…aa8`
  - 当前裁判：`063c424b…e57`
  - 与 [mutation-check.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/mutation-check.txt:2) 完全一致。
  - 我直接对当前字节重跑 `mutate_engine.py`：**28/28 对应裁判变红，退出码 0**。

## 边界声明诚实性专项

- **§4.1：9/10 与实现相符。#6 列错。**

  契约称板文件改名会“全板换 ID”，[契约:159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:159)。混合构造同时含板体候选和种子笔记候选后，将板名从“板甲”改为“板乙”：

  - 板体候选：ID 改变
  - 种子候选：ID **不变**

  因为种子候选的 `file_rel` 是 `节点/种子.md`，不含板文件名。现有裁判只使用纯板体候选，因此产生假完备感，[测试:671](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:671)。

- **§4.2：按限定后的 10 个操作均吻合。**

  行漂移、正文修改、唯一标题调序、编号/行尾时间戳、NFC/NFD、空行空白、等价文件名、机器段、节点池名称、祖先链不变的层级调整均实跑通过。

  但“调序不换 ID”必须限定为无身份歧义的候选；重复标题的反例由 §4.4 正确披露。UAT 的“不管把这一节挪到哪，ID 都不变”明显超过该边界，[UAT:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/验收单/UAT-CARD-G5-3-拆分稳定ID与diff契约-2026-08-30.md:21)。

- **§3.1：符合。**

  代码 fence 和普通 HTML 注释改动均改变指纹；Recent Activity 和 AUTO-GENERATED 刷新均不改变指纹。

- **§4.4：行为声明准确，防误用措辞仍过头。**

  删除/插入重复标题的 occurrence 改嫁、交换时指纹对调、歧义红旗均与实现一致。但“让它无法被误用”与实际不符，[契约:223](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:223)；后文自己承认这只是契约约束、不是运行时强制，[契约:419](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:419)。审查存档的“接口层面不可能发生”也同样过头，[审查存档:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/codex-review-CARD-G5-3.md:55)。

- **§8.2：scale gate、namespace、vault 指纹守卫符合；标题守卫 PARTIAL。**

  自洽伪品不可识别的声明准确，但不能把同层数、正向归一化不一致的锚点归入该边界。原矩阵中 `board` 重标但 `board_file` 不变也仍 `rc=0`，同样是无需读 vault 就能对账的内部不一致。

- **§十：方向正确，但措辞/机械清单不完全。**

  当前 v1 引擎确实只接受自身 namespace，跨代拒绝生效。升级时提升 namespace、稳定性自陈和前缀的方向正确。不过“改动 occurrence/归一化口径都会让全部 ID 变化”说得过满——只有受新规则影响的身份键才会变化；同时 `_ID_RE` 仍硬编码 `bsa1-`，[实现:1083](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1083)，v2 清单应明确同步更新验证规则。

## 本轮新发现

- **HIGH · 同层数伪造标题路径仍静默通过**

  复现脚本：`/private/tmp/g53_same_depth_probe.py`。结果目录：`/private/tmp/codex-g53-r5-depth.ilpa0g95`。生产 CLI `rc=0`、`unchanged=1`，伪造的新锚点被输出。

- **MEDIUM · §4.1 #6 “板改名后全板换 ID”错误**

  复现脚本：`/private/tmp/g53_boundary_matrix.py`。20 项矩阵为 **19/20**，唯一失败即 #6；板体候选换 ID，种子候选不换。

- **MEDIUM · UAT 仍向用户过度承诺移动稳定性**

  [UAT:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/验收单/UAT-CARD-G5-3-拆分稳定ID与diff契约-2026-08-30.md:21) 的“挪到哪都不变”与跨文件、换父、重复标题三类已声明不稳定面冲突。

- **LOW · 测试覆盖声明过宽**

  UAT 称 §4 的 20 条“逐条变成断言”，[UAT:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/验收单/UAT-CARD-G5-3-拆分稳定ID与diff契约-2026-08-30.md:65)，但仓库裁判没有分别覆盖 §4.1 #4、#9、#10；本轮独立矩阵验证了当前行为，不等于交付裁判已经钉死。

- **LOW · UAT 的格式检查绿证不实**

  `ruff check` 通过；`ruff format --check` 当前返回 `rc=1`，点名两个测试文件需要格式化，与 [UAT:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/验收单/UAT-CARD-G5-3-拆分稳定ID与diff契约-2026-08-30.md:73) 的“全绿”不符。

## 我实际跑了什么

- 用户指定完整测试：**132 passed / 10 warnings / rc=0**，即 98＋34。
- 原 166 组 schema 复现器：**166/166 拒绝**。
- 原 13 类语义矩阵：**13/13 拒绝**。
- 第四轮 11 组补充语义矩阵：**7 rc=0 / 4 拒绝**。
- 独立 §4.1/§4.2 20 项生产入口矩阵：**19/20 与文档吻合**。
- §3.1 fence、HTML、Recent Activity、AUTO-GENERATED 覆盖实验。
- 同层数标题伪造的单侧 diff 反例。
- 两份 manifest `shasum -c`、manifest 与递归文件集合对账。
- 当前字节上的 28 组变异反证：**28/28 变红**。
- `ruff check` 与 `ruff format --check`。
- 审查前后 `git status` 和四个核心文件哈希一致；未编辑仓库，未写真实 vault。Graphiti MCP 本会话不可用，因此未执行其记忆检索。
