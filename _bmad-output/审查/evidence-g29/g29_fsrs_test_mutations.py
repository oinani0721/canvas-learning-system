#!/usr/bin/env python3
"""CARD-G2-9 (c) 的验伪 harness —— 原地变异 → **指定断言**必须红 → 无条件还原。

⛔ round-1 整改（Codex MEDIUM-3）：初版关掉了 traceback（``--tb=no``）并且把
**任何**非零退出码判为 KILLED。那只能证明"三次都出现了测试失败"，证明不了
"失败来自预期的那条断言"——被 collect error、被 import 失败、被任何一条无关断言
喂饱，判据都会一样地绿。这正是「判据必须绑定被哪一层拒的」那条老账。

现在每条变异声明 ``expect_nodeid`` + ``expect_assert``，判据是三条 AND：
  1. 进程退出码非 0
  2. 失败的测试**恰好**是点名的那个 nodeid（不多不少）
  3. 失败输出里含点名的断言消息片段

外加还原对账：跑前记全文件 sha，跑完逐字节复核（无条件 finally 还原）。
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

TGT = pathlib.Path("tests/regression/test_g29_dual_vault_fsrs_isolation.py")
PYTEST = "./.venv/bin/pytest"
NODE_MAIN = f"{TGT}::test_two_vaults_fsrs_and_notification_chain_isolated"
NODE_PUSH = f"{TGT}::test_vault_a_push_does_not_consume_vault_b_same_day_slot"

ORIG = TGT.read_text(encoding="utf-8")
BASE_SHA = hashlib.sha256(ORIG.encode()).hexdigest()

#: (名字, 锚点, 替换, 说明, 期望失败的 nodeid, 期望断言消息片段)
MUTS = [
    (
        "C1_global_state_file",
        'state = backups / f"daily-review.{vault.name}.state.json"',
        'state = backups / "daily-review.vaultA.state.json"',
        "state 文件退化成全局单例（C1a 修的那个根缺陷的观察器侧等价物）",
        NODE_MAIN,
        "A 的独有标识",
    ),
    (
        "C2_fsrs_due_ignored",
        'FUTURE_DUE = "2099-01-01T00:00:00Z"',
        'FUTURE_DUE = ""',
        "B 的 fsrs_due 被抹掉 ⇒ 变 New 卡即刻到期（FSRS 到期判定失效）",
        NODE_MAIN,
        "远未到期",
    ),
    (
        # ⚠️ 如实命名（round-2 复核 MEDIUM）：这条杀死的是 **LOW-4 的前提断言**
        #    （A 的产物里得有 A 自己的东西），不是它下游的交叉排除断言——
        #    texts_a 一旦读成 B 的投影，前提就先炸了，交叉排除根本没跑到。
        #    真正证明交叉排除承重的是下面的 C5。
        "C3_a_reads_b_projection__kills_precondition",
        "texts_a = _projection_texts(vault_a, backups)",
        "texts_a = _projection_texts(vault_b, backups)",
        "A 侧读到 B 的投影 ⇒ 打的是 LOW-4 前提断言（不是交叉排除）",
        NODE_MAIN,
        "A 的 json 里没有 A 自己的节点",
    ),
    (
        # ⛔ 这条才是交叉排除断言的验伪锚：往 vault A 的节点池里塞一个**未到期**、
        #    且挂在 B 的板上的节点。实测（scratchpad/c3probe）该节点会随板级 rollup
        #    进入 A 的 json 与 md，而 due_nodes 仍只有 A 自己的节点、A 的标识也都在
        #    ⇒ 三条前提**全部通过**，只有「A 的产物不含 B 的标识」这一条翻红。
        #    这是真实的交叉污染，不是把断言本身改坏。
        "C5_a_pool_carries_b_board_node",
        # 锚点取 vault_a + vault_b 两行：第一行在两个测试里相同，harness 的
        # 唯一性守卫会挡住二义锚点（它抓到的第一个真问题）。
        'vault_a = _vault(tmp_path, {A_NODE: _node(A_BOARD)}, name="vaultA")\n'
        '    vault_b = _vault(tmp_path, {B_NODE: _node(B_BOARD, fsrs_due=FUTURE_DUE)}, name="vaultB")\n',
        'vault_a = _vault(\n'
        '        tmp_path,\n'
        '        {A_NODE: _node(A_BOARD), B_NODE: _node(B_BOARD, fsrs_due=FUTURE_DUE)},\n'
        '        name="vaultA",\n'
        '    )\n'
        '    vault_b = _vault(tmp_path, {B_NODE: _node(B_BOARD, fsrs_due=FUTURE_DUE)}, name="vaultB")\n',
        "A 的节点池里混进一个挂在 B 板上的节点 ⇒ 打的正是交叉排除断言",
        NODE_MAIN,
        "A 的 outputs/今日复习.json 里出现了 B 的独有标识",
    ),
    (
        "C4_md_precondition_dropped",
        'assert A_NODE in texts_a["outputs/今日复习.md"], "A 的 md 里没有 A 自己的节点"',
        'assert True',
        "拿掉 md 的本库内容前提 —— 应当**不再**红（证明它是加性前提，不承担隔离结论）",
        None,  # 期望不红
        None,
    ),
]

FAIL_RE = re.compile(r"^FAILED (\S+)", re.M)


def run_pytest() -> tuple[int, str]:
    r = subprocess.run(
        [PYTEST, "-q", "-p", "no:cacheprovider", str(TGT), "--tb=line", "-rf"],
        capture_output=True,
        text=True,
    )
    return r.returncode, r.stdout + r.stderr


results = []
try:
    for name, old, new, what, want_node, want_msg in MUTS:
        n = ORIG.count(old)
        assert n == 1, f"{name}: 锚点命中 {n} 次（应为 1）—— 变异没打进去就不能记 SURVIVED"
        TGT.write_text(ORIG.replace(old, new), encoding="utf-8")
        rc, out = run_pytest()
        failed = FAIL_RE.findall(out)
        if want_node is None:  # C4：期望**不红**
            ok = rc == 0
            detail = f"rc={rc} failed={failed or '无'}（期望 rc=0）"
        else:
            node_ok = failed == [want_node]
            msg_ok = want_msg in out
            ok = rc != 0 and node_ok and msg_ok
            detail = (
                f"rc={rc} | 失败节点={'✓' if node_ok else '✗ ' + str(failed)} "
                f"| 断言消息{'✓' if msg_ok else '✗ 未见 ' + repr(want_msg)}"
            )
        results.append((name, ok, what, detail))
finally:
    TGT.write_text(ORIG, encoding="utf-8")

after = hashlib.sha256(TGT.read_text(encoding="utf-8").encode()).hexdigest()
restored = after == BASE_SHA
print(f"还原对账: {'OK 逐字节相同' if restored else '*** 未还原 ***'}  sha={BASE_SHA[:12]}")
print()
bad = []
for name, ok, what, detail in results:
    verdict = "KILLED" if ok else "SURVIVED"
    if not ok:
        bad.append(name)
    print(f"  {verdict:<9} {name}")
    print(f"            {what}")
    print(f"            {detail}")
print()
print("判据 = 退出码非 0 **且** 失败的正是点名的 nodeid **且** 输出含点名的断言消息。")
print("（C4 是反向锚：拿掉加性前提后应当不红，用来证明前三条的红不是被前提喂饱的。）")
sys.exit(1 if bad or not restored else 0)
