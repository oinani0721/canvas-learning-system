# 验收单 · CARD-G3-4 FSRS golden vectors 防漂移门

> **批次**: BATCH-2026-08-28-第五批 · 车道 S3 第二卡
> **分支**: `card/s3-events`（不 push，等你验收）
> **日期**: 2026-08-28
> **一句话**: 给你的复习调度算法拍了一张"标准照"——用真实 fsrs 6.3.1 库在完全固定的条件下
> 算出 20 个关键场景的标准答案并冻结入库。以后任何人升级依赖、任何库版本悄悄改了算法权重，
> 回归测试会**立刻翻红**，你的复习间隔不会在不知情时被悄悄改变。

---

## 一、这对你意味着什么（用户视角）

没有界面变化。它保的是：**你今天评一个"记得"，系统排给你的下次复习日期，
明年重装环境后还是同一个日期**。三类会被当场抓住的漂移：

1. 有人把 `fsrs` 升到 6.4.x/7.x → 测试红（要求先重新评审冻结基线）；
2. 库版本没变但默认算法参数（21 个权重）变了 → 测试红；
3. golden 文件本身被误改/篡改 → 完整性 hash 测试红。

## 二、技术判据（Claude 已代跑）

| 裁判 | 结果 |
|---|---|
| 新建 `backend/tests/regression/test_fsrs_golden_vectors.py` | **11 passed 全绿**（Codex 一轮整改后：七门） |
| 现有 fsrs 套件不回归 | `test_fsrs_manager.py` / `test_create_fsrs_manager.py` / `test_fsrs_state_query.py` / `test_fsrs_bridge.py` / `test_fsrs_legacy_state_zero.py` / `test_fsrs_new_card_none_serialization.py` = **91 passed** + 扩面 `test_review_service_fsrs.py` / `test_story_38_3_fsrs_init_guarantee.py` / `test_mastery_engine_fsrs.py` / `test_fsrs_state_api.py` / `test_review_fsrs_degradation.py`（e2e）= **100 passed**，合计 191/191 零回归 |
| 向量覆盖 | **5 关键态 × 4 评分 = 20 向量**：新卡首评 / Learning 第二步 / Review 准时 / **Review 逾期 30 天** / Relearning（`state_before_final_review` 字段逐条可核）+ retrievability 曲线 3 点（due/+7d/+30d） |
| 确定性 | 固定 card_id + 固定 UTC 时刻链 + `enable_fuzzing=False`；生成器**连跑两次 byte 级一致** |
| manifest 锁定面 | library_version=6.3.1 / algorithm=FSRS-6（21 参数）/ timezone=UTC / params_hash（sha256 canonical）/ Rating&State 枚举值域 |
| requirements 钉版 | 根与 backend 两处 `fsrs==6.3.1`（原 `>=6.0.0,<7.0.0` 范围约束收紧），且有测试防松绑回潮 |
| **负验证 v2（留档，SHA-bound）** | 8 变体全部按预期翻红并恢复：params_hash 篡改→1 门红 / 向量篡改→1 门红 / **仅改 manifest 版本→恰 3 门红**（与 Codex 复算一致）/ 重复向量→结构门红 / retrievability 清空→结构门红 / 容差放宽→上限门红 / 前态=999→双门红 / 恢复后文件 sha256 与基线全等 + 11 passed（存证含完整命令、失败测试名、pytest exit code、前后 SHA：`审查/g3-4-evidence/g3-4-negative-verification.txt`） |
| 真实库验收 | `FSRS_AVAILABLE` 断言在位——库缺失是 FAIL 不是 skip，零 mock 零 FakeCard |
| 铁律遵守 | `fsrs_manager.py` **零改动**（in-flight D4 锁定；测试只经其公开 re-export 出口消费）；不改任何调度逻辑 |
| ruff | All checks passed |

## 三、算法合理性抽查（冻结值一眼可信）

- 新卡 Again 停 Learning 步 0（1 分钟后重来）；Good 进步 1（10 分钟）；Easy 直升 Review（+8 天）
- Review 态逾期 30 天后答对，stability 增益显著大于准时答对（38.19 vs 10.97）——间隔效应，符合 FSRS-6 语义
- Review 答 Again 落 Relearning，Good/Easy 从 Relearning 回 Review
- retrievability 单调衰减：0.909（到期日）→ 0.785（+7d）→ 0.661（+30d）

## 四、交付物清单

| 文件 | 说明 |
|---|---|
| `backend/scripts/generate_fsrs_golden_vectors.py` | 确定性生成器（仅评审后重冻结时重跑） |
| `backend/tests/regression/fsrs_golden_manifest.json` | versioned manifest（版本/算法/时区/参数 hash/枚举面/容差） |
| `backend/tests/regression/fsrs_golden_vectors.json` | 20 向量 + 3 retrievability 点（自包含绝对时刻，不依赖生成器） |
| `backend/tests/regression/test_fsrs_golden_vectors.py` | 五门回归测试 |
| `requirements.txt` / `backend/requirements.txt` | `fsrs==6.3.1` 精确钉版 |

## 五、Codex 审查处置（一轮 → 整改全落地）

一轮存档 `_bmad-output/审查/codex-review-CARD-G3-4-2026-08-28.md`（裁定"需整改"：1 BLOCKER + 2 HIGH + 3 MEDIUM + 1 LOW）。逐条处置：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| c | **BLOCKER** | golden 测试不在 test.yml 显式清单，root requirements.txt 不在 paths trigger——CI 自动控制面五门均不执行 | **登记移交（本卡不可修）**：`.github/workflows/` 为第五批 **S8 车道独占**（开跑手册 V2 合同点）且 test.yml 零改动纪律。移交条款：主 session 合并后 micro-patch 把 `test_fsrs_golden_vectors.py` + `test_learning_events_schema_contract.py` 两行加入 test.yml 白名单、root `requirements.txt` 加入 paths trigger。测试文件 docstring 已注明。**在 CI 接入前，防漂移门的执行面 = 本地 pytest + Codex/主 session 复核**（如实声明，不装 CI 已生效） |
| b | HIGH | 矩阵结构可篡改后全绿（重复向量/缺格/前态=999/retrievability 清空/algorithm='arbitrary' 均不红） | **已修（代码）**：新增门 5（manifest 元数据字面锁）+ 门 6（矩阵结构：5×4 组合全集、20 唯一 id、每场景前态字面锁、retrievability 恰 3 点升序）；重放门升级为**先重放前缀断言 state_before 实测值**再评最终分。全部 Codex 反例负验证 v2 翻红留档 |
| — | HIGH/MEDIUM | 容差直接信任 manifest，放宽可静默削弱浮点门 | **已修（代码）**：`test_tolerance_ceiling_locked` 锁上限（rel ≤1e-9、abs ≤1e-12），manifest 单方放宽即红（负验证 N6） |
| — | MEDIUM | requirements 正则 `^fsrs==6.3.1\b` 放过 `.post1`/marker | **已修（代码）**：改严格逐行解析——去注释、包名恰为 fsrs、整行全等 `fsrs==6.3.1`，且每份文件恰一行 |
| — | MEDIUM | "只消费 fsrs_manager 公开接口"表述不成立（无 `__all__`，实际驱动第三方 Scheduler） | **已修（口径）**：库对象改为直接 `from fsrs import`，仅保留 `FSRS_AVAILABLE` 生产模块在位断言；docstring 明示不再作"公开接口"宣称。fsrs_manager.py 零接触不变 |
| — | MEDIUM | 负验证存证无完整命令/exit code/失败名/前后 SHA；N3 描述与实际操作不符（改两文件才 2 红） | **已修（存证）**：负验证 v2 重做——8 变体、完整命令、失败测试名、pytest exit code、基线与恢复后 sha256 全等证明；N3 改为"仅改 manifest"变体，实测**恰 3 门红**与 Codex 复算一致 |
| a | LOW | `write_text` 未定 newline，Windows 重生成可产 CRLF | **已修（代码）**：生成器两处 `newline="\n"` |
| a | LOW | 跨 CPU/libm 末位浮点 bytes 未物理验证 | **如实登记不修**：基线在本机（darwin/arm64, Python 3.14.4）生成；跨平台复现属容差设计承担面（rel=1e-9），无异构环境可实测，不作宣称 |

整改后复跑：golden 门 11 passed、核心 fsrs 六文件 91 passed 复跑零回归、ruff 全过。

## 六、移交登记

1. **CI 接入（Codex 一轮 BLOCKER）**：test.yml 白名单 +2 行与 root requirements paths trigger——S8 车道独占 `.github/workflows/`，移交主 session 合并后 micro-patch（见处置表 #c）。
2. `FSRSManager.review_card()` 不透传 `review_datetime`（`fsrs_manager.py` D4 锁定禁改）——golden 测试直接驱动 fsrs `Scheduler`；若未来希望 manager 层也可确定性重放，需在 D4 解锁后加可选参数（登记，不阻塞本卡）。
3. `FSRSManager` 生产默认 `enable_fuzzing=True`（库默认）——golden 基线冻结的是**算法核**（fuzz 关闭下的确定性行为）；fuzz 开启路径的调度带随机模糊属库设计语义，不在防漂移门范围，如实声明。
