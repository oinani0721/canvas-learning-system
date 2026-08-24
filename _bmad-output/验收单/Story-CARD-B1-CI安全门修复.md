---
story: "CARD-B1"
title: "ci-security-gate-fix"
status: "review"
version: "1"
date: "2026-08-25"
developer: "Claude Code (Fable 5)"
commit: "card/b1-ci-e0 分支 BATCH-2026-08-24-复习闭环 两个 commit（CARD-E0 + CARD-B1）"
---

# CARD-B1 验收单（给你看的版本）— 附 CARD-E0

> [!info]+ 这是什么
> 这是 **CARD-B1（质量门红灯修复）** 的用户验收文档，**给你（非技术）读的版本**，顺带汇报同车道的 **CARD-E0（夜间车道准备）**。
> 技术档案在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md` 的 CARD-B1 / CARD-E0 节（Claude 读的）。

---

## 🎯 这两张卡做到了什么

**B1**：自动质量检查此前发现 5 个图像库安全漏洞，被 13 条"先放行"的豁免条款挡着假装绿灯。根因是一个**从来没人用过**的视频处理组件把图像库锁死在有漏洞的旧版本。现在：死组件已移除、图像库升到安全版本、13 条豁免全部删光——质量门从"睁一只眼闭一只眼"变成**真把关**。

**E0**：一个坏掉的旧测试文件曾让整个自动测试没法启动（一启动就中断）。现在已绕过（文件本身保留，留给未来专门的卡修复），并写好了《夜间车道运行手册》。

---

## 📖 用户故事（你的视角）

**作为** 每天用这套系统复习的学生，
**我想** 每次代码改动都有真实的安全和质量把关，而不是被豁免条款糊弄过去的假绿灯，
**以便** 我可以放心让 Claude 夜间自动推进开发，不担心悄悄混进有漏洞的组件。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 你在 Obsidian 打开这份验收单，读完
       ↓
2. 你满意的话，白天对 Claude 说："CARD-B1 通过，推送"
       ↓
3. Claude 推送后，你打开 GitHub 网页的 Actions 页面
       ↓
4. 最新一行显示 4 个绿色勾勾（包括以前老红着的那个安全检查）
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | B1 裁判①：`backend/.venv/bin/pip-audit -r backend/requirements.txt`（**零豁免参数**） | ✅ 输出 `No known vulnerabilities found` |
| 2 | B1 裁判②：CI 白名单 14 测试文件 + `tests/unit/test_multimodal_fixes.py`（`-m "not integration"`，在重建后 pillow 12.3.0 环境跑） | ✅ `305 passed, 13 skipped, 0 failed` |
| 3 | pillow 11→12 API 断裂面：`Image.LANCZOS` 别名在 12.3.0 实测仍存在 | ✅ 无需改代码（卡片预案未触发） |
| 4 | moviepy 零调用方复核：全仓唯一 import 在 `video_processor.py:26` 且有 try/except 守护；`VideoProcessor` 无外部调用方；tests 目录零引用 | ✅ 卸载后 import 链无断裂 |
| 5 | venv 重建：旧环境保留为 `backend/.venv-pre-b1-backup`（可回滚），新环境按 requirements 全量重装 + CI 同款测试附加依赖（hypothesis 等，版本与旧环境一致） | ✅ |
| 6 | `.github/workflows/test.yml`：13 条 `--ignore-vuln` 全部删除，豁免注释块改写为历史决策记录（保留 2026-08-19 P1-04 上下文） | ✅ |
| 7 | `docs/known-gotchas.md`：新增 G-DEP-001（moviepy 已移除 / graceful degradation / 复活条件） | ✅ |
| 8 | E0 裁判：`pytest tests/ --collect-only -q` 在旧 venv 与重建后 venv 各跑一次 | ✅ 两次均 `6608 tests collected`，无 `Interrupted` |
| 9 | E0 查重：兄弟分支 fix/test-infra-paralysis 全历史零触碰同类改动 | ✅ 无重复劳动，结论记入手册 §0 |
| 10 | E0 交付：《夜间车道运行手册》已写入 `_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md` | ✅ 含裁判命令清单 / Epic 编号错位警告 / 禁止动作清单 |
| 11 | Codex 交叉审查（gpt-5.6-sol · ultra · 只读沙箱）重点审"零调用方"与"pillow 12 断裂面" | ✅ `0 BLOCKER / 0 HIGH / 2 MEDIUM`；两条 MEDIUM（文档措辞精确性）已当场修复并复跑裁判①通过。全文见 `_bmad-output/审查/codex-review-CARD-B1.md` |

---

## 👤 你来验（产品使用体验 — 3 步，5 分钟内全在 Obsidian / 浏览器里完成）

### 第 0 步：First 5 seconds

- [ ] 我在 Obsidian 打开《夜间车道运行手册》（在 `_bmad-output/implementation-artifacts/goal-cards/` 文件夹里），5 秒内能看出它分成"照抄可跑的清单"和"禁止动作"两大块
- [ ] 5 秒后我感觉这份手册 (a) 拿来就能用 (b) 还是看不懂 (c) 说不清 — 选: ___

### 第 1 步：读懂"这次修了什么"

- [ ] 我读完本验收单最上面"🎯 这两张卡做到了什么"一段
- [ ] 我能用自己的话说出一句："以前安全检查是____的，现在是____的"
- [ ] 我感觉（放心 / 还有疑问，写下来）：___

### 第 2 步：白天验真绿灯（唯一需要你出手的动作）

- [ ] 我对 Claude 说："**CARD-B1 通过，推送**"（这一步会联网公开代码改动，所以留给你白天知情时拍板）
- [ ] 之后我打开 GitHub 网页的 Actions 页面，看到最新一行 **4 个绿色勾勾**
- [ ] 我感觉这条质量门以后是真的在替我把关：___

### 第 3 步：边界（如果出问题会怎样）

- [ ] 如果 Actions 页面出现红叉，我不用自己修——我直接把红叉截图或页面链接发给 Claude 说"红了"
- [ ] 我知道视频处理功能现在是"未安装"状态：万一将来真的要处理视频，系统会给出明确提示而不是闪退（复活步骤 Claude 已记录在案）

### 主观打分（Felt-sense）

- [ ] **这次改动让我对夜间自动开发的信任度**（1=更不放心 / 5=更放心）：___
- [ ] 一句话告诉 Claude 打分原因：___

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**CARD-B1 通过**"（想连推送一起做就说"CARD-B1 通过，推送"），Claude 会 mark as **done**，本车道（B1+E0）收工。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象，Claude 根据你反馈 correct-course 调整。

---

## 📝 你的批注区

> [!question]+ 你对 CARD-B1 / CARD-E0 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **卡片档案**：`_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md` §CARD-B1 / §CARD-E0
- **源改动**：
  - `backend/requirements.txt`（删 moviepy>=1.0.3，加 pillow>=12.3.0）
  - `.github/workflows/test.yml`（security job：13 条 --ignore-vuln 删除，L159 起注释块改写为历史决策记录）
  - `docs/known-gotchas.md`（G-DEP-001）
  - `backend/tests/conftest.py`（E0：collect_ignore + 回收条件注释）
  - `_bmad-output/implementation-artifacts/goal-cards/夜间车道运行手册.md`（E0 交付）
- **审查存档**：`_bmad-output/审查/codex-review-CARD-B1.md`
- **测试证据**：`305 passed, 13 skipped`（CI 白名单 14 文件 + test_multimodal_fixes.py，pillow 12.3.0 环境）；pip-audit 零豁免 0 finding
- **Git commit**：card/b1-ci-e0 分支，两个独立 commit——`BATCH-2026-08-24-复习闭环 / CARD-E0`（848469ca）与 `BATCH-2026-08-24-复习闭环 / CARD-B1`（本卡收尾 commit）
- **完成判据 → 证据对应**：
  - B1(a) → requirements.txt diff；B1(b) → test.yml diff；B1(c) → 代验表 #1/#2；B1(d) → 代验表 #7；B1(e) → 代验表 #11；B1(g) → git log
  - E0(a) → conftest.py diff；E0(b) → 代验表 #8；E0(c) → 代验表 #10

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "CARD-B1 通过（，推送）" → Claude mark done → 白天推送后你在 GitHub 网页看四绿勾
2. **部分 ❌** → 在批注区写清楚，或用 `Cmd+Shift+A` 批注 → Claude correct-course 再修正
3. **本车道收工后** → A2/A3 车道按批次计划继续
