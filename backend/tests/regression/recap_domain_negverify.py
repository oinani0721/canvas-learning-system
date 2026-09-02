#!/usr/bin/env python3
"""维护卡 B · 负验证（变异）脚本 —— 证明双向门是**承重**的，不是摆设。

⛔ 三条铁律，全部来自踩过的坑：
  1. **必须串行**（MEMORY `reference_mutation_script_serial_only`）：本脚本原地改
     被测文件再还原，并发跑会让 B 的还原把 A 的 mutation 写回，而测试照样全绿。
     脚本自带互斥锁，重入直接拒绝。
  2. **变体必须禁掉该性质的全部防线**（MEMORY `reference_mutation_must_disable_all_layers`）：
     只退化一层时纵深防御会让测试仍绿，从而误判「门非承重」去改本来正确的测试。
  3. **还原后必须与备份逐字节相同**——这道自检本身抓出过"还原不干净"。
  4. ⛔ **锚点匹配得上 ≠ 变异还禁得掉东西**（CARD-维护B-R3 两次踩中）：
     · survivor-18：改锚点时改成了"保留原串"，但端点早已在 `_range_ok` **内部**
       收集完毕，保留与否不影响上报 ⇒ **空变异**；
     · survivor-22：round-6 把 `html.unescape` 从 `_normalize_number_seps` 移进
       `_visible_text`，原变异锚点仍能匹配，但那一处已成冗余 ⇒ **空变异**。
     两次都是脚本报「变异后仍全绿 = 该门不承重」才暴露的 —— 若脚本当时选择
     静默跳过，它们会以「✅ 如期变红」的形式混进证据。
     **规则：每当一个性质的实现位置移动，所有指向旧位置的变异都必须重新审视；
     改锚点时不能只对齐文本形态，必须重新问一句「它现在还禁得掉什么」。**
  5. ⛔ **变异必须让被测物"判错"，不能让它"崩溃"**（round-10 新增，见 run_suite）：
     survivor-20 曾把正则换成无捕获组却保留 `r"\1"` replacement ⇒ `re.error`。
     测试红了，但那是**因崩溃红**。脚本现在显式识别并按失败计。

用法: python recap_domain_negverify.py   （无参数；退出码 0 = 全部如期变红）
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "canvas-vault/.claude/skills/board-recap/scripts/recap_scan.py"
PYTEST = ROOT / "backend/.venv/bin/pytest"
SUITE = "tests/regression/test_recap_scan_signals.py"
LOCK = Path(tempfile.gettempdir()) / "recap-domain-negverify.lock.d"

# 每条变体 = (名称, [(原文, 替换), ...], 期望至少变红的用例关键字)
# ⛔ 列表里给出的是**该性质的全部防线**，一次全禁——只禁一层会得到假绿。
MUTANTS: list[tuple[str, list[tuple[str, str]], str]] = [
    (
        "survivor-1 围栏闭合退回宽松判定（E1 全线：长度 + 尾随空白 两条一起禁）",
        [
            (
                'close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})[^\\S\\n]*$")',
                'close_re = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")',
            ),
            (
                'if (\n                mc\n                and mc.group("fence")[0] == fence[0]\n'
                '                and len(mc.group("fence")) >= len(fence)\n            ):',
                "if mc:",
            ),
        ],
        "four_fence_short_close or fence_close_needs_trailing_blank_only",
    ),
    (
        "survivor-2 规模行允许式去掉行尾锚（H-2 前半全线）",
        [
            (
                # ⛔ CARD-维护B-R2 (d): 允许式表已从 _verify_report 局部提为模块级
                # _FALLBACK_DERIVE_ALLOW，缩进 16→12 空格——锚点随之更新（变异性质不变）。
                'r"^[>\\s]*\\d+\\s*成员（\\d+\\s*种子\\s*\\+\\s*\\d+\\s*派生，\\d+\\s*占位）"\n            r"\\s*/\\s*\\d+\\s*批注\\s*/?\\s*$"',
                'r"^[>\\s]*\\d+\\s*成员（\\d+\\s*种子\\s*\\+\\s*\\d+\\s*派生，\\d+\\s*占位）"',
            )
        ],
        "scale_line_tail_append",
    ),
    (
        "survivor-3 种子行只查形状不绑值（H-2 后半全线）",
        [("    _verify_seed_ledger_counts(text, scan, problems)\n", "")],
        "seed_ledger_fake_count",
    ),
    (
        "survivor-4 信号行尾部退回开放式 + 恢复字符黑名单（H-3 全线）",
        [
            (
                "rf\"{sig['denominator']}\\s*{re.escape(tail)}\"",
                "rf\"{sig['denominator']}\\s*(?P<tail>[^【】]*)\"",
            )
        ],
        "signal_tail_append",
    ),
    (
        "survivor-5 D2 叙述域计数绑定整体关闭（本卡原始命题）",
        [("    _verify_prose_counts(text, scan, problems)\n", "")],
        "bare_count_in_prose",
    ),
    # ── CARD-维护B-R2 (g): 第七批复核 F-4 的三个 survivor + 本卡两处新面的承重变体。
    # 每条的 keyword 都指向 (b)-(e) 配的新承重门；隔离拷贝重放证据见验收单 4-A。
    (
        "survivor-6 S1 `_NODATA_REASONS` 增「任意原因」（F-4: 既有门只喂固定 bogus）",
        [('    "数据源不可用",\n)', '    "数据源不可用",\n    "任意原因",\n)')],
        "skill_sync_nodata_reasons_table or nodata_reason_outside_table",
    ),
    (
        "survivor-7 S3 围栏剥离退回单层（F-4: `> > ```` 逃逸 + Obsidian 渲染引用内代码块）",
        [
            (
                # ⛔ CARD-维护B-R2 round-3 锚点更新: bare 现为「引用+无序/有序/多层
                # 列表 marker」交替剥法 + 列表容器边界跟踪。变异性质不变——退回
                # "只剥一层引用"形态时, c1/c2/列表项围栏/r3 门都应变红。
                "        bare = re.sub(\n"
                '            r"^(?: {0,3}(?:>[^\\S\\n]?|(?:[-*+]|\\d{1,9}[.)])[^\\S\\n]{1,4}))*", "", ln\n'
                "        )",
                '        bare = re.sub(r"^>?[^\\S\\n]*", "", ln)',
            )
        ],
        "multilevel_blockquote_fence or strip_code_blocks_unit_contract or list_item_fence",
    ),
    (
        "survivor-8 S4 允许式表增「备注：…派生」自由式（F-4: 无依据可写的模式混入）",
        [
            (
                '        "skill:③段固定句式",\n    ),\n)',
                '        "skill:③段固定句式",\n    ),\n'
                '    (re.compile(r"^\\s*备注[：:].*派生.*$"), "skill:③段固定句式"),\n)',
            )
        ],
        "freeform_derivation_note or derive_allow_entries_are_grounded",
    ),
    (
        "survivor-9 (e) 注记槽退化为自由文本（H-3「先开放再排除」黑名单老路复活）",
        [
            (
                "            note_slot = (\n"
                '                rf"(?:\\s*[·，,、]?\\s*"\n'
                "                rf\"(?:{'|'.join(re.escape(x) for x in _SIGNAL_TAIL_NOTES)}))?\"\n"
                "            )",
                '            note_slot = r"(?:[^【】]*)"',
            )
        ],
        "signal_tail_note_outside_table",
    ),
    (
        "survivor-10 (e) `_SIGNAL_TAIL_NOTES` 增「另有仨条」（封闭表被单侧扩表）",
        [
            (
                '_SIGNAL_TAIL_NOTES = ("口径一致",)',
                '_SIGNAL_TAIL_NOTES = ("口径一致", "另有仨条")',
            )
        ],
        "skill_sync_signal_tail_notes_table",
    ),
    # ── CARD-维护B-R3 (e): C「中文数词终态」的两条承重变体 ──
    # round-5 HIGH 的两个可失效面各配一条: ①判据本身退回多位文法解析器;
    # ②提取面收窄导致多字串根本不进检查面 (漏拦冒充 fail-closed)。
    # D2 叙述段与 fallback 允许式**共用同一判据/同一提取常量**, 故每条变体
    # 改一处即禁掉该性质的**全部**防线 (脚本铁律 2)。
    (
        "survivor-11 (C) 判据退回多位解析器（round-5 HIGH 全线：两侧共用判据，一处即全禁）",
        [
            (
                "    return _CJK_NUM.get(s) if len(s) == 1 else None",
                "    total, section, digit, seen = 0, 0, None, False\n"
                "    for ch in s:\n"
                "        if ch in _CJK_NUM:\n"
                "            digit = _CJK_NUM[ch]\n"
                "            seen = True\n"
                "        elif ch in _CJK_UNIT:\n"
                "            unit = _CJK_UNIT[ch]\n"
                "            if unit >= 10000:\n"
                "                section = (section + (digit or 0)) if (section or digit) else 1\n"
                "                total += section * unit\n"
                "                section, digit = 0, None\n"
                "            else:\n"
                "                section += (digit if digit is not None else 1) * unit\n"
                "                digit = None\n"
                "            seen = True\n"
                "        else:\n"
                "            return None\n"
                "    if not seen:\n"
                "        return None\n"
                "    return total + section + (digit or 0)",
            )
        ],
        "r5_cjk or r5_derive or r5_prose or r4_derive_allow_cjk",
    ),
    (
        "survivor-12 (C) 提取面收窄成单字（「抓得到才拒得掉」全线：唯一提取模式被禁）",
        [
            (
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}](?:{_D2_JOIN_ONE}*+[{_NUMERAL_LIKE_CHARS}])*"',
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}]"',
            )
        ],
        "r5_cjk or r5_derive or r5_prose or r5_noise or r4_derive_allow_cjk",
    ),
    # ── R3 round-2 (车道对抗审查 1B+4H): 连接语义的承重变体 ──
    (
        "survivor-13 (C-2) 数串不再跨连接字符（CJK 与 ASCII 两侧提取面一起禁）",
        [
            (
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}](?:{_D2_JOIN_ONE}*+[{_NUMERAL_LIKE_CHARS}])*"',
                '_NUM_RUN_PAT = rf"[{_NUMERAL_LIKE_CHARS}]+"',
            ),
        ],
        "r5_noise_split",
    ),
    (
        "survivor-14 (C-2) 剥噪声还原被禁（_join_free 变恒等：token 带着噪声去判/查池）",
        [('    return _D2_JOIN_RE.sub("", s)', "    return s")],
        "r5_noise_split or r5_prose_single_char or r5_cjk",
    ),
    # ── R3 round-3 (Codex round-2 四条 HIGH): 统一取数规则的三条承重变体 ──
    (
        "survivor-15 (C-3) 判值放宽为「取末位字」（表内单字判据被禁：廿五/一零 被赋值）",
        [
            (
                "    return _cjk_single_to_int(token)",
                "    return _CJK_NUM.get(token[-1])",
            )
        ],
        "r6_cross_class or r5_prose or r5_derive",
    ),
    (
        "survivor-16 (C-3) 定界集退回窄集合（表外数词字不进提取面 ⇒ 从尾片重锚）",
        [
            (
                'sorted(set(_CJK_NUM_CHARS) | set(_CJK_NUM_EXTRA) | set("0123456789"))',
                'sorted(set(_CJK_NUM_CHARS) | set("0123456789"))',
            )
        ],
        "r6_cross_class",
    ),
    (
        "survivor-17 (C-3) CJK 小数形态检查被摘除（五点五个 / 5点5个 拆成两个 5 碰池）",
        [
            (
                "            for m_dec in _CJK_DECIMAL_RE.finditer(line):",
                "            for m_dec in ():",
            )
        ],
        "r6_cross_class",
    ),
    # ── R3 round-4 (Codex round-3 三条 HIGH): 区间端点与 fallback 前处理 ──
    (
        "survivor-18 (C-4) 区间端点不再逐个上报、无出处时保留原串交给后面「逐个判」"
        "（而后面的循环只取紧邻量词的一端 ⇒ 另一端免检）",
        [
            (
                "                for raw in (mm.group(1), mm.group(2)):\n"
                "                    tok = _join_free(raw)\n"
                "                    val = _count_token_value(tok)\n"
                "                    if val is None or val not in pool:\n"
                "                        bad_ends.append(tok)\n"
                '                return " " * len(mm.group(0))',
                "                ends = [\n"
                "                    _count_token_value(_join_free(x))\n"
                "                    for x in (mm.group(1), mm.group(2))\n"
                "                ]\n"
                "                return (\n"
                '                    " " * len(mm.group(0))\n'
                "                    if all(e is not None and e in pool for e in ends)\n"
                "                    else mm.group(0)\n"
                "                )",
            )
        ],
        "r7_range or r8_entities",
    ),
    (
        "survivor-19 (C-4) fallback 的千分位归一与小数防线被摘除（退回对原行直接 findall 逐片入池）",
        [
            (
                "            norm = _normalize_number_seps(_visible_text(ln))\n"
                "            for m_dec in _DECIMAL_ANY_RE.finditer(norm):",
                "            norm = _visible_text(ln)\n            for m_dec in ():",
            )
        ],
        "r7_range",
    ),
    (
        "survivor-20 (C-4→8) 千分位只认半角逗号且两侧不容连接字符"
        '；⚠️ 原版把 pattern 换成**无捕获组** lookaround 却保留生产的 `r"\\1"` '
        "replacement ⇒ 调用即 `re.error: invalid group reference`，"
        "「变红」是**因崩溃**而非因漏拦（Codex round-8 HIGH-7，车道复现属实）。"
        "**异常伪红比不变红更坏**：它会以「✅ 如期变红」混进证据。"
        "现改为保留捕获组、只收窄字符集，代码仍可运行。",
        [
            (
                'rf"([0-9]){_D2_JOIN_ONE}*[,，\'’]{_D2_JOIN_ONE}*(?=[0-9]{{3}}(?![0-9]))"',
                'r"([0-9]),(?=[0-9]{3}(?![0-9]))"',
            ),
        ],
        "r7_range",
    ),
    # ── R3 round-5 (Codex round-4 七条 HIGH): 四条承重变体 ──
    # ⛔ Codex 指出 survivor-19/20 各组合多个替换共用一个测试函数,
    # 「变红」只能证明每个组合**至少一项**承重。下面四条**逐条单一性质**,
    # 各自对应一个独立的 -k 关键字, 便于分辨。
    (
        "survivor-21 (C-5) 句式判定改回取自**挖空之后**的行（裸『总计』自陈失锚）",
        [
            (
                "            is_claim = bool(_D2_CLAIM_RE.search(line))",
                "            is_claim = False",
            )
        ],
        "r8_entities",
    ),
    (
        "survivor-22 (C-5→6) HTML 字符实体不再规范化（&#46; / &#20010; / &#xff19; 重新免检）"
        "；⚠️ round-6 把该性质从 _normalize_number_seps 移进了 _visible_text，"
        "原变异随之变成**空变异**（锚点仍在但已禁不掉任何东西），锚点已重指",
        [
            (
                "    line = html.unescape(line)",
                "    line = line  # MUTANT-22: 不解实体",
            )
        ],
        "r8_entities or r9_visible",
    ),
    (
        "survivor-23 (C-5) 小数式左侧数串改回必需（`.5个` / `．五个` 重新免检）",
        [
            (
                '_DECIMAL_ANY_RE = re.compile(rf"(?:{_NUM_RUN_PAT})?{_DECIMAL_SEP}{_NUM_RUN_PAT}")',
                '_DECIMAL_ANY_RE = re.compile(rf"{_NUM_RUN_PAT}{_DECIMAL_SEP}{_NUM_RUN_PAT}")',
            ),
            (
                'rf"((?:{_NUM_RUN_PAT})?{_DECIMAL_SEP}{_NUM_RUN_PAT}){_D2_JOIN_ONE}*(?={_D2_QUANT})"',
                'rf"({_NUM_RUN_PAT}{_DECIMAL_SEP}{_NUM_RUN_PAT}){_D2_JOIN_ONE}*(?={_D2_QUANT})"',
            ),
        ],
        "r8_entities",
    ),
    (
        "survivor-24 (C-5) 区间端点改回裸 int() 且不共用数串式（中文/连接字符端点免检）",
        [
            (
                "                for raw in (mm.group(1), mm.group(2)):\n"
                "                    tok = _join_free(raw)\n"
                "                    val = _count_token_value(tok)\n"
                "                    if val is None or val not in pool:\n"
                "                        bad_ends.append(tok)",
                '                for raw in re.findall(r"[0-9]+", mm.group(0)):\n'
                "                    if int(raw) not in pool:\n"
                "                        bad_ends.append(raw)",
            )
        ],
        "r8_entities",
    ),
    # ── R3 round-6 (Codex round-5 八条实现 HIGH): 五条**逐条单一性质**的变体 ──
    (
        "survivor-25 (C-6) 渲染归一整体停用（_visible_text 变恒等：实体/标签/wikilink/零宽全部复活）",
        [
            (
                "    line = html.unescape(line)",
                "    return line",
            )
        ],
        "r9_visible",
    ),
    (
        "survivor-26 (C-6) 解实体晚于全角转换（&#xff19; 停在全角 ９，永远转不成 ASCII）",
        [
            (
                "    line = html.unescape(line)",
                "    line = line  # MUTANT-26",
            ),
            (
                "    line = line.translate(_FULLWIDTH_DIGITS)",
                "    line = line.translate(_FULLWIDTH_DIGITS)\n    line = html.unescape(line)",
            ),
        ],
        "r9_visible",
    ),
    (
        "survivor-27 (C-6) 句式门退回只认 ASCII 数字（裸『总计五个/总计：N』整句不进检查面）",
        [
            (
                'rf"|(?:共有|总计|合计)[\\s：:]*[{_NUMERAL_LIKE_CHARS}]"',
                'r"|(?:共有|总计|合计)\\s*[0-9]"',
            )
        ],
        "r9_visible",
    ),
    (
        "survivor-28 (C-6→14) 负数计数检查被摘除（`-5个` 按 +5 入池）",
        [
            (
                '                if re.search(rf"{_NEG_SIGN}{_D2_JOIN_ONE}*$", line[: m_cnt.start(1)]):',
                "                if False:",
            )
        ],
        "r9_visible",
    ),
    (
        "survivor-29 (C-6→8) 无别名 wikilink 不再取显示文本（`[[987654]]个` 的可见计数被藏起来）"
        "；⚠️ round-8 把 wikilink 处理整个移进 _visible_text 并删掉了旧常量，"
        "原变异随之变成**空变异**（第三次同型），锚点已重指到活实现",
        [('    line = _VIS_WIKILINK_PLAIN_RE.sub(r"\\1", line)\n', "")],
        "r9_visible or r10_ordering",
    ),
    (
        "survivor-30 (C-6) 归一器无条件剥 `~`（合法区间 `2~3个` 被拼成 23 ⇒ **误伤**; "
        "`987654~0个` 的区间分支同时失效）—— 车道 round-6 自己引入过的回归",
        [('_VIS_STRIKE_RE = re.compile(r"~~")', '_VIS_STRIKE_RE = re.compile(r"~")')],
        "r9_visible",
    ),
    # ── R3 round-8 (Codex round-6 七条实现 HIGH): 逐条单一性质 ──
    (
        "survivor-31 (C-8) wikilink 挖空退回豁免链（跑在 _visible_text 之前 ⇒ 有别名链接只剩 `|N]]`）",
        [
            (
                "        body = _D2_CODE_SPAN_RE.sub(_blank_inline_code, body)\n",
                "        body = _D2_CODE_SPAN_RE.sub(_blank_inline_code, body)\n"
                '        body = re.compile(r"\\[\\[[^\\]\\n|]*(?=\\|)").sub(lambda mm: " " * len(mm.group(0)), body)\n',
            )
        ],
        "r10_ordering",
    ),
    (
        "survivor-32 (C-8) fallback 退回在**源码行**上选行（`派**生**` 整行不进检查面）",
        [
            (
                '        if "派生" in vis and heading_pat.match(vis):\n'
                '            tags.append(("标题", heading_pat))\n'
                "        if relation_pat.match(vis):",
                '        if "派生" in ln and heading_pat.match(ln):\n'
                '            tags.append(("标题", heading_pat))\n'
                "        if relation_pat.match(ln):",
            )
        ],
        "r10_ordering",
    ),
    (
        "survivor-33 (C-8→14) fallback 负数守卫被摘除（`-5` 按 +5 入池，D2 侧仍在）",
        [
            (
                "            for m_neg in re.finditer(\n"
                '                rf"{_NEG_SIGN}{_D2_JOIN_ONE}*({_NUM_RUN_PAT})", norm\n'
                "            ):",
                "            for m_neg in ():",
            )
        ],
        "r10_ordering",
    ),
    (
        "survivor-34 (C-8) Markdown link 不再取显示文本（`总[计](u)N个` 句式门失锚）",
        [('    line = _VIS_MDLINK_RE.sub(r"\\1", line)\n', "")],
        "r10_ordering",
    ),
    # ── R3 round-9 (Codex round-7 实现侧): 三条逐条单一性质 ──
    (
        "survivor-35 (C-9) 全文『派生』门退回在**源码行**上判（`派**生**` 整行绕过全文门）",
        [
            (
                "            vis_ln = _visible_text(ln)\n"
                '            if "派生" in vis_ln and not any(\n'
                "                p.match(vis_ln) for p, _ in _FALLBACK_DERIVE_ALLOW\n"
                "            ):",
                '            if "派生" in ln and not any(\n'
                "                p.match(ln) for p, _ in _FALLBACK_DERIVE_ALLOW\n"
                "            ):",
            )
        ],
        "r11_fulltext",
    ),
    (
        "survivor-36 (C-9) 定界集去掉可见数字（带圈/苏州码 ⇒ 一个 token 都抽不出、整句零校验）",
        [
            (
                '    "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"\n    "〡〢〣〤〥〦〧〨〩〸〹〺"\n',
                "",
            )
        ],
        "r11_fulltext",
    ),
    (
        "survivor-37 (C-9) 负号守卫去掉中文『负』（`负五个` 按 +5 入池）",
        [
            (
                '_NEG_SIGN = r"(?:[-−－‑﹣]|负)"',
                '_NEG_SIGN = r"[-−－‑﹣]"',
            )
        ],
        "r11_fulltext",
    ),
    (
        "survivor-40 (C-14) inline-code 守卫的数字部分退回手写 `[0-9]+`"
        "（`九十八万个`/`987654 个` 等完整可见计数写进 code span 即整域免检）",
        [
            (
                '_D2_COUNTISH_CHARS = _NUMERAL_LIKE_CHARS + _D2_QUANT.strip("[]")',
                '_D2_COUNTISH_CHARS = "0123456789" + _D2_QUANT.strip("[]")',
            )
        ],
        "r12_no_silent",
    ),
    (
        "survivor-41 (C-15) 全文零宽门退回手抄集合（只到 U+2064 ⇒ bidi isolate U+2065-2069 过门）",
        [
            (
                "    if re.search(_INVISIBLE_ONE, text):",
                '    if re.search(r"[\\u200b-\\u200f\\u202a-\\u202e\\u2060-\\u2064\\ufeff]", text):',
            )
        ],
        "r12_no_silent",
    ),
    (
        "survivor-39 (C-12) reference-style link 不再取显示文本（`总[计][r]N个` 句式门失锚）",
        [('    line = _VIS_REFLINK_RE.sub(r"\\1", line)\n', "")],
        "r10_ordering",
    ),
    (
        "survivor-38 (C-8) 小数分隔符两侧不再容连接字符（原与千分位混成组合变异，现拆开单测）",
        [
            (
                '_DECIMAL_SEP = rf"{_D2_JOIN_ONE}*[.．点]{_D2_JOIN_ONE}*"',
                '_DECIMAL_SEP = r"[.．点]"',
            )
        ],
        "r8_entities",
    ),
    (
        "survivor-42 (C-13) shortcut reference link 不再取显示文本（`总[计]N个` 句式门失锚）",
        [('    line = _VIS_SHORTCUT_LINK_RE.sub(r"\\1", line)\n', "")],
        "r13_shortcut",
    ),
    (
        "survivor-43 (C-16) 区间首端守卫去掉（`-2~3个`/`2.2~3个` 从符号后重新起锚，整段挖空后负号与小数门再也看不到）",
        [
            (
                "                _pre = _RANGE_LEFT_BAD_RE.search(line[: mm.start(1)])\n"
                "                if _pre:\n"
                "                    bad_range_ctx.append(_pre.group(0) + mm.group(0))\n"
                '                    return " " * len(mm.group(0))\n',
                "",
            )
        ],
        "r14_range_left",
    ),
    (
        "survivor-44 (C-17) inline-code 豁免退回 raw 判据（不先归一 ⇒ 符号/小数/千分位/全角写进 code span 即整域免检）",
        [
            (
                '    if _codespan_is_visible_count(span[1:-1]):\n        return " " + span[1:-1] + " "\n',
                "",
            )
        ],
        "r14_range_left",
    ),
    (
        "survivor-45 (C-18) ③段信号行退回 raw 选行（label 被 `**`/`<b>` 切开的冲突行整条逃逸「逐条全查」）",
        [
            (
                "        lines = [v for v in _visible_block(s3).splitlines() if label in v]",
                '        lines = re.findall(rf"^.*{label}.*$", s3, re.M)',
            )
        ],
        "r15_signal_line",
    ),
    (
        "survivor-46 (C-19) ⑦前置 N 绑定退回 raw 行（白名单在渲染文本上放行、N 绑定在源码行上跳过 ⇒ 夹缝）",
        [("        mm = m7.match(_visible_text(ln))", "        mm = m7.match(ln)")],
        "r16_clause7",
    ),
    (
        "survivor-47 (C-20) 区间首端守卫要求小数点前必须有数词（`.2~3个`/`．二~三个`/`点二~三个` 从小数点后重锚）",
        [
            (
                'rf"(?:{_NEG_SIGN}|[{_NUMERAL_LIKE_CHARS}]?{_D2_JOIN_ONE}*[.．点]){_D2_JOIN_ONE}*$"',
                'rf"(?:{_NEG_SIGN}|[{_NUMERAL_LIKE_CHARS}]{_D2_JOIN_ONE}*[.．点]){_D2_JOIN_ONE}*$"',
            )
        ],
        "r17_freeze",
    ),
    (
        "survivor-48 (C-21) code span 字符域去掉**全部**区间分隔面"
        "（含 _D2_COUNTISH_EXTRA 自带的横线 —— 只清 _D2_RANGE_SEPS 时它们仍在，"
        "变异名比实际范围宽，round-21 冻结审查 v3 指出）"
        "（`` `999~999个` `` 被当字段值整段挖空，区间门与数字门都不可达）",
        [
            (
                '_D2_RANGE_SEPS = "~～〜-－−‑—–到至"\n_D2_COUNTISH_EXTRA = "-−－‑﹣负.．,，\'’" + _D2_RANGE_SEPS',
                '_D2_RANGE_SEPS = ""\n_D2_COUNTISH_EXTRA = "﹣负.．,，\'’" + _D2_RANGE_SEPS',
            )
        ],
        "r17_freeze",
    ),
    (
        "survivor-49 (C-22) code span 空白域退回字面空格+tab（NBSP 让整段被豁免）",
        [
            (
                "        ch in _D2_COUNTISH_CHARS or ch in _D2_COUNTISH_EXTRA or ch.isspace()",
                '        ch in _D2_COUNTISH_CHARS or ch in _D2_COUNTISH_EXTRA or ch in " \\t"',
            )
        ],
        "r17_freeze",
    ),
    (
        "survivor-50 (C-23) 五元组退回 raw 全文 findall（双行逃逸：正确行 + 渲染等价冲突行）",
        [
            (
                "    scale_hits = scale_pat.findall(_visible_block(text))",
                "    scale_hits = scale_pat.findall(text)",
            )
        ],
        "r17_freeze",
    ),
    (
        "survivor-51 (C-24) 种子小节的逐行归一退回 raw（vis_lines = raw_lines）"
        "⚠️ round-31 归因更正（冻结审查 v11/v12 两轮点名）：它变红的**实际原因**是"
        "「合法的渲染等价行被非模板门误拒」（误伤面），**不是**「冲突行逃逸」——"
        "恶意行在退回 raw 后仍会被非模板 fail-closed 门拦下。"
        "所以它证明的是：渲染空间比对这一步是活的",
        [
            (
                "    vis_lines = [_visible_text(_ln) for _ln in raw_lines]",
                "    vis_lines = raw_lines",
            )
        ],
        "r20_seed_ledger",
    ),
    (
        "survivor-52 (C-25) 种子节点身份退回「归一名对 raw node_id」（`Seed_A` 归一成 `SeedA` ⇒ 误拒 + 值绑定被跳过）",
        [
            (
                "        raw_ms = _SEED_LEDGER_LINE_RE.match(raw_ln)",
                "        raw_ms = None",
            )
        ],
        "r21_seed_node_identity",
    ),
    (
        "survivor-53 (C-26) 围栏前缀剥离退回吃掉任意缩进（四空格伪围栏 ⇒ 其后可见计数整段免检）",
        [
            (
                '            r"^(?: {0,3}(?:>[^\\S\\n]?|(?:[-*+]|\\d{1,9}[.)])[^\\S\\n]{1,4}))*", "", ln',
                '            r"^(?:[>\\s]|(?:[-*+]|\\d{1,9}[.)])[^\\S\\n]+)*", "", ln',
            )
        ],
        "r22_fence_indent",
    ),
    (
        "survivor-54 (C-27) 种子小节不再限定在『台账』之下（附录同名小节被强制套模板）",
        [
            (
                "        if _under_ledger and _H3_SEED_RE.match(vis_lines[_i]):",
                "        if _H3_SEED_RE.match(vis_lines[_i]):",
            )
        ],
        "r22_fence_indent",
    ),
    (
        "survivor-55 (C-28) 种子小节的围栏判定整体失效（_in_fence 恒 False）"
        "⚠️ round-31 归因更正：替换是 `_stripped = text.splitlines()`，效果是**所有行都不算在围栏内**，"
        "**不是**「退回手抄布尔翻转」；它变红来自 fenced-seed 被误当台账行（误伤面）",
        [
            (
                "    _stripped = _strip_code_blocks(text).splitlines()",
                "    _stripped = text.splitlines()",
            )
        ],
        "r23_seed_scope",
    ),
    (
        "survivor-56 (C-29) 种子绑定索引退回摊平全部角色（派生节点混进种子小节即通过）"
        "⚠️ round-30 归因更正：上一版只把 seeds 置 None，生产随即报「缺 seeds」并返回，"
        "**完全没有摊平**——红来自 fail-closed 而非名称所称的行为。现改为**两步替换**："
        "先把 fail-closed 分支换回摊平，再置 None，才真正复现该行为",
        [
            (
                "            problems.append(\n"
                '                "数字终核: scan JSON 的 ledger 是分组形态但缺少可用的 seeds 列表, "\n'
                '                "台账『种子』行无法绑定 (不回落到其它角色, 避免派生节点冒充种子)"\n'
                "            )\n"
                "            return",
                "            for grp in groups.values():\n"
                "                if isinstance(grp, list):\n"
                "                    rows.extend(x for x in grp if isinstance(x, dict))",
            ),
            (
                '        seeds = groups.get("seeds")',
                "        seeds = None",
            ),
        ],
        "r23_seed_scope",
    ),
    (
        "survivor-57 (C-30) 顶层围栏闭合重新允许列表 marker（块内 `- ``` ` 误当闭栏 ⇒ 其后可见正文被剥到 EOF）",
        [
            (
                "            if fence_list_col is None:\n"
                '                bare_close = re.sub(r"^(?: {0,3}>[^\\S\\n]?)*", "", ln)\n'
                "            else:\n"
                "                bare_close = bare",
                "            bare_close = bare",
            )
        ],
        "r24_fence_closer",
    ),
    (
        "survivor-58 (C-31) 尾巴同名字段重新排除全部汉字前缀（`累计/共/已批注 N 条` 放过）",
        [
            (
                'for _n in re.findall(r"(?<!未)批注\\s*(\\d+)\\s*条", rest):',
                'for _n in re.findall(r"(?<![\\u4e00-\\u9fff])批注\\s*(\\d+)\\s*条", rest):',
            )
        ],
        "r24_fence_closer",
    ),
    (
        "survivor-59 (C-32) 种子小节的段落标题口径退回自造式（与 _SECTION_RE 分叉）",
        [
            (
                '    _H2_LEDGER_RE = re.compile(_SECTION_RE("## 台账"))',
                '    _H2_LEDGER_RE = re.compile(r"^ {0,3}##[^\\S\\n]+台账[^\\S\\n]*$")',
            )
        ],
        "r25_section_criterion",
    ),
    (
        "survivor-60 (C-33) 小节终点扫描不再判围栏（围栏内假标题提前截断小节）",
        [
            (
                '                not _in_fence[_j] and re.match(r"^#{2,3}[^\\S\\n]", vis_lines[_j])',
                '                re.match(r"^#{2,3}[^\\S\\n]", vis_lines[_j])',
            )
        ],
        "r25_section_criterion",
    ),
    (
        "survivor-61 (C-34) H3 找不到种子小节时退回静默 return"
        "（H2 有全局必需段门兜底，H3 没有 ⇒ 不合口径的 `### 种子 ###` 整块不受绑定）",
        [
            (
                '        if _seed_rows and re.search(_SECTION_RE("## 台账"), text, re.M):\n            problems.append(',
                "        if False:\n            problems.append(",
            )
        ],
        "r25_section_criterion",
    ),
    (
        "survivor-62 (C-35) 零种子板的空绑定面提前 return（板里写的台账行被静默放行）",
        [
            (
                "        # ⚠️ `seeds == []` 时**不能提前 return**",
                "        return\n        # ⚠️ `seeds == []` 时**不能提前 return**",
            )
        ],
        "r26_zero_seed",
    ),
    (
        "survivor-63 (C-36) 台账段内『认可小节之外的台账形状行』不再报"
        "（第六/第七形态：不合规 H3 底下装台账行，整块排除在审计面外）",
        [
            (
                "            if _k in _covered or _in_fence[_k] or not _bad_h3[_k]:",
                "            if True:",
            )
        ],
        "r27_seedish_h3",
    ),
    (
        "survivor-64 (C-37) 损坏的 ledger.seeds（含非对象条目）退回被当合法零种子",
        [
            (
                "        if isinstance(_raw_seeds, list) and any(",
                "        if False and isinstance(_raw_seeds, list) and any(",
            )
        ],
        "r27_seedish_h3",
    ),
    (
        "survivor-65 (C-38) tips 两数的绑定退回 raw 文本（保留正确行 + 追加渲染等价冲突行 ⇒ 绑定器看不到）",
        [
            (
                "        in_sec = re.findall(pat, _visible_block(recon.group(1)))\n"
                "        all_hits = re.findall(pat, _visible_block(text))",
                "        in_sec = re.findall(pat, recon.group(1))\n        all_hits = re.findall(pat, text)",
            )
        ],
        "r28_tips_binding",
    ),
]


def _crash_text(stdout: str, stderr: str | None) -> str:
    """崩溃分析的**输入面**: stdout + stderr 一起看。

    提成纯函数是为了让"有没有把 stderr 丢掉"能被行为门直接测 ——
    藏在 run_suite 里就只能靠读源码, 而 transport 缺失**不会**让任何测试变红。
    """
    return stdout + "\n" + (stderr or "")


def _looks_like_crash(out: str) -> bool:
    """pytest 输出 → 这次「变红」是不是**崩溃**造成的（而非判错）。

    提成纯函数是为了能被 `test_recap_scan_signals.py` 逐形态单测 ——
    藏在 `run_suite` 里就只能靠肉眼，而崩溃伪红**唯一的症状就是显示 ✅**。

    ⚠️ **能力边界（round-21 如实声明，不再自称可靠二分）**：
      · **确定性**的那一半：子进程崩溃由测试侧在源头打 `[[CHILD-CRASH]]` 标记，
        标记出现即判崩溃 —— 不依赖任何渲染格式；
      · **启发式**的那一半：解析外层 pytest 渲染（缩进上界 + assert 白名单），
        绑定 `backend/pytest.ini` 当前的 `--tb=short`。它**会**漏（内层无
        traceback 的崩溃、致命信号）**也会**误报（正文偶然含 traceback 字样）。
        它只是补充，不是判据的主干。
    """
    # ⛔ R3 round-17 (冻结审查 §一.4): 上一版号称「从名单改形态」, 其实只是把名单
    # 从**全名**换成了**后缀** —— `(?:[Ee]rror|Exception)` 仍是一张我手写的闭表,
    # 漏掉 `SystemExit` / `subprocess.TimeoutExpired` / 裸 `Exception` 以外的一切
    # 不以 Error/Exception 结尾的异常。这是本项目记账过的「枚举 vs 结构」第四次。
    # ⇒ 判据反过来写: 枚举的不是**异常空间**(开放), 而是 **pytest 自己的"判错"
    #   词汇表**(封闭, 由 pytest API 定义): 断言失败只会以 `assert` / `AssertionError`
    #   开头。除此之外任何出现在 `E ` 详情行首的标识符都是"崩坏"。
    # ⛔ R3 round-17 二修（实测 39/44 假阳）: 上一版写成 `^E\s+<标识符>`, 以为那是
    # 「异常行」—— 其实 pytest 给失败详情的**每一行**都加 `E ` 前缀, 于是断言消息
    # 的续行 `E     VERIFY FAIL (1 项) …` 被当成异常 `VERIFY`, 44 条变体里 39 条
    # 被误判成崩溃。**修严引入松、修松引入严**, 两次的病根都是没去读 pytest 的
    # 真实输出语法。实测语法: 异常行是 `E   <类名>: <消息>` —— 标识符后**紧跟冒号**;
    # 断言是 `E   assert …` 或 `E   AssertionError: …`; 续行则是缩进的自由文本。
    # ⇒ 加上"紧跟冒号"这一条, 两个方向同时收敛(负控见 r13 门的 16 条形态)。
    # ⛔ round-21（冻结审查 v3）：上一版号称"可靠二分"，**那个说法不成立**，如实收回。
    #    审查方点名的三条都对：
    #      · 内层 CLI 的无 traceback 崩溃（`SyntaxError` / 致命信号）在外层只剩
    #        一个 `AssertionError` ⇒ 假阴；
    #      · 正文偶然含 `Traceback…` / `N error(s)` ⇒ 假阳；
    #      · 缩进上界是**当前 formatter 的启发式** —— 而且我此前注释说"跑的是
    #        `-q` 默认 tb"是**事实错误**：`backend/pytest.ini` 的 addopts 强制
    #        `--tb=short`。实测的 3 格是**那个配置下**的形态，不是普适规律。
    #    ⇒ 结构调整：**子进程崩溃改由源头打确定性标记**（见 test 侧
    #      `CHILD_CRASH_MARK`），标记出现即权威判定；下面这套解析 pytest 渲染的
    #      规则**降级为补充启发式**，只用于捕捉外层自身抛出的异常。
    CHILD_CRASH_MARK = "[[CHILD-CRASH]]"
    if CHILD_CRASH_MARK in out:
        return True
    LEGIT_RED = {"assert", "AssertionError"}
    # ⛔ round-20 (冻结审查 v2 §四.4): 只要"紧跟冒号"仍会假阳 —— 断言消息的
    #    续行 `E       Expected: …` 同样是"标识符+冒号"。实测 pytest 语法:
    #    顶层行是 `E` + **3 个空格** + 内容(异常行与 `assert` 行都是),
    #    续行则缩进**更深**(`E     VERIFY…` 5 格 / `E    +  where` 4 格)。
    #    ⇒ 缩进上界 3 格 + 紧跟冒号, 两个条件一起才是异常行。
    #    这条规则的规格书是 pytest 的真实输出, 不是我对它的印象 —— 本判据
    #    已在这个方向上错过两次(枚举后缀=假阴, 任意标识符=假阳 39/44)。
    # ⛔ round-20 二修（变异 C 存活 + 冻结审查 v2 的第三条判词）:
    #    加了缩进上界之后, "紧跟冒号"这个条件**既多余又有害** ——
    #    · 多余: 续行缩进 ≥4 格, 上界已经把它们排除, 冒号不再承担区分职责
    #      (实测: 去掉冒号后 mutC 不再让任何门变红 ⇒ 那条变异已不承重);
    #    · 有害: **无消息异常**打出来是 `E   RecursionError`(没有冒号),
    #      要求冒号 = 漏掉整整一类崩溃(假阴)。
    #    ⇒ 只留缩进上界 + LEGIT_RED 白名单。判据的两个条件里, 承重的是缩进。
    exc_names = re.findall(r"^E {1,3}([A-Za-z_][\w.]*)\b", out, re.M)
    errors = sum(int(m) for m in re.findall(r"(\d+) error(?:s)?\b", out))
    return bool(
        any(name not in LEGIT_RED for name in exc_names)
        or "Traceback (most recent call last):" in out
        or "INTERNALERROR" in out
        or errors > 0
    )


def run_suite(keyword: str) -> tuple[int, str, int, int, bool]:
    """跑目标用例，返回 (rc, 输出尾部, 收集到的用例数, 失败数, 是否崩溃)。

    ⛔ round-27（冻结审查 v8）：注解与 docstring 原写**四元组**，实际返回五元组
    （`crash` 是 round-10 加的）—— 又一处「说的与做的不符」。

    ⛔ Codex round-1 HIGH: 原实现只看 `rc != 0` 就判「如期变红」——
    pytest 的 rc=5 是**一个用例都没匹配到**（`-k` 写错就会这样），
    rc=2/3/4 是用法错误/内部错误。把它们当成"门变红了"正是
    MEMORY `reference_gate_design_pitfalls` 的头号形态：
    **把「没有发生」当成「验证通过」**。现在解析出真实的 passed/failed 计数，
    要求"确实收集到用例"且"确实有失败"才算变红。
    """
    r = subprocess.run(
        [str(PYTEST), SUITE, "-q", "-p", "no:cacheprovider", "-k", keyword],
        cwd=ROOT / "backend",
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=600,
    )
    out = r.stdout
    failed = sum(int(m) for m in re.findall(r"(\d+) failed", out))
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    # ⛔ R3 round-17 (冻结审查 §一.4): 崩溃分析必须看 **stdout + stderr**。
    # 上一版只分析 stdout ⇒ 本域大量门是**跑 CLI 子进程**再核输出的, 子进程的
    # traceback 若只落在 stderr, 外层就只剩一个 AssertionError,
    # 生产崩溃被当成正常"判错变红"。计数仍只从 stdout 取(摘要行在那儿)。
    both = _crash_text(out, r.stderr)
    # ⛔ 铁律 5 (CARD-维护B-R3 round-10, Codex round-8 HIGH-7 实证):
    # 变异必须让被测物**产生错误的判断**, 而不是让它**崩溃**。
    # survivor-20 原版把千分位 pattern 换成无捕获组 lookaround, 却保留生产代码的
    # `r"\1"` replacement ⇒ 一调用就 `re.error: invalid group reference`。
    # 测试确实变红了 —— 但那是**因崩溃变红**, 不是因漏拦变红, 而脚本把任何
    # failure 都记成"承重"。**异常伪红比不变红更坏**: 它会以「✅ 如期变红」
    # 的形式混进证据, 且永远不会有人去查。
    # ⇒ 这里显式识别"变异让生产代码抛异常"的形态并单独报出。
    # ⛔ R3 round-16 (冻结审查 HIGH: 「崩溃假阴存在」): 上一版**枚举**五个异常名,
    # 且只扫**外层 pytest** 的 stdout —— 两个假阴面:
    #   ① 枚举之外的异常 (ValueError / KeyError / IndexError / RecursionError …)
    #      让生产代码崩溃时, 脚本照旧记「✅ 如期变红」;
    #   ② 本域大量门是**跑 CLI 子进程**再核 stdout 的, 子进程里的 traceback
    #      被捕获进断言详情, 外层不出现任何异常名 ⇒ 崩溃完全隐形。
    # ⇒ 改为按**形态**识别, 不再枚举名字:
    #   · pytest 失败详情行 `E   <Exc>: …` —— 除 AssertionError 外一律算崩溃
    #     (断言失败才是「判错」, 其余异常都是「崩坏」);
    #   · 任何位置出现 `Traceback (most recent call last):` —— 覆盖子进程崩溃;
    #   · pytest 自身的 INTERNALERROR / 收集期 error 计数。
    # 假阳边界如实声明: 若某条门**故意**断言输出里含 traceback 文本, 会被误判为
    # 崩溃 —— 那是「宁可误报也不漏报」的方向选择, 且当前目标套件无此形态。
    crash = _looks_like_crash(both)
    return r.returncode, out[-400:], passed + failed, failed, crash


MUTANT_COUNT_EXPECTED = 65
"""变体数的**独立**期望值。

⛔ 冻结审查 v6：脚本原先只在结尾动态打印「共 N 条」—— 误删一个变体仍会成功退出。
期望值必须来自**另一个来源**才能验伪（本卡反复吃过"期望抄自被测物"的亏）。
改这个数 = 明确声明"我知道自己在增删变体"。
"""


def preflight() -> list[str]:
    """开跑前的**锚点预检**（秒级）—— 失败即停，不进 40 分钟长流程。

    ⛔ 「性质一搬家、旧锚点静默失效」在本卡发生了 **6 次**，每次代价固定：
    改实现 → 跑满一轮 → 跑到那一条才报「未命中」→ 重锚 → 再跑一轮。
    **发现成本远高于修复成本，且发现得越晚越贵。**

    ⚠️ 能力边界（round-25 声明，round-26 按冻结审查 v7 收紧措辞）：
      · 「恰好命中一次」只证明**文本定位唯一**；
      · 「整组替换后源码确实变化」证明**替换非空**（round-26 新增，此前只比
        `old != new`，而成功消息却宣布了"替换非空" —— 措辞比证据宽）；
      · **不**证明该位置**可达**、或确实**禁掉了目标防线**（行为非空）——
        「锚点仍命中但变异已为空」在本卡真实发生过（见 铁律 4 / 铁律 5）。
      · 它是**必要非充分**条件：能挡住**锚点漂移**与**文本级**空变异，
        挡不住**行为级**空变异（改到了活代码，却没禁掉那条防线）。
      ⚠️ 归因edge：`survivor-7` 那次是被 `hits != 1` 抓到的，**不是**被新增的
        「整组替换后源码确实变化」抓到的 —— 我此前把功劳记给了后者，过宽。
    """
    bad: list[str] = []
    if len(MUTANTS) != MUTANT_COUNT_EXPECTED:
        bad.append(f"变体数 {len(MUTANTS)} ≠ 期望 {MUTANT_COUNT_EXPECTED}（增删变体须同步改期望值）")
    ids = [n.split()[0] for n, _s, _k in MUTANTS]
    if len(set(ids)) != len(ids):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        bad.append(f"变体 ID 重复: {dup}")
    src = TARGET.read_text(encoding="utf-8")
    for idx, (name, subs, _kw) in enumerate(MUTANTS):
        sid = ids[idx]
        if not subs:
            bad.append(f"{sid}: subs 为空 = 什么都不改")
            continue
        # ⛔ round-26（冻结审查 v7）：原先逐条只比 `old != new`，成功消息却宣布
        #    「替换非空」—— **措辞比证据宽**。改为**按真实顺序模拟整组替换**，
        #    要求最终源码确实变化：这才配得上那句话。
        mutated = src
        for old, new in subs:
            hits = mutated.count(old)
            if hits != 1:
                bad.append(f"{sid}: 锚点命中 {hits} 次（须恰好 1）")
                mutated = None
                break
            mutated = mutated.replace(old, new, 1)
        if mutated is not None and mutated == src:
            bad.append(f"{sid}: 整组替换后源码与原文逐字节相同 = 空变异")
    return bad


def main() -> int:
    try:
        LOCK.mkdir()  # 原子互斥: 已存在即抛
    except FileExistsError:
        print(f"⛔ 另一个负验证进程正在跑（锁: {LOCK}）。变异脚本必须串行——见脚本 docstring。")
        return 2
    try:
        _bad = preflight()
        if _bad:
            print("⛔ 锚点预检失败（不跑长流程）：")
            for _b in _bad:
                print("   -", _b)
            return 2
        print(
            f"✅ 锚点预检通过：{len(MUTANTS)} 条变体 —— 锚点均恰好命中一次，"
            "整组替换后源码确实变化（**不**证明该处可达或真禁掉了目标防线）\n"
        )
        original = TARGET.read_bytes()
        backup_sha = hashlib.sha256(original).hexdigest()

        rc0, out0, n0, f0, _c0 = run_suite("domain_")
        if rc0 != 0 or f0 or n0 == 0:
            print(f"⛔ 基线不可信（rc={rc0} 收集={n0} 失败={f0}）:\n{out0}")
            return 2
        print(f"基线: 双向门全绿 · 被测文件 sha256={backup_sha[:12]}…\n")

        failures = 0
        for name, subs, keyword in MUTANTS:
            text = original.decode("utf-8")
            for old, new in subs:
                if old not in text:
                    print(f"❌ {name}: 变异点未命中（实现已变？）——按失败计")
                    failures += 1
                    text = None
                    break
                text = text.replace(old, new, 1)
            if text is None:
                continue
            # ⛔ R3 round-23（冻结审查 v4）：写入原先在 `try` **之前** —— 写到一半抛异常
            #    （磁盘满 / 权限 / 编码）就落不进 finally，变异体留在生产文件里。
            #    把写入挪进 try：从"文件可能已被改动"的第一刻起就有还原兜底。
            #    ⚠️ 如实声明**兜底不到**的情况：SIGKILL / 解释器崩溃 / 断电 ——
            #    Python 层的 finally 对它们无能为力，前后 hash 自检也覆盖不了
            #    （进程都没了）。真正的根治是"改副本不改原件"，属重做设计，未做。
            #    残留检测靠外部锚点：见 MEMORY `reference_mutation_restore_must_be_unconditional`
            #    （grep MUTANT + sha 对比），本脚本自身证明不了这件事。
            try:
                TARGET.write_text(text, encoding="utf-8")
                rc, out, n, f, crash = run_suite(keyword)
            finally:
                TARGET.write_bytes(original)  # 立刻还原，异常也还原
            got = hashlib.sha256(TARGET.read_bytes()).hexdigest()
            assert got == backup_sha, f"还原后字节与备份不同！{got[:12]} != {backup_sha[:12]}"
            # ⛔ 必须是"收集到用例 且 确实有失败"，不能只看 rc != 0
            if n == 0:
                print(f"❌ {name}: `-k {keyword}` 一个用例都没匹配到（rc={rc}）——这不是变红")
                failures += 1
            elif rc != 1:
                # ⛔ R3 round-16 (冻结审查 HIGH): 上一版只要「收集到 且 有失败」就算承重,
                # **不看 rc**。pytest 只有 rc=1 才是「测试失败」; 2=中断 3=内部错
                # 4=用法错 5=没收集到。收集到用例的同时 rc=2/3 (如中途 KeyboardInterrupt
                # 或插件炸) 会让一次**残缺运行**冒充「如期变红」。
                print(f"❌ {name}: rc={rc}（只有 rc=1 才是「测试失败」）——不算变红")
                failures += 1
            elif crash:
                print(
                    f"❌ {name}: 变异让生产代码**抛异常**（输出含 re.error/NameError 等）"
                    f"——这是**因崩溃变红**, 不是因漏拦变红, 不算承重\n{out}"
                )
                failures += 1
            elif f == 0:
                print(f"❌ {name}: 变异后 {n} 个用例仍全绿 = 该门不承重\n{out}")
                failures += 1
            else:
                print(f"✅ {name}: 如期变红（{f}/{n} 失败）")

        print(f"\n{'全部承重' if not failures else f'{failures} 条未承重'}（共 {len(MUTANTS)} 条变体）")
        return 1 if failures else 0
    finally:
        LOCK.rmdir()


if __name__ == "__main__":
    sys.exit(main())
