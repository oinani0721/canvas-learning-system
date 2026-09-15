"""验证新加的门**真能杀掉**变异测试里那批存活者。不验就只是信仰。

做法：在内存里把每个存活变异体打到 `_harness_tree` 上，然后按新门的**形状 × 缺库方式**
逐格跑，看是否至少有一格红（= KILLED）。全格绿 = 门仍然抓不住（= 我白加了）。
⛔ 只读仓库；变异只在内存里。
"""
import ast, builtins, json, os, re, sys, tempfile, pathlib

WT = pathlib.Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t7-skills")
txt = (WT / "canvas-vault/.claude/skills/quiz-answer/SKILL.md").read_text(encoding="utf-8")
CODE = [b for b in re.findall(r"python3 - <<'PYEOF'\n(.*?)\nPYEOF", txt, re.DOTALL)
        if 'P = "/tmp/quiz-answer-payload.json"' in b][0]
SRC = ast.get_source_segment(CODE, [n for n in ast.parse(CODE).body
                                    if isinstance(n, ast.FunctionDef) and n.name == "_harness_tree"][0])
ANCHOR = "PyYAML 不可用 — harness_tree 指向哪棵树不可证"

IMPORT_ERR_LINE = '        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree'


def make_fn(mutant_src):
    prelude = CODE[: CODE.index("def _harness_tree")]
    ns = {}
    for st in ast.parse(prelude).body:
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            exec(compile(ast.Module(body=[st], type_ignores=[]), "<p>", "exec"), ns)
    exec(mutant_src, ns)
    return ns["_harness_tree"]


def usable(root):
    (root / "backend" / "scripts").mkdir(parents=True, exist_ok=True)
    return root


def build(shape, base):
    vd = base / "canvas-vault"
    vd.mkdir(parents=True)
    cfg = vd / ".canvas-config.yaml"
    real = usable(base / "real-harness")
    env = {}
    if shape == "no_config_file":
        pass
    elif shape == "target_tree_really_exists":
        cfg.write_text(f'# c\nvault_id: "v"\nharness_tree: {real}\n', encoding="utf-8")
    elif shape == "parent_is_a_usable_tree":
        usable(base)
        cfg.write_text('# c\nvault_id: "v"\nsubject: cs-61b\n', encoding="utf-8")
    elif shape == "minimal_unquoted_config":
        cfg.write_text(f"subject: cs61b\nharness_tree: {real}\n", encoding="utf-8")
    elif shape == "pure_json_config":
        cfg.write_text(json.dumps({"subject": "cs61b", "harness_tree": str(real)}), encoding="utf-8")
    elif shape == "env_override_set":
        cfg.write_text('# c\nvault_id: "v"\nsubject: cs-61b\n', encoding="utf-8")
        env = {k: str(real) for k in ("QUIZ_ANSWER_HARNESS_TREE", "CANVAS_HARNESS_TREE", "HARNESS_TREE")}
    else:
        cfg.write_text('# c\nvault_id: "v"\nsubject: cs-61b\n', encoding="utf-8")
        (vd / ".canvas-config.harness-tree").write_text(str(real), encoding="utf-8")
    return vd, env


SHAPES = ["no_config_file", "target_tree_really_exists", "parent_is_a_usable_tree",
          "minimal_unquoted_config", "pure_json_config", "env_override_set", "sidecar_present"]
PROBES = ["module_not_found", "plain_import_error"]


def run_cell(fn, shape, probe):
    base = pathlib.Path(tempfile.mkdtemp(prefix="vk-"))
    vd, env = build(shape, base)
    saved_env = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    prev_mod = sys.modules.get("yaml")
    real_import = builtins.__import__
    if probe == "module_not_found":
        sys.modules["yaml"] = None
    else:
        def fake(name, *a, **kw):
            if name == "yaml":
                raise ImportError("cannot import name '_yaml' from partially initialized module 'yaml'")
            return real_import(name, *a, **kw)
        builtins.__import__ = fake
    try:
        out = ("ok", fn(str(vd)))
    except SystemExit as e:
        out = ("exit", str(e))
    except Exception as e:  # noqa: BLE001
        out = ("err", f"{type(e).__name__}: {e}")
    finally:
        builtins.__import__ = real_import
        if prev_mod is None:
            sys.modules.pop("yaml", None)
        else:
            sys.modules["yaml"] = prev_mod
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    # 新门的断言：必须 exit 且拒因含整句锚
    green = out[0] == "exit" and ANCHOR in out[1]
    return green, out


MUTANTS = {
    "R3-try-then-refuse": (
        IMPORT_ERR_LINE,
        '''        import re as _re2
        try:
            _raw2 = open(_cfg_p, encoding="utf-8").read()
        except OSError:
            _raw2 = ""
        _m2 = _re2.search(r"^harness_tree:[ ]+(\\S+)[ ]*$", _raw2, _re2.M)
        if _m2:
            try:
                _cand = os.path.realpath(_m2.group(1), strict=True)
                if os.path.isdir(os.path.join(_cand, "backend", "scripts")):
                    return _cand
            except OSError:
                pass
        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree''',
    ),
    "R6-env-override": (
        IMPORT_ERR_LINE,
        '''        _ev = os.environ.get("QUIZ_ANSWER_HARNESS_TREE") or os.environ.get("CANVAS_HARNESS_TREE")
        if _ev and os.path.isdir(os.path.join(_ev, "backend", "scripts")):
            return os.path.realpath(_ev)
        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree''',
    ),
    "M1-parent-is-a-tree": (
        IMPORT_ERR_LINE,
        '''        _par = os.path.dirname(vault_dir)
        if os.path.isdir(os.path.join(_par, "backend", "scripts")):
            return _par
        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree''',
    ),
    "R4-sidecar-cache": (
        IMPORT_ERR_LINE,
        '''        try:
            _sc = open(os.path.join(vault_dir, ".canvas-config.harness-tree"), encoding="utf-8").read().strip()
            if _sc and os.path.isdir(os.path.join(_sc, "backend", "scripts")):
                return os.path.realpath(_sc)
        except OSError:
            pass
        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree''',
    ),
    "R5-json-superset": (
        IMPORT_ERR_LINE,
        '''        try:
            _jd = json.load(open(_cfg_p, encoding="utf-8"))
            if isinstance(_jd, dict) and _jd.get("harness_tree"):
                return os.path.realpath(str(_jd["harness_tree"]))
        except Exception:
            pass
        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree''',
    ),
    "R1-simple-config-only": (
        IMPORT_ERR_LINE,
        '''        import re as _re3
        try:
            _lines3 = open(_cfg_p, encoding="utf-8").read().split("\\n")
        except OSError:
            _lines3 = []
        if all(_re3.match(r"^[A-Za-z_][A-Za-z0-9_]*: [^\\s\\"'#|>&*{}\\[\\],:]+$", _l) for _l in _lines3 if _l.strip()):
            for _l in _lines3:
                _mm = _re3.match(r"^harness_tree: (\\S+)$", _l)
                if _mm:
                    return os.path.realpath(_mm.group(1))
        raise SystemExit(f"[quiz-answer] PyYAML 不可用 — harness_tree''',
    ),
    "P2-open-before-import": ("    try:\n        import yaml  # harness_tree 解析: 与 F1 判定同一个理由\n        with open(_cfg_p, encoding=\"utf-8\") as _cf:\n            _doc = yaml.safe_load(_cf)",
                              "    try:\n        with open(_cfg_p, encoding=\"utf-8\") as _cf:\n            _txt0 = _cf.read()\n        import yaml  # harness_tree 解析: 与 F1 判定同一个理由\n        _doc = yaml.safe_load(_txt0)"),
    "WM-narrow-except": ("    except ImportError:", "    except ModuleNotFoundError:"),
    "WM-merge-message": (IMPORT_ERR_LINE,
                         '        raise SystemExit(f"[quiz-answer] .canvas-config.yaml 无法用 PyYAML 解析 — fail-closed 拒写 — 请人工修复 {_cfg_p}") or SystemExit(f"[quiz-answer] x — harness_tree'),
}

print("%-24s %-9s %s" % ("变异体", "判定", "被哪一格抓住"))
print("-" * 78)
n_killed = 0
for name, (old, new) in MUTANTS.items():
    if SRC.count(old) != 1:
        print("%-24s %-9s old_snippet 命中 %d 次" % (name, "INVALID", SRC.count(old)))
        continue
    mut = SRC.replace(old, new)
    try:
        fn = make_fn(mut)
    except SyntaxError as e:
        print("%-24s %-9s 语法错: %s" % (name, "INVALID", e))
        continue
    caught = []
    for sh in SHAPES:
        for pr in PROBES:
            green, out = run_cell(fn, sh, pr)
            if not green:
                caught.append(f"{sh}/{pr}")
    if caught:
        n_killed += 1
        print("%-24s %-9s %s" % (name, "KILLED", caught[0] + (f" (+{len(caught)-1})" if len(caught) > 1 else "")))
    else:
        print("%-24s %-9s %s" % (name, "SURVIVED", "⛔ 14 格全绿 —— 新门仍抓不住"))

print("-" * 78)
print("KILLED %d / %d" % (n_killed, len(MUTANTS)))

# 阴性对照：生产代码本身必须 14 格全绿（否则是新门误伤）
prod = make_fn(SRC)
bad = [(s, p) for s in SHAPES for p in PROBES if not run_cell(prod, s, p)[0]]
print("阴性对照（生产代码应 14 格全绿）:", "全绿 ✅" if not bad else f"⛔ 误伤 {bad}")
