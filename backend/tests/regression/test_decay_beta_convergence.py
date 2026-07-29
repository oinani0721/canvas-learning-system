"""批次2' A1 衰减 Beta 收敛性质锁定 (MEM-FLYWHEEL-2026-07-22, 对账 §2 quick-spec)。

被测对象 = canvas-vault/.claude/scripts/decay_beta.py (单一真相源, quiz-answer
写分与 start-exam-board 选点共用同一模块)。

quick-spec 要求的两组测试: σ 单调性 (3/10/100 次模拟观测) + 状态跳变跟踪。
"""

import sys
from pathlib import Path

VAULT_SCRIPTS = Path(__file__).resolve().parents[3] / "canvas-vault" / ".claude" / "scripts"
sys.path.insert(0, str(VAULT_SCRIPTS))

import decay_beta as dbeta  # noqa: E402


def _simulate(grades, a=dbeta.PRIOR_A, b=dbeta.PRIOR_B):
    for g in grades:
        a, b = dbeta.update(a, b, g)
    return a, b


# ── σ 单调性 (quick-spec 组 1): 越考越准 ──


def test_sigma_decreases_with_observations_3_10_100():
    sigmas = []
    for n in (3, 10, 100):
        a, b = _simulate([0.8] * n)
        sigmas.append(dbeta.sigma(a, b))
    assert sigmas[0] > sigmas[1], "10 次观测应比 3 次更准"
    # γ 打折下 σ 收敛到平台 (有效窗口 ~10 次), 100 次不应比 10 次更差
    assert sigmas[2] <= sigmas[1] * 1.05


def test_sigma_converges_but_never_zero():
    """γ 打折给出 σ 下界 — 永远保留复习压力, 不像纯 Beta 趋于零置盲。"""
    a, b = _simulate([1.0] * 200)
    assert dbeta.sigma(a, b) > 0.01
    # 有效样本量上界 = 1/(1-γ) + 先验质量, 远小于 200
    assert a + b < 1.0 / (1.0 - dbeta.GAMMA) + dbeta.PRIOR_A + dbeta.PRIOR_B


# ── 状态跳变跟踪 (quick-spec 组 2): 学会了要能追上 ──


def test_mastery_recovers_after_state_jump():
    """20 次低分后连续 10 次满分, μ 必须恢复到 0.7 以上 (纯 Beta 做不到)。"""
    a, b = _simulate([0.2] * 20)
    assert dbeta.mu(a, b) < 0.4, "前置: 低分期 μ 应在低位"
    a, b = _simulate([1.0] * 10, a, b)
    assert dbeta.mu(a, b) > 0.7, "衰减 Beta 应在 ~10 次内跟上状态跳变"


def test_pure_beta_would_lag_decay_beta_catches_up():
    """对照: 同样序列下无打折 (γ=1) 的纯 Beta 恢复更慢 — 合成方案的存在理由。"""
    a1, b1 = dbeta.PRIOR_A, dbeta.PRIOR_B
    a2, b2 = dbeta.PRIOR_A, dbeta.PRIOR_B
    for g in [0.2] * 20 + [1.0] * 10:
        a1, b1 = dbeta.update(a1, b1, g)  # γ=0.9
        a2, b2 = dbeta.update(a2, b2, g, gamma=1.0)  # 纯 Beta
    assert dbeta.mu(a1, b1) > dbeta.mu(a2, b2) + 0.1


# ── 迁移与选点 ──


def test_from_legacy_preserves_mean_low_confidence():
    a, b = dbeta.from_legacy(0.6)
    assert abs(dbeta.mu(a, b) - 0.6) < 0.01
    assert a + b <= 3.01, "legacy 只配等效样本量 3 的置信"
    # 极端值不退化 (σ > 0)
    for m in (0.0, 1.0):
        a, b = dbeta.from_legacy(m)
        assert dbeta.sigma(a, b) > 0


def test_pick_score_breaks_p3_deadlock():
    """P3 死循环: argmin μ 会锁死最低分节点。μ−σ 下, 考熟的低分节点
    (σ 收窄) 应让位给从未考过的节点 (先验 σ 大)。"""
    # 节点 X: 考了 30 次, 分数稳定 0.45 (旧逻辑: μ 最低者永远是它)
    ax, bx = _simulate([0.45] * 30)
    # 节点 Y: 从未考过 (先验, μ=0.30 更低但 σ 大)
    ay, by = dbeta.PRIOR_A, dbeta.PRIOR_B
    assert dbeta.pick_score(ay, by) < dbeta.pick_score(ax, bx), "未考节点应优先于考熟的低分节点"


def test_update_clamps_grade():
    """F3 回归: grade_norm 越界 (LLM 误传 1-4 分) 必须钳制。"""
    a, b = dbeta.update(dbeta.PRIOR_A, dbeta.PRIOR_B, 3.5)
    assert dbeta.mu(a, b) <= 1.0
    a, b = dbeta.update(dbeta.PRIOR_A, dbeta.PRIOR_B, -1.0)
    assert dbeta.mu(a, b) >= 0.0


# ── 读时时效项 + 闲置感知评分 (终审 A1/A2, DAILY-REVIEW-PUSH-2026-07-29) ──

import pytest  # noqa: E402


@pytest.mark.parametrize("days", [0, 30, 69, 365, 3650])
def test_effective_preserves_mu(days):
    """A1: 同比缩放下 μ 严格不变 (无 FLOOR — 逐坐标截断会使 μ 漂向 0.5)。"""
    a2, b2 = dbeta.effective(9.0, 1.0, days)
    assert dbeta.mu(a2, b2) == pytest.approx(0.9, abs=1e-12)


def test_effective_sigma_monotonic_with_idle():
    """A1: σ 随闲置天数单调回升 (久不考 → 不确定度上升)。"""
    values = [dbeta.sigma(*dbeta.effective(4, 6, d)) for d in (0, 30, 69, 180, 365)]
    assert values == sorted(values) and values[0] < values[-1]


def test_effective_future_timestamp_clamps():
    """A1: 未来时间戳 (负 days_idle) 钳到 0 — 不放大置信度。"""
    assert dbeta.effective(4, 6, -10) == pytest.approx((4.0, 6.0))


def test_effective_rejects_corrupt_state():
    """A1 适配: 非正参数 = 数据损坏, 抛错由批处理调用方逐节点跳过。"""
    with pytest.raises(ValueError):
        dbeta.effective(0.0, 2.0, 10)


def test_effective_evidence_half_life_69_days():
    """口径修正: 69 天是证据质量 n=a+b 的半衰期 (0.99^69≈0.5), 不是 σ 的。"""
    a2, b2 = dbeta.effective(4, 6, 69)
    assert (a2 + b2) / 10.0 == pytest.approx(0.5, abs=0.01)


def test_update_after_idle_kills_confidence_revival():
    """A2 病理锁定: a=9,b=1 闲置 365 天后答错, 节点必须比考前更紧急。
    旧写法 (裸 update 原始 a,b) 的 pick 反而升高 0.632→0.692 — 作对照钉死。"""
    a, b = 9.0, 1.0
    pick_before = dbeta.pick_score(*dbeta.effective(a, b, 365))
    a2, b2 = dbeta.update_after_idle(a, b, 0.0, 365)
    assert dbeta.pick_score(a2, b2) < pick_before, "答错后必须更紧急"
    a3, b3 = dbeta.update(a, b, 0.0)
    assert dbeta.pick_score(a3, b3) > pick_before, "对照: 旧写法正是置信度复活病理"


def test_update_after_idle_zero_days_equals_update():
    """A2: 无闲置时退化为普通 update — 连续考察日行为不变。"""
    assert dbeta.update_after_idle(4, 6, 0.7, 0) == pytest.approx(dbeta.update(4, 6, 0.7))


def test_effective_underflow_guard():
    """Code-Review M2 回归: last_examined 年份打成 0001 (≈74 万天) 时
    0.99^d 下溢为 0 → 除零崩全轮。下限防护后必须保持正参数且 pick 可算。"""
    a2, b2 = dbeta.effective(2.0, 3.0, 739825)
    assert a2 > 0 and b2 > 0
    dbeta.pick_score(a2, b2)  # 不得抛 ZeroDivisionError
    assert dbeta.mu(a2, b2) == pytest.approx(0.4, abs=1e-9)  # μ 不变契约仍守住
