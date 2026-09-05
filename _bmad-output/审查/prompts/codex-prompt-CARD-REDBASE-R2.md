# Codex 对抗性审查 Round-1 — CARD-REDBASE-R2 [BATCH-2026-09-05-第十一批]

你是独立对抗审查者。LANE = 你的当前工作目录（车道 `card/z4-redbase`）。
审查面 = **`git diff 7283a8df a5e0ce79`**（Z4-B 单个 commit，5 个文件）。
`7283a8df` 是同车道前一张卡 Z4-A 的 commit，**不在本轮审查面内**。

## 本卡做了什么

把对外契约面上残留的、D16（2026-05-05）之前的裸 group_id 示例 `math54:离散数学`
改成现行四段格式。六处：

- `backend/app/models/metadata_models.py:52`（`CanvasMetadataResponse.group_id` 的 Field description）
- `backend/app/models/metadata_models.py:62 / :177 / :292`（三个 model 的 `json_schema_extra` example）
- `backend/app/api/v1/endpoints/metadata.py:125`（端点 docstring，进 OpenAPI path description）
- `backend/app/services/subject_resolver.py:48`（类 docstring 的 doctest 风格示例）

`backend/openapi.json` 经 `scripts/spec-tools/check-openapi-drift.py --write` 重生成（声称未手改）。

## 本卡的主张（请逐条证伪）

- **A 零逻辑改动**：`backend/app` 的全部新增行都是字符串字面量或 docstring，
  无 `if` / `return` / 赋值行变更。
- **B 快照只经 `--write`**：`backend/openapi.json` 未被手工编辑；`--snapshot` 返回 `DRIFT: none`。
- **C 六处源码只反映为四处快照变化是正确的**，因为 `SubjectInfo`（`:292`）不是任何端点的
  response_model（`components.schemas` 里没有该 schema），`subject_resolver.py:48` 是服务层
  docstring —— 两者本就不进 OpenAPI。
- **D 示例值的选择是对的**：卡文原文要求用 `vault:cs_61b:math54:线性代数`，本卡改用
  `vault:cs_61b:math54:离散数学`。理由是这六处的上下文（`canvas_path` 示例 ×3、
  `subject_resolver.py:46` 的 doctest 输入）全是「离散数学」，照卡文字面会让契约示例
  自相矛盾；卡文的实质约束（D16 四段 + vault 段中性、不写本机 `canvas_vault`）已满足。
- **E 全仓裸格式示例归零**（Z4-A 那条引述历史旧值的 docstring 陈述句除外）。

## 验证清单（每项 PASS / FAIL + 证据）

1. **A 是否成立。** 逐行核 `git diff 7283a8df a5e0ce79 -- backend/app`。有没有任何一行
   改变了运行时行为（包括：Field 的 description 是否被某处代码读取并参与判断、
   docstring 是否被 doctest 收集器实际执行、`json_schema_extra` 是否被校验逻辑消费）。

2. **B 是否成立。** 请判断 `backend/openapi.json` 的当前内容是否与
   `--write` 的确定性输出一致（自行重跑生成到临时路径后比对，不要写回仓库文件）。
   如果存在只能由手工编辑产生的差异，指出来。

3. **C 的解释是否属实。** 独立确认 `SubjectInfo` 确实不在 `components.schemas`，
   以及它是否真的没有出现在任何端点的 request/response 里（含嵌套引用）。
   如果它其实以别的方式暴露给消费方，本卡就漏改了契约面。

4. **D 的判断是谁对。** 这是本卡与卡文的明确分歧，请给出你的独立裁定：
   a) 保持示例内部一致（canvas 段跟随上下文）与逐字遵循卡文，哪个对消费方更好；
   b) 有没有第三种更好的选择（例如把整组示例统一换成另一个白板名）；
   c) 现在的示例里，`cs_61b` 这个 vault 段与同一个 example 里的其它字段有没有新的矛盾。

5. **E 是否成立 —— 这一项请扫得比本卡更宽。** 本卡只 grep 了 `math54:离散数学` 与
   `math54:线性代数` 两个字面量。请判断**全仓**（含 `frontend/`、`canvas-vault/`、
   `docs/`、`scripts/`、`.claude/`）还有没有其它 D16 之前形态的 group_id 示例或文档说明
   —— 即形如 `<subject>:<canvas>` 而前面没有 `vault:<vault_id>:` 的写法。列出你找到的每一处。

6. **消费方风险（本卡自认未证明，请你补上仓内部分）。** 仓内有没有任何代码在按裸格式
   解析 group_id —— 例如对 group_id 做 `split(":")` 后取 `[0]` 当 subject、取 `[1]` 当 canvas，
   或用固定的段数假设。若有，指出 `file:line` 并说明它在四段格式下会得到什么。
   注意：实际返回值自 D16 起就是四段，所以这类问题（若存在）是既有缺陷、不是本卡引入 —— 
   请分清并如实标注归属。

7. **门处置的证据是否成立。** 本卡绕过了 `python-lint` 与 `python-typecheck` 两个 hook，
   声称两者的红点都是存量：
   - `ruff format --check` rc=1：声称用 `--stdin-filename` 对比 Z4-A 基线，漂移 215 行 = 215 行，
     唯一差异就是本卡改的那个字符串本身；
   - `pyright` rc=1：声称基线 5 errors / 本卡 5 errors、双向差集为空。
   请独立复算这两条。

## 纪律

- **只读**。不要写回 `backend/openapi.json` 或任何仓库文件；需要生成物就写到临时路径。
  复现用 `LANE/backend/.venv/bin/python` 与
  `PYTHONDONTWRITEBYTECODE=1 LANE/backend/.venv/bin/pytest -q -p no:cacheprovider <文件>`。
  禁连 Neo4j 7691 / 7687。
- 每条结论给 `file:line` 或命令输出原文。新发现按 BLOCKER / HIGH / MEDIUM / LOW 分级，
  并标注「本卡引入」还是「既有」。
- 判断不出来就写「未找到」，不要硬造。
- 末行必须给：`BLOCKER/HIGH 清零: 是|否`。
