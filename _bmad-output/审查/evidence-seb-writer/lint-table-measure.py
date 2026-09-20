#!/usr/bin/env python3
"""CARD-SEB-WRITER-SUBSTRING-TMP: 把 lint 模块里**全部**与 start-exam-board 相关的
基线值实测一遍并按可直接粘贴的形态打印。

⛔ 存在的理由: 卡文 (d) 只点名了 BASELINE / ESCAPING_TMP_BASELINE /
MANAGED_FILE_DIGESTS 三张表, 实跑发现另有 4 张表(块指纹 / 可疑行 / 不透明 /
父目录散文)同样按**行号**钉 start-exam-board —— 本卡的改动让 Step 6.5 之后的行号
整体下移, 那 4 张表全部漂移。手写猜值必错, 一律实测后贴。

用法: cd backend && .venv/bin/python3 <此脚本>
"""
import sys

sys.path.insert(0, "tests/skills")

from skill_portability_lint import (  # noqa: E402
    DEFAULT_ROOT,
    _body_counts,
    bare_tmp,
    dynamic_tmp_join_lines,
    escaping_tmp_paths,
    managed_file_digests,
    opaque_tmp_lines,
    parent_dir_prose_lines,
    suspicious_tmp_lines,
    tmp_block_fingerprints,
    url_default_overridden_lines,
)

NAME = "start-exam-board"
text = (DEFAULT_ROOT / "skills" / NAME / "SKILL.md").read_text(encoding="utf-8")

c = _body_counts(text)
print(f"[BASELINE] tmp_all={c['tmp_all']} tmp_ns={c['tmp_ns']} bare={bare_tmp(c)} "
      f"p8011_all={c['p8011_all']} p8011_ns={c['p8011_ns']} "
      f"ask={c['ask_user_question']} mcp={c['mcp_tool']} claude_dir={c['claude_dir_ref']}")

print("\n[ESCAPING_TMP_BASELINE]")
for norm in sorted(n for _tok, n in escaping_tmp_paths(text)):
    print(f"        {norm!r},")

print("\n[SUSPICIOUS_TMP_LINES_BASELINE]")
print(f"    {sorted(no for no, _l in suspicious_tmp_lines(text))!r}")
for no, line in suspicious_tmp_lines(text):
    print(f"      # {no}: {line.strip()[:100]}")

print("\n[DYNAMIC_TMP_JOIN_BASELINE]")
print(f"    {sorted(no for no, _l in dynamic_tmp_join_lines(text))!r}")

print("\n[OPAQUE_TMP_BASELINE]")
for item in sorted(opaque_tmp_lines(text), key=lambda x: x[0]):
    print(f"        {item!r},")

print("\n[TMP_BLOCK_BASELINE]")
for fp in sorted(tmp_block_fingerprints(text)):
    print(f"        {fp!r},")

print("\n[URL_OVERRIDE_BASELINE]")
print(f"    {sorted(no for no, _l in url_default_overridden_lines(text))!r}")

print("\n[PARENT_DIR_PROSE_BASELINE]")
print(f"    {sorted(no for no, _l in parent_dir_prose_lines(text))!r}")

print("\n[MANAGED_FILE_DIGESTS]")
print(f'    "skills/{NAME}/SKILL.md": "{managed_file_digests(DEFAULT_ROOT)[f"skills/{NAME}/SKILL.md"]}",')
