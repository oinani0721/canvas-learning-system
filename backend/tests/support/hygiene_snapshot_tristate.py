"""CARD-W4-SENTINEL-REBIND [BATCH-2026-09-11-第十四批] —— 卫生快照 sha 比对的三态。

``tests/unit/conftest.py`` 的卫生门在 session 首尾各取一次快照，对每个被跟踪文件记它的
sha256；**读不到时记 ``None``**（``_hygiene_snapshot()`` 的 ``except OSError`` 分支）。

原先的比对是 2-way 的 ``after != before``，于是两种 ``None`` 形态都被判错：

* ``None ↔ hash``（一次读到、一次没读到）⇒ 判成 ``pollution``（「文件被改写了」）——
  **假阳**：没读到不等于内容变了；
* ``None ↔ None``（两次都没读到）⇒ ``after != before`` 为假 ⇒ **静默**当「未变化」放过 ——
  **假阴**，而且是最坏的那种：把「没查完」当成了「没问题」。

第二种正是同文件 ``:302`` 注释所禁的事：「``cannot_check`` —— 是否违规尚不能判定,
门拒绝把「没检查」当「没问题」」。本模块把判定拆成三态，让 ``None`` 走 ``cannot_check``。
"""

from __future__ import annotations

#: 两侧都是 hash 且相等 —— 内容确实没变。
UNCHANGED = "unchanged"
#: 两侧都是 hash 且不等 —— 内容确实变了。
CHANGED = "changed"
#: 任一侧是 ``None`` —— 这一次没读到，**是否违规尚不能判定**。
UNCHECKED = "unchecked"


def classify_sha_change(before: str | None, after: str | None) -> str:
    """比对首尾两次快照里同一个文件的 sha，返回三态之一。

    :param before: session 开始时读到的 sha256，读不到为 ``None``。
    :param after: session 结束时读到的 sha256，读不到为 ``None``。
    :returns: :data:`UNCHANGED` / :data:`CHANGED` / :data:`UNCHECKED`。

    语义（三条，逐条对应一种真实情形）：

    * 两侧均为 hash 且**相等** ⇒ :data:`UNCHANGED`；
    * 两侧均为 hash 且**不等** ⇒ :data:`CHANGED`；
    * **任一侧为 ``None``（含 ``None ↔ None``）** ⇒ :data:`UNCHECKED`。

    ⛔ ``None ↔ None`` **不得**判 :data:`UNCHANGED`。``None`` 的含义是「这一次没读到」，
    不是「内容没变」：两次都没读到，恰恰说明这道门这两次**都没看见**这个文件，
    它是否被动过**无从判断**。判 unchanged 等于用「我没看」换「它没事」。

    ⚠️ 如实声明一条**本函数不覆盖**的情形：被跟踪文件若**真的被删**，两次都读不到
    ⇒ ``None ↔ None`` ⇒ :data:`UNCHECKED`。调用方拿到 unchecked 只知道「没查成」，
    不知道「因为它没了」。``exists`` 侧**覆盖不到**这一类 —— 实测
    ``_HYGIENE_SKELETON_PATHS``（``raw`` / ``wiki`` / ``outputs`` / ``CLAUDE.md``）与
    ``_HYGIENE_TRACKED_FILES``（``.gitignore`` / ``config/subject_mapping.yaml``）是
    **两批不相交的路径**，exists 侧根本不看被跟踪文件。
    （卡文 §五③ 写的「归 exists 侧覆盖」据此**不成立**，已登记移交。）
    相对旧实现这仍是严格改善：旧实现对同一情形是**静默放过**，现在至少会说「没查成」。
    """
    if before is None or after is None:
        return UNCHECKED
    return UNCHANGED if before == after else CHANGED
