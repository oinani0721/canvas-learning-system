# g5-1-evidence — 触发矩阵负例回归 + board-recap 正例实跑证据包 v3

> **批次**: BATCH-2026-08-27-第四批 / CARD-G5-1 · 执行日 2026-08-27
> 矩阵文档: `_bmad-output/研究/2026-08-27-G5-1-信息收集四类触发矩阵.md`（v3·登记簿 4 条）
> 断言表: `backend/tests/regression/skill_trigger_matrix.yaml`（checker v3 9/9 PASS · 18 类变异负控全抓）
> **审查链**: 一轮 3 BLOCKER + 4 HIGH（codex-review-CARD-G5-1.md）→ v2 加固+全量重放 →
> 二轮复核（codex-review-CARD-G5-1-round2.md）→ **v3 加固（本版）+ 第三轮全量重放**：
> manifest 纳入 .claude/skills 施工面 + FIFO/socket + symlink 目标；judge 加 sidecar 话语绑定 +
> result 恰 1 且为末事件 + B1 双条件不分形状；checker 锁死 real_floor + 归属锚语义分类；变异负控 18 类。

## 终判（v3 判据 · 第三轮全量 fresh 重放 · final-verdict.txt）

| 面 | 结果 |
|---|---|
| 负例 N1/N3/N5/N7/N8/N10 | **全门通过**（J0 完整性+sidecar 绑定 + J1 三证据面零命中 + J2/J3 前后一致） |
| 负例 N2/N9 | 全门通过（本轮干净；v2 轮 N2 的代行写侧已登记, 日志留档 logs-v2-archive/） |
| 负例 N6 | ⛔ **误触发复现（2/2 轮）**：`Skill(study-plan)`——用户全局环境 skill，vault/outputs 零变化 |
| 负例 N4 | ⛔ **实测误触发 board-recap**（无斜杠自然语言「回顾一下特征值与特征向量」被显式 Skill 调用并执行至覆盖 outputs 审计快照）。**存档 2 份采样：1 净（v2 轮）+ 1 误触发（v3 重放）**；另有 2 次早期采样观察为净但日志被后续重放覆盖未存档，不计入分母——**全卡最重要发现**，直接支撑矩阵 §三 待拍板 |
| 正例 B1 | 触发确认（命令展开形状：Bash 实跑 recap_scan.py ×2 + **VERIFY PASS**）；写侧足迹**恰为** 3 个 outputs/ 白名单文件（双条件+outputs-only diff 机械核） |
| 正例 B2 | 触发确认（终版带括弧样本显式 `Skill` 调用）+ 无参选板询问（headless 无 AskUserQuestion → 文本枚举降级如实标注）；**存档 5 份采样：2 显式 + 3 行为性**（另有 2 次显式调用的早期采样因日志被后续重放覆盖未存档，不计入）→ 漂移登记 |

**判读**：机械终判 exit 1 且 N4/N6 红行如实可见——登记项不被粉饰。负例回归三轮共抓出
4 条真实发现（N4 误触发 / N6 误触发×2 / N2 代行写侧 / B2 形式化漂移），全部只登记不改 skill。

**过程诚实记录**：第三轮首跑时 N4 窗口曾被**施工方自己的并发活动**污染（重跑进行中同时 bump 了
引擎版本——v3 manifest 恰好抓个正着，反证新网面有效）；随后冻结一切并发单独重放 N4，
重放才暴露真误触发。v2 轮的 N 组日志整体归档 `logs-v2-archive/`（N2 代行写侧的原始证据在内）。

## 登记的四条真实发现（详见矩阵文档 §五）

1. **N4 → board-recap 被自然语言误触发**（⛔ 最重要：无斜杠近失误语句在存档 2 采样中 1 次触发并执行到
   写审计快照——斜杠约定非模型级强制，§三 待拍板必须计入此实证）
2. **N6 → study-plan 误触发**（两轮复现；用户全局 skill 干扰面，建议 G5-8 ROUTING 验收一并复核）
3. **N2 → headless 代行写侧**（写 2 份思维导图 + 在 .claude/skills/board-split/scripts/ 擅写
   export_mindmap.py——Codex 二轮从日志抓出，v3 起该面已入 manifest；产物全部移出留档）
4. **B2 → 触发形式化漂移**（裸 /board-recap **存档 5 份**：2 显式 / 3 行为性，`logs/B2*.jsonl`；
   终版为带完整 manifest 括弧的显式调用样本。⚠ 计数纪律教训（Codex 三轮抓出）：另有 2 次显式调用
   的采样因日志被后续重放覆盖而未存档——计数一律以存档为准，未存档观察只作旁注不进分母）

## 判据与两个环境事实（如实登记）

- **判定三面**（负例）：J1 触发证据 = 显式 Skill 调用 / `Launching skill:` 结果行 / 命令展开痕迹
  （`<command-name>` / `commandName`）三面全查；J2 outputs 清单；J3 内容面 manifest
  （文件 sha256 + 目录/symlink 清单，v2 起含 dirs/links 段）。J0 会话流完整性
  （零坏行 + 恰 1 init 且 cwd 绑定本 vault + result 落幕 + session 唯一且跨日志零复用）。
- **触发形状分裂**：带参斜杠可走 CLI slash 展开（无 Skill 工具调用，以 Bash 实跑 skill 脚本 +
  VERIFY PASS 双条件为指纹）也可走显式 Skill 调用——两种形状 judge 都接受且判据写死在 docstring。
- **headless 工具面无 AskUserQuestion**（init.tools 实证）：无参选板询问以文本枚举降级；UI 本体须交互环境实测。
- vault SessionEnd hook 在 backend 离线时会写 `.claude/hooks/pending_archives.jsonl`（hook 基础设施，
  不在内容面口径——D5 先例同口径）；headless agent 可能执行只读 Bash 或写 /tmp（vault 外侧效应，
  judge 逐条列出 Bash 次数供人工复核）。

## 文件清单

| 文件 | 内容 |
|---|---|
| `run_headless_negatives.sh` | 负例 runner v3（manifest 含 .claude/skills 施工面 + dirs/links/special + symlink 目标 + sidecar meta） |
| `run_headless_positives.sh` | 正例 runner v3（B1 全链 / B2 无参; manifest 同 v3 网面） |
| `judge_headless_logs.py` | 机械裁判 v3（J0 完整性+终局唯一+sidecar 绑定 / J1 三证据面 / B1 双条件不分形状） |
| `mutation_negative_controls.py` + `mutation-verdict.txt` | checker「能红」变异负控（18 类全抓 + 对照组，可复跑） |
| `negatives.tsv` | 负例清单（id + 话语，从 YAML 抽取） |
| `logs/N1..N10.jsonl` | 负例完整会话流（v3 第三轮重放）；`logs-v2-archive/` = v2 轮 N 组日志（N2 代行写侧原始证据） |
| `logs/B1.jsonl / B2.jsonl` | 正例终版会话流；`logs/B2-attempt{1,2,3,5}*.jsonl` = 形式化漂移采样留档 |
| `manifests/*` | 逐条运行前后 manifest（内容面/outputs/`*-meta.json` sidecar；B2 attempt1 括弧另存 `*-attempt1.txt`） |
| `final-verdict.txt` | 机械终判（登记项显示为红行，exit 1 如实） |

## 复跑方式

```bash
bash _bmad-output/审查/g5-1-evidence/run_headless_negatives.sh
bash _bmad-output/审查/g5-1-evidence/run_headless_positives.sh
python3 _bmad-output/审查/g5-1-evidence/judge_headless_logs.py --positive B1 --positive B2
backend/.venv/bin/python3 _bmad-output/审查/g5-1-evidence/mutation_negative_controls.py
```

注意：B1 会在 worktree `canvas-vault/outputs/` 落当日回顾（测试产物不入 commit，D5 同口径）；
同日复跑触发 board-recap 幂等询问属预期；headless agent 行为有随机面（N2/N6/B2 的登记即来自此），
复跑结果按当轮实况判读，不与本包逐字节对齐。
