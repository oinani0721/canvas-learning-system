"""批次2' A1 — 带遗忘因子的 Beta 后验 (衰减 Beta) 掌握度收敛算法。

MEM-FLYWHEEL-2026-07-22, 对账 §2 合成方案 (2026-07-23 用户默认拍板):
  - 纯 EMA (α=0.5 恒权) 不收敛: 考 100 次和考 3 次估计精度一样 → 已弃
  - ChatGPT 纯 Beta 后验收敛但僵化: a,b 无限累计, 新证据边际影响趋零,
    与「越考越准」矛盾 (非平稳性盲点) → 拒绝原版
  - 合成: 每次观测前按 γ 打折 (有效记忆窗口 ~1/(1-γ)=10 次), 收敛且能
    跟随掌握状态跳变; σ 解析可得, 不再拍脑袋探索项

被四方共用 (单一真相源):
  - quiz-answer SKILL 静态 python 段 (写分): update_after_idle / mu / from_legacy
  - start-exam-board SKILL 选点段: pick_score (μ−β·σ, 低者优先考)
  - scripts/daily_review_pick.py (每日推送选板): effective + pick_score
  - backend/tests/regression/test_decay_beta_convergence.py (数学性质锁定)
"""

import math

#: 先验 Beta(0.9, 2.1) — 均值 0.30 (与旧 EMA 默认档一致), 等效样本量 3
#: (比 ChatGPT 提案的 2 稍保守, 抗首评噪声)
PRIOR_A = 0.9
PRIOR_B = 2.1

#: 遗忘因子 — 每次观测前 a,b 同乘 γ, 有效记忆窗口 ~1/(1-γ) = 10 次观测
GAMMA = 0.9

#: 选点探索权重 (μ − β·σ)
BETA_EXPLORE = 1.0

#: 质量地板 — 防连续同质证据下 γ 打折把 a 或 b 衰减到零 (Beta(n,0) 退化
#: 分布 σ=0, 「永远保留复习压力」承诺被破坏; 单测抓到的边界)。
#: 代价: μ 上限从 1.0 降到 ~0.995, 可忽略。
FLOOR = 0.05


def update(a: float, b: float, grade_norm: float, gamma: float = GAMMA):
    """一次评分观测: 先打折 (遗忘), 再累计证据。返回 (a', b')。"""
    grade = max(0.0, min(1.0, float(grade_norm)))
    a, b = gamma * a, gamma * b
    return max(a + grade, FLOOR), max(b + (1.0 - grade), FLOOR)


def mu(a: float, b: float) -> float:
    """掌握度点估计 (Beta 均值)。"""
    return a / (a + b)


def sigma(a: float, b: float) -> float:
    """掌握度不确定度 (Beta 标准差, 解析)。"""
    n = a + b
    return math.sqrt(a * b / (n * n * (n + 1.0)))


def from_legacy(mastery_score: float, pseudo_n: float = 3.0):
    """旧 EMA 的 mastery_score → 初始 (a, b)。

    继承已有掌握度但只给等效样本量 3 的置信 (与先验同量级) — 老分数是
    恒权 EMA 产物, 不配高置信。0/1 极端值钳到 0.05 防 σ 退化为零。
    """
    m = max(0.0, min(1.0, float(mastery_score)))
    return max(0.05, m * pseudo_n), max(0.05, (1.0 - m) * pseudo_n)


def pick_score(a: float, b: float, beta: float = BETA_EXPLORE) -> float:
    """选点分 = μ − β·σ, 越低越优先考。

    σ 项破解 P3 死循环 (旧逻辑 argmin μ 把最低分节点锁死循环考):
    久考节点 σ 收窄退出竞争, 久不考节点被 γ 间接抬 σ 回到候选池。
    """
    return mu(a, b) - beta * sigma(a, b)


#: 读时时效折扣 — 每闲置 1 天 a,b 同乘 γ_d。证据质量 n=a+b 半衰期 ≈69 天
#: (0.99^69≈0.5)。σ 无统一半衰期: σ²=μ(1−μ)/(n·f+1), 随闲置向上限渐近
#: 回升, 回升速度取决于节点已有证据量 (ChatGPT 终审 A1 口径, 2026-07-29)。
GAMMA_DAILY = 0.99


def effective(a: float, b: float, days_idle: float, gamma_daily: float = GAMMA_DAILY):
    """读时时效: a,b 同比缩放 → μ 严格不变, σ 随闲置回升。纯读时, 不写回。

    ⛔ 无 FLOOR — 逐坐标截断会破坏 a:b 比例使 μ 长期漂向 0.5 (先验
    288 天起漂移, 双触底后被强改 0.50; 终审 A1)。存量 a,b 经 update()/
    from_legacy() 恒 ≥ FLOOR>0, 同比缩放不产生无效 Beta 参数。
    非正参数 = 数据损坏 → 抛错, 批处理调用方逐节点捕获跳过 (不崩全轮)。
    """
    a, b = float(a), float(b)
    if a <= 0.0 or b <= 0.0:
        raise ValueError(f"Beta 参数必须为正: a={a}, b={b}")
    f = gamma_daily ** max(0.0, float(days_idle))
    # 下溢防护 (Code-Review M2): 病理 last_examined (如年份打成 0001) 的
    # 巨量天数会把 f 压到 0.0 → a=b=0 → pick_score 除零崩全轮。
    # 同比下限不破「μ 不变」契约, σ 已到达上限附近。
    f = max(f, 1e-150)
    return a * f, b * f


def update_after_idle(
    a: float,
    b: float,
    grade_norm: float,
    days_idle: float,
    gamma: float = GAMMA,
    gamma_daily: float = GAMMA_DAILY,
):
    """闲置感知评分: 先按闲置天数折旧旧证据, 再吸收新观测。

    防「置信度复活」(终审 A2): 裸 update(原始 a,b) 会让闲置期抬高的 σ
    被旧 n 一次评分瞬间抹平 — a=9,b=1 闲置 365 天答错, pick 反而
    0.632→0.692 变得更不紧急。旧证据最终权重 γ·γ_d^d: 按次 + 按时
    两层折扣机制不同, 有意复合 (非 double-discount 错误)。
    """
    a_eff, b_eff = effective(a, b, days_idle, gamma_daily)
    return update(a_eff, b_eff, grade_norm, gamma)
