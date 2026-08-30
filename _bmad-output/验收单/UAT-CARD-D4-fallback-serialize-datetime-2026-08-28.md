# 验收单 · CARD-D4 fallback serialize datetime 修复

> **批次**: BATCH-2026-08-27-Anki化与诚实收尾 · 车道 2 第二卡（顺手卡，独立 commit）
> **分支**: `card/m2-honest`（不 push，等你验收）
> **日期**: 2026-08-28

---

## 〇、如实定位

**近死码诚实评级 P3**：现网 fsrs 6.3.1 在位，FSRS_AVAILABLE=False 的 fallback 分支仅在环境损坏/未来 7.x 升级时激活。修的是写读不对称铁证：fallback create_card/_fallback_review 直出 raw datetime，serialize else 分支原样 json.dumps 三连崩 TypeError，而 deserialize 一直有 fromisoformat。**"FSRS_AVAILABLE 判不到底层 fsrs 缺失"问题按卡片纪律未碰（后续候选 DEBT-8）**。

## 一、你需要做什么（用户产品体验）

**没有任何要你操作的**。近死码防御修复，现网行为零变化（真实 fsrs 分支 diff 零改动）。

## 二、技术判据（Claude 已代跑，全部通过）

| 裁判 | 命令 | 结果 |
|---|---|---|
| 先红后绿 | 新增 2 探针测试实现前 | **2 failed**（TypeError 如预期）✅ |
| 判据套件 | `pytest tests/regression/test_fsrs_fallback_datetime_serialize.py tests/regression/test_fsrs_legacy_state_zero.py tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py -q` | **60 passed, 0 fail** ✅ |
| 真实分支零改动 | `git diff lib/memory/temporal/fsrs_manager.py` | **diff 只落 else 分支**（+6 行）✅ |
| due=None 绕过已删 | test_fsrs_legacy_state_zero.py 原 :200-201 | 删除后该文件仍全绿 ✅ |
| ruff | 3 个改动文件 | All checks passed ✅ |

### 修复内容

serialize_card else 分支：`due`/`last_review` 若为 datetime → isoformat（与 deserialize 的 fromisoformat 对称）。`last_review` 属防御性覆盖（fallback 卡当前不产该键）。新探针测试锁定：create→serialize→deserialize roundtrip 无 TypeError 且 due 等值还原；review_card 后与 card_to_state(...).card_data 同样可序列化（子进程屏蔽 fsrs import，沿用 legacy_state_zero 探针模式）。

### Codex 对抗审查

- 一轮（gpt-5.6-sol ultra）：`_bmad-output/审查/codex-review-CARD-D4.md` — **0 BLOCKER + 0 HIGH + 2 MEDIUM + 3 LOW**，行为修复裁定 PASS
- 关键 PASS 证据（Codex 独立验证）：真实 FSRS 分支前后 SHA-256 同为 `8f66a109…`，diff 只有 fallback else 内 +6/-0；HEAD 旧代码实测 create/review/card_to_state 三路径均 TypeError；四文件套件 60 passed
- MEDIUM 处置：
  - **M1 新测试文件未 staged**（`??` 状态）→ commit 时显式 `git add`，本卡 commit 流程内解决
  - **M2 goal-card 档案不在本分支 HEAD**（DD-14 追踪锚点跨分支）→ 如实入档：卡片档案按批次惯例存于 feature-obsidian-hybrid-dev worktree（绝对路径引用），三批均此模式，合并日主仓归档
- LOW×3 入档不扩（与卡范围纪律一致）：fallback 读侧 last_review 不还原（fallback 卡不产该键，无行为差异）；ZoneInfo DST 重叠时刻等值还原边界（fallback 自产值全 UTC）；子进程裸 assert 在 python -O 下的静默面（标准 pytest 不受影响）
- 条件性 BLOCKER 澄清：贴文 diff 路径前缀（`tests/…` vs `backend/tests/…`）是从 backend cwd 生成 diff 的呈现问题，实际文件在 `backend/tests/regression/`（Codex 以 worktree 为权威时该项不存在）

## 三、改动清单

- `backend/lib/memory/temporal/fsrs_manager.py` — serialize_card else 分支 +6 行（含注释），真实分支零改动
- `backend/tests/regression/test_fsrs_fallback_datetime_serialize.py` — 新文件，2 探针测试
- `backend/tests/regression/test_fsrs_legacy_state_zero.py` — 删 due=None 绕过 2 行
