"""批次2' A1 — 带遗忘因子的 Beta 后验 (衰减 Beta) 掌握度收敛算法。

MEM-FLYWHEEL-2026-07-22, 对账 §2 合成方案 (2026-07-23 用户默认拍板):
  - 纯 EMA (α=0.5 恒权) 不收敛: 考 100 次和考 3 次估计精度一样 → 已弃
  - ChatGPT 纯 Beta 后验收敛但僵化: a,b 无限累计, 新证据边际影响趋零,
    与「越考越准」矛盾 (非平稳性盲点) → 拒绝原版
  - 合成: 每次观测前按 γ 打折 (有效记忆窗口 ~1/(1-γ)=10 次), 收敛且能
    跟随掌握状态跳变; σ 解析可得, 不再拍脑袋探索项

被三方共用 (单一真相源):
  - quiz-answer SKILL 静态 python 段 (写分): update / mu / from_legacy
  - start-exam-board SKILL 选点段: pick_score (μ−β·σ, 低者优先考)
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
