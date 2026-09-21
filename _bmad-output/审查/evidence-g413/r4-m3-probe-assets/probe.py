"""r4 M-3 变异探针：复跑 `r4-m3-mutation-probe-*.txt` 的判定。

变异体 = 把 runner 的 manifest 校验块挪到环境检查之后（见 mutants.diff）。
判定：① 加了 pin（alive=False）后，变异体让测试红（早期返回，无「不符」）；
      ② 没有 pin 的环境（alive=True）下，变异体与正确顺序**不可区分**（都「不符」+rc2）。
"""
import importlib.util, io, sys, contextlib, tempfile
from pathlib import Path

import yaml

LANE = Path("/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p9-testinfra")
SCRIPTS, REG = LANE / "backend" / "scripts", LANE / "backend" / "tests" / "regression"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

tool = load("gold_set_manifest_tool", SCRIPTS / "gold_set_manifest_tool.py")

# 篡改 manifest 副本：把 memory shadow 项的 sha 首字符翻一位
doc = tool.load_yaml(REG / "gold_set_manifest.yaml")
for e in doc["files"]:
    if e["path"].endswith("memory_gold_set_shadow.yaml"):
        e["sha256"] = ("0" if e["sha256"][0] != "0" else "1") + e["sha256"][1:]
tmp = Path(tempfile.mkdtemp()) / "tampered.yaml"
tmp.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
tool.MANIFEST_PATH = tmp

def run(runner, alive_flag, calls):
    def _alive():
        calls.append("alive")
        return alive_flag
    runner.check_backend_alive = _alive
    sys.argv = ["runner", "--shadow", "--no-judge"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = runner.main()
    return rc, buf.getvalue()

mem = load("run_memory_mut", Path(__file__).with_name("run_memory_mut.py"))
mem.SHADOW_SET, mem.GOLD_SET = REG / "memory_gold_set_shadow.yaml", REG / "memory_gold_set.yaml"

calls = []
rc, out = run(mem, False, calls)
pin_red = ("不符" not in out) and rc == 2 and "backend 不可达" in out
print(f"[变异体 + pin(alive=False)] rc={rc} 含不符={'不符' in out} 含不可达={'backend 不可达' in out} ⇒ pin 会红 = {pin_red}")

calls2 = []
rc2, out2 = run(mem, True, calls2)
indistinguishable = ("不符" in out2) and rc2 == 2
print(f"[变异体 + 无 pin(alive=True)] rc={rc2} 含不符={'不符' in out2} ⇒ 与正确顺序不可区分 = {indistinguishable}")
print(f"⇒ 结论：pin {'承重（两条都成立）' if (pin_red and indistinguishable) else '结论不成立，需复查'}")
