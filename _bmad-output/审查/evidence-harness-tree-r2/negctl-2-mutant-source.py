"""负控段② —— 只把 `_harness_contract` 的版本判据从 `== 1` 放宽成 `in (1, 2)`。

只拆这一格：`isinstance(_ver, bool)` 那半**保留**（所以 version_bool 格仍应绿），
形状 / 影子 / 纯函数探针一个字没动（所以 missing_name 等格仍应绿）。

期望：..._harness_contract_refuses[event_version_2] FAILED；
      [missing_name] / [version_bool] / [ts_re_rejects_z] / [validate_accepts_scalar]
      与控制组 ..._accepts_real_tree 仍 passed。
"""
p = "canvas-vault/.claude/skills/quiz-answer/SKILL.md"
t = open(p, encoding="utf-8").read()

OLD = "    if isinstance(_ver, bool) or _ver != 1:"
NEW = "    if isinstance(_ver, bool) or _ver not in (1, 2):"
assert t.count(OLD) == 1, f"锚点应恰 1 处, 实见 {t.count(OLD)}"
t2 = t.replace(OLD, NEW, 1)
assert t2 != t, "变异没生效"
assert t2.count("isinstance(_ver, bool)") == 1, "⛔ bool 那半被动了 = 拆了两层"
open(p, "w", encoding="utf-8").write(t2)
print("段② 变异已注入：EVENT_VERSION 判据 `!= 1` → `not in (1, 2)`（只动版本一格）")
