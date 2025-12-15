"""
Script to fix encoding issues in test_diagnose_environment_simple.py
Adds UTF-8 encoding parameters to subprocess.run() calls
"""
import re
from pathlib import Path

def fix_encoding():
    # Read the test file
    test_file = Path(__file__).parent / "tests" / "test_diagnose_environment_simple.py"

    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: Fix test_diagnostic_script_runs() - add encoding and assert
    pattern1 = r'''(def test_diagnostic_script_runs\(\):.*?# Act\s+result = subprocess\.run\(\s+\[sys\.executable, str\(script_path\)\],\s+capture_output=True,\s+text=True,)\s+(timeout=30\s+\))'''

    replacement1 = r'''\1
        encoding='utf-8',
        errors='ignore',
        \2'''

    content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

    # Add assert output is not None for test 1
    pattern1b = r'''(# Verify output contains expected sections\s+output = result\.stdout if result\.stdout else result\.stderr\s+)(assert "Python版本")'''
    replacement1b = r'''\1assert output is not None, "Should have output from diagnostic script"
    \2'''
    content = re.sub(pattern1b, replacement1b, content)

    # Pattern 2: Fix test_diagnostic_output_format() - add encoding and assert
    pattern2 = r'''(def test_diagnostic_output_format\(\):.*?# Act\s+result = subprocess\.run\(\s+\[sys\.executable, str\(script_path\)\],\s+capture_output=True,\s+text=True,)\s+(timeout=30\s+\))'''

    replacement2 = r'''\1
        encoding='utf-8',
        errors='ignore',
        \2'''

    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

    # Add assert output is not None for test 2
    pattern2b = r'''(# Assert - Should have checkmarks.*?\s+output = result\.stdout if result\.stdout else result\.stderr\s+)(has_success_mark)'''
    replacement2b = r'''\1assert output is not None, "Should have output from diagnostic script"
    \2'''
    content = re.sub(pattern2b, replacement2b, content, flags=re.DOTALL)

    # Pattern 3: Fix test_diagnostic_exit_codes() - add encoding only (no assert needed)
    pattern3 = r'''(def test_diagnostic_exit_codes\(\):.*?# Act\s+result = subprocess\.run\(\s+\[sys\.executable, str\(script_path\)\],\s+capture_output=True,\s+text=True,)\s+(timeout=30\s+\))'''

    replacement3 = r'''\1
        encoding='utf-8',
        errors='ignore',
        \2'''

    content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)

    # Write the fixed content back
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: Applied encoding fixes to test_diagnose_environment_simple.py")
    print("")
    print("Fixed locations:")
    print("  1. test_diagnostic_script_runs() - Added UTF-8 encoding + assert")
    print("  2. test_diagnostic_output_format() - Added UTF-8 encoding + assert")
    print("  3. test_diagnostic_exit_codes() - Added UTF-8 encoding")

if __name__ == "__main__":
    fix_encoding()
