- **阻断级**：[review_app.py:397](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/app/api/v1/endpoints/review_app.py:397)。`startMs < n.atMs` 无法区分同毫秒内的真实先后。最小场景：固定 `Date.now()=T`，隐藏态先挂起旧 GET，再完成 rebuild 并写入 `atMs=T`；旧 GET 返回重建前投影时 `T < T` 为假，pending 被删除并显示“数字已更新”。`pollGen` 未变化，挡不住该路径；[test_review_app.py:1745](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:1745) 未控制相等边界。

- **阻断级**：[test_review_app.py:362](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:362)。模块级 `init` 豁免对所有保护名开放，但 `definitions` 不统计 import/builtin 的既有绑定。向真实源码追加 `json = 0`、`list = 0` 或 `HTMLResponse = APIRouter()`，门均返回放行；随后 `/overview/app` 会在 `json.dumps`、`list(...)` 或响应构造处失败。`:460` 的“定义点唯一性”口径因此不成立。

- **阻断级**：[test_review_app.py:321](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:321)。Store 过滤没有漏掉真正的 `Name` 绑定；漏洞是非 `Name` 目标未受保护。`(json.dumps,) = (lambda value, **kwargs: "wrong",)`、`for json.dumps in (...)`、`json.__dict__["dumps"] = ...`、`_STATUS_META["ok"] = (...)` 均被放行，可直接改写白名单接收者；`del json` 也未检查。[`:524`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:524) 的“取别名改属性”探针先被 `alias = json` 拒绝，未证明属性规则。

- **阻断级**：[test_review_app.py:407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:407)。装饰器只检查 `Name`/`Attribute`，且 Attribute 不检查 receiver。`@__builtins__["print"]`、`@(lambda fn: fn)` 和非白名单接收者 `@D.get` 均放行，却会在导入期执行隐式调用。现有 `@print` 探针只覆盖裸 Name。四组 `_ALLOWED_*` 取值虽与基线逐字相同，但判定语义仍架空了白名单。

- **阻断级**：[test_review_app.py:439](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:439)。所有名为 `request` 的参数均无条件豁免，未验证其确为 `request: Request`。所谓合法反向探针 [`:532`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:532) 恰好没有注解：FastAPI 会把它当普通查询参数，缺参返回 422，传参后得到字符串，`request.url_for(...)` 失败；但 AST 门仍放行。

- **登记级**：[test_review_app.py:338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:338)。作用域判定存在具体误伤：`class Holder: json = 1` 只创建类属性，却被当成模块 `json` 重绑定；`:350` 还会拒绝 `def f(obj): obj.value = 1` 这类不涉及保护对象的普通属性赋值。四条反向探针未覆盖这些合法形态。

- **登记级**：[test_review_app.py:490](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b/backend/tests/unit/test_review_app.py:490)。矩阵没有独立覆盖 `TypeVar`、`ParamSpec`、`TypeVarTuple` 或 import alias；“嵌套自有定义”和“重复定义-class”又只匹配宽泛的“受保护名”，删除对应 scope/type 限制后仍可能被最终 duplicate 文案撞绿。验伪锚只能排除真实源码上的恒红，不能弥补这些分支证据缺口。

BLOCKER/HIGH 清零：否


