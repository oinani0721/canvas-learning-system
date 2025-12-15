#!/usr/bin/env python3
"""
修复 canvas_utils.py 中的缩进错误
"""

import re

def fix_canvas_indentation():
    with open('canvas_utils.py', 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    fixed_lines = []
    current_indent = 0

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            fixed_lines.append(line)
            continue

        # 检查是否是类定义或顶级定义
        if stripped.startswith('class ') or stripped.startswith('@dataclass'):
            current_indent = 0
            fixed_lines.append(line)
        elif stripped.startswith('def ') or stripped.startswith('async def '):
            # 判断是否是类方法
            if i > 0 and any('class ' in lines[j] for j in range(max(0, i-50), i)):
                # 找到最近的类定义
                class_indent = 0
                for j in range(i-1, -1, -1):
                    if lines[j].strip().startswith('class ') or lines[j].strip().startswith('@dataclass'):
                        class_line = lines[j]
                        class_indent = len(class_line) - len(class_line.lstrip())
                        break

                # 方法应该缩进4个空格
                if current_indent == 0:
                    fixed_lines.append('    ' + stripped)
                else:
                    fixed_lines.append('    ' + stripped)
            else:
                fixed_lines.append(stripped)
        else:
            # 保持原有缩进或使用4的倍数
            if line.startswith('    '):
                fixed_lines.append(line)
            elif line.strip():
                # 尝试智能缩进
                indent = len(line) - len(line.lstrip())
                if indent % 4 == 0:
                    fixed_lines.append(line)
                else:
                    # 修正为4的倍数
                    correct_indent = (indent // 4) * 4
                    fixed_lines.append(' ' * correct_indent + stripped)
            else:
                fixed_lines.append(line)

    # 写回文件
    with open('canvas_utils.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))

    print("缩进修复完成")

if __name__ == "__main__":
    fix_canvas_indentation()