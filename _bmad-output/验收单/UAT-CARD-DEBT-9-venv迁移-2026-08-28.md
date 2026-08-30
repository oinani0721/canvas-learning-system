# 验收单 · CARD-DEBT-9 feature venv 按 G-DEP-001 迁移（环境卡）

> **批次**: BATCH-2026-08-28-第五批 · 车道 S4（第 0 小时先行卡）
> **分支**: `card/s4-venv`（不 push，等你验收）
> **日期**: 2026-08-28（v3 = Codex 二轮终裁后定稿）
> **一句话**: 给本车道的 Python 依赖环境做了一次「搬家式大扫除」——旧环境里
> 残留着一个已下架的视频库（moviepy），它和安全修复版图片库（pillow 12）互相声明不兼容
> 却硬凑在一起，属于「原地升级永远洗不掉」的暗坑。本卡整个环境推倒重建：
> 依赖来自与 CI 同一份 requirements.txt + CI 同名单测试三包，另补两个仅本地工作流需要的包
> （ruff/pytest-mock，CI 不装；本机 Python 3.14 vs CI 3.11/3.12——均如实区分，不称完全同构）。

---

## 一、这对你意味着什么（用户视角）

1. **本车道所有测试和回归跑在干净环境上**：moviepy/pillow 的冲突组合
   （G-DEP-001 一年前预言的坑，本次实测坐实）已彻底清除，依赖安全扫描在
   **零豁免**条件下输出「No known vulnerabilities found」。
2. **顺手抓出三个环境暗坑并闭合**（详见第三节 Codex 处置表）：
   lint 工具 ruff 是散装的、测试要用的 pytest-mock 从来没装过（新旧环境都缺）、
   重建配方之前没有写下来——现在配方完整落在 G-DEP-001 档案里，照抄就能复现。
3. **旧环境没有删，只是改名封存**：`backend/.venv-pre-gdep001-backup` 原样保留可回滚。

## 二、⛔ 两个待你裁决的点（不急，但要你拍板）

| # | 裁决点 | 背景 |
|---|---|---|
| 1 | **feature-obsidian-hybrid-dev 那份旧环境要不要也照此迁移？** | 总账 v2 的 DEBT-9 档案节写的迁移对象是 feature-obsidian-hybrid-dev worktree，而第五批开跑手册给本车道的 /goal 限定「只动本 worktree venv、其余车道 venv 不碰」。本卡按 /goal 执行于 card/s4-venv；feature worktree 的环境实测**仍是 moviepy 2.2.1 + pillow 11.3.0**（原样未动）。要迁的话照 G-DEP-001 里新写的配方一小时内可完成（Codex 一轮 BLOCKER 定性为「对象口径需裁决」，非本卡执行错误） |
| 2 | **备份目录何时清理？** | 新环境用一阵子没问题后，回一句「备份可以清了」，Claude 走合规路线处理 `backend/.venv-pre-gdep001-backup` |

## 三、技术判据（Claude 已全部代跑 · 你不用跑任何命令）

| 裁判（goal 完成条件 c） | 结果 |
|---|---|
| 全量测试收集 `pytest tests/ --collect-only -q` | **6857 tests collected，exit 0，无 Interrupted**（判据线 ≥6857 达标；收集≠运行，如实口径）✅ |
| `pip-audit -r requirements.txt`（零豁免） | **No known vulnerabilities found**（Codex 联网独立复核同结论）✅ |
| 抽样套件 `tests/unit/test_fsrs_manager.py` | **37 passed** ✅ |
| 抽样套件 `tests/unit/test_check_readme_claims.py --noconftest` | **120 passed** ✅ |
| `pip show pillow` | **12.3.0** ✅ |
| `pip show moviepy` | **Package(s) not found** ✅ |
| `pip check`（总账判据） | **No broken requirements found** ✅ |

### 迁移过程记录（完成条件 a）

| 步骤 | 实况 |
|---|---|
| 迁移前实测 | 旧 venv = **moviepy 2.2.1 + pillow 12.3.0 共存**，`pip check` 报 `moviepy 2.2.1 has requirement pillow<12.0`——即 G-DEP-001 预言的「原地 pip install 升了 pillow 但卸不掉 moviepy」未验证组合（总账勘探时为 pillow 11.3.0，期间有过一次原地升级，恰好演成坑位描述的形态） |
| 备份 | `mv .venv .venv-pre-gdep001-backup`（guard-hook 禁 rm/pip uninstall，走 MEMORY 记录的 mv+新建合规路线；确认为真目录非符号链接，未触碰其他车道 venv） |
| 重建 | Homebrew Python 3.14.4（与旧环境同 base 解释器）新建 → `pip install -r requirements.txt` 成功（exit 0） |
| 补装（最终四包） | hypothesis 6.165.10 / pytest-bdd 8.1.0 / schemathesis 4.25.2（CI `.github/workflows/test.yml:71` 同名单；pyproject dev extras 五项核对全覆盖）+ **ruff 0.15.9**（lefthook 硬门，见处置表 HIGH-1）+ **pytest-mock 3.15.1**（存量闭包缺口，见处置表 MEDIUM-1） |
| 缺包探针边界 | 名级对比旧 226 包 vs 新 venv：真缺失为 moviepy 家族（有意移除）与 mutmut/vulture/pydeps（按需散装工具：mutmut-targeted.sh 调用带 `\|\| true`、vulture 所在 hook 未在 settings 注册、pydeps 无活调用——如需回补按需散装，UAT 如实登记为降级项）；收集探针只能抓 import 面缺包，fixture 运行时缺口（pytest-mock）靠 Codex 对抗审查抓出 |

### 完成条件 b + d（文本产物）

- `backend/.gitignore`（**新建**，本卡独占合同点，全批他车道禁改）：`/.venv-pre-*` 忽略模式
  （前导 `/` 锚定 backend 根，不递归误伤子目录——Codex LOW-1 收窄）；实测 `git check-ignore` 命中备份目录
- `docs/known-gotchas.md` G-DEP-001 条目：修复状态列追加「**✅ 已迁移（范围=card/s4-venv）**」段
  （含完整重建配方 + 迁移对象口径 + 裁决点指引）；左列陈旧回滚指引（`.venv-pre-b1-backup` 不在本
  worktree）已修正；moviepy 复活时一并处理清单补入 EPIC-35:258 与 35.7.story.md:642 两份冲突文档

## 四、Codex 对抗审查处置表（round-1 发现 → round-2 终裁）

| 级别 | 发现 | 处置 | round-2 裁定 |
|---|---|---|---|
| BLOCKER-1 | 迁移对象不唯一（总账 v2 写 feature worktree，/goal 写本 worktree） | **移交裁决点 #1**（硬边界禁碰他车道 venv，本卡无权代决）；gotcha 已写明口径与 feature worktree 实测现状 | **CLOSED（仅本卡范围）**——移交可接受；上位总账 DEBT-9 目标保持 OPEN，不得标记总账完成 |
| HIGH-1 | ruff 是 lefthook 硬门但配方无声明，重建即丢 | **已闭合**：ruff==0.15.9 钉版补装 + 完整配方写入 G-DEP-001 | **CLOSED** |
| MEDIUM-1 | pytest-mock 缺装（tests 请求 mocker fixture，新旧 venv 均缺） | **已闭合**：pytest-mock 3.15.1 补装（对齐根 requirements.txt:182）；反例复跑 mocker error 消失，残留 1 failed 经备份解释器复跑确认为存量非回归 | **CLOSED** |
| MEDIUM-2 | G-DEP-001 左列陈旧回滚指引（.venv-pre-b1-backup 不存在于本 worktree） | **已闭合**：左列改写指向现行备份 | **CLOSED** |
| MEDIUM-3 | EPIC-35:258 / 35.7.story.md:642 两份完成态文档仍无条件 `pip install moviepy` | **登记移交**：写入 G-DEP-001 复活时一并处理清单（历史文档不在本卡合同点） | **NOT-CLOSED（移交合格、非本卡阻断）**——仓库矛盾本体待后续卡消除 |
| LOW-1 | `.venv-pre-*` 模式递归过宽 | 收窄为锚定 `/.venv-pre-*`，check-ignore 复验通过 | **NOT-CLOSED（接受残留）**——round-2 建议再窄至 `/.venv-pre-*-backup/`，本卡不采纳：goal 完成条件 (b) 钦定字面模式为 `.venv-pre-*`，进一步偏离将不满足判据原文；backend 根同前缀普通文件被忽略的风险经评估可接受（无 tracked 命中，约定名恒为目录） |
| LOW-2 | 收集≠运行、CI Python 3.11/3.12 vs 本机 3.14、「依赖清单与 CI 同一份」措辞不准（ruff/pytest-mock 非 CI 安装面） | v3 措辞修正：明示两包为 CI 不装的本地工作流补装 | **CLOSED（v3 修正后）** |
| LOW-3 | 工作树状态项不止两个文件 | **非问题**：另两个是本卡交付物（审查存档+验收单），同 commit 入 git | **CLOSED** |
| LOW-4 | mutmut/vulture/pydeps 降级未披露 | **已闭合**：本单「缺包探针边界」行如实登记 | **CLOSED** |

> **round-2 总裁决**（全文见审查存档）：残留 BLOCKER/HIGH 无；**可合并**，但只能表述为
> 「S4 worktree 迁移完成、feature worktree 迁移已移交待裁决」，不得关闭上位 DEBT-9 总账目标。

## 五、验收步骤（1 分钟）

1. 看第三节 7 行裁判表——全绿即环境迁移达标
2. 对第二节两个裁决点各回一句话（feature worktree 迁不迁 / 备份何时清）

## 六、批注区

> [!question]+ 你的疑问写这里
>

## 七、技术引用（给 Claude 读的）

- Codex 审查存档: `_bmad-output/审查/codex-review-CARD-DEBT-9.md`（round-1 原文；处置见本单第四节）
- 坑位档案: `docs/known-gotchas.md` G-DEP-001（:122，含完整重建配方）
- 卡定义: 总账 v2 DEBT-9 档案节 + 第五批开跑手册 §二 DEBT-9 决议（commit 5b9c00cf，本分支未合入，经 git show 读取）
- 迁移证据（scratchpad，session 内）: old/new-venv-freeze.txt、pip-install-log.txt、collect1.txt
