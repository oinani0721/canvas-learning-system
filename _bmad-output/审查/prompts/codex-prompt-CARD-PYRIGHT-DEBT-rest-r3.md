# 一 背景与最小读取面

你在审查 Canvas Learning System 后端的一次**类型层清理**改动：卡 CARD-PYRIGHT-DEBT-rest（第十三批 U2 车道）阶段 2。
目标是让 `pyright` 在 `backend/app` 的**非 `services/` 面**归 0，且**运行期语义零变化**。

⛔ 只读审查。不连任何数据库，不跑 integration/e2e。

**最小读取面（只看这些，不要扩大）**：

```
git diff 286178d8 9c2ee90b -- backend/app/api/v1/endpoints/review.py backend/app/api/v1/system.py backend/app/services/exam_service.py
```

> `9c2ee90b` = 本卡阶段 2 最终 commit（车道 tip）。基线 `286178d8` 是主干候选树（本卡已 merge 它）。

配套材料（按需读，不必全读）：
- 验收单：`_bmad-output/验收单/UAT-CARD-PYRIGHT-DEBT-rest-2026-09-11-v2.md`（§二 判据表、§三 逐点等价证明、§四 未证明清单）
- 证据目录：`_bmad-output/审查/evidence-pyright-rest/`（2026-09-11 的文件是阶段 2 的）
- services 残余清单（**不属本卡**，仅供你确认残余确实全在 services）：`evidence-pyright-rest/services-residual-20260911T084046.txt`

# 二 作者自述（请独立核对，不要照单全收）

1. 改动恰好 3 个文件；`review.py` / `system.py` 只叠类型层，未改任何判定逻辑、返回值、状态码或日志内容。
2. `backend/app/services/exam_service.py` 是**整文件从 `card/u1-pyright-svc` 原样带入**（裁定 D-29 单文件 crossover），
   本卡**一个字未改**，与该分支 sha256 逐字节相同；集成时以 U1 版本为准。**该文件的内容本身不属本卡审查范围**，
   但「带入是否干净、是否引入运行期变化」属本卡范围。
3. `review.py` 的海象改写 `(nid := n.get("id")) is not None and nid in difficulty_map and difficulty_map[nid].is_mastered`
   与原式等价，依据是 `difficulty_map` 键填充处（`review.py` 约 :322-330）有 `if nid and diff is not None` 守卫 ⇒ None 永不入键集。
4. `system.py` 的 `Field(0, …)` → `Field(default=0, …)` 在 pydantic v2 下语义等价；这几个模型不进 openapi，
   故另用 `model_json_schema()` + `model_fields` 直比证明等价（带验伪锚）。
5. 全部 `# pyright: ignore` 都带理由，且理由是「这是真 bug，但修它属于别的卡的语义面」，不是掩盖。
6. 本卡**未提交前**两条 lefthook 门（`python-lint` / `python-typecheck`）红，作者主张是主干既有基线、本卡引入 0。

# 三 请按重要性排序回答

1. 有没有哪条 `# pyright: ignore` 实际在**掩盖真错误**，或加在错误的行/用了错误的规则名？
2. 海象改写有没有**任何**输入会与原式行为不同？（含异常、短路、可变状态、None 键）
3. `Field(0,…)`→`Field(default=0,…)` 有没有边界情况不等价？
4. `exam_service.py` 的 `if TYPE_CHECKING` 块与删掉的 `import logging`，会不会造成运行期变化或循环导入？
5. `review.py` / `system.py` 是别的车道刚改过的共享文件——本卡有没有哪一行其实动了语义？
6. 作者的判据里有没有**空判据**（探针看不见被测改动）或**假绿**（验伪锚两种情况给同样结果）？
7. 新增注释里有没有事实错误或失实的行号引用？

# 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给 `file:line` + 一句话结论 + 你的核对依据。
没有问题就明确说没有；不要为凑数编造。

# 五 边界

- `backend/app/services/**` 的残余 197 条类型错误**不在本卡范围**（属并行车道 U1-A）。
- `review.py:184 / :238 / :408 / :1543` 族的真 bug 修复**不在本卡范围**（已登记移交）。
- 仓库级 ruff-format 基线（462 文件）**不在本卡范围**。
- 只读；不要提出需要修改文件才能验证的方案。
