# Codex 审查 · CARD-G5-3（第 6 轮 · 终裁）

## 裁决

**不通过** —— 五轮点名的具体守卫大多已修复，但 §8.2 的“自洽伪品”断言仍把可由 JSON 自身发现的矛盾算进信任边界，核心边界声明尚不诚实。

## 四轮发现逐条复核

- **PARTIAL · HIGH 语义层 fail-open**

  - 原第 4 轮 11 组矩阵原样重跑：**5 组拒绝、6 组仍 `rc=0`**。
  - 已拒绝：外来 namespace、伪造原文标题、空白 vault 指纹、自相矛盾 scale gate、board 重标但 board_file 不变；全部零产物。
  - 仍接受：合法正行号、合法格式假指纹、协同歧义标志、伪造名称、自洽 file 重绑、自洽 heading 重绑。
  - 前两类确属不读 vault 时的真实性边界；后几类中仍混有可检查的内部矛盾，详见“本轮新发现”。

- **RESOLVED · P3 产物清单**

  [取证脚本](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/run_live_evidence.sh:54) 已使用递归 `find "$OUT" -type f`。实测 `outputs/` 为 11 个普通文件，manifest 12 行＝引擎＋11 文件；路径集合差异为空，两份 manifest 全部 `shasum -c` 通过，包含 `outputs/exam_boards/.gitkeep`。

- **RESOLVED · LOW 变异日志字节陈旧**

  当前 engine 为 `51e3cd67…19ef`、judge 为 `54429e35…5249`，与 `mutation-check.txt` 头部逐字一致。当前字节独立重跑：**29/29 变异体均使对应门变红，rc=0**。

### 第五轮六项处置

1. **RESOLVED · 同层数伪造标题**  
   原复现脚本重跑为 `rc=1`、零产物，诊断明确为正向归一化不符。守卫实现见 [split_preview.py:1248](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1248)。`board ↔ board_file` 重标也已拒绝。

2. **RESOLVED · 板改名真实口径**  
   混合构造确认：板体候选换 ID，种子候选不换。当前 [§4.1 #6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:159) 与实现一致。

3. **PARTIAL · UAT 移动稳定性**  
   “同一份笔记里上下调序”仍漏掉**换父**：同文件中把 `子小节` 从 `父甲` 移到 `父乙`，ID 从 `bsa1-fbed…` 变为 `bsa1-8a13…`。UAT [第 21–27 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/验收单/UAT-CARD-G5-3-拆分稳定ID与diff契约-2026-08-30.md:21) 没有列出该例外；审查存档其实点名了“换父”，但随后仅改成“同一份笔记”，处置不足，[见第 480–482 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/codex-review-CARD-G5-3.md:480)。

4. **RESOLVED · 20/20 回归门**  
   #4、#9、#10 的独立测试均已存在并通过；104 条稳定 ID 测试的收集结果也确认它们实际被执行。

5. **RESOLVED · lint**  
   Ruff 0.15.9：后端两个测试文件 `ruff check` 与 `ruff format --check` 均绿；引擎单独检查也绿。

6. **RESOLVED · keyword 路径假绿**  
   被 diff 读取的畸形 JSON 与 out-dir 均改为中性名；诊断关键词只能来自 stderr/stdout。全量及参数化门均通过，相关注释与实现一致，[测试:1159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:1159)。

## 边界声明诚实性专项

### §4.1「会换 ID」10 条

当前口径下逐条实跑：

1. 改标题实词：换 ID。
2. 改祖先标题实词：子树换 ID。
3. 跨文件搬家：换 ID。
4. 调层级且改变祖先链：换 ID。
5. 删除前面的同名小节：后项 occurrence 位移并继承前项 ID。
6. 板改名：仅板体候选换，种子候选不换。
7. seed whole → section：换 ID。
8. 改非行尾时间戳：换 ID。
9. 前插同名小节：原项 occurrence 位移并换 ID。
10. 标题行加 HTML 注释：标题消失，子树祖先链改变。

**结论：10/10 实现事实与当前条目相符。** 但仍漏列“同文件换父”，它也是高频且确定会换 ID 的操作。

### §4.2「不换 ID」10 条

代表构造全部通过：纯行漂移、正文修改、唯一标题同父调序、编号/行尾时间戳、NFC/NFD 标题、空白空行、等价文件名、机器段刷新、节点池导致名称变化、祖先链不变的层级调整。

但字面仍有两处过宽：

- [§4.2 行号漂移](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:189) 应限定为“非结构性行增删”；插入标题或同名小节可能改变祖先链/occurrence。
- [§4.2 小节整体调序](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:191) 应限定为“同一父路径内、非歧义候选”。换父即换 ID，重复标题另受 §4.4 影响。

因此“测试构造 10/10”成立，但“文字边界没有漏项、没有说过头”不成立。

### §3.1、§4.4、§8.2、§十

- **§3.1 PASS**：代码 fence 与普通 HTML 注释改动都会改变指纹；Recent Activity、AUTO-GENERATED 刷新不改变指纹。声明与实现一致。
- **§4.4 PASS**：槽位身份、删除/插入后的 ID 改嫁、交换时 `changed×2`、JSON/warning/MD 红旗均相符；“只是契约约束、不是运行时强制”的纠正也准确。
- **§8.2 FAIL**：具体新增的 heading、board_file、scale gate、namespace、vault fingerprint 守卫均正确，但“只有每一处都自洽的伪品才落入信任边界”及其可执行断言不成立。
- **§十 PASS**：namespace、`ID_STABILITY`、`bsa2-` 前缀与 `_ID_RE` 必须一起升级的清单完整；“并非全部 ID 都变”的纠正准确。

## 本轮新发现

### HIGH · “自洽伪品”测试实际包含可检查的内部矛盾

契约声称真正的信任边界只有“改完后每一处都自洽”的伪品，[契约:478](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:478)。但对应测试：

- 基础候选是 `board-body-section`；
- 仅把 `stable_id_basis.file` 与 `source_anchor.file` 改成 `节点/根本不存在的来源.md`；
- 未同步 `basis`、顶层 `board_file` 和 `sources`；
- 重算 stable ID 后断言 `rc=0`，[测试:1269](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/backend/tests/skills/test_split_stable_id.py:1269)。

生产端明确定义 `board-body-section` 来自 `原白板/<board>.md`，种子 basis 才来自 `节点/`，[实现:710](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:710)。这无需读 vault 就能对账。因此该测试并非“真正自洽的伪品”，而是在把可检查不一致算进信任边界。

独立生产 CLI 复现目录：`/private/tmp/g53-r6-trust.7tbezb18`。以下均 `rc=0`：

- `board-body-section` 重绑到 `节点/不存在.md`，但 `sources` 仍只有原白板；
- `basis="invented-basis"` 并重算 ID；
- 标题不变但 `suggested_name/resolved_name` 协同伪造；
- 顶层 `id_stability="invented_v999"`。

真正完全自洽的标题伪造同样 `rc=0`，那一项才准确体现“不读 vault、无签名”的真实性边界。

此外，[§8.2“任一字段类型不对即拒绝”](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/docs/design/split-stable-id-contract.md:464) 也说过头：`id_stability=7`、`sources=7`、`board_sha256=[]`、`existing_node_pool_count=true` 四组均 `rc=0`，复现于 `/private/tmp/g53-r6-types.cxhh6rdh`。

### MEDIUM · 同文件换父未列入不稳定面，且被“调序不变”覆盖

复现于 `/private/tmp/g53-r6-reparent.i0x26cvl`：

- 文件始终为 `原白板/板A.md`；
- 只把子节从父甲移到父乙；
- 路径由 `主板/父甲/子小节` 变为 `主板/父乙/子小节`；
- ID 改变。

这既是 §4.1 漏列，也是 §4.2/UAT“同一笔记调序不变”的反例。

## 我实际跑了什么

- HEAD `eaf208ca3289a8caab62c1e8040b1fe53de4bc44`，分支 `card/t5-stableid`。
- 指定全量测试：**138 passed / 10 warnings / rc=0**，即 104＋34。
- 第 4 轮 11 组语义矩阵：**5 拒绝 / 6 rc=0**。
- 同层数标题伪造：`rc=1`，零产物。
- §4.1/§4.2 20 项生产行为矩阵及 §3.1 覆盖实验。
- 同文件换父、basis 枚举、file/basis/sources、名称、顶层字段类型专项探针。
- 当前字节 29 组变异反证：**29/29 变红**。
- 两份 manifest `shasum -c`、manifest 与递归文件集合对账、mutation 日志哈希复算。
- Ruff check/format check。
- 审查前后 `git status` 相同，六个被审核心文件无 tracked diff；未编辑仓库，未写真实 vault。`graphiti-canvas` 本会话不可用，未执行其记忆检索。


