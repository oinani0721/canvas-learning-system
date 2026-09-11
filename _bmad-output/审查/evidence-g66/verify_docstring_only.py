"""对 hunk 2（DST 门的 docstring）做精确证明：函数体除 docstring 外的 AST 完全相同。

judge v3 的行级判据不认 docstring（它只剥 # 与 //），所以那个 hunk 报了 ✗。
这里用 ast：取两个版本里 test_g66_tomorrow_survives_dst_transitions 的函数节点，
去掉 docstring 后 ast.dump 逐字节比对。AST 不含注释，所以相同 = 除 docstring 外一切未变。
"""

import ast
import subprocess

REPO = (
    "/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u6-reviewtime"
)
PATH = "backend/tests/unit/test_review_overview.py"
FN = "test_g66_tomorrow_survives_dst_transitions"


def fn_ast(rev):
    src = subprocess.run(
        ["git", "-C", REPO, "show", f"{rev}:{PATH}"], capture_output=True, text=True, check=True
    ).stdout
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == FN:
            body = list(node.body)
            # 去掉 docstring（函数体首个纯字符串表达式）
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                doc = body[0].value.value
                body = body[1:]
            else:
                doc = None
            stripped = ast.FunctionDef(
                name=node.name, args=node.args, body=body, decorator_list=node.decorator_list,
                returns=node.returns, type_comment=None, type_params=[],
            )
            return ast.dump(ast.fix_missing_locations(stripped), annotate_fields=True), doc
    raise SystemExit(f"没找到 {FN}")


a_ast, a_doc = fn_ast("1ccc9711")
b_ast, b_doc = fn_ast("dc6cfb17")

print(f"函数: {FN}")
print(f"  去掉 docstring 后 AST 相同: {a_ast == b_ast}   ← AST 不含注释, 相同即「除 docstring 外一切未变」")
print(f"  docstring 变了:            {a_doc != b_doc}")
if a_ast != b_ast:
    print("  ⚠ AST 不同 —— 本轮**不是**纯注释改动")
print()
print("反例自检（同一判据跑 BASE→HEAD，那时这个函数还不存在 / 或内容不同）:")
try:
    base_ast, _ = fn_ast("72ab01ed")
    print(f"  BASE 上该函数存在, AST 与 HEAD 相同: {base_ast == b_ast}（应为 False）")
except SystemExit as e:
    print(f"  {e} ⇒ 该函数是本卡新增的, 判据对『函数存在与否』敏感 ✓")
