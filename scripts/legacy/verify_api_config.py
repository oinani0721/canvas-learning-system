#!/usr/bin/env python3
"""
验证API配置是否正确切换到Anthropic官方
"""

import os
import json

def verify_config():
    print("=== Claude Code API配置验证 ===\n")

    # 1. 检查环境变量
    api_url = os.getenv('ANTHROPIC_BASE_URL', '未设置')
    print(f"1. 环境变量 ANTHROPIC_BASE_URL: {api_url}")

    # 2. 检查settings.json
    settings_path = os.path.expanduser('~/.claude/settings.json')
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            print(f"\n2. settings.json配置:")
            print(f"   - 模型: {settings.get('model', '未设置')}")
            if 'env' in settings:
                print(f"   - ENV配置: {settings['env']}")
    except Exception as e:
        print(f"\n2. 读取settings.json失败: {e}")

    # 3. 验证结论
    print("\n=== 验证结论 ===")
    if 'api.anthropic.com' in api_url or ('env' in settings and 'api.anthropic.com' in str(settings['env'])):
        print("✅ 已配置使用Anthropic官方API")
        print("✅ 应该可以访问真正的Haiku 4.5模型")
    else:
        print("❌ 仍使用代理服务，未切换到官方API")

    print("\n=== 测试建议 ===")
    print("重启Claude Code后，可以：")
    print("1. 使用 /model 查看可用模型")
    print("2. 询问：'Claude Haiku 4.5是什么时候发布的？'")
    print("3. 如果回答2025年10月15日，说明使用的是真正的Haiku 4.5")

if __name__ == "__main__":
    verify_config()