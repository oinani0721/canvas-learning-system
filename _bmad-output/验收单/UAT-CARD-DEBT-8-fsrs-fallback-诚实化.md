# UAT 验收单 — CARD-DEBT-8：FSRS fallback 诚实化

> 批次：[BATCH-2026-09-01-第八批] ｜ 车道：W8（card/w8-scope）｜ 状态：待用户验收
> 卡文：`第八批-goals/W8-1.md` ｜ 审查证据：`_bmad-output/审查/evidence-debt8/`

---

## 1. 🎯 一句话目标

复习调度器在「备用调度模式」运行时，不再谎报自己在用 FSRS-4.5 算法——系统说什么就用什么。

## 2. 📖 你的视角

作为一个学习者，我想让系统诚实告诉我它用了哪种复习安排，以便我复习间隔突然变得死板时能知道原因（比如算法库损坏退化成了简单模式），而不是被一个假标签蒙在鼓里。

## 3. 🖥️ 交互流程

（本卡是诚实性修复，不改变任何界面流程）

你平时的复习操作完全不变：打开白板 → 评分 → 看到下次复习时间。唯一的隐藏变化：如果底层算法库哪天坏了，系统内部记录会如实标注「退化了」，而不是继续宣称一切正常。

## 4-A. 🤖 Claude 已代验（全部实跑，证据在 `_bmad-output/审查/evidence-debt8/`）

| # | 裁判 | 结果 | 证据 |
|---|------|------|------|
| 1 | 七文件 pytest 全绿 | ✅ 136 passed, 0 failed | `judge1-7files-v2.txt` |
| 2 | 子进程探针：屏蔽 py-fsrs 后 `record_review_result` 返回 `algorithm="fsrs-fallback-scheduler"` + `degraded_reason="fsrs_library_missing"`；跑前后 backend/data 全目录 sha256 快照零变化 | ✅ | `judge2` 段（本文件下方原文摘录） |
| 3 | `-k "fsrs or review_service or story_38_3"` 开工基线 vs 改后 | ✅ 193 passed 前后一致，0 新增失败 | `baseline-k-filter.txt` / `after-k-filter-v2.txt` |
| 4 | 无新增第三个模块级标志 | ✅ `FSRS_RUNTIME_OK\|FSRS_AVAILABLE\|FSRS_LIB` grep 与 HEAD 逐行相同 | 本文件下方原文摘录 |
| 5 | 先红后绿 | ✅ 改码前 4 failed + 1 passed（红因=`lied fsrs-4.5: 'fsrs-4.5'`），改后 5 passed | `red-state-run.txt` |
| 6 | 变异负控制（串行 10 条，超卡文 ≥2 要求） | ✅ 10/10 KILLED，还原后 sha256 逐字节一致 | `mutation-run-v2.txt` / `mutation-run-v3.txt` |
| 7 | **Codex round-1 终判** | ✅ **PASS：0 BLOCKER / 0 HIGH**；3 MEDIUM 中 2 条当场整改、1 条登记移交，2 LOW 中 1 条当场整改、1 条并入移交 | `_bmad-output/审查/codex-review-CARD-DEBT-8.md` |

**Codex 三项正面确认**（「未发现」= 没审出问题）：底层真值链全通（factory 缺库路径四层标志逐层 False → 三入口诚实）；无第三个模块级标志（grep 与 HEAD 逐行相同）；真实库路径与 `a63fadd3^` 对照**逐键相等**（`*_equal=True` ×5，含写失败与空 concept_id 路径）。

**Codex M/LOW 处置**（整改后全门复绿：探针 5 passed / 七文件 136 passed / 变异 10/10 / -k 193 passed）：

| 条目 | 内容 | 处置 |
|------|------|------|
| M1 | 注入缺 `library_available` 属性的 manager 时 fail-open 复活谎报 | **已整改**：`__init__` 一次性 warning 显式出声；fail-open 保留为显式裁决（改 fail-closed 会打红既有 mock 注入套件，且越文件边界），why 已写进 helper docstring |
| M2 | py-fsrs 缺失环境下既有 `TestCardStatePersistHonestyD3` 4 条精确断言回归（拼接值≠旧单值） | **登记移交**（§移交项 5）：修复须改 `test_review_service_fsrs.py`，越本卡独占面；真库环境（本机）全绿 |
| M3 | 真实库探针只查个别键，锁不死「夹带键/绕过实例真相源」变异 | **已整改**：三响应改精确键集断言 + 关键值不变式 + `library_available is True/False` 实例真相源双环境钉死 |
| LOW1 | D3 拼接只查 substring，杀不死删逗号变异 | **已整改**：断言升级为精确全串 `fsrs_library_missing,card_state_write_failed` |
| LOW2 | `schemas.py` 的 `algorithm`/`degraded_reason` 契约描述未含第三值/复合值 | **登记移交**（§移交项 3 扩充） |

**裁判 2 探针原文输出**（跑前后 `backend/data` 全目录 sha256 比对，diff 为空）：

```
ALGORITHM: fsrs-fallback-scheduler
DEGRADED_REASON: fsrs_library_missing
STATE_ALGORITHM: fsrs-fallback-scheduler | STATE_REASON: fsrs_library_missing
DATA-UNCHANGED-OK (真门: sha256 全目录比对)
```

> ⚠️ 门升级说明：卡文裁判 2 原文用 `git status --short backend/data` 判无变化——实测该门是**假门**（`fsrs_card_states.json` 被 `backend/data/.gitignore:8` 忽略，探针真写了盘它也永远无输出）。已升级为全目录文件清单 + sha256 快照比对（真门），结论不变：零写入。

**裁判 4 原文**（当前与 HEAD 基线逐行相同，仅存在 :95/:97/:105 等既有标志）：

```
95:    FSRS_AVAILABLE = True
97:    FSRS_AVAILABLE = False
105:FSRS_RUNTIME_OK: Optional[bool] = None
（与 git show HEAD 同位置逐行一致，无新增模块级标志）
```

## 4-B. 👤 你来验（live 库在位 → 本卡对你是「无变化」验证）

说明：你机器上算法库是完好的，所以这轮验收只能确认「好东西没被改坏」。

- [ ] 我打开 Obsidian 白板，给几个概念做一次平时那样的评分 → 我看到回执/下次复习时间和以前一样正常出现 → 我感觉流程没有任何异样。
- [ ] 我翻一下总览页的复习提醒 → 我看到数字和日期还是老样子 → 我感觉安心：修复没有动到我正在用的部分。
- [ ] （诚实声明）现在没有任何界面直接显示「算法名」标签，所以「不再出现假 FSRS-4.5 标签」这件事你暂时看不到——它修的是系统内部回话的诚实性，未来界面引用这个字段时才不会被骗。

## 5. 🚦 验收结果

- 4-B 全勾 + 无批注 → 本卡通过，等主 session 合并。
- 任何一条不符 → 在 §6 批注，走 correct-course。

## 6. 📝 批注区

[!question]+ 待你裁决（卡文默认裁决，未批前按默认落地）
- ① fallback 激活时报 `algorithm="fsrs-fallback-scheduler"`（不冒充 fsrs-4.5，也不冒充 ebbinghaus）——名称可以改。
- ② 底层库可用性用 manager 实例属性暴露，不新增第三个全局标志位。
- ③ 真实库在位时三个接口响应逐键不变（对照探针锁定）。

[!question]+ 空 callout（写你的批注）

### 移交项（真实、但不在本卡文件边界内，逐条登记）

1. **`GET /api/v1/review/fsrs-state` 的新诚实键透不到 HTTP**（review.py:1437 白名单构造响应 + response model 无字段）——本卡在 service 层修好，但该端点消费方拿不到；PUT /record 路径已实证可见（review.py:1122/:1125 转发）。
2. **`/api/v1/health` 的 `components.fsrs` 在 py-fsrs 缺失时仍报 "ok"**（health.py:108；两个分支分别依赖恒真标志与「manager 对象存在」语义）——修复触及 FSRS_RUNTIME_OK 语义（裁决② 禁区），须持卡人/用户另裁。
3. **`RecordReviewResponse` 契约描述未同步**（schemas.py:1001 `algorithm` 描述只有 "fsrs-4.5 or ebbinghaus-fallback"；Codex LOW2 补充：:1013 `degraded_reason` 描述宣称「仅持久化失败时出现、仅两个单值」，现成功时也可能带 `fsrs_library_missing`、双降级为复合值）——两行描述同步，LOW。
4. `schedule_review` 无 HTTP 端点（纯内部调用），其诚实化仅服务层可见——现状如实记录。
5. **缺 py-fsrs 环境下既有 D3 测试类回归**（Codex round-1 M2：屏蔽 fsrs 后 `TestCardStatePersistHonestyD3` 4 failed——精确断言 `degraded_reason` 旧单值/`algorithm` 旧恒值，与本卡新诚实值冲突）——修复须改 `test_review_service_fsrs.py`（越本卡独占面），真库环境全绿不受影响；建议随下批测试卫生卡把该类断言改为 fallback-感知。

### ⚠️ 本卡执行过程事故披露（已全部恢复）

审查阶段一个后台子代理把「变异测试中间态」遗留在 review_service.py（get_fsrs_state 加性块被替换为 `pass`），被变异脚本的基线前置检查当场拦住后手工恢复并全量复跑；同批另一子代理越权往 rag.py / nodes.py 写入了下一张卡（G4-4）的内容，已按 HEAD 逐字节还原（`git diff HEAD` = 0）。教训已入项目记忆：**给审查代理写权限 + 弱模型 = 越权与残留双重风险**。

## 7. 🔗 技术 spec 引用

- 改动：`backend/app/services/review_service.py`（+`_fsrs_library_ok` helper、三处消费点、log_decision 诚实化）、`backend/lib/memory/temporal/fsrs_manager.py`（`library_available` 实例属性）
- 新测试：`backend/tests/regression/test_debt8_fsrs_fallback_honest.py`（5 探针）
- 变异工具：`_bmad-output/审查/evidence-debt8/mutation_negative_controls_debt8.py`（10 条，串行，sha 复核）
- Codex 审查：`_bmad-output/审查/codex-review-CARD-DEBT-8.md`（round-N 结果以文件为准）

## ⛔ 本卡未证明什么（必填）

1. `tests/api/v1/endpoints/test_fsrs_state_api.py` **未跑**（lifespan 连现网 7691）——待 CARD-TEST-isolate-lifespan（W4②）合入主干后由主 session 补跑。
2. **全量 `tests/unit` 未跑**（含 8 个 lifespan 文件，同上）——过渡期判据收窄为 `-k "fsrs or review_service or story_38_3"`（193 passed），全量由主 session 在含 ② 的主干补跑。
3. HTTP 层面：`get_fsrs_state` 的新键**透不到** HTTP 响应（见移交项 1）——本卡只证明了 service 层诚实性，未证明端到端可见性。
4. 「真实库零变化」由同进程对照探针 + 存量 193 测试证明，未在真实 7691 部署上端到端复验。
5. 本机 py-fsrs 在位，fallback 分支的**长期**生产行为（真发生库损坏时）无实机演练，仅有子进程模拟。
