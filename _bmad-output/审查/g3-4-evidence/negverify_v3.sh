#!/bin/zsh
# G3-4 负验证 v3 生成器 (Codex round-2 MEDIUM 整改: 内联 mutation 命令 + 准确计数
# + algorithm/.post 变体入档)。在 backend/ 下运行。
set -u
GATE=".venv/bin/python -m pytest tests/regression/test_fsrs_golden_vectors.py -q"
RESTORE=".venv/bin/python scripts/generate_fsrs_golden_vectors.py"

run_gate() { eval "$GATE" 2>&1 | grep -E "^FAILED|passed|failed"; echo "pytest-exit=${pipestatus[1]}"; }

mutate() {  # $1 = python 变异代码 (内联入档)
  echo "  mutation command:"
  echo "$1" | sed 's/^/    | /'
  .venv/bin/python -c "$1"
}

restore() { eval "$RESTORE" >/dev/null; echo "  restore command: $RESTORE"; }

echo "== G3-4 负验证存档 v3 (Codex round-2 整改: 内联 mutation 命令 + 准确计数) =="
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "git HEAD: $(git -C .. rev-parse HEAD) (branch $(git -C .. rev-parse --abbrev-ref HEAD))"
echo "  注: 本轮 round-2 整改尚未提交, 工作树 bytes 以下列 sha256 为准"
echo "python: $(.venv/bin/python -V); fsrs installed: $(.venv/bin/python -c 'from importlib.metadata import version; print(version(\"fsrs\"))')"
echo "test sha256:     $(shasum -a 256 tests/regression/test_fsrs_golden_vectors.py | cut -d' ' -f1)"
echo "manifest sha256: $(shasum -a 256 tests/regression/fsrs_golden_manifest.json | cut -d' ' -f1)"
echo "vectors sha256:  $(shasum -a 256 tests/regression/fsrs_golden_vectors.json | cut -d' ' -f1)"
echo "gate command (每变体同一命令): $GATE"
echo "变体总数: 1 基线 (N0) + 9 负例 (N1-N9)"
echo

echo "--- [N0] 基线 → 期望全绿 ---"; run_gate; echo

echo "--- [N1] manifest params_hash 首字符篡改 → 期望 params_hash_integrity 红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text());h=m["params_hash"]
m["params_hash"]=("0" if h[0]!="0" else "1")+h[1:]
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N2] 向量 stability +0.5 → 期望 replay_exact 红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][0]["expected"]["stability"]+=0.5
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N3] 仅改 manifest library_version=6.4.0 (GOLDEN 不动) → 期望 3 门红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text())
m["library_version"]="6.4.0"
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N4] 末向量替换为首向量副本 (重复+缺格) → 期望 matrix_structure 红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][-1]=d["vectors"][0]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N5] retrievability.at 清空 → 期望 matrix_structure 红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["retrievability"]["at"]=[]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N6] 容差放宽 float_rel=1e-3 → 期望 tolerance_ceiling 红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text())
m["comparison_tolerance"]["float_rel"]=1e-3
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N7] state_before_final_review=999 → 期望 matrix_structure + replay 双红 ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_vectors.json");d=json.loads(p.read_text())
d["vectors"][0]["state_before_final_review"]=999
p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N8] manifest algorithm 改任意值 → 期望 metadata_frozen 红 (round-1 曾全绿) ---"
mutate 'import json,pathlib
p=pathlib.Path("tests/regression/fsrs_golden_manifest.json");m=json.loads(p.read_text())
m["algorithm"]="arbitrary"
p.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n")'
run_gate; restore; echo

echo "--- [N9] requirements 改 fsrs==6.3.1.post1 → 期望 requirements_pin 红 (round-1 正则曾放过) ---"
echo "  mutation command:"
echo "    | sed -i '' 's/^fsrs==6.3.1$/fsrs==6.3.1.post1/' ../backend/requirements.txt"
sed -i '' 's/^fsrs==6.3.1$/fsrs==6.3.1.post1/' requirements.txt
run_gate
echo "  restore command: sed -i '' 's/^fsrs==6.3.1.post1$/fsrs==6.3.1/' ../backend/requirements.txt"
sed -i '' 's/^fsrs==6.3.1.post1$/fsrs==6.3.1/' requirements.txt
echo

echo "--- 终态: 恢复后 sha256 与基线一致性 + 全绿 ---"
echo "manifest sha256: $(shasum -a 256 tests/regression/fsrs_golden_manifest.json | cut -d' ' -f1)"
echo "vectors sha256:  $(shasum -a 256 tests/regression/fsrs_golden_vectors.json | cut -d' ' -f1)"
echo "requirements fsrs 行: $(grep -n '^fsrs==' requirements.txt)"
run_gate
