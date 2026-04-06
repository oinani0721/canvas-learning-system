"""Generate Excalidraw mind map: 7 Modules → FRs → User Annotations."""
import json
import hashlib
import math

def make_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:8]

def rect(id, x, y, w, h, text, bg="#ffffff", stroke="#000000", font_size=16, bound_text=None):
    el = {
        "id": id,
        "type": "rectangle",
        "x": x, "y": y,
        "width": w, "height": h,
        "strokeColor": stroke,
        "backgroundColor": bg,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "roundness": {"type": 3},
        "opacity": 100,
        "angle": 0,
        "groupIds": [],
        "boundElements": [{"id": bound_text, "type": "text"}] if bound_text else [],
        "isDeleted": False,
        "seed": abs(hash(id)) % 2000000000,
        "version": 1,
        "versionNonce": abs(hash(id+"v")) % 2000000000,
    }
    return el

def text_el(id, x, y, text, font_size=16, color="#000000", container_id=None, w=None, h=None, text_align="center"):
    el = {
        "id": id,
        "type": "text",
        "x": x, "y": y,
        "width": w or len(text) * font_size * 0.6,
        "height": h or font_size * 1.5 * max(1, text.count('\n') + 1),
        "text": text,
        "fontSize": font_size,
        "fontFamily": 1,
        "textAlign": text_align,
        "verticalAlign": "middle" if container_id else "top",
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "opacity": 100,
        "angle": 0,
        "groupIds": [],
        "containerId": container_id,
        "boundElements": [],
        "isDeleted": False,
        "seed": abs(hash(id)) % 2000000000,
        "version": 1,
        "versionNonce": abs(hash(id+"v")) % 2000000000,
        "originalText": text,
        "lineHeight": 1.25,
    }
    return el

def arrow(id, start_id, end_id, points, stroke="#000000"):
    return {
        "id": id,
        "type": "arrow",
        "x": points[0][0], "y": points[0][1],
        "width": abs(points[-1][0] - points[0][0]) or 1,
        "height": abs(points[-1][1] - points[0][1]) or 1,
        "points": [[0,0], [points[-1][0]-points[0][0], points[-1][1]-points[0][1]]],
        "strokeColor": stroke,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "opacity": 100,
        "angle": 0,
        "groupIds": [],
        "startBinding": {"elementId": start_id, "focus": 0, "gap": 5},
        "endBinding": {"elementId": end_id, "focus": 0, "gap": 5},
        "boundElements": [],
        "isDeleted": False,
        "seed": abs(hash(id)) % 2000000000,
        "version": 1,
        "versionNonce": abs(hash(id+"v")) % 2000000000,
        "roundness": {"type": 2},
        "startArrowhead": None,
        "endArrowhead": "arrow",
    }

elements = []

# ═══ Module definitions with FRs and user annotations ═══
modules = [
    {
        "name": "Agent\n(14 services)",
        "color": "#f38ba8",
        "stroke": "#d20f39",
        "frs": [
            {"id": "FR-CONV", "label": "FR-CONV\n节点对话 (13项)", "annotations": [
                "CONV-03: 多节点上下文怎么处理？",
                "CONV-04: 对话框没有命令可用",
                "CONV-06: 没看到错误提取 [BROKEN]",
                "CONV-10: 到底要实现什么功能？",
                "CONV-11: =上下文压缩？参考Claude Code",
                "CONV-12: 没看到session切换",
                "CONV-13: 需求指什么？",
            ]},
            {"id": "FR-AGENT", "label": "FR-AGENT\nAgent系统 (3项)", "annotations": [
                "AGENT-01: 没看到Sidecar",
                "AGENT-02: 没看到per-node session",
                "AGENT-03: Gemini硬编码",
                "Critical #4: 对话要和Claude Code一样智能",
            ]},
            {"id": "FR-SKILL", "label": "FR-SKILL\nAgent技能 (5项)", "annotations": [
                "SKILL-01~05: 全部前端没看到",
            ]},
        ]
    },
    {
        "name": "Exam\n(9 services)",
        "color": "#fab387",
        "stroke": "#df8e1d",
        "frs": [
            {"id": "FR-EXAM", "label": "FR-EXAM\n检验白板 (18项)", "annotations": [
                "EXAM-01: 功能全部卡死 [BROKEN]",
                "EXAM-02: 选节点策略需技术更新",
                "EXAM-11: 三种考察模式未激活",
                "EXAM-12: 估计硬编码",
                "EXAM-17: 死代码",
                "EXAM-22: 技术框架有更新",
            ]},
            {"id": "FR-QA", "label": "FR-QA\n质量保证 (7项)", "annotations": [
                "QA-01: 忠实度算法靠不靠谱？",
                "QA-04: Dashboard展示不完整",
                "AutoSCORE: 未验证",
                "Area9: 未验证",
                "ACP: 3K token依据？5要素组装？",
                "SOLO rubric: 未测试",
            ]},
        ]
    },
    {
        "name": "Mastery\n(6 services)",
        "color": "#a6e3a1",
        "stroke": "#40a02b",
        "frs": [
            {"id": "FR-MAST", "label": "FR-MAST\n精通度 (6项)", "annotations": [
                "MAST-01: 没有日志验证+技术更新",
                "MAST-02: '考察更新'什么意思？",
                "MAST-06: 5维融合怎么设计？可信度？",
                "BKT: deep research有技术更新",
                "FSRS: deep research有技术更新",
            ]},
        ]
    },
    {
        "name": "Memory\n(3 services)",
        "color": "#89dceb",
        "stroke": "#209fb5",
        "frs": [
            {"id": "FR-MEM", "label": "个人记忆系统", "annotations": [
                "Critical #1: 算法流程怎么设计？",
                "Critical #2: 硬编码 vs LangGraph?",
                "Critical #3: 引入Auto Research迭代",
                "RET-03: 42处假命名+无A/B测试",
                "梦记忆: Claude Code泄漏代码有帮助吗",
            ]},
        ]
    },
    {
        "name": "Canvas\n(5 services)",
        "color": "#94e2d5",
        "stroke": "#179299",
        "frs": [
            {"id": "FR-KG", "label": "FR-KG\n知识图谱 (9项)", "annotations": [
                "KG-04~07: 前端没看到(Tauri)",
                "KG-09: 粘贴图片不能用",
            ]},
            {"id": "FR-EDGE", "label": "FR-EDGE\n连线对话 (4项)", "annotations": [
                "EDGE-01~04: 前端没看到(Tauri)",
            ]},
            {"id": "FR-DASH", "label": "FR-DASH\nDashboard (4项)", "annotations": [
                "DASH-04: 前端没看到",
            ]},
        ]
    },
    {
        "name": "RAG\n(5 services)",
        "color": "#f5c2e7",
        "stroke": "#ea76cb",
        "frs": [
            {"id": "FR-RET", "label": "FR-RET\n检索管道 (13项)\n⚠️ 最弱 7.7%", "annotations": [
                "RET-01: 是个人记忆系统吗？",
                "RET-02: 检索什么？引用什么？",
                "RET-04: LangGraph算法设计不靠谱",
                "RET-05: 检索笔记还是记忆？",
                "RET-06: 指增量索引？",
                "RET-08: 涉及笔记ARAG",
                "RET-09: jieba可能假实现",
                "RET-10: 这是什么？",
                "RET-11: 这是什么？",
                "RET-12: 参考Claude Code压缩算法",
                "RET-13: Obsidian原生跳转？",
                "核心困惑: 两个RAG杂糅不清",
            ]},
        ]
    },
    {
        "name": "Infra\n(17 services)",
        "color": "#585b70",
        "stroke": "#4c4f69",
        "frs": [
            {"id": "FR-SYS", "label": "FR-SYS\n系统配置 (9项)", "annotations": [
                "SYS-01: 安装向导未实现",
                "SYS-08: 账号切换未实现",
                "SYS-09: 模型切换未实现",
                "Gemini额度: M5Max可本地模型",
            ]},
            {"id": "FR-MCP", "label": "FR-MCP\n协议 (3项)", "annotations": [
                "MCP-01~03: 前端没看到",
            ]},
            {"id": "FR-TRACE", "label": "FR-TRACE\n学习轨迹 (5项)", "annotations": [
                "TRACE-01: 死代码",
                "TRACE-05: 归档链路不完整",
            ]},
        ]
    },
]

# Cross-module item
cross_module = {
    "name": "跨模块\nAuto Research",
    "color": "#eba0ac",
    "stroke": "#d20f39",
    "annotations": [
        "Critical #3: 引入Auto Research量化迭代",
        "FR-QA-01: 算法靠不靠谱需要评估",
        "S40报告: 当前无评估基础设施",
    ]
}

# ═══ Layout calculation ═══
CENTER_X = 2000
CENTER_Y = 1800
MODULE_RADIUS = 800
MODULE_W = 220
MODULE_H = 80

# Center node
cid = "center"
ctid = "center_t"
elements.append(rect(cid, CENTER_X - 150, CENTER_Y - 50, 300, 100, "", "#1e1e2e", "#cdd6f4", bound_text=ctid))
elements.append(text_el(ctid, CENTER_X - 150, CENTER_Y - 50, "Canvas Learning\nSystem\n7 Modules → 99 FR → 108 批注", 20, "#cdd6f4", container_id=cid, w=300, h=100))

n_modules = len(modules)
for i, mod in enumerate(modules):
    angle = (2 * math.pi * i / n_modules) - math.pi / 2
    mx = CENTER_X + MODULE_RADIUS * math.cos(angle) - MODULE_W/2
    my = CENTER_Y + MODULE_RADIUS * math.sin(angle) - MODULE_H/2

    mid = f"mod_{i}"
    mtid = f"mod_t_{i}"
    elements.append(rect(mid, mx, my, MODULE_W, MODULE_H, "", mod["color"], mod["stroke"], bound_text=mtid))
    elements.append(text_el(mtid, mx, my, mod["name"], 18, "#1e1e2e", container_id=mid, w=MODULE_W, h=MODULE_H))

    # Arrow from center to module
    aid = f"arr_c_{i}"
    elements.append(arrow(aid, cid, mid,
        [[CENTER_X, CENTER_Y], [mx + MODULE_W/2, my + MODULE_H/2]], mod["stroke"]))

    # FRs for this module
    fr_start_x = mx + MODULE_W + 60
    fr_y = my - (len(mod["frs"]) - 1) * 90 / 2

    for j, fr in enumerate(mod["frs"]):
        fy = fr_y + j * 130
        fid = f"fr_{i}_{j}"
        ftid = f"fr_t_{i}_{j}"
        fw = 200
        fh = 60

        elements.append(rect(fid, fr_start_x, fy, fw, fh, "", "#313244", mod["stroke"], bound_text=ftid))
        elements.append(text_el(ftid, fr_start_x, fy, fr["label"], 14, "#cdd6f4", container_id=fid, w=fw, h=fh))

        # Arrow module -> FR
        afid = f"arr_f_{i}_{j}"
        elements.append(arrow(afid, mid, fid,
            [[mx + MODULE_W, my + MODULE_H/2], [fr_start_x, fy + fh/2]], mod["stroke"]))

        # Annotations
        ann_x = fr_start_x + fw + 40
        for k, ann in enumerate(fr["annotations"]):
            ay = fy + k * 32 - (len(fr["annotations"]) - 1) * 16
            ann_id = f"ann_{i}_{j}_{k}"

            is_broken = "[BROKEN]" in ann
            is_question = "？" in ann or "什么" in ann
            ann_color = "#d20f39" if is_broken else ("#df8e1d" if is_question else "#5c5f77")

            elements.append(text_el(ann_id, ann_x, ay, f"• {ann}", 12, ann_color, w=350, h=18, text_align="left"))

            # Arrow FR -> annotation
            aaid = f"arr_a_{i}_{j}_{k}"
            elements.append(arrow(aaid, fid, ann_id,
                [[fr_start_x + fw, fy + fh/2], [ann_x, ay + 9]], "#6c7086"))

# Cross-module Auto Research node
crx = CENTER_X - 150
cry = CENTER_Y + MODULE_RADIUS + 200
crid = "cross"
crtid = "cross_t"
elements.append(rect(crid, crx, cry, 260, 70, "", cross_module["color"], cross_module["stroke"], bound_text=crtid))
elements.append(text_el(crtid, crx, cry, cross_module["name"], 18, "#1e1e2e", container_id=crid, w=260, h=70))

# Arrow center -> cross
elements.append(arrow("arr_cross", cid, crid,
    [[CENTER_X, CENTER_Y + 50], [crx + 130, cry]], cross_module["stroke"]))

# Cross-module annotations
for k, ann in enumerate(cross_module["annotations"]):
    ay = cry + 90 + k * 28
    ann_id = f"cross_ann_{k}"
    elements.append(text_el(ann_id, crx, ay, f"• {ann}", 12, "#d20f39", w=400, h=18, text_align="left"))

# ═══ Build Excalidraw file ═══
excalidraw = {
    "type": "excalidraw",
    "version": 2,
    "source": "canvas-learning-system-mindmap",
    "elements": elements,
    "appState": {
        "viewBackgroundColor": "#ffffff",
        "gridSize": None,
    },
    "files": {}
}

output_path = "docs/architecture/module-fr-annotations-mindmap.excalidraw"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(excalidraw, f, ensure_ascii=False, indent=2)

print(f"Generated {output_path}")
print(f"Elements: {len(elements)}")
print(f"Modules: {len(modules)}")
print(f"Total annotations mapped: {sum(len(a) for m in modules for f in m['frs'] for a in [f['annotations']])}")
