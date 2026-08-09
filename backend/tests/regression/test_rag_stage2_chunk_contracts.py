# RAG-S2-2026-08-09 阶段 2 T3 chunk 改造 — 契约测试（五组）
#
# 组 A doc_type 推断: 考察文件 (exam_question_id, 无 type:) → exam_board;
#       显式 type: 最优先; 普通笔记仍 note — 堵题面泄漏 (信息隔离旁路)
# 组 B 段落级切分: 段落在 chunk 内保持完整不跨段拼接; 超长单段降级句子级;
#       overlap 段落化 (只取完整段落, 超预算不取); 原子单元 (代码块) 保护不变
# 组 C callout 三级分级: EXTRACT (question/error-candidate 独立成块) /
#       STRIP (info/video/note + tip 模板标记) / KEEP (tips/warning/quote 留正文)
# 组 D 模板样板: 派生节点占位 section (（你的…）/空 bullet) 不产 chunk
# 组 E 面包屑与行号: 短块面包屑只留文件名, 长块完整路径;
#       line_start/line_end 含 frontmatter 占行偏移
#
# 纯单元契约 — 直接调 LanceDBClient._split_md_by_heading / _chunk_text,
# 不碰 LanceDB / embedding。
#
# [Source: _bmad-output/研究/2026-08-09-RAG阶段2-强化fastpath实施计划.md T3]

from agentic_rag.clients.lancedb_client import LanceDBClient, _chunk_text

# ═══════════════════════════════════════════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _split(content: str, path: str = "节点/测试.md"):
    return LanceDBClient._split_md_by_heading(content, path)


def _bodies(chunks):
    """去掉面包屑前缀后的 chunk 正文列表。"""
    out = []
    for c in chunks:
        _, _, body = c["content"].partition("\n\n")
        out.append(body)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# 组 A — doc_type 推断（T3 Step1 堵题面泄漏）
# ═══════════════════════════════════════════════════════════════════════════════


def test_exam_file_without_type_infers_exam_board():
    """考察文件 frontmatter 无 type: 但有 exam_question_id → exam_board。

    旧行为 fallback "note" 让完整题面以最高权重入索引, 现有
    doc_type NOT IN ('whiteboard','exam_board') 排除拦不住 = 信息隔离旁路。
    """
    content = (
        "---\n"
        "exam_question_id: eq-001\n"
        'source_concept: "[[Fundamentals]]"\n'
        "exam_status: pending\n"
        "---\n"
        "# 考察-Fundamentals\n\n题面：请解释特征值的几何意义。\n"
    )
    chunks = _split(content, "节点/考察-Fundamentals-2026-07-16.md")
    assert chunks, "考察文件应产 chunk (仍入索引, 只是被检索链排除)"
    assert {c["doc_type"] for c in chunks} == {"exam_board"}


def test_explicit_type_beats_exam_inference():
    content = "---\ntype: concept\nexam_question_id: eq-002\n---\n# X\n\n正文。\n"
    chunks = _split(content)
    assert {c["doc_type"] for c in chunks} == {"concept"}


def test_plain_note_still_defaults_note():
    content = "---\ncourse: cs188\n---\n# X\n\n正文。\n"
    chunks = _split(content)
    assert {c["doc_type"] for c in chunks} == {"note"}


# ═══════════════════════════════════════════════════════════════════════════════
# 组 B — 段落级切分（T3 Step2）
# ═══════════════════════════════════════════════════════════════════════════════


def test_paragraphs_stay_intact_across_chunks():
    """段落是最小累积单元 — 任何段落不被切开分进两个 chunk。"""
    paras = [f"段落{i}开头标记。" + "填充句子内容。" * 40 for i in range(6)]
    out = _chunk_text("\n\n".join(paras), max_tokens=512, overlap_tokens=50)
    assert len(out) > 1, "6 个 ~240 token 段落必须切成多个 chunk"
    joined = "".join(out)
    for p in paras:
        # 每个段落必须在某个 chunk 中完整出现（不被从中间切断）
        assert any(p in chunk for chunk in out), f"段落被切断: {p[:20]}"
    assert joined.count("段落0开头标记") == 1, "无 overlap 时段落不应重复"


def test_oversized_paragraph_degrades_to_sentences():
    """单段超 max_tokens → 降级句子级切分, 而不是整段独立超限 chunk。"""
    giant = "这是一个超长段落的句子。" * 120  # 单段远超 512 token
    out = _chunk_text(giant, max_tokens=512, overlap_tokens=50)
    assert len(out) > 1, "超长单段必须被句子级降级切开"


def test_paragraph_overlap_only_complete_and_within_budget():
    """overlap 段落化: 上一 chunk 最后一个完整段落 ≤ overlap 预算才取。"""
    # 尾段落很小 (≤50 token) → 应作为 overlap 完整出现在下一 chunk 开头
    big = "大段落内容句子。" * 55
    tiny = "小尾段。"
    following = "后续段落内容。" * 50
    out = _chunk_text(f"{big}\n\n{tiny}\n\n{following}", max_tokens=512, overlap_tokens=50)
    assert len(out) >= 2
    tiny_total = sum(chunk.count(tiny) for chunk in out)
    assert tiny_total >= 2, "≤50 token 的完整尾段应被段落化 overlap 带入下一 chunk"
    # 超预算段落 (>50 token) 不作 overlap — 杜绝半截上下文
    paras = [f"段落{i}标记。" + "内容句子。" * 40 for i in range(4)]
    out2 = _chunk_text("\n\n".join(paras), max_tokens=512, overlap_tokens=50)
    for i in range(4):
        assert sum(c.count(f"段落{i}标记") for c in out2) == 1, "超预算段落不得作 overlap 重复"


def test_atomic_code_block_still_protected():
    code = "```python\n" + "x = 1\n" * 30 + "```"
    text = ("前置说明段落。" * 30) + "\n\n" + code + "\n\n" + ("后置段落。" * 60)
    out = _chunk_text(text, max_tokens=128, overlap_tokens=20)
    holders = [c for c in out if "```python" in c]
    assert len(holders) == 1, "代码块必须完整保留在单一 chunk"
    assert holders[0].count("x = 1") == 30, "代码块内容不得被切断"


# ═══════════════════════════════════════════════════════════════════════════════
# 组 C — callout 三级分级（T3 Step3）
# ═══════════════════════════════════════════════════════════════════════════════

_CALLOUT_DOC = (
    "---\ntype: concept\n---\n"
    "# Fundamentals\n\n"
    "## 我的理解\n\n"
    "用户手写的理解正文，讲特征值的几何直觉。\n\n"
    "> [!question]+ ❓ 提问 %%cb-x1%%\n"
    "> 为什么特征向量方向不变？\n\n"
    "> [!error-candidate]+ 🔴 待复盘 · AI 建议\n"
    "> 混淆了特征值与奇异值。\n\n"
    "> [!info]+ 这是什么\n"
    "> 模板说明文字。\n\n"
    "> [!video]- 视频播放器\n"
    "> ![[lecture 2.mp4]]\n\n"
    "> [!tips]+ 💡 Tips\n"
    "> - [x] 🤔 模糊\n"
    "> 吃豆人例子说明代理决策。\n\n"
    "> [!warning]+ 注意\n"
    "> 特征值可以为复数。\n\n"
    "正文收尾句。\n"
)


def test_question_and_error_callouts_extracted_standalone():
    """EXTRACT: question / error-candidate 独立成块 — 不混入正文稀释也不被淹没。"""
    bodies = _bodies(_split(_CALLOUT_DOC))
    q_chunks = [b for b in bodies if "为什么特征向量方向不变" in b]
    e_chunks = [b for b in bodies if "混淆了特征值与奇异值" in b]
    assert len(q_chunks) == 1 and len(e_chunks) == 1
    # 独立成块 = 该 chunk 不含正文句
    assert "用户手写的理解正文" not in q_chunks[0]
    assert "[!question]" in q_chunks[0], "EXTRACT 块保留 callout 标记供来源识别"
    assert "用户手写的理解正文" not in e_chunks[0]


def test_template_callouts_stripped():
    """STRIP: info / video 模板 callout 从索引内容中消失。"""
    all_content = "".join(c["content"] for c in _split(_CALLOUT_DOC))
    assert "模板说明文字" not in all_content
    assert "视频播放器" not in all_content
    assert "lecture 2.mp4" not in all_content


def test_semantic_callouts_kept_in_body():
    """KEEP: tips (用户勾选学习痕迹) / warning 留在正文 chunk 内。"""
    bodies = _bodies(_split(_CALLOUT_DOC))
    prose = [b for b in bodies if "用户手写的理解正文" in b]
    assert prose, "正文 chunk 必须存在"
    assert "吃豆人例子说明代理决策" in prose[0], "tips callout 应保留在正文"
    assert "特征值可以为复数" in prose[0], "warning callout 应保留在正文"


def test_scaffold_tip_template_stripped_but_quote_kept():
    """tip 类型整体 KEEP, 但插件脚手架模板 (💬 围绕这个概念讨论) 命中标记即 STRIP;
    quote 派生起点是节点语义锚, 必须保留。"""
    content = (
        "---\ntype: concept\n---\n"
        "# TestConcept\n\n"
        "> [!quote]+ 派生起点（来自 [[Fundamentals]] 选中文本）\n"
        "> Eigenvalues satisfy Av = λv\n\n"
        "用户补充的一句理解。\n\n"
        "> [!tip] 💬 围绕这个概念讨论\n"
        "> 这个节点是**讨论容器**，不是 AI 写好的内容。\n"
    )
    all_content = "".join(c["content"] for c in _split(content))
    assert "Eigenvalues satisfy Av" in all_content, "quote 派生起点必须保留"
    assert "讨论容器" not in all_content, "脚手架 tip 模板必须剥离"


# ═══════════════════════════════════════════════════════════════════════════════
# 组 D — 模板样板 section 不产 chunk（T3 Step3）
# ═══════════════════════════════════════════════════════════════════════════════


def test_placeholder_sections_produce_no_chunks():
    """派生节点脚手架的占位 section (（你的…）指导语 / 空 bullet) 零 chunk。"""
    content = (
        "---\ntype: concept\n---\n"
        "# TestConcept\n\n"
        "## 核心概念\n\n"
        "（你的 1-2 句精准定义。这个概念 *是什么* / *为什么重要*？）\n\n"
        "## 关键点\n\n"
        "- \n\n"
        "## 我的笔记\n\n"
        "用户真实写下的内容。\n"
    )
    chunks = _split(content)
    headings = [c["heading"] for c in chunks]
    assert "核心概念" not in headings, "纯占位 section 不得产 chunk"
    assert "关键点" not in headings, "空 bullet 骨架不得产 chunk"
    assert any("用户真实写下的内容" in c["content"] for c in chunks)


def test_user_filled_placeholder_section_kept():
    """用户在占位 section 写了真实内容 → 照常产 chunk。"""
    content = "---\ntype: concept\n---\n# X\n\n## 核心概念\n\n特征值刻画线性变换的伸缩。\n"
    chunks = _split(content)
    assert any("特征值刻画线性变换的伸缩" in c["content"] for c in chunks)


# ═══════════════════════════════════════════════════════════════════════════════
# 组 E — 面包屑条件化 + 行号偏移（T3 Step4/Step5）
# ═══════════════════════════════════════════════════════════════════════════════


def test_short_chunk_breadcrumb_filename_only():
    """短块 (<150 token) 面包屑只留文件名 — 完整路径反客为主。"""
    content = "---\ntype: note\n---\n# 咖啡笔记\n\n## 手冲要点\n\n水温 92 度。\n"
    chunks = _split(content, "节点/咖啡笔记.md")
    assert len(chunks) == 1
    first_line = chunks[0]["content"].split("\n")[0]
    assert first_line == "文档：咖啡笔记", f"短块面包屑应只留文件名, 实际: {first_line}"


def test_long_chunk_breadcrumb_full_path():
    long_body = "这是足够长的正文内容句子。" * 40  # > 150 token
    content = f"---\ntype: note\n---\n# 咖啡笔记\n\n## 手冲要点\n\n{long_body}\n"
    chunks = _split(content, "节点/咖啡笔记.md")
    first_line = chunks[0]["content"].split("\n")[0]
    assert "咖啡笔记 > " in first_line and "手冲要点" in first_line, f"长块面包屑应保留完整路径, 实际: {first_line}"


def test_line_numbers_include_frontmatter_offset():
    """line_start/line_end 是原文件坐标 — 含 frontmatter 占行偏移 (bug②)。"""
    content = (
        "---\n"  # 文件行 1
        "type: note\n"  # 2
        "course: cs188\n"  # 3
        "---\n"  # 4
        "# 标题\n"  # 5
        "\n"  # 6
        "正文第一句。\n"  # 7
    )
    chunks = _split(content)
    assert len(chunks) == 1
    # section 从 heading 行开始 = 原文件第 5 行
    assert chunks[0]["line_start"] == 5, f"应为原文件行 5, 实际 {chunks[0]['line_start']}"
    assert chunks[0]["line_end"] >= 7


def test_line_numbers_without_frontmatter_unchanged():
    chunks = _split("# 标题\n\n正文第一句。\n")
    assert chunks[0]["line_start"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 组 F — 对抗审查红线（Code-Review 2026-08-09 findings 回归）
# ═══════════════════════════════════════════════════════════════════════════════


def test_yaml_parse_failure_still_infers_exam_board():
    """HIGH-1: 生产者 exam-quick.ts 写裸标量, 概念名含 YAML 指示符炸 safe_load
    → fm={} → 旧逻辑判 note = 题面泄漏复活。嗅探兜底后仍须 exam_board。"""
    content = (
        "---\n"
        "exam_question_id: eq-9\n"
        "source_concept: Minimax: Alpha-Beta Pruning\n"  # 裸冒号 → YAML 解析失败
        "exam_status: pending\n"
        "---\n"
        "# 考察-Minimax\n\n题面：写出 alpha-beta 剪枝的伪代码。\n"
    )
    chunks = _split(content, "节点/考察-Minimax-2026-08-01.md")
    assert chunks, "解析失败的考察文件仍应产 chunk"
    assert {c["doc_type"] for c in chunks} == {"exam_board"}, "YAML 失败路径不得回落 note"


def test_adjacent_callouts_without_blank_line_classified_separately():
    """MEDIUM-1: 无空行紧贴的 [!info]+[!question] 不得整块按头行 STRIP
    吞掉用户批注 — 每个 callout 头独立断块分级。"""
    content = (
        "---\ntype: concept\n---\n# X\n\n"
        "正文内容一句。\n\n"
        "> [!info]+ 模板说明\n"
        "> 模板指导文字。\n"
        "> [!question]+ ❓ 提问\n"
        "> 用户紧贴模板写下的疑问？\n"
    )
    chunks = _split(content)
    all_content = "".join(c["content"] for c in chunks)
    assert "用户紧贴模板写下的疑问" in all_content, "紧贴 callout 的用户提问不得被吞"
    assert "模板指导文字" not in all_content, "紧贴的 info 模板仍须 STRIP"
    q_chunks = [c for c in chunks if "用户紧贴模板写下的疑问" in c["content"]]
    assert "[!question]" in q_chunks[0]["content"], "提问仍须 EXTRACT 独立成块"


def test_boilerplate_detection_no_false_kill():
    """MEDIUM-2: 用户真实内容形似占位不得误杀 —
    （你的意思是…吗？）是疑问不是模板; 正文里字面引用 [在此填写] 不是占位。"""
    content = (
        "---\ntype: concept\n---\n# X\n\n"
        "## 疑问区\n\n"
        "（你的意思是矩阵一定可以对角化吗？）\n\n"
        "## 备忘\n\n"
        "注意模板里的 [在此填写] 占位符必须删掉，否则评分失败。\n"
    )
    chunks = _split(content)
    all_content = "".join(c["content"] for c in chunks)
    assert "矩阵一定可以对角化" in all_content, "用户括号疑问不得被判占位丢弃"
    assert "占位符必须删掉" in all_content, "字面引用 [在此填写] 的正文不得丢弃"


def test_pure_placeholder_still_skipped_after_tightening():
    """MEDIUM-2 收紧后, 真模板占位仍须被跳过 (回归保护)。"""
    content = (
        "---\ntype: concept\n---\n# X\n\n"
        "## 核心概念\n\n"
        "（你的 1-2 句精准定义。这个概念 *是什么* / *为什么重要*？）\n\n"
        "## 待填\n\n"
        "[在此填写]\n"
    )
    chunks = _split(content)
    headings = [c["heading"] for c in chunks]
    assert "核心概念" not in headings
    assert "待填" not in headings
