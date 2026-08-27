# g5-2-evidence — 拆分建议 preview 引擎（只读）真实板取证 v3

> **批次**: BATCH-2026-08-27-第四批 / CARD-G5-2 · 执行日 2026-08-27
> 被测物: `canvas-vault/.claude/skills/board-split/scripts/split_preview.py` **v3**（scripts-only，无 SKILL.md）
> 裁判: `backend/tests/skills/test_split_preview.py` **34 条全绿**
> 审查链: 二轮 0 BLOCKER + 6 HIGH（codex-review-CARD-G5-2.md）→ v2 加固 → 三轮复核
> （codex-review-CARD-G5-2-round3.md：H5 RESOLVED、5 项 MEDIUM RESOLVED、新抓 H1 次序/H2 目录级/
> 偏差5/证据绑定）→ **v3 加固（本版）**。

## 先红后绿履历（累计四轮）

1. 首轮 14/14 全红（被测物不存在；当场修掉一处裁判假绿——脚本缺失时拒绝类断言空洞通过）→ 实现后 14 绿
2. 真实板实测暴露 2 缺陷（注释续行/hr 凑正文、Fundamentals 无 ##+ 小节漏拆分源）→ 先红 2 测试 → 修复 16 绿
3. Codex 二轮 6 HIGH → 新增 15 条对抗测试（先验证「能红」）→ 引擎 v2 → 31 绿
4. Codex 三轮 → 引擎 v3 + 3 条新测试（祖先 symlink **零写**断言 / 目录级 symlink vault 拒绝 /
   反事实固化为常驻测试 + JS 空白负例集）→ **34 绿**

## v3 引擎加固（对应 Codex 三轮发现）

| 三轮发现 | 处置 |
|---|---|
| H1 mkdir 先于 symlink 检查（拒绝但已写） | 先验祖先链 `assert_symlink_free(out_dir.parent)` **再** mkdir；测试断言物理目标处零残留 |
| H1 nlink 检查与 open 非同一 FD | 单 FD 流程：O_NOFOLLOW open（无 O_TRUNC）→ fstat 验 nlink → ftruncate → write，零换身窗口；祖先整体替换竞态为声明的用户态边界 |
| H2 目录级 symlink 逃逸 | 原白板/节点 目录本身 symlink → 整体拒绝；板/种子文件 realpath 必须在 vault 物理树内（`_contained_regular_file`）；TOCTOU 声明 |
| H3 clean_heading 未声明偏差 | 升为显式偏差 #5（输入预处理，等价性宣称范围=slug 函数本体） |
| H4 证据未绑当前引擎字节 | `run_live_evidence.sh`（set -x 全命令回放+逐步 rc）重做取证，engine digest 与产物 digest 同一转录内绑定 |
| H6 AUTO fixture 静态质疑 | 反事实固化为常驻测试 `TestCounterfactualStripping`（AUTO 开闭标记是单行注释，富假小节不在注释内——实证 stripping 失效时三类 fixture 全红，静态推断不成立有测试为证） |
| MEDIUM 读三次/sha 不同版本 | 每来源文件只读一次，sha 对同一份字节计算 |
| MEDIUM collector 目录 symlink | 目录 symlink 按 L 行记录并带 target |
| MEDIUM 标记不严格配对 | 维持确定性吞到 EOF 语义（docstring 声明的设计立场：宁可少判候选不误判） |
| LOW JS 空白负例 | U+0085/U+001C 非空白负例入测试 |

## v2 引擎加固存档（对应 Codex 二轮发现）

| 发现 | 处置 |
|---|---|
| H1 写边界无物理 fail-closed | out-dir 路径全程无 symlink 组件（realpath≠词法即拒）+ 单级 mkdir 不造祖先链 + 既存目标 nlink>1 拒绝 + O_NOFOLLOW 原子写（消 TOCTOU）；bind mount 不可判定→docstring 如实声明 |
| H2 板内 seed 名越界读 | Concepts 成员名同套 containment，越界/symlink 种子**跳过留痕**（JSON sources.skipped + MD ⛔ 行）；板文件 symlink 拒读 |
| H3 slug 等价性缺口 | 空白集改 **ECMAScript 口径**（含 U+FEFF；弃 Python \s）；词边界阈值按 **UTF-16 code unit** 比较（Codex 反例 😀+18a+-+25b 已入测试）；README 偏差清单改为完整四条（见下） |
| H4 live 0 修改宣称过度 | 新采集器 `collect_live_baseline.py`：live vault **全部文件** sha256+size+mtime_ns+ctime_ns+mode+nlink+symlink 目标+目录集合，确定性 TSV；命令/运行日志/引擎与产物 digest 全部入包 |
| H5 非法板名测试空洞 | 测试钉具体诊断（「非法字符」vs「不存在」两路可区分）+ 拒绝路径零产物 |
| H6 剥离测试假绿 | 三类对抗 fixture（假小节只有对应标记能排除）+ strip_generated 单测 + 反事实验证 |
| MEDIUM 注释标题截断/伪造 | 注释行不参与小节切分与派生重叠证据（fence 内 callout 亦不算 overlap） |
| MEDIUM 9+ 重名渲染 | conflict_unresolvable 候选**停用**展示性 diff（TS 同场景 throw） |
| MEDIUM 免责声明字面 | 措辞改为「未修改任何**既有** vault 文件（唯一写入 = out-dir 两产物）」 |
| LOW 规模门/README 复跑 | 测试钉「恰为文档序最前 N 个」名单；复跑命令改为仓库根单目录执行 |

## slug 与 TS 真相源的显式偏差（完整清单, 无未声明项）

1. 空输入 fallback：TS 时间戳（非确定）→ 锚点 sha1 前 6 位（受「同输入二跑 diff 空」硬门）
2. 重名判定 NFC 归一（TS existsCheck 字节精确）——macOS NFD 落盘不归一会漏报，preview 侧自觉增强
3. preview 内候选互撞检测（claimed 集合）为 TS 无对应物的确定性补充
4. TS 9+ 重名 throw → preview 标 conflict_unresolvable 并停用该条展示 diff
5. 输入预处理：slug 前先 clean_heading() 剥离标题编号与时间戳标记（TS 管道无此步）——
   等价性宣称范围 = slug 函数本体，不含此预处理（引擎 docstring 同步声明）

## 真实板取证（G5-2 (d) · v3 引擎产物）

| 板 | vault | 候选 | 要点 |
|---|---|---|---|
| CS188 lecture 2（富样本） | **live** 主仓 canvas-vault | 27 | 全部来自种子 `节点/lecture 2.md` ##/### 小节；派生重叠精准命中 7 处 `已派生为` callout 所在小节 |
| 特征值与特征向量 | **live** 主仓 canvas-vault | 1 | Fundamentals 无 ##+ 小节 → 整篇回退候选；重叠命中现网金样本节点 `Eigenvalues-are-special-vectors-that-sat` |

产物写**本 worktree** `canvas-vault/outputs/`（测试产物不入 commit）；产物 sha256 见 `engine-and-products.sha256`。

## live vault 零修改证据（v3 口径, 精确表述）

- `live-full-before/after.tsv`：live vault **全部文件**（324 个, 含 .obsidian 等二进制）逐一
  sha256+size+mtime_ns+ctime_ns+mode+nlink + 全部目录 + symlink 目标——两板 v3 运行前后 **diff 为空**
- `live-run-log.txt`：采集与运行的完整命令回放；`engine-and-products.sha256`：引擎与 4 份产物 digest
- 早期口径留档：`live-sha-before/after.txt`（md/yaml/json 284 文件）+ `live-stat-before/after.txt`
  （全文件 size+整秒 mtime）——覆盖早期引擎运行窗口，diff 亦为空
- **判定边界（如实声明）**：本证据 = 所记录投影在采集窗口内**零净差异**；atime 不采集不断言
  （只读扫描在 atime 挂载上本身会更新访问时间）；before/after 快照无法排除窗口内先改后恢复；
  xattr/ACL/owner 不在判定面。宣称止步于此，不外推。

## Codex 审查过程留痕

- 一轮：Codex 实弹探测 **symlink out-dir 重定向**——被引擎预检当场拒绝（stderr「✗ 输出目录本身是
  symlink, 拒绝写入」，零写入）。该轮随后被 OpenAI cyber 内容过滤器误拦中断（已知坑：审查提示词
  含攻击构造措辞会触发），未产出报告。
- 二轮（静态审阅措辞重发）：正式报告 `codex-review-CARD-G5-2.md`（0 BLOCKER + 6 HIGH），v2 处置见存档表。
- 三轮复核：`codex-review-CARD-G5-2-round3.md`（H5 与 5 项 MEDIUM 判 RESOLVED；新抓 4 面）→ v3 处置见首表。

## 复跑方式（仓库根目录执行）

```bash
backend/.venv/bin/pytest backend/tests/skills/test_split_preview.py -q    # 34 passed
python3 canvas-vault/.claude/skills/board-split/scripts/split_preview.py \
  --vault /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault \
  --board "CS188 lecture 2" --out-dir canvas-vault/outputs
python3 _bmad-output/审查/g5-2-evidence/collect_live_baseline.py \
  /Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault > /tmp/live-check.tsv
```
