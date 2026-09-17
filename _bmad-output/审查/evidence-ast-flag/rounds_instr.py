"""不动点轮数 instrument —— 本卡 (f) 选 _FIXPOINT_MAX_ROUNDS 的依据。

用法: rounds_instr.py <被测脚本路径> <该脚本里不动点 for 所在行号>

⛔ 行号必须随被测文件一起给，且本脚本把验伪锚做成 assert：若观测到的 range 调用行
   里没有它，说明锚已漂移、计数器从未被写过 —— 那一跑的直方图是全 0 的假数据。
   （本卡实测栽过一次：硬编码 634 的旧版在改动后漂到 687，产出 {0: 78}。）
"""
import ast, builtins, importlib.util as u, pathlib, sys

TARGET, FIX_LINE = pathlib.Path(sys.argv[1]).resolve(), int(sys.argv[2])
sys.argv = ["x"]
s = u.spec_from_file_location("n", TARGET); m = u.module_from_spec(s); s.loader.exec_module(m)

counter = {"n": 0, "lines": set()}
def counting_range(k):
    ln = sys._getframe(1).f_lineno
    counter["lines"].add(ln)
    if ln != FIX_LINE:            # 模块里还有别处 range()，只数不动点那一处
        return builtins.range(k)
    def gen():
        for i in builtins.range(k):
            counter["n"] = i + 1
            yield i
    return gen()
m.range = counting_range

def rounds(tree):
    counter["n"] = 0
    m._ModuleIndex(tree)
    return counter["n"]

print(f"被测文件: {TARGET}")
print(f"不动点 for 行号: {FIX_LINE}")
rounds(ast.parse("x = 1\n"))
assert FIX_LINE in counter["lines"], (
    f"验伪锚失败: 观测到的 range 调用行 {sorted(counter['lines'])} 不含 {FIX_LINE} "
    "—— 锚已漂移，本次计数全是 0，不是真数据"
)
print(f"验伪锚 OK：观测到的 range 调用行 = {sorted(counter['lines'])}（含 {FIX_LINE}）\n")

hist, worst = {}, []
for label, src in (*m._AST_MUST_FLAG, *m._AST_MUST_PASS):
    r = rounds(ast.parse(src)); hist[r] = hist.get(r, 0) + 1
    if r >= 3: worst.append(f"    轮数={r}  {label[:72]}")
print(f"A. 负控输入 {len(m._AST_MUST_FLAG)}+{len(m._AST_MUST_PASS)} 条 · 轮数直方图: {dict(sorted(hist.items()))}")
print("\n".join(worst) if worst else "    （无 >=3 轮）")

files = m.ast_scope_files(); hist2 = {}
for p in files:
    try: tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError: continue
    r = rounds(tree); hist2[r] = hist2.get(r, 0) + 1
print(f"\nB. 门的真实扫描面 {len(files)} 文件 · 轮数直方图: {dict(sorted(hist2.items()))}")
print(f"   达改前上限(4)的文件数 = {hist2.get(4, 0)}")
