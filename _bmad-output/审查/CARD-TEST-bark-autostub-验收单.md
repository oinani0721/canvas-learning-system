---
story: "CARD-TEST-bark-autostub"
title: "bark-autostub"
status: "review"
version: "3"
date: "2026-09-01"
developer: "Claude Code (Fable 5)"
commit: "e1dab3c5"
batch: "BATCH-2026-09-01-第八批"
---

# CARD-TEST-bark-autostub 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是第八批 W4 车道第 ① 卡的验收文档。技术细节全部在「🤖 Claude 已代验」段，你只看 4-B 那一小段。

---

## 🎯 这个卡要做到什么

给每日复习推送的**现有测试套件**（`test_daily_review*` 系列 + 负门探针）装上自动防护：其中任何一条测试就算忘了做防护，也**不会**往你手机上推真通知——它会自己响亮地失败，逼着写测试的人补防护。如实边界：换名字的新测试文件（如 `test_review_push.py`）默认不在防护圈内，要不要扩圈列为裁决点 5 待你批。

---

## 📖 你的视角

**作为** 每天靠手机推送提醒复习的用户，
**我想** 开发和测试过程永远不要碰我的真实手机通知，
**以便** 我收到的每条推送都是真的当日复习提醒，不被测试假通知污染或顶掉。

---

## 🖥️ 交互流程

```
1. 你什么都不用做
       ↓
2. 现有每日复习测试套件（test_daily_review* 系列 + 探针）装上自动防护：
   这些测试无论怎么忘防护都不会再推你的手机
       ↓
3. （这张卡是纯保护性质的，装好后你看不到任何变化；
   换名字的新测试文件不在保护圈内 — 边界已登记，扩不扩等你批）
```

---

## 🤖 Claude 已代验（4-A：全部裁判输出）

> [!success]+ 六条裁判全绿，以下为逐条证据（round-3 终修后终态实测）

| # | 裁判 | 期望 | 实测 | 结果 |
|---|---|---|---|---|
| 1 | `caffeinate -i .venv/bin/pytest tests/regression/test_daily_review_run.py -q -p no:cacheprovider` | passed == 开工基线 N=32 | `32 passed, 10 warnings in 0.82s`（开工 collect-only 基线亦 32） | ✅ |
| 2 | `.venv/bin/python scripts/bark_autostub_negative_control.py` | 末行 NEGATIVE-CONTROL: PASS + exit 0 | 末行 PASS（下表八跑逐行），脚本 exit 0 | ✅ |
| 3 | (d) 两条 grep | 0 行 / 恰 1 行 | grep-1 输出 0 行（rc=1）；grep-2 恰 1 行 = `scripts/daily_review_run.py:250` | ✅ |
| 4 | 模块门零副作用 | regression collect 计数不变 + pick 37 不变 | fixture 加入前后均 `1028 tests collected`；`test_daily_review_pick.py` 前后均 `37 passed` | ✅ |
| 5 | `stat -f %m ~/.config/canvas-review/bark.key` 裁判 1 前后 | 不变 | 前 `1785602341` / 后 `1785602341` | ✅ |
| 6 | `.venv/bin/ruff check`（conftest.py / bark_egress_probe.py / bark_autostub_negative_control.py / send_bark.py） | 0 error | `All checks passed!` rc=0 | ✅ |

### 裁判 2 负控八跑逐行（v2：放行门 ×3 + 篡改门 ×3 + 探针双跑）

| 跑 | 形态 | nodeid | 期望 | 实测摘要 |
|---|---|---|---|---|
| A | --noconftest（卸甲） | test_probe | PASS | `1 passed` rc=0 ✅ |
| B | 布防 | test_probe | FAIL + 指定拒绝器断言 | `1 failed, 10 warnings` rc=1，整行 `E AssertionError: Bark egress attempted in tests` ✅ |
| C | 布防 | test_keyfile_guarded | PASS | `1 passed, 10 warnings` ✅ |
| C' | --noconftest | test_keyfile_guarded | FAIL + 指定消息 | `1 failed`，`E …守卫未布防: send_bark.KEY_FILE 仍指向真实 key 位置` ✅ |
| D | 布防 | test_osascript_guarded | PASS | `1 passed, 10 warnings` ✅ |
| D' | --noconftest | test_osascript_guarded | FAIL + 指定消息 | `1 failed`，`E …守卫未布防: osascript_fallback 仍是 runner 原始实现` ✅ |
| E | 布防 | test_reload_selfheal | PASS | `1 passed, 10 warnings` ✅ |
| E' | --noconftest | test_reload_selfheal | FAIL + 指定消息 | `1 failed`，`E …reload 后 KEY_FILE 回到真实 key 位置` ✅ |

末行：`NEGATIVE-CONTROL: PASS (armed=probe-FAILED-as-expected, disarmed=probe-PASSED-egress-attempted)`，exit 0。

C/D/E 是守卫三层（KEY_FILE 重定向 / osascript 打桩 / reload 自愈）各自的**放行门**；C'/D'/E' 是对应的**篡改门**——卸甲必须翻红，证明放行门真的依赖守卫而非恒真。

### 拒绝器不被吞的证明（行号为改后实况）

`send_bark.py` 网络重试循环内共三个 except：`:132 except (json.JSONDecodeError, UnicodeDecodeError)`（:130 内层响应解析 try）、`:138 except urllib.error.HTTPError`、`:140 except (urllib.error.URLError, TimeoutError, OSError)`。`AssertionError` 与三者均无继承关系，必然穿透 `send()`；`daily_review_run.main()` 的 try 只包 `ensure_payload`（:224-229），`:250` 的 send 调用不在 try 内。负控 B 跑实证整行输出含 `AssertionError: Bark egress attempted in tests`。

### (a) 缝的改动实况

`git diff HEAD --numstat` → `scripts/send_bark.py` 为 **+5 / -1**（新增 2 行注释 + 1 行别名 + 1 行空行；删除 1 行旧调用点改写为 `_urlopen(req, timeout=TIMEOUT_S)`）。卡文 (a) 限「≤5 行」按增行计恰好合规。别名在 import 时与 `urllib.request.urlopen` 绑定同一函数对象，生产调用路径语义不变（如实边界：绑定后不再观察对 `urllib.request.urlopen` 的后续 rebind，如 tracing 注入——本仓无此用法）。

### 同类扫描结果表（(d) 可复跑命令，cwd = LANE 仓根）

| 门 | 命令 | 期望 | 实测 |
|---|---|---|---|
| 测试侧无第二处出网面 | `grep -rn "send_bark\.send\|_urlopen\|api\.day\.app\|osascript" backend/tests --include='*.py' \| grep -v "regression/test_daily_review_run.py\|regression/conftest.py\|regression/bark_egress_probe.py"` | 0 行 | 0 行（rc=1） |
| 生产侧唯一 send 调用点 | `grep -rn "send_bark\.send(" scripts backend/app --include='*.py' --include='*.sh'` | 恰 1 行 | `scripts/daily_review_run.py:250` 恰 1 行 |

（卡文原命令用 `LANE/` 绝对前缀，此处等价改为 cwd=仓根 的相对路径，命中集合逐字相同。扫描是文本级不是 AST——它证明「当前快照无第二处」，对未来新增代码无约束力。）

### 每道门「不比什么」

| 门 | 它证明什么 | 它**不**证明什么 |
|---|---|---|
| 裁判 1（32 绿） | 现有 32 条在守卫下语义不变 | 不证明任意命名的新测试自动受保护——布防面 = `test_daily_review*` 前缀（该系列未来新文件自动在内）+ 探针精确名；**其它命名**的新文件（如 test_review_push.py）不设防（裁决点 5 / 待你批扩面方案） |
| 负控 A（卸甲 PASS） | 探针这条 main() 路径在无守卫时会真的尝试外发（解析 api.day.app 被观察到） | 不证明所有可能的出网路径都被探针枚举；只锚定 send_bark 经 `_urlopen` 这一条（「唯一」由同类扫描门背书） |
| 负控 B（布防 FAIL+指定断言） | 拒绝器在被它验证的逻辑上，且判据按整行锚定 + 摘要形状收紧（error 即拒收） | 不证明 `--noconftest` 以外的进程内自解脱绑（见「未证明」#4） |
| C/C'（KEY_FILE 门） | 布防下 KEY_FILE 已移出真实位置；卸甲翻红 | 结构性断言，不证明真调 send 时的行为（行为面由 A/B 覆盖） |
| D/D'（osascript 门） | 布防下 fallback 是替身；卸甲翻红 | 同上（不真调函数——调了在卸甲形态就真弹通知） |
| E/E'（reload 门） | reload 生产模块后三层被自动重打；卸甲翻红 | `from importlib import reload` 预绑定形态拦不住（见「未证明」#4） |
| 裁判 4（1028/37 不变） | 非布防模块的收集/通过面不变；守卫 fixture 对它们不建临时目录、不 import、不打桩（如实边界：autouse fixture 本身与其 `request` 依赖仍在每条测试的 fixture closure 内） | 不证明布防模块零开销（它们多了守卫五层 + 一个 mkdtemp 临时目录，测试结束即删） |
| 裁判 5（mtime 不变） | 真 key 文件未被**写** | **读取未被证明**——mtime 不反映读；靠 KEY_FILE 重定向 + 拒绝器双层保证测试不该走到读真 key 那步 |
| 裁判 6（ruff） | 四文件无 lint error | 不证明逻辑正确性 |

### 本卡未证明什么（必填段）

1. **未证明真 key 从未被读取**：mtime 只证未写；「import 瞬间之外、守卫覆盖之外的读」没有系统级取证（如 fs 审计）。
2. **未覆盖两个布防模块名之外的未来测试**：同目录新文件、tests/regression 之外的目录（tests/unit、tests/api 等）未来若直调 send_bark 不受防线保护（当前 grep 门证明现在为 0）。目录级自动扩面方案列为裁决点 5。
3. **未证明生产链行为**：本卡零改生产逻辑（(a) 缝除外），不为 runner 窗口门/重试/兜底语义提供新证据。
4. **进程内故意对抗不在威胁模型**：`from importlib import reload` 的预绑定形态、`del sys.modules[...]` 后重建、测试自建第二个模块实例——这类「故意自解脱绑」守卫不承诺拦截（`importlib.reload` 属性式调用已锁；teardown 后 reload 已 fail-closed 拒绝；from-import 逃逸的最坏后果被 ①loopback + ⑤禁代理 兜到无代理直连本机必拒，偏差 11）；负控也只覆盖显式列出的八跑。
5. **代理清理是尽力消除**（探针内）：已建 opener 的缓存形态拦不住（探针双墙 getaddrinfo + create_connection 恒兜底，两种形态都不出网）；守卫侧的 ⑤ 层（getproxies 恒空）在布防期内无此例外。
6. **负控的来源绑定是启发式**：`E ` 行前窗口的文件名子串检查，非 traceback frame 级绑定——合成「同文件无关失败 + 打印目标行」可绕过（Codex round-3 实证）；完整修法需解析 frame 结构，收益边际小，登记不修。

---

## 👤 你来验（4-B）

> [!info]+ 这张卡对你没有任何可见变化
> 本卡是纯保护性质的：**无变化**。现有每日复习测试套件已装自动防护，跑测试不会再推你手机。
> 你不需要做任何操作。如果今后某天你的手机在没有复习内容的时刻收到一条奇怪的「今日复习」推送，那就是这道防线漏了，直接批注告诉我。

- [ ] 我今天正常用手机 → 我没看到任何多余的假推送 → 我感觉一切照旧、很安心

---

## 🚦 验收结果

**默认裁决回执全数确认即通过**：回复「CARD-TEST-bark-autostub 通过」，本卡随 ②（isolate-lifespan）一起合中间 commit。
**任何一条不同意**：在批注区写明，我按你的裁决改。

---

## 📝 你的批注区

> [!question]+ 待你裁决（默认裁决回执 1-4 = 卡文列明的默认值；5-10 = 本卡执行中的如实偏差，依据在括号内）
>
> **默认裁决（均已按默认执行）**
> 1. **send_bark.py ≤5 行缝**：已落地（+5/-1）。若你不许动 send_bark.py，退回方案是测试侧只 patch send_bark 模块内命名空间壳。
> 2. **autouse 放 regression/conftest.py 带模块门**（不放根 conftest）：已执行。
> 3. **osascript_fallback 打桩**：已执行（守卫内记录并返回 True）。
> 4. **探针文件不带 test_ 前缀**：已执行（默认收集不到，1028 计数不变实证）。
>
> **执行偏差（每条附依据）**
> 5. **模块门 = 语义前缀 + 探针精确名**：模块名末段以 `test_daily_review` 开头的文件自动布防（该系列未来的 test_daily_review_push.py 等自动在内），探针 bark_egress_probe 精确名布防；**其它命名**的新文件不设防。依据：前缀挂在功能名上，防 endswith 的误伤（foo_test_daily_review_run 不误伤）又给系列新文件自动设防（round-2 H3 的部分代码侧修复）；探针必须在布防面内否则负控 B 失效。**待你裁决扩面方案**：目录级门（该目录任何文件都布防）覆盖最全，但会把无关测试文件也圈进守卫；维持现状则换命名的新推送测试文件要手动加名。我推荐维持现状 + conftest 注释写明（现状），等你批。
> 6. **探针在卡文之外自加了桩**：osascript_fallback（卸甲形态会真弹 macOS 通知）、PUSH_WINDOW 放行（机器时区无关）、RETRIES=0（免 2s+4s 重试空等）、DNS/建连双墙 + 代理禁用（见 7）。
> 7. **真实发现**：本机配有 macOS 系统代理——`urllib` 在 env 之外还读系统代理，卸甲形态首跳解析记到的是代理主机 `127.0.0.1` 而非 `api.day.app`（负控首跑 FAIL 抓出）。探针现清代理 env + patch `getproxies`，强制直连形态。**含义**：若真发生测试外发事故，流量会先走你的本地代理——代理日志可作事后取证面。
> 8. **KEY_FILE 重定向从卡文字面的「不存在的路径」改为「真实存在的假 key」**。依据：不存在的 key 会让 send 走 rc=2 静默分支（返 0 不报错）——恰好把「忘了打桩 = 响亮失败」变成「忘了打桩 = 假绿」，是 Codex round-1 的 HIGH-1；假 key 让 load_key 成功、拒绝器必然可达。这是对卡文 (b)① 字面的偏离、对 (b) 意图（响亮失败）的忠于。
> 9. **reload 双保险**：守卫 patch `importlib.reload`（仅布防测试期间进程级生效），对 send_bark/daily_review_run 的 reload 完成后自动重打三层。如实边界：`from importlib import reload` 预绑定形态拦不住（已声明）；E/E' 门证明自愈真的在工作（初版条件写错命名空间，被 E 门当场抓住后修正）。
> 10. **负控从卡文的 A/B 两跑扩为八跑**（C/C'、D/D'、E/E' 三对放行/篡改门）。依据：放行门必须配篡改门，否则「门存在」≠「门在工作」（项目教训 feedback 正反门配对）；A/B 只锁三层中的第②层。
> 11. **假 key 的 server 钉死 loopback**（round-2 H1 整改）：假 key 内容是整段 URL `http://127.0.0.1:9/…`（本机 discard 端口）。语义：拒绝器仍是主防线；若哪条未知的 reload/逃逸路径让真 urlopen 回来，最坏后果 = 对本机发一个必被拒的连接——不出外网、不触真 key、不弹通知。
> 12. **teardown 后 reload 受保护模块会被拒绝**（round-2 H2 整改）：布防结束后的测试代码若 reload send_bark/daily_review_run，会得到生产态模块（真实 key 在位 + 真 urlopen）并污染同进程后续测试——守卫对此 fail-closed（RuntimeError），不再「真 reload 放行」。语义变化：reload 这两个模块只允许在布防测试内做。
> 13. **E 门（reload 自愈）锁双模块**（round-2 M3 整改）：对 send_bark 与 daily_review_run 各自 reload 后断言两侧桩都被重打——守卫若漏 rearm 任一侧，E 必红。
> 14. **⛔ 待你裁决：终修未经第四轮 Codex 复审**。round-3 终判 FAIL 的 3 条 HIGH 已终修 + 客观裁判全绿（终修明细见下方 [!error]+ 显著声明），但 3 轮续轮预算已尽，终修本身没有再送审。你可选：(a) 接受此收尾，卡随 ② 合中间 commit；(b) 批一轮追加复审再合。
> 15. **round-3 的 MEDIUM/LOW 处置**：5 处已修（冷启动 KEY_FILE 残留 / C 门锁 loopback 内容 / 注释与行号 / negctl 摘要正则 / 裁判 4 边界措辞），2 处结案登记（来源绑定是启发式非 frame 级 / from-import 别名不在 osascript 桩保护内）——明细见下方显著声明之后的「round-3 其余发现的处置」段。
>
> **审查轨迹（如实）**：Codex round-1 判 FAIL（3H+2M+**4L**——L 计数在 commit message 中误记为 3L，以本验收单与本审查文件为准，全文 `codex-review-CARD-TEST-bark-autostub.md`）；并行 7 维度对抗审查产 22 条发现（其中「守卫层①抢先短路使拒绝器不可达」「负控只锁一层」与 Codex 重合互证，全程记录在案）；整改后 E 门自测又抓出一个我自己的 bug（reload 重打条件写错命名空间，见 9）；round-2 复审判 FAIL（3H+3M+4L，全文 `…-round2.md`）→ round-3 整改（偏差 11-13 + 前缀门 + 判据锚定）→ **round-3 终审判 FAIL（3H+5M+3L，全文 `…-round3.md`）**。
>
> > [!error]+ ⚠️ 显著声明：终修未经第四轮 Codex 复审（3 轮续轮预算已尽，按卡文降级预案收尾）
> > round-3 的 3 条 HIGH 终修如下（MEDIUM/LOW 处置见裁决 15）：
> > - **H2'（stale wrapper 先 reload 后 raise）**：flag 检查已挪到 reload **之前**（conftest `_guarded_reload`），拒绝真正发生在重载前。
> > - **H2''（loopback key 被系统代理接管转出机）**：新增第 **⑤** 层——布防期内 `urllib.request.getproxies` 恒空，①的 loopback 兜底成为「无代理直连本机 discard 端口必拒」，请求不出机。
> > - **H3'（验收单绝对承诺）**：目标段/交互流程/4-B 段全部收窄为「现有 test_daily_review* 系列 + 探针布防；换名新文件不设防（裁决点 5）」。
> > 终修后**客观裁判全套重跑全绿**（八跑 NEGATIVE-CONTROL PASS exit 0 / 32 / 1028 / 37 / ruff / grep 0+1 / 真 key mtime 不变 / send_bark +5/-1 合规）；终修期间我自己引入过一次 `import os` 缺失，被八跑当场全红抓住（布防形态 fail-closed 失败方向正确）后修复。**终修本身未再送 Codex 复审**——请你（用户）裁决是否接受此收尾（裁决 14）。
>
> **round-3 其余发现的处置（MEDIUM/LOW 登记结案）**：
> - M（来源绑定子串弱）→ 结案登记：`_judged` 的 src 检查是「文件名子串窗口」启发式，非 traceback frame 级绑定；合成场景可绕过（Codex 已演示）。完整修法收益边际小，已如实写入「未证明」#6。
> - M（冷启动 KEY_FILE 残留）→ **已修**：守卫 setup 对首次加载的 send_bark 先手动复位真实默认路径再打桩，teardown 恢复真实默认（conftest `real_default_key` 段）。
> - M（collection 期 from-import 别名绕过 osascript 桩）→ 结案登记（docstring ③ 如实边界）；现有 32 条无此形态。
> - M（八跑不锁 loopback 内容）→ **已修**：C 门加内容断言（假 key 必以 `http://127.0.0.1:9/` 开头）。
> - M（注释引用不存在的 `_BARK_GUARDED_EXTRA` / 「三层」过时）→ **已修**（注释改 `_BARK_GUARDED_MODULES` + 五层表述）。
> - L（「只实例化 request」不准）→ **已修**（裁判 4「不比什么」补 closure 如实边界）。
> - L（negctl 摘要正则吞尾巴）→ **已修**（`_SUMMARY` 去掉 `(?:\s.*)?`）。
> - L（docstring 行号漂移 :139/:141）→ **已修**（send_bark 注释压缩回 +5/-1，行号复位 :138/:140/:128，验收单同步）。

（空）

---

## 🔗 技术 spec 参考（给 Claude 读的）

- **卡文**：`feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W4-1.md`
- **改动/新增文件**：
  - `scripts/send_bark.py`（(a) 缝，+5/-1）
  - `backend/tests/regression/conftest.py`（(b) `_bark_egress_guard` v3：独立 MonkeyPatch + 前缀模块门 + 四层防线（含全局 urlopen 兜底）+ reload 双保险（teardown 后 fail-closed）+ loopback 假 key）
  - `backend/tests/regression/test_daily_review_run.py`（`_capture_bark_request` 改 patch 缝）
  - `backend/tests/regression/bark_egress_probe.py`（(c) 探针 + C/D/E 自证门（E 锁双模块）+ 双墙断网，新增）
  - `backend/scripts/bark_autostub_negative_control.py`（(c) 八跑负控：判据含摘要唯一性 + 整行锚定 + 异常来源绑定，新增）
- **Codex 对抗审查**：round-1 `_bmad-output/审查/codex-review-CARD-TEST-bark-autostub.md`（FAIL 3H+2M+4L → 全整改；commit message 中误记 3L）；round-2 `codex-review-CARD-TEST-bark-autostub-round2.md`（FAIL 3H+3M+4L → round-3 全整改）；round-3 `codex-review-CARD-TEST-bark-autostub-round3.md`（终轮，回填）
- **Git commit**：`e1dab3c5`（card/w4-micro，未 push）
- **完成条件 → 落点**：
  - (a) → send_bark.py:38-41 + :128（+5/-1）
  - (b) → tests/regression/conftest.py `_bark_egress_guard`（① KEY_FILE=loopback 假 key（偏差 8/11）；② 拒绝器；③ osascript 桩；④ 全局 urlopen 兜底；+ reload 双保险（偏差 9/12））
  - (c) → tests/regression/bark_egress_probe.py + backend/scripts/bark_autostub_negative_control.py（八跑，偏差见裁决 10/13）
  - (d) → 本单「同类扫描结果表」
  - (e) → 本单 4-A 表六行

---

## 📅 下一步

1. **默认裁决 + 偏差 5-10 全数确认** → 说「通过」→ 本卡随 ② 合中间 commit
2. **任何裁决点不同意** → 批注区写明 → 我按裁决调整后重跑六条裁判
