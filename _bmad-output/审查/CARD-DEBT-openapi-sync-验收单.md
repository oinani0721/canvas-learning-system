# CARD-DEBT-openapi-sync 验收单 — [BATCH-2026-09-01-第八批]

> 车道: card-w4-micro (W4 第 ③ 卡) · 分支 card/w4-micro · 首 commit 2fb779b3 (2026-09-01 17:27:11 +0800) + Codex round-1 整改 commit
> 完整卡文: `feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第八批-goals/W4-3.md`

## 〇、一句话

OpenAPI 漂移门此前是假门(CI 查一个全历史从不存在的仓库根文件、失败被 `|| true` 吞掉、
lefthook spec-sync 死了 4 个月), 本卡把它们修活: 门真的能翻红、快照重生成(同时登记
5 个月漂移)、三个 CI/CD 处置按默认落 commit 待用户逐项批。

## 一、改动面(7 文件, 生产代码 backend/app/** 零改动)

| 文件 | 动作 | 说明 |
|---|---|---|
| `scripts/spec-tools/check-openapi-drift.py` | 新增 | 唯一合法快照写入口: --snapshot 只读比对 / --write 重生成; stdlib-only; import 期 socket 禁闭自证不起 lifespan |
| `backend/openapi.json` | 重生成 | 只经 --write; 163→192 paths, 299→353 schemas; x-generated-at=2026-09-01T09:21:35Z(UTC/沪时均 ≥2026-09-01) |
| `.github/workflows/api-spec-sync.yml` | 修改 | 路径全改 backend/openapi.json; 漂移=job 红; 删 update-spec 假门 job; Dredd if:false 停用; breaking 基线改 git show origin/<base>:backend/openapi.json |
| `lefthook.yml` | 修改 | spec-sync 段重写: backend/.venv/bin/python + 失败 exit 1 出声 + git add backend/openapi.json |
| `backend/tests/contract/test_openapi_snapshot_drift.py` | 新增 | 进程内门 19 测试: 生产形态(真实 app.openapi() vs committed 快照) + 合成形态(归一化五规则承重) |
| `backend/scripts/openapi_drift_negative_control.py` | 新增 | 负控: 3 红变异(删 path/改 enum/删 required, 逐个点名) + 1 放行对照(只改时间戳) + 正本 sha 前后一致门 |
| `_bmad-output/审查/prompts/codex-prompt-CARD-DEBT-openapi-sync.md` | 新增 | Codex 冻结审查提示词 |

禁改核对(裁判 9): `git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD -- backend/app/ .github/workflows/test.yml .github/workflows/plugin-ci.yml .github/workflows/readme-claims.yml .github/workflows/release-evidence.yml backend/tests/contract/test_openapi_contract.py .gitignore` → **0 行**; 对照组自证查询有效(scripts/send_bark.py、backend/tests/support/lifespan.py 均命中, 防假空)。

## 4-A、裁判输出(全部 LANE 实跑, 2026-09-01)

**裁判 1** `cd backend && .venv/bin/python ../scripts/spec-tools/check-openapi-drift.py --snapshot openapi.json` → exit 0
```
DRIFT: none (paths=192 schemas=353)
```

**裁判 2** `.venv/bin/python scripts/openapi_drift_negative_control.py` → exit 0
```
  PASS  前提: 正本无漂移 (DRIFT: none (paths=192 schemas=353))
  PASS  M1 删 path: OK (删除 path /api/v1/system/extraction-records/{record_id}/annotation)
  PASS  M2 改 enum 取值: OK (schema ActionTrend 的 enum 首值 'improving' → __MUTANT_ENUM_VALUE__)
  PASS  M3 删 required 字段: OK (schema AIConfigResponse 的 required 删除字段 'ai_api_key_set')
  PASS  M4 只改 x-generated-at: OK (只改 info.x-generated-at(易变键))
  PASS  正本 openapi.json 全程未变 (sha256 5360e9d6d6b24ef2…)
NEGATIVE-CONTROL: PASS (3 mutants → exit 1 with named diff; timestamp-only → exit 0)
```

**裁判 3** `caffeinate -i .venv/bin/pytest tests/contract/test_openapi_snapshot_drift.py -q -p no:cacheprovider` → exit 0(在 W4② 的 socket 门下)
```
NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)
19 passed, 10 warnings in 0.84s
```

**裁判 4** 根路径引用 grep → **0 行**; `grep -c "update-spec:"` → **0**。

**裁判 5** 快照内容:
```
review-suggestions 200 → {"$ref": "#/components/schemas/ReviewSuggestionsResponse"}
x-generated-at → 2026-09-01T09:21:35.844092+00:00
retrieval_status 计数 → 10 (≥4)
```

**裁判 6** hook 活性(本卡 commit 后执行, 输出回填于下方 §六)。

**裁判 7** `python3 -c "import yaml; yaml.safe_load(...)"` → `YAML OK` 无异常。

**裁判 8** 车道本地态声明: **本卡生成的 backend/openapi.json 是车道本地态**——V5 G2-5 /
W5 G6-2 / W8 G4-4 都会再改 app.openapi(), 且 lefthook 无 pre-merge-commit hook, 故本卡
commit 是全批最后一个合入; 批次收官时主 session 必须在最终主干执行
`backend/.venv/bin/python scripts/spec-tools/check-openapi-drift.py --write backend/openapi.json`
并单独 governance commit, 随后 `--snapshot backend/openapi.json` 必须打印 `DRIFT: none` 才算收官。

### 5 个月漂移登记(旧快照 48f4b82b 2026-03-31 → 本卡重生成 2026-09-01)

- **paths +43 / -14**(净 +29), **schemas +78 / -24**(净 +54);
- 新增 path(整类): `/api/v1/exam/{grade,quick,targeting-material}`、errors 图 6 条
  (accept/dismiss/dispute-candidate, by-node, by-type, list, rebuild-graphiti)、
  `/api/v1/wikilink/*` 4 条、`/api/v1/vault/{current,list,switch}`、
  `/api/v1/review/overview{,/page,/refresh}`、`/api/v1/index/*` 3 条、
  `/api/v1/system/{config-check,health/detailed,setup-wizard,startup-check}`、
  `/api/v1/traces/{request_id}`、`/api/v1/tips/*` 3 条、`/api/v1/chat/*` 3 条、
  `/api/v1/boards/manifest`、`/api/v1/memory/archive/session`、
  `/api/v1/sync/relationships/*` 2 条、`/mcp/tools/*` 只读 5 条;
- 移除 path: `/api/v1/review/schedule` + 13 个 `/mcp/tools/*` 隔离桩(MCP 改版后 410 化,
  对应 "[P0-2] 6 read-only + 14 quarantined");
- 信封/四态: review-suggestions 200 从 `array of ReviewSuggestionResponse`(G4-3 前形态)
  → `$ref ReviewSuggestionsResponse`; `retrieval_status` 0 → 10 处。

## 4-B、用户可见变化

无变化。本卡不触碰任何产品功能、界面、通知或数据，只影响开发与持续集成流程，以及一份随代码更新的接口说明文档。

## 二、「待你裁决」(均为建议默认、待裁决——已按默认在车道落 commit、未 push)

1. **删除 update-spec 自动提交 job** — 它写仓库根路径(文件全历史不存在)、`|| true` 吞掉
   commit 与 push 失败、job 恒绿却从未推上任何东西。删除后快照保鲜靠三层:
   lefthook(改 API 即重生成并 stage, 失败 exit 1 阻断 commit) + CI 漂移红门 + 批次收官
   主干重生成。
2. **Dredd job 停用(`if: false`)** — GitHub 24/24 runs failure(2026-04-17→06-01), 最新
   run 里唯一 failure job 就是它, 失败原因因日志 410 Gone 不可再证; schemathesis
   in-process(`test_openapi_contract.py`, from_asgi)继续承担 schema 一致性校验。
   已登记独立候选卡(复活/退役由该卡裁决, 届时删 `if: false` 即可)。
3. **lefthook spec-sync 出声化+改口径** — 失败从静默改为 exit 1 阻断 commit; 解析器从裸
   `python` 改 `backend/.venv/bin/python`; 直接写并 stage `backend/openapi.json`。代价:
   触及 backend/app/{api,models,schemas} 的 commit 多约 20s 导入耗时, 且快照因时间戳
   恒变必然出现在这类 commit 的 diff 里(内容漂移由比对侧归一化吸收, 不会误红)。

## 三、证据缺口与已知边界(如实声明)

1. **workflow 修正未经 GitHub 实跑验证** — CI 翻红/翻绿只有 push 后可见; 本卡验证止于
   本地 YAML 解析(actionlint 本机未装) + 语义逐 job 复核 + 等价脚本本地实跑。首推后若红,
   修正属后续微调。
2. **跨 Python 版本与跨依赖版本导出未实测** — 本机 3.14 三次导出连 key 序都逐字节相同;
   CI 用 3.11。且 requirements.txt 对 fastapi/pydantic/fastapi-mcp 等只锁下限, CI 每次
   fresh resolve 可能取到与本机不同的版本 → schema 可能不同 → CI 漂移门红——那是门在
   工作, 但首跑可能红得"意外"(Codex round-1 HIGH-5)。requirements.txt 本批禁动(手册
   §四.2 #5), 版本锁定移交独立卡。
3. **schemathesis 契约测试未接入 CI 白名单** — test_openapi_contract.py 只在本机跑
   (且 importorskip), test.yml 白名单没列它; Dredd 停用后 HTTP 回放面确实丢失、
   schema 一致性主体只有本地保障(Codex round-1 HIGH-6, 已记入 Dredd 独立候选卡)。
4. **Dredd 失败根因不可考** — 日志 410, 只能证明"它一直红", 不能证明"修不好"; 处置取停用。
5. **本卡快照为车道本地态** — 见裁判 8, 由主 session 收官重生成兜底。
6. **socket 禁闭的观测副作用** — 禁闭拦下 LiteLLM 拉远程 model cost map(本机走代理
   127.0.0.1:1082), 它自带本地 fallback、不进 schema; 已实测带/不带禁闭导出逐字节相同
   (sha 前 16 位同为 919d6b41fb870217)。
7. **lefthook glob 引擎边界(本机 2.1.6 实测)** — 数组形态完全不工作、`**` 需跨至少
   一级、花括号备选项必须是真实存在的路径; 因此 spec-sync 拆三条命令, 触发面以探针
   逐条验证(mcp/server.py、config.py、api 端点文件各命中对应命令)。CI 的 ubuntu
   lefthook 版本若不同, 行为可能不同——但 lefthook 只影响本地 hook, 不影响 CI 门。

## 四、每道门「证明什么 / 不证明什么」

- 裁判1: 证明 committed 快照与 app.openapi() 归一化后逐键逐值相等; 不证明实现符合
  spec(schemathesis 职责)、不证明 CI 会绿。
- 裁判2: 证明门对删 path/改 enum/删 required 翻红并**点名对象**、对时间戳噪音不翻红、
  负控全程未动正本; 不穷举差异形态(anyOf/parameters 顺序等未覆盖)、不证明 CI 行为。
- 裁判3: 证明门函数在进程内可用、快照同步、且与 W4② 硬门复合(零连接); 不验证跨版本确定性。
- 裁判4: 证明无根路径引用残留、update-spec 已删; 不证明 YAML 在 GitHub 的运行时语义。
- 裁判5: 证明信封/四态/时间戳落进快照; 时间戳按 UTC 记, 本卡实测已 ≥2026-09-01 双口径成立。
- 裁判6: 证明 hook 会重生成并 stage 快照、还原后树干净无新 commit; 不证明真实 commit 全程。
- 裁判7: 仅语法可解析, 不证明 Actions 语义。
- 裁判8: 合并序声明, 见上。

## 五、本卡未证明什么(必填)

1. 未证明 push 后 GitHub 上 workflow 变绿(缺口三.1);
2. 未证明 Python 3.11 与 3.14 导出一致(缺口三.2);
3. 未证明 Dredd 的 HTTP 回放覆盖面被 schemathesis 完全等价替代——丢的是「真实 HTTP 栈上
   按 example 回放 + dredd-hooks 自定义流转」这一层, schema 一致性主体仍在;
4. 未证明本卡快照在全部 14 卡合入后仍无漂移(设计上必然漂移, 由裁判 8 的收官重生成兜底);
5. 未证明 `--no-verify` 绕过 lefthook 的场景有兜底(CI 红门是唯一兜底, 且依赖 push);
6. 未证明 openapi.json 作为 committed 产物在长期多人并行下的 merge conflict 负担可控
   (本批靠合并序协议化解, 日常并行的冲突解法=`git checkout --theirs` 后 `--write` 重生成)。

## 六、Codex 审查与裁判 6 回填

**裁判 6**(commit 2fb779b3 后, 对已提交态执行):
```
$ printf '\n' >> backend/app/api/v1/endpoints/health.py && git add <同文件>
$ lefthook run pre-commit --command spec-sync
[Spec Sync] API changes detected, regenerating backend/openapi.json (via backend/.venv/bin/python)...
WROTE: backend/openapi.json (paths=192 schemas=353, x-generated-at=2026-09-01T09:28:27.214028+00:00)
[Spec Sync] + backend/openapi.json staged          ← hook 重生成并 stage, 6.29s, exit 0
$ 还原(unstage + 内容还原)
before=5360e9d6d6b24ef21fce52945e19269eba0f678449be0252f8ea5518b3702e50
after =5360e9d6d6b24ef21fce52945e19269eba0f678449be0252f8ea5518b3702e50   ← 逐字节一致
git status --short → (空) ; 无新 commit
```
环境备注: 本机 lefthook 2.1.6 的 `run` 子命令旗标是单数 `--command`(卡文字面
`--commands` 报 "flag provided but not defined", 行为等价); guard-hook 对
`git checkout --`/`git restore` 会以 "No stderr output" 异常拦截, 还原改用
备份 cp + `git show HEAD:` 重定向(效果等同且逐字节可证)。

**Codex 轮次与终裁**:

- **Round 1**(gpt-5.6-sol ultra, 2026-09-01): 终裁 **FAIL — 4 BLOCKER + 2 HIGH**。
  逐条溯源验证后**全部成立**(本地可复现: enum 内嵌 required 反序 compare()==clean、
  clean-env import app.config 抛 pydantic ValidationError、c44c48e8 只改 mcp/server.py
  却改契约面、`git cat-file -e 9af18b27:backend/openapi.json` exit 0 证明基线真实存在);
  本地归一化守卫前提亦验证: 真实快照 281/281 个 required 数组的宿主 dict 均含
  properties/type 键, 守卫零成本。
- **Round 1 整改**(本 commit):
  - B1 吞漂移: required 排序加 Schema Object 宿主守卫(含 properties/type 才排序);
    新增 2 个反例测试(enum 内嵌 required 反序必须报漂移、无语境裸对象 required
    顺序变化必须报漂移), 测试数 19→21 全绿; 守卫后 --write 重生成, 快照 diff
    仅时间戳 1 行(内容零变化实证)。
  - B2 clean CI 必炸: export 与 drift gate 两个步骤按 test.yml:119-121 同配方显式
    注入 DEBUG/CORS_ORIGINS/INTERNAL_API_KEY。
  - B3 触发面缺口: workflow paths 与 lefthook 都补 main.py/config.py/mcp/**;
    lefthook 因 glob 引擎边界拆三条命令(spec-sync/spec-sync-flat/spec-sync-root),
    三条探针各命中(mcp/server.py→flat, config.py→root, api 端点→主命令);
    push 触发也纳入 backend/openapi.json 自身。
  - B4 breaking 基线 fail-open: 删 `{}` 降级(git show 失败=job 红); oasdiff 输出
    解析失败=步骤红(不再把工具错误伪装成零变化); summary 对 skipped/failure 的
    breaking 检测不再显示绿色 None。
  - H6 措辞: 删除「覆盖面并未丢失」的不实声明, 如实写「HTTP 回放面丢失 +
    schemathesis 未接入 CI 白名单」(验收单 §三.3 同步)。
  - MEDIUM(DETAIL_LINE_CAP 截断可掩盖点名行)与 LOW(验收单 pathspec 缩写/时间
    模糊/文件计数)一并修正; MEDIUM 另一缓解: 差异头部恒打印 paths/schemas 增删
    计数, 截断只作用于逐行明细。
- **Round 2**: (待回填)
