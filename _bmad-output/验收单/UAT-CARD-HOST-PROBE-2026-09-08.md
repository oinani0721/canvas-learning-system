# UAT — CARD-HOST-PROBE 三家二线宿主实测表

> `[BATCH-2026-09-07-第十三批 / CARD-HOST-PROBE]` · 车道 `card-u4-hosts` · 2026-09-08 · 零代码卡

---

## 1. 🎯 一句话目标

搞清楚除了 Claude Code，另外三个 AI 助手（Codex / OpenCode / dsh）能不能在你的课程库里认出你写好的那套技能、连上你的学习后端——**每一条都真的去试一次**，而不是照着说明书猜。

---

## 2. 📖 你的视角

作为一个想把这套学习系统交给不同 AI 助手来用的人，
我想知道**哪一个助手现在就能用、哪一个还差什么**，
以便下一步只给真正能用的那个开绿灯，不把时间花在注定跑不通的方向上。

---

## 3. 🖥️ 交互流程

```
新建一个空白课程库（干净的，跟你现有的资料完全隔开）
   ↓
往里放：一份示范技能、两份「故意写错名字」的技能、四个助手各自的设置文件
   ↓
让四个助手依次打开这个课程库
   ↓
每个助手回答两个问题：① 你看见了哪些技能？ ② 你连上学习后端了吗？
   ↓
把每个答案都存成一份可回看的记录，写清楚「试过了，结果是这样」
   ↓
最后回头检查：你现有的资料、你原来的设置，有没有被动过
```

---

## 4-A. 🤖 Claude 已代验（技术层，全部已跑完并带证据）

| # | 断言 | 结果 | 证据 |
|---|---|---|---|
| 1 | 探针 vault 无 `.git` 祖先（P0 地基） | ✅ `fatal: not a git repository`，rc=**128**；正控：车道树同命令 rc=0 ⇒ 判据非恒真 | `evidence-host-probe/P0-skeleton-20260908T065021.txt:5,8` |
| 2 | 四家 CLI 版本与勘探值一致 | ✅ dsh 0.1.1-rc.2 / codex-cli 0.153.3 / opencode 1.18.27 / claude 2.1.263，逐字一致 | `evidence-host-probe/versions-20260908T064311.txt:8-14` |
| 3 | 后端健康检查 | ✅ `http_code=200`（LISTEN 127.0.0.1:8011）⇒ P2/P5/P7/P9 运行期面可测 | `evidence-host-probe/backend-health-20260908T064311.txt:2` |
| 4 | dsh `--patch` 注入 MCP 生效（四态，判据绑字面量） | ✅ 无 patch 命中 0；8011 态 `id: mcp-cls`/`url…8011`/`failOnStartupError: true` 各 1；8999 态命中 8999；skills patch 态 `disabled: false` | `evidence-host-probe/P1a-dsh-dumpconfig-r2-20260908T065219.txt:15-38` |
| 5 | `failOnStartupError: true` 断连对照**真会说话** | ✅ 8999+`true` ⇒ rc=**1** 自行退出 + `ECONNREFUSED 127.0.0.1:8999`，错误链落到 `dsh-mcp-client/lib/index.js:782`（MCP 客户端层，非 profile 加载层），且**无** `dsh web:` 行 | `evidence-host-probe/P2b-dsh-mcp-8999-failtrue-20260908T065518.txt:11` |
| 6 | 缺省 `false` 的**假绿面**实证 | ✅ 8999+缺省 ⇒ 打印 `dsh web: …:55546`、rc=142，与 8011 正常态**外部行为逐字同形**，但 MCP 未连上 | `evidence-host-probe/P2c-dsh-mcp-8999-faildefault-20260908T065544.txt:5` |
| 7 | `--dump-config` 不建立 MCP 连接 | ✅ 死端口 + `true` 仍 rc=0；命中数与端口存活无关（8011/8999 同为 1、无 patch 为 0，经验伪锚排除 `failOnStartupError` 自匹配）；8999 无监听由 `curl rc=7` 独立自证 | `evidence-host-probe/P1c-dumpconfig-no-mcp-connect-20260908T065401.txt:28` |
| 8 | 白名单工具可见且可调（全卡唯一一次工具调用） | ✅ `tools/list` 返回 6 个只读工具含 `check_backend_health`；实调返回 `isError=False`、1 个 content 块 | `evidence-host-probe/P2e-mcp-tools-list-20260908T065850.txt:15` / `evidence-host-probe/P2f-mcp-health-call-20260908T065913.txt:9` |
| 9 | Claude Code 两种软链形态都被扫（P4 两态） | ✅ 整目录软链 `project: 3`（三个都列出）/ 条目级软链 `project: 1`（只列 probe-skill）；反假阳性：文件工具全禁 + `permission_denials: []` + `num_turns: 1` | `evidence-host-probe/P4a2-claude-skills-debug-20260908T070258.txt:5,8` / `evidence-host-probe/P4b-claude-skills-symlink-entry-20260908T070335.txt:15` |
| 10 | Claude Code 项目级 MCP 状态 | ✅ 条目被读到、类型识别正确，状态 `⏸ Pending approval`（不自动启用）；负控假名零出现 | `evidence-host-probe/P5-claude-mcp-list-20260908T070048.txt:28,31-33` |
| 11 | ⛔ **Codex 沙箱两层归位 —— 该结论已撤销** | ⛔ Codex 复核指出三个「拒绝格」无实际写入返回。整改实验证实：四格中**只有「成功」那格有执行事件**，三个拒绝格 `command_execution` **全为 0**；换成「必须实际运行」的提示词重跑，模型仍在零执行事件下**编造**完整命令输出（含纯读命令 `ls -d .` 的结果）。✅ 仅保留「可写目录确实可写」；⚠️ 「read-only 是否拒绝」「隐藏目录是否另有规则」降级为未证明 | `evidence-host-probe/P6ef-codex-selfreport-not-executed-20260908T074037.txt` |
| 12 | Codex 项目级 MCP 未被读取 | ✅ 条目数 8 == 用户级段数 8，本卡自建条目零出现 | `evidence-host-probe/P7-codex-mcp-list-20260908T070457.txt:20-22` |
| 13 | OpenCode 双位置**不重复** + MCP 自动连 + 三根**真**被扫 | ✅ 同名 skill 只出现 1 次；`✓ canvas-learning-mcp connected` 与 `✗ probe-dead-mcp failed`（8999 负控）两状态不同 ⇒ 真去连非回显。**送审后自查补做 P8-d**：各根放独有名字 skill，把「三处都读」从推断升为直证（Codex 独立提了同一条 HIGH-4，两处互证） | `evidence-host-probe/P8-opencode-20260908T071157.txt:9,36` / `evidence-host-probe/P8d-opencode-root-proof-20260908T073003.txt` |
| 14 | 后端 `/mcp` 两层归位 | ✅ POST `initialize`=200；旧式 SSE 端点 `/sse`、`/mcp/sse`、`/messages` 全 **404**；GET `/mcp` 无会话标识=400 `Missing session ID`、带会话标识则保持流（非拒绝） | `evidence-host-probe/P9-backend-mcp-http-vs-sse-20260908T065732.txt:7,29` / `evidence-host-probe/P9b-sse-rejection-layer-20260908T065803.txt:15,19-22` |
| 15 | 三家认根对照 + 跑后零污染 | ✅ Claude Code 与 OpenCode 都把 worktree 的 `.git` **文件**当项目根、条目数同为 **15**（交叉印证）；跑后 `git status --porcelain -- canvas-vault/` = **0 行** | `evidence-host-probe/P10c-claude-root-20260908T071420.txt:10-11` / `evidence-host-probe/P10d-post-check-20260908T071449.txt:4` |
| 16 | live vault 零写入 | ✅ `find -newer sentinel` = **0** | `evidence-host-probe/closeout-final-20260908T071818.txt` |
| 17 | 零代码门 | ✅ `git diff --stat --no-color da690bf8 HEAD -- . ':(exclude)_bmad-output'` = **0 行**（用 `':(exclude)…'`，非 zsh 下会假绿的 `':!…'`） | `evidence-host-probe/closeout-final-20260908T071818.txt` |
| 18 | 实测表自检 | ✅ 三态字样 31（需 ≥11）/ 证据引用 36（需 ≥11）/ 敏感字样 **0** / 引用文件 0 MISS | 本单 §7 |
| 19 | ⛔ **禁写面 (i) 阻断项（未通过，如实登记）** | ⛔ `~/.codex/config.toml` sha 变化。根因 = `codex exec --sandbox workspace-write` 追加 `[projects."<dir>"]` trust 记录，**非本卡编辑**；正控 r2（workspace-write ⇒ 写入）/ 负控 r1（read-only ⇒ 不写）/ 对照（`[mcp_servers.*]` 恒 8）三证齐全。**本卡不自判放宽，提请主 session 裁定** | `evidence-host-probe/causal-codex-writes-config-r2-20260908T071710.txt:20-22` / `evidence-host-probe/closeout-final-20260908T071818.txt:13` |

| 20 | *(送审后自查补做)* OpenCode 三个 skills 根**真**被扫 | ✅ `.opencode/skills` 下放独有名字 `opencode-only-skill` ⇒ 被枚举到且 location 指向该根，把「三处都读」从推断升为直证；同批发现 location **不稳定**（同一骨架两次枚举 `probe-skill` 分别报 `.opencode/…` 与 `.agents/…`），故**收紧**口径：不可用 location 反推某根被扫 | `evidence-host-probe/P8d-opencode-root-proof-20260908T073003.txt` |

| 21 | Codex 复核 r1（绑 HEAD `434c77dc`） | ✅ 已跑完并整改：**BLOCKER 0 / HIGH 6 / MEDIUM 4 / LOW 2**，12 条全部采纳。净影响 = **撤销 1**（P6 分层）、**收窄 8**、**更正 1**（OpenCode 副作用原表述错误）、**新增发现 2**（Codex 会编造命令输出 / D-26 (i) 对 OpenCode 覆盖面漏洞）。⚠️ 零代码卡 1 轮，**整改后未复审**，已登记交主 session 裁定 | `_bmad-output/审查/codex-review-CARD-HOST-PROBE.md`（首部含模型/effort/版本三字段）· 实测表 §七 |
| 22 | ⛔ **副作用登记更正**（Codex HIGH-5） | ⛔ 原写「OpenCode 未见新建物」**是错的**：`~/.config/opencode/` 由空目录变为含 `.gitignore`(63B) + `opencode.jsonc`(50B)，mtime 07:09 = P8-b；`~/.claude.json` 95756B→95945B。均属 (ii) 登记面不阻断。**连带发现 D-26 (i) 列的是 `opencode.json`，而实际写的是 `opencode.jsonc`** ⇒ (i) 覆盖面有漏洞 | `evidence-host-probe/runtime-state-close-20260908T071818.txt:3117-3124` |

**其余禁写面**：`~/.dsh/profiles/web/` 两份、`~/.claude/settings.json` sha 均未变；`~/.config/opencode/opencode.json` 开工/收工同为 `ABSENT`。运行期状态面差集 86 行，**登记不阻断**（差集非空正说明探针真跑起来了）。

---

## 4-B. 👤 你来验（3 分钟，全程在 Obsidian 里看文档）

- [ ] 我打开 `_bmad-output/研究/2026-09-08-HOST-PROBE-宿主实测表.md` → 我看到开头就是一张四个助手横向对比的大表 → 我感觉**一眼就能找到我关心的那一格**，不用从头读到尾。

- [ ] 我在第一张表里找「怎么连上学习后端」那一行（表 A 第 5 行） → 我看到三个助手给出三种完全不同的答案：一个读到了但要我点头同意、一个压根不看我放在课程库里的设置、一个直接就连上了 → 我感觉**这三家的差别是真的被试出来的**，不是抄来的说法。

- [ ] 我往下翻到第二张表，逐行看 P0 到 P10 → 我看到每一行都有「确认 / 推翻 / 没跑成」三种结论之一，**没有一行是空着的**，没跑成的还写明了为什么没跑成 → 我感觉**不确定的地方比之前少了**，也不担心有人拿「应该可以」糊弄我。

- [ ] 我看「决策页更正清单」那一节 → 我看到有一条写着**之前的更正本身错了**（沙箱默认值那条），并说明了错在哪里 → 我感觉**这份表是敢改自己的**，可信度更高了。

- [ ] 我看最后的「二线转正建议」三行 → 我看到每一行都不是光写「行/不行」，还写了行的前提是什么、不行是卡在哪 → 我感觉**知道下一步该先给谁开绿灯**，而且知道开之前还要补什么。

- [ ] 我看「本卡未证明什么」这一节 → 我看到有 20 条明写着**这次没测到**的东西 → 我感觉**踏实**，因为它没有把没做的事说成做过了。

---

## 5. 🚦 验收结果

- **全部勾上** → 回一句「U4-A 通过」，同车道继续 U4-B（技能跨助手命名检查）。
- **有勾不上的** → 在下面批注区写一条 `[!error]+`，说清楚是哪一格看不懂或者觉得不对，我改完重新 ship。
- **📌 另外要告诉你一件事**：这次的复核（4-A 第 21 条）挑出了 6 条重要问题，我全部采纳并改了——其中**有一条是我原本写错了**（我说某个助手没往你电脑上留文件，其实它留了两个），还有一条让我**撤回了一个我本来挺得意的结论**。表里都标了「已撤销 / 已更正」，你能看到改了什么。
- **⚠️ 有一件事需要你拍板**（见 4-A 第 19 条）：这次发现 Codex 在「可写」模式下会自己往它的设置文件里记一笔「这个目录我信任」。按现有规矩这算「设置被改了 = 该卡住」，但那是它自己写的、不是我写的，而且以后**每一张用 Codex 可写模式的卡都会卡在这里**。我没有自作主张放宽，想请你定：是把这类「助手自己记的东西」挪到「允许它自己写」那一类，还是保持现状。

---

## 6. 📝 批注区

> [!question]+ 你的提问
>
>

> [!error]+ 你发现的问题
>
>

---

## 7. 🔗 技术 spec 引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十三批-goals/U4-A.md`（feature 主干树）
- 产出：`_bmad-output/研究/2026-09-08-HOST-PROBE-宿主实测表.md`
- 证据根：`_bmad-output/审查/evidence-host-probe/`（49 份；每条探针含 `rc=` 末行；5 份提示词逐字落盘 `prompt-P*.txt`）
- 绑定：`da690bf8`（零代码，HEAD 与其只差 `_bmad-output/**`）
- 协议：`.claude/rules/card-batch-protocol.md` §1 合并门 / §2.1 存档首部 / §2.2 裁判落盘
- 禁写面口径：手册 §四.5 **D-26**

### 本卡未证明什么（20 条，全文见实测表 §五）

① Codex/OpenCode **受信**项目下的行为（受信需改用户级配置，禁）；② dsh `web` 之外的 profile；③ dsh 的**认根**（dump 不含已解析路径 + 插件被禁用）；④ dsh 两种沙箱模式的拒因是否可区分（Codex 的分层结论**不可外推**）；⑤ P3 弹审批的**运行期**行为（仅配置面求值）；⑥ dsh 侧公开工具名**确实被注册**（由包文档规则 + 后端原始名**推导**）；⑦ ChatGPT 桌面端发现；⑧ live vault（主仓 `.git` **目录**祖先）下的行为；⑨ OpenCode 模型侧能否**使用** skill（provider 凭据缺失）；⑩ 真 skill 在二线宿主里**能跑**（只证能被列出）；⑪ 探针 vault 观测对「有 `.git` 祖先的用户 vault」全部成立；⑫ 运行期状态面新增文件的内容（只记路径与时刻）；⑬ OpenCode 向上遍历边界**就是** git 根（两点一致但缺第三个对照）；⑭ OpenCode 去重时按什么规则保留哪一份（P8-d 实测 location 不稳定）；⑮ dsh web profile **运行期**确实不加载 skills（`disabled: true` 是实测值，「禁用即不读」是推断）。

### 台账待登记条目（16 条，全文见实测表 §六）

要点：① 实测表路径 + 三态计数（整改后）**CONFIRMED 11 / 部分 CONFIRMED 1 / REFUTED 3 / NOT-RUN 4**；② 决策页更正 8 条（含 **#1 反转**：卡文 §〇 对 dsh 沙箱缺省的「更正」不成立）；③ 二线转正建议三行（不裁）；④ **D-24 形态部分不成立**（`--profile web` 可用于 MCP 面，不可用于 skills / 写入面）；⑤ P10 偏离 + 「`.git` 文件被当祖先」+ 两家条目数同为 15；⑥ 宿主副作用 4 项；⑦ Codex 存档（轮次后回填）；⑧ 后端在跑 + `/mcp` 6 个只读工具；⑨ 只读白名单与提示词落盘路径；⑩ `failOnStartupError` 引用更正（`:47`/`:64`）**成立**；⑪ **⛔ D-26 (i) 阻断项待裁**；⑫ P3 写法更正确认；⑬ 两层口径出处 = D-26；⑭ 其它硬判据全绿；⑮ **送审后自查补做项 P8-d**（Codex 绑 `434c77dc`，此后只改 `_bmad-output`，代码树零变更绑定不破）；⑯ 用户级某 skill 的 frontmatter 解析失败（既有问题，不改）。
