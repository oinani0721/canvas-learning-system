"""冷启动布防探针 (CARD-TEST-bark-autostub-R1 完成条件 (c) 的取证载体)。

为什么必须单独一个文件: (c) 说的「冷启动」= **守卫自己**那次 import 才是
send_bark 在本进程里的首次加载。bark_egress_probe.py 与
test_daily_review_run.py 都在模块顶层 `import daily_review_run`
(→ send_bark), 那是 collection 期、早于 fixture, 于是永远走不到冷启动分支
—— 拿它们做 (c) 的判据等于给一条恒不执行的分支加门 (假门)。

本文件因此**刻意不在顶层 import** 任何 scripts 模块; 也刻意不带 test_ 前
缀 (默认收集不到, regression collect 计数不变), 靠 conftest 的
_BARK_GUARDED_MODULES 精确名布防。

残留判据本身不在这里 —— 它必须在 fixture teardown **之后**看, 由
backend/scripts/bark_keyfile_residue_check.py 在同一解释器内跑完本条测试
后检查 sys.modules["send_bark"].KEY_FILE。本文件只负责证明「冷启动路径确实
被走到了」, 否则残留检查会在一个没发生过冷启动的进程里空转报绿。
"""

import sys
from pathlib import Path

#: 只把 scripts/ 放进 sys.path, **不** import 其中任何模块 —— 冷启动语义靠
#: 「send_bark 未被加载」成立, 与路径可见性无关。不放的话卸甲形态会先炸
#: ModuleNotFoundError, 篡改门就红在导入上而不是红在指定断言上 (红了但红
#: 错原因 = 假门, R1 负控首跑当场抓出)。
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))


def test_coldstart_keyfile_redirected():
    """armed: 守卫在 lazy import 之前重定向 BARK_KEY_FILE, 因此这次冷启动
    加载出来的 send_bark.KEY_FILE 必须落在守卫的 bark-guard-* 临时目录里。

    卸甲 (--noconftest) 形态下 send_bark 在本行才首次加载, KEY_FILE = 本机
    真实默认位置 → 必红。两形态都只比较路径, 不读 key 内容。"""
    import send_bark

    kf = Path(send_bark.KEY_FILE)
    assert kf.parent.name.startswith("bark-guard-"), (
        f"BARK-GATE-CS-COLDSTART: 冷启动未落在守卫 tmp 目录 (KEY_FILE={kf})"
    )
    assert kf.exists(), f"BARK-GATE-CS-EXISTS: 守卫假 key 不存在 ({kf})"
