"""CARD-W4-FINAL-ACCOUNTING 负控变异器：把 (c) 新加的嵌套 try/except BaseException 删掉，
还原成 UNPROTECTED 形态，用来证明两个判据真能翻转（不是恒绿）。

严格是 (c) 修法的逆操作：NEW -> OLD，恰 1 处命中，净减 3 行。
跑完必须由调用方的 EXIT trap 无条件还原（禁 git stash / 禁 git checkout）。
"""
import sys
from pathlib import Path

p = Path('backend/tests/support/live_port_guard.py')
src = p.read_text(encoding='utf-8')

OLD = (
    '        except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账\n'
    '            print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)\n'
)
NEW = (
    '        except Exception as exc:  # noqa: BLE001 —— 落盘失败要说话，但不能盖掉结账\n'
    '            try:\n'
    '                print(f"*** W4 guard: 账本落盘失败 {path}: {exc!r} ***", file=sys.stderr)\n'
    '            except BaseException:  # noqa: BLE001 —— 可观测性不得挡在强制退出前面\n'
    '                pass\n'
)

n = src.count(NEW)
if n != 1:
    print(f'ABORT: 期望命中恰 1 处 NEW，实测 {n}', file=sys.stderr)
    sys.exit(2)

out = src.replace(NEW, OLD)
delta = len(out.splitlines()) - len(src.splitlines())
if delta != -3:
    print(f'ABORT: 净变行数不是 -3，实测 {delta}', file=sys.stderr)
    sys.exit(2)

tmp = p.with_suffix('.py.tmp-nc')
tmp.write_text(out, encoding='utf-8')
tmp.replace(p)
print(f'NC mutated ok; 行数 {len(src.splitlines())} -> {len(out.splitlines())}')
