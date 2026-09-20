> 批次: BATCH-2026-09-18-第十五批 · 车道 P9 · 卡 CARD-G4-13 round-2 [prompt-2]
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G4-13-r2.md)" > _bmad-output/审查/codex-review-CARD-G4-13-r2.md 2> _bmad-output/审查/codex-review-CARD-G4-13-r2.stderr </dev/null`
> 审查绑定: `2e0642aa`（修复 commit；`git --no-pager diff --stat --no-color 2e0642aa HEAD -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py` = 空；PREV = `18f31c44`）
> 会话头自证（`.stderr` 第 2 / 5 / 9 行原文抄录；stderr 本身不入库）:
> `OpenAI Codex v0.153.3`（:2） / `model: glm-5.3`（:5） / `reasoning effort: max`（:9）

# CARD-G4-13 · round-2 独立复核报告（绑 `2e0642aa`）

## ⓿ 绑定与读取面核验（独立重算，非采信自证）

| 项 | 复核结果 |
|---|---|
| HEAD | `2e0642aae20668e6e32399e6e735c8d841744560` ✅ |
| `2e0642aa^` | `18f31c445006d31b6eec32cc9226cbd3f0f92e7a` ✅（父提交即 PREV，diff 面纯净） |
| 两代码文件 `2e0642aa..HEAD` diff | **空** ✅（自证成立） |
| commit 变更面 | 恰两代码文件 + `_bmad-output` 证据 ✅；⚠️ 中性观察：commit 里另有 prompt 未列的 `gate-r2-green-20260919T235605.txt`（57 行），不影响结论 |
| 内嵌 diff | 实测 264 行，与 prompt 一致 ✅ |
| 工作树 | tracked 0 脏；3 个 untracked 均为本轮审查物料（prompt/jev/评审输出），无代码漂移 ✅ |

## 总裁定

**无 BLOCKER / 无新 HIGH。H-1 = PASS（按 r1 定义闭合）· H-2 = PASS。** 修复未引入新问题；但 H-1 的「同类残余逃逸面」仍有两族（预存、非本轮引入）→ 新增 **2 MEDIUM + 3 LOW**，建议登记进 UAT 债务表，不阻断本轮收口。既有 M-1/M-2/M-3、L-1~L-6 **无一条够 HIGH 升级**（逐条理由见 §④ 末）。

---

## ① HIGH 复核结论

### H-1（fail-closed 边界）→ **PASS**

r1 点名的三类输入全部闭合，且比 r1 要求多修了一类：

- `yaml.YAMLError` → `tool.py:290-293` try/except → `(False, 解析失败…)` ✅
- 顶层非映射 → `:294-295` `isinstance(m, dict)` ✅
- 已登记文件缺失 → `:302-303` exists 前置 ✅
- 条目 sha 非 str → `:304-306`（r1 未点名，bonus）✅

runner 侧证据链成立：调用点 `run_vault…:490` / `run_memory…:359` 均在任何网络之前（memory 明确先于 `check_backend_alive():365`），先红档案 `negctl-r2-h1-red-*.txt` 的 3 failed **精确等于** 3 个新增测试项（`fail_closed` + `parse_error_as_rc2[vault/memory]`），后绿 15 passed。门⑧断言的异常路径与旧代码机制逐条对得上。

### H-2（门⑤假绿）→ **PASS**

修法四要素全部核实为真，不是文案自证：

1. `_import_tool():93-100` 先注册 `sys.modules["gold_set_manifest_tool"]`，`_import_runner` 后 exec 时 runner 的 `from … import`（`run_vault:67` / `run_memory:61`）**复用同实例**；
2. identity 断言 `test:346-348` —— 顺序回归/双实例**第一条就红**（早于任何 rc 断言）；
3. 真金集在仓内 + 仅篡改 manifest 副本 sha（`test:299-310`，`assert hits==1` 防路径拼错）→ 必经 `tool.py:307-309` 的真 sha 比较；
4. 验伪锚 `test:359-362`（sha 签名必在 + 「在仓外」必不在）+ 干净对照 `:364-368`（非恒真）。

旧路径探针档案的 old/new 布尔**完全反向**（old：在仓外=True/sha=False；new：在仓外=False/sha=True），与 r1 H-2 机制复现吻合。死补丁的原两种失效模式（顺序反、patch 错实例）分别被 identity 与签名断言拦住；若 runner 未来改走 subprocess/自拷贝函数 → identity 断言直接 AttributeError（红，不假绿）。

---

## ② ③ 逐问回答

- **A1（还有别的逃逸面吗）**：**有，两族**（见 M-R2a/M-R2b）：OSError/UnicodeDecodeError 族（manifest 或金集不可读/是目录/非 UTF-8）与 `files:` 非可迭代标量。`rel_to_repo:99-102` 无新破口（`resolve()` 的 ValueError——含 NUL 路径——恰被 `except ValueError` 捕获）；`entry.get("query_count")` 无格式化风险。
- **A2（文案兼容）**：**PASS**。全仓消费者仅两 runner，detail 只被内插进 `「不符 ({detail})」`（`run_vault:492` / `run_memory:361`）；grep 无任何按旧文案字面断言的测试/脚本（`validate_release_manifest.py:139` 的「manifest 不存在」是无关文件的巧合同词）。
- **A3（「口径对齐 verify_all」）**：**部分属实**（见 L-R2a）。环境错方向对齐且**更严**；但 sha 不符在 `verify_all:237-239` 是 rc=1、经本函数+runner 是 rc=2（bool 压缩，靠文案区分）；且 `verify_all:223-224/:237` 自身对顶层 list / 坏条目会崩——它不是完备的对齐基准。
- **B1**：见 H-2 分析——identity 拦「补丁打错实例」，sha 签名拦「未到比较」，负断言拦 r1 早退路径；即使 identity 被删，补丁失效 → 真 manifest 放行 → runner 落到无签名的环境失败/rc=0，签名/rc 断言仍红。未发现「改坏仍绿」的门未覆盖路径。
- **B2**：干净对照（直接函数调用，`:364-368`）足以证明拒绝支路非恒真；「在仓外」负断言只作用于**本测试输出域**，不触碰合法早退分支本身，误伤风险仅是未来 runner 输出恰含该子串（偏红方向，L-R2c）。
- **B3**：runner 两参数**都真跑到了校验段**：vault `:485-494` 先于 `run_tiers:503`；memory `:358-363` 先于 alive `:365`（代码 + 文件内注释双重钉住）✅。但⑧四 case 串行在一个函数里，先红档案只实证了 case①（① 抛 ScannerError 即遮蔽 ②③④）→ L-R2b。
- **B4**：**PASS（退化方向=红，不是绿）**。文件挪走 → `_tampered_manifest_copy` 的 `hits==1` 红；manifest 挪走 → `_load(MANIFEST)` 直接 error；runner 挪走 → import spec 断言红；无 skip/恒真退化路径。

---

## ③ 分级清单（按 ④ 格式）

### MEDIUM（新增，登记不改；均**预存**、非本轮引入）

**M-R2a · H-1 同族残余：OSError/UnicodeDecodeError 未纳入 fail-closed，runner 仍会 exit 1**
- 落点：`backend/scripts/gold_set_manifest_tool.py:288-293`（源头 `load_yaml:79-80` 用 `read_text`）、`:302-307`
- 复现思路：**负控输入** = `MANIFEST_PATH` 指向目录（`exists()` 为 True，`read_text` → `IsADirectoryError`）、chmod 000 的 manifest（`PermissionError`）、或非 UTF-8 字节损坏（`UnicodeDecodeError`，不是 `yaml.YAMLError`）；同类：已登记金集不可读/为目录 → `sha256_of:307` 逃逸。均绕过 `except yaml.YAMLError`。
- 不升级 HIGH 理由：四个常见损坏形态（冲突标记/截断/缺文件/坏 sha）已闭合；余下触发需路径配置错或权限异常，且 traceback 立即可见。

**M-R2b · H-1 同族残余：`files:` 为非可迭代标量 → TypeError 逃逸**
- 落点：`backend/scripts/gold_set_manifest_tool.py:299`
- 复现思路：**负控输入** = manifest 写 `files: 5`（或 `4.5`/`true`）——truthy 标量绕过 `or []`，`for entry in 5` → `TypeError`；字符串/dict 形态则安全落到「未登记」。（`verify_all:223` 同病，属同一登记项。）

### LOW

**L-R2a · docstring「口径对齐 verify_all」过claim**
- 落点：`gold_set_manifest_tool.py:285`（声明）vs `:217-239`（实际）
- 复现思路：**对照输入** = 同一份 sha-不符 manifest：`verify_all` → rc=1（内容不符），本函数+runner → rc=2（bool 压缩，仅文案区分）；顶层 list manifest → `verify_all:223-224` 自身 AttributeError（CLI `verify` 残留同类崩溃，非 runner 面）。方向是本函数**更稳**，纯文档精度 + 预存 CLI 残留，不影响正确性。

**L-R2b · ⑧ 先红证据被 case① 遮蔽 + 模块 docstring 计数不一致**
- 落点：`test_gold_set_manifest_g413.py:456-493`（四 case 串行）、`:18-20`（写「三类」，实际四 case）
- 复现思路：**门未覆盖的路径** = 修前运行只看到①的 ScannerError，②③④的「各自红」由旧代码机制推断（`m.get`→AttributeError / `sha256_of`→FileNotFoundError / `None[:12]`→TypeError），无独立红证据。拆成四个测试或 parametrize 即可补齐；不影响当前绿的效力。

**L-R2c · 「在仓外」负断言的未来误红边界（风格）**
- 落点：`test_gold_set_manifest_g413.py:362`
- 复现思路：**门未覆盖的路径** = 将来 runner 合法输出中任何位置出现「在仓外」子串都会误伤本门；当前正确，偏红方向，不掩盖假绿。

### 既有 M/L 升级审查

**全部维持原级，无 HIGH**：M-1（锚丢失归错条目，需用户在 Obsidian 源码态误删锚才触发）、M-2（注释抹除，可逆且有 sha 可见性）、M-3（顺序钉法环境依赖——r2 门⑤仍实质存在：未强制 `check_backend_alive→False` 对照，backend 恰好 up 时顺序回归不红；但有代码注释 + 离线 UAT 佐证 + 签名断言兜底）、L-1~L-6 均无正确性升级理由。

---

## ④ 证据一致性与局限

**一致** ✅：negctl-h2 old/new 布尔反向；h1-red=3 failed（与新增测试项一一对应）；gate=15 passed；named=37；regression=1928/6/1 红 0；unit=32 failed；jev JSON 与分诊表数字吻合。

**局限（不采信为已证）**：① 本轮只读沙箱，我**未执行** pytest/python/sha 复算——执行性结论来自存档证据交叉 + 静态代码核对；② unit 32 红与 close 集 nodeid 等值（rc=0）是主 session 自证，close 清单不在读取面，未独立重算；③ ruff/format 双绿无存档在读取面；④ H-2 探针 scratchpad 脚本本体在 `/var/folders`（不入库），仅有输出档可审。

**处置建议**：H-1/H-2 可判闭合；M-R2a/M-R2b/L-R2a~c 登记入 UAT 债务表（与 M-1~3、L-1~6 同池），不要求本轮返工。
