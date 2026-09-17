"""CARD-W4-FINAL-ACCOUNTING 判据 1：_final_accounting 内每个 print 是否被 except BaseException 护住。

判据是逐 print 的 protected/UNPROTECTED 名单（不是只数个数——等长替换会混淆计数）。
改前（B14_BASE 08100483）期望：1512 UNPROTECTED / 1523 protected / 1530 protected。
改后期望：三行全 protected，grep -c UNPROTECTED = 0。
⛔ 行号不写死进判据——以本树实测名单为准（修法在 :1511 except 体内净增 3 行，print 各下移 +1/+3/+3）。
从车道树根跑（按相对路径 backend/tests/support/live_port_guard.py 打开）。
"""
import ast

src = open('backend/tests/support/live_port_guard.py', encoding='utf-8').read()
fn = [n for n in ast.walk(ast.parse(src)) if getattr(n, 'name', '') == '_final_accounting'][0]
rows = []
for n in ast.walk(fn):
    if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'print':
        prot = any(
            isinstance(a, ast.Try) and a.lineno < n.lineno <= a.end_lineno
            and any(isinstance(h.type, ast.Name) and h.type.id == 'BaseException' for h in a.handlers)
            for a in ast.walk(fn) if isinstance(a, ast.Try)
        )
        rows.append((n.lineno, 'protected' if prot else 'UNPROTECTED'))
# ⚠️ 必须 sorted 后再打印：ast.walk 是 BFS，原样顺序实测是 1523/1512/1530（非升序），
#    不排序会让「输出与期望名单逐字比对」在完全正常的树上报不一致（假红）。
for lineno, verdict in sorted(rows):
    print(lineno, verdict)
