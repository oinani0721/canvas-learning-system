# CARD-G2-6 (BATCH-2026-09-05-第十二批) + CARD-RV-G2-6 (BATCH-2026-09-07-第十三批)
#   — vault 部署清单 + 只读校验器的裁判
#
# 被测物: scripts/vault-install-manifest.json + scripts/verify_vault_install.py
#         + scripts/install-vault.sh 的自检块 (:112-125)
# 真相源: install-vault.sh MANIFEST 区 (:61-69) 与其隐含部署语义 (:74-109);
#         插件命令 id 的真相源是 frontend/obsidian-plugin/src/main.ts (只读, 不构建)。
#
# ⚠️ 头注维护约定 (UAT-CARD-G2-6 「未证明」#19 的债, 由 CARD-RV-G2-6 还上):
#   这份清单写于 round-1, 三轮整改期间钉死点从 5 条扩到下面这些却一直没同步 ——
#   头注与实现不一致会误导后来者。**增删钉死点必须同批改这里。**
#
# 钉死点 (G2-6 三轮累积):
#   1. **集合等价**: manifest 里 action ∈ {copy, skeleton} 的 path 集合, 与 install-vault.sh
#      :63-67 五个 shell 数组按各自前缀展开后的并集**逐项相等** (27 项)。这是本门的主判据。
#      验伪锚: 先断言正则确实解析出 5 个数组 / 27 个元素, 否则「空集 == 空集」会假绿;
#      另有全文扫描门, 防 :63-67 之外新增第 6 个数组对主判据不可见。
#   2. **schema**: version int / source 非空 / items 非空列表 / 必填键 / action 四枚举 /
#      kind 四枚举 / path 相对·无 `..`·无 NUL·可编码 UTF-8·规范化后无重复;
#      extra_scan 的 dir 与 path **共用同一个校验函数** (同一条约束不得只在一半字段生效);
#      match 单层名字不得含 `/`。任何 schema 问题 → 用法错档, 不与内容差异混淆。
#   3. **六类 diff 各自独立承重**: missing / extra / content-drift / intentionally-excluded /
#      unreadable / hotkey-orphan, 每类一个反例, 一次只打一类, 断言「该类精确命中该 path」
#      且「其余各类为空」—— 只断言 rc != 0 是粗判据, 会被任意一类差异喂饱。
#   4. **报告落点的三种别名**: 大小写目录别名 (macOS 默认大小写不敏感, 按 (st_dev,st_ino)
#      身份判) / 两层软链目标 (禁写根递归展开) / 硬链接; 外加「安全性扫描没跑完就拒绝落盘」。
#   5. **写入资源管理**: O_EXCL 失败时只清理本次真正创建的临时文件 (删别人的文件 = 数据丢失);
#      os.write 短写必须循环写满才换目录项 (否则发布截断报告)。
#   6. **unreadable 计入阻断**: 顶层普通文件与目录内叶子两条路径都要登记 ——
#      「我看不见」不等于「一致」, 两侧都读不动而报 0 是假绿。
#   7. **零写**: 对 target 跑一次校验器, 前后全树 (文件 sha + 目录条目) 清单逐字相同。
#      校验器有任何写目标 vault 的路径 = 阻断级缺陷。AST 门另钉「源码里没有写调用」。
#   8. **glob 口径一致**: `[` 在 _has_glob 与 _pattern_to_regex 两处都是字面量;
#      清单里真放一条含方括号的 exclude 声明, 端到端验分类与负例。
#
# 钉死点 (CARD-RV-G2-6 新增):
#   9. **退出码四档**: 0 ok / 1 只缺 (missing) / 2 mismatch (extra 未放行·content-drift·
#      unreadable·hotkey-orphan, 与 missing 并存时也取 2) / 3 用法错。数字写死 ——
#      调用方 (deploy-vault.sh, CARD-G2-7b) 靠它区分「缺东西」与「多东西」。
#      `test_missing_is_detected_alone` 仍期望 **1**, 它是「missing 语义没被 mismatch
#      吞掉」的唯一守门人; 禁止把任何一条 rc 断言弱化成 `!= 0`。
#  10. **extra_allow**: manifest 顶层白名单, 与 item.path 同口径 (相对 / 无 `..` / 可编码 /
#      无重复 / 支持 *? glob); 与 declared 或 exclude 模式**重叠即拒绝加载**;
#      命中的项进 allowed-extra 段, 只报告不计退出码。仓内清单初值必须是 []。
#  11. **hotkeys ↔ 命令 id 交叉核 (两层)**:
#      校验器层 — vault 的 .obsidian/hotkeys.json 里 `canvas-learning-system:` 前缀的键,
#        必须在同一 vault 的 .obsidian/plugins/canvas-learning-system/main.js 里找到
#        对应命令 id 字面量; 找不到 = hotkey-orphan (计 mismatch); main.js 缺 →
#        报告明写 not evaluated, **不计退出码也不静默**; hotkeys.json 非法 JSON → unreadable。
#      测试层 — main.ts 恰 10 个命令 id (数字写死, 防正则退化成空集), 且树内
#        canvas-vault/.obsidian/hotkeys.json 的 CLS 前缀 id ⊂ 该集合 (另断言非空,
#        否则 `∅ ⊆ 任何集合` 恒真)。
#  12. **install-vault.sh:117 的 skills 判据**: 数「含 SKILL.md 的一级子目录」, 不数目录条目
#      (树内 11 个目录只有 9 个含 SKILL.md, 旧 `ls | wc -l` 对半成品 skill 失明)。
#      判据只看 check 的 eval 体, 不看标签 —— 标签里的 "skills " 自带子串 "ls "。
#
# 本门证明什么: manifest 与脚本数组等价; 校验器的六种分类各自可被单独触发且退出码分档正确;
#   校验器不写目标树; 报告落点对三类别名与扫描失败都拒绝; extra_allow 的放行与重叠拒绝;
#   hotkeys 绑定与命令 id 的一致性 (在 main.js 存在时)。
# 本门不证明什么: 不证明 install-vault.sh 真跑起来会产出符合 manifest 的 vault (禁真跑脚本,
#   属 CARD-G2-7 五动作 CLI 的范围); 不证明 live vault 的 extra 项应否进 extra_allow (归 U3-B);
#   不证明构建产物 main.js 与源码 main.ts 的命令集一致 (只读源, 不 build);
#   不证明字面量法对「非命令 id 的同形字符串」没有假放行;
#   合成 fixture 的「有扩展名 = 文件」启发式只服务于本文件的目录/文件搭建, 不是生产语义
#   (该启发式的直接后果: 合成 vault 里没有 main.js, hotkeys 一路走 not evaluated 分支)。
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
VERIFIER = SCRIPTS_DIR / "verify_vault_install.py"
MANIFEST = SCRIPTS_DIR / "vault-install-manifest.json"
INSTALL_SH = SCRIPTS_DIR / "install-vault.sh"

# install-vault.sh 五数组各自的 vault 内前缀 (数组元素是裸名, 部署时拼在这些前缀下)
ARRAY_PREFIX = {
    "SKELETON_DIRS": "",
    "CLAUDE_ITEMS": ".claude/",
    "OBSIDIAN_FILES": ".obsidian/",
    "OBSIDIAN_PLUGINS": ".obsidian/plugins/",
    "ROOT_FILES": "",
}
MANIFEST_BLOCK = (71, 75)  # MANIFEST 数组区间 (1-indexed, 含两端)
# ⚠️ CARD-G2-7a 把区间从 (63,67) 下移到 (71,75): 新增 --harness-tree / --backend-url
#    参数与用法注释、E-4 缺省源块(替换原 .env 解析块, 少一行)加在数组之前。这个常量是**手写的**, 不会自己跟着脚本走 ——
#    区间写错时 _parse_install_arrays 会解析到别的行、甚至解析到空集,
#    所以 test_install_arrays_parse_as_expected 那条验伪锚 (断言恰好解析出 5 个数组
#    且元素数与预期相符) 是这个常量唯一的守门人 —— 改脚本行数时必须让它红一次。


def _load_verifier():
    """加载仓根 scripts/verify_vault_install.py。

    照 backend/tests/contract/test_openapi_snapshot_drift.py:39-51 的形态, 另加
    sys.modules 注册 —— 协议 §3: Python 3.14 的 @dataclass 自省要取
    sys.modules[cls.__module__].__dict__, 不先注册则 exec_module 期 KeyError。
    """
    name = "_verify_vault_install"
    spec = importlib.util.spec_from_file_location(name, VERIFIER)
    if spec is None or spec.loader is None:  # pragma: no cover — 路径错时立即失败
        raise RuntimeError(f"无法加载 {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    previous_dwb = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # 不往仓根 scripts/ 落 __pycache__
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:  # pragma: no cover — 加载失败不留半成品模块
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous_dwb
    return module


vv = _load_verifier()


# ── 集合等价 (钉死点 1) ────────────────────────────────────────────────


def _parse_install_arrays() -> dict[str, list[str]]:
    """正则解析 install-vault.sh:63-67 的五个 shell 数组。"""
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    lo, hi = MANIFEST_BLOCK
    block = lines[lo - 1 : hi]
    pattern = re.compile(r"^(?P<name>[A-Z_]+)=\((?P<body>[^)]*)\)\s*$")
    parsed: dict[str, list[str]] = {}
    for line in block:
        m = pattern.match(line)
        if m:
            parsed[m.group("name")] = m.group("body").split()
    return parsed


def test_install_arrays_parse_as_expected():
    """验伪锚: 正则真的解析到 5 个数组 / 27 个元素。

    没有这一条, 解析失败时 test_manifest_matches_install_arrays 会退化成
    「空集 == 空集」的假绿。
    """
    arrays = _parse_install_arrays()
    assert set(arrays) == set(ARRAY_PREFIX), f"解析到的数组名与预期不符: {sorted(arrays)}"
    counts = {k: len(v) for k, v in arrays.items()}
    # CARD-G2-7a 后的值（逐条依据见 evidence-g27a/manifest-ruling.md）:
    #   SKELETON_DIRS 6→8   +wiki/concepts +wiki/canvases（后端 vault_init_service 建它、脚本原本不建）
    #   CLAUDE_ITEMS  8→6   -settings.local.json（改生成）-mcp.json（退役）
    #   OBSIDIAN_FILES 6→9  -cls-internal-key.txt（改生成）+templates×2 +themes×2
    #   OBSIDIAN_PLUGINS 5→4 -claudian（退役）
    #   ROOT_FILES    2→3   +.mcp.json（git 追踪却从未进过任一数组）
    assert counts == {
        "SKELETON_DIRS": 8,
        "CLAUDE_ITEMS": 6,
        "OBSIDIAN_FILES": 9,
        "OBSIDIAN_PLUGINS": 4,
        "ROOT_FILES": 3,
    }, f"数组元素数与预期不符: {counts}"
    assert sum(counts.values()) == 30


def test_manifest_matches_install_arrays():
    """主判据: manifest 的 copy+skeleton 集合 == 五数组展开并集, 两侧差集均为空。"""
    arrays = _parse_install_arrays()
    from_script = {f"{ARRAY_PREFIX[name]}{item}" for name, items in arrays.items() for item in items}
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    from_manifest = {i["path"] for i in data["items"] if i["action"] in ("copy", "skeleton")}
    assert from_manifest - from_script == set(), "manifest 多出脚本没有的项"
    assert from_script - from_manifest == set(), "脚本数组有项未进 manifest"
    assert len(from_manifest) == 30


def test_manifest_covers_implicit_and_generated_semantics():
    """排除语义、两个隐含 exclude、generate 段都要有 item。

    origin 是**手写**的, 不会自己跟着脚本走 —— 这条门就是它的守门人。
    锚按**内容**取（`_sh_line`）: CARD-G2-7a 期间脚本三次增删行, 钉行号字面量的
    门批量假红, 而真正要防的「origin 指错地方」它反而看不见（Codex round-2 LOW）。
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    origins = {i["origin"] for i in data["items"]}
    pycache = f"install-vault.sh:{_sh_line('__pycache__ -prune')}"
    pending = f"install-vault.sh:{_sh_line('pending_archives')}"
    for required in (
        f"install-vault.sh:{_sh_line('明确不复制', kind='comment')}",  # 「明确不复制」注释块
        f"install-vault.sh:{_sh_line(SKELETON_LOOP_ANCHOR)}",  # 骨架 mkdir 循环
        pycache,  # find __pycache__ -prune
        pending,  # rm pending_archives*.jsonl
    ):
        assert required in origins, f"缺少源自 {required} 的 item"
    # yaml 生成器与生成件段是**区间** origin, 起点按内容锚, 区间尾另有越界门把关
    yaml_start = f"install-vault.sh:{_sh_line(YAML_HEREDOC_ANCHOR, prefix=True)}-"
    gen_start = f"install-vault.sh:{_sh_line('生成件 (CARD-G2-7a)', kind='comment')}-"
    assert any(o.startswith(yaml_start) for o in origins), f"缺少 yaml 生成器区间 origin ({yaml_start}…)"
    assert any(o.startswith(gen_start) and "生成件段" in o for o in origins), f"缺少生成件段 origin ({gen_start}…)"
    by_origin = {}
    for i in data["items"]:
        by_origin.setdefault(i["origin"], []).append(i)
    # find 只在 "$TARGET/.claude" 下剪 __pycache__ — 模式必须带该前缀,
    # 写成全树 `**/__pycache__` 就比源语义宽了。
    assert [i["path"] for i in by_origin[pycache]] == [".claude/**/__pycache__"]
    assert [i["path"] for i in by_origin[pending]] == [".claude/hooks/pending_archives*.jsonl"]
    # 每条 origin 都要真的指向脚本里存在的行（防「行号写错但没人发现」）
    import re as _re

    sh_lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    for o in origins:
        m = _re.match(r"install-vault\.sh:(\d+)(?:-(\d+))?", o)
        if m:
            n = int(m.group(1))
            end = int(m.group(2) or n)
            assert 1 <= n <= end <= len(sh_lines), f"origin {o} 指向脚本外的行（脚本 {len(sh_lines)} 行）"
            # 落在数组区的 origin, 起始行必须真是**某个数组的定义行** —— 行号偏一格
            # (指向注释/空行)时纯越界检查照样放行 (Codex round-2 LOW 实例)
            if MANIFEST_BLOCK[0] <= n <= MANIFEST_BLOCK[1]:
                assert _re.match(r"^[A-Z_]+=", sh_lines[n - 1]), (
                    f"origin {o} 落在数组区但第 {n} 行不是数组定义: {sh_lines[n - 1]!r}"
                )

    # CARD-G2-7a: generate 由 1 条扩到 5 条 —— 每 vault 应当**不同**的东西一律生成不复制
    generated = sorted(i["path"] for i in data["items"] if i["action"] == "generate")
    assert generated == [
        ".canvas-config.yaml",
        ".claude/settings.local.json",
        ".obsidian/cls-internal-key.txt",
        ".obsidian/plugins/canvas-learning-system/data.json",
        ".obsidian/plugins/templater-obsidian/data.json",
    ], f"generate 清单不符: {generated}"
    # 其中 4 条带 optional（除 .canvas-config.yaml —— 脚本无条件生成它, 必须在）
    gen_opt = sorted(i["path"] for i in data["items"] if i["action"] == "generate" and i.get("optional"))
    assert len(gen_opt) == 4 and ".canvas-config.yaml" not in gen_opt, f"generate+optional 不符: {gen_opt}"


def test_manifest_has_no_absolute_paths_and_no_secrets_inline():
    """(c) 0 绝对路径; 两个密钥件必须标 secret-or-local。"""
    raw = MANIFEST.read_text(encoding="utf-8")
    assert "/Users/" not in raw
    data = json.loads(raw)
    roles = {i["path"]: i["role"] for i in data["items"]}
    assert roles[".obsidian/cls-internal-key.txt"] == "secret-or-local"
    assert roles[".claude/settings.local.json"] == "secret-or-local"


def test_manifest_is_template_free():
    """(f)「活 vault 即模板」自证: manifest 不含任何内容/哈希基线字段。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    banned = {"sha256", "sha", "checksum", "content", "bytes", "size", "hash"}
    for item in data["items"]:
        assert not (set(item) & banned), f"{item['path']} 携带了内容基线字段"
    assert data["source"] == "harness-canvas-vault"  # E-4: 模板源改为 harness 树的 canvas-vault/


# ── schema (钉死点 2) ─────────────────────────────────────────────────


def test_repo_manifest_passes_schema():
    vv.load_manifest(MANIFEST)


@pytest.mark.parametrize(
    "mutate,fragment",
    [
        (lambda d: d.__setitem__("version", "1"), "version"),
        (lambda d: d.__setitem__("items", {}), "items"),
        (lambda d: d["items"][0].pop("role"), "role"),
        (lambda d: d["items"][0].__setitem__("action", "symlink"), "action"),
        (lambda d: d["items"][0].__setitem__("path", "/Users/x"), "绝对"),
        (lambda d: d["items"][0].__setitem__("path", "../escape"), ".."),
        (lambda d: d["items"].append(dict(d["items"][0])), "重复"),
    ],
)
def test_schema_rejects_malformed_manifest(tmp_path, mutate, fragment):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mutate(data)
    bad = tmp_path / "bad-manifest.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(bad)
    assert fragment in str(exc.value)


# ── 合成 vault fixture ────────────────────────────────────────────────


def _looks_like_file(path: str) -> bool:
    """合成 fixture 用的搭建启发式: 末段带扩展名 → 造文件, 否则造目录。

    只服务于本文件的 tmp 树搭建, 不是生产语义 (生产按磁盘实际类型判定)。
    """
    return "." in Path(path).name


HOTKEYS_REL_IN_VAULT = ".obsidian/hotkeys.json"


def _build_vault(root: Path, manifest: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for item in manifest["items"]:
        if item["action"] == "skeleton":
            (root / item["path"]).mkdir(parents=True, exist_ok=True)
        elif item["action"] == "copy":
            target = root / item["path"]
            if _looks_like_file(item["path"]):
                target.parent.mkdir(parents=True, exist_ok=True)
                if item["path"] == HOTKEYS_REL_IN_VAULT:
                    # 夹具形态必须与生产一致: 真实 vault 的 hotkeys.json 是 JSON 对象。
                    # 早先这里写的是 `content of …`(非法 JSON), 之所以没人发现, 是因为
                    # 校验器在 main.js 缺失时就提前 return、根本没验过 hotkeys 自身 ——
                    # 那个提前 return 正是 Codex round-4 的 MEDIUM。修好之后夹具立刻暴露。
                    target.write_text("{}\n", encoding="utf-8")
                else:
                    target.write_text(f"content of {item['path']}\n", encoding="utf-8")
            else:
                target.mkdir(parents=True, exist_ok=True)
                (target / "payload.txt").write_text(f"payload of {item['path']}\n", encoding="utf-8")
    (root / ".canvas-config.yaml").write_text('vault_id: "synthetic"\nsubject: "synthetic"\n', encoding="utf-8")


@pytest.fixture
def manifest_data() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture
def vault_pair(tmp_path, manifest_data):
    """一对逐字节相同的 source / target 合成 vault (基线全 match)。"""
    source = tmp_path / "source-vault"
    target = tmp_path / "target-vault"
    _build_vault(source, manifest_data)
    _build_vault(target, manifest_data)
    return source, target


def _run(target: Path, *, source: Path | None = None, report: Path | None = None) -> int:
    argv = ["--vault", str(target), "--manifest", str(MANIFEST)]
    if source is not None:
        argv += ["--source", str(source)]
    if report is not None:
        argv += ["--report", str(report)]
    return vv.main(argv)


def _classify(target: Path, *, source: Path | None = None):
    manifest = vv.load_manifest(MANIFEST)
    return vv.verify(target, manifest, source_dir=source)


def test_clean_pair_is_all_match(vault_pair, tmp_path):
    source, target = vault_pair
    report = tmp_path / "report.txt"
    assert _run(target, source=source, report=report) == 0
    result = _classify(target, source=source)
    assert result.missing == []
    assert result.extra == []
    assert result.content_drift == []
    assert result.intentionally_excluded == []
    # 30 数组项 + .canvas-config.yaml（generate，夹具显式造）= 31。
    # 其余 4 条 generate 项夹具不造 ⇒ 它们都带 optional ⇒ 进 optional-missing 不进 match。
    assert len(result.match) == 31


# ── 四类 diff 各自独立承重 (钉死点 3) ──────────────────────────────────


def _assert_only(result, bucket: str, expected_paths: list[str]):
    """一次只打一类: 目标桶精确命中, 其余三桶必须为空。"""
    buckets = {
        "missing": result.missing,
        "extra": result.extra,
        "content_drift": result.content_drift,
        "intentionally_excluded": result.intentionally_excluded,
    }
    assert sorted(f.path for f in buckets.pop(bucket)) == sorted(expected_paths)
    for name, findings in buckets.items():
        assert findings == [], f"变异只应触发 {bucket}, 但 {name} 也非空: {findings}"


def test_missing_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / ".obsidian" / "hotkeys.json").unlink()
    _assert_only(_classify(target, source=source), "missing", [".obsidian/hotkeys.json"])
    assert _run(target, source=source) == 1


def test_extra_is_detected_alone(vault_pair):
    source, target = vault_pair
    # ⚠️ 不能再用 .claude/cache —— CARD-G2-7a 把它放进 extra_allow 了, 它现在进
    # allowed-extra 而不是 extra。换一个**不在**白名单里的名字, 这条门才还在测 extra。
    (target / ".claude" / "probe-extra").mkdir()
    _assert_only(_classify(target, source=source), "extra", [".claude/probe-extra"])
    assert _run(target, source=source) == 2


def test_content_drift_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    _assert_only(_classify(target, source=source), "content_drift", ["Dashboard.md"])
    assert _run(target, source=source) == 2


def test_intentionally_excluded_is_detected_alone(vault_pair):
    source, target = vault_pair
    (target / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    _assert_only(
        _classify(target, source=source),
        "intentionally_excluded",
        [".obsidian/workspace.json"],
    )
    # intentionally-excluded 只报告, 不进退出码
    assert _run(target, source=source) == 0


def test_glob_exclude_matches_nested_pycache(vault_pair):
    """两个隐含 exclude 的实际匹配 (Finding.path = 声明的模式, detail 带命中项)。"""
    source, target = vault_pair
    (target / ".claude" / "scripts" / "__pycache__").mkdir(parents=True)
    (target / ".claude" / "hooks" / "pending_archives_2026.jsonl").write_text("[]", encoding="utf-8")
    result = _classify(target, source=source)
    by_path = {f.path: f for f in result.intentionally_excluded}
    assert sorted(by_path) == [
        ".claude/**/__pycache__",
        ".claude/hooks/pending_archives*.jsonl",
    ]
    assert ".claude/scripts/__pycache__" in by_path[".claude/**/__pycache__"].detail
    assert ".claude/hooks/pending_archives_2026.jsonl" in by_path[".claude/hooks/pending_archives*.jsonl"].detail
    # __pycache__ 落在 .claude 一级之下, 不在 extra 覆盖面 (.claude/* 只看直接子项)
    assert result.extra == []


def test_content_drift_not_evaluated_without_source(vault_pair):
    """(b) content-drift 只在给了 --source 时评估。"""
    _source, target = vault_pair
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    result = _classify(target, source=None)
    assert result.content_drift == []
    assert result.drift_evaluated is False
    assert _run(target) == 0


def test_missing_skeleton_dir_is_missing(vault_pair):
    source, target = vault_pair
    (target / "templates").rmdir()
    _assert_only(_classify(target, source=source), "missing", ["templates"])


def test_skeleton_present_as_file_is_missing(vault_pair):
    """骨架项存在但不是目录 —— 由「skeleton 须为目录」那道分支单独承重。

    与上一条不同: 上一条把目录删掉, 两道分支 (不存在 / 不是目录) 都能抓到,
    拆掉任一条另一条都兜得住; 只有这一条能单独把第二道分支打红。
    """
    source, target = vault_pair
    (target / "templates").rmdir()
    (target / "templates").write_text("骨架位置被占成了文件\n", encoding="utf-8")
    result = _classify(target, source=source)
    _assert_only(result, "missing", ["templates"])
    assert "不是目录" in result.missing[0].detail


def test_generate_item_missing_is_reported(vault_pair):
    source, target = vault_pair
    (target / ".canvas-config.yaml").unlink()
    _assert_only(_classify(target, source=source), "missing", [".canvas-config.yaml"])


# ── 退出码 2: 用法/配置错 (钉死点 4) ───────────────────────────────────


def test_absolute_path_in_manifest_exits_2(tmp_path, vault_pair, manifest_data):
    source, target = vault_pair
    manifest_data["items"][0]["path"] = "/Users/x"
    bad = tmp_path / "abs-manifest.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    rc = vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)])
    assert rc == 3


def test_missing_vault_dir_exits_2(tmp_path):
    rc = vv.main(["--vault", str(tmp_path / "nope"), "--manifest", str(MANIFEST)])
    assert rc == 3


def test_report_inside_vault_exits_2(vault_pair):
    source, target = vault_pair
    rc = _run(target, source=source, report=target / "report.txt")
    assert rc == 3
    assert not (target / "report.txt").exists()


def test_report_inside_source_exits_2(vault_pair):
    source, target = vault_pair
    rc = _run(target, source=source, report=source / "report.txt")
    assert rc == 3
    assert not (source / "report.txt").exists()


# ── Codex round-1 四条指控的回归门 ────────────────────────────────────
#
# 四条都在本机独立复现成立后才改的代码（证据 evidence-g26/codex-r1-claims-verified-*.txt）。
# 每条配一个能在修复前打红的反例——只写「修好了」不算数。


def test_report_hardlinked_into_vault_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: 树外报告路径若与树内文件同 inode，必须拒绝（rc=2）且不改那个文件。

    修复前: `is_relative_to` 只看路径不看 inode，检查放行 → `write_text` 原地覆盖，
    树内 Dashboard.md 被报告正文冲掉，且校验器还返回 0。
    """
    source, target = vault_pair
    victim = target / "Dashboard.md"
    before = victim.read_bytes()
    outside = tmp_path / "outside-report.txt"
    os.link(victim, outside)  # 树外路径，与树内文件共享 inode

    assert not outside.is_relative_to(target), "前提: 该路径确实在被查树之外"
    rc = _run(target, source=source, report=outside)
    assert rc == 3
    assert victim.read_bytes() == before, "树内文件被写穿了"


def test_normally_deployed_vault_is_not_reported_as_drift(vault_pair):
    """HIGH 回归: 模板源里有 exclude 件、目标按脚本剪掉了 —— 这是**正确部署**，不是漂移。

    修复前: 目录摘要把 `.claude/scripts/__pycache__` 与 `pending_archives*.jsonl`
    也算进去，于是 `.claude/scripts` 和 `.claude/hooks` 双双被判 content-drift、exit 1。
    """
    source, target = vault_pair
    # 活 vault（模板源）天然带这两类东西 —— live 实测确实有
    (source / ".claude" / "scripts" / "__pycache__").mkdir(parents=True)
    (source / ".claude" / "scripts" / "__pycache__" / "cached.pyc").write_bytes(b"\x00c")
    (source / ".claude" / "hooks" / "pending_archives_2026.jsonl").write_text("[]", encoding="utf-8")
    # target = install-vault.sh 正常部署的结果（:84 剪了 pycache，:86 删了归档队列）
    result = _classify(target, source=source)
    assert result.content_drift == [], "正确部署被误报 drift"
    assert result.missing == []
    assert result.extra == []
    assert result.intentionally_excluded == [], "目标侧本就没有这些件"
    assert _run(target, source=source) == 0


def test_exclude_kind_matches_script_type_conditions(vault_pair):
    """MEDIUM 回归: `:84` 是 `-type d`、`:86` 是 `rm -f` —— 类型不符的同名条目不算 excluded。"""
    source, target = vault_pair
    # __pycache__ 这次是个**普通文件**：脚本的 find -type d 不会删它
    (target / ".claude" / "scripts" / "__pycache__").write_text("not a dir", encoding="utf-8")
    # pending_archives_x.jsonl 这次是个**目录**：rm -f 不会删目录
    (target / ".claude" / "hooks" / "pending_archives_x.jsonl").mkdir(parents=True)
    result = _classify(target, source=source)
    assert result.intentionally_excluded == [], "类型不符却被判 excluded，与脚本的 -type d / rm -f 条件不一致"


@pytest.mark.parametrize("bad_action", [[], {}, 123, None])
def test_non_string_action_still_exits_2(tmp_path, vault_pair, manifest_data, bad_action):
    """MEDIUM 回归: unhashable 的 action 曾抛 TypeError 逃出捕获面，CLI 拿不到 rc=2。"""
    source, target = vault_pair
    manifest_data["items"][0]["action"] = bad_action
    bad = tmp_path / "bad-action.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError):
        vv.load_manifest(bad)
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)]) == 3


@pytest.mark.parametrize("bad_kind", ["directory", "DIR", 1, []])
def test_invalid_kind_is_rejected(tmp_path, manifest_data, bad_kind):
    manifest_data["items"][0]["kind"] = bad_kind
    bad = tmp_path / "bad-kind.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(bad)
    assert "kind" in str(exc.value)


def test_manifest_declares_kind_for_the_two_typed_excludes():
    """两个隐含 exclude 必须带类型条件，且类型要对得上脚本命令的实际可删集合。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_path = {i["path"]: i for i in data["items"]}
    # :84 是 find -type d —— 只剪目录
    assert by_path[".claude/**/__pycache__"]["kind"] == "dir"
    # :86 的强制删除清掉一切**非目录**条目（软链、悬空软链、FIFO 都删，真目录不删）。
    # 写成 "file" 是错的：is_file() 对后三者为 False。
    assert by_path[".claude/hooks/pending_archives*.jsonl"]["kind"] == "nondir"


def test_manifest_does_not_over_constrain_path_only_excludes():
    """:68/:69 那些按路径声明「不复制」的项**没有**类型条件，不得擅自加 kind。

    早先给 learning_events.jsonl 与 workspace.json 加了 kind=file，反而收窄了语义：
    同名的目录会因类型不符而落到 extra 去。
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_path = {i["path"]: i for i in data["items"]}
    for p in ("learning_events.jsonl", ".obsidian/workspace.json", "outputs/**", "原白板/**"):
        assert "kind" not in by_path[p], f"{p} 不该有类型条件"


def test_verifier_exposes_only_readonly_switches():
    """(b) 只读: CLI 参数面是**白名单**, 多一个开关就红。

    不用「文本里不得出现 --fix」那种判据 —— 它既假红 (docstring 里提一嘴就中)
    又假绿 (换个名字叫 --repair-now 就漏)。白名单挡得住没预想到的名字。
    """
    parser = vv._build_parser()
    options = {s for action in parser._actions for s in action.option_strings}
    assert options == {"-h", "--help", "--vault", "--source", "--manifest", "--report"}
    # 白名单只管带前缀的开关；位置参数和子命令的 option_strings 是空的，会从名单里漏过去
    positional = [a for a in parser._actions if not a.option_strings]
    assert positional == [], f"不得有位置参数或子命令: {positional}"


def _is_stdio_write(node) -> bool:
    """精确豁免 `sys.stdout.write` / `sys.stderr.write` 两个字面形态。

    只豁免这两个：`f.write(...)` 那种对文件对象的写照样要被抓住，
    所以判据不能简单地放过所有名字叫 write 的调用。
    """
    import ast

    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "write":
        return False
    owner = func.value
    return (
        isinstance(owner, ast.Attribute)
        and owner.attr in ("stdout", "stderr")
        and isinstance(owner.value, ast.Name)
        and owner.value.id == "sys"
    )


def test_verifier_write_calls_are_confined_to_write_report():
    """(b) 只读: 所有写调用必须落在 `_write_report()` 这一个函数内。

    比早先那条「只允许一次 write_text」强两处：
      ① 调用名面扩大 —— 旧版漏掉 `Path.open("w")`、文件对象 `.write`、
         `os` 模块里**列在 `write_names` 中的那些**、以及 from-import 形式的 rmtree；
      ② 判据从「计数 + 落在 main 的行号区间」改成「按函数边界圈定」——
         写操作只允许出现在那个专门负责落盘的函数里，别处一个都不许有。
    看的是调用节点，不是文本，所以注释/docstring 里怎么写都不影响判定。

    **它不证明什么**（Codex round-2 MEDIUM-3 指出前，这里写的是「`os.*` 全族」，
    那是过强措辞，已改）：本门按**表面调用名**筛选，因此下面这些写调用**根本不进**
    判定，`offenders == []` 也不排除它们存在 —— 已登记移交独立卡：
      - 别名：`_open = os.open` 之后 `_open(p, os.O_WRONLY | os.O_TRUNC)`；
      - 动态取属性：`getattr(os, "open")(p, os.O_WRONLY | os.O_TRUNC)`；
      - 间接调用：`functools.partial(os.open, p, os.O_WRONLY | os.O_TRUNC)()`；
      - 名单本身的遗漏：`os.ftruncate(fd, 0)` 等不在 `write_names` 里的写 API。
    """
    import ast

    source = VERIFIER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    write_names = {
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmdir",
        "touch",
        "rename",
        "replace",
        "chmod",
        "symlink_to",
        "rmtree",
        "copy",
        "copytree",
        "copy2",
        "move",
        "write",
        "writelines",
        "truncate",
        "makedirs",
        "remove",
        "link",
        "symlink",
        "mknod",
        "mkfifo",
        "chown",
        "utime",
        "open",
    }
    funcs = {
        n.name: (n.lineno, n.end_lineno)
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.end_lineno is not None
    }
    assert "_write_report" in funcs, "落盘应当收敛到 _write_report()"
    lo, hi = funcs["_write_report"]

    # 重绑定拒绝（Codex round-2 MEDIUM-1）：本门按**实参位置**判断哪个是 mode/flags,
    # 而这个前提只在「调用名解析到原始 API」时成立。若源码里把写 API 重新绑定过 ——
    #   `os.open = functools.partial(os.open, p)` 之后 `os.open(os.O_WRONLY | os.O_TRUNC, ...)`
    # —— 表面的第 2 个实参其实是 mode、真正的 flags 落在第 1 个位置上, 按位置读出来的
    # 结论就是错的（实测: 该输入在本卡加 os.open 分支前判 False、加之后判 True）。
    # 静态跟不了重绑定, 就明确拒绝, 而不是继续按一个已经不成立的前提去判。
    # ⚠️ 只拦**真能改变调用解析**的两类, 不一刀切（一刀切会误伤同名局部变量, 例如
    #    生产脚本 :899 的 `link = cur / rel`）:
    #      - `<owner>.<写名> = ...`  例如 `os.open = ...`
    #      - `open = ...`            遮蔽内置 open
    # ⚠️ 判据按 **Store 上下文** 走, 不按「是不是 Assign 的 targets」——后者漏掉解包
    #    `(os.open,) = (...)`、`for` 目标、`with ... as`、海象、推导式目标等一大片
    #    （Codex round-3 MEDIUM-1 给的就是解包那一例）。Store 上下文一次覆盖它们全部。
    # ⚠️ **只有类型注解、没有赋值**（`os.open: object`）不改变任何绑定, 必须排除,
    #    否则是假红（Codex round-3 LOW-2；本文件另有 16 处无值注解, 误报面真实存在）。
    # ⚠️ 敏感名集**只有** `os` 与 `open` —— 本门的位置判断只依赖这两个名字解析到原始 API。
    #    曾经把 `io` / `builtins` 也放进来(为了配合模块级 open 那个特性), 代价是
    #    `def label(io)` / `for io in []` / 函数内 `io = 1` 这类**合法只读代码**统统假红
    #    (Codex round-4 LOW-9)。那个特性本身是**既有**缺口、不是本卡引入的,
    #    修它超出本卡范围 —— 已连同特性一起撤回、登记移交。
    _rebind_sensitive = {"open", "os"}
    # ⚠️ 只跳 `AnnAssign` 的 **target 节点本身**, 不跳整棵子树: 无值注解虽然不赋值给
    #    target, 它的**对象表达式仍会求值** —— `(open := partial(open, "log")).open: object`
    #    里的海象绑定是真的会执行的, 跳整棵子树就把它一并漏掉了(Codex round-4 MEDIUM-3)。
    annotation_only = {
        id(node.target) for node in ast.walk(tree) if isinstance(node, ast.AnnAssign) and node.value is None
    }
    rebinds = []
    for node in ast.walk(tree):
        if id(node) in annotation_only:
            continue
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in _rebind_sensitive:
            rebinds.append((node.id, node.lineno))
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and node.attr in write_names:
            rebinds.append((ast.unparse(node), node.lineno))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                if arg.arg in _rebind_sensitive:
                    rebinds.append((arg.arg, node.lineno))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                if local in _rebind_sensitive and alias.name != "os":
                    rebinds.append((local, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if (alias.asname or alias.name) in _rebind_sensitive:
                    rebinds.append((alias.asname or alias.name, node.lineno))
    assert rebinds == [], f"写 API / 其 owner 被重新绑定, 按位置判 mode/flags 的前提失效: {sorted(set(rebinds))}"

    # 验伪锚(CARD-G2-7a-TAIL): 只读豁免 `_is_readonly_open` 自己先得站得住 —— 否则
    # 下面那条 `offenders == []` 可能是**因为豁免放水**而绿, 不是因为源码真的没写调用。
    # 逐条给出「在什么输入下结论应当不同」, 而不是只证一个正例。
    def _verdict(expr: str) -> bool:
        return _is_readonly_open(ast.parse(expr, mode="eval").body)

    assert _verdict("os.open(p, os.O_RDONLY | os.O_NONBLOCK)") is True, "只读旗标必须放行"
    assert _verdict("os.open(p, os.O_RDONLY)") is True, "单个只读旗标必须放行"
    assert _verdict("os.open(p, os.O_WRONLY | os.O_CREAT)") is False, "写旗标不得放行"
    assert _verdict("os.open(p, os.O_RDONLY | os.O_TRUNC)") is False, "混进一个写旗标就不得放行"
    assert _verdict("os.open(p, flags)") is False, "算出来的旗标证明不了只读"
    assert _verdict("os.open(p)") is False, "缺旗标不得放行"
    assert _verdict("p.open('wb+')") is False, "绑定方法的写模式主张不得被削弱"
    assert _verdict("p.open()") is True, "绑定方法缺省模式仍是只读"
    assert _verdict("open(p, 'rb')") is True, "内置 open 的只读模式仍放行"
    assert _verdict("open(p, 'w')") is False, "内置 open 的写模式仍不放行"
    # 参数展开: 位置绑定不可知 ⇒ 一律不放行(Codex round-1 MEDIUM + 本卡自查的同族第二例)
    assert _verdict("os.open(*[p, os.O_WRONLY | os.O_TRUNC], os.O_RDONLY)") is False, (
        "展开后 flags 是写+截断, 按位置读 args[1] 会读成只读 —— 不得放行"
    )
    assert _verdict("os.open(p, os.O_RDONLY, **kw)") is False, "**kwargs 可再塞实参, 不得放行"
    assert _verdict("os.open(*args)") is False, "整串展开不得放行"
    assert _verdict("os.open(p, *flags_list)") is False, "旗标位展开不得放行"
    assert _verdict("open(*args)") is False, "内置 open 的展开形态不得放行"
    assert _verdict("p.open(*a)") is False, "绑定方法的展开形态不得放行"
    # ⚠️ `io.open("log", "w")` / `builtins.open(...)` 这类**模块级 open** 本门仍会误豁免
    #    (它们形态是 Attribute, 被当成绑定方法、把 "log" 当模式读)。那是**既有**缺口,
    #    与别名 / getattr / partial / 名单遗漏同属一族, 已登记移交独立卡 —— 本卡不扩面。
    #    我曾在 round-2 修过它, 结果两轮里引入 6 个新缺陷(判值反转 + 合法代码假红),
    #    round-5 连同那个特性一起撤回。见验收单 §八。

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = None
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        if name not in write_names:
            continue
        if name == "open" and _is_readonly_open(node):
            # `open(p, "rb")` 是只读探测, 不是落盘。**只按模式字面量放行** ——
            # 缺省模式("r")也放行, 但任何含 w/a/x/+ 的模式、以及模式是变量算出来的,
            # 都仍然算违规(宁可假红也不放宽这道门的主张)。
            continue
        if _is_stdio_write(node):
            # 缺省报告去处。说明一句边界: 这里只按**语法形态**豁免
            # `sys.stdout` / `sys.stderr` 这两个名字，并**不验证运行时那个文件描述符
            # 指向哪里**（被重定向到文件时它当然会落盘）。这道门证明的是
            # 「源码里没有别处的写调用」，不是「进程一定不写文件」。
            continue
        if not (lo <= node.lineno <= hi):
            offenders.append((name, node.lineno))
    assert offenders == [], f"写调用出现在 _write_report 之外: {offenders}"

    # 危险的整树删除工具一律不许进来，无论 import 形式
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(a.name for a in node.names)
    assert "shutil" not in imported and "rmtree" not in imported


# ── 零写门 (钉死点 5) ─────────────────────────────────────────────────


# `os.open()` 的旗标里, 这些是**确定不写**的; 任何不在表内的名字(O_WRONLY / O_RDWR /
# O_CREAT / O_TRUNC / O_APPEND …)都不放行。表是白名单不是黑名单 —— 黑名单漏一个就放水。
_OS_OPEN_READONLY_FLAGS = frozenset({"O_RDONLY", "O_NONBLOCK", "O_CLOEXEC", "O_NOFOLLOW", "O_DIRECTORY", "O_NOCTTY"})


def _is_os_open(node) -> bool:
    """是不是字面形态的 `os.open(...)`(而不是内置 open / 绑定方法 path.open)。"""
    import ast

    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "open"
        and isinstance(func.value, ast.Name)
        and func.value.id == "os"
    )


def _os_open_flag_names(flags):
    """把 `os.O_A | os.O_B` 这种**纯字面**旗标表达式摊成名字集合; 形态不认得返回 None。

    只认 `os.O_XXX` 与它们之间的 `|`。变量、函数调用、算术、`getattr` 一律返回 None ⇒
    上层判不放行 —— 与模式字面量那条同一主张: **算出来的东西证明不了只读**。
    """
    import ast

    if isinstance(flags, ast.Attribute) and isinstance(flags.value, ast.Name) and flags.value.id == "os":
        return {flags.attr}
    if isinstance(flags, ast.BinOp) and isinstance(flags.op, ast.BitOr):
        left = _os_open_flag_names(flags.left)
        right = _os_open_flag_names(flags.right)
        if left is None or right is None:
            return None
        return left | right
    return None


def _is_readonly_open(node) -> bool:
    """`open()` 调用是否**确定**只读: 模式缺省, 或模式是不含 w/a/x/+ 的字面量。

    ⚠️ 模式参数的**位置随调用形态变**: 内置 `open(path, mode)` 是第 2 个,
    而绑定方法 `path.open(mode)` 是第 **1** 个。上一轮统一按第 2 个判 ⇒
    `path.open("wb+")` 被当成「没给模式」而放行 —— 我为只读探测开的豁免,
    把 U3-A 的零写门重新捅开了(Codex round-4 实测)。

    ⚠️ `os.open(path, flags)` 是**第三种**形态, 且此前被这里误判: 它也是 Attribute 调用,
    于是走了 `bound_method` 那条分支、把 **path**(args[0]) 当模式读 —— 不是字符串字面量,
    结论恒 False。对 CARD-G2-7a-TAIL 新增的只读探测 `os.open(p, os.O_RDONLY | os.O_NONBLOCK)`
    就会误报成「写调用」。这里给它单开一条分支, 判据仍是**只按字面量放行**:
    旗标必须是纯 `os.O_*` 字面(可用 `|` 连), 且**全部**落在只读白名单里;
    缺旗标 / 算出来的旗标 / 含任一写旗标, 一律不放行。
    """
    import ast

    if any(isinstance(a, ast.Starred) for a in node.args) or any(kw.arg is None for kw in node.keywords):
        # 参数被展开(`*args` / `**kwargs`)时**位置绑定不可知** —— 哪个实参最终落到 mode/flags
        # 位上, 在静态看不出来。与「算出来的模式证明不了只读」是同一主张, 一律不放行。
        # 未被拦下的输入(Codex round-1 MEDIUM, 已实测复现):
        #   `os.open(*[p, os.O_WRONLY | os.O_TRUNC], os.O_RDONLY)`
        #   —— 展开后 flags 其实是 O_WRONLY|O_TRUNC(写且截断), 而 AST 的 args[1] 是
        #   `os.O_RDONLY`; 按位置去读就读成了只读。同族第二例(本卡自查补出):
        #   `os.open(p, os.O_RDONLY, **kw)` —— `**kw` 可再塞进别的实参。
        # ⚠️ 这道拒绝必须放在**所有分支之前**: 本卡加 `os.open` 分支之前, 展开形态是被
        #   「mode 不是字符串字面量」这条**顺带**挡住的; 新分支更精确, 却把那条附带保证
        #   删掉了 —— 精确性提高不等于强度提高, 这里显式补回来。
        return False

    if _is_os_open(node):
        flags = node.args[1] if len(node.args) > 1 else None
        for kw in node.keywords:
            if kw.arg == "flags":
                flags = kw.value
        if flags is None:
            return False  # os.open 缺旗标在语法上不合法, 但宁可当违规也不猜
        names = _os_open_flag_names(flags)
        return names is not None and names <= _OS_OPEN_READONLY_FLAGS

    bound_method = isinstance(node.func, ast.Attribute)  # x.open(...) ⇒ 模式在 args[0]
    mode_index = 0 if bound_method else 1
    mode = None
    if len(node.args) > mode_index:
        mode = node.args[mode_index]
    for kw in node.keywords:
        if kw.arg == "mode":
            mode = kw.value
    if mode is None:
        return True  # 缺省 "r"
    if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)):
        return False  # 算出来的模式无法证明只读
    return not any(c in mode.value for c in "wax+")


def _tree_digest(root: Path) -> str:
    entries = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            entries.append(f"DIR   {rel}")
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{digest}  {rel}")
    return "\n".join(entries)


def test_verifier_writes_nothing_into_vault_or_source(vault_pair, tmp_path):
    source, target = vault_pair
    # 先制造全部四类差异, 让校验器走遍所有分类分支
    (target / ".obsidian" / "hotkeys.json").unlink()
    (target / ".claude" / "cache").mkdir()
    (target / "Dashboard.md").write_text("drifted\n", encoding="utf-8")
    (target / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")

    before_target, before_source = _tree_digest(target), _tree_digest(source)
    report = tmp_path / "zero-write-report.txt"
    assert _run(target, source=source, report=report) == 2
    assert _tree_digest(target) == before_target, "校验器写了目标 vault"
    assert _tree_digest(source) == before_source, "校验器写了模板源"
    assert report.exists()


# ── Codex round-2 + 对抗审查的回归门 ──────────────────────────────────
#
# 这一组同样是「先在本机复现指控成立，再改代码，再补门」的产物。
# 证据：evidence-g26/codex-r2-claims-verified-*.txt


def test_report_via_dev_fd_alias_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: `--report /dev/fd/N` 曾能写穿被审文件。

    `/dev/fd/N` 的 resolve() 返回它自己（路径判据以为在树外），stat() 又返回被打开
    文件的属性、st_nlink=1（硬链接判据也不触发）——两道早退判据同时失明。
    真正承重的是落盘写法本身：临时文件 + os.replace，绝不原地覆盖已有 inode。
    """
    source, target = vault_pair
    victim = target / "Dashboard.md"
    before = victim.read_bytes()
    fd = os.open(str(victim), os.O_WRONLY)
    try:
        rc = _run(target, source=source, report=Path(f"/dev/fd/{fd}"))
    finally:
        os.close(fd)
    assert rc == 3
    assert victim.read_bytes() == before, "被审文件被写穿了"


def test_report_behind_vault_symlink_is_refused(tmp_path, manifest_data):
    """HIGH 回归: vault 里一条指向树外的目录软链，会让「树外」路径其实就是树内文件。

    只比路径前缀挡不住这个：报告落点在 vault 之外（字符串上成立），但通过 vault 里
    那条软链看得见。落点判据必须把树内软链的解析目标也算作禁写区。
    """
    outside = tmp_path / "outside-claude"
    (outside / "skills").mkdir(parents=True)
    real = outside / "settings.json"
    real.write_text("REAL SETTINGS\n", encoding="utf-8")
    vault = tmp_path / "v"
    _build_vault(vault, manifest_data)
    # 把 vault 里的 .claude 换成指向树外目录的软链
    shutil_free_remove(vault / ".claude")
    os.symlink(str(outside), str(vault / ".claude"))

    assert not real.resolve().is_relative_to(vault.resolve()), "前提: 落点在路径意义上确实在树外"
    rc = _run(vault, report=real)
    assert rc == 3
    assert real.read_text(encoding="utf-8") == "REAL SETTINGS\n"


def shutil_free_remove(path: Path) -> None:
    """删掉一棵测试用的临时目录树（只在 tmp_path 下用；不引入 shutil，AST 门禁它）。"""
    for child in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if child.is_dir() and not child.is_symlink():
            child.rmdir()
        else:
            child.unlink()
    path.rmdir()


def test_unreadable_subtree_is_not_reported_as_match(vault_pair):
    """HIGH 回归: 读不进去的子树不得被当成「不存在」而判等。

    `Path.rglob` 静默吞 PermissionError —— 源里一棵 000 权限的子树看起来跟不存在
    一样，与目标的空目录一比就「相等」，exit=0。那是漏报：把「我看不见」说成
    「一致」，比误报危险。
    """
    source, target = vault_pair
    locked = source / ".claude" / "hooks" / "child"
    locked.mkdir(parents=True)
    (locked / "hidden.txt").write_text("SECRET DIFFERENCE\n", encoding="utf-8")
    (target / ".claude" / "hooks" / "child").mkdir(parents=True)  # 目标是空目录
    os.chmod(locked, 0o000)
    try:
        result = _classify(target, source=source)
        assert result.unreadable != [], "不可读条目必须被登记"
        assert result.exit_code != 0, "读不进去就不能报 0"
    finally:
        os.chmod(locked, 0o755)


def test_trailing_newline_name_is_not_excluded(vault_pair):
    """MEDIUM 回归: 正则用 `$` 会匹配「最后一个换行之前」，名字带尾随换行的文件被误排除。

    POSIX 文件名允许换行；shell 的模式不会匹配它，校验器也不该匹配。
    """
    rx = vv._pattern_to_regex(".claude/hooks/pending_archives*.jsonl")
    assert rx.fullmatch(".claude/hooks/pending_archives_keep.jsonl")
    assert not rx.fullmatch(".claude/hooks/pending_archives_keep.jsonl\n")
    source, target = vault_pair
    weird = source / ".claude" / "hooks" / "pending_archives_keep.jsonl\n"
    weird.write_text("[]", encoding="utf-8")
    result = _classify(target, source=source)
    # 源多了一个不该被排除的文件 → 必须体现为 drift，而不是被静默排除
    assert [f.path for f in result.content_drift] == [".claude/hooks"]


@pytest.mark.parametrize(
    "bad_scan",
    [
        {"dir": 123, "match": "*"},
        {"dir": [], "match": "*"},
        {"dir": ".claude", "match": 123},
        {"dir": ".claude", "match": []},
        {"dir": ".claude", "match": ""},
        {"dir": "/absolute", "match": "*"},
        {"dir": "../outside", "match": "*"},
    ],
)
def test_invalid_extra_scan_exits_2(tmp_path, vault_pair, manifest_data, bad_scan):
    """MEDIUM 回归: extra_scan 的 dir/match 曾完全不校验。

    非字符串让校验器以未捕获 TypeError 终止（rc=1 而非承诺的 2）；更糟的是 `dir`
    接受绝对路径与 `..`，扫描面直接逃出 --vault。path 有这套校验、extra_scan.dir
    没有——同一条约束只在一半字段上生效，正是根因。
    """
    source, target = vault_pair
    manifest_data["extra_scan"] = [bad_scan]
    bad = tmp_path / "bad-scan.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError):
        vv.load_manifest(bad)
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)]) == 3


@pytest.mark.parametrize("variant", [".claude/skills/", ".claude//skills", ".claude/./skills"])
def test_path_is_normalized_so_match_and_extra_agree(tmp_path, vault_pair, manifest_data, variant):
    """MEDIUM 回归: path 原样入集、extra 检测用规范化路径 → 同一条目同时进 match 与 extra。"""
    source, target = vault_pair
    for item in manifest_data["items"]:
        if item["path"] == ".claude/skills":
            item["path"] = variant
            break
    else:  # pragma: no cover — 清单里一定有这一项
        raise AssertionError("清单里找不到 .claude/skills")
    m = tmp_path / "variant.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    manifest = vv.load_manifest(m)
    assert ".claude/skills" in manifest.declared_paths, "规范化后应当与磁盘上的相对路径一致"
    result = vv.verify(target, manifest, source_dir=source)
    assert result.extra == [], "同一条目不该既是 match 又是 extra"
    assert result.missing == []


@pytest.mark.parametrize(
    "bad_manifest_bytes",
    [b"\xff\xfe not utf-8", b"{ not json", b'{"version": 1'],
)
def test_unreadable_or_malformed_manifest_exits_2(tmp_path, vault_pair, bad_manifest_bytes):
    """MEDIUM 回归: 非 UTF-8 / 坏 JSON 曾以未捕获异常终止，rc=1 而非 2。"""
    source, target = vault_pair
    bad = tmp_path / "bad.json"
    bad.write_bytes(bad_manifest_bytes)
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--source", str(source)]) == 3


def test_manifest_pointing_at_a_directory_exits_2(tmp_path, vault_pair):
    """`--manifest` 指向一个目录时也必须是 rc=2（曾是 IsADirectoryError 逃出）。"""
    source, target = vault_pair
    assert vv.main(["--vault", str(target), "--manifest", str(tmp_path), "--source", str(source)]) == 3


def test_exclude_kind_nondir_matches_what_the_script_deletes(vault_pair):
    """脚本 `:86` 的强制删除清掉一切非目录条目 —— 软链/悬空软链/FIFO 都算，真目录不算。"""
    _source, target = vault_pair
    hooks = target / ".claude" / "hooks"
    (hooks / "pending_archives_plain.jsonl").write_text("[]", encoding="utf-8")
    os.symlink(str(target / "Dashboard.md"), str(hooks / "pending_archives_link.jsonl"))
    os.symlink(str(target / "nope"), str(hooks / "pending_archives_dangling.jsonl"))
    os.mkfifo(str(hooks / "pending_archives_fifo.jsonl"))
    (hooks / "pending_archives_dir.jsonl").mkdir()

    hits = vv.ExcludeMatcher(vv.load_manifest(MANIFEST).exclude_items).hits_for(
        target,
        next(i for i in vv.load_manifest(MANIFEST).items if i.path == ".claude/hooks/pending_archives*.jsonl"),
    )
    assert "pending_archives_plain.jsonl" in " ".join(hits)
    assert "pending_archives_link.jsonl" in " ".join(hits)
    assert "pending_archives_dangling.jsonl" in " ".join(hits)
    assert "pending_archives_fifo.jsonl" in " ".join(hits)
    assert "pending_archives_dir.jsonl" not in " ".join(hits), "真目录不该被算作已删除"


def test_extra_scan_surface_is_pinned():
    """extra 覆盖面是本卡承诺的一部分，删掉一条不能静默通过。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert [(s["dir"], s["match"]) for s in data["extra_scan"]] == [
        (".claude", "*"),
        (".obsidian", "*.json"),
        (".obsidian/plugins", "*"),
    ]


def test_target_side_exclusion_is_also_pinned(vault_pair):
    """exclude 剔除在**目标侧**同样承重（早先只有源侧那一半被钉住）。"""
    source, target = vault_pair
    (target / ".claude" / "scripts" / "__pycache__").mkdir(parents=True)
    (target / ".claude" / "scripts" / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    result = _classify(target, source=source)
    assert result.content_drift == [], "目标侧多出的排除件不该算 drift"
    assert [f.path for f in result.intentionally_excluded] == [".claude/**/__pycache__"]


def test_array_parse_scans_whole_file_not_a_fixed_window():
    """五数组解析不能只盯 :63-67 —— 那一行之下新增第 6 个数组会对主判据不可见。"""
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    whole = re.findall(r"^([A-Z_]+)=\(([^)]*)\)\s*$", "\n".join(lines), re.M)
    assert len(whole) == 5, f"全文扫描到的数组数与预期不符: {[n for n, _ in whole]}"
    lo, hi = MANIFEST_BLOCK
    for name, _ in whole:
        hit = [i + 1 for i, ln in enumerate(lines) if ln.startswith(name + "=(")]
        assert hit and lo <= hit[0] <= hi, f"{name} 落在 MANIFEST 区之外: 第 {hit} 行"


def test_bracket_is_literal_in_both_places(vault_pair):
    """`[` 在 _has_glob 与 _pattern_to_regex 两处必须是同一种东西。

    早先 GLOB_CHARS 含 `[`，于是一条写成字符类的模式会被判为 glob（走正则路径），
    而正则里 `[` 又被 re.escape 成字面量 —— 两处口径分裂，模式静默不命中，
    正确部署的 vault 因此被误报 drift。现在统一按字面量。
    """
    assert not vv._has_glob("outputs/[abc].json"), "`[` 不再算通配符"
    rx = vv._pattern_to_regex("outputs/[abc].json")
    assert rx.fullmatch("outputs/[abc].json"), "字面量应当精确命中"
    assert not rx.fullmatch("outputs/a.json"), "不得展开成字符类"
    # 真实文件名里的方括号按字面匹配 —— 这才是这类名字该有的行为
    source, target = vault_pair
    odd = target / "outputs" / "[draft].json"
    odd.write_text("{}", encoding="utf-8")
    result = _classify(target, source=source)
    assert [f.path for f in result.intentionally_excluded] == ["outputs/**"]
    assert odd.name in result.intentionally_excluded[0].detail


def test_duplicate_path_is_caught_after_normalization(tmp_path, manifest_data):
    """`outputs/` 与 `outputs` 是同一个 path —— 查重必须在规范化之后做。"""
    for item in manifest_data["items"]:
        if item["path"] == "outputs/**":
            item["path"] = "outputs/"
            break
    bad = tmp_path / "dup.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(bad)
    assert "重复" in str(exc.value)


def test_unreadable_alone_still_blocks(vault_pair):
    """unreadable 单独出现时也必须挡住 —— 这条是「计入阻断」的专属门。

    上一条 test_unreadable_subtree_is_not_reported_as_match 里源侧不可读、目标侧空，
    两侧摘要不同 ⇒ content_drift 非空 ⇒ 退出码被它兜成 1，于是「unreadable 计入阻断」
    那段逻辑拆掉也不红（纵深兜住）。这里让**两侧都有同一个读不进去的目录**：
    摘要相同、没有 drift，unreadable 成为唯一的差异来源。
    顺带钉住一件事——两侧都读不进去时摘要会「判等」，所以不假绿全靠 unreadable 这一桶。
    """
    source, target = vault_pair
    locked_src = source / ".claude" / "hooks" / "locked"
    locked_tgt = target / ".claude" / "hooks" / "locked"
    for d in (locked_src, locked_tgt):
        d.mkdir(parents=True)
        (d / "same.txt").write_text("same\n", encoding="utf-8")
    os.chmod(locked_src, 0o000)
    os.chmod(locked_tgt, 0o000)
    try:
        result = _classify(target, source=source)
        assert result.content_drift == [], "两侧同样读不进去，摘要应当判等（无 drift）"
        assert result.missing == [] and result.extra == []
        assert result.unreadable != [], "读不进去必须被登记"
        assert result.exit_code != 0, "unreadable 单独出现时也不能报 0"
        assert _run(target, source=source) == 2
    finally:
        os.chmod(locked_src, 0o755)
        os.chmod(locked_tgt, 0o755)


# ── Codex round-3 的回归门 ────────────────────────────────────────────
#
# 八条都是隔离夹具实测成立后才改的，证据 evidence-g26/codex-r3-claims-AFTER-FIX-*.txt。


def test_case_insensitive_alias_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: 大小写目录别名曾直接绕过禁写检查。

    本机文件系统默认大小写不敏感——目录实际叫什么大小写都指向同一个对象，
    而 `resolve()` 不做大小写规范化、`is_relative_to` 是纯字符串比较。
    落点判据必须按 `(st_dev, st_ino)` 判，路径这个维度本身不成立。
    """
    _source, target = vault_pair
    if not (target.parent / target.name.upper()).is_dir():
        pytest.skip("本机文件系统大小写敏感，这条形态不适用")
    alias = target.parent / target.name.upper() / "report.txt"
    rc = _run(target, report=alias)
    assert rc == 3
    assert not (target / "report.txt").exists(), "报告被写进了被审树"


def test_exclusive_create_failure_does_not_delete_someone_elses_file(vault_pair, tmp_path):
    """BLOCKER 回归: `O_EXCL` 失败时那个文件不是本次创建的，绝不能清理它。

    早先 except 分支无条件 `unlink(tmp)`——实测会删掉别人的文件，
    指向它的软链因此变悬空。这是本轮整改**自己引入**的缺陷。
    """
    del vault_pair  # 这条只需要一个可写的临时目录, 不用被审树
    outside = tmp_path / "outside"
    outside.mkdir()
    report = outside / "report.txt"

    # 临时名 = .<name>.tmp-<pid>-<随机串>。把随机串固定住，才能预置一个**同名**的
    # 「别人的文件」，让 O_EXCL 真的失败 —— 否则那条 except 分支根本不会被触发，
    # 测试看起来绿其实什么都没验（fixture 形态 ≠ 生产形态）。
    fixed = bytes.fromhex("deadbeef")
    stranger = outside / f".report.txt.tmp-{os.getpid()}-deadbeef"
    stranger.write_text("SOMEONE ELSE'S FILE\n", encoding="utf-8")

    real_urandom = os.urandom
    os.urandom = lambda n: fixed[:n]
    try:
        with pytest.raises(vv.ReportWriteError):
            vv._write_report(report, "报告正文\n")
    finally:
        os.urandom = real_urandom

    assert stranger.exists(), "删掉了不属于本次调用的临时文件"
    assert stranger.read_text(encoding="utf-8") == "SOMEONE ELSE'S FILE\n"
    assert not report.exists(), "O_EXCL 失败后不该产出报告"


def test_two_hop_symlink_target_is_refused(vault_pair, tmp_path):
    """BLOCKER 回归: 禁写根必须**递归**展开——两层软链能绕开单层解析。"""
    _source, target = vault_pair
    a, b = tmp_path / "outA", tmp_path / "outB"
    a.mkdir()
    b.mkdir()
    os.symlink(str(b), str(a / "link"))
    os.symlink(str(a), str(target / "link"))
    rc = _run(target, report=b / "report.txt")
    assert rc == 3
    assert not (target / "link" / "link" / "report.txt").exists()


def test_incomplete_safety_scan_refuses_to_write(vault_pair, tmp_path):
    """BLOCKER 回归: 安全性扫描没跑完就不能声称落点安全。

    权限 0111 的目录能按名字访问、不能列目录——里面可能藏着指向树外的软链。
    扫不动就必须拒绝落盘，而不是默默放行。
    """
    _source, target = vault_pair
    locked = target / "locked"
    locked.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    os.symlink(str(outside), str(locked / "escape"))
    os.chmod(locked, 0o111)
    try:
        rc = _run(target, report=outside / "r.txt")
        assert rc == 3
        assert not (outside / "r.txt").exists()
    finally:
        os.chmod(locked, 0o755)


def test_both_sides_unreadable_plain_files_still_block(vault_pair):
    """HIGH 回归: 两侧同名普通文件都读不动、内容其实不同时，不得判等且报 0。

    `_leaf_digest` 早先遇到 OSError 只返回一个标记字符串，调用方无从知道发生过
    读取失败——摘要相等、unreadable 为空、rc=0。那是假绿。
    """
    source, target = vault_pair
    (source / "CLAUDE.md").write_text("AAAA\n", encoding="utf-8")
    (target / "CLAUDE.md").write_text("BBBB\n", encoding="utf-8")
    os.chmod(source / "CLAUDE.md", 0o000)
    os.chmod(target / "CLAUDE.md", 0o000)
    try:
        result = _classify(target, source=source)
        assert result.unreadable != [], "读不动的普通文件必须被登记"
        assert result.exit_code != 0, "读不动就不能报 0"
    finally:
        os.chmod(source / "CLAUDE.md", 0o644)
        os.chmod(target / "CLAUDE.md", 0o644)


def test_short_write_is_detected(tmp_path):
    """MEDIUM 回归: `os.write` 会短写，必须循环写满才换目录项。

    用一个只肯接受 1 字节的假 fd 复现——早先单次 `os.write` 正常返回，
    于是发布了一份截断的报告。
    """
    calls = []
    real_write = os.write

    def stingy_write(fd, data):
        calls.append(len(data))
        return real_write(fd, data[:1])

    out = tmp_path / "r.txt"
    original = os.write
    os.write = stingy_write
    try:
        vv._write_report(out, "ABCDE")
    finally:
        os.write = original
    assert out.read_text(encoding="utf-8") == "ABCDE", "短写没有被补齐"
    assert len(calls) >= 5, f"应当循环写满，实际只调了 {len(calls)} 次"


@pytest.mark.parametrize("field", ["source", "role", "origin", "note"])
def test_unencodable_string_in_manifest_exits_2(tmp_path, vault_pair, manifest_data, field):
    """MEDIUM 回归: 孤立代理字符能过 json.loads，却在写报告时抛 UnicodeEncodeError。

    那时已经过了 ManifestError 的捕获面，拿不到承诺的 rc=2，还会留下临时文件。
    """
    _source, target = vault_pair
    if field == "source":
        manifest_data["source"] = "\ud800"
    else:
        manifest_data["items"][0][field] = "\ud800"
    bad = tmp_path / "surrogate.json"
    bad.write_text(json.dumps(manifest_data), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    assert vv.main(["--vault", str(target), "--manifest", str(bad), "--report", str(out / "r.txt")]) == 3
    assert list(out.iterdir()) == [], "落点目录留下了临时文件"


@pytest.mark.parametrize("dot", [".", "./", ".//"])
def test_extra_scan_dot_is_normalized_to_root(tmp_path, vault_pair, manifest_data, dot):
    """MEDIUM 回归: `dir="."` 拼接出 `./a`，与 declared_paths 里的 `a` 对不上 → 误报 extra。"""
    _source, target = vault_pair
    manifest_data["extra_scan"] = [{"dir": dot, "match": "*.md"}]
    m = tmp_path / "dot.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(m))
    assert result.extra == [], f"dir={dot!r} 把已声明的条目误报成了 extra"


def test_dangling_symlink_exclude_is_registered(vault_pair):
    """LOW 回归: `exists()` 对悬空软链是 False，但那个目录项确实在目标里。"""
    _source, target = vault_pair
    os.symlink(str(target / "nowhere"), str(target / "learning_events.jsonl"))
    os.symlink(str(target / "nowhere2"), str(target / ".obsidian" / "workspace.json"))
    result = _classify(target)
    got = [f.path for f in result.intentionally_excluded]
    assert "learning_events.jsonl" in got
    assert ".obsidian/workspace.json" in got
    assert result.extra == [], "悬空的 workspace.json 不该落到 extra"


def test_skeleton_content_excludes_are_pinned(vault_pair):
    """LOW 回归: `raw/**` 与 `templates/**` 删掉后曾仍然全绿——现在钉住它们。

    骨架 mkdir 循环对**全部**骨架目录一视同仁，清单必须逐个声明「内容不复制」。
    循环行按内容锚（`_sh_line`）—— 行号在本卡内漂过三次。
    """
    _source, target = vault_pair
    (target / "raw" / "lecture.pdf").write_text("x", encoding="utf-8")
    (target / "templates" / "daily.md").write_text("y", encoding="utf-8")
    result = _classify(target)
    got = [f.path for f in result.intentionally_excluded]
    assert "raw/**" in got, "raw 下的遗留内容必须被登记为「故意不复制」"
    assert "templates/**" in got
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mkdir_origin = f"install-vault.sh:{_sh_line(SKELETON_LOOP_ANCHOR)}"
    by_origin = [i["path"] for i in data["items"] if i["origin"] == mkdir_origin]
    # CARD-G2-7a Codex r1 M2: wiki 两件随 skeleton 一起补「内容不复制」(Codex round-1 MEDIUM)
    assert sorted(by_origin) == ["raw/**", "templates/**", "wiki/canvases/**", "wiki/concepts/**"]


def test_bracket_exclude_declaration_works_end_to_end(tmp_path, vault_pair, manifest_data):
    """LOW 回归: 之前那条方括号测试用的规则是 `outputs/**`，没有真正含 `[` 的声明。

    这里放一条**真的带方括号**的 exclude，验证分类与负例都对。
    """
    _source, target = vault_pair
    manifest_data["items"].append(
        {"path": "outputs/[draft].json", "role": "build-artifact", "action": "exclude", "origin": "test-only"}
    )
    m = tmp_path / "bracket.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    (target / "outputs" / "[draft].json").write_text("{}", encoding="utf-8")
    (target / "outputs" / "d.json").write_text("{}", encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(m))
    got = [f.path for f in result.intentionally_excluded]
    assert "outputs/[draft].json" in got, "字面方括号声明应当精确命中"
    # 负例：它不该被当成字符类而匹配到 outputs/d.json
    hits = vv.ExcludeMatcher(vv.load_manifest(m).exclude_items).hits_for(
        target,
        next(i for i in vv.load_manifest(m).items if i.path == "outputs/[draft].json"),
    )
    assert hits == ["outputs/[draft].json"]


def test_unreadable_leaf_inside_directory_is_registered(vault_pair):
    """目录**内部**的叶子读不动时也要登记 —— 与顶层文件那条走的是不同分支。

    `_digest` 有两处登记：顶层(被比对的 copy 项本身是文件)和循环内(目录里的子孙)。
    只测其中一处，另一处拆掉也不会红。
    """
    source, target = vault_pair
    for root in (source, target):
        leaf = root / ".claude" / "hooks" / "leaf.txt"
        leaf.write_text("same\n", encoding="utf-8")
    os.chmod(source / ".claude" / "hooks" / "leaf.txt", 0o000)
    os.chmod(target / ".claude" / "hooks" / "leaf.txt", 0o000)
    try:
        result = _classify(target, source=source)
        assert any("leaf.txt" in f.path for f in result.unreadable), "目录内读不动的叶子必须被登记"
        assert result.exit_code != 0
    finally:
        os.chmod(source / ".claude" / "hooks" / "leaf.txt", 0o644)
        os.chmod(target / ".claude" / "hooks" / "leaf.txt", 0o644)


# ── CARD-RV-G2-6: rc 四档 / extra_allow / hotkeys↔命令 id ────────────

PLUGIN_ID_PREFIX = "canvas-learning-system:"
PLUGIN_MAIN_TS = REPO_ROOT / "frontend" / "obsidian-plugin" / "src" / "main.ts"
TREE_HOTKEYS = REPO_ROOT / "canvas-vault" / ".obsidian" / "hotkeys.json"


def _command_ids_from_main_ts() -> set[str]:
    """真相源: main.ts 里 **addCommand 注册点**的 id 字面量。只读 frontend/, 不构建。

    正则绑到 `addCommand({ id: "…"` 而不是任意 `id: "canvas:…"` —— 后者把注释、
    别处的常量、乃至 `console.log` 里的同形字符串一并算进来, 数量锚就只证明了
    「文本里有 10 个这样的串」, 证明不了「真的注册了 10 个命令」(Codex r1 MEDIUM)。
    如实声明其上限: 这仍是文本提取, 不是 TS 语义分析。
    """
    text = PLUGIN_MAIN_TS.read_text(encoding="utf-8")
    return set(re.findall(r'addCommand\(\{\s*id:\s*"(canvas:[a-z0-9-]+)"', text))


def _write_plugin_main_js(vault: Path, ids) -> Path:
    """在合成 vault 里造一份只含指定 id 字面量的 main.js (构建产物的最小替身)。"""
    plugin_dir = vault / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    main_js = plugin_dir / "main.js"
    main_js.write_text("".join('this.addCommand({id:"%s"});' % i for i in sorted(ids)) + "\n", encoding="utf-8")
    return main_js


def _write_hotkeys(vault: Path, keys) -> None:
    (vault / ".obsidian" / "hotkeys.json").write_text(
        json.dumps({k: [{"modifiers": ["Mod"], "key": "X"}] for k in keys}), encoding="utf-8"
    )


def test_exit_codes_are_four_tiered():
    """rc 四档常量门 —— 0 ok / 1 missing / 2 mismatch / 3 usage。

    数字写死: 调用方 (deploy-vault.sh, U3-C) 靠它区分「缺东西」与「多东西」。
    """
    assert (vv.EXIT_OK, vv.EXIT_MISSING, vv.EXIT_MISMATCH, vv.EXIT_USAGE) == (0, 1, 2, 3)


def test_missing_and_mismatch_together_take_mismatch(vault_pair):
    """同时有 missing 与 mismatch 时取 2 —— 且 missing 单独出现仍是 1 (没被吞)。"""
    _source, target = vault_pair
    (target / ".obsidian" / "hotkeys.json").unlink()
    only_missing = _classify(target)
    assert [f.path for f in only_missing.missing] == [".obsidian/hotkeys.json"]
    assert only_missing.exit_code == vv.EXIT_MISSING == 1
    (target / ".claude" / "probe-extra").mkdir(parents=True)  # cache 已进 extra_allow, 换名
    both = _classify(target)
    assert both.missing and both.extra
    assert both.exit_code == vv.EXIT_MISMATCH == 2


def test_extra_allow_moves_entry_out_of_extra(tmp_path, vault_pair, manifest_data):
    """(g)① extra_allow 放行的项进 allowed-extra 且不计 rc; 未放行仍是 extra(2)。"""
    # ⚠️ 不能再用 graph.json —— CARD-G2-7a 已把它写进仓内 extra_allow, 「未放行」那一半
    # 会拿不到 extra。用一个**不在**白名单里的名字, 翻转的两端才都成立。
    probe = ".obsidian/probe-extra.json"
    _source, target = vault_pair
    (target / ".obsidian" / "probe-extra.json").write_text("{}", encoding="utf-8")

    base = json.loads(json.dumps(manifest_data))
    base["extra_allow"] = [e for e in base.get("extra_allow", []) if e != probe]
    base_path = tmp_path / "base.json"
    base_path.write_text(json.dumps(base), encoding="utf-8")
    before = vv.verify(target, vv.load_manifest(base_path))
    assert [f.path for f in before.extra] == [probe], "未放行时必须是 extra"
    assert before.exit_code == vv.EXIT_MISMATCH == 2
    assert not before.allowed_extra

    allowed = json.loads(json.dumps(manifest_data))
    allowed["extra_allow"] = list(manifest_data.get("extra_allow", [])) + [probe]
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps(allowed), encoding="utf-8")
    manifest = vv.load_manifest(allow)
    after = vv.verify(target, manifest)
    assert after.extra == [], "放行后不得再计入 extra"
    # 精确集合(Codex round-1 LOW): 夹具只造了 probe 一个额外文件, allowed-extra 应恰为它 ——
    # 成员包含式断言会容忍多出非预期条目。
    assert [f.path for f in after.allowed_extra] == [probe]
    assert after.exit_code == vv.EXIT_OK == 0, "allowed-extra 不计退出码"
    assert "## allowed-extra" in vv.render(after, manifest)


def test_extra_allow_glob_is_supported(tmp_path, vault_pair, manifest_data):
    """extra_allow 支持 *? glob —— 与 item.path 同一套 _pattern_to_regex 口径。"""
    _source, target = vault_pair
    (target / ".claude" / "cache").mkdir(parents=True)
    manifest_data["extra_allow"] = [".claude/cach?"]
    m = tmp_path / "glob.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(m))
    assert [f.path for f in result.allowed_extra] == [".claude/cache"]
    assert result.exit_code == vv.EXIT_OK


def test_manifest_ships_the_five_ruled_extra_allow_entries():
    """CARD-G2-7a 裁定：live 那 5 个 extra 逐字进 extra_allow（U3-A 时初值是 []）。

    ⛔ **逐字列出，不得用 glob**：`.obsidian/plugins/*` 这类会与已声明的插件项重叠，
    U3-A 的重叠检查会直接 `ManifestError`（那是设计，不是 bug）。
    """
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert sorted(data["extra_allow"]) == sorted(
        [
            ".claude/cache",
            ".obsidian/graph.json",
            ".obsidian/types.json",
            ".obsidian/plugins/excalibrain",
            ".obsidian/plugins/obsidian-excalidraw-plugin",
        ]
    ), f"extra_allow 与裁定表不符: {data['extra_allow']}"
    assert not any("*" in e for e in data["extra_allow"]), "不得用 glob（会与 declared 重叠）"
    assert "extra_allow" in data["description"], "description 须说明 extra_allow 语义"
    assert "optional" in data["description"], "description 须说明 optional 语义"


@pytest.mark.parametrize("bad", ["not-a-list", {"a": 1}, 5, None])
def test_extra_allow_must_be_a_list(tmp_path, manifest_data, bad):
    manifest_data["extra_allow"] = bad
    m = tmp_path / "bad.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "extra_allow" in str(exc.value)


@pytest.mark.parametrize(
    "bad, fragment",
    [
        ("/etc/passwd", "绝对路径"),
        ("../outside", ".."),
        ("", "不得为空"),
    ],
)
def test_extra_allow_path_field_uses_same_checks_as_item_path(tmp_path, manifest_data, bad, fragment):
    """同口径: 相对 / 无 .. / 非空 —— 与 item 的 path 共用 _check_relative_segment。"""
    manifest_data["extra_allow"] = [bad]
    m = tmp_path / "bad.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert fragment in str(exc.value)


def test_extra_allow_rejects_duplicates(tmp_path, manifest_data):
    manifest_data["extra_allow"] = [".claude/cache", ".claude/cache"]
    m = tmp_path / "dup.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "重复" in str(exc.value)


@pytest.mark.parametrize(
    "bad, why",
    [
        (".obsidian/hotkeys.json", "与 declared 精确重叠"),
        ("outputs/**", "与 exclude 模式精确重叠"),
        (".obsidian/*.json", "allow 的 glob 覆盖了已声明的 .obsidian/app.json"),
        (".claude/**/__pycache__", "与 exclude 的 glob 精确重叠"),
        # ↓ 反向覆盖: allow 是字面量, 被 exclude 的 glob 罩住。缺了这一条,
        #   删掉实现里两处 `_pattern_covers(path, allow)` 上面四条仍全绿(Codex r1 LOW 实证)。
        ("outputs/cache.md", "字面 allow 被 exclude 的 glob outputs/** 罩住（反向覆盖）"),
        (".claude/hooks/pending_archives9.jsonl", "字面 allow 被 exclude 的 glob 罩住（反向覆盖）"),
    ],
)
def test_extra_allow_overlapping_declared_or_exclude_is_refused(tmp_path, manifest_data, bad, why):
    """(g)⑥ 同一路径不得有两种语义 —— 重叠即 ManifestError, CLI 侧走用法错档 3。"""
    manifest_data["extra_allow"] = [bad]
    m = tmp_path / "overlap.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "重叠" in str(exc.value), why
    assert vv.main(["--vault", str(tmp_path), "--manifest", str(m)]) == 3


def test_plugin_command_ids_are_exactly_ten_and_tree_hotkeys_are_a_subset():
    """测试层真相源门: main.ts 恰 10 个命令 id, 树内 hotkeys 全是其中之一。

    10 写死是**防解析退化成空集**的验伪锚 —— 正则一旦失配, `∅ ⊆ 任何集合` 会假绿,
    所以下面还断言了 CLS 前缀的 hotkey 集合非空。
    """
    ids = _command_ids_from_main_ts()
    assert len(ids) == 10, f"main.ts 的命令 id 数与勘探不符: {sorted(ids)}"
    keys = json.loads(TREE_HOTKEYS.read_text(encoding="utf-8"))
    bound = {k[len(PLUGIN_ID_PREFIX) :] for k in keys if k.startswith(PLUGIN_ID_PREFIX)}
    assert bound, "树内 hotkeys 的 CLS 前缀项不得为空 (否则子集断言恒真)"
    assert bound <= ids, f"树内 hotkeys 绑了不存在的命令: {sorted(bound - ids)}"


def test_hotkey_orphan_is_counted_as_mismatch(vault_pair):
    """(g)⑦ 假 id → hotkey-orphan 1 且 rc=2。"""
    _source, target = vault_pair
    _write_plugin_main_js(target, _command_ids_from_main_ts())
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:does-not-exist"])
    result = _classify(target)
    assert [f.path for f in result.hotkey_orphan] == [PLUGIN_ID_PREFIX + "canvas:does-not-exist"]
    # 一次只打一类: 其余阻断桶必须为空, 否则 rc=2 会被别的差异喂饱
    assert (result.missing, result.extra, result.content_drift, result.unreadable) == ([], [], [], [])
    assert result.exit_code == vv.EXIT_MISMATCH == 2
    assert "## hotkey-orphan" in vv.render(result, vv.load_manifest(MANIFEST))


def test_hotkey_real_id_is_clean(vault_pair):
    """(g)⑧ 同一夹具换成真 id → orphan 0, rc 0 (对照组, 证 ⑦ 不是恒红)。"""
    _source, target = vault_pair
    ids = _command_ids_from_main_ts()
    _write_plugin_main_js(target, ids)
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + sorted(ids)[0]])
    result = _classify(target)
    assert result.hotkey_orphan == []
    assert result.exit_code == vv.EXIT_OK == 0


def test_hotkeys_not_evaluated_when_main_js_missing(vault_pair):
    """(g)⑨ main.js 缺 → 报告明写 not evaluated, 不计 rc, 不静默。"""
    _source, target = vault_pair
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:does-not-exist"])
    assert not (target / ".obsidian" / "plugins" / "canvas-learning-system" / "main.js").exists()
    result = _classify(target)
    assert result.hotkey_orphan == []
    assert result.exit_code == vv.EXIT_OK == 0
    # ⚠️ 判据必须锁到 hotkeys 那一行: 整份报告的 content-drift 段在无 --source 时
    # 也写着 "not evaluated", 拿全文做包含判断会借用它 —— 把 hotkeys 提示删光也照样绿。
    text = vv.render(result, vv.load_manifest(MANIFEST))
    line = next(l for l in text.splitlines() if l.startswith("hotkeys "))
    assert "not evaluated" in line and "main.js" in line, f"hotkeys 行未明写未评估: {line}"


def test_foreign_plugin_hotkeys_are_ignored(vault_pair):
    """别的插件的快捷键不归本校验器管 —— 无 CLS 前缀的键一律忽略。"""
    _source, target = vault_pair
    _write_plugin_main_js(target, _command_ids_from_main_ts())
    _write_hotkeys(target, ["dataview:dataview-force-refresh-views"])
    result = _classify(target)
    assert result.hotkey_orphan == []
    assert result.exit_code == vv.EXIT_OK


def test_invalid_hotkeys_json_is_unreadable(vault_pair):
    """hotkeys.json 非法 JSON → unreadable (计入阻断), 不是静默跳过。"""
    _source, target = vault_pair
    _write_plugin_main_js(target, _command_ids_from_main_ts())
    (target / ".obsidian" / "hotkeys.json").write_text("{not json", encoding="utf-8")
    result = _classify(target)
    assert [f.path for f in result.unreadable] == [".obsidian/hotkeys.json"]
    # 一次只打一类
    assert (result.missing, result.extra, result.content_drift, result.hotkey_orphan) == ([], [], [], [])
    assert result.exit_code == vv.EXIT_MISMATCH == 2


def test_install_sh_skills_check_counts_skill_md_dirs(tmp_path):
    """(f) :117 的判据必须数「含 SKILL.md 的目录」, 不是数目录条目。

    树内 .claude/skills 有 11 个目录但只有 9 个含 SKILL.md —— 旧 `ls | wc -l`
    对「有目录没 SKILL.md」的半成品 skill 失明。
    """
    # 按**内容**定位, 不按行号索引: U3-A 写这条门时用的是 splitlines()[116],
    # CARD-G2-7a 在它上面加了两个参数与用法注释, 行号就指到别处去了 (门变红且理由离谱)。
    # 硬编码行号的门, 寿命只到下一次有人在它上面插一行为止。
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    hits = [ln for ln in lines if ln.startswith("check ") and "skills" in ln]
    assert len(hits) == 1, f"skills 自检行应当恰好一条, 实得 {len(hits)}: {hits}"
    line = hits[0]
    # 判据只看 check 的第二个参数(单引号包住的 eval 体), 不看标签 ——
    # 标签里的 "skills " 本身就含子串 "ls ", 拿整行做黑名单会因无关文本假红。
    assert line.count("'") == 2, f":117 不是「check \"标签\" '判据'」的形态: {line}"
    body = line.split("'", 1)[1].rsplit("'", 1)[0]
    assert "find " in body and "-name SKILL.md" in body, f":117 仍是旧判据: {body}"
    assert "-mindepth 2 -maxdepth 2" in body, "必须只数一级子目录下的 SKILL.md"
    assert "$(ls " not in body, "计数命令不得再是 ls | wc -l (那会把无 SKILL.md 的半成品目录算进去)"
    assert "-ge 8" in body, "阈值 8 不改 (决策页 §五「≥9」是 preflight 口径, 归 U3-C)"
    assert "-type f" in body, "SKILL.md 必须是普通文件 —— 同名目录不算一个 skill (Codex r1 MEDIUM)"

    # 行为断言: 只查命令字符串挡不住「给判据加 `|| true`」这类退化, 必须真跑一次。
    # 抽 :113(check 函数定义) + :117 两行喂给 bash, 不跑整个脚本(它会建目录)。
    check_def = [ln for ln in lines if ln.startswith("check() {")]
    assert len(check_def) == 1, f"check() 定义应当恰好一条, 实得 {len(check_def)}"
    two_lines = "\n".join(check_def + [line])

    def _probe(root: Path) -> str:
        return subprocess.run(
            ["bash", "-c", two_lines],
            env={**os.environ, "TARGET": str(root)},
            capture_output=True,
            text=True,
        ).stdout

    good = tmp_path / "good"
    for i in range(9):
        (good / ".claude" / "skills" / f"s{i}").mkdir(parents=True)
        (good / ".claude" / "skills" / f"s{i}" / "SKILL.md").write_text("# s", encoding="utf-8")
    assert "✅" in _probe(good), "9 个含 SKILL.md 的 skill 应当通过"

    # 负控 A —— 只隔离 `-type f`: 7 个合格文件 + 1 个「SKILL.md 是目录」。
    # 不区分类型时数到 8 会通过, 加上 -type f 是 7 而拦下 ⇒ 这条样例单独承重。
    # (早先写成「6 文件 + 1 scripts + 1 目录」不隔离: 去掉 -type f 也才 7, 照样红,
    #  于是那条负控其实是被别的原因打红的 —— Codex round-2 LOW 实证。)
    dir_entry = tmp_path / "dir-entry"
    for i in range(8):
        (dir_entry / ".claude" / "skills" / f"s{i}").mkdir(parents=True)
        if i < 7:
            (dir_entry / ".claude" / "skills" / f"s{i}" / "SKILL.md").write_text("# s", encoding="utf-8")
    (dir_entry / ".claude" / "skills" / "s7" / "SKILL.md").mkdir()
    assert len(list((dir_entry / ".claude" / "skills").glob("*/SKILL.md"))) == 8, (
        "负控前提: 不区分类型时恰好数到 8, 否则这条样例隔离不出 -type f"
    )
    assert "❌" in _probe(dir_entry), "SKILL.md 是目录的条目不得计为一个 skill"

    # 负控 B —— 只隔离「数目录条目 vs 数入口文件」: 8 个目录, 其中一个只有 scripts/
    shy = tmp_path / "shy"
    for i in range(8):
        (shy / ".claude" / "skills" / f"s{i}").mkdir(parents=True)
        if i < 7:
            (shy / ".claude" / "skills" / f"s{i}" / "SKILL.md").write_text("# s", encoding="utf-8")
    (shy / ".claude" / "skills" / "s7" / "scripts").mkdir()
    assert "❌" in _probe(shy), "无入口文件的半成品 skill 不得计为完成"


# ── CARD-G2-7a: manifest v2（E-4 模板源 = harness 树 + optional 语义 + 裁定表落地）──
#   新增/改动的门:
#     optional 四门(缺失不计 rc / 在位仍比 drift / 在位不报 extra / 类型校验)
#     yaml 2.1 两门(生成器六键 + 后端单键兼容)
#     裁定表落地三门(五项 allow / 四条改动 / 后端-脚本骨架不漂移)
#     key 自检反向门 | 树 HEAD 自洽门(常驻 E-4)
#     generate 项不参与父目录摘要门
#   钉点迁移: 数组计数 6/8/6/5/2 → 8/6/9/4/3 (合计 27→30);
#     MANIFEST_BLOCK (63,67)→(73,77); match 28→31; declared 28→35;
#     origin 全量按行号重测(:68→:78, :84→:94, :86→:96, :103-109→:116-130)


# ── CARD-RV-G2-6 round-2 整改的门（Codex round-1 结论）────────────────


def test_copy_item_missing_on_source_is_not_reported_as_match(vault_pair):
    """HIGH 回归: 给了 --source 而模板源没有这一项时, 目标那一项**不得**记 match。

    match 读起来就是「核对过, 一致」—— 而这一项根本没比过。改记 unreadable
    (「看不见不等于一致」的同一条纪律), 计入阻断。
    """
    source, target = vault_pair
    (source / "Dashboard.md").unlink()  # 模板源没有, 目标有
    result = _classify(target, source=source)
    assert "Dashboard.md" not in [f.path for f in result.match], "未比较的项不得记 match"
    assert [f.path for f in result.unreadable] == ["Dashboard.md"]
    assert "模板源没有这一项" in result.unreadable[0].detail
    assert (result.missing, result.extra, result.content_drift) == ([], [], [])
    assert result.exit_code == vv.EXIT_MISMATCH == 2


def test_unreadable_dir_in_exclude_scan_surface_is_registered(vault_pair):
    """HIGH 回归 (= UAT-CARD-G2-6「未证明」#25): exclude 覆盖面读不动时不得静默跳过。

    `outputs/**` 的静态前缀是 `outputs`; 把它设成不可列目录, 旧实现只是跳过,
    报告照样 0 —— 「一个读不进去的目录里藏着 exclude 项」完全看不见。
    """
    _source, target = vault_pair
    locked = target / "outputs"
    (locked / "leftover.bin").write_text("x", encoding="utf-8")
    os.chmod(locked, 0o111)  # 可按名访问, 不可列目录
    try:
        result = _classify(target)
        assert any(f.path == "outputs" for f in result.unreadable), (
            f"exclude 覆盖面读不动必须登记, 实得 {[f.path for f in result.unreadable]}"
        )
        assert "exclude 覆盖面读不进去" in next(f for f in result.unreadable if f.path == "outputs").detail
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(locked, 0o755)


@pytest.mark.parametrize(
    "body, quote",
    [
        ('this.addCommand({id:"canvas:open-dashboard"});', "双引号"),
        ("this.addCommand({id:'canvas:open-dashboard'});", "单引号"),
        ("this.addCommand({id:`canvas:open-dashboard`});", "反引号"),
    ],
)
def test_command_id_literals_accept_every_quote_style(vault_pair, body, quote):
    """MEDIUM 回归: 只认双引号时, 单引号产物会让命令集变空 ⇒ **真实绑定全被误报 orphan**。

    打包器的引号风格不是稳定契约; 误拦一个正确部署的 vault 比漏放更难排查。
    """
    _source, target = vault_pair
    plugin_dir = target / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "main.js").write_text(body, encoding="utf-8")
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:open-dashboard"])
    result = _classify(target)
    assert result.hotkey_orphan == [], f"{quote}注册的命令被误判成 orphan"
    assert result.exit_code == vv.EXIT_OK == 0


def test_zero_command_ids_is_reported_as_unreadable_not_a_wall_of_orphans(vault_pair):
    """MEDIUM 回归: 产物里一个命令 id 都没解析出来时, 不得把每条绑定报成 orphan。

    阻断是对的, 但理由必须是「没法核对」而不是「这些命令不存在」——
    N 条**说错原因**的结论会把人引到错误的排查方向。
    """
    _source, target = vault_pair
    plugin_dir = target / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "main.js").write_text("/* 产物格式变了, 没有任何命令 id 字面量 */", encoding="utf-8")
    _write_hotkeys(target, [PLUGIN_ID_PREFIX + "canvas:open-dashboard", PLUGIN_ID_PREFIX + "canvas:open-node-chat"])
    result = _classify(target)
    assert result.hotkey_orphan == [], "不得报成 orphan"
    assert [f.path for f in result.unreadable] == [".obsidian/plugins/canvas-learning-system/main.js"]
    assert "无法核对 2 条快捷键绑定" in result.unreadable[0].detail
    assert result.exit_code == vv.EXIT_MISMATCH == 2
    line = next(ln for ln in vv.render(result, vv.load_manifest(MANIFEST)).splitlines() if ln.startswith("hotkeys "))
    assert "0 个命令 id" in line


def test_unencodable_hotkey_key_does_not_escape_the_exit_code(tmp_path, vault_pair):
    """MEDIUM 回归: vault 来源的不可编码字符不得让 UnicodeEncodeError 逃出退出码契约。

    JSON 里的 `"\\ud800"` 被 json.loads 解成孤立代理字符, 进了报告文本后
    `text.encode("utf-8")` 会抛 —— 而那个异常**不在** ReportWriteError 的捕获面里
    (那里只捕 OSError), 于是解释器以 1 退出, 被误读成「只有 missing」。
    round-3 已为 manifest 来源修过同一形态, 本卡新开的 vault 输入面把它重开了。
    """
    _source, target = vault_pair
    plugin_dir = target / ".obsidian" / "plugins" / "canvas-learning-system"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "main.js").write_text('addCommand({id:"canvas:open-dashboard"});', encoding="utf-8")
    (target / ".obsidian" / "hotkeys.json").write_text(
        '{"canvas-learning-system:canvas:\\ud800": [{"modifiers":["Mod"],"key":"X"}]}',
        encoding="utf-8",
        errors="surrogatepass",
    )
    out = tmp_path / "out"
    out.mkdir()
    report_path = out / "r.txt"
    rc = vv.main(["--vault", str(target), "--manifest", str(MANIFEST), "--report", str(report_path)])
    assert rc == vv.EXIT_MISMATCH == 2, "必须给出承诺的退出码, 而不是让异常逃逸"
    assert report_path.exists(), "报告必须落得下去"
    text = report_path.read_text(encoding="utf-8")
    assert "\\ud800" in text, "不可编码字符应转义成可见形式而不是丢失"
    assert sorted(p.name for p in out.iterdir()) == ["r.txt"], "不得留下临时文件"


def test_argparse_error_also_uses_the_usage_exit_code(vault_pair, capsys):
    """MEDIUM 回归: argparse 默认用 rc=2 退出 —— 而 2 在四档语义里是 mismatch。

    「命令行没写对」被调用方读成「vault 有多余文件」是最坏的一种混淆。
    """
    with pytest.raises(SystemExit) as exc:
        vv.main(["--vault"])  # 缺参数值
    assert exc.value.code == vv.EXIT_USAGE == 3
    assert "参数错误" in capsys.readouterr().err


def test_declared_paths_has_a_single_source_of_truth():
    """`Manifest.declared_paths` 与 load_manifest 的重叠检查必须共用同一个口径。

    各写一份就会漂: 将来给 declared 加一类 action 而只改一处, extra_allow 就能
    放行一条本该被管住的路径, 而且没有任何门会红。
    """
    manifest = vv.load_manifest(MANIFEST)
    assert vv._declared_paths(manifest.items) == manifest.declared_paths
    # 35 而不是 30: declared 是 copy+skeleton+**generate**, 比集合等价门那 30 项多
    # 5 条 generate。两个数字各有出处, 不得互抄 —— 抄错正是本条的来历。
    assert len(manifest.declared_paths) == 35
    assert manifest.declared_paths - {
        i["path"]
        for i in json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
        if i["action"] in ("copy", "skeleton")
    } == {
        ".canvas-config.yaml",
        ".claude/settings.local.json",
        ".obsidian/cls-internal-key.txt",
        ".obsidian/plugins/canvas-learning-system/data.json",
        ".obsidian/plugins/templater-obsidian/data.json",
    }


def test_extra_allow_overlap_check_uses_the_same_declared_set_as_the_property(tmp_path, manifest_data):
    """LOW 回归: 「单一真相源」不能只比 helper 与调用 helper 的 property —— 那是自证。

    要证的是**加载侧**也走同一口径。判据取 `generate` 那一类: 它在 declared 里、
    却不在集合等价门那 27 项里。加载侧若自己另写一份而漏掉 generate,
    `extra_allow=[".canvas-config.yaml"]` 就会被错误接受 —— 本门直接拦这个行为。
    """
    manifest_data["extra_allow"] = [".canvas-config.yaml"]  # action=generate 的那一项
    m = tmp_path / "gen-overlap.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "重叠" in str(exc.value) and ".canvas-config.yaml" in str(exc.value)


def test_unreachable_exclude_scan_root_is_registered_not_treated_as_absent(tmp_path, vault_pair, manifest_data):
    """HIGH 回归: `Path.exists()` 把「不存在」和「问不出来」都返回 False。

    一个因祖先目录缺搜索权限而 stat 不到的 exclude 目标, 会在**进入** `_walk()` 的
    错误透传链之前就提前返回空 —— 报告照样 0。glob 分支与精确分支两个入口都要盖到。
    """
    _source, target = vault_pair
    guard = target / "outputs"
    (guard / "locked").mkdir(parents=True)
    (guard / "locked" / "x.jsonl").write_text("x", encoding="utf-8")
    manifest_data["items"].append(
        {"path": "outputs/locked/**", "role": "test", "action": "exclude", "origin": "test-only"}
    )
    manifest_data["items"].append(
        {"path": "outputs/locked/x.jsonl", "role": "test", "action": "exclude", "origin": "test-only"}
    )
    m = tmp_path / "unreachable.json"
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    os.chmod(guard, 0o000)  # 祖先无搜索权限 ⇒ 子项 lstat 不到
    try:
        result = vv.verify(target, vv.load_manifest(m))
        paths = [f.path for f in result.unreadable]
        assert "outputs/locked" in paths, f"glob 分支的扫描根问不出来时必须登记, 实得 {paths}"
        assert "outputs/locked/x.jsonl" in paths, f"精确分支同样要登记, 实得 {paths}"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(guard, 0o755)


def test_exclude_scan_failure_is_registered_exactly_once(vault_pair):
    """LOW 回归: 同一个读不动的位置被多条 exclude 前缀扫到时**只登记一次**。

    `any()` / `next()` 这类断言允许重复登记 —— 要锁去重就得数次数。
    `.claude/hooks` 同时落在 `.claude/**/__pycache__` 与
    `.claude/hooks/pending_archives*.jsonl` 两条 exclude 的扫描面里。
    """
    _source, target = vault_pair
    locked = target / ".claude" / "hooks"
    (locked / "x.txt").write_text("x", encoding="utf-8")
    os.chmod(locked, 0o111)  # 可按名访问, 不可列目录
    try:
        manifest = vv.load_manifest(MANIFEST)
        # 前提: 确实有**两条** exclude 的扫描面覆盖 .claude/hooks —— 否则「只登记一次」
        # 也可能是「只有一个来源到达」, 少扫一个会伪装成去重成功(Codex round-3 LOW)。
        reaching = [
            i.path for i in manifest.exclude_items if vv._static_prefix(i.path) in ("", ".claude", ".claude/hooks")
        ]
        assert len(reaching) >= 2, f"前提不成立: 覆盖 .claude/hooks 的 exclude 只有 {reaching}"
        # 前提二: **每一条**单独跑都真的登记到这个位置 —— 只数配置条数不够,
        # 少扫一路会伪装成「去重成功」(Codex round-4 LOW: 把某一路的早退提前即可)。
        matcher = vv.ExcludeMatcher(manifest.exclude_items)
        for rule_path in reaching:
            rule = next(i for i in manifest.exclude_items if i.path == rule_path)
            solo: list[str] = []
            matcher.hits_for(target, rule, solo)
            assert ".claude/hooks" in solo, f"exclude {rule_path!r} 这一路没到达该位置, 实得 {solo}"
        result = vv.verify(target, manifest)
        hits = [f.path for f in result.unreadable if f.path == ".claude/hooks"]
        assert len(hits) == 1, f"同一位置必须恰好登记一次, 实得 {len(hits)} 次"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(locked, 0o755)


def test_both_sides_unreadable_is_not_counted_as_match(vault_pair):
    """MEDIUM 回归: 两侧都读不动、摘要标记因此相等时, 该项**不得**同时计入 match。

    登记了 unreadable 却还把它算作「一致」, 等于在同一份报告里既说「没证明」又说「证明了」。
    """
    source, target = vault_pair
    for root in (source, target):
        (root / "Dashboard.md").chmod(0o000)
    try:
        result = _classify(target, source=source)
        assert "Dashboard.md" in [f.path for f in result.unreadable]
        assert "Dashboard.md" not in [f.path for f in result.match], "未证明一致的项不得记 match"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        for root in (source, target):
            (root / "Dashboard.md").chmod(0o644)


def test_symlink_target_with_undecodable_bytes_does_not_crash_the_digest(vault_pair):
    """MEDIUM 回归: 摘要阶段的编码也不得抛 —— `_printable()` 只守 render 出口, 守不到这里。

    软链目标是任意字节串, `os.readlink` 用 surrogateescape 解码; 严格 `encode("utf-8")`
    会抛 `UnicodeEncodeError`, 而它不在任何捕获面里 —— CLI 会以 1 退出, 被读成「只有 missing」。
    """
    source, target = vault_pair
    link = target / ".claude" / "skills" / "odd-link"
    os.symlink(b"bad\xff-target", os.fsencode(link))
    result = _classify(target, source=source)  # 不抛即为通过
    assert result.exit_code in (vv.EXIT_MISSING, vv.EXIT_MISMATCH)
    text = vv.render(result, vv.load_manifest(MANIFEST))
    text.encode("utf-8")  # 报告仍可编码


def test_tilde_expansion_failure_uses_the_usage_exit_code(vault_pair, capsys):
    """MEDIUM 回归: `~未知用户名` 让 `expanduser()` 抛 `RuntimeError` —— 归用法错档 3, 不是 1。"""
    _source, target = vault_pair
    bogus = "~cls-no-such-user-9c1f/x"
    # 四个调用点逐个覆盖 —— 只测 vault/manifest 时, 把 --report 恢复成直接
    # expanduser 也不会红(Codex round-3 LOW)。
    assert vv.main(["--vault", bogus]) == vv.EXIT_USAGE == 3
    assert "路径展开失败" in capsys.readouterr().err
    assert vv.main(["--vault", str(target), "--source", bogus]) == vv.EXIT_USAGE == 3
    assert vv.main(["--vault", str(target), "--manifest", bogus]) == vv.EXIT_USAGE == 3
    assert vv.main(["--vault", str(target), "--report", bogus]) == vv.EXIT_USAGE == 3


# ── CARD-RV-G2-6 round-4 整改的门（Codex round-3 结论）────────────────


def test_digest_is_injective_over_adversarial_leaves(tmp_path):
    """HIGH 回归: 摘要必须**单射** —— 判据是这个性质本身，不是某个函数名或某个编码器名。

    round-3 我选了 `backslashreplace`，理由写的是「摘要只需确定性」—— 确定性是必要条件
    不是充分条件。round-4 的第一版门写成「摘要函数里不许出现 backslashreplace」，
    那是**按名字**判：换成 `ignore` / `replace` 照样有损而门不红（Codex round-4 LOW）。
    这一版直接把一组两两不同、但历史上会被各种有损变换压到一起的叶子喂进真实摘要，
    断言产出**两两不同**。新的有损写法只要出现，这条门就会红。
    """
    kinds: dict[str, Path] = {}

    def _leaf(name: str) -> Path:
        d = tmp_path / name
        d.mkdir()
        return d

    # ① 软链目标: 尾斜杠 / 冗余分隔 / 非法字节 —— 前两类被 Path 规范化压平,
    #    第三类被 backslashreplace 与字面转义串压平。
    for name, target in [
        ("link_plain", b"payload"),
        ("link_slash", b"payload/"),
        ("link_dslash", b"x//y"),
        ("link_dot", b"x/./y"),
        ("link_rawbyte", b"bad\xff-target"),
        ("link_literal", b"bad\\udcff-target"),
    ]:
        d = _leaf(name)
        os.symlink(target, os.fsencode(d / "node"))
        kinds[name] = d

    # ② 非常规类型: FIFO 与 socket 原先都记成同一个 "?:unknown"
    fifo = _leaf("fifo")
    os.mkfifo(fifo / "node")
    kinds["fifo"] = fifo
    sock_dir = _leaf("sock")
    # AF_UNIX 的路径有长度上限(约 104 字节), pytest 的 tmp_path 常常超 —— 先 chdir
    # 再用裸名绑定, 免得这条门在别的机器上因为临时目录更深而变红。
    sock = socket.socket(socket.AF_UNIX)
    cwd = os.getcwd()
    try:
        os.chdir(sock_dir)
        sock.bind("node")
    finally:
        os.chdir(cwd)
        sock.close()
    kinds["sock"] = sock_dir

    # ③ 普通文件与目录作为对照
    reg = _leaf("regular")
    (reg / "node").write_text("payload", encoding="utf-8")
    kinds["regular"] = reg
    plain_dir = _leaf("dir")
    (plain_dir / "node").mkdir()
    kinds["dir"] = plain_dir

    digests = {name: vv._digest(d) for name, d in kinds.items()}
    collisions = [
        (a, b) for i, a in enumerate(sorted(digests)) for b in sorted(digests)[i + 1 :] if digests[a] == digests[b]
    ]
    assert collisions == [], f"这些本该不同的叶子给出了相同摘要: {collisions}"
    # 验伪锚: 这些夹具确实都造出来了(否则「空集两两不同」恒真)
    assert len(digests) == 10, f"夹具数与预期不符: {sorted(digests)}"


def test_two_different_symlink_targets_do_not_collide(tmp_path):
    """HIGH 回归（行为面）: 上一条钉性质，这一条钉后果 —— 两个不同软链目标不得判等。"""
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    os.symlink(b"bad\xff-target", os.fsencode(a / "link"))
    os.symlink(b"bad\\udcff-target", os.fsencode(b / "link"))
    assert vv._digest(a) != vv._digest(b), "不同的软链目标必须给出不同摘要"


def test_entry_state_maps_enotdir_to_absent(tmp_path):
    """MEDIUM 回归: `ENOTDIR` 是**确定的**否定答案，不是「问不出来」。

    `a` 是普通文件时，`a/b` 不可能存在 —— 归 unreadable 会让 exclude 被误阻断。
    """
    plain = tmp_path / "a"
    plain.write_text("x", encoding="utf-8")
    assert vv._entry_state(plain / "b") == "absent"
    assert vv._entry_state(tmp_path / "nope") == "absent"
    assert vv._entry_state(plain) == "present"


def test_unreadable_leaf_in_listable_but_unsearchable_dir_is_registered(tmp_path):
    """HIGH 回归: 目录可列名字但不可 stat 里面的条目（0444）时，叶子摘要不得落到 unknown。

    那几个类型谓词全都吞 OSError ⇒ 权限不足时**全部返回 False** ⇒ 走到 `"?:unknown"`
    且 `bad=False` ⇒ 两侧都这样就判等，unreadable 为空，退出码 0 = 假绿。
    """
    d = tmp_path / "d"
    d.mkdir()
    (d / "f.txt").write_text("AAA", encoding="utf-8")
    os.chmod(d, 0o444)
    try:
        digest, bad = vv._leaf_digest(d / "f.txt")
        assert bad is True, f"读不动的叶子必须回报 bad=True, 实得 ({digest!r}, {bad})"
        assert digest == "U:unreadable"
        collected: list[str] = []
        vv._digest(d, unreadable=collected)
        assert collected == ["f.txt"], f"目录摘要必须把它登记进 unreadable, 实得 {collected}"
    finally:
        os.chmod(d, 0o755)


def test_kind_ok_is_tri_state_when_it_cannot_query(tmp_path):
    """HIGH 回归: 问不出类型时返回 **None**（判不了），既不宣称满足、也不宣称不满足。

    两个方向都错过：
      - 原写法 `not (is_dir() and not is_symlink())` 在谓词被权限吞掉时**恒为 True**
        ⇒ 查不动的条目被当成 `nondir` 而误判成「故意不复制」= **漏报**；
      - round-4 改成一律 `False` ⇒ 丢了失败原因，且会把它从「故意不复制」翻成
        「清单外的 extra」= **误报**（Codex round-4 HIGH-3）。
    """
    guard = tmp_path / "g"
    guard.mkdir()
    (guard / "x").write_text("x", encoding="utf-8")
    os.chmod(guard, 0o000)
    try:
        target = guard / "x"
        for kind in ("dir", "file", "nondir", ""):
            item = vv.Item(path="x", role="t", action="exclude", kind=kind)
            assert vv._kind_ok(item, target) is None, f"kind={kind!r} 时应当是「判不了」而不是二值"
    finally:
        os.chmod(guard, 0o755)


def test_unqueryable_exclude_hit_is_registered_not_silently_dropped(tmp_path):
    """HIGH 回归（行为面）: 类型判不了的 exclude 命中要透传到 unreadable，不得静默丢弃。

    上一条钉 `_kind_ok` 的返回值，这一条钉**调用方真的接住了**它 ——
    round-4 那版一律返回 False，`hits_for` 拿到的就是「没命中」，什么都不会登记。
    """
    guard = tmp_path / "g"
    guard.mkdir()
    (guard / "x").write_text("x", encoding="utf-8")
    os.chmod(guard, 0o444)  # 可列名字, 不可 stat 里面的条目
    try:
        for pattern in ("g/*", "g/x"):  # glob 分支与精确分支各一
            item = vv.Item(path=pattern, role="t", action="exclude", kind="nondir")
            matcher = vv.ExcludeMatcher((item,))
            collected: list[str] = []
            hits = matcher.hits_for(tmp_path, item, collected)
            assert hits == [], f"{pattern}: 判不了的条目不得算作命中"
            assert collected, f"{pattern}: 判不了的位置必须登记, 实得 {collected}"
    finally:
        os.chmod(guard, 0o755)


def test_unqueryable_item_target_is_not_downgraded_to_missing(tmp_path, vault_pair, manifest_data):
    """HIGH 回归: item 目标「问不出来」不得降级成 missing（那会给 rc=1「只缺东西」）。"""
    _source, target = vault_pair
    guard = target / ".claude"
    os.chmod(guard, 0o000)
    try:
        result = _classify(target)
        assert not any(f.path.startswith(".claude/") for f in result.missing), (
            f"查询不到的项不得记 missing, 实得 {[f.path for f in result.missing]}"
        )
        assert any(f.path.startswith(".claude/") and "查询不到" in f.detail for f in result.unreadable)
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(guard, 0o755)


def test_unqueryable_extra_scan_root_is_registered(tmp_path, vault_pair):
    """HIGH 回归: extra 覆盖面的根问不出来时不得静默跳过 —— 「没扫」不等于「没有」。"""
    _source, target = vault_pair
    guard = target / ".obsidian"
    os.chmod(guard, 0o000)
    try:
        result = _classify(target)
        assert any(f.path in (".obsidian", ".obsidian/plugins") for f in result.unreadable), (
            f"覆盖面根查询不到必须登记, 实得 {[f.path for f in result.unreadable]}"
        )
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(guard, 0o755)


def test_content_drift_is_not_hidden_by_an_unreadable_sibling(vault_pair):
    """MEDIUM 回归: 同一 copy 项里既有读不动的叶子、又有真实内容差异时，两者都要报。

    round-3 我把「读不动就 continue」放在漂移判断**之前**，于是 content-drift 归 0 ——
    退出码仍是 2，但分类信息退化了，人会照着错误的方向去查。
    """
    source, target = vault_pair
    skills = "skills"
    (source / ".claude" / skills / "readable.txt").write_text("AAA", encoding="utf-8")
    (target / ".claude" / skills / "readable.txt").write_text("BBB", encoding="utf-8")
    for root in (source, target):
        blocked = root / ".claude" / skills / "blocked.txt"
        blocked.write_text("x", encoding="utf-8")
        blocked.chmod(0o000)
    try:
        result = _classify(target, source=source)
        assert ".claude/skills" in [f.path for f in result.content_drift], (
            f"可见的内容差异不得被读不动的兄弟条目遮掉, 实得 drift={[f.path for f in result.content_drift]}"
        )
        assert result.unreadable, "读不动的叶子仍要登记"
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        for root in (source, target):
            (root / ".claude" / skills / "blocked.txt").chmod(0o644)


def test_output_stream_failures_stay_inside_the_exit_contract(tmp_path):
    """MEDIUM 回归: 输出流写不出去也不得脱离四档 —— 而**断在哪一步取决于缓冲**。

    我第一版修复只包了最后的 `sys.stdout.flush()`，于是只覆盖了默认缓冲那条路径：
      - 默认缓冲 + 断管：小报告先进管道缓冲，退出期 flush 才炸（曾 rc=120）；
      - `-u` 无缓冲 + 断管：`sys.stdout.write(text)` **当场**抛，异常从 main() 逃出（曾 rc=1）；
      - stderr 断管 + 参数错误：同样逃出，且只 flush stdout 时仍会 120。
    所以这条门把**缓冲模式 × 哪个流**的组合都跑一遍，正控（不断管）一并断言。
    """
    lv = str(tmp_path)  # 只用临时目录，避免这条门依赖 live vault
    base = [sys.executable, "-B"]
    common = [str(VERIFIER), "--vault", lv, "--manifest", str(MANIFEST)]

    def _pipe(extra, argv, close_out=False, close_err=False):
        proc = subprocess.Popen([*base, *extra, *argv], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if close_out:
            proc.stdout.close()
        if close_err:
            proc.stderr.close()
        _out, err = proc.communicate()
        assert b"Traceback" not in (err or b""), "不得在解释器退出期留下未处理异常"
        return proc.returncode

    for extra in ([], ["-u"]):
        tag = "无缓冲" if extra else "默认缓冲"
        assert _pipe(extra, common, close_out=True) == vv.EXIT_USAGE == 3, f"{tag}: stdout 断管"
        assert _pipe(extra, [str(VERIFIER), "--bogus"], close_err=True) == vv.EXIT_USAGE, f"{tag}: stderr 断管"
        assert _pipe(extra, common, close_out=True, close_err=True) == vv.EXIT_USAGE, f"{tag}: 两流同断"

    # 正控: 不断管时退出码必须是**校验结果**本身，不能被上面的兜底吞成 3
    env = {**os.environ, "PYTHONIOENCODING": "ascii"}
    assert subprocess.run([*base, str(VERIFIER), "--help"], capture_output=True, env=env).returncode == 0
    assert subprocess.run([*base, str(VERIFIER), "--help"], capture_output=True).returncode == 0
    normal = subprocess.run([*base, *common], capture_output=True)
    assert normal.returncode in (vv.EXIT_OK, vv.EXIT_MISSING, vv.EXIT_MISMATCH), (
        f"正常路径不得落进用法错档, 实得 {normal.returncode}"
    )


def test_symlinked_scan_root_that_cannot_be_resolved_is_registered(tmp_path, vault_pair, manifest_data):
    """HIGH 回归: `lstat` 成功不代表跟随软链后查得到 —— 「问不出来」不得说成「不是目录」。"""
    _source, target = vault_pair
    hidden = tmp_path / "hidden"
    (hidden / "real").mkdir(parents=True)
    scan_root = target / ".claude"
    for child in scan_root.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    scan_root.rmdir()
    os.symlink(hidden / "real", scan_root)
    os.chmod(hidden, 0o000)
    try:
        assert vv._entry_state(scan_root) == "present", "前提: lstat 成功（软链本身在）"
        assert vv._resolved_kind(scan_root) == "unreadable", "前提: 跟随软链后查不到"
        result = _classify(target)
        assert any(f.path == ".claude" for f in result.unreadable), (
            f"覆盖面根跟随软链查不到必须登记, 实得 {[f.path for f in result.unreadable]}"
        )
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        os.chmod(hidden, 0o755)


def test_unreadable_on_one_side_alone_is_not_reported_as_drift(vault_pair):
    """MEDIUM 回归: 两侧内容相同、只有一侧读不动时，不得报成 content-drift。

    那是把「读取能力的差异」说成「字节的差异」。做法是把**任一侧**读不动的位置从
    两侧同时剔掉再比；剩下能读的部分若仍不同，那才是真漂移（下一条门验这一半）。
    """
    source, target = vault_pair
    (target / "Dashboard.md").chmod(0o000)
    try:
        result = _classify(target, source=source)
        assert [f.path for f in result.content_drift] == [], (
            f"只有读取能力差异时不得报 drift, 实得 {[f.path for f in result.content_drift]}"
        )
        assert "Dashboard.md" in [f.path for f in result.unreadable]
        assert "Dashboard.md" not in [f.path for f in result.match]
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        (target / "Dashboard.md").chmod(0o644)


def test_source_side_query_failure_enters_the_unreadable_bucket(tmp_path, vault_pair):
    """MEDIUM 回归: 目标确实缺项、而源端那一项查询不到时，查询失败也要进四档分类。

    只写进 `missing` 的说明文字会让整轮出现 `unreadable=0`、rc=1 —— 看上去「只是缺东西」。
    """
    source, target = vault_pair
    (target / "Dashboard.md").unlink()
    guard = source / "Dashboard.md"
    assert guard.exists(), "前提: 源端本来有这一项"
    os.chmod(source, 0o000)
    try:
        result = _classify(target, source=source)
        assert "Dashboard.md" in [f.path for f in result.missing]
        assert any("查询不到" in f.detail for f in result.unreadable), (
            f"源端查询失败必须进 unreadable 桶, 实得 {[(f.path, f.detail) for f in result.unreadable]}"
        )
        assert result.exit_code == vv.EXIT_MISMATCH == 2, "不得只报 rc=1「只缺东西」"
    finally:
        os.chmod(source, 0o755)


# ── CARD-G2-7a: manifest item 级 optional ────────────────────────────


def _manifest_with(tmp_path, manifest_data, name="opt.json"):
    m = tmp_path / name
    m.write_text(json.dumps(manifest_data), encoding="utf-8")
    return m


def _mark_optional(manifest_data, path, flag=True):
    """把**既有**条目标成 optional —— 不能追加同 path 的新条目(会触发重复声明校验)。

    这也更贴近本卡的实际做法: (b) 裁定表是给现有条目加 `optional: true`, 不是新增条目。
    """
    data = json.loads(json.dumps(manifest_data))  # 深拷贝, 不污染 fixture
    hit = [i for i in data["items"] if i["path"] == path]
    assert len(hit) == 1, f"前提: {path} 在清单里恰好一条, 实得 {len(hit)}"
    if flag:
        hit[0]["optional"] = True
    else:
        hit[0].pop("optional", None)
    return data


def test_optional_missing_is_reported_but_does_not_block(tmp_path, vault_pair, manifest_data):
    """(g)② optional 项缺失 → optional-missing 段 + rc **0**；非 optional 缺失 → rc 1。

    这是本卡的核心语义：E-4 之后一批 declared 项在 git 树上本就不存在
    （`.gitignore` 让 Obsidian 配置、第三方插件、插件 data.json 都不入库），
    「树自身跑校验器」必须能 rc 0，否则部署链上没有一个绿的基线态。
    """
    _source, target = vault_pair
    (target / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")  # 先造出来再删, 确保路径可控
    (target / ".obsidian" / "app.json").unlink()

    # 对照组: 同一条目**不带** optional ⇒ 仍是 missing、rc 1
    plain = _mark_optional(manifest_data, ".obsidian/app.json", flag=False)
    before = vv.verify(target, vv.load_manifest(_manifest_with(tmp_path, plain, "plain.json")))
    assert ".obsidian/app.json" in [f.path for f in before.missing]
    # 同样收敛到被测那一项 —— 别的 optional 项缺失不影响「这一条是不是 missing」
    assert ".obsidian/app.json" not in [f.path for f in before.optional_missing]
    assert before.exit_code == vv.EXIT_MISSING == 1

    # 处理组: 同一条目带 optional ⇒ 进 optional-missing、rc 0
    opt = _mark_optional(manifest_data, ".obsidian/app.json")
    manifest = vv.load_manifest(_manifest_with(tmp_path, opt, "opt.json"))
    after = vv.verify(target, manifest)
    assert ".obsidian/app.json" not in [f.path for f in after.missing], "optional 项不得再进 missing"
    # ⚠️ 断言收敛到**被测那一项**: 仓内清单现在有 12 条 optional, 夹具不造其中多数,
    # 所以 optional_missing 本来就不为空 —— 要求它全局为空是错的判据。
    assert ".obsidian/app.json" in [f.path for f in after.optional_missing]
    assert after.exit_code == vv.EXIT_OK == 0, "optional 缺失不得计入退出码"
    assert "## optional-missing" in vv.render(after, manifest)


def test_optional_item_present_still_participates_in_drift(vault_pair, tmp_path, manifest_data):
    """optional 只放松「在不在」，**不放松「内容对不对」** —— 在位时照常参与 drift。"""
    source, target = vault_pair
    (source / ".obsidian" / "app.json").write_text("AAA", encoding="utf-8")
    (target / ".obsidian" / "app.json").write_text("BBB", encoding="utf-8")
    data = _mark_optional(manifest_data, ".obsidian/app.json")
    result = vv.verify(target, vv.load_manifest(_manifest_with(tmp_path, data, "drift.json")), source_dir=source)
    assert [f.path for f in result.content_drift] == [".obsidian/app.json"], "optional 项在位时仍要比内容"
    # 被测那一项**在位** ⇒ 它不该出现在 optional-missing 里（别的 optional 项缺失不影响本判据）
    assert ".obsidian/app.json" not in [f.path for f in result.optional_missing]
    assert result.exit_code == vv.EXIT_MISMATCH == 2


def test_optional_item_present_is_not_reported_as_extra(vault_pair, tmp_path, manifest_data):
    """optional 项始终留在 declared_paths 里 —— 在位时不得被反过来报成 extra。"""
    _source, target = vault_pair
    (target / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")
    data = _mark_optional(manifest_data, ".obsidian/app.json")
    manifest = vv.load_manifest(_manifest_with(tmp_path, data, "decl.json"))
    assert ".obsidian/app.json" in manifest.declared_paths
    result = vv.verify(target, manifest)
    assert [f.path for f in result.extra] == [], (
        f"在位的 optional 项不得报 extra, 实得 {[f.path for f in result.extra]}"
    )
    assert result.exit_code == vv.EXIT_OK


@pytest.mark.parametrize("bad", ["true", 1, 0, None, [], {}])
def test_optional_must_be_a_boolean(tmp_path, manifest_data, bad):
    """optional 写成字符串 "true" 会被静默当真值 ⇒ 一个本该阻断的缺失被放行。类型错直接拒绝加载。"""
    data = json.loads(json.dumps(manifest_data))
    data["items"].append(
        {"path": "probe-optional-type", "role": "t", "action": "copy", "optional": bad, "origin": "test-only"}
    )
    m = _manifest_with(tmp_path, data, "badopt.json")
    with pytest.raises(vv.ManifestError) as exc:
        vv.load_manifest(m)
    assert "optional" in str(exc.value) and "布尔" in str(exc.value)


def test_optional_type_error_uses_the_usage_exit_code(tmp_path, vault_pair, manifest_data):
    """optional 非 bool 走用法错档 3（配置错，不是内容差异）。"""
    _source, target = vault_pair
    data = json.loads(json.dumps(manifest_data))
    data["items"].append(
        {"path": "probe-optional-type", "role": "t", "action": "copy", "optional": "true", "origin": "test-only"}
    )
    m = _manifest_with(tmp_path, data, "badopt2.json")
    assert vv.main(["--vault", str(target), "--manifest", str(m)]) == vv.EXIT_USAGE == 3


# ── CARD-G2-7a: .canvas-config.yaml schema 2.1 ───────────────────────

YAML_SCHEMA_VERSION = "2.1-vault-harness-2026-09-07"


def _extract_yaml_generator() -> str:
    """按**内容**切出 yaml 生成器那段 heredoc（不写死行号——见 skills 门那条教训）。"""
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith('cat > "$TARGET/.canvas-config.yaml" <<EOF')]
    assert len(starts) == 1, f"yaml 生成器应当恰好一处, 实得 {len(starts)}"
    i = starts[0]
    ends = [j for j in range(i + 1, len(lines)) if lines[j] == "EOF"]
    assert ends, "找不到 heredoc 的 EOF 结束行"
    return "\n".join(lines[i : ends[0] + 1])


def test_generated_yaml_is_schema_2_1_with_the_three_new_keys(tmp_path):
    """(f) 生成器产出 schema 2.1，含 backend_url / harness_tree / push_enabled 三个新键。

    `schema_version` 的字面量写死在这里 —— CARD-G2-7b 与 U5-B 引用**同一串**，
    三处对不上就是部署链断了，而这种断裂平时没有任何信号。
    """
    yaml = pytest.importorskip("yaml")
    target = tmp_path / "probe-vault"
    target.mkdir()
    harness = tmp_path / "harness-tree"
    harness.mkdir()
    done = subprocess.run(
        ["bash", "-c", _extract_yaml_generator()],
        env={
            **os.environ,
            "TARGET": str(target),
            "VAULT_NAME": "probe",
            "SUBJECT": "probe-subject",
            "HARNESS_TREE": str(harness),
            "BACKEND_URL": "http://127.0.0.1:8123",
        },
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, f"生成器跑失败: {done.stderr}"
    produced = target / ".canvas-config.yaml"
    assert produced.exists(), "生成器没有产出 yaml"
    parsed = yaml.safe_load(produced.read_text(encoding="utf-8"))

    required = {"vault_id", "subject", "schema_version", "backend_url", "harness_tree", "push_enabled"}
    assert required <= set(parsed), f"yaml 缺键: {sorted(required - set(parsed))}"
    assert parsed["schema_version"] == YAML_SCHEMA_VERSION
    assert parsed["schema_version"].startswith("2.1-")
    assert parsed["vault_id"] == "probe"
    assert parsed["subject"] == "probe-subject"
    assert parsed["backend_url"] == "http://127.0.0.1:8123", "backend_url 必须取 --backend-url 的值"
    assert parsed["harness_tree"] == str(harness), "harness_tree 必须是传入的绝对路径"
    assert parsed["push_enabled"] is False, "push_enabled 缺省必须是 false（--also-push 归 U3-C）"


def test_backend_still_reads_vault_id_from_schema_2_1(tmp_path):
    """后端对新键**天然兼容** —— 它用单键 `.get`，没有 schema_version 校验。

    这条门证的是「加键不会把后端弄坏」。若哪天后端加了 schema 白名单，它会红。
    """
    yaml = pytest.importorskip("yaml")
    target = tmp_path / "probe-vault-2"
    target.mkdir()
    harness = tmp_path / "h2"
    harness.mkdir()
    done = subprocess.run(
        ["bash", "-c", _extract_yaml_generator()],
        env={
            **os.environ,
            "TARGET": str(target),
            "VAULT_NAME": "probe",
            "SUBJECT": "x",
            "HARNESS_TREE": str(harness),
            "BACKEND_URL": "http://127.0.0.1:8123",
        },
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0
    # sanitize_vault_id 就定义在 config.py（不是 graphiti.group_id_compat —— 实测更正）
    from app.config import Settings, sanitize_vault_id

    assert Settings(CANVAS_BASE_PATH=str(target)).vault_id == sanitize_vault_id("probe")


# ── CARD-G2-7a (g)③④⑧: 裁定表落地的行为门 ─────────────────────────


def test_five_ruled_extra_entries_become_allowed_extra(vault_pair):
    """(g)③ live 那 5 个 extra 在新清单下进 allowed-extra，rc 0（U3-A 时是 extra、rc 2）。"""
    _source, target = vault_pair
    (target / ".claude" / "cache").mkdir(parents=True, exist_ok=True)
    (target / ".obsidian" / "graph.json").write_text("{}", encoding="utf-8")
    (target / ".obsidian" / "types.json").write_text("{}", encoding="utf-8")
    (target / ".obsidian" / "plugins" / "excalibrain").mkdir(parents=True, exist_ok=True)
    (target / ".obsidian" / "plugins" / "obsidian-excalidraw-plugin").mkdir(parents=True, exist_ok=True)
    manifest = vv.load_manifest(MANIFEST)
    result = vv.verify(target, manifest)
    assert sorted(f.path for f in result.allowed_extra) == sorted(
        [
            ".claude/cache",
            ".obsidian/graph.json",
            ".obsidian/types.json",
            ".obsidian/plugins/excalibrain",
            ".obsidian/plugins/obsidian-excalidraw-plugin",
        ]
    )
    assert result.extra == [], f"这 5 项都该被放行, 实得 extra={[f.path for f in result.extra]}"
    assert result.exit_code == vv.EXIT_OK == 0
    assert "## allowed-extra" in vv.render(result, manifest)


def test_ruling_table_landed_in_the_manifest():
    """(g)④ 裁定表的四条关键改动真的落到了清单里（不是只写在文档中）。"""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by = {i["path"]: i for i in data["items"]}
    copy_set = {i["path"] for i in data["items"] if i["action"] == "copy"}
    exclude_set = {i["path"] for i in data["items"] if i["action"] == "exclude"}

    # ① 根级 .mcp.json 进 copy（git 追踪却从未进过任一数组）
    assert ".mcp.json" in copy_set
    # ② .claude/mcp.json 退役：出 copy、进 exclude
    assert ".claude/mcp.json" not in copy_set and ".claude/mcp.json" in exclude_set
    assert "sse" in by[".claude/mcp.json"]["note"] or "SSE" in by[".claude/mcp.json"]["note"]
    # ③ claudian 退役
    assert ".obsidian/plugins/claudian" not in copy_set
    assert ".obsidian/plugins/claudian" in exclude_set
    # ④ 密钥件改生成 + optional
    key = by[".obsidian/cls-internal-key.txt"]
    assert key["action"] == "generate" and key.get("optional") is True
    # ⑤ 本卡新补的两条 skeleton（交叉真相源找出的缺口）
    skeleton_set = {i["path"] for i in data["items"] if i["action"] == "skeleton"}
    assert {"wiki/concepts", "wiki/canvases"} <= skeleton_set


def test_backend_and_script_skeleton_definitions_do_not_diverge_on_wiki():
    """(g)④ 附加：两个「新 vault 需要哪些目录」的真相源在 wiki 上必须一致。

    `backend/app/services/vault_init_service.py` 的 `VAULT_DIRECTORIES` 是**第二份**定义。
    本卡之前两者只在 `raw` 上重合 —— `wiki/concepts` / `wiki/canvases` 后端建、脚本不建,
    而 skills 与 MCP 工具都引用这些路径 ⇒ 新部署的 vault 拿不到。
    这条门盯住**已经对齐的那部分**不再漂回去。
    """
    init_src = (BACKEND_DIR / "app" / "services" / "vault_init_service.py").read_text(encoding="utf-8")
    block = re.search(r"VAULT_DIRECTORIES\s*=\s*\[(.*?)\]", init_src, re.S)
    assert block, "找不到 VAULT_DIRECTORIES（后端骨架定义改名了？）"
    backend_dirs = set(re.findall(r'"([^"]+)"', block.group(1)))
    assert {"wiki/concepts", "wiki/canvases"} <= backend_dirs, "前提: 后端确实定义了这两个目录"

    arrays = _parse_install_arrays()
    script_dirs = set(arrays["SKELETON_DIRS"])
    assert {"wiki/concepts", "wiki/canvases"} <= script_dirs, (
        f"脚本骨架必须包含后端也建的 wiki 两件, 实得 {sorted(script_dirs)}"
    )
    # 如实登记仍未对齐的部分（本卡不修, 见 manifest-ruling.md §2.2）
    assert "outputs/exam_boards" in backend_dirs, "前提: 后端还建 outputs/exam_boards"
    assert "outputs/exam_boards" not in script_dirs, (
        "outputs/exam_boards 本卡刻意不加（与 outputs/** exclude 冲突），若已加请同步更新裁定表"
    )


def test_key_self_check_is_reversed(tmp_path):
    """(g)⑧ 密钥件自检**反向**：源目标同字节 → ❌；目标没有 key → ✅。

    E-3 各 vault 各 key：从模板源复制过来就是错的，自检要抓的正是「复制过来了」。
    抽行 eval，不真跑脚本。
    """
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    check_def = [ln for ln in lines if ln.startswith("check() {")]
    key_line = [ln for ln in lines if ln.startswith("check ") and "cls-internal-key" in ln]
    assert len(check_def) == 1 and len(key_line) == 1, "check 定义 / key 自检行应各恰一条"
    # ⚠️ 不锁 `! cmp -s` 字面量: 那样会把「按 cmp 返回码区分 不同(1) 与 读失败(2)」
    # 的正确写法一起挡掉(Codex round-3 MEDIUM 实例 —— 门锁死了缺陷)。
    # 这里只要求它**引用了两侧路径并用 cmp 比较**, 方向由下面三条行为门证明。
    assert "cmp" in key_line[0] and "$SOURCE" in key_line[0] and "$TARGET" in key_line[0], (
        f"key 自检必须用 cmp 比较源与目标: {key_line[0]!r}"
    )
    snippet = "\n".join(check_def + key_line)

    def _probe(source, target):
        return subprocess.run(
            ["bash", "-c", snippet],
            env={**os.environ, "SOURCE": str(source), "TARGET": str(target)},
            capture_output=True,
            text=True,
        ).stdout

    src = tmp_path / "src"
    (src / ".obsidian").mkdir(parents=True)
    (src / ".obsidian" / "cls-internal-key.txt").write_text("SECRET-A\n", encoding="utf-8")

    # 负控: 目标的 key 与源逐字节相同 = 被复制过来了 ⇒ ❌
    copied = tmp_path / "copied"
    (copied / ".obsidian").mkdir(parents=True)
    (copied / ".obsidian" / "cls-internal-key.txt").write_text("SECRET-A\n", encoding="utf-8")
    assert "❌" in _probe(src, copied), "从源复制过来的 key 必须被抓住"

    # 正控一: 目标没有 key（本卡的期望态——由 activate 步重生）⇒ ✅
    absent = tmp_path / "absent"
    (absent / ".obsidian").mkdir(parents=True)
    assert "✅" in _probe(src, absent), "目标没有 key 是期望态"

    # 正控二: 目标有一个**不同**的 key（activate 步已重生）⇒ ✅
    regen = tmp_path / "regen"
    (regen / ".obsidian").mkdir(parents=True)
    (regen / ".obsidian" / "cls-internal-key.txt").write_text("SECRET-B\n", encoding="utf-8")
    assert "✅" in _probe(src, regen), "重生成的不同 key 是期望态"


def test_generated_items_do_not_participate_in_parent_dir_digest(vault_pair):
    """(h)① 真跑照出的缺陷：generate 项嵌套在 copy 目录里时，父目录被误报 drift。

    脚本刚在新 vault 里生成了插件 data.json（源里没有）⇒ 插件目录两侧摘要不同
    ⇒ content-drift。generate 项按定义每 vault 都不同，本就不该参与父目录摘要 ——
    条目自身的「generate 不评 drift」是既有规则，这只是把它推广到嵌套形态。
    """
    source, target = vault_pair
    plugin = ".obsidian/plugins/canvas-learning-system"
    (source / plugin).mkdir(parents=True, exist_ok=True)
    (target / plugin).mkdir(parents=True, exist_ok=True)
    manifest = vv.load_manifest(MANIFEST)
    assert f"{plugin}/data.json" in manifest.declared_paths, "前提: 清单声明了它"
    assert next(i for i in manifest.items if i.path == f"{plugin}/data.json").action == "generate"

    # 生成件只在目标侧（脚本刚生成、源里没有）→ 不得让父目录报 drift
    (target / plugin / "data.json").write_text('{"generated": true}', encoding="utf-8")
    result = vv.verify(target, manifest, source_dir=source)
    assert result.content_drift == [], f"生成件不得让父目录报 drift: {[f.path for f in result.content_drift]}"

    # 对照：同一目录放一个**没有** generate 声明的文件 → 必须报 drift（证门不是恒绿）
    (target / plugin / "stray-file.js").write_text("x", encoding="utf-8")
    result2 = vv.verify(target, manifest, source_dir=source)
    assert plugin in [f.path for f in result2.content_drift], "非生成件的差异仍要比"


def test_tree_head_is_self_consistent_under_the_new_manifest():
    """(g)⑥ E-4 自洽门（常驻版）：树 HEAD 自身作 --vault 与 --source，rc 必须 0。

    卡文特别强调期望**不是**「optional-missing 为空」—— .gitignore 让一批 declared 项
    在树上本就不存在，它们靠 optional 语义放行。期望是：missing / extra / drift /
    unreadable 全 0，且 optional-missing 与「declared 且树上 ABSENT」的集合**恰好相等**
    （二者任何一侧多出来都是清单与树的漂移）。
    """
    tree_vault = REPO_ROOT / "canvas-vault"
    if not tree_vault.is_dir():  # pragma: no cover — 只在完整 checkout 上跑
        pytest.skip("canvas-vault 不在本树")
    manifest = vv.load_manifest(MANIFEST)
    result = vv.verify(tree_vault, manifest, source_dir=tree_vault)
    assert [f.path for f in result.missing] == [], f"树上 declared 缺失未标 optional: {result.missing}"
    assert result.extra == [] and result.content_drift == [] and result.unreadable == []
    absent = sorted(i.path for i in manifest.items if i.action != "exclude" and not (tree_vault / i.path).exists())
    got = sorted(f.path for f in result.optional_missing)
    assert got == absent, (
        f"optional-missing 与树上 ABSENT 集漂移:\n  多出 {sorted(set(got) - set(absent))}\n  少了 {sorted(set(absent) - set(got))}"
    )
    assert result.exit_code == vv.EXIT_OK == 0


# ── CARD-G2-7a round-1 整改的门（Codex r1: H1/H2/M1/M3）────────────────


# 锚字面量提成常量: 它们含双引号, 直接写进 f-string 的 {} 里会复用外层引号 ——
# 运行时(3.14)能跑, 但项目 ruff target=py39 判 invalid-syntax。
SKELETON_LOOP_ANCHOR = 'for d in "${SKELETON_DIRS[@]}"'
YAML_HEREDOC_ANCHOR = 'cat > "$TARGET/.canvas-config.yaml"'


def _sh_line(marker: str, *, prefix: bool = False, kind: str = "code") -> int:
    """按**内容**定位脚本里的唯一锚行, 返回 1-based 行号。

    ⚠️ 门里禁写死行号字面量: 脚本每加一个参数/注释, 全部 origin 都平移,
    钉字面量的门会整批假红(本卡实测两次), 而「行号写偏一格」它又照样放行。
    锚内容 + 实测行号 = 漂移自动跟随, 写错仍然红。
    """
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()

    def _match(ln: str) -> bool:
        return ln.startswith(marker) if prefix else marker in ln

    # 锚**分型**, 不做「优先/回退」(Codex round-4 LOW): 回退式会让「把命令整行注释掉」
    # 照样命中(命令没了、门还绿), 反过来给 echo 加一句注释又能把标题锚抢走。
    #   kind="code"    命令锚 —— 只在剥掉行内注释后的**代码**里找
    #   kind="comment" 注释标题锚 —— 只在注释行里找
    if kind == "code":
        hits = [i + 1 for i, ln in enumerate(lines) if not ln.lstrip().startswith("#") and _match(ln.split("#", 1)[0])]
    elif kind == "comment":
        hits = [i + 1 for i, ln in enumerate(lines) if ln.lstrip().startswith("#") and _match(ln)]
    else:  # pragma: no cover — 调用方拼错类型应当立刻暴露
        raise AssertionError(f"未知锚类型 {kind!r}")
    assert len(hits) == 1, f"锚 {marker!r} 命中 {hits}（应恰好 1 处）"
    return hits[0]


def _extract_block(start_marker: str, end_marker: str, *, last: bool = False, close_fi: bool = False) -> str:
    """按**子串**切出脚本的某一段（不写死行号——见 skills 门那条教训）。

    纯 `in` 匹配而非正则: marker 里常带 `$`/引号, 当正则会静默失配
    (实测 `TARGET="$VAULTS_ROOT…"` 作为正则匹配不到任何行)。
    `last=True` 取 end 的**最后一次**命中 —— 切到 heredoc 结束符时,
    第一次命中是 `<<'EOF'` 起始行, 结束行在后。
    """
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    starts = [i for i, ln in enumerate(lines) if start_marker in ln]
    # ⚠️ end 只在 start **之后**找: done/fi/EOF 这类结束符在脚本前半段已出现多次,
    # 取全局第一次命中会得到 end < start（本卡实测 ends[0]=44 而 start=104）。
    ends = [i for i, ln in enumerate(lines) if end_marker in ln and i > starts[0]]
    assert len(starts) == 1, f"start {start_marker!r} 命中 {len(starts)} 次"
    assert ends, f"end {end_marker!r} 在 start 之后零命中"
    end = ends[-1] if last else ends[0]
    assert end > starts[0], (starts, ends[:3])
    stop = end
    if close_fi:
        # end 行常落在 if 块**内部**(如 echo), 向后找到本块的 fi 才闭合
        j = end + 1
        while j < len(lines) and lines[j].strip() != "fi":
            j += 1
        assert j < len(lines), f"end({end}) 之后找不到 fi"
        stop = j
    return "\n".join(lines[starts[0] : stop + 1])


def test_stale_data_json_from_dir_copy_is_cleared_before_generate(tmp_path):
    """H1 回归: 整目录复制带进来的旧 data.json 必须在生成前被清掉。

    (h)② 真跑实测: live 源的 internalApiKey/backendUrl 原样进了新 vault ——
    `[ ! -e ]` 生成被短路, verify 的 generate 摘要过滤又看不见它。先 rm 再生成。
    """
    target = tmp_path / "t"
    (target / ".obsidian/plugins/canvas-learning-system").mkdir(parents=True)
    (target / ".obsidian/plugins/canvas-learning-system/data.json").write_text(
        '{"internalApiKey": "STALE-KEY-FROM-LIVE"}', encoding="utf-8"
    )
    # 只切「rm 清理行 + 插件 data.json 生成块」: 切到 settings 块的 heredoc 结束符
    # 会把它的 if 留半截(语法错), 切到 echo 行会把 cat<<EOF 断在中间 —— 都实测踩过。
    # 生成块以 echo 收尾、不含未闭合结构, 是安全边界。
    block = _extract_block(
        'rm -f "$TARGET/.obsidian/plugins/canvas-learning-system/data.json"',
        "✏️  生成 插件 data.json",
        close_fi=True,
    )
    done = subprocess.run(
        ["bash", "-c", block],
        env={**os.environ, "TARGET": str(target), "BACKEND_URL": "http://127.0.0.1:8123"},
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    data = json.loads((target / ".obsidian/plugins/canvas-learning-system/data.json").read_text(encoding="utf-8"))
    assert data["internalApiKey"] == "", f"旧 key 必须被清掉, 实得 {data['internalApiKey']!r}"
    assert data["backendUrl"] == "http://127.0.0.1:8123", "生成值必须来自 --backend-url"


def test_default_source_is_harness_canvas_vault(tmp_path):
    """H2 回归: 不传 --source 时, 模板源缺省 = $REPO/canvas-vault(harness 树)。

    不再从 .env ACTIVE_VAULT 解析 —— 那会把「当前活 vault」当模板,
    活 vault 里的 gitignored 件整个带进新库, 正是 E-3/E-4 要停的行为。
    """
    block = _extract_block('if [ -z "$SOURCE" ]', 'TARGET="$VAULTS_ROOT/$VAULT_NAME"')
    harness = tmp_path / "harness"
    harness.mkdir()
    # ⚠️ ENV_FILE 必须**有效且指向别处**(Codex round-2 MEDIUM): 指向不存在的文件时,
    # 旧 .env 解析实现同样回退成 ${REPO}/canvas-vault —— 这条门就恒真、拦不住回退。
    # 有效 .env 下旧实现输出 other-root/other-vault, 新实现固定 harness, 两者才分得开。
    other_root = tmp_path / "other-root"
    env_file = tmp_path / "real.env"
    env_file.write_text(f"VAULTS_ROOT={other_root}\nACTIVE_VAULT=other-vault\n", encoding="utf-8")
    done = subprocess.run(
        ["bash", "-c", block + '\necho "SOURCE=$SOURCE"'],
        env={**os.environ, "REPO": str(harness), "ENV_FILE": str(env_file), "SOURCE": ""},
        capture_output=True,
        text=True,
    )
    assert f"SOURCE={harness}/canvas-vault" in done.stdout, (
        f"缺省源必须是 harness 树的 canvas-vault, 实得: {done.stdout!r}"
    )


def test_generate_item_wrong_shape_is_not_a_match(vault_pair, tmp_path, manifest_data):
    """M1 回归: generate 项被误建成**目录**时不得记 match —— digest 侧的
    generate 过滤会把整棵剔掉, 这里是形态错误唯一的信号点。"""
    _source, target = vault_pair
    probe = target / ".obsidian" / "plugins" / "canvas-learning-system" / "data.json"
    probe.parent.mkdir(parents=True, exist_ok=True)
    if probe.exists():
        probe.unlink()
    probe.mkdir()  # 误建成目录
    (probe / "inner.txt").write_text("x", encoding="utf-8")
    result = _classify(target)
    # 按**分类**判, 不锁 detail 措辞 —— 措辞是实现细节, 分类才是这条门的主张
    assert any(f.path == str(probe.relative_to(target)) for f in result.unreadable), (
        f"形态错误必须登记 unreadable, 实得 {[(f.path, f.detail) for f in result.unreadable]}"
    )
    assert str(probe.relative_to(target)) not in [f.path for f in result.match]
    assert result.exit_code == vv.EXIT_MISMATCH == 2


def test_key_self_check_rejects_unreadable_key(tmp_path):
    """M3 回归: `! cmp -s` 会把 cmp 的读错误也当通过 —— 目标 key 存在但源不可读时
    必须显式 ❌, 不能证明「未复制」。"""
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    check_def = [ln for ln in lines if ln.startswith("check() {")]
    key_line = [ln for ln in lines if ln.startswith("check ") and "cls-internal-key" in ln]
    assert len(check_def) == 1 and len(key_line) == 1
    snippet = "\n".join(check_def + key_line)

    src = tmp_path / "src"
    (src / ".obsidian").mkdir(parents=True)
    (src / ".obsidian" / "cls-internal-key.txt").write_text("A\n", encoding="utf-8")
    (src / ".obsidian" / "cls-internal-key.txt").chmod(0o000)
    tgt = tmp_path / "tgt"
    (tgt / ".obsidian").mkdir(parents=True)
    (tgt / ".obsidian" / "cls-internal-key.txt").write_text("B\n", encoding="utf-8")
    try:
        out = subprocess.run(
            ["bash", "-c", snippet],
            env={**os.environ, "SOURCE": str(src), "TARGET": str(tgt)},
            capture_output=True,
            text=True,
        ).stdout
        assert "❌" in out, f"源不可读必须显式拒绝(不锁措辞), 实得: {out!r}"
    finally:
        (src / ".obsidian" / "cls-internal-key.txt").chmod(0o644)


def test_generate_section_covers_exactly_the_generate_items():
    """round-1 自查补门（Codex r2 §三.1 的问题）：脚本生成段清理/生成的路径集合，
    必须与 manifest 的 generate 集（除 .canvas-config.yaml——它由独立 yaml 生成器写）
    **恰好一致** —— 将来加第四个 generate 件时，rm 行不会自己跟上来，这条门会红。
    """
    import re as _re3

    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if "生成件 (CARD-G2-7a)" in ln)  # 段标题本身是注释行
    section = lines[start:]
    # ⚠️ 只认**清理命令自己的操作数**。首版把 `X="$TARGET/…"` 变量赋值也并进来 ——
    # 于是「删掉 templater 的 rm 操作数、保留 TEMPLATER_DATA=」这个变异照样通过
    # (Codex round-3 LOW，它自己跑的变异实测存活)。赋值只说明脚本**提到**这个路径,
    # 不说明它**清理**了这个路径, 而漏清正是要防的那件事。
    cleaned = set()
    in_rm = False
    for ln in section:
        stripped = ln.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith("rm "):
            in_rm = True
        if in_rm:
            # 先剥**行内注释**: 把操作数注释掉、路径字面量却还留在行上, 原判据照收
            # ⇒ 「已不再清理」却仍然通过(Codex round-4 实测)。
            code_part = ln.split("#", 1)[0]
            cleaned.update(_re3.findall(r'\$TARGET/(\S+?)"', code_part))
            in_rm = code_part.rstrip().endswith("\\")  # 反斜杠续行才继续算同一条 rm
    touched = cleaned
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # 两个例外的归属（首版门就抓到了这个漂移——不是脚本漏，是归属不同）:
    #   .canvas-config.yaml      → 本脚本独立的 yaml 生成器(:116 附近)
    #   .obsidian/cls-internal-key.txt → deploy-vault.sh 的 activate 步(CARD-G2-7b,
    #     那一步才知道跟哪个后端实例配对); 本脚本对它只「不清不生成」+ 自检反向判
    OUTSOURCED = {".canvas-config.yaml", ".obsidian/cls-internal-key.txt"}
    expected = {i["path"] for i in data["items"] if i["action"] == "generate"} - OUTSOURCED
    # 验伪锚: 生成段确实被解析到了(否则空集==空集恒真)
    # 验伪锚只证明「解析器没有空转」, 阈值要**远低于**主断言的期望值 ——
    # 写成 >=3(恰等于期望集大小)会让「少清一条」先撞锚, 报出来的是解析异常而不是
    # 「漏清了哪一条」, 定位信息全丢(变异实测: LOW-1 变异撞的是锚不是主断言)。
    assert len(touched) >= 1, f"生成段清理集解析异常(解析器空转): {touched}"
    assert touched == expected, (
        f"脚本生成段与 manifest generate 集漂移:\n  脚本多清/多生成: {sorted(touched - expected)}\n  脚本漏了: {sorted(expected - touched)}"
    )


# ── CARD-G2-7a round-2 整改的门（Codex r2: H1/M1/M2）──────────────────


def test_every_recursive_copy_follows_operand_symlinks():
    """H1 结构门: 脚本里每一处 `cp -R` 都必须带 `-H`。

    裸 `cp -R` 对**目录软链**保留链接（macOS 实测）, 于是 TARGET 里放的是一条指回
    共享源的链；随后生成段清理/写入就会**沿链改写模板源自己**。这是按性质写的门 ——
    将来新增任何递归复制点漏了 `-H`, 这里就红, 不必等有人踩到。
    """
    # 判据按 **token** 走, 不按整行子串 —— 两个实测存活的变异都是文本层的花招
    # (Codex round-3 LOW): ① 去掉 `.claude` 的 `-H` 但行尾补 `# cp -R -H required`;
    # ② 写成 `cp -PR` 这类参数重排。所以: 先剥行内注释, 再把 cp 的选项 token 摊平成
    # 字母集合, 断言「有 R/r 就必须有 H」。
    import shlex as _shlex

    bad = []
    for i, raw in enumerate(INSTALL_SH.read_text(encoding="utf-8").splitlines()):
        code = raw.split("#", 1)[0]  # 剥行内注释（本脚本的命令行里不含带 # 的字面量）
        code = code.rstrip().rstrip("\\")  # 剥行尾续行反斜杠: 否则 shlex 抛错整行被跳过
        # (变异实测 `cp -PR` 因此存活)
        if "cp" not in code:
            continue
        try:
            tokens = _shlex.split(code)
        except ValueError:  # 引号未闭合的续行片段, 交给别的行去判
            continue
        # 按 **basename** 认命令: `/bin/cp -R` 与 `cp -R` 是同一条命令,
        # 只认裸 token 会漏掉带路径的写法(Codex round-4 实测七门全 PASS)。
        cp_at = next((k for k, tok in enumerate(tokens) if tok.rsplit("/", 1)[-1] == "cp"), None)
        if cp_at is None:
            continue
        flags = set()
        for tok in tokens[cp_at + 1 :]:
            if tok.startswith("-") and not tok.startswith("--"):
                flags.update(tok[1:])
            elif not tok.startswith("-"):
                break  # 到操作数为止
        if ("R" in flags or "r" in flags) and "H" not in flags:
            bad.append((i + 1, raw.strip()))
    assert bad == [], f"递归复制未带 -H（会沿目录软链写穿模板源）: {bad}"


def test_plugin_dir_symlink_does_not_write_through_to_shared_source(tmp_path):
    """H1 行为门: 源插件目录是软链时, 部署 + 生成不得改写共享源。

    复现 Codex round-2 HIGH-1: 裸 `cp -R` 下 TARGET 里是链, 生成段写 data.json
    实际落在 shared/ 上（本机实测 shared 被改写）。
    """
    # ⚠️ 形态要害: **插件目录自身**是软链, 不是它的父目录。
    # 若把 plugins/ 做成链, cp 的操作数是穿过链之后的真目录, -H 有没有都一样 ——
    # 首版夹具就是这么写的, 变异(去掉 -H)照样全绿 = 探针避开了缺陷显形点。
    shared = tmp_path / "shared"
    shared.mkdir()
    guard = shared / "data.json"
    guard.write_text('{"internalApiKey": "SHARED-MUST-NOT-CHANGE"}', encoding="utf-8")
    before = guard.read_bytes()

    source = tmp_path / "src"
    (source / ".obsidian" / "plugins").mkdir(parents=True)
    (source / ".obsidian" / "plugins" / "canvas-learning-system").symlink_to(shared, target_is_directory=True)
    target = tmp_path / "tgt"
    (target / ".obsidian" / "plugins").mkdir(parents=True)

    copy_block = _extract_block('for p in "${OBSIDIAN_PLUGINS[@]}"', "done")
    gen_block = _extract_block(
        'rm -f "$TARGET/.obsidian/plugins/canvas-learning-system/data.json"',
        "✏️  生成 插件 data.json",
        close_fi=True,
    )
    script = "OBSIDIAN_PLUGINS=(canvas-learning-system)\n" + copy_block + "\n" + gen_block
    done = subprocess.run(
        ["bash", "-c", script],
        env={**os.environ, "SOURCE": str(source), "TARGET": str(target), "BACKEND_URL": "http://127.0.0.1:8123"},
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    assert guard.read_bytes() == before, "共享模板源被沿软链写穿（H1 回归）"
    tgt_data = json.loads((target / ".obsidian/plugins/canvas-learning-system/data.json").read_text(encoding="utf-8"))
    assert tgt_data["internalApiKey"] == "", "目标应拿到新生成的空 key"


def test_unreadable_generate_file_is_not_a_match(vault_pair):
    """M1 回归: generate 件在位但**读不动**时不得记 match。

    `is_file()` 对 000 权限的普通文件照样返回 True —— 只查类型会把「脚本写坏的
    生成件」当成正常件, 而父目录摘要又把 generate 路径整棵剔掉, 两边都没信号。
    """
    _source, target = vault_pair
    probe = target / ".obsidian" / "plugins" / "canvas-learning-system" / "data.json"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("{}", encoding="utf-8")
    probe.chmod(0o000)
    try:
        result = _classify(target)
        rel = str(probe.relative_to(target))
        assert any(f.path == rel for f in result.unreadable), (
            f"不可读生成件必须登记 unreadable, 实得 {[f.path for f in result.unreadable]}"
        )
        assert rel not in [f.path for f in result.match]
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        probe.chmod(0o644)


def test_key_self_check_rejects_directory_shaped_key(tmp_path):
    """M2 回归: 源 key 路径是**可读目录**时, `cmp` 读目录失败(rc=2), `! cmp` 反而成真。

    本机实测: 旧写法对这种形态打 ✅ 并附带 cmp 的错误输出 —— 判据必须先验形态。
    """
    lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    snippet = "\n".join(
        [ln for ln in lines if ln.startswith("check() {")]
        + [ln for ln in lines if ln.startswith("check ") and "cls-internal-key" in ln]
    )
    src = tmp_path / "src"
    (src / ".obsidian" / "cls-internal-key.txt").mkdir(parents=True)  # 误建成目录
    tgt = tmp_path / "tgt"
    (tgt / ".obsidian").mkdir(parents=True)
    (tgt / ".obsidian" / "cls-internal-key.txt").write_text("B\n", encoding="utf-8")
    out = subprocess.run(
        ["bash", "-c", snippet],
        env={**os.environ, "SOURCE": str(src), "TARGET": str(tgt)},
        capture_output=True,
        text=True,
    ).stdout
    assert "❌" in out, f"目录态源必须显式拒绝(不锁措辞), 实得: {out!r}"


def test_origin_points_at_the_array_that_actually_declares_each_item():
    """LOW-3 回归：origin 必须落在该 item **自己所属**的那个数组行，区间 origin 的尾要精确。

    审查者实测：把 `.claude/skills` 的 origin 从 CLAUDE_ITEMS 行改成 OBSIDIAN_FILES 行、
    或把生成段区间缩成 `134-135`，原来的门**都照样通过**——它只验「落在数组区」和
    「不越界」，不验「是不是**这一条**的来源」。判据取名面必须恰好等于它的主张。
    """
    import re as _re4

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sh_lines = INSTALL_SH.read_text(encoding="utf-8").splitlines()
    names = ("SKELETON_DIRS", "CLAUDE_ITEMS", "OBSIDIAN_FILES", "OBSIDIAN_PLUGINS", "ROOT_FILES")
    hits = {name: [i + 1 for i, ln in enumerate(sh_lines) if ln.startswith(name + "=")] for name in names}
    # ⚠️ 逐个断言**唯一**: 用 dict 推导会把重复定义静默吞掉(后一条覆盖前一条),
    # 于是「在后面补一行 CLAUDE_ITEMS=(skills) 把数组改瘦」也能通过(Codex round-4 实测)。
    for name, ls in hits.items():
        assert len(ls) == 1, f"{name} 必须恰好一处定义, 实测在 {ls}"
    arrays = {name: ls[0] for name, ls in hits.items()}

    def owner(path: str, action: str) -> str | None:
        """这一条**应当**由哪个数组声明（None = 不由数组声明，如 exclude/generate）。"""
        if action == "skeleton":
            return "SKELETON_DIRS"
        if action != "copy":
            return None
        parts = path.split("/")
        if parts[0] == ".claude" and len(parts) == 2:
            return "CLAUDE_ITEMS"
        if parts[:2] == [".obsidian", "plugins"] and len(parts) == 3:
            return "OBSIDIAN_PLUGINS"
        if parts[0] == ".obsidian":
            return "OBSIDIAN_FILES"
        if len(parts) == 1:
            return "ROOT_FILES"
        return None

    checked = 0
    for item in data["items"]:
        want = owner(item["path"], item["action"])
        if want is None:
            continue
        m = _re4.match(r"install-vault\.sh:(\d+)(?:-(\d+))?$", item["origin"])
        assert m, f"{item['path']} 的 origin 形态异常: {item['origin']!r}"
        # 数组声明是**单行**来源, 写成区间(如 72-180)等于把整段脚本都算作出处
        assert m.group(2) is None, f"{item['path']} 由数组单行声明, origin 不该是区间: {item['origin']}"
        assert int(m.group(1)) == arrays[want], (
            f"{item['path']} 应由 {want}(第 {arrays[want]} 行) 声明，origin 却指 {item['origin']}"
        )
        checked += 1
    # 验伪锚：确实核过了 30 条声明件（8 skeleton + 22 copy）
    assert checked == 30, f"应核 30 条数组声明件，实核 {checked}"

    # 区间 origin 的**尾**要精确：yaml 段收在它的 heredoc 结束符，生成段收在 settings 块的 fi
    yaml_start = _sh_line(YAML_HEREDOC_ANCHOR, prefix=True)
    yaml_end = next(i + 1 for i, ln in enumerate(sh_lines) if ln.strip() == "EOF" and i + 1 > yaml_start)
    gen_start = _sh_line("生成件 (CARD-G2-7a)", kind="comment")
    localeof = [i + 1 for i, ln in enumerate(sh_lines) if ln.strip() == "LOCALEOF"][-1]
    gen_end = next(i + 1 for i, ln in enumerate(sh_lines) if i + 1 > localeof and ln.strip() == "fi")
    by_path = {i["path"]: i["origin"] for i in data["items"]}
    assert by_path[".canvas-config.yaml"] == f"install-vault.sh:{yaml_start}-{yaml_end}"
    for p in (
        ".claude/settings.local.json",
        ".obsidian/plugins/canvas-learning-system/data.json",
        ".obsidian/plugins/templater-obsidian/data.json",
    ):
        assert by_path[p] == f"install-vault.sh:{gen_start}-{gen_end} (生成件段)", (
            f"{p} 的生成段区间应为 {gen_start}-{gen_end}，实为 {by_path[p]}"
        )


def test_generate_symlink_to_unreadable_file_is_not_a_match(vault_pair):
    """MEDIUM-2 回归：generate 件是**软链**时不得记 match，链到不可读文件更不行。

    审查者复现：`is_file()` 跟随软链只看类型 ⇒ True；`_leaf_digest` 对链只读
    `readlink` 原文 ⇒ 永远 `bad=False`。两个「查了」的动作叠起来仍是 `match`/`rc=0`。
    生成件按定义是脚本写出的**实体**文件，判据必须用 `lstat` 不跟随。
    """
    _source, target = vault_pair
    hidden = target.parent / "hidden-payload.json"
    hidden.write_text('{"internalApiKey": "LEAKED"}', encoding="utf-8")
    hidden.chmod(0o000)
    probe = target / ".obsidian" / "plugins" / "canvas-learning-system" / "data.json"
    probe.parent.mkdir(parents=True, exist_ok=True)
    if probe.exists() or probe.is_symlink():
        probe.unlink()
    probe.symlink_to(hidden)
    try:
        result = _classify(target)
        rel = str(probe.relative_to(target))
        assert any(f.path == rel for f in result.unreadable), (
            f"软链生成件必须登记 unreadable，实得 {[(f.path, f.detail) for f in result.unreadable]}"
        )
        assert rel not in [f.path for f in result.match]
        assert result.exit_code == vv.EXIT_MISMATCH == 2
    finally:
        hidden.chmod(0o644)

    # 第二种形态才真正锁住「不跟随」: 链指向一个**可读**的普通文件。
    # 跟随式判据(os.stat)会说「普通文件且读得动」⇒ match；只有 lstat 不跟随才拦得下。
    readable = target.parent / "readable-payload.json"
    readable.write_text("{}", encoding="utf-8")
    probe.unlink()
    probe.symlink_to(readable)
    result2 = _classify(target)
    rel = str(probe.relative_to(target))
    assert any(f.path == rel for f in result2.unreadable), (
        f"链到可读文件的生成件同样必须拦下（生成件应为实体文件），实得 {[(f.path, f.detail) for f in result2.unreadable]}"
    )
    assert rel not in [f.path for f in result2.match]


def test_symlinked_source_dir_copied_with_H_is_not_reported_as_drift(tmp_path, manifest_data):
    """MEDIUM-1 回归：源侧目录软链 + `cp -R -H` 得到的实体目录，内容相同就不该报 drift。

    这是 round-2 修法引入的**误报**：`cp -R -H` 把链实体化，而摘要侧对源仍按
    「链记 readlink 原文」算 ⇒ 源是 `L:`、目标是内容摘要 ⇒ 完全正确的复制也 rc=2。
    校验器的源侧根条目因此与 `-H` 对齐：只跟随**根**这一层。
    """
    shared = tmp_path / "shared"
    (shared / "inner").mkdir(parents=True)
    (shared / "inner" / "a.txt").write_text("same", encoding="utf-8")

    source = tmp_path / "src"
    (source / ".obsidian" / "plugins").mkdir(parents=True)
    (source / ".obsidian" / "plugins" / "dataview").symlink_to(shared, target_is_directory=True)

    target = tmp_path / "tgt"
    (target / ".obsidian" / "plugins" / "dataview" / "inner").mkdir(parents=True)
    (target / ".obsidian" / "plugins" / "dataview" / "inner" / "a.txt").write_text("same", encoding="utf-8")

    manifest_data["items"] = [
        {
            "path": ".obsidian/plugins/dataview",
            "role": "system-file",
            "action": "copy",
            "origin": "test-only",
        }
    ]
    manifest_data["extra_allow"] = [".obsidian", ".obsidian/plugins"]
    mpath = tmp_path / "m.json"
    mpath.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
    manifest = vv.load_manifest(mpath)
    result = vv.verify(target, manifest, source_dir=source)
    assert [f.path for f in result.content_drift] == [], (
        f"源侧根软链 + -H 实体化后内容相同，不该报 drift：{[(f.path, f.detail) for f in result.content_drift]}"
    )
    assert ".obsidian/plugins/dataview" in [f.path for f in result.match]


def test_malformed_hotkeys_is_caught_even_when_main_js_is_absent(vault_pair):
    """MEDIUM-1 回归：hotkeys 顶层不是对象时，即使 main.js 缺席也必须拦下。

    原顺序是「main.js 缺 → not evaluated → return」，于是 hotkeys 自身的结构错误
    在**树源部署**（main.js 是 gitignored 构建产物、本来就不在）下完全无声：
    两层检查同时放行、rc=0。hotkeys 的自校验必须独立于 main.js 在不在。
    """
    _source, target = vault_pair
    main_js = target / vv.PLUGIN_MAIN_JS_REL
    assert not main_js.exists(), "该夹具本就没有 main.js（正是这条门要覆盖的场景）"
    (target / vv.HOTKEYS_REL).write_text('[{"canvas-learning-system:canvas-start-exam": []}]', encoding="utf-8")
    result = _classify(target)
    assert any(f.path == vv.HOTKEYS_REL for f in result.unreadable), (
        f"hotkeys 顶层非对象必须登记 unreadable，实得 {[(f.path, f.detail) for f in result.unreadable]}"
    )
    assert result.exit_code == vv.EXIT_MISMATCH == 2


# 无写端 FIFO 的回归门只有在**校验器不挂**时才会返回, 所以超时值既是判据也是保险丝。
# 取 60s 的实证依据: 同一条命令的正常路径本机连跑 5 次, 最慢 0.052s(见
# evidence-g27a-tail/ 的 (f) 取值实测) —— 60s 是 >1000× 余量, 慢机/冷启动打不穿;
# 而一旦形态门被改回裸 read_text, 这条门会在 60s 后以 TimeoutExpired 变红, 不会静默挂住整套。
HOTKEYS_FIFO_TIMEOUT_S = 60


def _report_section(report_text: str, title: str) -> list[str]:
    """从渲染报告里取出 `## <title>` 那一段的明细行(不含标题行)。

    判据要的是**归桶身份**而不是「某处出现过这串字」: 同一句 detail 若只在别的段落
    出现, 断言 `in report_text` 照样成立, 门就变成了在测字符串存在性。
    """
    out: list[str] = []
    inside = False
    for line in report_text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == f"## {title}"
            continue
        if inside and line.strip():
            out.append(line)
    return out


def test_hotkeys_fifo_does_not_hang_and_reports_unreadable(vault_pair, tmp_path):
    """MEDIUM-2 回归: hotkeys.json 是**无写端 FIFO** 时, 校验器不得挂住, 且必须归 unreadable ⇒ rc=2。

    修之前 `_check_hotkeys` 先 `_entry_state`(走 `os.lstat`, FIFO 判 present)、随后直接
    `hotkeys_path.read_text()` —— `read_text` 内部是**阻塞** open, 无写端 FIFO 上它会一直
    等写者, 永久停在打开阶段: 包在外面的 `except (OSError, UnicodeDecodeError)` 根本到不了,
    `--vault` 连 rc=2 都跑不出来(改前探针实测 15s TimeoutExpired, faulthandler 自报栈停在
    那一行的 open 系统调用)。

    ⛔ 这条门**必须**走 `subprocess` + `timeout=`, 不能进程内调 `vv.main()` / `_classify()`:
       回归时进程内那条路会把**整套 pytest** 一起挂死, 既不会红也拿不到任何失败信息。
    ⚠️ `--report` 落点必须在 `--vault` 树**外** —— 落在树内会被 `_check_report_location`
       判 rc=3(用法错), 门就变成在测别的东西(本卡探针初版踩过这一脚)。

    两段输入配成对照:
      - 对照输入: 同一个 vault, hotkeys 是**普通文件** ⇒ 不得进 unreadable(验伪锚:
        证明下面那条断言不是「在任何输入下都成立」的空判据);
      - 被测输入: 同一个 vault, hotkeys 换成无写端 FIFO ⇒ rc=2 + 归 unreadable + note 说清形态。
    """
    _source, target = vault_pair
    hotkeys = target / vv.HOTKEYS_REL

    def _run_verifier(report_name: str) -> tuple[int, str]:
        report = tmp_path / report_name
        done = subprocess.run(
            [
                sys.executable,
                str(VERIFIER),
                "--vault",
                str(target),
                "--manifest",
                str(MANIFEST),
                "--report",
                str(report),
            ],
            capture_output=True,
            timeout=HOTKEYS_FIFO_TIMEOUT_S,
        )
        assert done.returncode != vv.EXIT_USAGE, (
            f"落进用法错档说明这条门没跑到 hotkeys 检查: rc={done.returncode} "
            f"stderr={done.stderr.decode('utf-8', 'replace')[:400]}"
        )
        text = report.read_text(encoding="utf-8") if report.exists() else ""
        assert text, f"--report 没落盘, 无从判归桶: rc={done.returncode}"
        return done.returncode, text

    # ── 对照输入: 普通文件 hotkeys ────────────────────────────────────────
    assert hotkeys.is_file(), "夹具前提: 对照段的 hotkeys 必须是普通文件"
    _control_rc, control_report = _run_verifier("control-report.txt")
    assert vv.HOTKEYS_REL not in " ".join(_report_section(control_report, "unreadable")), (
        f"普通文件 hotkeys 不该进 unreadable, 实得 {_report_section(control_report, 'unreadable')}"
    )
    assert "不是普通文件" not in control_report, "对照输入不该出现形态门的判词"

    # ── 被测输入: 无写端 FIFO ─────────────────────────────────────────────
    hotkeys.unlink()
    os.mkfifo(hotkeys)
    try:
        # 回归时这一行抛 subprocess.TimeoutExpired ⇒ 本条测试红, 且**不会**挂住整套。
        rc, report_text = _run_verifier("fifo-report.txt")
    finally:
        # FIFO 必须删干净: 留着会把后面任何读它的进程一起挂住(含 pytest 自己的清理)。
        if hotkeys.is_fifo():
            hotkeys.unlink()

    assert rc == vv.EXIT_MISMATCH == 2, f"无写端 FIFO 必须归 mismatch 档, 实得 rc={rc}"
    unreadable_rows = _report_section(report_text, "unreadable")

    # ⚠️ 不要试图从**渲染后的文本**里把结构化身份切回来 —— 那是有损的。
    #    上一版按 `row.split("  —", 1)[0]` 切出路径再比相等, 仍有两类未被拦下的输入
    #    (Codex round-3 LOW-1):
    #      · 真实路径就叫 `.obsidian/hotkeys.json  —.bak` 的 finding —— 切出来的前半段
    #        恰好等于 HOTKEYS_REL, 于是「真实 hotkeys finding 有 0 条」却选中 1 条并通过;
    #      · 同一路径两条(`role="-"` 与 `role="config"`) —— 实际 2 条, 却只选中第一条,
    #        照样满足「恰好一条」。
    #    改成两条一起卡:
    #      ① 整个 ## unreadable 段里**提到** HOTKEYS_REL 的行必须**恰好 1 条**(卡唯一性);
    #      ② 那一行必须与生产渲染出来的**那一行逐字相同**(卡身份 + 理由, 一次到位)。
    #    代价如实声明: 这条判据与生产的 detail 文案、以及 role 恒为 "-" 这两件事**绑死**。
    #    任一改动会让本门**响亮地红**(而不是静默放行) —— 方向是保守的, 但要知道它会红。
    # 归一化空白后再比（Codex round-4 LOW-10）：上一版直接比整行原文，于是生产端
    # 只把缩进从两格改成四格、或末尾多一个空格，这条门就红 —— 那是对**展示格式**的耦合，
    # 不是对**行为**的判定。归一化只抹掉空白，身份与理由仍然逐字卡住。
    def _norm(row: str) -> str:
        return " ".join(row.split())

    expected_row = _norm(f"{vv.HOTKEYS_REL}  — 快捷键文件不是普通文件(FIFO/设备等特殊文件), 无法核对快捷键")
    mentions = [row for row in unreadable_rows if vv.HOTKEYS_REL in row]
    assert len(mentions) == 1, (
        f"## unreadable 段里提到 {vv.HOTKEYS_REL} 的行必须恰好 1 条, 实得 {len(mentions)} 条: {unreadable_rows}"
    )
    assert _norm(mentions[0]) == expected_row, (
        f"那一行必须与生产渲染逐字相同(身份+理由一起卡, 空白归一化后比)"
        f"\n  期望: {expected_row!r}\n  实得: {_norm(mentions[0])!r}"
    )
    assert "hotkeys                : not evaluated (不是普通文件)" in report_text, (
        "汇总行的 hotkeys note 必须如实写形态, 不得说成「查过没问题」"
    )


def test_claude_dir_symlink_does_not_write_through_either(tmp_path):
    """LOW-2 回归：`.claude` 复制点与插件复制点同样要防写穿。

    原来只有插件复制点有行为门，于是把 `.claude` 那行改成 `/bin/cp -R`（去掉 -H、
    带绝对路径）时，结构门与七条 origin 门全部通过——审查者实测。
    """
    shared = tmp_path / "shared-skills"
    shared.mkdir()
    guard = shared / "SKILL.md"
    guard.write_text("SHARED-MUST-NOT-CHANGE", encoding="utf-8")
    before = guard.read_bytes()

    source = tmp_path / "src"
    (source / ".claude").mkdir(parents=True)
    (source / ".claude" / "skills").symlink_to(shared, target_is_directory=True)
    target = tmp_path / "tgt"
    (target / ".claude").mkdir(parents=True)

    block = _extract_block('for item in "${CLAUDE_ITEMS[@]}"', "done")
    script = "CLAUDE_ITEMS=(skills)\n" + block
    done = subprocess.run(
        ["bash", "-c", script],
        env={**os.environ, "SOURCE": str(source), "TARGET": str(target)},
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    copied = target / ".claude" / "skills"
    assert not copied.is_symlink(), ".claude 下的目录软链必须被实体化，否则写它会穿到共享源"
    (copied / "SKILL.md").write_text("LOCAL-EDIT", encoding="utf-8")
    assert guard.read_bytes() == before, "共享源被沿软链写穿（LOW-2 回归）"


# ── U3-A(CARD-RV-G2-6) round-5 遗留两条 HIGH 的回归门 ──────────────────


def test_kind_file_reports_unreadable_when_symlink_target_is_unqueryable(tmp_path, manifest_data):
    """U3-A r5 HIGH-1：`kind=file` 的链目标查不到时必须是三态 None，不能说成「不是文件」。

    `_entry_state` 是 lstat 语义，只覆盖「目录项本身查不到」；而 `is_file()` **跟随软链**
    且吞 OSError —— 链在、链目标查不到时它返回 False = 宣称「不满足 kind」，于是这一项
    从「故意不复制」翻成可放行，其余检查干净时可得 rc=0（假绿）。
    """
    target = tmp_path / "vault"
    blocked = target / "blocked"
    blocked.mkdir(parents=True)
    (blocked / "inner.txt").write_text("payload", encoding="utf-8")
    probe = target / "x"
    probe.symlink_to(blocked / "inner.txt")
    blocked.chmod(0o000)  # 目录不可搜索 ⇒ 跟随链后 stat 失败
    try:
        manifest_data["items"] = [
            {"path": "x", "role": "learning-data", "action": "exclude", "kind": "file", "origin": "test-only"}
        ]
        manifest_data["extra_allow"] = []
        mpath = tmp_path / "m.json"
        mpath.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
        result = vv.verify(target, vv.load_manifest(mpath))
        assert any(f.path == "x" for f in result.unreadable), (
            f"链目标查不到必须登记 unreadable，实得 unreadable={[(f.path, f.detail) for f in result.unreadable]} "
            f"intentionally_excluded={[f.path for f in result.intentionally_excluded]}"
        )
        assert result.exit_code == vv.EXIT_MISMATCH == 2, "查不动不得放行成 rc=0"
    finally:
        blocked.chmod(0o755)


def test_device_nodes_of_same_type_do_not_collide():
    """U3-A r5 HIGH-2：同类型设备节点必须靠 `st_rdev` 区分，否则不同对象判 match。

    只读取系统已有的字符设备（`lstat` + 摘要，不创建任何节点、不需要 root）。
    """
    import stat as _stat

    a, b = Path("/dev/null"), Path("/dev/zero")
    for p in (a, b):
        if not p.exists():
            pytest.skip(f"{p} 不存在，跳过设备节点判据")
    # 正控：两者确实是同类型（都是字符设备），否则这条门证明不了「同类型不碰撞」
    assert _stat.S_ISCHR(os.lstat(a).st_mode) and _stat.S_ISCHR(os.lstat(b).st_mode)
    da, _ = vv._leaf_digest(a)
    db, _ = vv._leaf_digest(b)
    assert da != db, f"两个不同的字符设备摘要相同（丢了 st_rdev）：{da} == {db}"
    assert da.startswith("?:") and db.startswith("?:"), (da, db)


def test_extra_scan_propagates_kind_unqueryable_instead_of_allowing(tmp_path, manifest_data):
    """U3-A r6 HIGH（旧 M2 升级）：extra 消费端必须把「类型判不了」带出来。

    `_collect_extra` 原先调 `is_under_exclusion(vault, rel)` **不传 unreadable**，于是
    `_kind_ok` 的 `None` 被压成「没被 exclude 覆盖」⇒ 条目落进 allowed-extra、
    阻断桶全空 ⇒ **rc=0 假绿**。exclude 遍历不跟随末级软链、没登记失败，而 extra
    遍历跟随它——两侧口径不同正是这个缺口的来源。
    """
    target = tmp_path / "vault"
    real = tmp_path / "real"
    real.mkdir()
    blocked = tmp_path / "blocked"  # ⚠️ 放在扫描面**之外**, 否则它自己会以 extra 身份进结果
    blocked.mkdir()
    (blocked / "inner.txt").write_text("payload", encoding="utf-8")
    target.mkdir()
    (target / "alias").symlink_to(real, target_is_directory=True)
    (real / "f.json").symlink_to(blocked / "inner.txt")
    blocked.chmod(0o000)  # 跟随 f.json 后 stat 失败 ⇒ _kind_ok 判不了类型
    try:
        manifest_data["items"] = [
            {"path": "alias/*json", "role": "learning-data", "action": "exclude", "kind": "file", "origin": "test-only"}
        ]
        manifest_data["extra_allow"] = ["alias/f*"]
        manifest_data["extra_scan"] = [{"dir": "alias", "match": "*"}]
        mpath = tmp_path / "m.json"
        mpath.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
        result = vv.verify(target, vv.load_manifest(mpath))
        assert result.unreadable != [], (
            f"类型判不了必须登记 unreadable，实得 allowed-extra={[f.path for f in result.allowed_extra]} "
            f"extra={[f.path for f in result.extra]}"
        )
        assert "alias/f.json" not in [f.path for f in result.allowed_extra], "判不了类型的条目不得放行进 allowed-extra"
        assert result.exit_code == vv.EXIT_MISMATCH == 2, "判不了不得收敛成 rc=0"
    finally:
        blocked.chmod(0o755)


def test_absent_exclude_with_kind_file_is_not_reported_unreadable(tmp_path, manifest_data):
    """U3-A r6 MEDIUM（我上一轮修法引入的误报）：**不存在**是确定的否定答案。

    `_resolved_kind` 只有四态、把 ENOENT/ENOTDIR 一律归 `unreadable`；上一轮给
    `kind=file` 接上它之后，一条本就不在目标里的 exclude 被误报成读取失败、rc=2。
    这是同一个错误第三次出现（round-4 修 `_entry_state` 的 ENOTDIR、round-5 新写
    `_resolved_kind` 时重犯、round-6 消费它时再犯）。
    """
    target = tmp_path / "vault"
    target.mkdir()
    manifest_data["items"] = [
        {"path": "x", "role": "learning-data", "action": "exclude", "kind": "file", "origin": "test-only"}
    ]
    manifest_data["extra_allow"] = []
    manifest_data["extra_scan"] = []
    mpath = tmp_path / "m.json"
    mpath.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
    result = vv.verify(target, vv.load_manifest(mpath))
    assert result.unreadable == [], (
        f"不存在的 exclude 项不得报成读取失败，实得 {[(f.path, f.detail) for f in result.unreadable]}"
    )
    assert result.exit_code == vv.EXIT_OK == 0, "一个本就不在目标里的 exclude 不该阻断"
