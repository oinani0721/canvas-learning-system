# Codex 审查 · CARD-G5-3（第 4 轮 · 终裁）

## 裁决

**不通过**——P1、P2 已解决，当前测试和 manifest 全绿；但“类型正确且复算通过”的语义输入仍存在可复现 fail-open，契约的“整类收口”声明不成立。

## 三轮 PARTIAL 逐条复核

- **P1 · RESOLVED**  
  原第三轮 `/private/tmp/.../audit_round3.py` 复制到新临时目录原样复跑：**166/166 拒绝，rc=0 剩余 0 组**。`index`、`ambiguous_group_size`、`occurrence`、`line_start/line_end` 的布尔绕过均关闭；正整数及行区间守卫见 [split_preview.py:1077](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1077) 和 [split_preview.py:1147](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1147)。

- **P2 · RESOLVED**  
  悬空链接、有效链接、多引用文件、`0444` 文件、目录五种形态均 `rc=1`；拒绝前后 inode、mode、nlink、内容、链接目标、目录成员完全相同，第一份 JSON 均不存在。`lexists()` 回滚判据见 [split_preview.py:1693](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1693)。

- **P3 · PARTIAL**  
  原缺失的四态双产物已纳入；当前 manifest 覆盖 **10/10 个 `split-*` 产物**，两份 manifest 均全绿，`verify_manifests.sh` 最终 `rc=0`，绿证与实跑同为 **123 passed**。  
  但按本轮要求“覆盖 outputs 下全部文件”字面核对，`outputs/` 递归共有 11 个普通文件，manifest 只含 10 个产物，遗漏已跟踪的 `outputs/exam_boards/.gitkeep`。生成脚本实际是 `-maxdepth 1 -name 'split-*'`，并非注释宣称的“扫全目录、未来新增产物自动纳入”，见 [run_live_evidence.sh:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/run_live_evidence.sh:54)。

## 本轮新发现

### HIGH · “类型正确、绑定正确、复算正确”的语义层仍未收口

生产 CLI 复现：

- 只篡改新侧 `source_anchor.heading_path=["伪造标题"]`，ID/basis 不动：`rc=0`、`unchanged=1`、无 warning，伪造锚点进入 diff。
- 只篡改新侧 `scale_gate` 为 `{threshold:30,total_candidates:999,kept:1,over_threshold:false}`：`rc=0`、`unchanged=1`、无 warning，截断告警被静默压掉。
- 两侧顶层及 basis 的 namespace 协同改为 `split-anchor/v999`：同侧绑定、跨侧绑定、stable ID 复算全部通过，`rc=0`。
- 原 13 类复现矩阵仍有 `source_anchor.heading_path=[]`、空白 `vault_fingerprint="   "` 两类 `rc=0`。
- 同步伪造 `basis.file/source_anchor.file` 或标题路径并重新计算 stable ID，同样可通过。

根因是现有门只校验部分内部一致性：[split_preview.py:1191](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1191) 未绑定原文标题与归一化标题；[split_preview.py:1341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/canvas-vault/.claude/skills/board-split/scripts/split_preview.py:1341) 直接信任 `scale_gate`。

### LOW · 存档 mutation 日志未绑定当前字节

当前字节上独立复跑确为 **24/24 全红**，覆盖声明及“连同复算一起撤”的冗余说明是诚实的，见 [mutate_engine.py:231](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/mutate_engine.py:231)。  
但仓库内 [mutation-check.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-stableid/_bmad-output/审查/g5-3-evidence/mutation-check.txt:2) 记录的是旧 engine/judge 哈希，不是当前 `1b1379d0…` / `fea57bf3…`。

## 剩余边界是否已被诚实声明

1. **重复标题歧义、64-bit 截断碰撞、候选嵌套、LCS 最小移动集、时间戳行尾锚定**：声明与实现一致。
2. **规模门截断**：对引擎自产 preview 一致；但外部 JSON 的 `scale_gate` 自洽性未校验，可压掉告警，遗漏。
3. **写侧 TOCTOU、bind mount、准入后 I/O 半发布**：声明与实现一致；P2 五形态已通过。
4. **namespace 两跳**：对代码机制的描述属实；但没有说明“两侧协同重标仍可通过”，披露不完整。
5. **diff 不读 vault**：事实属实，但由此导致复算只能证明内部自洽、不能证明来源真实性。合法格式的假指纹、假行号、自洽重算后的假 basis 无法被识别，这一信任边界没有明确声明。
6. **守卫是否过严**：未发现。未篡改反面锚通过；另测板甲/板乙、`seed-note-whole` 回退、重名解析、歧义组、合法截断均 `preview rc=0 + diff rc=0`，结果符合预期。

## 我实际跑了什么

- 用户指定完整测试：**123 passed / 10 warnings / rc0**，实际为稳定 ID 89 条 + 存量 34 条。
- 原第三轮 166 组复现器：**166/166 拒绝**。
- 五种预置目标独立文件系统快照矩阵：**5/5 原样保留**。
- 合法输入矩阵：不同板、种子回退、重名、歧义组、截断全部通过。
- 语义篡改矩阵及单侧篡改矩阵：上述 fail-open 均已复现。
- 在 `/private/tmp` 的镜像目录运行当前 `run_mutation_check.sh`：**24/24 变红，rc0**。
- `verify_manifests.sh` 最终：两份 manifest 全绿、123=123、`rc=0`。
- 递归枚举 `outputs/`：11 个普通文件；其中 10 个 `split-*` 产物全部入 manifest。
- 最终锚点：HEAD `cbb20afb…`，engine `1b1379d0…`，judge `fea57bf3…`，contract `14eb0151…`。
- 审查中证据文件曾被外部并发刷新；上述结论已按最终字节重新核验。本次未编辑仓库，也未写真实 vault；审查前后 `git status --short` 项目集合一致。


