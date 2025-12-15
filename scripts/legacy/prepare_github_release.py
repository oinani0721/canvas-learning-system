#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare Canvas Learning System for GitHub release
"""

import os
import shutil
from pathlib import Path

def prepare_github_release():
    """Copy all necessary files to github-release folder"""

    # Source and target directories
    source_root = Path('.')
    target_root = Path('canvas-learning-system-github')

    # Remove target if exists
    if target_root.exists():
        shutil.rmtree(target_root)

    # Create target directory
    target_root.mkdir()

    # Directories to exclude
    exclude_dirs = {
        '笔记库',  # User's personal notes
        '__pycache__',
        '.pytest_cache',
        'node_modules',
        '.git',
        'venv',
        'env',
        'canvas-learning-system-github'  # Don't copy the target itself
    }

    # Files to exclude
    exclude_files = {
        'prepare_github_release.py',  # This script itself
        '.DS_Store',
        'Thumbs.db'
    }

    # Track what we copy
    copied_files = []
    copied_dirs = []

    # Copy .claude/ directory
    if (source_root / '.claude').exists():
        shutil.copytree(source_root / '.claude', target_root / '.claude')
        copied_dirs.append('.claude/')
        print('[OK] Copied .claude/')

    # Copy docs/ directory
    if (source_root / 'docs').exists():
        shutil.copytree(source_root / 'docs', target_root / 'docs')
        copied_dirs.append('docs/')
        print('[OK] Copied docs/')

    # Copy tests/ directory
    if (source_root / 'tests').exists():
        shutil.copytree(source_root / 'tests', target_root / 'tests')
        copied_dirs.append('tests/')
        print('[OK] Copied tests/')

    # Root files to copy
    root_files = [
        'canvas_utils.py',
        'requirements.txt',
        '.gitignore',
        'CLAUDE.md',
        'README.md',
        'QUICK-START.md',
        'LICENSE',  # If exists
        'setup.py',  # If exists
    ]

    for filename in root_files:
        source_file = source_root / filename
        if source_file.exists():
            shutil.copy2(source_file, target_root / filename)
            copied_files.append(filename)
            print(f'[OK] Copied {filename}')

    # Create a manifest file
    manifest_path = target_root / 'MANIFEST.txt'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write('Canvas Learning System - GitHub Release\n')
        f.write('=' * 50 + '\n\n')
        f.write('Copied Directories:\n')
        for d in sorted(copied_dirs):
            f.write(f'  - {d}\n')
        f.write('\nCopied Root Files:\n')
        for file in sorted(copied_files):
            f.write(f'  - {file}\n')
        f.write(f'\nTotal: {len(copied_dirs)} directories, {len(copied_files)} root files\n')

    print(f'\n[OK] Created manifest: MANIFEST.txt')

    # Count total files
    total_files = sum(1 for _ in target_root.rglob('*') if _.is_file())

    print('\n' + '=' * 50)
    print(f'[SUCCESS] GitHub release prepared!')
    print(f'[INFO] Location: {target_root.absolute()}')
    print(f'[INFO] Total files: {total_files}')
    print('=' * 50)

    return str(target_root.absolute())

if __name__ == '__main__':
    target_path = prepare_github_release()
    print(f'\nNext steps:')
    print(f'1. Review files in: {target_path}')
    print(f'2. Initialize git: cd {target_path} && git init')
    print(f'3. Create GitHub repo and push')
